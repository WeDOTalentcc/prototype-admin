#!/usr/bin/env python3
"""Sensor canonical T-12 (V3.1 reclassificação): valida 30 stubs thin-CRUD.

V3 D2 original disse "deletar 10 stubs". Audit Fase A revelou que todos 10
têm endpoints v1 ATIVOS em produção (~110 rotas, 7000+ LOC). Reclassificação:

- DELETE candidates → "DESCONTINUE-FEATURE-FIRST" (não delete imediato)
- Os 30 são pattern intencional thin-CRUD com dependency injection canonical
- 5 high-value candidatos a promoção (auth, chat, notifications, consent, data_subject)
- Sensor valida invariantes: stub mantém shape canonical, sem domain.py drift

Modo: WARN-ONLY inicial.

Uso:
    python scripts/check_stub_invariants.py [--strict]
"""
from __future__ import annotations

import sys
from pathlib import Path


# Os 30 stubs documentados em DOMAIN_CATALOG.md como repository stubs
STUB_DOMAINS = {
    "admin", "admin_settings", "agent_memory", "approvals", "auth",
    "bulk_actions", "candidate_lists", "chat", "clients", "client_users",
    "company_culture", "compliance", "consent", "data_subject",
    "email_templates", "goals", "health_check", "job_vacancies_analytics",
    "journey_mapping", "notifications", "observability", "opinions",
    "recruitment_journey", "saas_metrics", "shared_searches", "tasks",
    "technical_tests", "triagem", "trust_center", "workforce",
}

# 5 high-value candidatos a promoção (futuro, não Sprint atual)
PROMOTION_CANDIDATES = {
    "auth", "chat", "notifications", "consent", "data_subject",
}

# 2 deprecated (T-09 Fase 1+ migration target)
DEPRECATED = {
    "autonomous", "policy",
}


def check(strict: bool = False) -> int:
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

    # R2: stub novo apareceu fora da lista?
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
                    and entry.name not in STUB_DOMAINS
                    and entry.name not in DEPRECATED
                ):
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
            f"[T-12 STUB INVARIANTS] OK -- 30 stubs canonical + "
            f"5 promotion candidates documentados"
        )
        return 0

    print(f"[T-12 STUB INVARIANTS] {len(violations)} violations:")
    for v in violations:
        print(f"  ⚠  {v}")
    print()
    print("CORRECAO canonical:")
    print("  - stub novo: adicionar a STUB_DOMAINS em scripts/check_stub_invariants.py")
    print("  - stub promovido: criar domain.py + adicionar a PROMOTION_CANDIDATES")
    print("  - update DOMAIN_CATALOG.md acordando")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    sys.exit(check(strict=strict))
