"""StatsTracker — 학습 통계 계산."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..data.models import (
    DailyStats,
    LearningRecord,
    LearningSession,
    Word,
    WordProgress,
)


@dataclass
class SessionStatsResult:
    """세션 통계."""

    session_id: str
    total_words: int
    correct_count: int
    correct_rate: float
    max_combo: int
    new_words: int
    review_words: int
    duration_sec: int
    status: str


@dataclass
class DailyStatsResult:
    """일일 통계."""

    date: date
    words_studied: int
    new_words: int
    review_words: int
    correct_rate: float
    sessions_count: int
    streak_days: int
    study_time_sec: int


@dataclass
class LevelDistribution:
    """Level별 단어 분포."""

    level: int
    label: str
    count: int
    percentage: float


@dataclass
class ChapterProgress:
    """챕터별 진도."""

    chapter: str
    total: int
    studied: int
    mastered: int
    completion_rate: float


@dataclass
class OverallProgress:
    """전체 진도 요약."""

    total_words: int
    studied_words: int
    level_distribution: list[LevelDistribution] = field(default_factory=list)
    chapter_progress: list[ChapterProgress] = field(default_factory=list)
    streak_days: int = 0
    estimated_days_remaining: int = 0


LEVEL_LABELS = {
    1: "New",
    2: "Learning",
    3: "Review",
    4: "Familiar",
    5: "Mastered",
}


class StatsTracker:
    """학습 통계를 계산하고 캐시."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_session_stats(self, session_id: str) -> SessionStatsResult | None:
        """특정 세션의 통계."""
        ls = self._session.get(LearningSession, session_id)
        if not ls:
            return None

        duration = 0
        if ls.started_at and ls.ended_at:
            duration = int((ls.ended_at - ls.started_at).total_seconds())

        total = ls.total_words or 1
        return SessionStatsResult(
            session_id=ls.id,
            total_words=ls.total_words,
            correct_count=ls.correct_count,
            correct_rate=round(ls.correct_count / total, 4),
            max_combo=ls.max_combo,
            new_words=ls.new_words_count,
            review_words=ls.review_words_count,
            duration_sec=duration,
            status=ls.status,
        )

    def get_daily_stats(self, target_date: date | None = None) -> DailyStatsResult:
        """특정 날짜의 학습 통계 (기본: 오늘)."""
        if target_date is None:
            target_date = date.today()

        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        sessions = (
            self._session.query(LearningSession)
            .filter(
                LearningSession.started_at >= day_start,
                LearningSession.started_at < day_end,
            )
            .all()
        )

        total_words = sum(s.total_words for s in sessions)
        correct_count = sum(s.correct_count for s in sessions)
        new_words = sum(s.new_words_count for s in sessions)
        review_words = sum(s.review_words_count for s in sessions)
        study_time = 0
        for s in sessions:
            if s.started_at and s.ended_at:
                study_time += int((s.ended_at - s.started_at).total_seconds())

        return DailyStatsResult(
            date=target_date,
            words_studied=total_words,
            new_words=new_words,
            review_words=review_words,
            correct_rate=round(correct_count / max(total_words, 1), 4),
            sessions_count=len(sessions),
            streak_days=self.get_streak(),
            study_time_sec=study_time,
        )

    def get_overall_progress(self, *, exam_type: str | None = None) -> OverallProgress:
        """전체 학습 진도."""
        word_query = self._session.query(Word)
        if exam_type:
            word_query = word_query.filter(Word.exam_type == exam_type)
        total_words = word_query.count()

        studied = (
            self._session.query(WordProgress)
            .join(Word)
            .filter(Word.id == WordProgress.word_id)
        )
        if exam_type:
            studied = studied.filter(Word.exam_type == exam_type)
        studied_count = studied.count()

        level_dist = self._get_level_distribution(exam_type=exam_type, total_words=total_words)
        chapter_prog = self._get_chapter_progress(exam_type=exam_type)
        streak = self.get_streak()
        est_days = self._estimate_remaining_days(total_words, studied_count)

        return OverallProgress(
            total_words=total_words,
            studied_words=studied_count,
            level_distribution=level_dist,
            chapter_progress=chapter_prog,
            streak_days=streak,
            estimated_days_remaining=est_days,
        )

    def get_streak(self) -> int:
        """연속 학습 일수 계산."""
        today = date.today()
        streak = 0
        check_date = today

        while True:
            day_start = datetime.combine(check_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            has_session = (
                self._session.query(LearningSession)
                .filter(
                    LearningSession.started_at >= day_start,
                    LearningSession.started_at < day_end,
                    LearningSession.status == "completed",
                )
                .first()
            )

            if has_session:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                if check_date == today:
                    check_date -= timedelta(days=1)
                    continue
                break

        return streak

    def update_daily_cache(self, target_date: date | None = None) -> None:
        """DailyStats 캐시 테이블 갱신."""
        if target_date is None:
            target_date = date.today()

        stats = self.get_daily_stats(target_date)

        existing = (
            self._session.query(DailyStats)
            .filter(DailyStats.date == target_date)
            .first()
        )

        if existing:
            existing.words_studied = stats.words_studied
            existing.new_words = stats.new_words
            existing.review_words = stats.review_words
            existing.correct_rate = stats.correct_rate
            existing.sessions_count = stats.sessions_count
            existing.streak_days = stats.streak_days
            existing.study_time_sec = stats.study_time_sec
        else:
            daily = DailyStats(
                date=target_date,
                words_studied=stats.words_studied,
                new_words=stats.new_words,
                review_words=stats.review_words,
                correct_rate=stats.correct_rate,
                sessions_count=stats.sessions_count,
                streak_days=stats.streak_days,
                study_time_sec=stats.study_time_sec,
            )
            self._session.add(daily)

        self._session.commit()

    def _get_level_distribution(
        self, *, exam_type: str | None, total_words: int
    ) -> list[LevelDistribution]:
        """Level별 단어 수 분포."""
        query = (
            self._session.query(
                WordProgress.mastery_level,
                func.count(WordProgress.id),
            )
            .join(Word)
            .group_by(WordProgress.mastery_level)
        )
        if exam_type:
            query = query.filter(Word.exam_type == exam_type)

        level_counts: dict[int, int] = dict(query.all())

        studied_total = sum(level_counts.values())
        unstudied = max(0, total_words - studied_total)
        level_counts.setdefault(1, 0)
        level_counts[1] += unstudied

        result = []
        for level in range(1, 6):
            count = level_counts.get(level, 0)
            pct = round(count / max(total_words, 1) * 100, 1)
            result.append(LevelDistribution(
                level=level,
                label=LEVEL_LABELS[level],
                count=count,
                percentage=pct,
            ))
        return result

    def _get_chapter_progress(self, *, exam_type: str | None) -> list[ChapterProgress]:
        """챕터별 학습 진도."""
        chapter_query = (
            self._session.query(
                Word.chapter,
                func.count(Word.id),
            )
            .group_by(Word.chapter)
            .order_by(Word.chapter)
        )
        if exam_type:
            chapter_query = chapter_query.filter(Word.exam_type == exam_type)

        result = []
        for chapter, total in chapter_query.all():
            studied_q = (
                self._session.query(func.count(WordProgress.id))
                .join(Word)
                .filter(Word.chapter == chapter)
            )
            mastered_q = (
                self._session.query(func.count(WordProgress.id))
                .join(Word)
                .filter(Word.chapter == chapter, WordProgress.mastery_level >= 4)
            )
            if exam_type:
                studied_q = studied_q.filter(Word.exam_type == exam_type)
                mastered_q = mastered_q.filter(Word.exam_type == exam_type)

            studied = studied_q.scalar() or 0
            mastered = mastered_q.scalar() or 0

            result.append(ChapterProgress(
                chapter=chapter,
                total=total,
                studied=studied,
                mastered=mastered,
                completion_rate=round(studied / max(total, 1) * 100, 1),
            ))
        return result

    def _estimate_remaining_days(self, total: int, studied: int) -> int:
        """현재 학습 속도 기준 예상 남은 일수."""
        week_ago = datetime.now() - timedelta(days=7)
        recent_new = (
            self._session.query(func.count(WordProgress.id))
            .filter(WordProgress.first_studied_at >= week_ago)
            .scalar() or 0
        )

        if recent_new == 0:
            return 0

        daily_rate = recent_new / 7
        remaining = total - studied
        if remaining <= 0:
            return 0
        return round(remaining / daily_rate)
