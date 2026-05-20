"""FitBase 数据库种子数据加载

在应用启动时自动检测并填充 fitbase.db，幂等操作（已有数据则跳过）。
数据源统一为 JSON 文件，位于 scripts/ 目录下。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import text

from .models.base_db import Base, Exercise, FoodItem, TrainingCardTemplateSample
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
# 训练结果卡片模板样例
# ---------------------------------------------------------------------------

_TRAINING_CARD_TEMPLATE_SAMPLES = [
    {
        "template_key": "training-card-modern",
        "template_name": "现代动效卡",
        "description": "强调大数字统计、渐变头图和阶段总结，适合周报与近7天成果展示。",
        "highlights_json": json.dumps(
            ["大数字指标", "渐变氛围", "阶段总结区", "适合周报"], ensure_ascii=False
        ),
        "preview_html": """
<div class="training-card training-card-modern" style="font-family: Arial, sans-serif; background: linear-gradient(135deg,#0f172a 0%,#1d4ed8 50%,#38bdf8 100%); color:#fff; border-radius:24px; padding:28px; min-height:320px;">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
    <div>
      <div style="font-size:12px; opacity:.85; letter-spacing:.12em; text-transform:uppercase;">Training Result</div>
      <div style="font-size:28px; font-weight:700; margin-top:8px;">近7天训练成果</div>
      <div style="font-size:14px; opacity:.82; margin-top:8px;">阶段表现稳定提升，训练节奏良好。</div>
    </div>
    <div style="background:rgba(255,255,255,.14); padding:10px 14px; border-radius:999px; font-size:12px;">Modern</div>
  </div>
  <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:24px;">
    <div style="background:rgba(255,255,255,.12); border-radius:18px; padding:16px;"><div style="font-size:12px; opacity:.75;">训练次数</div><div style="font-size:28px; font-weight:700; margin-top:6px;">5</div></div>
    <div style="background:rgba(255,255,255,.12); border-radius:18px; padding:16px;"><div style="font-size:12px; opacity:.75;">总时长</div><div style="font-size:28px; font-weight:700; margin-top:6px;">320m</div></div>
    <div style="background:rgba(255,255,255,.12); border-radius:18px; padding:16px;"><div style="font-size:12px; opacity:.75;">热量消耗</div><div style="font-size:28px; font-weight:700; margin-top:6px;">1850</div></div>
  </div>
  <div style="margin-top:20px; padding:16px; border-radius:18px; background:rgba(255,255,255,.10); font-size:14px; line-height:1.7;">重点强化了上肢与核心训练，建议下阶段继续保持频率，同时补足下肢力量练习。</div>
</div>
""".strip(),
        "prompt_hint": "使用明亮渐变和大数字模块，顶部突出标题与阶段总结，下方以三列核心指标展示训练成果。",
        "sort_order": 10,
    },
    {
        "template_key": "training-card-magazine",
        "template_name": "杂志封面卡",
        "description": "强调编排感与分栏布局，适合月报或需要更强内容层级的结果展示。",
        "highlights_json": json.dumps(
            ["杂志排版", "分栏布局", "更强叙事感", "适合月报"], ensure_ascii=False
        ),
        "preview_html": """
<div class="training-card training-card-magazine" style="font-family: Georgia, serif; background:#f8fafc; color:#0f172a; border:1px solid #cbd5e1; border-radius:24px; padding:28px; min-height:320px;">
  <div style="display:grid; grid-template-columns:1.1fr .9fr; gap:20px;">
    <div>
      <div style="font-size:12px; letter-spacing:.28em; text-transform:uppercase; color:#475569;">Monthly Report</div>
      <div style="font-size:34px; font-weight:700; line-height:1.15; margin-top:10px;">五月训练成果</div>
      <div style="font-size:15px; color:#475569; margin-top:12px; line-height:1.8;">本月训练节奏稳定，力量训练与有氧训练分配更均衡，整体执行度高于上月。</div>
    </div>
    <div style="display:flex; flex-direction:column; gap:12px;">
      <div style="padding:14px 16px; border-radius:18px; background:#e2e8f0;"><div style="font-size:12px; color:#475569;">训练次数</div><div style="font-size:26px; font-weight:700; margin-top:6px;">12 次</div></div>
      <div style="padding:14px 16px; border-radius:18px; background:#e2e8f0;"><div style="font-size:12px; color:#475569;">总时长</div><div style="font-size:26px; font-weight:700; margin-top:6px;">14.5 小时</div></div>
      <div style="padding:14px 16px; border-radius:18px; background:#e2e8f0;"><div style="font-size:12px; color:#475569;">连续训练</div><div style="font-size:26px; font-weight:700; margin-top:6px;">8 天</div></div>
    </div>
  </div>
  <div style="margin-top:18px; display:grid; grid-template-columns:1fr 1fr; gap:14px; font-size:14px; line-height:1.7;">
    <div style="padding:14px 16px; border-radius:18px; background:#fff;">完成度优秀，重点肌群训练分布更均衡。</div>
    <div style="padding:14px 16px; border-radius:18px; background:#fff;">建议下一阶段增加恢复安排与下肢训练容量。</div>
  </div>
</div>
""".strip(),
        "prompt_hint": "采用杂志感分栏编排，左侧是标题和总结，右侧是纵向关键指标，底部补充两块结论区。",
        "sort_order": 20,
    },
    {
        "template_key": "training-card-minimal",
        "template_name": "极简摘要卡",
        "description": "强调克制留白和信息清晰度，适合移动端展示和快速浏览。",
        "highlights_json": json.dumps(
            ["极简留白", "信息清晰", "适合移动端", "摘要导向"], ensure_ascii=False
        ),
        "preview_html": """
<div class="training-card training-card-minimal" style="font-family: Arial, sans-serif; background:#ffffff; color:#111827; border:1px solid #e5e7eb; border-radius:24px; padding:28px; min-height:320px;">
  <div style="display:flex; justify-content:space-between; align-items:center; gap:16px;">
    <div>
      <div style="font-size:24px; font-weight:700;">本周训练成果</div>
      <div style="font-size:13px; color:#6b7280; margin-top:8px;">2026-05-17 至 2026-05-23</div>
    </div>
    <div style="font-size:12px; color:#2563eb; background:#eff6ff; border-radius:999px; padding:8px 12px;">Minimal</div>
  </div>
  <div style="display:flex; gap:18px; margin-top:26px; flex-wrap:wrap;">
    <div><div style="font-size:30px; font-weight:700;">5</div><div style="font-size:12px; color:#6b7280;">次训练</div></div>
    <div><div style="font-size:30px; font-weight:700;">320</div><div style="font-size:12px; color:#6b7280;">总分钟</div></div>
    <div><div style="font-size:30px; font-weight:700;">1850</div><div style="font-size:12px; color:#6b7280;">kcal</div></div>
  </div>
  <div style="margin-top:26px; padding-top:18px; border-top:1px solid #e5e7eb; font-size:14px; line-height:1.8; color:#374151;">训练完成度良好，节奏稳定，适合继续沿用当前频率并逐步增加强度。</div>
</div>
""".strip(),
        "prompt_hint": "使用极简留白风格，减少装饰，重点突出标题、日期和 3 组核心指标，结尾保留简短总结。",
        "sort_order": 30,
    },
]


def _need_seed_training_card_templates(session) -> bool:
    return session.query(TrainingCardTemplateSample).count() == 0


def seed_training_card_templates() -> int:
    """导入训练结果卡片模板样例。已有数据则跳过。"""
    session = BaseSessionLocal()
    try:
        if not _need_seed_training_card_templates(session):
            return 0

        session.bulk_save_objects(
            [TrainingCardTemplateSample(**item, template_group="training-results", is_active=True) for item in _TRAINING_CARD_TEMPLATE_SAMPLES]
        )
        session.commit()
        logger.info("已导入 %d 条训练结果卡片模板样例", len(_TRAINING_CARD_TEMPLATE_SAMPLES))
        return len(_TRAINING_CARD_TEMPLATE_SAMPLES)
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
        "training_card_templates": seed_training_card_templates(),
    }
