"""Health Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional

import sys
sys.path.insert(0, "E:/fitagent/rogers/src")
from fitme.utils.database import get_db
from fitme.services.health_service import HealthService
from fitme.services.user_service import UserService
from fitme.schemas.health import (
    HealthMetricsResponse,
    CreateHealthMetricRequest,
    CreateHealthMetricResponse,
    HealthMeasurementsResponse,
    HealthReportResponse,
)
from fitme.schemas.common import BaseResponse
from fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/health", tags=["Health"])


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


@router.get("/metrics", response_model=HealthMetricsResponse)
def get_metrics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户基础指标"""
    metric = HealthService.get_metrics(db, current_user.user_id)
    user_settings = UserService.get_settings(db, current_user.user_id)

    if not metric:
        return HealthMetricsResponse(
            data={
                "weight": 0,
                "height": 175,
                "bodyFat": 0,
                "bmi": 0,
                "weightGoal": float(user_settings.weight_goal) if user_settings and user_settings.weight_goal else None,
                "bmiStatus": "normal",
            }
        )

    return HealthMetricsResponse(
        data={
            "weight": float(metric.weight) if metric.weight else 0,
            "height": float(metric.height) if metric.height else 175,
            "bodyFat": float(metric.body_fat) if metric.body_fat else 0,
            "bmi": float(metric.bmi) if metric.bmi else 0,
            "weightGoal": float(user_settings.weight_goal) if user_settings and user_settings.weight_goal else None,
            "bmiStatus": metric.bmi_status or "normal",
        }
    )


@router.post("/metrics", response_model=CreateHealthMetricResponse)
def create_metric(
    data: CreateHealthMetricRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建健康指标记录"""
    metric = HealthService.create_metric(db, current_user.user_id, data)
    return CreateHealthMetricResponse(
        message="记录成功",
        data={"recordId": metric.record_id, "createdAt": metric.created_at}
    )


@router.get("/measurements", response_model=HealthMeasurementsResponse)
def get_measurements(
    limit: int = Query(default=10, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取历史测量记录"""
    metrics = HealthService.get_measurements(db, current_user.user_id, limit)
    return HealthMeasurementsResponse(
        data=[
            {
                "recordId": m.record_id,
                "weight": float(m.weight) if m.weight else 0,
                "bodyFat": float(m.body_fat) if m.body_fat else 0,
                "bmi": float(m.bmi) if m.bmi else 0,
                "measureDate": m.measure_date,
                "createdAt": m.created_at,
            }
            for m in metrics
        ]
    )


@router.get("/report", response_model=HealthReportResponse)
def get_report(
    period: str = Query(default="week", regex="^(week|month|year)$"),
    status: str = Query(default="all", regex="^(all|pass|low|high)$"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取健康数据报表"""
    report = HealthService.get_report(db, current_user.user_id, period)
    return HealthReportResponse(data=report)


@router.get("/export")
def export_health(
    period: str = Query(default="week"),
    format: str = Query(default="csv", regex="^(csv|excel)$"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出健康数据"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    metrics = HealthService.get_measurements(db, current_user.user_id, 100)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "体重", "体脂率", "BMI", "状态"])

    for m in metrics:
        writer.writerow([
            m.measure_date,
            float(m.weight) if m.weight else "",
            float(m.body_fat) if m.body_fat else "",
            float(m.bmi) if m.bmi else "",
            m.bmi_status,
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=health_data_{period}.csv"}
    )