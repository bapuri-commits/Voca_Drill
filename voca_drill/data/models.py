"""SQLAlchemy ORM 모델.

Word + WordMeaning 분리 구조:
- Word: 단어 단위 (english, pronunciation, frequency, derivatives...)
- WordMeaning: 뜻 단위 (tested_synonyms, important_synonyms, example_en/ko...)
- WordProgress: 학습 진도 (SM-2, 라이트너 단계)
- BookTest / BookTestQuestion: 교재 테스트 (Quiz, Review TEST, Final TEST)
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Word(Base):
    """단어 테이블 -- 단어 단위."""

    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    english: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pronunciation: Mapped[str] = mapped_column(String, default="")
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    derivatives_json: Mapped[str] = mapped_column(Text, default="[]")
    exam_type: Mapped[str] = mapped_column(String, default="toefl")
    chapter: Mapped[str] = mapped_column(String, default="")
    word_order: Mapped[int] = mapped_column(Integer, default=0)
    exam_tip: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    meanings: Mapped[list["WordMeaning"]] = relationship(
        back_populates="word", cascade="all, delete-orphan", order_by="WordMeaning.meaning_order"
    )
    progress: Mapped["WordProgress | None"] = relationship(
        back_populates="word", uselist=False, cascade="all, delete-orphan"
    )


class WordMeaning(Base):
    """뜻 테이블 -- Word와 1:N. 뜻마다 다른 동의어 세트."""

    __tablename__ = "word_meanings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False, index=True)
    meaning_order: Mapped[int] = mapped_column(Integer, default=1)
    part_of_speech: Mapped[str] = mapped_column(String, default="")
    korean: Mapped[str] = mapped_column(String, default="")
    tested_synonyms_json: Mapped[str] = mapped_column(Text, default="[]")
    important_synonyms_json: Mapped[str] = mapped_column(Text, default="[]")
    example_en: Mapped[str] = mapped_column(Text, default="")
    example_ko: Mapped[str] = mapped_column(Text, default="")
    english_definition: Mapped[str | None] = mapped_column(Text, nullable=True)

    word: Mapped["Word"] = relationship(back_populates="meanings")


class WordProgress(Base):
    """단어별 학습 진도 -- Word와 1:1."""

    __tablename__ = "word_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False, unique=True, index=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mastery_level: Mapped[int] = mapped_column(Integer, default=1)
    quiz_level: Mapped[int] = mapped_column(Integer, default=1)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="new")
    first_studied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    word: Mapped["Word"] = relationship(back_populates="progress")


class LearningSession(Base):
    """학습 세션."""

    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    new_words_count: Mapped[int] = mapped_column(Integer, default=0)
    review_words_count: Mapped[int] = mapped_column(Integer, default=0)
    max_combo: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="in_progress")

    records: Mapped[list["LearningRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class LearningRecord(Base):
    """개별 응답 이력."""

    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("learning_sessions.id"), nullable=False)
    quiz_type: Mapped[str] = mapped_column(String, default="card_flip")
    quality: Mapped[int] = mapped_column(Integer, default=0)
    is_correct: Mapped[int] = mapped_column(Integer, default=0)
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped["LearningSession"] = relationship(back_populates="records")


class DailyStats(Base):
    """일일 통계 캐시."""

    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    words_studied: Mapped[int] = mapped_column(Integer, default=0)
    new_words: Mapped[int] = mapped_column(Integer, default=0)
    review_words: Mapped[int] = mapped_column(Integer, default=0)
    correct_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    study_time_sec: Mapped[int] = mapped_column(Integer, default=0)


class BookTest(Base):
    """교재 테스트 (Quiz / Review TEST / Final TEST)."""

    __tablename__ = "book_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_type: Mapped[str] = mapped_column(String, nullable=False)
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    covers_json: Mapped[str] = mapped_column(Text, default="[]")

    questions: Mapped[list["BookTestQuestion"]] = relationship(
        back_populates="test", cascade="all, delete-orphan", order_by="BookTestQuestion.question_order"
    )


class BookTestQuestion(Base):
    """교재 테스트 문제."""

    __tablename__ = "book_test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("book_tests.id"), nullable=False, index=True)
    question_order: Mapped[int] = mapped_column(Integer, default=1)
    question_type: Mapped[str] = mapped_column(String, default="synonym_matching")
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_word: Mapped[str] = mapped_column(String, default="")
    choices_json: Mapped[str] = mapped_column(Text, default="{}")
    answer: Mapped[str | None] = mapped_column(String, nullable=True)

    test: Mapped["BookTest"] = relationship(back_populates="questions")
