# -*- coding: utf-8 -*-
"""AI 教练 Agent 工具模块"""

from .analysis_tools import summarize_text
from .multimodal import (
    analyze_food_image,
    analyze_scale_image,
    view_image,
    view_image_base64,
)
from .read_tools import (
    analyze_body_composition,
    get_dashboard_summary,
    get_health_metrics,
    get_nutrition_history,
    get_user_profile,
    get_workout_history,
)
from .write_tools import (
    update_daily_metrics,
    update_nutrition,
    update_workout_plan,
)

__all__ = [
    "get_user_profile",
    "get_health_metrics",
    "get_workout_history",
    "get_nutrition_history",
    "get_dashboard_summary",
    "analyze_body_composition",
    "update_daily_metrics",
    "update_workout_plan",
    "update_nutrition",
    "summarize_text",
    "view_image",
    "view_image_base64",
    "analyze_food_image",
    "analyze_scale_image",
]
