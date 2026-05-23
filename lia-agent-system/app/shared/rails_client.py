"""Thin convenience wrappers around RailsClient for cross-domain use.

⚠️ DEPRECATION SHIM (W2-010 Phase A, 2026-05-22):
Canonical home agora é `app/shared/integration/rails_client.py`.
Esse arquivo permanece como shim de retrocompat (13 callers in-tree usam
lazy imports inside-function — migram transparentemente via re-export).

Migração de imports (preferida, novos callers):
    # ANTES (deprecated)
    from app.shared.rails_client import rails_get, rails_patch, rails_post

    # DEPOIS (canonical)
    from app.shared.integration.rails_client import rails_get, rails_patch, rails_post

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-010).

Phase B (futura) deletará este arquivo após 1 sprint estável com zero callers
do path legacy.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "`app.shared.rails_client` está depreciado desde W2-010 (2026-05-22). "
    "Use `app.shared.integration.rails_client` (canonical home com OTel "
    "observability). Esse shim permanece pra retrocompat dos 13 callers in-tree.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export do canonical (preserva API: rails_get, rails_patch, rails_post)
from app.shared.integration.rails_client import (  # noqa: E402,F401
    rails_get,
    rails_patch,
    rails_post,
)

__all__ = [
    "rails_get",
    "rails_patch",
    "rails_post",
]
