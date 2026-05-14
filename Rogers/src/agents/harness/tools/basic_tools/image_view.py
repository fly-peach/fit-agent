"""图片分析工具：调用 DashScope 视觉模型分析图片内容。"""
from agentscope.tool import ToolResponse, dashscope_image_to_text
from agentscope.message import TextBlock


async def analyze_image(
    image_urls: str | list[str],
    prompt: str = "请详细描述这张图片的内容",
    api_key: str = "",
    model: str = "qwen-vl-plus",
) -> ToolResponse:
    """分析一张或多张图片，返回 AI 对图片的文字描述。

    支持本地文件路径和网络URL。

    Args:
        image_urls (str | list[str]):
            图片的 URL 或本地路径。可以传单张图片的字符串，或多张图片的列表。
        prompt (str, defaults to '请详细描述这张图片的内容'):
            向视觉模型提出的问题或指令。
        api_key (str):
            阿里云 DashScope API Key。
        model (str, defaults to 'qwen-vl-plus'):
            使用的视觉模型。可选 qwen-vl-plus、qwen-vl-max 等。
    """
    # 将单张图片包装为列表，兼容 dashscope_image_to_text 的签名
    if isinstance(image_urls, str):
        urls = [image_urls]
    else:
        urls = image_urls

    return dashscope_image_to_text(
        image_urls=urls,
        api_key=api_key,
        prompt=prompt,
        model=model,
    )
