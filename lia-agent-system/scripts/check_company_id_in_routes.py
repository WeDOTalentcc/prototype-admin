#!/usr/bin/env python3
"""AST sensor — every FastAPI route in app/api/v1/ must reference a canonical
multi-tenancy gate within its signature/body.

Multi-tenancy is the most important invariant in this codebase. CLAUDE.md
makes it golden rule #1. This script walks every Python file under
app/api/v1/, finds @router.{get,post,put,patch,delete} decorated functions,
and asserts each function references at least one of the canonical
multi-tenancy gate functions.

Canonical gates (CLAUDE.md REGRA 6 + ADR multi-tenancy):
  - require_company_id              (Depends — JWT-authoritative)
  - require_company_id_strict_match (Depends factory — 403 se header/query != JWT)
  - get_verified_company_id         (tenant_guard — defense-in-depth)
  - _require_company_id             (helper interno)
  - get_user_company_id             (helper de resolução por user)
  - _assert_tenant_scope            (assert pós-load do recurso)

Exit code (RATCHET):
  0 — offenders <= BASELINE (no regression)
  1 — offenders >  BASELINE (new untenanted route introduced)  OR  --strict

O ratchet impede REGRESSAO: qualquer rota nova sem gate canonico falha o CI.
Os offenders legados (BASELINE) sao debito documentado — triagem em backlog
separado (auth/* endpoints pre-tenant + catalogos globais WeDOTalent sao
falsos positivos legitimos; candidates_crud/stages_* sao gaps reais).

Para baixar o baseline conforme o debito e pago, ajuste BASELINE_OFFENDERS.

Usage:
  python scripts/check_company_id_in_routes.py            # ratchet (default)
  python scripts/check_company_id_in_routes.py --strict   # zero-tolerance
  python scripts/check_company_id_in_routes.py --list      # lista todos offenders

Allowlist por rota:
  Adicione  no corpo da funcao para rotas que
  intencionalmente NAO escopam por company_id (login, webhooks resolvidos por
  assinatura de payload, catalogos globais da plataforma).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1] / "app" / "api" / "v1"

# Conjunto canonico completo de gates multi-tenancy (CLAUDE.md REGRA 6).
# Inclui as funcoes Depends, o factory strict-match e os asserts pos-load.
GATE_FUNCS = {
    "_require_company_id",
    "get_user_company_id",
    "require_company_id",
    "require_company_id_strict_match",
    "get_verified_company_id",
    "_assert_tenant_scope",
}
OPT_OUT_MARKER = "# multi-tenancy:"

# Baseline honesto medido 2026-05-29 com o conjunto canonico completo de gates + deteccao
# correta de Depends(gate) por ast.Name (fix do falso positivo massivo 224->33).
# 33 offenders legados = majoritariamente falsos positivos legitimos:
#   - auth.py (13): login/register/refresh/password/verify/invitation -> pre-tenant
#     (sem JWT company ainda); deveriam receber marker `# multi-tenancy: pre-auth`.
#   - webhooks (email_tracking, mailgun, openmic, whatsapp, twilio_voice): resolvidos
#     por assinatura/provider, nao JWT -> marker `# multi-tenancy: webhook-signature`.
#   - self_scheduling_public: candidate-facing por token publico.
# Triagem Fase 2.5 (2026-05-29): os 3 "gaps reais" suspeitos eram falsos positivos
#   ja-protegidos -> marcados com `# multi-tenancy:`:
#   - wsi/reports.py get_wsi_audit_trail: tenant-scoped via validate_company_access +
#     deny-by-default (Task #511 r3); cross-tenant INTENCIONAL p/ wedotalent_admin
#     (EU AI Act Art. 12). Gate nao estava em GATE_FUNCS -> false positive.
#   - admin_persona.py get_contract_version: retorna constante estatica, zero dado de
#     tenant, gated por require_wedotalent_admin.
#   - custom_agents.py get_agent_kpis: ja usa require_company_id (aliased
#     _require_company_id_onda4) + filtro company_id + 404 cross-tenant (Onda 4).
# Remanescentes (30) sao FPs legitimos em auth/webhooks/self_scheduling_public,
#   fora do escopo deste agente (ownership) -> backlog de marker dedicado.
# RATCHET: qualquer rota nova sem gate canonico empurra acima de 30 e falha o CI.
BASELINE_OFFENDERS = 30


def is_router_decorator(decorator: ast.expr) -> bool:
    """Match @router.get / @router.post / etc."""
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Attribute):
        return (
            isinstance(decorator.value, ast.Name)
            and decorator.value.id == "router"
            and decorator.attr in {"get", "post", "put", "patch", "delete"}
        )
    return False


def function_calls_gate(func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """True iff the function references a canonical gate anywhere.

    Detecta tanto chamadas diretas (``require_company_id(...)``) quanto
    referencias por nome usadas como dependencia FastAPI
    (``Depends(require_company_id)`` -- onde o gate e um ``ast.Name``
    argumento de ``Depends``, NAO o ``.func`` da call). O sensor antigo so
    olhava ``node.func`` e gerava falso positivo massivo em rotas que se
    gateavam corretamente via ``Depends(...)`` na assinatura.
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Name) and node.id in GATE_FUNCS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in GATE_FUNCS:
            return True
    return False


def function_has_opt_out(source: str, func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """Look for the # multi-tenancy: marker in the lines spanning the function."""
    lines = source.splitlines()
    start = func.lineno - 1
    end = (func.end_lineno or func.lineno)
    body = "\n".join(lines[start:end])
    return OPT_OUT_MARKER in body


def iter_routes(py_path: Path) -> Iterator[tuple[str, ast.AsyncFunctionDef | ast.FunctionDef]]:
    source = py_path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"WARN: syntax error in {py_path}: {e}", file=sys.stderr)
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            for dec in node.decorator_list:
                if is_router_decorator(dec):
                    yield (source, node)


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 1

    offenders: list[tuple[Path, str, int]] = []
    files_scanned = 0
    routes_checked = 0

    for py in ROOT.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        files_scanned += 1
        for source, func in iter_routes(py):
            routes_checked += 1
            if function_calls_gate(func):
                continue
            if function_has_opt_out(source, func):
                continue
            offenders.append((py.relative_to(ROOT.parent.parent.parent), func.name, func.lineno))

    print(f"Scanned {files_scanned} file(s), {routes_checked} route(s).")

    is_strict = "--strict" in sys.argv
    do_list = "--list" in sys.argv
    n = len(offenders)

    if do_list or n > BASELINE_OFFENDERS or is_strict:
        for path, name, line in offenders:
            print(
                f"  {path}:{line}  {name}()  — call require_company_id / "
                "get_verified_company_id / _assert_tenant_scope, or add "
                " comment if intentional.",
                file=sys.stderr,
            )

    if is_strict:
        if n:
            print(f"\nFAIL (--strict) — {n} route(s) missing canonical multi-tenancy gate.", file=sys.stderr)
            return 1
        print("OK (--strict) — every route is multi-tenant guarded.")
        return 0

    # RATCHET mode (default).
    if n > BASELINE_OFFENDERS:
        print(
            f"\nFAIL — {n} route(s) sem gate canonico, acima do baseline {BASELINE_OFFENDERS}.\n"
            f"  Uma rota NOVA foi adicionada sem gate multi-tenancy.\n"
            f"  Fix: adicione  (do JWT, NUNCA do payload),\n"
            f"       ou  se a rota e intencionalmente global.",
            file=sys.stderr,
        )
        return 1

    if n < BASELINE_OFFENDERS:
        print(
            f"\n✅ {n} offender(s) — ABAIXO do baseline {BASELINE_OFFENDERS}. "
            f"Debito pago! Atualize BASELINE_OFFENDERS = {n} no sensor para travar o ganho."
        )
        return 0

    print(
        f"\n⚠️  {n} offender(s) legados == baseline {BASELINE_OFFENDERS} (debito documentado, sem regressao). "
        f"Use --list para inspecionar, --strict para zero-tolerance."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
