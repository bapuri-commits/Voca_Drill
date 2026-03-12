"""SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    english = Column(String, nullable=False, index=True)
    korean = Column(String, nullable=False)
    part_of_speech = Column(String, default="")
    example = Column(String, default="")
    exam_type = Column(String, default="")
    group_name = Column(String, default="")
    difficulty = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, nullable=False, index=True)
    is_correct = Column(Integer, nullable=False)
    mode = Column(String, default="en2kr")
    session_id = Column(String, nullable=False)
    answered_at = Column(DateTime, default=datetime.now)


class WordProgress(Base):
    __tablename__ = "word_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, nullable=False, unique=True, index=True)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=0)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime, nullable=True)
    total_attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    status = Column(String, default="new")
    updated_at = Column(DateTime, default=datetime.now)
