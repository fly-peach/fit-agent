"""命令行脚本：手动初始化 fitbase.db

通常无需手动运行，应用启动时会自动初始化。
此脚本用于首次部署或重置基础数据库。

用法：
    cd rogers
    python scripts/init_base_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitme.seed import seed_base_db


def main():
    print("初始化 fitbase.db...")
    result = seed_base_db()
    for table, count in result.items():
        if count > 0:
            print(f"  ✓ {table}: 导入 {count} 条")
        else:
            print(f"  - {table}: 已有数据，跳过")
    print("完成！")


if __name__ == "__main__":
    main()
