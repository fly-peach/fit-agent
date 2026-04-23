"""User Router"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

import sys
sys.path.insert(0, "E:/fitagent/rogers/src")
from fitme.utils.database import get_db
from fitme.services.user_service import UserService
from fitme.schemas.user import (
    UserProfileResponse,
    UpdateProfileRequest,
    UserSettingsResponse,
    UpdateSettingsRequest,
)
from fitme.schemas.common import BaseResponse
from fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/user", tags=["User"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录过期")
    return user


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户信息"""
    user = UserService.get_profile(db, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserProfileResponse(
        data={
            "userId": user.user_id,
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar,
            "role": user.role,
            "createdAt": user.created_at,
        }
    )


@router.put("/profile", response_model=BaseResponse)
def update_profile(
    data: UpdateProfileRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = UserService.update_profile(db, current_user.user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return BaseResponse(message="更新成功")


@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户设置"""
    settings = UserService.get_settings(db, current_user.user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="设置不存在")
    return UserSettingsResponse(
        data={
            "calorieGoal": settings.calorie_goal,
            "proteinGoal": settings.protein_goal,
            "carbsGoal": settings.carbs_goal,
            "fatGoal": settings.fat_goal,
            "waterGoal": settings.water_goal,
            "weightGoal": float(settings.weight_goal) if settings.weight_goal else None,
            "weeklyTrainingGoal": settings.weekly_training_goal,
            "notificationEnabled": settings.notification_enabled,
            "reminderTime": str(settings.reminder_time),
        }
    )


@router.put("/settings", response_model=BaseResponse)
def update_settings(
    data: UpdateSettingsRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户设置"""
    settings = UserService.update_settings(db, current_user.user_id, data)
    if not settings:
        raise HTTPException(status_code=404, detail="设置不存在")
    return BaseResponse(message="更新成功")