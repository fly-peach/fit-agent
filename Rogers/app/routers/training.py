"""Training Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from src.fitme.utils.database import get_db
from src.fitme.services.training_service import TrainingService
from src.fitme.schemas.training import (
    WeeklyStatsResponse,
    WeeklyScheduleResponse,
    WeeklyProgressResponse,
    RecommendedTrainingResponse,
    CreateTrainingPlanRequest,
    CreateTrainingPlanResponse,
    UpdateTrainingPlanRequest,
    CompleteTrainingRequest,
    DateRangeTrainingTrendResponse,
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/training", tags=["Training"])


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


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
def get_weekly_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取本周训练统计"""
    stats = TrainingService.get_weekly_stats(db, current_user.user_id)
    return WeeklyStatsResponse(data=stats)


@router.get("/schedule/weekly", response_model=WeeklyScheduleResponse)
def get_weekly_schedule(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取本周训练安排"""
    schedule = TrainingService.get_weekly_schedule(db, current_user.user_id)
    return WeeklyScheduleResponse(data=schedule)


@router.get("/progress/weekly", response_model=WeeklyProgressResponse)
def get_weekly_progress(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取本周进度"""
    progress = TrainingService.get_weekly_progress(db, current_user.user_id)
    return WeeklyProgressResponse(data=progress)


@router.get("/recommendations", response_model=RecommendedTrainingResponse)
def get_recommendations(
    db: Session = Depends(get_db)
):
    """获取推荐训练计划"""
    recommendations = TrainingService.get_recommendations(db)
    return RecommendedTrainingResponse(
        data=[
            {
                "recommendId": r.recommend_id,
                "planName": r.plan_name,
                "planType": r.plan_type,
                "duration": r.duration,
                "intensity": r.intensity,
                "caloriesBurn": r.calories_burn,
                "suitability": "high",
            }
            for r in recommendations
        ]
    )


@router.get("/trend/range", response_model=DateRangeTrainingTrendResponse)
def get_date_range_trend(
    start_date: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定日期范围的训练趋势"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
    trend = TrainingService.get_date_range_trend(db, current_user.user_id, start_date, end_date)
    return DateRangeTrainingTrendResponse(data=trend)


@router.post("/plans", response_model=CreateTrainingPlanResponse)
def create_plan(
    data: CreateTrainingPlanRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建训练计划"""
    plan = TrainingService.create_plan(db, current_user.user_id, data)
    return CreateTrainingPlanResponse(
        message="创建成功",
        data={"planId": plan.plan_id}
    )


@router.put("/plans/{planId}", response_model=BaseResponse)
def update_plan(
    planId: int,
    data: UpdateTrainingPlanRequest = Body(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新训练计划"""
    plan = TrainingService.update_plan(db, planId, current_user.user_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="更新成功")


@router.post("/complete/{planId}", response_model=BaseResponse)
def complete_plan(
    planId: int,
    data: CompleteTrainingRequest = Body(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成训练记录"""
    record = TrainingService.complete_plan(db, planId, current_user.user_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="记录成功")


@router.delete("/plans/{planId}", response_model=BaseResponse)
def delete_plan(
    planId: int = Path(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除训练计划"""
    success = TrainingService.delete_plan(db, planId, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="删除成功")