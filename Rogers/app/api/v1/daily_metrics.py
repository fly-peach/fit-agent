from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.schemas.daily_metrics import DailyMetricsResponse, DailyMetricsUpsert
from app.services.daily_metrics_service import DailyMetricsService

router = APIRouter()


@router.put("/{record_date}", response_model=dict[str, Any])
def upsert_daily_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_date: date,
    payload: DailyMetricsUpsert,
) -> Any:
    service = DailyMetricsService(DailyMetricsRepository(db))
    record = service.upsert(current_user=current_user, record_date=record_date, payload=payload)
    return {"code": 0, "message": "success", "data": DailyMetricsResponse.model_validate(record).model_dump()}


@router.get("", response_model=dict[str, Any])
def list_daily_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    service = DailyMetricsService(DailyMetricsRepository(db))
    records = service.list(
        current_user=current_user,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    return {
        "code": 0,
        "message": "success",
        "data": [DailyMetricsResponse.model_validate(r).model_dump() for r in records],
    }
