"""Canonical admin-only helpers (cross-tenant bypass, etc.).

Public import contract (use this single style everywhere):

    from app.shared.admin.cross_tenant_session import (
        cross_tenant_session, require_superadmin,
    )

The submodule ``app.shared.admin.cross_tenant_session`` exposes the
asynccontextmanager of the same name and the FastAPI dependency
``require_superadmin``. Do NOT import the function as an attribute of the
``app.shared.admin`` package itself (the submodule name shadows the function).
"""
