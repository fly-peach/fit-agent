# -*- coding: utf-8 -*-
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit, execute_python_code
from agentscope.memory import InMemoryMemory
from agentscope.session import RedisSession

from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv
load_dotenv()  # 从 .env 文件加载环境变量

# ---------- 模型配置（三个智能体复用同一个配置）----------
_MODEL = DashScopeChatModel(
    "qwen-turbo",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    enable_thinking=True,
    stream=True,
)


def _make_toolkit() -> Toolkit:
    """创建工具包（每个 agent 独立实例）。"""
    tk = Toolkit()
    tk.register_tool_function(execute_python_code)
    return tk


def _make_formatter():
    """创建消息格式化器。"""
    return DashScopeChatFormatter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化服务。"""
    import fakeredis

    fake_redis = fakeredis.aioredis.FakeRedis(
        decode_responses=True
    )
    # 注意：这个 FakeRedis 实例仅用于开发/测试。
    # 在生产环境中，请替换为你自己的 Redis 客户端/连接
    #（例如 aioredis.Redis）。
    app.state.session = RedisSession(
        connection_pool=fake_redis.connection_pool
    )
    try:
        yield
    finally:
        print("AgentApp is shutting down...")


async def three_agent_pipeline(
    agent_a,
    agent_b,
    agent_c,
    msg,
):
    """
    三智能体管道：
    A(分析意图) → B(技术分析) → C(用户体验分析) → A(整合输出)
    """
    # 提取用户原始问题
    user_question = ""
    if isinstance(msg, list) and msg:
        last_msg = msg[-1]
        if isinstance(last_msg, Msg):
            user_question = last_msg.get_text_content() if hasattr(last_msg, "get_text_content") else str(last_msg)
    elif isinstance(msg, Msg):
        user_question = msg.get_text_content() if hasattr(msg, "get_text_content") else str(msg)

    # ========== 步骤 1/4：Agent A 分析用户意图 ==========
    response_a = await agent_a(msg)
    response_a_text = response_a.get_text_content() if hasattr(response_a, "get_text_content") else str(response_a)

    # ========== 步骤 2/4：Agent B 从技术/逻辑角度分析 ==========
    analysis_msg_for_b = Msg(
        name="user",
        content=f"用户原始问题：{user_question}\n\n意图分析员的分析结果：\n{response_a_text}\n\n请从技术/逻辑角度进行深入分析。",
        role="user",
    )
    response_b = await agent_b([analysis_msg_for_b])
    response_b_text = response_b.get_text_content() if hasattr(response_b, "get_text_content") else str(response_b)

    # ========== 步骤 3/4：Agent C 从用户体验/实践角度分析 ==========
    analysis_msg_for_c = Msg(
        name="user",
        content=f"用户原始问题：{user_question}\n\n意图分析员的分析结果：\n{response_a_text}\n\n请从用户体验/实践角度进行深入分析。",
        role="user",
    )
    response_c = await agent_c([analysis_msg_for_c])
    response_c_text = response_c.get_text_content() if hasattr(response_c, "get_text_content") else str(response_c)

    # ========== 步骤 4/4：Agent A 整合并给出最终答案 ==========
    summary_msg = Msg(
        name="user",
        content=f"""用户原始问题：{user_question}

以下是两位分析员的分析结果：

【分析员 B（技术/逻辑角度）】：
{response_b_text}

【分析员 C（用户体验/实践角度）】：
{response_c_text}

请综合以上分析，给出一个完整、专业的最终回答。
""",
        role="user",
    )
    final_response = await agent_a([summary_msg])

    return final_response, response_b_text, response_c_text


# 创建 AgentApp
agent_app = AgentApp(
    app_name="ThreeAgentWorkflow",
    app_description="三智能体工作流演示：意图分析 → 技术分析 → 用户体验分析 → 整合输出",
    lifespan=lifespan,
)


@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest = None,
    **kwargs,
):
    """处理用户查询 — 三智能体工作流。"""
    session_id = request.session_id
    user_id = request.user_id

    # ========== Agent A：意图分析员 & 最终整合 ==========
    agent_a = ReActAgent(
        name="意图分析员",
        model=_MODEL,
        sys_prompt=(
            "你是一个专业的意图分析专家。当第一次收到用户问题时，你需要：\n"
            "1. 先思考（思考过程要详细）\n"
            "2. 分析用户的问题意图\n"
            "3. 明确用户想知道什么、关注点在哪里\n"
            "4. 输出你的分析结果\n\n"
            "当最后收到两位分析员的分析结果时，你需要：\n"
            "1. 先思考（思考过程要详细）\n"
            "2. 综合两位分析员的观点\n"
            "3. 给出一个完整、专业的最终回答\n\n"
            "用中文回答。"
        ),
        toolkit=_make_toolkit(),
        memory=InMemoryMemory(),
        formatter=_make_formatter(),
    )

    # ========== Agent B：技术/逻辑分析员 ==========
    agent_b = ReActAgent(
        name="分析员B",
        model=_MODEL,
        sys_prompt=(
            "你是分析员 B，擅长从技术/逻辑角度分析问题。\n"
            "请基于用户问题和意图分析，从技术可行性、逻辑严谨性等角度进行深入分析。\n"
            "先思考（思考过程要详细），然后输出你的分析结果。\n"
            "用中文回答。"
        ),
        toolkit=_make_toolkit(),
        memory=InMemoryMemory(),
        formatter=_make_formatter(),
    )

    # ========== Agent C：用户体验/实践分析员 ==========
    agent_c = ReActAgent(
        name="分析员C",
        model=_MODEL,
        sys_prompt=(
            "你是分析员 C，擅长从用户体验/实践角度分析问题。\n"
            "请基于用户问题和意图分析，从用户需求、实际应用场景等角度进行深入分析。\n"
            "先思考（思考过程要详细），然后输出你的分析结果。\n"
            "用中文回答。"
        ),
        toolkit=_make_toolkit(),
        memory=InMemoryMemory(),
        formatter=_make_formatter(),
    )

    # 关闭终端打印，改为通过 stream_printing_messages 返回
    agent_a.set_console_output_enabled(False)
    agent_b.set_console_output_enabled(False)
    agent_c.set_console_output_enabled(False)

    # 从 session 恢复分析员 A 的记忆状态
    await agent_app.state.session.load_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent_a,
    )

    # 运行完整的三智能体工作流
    final_response, response_b_text, response_c_text = await three_agent_pipeline(
        agent_a=agent_a,
        agent_b=agent_b,
        agent_c=agent_c,
        msg=msgs,
    )

    # 输出分析员 B 的结果（使用特殊标记）
    yield Msg(
        name="分析员B",
        content=f"---ANALYST_B_START---\n{response_b_text}\n---ANALYST_B_END---",
        role="assistant",
    ), False

    # 输出分析员 C 的结果（使用特殊标记）
    yield Msg(
        name="分析员C",
        content=f"---ANALYST_C_START---\n{response_c_text}\n---ANALYST_C_END---",
        role="assistant",
    ), False

    # 输出最终结果
    yield final_response, True

    # 保存分析员 A 的 session 状态
    await agent_app.state.session.save_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent_a,
    )


if __name__ == "__main__":
    agent_app.run(host="127.0.0.1", port=8000)
