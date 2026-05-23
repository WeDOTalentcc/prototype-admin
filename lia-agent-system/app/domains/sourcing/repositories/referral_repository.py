"""
ReferralRepository — ADR-001 canonical repository.
Gerencia identificação de connectors (candidatos contratados)
e aprovações HITL para referral requests.

Tabelas:
  candidates — filtro WHERE status=hired AND company_id=:company_id
    cols usados: id, name, email, current_title, technical_skills,
                 years_of_experience, location_city, location_country
  referral_hitl_approvals — PK: request_key (UNIQUE)
    cols: approval_id, request_key, approved_by, channel, vacancy_id,
          company_id, approved_at, status
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ReferralRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_hired_connectors(
        self,
        company_id: str,
        role_filter: Optional[str] = None,
        skills: Optional[list] = None,
        limit: int = 15,
    ) -> list[dict]:
        """
        Retorna candidatos contratados (status=hired) da empresa que podem
        atuar como connectors para indicação. Fail-closed em company_id.
        Limita a 50 registros para evitar payloads excessivos.
        """
        self._require_company_id(company_id)
        limit = min(int(limit), 50)
        conditions = [
            "c.status = hired",
            "c.company_id = :company_id",
        ]
        params: dict = {"company_id": company_id, "lim": limit}

        if role_filter:
            conditions.append("c.current_title ILIKE :role_pattern")
            params["role_pattern"] = f"%{role_filter}%"

        if skills and isinstance(skills, list) and len(skills) > 0:
            conditions.append("c.technical_skills && :skills_arr")
            params["skills_arr"] = skills

        where_clause = " AND ".join(conditions)
        # ADR-001-EXEMPT: dynamic WHERE clause for optional filters (role/skills);
        # table is candidates (Rails-owned schema), no inline ORM model available.
        # company_id always in WHERE — multi-tenancy enforced.
        result = await self.db.execute(
            text(
                f"SELECT c.id, c.name, c.email, c.current_title,"  # noqa: S608
                f" c.technical_skills, c.years_of_experience,"
                f" c.location_city, c.location_country"
                f" FROM candidates c"
                f" WHERE {where_clause}"
                f" ORDER BY c.years_of_experience DESC NULLS LAST"
                f" LIMIT :lim"
            ),
            params,
        )
        rows = result.mappings().fetchall()
        return [dict(r) for r in rows]

    async def upsert_hitl_approval(
        self,
        request_key: str,
        company_id: str,
        approved_by: str = "recruiter",
        channel: str = "email",
        vacancy_id: Optional[str] = None,
        approval_id: Optional[str] = None,
    ) -> dict:
        """
        Persiste aprovação HITL para referral (ON CONFLICT request_key UPDATE).
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        import uuid as _uuid
        appr_id = approval_id or str(_uuid.uuid4())
        now = datetime.utcnow()
        await self.db.execute(
            text("""
                INSERT INTO referral_hitl_approvals (
                    approval_id, request_key, approved_by,
                    channel, vacancy_id, company_id, approved_at, status
                ) VALUES (
                    :appr_id, :req_key, :approver,
                    :channel, :vac_id, :co_id, :now, approved
                )
                ON CONFLICT (request_key) DO UPDATE
                    SET approval_id = EXCLUDED.approval_id,
                        approved_by = EXCLUDED.approved_by,
                        approved_at = EXCLUDED.approved_at,
                        status = approved
            """),
            {
                "appr_id": appr_id,
                "req_key": request_key,
                "approver": approved_by,
                "channel": channel,
                "vac_id": vacancy_id or None,
                "co_id": company_id,
                "now": now,
            },
        )
        await self.db.commit()
        return {"approval_id": appr_id, "request_key": request_key}

    async def get_hitl_approval(
        self, request_key: str, company_id: str
    ) -> Optional[dict]:
        """
        Verifica aprovação HITL por request_key com filtro company_id.
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT approval_id, request_key, status,
                       approved_by, approved_at, channel, vacancy_id
                FROM referral_hitl_approvals
                WHERE request_key = :req_key
                  AND company_id = :company_id
                LIMIT 1
            """),
            {"req_key": request_key, "company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None
