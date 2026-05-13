"""Fitme 饮食数据工具。"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.fitme.schemas.diet import CreateCustomFood
from src.fitme.services.diet_service import DietService
from src.fitme.utils.database import BaseDBContext, UserDBContext


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _serialize_food(food: dict[str, Any]) -> dict[str, Any]:
    return {
        "food_id": food["food_id"],
        "name": food["name"],
        "category": food["category"],
        "source": food["source"],
        "portion_unit": food["portion_unit"],
        "portion_grams": food["portion_grams"],
        "portion_calories": int(food["portion_calories"]) if food["portion_calories"] is not None else None,
        "calories_per_100g": int(food["calories_per_100g"]) if food["calories_per_100g"] is not None else None,
        "calorie_level": food["calorie_level"],
        "protein": _to_float(food["protein"]),
        "carbs": _to_float(food["carbs"]),
        "fat": _to_float(food["fat"]),
        "suitable_meals": food["suitable_meals"] or "breakfast,lunch,dinner",
    }


def get_diet_today(user_id: int) -> dict[str, Any]:
    """获取今日饮食总览。"""
    with UserDBContext() as user_db:
        stats = DietService.get_today_stats(user_db, user_id)
        meals = DietService.get_today_meals(user_db, user_id)
        progress = DietService.get_nutrition_progress(user_db, user_id)
        return {
            "success": True,
            "data": {
                "summary": stats,
                "nutrition_progress": progress,
                "meals": meals,
            },
        }


def get_diet_weekly_trend(user_id: int) -> dict[str, Any]:
    """获取本周饮食趋势。"""
    with UserDBContext() as user_db:
        return {
            "success": True,
            "data": DietService.get_weekly_trend(user_db, user_id),
        }


def get_nutrition_progress(user_id: int) -> dict[str, Any]:
    """获取今日宏量营养进度。"""
    with UserDBContext() as user_db:
        return {
            "success": True,
            "data": DietService.get_nutrition_progress(user_db, user_id),
        }


def get_food_recommendations(user_id: int, limit: int = 5) -> dict[str, Any]:
    """获取推荐食物。"""
    del user_id  # recommendations do not depend on user-specific rows today.
    with BaseDBContext() as base_db:
        foods = DietService.get_recommendations(base_db, limit=limit)
        return {
            "success": True,
            "data": [
                {
                    "food_name": f.food_name,
                    "calories": f.calories,
                    "protein": _to_float(f.protein),
                    "carbs": _to_float(f.carbs),
                    "fat": _to_float(f.fat),
                    "reason": f.reason,
                    "suitable_time": f.suitable_time,
                    "category": f.category,
                }
                for f in foods
            ],
        }


def search_foods(
    user_id: int,
    keyword: str = "",
    category: str = "",
    meal_type: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """搜索食物库（系统 + 自定义）。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        foods = DietService.search_foods(
            base_db,
            user_db,
            user_id=user_id,
            keyword=keyword,
            category=category,
            meal_type=meal_type,
            limit=limit,
        )
        return {
            "success": True,
            "data": [_serialize_food(food) for food in foods],
        }


def get_food_categories(user_id: int) -> dict[str, Any]:
    """获取食物分类。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        return {
            "success": True,
            "data": DietService.get_categories(base_db, user_db, user_id),
        }


def add_custom_food(
    user_id: int,
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
    suitable_meals: str = "breakfast,lunch,dinner",
) -> dict[str, Any]:
    """添加用户自定义食物。"""
    data = CreateCustomFood(
        name=name,
        category=category,
        portionUnit=portion_unit,
        portionGrams=int(portion_grams) if portion_grams is not None else None,
        portionCalories=portion_calories,
        caloriesPer100g=calories_per_100g,
        calorieLevel=calorie_level,
        protein=protein,
        carbs=carbs,
        fat=fat,
    )
    with UserDBContext() as user_db:
        food = DietService.create_custom_food(user_db, user_id, data)
        # service schema does not expose suitableMeals yet; return caller input for transparency.
        return {
            "success": True,
            "data": {
                "food_id": food.food_id,
                "name": food.name,
                "category": food.category,
                "source": "custom",
                "suitable_meals": suitable_meals,
            },
        }


def delete_custom_food(user_id: int, food_id: int) -> dict[str, Any]:
    """删除用户自定义食物。"""
    with UserDBContext() as user_db:
        success = DietService.delete_custom_food(user_db, user_id, food_id)
        if not success:
            return {"success": False, "error": "食物不存在或无权删除"}
        return {"success": True, "data": {"food_id": food_id}}


def analyze_diet_gap(user_id: int, meal_type: str = "", limit: int = 5) -> dict[str, Any]:
    """分析今日营养缺口并给出补充建议。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        stats = DietService.get_today_stats(user_db, user_id)
        progress = DietService.get_nutrition_progress(user_db, user_id)
        foods = DietService.search_foods(
            base_db,
            user_db,
            user_id=user_id,
            meal_type=meal_type,
            limit=120,
        )

    deficits = {
        "calories": max(0, stats["remainingCalories"]),
        "protein": max(0, stats["proteinGoal"] - stats["protein"]),
        "carbs": max(0, stats["carbsGoal"] - stats["carbs"]),
        "fat": max(0, stats["fatGoal"] - stats["fat"]),
        "water": max(0, stats["waterGoal"] - stats["water"]),
    }

    foods_with_macro = [
        food for food in foods
        if _to_float(food["protein"]) > 0
        or _to_float(food["carbs"]) > 0
        or _to_float(food["fat"]) > 0
    ]
    has_macro_catalog = bool(foods_with_macro)

    macro_ratios = {
        "protein": 100 - progress["protein"]["percent"],
        "carbs": 100 - progress["carbs"]["percent"],
        "fat": 100 - progress["fat"]["percent"],
    }
    priority = max(macro_ratios, key=lambda x: macro_ratios[x])
    if not has_macro_catalog:
        priority = "calories"

    def score(food: dict[str, Any]) -> float:
        protein = _to_float(food["protein"])
        carbs = _to_float(food["carbs"])
        fat = _to_float(food["fat"])
        portion_calories = int(food["portion_calories"] or 0)
        result = 0.0
        result += protein * (3.0 if deficits["protein"] > 0 else 1.0)
        result += carbs * (1.8 if deficits["carbs"] > 0 else 0.6)
        result += fat * (1.2 if deficits["fat"] > 0 else 0.4)
        if deficits["calories"] > 0:
            result += min(portion_calories, deficits["calories"]) / 40
        else:
            result -= portion_calories / 25
        if priority == "protein":
            result += protein * 1.5
        if priority == "carbs":
            result += carbs
        if priority == "fat":
            result += fat
        return result

    candidates = sorted(foods, key=score, reverse=True)[:limit]
    suggestions = []
    for food in candidates:
        reasons = []
        protein = _to_float(food["protein"])
        carbs = _to_float(food["carbs"])
        fat = _to_float(food["fat"])
        if deficits["protein"] > 0 and protein >= 10:
            reasons.append(f"补蛋白 {protein:.0f}g")
        if deficits["carbs"] > 0 and carbs >= 15:
            reasons.append(f"补碳水 {carbs:.0f}g")
        if deficits["fat"] > 0 and fat >= 8:
            reasons.append(f"补脂肪 {fat:.0f}g")
        if deficits["calories"] > 0:
            reasons.append(f"单份约 {int(food['portion_calories'] or 0)} kcal")
        if not has_macro_catalog:
            reasons.append("基础食物库暂无可靠宏量营养字段，按热量与餐次适配推荐")
        suggestions.append({
            **_serialize_food(food),
            "reason": "，".join(reasons) if reasons else "适合作为当前饮食补充",
        })

    return {
        "success": True,
        "data": {
            "meal_type": meal_type or "all",
            "current": {
                "calories": stats["calories"],
                "protein": stats["protein"],
                "carbs": stats["carbs"],
                "fat": stats["fat"],
                "water": stats["water"],
            },
            "goals": {
                "calories": stats["caloriesGoal"],
                "protein": stats["proteinGoal"],
                "carbs": stats["carbsGoal"],
                "fat": stats["fatGoal"],
                "water": stats["waterGoal"],
            },
            "deficits": deficits,
            "priority": priority,
            "data_quality": {
                "has_macro_catalog": has_macro_catalog,
                "macro_coverage_count": len(foods_with_macro),
                "note": (
                    "基础食物库缺少宏量营养数据，本次建议按热量与餐次优先。"
                    if not has_macro_catalog
                    else "基础食物库包含宏量营养数据，可按缺口做更细粒度推荐。"
                ),
            },
            "suggestions": suggestions,
        },
    }
