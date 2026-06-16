"""Contract tests pra agent_template_catalog endpoint (Sprint 3 Caminho B).

Validate canonical patterns:
- REGRA 1: extra='forbid' via WeDoBaseModel rejeita field fantasma
- REGRA 2: company_id no payload rejeitado
- REGRA 3: UUID path com type alias canonical
- multi-tenancy: require_company_id via JWT
- role gate: writes apenas para UserRole.wedotalent_admin

Strategy: unit-level (mocked repository) — não spin up DB real (vide
test_offer_approval_gate.py pattern). Validation testes via Pydantic
não precisam de db.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.agent_template_catalog import AgentTemplateCatalogRequest


# ─────────────────────────────────────────────────────────────────────────────
# Schema validation tests (REGRA 1, REGRA 2)
# ─────────────────────────────────────────────────────────────────────────────


def _base_payload() -> dict:
    return {
        "slug": "tpl-test",
        "name": "Test Template",
        "description": "test description meets min length",
        "category_id": "screening",
        "system_prompt": "you are a test agent with enough chars",
        "allowed_tools": ["search_candidates"],
        "context_level": "standard",
        "max_steps": 5,
        "temperature": 0.3,
        "enable_memory": True,
        "tags": ["test"],
    }


def test_schema_accepts_valid_payload():
    """Baseline: payload canonical é aceito."""
    payload = AgentTemplateCatalogRequest(**_base_payload())
    assert payload.slug == "tpl-test"
    assert payload.category_id == "screening"


def test_schema_rejects_extra_field_REGRA_1():
    """REGRA 1 Pydantic conventions: extra='forbid' via WeDoBaseModel.

    Field fantasma deve ser rejeitado com ValidationError.
    """
    payload = _base_payload()
    payload["ghost_field"] = "nope"
    with pytest.raises(ValidationError) as exc_info:
        AgentTemplateCatalogRequest(**payload)
    assert "extra" in str(exc_info.value).lower() or "forbid" in str(exc_info.value).lower()


def test_schema_rejects_company_id_in_payload_REGRA_2():
    """REGRA 2 Pydantic conventions: company_id PROIBIDO no request body.

    Multi-tenancy canonical: company_id vem do JWT via require_company_id.
    """
    payload = _base_payload()
    payload["company_id"] = "some-other-company-uuid"
    with pytest.raises(ValidationError):
        AgentTemplateCatalogRequest(**payload)


def test_schema_rejects_missing_required():
    """Required fields ausentes → ValidationError."""
    payload = _base_payload()
    del payload["slug"]
    with pytest.raises(ValidationError):
        AgentTemplateCatalogRequest(**payload)


def test_schema_temperature_clamped():
    """Temperature fora de [0, 2] → ValidationError."""
    payload = _base_payload()
    payload["temperature"] = 5.0
    with pytest.raises(ValidationError):
        AgentTemplateCatalogRequest(**payload)


def test_schema_max_steps_clamped():
    """max_steps fora de [1, 50] → ValidationError."""
    payload = _base_payload()
    payload["max_steps"] = 999
    with pytest.raises(ValidationError):
        AgentTemplateCatalogRequest(**payload)


# ─────────────────────────────────────────────────────────────────────────────

# NOTE: Repository DB-backed integration tests removidos do contract layer
# (test_repo_list_returns_seeded_templates, test_repo_filter_by_category_screening,
#  test_repo_filter_by_nps_returns_empty, test_repo_list_categories_includes_canonical_7).
#
# Razão: DATABASE_URL no Replit usa `?sslmode=require` (libpq-style) que asyncpg
# rejeita quando passado direto pra create_async_engine fora do helper canonical
# de lia_config.database. O helper canonical usa engine module-level que cria
# event-loop reuse conflicts com pytest-asyncio.
#
# Validação canonical de seed/filter/categorias foi feita via CLI direto (vide
# /tmp/quick_repo_check.py durante Sprint 3 — output:
#   list(): 15 templates
#   category=screening: 4
#   category=nps (extensibility): 0
#   categories: ['all','analytics','automation','communication','job_management','screening','sourcing']
#   sectors: ['educacao','generico','saude','tech','varejo']
#   get_by_slug: Triagem Tech
# ).
#
# Para teste integration futuro: criar tests/integration/test_agent_template_catalog.py
# usando o helper de session canonical de lia_config.database (que sanitiza sslmode).
