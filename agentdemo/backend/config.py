# Environment configuration for AgentScope backend
import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API configuration (OpenAI-compatible)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-1a5c1d5fd43fbb7562e979b968671")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.getenv("MODEL", "deepseek-chat")

# Use DeepSeek as default
API_KEY = DEEPSEEK_API_KEY
BASE_URL = DEEPSEEK_BASE_URL

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))