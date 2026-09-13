"""Pure metric-computation functions for evaluation. No side effects."""
from typing import List, Dict


def compute_accuracy(results: List[dict]) -> float:
    """Overall accuracy: correct / total."""
    if not results:
        return 0.0
    correct = sum(1 for r in results if r["actual"] == r["expected"])
    return correct / len(results)


def compute_per_category(results: List[dict], expected_by_case: Dict[str, str]) -> Dict[str, dict]:
    """Group results by expected decision category and compute accuracy per category."""
    buckets: Dict[str, dict] = {}
    for r in results:
        expected = r["expected"]
        if expected not in buckets:
            buckets[expected] = {"correct": 0, "total": 0}
        buckets[expected]["total"] += 1
        if r["actual"] == expected:
            buckets[expected]["correct"] += 1

    for cat, stats in buckets.items():
        stats["accuracy"] = stats["correct"] / stats["total"] if stats["total"] else 0.0

    return buckets


def compute_confidence_stats(results: List[dict]) -> dict:
    """Average confidence for correct vs incorrect decisions."""
    correct = [r["confidence"] for r in results if r.get("actual") == r["expected"] and "confidence" in r]
    incorrect = [r["confidence"] for r in results if r.get("actual") != r["expected"] and "confidence" in r]

    return {
        "avg_correct": sum(correct) / len(correct) if correct else 0.0,
        "avg_incorrect": sum(incorrect) / len(incorrect) if incorrect else 0.0,
        "count_correct": len(correct),
        "count_incorrect": len(incorrect),
    }


def summarize(results: List[dict]) -> dict:
    """Top-level summary metrics."""
    total = len(results)
    correct = sum(1 for r in results if r["actual"] == r["expected"])
    failures = [r for r in results if r["actual"] != r["expected"]]

    return {
        "total_cases": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "failure_count": len(failures),
        "failures": failures,
    }