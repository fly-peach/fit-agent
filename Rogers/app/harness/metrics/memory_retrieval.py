"""记忆召回效果评估 — 使用分词交集匹配，非简单 in"""
from agentscope.evaluate import MetricBase, MetricResult, MetricType, SolutionOutput


class MemoryRetrievalMetric(MetricBase):
    """评估记忆召回效果"""

    def __init__(self):
        super().__init__(
            name="memory_retrieval",
            metric_type=MetricType.NUMERICAL,
            description="评估记忆提取、召回、注入效果",
            categories=["memory", "retrieval"],
        )

    async def __call__(self, solution: SolutionOutput) -> MetricResult:
        # 检查 1：记忆是否成功提取
        if solution.ground_truth.get("memory_extracted"):
            if not solution.metadata.get("memory_extracted"):
                return MetricResult(
                    name=self.name, result=0.0,
                    message="Memory extraction failed",
                )

        # 检查 2：预期召回的记忆是否命中（字符级 Jaccard 相似度）
        expected_keys = solution.ground_truth.get("expected_memory_used", [])
        actual_memory = solution.metadata.get("memory_hits", [])

        if not expected_keys:
            return MetricResult(name=self.name, result=1.0, message="No expected memory")

        recalled = 0
        for key in expected_keys:
            key_tokens = set(key)
            for hit in actual_memory:
                hit_tokens = set(hit)
                if len(key_tokens & hit_tokens) / max(len(key_tokens), 1) >= 0.8:
                    recalled += 1
                    break

        recall_rate = recalled / len(expected_keys)

        return MetricResult(
            name=self.name, result=recall_rate,
            message=f"Recall rate: {recall_rate:.2%}, Expected: {expected_keys}, Got: {actual_memory}",
        )
