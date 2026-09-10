"""Phase 3: run every model on the same 40 tickets.

Each ticket in data/eval_tickets.json is triaged ONCE per model, at
temperature 0 with the schema on. Phase 2 showed temperature 0 gives the
same answer every time, so repeats would add nothing.

Each model starts cold (unloaded), so the first ticket includes loading time.
That row is marked "cold" and left out of the speed numbers.

Raw rows go to results/comparison.jsonl; score_models.py turns them into tables.

Run:  .venv/bin/python compare_models.py
      .venv/bin/python compare_models.py --models llama3.2:3b --limit 2   (quick test)
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from llm_client import memory_gb, unload
from prompts import TRIAGE_PROMPT_VERSION
from triage import triage

TICKETS_FILE = Path("data/eval_tickets.json")
RESULTS_FILE = Path("results/comparison.jsonl")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["llama3.2:3b", "phi4-mini"])
    parser.add_argument("--limit", type=int, help="only use the first N tickets")
    args = parser.parse_args()

    tickets = json.loads(TICKETS_FILE.read_text())
    tickets = tickets[:args.limit] if args.limit else tickets
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"run_id {run_id}: {len(args.models)} model(s), {len(tickets)} tickets, "
          f"prompt {TRIAGE_PROMPT_VERSION}, temperature 0, schema on")

    with RESULTS_FILE.open("a") as out:
        for model in args.models:
            print(f"\n== {model} ==")
            unload(model)
            time.sleep(2)  # start cold, so the first ticket shows a real load
            for i, t in enumerate(tickets):
                o = triage(t["ticket"], model)
                eval_s = sum(r.eval_s for r in o.results)
                row = {
                    "run_id": run_id, "prompt_version": TRIAGE_PROMPT_VERSION,
                    "model": model, "ticket_id": t["id"], "cold": i == 0,
                    "ok": o.ok, "attempts": o.attempts,
                    "answer": o.triage.model_dump() if o.ok else None,
                    "expected": t["expected"],
                    "total_s": o.total_s,
                    "ttft_s": o.results[0].ttft_s,
                    "load_s": o.results[0].load_s,
                    "output_tokens": sum(r.output_tokens for r in o.results),
                    "tokens_per_s": sum(r.output_tokens for r in o.results) / eval_s,
                    "words_per_s": sum(len(r.text.split()) for r in o.results) / eval_s,
                    "memory_gb": memory_gb(model),
                }
                out.write(json.dumps(row) + "\n")
                out.flush()  # save each run immediately
                got = (f"{o.triage.category}/{o.triage.priority}/{o.triage.sentiment}"
                       if o.ok else "FAILED")
                exp = "/".join(t["expected"][k] for k in ("category", "priority", "sentiment"))
                print(f"  {t['id']}  {got:28} key {exp:28} attempts={o.attempts} "
                      f"({o.total_s:.1f}s)", flush=True)
            unload(model)  # free memory before the next model loads

    print(f"\nSaved to {RESULTS_FILE} (run_id {run_id})")


if __name__ == "__main__":
    main()
