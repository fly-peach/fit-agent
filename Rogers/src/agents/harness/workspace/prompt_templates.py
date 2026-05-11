from sqlalchemy.orm import Session
from src.fitme.models.user_db import UserPromptTemplate
from src.agents.harness.templates.templates import get_template_path
from pathlib import Path


def get_user_prompt_templates(db: Session, user_id: int) -> UserPromptTemplate | None:
    """获取用户提示词模板"""
    return db.query(UserPromptTemplate).filter(UserPromptTemplate.user_id == user_id).first()


def init_user_prompt_templates(db: Session, user_id: int) -> UserPromptTemplate:
    """初始化用户提示词模板（从模板文件复制）"""
    template_dir = get_template_path()
    agents_md = ""
    soul_md = ""

    agents_path = template_dir / "agents.md"
    soul_path = template_dir / "soul.md"

    if agents_path.exists():
        agents_md = agents_path.read_text(encoding="utf-8")
    if soul_path.exists():
        soul_md = soul_path.read_text(encoding="utf-8")

    template = UserPromptTemplate(
        user_id=user_id,
        agents_md=agents_md,
        soul_md=soul_md
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_user_prompt_templates(
    db: Session,
    user_id: int,
    agents_md: str | None = None,
    soul_md: str | None = None
) -> UserPromptTemplate | None:
    """更新用户提示词模板"""
    template = get_user_prompt_templates(db, user_id)
    if not template:
        template = init_user_prompt_templates(db, user_id)

    if agents_md is not None:
        template.agents_md = agents_md
    if soul_md is not None:
        template.soul_md = soul_md

    db.commit()
    db.refresh(template)
    return template


def get_or_create_prompt_templates(db: Session, user_id: int) -> UserPromptTemplate:
    """获取或创建用户提示词模板"""
    template = get_user_prompt_templates(db, user_id)
    if not template:
        template = init_user_prompt_templates(db, user_id)
    return template
