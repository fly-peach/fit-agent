"""从 ~/.fitagent 迁移到纯数据库模式

迁移内容：
1. agents.md 和 soul.md → UserPromptTemplate 数据库表
2. agent.json 中的 API Key 不迁移（安全原因，用户需重新设置）
"""
from pathlib import Path
from sqlalchemy.orm import Session

from src.fitme.utils.database import UserSessionLocal
from src.agents.harness.workspace.prompt_templates import (
    get_user_prompt_templates,
    update_user_prompt_templates,
)
from src.fitme.models.user_db import User, UserPromptTemplate
from src.fitme.utils.agent_directory import get_default_agent_directory


def migrate_user(user_id: int, db: Session):
    """迁移单个用户的提示词模板"""
    default_dir = Path(get_default_agent_directory())

    agents_md = ""
    soul_md = ""

    # 尝试从 ~/.fitagent 读取现有模板
    if (default_dir / "agents.md").exists():
        agents_md = (default_dir / "agents.md").read_text(encoding="utf-8")
    if (default_dir / "soul.md").exists():
        soul_md = (default_dir / "soul.md").read_text(encoding="utf-8")

    # 如果用户已有模板，不覆盖
    existing = get_user_prompt_templates(db, user_id)
    if existing:
        print(f"用户 {user_id} 已有模板，跳过")
        return

    if agents_md or soul_md:
        update_user_prompt_templates(db, user_id, agents_md=agents_md, soul_md=soul_md)
        print(f"用户 {user_id} 迁移成功")
    else:
        print(f"用户 {user_id} 无本地模板，跳过")


def migrate_all():
    """迁移所有用户"""
    db = UserSessionLocal()
    try:
        users = db.query(User).filter(User.deleted_at.is_(None)).all()
        print(f"找到 {len(users)} 个用户")

        for user in users:
            migrate_user(user.user_id, db)

        print("\n迁移完成！")
        print("注意：API Key 需要用户重新在前端设置")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_all()
