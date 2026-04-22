from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.body_composition import (
    BodyCompositionCompareResponse,
    BodyCompositionCreate,
    BodyCompositionEvaluateResponse,
    BodyCompositionResponse,
    BodyCompositionTrendPoint,
    INDICATOR_GROUPS,
    IndicatorConfigResponse,
)
from app.services.body_composition_evaluator import evaluate_all
from app.services.body_composition_service import BodyCompositionService

router = APIRouter()


@router.post("", response_model=dict[str, Any])
def create_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: BodyCompositionCreate,
) -> Any:
    service = BodyCompositionService(db)
    record = service.create(current_user=current_user, payload=payload)
    return {"code": 0, "message": "success", "data": BodyCompositionResponse.model_validate(record).model_dump()}


@router.get("", response_model=dict[str, Any])
def list_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    assessment_id: int | None = None,
) -> Any:
    service = BodyCompositionService(db)
    records = service.get_multi(
        current_user=current_user,
        from_dt=from_dt,
        to_dt=to_dt,
        assessment_id=assessment_id,
        skip=skip,
        limit=limit,
    )
    return {
        "code": 0,
        "message": "success",
        "data": [BodyCompositionResponse.model_validate(r).model_dump() for r in records],
    }


@router.get("/trend", response_model=dict[str, Any])
def trend_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metric: str,
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    limit: int = 200,
) -> Any:
    service = BodyCompositionService(db)
    points: list[BodyCompositionTrendPoint] = service.trend(
        current_user=current_user, metric=metric, from_dt=from_dt, to_dt=to_dt, limit=limit
    )
    return {"code": 0, "message": "success", "data": [p.model_dump() for p in points]}


@router.get("/compare", response_model=dict[str, Any])
def compare_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    a: int,
    b: int,
) -> Any:
    service = BodyCompositionService(db)
    result: BodyCompositionCompareResponse = service.compare(current_user=current_user, a_id=a, b_id=b)
    return {"code": 0, "message": "success", "data": result.model_dump()}


@router.get("/{id}", response_model=dict[str, Any])
def get_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
) -> Any:
    service = BodyCompositionService(db)
    record = service.get(current_user=current_user, record_id=id)
    return {"code": 0, "message": "success", "data": BodyCompositionResponse.model_validate(record).model_dump()}


@router.get("/evaluate/{id}", response_model=dict[str, Any])
def evaluate_body_composition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
    height_cm: float | None = None,
    actual_age: int | None = None,
) -> Any:
    """体成分综合评估"""
    service = BodyCompositionService(db)
    record = service.get(current_user=current_user, record_id=id)
    result = evaluate_all(record, height_cm=height_cm, actual_age=actual_age)

    # Persist computed fields back to record
    for field in ("body_type", "nutrition_status", "body_age", "subcutaneous_fat",
                   "ideal_weight", "weight_control", "fat_control", "muscle_control",
                   "fat_free_mass", "protein_rate", "fat_burn_hr_low", "fat_burn_hr_high"):
        if field in result and result[field] is not None:
            setattr(record, field, result[field])
    db.commit()
    db.refresh(record)

    response = BodyCompositionEvaluateResponse(**result)
    return {"code": 0, "message": "success", "data": response.model_dump()}


@router.get("/indicator-config", response_model=dict[str, Any])
def get_indicator_config() -> Any:
    """返回指标分组定义 + 状态标签颜色"""
    level_colors = {
        "优": "green", "标准": "blue", "正常": "blue",
        "偏高": "orange", "偏胖": "orange", "轻度肥胖": "orange",
        "不足": "cyan", "偏低": "cyan", "警戒型": "red",
        "减重": "purple", "增重": "purple",
        "良": "green", "过重": "orange", "偏轻": "cyan",
        "偏高": "orange", "减脂": "purple", "增脂": "purple",
        "增肌": "purple", "减肌": "purple",
        "肥胖": "red", "运动型偏胖": "orange", "隐藏型肥胖": "orange",
        "偏瘦": "cyan", "肌肉型": "blue",
        "营养不足": "cyan", "营养均衡": "blue", "营养过剩": "orange",
    }
    config = IndicatorConfigResponse(groups=INDICATOR_GROUPS, level_colors=level_colors)
    return {"code": 0, "message": "success", "data": config.model_dump()}
