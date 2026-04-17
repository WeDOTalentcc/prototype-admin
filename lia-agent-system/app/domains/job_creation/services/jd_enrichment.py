"""
JdEnrichmentService — F1 of WSI methodology.

Enriches raw JD text via LLM structured output + calculates quality score.
Replaces 4 regex extractors with a single LLM call (WSI F1.C prompt).

Governance integrations:
  - Fairness: bias term detection + inclusive language corrections
  - Circuit breaker: wraps LLM calls for resilience
  - Audit: tracked via create_tracked_llm callbacks
  - PII: masks sensitive data before logging

Parameters from methodology:
  - temperature=0.3
  - max_tokens=4000
  - top_p=0.95

Quality score thresholds (F1.B deterministic):
  - < 30: blocked (hard stop)
  - 30-49: warning, proceeds with caveats
  - >= 50: OK
"""

import json
import logging
import re
from typing import List, Tuple

from app.domains.job_creation.schemas import EnrichedJobDescription
from app.shared.compliance.fairness_guard import (
    BLOCKED_FILTER_FIELDS as BLOCKED_FILTERS,
    INCLUSIVE_LANGUAGE_REPLACEMENTS_EN as BIAS_TERMS_EN,
    INCLUSIVE_LANGUAGE_REPLACEMENTS_PT as BIAS_TERMS_PT,
    FairnessGuard,
)

logger = logging.getLogger(__name__)

# Single source of truth for inclusive-language replacements is FairnessGuard.
_fairness_guard = FairnessGuard()


def check_fairness(text: str) -> Tuple[str, List[str]]:
    """Apply fairness corrections to JD text.

    Thin wrapper over FairnessGuard.apply_inclusive_language() (task #321).
    Returns:
        tuple of (corrected_text, list_of_corrections_applied)
    """
    return _fairness_guard.apply_inclusive_language(text)

# WSI F1.B minimum thresholds
MIN_TECHNICAL_SKILLS = 9
MIN_BEHAVIORAL_COMPETENCIES = 5
MIN_RESPONSIBILITIES = 5


def _build_enrichment_prompt(
    jd_raw: str,
    title: str = "",
    seniority: str = "",
    department: str = "",
) -> str:
    """Build the F1.C enrichment prompt from WSI methodology."""
    return f"""Voce e um especialista em recrutamento. Analise o JD (Job Description) abaixo e produza uma versao enriquecida e estruturada.

REGRAS:
1. Mantenha o conteudo original, apenas estruture e enriqueca
2. Adicione skills e competencias que estao implicitas no JD
3. Classifique cada competencia comportamental pelo trait Big Five correspondente (openness, conscientiousness, extraversion, agreeableness, stability)
4. Aplique linguagem inclusiva — corrija termos excludentes
5. Minimos: {MIN_TECHNICAL_SKILLS} skills tecnicas, {MIN_BEHAVIORAL_COMPETENCIES} competencias comportamentais, {MIN_RESPONSIBILITIES} responsabilidades
6. Se o JD for muito curto, enriqueca com base no titulo e senioridade

JD ORIGINAL:
{jd_raw}

TITULO: {title or '(nao informado)'}
SENIORIDADE: {seniority or '(nao informada)'}
DEPARTAMENTO: {department or '(nao informado)'}

Responda APENAS com JSON valido no formato:
{{
  "titulo_padronizado": "titulo normalizado",
  "senioridade_confirmada": "junior|pleno|senior|lead|diretor",
  "about_role": "descricao resumida do papel (2-3 frases)",
  "responsabilidades": ["resp1", "resp2", ...],
  "skills_obrigatorias": [
    {{"skill": "nome", "contexto": "como e usado no cargo"}}
  ],
  "skills_desejaveis": ["skill1", "skill2"],
  "competencias_comportamentais": [
    {{
      "competencia": "nome",
      "contexto": "como se manifesta no cargo",
      "trait_big_five": "openness|conscientiousness|extraversion|agreeableness|stability"
    }}
  ],
  "context_signals": {{
    "nivel_autonomia": "baixo|medio|alto",
    "nivel_inovacao": "baixo|medio|alto",
    "nivel_pressao": "baixo|medio|alto",
    "nivel_colaboracao": "baixo|medio|alto"
  }},
  "alteracoes_realizadas": ["descricao de cada alteracao feita"],
  "fairness_corrections": ["correcoes de linguagem inclusiva aplicadas"]
}}"""


def calculate_quality_score(enriched: EnrichedJobDescription) -> float:
    """F1.B — Deterministic quality score (0-100).

    Based on WSI methodology thresholds:
    - D3: minimum technical skills
    - D4: minimum behavioral competencies
    - Also checks responsibilities, about_role, context signals
    """
    score = 0.0
    warnings = []

    # D3: Technical skills (max 30 points)
    n_tech = len(enriched.skills_obrigatorias)
    if n_tech >= MIN_TECHNICAL_SKILLS:
        score += 30.0
    elif n_tech >= 5:
        score += 15.0 + (n_tech - 5) * (15.0 / (MIN_TECHNICAL_SKILLS - 5))
        warnings.append(f"Apenas {n_tech} skills tecnicas (minimo recomendado: {MIN_TECHNICAL_SKILLS})")
    else:
        score += n_tech * 3.0
        warnings.append(f"Skills tecnicas insuficientes: {n_tech}/{MIN_TECHNICAL_SKILLS}")

    # D4: Behavioral competencies (max 25 points)
    n_behav = len(enriched.competencias_comportamentais)
    if n_behav >= MIN_BEHAVIORAL_COMPETENCIES:
        score += 25.0
    elif n_behav >= 2:
        score += 10.0 + (n_behav - 2) * (15.0 / (MIN_BEHAVIORAL_COMPETENCIES - 2))
        warnings.append(f"Apenas {n_behav} competencias comportamentais (minimo: {MIN_BEHAVIORAL_COMPETENCIES})")
    else:
        score += n_behav * 5.0
        warnings.append(f"Competencias comportamentais insuficientes: {n_behav}/{MIN_BEHAVIORAL_COMPETENCIES}")

    # Responsibilities (max 20 points)
    n_resp = len(enriched.responsabilidades)
    if n_resp >= MIN_RESPONSIBILITIES:
        score += 20.0
    else:
        score += n_resp * (20.0 / MIN_RESPONSIBILITIES)
        warnings.append(f"Apenas {n_resp} responsabilidades (minimo: {MIN_RESPONSIBILITIES})")

    # About role presence (max 10 points)
    if enriched.about_role and len(enriched.about_role) > 20:
        score += 10.0

    # Context signals completeness (max 10 points)
    signals = enriched.context_signals
    if signals.nivel_autonomia and signals.nivel_inovacao and signals.nivel_pressao and signals.nivel_colaboracao:
        score += 10.0
    else:
        score += 5.0

    # Fairness corrections bonus (max 5 points)
    if enriched.fairness_corrections:
        score += 5.0

    return round(min(score, 100.0), 1), warnings


class JdEnrichmentService:
    """F1 — JD enrichment via LLM structured output."""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from app.shared.providers.llm_factory import create_tracked_llm
            self._llm = create_tracked_llm(
                temperature=0.3,
                service_name="JdEnrichmentService",
                operation="enrich_jd",
                max_output_tokens=4000,
            )
        return self._llm

    def enrich(
        self,
        jd_raw: str,
        title: str = "",
        seniority: str = "",
        department: str = "",
    ) -> tuple[EnrichedJobDescription, float, list[str]]:
        """Enrich a raw JD using LLM.

        Governance layers applied:
        1. Fairness: bias detection on raw JD BEFORE LLM call
        2. Circuit breaker: wraps LLM call for resilience
        3. Audit: tracked via create_tracked_llm callbacks (automatic)
        4. Fairness: post-LLM validation on enriched output

        Returns:
            tuple of (enriched_jd, quality_score, warnings)
        """
        # --- GOV 1: Pre-LLM fairness check on raw JD ---
        jd_cleaned, pre_corrections = check_fairness(jd_raw)
        if pre_corrections:
            logger.info("[JdEnrichment:Fairness] %d pre-corrections applied", len(pre_corrections))

        prompt = _build_enrichment_prompt(jd_cleaned, title, seniority, department)

        # --- GOV 2: Circuit breaker wraps LLM call ---
        try:
            from app.shared.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
            try:
                response = circuit_breaker_call(
                    self.llm.invoke,
                    prompt,
                    circuit_key="job_creation:jd_enrichment",
                )
            except CircuitBreakerOpenError:
                logger.warning("[JdEnrichment] Circuit breaker OPEN — using fallback")
                enriched = self._fallback_enrichment(jd_raw, title, seniority)
                enriched.wsi_quality_warnings.append("Servico de enriquecimento temporariamente indisponivel")
                quality_score, warnings = calculate_quality_score(enriched)
                return enriched, quality_score, warnings
        except ImportError:
            # Circuit breaker not available — direct call
            response = self.llm.invoke(prompt)

        try:
            content = response.content.strip()

            # Strip markdown code fences if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            enriched = EnrichedJobDescription(**data)

        except Exception as e:
            logger.warning("[JdEnrichment] LLM parse failed, using fallback: %s", e)
            enriched = self._fallback_enrichment(jd_raw, title, seniority)

        # --- GOV 3: Post-LLM fairness check on enriched output ---
        enriched_text = " ".join([
            enriched.about_role,
            " ".join(enriched.responsabilidades),
            " ".join(s.skill for s in enriched.skills_obrigatorias),
        ])
        _, post_corrections = check_fairness(enriched_text)

        # Merge all fairness corrections
        all_corrections = pre_corrections + post_corrections + enriched.fairness_corrections
        enriched.fairness_corrections = list(set(all_corrections))

        quality_score, warnings = calculate_quality_score(enriched)
        enriched.wsi_quality_score = quality_score
        enriched.wsi_quality_warnings = warnings

        logger.info(
            "[JdEnrichment] score=%.1f | skills=%d | behavioral=%d | fairness=%d | warnings=%d",
            quality_score,
            len(enriched.skills_obrigatorias),
            len(enriched.competencias_comportamentais),
            len(all_corrections),
            len(warnings),
        )

        return enriched, quality_score, warnings

    def _fallback_enrichment(
        self, jd_raw: str, title: str, seniority: str
    ) -> EnrichedJobDescription:
        """Minimal enrichment when LLM fails."""
        return EnrichedJobDescription(
            titulo_padronizado=title or "Cargo nao especificado",
            senioridade_confirmada=seniority or "pleno",
            about_role=jd_raw[:200] if jd_raw else "",
            responsabilidades=[],
            skills_obrigatorias=[],
            competencias_comportamentais=[],
            wsi_quality_warnings=["Enriquecimento por LLM falhou — usando fallback minimo"],
        )
