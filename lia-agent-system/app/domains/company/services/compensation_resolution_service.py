"""Motor de resolucao de remuneracao — UNICO ponto de multiplicacao % -> R$.

Antes deste servico, o "% do salario" da verba (CompensationComponent) era
decorativo: nunca era multiplicado por nada. Aqui derivamos o valor absoluto:

    R$ = (% / 100) x faixa_salarial[nivel]

A faixa vem do SalaryBand canonico (band_map = {level: {min,mid,max,currency}}),
nunca redigitada na verba. Consumido por vaga (preview), oferta e (futuro) JD.

Funcoes PURAS (sem DB) p/ testabilidade. O caller obtem band_map via
SalaryBandRepository.get_band_map e passa aqui. Aceita verba como objeto ORM OU
dict (getattr/get).
"""
from __future__ import annotations

from typing import Any


def _get(obj: Any, key: str, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _num(x) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def resolve_for_band(component: Any, band: Any) -> dict:
    """Resolve a faixa R$ de UMA verba contra UMA banda salarial {min,mid,max}.

    Retorna {min, max, currency, basis} onde basis explica como foi derivado:
      - "fixed"            valor ja absoluto (value_type=currency / min_amount/max_amount)
      - "percent_of_salary"  % x faixa do nivel
      - "n_salaries"       spec.n_salaries_* x faixa do nivel (PLR/PPR)
      - "undefined"        sem dados suficientes p/ derivar
    min/max podem ser None quando undefined.
    """
    value_type = (_get(component, "value_type") or "percent").lower()
    currency = _get(component, "currency") or (_get(band, "currency") if band else None) or "BRL"

    # 1) Valor absoluto declarado (currency) — nao depende da banda
    min_amount = _num(_get(component, "min_amount"))
    max_amount = _num(_get(component, "max_amount"))
    if value_type == "currency" or (min_amount is not None or max_amount is not None):
        if min_amount is not None or max_amount is not None:
            return {"min": min_amount, "max": max_amount, "currency": currency, "basis": "fixed"}

    band_min = _num(_get(band, "min")) if band else None
    band_max = _num(_get(band, "max")) if band else None

    # 2) Percentual do salario
    min_pct = _num(_get(component, "min_pct"))
    max_pct = _num(_get(component, "max_pct"))
    target_pct = _num(_get(component, "target_pct"))
    if min_pct is None and max_pct is None and target_pct is not None:
        min_pct = max_pct = target_pct
    if (min_pct is not None or max_pct is not None) and (band_min is not None or band_max is not None):
        lo = (band_min * min_pct / 100.0) if (band_min is not None and min_pct is not None) else None
        hi = (band_max * max_pct / 100.0) if (band_max is not None and max_pct is not None) else None
        return {"min": lo, "max": hi, "currency": currency, "basis": "percent_of_salary"}

    # 3) PLR/PPR em "n salarios" (spec)
    spec = _get(component, "spec") or {}
    if isinstance(spec, dict):
        n_min = _num(spec.get("n_salaries_min"))
        n_max = _num(spec.get("n_salaries_max"))
        if (n_min is not None or n_max is not None) and (band_min is not None or band_max is not None):
            lo = (band_min * n_min) if (band_min is not None and n_min is not None) else None
            hi = (band_max * n_max) if (band_max is not None and n_max is not None) else None
            return {"min": lo, "max": hi, "currency": currency, "basis": "n_salaries"}

    return {"min": None, "max": None, "currency": currency, "basis": "undefined"}


def _scoped_levels(component: Any, band_map: dict) -> list[str]:
    """Niveis aos quais a verba se aplica. Vazio = todos os niveis com banda."""
    levels = _get(component, "seniority_levels") or []
    levels = [str(l).strip() for l in levels if str(l).strip()]
    if not levels or any(l.lower() == "all" for l in levels):
        return list(band_map.keys())
    # so niveis que tem banda definida
    return [l for l in levels if l in band_map]


def resolve_for_levels(component: Any, band_map: dict) -> dict[str, dict]:
    """Resolve a verba para cada nivel aplicavel. {level: {min,max,currency,basis}}.

    band_map = {level_id: {min,mid,max,currency}} (SalaryBandRepository.get_band_map).
    """
    out: dict[str, dict] = {}
    for level in _scoped_levels(component, band_map):
        out[level] = resolve_for_band(component, band_map.get(level))
    return out


def resolve_for_salary_range(component: Any, salary_range: Any) -> dict:
    """Resolve a verba contra um salary_range arbitrario {min,max,currency}
    (override da vaga). Trata salary_range como uma 'banda' ad-hoc."""
    band = None
    if salary_range:
        band = {
            "min": _num(_get(salary_range, "min")),
            "max": _num(_get(salary_range, "max")),
            "currency": _get(salary_range, "currency") or "BRL",
        }
    return resolve_for_band(component, band)
