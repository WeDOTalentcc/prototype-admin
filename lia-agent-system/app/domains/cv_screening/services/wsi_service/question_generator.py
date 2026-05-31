"""
WSI Question Generator - Generates scientific questions based on WSI frameworks.
"""
import asyncio
import json
import logging
import re
import uuid
from collections.abc import Callable
from typing import Any, Literal

from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS
from app.domains.ai.services.llm import llm_service
from app.shared.llm.safe_response import safe_llm_with_flag_async, LLMResponseEnvelope
from app.shared.observability.fallback_metrics import inc_wsi_fallback

from .models import (
    safe_json_parse,
    Competency,
    OceanTraitScore,
    SENIORITY_BIGFIVE_TOP_N,
    WSIQuestion,
)

logger = logging.getLogger(__name__)

# Consolidação WSI Fase 2 (2026-05-31): alvos Bloom/Dreyfus por senioridade.
# Bloom (1-6) e Dreyfus (1-5) calibrados pelo nível da vaga — usados como ALVO
# de geração das perguntas dos respectivos frameworks (o nível DEMONSTRADO
# continua sendo medido em ResponseAnalysis a partir da resposta do candidato).
_WSI_BLOOM_TARGET_BY_SENIORITY = {
    "junior": 3, "pleno": 4, "senior": 5, "lead": 5, "executive": 6,
}
_WSI_DREYFUS_TARGET_BY_SENIORITY = {
    "junior": 2, "pleno": 3, "senior": 4, "lead": 4, "executive": 5,
}


class WSIQuestionGenerator:
    """Gerador de perguntas científicas baseado em frameworks e RAG."""

    def __init__(self, llm):
        self.llm = llm
        self._load_rag_templates()

    def _load_rag_templates(self):
        """Carrega templates de perguntas do RAG knowledge base com fallbacks.

        T-1167 / Bug #2 — path resolvido RELATIVO AO __file__ deste módulo.
        Antes usava `Path("lia-agent-system/training/...")` (relativo ao CWD),
        que sob `cd lia-agent-system && uvicorn ...` resolvia para
        `lia-agent-system/lia-agent-system/training/...` — inexistente.
        Resultado: fallback hardcoded minúsculo sempre acionado, modo
        completo (12 perguntas) crashava em Pydantic → 500 → "Falha ao gerar WSI".
        """
        from pathlib import Path

        # __file__ resolvido =
        #   .../lia-agent-system/app/domains/cv_screening/services/wsi_service/question_generator.py
        # parents[0]=wsi_service  parents[1]=services  parents[2]=cv_screening
        # parents[3]=domains      parents[4]=app       parents[5]=lia-agent-system
        _LIA_ROOT = Path(__file__).resolve().parents[5]
        rag_dir = _LIA_ROOT / "training" / "rag_knowledge" / "wsi_methodology"

        # Load frameworks overview with fallback
        frameworks_file = rag_dir / "frameworks_overview.md"
        if frameworks_file.exists():
            self.frameworks_doc = frameworks_file.read_text(encoding="utf-8")
        else:
            logger.warning("RAG frameworks_overview.md not found. Using hardcoded fallback.")
            self.frameworks_doc = """
# WSI Frameworks Overview (Fallback)

## 1. CBI (Competency-Based Interviewing)
Princípio: Comportamentos passados são os melhores preditores de performance futura.
Estrutura: "Conte sobre uma situação..." (STAR: Situation, Task, Action, Result)

## 2. Dreyfus Model
Levels: 1-Novice, 2-Advanced Beginner, 3-Competent, 4-Proficient, 5-Expert

## 3. Bloom's Taxonomy
Levels: 1-Lembrar, 2-Compreender, 3-Aplicar, 4-Analisar, 5-Avaliar, 6-Criar

## 4. Big Five (OCEAN)
Traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
"""

        # Load question templates with fallback
        templates_file = rag_dir / "question_generation_templates.md"
        if templates_file.exists():
            self.question_templates = templates_file.read_text(encoding="utf-8")
        else:
            logger.warning("RAG question_generation_templates.md not found. Using hardcoded fallback.")
            self.question_templates = """
# Question Templates (Fallback)

## CBI Questions
- "Conte sobre um projeto onde você usou {skill}. Qual foi o contexto, sua ação e o resultado?"
- "Descreva uma situação desafiadora envolvendo {skill}. Como você resolveu?"

## Dreyfus Questions
- "De 1 a 5, quanto você domina {skill}? Cite um projeto recente onde aplicou."

## Bloom Questions
- Level 3-4: "Como você implementaria/diagnosticaria {scenario}?"
- Level 5: "Projete uma solução para {complex_problem}"

## Big Five Questions
- "Como você reage quando {stressful_situation}?"
- "Descreva como você trabalha em equipe..."
"""

    async def _extract_ocean_scores(
        self,
        job_description: str,
        behavioral_competencies: list[str] | None = None,
    ) -> list[OceanTraitScore]:
        """F2.5 — Extrai perfil Big Five do JD com rubric NEO-PI-R (Abordagem C).

        Temperatura 0.1: extração estruturada baseada em evidências — não criação.
        Retorna lista ordenada por score decrescente (F3 — ranking).
        """
        _FIVE_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]
        _FALLBACK = {t: {"score": 60, "evidence": [], "confidence": "low"} for t in _FIVE_TRAITS}

        behav_context = (
            f"Competências comportamentais declaradas: {', '.join(behavioral_competencies)}"
            if behavioral_competencies else ""
        )

        prompt = f"""Você é um psicólogo organizacional especialista em avaliação de competências e modelo Big Five (NEO-PI-R).
Analise o Job Description fornecido e extraia o perfil de personalidade requerido pela vaga.
Para cada um dos 5 traits do Big Five, avalie a INTENSIDADE com que o JD REQUER aquele trait.
Baseie-se EXCLUSIVAMENTE no texto do JD — não em suposições sobre o tipo de cargo.

RUBRIC DE AVALIAÇÃO:
- 0–30: O trait não é mencionado ou relevante para este papel
- 31–50: O trait aparece implicitamente; é útil mas não diferenciador
- 51–70: O trait é claramente necessário; mencionado em responsabilidades ou requisitos
- 71–85: O trait é central para o papel; mencionado múltiplas vezes com evidências fortes
- 86–100: O trait é absolutamente crítico; a vaga seria inviável sem ele

REGRAS DE EVIDÊNCIA (OBRIGATÓRIAS):
- O campo "evidence" deve conter CITAÇÕES LITERAIS do JD — trechos exatos entre aspas duplas
  Correto:   "evidence": ["\"lidera equipes multidisciplinares em contextos de alta ambiguidade\""]
  PROIBIDO:  "evidence": ["menciona liderança de equipes"] — paráfrase NÃO é evidência
- Se um trait não tem nenhum trecho literal que o suporte, "evidence" deve ser [] e
  "confidence" deve ser "low" com score ≤ 30
- NUNCA infira traits a partir do nome da empresa, setor, tecnologias usadas ou cargo —
  somente do texto explícito de responsabilidades, requisitos e contexto do JD

REGRAS PARA JD INSUFICIENTE:
- Se o JD tiver menos de 50 palavras úteis disponíveis para análise:
  definir "confidence": "low" para TODOS os traits, independentemente dos scores
  adicionar nota em todos os "evidence": ["[JD insuficiente — análise com baixa confiança]"]

REGRAS PARA SINAIS CONTRADITÓRIOS:
- Quando o JD apresentar sinais que se contradizem para o mesmo trait,
  registrar em "evidence" com prefixo "[SINAL CONTRADITÓRIO]" e reduzir score para 40–55,
  definir "confidence": "medium"

JD enriquecido:
---
{job_description[:2000]}
---
{behav_context}

Retorne APENAS JSON válido (sem texto fora do JSON):
{{
  "big_five_jd": {{
    "openness":          {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "conscientiousness": {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "extraversion":      {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "agreeableness":     {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }},
    "stability":         {{ "score": 0, "evidence": ["\"trecho literal do JD\""], "confidence": "high|medium|low" }}
  }}
}}"""
        try:
            response = await self.llm.safe_invoke(prompt, temperature=0.1, max_tokens=800)
            # F6.B5 fix (2026-05-20): safe_invoke retorna string (não AIMessage)
            parsed = safe_json_parse(response, fallback={"big_five_jd": _FALLBACK})
            data = parsed.get("big_five_jd") or _FALLBACK
            if not isinstance(data, dict) or not any(t in data for t in _FIVE_TRAITS):
                data = _FALLBACK
        except Exception as e:
            logger.error(f"F2.5 OCEAN extraction failed: {e} — using fallback")
            data = _FALLBACK

        result = []
        for t in _FIVE_TRAITS:
            if t not in data:
                continue
            entry = data[t]
            result.append(OceanTraitScore(
                trait=t,
                score=max(0, min(100, int(entry.get("score", 60)))),
                confidence=entry.get("confidence", "medium"),
                evidence=entry.get("evidence", []),
            ))
        return sorted(result, key=lambda x: x.score, reverse=True)

    def _select_traits_by_seniority(
        self,
        ranked_traits: list[OceanTraitScore],
        seniority: str,
    ) -> list[OceanTraitScore]:
        """F5 — Seleciona top-N traits conforme senioridade da vaga."""
        key = seniority.lower().strip().replace(" ", "_").replace("-", "_")
        n = SENIORITY_BIGFIVE_TOP_N.get(key, 3)
        return ranked_traits[:n]

    async def generate_all(
        self,
        competencies: list[Competency],
        mode: Literal["compact", "full"] = "compact",
        job_description: str | None = None,
        seniority: str | None = None,
    ) -> list[WSIQuestion]:
        """
        Gera todas as perguntas para as competências selecionadas.

        Estratégia:
        - compact: 7 perguntas  (~14 min WhatsApp)
        - full:    12 perguntas (~25 min WhatsApp)

        Ambos os modos extraem 5 técnicas + 5 comportamentais do JD.
        A metodologia seleciona as mais relevantes por peso e is_critical.
        CBI cobre técnico E comportamental em ambos os modos.

        Distribuição compact (7 perguntas):
        - CBI técnico:        2 perguntas  (top 2 técnicas por is_critical + peso)
        - CBI comportamental: 1 pergunta   (top 1 comportamental por peso)
        - Dreyfus:            1 pergunta   (3ª técnica — autodeclaração)
        - Bloom:              1 pergunta   (4ª técnica — microcase)
        - Big Five:           2 perguntas  (2ª e 3ª comportamentais — fit cultural/situacional OCEAN)

        Distribuição full (12 perguntas):
        - CBI técnico:        3 perguntas  (top 3 técnicas por is_critical + peso)
        - CBI comportamental: 3 perguntas  (top 3 comportamentais por peso)
        - Dreyfus:            2 perguntas  (4ª e 5ª técnicas — autodeclaração)
        - Bloom:              2 perguntas  (microcase — técnica de maior bloom_level + outra técnica crítica)
        - Big Five:           2 perguntas  (4ª e 5ª comportamentais — fit cultural/situacional)
        """
        if not competencies:
            raise ValueError("At least 1 competency is required to generate questions")

        if len(competencies) < 2:
            logger.warning(f"Only {len(competencies)} competencies provided. Minimum 2 recommended for WSI screening.")

        # Separar e ordenar por relevância: is_critical primeiro, depois peso decrescente
        technical = sorted(
            [c for c in competencies if c.type == "technical"],
            key=lambda c: (c.is_critical, c.weight),
            reverse=True
        )
        behavioral = sorted(
            [c for c in competencies if c.type in ("behavioral", "cultural")],
            key=lambda c: c.weight,
            reverse=True
        )

        if not technical:
            logger.warning("No technical competencies provided. Using behavioral for all questions.")
            technical = behavioral

        # D3/D4 quality warnings: alertar quando abaixo dos mínimos ideais da spec WSI F8
        if len(technical) < 9:
            logger.warning(
                f"WSI question generation: only {len(technical)} technical competencies provided "
                f"(spec minimum: 9). Question quality may be reduced for {'compact' if mode == 'compact' else 'full'} mode."
            )
        if len(behavioral) < 5:
            logger.warning(
                f"WSI question generation: only {len(behavioral)} behavioral competencies provided "
                f"(spec minimum: 5). Big Five questions may repeat competencies."
            )

        # F2.5 / F3 / F5 pipeline — quando job_description disponível
        selected_traits: list[OceanTraitScore] = []
        if job_description:
            behav_names = [c.name for c in behavioral]
            ranked = await self._extract_ocean_scores(job_description, behav_names)
            selected_traits = self._select_traits_by_seniority(ranked, seniority or "pleno")
            logger.info(f"WSI F2.5 OCEAN ranked: {[(t.trait, t.score) for t in ranked]}")
            logger.info(f"WSI F5 selected ({len(selected_traits)} for '{seniority}'): {[t.trait for t in selected_traits]}")

        # F5 — distribuição adaptativa por senioridade (WSI-8)
        _norm_sen = (seniority or "pleno").lower().strip().replace(" ", "_").replace("-", "_")
        _mode_dists = SENIORITY_DISTRIBUTIONS.get(mode, SENIORITY_DISTRIBUTIONS["full"])
        _dist = _mode_dists.get(_norm_sen, _mode_dists.get("senior", list(_mode_dists.values())[0]))
        _tech_target = _dist["technical"]
        _behav_target = _dist["behavioral"]

        if mode == "compact":
            _has_dreyfus = _tech_target >= 2
            _has_bloom = _tech_target >= 3
            _cbi_tech_n = max(1, _tech_target - int(_has_dreyfus) - int(_has_bloom))
            _dreyfus_n = int(_has_dreyfus)
            _bloom_n = int(_has_bloom)
            _cbi_behav_n = 1
            _bigfive_n = _behav_target - 1
        else:  # full
            _dreyfus_n = min(2, max(0, _tech_target - 3))
            _bloom_n = min(2, max(0, _tech_target - 1 - _dreyfus_n))
            _cbi_tech_n = max(1, _tech_target - _dreyfus_n - _bloom_n)
            _cbi_behav_n = max(1, _behav_target - 2)
            _bigfive_n = _behav_target - _cbi_behav_n

        logger.info(
            f"WSI F5 generate_all distribution ({_norm_sen}/{mode}): "
            f"cbi_tech={_cbi_tech_n}, dreyfus={_dreyfus_n}, bloom={_bloom_n}, "
            f"cbi_behav={_cbi_behav_n}, bigfive={_bigfive_n}"
        )

        jd = job_description  # alias curto para legibilidade

        # F6.O1 — pré-computa plano determinístico de geração ANTES de disparar gather.
        # Cada item: (gen_fn, competency, kwargs_dict). Ordem preservada para distribuição final.
        # BigFive trait uniqueness: `used_bf` set é mutado SOMENTE neste loop síncrono pré-gather,
        # eliminando race condition em execução paralela.
        generation_plan: list[tuple[Callable, Any, dict]] = []

        # --- CBI técnico ---
        for comp in technical[:_cbi_tech_n]:
            generation_plan.append((
                self._generate_cbi_question, comp,
                {"jd_text": jd, "skill_or_trait": comp.name, "question_category": "technical"},
            ))

        # --- CBI comportamental ---
        for comp in behavioral[:_cbi_behav_n]:
            generation_plan.append((
                self._generate_cbi_question, comp,
                {"jd_text": jd, "skill_or_trait": comp.name, "question_category": "behavioral"},
            ))

        # --- Dreyfus (autodeclaração de proficiência) ---
        dreyfus_offset = _cbi_tech_n
        for i in range(_dreyfus_n):
            comp = technical[dreyfus_offset + i] if len(technical) > dreyfus_offset + i else technical[-1]
            generation_plan.append((
                self._generate_dreyfus_question, comp,
                {"jd_text": jd, "skill_or_trait": comp.name, "question_category": "technical"},
            ))

        # --- Bloom (microcase situacional) ---
        bloom_offset = dreyfus_offset + _dreyfus_n
        for i in range(_bloom_n):
            comp = technical[bloom_offset + i] if len(technical) > bloom_offset + i else technical[0]
            generation_plan.append((
                self._generate_bloom_question, comp,
                {"jd_text": jd, "skill_or_trait": comp.name, "question_category": "technical"},
            ))

        # --- Big Five: F6.6 — seleção por afinidade de trait (fallback: posicional) ---
        # Pré-alocação SÍNCRONA de traits ANTES do gather — preserva uniqueness sem race.
        used_bf: set = set()
        for i in range(_bigfive_n):
            trait = selected_traits[i].trait if i < len(selected_traits) else None
            if trait and behavioral:
                bf_comp, idx = self._select_comp_by_trait(trait, behavioral, used_bf)
                used_bf.add(idx)
            else:
                available = [j for j in range(len(behavioral)) if j not in used_bf]
                idx = available[0] if available else 0
                bf_comp = behavioral[idx] if behavioral else technical[0]
                used_bf.add(idx)
            generation_plan.append((
                self._generate_bigfive_question, bf_comp,
                {
                    "jd_text": jd,
                    "skill_or_trait": trait or bf_comp.name,
                    "question_category": "behavioral",
                    "ocean_trait": trait,
                },
            ))

        # F6.O1 — dispara TODAS as gerações em paralelo via asyncio.gather.
        # Ganho esperado: ~5x (de ~103-167s sequencial para ~25-35s paralelo) —
        # cada LLM call Anthropic é ~17-26s; sequencial == soma, paralelo == max.
        # `return_exceptions=False`: propaga primeira falha (comportamento idêntico ao loop original com await).
        logger.info(
            f"WSI F6.O1 dispatching {len(generation_plan)} LLM generations in parallel via asyncio.gather"
        )
        questions = list(await asyncio.gather(*[
            self._generate_with_validation(gen_fn, comp, **kwargs)
            for gen_fn, comp, kwargs in generation_plan
        ]))

        target_count = _dist["total"]

        if len(questions) < target_count:
            logger.warning(f"Generated only {len(questions)}/{target_count} questions due to limited competencies")

        return questions[:target_count]

    # -----------------------------------------------------------------------
    # F6.8 — Validação automática pós-geração (determinística + LLM anchoring)
    # -----------------------------------------------------------------------

    _BIAS_MARKERS_RE = re.compile(
        r"\b(homem|mulher|masculino|feminino|gênero|raça|etnia|origem|religião|"
        r"casad[oa]|filh[oa]s?|grávid[ao]|deficiência)\b",
        re.IGNORECASE,
    )
    _HYPOTHETICAL_RE = re.compile(
        r"\b(como você faria se|imagine que|suponha que|se você fosse|"
        r"o que você faria se|e se você)\b",
        re.IGNORECASE,
    )
    _PAST_VERB_RE = re.compile(
        r"\b(conte|descreva|fale|dê um exemplo|me diga|relat[ea]|compartilhe)\b",
        re.IGNORECASE,
    )

    def _validate_deterministic(self, text: str) -> list[str]:
        """F6.8 Estágio 1 — verificações determinísticas (regex, ~0 ms).

        Returns:
            Lista de flags de falha (vazia = aprovado).
        """
        flags: list[str] = []
        word_count = len(text.split())
        if word_count < 15 or word_count > 80:
            flags.append(f"length_out_of_range:{word_count}_words")
        if self._HYPOTHETICAL_RE.search(text):
            flags.append("hypothetical_phrasing")
        if self._BIAS_MARKERS_RE.search(text):
            flags.append("bias_marker_detected")
        if not self._PAST_VERB_RE.search(text):
            flags.append("missing_situational_verb")
        return flags

    async def _validate_jd_anchor(
        self,
        question_text: str,
        jd_text: str,
        skill_or_trait: str,
        question_category: str = "technical",
    ) -> dict:
        """F6.8.1 — Validação de ancoragem no JD via LLM (temperature=0.0).

        Returns dict com campos: is_anchored, evidence_in_jd, anchor_type,
        confidence, anchor_explanation, suggestion.
        """
        system_prompt = (
            "Você é um auditor de qualidade de perguntas de triagem.\n"
            "Sua única tarefa é verificar se a pergunta gerada é ANCORADA no Job Description fornecido.\n\n"
            "Uma pergunta é ANCORADA quando:\n"
            "- Refere-se a uma responsabilidade, skill, contexto ou desafio EXPLICITAMENTE mencionado no JD\n"
            "- Não poderia ser feita com a mesma especificidade para qualquer outra vaga\n\n"
            "Uma pergunta NÃO é ancorada quando:\n"
            '- Poderia ser feita para qualquer cargo do mesmo nível ("Descreva um projeto desafiador...")\n'
            "- Refere-se a skills ou contextos ausentes do JD\n"
            "- É genérica o suficiente para ser reutilizada em vagas completamente diferentes\n\n"
            "REGRAS:\n"
            "- Retorne APENAS o JSON. Sem texto fora do JSON.\n"
            '- "evidence_in_jd" deve ser uma citação LITERAL do JD entre aspas — nunca paráfrase\n'
            '- Se a pergunta não for ancorada, "evidence_in_jd" deve ser "" (string vazia)\n'
            '- "anchor_type" classifica o tipo de ancoragem encontrada'
        )
        user_prompt = (
            f"Job Description da vaga (texto completo ou trecho relevante):\n"
            f"---\n{jd_text[:3000]}\n---\n\n"
            f"Skill ou trait que a pergunta avalia: {skill_or_trait}\n"
            f"Tipo de pergunta: {question_category} (technical | behavioral)\n\n"
            f'Pergunta gerada para validar:\n"{question_text}"\n\n'
            "Retorne o seguinte JSON (sem texto fora do JSON):\n"
            "{\n"
            '  "is_anchored": true|false,\n'
            '  "evidence_in_jd": "trecho literal exato do JD (vazio se não ancorada)",\n'
            '  "anchor_type": "responsibility | skill | context | challenge | none",\n'
            '  "confidence": "high | medium | low",\n'
            '  "anchor_explanation": "em 1 frase: por que esta pergunta é ou não é específica para este JD",\n'
            '  "suggestion": "reformulação sugerida apenas se is_anchored = false, senão string vazia"\n'
            "}"
        )
        full_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
        try:
            response = await self.llm.safe_invoke(full_prompt, temperature=0.0, max_tokens=300)
            # F6.B5 fix (2026-05-20): safe_invoke retorna string (não AIMessage)
            result = safe_json_parse(response, fallback=None)
            if result and isinstance(result, dict) and "is_anchored" in result:
                return result
        except Exception as e:
            logger.warning(f"WSI F6.8.1 anchor validation failed: {e}")
        # Fallback: assume ancorada para não bloquear indefinidamente
        return {
            "is_anchored": True,
            "evidence_in_jd": "",
            "anchor_type": "none",
            "confidence": "low",
            "anchor_explanation": "Validação de ancoragem indisponível — aprovado automaticamente.",
            "suggestion": "",
        }

    async def _generate_with_validation(
        self,
        gen_fn: Callable,
        competency: "Competency",
        jd_text: str | None = None,
        skill_or_trait: str | None = None,
        question_category: str = "technical",
        **gen_kwargs,
    ) -> "WSIQuestion":
        """F6.8 wrapper — gera pergunta com até 3 tentativas de validação.

        Fluxo:
        1. Gera pergunta via gen_fn(competency, **gen_kwargs)
        2. Estágio 1: _validate_deterministic → se falhar, regenera com hint
        3. Estágio 2: _validate_jd_anchor (se jd_text fornecido) → se falhar, regenera com suggestion
        4. Após 3 falhas em qualquer estágio, marca needs_manual_review=True e retorna

        Hardening C.1: chama ``inc_wsi_fallback(framework, "validation_fail")``
        quando atinge MAX_RETRIES em qualquer estagio (sinal canary REGRA 4 --
        question gerada com manual_review=True conta como degradation real).
        """
        MAX_RETRIES = 3
        last_question: WSIQuestion | None = None
        improvement_hint: str | None = None

        # Hardening C.1 -- mapping gen_fn -> framework label canonical
        # (espelha allow-list em app/shared/observability/fallback_metrics.py).
        _framework_label = {
            "_generate_cbi_question": "CBI",
            "_generate_dreyfus_question": "Dreyfus",
            "_generate_bloom_question": "Bloom",
            "_generate_bigfive_question": "BigFive",
        }.get(getattr(gen_fn, "__name__", ""), None)

        for attempt in range(1, MAX_RETRIES + 1):
            if improvement_hint:
                gen_kwargs["improvement_hint"] = improvement_hint

            question = await gen_fn(competency, **gen_kwargs)
            last_question = question

            # Estágio 1 — determinístico
            det_flags = self._validate_deterministic(question.question_text)
            if det_flags:
                logger.warning(
                    f"WSI F6.8 det. flags (attempt {attempt}/{MAX_RETRIES}) "
                    f"for '{competency.name}': {det_flags}"
                )
                improvement_hint = (
                    f"A pergunta anterior falhou nas seguintes verificações automáticas: {det_flags}. "
                    "Corrija: use verbo situacional no imperativo (Conte/Descreva), "
                    "mantenha entre 15 e 80 palavras, evite linguagem hipotética e marcadores de viés."
                )
                if attempt == MAX_RETRIES:
                    question.needs_manual_review = True
                    question.validation_flags = {"deterministic": det_flags}
                    logger.error(
                        f"WSI F6.8 max retries reached for '{competency.name}'. "
                        "Marking needs_manual_review=True."
                    )
                    # Hardening C.1 -- REGRA 4 canary signal
                    if _framework_label:
                        inc_wsi_fallback(_framework_label, "validation_fail")
                    return question
                continue

            # Estágio 2 — ancoragem no JD (somente se jd_text disponível)
            if jd_text and skill_or_trait:
                anchor = await self._validate_jd_anchor(
                    question_text=question.question_text,
                    jd_text=jd_text,
                    skill_or_trait=skill_or_trait,
                    question_category=question_category,
                )
                if not anchor.get("is_anchored", True):
                    logger.warning(
                        f"WSI F6.8.1 not anchored (attempt {attempt}/{MAX_RETRIES}) "
                        f"for '{competency.name}': {anchor.get('anchor_explanation')}"
                    )
                    suggestion = anchor.get("suggestion", "")
                    improvement_hint = (
                        f"A pergunta anterior não está ancorada no Job Description. "
                        f"Sugestão de reformulação: {suggestion}"
                        if suggestion else
                        "A pergunta anterior é genérica demais. Referencie explicitamente "
                        "uma responsabilidade ou skill mencionada no JD."
                    )
                    if attempt == MAX_RETRIES:
                        question.needs_manual_review = True
                        question.validation_flags = {
                            "anchor": anchor,
                            "attempts": MAX_RETRIES,
                        }
                        logger.error(
                            f"WSI F6.8.1 max retries reached for '{competency.name}'. "
                            "Marking needs_manual_review=True."
                        )
                        # Hardening C.1 -- REGRA 4 canary signal
                        if _framework_label:
                            inc_wsi_fallback(_framework_label, "validation_fail")
                        return question
                    continue
                # Persiste metadados de ancoragem nos flags (auditável)
                question.validation_flags = {
                    "anchor_type": anchor.get("anchor_type"),
                    "confidence": anchor.get("confidence"),
                    "evidence_in_jd": anchor.get("evidence_in_jd", ""),
                }

            return question

        # Nunca deveria chegar aqui, mas retorna last_question por segurança
        if last_question:
            last_question.needs_manual_review = True
        return last_question  # type: ignore[return-value]

    async def _generate_question_with_envelope(
        self,
        prompt: str,
        fallback_data: dict,
        framework_label: str,
        competency_name: str,
        bind_kwargs: dict | None = None,
    ) -> LLMResponseEnvelope:
        """P0.D SIBLINGS canonical helper (audit 2026-05-21).

        Envelopa todas as chamadas LLM dos 4 _generate_X_question() em
        ``safe_llm_with_flag_async`` (canonical helper em
        ``app.shared.llm.safe_response``). Em failure, envelope vem com
        ``success=False`` + ``fallback_used=True`` + ``failure_mode``
        classificado + ``error_message`` populated.

        Resultado anterior (silent fallback): pergunta template stock caia
        no payload sem flag, recrutador via WSIQuestion como se fosse output
        legitimo da LIA. Pattern F6.B3 (audit 2026-05-20) eliminado.

        Args:
            prompt: prompt completo a enviar a LLM.
            fallback_data: dict canonical com mesma shape do JSON LLM esperado;
                eh injetado como ``safe_json_parse`` fallback E como
                ``envelope.fallback_data`` em caso de excecao da call LLM.
            framework_label: CBI | Dreyfus | Bloom | BigFive -- usado pra
                ``inc_wsi_fallback`` Prometheus counter (Grafana alarm).
            competency_name: nome da competencia -- pra contexto de log
                estruturado em failure.
            bind_kwargs: kwargs pra ``self.llm.claude.bind(...)`` (temperature,
                max_tokens). Cada framework usa valores diferentes.

        Returns:
            LLMResponseEnvelope com ``success / data / fallback_used /
            failure_mode / error_message`` populated. Caller transforma
            ``envelope.data`` (dict) em ``WSIQuestion(...)`` e propaga campos
            de envelope pros fields canonical da pergunta.

        REGRA 4 (CLAUDE.md): handlers tocando LLM/critical IO DEVEM fail-loud.
        ADR-001 (helper DRY): 4 SIBLINGS compartilham mesmo invariant -- extract
        elimina divergence + reduz LOC.
        """
        bind_kwargs = bind_kwargs or {}

        async def _invoke_llm() -> dict:
            response = await self.llm.claude.bind(**bind_kwargs).ainvoke(prompt)
            return safe_json_parse(response.content, fallback=fallback_data)

        envelope = await safe_llm_with_flag_async(
            _invoke_llm,
            fallback_data=fallback_data,
            # P0.D nota: needs_manual_review_on_fail=False -- questions
            # ja tem field ``needs_manual_review`` proprio (F6.8 ancoragem JD).
            # Sinal de LLM failure vive em fallback_used / llm_failure_mode
            # separado. Nao-conflitamos a semantica do campo F6.8.
            needs_manual_review_on_fail=False,
        )

        if not envelope.success:
            # pii-logs ok: nome de entidade/config (nao PII per LGPD Art.5 V -- pessoa natural)
            logger.error(
                "Failed to generate %s question for %s: %s (failure_mode=%s)",
                framework_label,
                competency_name,
                envelope.error_message,
                envelope.failure_mode.value,
            )
            # REGRA 4 sensor -- Prometheus counter for Grafana alarm
            inc_wsi_fallback(framework_label, "llm_error")

        return envelope

    async def _generate_cbi_question(
        self, competency: Competency, improvement_hint: str | None = None
    ) -> WSIQuestion:
        """Gera pergunta CBI (contextual) para competência."""
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA (baseada em validação anterior):\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta CBI (Competency-Based Interviewing) para avaliar: **{competency.name}**

Nível da vaga: {competency.seniority_level}
Tipo: {competency.type}

Princípio CBI: "Comportamentos passados são os melhores preditores de performance futura."

Estrutura: "Conte sobre uma situação em que [contexto específico]. O que você fez e qual foi o resultado?"

Exemplos de referência do RAG:
{self.question_templates[:2000]}
{hint_block}
Responda APENAS em JSON:
{{
  "framework": "CBI",
  "question_type": "contextual",
  "question_text": "[Pergunta aqui]",
  "expected_signals": ["Contexto claro", "Ação técnica", "Resultado mensurável"],
  "scoring_criteria": {{
    "score_5": "Contexto complexo + decisões avançadas + impacto quantificado",
    "score_3": "Contexto claro + ação técnica + resultado visível",
    "score_1": "Contexto vago + ação genérica + sem resultado"
  }}
}}"""

        # P0.D SIBLINGS canonical (audit 2026-05-21): envelope via DRY helper.
        cbi_fallback = {
            "framework": "CBI",
            "question_type": "contextual",
            "question_text": (
                f"Conte sobre uma experiência onde você aplicou {competency.name} "
                "em um projeto real. Qual foi o contexto, sua ação e o resultado?"
            ),
            "expected_signals": ["Contexto claro", "Ação específica", "Resultado mensurável"],
            "scoring_criteria": {
                "score_5": "Projeto complexo + decisões avançadas + impacto quantificado",
                "score_3": "Projeto real + ação técnica + resultado visível",
                "score_1": "Projeto vago + ação genérica",
            },
        }
        envelope = await self._generate_question_with_envelope(
            prompt=prompt,
            fallback_data=cbi_fallback,
            framework_label="CBI",
            competency_name=competency.name,
            bind_kwargs={"temperature": 0.7, "max_tokens": 2000},
        )
        data = envelope.data if envelope.success else (envelope.data or cbi_fallback)

        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="CBI",
            question_type="contextual",
            block=competency.type,
            question_text=data.get("question_text") or f"Conte sobre uma situação em que você precisou utilizar {competency.name} para resolver um problema técnico. Qual foi o contexto, sua ação e o resultado obtido?",
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Contexto", "Ação", "Resultado"]),
            scoring_criteria=data.get("scoring_criteria", {}),
            is_critical=competency.is_critical,
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )

    async def _generate_dreyfus_question(
        self, competency: Competency, improvement_hint: str | None = None
    ) -> WSIQuestion:
        """Gera pergunta Dreyfus (autodeclaração) para competência."""
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta Dreyfus (autodeclaração) para avaliar: **{competency.name}**

Estrutura: "De 1 a 5, quanto você domina [tecnologia]? Pode citar um projeto recente onde aplicou?"

Combina:
- Autodeclaração (score 1-5)
- Validação contextual (projeto real)
{hint_block}
Responda APENAS em JSON com mesma estrutura anterior."""

        # P0.D SIBLINGS canonical (audit 2026-05-21): envelope via DRY helper.
        dreyfus_fallback = {
            "framework": "Dreyfus",
            "question_type": "autodeclaration",
            "question_text": (
                f"De 1 a 5, quanto você se considera proficiente em {competency.name}? "
                "Pode citar um projeto recente onde aplicou essa competência?"
            ),
            "expected_signals": ["Autodeclaração honesta", "Projeto real mencionado", "Contexto de aplicação"],
            "scoring_criteria": {
                "score_5": "Expert com projeto complexo e impacto mensurável",
                "score_3": "Competente com projeto real e aplicação prática",
                "score_1": "Iniciante sem experiência prática",
            },
        }
        envelope = await self._generate_question_with_envelope(
            prompt=prompt,
            fallback_data=dreyfus_fallback,
            framework_label="Dreyfus",
            competency_name=competency.name,
            bind_kwargs={"temperature": 0.75, "max_tokens": 2000},
        )
        data = envelope.data if envelope.success else (envelope.data or dreyfus_fallback)

        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="Dreyfus",
            question_type="autodeclaration",
            block=competency.type,
            dreyfus_level=_WSI_DREYFUS_TARGET_BY_SENIORITY.get(
                (competency.seniority_level or "pleno"), 3
            ),
            question_text=data.get("question_text") or f"Descreva sua experiência com {competency.name} em projetos reais. De 1 a 5, como você avalia sua proficiência e em que tipo de cenário aplicou?",
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Autodeclaração", "Projeto", "Contexto"]),
            scoring_criteria=data.get("scoring_criteria", {}),
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )

    async def _generate_bloom_question(
        self, competency: Competency, improvement_hint: str | None = None
    ) -> WSIQuestion:
        """Gera microcase Bloom para competência."""
        seniority_level_map = {
            "junior": 3,
            "pleno": 4,
            "senior": 4,
            "lead": 5,
            "executive": 5
        }
        bloom_level = seniority_level_map.get(competency.seniority_level, 3)
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )
        prompt = f"""Gere UMA pergunta tipo microcase (Bloom Level {bloom_level}) para: **{competency.name}**

Nível cognitivo esperado: {"APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"}

Exemplos:
- Level 3 (Aplicar): "Como você implementaria [solução]?"
- Level 4 (Analisar): "Como diagnosticaria [problema]?"
- Level 5 (Criar): "Projete [arquitetura/solução]"
{hint_block}
Responda APENAS em JSON."""

        cognitive_level = "APLICAR" if bloom_level == 3 else "ANALISAR" if bloom_level == 4 else "CRIAR"

        # P0.D SIBLINGS canonical (audit 2026-05-21): envelope via DRY helper.
        bloom_fallback = {
            "framework": "Bloom",
            "question_type": "microcase",
            "question_text": (
                f"Como você abordaria um desafio técnico envolvendo {competency.name}? "
                "Descreva sua estratégia de solução."
            ),
            "expected_signals": ["Raciocínio técnico", "Abordagem estruturada", "Conhecimento aplicado"],
            "scoring_criteria": {
                "score_5": f"Nível {cognitive_level}: Solução completa, trade-offs considerados, best practices",
                "score_3": f"Nível {cognitive_level}: Solução funcional com conceitos corretos",
                "score_1": "Conhecimento teórico sem aplicação prática",
            },
        }
        envelope = await self._generate_question_with_envelope(
            prompt=prompt,
            fallback_data=bloom_fallback,
            framework_label="Bloom",
            competency_name=competency.name,
            bind_kwargs={"temperature": 0.75, "max_tokens": 2000},
        )
        data = envelope.data if envelope.success else (envelope.data or bloom_fallback)

        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="Bloom",
            question_type="microcase",
            block=competency.type,
            bloom_level=_WSI_BLOOM_TARGET_BY_SENIORITY.get(
                (competency.seniority_level or "pleno"), 4
            ),
            question_text=data.get("question_text") or f"Descreva como você abordaria um desafio técnico envolvendo {competency.name}. Explique sua estratégia, decisões e trade-offs considerados.",
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Raciocínio", "Abordagem", "Conhecimento"]),
            scoring_criteria=data.get("scoring_criteria", {}),
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )

    def _select_comp_by_trait(
        self,
        trait: str,
        behavioral: list["Competency"],
        used_indices: set,
    ) -> tuple:
        """F6.6 — Seleciona competência comportamental por afinidade de trait OCEAN.

        Estratégia:
        1. Match exato: busca competência com big_five_mapping == trait
        2. Fallback posicional: próxima disponível não usada
        3. Último recurso: primeira da lista

        Args:
            trait: trait OCEAN alvo (openness|conscientiousness|extraversion|agreeableness|stability)
            behavioral: lista ordenada de competências comportamentais
            used_indices: índices já utilizados (evita repetição)

        Returns:
            Tuple[Competency, int] — competência selecionada e seu índice
        """
        # 1. Match exato por big_five_mapping
        for i, comp in enumerate(behavioral):
            if i not in used_indices and comp.big_five_mapping == trait:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"WSI F6.6 trait-match (exact): {trait} → {comp.name} (idx={i})")
                return comp, i
        # 2. Fallback posicional — próxima disponível
        for i, comp in enumerate(behavioral):
            if i not in used_indices:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"WSI F6.6 trait-match (fallback positional): {trait} → {comp.name} (idx={i})")
                return comp, i
        # 3. Último recurso — reusar primeira
        logger.warning(f"WSI F6.6 trait-match: no available competency for {trait}, reusing behavioral[0]")
        return behavioral[0], 0

    async def _generate_bigfive_question(
        self,
        competency: Competency,
        ocean_trait: str | None = None,
        improvement_hint: str | None = None,
    ) -> WSIQuestion:
        """Gera pergunta Big Five (situacional) para competência.

        Args:
            competency: Competência a avaliar
            ocean_trait: Trait OCEAN alvo (F6.6). Quando fornecido, calibra a pergunta
                         para revelar especificamente esse trait.
            improvement_hint: Sugestão de melhoria da validação F6.8.1 (ancoragem no JD).
        """
        _TRAIT_LABELS = {
            "openness":          "Abertura a mudanças — inovação, curiosidade, aprendizado",
            "conscientiousness": "Organização e disciplina — entregas, rigor, método",
            "extraversion":      "Sociabilidade — comunicação, assertividade, energia",
            "agreeableness":     "Cooperação — empatia, colaboração, gestão de stakeholders",
            "stability":         "Estabilidade emocional — resiliência sob pressão",
        }
        trait_context = (
            f"\nTrait OCEAN alvo: {ocean_trait} ({_TRAIT_LABELS.get(ocean_trait, '')})\n"
            "A pergunta deve revelar especificamente este trait."
            if ocean_trait else ""
        )
        hint_block = (
            f"\n\nINSTRUÇÃO DE MELHORIA:\n{improvement_hint}\n"
            if improvement_hint else ""
        )

        prompt = f"""Gere UMA pergunta Big Five (situacional) para avaliar: **{competency.name}**

Tipo: Comportamental/Cultural

Estrutura: "Como você reage quando...", "Descreva uma situação em que..."

Foco em traços OCEAN:
- Openness: Inovação, aprendizado
- Conscientiousness: Organização, entrega
- Extraversion: Comunicação, liderança
- Agreeableness: Colaboração
- Emotional Stability: Pressão
{trait_context}{hint_block}
Responda APENAS em JSON."""

        # P0.D SIBLINGS canonical (audit 2026-05-21): envelope via DRY helper.
        bigfive_fallback = {
            "framework": "BigFive",
            "question_type": "situational",
            "question_text": (
                f"Descreva uma situação recente onde você demonstrou {competency.name}. "
                "Como você lidou com o desafio e qual foi o resultado?"
            ),
            "expected_signals": ["Situação real", "Comportamento específico", "Resultado alcançado"],
            "scoring_criteria": {
                "score_5": "Situação complexa + comportamento exemplar + impacto positivo mensurável",
                "score_3": "Situação clara + comportamento adequado + resultado satisfatório",
                "score_1": "Situação vaga + comportamento genérico + sem resultado claro",
            },
        }
        envelope = await self._generate_question_with_envelope(
            prompt=prompt,
            fallback_data=bigfive_fallback,
            framework_label="BigFive",
            competency_name=competency.name,
            bind_kwargs={"temperature": 0.8, "max_tokens": 2000},
        )
        data = envelope.data if envelope.success else (envelope.data or bigfive_fallback)

        scoring_criteria = data.get("scoring_criteria", {})
        if ocean_trait:
            scoring_criteria["ocean_trait"] = ocean_trait

        return WSIQuestion(
            id=str(uuid.uuid4()),  # Generate UUID instead of relying on LLM
            competency=competency.name,
            framework="BigFive",
            question_type="situational",
            block="behavioral",
            question_text=data.get("question_text") or f"Compartilhe uma situação recente em que você precisou demonstrar {competency.name} em seu trabalho. Como você lidou com o desafio e qual foi o impacto?",
            weight=competency.weight,
            expected_signals=data.get("expected_signals", ["Situação", "Comportamento", "Resultado"]),
            scoring_criteria=scoring_criteria,
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )


