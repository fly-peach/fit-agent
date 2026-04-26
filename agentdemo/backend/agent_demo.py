import os
import asyncio

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.tool import Toolkit, execute_python_code


class DeepSeekChatFormatter(OpenAIChatFormatter):
    async def _format(self, msgs: list) -> list:
        formatted_msgs = await super()._format(msgs)
        # 遍历原始消息列表，找到包含 thinking 块的助手消息，给对应的格式化后消息添加 reasoning_content
        for i, msg in enumerate(msgs):
            if isinstance(msg.content, list):
                thinking_parts = []
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "thinking":
                        thinking_parts.append(block.get("thinking", ""))
                if thinking_parts and i < len(formatted_msgs):
                    formatted_msgs[i]["reasoning_content"] = "\n".join(thinking_parts)
        return formatted_msgs


async def creating_react_agent() -> None:
    """创建一个支持 DeepSeek 思考模式的 ReAct 智能体并运行简单任务。"""

    # 准备工具
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)



    # 创建智能体
    Rogers = ReActAgent(
        name="Rogers",
        sys_prompt="你是一个名为 Rogers 的助手",
        model=OpenAIChatModel(
            model_name="deepseek-v4-flash",  # 请确认你使用的模型名，这里是示例
            api_key="sk-1a5c1ef1d5fd43fbb7562e979b968671",
            stream=True,
            client_kwargs={
                "base_url": "https://api.deepseek.com",
            },
            generate_kwargs={
                "extra_body": {
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "high",
                }
            },
        ),
        formatter=DeepSeekChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    # 创建测试消息
    msg = Msg(
        name="user",
        content="你好Rogers， 请使用 Python 运行 Hello World。",
        role="user",
    )

    # 执行
    await Rogers(msg)


if __name__ == "__main__":
    asyncio.run(creating_react_agent())