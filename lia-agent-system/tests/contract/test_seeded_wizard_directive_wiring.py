"""Contract: seeded-wizard tool directive wiring (create-vacancy-from-source).

Wires the LAST mile of the create-from-source flow. The tool
``start_creation_from_source`` returns a directive
``{data: {ui_action: "start_wizard_seeded", seed_source: {...}}}``. Until now the
orchestrator's agentic loop captured only tool *names+params*, never *results* —
so the directive was inert. This test pins the three additive pieces:

  A. ``AgenticLoop.run`` surfaces ``tool_directive`` from a tool result
     (None for normal results — regression-critical: the core chat path runs
     on EVERY turn and must NOT divert unless ui_action=='start_wizard_seeded').
  B/C. ``MainOrchestrator._start_seeded_wizard`` is the SINGLE delegation+response
     helper, reused by both ``_try_wizard_canonical`` (seed_source=None) and the
     directive-consume path (seed_source carrying the template id).

Run pattern for run() mirrors tests/unit/test_agentic_loop_overload_retry.py.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.execution.agentic_loop import (
    AgenticLoop,
    _extract_tool_directive,
)
from app.tools.executor import ToolResult


# ── helpers (mirror test_agentic_loop_overload_retry._mk_loop/_patches) ──────
def _clean_c3b():
    return type(
        "R",
        (),
        {
            "hate_speech_blocked": False,
            "injection_blocked": False,
            "clean_message": "hi",
            "block_reason": None,
        },
    )()


def _tool_call_resp(name: str, params: dict):
    tc = type("TC", (), {"id": "tc1", "name": name, "parameters": params})()
    return type(
        "LR", (), {"is_tool_call": True, "text_response": None, "tool_calls": [tc]}
    )()


def _text_resp(text: str):
    return type(
        "LR", (), {"is_tool_call": False, "text_response": text, "tool_calls": []}
    )()


def _mk_loop(generate_side_effect, tool_result: ToolResult):
    loop = AgenticLoop()
    loop._llm_service = AsyncMock()
    loop._llm_service.generate_with_tools = AsyncMock(side_effect=generate_side_effect)
    loop._tool_executor = AsyncMock()
    loop._tool_executor.execute = AsyncMock(return_value=tool_result)
    loop._ToolExecutionContext = MagicMock(return_value=object())
    return loop


def _patches(loop):
    return [
        patch.object(loop, "_ensure_deps"),
        patch.object(loop, "get_tool_schemas", return_value=[{"name": "x"}]),
        patch(
            "app.orchestrator.execution.agentic_loop._c3b_pre",
            new=AsyncMock(return_value=_clean_c3b()),
        ),
        patch(
            "app.orchestrator.execution.agentic_loop._c3b_post",
            new=AsyncMock(side_effect=lambda txt, ctx: txt),
        ),
        patch("asyncio.sleep", new=AsyncMock()),
    ]


async def _run(loop, **kw):
    ctxs = _patches(loop)
    for c in ctxs:
        c.start()
    try:
        return await loop.run(
            user_message="usa o template X",
            company_id="c1",
            user_id="u1",
            provider="claude",
            **kw,
        )
    finally:
        for c in ctxs:
            c.stop()


# ── 1. Pure extractor (fast, deterministic) ──────────────────────────────────
class TestExtractToolDirective:
    def test_normal_result_yields_no_directive(self):
        """REGRESSAO: turno de chat normal nao pode ser desviado pro wizard
        semeado — o directive so dispara com ui_action=='start_wizard_seeded'."""
        r = ToolResult(success=True, result={"data": {"count": 3}}, tool_name="search")
        assert _extract_tool_directive(r) is None

    def test_no_data_key_yields_none(self):
        r = ToolResult(success=True, result={"message": "ok"}, tool_name="x")
        assert _extract_tool_directive(r) is None

    def test_failed_result_yields_none(self):
        r = ToolResult(
            success=False,
            result={"data": {"ui_action": "start_wizard_seeded"}},
            tool_name="x",
        )
        assert _extract_tool_directive(r) is None

    def test_unrecognized_ui_action_yields_none(self):
        r = ToolResult(
            success=True, result={"data": {"ui_action": "open_modal"}}, tool_name="x"
        )
        assert _extract_tool_directive(r) is None

    def test_seeded_directive_extracted(self):
        r = ToolResult(
            success=True,
            result={
                "data": {
                    "ui_action": "start_wizard_seeded",
                    "seed_source": {"type": "template", "id": "X"},
                }
            },
            tool_name="start_creation_from_source",
        )
        d = _extract_tool_directive(r)
        assert d == {
            "ui_action": "start_wizard_seeded",
            "seed_source": {"type": "template", "id": "X"},
        }

    def test_none_result_object_is_safe(self):
        assert _extract_tool_directive(None) is None


# ── 2. run() REGRESSION — normal tool result => tool_directive is None ───────
@pytest.mark.asyncio
async def test_run_normal_tool_result_no_directive():
    """REGRESSAO: turno de chat normal nao pode ser desviado pro wizard
    semeado — o directive so dispara com ui_action=='start_wizard_seeded'."""
    normal = ToolResult(
        success=True, result={"data": {"jobs": []}}, tool_name="list_jobs"
    )
    loop = _mk_loop(
        [_tool_call_resp("list_jobs", {}), _text_resp("Aqui estão as vagas.")],
        tool_result=normal,
    )
    result = await _run(loop)
    assert result["response"] == "Aqui estão as vagas."
    assert result["tool_directive"] is None


# ── 3. run() HAPPY — seeded directive surfaces ───────────────────────────────
@pytest.mark.asyncio
async def test_run_surfaces_seeded_directive():
    seeded = ToolResult(
        success=True,
        result={
            "data": {
                "ui_action": "start_wizard_seeded",
                "seed_source": {"type": "template", "id": "X"},
            },
            "message": "abrindo o assistente",
        },
        tool_name="start_creation_from_source",
    )
    loop = _mk_loop(
        [
            _tool_call_resp("start_creation_from_source",
                            {"source_type": "template", "source_id": "X"}),
            _text_resp("Pronto."),
        ],
        tool_result=seeded,
    )
    result = await _run(loop)
    assert result["tool_directive"] == {
        "ui_action": "start_wizard_seeded",
        "seed_source": {"type": "template", "id": "X"},
    }


# ── 4. _start_seeded_wizard — seed_source flows into process_message ─────────
def _make_ctx():
    from app.orchestrator.context.context_adapter import UniversalContext

    return UniversalContext(
        message="usa o template X",
        user_id="u1",
        company_id="c1",
        conversation_id="conv-1",
        skip_memory_persist=True,
    )


def _make_orch():
    from app.orchestrator.execution.main_orchestrator import MainOrchestrator

    return MainOrchestrator(orchestrator=MagicMock())


@pytest.mark.asyncio
async def test_start_seeded_wizard_injects_seed_source():
    orch = _make_orch()
    ctx = _make_ctx()

    captured = {}

    async def _fake_pm(*, thread_id, user_message, user_id, company_id,
                       session_id, context, on_token):
        captured["context"] = context
        return ("Vamos começar pelo título?", {"stage": "intake"}, 0)

    with patch(
        "app.domains.job_creation.services.wizard_session_service."
        "WizardSessionService.process_message",
        new=AsyncMock(side_effect=_fake_pm),
    ):
        resp = await orch._start_seeded_wizard(
            ctx, "conv-1", None, None,
            seed_source={"type": "template", "id": "X"},
        )

    # seed_source carried into process_message context for the producer to seed.
    assert captured["context"]["seed_source"] == {"type": "template", "id": "X"}
    assert resp.success is True
    assert resp.agent_used == "wizard_session_canonical"
    assert resp.intent_detected == "wizard"


# ── 5. DEDUP PIN — _try_wizard_canonical routes through _start_seeded_wizard ─
@pytest.mark.asyncio
async def test_try_wizard_canonical_delegates_to_helper():
    """Single source of truth: the classic bootstrap path and the directive
    path BOTH go through _start_seeded_wizard. The bootstrap call passes
    seed_source=None and still yields a wizard response."""
    orch = _make_orch()
    ctx = _make_ctx()
    ctx.message = "criar vaga de backend"  # matches _WIZARD_START_PATTERNS

    seen = {}

    async def _spy(ctx_, conv_id_, conv_, db_, seed_source=None):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        seen["seed_source"] = seed_source
        return ChatResponse(
            success=True, content="ok", agent_used="wizard_session_canonical",
            intent_detected="wizard", conversation_id=conv_id_,
        )

    with patch.object(orch, "_start_seeded_wizard", new=AsyncMock(side_effect=_spy)):
        resp = await orch._try_wizard_canonical(ctx, "conv-1", None, None)

    assert resp is not None
    assert resp.agent_used == "wizard_session_canonical"
    # Classic bootstrap path delegates with seed_source=None (dedup proof).
    assert seen["seed_source"] is None
