"""User Service"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import time as dt_time
from ..models import User, UserSettings
from ..schemas.user import UpdateProfileRequest, UpdateSettingsRequest


class UserService:
    """用户服务"""

    @staticmethod
    def get_profile(db: Session, user_id: int) -> Optional[User]:
        """获取用户信息"""
        return db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()

    @staticmethod
    def update_profile(db: Session, user_id: int, data: UpdateProfileRequest) -> Optional[User]:
        """更新用户信息"""
        user = db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()
        if user:
            if data.name:
                user.name = data.name
            if data.avatar:
                user.avatar = data.avatar
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_settings(db: Session, user_id: int) -> Optional[UserSettings]:
        """获取用户设置"""
        return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

    @staticmethod
    def update_settings(db: Session, user_id: int, data: UpdateSettingsRequest) -> Optional[UserSettings]:
        """更新用户设置"""
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings:
            if data.calorieGoal is not None:
                settings.calorie_goal = data.calorieGoal
            if data.proteinGoal is not None:
                settings.protein_goal = data.proteinGoal
            if data.carbsGoal is not None:
                settings.carbs_goal = data.carbsGoal
            if data.fatGoal is not None:
                settings.fat_goal = data.fatGoal
            if data.waterGoal is not None:
                settings.water_goal = data.waterGoal
            if data.weightGoal is not None:
                settings.weight_goal = data.weightGoal
            if data.weeklyTrainingGoal is not None:
                settings.weekly_training_goal = data.weeklyTrainingGoal
            if data.notificationEnabled is not None:
                settings.notification_enabled = data.notificationEnabled
            if data.autoApproveDbWrite is not None:
                settings.auto_approve_db_write = data.autoApproveDbWrite
            if data.reminderTime is not None:
                t = data.reminderTime
                if isinstance(t, str) and ':' in t:
                    parts = t.split(':')
                    t = dt_time(int(parts[0]), int(parts[1]))
                settings.reminder_time = t
            db.commit()
            db.refresh(settings)
        return settings