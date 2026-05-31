"""Matching de elegibilidade catalogo<->vaga (compartilhado benefits + comp).

Extraido de company_benefit_repository (2026-05-31, Rule of Three: benefits +
compensation). Regras: lista vazia/None = aplica a todos; "all" = curinga; senao
casa pelo token normalizado (key_fn) ignorando EN/PT, caixa e acentos.
"""
from app.domains.job_creation.helpers.vacancy_vocab import _norm


def matches_dimension_list(values, vaga_key, key_fn) -> bool:
    """True se o item se aplica ao valor da vaga nesta dimensao (seniority/contract)."""
    if not values:
        return True
    if any((v or "").strip().lower() == "all" for v in values):
        return True
    if not vaga_key:
        return True  # vaga nao informou a dimensao -> nao restringe
    return any(key_fn(v) == vaga_key for v in values)


def matches_department(departments, vaga_department) -> bool:
    """departments e um dict {nome_dept: bool}. Aplica a todos se vazio/sem chave
    ativa; 'all' ativo = curinga; senao casa o dept da vaga (normalizado)."""
    if not departments or not any(departments.values()):
        return True
    if departments.get("all"):
        return True
    if not vaga_department:
        return True
    target = _norm(vaga_department)
    return any(enabled and _norm(k) == target for k, enabled in departments.items())
