"""
Comparative Analysis Service — Compare interview performance across candidates.

Compares a candidate's interview WSI scores against three cohorts:
1. Vacancy peers — other candidates interviewed for the same vacancy
2. Hired top performers — candidates hired in similar roles with high WSI
3. Triaged high scorers — candidates who scored well in WSI screening

Each cohort has explicit provenance in the response.
Enforces tenant isolation via mandatory company_id.
"""
import logging
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_intelligence.repositories.interview_repository import (
    InterviewRepository,
)
from app.domains.interview_intelligence.services.interview_wsi_service import (
    interview_wsi_service,
)
from app.models.interview import Interview

logger = logging.getLogger(__name__)


class ComparativeAnalysisService:

    async def compare(
        self,
        interview_id: str,
        db: AsyncSession,
        company_id: str,
    ) -> dict[str, Any]:
        if not company_id:
            return {"success": False, "error": "company_id is required for tenant isolation"}

        _ii_repo = InterviewRepository(db)
        interview = await _ii_repo.get_for_company(
            interview_id=interview_id, company_id=company_id
        )
        if not interview:
            return {"success": False, "error": "Interview not found"}

        if not interview.transcript or len(interview.transcript.strip()) < 50:
            return {"success": False, "error": "Transcript too short or missing"}

        candidate_wsi = await interview_wsi_service.analyze(
            interview_id, db, company_id=company_id
        )
        if not candidate_wsi.get("success"):
            return {"success": False, "error": "WSI analysis failed for this candidate"}

        vacancy_peers = await self._get_vacancy_peers(
            db, interview, company_id, interview_id
        )
        vacancy_scores = await self._analyze_cohort(vacancy_peers, db, company_id)

        hired_top = await self._get_hired_top_performers(
            db, interview, company_id, interview_id
        )
        hired_scores = await self._analyze_cohort(hired_top, db, company_id)

        triaged_high = await self._get_triaged_high_scorers(
            db, interview, company_id, interview_id
        )
        triaged_scores = await self._analyze_cohort(triaged_high, db, company_id)

        all_scores = vacancy_scores + hired_scores + triaged_scores

        ranking = self._build_ranking(candidate_wsi, all_scores)
        benchmarks = self._compute_benchmarks(candidate_wsi, all_scores)

        return {
            "success": True,
            "interview_id": interview_id,
            "candidate_wsi_score": candidate_wsi["wsi_score"],
            "cohorts": {
                "vacancy_peers": {
                    "count": len(vacancy_scores),
                    "provenance": "Candidatos entrevistados para a mesma vaga",
                    "scores": vacancy_scores[:5],
                },
                "hired_top_performers": {
                    "count": len(hired_scores),
                    "provenance": "Candidatos contratados (status=hired) em vagas similares com lia_score >= 3.5",
                    "scores": hired_scores[:5],
                },
                "triaged_high_scorers": {
                    "count": len(triaged_scores),
                    "provenance": "Candidatos com alta pontuação na triagem (lia_score >= 3.5) para a mesma vaga",
                    "scores": triaged_scores[:5],
                },
            },
            "ranking": ranking,
            "benchmarks": benchmarks,
            "top_performers": self._identify_top_performers(all_scores),
            "comparative_insights": self._generate_insights(
                candidate_wsi, all_scores, ranking,
                vacancy_count=len(vacancy_scores),
                hired_count=len(hired_scores),
            ),
        }

    async def _analyze_cohort(
        self,
        interviews: list[Interview],
        db: AsyncSession,
        company_id: str,
    ) -> list[dict[str, Any]]:
        scores: list[dict[str, Any]] = []
        for peer in interviews:
            try:
                peer_analysis = await interview_wsi_service.analyze(
                    str(peer.id), db, company_id=company_id
                )
                if peer_analysis.get("success"):
                    scores.append({
                        "interview_id": str(peer.id),
                        "candidate_id": str(peer.candidate_id) if peer.candidate_id else None,
                        "candidate_name": peer.candidate_name,
                        "wsi_score": peer_analysis["wsi_score"],
                        "technical_score": peer_analysis["technical_score"],
                        "behavioral_score": peer_analysis["behavioral_score"],
                        "cultural_score": peer_analysis["cultural_score"],
                        "recommendation": peer_analysis["recommendation"],
                    })
            except Exception as exc:
                logger.debug("Skipping peer %s: %s", peer.id, exc)
        return scores

    async def _get_vacancy_peers(
        self,
        db: AsyncSession,
        interview: Interview,
        company_id: str,
        exclude_id: str,
    ) -> list[Interview]:
        if not interview.job_vacancy_id:
            return []

        _ii_repo = InterviewRepository(db)
        return await _ii_repo.list_vacancy_peers_with_transcript(
            job_vacancy_id=interview.job_vacancy_id,
            company_id=company_id,
            exclude_id=exclude_id,
            limit=20,
        )

    async def _get_hired_top_performers(
        self,
        db: AsyncSession,
        interview: Interview,
        company_id: str,
        exclude_id: str,
    ) -> list[Interview]:
        try:
            from lia_models.job_vacancy import JobVacancy
            from lia_models.candidate import VacancyCandidate

            if not interview.job_vacancy_id:
                return []

            # ADR-001-EXEMPT: bespoke cross-domain column-only reads (JobVacancy.title,
            # JobVacancy.id, VacancyCandidate.candidate_id) used solely to build the
            # `hired_ids` filter for the Interview cohort below. Wrapping each of these
            # ad-hoc selects in a foreign repo would create single-callsite methods with
            # no other consumers. The Interview cohort read itself uses the repo.
            jv_result = await db.execute(
                select(JobVacancy.title).where(
                    and_(
                        JobVacancy.id == interview.job_vacancy_id,
                        JobVacancy.company_id == company_id,
                    )
                )
            )
            job_title_row = jv_result.scalar_one_or_none()
            if not job_title_row:
                return []

            job_title = str(job_title_row).lower()
            title_words = [w for w in job_title.split() if len(w) > 3][:3]

            if not title_words:
                return []

            title_filters = [JobVacancy.title.ilike(f"%{w}%") for w in title_words]

            # ADR-001-EXEMPT: see comment above (cross-domain column-only ad-hoc query).
            similar_vacancy_ids = await db.execute(
                select(JobVacancy.id).where(
                    and_(
                        or_(*title_filters),
                        JobVacancy.company_id == company_id,
                    )
                ).limit(20)
            )
            similar_ids = [r[0] for r in similar_vacancy_ids.all()]
            if not similar_ids:
                return []

            # ADR-001-EXEMPT: see comment above (cross-domain column-only ad-hoc query).
            hired_candidate_ids = await db.execute(
                select(VacancyCandidate.candidate_id).where(
                    and_(
                        VacancyCandidate.vacancy_id.in_(similar_ids),
                        VacancyCandidate.company_id == company_id,
                        VacancyCandidate.status == "hired",
                        VacancyCandidate.lia_score >= 3.5,
                    )
                ).limit(10)
            )
            hired_ids = [r[0] for r in hired_candidate_ids.all()]
            if not hired_ids:
                return []

            _ii_repo = InterviewRepository(db)
            return await _ii_repo.list_with_transcript_for_candidates(
                candidate_ids=list(hired_ids),
                company_id=company_id,
                exclude_id=exclude_id,
                limit=10,
            )
        except Exception as exc:
            logger.debug("Failed to get hired top performers: %s", exc)
            return []

    async def _get_triaged_high_scorers(
        self,
        db: AsyncSession,
        interview: Interview,
        company_id: str,
        exclude_id: str,
    ) -> list[Interview]:
        try:
            from lia_models.candidate import VacancyCandidate

            if not interview.job_vacancy_id:
                return []

            # ADR-001-EXEMPT: cross-domain column-only ad-hoc query
            # (VacancyCandidate.candidate_id) used solely to build the `high_scorer_ids`
            # filter for the Interview cohort below. Single-callsite, no leverage in repo.
            vc_result = await db.execute(
                select(VacancyCandidate.candidate_id).where(
                    and_(
                        VacancyCandidate.vacancy_id == interview.job_vacancy_id,
                        VacancyCandidate.company_id == company_id,
                        VacancyCandidate.lia_score >= 3.5,
                    )
                ).limit(10)
            )
            high_scorer_ids = [r[0] for r in vc_result.all()]
            if not high_scorer_ids:
                return []

            _ii_repo = InterviewRepository(db)
            return await _ii_repo.list_with_transcript_for_candidates(
                candidate_ids=list(high_scorer_ids),
                company_id=company_id,
                exclude_id=exclude_id,
                limit=10,
            )
        except Exception as exc:
            logger.debug("Failed to get triaged high scorers: %s", exc)
            return []

    def _build_ranking(
        self,
        candidate_wsi: dict[str, Any],
        all_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        scores_list = [candidate_wsi["wsi_score"]] + [
            p["wsi_score"] for p in all_scores
        ]
        scores_list.sort(reverse=True)

        position = scores_list.index(candidate_wsi["wsi_score"]) + 1
        total = len(scores_list)
        percentile = round((1 - (position - 1) / max(total, 1)) * 100, 1)

        return {
            "position": position,
            "total_candidates": total,
            "percentile": percentile,
            "tier": (
                "top_10" if percentile >= 90
                else "top_25" if percentile >= 75
                else "top_50" if percentile >= 50
                else "bottom_50"
            ),
        }

    def _compute_benchmarks(
        self,
        candidate_wsi: dict[str, Any],
        all_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not all_scores:
            return {
                "avg_wsi": candidate_wsi["wsi_score"],
                "max_wsi": candidate_wsi["wsi_score"],
                "min_wsi": candidate_wsi["wsi_score"],
                "candidate_vs_avg": 0.0,
                "dimensions": {},
            }

        wsi_scores = [p["wsi_score"] for p in all_scores]
        avg_wsi = round(sum(wsi_scores) / len(wsi_scores), 2)
        max_wsi = round(max(wsi_scores), 2)
        min_wsi = round(min(wsi_scores), 2)

        dimensions: dict[str, dict[str, float]] = {}
        for dim in ("technical_score", "behavioral_score", "cultural_score"):
            dim_scores = [p[dim] for p in all_scores if p.get(dim) is not None]
            if dim_scores:
                dim_avg = round(sum(dim_scores) / len(dim_scores), 2)
                dimensions[dim] = {
                    "candidate": round(candidate_wsi.get(dim, 0), 2),
                    "peer_avg": dim_avg,
                    "delta": round(candidate_wsi.get(dim, 0) - dim_avg, 2),
                }

        return {
            "avg_wsi": avg_wsi,
            "max_wsi": max_wsi,
            "min_wsi": min_wsi,
            "candidate_vs_avg": round(candidate_wsi["wsi_score"] - avg_wsi, 2),
            "dimensions": dimensions,
        }

    def _identify_top_performers(
        self, all_scores: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        sorted_peers = sorted(
            all_scores, key=lambda p: p["wsi_score"], reverse=True
        )
        return sorted_peers[:3]

    def _generate_insights(
        self,
        candidate_wsi: dict[str, Any],
        all_scores: list[dict[str, Any]],
        ranking: dict[str, Any],
        vacancy_count: int = 0,
        hired_count: int = 0,
    ) -> list[str]:
        insights: list[str] = []

        if not all_scores:
            insights.append(
                "Primeiro candidato entrevistado para esta vaga — "
                "comparativo será enriquecido com mais entrevistas."
            )
            return insights

        delta = ranking.get("percentile", 50)
        if delta >= 90:
            insights.append(
                f"Candidato no top 10% (percentil {delta}) — "
                "performance excepcional comparada aos demais."
            )
        elif delta >= 75:
            insights.append(
                f"Candidato no top 25% (percentil {delta}) — "
                "acima da média do grupo."
            )
        elif delta >= 50:
            insights.append(
                f"Candidato na metade superior (percentil {delta})."
            )
        else:
            insights.append(
                f"Candidato abaixo da mediana (percentil {delta}) — "
                "considerar gaps identificados."
            )

        if hired_count > 0:
            insights.append(
                f"Comparado com {hired_count} profissionais contratados em vagas similares."
            )

        if vacancy_count > 0:
            insights.append(
                f"Comparado com {vacancy_count} candidatos para a mesma vaga."
            )

        tech = candidate_wsi.get("technical_score", 0)
        beh = candidate_wsi.get("behavioral_score", 0)
        if tech > beh + 1:
            insights.append(
                "Perfil predominantemente técnico — "
                "competências comportamentais precisam de mais evidências."
            )
        elif beh > tech + 1:
            insights.append(
                "Forte perfil comportamental — "
                "avaliar profundidade técnica em próxima etapa."
            )

        return insights


comparative_analysis_service = ComparativeAnalysisService()
