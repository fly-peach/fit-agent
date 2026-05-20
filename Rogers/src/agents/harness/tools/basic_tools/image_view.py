"""图片分析工具：调用 DashScope 视觉模型分析图片内容。"""
from agentscope.tool import ToolResponse, dashscope_image_to_text
from agentscope.message import TextBlock


def _error_response(text: str) -> ToolResponse:
    """返回统一的错误文本响应。"""
    return ToolResponse(content=[TextBlock(type="text", text=text)])


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
    # 将单张图片包装为列表，兼容 dashscope_image_to_text 的签名。
    if isinstance(image_urls, str):
        raw_urls = [image_urls]
    else:
        raw_urls = image_urls

    urls = [item.strip() for item in raw_urls if isinstance(item, str) and item.strip()]
    if not urls:
        return _error_response("错误: 请至少提供一张有效图片的本地路径或 URL")

    # 临时文件处理：将 DashScope 无法访问的 localhost 图片下载为临时文件
    import urllib.parse
    import tempfile
    import os
    import httpx
    from pathlib import Path
    
    processed_urls = []
    temp_files = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for url in urls:
                try:
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme in ('http', 'https') and parsed.hostname in ('localhost', '127.0.0.1'):
                        resp = await client.get(url)
                        resp.raise_for_status()
                        
                        # 创建临时文件
                        suffix = Path(parsed.path).suffix or '.jpg'
                        fd, temp_path = tempfile.mkstemp(suffix=suffix)
                        with os.fdopen(fd, 'wb') as f:
                            f.write(resp.content)
                        
                        processed_urls.append(temp_path)
                        temp_files.append(temp_path)
                        continue
                except Exception:
                    pass
                # 无论是否下载成功，只要没有continue，都把原url塞回去让SDK自己处理
                processed_urls.append(url)

        if not api_key.strip():
            return _error_response("错误: 缺少 DashScope API Key，无法执行图片分析")

        final_prompt = prompt.strip() or "请详细描述这张图片的内容"

        try:
            return dashscope_image_to_text(
                image_urls=processed_urls,
                api_key=api_key,
                prompt=final_prompt,
                model=model,
            )
        except Exception as exc:
            return _error_response(f"图片分析失败: {exc}")
    finally:
        # 清理生成的临时文件
        for tmp_file in temp_files:
            try:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except Exception:
                pass
