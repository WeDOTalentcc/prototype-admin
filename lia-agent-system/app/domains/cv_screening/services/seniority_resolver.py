"""
Sistema de Resolução Multi-Sinal de Senioridade para o WSI.

Este módulo implementa o motor central de resolução de senioridade que coleta
sinais de múltiplas fontes, combina-os de forma determinística (sem LLM),
detecta conflitos entre sinais e retorna uma resolução estruturada com
metadados de auditoria completos.

SINAIS COLETADOS:
1. Entrada explícita do recrutador (peso 0.50)
2. Inferência por palavras-chave do título (peso 0.25)
3. Análise de JD - Job Description (peso 0.25)
4. Faixa salarial (peso 0.15)
5. Complexidade de skills técnicas (peso 0.10)

MOTOR DE COMBINAÇÃO (100% determinístico):
- Regra 1: Todos concordam → confiança 1.0, acordo "full"
- Regra 2: Maioria concorda (2+) → confiança 0.85, acordo "majority"
- Regra 3: Conflito entre explícito e inferido → confiança 0.40, acordo "conflict"
- Regra 4: Sinal único → confiança 0.50-0.70, acordo "single"
- Regra 5: Sem sinais → "pleno" com confiança 0.0, acordo "none"

Autor: LIA Agent System
Data: 2026-02-11
Versão: 1.0
"""

import asyncio
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any


from app.domains.cv_screening.services.calibration_profiles import SALARY_REFERENCE_RANGES_BRL
from app.domains.cv_screening.services.seniority_utils import (
    infer_seniority_from_title,
    is_valid_seniority_level,
    normalize_seniority,
)

logger = logging.getLogger(__name__)

SENIORITY_RESOLVER_ENABLED = True

SIGNAL_WEIGHTS = {
    "explicit": 0.50,
    "title_keywords": 0.25,
    "jd_analysis": 0.25,
    "salary_range": 0.15,
    "skills_complexity": 0.10,
}

SENIOR_SKILL_INDICATORS = [
    "kubernetes",
    "system design",
    "arquitetura",
    "microserviços",
    "machine learning",
    "deep learning",
    "terraform",
    "aws architect",
    "distributed systems",
]

JUNIOR_SKILL_INDICATORS = [
    "html básico",
    "excel",
    "word",
    "digitação",
]

SENIORITY_DISPLAY_NAMES = {
    "junior": "Júnior",
    "pleno": "Pleno",
    "senior": "Sênior",
    "lead": "Liderança",
    "executive": "Executivo",
}


@dataclass
class SenioritySignal:
    """Representa um sinal individual de senioridade coletado de uma fonte específica.

    Cada sinal contém a fonte de origem, o nível inferido, a confiança da
    inferência, o peso na combinação final e a evidência textual que originou
    a inferência.

    Atributos:
        source: Identificador da fonte ("explicit", "title_keywords", "jd_analysis",
                "salary_range", "skills_complexity", "company_history").
        level: Nível de senioridade inferido ("junior", "pleno", "senior", "lead",
               "executive") ou None se não foi possível inferir.
        confidence: Confiança da inferência (0.0 a 1.0).
        weight: Peso deste sinal na combinação final.
        evidence: Texto ou dados que originaram a inferência.
    """
    source: str
    level: str | None
    confidence: float
    weight: float
    evidence: str | None


@dataclass
class SeniorityResolution:
    """Resultado final da resolução multi-sinal de senioridade.

    Contém o nível resolvido, a descrição combinada das fontes, a confiança
    final, o grau de acordo entre sinais, todos os sinais coletados, avisos
    de validação, flag de confirmação e metadados de auditoria.

    Atributos:
        level: Nível final resolvido ("junior", "pleno", "senior", "lead", "executive").
        source: Descrição combinada das fontes (ex: "explicit+title+jd").
        confidence: Confiança final da resolução (0.0 a 1.0).
        agreement: Grau de acordo ("full", "majority", "conflict", "single", "none").
        signals: Lista de todos os sinais coletados.
        validation_warnings: Lista de inconsistências detectadas (em português).
        requires_confirmation: Se LIA deve perguntar ao recrutador para confirmar.
        confirmation_message: Mensagem para o recrutador (em português).
        metadata: Detalhes de auditoria.
    """
    level: str
    source: str
    confidence: float
    agreement: str
    signals: list[SenioritySignal]
    validation_warnings: list[str]
    requires_confirmation: bool
    confirmation_message: str | None
    metadata: dict[str, Any]


def _infer_seniority_from_salary(
    salary_min: float | None,
    salary_max: float | None,
) -> str | None:
    """Infere o nível de senioridade a partir da faixa salarial.

    Calcula o ponto médio salarial e determina em qual faixa de referência
    do mercado brasileiro (SALARY_REFERENCE_RANGES_BRL) ele melhor se encaixa.

    Args:
        salary_min: Salário mínimo em BRL.
        salary_max: Salário máximo em BRL.

    Returns:
        Nível de senioridade inferido ou None se não houver dados salariais.
    """
    if salary_min is None and salary_max is None:
        return None

    if salary_min is not None and salary_max is not None:
        midpoint = (salary_min + salary_max) / 2.0
    elif salary_min is not None:
        midpoint = salary_min
    else:
        midpoint = salary_max

    best_level = None
    best_distance = float("inf")

    for level, (range_min, range_max) in SALARY_REFERENCE_RANGES_BRL.items():
        range_midpoint = (range_min + range_max) / 2.0
        distance = abs(midpoint - range_midpoint)
        if distance < best_distance:
            best_distance = distance
            best_level = level

    logger.info(
        "Salary-based seniority inference: midpoint=R$%.0f -> level=%s",
        midpoint,
        best_level,
    )
    return best_level


def _infer_seniority_from_skills(
    technical_skills: list[str] | None,
) -> str | None:
    """Infere o nível de senioridade a partir da complexidade das skills técnicas.

    Realiza matching determinístico das skills fornecidas contra listas de
    indicadores de senioridade (senior+ e junior). Retorna o nível baseado
    na proporção de matches.

    Args:
        technical_skills: Lista de habilidades técnicas.

    Returns:
        "senior" se maioria das skills são de nível senior+,
        "junior" se maioria são de nível junior,
        None se inconclusivo ou sem dados.
    """
    if not technical_skills:
        return None

    skills_lower = [s.strip().lower() for s in technical_skills]

    senior_count = 0
    junior_count = 0

    for skill in skills_lower:
        for indicator in SENIOR_SKILL_INDICATORS:
            if indicator in skill:
                senior_count += 1
                break

        for indicator in JUNIOR_SKILL_INDICATORS:
            if indicator in skill:
                junior_count += 1
                break

    total_matched = senior_count + junior_count

    if total_matched == 0:
        logger.debug("No skill complexity indicators matched")
        return None

    if senior_count > junior_count:
        logger.info(
            "Skills complexity inference: senior (senior_count=%d, junior_count=%d)",
            senior_count,
            junior_count,
        )
        return "senior"

    if junior_count > senior_count:
        logger.info(
            "Skills complexity inference: junior (senior_count=%d, junior_count=%d)",
            senior_count,
            junior_count,
        )
        return "junior"

    logger.debug(
        "Skills complexity inference inconclusive (senior_count=%d, junior_count=%d)",
        senior_count,
        junior_count,
    )
    return None


def _collect_signals(
    explicit_seniority: str | None,
    job_title: str | None,
    job_description: str | None,
    salary_min: float | None,
    salary_max: float | None,
    technical_skills: list[str] | None,
) -> list[SenioritySignal]:
    """Coleta todos os sinais de senioridade disponíveis.

    Executa a coleta de sinais de todas as fontes disponíveis: entrada explícita,
    título do cargo, análise de JD, faixa salarial e complexidade de skills.

    Args:
        explicit_seniority: Senioridade informada explicitamente pelo recrutador.
        job_title: Título do cargo.
        job_description: Texto completo da descrição da vaga.
        salary_min: Salário mínimo em BRL.
        salary_max: Salário máximo em BRL.
        technical_skills: Lista de habilidades técnicas requeridas.

    Returns:
        Lista de SenioritySignal com todos os sinais coletados.
    """
    signals: list[SenioritySignal] = []

    if explicit_seniority:
        normalized = normalize_seniority(explicit_seniority)
        is_valid = is_valid_seniority_level(normalized)
        signals.append(SenioritySignal(
            source="explicit",
            level=normalized if is_valid else None,
            confidence=1.0 if is_valid else 0.3,
            weight=SIGNAL_WEIGHTS["explicit"],
            evidence=f"Recrutador informou: '{explicit_seniority}' -> normalizado: '{normalized}'",
        ))
        logger.info(
            "Signal 1 (explicit): level=%s, confidence=%.2f",
            normalized if is_valid else None,
            1.0 if is_valid else 0.3,
        )

    if job_title:
        title_level = infer_seniority_from_title(job_title)
        signals.append(SenioritySignal(
            source="title_keywords",
            level=title_level,
            confidence=0.80 if title_level else 0.0,
            weight=SIGNAL_WEIGHTS["title_keywords"],
            evidence=f"Título: '{job_title}' -> inferido: '{title_level}'",
        ))
        logger.info(
            "Signal 2 (title_keywords): level=%s, confidence=%.2f",
            title_level,
            0.80 if title_level else 0.0,
        )

    if job_description:
        try:
            from app.domains.job_management.services.seniority_jd_analyzer import analyze_jd_for_seniority
            jd_result = analyze_jd_for_seniority(job_description)
            jd_level = jd_result.get("level") if isinstance(jd_result, dict) else None
            jd_confidence = jd_result.get("confidence", 0.70) if isinstance(jd_result, dict) else 0.70
            signals.append(SenioritySignal(
                source="jd_analysis",
                level=jd_level,
                confidence=jd_confidence if jd_level else 0.0,
                weight=SIGNAL_WEIGHTS["jd_analysis"],
                evidence=f"Análise de JD: nível inferido '{jd_level}'",
            ))
            logger.info(
                "Signal 3 (jd_analysis): level=%s, confidence=%.2f",
                jd_level,
                jd_confidence if jd_level else 0.0,
            )
        except (ImportError, Exception) as e:
            logger.warning(
                "Signal 3 (jd_analysis): module not available or error: %s", str(e)
            )

    if salary_min is not None or salary_max is not None:
        salary_level = _infer_seniority_from_salary(salary_min, salary_max)
        salary_evidence_parts = []
        if salary_min is not None:
            salary_evidence_parts.append(f"min=R${salary_min:,.0f}")
        if salary_max is not None:
            salary_evidence_parts.append(f"max=R${salary_max:,.0f}")
        signals.append(SenioritySignal(
            source="salary_range",
            level=salary_level,
            confidence=0.65 if salary_level else 0.0,
            weight=SIGNAL_WEIGHTS["salary_range"],
            evidence=f"Faixa salarial ({', '.join(salary_evidence_parts)}) -> inferido: '{salary_level}'",
        ))
        logger.info(
            "Signal 4a (salary_range): level=%s, confidence=%.2f",
            salary_level,
            0.65 if salary_level else 0.0,
        )

    if technical_skills:
        skills_level = _infer_seniority_from_skills(technical_skills)
        signals.append(SenioritySignal(
            source="skills_complexity",
            level=skills_level,
            confidence=0.55 if skills_level else 0.0,
            weight=SIGNAL_WEIGHTS["skills_complexity"],
            evidence=f"Skills: {technical_skills[:5]}{'...' if len(technical_skills) > 5 else ''} -> inferido: '{skills_level}'",
        ))
        logger.info(
            "Signal 4c (skills_complexity): level=%s, confidence=%.2f",
            skills_level,
            0.55 if skills_level else 0.0,
        )

    return signals


def _redistribute_weights(signals: list[SenioritySignal]) -> None:
    """Redistribui os pesos proporcionalmente quando há menos sinais ativos.

    Sinais ativos são aqueles com level não-None. Os pesos são redistribuídos
    proporcionalmente para que a soma dos pesos ativos seja 1.0.

    Args:
        signals: Lista de sinais (modificada in-place).
    """
    active_signals = [s for s in signals if s.level is not None]
    if not active_signals:
        return

    total_weight = sum(s.weight for s in active_signals)
    if total_weight <= 0:
        return

    for signal in active_signals:
        signal.weight = signal.weight / total_weight

    logger.debug(
        "Weights redistributed for %d active signals (total_original=%.2f)",
        len(active_signals),
        total_weight,
    )


def _detect_conflicts(
    signals: list[SenioritySignal],
    explicit_seniority: str | None,
    salary_min: float | None,
    salary_max: float | None,
) -> list[str]:
    """Detecta conflitos e inconsistências entre os sinais coletados.

    Gera mensagens de aviso em português quando sinais divergem significativamente,
    especialmente quando o sinal explícito do recrutador contradiz sinais inferidos.

    Args:
        signals: Lista de sinais coletados.
        explicit_seniority: Senioridade informada pelo recrutador (valor original).
        salary_min: Salário mínimo em BRL.
        salary_max: Salário máximo em BRL.

    Returns:
        Lista de mensagens de aviso em português.
    """
    warnings: list[str] = []
    active_signals = [s for s in signals if s.level is not None]

    if len(active_signals) < 2:
        return warnings

    explicit_signal = next((s for s in active_signals if s.source == "explicit"), None)
    if not explicit_signal:
        return warnings

    explicit_level = explicit_signal.level
    explicit_display = SENIORITY_DISPLAY_NAMES.get(explicit_level or "", explicit_level or "")

    for signal in active_signals:
        if signal.source == "explicit":
            continue
        if signal.level == explicit_level:
            continue

        inferred_display = SENIORITY_DISPLAY_NAMES.get(signal.level or "", signal.level or "")

        if signal.source == "title_keywords":
            warnings.append(
                f"CONFLITO: Título indica '{inferred_display.lower()}' mas "
                f"recrutador informou '{explicit_display.lower()}'. Requer confirmação."
            )
        elif signal.source == "jd_analysis":
            warnings.append(
                f"CONFLITO: Descrição da vaga indica '{inferred_display.lower()}' mas "
                f"recrutador informou '{explicit_display.lower()}'. Requer confirmação."
            )
        elif signal.source == "salary_range":
            salary_parts = []
            if salary_min is not None:
                salary_parts.append(f"R$ {salary_min:,.0f}")
            if salary_max is not None:
                salary_parts.append(f"R$ {salary_max:,.0f}")
            salary_str = "-".join(salary_parts)
            warnings.append(
                f"INCONSISTÊNCIA: Faixa salarial ({salary_str}) sugere "
                f"'{inferred_display.lower()}', mas senioridade informada é "
                f"'{explicit_display.lower()}'."
            )
        elif signal.source == "skills_complexity":
            warnings.append(
                f"INCONSISTÊNCIA: Complexidade das skills sugere "
                f"'{inferred_display.lower()}', mas senioridade informada é "
                f"'{explicit_display.lower()}'."
            )

    return warnings


def _combine_signals(
    signals: list[SenioritySignal],
    warnings: list[str],
    explicit_seniority: str | None,
    job_title: str | None,
) -> SeniorityResolution:
    """Combina os sinais coletados usando o Motor de Combinação determinístico.

    Aplica as 5 regras de combinação para determinar o nível final, confiança,
    grau de acordo e necessidade de confirmação.

    Args:
        signals: Lista de sinais coletados (com pesos já redistribuídos).
        warnings: Lista de avisos de conflito já detectados.
        explicit_seniority: Valor original informado pelo recrutador.
        job_title: Título do cargo original.

    Returns:
        SeniorityResolution com o resultado final da resolução.
    """
    active_signals = [s for s in signals if s.level is not None]
    active_levels = [s.level for s in active_signals]
    source_parts = [s.source for s in active_signals]
    source_str = "+".join(source_parts) if source_parts else "none"

    metadata: dict[str, Any] = {
        "total_signals_collected": len(signals),
        "active_signals": len(active_signals),
        "signal_sources": [s.source for s in signals],
        "active_sources": source_parts,
        "weights": {s.source: round(s.weight, 4) for s in signals},
    }

    if not active_signals:
        logger.warning("No active signals available, defaulting to 'pleno'")
        return SeniorityResolution(
            level="pleno",
            source="none",
            confidence=0.0,
            agreement="none",
            signals=signals,
            validation_warnings=warnings,
            requires_confirmation=True,
            confirmation_message=(
                "Não consegui identificar o nível de senioridade desta vaga. "
                "Para gerar perguntas adequadas, preciso saber: é Júnior, Pleno, "
                "Sênior ou Liderança?"
            ),
            metadata=metadata,
        )

    level_counts = Counter(active_levels)
    most_common_level, most_common_count = level_counts.most_common(1)[0]

    explicit_signal = next((s for s in active_signals if s.source == "explicit"), None)
    inferred_signals = [s for s in active_signals if s.source != "explicit"]
    inferred_levels = [s.level for s in inferred_signals]

    all_agree = len(set(active_levels)) == 1

    has_conflict = False
    if explicit_signal and inferred_levels:
        conflicting_inferred = [l for l in inferred_levels if l != explicit_signal.level]
        if conflicting_inferred:
            has_conflict = True

    if len(active_signals) == 1:
        single_signal = active_signals[0]
        confidence = 0.70 if single_signal.source == "explicit" else 0.50
        logger.info(
            "Single signal resolution: level=%s, source=%s, confidence=%.2f",
            single_signal.level,
            single_signal.source,
            confidence,
        )
        return SeniorityResolution(
            level=single_signal.level or "pleno",
            source=source_str,
            confidence=confidence,
            agreement="single",
            signals=signals,
            validation_warnings=warnings,
            requires_confirmation=False,
            confirmation_message=None,
            metadata=metadata,
        )

    if all_agree:
        logger.info(
            "Full agreement resolution: level=%s, signals=%d",
            most_common_level,
            len(active_signals),
        )
        return SeniorityResolution(
            level=most_common_level or "pleno",
            source=source_str,
            confidence=1.0,
            agreement="full",
            signals=signals,
            validation_warnings=warnings,
            requires_confirmation=False,
            confirmation_message=None,
            metadata=metadata,
        )

    if has_conflict and explicit_signal:
        explicit_display = SENIORITY_DISPLAY_NAMES.get(
            explicit_signal.level or "", explicit_signal.level or ""
        )
        conflicting_displays = []
        conflicting_sources = []
        for s in inferred_signals:
            if s.level != explicit_signal.level:
                display = SENIORITY_DISPLAY_NAMES.get(s.level or "", s.level or "")
                conflicting_displays.append(display)
                conflicting_sources.append(s.source)

        inferred_majority = Counter(inferred_levels).most_common(1)[0][0] if inferred_levels else None
        inferred_majority_display = SENIORITY_DISPLAY_NAMES.get(
            inferred_majority, inferred_majority
        ) if inferred_majority else ""

        source_descriptions = []
        for src in conflicting_sources:
            if src == "title_keywords":
                source_descriptions.append(f"o título '{job_title}'")
            elif src == "jd_analysis":
                source_descriptions.append("a descrição da vaga")
            elif src == "salary_range":
                source_descriptions.append("a faixa salarial")
            elif src == "skills_complexity":
                source_descriptions.append("as skills técnicas")

        sources_text = " e ".join(source_descriptions) if source_descriptions else "outros sinais"

        confirmation_msg = (
            f"Você definiu {explicit_display}, mas {sources_text} "
            f"indicam {inferred_majority_display}. Qual nível está correto?"
        )

        logger.info(
            "Conflict resolution: explicit=%s vs inferred=%s, requires_confirmation=True",
            explicit_signal.level,
            inferred_majority,
        )

        return SeniorityResolution(
            level=explicit_signal.level or "pleno",
            source=source_str,
            confidence=0.40,
            agreement="conflict",
            signals=signals,
            validation_warnings=warnings,
            requires_confirmation=True,
            confirmation_message=confirmation_msg,
            metadata=metadata,
        )

    if most_common_count >= 2:
        logger.info(
            "Majority agreement resolution: level=%s, count=%d/%d",
            most_common_level,
            most_common_count,
            len(active_signals),
        )
        return SeniorityResolution(
            level=most_common_level or "pleno",
            source=source_str,
            confidence=0.85,
            agreement="majority",
            signals=signals,
            validation_warnings=warnings,
            requires_confirmation=False,
            confirmation_message=None,
            metadata=metadata,
        )

    if explicit_signal:
        resolved_level = explicit_signal.level
    else:
        weighted_levels: dict[str, float] = {}
        for s in active_signals:
            weighted_levels[s.level or ""] = weighted_levels.get(s.level or "", 0) + s.weight
        resolved_level = max(weighted_levels, key=lambda k: weighted_levels.get(k, 0.0))

    logger.info(
        "Weighted resolution fallback: level=%s",
        resolved_level,
    )

    return SeniorityResolution(
        level=resolved_level or "pleno",
        source=source_str,
        confidence=0.60,
        agreement="majority",
        signals=signals,
        validation_warnings=warnings,
        requires_confirmation=len(warnings) > 0,
        confirmation_message=None,
        metadata=metadata,
    )


async def resolve_seniority(
    explicit_seniority: str | None = None,
    job_title: str | None = None,
    job_description: str | None = None,
    department: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    technical_skills: list[str] | None = None,
    company_id: str | None = None,
) -> SeniorityResolution:
    """Resolve o nível de senioridade combinando múltiplos sinais de forma determinística.

    Função principal do sistema de resolução multi-sinal. Coleta sinais de todas
    as fontes disponíveis (entrada explícita, título, JD, salário, skills),
    redistribui pesos, detecta conflitos e combina os sinais usando regras
    determinísticas sem uso de LLM.

    Args:
        explicit_seniority: Senioridade informada explicitamente pelo recrutador
                           (ex: "Junior", "Sênior", "Tech Lead").
        job_title: Título do cargo (ex: "Senior Software Engineer").
        job_description: Texto completo da descrição da vaga (JD).
        department: Departamento da vaga (ex: "Engenharia", "Jurídico").
        salary_min: Salário mínimo em BRL.
        salary_max: Salário máximo em BRL.
        technical_skills: Lista de habilidades técnicas requeridas.
        company_id: Identificador da empresa (reservado para uso futuro).

    Returns:
        SeniorityResolution com o resultado completo da resolução incluindo
        nível final, confiança, acordo, sinais, avisos e metadados de auditoria.

    Exemplo:
        >>> result = await resolve_seniority(
        ...     explicit_seniority="Junior",
        ...     job_title="Senior Software Engineer",
        ...     salary_min=15000,
        ...     salary_max=25000,
        ... )
        >>> result.level
        'junior'
        >>> result.agreement
        'conflict'
        >>> result.requires_confirmation
        True
    """
    logger.info(
        "Starting multi-signal seniority resolution: "
        "explicit=%s, title=%s, has_jd=%s, salary=(%s-%s), "
        "skills_count=%s, company_id=%s",
        explicit_seniority,
        job_title,
        bool(job_description),
        salary_min,
        salary_max,
        len(technical_skills) if technical_skills else 0,
        company_id,
    )

    if not SENIORITY_RESOLVER_ENABLED:
        logger.warning("Seniority resolver is disabled via feature flag")
        fallback_level = normalize_seniority(explicit_seniority) if explicit_seniority else "pleno"
        return SeniorityResolution(
            level=fallback_level,
            source="explicit" if explicit_seniority else "fallback",
            confidence=0.50 if explicit_seniority else 0.0,
            agreement="single" if explicit_seniority else "none",
            signals=[],
            validation_warnings=["Resolver desabilitado via feature flag. Usando fallback."],
            requires_confirmation=False,
            confirmation_message=None,
            metadata={"feature_flag_enabled": False},
        )

    signals = _collect_signals(
        explicit_seniority=explicit_seniority,
        job_title=job_title,
        job_description=job_description,
        salary_min=salary_min,
        salary_max=salary_max,
        technical_skills=technical_skills,
    )

    _redistribute_weights(signals)

    warnings = _detect_conflicts(
        signals=signals,
        explicit_seniority=explicit_seniority,
        salary_min=salary_min,
        salary_max=salary_max,
    )

    for w in warnings:
        logger.warning("Conflict detected: %s", w)

    resolution = _combine_signals(
        signals=signals,
        warnings=warnings,
        explicit_seniority=explicit_seniority,
        job_title=job_title,
    )

    resolution.metadata["department"] = department
    resolution.metadata["company_id"] = company_id
    resolution.metadata["feature_flag_enabled"] = SENIORITY_RESOLVER_ENABLED

    logger.info(
        "Seniority resolution complete: level=%s, confidence=%.2f, "
        "agreement=%s, requires_confirmation=%s, warnings=%d",
        resolution.level,
        resolution.confidence,
        resolution.agreement,
        resolution.requires_confirmation,
        len(resolution.validation_warnings),
    )

    return resolution


def _run_resolve_sync(
    explicit_seniority: str | None = None,
    job_title: str | None = None,
    job_description: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    technical_skills: list[str] | None = None,
) -> "SeniorityResolution":
    """Executa resolve_seniority de forma síncrona."""
    coro = resolve_seniority(
        explicit_seniority=explicit_seniority,
        job_title=job_title,
        job_description=job_description,
        salary_min=salary_min,
        salary_max=salary_max,
        technical_skills=technical_skills,
    )
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def resolve_seniority_full(
    explicit_seniority: str | None = None,
    job_title: str | None = None,
    job_description: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    technical_skills: list[str] | None = None,
) -> "SeniorityResolution":
    """Wrapper síncrono que retorna a resolução completa com todos os metadados.

    Executa a resolução completa de senioridade e retorna o objeto
    SeniorityResolution inteiro, incluindo sinais, agreement, confidence,
    warnings e mensagem de confirmação.

    Args:
        explicit_seniority: Senioridade informada pelo recrutador.
        job_title: Título do cargo.
        job_description: Texto da descrição da vaga.
        salary_min: Salário mínimo da vaga em BRL.
        salary_max: Salário máximo da vaga em BRL.
        technical_skills: Lista de habilidades técnicas requeridas.

    Returns:
        SeniorityResolution completa com todos os metadados de auditoria.
    """
    return _run_resolve_sync(
        explicit_seniority=explicit_seniority,
        job_title=job_title,
        job_description=job_description,
        salary_min=salary_min,
        salary_max=salary_max,
        technical_skills=technical_skills,
    )


def resolve_seniority_simple(
    explicit_seniority: str | None = None,
    job_title: str | None = None,
    job_description: str | None = None,
) -> str:
    """Wrapper síncrono simplificado que retorna apenas o nível como string.

    Função de conveniência para compatibilidade retroativa. Executa a resolução
    completa de senioridade de forma síncrona e retorna apenas o nível final
    como string.

    Args:
        explicit_seniority: Senioridade informada pelo recrutador.
        job_title: Título do cargo.
        job_description: Texto da descrição da vaga.

    Returns:
        String com o nível de senioridade resolvido ("junior", "pleno",
        "senior", "lead", "executive").

    Exemplo:
        >>> resolve_seniority_simple("Senior", "Senior Developer")
        'senior'

        >>> resolve_seniority_simple(None, "Engenheiro")
        'pleno'
    """
    result = _run_resolve_sync(
        explicit_seniority=explicit_seniority,
        job_title=job_title,
        job_description=job_description,
    )
    return result.level
