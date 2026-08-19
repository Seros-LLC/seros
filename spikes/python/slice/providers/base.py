"""The provider abstraction (ADR 0004).

One operation, ``complete``. Budget check, metering, timeout, bounded retry and schema
validation all live here, so no call site can skip them. No provider SDK type escapes
this package.
"""
from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from django.conf import settings
from pydantic import BaseModel, ValidationError

from ..logging_ext import event
from ..models import ActionMeter

log = logging.getLogger("slice.provider")
T = TypeVar("T", bound=BaseModel)


class ProviderError(Exception):
    outcome = "provider_error"


class ProviderCredentialError(ProviderError):
    outcome = "credential_error"


class ProviderTimeout(ProviderError):
    outcome = "timeout"


class SchemaValidationError(ProviderError):
    outcome = "invalid_output"


class BudgetExceeded(ProviderError):
    outcome = "budget_blocked"


@dataclass(frozen=True)
class CompletionRequest:
    prompt_version_id: str
    messages: list[dict[str, str]]
    response_schema: type[BaseModel]
    tier: str
    max_input_tokens: int
    max_output_tokens: int
    timeout_s: float
    workspace_id: int
    purpose: str  # detect | draft | route


@dataclass(frozen=True)
class CompletionResult:
    value: BaseModel
    model_id: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    outcome: str


@dataclass(frozen=True)
class RawCompletion:
    text: str
    tokens_in: int
    tokens_out: int
    model_id: str


class ModelProvider(ABC):
    name: str = "abstract"
    max_attempts: int = 2

    @abstractmethod
    def _invoke(self, request: CompletionRequest) -> RawCompletion:
        """Do the vendor-specific thing. Raise ProviderError subclasses only."""

    # -- the only public entry point ---------------------------------------
    def complete(self, request: CompletionRequest) -> CompletionResult:
        model_id = settings.MODEL_TIERS[request.tier]["model_id"]
        started = time.monotonic()

        if not self._budget_allows(request):
            self._meter(request, model_id, 0, 0, 0, "budget_blocked")
            event(log, logging.ERROR, "provider.budget_blocked",
                  workspace_id=request.workspace_id, purpose=request.purpose, tier=request.tier)
            raise BudgetExceeded(f"workspace {request.workspace_id} is over its action budget")

        last_exc: ProviderError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = self._invoke(request)
            except ProviderError as exc:
                last_exc = exc
                event(log, logging.ERROR, "provider.call_failed",
                      provider=self.name, model=model_id, purpose=request.purpose,
                      prompt_version=request.prompt_version_id, attempt=attempt,
                      of_attempts=self.max_attempts, error_class=type(exc).__name__,
                      outcome=exc.outcome, detail=str(exc),
                      timeout_s=request.timeout_s, workspace_id=request.workspace_id)
                if isinstance(exc, ProviderCredentialError):
                    break  # retrying a bad credential is pointless and noisy
                continue

            latency_ms = int((time.monotonic() - started) * 1000)
            try:
                value = self._validate(raw.text, request.response_schema)
            except SchemaValidationError as exc:
                last_exc = exc
                self._meter(request, raw.model_id, raw.tokens_in, raw.tokens_out,
                            latency_ms, "invalid_output")
                event(log, logging.ERROR, "provider.invalid_output",
                      provider=self.name, model=raw.model_id, purpose=request.purpose,
                      prompt_version=request.prompt_version_id, attempt=attempt,
                      schema=request.response_schema.__name__,
                      validation_errors=str(exc)[:400],
                      raw_output_head=raw.text[:120],
                      workspace_id=request.workspace_id)
                continue

            self._meter(request, raw.model_id, raw.tokens_in, raw.tokens_out, latency_ms, "ok")
            event(log, logging.INFO, "provider.ok", provider=self.name, model=raw.model_id,
                  purpose=request.purpose, prompt_version=request.prompt_version_id,
                  tokens_in=raw.tokens_in, tokens_out=raw.tokens_out, latency_ms=latency_ms,
                  workspace_id=request.workspace_id)
            return CompletionResult(
                value, raw.model_id, raw.tokens_in, raw.tokens_out, latency_ms, "ok"
            )

        latency_ms = int((time.monotonic() - started) * 1000)
        assert last_exc is not None
        if last_exc.outcome != "invalid_output":  # invalid_output already metered per attempt
            self._meter(request, model_id, 0, 0, latency_ms, last_exc.outcome)
        raise last_exc

    # -- internals ---------------------------------------------------------
    def _validate(self, text: str, schema: type[BaseModel]) -> BaseModel:
        try:
            payload: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SchemaValidationError(f"response was not JSON: {exc}") from exc
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise SchemaValidationError(exc.json(include_url=False)) from exc

    def _budget_allows(self, request: CompletionRequest) -> bool:
        used = ActionMeter.tenant.scoped_to(request.workspace_id).count()
        return used < settings.WORKSPACE_ACTION_BUDGET

    def _meter(self, request, model_id, tokens_in, tokens_out, latency_ms, outcome) -> None:
        prices = settings.MODEL_TIERS[request.tier]
        cost = (tokens_in / 1000) * prices["price_per_1k_in"] + (
            tokens_out / 1000
        ) * prices["price_per_1k_out"]
        ActionMeter.tenant.scoped_to(request.workspace_id).create(
            workspace_id=request.workspace_id,
            purpose=request.purpose,
            tier=request.tier,
            model_id=model_id,
            prompt_version=request.prompt_version_id,
            provider=self.name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_micros=int(cost * 1_000_000),
            outcome=outcome,
        )
