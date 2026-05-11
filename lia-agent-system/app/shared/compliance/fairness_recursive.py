"""PR3 (Task #1003) — Recursive FairnessGuard wrapper.

Origem: bug C3 do audit T1-T6 ("FairnessGuard com bypass estrutural em 4 das 6
tools"). Antes deste helper, os wrappers em
``app/domains/company_settings/agents/company_tool_registry.py`` filtravam
``isinstance(value, str) and len(value) > 10`` antes de chamar
``FairnessGuard.check`` — o que deixava passar:

  * listas (``dei_initiatives = ["jovens", "solteiros"]``);
  * dicts (``default_salary_ranges = {"Junior Homem": "5k", ...}``);
  * strings curtas com bias (``"Só jovens"`` = 9 chars);
  * payloads de ``import_workforce_plan`` e ``import_benefits_from_data``
    nunca eram passados pelo guard.

``validate_fairness_recursive`` percorre qualquer payload (Mapping | Sequence |
str) chamando ``FairnessGuard.check`` em cada *string folha* e veta no primeiro
flag, retornando contexto suficiente para a LIA verbalizar "esse trecho gerou
um alerta de viés, prefere reescrever?".

Contrato (mantido estável para os 5 wrappers que consomem):

    result = validate_fairness_recursive(payload, guard=_fairness_guard)
    if result.is_blocked:
        return {
            "success": False,
            "error": "fairness_blocked",
            "data": {
                "offending_field": result.offending_field,
                "offending_signal": result.offending_signal,
                "category": result.category,
            },
            "message": result.educational_message,
        }

Sem `len > 10` aqui — quem decide o que é viés é o ``FairnessGuard``, não o
caller (Crença #02 do WeDO + Inegociável #2).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult


@dataclass
class RecursiveFairnessResult:
    """Resultado consolidado da varredura recursiva.

    ``offending_field`` é o "caminho dot-notation" até a string folha que
    disparou o block (ex.: ``"plan_data[0].role"`` ou ``"culture.dei_initiatives[1]"``).
    ``offending_signal`` é o trecho exato (truncado) que o FairnessGuard
    flagou — usado pela LIA para devolver feedback educativo preciso.
    """

    is_blocked: bool
    offending_field: Optional[str] = None
    offending_signal: Optional[str] = None
    category: Optional[str] = None
    educational_message: Optional[str] = None
    blocked_terms: list[str] | None = None


_MAX_SIGNAL_LEN = 200

# Limites defensivos contra payloads abusivos (DoS via guard recursivo).
# Os 5 wrappers chamam isso ANTES de qualquer DB call — um payload
# patológico não deve poder consumir CPU sem teto. Os limites são
# generosos para tenants reais (workforce com centenas de itens passa
# tranquilo) mas cortam payloads adversariais.
_MAX_DEPTH = 32
_MAX_NODES = 10_000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_SIGNAL_LEN:
        return text
    return text[: _MAX_SIGNAL_LEN - 1] + "…"


def _walk(
    payload: Any,
    guard: FairnessGuard,
    path: str,
    *,
    depth: int,
    counter: list[int],
) -> Optional[RecursiveFairnessResult]:
    # Defesa: corta silenciosamente quando estoura o orçamento.
    # Retornar None aqui é fail-OPEN local mas o caller é tool de save
    # com auditoria — payloads que estouram esses limites já indicam
    # abuso e devem ser tratados acima (validação de schema, body size).
    if depth > _MAX_DEPTH:
        return None
    counter[0] += 1
    if counter[0] > _MAX_NODES:
        return None
    if isinstance(payload, str):
        # FairnessGuard decide — sem threshold de tamanho local.
        check: FairnessCheckResult = guard.check(payload)
        if check.is_blocked:
            return RecursiveFairnessResult(
                is_blocked=True,
                offending_field=path or "<root>",
                offending_signal=_truncate(payload),
                category=check.category,
                educational_message=check.educational_message,
                blocked_terms=list(check.blocked_terms or []),
            )
        return None
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            sub_path = f"{path}.{key}" if path else str(key)
            result = _walk(value, guard, sub_path, depth=depth + 1, counter=counter)
            if result is not None:
                return result
        return None
    if isinstance(payload, (list, tuple)) or (
        isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray))
    ):
        for idx, item in enumerate(payload):
            sub_path = f"{path}[{idx}]"
            result = _walk(item, guard, sub_path, depth=depth + 1, counter=counter)
            if result is not None:
                return result
        return None
    # Tipos primitivos não-string (int, float, bool, None, bytes, etc.)
    # não são analisados — FairnessGuard opera sobre texto natural.
    return None


def validate_fairness_recursive(
    payload: Any,
    *,
    guard: FairnessGuard | None = None,
    root_label: str = "",
) -> RecursiveFairnessResult:
    """Varre `payload` (string | Mapping | Sequence) e devolve o primeiro block.

    Args:
        payload: estrutura arbitrária (str, dict, list, tuple, mistos).
        guard: instância de ``FairnessGuard``. Se ``None``, instancia uma nova
            (compatibilidade — calls existentes mantêm o singleton local).
        root_label: rótulo do nó raiz (ex.: ``"value"``, ``"data"``,
            ``"plan_data"``) usado para montar ``offending_field`` legível.

    Returns:
        RecursiveFairnessResult com ``is_blocked=True`` no primeiro flag, ou
        ``is_blocked=False`` se nada foi vetado.
    """
    if guard is None:
        guard = FairnessGuard()
    counter: list[int] = [0]
    result = _walk(payload, guard, root_label, depth=0, counter=counter)
    if result is not None:
        return result
    return RecursiveFairnessResult(is_blocked=False)


__all__ = ["RecursiveFairnessResult", "validate_fairness_recursive"]
