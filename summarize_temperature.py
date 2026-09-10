"""Turn results/temperature.jsonl into consistency tables (Markdown).

For each model and temperature, looking at the repeats of each ticket:
- Label agreement: how often a label matches that ticket's most common answer.
  100% = the model gave the same label every single time.
- Distinct answers: how many different complete answers came back per ticket.
  1.0 = identical every time.
- Summary overlap: average word overlap between summaries of the same ticket
  (1.0 = word-for-word identical), like the word-overlap check in fastapi-rag.
- Matches answer key: how often labels match data/eval_tickets.json
  (a small preview of Phase 3).

Run:  .venv/bin/python summarize_temperature.py              (latest run)
      .venv/bin/python summarize_temperature.py --run-id 20260910-170000
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean

RESULTS_FILE = Path("results/temperature.jsonl")
SUMMARY_FILE = Path("results/temperature_summary.md")
LABELS = ("category", "priority", "sentiment")


def load_rows(run_id=None):
    rows = [json.loads(line) for line in RESULTS_FILE.read_text().splitlines() if line.strip()]
    run_id = run_id or max(r["run_id"] for r in rows)
    return run_id, [r for r in rows if r["run_id"] == run_id]


def word_overlap(a, b):
    wa, wb = set(re.findall(r"[a-z0-9']+", a.lower())), set(re.findall(r"[a-z0-9']+", b.lower()))
    return len(wa & wb) / len(wa | wb) if wa | wb else 1.0


def pct(x):
    return f"{x:.0%}" if x is not None else "–"


def ticket_stats(rows):
    """Consistency numbers for the repeats of ONE ticket, at one model + temperature."""
    answers = [r["answer"] for r in rows if r["ok"]]
    if not answers:
        return None
    agreement = {label: Counter(a[label] for a in answers).most_common(1)[0][1] / len(answers)
                 for label in LABELS}
    distinct = len({json.dumps(a, sort_keys=True) for a in answers})
    pairs = list(combinations([a["summary"] for a in answers], 2))
    overlap = mean(word_overlap(x, y) for x, y in pairs) if pairs else 1.0
    return {"agreement": agreement, "distinct": distinct, "overlap": overlap}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()
    run_id, rows = load_rows(args.run_id)

    by_ticket = defaultdict(list)  # (model, temperature, ticket) -> rows
    for r in rows:
        by_ticket[(r["model"], r["temperature"], r["ticket_id"])].append(r)
    settings = sorted({(r["model"], r["temperature"]) for r in rows})

    consistency = [
        "| Model | Temp | Valid | Category agree | Priority agree | Sentiment agree "
        "| Distinct answers / ticket | Summary overlap |",
        "|---|---|---|---|---|---|---|---|",
    ]
    accuracy = [
        "| Model | Temp | Category | Priority | Sentiment |",
        "|---|---|---|---|---|",
    ]
    for model, temp in settings:
        these = [r for r in rows if r["model"] == model and r["temperature"] == temp]
        stats = [s for (m, t, _), rs in by_ticket.items() if (m, t) == (model, temp)
                 for s in [ticket_stats(rs)] if s]
        valid = [r for r in these if r["ok"]]
        consistency.append(
            f"| {model} | {temp} | {len(valid)}/{len(these)} "
            + "".join(f"| {pct(mean(s['agreement'][l] for s in stats))} " for l in LABELS)
            + f"| {mean(s['distinct'] for s in stats):.1f} "
            f"| {mean(s['overlap'] for s in stats):.2f} |"
        )
        accuracy.append(
            f"| {model} | {temp} "
            + "".join(f"| {pct(mean(r['answer'][l] == r['expected'][l] for r in valid))} "
                      for l in LABELS) + "|"
        )

    per_ticket = [
        "| Ticket | Model | Temp | Category | Priority | Sentiment | Expected |",
        "|---|---|---|---|---|---|---|",
    ]
    for (model, temp, ticket_id), rs in sorted(by_ticket.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        answers = [r["answer"] for r in rs if r["ok"]]
        cells = ["".join(f"{k}×{v} " for k, v in Counter(a[l] for a in answers).most_common()).strip()
                 for l in LABELS]
        exp = rs[0]["expected"]
        per_ticket.append(f"| {ticket_id} | {model} | {temp} | " + " | ".join(cells)
                          + f" | {exp['category']}/{exp['priority']}/{exp['sentiment']} |")

    report = (
        f"# Temperature experiment (run {run_id}, {len(rows)} runs, "
        f"prompt {rows[0]['prompt_version']})\n\n"
        f"## Consistency across repeats\n\n" + "\n".join(consistency) + "\n\n"
        "Agreement = how often a label matched that ticket's most common answer "
        "(100% = never changed). Distinct answers = different complete answers per ticket "
        "(1.0 = identical every time). Summary overlap = shared words between summaries "
        "of the same ticket (1.00 = word-for-word identical).\n\n"
        f"## Matches the answer key\n\n" + "\n".join(accuracy) + "\n\n"
        f"## Every ticket (label × times given)\n\n" + "\n".join(per_ticket) + "\n"
    )
    SUMMARY_FILE.write_text(report)
    print(report)
    print(f"(saved to {SUMMARY_FILE})")


if __name__ == "__main__":
    main()
