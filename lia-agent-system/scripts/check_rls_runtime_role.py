#!/usr/bin/env python3
"""Diagnostico de harness (audit C8/#7 2026-06-05): o RLS protege de verdade?

Postgres IGNORA Row-Level Security para conexoes superuser. Se o app conecta como
superuser (hoje: 'postgres'), TODO o RLS do projeto (068 deny-by-default,
job_vacancies, etc.) esta INERTE em runtime — nao protege contra as queries do
proprio app. A protecao multi-tenant REAL e a camada de aplicacao:
ownership gates (ex: JobVacancyCrudRepository.owned_by_company) + _require_company_id.

Uso:
    python3 scripts/check_rls_runtime_role.py           # diagnostico (exit 0)
    python3 scripts/check_rls_runtime_role.py --block   # exit 1 se role e superuser

Mensagem otimizada pra consumo LLM (instrucao de fix embutida). Sem DATABASE_URL,
pula (exit 0).
"""
from __future__ import annotations

import os
import sys


def format_verdict(
    current_user: str,
    is_superuser: bool,
    rls_tables: list[str],
    block: bool = False,
) -> tuple[int, str]:
    """Funcao pura: decide exit code + mensagem a partir do role/tabelas.

    Separada de I/O pra ser testavel sem DB (sensor computacional).
    """
    if is_superuser:
        tables = ", ".join(sorted(rls_tables)) if rls_tables else "(nenhuma detectada)"
        msg = (
            f"[rls-role] ATENCAO: o app conecta como '{current_user}' (SUPERUSER). "
            "Postgres IGNORA Row-Level Security para superusers — logo TODO o RLS do "
            "projeto esta INERTE em runtime, incluindo tabelas com RLS habilitada: "
            f"{tables}. "
            "A protecao multi-tenant REAL e a camada de aplicacao: ownership gates "
            "(ex: JobVacancyCrudRepository.owned_by_company) + _require_company_id nos "
            "repos. NUNCA confie em RLS nem em comentarios 'RLS-EXEMPT: transitive via "
            "...' como protecao enquanto o app for superuser. RLS so ativa com cliente "
            "NAO-superuser (role lia_app / Rails) usando SET app.company_id. "
            "-> Fix de fundo (epico): migrar o app pra conectar como role nao-superuser."
        )
        return (1 if block else 0, msg)
    return (
        0,
        f"[rls-role] OK: '{current_user}' nao e superuser — RLS e enforced em runtime.",
    )


async def _amain(block: bool) -> int:
    url = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")
    if not url:
        print("[rls-role] DATABASE_URL ausente — diagnostico pulado.")
        return 0
    import asyncpg  # lazy: nao exigir no import (testes da funcao pura)

    conn = await asyncpg.connect(url)
    try:
        row = await conn.fetchrow(
            "SELECT current_user AS u, "
            "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user) AS s"
        )
        rls_rows = await conn.fetch(
            "SELECT relname FROM pg_class WHERE relrowsecurity AND relkind = 'r'"
        )
        tables = [r["relname"] for r in rls_rows]
        code, msg = format_verdict(row["u"], bool(row["s"]), tables, block=block)
        print(msg)
        return code
    finally:
        await conn.close()


def main() -> None:
    import argparse
    import asyncio

    ap = argparse.ArgumentParser(description="Diagnostico de role/RLS runtime")
    ap.add_argument(
        "--block",
        action="store_true",
        help="exit 1 se o app conecta como superuser (RLS inerte)",
    )
    args = ap.parse_args()
    sys.exit(asyncio.run(_amain(args.block)))


if __name__ == "__main__":
    main()
