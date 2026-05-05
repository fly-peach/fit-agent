"""FitMe Package"""
from .core import settings
from .models import (
    BaseDBBase,
    UserDBBase,
    # Base DB models
    Exercise,
    FoodItem,
    RecommendedTraining,
    RecommendedFood,
    # User DB models
    User,
    UserSettings,
    HealthMetric,
    TrainingPlan,
    TrainingRecord,
    DietMeal,
    DailyDietSummary,
    StreakStats,
    UserImage,
    UserPinnedExercise,
    PlanExerciseItem,
    CustomFoodItem,
    # Backward compat
    Base,
)
from .services import UserService, HealthService, TrainingService, DietService, AuthService, ExerciseService
from .utils import get_db, get_base_db, get_user_db, engine, SessionLocal, BaseSessionLocal, UserSessionLocal, BaseDBContext, UserDBContext

__all__ = [
    # Config
    "settings",
    # Base models
    "BaseDBBase",
    "Exercise",
    "FoodItem",
    "RecommendedTraining",
    "RecommendedFood",
    # User models
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
    # Backward compat
    "Base",
    # Services
    "UserService",
    "HealthService",
    "TrainingService",
    "DietService",
    "AuthService",
    "ExerciseService",
    # Database
    "get_db",
    "get_base_db",
    "get_user_db",
    "engine",
    "SessionLocal",
    "BaseSessionLocal",
    "UserSessionLocal",
    "BaseDBContext",
    "UserDBContext",
]
