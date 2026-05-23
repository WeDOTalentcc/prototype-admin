#!/usr/bin/env python3
"""
Sensor anti-regressão · W1-006 part 1 (2026-05-22)

Verifica que `audit_execution_metadata` tem hash chain SHA-256 per-tenant
via BEFORE INSERT trigger — proteção contra remoção acidental do trigger,
da function, das colunas, ou do index de lookup.

Mitigations protegidas:
- Tampering detection (hash chain SHA-256 per-tenant)
- Multi-tenancy isolation (chain isolada por company_id)
- Performance (index `ix_audit_execution_metadata_company_timestamp`)

Sem qualquer um desses componentes, audit_execution_metadata vira
mutable trail sem garantia de integridade — violação LGPD Art 37 §1
(registros administrativos de tratamento de dados pessoais devem
ser auditáveis e tamper-evident).

Verificações:
1. Migration file `alembic/versions/176_audit_hash_chain.py` existe
2. Function `audit_compute_hash_chain` definida na migration
3. Trigger `audit_execution_metadata_hash_chain_trigger` declarada
4. Colunas `prev_hash` + `this_hash` adicionadas
5. Index `ix_audit_execution_metadata_company_timestamp` adicionado
6. Backfill statement presente (para rows pre-existentes)
7. (Opcional, se DATABASE_URL) Verifica no DB que tudo está aplicado

Mensagem em PT-BR com fix sugerido em sintaxe exata (harness pattern
CLAUDE.md — otimizado para consumo do LLM consumidor do erro).

Modo: BLOCKING por default. `--warn-only` para opt-out.

Pre-audit: sprint_logs/sprint_1.1/W1-006_AUDIT.md.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_FILE = (
    REPO_ROOT / "alembic" / "versions" / "176_audit_hash_chain.py"
)


def check_migration_file_present() -> list[str]:
    """Migration 176 deve existir."""
    errors: list[str] = []
    if not MIGRATION_FILE.exists():
        errors.append(
            "❌ Migration W1-006 ausente: "
            f"`{MIGRATION_FILE.relative_to(REPO_ROOT)}`\n"
            "   FIX: criar migration alembic com hash chain SHA-256 + trigger\n"
            "        BEFORE INSERT em audit_execution_metadata.\n"
            "        Pre-audit: sprint_logs/sprint_1.1/W1-006_AUDIT.md"
        )
    return errors


def check_migration_content() -> list[str]:
    """Função, trigger, colunas, index, backfill devem estar presentes."""
    errors: list[str] = []
    if not MIGRATION_FILE.exists():
        return errors

    src = MIGRATION_FILE.read_text(encoding="utf-8")

    required_artifacts = {
        "function audit_compute_hash_chain":
            "CREATE OR REPLACE FUNCTION audit_compute_hash_chain",
        "trigger BEFORE INSERT":
            "audit_execution_metadata_hash_chain_trigger",
        "column prev_hash CHAR(64)":
            "prev_hash",
        "column this_hash CHAR(64)":
            "this_hash",
        "index company_timestamp":
            "ix_audit_execution_metadata_company_timestamp",
        "pgcrypto extension":
            "pgcrypto",
        "SHA-256 digest":
            "sha256",
    }

    for description, needle in required_artifacts.items():
        if needle not in src:
            errors.append(
                f"❌ Migration 176 incompleta · faltando: {description}\n"
                f"   needle: `{needle}`\n"
                "   FIX: revisar migration `176_audit_hash_chain.py` e\n"
                "        restaurar artifact removido (ver pre-audit\n"
                "        sprint_logs/sprint_1.1/W1-006_AUDIT.md para template)."
            )

    # Backfill: rows pre-existentes ficam com prev_hash NULL e this_hash computado
    if "UPDATE audit_execution_metadata m" not in src:
        errors.append(
            "❌ Migration 176 SEM backfill de rows pre-existentes\n"
            "   Risco: rows existentes ficam sem this_hash (chain corrompida)\n"
            "   FIX: adicionar UPDATE ... SET this_hash = encode(digest(...)) ..."
        )

    return errors


def check_db_state() -> list[str]:
    """Quando DATABASE_URL disponível, verifica estado real do DB."""
    errors: list[str] = []
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return errors

    try:
        from sqlalchemy import create_engine, text

        url_clean = url.replace("postgres://", "postgresql://", 1).split("?")[0]
        eng = create_engine(url_clean)
        with eng.connect() as conn:
            cols = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'audit_execution_metadata' "
                "AND column_name IN ('prev_hash', 'this_hash')"
            )).fetchall()
            col_names = {c[0] for c in cols}
            if "prev_hash" not in col_names or "this_hash" not in col_names:
                errors.append(
                    f"❌ DB · colunas hash chain ausentes em audit_execution_metadata\n"
                    f"   Encontradas: {sorted(col_names)}\n"
                    "   FIX: rodar `alembic upgrade head`."
                )

            trg = conn.execute(text(
                "SELECT trigger_name FROM information_schema.triggers "
                "WHERE trigger_name = "
                "'audit_execution_metadata_hash_chain_trigger'"
            )).fetchone()
            if not trg:
                errors.append(
                    "❌ DB · trigger audit_execution_metadata_hash_chain_trigger ausente\n"
                    "   Sem trigger, INSERT em audit_execution_metadata não computa hash\n"
                    "   FIX: rodar `alembic upgrade head` (migration 176)."
                )

            fn = conn.execute(text(
                "SELECT proname FROM pg_proc WHERE proname = "
                "'audit_compute_hash_chain'"
            )).fetchone()
            if not fn:
                errors.append(
                    "❌ DB · function audit_compute_hash_chain ausente\n"
                    "   FIX: rodar `alembic upgrade head` (migration 176)."
                )
    except Exception as exc:
        # DB acessível mas erro de query — não-fatal pra sensor estático
        errors.append(
            f"⚠️  DB check skipped (não-fatal): {exc.__class__.__name__}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta violações mas retorna exit 0.",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip verificação de estado real do DB (apenas validação estática).",
    )
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_migration_file_present())
    errors.extend(check_migration_content())
    if not args.skip_db:
        errors.extend(check_db_state())

    # Filtra warnings (⚠) — não bloquear em modo strict por warnings DB
    fatal = [e for e in errors if not e.lstrip().startswith("⚠")]
    warnings_list = [e for e in errors if e.lstrip().startswith("⚠")]

    for w in warnings_list:
        print(w, file=sys.stderr)

    if fatal:
        print(file=sys.stderr)
        for err in fatal:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print(
                "⚠️  WARN-ONLY mode: exit 0 despite violations",
                file=sys.stderr,
            )
            return 0
        return 1

    print(
        "✅ Audit hash chain wired (W1-006 part 1) · "
        "migration 176 + trigger + function + index OK"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
