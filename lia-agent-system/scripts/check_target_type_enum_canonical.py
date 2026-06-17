#!/usr/bin/env python3
"""Sensor: target_type (junction agente↔surface) é canonical em UM lugar.

Onda 2 B4 (2026-05-28) — sensor BLOCKING canonical.

DeploymentTargetType (em lia_models.agent_deployment) é a fonte única de
verdade pros 4 valores canonical do enum:
  {job, talent_pool, pipeline_stage, candidate_list}

Recidiva proibida: várias features (schemas Pydantic, Literal[] hardcoded,
TS frontend, query params FastAPI) tendem a redeclarar a lista com valores
divergentes. Drift = bugs subtis em cross-tenant filters, pingos UI que
não atualizam, deployments aceitos com target_type inválido.

O sensor é AST-based (não-inferencial — não usa LLM). Verifica:
  1. lia_models/agent_deployment.py define DeploymentTargetType com EXATOS
     {job, talent_pool, pipeline_stage, candidate_list}.
  2. Não há outras definições de Enum classe com nome *TargetType* nos
     paths app/, libs/ (drift detection).
  3. Literal[] hardcoded de target_type em app/schemas/ ou app/api/ deve
     conter EXATAMENTE os 4 valores (alerta se sobra/falta).

Output otimizado pra consumo de LLM (instruções de fix embutidas em PT-BR).

Exit codes:
  0 — OK (canonical respeitado)
  1 — violação (drift de enum ou Literal divergente)
  2 — canonical não encontrado (estrutura mudou — investigar)

Uso:
  python3 scripts/check_target_type_enum_canonical.py
  python3 scripts/check_target_type_enum_canonical.py --warn-only
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_FILE = ROOT / "libs" / "models" / "lia_models" / "agent_deployment.py"
CANONICAL_ENUM_NAME = "DeploymentTargetType"
CANONICAL_VALUES = {"job", "talent_pool", "pipeline_stage", "candidate_list"}

# Onde buscar drift (recursivo).
SCAN_DIRS = [
    ROOT / "app" / "schemas",
    ROOT / "app" / "api",
    ROOT / "app" / "domains",
    ROOT / "libs" / "models",
]

EXEMPT_PATHS: list[str] = [
    # Canonical defesa (lia_models/agent_deployment.py) é o source-of-truth
    # — não conta como drift.
    "libs/models/lia_models/agent_deployment.py",
]

# Allowlist para Literal[] em contextos específicos (DSL helper, surface UI etc).
# Estes ficam isentos se redeclararem valores canonical — outros valores apitam.
ALLOWED_LITERAL_REDECLARATIONS = {
    # surface UI superset: agent_monitoring._StudioTargetSurface,
    # _AgentsCardSurface (talent_pool|job|pipeline_stage|candidate_list)
    # — ainda são CANONICAL (subset OK). Drift = extra ou faltando.
}


def _load_canonical() -> set[str]:
    """Parse lia_models/agent_deployment.py and extract canonical enum values."""
    if not CANONICAL_FILE.exists():
        print(f"ERRO B4.canonical: arquivo canonical não encontrado: {CANONICAL_FILE}")
        print("→ Estrutura mudou. Investigar antes de prosseguir.")
        sys.exit(2)

    tree = ast.parse(CANONICAL_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == CANONICAL_ENUM_NAME:
            values: set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    # Padrao: NAME = "value"
                    if (
                        len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                    ):
                        values.add(stmt.value.value)
            return values

    print(f"ERRO B4.canonical: enum {CANONICAL_ENUM_NAME} não encontrado em {CANONICAL_FILE}")
    print("→ Renomeado ou removido? Atualizar o sensor canonical antes.")
    sys.exit(2)


def _scan_drift() -> list[tuple[Path, int, str]]:
    """Procura outras definições de enum com TargetType no nome."""
    drifts: list[tuple[Path, int, str]] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel in EXEMPT_PATHS:
                continue
            if "/__pycache__/" in rel or "/.venv/" in rel:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if node.name == CANONICAL_ENUM_NAME:
                    continue
                # Extract enum-like string constants from the class body.
                values: set[str] = set()
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        if (
                            len(stmt.targets) == 1
                            and isinstance(stmt.targets[0], ast.Name)
                            and isinstance(stmt.value, ast.Constant)
                            and isinstance(stmt.value.value, str)
                        ):
                            values.add(stmt.value.value)
                # Drift detection: a classe é drift do canonical somente se
                # seus valores intersectam >=2 com o canonical (não é coincidência
                # de nome "TargetType" entre conceitos diferentes — policy/rate-limit
                # tem TargetType={company,user,agent,action} sem overlap).
                overlap = values & CANONICAL_VALUES
                if len(overlap) >= 2:
                    drifts.append(
                        (
                            path,
                            node.lineno,
                            f"classe {node.name} redefine target_type canonical "
                            f"(overlap com canonical: {sorted(overlap)})",
                        )
                    )
    return drifts


def _scan_literal_redeclarations() -> list[tuple[Path, int, set[str], str]]:
    """Procura Literal[\"job\", \"talent_pool\", ...] hardcoded.

    Aceita subsets/supersets dos canonical, MAS apita se inclui valor
    NÃO-canonical (typo, valor descontinuado, drift).
    """
    findings: list[tuple[Path, int, set[str], str]] = []

    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel in EXEMPT_PATHS:
                continue
            if "/__pycache__/" in rel:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                # Procurar Subscript: Literal[ "x", "y", ... ]
                if not isinstance(node, ast.Subscript):
                    continue
                if not isinstance(node.value, ast.Name):
                    continue
                if node.value.id != "Literal":
                    continue
                # Slice: Tuple ou single
                slc = node.slice
                consts: list[str] = []
                if isinstance(slc, ast.Tuple):
                    for elt in slc.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            consts.append(elt.value)
                elif isinstance(slc, ast.Constant) and isinstance(slc.value, str):
                    consts.append(slc.value)

                if not consts:
                    continue
                consts_set = set(consts)
                # Heuristic: só relevante se subset/intersect tem >=2 valores canonical
                # OU se um valor não-canonical próximo (job_X, candidate_id_list etc).
                intersect = consts_set & CANONICAL_VALUES
                if len(intersect) < 2:
                    # Não é um Literal de target_type — outro contexto.
                    continue
                # Drift detection: valores fora do canonical
                extras = consts_set - CANONICAL_VALUES
                if extras:
                    findings.append(
                        (
                            path,
                            node.lineno,
                            extras,
                            "Literal de target_type tem valores não-canonical",
                        )
                    )
    return findings


def main() -> int:
    warn_only = "--warn-only" in sys.argv

    # 1) Validar canonical tem os 4 valores exatos.
    canonical_values = _load_canonical()
    violations: list[str] = []

    if canonical_values != CANONICAL_VALUES:
        missing = CANONICAL_VALUES - canonical_values
        extra = canonical_values - CANONICAL_VALUES
        msg = [
            f"VIOLAÇÃO B4.1: {CANONICAL_ENUM_NAME} drift no canonical {CANONICAL_FILE.relative_to(ROOT)}",
        ]
        if missing:
            msg.append(f"  → Valores FALTANDO: {sorted(missing)}")
            msg.append(f"  → Fix: adicionar como entradas do enum (em lia_models/agent_deployment.py).")
        if extra:
            msg.append(f"  → Valores EXTRAS (não-canonical): {sorted(extra)}")
            msg.append(
                "  → Fix: discutir com Paulo antes de remover. Mudar o canonical "
                "exige sincronizar schemas, FastAPI Literals, frontend TS types, e migrar dados."
            )
        violations.append("\n".join(msg))

    # 2) Detectar drift (outras classes *TargetType).
    drifts = _scan_drift()
    for path, lineno, msg in drifts:
        rel = path.relative_to(ROOT).as_posix()
        violations.append(
            f"VIOLAÇÃO B4.2: {rel}:{lineno} — {msg}\n"
            f"  → Fix: remover a classe duplicada e importar "
            f"DeploymentTargetType de lia_models.agent_deployment."
        )

    # 3) Detectar Literal[...] com valores não-canonical.
    literal_findings = _scan_literal_redeclarations()
    for path, lineno, extras, msg in literal_findings:
        rel = path.relative_to(ROOT).as_posix()
        violations.append(
            f"VIOLAÇÃO B4.3: {rel}:{lineno} — {msg}\n"
            f"  → Valores não-canonical detectados: {sorted(extras)}\n"
            f"  → Fix: ou (a) remover esses valores e usar DeploymentTargetType "
            f"do canonical, ou (b) renomear o Literal para outro nome se for "
            f"deliberadamente diferente (e abrir issue pra discutir o nome)."
        )

    if violations:
        print("\n".join(violations))
        print()
        print(f"Total violations: {len(violations)}")
        if warn_only:
            print("Modo --warn-only: exit 0 (não-bloqueante)")
            return 0
        print("Modo BLOCKING (default): exit 1")
        return 1

    print("OK — target_type enum canonical respeitado (B4)")
    print(f"  Canonical: {CANONICAL_ENUM_NAME} em {CANONICAL_FILE.relative_to(ROOT)}")
    print(f"  Valores: {sorted(CANONICAL_VALUES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
