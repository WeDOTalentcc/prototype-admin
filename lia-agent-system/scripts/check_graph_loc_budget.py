#!/usr/bin/env python3
"""Sensor LOC budget para graph.py (PR-9 / F-3.1 sub-sprint A).

Background: graph.py monolito (5514 LOC baseline pre-PR-9). PR-9 extraiu o
pattern ``ws_stage_payload`` para helper canonical
``app/domains/job_creation/helpers/ws_payload_builder.py``, reduzindo o LOC
do graph.py.

Target eventual: <=1500 LOC pos-refactor completo (PR-10 split nodes em
arquivos separados, ex.: ``app/domains/job_creation/nodes/jd_enrichment_node.py``).

Modo atual: warn-only. Promover para BLOCKING quando PR-10 completar.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve canonical path relativo ao script (vive em scripts/).
GRAPH_PATH = Path(__file__).resolve().parent.parent / "app" / "domains" / "job_creation" / "graph.py"

# Budget pos-PR-9. Ajustar quando PR-10 (split nodes) completar.
TARGET_LOC = 5300
WARN_THRESHOLD = 5400  # 100 LOC margem
HARD_LIMIT = 5550  # +50 sobre baseline atual (5500 pos-PR-9)


def main() -> int:
    if not GRAPH_PATH.is_file():
        print(f"[graph_loc_budget] ERROR: {GRAPH_PATH} nao encontrado")
        return 2

    loc = sum(1 for _ in GRAPH_PATH.open())
    print(
        f"[graph_loc_budget] graph.py LOC: {loc} "
        f"(target <={TARGET_LOC}, warn >{WARN_THRESHOLD}, hard >{HARD_LIMIT})"
    )

    if loc > HARD_LIMIT:
        print(
            f"[graph_loc_budget] HARD LIMIT excedido ({loc} > {HARD_LIMIT}). "
            "PR-10 (split nodes em arquivos separados) deve seguir antes de "
            "adicionar mais codigo aqui."
        )
        if "--blocking" in sys.argv:
            return 1
        return 0

    if loc > WARN_THRESHOLD:
        print(
            f"[graph_loc_budget] WARN: {loc} > {WARN_THRESHOLD}. "
            "Considere extrair mais helpers ou aplicar PR-10."
        )
        return 0

    print(f"[graph_loc_budget] OK ({loc} <= {WARN_THRESHOLD})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
