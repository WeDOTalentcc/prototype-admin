"""Backfill `candidates.cpf_hash` / `candidates.phone_hash` for existing rows.

Fase 1 (2026-06-10, ADR-LGPD-002 resolve-then-strip). A migration 259 adicionou as
colunas de hash indexadas (SHA-256 do CPF/telefone normalizado digits-only) que
permitem ao chat resolver candidato POR identificador sem vazar o identificador cru
ao LLM vendor. Linhas gravadas antes desta feature ficam com hash NULL — este script
recalcula a partir do valor decriptado.

Reusa o produtor canonico de hash (Candidate.cpf_hash_for / phone_hash_for) — NAO
duplica logica de normalizacao/hash. Le o valor via hybrid_property (`c.cpf`/`c.phone`)
que decripta transparentemente (Fernet) ou retorna plaintext de linhas pre-migracao.

Idempotente:
  * Reprocessar recomputa o MESMO hash (deterministico) — inofensivo.
  * Falha individual e logada e NAO interrompe o lote (fail-loud, nao fail-silent:
    conta e reporta no final).
  * Processa por cursor de PK (id) em lotes.

Uso:
    cd lia-agent-system && python scripts/backfill_candidate_identifier_hash.py

Variaveis opcionais:
  BACKFILL_BATCH_SIZE   tamanho do lote por commit (default 200)
  BACKFILL_DRY_RUN      "1" para apenas inspecionar o PRIMEIRO lote sem UPDATE
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_candidate_identifier_hash")

BATCH_SIZE = int(os.environ.get("BACKFILL_BATCH_SIZE", "200"))
DRY_RUN = os.environ.get("BACKFILL_DRY_RUN", "").strip().lower() in ("1", "true", "yes")


async def main() -> None:
    os.environ.setdefault("IS_DEVELOPMENT", "true")
    from app.core.database import AsyncSessionLocal
    from app.models.candidate import Candidate

    total = 0
    updated_cpf = 0
    updated_phone = 0
    failures = 0
    last_id = None

    logger.info(
        "Backfill cpf_hash/phone_hash start (batch=%d, dry_run=%s)", BATCH_SIZE, DRY_RUN
    )

    while True:
        async with AsyncSessionLocal() as session:
            stmt = select(Candidate).order_by(Candidate.id).limit(BATCH_SIZE)
            if last_id is not None:
                stmt = stmt.where(Candidate.id > last_id)
            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                break

            batch_changed = 0
            for c in rows:
                last_id = c.id
                total += 1
                try:
                    # hybrid props decrypt transparently (or return plaintext pre-migration)
                    cpf_val = c.cpf
                    phone_val = c.phone
                    want_cpf = Candidate.cpf_hash_for(cpf_val) if cpf_val else None
                    want_phone = Candidate.phone_hash_for(phone_val) if phone_val else None

                    if want_cpf and c.cpf_hash != want_cpf:
                        if not DRY_RUN:
                            c.cpf_hash = want_cpf
                        updated_cpf += 1
                        batch_changed += 1
                    if want_phone and c.phone_hash != want_phone:
                        if not DRY_RUN:
                            c.phone_hash = want_phone
                        updated_phone += 1
                        batch_changed += 1
                except Exception as exc:  # fail-loud per row, continue batch
                    failures += 1
                    logger.error(
                        "Row %s hash backfill failed (continuing): %s", c.id, exc
                    )

            if DRY_RUN:
                logger.info(
                    "[DRY_RUN] First batch inspected: %d rows, would update "
                    "cpf=%d phone=%d. Stopping (dry-run does not paginate).",
                    len(rows), updated_cpf, updated_phone,
                )
                break

            if batch_changed:
                await session.commit()
            logger.info(
                "Batch done up to id=%s (total=%d, cpf=%d, phone=%d, failures=%d)",
                last_id, total, updated_cpf, updated_phone, failures,
            )

    logger.info(
        "Backfill COMPLETE: scanned=%d, cpf_hash set=%d, phone_hash set=%d, failures=%d",
        total, updated_cpf, updated_phone, failures,
    )
    if failures:
        logger.warning(
            "%d row(s) failed — NOT silent. Investigue antes de considerar completo.",
            failures,
        )


if __name__ == "__main__":
    asyncio.run(main())
