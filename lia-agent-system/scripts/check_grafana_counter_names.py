#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-029 (2026-05-23)

Verifica que todos os Prometheus counter names referenciados em
`observability/grafana/*.json` dashboards EXISTEM como Counter() / Histogram()
declarações no código Python.

Pattern violação:
- Adicionar query Grafana para counter `lia_xxx_total` mas esquecer de criar
  o Counter() correspondente em código → dashboard fica permanentemente vazio
- Renomear counter no código sem atualizar dashboard JSON → drift silent

Mensagem PT-BR + fix sugerido em sintaxe exata (harness pattern CLAUDE.md).
Modo: BLOCKING por default · --warn-only opt-out.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W3-029).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAFANA_DIR = REPO_ROOT / "observability" / "grafana"
APP_DIR = REPO_ROOT / "app"
LIBS_DIR = REPO_ROOT / "libs"

# Pattern dos counter names do projeto LIA
COUNTER_NAME_RE = re.compile(r"\blia_[a-z_]+_(?:total|count|sum|bucket)\b")
# Pattern dos counter names declarados:
# (a) Counter("lia_xxx_total", ...) — direct constructor
# (b) _METRIC_NAME = "lia_xxx_total" / METRIC_NAME = "..." — constant pattern
#     (canonical em app/jobs/tenant_aware_task.py, app/shared/admin/cross_tenant_session.py,
#      app/shared/security/{require_company_id,webhook_ownership}.py)
DECL_RE = re.compile(
    r'(?:Counter|Histogram|Gauge|Summary)\s*\(\s*["\']([^"\']+)["\']'
    r'|_METRIC_NAME\s*[:=]\s*["\']([^"\']+)["\']'
    r'|METRIC_NAME\s*[:=]\s*["\']([^"\']+)["\']'
)


def extract_grafana_metric_names() -> set[str]:
    """Extract metric names referenced in any Grafana dashboard JSON expr."""
    metrics: set[str] = set()
    if not GRAFANA_DIR.exists():
        return metrics
    for jf in GRAFANA_DIR.rglob("*.json"):
        try:
            text = jf.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for match in COUNTER_NAME_RE.finditer(text):
            metrics.add(match.group(0))
    return metrics


def extract_declared_metric_names() -> set[str]:
    """Extract metric names declared via Counter()/Histogram() in Python code."""
    declared: set[str] = set()
    for root in (APP_DIR, LIBS_DIR):
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                src = py.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for match in DECL_RE.finditer(src):
                # 3 groups: (Counter ctor), (_METRIC_NAME =), (METRIC_NAME =)
                # exatamente 1 grupo é não-None per match
                name = match.group(1) or match.group(2) or match.group(3)
                if name and name.startswith("lia_"):
                    declared.add(name)
    return declared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    grafana = extract_grafana_metric_names()
    declared = extract_declared_metric_names()

    if not grafana:
        print("✅ Grafana dashboards · 0 referenciados (skipped)")
        return 0

    missing_in_code = grafana - declared
    if missing_in_code:
        print(
            f"W3-029 grafana counter drift · {len(missing_in_code)} metric(s) "
            f"referenciado(s) no Grafana mas NÃO declarado(s) em código:",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for name in sorted(missing_in_code):
            print(f"  ❌ {name}", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "FIX: declarar Counter()/Histogram() no código OU remover query do dashboard.\n"
            "Exemplo:\n"
            "    from prometheus_client import Counter\n"
            "    my_counter = Counter(\"lia_my_metric_total\", \"Description\")\n",
            file=sys.stderr,
        )
        if args.warn_only:
            return 0
        return 1

    print(
        f"✅ Grafana counter coherence (W3-029) · "
        f"{len(grafana)} grafana metrics todos declarados em código"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
