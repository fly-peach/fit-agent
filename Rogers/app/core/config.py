from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Rogers API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./rogers.db"
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # Agent / LLM runtime
    dashscope_coding_url: str = "https://coding.dashscope.aliyuncs.com/v1"
    dashscope_coding_api_key: str = ""
    model: str = "qwen3.5-plus"
    agent_temperature: float = 0.3
    agent_memory_top_k: int = 5
    agent_framework: str = "agentscope"
    agent_max_iters: int = 8


settings = Settings()
