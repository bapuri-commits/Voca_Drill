"""DrillEngine — 학습 세션 구성 + 진행 관리."""

from __future__ import annotations

import random
from datetime import datetime

from sqlalchemy.orm import Session

from ..data.models import LearningRecord, LearningSession, Word
from .scheduler import Scheduler


class DrillEngine:
    """학습 세션을 구성하고 진행을 관리."""

    def __init__(self, session: Session, scheduler: Scheduler) -> None:
        self._session = session
        self._scheduler = scheduler

    def create_session(
        self,
        *,
        size: int = 15,
        review_ratio: float = 0.7,
        exam_type: str | None = None,
        daily_new_limit: int = 15,
    ) -> SessionContext:
        """새 학습 세션 생성.

        Args:
            size: 세션 단어 수
            review_ratio: 복습 단어 비율 (0.0~1.0)
            exam_type: 시험 유형 필터
            daily_new_limit: 일일 새 단어 상한
        """
        review_count = round(size * review_ratio)
        new_count = size - review_count

        review_words = self._scheduler.get_review_words(
            exam_type=exam_type, limit=review_count
        )
        if len(review_words) < review_count:
            new_count += review_count - len(review_words)

        new_words = self._scheduler.get_new_words(
            exam_type=exam_type, daily_limit=daily_new_limit, limit=new_count
        )

        all_words = review_words + new_words
        if not all_words:
            return SessionContext(
                engine=self,
                learning_session=None,
                words=[],
                review_ids=set(),
            )

        random.shuffle(all_words)

        learning_session = LearningSession(
            user_id=self._scheduler._user_id,
            total_words=len(all_words),
            new_words_count=len(new_words),
            review_words_count=len(review_words),
        )
        self._session.add(learning_session)
        self._session.commit()

        review_ids = {w.id for w in review_words}

        return SessionContext(
            engine=self,
            learning_session=learning_session,
            words=all_words,
            review_ids=review_ids,
        )

    def resume_session(self, session_id: str) -> SessionContext | None:
        """미완료 세션 이어하기."""
        ls = (
            self._session.query(LearningSession)
            .filter(
                LearningSession.id == session_id,
                LearningSession.status == "in_progress",
            )
            .first()
        )
        if not ls:
            return None

        answered_word_ids = {
            r.word_id
            for r in self._session.query(LearningRecord.word_id)
            .filter(LearningRecord.session_id == session_id)
            .all()
        }

        all_word_ids = set()
        review_ids: set[int] = set()

        for record in ls.records:
            all_word_ids.add(record.word_id)

        remaining_words = (
            self._session.query(Word)
            .filter(Word.id.in_(all_word_ids - answered_word_ids))
            .all()
        )

        return SessionContext(
            engine=self,
            learning_session=ls,
            words=remaining_words,
            review_ids=review_ids,
        )

    def submit_answer(
        self,
        learning_session: LearningSession,
        word_id: int,
        quality: int,
        *,
        quiz_type: str = "card_flip",
        response_time_ms: int = 0,
    ) -> dict:
        """응답 제출 → SM-2 갱신 + 기록 저장.

        Returns:
            {"review_result": ReviewResult, "needs_retry": bool}
        """
        review_result = self._scheduler.process_answer(word_id, quality)

        record = LearningRecord(
            word_id=word_id,
            session_id=learning_session.id,
            quiz_type=quiz_type,
            quality=quality,
            is_correct=1 if quality >= 2 else 0,
            response_time_ms=response_time_ms,
        )
        self._session.add(record)

        if quality >= 2:
            learning_session.correct_count += 1

        self._session.commit()

        return {
            "review_result": review_result,
            "needs_retry": quality == 0,
        }

    def finish_session(self, learning_session: LearningSession, *, max_combo: int = 0) -> dict:
        """세션 종료 처리.

        Returns:
            세션 요약 dict
        """
        learning_session.status = "completed"
        learning_session.ended_at = datetime.now()
        learning_session.max_combo = max_combo
        self._session.commit()

        return {
            "total_words": learning_session.total_words,
            "correct_count": learning_session.correct_count,
            "new_words": learning_session.new_words_count,
            "review_words": learning_session.review_words_count,
            "max_combo": learning_session.max_combo,
        }


class SessionContext:
    """진행 중인 세션의 상태를 관리."""

    MAX_RETRIES_PER_WORD = 3

    def __init__(
        self,
        *,
        engine: DrillEngine,
        learning_session: LearningSession | None,
        words: list[Word],
        review_ids: set[int],
    ) -> None:
        self.engine = engine
        self.learning_session = learning_session
        self._words = list(words)
        self._retry_queue: list[Word] = []
        self._retry_counts: dict[int, int] = {}
        self._current_index = 0
        self._combo = 0
        self._max_combo = 0
        self._review_ids = review_ids

    @property
    def is_empty(self) -> bool:
        return self.learning_session is None

    @property
    def total(self) -> int:
        return len(self._words) + len(self._retry_queue)

    @property
    def answered(self) -> int:
        return self._current_index

    @property
    def remaining(self) -> int:
        return max(0, len(self._words) - self._current_index) + len(self._retry_queue)

    @property
    def combo(self) -> int:
        return self._combo

    @property
    def max_combo(self) -> int:
        return self._max_combo

    def next_word(self) -> Word | None:
        """다음 단어 반환. 없으면 재시도 큐에서 반환."""
        if self._current_index < len(self._words):
            word = self._words[self._current_index]
            return word

        if self._retry_queue:
            return self._retry_queue[0]

        return None

    def answer(self, quality: int, *, quiz_type: str = "card_flip", response_time_ms: int = 0) -> dict | None:
        """현재 단어에 응답. next_word()로 가져온 단어에 대한 응답."""
        if self.learning_session is None:
            return None

        word = self.next_word()
        if word is None:
            return None

        result = self.engine.submit_answer(
            self.learning_session,
            word.id,
            quality,
            quiz_type=quiz_type,
            response_time_ms=response_time_ms,
        )

        if self._current_index < len(self._words):
            self._current_index += 1
        elif self._retry_queue:
            self._retry_queue.pop(0)

        if quality == 0:
            count = self._retry_counts.get(word.id, 0) + 1
            self._retry_counts[word.id] = count
            if count < self.MAX_RETRIES_PER_WORD:
                self._retry_queue.append(word)
            self._combo = 0
        elif quality >= 2:
            self._combo += 1
            self._max_combo = max(self._max_combo, self._combo)
        else:
            self._combo = 0

        return result

    def is_complete(self) -> bool:
        """세션 완료 여부 (모든 단어 + 재시도 큐 소진)."""
        return self._current_index >= len(self._words) and not self._retry_queue

    def finish(self) -> dict | None:
        """세션 종료."""
        if self.learning_session is None:
            return None
        return self.engine.finish_session(self.learning_session, max_combo=self._max_combo)
