"""Health Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class HealthMetrics(BaseModel):
    """健康指标"""
    weight: float
    height: float
    bodyFat: float
    bmi: float
    weightGoal: Optional[float] = None
    bmiStatus: str


class HealthMetricsResponse(BaseModel):
    """健康指标响应"""
    code: int = 200
    data: HealthMetrics


class CreateHealthMetricRequest(BaseModel):
    """创建健康指标请求"""
    weight: Optional[float] = None
    height: Optional[float] = None
    bodyFat: Optional[float] = None
    measureDate: date


class CreateHealthMetricResponse(BaseModel):
    """创建健康指标响应"""
    code: int = 200
    message: str = "记录成功"
    data: dict


class HealthMeasurement(BaseModel):
    """健康测量记录"""
    recordId: int
    weight: float
    bodyFat: float
    bmi: float
    measureDate: date
    createdAt: datetime


class HealthMeasurementsResponse(BaseModel):
    """历史测量记录响应"""
    code: int = 200
    data: List[HealthMeasurement]


class TrendPoint(BaseModel):
    """趋势数据点"""
    date: date
    value: float


class StatusSummary(BaseModel):
    """状态统计"""
    normal: int
    low: int
    high: int


class HealthReportSummary(BaseModel):
    """健康报表摘要"""
    avgWeight: float
    avgBmi: float
    weightChange: float
    statusSummary: StatusSummary


class HealthReport(BaseModel):
    """健康报表"""
    weightTrend: List[TrendPoint]
    bmiTrend: List[TrendPoint]
    summary: HealthReportSummary


class HealthReportResponse(BaseModel):
    """健康报表响应"""
    code: int = 200
    data: HealthReport