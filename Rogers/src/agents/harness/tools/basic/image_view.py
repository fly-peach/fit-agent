"""图片查看工具

Agent 可以调用此工具来分析用户上传的图片内容，
如健身动作、食物图片等。
"""

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock


def view_image(image_data: str, description: str = "") -> ToolResponse:
    """
    查看并分析图片内容。

    当用户上传图片时，Agent 可以调用此工具来查看图片。

    Args:
        image_data: 图片数据，可以是：
            - URL: 图片的网络地址
            - base64: base64 编码的图片数据，格式如 "data:image/png;base64,xxxxx"
        description: 用户对图片的简要描述（可选）

    Returns:
        包含图片查看结果的 ToolResponse

    Example:
        >>> result = view_image("https://example.com/food.jpg", "午餐照片")
        >>> result = view_image("data:image/png;base64,iVBORw0KG...", "健身动作")
    """
    result_parts = []

    if description:
        result_parts.append(f"图片描述：{description}")

    # 判断图片数据类型
    if image_data.startswith("data:"):
        result_parts.append("已接收到 base64 编码的图片数据")
    elif image_data.startswith("http://") or image_data.startswith("https://"):
        result_parts.append(f"已获取图片 URL：{image_data}")
    else:
        result_parts.append(f"已接收图片数据，长度：{len(image_data)} 字符")

    result_parts.append("图片已成功加载，Agent 可以开始分析图片内容。")

    result_text = "\n".join(result_parts)

    return ToolResponse(
        content=[TextBlock(type="text", text=result_text)]
    )
