"""FitMe Models Module - Split into base_db and user_db"""
# New split models
from .base_db import Base as BaseDBBase, Exercise, FoodItem, RecommendedTraining, RecommendedFood
from .user_db import Base as UserDBBase, User, UserSettings, HealthMetric, TrainingPlan, TrainingRecord, DietMeal, DailyDietSummary, StreakStats, UserImage, UserPinnedExercise, PlanExerciseItem, CustomFoodItem

# Chat models are defined in agents module, re-exported here for convenience
from src.agents.harness.chats.models import ChatSession  # noqa: F401

# For backward compatibility - alias to UserDBBase
Base = UserDBBase

__all__ = [
    # New split models
    "BaseDBBase",
    "Exercise",
    "FoodItem",
    "RecommendedTraining",
    "RecommendedFood",
    "UserDBBase",
    "User",
    "UserSettings",
    "HealthMetric",
    "TrainingPlan",
    "TrainingRecord",
    "DietMeal",
    "DailyDietSummary",
    "StreakStats",
    "UserImage",
    "UserPinnedExercise",
    "PlanExerciseItem",
    "CustomFoodItem",
    "ChatSession",
    # Backward compatibility
    "Base",
]
