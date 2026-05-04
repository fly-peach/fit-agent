"""Exercise Router"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from src.fitme.utils.database import get_db
from src.fitme.services.exercise_service import ExerciseService
from src.fitme.schemas.exercise import (
    ExercisesResponse,
    ExerciseDetailResponse,
    ExerciseItem,
    ExerciseDetail,
    PinnedExercisesResponse,
    PinnedExerciseSchema,
    PinExerciseRequest,
    ReorderPinnedRequest,
)
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/exercises", tags=["Exercises"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录过期")
    return user


@router.get("", response_model=ExercisesResponse)
def list_exercises(
    keyword: str = Query(""),
    target_muscle: str = Query(""),
    exercise_type: str = Query(""),
    difficulty: str = Query(""),
    equipment: str = Query(""),
    force_type: str = Query(""),
    mechanics: str = Query(""),
    limit: int = Query(200),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取健身动作列表"""
    results = ExerciseService.list_exercises(
        db,
        user_id=current_user.user_id,
        keyword=keyword,
        target_muscle=target_muscle,
        exercise_type=exercise_type,
        difficulty=difficulty,
        equipment=equipment,
        force_type=force_type,
        mechanics=mechanics,
        limit=limit,
    )
    data = [ExerciseItem.from_orm(ex, is_pinned) for ex, is_pinned in results]
    return ExercisesResponse(data=data)


@router.get("/{exercise_id}", response_model=ExerciseDetailResponse)
def get_exercise(
    exercise_id: int = Path(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取动作详情"""
    result = ExerciseService.get_exercise(db, current_user.user_id, exercise_id)
    if not result:
        raise HTTPException(status_code=404, detail="动作不存在")
    exercise, is_pinned = result
    return ExerciseDetailResponse(data=ExerciseDetail.from_orm(exercise, is_pinned))


@router.get("/categories/muscles")
def get_muscle_categories(db: Session = Depends(get_db)):
    """获取目标肌肉分类"""
    muscles = ExerciseService.get_target_muscles(db)
    return {"code": 200, "data": muscles}


@router.get("/categories/types")
def get_type_categories(db: Session = Depends(get_db)):
    """获取动作类型分类"""
    types = ExerciseService.get_exercise_types(db)
    return {"code": 200, "data": types}


@router.get("/categories/equipment")
def get_equipment_categories(db: Session = Depends(get_db)):
    """获取器械分类"""
    equipment = ExerciseService.get_equipment_list(db)
    return {"code": 200, "data": equipment}


@router.get("/categories/force-types")
def get_force_type_categories(db: Session = Depends(get_db)):
    """获取发力类型分类"""
    force_types = ExerciseService.get_force_types(db)
    return {"code": 200, "data": force_types}


@router.get("/categories/mechanics")
def get_mechanics_categories(db: Session = Depends(get_db)):
    """获取力学类型分类"""
    mechanics = ExerciseService.get_mechanics_list(db)
    return {"code": 200, "data": mechanics}


# --- 收藏 ---

@router.post("/pin")
def pin_exercise(
    data: PinExerciseRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """收藏动作"""
    pinned = ExerciseService.pin_exercise(db, current_user.user_id, data.exerciseId)
    if pinned is None:
        raise HTTPException(status_code=400, detail="已收藏或动作不存在")
    return {"code": 200, "message": "收藏成功"}


@router.delete("/pin/{exercise_id}")
def unpin_exercise(
    exercise_id: int = Path(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消收藏"""
    success = ExerciseService.unpin_exercise(db, current_user.user_id, exercise_id)
    if not success:
        raise HTTPException(status_code=404, detail="未找到收藏")
    return {"code": 200, "message": "取消收藏成功"}


@router.get("/pinned", response_model=PinnedExercisesResponse)
def get_pinned_exercises(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我的收藏"""
    pinned = ExerciseService.get_pinned_exercises(db, current_user.user_id)
    return PinnedExercisesResponse(data=[PinnedExerciseSchema.from_orm(p) for p in pinned])


@router.post("/pin/reorder")
def reorder_pinned(
    data: ReorderPinnedRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """调整收藏排序"""
    success = ExerciseService.reorder_pinned(db, current_user.user_id, data.exerciseIds)
    if not success:
        raise HTTPException(status_code=400, detail="排序失败")
    return {"code": 200, "message": "排序更新成功"}
