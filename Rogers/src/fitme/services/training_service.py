"""Training Service - Dual Database Support"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta, datetime, timezone
import time
from ..models import (
    TrainingPlan, TrainingRecord, RecommendedTraining, StreakStats,
    PlanExerciseItem, Exercise
)
from ..schemas.training import CreateTrainingPlanRequest, UpdateTrainingPlanRequest, CompleteTrainingRequest
from ..schemas.exercise import PlanExerciseItemInput, PlanExerciseItemOutput, UpdatePlanExerciseItem


class TrainingService:
    """训练计划服务 - 双数据库
    - base_db: RecommendedTraining, Exercise
    - user_db: TrainingPlan, TrainingRecord, StreakStats, PlanExerciseItem
    """

    @staticmethod
    def _copy_exercises(user_db: Session, from_plan_id: int, to_plan_id: int) -> None:
        """复制一个计划的所有动作到另一个计划"""
        items = user_db.query(PlanExerciseItem).filter(PlanExerciseItem.plan_id == from_plan_id).all()
        for item in items:
            user_db.add(PlanExerciseItem(
                plan_id=to_plan_id,
                exercise_id=item.exercise_id,
                custom_name=item.custom_name or "",
                sets=item.sets,
                reps=item.reps,
                weight=item.weight,
                duration=item.duration,
                notes=item.notes,
            ))

    @staticmethod
    def _generate_plans(user_db: Session, user_id: int, data: CreateTrainingPlanRequest, start_date: date, weeks: int = 8) -> List[int]:
        """从起始日期开始，按指定星期几生成 N 周的真实计划记录，返回 plan_id 列表"""
        plan_ids = []
        for week in range(weeks):
            plan_date = start_date + timedelta(weeks=week)
            plan = TrainingPlan(
                user_id=user_id,
                plan_name=data.planName,
                plan_type=data.planType,
                target_intensity=data.targetIntensity,
                estimated_duration=data.estimatedDuration,
                scheduled_date=plan_date,
                day_of_week=data.scheduledDate.isoweekday(),
                note=data.note,
                is_recurring=False,
                recurring_group_id=data.recurringGroupId,
                status="pending",
            )
            user_db.add(plan)
            user_db.flush()
            plan_ids.append(plan.plan_id)
            if data.exercises:
                for ex_data in data.exercises:
                    user_db.add(PlanExerciseItem(
                        plan_id=plan.plan_id,
                        exercise_id=ex_data.exerciseId,
                        custom_name=ex_data.customName or "",
                        sets=ex_data.sets,
                        reps=ex_data.reps,
                        weight=ex_data.weight,
                        duration=ex_data.duration,
                        notes=ex_data.notes,
                    ))
        user_db.commit()
        return plan_ids

    @staticmethod
    def get_weekly_stats(user_db: Session, user_id: int) -> dict:
        """获取本周训练统计"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plans = user_db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= week_start,
            TrainingPlan.scheduled_date <= today
        ).all()

        completed = [p for p in plans if p.status == "completed"]
        pending = [p for p in plans if p.status == "pending"]

        records = user_db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= week_start
        ).all()

        total_hours = sum(r.actual_duration or 0 for r in records) / 60
        total_calories = sum(r.calories_burned or 0 for r in records)

        streak = user_db.query(StreakStats).filter(StreakStats.user_id == user_id).first()
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
    def get_weekly_schedule(user_db: Session, user_id: int) -> List[dict]:
        """获取本周训练安排"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        plans = user_db.query(TrainingPlan).filter(
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
                "isRecurring": bool(p.recurring_group_id),
                "completedAt": None,
            }
            for p in plans
        ]

    @staticmethod
    def get_monthly_schedule(user_db: Session, user_id: int, year: int, month: int) -> List[dict]:
        """获取指定月份的训练安排"""
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year, 12, 31)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        plans = user_db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.scheduled_date >= month_start,
            TrainingPlan.scheduled_date <= month_end
        ).order_by(TrainingPlan.scheduled_date).all()

        # 找出同一组中日期最晚的计划，标记为 isLastInGroup
        group_last = {}
        for p in plans:
            gid = p.recurring_group_id
            if gid:
                if gid not in group_last or p.scheduled_date > group_last[gid]:
                    group_last[gid] = p.scheduled_date

        return [
            {
                "planId": p.plan_id,
                "date": p.scheduled_date.isoformat(),
                "planName": p.plan_name,
                "planType": p.plan_type,
                "duration": p.estimated_duration,
                "intensity": p.target_intensity,
                "status": p.status,
                "isRecurring": bool(p.recurring_group_id),
                "isLastInGroup": bool(p.recurring_group_id and p.scheduled_date == group_last.get(p.recurring_group_id)),
            }
            for p in plans
        ]

    @staticmethod
    def renew_recurring(user_db: Session, plan_id: int, user_id: int, weeks: int = 8) -> List[int]:
        """为循环计划续期：从该组最晚日期之后再生成 N 周"""
        plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan or not plan.recurring_group_id:
            return []

        gid = plan.recurring_group_id
        # 找到同组最晚的日期
        latest = user_db.query(func.max(TrainingPlan.scheduled_date)).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.recurring_group_id == gid
        ).scalar()

        if not latest:
            return []

        # 从最晚日期的下一周开始生成
        start_date = latest + timedelta(weeks=1)

        # 查询用户在这些日期是否已有计划，避免重复
        existing_dates = set(
            d[0] for d in user_db.query(TrainingPlan.scheduled_date).filter(
                TrainingPlan.user_id == user_id,
                TrainingPlan.scheduled_date >= start_date,
            ).all()
        )

        # 读取该组任意一个计划的动作配置
        ref_plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.user_id == user_id,
            TrainingPlan.recurring_group_id == gid
        ).first()
        if not ref_plan:
            return []

        ref_exercises = user_db.query(PlanExerciseItem).filter(PlanExerciseItem.plan_id == ref_plan.plan_id).all()

        plan_ids = []
        for week in range(weeks):
            plan_date = start_date + timedelta(weeks=week)
            # 跳过已有计划的日期，避免重复
            if plan_date in existing_dates:
                continue
            new_plan = TrainingPlan(
                user_id=user_id,
                plan_name=ref_plan.plan_name,
                plan_type=ref_plan.plan_type,
                target_intensity=ref_plan.target_intensity,
                estimated_duration=ref_plan.estimated_duration,
                scheduled_date=plan_date,
                day_of_week=ref_plan.day_of_week,
                note=ref_plan.note,
                is_recurring=False,
                recurring_group_id=gid,
                status="pending",
            )
            user_db.add(new_plan)
            user_db.flush()
            plan_ids.append(new_plan.plan_id)
            for ex in ref_exercises:
                user_db.add(PlanExerciseItem(
                    plan_id=new_plan.plan_id,
                    exercise_id=ex.exercise_id,
                    custom_name=ex.custom_name or "",
                    sets=ex.sets,
                    reps=ex.reps,
                    weight=ex.weight,
                    duration=ex.duration,
                    notes=ex.notes,
                ))
        user_db.commit()
        return plan_ids

    @staticmethod
    def get_weekly_progress(user_db: Session, user_id: int) -> dict:
        """获取本周进度"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        days_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        plans = user_db.query(TrainingPlan).filter(
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
    def get_recommendations(base_db: Session, limit: int = 5) -> List[RecommendedTraining]:
        """获取推荐训练计划"""
        return base_db.query(RecommendedTraining).filter(
            RecommendedTraining.is_active == True
        ).limit(limit).all()

    @staticmethod
    def create_plan(user_db: Session, user_id: int, data: CreateTrainingPlanRequest) -> TrainingPlan:
        """创建训练计划（循环计划自动生成未来 2 个月）"""
        if data.isRecurring:
            # 生成循环组 ID（用时间戳保证唯一）
            group_id = int(time.time() * 1000)
            data.recurringGroupId = group_id
            # 生成 8 周的计划
            plan_ids = TrainingService._generate_plans(user_db, user_id, data, data.scheduledDate, weeks=8)
            # 返回第一个计划作为代表
            return user_db.query(TrainingPlan).filter(
                TrainingPlan.plan_id == plan_ids[0],
                TrainingPlan.user_id == user_id
            ).first()
        else:
            plan = TrainingPlan(
                user_id=user_id,
                plan_name=data.planName,
                plan_type=data.planType,
                target_intensity=data.targetIntensity,
                estimated_duration=data.estimatedDuration,
                scheduled_date=data.scheduledDate,
                day_of_week=data.scheduledDate.isoweekday(),
                note=data.note,
                is_recurring=False,
                recurring_group_id=None,
                status="pending",
            )
            user_db.add(plan)
            user_db.flush()

            if data.exercises:
                for ex_data in data.exercises:
                    plan_item = PlanExerciseItem(
                        plan_id=plan.plan_id,
                        exercise_id=ex_data.exerciseId,
                        custom_name=ex_data.customName or "",
                        sets=ex_data.sets,
                        reps=ex_data.reps,
                        weight=ex_data.weight,
                        duration=ex_data.duration,
                        notes=ex_data.notes,
                    )
                    user_db.add(plan_item)

            user_db.commit()
            user_db.refresh(plan)
            return plan

    @staticmethod
    def update_plan(user_db: Session, plan_id: int, user_id: int, data: UpdateTrainingPlanRequest) -> Optional[TrainingPlan]:
        """更新训练计划"""
        plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            if data.planName is not None:
                plan.plan_name = data.planName
            if data.scheduledDate is not None:
                plan.scheduled_date = data.scheduledDate
                plan.day_of_week = data.scheduledDate.isoweekday()
            if data.targetIntensity is not None:
                plan.target_intensity = data.targetIntensity
            if data.estimatedDuration is not None:
                plan.estimated_duration = data.estimatedDuration
            if data.note is not None:
                plan.note = data.note
            user_db.commit()
            user_db.refresh(plan)
        return plan

    @staticmethod
    def complete_plan(user_db: Session, plan_id: int, user_id: int, data: CompleteTrainingRequest) -> Optional[TrainingRecord]:
        """完成训练"""
        plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            if plan.status == "completed":
                return None
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
            user_db.add(record)
            user_db.commit()
            user_db.refresh(record)
            return record
        return None

    @staticmethod
    def delete_plan(user_db: Session, plan_id: int, user_id: int) -> bool:
        """删除训练计划（先删关联记录，再删计划本身）"""
        plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if plan:
            user_db.query(TrainingRecord).filter(TrainingRecord.plan_id == plan_id).delete()
            user_db.query(PlanExerciseItem).filter(PlanExerciseItem.plan_id == plan_id).delete()
            user_db.delete(plan)
            user_db.commit()
            return True
        return False

    @staticmethod
    def get_plan_by_id(user_db: Session, plan_id: int, user_id: int) -> Optional[TrainingPlan]:
        """获取训练计划详情"""
        return user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()

    @staticmethod
    def get_plan_exercises(base_db: Session, user_db: Session, plan_id: int) -> List[PlanExerciseItemOutput]:
        """获取计划关联的动作列表 - 从两个数据库分别查询后合并"""
        items = user_db.query(PlanExerciseItem).filter(PlanExerciseItem.plan_id == plan_id).all()

        # 收集所有需要查询的 exercise_id
        exercise_ids = [item.exercise_id for item in items if item.exercise_id]

        # 从 base_db 批量查询 Exercise
        exercise_map = {}
        if exercise_ids:
            exercises = base_db.query(Exercise).filter(Exercise.exercise_id.in_(exercise_ids)).all()
            exercise_map = {ex.exercise_id: ex for ex in exercises}

        result = []
        for item in items:
            output = PlanExerciseItemOutput(
                id=item.id,
                exerciseId=item.exercise_id,
                customName=item.custom_name,
                sets=item.sets,
                reps=item.reps,
                weight=float(item.weight) if item.weight else None,
                duration=item.duration,
                notes=item.notes,
            )
            exercise = exercise_map.get(item.exercise_id)
            if exercise:
                output.nameCn = exercise.name_cn
                output.targetMuscle = exercise.target_muscle
                output.helperMuscles = exercise.helper_muscles or ""
                output.difficulty = exercise.difficulty
                output.forceType = exercise.force_type
                output.mechanics = exercise.mechanics
                output.equipment = exercise.equipment
            result.append(output)
        return result

    @staticmethod
    def update_plan_exercise(user_db: Session, exercise_item_id: int, user_id: int, data: UpdatePlanExerciseItem) -> Optional[PlanExerciseItem]:
        """更新计划中动作的组数/次数/重量"""
        item = user_db.query(PlanExerciseItem).join(TrainingPlan).filter(
            PlanExerciseItem.id == exercise_item_id,
            TrainingPlan.user_id == user_id
        ).first()
        if item:
            if data.sets is not None:
                item.sets = data.sets
            if data.reps is not None:
                item.reps = data.reps
            if data.weight is not None:
                item.weight = data.weight
            if data.duration is not None:
                item.duration = data.duration
            user_db.commit()
            user_db.refresh(item)
        return item

    @staticmethod
    def add_plan_exercise(user_db: Session, plan_id: int, user_id: int, data: PlanExerciseItemInput) -> Optional[PlanExerciseItem]:
        """向已有计划新增一个动作项"""
        plan = user_db.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not plan:
            return None
        item = PlanExerciseItem(
            plan_id=plan_id,
            exercise_id=data.exerciseId,
            custom_name=data.customName or "",
            sets=data.sets,
            reps=data.reps,
            weight=data.weight,
            duration=data.duration,
            notes=data.notes,
        )
        user_db.add(item)
        user_db.commit()
        user_db.refresh(item)
        return item

    @staticmethod
    def delete_plan_exercise(user_db: Session, exercise_item_id: int, user_id: int) -> bool:
        """从计划中删除一个动作项"""
        item = user_db.query(PlanExerciseItem).join(TrainingPlan).filter(
            PlanExerciseItem.id == exercise_item_id,
            TrainingPlan.user_id == user_id
        ).first()
        if not item:
            return False
        user_db.delete(item)
        user_db.commit()
        return True

    @staticmethod
    def get_date_range_trend(user_db: Session, user_id: int, start_date: date, end_date: date) -> dict:
        """获取日期范围内的每日训练趋势"""
        records = user_db.query(TrainingRecord).filter(
            TrainingRecord.user_id == user_id,
            TrainingRecord.completed_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            TrainingRecord.completed_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc),
        ).order_by(TrainingRecord.completed_at).all()

        daily_map: dict[date, list] = {}
        for r in records:
            day = r.completed_at.date()
            daily_map.setdefault(day, []).append(r)

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
