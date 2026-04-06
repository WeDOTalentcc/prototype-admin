"""
Serviço Central de Calibração Contextual de Senioridade para o Sistema WSI.

Este módulo implementa o pipeline de calibração contextual que recebe o contexto
completo de uma vaga de emprego e produz níveis calibrados de Bloom e Dreyfus.

CARACTERÍSTICAS FUNDAMENTAIS:
- 100% DETERMINÍSTICO: Nenhuma chamada a LLM, API externa ou modelo de ML.
- NÃO CONFIGURÁVEL POR CLIENTE: Todos os perfis e ajustes são hardcoded e
  versionados no repositório. Alterações requerem deploy.
- AUDITÁVEL: Cada resultado inclui rationale completo em português e breakdown
  detalhado de todos os offsets aplicados.

PIPELINE DE 4 ETAPAS:
1. Detecção de perfil de área (keywords matching)
2. Ajuste geográfico (multiplicador de anos)
3. Fator de idade tecnológica (teto de Bloom e multiplicador de anos)
4. Validação de sinal salarial (ajuste de Dreyfus)

ENTRADAS: CalibrationContext (contexto da vaga)
SAÍDAS: CalibrationResult (níveis calibrados + rationale)

Autor: LIA Agent System
Data: 2026-02-11
Versão: 1.0
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.domains.cv_screening.services.calibration_profiles import (
    AREA_MATURITY_PROFILES,
    DEFAULT_PROFILE,
    GEOGRAPHIC_ADJUSTMENTS,
    SALARY_REFERENCE_RANGES_BRL,
    TECHNOLOGY_AGE_PROFILES,
)
from app.domains.cv_screening.services.seniority_utils import normalize_seniority

logger = logging.getLogger(__name__)

WSI_CONTEXTUAL_CALIBRATION_ENABLED = True

from app.domains.cv_screening.constants.wsi_constants import (
    SENIORITY_TO_BLOOM as BASE_SENIORITY_TO_BLOOM,
)
from app.domains.cv_screening.constants.wsi_constants import (
    SENIORITY_TO_DREYFUS as BASE_SENIORITY_TO_DREYFUS,
)

_TECH_AGE_YEARS_MULTIPLIERS = {
    "very_new": 0.8,
    "new": 0.9,
    "established": 1.0,
    "legacy": 1.0,
}


@dataclass
class CalibrationContext:
    """Entrada: contexto completo da vaga de emprego para calibração.

    Contém todos os sinais contextuais disponíveis sobre a vaga. Campos opcionais
    que não forem preenchidos simplesmente não contribuem para a calibração
    (reduzindo a confiança do resultado).

    Atributos:
        seniority: Senioridade bruta (será normalizada internamente).
        job_title: Título do cargo (ex: "Engenheiro de Dados Senior").
        department: Departamento da vaga (ex: "Engenharia", "Jurídico").
        industry: Indústria/setor (ex: "Tecnologia", "Saúde").
        country: Código do país ISO 2 (ex: "BR", "US", "UK").
        location: Cidade ou localização (ex: "São Paulo", "Remote").
        required_skills: Lista de habilidades requeridas (ex: ["Python", "Spark"]).
        salary_min: Salário mínimo em BRL.
        salary_max: Salário máximo em BRL.
        company_size: Porte da empresa (micro/small/medium/large/enterprise).
    """
    seniority: str
    job_title: str
    department: str | None = None
    industry: str | None = None
    country: str | None = None
    location: str | None = None
    required_skills: list[str] | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    company_size: str | None = None


@dataclass
class CalibrationResult:
    """Saída: resultado da calibração contextual determinística.

    Contém os níveis calibrados de Dreyfus e Bloom, referência de anos de
    experiência, e informações completas de auditoria incluindo rationale
    em português e breakdown detalhado dos offsets aplicados.

    Atributos:
        dreyfus_target: Nível Dreyfus alvo (1-5), ajustado pelo contexto.
        bloom_levels: Níveis de Bloom esperados (ex: [3, 4] ou [4, 5]).
        years_reference: Faixa de anos de experiência esperada (ex: (3.0, 5.0)).
        area_maturity: Maturidade da área ("emergent"|"growing"|"mature"|"traditional").
        area_profile_id: Identificador do perfil de área (ex: "legal", "data_science").
        confidence: Confiança da calibração (0.0-1.0) baseada em sinais utilizados.
        rationale: Justificativa legível em português para auditoria.
        calibration_offsets: Breakdown detalhado de todos os offsets aplicados.
    """
    dreyfus_target: int
    bloom_levels: list[int]
    years_reference: tuple[float, float]
    area_maturity: str
    area_profile_id: str
    confidence: float
    rationale: str
    calibration_offsets: dict[str, Any]


def _detect_area_profile(
    title: str,
    department: str | None,
    industry: str | None,
    skills: list[str] | None,
) -> tuple[dict[str, Any], str]:
    """Detecta o perfil de área profissional com base em keywords.

    Realiza matching de keywords dos AREA_MATURITY_PROFILES contra o título,
    departamento, indústria e habilidades da vaga. Seleciona o perfil com
    maior número de matches (mínimo 2 matches necessários).

    Args:
        title: Título do cargo (já em minúsculas).
        department: Departamento da vaga (pode ser None).
        industry: Indústria/setor (pode ser None).
        skills: Lista de habilidades requeridas (pode ser None).

    Returns:
        Tupla (perfil_dict, profile_id). Se nenhum perfil tiver ≥ 2 matches,
        retorna (DEFAULT_PROFILE, "default").
    """
    title_lower = title.lower()
    department_lower = department.lower() if department else ""
    industry_lower = industry.lower() if industry else ""
    skills_lower = [s.lower() for s in skills] if skills else []

    search_text = f"{title_lower} {department_lower} {industry_lower} {' '.join(skills_lower)}"

    best_profile_id = "default"
    best_profile = DEFAULT_PROFILE
    best_count = 0

    for profile_id, profile in AREA_MATURITY_PROFILES.items():
        match_count = 0
        for keyword in profile["keywords"]:
            keyword_lower = keyword.lower()
            if keyword_lower in search_text:
                match_count += 1

        if match_count > best_count:
            best_count = match_count
            best_profile_id = profile_id
            best_profile = profile

    if best_count < 2:
        logger.info(
            f"Nenhum perfil de área atingiu mínimo de 2 matches "
            f"(melhor: {best_profile_id} com {best_count}). Usando DEFAULT_PROFILE."
        )
        return DEFAULT_PROFILE, "default"

    logger.info(
        f"Perfil de área detectado: {best_profile_id} "
        f"(maturity={best_profile['maturity']}, matches={best_count})"
    )
    return best_profile, best_profile_id


def _get_geographic_multiplier(
    country: str | None,
    location: str | None,
) -> float:
    """Obtém o multiplicador geográfico de progressão de carreira.

    Verifica o país e a localização contra GEOGRAPHIC_ADJUSTMENTS para determinar
    a velocidade de progressão de carreira no mercado de trabalho local.

    Args:
        country: Código ISO 2 do país (ex: "BR", "US").
        location: Cidade ou localização (ex: "São Paulo", "Remote").

    Returns:
        Multiplicador de anos (float). Padrão 1.0 se nenhum ajuste encontrado.
        Valores < 1.0 indicam progressão mais rápida.
        Valores > 1.0 indicam progressão mais lenta.
    """
    country_upper = country.strip().upper() if country else ""
    location_lower = location.strip().lower() if location else ""

    for _adjustment_id, adjustment in GEOGRAPHIC_ADJUSTMENTS.items():
        if country_upper in adjustment["countries"]:
            logger.debug(
                f"Ajuste geográfico por país: {country_upper} -> "
                f"multiplier={adjustment['years_multiplier']}"
            )
            return adjustment["years_multiplier"]

        if location_lower and location_lower in adjustment["cities"]:
            logger.debug(
                f"Ajuste geográfico por cidade: {location_lower} -> "
                f"multiplier={adjustment['years_multiplier']}"
            )
            return adjustment["years_multiplier"]

    logger.debug(
        f"Nenhum ajuste geográfico encontrado para country={country_upper}, "
        f"location={location_lower}. Usando multiplier=1.0"
    )
    return 1.0


def _calculate_tech_age_factor(
    skills: list[str] | None,
) -> dict[str, Any]:
    """Calcula o fator de idade tecnológica com base nas habilidades requeridas.

    Realiza matching das habilidades contra TECHNOLOGY_AGE_PROFILES e determina
    a categoria dominante (com mais matches). Retorna o teto de Bloom e o
    multiplicador de anos correspondente.

    Args:
        skills: Lista de habilidades requeridas (pode ser None).

    Returns:
        Dicionário com:
        - bloom_ceiling (int): Teto máximo para níveis de Bloom.
        - years_multiplier (float): Multiplicador de anos de experiência.
        - dominant_category (str): Categoria dominante identificada.
        - match_counts (dict): Contagem de matches por categoria.
    """
    if not skills:
        logger.debug("Nenhuma habilidade fornecida para cálculo de tech age factor.")
        return {
            "bloom_ceiling": 6,
            "years_multiplier": 1.0,
            "dominant_category": "none",
            "match_counts": {},
        }

    skills_lower = [s.lower() for s in skills]
    match_counts: dict[str, int] = {}

    for category, profile in TECHNOLOGY_AGE_PROFILES.items():
        count = 0
        for skill in profile["skills"]:
            if skill.lower() in skills_lower:
                count += 1
        if count > 0:
            match_counts[category] = count

    if not match_counts:
        logger.debug("Nenhuma habilidade correspondeu a perfis de tech age.")
        return {
            "bloom_ceiling": 6,
            "years_multiplier": 1.0,
            "dominant_category": "none",
            "match_counts": {},
        }

    dominant_category = max(match_counts, key=lambda k: match_counts[k])
    bloom_ceiling = TECHNOLOGY_AGE_PROFILES[dominant_category]["bloom_ceiling"]
    years_multiplier = _TECH_AGE_YEARS_MULTIPLIERS[dominant_category]

    logger.info(
        f"Tech age factor: categoria dominante={dominant_category}, "
        f"bloom_ceiling={bloom_ceiling}, years_multiplier={years_multiplier}, "
        f"matches={match_counts}"
    )

    return {
        "bloom_ceiling": bloom_ceiling,
        "years_multiplier": years_multiplier,
        "dominant_category": dominant_category,
        "match_counts": match_counts,
    }


def _validate_salary_signal(
    seniority: str,
    salary_min: float | None,
    salary_max: float | None,
) -> dict[str, Any]:
    """Valida o sinal salarial contra os ranges de referência do mercado.

    Compara o ponto médio salarial da vaga com os ranges de referência em
    SALARY_REFERENCE_RANGES_BRL para detectar inconsistências que sugiram
    que a senioridade real é diferente da declarada.

    Args:
        seniority: Senioridade normalizada (ex: "junior", "senior").
        salary_min: Salário mínimo em BRL (pode ser None).
        salary_max: Salário máximo em BRL (pode ser None).

    Returns:
        Dicionário com:
        - dreyfus_adj (int): Ajuste de Dreyfus (-1, 0 ou +1).
        - reason (str): Razão do ajuste em português.
        - salary_midpoint (float|None): Ponto médio salarial calculado.
    """
    if salary_min is None and salary_max is None:
        logger.debug("Nenhum dado salarial fornecido para validação.")
        return {
            "dreyfus_adj": 0,
            "reason": "Sem dados salariais disponíveis",
            "salary_midpoint": None,
        }

    if salary_min is not None and salary_max is not None:
        midpoint = (salary_min + salary_max) / 2.0
    elif salary_min is not None:
        midpoint = salary_min
    else:
        midpoint = salary_max

    ref_range = SALARY_REFERENCE_RANGES_BRL.get(seniority)
    if not ref_range:
        logger.warning(
            f"Senioridade '{seniority}' não encontrada em SALARY_REFERENCE_RANGES_BRL."
        )
        return {
            "dreyfus_adj": 0,
            "reason": f"Senioridade '{seniority}' sem range de referência salarial",
            "salary_midpoint": midpoint,
        }

    ref_min, ref_max = ref_range

    if midpoint > 1.5 * ref_max:
        logger.info(
            f"Sinal salarial: midpoint R${midpoint:.0f} > 1.5×ref_max R${ref_max:.0f}. "
            f"Dreyfus +1 (salário sugere senioridade maior)."
        )
        return {
            "dreyfus_adj": 1,
            "reason": (
                f"Salário médio (R${midpoint:.0f}) significativamente acima do "
                f"range de referência para {seniority} (R${ref_min}-R${ref_max}). "
                f"Sugere senioridade efetiva superior."
            ),
            "salary_midpoint": midpoint,
        }

    if midpoint < 0.5 * ref_min:
        logger.info(
            f"Sinal salarial: midpoint R${midpoint:.0f} < 0.5×ref_min R${ref_min:.0f}. "
            f"Dreyfus -1 (salário sugere senioridade menor)."
        )
        return {
            "dreyfus_adj": -1,
            "reason": (
                f"Salário médio (R${midpoint:.0f}) significativamente abaixo do "
                f"range de referência para {seniority} (R${ref_min}-R${ref_max}). "
                f"Sugere senioridade efetiva inferior."
            ),
            "salary_midpoint": midpoint,
        }

    logger.debug(
        f"Sinal salarial dentro do esperado: midpoint R${midpoint:.0f} "
        f"dentro de R${ref_min}-R${ref_max} para {seniority}."
    )
    return {
        "dreyfus_adj": 0,
        "reason": (
            f"Salário médio (R${midpoint:.0f}) compatível com range de "
            f"referência para {seniority} (R${ref_min}-R${ref_max})."
        ),
        "salary_midpoint": midpoint,
    }


def calibrate(context: CalibrationContext) -> CalibrationResult:
    """Executa o pipeline completo de calibração contextual de senioridade.

    Pipeline determinístico de 4 etapas que ajusta os níveis base de Bloom e
    Dreyfus com base no contexto completo da vaga. Cada etapa contribui com
    offsets e multiplicadores que são combinados no resultado final.

    Args:
        context: CalibrationContext com todos os sinais contextuais da vaga.

    Returns:
        CalibrationResult com níveis calibrados, referência de anos,
        confiança e rationale completo para auditoria.

    Exemplo:
        >>> ctx = CalibrationContext(
        ...     seniority="Senior",
        ...     job_title="Engenheiro de Dados Senior",
        ...     department="Engenharia",
        ...     required_skills=["Python", "Spark"],
        ...     country="BR"
        ... )
        >>> result = calibrate(ctx)
        >>> result.dreyfus_target
        4
    """
    logger.info(
        f"Iniciando calibração contextual para vaga: "
        f"title='{context.job_title}', seniority_raw='{context.seniority}'"
    )

    seniority = normalize_seniority(context.seniority)
    logger.info(f"Senioridade normalizada: '{context.seniority}' -> '{seniority}'")

    signals_used = 0
    rationale_parts: list[str] = []

    rationale_parts.append(
        f"Senioridade normalizada: '{context.seniority}' → '{seniority}'"
    )

    # ========================================================================
    # ETAPA 1: Detecção de perfil de área
    # ========================================================================
    area_profile, area_profile_id = _detect_area_profile(
        title=context.job_title,
        department=context.department,
        industry=context.industry,
        skills=context.required_skills,
    )
    if area_profile_id != "default":
        signals_used += 1
    rationale_parts.append(
        f"Perfil de área: {area_profile_id} "
        f"(maturidade={area_profile['maturity']}, "
        f"bloom_offset={area_profile['bloom_offset']}, "
        f"dreyfus_offset={area_profile['dreyfus_offset']})"
    )

    # ========================================================================
    # ETAPA 2: Ajuste geográfico
    # ========================================================================
    geo_multiplier = _get_geographic_multiplier(
        country=context.country,
        location=context.location,
    )
    if geo_multiplier != 1.0:
        signals_used += 1
    rationale_parts.append(
        f"Multiplicador geográfico: {geo_multiplier} "
        f"(país={context.country or 'N/A'}, local={context.location or 'N/A'})"
    )

    # ========================================================================
    # ETAPA 3: Fator de idade tecnológica
    # ========================================================================
    tech_factor = _calculate_tech_age_factor(skills=context.required_skills)
    if tech_factor["dominant_category"] != "none":
        signals_used += 1
    rationale_parts.append(
        f"Tech age: categoria={tech_factor['dominant_category']}, "
        f"bloom_ceiling={tech_factor['bloom_ceiling']}, "
        f"years_multiplier={tech_factor['years_multiplier']}"
    )

    # ========================================================================
    # ETAPA 4: Validação de sinal salarial
    # ========================================================================
    salary_signal = _validate_salary_signal(
        seniority=seniority,
        salary_min=context.salary_min,
        salary_max=context.salary_max,
    )
    if salary_signal["dreyfus_adj"] != 0:
        signals_used += 1
    rationale_parts.append(f"Sinal salarial: {salary_signal['reason']}")

    # ========================================================================
    # CÁLCULO FINAL
    # ========================================================================
    base_dreyfus = BASE_SENIORITY_TO_DREYFUS.get(seniority, 3)
    base_bloom = list(BASE_SENIORITY_TO_BLOOM.get(seniority, [3, 4]))

    dreyfus_target = base_dreyfus + area_profile["dreyfus_offset"] + salary_signal["dreyfus_adj"]
    dreyfus_target = max(1, min(5, dreyfus_target))

    bloom_offset = area_profile["bloom_offset"]
    adjusted_bloom = [level + bloom_offset for level in base_bloom]

    bloom_ceiling = tech_factor["bloom_ceiling"]
    adjusted_bloom = [min(level, bloom_ceiling) for level in adjusted_bloom]

    adjusted_bloom = [max(1, min(6, level)) for level in adjusted_bloom]

    adjusted_bloom = sorted(set(adjusted_bloom))

    seniority_years = area_profile["seniority_years"].get(seniority, (2, 5))
    years_min = round(seniority_years[0] * geo_multiplier * tech_factor["years_multiplier"], 1)
    years_max = round(seniority_years[1] * geo_multiplier * tech_factor["years_multiplier"], 1)
    years_reference = (years_min, years_max)

    confidence = signals_used / 4.0

    rationale_parts.append(
        f"Resultado final: Dreyfus={dreyfus_target} (base={base_dreyfus}, "
        f"area_offset={area_profile['dreyfus_offset']}, "
        f"salary_adj={salary_signal['dreyfus_adj']}), "
        f"Bloom={adjusted_bloom} (base={base_bloom}, "
        f"bloom_offset={bloom_offset}, ceiling={bloom_ceiling}), "
        f"Anos={years_reference}, Confiança={confidence:.2f}"
    )

    rationale = " | ".join(rationale_parts)

    calibration_offsets = {
        "base_dreyfus": base_dreyfus,
        "base_bloom": BASE_SENIORITY_TO_BLOOM.get(seniority, [3, 4]),
        "area_profile_id": area_profile_id,
        "area_bloom_offset": area_profile["bloom_offset"],
        "area_dreyfus_offset": area_profile["dreyfus_offset"],
        "geo_multiplier": geo_multiplier,
        "tech_age_category": tech_factor["dominant_category"],
        "tech_age_bloom_ceiling": tech_factor["bloom_ceiling"],
        "tech_age_years_multiplier": tech_factor["years_multiplier"],
        "tech_age_match_counts": tech_factor["match_counts"],
        "salary_dreyfus_adj": salary_signal["dreyfus_adj"],
        "salary_midpoint": salary_signal["salary_midpoint"],
        "salary_reason": salary_signal["reason"],
        "signals_used": signals_used,
        "seniority_normalized": seniority,
    }

    result = CalibrationResult(
        dreyfus_target=dreyfus_target,
        bloom_levels=adjusted_bloom,
        years_reference=years_reference,
        area_maturity=area_profile["maturity"],
        area_profile_id=area_profile_id,
        confidence=confidence,
        rationale=rationale,
        calibration_offsets=calibration_offsets,
    )

    logger.info(
        f"Calibração concluída: dreyfus={result.dreyfus_target}, "
        f"bloom={result.bloom_levels}, years={result.years_reference}, "
        f"confidence={result.confidence:.2f}, profile={result.area_profile_id}"
    )

    return result


def calibrate_or_fallback(context: CalibrationContext) -> CalibrationResult:
    """Executa calibração com fallback seguro para mapeamentos base.

    Wrapper de segurança que encapsula calibrate() em try/except. Em caso de
    qualquer falha, retorna um resultado usando os mapeamentos base (comportamento
    legado) garantindo que o sistema nunca falhe por erro de calibração.

    Args:
        context: CalibrationContext com os sinais contextuais da vaga.

    Returns:
        CalibrationResult calibrado ou resultado fallback com mapeamentos base.
    """
    try:
        return calibrate(context)
    except Exception as e:
        seniority = normalize_seniority(context.seniority)

        logger.warning(
            f"Erro na calibração contextual, usando fallback para "
            f"seniority='{seniority}': {e}",
            exc_info=True,
        )

        base_dreyfus = BASE_SENIORITY_TO_DREYFUS.get(seniority, 3)
        base_bloom = list(BASE_SENIORITY_TO_BLOOM.get(seniority, [3, 4]))
        default_years = DEFAULT_PROFILE["seniority_years"].get(seniority, (2, 5))

        return CalibrationResult(
            dreyfus_target=base_dreyfus,
            bloom_levels=base_bloom,
            years_reference=(float(default_years[0]), float(default_years[1])),
            area_maturity="mature",
            area_profile_id="default",
            confidence=0.0,
            rationale=(
                f"FALLBACK: Calibração contextual falhou ({type(e).__name__}: {e}). "
                f"Usando mapeamentos base para senioridade '{seniority}'."
            ),
            calibration_offsets={
                "fallback": True,
                "error": str(e),
                "seniority_normalized": seniority,
            },
        )
