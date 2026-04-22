# -*- coding: utf-8 -*-
"""AI 教练写入工具（由审批流驱动）。

核心设计：
- 所有写入工具默认 approved=false，AI 调用时不得主动设为 true
- approved=false 时，工具创建待审批记录并返回审批 ID，挂起执行
- 用户审批通过后，由 ApprovalService 执行实际操作
"""

from datetime import date

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.schemas.daily_metrics import DailyMetricsUpsert
from app.schemas.daily_nutrition import DailyNutritionUpsert
from app.schemas.daily_workout_plan import DailyWorkoutPlanUpsert, WorkoutItem


async def update_daily_metrics(
    repo: DailyMetricsRepository,
    user_id: int,
    record_date: str,
    data: dict,
    approved: bool = False,
    approval_id: str | None = None,
) -> ToolResponse:
    """Update the user's daily body metrics.

    Args:
        repo (`DailyMetricsRepository`):
            Daily metrics repository instance.
        user_id (`int`):
            User ID.
        record_date (`str`):
            Date string in ISO format (YYYY-MM-DD).
        data (`dict`):
            Metrics data including weight, body_fat_rate, bmi.
        approved (`bool`):
            Whether the operation has been approved by human. Default False.
        approval_id (`str | None`):
            Approval ID when approved=True.

    Returns:
        `ToolResponse`:
            Success or error message.
    """
    if not approved:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"⏸️ 操作已挂起：等待审批（工具：update_daily_metrics，日期：{record_date}）",
                ),
            ],
        )

    try:
        date_obj = date.fromisoformat(record_date)
    except ValueError:
        return ToolResponse(
            content=[
                TextBlock(type="text", text=f"Error: 无效的日期格式 {record_date}"),
            ],
        )
    payload = DailyMetricsUpsert(
        weight=data.get("weight"),
        body_fat_rate=data.get("body_fat_rate"),
        bmi=data.get("bmi"),
    )
    repo.upsert(user_id=user_id, record_date=date_obj, payload=payload)
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"已更新 {record_date} 的身体数据"),
        ],
    )


async def update_workout_plan(
    repo: DailyWorkoutPlanRepository,
    user_id: int,
    record_date: str,
    plan: dict,
    approved: bool = False,
    approval_id: str | None = None,
) -> ToolResponse:
    """Update the user's daily workout plan.

    Args:
        repo (`DailyWorkoutPlanRepository`):
            Workout plan repository instance.
        user_id (`int`):
            User ID.
        record_date (`str`):
            Date string in ISO format (YYYY-MM-DD).
        plan (`dict`):
            Workout plan data including plan_title, items, duration_minutes.
        approved (`bool`):
            Whether the operation has been approved by human. Default False.
        approval_id (`str | None`):
            Approval ID when approved=True.

    Returns:
        `ToolResponse`:
            Success or error message.
    """
    if not approved:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"⏸️ 操作已挂起：等待审批（工具：update_workout_plan，日期：{record_date}）",
                ),
            ],
        )

    try:
        date_obj = date.fromisoformat(record_date)
    except ValueError:
        return ToolResponse(
            content=[
                TextBlock(type="text", text=f"Error: 无效的日期格式 {record_date}"),
            ],
        )
    items = [WorkoutItem.model_validate(i) for i in plan.get("items", [])]
    payload = DailyWorkoutPlanUpsert(
        plan_title=plan.get("plan_title", "今日训练"),
        items=items,
        duration_minutes=plan.get("duration_minutes", 0),
        is_completed=plan.get("is_completed", False),
        notes=plan.get("notes"),
    )
    repo.upsert(user_id=user_id, record_date=date_obj, payload=payload)
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"已更新 {record_date} 的训练计划"),
        ],
    )


def _parse_meal(data: dict, key: str) -> dict | None:
    m = data.get(key)
    if not m:
        return None
    return {
        "calories_kcal": float(m.get("calories_kcal", 0)),
        "protein_g": float(m.get("protein_g", 0)),
        "carb_g": float(m.get("carb_g", 0)),
        "fat_g": float(m.get("fat_g", 0)),
    }


async def update_nutrition(
    repo: DailyNutritionRepository,
    user_id: int,
    record_date: str,
    data: dict,
    approved: bool = False,
    approval_id: str | None = None,
) -> ToolResponse:
    """Update the user's daily nutrition intake.

    Args:
        repo (`DailyNutritionRepository`):
            Nutrition repository instance.
        user_id (`int`):
            User ID.
        record_date (`str`):
            Date string in ISO format (YYYY-MM-DD).
        data (`dict`):
            Nutrition data including calories_kcal, protein_g, carb_g, fat_g,
            and optional meal breakdowns (breakfast, lunch, dinner).
        approved (`bool`):
            Whether the operation has been approved by human. Default False.
        approval_id (`str | None`):
            Approval ID when approved=True.

    Returns:
        `ToolResponse`:
            Success or error message.
    """
    if not approved:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"⏸️ 操作已挂起：等待审批（工具：update_nutrition，日期：{record_date}）",
                ),
            ],
        )

    try:
        date_obj = date.fromisoformat(record_date)
    except ValueError:
        return ToolResponse(
            content=[
                TextBlock(type="text", text=f"Error: 无效的日期格式 {record_date}"),
            ],
        )

    payload_data: dict = {
        "calories_kcal": data.get("calories_kcal"),
        "protein_g": data.get("protein_g"),
        "carb_g": data.get("carb_g"),
        "fat_g": data.get("fat_g"),
        "notes": data.get("notes"),
        "breakfast": _parse_meal(data, "breakfast"),
        "lunch": _parse_meal(data, "lunch"),
        "dinner": _parse_meal(data, "dinner"),
    }
    payload = DailyNutritionUpsert(**{k: v for k, v in payload_data.items() if v is not None})
    repo.upsert(user_id=user_id, record_date=date_obj, payload=payload)
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"已更新 {record_date} 的营养摄入数据"),
        ],
    )