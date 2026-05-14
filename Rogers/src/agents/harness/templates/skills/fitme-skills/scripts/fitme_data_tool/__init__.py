"""Fitme 数据工具模块

所有函数都要求提供有效的 JWT Token 进行身份验证。
"""
from .read import (
    get_user_profile,
    get_health_summary,
    get_health_history,
    get_training_today,
    get_training_weekly,
    get_training_recommendations,
    get_diet_today,
    get_diet_weekly_trend,
    get_food_recommendations,
    get_user_settings,
    search_foods,
    get_full_overview,
)
from .exercise import (
    search_exercises,
    get_exercise_detail,
    get_exercise_categories,
    pin_exercise,
    unpin_exercise,
    get_pinned_exercises,
    reorder_pinned_exercises,
)
from .write import (
    update_profile,
    add_health_metric,
    add_training_plan,
    complete_training,
    delete_training_plan,
    add_meal,
    update_meal,
    delete_meal,
    update_settings,
)

__all__ = [
    "get_user_profile",
    "get_health_summary",
    "get_health_history",
    "get_training_today",
    "get_training_weekly",
    "get_training_recommendations",
    "get_diet_today",
    "get_diet_weekly_trend",
    "get_food_recommendations",
    "get_user_settings",
    "search_foods",
    "get_full_overview",
    "search_exercises",
    "get_exercise_detail",
    "get_exercise_categories",
    "pin_exercise",
    "unpin_exercise",
    "get_pinned_exercises",
    "reorder_pinned_exercises",
    "update_profile",
    "add_health_metric",
    "add_training_plan",
    "complete_training",
    "delete_training_plan",
    "add_meal",
    "update_meal",
    "delete_meal",
    "update_settings",
]
