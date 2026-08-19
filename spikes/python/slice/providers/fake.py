"""Deterministic offline provider.

This is what the tests and the smoke run use. It never touches the network and needs
no API key, so the whole spike runs on an aeroplane (TESTING-STRATEGY section 1).

The detection heuristic is a stand-in for a cheap-tier classifier: it exists so the
evaluation harness has something with non-trivial precision/recall to score.
"""
from __future__ import annotations

import json
import re

from .base import CompletionRequest, ModelProvider, RawCompletion

COMMIT_CUES = [
    r"\bi'?ll\b", r"\bi will\b", r"\bi'?m going to\b", r"\bi can have\b",
    r"\bwill (?:send|have|write|ship|do|get|prepare|review|fix)\b",
    r"\bon it\b", r"\bi'?ve got it\b", r"\btaking (?:this|that) on\b",
]
REQUEST_CUES = [
    r"\bcan you\b", r"\bcould you\b", r"\bplease (?:send|do|review|fix|update)\b",
    r"\bwould you mind\b",
]
DECISION_CUES = [
    r"\bwe(?:'| a)re going with\b", r"\bdecision:\b", r"\bwe'?ve decided\b",
    r"\blet'?s go with\b",
]
NEGATIVE_CUES = [
    r"\bshould probably\b", r"\bwe should\b", r"\bmaybe we\b", r"\bif we ever\b",
    r"\bwould have\b", r"\bhypothetically\b", r"\bjoking\b", r"\b(?:lol|haha)\b",
    r"\bsaid (?:he|she|they)'?d\b", r"\bnice to have\b", r"\bwhat if\b",
    r"\byesterday i (?:sent|did|finished)\b", r"\bi (?:sent|did|finished) .* (?:yesterday|last week)\b",
]
DUE_RE = re.compile(
    r"\b(?:by|before|on)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"tomorrow|today|eod|end of (?:day|week)|\d{4}-\d{2}-\d{2})\b",
    re.I,
)
DAY_OFFSET = {
    "monday": 3, "tuesday": 4, "wednesday": 5, "thursday": 6, "friday": 7,
    "saturday": 8, "sunday": 9, "tomorrow": 1, "today": 0, "eod": 0,
    "end of day": 0, "end of week": 5,
}


def _hits(patterns, text):
    return [p for p in patterns if re.search(p, text, re.I)]


def classify(text: str) -> tuple[bool, str, float, str]:
    """Returns (is_candidate, type, confidence, reason). Pure, deterministic."""
    negatives = _hits(NEGATIVE_CUES, text)
    if negatives:
        return False, "none", 0.9, "hedged, hypothetical, past tense or joking"
    for cues, kind, conf in (
        (COMMIT_CUES, "commitment", 0.92),
        (REQUEST_CUES, "request", 0.78),
        (DECISION_CUES, "decision", 0.7),
    ):
        if _hits(cues, text):
            bump = 0.05 if DUE_RE.search(text) else 0.0
            return True, kind, min(conf + bump, 0.99), f"matched {kind} cue"
    return False, "none", 0.8, "no actionable cue"


class FakeProvider(ModelProvider):
    name = "fake"

    def _invoke(self, request: CompletionRequest) -> RawCompletion:
        if request.purpose == "detect":
            payload = self._detect(request)
        elif request.purpose == "draft":
            payload = self._draft(request)
        else:  # pragma: no cover - only two purposes in the slice
            raise NotImplementedError(request.purpose)
        text = json.dumps(payload)
        return RawCompletion(
            text=text,
            tokens_in=sum(len(m["content"]) for m in request.messages) // 4,
            tokens_out=len(text) // 4,
            model_id="fake-" + request.tier + "-1",
        )

    def _detect(self, request: CompletionRequest) -> dict:
        batch = json.loads(request.messages[-1]["content"])
        results = []
        for item in batch["messages"]:
            is_candidate, kind, confidence, reason = classify(item["text"])
            results.append(
                {
                    "message_id": item["id"],
                    "is_candidate": is_candidate,
                    "type": kind,
                    "confidence": confidence,
                    "reason": reason,
                }
            )
        return {"results": results}

    def _draft(self, request: CompletionRequest) -> dict:
        from datetime import date, timedelta

        payload = json.loads(request.messages[-1]["content"])
        text = payload["text"].strip()
        author = payload.get("author", "")
        title = re.sub(r"\s+", " ", text)[:120]
        title = title[0].upper() + title[1:] if title else "Follow up"
        due = None
        m = DUE_RE.search(text)
        if m:
            offset = DAY_OFFSET.get(m.group(1).lower())
            if offset is not None:
                due = (date(2026, 1, 5) + timedelta(days=offset)).isoformat()
        owner = author or None
        for cues in (REQUEST_CUES,):
            if _hits(cues, text):
                mention = re.search(r"@([a-z0-9._-]+)", text, re.I)
                owner = mention.group(1) if mention else None
        return {
            "title": title,
            "outcome": f"Close the loop on: {title}",
            "proposed_owner": owner,
            "due_date": due,
            "confidence": 0.8,
        }
