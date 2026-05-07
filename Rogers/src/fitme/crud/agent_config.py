"""CRUD operations for Agent configuration"""
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.user_db import UserAgentConfig


def get_user_agent_config(db: Session, user_id: int) -> UserAgentConfig | None:
    """获取用户的 Agent 配置"""
    return db.query(UserAgentConfig).filter(UserAgentConfig.user_id == user_id).first()


def create_user_agent_config(
    db: Session, user_id: int, local_working_dir: str
) -> UserAgentConfig:
    """创建用户 Agent 配置"""
    db_config = UserAgentConfig(
        user_id=user_id,
        local_working_dir=local_working_dir,
        last_used_at=datetime.now()
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_user_agent_config(
    db: Session, user_id: int, local_working_dir: str
) -> UserAgentConfig:
    """更新用户 Agent 配置"""
    config = get_user_agent_config(db, user_id)
    if config:
        config.local_working_dir = local_working_dir
        config.last_used_at = datetime.now()
        db.commit()
        db.refresh(config)
    else:
        config = create_user_agent_config(db, user_id, local_working_dir)
    return config


def delete_user_agent_config(db: Session, user_id: int) -> bool:
    """删除用户 Agent 配置"""
    config = get_user_agent_config(db, user_id)
    if config:
        db.delete(config)
        db.commit()
        return True
    return False


def update_last_used(db: Session, user_id: int) -> UserAgentConfig | None:
    """更新最后使用时间"""
    config = get_user_agent_config(db, user_id)
    if config:
        config.last_used_at = datetime.now()
        db.commit()
        db.refresh(config)
    return config


def get_all_agent_configs(db: Session) -> list[UserAgentConfig]:
    """获取所有用户的 Agent 配置。"""
    return db.query(UserAgentConfig).all()
