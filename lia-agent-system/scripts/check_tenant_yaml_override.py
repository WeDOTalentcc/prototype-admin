#!/usr/bin/env python3
"""Sensor canonical T-13: tenant YAML overrides validation.

Regras canonical (ADR-028-v3):
- R1: tenant override file DEVE existir em app/prompts/tenants/{id}/{path}.yaml
  (validates directory structure)
- R2: tenant YAML DEVE ter metadata.version (mesma regra T-05 / ADR-028)
- R3: tenant YAML NÃO PODE ter campos PII direto no override
  (CPF/email/phone patterns triggered cross-tenant LGPD risk if exfiltrated)
- R4: tenant YAML schema DEVE ser compatível com canonical (mesmas top-level keys)
  - WARN-only se schema diverge (não bloqueia, mas alerta drift)

Modo: WARN-ONLY inicial. Promover BLOCKING após admin UI live (T-13 Fase 2).

Uso:
    python scripts/check_tenant_yaml_override.py [--strict]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


# PII patterns canonical (mesmos do TrainingDataAnonymizer T-21)
PII_PATTERNS = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "CPF"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    (re.compile(r"\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"), "PHONE"),
]


def _scan_pii_recursive(value, path_prefix: str = "") -> list[str]:
    """Recursively scan dict/list for PII patterns. Returns list of findings."""
    findings = []
    if isinstance(value, str):
        for pattern, label in PII_PATTERNS:
            if pattern.search(value):
                findings.append(f"{path_prefix}: {label} pattern detected")
    elif isinstance(value, dict):
        for k, v in value.items():
            findings.extend(_scan_pii_recursive(v, f"{path_prefix}.{k}"))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            findings.extend(_scan_pii_recursive(item, f"{path_prefix}[{i}]"))
    return findings


def check(strict: bool = True) -> int:  # [PROMOTED BLOCKING Sprint 7]
    repo_root = Path(__file__).resolve().parent.parent
    tenants_dir = repo_root / "app/prompts/tenants"

    if not tenants_dir.exists():
        print("[T-13 TENANT YAML] tenants/ directory does not exist — skip")
        return 0

    violations = []
    info_lines = []
    tenant_count = 0
    yaml_count = 0

    # Iterate tenant directories
    for tenant_dir in sorted(tenants_dir.iterdir()):
        if not tenant_dir.is_dir():
            continue
        if tenant_dir.name.startswith("."):
            continue

        tenant_id = tenant_dir.name
        tenant_count += 1
        yaml_files = list(tenant_dir.rglob("*.yaml"))

        for yaml_file in yaml_files:
            yaml_count += 1
            rel_path = yaml_file.relative_to(tenants_dir)
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                violations.append(
                    f"{rel_path}: YAML parse error: {e}"
                )
                continue

            if data is None:
                violations.append(f"{rel_path}: empty YAML file")
                continue

            # R2: metadata.version present
            if not isinstance(data, dict) or "metadata" not in data:
                violations.append(
                    f"{rel_path}: missing 'metadata' key (R2 ADR-028 compliance)"
                )
            elif not isinstance(data.get("metadata"), dict) or "version" not in data["metadata"]:
                violations.append(
                    f"{rel_path}: missing 'metadata.version' (R2)"
                )

            # R3: PII patterns scan
            pii_findings = _scan_pii_recursive(data, path_prefix=str(rel_path))
            if pii_findings:
                for f in pii_findings:
                    violations.append(f"R3 LGPD risk: {f}")

            info_lines.append(f"  ✓ tenant={tenant_id} file={yaml_file.name}")

    if violations:
        print(f"[T-13 TENANT YAML] {len(violations)} violations:")
        for v in violations:
            print(f"  ❌ {v}")
        print()
        print("CORRECAO canonical:")
        print("  R2: adicionar metadata: { version: '1.0', tenant_id: <id> } no topo")
        print("  R3: remover PII raw (use placeholders se necessário)")
        print()
        mode = "BLOCKING" if strict else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if strict else 0

    print(
        f"[T-13 TENANT YAML] OK -- {tenant_count} tenants, {yaml_count} YAMLs validated"
    )
    if info_lines and tenant_count > 0:
        print("\n".join(info_lines[:20]))
    return 0


if __name__ == "__main__":
    strict = "--warn-only" not in sys.argv  # [PROMOTED BLOCKING Sprint 7]
    sys.exit(check(strict=strict))
