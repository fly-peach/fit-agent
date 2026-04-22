from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.assessment import (
    AssessmentComplete,
    AssessmentCreate,
    AssessmentReportResponse,
    AssessmentResponse,
)
from app.services.assessment_service import AssessmentService

router = APIRouter()


@router.post("", response_model=dict[str, Any])
def create_assessment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    assessment_in: AssessmentCreate,
) -> Any:
    """创建评估记录"""
    service = AssessmentService(db)
    assessment = service.create_assessment(obj_in=assessment_in, current_user=current_user)
    return {
        "code": 0,
        "message": "success",
        "data": AssessmentResponse.model_validate(assessment).model_dump()
    }


@router.get("", response_model=dict[str, Any])
def read_assessments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
) -> Any:
    """获取评估列表"""
    service = AssessmentService(db)
    assessments = service.list_assessments(current_user=current_user, skip=skip, limit=limit, status=status)
    return {
        "code": 0,
        "message": "success",
        "data": [AssessmentResponse.model_validate(a).model_dump() for a in assessments]
    }


@router.get("/{id}", response_model=dict[str, Any])
def read_assessment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
) -> Any:
    """获取评估详情"""
    service = AssessmentService(db)
    assessment = service.get_assessment(assessment_id=id, current_user=current_user)
    return {
        "code": 0,
        "message": "success",
        "data": AssessmentResponse.model_validate(assessment).model_dump()
    }


@router.post("/{id}/complete", response_model=dict[str, Any])
def complete_assessment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
    assessment_in: AssessmentComplete,
) -> Any:
    """完成评估并生成报告"""
    service = AssessmentService(db)
    assessment = service.complete_assessment(assessment_id=id, data=assessment_in, current_user=current_user)
    return {
        "code": 0,
        "message": "success",
        "data": AssessmentResponse.model_validate(assessment).model_dump()
    }


@router.get("/{id}/report", response_model=dict[str, Any])
def read_assessment_report(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    id: int,
) -> Any:
    """获取评估报告摘要"""
    service = AssessmentService(db)
    assessment = service.get_assessment_report(assessment_id=id, current_user=current_user)
    return {
        "code": 0,
        "message": "success",
        "data": AssessmentReportResponse.model_validate(assessment).model_dump()
    }
