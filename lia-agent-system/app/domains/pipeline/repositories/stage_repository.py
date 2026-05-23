"""StageRepository — ADR-001 canonical.

Queries para estágios e sub-statuses de recrutamento por tenant.
Migrado de pipeline_tool_registry.py: _wrap_get_stage_sub_statuses,
_wrap_suggest_sub_status (DB lookup path).
Multi-tenancy fail-closed via _require_company_id.

Schema source of truth: libs/models/lia_models/recruitment_stages.py
Tabelas: recruitment_stages, recruitment_sub_statuses.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class StageRepository:
    """Repository canonical com multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_sub_statuses_for_stage(
        self, stage_name: str, company_id: str
    ) -> list[dict]:
        """Lista sub-statuses ativos para uma etapa específica do tenant. Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT rs.name AS stage_name,
                       ss.name AS sub_status_name,
                       ss.display_name,
                       ss.is_default,
                       ss.is_waiting,
                       ss.waiting_for,
                       ss.color,
                       ss.description
                FROM recruitment_stages rs
                JOIN recruitment_sub_statuses ss ON ss.stage_id = rs.id
                WHERE rs.name = :stage_name
                  AND rs.company_id = :company_id
                  AND ss.is_active = TRUE
                ORDER BY ss.sub_status_order
            """),
            {"stage_name": stage_name, "company_id": company_id},
        )
        return [dict(r) for r in result.mappings().all()]

    async def get_default_sub_status(
        self, stage_name: str, company_id: str
    ) -> Optional[dict]:
        """Retorna o sub-status padrão de uma etapa. Fail-closed.

        Usado em _wrap_suggest_sub_status (DB lookup path antes do fallback comportamental).
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT ss.name, ss.display_name
                FROM recruitment_stages rs
                JOIN recruitment_sub_statuses ss ON ss.stage_id = rs.id
                WHERE rs.name = :stage_name
                  AND rs.company_id = :company_id
                  AND ss.is_active = TRUE
                  AND ss.is_default = TRUE
                LIMIT 1
            """),
            {"stage_name": stage_name, "company_id": company_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None
