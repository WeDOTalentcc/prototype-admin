"""Test: quota_enforcement sourcing_agents resource counta CustomAgent canonical.

Sub-sprint 7B-3a part 1 (2026-05-25). Cobre mudança em
app/services/quota_enforcement.py:get_current_count — resource_key
'sourcing_agents' agora consulta CustomAgent.where(category='sourcing',
status != 'archived'), removendo SourcingAgent legacy.

Resource string 'sourcing_agents' permanece (back-compat pricing 7B-3b).
"""
from __future__ import annotations

import inspect

from app.services import quota_enforcement
from app.services.quota_enforcement import get_current_count


def test_get_current_count_sourcing_agents_usa_custom_agent_canonical():
    """Branch 'sourcing_agents' filtra CustomAgent.category='sourcing'."""
    src = inspect.getsource(get_current_count)
    # Branch correto presente
    assert 'resource_key == "sourcing_agents"' in src
    # Query usa CustomAgent canonical
    assert "CustomAgent.id" in src
    assert 'CustomAgent.category == "sourcing"' in src
    assert 'CustomAgent.status != "archived"' in src


def test_quota_enforcement_no_legacy_sourcing_agent_import():
    """Import SourcingAgent legacy removido do módulo."""
    mod_src = inspect.getsource(quota_enforcement)
    # Não importa do path legacy
    assert "from app.models.sourcing_agent import SourcingAgent" not in mod_src
    # CustomAgent continua importado (canonical)
    assert "from app.models.custom_agent import CustomAgent" in mod_src
