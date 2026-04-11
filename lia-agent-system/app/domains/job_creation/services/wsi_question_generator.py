"""
WSIQuestionGenerator — F2+F3+F6 of WSI methodology.

F2: Extract Big Five profile from enriched JD (LLM temp=0.1)
F3: Rank traits by weighted formula (deterministic)
F6: Generate screening questions via LLM (CBI/Bloom/Dreyfus/BigFive)

Governance integrations:
  - Circuit breaker: wraps all LLM calls
  - Audit: tracked via create_tracked_llm callbacks (automatic)
  - WSI validation: post-generation question quality checks
  - Fairness: no cultural fit questions (enforced in prompt + validation)

WSI absolute rules:
  - CBI only (no hypothetical questions)
  - No cultural fit questions
  - Temperature=0.0 for evaluation (0.7 for tech generation, 0.75 for behavioral)
  - Recrutador aprova todas as perguntas
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from app.domains.job_creation.schemas import (
    BigFiveExtraction,
    EnrichedJobDescription,
    GeneratedQuestion,
)

logger = logging.getLogger(__name__)

# F3: Trait ranking formula weights
TRAIT_FORMULA_WEIGHTS = {
    "llm": 0.40,
    "prior": 0.35,
    "seniority_boost": 0.25,
}

# O*NET prior profiles by role archetype (simplified)
ONET_PRIOR_PROFILES = {
    "engineering": {"openness": 0.7, "conscientiousness": 0.8, "extraversion": 0.4, "agreeableness": 0.5, "stability": 0.7},
    "product": {"openness": 0.8, "conscientiousness": 0.6, "extraversion": 0.7, "agreeableness": 0.6, "stability": 0.6},
    "design": {"openness": 0.9, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.6},
    "sales": {"openness": 0.5, "conscientiousness": 0.6, "extraversion": 0.9, "agreeableness": 0.7, "stability": 0.5},
    "operations": {"openness": 0.4, "conscientiousness": 0.9, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.7},
    "default": {"openness": 0.5, "conscientiousness": 0.7, "extraversion": 0.5, "agreeableness": 0.6, "stability": 0.6},
}

# Seniority boosts for trait ranking (F3)
SENIORITY_TRAIT_BOOSTS = {
    "junior": {"conscientiousness": 0.2, "agreeableness": 0.1},
    "pleno": {"conscientiousness": 0.1, "openness": 0.1},
    "senior": {"openness": 0.15, "stability": 0.1},
    "lead": {"extraversion": 0.2, "stability": 0.15},
    "diretor": {"extraversion": 0.2, "openness": 0.15, "stability": 0.1},
}


def _build_bigfive_prompt(enriched: EnrichedJobDescription) -> str:
    """Build F2 Big Five extraction prompt."""
    skills = ", ".join(s.skill for s in enriched.skills_obrigatorias[:10])
    competencies = ", ".join(c.competencia for c in enriched.competencias_comportamentais[:8])
    responsibilities = "\n".join(f"- {r}" for r in enriched.responsabilidades[:8])

    return f"""Analise o perfil da vaga abaixo e extraia o perfil Big Five (OCEAN) esperado para o cargo.
Para cada trait, atribua um score de 0.0 a 1.0 indicando a importancia para o cargo.
Inclua evidencias do JD que justificam cada score.

VAGA: {enriched.titulo_padronizado}
SENIORIDADE: {enriched.senioridade_confirmada}

SKILLS TECNICAS: {skills}
COMPETENCIAS COMPORTAMENTAIS: {competencies}

RESPONSABILIDADES:
{responsibilities}

CONTEXTO:
- Autonomia: {enriched.context_signals.nivel_autonomia}
- Inovacao: {enriched.context_signals.nivel_inovacao}
- Pressao: {enriched.context_signals.nivel_pressao}
- Colaboracao: {enriched.context_signals.nivel_colaboracao}

Responda APENAS com JSON:
{{
  "openness": 0.0-1.0,
  "conscientiousness": 0.0-1.0,
  "extraversion": 0.0-1.0,
  "agreeableness": 0.0-1.0,
  "stability": 0.0-1.0,
  "evidences": {{
    "openness": ["evidencia1", "evidencia2"],
    "conscientiousness": ["evidencia1"],
    "extraversion": ["evidencia1"],
    "agreeableness": ["evidencia1"],
    "stability": ["evidencia1"]
  }}
}}"""


def _build_questions_prompt(
    block: Literal["technical", "behavioral"],
    enriched: EnrichedJobDescription,
    seniority: str,
    count: int,
    trait_rankings: Optional[List[Dict]] = None,
) -> str:
    """Build F6 question generation prompt."""
    if block == "technical":
        skills = ", ".join(s.skill for s in enriched.skills_obrigatorias[:count + 3])
        return f"""Gere {count} perguntas TECNICAS de triagem para a vaga abaixo.

REGRAS ABSOLUTAS:
- Cada pergunta DEVE ser baseada em CBI (Competency-Based Interview) — pergunte sobre situacoes REAIS passadas
- PROIBIDO: perguntas hipoteticas ("o que voce faria se...")
- PROIBIDO: perguntas de fit cultural
- Cada pergunta deve avaliar uma skill tecnica diferente
- Calibre a complexidade pela senioridade: {seniority}

VAGA: {enriched.titulo_padronizado} ({seniority})
SKILLS A AVALIAR: {skills}

Para cada pergunta inclua:
- bloom_level: 1-6 (Remembering=1 ... Creating=6) — calibrado por senioridade
- dreyfus_level: 1-5 (Novice=1 ... Expert=5) — calibrado por senioridade

Responda APENAS com JSON:
{{
  "questions": [
    {{
      "question": "texto da pergunta CBI",
      "ideal_answer": "resposta ideal esperada",
      "skill": "skill avaliada",
      "bloom_level": 1-6,
      "dreyfus_level": 1-5,
      "scoring_rubric": {{
        "1-3": "descricao para score baixo",
        "4-6": "descricao para score medio",
        "7-9": "descricao para score alto",
        "10": "descricao para score maximo"
      }}
    }}
  ]
}}"""
    else:
        # Behavioral questions — use trait rankings for selection
        top_traits = trait_rankings[:count] if trait_rankings else []
        traits_desc = ", ".join(
            f"{t.get('trait', 'conscientiousness')} (peso: {t.get('weight', 0.5):.2f})"
            for t in top_traits
        )
        competencies = ", ".join(c.competencia for c in enriched.competencias_comportamentais[:count + 2])

        return f"""Gere {count} perguntas COMPORTAMENTAIS de triagem para a vaga abaixo.

REGRAS ABSOLUTAS:
- Cada pergunta DEVE ser baseada em CBI (Competency-Based Interview) — pergunte sobre situacoes REAIS passadas
- PROIBIDO: perguntas hipoteticas
- PROIBIDO: perguntas de fit cultural
- Cada pergunta deve avaliar um trait Big Five diferente
- Use a afinidade trait-competencia: selecione a competencia que melhor mapeia para cada trait

VAGA: {enriched.titulo_padronizado} ({seniority})
TRAITS A AVALIAR (por ordem de prioridade): {traits_desc}
COMPETENCIAS DISPONIVEIS: {competencies}

Para cada pergunta inclua:
- trait_ocean: qual trait Big Five esta sendo avaliado
- A competencia selecionada deve ter big_five_mapping correspondente ao trait

Responda APENAS com JSON:
{{
  "questions": [
    {{
      "question": "texto da pergunta CBI comportamental",
      "ideal_answer": "resposta ideal esperada",
      "skill": "competencia avaliada",
      "trait_ocean": "openness|conscientiousness|extraversion|agreeableness|stability",
      "scoring_rubric": {{
        "1-3": "descricao para score baixo",
        "4-6": "descricao para score medio",
        "7-9": "descricao para score alto",
        "10": "descricao para score maximo"
      }}
    }}
  ]
}}"""


class WSIQuestionGenerator:
    """Generates WSI screening questions using the full F2+F3+F6 pipeline."""

    def __init__(self):
        self._llm_bigfive = None  # temp=0.1
        self._llm_tech = None     # temp=0.7
        self._llm_behav = None    # temp=0.75

    def _get_llm(self, purpose: str):
        from app.shared.providers.llm_factory import create_tracked_llm

        if purpose == "bigfive":
            if not self._llm_bigfive:
                self._llm_bigfive = create_tracked_llm(
                    temperature=0.1, service_name="WSIQuestionGenerator", operation="bigfive",
                )
            return self._llm_bigfive
        elif purpose == "technical":
            if not self._llm_tech:
                self._llm_tech = create_tracked_llm(
                    temperature=0.7, service_name="WSIQuestionGenerator", operation="gen_technical",
                )
            return self._llm_tech
        else:
            if not self._llm_behav:
                self._llm_behav = create_tracked_llm(
                    temperature=0.75, service_name="WSIQuestionGenerator", operation="gen_behavioral",
                )
            return self._llm_behav

    # -------------------------------------------------------------------
    # F2: Big Five extraction
    # -------------------------------------------------------------------

    def extract_bigfive(
        self, enriched: EnrichedJobDescription
    ) -> BigFiveExtraction:
        """F2 — Extract Big Five profile from enriched JD."""
        prompt = _build_bigfive_prompt(enriched)
        llm = self._get_llm("bigfive")

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            result = BigFiveExtraction(**data)
            logger.info("[WSI:F2] Big Five extracted: O=%.2f C=%.2f E=%.2f A=%.2f S=%.2f",
                       result.openness, result.conscientiousness,
                       result.extraversion, result.agreeableness, result.stability)
            return result

        except Exception as e:
            logger.warning("[WSI:F2] Big Five extraction failed: %s", e)
            return BigFiveExtraction()  # defaults to 0.5 across all traits

    # -------------------------------------------------------------------
    # F3: Trait ranking (deterministic)
    # -------------------------------------------------------------------

    def rank_traits(
        self,
        bigfive: BigFiveExtraction,
        seniority: str,
        role_archetype: str = "default",
    ) -> List[Dict[str, Any]]:
        """F3 — Deterministic trait ranking.

        Formula: score = 0.40 * LLM + 0.35 * Prior + 0.25 * SeniorityBoost
        """
        llm_scores = {
            "openness": bigfive.openness,
            "conscientiousness": bigfive.conscientiousness,
            "extraversion": bigfive.extraversion,
            "agreeableness": bigfive.agreeableness,
            "stability": bigfive.stability,
        }

        prior = ONET_PRIOR_PROFILES.get(role_archetype, ONET_PRIOR_PROFILES["default"])
        boosts = SENIORITY_TRAIT_BOOSTS.get(seniority, {})

        rankings = []
        for trait in llm_scores:
            score = (
                TRAIT_FORMULA_WEIGHTS["llm"] * llm_scores[trait]
                + TRAIT_FORMULA_WEIGHTS["prior"] * prior.get(trait, 0.5)
                + TRAIT_FORMULA_WEIGHTS["seniority_boost"] * boosts.get(trait, 0.0)
            )
            rankings.append({
                "trait": trait,
                "score": round(score, 4),
                "llm_score": llm_scores[trait],
                "prior_score": prior.get(trait, 0.5),
                "boost": boosts.get(trait, 0.0),
            })

        # Sort by score descending, assign ranks and weights
        rankings.sort(key=lambda x: x["score"], reverse=True)
        total_score = sum(r["score"] for r in rankings) or 1.0
        for i, r in enumerate(rankings):
            r["rank"] = i + 1
            r["weight"] = round(r["score"] / total_score, 4)

        logger.info("[WSI:F3] Trait ranking: %s",
                    " > ".join(f"{r['trait']}({r['score']:.3f})" for r in rankings))
        return rankings

    # -------------------------------------------------------------------
    # F6: Question generation
    # -------------------------------------------------------------------

    def generate_questions(
        self,
        enriched: EnrichedJobDescription,
        seniority: str,
        distribution: Dict[str, int],
        trait_rankings: List[Dict[str, Any]],
    ) -> List[GeneratedQuestion]:
        """F6 — Generate WSI screening questions.

        Generates technical and behavioral questions separately with
        different LLM temperatures per WSI methodology.
        """
        all_questions: List[GeneratedQuestion] = []

        n_tech = distribution.get("technical", 5)
        n_behav = distribution.get("behavioral", 2)

        # Generate technical questions
        if n_tech > 0:
            tech_qs = self._generate_block(
                "technical", enriched, seniority, n_tech, trait_rankings
            )
            all_questions.extend(tech_qs)

        # Generate behavioral questions
        if n_behav > 0:
            behav_qs = self._generate_block(
                "behavioral", enriched, seniority, n_behav, trait_rankings
            )
            all_questions.extend(behav_qs)

        # Normalize weights
        total_weight = sum(q.weight for q in all_questions) or 1.0
        for q in all_questions:
            q.weight = round(q.weight / total_weight, 3)

        logger.info("[WSI:F6] Generated %d questions (%d tech + %d behav)",
                    len(all_questions), n_tech, n_behav)
        return all_questions

    def _generate_block(
        self,
        block: Literal["technical", "behavioral"],
        enriched: EnrichedJobDescription,
        seniority: str,
        count: int,
        trait_rankings: List[Dict],
    ) -> List[GeneratedQuestion]:
        """Generate a block of questions (technical or behavioral).

        Governance: circuit breaker + WSI validation + fairness check.
        """
        prompt = _build_questions_prompt(block, enriched, seniority, count, trait_rankings)
        llm = self._get_llm(block)

        # Circuit breaker wraps LLM call
        try:
            from app.shared.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
            try:
                response = circuit_breaker_call(
                    llm.invoke, prompt,
                    circuit_key=f"job_creation:wsi_{block}",
                )
            except CircuitBreakerOpenError:
                logger.warning("[WSI:F6] Circuit breaker OPEN for %s — using fallback", block)
                return self._fallback_questions(block, count)
        except ImportError:
            response = llm.invoke(prompt)

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            raw_questions = data.get("questions", [])[:count]

            questions = []
            for q in raw_questions:
                generated = GeneratedQuestion(
                    question=q.get("question", ""),
                    ideal_answer=q.get("ideal_answer", ""),
                    scoring_rubric=q.get("scoring_rubric", {}),
                    framework="CBI",
                    block=block,
                    competency=block,
                    skill=q.get("skill", ""),
                    trait_ocean=q.get("trait_ocean"),
                    bloom_level=q.get("bloom_level"),
                    dreyfus_level=q.get("dreyfus_level"),
                    weight=1.0 / max(count, 1),
                )

                # WSI validation: reject non-compliant questions
                if self._validate_question(generated):
                    questions.append(generated)
                else:
                    logger.warning("[WSI:F6] Question rejected by validation: %s", generated.question[:50])

            # If validation removed too many, pad with fallbacks
            if len(questions) < count:
                fallbacks = self._fallback_questions(block, count - len(questions))
                questions.extend(fallbacks)

            return questions[:count]

        except Exception as e:
            logger.warning("[WSI:F6] %s question generation failed: %s", block, e)
            return self._fallback_questions(block, count)

    @staticmethod
    def _validate_question(q: GeneratedQuestion) -> bool:
        """WSI compliance validation for generated questions.

        Rejects:
        - Hypothetical questions ("o que voce faria se...")
        - Cultural fit questions
        - Empty questions
        """
        text = q.question.lower()

        if not text or len(text) < 10:
            return False

        # WSI Rule: No hypothetical questions (CBI = real past situations only)
        hypothetical_patterns = [
            "o que voce faria", "o que você faria",
            "como voce faria", "como você faria",
            "imagine que", "suponha que",
            "se voce tivesse", "se você tivesse",
            "what would you do", "how would you handle",
            "imagine a scenario", "suppose you",
        ]
        for pattern in hypothetical_patterns:
            if pattern in text:
                return False

        # WSI Rule: No cultural fit questions
        cultural_fit_patterns = [
            "fit cultural", "cultural fit",
            "valores da empresa", "company values",
            "se encaixa", "encaixar no time",
            "cultura da empresa", "company culture",
        ]
        for pattern in cultural_fit_patterns:
            if pattern in text:
                return False

        return True

    def _fallback_questions(
        self, block: str, count: int
    ) -> List[GeneratedQuestion]:
        """Fallback questions when LLM fails."""
        if block == "technical":
            return [GeneratedQuestion(
                question="Descreva uma situacao real onde voce precisou resolver um problema tecnico complexo. Qual foi o resultado?",
                ideal_answer="Resposta com STAR: situacao concreta, acoes tecnicas especificas, resultado mensuravel",
                framework="CBI",
                block="technical",
                competency="technical",
                skill="problem_solving",
                weight=1.0 / max(count, 1),
            )]
        else:
            return [GeneratedQuestion(
                question="Conte sobre uma situacao em que precisou lidar com pressao ou prazos apertados. Como voce agiu?",
                ideal_answer="Resposta com STAR: situacao de pressao real, estrategia de coping, resultado positivo",
                framework="CBI",
                block="behavioral",
                competency="behavioral",
                skill="stress_management",
                trait_ocean="stability",
                weight=1.0 / max(count, 1),
            )]
