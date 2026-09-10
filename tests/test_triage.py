"""Tests for the retry logic in triage.py - no model or Ollama needed.

A fake generate() returns scripted replies, so we can check exactly what
happens when the model gets it right, wrong-then-right, or wrong twice.
(With a real model we can't choose when it fails.)

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
import json
import unittest
from unittest.mock import patch

import triage
from llm_client import GenerationResult

GOOD = json.dumps({
    "category": "billing", "priority": "high", "sentiment": "negative",
    "summary": "Customer was charged twice for their subscription this month.",
    "action_items": ["Confirm the duplicate charge", "Refund the second charge"],
})
BAD_CATEGORY = GOOD.replace('"billing"', '"payments"')  # not one of the 5 categories
NOT_JSON = 'Sure! Here is the triage: {"category": "billing", ...'


def fake_replies(*texts):
    """Replace the real model with one that returns these replies, in order."""
    results = [GenerationResult(model="fake", text=t, ttft_s=0.0, total_s=1.0, load_s=0.0,
                                prompt_tokens=0, prompt_eval_s=0.0, output_tokens=0,
                                eval_s=1.0, tokens_per_s=0.0) for t in texts]
    return patch.object(triage, "generate", side_effect=results)


class TriageRetryTests(unittest.TestCase):

    def test_valid_first_time_needs_no_retry(self):
        with fake_replies(GOOD) as fake:
            out = triage.triage("ticket text")
        self.assertTrue(out.ok)
        self.assertEqual(out.triage.category, "billing")
        self.assertEqual(out.attempts, 1)
        self.assertEqual(fake.call_count, 1)

    def test_retry_fixes_an_invalid_reply(self):
        with fake_replies(BAD_CATEGORY, GOOD) as fake:
            out = triage.triage("ticket text")
        self.assertTrue(out.ok)
        self.assertEqual(out.attempts, 2)
        self.assertEqual(len(out.results), 2)      # timings kept for every attempt
        retry_prompt = fake.call_args_list[1].args[1]
        self.assertIn(BAD_CATEGORY, retry_prompt)  # the model is shown its own reply...
        self.assertIn("category", retry_prompt)    # ...and which field was wrong

    def test_unreadable_json_gets_a_plain_english_hint(self):
        with fake_replies(NOT_JSON, GOOD) as fake:
            out = triage.triage("ticket text")
        self.assertTrue(out.ok)
        retry_prompt = fake.call_args_list[1].args[1]
        self.assertIn(triage.JSON_HINT, retry_prompt)

    def test_field_errors_do_not_get_the_json_hint(self):
        with fake_replies(BAD_CATEGORY, GOOD) as fake:
            triage.triage("ticket text")
        retry_prompt = fake.call_args_list[1].args[1]
        self.assertNotIn(triage.JSON_HINT, retry_prompt)  # its own message is already clear

    def test_two_bad_replies_fail_gracefully(self):
        with fake_replies(NOT_JSON, BAD_CATEGORY) as fake:
            out = triage.triage("ticket text")
        self.assertFalse(out.ok)
        self.assertIsNone(out.triage)
        self.assertEqual(out.attempts, 2)
        self.assertEqual(len(out.errors), 2)  # a reason kept for each failure
        self.assertEqual(fake.call_count, 2)  # never a third try

    def test_no_schema_mode_sends_no_schema(self):
        with fake_replies(GOOD) as fake:
            triage.triage("ticket text", constrained=False)
        self.assertIsNone(fake.call_args.kwargs["schema"])

    def test_constrained_mode_sends_the_schema(self):
        with fake_replies(GOOD) as fake:
            triage.triage("ticket text")
        self.assertEqual(fake.call_args.kwargs["schema"]["title"], "TicketTriage")


if __name__ == "__main__":
    unittest.main()
