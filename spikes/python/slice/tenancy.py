"""Structural tenant scoping.

ADR 0003 / ARCHITECTURE.md section 8 require that workspace scoping is *structural*,
not a convention. Three mechanisms, all in this file plus migration 0002:

1. ``TenantModel`` has no ``objects`` manager. Its default manager is ``tenant``,
   whose querysets raise ``TenantScopeError`` when evaluated unless they were built
   through :class:`WorkspaceScope`. There is no ambient "current workspace".
2. Every tenant-owned table carries ``workspace`` and a ``UniqueConstraint``
   ``(workspace, id)``, so the composite tenant key is real in the schema and a
   future composite foreign key has something to point at.
3. Migration 0002 installs SQLite triggers that reject any row whose parent row
   belongs to a different workspace. That is the database-level second line: an
   application bug cannot stitch two tenants together.
"""
from __future__ import annotations

from django.db import models


class TenantScopeError(RuntimeError):
    """Raised when a tenant-owned table is queried without a workspace predicate."""


class TenantQuerySet(models.QuerySet):
    _workspace_scoped = False

    def _clone(self, *args, **kwargs):
        clone = super()._clone(*args, **kwargs)
        clone._workspace_scoped = self._workspace_scoped
        return clone

    def scoped_to(self, workspace_id: int) -> "TenantQuerySet":
        clone = self.filter(workspace_id=workspace_id)
        clone._workspace_scoped = True
        return clone

    def _fetch_all(self):
        if not self._workspace_scoped:
            raise TenantScopeError(
                f"{self.model.__name__} was queried without a workspace predicate. "
                "Use WorkspaceScope (scope_for(workspace)) instead."
            )
        return super()._fetch_all()

    # Writes are equally guarded.
    def _raise(self, op):
        raise TenantScopeError(f"{op} on {self.model.__name__} requires a workspace scope")

    def update(self, **kwargs):
        if not self._workspace_scoped:
            self._raise("update()")
        return super().update(**kwargs)

    def delete(self):
        if not self._workspace_scoped:
            self._raise("delete()")
        return super().delete()


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):  # type: ignore[misc]
    pass


class TenantModel(models.Model):
    """Base class for every tenant-owned table."""

    workspace = models.ForeignKey("slice.Workspace", on_delete=models.CASCADE)

    tenant = TenantManager()
    # Django internals (reverse relations, refresh_from_db) need an unguarded base
    # manager. It is deliberately named so that the static check in
    # tests/test_tenancy.py fails the build if application code touches it.
    _unscoped = models.Manager()

    class Meta:
        abstract = True
        base_manager_name = "_unscoped"
        default_manager_name = "tenant"


class WorkspaceScope:
    """The only sanctioned way for application code to touch tenant-owned tables."""

    def __init__(self, workspace) -> None:
        if workspace is None or getattr(workspace, "pk", None) is None:
            raise TenantScopeError("WorkspaceScope requires a saved Workspace")
        self.workspace = workspace

    @property
    def workspace_id(self) -> int:
        return self.workspace.pk

    def query(self, model: type[models.Model]) -> TenantQuerySet:
        if not issubclass(model, TenantModel):
            raise TenantScopeError(f"{model.__name__} is not a tenant-owned model")
        return model.tenant.scoped_to(self.workspace_id)  # type: ignore[attr-defined]

    def create(self, model: type[models.Model], **kwargs):
        if "workspace" in kwargs or "workspace_id" in kwargs:
            raise TenantScopeError("workspace is supplied by the scope, not the caller")
        return self.query(model).create(workspace=self.workspace, **kwargs)

    def get_or_create(self, model: type[models.Model], defaults=None, **kwargs):
        if "workspace" in kwargs or "workspace_id" in kwargs:
            raise TenantScopeError("workspace is supplied by the scope, not the caller")
        return self.query(model).get_or_create(
            workspace=self.workspace, defaults=defaults or {}, **kwargs
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<WorkspaceScope {self.workspace.slug}>"


def scope_for(workspace) -> WorkspaceScope:
    return WorkspaceScope(workspace)
