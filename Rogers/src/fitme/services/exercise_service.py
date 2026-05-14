"""Exercise Service - Dual Database Support"""
import json
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import Optional, List, Tuple, Union
from ..models import Exercise, UserPinnedExercise, CustomExerciseItem


class ExerciseService:
    """健身动作服务 - 使用双数据库
    - base_db: Exercise (健身动作库)
    - user_db: UserPinnedExercise, CustomExerciseItem (用户数据)
    """

    @staticmethod
    def list_exercises(
        base_db: Session,
        user_db: Session,
        user_id: int,
        keyword: str = "",
        target_muscle: str = "",
        exercise_type: str = "",
        difficulty: str = "",
        equipment: str = "",
        force_type: str = "",
        mechanics: str = "",
        limit: int = 200,
    ) -> List[Tuple[Union[Exercise, CustomExerciseItem], bool, str]]:
        """获取动作列表，附带用户收藏状态和来源。
        返回 (exercise_object, is_pinned, source) 元组列表
        """
        # 1. 查询系统动作
        system_query = base_db.query(Exercise).filter(Exercise.is_active == True)

        if keyword:
            system_query = system_query.filter(
                Exercise.name_cn.contains(keyword) | Exercise.name_en.contains(keyword)
            )
        if target_muscle:
            system_query = system_query.filter(Exercise.target_muscle == target_muscle)
        if exercise_type:
            system_query = system_query.filter(Exercise.exercise_type == exercise_type)
        if difficulty:
            system_query = system_query.filter(Exercise.difficulty == difficulty)
        if equipment:
            system_query = system_query.filter(Exercise.equipment == equipment)
        if force_type:
            system_query = system_query.filter(Exercise.force_type == force_type)
        if mechanics:
            system_query = system_query.filter(Exercise.mechanics == mechanics)

        system_exercises = system_query.order_by(Exercise.name_cn).limit(limit).all()

        # 2. 查询用户自定义动作
        custom_query = user_db.query(CustomExerciseItem).filter(CustomExerciseItem.user_id == user_id)

        if keyword:
            custom_query = custom_query.filter(
                CustomExerciseItem.name_cn.contains(keyword) |
                (CustomExerciseItem.name_en is not None and CustomExerciseItem.name_en.contains(keyword))
            )
        if target_muscle:
            custom_query = custom_query.filter(CustomExerciseItem.target_muscle == target_muscle)
        if exercise_type:
            custom_query = custom_query.filter(CustomExerciseItem.exercise_type == exercise_type)
        if difficulty:
            custom_query = custom_query.filter(CustomExerciseItem.difficulty == difficulty)
        if equipment:
            custom_query = custom_query.filter(CustomExerciseItem.equipment == equipment)
        if force_type:
            custom_query = custom_query.filter(CustomExerciseItem.force_type == force_type)
        if mechanics:
            custom_query = custom_query.filter(CustomExerciseItem.mechanics == mechanics)

        custom_exercises = custom_query.order_by(CustomExerciseItem.name_cn).limit(limit).all()

        # 3. 批量获取用户收藏的 exercise_id
        pinned_ids = set()
        if user_id:
            pinned = user_db.query(UserPinnedExercise.exercise_id).filter(
                UserPinnedExercise.user_id == user_id
            ).all()
            pinned_ids = {p[0] for p in pinned}

        # 4. 合并结果，系统动作在前，自定义在后
        results = []
        for ex in system_exercises:
            results.append((ex, ex.exercise_id in pinned_ids, "system"))
        for ex in custom_exercises:
            results.append((ex, ex.exercise_id in pinned_ids, "custom"))

        return results[:limit]

    @staticmethod
    def get_exercise(
        base_db: Session,
        user_db: Session,
        user_id: int,
        exercise_id: int
    ) -> Optional[Tuple[Union[Exercise, CustomExerciseItem], bool, str]]:
        """获取单个动作详情，附带收藏状态和来源。
        返回 (exercise_object, is_pinned, source) 或 None
        """
        # 1. 先查系统动作库
        exercise = base_db.query(Exercise).filter(
            Exercise.exercise_id == exercise_id
        ).first()

        if exercise:
            is_pinned = False
            if user_id:
                is_pinned = user_db.query(UserPinnedExercise).filter(
                    UserPinnedExercise.user_id == user_id,
                    UserPinnedExercise.exercise_id == exercise_id,
                ).first() is not None
            return (exercise, is_pinned, "system")

        # 2. 再查用户自定义动作库
        custom_exercise = user_db.query(CustomExerciseItem).filter(
            CustomExerciseItem.exercise_id == exercise_id,
            CustomExerciseItem.user_id == user_id
        ).first()

        if custom_exercise:
            is_pinned = False
            if user_id:
                is_pinned = user_db.query(UserPinnedExercise).filter(
                    UserPinnedExercise.user_id == user_id,
                    UserPinnedExercise.exercise_id == exercise_id,
                ).first() is not None
            return (custom_exercise, is_pinned, "custom")

        return None

    @staticmethod
    def get_target_muscles(base_db: Session, user_db: Optional[Session] = None, user_id: Optional[int] = None) -> List[str]:
        """获取所有目标肌肉分类（包含用户自定义）"""
        system_muscles = base_db.query(distinct(Exercise.target_muscle)).order_by(Exercise.target_muscle).all()
        system_set = {m[0] for m in system_muscles if m[0]}

        if user_db and user_id:
            custom_muscles = user_db.query(distinct(CustomExerciseItem.target_muscle)).filter(
                CustomExerciseItem.user_id == user_id
            ).order_by(CustomExerciseItem.target_muscle).all()
            custom_set = {m[0] for m in custom_muscles if m[0]}
            system_set.update(custom_set)

        return sorted(system_set)

    @staticmethod
    def get_exercise_types(base_db: Session, user_db: Optional[Session] = None, user_id: Optional[int] = None) -> List[str]:
        """获取所有动作类型分类（包含用户自定义）"""
        system_types = base_db.query(distinct(Exercise.exercise_type)).order_by(Exercise.exercise_type).all()
        system_set = {t[0] for t in system_types if t[0]}

        if user_db and user_id:
            custom_types = user_db.query(distinct(CustomExerciseItem.exercise_type)).filter(
                CustomExerciseItem.user_id == user_id
            ).order_by(CustomExerciseItem.exercise_type).all()
            custom_set = {t[0] for t in custom_types if t[0]}
            system_set.update(custom_set)

        return sorted(system_set)

    @staticmethod
    def get_equipment_list(base_db: Session, user_db: Optional[Session] = None, user_id: Optional[int] = None) -> List[str]:
        """获取所有器械分类（包含用户自定义）"""
        system_equip = base_db.query(distinct(Exercise.equipment)).order_by(Exercise.equipment).all()
        system_set = {e[0] for e in system_equip if e[0]}

        if user_db and user_id:
            custom_equip = user_db.query(distinct(CustomExerciseItem.equipment)).filter(
                CustomExerciseItem.user_id == user_id
            ).order_by(CustomExerciseItem.equipment).all()
            custom_set = {e[0] for e in custom_equip if e[0]}
            system_set.update(custom_set)

        return sorted(system_set)

    @staticmethod
    def get_force_types(base_db: Session) -> List[str]:
        """获取发力类型分类"""
        results = base_db.query(distinct(Exercise.force_type)).order_by(Exercise.force_type).all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_mechanics_list(base_db: Session) -> List[str]:
        """获取力学类型分类"""
        results = base_db.query(distinct(Exercise.mechanics)).order_by(Exercise.mechanics).all()
        return [r[0] for r in results if r[0]]

    # --- 收藏功能 ---

    @staticmethod
    def pin_exercise(
        base_db: Session,
        user_db: Session,
        user_id: int,
        exercise_id: int
    ) -> Optional[UserPinnedExercise]:
        """收藏动作，如果已收藏则返回 None"""
        existing = user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id == exercise_id,
        ).first()
        if existing:
            return None

        # 检查动作是否存在（系统库或自定义库）
        exercise_exists = base_db.query(Exercise).filter(
            Exercise.exercise_id == exercise_id
        ).first() is not None

        if not exercise_exists:
            exercise_exists = user_db.query(CustomExerciseItem).filter(
                CustomExerciseItem.exercise_id == exercise_id,
                CustomExerciseItem.user_id == user_id
            ).first() is not None

        if not exercise_exists:
            return None

        # 获取当前最大 sort_order
        max_order = user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id
        ).order_by(UserPinnedExercise.sort_order.desc()).first()
        new_order = (max_order.sort_order + 1) if max_order else 0

        pinned = UserPinnedExercise(
            user_id=user_id,
            exercise_id=exercise_id,
            sort_order=new_order,
        )
        user_db.add(pinned)
        user_db.commit()
        user_db.refresh(pinned)
        return pinned

    @staticmethod
    def unpin_exercise(user_db: Session, user_id: int, exercise_id: int) -> bool:
        """取消收藏"""
        pinned = user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id == exercise_id,
        ).first()
        if pinned:
            user_db.delete(pinned)
            user_db.commit()
            return True
        return False

    @staticmethod
    def get_pinned_exercises(
        base_db: Session,
        user_db: Session,
        user_id: int
    ) -> List[UserPinnedExercise]:
        """获取用户收藏列表（按 sort_order 排序）"""
        # 注意：由于 Exercise 可能在不同数据库，无法使用 joinedload
        # 需要先获取 UserPinnedExercise，再从 base_db 或 user_db 批量获取
        pinned_list = user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id
        ).order_by(UserPinnedExercise.sort_order).all()

        # 批量获取 Exercise（同时从两个库获取）
        if pinned_list:
            exercise_ids = [p.exercise_id for p in pinned_list]

            # 从系统库获取
            system_exercises = base_db.query(Exercise).filter(
                Exercise.exercise_id.in_(exercise_ids)
            ).all()
            exercise_map = {ex.exercise_id: ex for ex in system_exercises}

            # 从用户自定义库获取
            custom_exercises = user_db.query(CustomExerciseItem).filter(
                CustomExerciseItem.exercise_id.in_(exercise_ids),
                CustomExerciseItem.user_id == user_id
            ).all()
            for ex in custom_exercises:
                exercise_map[ex.exercise_id] = ex

            # 手动绑定
            for pinned in pinned_list:
                pinned.exercise = exercise_map.get(pinned.exercise_id)

        return pinned_list

    @staticmethod
    def reorder_pinned(user_db: Session, user_id: int, exercise_ids: List[int]) -> bool:
        """调整收藏排序。exercise_ids 按新顺序排列"""
        # 验证所有 exercise_id 都属于该用户
        existing = user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id.in_(exercise_ids),
        ).all()
        if len(existing) != len(exercise_ids):
            return False

        for idx, ex_id in enumerate(exercise_ids):
            pinned = user_db.query(UserPinnedExercise).filter(
                UserPinnedExercise.user_id == user_id,
                UserPinnedExercise.exercise_id == ex_id,
            ).first()
            if pinned:
                pinned.sort_order = idx

        user_db.commit()
        return True

    # --- 自定义动作功能 ---

    @staticmethod
    def create_custom_exercise(
        user_db: Session,
        user_id: int,
        data: dict
    ) -> CustomExerciseItem:
        """创建自定义动作"""
        instructions_json = json.dumps(data.get('instructions', []), ensure_ascii=False)

        exercise = CustomExerciseItem(
            user_id=user_id,
            name_cn=data.get('nameCn', data.get('name_cn', '')),
            name_en=data.get('nameEn', data.get('name_en')) or None,
            difficulty=data.get('difficulty') or None,
            force_type=data.get('forceType', data.get('force_type')) or None,
            mechanics=data.get('mechanics') or None,
            equipment=data.get('equipment') or None,
            exercise_type=data.get('exerciseType', data.get('exercise_type')) or None,
            target_muscle=data.get('targetMuscle', data.get('target_muscle', '')),
            helper_muscles=data.get('helperMuscles', data.get('helper_muscles', '')) or '',
            instructions=instructions_json,
        )
        user_db.add(exercise)
        user_db.commit()
        user_db.refresh(exercise)
        return exercise

    @staticmethod
    def update_custom_exercise(
        user_db: Session,
        user_id: int,
        exercise_id: int,
        data: dict
    ) -> Optional[CustomExerciseItem]:
        """更新自定义动作"""
        exercise = user_db.query(CustomExerciseItem).filter(
            CustomExerciseItem.exercise_id == exercise_id,
            CustomExerciseItem.user_id == user_id
        ).first()

        if not exercise:
            return None

        if 'nameCn' in data or 'name_cn' in data:
            val = data.get('nameCn', data.get('name_cn'))
            if val is not None:
                exercise.name_cn = val
        if 'nameEn' in data or 'name_en' in data:
            val = data.get('nameEn', data.get('name_en'))
            exercise.name_en = val if val is not None else None
        if 'difficulty' in data:
            exercise.difficulty = data['difficulty'] if data['difficulty'] is not None else None
        if 'forceType' in data or 'force_type' in data:
            val = data.get('forceType', data.get('force_type'))
            exercise.force_type = val if val is not None else None
        if 'mechanics' in data:
            exercise.mechanics = data['mechanics'] if data['mechanics'] is not None else None
        if 'equipment' in data:
            exercise.equipment = data['equipment'] if data['equipment'] is not None else None
        if 'exerciseType' in data or 'exercise_type' in data:
            val = data.get('exerciseType', data.get('exercise_type'))
            exercise.exercise_type = val if val is not None else None
        if 'targetMuscle' in data or 'target_muscle' in data:
            val = data.get('targetMuscle', data.get('target_muscle'))
            if val is not None:
                exercise.target_muscle = val
        if 'helperMuscles' in data or 'helper_muscles' in data:
            val = data.get('helperMuscles', data.get('helper_muscles'))
            exercise.helper_muscles = val if val is not None else ''
        if 'instructions' in data:
            exercise.instructions = json.dumps(data['instructions'], ensure_ascii=False)

        user_db.commit()
        user_db.refresh(exercise)
        return exercise

    @staticmethod
    def delete_custom_exercise(
        user_db: Session,
        user_id: int,
        exercise_id: int
    ) -> bool:
        """删除自定义动作"""
        exercise = user_db.query(CustomExerciseItem).filter(
            CustomExerciseItem.exercise_id == exercise_id,
            CustomExerciseItem.user_id == user_id
        ).first()

        if not exercise:
            return False

        # 同时删除收藏记录
        user_db.query(UserPinnedExercise).filter(
            UserPinnedExercise.user_id == user_id,
            UserPinnedExercise.exercise_id == exercise_id
        ).delete()

        user_db.delete(exercise)
        user_db.commit()
        return True

