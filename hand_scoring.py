"""Phase 3: blind head-to-head judging of summaries and action items.

For each chosen ticket, both models' answers are shown as "Answer A" and
"Answer B" in a random order, so the judge can't favour a model by name.
The judge picks the better summary and the better action items (A, B or tie).
The A/B order is saved in results/hand_scoring_key.json and only used when
recording picks.

Run:  .venv/bin/python hand_scoring.py show 1                          (print batch 1 of 3)
      .venv/bin/python hand_scoring.py record t01 A tie "reason..."    (summary pick, action pick)
      .venv/bin/python hand_scoring.py reveal                          (who was A and B)
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

GUIDE = """For each ticket, pick the better SUMMARY and the better ACTION ITEMS: A, B, or tie.
  Better summary:      accurate and complete - the main issue and key details, nothing made up
  Better action items: the right steps, specific, nothing the customer already tried, nothing made up"""


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
    print(GUIDE)
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


def record(tid, summary_pick, actions_pick, reason):
    run_id, answers = latest_answers()
    key = load_key(run_id, answers)
    order = key["order"][tid]

    def winner(pick):
        pick = pick.upper()
        if pick == "TIE":
            return "tie"
        if pick not in ("A", "B"):
            raise SystemExit("Each pick must be A, B or tie.")
        return order[pick]

    scores = json.loads(SCORES_FILE.read_text()) if SCORES_FILE.exists() else []
    scores = [s for s in scores if not (s["run_id"] == run_id and s["ticket_id"] == tid)]  # re-judging replaces
    scores.append({"run_id": run_id, "ticket_id": tid, "summary": winner(summary_pick),
                   "action_items": winner(actions_pick), "reason": reason})
    SCORES_FILE.write_text(json.dumps(scores, indent=2))
    done = len({s["ticket_id"] for s in scores if s["run_id"] == run_id})
    print(f"Recorded {tid}. {done}/{len(sum(BATCHES, []))} tickets judged.")


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
    r.add_argument("summary_pick", help="A, B or tie")
    r.add_argument("actions_pick", help="A, B or tie")
    r.add_argument("reason", nargs="?", default="")
    sub.add_parser("reveal")
    args = parser.parse_args()

    if args.command == "show":
        show(args.batch)
    elif args.command == "record":
        record(args.ticket_id, args.summary_pick, args.actions_pick, args.reason)
    else:
        reveal()


if __name__ == "__main__":
    main()
