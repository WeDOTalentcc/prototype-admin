"""
UserAgentPreferenceService — Sprint J3

Gerencia preferências de auto_confirm por usuário/domínio/action_type.
Integração com HITL: se auto_confirm=True, aprovação automática sem interrupção.

Arquitetura:
- Upsert por (user_id, company_id, domain, action_type)
- Integrado em hitl_service.request_approval() via check_auto_confirm()
- Endpoint: POST /api/v1/user-preferences/agent

Referência: docs/analises/PLANO_IMPLEMENTACAO_GAPS_IA.md → Sprint J3
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.repositories.user_agent_preference_repository import (
    UserAgentPreferenceRepository,
)
from lia_models.user_agent_preference import UserAgentPreference

logger = logging.getLogger(__name__)


class UserAgentPreferenceService:

    @staticmethod
    async def get(
        db: AsyncSession,
        *,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
    ) -> UserAgentPreference | None:
        """Retorna preferência existente ou None."""
        repo = UserAgentPreferenceRepository(db)
        return await repo.get(
            user_id=user_id,
            company_id=company_id,
            domain=domain,
            action_type=action_type,
        )

    @staticmethod
    async def check_auto_confirm(
        db: AsyncSession,
        *,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
    ) -> bool:
        """
        Retorna True se usuário optou por auto_confirm para esta ação.
        Retorna False por padrão (seguro: requer confirmação explícita).
        """
        pref = await UserAgentPreferenceService.get(
            db, user_id=user_id, company_id=company_id,
            domain=domain, action_type=action_type,
        )
        return bool(pref and pref.auto_confirm)

    @staticmethod
    async def upsert(
        db: AsyncSession,
        *,
        user_id: str,
        company_id: str,
        domain: str,
        action_type: str,
        auto_confirm: bool,
    ) -> UserAgentPreference:
        """
        Cria ou atualiza preferência de auto_confirm.
        Upsert por (user_id, company_id, domain, action_type).
        """
        repo = UserAgentPreferenceRepository(db)
        pref = await repo.upsert(
            user_id=user_id,
            company_id=company_id,
            domain=domain,
            action_type=action_type,
            auto_confirm=auto_confirm,
        )
        logger.info(
            "[UserAgentPrefs] user=%s domain=%s action=%s auto_confirm=%s",
            user_id, domain, action_type, auto_confirm,
        )
        return pref

    @staticmethod
    async def list_user_preferences(
        db: AsyncSession,
        *,
        user_id: str,
        company_id: str,
    ) -> list[UserAgentPreference]:
        """Lista todas as preferências de um usuário."""
        repo = UserAgentPreferenceRepository(db)
        return await repo.list_for_user(user_id=user_id, company_id=company_id)
