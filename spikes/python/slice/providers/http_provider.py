"""Thin, deliberately unexercised real-provider adapter.

It exists to prove the interface is implementable against a real vendor and to give
the 2am test something to fail with. Nothing in the test suite or the smoke run calls
it with a real key, and it makes no network call unless one is configured.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import (
    CompletionRequest,
    ModelProvider,
    ProviderCredentialError,
    ProviderError,
    ProviderTimeout,
    RawCompletion,
)


class HttpProvider(ModelProvider):
    """One vendor, one HTTP call, no SDK types leaking out of this module."""

    name = "http"
    base_url = os.environ.get("SEROS_PROVIDER_URL", "https://api.example-provider.invalid/v1/messages")

    def _invoke(self, request: CompletionRequest) -> RawCompletion:
        api_key = os.environ.get("SEROS_PROVIDER_API_KEY", "")
        if not api_key:
            raise ProviderCredentialError(
                "SEROS_PROVIDER_API_KEY is empty; refusing to call the provider"
            )
        body = json.dumps(
            {
                "model": request.tier,
                "messages": request.messages,
                "max_tokens": request.max_output_tokens,
                "response_format": {
                    "type": "json_schema",
                    "schema": request.response_schema.model_json_schema(),
                },
            }
        ).encode()
        req = urllib.request.Request(
            self.base_url,
            data=body,
            headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout_s) as resp:
                payload = json.loads(resp.read())
        except TimeoutError as exc:
            raise ProviderTimeout(f"provider did not answer within {request.timeout_s}s") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderCredentialError(f"provider rejected credential: HTTP {exc.code}") from exc
            raise ProviderError(f"provider HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"provider unreachable: {exc.reason}") from exc
        return RawCompletion(
            text=payload["content"][0]["text"],
            tokens_in=payload.get("usage", {}).get("input_tokens", 0),
            tokens_out=payload.get("usage", {}).get("output_tokens", 0),
            model_id=payload.get("model", request.tier),
        )
