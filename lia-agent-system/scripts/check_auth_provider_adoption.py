#!/usr/bin/env python3
"""Sensor canonical: adoção de get_auth_context_dependency nos routers de sub-apps.

Contexto (Sprint G7 — 2026-06-13):
  app/shared/auth/auth_provider.py criou AuthContext + get_auth_context_dependency().
  Os sub-apps (api-onboarding, api-funil, api-vagas) importam routers de app/api/v1/.
  Esses routers ainda usam get_current_active_user / get_current_user de app.auth.dependencies.

O que este sensor detecta:
  1. Endpoints em app/api/v1/ que usam auth legada via Depends(...):
       Depends(get_current_active_user)
       Depends(get_current_user)
       Depends(get_current_user_strict)
       Depends(get_current_user_or_demo)
  2. Agrupa por sub-app (onboarding / funil / vagas) com base nos routers incluídos.

Mapeamento canonical sub-app → módulos de router:
  Derivado dos main.py de cada sub-app em apps/.

Modo: WARN-ONLY por default (baseline alto — migração gradual).
     --block: exit 1 se violations > 0.
     --subapp <nome>: filtra por sub-app específico.

Uso:
    python scripts/check_auth_provider_adoption.py
    python scripts/check_auth_provider_adoption.py --block
    python scripts/check_auth_provider_adoption.py --subapp vagas
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import NamedTuple

# ─────────────────────────────────────────────────────────────────────────────
# Mapeamento sub-app → prefixos de módulo de router
# Extraído dos main.py em apps/api-*/main.py (imports from app.api.v1.*)
# ─────────────────────────────────────────────────────────────────────────────
SUBAPP_MODULE_PREFIXES: dict[str, list[str]] = {
    "onboarding": [
        "app/api/v1/auth",
        "app/api/v1/workos",
        "app/api/v1/company",
        "app/api/v1/company_culture",
        "app/api/v1/company_benefits",
        "app/api/v1/workforce",
        "app/api/v1/goals",
        "app/api/v1/benefits",
        "app/api/v1/admin",
        "app/api/v1/admin_settings",
        "app/api/v1/admin_templates",
        "app/api/v1/settings_progress",
        "app/api/v1/integrations_hub",
        "app/api/v1/integrations",
        "app/api/v1/billing",
        "app/api/v1/clients",
        "app/api/v1/client_users",
        "app/api/v1/notifications",
        "app/api/v1/communication_settings",
        "app/api/v1/email_templates",
        "app/api/v1/default_templates",
        "app/api/v1/global_policies",
        "app/api/v1/lgpd_compliance",
        "app/api/v1/compliance_controls",
        "app/api/v1/trust_center",
        "app/api/v1/audit_logs",
        "app/api/v1/data_subject_requests",
        "app/api/v1/consent_management",
        "app/api/v1/data_request",
        "app/api/v1/microsoft_graph",
        "app/api/v1/merge_webhooks",
        "app/api/v1/external_webhooks",
        "app/api/v1/saas_metrics",
        "app/api/v1/ai_consumption",
        "app/api/v1/observability",
        "app/api/v1/audit_timeline",
    ],
    "funil": [
        "app/api/v1/pipeline",
        "app/api/v1/pipeline_templates",
        "app/api/v1/pipeline_velocity",
        "app/api/v1/pipeline_prediction",
        "app/api/v1/pipeline_policy",
        "app/api/v1/pipeline_orchestrator",
        "app/api/v1/stage_transition_automation",
        "app/api/v1/candidates",
        "app/api/v1/candidate_search",
        "app/api/v1/candidate_lists",
        "app/api/v1/applications",
        "app/api/v1/sourcing",
        "app/api/v1/sourcing_pipeline",
        "app/api/v1/sourcing_orchestrator",
        "app/api/v1/kanban_assistant",
        "app/api/v1/recruitment_stages",
        "app/api/v1/screening",
        "app/api/v1/screening_questions",
        "app/api/v1/talent_funnel",
        "app/api/v1/calibration",
        "app/api/v1/affirmative",
        "app/api/v1/early_warning",
        "app/api/v1/journey_intelligence",
        "app/api/v1/predictive_analytics",
        "app/api/v1/interview_analysis",
        "app/api/v1/interviews",
        "app/api/v1/cv_parser",
        "app/api/v1/bulk_actions",
        "app/api/v1/activities",
        "app/api/v1/audit_timeline",
    ],
    "vagas": [
        "app/api/v1/job_vacancies",
        "app/api/v1/job_drafts",
        "app/api/v1/job_board",
        "app/api/v1/job_status_webhooks",
        "app/api/v1/job_analytics",
        "app/api/v1/job_learning",
        "app/api/v1/job_templates",
        "app/api/v1/job_embeddings",
        "app/api/v1/job_qualification",
        "app/api/v1/jobs_ws",
        "app/api/v1/jd_import",
        "app/api/v1/jd_generation",
        "app/api/v1/wizard_analytics",
        "app/api/v1/wizard_suggestions",
        "app/api/v1/wizard_smart_orchestrator",
        "app/api/v1/wsi",
        "app/api/v1/wsi_questions",
        "app/api/v1/wsi_question_adjust",
        "app/api/v1/wsi_observability",
        "app/api/v1/wsi_screening_pipeline_endpoint",
        "app/api/v1/orchestrated_job_chat",
        "app/api/v1/orchestrated_jobs_management",
        "app/api/v1/briefing",
        "app/api/v1/hiring_policy",
        "app/api/v1/audit_timeline",
    ],
}

# Auth legada — dependências que deveriam ser migradas para AuthContext
LEGACY_AUTH_DEPENDS = {
    "get_current_active_user",
    "get_current_user",
    "get_current_user_strict",
    "get_current_user_or_demo",
}

# Novos endpoints DEVEM usar:
CANONICAL_DEPENDS = "get_auth_context_dependency"


class Violation(NamedTuple):
    subapp: str
    filepath: str
    lineno: int
    func_name: str
    legacy_dep: str
    message: str


def _file_to_subapp(rel_path: str) -> str | None:
    """Mapeia caminho de arquivo para sub-app correspondente."""
    # Normaliza separadores
    rel_normalized = rel_path.replace("\\", "/")
    for subapp, prefixes in SUBAPP_MODULE_PREFIXES.items():
        for prefix in prefixes:
            if rel_normalized.startswith(prefix + "/") or rel_normalized == prefix + ".py":
                return subapp
    return None


def _extract_legacy_depends(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Extrai nomes de dependências legadas do cabeçalho de função."""
    found = []
    for arg in func_node.args.args + func_node.args.kwonlyargs:
        default_nodes = func_node.args.defaults + func_node.args.kw_defaults
        # Também verifica as anotações padrão de Depends
        pass

    # Verifica defaults
    all_defaults = list(func_node.args.defaults) + list(func_node.args.kw_defaults)
    for default in all_defaults:
        if default is None:
            continue
        # Depends(get_current_active_user) → ast.Call com func=Depends e args=[Name]
        if isinstance(default, ast.Call):
            func = default.func
            func_name = None
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            if func_name == "Depends" and default.args:
                dep_arg = default.args[0]
                dep_name = None
                if isinstance(dep_arg, ast.Name):
                    dep_name = dep_arg.id
                elif isinstance(dep_arg, ast.Attribute):
                    dep_name = dep_arg.attr

                if dep_name and dep_name in LEGACY_AUTH_DEPENDS:
                    found.append(dep_name)
    return found


def scan_file(py_file: Path, repo_root: Path) -> list[tuple[str, int, str, str]]:
    """
    Retorna lista de (rel_path, lineno, func_name, legacy_dep).
    """
    results = []
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return results

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            legacy_deps = _extract_legacy_depends(node)
            for dep in legacy_deps:
                rel_path = str(py_file.relative_to(repo_root))
                results.append((rel_path, node.lineno, node.name, dep))

    return results


def run(filter_subapp: str | None = None) -> list[Violation]:
    repo_root = Path(__file__).resolve().parent.parent
    api_v1_dir = repo_root / "app" / "api" / "v1"

    violations: list[Violation] = []
    scanned_files = 0

    for py_file in sorted(api_v1_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue

        rel_path = str(py_file.relative_to(repo_root))
        subapp = _file_to_subapp(rel_path)

        if subapp is None:
            continue  # módulo compartilhado, não pertence a sub-app específico

        if filter_subapp and subapp != filter_subapp:
            continue

        scanned_files += 1
        file_results = scan_file(py_file, repo_root)

        for (fp, lineno, func_name, legacy_dep) in file_results:
            violations.append(
                Violation(
                    subapp=subapp,
                    filepath=fp,
                    lineno=lineno,
                    func_name=func_name,
                    legacy_dep=legacy_dep,
                    message=(
                        f"[{fp}:{lineno}] {func_name}() usa Depends({legacy_dep}) "
                        f"→ Migrar para: auth: AuthContext = Depends(get_auth_context_dependency())"
                    ),
                )
            )

    return violations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sensor: adoção de get_auth_context_dependency nos routers de sub-apps"
    )
    parser.add_argument("--block", action="store_true", help="Exit 1 se violations > 0")
    parser.add_argument("--subapp", choices=["onboarding", "funil", "vagas"], help="Filtrar por sub-app")
    parser.add_argument("--json", action="store_true", help="Output em JSON para CI tooling")
    args = parser.parse_args()

    violations = run(filter_subapp=args.subapp)

    # Agrupa por sub-app para relatório estruturado
    by_subapp: dict[str, list[Violation]] = {}
    for v in violations:
        by_subapp.setdefault(v.subapp, []).append(v)

    if args.json:
        import json
        print(json.dumps({
            "total": len(violations),
            "by_subapp": {
                subapp: [
                    {"file": v.filepath, "line": v.lineno, "func": v.func_name, "dep": v.legacy_dep}
                    for v in vlist
                ]
                for subapp, vlist in sorted(by_subapp.items())
            },
        }, indent=2))
        sys.exit(1 if (args.block and violations) else 0)

    if not violations:
        print("[AUTH-ADOPTION] OK -- 0 endpoints com auth legada nos routers de sub-apps")
        sys.exit(0)

    # Relatório human/LLM-friendly
    print(f"[AUTH-ADOPTION] {len(violations)} endpoints com auth legada nos routers de sub-apps")
    print()

    for subapp in sorted(by_subapp.keys()):
        vlist = by_subapp[subapp]
        print(f"  📦 api-{subapp}: {len(vlist)} endpoints")
        for v in vlist[:10]:  # max 10 por sub-app para não poluir
            print(f"    {v.message}")
        if len(vlist) > 10:
            print(f"    ... e mais {len(vlist) - 10} endpoints (use --subapp {subapp} para ver todos)")
        print()

    print("─" * 72)
    print("GUIA DE MIGRAÇÃO (novos endpoints):")
    print()
    print("  # ANTES (legado — NÃO usar em novos endpoints):")
    print("  async def meu_endpoint(")
    print("      current_user: User = Depends(get_current_active_user),")
    print("  ):")
    print()
    print("  # DEPOIS (canonical — usar em todos os novos endpoints):")
    print("  from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency")
    print()
    print("  async def meu_endpoint(")
    print("      auth: AuthContext = Depends(get_auth_context_dependency()),")
    print("  ):")
    print("      user = auth.user")
    print("      company_id = auth.company_id")
    print()
    print("NOTA: Endpoints legados existentes são PERM-EXEMPT — NÃO migrar em massa.")
    print("      Apenas novos endpoints devem usar get_auth_context_dependency().")
    print()
    print(f"Modo: WARN-ONLY. Use --block para modo bloqueante (CI).")

    sys.exit(1 if args.block else 0)


if __name__ == "__main__":
    main()
