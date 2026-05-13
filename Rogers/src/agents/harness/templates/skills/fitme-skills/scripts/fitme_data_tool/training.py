"""Fitme 训练编排数据工具。"""
from __future__ import annotations

from datetime import date
from typing import Any

from src.fitme.schemas.exercise import UpdatePlanExerciseItem, PlanExerciseItemInput
from src.fitme.schemas.training import (
    CompleteTrainingRequest,
    CreateTrainingPlanRequest,
    UpdateTrainingPlanRequest,
)
from src.fitme.services.training_service import TrainingService
from src.fitme.utils.database import BaseDBContext, UserDBContext


def get_training_monthly_schedule(user_id: int, year: int, month: int) -> dict[str, Any]:
    """获取指定月份训练安排。"""
    with UserDBContext() as user_db:
        return {
            "success": True,
            "data": TrainingService.get_monthly_schedule(user_db, user_id, year, month),
        }


def get_training_weekly_progress(user_id: int) -> dict[str, Any]:
    """获取本周训练进度。"""
    with UserDBContext() as user_db:
        return {
            "success": True,
            "data": TrainingService.get_weekly_progress(user_db, user_id),
        }


def get_training_plan_detail(user_id: int, plan_id: int) -> dict[str, Any]:
    """获取训练计划详情及动作项。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        plan = TrainingService.get_plan_by_id(user_db, plan_id, user_id)
        if not plan:
            return {"success": False, "error": "计划不存在"}
        exercises = TrainingService.get_plan_exercises(base_db, user_db, plan_id)
        return {
            "success": True,
            "data": {
                "planId": plan.plan_id,
                "planName": plan.plan_name,
                "planType": plan.plan_type,
                "targetIntensity": plan.target_intensity,
                "estimatedDuration": plan.estimated_duration,
                "scheduledDate": plan.scheduled_date.isoformat() if plan.scheduled_date is not None else None,
                "status": plan.status,
                "note": plan.note,
                "isRecurring": bool(plan.recurring_group_id),
                "recurringGroupId": plan.recurring_group_id,
                "exercises": [item.model_dump() for item in exercises],
            },
        }


def create_training_plan(
    user_id: int,
    plan_name: str,
    plan_type: str,
    scheduled_date: str | None = None,
    estimated_duration: int = 60,
    target_intensity: str = "medium",
    note: str | None = None,
    is_recurring: bool = False,
    exercises: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """创建训练计划，支持动作项和循环计划。"""
    sched_dt = date.fromisoformat(scheduled_date) if scheduled_date else date.today()
    
    # 将 exercises 从字典列表转换为 PlanExerciseItemInput 对象列表
    exercises_input = None
    if exercises is not None:
        exercises_input = [PlanExerciseItemInput(**exercise) for exercise in exercises]
    
    data = CreateTrainingPlanRequest(
        planName=plan_name,
        planType=plan_type,
        targetIntensity=target_intensity,
        estimatedDuration=estimated_duration,
        scheduledDate=sched_dt,
        note=note,
        isRecurring=is_recurring,
        exercises=exercises_input,
    )
    with UserDBContext() as user_db:
        plan = TrainingService.create_plan(user_db, user_id, data)
        return {
            "success": True,
            "data": {
                "planId": plan.plan_id,
                "planName": plan.plan_name,
                "planType": plan.plan_type,
                "scheduledDate": plan.scheduled_date.isoformat() if plan.scheduled_date is not None else None,
                "estimatedDuration": plan.estimated_duration,
                "targetIntensity": plan.target_intensity,
                "note": plan.note,
                "isRecurring": is_recurring,
                "recurringGroupId": plan.recurring_group_id,
                "exerciseCount": len(exercises or []),
            },
        }


def update_training_plan(
    user_id: int,
    plan_id: int,
    plan_name: str | None = None,
    scheduled_date: str | None = None,
    estimated_duration: int | None = None,
    target_intensity: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """更新训练计划基础信息。"""
    data = UpdateTrainingPlanRequest(
        planName=plan_name,
        scheduledDate=date.fromisoformat(scheduled_date) if scheduled_date else None,
        estimatedDuration=estimated_duration,
        targetIntensity=target_intensity,
        note=note,
    )
    with UserDBContext() as user_db:
        plan = TrainingService.update_plan(user_db, plan_id, user_id, data)
        if not plan:
            return {"success": False, "error": "计划不存在"}
        return {
            "success": True,
            "data": {
                "planId": plan.plan_id,
                "planName": plan.plan_name,
                "scheduledDate": plan.scheduled_date.isoformat() if plan.scheduled_date is not None else None,
                "estimatedDuration": plan.estimated_duration,
                "targetIntensity": plan.target_intensity,
                "note": plan.note,
            },
        }


def complete_training_plan(
    user_id: int,
    plan_id: int,
    actual_duration: int,
    actual_intensity: str | None = None,
    calories_burned: int | None = None,
    note: str | None = None,
    completed_date: str | None = None,
) -> dict[str, Any]:
    """完成训练计划。"""
    data = CompleteTrainingRequest(
        actualDuration=actual_duration,
        actualIntensity=actual_intensity,
        caloriesBurned=calories_burned,
        note=note,
        completedDate=completed_date,
    )
    with UserDBContext() as user_db:
        record = TrainingService.complete_plan(user_db, plan_id, user_id, data)
        if not record:
            return {"success": False, "error": "计划不存在"}
        return {
            "success": True,
            "data": {
                "planId": plan_id,
                "recordId": record.record_id,
                "actualDuration": record.actual_duration,
                "actualIntensity": record.actual_intensity,
                "caloriesBurned": record.calories_burned,
                "completedAt": record.completed_at.isoformat() if record.completed_at is not None else None,
            },
        }


def update_plan_exercise_item(
    user_id: int,
    exercise_item_id: int,
    sets: int | None = None,
    reps: int | None = None,
    weight: float | None = None,
    duration: int | None = None,
) -> dict[str, Any]:
    """更新计划内动作项。"""
    data = UpdatePlanExerciseItem(
        sets=sets,
        reps=reps,
        weight=weight,
        duration=duration,
    )
    with UserDBContext() as user_db:
        item = TrainingService.update_plan_exercise(user_db, exercise_item_id, user_id, data)
        if not item:
            return {"success": False, "error": "计划动作不存在"}
        
        # 为了解决Pylance报告的类型错误，我们显式检查weight值是否可以转换为float
        weight_value = item.weight
        if weight_value is not None:
            # 如果weight_value本身是可转换为float的类型，则转换
            try:
                weight_result = float(weight_value)
            except (TypeError, ValueError):
                # 如果转换失败，返回None
                weight_result = None
        else:
            weight_result = None
        
        return {
            "success": True,
            "data": {
                "exerciseItemId": item.id,
                "sets": item.sets,
                "reps": item.reps,
                "weight": weight_result,
                "duration": item.duration,
            },
        }


def renew_recurring_training_plan(user_id: int, plan_id: int) -> dict[str, Any]:
    """为循环计划续期。"""
    with UserDBContext() as user_db:
        plan_ids = TrainingService.renew_recurring(user_db, plan_id, user_id)
        if not plan_ids:
            return {"success": False, "error": "计划不存在或不是循环计划"}
        return {
            "success": True,
            "data": {
                "generatedPlanIds": plan_ids,
                "generatedWeeks": len(plan_ids),
            },
        }
