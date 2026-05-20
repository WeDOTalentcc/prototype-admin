#!/usr/bin/env python3
"""
AST checker canonical — enforça convenções Pydantic em request schemas.

Registrado 2026-05-20 pós-audit E2E (sensor #3 do harness analysis).

Regras enforced (todas Replit-only; output otimizado pra consumo de LLM):

  R1 — extra='forbid' em request body schemas
       Schemas (Create|Update|Request suffix) DEVEM ter model_config = ConfigDict(extra='forbid')
       OU herdar de WeDoBaseModel (canonical em app/shared/types.py).
       Por quê: audit F1.O2 — POST /job-vacancies aceitou silenciosamente fields fantasma
       (city, state, country, industry). Default Pydantic é 'extra=ignore' — anti-canonical.

  R2 — company_id PROIBIDO em request body
       Nenhum BaseModel pode ter field 'company_id'. Multi-tenancy canonical (CLAUDE.md):
       company_id SEMPRE vem do JWT via Depends(require_company_id).
       Por quê: audit F4.O1, F5.O1 — endpoints recentes pediam company_id no payload,
       abrindo brecha cross-tenant. Violação direta de canonical existente.

  R3 — Path UUID + pattern combo PROIBIDO
       Nenhum `: UUID = Path(..., pattern=...)` — Pydantic 2.10+ não aceita.
       Use `: JobIdParam` (alias canonical em app/shared/types.py) ou `: str = Path(...)`.
       Por quê: audit F2.B1 — 24 endpoints quebrados pelo mesmo copy-paste pattern.

Uso:
    python3 scripts/check_pydantic_conventions.py [DIR]   # default: lia-agent-system/app
    Exit 0 = clean, Exit 1 = violations encontradas (mensagens com fix sugerido).

Integração canonical:
    - pre-commit hook (.pre-commit-config.yaml)
    - CI/CD step (backend-ci.yml ou equivalente)
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────
REQUEST_BODY_SUFFIXES = ("Create", "Update", "Request", "Payload", "Input")
"""Heurística: schemas com esses sufixos são request bodies. Override via SKIP_R1."""

SKIP_R1: set[str] = {
    # Classes que legitimamente precisam de extra=allow (externas, schema drift)
    # Formato: "ModelName" ou "module.path:ModelName"
    # Sempre adicionar com motivo + ticket associado.
}

CANONICAL_BASE_CLASSES = {"WeDoBaseModel"}
"""Subclasses dessas têm extra='forbid' herdado — passam R1 sem model_config explícito."""

EXCLUDE_PATHS = (
    "__pycache__",
    ".bak",
    "tests/fixtures",
    "alembic/versions",  # migrations geram models temporários
)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Violation:
    rule: str  # R1, R2, R3
    file: str
    line: int
    target: str  # class name or symbol
    message: str  # multi-line, LLM-friendly fix instructions


# ─────────────────────────────────────────────────────────────────────────────
# AST checkers
# ─────────────────────────────────────────────────────────────────────────────
def _is_pydantic_basemodel(class_node: ast.ClassDef) -> bool:
    """Heurística: classe é Pydantic BaseModel (direto ou via alias canonical)."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in {"BaseModel"} | CANONICAL_BASE_CLASSES:
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    return False


def _inherits_canonical_base(class_node: ast.ClassDef) -> bool:
    """True se herda de WeDoBaseModel (que já tem extra='forbid')."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in CANONICAL_BASE_CLASSES:
            return True
    return False


def _has_extra_forbid(class_node: ast.ClassDef) -> bool:
    """True se classe declara model_config = ConfigDict(extra='forbid')."""
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "model_config" for t in stmt.targets):
            continue
        # Verifica se valor contém extra='forbid'
        if isinstance(stmt.value, ast.Call):
            for kw in stmt.value.keywords:
                if kw.arg == "extra" and isinstance(kw.value, ast.Constant):
                    if kw.value.value == "forbid":
                        return True
    return False


def _is_request_body_schema(class_name: str) -> bool:
    return any(class_name.endswith(suffix) for suffix in REQUEST_BODY_SUFFIXES)


def check_r1(class_node: ast.ClassDef, filepath: str) -> Violation | None:
    """R1: request body schemas precisam de extra='forbid'."""
    if not _is_pydantic_basemodel(class_node):
        return None
    if not _is_request_body_schema(class_node.name):
        return None
    if class_node.name in SKIP_R1:
        return None
    if _inherits_canonical_base(class_node):
        return None  # WeDoBaseModel já tem
    if _has_extra_forbid(class_node):
        return None
    return Violation(
        rule="R1",
        file=filepath,
        line=class_node.lineno,
        target=class_node.name,
        message=(
            f"❌ R1 violation: {class_node.name} em {filepath}:{class_node.lineno}\n"
            f"   Request body schema sem extra='forbid' — Pydantic default 'ignore' aceita "
            f"silenciosamente fields fantasma (audit F1.O2).\n"
            f"\n"
            f"   Fix canonical (escolher 1):\n"
            f"   (a) Herdar de WeDoBaseModel:\n"
            f"       from app.shared.types import WeDoBaseModel\n"
            f"       class {class_node.name}(WeDoBaseModel):\n"
            f"           ...\n"
            f"\n"
            f"   (b) Adicionar model_config explícito:\n"
            f"       from pydantic import ConfigDict\n"
            f"       class {class_node.name}(BaseModel):\n"
            f"           model_config = ConfigDict(extra='forbid')\n"
            f"           ...\n"
        ),
    )


def check_r2(class_node: ast.ClassDef, filepath: str) -> Iterable[Violation]:
    """R2: nenhum BaseModel pode ter field company_id (multi-tenancy canonical)."""
    if not _is_pydantic_basemodel(class_node):
        return
    for stmt in class_node.body:
        if not isinstance(stmt, ast.AnnAssign):
            continue
        if not isinstance(stmt.target, ast.Name):
            continue
        if stmt.target.id == "company_id":
            yield Violation(
                rule="R2",
                file=filepath,
                line=stmt.lineno,
                target=f"{class_node.name}.company_id",
                message=(
                    f"❌ R2 violation: {class_node.name}.company_id em {filepath}:{stmt.lineno}\n"
                    f"   Multi-tenancy canonical (CLAUDE.md) proíbe company_id em request payload.\n"
                    f"   Audit F4.O1, F5.O1: endpoints com company_id no body abrem brecha cross-tenant.\n"
                    f"\n"
                    f"   Fix canonical:\n"
                    f"   1. Remova o field 'company_id' do schema {class_node.name}.\n"
                    f"   2. No handler que usa este schema, adicione:\n"
                    f"        from app.shared.security.require_company_id import require_company_id\n"
                    f"        async def my_handler(\n"
                    f"            payload: {class_node.name},\n"
                    f"            company_id: str = Depends(require_company_id),  # extraído do JWT\n"
                    f"        ):\n"
                    f"   3. Use `company_id` extraído do JWT, NUNCA do `payload`.\n"
                ),
            )


def check_r3(tree: ast.AST, filepath: str) -> Iterable[Violation]:
    """R3: nenhum `: UUID = Path(..., pattern=...)` combo."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign):
            continue
        # type annotation == UUID?
        ann = node.annotation
        is_uuid = isinstance(ann, ast.Name) and ann.id == "UUID"
        if not is_uuid:
            continue
        # value = Path(..., pattern=...)?
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        is_path_call = isinstance(func, ast.Name) and func.id == "Path"
        if not is_path_call:
            continue
        has_pattern = any(kw.arg == "pattern" for kw in node.value.keywords)
        if not has_pattern:
            continue
        target_name = node.target.id if isinstance(node.target, ast.Name) else "<unknown>"
        yield Violation(
            rule="R3",
            file=filepath,
            line=node.lineno,
            target=target_name,
            message=(
                f"❌ R3 violation: {target_name}: UUID = Path(..., pattern=...) em {filepath}:{node.lineno}\n"
                f"   Pydantic 2.10+ não permite constraint 'pattern' em type UUID — só em str (audit F2.B1).\n"
                f"\n"
                f"   Fix canonical (escolher 1):\n"
                f"   (a) Use o type alias canonical:\n"
                f"       from app.shared.types import JobIdParam  # ou CandidateIdParam, CompanyIdParam\n"
                f"       async def my_handler({target_name}: JobIdParam, ...):\n"
                f"           ...\n"
                f"\n"
                f"   (b) Substitua type por `str` mantendo pattern:\n"
                f"       {target_name}: str = Path(..., pattern=r'^(?:[0-9a-fA-F-]{{36}}|[0-9]+)$')\n"
                f"\n"
                f"   Se precisar de UUID no body do handler, converta dentro:\n"
                f"       from uuid import UUID\n"
                f"       _uuid = UUID({target_name})  # raises ValueError se não for UUID v4\n"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
def scan_file(filepath: Path) -> list[Violation]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        # Skip files que não parseiam (não é nosso problema reportar — outros linters pegam)
        return []

    violations: list[Violation] = []

    # R3: file-level (qualquer AnnAssign UUID+Path)
    violations.extend(check_r3(tree, str(filepath)))

    # R1 e R2: class-level
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            r1 = check_r1(node, str(filepath))
            if r1:
                violations.append(r1)
            violations.extend(check_r2(node, str(filepath)))

    return violations


def should_skip_file(filepath: Path) -> bool:
    return any(excl in str(filepath) for excl in EXCLUDE_PATHS)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "lia-agent-system/app")
    if not root.exists():
        print(f"⚠ Path não existe: {root}")
        return 2

    all_violations: list[Violation] = []
    files_scanned = 0

    for py_file in root.rglob("*.py"):
        if should_skip_file(py_file):
            continue
        files_scanned += 1
        all_violations.extend(scan_file(py_file))

    if not all_violations:
        print(f"✅ Pydantic conventions OK ({files_scanned} arquivos verificados)")
        return 0

    print(f"❌ {len(all_violations)} violações em {files_scanned} arquivos:\n")
    # Group by rule
    by_rule: dict[str, list[Violation]] = {}
    for v in all_violations:
        by_rule.setdefault(v.rule, []).append(v)

    for rule in sorted(by_rule):
        violations = by_rule[rule]
        print(f"\n{'=' * 70}")
        print(f"{rule} — {len(violations)} violação(ões)")
        print("=" * 70)
        for v in violations:
            print(v.message)

    print(f"\n📊 Resumo: {len(all_violations)} violações total")
    for rule in sorted(by_rule):
        print(f"   {rule}: {len(by_rule[rule])} violação(ões)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
