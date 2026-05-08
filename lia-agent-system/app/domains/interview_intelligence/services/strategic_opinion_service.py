"""
Strategic Opinion Service — LLM-generated hiring recommendation.

Generates a structured strategic opinion (parecer) based on:
- WSI analysis results
- Bias detection findings
- Comparative analysis
- Job requirements context

Output: evidence-based recommendation with confidence level.
"""
import json
import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_intelligence.repositories.interview_repository import (
    InterviewRepository,
)

from app.models.interview import Interview

logger = logging.getLogger(__name__)

OPINION_PROMPT = """Você é um consultor sênior de recrutamento da WeDO Talent, especialista em avaliação de candidatos.

Com base nos dados da entrevista abaixo, gere um PARECER ESTRATÉGICO DE CONTRATAÇÃO.

DADOS DA ENTREVISTA:
- Candidato: {candidate_name}
- Vaga: {job_title}
- Tipo: {interview_type}
- Score WSI: {wsi_score}/5.0
- Score Técnico: {technical_score}/5.0
- Score Comportamental: {behavioral_score}/5.0
- Score Cultural: {cultural_score}/5.0
- Nível Bloom: {bloom_level}
- Estágio Dreyfus: {dreyfus_stage}
- Completude CBI: {cbi_completeness}%
- Pontos fortes: {strengths}
- Pontos de atenção: {concerns}
- Red flags: {red_flags}
- Viés detectado: {bias_summary}
- Ranking comparativo: {ranking_info}

TRECHO DA TRANSCRIÇÃO (para embasar parecer):
{transcript_excerpt}

INSTRUÇÕES:
1. Forneça uma recomendação clara: CONTRATAR / NÃO CONTRATAR / AVALIAR MAIS
2. Justifique com evidências concretas da entrevista
3. Identifique riscos e mitigações
4. Sugira próximos passos
5. Atribua um nível de confiança à sua recomendação (alto/médio/baixo)

Responda em JSON:
{{
  "recommendation": "CONTRATAR/NÃO CONTRATAR/AVALIAR MAIS",
  "confidence": "alto/médio/baixo",
  "executive_summary": "Resumo executivo em 2-3 frases",
  "evidence_for": ["evidências a favor, com citações da transcrição"],
  "evidence_against": ["evidências contra, com citações"],
  "risks": ["riscos identificados"],
  "mitigations": ["mitigações sugeridas"],
  "next_steps": ["próximos passos recomendados"],
  "salary_positioning": "observação sobre posicionamento salarial se houver dados",
  "onboarding_notes": "notas para onboarding se contratado"
}}"""


class StrategicOpinionService:

    async def generate(
        self,
        interview_id: str,
        db: AsyncSession,
        wsi_data: Optional[dict[str, Any]] = None,
        bias_data: Optional[dict[str, Any]] = None,
        comparative_data: Optional[dict[str, Any]] = None,
        company_id: str = "",
    ) -> dict[str, Any]:
        if not company_id:
            return {"success": False, "error": "company_id is required for tenant isolation"}
        from sqlalchemy import and_
        _ii_repo = InterviewRepository(db)
        interview = await _ii_repo.get_for_company(
            interview_id=interview_id, company_id=company_id
        )
        if not interview:
            return {"success": False, "error": "Interview not found"}

        if not interview.transcript or len(interview.transcript.strip()) < 50:
            return {"success": False, "error": "Transcript too short or missing"}

        if not wsi_data or not wsi_data.get("success"):
            return {"success": False, "error": "WSI analysis required before opinion generation"}

        transcript_excerpt = interview.transcript[:4000]

        bias_summary = "Nenhum viés detectado"
        if bias_data and bias_data.get("success"):
            if bias_data.get("bias_detected"):
                count = len(bias_data.get("findings", []))
                score = bias_data.get("overall_fairness_score", "N/A")
                bias_summary = f"{count} indicador(es) de viés (equidade: {score}/5)"
            else:
                bias_summary = "Entrevista justa (sem viés detectado)"

        ranking_info = "Sem dados comparativos"
        if comparative_data and comparative_data.get("success"):
            r = comparative_data.get("ranking", {})
            ranking_info = (
                f"Posição {r.get('position', '?')}/{r.get('total_candidates', '?')} "
                f"(percentil {r.get('percentile', '?')})"
            )

        prompt = OPINION_PROMPT.format(
            candidate_name=interview.candidate_name or "N/A",
            job_title=interview.job_title or "N/A",
            interview_type=interview.interview_type or "behavioral",
            wsi_score=wsi_data.get("wsi_score", "N/A"),
            technical_score=wsi_data.get("technical_score", "N/A"),
            behavioral_score=wsi_data.get("behavioral_score", "N/A"),
            cultural_score=wsi_data.get("cultural_score", "N/A"),
            bloom_level=wsi_data.get("bloom_level", "N/A"),
            dreyfus_stage=wsi_data.get("dreyfus_stage", "N/A"),
            cbi_completeness=round((wsi_data.get("cbi_completeness", 0) or 0) * 100),
            strengths=", ".join(wsi_data.get("strengths", [])) or "Nenhum identificado",
            concerns=", ".join(wsi_data.get("concerns", [])) or "Nenhum",
            red_flags=", ".join(wsi_data.get("red_flags", [])) or "Nenhum",
            bias_summary=bias_summary,
            ranking_info=ranking_info,
            transcript_excerpt=transcript_excerpt,
        )

        try:
            from app.domains.ai.services.llm import LLMService
            llm = LLMService()
            raw = await llm.generate(prompt, provider="gemini")

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

            opinion = json.loads(cleaned)

            return {
                "success": True,
                "interview_id": interview_id,
                "candidate_name": interview.candidate_name,
                "job_title": interview.job_title,
                "recommendation": opinion.get("recommendation", "AVALIAR MAIS"),
                "confidence": opinion.get("confidence", "médio"),
                "executive_summary": opinion.get("executive_summary", ""),
                "evidence_for": opinion.get("evidence_for", []),
                "evidence_against": opinion.get("evidence_against", []),
                "risks": opinion.get("risks", []),
                "mitigations": opinion.get("mitigations", []),
                "next_steps": opinion.get("next_steps", []),
                "salary_positioning": opinion.get("salary_positioning", ""),
                "onboarding_notes": opinion.get("onboarding_notes", ""),
            }
        except Exception as exc:
            logger.error("Strategic opinion generation failed: %s", exc)
            return self._generate_deterministic_opinion(
                interview, wsi_data, bias_data, comparative_data
            )

    def _generate_deterministic_opinion(
        self,
        interview: Interview,
        wsi_data: dict[str, Any],
        bias_data: Optional[dict[str, Any]],
        comparative_data: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        wsi_score = wsi_data.get("wsi_score", 0)
        red_flags = wsi_data.get("red_flags", [])

        if len(red_flags) >= 3 or wsi_score < 2.5:
            recommendation = "NÃO CONTRATAR"
            confidence = "alto" if wsi_score < 2.0 else "médio"
        elif wsi_score >= 4.0 and len(red_flags) == 0:
            recommendation = "CONTRATAR"
            confidence = "alto"
        elif wsi_score >= 3.5:
            recommendation = "CONTRATAR"
            confidence = "médio"
        elif wsi_score >= 3.0:
            recommendation = "AVALIAR MAIS"
            confidence = "médio"
        else:
            recommendation = "AVALIAR MAIS"
            confidence = "baixo"

        return {
            "success": True,
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "job_title": interview.job_title,
            "recommendation": recommendation,
            "confidence": confidence,
            "executive_summary": (
                f"Score WSI: {wsi_score}/5.0. "
                f"Recomendação: {recommendation} (confiança {confidence}). "
                f"Parecer gerado por análise determinística (fallback)."
            ),
            "evidence_for": wsi_data.get("strengths", []),
            "evidence_against": wsi_data.get("concerns", []) + red_flags,
            "risks": red_flags,
            "mitigations": [],
            "next_steps": (
                ["Entrevista técnica adicional"] if recommendation == "AVALIAR MAIS"
                else ["Prosseguir com proposta"] if recommendation == "CONTRATAR"
                else ["Agradecer participação e encerrar processo"]
            ),
            "salary_positioning": "",
            "onboarding_notes": "",
            "_fallback": True,
        }


strategic_opinion_service = StrategicOpinionService()
