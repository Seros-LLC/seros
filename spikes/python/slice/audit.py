from __future__ import annotations

import logging

from .logging_ext import event
from .models import AuditEvent

log = logging.getLogger("slice.audit")


def record(scope, entity, action: str, actor: str, **metadata) -> AuditEvent:
    """One audit row per state change. Metadata must be content-free."""
    row = scope.create(
        AuditEvent,
        entity_type=type(entity).__name__,
        entity_id=str(entity.pk),
        action=action,
        actor=actor,
        metadata=metadata,
    )
    event(
        log,
        logging.INFO,
        "audit",
        workspace=scope.workspace.slug,
        entity=row.entity_type,
        entity_id=row.entity_id,
        action=action,
        actor=actor,
    )
    return row
