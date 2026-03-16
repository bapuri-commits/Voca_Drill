"""WordBank -- 단어 DB CRUD, JSON import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..data.models import BookTest, BookTestQuestion, Word, WordMeaning, WordProgress


class WordBank:
    """단어 관리 서비스. DB CRUD + JSON import."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def import_from_json(
        self,
        file_path: str | Path,
        *,
        exam_type: str = "toefl",
        source: str = "import",
    ) -> dict[str, int]:
        """Day JSON 파일에서 단어 + Quiz를 DB에 import.

        지원 형식:
        - 추출 스크립트 출력: {"day": ..., "words": [...], "quiz": {...}}
        - 단순 배열: [{"english": ..., "meanings": [...]}, ...]
        """
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if isinstance(raw, dict) and "words" in raw:
            words_data = raw["words"]
            day_label = raw.get("day", "")
            quiz_data = raw.get("quiz")
        elif isinstance(raw, list):
            words_data = raw
            day_label = ""
            quiz_data = None
        else:
            words_data = [raw]
            day_label = ""
            quiz_data = None

        imported = 0
        skipped = 0

        for entry in words_data:
            english = entry.get("english", "").strip()
            if not english:
                skipped += 1
                continue

            entry_exam_type = entry.get("exam_type", exam_type)
            existing = self._session.execute(
                select(Word).where(
                    Word.english == english,
                    Word.exam_type == entry_exam_type,
                )
            ).scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            if not entry.get("chapter") and day_label:
                entry["chapter"] = day_label

            word = self._build_word(entry, exam_type=exam_type, source=source)
            self._session.add(word)
            imported += 1

        if quiz_data:
            self._import_quiz(quiz_data, day_label=day_label)

        self._session.commit()
        return {"imported": imported, "skipped": skipped}

    def import_test_json(
        self,
        file_path: str | Path,
    ) -> dict[str, int]:
        """Review/Final TEST JSON 파일을 DB에 import."""
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        tests = raw if isinstance(raw, list) else [raw]
        imported = 0

        for test_data in tests:
            test_name = test_data.get("test_name", "")
            existing = self._session.execute(
                select(BookTest).where(BookTest.test_name == test_name)
            ).scalar_one_or_none()
            if existing:
                continue

            test = BookTest(
                test_type="review_test" if "Review" in test_name else "final_test",
                test_name=test_name,
                covers_json=json.dumps(test_data.get("covers", []), ensure_ascii=False),
            )

            for q in test_data.get("questions", []):
                question = BookTestQuestion(
                    question_order=q.get("number", 1),
                    question_type="multiple_choice",
                    question_text=q.get("question_text"),
                    target_word=q.get("highlighted_word", ""),
                    choices_json=json.dumps(q.get("choices", {}), ensure_ascii=False),
                    answer=q.get("answer"),
                )
                test.questions.append(question)

            self._session.add(test)
            imported += 1

        self._session.commit()
        return {"imported": imported}

    def list_words(
        self,
        *,
        chapter: str | None = None,
        exam_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Word]:
        """단어 목록 조회 (필터링 + 페이지네이션)."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .order_by(Word.chapter, Word.word_order)
        )

        if chapter:
            stmt = stmt.where(Word.chapter == chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        if status:
            if status == "new":
                stmt = stmt.outerjoin(Word.progress).where(
                    or_(WordProgress.status == "new", WordProgress.id.is_(None))
                )
            else:
                stmt = stmt.join(Word.progress).where(WordProgress.status == status)

        stmt = stmt.offset(offset).limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def get_word(self, word_id: int) -> Word | None:
        """단어 상세 조회 (meanings, progress 포함)."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .where(Word.id == word_id)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_word_by_english(self, english: str) -> Word | None:
        """영어 단어명으로 조회."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .where(Word.english == english)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def count_words(
        self,
        *,
        chapter: str | None = None,
        exam_type: str | None = None,
    ) -> int:
        """단어 수 카운트."""
        stmt = select(func.count(Word.id))
        if chapter:
            stmt = stmt.where(Word.chapter == chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        result = self._session.execute(stmt).scalar()
        return result or 0

    def delete_word(self, word_id: int) -> bool:
        """단어 삭제 (cascade로 meanings, progress도 삭제)."""
        word = self._session.get(Word, word_id)
        if not word:
            return False
        self._session.delete(word)
        self._session.commit()
        return True

    def get_chapters(self, exam_type: str | None = None) -> list[str]:
        """등록된 챕터 목록."""
        stmt = select(Word.chapter).distinct().order_by(Word.chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        return list(self._session.execute(stmt).scalars().all())

    def _import_quiz(self, quiz_data: dict, *, day_label: str) -> None:
        """Day Quiz 데이터를 BookTest에 저장."""
        test_name = f"{day_label} Quiz" if day_label else "Quiz"
        existing = self._session.execute(
            select(BookTest).where(BookTest.test_name == test_name)
        ).scalar_one_or_none()
        if existing:
            return

        test = BookTest(
            test_type="quiz",
            test_name=test_name,
            covers_json=json.dumps([day_label] if day_label else [], ensure_ascii=False),
        )

        for q in quiz_data.get("questions", []):
            question = BookTestQuestion(
                question_order=q.get("number", 1),
                question_type="synonym_matching",
                target_word=q.get("word", ""),
                choices_json=json.dumps(
                    {"label": q.get("choice_label", ""), "text": q.get("choice_text", "")},
                    ensure_ascii=False,
                ),
                answer=q.get("answer_label"),
            )
            test.questions.append(question)

        self._session.add(test)

    @staticmethod
    def _build_word(entry: dict[str, Any], *, exam_type: str, source: str) -> Word:
        """JSON 엔트리 -> Word ORM 객체 변환."""
        derivatives = entry.get("derivatives", [])

        word = Word(
            english=entry["english"].strip(),
            pronunciation=entry.get("pronunciation") or "",
            frequency=entry.get("frequency", 0),
            derivatives_json=json.dumps(derivatives, ensure_ascii=False),
            exam_type=entry.get("exam_type", exam_type),
            chapter=entry.get("chapter", ""),
            word_order=entry.get("word_order", 0),
            exam_tip=entry.get("exam_tip"),
            source=source,
        )

        for m in entry.get("meanings", []):
            tested = m.get("tested_synonyms", [])
            important = m.get("important_synonyms", [])
            meaning = WordMeaning(
                meaning_order=m.get("order", 1),
                part_of_speech=m.get("part_of_speech", ""),
                korean=m.get("korean", ""),
                tested_synonyms_json=json.dumps(tested, ensure_ascii=False),
                important_synonyms_json=json.dumps(important, ensure_ascii=False),
                example_en=m.get("example_en", ""),
                example_ko=m.get("example_ko") or "",
                english_definition=m.get("english_definition"),
            )
            word.meanings.append(meaning)

        if not entry.get("meanings"):
            word.meanings.append(WordMeaning(
                meaning_order=1,
                korean=entry.get("korean", ""),
                part_of_speech=entry.get("part_of_speech", ""),
            ))

        return word
