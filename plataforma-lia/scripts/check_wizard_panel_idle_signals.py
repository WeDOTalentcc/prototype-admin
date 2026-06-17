#!/usr/bin/env python3
"""Canonical sensor — wizard panels MUST read backend awaiting_*_input signals.

Background (2026-05-29):
    Bug historico no wizard de criacao de vaga: JdEnrichmentPanel ignorava
    awaiting_jd_input (sinal emitido pelo jd_enrichment_node quando o
    recrutador disse "vamos abrir uma vaga" sem cole de JD ainda). Painel
    renderizava "Critico 0/100" + JdLoadingState com timer 30s ("demorando"),
    confundindo o usuario que estava sendo solicitado a colar a JD no chat.

    Defeito de harness (Hashimoto): produtor emitia o sinal correto, consumidor
    nao lia. Saga A-G de fixes (commits dd2586dc..c288be976) tratou loop bugs
    no jd_gate mas nao tratou idle UX.

Contrato canonical:
    1. Backend (lia-agent-system/app/domains/job_creation/nodes/*.py) pode
       emitir 'awaiting_<stage>_input: True' em build_ws_stage_payload.data
       quando o stage esta em idle (aguardando user input substancial).
    2. Frontend panel correspondente (plataforma-lia/src/components/unified-chat/
       wizard/panels/<Stage>Panel.tsx) DEVE ler esse campo e renderizar idle
       state explicito — sem badge de qualidade, sem timer de loading, sem
       mensagem "demorando".

Mapeamento canonical sinal -> panel:
    awaiting_jd_input  ->  JdEnrichmentPanel.tsx

Como adicionar novo signal (futuro):
    1. Backend emite "awaiting_<X>_input": True em build_ws_stage_payload
    2. Adicione entry em SIGNAL_TO_PANEL abaixo
    3. Adicione handler 'if (d.awaiting_<X>_input) return <...AwaitingInputState />'
       no panel correspondente
    4. Adicione teste em panels/__tests__/<X>Panel.test.tsx (template:
       JdEnrichmentPanel.test.tsx describe "canonical idle state")

Output (otimizado pra LLM consumer):
    - Cada violation: [tipo] sinal X emitido sem handler no panel Y
    - Fix sugerido inline com o pattern exato

Wired em CI: .github/workflows/frontend-ci.yml step "wizard panel idle signals"
(warn-only enquanto baseline = 0; promover a blocking quando estavel).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NODES_DIR = ROOT / "lia-agent-system" / "app" / "domains" / "job_creation" / "nodes"
PANELS_DIR = ROOT / "plataforma-lia" / "src" / "components" / "unified-chat" / "wizard" / "panels"

# Mapping signal -> panel filename. Add new entries when backend introduces
# new awaiting_<X>_input signals (see module docstring).
SIGNAL_TO_PANEL: dict[str, str] = {
    "awaiting_jd_input": "JdEnrichmentPanel.tsx",
}

# Regex to find backend emission sites: "awaiting_X_input": True (any spacing).
BACKEND_SIGNAL_RE = re.compile(r'"(awaiting_[a-z_]+_input)"\s*:\s*True')


def find_backend_signals() -> dict[str, list[tuple[Path, int]]]:
    """Walk nodes/*.py, return {signal_name: [(path, line), ...]}."""
    out: dict[str, list[tuple[Path, int]]] = {}
    if not NODES_DIR.exists():
        return out
    for py in NODES_DIR.glob("*.py"):
        for lineno, line in enumerate(py.read_text().splitlines(), 1):
            for m in BACKEND_SIGNAL_RE.finditer(line):
                out.setdefault(m.group(1), []).append((py, lineno))
    return out


def panel_handles_signal(panel_path: Path, signal: str) -> bool:
    """Return True if panel reads the signal AND uses it in a conditional."""
    if not panel_path.exists():
        return False
    src = panel_path.read_text()
    if signal not in src:
        return False
    # Look for conditional access patterns: if (d.X / X ? <... / d.X) / ?<...X>
    handler_re = re.compile(
        rf"(if\s*\(\s*[^)]*\.{signal}|\?\s*<.*{signal}|\.{signal}\s*\)|{signal}\s*\?\s*<)",
        re.DOTALL,
    )
    return bool(handler_re.search(src))


def main(argv: list[str]) -> int:
    blocking = "--blocking" in argv
    json_out = "--json" in argv

    backend_signals = find_backend_signals()
    violations: list[str] = []
    matched: list[str] = []

    for signal, sites in sorted(backend_signals.items()):
        emit_locs = ", ".join(f"{p.relative_to(ROOT)}:{ln}" for p, ln in sites)
        panel_name = SIGNAL_TO_PANEL.get(signal)
        if not panel_name:
            violations.append(
                f"[SIGNAL] {signal} emitido pelo backend ({emit_locs}) mas NAO esta "
                f"em SIGNAL_TO_PANEL deste script.\n"
                f"  -> Fix: adicione mapping {signal!r}: \"<X>Panel.tsx\" em "
                f"plataforma-lia/scripts/check_wizard_panel_idle_signals.py"
            )
            continue
        panel_path = PANELS_DIR / panel_name
        if not panel_handles_signal(panel_path, signal):
            violations.append(
                f"[PANEL] {panel_name} NAO trata {signal} (emitido em {emit_locs}).\n"
                f"  -> Fix: adicione early-return no panel:\n"
                f"     if (d.{signal}) {{ return <...AwaitingInputState message={{d.message}} /> }}"
            )
        else:
            matched.append(f"OK {signal} -> {panel_name}")

    for signal in SIGNAL_TO_PANEL:
        if signal not in backend_signals:
            violations.append(
                f"[DEAD] mapping {signal!r} -> {SIGNAL_TO_PANEL[signal]!r} no script, "
                f"mas backend nao emite mais esse sinal.\n"
                f"  -> Fix: remova mapping de check_wizard_panel_idle_signals.py "
                f"(ou restaure emissao em lia-agent-system/.../nodes/)"
            )

    if json_out:
        import json
        print(json.dumps({"violations": violations, "matched": matched}, indent=2))
    else:
        for v in violations:
            print(v)
            print()
        for m in matched:
            print(m)
        print()
        print(f"Total: {len(violations)} violations, {len(matched)} OK")

    if violations and blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
