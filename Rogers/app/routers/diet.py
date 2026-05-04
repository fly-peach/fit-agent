"""Diet Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date


from src.fitme.utils.database import get_db
from src.fitme.services.diet_service import DietService
from src.fitme.schemas.diet import (
    DietStatsResponse,
    DietMealsResponse,
    CreateMealRequest,
    CreateMealResponse,
    UpdateMealRequest,
    NutritionProgressResponse,
    RecommendedFoodResponse,
    WeeklyDietTrendResponse,
    DateRangeDietTrendResponse,
    FoodItemsResponse,
    CreateCustomFood,
    CreateCustomFoodResponse,
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/diet", tags=["Diet"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录过期")
    return user


@router.get("/stats/today", response_model=DietStatsResponse)
def get_today_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取今日饮食统计"""
    stats = DietService.get_today_stats(db, current_user.user_id)
    return DietStatsResponse(data=stats)


@router.get("/meals/today", response_model=DietMealsResponse)
def get_today_meals(
    target_date: Optional[date] = Query(None, description="指定日期 YYYY-MM-DD，默认今日"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取饮食记录（默认今日，支持指定日期）"""
    meals = DietService.get_today_meals(db, current_user.user_id, target_date)
    return DietMealsResponse(data=meals)


@router.post("/meals", response_model=CreateMealResponse)
def create_meal(
    data: CreateMealRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加饮食记录"""
    meal = DietService.create_meal(db, current_user.user_id, data)
    return CreateMealResponse(
        message="添加成功",
        data={"mealId": meal.meal_id}
    )


@router.put("/meals/{mealId}", response_model=BaseResponse)
def update_meal(
    mealId: int,
    data: UpdateMealRequest = Body(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新饮食记录"""
    meal = DietService.update_meal(db, mealId, current_user.user_id, data)
    if not meal:
        raise HTTPException(status_code=404, detail="记录不存在")
    return BaseResponse(message="更新成功")


@router.delete("/meals/{mealId}", response_model=BaseResponse)
def delete_meal(
    mealId: int = Path(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除饮食记录"""
    success = DietService.delete_meal(db, mealId, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return BaseResponse(message="删除成功")


@router.get("/nutrition/progress", response_model=NutritionProgressResponse)
def get_nutrition_progress(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取营养摄入进度"""
    progress = DietService.get_nutrition_progress(db, current_user.user_id)
    return NutritionProgressResponse(data=progress)


@router.get("/recommendations", response_model=RecommendedFoodResponse)
def get_recommendations(
    db: Session = Depends(get_db)
):
    """获取推荐食物"""
    recommendations = DietService.get_recommendations(db)
    return RecommendedFoodResponse(
        data=[
            {
                "recommendId": r.recommend_id,
                "foodName": r.food_name,
                "calories": r.calories,
                "protein": float(r.protein) if r.protein else None,
                "reason": r.reason,
                "suitableTime": r.suitable_time,
            }
            for r in recommendations
        ]
    )


@router.get("/trend/weekly", response_model=WeeklyDietTrendResponse)
def get_weekly_trend(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取本周饮食趋势"""
    trend = DietService.get_weekly_trend(db, current_user.user_id)
    return WeeklyDietTrendResponse(data=trend)


@router.get("/trend/range", response_model=DateRangeDietTrendResponse)
def get_date_range_trend(
    start_date: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定日期范围的饮食趋势"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
    trend = DietService.get_date_range_trend(db, current_user.user_id, start_date, end_date)
    return DateRangeDietTrendResponse(data=trend)


# ---------------------------------------------------------------------------
# 食物数据库
# ---------------------------------------------------------------------------

@router.get("/foods", response_model=FoodItemsResponse)
def search_foods(
    keyword: str = Query("", description="搜索关键词"),
    category: str = Query("", description="分类筛选"),
    meal_type: str = Query("", description="餐次筛选：breakfast/lunch/dinner"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索食物数据库"""
    foods = DietService.search_foods(db, current_user.user_id, keyword, category, meal_type)
    return FoodItemsResponse(
        data=[
            {
                "foodId": f.food_id,
                "name": f.name,
                "category": f.category,
                "source": f.source,
                "portionUnit": f.portion_unit,
                "portionGrams": f.portion_grams,
                "portionCalories": f.portion_calories,
                "caloriesPer100g": f.calories_per_100g,
                "calorieLevel": f.calorie_level,
                "protein": float(f.protein) if f.protein else 0,
                "carbs": float(f.carbs) if f.carbs else 0,
                "fat": float(f.fat) if f.fat else 0,
                "suitableMeals": f.suitable_meals or "breakfast,lunch,dinner",
            }
            for f in foods
        ]
    )


@router.get("/foods/categories")
def get_food_categories(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取食物分类列表"""
    categories = DietService.get_categories(db, current_user.user_id)
    return {"code": 200, "data": categories}


@router.post("/foods", response_model=CreateCustomFoodResponse)
def add_custom_food(
    data: CreateCustomFood,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加自定义食物"""
    food = DietService.create_custom_food(db, current_user.user_id, data)
    return CreateCustomFoodResponse(
        data={"foodId": food.food_id}
    )


@router.delete("/foods/{foodId}", response_model=BaseResponse)
def delete_custom_food(
    foodId: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除自定义食物"""
    success = DietService.delete_custom_food(db, current_user.user_id, foodId)
    if not success:
        raise HTTPException(status_code=404, detail="食物不存在或无权删除")
    return BaseResponse(message="删除成功")