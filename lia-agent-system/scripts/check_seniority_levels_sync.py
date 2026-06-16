#!/usr/bin/env python3
"""Sensor — niveis de senioridade canonicos sincronizados back<->front.

FONTE UNICA: lia-agent-system/app/shared/seniority_levels.py
ESPELHO TS:  plataforma-lia/src/lib/compensation/seniority-levels.ts

Quebra (exit 1 com --blocking) se os ids/labels/ordem divergirem. Evita a
regressao que existia (PRV tinha 8 niveis, benefits tinha 10 com 'coordinator'):
duas listas hardcoded divergentes. Saida otimizada p/ LLM (instrucao de fix embutida).

Uso:
  python scripts/check_seniority_levels_sync.py            # warn-only (exit 0)
  python scripts/check_seniority_levels_sync.py --blocking # exit 1 em drift
"""
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[2]  # .../workspace
PY = WS / "lia-agent-system/app/shared/seniority_levels.py"
TS = WS / "plataforma-lia/src/lib/compensation/seniority-levels.ts"

_PAIR = re.compile(r'id"?\s*:\s*"([^"]+)"\s*,\s*"?label"?\s*:\s*"([^"]+)"')


def extract(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    i = text.find("CANONICAL_SENIORITY_LEVELS")
    if i < 0:
        raise SystemExit(f"[sensor] CANONICAL_SENIORITY_LEVELS nao encontrado em {path}")
    # Ancora no '= [' da atribuicao (evita os '[' das anotacoes de tipo
    # como list[dict[...]] em PY ou SeniorityLevel[] em TS).
    eq = text.find("= [", i)
    if eq < 0:
        raise SystemExit(f"[sensor] literal de array nao encontrado apos a const em {path}")
    start = text.find("[", eq)
    end = text.find("]", start)  # entradas {...} nao contem ']', logo o 1o fecha o array
    block = text[start:end]
    pairs = _PAIR.findall(block)
    if not pairs:
        raise SystemExit(f"[sensor] 0 niveis extraidos de {path} — regex/extracao quebrada (NAO e drift).")
    return pairs


def main() -> int:
    blocking = "--blocking" in sys.argv
    py = extract(PY)
    ts = extract(TS)
    if py == ts:
        print(f"[sensor] OK — {len(py)} niveis canonicos sincronizados (PY == TS).")
        return 0

    print("[sensor] DRIFT entre niveis canonicos PY e TS:")
    print(f"  PY ({PY.relative_to(WS)}): {py}")
    print(f"  TS ({TS.relative_to(WS)}): {ts}")
    py_ids = [p[0] for p in py]
    ts_ids = [t[0] for t in ts]
    only_py = [x for x in py_ids if x not in ts_ids]
    only_ts = [x for x in ts_ids if x not in py_ids]
    if only_py:
        print(f"  -> So em PY: {only_py} — adicione em {TS.relative_to(WS)}")
    if only_ts:
        print(f"  -> So em TS: {only_ts} — adicione em {PY.relative_to(WS)}")
    if py_ids == ts_ids:
        print("  -> ids batem mas labels/ordem divergem — alinhe os labels.")
    print("  Fix: as duas listas CANONICAL_SENIORITY_LEVELS devem ser identicas (ids, labels, ordem).")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
