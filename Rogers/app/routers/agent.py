import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.tool import Toolkit, execute_python_code
from agentscope.pipeline import stream_printing_messages
from agentscope.memory import InMemoryMemory
from agentscope.session import RedisSession

from agentscope_runtime.engine import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv

load_dotenv()


agent_app = AgentApp(
    app_name="rogers-agent",
    app_description="rogers as fitagent to assist user",
)

# 3. 定义请求处理逻辑
@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest = None,
    **kwargs,
):
    session_id = request.session_id
    user_id = request.user_id

    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)


    agent.set_console_output_enabled(enabled=True)

    # 加载 agent 状态
    await agent_app.state.session.load_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )

    try:
        async for msg, last in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(msgs),
        ):
            yield msg, last

    except asyncio.CancelledError:
        # 中断处理逻辑
        print(f"Task {session_id} was manually interrupted.")

        # 为彻底停止底层 agent 的运行，此处须手动中断 agent
        await agent.interrupt()

        # 重新抛出异常，让系统将任务状态标记为 STOPPED
        raise

    finally:
        # 保存 agent 状态
        await agent_app.state.session.save_session_state(
            session_id=session_id,
            user_id=user_id,
            agent=agent,
        )

# 4. 注册中断触发路由
@agent_app.post("/stop")
async def stop_task(request: AgentRequest):
    await agent_app.stop_chat(
        user_id=request.user_id,
        session_id=request.session_id,
    )
    return {
        "status": "success",
        "message": "Interrupt signal broadcasted.",
    }

# 5. 启动应用
agent_app.run(host="127.0.0.1", port=8090)