"""
Sensor permanente: audit log em handlers de write de Tech Stack / Skills Catalog.

Garante que add_skill_to_catalog e sync_tech_stack_to_catalog chamam
AuditService.log_action após o save bem-sucedido.

Estratégia: unit pura — mocka db_service e AuditService, chama o handler
diretamente via pytest-asyncio, verifica que log_action foi chamado com
os campos canônicos esperados.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


COMPANY_ID = "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa"
FAKE_USER_EMAIL = "recrutador@empresa.com"


def _make_user(email: str = FAKE_USER_EMAIL):
    u = MagicMock()
    u.email = email
    u.id = str(uuid.uuid4())
    return u


# ---------------------------------------------------------------------------
# add_skill_to_catalog
# ---------------------------------------------------------------------------

class TestAddSkillToCatalogAuditLog:
    """Handler POST /company/skills-catalog chama audit log após save."""

    @pytest.mark.asyncio
    async def test_add_skill_calls_audit_log_after_save(self):
        """
        Quando add_skill_to_catalog bem-sucedido,
        AuditService.log_action deve ser chamado com action_type='company_tech_stack_update'.
        """
        from app.api.v1.skills_catalog import add_skill_to_catalog, AddSkillRequest

        request = AddSkillRequest(
            skill_name="Python",
            category="Linguagens de Programação",
            default_weight=4,
            default_level="Sênior",
        )

        mock_result = {
            "skill_name": "Python",
            "category": "Linguagens de Programação",
            "subcategory": None,
            "default_weight": 4,
            "default_level": "Sênior",
            "is_required_default": False,
            "created_at": "2026-05-24T00:00:00",
            "updated_at": "2026-05-24T00:00:00",
        }

        mock_db_service = AsyncMock()
        mock_db_service.add_skill_to_catalog = AsyncMock(return_value=mock_result)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.skills_catalog.get_skills_catalog_db_service",
                return_value=mock_db_service,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await add_skill_to_catalog(
                request=request,
                current_user=_make_user(),
                db=AsyncMock(),
                company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called, (
            "AuditService.log_action NÃO foi chamado em add_skill_to_catalog — "
            "gap de compliance LGPD/SOX. Fix: adicionar bloco audit após db_service.add_skill_to_catalog."
        )
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "company_tech_stack_update", (
            f"action_type esperado 'company_tech_stack_update', recebeu {call_kwargs.get('action_type')!r}"
        )
        assert call_kwargs.get("company_id") == COMPANY_ID
        assert call_kwargs.get("target_type") == "company_skills_catalog"

    @pytest.mark.asyncio
    async def test_add_skill_audit_failure_is_non_blocking(self):
        """
        Quando AuditService.log_action lança exceção,
        o handler deve retornar HTTP 200 normalmente (audit nunca bloqueia o save).
        """
        from app.api.v1.skills_catalog import add_skill_to_catalog, AddSkillRequest

        request = AddSkillRequest(
            skill_name="React",
            category="Frontend",
        )
        mock_result = {
            "skill_name": "React",
            "category": "Frontend",
            "subcategory": None,
            "default_weight": 3,
            "default_level": "Intermediário",
            "is_required_default": False,
            "created_at": "2026-05-24T00:00:00",
            "updated_at": "2026-05-24T00:00:00",
        }

        mock_db_service = AsyncMock()
        mock_db_service.add_skill_to_catalog = AsyncMock(return_value=mock_result)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock(side_effect=RuntimeError("audit DB down"))

        with (
            patch(
                "app.api.v1.skills_catalog.get_skills_catalog_db_service",
                return_value=mock_db_service,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await add_skill_to_catalog(
                request=request,
                current_user=_make_user(),
                db=AsyncMock(),
                company_id=COMPANY_ID,
            )

        assert result.skill_name == "React", (
            "Handler não retornou resultado mesmo com audit falhando — "
            "violou regra 'audit nunca bloqueia o save'"
        )


# ---------------------------------------------------------------------------
# sync_tech_stack_to_catalog
# ---------------------------------------------------------------------------

class TestSyncTechStackAuditLog:
    """Handler POST /company/skills-catalog/sync chama audit log após save."""

    @pytest.mark.asyncio
    async def test_sync_calls_audit_log_after_save(self):
        """
        Quando sync_tech_stack_to_catalog bem-sucedido,
        AuditService.log_action deve ser chamado com action_type='company_tech_stack_update'.
        """
        from app.api.v1.skills_catalog import sync_tech_stack_to_catalog, SyncTechStackRequest

        request = SyncTechStackRequest(tech_stack=["Python", "FastAPI", "PostgreSQL"])

        mock_result = {"added": 2, "updated": 1, "skipped": 0, "total_processed": 3}

        mock_db_service = AsyncMock()
        mock_db_service.sync_from_tech_stack = AsyncMock(return_value=mock_result)

        mock_audit_instance = AsyncMock()
        mock_audit_instance.log_action = AsyncMock()

        with (
            patch(
                "app.api.v1.skills_catalog.get_skills_catalog_db_service",
                return_value=mock_db_service,
            ),
            patch(
                "app.shared.compliance.audit_service.AuditService",
                return_value=mock_audit_instance,
            ),
        ):
            result = await sync_tech_stack_to_catalog(
                request=request,
                current_user=_make_user(),
                db=AsyncMock(),
                company_id=COMPANY_ID,
            )

        assert mock_audit_instance.log_action.called, (
            "AuditService.log_action NÃO foi chamado em sync_tech_stack_to_catalog — "
            "gap de compliance LGPD/SOX."
        )
        call_kwargs = mock_audit_instance.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "company_tech_stack_update"
        assert call_kwargs.get("company_id") == COMPANY_ID
        meta = call_kwargs.get("metadata", {})
        assert meta.get("source") == "rest_post_sync_tech_stack"
        assert meta.get("total_techs") == 3
