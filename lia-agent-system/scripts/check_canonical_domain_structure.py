#!/usr/bin/env python3
"""Sensor canonical T-15: valida estrutura canonical de agentic domains.

Regras (R1-R5):
- R1: domain agentic DEVE ter domain.py com @register_domain + ComplianceDomainPrompt
- R2: YAML correspondente em app/prompts/domains/{domain_id}.yaml
- R3: metadata.version válido no YAML (ADR-028-v2)
- R4: tests em tests/test_domains/test_{domain_id}*.py OU tests/unit/test_{domain_id}_domain.py
- R5: promotion candidates state preview (5 candidates ADR-V3.1)

Modo: BLOCKING [PROMOTED Sprint 8 Frente B] — baseline 0 violations confirmado
2026-05-21. Use --warn-only para opt-out em branches legadas (ratchet).

Uso:
    python scripts/check_canonical_domain_structure.py            # BLOCKING (default)
    python scripts/check_canonical_domain_structure.py --warn-only  # opt-out
"""
from __future__ import annotations

import ast
import sys
import yaml
from pathlib import Path


# Lista canonical agentic domains (DOMAIN_CATALOG.md ground truth)
AGENTIC_DOMAINS = [
    "analytics", "ats_integration", "automation", "communication",
    "cv_screening", "hiring_policy", "interview_scheduling", "job_creation",
    "job_management", "pipeline", "recruiter_assistant", "sourcing",
    "agent_studio",
]

# Micro-action domains (3)
MICRO_ACTION_DOMAINS = ["digital_twin", "recruitment_campaign", "talent_pool"]

# Promotion candidates ADR-V3.1 (5)
PROMOTION_CANDIDATES = [
    "auth", "chat", "notifications", "consent", "data_subject",
]


def check_r1_domain_py(repo_root: Path, domain_id: str) -> list[str]:
    """R1: domain.py com @register_domain + ComplianceDomainPrompt."""
    issues = []
    domain_py = repo_root / "app" / "domains" / domain_id / "domain.py"
    if not domain_py.exists():
        issues.append(
            f"R1 [{domain_id}]: domain.py NÃO existe em app/domains/{domain_id}/. "
            f"Criar com @register_domain + class herda ComplianceDomainPrompt."
        )
        return issues

    try:
        tree = ast.parse(domain_py.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append(f"R1 [{domain_id}]: domain.py erro de parse — {e}")
        return issues

    has_register = False
    has_compliance_base = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check @register_domain decorator
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "register_domain":
                    has_register = True
                elif isinstance(dec, ast.Attribute) and dec.attr == "register_domain":
                    has_register = True
            # Check ComplianceDomainPrompt base
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "ComplianceDomainPrompt":
                    has_compliance_base = True

    if not has_register:
        issues.append(
            f"R1 [{domain_id}]: domain.py sem @register_domain. "
            f"Adicionar from app.domains.registry import register_domain"
        )
    if not has_compliance_base:
        issues.append(
            f"R1 [{domain_id}]: domain.py sem ComplianceDomainPrompt base. "
            f"Class deve herdar de ComplianceDomainPrompt"
        )
    return issues


def check_r2_yaml(repo_root: Path, domain_id: str) -> list[str]:
    """R2: YAML em app/prompts/domains/."""
    yaml_path = repo_root / "app" / "prompts" / "domains" / f"{domain_id}.yaml"
    if not yaml_path.exists():
        return [
            f"R2 [{domain_id}]: YAML ausente em app/prompts/domains/{domain_id}.yaml. "
            f"Criar com metadata.version + system_prompt."
        ]
    return []


def check_r3_version(repo_root: Path, domain_id: str) -> list[str]:
    """R3: metadata.version válido no YAML."""
    yaml_path = repo_root / "app" / "prompts" / "domains" / f"{domain_id}.yaml"
    if not yaml_path.exists():
        return []  # R2 já reportou
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return [f"R3 [{domain_id}]: YAML root não é dict"]
        meta = data.get("metadata")
        if not isinstance(meta, dict) or "version" not in meta:
            return [
                f"R3 [{domain_id}]: YAML sem metadata.version. "
                f"Adicionar metadata: {{version: \"1.0\"}}"
            ]
    except Exception as e:
        return [f"R3 [{domain_id}]: YAML parse error — {e}"]
    return []


def check_r4_tests(repo_root: Path, domain_id: str) -> list[str]:
    """R4: tests existem para o domain."""
    candidates = [
        repo_root / "tests" / "test_domains" / f"test_{domain_id}.py",
        repo_root / "tests" / "test_domains" / f"test_{domain_id}_domain.py",
        repo_root / "tests" / "unit" / f"test_{domain_id}_domain.py",
        repo_root / "tests" / "unit" / f"test_{domain_id}.py",
        repo_root / "tests" / "domains" / f"test_{domain_id}.py",
        repo_root / "tests" / "domains" / domain_id,  # diretorio
    ]
    # Also glob: any test_*{domain_id}*.py
    for candidate in candidates:
        if candidate.exists():
            return []
    # Glob fallback
    test_dir = repo_root / "tests"
    if test_dir.exists():
        for tf in test_dir.rglob(f"*{domain_id}*.py"):
            if tf.name.startswith("test_") or "test" in tf.parent.name:
                return []
    return [
        f"R4 [{domain_id}]: nenhum test encontrado para domain. "
        f"Criar smoke test mínimo em tests/test_domains/test_{domain_id}.py"
    ]


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    all_issues: list[str] = []
    all_warnings: list[str] = []

    # Agentic domains: R1-R4
    for domain_id in AGENTIC_DOMAINS:
        issues = []
        issues.extend(check_r1_domain_py(repo_root, domain_id))
        issues.extend(check_r2_yaml(repo_root, domain_id))
        issues.extend(check_r3_version(repo_root, domain_id))
        issues.extend(check_r4_tests(repo_root, domain_id))
        all_issues.extend(issues)

    # Micro-action: R2-R3 only (não exige domain.py canonical)
    for domain_id in MICRO_ACTION_DOMAINS:
        all_warnings.extend(check_r2_yaml(repo_root, domain_id))
        all_warnings.extend(check_r3_version(repo_root, domain_id))

    # R5: promotion candidates preview
    for cand in PROMOTION_CANDIDATES:
        domain_py = repo_root / "app" / "domains" / cand / "domain.py"
        if domain_py.exists():
            all_warnings.append(
                f"R5 [{cand}]: PROMOÇÃO DETECTADA — domain.py existe. "
                f"Mover de PROMOTION_CANDIDATES para AGENTIC_DOMAINS em sensor + DOMAIN_CATALOG.md"
            )
        else:
            # Expected — está no backlog F4+
            pass

    total_issues = len(all_issues)
    total_warnings = len(all_warnings)

    if total_issues == 0 and total_warnings == 0:
        print(
            f"[T-15 CANONICAL STRUCTURE] OK -- "
            f"{len(AGENTIC_DOMAINS)} agentic + {len(MICRO_ACTION_DOMAINS)} micro-action canonical"
        )
        return 0

    if total_issues:
        print(f"[T-15 CANONICAL STRUCTURE] {total_issues} ISSUES (agentic domains):")
        for issue in all_issues:
            print(f"  ❌ {issue}")
        print()

    if total_warnings:
        print(f"[T-15 CANONICAL STRUCTURE] {total_warnings} WARNINGS:")
        for w in all_warnings:
            print(f"  ⚠  {w}")
        print()

    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if (strict and total_issues > 0) else 0


if __name__ == "__main__":
    # PROMOTED Sprint 8 Frente B (2026-05-21): default BLOCKING.
    # --warn-only é opt-out para branches legadas/ratchet incremental.
    # --strict mantido como alias backward-compatible (no-op em modo default).
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
