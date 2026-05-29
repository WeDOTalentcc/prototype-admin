#!/usr/bin/env python3
"""Agent Studio Fase 2.5 — Onda C1.3 (registrado 2026-05-29).

Sensor warn-only: garante que todo trigger_mode event-based tem um publisher
correspondente que emite o evento no platform.events.

Motivacao (AUDIT 4): `validate_trigger_mode("job", "on_apply")` aceitava o
trigger, mas NENHUM publisher emitia `candidate_applied` -> silent contract
break. Agentes com trigger event-based nunca disparavam porque o evento nunca
era publicado.

Mapeamento canonical trigger_mode -> event_type (espelha o consumer C1.2 +
a matriz de app.shared.trigger_mode_validation):

  on_apply                                          -> candidate_applied
  on_enter_stage / on_exit_stage / on_stage_change  -> stage_changed
  (on_stuck_in_stage e detectado por SCHEDULER, nao por evento -> isento aqui)

Heuristica de deteccao de publisher: procura em app/ por uma instanciacao do
Event canonical (CandidateAppliedEvent / StageChangedEvent) OU um
publish_platform_event com event_type literal correspondente. Detecta o
contrato "evento e realmente emitido em algum lugar do codigo".

Uso:
  python3 scripts/check_platform_events_published.py            # warn-only (exit 0)
  python3 scripts/check_platform_events_published.py --blocking # exit 1 se gap

Output otimizado pra LLM: cada gap lista o trigger_mode orfao + o evento que
falta publicar + sugestao de fix.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Resolve project root: scripts/ esta dentro de lia-agent-system/.
ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"

# trigger_mode event-based -> (event_type flat, classe Event canonical)
# on_stuck_in_stage NAO entra: detectado por scheduler, nao por evento.
EVENT_BASED_TRIGGERS: dict[str, tuple[str, str]] = {
    "on_apply": ("candidate_applied", "CandidateAppliedEvent"),
    "on_enter_stage": ("stage_changed", "StageChangedEvent"),
    "on_exit_stage": ("stage_changed", "StageChangedEvent"),
    "on_stage_change": ("stage_changed", "StageChangedEvent"),
}


def _iter_py_files():
    for p in APP_DIR.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _build_corpus() -> str:
    """Concatena o conteudo de todos os .py de app/ (busca textual barata)."""
    chunks = []
    for p in _iter_py_files():
        try:
            chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(chunks)


def _publisher_exists(corpus: str, event_type: str, event_cls: str) -> bool:
    """True se o evento e emitido em algum lugar (instancia classe OU event_type literal).

    Exclui a propria definicao da classe (em platform_events.py) e este sensor.
    """
    # Instanciacao da classe Event canonical: `CandidateAppliedEvent(` fora da
    # definicao `class CandidateAppliedEvent(`.
    inst_pattern = re.compile(rf"(?<!class ){re.escape(event_cls)}\s*\(")
    if inst_pattern.search(corpus):
        return True
    # publish_platform_event com event_type literal `"candidate_applied"`.
    literal_pattern = re.compile(
        rf'event_type\s*=\s*["\']{re.escape(event_type)}["\']'
    )
    # Conta ocorrencias FORA da definicao default da classe (que tambem usa
    # event_type = "candidate_applied"). Se houver >= 2 ocorrencias, ha uso
    # alem da definicao. Se houver 1, e so a definicao -> nao conta como publish.
    if len(literal_pattern.findall(corpus)) >= 2:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sensor: trigger_modes event-based tem publisher correspondente."
    )
    parser.add_argument(
        "--blocking", action="store_true",
        help="Exit 1 se houver gap (default: warn-only exit 0).",
    )
    args = parser.parse_args()

    corpus = _build_corpus()

    gaps: list[tuple[str, str, str]] = []
    checked: set[str] = set()
    for trigger_mode, (event_type, event_cls) in EVENT_BASED_TRIGGERS.items():
        key = event_type
        if key in checked:
            # Ja validamos esse event_type via outro trigger_mode (stage_changed
            # cobre 3 modes). Evita ruido.
            continue
        if not _publisher_exists(corpus, event_type, event_cls):
            gaps.append((trigger_mode, event_type, event_cls))
        else:
            checked.add(key)

    print("🔍 C1.3 — publishers de eventos event-based")
    print(f"   App dir: {APP_DIR}")
    print(f"   trigger_modes event-based: {sorted(EVENT_BASED_TRIGGERS.keys())}\n")

    if not gaps:
        print("   ✅ Todos os event_types event-based tem publisher correspondente.")
        for tm, (et, ec) in EVENT_BASED_TRIGGERS.items():
            print(f"      - {tm:18s} -> {et} (via {ec})")
        return 0

    print("   ❌ GAPS detectados (trigger_mode aceito mas evento NUNCA publicado):\n")
    for trigger_mode, event_type, event_cls in gaps:
        print(f"      - trigger_mode '{trigger_mode}' precisa do evento '{event_type}'")
        print(f"        → Fix: emitir {event_cls}(...) via publish_platform_event")
        print(f"          no ponto nativo onde a acao ocorre (apply / stage change).")
        print(f"          Caso contrario, agentes com trigger_mode='{trigger_mode}'")
        print(f"          NUNCA disparam (silent contract break — AUDIT 4).\n")

    mode = "BLOCKING" if args.blocking else "warn-only"
    print(f"   Modo: {mode}.")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
