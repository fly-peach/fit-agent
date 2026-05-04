"""种子脚本：从 JSON 文件导入健身动作数据到数据库。

用法：
    cd rogers
    python scripts/seed_exercises.py
"""
import json
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fitme.models import Exercise
from fitme.utils.database import engine, SessionLocal


def main():
    json_path = os.path.join(os.path.dirname(__file__), "..", "健身动作数据大全_中文版说明.json")
    if not os.path.exists(json_path):
        print(f"错误: 找不到文件 {json_path}")
        sys.exit(1)

    print("正在读取健身动作数据...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"  共 {len(data)} 个动作")

    # Create table if not exists
    Exercise.__table__.create(engine, checkfirst=True)

    session = SessionLocal()

    try:
        # Clear existing data
        deleted = session.query(Exercise).delete()
        if deleted:
            print(f"  已清空 {deleted} 条旧数据")

        # Insert exercises
        exercises = []
        skipped = 0
        for item in data:
            name_cn = item.get("动作名称", "").strip()
            if not name_cn:
                skipped += 1
                continue

            instructions = item.get("动作说明", [])
            if isinstance(instructions, list):
                instructions = json.dumps(instructions, ensure_ascii=False)
            elif not instructions:
                instructions = "[]"

            helper_muscles = item.get("辅助肌肉", [])
            if isinstance(helper_muscles, list):
                helper_muscles = ",".join(helper_muscles)

            exercise = Exercise(
                name_cn=name_cn,
                name_en=item.get("动作名称英文", ""),
                difficulty=item.get("难度") or None,
                force_type=item.get("发力类型") or None,
                mechanics=item.get("力学类型") or None,
                equipment=item.get("所需器械") or None,
                exercise_type=item.get("动作类型") or None,
                target_muscle=item.get("目标肌肉", [""])[0] if item.get("目标肌肉") else "",
                helper_muscles=helper_muscles or "",
                instructions=instructions,
                is_active=True,
            )
            exercises.append(exercise)

        session.bulk_save_objects(exercises)
        session.commit()
        print(f"\n  成功导入 {len(exercises)} 个动作")
        if skipped:
            print(f"  跳过 {skipped} 条（缺少动作名称）")

        # Summary
        print("\n  按动作类型分布:")
        result = session.execute(
            text("SELECT exercise_type, COUNT(*) as cnt FROM exercises GROUP BY exercise_type ORDER BY cnt DESC")
        )
        for row in result:
            print(f"    {row[0] or '未分类'}: {row[1]} 条")

        print(f"\n  按难度分布:")
        result = session.execute(
            text("SELECT difficulty, COUNT(*) as cnt FROM exercises GROUP BY difficulty ORDER BY difficulty")
        )
        for row in result:
            print(f"    {row[0] or '未分类'}: {row[1]} 条")

        print(f"\n  按目标肌肉分布:")
        result = session.execute(
            text("SELECT target_muscle, COUNT(*) as cnt FROM exercises GROUP BY target_muscle ORDER BY cnt DESC")
        )
        for row in result:
            print(f"    {row[0]}: {row[1]} 条")

    except Exception as e:
        session.rollback()
        print(f"\n  错误: {e}")
        raise
    finally:
        session.close()

    print("\n  完成！")


if __name__ == "__main__":
    main()
