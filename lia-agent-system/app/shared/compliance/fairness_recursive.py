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

Contrato canônico (task #1003 spec — mantido estável para os 5 wrappers):

    result = validate_fairness_recursive(payload, guard=_fairness_guard)
    if result.is_blocked:
        return {
            "success": False,
            "reason": "fairness_violation",
            "offending_field": result.offending_field,
            "offending_signal": result.offending_signal,
            "category": result.category,
            "blocked_terms": result.blocked_terms or [],
            "message": result.educational_message,
        }

Sem `len > 10` aqui — quem decide o que é viés é o ``FairnessGuard``, não o
caller (Crença #02 do WeDO + Inegociável #2).
"""
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult

logger = logging.getLogger(__name__)


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
# Os 5 wrappers chamam ``check_payload_limits`` ANTES de qualquer DB call —
# um payload patológico é rejeitado pelo caller (4xx-equivalente). Os
# limites são generosos para tenants reais (workforce com centenas de
# itens passa tranquilo) mas cortam payloads adversariais.
#
# Task #1010 — quando o estouro acontece DENTRO do walk recursivo (porque
# um caller pulou o pre-check), o walk é **fail-OPEN local**: emite
# warning estruturado (tool_name + tenant_id) para SRE, retorna
# `is_blocked=False` e o save segue para auditoria. A camada de cima
# (pre_check no caller + alerta SRE) é quem decide rejeitar; o walk
# nunca silencia, mas também não vira o gatekeeper de abuso (esse papel
# é da rejeição preventiva).
_MAX_DEPTH = 32
_MAX_NODES = 10_000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_SIGNAL_LEN:
        return text
    return text[: _MAX_SIGNAL_LEN - 1] + "…"


def _emit_limit_warning(
    *,
    kind: str,
    path: str,
    tool_name: str | None,
    tenant_id: str | None,
    observed_depth: int | None = None,
    observed_nodes: int | None = None,
    stage: str,
) -> None:
    """Task #1010 — observabilidade quando o orçamento de varredura estoura.

    Emite warning estruturado (compatível com Sentry/log shippers) com
    ``tool_name`` e ``tenant_id`` para que SRE detecte abuso ou um bug
    real (payload genuíno vazando os limites). ``stage`` distingue entre
    ``pre_check`` (rejeição preventiva pelo caller) e ``recursive_walk``
    (defesa em profundidade — só dispara se o pre-check foi pulado).
    """
    logger.warning(
        "[fairness_recursive] payload excedeu limite (%s) — tool=%s tenant=%s stage=%s",
        kind,
        tool_name or "<unknown>",
        tenant_id or "<unknown>",
        stage,
        extra={
            "fairness_recursive_limit_kind": kind,
            "fairness_recursive_max_depth": _MAX_DEPTH,
            "fairness_recursive_max_nodes": _MAX_NODES,
            "fairness_recursive_observed_depth": observed_depth,
            "fairness_recursive_observed_nodes": observed_nodes,
            "fairness_recursive_path": path or "<root>",
            "fairness_recursive_tool": tool_name,
            "fairness_recursive_tenant_id": tenant_id,
            "fairness_recursive_stage": stage,
        },
    )


def _limit_block(
    path: str,
    kind: str,
    *,
    tool_name: str | None = None,
    tenant_id: str | None = None,
    observed_depth: int | None = None,
    observed_nodes: int | None = None,
) -> RecursiveFairnessResult:
    """Task #1010 — fail-OPEN local com warning estruturado.

    Quando o orçamento da varredura estoura DENTRO do walk recursivo
    (caller pulou ``check_payload_limits``), emite warning com
    ``tool_name``/``tenant_id`` e devolve resultado **não-bloqueado**:
    a save tool segue para auditoria normalmente. A defesa real contra
    abuso é o ``check_payload_limits`` no caller (4xx claro) + alerta
    SRE em cima dos warnings agregados — o walk nunca silencia, mas
    também não vira o gatekeeper.
    """
    _emit_limit_warning(
        kind=kind,
        path=path,
        tool_name=tool_name,
        tenant_id=tenant_id,
        observed_depth=observed_depth,
        observed_nodes=observed_nodes,
        stage="recursive_walk",
    )
    return RecursiveFairnessResult(
        is_blocked=False,
        offending_field=path or "<root>",
        offending_signal=f"<payload excedeu {kind}>",
        category="fairness_validation_limit",
        educational_message=(
            "Payload excedeu o orçamento da validação recursiva de viés "
            "(varredura interrompida). Pre-check no caller deveria ter "
            "rejeitado antes — warning estruturado emitido para SRE."
        ),
        blocked_terms=[],
    )


def _walk(
    payload: Any,
    guard: FairnessGuard,
    path: str,
    *,
    depth: int,
    counter: list[int],
    tool_name: str | None = None,
    tenant_id: str | None = None,
) -> Optional[RecursiveFairnessResult]:
    # Task #1010 — fail-OPEN local: estourar o orçamento NÃO bloqueia
    # (a rejeição preventiva é do `check_payload_limits` no caller),
    # mas `_limit_block` emite warning estruturado para SRE — nunca
    # silencia. Crença #02 do WeDO + Inegociável #2 honrados via
    # observabilidade + pre-check 4xx, não via bloqueio cego.
    if depth > _MAX_DEPTH:
        return _limit_block(
            path,
            f"profundidade máxima ({_MAX_DEPTH})",
            tool_name=tool_name,
            tenant_id=tenant_id,
            observed_depth=depth,
            observed_nodes=counter[0],
        )
    counter[0] += 1
    if counter[0] > _MAX_NODES:
        return _limit_block(
            path,
            f"limite de nós ({_MAX_NODES})",
            tool_name=tool_name,
            tenant_id=tenant_id,
            observed_depth=depth,
            observed_nodes=counter[0],
        )
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
            # Validar a CHAVE também — bypass clássico era usar o nome
            # da chave como veículo de viés (ex.:
            # `default_salary_ranges = {"Junior Homem": "5k"}`).
            if isinstance(key, str):
                key_path = f"{path}.<key:{key}>" if path else f"<key:{key}>"
                key_check: FairnessCheckResult = guard.check(key)
                if key_check.is_blocked:
                    return RecursiveFairnessResult(
                        is_blocked=True,
                        offending_field=key_path,
                        offending_signal=_truncate(key),
                        category=key_check.category,
                        educational_message=key_check.educational_message,
                        blocked_terms=list(key_check.blocked_terms or []),
                    )
            sub_path = f"{path}.{key}" if path else str(key)
            result = _walk(
                value, guard, sub_path,
                depth=depth + 1, counter=counter,
                tool_name=tool_name, tenant_id=tenant_id,
            )
            if result is not None:
                return result
        return None
    if isinstance(payload, (list, tuple)) or (
        isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray))
    ):
        for idx, item in enumerate(payload):
            sub_path = f"{path}[{idx}]"
            result = _walk(
                item, guard, sub_path,
                depth=depth + 1, counter=counter,
                tool_name=tool_name, tenant_id=tenant_id,
            )
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
    tool_name: str | None = None,
    tenant_id: str | None = None,
) -> RecursiveFairnessResult:
    """Varre `payload` (string | Mapping | Sequence) e devolve o primeiro block.

    Args:
        payload: estrutura arbitrária (str, dict, list, tuple, mistos).
        guard: instância de ``FairnessGuard``. Se ``None``, instancia uma nova
            (compatibilidade — calls existentes mantêm o singleton local).
        root_label: rótulo do nó raiz (ex.: ``"value"``, ``"data"``,
            ``"plan_data"``) usado para montar ``offending_field`` legível.
        tool_name: identificador da tool chamadora (ex.: ``"save_company_field"``).
            Task #1010 — usado no warning estruturado emitido por
            ``_emit_limit_warning`` quando os limites de DoS estouram.
        tenant_id: ``company_id`` do tenant atual. Mesma rationale do
            ``tool_name`` — permite SRE detectar abuso por tenant.

    Returns:
        RecursiveFairnessResult com ``is_blocked=True`` no primeiro flag, ou
        ``is_blocked=False`` se nada foi vetado.
    """
    if guard is None:
        guard = FairnessGuard()
    counter: list[int] = [0]
    result = _walk(
        payload, guard, root_label,
        depth=0, counter=counter,
        tool_name=tool_name, tenant_id=tenant_id,
    )
    if result is not None:
        return result
    return RecursiveFairnessResult(is_blocked=False)


# ────────────────────────────────────────────────────────────────────────────
# Task #1010 — Pre-check de tamanho de payload para uso pelos callers HTTP/
# agent. Roda ANTES de ``validate_fairness_recursive`` para que payloads
# patológicos sejam rejeitados com 4xx claro (em vez de degradarem ao
# walk recursivo, agora fail-OPEN local + warning). Quando rejeita, emite o mesmo
# warning estruturado de ``_emit_limit_warning`` — então qualquer estouro
# (pre_check OU recursive_walk) gera observabilidade idêntica.
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class PayloadLimitReport:
    """Resultado do pre-check de tamanho. ``exceeded=True`` significa que o
    payload deve ser rejeitado pelo caller antes de chegar ao DB."""

    exceeded: bool
    kind: Optional[str] = None  # "depth" | "nodes"
    observed_depth: int = 0
    observed_nodes: int = 0


def _measure_payload(payload: Any) -> PayloadLimitReport:
    """Medição iterativa (sem recursão Python) de profundidade + nós.

    Faz early-exit assim que ``_MAX_DEPTH`` ou ``_MAX_NODES`` é estourado
    para que o custo do pre-check seja proporcional aos limites, não ao
    payload (defesa contra DoS no próprio measure).
    """
    nodes = 0
    max_depth_seen = 0
    stack: list[tuple[Any, int]] = [(payload, 0)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if depth > max_depth_seen:
            max_depth_seen = depth
        if depth > _MAX_DEPTH:
            return PayloadLimitReport(
                exceeded=True, kind="depth",
                observed_depth=depth, observed_nodes=nodes,
            )
        if nodes > _MAX_NODES:
            return PayloadLimitReport(
                exceeded=True, kind="nodes",
                observed_depth=max_depth_seen, observed_nodes=nodes,
            )
        if isinstance(item, str):
            continue
        if isinstance(item, Mapping):
            for k, v in item.items():
                stack.append((v, depth + 1))
            continue
        if isinstance(item, (list, tuple)) or (
            isinstance(item, Sequence)
            and not isinstance(item, (str, bytes, bytearray))
        ):
            for v in item:
                stack.append((v, depth + 1))
    return PayloadLimitReport(
        exceeded=False,
        observed_depth=max_depth_seen, observed_nodes=nodes,
    )


def check_payload_limits(
    payload: Any,
    *,
    tool_name: str,
    tenant_id: str | None,
) -> Optional[dict[str, Any]]:
    """Caller-side guard: retorna payload de rejeição (4xx-equivalente) se o
    payload estourar profundidade/quantidade máxima; ``None`` caso contrário.

    Quando rejeita, emite warning estruturado via ``_emit_limit_warning``
    com ``stage="pre_check"`` para que SRE observe abuso/bug genuíno
    (ver Task #1010).

    Os 5 wrappers de save em ``company_settings`` (``save_company_field``,
    ``save_company_section``, ``save_hiring_policy``,
    ``import_workforce_plan``, ``import_benefits_from_data``) chamam isso
    antes de qualquer leitura de DB.
    """
    report = _measure_payload(payload)
    if not report.exceeded:
        return None

    _emit_limit_warning(
        kind=report.kind or "unknown",
        path="<payload>",
        tool_name=tool_name,
        tenant_id=tenant_id,
        observed_depth=report.observed_depth,
        observed_nodes=report.observed_nodes,
        stage="pre_check",
    )
    if report.kind == "depth":
        detail = (
            f"profundidade máxima excedida (limite={_MAX_DEPTH}, "
            f"observado={report.observed_depth})"
        )
    else:
        detail = (
            f"limite de nós excedido (limite={_MAX_NODES}, "
            f"observado={report.observed_nodes})"
        )
    return {
        "success": False,
        "reason": "payload_too_large",
        "limit_kind": report.kind,
        "max_depth": _MAX_DEPTH,
        "max_nodes": _MAX_NODES,
        "observed_depth": report.observed_depth,
        "observed_nodes": report.observed_nodes,
        "message": (
            f"Payload muito grande para validação de viés ({detail}). "
            "Envie em lotes menores e tente novamente."
        ),
    }


__all__ = [
    "RecursiveFairnessResult",
    "PayloadLimitReport",
    "validate_fairness_recursive",
    "check_payload_limits",
]
