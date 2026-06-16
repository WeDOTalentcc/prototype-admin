"""
Sensor canonical — agent_chat_ws envia thread_id no payload wizard_stage.

Onda 2 do PLAN_FIX_wizard_memory_loss (defense-in-depth do P0-C).

RED pre-Onda-2: handler `wizard_session_canonical` envia evento WS
`wizard_stage` SEM thread_id explicito. Cliente nao consegue persistir.

Disciplinas: TDD-IA red-green-refactor + harness-engineering (sensor
estrutural via regex sobre source) + canonical-fix.
"""
from __future__ import annotations

import os
import re

SRC_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "app", "api", "v1", "agent_chat_ws.py",
)

START_MARKER = 'source="wizard_session_canonical"'
END_MARKER = "_wizard_canonical_handled = True"


def _src() -> str:
    with open(SRC_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _wizard_canonical_send_block() -> str:
    """Extrai bloco que envia evento wizard_stage no canonical path."""
    src = _src()
    start = src.find(START_MARKER)
    end = src.find(END_MARKER, start) if start != -1 else -1
    assert start != -1, "start marker (source=wizard_session_canonical) nao encontrado"
    assert end != -1, "end marker (_wizard_canonical_handled = True) nao encontrado"
    return src[start:end]


def test_wizard_canonical_path_sends_thread_id_in_wizard_stage_event():
    """RED pre-Onda-2: payload spread NAO inclui thread_id explicito.
    GREEN apos fix: dict literal envia thread_id (_wiz_thread_id).
    """
    block = _wizard_canonical_send_block()

    pattern = re.compile(
        r'"type":\s*"wizard_stage".*?"thread_id"\s*:',
        re.DOTALL,
    )
    assert pattern.search(block), (
        "wizard_stage payload em wizard_session_canonical NAO inclui "
        "thread_id explicito. Frontend nao consegue persistir o thread_id. "
        "Fix Onda 2: adicionar thread_id: _wiz_thread_id no dict ao lado de stage. "
        f"\nBlock atual (primeiros 600 chars):\n{block[:600]}"
    )


def test_wizard_canonical_path_uses_derived_thread_id_variable():
    """Pre-condition canonical: _wiz_thread_id e derivado de
    WizardSessionService.derive_thread_id."""
    src = _src()
    assert "_wiz_thread_id = _derive_tid(company_id, session_id)" in src, (
        "Pre-condition violada: _wiz_thread_id deveria ser derivado canonical "
        "via app.shared.sessions.derive_thread_id (Task #1080)."
    )
    assert "thread_id=_wiz_thread_id" in src, (
        "Pre-condition violada: _wiz_thread_id deveria ser passado em "
        "WizardSessionService.process_message."
    )
