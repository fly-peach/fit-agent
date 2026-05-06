"""
数据迁移脚本：从旧结构迁移到新结构

将 Agent 数据从服务器端 (data/agent_db/workspace/users/{user_id})
迁移到用户本地目录 (~/.fitagent 或用户配置的目录)

使用方式:
    python scripts/migrate_agent_data.py

警告：此脚本会修改数据库，请先备份！
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载 .env 配置
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")


def migrate_agent_data():
    """迁移旧的 agent_db 结构到新的用户本地目录"""
    print("=" * 60)
    print("Agent 数据迁移脚本")
    print("=" * 60)
    print()
    print("注意：此脚本将数据从服务器端迁移到用户本地目录。")
    print("请确保已备份数据库！")
    print()

    # 旧路径（服务器端）
    old_agent_db = project_root / "data" / "agent_db"

    if not old_agent_db.exists():
        print("[跳过] 旧 agent_db 不存在，无需迁移")
        print()
        return False

    # 检查旧数据是否存在
    old_workspace = old_agent_db / "workspace" / "users"
    if not old_workspace.exists() or not any(old_workspace.iterdir()):
        print("[跳过] 旧用户数据不存在，无需迁移")
        print()
        return False

    print(f"发现旧数据位置: {old_agent_db}")
    print(f"用户数据位置: {old_workspace}")
    print()

    # 确认操作
    confirm = input("是否继续迁移？(y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消迁移")
        return False

    print()
    print("开始迁移...")
    print()

    # 初始化数据库
    from src.fitme.models import UserDBBase
    from src.fitme.models.user_db import User, UserAgentConfig
    from src.fitme.utils.database import UserSessionLocal, user_engine

    # 确保表已创建
    UserDBBase.metadata.create_all(bind=user_engine)

    db = UserSessionLocal()
    migrated_count = 0
    skipped_count = 0

    try:
        # 获取所有用户
        users = db.query(User).all()
        print(f"找到 {len(users)} 个用户")
        print()

        for user in users:
            print(f"处理用户: {user.name} (ID: {user.user_id})")

            # 检查是否已有配置
            existing_config = db.query(UserAgentConfig).filter(
                UserAgentConfig.user_id == user.user_id
            ).first()

            if existing_config:
                print(f"  - 用户已有配置: {existing_config.local_working_dir}")
                print(f"  - 跳过（需要手动处理）")
                skipped_count += 1
                print()
                continue

            # 旧的用户数据路径
            old_user_path = old_workspace / str(user.user_id)

            if not old_user_path.exists() or not any(old_user_path.iterdir()):
                print(f"  - 无旧数据，跳过")
                skipped_count += 1
                print()
                continue

            # 创建新的用户配置
            new_dir = str(Path.home() / ".fitagent")

            # 迁移数据
            print(f"  - 旧路径: {old_user_path}")
            print(f"  - 新路径: {new_dir}")

            try:
                new_path = Path(new_dir)
                new_path.mkdir(parents=True, exist_ok=True)

                # 迁移工作区内容
                old_workspace_dir = old_user_path / "workspace"

                if old_workspace_dir.exists() and any(old_workspace_dir.iterdir()):
                    new_workspace_dir = new_path / "workspace"
                    new_workspace_dir.mkdir(parents=True, exist_ok=True)

                    # 复制所有内容
                    for item in old_workspace_dir.iterdir():
                        dest = new_workspace_dir / item.name
                        if not dest.exists():
                            if item.is_dir():
                                shutil.copytree(item, dest)
                            else:
                                shutil.copy2(item, dest)

                    print(f"  - 已迁移 workspace 数据")

                # 复制模板文件（agents.md, soul.md）
                for template_file in ["agents.md", "soul.md"]:
                    src = old_user_path / template_file
                    if src.exists():
                        shutil.copy2(src, new_path / template_file)
                        print(f"  - 已迁移 {template_file}")

                # 创建配置记录
                new_config = UserAgentConfig(
                    user_id=user.user_id,
                    local_working_dir=new_dir,
                    last_used_at=datetime.now()
                )
                db.add(new_config)
                db.commit()

                print(f"  - 已创建配置记录")
                migrated_count += 1

            except Exception as e:
                print(f"  - 迁移失败: {e}")
                db.rollback()
                skipped_count += 1

            print()

    finally:
        db.close()

    print("=" * 60)
    print("迁移完成")
    print(f"  成功迁移: {migrated_count} 个用户")
    print(f"  跳过: {skipped_count} 个用户")
    print("=" * 60)
    print()

    # 询问是否清理旧数据
    if migrated_count > 0:
        print("建议：在确认新系统正常工作后，可以手动删除旧数据：")
        print(f"  rm -rf {old_agent_db}")
        print()

    return True


def clean_old_data():
    """清理旧的 agent_db 数据（需要手动确认）"""
    print()
    print("=" * 60)
    print("清理旧数据")
    print("=" * 60)

    old_agent_db = project_root / "data" / "agent_db"

    if not old_agent_db.exists():
        print("[完成] 旧数据目录不存在")
        return

    print(f"旧数据目录: {old_agent_db}")
    print()
    print("警告：此操作不可恢复！")
    print()

    confirm = input("确定要删除旧数据吗？(y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    try:
        shutil.rmtree(old_agent_db)
        print(f"[完成] 已删除 {old_agent_db}")
    except Exception as e:
        print(f"[失败] 删除失败: {e}")


if __name__ == "__main__":
    migrate_agent_data()

    # 允许单独运行清理
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clean_old_data()
