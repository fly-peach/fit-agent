"""Rogers Agent - Pipeline 多智能体编排

基于 AgentScope 的多智能体管道工作流：
- Vision Agent: 图片→文字描述（仅当消息有图片时触发）
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
from agentscope.tool import Toolkit
from agentscope.memory import InMemoryMemory

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "你是 Rogers，一个专业的健身和健康管理助手。"
    "你帮助用户制定训练计划、记录饮食、跟踪健康指标。"
    "用中文回答。"
)

SKILL_BINDINGS = {
    "diet": [],
    "training": [],
    "health": [],
    "user": [],
    "all": [],
}

SUB_AGENT_SYS_PROMPTS = {
    "diet": (
        "你是饮食分析助手。分析用户的饮食相关问题。"
        "先思考（思考过程要详细），然后输出分析结果。"
        "用中文回答。"
    ),
    "training": (
        "你是训练分析助手。分析用户的训练相关问题。"
        "先思考（思考过程要详细），然后输出分析结果。"
        "用中文回答。"
    ),
}

MASTER_SYS_PROMPT_ADDON = """

    ## 管道工作流规则

    你负责决定是否需要调用饮食/训练分析子Agent进行深度分析。

    判断流程：
    1. 理解用户的问题
    2. 基于问题判断：
       - **simple**: 用户只是在聊天/问简单问题→直接回答
       - **complex**: 用户要求分析/评估/制定计划/综合建议→需要子Agent分析

    如果需要深度分析，你必须输出 JSON 标记：
    ```pipeline
    {"action":"fanout","needs":["diet","training"]}
    ```
    然后停止输出，等待子Agent分析结果后再继续。

    如果不需要深度分析，直接回复用户即可，不要输出 pipeline 标记。
    """

# =============================================================================
# 工具函数
# =============================================================================


def _parse_pipeline_marker(text: str) -> dict[str, Any] | None:
    """解析 MasterAgent 输出中的 pipeline JSON 标记。"""
    m = re.search(r"```pipeline\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    return None


def _has_image(msg: Msg) -> bool:
    """检查消息是否包含图片。"""
    content = getattr(msg, "content", None)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "image":
                return True
    return False


def _make_toolkit() -> Toolkit:
    """创建工具包。"""
    return Toolkit()


def _make_formatter():
    """创建消息格式化器。"""
    return DashScopeChatFormatter()


# =============================================================================
# PipelineController - 多智能体管道工作流编排
# =============================================================================


class PipelineController:
    """多智能体管道工作流编排器。

    使用方式:
        controller = PipelineController(pipeline_cfg, api_key)
        async for msg, last in controller.run(msgs):
            yield msg, last
    """

    def __init__(
        self,
        api_key: str,
        vision_model: str = "qwen-vl-max",
        reasoning_model: str = "qwen-max",
        fanout_enabled: bool = True,
    ):
        self.api_key = api_key
        self.vision_model_name = vision_model
        self.reasoning_model_name = reasoning_model
        self.fanout_enabled = fanout_enabled
        self.master_agent: ReActAgent | None = None
        self.diet_agent: ReActAgent | None = None
        self.training_agent: ReActAgent | None = None

    # ---------------------------------------------------------------------------
    # 模型创建
    # ---------------------------------------------------------------------------

    def _make_vision_model(self) -> DashScopeChatModel:
        return DashScopeChatModel(
            model_name=self.vision_model_name,
            api_key=self.api_key,
            stream=False,
        )

    def _make_reasoning_model(self, stream: bool = True) -> DashScopeChatModel:
        """创建推理模型。"""
        return DashScopeChatModel(
            model_name=self.reasoning_model_name,
            api_key=self.api_key,
            stream=stream,
            enable_thinking=True,
        )

    # ---------------------------------------------------------------------------
    # SubAgent 创建
    # ---------------------------------------------------------------------------

    def _make_sub_agent(
        self,
        name: str,
        sys_prompt: str,
    ) -> ReActAgent:
        """创建一个带有特定技能集的 SubAgent（始终使用流式模型）。"""
        model = self._make_reasoning_model(stream=True)

        agent = ReActAgent(
            name=name,
            model=model,
            sys_prompt=sys_prompt,
            toolkit=_make_toolkit(),
            memory=InMemoryMemory(),
            formatter=_make_formatter(),
        )
        agent.set_console_output_enabled(False)
        return agent

    def _get_or_create_master_agent(
        self,
        base_sys_prompt: str,
    ) -> ReActAgent:
        """获取或创建主子Agent（懒初始化）。"""
        if self.master_agent is None:
            full_prompt = base_sys_prompt + MASTER_SYS_PROMPT_ADDON
            self.master_agent = self._make_sub_agent(
                name="Rogers",
                sys_prompt=full_prompt,
            )
        return self.master_agent

    def _get_or_create_diet_agent(self) -> ReActAgent:
        if self.diet_agent is None:
            self.diet_agent = self._make_sub_agent(
                name="DietAnalyst",
                sys_prompt=SUB_AGENT_SYS_PROMPTS["diet"],
            )
        return self.diet_agent

    def _get_or_create_training_agent(self) -> ReActAgent:
        if self.training_agent is None:
            self.training_agent = self._make_sub_agent(
                name="TrainingAnalyst",
                sys_prompt=SUB_AGENT_SYS_PROMPTS["training"],
            )
        return self.training_agent

    # ---------------------------------------------------------------------------
    # Step 1: 视觉分析
    # ---------------------------------------------------------------------------

    async def _vision_step(self, msgs) -> Msg | None:
        """使用视觉模型分析图片，返回描述文本。"""
        has_img = False
        if isinstance(msgs, list):
            has_img = any(_has_image(m) for m in msgs if isinstance(m, Msg))
        elif isinstance(msgs, Msg):
            has_img = _has_image(msgs)

        if not has_img:
            return None

        vision_model = self._make_vision_model()

        vision_agent = ReActAgent(
            name="VisionAnalyzer",
            model=vision_model,
            sys_prompt=(
                "你是专业的视觉分析助手。请分析用户上传的图片内容。"
                "如果是食物照片，描述食物种类、份量和营养价值；"
                "如果是身体数据截图，提取关键数字和指标；"
                "如果是训练动作截图，描述动作要点和规范性。"
                "用中文清晰描述，不要评价，只提供客观分析。"
            ),
            toolkit=_make_toolkit(),
            formatter=_make_formatter(),
            memory=InMemoryMemory(),
        )
        vision_agent.set_console_output_enabled(False)

        result = await vision_agent(msgs)
        desc = result.get_text_content() if hasattr(result, "get_text_content") else str(result)
        logger.info("Vision analysis: %s", desc[:200])
        return Msg(name="VisionAnalyzer", content=desc, role="assistant")

    # ---------------------------------------------------------------------------
    # Step 2: 主子Agent (流式检测标记)
    # ---------------------------------------------------------------------------

    async def _master_step_streaming(
        self,
        input_msgs,
        base_sys_prompt: str,
    ) -> AsyncGenerator[tuple[Msg, bool], None]:
        """运行主子Agent（流式），边输出边检测 pipeline 标记。

        如果检测到 pipeline 标记，将标记存入 self._pending_marker，
        后续由 run() 判断是否需要 fanout。

        Yields:
            (Msg, bool) - 与 stream_printing_messages 一致的流式消息
        """
        agent = self._get_or_create_master_agent(base_sys_prompt)
        agent.set_console_output_enabled(False)
        agent.model.stream = True

        self._pending_marker: dict | None = None
        buffer = ""

        async for msg, last in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(input_msgs),
        ):
            chunk = msg.get_text_content() if hasattr(msg, "get_text_content") else str(msg)
            buffer += chunk

            # 检测 pipeline 标记
            if self._pending_marker is None:
                parsed = _parse_pipeline_marker(buffer)
                if parsed is not None:
                    self._pending_marker = parsed
                    # 找到标记结束位置，截取标记前内容作为最后的 Msg
                    m = re.search(r"```pipeline\s*\{.*?\}\s*```", buffer, re.DOTALL)
                    if m:
                        before_marker = buffer[:m.start()].strip()
                        if before_marker:
                            yield Msg(name="Rogers", content=before_marker, role="assistant"), True
                    return  # 停止输出

            yield msg, last

    async def _fanout_step_streaming(
        self,
        user_msg_text: str,
        marker: dict,
    ) -> AsyncGenerator[tuple[Msg, bool, str], None]:
        """流式 Fanout：逐个运行子Agent并流式输出思考过程。

        Yields:
            (msg, last, sub_type) - 每个子Agent的流式消息及其类型
        """
        needs = marker.get("needs", ["diet", "training"])

        analysis_msg = Msg(
            name="user",
            content=(
                f"用户原始问题：{user_msg_text}\n\n"
                "请按照以下流程操作：\n"
                "1. 理解用户的问题\n"
                "2. 思考（思考过程要详细）\n"
                "3. 输出：给出专业的分析\n\n"
            ),
            role="user",
        )

        for sub_type in ["diet", "training"]:
            if sub_type not in needs:
                continue

            if sub_type == "diet":
                agent = self._get_or_create_diet_agent()
            else:
                agent = self._get_or_create_training_agent()

            agent.set_console_output_enabled(False)

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(analysis_msg),
            ):
                msg.name = "DietAnalyst" if sub_type == "diet" else "TrainingAnalyst"
                yield msg, last, sub_type

    # ---------------------------------------------------------------------------
    # 主流程
    # ---------------------------------------------------------------------------

    async def run(
        self,
        msgs,
        base_sys_prompt: str | None = None,
    ):
        """运行完整的管道工作流。

        Yields:
            (Msg, bool) - 流式输出消息和完成标志
        """
        user_msg_text = ""
        if isinstance(msgs, list) and msgs:
            last_msg = msgs[-1]
            if isinstance(last_msg, Msg):
                user_msg_text = last_msg.get_text_content() if hasattr(last_msg, "get_text_content") else str(last_msg)
        elif isinstance(msgs, Msg):
            user_msg_text = msgs.get_text_content() if hasattr(msgs, "get_text_content") else str(msgs)

        if base_sys_prompt is None:
            base_sys_prompt = DEFAULT_SYSTEM_PROMPT

        # =============================================================
        # Step 1: 视觉分析（仅当消息有图片时触发）
        # =============================================================
        vision_desc = await self._vision_step(msgs)
        if vision_desc is not None:
            yield Msg(
                name="VisionAnalyzer",
                content=f"👁️ **图片识别结果**\n\n{vision_desc.content}",
                role="assistant",
            ), False
            if isinstance(msgs, list):
                msgs = list(msgs) + [vision_desc]
            elif isinstance(msgs, Msg):
                msgs = [msgs, vision_desc]

        # =============================================================
        # Step 2: MasterAgent 流式分析判断
        # =============================================================
        yield Msg(name="Rogers", content="🤔 正在分析你的问题...", role="assistant"), False

        # 确保 _pending_marker 初始为 None
        self._pending_marker = None

        async for msg, last in self._master_step_streaming(
            msgs,
            base_sys_prompt,
        ):
            # 检测到 pipeline 标记 -> _master_step_streaming 已自行 return
            yield msg, last
            if last:
                break

        # 如果 _master_step_streaming 检测到了 pipeline 标记
        if self._pending_marker is not None and self.fanout_enabled:
            yield Msg(
                name="system",
                content="--- 📋 开始调用专业子Agent进行深度分析 ---",
                role="assistant",
            ), False
        else:
            # 简单场景->已流式输出完毕
            return

        # =============================================================
        # Step 3: 流式 Fanout - 饮食/训练 子Agent 逐个流式输出
        # =============================================================
        fanout_final: dict[str, Msg] = {}
        async for msg, last, sub_type in self._fanout_step_streaming(
            user_msg_text,
            self._pending_marker,
        ):
            fanout_final[sub_type] = msg
            yield msg, last

        # =============================================================
        # Step 4: MasterAgent 汇总 - 流式输出综合回复
        # =============================================================
        summary_parts = []
        for sub_type in ["diet", "training"]:
            if sub_type in fanout_final:
                m = fanout_final[sub_type]
                text = m.get_text_content() if hasattr(m, "get_text_content") else str(m)
                summary_parts.append(f"## {'饮食分析' if sub_type == 'diet' else '训练分析'}\n{text}")

        if summary_parts:
            yield Msg(
                name="system",
                content="--- 🔄 Rogers 正在综合子Agent的分析结果... ---",
                role="assistant",
            ), False

            summary_msg = Msg(
                name="user",
                content=(
                    "以下是子Agent的分析结果，请基于这些结果和之前的对话，"
                    "给用户一个完整、温暖的综合回复：\n\n"
                    + "\n\n".join(summary_parts)
                ),
                role="user",
            )
            agent = self._get_or_create_master_agent(base_sys_prompt)
            agent.set_console_output_enabled(False)

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(summary_msg),
            ):
                msg.name = "Rogers"
                yield msg, last

