"""工具调用准确性评估 — 工具选择 + 参数正确性"""
from agentscope.evaluate import MetricBase, MetricResult, MetricType, SolutionOutput


class ToolAccuracyMetric(MetricBase):
    """评估工具调用准确性"""

    def __init__(self, tool_match_weight: float = 0.5, param_match_weight: float = 0.5):
        super().__init__(
            name="tool_accuracy",
            metric_type=MetricType.NUMERICAL,
            description="评估工具选择准确性、参数正确性、执行成功率",
            categories=["accuracy", "tool_usage"],
        )
        self.tool_match_weight = tool_match_weight
        self.param_match_weight = param_match_weight

    async def __call__(self, solution: SolutionOutput) -> MetricResult:
        trajectory = solution.trajectory or []
        expected_tools = solution.ground_truth.get("expected_tools", [])

        if not expected_tools:
            return MetricResult(
                name=self.name, result=1.0,
                message="No expected tools defined, skipping",
            )

        # 工具选择匹配
        actual_tools = [
            t.get("tool_name") for t in trajectory
            if t.get("phase") in ("completed", "pending")
        ]
        tool_match = set(actual_tools) == set(expected_tools)

        # 参数正确性（子集匹配）
        expected_params = solution.ground_truth.get("expected_params", {})
        param_correct = True
        if expected_params:
            for tool_call in trajectory:
                if tool_call.get("phase") not in ("completed", "pending"):
                    continue
                actual_params = tool_call.get("input", {})
                for key, value in expected_params.items():
                    if actual_params.get(key) != value:
                        param_correct = False
                        break

        score = (
            self.tool_match_weight * (1.0 if tool_match else 0.0) +
            self.param_match_weight * (1.0 if param_correct else 0.0)
        )

        return MetricResult(
            name=self.name, result=score,
            message=f"Tool match: {tool_match}, Param correct: {param_correct}",
        )
