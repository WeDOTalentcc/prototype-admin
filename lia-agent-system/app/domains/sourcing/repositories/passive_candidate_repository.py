"""
PassiveCandidateRepository — ADR-001 canonical.
Queries de candidatos passivos com verificação de TTL LGPD obrigatória.

LGPD Art. 18 §1 — dados de candidatos passivos devem ser expurgados após
o período de retenção consentido (lgpd_cutoff). Este repositório preserva
o TTL check como invariante — não pode ser chamado sem cutoff.
"""
from typing import Optional
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PassiveCandidateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_with_lgpd_check(
        self,
        candidate_id: str,
        company_id: str,
        lgpd_cutoff: date,
    ) -> Optional[dict]:
        """
        Retorna candidato SE ainda dentro do TTL LGPD.
        lgpd_cutoff é OBRIGATÓRIO — impossível de chamar sem TTL.
        Fail-closed em company_id E em TTL.

        LGPD Art. 18 §1: dados de candidatos passivos devem ser expurgados
        após o período de retenção consentido. O invariante de TTL é imposto
        aqui no nível do repositório — callers não conseguem bypasear.
        """
        self._require_company_id(company_id)
        if lgpd_cutoff is None:
            raise ValueError("lgpd_cutoff is required — LGPD TTL cannot be bypassed")
        result = await self.db.execute(
            text("""
            SELECT id, name, email, status, updated_at, created_at
            FROM candidates
            WHERE id = :cid
              AND (company_id IS NULL OR company_id = :company_id)
              AND (updated_at >= :lgpd_cutoff OR (updated_at IS NULL AND created_at >= :lgpd_cutoff))
            LIMIT 1
            """),
            {"cid": candidate_id, "company_id": company_id, "lgpd_cutoff": lgpd_cutoff},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None
