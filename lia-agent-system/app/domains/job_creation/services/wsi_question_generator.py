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

from app.domains.job_creation.helpers.screening_mode_config import (
    SCREENING_MODE_CONFIG,
)
from app.domains.job_creation.schemas import (
    BigFiveExtraction,
    EnrichedJobDescription,
    GeneratedQuestion,
)

logger = logging.getLogger(__name__)

# F3: Trait ranking formula weights
# Sprint B Phase 2: extended to 4-layer hybrid formula
TRAIT_FORMULA_WEIGHTS = {
    "llm": 0.40,
    "prior": 0.35,
    "seniority_boost": 0.25,
}
TRAIT_FORMULA_WEIGHTS_4L = {"llm": 0.40, "onet": 0.20, "culture": 0.15, "dept": 0.25}
TRAIT_FORMULA_WEIGHTS_3L = {"llm": 0.40, "onet": 0.35, "culture": 0.25}

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


def _classify_questions_with_taxonomy(questions: list, llm=None) -> list:
    """Sprint B Phase 3: classifica cada pergunta gerada em skill_probed.

    Modifies questions in-place adding skill_probed + skill_parent + classification_source.
    Fail-soft: erro na classificacao mantem skill_probed=None.

    Sprint F.5 perf note: kept sequential (not parallel) because each LLM
    invoke triggers an audit_service.log_decision coroutine via  # AUDIT-NO-DEMO: docstring text only — no real audit call at this site
    create_tracked_llm callback, and >2 concurrent callbacks corrupt the
    asyncpg pool through a pre-existing event-loop-leak in audit_service.
    The classifier loop adds ~7s but does not block the wizard.
    """
    if not questions:
        return questions
    try:
        from app.domains.job_creation.services.wsi_skill_classifier import (
            WsiSkillClassifier,
        )
        from app.domains.job_creation.services.wsi_skill_taxonomy import parent_of
        clf = WsiSkillClassifier(llm=llm)
        for q in questions:
            try:
                text = q.get("question", "") if isinstance(q, dict) else getattr(q, "question", "")
                result = clf.classify(text)
                skill_id = result["skill_id"]
                parent_id = parent_of(skill_id)
                if isinstance(q, dict):
                    q["skill_probed"] = skill_id
                    q["skill_parent"] = parent_id
                    q["skill_classification_source"] = result["source"]
                else:
                    q.skill_probed = skill_id
                    q.skill_parent = parent_id
                    q.skill_classification_source = result["source"]
            except Exception:
                pass  # fail-soft per-question
    except Exception:
        pass  # fail-soft module-level
    return questions


def _get_blend_score(blend, trait: str) -> float:
    """Extract blend score for trait from BigFiveBlend.

    Stability semantics: alto = bom em ambas BigFiveBlend e CompanyCultureProfile.
    Sem inversao - simplificado apos P0.5 fix (Sprint B Phase 2).
    """
    if blend is None:
        return 0.5
    val = getattr(blend, f"{trait}_score", None)
    return val if val is not None else 0.5


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


def _build_single_question_prompt(
    block: Literal["technical", "behavioral"],
    enriched: "EnrichedJobDescription",
    seniority: str,
    directive: str,
    base_question=None,
    trait_rankings: Optional[List[Dict]] = None,
) -> str:
    """Prompt para gerar/regenerar UMA pergunta CBI (edição ou adição).

    Reusa as REGRAS ABSOLUTAS WSI do _build_questions_prompt (CBI, proibido
    hipotética/fit-cultural). base_question != None => modo edição (revisar a
    pergunta existente conforme `directive`); senão => adição sobre o `directive`
    como tópico.
    """
    is_edit = base_question is not None
    if is_edit:
        _q_text = _q_attr(base_question, "question", "")
        directive_block = (
            f'PERGUNTA ATUAL (revisar mantendo a metodologia):\n"{_q_text}"\n'
            f"AJUSTE PEDIDO PELO RECRUTADOR: {directive}"
        )
    else:
        directive_block = f"TÓPICO DA NOVA PERGUNTA: {directive}"

    if block == "technical":
        skills = ", ".join(s.skill for s in enriched.skills_obrigatorias[:12])
        return f"""Gere UMA única pergunta TÉCNICA de triagem para a vaga abaixo.

REGRAS ABSOLUTAS (metodologia WSI — obrigatórias):
- CBI: pergunte sobre situações REAIS passadas. PROIBIDO hipotéticas ("o que você faria se...").
- PROIBIDO perguntas de fit cultural.
- Calibre a complexidade pela senioridade: {seniority}.

VAGA: {enriched.titulo_padronizado} ({seniority})
SKILLS DISPONÍVEIS: {skills}
{directive_block}

Responda APENAS com JSON válido:
{{
  "questions": [
    {{
      "question": "texto da pergunta CBI",
      "ideal_answer": "resposta ideal esperada",
      "skill": "skill avaliada",
      "bloom_level": 1,
      "dreyfus_level": 1,
      "scoring_rubric": {{"1-3": "baixo", "4-6": "médio", "7-9": "alto", "10": "máximo"}}
    }}
  ]
}}"""
    else:
        competencies = ", ".join(c.competencia for c in enriched.competencias_comportamentais[:10])
        return f"""Gere UMA única pergunta COMPORTAMENTAL de triagem para a vaga abaixo.

REGRAS ABSOLUTAS (metodologia WSI — obrigatórias):
- CBI: pergunte sobre situações REAIS passadas. PROIBIDO hipotéticas.
- PROIBIDO perguntas de fit cultural.
- A pergunta avalia um trait Big Five via competência correspondente.

VAGA: {enriched.titulo_padronizado} ({seniority})
COMPETÊNCIAS DISPONÍVEIS: {competencies}
{directive_block}

Responda APENAS com JSON válido:
{{
  "questions": [
    {{
      "question": "texto da pergunta CBI comportamental",
      "ideal_answer": "resposta ideal esperada",
      "skill": "competência avaliada",
      "trait_ocean": "openness|conscientiousness|extraversion|agreeableness|stability",
      "scoring_rubric": {{"1-3": "baixo", "4-6": "médio", "7-9": "alto", "10": "máximo"}}
    }}
  ]
}}"""


def _q_attr(q, field: str, default=None):
    """Lê um campo de uma pergunta que pode ser dict (model_dump no state) ou GeneratedQuestion."""
    if q is None:
        return default
    if isinstance(q, dict):
        return q.get(field, default)
    return getattr(q, field, default)


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
        bigfive,
        seniority: str,
        role_archetype: str = "default",
        dept_blend=None,  # Optional[BigFiveBlend] Sprint B Phase 2 Layer 4
    ):
        """F3 — delega ao canonico cv_screening (Consolidacao WSI Fase 2.4b).

        Single source of truth: a formula F3 (LLM + O*NET + senioridade/dept-blend)
        agora vive em cv_screening.services.wsi_service.bigfive.rank_traits. Este
        metodo e um THIN ADAPTER (converte BigFiveExtraction -> dict) mantido ate
        a Fase 4 deletar o fork. Comportamento identico (mesma formula/pesos).
        """
        from app.domains.cv_screening.services.wsi_service.bigfive import (
            rank_traits as _canonical_rank_traits,
        )

        llm_scores = {
            "openness": bigfive.openness,
            "conscientiousness": bigfive.conscientiousness,
            "extraversion": bigfive.extraversion,
            "agreeableness": bigfive.agreeableness,
            "stability": bigfive.stability,
        }
        return _canonical_rank_traits(
            llm_scores,
            seniority,
            role_archetype=role_archetype,
            dept_blend=dept_blend,
        )

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

        # Sprint F.4 (iter 3) harness guard — state["question_distribution"]
        # may be explicitly None when the gate classifier resumes via
        # Command(resume=...) before the dispatcher writes the canonical
        # dict. Coerce to the WSI default instead of raising AttributeError
        # (which propagated to wizard_session_service:L958 silent fallback
        # → "vaga foi cortada" reply observed in F.2 retest 2026-05-20).
        if not isinstance(distribution, dict):
            distribution = {"technical": 5, "behavioral": 2}

        n_tech = distribution.get("technical", 5)
        n_behav = distribution.get("behavioral", 2)

        # Sprint F.5 perf fix: technical and behavioral generation are
        # independent LLM calls (~40s + ~18s seq = ~58s). Run them in
        # parallel via ThreadPoolExecutor — wall time drops to max(40s, 18s).
        # Each create_tracked_llm call uses its own ChatAnthropic instance
        # (separate HTTP session), so concurrency is safe.
        import concurrent.futures as _cf_gen
        futures = {}
        with _cf_gen.ThreadPoolExecutor(max_workers=2) as ex:
            if n_tech > 0:
                futures["technical"] = ex.submit(
                    self._generate_block,
                    "technical", enriched, seniority, n_tech, trait_rankings,
                )
            if n_behav > 0:
                futures["behavioral"] = ex.submit(
                    self._generate_block,
                    "behavioral", enriched, seniority, n_behav, trait_rankings,
                )
            # Maintain canonical ordering: technical first, then behavioral
            for block_key in ("technical", "behavioral"):
                fut = futures.get(block_key)
                if fut is not None:
                    try:
                        all_questions.extend(fut.result())
                    except Exception as _fut_exc:
                        logger.warning(
                            "[WSI:F6] %s generation failed in parallel exec: %s",
                            block_key, _fut_exc,
                        )
                        # Fail-soft: contribute fallback questions
                        count = n_tech if block_key == "technical" else n_behav
                        all_questions.extend(self._fallback_questions(block_key, count))

        # Normalize weights
        total_weight = sum(q.weight for q in all_questions) or 1.0
        for q in all_questions:
            q.weight = round(q.weight / total_weight, 3)

        # Sprint B Phase 2 wiring (gap W1): tag every question with a
        # taxonomy skill_id so wsi_question_effectiveness can aggregate
        # outcomes per skill (not per literal question text). Modifies
        # objects in-place; fail-soft via _classify_questions_with_taxonomy
        # internal try/except. Use the behavioral LLM (lower temperature)
        # for classification — it's a categorization task, not generation.
        _classify_questions_with_taxonomy(
            all_questions, llm=self._get_llm("behavioral"),
        )

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
        """Fallback questions when LLM fails. Returns exactly `count` distinct items."""
        w = 1.0 / max(count, 1)
        if block == "technical":
            tpls = [
                ("Descreva uma situacao real onde voce precisou resolver um problema tecnico complexo. Qual foi o resultado?", "problem_solving"),
                ("Descreva um projeto tecnico desafiador que voce liderou. Quais obstaculos encontrou e como os superou?", "project_leadership"),
                ("Como voce aborda revisao de codigo e garantia de qualidade tecnica no desenvolvimento?", "code_quality"),
                ("Descreva uma situacao em que precisou aprender rapidamente uma nova tecnologia para resolver um problema.", "learning_agility"),
                ("Conte sobre uma decisao tecnica dificil que voce tomou. Quais foram os trade-offs considerados?", "technical_decision"),
                ("Como voce depura e resolve problemas em sistemas complexos ou de producao?", "debugging"),
                ("Como voce garante que o codigo que escreve e testavel e mantenivel a longo prazo?", "maintainability"),
            ]
            return [
                GeneratedQuestion(
                    question=tpls[i % len(tpls)][0],
                    ideal_answer="Resposta com STAR: situacao concreta, acoes especificas, resultado mensuravel",
                    framework="CBI",
                    block="technical",
                    competency="technical",
                    skill=tpls[i % len(tpls)][1],
                    weight=w,
                )
                for i in range(count)
            ]
        else:
            tpls = [
                ("Conte sobre uma situacao em que precisou lidar com pressao ou prazos apertados. Como voce agiu?", "stress_management", "stability"),
                ("Descreva uma experiencia trabalhando em colaboracao com pessoas de areas ou culturas diferentes.", "collaboration", "agreeableness"),
                ("Conte sobre um momento em que recebeu um feedback critico. Como voce reagiu e o que fez com ele?", "feedback_receptivity", "openness"),
                ("Descreva uma situacao em que voce identificou um problema antes que ele se tornasse critico.", "proactivity", "conscientiousness"),
                ("Conte sobre um conflito profissional que voce vivenciou. Como voce o resolveu?", "conflict_resolution", "agreeableness"),
                ("Descreva uma situacao em que precisou influenciar ou convencer outros sem ter autoridade direta.", "influence", "extraversion"),
                ("Conte sobre uma falha profissional significativa. O que voce aprendeu e como agiu depois?", "resilience", "stability"),
            ]
            return [
                GeneratedQuestion(
                    question=tpls[i % len(tpls)][0],
                    ideal_answer="Resposta com STAR: situacao real, estrategia aplicada, resultado positivo",
                    framework="CBI",
                    block="behavioral",
                    competency="behavioral",
                    skill=tpls[i % len(tpls)][1],
                    trait_ocean=tpls[i % len(tpls)][2],
                    weight=w,
                )
                for i in range(count)
            ]

    def generate_single_question(
        self,
        *,
        block: Literal["technical", "behavioral"],
        enriched: EnrichedJobDescription,
        seniority: str,
        directive: str,
        base_question: Optional[GeneratedQuestion] = None,
        trait_rankings: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[GeneratedQuestion]:
        """Gera/regenera UMA pergunta CBI (Task #1089 — geração cirúrgica).

        Edição: base_question != None — regenera aquela pergunta conforme
        `directive`, preservando block. Adição: base_question None — gera nova
        pergunta sobre o tópico `directive`.

        A pergunta passa pela MESMA validação WSI (_validate_question) das
        geradas em lote. Retorna None se falhar validação ou parse — o caller
        decide (edição mantém a original; adição cai em _fallback_questions).
        """
        prompt = _build_single_question_prompt(
            block, enriched, seniority, directive, base_question, trait_rankings,
        )
        llm = self._get_llm(block)
        try:
            from app.shared.services.circuit_breaker import (
                circuit_breaker_call, CircuitBreakerOpenError,
            )
            try:
                response = circuit_breaker_call(
                    llm.invoke, prompt, circuit_key=f"job_creation:wsi_single_{block}",
                )
            except CircuitBreakerOpenError:
                logger.warning("[WSI:F6] Circuit breaker OPEN (single %s) — None", block)
                return None
        except ImportError:
            response = llm.invoke(prompt)

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            data = json.loads(content.strip())
            raw = (data.get("questions") or [])
            if not raw:
                return None
            q = raw[0]
            generated = GeneratedQuestion(
                question=q.get("question", ""),
                ideal_answer=q.get("ideal_answer", ""),
                scoring_rubric=q.get("scoring_rubric", {}),
                framework="CBI",
                block=block,
                competency=block,
                skill=q.get("skill", "") or _q_attr(base_question, "skill", ""),
                trait_ocean=q.get("trait_ocean") or _q_attr(base_question, "trait_ocean", None),
                bloom_level=q.get("bloom_level"),
                dreyfus_level=q.get("dreyfus_level"),
                weight=_q_attr(base_question, "weight", 1.0),
            )
            if not self._validate_question(generated):
                logger.warning(
                    "[WSI:F6] single question rejected by WSI validation: %s",
                    generated.question[:60],
                )
                return None
            return generated
        except Exception as exc:  # noqa: BLE001 — fail-soft (caller decide)
            logger.warning("[WSI:F6] single question generation failed: %s", exc)
            return None

    def generate_missing_questions(
        self,
        *,
        enriched: EnrichedJobDescription,
        seniority: str,
        existing_questions: List[GeneratedQuestion],
        screening_mode: str,
        trait_rankings: Optional[List[Dict[str, Any]]] = None,
    ) -> List[GeneratedQuestion]:
        """Auto-completa o pacote até o mínimo do modo (Task #1089 / hard gate).

        Alvos per-senioridade (YAML canonical via block_distribution -- audit
        2026-06-05 #3; ex.: full/senior => 7 téc + 5 comp). Gera apenas
        o DÉFICIT por bloco, cobrindo competências confirmadas ainda NÃO cobertas
        pelas perguntas atuais. Retorna [] quando o pacote já atinge o mínimo.
        """
        # Per-senioridade (YAML canonical) -- audit 2026-06-05 #3. Alinha com
        # o validador (_get_question_distribution); antes 8+4 por modo divergia.
        from app.domains.job_creation.helpers.wsi_distribution import (
            block_distribution,
        )
        _dist = block_distribution(screening_mode, seniority)
        target_tech = _dist["technical"]
        target_behav = _dist["behavioral"]

        cur_tech = sum(1 for q in existing_questions if _q_attr(q, "block", "") == "technical")
        cur_behav = sum(1 for q in existing_questions if _q_attr(q, "block", "") == "behavioral")
        deficit_tech = max(0, target_tech - cur_tech)
        deficit_behav = max(0, target_behav - cur_behav)
        if deficit_tech == 0 and deficit_behav == 0:
            return []

        missing: List[GeneratedQuestion] = []

        if deficit_tech > 0:
            covered = {_q_attr(q, "skill", "") for q in existing_questions if _q_attr(q, "block", "") == "technical"}
            uncovered = [s for s in enriched.skills_obrigatorias if s.skill not in covered]
            enriched_tech = enriched.model_copy(
                update={"skills_obrigatorias": uncovered or enriched.skills_obrigatorias}
            )
            missing.extend(
                self._generate_block("technical", enriched_tech, seniority, deficit_tech, trait_rankings or [])
            )

        if deficit_behav > 0:
            covered = {_q_attr(q, "skill", "") for q in existing_questions if _q_attr(q, "block", "") == "behavioral"}
            uncovered = [c for c in enriched.competencias_comportamentais if c.competencia not in covered]
            enriched_behav = enriched.model_copy(
                update={"competencias_comportamentais": uncovered or enriched.competencias_comportamentais}
            )
            missing.extend(
                self._generate_block("behavioral", enriched_behav, seniority, deficit_behav, trait_rankings or [])
            )

        logger.info(
            "[WSI:F6] auto-complete: +%d téc +%d comp (mode=%s, alvo=%d+%d)",
            deficit_tech, deficit_behav, screening_mode, target_tech, target_behav,
        )
        return missing
