"""Contract tests: PipelineTemplateService audit emission canonical (REGRA #1 ACH-026).

Sprint Pipeline Templates Afya 2026-05-26 — Fase 4.1 (TDD canonical green).

Garante:
1. create() emite audit_service.log_decision com canonical fields
   (agent_name="pipeline_template_service", decision_type="company_settings_change",
   action="pipeline_template_created", reasoning contém template_id+template_name,
   actor_user_id=created_by, human_review_required=False).
2. update() / archive() / clone() / apply_to_vacancy() seguem mesmo pattern.
3. Falha do audit NÃO bloqueia a mutation (resilience canonical) — quando
   audit_service.log_decision raise, service retorna template normalmente.
4. Audit é emitido UMA vez por mutation (não duplica).
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.pipeline.services.pipeline_template_service import (
    APPLY_SOURCE_MANUAL_MODAL,
    PipelineTemplateService,
)


COMPANY_A = "company-a-audit"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_template_mock(name="T", template_id=None):
    t = MagicMock()
    t.id = template_id or uuid.uuid4()
    t.name = name
    t.company_id = COMPANY_A
    t.is_default = False
    t.stages = [{"name": "S1", "order": 1, "type": "manual", "sla_days": 2}]
    t.usage_count = 0
    return t


def _make_vacancy_mock(vacancy_id=None):
    v = MagicMock()
    v.id = vacancy_id or uuid.uuid4()
    v.company_id = COMPANY_A
    v.interview_stages = []
    v.is_pipeline_customized = False
    return v


def _build_service(template_mock=None, vacancy_mock=None):
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    service = PipelineTemplateService(db)
    service.repo = MagicMock()
    service.repo.get_by_id = AsyncMock(return_value=template_mock)
    service.repo.create = AsyncMock(return_value=template_mock or _make_template_mock())
    service.repo.update = AsyncMock(side_effect=lambda t, data, updated_by=None: t)
    service.repo.archive = AsyncMock(return_value=None)
    service.repo.clone = AsyncMock(return_value=_make_template_mock(name="Cloned"))
    service.repo.clear_default = AsyncMock(return_value=None)
    service.repo.increment_usage = AsyncMock(
        side_effect=lambda t: (setattr(t, "usage_count", t.usage_count + 1), t)[1]
    )

    service._vacancy_repo = MagicMock()
    service._vacancy_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=vacancy_mock)

    return service


def _canonical_audit_assertions(call_kwargs, *, action: str, actor: str, template):
    assert call_kwargs["company_id"] == COMPANY_A
    assert call_kwargs["agent_name"] == "pipeline_template_service"
    assert call_kwargs["decision_type"] == "company_settings_change"
    assert call_kwargs["action"] == action
    assert call_kwargs["actor_user_id"] == actor
    assert call_kwargs["human_review_required"] is False

    reasoning = call_kwargs["reasoning"]
    assert any(f"template_id: {template.id}" in r for r in reasoning), (
        f"reasoning MUST contain template_id; got {reasoning}"
    )
    assert any(f"template_name: {template.name}" in r for r in reasoning), (
        f"reasoning MUST contain template_name; got {reasoning}"
    )
    assert any(f"action: {action}" in r for r in reasoning)


# ---------------------------------------------------------------------------
# create() audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_emits_audit_canonical():
    """create() emite audit ATÔMICO: log_decision_in_session na MESMA sessão
    da mutação (self.db), com commit único delegado ao get_tenant_db."""
    template = _make_template_mock(name="NewTemplate")
    service = _build_service(template_mock=template)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision_in_session",
        new_callable=AsyncMock,
    ) as mock_audit, patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_independent:
        result = await service.create(
            COMPANY_A,
            {"name": "NewTemplate", "stages": []},
            created_by="creator@x",
        )

    assert mock_audit.call_count == 1, "audit MUST be emitted exactly once per create"
    assert mock_independent.call_count == 0, (
        "create MUST NOT open a separate audit session (atomic path only)"
    )
    # Sentinela atomicidade: a sessão do audit é a MESMA da mutação (self.db).
    assert mock_audit.call_args.args[0] is service.db, (
        "audit row MUST share the mutation session (single transaction)"
    )
    _canonical_audit_assertions(
        mock_audit.call_args.kwargs,
        action="pipeline_template_created",
        actor="creator@x",
        template=template,
    )


# ---------------------------------------------------------------------------
# update() audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_emits_audit_canonical_with_fields_updated_reasoning():
    """update() emite audit ATÔMICO na MESMA sessão da mutação (self.db)."""
    template = _make_template_mock(name="Existing")
    service = _build_service(template_mock=template)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision_in_session",
        new_callable=AsyncMock,
    ) as mock_audit, patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_independent:
        await service.update(
            template.id,
            COMPANY_A,
            {"name": "Renamed", "description": "v2"},
            updated_by="editor@x",
        )

    assert mock_audit.call_count == 1
    assert mock_independent.call_count == 0, (
        "update MUST NOT open a separate audit session (atomic path only)"
    )
    # Sentinela atomicidade: a sessão do audit é a MESMA da mutação (self.db).
    assert mock_audit.call_args.args[0] is service.db, (
        "audit row MUST share the mutation session (single transaction)"
    )
    kwargs = mock_audit.call_args.kwargs
    _canonical_audit_assertions(
        kwargs,
        action="pipeline_template_updated",
        actor="editor@x",
        template=template,
    )
    # Reasoning canonical contém fields_updated
    assert any("fields_updated" in r for r in kwargs["reasoning"]), (
        "update reasoning MUST include fields_updated list"
    )


@pytest.mark.asyncio
async def test_update_skips_audit_when_template_not_found():
    """Cross-tenant / template não existe → audit NÃO é emitido."""
    service = _build_service(template_mock=None)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision_in_session",
        new_callable=AsyncMock,
    ) as mock_audit, patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_independent:
        result = await service.update(
            uuid.uuid4(), COMPANY_A, {"name": "X"}, updated_by="u"
        )

    assert result is None
    assert mock_audit.call_count == 0, "audit MUST NOT fire for non-existent template"
    assert mock_independent.call_count == 0


# ---------------------------------------------------------------------------
# archive() audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archive_emits_audit_canonical():
    template = _make_template_mock(name="ToArchive")
    service = _build_service(template_mock=template)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_audit:
        await service.archive(template.id, COMPANY_A, updated_by="admin@x")

    assert mock_audit.call_count == 1
    _canonical_audit_assertions(
        mock_audit.call_args.kwargs,
        action="pipeline_template_archived",
        actor="admin@x",
        template=template,
    )


# ---------------------------------------------------------------------------
# clone() audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clone_emits_audit_canonical_with_origin_reasoning():
    original = _make_template_mock(name="Origin")
    service = _build_service(template_mock=original)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_audit:
        cloned = await service.clone(
            original.id, COMPANY_A, new_name="Origin Cópia", created_by="cloner@x"
        )

    assert mock_audit.call_count == 1
    kwargs = mock_audit.call_args.kwargs
    assert kwargs["action"] == "pipeline_template_cloned"
    assert kwargs["actor_user_id"] == "cloner@x"
    # Reasoning canonical: cloned_from_id + cloned_from_name
    assert any(f"cloned_from_id: {original.id}" in r for r in kwargs["reasoning"]), (
        f"clone reasoning MUST include cloned_from_id; got {kwargs['reasoning']}"
    )
    assert any("cloned_from_name: Origin" in r for r in kwargs["reasoning"])


# ---------------------------------------------------------------------------
# apply_to_vacancy() audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_to_vacancy_emits_audit_canonical():
    template = _make_template_mock(name="ToApply")
    vacancy = _make_vacancy_mock()
    service = _build_service(template_mock=template, vacancy_mock=vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
    ) as mock_audit:
        await service.apply_to_vacancy(
            template_id=template.id,
            vacancy_id=vacancy.id,
            company_id=COMPANY_A,
            applied_by="applier@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert mock_audit.call_count == 1
    kwargs = mock_audit.call_args.kwargs
    _canonical_audit_assertions(
        kwargs,
        action="pipeline_template_applied",
        actor="applier@x",
        template=template,
    )
    # job_vacancy_id canonical presente
    assert kwargs["job_vacancy_id"] == str(vacancy.id), (
        "apply audit MUST include job_vacancy_id for SOX trail"
    )
    # source no reasoning
    assert any("source: manual_modal" in r for r in kwargs["reasoning"]), (
        f"apply reasoning MUST contain source; got {kwargs['reasoning']}"
    )


# ---------------------------------------------------------------------------
# Audit failure does NOT block mutation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_audit_failure_propagates_atomic():
    """ATÔMICO (fail-CLOSED): create grava template + audit na MESMA sessão e o
    commit é único (get_tenant_db). Se o audit falhar, a exceção PROPAGA — o
    get_tenant_db faz rollback do template junto. Não existe save sem trail.

    (Antes da atomicidade o audit rodava em conexão separada e o erro era
    engolido; com sessão compartilhada engolir seria incoerente — a sessão já
    estaria poisoned e o commit do route falharia de forma opaca.)
    """
    template = _make_template_mock(name="X")
    service = _build_service(template_mock=template)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision_in_session",
        new_callable=AsyncMock,
        side_effect=RuntimeError("audit DB down"),
    ):
        with pytest.raises(RuntimeError, match="audit DB down"):
            await service.create(
                COMPANY_A, {"name": "X", "stages": []}, created_by="u@x"
            )


@pytest.mark.asyncio
async def test_audit_failure_does_not_block_apply():
    template = _make_template_mock(name="ApplyResilient")
    vacancy = _make_vacancy_mock()
    service = _build_service(template_mock=template, vacancy_mock=vacancy)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
        side_effect=RuntimeError("audit down"),
    ):
        result = await service.apply_to_vacancy(
            template_id=template.id,
            vacancy_id=vacancy.id,
            company_id=COMPANY_A,
            applied_by="u@x",
            source=APPLY_SOURCE_MANUAL_MODAL,
        )

    assert result is not None, "apply MUST complete even when audit fails"
    assert result["template_id"] == str(template.id)


@pytest.mark.asyncio
async def test_audit_failure_does_not_block_archive():
    template = _make_template_mock(name="ArchiveResilient")
    service = _build_service(template_mock=template)

    with patch(
        "app.domains.pipeline.services.pipeline_template_service.audit_service.log_decision",
        new_callable=AsyncMock,
        side_effect=RuntimeError("audit down"),
    ):
        result = await service.archive(template.id, COMPANY_A, updated_by="u")

    assert result is not None
