from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardMeResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/me", response_model=DashboardMeResponse)
def dashboard_me(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    target_date: date | None = Query(None, description="查看指定日期的数据，默认今日数据"),
) -> Any:
    service = DashboardService(db)
    data = service.me(current_user, target_date=target_date)
    return {"code": 0, "message": "success", "data": data.model_dump()}

