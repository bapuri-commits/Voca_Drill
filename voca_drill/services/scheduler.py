"""Scheduler — SM-2 간격 반복 알고리즘 + 라이트너 단계 파생."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..data.models import Word, WordProgress

QUALITY_MAP: dict[int, int] = {
    0: 0,   # 모름 → SM-2 quality 0
    1: 2,   # 헷갈림 → SM-2 quality 2
    2: 4,   # 알겠음 → SM-2 quality 4
    3: 5,   # 완벽 → SM-2 quality 5
}

MIN_EASE_FACTOR = 1.3
INITIAL_EASE_FACTOR = 2.5


@dataclass
class ReviewResult:
    """SM-2 계산 결과."""

    ease_factor: float
    interval_days: int
    repetitions: int
    next_review: datetime
    mastery_level: int
    status: str


class Scheduler:
    """SM-2 기반 복습 스케줄러."""

    def __init__(self, session: Session, user_id: int = 1) -> None:
        self._session = session
        self._user_id = user_id

    def process_answer(self, word_id: int, quality: int) -> ReviewResult:
        """사용자 응답 처리 → WordProgress 갱신.

        Args:
            word_id: 단어 ID
            quality: 사용자 평가 (0: 모름, 1: 헷갈림, 2: 알겠음, 3: 완벽)

        Returns:
            갱신된 복습 정보
        """
        progress = self._get_or_create_progress(word_id)
        sm2_quality = QUALITY_MAP.get(quality, 0)
        result = self._calculate_sm2(progress, sm2_quality)

        progress.ease_factor = result.ease_factor
        progress.interval_days = result.interval_days
        progress.repetitions = result.repetitions
        progress.next_review = result.next_review
        progress.mastery_level = result.mastery_level
        progress.status = result.status
        progress.total_attempts += 1
        if quality >= 2:
            progress.correct_count += 1

        self._session.commit()
        return result

    def get_review_words(self, *, exam_type: str | None = None, limit: int = 50) -> list[Word]:
        """복습 대상 단어 조회 (next_review가 현재 이전인 단어)."""
        now = datetime.now()
        query = (
            self._session.query(Word)
            .join(WordProgress)
            .filter(
                WordProgress.user_id == self._user_id,
                WordProgress.next_review <= now,
                WordProgress.status != "new",
            )
            .order_by(WordProgress.next_review)
        )
        if exam_type:
            query = query.filter(Word.exam_type == exam_type)
        return list(query.limit(limit).all())

    def get_new_words(
        self,
        *,
        exam_type: str | None = None,
        daily_limit: int = 15,
        limit: int = 50,
    ) -> list[Word]:
        """새 단어 조회 (아직 학습하지 않은 단어)."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        today_new_count = (
            self._session.query(WordProgress)
            .filter(WordProgress.user_id == self._user_id, WordProgress.first_studied_at >= today_start)
            .count()
        )

        remaining = max(0, daily_limit - today_new_count)
        if remaining == 0:
            return []

        query = (
            self._session.query(Word)
            .outerjoin(WordProgress, (WordProgress.word_id == Word.id) & (WordProgress.user_id == self._user_id))
            .filter(WordProgress.id.is_(None))
            .order_by(Word.chapter, Word.word_order)
        )
        if exam_type:
            query = query.filter(Word.exam_type == exam_type)
        return list(query.limit(min(remaining, limit)).all())

    def _get_or_create_progress(self, word_id: int) -> WordProgress:
        """WordProgress 조회 또는 생성."""
        progress = (
            self._session.query(WordProgress)
            .filter(WordProgress.word_id == word_id, WordProgress.user_id == self._user_id)
            .first()
        )
        if not progress:
            progress = WordProgress(word_id=word_id, user_id=self._user_id)
            self._session.add(progress)
            self._session.flush()
        return progress

    @staticmethod
    def _calculate_sm2(progress: WordProgress, sm2_quality: int) -> ReviewResult:
        """SM-2 알고리즘 핵심 계산.

        Args:
            progress: 현재 학습 진도
            sm2_quality: SM-2 표준 quality (0-5)
        """
        ef = progress.ease_factor
        reps = progress.repetitions
        interval = progress.interval_days

        if sm2_quality < 2:
            reps = 0
            interval = 1
        else:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 3
            else:
                interval = round(interval * ef)
            reps += 1

        ef = ef + (0.1 - (5 - sm2_quality) * (0.08 + (5 - sm2_quality) * 0.02))
        ef = max(MIN_EASE_FACTOR, ef)

        next_review = datetime.now() + timedelta(days=interval)
        mastery_level = _derive_mastery_level(interval)
        status = _derive_status(mastery_level)

        return ReviewResult(
            ease_factor=round(ef, 4),
            interval_days=interval,
            repetitions=reps,
            next_review=next_review,
            mastery_level=mastery_level,
            status=status,
        )


def _derive_mastery_level(interval_days: int) -> int:
    """interval에서 라이트너 단계 파생 (1-5)."""
    if interval_days <= 0:
        return 1
    if interval_days < 3:
        return 2
    if interval_days <= 7:
        return 3
    if interval_days <= 30:
        return 4
    return 5


def _derive_status(mastery_level: int) -> str:
    """mastery_level → status 문자열."""
    return {
        1: "new",
        2: "learning",
        3: "review",
        4: "familiar",
        5: "mastered",
    }.get(mastery_level, "new")
