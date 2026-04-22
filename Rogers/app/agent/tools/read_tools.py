# -*- coding: utf-8 -*-
"""AI 教练读取工具（无副作用）。"""

from datetime import date, timedelta

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from app.models.user import User
from app.repositories.body_composition_repository import BodyCompositionRepository
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.repositories.user_repository import UserRepository
from app.services.body_composition_evaluator import evaluate_all
from app.services.dashboard_service import DashboardService


async def get_user_profile(user_repo: UserRepository, user_id: int) -> ToolResponse:
    """Get the current user's profile information.

    Args:
        user_repo (`UserRepository`):
            User repository instance.
        user_id (`int`):
            User ID to query.

    Returns:
        `ToolResponse`:
            User profile data or error message.
    """
    user: User | None = user_repo.get_by_id(user_id)
    if user is None:
        return ToolResponse(
            content=[
                TextBlock(type="text", text="Error: 用户不存在"),
            ],
        )
    result = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at.isoformat(),
    }
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"用户信息：{result}"),
        ],
    )


async def get_health_metrics(repo: DailyMetricsRepository, user_id: int, days: int = 7) -> ToolResponse:
    """Get the user's health metrics history.

    Args:
        repo (`DailyMetricsRepository`):
            Daily metrics repository instance.
        user_id (`int`):
            User ID to query.
        days (`int`, optional):
            Number of days to look back. Defaults to 7.

    Returns:
        `ToolResponse`:
            Health metrics data for the specified period.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=max(days - 1, 0))
    rows = repo.list_by_user(user_id=user_id, from_date=start_date, to_date=end_date, skip=0, limit=max(days, 7))
    rows = list(reversed(rows))
    result = [
        {
            "record_date": r.record_date.isoformat(),
            "weight": r.weight,
            "body_fat_rate": r.body_fat_rate,
            "bmi": r.bmi,
            "visceral_fat_level": r.visceral_fat_level,
            "bmr": r.bmr,
        }
        for r in rows
    ]
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"最近 {days} 天健康数据：{result}"),
        ],
    )


async def get_workout_history(repo: DailyWorkoutPlanRepository, user_id: int, days: int = 7) -> ToolResponse:
    """Get the user's workout plan history.

    Args:
        repo (`DailyWorkoutPlanRepository`):
            Workout plan repository instance.
        user_id (`int`):
            User ID to query.
        days (`int`, optional):
            Number of days to look back. Defaults to 7.

    Returns:
        `ToolResponse`:
            Workout plan data for the specified period.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=max(days - 1, 0))
    rows = repo.list_by_user(user_id=user_id, from_date=start_date, to_date=end_date, skip=0, limit=max(days, 7))
    rows = list(reversed(rows))
    result = [
        {
            "record_date": r.record_date.isoformat(),
            "plan_title": r.plan_title,
            "duration_minutes": r.duration_minutes,
            "is_completed": r.is_completed,
        }
        for r in rows
    ]
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"最近 {days} 天训练记录：{result}"),
        ],
    )


def _meal_dict(obj, prefix: str) -> dict:
    return {
        "calories_kcal": getattr(obj, f"{prefix}_calories_kcal", 0),
        "protein_g": getattr(obj, f"{prefix}_protein_g", 0),
        "carb_g": getattr(obj, f"{prefix}_carb_g", 0),
        "fat_g": getattr(obj, f"{prefix}_fat_g", 0),
    }


async def get_nutrition_history(repo: DailyNutritionRepository, user_id: int, days: int = 7) -> ToolResponse:
    """Get the user's nutrition intake history.

    Args:
        repo (`DailyNutritionRepository`):
            Nutrition repository instance.
        user_id (`int`):
            User ID to query.
        days (`int`, optional):
            Number of days to look back. Defaults to 7.

    Returns:
        `ToolResponse`:
            Nutrition data for the specified period.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=max(days - 1, 0))
    rows = repo.list_by_user(user_id=user_id, from_date=start_date, to_date=end_date, skip=0, limit=max(days, 7))
    rows = list(reversed(rows))
    result = [
        {
            "record_date": r.record_date.isoformat(),
            "calories_kcal": r.calories_kcal,
            "protein_g": r.protein_g,
            "carb_g": r.carb_g,
            "fat_g": r.fat_g,
            "breakfast": _meal_dict(r, "breakfast"),
            "lunch": _meal_dict(r, "lunch"),
            "dinner": _meal_dict(r, "dinner"),
        }
        for r in rows
    ]
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"最近 {days} 天营养摄入：{result}"),
        ],
    )


async def get_dashboard_summary(service: DashboardService, user: User) -> ToolResponse:
    """Get the user's dashboard summary.

    Args:
        service (`DashboardService`):
            Dashboard service instance.
        user (`User`):
            Current user.

    Returns:
        `ToolResponse`:
            Dashboard summary data.
    """
    data = service.me(user)
    result = {
        "latest_metrics": data.growth_analytics.metrics_latest.model_dump() if data.growth_analytics.metrics_latest else None,
        "health_profile": {k: v.model_dump() for k, v in data.growth_analytics.health_profile.items()},
        "goal_progress": data.growth_analytics.goal_progress.model_dump(),
        "alerts": [a.model_dump() for a in data.growth_analytics.alerts],
    }
    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"仪表盘摘要：{result}"),
        ],
    )


async def analyze_body_composition(
    body_repo: BodyCompositionRepository,
    user_id: int,
    height_cm: float = 175.0,
    actual_age: int = 30,
) -> ToolResponse:
    """Analyze the user's latest body composition record and return assessment.

    Args:
        body_repo (`BodyCompositionRepository`):
            Body composition repository instance.
        user_id (`int`):
            User ID to query.
        height_cm (`float`, optional):
            User height in cm. Defaults to 175.
        actual_age (`int`, optional):
            User actual age. Defaults to 30.

    Returns:
        `ToolResponse`:
            Body composition analysis including body type, health score, nutrition status, body age, and indicator levels.
    """
    latest = body_repo.latest(member_id=user_id)
    if latest is None:
        return ToolResponse(
            content=[
                TextBlock(type="text", text="暂无体成分记录，请先录入一次体成分数据。"),
            ],
        )

    result = evaluate_all(latest, height_cm=height_cm, actual_age=actual_age)

    summary = {
        "measured_at": latest.measured_at.isoformat(),
        "weight": latest.weight,
        "body_fat_rate": latest.body_fat_rate,
        "bmi": latest.bmi,
        "body_type": result["body_type"],
        "health_score": result["health_score"],
        "nutrition_status": result["nutrition_status"],
        "body_age": result["body_age"],
        "ideal_weight": result.get("ideal_weight"),
        "weight_control": result.get("weight_control"),
        "fat_control": result.get("fat_control"),
        "muscle_control": result.get("muscle_control"),
        "indicator_levels": result["indicator_levels"],
    }

    level_text = "、".join(f"{k}={v}" for k, v in result["indicator_levels"].items() if v not in ("标准", "正常", "优", "良"))
    note = ""
    if level_text:
        note = f" 需要关注的指标：{level_text}"

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"体成分评估（{summary['measured_at'][:10]}）："
                    f"体型={summary['body_type']}，"
                    f"健康评分={summary['health_score']}分，"
                    f"营养状态={summary['nutrition_status']}，"
                    f"体年龄={summary['body_age']}岁，"
                    f"理想体重={summary['ideal_weight']}kg，"
                    f"体重控制={summary['weight_control']}kg，"
                    f"脂肪控制={summary['fat_control']}kg，"
                    f"肌肉控制={summary['muscle_control']}kg"
                    f"{note}"
                ),
            ),
        ],
    )