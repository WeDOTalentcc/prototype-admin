"""Sensor canonical — detecta leak de test data em prod via regex no título de vagas.

Sprint 1.B Task 1.B Phase 4 (2026-05-25).

INCIDENT 2026-05-22 (driver desta sensor):
  8 vagas criadas com title 'Sensor Harness Roundtrip Test' em company_id
  test fixture (00000000-0000-4000-a000-000000000001) entre 17:06-18:58.
  Origem: tests/contract/test_jobvacancy_roundtrip.py rodou contra
  LIA_BACKEND_URL=http://127.0.0.1:8001 (prod-local Replit canonical) com
  cleanup `try/except Exception: pass` silenciosamente falhando.

GUIDE COMPUTACIONAL (harness-engineering):
  Pre-commit + CI hourly query → falha se job_vacancies tem row matching
  regex de test pattern. Cleanup é responsabilidade do test runner, mas
  esta sensor é defense-in-depth quando cleanup falha.

Padrões detectados (case-insensitive):
  - 'sensor.*roundtrip'   — incident driver
  - 'sensor.*harness'      — variantes
  - 'smoke.*test'          — pytest smoke tests
  - 'harness.*test'        — outros harness sensors
  - 'fixture.*test'        — fixture leaks
  - 'pytest.*'             — typos óbvios

Quando achar matches, sensor sai com exit code 1 e mensagem que diz EXATAMENTE
o que deletar (queries SQL + IDs).

Modos:
  --warn-only    Exit 0, só imprime (default pra integração gradual)
  --blocking     Exit 1 se encontrar (CI gate)

Uso CI:
  python scripts/check_test_pattern_in_vacancy_names.py --blocking

Uso cron:
  python scripts/check_test_pattern_in_vacancy_names.py --blocking | tee -a logs/test_leak_sensor.log
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from textwrap import dedent

import psycopg2


TEST_PATTERNS = [
    r"sensor.*roundtrip",
    r"sensor.*harness",
    r"smoke.*test",
    r"harness.*test",
    r"fixture.*test",
    r"^pytest",
    r"^test\s",
    r"^\[test\]",
]

# Test fixture company UUID canonical (all-zeros padrão).
# Rows com este company_id são auto-elegíveis pra cleanup.
TEST_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"


def fetch_suspicious_rows(conn) -> list[tuple]:
    """Query job_vacancies por título matching qualquer test pattern.

    Returns list of (id, title, company_id, status, source, created_at).
    """
    cur = conn.cursor()
    pattern_or = "|".join(f"({p})" for p in TEST_PATTERNS)
    cur.execute(
        """
        SELECT id::text, title, company_id, status, source, created_at::text
        FROM job_vacancies
        WHERE title ~* %s
        ORDER BY created_at DESC
        """,
        (pattern_or,),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def format_findings(rows: list[tuple]) -> str:
    """Format output para consumo LLM/human."""
    if not rows:
        return "✅ Nenhuma vaga com test pattern encontrada.\n"

    lines = [
        f"🛑 {len(rows)} vaga(s) com test pattern encontrada(s):",
        "",
    ]
    for row in rows:
        vid, title, cid, status, source, created = row
        cid_marker = "🧪 test_fixture" if cid == TEST_COMPANY_UUID else f"⚠ company={cid[:8]}"
        lines.append(
            f"  {vid[:8]} | {title!r} | {status} | source={source} | {cid_marker} | {created}"
        )
    lines.append("")
    lines.append("FIX recomendado:")
    lines.append("")
    lines.append("  1. Verificar manualmente cada row se é realmente test artifact")
    lines.append("  2. Backup SQL dump (audit trail) antes de delete")
    lines.append("  3. SQL canonical DELETE com triple guard:")
    lines.append("")
    test_ids = [r[0] for r in rows if r[2] == TEST_COMPANY_UUID]
    if test_ids:
        ids_quoted = ",\n        ".join(f"'{i}'" for i in test_ids)
        lines.append(
            dedent(
                f"""\
                  DELETE FROM job_vacancies
                  WHERE id IN (
                    {ids_quoted}
                  )
                  AND company_id = '{TEST_COMPANY_UUID}'
                  AND title ~* '({pattern_or_short()})';

                """
            ).rstrip()
        )
    lines.append("  4. Adicionar `export LIA_ENV=staging` no env do test runner")
    lines.append("     (vide tests/contract/conftest.py guard)")
    return "\n".join(lines) + "\n"


def pattern_or_short() -> str:
    return "|".join(TEST_PATTERNS[:4])  # primeiros 4 mais comuns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 se encontrar matches (modo CI gate)",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 sempre, só imprime (default)",
    )
    args = parser.parse_args()

    blocking = args.blocking and not args.warn_only

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("⚠ DATABASE_URL não setado — pulando sensor")
        return 0

    try:
        conn = psycopg2.connect(db_url)
    except Exception as e:
        print(f"❌ Falha conectar DB: {e}", file=sys.stderr)
        return 0 if not blocking else 1

    try:
        rows = fetch_suspicious_rows(conn)
    finally:
        conn.close()

    print(format_findings(rows))

    if rows and blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
