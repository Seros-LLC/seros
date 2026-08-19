"""Data model for the slice. Every tenant-owned table extends TenantModel."""
from __future__ import annotations

from django.db import models

from .tenancy import TenantModel


class Workspace(models.Model):
    """The tenant root. Not itself tenant-owned."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.slug


class Member(TenantModel):
    """A real person in a workspace. Only a Member may confirm (ADR 0002 rule 3)."""

    ROLES = [("admin", "admin"), ("member", "member"), ("viewer", "viewer")]
    external_id = models.CharField(max_length=64)
    display_name = models.CharField(max_length=200)
    role = models.CharField(max_length=16, choices=ROLES, default="member")
    is_service_account = models.BooleanField(default=False)

    class Meta(TenantModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="member_tenant_key"),
            models.UniqueConstraint(
                fields=["workspace", "external_id"], name="member_unique_external"
            ),
        ]

    def can_confirm(self) -> bool:
        return self.role in {"admin", "member"} and not self.is_service_account


class SourceMessage(TenantModel):
    """Ingest idempotency key: (workspace, channel_id, slack_ts)."""

    channel_id = models.CharField(max_length=64)
    slack_ts = models.CharField(max_length=32)
    author_external_id = models.CharField(max_length=64)
    text = models.TextField()
    permalink = models.URLField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="srcmsg_tenant_key"),
            models.UniqueConstraint(
                fields=["workspace", "channel_id", "slack_ts"], name="srcmsg_idempotent"
            ),
        ]


class Draft(TenantModel):
    """A proposed task. Nothing here has touched the tracker."""

    STATUS = [
        ("pending", "pending"),
        ("confirmed", "confirmed"),
        ("rejected", "rejected"),
    ]
    source_message = models.ForeignKey(SourceMessage, on_delete=models.CASCADE, related_name="drafts")
    title = models.CharField(max_length=300)
    outcome = models.TextField()
    proposed_owner = models.CharField(max_length=200, blank=True)
    due_date = models.DateField(null=True, blank=True)
    source_permalink = models.URLField()
    status = models.CharField(max_length=16, choices=STATUS, default="pending")
    prompt_version = models.CharField(max_length=64)
    confidence = models.FloatField(default=0.0)
    tracker_task_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="draft_tenant_key"),
            # Draft idempotency: one draft per source message per prompt version.
            models.UniqueConstraint(
                fields=["workspace", "source_message", "prompt_version"],
                name="draft_idempotent",
            ),
        ]


class Confirmation(TenantModel):
    """The human act. Idempotency key: (draft, member)."""

    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name="confirmations")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="confirmations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="confirmation_tenant_key"),
            models.UniqueConstraint(fields=["draft", "member"], name="confirmation_idempotent"),
        ]


class TrackerTask(TenantModel):
    """Proof that a write happened. confirmation is required and unique (ADR 0002 rule 2)."""

    confirmation = models.OneToOneField(
        Confirmation, on_delete=models.PROTECT, related_name="tracker_task"
    )
    idempotency_key = models.CharField(max_length=100)
    external_task_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantModel.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="trackertask_tenant_key"),
            models.UniqueConstraint(
                fields=["workspace", "idempotency_key"], name="trackertask_idempotent"
            ),
        ]


class AuditEvent(TenantModel):
    """One row per state change."""

    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    actor = models.CharField(max_length=100)
    at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # content-free by convention and by test

    class Meta(TenantModel.Meta):
        abstract = False
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="audit_tenant_key")
        ]


class ActionMeter(TenantModel):
    """One row per model call, including failures (ADR 0004 rule 4)."""

    purpose = models.CharField(max_length=32)
    tier = models.CharField(max_length=16)
    model_id = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=64)
    provider = models.CharField(max_length=64)
    tokens_in = models.IntegerField(default=0)
    tokens_out = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    cost_micros = models.IntegerField(default=0)
    outcome = models.CharField(max_length=32)  # ok|invalid_output|provider_error|timeout|budget_blocked|credential_error
    at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantModel.Meta):
        abstract = False
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["workspace", "id"], name="meter_tenant_key")
        ]
