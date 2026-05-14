"""
Harness Memory Models

数据库模型定义：
- PipelineExchange: Agent Pipeline 交互记录表
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.fitme.models.user_db import Base as UserDBBase


class PipelineExchange(UserDBBase):
    """Agent Pipeline 单次完整交互记录

    一次用户提问 → Pipeline 全流程（Master + SubAgents）→ 一行记录。
    前端可按 user_id / session_id 查询历史对话。
    """
    __tablename__ = "agent_pipeline_exchanges"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 会话标识 ──
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True,
                        comment="AgentScope session_id，复用前端传入的 session ID")

    # ── Phase 1: 用户输入 ──
    user_message = Column(Text, nullable=False, comment="用户原始输入")

    # ── Phase 1: Master Agent 首次分析 / 简单回答 ──
    master_phase1_output = Column(Text, default="", comment="Phase 1 Master 分析复杂度或直接回答")

    # ── Phase 2: 判断结果 ──
    need_fanout = Column(Boolean, default=False,
                         comment="是否触发了 SubAgent 专项分析（Fanout）")

    # ── Phase 3: SubAgent 输出 ──
    diet_analyst_output = Column(Text, default="", comment="SubAgent DietAnalyst 饮食分析")
    training_analyst_output = Column(Text, default="", comment="SubAgent TrainingAnalyst 训练分析")

    # ── Phase 4: Master Agent 汇总 ──
    master_phase4_output = Column(Text, default="", comment="Phase 4 Master 汇总结论")

    # ── 时间戳 ──
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ── 关联 ──
    user = relationship("User", backref="pipeline_exchanges")

    def to_dict(self) -> dict:
        """转为前端友好的字典"""
        import datetime as _dt
        created = self.created_at
        updated = self.updated_at
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "master_phase1_output": self.master_phase1_output,
            "need_fanout": self.need_fanout,
            "diet_analyst_output": self.diet_analyst_output,
            "training_analyst_output": self.training_analyst_output,
            "master_phase4_output": self.master_phase4_output,
            "created_at": created.isoformat() if isinstance(created, _dt.datetime) else None,
            "updated_at": updated.isoformat() if isinstance(updated, _dt.datetime) else None,
        }
