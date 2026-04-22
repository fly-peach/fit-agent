"""Harness 配置对象 — 六层能力通过 Pydantic BaseModel 注入 FitAgent。"""
from pydantic import BaseModel, Field
from typing import Callable, Optional


class ModelConfig(BaseModel):
    """LLM 模型配置"""
    provider: str = "dashscope"
    model_name: str = "qwen3.5-plus"
    api_key: str
    base_url: Optional[str] = None
    enable_thinking: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7


class ToolRegistry(BaseModel):
    """工具注册表"""
    model_config = {"arbitrary_types_allowed": True}

    tools: dict[str, Callable] = Field(default_factory=dict)
    write_tools: set[str] = Field(
        default={"update_daily_metrics", "update_workout_plan", "update_nutrition"},
        description="需要审批的写入工具名集合",
    )

    def register(self, name: str, func: Callable) -> None:
        self.tools[name] = func

    def is_write_tool(self, name: str) -> bool:
        return name in self.write_tools


class GuardConfig(BaseModel):
    """Tool Guard 配置"""
    deny_patterns: list[str] = Field(default_factory=lambda: [
        r"drop\s+table", r"delete\s+from", r"truncate",
        r"rm\s+-rf", r"exec\s*\(", r"eval\s*\(",
    ])
    guard_patterns: list[str] = Field(default_factory=lambda: [
        r"审批", r"批准", r"授权",
    ])
    deny_decision: str = "检测到高风险请求，已阻止执行。"


class ApprovalConfig(BaseModel):
    """审批流程配置"""
    auto_pending: bool = True
    pending_prefix: str = "act_"
    pending_id_length: int = 12
    write_tools: set[str] = Field(
        default={"update_daily_metrics", "update_workout_plan", "update_nutrition"},
    )
    tool_type_map: dict[str, str] = Field(default={
        "update_daily_metrics": "身体指标",
        "update_workout_plan": "训练计划",
        "update_nutrition": "营养摄入",
    })


class MemoryConfig(BaseModel):
    """记忆与上下文治理配置"""
    max_tokens: int = 8000
    compression_threshold: float = 0.8
    compression_strategy: str = "progressive"
    memory_top_k: int = 3
    enable_auto_compress: bool = True


class RecoveryConfig(BaseModel):
    """故障恢复配置"""
    max_retries: int = 3
    retry_delay_ms: int = 1000
    stream_timeout_seconds: float = 15.0
    reconnect_enabled: bool = True


class EvalConfig(BaseModel):
    """评估门禁配置（可选，不传则不开启评估）"""
    benchmark_name: str = "FitnessBench"
    metrics: list[str] = Field(default=["tool_accuracy", "approval_compliance", "safety_guard"])
    output_dir: str = "./eval_results"
