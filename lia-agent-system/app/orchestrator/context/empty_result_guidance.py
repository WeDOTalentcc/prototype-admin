"""
empty_result_guidance — sinal estruturado para buscas com 0 resultados (P0.2).

Regua Apollo: busca vazia NAO termina em "nada encontrado". O sistema relaxa o
filtro mais restritivo, roda de novo e oferece opcoes com contagem. Este helper
e o SENSOR (computacional): em vez de uma lista vazia silenciosa, as tools de
busca devolvem filtros aplicados + sugestoes de relaxamento, e o agente
(guiado pelo prompt) relaxa e oferece opcoes.

Extensao da CLAUDE.md REGRA 4 (anti-silent-fallback): 0-resultados e um sinal,
nao um silencio.

Funcao PURA — testavel sem DB/LLM. Sensor: tests/contract/test_empty_result_guidance.py
"""
from __future__ import annotations

from typing import Any

_EMPTY_VALUES = (None, "", 0, [], {}, ())


def build_empty_result_guidance(
    entity: str, applied_filters: dict[str, Any] | None
) -> dict[str, Any]:
    """Constroi o sinal estruturado de 0-resultados.

    Args:
        entity: substantivo singular ("candidato", "vaga").
        applied_filters: filtros que estavam ativos na busca vazia.

    Returns:
        {empty, applied_filters (so os ativos), relaxation_suggestions, guidance}.
    """
    active = {
        k: v
        for k, v in (applied_filters or {}).items()
        if v not in _EMPTY_VALUES
    }
    suggestions = [
        f"remover o filtro '{k}' (={v})" for k, v in active.items()
    ]

    if not suggestions:
        guidance = (
            f"Nenhum {entity} encontrado. Como nao havia filtros restritivos, "
            f"provavelmente nao ha {entity}s para este criterio — confirme com "
            f"o recrutador ou amplie o escopo."
        )
    else:
        filtros_txt = ", ".join(f"{k}={v}" for k, v in active.items())
        guidance = (
            f"Nenhum {entity} encontrado com os filtros aplicados ({filtros_txt}). "
            f"NAO pare aqui: relaxe o filtro mais restritivo, rode a busca de novo "
            f"e ofereca as opcoes com a contagem de cada uma "
            f"(ex.: 'sem o filtro X sao N {entity}s'). Deixe o recrutador escolher."
        )

    return {
        "empty": True,
        "applied_filters": active,
        "relaxation_suggestions": suggestions,
        "guidance": guidance,
    }
