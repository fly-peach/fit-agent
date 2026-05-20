"""Training Router - Dual Database Support"""
import json
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from pydantic import parse_obj_as

from src.fitme.utils.database import get_db, get_base_db, get_user_db
from src.fitme.services.training_service import TrainingService
from src.fitme.schemas.exercise import UpdatePlanExerciseItem, PlanExerciseItemInput
from src.fitme.schemas.training import (
    WeeklyStatsResponse,
    WeeklyScheduleResponse,
    WeeklyProgressResponse,
    RecommendedTraining,
    RecommendedTrainingResponse,
    CreateTrainingPlanRequest,
    CreateTrainingPlanResponse,
    UpdateTrainingPlanRequest,
    CompleteTrainingRequest,
    DateRangeTrainingTrendResponse,
    MonthlyScheduleResponse,
    TrainingSchedule
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.services.auth_service import AuthService
from src.fitme.models.base_db import TrainingCardTemplateSample

router = APIRouter(prefix="/api/training", tags=["Training"])


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


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
def get_weekly_stats(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取本周训练统计"""
    stats = TrainingService.get_weekly_stats(user_db, current_user.user_id)
    return WeeklyStatsResponse(data=stats)


@router.get("/schedule/weekly", response_model=WeeklyScheduleResponse)
def get_weekly_schedule(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取本周训练安排"""
    schedule_dicts = TrainingService.get_weekly_schedule(user_db, current_user.user_id)
    # 将字典列表转换为TrainingSchedule对象列表
    schedule = [parse_obj_as(TrainingSchedule, item) for item in schedule_dicts]
    return WeeklyScheduleResponse(data=schedule)


@router.get("/schedule/monthly", response_model=MonthlyScheduleResponse)
def get_monthly_schedule(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取指定月份的训练安排"""
    schedule = TrainingService.get_monthly_schedule(user_db, current_user.user_id, year, month)
    return MonthlyScheduleResponse(data=schedule)


@router.get("/progress/weekly", response_model=WeeklyProgressResponse)
def get_weekly_progress(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取本周进度"""
    progress = TrainingService.get_weekly_progress(user_db, current_user.user_id)
    return WeeklyProgressResponse(data=progress)


@router.get("/recommendations", response_model=RecommendedTrainingResponse)
def get_recommendations(
    base_db: Session = Depends(get_base_db)
):
    """获取推荐训练计划"""
    recommendations = TrainingService.get_recommendations(base_db)
    return RecommendedTrainingResponse(
        data=[
            RecommendedTraining(
                recommendId=r.recommend_id,
                planName=r.plan_name,
                planType=r.plan_type,
                duration=r.duration,
                intensity=r.intensity,
                caloriesBurn=r.calories_burn,
                suitability="high",
            )
            for r in recommendations
        ]
    )


@router.get("/trend/range", response_model=DateRangeTrainingTrendResponse)
def get_date_range_trend(
    start_date: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期 YYYY-MM-DD"),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取指定日期范围的训练趋势"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
    trend = TrainingService.get_date_range_trend(user_db, current_user.user_id, start_date, end_date)
    return DateRangeTrainingTrendResponse(data=trend)


@router.post("/plans", response_model=CreateTrainingPlanResponse)
def create_plan(
    data: CreateTrainingPlanRequest,
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """创建训练计划"""
    plan = TrainingService.create_plan(user_db, current_user.user_id, data)
    return CreateTrainingPlanResponse(
        message="创建成功",
        data={"planId": plan.plan_id}
    )


@router.put("/plans/{planId}", response_model=BaseResponse)
def update_plan(
    planId: int,
    data: UpdateTrainingPlanRequest = Body(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """更新训练计划"""
    plan = TrainingService.update_plan(user_db, planId, current_user.user_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="更新成功")


@router.post("/complete/{planId}", response_model=BaseResponse)
def complete_plan(
    planId: int,
    data: CompleteTrainingRequest = Body(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """完成训练记录"""
    from datetime import date as _date
    plan = TrainingService.get_plan_by_id(user_db, planId, current_user.user_id)
    if plan and plan.scheduled_date and plan.scheduled_date > _date.today():
        raise HTTPException(status_code=400, detail="计划日期未到，无法打卡")
    record = TrainingService.complete_plan(user_db, planId, current_user.user_id, data)
    if not record:
        plan = TrainingService.get_plan_by_id(user_db, planId, current_user.user_id)
        if plan and plan.status == "completed":
            raise HTTPException(status_code=400, detail="该计划已完成，不能重复打卡")
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="记录成功")


@router.delete("/plans/{planId}", response_model=BaseResponse)
def delete_plan(
    planId: int = Path(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """删除训练计划"""
    success = TrainingService.delete_plan(user_db, planId, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="删除成功")


@router.get("/plans/{planId}/detail")
def get_plan_detail(
    planId: int = Path(...),
    current_user = Depends(get_current_user),
    base_db: Session = Depends(get_base_db),
    user_db: Session = Depends(get_user_db)
):
    """获取训练计划详情（含动作列表）"""
    plan = TrainingService.get_plan_by_id(user_db, planId, current_user.user_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    exercises = TrainingService.get_plan_exercises(base_db, user_db, planId)
    return {
        "code": 200,
        "data": {
            "planId": plan.plan_id,
            "planName": plan.plan_name,
            "planType": plan.plan_type,
            "targetIntensity": plan.target_intensity,
            "estimatedDuration": plan.estimated_duration,
            "scheduledDate": plan.scheduled_date.isoformat() if plan.scheduled_date else None,
            "status": plan.status,
            "note": plan.note,
            "exercises": [e.model_dump() for e in exercises],
        }
    }


@router.put("/plans/exercise/{exerciseId}", response_model=BaseResponse)
def update_plan_exercise(
    exerciseId: int = Path(...),
    data: UpdatePlanExerciseItem = Body(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """更新计划中动作的组数/次数/重量"""
    item = TrainingService.update_plan_exercise(user_db, exerciseId, current_user.user_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="动作不存在")
    return BaseResponse(message="更新成功")


@router.post("/plans/{planId}/exercises", response_model=BaseResponse)
def add_plan_exercise(
    planId: int = Path(...),
    data: PlanExerciseItemInput = Body(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """向计划中新增一个动作"""
    item = TrainingService.add_plan_exercise(user_db, planId, current_user.user_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="计划不存在")
    return BaseResponse(message="添加成功")


@router.delete("/plans/exercise/{exerciseId}", response_model=BaseResponse)
def delete_plan_exercise(
    exerciseId: int = Path(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """从计划中删除一个动作"""
    success = TrainingService.delete_plan_exercise(user_db, exerciseId, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="动作不存在")
    return BaseResponse(message="删除成功")


@router.post("/plans/{planId}/renew", response_model=BaseResponse)
def renew_recurring_plan(
    planId: int = Path(...),
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """循环计划续期：从该组最晚日期之后再生成 8 周"""
    plan_ids = TrainingService.renew_recurring(user_db, planId, current_user.user_id)
    if not plan_ids:
        raise HTTPException(status_code=404, detail="计划不存在或不是循环计划")
    return BaseResponse(message=f"续期成功，已生成 {len(plan_ids)} 周计划")


# ============================================================================
# Training Results Snapshots - 训练成果快照
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional
from src.agents.harness.memory.training_results_storage import (
    save_training_result_snapshot,
    get_training_result_snapshot,
    list_training_result_snapshots,
    update_training_result_snapshot,
    delete_training_result_snapshot,
)


class ArchiveTrainingResultRequest(BaseModel):
    card_html: str = Field(..., description="Agent 生成的完整 HTML 卡片")
    title: str = Field(..., description="快照标题")
    session_id: Optional[str] = Field(None, description="关联的 Agent 会话 ID")
    stats_json: Optional[str] = Field(None, description="统计数据 JSON")
    template_key: Optional[str] = Field(None, description="卡片模板标识")
    period_type: Optional[str] = Field(None, description="周期类型：week/month/custom")
    period_start: Optional[date] = Field(None, description="统计周期开始")
    period_end: Optional[date] = Field(None, description="统计周期结束")
    thumbnail: Optional[str] = Field(None, description="缩略图")


class UpdateTrainingResultRequest(BaseModel):
    title: Optional[str] = Field(None, description="新标题")
    stats_json: Optional[str] = Field(None, description="新统计 JSON")
    thumbnail: Optional[str] = Field(None, description="新缩略图")


def _template_sample_to_dict(record: TrainingCardTemplateSample) -> dict:
    try:
        highlights = json.loads(record.highlights_json or "[]")
    except Exception:
        highlights = []
    return {
        "templateKey": record.template_key,
        "templateName": record.template_name,
        "templateGroup": record.template_group,
        "description": record.description,
        "highlights": highlights,
        "previewHtml": record.preview_html,
        "promptHint": record.prompt_hint,
        "sortOrder": record.sort_order,
    }


@router.get("/result-templates")
def list_result_templates(
    template_group: str = Query("training-results", description="模板分组"),
    base_db: Session = Depends(get_base_db),
):
    """获取训练结果卡片模板样例列表"""
    records = (
        base_db.query(TrainingCardTemplateSample)
        .filter(
            TrainingCardTemplateSample.template_group == template_group,
            TrainingCardTemplateSample.is_active == True,
        )
        .order_by(TrainingCardTemplateSample.sort_order.asc(), TrainingCardTemplateSample.id.asc())
        .all()
    )
    return {
        "code": 200,
        "data": [_template_sample_to_dict(record) for record in records],
    }


@router.get("/result-templates/{templateKey}")
def get_result_template(
    templateKey: str = Path(...),
    base_db: Session = Depends(get_base_db),
):
    """获取单个训练结果卡片模板样例"""
    record = (
        base_db.query(TrainingCardTemplateSample)
        .filter(
            TrainingCardTemplateSample.template_key == templateKey,
            TrainingCardTemplateSample.is_active == True,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {
        "code": 200,
        "data": _template_sample_to_dict(record),
    }


@router.post("/results/archive")
def archive_result(
    data: ArchiveTrainingResultRequest,
    current_user = Depends(get_current_user),
):
    """归档训练成果快照（供 Agent/CLI 调用）"""
    snapshot_id = save_training_result_snapshot(
        user_id=current_user.user_id,
        card_html=data.card_html,
        title=data.title,
        session_id=data.session_id,
        stats_json=data.stats_json,
        template_key=data.template_key,
        period_type=data.period_type,
        period_start=data.period_start,
        period_end=data.period_end,
        thumbnail=data.thumbnail,
    )
    return {
        "code": 200,
        "message": "归档成功",
        "data": {"snapshotId": snapshot_id}
    }


@router.get("/results/list")
def list_results(
    period_type: Optional[str] = Query(None, description="周期类型筛选"),
    session_id: Optional[str] = Query(None, description="Agent 会话 ID 筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回条数"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    current_user = Depends(get_current_user),
):
    """获取训练成果快照列表（不含完整 HTML，减少数据传输）"""
    snapshots = list_training_result_snapshots(
        user_id=current_user.user_id,
        period_type=period_type,
        session_id=session_id,
        limit=limit,
        offset=offset,
        include_html=False,
    )
    return {
        "code": 200,
        "data": snapshots
    }


@router.get("/results/{snapshotId}")
def get_result(
    snapshotId: int = Path(...),
    current_user = Depends(get_current_user),
):
    """获取单个训练成果快照详情（含完整 HTML）"""
    snapshot = get_training_result_snapshot(snapshotId)
    if not snapshot or snapshot["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="快照不存在")
    return {
        "code": 200,
        "data": snapshot
    }


@router.put("/results/{snapshotId}")
def update_result(
    snapshotId: int = Path(...),
    data: UpdateTrainingResultRequest = Body(...),
    current_user = Depends(get_current_user),
):
    """更新训练成果快照信息"""
    # 先验证归属
    snapshot = get_training_result_snapshot(snapshotId)
    if not snapshot or snapshot["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="快照不存在")
    success = update_training_result_snapshot(
        snapshot_id=snapshotId,
        title=data.title,
        stats_json=data.stats_json,
        thumbnail=data.thumbnail,
    )
    if not success:
        raise HTTPException(status_code=404, detail="快照不存在")
    return {
        "code": 200,
        "message": "更新成功"
    }


@router.delete("/results/{snapshotId}")
def delete_result(
    snapshotId: int = Path(...),
    current_user = Depends(get_current_user),
):
    """软删除训练成果快照"""
    # 先验证归属
    snapshot = get_training_result_snapshot(snapshotId)
    if not snapshot or snapshot["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="快照不存在")
    success = delete_training_result_snapshot(snapshotId)
    if not success:
        raise HTTPException(status_code=404, detail="快照不存在")
    return {
        "code": 200,
        "message": "删除成功"
    }
