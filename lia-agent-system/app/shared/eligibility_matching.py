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


def _digits(s) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


def matches_subsidiaries(subsidiaries, vaga_subsidiary=None, vaga_cnpj=None) -> bool:
    """subsidiaries = [{"name","cnpj"}]. Vazio/None = aplica a todas as entidades.
    Se a vaga nao informar filial/CNPJ, nao restringe. Senao casa por nome
    normalizado OU CNPJ (so digitos)."""
    if not subsidiaries or not isinstance(subsidiaries, list):
        return True
    if not vaga_subsidiary and not vaga_cnpj:
        return True
    tgt_name = _norm(vaga_subsidiary) if vaga_subsidiary else ""
    tgt_cnpj = _digits(vaga_cnpj) if vaga_cnpj else ""
    for s in subsidiaries:
        if not isinstance(s, dict):
            continue
        if tgt_name and _norm(s.get("name")) == tgt_name:
            return True
        if tgt_cnpj and _digits(s.get("cnpj")) == tgt_cnpj:
            return True
    return False


def matches_area(areas, vaga_area=None) -> bool:
    """areas = tokens livres de area de negocio. Vazio/None = aplica a todas.
    Se a vaga nao informar area, nao restringe. Senao casa por token normalizado."""
    if not areas:
        return True
    if any((a or "").strip().lower() == "all" for a in areas):
        return True
    if not vaga_area:
        return True
    target = _norm(vaga_area)
    return any(_norm(a) == target for a in areas)
