"""
Interview WSI Service — Applies WSI 7-block methodology to interview transcripts.

Wraps the existing InterviewTranscriptAnalysisService (deterministic scorer)
and maps results to the 7-block WSI rubric:
  1. Hard Skills (técnico)
  2. Soft Skills (comportamental)
  3. Experiência (Dreyfus stage)
  4. Liderança
  5. Comunicação
  6. Fit Cultural
  7. Potencial (Bloom cognitive level)

Enforces tenant isolation via mandatory company_id.
"""
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.services.interview_transcript_analysis_service import (
    interview_transcript_analysis_service,
)
from lia_models.interview import Interview

logger = logging.getLogger(__name__)

LEADERSHIP_KEYWORDS = [
    "liderar", "liderança", "equipe", "gerenciar", "coordenar",
    "delegar", "mentoria", "gestão de pessoas", "people management",
]
COMMUNICATION_KEYWORDS = [
    "comunicar", "comunicação", "apresentar", "explicar", "articular",
    "negociar", "oratória", "feedback", "escuta ativa",
]


class InterviewWSIService:

    def __init__(self) -> None:
        self._analyzer = interview_transcript_analysis_service

    async def analyze(
        self,
        interview_id: str,
        db: AsyncSession,
        company_id: str,
        job_requirements: list[str] | None = None,
    ) -> dict[str, Any]:
        if not company_id:
            return {"success": False, "error": "company_id is required for tenant isolation"}

        result = await db.execute(
            select(Interview).where(
                and_(
                    Interview.id == interview_id,
                    Interview.company_id == company_id,
                )
            )
        )
        interview = result.scalar_one_or_none()
        if not interview:
            return {"success": False, "error": "Interview not found"}

        transcript = interview.transcript
        if not transcript or len(transcript.strip()) < 50:
            return {
                "success": False,
                "error": "Transcript too short or missing (min 50 chars)",
            }

        job_competencies: list[dict] | None = None
        if job_requirements:
            job_competencies = [
                {"name": r, "type": "technical"} for r in job_requirements
            ]

        analysis = self._analyzer.analyze_transcript(
            transcript_text=transcript,
            interview_id=interview_id,
            candidate_id=str(interview.candidate_id) if interview.candidate_id else "",
            job_vacancy_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
            job_competencies=job_competencies,
        )

        seven_blocks = self._map_to_seven_blocks(analysis, transcript)

        # B0 #523 — Normalização /5→/10. O analyzer subjacente
        # (interview_transcript_analysis_service) ainda produz scores em /5
        # (legacy out-of-scope deste refactor). Aqui promovemos para a escala
        # canônica /10 antes de expor a consumidores (strategic_opinion,
        # comparative_analysis, frontend). Fator vem do canônico (SCALE_MAX/5)
        # — não literal — pra colapsar automaticamente se a escala mudar.
        # Bloom (1-6) e Dreyfus (1-5) seguem escalas próprias — não multiplicar.
        from app.domains.cv_screening.constants.wsi_scale import SCALE_MAX
        LEGACY_5_TO_10 = SCALE_MAX / 5.0  # = 2.0 enquanto SCALE_MAX=10.0
        return {
            "success": True,
            "interview_id": interview_id,
            "candidate_id": str(interview.candidate_id) if interview.candidate_id else None,
            "job_vacancy_id": str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
            "interview_type": interview.interview_type,
            "wsi_score": round(analysis.overall_wsi_score * LEGACY_5_TO_10, 2),
            "technical_score": round(analysis.technical_score * LEGACY_5_TO_10, 2),
            "behavioral_score": round(analysis.behavioral_score * LEGACY_5_TO_10, 2),
            "cultural_score": round(analysis.cultural_score * LEGACY_5_TO_10, 2),
            "bloom_level": analysis.bloom_average,
            "dreyfus_stage": analysis.dreyfus_average,
            "cbi_completeness": analysis.cbi_completeness,
            "big_five": analysis.big_five_profile,
            "seven_blocks": seven_blocks,
            "evidences": [
                {
                    "competency": e.competency_name,
                    "category": e.category,
                    "excerpt": e.evidence_text[:200],
                    "bloom_level": e.bloom_level,
                }
                for e in analysis.evidences[:15]
            ],
            "strengths": analysis.strengths[:5],
            "concerns": analysis.concerns[:5],
            "red_flags": analysis.red_flags[:5],
            "recommendation": analysis.recommendation,
            "summary": analysis.summary,
        }

    def _map_to_seven_blocks(self, analysis: Any, transcript: str) -> dict[str, Any]:
        # B0 #523 — Todos os scores expostos em escala canônica /10 via constantes
        # do wsi_scale (zero literais). analysis.* vem em /5 do analyzer legacy,
        # então multiplicamos por LEGACY_5_TO_10 ao expor. Bloom (1-6) e
        # Dreyfus (1-5) ficam como escalas próprias — sem conversão.
        from app.domains.cv_screening.constants.wsi_scale import (
            GATE_G3_THRESHOLD,
            SCALE_MAX,
        )
        LEGACY_5_TO_10 = SCALE_MAX / 5.0
        # Base inicial = GATE_G3_THRESHOLD (4.0 em /10): score técnico mínimo
        # aceitável. Cada evidência adiciona 1 ponto, capado em SCALE_MAX.
        BASE_KEYWORD_SCORE = GATE_G3_THRESHOLD

        text_lower = transcript.lower()

        leadership_hits = sum(1 for kw in LEADERSHIP_KEYWORDS if kw in text_lower)
        leadership_score = min(SCALE_MAX, BASE_KEYWORD_SCORE + leadership_hits * 1.0)

        comm_hits = sum(1 for kw in COMMUNICATION_KEYWORDS if kw in text_lower)
        communication_score = min(SCALE_MAX, BASE_KEYWORD_SCORE + comm_hits * 1.0)

        big_five = analysis.big_five_profile or {}
        extraversion = big_five.get("extraversion", 0)
        agreeableness = big_five.get("agreeableness", 0)
        if extraversion > 0.3 or agreeableness > 0.3:
            communication_score = min(SCALE_MAX, communication_score + 1.0)

        # Bloom 1-6 → /10 via SCALE_MAX (Bloom é escala fixa, denominador literal).
        BLOOM_MAX = 6.0
        potential_score = min(SCALE_MAX, (analysis.bloom_average / BLOOM_MAX) * SCALE_MAX)

        return {
            "hard_skills": {
                "score": round(analysis.technical_score * LEGACY_5_TO_10, 2),
                "label": "Hard Skills / Técnico",
                "description": "Competências técnicas demonstradas na entrevista",
            },
            "soft_skills": {
                "score": round(analysis.behavioral_score * LEGACY_5_TO_10, 2),
                "label": "Soft Skills / Comportamental",
                "description": "Competências comportamentais e interpessoais",
            },
            "experience": {
                "score": round(analysis.dreyfus_average, 2),  # Dreyfus 1-5: escala própria
                "label": "Experiência (Dreyfus)",
                "description": f"Estágio de expertise: {self._dreyfus_label(analysis.dreyfus_average)}",
            },
            "leadership": {
                "score": round(leadership_score, 2),
                "label": "Liderança",
                "description": f"{leadership_hits} indicadores de liderança identificados",
            },
            "communication": {
                "score": round(communication_score, 2),
                "label": "Comunicação",
                "description": f"{comm_hits} indicadores de comunicação identificados",
            },
            "cultural_fit": {
                "score": round(analysis.cultural_score * LEGACY_5_TO_10, 2),
                "label": "Fit Cultural",
                "description": "Compatibilidade cultural baseada em Big Five e evidências",
            },
            "potential": {
                "score": round(potential_score, 2),
                "label": "Potencial (Bloom)",
                "description": f"Nível cognitivo: {self._bloom_label(analysis.bloom_average)}",
            },
        }

    @staticmethod
    def _dreyfus_label(score: float) -> str:
        if score >= 4.5:
            return "Expert"
        if score >= 3.5:
            return "Proficient"
        if score >= 2.5:
            return "Competent"
        if score >= 1.5:
            return "Advanced Beginner"
        return "Novice"

    @staticmethod
    def _bloom_label(score: float) -> str:
        if score >= 4.5:
            return "Create"
        if score >= 3.5:
            return "Evaluate"
        if score >= 2.5:
            return "Analyze"
        if score >= 1.5:
            return "Apply"
        if score >= 0.5:
            return "Understand"
        return "Remember"


interview_wsi_service = InterviewWSIService()
