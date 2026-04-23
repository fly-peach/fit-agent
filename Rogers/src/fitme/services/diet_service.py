"""Diet Service"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta
from ..models import DietMeal, DailyDietSummary, RecommendedFood, UserSettings, StreakStats
from ..schemas.diet import CreateMealRequest, UpdateMealRequest


class DietService:
    """饮食管理服务"""

    @staticmethod
    def get_today_stats(db: Session, user_id: int) -> dict:
        """获取今日饮食统计"""
        today = date.today()

        # 获取今日所有饮食记录
        meals = db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == today
        ).all()

        # 获取用户设置
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        total_calories = sum(m.calories for m in meals)
        total_protein = sum(float(m.protein) for m in meals)
        total_carbs = sum(float(m.carbs) for m in meals)
        total_fat = sum(float(m.fat) for m in meals)
        total_water = sum(m.water for m in meals)

        # 连续记录天数
        streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
        streak_days = streak.diet_streak if streak else 0

        return {
            "calories": total_calories,
            "caloriesGoal": settings.calorie_goal if settings else 2000,
            "remainingCalories": (settings.calorie_goal if settings else 2000) - total_calories,
            "protein": int(total_protein),
            "proteinGoal": settings.protein_goal if settings else 150,
            "carbs": int(total_carbs),
            "carbsGoal": settings.carbs_goal if settings else 250,
            "fat": int(total_fat),
            "fatGoal": settings.fat_goal if settings else 65,
            "water": total_water,
            "waterGoal": settings.water_goal if settings else 2000,
            "streakDays": streak_days,
        }

    @staticmethod
    def get_today_meals(db: Session, user_id: int) -> List[dict]:
        """获取今日饮食记录"""
        today = date.today()

        meals = db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == today
        ).order_by(DietMeal.meal_time).all()

        return [
            {
                "mealId": m.meal_id,
                "mealType": m.meal_type,
                "mealName": m.meal_name,
                "calories": m.calories,
                "protein": float(m.protein),
                "carbs": float(m.carbs),
                "fat": float(m.fat),
                "time": str(m.meal_time),
                "note": m.note,
            }
            for m in meals
        ]

    @staticmethod
    def create_meal(db: Session, user_id: int, data: CreateMealRequest) -> DietMeal:
        """添加饮食记录"""
        from datetime import datetime
        meal_time = datetime.strptime(data.time, "%H:%M").time()

        meal = DietMeal(
            user_id=user_id,
            meal_type=data.mealType,
            meal_name=data.mealName,
            calories=data.calories,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
            water=data.water,
            meal_date=date.today(),
            meal_time=meal_time,
            note=data.note,
        )
        db.add(meal)
        db.commit()
        db.refresh(meal)
        return meal

    @staticmethod
    def update_meal(db: Session, meal_id: int, user_id: int, data: UpdateMealRequest) -> Optional[DietMeal]:
        """更新饮食记录"""
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if meal:
            if data.mealName:
                meal.meal_name = data.mealName
            if data.calories:
                meal.calories = data.calories
            if data.protein:
                meal.protein = data.protein
            if data.carbs:
                meal.carbs = data.carbs
            if data.fat:
                meal.fat = data.fat
            if data.water:
                meal.water = data.water
            db.commit()
            db.refresh(meal)
        return meal

    @staticmethod
    def delete_meal(db: Session, meal_id: int, user_id: int) -> bool:
        """删除饮食记录"""
        meal = db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if meal:
            db.delete(meal)
            db.commit()
            return True
        return False

    @staticmethod
    def get_nutrition_progress(db: Session, user_id: int) -> dict:
        """获取营养摄入进度"""
        stats = DietService.get_today_stats(db, user_id)
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        return {
            "protein": {
                "current": stats["protein"],
                "goal": stats["proteinGoal"],
                "percent": int(stats["protein"] / stats["proteinGoal"] * 100) if stats["proteinGoal"] > 0 else 0,
            },
            "carbs": {
                "current": stats["carbs"],
                "goal": stats["carbsGoal"],
                "percent": int(stats["carbs"] / stats["carbsGoal"] * 100) if stats["carbsGoal"] > 0 else 0,
            },
            "fat": {
                "current": stats["fat"],
                "goal": stats["fatGoal"],
                "percent": int(stats["fat"] / stats["fatGoal"] * 100) if stats["fatGoal"] > 0 else 0,
            },
        }

    @staticmethod
    def get_recommendations(db: Session, limit: int = 5) -> List[RecommendedFood]:
        """获取推荐食物"""
        return db.query(RecommendedFood).filter(
            RecommendedFood.is_active == True
        ).limit(limit).all()

    @staticmethod
    def get_weekly_trend(db: Session, user_id: int) -> dict:
        """获取本周饮食趋势"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        summaries = db.query(DailyDietSummary).filter(
            DailyDietSummary.user_id == user_id,
            DailyDietSummary.summary_date >= week_start
        ).order_by(DailyDietSummary.summary_date).all()

        daily_stats = [
            {
                "day": days_names[(s.summary_date.weekday())],
                "date": s.summary_date,
                "calories": s.total_calories,
                "proteinGoalMet": s.protein_goal_met,
                "waterGoalMet": s.water_goal_met,
            }
            for s in summaries
        ]

        avg_calories = sum(s.total_calories for s in summaries) / len(summaries) if summaries else 0
        protein_goal_days = sum(1 for s in summaries if s.protein_goal_met)
        water_goal_days = sum(1 for s in summaries if s.water_goal_met)

        return {
            "dailyStats": daily_stats,
            "summary": {
                "avgCalories": int(avg_calories),
                "proteinGoalDays": protein_goal_days,
                "waterGoalDays": water_goal_days,
            },
        }