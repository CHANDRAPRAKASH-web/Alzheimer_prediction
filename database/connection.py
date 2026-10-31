"""
=========================================================
Aid Axis - Database Connection Manager

Provides thread-safe connection handling for SQLite,
with table initialization and parameterized query support.
Designed with repository pattern so that it can later be
extended or swapped with PostgreSQL / SQLAlchemy.
=========================================================
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

from configs.config import PROJECT_ROOT

# Default DB Path in persistent outputs directory
DEFAULT_DB_PATH = PROJECT_ROOT / "outputs" / "aid_axis.db"


def get_db_path() -> Path:
    """
    Returns the active database file path. Can be overridden
    by the AID_AXIS_DB_PATH environment variable.
    """
    env_path = os.getenv("AID_AXIS_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


@contextmanager
def get_db_connection(db_path: Path = None):
    """
    Context manager yielding a thread-safe SQLite connection
    configured with row factories and foreign keys.
    """
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(
        str(path),
        timeout=30.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency in Streamlit
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except sqlite3.Error:
        pass
        
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
