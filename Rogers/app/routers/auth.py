"""Auth Router"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from src.fitme.utils.database import get_db
from src.fitme.services.auth_service import AuthService
from src.fitme.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, RegisterRequest, RegisterResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    result = AuthService.register(db, data)
    if not result:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    return RegisterResponse(data=result)


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    result = AuthService.login(db, data)
    if not result:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return LoginResponse(data=result)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    authorization: Optional[str] = Header(None)
):
    """用户登出"""
    return LogoutResponse()