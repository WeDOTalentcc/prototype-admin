"""block_distribution(mode, seniority) -- fonte canonical UNICA do split por
bloco (technical/behavioral) das perguntas WSI. Le o YAML per-senioridade
(wsi_question_distribution.yaml).

Audit 2026-06-05 (#3 -- decisao Paulo: per-senioridade e canonical): antes havia
SPLIT-BRAIN -- a sugestao de competencias (competency_benchmark), a auto-complete
(wsi_question_generator) e os thresholds de qualidade (jd_enrichment) usavam
SCREENING_MODE_CONFIG (por MODO: full=8+4), enquanto o VALIDADOR usava a tabela
por SENIORIDADE (full/senior=7+5). Resultado: gerava 8+4, o validador exigia
7+5, acusava "falta 1 comportamental" e sugeria uma 13a pergunta (fora do total
12). Agora TODOS os consumidores de split passam por aqui (YAML por senioridade).
SCREENING_MODE_CONFIG fica so para total_questions/estimated_minutes (estimativa
de tempo no intake_gate), que independem da senioridade.

graph.py::_get_question_distribution delega a este modulo (uma fonte de codigo).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict

from app.domains.job_creation.internal.constants import (
    _WSI_QUESTION_DISTRIBUTION_FILE,
)

# Default conservador (compact/pleno) quando a senioridade nao existe na tabela.
_DEFAULT_BLOCK = {"technical": 5, "behavioral": 2}


@lru_cache(maxsize=1)
def load_distributions() -> Dict[str, Dict[str, Dict[str, int]]]:
    """Lazy load + cache do YAML canonical. Fail-loud se malformado."""
    import yaml as _yaml

    with open(_WSI_QUESTION_DISTRIBUTION_FILE) as _fh:
        data = _yaml.safe_load(_fh)
    if not isinstance(data, dict):
        raise RuntimeError(
            f"wsi_question_distribution.yaml malformed: expected dict, got {type(data)}"
        )
    return data


def _norm_seniority(seniority: str | None) -> str:
    return (
        (seniority or "")
        .lower()
        .replace("sênior", "senior")
        .replace("júnior", "junior")
        .replace("estágio", "estagiario")
        .replace("estagiário", "estagiario")
    )


def block_distribution(mode: str, seniority: str | None) -> Dict[str, int]:
    """{"technical": int, "behavioral": int} para (modo, senioridade).

    Per-senioridade (YAML canonical). Default pleno -> compact {5,2} quando a
    senioridade nao consta. Soma technical+behavioral == total_questions do modo
    (invariante pinado em tests/contract).
    """
    distributions = load_distributions()
    table = distributions.get(mode if mode == "compact" else "full", {})
    key = _norm_seniority(seniority)
    return table.get(key, table.get("pleno", dict(_DEFAULT_BLOCK)))
