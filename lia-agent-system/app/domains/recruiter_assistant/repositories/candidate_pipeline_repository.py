"""CandidatePipelineRepository — pipeline candidate queries (W1-004-B).

Cobre queries de candidatos no pipeline kanban do recruiter_assistant.
Separado de RecruiterMetricsRepository por concern:
- Este repo toca PII de candidatos (tabela candidates + candidate_education).
- RecruiterMetricsRepository só toca vacancy_candidates (métricas agregadas
  sem PII direto).

W1-004-B (2026-05-23): Migração dos 11 blocos SQL inline de
`kanban_tool_registry.py` para repositories canonicos (ADR-001).

Multi-tenancy fail-closed via `_require_company_id` em todo método público.
LGPD: dados de candidates incluem PII (name, email, skills, education).
Acesso auditado via tool_handler no caller (kanban_tool_registry).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CandidatePipelineRepository:
    """Repository para queries de candidatos no pipeline kanban.

    Métodos canonical:
    - `list_candidates_in_stage`               — candidatos por stage (com PII básico)
    - `get_aging_candidates`                   — candidatos estagnados
    - `get_candidates_for_movement_suggestion` — candidatos elegíveis para sugestão
    - `get_candidate_full_profile`             — perfil completo (PII — LGPD)

    Usage:
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        async with AsyncSessionLocal() as session:
            repo = CandidatePipelineRepository(session)
            candidates, total = await repo.list_candidates_in_stage(
                vacancy_id=vid, company_id=cid, stage="triagem", limit=20
            )
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> str:
        """Multi-tenancy fail-closed gate (ADR-001 + REGRA 6)."""
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy fail-closed). "
                "CandidatePipelineRepository never accepts cross-tenant queries."
            )
        return str(company_id)

    async def list_candidates_in_stage(
        self,
        *,
        vacancy_id: str,
        company_id: str,
        stage: str,
        limit: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Lista candidatos em um stage com contagem total.

        PII fields retornados: name, current_title, technical_skills.

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).
            stage: nome do stage (partial match via ILIKE).
            limit: número máximo de candidatos a retornar.

        Returns:
            tuple (candidates_list, total_count)
        """
        company_id = self._require_company_id(company_id)

        rows_result = await self.db.execute(
            text("""
                SELECT vc.candidate_id, vc.stage, vc.status, vc.lia_score, vc.match_percentage,
                       vc.updated_at,
                       EXTRACT(DAY FROM NOW() - vc.updated_at)::int AS days_in_stage,
                       c.name, c.current_title, c.technical_skills
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.stage ILIKE :stage_val
                  AND (:vid = '' OR vc.vacancy_id::text = :vid)
                  AND vc.company_id = :cid
                ORDER BY vc.lia_score DESC NULLS LAST
                LIMIT :lim
            """),
            {"stage_val": f"%{stage}%", "vid": vacancy_id, "cid": company_id, "lim": limit},
        )
        candidates = []
        for row in rows_result.mappings():
            candidates.append({
                "id": str(row["candidate_id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "skills": row["technical_skills"] or [],
                "stage": row["stage"],
                "status": row["status"],
                "lia_score": row["lia_score"],
                "match_percentage": row["match_percentage"],
                "days_in_stage": int(row["days_in_stage"] or 0),
            })

        count_result = await self.db.execute(
            text("""
                SELECT COUNT(*) AS total FROM vacancy_candidates
                WHERE stage ILIKE :stage_val
                  AND (:vid = '' OR vacancy_id::text = :vid)
                  AND company_id = :cid
            """),
            {"stage_val": f"%{stage}%", "vid": vacancy_id, "cid": company_id},
        )
        total = int((count_result.mappings().first() or {}).get("total", len(candidates)))

        return candidates, total

    async def get_aging_candidates(
        self,
        *,
        vacancy_id: str,
        company_id: str,
        threshold_days: int,
        stage: str = "",
    ) -> list[dict[str, Any]]:
        """Candidatos estagnados acima do threshold de dias.

        PII fields retornados: name, current_title.

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).
            threshold_days: mínimo de dias para considerar estagnado.
            stage: filtro de stage (string vazia = todos).

        Returns:
            list de dicts com candidate_id, name, current_title, stage, days_stuck, lia_score.
        """
        company_id = self._require_company_id(company_id)

        result = await self.db.execute(
            text("""
                SELECT vc.candidate_id, vc.stage, vc.status, vc.lia_score,
                       EXTRACT(DAY FROM NOW() - vc.updated_at)::int AS days_stuck,
                       c.name, c.current_title
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.updated_at < NOW() - MAKE_INTERVAL(days => :threshold)
                  AND vc.status NOT IN ('rejected', 'hired')
                  AND (:stage = '' OR vc.stage ILIKE :stage_val)
                  AND (:vid = '' OR vc.vacancy_id::text = :vid)
                  AND vc.company_id = :cid
                ORDER BY days_stuck DESC
                LIMIT 50
            """),
            {
                "threshold": threshold_days,
                "stage": stage,
                "stage_val": f"%{stage}%",
                "vid": vacancy_id,
                "cid": company_id,
            },
        )
        aging = []
        for row in result.mappings():
            aging.append({
                "id": str(row["candidate_id"]),
                "name": row["name"],
                "current_title": row["current_title"],
                "stage": row["stage"],
                "days_stuck": int(row["days_stuck"] or 0),
                "lia_score": row["lia_score"],
            })
        return aging

    async def get_candidates_for_movement_suggestion(
        self,
        *,
        vacancy_id: str,
        company_id: str,
        stage: str = "",
    ) -> list[dict[str, Any]]:
        """Candidatos elegíveis para sugestão de movimento de stage.

        PII fields retornados: name.
        Candidatos com status rejected/hired são excluídos.

        Args:
            vacancy_id: UUID da vaga (string vazia = todas as vagas).
            company_id: tenant uuid (REQUIRED, fail-closed).
            stage: stage de origem para filtrar (string vazia = todos).

        Returns:
            list de dicts com candidate_id, name, stage, lia_score, match_percentage,
            days_in_stage. Ordenados por lia_score DESC.
        """
        company_id = self._require_company_id(company_id)

        result = await self.db.execute(
            text("""
                SELECT vc.candidate_id, vc.stage, vc.lia_score, vc.match_percentage,
                       EXTRACT(DAY FROM NOW() - vc.updated_at)::int AS days_in_stage,
                       c.name
                FROM vacancy_candidates vc
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE vc.status NOT IN ('rejected', 'hired')
                  AND (:stage = '' OR vc.stage ILIKE :stage_val)
                  AND (:vid = '' OR vc.vacancy_id::text = :vid)
                  AND vc.company_id = :cid
                ORDER BY vc.lia_score DESC NULLS LAST
                LIMIT 30
            """),
            {
                "stage": stage,
                "stage_val": f"%{stage}%",
                "vid": vacancy_id,
                "cid": company_id,
            },
        )
        rows = []
        for row in result.mappings():
            rows.append({
                "candidate_id": str(row["candidate_id"]),
                "name": row["name"],
                "stage": row["stage"],
                "lia_score": row["lia_score"] or 0,
                "match_percentage": row["match_percentage"],
                "days_in_stage": int(row["days_in_stage"] or 0),
            })
        return rows

    async def get_candidate_full_profile(
        self,
        *,
        candidate_id: str,
        company_id: str,
    ) -> dict[str, Any] | None:
        """Perfil completo do candidato incluindo educação.

        LGPD NOTICE: retorna campos PII (name, email, salary, gender, linkedin_url).
        Acesso deve ser auditado pelo caller (tool_handler + AuditService).

        Multi-tenancy: company_id IS NULL OR = :company_id reflete o modelo de
        candidatos globais (pool) que podem pertencer a múltiplas empresas.
        Candidatos com company_id = NULL são do pool global — acesso é permitido
        para qualquer tenant autenticado (recrutador view read-only).

        Args:
            candidate_id: UUID do candidato.
            company_id: tenant uuid (REQUIRED, fail-closed).

        Returns:
            dict com perfil completo ou None se não encontrado.
        """
        company_id = self._require_company_id(company_id)
        if not candidate_id:
            raise ValueError("candidate_id is required")

        profile_result = await self.db.execute(
            text("""
                SELECT id, name, email, current_title, current_company,
                       seniority_level, years_of_experience,
                       technical_skills, soft_skills, certifications,
                       location_city, location_state, location_country,
                       lia_score, skills_match_percentage,
                       status, is_active, linkedin_url,
                       self_introduction, work_history, languages,
                       salary_expectation_clt, salary_expectation_pj,
                       work_model_preference, is_remote, willing_to_relocate,
                       gender
                FROM candidates
                WHERE id = :cid
                  AND (company_id IS NULL OR company_id = :company_id)
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        data = profile_result.mappings().first()
        if not data:
            return None

        edu_result = await self.db.execute(
            text("""
                SELECT institution, degree, field_of_study, start_year, end_year, is_current
                FROM candidate_education
                WHERE candidate_id = :cid
                ORDER BY end_year DESC NULLS FIRST, start_year DESC NULLS FIRST
            """),
            {"cid": candidate_id},
        )
        education = [
            {
                "institution": r["institution"],
                "degree": r["degree"],
                "field_of_study": r["field_of_study"],
                "period": f"{r['start_year'] or '?'} - {'atual' if r['is_current'] else (r['end_year'] or '?')}",
            }
            for r in edu_result.mappings()
        ]

        return {
            "candidate_id": str(data["id"]),
            "name": data["name"],
            "email": data["email"],
            "current_title": data["current_title"],
            "current_company": data["current_company"],
            "seniority_level": data["seniority_level"],
            "years_of_experience": data["years_of_experience"],
            "technical_skills": data["technical_skills"] or [],
            "soft_skills": data["soft_skills"] or [],
            "certifications": data["certifications"] or [],
            "location": f"{data['location_city'] or ''}, {data['location_country'] or ''}".strip(", "),
            "lia_score": data["lia_score"],
            "match_percentage": data["skills_match_percentage"],
            "status": data["status"],
            "linkedin_url": data["linkedin_url"],
            "summary": data["self_introduction"],
            "languages": data["languages"],
            "work_history": data["work_history"] or [],
            "education": education,
            "salary_expectation_clt": data["salary_expectation_clt"],
            "salary_expectation_pj": data["salary_expectation_pj"],
            "work_model": data["work_model_preference"],
            "is_remote": data["is_remote"],
            "willing_to_relocate": data["willing_to_relocate"],
            "gender": data["gender"],
            "profile_loaded": True,
        }
