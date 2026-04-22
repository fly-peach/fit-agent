from typing import Any

from fastapi import APIRouter, Depends
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
) -> Any:
    service = DashboardService(db)
    data = service.me(current_user)
    return {"code": 0, "message": "success", "data": data.model_dump()}

