"""记忆搜索工具工厂。

创建绑定到 ReMeLightMemoryManager 实例的 memory_search 工具函数。
"""
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock


def create_memory_search_tool(memory_manager):
    """创建绑定 memory_manager 的 memory_search 工具函数。

    Args:
        memory_manager: ReMeLightMemoryManager 实例。

    Returns:
        一个可注册为工具的异步函数。
    """

    async def memory_search(
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
    ) -> ToolResponse:
        """语义搜索历史记忆文件。

        在回答关于先前工作、决策、日期、用户偏好或待办事项之前使用。
        返回最相关的文本片段及文件路径和行号。

        Args:
            query: 语义搜索查询字符串。
            max_results: 最大返回结果数，默认 5。
            min_score: 最低相关性分数阈值，默认 0.1。

        Returns:
            ToolResponse: 搜索结果，包含路径、行号和内容。
        """
        if memory_manager is None:
            return ToolResponse(
                content=[TextBlock(type="text", text="记忆系统未启用")],
            )
        try:
            return await memory_manager.memory_search(
                query=query,
                max_results=max_results,
                min_score=min_score,
            )
        except Exception as e:
            return ToolResponse(
                content=[TextBlock(type="text", text=f"记忆搜索失败: {e}")],
            )

    return memory_search
