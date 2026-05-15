"""User Memory Profile — SecondMe 用户画像持久化

EAV 灵活模式存储用户全方位画像数据：饮食偏好、运动偏好、健身目标、
已达成成就、性格特质等。支持压缩时自动提取 + Agent 工具显式写入。

表位置: fituser.db (与 users/health_metrics 等同库)
ORM 基类: UserDBBase (来自 src.fitme.models.user_db)
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.sql import func

from src.fitme.models.user_db import Base as UserDBBase
from src.fitme.utils.database import UserDBContext


class UserMemoryProfile(UserDBBase):
    """用户记忆画像表 (EAV 模式)

    每个用户可以有任意多条记录，通过 (user_id, key) 唯一约束实现 upsert。
    """

    __tablename__ = "user_memory_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)

    category = Column(String(50), nullable=False, comment="food / exercise / health / goal / achievement / personality / note")
    key = Column(String(100), nullable=False, comment="属性名，如 favorite_foods")
    value = Column(Text, nullable=False, comment="属性值，可存储 JSON 复杂数据")

    confidence = Column(Float, default=1.0, comment="0.0~1.0，Agent 对此条数据的置信度")
    source = Column(String(20), default="explicit", comment="explicit(用户明说) / inferred(行为推断) / extracted(压缩提取)")
    is_active = Column(Boolean, default=True, comment="软删除标记")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


def upsert_user_fact(
    user_id: int,
    category: str,
    key: str,
    value: str,
    confidence: float = 1.0,
    source: str = "explicit",
) -> int:
    """插入或更新一条用户画像事实。

    Args:
        user_id: 用户 ID
        category: 分类 (food/exercise/health/goal/achievement/personality/note)
        key: 属性名
        value: 属性值
        confidence: 置信度 0.0~1.0
        source: 数据来源 (explicit/inferred/extracted)

    Returns:
        记录的 id
    """
    with UserDBContext() as db:
        existing = db.query(UserMemoryProfile).filter(
            UserMemoryProfile.user_id == user_id,
            UserMemoryProfile.key == key,
        ).first()

        if existing:
            existing.category = category
            existing.value = value
            existing.confidence = confidence
            existing.source = source
            existing.is_active = True
            db.commit()
            return existing.id
        else:
            fact = UserMemoryProfile(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
            )
            db.add(fact)
            db.commit()
            db.refresh(fact)
            return fact.id


def delete_user_fact(user_id: int, key: str) -> bool:
    """软删除一条用户画像事实（设为 inactive）。

    Args:
        user_id: 用户 ID
        key: 属性名

    Returns:
        是否成功删除
    """
    with UserDBContext() as db:
        fact = db.query(UserMemoryProfile).filter(
            UserMemoryProfile.user_id == user_id,
            UserMemoryProfile.key == key,
        ).first()
        if fact:
            fact.is_active = False
            db.commit()
            return True
        return False


def get_user_facts(
    user_id: int,
    category: Optional[str] = None,
) -> list[dict]:
    """获取用户的所有活跃画像事实。

    Args:
        user_id: 用户 ID
        category: 可选，按分类过滤

    Returns:
        事实字典列表
    """
    with UserDBContext() as db:
        q = db.query(UserMemoryProfile).filter(
            UserMemoryProfile.user_id == user_id,
            UserMemoryProfile.is_active == True,
        )
        if category:
            q = q.filter(UserMemoryProfile.category == category)
        facts = q.order_by(UserMemoryProfile.category, UserMemoryProfile.key).all()
        return [
            {
                "id": f.id,
                "category": f.category,
                "key": f.key,
                "value": f.value,
                "confidence": float(f.confidence) if f.confidence else 1.0,
                "source": f.source,
            }
            for f in facts
        ]


def get_user_facts_by_category(
    user_id: int,
    categories: list[str],
) -> dict[str, list[dict]]:
    """按分类批量获取用户画像事实。

    Args:
        user_id: 用户 ID
        categories: 分类列表

    Returns:
        {category: [fact_dict, ...], ...}
    """
    result: dict[str, list[dict]] = {c: [] for c in categories}
    facts = get_user_facts(user_id)
    for fact in facts:
        cat = fact["category"]
        if cat in result:
            result[cat].append(fact)
    return result
