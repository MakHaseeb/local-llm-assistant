"""Phase 2: how much do answers change between runs, at temperature 0 vs 0.7?

Temperature controls randomness. At 0 the model always picks its most likely
next word; at 0.7 it sometimes picks a less likely one. Each ticket marked
"temperature_subset" in data/eval_tickets.json is triaged several times at
each temperature.

There is deliberately NO fixed seed here: a fixed seed would make even 0.7
repeat itself exactly, and there'd be nothing to measure.

Every run is appended to results/temperature.jsonl (raw data first);
summarize_temperature.py turns it into tables.

Run:  .venv/bin/python temperature_test.py
      .venv/bin/python temperature_test.py --models llama3.2:3b --repeats 2 --limit 1   (quick test)
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from llm_client import unload
from prompts import TRIAGE_PROMPT_VERSION
from triage import triage

TICKETS_FILE = Path("data/eval_tickets.json")
RESULTS_FILE = Path("results/temperature.jsonl")
TEMPERATURES = (0.0, 0.7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["llama3.2:3b", "phi4-mini"])
    parser.add_argument("--repeats", type=int, default=5, help="runs per ticket per temperature")
    parser.add_argument("--limit", type=int, help="only use the first N subset tickets")
    args = parser.parse_args()

    tickets = [t for t in json.loads(TICKETS_FILE.read_text()) if t.get("temperature_subset")]
    tickets = tickets[:args.limit] if args.limit else tickets
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"run_id {run_id}: {len(args.models)} model(s), {len(tickets)} tickets, "
          f"temperatures {TEMPERATURES}, {args.repeats} repeats, prompt {TRIAGE_PROMPT_VERSION}")

    with RESULTS_FILE.open("a") as out:
        for model in args.models:
            print(f"\n== {model} ==")
            for t in tickets:
                for temperature in TEMPERATURES:
                    for i in range(1, args.repeats + 1):
                        o = triage(t["ticket"], model, temperature=temperature)
                        row = {
                            "run_id": run_id, "prompt_version": TRIAGE_PROMPT_VERSION,
                            "model": model, "ticket_id": t["id"], "temperature": temperature,
                            "repeat": i, "ok": o.ok, "attempts": o.attempts,
                            "answer": o.triage.model_dump() if o.ok else None,
                            "expected": t["expected"], "total_s": o.total_s,
                        }
                        out.write(json.dumps(row) + "\n")
                        out.flush()  # save each run immediately
                        labels = (f"{o.triage.category}/{o.triage.priority}/{o.triage.sentiment}"
                                  if o.ok else "FAILED")
                        print(f"  {t['id']} temp {temperature} #{i}  {labels:30} "
                              f"attempts={o.attempts} ({o.total_s:.1f}s)", flush=True)
            unload(model)  # free memory before the next model loads

    print(f"\nSaved to {RESULTS_FILE} (run_id {run_id})")


if __name__ == "__main__":
    main()
