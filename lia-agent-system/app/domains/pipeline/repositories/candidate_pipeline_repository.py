"""CandidatePipelineRepository — ADR-001 canonical.

Queries para perfil de candidato, salário e telefone no contexto
do Pipeline Transition Agent (pipeline_tool_registry.py).

Migrado de pipeline_tool_registry.py: _wrap_get_candidate_profile,
_wrap_get_candidate_salary_info, _get_candidate_phone helper.
Multi-tenancy fail-closed via _require_company_id.
company_id IS NULL preserva talent pool global sharing (Pearch AI / merge.dev).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CandidatePipelineRepository:
    """Repository canonical com multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_profile(self, candidate_id: str, company_id: str) -> Optional[dict]:
        """Retorna perfil completo do candidato (PII gate tenant-isolated). Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT c.id, c.name, c.email, c.phone, c.linkedin_url,
                       c.current_title, c.current_company,
                       c.technical_skills, c.soft_skills,
                       c.location_city, c.location_state,
                       c.salary_expectation_clt, c.salary_expectation_pj,
                       c.work_model_preference, c.is_remote,
                       c.source, c.resume_url
                FROM candidates c
                WHERE c.id = :cid
                  AND (c.company_id IS NULL OR c.company_id = :company_id)
                LIMIT 1
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        profile = dict(row)
        for k, v in profile.items():
            if isinstance(v, datetime):
                profile[k] = v.isoformat()
        return profile

    async def get_salary_info(self, candidate_id: str, company_id: str) -> Optional[dict]:
        """Retorna informações salariais do candidato (PII gate). Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT c.salary_expectation_clt, c.salary_expectation_pj,
                       c.current_title, c.current_company
                FROM candidates c
                WHERE c.id = :cid
                  AND (c.company_id IS NULL OR c.company_id = :company_id)
                LIMIT 1
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        row = result.mappings().first()
        if not row:
            return None
        return dict(row)

    async def get_phone_by_email(self, email: str, company_id: str) -> Optional[str]:
        """Retorna telefone do candidato por email (para envio de comunicação). Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT phone FROM candidates
                WHERE email = :email
                  AND (company_id IS NULL OR company_id = :company_id)
                LIMIT 1
            """),
            {"email": email, "company_id": company_id},
        )
        row = result.mappings().first()
        return str(row["phone"]) if row and row.get("phone") else None

    async def get_phone_by_interview(self, interview_id: str, company_id: str) -> Optional[str]:
        """Retorna telefone do candidato via FK de entrevista. Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT c.phone FROM candidates c
                JOIN interviews i ON i.candidate_id = c.id
                WHERE i.id::text = :iid
                  AND (c.company_id IS NULL OR c.company_id = :company_id)
                LIMIT 1
            """),
            {"iid": interview_id, "company_id": company_id},
        )
        row = result.mappings().first()
        return str(row["phone"]) if row and row.get("phone") else None
