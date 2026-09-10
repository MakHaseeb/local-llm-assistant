"""Phase 3: blind hand-scoring of summary and action-item quality.

For each chosen ticket, both models' answers are shown as "Answer A" and
"Answer B" in a random order, so the scorer can't favour a model by name.
The order is saved in results/hand_scoring_key.json and only used when
recording scores.

Run:  .venv/bin/python hand_scoring.py show 1                  (print batch 1 of 3)
      .venv/bin/python hand_scoring.py record t01 3 2 2 3      (A summary, A actions,
                                                                B summary, B actions)
      .venv/bin/python hand_scoring.py reveal                  (who was A and B)
"""
import argparse
import json
import random
from pathlib import Path

RESULTS_FILE = Path("results/comparison.jsonl")
TICKETS_FILE = Path("data/eval_tickets.json")
KEY_FILE = Path("results/hand_scoring_key.json")
SCORES_FILE = Path("results/hand_scores.json")

BATCHES = [["t01", "t05", "t09"], ["t12", "t17", "t21"], ["t26", "t28", "t35", "t39"]]

RUBRIC = """Score each answer 1-3:
  Summary       3 = accurate and complete: the main issue and the key details, nothing made up
                2 = mostly right, but misses a key detail or adds something not in the ticket
                1 = wrong, misleading, or misses the main issue
  Action items  3 = the right steps, specific, nothing the customer already tried, nothing made up
                2 = useful, but misses an important step or includes a vague or unnecessary one
                1 = misses the main action, or suggests something wrong or unhelpful"""


def latest_answers():
    """{ticket_id: {model: answer}} from the latest comparison run."""
    rows = [json.loads(line) for line in RESULTS_FILE.read_text().splitlines() if line.strip()]
    run_id = max(r["run_id"] for r in rows)
    answers = {}
    for r in rows:
        if r["run_id"] == run_id and r["ok"]:
            answers.setdefault(r["ticket_id"], {})[r["model"]] = r["answer"]
    return run_id, answers


def load_key(run_id, answers):
    """Random A/B order per ticket - created once per run, then reused."""
    if KEY_FILE.exists():
        key = json.loads(KEY_FILE.read_text())
        if key["run_id"] == run_id:
            return key
    rng = random.Random()
    order = {}
    for tid in sum(BATCHES, []):
        models = sorted(answers[tid])
        rng.shuffle(models)
        order[tid] = {"A": models[0], "B": models[1]}
    key = {"run_id": run_id, "order": order}
    KEY_FILE.write_text(json.dumps(key, indent=2))
    return key


def show(batch_no):
    run_id, answers = latest_answers()
    key = load_key(run_id, answers)
    tickets = {t["id"]: t["ticket"] for t in json.loads(TICKETS_FILE.read_text())}
    print(RUBRIC)
    for tid in BATCHES[batch_no - 1]:
        print(f"\n{'=' * 70}\n{tid}: {tickets[tid]}\n")
        for letter in ("A", "B"):
            a = answers[tid][key["order"][tid][letter]]
            print(f"--- Answer {letter} ---")
            print(f"Summary: {a['summary']}")
            print("Action items:")
            for item in a["action_items"]:
                print(f"  - {item}")
            print()


def record(tid, a_summary, a_actions, b_summary, b_actions):
    run_id, answers = latest_answers()
    key = load_key(run_id, answers)
    scores = json.loads(SCORES_FILE.read_text()) if SCORES_FILE.exists() else []
    scores = [s for s in scores if not (s["run_id"] == run_id and s["ticket_id"] == tid)]  # re-score replaces
    for letter, summary, actions in (("A", a_summary, a_actions), ("B", b_summary, b_actions)):
        if not all(v in (1, 2, 3) for v in (summary, actions)):
            raise SystemExit("Scores must be 1, 2 or 3.")
        scores.append({"run_id": run_id, "ticket_id": tid, "model": key["order"][tid][letter],
                       "summary": summary, "action_items": actions})
    SCORES_FILE.write_text(json.dumps(scores, indent=2))
    done = len({s["ticket_id"] for s in scores if s["run_id"] == run_id})
    print(f"Recorded {tid}. {done}/{len(sum(BATCHES, []))} tickets scored.")


def reveal():
    key = json.loads(KEY_FILE.read_text())
    for tid, order in key["order"].items():
        print(f"{tid}: A = {order['A']}, B = {order['B']}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("show")
    s.add_argument("batch", type=int, choices=range(1, len(BATCHES) + 1))
    r = sub.add_parser("record")
    r.add_argument("ticket_id")
    r.add_argument("scores", type=int, nargs=4, help="A summary, A actions, B summary, B actions")
    sub.add_parser("reveal")
    args = parser.parse_args()

    if args.command == "show":
        show(args.batch)
    elif args.command == "record":
        record(args.ticket_id, *args.scores)
    else:
        reveal()


if __name__ == "__main__":
    main()
