"""Phase 2: turn a support ticket into validated JSON, with one retry.

The flow:
  1. Ask the model for JSON. By default Ollama also forces the reply into the
     schema's shape ("constrained generation"); --no-schema turns that off.
  2. Check the reply with Pydantic (schemas.py).
  3. If it fails, ask once more, showing the model its own reply and the exact
     error message.
  4. If that fails too, return a clean failure instead of crashing.

Run:  .venv/bin/python triage.py "I was charged twice for my subscription this month."
      .venv/bin/python triage.py --model phi4-mini --no-schema "..."
"""
import argparse
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import ValidationError

from llm_client import generate
from prompts import build_triage_prompt
from schemas import TicketTriage

MAX_ATTEMPTS = 2  # the first try + one retry


@dataclass
class TriageOutcome:
    ok: bool
    triage: Optional[TicketTriage]
    attempts: int
    replies: List[str] = field(default_factory=list)  # every raw reply, in order
    errors: List[str] = field(default_factory=list)   # why each failed reply was rejected
    total_s: float = 0.0                              # time across all attempts


def describe_errors(e: ValidationError) -> str:
    """Turn Pydantic's error list into short lines a model (or person) can act on."""
    lines = []
    for err in e.errors():
        where = ".".join(str(part) for part in err["loc"]) or "(whole reply)"
        lines.append(f"- {where}: {err['msg']}")
    return "\n".join(lines)


def build_retry_prompt(ticket: str, bad_reply: str, errors: str) -> str:
    # Same instructions + ticket as the first try (so the cache still helps),
    # then the rejected reply and exactly what was wrong with it.
    return (f"{build_triage_prompt(ticket)}\n\n"
            f"Your previous reply was:\n{bad_reply}\n\n"
            f"It was rejected for these reasons:\n{errors}\n\n"
            f"Reply again with corrected JSON only.")


def triage(ticket: str, model: str = "llama3.2:3b", constrained: bool = True,
           temperature: float = 0.0, max_tokens: int = 500) -> TriageOutcome:
    schema = TicketTriage.model_json_schema() if constrained else None
    outcome = TriageOutcome(ok=False, triage=None, attempts=0)
    prompt = build_triage_prompt(ticket)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = generate(model, prompt, temperature=temperature,
                          max_tokens=max_tokens, schema=schema)
        outcome.attempts = attempt
        outcome.total_s += result.total_s
        outcome.replies.append(result.text)
        try:
            outcome.triage = TicketTriage.model_validate_json(result.text)
            outcome.ok = True
            return outcome
        except ValidationError as e:
            errors = describe_errors(e)
            outcome.errors.append(errors)
            prompt = build_retry_prompt(ticket, result.text, errors)

    return outcome  # both attempts failed: ok=False, with every reply and error kept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket", help="the support ticket text")
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--no-schema", action="store_true",
                        help="don't let Ollama force the JSON shape (instructions only)")
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    outcome = triage(args.ticket, args.model, constrained=not args.no_schema,
                     temperature=args.temperature)

    for i, errors in enumerate(outcome.errors, start=1):
        print(f"Attempt {i} rejected:\n{errors}\n")
    if outcome.ok:
        print(outcome.triage.model_dump_json(indent=2))
        print(f"\n({args.model}, {outcome.attempts} attempt(s), {outcome.total_s:.1f}s)")
    else:
        print(f"Could not get a valid answer after {outcome.attempts} attempts. "
              f"The ticket needs a human. Last reply was:\n{outcome.replies[-1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
