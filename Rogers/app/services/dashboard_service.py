from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import mean

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.body_composition_repository import BodyCompositionRepository
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.schemas.assessment import AssessmentResponse
from app.schemas.body_composition import BodyCompositionCompareResponse, BodyCompositionResponse, BodyCompositionTrendPoint
from app.schemas.dashboard import (
    AlertItem,
    BodyCompositionSummary,
    DashboardMeData,
    GoalProgressSummary,
    GrowthAnalyticsSummary,
    HealthMetricCard,
    NumericTrendPoint,
)
from app.schemas.daily_metrics import DailyMetricsResponse
from app.schemas.daily_nutrition import DailyNutritionResponse
from app.schemas.daily_workout_plan import DailyWorkoutPlanResponse
from app.schemas.user import UserPublic
from app.services.body_composition_service import BodyCompositionService


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assessment_repo = AssessmentRepository(db)
        self.body_repo = BodyCompositionRepository(db)
        self.daily_metrics_repo = DailyMetricsRepository(db)
        self.daily_workout_repo = DailyWorkoutPlanRepository(db)
        self.daily_nutrition_repo = DailyNutritionRepository(db)
        self.body_service = BodyCompositionService(db)

    @staticmethod
    def _last_days_start(days: int) -> date:
        now = datetime.now(timezone.utc).date()
        return now - timedelta(days=days - 1)

    @staticmethod
    def _status_by_range(value: float | None, low: float, high: float, severe_low: float, severe_high: float) -> str:
        if value is None:
            return "blue"
        if value < severe_low or value > severe_high:
            return "red"
        if value < low or value > high:
            return "yellow"
        return "normal"

    @staticmethod
    def _delta(current: float | None, previous: float | None) -> float | None:
        if current is None or previous is None:
            return None
        return round(current - previous, 2)

    @staticmethod
    def _week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    def _build_goal_progress(self, fat_rate_points: list[NumericTrendPoint]) -> GoalProgressSummary:
        weekly = defaultdict(list)
        for p in fat_rate_points:
            d = datetime.fromisoformat(p.record_date).date()
            weekly[self._week_start(d)].append(p.value)

        weekly_points = sorted(
            [NumericTrendPoint(record_date=k.isoformat(), value=round(mean(v), 2)) for k, v in weekly.items()],
            key=lambda x: x.record_date,
        )[-4:]

        if len(fat_rate_points) >= 2:
            this_week_change = round(fat_rate_points[-1].value - fat_rate_points[max(0, len(fat_rate_points) - 7)].value, 2)
        else:
            this_week_change = 0.0

        if len(fat_rate_points) >= 1:
            baseline = fat_rate_points[0].value
            current = fat_rate_points[-1].value
            # 目标：8周体脂率下降2个百分点
            inner_achieve = max(0.0, min(100.0, round(((baseline - current) / 2.0) * 100, 1)))
        else:
            inner_achieve = 0.0

        outer_percent = max(0.0, min(100.0, round(min(abs(this_week_change) / 1.0, 1.0) * 100, 1)))
        return GoalProgressSummary(
            target_type="减脂",
            outer_week_change=this_week_change,
            outer_ring_percent=outer_percent,
            inner_achieve_percent=inner_achieve,
            trend_4w=weekly_points,
        )

    def _build_health_profile_and_alerts(
        self,
        *,
        metrics_latest: DailyMetricsResponse | None,
        metrics_prev: DailyMetricsResponse | None,
        latest_body: BodyCompositionResponse | None,
    ) -> tuple[dict[str, HealthMetricCard], list[AlertItem]]:
        bmi_value = metrics_latest.bmi if metrics_latest else latest_body.bmi if latest_body else None
        body_fat = metrics_latest.body_fat_rate if metrics_latest else latest_body.body_fat_rate if latest_body else None
        muscle_mass = latest_body.muscle_mass if latest_body else None
        bmr = latest_body.bmr if latest_body else None

        bmi_status = self._status_by_range(bmi_value, 18.5, 23.9, 17.0, 28.0)
        fat_status = self._status_by_range(body_fat, 10.0, 20.0, 8.0, 25.0)
        muscle_status = self._status_by_range(muscle_mass, 35.0, 55.0, 30.0, 65.0)
        bmr_status = self._status_by_range(bmr, 1400.0, 2200.0, 1200.0, 2600.0)

        health_profile = {
            "bmi": HealthMetricCard(
                label="BMI",
                value=bmi_value,
                unit="",
                reference_range="18.5 - 23.9",
                reference_note="行业标准参考值范围",
                delta=self._delta(bmi_value, metrics_prev.bmi if metrics_prev else None),
                status=bmi_status,
            ),
            "body_fat_rate": HealthMetricCard(
                label="体脂率",
                value=body_fat,
                unit="%",
                reference_range="10% - 20%（男性）",
                reference_note="行业标准参考值范围",
                delta=self._delta(body_fat, metrics_prev.body_fat_rate if metrics_prev else None),
                status=fat_status,
            ),
            "muscle_mass": HealthMetricCard(
                label="肌肉量",
                value=muscle_mass,
                unit="kg",
                reference_range="35 - 55 kg（通用）",
                reference_note="行业经验参考值",
                delta=None,
                status=muscle_status,
            ),
            "bmr": HealthMetricCard(
                label="基础代谢(BMR)",
                value=bmr,
                unit="kcal",
                reference_range="1400 - 2200 kcal",
                reference_note="行业经验参考值",
                delta=None,
                status=bmr_status,
            ),
        }

        alerts: list[AlertItem] = []
        for key, card in health_profile.items():
            if card.status in {"red", "yellow", "blue"}:
                level = card.status
                action = "建议持续观察"
                if level == "yellow":
                    action = "建议调整训练和饮食计划"
                if level == "red":
                    action = "建议尽快进行专业评估"
                alerts.append(
                    AlertItem(
                        level=level,
                        metric=card.label,
                        message=f"{card.label} 当前值偏离参考范围（{card.reference_range}）",
                        action=action,
                    )
                )
        return health_profile, alerts

    def _build_behavior_alerts(
        self,
        *,
        daily_workouts: list,
        fat_rate_points: list[NumericTrendPoint],
    ) -> list[AlertItem]:
        alerts: list[AlertItem] = []

        # 规则1：3天未训练（近3天无已完成训练）
        today = datetime.now(timezone.utc).date()
        recent_3d_start = today - timedelta(days=2)
        has_completed_recent = any(
            w.record_date >= recent_3d_start and w.is_completed and w.duration_minutes > 0 for w in daily_workouts
        )
        if not has_completed_recent:
            alerts.append(
                AlertItem(
                    level="yellow",
                    metric="训练执行",
                    message="检测到3天未训练",
                    action="建议恢复轻量训练，避免连续中断",
                )
            )

        # 规则2：体脂率连续2周上升（最近3周均值连续上升）
        weekly = defaultdict(list)
        for p in fat_rate_points:
            d = datetime.fromisoformat(p.record_date).date()
            weekly[self._week_start(d)].append(p.value)
        weekly_means = sorted(
            [round(mean(vals), 2) for _, vals in sorted(weekly.items(), key=lambda x: x[0]) if vals]
        )
        if len(weekly_means) >= 3 and weekly_means[-3] < weekly_means[-2] < weekly_means[-1]:
            alerts.append(
                AlertItem(
                    level="red",
                    metric="体脂率",
                    message="检测到体脂率连续2周上升",
                    action="建议收紧热量摄入并增加有氧训练频次",
                )
            )

        return alerts

    def me(self, current_user: User, *, target_date: date | None = None) -> DashboardMeData:
        ref_date = target_date or datetime.now(timezone.utc).date()
        to_dt = datetime(ref_date.year, ref_date.month, ref_date.day, 23, 59, 59)
        from_dt_range = datetime(ref_date.year, ref_date.month, ref_date.day, 0, 0, 0)
        latest_assessment = self.assessment_repo.latest_by_user(current_user.id)

        body_all = self.body_repo.get_multi(member_id=current_user.id, to_dt=to_dt, limit=2)
        latest_body = body_all[0] if body_all else None
        compare: BodyCompositionCompareResponse | None = None
        if len(body_all) == 2:
            b = body_all[0]
            a = body_all[1]
            compare = self.body_service.compare(current_user=current_user, a_id=a.id, b_id=b.id)

        trend: dict[str, list[BodyCompositionTrendPoint]] = {
            "weight": self.body_service.trend(current_user=current_user, metric="weight", from_dt=None, to_dt=to_dt, limit=60),
            "body_fat_rate": self.body_service.trend(
                current_user=current_user, metric="body_fat_rate", from_dt=None, to_dt=to_dt, limit=60
            ),
        }

        from_date = ref_date - timedelta(days=29)
        daily_metrics = self.daily_metrics_repo.list_by_user(
            user_id=current_user.id, from_date=from_date, to_date=ref_date, skip=0, limit=60
        )
        daily_workouts = self.daily_workout_repo.list_by_user(
            user_id=current_user.id, from_date=from_date, to_date=ref_date, skip=0, limit=60
        )
        daily_nutritions = self.daily_nutrition_repo.list_by_user(
            user_id=current_user.id, from_date=from_date, to_date=ref_date, skip=0, limit=60
        )

        metrics_latest = daily_metrics[0] if daily_metrics else None
        metrics_prev = daily_metrics[1] if len(daily_metrics) > 1 else None
        workout_latest = daily_workouts[0] if daily_workouts else None
        nutrition_latest = daily_nutritions[0] if daily_nutritions else None

        growth_trends: dict[str, list[NumericTrendPoint]] = {
            "weight": [
                NumericTrendPoint(record_date=r.record_date.isoformat(), value=float(r.weight))
                for r in reversed(daily_metrics)
                if r.weight is not None
            ],
            "body_fat_rate": [
                NumericTrendPoint(record_date=r.record_date.isoformat(), value=float(r.body_fat_rate))
                for r in reversed(daily_metrics)
                if r.body_fat_rate is not None
            ],
            "bmi": [
                NumericTrendPoint(record_date=r.record_date.isoformat(), value=float(r.bmi))
                for r in reversed(daily_metrics)
                if r.bmi is not None
            ],
            "calories_kcal": [
                NumericTrendPoint(record_date=r.record_date.isoformat(), value=float(r.calories_kcal))
                for r in reversed(daily_nutritions)
            ],
            "workout_duration": [
                NumericTrendPoint(record_date=r.record_date.isoformat(), value=float(r.duration_minutes))
                for r in reversed(daily_workouts)
            ],
        }
        fat_rate_points = growth_trends.get("body_fat_rate", [])
        goal_progress = self._build_goal_progress(fat_rate_points)
        health_profile, alerts = self._build_health_profile_and_alerts(
            metrics_latest=DailyMetricsResponse.model_validate(metrics_latest) if metrics_latest else None,
            metrics_prev=DailyMetricsResponse.model_validate(metrics_prev) if metrics_prev else None,
            latest_body=BodyCompositionResponse.model_validate(latest_body) if latest_body else None,
        )
        behavior_alerts = self._build_behavior_alerts(daily_workouts=daily_workouts, fat_rate_points=fat_rate_points)
        alerts.extend(behavior_alerts)

        return DashboardMeData(
            me=UserPublic.model_validate(current_user),
            latest_assessment=AssessmentResponse.model_validate(latest_assessment) if latest_assessment else None,
            body_composition_summary=BodyCompositionSummary(
                latest=BodyCompositionResponse.model_validate(latest_body) if latest_body else None,
                trend=trend,
                compare=compare,
            ),
            growth_analytics=GrowthAnalyticsSummary(
                metrics_latest=DailyMetricsResponse.model_validate(metrics_latest) if metrics_latest else None,
                workout_latest=DailyWorkoutPlanResponse.model_validate(workout_latest) if workout_latest else None,
                nutrition_latest=DailyNutritionResponse.model_validate(nutrition_latest) if nutrition_latest else None,
                trends=growth_trends,
                health_profile=health_profile,
                goal_progress=goal_progress,
                alerts=alerts,
            ),
        )
