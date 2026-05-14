"""Diet Router - Dual Database Support"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date


from src.fitme.utils.database import get_db, get_base_db, get_user_db
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
    DietStats,
    DietMeal,
    NutritionProgress,
    WeeklyDietTrend,
    DateRangeDietTrend,
    FoodItem,
    RecommendedFood
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/diet", tags=["Diet"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    user_db: Session = Depends(get_user_db)
):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(user_db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录过期")
    return user


@router.get("/stats/today", response_model=DietStatsResponse)
def get_today_stats(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取今日饮食统计"""
    stats = DietService.get_today_stats(user_db, current_user.user_id)
    # 确保返回的是DietStats模型实例
    return DietStatsResponse(data=DietStats(**stats) if isinstance(stats, dict) else stats)


@router.get("/meals/today", response_model=DietMealsResponse)
def get_today_meals(
    target_date: Optional[date] = Query(None, description="指定日期 YYYY-MM-DD，默认今日"),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取饮食记录（默认今日，支持指定日期）"""
    meals = DietService.get_today_meals(user_db, current_user.user_id, target_date)
    # 确保返回的是DietMeal列表
    return DietMealsResponse(data=[DietMeal(**meal) if isinstance(meal, dict) else meal for meal in meals])


@router.post("/meals", response_model=CreateMealResponse)
def create_meal(
    data: CreateMealRequest,
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """添加饮食记录"""
    meal = DietService.create_meal(user_db, current_user.user_id, data)
    return CreateMealResponse(
        message="添加成功",
        data={"mealId": meal.meal_id}
    )


@router.put("/meals/{mealId}", response_model=BaseResponse)
def update_meal(
    mealId: int,
    data: UpdateMealRequest = Body(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """更新饮食记录"""
    meal = DietService.update_meal(user_db, mealId, current_user.user_id, data)
    if not meal:
        raise HTTPException(status_code=404, detail="记录不存在")
    return BaseResponse(message="更新成功")


@router.delete("/meals/{mealId}", response_model=BaseResponse)
def delete_meal(
    mealId: int = Path(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """删除饮食记录"""
    success = DietService.delete_meal(user_db, mealId, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return BaseResponse(message="删除成功")


@router.get("/nutrition/progress", response_model=NutritionProgressResponse)
def get_nutrition_progress(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取营养摄入进度"""
    progress = DietService.get_nutrition_progress(user_db, current_user.user_id)
    return NutritionProgressResponse(data=NutritionProgress(**progress) if isinstance(progress, dict) else progress)


@router.get("/recommendations", response_model=RecommendedFoodResponse)
def get_recommendations(
    base_db: Session = Depends(get_base_db)
):
    """获取推荐食物"""
    recommendations = DietService.get_recommendations(base_db)
    
    result = []
    for r in recommendations:
        # 使用 getattr 获取对象的实际属性值，解决SQLAlchemy列对象转换问题
        r_dict = {}
        for col in ['recommend_id', 'food_name', 'calories', 'protein', 'reason', 'suitable_time']:
            val = getattr(r, col)
            # 确保获取的是实际值而不是Column对象等
            if val is not None:
                r_dict[col] = val
            else:
                r_dict[col] = None
        
        result.append(RecommendedFood(
            recommendId=r_dict['recommend_id'],
            foodName=r_dict['food_name'],
            calories=r_dict['calories'],
            protein=float(r_dict['protein']) if r_dict['protein'] is not None else None,
            reason=r_dict['reason'],
            suitableTime=r_dict['suitable_time'],
        ))
    
    return RecommendedFoodResponse(data=result)


@router.get("/trend/weekly", response_model=WeeklyDietTrendResponse)
def get_weekly_trend(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取本周饮食趋势"""
    trend = DietService.get_weekly_trend(user_db, current_user.user_id)
    # 确保返回的是WeeklyDietTrend模型实例
    return WeeklyDietTrendResponse(data=WeeklyDietTrend(**trend) if isinstance(trend, dict) else trend)


@router.get("/trend/range", response_model=DateRangeDietTrendResponse)
def get_date_range_trend(
    start_date: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取指定日期范围的饮食趋势"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
    trend = DietService.get_date_range_trend(user_db, current_user.user_id, start_date, end_date)
    # 确保返回的是DateRangeDietTrend模型实例
    return DateRangeDietTrendResponse(data=DateRangeDietTrend(**trend) if isinstance(trend, dict) else trend)


# ---------------------------------------------------------------------------
# 食物数据库
# ---------------------------------------------------------------------------

@router.get("/foods", response_model=FoodItemsResponse)
def search_foods(
    keyword: str = Query("", description="搜索关键词"),
    category: str = Query("", description="分类筛选"),
    meal_type: str = Query("", description="餐次筛选：breakfast/lunch/dinner"),
    current_user = Depends(get_current_user),
    base_db: Session = Depends(get_base_db),
    user_db: Session = Depends(get_user_db)
):
    """搜索食物数据库"""
    foods = DietService.search_foods(base_db, user_db, current_user.user_id, keyword, category, meal_type)
    return FoodItemsResponse(
        data=[
            FoodItem(
                foodId=f["food_id"],
                name=f["name"],
                category=f["category"],
                source=f["source"],
                portionUnit=f["portion_unit"],
                portionGrams=f["portion_grams"],
                portionCalories=f["portion_calories"],
                caloriesPer100g=f["calories_per_100g"],
                calorieLevel=f["calorie_level"],
                protein=float(f["protein"]) if f["protein"] else 0,
                carbs=float(f["carbs"]) if f["carbs"] else 0,
                fat=float(f["fat"]) if f["fat"] else 0,
                suitableMeals=f["suitable_meals"] or "breakfast,lunch,dinner",
            )
            for f in foods
        ]
    )


@router.get("/foods/categories")
def get_food_categories(
    current_user = Depends(get_current_user),
    base_db: Session = Depends(get_base_db),
    user_db: Session = Depends(get_user_db)
):
    """获取食物分类列表"""
    categories = DietService.get_categories(base_db, user_db, current_user.user_id)
    return {"code": 200, "data": categories}


@router.post("/foods", response_model=CreateCustomFoodResponse)
def add_custom_food(
    data: CreateCustomFood,
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """添加自定义食物"""
    food = DietService.create_custom_food(user_db, current_user.user_id, data)
    return CreateCustomFoodResponse(
        data={"foodId": food.food_id}
    )


@router.delete("/foods/{food_id}", response_model=BaseResponse)
def delete_custom_food(
    food_id: int = Path(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """删除自定义食物"""
    success = DietService.delete_custom_food(user_db, current_user.user_id, food_id)
    if not success:
        raise HTTPException(status_code=404, detail="自定义食物不存在")
    return BaseResponse(message="删除成功")