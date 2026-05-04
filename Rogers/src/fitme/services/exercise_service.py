"""Exercise Service"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import distinct
from typing import Optional, List
from ..models import Exercise, UserPinnedExercise


class ExerciseService:
    """健身动作服务"""

    @staticmethod
    def list_exercises(
        db: Session,
        user_id: int,
        keyword: str = "",
        target_muscle: str = "",
        exercise_type: str = "",
        difficulty: str = "",
        equipment: str = "",
        force_type: str = "",
        mechanics: str = "",
        limit: int = 200,
    ) -> List[tuple]:
        """获取动作列表，附带用户收藏状态。返回 (Exercise, is_pinned) 元组列表"""
        query = db.query(Exercise).filter(Exercise.is_active == True)

        if keyword:
            query = query.filter(
                Exercise.name_cn.contains(keyword) | Exercise.name_en.contains(keyword)
            )
        if target_muscle:
            query = query.filter(Exercise.target_muscle == target_muscle)
        if exercise_type:
            query = query.filter(Exercise.exercise_type == exercise_type)
        if difficulty:
            query = query.filter(Exercise.difficulty == difficulty)
        if equipment:
            query = query.filter(Exercise.equipment == equipment)
        if force_type:
            query = query.filter(Exercise.force_type == force_type)
        if mechanics:
            query = query.filter(Exercise.mechanics == mechanics)

        exercises = query.order_by(Exercise.name_cn).limit(limit).all()

        # 批量获取用户收藏的 exercise_id
        pinned_ids = set()
        if user_id:
            pinned = db.query(UserPinnedExercise.exercise_id).filter(
                UserPinnedExercise.user_id == user_id
            ).all()
            pinned_ids = {p[0] for p in pinned}

        return [(ex, ex.exercise_id in pinned_ids) for ex in exercises]

    @staticmethod
    def get_exercise(db: Session, user_id: int, exercise_id: int) -> Optional[tuple]:
        """获取单个动作详情，附带收藏状态"""
        exercise = db.query(Exercise).filter(
            Exercise.exercise_id == exercise_id
        ).first()
        if not exercise:
            return None

        is_pinned = False
        if user_id:
            is_pinned = db.query(UserPinnedExercise).filter(
                UserPinnedExercise.user_id == user_id,
                UserPinnedExercise.exercise_id == exercise_id,
            ).first() is not None

        return (exercise, is_pinned)

    @staticmethod
    def get_target_muscles(db: Session) -> List[str]:
        """获取所有目标肌肉分类"""
        results = db.query(distinct(Exercise.target_muscle)).order_by(Exercise.target_muscle).all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_exercise_types(db: Session) -> List[str]:
        """获取所有动作类型"""
        results = db.query(distinct(Exercise.exercise_type)).order_by(Exercise.exercise_type).all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_equipment_list(db: Session) -> List[str]:
        """获取所有器械分类"""
        results = db.query(distinct(Exercise.equipment)).order_by(Exercise.equipment).all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_force_types(db: Session) -> List[str]:
        """获取发力类型分类"""
        results = db.query(distinct(Exercise.force_type)).order_by(Exercise.force_type).all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_mechanics_list(db: Session) -> List[str]:
        """获取力学类型分类"""
        results = db.query(distinct(Exercise.mechanics)).order_by(Exercise.mechanics).all()
        return [r[0] for r in results if r[0]]

    # --- 收藏功能 ---

    @staticmethod
    def pin_exercise(db: Session, user_id: int, exercise_id: int) -> Optional[UserPinnedExercise]:
        """收藏动作，如果已收藏则返回 None"""
        existing = db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id == exercise_id,
        ).first()
        if existing:
            return None

        # 检查动作是否存在
        exercise = db.query(Exercise).filter(Exercise.exercise_id == exercise_id).first()
        if not exercise:
            return None

        # 获取当前最大 sort_order
        max_order = db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id
        ).order_by(UserPinnedExercise.sort_order.desc()).first()
        new_order = (max_order.sort_order + 1) if max_order else 0

        pinned = UserPinnedExercise(
            user_id=user_id,
            exercise_id=exercise_id,
            sort_order=new_order,
        )
        db.add(pinned)
        db.commit()
        db.refresh(pinned)
        return pinned

    @staticmethod
    def unpin_exercise(db: Session, user_id: int, exercise_id: int) -> bool:
        """取消收藏"""
        pinned = db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id == exercise_id,
        ).first()
        if pinned:
            db.delete(pinned)
            db.commit()
            return True
        return False

    @staticmethod
    def get_pinned_exercises(db: Session, user_id: int) -> List[UserPinnedExercise]:
        """获取用户收藏列表（按 sort_order 排序）"""
        return db.query(UserPinnedExercise).options(
            joinedload(UserPinnedExercise.exercise)
        ).filter(
            UserPinnedExercise.user_id == user_id
        ).order_by(UserPinnedExercise.sort_order).all()

    @staticmethod
    def reorder_pinned(db: Session, user_id: int, exercise_ids: List[int]) -> bool:
        """调整收藏排序。exercise_ids 按新顺序排列"""
        # 验证所有 exercise_id 都属于该用户
        existing = db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id.in_(exercise_ids),
        ).all()
        if len(existing) != len(exercise_ids):
            return False

        for idx, ex_id in enumerate(exercise_ids):
            pinned = db.query(UserPinnedExercise).filter(
                UserPinnedExercise.user_id == user_id,
                UserPinnedExercise.exercise_id == ex_id,
            ).first()
            if pinned:
                pinned.sort_order = idx

        db.commit()
        return True
