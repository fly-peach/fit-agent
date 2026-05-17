"""
Training Results Storage

训练成果快照存储工具，提供：
- save_training_result_snapshot: 保存新快照
- get_training_result_snapshot: 获取单条快照
- list_training_result_snapshots: 查询快照列表
- update_training_result_snapshot: 更新快照
- delete_training_result_snapshot: 软删除快照
"""
from __future__ import annotations

import logging
from typing import Optional
from datetime import date

from sqlalchemy.orm import Session

from src.fitme.models.user_db import TrainingResultSnapshot
from src.fitme.utils.database import UserSessionLocal

logger = logging.getLogger(__name__)


def save_training_result_snapshot(
    user_id: int,
    card_html: str,
    title: str,
    session_id: Optional[str] = None,
    stats_json: Optional[str] = None,
    period_type: Optional[str] = None,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    thumbnail: Optional[str] = None,
) -> int:
    """保存训练成果快照。

    Args:
        user_id: 用户 ID
        card_html: Agent 生成的完整 HTML 卡片
        title: 快照标题
        session_id: 关联的 Agent 会话 ID
        stats_json: 统计数据 JSON（列表预览用）
        period_type: 周期类型："week" | "month" | "custom"
        period_start: 统计周期开始
        period_end: 统计周期结束
        thumbnail: 缩略图/封面图

    Returns:
        int: 新记录的 id
    """
    db: Session = UserSessionLocal()
    try:
        record = TrainingResultSnapshot(
            user_id=user_id,
            session_id=session_id,
            card_html=card_html,
            stats_json=stats_json,
            title=title,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            thumbnail=thumbnail,
            is_active=True,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id: int = record.id  # type: ignore[assignment]
        logger.info(
            "Training result snapshot saved: id=%s user=%s title=%s",
            record_id, user_id, title,
        )
        return record_id
    except Exception:
        db.rollback()
        logger.exception("Failed to save training result snapshot")
        raise
    finally:
        db.close()


def get_training_result_snapshot(snapshot_id: int) -> Optional[dict]:
    """按 ID 获取单条快照详情（含完整 card_html）

    Args:
        snapshot_id: 快照 ID

    Returns:
        dict or None: 快照字典
    """
    db: Session = UserSessionLocal()
    try:
        record = db.query(TrainingResultSnapshot).filter(
            TrainingResultSnapshot.id == snapshot_id,
            TrainingResultSnapshot.is_active == True
        ).first()
        return _record_to_dict(record, include_html=True) if record else None
    finally:
        db.close()


def list_training_result_snapshots(
    user_id: int,
    period_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    include_html: bool = False,
) -> list[dict]:
    """按 user_id 查询训练成果快照列表。

    Args:
        user_id: 用户 ID（必选）
        period_type: 周期类型筛选（可选）
        limit: 返回条数上限
        offset: 分页偏移
        include_html: 是否包含完整的 card_html（列表页建议 False 减少数据传输）

    Returns:
        list[dict]: 按 created_at 降序排列的快照列表
    """
    db: Session = UserSessionLocal()
    try:
        q = db.query(TrainingResultSnapshot).filter(
            TrainingResultSnapshot.user_id == user_id,
            TrainingResultSnapshot.is_active == True
        )
        if period_type:
            q = q.filter(TrainingResultSnapshot.period_type == period_type)
        records = (
            q.order_by(TrainingResultSnapshot.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_record_to_dict(r, include_html=include_html) for r in records]
    finally:
        db.close()


def update_training_result_snapshot(
    snapshot_id: int,
    title: Optional[str] = None,
    stats_json: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> bool:
    """更新快照信息。

    Args:
        snapshot_id: 快照 ID
        title: 新标题（可选）
        stats_json: 新统计 JSON（可选）
        thumbnail: 新缩略图（可选）

    Returns:
        bool: 是否更新成功
    """
    db: Session = UserSessionLocal()
    try:
        record = db.query(TrainingResultSnapshot).filter(
            TrainingResultSnapshot.id == snapshot_id,
            TrainingResultSnapshot.is_active == True
        ).first()
        if not record:
            return False
        if title is not None:
            record.title = title
        if stats_json is not None:
            record.stats_json = stats_json
        if thumbnail is not None:
            record.thumbnail = thumbnail
        db.commit()
        logger.info("Training result snapshot updated: id=%s", snapshot_id)
        return True
    except Exception:
        db.rollback()
        logger.exception("Failed to update training result snapshot")
        raise
    finally:
        db.close()


def delete_training_result_snapshot(snapshot_id: int) -> bool:
    """软删除快照（设置 is_active=False）。

    Args:
        snapshot_id: 快照 ID

    Returns:
        bool: 是否删除成功
    """
    db: Session = UserSessionLocal()
    try:
        record = db.query(TrainingResultSnapshot).filter(
            TrainingResultSnapshot.id == snapshot_id,
            TrainingResultSnapshot.is_active == True
        ).first()
        if not record:
            return False
        record.is_active = False
        db.commit()
        logger.info("Training result snapshot deleted (soft): id=%s", snapshot_id)
        return True
    except Exception:
        db.rollback()
        logger.exception("Failed to delete training result snapshot")
        raise
    finally:
        db.close()


def _record_to_dict(record: TrainingResultSnapshot, include_html: bool = False) -> dict:
    """将记录转为前端友好的字典。

    Args:
        record: 数据库记录
        include_html: 是否包含完整的 card_html

    Returns:
        dict: 字典
    """
    import datetime as _dt
    created = record.created_at
    updated = record.updated_at
    p_start = record.period_start
    p_end = record.period_end

    result = {
        "id": record.id,
        "user_id": record.user_id,
        "session_id": record.session_id,
        "title": record.title,
        "period_type": record.period_type,
        "period_start": p_start.isoformat() if isinstance(p_start, date) else None,
        "period_end": p_end.isoformat() if isinstance(p_end, date) else None,
        "thumbnail": record.thumbnail,
        "stats_json": record.stats_json,
        "is_active": record.is_active,
        "created_at": created.isoformat() if isinstance(created, _dt.datetime) else None,
        "updated_at": updated.isoformat() if isinstance(updated, _dt.datetime) else None,
    }
    if include_html:
        result["card_html"] = record.card_html
    return result
