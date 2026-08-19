"""Providers that fail on purpose. Used only by the 2am test (manage.py twoam)."""
from __future__ import annotations

import time

from .base import CompletionRequest, ProviderTimeout, RawCompletion
from .fake import FakeProvider


class TimingOutProvider(FakeProvider):
    name = "fake-timeout"

    def _invoke(self, request: CompletionRequest) -> RawCompletion:
        time.sleep(min(request.timeout_s, 0.05))
        raise ProviderTimeout(
            f"read timed out after {request.timeout_s}s calling tier={request.tier}"
        )


class MalformedProvider(FakeProvider):
    name = "fake-malformed"

    def _invoke(self, request: CompletionRequest) -> RawCompletion:
        # Plausibly wrong: right shape, wrong types, confidence out of range.
        bad = (
            '{"results": [{"message_id": 12, "is_candidate": "yes", '
            '"type": "vibes", "confidence": 4.5}]}'
        )
        return RawCompletion(text=bad, tokens_in=120, tokens_out=40, model_id="fake-cheap-1")
