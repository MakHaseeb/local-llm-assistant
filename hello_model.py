"""Step 1: send one prompt to a local model and measure how fast it answers.

Run:  .venv/bin/python hello_model.py              (uses llama3.2:3b)
      .venv/bin/python hello_model.py phi4-mini    (any model you've pulled)
"""
import sys
import time

import ollama

MODEL = sys.argv[1] if len(sys.argv) > 1 else "llama3.2:3b"
PROMPT = "In two sentences, why might a company run an AI model locally instead of using a cloud API?"

start = time.perf_counter()
first_token_at = None

# stream=True means words arrive one at a time, so we can time the first one.
stream = ollama.chat(model=MODEL, messages=[{"role": "user", "content": PROMPT}], stream=True)
for chunk in stream:
    if first_token_at is None and chunk.message.content:
        first_token_at = time.perf_counter()
    print(chunk.message.content, end="", flush=True)
    if chunk.done:
        stats = chunk  # the last chunk carries Ollama's own timing numbers
end = time.perf_counter()

NS = 1e9  # Ollama reports durations in nanoseconds
print("\n\n--- measurements ---")
print(f"time to first token : {first_token_at - start:.2f} s   (our stopwatch)")
print(f"total latency       : {end - start:.2f} s   (our stopwatch)")
print(f"model load time     : {stats.load_duration / NS:.2f} s   (Ollama; large = cold start)")
print(f"tokens generated    : {stats.eval_count}")
print(f"tokens per second   : {stats.eval_count / (stats.eval_duration / NS):.1f}   (Ollama)")
