"""check_trigger_types_canonical.py — Sprint Z.7 sensor.

Garante que NAO existe mais de 1 fonte de TRIGGER_TYPES no backend.
Pos-consolidacao Sprint Z.4: apenas trigger_types_canonical.py deve definir
TriggerType enum + TRIGGER_TYPE_CATALOG.

Outros arquivos podem USAR esses (via import) mas NAO definir lista propria.

DEFERRED ALLOWLIST (Sprint Z.5/Z.6):
- libs/models/lia_models/automation.py — DB enum bound a coluna. Sera removido
  apos migration data-only Z.6.
- app/domains/automation/services/stage_automation_engine.py — runtime dispatch
  local. Sera removido em Z.5 (refactor handlers para importar canonical).
- app/domains/automation/services/automation_trigger_service.py — proactive
  triggers cron. Sera removido em Z.6.

Exit codes:
- 0: ok (somente canonical + deferred allowlist)
- 1: drift detected (novo arquivo definiu TriggerType fora do allowlist)

Usage:
    python3 scripts/check_trigger_types_canonical.py
    python3 scripts/check_trigger_types_canonical.py --strict  # ignora allowlist
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_PATH = "app/shared/automation/trigger_types_canonical.py"
SCAN_DIRS = ["app/", "libs/"]

# Arquivos que ainda definem TriggerType pre-Z.4 e estao agendados pra
# deprecacao. Drift = qualquer arquivo NOVO fora do canonical OU deste set.
DEPRECATED_ALLOWLIST = {
    # Sprint Z.db (2026-05-27): automation.py removed after data migration 213.
    # All deferred entries resolved. Allowlist is now empty.
}


# Scope do sensor: apenas modulos relacionados a automation. Outros dominios
# (data_request, policy/escalation) podem ter class TriggerType propria —
# namespace collision legitimo, escopo semantico diferente.
AUTOMATION_PATH_MARKERS = (
    "automation",  # app/domains/automation/...
    "lia_models/automation",  # libs/models/lia_models/automation.py
)


def _is_automation_scope(rel_path: str) -> bool:
    """True se o arquivo pertence ao dominio de automation triggers."""
    return any(marker in rel_path for marker in AUTOMATION_PATH_MARKERS)


def find_trigger_type_definitions() -> list[tuple[Path, str]]:
    """Procura arquivos que definem class TriggerType OU TRIGGER_TYPES = [...]
    DENTRO do escopo automation (ignora namespaces colidindo em outros dominios).

    Returns lista de (Path, kind) onde kind é 'class' ou 'list'.
    """
    found: list[tuple[Path, str]] = []
    for scan_dir in SCAN_DIRS:
        base = REPO_ROOT / scan_dir
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                source = py.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            rel = py.relative_to(REPO_ROOT).as_posix()
            if not _is_automation_scope(rel):
                continue  # skip data_request, policy, etc.

            for node in ast.walk(tree):
                # class TriggerType(...): / class TriggerType(StrEnum): / etc.
                if isinstance(node, ast.ClassDef) and node.name == "TriggerType":
                    found.append((py, "class"))
                    break
                # TRIGGER_TYPES = [...] / TRIGGER_TYPE_CHOICES = [...] /
                # TRIGGER_TYPE_CATALOG = (...)
                if isinstance(node, ast.Assign):
                    matched = False
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in (
                            "TRIGGER_TYPES",
                            "TRIGGER_TYPE_CHOICES",
                            "TRIGGER_TYPE_CATALOG",
                        ):
                            # TRIGGER_TYPE_CATALOG no canonical é OK
                            if rel != CANONICAL_PATH:
                                found.append((py, "list"))
                            matched = True
                            break
                    if matched:
                        break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Ignora DEPRECATED_ALLOWLIST. Use quando Z.5/Z.6 estiverem fechados.",
    )
    args = parser.parse_args()

    suspects = find_trigger_type_definitions()
    drift: list[tuple[Path, str]] = []
    deferred: list[tuple[Path, str]] = []

    for path, kind in suspects:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == CANONICAL_PATH:
            continue
        if not args.strict and rel in DEPRECATED_ALLOWLIST:
            deferred.append((path, kind))
            continue
        drift.append((path, kind))

    if deferred:
        print("DEFERRED (allowlisted ate Sprint Z.5/Z.6):")
        for path, kind in deferred:
            rel = path.relative_to(REPO_ROOT).as_posix()
            print(f"  - {rel} ({kind})")
        print()

    if not drift:
        print(f"OK: canonical source ({CANONICAL_PATH}) is single source of truth.")
        if deferred and not args.strict:
            print(f"NOTE: {len(deferred)} deferred files agendados pra remocao Z.5/Z.6.")
        return 0

    print("DRIFT DETECTED — TriggerType definido fora do canonical:")
    for path, kind in drift:
        rel = path.relative_to(REPO_ROOT).as_posix()
        print(f"  - {rel} ({kind})")
    print()
    print(f"Canonical: {CANONICAL_PATH}")
    print("Fix: refatorar para importar TriggerType / TRIGGER_TYPE_CATALOG do canonical.")
    print("     Se o arquivo é deferred legacy, adicionar em DEPRECATED_ALLOWLIST.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
