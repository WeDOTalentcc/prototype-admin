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

from app.domains.job_creation.schemas import (
    EnrichedJobDescription,
    TechnicalSkill,
    BehavioralCompetency,
)
from app.domains.job_creation.helpers.screening_mode_config import (
    SCREENING_MODE_CONFIG,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fairness: Bias term detection (WSI P7 — linguagem inclusiva)
# Merged from lia-hardening/fairness/fairness_guard_patch.py
# ---------------------------------------------------------------------------

BIAS_TERMS_PT = {
    # Age proxy
    "jovem e dinâmico": "proativo e engajado",
    "jovem e dinamico": "proativo e engajado",
    "energia jovem": "alta energia",
    "recém-formado apenas": "formação recente é diferencial",
    "recem-formado apenas": "formacao recente e diferencial",
    # Gender proxy
    "ele deve": "a pessoa deve",
    "ele precisa": "a pessoa precisa",
    "o candidato ideal": "a pessoa ideal",
    # Culture fit (class bias proxy)
    "fit cultural": "alinhamento com valores",
    "cultural fit": "alinhamento com valores",
    "cara da empresa": "alinhamento com a missao",
    # Appearance proxy
    "boa aparência": "",
    "boa aparencia": "",
    "boa apresentação pessoal": "",
    "boa apresentacao pessoal": "",
    # Marital/family
    "sem filhos": "",
    "disponibilidade total": "disponibilidade conforme combinado",
}

BIAS_TERMS_EN = {
    "young and dynamic": "proactive and engaged",
    "culture fit": "values alignment",
    "he should": "the person should",
    "he must": "the person must",
    "native speaker": "fluent in",
    "good looking": "",
    "attractive": "",
}

# BLOCKED filters (from fairness_guard)
BLOCKED_FILTERS = {
    "gender", "genero", "sexo", "age", "idade",
    "race", "raca", "ethnicity", "etnia",
    "marital", "estado_civil", "religion", "religiao",
}


def check_fairness(text: str) -> Tuple[str, List[str]]:
    """Apply fairness corrections to JD text.

    Returns:
        tuple of (corrected_text, list_of_corrections_applied)
    """
    corrections = []
    corrected = text

    # Check PT bias terms
    for bias_term, replacement in BIAS_TERMS_PT.items():
        pattern = re.compile(re.escape(bias_term), re.IGNORECASE)
        if pattern.search(corrected):
            if replacement:
                corrected = pattern.sub(replacement, corrected)
                corrections.append(f"Substituido '{bias_term}' por '{replacement}' (linguagem inclusiva)")
            else:
                corrected = pattern.sub("", corrected)
                corrections.append(f"Removido '{bias_term}' (termo potencialmente discriminatorio)")

    # Check EN bias terms
    for bias_term, replacement in BIAS_TERMS_EN.items():
        pattern = re.compile(re.escape(bias_term), re.IGNORECASE)
        if pattern.search(corrected):
            if replacement:
                corrected = pattern.sub(replacement, corrected)
                corrections.append(f"Replaced '{bias_term}' with '{replacement}' (inclusive language)")
            else:
                corrected = pattern.sub("", corrected)
                corrections.append(f"Removed '{bias_term}' (potentially discriminatory term)")

    return corrected.strip(), corrections

# WSI F1.B minimum thresholds
MIN_TECHNICAL_SKILLS = 9
MIN_BEHAVIORAL_COMPETENCIES = 5
MIN_RESPONSIBILITIES = 5


def _build_enrichment_prompt(
    jd_raw: str,
    title: str = "",
    seniority: str = "",
    department: str = "",
    confirmed_technical: list | None = None,
    confirmed_behavioral: list | None = None,
    confirmed_responsibilities: list | None = None,
    company_context: str = "",
) -> str:
    """Build the F1.C enrichment prompt from WSI methodology.

    Fase 4 (inversao): quando confirmed_technical/confirmed_behavioral sao
    fornecidas (competencias confirmadas pelo recrutador na Fase 3), o prompt
    instrui o LLM a gerar um JD CONSISTENTE com elas, sem inventar/substituir
    competencias. O servico ainda sobrescreve as listas confirmadas apos o
    parse (garantia computacional contra drift do LLM).
    """
    _has_confirmed = bool(confirmed_technical or confirmed_behavioral)
    if _has_confirmed:
        _tech_lines = "\n".join(
            f"  - {t.get('skill', '')}: {t.get('contexto', '')}"
            for t in (confirmed_technical or [])
        ) or "  (nenhuma)"
        _behav_lines = "\n".join(
            f"  - {b.get('competencia', '')} [{b.get('trait_big_five', 'conscientiousness')}]: {b.get('contexto', '')}"
            for b in (confirmed_behavioral or [])
        ) or "  (nenhuma)"
        _rule2 = "2. NAO invente nem altere competencias — use EXATAMENTE as confirmadas abaixo"
        _rule5 = "5. As contagens sao definidas pelas competencias confirmadas (nao force minimos)"
        _confirmed_block = (
            "\n\nCOMPETENCIAS JA CONFIRMADAS PELO RECRUTADOR (FIXAS — NAO ALTERE, NAO ADICIONE, NAO REMOVA):\n"
            "Tecnicas:\n" + _tech_lines + "\n"
            "Comportamentais:\n" + _behav_lines + "\n\n"
            "Gere about_role, responsabilidades, skills_desejaveis e context_signals "
            "CONSISTENTES com essas competencias. Em skills_obrigatorias e "
            "competencias_comportamentais, retorne EXATAMENTE as competencias confirmadas acima.\n"
        )
    else:
        _rule2 = "2. Adicione skills e competencias que estao implicitas no JD"
        _rule5 = f"5. Minimos: {MIN_TECHNICAL_SKILLS} skills tecnicas, {MIN_BEHAVIORAL_COMPETENCIES} competencias comportamentais, {MIN_RESPONSIBILITIES} responsabilidades"
        _confirmed_block = ""

    # Responsabilidades confirmadas pelo recrutador (independente das competencias):
    # usar EXATAMENTE estas. O servico tambem sobrescreve apos o parse (garantia).
    if confirmed_responsibilities:
        _resp_lines = "\n".join(
            f"  - {r}" for r in _coerce_responsibilities(confirmed_responsibilities)
        ) or "  (nenhuma)"
        _confirmed_block += (
            "\n\nRESPONSABILIDADES JA DEFINIDAS PELO RECRUTADOR "
            "(FIXAS — use EXATAMENTE estas em 'responsabilidades', NAO invente outras):\n"
            + _resp_lines + "\n"
        )

    _company_block = (
        "\n\nCONTEXTO DA EMPRESA (use para a secao \"about_company\" e para ancorar o "
        "tom do JD; NUNCA invente dados que nao estejam aqui):\n" + company_context + "\n"
        if company_context else ""
    )
    return f"""Voce e um especialista em recrutamento. Analise o JD (Job Description) abaixo e produza uma versao enriquecida e estruturada.

REGRAS:
1. Mantenha o conteudo original, apenas estruture e enriqueca
{_rule2}
3. Classifique cada competencia comportamental pelo trait Big Five correspondente (openness, conscientiousness, extraversion, agreeableness, stability)
4. Aplique linguagem inclusiva — corrija termos excludentes
{_rule5}
6. Se o JD for muito curto, enriqueca com base no titulo e senioridade
{_confirmed_block}
{_company_block}
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
  "about_company": "2-3 frases sobre a empresa, baseado SOMENTE no CONTEXTO DA EMPRESA fornecido; string vazia se nenhum contexto foi dado",
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


def calculate_quality_score(
    enriched: EnrichedJobDescription,
    min_technical: int = MIN_TECHNICAL_SKILLS,
    min_behavioral: int = MIN_BEHAVIORAL_COMPETENCIES,
) -> tuple[float, list[str]]:
    """F1.B — quality score (0-100) DELEGADO ao canônico 9-dim (Fase 3.3).

    Consolidação WSI: delega a
    ``cv_screening.services.wsi_service.jd_quality.evaluate_jd_quality`` —
    single source de qualidade de JD (mesma função do endpoint /jd-evaluate e
    do wizard). Mode-aware via ``d3_min``/``d4_min`` (passa os thresholds do
    modo resolvidos pelo caller; NÃO penaliza modo compact). Mapeia
    EnrichedJobDescription -> inputs do canônico; warnings derivados dos
    indicadores insufficient/partial.

    NOTA: o número agora segue a metodologia 9-dim (D1-D9), substituindo o
    score de completude legado (tech/behav/resp/about/context/fairness). É a
    consistência desejada (mesmo número do /jd-evaluate de Settings).
    """
    from app.domains.cv_screening.services.wsi_service.jd_quality import (
        evaluate_jd_quality,
    )

    r = evaluate_jd_quality(
        description=enriched.about_role,
        job_title=enriched.titulo_padronizado,
        seniority=enriched.senioridade_confirmada,
        responsibilities=list(enriched.responsabilidades or []),
        technical_skills=[s.skill for s in (enriched.skills_obrigatorias or [])],
        behavioral_competencies=[
            c.competencia for c in (enriched.competencias_comportamentais or [])
        ],
        d3_min=min_technical,
        d4_min=min_behavioral,
    )
    warnings = [
        ind["detail"]
        for ind in r["indicators"]
        if ind.get("status") in ("insufficient", "partial")
    ]
    return float(r["score"]), warnings


def _coerce_technical(items: list | None) -> list:
    """Converte dicts {skill, contexto} confirmados em TechnicalSkill."""
    out = []
    for t in items or []:
        out.append(TechnicalSkill(
            skill=t.get("skill", ""),
            contexto=t.get("contexto", ""),
        ))
    return out


def _coerce_behavioral(items: list | None) -> list:
    """Converte dicts {competencia, contexto, trait_big_five} em BehavioralCompetency."""
    out = []
    for b in items or []:
        trait = b.get("trait_big_five") or "conscientiousness"
        try:
            out.append(BehavioralCompetency(
                competencia=b.get("competencia", ""),
                contexto=b.get("contexto", ""),
                trait_big_five=trait,
            ))
        except Exception:  # noqa: BLE001 -- trait invalido -> default
            out.append(BehavioralCompetency(
                competencia=b.get("competencia", ""),
                contexto=b.get("contexto", ""),
            ))
    return out


def _coerce_responsibilities(items: list | None) -> list:
    """Converte responsabilidades confirmadas (strings ou dicts) em list[str]."""
    out: list[str] = []
    for r in items or []:
        if isinstance(r, dict):
            s = r.get("responsabilidade") or r.get("texto") or r.get("text") or r.get("value") or ""
        else:
            s = str(r or "")
        s = s.strip()
        if s:
            out.append(s[:500])
    return out


def _apply_confirmed_override(
    enriched: EnrichedJobDescription,
    confirmed_technical: list | None,
    confirmed_behavioral: list | None,
    confirmed_responsibilities: list | None = None,
) -> EnrichedJobDescription:
    """Fase 4: sobrescreve as competencias (e responsabilidades, quando
    confirmadas pelo recrutador) com as confirmadas — garantia computacional
    contra drift do LLM. Mantem o restante do JD gerado.
    """
    if confirmed_technical:
        enriched.skills_obrigatorias = _coerce_technical(confirmed_technical)
    if confirmed_behavioral:
        enriched.competencias_comportamentais = _coerce_behavioral(confirmed_behavioral)
    if confirmed_responsibilities:
        enriched.responsabilidades = _coerce_responsibilities(confirmed_responsibilities)
    return enriched


def _resolve_quality_thresholds(
    screening_mode: str | None,
    confirmed_technical: list | None,
    confirmed_behavioral: list | None,
) -> tuple[int, int]:
    """Thresholds mode-aware para o quality_score (Fase 4).

    - Sem confirmadas: thresholds legados (9/5) -- comportamento original.
    - Com confirmadas + modo conhecido: targets do modo (SCREENING_MODE_CONFIG).
    - Com confirmadas + modo desconhecido: as proprias contagens confirmadas
      (a contagem e decisao do recrutador -- nao penalizar).
    """
    has_confirmed = bool(confirmed_technical or confirmed_behavioral)
    if not has_confirmed:
        return MIN_TECHNICAL_SKILLS, MIN_BEHAVIORAL_COMPETENCIES
    if screening_mode in SCREENING_MODE_CONFIG:
        cfg = SCREENING_MODE_CONFIG[screening_mode]
        return cfg["technical_competencies"], cfg["behavioral_competencies"]
    return (
        max(1, len(confirmed_technical or [])),
        max(1, len(confirmed_behavioral or [])),
    )


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
        confirmed_technical: list | None = None,
        confirmed_behavioral: list | None = None,
        confirmed_responsibilities: list | None = None,
        screening_mode: str | None = None,
        company_context: str = "",
    ) -> tuple[EnrichedJobDescription, float, list[str]]:
        """Enrich a raw JD using LLM.

        Fase 4 (inversao): quando confirmed_technical/confirmed_behavioral sao
        fornecidas, o JD e gerado CONSISTENTE com elas e as competencias sao
        sobrescritas verbatim (garantia computacional). quality_score vira
        mode-aware (thresholds do modo, nao os fixos 9/5). Sem confirmadas,
        comportamento legado (gera competencias do zero).

        Governance layers applied:
        1. Fairness: bias detection on raw JD BEFORE LLM call
        2. Circuit breaker: wraps LLM call for resilience
        3. Audit: tracked via create_tracked_llm callbacks (automatic)
        4. Fairness: post-LLM validation on enriched output

        Returns:
            tuple of (enriched_jd, quality_score, warnings)
        """
        _min_tech, _min_behav = _resolve_quality_thresholds(
            screening_mode, confirmed_technical, confirmed_behavioral,
        )

        # --- GOV 1: Pre-LLM fairness check on raw JD ---
        jd_cleaned, pre_corrections = check_fairness(jd_raw)
        if pre_corrections:
            logger.info("[JdEnrichment:Fairness] %d pre-corrections applied", len(pre_corrections))

        prompt = _build_enrichment_prompt(
            jd_cleaned, title, seniority, department,
            confirmed_technical=confirmed_technical,
            confirmed_behavioral=confirmed_behavioral,
            confirmed_responsibilities=confirmed_responsibilities,
            company_context=company_context,
        )

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
                enriched = self._fallback_enrichment(
                    jd_raw, title, seniority,
                    confirmed_technical=confirmed_technical,
                    confirmed_behavioral=confirmed_behavioral,
                )
                enriched.wsi_quality_warnings.append("Servico de enriquecimento temporariamente indisponivel")
                quality_score, warnings = calculate_quality_score(
                    enriched, min_technical=_min_tech, min_behavioral=_min_behav,
                )
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

        # --- Fase 4: sobrescreve com competencias + responsabilidades confirmadas ---
        enriched = _apply_confirmed_override(
            enriched, confirmed_technical, confirmed_behavioral,
            confirmed_responsibilities,
        )

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

        quality_score, warnings = calculate_quality_score(
            enriched, min_technical=_min_tech, min_behavioral=_min_behav,
        )
        enriched.wsi_quality_score = quality_score
        enriched.wsi_quality_warnings = warnings

        logger.info(
            "[JdEnrichment] score=%.1f | skills=%d | behavioral=%d | confirmed=%s | fairness=%d | warnings=%d",
            quality_score,
            len(enriched.skills_obrigatorias),
            len(enriched.competencias_comportamentais),
            bool(confirmed_technical or confirmed_behavioral),
            len(all_corrections),
            len(warnings),
        )

        return enriched, quality_score, warnings

    def _fallback_enrichment(
        self,
        jd_raw: str,
        title: str,
        seniority: str,
        confirmed_technical: list | None = None,
        confirmed_behavioral: list | None = None,
        confirmed_responsibilities: list | None = None,
    ) -> EnrichedJobDescription:
        """Minimal enrichment when LLM fails.

        Fase 4: honra competencias E responsabilidades confirmadas (seta
        verbatim) para que o fallback de timeout/erro no node tambem produza
        o JD consistente.
        """
        return EnrichedJobDescription(
            titulo_padronizado=title or "Cargo nao especificado",
            senioridade_confirmada=seniority or "pleno",
            about_role=jd_raw[:200] if jd_raw else "",
            responsabilidades=_coerce_responsibilities(confirmed_responsibilities),
            skills_obrigatorias=_coerce_technical(confirmed_technical),
            competencias_comportamentais=_coerce_behavioral(confirmed_behavioral),
            wsi_quality_warnings=["Enriquecimento por LLM falhou — usando fallback minimo"],
        )
