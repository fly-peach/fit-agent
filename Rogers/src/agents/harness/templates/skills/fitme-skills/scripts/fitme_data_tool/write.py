"""Fitme 数据写入操作

所有函数都要求提供有效的 JWT Token。
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, time as dt_time, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.fitme.models import (
    HealthMetric,
    TrainingPlan,
    TrainingRecord,
    DietMeal,
    User,
    UserSettings,
    StreakStats,
    DailyDietSummary,
    FoodItem,
    CustomFoodItem,
)
from src.fitme.utils.database import SessionLocal
from .auth import verify_token, get_db_session


def _auto_update_diet_summary(user_id: int, meal_date: date, db):
    """写入饮食后自动更新 DailyDietSummary 和 StreakStats。"""
    today_meals = db.query(DietMeal).filter(
        DietMeal.user_id == user_id,
        DietMeal.meal_date == meal_date
    ).all()
    user_settings = db.query(UserSettings).filter(
        UserSettings.user_id == user_id
    ).first()
    cal_goal = user_settings.calorie_goal if user_settings else 2000
    protein_goal = user_settings.protein_goal if user_settings else 150
    water_goal = user_settings.water_goal if user_settings else 2000

    total_calories = sum(m.calories for m in today_meals)
    total_protein = sum(float(m.protein or 0) for m in today_meals)
    total_carbs = sum(float(m.carbs or 0) for m in today_meals)
    total_fat = sum(float(m.fat or 0) for m in today_meals)
    total_water = sum(m.water or 0 for m in today_meals)

    summary = db.query(DailyDietSummary).filter(
        DailyDietSummary.user_id == user_id,
        DailyDietSummary.summary_date == meal_date
    ).first()

    if summary:
        summary.total_calories = total_calories
        summary.total_protein = total_protein
        summary.total_carbs = total_carbs
        summary.total_fat = total_fat
        summary.total_water = total_water
        summary.protein_goal_met = total_protein >= protein_goal
        summary.water_goal_met = total_water >= water_goal
        summary.meal_count = len(today_meals)
    else:
        db.add(DailyDietSummary(
            user_id=user_id,
            summary_date=meal_date,
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat,
            total_water=total_water,
            protein_goal_met=total_protein >= protein_goal,
            water_goal_met=total_water >= water_goal,
            meal_count=len(today_meals),
        ))

    streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
    if not streak:
        streak = StreakStats(user_id=user_id)
        db.add(streak)
    if streak.last_diet_date != meal_date:
        yesterday = meal_date - timedelta(days=1)
        if streak.last_diet_date == yesterday:
            streak.diet_streak = (streak.diet_streak or 0) + 1
        else:
            streak.diet_streak = 1
        streak.last_diet_date = meal_date


def _auto_update_training_streak(user_id: int, completed_at: datetime, db):
    """完成训练后自动更新 StreakStats。"""
    completed_date = completed_at.date()
    streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
    if not streak:
        streak = StreakStats(user_id=user_id)
        db.add(streak)
    if streak.last_training_date != completed_date:
        yesterday = completed_date - timedelta(days=1)
        if streak.last_training_date == yesterday:
            streak.training_streak = (streak.training_streak or 0) + 1
        else:
            streak.training_streak = 1
        streak.last_training_date = completed_date


def update_profile(token: str, **kwargs) -> dict[str, Any]:
    user_id, error = verify_token(token)
    if error:
        return error
    assert user_id is not None
    """更新用户基本信息。"""
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {"success": False, "error": "用户不存在"}
        changes = []
        if "name" in kwargs and kwargs["name"]:
            user.name = kwargs["name"]
            changes.append(f"姓名 → {kwargs['name']}")
        if "avatar" in kwargs and kwargs["avatar"]:
            user.avatar = kwargs["avatar"]
            changes.append(f"头像 → {kwargs['avatar']}")
        if not changes:
            return {"success": False, "error": "没有需要更新的字段"}
        db.commit()
        return {"success": True, "data": {"changes": changes}}


def add_health_metric(token: str,
                      weight: float | None = None,
                      height: float | None = None,
                      body_fat: float | None = None,
                      measure_date: str | None = None) -> dict[str, Any]:
    user_id, error = verify_token(token)
    if error:
        return error
    assert user_id is not None
    """添加一条新的健康指标记录。"""
    with get_db_session() as db:
        if weight is None and height is None and body_fat is None:
            return {"success": False, "error": "请至少提供一项指标（体重、身高、体脂）"}
        measure_dt = date.fromisoformat(measure_date) if measure_date else date.today()

        bmi = None
        bmi_status = None
        if weight and height:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 2)
            if bmi < 18.5:
                bmi_status = "under"
            elif bmi > 25:
                bmi_status = "over"
            else:
                bmi_status = "normal"

        metric = HealthMetric(
            user_id=user_id,
            weight=Decimal(str(weight)) if weight else None,
            height=Decimal(str(height)) if height else None,
            body_fat=Decimal(str(body_fat)) if body_fat else None,
            bmi=Decimal(str(bmi)) if bmi else None,
            bmi_status=bmi_status,
            measure_date=measure_dt,
        )
        db.add(metric)
        db.commit()

        return {
            "success": True,
            "data": {
                "record_id": metric.record_id,
                "measure_date": str(measure_dt),
                "weight": weight,
                "height": height,
                "body_fat": body_fat,
                "bmi": bmi,
                "bmi_status": bmi_status,
            }
        }


def update_health_metric(user_id: int,
                         record_id: int,
                         weight: float | None = None,
                         height: float | None = None,
                         body_fat: float | None = None,
                         measure_date: str | None = None) -> dict[str, Any]:
    """更新一条健康指标记录。"""
    with get_db_session() as db:
        metric = db.query(HealthMetric).filter(
            HealthMetric.record_id == record_id,
            HealthMetric.user_id == user_id,
        ).first()
        if not metric:
            return {"success": False, "error": f"健康指标记录 #{record_id} 不存在"}

        changes = []
        if weight is not None:
            metric.weight = Decimal(str(weight))
            changes.append(f"体重 → {weight} kg")
        if height is not None:
            metric.height = Decimal(str(height))
            changes.append(f"身高 → {height} cm")
        if body_fat is not None:
            metric.body_fat = Decimal(str(body_fat))
            changes.append(f"体脂 → {body_fat}%")
        if measure_date is not None:
            metric.measure_date = date.fromisoformat(measure_date)
            changes.append(f"日期 → {measure_date}")
        if not changes:
            return {"success": False, "error": "没有需要更新的字段"}

        # 重算 BMI
        if metric.weight and metric.height:
            bmi = round(float(metric.weight) / ((float(metric.height) / 100) ** 2), 2)
            metric.bmi = Decimal(str(bmi))
            if bmi < 18.5:
                metric.bmi_status = "under"
            elif bmi > 25:
                metric.bmi_status = "over"
            else:
                metric.bmi_status = "normal"

        db.commit()
        return {"success": True, "data": {"record_id": record_id, "changes": changes}}


def delete_health_metric(user_id: int, record_id: int) -> dict[str, Any]:
    """删除一条健康指标记录。"""
    with get_db_session() as db:
        metric = db.query(HealthMetric).filter(
            HealthMetric.record_id == record_id,
            HealthMetric.user_id == user_id,
        ).first()
        if not metric:
            return {"success": False, "error": f"健康指标记录 #{record_id} 不存在"}
        db.delete(metric)
        db.commit()
        return {"success": True, "data": {"record_id": record_id}}


def add_training_plan(user_id: int,
                      plan_name: str,
                      plan_type: str,
                      scheduled_date: str | None = None,
                      estimated_duration: int = 60,
                      target_intensity: str = "medium",
                      note: str | None = None) -> dict[str, Any]:
    """创建一条训练计划。"""
    with get_db_session() as db:
        if not plan_name:
            return {"success": False, "error": "请提供训练计划名称"}
        if plan_type not in ("strength", "cardio", "flexibility"):
            return {"success": False, "error": "计划类型需为 strength / cardio / flexibility 之一"}
        sched_dt = date.fromisoformat(scheduled_date) if scheduled_date else date.today()
        day = sched_dt.isoweekday()

        plan = TrainingPlan(
            user_id=user_id,
            plan_name=plan_name,
            plan_type=plan_type,
            target_intensity=target_intensity,
            estimated_duration=estimated_duration,
            scheduled_date=sched_dt,
            day_of_week=day,
            note=note,
            status="pending",
        )
        db.add(plan)
        db.commit()

        return {
            "success": True,
            "data": {
                "plan_id": plan.plan_id,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "scheduled_date": str(sched_dt),
                "estimated_duration": estimated_duration,
                "target_intensity": target_intensity,
                "note": note,
            }
        }


def complete_training(user_id: int,
                      plan_id: int,
                      actual_duration: int | None = None,
                      actual_intensity: str | None = None,
                      calories_burned: int | None = None,
                      note: str | None = None) -> dict[str, Any]:
    """完成一个训练计划，标记为已完成并记录实际数据。"""
    with get_db_session() as db:
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan:
            return {"success": False, "error": f"训练计划 #{plan_id} 不存在"}
        plan.status = "completed"
        now = datetime.now(timezone.utc)
        db.add(TrainingRecord(
            plan_id=plan_id,
            user_id=user_id,
            actual_duration=actual_duration,
            actual_intensity=actual_intensity,
            calories_burned=calories_burned,
            completed_at=now,
            note=note,
        ))
        _auto_update_training_streak(user_id, now, db)
        db.commit()
        return {
            "success": True,
            "data": {
                "plan_id": plan_id,
                "plan_name": plan.plan_name,
                "status": "completed",
                "actual_duration": actual_duration,
                "actual_intensity": actual_intensity,
                "calories_burned": calories_burned,
                "note": note,
            }
        }


def delete_training_plan(user_id: int, plan_id: int) -> dict[str, Any]:
    """删除一个训练计划。"""
    with get_db_session() as db:
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan:
            return {"success": False, "error": f"训练计划 #{plan_id} 不存在"}
        plan_name = plan.plan_name
        db.delete(plan)
        db.commit()
        return {"success": True, "data": {"plan_id": plan_id, "plan_name": plan_name}}


def add_meal(user_id: int,
             meal_type: str,
             meal_name: str,
             calories: int,
             protein: float = 0,
             carbs: float = 0,
             fat: float = 0,
             water: int = 0,
             meal_date_str: str | None = None,
             meal_time_str: str | None = None,
             note: str | None = None) -> dict[str, Any]:
    """添加饮食记录。"""
    with get_db_session() as db:
        valid_types = ("breakfast", "lunch", "dinner", "snack")
        if meal_type not in valid_types:
            return {"success": False, "error": f"饮食类型需为 {' / '.join(valid_types)} 之一"}
        if not meal_name:
            return {"success": False, "error": "请提供食物名称"}
        if calories <= 0:
            return {"success": False, "error": "热量需大于 0"}

        now = datetime.now(timezone.utc)
        meal_dt = date.fromisoformat(meal_date_str) if meal_date_str else date.today()
        if meal_time_str:
            mt = dt_time.fromisoformat(meal_time_str)
        else:
            mt = now.time()

        meal = DietMeal(
            user_id=user_id,
            meal_type=meal_type,
            meal_name=meal_name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            water=water,
            meal_date=meal_dt,
            meal_time=mt,
            note=note,
        )
        db.add(meal)
        db.flush()
        _auto_update_diet_summary(user_id, meal_dt, db)
        db.commit()

        return {
            "success": True,
            "data": {
                "meal_id": meal.meal_id,
                "meal_type": meal_type,
                "meal_name": meal_name,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "water": water,
                "meal_date": str(meal_dt),
                "meal_time": str(mt) if mt else None,
                "note": note,
            }
        }


def update_meal(user_id: int, meal_id: int, **kwargs) -> dict[str, Any]:
    """更新一条饮食记录。"""
    with get_db_session() as db:
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if not meal:
            return {"success": False, "error": f"饮食记录 #{meal_id} 不存在"}
        changes = []
        if "meal_name" in kwargs and kwargs["meal_name"]:
            meal.meal_name = kwargs["meal_name"]
            changes.append(f"名称 → {kwargs['meal_name']}")
        if "calories" in kwargs and kwargs["calories"]:
            meal.calories = kwargs["calories"]
            changes.append(f"热量 → {kwargs['calories']} kcal")
        if "protein" in kwargs:
            meal.protein = kwargs["protein"]
            changes.append(f"蛋白 → {kwargs['protein']}g")
        if "carbs" in kwargs:
            meal.carbs = kwargs["carbs"]
            changes.append(f"碳水 → {kwargs['carbs']}g")
        if "fat" in kwargs:
            meal.fat = kwargs["fat"]
            changes.append(f"脂肪 → {kwargs['fat']}g")
        if "water" in kwargs:
            meal.water = kwargs["water"]
            changes.append(f"水 → {kwargs['water']}ml")
        if not changes:
            return {"success": False, "error": "没有需要更新的字段"}
        db.commit()
        return {"success": True, "data": {"meal_id": meal_id, "changes": changes}}


def delete_meal(user_id: int, meal_id: int) -> dict[str, Any]:
    """删除一条饮食记录。"""
    with get_db_session() as db:
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if not meal:
            return {"success": False, "error": f"饮食记录 #{meal_id} 不存在"}
        meal_name = meal.meal_name
        meal_date = meal.meal_date
        db.delete(meal)
        db.flush()
        _auto_update_diet_summary(user_id, meal_date, db)
        db.commit()
        return {"success": True, "data": {"meal_id": meal_id, "meal_name": meal_name}}


def add_custom_food(user_id: int,
                    name: str,
                    category: str,
                    portion_calories: int,
                    calories_per_100g: int,
                    portion_unit: str | None = None,
                    portion_grams: float | None = None,
                    calorie_level: str | None = None,
                    protein: float = 0,
                    carbs: float = 0,
                    fat: float = 0,
                    suitable_meals: str = "breakfast,lunch,dinner") -> dict[str, Any]:
    """添加自定义食物到用户个人食物库。"""
    with get_db_session() as db:
        if not name:
            return {"success": False, "error": "请提供食物名称"}
        if not category:
            return {"success": False, "error": "请提供食物分类"}
        if portion_calories <= 0:
            return {"success": False, "error": "单份热量需大于 0"}
        if calories_per_100g <= 0:
            return {"success": False, "error": "每100克热量需大于 0"}

        food = FoodItem(
            user_id=user_id,
            source="custom",
            name=name,
            category=category,
            portion_unit=portion_unit,
            portion_grams=portion_grams,
            portion_calories=portion_calories,
            calories_per_100g=calories_per_100g,
            calorie_level=calorie_level,
            protein=protein,
            carbs=carbs,
            fat=fat,
            suitable_meals=suitable_meals,
        )
        db.add(food)
        db.commit()

        return {
            "success": True,
            "data": {
                "food_id": food.food_id,
                "name": name,
                "category": category,
                "source": "custom",
            }
        }


def update_custom_food(user_id: int,
                       food_id: int,
                       **kwargs) -> dict[str, Any]:
    """更新自定义食物。"""
    with get_db_session() as db:
        food = db.query(CustomFoodItem).filter(
            CustomFoodItem.food_id == food_id,
            CustomFoodItem.user_id == user_id,
        ).first()
        if not food:
            return {"success": False, "error": f"自定义食物 #{food_id} 不存在"}

        changes = []
        if "name" in kwargs and kwargs["name"]:
            food.name = kwargs["name"]
            changes.append(f"名称 → {kwargs['name']}")
        if "category" in kwargs and kwargs["category"]:
            food.category = kwargs["category"]
            changes.append(f"分类 → {kwargs['category']}")
        if "portion_calories" in kwargs and kwargs["portion_calories"] is not None:
            food.portion_calories = kwargs["portion_calories"]
            changes.append(f"单份热量 → {kwargs['portion_calories']} kcal")
        if "calories_per_100g" in kwargs and kwargs["calories_per_100g"] is not None:
            food.calories_per_100g = kwargs["calories_per_100g"]
            changes.append(f"每100g热量 → {kwargs['calories_per_100g']} kcal")
        if "portion_unit" in kwargs and kwargs["portion_unit"]:
            food.portion_unit = kwargs["portion_unit"]
            changes.append(f"单位 → {kwargs['portion_unit']}")
        if "portion_grams" in kwargs and kwargs["portion_grams"] is not None:
            food.portion_grams = int(kwargs["portion_grams"])
            changes.append(f"单份克数 → {kwargs['portion_grams']}g")
        if "calorie_level" in kwargs and kwargs["calorie_level"]:
            food.calorie_level = kwargs["calorie_level"]
            changes.append(f"热量等级 → {kwargs['calorie_level']}")
        if "protein" in kwargs and kwargs["protein"] is not None:
            food.protein = kwargs["protein"]
            changes.append(f"蛋白 → {kwargs['protein']}g")
        if "carbs" in kwargs and kwargs["carbs"] is not None:
            food.carbs = kwargs["carbs"]
            changes.append(f"碳水 → {kwargs['carbs']}g")
        if "fat" in kwargs and kwargs["fat"] is not None:
            food.fat = kwargs["fat"]
            changes.append(f"脂肪 → {kwargs['fat']}g")
        if "suitable_meals" in kwargs and kwargs["suitable_meals"]:
            food.suitable_meals = kwargs["suitable_meals"]
            changes.append(f"适合餐次 → {kwargs['suitable_meals']}")
        if not changes:
            return {"success": False, "error": "没有需要更新的字段"}
        db.commit()
        return {"success": True, "data": {"food_id": food_id, "changes": changes}}


def update_settings(user_id: int, **kwargs) -> dict[str, Any]:
    """更新用户设置（目标值等）。"""
    with get_db_session() as db:
        s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not s:
            return {"success": False, "error": "暂无用户设置，请先初始化设置"}
        field_map = {
            "calorie_goal": ("calorie_goal", int),
            "protein_goal": ("protein_goal", int),
            "carbs_goal": ("carbs_goal", int),
            "fat_goal": ("fat_goal", int),
            "water_goal": ("water_goal", int),
            "weight_goal": ("weight_goal", float),
            "weekly_training_goal": ("weekly_training_goal", int),
        }
        changes = []
        for key, (field, _) in field_map.items():
            if key in kwargs and kwargs[key] is not None:
                old_val = getattr(s, field)
                setattr(s, field, kwargs[key])
                changes.append(f"{key} {old_val} → {kwargs[key]}")
        if not changes:
            return {"success": False, "error": "没有需要更新的设置项"}
        db.commit()
        return {"success": True, "data": {"changes": changes}}
