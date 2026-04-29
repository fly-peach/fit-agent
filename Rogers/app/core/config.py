"""App Configuration"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 确保可以导入 src.fitme
ROGERS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROGERS_DIR / "src"))
from src.fitme.core.config import settings
# Environment configuration for AgentScope backend


load_dotenv()

# DashScope API configuration (primary)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

# OpenAI-compatible API configuration (optional fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Redis configuration (None = use fakeredis for dev)
REDIS_URL = os.getenv("REDIS_URL", None)

__all__ = ["settings"]