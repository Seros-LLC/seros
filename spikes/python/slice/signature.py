"""Slack v0 request signing. Nothing here knows about Django."""
from __future__ import annotations

import hashlib
import hmac
import time


class SignatureError(Exception):
    """Base class for every reason a request is rejected."""


class MissingSignature(SignatureError):
    pass


class StaleTimestamp(SignatureError):
    pass


class BadSignature(SignatureError):
    pass


def sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    basestring = b"v0:" + timestamp.encode() + b":" + raw_body
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def verify(
    secret: str,
    timestamp: str | None,
    signature: str | None,
    raw_body: bytes,
    max_skew_seconds: int = 300,
    now: float | None = None,
) -> None:
    """Raise a SignatureError subclass, or return None."""
    if not timestamp or not signature:
        raise MissingSignature("missing X-Slack-Request-Timestamp or X-Slack-Signature")
    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise StaleTimestamp("non-integer timestamp") from exc
    now = time.time() if now is None else now
    if abs(now - ts) > max_skew_seconds:
        raise StaleTimestamp(f"timestamp skew {int(now - ts)}s exceeds {max_skew_seconds}s")
    expected = sign(secret, timestamp, raw_body)
    if not hmac.compare_digest(expected, signature):
        raise BadSignature("hmac mismatch")
