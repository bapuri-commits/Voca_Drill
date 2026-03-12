"""DB 연결/세션 관리."""

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def get_engine(db_path: str = "voca_drill.db") -> Engine:
    path = Path(db_path).resolve()
    return create_engine(f"sqlite:///{path}", echo=False)


def init_db(db_path: str = "voca_drill.db") -> None:
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def get_session(db_path: str = "voca_drill.db") -> Session:
    engine = get_engine(db_path)
    factory = sessionmaker(bind=engine)
    return factory()
