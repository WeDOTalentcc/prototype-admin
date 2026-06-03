"""
Sensor permanente: audit log em handlers de write de Benefícios.

Garante que create_company_benefit, update_company_benefit e
delete_company_benefit chamam AuditService.log_action após o save.

Estratégia: unit pura — mocka repo e AuditService,
chama handlers diretamente via pytest-asyncio.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


COMPANY_ID = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
BENEFIT_ID = uuid.UUID("cccccccc-cccc-4ccc-cccc-cccccccccccc")
FAKE_USER_EMAIL = "rh@empresa.com"


def _make_user(email: str = FAKE_USER_EMAIL):
    u = MagicMock()
    u.email = email
    u.id = str(uuid.uuid4())
    return u


def _make_benefit(name: str = "Vale Refeição"):
    b = MagicMock()
    b.id = BENEFIT_ID
    b.company_id = COMPANY_ID
    b.name = name
    b.category = "food"
    b.description = "Benefício de alimentação"
    b.icon = None
    b.value = 800.0
    b.percentage_value = None
    b.value_type = "monetary"
    b.value_details = None
    b.applicable_to = None
    b.seniority_levels = None
    b.contract_types = None
    b.departments = None
    b.is_active = True
    b.is_highlighted = False
    b.order = 0
    # Campos serializados por _to_response()->CompanyBenefitResponse.
    # MagicMock retorna filhos truthy para atributos nao-setados, o que
    # passa pelo gate getattr() e quebra a validacao do response model
    # (provider_cnpj str | None recebe MagicMock; *_date.isoformat() idem).
    # Setar None explicito espelha o estado real do model SQLAlchemy.
    b.provider_cnpj = None
    b.subsidiaries = None
    b.valid_from = None
    b.valid_until = None
    b.review_frequency_months = None
    b.next_review_date = None
    b.created_at = None
    b.updated_at = None
    return b


# ---------------------------------------------------------------------------
# create_company_benefit
# ---------------------------------------------------------------------------

class TestCreateCompanyBenefitAuditLog:
    """Handler POST /company/benefits/ chama audit log após save."""

    @pytest.mark.asyncio
    async def test_create_calls_audit_log_after_save(self):
        from app.api.v1.company_benefits import create_company_benefit, CompanyBenefitCreate

        payload = CompanyBenefitCreate(
            name="Vale Refeição",
            category="food",
            value=800.0,
            value_type="monetary",
            description="Cartão alimentação",
        )

        mock_benefit = _make_benefit()
        mock_repo = AsyncMock()
        mock_repo.create = AsyncMock(return_value=mock_benefit)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.company_benefits.CompanyBenefitRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await create_company_benefit(
                benefit=payload,
                company_id=COMPANY_ID,
                db=AsyncMock(),
                current_user=_make_user(),
                gated_company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called, (
            "AuditService.log_action NÃO foi chamado em create_company_benefit — "
            "gap de compliance LGPD/SOX. Fix: adicionar bloco audit após repo.create."
        )
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "company_benefits_update"
        assert call_kwargs.get("company_id") == COMPANY_ID
        meta = call_kwargs.get("metadata", {})
        assert meta.get("operation") == "create"

    @pytest.mark.asyncio
    async def test_create_audit_failure_is_non_blocking(self):
        from app.api.v1.company_benefits import create_company_benefit, CompanyBenefitCreate

        payload = CompanyBenefitCreate(
            name="Gympass",
            category="wellness",
            description="Acesso a academias",
        )

        mock_benefit = _make_benefit("Gympass")
        mock_repo = AsyncMock()
        mock_repo.create = AsyncMock(return_value=mock_benefit)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock(side_effect=RuntimeError("audit DB down"))

        with (
            patch(
                "app.api.v1.company_benefits.CompanyBenefitRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await create_company_benefit(
                benefit=payload,
                company_id=COMPANY_ID,
                db=AsyncMock(),
                current_user=_make_user(),
                gated_company_id=COMPANY_ID,
            )

        assert result.name == "Gympass", (
            "Handler não retornou resultado mesmo com audit falhando — "
            "violou regra 'audit nunca bloqueia o save'"
        )


# ---------------------------------------------------------------------------
# update_company_benefit
# ---------------------------------------------------------------------------

class TestUpdateCompanyBenefitAuditLog:
    """Handler PUT /company/benefits/{id} chama audit log após update."""

    @pytest.mark.asyncio
    async def test_update_calls_audit_log_after_save(self):
        from app.api.v1.company_benefits import update_company_benefit, CompanyBenefitUpdate

        updates = CompanyBenefitUpdate(name="Vale Refeição Plus", value=1000.0)

        mock_benefit = _make_benefit("Vale Refeição Plus")
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_benefit)
        mock_repo.update = AsyncMock(return_value=mock_benefit)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.company_benefits.CompanyBenefitRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await update_company_benefit(
                benefit_id=BENEFIT_ID,
                updates=updates,
                db=AsyncMock(),
                current_user=_make_user(),
                company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called, (
            "AuditService.log_action NÃO foi chamado em update_company_benefit — "
            "gap de compliance LGPD/SOX."
        )
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "company_benefits_update"
        meta = call_kwargs.get("metadata", {})
        assert meta.get("operation") == "update"
        assert meta.get("source") == "rest_put_inline_edit"


# ---------------------------------------------------------------------------
# delete_company_benefit
# ---------------------------------------------------------------------------

class TestDeleteCompanyBenefitAuditLog:
    """Handler DELETE /company/benefits/{id} chama audit log após deleção."""

    @pytest.mark.asyncio
    async def test_soft_delete_calls_audit_log(self):
        from app.api.v1.company_benefits import delete_company_benefit

        mock_benefit = _make_benefit()
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_benefit)
        mock_repo.soft_delete = AsyncMock()

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.company_benefits.CompanyBenefitRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await delete_company_benefit(
                benefit_id=BENEFIT_ID,
                hard_delete=False,
                db=AsyncMock(),
                current_user=_make_user(),
                company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called, (
            "AuditService.log_action NÃO foi chamado em delete_company_benefit — "
            "gap de compliance LGPD/SOX."
        )
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "company_benefits_update"
        meta = call_kwargs.get("metadata", {})
        assert meta.get("operation") == "soft_delete"

    @pytest.mark.asyncio
    async def test_hard_delete_calls_audit_log_with_hard_delete_operation(self):
        from app.api.v1.company_benefits import delete_company_benefit

        mock_benefit = _make_benefit()
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_benefit)
        mock_repo.hard_delete = AsyncMock()

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.company_benefits.CompanyBenefitRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await delete_company_benefit(
                benefit_id=BENEFIT_ID,
                hard_delete=True,
                db=AsyncMock(),
                current_user=_make_user(),
                company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        meta = call_kwargs.get("metadata", {})
        assert meta.get("operation") == "hard_delete"
