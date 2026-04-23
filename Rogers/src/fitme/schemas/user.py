"""User Schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    """用户信息"""
    userId: int
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    role: str
    createdAt: datetime


class UserProfileResponse(BaseModel):
    """用户信息响应"""
    code: int = 200
    data: UserProfile


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""
    name: Optional[str] = None
    avatar: Optional[str] = None


class UserSettings(BaseModel):
    """用户设置"""
    calorieGoal: int
    proteinGoal: int
    carbsGoal: int
    fatGoal: int
    waterGoal: int
    weightGoal: Optional[float] = None
    weeklyTrainingGoal: int
    notificationEnabled: bool
    reminderTime: str


class UserSettingsResponse(BaseModel):
    """用户设置响应"""
    code: int = 200
    data: UserSettings


class UpdateSettingsRequest(BaseModel):
    """更新用户设置请求"""
    calorieGoal: Optional[int] = None
    proteinGoal: Optional[int] = None
    carbsGoal: Optional[int] = None
    fatGoal: Optional[int] = None
    waterGoal: Optional[int] = None
    weightGoal: Optional[float] = None
    weeklyTrainingGoal: Optional[int] = None
    notificationEnabled: Optional[bool] = None
    reminderTime: Optional[str] = None