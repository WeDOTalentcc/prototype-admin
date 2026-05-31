"""Canonical JD quality scorer — WSI 9 dimensões (F1.B).

Consolidação WSI Fase 3 (decisão Paulo 2026-05-31): a avaliação determinística
de qualidade do Job Description (9 dimensões D1-D9, 5 bands, hard-block < 30)
que vivia INLINE no endpoint ``/api/v1/wsi/jd-evaluate`` agora é canônica em
cv_screening — single source of truth. Endpoint (Settings) e wizard
conversacional consomem a MESMA função.

100% determinístico (sem LLM, sem DB). Constantes + lógica idênticas ao endpoint
original (zero mudança de comportamento). ``api/v1/wsi/_shared`` re-exporta as
constantes para preservar consumidores existentes.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constantes JD evaluate (movidas de api/v1/wsi/_shared.py — Fase 3)
# ---------------------------------------------------------------------------
_JD_SENIORITY_KEYWORDS = {
    "estagiario": ["estagiário", "estagiaria", "estágio", "trainee"],
    "junior": ["junior", "júnior", "jr"],
    "pleno": ["pleno", "pl"],
    "senior": ["sênior", "senior", "sr"],
    "lead": ["lead", "líder", "tech lead"],
    "principal": ["principal", "staff"],
    "diretor": ["diretor", "diretora", "director"],
    "vp": ["vp", "vice-presidente", "cxo", "cto", "cpo"],
}
_BIAS_TERMS = [
    "boa aparência",
    "apresentação pessoal",
    "jovem",
    "recém-formado",
    "native speaker",
    "universidades de primeira linha",
    "faculdade de ponta",
    "perfil adequado",
    "escola particular",
    "bairros nobres",
    "morar próximo",
    "boa família",
    "estado civil",
    "filho",
    "filha",
    "casado",
    "solteiro",
]
_JD_BANDS = [
    (85, "excelente", "Excelente"),
    (70, "bom", "Bom"),
    (50, "adequado", "Adequado"),
    (30, "insuficiente", "Insuficiente"),
    (0, "critico", "Crítico"),
]


def _jd_get_band(score: int):
    for threshold, band_key, band_label in _JD_BANDS:
        if score >= threshold:
            return band_key, band_label
    return "critico", "Crítico"


def evaluate_jd_quality(
    *,
    description: str | None = None,
    job_title: str | None = None,
    department: str | None = None,
    seniority: str | None = None,
    responsibilities: list[str] | None = None,
    technical_skills: list[str] | None = None,
    behavioral_competencies: list[str] | None = None,
    d3_min: int = 9,
    d4_min: int = 5,
) -> dict[str, Any]:
    """Avalia qualidade do JD em 9 dimensões (D1-D9), score 0-100 + band.

    Determinístico. Retorna dict: {score, max_score, band, band_label,
    indicators, suggestion, can_generate}. ``can_generate`` é False quando
    score < 30 (band crítico) — o caller decide se bloqueia (o endpoint
    levanta HTTP 422; o wizard pode apenas sinalizar).
    """
    resp_count = len(responsibilities or [])
    tech_count = len(technical_skills or [])
    behav_count = len(behavioral_competencies or [])
    has_seniority = bool(seniority)
    desc = (description or "").lower()
    title = (job_title or "").lower()
    dept = department or ""

    score = 0
    indicators: list[dict[str, Any]] = []

    title_has_seniority = any(
        kw in title
        for keywords in _JD_SENIORITY_KEYWORDS.values()
        for kw in keywords
    )
    pts_1 = 10 if (title_has_seniority or has_seniority) else 0
    score += pts_1
    indicators.append({
        "dimension": "D1",
        "label": "Clareza do título",
        "weight": 10,
        "earned": pts_1,
        "status": "sufficient" if pts_1 == 10 else "insufficient",
        "detail": f"{'Indicador de senioridade detectado' if pts_1 else 'Título sem indicador de senioridade'}",
    })

    if resp_count >= 5:
        pts_2, st_2 = 15, "sufficient"
    elif resp_count >= 2:
        pts_2, st_2 = 7, "partial"
    else:
        pts_2, st_2 = 0, "insufficient"
    score += pts_2
    indicators.append({
        "dimension": "D2", "label": "Responsabilidades", "weight": 15,
        "earned": pts_2, "count": resp_count, "minimum": 5, "status": st_2,
        "detail": f"{resp_count} responsabilidade(s) — mínimo ideal: 5",
    })

    # Consolidação WSI Fase 3.3: d3_min parametrizável (mode-aware no wizard;
    # default 9 = mínimo ideal Full WSI, paridade com /jd-evaluate).
    _D3_MIN_IDEAL = d3_min
    if tech_count >= _D3_MIN_IDEAL:
        pts_3, st_3 = 15, "sufficient"
    elif tech_count >= 3:
        pts_3, st_3 = 7, "partial"
    else:
        pts_3, st_3 = 0, "insufficient"
    score += pts_3
    indicators.append({
        "dimension": "D3", "label": "Skills técnicas", "weight": 15,
        "earned": pts_3, "count": tech_count, "minimum": _D3_MIN_IDEAL, "status": st_3,
        "detail": f"{tech_count} skill(s) técnica(s) — mínimo ideal: {_D3_MIN_IDEAL}",
    })

    _D4_MIN_IDEAL = d4_min
    if behav_count >= _D4_MIN_IDEAL:
        pts_4, st_4 = 10, "sufficient"
    elif behav_count >= 2:
        pts_4, st_4 = 5, "partial"
    else:
        pts_4, st_4 = 0, "insufficient"
    score += pts_4
    indicators.append({
        "dimension": "D4", "label": "Comp. comportamentais", "weight": 10,
        "earned": pts_4, "count": behav_count, "minimum": _D4_MIN_IDEAL, "status": st_4,
        "detail": f"{behav_count} comportamental(is) — mínimo ideal: {_D4_MIN_IDEAL}",
    })

    if has_seniority and resp_count >= 3:
        pts_5, st_5 = 15, "sufficient"
    elif has_seniority or resp_count >= 2:
        pts_5, st_5 = 7, "partial"
    else:
        pts_5, st_5 = 0, "insufficient"
    score += pts_5
    indicators.append({
        "dimension": "D5", "label": "Consistência senioridade", "weight": 15,
        "earned": pts_5, "status": st_5,
        "detail": "Senioridade declarada com responsabilidades compatíveis" if pts_5 == 15 else "Senioridade ou responsabilidades insuficientes para calibração",
    })

    desc_words = len(desc.split()) if desc else 0
    has_contradiction = (
        ("autonomia" in desc and "aprovação" in desc) or
        ("independente" in desc and "acompanhamento diário" in desc)
    )
    pts_6 = 0 if has_contradiction else (10 if desc_words > 80 else 5)
    score += pts_6
    indicators.append({
        "dimension": "D6", "label": "Ausência de inconsistências", "weight": 10,
        "earned": pts_6,
        "status": "insufficient" if has_contradiction else ("sufficient" if pts_6 == 10 else "partial"),
        "detail": "Contradição detectada (autonomia vs. aprovação)" if has_contradiction else "Sem inconsistências detectadas",
    })

    has_context = bool(dept) or any(kw in desc for kw in ["empresa", "equipe", "time", "setor", "segmento", "startup", "corporati"])
    pts_7 = 10 if has_context else 0
    score += pts_7
    indicators.append({
        "dimension": "D7", "label": "Contexto organizacional", "weight": 10,
        "earned": pts_7, "status": "sufficient" if pts_7 == 10 else "insufficient",
        "detail": "Contexto de empresa/time/setor presente" if pts_7 else "Sem contexto organizacional (empresa, time, setor)",
    })

    found_bias = [t for t in _BIAS_TERMS if t in desc or t in title]
    pts_8 = 0 if found_bias else 10
    score += pts_8
    indicators.append({
        "dimension": "D8", "label": "Linguagem inclusiva", "weight": 10,
        "earned": pts_8, "status": "insufficient" if found_bias else "sufficient",
        "detail": f"Termo(s) de viés encontrado(s): {', '.join(found_bias[:3])}" if found_bias else "Linguagem neutra e inclusiva",
    })

    all_text = " ".join(filter(None, [
        description,
        " ".join(responsibilities or []),
        " ".join(technical_skills or []),
        " ".join(behavioral_competencies or []),
    ]))
    total_words = len(all_text.split())
    pts_9 = 5 if total_words >= 150 else 0
    score += pts_9
    indicators.append({
        "dimension": "D9", "label": "Densidade total", "weight": 5,
        "earned": pts_9, "word_count": total_words, "minimum": 150,
        "status": "sufficient" if pts_9 == 5 else "insufficient",
        "detail": f"{total_words} palavras — mínimo ideal: 150",
    })

    band_key, band_label = _jd_get_band(score)

    if score >= 85:
        suggestion = f"JD excelente para {job_title}. Perguntas WSI serão altamente calibradas com {tech_count} competências técnicas e {behav_count} comportamentais."
    elif score >= 70:
        suggestion = "JD bem estruturado. Perguntas WSI geradas com boa qualidade. Recomenda-se enriquecer contexto organizacional para maximizar precisão."
    elif score >= 50:
        missing = []
        if resp_count < 5:
            missing.append(f"responsabilidades (tem {resp_count}, ideal ≥5)")
        if tech_count < 3:
            missing.append(f"skills técnicas (tem {tech_count}, ideal ≥3)")
        if behav_count < 2:
            missing.append(f"comportamentais (tem {behav_count}, ideal ≥2)")
        suggestion = f"JD adequado mas com lacunas. Melhore: {'; '.join(missing) or 'contexto e densidade'}."
    elif score >= 30:
        suggestion = "JD insuficiente para gerar perguntas de alta qualidade. Adicione responsabilidades detalhadas, skills técnicas específicas e senioridade."
    else:
        suggestion = "JD crítico — perguntas WSI bloqueadas. Adicione no mínimo: título com senioridade, 2+ responsabilidades, 1+ skill técnica e senioridade definida."

    return {
        "score": score,
        "max_score": 100,
        "band": band_key,
        "band_label": band_label,
        "indicators": indicators,
        "suggestion": suggestion,
        "can_generate": score >= 30,
        "details": {
            "responsibilities_count": resp_count,
            "technical_skills_count": tech_count,
            "behavioral_competencies_count": behav_count,
            "seniority_defined": has_seniority,
            "total_word_count": total_words,
            "has_context": has_context,
            "bias_terms_found": found_bias,
            "has_inconsistency": has_contradiction,
        },
    }
