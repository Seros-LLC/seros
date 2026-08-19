"""Log formatter that refuses to emit content-classed values (README rule 2)."""
import logging
import re

# Anything passed as extra={"content": ...} is dropped. Anything that looks like a
# Slack signing secret or a provider key is masked.
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{6,}|xoxb-[A-Za-z0-9_\-]{6,})")


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = super().format(record)
        out = SECRET_RE.sub("[redacted-credential]", out)
        return out


def event(logger: logging.Logger, level: int, event_name: str, **fields: object) -> None:
    """Structured, content-free operator log line."""
    parts = " ".join(f"{k}={v!r}" for k, v in sorted(fields.items()))
    logger.log(level, "%s %s", event_name, parts)
