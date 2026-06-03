"""
P0-5 + P0-6 sentinels: FairnessGuard + audit_log no REST PUT culture-profile.

Auditoria 2026-05-24: REST PUT handler (lapis inline da UI) nao tinha
FairnessGuard nem audit trail.

Sentinels:
- T1: FairnessGuard e chamado no PUT handler (P0-5)
- T2: Texto discriminatorio levanta HTTPException 422 (P0-5 fail-closed)
- T3: FairnessGuard regression (excecao) nao bloqueia o save (padrao canonico)
- T4: Audit log_action e chamado apos save bem-sucedido (P0-6)
- T5: Falha no audit nao bloqueia save
- T6: Texto limpo passa normalmente (sem false positive)
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _company_id_str():
    return "00000000-0000-0000-0000-000000000001"


def _company_id_uuid():
    return uuid.UUID(_company_id_str())


def _make_current_user():
    user = MagicMock()
    user.email = "recruiter@company.test"
    user.id = "user-uuid-456"
    return user


def _make_repo():
    repo = AsyncMock()
    repo.upsert_profile_fields = AsyncMock(return_value=MagicMock())
    return repo


def _clean_data():
    from app.schemas.company_culture import CompanyCultureProfileUpdate
    return CompanyCultureProfileUpdate(mission="Empresa inovadora com proposito.")


def _discriminatory_data():
    from app.schemas.company_culture import CompanyCultureProfileUpdate
    return CompanyCultureProfileUpdate(mission="Buscamos jovens solteiros sem filhos.")


# ---------------------------------------------------------------------------
# T1 — FairnessGuard e chamado no PUT handler (P0-5)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fairness_guard_is_called_on_put_culture_profile():
    """T1: FairnessGuard.check() deve ser invocado em toda chamada PUT."""
    from app.api.v1.company_culture import update_culture_profile

    current_user = _make_current_user()
    repo = _make_repo()
    data = _clean_data()
    cid = _company_id_uuid()

    mock_fg_result = MagicMock()
    mock_fg_result.is_blocked = False

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
         patch("app.shared.compliance.audit_service.AuditService") as MockAS:
        mock_fg = MagicMock()
        mock_fg.check.return_value = mock_fg_result
        MockFG.return_value = mock_fg

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)
        MockAS.return_value = mock_audit

        await update_culture_profile(
            company_id=cid,
            data=data,
            repo=repo,
            current_user=current_user,
            tenant_company_id=_company_id_str(),
        )

    assert MockFG.called, "T1: FairnessGuard deve ser instanciado no PUT handler"
    assert mock_fg.check.called, "T1: FairnessGuard.check() deve ser chamado"


# ---------------------------------------------------------------------------
# T2 — Texto discriminatorio levanta 422 (P0-5 fail-closed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discriminatory_text_raises_422():
    """T2: is_blocked=True deve levantar HTTPException 422 antes do save."""
    from app.api.v1.company_culture import update_culture_profile

    current_user = _make_current_user()
    repo = _make_repo()
    data = _discriminatory_data()
    cid = _company_id_uuid()

    mock_fg_result = MagicMock()
    mock_fg_result.is_blocked = True
    mock_fg_result.category = "age_discrimination"
    mock_fg_result.educational_message = "Conteudo discriminatorio por idade."
    mock_fg_result.blocked_terms = ["jovens", "solteiros"]

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG:
        mock_fg = MagicMock()
        mock_fg.check.return_value = mock_fg_result
        MockFG.return_value = mock_fg

        with pytest.raises(HTTPException) as exc_info:
            await update_culture_profile(
                company_id=cid,
                data=data,
                repo=repo,
                current_user=current_user,
                tenant_company_id=_company_id_str(),
            )

    assert exc_info.value.status_code == 422, (
        f"T2: status_code deve ser 422, got {exc_info.value.status_code}"
    )
    assert exc_info.value.detail["code"] == "fairness_blocked"
    # Save NAO deve ter sido chamado
    repo.upsert_profile_fields.assert_not_called()


# ---------------------------------------------------------------------------
# T3 — FairnessGuard regression nao bloqueia save
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fairness_guard_exception_does_not_block_save():
    """T3: excecao no FairnessGuard NAO deve impedir o save (padrao canonico JD)."""
    from app.api.v1.company_culture import update_culture_profile

    current_user = _make_current_user()
    repo = _make_repo()
    data = _clean_data()
    cid = _company_id_uuid()

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
         patch("app.shared.compliance.audit_service.AuditService") as MockAS:
        mock_fg = MagicMock()
        mock_fg.check.side_effect = RuntimeError("engine crash simulado")
        MockFG.return_value = mock_fg

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)
        MockAS.return_value = mock_audit

        result = await update_culture_profile(
            company_id=cid,
            data=data,
            repo=repo,
            current_user=current_user,
            tenant_company_id=_company_id_str(),
        )

    assert result is not None, "T3: save deve ocorrer mesmo com FairnessGuard em falha"
    repo.upsert_profile_fields.assert_called_once()


# ---------------------------------------------------------------------------
# T4 — Audit log_action e chamado apos save bem-sucedido (P0-6)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_log_action_called_after_save():
    """T4: AuditService.log_action deve ser chamado com action_type=company_culture_update."""
    from app.api.v1.company_culture import update_culture_profile

    current_user = _make_current_user()
    repo = _make_repo()
    data = _clean_data()
    cid = _company_id_uuid()

    mock_fg_result = MagicMock()
    mock_fg_result.is_blocked = False

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
         patch("app.shared.compliance.audit_service.AuditService") as MockAS:
        mock_fg = MagicMock()
        mock_fg.check.return_value = mock_fg_result
        MockFG.return_value = mock_fg

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)
        MockAS.return_value = mock_audit

        await update_culture_profile(
            company_id=cid,
            data=data,
            repo=repo,
            current_user=current_user,
            tenant_company_id=_company_id_str(),
        )

    assert MockAS.called, "T4: AuditService deve ser instanciado"
    assert mock_audit.log_action.called, "T4: log_action deve ser chamado"
    call_kwargs = mock_audit.log_action.call_args.kwargs
    assert call_kwargs.get("action_type") == "company_culture_update", (
        f"T4: action_type deve ser company_culture_update, got {call_kwargs.get('action_type')}"
    )
    assert call_kwargs.get("company_id") == _company_id_str()
    assert call_kwargs.get("target_type") == "company_culture_profile"
    metadata = call_kwargs.get("metadata", {})
    assert "fields_updated" in metadata
    assert metadata.get("source") == "rest_put_inline_edit"


# ---------------------------------------------------------------------------
# T5 — Falha no audit nao bloqueia save
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_failure_does_not_block_save():
    """T5: excecao no audit NAO deve impedir o save."""
    from app.api.v1.company_culture import update_culture_profile

    current_user = _make_current_user()
    repo = _make_repo()
    data = _clean_data()
    cid = _company_id_uuid()

    mock_fg_result = MagicMock()
    mock_fg_result.is_blocked = False

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
         patch("app.shared.compliance.audit_service.AuditService") as MockAS:
        mock_fg = MagicMock()
        mock_fg.check.return_value = mock_fg_result
        MockFG.return_value = mock_fg

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(side_effect=RuntimeError("db down"))
        MockAS.return_value = mock_audit

        result = await update_culture_profile(
            company_id=cid,
            data=data,
            repo=repo,
            current_user=current_user,
            tenant_company_id=_company_id_str(),
        )

    assert result is not None, "T5: resultado valido mesmo com audit falhando"
    repo.upsert_profile_fields.assert_called_once()


# ---------------------------------------------------------------------------
# T6 — Texto limpo passa sem false positive
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clean_text_passes_through():
    """T6: texto limpo sem vies NAO deve ser bloqueado."""
    from app.api.v1.company_culture import update_culture_profile
    from app.schemas.company_culture import CompanyCultureProfileUpdate

    current_user = _make_current_user()
    repo = _make_repo()
    data = CompanyCultureProfileUpdate(
        mission="Transformar o mercado de trabalho com tecnologia e empatia.",
        dei_initiatives="Valorizamos a diversidade de perspectivas e experiencias.",
    )
    cid = _company_id_uuid()

    mock_fg_result = MagicMock()
    mock_fg_result.is_blocked = False
    mock_fg_result.soft_warnings = []

    with patch("app.api.v1.company_culture.get_user_company_id", return_value=_company_id_str()), \
         patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
         patch("app.shared.compliance.audit_service.AuditService") as MockAS:
        mock_fg = MagicMock()
        mock_fg.check.return_value = mock_fg_result
        MockFG.return_value = mock_fg

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)
        MockAS.return_value = mock_audit

        result = await update_culture_profile(
            company_id=cid,
            data=data,
            repo=repo,
            current_user=current_user,
            tenant_company_id=_company_id_str(),
        )

    assert result is not None, "T6: texto limpo deve salvar normalmente"
    repo.upsert_profile_fields.assert_called_once()
