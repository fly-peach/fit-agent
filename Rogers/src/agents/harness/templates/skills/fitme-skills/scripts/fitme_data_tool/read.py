"""Fitme 数据读取操作

与 read_data.py 类似，但不依赖 contextvars，直接接受 user_id 参数
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

from src.fitme.models import (
    HealthMetric,
    TrainingPlan,
    DietMeal,
    User,
    UserSettings,
    StreakStats,
    DailyDietSummary,
    RecommendedTraining,
    RecommendedFood,
    FoodItem,
)
from src.fitme.utils.database import SessionLocal


@contextmanager
def get_db_session():
    """获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_profile(user_id: int) -> dict[str, Any]:
    """获取用户基本信息"""
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            return {"success": False, "error": "用户不存在"}
        return {
            "success": True,
            "data": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "created_at": str(user.created_at) if user.created_at is not None else None,
            }
        }


def get_health_summary(user_id: int) -> dict[str, Any]:
    """获取用户最新健康指标"""
    with get_db_session() as db:
        latest = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).first()
        if not latest:
            return {"success": False, "error": "暂无健康数据"}
        return {
            "success": True,
            "data": {
                "measure_date": str(latest.measure_date),
                "weight": float(latest.weight) if latest.weight is not None else None,
                "height": float(latest.height) if latest.height is not None else None,
                "body_fat": float(latest.body_fat) if latest.body_fat is not None else None,
                "bmi": float(latest.bmi) if latest.bmi is not None else None,
                "bmi_status": latest.bmi_status,
            }
        }


def get_health_history(user_id: int, limit: int = 7) -> dict[str, Any]:
    """获取近期健康指标变化趋势"""
    with get_db_session() as db:
        records = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).limit(limit).all()
        if not records:
            return {"success": False, "error": "暂无历史记录"}
        return {
            "success": True,
            "data": [
                {
                    "measure_date": str(r.measure_date),
                    "weight": float(r.weight) if r.weight else None,
                    "height": float(r.height) if r.height else None,
                    "body_fat": float(r.body_fat) if r.body_fat else None,
                    "bmi": float(r.bmi) if r.bmi else None,
                }
                for r in records
            ]
        }


def get_training_today(user_id: int) -> dict[str, Any]:
    """获取今日训练计划"""
    with get_db_session() as db:
        today = date.today()
        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date == today
        ).all()
        return {
            "success": True,
            "data": [
                {
                    "plan_id": p.plan_id,
                    "plan_name": p.plan_name,
                    "plan_type": p.plan_type,
                    "scheduled_date": str(p.scheduled_date),
                    "estimated_duration": p.estimated_duration,
                    "target_intensity": p.target_intensity,
                    "status": p.status,
                    "note": p.note,
                }
                for p in plans
            ]
        }


def get_training_weekly(user_id: int) -> dict[str, Any]:
    """获取本周训练统计和安排"""
    with get_db_session() as db:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start
        ).order_by(TrainingPlan.scheduled_date).all()
        completed = [p for p in plans if p.status == "completed"]
        pending = [p for p in plans if p.status == "pending"]
        streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
        streak_days = streak.training_streak if streak else 0
        return {
            "success": True,
            "data": {
                "streak_days": streak_days,
                "completed_count": len(completed),
                "pending_count": len(pending),
                "plans": [
                    {
                        "plan_id": p.plan_id,
                        "plan_name": p.plan_name,
                        "plan_type": p.plan_type,
                        "scheduled_date": str(p.scheduled_date),
                        "status": p.status,
                    }
                    for p in plans
                ]
            }
        }


def get_training_recommendations(user_id: int, limit: int = 5) -> dict[str, Any]:
    """获取推荐的训练计划"""
    with get_db_session() as db:
        plans = db.query(RecommendedTraining).filter(
            RecommendedTraining.is_active == True
        ).limit(limit).all()
        return {
            "success": True,
            "data": [
                {
                    "plan_name": p.plan_name,
                    "plan_type": p.plan_type,
                    "duration": p.duration,
                    "intensity": p.intensity,
                    "calories_burned": p.calories_burned,
                    "description": p.description,
                    "target_body_type": p.target_body_type,
                }
                for p in plans
            ]
        }


def get_diet_today(user_id: int) -> dict[str, Any]:
    """获取今日饮食记录和统计"""
    with get_db_session() as db:
        meals = db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == date.today()
        ).order_by(DietMeal.meal_time).all()
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        total_calories = sum(m.calories for m in meals)
        total_protein = sum(float(m.protein or 0) for m in meals)
        total_carbs = sum(float(m.carbs or 0) for m in meals)
        total_fat = sum(float(m.fat or 0) for m in meals)
        total_water = sum(m.water or 0 for m in meals)
        goal = settings_obj.calorie_goal if settings_obj else 2000
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_calories": total_calories,
                    "goal_calories": goal,
                    "remaining_calories": goal - total_calories,
                    "total_protein": total_protein,
                    "total_carbs": total_carbs,
                    "total_fat": total_fat,
                    "total_water": total_water,
                },
                "meals": [
                    {
                        "meal_id": m.meal_id,
                        "meal_type": m.meal_type,
                        "meal_name": m.meal_name,
                        "calories": m.calories,
                        "protein": float(m.protein) if m.protein else 0,
                        "carbs": float(m.carbs) if m.carbs else 0,
                        "fat": float(m.fat) if m.fat else 0,
                        "water": m.water if m.water else 0,
                        "meal_time": str(m.meal_time) if m.meal_time else None,
                        "note": m.note,
                    }
                    for m in meals
                ]
            }
        }


def get_diet_weekly_trend(user_id: int) -> dict[str, Any]:
    """获取本周饮食趋势"""
    with get_db_session() as db:
        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        summaries = db.query(DailyDietSummary).filter(
            DailyDietSummary.user_id == user_id,
            DailyDietSummary.summary_date >= week_start
        ).order_by(DailyDietSummary.summary_date).all()
        settings_obj = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        goal = settings_obj.calorie_goal if settings_obj else 2000
        return {
            "success": True,
            "data": {
                "goal_calories": goal,
                "daily_summaries": [
                    {
                        "summary_date": str(s.summary_date),
                        "total_calories": s.total_calories,
                        "total_protein": float(s.total_protein) if s.total_protein else 0,
                        "total_carbs": float(s.total_carbs) if s.total_carbs else 0,
                        "total_fat": float(s.total_fat) if s.total_fat else 0,
                        "protein_goal_met": s.protein_goal_met,
                        "water_goal_met": s.water_goal_met,
                    }
                    for s in summaries
                ]
            }
        }


def get_food_recommendations(user_id: int, limit: int = 5) -> dict[str, Any]:
    """获取推荐的食物"""
    with get_db_session() as db:
        foods = db.query(RecommendedFood).filter(
            RecommendedFood.is_active == True
        ).limit(limit).all()
        return {
            "success": True,
            "data": [
                {
                    "food_name": f.food_name,
                    "calories": f.calories,
                    "protein": float(f.protein) if f.protein else 0,
                    "carbs": float(f.carbs) if f.carbs else 0,
                    "fat": float(f.fat) if f.fat else 0,
                    "reason": f.reason,
                    "suitable_time": f.suitable_time,
                }
                for f in foods
            ]
        }


def get_user_settings(user_id: int) -> dict[str, Any]:
    """获取用户设置"""
    with get_db_session() as db:
        s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not s:
            return {"success": False, "error": "暂无用户设置"}
        return {
            "success": True,
            "data": {
                "calorie_goal": s.calorie_goal,
                "protein_goal": s.protein_goal,
                "carbs_goal": s.carbs_goal,
                "fat_goal": s.fat_goal,
                "water_goal": s.water_goal,
                "weekly_training_goal": s.weekly_training_goal,
                "weight_goal": float(s.weight_goal) if s.weight_goal else None,
            }
        }


def search_foods(user_id: int, keyword: str = "", category: str = "", meal_type: str = "") -> dict[str, Any]:
    """搜索食物数据库"""
    from sqlalchemy import or_
    with get_db_session() as db:
        query = db.query(FoodItem).filter(
            or_(FoodItem.source == "system", FoodItem.user_id == user_id)
        )
        if keyword:
            query = query.filter(FoodItem.name.ilike(f"%{keyword}%"))
        if category:
            query = query.filter(FoodItem.category == category)
        if meal_type:
            query = query.filter(FoodItem.suitable_meals.ilike(f"%{meal_type}%"))
        foods = query.order_by(FoodItem.calories_per_100g).limit(50).all()
        return {
            "success": True,
            "data": [
                {
                    "food_id": f.food_id,
                    "name": f.name,
                    "category": f.category,
                    "source": f.source,
                    "portion_unit": f.portion_unit,
                    "portion_grams": float(f.portion_grams) if f.portion_grams else None,
                    "portion_calories": f.portion_calories,
                    "calories_per_100g": f.calories_per_100g,
                    "protein": float(f.protein) if f.protein else 0,
                    "carbs": float(f.carbs) if f.carbs else 0,
                    "fat": float(f.fat) if f.fat else 0,
                    "suitable_meals": f.suitable_meals,
                }
                for f in foods
            ]
        }


def get_full_overview(user_id: int) -> dict[str, Any]:
    """获取用户综合概览"""
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id, User.deleted_at.is_(None)).first()
        latest = db.query(HealthMetric).filter(HealthMetric.user_id == user_id).order_by(HealthMetric.measure_date.desc()).first()
        today = date.today()
        plans = db.query(TrainingPlan).filter(TrainingPlan.user_id == user_id, TrainingPlan.scheduled_date == today).all()
        meals = db.query(DietMeal).filter(DietMeal.user_id == user_id, DietMeal.meal_date == today).all()
        total_cal = sum(m.calories for m in meals)
        return {
            "success": True,
            "data": {
                "user": {
                    "name": user.name if user else None,
                    "email": user.email if user else None,
                } if user else None,
                "health": {
                    "measure_date": str(latest.measure_date) if latest else None,
                    "weight": float(latest.weight) if latest and latest.weight else None,
                    "bmi": float(latest.bmi) if latest and latest.bmi else None,
                } if latest else None,
                "training": {
                    "today_plan_count": len(plans),
                },
                "diet": {
                    "today_calories": total_cal,
                },
            }
        }
