"""What a valid ticket-triage answer looks like.

Pydantic checks every answer the model gives against these rules. Anything that
doesn't match is rejected with an error message that says exactly what's wrong,
which the retry step can send back to the model.
"""
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["billing", "technical", "account", "shipping", "other"]
Priority = Literal["low", "medium", "high", "urgent"]
Sentiment = Literal["negative", "neutral", "positive"]


class TicketTriage(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject any field we didn't ask for

    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(min_length=10, max_length=400)
    action_items: List[str] = Field(min_length=1, max_length=8)
