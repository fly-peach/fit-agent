"""Health Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from src.fitme.utils.database import get_user_db
from src.fitme.services.health_service import HealthService
from src.fitme.services.user_service import UserService
from src.fitme.schemas.health import (
    HealthMetricsResponse,
    CreateHealthMetricRequest,
    CreateHealthMetricResponse,
    HealthMeasurementsResponse,
    HealthReportResponse,
    HealthMetrics,
    HealthMeasurement,
    HealthReport,
    TrendPoint,
    HealthReportSummary,
    StatusSummary
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/health", tags=["Health"])


def _safe_int(value) -> int:
    """安全地将可能为None的值转换为整数"""
    if value is None:
        return 0
    return int(value)


def _safe_float(value) -> float:
    """安全地将可能为None的值转换为浮点数或None"""
    if value is None:
        return 0.0
    return float(value)


def _safe_float_optional(value) -> Optional[float]:
    """安全地将可能为None的值转换为可选浮点数（保持None）"""
    if value is None:
        return None
    return float(value)


def _safe_str(value) -> str:
    """安全地处理字符串值"""
    if value is None:
        return ""
    return str(value)


def _safe_date(value) -> date:
    """安全地处理日期值"""
    if value is None:
        # 返回一个默认日期
        return date.today()
    return value


def _safe_datetime(value) -> datetime:
    """安全地处理日期时间值"""
    if value is None:
        # 返回一个默认日期时间
        return datetime.now()
    return value


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_user_db)
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
    db: Session = Depends(get_user_db)
):
    """获取用户基础指标"""
    metric = HealthService.get_metrics(db, current_user.user_id)
    user_settings = UserService.get_settings(db, current_user.user_id)

    if not metric:
        weight_goal = _safe_float_optional(user_settings.weight_goal) if user_settings else None
        health_metrics = HealthMetrics(
            weight=0.0,
            height=175.0,
            bodyFat=0.0,
            bmi=0.0,
            weightGoal=weight_goal,
            bmiStatus="normal",
        )
        return HealthMetricsResponse(data=health_metrics)

    health_metrics = HealthMetrics(
        weight=_safe_float(metric.weight),
        height=_safe_float(metric.height),
        bodyFat=_safe_float(metric.body_fat),
        bmi=_safe_float(metric.bmi),
        weightGoal=_safe_float_optional(user_settings.weight_goal) if user_settings else None,
        bmiStatus=_safe_str(metric.bmi_status) or "normal",
    )
    return HealthMetricsResponse(data=health_metrics)


@router.post("/metrics", response_model=CreateHealthMetricResponse)
def create_metric(
    data: CreateHealthMetricRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_user_db)
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
    db: Session = Depends(get_user_db)
):
    """获取历史测量记录"""
    metrics = HealthService.get_measurements(db, current_user.user_id, limit)
    
    measurements = [
        HealthMeasurement(
            recordId=_safe_int(m.record_id),
            weight=_safe_float(m.weight),
            bodyFat=_safe_float(m.body_fat),
            bmi=_safe_float(m.bmi),
            measureDate=_safe_date(m.measure_date),
            createdAt=_safe_datetime(m.created_at),
        )
        for m in metrics
    ]
    
    return HealthMeasurementsResponse(data=measurements)


@router.get("/report", response_model=HealthReportResponse)
def get_report(
    period: str = Query(default="week", pattern="^(week|month|year)$"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_user_db)
):
    """获取健康数据报表"""
    raw_report = HealthService.get_report(db, current_user.user_id, period)
    
    # 构建 HealthReport 对象
    weight_trend = [
        TrendPoint(date=item['date'], value=item['value']) 
        for item in raw_report['weightTrend']
    ]
    
    bmi_trend = [
        TrendPoint(date=item['date'], value=item['value']) 
        for item in raw_report['bmiTrend']
    ]
    
    status_summary = StatusSummary(
        normal=raw_report['summary']['statusSummary']['normal'],
        low=raw_report['summary']['statusSummary']['low'],
        high=raw_report['summary']['statusSummary']['high']
    )
    
    summary = HealthReportSummary(
        avgWeight=raw_report['summary']['avgWeight'],
        avgBmi=raw_report['summary']['avgBmi'],
        weightChange=raw_report['summary']['weightChange'],
        statusSummary=status_summary
    )
    
    report = HealthReport(
        weightTrend=weight_trend,
        bmiTrend=bmi_trend,
        summary=summary
    )
    
    return HealthReportResponse(data=report)


@router.get("/export")
def export_health(
    period: str = Query(default="week"),
    format: str = Query(default="csv", pattern="^csv$"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_user_db)
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
            _safe_float(m.weight) if m.weight is not None else "",
            _safe_float(m.body_fat) if m.body_fat is not None else "",
            _safe_float(m.bmi) if m.bmi is not None else "",
            _safe_str(m.bmi_status) or "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=health_data_{period}.csv"}
    )