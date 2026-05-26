"""Sensor — Sprint M (2026-05-21): review_gate dual-confirmation hygiene.

REGRA: Quando review_gate_node detecta o SEGUNDO publish_now dentro
da janela TTL, ele NÃO pode deixar gate_clarify_message ou
gate_last_intent truthy, senão o downstream publish_node (que
escreve "Vaga publicada com sucesso!" em stage_data.message) é
SUPRIMIDO pelo override em WizardSessionService.process_message:

    if gate_msg and (gate_intent or gate_fairness_blocked):
        message = str(gate_msg)
    else:
        message = stage_data.get("message") ...

Sem este sensor, a regressão fica invisível — o E2E observa LIA dizendo
"Só me confirma uma última vez" (LLM conversational_reply do classifier)
em vez de "Vaga publicada com sucesso!" da publish_node. Sintoma: usuário
acha que precisa confirmar uma TERCEIRA vez, mas a vaga já foi criada
no banco.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REVIEW_GATE_FILE = (
    Path(__file__).resolve().parents[2]
    / "app/domains/job_creation/graph.py"
)
# PR-10 step 17: review_gate_node moved to nodes/review_gate.py.
_REVIEW_GATE_NODE_FILE = (
    Path(__file__).resolve().parents[2]
    / "app/domains/job_creation/nodes/review_gate.py"
)


def _read_source() -> str:
    assert _REVIEW_GATE_FILE.exists(), f"missing canonical file: {_REVIEW_GATE_FILE}"
    parts = [_REVIEW_GATE_FILE.read_text(encoding="utf-8")]
    if _REVIEW_GATE_NODE_FILE.exists():
        parts.append(_REVIEW_GATE_NODE_FILE.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_dual_confirmation_clears_gate_clarify_message() -> None:
    """Within-TTL branch MUST set gate_clarify_message=None.

    Regressão histórica (Sprint M): código setava
    gate_clarify_message = output.conversational_reply or "...",
    e o LLM gerava texto tipo "Só me confirma uma última vez" que
    aparecia ao usuário como terceira solicitação de confirmação
    mesmo após routing correto para publish.
    """
    src = _read_source()
    # localize o branch within-TTL — pattern âncora estável
    block_re = re.compile(
        r"if _within_ttl:.*?confirmation_method = \"dual\"",
        re.DOTALL,
    )
    m = block_re.search(src)
    assert m, "could not locate review_gate within-TTL branch"
    block = m.group(0)

    # within-TTL branch DEVE setar gate_clarify_message = None
    assert "next_state[\"gate_clarify_message\"] = None" in block, (
        "Regression: within-TTL branch must clear gate_clarify_message "
        "to let publish_node\"s success message win. See Sprint M fix."
    )


def test_dual_confirmation_clears_gate_last_intent() -> None:
    """Within-TTL branch MUST also clear gate_last_intent.

    Sem isso, o if gate_msg and (gate_intent or ...) em
    process_message ainda dispara mesmo com gate_clarify_message=None
    porque gate_intent="publish_now" continua truthy do default
    next_state assembly (L4115).
    """
    src = _read_source()
    block_re = re.compile(
        r"if _within_ttl:.*?confirmation_method = \"dual\"",
        re.DOTALL,
    )
    m = block_re.search(src)
    assert m, "could not locate review_gate within-TTL branch"
    block = m.group(0)

    assert "next_state[\"gate_last_intent\"] = None" in block, (
        "Regression: within-TTL branch must clear gate_last_intent so "
        "downstream stage_data.message takes precedence over gate_msg. "
        "See Sprint M fix."
    )


def test_dual_confirmation_still_sets_policy_confirmed_publish() -> None:
    """The fix MUST NOT regress the actual confirmation flag.

    policy_confirmed_publish=True is what unlocks publish_node\"s
    PolicyGate (HITL_REQUIRED). The Sprint M fix only clears message
    overrides — the security gate flag stays.
    """
    src = _read_source()
    block_re = re.compile(
        r"if _within_ttl:.*?confirmation_method = \"dual\"",
        re.DOTALL,
    )
    m = block_re.search(src)
    assert m, "could not locate review_gate within-TTL branch"
    block = m.group(0)

    assert "next_state[\"policy_confirmed_publish\"] = True" in block, (
        "Critical regression: dual-confirmation MUST set "
        "policy_confirmed_publish=True. Without this, publish_node "
        "PolicyGate would reject HITL_REQUIRED and job never lands."
    )
    assert "next_state[\"pending_publish_confirmation\"] = False" in block, (
        "Dual-confirmation MUST reset pending flag."
    )


def test_orchestrator_extracts_job_vacancy_id_from_data() -> None:
    """Orchestrator falls back to stage_payload.data.job_id.

    Regressão histórica: publish_node e calibration_node escrevem
    job_id dentro de ws_stage_payload.data, não no top level.
    Orchestrator lia stage_payload.get("job_vacancy_id") direto,
    sempre None, mesmo após publish ter inserido o registro no DB.
    """
    orch = (
        Path(__file__).resolve().parents[2]
        / "app/api/v1/wizard_smart_orchestrator.py"
    )
    assert orch.exists()
    src = orch.read_text(encoding="utf-8")

    assert "(stage_payload.get(\"data\") or {}).get(\"job_id\")" in src, (
        "Orchestrator must fall back to stage_payload.data.job_id "
        "for job_vacancy_id extraction (publish_node + calibration_node "
        "stash the id inside data, not at top level)."
    )
    assert (
        "backend_stage in (\"publish\", \"calibration\", \"handoff\", \"done\")"
        in src
    ), (
        "Orchestrator must derive job_published from backend_stage "
        "reaching post-publish nodes."
    )
