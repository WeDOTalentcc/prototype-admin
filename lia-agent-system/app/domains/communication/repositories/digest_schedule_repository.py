"""Repository: DigestSchedulePreference — per-user + company-default digest frequency.

ADR-001 compliant: toda query SQL vive aqui.

Precedência canônica (Decisão 3):
  1. digest_schedule_preferences WHERE user_id = :user_id (override pessoal)
  2. digest_schedule_preferences WHERE user_id IS NULL   (company default)
  3. HiringPolicy.communication_rules.briefing_frequency (fallback — briefing_dispatch)
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from libs.models.lia_models.digest_schedule import DigestSchedulePreference


class DigestScheduleRepository:
    """CRUD + precedence lookup for DigestSchedulePreference rows."""

    def _require_company_id(self, company_id: str) -> None:
        """Multi-tenancy fail-closed — bloqueia operação sem company_id válido."""
        if not company_id or not company_id.strip():
            raise ValueError("company_id é obrigatório — operação bloqueada (multi-tenancy)")

    async def get_user_preference(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        user_id: str,
    ) -> Optional[DigestSchedulePreference]:
        """Busca override pessoal do usuário. Retorna None se não existe."""
        self._require_company_id(company_id)
        result = await db.execute(
            select(DigestSchedulePreference).where(
                and_(
                    DigestSchedulePreference.company_id == company_id,
                    DigestSchedulePreference.user_id == user_id,
                    DigestSchedulePreference.is_active.is_(True),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_company_default(
        self,
        db: AsyncSession,
        *,
        company_id: str,
    ) -> Optional[DigestSchedulePreference]:
        """Busca o padrão da empresa (user_id IS NULL). Retorna None se não existe."""
        self._require_company_id(company_id)
        result = await db.execute(
            select(DigestSchedulePreference).where(
                and_(
                    DigestSchedulePreference.company_id == company_id,
                    DigestSchedulePreference.user_id.is_(None),
                    DigestSchedulePreference.is_active.is_(True),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_effective(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        user_id: str,
    ) -> tuple[Optional[DigestSchedulePreference], str]:
        """Retorna a preferência efetiva e a fonte ('user' | 'company_default' | 'none').

        Precedência: user > company_default.
        """
        self._require_company_id(company_id)
        user_pref = await self.get_user_preference(db, company_id=company_id, user_id=user_id)
        if user_pref:
            return user_pref, "user"
        company_default = await self.get_company_default(db, company_id=company_id)
        if company_default:
            return company_default, "company_default"
        return None, "none"

    async def upsert_user_preference(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        user_id: str,
        frequency: str,
        preferred_time_morning: Optional[str] = None,
        preferred_time_afternoon: Optional[str] = None,
        quiet_hours_start: Optional[int] = None,
        quiet_hours_end: Optional[int] = None,
    ) -> DigestSchedulePreference:
        """Cria ou atualiza override pessoal do usuário."""
        self._require_company_id(company_id)
        existing = await self.get_user_preference(db, company_id=company_id, user_id=user_id)
        if existing:
            existing.frequency = frequency
            existing.preferred_time_morning = preferred_time_morning
            existing.preferred_time_afternoon = preferred_time_afternoon
            existing.quiet_hours_start = quiet_hours_start
            existing.quiet_hours_end = quiet_hours_end
            existing.is_active = True
            row = existing
        else:
            row = DigestSchedulePreference(
                id=str(uuid.uuid4()),
                company_id=company_id,
                user_id=user_id,
                frequency=frequency,
                preferred_time_morning=preferred_time_morning,
                preferred_time_afternoon=preferred_time_afternoon,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )
            db.add(row)
        await db.flush()
        return row

    async def upsert_company_default(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        frequency: str,
        preferred_time_morning: Optional[str] = None,
        preferred_time_afternoon: Optional[str] = None,
        quiet_hours_start: Optional[int] = None,
        quiet_hours_end: Optional[int] = None,
    ) -> DigestSchedulePreference:
        """Cria ou atualiza o padrão da empresa (user_id IS NULL)."""
        self._require_company_id(company_id)
        existing = await self.get_company_default(db, company_id=company_id)
        if existing:
            existing.frequency = frequency
            existing.preferred_time_morning = preferred_time_morning
            existing.preferred_time_afternoon = preferred_time_afternoon
            existing.quiet_hours_start = quiet_hours_start
            existing.quiet_hours_end = quiet_hours_end
            existing.is_active = True
            row = existing
        else:
            row = DigestSchedulePreference(
                id=str(uuid.uuid4()),
                company_id=company_id,
                user_id=None,  # company default
                frequency=frequency,
                preferred_time_morning=preferred_time_morning,
                preferred_time_afternoon=preferred_time_afternoon,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )
            db.add(row)
        await db.flush()
        return row

    async def delete_user_preference(
        self,
        db: AsyncSession,
        *,
        company_id: str,
        user_id: str,
    ) -> bool:
        """Remove override pessoal (soft delete via is_active=False). Retorna True se existia."""
        self._require_company_id(company_id)
        existing = await self.get_user_preference(db, company_id=company_id, user_id=user_id)
        if not existing:
            return False
        existing.is_active = False
        await db.flush()
        return True
