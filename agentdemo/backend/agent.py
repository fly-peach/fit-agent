import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit, execute_python_code, ToolResponse
from agentscope.memory import InMemoryMemory
from agentscope.session import RedisSession

from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv
from agentscope_runtime.tools.searches import ModelstudioSearch
import asyncio

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
if os.environ.get("DASHSCOPE_API_KEY") is None:
    raise ValueError("DASHSCOPE_API_KEY is not set")
print("APIkey设置没有：=================",os.environ.get("DASHSCOPE_API_KEY"),"===============")


def get_weather(location: str, date: str) -> ToolResponse:
    """Get the weather for a location and date."""
    print(f"Getting weather for {location} on {date}...")
    return ToolResponse(content=[{"type": "text", "text": f"The weather in {location} is sunny with a temperature of 25°C."}])



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

# 创建 AgentApp
agent_app = AgentApp(
    app_name="MyAssistant",
    app_description="A helpful assistant agent",
    lifespan=lifespan,
)

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest = None,
    **kwargs,
):
    """处理用户查询。"""
    session_id = request.session_id
    user_id = request.user_id

    # Create toolkit with Python execution
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(get_weather)

    # Create agent
    agent = ReActAgent(
        name="MyAssistant",
        model=DashScopeChatModel(
            "qwen-turbo",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            enable_thinking=True,
            stream=True,
        ),
        sys_prompt="You're a helpful assistant.",
        toolkit=toolkit,
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )
    agent.set_console_output_enabled(False)

    await agent_app.state.session.load_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )

    async for msg, last in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(msgs),
    ):
        yield msg, last

    await agent_app.state.session.save_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )


