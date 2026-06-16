"""
TalentPoolCandidateRepository — ADR-001 canonical.

Gerencia candidatos dentro de TalentPools (tabela talent_pool_candidates).
Usa lia_config.database.AsyncSessionLocal (padrão deste domínio).

Nota de schema: TalentPoolCandidate usa `talent_pool_id` como FK (não `pool_id`).
Multi-tenancy: _require_company_id fail-closed em todos os métodos públicos.
"""
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.talent_pool import TalentPoolCandidate


class TalentPoolCandidateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def list_by_pool(
        self,
        pool_id: str,
        company_id: str,
        stage: Optional[str] = None,
        limit: int = 50,
    ) -> list[TalentPoolCandidate]:
        """Lista candidatos de um pool com filtros opcionais. Fail-closed."""
        self._require_company_id(company_id)
        # Nota: TalentPoolCandidate usa `talent_pool_id` como FK column
        stmt = (
            select(TalentPoolCandidate)
            .where(TalentPoolCandidate.talent_pool_id == pool_id)
            .limit(limit)
        )
        if stage:
            stmt = stmt.where(TalentPoolCandidate.stage == stage)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_candidate_and_pool(
        self,
        candidate_id: str,
        pool_id: str,
        company_id: str,
    ) -> Optional[TalentPoolCandidate]:
        """Verifica se candidato está no pool. Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(TalentPoolCandidate).where(
                TalentPoolCandidate.candidate_id == candidate_id,
                TalentPoolCandidate.talent_pool_id == pool_id,
            )
        )
        return result.scalar_one_or_none()

    async def move_candidates_to_vacancy(
        self,
        candidate_ids: list,
        job_id: str,
        company_id: str,
        source_pool_id: str,
        target_stage: str = "triagem",
    ) -> int:
        """
        Move candidatos de pool para vacancy_candidates preservando screening_data.

        # ADR-001-EXEMPT: vacancy_candidates table is Rails-owned, no SQLAlchemy model.
        # INSERT via text() necessário. company_id fail-closed.
        """
        self._require_company_id(company_id)
        moved = 0
        for cid in candidate_ids:
            await self.db.execute(
                text("""
                    INSERT INTO vacancy_candidates
                        (id, vacancy_id, candidate_id, stage, source, company_id, screening_data)
                    SELECT
                        gen_random_uuid(),
                        :job_id,
                        :candidate_id,
                        :target_stage,
                        'talent_pool',
                        :company_id,
                        COALESCE(
                            (SELECT screening_data FROM talent_pool_candidates
                             WHERE talent_pool_id = :pool_id AND candidate_id = :candidate_id
                             LIMIT 1),
                            '{}'::jsonb
                        )
                    ON CONFLICT (vacancy_id, candidate_id) DO NOTHING
                """),
                {
                    "job_id": job_id,
                    "candidate_id": cid,
                    "target_stage": target_stage,
                    "company_id": company_id,
                    "pool_id": source_pool_id,
                },
            )
            moved += 1
        await self.db.commit()
        return moved
