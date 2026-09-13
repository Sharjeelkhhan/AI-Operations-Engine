"""CLI script to run the evaluation suite and produce reports."""
import json
from datetime import datetime
from pathlib import Path

from evaluation.metrics import (
    compute_confidence_stats,
    compute_per_category,
    summarize,
)
from evaluation.runner import load_expected, run_all

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = PROJECT_ROOT / "evaluation"


def write_json_report(report: dict, path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def write_markdown_report(report: dict, path: Path) -> None:
    lines = []
    lines.append("# NovaDesk AI Decision Engine — Evaluation Report\n")
    lines.append(f"**Run ID:** {report['run_id']}  ")
    lines.append(f"**Timestamp:** {report['timestamp']}  ")
    lines.append(f"**Model:** {report['model']}  ")
    lines.append(f"**Prompt version:** {report['prompt_version']}\n")

    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    s = report["summary"]
    lines.append(f"| Total cases | {s['total_cases']} |")
    lines.append(f"| Correct decisions | {s['correct']} |")
    lines.append(f"| **Accuracy** | **{s['accuracy']*100:.1f}%** |")
    lines.append(f"| Failures | {s['failure_count']} |")
    lines.append(f"| Avg confidence (correct) | {report['confidence']['avg_correct']:.2f} |")
    lines.append(f"| Avg confidence (incorrect) | {report['confidence']['avg_incorrect']:.2f} |")
    lines.append(f"| Avg latency | {report['avg_latency_ms']} ms |")
    lines.append("")

    lines.append("## Per-Category Accuracy\n")
    lines.append("| Expected Category | Correct | Total | Accuracy |")
    lines.append("|-------------------|---------|-------|----------|")
    for cat, stats in sorted(report["per_category"].items()):
        acc = stats["accuracy"] * 100
        lines.append(f"| {cat} | {stats['correct']} | {stats['total']} | {acc:.1f}% |")
    lines.append("")

    if s["failures"]:
        lines.append("## Failures\n")
        for f in s["failures"]:
            lines.append(f"### {f['case_id']}")
            lines.append(f"- **Expected:** `{f['expected']}`")
            lines.append(f"- **Actual:** `{f['actual']}`")
            if "confidence" in f:
                lines.append(f"- **Confidence:** {f['confidence']:.2f}")
            if "reason" in f:
                lines.append(f"- **Reason:** {f['reason']}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    print("Running evaluation on all golden cases...")
    results = run_all()
    print(f"\nCompleted {len(results)} cases.")

    expected_map = load_expected()
    summary = summarize(results)
    per_category = compute_per_category(results, expected_map)
    confidence = compute_confidence_stats(results)

    latencies = [r.get("latency_ms", 0) for r in results]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    report = {
        "run_id": run_id,
        "timestamp": timestamp,
        "model": "openai/gpt-oss-20b",
        "prompt_version": "decision_v1",
        "summary": summary,
        "per_category": per_category,
        "confidence": confidence,
        "avg_latency_ms": avg_latency,
    }

    json_path = EVAL_DIR / "report.json"
    md_path = EVAL_DIR / "report.md"

    write_json_report(report, json_path)
    write_markdown_report(report, md_path)

    print(f"\nReport written to:")
    print(f"  {json_path}")
    print(f"  {md_path}")
    print(f"\nAccuracy: {summary['accuracy']*100:.1f}%")
    print(f"Correct: {summary['correct']}/{summary['total_cases']}")


if __name__ == "__main__":
    main()