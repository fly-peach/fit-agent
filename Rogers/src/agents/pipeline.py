"""Pipeline Controller — 多智能体管道工作流编排

工作流：
  1. VisionAgent: 图片 → 文字描述（仅当消息含图片）
  2. MasterAgent: 判断复杂度 → 简单回复 or 触发 Fanout
  3. Fanout: 饮食 SubAgent + 训练 SubAgent 并行分析
  4. MasterAgent: 汇总 SubAgent 结果 → 最终回复
"""
from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from typing import Any

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import fanout_pipeline, stream_printing_messages

from .harness.skills.skill_manager import SkillManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SubAgent 创建工具
# ---------------------------------------------------------------------------

SKILL_BINDINGS = {
    "diet": ["fitme-diet"],
    "training": ["fitme-training", "fitme-exercise"],
    "health": ["fitme-health"],
    "user": ["fitme-user"],
    "all": ["fitme-diet", "fitme-training", "fitme-exercise", "fitme-health", "fitme-user"],
}

SUB_AGENT_SYS_PROMPTS = {
    "diet": (
        "你是饮食分析助手。只能使用 fitme-diet 技能来分析用户的饮食记录。"
        "用中文输出简洁的营养分析报告，包含：总热量、三大营养素、饮食建议。"
        "如果用户没有查询具体日期，分析最近三天的饮食趋势。"
    ),
    "training": (
        "你是训练分析助手。只能使用 fitme-training 和 fitme-exercise 技能来分析用户的训练数据。"
        "用中文输出简洁的训练分析报告，包含：训练频率、强度、动作推荐和进度评估。"
        "如果用户没有指定具体日期，分析最近一周的训练情况。"
    ),
}

MASTER_SYS_PROMPT_ADDON = """

## 管道工作流规则

你负责决定是否需要调用饮食/训练分析子Agent进行深度分析。

判断流程：
1. 调用 fitme-diet、fitme-training 技能查询用户近期的饮食和训练数据
2. 基于数据判断：
   - **simple**: 用户只是在聊天/问简单问题/查看单条数据 → 直接回答
   - **complex**: 用户要求分析/评估/制定计划/综合建议 → 需要子Agent分析

如果需要深度分析，你必须输出 JSON 标记：
```pipeline
{"action":"fanout","needs":["diet","training"]}
```
然后停止输出，等待子Agent分析结果后再继续。

如果不需要深度分析，直接回复用户即可，不要输出 pipeline 标记。
"""


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


# ---------------------------------------------------------------------------
# PipelineController
# ---------------------------------------------------------------------------


class PipelineController:
    """多智能体管道工作流编排器。

    使用方式:
        ctrl = PipelineController(pipeline_cfg, skill_manager, api_key)
        async for msg, last in ctrl.run(msgs):
            yield msg, last
    """

    def __init__(
        self,
        pipeline_cfg: "PipelineConfig",
        skill_manager: SkillManager,
        api_key: str,
        working_dir: str,
    ):
        from .config import PipelineConfig
        self.cfg = pipeline_cfg
        self.skill_manager = skill_manager
        self.api_key = api_key
        self.working_dir = working_dir
        self.master_agent: ReActAgent | None = None
        self.diet_agent: ReActAgent | None = None
        self.training_agent: ReActAgent | None = None

    # ------------------------------------------------------------------
    # 模型创建
    # ------------------------------------------------------------------

    def _make_vision_model(self) -> DashScopeChatModel:
        return self.cfg.get_vision_model(self.api_key)

    def _make_reasoning_model(self, stream: bool = True) -> DashScopeChatModel:
        """创建推理模型。"""
        return DashScopeChatModel(
            model_name=self.cfg.reasoning_model,
            api_key=self.api_key,
            stream=stream,
            enable_thinking=True,
        )

    # ------------------------------------------------------------------
    # SubAgent 创建
    # ------------------------------------------------------------------

    def _make_sub_agent(
        self,
        name: str,
        sys_prompt: str,
        skill_names: list[str],
        stream: bool = False,
    ) -> ReActAgent:
        """创建一个带有特定技能集的 SubAgent。"""
        from agentscope.tool import Toolkit

        model = DashScopeChatModel(
            model_name=self.cfg.reasoning_model,
            api_key=self.api_key,
            stream=stream,
            enable_thinking=True,
        )

        toolkit = Toolkit()
        for skill_dir in self.skill_manager.get_skill_dirs(skill_names):
            toolkit.register_agent_skill(skill_dir)

        agent = ReActAgent(
            name=name,
            model=model,
            sys_prompt=sys_prompt,
            toolkit=toolkit,
            formatter=DashScopeChatFormatter(),
        )
        agent.set_console_output_enabled(False)
        return agent

    def _get_or_create_master_agent(
        self, base_sys_prompt: str, user_id: int | str, stream: bool = True
    ) -> ReActAgent:
        """获取或创建主子Agent（懒初始化）。"""
        if self.master_agent is None or stream != (getattr(self.master_agent.model, "stream", True)):
            full_prompt = base_sys_prompt + MASTER_SYS_PROMPT_ADDON
            self.master_agent = self._make_sub_agent(
                name="Rogers",
                sys_prompt=full_prompt,
                skill_names=SKILL_BINDINGS["all"],
                stream=stream,
            )
        return self.master_agent

    def _get_or_create_diet_agent(self) -> ReActAgent:
        if self.diet_agent is None:
            self.diet_agent = self._make_sub_agent(
                name="DietAnalyst",
                sys_prompt=SUB_AGENT_SYS_PROMPTS["diet"],
                skill_names=SKILL_BINDINGS["diet"],
                stream=False,
            )
        return self.diet_agent

    def _get_or_create_training_agent(self) -> ReActAgent:
        if self.training_agent is None:
            self.training_agent = self._make_sub_agent(
                name="TrainingAnalyst",
                sys_prompt=SUB_AGENT_SYS_PROMPTS["training"],
                skill_names=SKILL_BINDINGS["training"],
                stream=False,
            )
        return self.training_agent

    # ------------------------------------------------------------------
    # Step 1: 视觉分析
    # ------------------------------------------------------------------

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
                "你只能看到用户上传的图片。请用中文描述图片中与健身相关的内容："
                "食物照片→描述食物种类和份量；身体数据截图→提取关键数字；"
                "训练动作截图→描述姿势要点。只返回描述，不要评价。"
            ),
            formatter=DashScopeChatFormatter(),
        )
        vision_agent.set_console_output_enabled(False)

        result = await vision_agent(msgs)
        desc = result.get_text_content() if hasattr(result, "get_text_content") else str(result)
        logger.info("Vision analysis: %s", desc[:200])
        return Msg(name="VisionAnalyzer", content=desc, role="assistant")

    # ------------------------------------------------------------------
    # Step 2: 主子Agent (非流式，用于检测标记)
    # ------------------------------------------------------------------

    async def _master_step_detect_marker(
        self, input_msgs, base_sys_prompt: str, user_id: int | str
    ) -> tuple[str, dict | None]:
        """运行主子Agent（非流式），返回 (完整文本, pipeline标记或None)。"""
        # 使用非流式模型来获取完整输出
        agent = self._get_or_create_master_agent(base_sys_prompt, user_id, stream=False)
        agent.set_console_output_enabled(False)

        # 直接运行agent获取完整输出
        result = await agent(input_msgs)
        full_text = result.get_text_content() if hasattr(result, "get_text_content") else str(result)

        # 解析 pipeline 标记
        marker = _parse_pipeline_marker(full_text)
        return full_text, marker

    # ------------------------------------------------------------------
    # Step 3: Fanout 并行分析
    # ------------------------------------------------------------------

    async def _fanout_step(
        self, user_msg_text: str, marker: dict
    ) -> dict[str, Msg]:
        """运行 Fanout 管道，并行分析饮食和训练数据。"""
        needs = marker.get("needs", ["diet", "training"])
        agents: list[ReActAgent] = []
        agent_names: list[str] = []

        if "diet" in needs:
            agents.append(self._get_or_create_diet_agent())
            agent_names.append("diet")
        if "training" in needs:
            agents.append(self._get_or_create_training_agent())
            agent_names.append("training")

        if not agents:
            return {}

        # 构建分析指令
        analysis_msg = Msg(
            name="user",
            content=(
                f"用户原始问题：{user_msg_text}\n\n"
                "请调用你的技能查询数据并给出专业分析报告。只输出分析结果，不要对话。"
            ),
            role="user",
        )

        results: dict[str, Msg] = {}
        try:
            fanout_results = await fanout_pipeline(
                agents=agents,
                msg=analysis_msg,
                enable_gather=False,
            )
            for name, result in zip(agent_names, fanout_results):
                results[name] = result
        except Exception as e:
            logger.error("Fanout pipeline failed: %s", e)

        return results

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------

    async def run(
        self,
        msgs,
        user_id: int | str,
        base_sys_prompt: str,
    ):
        """运行完整的管道工作流。

        Yields:
            (Msg, bool) — 流式输出消息和完成标志
        """
        user_msg_text = ""
        if isinstance(msgs, list) and msgs:
            last_msg = msgs[-1]
            if isinstance(last_msg, Msg):
                user_msg_text = last_msg.get_text_content() if hasattr(last_msg, "get_text_content") else str(last_msg)
        elif isinstance(msgs, Msg):
            user_msg_text = msgs.get_text_content() if hasattr(msgs, "get_text_content") else str(msgs)

        # Step 1: 视觉分析
        vision_desc = await self._vision_step(msgs)
        if vision_desc is not None:
            if isinstance(msgs, list):
                msgs = list(msgs) + [vision_desc]
            elif isinstance(msgs, Msg):
                msgs = [msgs, vision_desc]

        # Step 2: 先非流式运行 Master Agent 检测是否需要 pipeline
        full_text, marker = await self._master_step_detect_marker(
            msgs, base_sys_prompt, user_id
        )

        # 如果不需要 Fanout，直接流式输出 master 的结果
        if marker is None or not self.cfg.fanout_enabled:
            # 使用流式模型输出给用户
            agent = self._get_or_create_master_agent(base_sys_prompt, user_id, stream=True)
            agent.set_console_output_enabled(False)
            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last
            return

        # Step 3: 需要 Fanout，执行并行分析
        logger.info("Pipeline marker detected: %s", marker)
        fanout_results = await self._fanout_step(user_msg_text, marker)

        # 先输出子 Agent 的分析结果
        summary_parts = []
        if "diet" in fanout_results:
            diet_text = fanout_results["diet"].get_text_content() if hasattr(fanout_results["diet"], "get_text_content") else str(fanout_results["diet"])
            summary_parts.append(f"## 饮食分析\n{diet_text}")
            diet_msg = Msg(
                name="DietAnalyst",
                content=f"🍎 **饮食分析**\n\n{diet_text}",
                role="assistant",
            )
            yield diet_msg, False
        if "training" in fanout_results:
            train_text = fanout_results["training"].get_text_content() if hasattr(fanout_results["training"], "get_text_content") else str(fanout_results["training"])
            summary_parts.append(f"## 训练分析\n{train_text}")
            train_msg = Msg(
                name="TrainingAnalyst",
                content=f"💪 **训练分析**\n\n{train_text}",
                role="assistant",
            )
            yield train_msg, False

        # Step 4: 主子Agent 汇总并流式输出最终结果
        if summary_parts:
            summary_msg = Msg(
                name="user",
                content=(
                    f"以下是子Agent的分析结果，请基于这些结果和之前的对话，"
                    f"给用户一个完整、温暖的综合回复：\n\n"
                    + "\n\n".join(summary_parts)
                ),
                role="user",
            )
            agent = self._get_or_create_master_agent(base_sys_prompt, user_id, stream=True)
            agent.set_console_output_enabled(False)
            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(summary_msg),
            ):
                msg.name = "Rogers"
                yield msg, last
