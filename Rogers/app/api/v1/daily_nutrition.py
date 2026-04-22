from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.schemas.daily_nutrition import DailyNutritionResponse, DailyNutritionUpsert
from app.services.daily_nutrition_service import DailyNutritionService

router = APIRouter()


@router.put("/{record_date}", response_model=dict[str, Any])
def upsert_daily_nutrition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_date: date,
    payload: DailyNutritionUpsert,
) -> Any:
    service = DailyNutritionService(DailyNutritionRepository(db))
    record = service.upsert(current_user=current_user, record_date=record_date, payload=payload)
    return {"code": 0, "message": "success", "data": DailyNutritionResponse.model_validate(record).model_dump()}


@router.get("", response_model=dict[str, Any])
def list_daily_nutrition(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    service = DailyNutritionService(DailyNutritionRepository(db))
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
        "data": [DailyNutritionResponse.model_validate(r).model_dump() for r in records],
    }
