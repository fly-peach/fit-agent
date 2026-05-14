"""
Harness Memory Storage

Pipeline 交互记录存储工具，提供：
- save_pipeline_exchange: 保存记录
- get_pipeline_exchange: 获取单条记录
- list_pipeline_exchanges: 查询历史记录
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from .models import PipelineExchange
from src.fitme.utils.database import UserSessionLocal

logger = logging.getLogger(__name__)


def save_pipeline_exchange(
    user_id: int,
    session_id: str,
    user_message: str,
    master_phase1_output: str = "",
    need_fanout: bool = False,
    diet_analyst_output: str = "",
    training_analyst_output: str = "",
    master_phase4_output: str = "",
) -> int:
    """保存一次完整的 Pipeline 交互记录。

    Args:
        user_id: 用户 ID
        session_id: 会话 ID
        user_message: 用户原始输入
        master_phase1_output: Phase 1 Master 输出
        need_fanout: 是否触发了 SubAgent
        diet_analyst_output: SubAgent DietAnalyst 输出
        training_analyst_output: SubAgent TrainingAnalyst 输出
        master_phase4_output: Phase 4 Master 汇总输出

    Returns:
        int: 新记录的 id
    """
    db: Session = UserSessionLocal()
    try:
        record = PipelineExchange(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            master_phase1_output=master_phase1_output,
            need_fanout=need_fanout,
            diet_analyst_output=diet_analyst_output,
            training_analyst_output=training_analyst_output,
            master_phase4_output=master_phase4_output,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id: int = record.id  # type: ignore[assignment]
        logger.info(
            "Pipeline exchange saved: id=%s user=%s session=%s fanout=%s",
            record_id, user_id, session_id, need_fanout,
        )
        return record_id
    except Exception:
        db.rollback()
        logger.exception("Failed to save pipeline exchange")
        raise
    finally:
        db.close()


def get_pipeline_exchange(exchange_id: int) -> Optional[dict]:
    """按 ID 获取单条记录

    Args:
        exchange_id: 记录 ID

    Returns:
        dict or None: 记录字典
    """
    db: Session = UserSessionLocal()
    try:
        record = db.query(PipelineExchange).filter(PipelineExchange.id == exchange_id).first()
        return record.to_dict() if record else None
    finally:
        db.close()


def list_pipeline_exchanges(
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """按 user_id（必选）和可选的 session_id 查询历史记录。

    Args:
        user_id: 用户 ID（必选）
        session_id: 会话 ID（可选，不传则返回该用户所有会话记录）
        limit: 返回条数上限
        offset: 分页偏移

    Returns:
        list[dict]: 按 created_at 降序排列的交互记录
    """
    db: Session = UserSessionLocal()
    try:
        q = db.query(PipelineExchange).filter(PipelineExchange.user_id == user_id)
        if session_id:
            q = q.filter(PipelineExchange.session_id == session_id)
        records = (
            q.order_by(PipelineExchange.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in records]
    finally:
        db.close()
