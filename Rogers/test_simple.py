#!/usr/bin/env python3
"""简单直接的测试脚本，绕过 AgentScope Runtime，直接调用我们的 pipeline"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from agentscope.message import Msg

from src.agents.agents_pipeline import run_rogers_pipeline
from src.fitme.utils.database import async_user_engine


async def test():
    print("===== 测试 pipeline 直接调用 =====")

    # 模拟用户消息
    msgs = [
        Msg(
            name="User",
            role="user",
            content="你好，请用 record_user_fact 记录: category=personality, key=test_personality, value=测试数据"
        )
    ]

    yield_count = 0
    try:
        async for output in run_rogers_pipeline(
            msgs,
            user_id=1,
            session_id="test-session-123",
            db_engine=async_user_engine,
            auth_token=None,
            auto_approve_enabled=True,  # 自动批准，不用审批
        ):
            yield_count += 1
            print(f"Yield #{yield_count}: {output}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n===== 测试完成，共 yield {yield_count} 次 =====")


if __name__ == "__main__":
    asyncio.run(test())
