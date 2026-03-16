"""DB 연결/세션 관리."""

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(db_path: str = "voca_drill.db") -> Engine:
    global _engine
    if _engine is None:
        path = Path(db_path).resolve()
        _engine = create_engine(f"sqlite:///{path}", echo=False)
    return _engine


def get_session_factory(db_path: str = "voca_drill.db") -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = sessionmaker(bind=engine)
    return _session_factory


def init_db(db_path: str = "voca_drill.db") -> None:
    """테이블 생성. 이미 존재하면 무시."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def get_session(db_path: str = "voca_drill.db") -> Session:
    """새 DB 세션 반환."""
    factory = get_session_factory(db_path)
    return factory()


def reset_engine() -> None:
    """엔진/팩토리 리셋 (테스트용)."""
    global _engine, _session_factory
    if _engine:
        _engine.dispose()
    _engine = None
    _session_factory = None
