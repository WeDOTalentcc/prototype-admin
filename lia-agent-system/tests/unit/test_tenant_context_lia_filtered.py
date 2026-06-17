"""Unit tests for TenantContext.lia_filtered_prompt wiring (produtor único).

Covers:
- Teste B (no DB): to_prompt_snippet() includes the rich filtered block when
  populated, and emits no hanging "---" separator when empty.
- Field default is "" (back-compat + fail-safe).

The get_context() wiring against a real Postgres lives in the integration
suite (test_tenant_context_enriched.py); here we keep it DB-free and assert
the snippet contract, mirroring the AggregatedContext.lia_filtered_prompt
precedent.
"""
from __future__ import annotations

from app.shared.services.tenant_context_service import TenantContext


def _base(**kw) -> TenantContext:
    defaults = dict(
        company_id="co-1",
        company_name="ACME",
        sector="Tech",
        open_vacancies=0,
        autonomy_level="medium",
        plan="standard",
    )
    defaults.update(kw)
    return TenantContext(**defaults)


def test_field_default_is_empty_string():
    ctx = _base()
    assert ctx.lia_filtered_prompt == ""


def test_snippet_includes_filtered_block_when_populated():
    ctx = _base(lia_filtered_prompt="BLOCO_RICO_DA_EMPRESA")
    snippet = ctx.to_prompt_snippet()
    assert "BLOCO_RICO_DA_EMPRESA" in snippet


def test_snippet_emits_separator_only_when_block_present():
    ctx = _base(lia_filtered_prompt="BLOCO")
    assert "---" in ctx.to_prompt_snippet()


def test_snippet_no_hanging_separator_when_empty():
    ctx = _base(lia_filtered_prompt="")
    assert "---" not in ctx.to_prompt_snippet()
