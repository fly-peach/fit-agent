"""Rogers Agent - Pipeline 多智能体编排

基于 AgentScope 的多智能体管道工作流：
- Master Agent: 判断复杂度→输出思考过程→简单回答 or 触发 Fanout
- Fanout: DietAnalyst + TrainingAnalyst 流式分析
- Master Agent: 汇总→流式输出最终回复
"""
from __future__ import annotations

import json
import logging
import re
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, AsyncGenerator

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from harness.tools.tools_for_agent import Toolkit,register_tools
from agentscope.memory import InMemoryMemory



DEFAULT_SYSTEM_PROMPT = (
    "你是 Rogers，一个专业的健身和健康管理助手。"
    "你帮助用户制定训练计划、记录饮食、跟踪健康指标。"
    "用中文回答。"
)



class FitAgent(ReActAgent):
    def __init__(
        self,
        name: str,
        toolkit: Toolkit,
        sys_prompt: str = DEFAULT_SYSTEM_PROMPT,
        model=None,
        memory=None,
        formatter=None,
    ):
        if model is None:
            model = DashScopeChatModel(
                "qwen-turbo",
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                stream=True,
            )
        if memory is None:
            memory = InMemoryMemory()
        if formatter is None:
            formatter = DashScopeChatFormatter()

        super().__init__(
            name=name,
            model=model,
            sys_prompt=sys_prompt,
            toolkit=toolkit,
            memory=memory,
            formatter=formatter,
        )

# 使用时只需提供 name 和 toolkit
rogers_agent = FitAgent(
    name="Friday",
)
