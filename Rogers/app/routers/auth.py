"""Auth Router - Dual Database Support"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from src.fitme.utils.database import get_user_db
from src.fitme.services.auth_service import AuthService
from src.fitme.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, RegisterRequest, RegisterResponse
from src.agents.utils.api_key_cache import api_key_cache

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
def register(
    data: RegisterRequest,
    user_db: Session = Depends(get_user_db)
):
    """用户注册"""
    result = AuthService.register(user_db, data)
    if not result:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    return RegisterResponse(data=result)


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    user_db: Session = Depends(get_user_db)
):
    """用户登录"""
    result = AuthService.login(user_db, data)
    if not result:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return LoginResponse(data=result)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    authorization: Optional[str] = Header(None)
):
    """用户登出"""
    if authorization:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        try:
            user_id = AuthService.get_user_id_from_token(token)
            if user_id:
                api_key_cache.delete(user_id)
        except Exception:
            pass
    return LogoutResponse()
