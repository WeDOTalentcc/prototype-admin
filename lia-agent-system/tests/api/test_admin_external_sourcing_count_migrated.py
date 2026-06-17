"""Test: admin_external endpoints contam sourcing via CustomAgent canonical.

Sub-sprint 7B-3a part 1 (2026-05-25). Cobre 3 sites migrados em
app/api/v1/admin_external.py (linhas ~208, ~320, ~409):
1. list_clients per-client active_sourcing count
2. single-company sourcing_count
3. list studio agents sourcing_agents (lendo runtime_metrics JSONB)

Label 'sourcing_agent' preservado nos response items (UI back-compat).
Import legacy SourcingAgent removido.
"""
from __future__ import annotations

import inspect

from app.api.v1 import admin_external


def test_admin_external_no_legacy_sourcing_agent_import():
    """Import SourcingAgent legacy removido do módulo."""
    src = inspect.getsource(admin_external)
    assert "from app.models.sourcing_agent import SourcingAgent" not in src
    # CustomAgent importado canonical
    assert "from app.models.custom_agent import CustomAgent" in src


def test_admin_external_sourcing_counts_usam_custom_agent():
    """Ambas as queries de count usam CustomAgent.category='sourcing'."""
    src = inspect.getsource(admin_external)
    # Não deve usar SourcingAgent.id em count
    assert "func.count(SourcingAgent.id)" not in src
    # Deve usar CustomAgent.id com filter canonical
    assert "func.count(CustomAgent.id)" in src
    # Pattern canonical category=sourcing + not archived
    assert 'CustomAgent.category == "sourcing"' in src
    assert 'CustomAgent.status != "archived"' in src


def test_admin_external_studio_listing_le_runtime_metrics_jsonb():
    """Listing studio agents agora lê metrics de runtime_metrics JSONB (migration 203)."""
    src = inspect.getsource(admin_external)
    # runtime_metrics dict acessado para metrics legacy
    assert "runtime_metrics" in src
    # Label back-compat preservado
    assert '"sourcing_agent"' in src or "'sourcing_agent'" in src
