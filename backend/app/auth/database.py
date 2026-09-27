import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    must_change_password INTEGER NOT NULL DEFAULT 0,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    social_instagram TEXT NOT NULL DEFAULT '',
    social_tiktok TEXT NOT NULL DEFAULT '',
    social_youtube TEXT NOT NULL DEFAULT '',
    social_website TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def db_path() -> Path:
    path = settings.storage_path / "app.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def row_to_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "mustChangePassword": bool(row["must_change_password"]),
        "fullName": row["full_name"],
        "email": row["email"],
        "phone": row["phone"],
        "socialInstagram": row["social_instagram"],
        "socialTiktok": row["social_tiktok"],
        "socialYoutube": row["social_youtube"],
        "socialWebsite": row["social_website"],
        "createdAt": row["created_at"],
    }
