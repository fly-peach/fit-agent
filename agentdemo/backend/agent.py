import os


from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit, execute_python_code, ToolResponse
from agentscope.memory import InMemoryMemory


from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv

# load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
# if os.environ.get("DASHSCOPE_API_KEY") is None:
#     raise ValueError("DASHSCOPE_API_KEY is not set")



def get_weather(location: str, date: str) -> ToolResponse:
    """获取天气数据函数工具."""
    print(f"Getting weather for {location} on {date}...")
    return ToolResponse(content=[{"type": "text", "text": f"The weather in {location} is sunny with a temperature of 25°C."}])


# 创建 AgentApp
agent_app = AgentApp(
    app_name="MyAssistant",
    app_description="A helpful assistant agent",
)

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest | None = None,
    **kwargs,
):
    """处理用户查询。"""
    assert request is not None, "request is required"
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
            api_key=os.environ["DASHSCOPE_API_KEY"],
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

    async for msg, last, *_ in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(msgs),
    ):
        yield msg, last

    await agent_app.state.session.save_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )


