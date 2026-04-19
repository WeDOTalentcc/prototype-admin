"""Smoke test parametrizado para a cadeia de execução do chat unificado.

Para cada (domain, tool) registrado no DomainRegistry, valida que o handler
declarado é resolvível (importável) — isto é, não levanta ModuleNotFoundError
nem AttributeError. Não invoca a função (para evitar side-effects em DB/APIs
externas), apenas verifica que o caminho do handler aponta para um callable
existente.

Falha intencional: se um handler novo for cadastrado apontando para módulo
inexistente, este teste bloqueia o merge.

Backlog (Fase 2/3): estender o teste para invocar cada handler com params
dummy capturando NotImplementedError como "graceful pending" e qualquer outra
exceção como "regression".
"""
from __future__ import annotations

import importlib
from typing import Any

import pytest


def _collect_tools_per_domain() -> list[tuple[str, str, str]]:
    """Returns (domain_id, tool_id, handler_path) for every registered tool."""
    from app.domains.registry import DomainRegistry

    registry = DomainRegistry()
    rows: list[tuple[str, str, str]] = []
    for domain_id in registry.list_domains():
        try:
            tools_module = importlib.import_module(
                f"app.domains.{domain_id}.tools"
            )
        except ImportError:
            continue
        # Cada domínio expõe sua lista de tools com nomes diferentes
        # (JOB_MANAGEMENT_TOOLS, COMMUNICATION_TOOLS, etc.).
        for attr_name in dir(tools_module):
            if not attr_name.endswith("_TOOLS"):
                continue
            tools_list = getattr(tools_module, attr_name)
            if not isinstance(tools_list, list):
                continue
            for tool in tools_list:
                if not isinstance(tool, dict):
                    continue
                tool_id = tool.get("tool_id") or tool.get("id") or "?"
                handler = tool.get("handler")
                if handler:
                    rows.append((domain_id, tool_id, handler))
    return rows


def _resolve_handler(handler_path: str) -> Any:
    """Resolve um handler path no formato `module.func` ou `module.singleton.method`.

    Tenta importar progressivamente caminhos cada vez mais curtos como módulo,
    depois caminha pelos atributos restantes. Levanta AttributeError ou
    ImportError em caso de falha — o teste captura.
    """
    parts = handler_path.split(".")
    last_err: Exception | None = None
    for i in range(len(parts), 0, -1):
        try:
            module = importlib.import_module(".".join(parts[:i]))
        except ImportError as exc:
            last_err = exc
            continue
        obj: Any = module
        try:
            for attr in parts[i:]:
                obj = getattr(obj, attr)
            return obj
        except AttributeError as exc:
            last_err = exc
            continue
    raise (last_err or ImportError(f"Não foi possível resolver: {handler_path}"))


_ROWS = _collect_tools_per_domain()


# Domínios P1 ainda fora de escopo da Fase 1 — esperados como xfail até Fase 2.
P1_DOMAINS_DEFERRED = {
    "ats_integration",
    "automation",
    "cv_screening",
    "interview_scheduling",
    "recruiter_assistant",
}


@pytest.mark.parametrize(
    "domain_id,tool_id,handler",
    _ROWS,
    ids=[f"{d}::{t}" for d, t, _ in _ROWS],
)
def test_chat_tool_handler_resolves(domain_id: str, tool_id: str, handler: str) -> None:
    """Cada handler declarado por um tool de chat deve ser importável."""
    if domain_id in P1_DOMAINS_DEFERRED:
        pytest.xfail(
            f"Domínio P1 ({domain_id}) ainda não saneado — Fase 2 da task #580."
        )

    resolved = _resolve_handler(handler)
    assert callable(resolved), (
        f"Handler {handler!r} para tool {tool_id!r} do domínio {domain_id!r} "
        f"não é callable (resolveu para: {type(resolved).__name__})."
    )


def test_smoke_collected_at_least_50_tools() -> None:
    """Sanity check: a auditoria detectou ~93 tools; o coletor deve achar a maioria."""
    assert len(_ROWS) >= 50, (
        f"Esperado ≥50 tools agregados; coletor achou {len(_ROWS)}. "
        f"Verifique se DomainRegistry está expondo todos os domínios."
    )
