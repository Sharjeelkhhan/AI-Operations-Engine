from evaluation.metrics import (
    compute_accuracy,
    compute_confidence_stats,
    compute_per_category,
    summarize,
)


def _result(case_id, expected, actual, confidence=0.9):
    return {
        "case_id": case_id,
        "expected": expected,
        "actual": actual,
        "confidence": confidence,
    }


def test_compute_accuracy_all_correct():
    results = [_result(f"C{i}", "A", "A") for i in range(5)]
    assert compute_accuracy(results) == 1.0


def test_compute_accuracy_half_correct():
    results = [_result("C1", "A", "A"), _result("C2", "A", "B")]
    assert compute_accuracy(results) == 0.5


def test_compute_accuracy_empty():
    assert compute_accuracy([]) == 0.0


def test_per_category_groups_correctly():
    results = [
        _result("C1", "REFUND_RECOMMENDED", "REFUND_RECOMMENDED"),
        _result("C2", "REFUND_RECOMMENDED", "HUMAN_REVIEW"),
        _result("C3", "HUMAN_REVIEW", "HUMAN_REVIEW"),
    ]
    cats = compute_per_category(results, {})
    assert cats["REFUND_RECOMMENDED"]["correct"] == 1
    assert cats["REFUND_RECOMMENDED"]["total"] == 2
    assert cats["REFUND_RECOMMENDED"]["accuracy"] == 0.5
    assert cats["HUMAN_REVIEW"]["accuracy"] == 1.0


def test_confidence_stats_split():
    results = [
        _result("C1", "A", "A", 0.95),
        _result("C2", "A", "A", 0.90),
        _result("C3", "A", "B", 0.60),
    ]
    stats = compute_confidence_stats(results)
    assert stats["count_correct"] == 2
    assert stats["count_incorrect"] == 1
    assert abs(stats["avg_correct"] - 0.925) < 0.001


def test_summarize_counts_failures():
    results = [
        _result("C1", "A", "A"),
        _result("C2", "A", "B"),
        _result("C3", "A", "B"),
    ]
    s = summarize(results)
    assert s["total_cases"] == 3
    assert s["correct"] == 1
    assert s["failure_count"] == 2