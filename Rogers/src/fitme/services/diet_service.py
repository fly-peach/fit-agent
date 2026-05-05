"""Diet Service - Dual Database Support"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import date, timedelta
from ..models import (
    DietMeal, DailyDietSummary, RecommendedFood, UserSettings, StreakStats,
    FoodItem, CustomFoodItem
)
from ..schemas.diet import CreateMealRequest, UpdateMealRequest, CreateCustomFood


class DietService:
    """饮食管理服务 - 双数据库
    - base_db: FoodItem, RecommendedFood
    - user_db: DietMeal, DailyDietSummary, UserSettings, StreakStats, CustomFoodItem
    """

    @staticmethod
    def get_today_stats(user_db: Session, user_id: int) -> dict:
        """获取今日饮食统计"""
        today = date.today()

        # 获取今日所有饮食记录
        meals = user_db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == today
        ).all()

        # 获取用户设置
        settings = user_db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        total_calories = sum(m.calories for m in meals)
        total_protein = sum(float(m.protein) for m in meals)
        total_carbs = sum(float(m.carbs) for m in meals)
        total_fat = sum(float(m.fat) for m in meals)
        total_water = sum(m.water for m in meals)

        # 连续记录天数
        streak = user_db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
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
    def get_today_meals(user_db: Session, user_id: int, target_date: Optional[date] = None) -> List[dict]:
        """获取饮食记录（默认今日，支持指定日期）"""
        if target_date is None:
            target_date = date.today()

        meals = user_db.query(DietMeal).filter(
            DietMeal.user_id == user_id,
            DietMeal.meal_date == target_date
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
    def create_meal(user_db: Session, user_id: int, data: CreateMealRequest) -> DietMeal:
        """添加饮食记录"""
        from datetime import datetime
        meal_time = datetime.strptime(data.time, "%H:%M").time()
        meal_date = date.fromisoformat(data.mealDate) if data.mealDate else date.today()

        meal = DietMeal(
            user_id=user_id,
            meal_type=data.mealType,
            meal_name=data.mealName,
            calories=data.calories,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
            water=data.water,
            meal_date=meal_date,
            meal_time=meal_time,
            note=data.note,
        )
        user_db.add(meal)
        user_db.commit()
        user_db.refresh(meal)
        return meal

    @staticmethod
    def update_meal(user_db: Session, meal_id: int, user_id: int, data: UpdateMealRequest) -> Optional[DietMeal]:
        """更新饮食记录"""
        meal = user_db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if meal:
            if data.mealName is not None:
                meal.meal_name = data.mealName
            if data.calories is not None:
                meal.calories = data.calories
            if data.protein is not None:
                meal.protein = data.protein
            if data.carbs is not None:
                meal.carbs = data.carbs
            if data.fat is not None:
                meal.fat = data.fat
            if data.water is not None:
                meal.water = data.water
            user_db.commit()
            user_db.refresh(meal)
        return meal

    @staticmethod
    def delete_meal(user_db: Session, meal_id: int, user_id: int) -> bool:
        """删除饮食记录"""
        meal = user_db.query(DietMeal).filter(
            DietMeal.meal_id == meal_id,
            DietMeal.user_id == user_id
        ).first()
        if meal:
            user_db.delete(meal)
            user_db.commit()
            return True
        return False

    @staticmethod
    def get_nutrition_progress(user_db: Session, user_id: int) -> dict:
        """获取营养摄入进度"""
        stats = DietService.get_today_stats(user_db, user_id)
        settings = user_db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

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
    def get_recommendations(base_db: Session, limit: int = 5) -> List[RecommendedFood]:
        """获取推荐食物"""
        return base_db.query(RecommendedFood).filter(
            RecommendedFood.is_active == True
        ).limit(limit).all()

    @staticmethod
    def get_weekly_trend(user_db: Session, user_id: int) -> dict:
        """获取本周饮食趋势"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        summaries = user_db.query(DailyDietSummary).filter(
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

    @staticmethod
    def get_date_range_trend(user_db: Session, user_id: int, start_date: date, end_date: date) -> dict:
        """获取日期范围内的每日饮食趋势"""
        settings = user_db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        summaries = user_db.query(DailyDietSummary).filter(
            DailyDietSummary.user_id == user_id,
            DailyDietSummary.summary_date >= start_date,
            DailyDietSummary.summary_date <= end_date
        ).order_by(DailyDietSummary.summary_date).all()

        daily_stats = [
            {
                "date": s.summary_date,
                "calories": s.total_calories,
                "protein": float(s.total_protein),
                "carbs": float(s.total_carbs),
                "fat": float(s.total_fat),
                "water": s.total_water,
                "proteinGoalMet": s.protein_goal_met,
                "waterGoalMet": s.water_goal_met,
                "mealCount": s.meal_count,
            }
            for s in summaries
        ]

        goals = {
            "caloriesGoal": settings.calorie_goal if settings else 2000,
            "proteinGoal": settings.protein_goal if settings else 150,
            "carbsGoal": settings.carbs_goal if settings else 250,
            "fatGoal": settings.fat_goal if settings else 65,
            "waterGoal": settings.water_goal if settings else 2000,
        }

        return {"dailyStats": daily_stats, "goals": goals}

    # -----------------------------------------------------------------------
    # 食物数据库
    # -----------------------------------------------------------------------

    @staticmethod
    def search_foods(base_db: Session, user_db: Session, user_id: int, keyword: str = "", category: str = "", meal_type: str = "", limit: int = 200) -> List[dict]:
        """搜索食物（系统 + 用户自定义） - 返回统一格式的字典列表"""
        # 搜索系统食物
        system_query = base_db.query(FoodItem).filter(FoodItem.source == "system")
        if keyword:
            system_query = system_query.filter(FoodItem.name.ilike(f"%{keyword}%"))
        if category:
            system_query = system_query.filter(FoodItem.category == category)
        if meal_type:
            system_query = system_query.filter(FoodItem.suitable_meals.like(f"%{meal_type}%"))
        system_foods = system_query.order_by(FoodItem.calories_per_100g).limit(limit).all()

        # 搜索自定义食物
        custom_query = user_db.query(CustomFoodItem).filter(CustomFoodItem.user_id == user_id)
        if keyword:
            custom_query = custom_query.filter(CustomFoodItem.name.ilike(f"%{keyword}%"))
        if category:
            custom_query = custom_query.filter(CustomFoodItem.category == category)
        if meal_type:
            custom_query = custom_query.filter(CustomFoodItem.suitable_meals.like(f"%{meal_type}%"))
        custom_foods = custom_query.order_by(CustomFoodItem.calories_per_100g).limit(limit).all()

        # 统一格式并合并
        results = []
        for f in system_foods:
            results.append({
                "food_id": f.food_id,
                "name": f.name,
                "category": f.category,
                "source": f.source,
                "portion_unit": f.portion_unit,
                "portion_grams": f.portion_grams,
                "portion_calories": f.portion_calories,
                "calories_per_100g": f.calories_per_100g,
                "calorie_level": f.calorie_level,
                "protein": f.protein,
                "carbs": f.carbs,
                "fat": f.fat,
                "suitable_meals": f.suitable_meals or "breakfast,lunch,dinner",
            })
        for f in custom_foods:
            results.append({
                "food_id": f.food_id,
                "name": f.name,
                "category": f.category,
                "source": "custom",
                "portion_unit": f.portion_unit,
                "portion_grams": f.portion_grams,
                "portion_calories": f.portion_calories,
                "calories_per_100g": f.calories_per_100g,
                "calorie_level": f.calorie_level,
                "protein": f.protein,
                "carbs": f.carbs,
                "fat": f.fat,
                "suitable_meals": f.suitable_meals or "breakfast,lunch,dinner",
            })
        # 按卡路里排序
        results.sort(key=lambda x: x["calories_per_100g"])
        return results[:limit]

    @staticmethod
    def get_food_by_id(base_db: Session, user_db: Session, user_id: int, food_id: int) -> Optional[dict]:
        """获取指定食物 - 返回统一格式的字典"""
        # 先查系统食物
        food = base_db.query(FoodItem).filter(
            FoodItem.food_id == food_id,
            FoodItem.source == "system"
        ).first()
        if food:
            return {
                "food_id": food.food_id,
                "name": food.name,
                "category": food.category,
                "source": food.source,
                "portion_unit": food.portion_unit,
                "portion_grams": food.portion_grams,
                "portion_calories": food.portion_calories,
                "calories_per_100g": food.calories_per_100g,
                "calorie_level": food.calorie_level,
                "protein": food.protein,
                "carbs": food.carbs,
                "fat": food.fat,
                "suitable_meals": food.suitable_meals or "breakfast,lunch,dinner",
            }
        # 再查自定义食物
        custom_food = user_db.query(CustomFoodItem).filter(
            CustomFoodItem.food_id == food_id,
            CustomFoodItem.user_id == user_id
        ).first()
        if custom_food:
            return {
                "food_id": custom_food.food_id,
                "name": custom_food.name,
                "category": custom_food.category,
                "source": "custom",
                "portion_unit": custom_food.portion_unit,
                "portion_grams": custom_food.portion_grams,
                "portion_calories": custom_food.portion_calories,
                "calories_per_100g": custom_food.calories_per_100g,
                "calorie_level": custom_food.calorie_level,
                "protein": custom_food.protein,
                "carbs": custom_food.carbs,
                "fat": custom_food.fat,
                "suitable_meals": custom_food.suitable_meals or "breakfast,lunch,dinner",
            }
        return None

    @staticmethod
    def get_categories(base_db: Session, user_db: Session, user_id: int) -> List[str]:
        """获取所有食物分类"""
        system_cats = base_db.query(FoodItem.category).filter(
            FoodItem.source == "system"
        ).distinct().all()
        custom_cats = user_db.query(CustomFoodItem.category).filter(
            CustomFoodItem.user_id == user_id
        ).distinct().all()

        categories = set()
        for r in system_cats:
            if r[0]:
                categories.add(r[0])
        for r in custom_cats:
            if r[0]:
                categories.add(r[0])
        return sorted(categories)

    @staticmethod
    def create_custom_food(user_db: Session, user_id: int, data: CreateCustomFood) -> CustomFoodItem:
        """添加自定义食物"""
        food = CustomFoodItem(
            user_id=user_id,
            name=data.name,
            category=data.category,
            portion_unit=data.portionUnit,
            portion_grams=data.portionGrams,
            portion_calories=data.portionCalories,
            calories_per_100g=data.caloriesPer100g,
            calorie_level=data.calorieLevel,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
        )
        user_db.add(food)
        user_db.commit()
        user_db.refresh(food)
        return food

    @staticmethod
    def delete_custom_food(user_db: Session, user_id: int, food_id: int) -> bool:
        """删除自定义食物"""
        food = user_db.query(CustomFoodItem).filter(
            CustomFoodItem.food_id == food_id,
            CustomFoodItem.user_id == user_id
        ).first()
        if food:
            user_db.delete(food)
            user_db.commit()
            return True
        return False
