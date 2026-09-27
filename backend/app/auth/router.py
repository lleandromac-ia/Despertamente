from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.deps import get_current_user, require_admin
from app.auth.repository import (
    create_user,
    get_password_hash,
    get_user_by_username,
    list_users,
    update_password,
    update_profile,
)
from app.auth.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdate(BaseModel):
    fullName: str | None = None
    email: str | None = None
    phone: str | None = None
    socialInstagram: str | None = None
    socialTiktok: str | None = None
    socialYoutube: str | None = None
    socialWebsite: str | None = None


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=8, max_length=128)


class AdminCreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)
    fullName: str = ""
    email: str = ""
    role: str = "user"


@router.post("/login")
def login(body: LoginRequest):
    user_row = get_user_by_username(body.username)
    if not user_row:
        raise HTTPException(401, "Usuário ou senha inválidos.")
    stored_hash = get_password_hash(user_row["id"])
    if not stored_hash or not verify_password(body.password, stored_hash):
        raise HTTPException(401, "Usuário ou senha inválidos.")
    token = create_access_token(user_row["id"], user_row["username"], user_row["role"])
    return {"accessToken": token, "user": user_row}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}


@router.patch("/me/profile")
def patch_profile(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    updated = update_profile(user["id"], body.model_dump(exclude_unset=True))
    return {"user": updated}


@router.post("/me/password")
def change_password(body: PasswordChange, user: dict = Depends(get_current_user)):
    stored = get_password_hash(user["id"])
    if not stored or not verify_password(body.currentPassword, stored):
        raise HTTPException(400, "Senha atual incorreta.")
    update_password(user["id"], hash_password(body.newPassword), clear_must_change=True)
    refreshed = get_user_by_username(user["username"])
    return {"ok": True, "user": refreshed}


@router.get("/users")
def admin_list_users(_admin: dict = Depends(require_admin)):
    return {"users": list_users()}


@router.post("/users")
def admin_create_user(body: AdminCreateUser, _admin: dict = Depends(require_admin)):
    if body.role not in {"user", "admin"}:
        raise HTTPException(400, "Papel inválido.")
    if get_user_by_username(body.username):
        raise HTTPException(400, "Nome de usuário já existe.")
    created = create_user(
        username=body.username.lower(),
        password_hash=hash_password(body.password),
        role=body.role,
        must_change_password=True,
        full_name=body.fullName,
        email=body.email,
    )
    return {"user": created}
