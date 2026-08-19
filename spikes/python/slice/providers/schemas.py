"""Structured outputs. A malformed response is a failed call, not a partial result."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    message_id: str
    is_candidate: bool
    type: Literal["commitment", "request", "decision", "none"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(max_length=200)


class DetectionBatch(BaseModel):
    results: list[DetectionItem]


class DraftProposal(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    outcome: str = Field(min_length=3)
    proposed_owner: str | None = None
    due_date: date | None = None
    confidence: float = Field(ge=0.0, le=1.0)
