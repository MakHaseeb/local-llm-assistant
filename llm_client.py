"""The one place in this project that talks to Ollama.

Every other script (benchmark, JSON validation, model comparison) calls
generate() here, so every model and every phase is measured the same way.
"""
import time
from dataclasses import dataclass
from typing import Optional

import ollama

NS = 1e9  # Ollama reports durations in nanoseconds


@dataclass
class GenerationResult:
    model: str
    text: str
    ttft_s: float         # our stopwatch: request sent -> first word arrives
    total_s: float        # our stopwatch: request sent -> last word arrives
    load_s: float         # Ollama: time spent loading the model into memory (big = cold start)
    prompt_tokens: int    # how long the input was, in tokens
    prompt_eval_s: float  # Ollama: time spent reading the input
    output_tokens: int    # how long the answer was, in tokens
    eval_s: float         # Ollama: time spent writing the answer
    tokens_per_s: float   # output_tokens / eval_s


def generate(model: str, prompt: str, temperature: float = 0.0,
             seed: Optional[int] = None, max_tokens: Optional[int] = None,
             show: bool = False) -> GenerationResult:
    """Send one prompt, stream the reply, and return the text plus timings."""
    options = {"temperature": temperature}
    if seed is not None:
        options["seed"] = seed
    if max_tokens is not None:
        options["num_predict"] = max_tokens

    start = time.perf_counter()
    first_token_at = None
    pieces = []

    stream = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}],
                         options=options, stream=True)
    for chunk in stream:
        if first_token_at is None and chunk.message.content:
            first_token_at = time.perf_counter()
        pieces.append(chunk.message.content)
        if show:
            print(chunk.message.content, end="", flush=True)
        if chunk.done:
            stats = chunk  # the last chunk carries Ollama's own timing numbers
    end = time.perf_counter()

    return GenerationResult(
        model=model,
        text="".join(pieces),
        ttft_s=(first_token_at or end) - start,
        total_s=end - start,
        load_s=stats.load_duration / NS,
        prompt_tokens=stats.prompt_eval_count or 0,
        prompt_eval_s=(stats.prompt_eval_duration or 0) / NS,
        output_tokens=stats.eval_count,
        eval_s=stats.eval_duration / NS,
        tokens_per_s=stats.eval_count / (stats.eval_duration / NS),
    )


def unload(model: str) -> None:
    """Remove the model from memory, so the next request is a true cold start."""
    ollama.generate(model=model, keep_alive=0)


def memory_gb(model: str) -> Optional[float]:
    """How much memory the model uses while loaded (None if it isn't loaded)."""
    for m in ollama.ps().models:
        if m.model.startswith(model):
            return m.size / 1e9
    return None
