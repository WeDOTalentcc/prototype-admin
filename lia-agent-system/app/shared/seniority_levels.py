"""Niveis de senioridade — FONTE UNICA canonica (back + front).

Antes a lista de niveis vivia hardcoded no frontend
(compensation-policies-types.ts) e como strings soltas espalhadas (PRV, verba,
vaga, membro de depto). Aqui ela e a fonte unica: SalaryBand.level,
CompensationComponent.seniority_levels[] e a UI de bandas/escopo referenciam
estes ids. O espelho TS fica em plataforma-lia/src/lib/compensation/seniority-levels.ts
e DEVE permanecer identico (sensor: scripts/check_seniority_levels_sync.py).

Os ids normalizam corretamente via vacancy_vocab.to_match_seniority_key, entao o
matcher de elegibilidade continua tolerante a EN/PT/acentos.
"""
from __future__ import annotations

# Ordem = ordem de exibicao (junior -> c-level)
CANONICAL_SENIORITY_LEVELS: list[dict[str, str]] = [
    {"id": "junior", "label": "Júnior"},
    {"id": "pleno", "label": "Pleno"},
    {"id": "senior", "label": "Sênior"},
    {"id": "staff", "label": "Staff"},
    {"id": "principal", "label": "Principal"},
    {"id": "manager", "label": "Gerente"},
    {"id": "director", "label": "Diretor"},
    {"id": "c-level", "label": "C-Level"},
]

SENIORITY_LEVEL_IDS: tuple[str, ...] = tuple(l["id"] for l in CANONICAL_SENIORITY_LEVELS)

_LABEL_BY_ID = {l["id"]: l["label"] for l in CANONICAL_SENIORITY_LEVELS}

# Default de display order por id (para SalaryBand.order ao seedar)
_ORDER_BY_ID = {l["id"]: i for i, l in enumerate(CANONICAL_SENIORITY_LEVELS)}


def is_valid_level(level_id: str | None) -> bool:
    return bool(level_id) and level_id in SENIORITY_LEVEL_IDS


def label_for(level_id: str | None) -> str:
    if not level_id:
        return ""
    return _LABEL_BY_ID.get(level_id, level_id)


def order_for(level_id: str | None) -> int:
    if not level_id:
        return 999
    return _ORDER_BY_ID.get(level_id, 999)
