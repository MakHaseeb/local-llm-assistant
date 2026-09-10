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
    if not values:
        return "–"  # e.g. older runs that had no cached rows
    worst = max(values) if lower_is_better else min(values)
    return f"{median(values):.2f} / {worst:.2f}"


def med(values, fmt="{:.2f}"):
    return fmt.format(median(values)) if values else "–"


def of_type(rows, run_type):
    return [r for r in rows if r["run_type"] == run_type]


def words_per_s(row):
    # Each model splits text into tokens differently, so tokens/sec isn't a fair
    # comparison between models. Words are the same for everyone.
    return len(row["text"].split()) / row["eval_s"]


def model_table(rows):
    lines = [
        "| Model | Cold load (s) | Cold TTFT (s) | Warm TTFT (s) | Cached TTFT (s) | Tokens/sec | Words/sec | Memory (GB) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (model,), rs in sorted(group_by(rows, "model").items()):
        cold, warm, cached = of_type(rs, "cold"), of_type(rs, "warm"), of_type(rs, "cached")
        lines.append(
            f"| {model} "
            f"| {med([r['load_s'] for r in cold])} "
            f"| {med_worst([r['ttft_s'] for r in cold])} "
            f"| {med_worst([r['ttft_s'] for r in warm])} "
            f"| {med_worst([r['ttft_s'] for r in cached])} "
            f"| {med_worst([r['tokens_per_s'] for r in warm], lower_is_better=False)} "
            f"| {med_worst([words_per_s(r) for r in warm], lower_is_better=False)} "
            f"| {max(r['memory_gb'] for r in rs):.2f} |"
        )
    lines.append(
        "\nTimes and speeds are shown as *median / worst*. "
        "Words/sec is the fairer cross-model speed, since each model counts tokens differently. "
        "Cold = model unloaded before the run. Warm = model in memory, new input each time "
        "(what a real new ticket costs). Cached = the exact same input repeated, so Ollama "
        "skips re-reading it."
    )
    return "\n".join(lines)


def prompt_table(rows):
    prompt_order = list(dict.fromkeys(r["prompt_id"] for r in of_type(rows, "warm")))
    lines = [
        "| Prompt | Model | Input tokens | Output tokens | Warm TTFT (s) | Cached TTFT (s) | Total (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    groups = group_by(rows, "prompt_id", "model")
    for prompt_id in prompt_order:
        for (pid, model), rs in sorted(groups.items()):
            if pid != prompt_id:
                continue
            warm, cached = of_type(rs, "warm"), of_type(rs, "cached")
            lines.append(
                f"| {prompt_id} | {model} | {warm[0]['prompt_tokens']} "
                f"| {med([r['output_tokens'] for r in warm], '{:.0f}')} "
                f"| {med([r['ttft_s'] for r in warm])} "
                f"| {med([r['ttft_s'] for r in cached])} "
                f"| {med([r['total_s'] for r in warm])} |"
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
        f"## Per prompt (medians)\n\n{prompt_table(rows)}\n"
    )
    SUMMARY_FILE.write_text(report)
    print(report)
    print(f"(saved to {SUMMARY_FILE})")


if __name__ == "__main__":
    main()
