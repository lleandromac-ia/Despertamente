from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.repository import get_user_by_id
from app.auth.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def _user_from_token(token: str | None) -> dict:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação necessária.")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.")
    user = get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado.")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    access_token: str | None = Query(None),
) -> dict:
    token = credentials.credentials if credentials else access_token
    return _user_from_token(token)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores.")
    return user
