from datetime import datetime, timezone
from typing import Any

from app.auth.database import get_conn, row_to_user


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
    return row_to_user(row) if row else None


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row) if row else None


def get_password_hash(user_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return row["password_hash"] if row else None


def list_users() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
    return [row_to_user(r) for r in rows]


def create_user(
    username: str,
    password_hash: str,
    role: str,
    must_change_password: bool = True,
    full_name: str = "",
    email: str = "",
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (
                username, password_hash, role, must_change_password,
                full_name, email, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username.strip().lower(),
                password_hash,
                role,
                1 if must_change_password else 0,
                full_name,
                email,
                now,
            ),
        )
        user_id = cur.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row)


def update_profile(user_id: int, data: dict[str, str]) -> dict[str, Any] | None:
    fields = {
        "full_name": data.get("fullName"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "social_instagram": data.get("socialInstagram"),
        "social_tiktok": data.get("socialTiktok"),
        "social_youtube": data.get("socialYoutube"),
        "social_website": data.get("socialWebsite"),
    }
    sets = []
    values: list[Any] = []
    for col, val in fields.items():
        if val is not None:
            sets.append(f"{col} = ?")
            values.append(val.strip())
    if not sets:
        return get_user_by_id(user_id)
    values.append(user_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", values)
    return get_user_by_id(user_id)


def update_password(user_id: int, password_hash: str, clear_must_change: bool = True) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = ?
            WHERE id = ?
            """,
            (password_hash, 0 if clear_must_change else 1, user_id),
        )
