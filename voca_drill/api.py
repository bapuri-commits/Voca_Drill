"""Voca_Drill FastAPI 서버.

실행: uvicorn voca_drill.api:app --port 8500 --reload
"""

from __future__ import annotations

import json
import uuid as _uuid
from collections.abc import Generator
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user_id, get_optional_user_id
from .config import load_config
from .data.database import get_session, init_db
from .data.models import BookTest
from .services.drill import DrillEngine, SessionContext
from .services.quiz import QuizGenerator
from .services.scheduler import Scheduler
from .services.stats import StatsTracker
from .services.wordbank import WordBank

_config = load_config()
_active_sessions: dict[str, tuple[SessionContext, Session]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(_config["db"]["path"])
    yield


app = FastAPI(title="Voca_Drill API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB 세션을 열고 끝나면 자동 close."""
    db = get_session(_config["db"]["path"])
    try:
        yield db
    finally:
        db.close()


# ──────────────────── Pydantic Models ────────────────────


class SessionCreateRequest(BaseModel):
    mode: str = "day"
    chapter: str | None = None
    size: int = 15
    review_ratio: float = 0.7
    exam_type: str | None = None
    daily_new_limit: int = 15


class AnswerRequest(BaseModel):
    word_id: int
    quality: int
    quiz_type: str = "card_flip"
    response_time_ms: int = 0


class TypingCheckRequest(BaseModel):
    correct: str
    user_input: str


# ──────────────────── Words API ────────────────────


@app.get("/api/words")
def list_words(
    chapter: str | None = Query(None),
    exam_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    wb = WordBank(db)
    words = wb.list_words(chapter=chapter, exam_type=exam_type, status=status, limit=limit, offset=offset)
    return [_serialize_word(w) for w in words]


@app.get("/api/words/chapters")
def list_chapters(
    exam_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    wb = WordBank(db)
    chapters = wb.get_chapters(exam_type=exam_type)
    return [
        {"chapter": ch, "count": wb.count_words(chapter=ch, exam_type=exam_type)}
        for ch in chapters
    ]


@app.get("/api/words/{word_id}")
def get_word(word_id: int, db: Session = Depends(get_db)) -> dict:
    wb = WordBank(db)
    w = wb.get_word(word_id)
    if not w:
        raise HTTPException(404, "단어를 찾을 수 없습니다")
    return _serialize_word(w)


@app.post("/api/words/import")
async def import_words(file: UploadFile, exam_type: str = "toefl", db: Session = Depends(get_db)) -> dict:
    content = await file.read()
    tmp_path = Path(f"_tmp_import_{_uuid.uuid4().hex[:8]}.json")
    tmp_path.write_bytes(content)
    try:
        wb = WordBank(db)
        return wb.import_from_json(tmp_path, exam_type=exam_type)
    finally:
        tmp_path.unlink(missing_ok=True)


# ──────────────────── Sessions API ────────────────────


@app.post("/api/sessions")
def create_session(req: SessionCreateRequest, user_id: int = Depends(get_current_user_id)) -> dict:
    db = get_session(_config["db"]["path"])
    scheduler = Scheduler(db, user_id=user_id)
    engine = DrillEngine(db, scheduler)

    if req.mode == "day":
        if not req.chapter:
            raise HTTPException(400, "Day Study에는 chapter가 필요합니다")
        ctx = engine.create_day_session(chapter=req.chapter)
    elif req.mode == "review":
        ctx = engine.create_review_session()
    else:
        ctx = engine.create_session(
            size=req.size,
            review_ratio=req.review_ratio,
            exam_type=req.exam_type,
            daily_new_limit=req.daily_new_limit,
        )

    if ctx.is_empty:
        db.close()
        raise HTTPException(400, "학습할 단어가 없습니다")

    session_id = ctx.learning_session.id
    _active_sessions[session_id] = (ctx, db)

    return {
        "session_id": session_id,
        "total": ctx.total,
        "remaining": ctx.remaining,
    }


def _get_active_session(session_id: str) -> tuple[SessionContext, Session]:
    entry = _active_sessions.get(session_id)
    if not entry:
        raise HTTPException(404, "세션을 찾을 수 없습니다")
    return entry


@app.get("/api/sessions/{session_id}/next")
def get_next_word(session_id: str, force_quiz_type: str | None = Query(None)) -> dict:
    ctx, db = _get_active_session(session_id)

    if ctx.is_complete():
        return {"complete": True, "remaining": 0}

    word = ctx.next_word()
    if not word:
        return {"complete": True, "remaining": 0}

    quiz_gen = QuizGenerator(db)
    quiz = quiz_gen.generate(word, force_quiz_type)

    return {
        "complete": False,
        "remaining": ctx.remaining,
        "answered": ctx.answered,
        "combo": ctx.combo,
        "max_combo": ctx.max_combo,
        "quiz": {
            "word_id": quiz.word_id,
            "quiz_type": quiz.quiz_type,
            "question": quiz.question,
            "choices": quiz.choices,
        },
    }


@app.post("/api/sessions/{session_id}/answer")
def submit_answer(session_id: str, req: AnswerRequest) -> dict:
    ctx, db = _get_active_session(session_id)

    result = ctx.answer(
        req.quality,
        quiz_type=req.quiz_type,
        response_time_ms=req.response_time_ms,
    )

    if result is None:
        raise HTTPException(400, "응답할 단어가 없습니다")

    review = result["review_result"]
    return {
        "needs_retry": result["needs_retry"],
        "remaining": ctx.remaining,
        "combo": ctx.combo,
        "max_combo": ctx.max_combo,
        "review": {
            "ease_factor": review.ease_factor,
            "interval_days": review.interval_days,
            "mastery_level": review.mastery_level,
            "status": review.status,
        },
    }


@app.post("/api/sessions/{session_id}/finish")
def finish_session(session_id: str) -> dict:
    ctx, db = _get_active_session(session_id)

    summary = ctx.finish()
    _active_sessions.pop(session_id, None)
    db.close()

    if summary is None:
        raise HTTPException(400, "세션 종료 실패")

    user_id = ctx.learning_session.user_id if ctx.learning_session else 1
    with get_session(_config["db"]["path"]) as stats_db:
        StatsTracker(stats_db, user_id=user_id).update_daily_cache()

    return summary


# ──────────────────── Quiz API ────────────────────


@app.get("/api/quiz/{word_id}")
def generate_quiz(word_id: int, quiz_type: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    wb = WordBank(db)
    word = wb.get_word(word_id)
    if not word:
        raise HTTPException(404, "단어를 찾을 수 없습니다")

    quiz_gen = QuizGenerator(db)
    quiz = quiz_gen.generate(word, quiz_type)

    return {
        "word_id": quiz.word_id,
        "quiz_type": quiz.quiz_type,
        "question": quiz.question,
        "choices": quiz.choices,
        "correct_answer": quiz.correct_answer,
    }


@app.post("/api/quiz/typing/check")
def check_typing(req: TypingCheckRequest, db: Session = Depends(get_db)) -> dict:
    quiz_gen = QuizGenerator(db)
    result = quiz_gen.check_typing(req.correct, req.user_input)
    return asdict(result)


# ──────────────────── Stats API ────────────────────


@app.get("/api/stats/daily")
def get_daily_stats(target_date: str | None = Query(None), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> dict:
    d = date.fromisoformat(target_date) if target_date else None
    stats = StatsTracker(db, user_id=user_id)
    result = stats.get_daily_stats(d)
    return asdict(result)


@app.get("/api/stats/overall")
def get_overall_progress(exam_type: str | None = Query(None), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> dict:
    stats = StatsTracker(db, user_id=user_id)
    result = stats.get_overall_progress(exam_type=exam_type)
    return asdict(result)


@app.get("/api/stats/streak")
def get_streak(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)) -> dict:
    stats = StatsTracker(db, user_id=user_id)
    return {"streak_days": stats.get_streak()}


# ──────────────────── Book Tests API ────────────────────


@app.get("/api/book-tests")
def list_book_tests(db: Session = Depends(get_db)) -> list[dict]:
    tests = db.query(BookTest).order_by(BookTest.id).all()
    return [
        {
            "id": t.id,
            "test_type": t.test_type,
            "test_name": t.test_name,
            "covers": json.loads(t.covers_json),
            "question_count": len(t.questions),
        }
        for t in tests
    ]


@app.get("/api/book-tests/{test_id}")
def get_book_test(test_id: int, db: Session = Depends(get_db)) -> dict:
    test = db.get(BookTest, test_id)
    if not test:
        raise HTTPException(404, "테스트를 찾을 수 없습니다")

    return {
        "id": test.id,
        "test_type": test.test_type,
        "test_name": test.test_name,
        "covers": json.loads(test.covers_json),
        "questions": [
            {
                "id": q.id,
                "order": q.question_order,
                "type": q.question_type,
                "question_text": q.question_text,
                "target_word": q.target_word,
                "choices": json.loads(q.choices_json),
                "answer": q.answer,
            }
            for q in test.questions
        ],
    }


# ──────────────────── Auth API ────────────────────


@app.get("/api/auth/me")
def get_me(user_id: int = Depends(get_current_user_id)) -> dict:
    return {"user_id": user_id}


# ──────────────────── PDF API ────────────────────

_PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdf"


@app.get("/api/pdf/list")
def list_pdfs(user_id: int = Depends(get_current_user_id)) -> dict:
    result: dict = {"full": [], "day": [], "test": []}
    if not _PDF_DIR.exists():
        return result
    for f in sorted(_PDF_DIR.glob("*.pdf")):
        result["full"].append({"filename": f.name, "size_mb": round(f.stat().st_size / 1024 / 1024, 1)})
    for sub, key in [("day", "day"), ("test", "test")]:
        sub_dir = _PDF_DIR / sub
        if sub_dir.exists():
            for f in sorted(sub_dir.glob("*.pdf")):
                result[key].append({"filename": f"{sub}/{f.name}", "label": f.stem, "size_mb": round(f.stat().st_size / 1024 / 1024, 1)})
    return result


@app.get("/api/pdf/{path:path}")
def serve_pdf(path: str, token: str = Query(None), user_id: int | None = Depends(get_optional_user_id)):
    """PDF 서빙 — Authorization 헤더 또는 ?token= 쿼리 파라미터로 인증."""
    from .auth import decode_token as _decode
    if user_id is None and token:
        try:
            payload = _decode(token)
            user_id = int(payload["sub"])
        except Exception:
            raise HTTPException(401, "Invalid token")
    if user_id is None:
        raise HTTPException(401, "Not authenticated")
    resolved = (_PDF_DIR / path).resolve()
    if not str(resolved).startswith(str(_PDF_DIR.resolve())):
        raise HTTPException(403, "접근 금지")
    if not resolved.exists() or resolved.suffix != ".pdf":
        raise HTTPException(404, "PDF를 찾을 수 없습니다")
    return FileResponse(resolved, media_type="application/pdf")


# ──────────────────── Helpers ────────────────────


def _serialize_word(w) -> dict:
    """Word ORM -> API 응답 dict."""
    return {
        "id": w.id,
        "english": w.english,
        "pronunciation": w.pronunciation,
        "frequency": w.frequency,
        "derivatives": json.loads(w.derivatives_json),
        "exam_type": w.exam_type,
        "chapter": w.chapter,
        "word_order": w.word_order,
        "exam_tip": w.exam_tip,
        "progress": _serialize_progress(w.progress) if w.progress else None,
        "meanings": [
            {
                "id": m.id,
                "order": m.meaning_order,
                "part_of_speech": m.part_of_speech,
                "korean": m.korean,
                "tested_synonyms": json.loads(m.tested_synonyms_json),
                "important_synonyms": json.loads(m.important_synonyms_json),
                "example_en": m.example_en,
                "example_ko": m.example_ko,
                "english_definition": m.english_definition,
            }
            for m in w.meanings
        ],
    }


def _serialize_progress(p) -> dict:
    return {
        "mastery_level": p.mastery_level,
        "status": p.status,
        "ease_factor": p.ease_factor,
        "interval_days": p.interval_days,
        "next_review": p.next_review.isoformat() if p.next_review else None,
        "total_attempts": p.total_attempts,
        "correct_count": p.correct_count,
    }


# ──────────────────── Static Files (React) ────────────────────

_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
