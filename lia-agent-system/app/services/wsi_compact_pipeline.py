"""
WSI Compact Mode Pipeline for Talent Pools.

Generates screening questions from an archetype (ideal_profile) using the same
WSI methodology as job vacancies, but in Compact Mode (3-5 essential questions
vs. 8-12 for Full Mode in jobs).

Integrates with:
  - JDEnrichmentService (existing): extracts traits and competencies
  - PromptRegistry (existing): uses WSI prompt templates
  - TenantAgentConfigService (Phase 6.2): applies tenant customization

Apply to: lia-agent-system/app/services/wsi_compact_pipeline.py
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

COMPACT_MODE_MAX_QUESTIONS = 5
COMPACT_MODE_MIN_QUESTIONS = 3


@dataclass
class ScreeningQuestion:
    question: str
    ideal_answer: str
    weight: float  # 0.0 to 1.0, sum should be ~1.0
    competency: str  # technical, behavioral, logistical
    source: str = "wsi_compact"  # wsi_compact, archetype, custom


@dataclass
class CompactScreeningConfig:
    questions: list[ScreeningQuestion] = field(default_factory=list)
    mode: str = "compact"
    archetype_id: Optional[str] = None
    traits_extracted: list[str] = field(default_factory=list)
    competencies_extracted: list[str] = field(default_factory=list)


class WSICompactPipeline:
    """
    Generates Compact Mode screening questions from an archetype.

    Flow:
    1. Load archetype data (ideal_profile from Rails or local DB)
    2. Extract traits and competencies (reuses JDEnrichmentService pattern)
    3. Generate 3-5 screening questions via LLM
    4. Return questions for recruiter approval
    """

    async def generate_from_archetype(
        self,
        archetype_data: dict,
        company_id: str,
        language: str = "pt-BR",
    ) -> CompactScreeningConfig:
        """
        Generate compact screening questions from archetype data.

        Args:
            archetype_data: dict with keys: name, description, seniority_level,
                           technical_requirements, behavioral_requirements,
                           experience_requirements, mandatory_skills
            company_id: tenant identifier
            language: output language

        Returns:
            CompactScreeningConfig with 3-5 questions ready for recruiter approval
        """
        name = archetype_data.get("name", "")
        description = archetype_data.get("description", "")
        seniority = archetype_data.get("seniority_level", "")
        tech_reqs = archetype_data.get("technical_requirements", {})
        behav_reqs = archetype_data.get("behavioral_requirements", {})
        exp_reqs = archetype_data.get("experience_requirements", {})
        skills = archetype_data.get("mandatory_skills", [])

        # Build context for LLM
        context = self._build_context(name, description, seniority, tech_reqs, behav_reqs, exp_reqs, skills)

        # Generate questions via LLM
        questions = await self._generate_questions(context, language, company_id=company_id)

        # Extract traits/competencies for metadata
        traits = self._extract_traits(tech_reqs, behav_reqs)
        competencies = self._extract_competencies(tech_reqs, behav_reqs, skills)

        config = CompactScreeningConfig(
            questions=questions,
            mode="compact",
            archetype_id=archetype_data.get("id"),
            traits_extracted=traits,
            competencies_extracted=competencies,
        )

        logger.info(
            "[WSICompact] Generated %d questions for archetype '%s' (company=%s)",
            len(questions), name, company_id
        )
        return config

    async def _generate_questions(
        self, context: str, language: str, company_id: str | None = None,
    ) -> list[ScreeningQuestion]:
        """Generate screening questions using LLM."""
        try:
            # Canonical LLM factory (multi-tenant aware). Replaces broken
            # get_llm import — WSI compact question generation was 100%
            # in fallback (template questions) until 2026-05-27.
            from app.shared.providers.llm_factory import create_tracked_llm
            llm = create_tracked_llm(
                temperature=0.3,
                service_name="WSICompactPipeline",
                operation="generate_questions",
                max_output_tokens=2048,
                tenant_id=company_id,
            )

            prompt = f"""
Você é um especialista em recrutamento usando a metodologia WSI (Work Sample Interview).
Com base no perfil abaixo, gere entre {COMPACT_MODE_MIN_QUESTIONS} e {COMPACT_MODE_MAX_QUESTIONS} perguntas de triagem essenciais.

PERFIL:
{context}

REGRAS:
- Modo Compacto: apenas as perguntas mais discriminantes (eliminam candidatos inadequados rapidamente)
- Cada pergunta deve ter: pergunta, resposta ideal, peso (soma = 1.0), categoria (technical/behavioral/logistical)
- Priorize: 1 logística (disponibilidade/local), 1-2 técnicas, 1-2 comportamentais
- Perguntas curtas e diretas
- Idioma: {"Português brasileiro" if language == "pt-BR" else language}

Responda APENAS com JSON:
{{
  "questions": [
    {{
      "question": "texto da pergunta",
      "ideal_answer": "resposta ideal esperada",
      "weight": 0.25,
      "competency": "technical|behavioral|logistical"
    }}
  ]
}}
"""
            response = await llm.ainvoke(prompt)
            data = json.loads(response.content)

            questions = []
            for q in data.get("questions", [])[:COMPACT_MODE_MAX_QUESTIONS]:
                questions.append(ScreeningQuestion(
                    question=q["question"],
                    ideal_answer=q["ideal_answer"],
                    weight=float(q.get("weight", 1.0 / len(data["questions"]))),
                    competency=q.get("competency", "technical"),
                ))

            # Normalize weights to sum to 1.0
            total_weight = sum(q.weight for q in questions)
            if total_weight > 0:
                for q in questions:
                    q.weight = round(q.weight / total_weight, 2)

            return questions

        except Exception as exc:
            logger.warning("[WSICompact] LLM generation failed, using fallback: %s", exc)
            return self._fallback_questions()

    def _build_context(
        self, name: str, description: str, seniority: str,
        tech_reqs: dict, behav_reqs: dict, exp_reqs: dict, skills: list
    ) -> str:
        parts = [f"Perfil: {name}"]
        if description:
            parts.append(f"Descrição: {description[:500]}")
        if seniority:
            parts.append(f"Senioridade: {seniority}")
        if skills:
            parts.append(f"Skills obrigatórias: {', '.join(skills[:10])}")
        if tech_reqs:
            parts.append(f"Requisitos técnicos: {json.dumps(tech_reqs, ensure_ascii=False)[:300]}")
        if behav_reqs:
            parts.append(f"Requisitos comportamentais: {json.dumps(behav_reqs, ensure_ascii=False)[:300]}")
        if exp_reqs:
            parts.append(f"Experiência: {json.dumps(exp_reqs, ensure_ascii=False)[:200]}")
        return "\n".join(parts)

    @staticmethod
    def _extract_traits(tech_reqs: dict, behav_reqs: dict) -> list[str]:
        traits = []
        if isinstance(behav_reqs, dict):
            traits.extend(list(behav_reqs.keys())[:5])
        if isinstance(tech_reqs, dict):
            traits.extend(list(tech_reqs.keys())[:3])
        return traits

    @staticmethod
    def _extract_competencies(tech_reqs: dict, behav_reqs: dict, skills: list) -> list[str]:
        competencies = list(skills[:5]) if skills else []
        if isinstance(tech_reqs, dict):
            competencies.extend(list(tech_reqs.keys())[:3])
        return list(set(competencies))[:8]

    @staticmethod
    def _fallback_questions() -> list[ScreeningQuestion]:
        """Generic fallback questions when LLM fails."""
        return [
            ScreeningQuestion(
                question="Qual é sua disponibilidade para início?",
                ideal_answer="Imediata ou em até 30 dias",
                weight=0.25,
                competency="logistical",
            ),
            ScreeningQuestion(
                question="Descreva brevemente sua experiência mais relevante para esta posição.",
                ideal_answer="Experiência alinhada com os requisitos do perfil",
                weight=0.35,
                competency="technical",
            ),
            ScreeningQuestion(
                question="O que te motiva a buscar uma nova oportunidade neste momento?",
                ideal_answer="Motivação genuína e alinhada com o perfil da vaga",
                weight=0.20,
                competency="behavioral",
            ),
            ScreeningQuestion(
                question="Qual é sua pretensão salarial?",
                ideal_answer="Dentro da faixa prevista para o perfil",
                weight=0.20,
                competency="logistical",
            ),
        ]

    def questions_to_json(self, config: CompactScreeningConfig) -> list[dict]:
        """Convert to JSON format compatible with Rails screening_questions column."""
        return [
            {
                "question": q.question,
                "ideal_answer": q.ideal_answer,
                "weight": q.weight,
                "competency": q.competency,
                "source": q.source,
            }
            for q in config.questions
        ]


# Singleton
wsi_compact_pipeline = WSICompactPipeline()
