"""
Shared DB session dependency for FastAPI.
Adds packages/db to sys.path so models and session are importable.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make packages/db importable from the API
_DB_PKG = Path(__file__).parents[4] / "packages" / "db"
if str(_DB_PKG) not in sys.path:
    sys.path.insert(0, str(_DB_PKG))

from session import get_engine, get_session  # noqa: E402 (re-export)

__all__ = ["get_session", "get_engine"]
