"""Task #977 — Sentinela canônica do `tenant_context_canary.rules.yaml`.

Defesa contra a regressão sinalizada no code review: o alerta warning
DEVE disparar mesmo em evento único de `fail_open` em prod (regressão
silenciosa pode ser uma única request degradada). Quebrar essa
invariante = o alerta vira ruído sem cobertura real.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "observability"
    / "tenant_context_canary.rules.yaml"
)


@pytest.fixture(scope="module")
def rules() -> dict:
    assert RULES_PATH.exists(), f"missing canonical rules file: {RULES_PATH}"
    return yaml.safe_load(RULES_PATH.read_text())


@pytest.fixture(scope="module")
def alerts(rules: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for group in rules.get("groups", []):
        for rule in group.get("rules", []):
            if "alert" in rule:
                out[rule["alert"]] = rule
    return out


def test_three_canonical_alerts_present(alerts: dict[str, dict]) -> None:
    assert {
        "LIATenantContextFailOpen",
        "LIATenantContextFailClosedRate",
        "LIATenantContextAgentSilent24h",
    }.issubset(alerts.keys())


def test_fail_open_fires_on_single_event(alerts: dict[str, dict]) -> None:
    """Code-review fix: single fail_open em prod DEVE alertar.

    Invariantes canônicas:
      - SEM `for:` (ou `for: 0`) — não esperar hold period
      - lookback >= 5m (deixa o ponto único caber na janela)
      - selector restringe a prod-like envs
    """
    rule = alerts["LIATenantContextFailOpen"]
    # Sem hold period — single event aciona imediatamente
    assert "for" not in rule or rule["for"] in ("0", "0s"), (
        "LIATenantContextFailOpen NÃO deve ter `for:` — single fail_open precisa "
        "alertar imediatamente (regressão silenciosa pode ser evento único)."
    )
    expr = rule["expr"]
    assert "[5m]" in expr or "[10m]" in expr, (
        "expr deve usar lookback >= 5m pra capturar evento único antes de aging out"
    )
    assert 'outcome="fail_open"' in expr
    # Prod scoping explícito
    assert "production" in expr and "staging" in expr, (
        "expr deve filtrar por env=~production|prod|staging — alerta é "
        "específico de prod ('em prod NUNCA deveria existir')"
    )
    assert rule["labels"]["severity"] == "warning"


def test_fail_closed_critical_threshold(alerts: dict[str, dict]) -> None:
    rule = alerts["LIATenantContextFailClosedRate"]
    expr = rule["expr"]
    assert 'outcome="fail_closed"' in expr
    assert "rate(" in expr  # taxa, não increase total
    assert "* 60" in expr and "> 5" in expr  # normalização per-min e threshold
    assert rule["labels"]["severity"] == "critical"
    assert rule["labels"].get("page_oncall") == "true"


def test_runbook_label_points_to_canonical_doc(alerts: dict[str, dict]) -> None:
    for name in ("LIATenantContextFailOpen", "LIATenantContextFailClosedRate"):
        assert (
            alerts[name]["labels"]["runbook"] == "missing_tenant_context.md"
        ), f"{name} deve apontar pro runbook canônico T-E"
