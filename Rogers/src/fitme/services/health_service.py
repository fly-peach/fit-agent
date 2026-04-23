"""Health Service"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta
from decimal import Decimal
from ..models import HealthMetric, UserSettings
from ..schemas.health import CreateHealthMetricRequest


class HealthService:
    """健康数据服务"""

    @staticmethod
    def get_metrics(db: Session, user_id: int) -> Optional[HealthMetric]:
        """获取用户基础指标（最新一条记录）"""
        return db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).first()

    @staticmethod
    def create_metric(db: Session, user_id: int, data: CreateHealthMetricRequest) -> HealthMetric:
        """创建健康指标记录"""
        metric = HealthMetric(
            user_id=user_id,
            weight=data.weight,
            body_fat=data.bodyFat,
            measure_date=data.measureDate,
        )
        if data.weight:
            user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            height = user_settings and 175  # 默认身高，可从设置获取
            if height:
                bmi = float(data.weight) / ((height / 100) ** 2)
                metric.height = Decimal(str(height))
                metric.bmi = Decimal(str(round(bmi, 2)))
                if bmi < 18.5:
                    metric.bmi_status = "under"
                elif bmi > 25:
                    metric.bmi_status = "over"
                else:
                    metric.bmi_status = "normal"
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @staticmethod
    def get_measurements(db: Session, user_id: int, limit: int = 10) -> List[HealthMetric]:
        """获取历史测量记录"""
        return db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id
        ).order_by(HealthMetric.measure_date.desc()).limit(limit).all()

    @staticmethod
    def get_report(db: Session, user_id: int, period: str = "week") -> dict:
        """获取健康数据报表"""
        today = date.today()
        if period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today - timedelta(days=30)
        elif period == "year":
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=7)

        metrics = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id,
            HealthMetric.measure_date >= start_date
        ).order_by(HealthMetric.measure_date).all()

        weight_trend = [{"date": m.measure_date, "value": float(m.weight)} for m in metrics if m.weight]
        bmi_trend = [{"date": m.measure_date, "value": float(m.bmi)} for m in metrics if m.bmi]

        avg_weight = sum(float(m.weight) for m in metrics if m.weight) / len(weight_trend) if weight_trend else 0
        avg_bmi = sum(float(m.bmi) for m in metrics if m.bmi) / len(bmi_trend) if bmi_trend else 0

        status_counts = {"normal": 0, "low": 0, "high": 0}
        for m in metrics:
            if m.bmi_status == "normal":
                status_counts["normal"] += 1
            elif m.bmi_status == "under":
                status_counts["low"] += 1
            elif m.bmi_status == "over":
                status_counts["high"] += 1

        return {
            "weightTrend": weight_trend,
            "bmiTrend": bmi_trend,
            "summary": {
                "avgWeight": round(avg_weight, 1),
                "avgBmi": round(avg_bmi, 1),
                "weightChange": float(metrics[-1].weight - metrics[0].weight) if len(metrics) >= 2 else 0,
                "statusSummary": status_counts,
            }
        }