"""Diet Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional

import sys
sys.path.insert(0, "E:/fitagent/rogers/src")
from fitme.utils.database import get_db
from fitme.services.diet_service import DietService
from fitme.schemas.diet import (
    DietStatsResponse,
    DietMealsResponse,
    CreateMealRequest,
    CreateMealResponse,
    UpdateMealRequest,
    NutritionProgressResponse,
    RecommendedFoodResponse,
    WeeklyDietTrendResponse,
)
from fitme.schemas.common import BaseResponse
from fitme.services.auth_service import AuthService

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
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取今日饮食记录"""
    meals = DietService.get_today_meals(db, current_user.user_id)
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