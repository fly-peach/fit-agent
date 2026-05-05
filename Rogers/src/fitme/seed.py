"""FitBase 数据库种子数据加载

在应用启动时自动检测并填充 fitbase.db，幂等操作（已有数据则跳过）。
数据源统一为 JSON 文件，位于 scripts/ 目录下。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import text

from .models.base_db import Base, Exercise, FoodItem
from .utils.database import base_engine, BaseSessionLocal

logger = logging.getLogger("fitagent.seed")

# 种子数据文件目录（rogers/scripts/）
_SEED_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"


# ---------------------------------------------------------------------------
# 表结构初始化
# ---------------------------------------------------------------------------

def init_tables() -> None:
    """创建 fitbase.db 的表结构（幂等）。"""
    Base.metadata.create_all(bind=base_engine)


# ---------------------------------------------------------------------------
# 动作库
# ---------------------------------------------------------------------------

def _need_seed_exercises(session) -> bool:
    return session.query(Exercise).count() == 0


def seed_exercises() -> int:
    """从 JSON 导入健身动作数据。返回导入条数，已有数据则跳过返回 0。"""
    session = BaseSessionLocal()
    try:
        if not _need_seed_exercises(session):
            return 0

        json_path = _SEED_DIR / "健身动作数据大全_中文版说明.json"
        if not json_path.exists():
            logger.warning("种子文件不存在: %s", json_path)
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        exercises = []
        for item in data:
            name_cn = item.get("动作名称", "").strip()
            if not name_cn:
                continue

            instructions = item.get("动作说明", [])
            if isinstance(instructions, list):
                instructions = json.dumps(instructions, ensure_ascii=False)
            elif not instructions:
                instructions = "[]"

            helper_muscles = item.get("辅助肌肉", [])
            if isinstance(helper_muscles, list):
                helper_muscles = ",".join(helper_muscles)

            target_muscle = item.get("目标肌肉", [])
            if isinstance(target_muscle, list):
                target_muscle = target_muscle[0] if target_muscle else ""

            exercises.append(Exercise(
                name_cn=name_cn,
                name_en=item.get("动作名称英文", ""),
                difficulty=item.get("难度") or None,
                force_type=item.get("发力类型") or None,
                mechanics=item.get("力学类型") or None,
                equipment=item.get("所需器械") or None,
                exercise_type=item.get("动作类型") or None,
                target_muscle=target_muscle or "",
                helper_muscles=helper_muscles or "",
                instructions=instructions,
                is_active=True,
            ))

        session.bulk_save_objects(exercises)
        session.commit()
        logger.info("已导入 %d 个健身动作", len(exercises))
        return len(exercises)

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 食物库
# ---------------------------------------------------------------------------

def _need_seed_foods(session) -> bool:
    return session.query(FoodItem).filter(FoodItem.source == "system").count() == 0


def seed_foods() -> int:
    """从 JSON 导入食物数据。返回导入条数，已有数据则跳过返回 0。"""
    session = BaseSessionLocal()
    try:
        if not _need_seed_foods(session):
            return 0

        json_path = _SEED_DIR / "seed_foods.json"
        if not json_path.exists():
            logger.warning("种子文件不存在: %s", json_path)
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        foods = []
        for item in data:
            foods.append(FoodItem(
                name=item["name"],
                category=item["category"],
                source="system",
                portion_unit=item.get("portion_unit"),
                portion_grams=item.get("portion_grams"),
                portion_calories=item["portion_calories"],
                calories_per_100g=item["calories_per_100g"],
                calorie_level=item.get("calorie_level"),
                suitable_meals=item.get("suitable_meals", "breakfast,lunch,dinner"),
                protein=item.get("protein", 0),
                carbs=item.get("carbs", 0),
                fat=item.get("fat", 0),
            ))

        session.bulk_save_objects(foods)
        session.commit()
        logger.info("已导入 %d 条食物数据", len(foods))
        return len(foods)

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 一键初始化
# ---------------------------------------------------------------------------

def seed_base_db() -> dict[str, int]:
    """初始化 fitbase.db：建表 + 种子数据。返回各表导入条数。"""
    init_tables()
    return {
        "exercises": seed_exercises(),
        "foods": seed_foods(),
    }
