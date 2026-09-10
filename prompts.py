"""Instructions for the triage assistant.

The JSON schema (schemas.py) controls the *shape* of the answer. These
instructions control the *meaning*: the model never sees the schema itself, so
this is where it learns what "urgent" or "account" actually means.

Bump the version whenever the wording changes, so results can be traced back
to the exact instructions that produced them.
"""
TRIAGE_PROMPT_VERSION = "v2"  # v2: tie-break rules for login bugs and multi-issue tickets

TRIAGE_INSTRUCTIONS = """You are a customer support triage assistant. Read the ticket and reply with JSON containing these fields:

category - pick exactly one:
  billing:   charges, invoices, payments, pricing, refunds
  technical: bugs, errors, crashes - anything that used to work and is now broken,
             including a login that fails because of a bug or an update
  account:   requests about access, users, invitations, passwords and settings,
             when nothing is broken
  shipping:  deliveries, tracking, orders in transit
  other:     anything else (sales questions, compliance, feedback)

  If the ticket raises several issues, use the category of the most serious one:
  money charged wrongly first, then something broken, then everything else.

priority - pick exactly one:
  urgent: the customer is blocked AND there is a deadline or business impact right now
  high:   something is broken or money is wrong, but no immediate deadline
  medium: a problem with a workaround, or a question that needs action
  low:    a general question, feedback, or request with nothing broken

sentiment - the customer's tone: negative, neutral, or positive

summary - one or two sentences, in your own words

action_items - the concrete steps the support team needs to take, one per item

Reply with the JSON only."""


def build_triage_prompt(ticket: str) -> str:
    # Instructions first, ticket last: the instructions are identical on every
    # request, so Ollama's cache can skip re-reading them (see Phase 1, finding 2).
    return f"{TRIAGE_INSTRUCTIONS}\n\nTicket:\n{ticket}"
