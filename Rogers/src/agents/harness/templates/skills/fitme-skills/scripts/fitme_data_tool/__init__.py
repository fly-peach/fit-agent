"""Fitme 数据工具模块

提供用户数据的读取和写入操作。
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
from .diet import (
    get_diet_today as get_diet_today_v2,
    get_diet_weekly_trend as get_diet_weekly_trend_v2,
    get_nutrition_progress,
    get_food_recommendations as get_food_recommendations_v2,
    search_foods as search_foods_v2,
    get_food_categories,
    add_custom_food as add_custom_food_v2,
    delete_custom_food,
    analyze_diet_gap,
)
from .training import (
    get_training_monthly_schedule,
    get_training_weekly_progress,
    get_training_plan_detail,
    create_training_plan,
    update_training_plan,
    complete_training_plan,
    update_plan_exercise_item,
    renew_recurring_training_plan,
)
from .write import (
    update_profile,
    add_health_metric,
    update_health_metric,
    delete_health_metric,
    add_training_plan,
    complete_training,
    delete_training_plan,
    add_meal,
    update_meal,
    delete_meal,
    add_custom_food,
    update_custom_food,
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
    "get_training_monthly_schedule",
    "get_training_weekly_progress",
    "get_training_plan_detail",
    "create_training_plan",
    "update_training_plan",
    "complete_training_plan",
    "update_plan_exercise_item",
    "renew_recurring_training_plan",
    "update_profile",
    "add_health_metric",
    "update_health_metric",
    "delete_health_metric",
    "add_training_plan",
    "complete_training",
    "delete_training_plan",
    "add_meal",
    "update_meal",
    "delete_meal",
    "add_custom_food",
    "update_custom_food",
    "update_settings",
    "get_nutrition_progress",
    "get_food_categories",
    "delete_custom_food",
    "analyze_diet_gap",
]

# Prefer the new dual-database diet implementation.
get_diet_today = get_diet_today_v2
get_diet_weekly_trend = get_diet_weekly_trend_v2
get_food_recommendations = get_food_recommendations_v2
search_foods = search_foods_v2
add_custom_food = add_custom_food_v2
