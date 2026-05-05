"""Fitme 动作数据工具。"""
from __future__ import annotations

from typing import Any

from src.fitme.schemas.exercise import (
    ExerciseDetail,
    ExerciseItem,
    PinnedExerciseSchema,
)
from src.fitme.services.exercise_service import ExerciseService
from src.fitme.utils.database import BaseDBContext, UserDBContext


def search_exercises(
    user_id: int,
    keyword: str = "",
    target_muscle: str = "",
    exercise_type: str = "",
    difficulty: str = "",
    equipment: str = "",
    force_type: str = "",
    mechanics: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """搜索动作库，返回动作列表及收藏状态。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        results = ExerciseService.list_exercises(
            base_db,
            user_db,
            user_id=user_id,
            keyword=keyword,
            target_muscle=target_muscle,
            exercise_type=exercise_type,
            difficulty=difficulty,
            equipment=equipment,
            force_type=force_type,
            mechanics=mechanics,
            limit=limit,
        )
        return {
            "success": True,
            "data": [ExerciseItem.from_orm(ex, is_pinned).model_dump() for ex, is_pinned in results],
        }


def get_exercise_detail(user_id: int, exercise_id: int) -> dict[str, Any]:
    """获取单个动作详情。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        result = ExerciseService.get_exercise(base_db, user_db, user_id, exercise_id)
        if not result:
            return {"success": False, "error": "动作不存在"}
        exercise, is_pinned = result
        return {
            "success": True,
            "data": ExerciseDetail.from_orm(exercise, is_pinned).model_dump(),
        }


def get_exercise_categories() -> dict[str, Any]:
    """获取动作筛选分类。"""
    with BaseDBContext() as base_db:
        return {
            "success": True,
            "data": {
                "target_muscles": ExerciseService.get_target_muscles(base_db),
                "exercise_types": ExerciseService.get_exercise_types(base_db),
                "equipment": ExerciseService.get_equipment_list(base_db),
                "force_types": ExerciseService.get_force_types(base_db),
                "mechanics": ExerciseService.get_mechanics_list(base_db),
            },
        }


def pin_exercise(user_id: int, exercise_id: int) -> dict[str, Any]:
    """收藏动作。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        pinned = ExerciseService.pin_exercise(base_db, user_db, user_id, exercise_id)
        if pinned is None:
            return {"success": False, "error": "动作不存在或已收藏"}
        return {
            "success": True,
            "data": {
                "exercise_id": exercise_id,
                "sort_order": pinned.sort_order,
            },
        }


def unpin_exercise(user_id: int, exercise_id: int) -> dict[str, Any]:
    """取消收藏动作。"""
    with UserDBContext() as user_db:
        success = ExerciseService.unpin_exercise(user_db, user_id, exercise_id)
        if not success:
            return {"success": False, "error": "未找到该收藏动作"}
        return {"success": True, "data": {"exercise_id": exercise_id}}


def get_pinned_exercises(user_id: int) -> dict[str, Any]:
    """获取收藏动作列表。"""
    with BaseDBContext() as base_db, UserDBContext() as user_db:
        pinned = ExerciseService.get_pinned_exercises(base_db, user_db, user_id)
        return {
            "success": True,
            "data": [PinnedExerciseSchema.from_orm(item).model_dump() for item in pinned],
        }


def reorder_pinned_exercises(user_id: int, exercise_ids: list[int]) -> dict[str, Any]:
    """调整收藏动作顺序。"""
    if not exercise_ids:
        return {"success": False, "error": "exercise_ids 不能为空"}

    with UserDBContext() as user_db:
        success = ExerciseService.reorder_pinned(user_db, user_id, exercise_ids)
        if not success:
            return {"success": False, "error": "排序失败，请确认动作都已收藏"}
        return {
            "success": True,
            "data": {"exercise_ids": exercise_ids},
        }
