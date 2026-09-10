"""Turn the raw rows in results/benchmark.jsonl into summary tables (Markdown).

"Median" = the middle value; one unusually slow run can't drag it around.
"Worst" = the slowest run (for tokens/sec, the lowest).

Run:  .venv/bin/python summarize.py                 (latest run)
      .venv/bin/python summarize.py --run-id 20260910-154138
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

RESULTS_FILE = Path("results/benchmark.jsonl")
SUMMARY_FILE = Path("results/benchmark_summary.md")


def load_rows(run_id=None):
    rows = [json.loads(line) for line in RESULTS_FILE.read_text().splitlines() if line.strip()]
    run_id = run_id or max(r["run_id"] for r in rows)
    return run_id, [r for r in rows if r["run_id"] == run_id]


def group_by(rows, *keys):
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in keys)].append(r)
    return groups


def med_worst(values, lower_is_better=True):
    worst = max(values) if lower_is_better else min(values)
    return f"{median(values):.2f} / {worst:.2f}"


def model_table(rows):
    lines = [
        "| Model | Cold load (s) | Cold TTFT (s) | Warm TTFT (s) | Tokens/sec | Memory (GB) |",
        "|---|---|---|---|---|---|",
    ]
    for (model,), rs in sorted(group_by(rows, "model").items()):
        cold = [r for r in rs if r["run_type"] == "cold"]
        warm = [r for r in rs if r["run_type"] == "warm"]
        lines.append(
            f"| {model} "
            f"| {median(r['load_s'] for r in cold):.2f} "
            f"| {med_worst([r['ttft_s'] for r in cold])} "
            f"| {med_worst([r['ttft_s'] for r in warm])} "
            f"| {med_worst([r['tokens_per_s'] for r in warm], lower_is_better=False)} "
            f"| {max(r['memory_gb'] for r in rs):.2f} |"
        )
    lines.append("\nTimes and tokens/sec are shown as *median / worst*. "
                 "Cold = model unloaded before the run; warm = model already in memory.")
    return "\n".join(lines)


def prompt_table(rows):
    warm = [r for r in rows if r["run_type"] == "warm"]
    prompt_order = list(dict.fromkeys(r["prompt_id"] for r in warm))  # keep file order
    lines = [
        "| Prompt | Model | Input tokens | Output tokens | Warm TTFT (s) | Total (s) |",
        "|---|---|---|---|---|---|",
    ]
    groups = group_by(warm, "prompt_id", "model")
    for prompt_id in prompt_order:
        for (pid, model), rs in sorted(groups.items()):
            if pid != prompt_id:
                continue
            lines.append(
                f"| {prompt_id} | {model} | {rs[0]['prompt_tokens']} "
                f"| {median(r['output_tokens'] for r in rs):.0f} "
                f"| {median(r['ttft_s'] for r in rs):.2f} "
                f"| {median(r['total_s'] for r in rs):.2f} |"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()

    run_id, rows = load_rows(args.run_id)
    report = (
        f"# Benchmark summary (run {run_id}, {len(rows)} runs)\n\n"
        f"## Per model\n\n{model_table(rows)}\n\n"
        f"## Per prompt (warm runs, medians)\n\n{prompt_table(rows)}\n"
    )
    SUMMARY_FILE.write_text(report)
    print(report)
    print(f"(saved to {SUMMARY_FILE})")


if __name__ == "__main__":
    main()
