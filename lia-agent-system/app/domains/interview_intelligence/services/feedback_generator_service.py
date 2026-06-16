"""
Feedback Generator Service — Structured candidate feedback from interview analysis.

Generates professional, constructive feedback suitable for sharing with candidates.
Based on WSI analysis, focused on strengths and development areas.

Follows best practices:
- Never reveal internal scoring details
- Focus on observable behaviors and demonstrated competencies
- Provide actionable development suggestions
- Maintain positive, professional tone
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

FEEDBACK_PROMPT = """Você é um especialista em desenvolvimento de carreira da WeDO Talent.

Gere um feedback estruturado e construtivo para o candidato com base na análise da entrevista.

REGRAS IMPORTANTES:
1. NUNCA revele scores numéricos ou detalhes internos de avaliação
2. Foque em comportamentos observáveis e competências demonstradas
3. Seja construtivo e encorajador, mesmo em pontos de melhoria
4. Forneça sugestões práticas de desenvolvimento
5. Mantenha tom profissional e respeitoso
6. O feedback deve ser útil para o candidato independente do resultado

DADOS DA ANÁLISE:
- Candidato: {candidate_name}
- Vaga: {job_title}
- Tipo de entrevista: {interview_type}
- Competências fortes: {strengths}
- Áreas de desenvolvimento: {development_areas}
- Nível cognitivo demonstrado (Bloom): {bloom_description}
- Estrutura de respostas (STAR): {star_description}
- Perfil comportamental: {behavioral_profile}

TRECHO DA TRANSCRIÇÃO:
{transcript_excerpt}

Gere o feedback em JSON:
{{
  "greeting": "Saudação personalizada ao candidato",
  "overall_impression": "Impressão geral em 2-3 frases",
  "strengths_highlighted": [
    {{
      "competency": "nome da competência",
      "observation": "o que foi observado durante a entrevista",
      "impact": "por que isso é valioso"
    }}
  ],
  "development_areas": [
    {{
      "area": "área de desenvolvimento",
      "observation": "o que foi observado",
      "suggestion": "sugestão prática de desenvolvimento"
    }}
  ],
  "interview_tips": ["dica prática para futuras entrevistas"],
  "closing": "Mensagem de encerramento encorajadora"
}}"""


class FeedbackGeneratorService:

    async def generate(
        self,
        interview_id: str,
        db: AsyncSession,
        wsi_data: Optional[dict[str, Any]] = None,
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
            return {"success": False, "error": "WSI analysis required before feedback generation"}

        bloom = wsi_data.get("bloom_level", 3)
        bloom_descriptions = {
            1: "Demonstrou conhecimento factual sólido",
            2: "Mostrou boa compreensão conceitual",
            3: "Demonstrou capacidade de aplicação prática",
            4: "Evidenciou pensamento analítico",
            5: "Mostrou capacidade avaliativa e crítica",
            6: "Demonstrou capacidade criativa e inovadora",
        }
        bloom_desc = bloom_descriptions.get(
            round(bloom) if isinstance(bloom, (int, float)) else 3,
            "Demonstrou boa compreensão conceitual"
        )

        cbi = wsi_data.get("cbi_completeness", 0) or 0
        if cbi >= 0.8:
            star_desc = "Respostas bem estruturadas com situação, tarefa, ação e resultado claros"
        elif cbi >= 0.5:
            star_desc = "Boa estrutura de respostas, com oportunidade de detalhar mais os resultados"
        else:
            star_desc = "Respostas podem se beneficiar de mais estrutura (contexto, ação, resultado)"

        big_five = wsi_data.get("big_five", {}) or {}
        behavioral_parts = []
        if big_five.get("openness", 0) > 0.3:
            behavioral_parts.append("abertura a novas experiências")
        if big_five.get("conscientiousness", 0) > 0.3:
            behavioral_parts.append("organização e responsabilidade")
        if big_five.get("extraversion", 0) > 0.3:
            behavioral_parts.append("boa comunicação interpessoal")
        if big_five.get("agreeableness", 0) > 0.3:
            behavioral_parts.append("perfil colaborativo")
        behavioral_profile = ", ".join(behavioral_parts) if behavioral_parts else "perfil equilibrado"

        transcript_excerpt = interview.transcript[:3000]

        prompt = FEEDBACK_PROMPT.format(
            candidate_name=interview.candidate_name or "Candidato(a)",
            job_title=interview.job_title or "a posição",
            interview_type=interview.interview_type or "behavioral",
            strengths=", ".join(wsi_data.get("strengths", [])) or "Em avaliação",
            development_areas=", ".join(wsi_data.get("concerns", [])) or "Nenhuma crítica",
            bloom_description=bloom_desc,
            star_description=star_desc,
            behavioral_profile=behavioral_profile,
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

            feedback = json.loads(cleaned)

            return {
                "success": True,
                "interview_id": interview_id,
                "candidate_name": interview.candidate_name,
                "feedback": {
                    "greeting": feedback.get("greeting", ""),
                    "overall_impression": feedback.get("overall_impression", ""),
                    "strengths_highlighted": feedback.get("strengths_highlighted", []),
                    "development_areas": feedback.get("development_areas", []),
                    "interview_tips": feedback.get("interview_tips", []),
                    "closing": feedback.get("closing", ""),
                },
            }
        except Exception as exc:
            logger.error("Feedback generation failed: %s", exc)
            return self._generate_deterministic_feedback(interview, wsi_data)

    def _generate_deterministic_feedback(
        self,
        interview: Interview,
        wsi_data: dict[str, Any],
    ) -> dict[str, Any]:
        strengths = wsi_data.get("strengths", [])
        concerns = wsi_data.get("concerns", [])

        strengths_highlighted = []
        for s in strengths[:3]:
            strengths_highlighted.append({
                "competency": s,
                "observation": f"Durante a entrevista, você demonstrou {s.lower()}.",
                "impact": "Esta é uma competência valorizada no mercado.",
            })

        development_areas = []
        for c in concerns[:3]:
            development_areas.append({
                "area": c,
                "observation": f"Identificamos oportunidade de desenvolvimento em {c.lower()}.",
                "suggestion": "Busque experiências práticas e treinamentos nesta área.",
            })

        return {
            "success": True,
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "feedback": {
                "greeting": f"Olá, {interview.candidate_name or 'Candidato(a)'}!",
                "overall_impression": (
                    "Agradecemos sua participação no processo seletivo. "
                    "Sua entrevista trouxe informações valiosas sobre seu perfil profissional."
                ),
                "strengths_highlighted": strengths_highlighted,
                "development_areas": development_areas,
                "interview_tips": [
                    "Estruture suas respostas com contexto, ação e resultado.",
                    "Prepare exemplos concretos de suas realizações profissionais.",
                    "Pesquise sobre a empresa e a vaga antes da entrevista.",
                ],
                "closing": (
                    "Desejamos sucesso em sua trajetória profissional. "
                    "Continue investindo em seu desenvolvimento!"
                ),
            },
            "_fallback": True,
        }


feedback_generator_service = FeedbackGeneratorService()
