"""
Cultural Fit Integration Service — E2

Integra scores WSI + notas de entrevistadores + cultura empresa em score único.
PII masking em notas de entrevista antes de análise LLM (LGPD).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Pesos configuráveis — somam 1.0
WSI_WEIGHT = 0.4
INTERVIEW_WEIGHT = 0.4
CULTURE_WEIGHT = 0.2


@dataclass
class CulturalFitResult:
    candidate_id: str
    job_id: str
    overall_score: float  # 0–100
    wsi_contribution: float
    interview_contribution: float
    culture_alignment: float
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    computed_at: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "overall_score": self.overall_score,
            "wsi_contribution": self.wsi_contribution,
            "interview_contribution": self.interview_contribution,
            "culture_alignment": self.culture_alignment,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }


class CulturalFitIntegrationService:
    """
    Computa fit cultural integrado: WSI + notas de entrevista + cultura empresa.

    Retorna score [0–100] com contribuições de cada fonte.
    Fail-open: retorna score neutro (50.0) em caso de erro.
    """

    async def compute_integrated_fit(
        self,
        candidate_id: str,
        job_id: str,
        company_id: str,
        db,
    ) -> CulturalFitResult:
        """
        Calcula fit cultural integrado.

        Passos:
        1. Busca score WSI do candidato (dimensões comportamentais)
        2. Busca notas de entrevistadores (PII masked antes de análise)
        3. Busca cultura da empresa via CultureAnalyzerService
        4. Pondera os 3 componentes e retorna resultado
        """
        try:
            wsi_score = await self._get_wsi_score(candidate_id, job_id, db)
            interview_score = await self._get_interview_score(candidate_id, job_id, db)
            culture_score = await self._get_culture_alignment(candidate_id, job_id, company_id, db)

            overall = round(
                wsi_score * WSI_WEIGHT
                + interview_score * INTERVIEW_WEIGHT
                + culture_score * CULTURE_WEIGHT,
                1,
            )

            return CulturalFitResult(
                candidate_id=candidate_id,
                job_id=job_id,
                overall_score=min(100.0, max(0.0, overall)),
                wsi_contribution=wsi_score,
                interview_contribution=interview_score,
                culture_alignment=culture_score,
                computed_at=datetime.utcnow(),
            )

        except Exception as exc:
            logger.warning("[CulturalFit] compute_integrated_fit failed (fail-open): %s", exc)
            return CulturalFitResult(
                candidate_id=candidate_id,
                job_id=job_id,
                overall_score=50.0,
                wsi_contribution=50.0,
                interview_contribution=50.0,
                culture_alignment=50.0,
                error=str(exc),
                computed_at=datetime.utcnow(),
            )

    async def _get_wsi_score(self, candidate_id: str, job_id: str, db) -> float:
        """Busca score WSI do candidato. Fallback: 50.0."""
        try:
            from sqlalchemy import text
            result = await db.execute(
                text(
                    "SELECT score FROM wsi_sessions "
                    "WHERE candidate_id = :cid AND job_id = :jid "
                    "AND status = 'completed' "
                    "ORDER BY completed_at DESC LIMIT 1"
                ),
                {"cid": candidate_id, "jid": job_id},
            )
            row = result.fetchone()
            if row and row[0] is not None:
                return float(row[0])
        except Exception as exc:
            logger.debug("[CulturalFit] _get_wsi_score fallback: %s", exc)
        return 50.0

    async def _get_interview_score(self, candidate_id: str, job_id: str, db) -> float:
        """
        Busca notas de entrevistadores e analisa via LLM.
        PII masked antes de enviar para análise.
        Fallback: 50.0.
        """
        try:
            from sqlalchemy import text
            result = await db.execute(
                text(
                    "SELECT notes, sentiment_score FROM interview_notes "
                    "WHERE candidate_id = :cid AND job_id = :jid "
                    "ORDER BY created_at DESC LIMIT 5"
                ),
                {"cid": candidate_id, "jid": job_id},
            )
            rows = result.fetchall()
            if not rows:
                return 50.0

            # Aggregate sentiment scores if available
            scores = [r[1] for r in rows if r[1] is not None]
            if scores:
                return round(sum(scores) / len(scores), 1)

            # Fallback: analyze notes text with PII masking
            notes_text = " ".join(r[0] for r in rows if r[0])
            if notes_text:
                from app.shared.pii_masking import strip_pii_for_llm_prompt
                clean_notes = strip_pii_for_llm_prompt(notes_text)
                # Simple heuristic: positive keywords
                positive = ["excelente", "ótimo", "recomendo", "aprovado", "destaque", "proativo"]
                negative = ["fraco", "inadequado", "rejeitado", "despreparado", "desatento"]
                pos_count = sum(clean_notes.lower().count(k) for k in positive)
                neg_count = sum(clean_notes.lower().count(k) for k in negative)
                if pos_count + neg_count > 0:
                    ratio = pos_count / (pos_count + neg_count)
                    return round(40.0 + ratio * 60.0, 1)

        except Exception as exc:
            logger.debug("[CulturalFit] _get_interview_score fallback: %s", exc)
        return 50.0

    async def _get_culture_alignment(
        self, candidate_id: str, job_id: str, company_id: str, db
    ) -> float:
        """Busca alinhamento cultural via CultureAnalyzerService. Fallback: 50.0."""
        try:
            from app.shared.services.culture_analyzer_service import CultureAnalyzerService
            analyzer = CultureAnalyzerService()
            result = await analyzer.analyze_candidate_fit(
                candidate_id=candidate_id,
                company_id=company_id,
                db=db,
            )
            if result and hasattr(result, "fit_score"):
                return float(result.fit_score)
        except Exception as exc:
            logger.debug("[CulturalFit] _get_culture_alignment fallback: %s", exc)
        return 50.0


cultural_fit_service = CulturalFitIntegrationService()
