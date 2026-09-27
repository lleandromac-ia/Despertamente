from app.auth.repository import create_user, get_user_by_username
from app.auth.security import hash_password
from app.config import settings


def ensure_default_admin() -> None:
    if get_user_by_username(settings.admin_username):
        return
    create_user(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_initial_password),
        role="admin",
        must_change_password=False,
        full_name="Administrador",
        email="",
    )
