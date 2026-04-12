"""
Comparative Analysis Service — Compare interview performance across candidates.

Compares a candidate's interview WSI scores against:
1. Other candidates for the same vacancy
2. Top performers (highest WSI scores) from similar roles
3. Historical benchmarks

Helps hiring managers contextualize individual performance.
"""
import logging
from typing import Any, Optional

from sqlalchemy import and_, select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

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
        result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        if not interview:
            return {"success": False, "error": "Interview not found"}

        if not interview.transcript or len(interview.transcript.strip()) < 50:
            return {"success": False, "error": "Transcript too short or missing"}

        candidate_wsi = await interview_wsi_service.analyze(interview_id, db)
        if not candidate_wsi.get("success"):
            return {"success": False, "error": "WSI analysis failed for this candidate"}

        vacancy_peers = await self._get_vacancy_peers(
            db, interview, company_id, interview_id
        )

        peer_scores: list[dict[str, Any]] = []
        for peer in vacancy_peers:
            try:
                peer_analysis = await interview_wsi_service.analyze(str(peer.id), db)
                if peer_analysis.get("success"):
                    peer_scores.append({
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

        ranking = self._build_ranking(candidate_wsi, peer_scores)
        benchmarks = self._compute_benchmarks(candidate_wsi, peer_scores)

        return {
            "success": True,
            "interview_id": interview_id,
            "candidate_wsi_score": candidate_wsi["wsi_score"],
            "peer_count": len(peer_scores),
            "ranking": ranking,
            "benchmarks": benchmarks,
            "top_performers": self._identify_top_performers(peer_scores),
            "comparative_insights": self._generate_insights(
                candidate_wsi, peer_scores, ranking
            ),
        }

    async def _get_vacancy_peers(
        self,
        db: AsyncSession,
        interview: Interview,
        company_id: str,
        exclude_id: str,
    ) -> list[Interview]:
        if not interview.job_vacancy_id:
            return []

        result = await db.execute(
            select(Interview).where(
                and_(
                    Interview.job_vacancy_id == interview.job_vacancy_id,
                    Interview.company_id == company_id,
                    Interview.id != exclude_id,
                    Interview.transcript.isnot(None),
                    Interview.status.in_(["completed", "transcribed"]),
                )
            ).limit(20)
        )
        return list(result.scalars().all())

    def _build_ranking(
        self,
        candidate_wsi: dict[str, Any],
        peer_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        all_scores = [candidate_wsi["wsi_score"]] + [
            p["wsi_score"] for p in peer_scores
        ]
        all_scores.sort(reverse=True)

        position = all_scores.index(candidate_wsi["wsi_score"]) + 1
        total = len(all_scores)
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
        peer_scores: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not peer_scores:
            return {
                "avg_wsi": candidate_wsi["wsi_score"],
                "max_wsi": candidate_wsi["wsi_score"],
                "min_wsi": candidate_wsi["wsi_score"],
                "candidate_vs_avg": 0.0,
                "dimensions": {},
            }

        wsi_scores = [p["wsi_score"] for p in peer_scores]
        avg_wsi = round(sum(wsi_scores) / len(wsi_scores), 2)
        max_wsi = round(max(wsi_scores), 2)
        min_wsi = round(min(wsi_scores), 2)

        dimensions: dict[str, dict[str, float]] = {}
        for dim in ("technical_score", "behavioral_score", "cultural_score"):
            dim_scores = [p[dim] for p in peer_scores if p.get(dim) is not None]
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
        self, peer_scores: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        sorted_peers = sorted(
            peer_scores, key=lambda p: p["wsi_score"], reverse=True
        )
        return sorted_peers[:3]

    def _generate_insights(
        self,
        candidate_wsi: dict[str, Any],
        peer_scores: list[dict[str, Any]],
        ranking: dict[str, Any],
    ) -> list[str]:
        insights: list[str] = []

        if not peer_scores:
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
