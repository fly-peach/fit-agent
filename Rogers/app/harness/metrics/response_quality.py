"""回答质量评估 — LLM-as-Judge，带本地缓存避免重复调用"""
import os
import json
from agentscope.evaluate import MetricBase, MetricResult, MetricType, SolutionOutput


class ResponseQualityMetric(MetricBase):
    """使用 LLM-as-Judge 评估回答质量"""

    _JUDGE_CACHE: dict[str, float] = {}

    def __init__(self, judge_model: str = "qwen3.5-plus"):
        super().__init__(
            name="response_quality",
            metric_type=MetricType.NUMERICAL,
            description="使用 LLM 评估回答的相关性、准确性、完整性",
            categories=["quality", "llm_judge"],
        )
        self.judge_model = judge_model

    async def __call__(self, solution: SolutionOutput) -> MetricResult:
        from agentscope.model import DashScopeChatModel
        from agentscope.message import Msg

        response = solution.output
        task_input = solution.metadata.get("task_input", "")

        # 缓存 key：避免重复评判
        cache_key = f"{task_input[:50]}|{response[:100]}"
        if cache_key in self._JUDGE_CACHE:
            return MetricResult(
                name=self.name, result=self._JUDGE_CACHE[cache_key],
                message="Cached judge result",
            )

        judge_prompt = f"""请评估以下 AI 回答的质量。

用户问题：{task_input}
AI 回答：{response}

评估维度（1-5分）：
1. 相关性：回答是否与问题相关
2. 准确性：回答内容是否正确
3. 完整性：回答是否完整覆盖问题
4. 友好度：回答是否友好、易于理解

请输出 JSON 格式：
{{"score": 4.2, "reason": "回答相关且准确，但缺少具体建议"}}
"""

        try:
            model = DashScopeChatModel(
                model_name=self.judge_model,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                stream=False,
            )
            msg = Msg("user", judge_prompt, "user")
            result = await model([msg])

            content = result.content if hasattr(result, "content") else str(result)
            score_data = json.loads(content)
            score = score_data.get("score", 0) / 5.0

            self._JUDGE_CACHE[cache_key] = score

            return MetricResult(
                name=self.name, result=score,
                message=score_data.get("reason", "No reason provided"),
            )
        except Exception as e:
            return MetricResult(
                name=self.name, result=0.0,
                message=f"Judge failed: {str(e)}",
            )
