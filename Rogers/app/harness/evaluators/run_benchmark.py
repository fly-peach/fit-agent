"""评估执行脚本 — 本地运行 + 报告生成。"""
import asyncio
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from agentscope.evaluate import GeneralEvaluator, FileEvaluatorStorage

from app.harness.benchmark.fitness_benchmark import FitnessBenchmark
from app.harness.solutions.rogers_agent import fit_agent_solution


async def run_fitness_benchmark(
    output_dir: str = "./eval_results",
    n_repeat: int = 1,
    parallel: bool = False,
):
    """运行健身场景基准测试"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    storage = FileEvaluatorStorage(
        save_dir=str(output_path / f"fitness_{timestamp}"),
    )

    benchmark = FitnessBenchmark()
    evaluator = GeneralEvaluator(
        name="Rogers Fitness Benchmark",
        benchmark=benchmark,
        n_repeat=n_repeat,
        storage=storage,
        n_workers=1 if not parallel else 4,
    )

    print(f"Starting Fitness Benchmark at {timestamp}")
    print(f"Tasks: {len(benchmark)}, Repeat: {n_repeat}")

    results = await evaluator.run(fit_agent_solution)

    report = generate_report(results)
    report_path = output_path / f"report_{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nBenchmark completed!")
    print(f"Report saved to: {report_path}")
    print(f"Overall score: {report['overall_score']:.2%}")

    return report


def generate_report(results) -> dict:
    """生成评估报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": len(results),
        "successful_tasks": sum(1 for r in results if r.success),
        "failed_tasks": sum(1 for r in results if not r.success),
        "overall_score": 0.0,
        "metrics_summary": {},
        "category_breakdown": {},
        "failed_cases": [],
    }

    category_scores = defaultdict(list)

    for result in results:
        category = result.task.tags.get("category", "unknown")

        for metric_result in result.metric_results:
            metric_name = metric_result.name
            if metric_name not in report["metrics_summary"]:
                report["metrics_summary"][metric_name] = []
            report["metrics_summary"][metric_name].append(metric_result.result)

        task_score = (
            sum(m.result for m in result.metric_results) / len(result.metric_results)
            if result.metric_results else 0
        )
        category_scores[category].append(task_score)

        if not result.success or task_score < 0.5:
            report["failed_cases"].append({
                "task_id": result.task.id,
                "category": category,
                "score": task_score,
                "error": getattr(result, "error", None),
            })

    all_scores = []
    for scores in category_scores.values():
        all_scores.extend(scores)
    report["overall_score"] = sum(all_scores) / len(all_scores) if all_scores else 0

    for metric_name, scores in report["metrics_summary"].items():
        report["metrics_summary"][metric_name] = {
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
        }

    for category, scores in category_scores.items():
        report["category_breakdown"][category] = {
            "mean": sum(scores) / len(scores),
            "count": len(scores),
        }

    return report


if __name__ == "__main__":
    asyncio.run(run_fitness_benchmark(n_repeat=1))
