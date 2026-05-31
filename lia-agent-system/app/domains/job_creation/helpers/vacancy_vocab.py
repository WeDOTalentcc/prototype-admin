"""Normalização de vocabulário wizard → cadastro de vaga (item #3, 2026-05-31).

O wizard usa vocabulário INTERNO (EN/minúsculo: hybrid, diretor, estagio) mas o
cadastro/FE (`edit-job-modal.constants.tsx`) espera vocabulário canônico PT
capitalizado (Híbrido→'híbrido' value, 'Diretor', 'Estágio'). Gravar direto fazia
o dropdown do cadastro não casar (vaga abria com campo vazio).

Fonte da verdade (FE — plataforma-lia/src/components/modals/edit-job-modal.constants.tsx):
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
