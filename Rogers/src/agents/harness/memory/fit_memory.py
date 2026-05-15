"""FitAsyncSQLAlchemyMemory - 会话内短期记忆，共用 fituser.db

继承 AsyncSQLAlchemyMemory，将内部 4 张表重命名（加 agent_ 前缀），
避免与 fituser.db 中的应用层 users 表冲突。

使用独立 declarative base 定义 ORM 类，在子类用同名类属性覆盖父类
的 SessionTable / MessageTable / MessageMarkTable / UserTable，
使父类 get_memory() 等方法的 self.SessionTable 指向我们的 agent_* 表。
"""
import json
import re
from typing import Any

from sqlalchemy import Column, String, JSON, BigInteger, ForeignKey, select, Text
from sqlalchemy import text
from sqlalchemy.orm import relationship, declarative_base

from agentscope.memory._working_memory._sqlalchemy_memory import (
    AsyncSQLAlchemyMemory,
    Base as AgentMemoryBase,
)

# ── 独立 base（避免与 AgentScope 的 SessionTable 等类名冲突） ──────────────

FitMemBase = declarative_base()


class _AgentMessage(FitMemBase):
    __tablename__ = "agent_message"

    id = Column(String(255), primary_key=True)
    msg = Column(JSON, nullable=False)
    session_id = Column(
        String(255),
        ForeignKey("agent_session.id"),
        nullable=False,
    )
    index = Column(BigInteger, nullable=False, index=True)
    session = relationship("_AgentSession", back_populates="messages")


class _AgentMessageMark(FitMemBase):
    __tablename__ = "agent_message_mark"

    msg_id = Column(
        String(255),
        ForeignKey("agent_message.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mark = Column(String(255), primary_key=True)


class _AgentSession(FitMemBase):
    __tablename__ = "agent_session"

    id = Column(String(255), primary_key=True)
    user_id = Column(
        String(255),
        ForeignKey("agent_users.id"),
        nullable=False,
    )
    compressed_summary = Column(Text, default=None)
    messages = relationship("_AgentMessage", back_populates="session")
    user = relationship("_AgentUser", back_populates="sessions")


class _AgentUser(FitMemBase):
    __tablename__ = "agent_users"

    id = Column(String(255), primary_key=True)
    sessions = relationship("_AgentSession", back_populates="user")


class FitAsyncSQLAlchemyMemory(AsyncSQLAlchemyMemory):
    """AsyncSQLAlchemyMemory 的子类，表名加 `agent_` 前缀。

    通过同名类属性覆盖父类的 table 类引用，使父类 get_memory()、
    add()、delete() 等方法都能正确使用我们的 agent_* 表。
    """

    MessageTable = _AgentMessage
    MessageMarkTable = _AgentMessageMark
    SessionTable = _AgentSession
    UserTable = _AgentUser

    async def _create_table(self) -> None:
        if self._initialized:
            return

        engine = self.session.bind

        async with engine.begin() as conn:
            agent_tables = [
                FitMemBase.metadata.tables[name]
                for name in (
                    "agent_users",
                    "agent_session",
                    "agent_message",
                    "agent_message_mark",
                )
            ]
            await conn.run_sync(
                lambda c: FitMemBase.metadata.create_all(c, tables=agent_tables),
            )

            result = await conn.execute(
                text("PRAGMA table_info(agent_session)")
            )
            columns = [row[1] for row in result.fetchall()]
            if "compressed_summary" not in columns:
                await conn.execute(
                    text("ALTER TABLE agent_session ADD COLUMN compressed_summary TEXT")
                )

            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='user_memory_profile'")
            )
            if not result.fetchone():
                await conn.execute(text("""
                    CREATE TABLE user_memory_profile (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        key VARCHAR(100) NOT NULL,
                        value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source VARCHAR(20) DEFAULT 'explicit',
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_ump_user_category ON user_memory_profile(user_id, category)"
                ))
                await conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uk_ump_user_key ON user_memory_profile(user_id, key)"
                ))

        needs_commit = False

        result = await self.session.execute(
            select(self.UserTable).filter(self.UserTable.id == self.user_id),
        )
        user_record = result.scalar_one_or_none()

        if user_record is None:
            user_record = self.UserTable(id=self.user_id)
            self.session.add(user_record)
            needs_commit = True

        result = await self.session.execute(
            select(self.SessionTable).filter(
                self.SessionTable.id == self.session_id,
            ),
        )
        session_record = result.scalar_one_or_none()

        if session_record is None:
            session_record = self.SessionTable(
                id=self.session_id,
                user_id=self.user_id,
            )
            self.session.add(session_record)
            needs_commit = True

        if needs_commit:
            await self.session.commit()

        self._initialized = True

    async def update_compressed_summary(self, summary: str) -> None:
        clean_summary = summary
        m = re.search(r"__USER_FACTS__(.*?)__END_USER_FACTS__", summary, re.DOTALL)
        if m:
            try:
                facts = json.loads(m.group(1))
                if facts:
                    await self.update_user_facts(facts)
                    logger = __import__("logging").getLogger(__name__)
                    logger.info("Extracted %d user facts from compression summary", len(facts))
            except (json.JSONDecodeError, Exception):
                pass
            clean_summary = summary[:m.start()] + summary[m.end():]

        self._compressed_summary = clean_summary
        from sqlalchemy import update as sa_update
        stmt = (
            sa_update(self.SessionTable)
            .where(self.SessionTable.id == self.session_id)
            .values(compressed_summary=clean_summary)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_user_facts(self, facts: list[dict]) -> None:
        try:
            uid = int(self.user_id)
        except (ValueError, TypeError):
            return

        for fact in facts:
            category = fact["category"]
            key = fact["key"]
            value = fact["value"]
            confidence = fact.get("confidence", 1.0)
            source = fact.get("source", "extracted")

            await self.session.execute(
                text("""
                    INSERT INTO user_memory_profile
                    (user_id, category, key, value, confidence, source, is_active, created_at, updated_at)
                    VALUES (:user_id, :category, :key, :value, :confidence, :source, 1, datetime('now'), datetime('now'))
                    ON CONFLICT(user_id, key) DO UPDATE SET
                        value = excluded.value,
                        confidence = excluded.confidence,
                        source = excluded.source,
                        is_active = 1,
                        updated_at = datetime('now')
                """),
                {
                    "user_id": uid,
                    "category": category,
                    "key": key,
                    "value": value,
                    "confidence": confidence,
                    "source": source,
                },
            )
        await self.session.commit()

    async def get_memory(self, mark=None, exclude_mark=None,
                         prepend_summary=True, **kwargs):
        await self._create_table()
        if prepend_summary and not self._compressed_summary:
            from sqlalchemy import select as sa_select
            result = await self.session.execute(
                sa_select(self.SessionTable.compressed_summary)
                .where(self.SessionTable.id == self.session_id)
            )
            row = result.scalar_one_or_none()
            if row:
                self._compressed_summary = row
        return await super().get_memory(
            mark=mark, exclude_mark=exclude_mark,
            prepend_summary=prepend_summary, **kwargs,
        )
