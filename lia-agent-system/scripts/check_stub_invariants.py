#!/usr/bin/env python3
"""Sensor canonical T-12 (V4.0 post-migration): valida que stubs foram removidos de app/domains/
e que app/repositories/ existe como canonical layer.

V4.0 (2026-06-09): migração T14 completa — 30 stub domains removidos de app/domains/,
repositórios movidos para app/repositories/ (canonical flat layer).

Principais invariantes:
  R0: app/repositories/ existe com >= 35 arquivos .py (baseline pós-migração)
  R1: NENHUM domínio com __domain_type__ = "repository_stub" em app/domains/
  R1b: service domains NÃO devem ter domain.py sem promoção formal
  R2: stub novo não pode reaparecer em app/domains/ (ratchet)
  R3: imports antigos app.domains.<stub>.repositories não existem em app/

Stubs removidos (T14 migração):
  admin, admin_settings, agent_memory, approvals, auth, bulk_actions,
  candidate_lists, chat, clients, client_users, company_culture, compliance(*),
  consent(*), data_subject, email_templates, goals, health_check,
  job_vacancies_analytics, journey_mapping, lia_assistant(*), notifications,
  observability, opinions, recruitment_journey, saas_metrics, shared_searches,
  tasks, technical_tests, triagem(*), trust_center, workforce(*)

  (*) repositórios removidos mas domain mantido (tem services/ ou backward-compat alias)

Modo: BLOCKING. Use --warn-only para opt-out legacy.

Uso:
    python scripts/check_stub_invariants.py             # BLOCKING default
    python scripts/check_stub_invariants.py --warn-only # opt-out
"""
from __future__ import annotations

import sys
from pathlib import Path


# Domínios que ERAM stubs e tiveram seus repositórios migrados para app/repositories/
# Mantidos aqui para histórico e verificação R1
MIGRATED_STUB_DOMAINS = {
    "admin", "admin_settings", "agent_memory", "approvals", "auth",
    "bulk_actions", "candidate_lists", "chat", "clients", "client_users",
    "company_culture", "compliance", "consent", "data_subject",
    "email_templates", "goals", "health_check", "job_vacancies_analytics",
    "journey_mapping", "lia_assistant", "notifications", "observability", "opinions",
    "recruitment_journey", "saas_metrics", "shared_searches", "tasks",
    "technical_tests", "triagem", "trust_center", "workforce",
}

# 11 service domains documentados em DOMAIN_CATALOG.md como Service Domains
# (têm services/ com business logic AND repositories/ AND dependencies.py, mas sem domain.py)
SERVICE_DOMAINS = {
    "ai",                       # 29+ files, LLM/RAG infrastructure transversal
    "billing",                  # 6 files, subscription + consumption tracking
    "candidates",               # 14 files, candidate CRUD + enrichment + comparison
    "company",                  # 31 files, company config + workos provisioning
    "credits",                  # 7 files, credit/token consumption tracking
    "integrations_hub",         # 10 files, Google Calendar + MS Graph + Rails adapter
    "interview_intelligence",   # 2026 LOC, bias detection + comparative analysis
    "lgpd",                     # 11 files, LGPD compliance + consent + DSR export
    "modules",                  # 4 files, module gating / feature flags
    "recruitment",              # 24 files, triagem session lifecycle + stages
    "voice",                    # 9 files, voice screening orchestrator
}

# Service domains com perfil agentic latente (futuro backlog F4+)
SERVICE_PROMOTION_CANDIDATES = {
    "interview_intelligence",   # 2026 LOC, bias + analytics — agentic potential
    "voice",                    # 1725 LOC orchestrator — agentic potential
}

# Deprecated domains (T-09 Fase 1+ migration target)
DEPRECATED = {
    "autonomous", "policy",
}

# Minimum expected files in app/repositories/ after migration
REPOSITORIES_MIN_FILES = 35


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    domains_root = repo_root / "app" / "domains"
    repos_root = repo_root / "app" / "repositories"

    violations: list[str] = []

    # R0: app/repositories/ must exist and have expected files
    if not repos_root.exists():
        violations.append(
            f"R0: app/repositories/ não existe! "
            f"Migração T14 incompleta — executar migrate_stubs.py"
        )
    else:
        py_files = [f for f in repos_root.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        if len(py_files) < REPOSITORIES_MIN_FILES:
            violations.append(
                f"R0: app/repositories/ tem apenas {len(py_files)} arquivos .py "
                f"(esperado >= {REPOSITORIES_MIN_FILES}) — migração T14 incompleta?"
            )

    # R1: nenhum domínio com repository_stub marker deve existir em app/domains/
    if domains_root.exists():
        for entry in domains_root.iterdir():
            if not entry.is_dir() or entry.name == "__pycache__":
                continue
            init_py = entry / "__init__.py"
            if init_py.exists() and "repository_stub" in init_py.read_text():
                violations.append(
                    f"R1: {entry.name} ainda tem __domain_type__ = 'repository_stub' — "
                    f"stub não foi removido na migração T14. "
                    f"Remover __init__.py marker ou deletar o domínio."
                )

    # R1b: service domains NÃO devem ter domain.py sem promoção formal
    if domains_root.exists():
        for svc in SERVICE_DOMAINS:
            domain_py = domains_root / svc / "domain.py"
            if domain_py.exists():
                if svc in SERVICE_PROMOTION_CANDIDATES:
                    violations.append(
                        f"R1b: {svc} tem domain.py (promovido?) — "
                        f"remover de SERVICE_DOMAINS e atualizar DOMAIN_CATALOG.md"
                    )
                else:
                    violations.append(
                        f"R1b: {svc} tem domain.py mas NÃO está em SERVICE_PROMOTION_CANDIDATES — "
                        f"adicionar a SERVICE_PROMOTION_CANDIDATES + DOMAIN_CATALOG.md"
                    )

    # R2: novo stub não pode reaparecer em app/domains/ (ratchet anti-regressão)
    known_domains = MIGRATED_STUB_DOMAINS | SERVICE_DOMAINS | DEPRECATED
    if domains_root.exists():
        for entry in domains_root.iterdir():
            if not entry.is_dir() or entry.name in ("__pycache__",):
                continue
            if entry.name in known_domains:
                continue
            # Domínio NOVO (não na lista): verificar se parece stub
            domain_py = entry / "domain.py"
            repos_dir = entry / "repositories"
            init_py = entry / "__init__.py"
            if not domain_py.exists() and repos_dir.exists() and init_py.exists():
                services_dir = entry / "services"
                has_services = services_dir.exists() and any(
                    f.suffix == ".py" and f.name != "__init__.py"
                    for f in services_dir.iterdir()
                    if f.is_file()
                )
                if has_services:
                    violations.append(
                        f"R2: service domain novo `{entry.name}` apareceu sem registro — "
                        f"adicionar a SERVICE_DOMAINS + DOMAIN_CATALOG.md"
                    )
                else:
                    violations.append(
                        f"R2: stub novo `{entry.name}` apareceu em app/domains/ — "
                        f"ANTI-REGRESSÃO T14: repositórios devem ir para app/repositories/, "
                        f"não criar novo stub. "
                        f"Ou adicionar a MIGRATED_STUB_DOMAINS se é domain existente re-criado."
                    )

    # R3: imports antigos app.domains.<stub>.repositories não devem existir em app/ (ratchet)
    # Só checa um subset de arquivos para performance (não inspeciona .venv)
    old_import_violations = []
    scan_dirs = [repo_root / "app", repo_root / "tests", repo_root / "scripts"]
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if str(py_file).startswith(str(repos_root)):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for stub in MIGRATED_STUB_DOMAINS:
                old_path = f"from app.domains.{stub}.repositories."
                if old_path in content:
                    # Ignore docstrings (triple-quoted) - simple heuristic
                    for line in content.splitlines():
                        if old_path in line and not line.strip().startswith(('"""', "'''", "#")):
                            old_import_violations.append(
                                f"R3: {py_file.relative_to(repo_root)}: "
                                f"import antigo `app.domains.{stub}.repositories.*` — "
                                f"reescrever para `app.repositories.*`"
                            )
                            break

    violations.extend(old_import_violations)

    if not violations:
        py_files = list(repos_root.glob("*.py")) if repos_root.exists() else []
        print(
            f"[T-12/T-14 STUB INVARIANTS] OK -- "
            f"app/repositories/ com {len(py_files)} arquivos, "
            f"0 stubs em app/domains/, "
            f"{len(SERVICE_DOMAINS)} service domains registrados"
        )
        return 0

    print(f"[T-12/T-14 STUB INVARIANTS] {len(violations)} violations:")
    for v in violations:
        print(f"  ⚠  {v}")
    print()
    print("CORRECAO canonical:")
    print("  - R0: executar scripts/migrate_stubs.py para criar app/repositories/")
    print("  - R1: remover __domain_type__ = 'repository_stub' do __init__.py ou deletar o stub")
    print("  - R1b: service domain promovido → criar domain.py + atualizar SERVICE_PROMOTION_CANDIDATES")
    print("  - R2: novo domínio deve ir em app/repositories/ + service domain em SERVICE_DOMAINS")
    print("  - R3: reescrever imports para usar app.repositories.*")
    print()
    mode = "WARN-ONLY" if not strict else "BLOCKING"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
