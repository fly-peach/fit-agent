"""Exercise Schemas"""
import json
from pydantic import BaseModel
from typing import Optional, List


class ExerciseItem(BaseModel):
    """动作列表项"""
    exerciseId: int
    nameCn: str
    nameEn: Optional[str] = None
    difficulty: Optional[str] = None
    forceType: Optional[str] = None
    mechanics: Optional[str] = None
    exerciseType: Optional[str] = None
    targetMuscle: str
    equipment: Optional[str] = None
    isPinned: bool = False

    @staticmethod
    def from_orm(exercise, is_pinned: bool = False) -> "ExerciseItem":
        return ExerciseItem(
            exerciseId=exercise.exercise_id,
            nameCn=exercise.name_cn,
            nameEn=exercise.name_en,
            difficulty=exercise.difficulty,
            forceType=exercise.force_type,
            mechanics=exercise.mechanics,
            exerciseType=exercise.exercise_type,
            targetMuscle=exercise.target_muscle,
            equipment=exercise.equipment,
            isPinned=is_pinned,
        )


class ExerciseDetail(BaseModel):
    """动作详情"""
    exerciseId: int
    nameCn: str
    nameEn: Optional[str] = None
    difficulty: Optional[str] = None
    forceType: Optional[str] = None
    mechanics: Optional[str] = None
    equipment: Optional[str] = None
    exerciseType: Optional[str] = None
    targetMuscle: str
    helperMuscles: str
    instructions: List[str] = []
    isPinned: bool = False

    @staticmethod
    def from_orm(exercise, is_pinned: bool = False) -> "ExerciseDetail":
        instructions = []
        if exercise.instructions:
            try:
                parsed = json.loads(exercise.instructions)
                if isinstance(parsed, list):
                    instructions = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return ExerciseDetail(
            exerciseId=exercise.exercise_id,
            nameCn=exercise.name_cn,
            nameEn=exercise.name_en,
            difficulty=exercise.difficulty,
            forceType=exercise.force_type,
            mechanics=exercise.mechanics,
            equipment=exercise.equipment,
            exerciseType=exercise.exercise_type,
            targetMuscle=exercise.target_muscle,
            helperMuscles=exercise.helper_muscles or "",
            instructions=instructions,
            isPinned=is_pinned,
        )


class ExercisesResponse(BaseModel):
    code: int = 200
    data: List[ExerciseItem]


class ExerciseDetailResponse(BaseModel):
    code: int = 200
    data: ExerciseDetail


# --- 计划动作项 ---

class PlanExerciseItemInput(BaseModel):
    """创建计划时的动作项"""
    exerciseId: Optional[int] = None  # 库动作引用
    customName: Optional[str] = None  # 自定义动作名称
    sets: int = 3
    reps: int = 10
    weight: Optional[float] = None
    duration: Optional[int] = None
    notes: Optional[str] = None


class PlanExerciseItemOutput(BaseModel):
    """计划中动作的返回体"""
    id: int
    exerciseId: Optional[int] = None
    customName: Optional[str] = None
    # 如果是库动作，附带信息
    nameCn: Optional[str] = None
    targetMuscle: Optional[str] = None
    helperMuscles: Optional[str] = None
    difficulty: Optional[str] = None
    forceType: Optional[str] = None
    mechanics: Optional[str] = None
    equipment: Optional[str] = None
    sets: int
    reps: int
    weight: Optional[float] = None
    duration: Optional[int] = None
    notes: Optional[str] = None


class UpdatePlanExerciseItem(BaseModel):
    """更新计划动作的组数/次数/重量"""
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration: Optional[int] = None


# --- 收藏 ---

class PinnedExerciseSchema(BaseModel):
    """用户收藏的动作"""
    pinId: int
    exerciseId: int
    nameCn: str
    nameEn: Optional[str] = None
    difficulty: Optional[str] = None
    forceType: Optional[str] = None
    mechanics: Optional[str] = None
    exerciseType: Optional[str] = None
    targetMuscle: str
    equipment: Optional[str] = None
    sortOrder: int

    @staticmethod
    def from_orm(pinned) -> "PinnedExerciseSchema":
        ex = pinned.exercise
        return PinnedExerciseSchema(
            pinId=pinned.id,
            exerciseId=ex.exercise_id,
            nameCn=ex.name_cn,
            nameEn=ex.name_en,
            difficulty=ex.difficulty,
            forceType=ex.force_type,
            mechanics=ex.mechanics,
            exerciseType=ex.exercise_type,
            targetMuscle=ex.target_muscle,
            equipment=ex.equipment,
            sortOrder=pinned.sort_order,
        )


class PinnedExercisesResponse(BaseModel):
    code: int = 200
    data: List[PinnedExerciseSchema]


class PinExerciseRequest(BaseModel):
    exerciseId: int


class ReorderPinnedRequest(BaseModel):
    exerciseIds: List[int]  # 按新顺序排列
