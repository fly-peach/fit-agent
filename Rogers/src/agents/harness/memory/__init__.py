"""
Harness Memory Module

整合后的 Memory 相关功能：
- models: 数据库模型定义
- storage: Pipeline 交互记录存储
- user_profile: 用户记忆画像 (SecondMe)

注意：SqliteSession 已移动到 src.agents.harness.session
"""
from .models import PipelineExchange
from .storage import (
    save_pipeline_exchange,
    get_pipeline_exchange,
    list_pipeline_exchanges,
)
from .user_profile import (
    UserMemoryProfile,
    upsert_user_fact,
    delete_user_fact,
    get_user_facts,
    get_user_facts_by_category,
)
# 向后兼容：从 session 模块导入
from src.agents.harness.session import SqliteSession

__all__ = [
    "PipelineExchange",
    "save_pipeline_exchange",
    "get_pipeline_exchange",
    "list_pipeline_exchanges",
    "UserMemoryProfile",
    "upsert_user_fact",
    "delete_user_fact",
    "get_user_facts",
    "get_user_facts_by_category",
    "SqliteSession",
]
