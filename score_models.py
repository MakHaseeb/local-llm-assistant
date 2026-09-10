"""Phase 3: score the model comparison and build the report tables (Markdown).

Reads the latest run in results/comparison.jsonl and reports:
1. Accuracy against the answer key: each label, and all three right at once.
2. Priority mix-ups: what each model said vs what the key says. This shows
   HOW a model is wrong, e.g. calling everything urgent.
3. Speed and memory, on warm runs only (the first ticket per model is cold).
4. Hand scores for summary and action-item quality, once
   results/hand_scores.json exists.
5. Every mistake, so each number can be checked against the actual answers.

Run:  .venv/bin/python score_models.py                 (latest run)
      .venv/bin/python score_models.py --run-id 20260910-190000
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

RESULTS_FILE = Path("results/comparison.jsonl")
HAND_SCORES_FILE = Path("results/hand_scores.json")
SUMMARY_FILE = Path("results/comparison_summary.md")
LABELS = ("category", "priority", "sentiment")
PRIORITIES = ("low", "medium", "high", "urgent")


def load_rows(run_id=None):
    rows = [json.loads(line) for line in RESULTS_FILE.read_text().splitlines() if line.strip()]
    run_id = run_id or max(r["run_id"] for r in rows)
    return run_id, [r for r in rows if r["run_id"] == run_id]


def correct(row, label):
    return row["ok"] and row["answer"][label] == row["expected"][label]


def accuracy_table(by_model):
    lines = ["| Model | Category | Priority | Sentiment | All three right | Valid | Needed a retry |",
             "|---|---|---|---|---|---|---|"]
    for model, rs in by_model.items():
        n = len(rs)
        cells = [f"{sum(correct(r, l) for r in rs)}/{n} ({mean(correct(r, l) for r in rs):.0%})"
                 for l in LABELS]
        all3 = sum(all(correct(r, l) for l in LABELS) for r in rs)
        lines.append(f"| {model} | " + " | ".join(cells)
                     + f" | {all3}/{n} ({all3 / n:.0%}) | {sum(r['ok'] for r in rs)}/{n} "
                     f"| {sum(r['attempts'] > 1 for r in rs)} |")
    return "\n".join(lines)


def priority_mixups(model, rs):
    counts = Counter((r["expected"]["priority"], r["answer"]["priority"]) for r in rs if r["ok"])
    lines = [f"**{model}** - rows: answer key, columns: what the model said\n",
             "| Key \\ Model | " + " | ".join(PRIORITIES) + " |",
             "|---|" + "---|" * len(PRIORITIES)]
    for exp in PRIORITIES:
        cells = [(f"**{counts[(exp, got)]}**" if exp == got else str(counts[(exp, got)] or "·"))
                 for got in PRIORITIES]
        lines.append(f"| {exp} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def speed_table(by_model):
    lines = ["| Model | Median time per ticket (s) | Slowest (s) | Median time to first token (s) "
             "| Tokens/sec | Words/sec | Cold load (s) | Memory (GB) |",
             "|---|---|---|---|---|---|---|---|"]
    for model, rs in by_model.items():
        warm = [r for r in rs if not r["cold"]]
        cold = [r for r in rs if r["cold"]]
        cold_load = f"{cold[0]['load_s']:.2f}" if cold else "–"
        lines.append(
            f"| {model} | {median(r['total_s'] for r in warm):.2f} "
            f"| {max(r['total_s'] for r in warm):.2f} "
            f"| {median(r['ttft_s'] for r in warm):.2f} "
            f"| {median(r['tokens_per_s'] for r in warm):.1f} "
            f"| {median(r['words_per_s'] for r in warm):.1f} "
            f"| {cold_load} | {max(r['memory_gb'] or 0 for r in rs):.2f} |"
        )
    return "\n".join(lines)


def hand_score_table():
    if not HAND_SCORES_FILE.exists():
        return "_Not scored yet._"
    scores = json.loads(HAND_SCORES_FILE.read_text())
    by_model = defaultdict(list)
    for s in scores:
        by_model[s["model"]].append(s)
    lines = ["| Model | Tickets scored | Summary (1-3) | Action items (1-3) |", "|---|---|---|---|"]
    for model, ss in sorted(by_model.items()):
        lines.append(f"| {model} | {len(ss)} | {mean(s['summary'] for s in ss):.2f} "
                     f"| {mean(s['action_items'] for s in ss):.2f} |")
    return "\n".join(lines)


def mistakes_list(by_model):
    lines = ["| Ticket | Model | Wrong labels (key → model) |", "|---|---|---|"]
    for model, rs in by_model.items():
        for r in rs:
            if not r["ok"]:
                lines.append(f"| {r['ticket_id']} | {model} | no valid answer |")
                continue
            wrong = [f"{l}: {r['expected'][l]} → {r['answer'][l]}" for l in LABELS if not correct(r, l)]
            if wrong:
                lines.append(f"| {r['ticket_id']} | {model} | " + "; ".join(wrong) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()
    run_id, rows = load_rows(args.run_id)

    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)
    by_model = dict(sorted(by_model.items()))

    report = (
        f"# Model comparison (run {run_id}, prompt {rows[0]['prompt_version']}, "
        f"{len(rows)} runs)\n\n"
        f"## Accuracy against the answer key\n\n{accuracy_table(by_model)}\n\n"
        f"## Priority mix-ups\n\n"
        + "\n\n".join(priority_mixups(m, rs) for m, rs in by_model.items()) + "\n\n"
        f"## Speed and memory (warm tickets)\n\n{speed_table(by_model)}\n\n"
        f"## Hand scores (blind)\n\n{hand_score_table()}\n\n"
        f"## Every mistake\n\n{mistakes_list(by_model)}\n"
    )
    SUMMARY_FILE.write_text(report)
    print(report)
    print(f"(saved to {SUMMARY_FILE})")


if __name__ == "__main__":
    main()
