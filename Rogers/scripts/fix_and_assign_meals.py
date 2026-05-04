"""修正食物分类错误 + 分配餐次标签。

用法：
    cd rogers
    python scripts/fix_and_assign_meals.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "fitagent.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Ensure suitable_meals column exists
    cur.execute("PRAGMA table_info(food_items)")
    cols = [row["name"] for row in cur.fetchall()]
    if "suitable_meals" not in cols:
        cur.execute("ALTER TABLE food_items ADD COLUMN suitable_meals TEXT DEFAULT 'breakfast,lunch,dinner'")
        print("  Added suitable_meals column")

    # 2. Fix category errors ---------------------------------------------------
    # (name, wrong_category, correct_category)
    category_fixes = [
        # 错分到蔬菜的水果
        ("苹果", "蔬菜", "水果"),
        ("西瓜", "蔬菜", "水果"),
        ("芒果", "蔬菜", "水果"),
        ("菠萝", "蔬菜", "水果"),
        ("火龙果", "蔬菜", "水果"),
        ("木瓜", "蔬菜", "水果"),
        # 错分到水果的蔬菜/菌类
        ("山药", "水果", "蔬菜"),
        ("木耳", "水果", "蔬菜"),
        # 错分到水果的坚果
        ("核桃", "水果", "坚果"),
        ("杏仁", "水果", "坚果"),
        # 错分到蔬菜的坚果
        ("瓜子", "蔬菜", "坚果"),
        ("腰果", "蔬菜", "坚果"),
        ("开心果", "蔬菜", "坚果"),
        # 错分到蔬菜的调料
        ("黄油", "蔬菜", "调料"),
        ("白糖", "蔬菜", "调料"),
        # 错分到肉类的其他
        ("猪油", "肉类", "调料"),
        # 错分到肉类的蛋类
        ("鸡蛋", "肉类", "蛋类"),
        ("鸭蛋", "肉类", "蛋类"),
        # 错分到水果的肉类
        ("牛油果", "肉类", "水果"),
        # 错分到水产的蔬菜（菌类）
        ("杏鲍菇", "水产", "蔬菜"),
        # 错分到其他的蔬菜
        ("莲藕", "其他", "蔬菜"),
        ("洋葱", "其他", "蔬菜"),
        ("大蒜", "其他", "蔬菜"),
        ("茄子", "其他", "蔬菜"),
        ("草莓", "其他", "水果"),
        # 错分到其他的海鲜
        ("蛤蜊", "其他", "水产"),
        ("牡蛎", "其他", "水产"),
        # 错分到猪肉的菜品
        ("红烧牛肉", "猪肉", "牛肉"),
        ("红烧羊肉", "猪肉", "羊肉"),
        # 错分到鱼虾的菜品
        ("鱼香肉丝", "鱼虾", "猪肉"),
        ("红烧鱼", "猪肉", "鱼虾"),
        ("糖醋鱼", "猪肉", "鱼虾"),
        # 错分到鸡肉的蛋类菜品
        ("西红柿炒鸡蛋", "鸡肉", "蛋类"),
        ("韭菜炒鸡蛋", "鸡肉", "蛋类"),
        ("虎皮鸡蛋", "鸡肉", "蛋类"),
        # 错分到鱼虾的蛋类菜品
        ("蒸蛋", "鱼虾", "蛋类"),
        # 错分到猪肉的海鲜菜品
        ("红烧鲍鱼", "猪肉", "海鲜"),
        # 错分到鱼虾的蔬菜菜品
        ("鱼香茄子", "鱼虾", "蔬菜"),
        # 错分到猪肉的蔬菜菜品
        ("红烧冬瓜", "猪肉", "蔬菜"),
        # 错分到主食的菜品
        ("锅包肉", "主食", "猪肉"),
        ("粉蒸排骨", "主食", "猪肉"),
        # 错分到主食的海鲜
        ("蒜蓉粉丝扇贝", "主食", "海鲜"),
        # 错分到主食的蛋类
        ("荷包蛋", "主食", "蛋类"),
        # 错分到主食的蔬菜
        ("手撕包菜", "主食", "蔬菜"),
        # 错分到蔬菜的猪肉菜品
        ("蒜苗炒肉片", "蔬菜", "猪肉"),
        ("农家小炒肉", "蔬菜", "猪肉"),
        # 错分到主食的其他
        ("花卷", "其他", "主食"),
        ("馄饨", "其他", "主食"),
        ("春卷", "其他", "主食"),
        ("肉夹馍", "其他", "主食"),
        ("酸辣土豆丝", "其他", "猪肉"),
        ("地三鲜", "其他", "蔬菜"),
        ("干煸豆角", "其他", "蔬菜"),
        ("青椒肉片", "其他", "猪肉"),
        ("蒜泥白肉", "其他", "猪肉"),
        ("蚂蚁上树", "其他", "猪肉"),
        ("咕噜肉", "其他", "猪肉"),
        ("脆皮五花肉", "其他", "猪肉"),
        ("夫妻肺片", "其他", "猪肉"),
        # 错分到蔬菜的海鲜
        ("凉拌海带丝", "海鲜", "其他"),
    ]

    fixed = 0
    for name, wrong, correct in category_fixes:
        cur.execute(
            "UPDATE food_items SET category = ? WHERE name = ? AND category = ? AND source = 'system'",
            (correct, name, wrong),
        )
        if cur.rowcount > 0:
            fixed += cur.rowcount

    print(f"  修正了 {fixed} 条分类错误")

    # 3. Assign meal types ----------------------------------------------------
    # Rules based on food name and category
    meal_rules = [
        # --- Breakfast-only / breakfast-heavy ---
        ("breakfast", [
            # 粥类
            "白粥", "皮蛋瘦肉粥", "小米粥", "八宝粥", "粥 (白)",
            # 面点类
            "馒头", "花卷", "包子 (肉)", "包子 (素)", "油条", "烧饼",
            "手抓饼", "煎饼果子", "鸡蛋灌饼", "春卷", "肠粉",
            # 蛋类
            "茶叶蛋", "荷包蛋", "卤蛋", "蒸蛋",
            # 饮品
            "豆浆",
            # 其他早餐
            "皮蛋", "咸蛋", "咸鸭蛋", "鹌鹑蛋",
        ]),
        # --- Lunch/Dinner heavy dishes (not typical breakfast) ---
        ("lunch,dinner", [
            # 火锅类
            "麻辣火锅", "番茄火锅", "菌菇火锅", "清汤火锅",
            "羊肉火锅", "牛肉火锅", "干锅肥肠",
            # 重口味大菜
            "红烧肉", "回锅肉", "梅菜扣肉", "东坡肉", "狮子头",
            "红烧排骨", "糖醋排骨", "卤猪蹄", "红烧猪尾",
            "水煮牛肉", "酸汤肥牛",
            "清炖羊肉", "红烧羊肉", "孜然羊肉", "烤羊肉串",
            "手抓羊肉", "羊肉泡馍", "羊杂汤", "煎羊排", "葱爆羊肉",
            "大盘鸡", "黄焖鸡", "鸡公煲", "辣子鸡", "叫花鸡",
            "水煮鱼", "酸菜鱼", "烤鱼", "剁椒鱼头",
            "油焖大虾", "麻辣小龙虾", "蒜蓉小龙虾", "椒盐虾",
            "椒盐皮皮虾",
            "锅包肉", "脆皮五花肉", "咕噜肉",
            "爆炒鸡胗", "虎皮凤爪", "泡椒炒鸡杂",
            # 汤类（通常午/晚餐）
            "老母鸡汤", "鱼头豆腐汤", "冬瓜排骨汤", "玉米排骨汤",
            "紫菜蛋花汤", "西红柿蛋汤", "酸辣汤",
            # 凉拌菜
            "凉拌皮蛋", "夫妻肺片", "凉拌猪耳朵", "凉拌凤爪",
            # 海鲜大菜
            "葱烧海参", "红烧鲍鱼", "大闸蟹",
            # 主食类大碗
            "螺蛳粉", "炒面", "炸酱面", "热干面", "凉面",
            "肉夹馍",
        ]),
    ]

    # Apply explicit rules first
    updated = 0
    for meal_type, names in meal_rules:
        for name in names:
            cur.execute(
                "UPDATE food_items SET suitable_meals = ? WHERE name = ? AND source = 'system'",
                (meal_type, name),
            )
            if cur.rowcount > 0:
                updated += cur.rowcount

    print(f"  为 {updated} 条食物分配了明确餐次")

    # 4. Default: remaining items get all three meals --------------------------
    cur.execute(
        "UPDATE food_items SET suitable_meals = 'breakfast,lunch,dinner' "
        "WHERE suitable_meals IS NULL AND source = 'system'"
    )
    remaining = cur.rowcount
    print(f"  剩余 {remaining} 条食物标记为三餐皆可")

    # 5. Remove duplicates ----------------------------------------------------
    # Find duplicates by name + category
    cur.execute("""
        SELECT name, category, MIN(food_id) as keep_id
        FROM food_items WHERE source = 'system'
        GROUP BY name, category HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    removed = 0
    for dup in duplicates:
        cur.execute(
            "DELETE FROM food_items WHERE name = ? AND category = ? AND food_id != ? AND source = 'system'",
            (dup["name"], dup["category"], dup["keep_id"]),
        )
        removed += cur.rowcount

    if removed:
        print(f"  删除了 {removed} 条重复食物")

    conn.commit()

    # 6. Summary ---------------------------------------------------------------
    cur.execute("SELECT COUNT(*) as cnt FROM food_items WHERE source = 'system'")
    total = cur.fetchone()["cnt"]

    cur.execute("SELECT suitable_meals, COUNT(*) as cnt FROM food_items WHERE source = 'system' GROUP BY suitable_meals")
    breakdown = cur.fetchall()

    print(f"\n  当前共 {total} 条系统食物")
    print("  餐次分布:")
    for row in breakdown:
        label = row["suitable_meals"]
        cnt = row["cnt"]
        print(f"    {label}: {cnt} 条")

    conn.close()
    print("\n  完成！")


if __name__ == "__main__":
    main()
