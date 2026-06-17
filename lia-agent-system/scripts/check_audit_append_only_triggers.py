#!/usr/bin/env python3
"""W1-006 part 2 · Sensor BLOCKING — append-only triggers em audit_execution_metadata.

Verifica que migration 180_audit_append_only_triggers permanece em alembic/versions/
E está corretamente formada (revision_id, down_revision, 3 funcs, 3 triggers).

Defesa contra:
- Migration acidentalmente deletada por outro agente
- Drift de revision_id ou down_revision
- Remoção de uma das 3 funcs/triggers (UPDATE/DELETE/TRUNCATE) — todos obrigatórios

NÃO é sensor de runtime (não conecta ao DB). É sensor de canonical file structure.
Para verificar runtime DB state, ver scripts/verify_audit_chain.py (já existente via W1-006 part 1).

Exit 0 = OK · Exit 1 = violation detectada.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "alembic" / "versions"
MIGRATION_NAME = "180_audit_append_only_triggers.py"
EXPECTED_REVISION = '"180_audit_append_only_triggers"'
EXPECTED_DOWN_REVISION = '"179_custom_agent_whatsapp_enabled"'

REQUIRED_FUNCTIONS = [
    "audit_execution_metadata_block_update",
    "audit_execution_metadata_block_delete",
    "audit_execution_metadata_block_truncate",
]

REQUIRED_TRIGGERS = [
    ("audit_execution_metadata_block_update_trigger", "BEFORE UPDATE"),
    ("audit_execution_metadata_block_delete_trigger", "BEFORE DELETE"),
    ("audit_execution_metadata_block_truncate_trigger", "BEFORE TRUNCATE"),
]


def check() -> list[str]:
    violations: list[str] = []
    path = MIGRATIONS_DIR / MIGRATION_NAME

    if not path.exists():
        violations.append(
            f"[W1-006 part 2] Migration ausente: {path}\n"
            f"  Fix: alembic/versions/180_audit_append_only_triggers.py deve existir.\n"
            f"  Esta migration é canonical para enforcement append-only em audit_execution_metadata."
        )
        return violations

    src = path.read_text(encoding="utf-8")

    if EXPECTED_REVISION not in src:
        violations.append(
            f"[W1-006 part 2] revision_id incorreto em {MIGRATION_NAME}.\n"
            f"  Esperado: revision = {EXPECTED_REVISION}\n"
            f"  Fix: não renomear revision_id — quebra cadeia alembic."
        )

    if EXPECTED_DOWN_REVISION not in src:
        violations.append(
            f"[W1-006 part 2] down_revision incorreto em {MIGRATION_NAME}.\n"
            f"  Esperado: down_revision = {EXPECTED_DOWN_REVISION}\n"
            f"  Fix: não alterar a cadeia alembic — migration 180 vem após 179."
        )

    for fn in REQUIRED_FUNCTIONS:
        # Pattern: CREATE OR REPLACE FUNCTION <name>(
        if not re.search(rf"CREATE OR REPLACE FUNCTION\s+{re.escape(fn)}\s*\(", src):
            violations.append(
                f"[W1-006 part 2] Função canonical ausente: {fn}().\n"
                f"  Fix: migration deve criar função {fn} que faz RAISE EXCEPTION.\n"
                f"  Esta função enforça invariante append-only em audit_execution_metadata."
            )

    for trigger_name, timing in REQUIRED_TRIGGERS:
        if not re.search(
            rf"CREATE TRIGGER\s+{re.escape(trigger_name)}\s+{re.escape(timing)}",
            src,
        ):
            violations.append(
                f"[W1-006 part 2] Trigger canonical ausente: {trigger_name} {timing}.\n"
                f"  Fix: migration deve atachar trigger {trigger_name} ({timing}) em audit_execution_metadata.\n"
                f"  Sem este trigger, mutações destrutivas passam sem bloqueio."
            )

    # downgrade must drop all 3 triggers + 3 functions (idempotency)
    for fn in REQUIRED_FUNCTIONS:
        if f"DROP FUNCTION IF EXISTS {fn}" not in src:
            violations.append(
                f"[W1-006 part 2] downgrade() falta: DROP FUNCTION IF EXISTS {fn}().\n"
                f"  Fix: downgrade canonical deve fazer cleanup completo."
            )

    return violations


def main() -> int:
    violations = check()
    if violations:
        print("❌ check_audit_append_only_triggers FAILED:\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"\nTotal: {len(violations)} violation(s). "
            "Esta migration é canonical para integridade do audit log (LGPD Art 37 §1).\n"
            "Não remover/alterar sem aprovação textual explícita do Paulo.",
            file=sys.stderr,
        )
        return 1
    print("✅ check_audit_append_only_triggers OK · migration 180 canonical preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
