"""Ghost-bypass regression sensor (audit 2026-05-21 P0-1, reintroduced 2026-05-22).

The pipeline tool ``get_company_culture`` (``_wrap_get_company_culture`` in
``app/domains/cv_screening/agents/pipeline_tool_registry.py``) returned
``culture.mission/vision/values/evp_bullets/...`` RAW to the LLM, ignoring the
per-field ``lia_field_toggles`` configured in the "Instruções LIA por Campo"
panel. A recruiter turning OFF "mission" still saw the tool inject mission.

This is the same ghost-setting class the canonical helper
``build_company_agent_context`` / ``LiaFieldConfigService`` closes elsewhere.

Gate contract (mirrors test_offer_approval_gate.py model):
- Toggle OFF for a canonical culture field  -> field MUST be omitted from the
  tool response ``data`` dict (fail-closed for the toggle).
- Toggle ON  for a canonical culture field  -> field present with company value.

The handler is decorated with ``@tool_handler("cv_screening")`` which injects
``company_id`` from the ``_current_company_id`` ContextVar -- the test sets it
directly rather than going through the auth middleware.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


_COMPANY_ID = "00000000-0000-0000-0000-000000000042"


def _make_culture():
    """A fully-populated CompanyCultureProfile-like object."""
    culture = MagicMock()
    culture.mission = "Nossa missao e X"
    culture.vision = "Nossa visao e Y"
    culture.values = ["Integridade", "Excelencia"]
    culture.evp_bullets = ["EVP 1", "EVP 2"]
    culture.core_competencies = ["Comp A"]
    culture.culture_description = "Cultura colaborativa"
    culture.industry = "Tecnologia"
    culture.work_model = "hybrid"
    culture.leadership_style = "servant"
    culture.team_dynamics = "agil"
    culture.dei_initiatives = ["DEI 1"]
    culture.tech_stack = ["Python"]
    culture.default_languages = ["pt-BR"]
    return culture


def _make_field_config_result(active: set[str], inactive: set[str]):
    """Mimic LiaFieldConfigResult.active_fields / all_fields keyed by field_key."""
    result = MagicMock()
    result.active_fields = {k: MagicMock(is_active=True) for k in active}
    result.inactive_fields = {k: MagicMock(is_active=False) for k in inactive}
    all_fields = {}
    for k in active:
        all_fields[k] = MagicMock(is_active=True)
    for k in inactive:
        all_fields[k] = MagicMock(is_active=False)
    result.all_fields = all_fields
    return result


@asynccontextmanager
async def _fake_session_cm():
    yield MagicMock()


def _set_tenant_contextvar():
    from app.middleware.auth_enforcement import _current_company_id
    return _current_company_id.set(_COMPANY_ID)


@pytest.mark.asyncio
async def test_mission_off_omitted_values_on_present():
    """mission toggle OFF -> omitted; values toggle ON -> present."""
    from app.domains.cv_screening.agents import pipeline_tool_registry as mod

    culture = _make_culture()
    repo = AsyncMock()
    # _wrap_get_company_culture uses the Fase 5.1 gate get_for_agent_context
    # (unapproved auto culture withheld), not get_for_company.
    repo.get_for_agent_context = AsyncMock(return_value=culture)

    # mission OFF, everything else ON so we isolate the mission case.
    active = {
        "vision", "values", "evp_bullets", "core_competencies",
        "industry", "work_model", "leadership_style", "team_dynamics",
        "dei_initiatives", "tech_stack", "default_languages",
    }
    inactive = {"mission"}
    fc_result = _make_field_config_result(active, inactive)

    svc_instance = MagicMock()
    svc_instance.get_field_config = AsyncMock(return_value=fc_result)

    token = _set_tenant_contextvar()
    try:
        with patch.object(mod, "AsyncSessionLocal", _fake_session_cm), \
             patch(
                 "app.domains.company.repositories.culture_profile_repository.CultureProfileRepository",
                 return_value=repo,
             ), \
             patch(
                 "app.domains.cv_screening.services.lia_field_config_service.LiaFieldConfigService",
                 return_value=svc_instance,
             ):
            out = await mod._wrap_get_company_culture()
    finally:
        from app.middleware.auth_enforcement import _current_company_id
        _current_company_id.reset(token)

    assert out["success"] is True, out
    data = out["data"]
    assert "mission" not in data or not data.get("mission"), (
        f"mission toggle is OFF but tool still injected it: {data.get('mission')!r}"
    )
    assert data.get("values") == ["Integridade", "Excelencia"], (
        f"values toggle is ON but tool omitted/altered it: {data.get('values')!r}"
    )
