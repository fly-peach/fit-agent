from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthTokenResponse, LoginRequest, RefreshTokenRequest, RegisterRequest, RegisterResponse
from app.schemas.user import UserPublic


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    @staticmethod
    def _generate_member_id() -> str:
        return f"MBR{uuid4().hex[:8].upper()}"

    def register(self, payload: RegisterRequest) -> RegisterResponse:
        if payload.email and self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")
        if payload.phone and self.repo.get_by_phone(payload.phone):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="手机号已存在")

        user = self.repo.create_user(
            email=payload.email,
            phone=payload.phone,
            password_hash=get_password_hash(payload.password),
            name=payload.name,
        )
        return RegisterResponse(
            user=UserPublic.model_validate(user),
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def login(self, payload: LoginRequest) -> AuthTokenResponse:
        user = self.repo.get_by_account(payload.account)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

        return AuthTokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def refresh(self, payload: RefreshTokenRequest) -> AuthTokenResponse:
        try:
            claims = decode_token(payload.refresh_token)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")
        if claims.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")

        user = self.repo.get_by_id(int(claims["sub"]))
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户无效")

        return AuthTokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def get_current_user(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
        return user
