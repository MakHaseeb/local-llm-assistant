"""Phase 1 benchmark: how fast is each model on this machine?

For each model:
  1. Cold runs   - unload the model before each run, so every run pays the loading cost.
  2. Warm runs   - model already in memory, but every run starts with a unique ticket
                   number, so Ollama can't reuse its notes from the last run (its
                   "KV cache"). This is what a real, new ticket costs.
  3. Cached runs - the exact same text sent again, so Ollama can skip re-reading it.
                   Shows how much the cache saves (useful for fixed instructions later).

Every single run is appended as one line to results/benchmark.jsonl.
Raw data first - summarize.py turns it into tables later.

Run:  .venv/bin/python benchmark.py
      .venv/bin/python benchmark.py --models llama3.2:3b --repeats 1 --cold-runs 1   (quick test)
"""
import argparse
import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from llm_client import generate, memory_gb, unload

PROMPTS_FILE = Path("prompts/benchmark_prompts.json")
RESULTS_FILE = Path("results/benchmark.jsonl")

# Same settings for every run, so differences come from the model, not the settings.
TEMPERATURE = 0.0
SEED = 42
MAX_TOKENS = 200


def record(out, run_id, result, run_type, prompt_id, repeat):
    row = {"run_id": run_id, "run_type": run_type, "prompt_id": prompt_id,
           "repeat": repeat, "memory_gb": memory_gb(result.model), **asdict(result)}
    out.write(json.dumps(row) + "\n")
    out.flush()  # save each run immediately, so a crash doesn't lose earlier runs
    print(f"  {run_type:6} {prompt_id:18} #{repeat}  ttft {result.ttft_s:6.2f}s"
          f"  total {result.total_s:6.2f}s  {result.tokens_per_s:5.1f} tok/s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["llama3.2:3b", "phi4-mini"])
    parser.add_argument("--repeats", type=int, default=5, help="warm runs per prompt")
    parser.add_argument("--cold-runs", type=int, default=3)
    parser.add_argument("--cached-repeats", type=int, default=3, help="cached runs per prompt")
    args = parser.parse_args()

    prompts = json.loads(PROMPTS_FILE.read_text())
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"run_id {run_id}: {len(args.models)} model(s), {len(prompts)} prompts, "
          f"{args.cold_runs} cold + {args.repeats} warm + {args.cached_repeats} cached repeats")
    ticket_no = 1000

    with RESULTS_FILE.open("a") as out:
        for model in args.models:
            print(f"\n== {model} ==")
            first = prompts[0]
            for i in range(1, args.cold_runs + 1):
                unload(model)
                time.sleep(2)  # give memory a moment to settle
                result = generate(model, first["prompt"], TEMPERATURE, SEED, MAX_TOKENS)
                record(out, run_id, result, "cold", first["id"], i)

            for prompt in prompts:
                # Warm: a different first line each time, so the cache can't be reused.
                for i in range(1, args.repeats + 1):
                    ticket_no += 1
                    text = f"Ticket #{ticket_no}\n{prompt['prompt']}"
                    result = generate(model, text, TEMPERATURE, SEED, MAX_TOKENS)
                    record(out, run_id, result, "warm", prompt["id"], i)

                # Cached: identical text. The first send only fills the cache (not recorded).
                generate(model, prompt["prompt"], TEMPERATURE, SEED, MAX_TOKENS)
                for i in range(1, args.cached_repeats + 1):
                    result = generate(model, prompt["prompt"], TEMPERATURE, SEED, MAX_TOKENS)
                    record(out, run_id, result, "cached", prompt["id"], i)

            unload(model)  # free memory before the next model loads

    print(f"\nSaved to {RESULTS_FILE} (run_id {run_id})")


if __name__ == "__main__":
    main()
