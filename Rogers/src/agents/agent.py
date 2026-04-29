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

load_dotenv()
# if os.environ.get("DASHSCOPE_API_KEY") is None:
#     raise ValueError("DASHSCOPE_API_KEY is not set")


def get_weather(location: str, date: str) -> ToolResponse:
    """获取天气数据函数工具."""
    print(f"Getting weather for {location} on {date}...")
    return ToolResponse(content=[{"type": "text", "text": f"The weather in {location} is sunny with a temperature of 25°C."}])

# Create toolkit with Python execution
toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(get_weather)

# Create agent
rogers_agent = ReActAgent(
    name="Rogers",
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