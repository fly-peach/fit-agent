from pydantic import BaseModel

from app.schemas.assessment import AssessmentResponse
from app.schemas.body_composition import BodyCompositionCompareResponse, BodyCompositionResponse, BodyCompositionTrendPoint
from app.schemas.daily_metrics import DailyMetricsResponse
from app.schemas.daily_nutrition import DailyNutritionResponse
from app.schemas.daily_workout_plan import DailyWorkoutPlanResponse
from app.schemas.user import UserPublic


class BodyCompositionSummary(BaseModel):
    latest: BodyCompositionResponse | None
    trend: dict[str, list[BodyCompositionTrendPoint]]
    compare: BodyCompositionCompareResponse | None


class NumericTrendPoint(BaseModel):
    record_date: str
    value: float


class HealthMetricCard(BaseModel):
    label: str
    value: float | None
    unit: str
    reference_range: str
    reference_note: str
    delta: float | None
    status: str  # blue / yellow / red / normal


class GoalProgressSummary(BaseModel):
    target_type: str
    outer_week_change: float
    outer_ring_percent: float
    inner_achieve_percent: float
    trend_4w: list[NumericTrendPoint]


class AlertItem(BaseModel):
    level: str  # blue / yellow / red
    metric: str
    message: str
    action: str


class GrowthAnalyticsSummary(BaseModel):
    metrics_latest: DailyMetricsResponse | None
    workout_latest: DailyWorkoutPlanResponse | None
    nutrition_latest: DailyNutritionResponse | None
    trends: dict[str, list[NumericTrendPoint]]
    health_profile: dict[str, HealthMetricCard]
    goal_progress: GoalProgressSummary
    alerts: list[AlertItem]


class DashboardMeData(BaseModel):
    me: UserPublic
    latest_assessment: AssessmentResponse | None
    body_composition_summary: BodyCompositionSummary
    growth_analytics: GrowthAnalyticsSummary


class DashboardMeResponse(BaseModel):
    code: int
    message: str
    data: DashboardMeData
