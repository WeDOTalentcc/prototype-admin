"""Normalização de vocabulário wizard → cadastro de vaga (item #3, 2026-05-31).

O wizard usa vocabulário INTERNO (EN/minúsculo: hybrid, diretor, estagio) mas o
cadastro/FE (formulario de vaga, job-edit-tab) espera vocabulário canônico PT
capitalizado (Híbrido→'híbrido' value, 'Diretor', 'Estágio'). Gravar direto fazia
o dropdown do cadastro não casar (vaga abria com campo vazio).

Fonte da verdade (FE — formulario de cadastro de vaga, plataforma-lia/src/components/jobs/job-edit-tab/):
  WORK_MODELS      = presencial | híbrido | remoto
  SENIORITY_LEVELS = Estágio | Júnior | Pleno | Sênior | Especialista | Coordenador | Gerente | Diretor
  CONTRACT_TYPES   = CLT | PJ | Estágio | Freelancer | Temporário

Aplicado no BOUNDARY canônico (publish_node), beneficiando orquestrador + grafo.
Fail-safe: valor não-mapeado é devolvido como veio (preserva o dado; nunca perde).
"""
from __future__ import annotations

import unicodedata
from typing import Optional


def _norm(s: str) -> str:
    """lower + strip de acentos para matching robusto."""
    s = (s or "").strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


# ── work_model ───────────────────────────────────────────────────────────
_WORK_MODEL_MAP = {
    "remote": "remoto", "remoto": "remoto", "home office": "remoto",
    "home-office": "remoto", "homeoffice": "remoto",
    "hybrid": "híbrido", "hibrido": "híbrido", "hibrida": "híbrido",
    "presencial": "presencial", "onsite": "presencial", "on-site": "presencial",
    "on site": "presencial", "escritorio": "presencial",
}


def to_canonical_work_model(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return _WORK_MODEL_MAP.get(_norm(value), value)


# ── seniority_level ──────────────────────────────────────────────────────
# Mapeia níveis WSI (estagiario..diretor) + sinônimos livres → vocabulário FE.
_SENIORITY_MAP = {
    "estagiario": "Estágio", "estagio": "Estágio", "intern": "Estágio",
    "trainee": "Estágio", "aprendiz": "Estágio",
    "junior": "Júnior", "jr": "Júnior",
    "pleno": "Pleno", "mid": "Pleno", "pl": "Pleno",
    "senior": "Sênior", "sr": "Sênior",
    "especialista": "Especialista", "specialist": "Especialista", "principal": "Especialista",
    "lead": "Coordenador", "coordenador": "Coordenador", "coordenadora": "Coordenador",
    "gerente": "Gerente", "manager": "Gerente", "gerencial": "Gerente",
    "diretor": "Diretor", "diretora": "Diretor", "director": "Diretor",
    "head": "Diretor", "vp": "Diretor", "c-level": "Diretor", "cfo": "Diretor",
    "cto": "Diretor", "ceo": "Diretor",
}


def to_canonical_seniority(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return _SENIORITY_MAP.get(_norm(value), value)


# ── employment_type / contract ───────────────────────────────────────────
_EMPLOYMENT_MAP = {
    "clt": "CLT", "pj": "PJ", "pessoa juridica": "PJ",
    "estagio": "Estágio", "estagiario": "Estágio", "intern": "Estágio",
    "freelancer": "Freelancer", "freela": "Freelancer", "freelance": "Freelancer",
    "temporario": "Temporário", "temporary": "Temporário", "temp": "Temporário",
}


def to_canonical_employment_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return _EMPLOYMENT_MAP.get(_norm(value), value)


# ── language level ───────────────────────────────────────────────────────
# FE (edit-job-modal.tsx): Básico | Intermediário | Avançado | Fluente | Nativo
_LANG_LEVEL_MAP = {
    "basico": "Básico", "basic": "Básico", "iniciante": "Básico",
    "intermediario": "Intermediário", "intermediate": "Intermediário",
    "avancado": "Avançado", "advanced": "Avançado",
    "fluente": "Fluente", "fluent": "Fluente",
    "nativo": "Nativo", "native": "Nativo",
}


def to_canonical_language_level(value: Optional[str]) -> str:
    """Normaliza o nível de idioma para o vocabulário FE. Default Intermediário."""
    if not value:
        return "Intermediário"
    return _LANG_LEVEL_MAP.get(_norm(value), "Intermediário")


# ── seniority → cv_screening (5 níveis) ──────────────────────────────────
# Consolidação WSI: o kernel canônico cv_screening.WSIService usa 5 níveis
# (junior|pleno|senior|lead|executive). Mapeia o vocabulário do wizard p/ ele.
_CV_SENIORITY_MAP = {
    "estagiario": "junior", "estagio": "junior", "intern": "junior", "trainee": "junior",
    "junior": "junior", "jr": "junior",
    "pleno": "pleno", "mid": "pleno", "pl": "pleno",
    "senior": "senior", "sr": "senior", "especialista": "senior", "specialist": "senior",
    "lead": "lead", "coordenador": "lead", "principal": "lead",
    "gerente": "executive", "manager": "executive", "diretor": "executive",
    "director": "executive", "head": "executive", "vp": "executive",
    "c-level": "executive", "ceo": "executive", "cfo": "executive", "cto": "executive",
}

_CV_VALID = {"junior", "pleno", "senior", "lead", "executive"}


def to_cv_screening_seniority(value: Optional[str]) -> str:
    """Mapeia senioridade do wizard p/ os 5 níveis do cv_screening.WSIService.
    Default 'pleno' (mesmo default do serviço canônico)."""
    if not value:
        return "pleno"
    n = _norm(value)
    if n in _CV_VALID:
        return n
    return _CV_SENIORITY_MAP.get(n, "pleno")


# ── match keys (benefício ↔ dimensão da vaga) ────────────────────────────
# Chave normalizada p/ casar dimensões de CompanyBenefit com os valores da
# vaga, ignorando EN/PT, caixa e acentos. Reusa os mapas canônicos acima
# (single source of truth) + _norm sobre o canônico resultante, garantindo
# que "jr"/"Júnior" e "clt"/"CLT" colidam na mesma chave de matching.
def to_match_seniority_key(value: Optional[str]) -> str:
    if not value:
        return ""
    return _norm(to_canonical_seniority(value) or "")


def to_match_contract_key(value: Optional[str]) -> str:
    if not value:
        return ""
    return _norm(to_canonical_employment_type(value) or "")
