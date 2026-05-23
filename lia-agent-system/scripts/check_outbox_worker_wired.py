#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-030 (2026-05-23)

Verifica que `OutboxDrainerWorker.start()` e `.stop()` estão wirados no
lifespan de `app/main.py`. Sem worker drenando, `ai_consumption_outbox`
table acumula payloads pendentes para sempre (silent data loss em audit
de consumo de LLM).

Pattern violação:
- Remover `await get_outbox_worker().start()` do lifespan startup
- Remover `await get_outbox_worker().stop()` do shutdown
- Deletar singleton `get_outbox_worker()` em ai_consumption_outbox_worker.py

Mensagem PT-BR + fix sugerido. Modo: BLOCKING por default.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_FILE = REPO_ROOT / "app" / "main.py"
WORKER_FILE = REPO_ROOT / "app" / "shared" / "observability" / "ai_consumption_outbox_worker.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []

    if not WORKER_FILE.exists():
        errors.append(
            f"❌ {WORKER_FILE.relative_to(REPO_ROOT)} ausente\n"
            "   FIX: restaurar OutboxDrainerWorker class + get_outbox_worker() singleton"
        )
    else:
        worker_src = WORKER_FILE.read_text()
        if "class OutboxDrainerWorker" not in worker_src:
            errors.append(
                "❌ `OutboxDrainerWorker` class ausente em ai_consumption_outbox_worker.py"
            )
        if "def get_outbox_worker" not in worker_src:
            errors.append(
                "❌ `get_outbox_worker()` singleton ausente em ai_consumption_outbox_worker.py"
            )

    if not MAIN_FILE.exists():
        errors.append("❌ app/main.py ausente")
    else:
        main_src = MAIN_FILE.read_text()
        if "get_outbox_worker().start()" not in main_src:
            errors.append(
                "❌ `OutboxDrainerWorker.start()` NÃO wirado em app/main.py lifespan\n"
                f"   File: {MAIN_FILE.relative_to(REPO_ROOT)}\n"
                "   Risco: ai_consumption_outbox acumula payloads sem drenagem\n"
                "          → silent data loss em audit consumo LLM (LGPD/SOX gap)\n"
                "   FIX em lifespan() após register_react_agents():\n"
                "       from app.shared.observability.ai_consumption_outbox_worker import (\n"
                "           get_outbox_worker,\n"
                "       )\n"
                "       await get_outbox_worker().start()"
            )
        if "get_outbox_worker().stop()" not in main_src:
            errors.append(
                "❌ `OutboxDrainerWorker.stop()` NÃO wirado em shutdown\n"
                f"   File: {MAIN_FILE.relative_to(REPO_ROOT)}\n"
                "   Risco: graceful drain do último lote skipped\n"
                "   FIX em shutdown section após rabbitmq_producer.close():\n"
                "       await get_outbox_worker().stop()"
            )

    if errors:
        print(f"W3-030 outbox worker · {len(errors)} violation(s):", file=sys.stderr)
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            return 0
        return 1

    print("✅ OutboxDrainerWorker wired (W3-030) · start()+stop() em lifespan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
