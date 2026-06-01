"""Contract tests: PipelineTemplateService.apply_to_vacancy canonical copy-on-write.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 4.1 (TDD canonical green).

Garante:
1. apply_to_vacancy copy-on-write: vacancy.interview_stages é replaced pela
   translação canonical do template.stages.
2. Translação dual-write (Fase 1 Unify, 2026-06-01) via translate_template_stages_to_interview_stages:
   - Canonical: {name, order, type, sla_days, instructions} (CanonicalPipelineStage)
   - Legacy compat: {stageName=name, sla=sla_days} preservados para kanban
   - type "automatic" permanece "automatic" (sem rename para "automated")
3. usage_count incrementa em 1.
4. is_pipeline_customized=False após apply.
5. Cross-tenant: template de A + vacancy de B (e vice-versa) → retorna None.
6. source inválido → ValueError.
7. Audit log emitido com decision_type=company_settings_change,
   action="pipeline_template_applied", job_vacancy_id presente, source no reasoning.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.pipeline.services.pipeline_template_service import (
    APPLY_SOURCE_MANUAL_MODAL,
    APPLY_SOURCE_WIZARD_AUTO_SUGGEST,
    APPLY_SOURCE_WIZARD_EXPLICIT,
    APPLY_VALID_SOURCES,
    PipelineTemplateService,
    translate_template_stages_to_interview_stages,
)


COMPANY_A = "company-a-apply"
COMPANY_B = "company-b-apply"


# ---------------------------------------------------------------------------
# Translation canonical
# ---------------------------------------------------------------------------


def test_translate_automatic_to_automated():
    """Fase 1 Unify dual-write (2026-06-01): 'automatic' NÃO é renomeado para
    'automated' — type permanece canônico. Dual-write grava name+stageName
    e sla_days+sla para compat retroativa com kanban.
    """
    out = translate_template_stages_to_interview_stages(
        [{"name": "Triagem", "order": 1, "type": "automatic", "sla_days": 2}]
    )
    assert len(out) == 1
    # ── Canonical fields (CanonicalPipelineStage) ─────────────────────────
    assert out[0]["name"] == "Triagem", "canonical 'name' ausente"
    assert out[0]["type"] == "automatic", (
        "Fase 1 Unify: 'automatic' NÃO deve mais ser renomeado para 'automated'"
    )
    assert out[0]["sla_days"] == 2, "canonical 'sla_days' ausente"
    assert out[0]["order"] == 1
    # ── Legacy compat (dual-write — remover quando kanban migrar p/ 'name') ─
    assert out[0]["stageName"] == "Triagem", "legacy 'stageName' ausente (kanban depende)"
    assert out[0]["sla"] == 2, "legacy 'sla' ausente (compat legada)"


def test_translate_manual_preserved():
    out = translate_template_stages_to_interview_stages(
        [{"name": "Entrevista", "order": 2, "type": "manual", "sla_days": 5}]
    )
    assert out[0]["type"] == "manual"


def test_translate_hybrid_preserved():
    out = translate_template_stages_to_interview_stages(
        [{"name": "Mix", "order": 1, "type": "hybrid", "sla_days": 3}]
    )
    assert out[0]["type"] == "hybrid"


def test_translate_field_mapping_canonical():
    """Fase 1 Unify dual-write: shape de saída tem AMBOS canonical + legacy aliases.

    Canonical (CanonicalPipelineStage): name, order, type, sla_days, instructions.
    Legacy compat (dual-write): stageName=name, sla=sla_days.
    Remover as legacy keys daqui quando kanban migrar p/ 'name'.
    """
    out = translate_template_stages_to_interview_stages(
        [{"name": "X", "order": 1, "type": "manual", "sla_days": 7, "instructions": "do it"}]
    )
    s = out[0]
    # Canonical fields obrigatórios
    assert "name" in s, "canonical field 'name' ausente"
    assert "order" in s, "canonical field 'order' ausente"
    assert "type" in s, "canonical field 'type' ausente"
    assert "sla_days" in s, "canonical field 'sla_days' ausente"
    assert "instructions" in s, "canonical field 'instructions' ausente"
    # Legacy compat (dual-write)
    assert "stageName" in s, "legacy 'stageName' ausente (kanban depende)"
    assert "sla" in s, "legacy 'sla' ausente (compat legada)"
    # Valores corretos
    assert s["name"] == "X"
    assert s["stageName"] == "X"          # alias de name
    assert s["sla_days"] == 7
    assert s["sla"] == 7                  # alias de sla_days
    assert s["instructions"] == "do it"


def test_translate_empty_list():
    assert translate_template_stages_to_interview_stages([]) == []
    assert translate_template_stages_to_interview_stages(None) == []


def test_translate_default_order_from_index():
    """Stage sem 'order' explícito recebe idx+1."""
    out = translate_template_stages_to_interview_stages(
        [{"name": "A", "type": "manual"}, {"name": "B", "type": "manual"}]
    )
    assert out[0]["order"] == 1
    assert out[1]["order"] == 2


# ---------------------------------------------------------------------------
# Helpers para mock service
# ---------------------------------------------------------------------------


def _make_template_mock(template_id, company_id=COMPANY_A, name="T", stages=None):
    t = MagicMock()
    t.id = template_id
    t.company_id = company_id
    t.name = name
    t.stages = stages or [
        {"name": "S1", "order": 1, "type": "automatic", "sla_days": 2},
        {"name": "S2", "order": 2, "type": "manual", "sla_days": 3},
    ]
    t.usage_count = 0
    return t


def _make_vacancy_mock(vacancy_id, company_id=COMPANY_A):
    v = MagicMock()
    v.id = vacancy_id
    v.company_id = company_id
    v.interview_stages = []
    v.is_pipeline_customized = True  # start customized, apply MUST reset to False
    return v


def _build_service_with_mocks(template_mock=None, vacancy_mock=None):
    """Builds PipelineTemplateService with all repo dependencies mocked."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    service = PipelineTemplateService(db)

    # Mock template repo
    service.repo = MagicMock()
    service.repo.get_by_id = AsyncMock(return_value=template_mock)
    service.repo.increment_usage = AsyncMock(
        side_effect=lambda t: (setattr(t, "usage_count", (t.usage_count or 0) + 1), t)[1]
    )

    # Mock vacancy repo
    service._vacancy_repo = MagicMock()
    service._vacancy_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=vacancy_mock)

    return service, db


# ---------------------------------------------------------------------------
# apply_to_vacancy core behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_copy_on_write_replaces_interview_stages():
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    vacancy = _make_vacancy_mock(vacancy_id)
    service, _ = _build_service_with_mocks(template, vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        result = await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert result is not None
    assert result["vacancy_id"] == str(vacancy_id)
    assert result["template_id"] == str(template_id)
    assert result["stages_applied"] == 2

    # vacancy.interview_stages MUST be replaced with translated stages (dual-write)
    assert len(vacancy.interview_stages) == 2
    # Canonical fields (CanonicalPipelineStage)
    assert vacancy.interview_stages[0]["name"] == "S1"
    assert vacancy.interview_stages[0]["type"] == "automatic", (
        "Fase 1 Unify: 'automatic' NÃO renomeia para 'automated'"
    )
    assert vacancy.interview_stages[1]["type"] == "manual"
    # Legacy compat (dual-write — kanban ainda depende)
    assert vacancy.interview_stages[0]["stageName"] == "S1"
    assert vacancy.interview_stages[1]["stageName"] == "S2"


@pytest.mark.asyncio
async def test_apply_increments_usage_count_by_one():
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    template.usage_count = 5
    vacancy = _make_vacancy_mock(vacancy_id)
    service, _ = _build_service_with_mocks(template, vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        result = await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_WIZARD_EXPLICIT,
        )

    assert template.usage_count == 6
    assert result["usage_count"] == 6


@pytest.mark.asyncio
async def test_apply_resets_is_pipeline_customized_to_false():
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    vacancy = _make_vacancy_mock(vacancy_id)
    vacancy.is_pipeline_customized = True
    service, _ = _build_service_with_mocks(template, vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert vacancy.is_pipeline_customized is False, (
        "apply MUST reset is_pipeline_customized=False (template traz pipeline limpo)"
    )


# ---------------------------------------------------------------------------
# Cross-tenant fail-closed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_returns_none_when_template_not_found():
    """Template não existe (ou cross-tenant) → repo retorna None → service None."""
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    service, _ = _build_service_with_mocks(template_mock=None, vacancy_mock=_make_vacancy_mock(vacancy_id))

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        result = await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert result is None, "cross-tenant template MUST return None (canonical non-leak)"


@pytest.mark.asyncio
async def test_apply_returns_none_when_vacancy_not_found():
    """Vacancy cross-tenant → vacancy_repo retorna None → service None."""
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    service, _ = _build_service_with_mocks(template_mock=template, vacancy_mock=None)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        result = await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert result is None, "cross-tenant vacancy MUST return None"


# ---------------------------------------------------------------------------
# Source validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_invalid_source_raises_valueerror():
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    vacancy = _make_vacancy_mock(vacancy_id)
    service, _ = _build_service_with_mocks(template, vacancy)

    with pytest.raises(ValueError, match="invalid apply source"):
        await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source="random_unknown_source",
        )


def test_apply_valid_sources_canonical_set():
    """Pin canonical APPLY_VALID_SOURCES — 3 valores explícitos."""
    assert APPLY_VALID_SOURCES == {
        "manual_modal",
        "wizard_auto_suggest",
        "wizard_explicit",
    }, "APPLY_VALID_SOURCES contract drift — adding sources requires endpoint Literal sync"


@pytest.mark.asyncio
@pytest.mark.parametrize("source", sorted(APPLY_VALID_SOURCES))
async def test_apply_accepts_all_canonical_sources(source):
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id)
    vacancy = _make_vacancy_mock(vacancy_id)
    service, _ = _build_service_with_mocks(template, vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ):
        result = await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=source,
        )
    assert result is not None
    assert result["source"] == source


# ---------------------------------------------------------------------------
# Audit log canonical
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_emits_audit_with_canonical_fields():
    template_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    template = _make_template_mock(template_id, name="MyTemplate")
    vacancy = _make_vacancy_mock(vacancy_id)
    service, _ = _build_service_with_mocks(template, vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_audit:
        await service.apply_to_vacancy(
            template_id=template_id,
            vacancy_id=vacancy_id,
            company_id=COMPANY_A,
            applied_by="recruiter@x",
            source=APPLY_SOURCE_WIZARD_AUTO_SUGGEST,
        )

    assert mock_audit.call_count == 1
    kwargs = mock_audit.call_args.kwargs

    assert kwargs["company_id"] == COMPANY_A
    assert kwargs["agent_name"] == "pipeline_template_service"
    assert kwargs["decision_type"] == "company_settings_change"
    assert kwargs["action"] == "pipeline_template_applied"
    assert kwargs["job_vacancy_id"] == str(vacancy_id)
    assert kwargs["actor_user_id"] == "recruiter@x"
    assert kwargs["human_review_required"] is False

    reasoning = kwargs["reasoning"]
    assert any("source: wizard_auto_suggest" in r for r in reasoning), (
        f"source MUST be in reasoning; got {reasoning}"
    )
    assert any("template_id" in r for r in reasoning)
    assert any("template_name: MyTemplate" in r for r in reasoning)
    assert any("stages_applied: 2" in r for r in reasoning)
