"""Training Service"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta, datetime, timezone
from ..models import TrainingPlan, TrainingRecord, RecommendedTraining, StreakStats
from ..schemas.training import CreateTrainingPlanRequest, UpdateTrainingPlanRequest, CompleteTrainingRequest


class TrainingService:
    """训练计划服务"""

    @staticmethod
    def get_weekly_stats(db: Session, user_id: int) -> dict:
        """获取本周训练统计"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # 本周训练计划
        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start,
            TrainingPlan.scheduled_date <= today
        ).all()

        completed = [p for p in plans if p.status == "completed"]
        pending = [p for p in plans if p.status == "pending"]

        # 本周训练时长和卡路里
        records = db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= week_start
        ).all()

        total_hours = sum(r.actual_duration or 0 for r in records) / 60
        total_calories = sum(r.calories_burned or 0 for r in records)

        # 连续训练天数
        streak = db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
        streak_days = streak.training_streak if streak else 0

        return {
            "weeklyCount": len(plans),
            "weeklyHours": round(total_hours, 1),
            "weeklyCalories": total_calories,
            "streakDays": streak_days,
            "completedCount": len(completed),
            "remainingCount": len(pending),
        }

    @staticmethod
    def get_weekly_schedule(db: Session, user_id: int) -> List[dict]:
        """获取本周训练安排"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start,
            TrainingPlan.scheduled_date <= week_end
        ).order_by(TrainingPlan.scheduled_date).all()

        return [
            {
                "planId": p.plan_id,
                "dayOfWeek": p.scheduled_date.isoweekday(),
                "date": p.scheduled_date,
                "planName": p.plan_name,
                "planType": p.plan_type,
                "duration": p.estimated_duration,
                "intensity": p.target_intensity,
                "status": p.status,
                "completedAt": None,  # 可从 TrainingRecord 获取
            }
            for p in plans
        ]

    @staticmethod
    def get_weekly_progress(db: Session, user_id: int) -> dict:
        """获取本周进度"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        plans = db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start,
        ).all()

        completed = [p for p in plans if p.status == "completed"]
        target_count = len(plans)

        days_progress = []
        for i, day_name in enumerate(days_names):
            day_date = week_start + timedelta(days=i)
            day_plans = [p for p in plans if p.scheduled_date == day_date]
            completed_today = any(p.status == "completed" for p in day_plans)
            days_progress.append({"day": day_name, "completed": completed_today})

        return {
            "targetCount": target_count,
            "completedCount": len(completed),
            "progressPercent": int(len(completed) / target_count * 100) if target_count > 0 else 0,
            "daysProgress": days_progress,
        }

    @staticmethod
    def get_recommendations(db: Session, limit: int = 5) -> List[RecommendedTraining]:
        """获取推荐训练计划"""
        return db.query(RecommendedTraining).filter(
            RecommendedTraining.is_active == True
        ).limit(limit).all()

    @staticmethod
    def create_plan(db: Session, user_id: int, data: CreateTrainingPlanRequest) -> TrainingPlan:
        """创建训练计划"""
        plan = TrainingPlan(
            user_id=user_id,
            plan_name=data.planName,
            plan_type=data.planType,
            target_intensity=data.targetIntensity,
            estimated_duration=data.estimatedDuration,
            scheduled_date=data.scheduledDate,
            day_of_week=data.scheduledDate.isoweekday(),
            note=data.note,
            status="pending",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_plan(db: Session, plan_id: int, user_id: int, data: UpdateTrainingPlanRequest) -> Optional[TrainingPlan]:
        """更新训练计划"""
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            if data.planName:
                plan.plan_name = data.planName
            if data.scheduledDate:
                plan.scheduled_date = data.scheduledDate
                plan.day_of_week = data.scheduledDate.isoweekday()
            if data.targetIntensity:
                plan.target_intensity = data.targetIntensity
            if data.estimatedDuration:
                plan.estimated_duration = data.estimatedDuration
            if data.note:
                plan.note = data.note
            db.commit()
            db.refresh(plan)
        return plan

    @staticmethod
    def complete_plan(db: Session, plan_id: int, user_id: int, data: CompleteTrainingRequest) -> Optional[TrainingRecord]:
        """完成训练"""
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            completed_dt = datetime.now(timezone.utc)
            if data.completedDate:
                completed_dt = datetime.combine(date.fromisoformat(data.completedDate), datetime.min.time()).replace(tzinfo=timezone.utc)

            record = TrainingRecord(
                plan_id=plan_id,
                user_id=user_id,
                actual_duration=data.actualDuration,
                actual_intensity=data.actualIntensity,
                calories_burned=data.caloriesBurned,
                completed_at=completed_dt,
                note=data.note,
            )
            plan.status = "completed"
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        return None

    @staticmethod
    def delete_plan(db: Session, plan_id: int, user_id: int) -> bool:
        """删除训练计划"""
        plan = db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            db.delete(plan)
            db.commit()
            return True
        return False

    @staticmethod
    def get_date_range_trend(db: Session, user_id: int, start_date: date, end_date: date) -> dict:
        """获取日期范围内的每日训练趋势"""
        # 按日期分组聚合训练记录
        records = db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            TrainingRecord.completed_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc),
        ).order_by(TrainingRecord.completed_at).all()

        # 按日期分组
        daily_map: dict[date, list] = {}
        for r in records:
            day = r.completed_at.date()
            daily_map.setdefault(day, []).append(r)

        # 填充所有日期（包括没有记录的日期）
        daily_stats = []
        current = start_date
        while current <= end_date:
            day_records = daily_map.get(current, [])
            daily_stats.append({
                "date": current,
                "duration": sum(r.actual_duration or 0 for r in day_records),
                "caloriesBurned": sum(r.calories_burned or 0 for r in day_records),
                "planCount": len(day_records),
            })
            current += timedelta(days=1)

        return {"dailyStats": daily_stats}