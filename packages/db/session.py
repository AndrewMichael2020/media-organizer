"""
DB session factory — shared across packages.
Usage:
    from forensic_db.session import get_session
    with get_session() as session:
        ...
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_DATABASE_URL = (
    os.environ.get("FMO_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql://fmo:fmo@localhost:5432/fmo"
)

_engine = create_engine(_DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine():
    return _engine
