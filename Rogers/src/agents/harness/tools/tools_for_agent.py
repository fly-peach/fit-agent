
from agentscope.tool import ToolResponse, TextBlock ,Toolkit,execute_shell_command

async def my_search(query: str, api_key: str) -> ToolResponse:
    """一个简单的示例工具函数。

    Args:
        query (str):
            搜索查询。
        api_key (str):
            用于身份验证的 API 密钥。
    """
    return ToolResponse(
        content=[
            TextBlock(
                type="text", 
                text=f"正在使用 API 密钥 '{api_key}' 搜索 '{query}'",
            ),
        ],
    )

# 在工具模块中注册工具函数
def build_toolkit() -> Toolkit:
    toolkit = Toolkit()
    toolkit.register_tool_function(my_search)
    toolkit.register_tool_function(execute_shell_command)
    return toolkit   # 返回最终的 tool_for_agent

# 使用
register_tools = build_toolkit()