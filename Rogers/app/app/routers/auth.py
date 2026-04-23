"""Auth Router"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

import sys
sys.path.insert(0, "E:/fitagent/rogers/src")
from fitme.utils.database import get_db
from fitme.services.auth_service import AuthService
from fitme.schemas.auth import LoginRequest, LoginResponse, LogoutResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


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