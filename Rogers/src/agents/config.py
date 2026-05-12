"""Rogers Agent 简单配置

基于环境变量的轻量级配置方案。
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class Config:
    """Rogers Agent 配置。"""

    # API 配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # 模型配置
    VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen-vl-max")
    REASONING_MODEL: str = os.getenv("REASONING_MODEL", "qwen-max")

    # 服务器配置
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Pipeline 配置
    FANOUT_ENABLED: bool = os.getenv("FANOUT_ENABLED", "true").lower() == "true"

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置 API Key。"""
        return bool(cls.DASHSCOPE_API_KEY)


# 全局配置实例
config = Config()
