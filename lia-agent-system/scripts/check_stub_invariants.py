#!/usr/bin/env python3
"""Sensor canonical T-12 (V3.1 reclassificação): valida 30 stubs thin-CRUD + 11 service domains.

V3 D2 original disse "deletar 10 stubs". Audit Fase A revelou que todos 10
têm endpoints v1 ATIVOS em produção (~110 rotas, 7000+ LOC). Reclassificação:

- DELETE candidates → "DESCONTINUE-FEATURE-FIRST" (não delete imediato)
- Os 30 são pattern intencional thin-CRUD com dependency injection canonical
- 5 high-value candidatos a promoção (auth, chat, notifications, consent, data_subject)
- Sensor valida invariantes: stub mantém shape canonical, sem domain.py drift

Sprint 8 Frente C (2026-05-21): adicionado SERVICE_DOMAINS canonical (11 domains
com services/ + repositories/ mas sem domain.py — categoria distinta de stub_repository).
Sensor promovido WARN-ONLY → BLOCKING [PROMOTED Sprint 8 Frente C].

Modo: BLOCKING [PROMOTED Sprint 8 Frente C]. Use --warn-only para opt-out legacy.

Uso:
    python scripts/check_stub_invariants.py             # BLOCKING default
    python scripts/check_stub_invariants.py --warn-only # opt-out para ratchet
"""
from __future__ import annotations

import sys
from pathlib import Path


# Os 30 stubs documentados em DOMAIN_CATALOG.md como repository stubs
# (apenas __init__.py + dependencies.py + repositories/ — sem services/ com business logic)
STUB_DOMAINS = {
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
# Categoria distinta de stub_repository: não são pure CRUD — têm domain services próprios.
# Registrados Sprint 8 Frente C (2026-05-21).
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

# 5 high-value candidatos a promoção (futuro, não Sprint atual)
PROMOTION_CANDIDATES = {
    "auth", "chat", "notifications", "consent", "data_subject",
}

# Service domains com perfil agentic latente (futuro backlog F4+)
# Critério: > 1500 LOC business logic + uso cross-domain + lógica não-trivial
SERVICE_PROMOTION_CANDIDATES = {
    "interview_intelligence",   # 2026 LOC, bias + analytics — agentic potential
    "voice",                    # 1725 LOC orchestrator — agentic potential
}

# 2 deprecated (T-09 Fase 1+ migration target)
DEPRECATED = {
    "autonomous", "policy",
}


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    domains_root = repo_root / "app" / "domains"

    if not domains_root.exists():
        print("[T-12 STUB INVARIANTS] domains/ não existe — skip")
        return 0

    violations: list[str] = []

    # R1: stubs NÃO devem ter domain.py (se tiverem, foram promovidos sem update aqui)
    for stub in STUB_DOMAINS:
        domain_py = domains_root / stub / "domain.py"
        if domain_py.exists():
            if stub in PROMOTION_CANDIDATES:
                violations.append(
                    f"R1: {stub} tem domain.py (promovido?) — "
                    f"remover de STUB_DOMAINS e atualizar DOMAIN_CATALOG.md"
                )
            else:
                violations.append(
                    f"R1: {stub} tem domain.py mas NÃO está em PROMOTION_CANDIDATES — "
                    f"adicionar a PROMOTION_CANDIDATES + DOMAIN_CATALOG.md"
                )

    # R1b: service domains tampouco devem ter domain.py sem promoção formal
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

    # R2: stub novo apareceu fora da lista?
    known_domains = STUB_DOMAINS | SERVICE_DOMAINS | DEPRECATED
    if domains_root.exists():
        for entry in domains_root.iterdir():
            if entry.is_dir() and entry.name not in ("__pycache__",):
                # É um stub se NÃO tem domain.py + tem repositories/
                domain_py = entry / "domain.py"
                repos_dir = entry / "repositories"
                init_py = entry / "__init__.py"
                if (
                    not domain_py.exists()
                    and repos_dir.exists()
                    and init_py.exists()
                    and entry.name not in known_domains
                ):
                    # Distingue stub (sem services/) vs service domain (com services/)
                    services_dir = entry / "services"
                    has_services = services_dir.exists() and any(
                        f.name != "__init__.py" and f.suffix == ".py"
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
                            f"R2: stub novo `{entry.name}` apareceu sem registro — "
                            f"adicionar a STUB_DOMAINS ou DOMAIN_CATALOG.md"
                        )

    # R3: deprecated não pode crescer
    for dep in DEPRECATED:
        dep_dir = domains_root / dep
        if dep_dir.exists():
            # Conta novos files .py adicionados (heurística simples)
            new_files = list(dep_dir.rglob("*.py"))
            # Não temos baseline — apenas existência hoje
            # Sensor real precisaria baseline. Por enquanto só skip.
            pass

    if not violations:
        print(
            f"[T-12 STUB INVARIANTS] OK -- {len(STUB_DOMAINS)} stubs canonical + "
            f"{len(SERVICE_DOMAINS)} service domains + "
            f"{len(PROMOTION_CANDIDATES)} promotion candidates + "
            f"{len(SERVICE_PROMOTION_CANDIDATES)} service promotion candidates documentados"
        )
        return 0

    print(f"[T-12 STUB INVARIANTS] {len(violations)} violations:")
    for v in violations:
        print(f"  ⚠  {v}")
    print()
    print("CORRECAO canonical:")
    print("  - stub novo (sem services/): adicionar a STUB_DOMAINS em scripts/check_stub_invariants.py")
    print("  - service domain novo (com services/): adicionar a SERVICE_DOMAINS")
    print("  - stub promovido: criar domain.py + adicionar a PROMOTION_CANDIDATES")
    print("  - service promovido: criar domain.py + adicionar a SERVICE_PROMOTION_CANDIDATES")
    print("  - update DOMAIN_CATALOG.md acordando")
    print()
    mode = "WARN-ONLY" if not strict else "BLOCKING [PROMOTED Sprint 8 Frente C]"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    # Sprint 8 Frente C: WARN-ONLY → BLOCKING (default strict=True).
    # Use --warn-only para opt-out (legacy ratchet em branches atrasadas).
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
