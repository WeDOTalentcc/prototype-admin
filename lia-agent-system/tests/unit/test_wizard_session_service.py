"""
Sensor: WizardSessionService — Sprint A.1 Bug 6 regression tests.

Validates:
1. derive_thread_id — client-supplied > session fallback
2. _get_prior_state — non-raising on checkpointer miss
3. _build_state — fresh session builds correct initial_state
4. _build_state — continuing session accumulates conversation_messages
5. _build_state — workspace_id always from authoritative company_id param
6. _build_state — hitl_approved reset on new message (not approval)
7. Multi-turn accumulation (Turn 1 → Turn 2 → Turn 3)

Skill canônica: harness-engineering [sensor computacional] + lia-testing TDD.
"""
import pytest

from app.domains.job_creation.services.wizard_session_service import WizardSessionService


# ── 1. derive_thread_id ─────────────────────────────────────────────────────

def test_derive_thread_id_uses_client_supplied():
    """Client-supplied thread_id takes priority."""
    msg = {"thread_id": "wiz-abc123", "content": "criar vaga"}
    assert WizardSessionService.derive_thread_id(msg, "sess-001") == "wiz-abc123"


def test_derive_thread_id_falls_back_to_session():
    """No thread_id in msg → stable f'wiz-{session_id}'."""
    msg = {"content": "criar vaga"}
    assert WizardSessionService.derive_thread_id(msg, "sess-001") == "wiz-sess-001"


def test_derive_thread_id_empty_string_falls_back():
    """Empty string thread_id treated as absent."""
    msg = {"thread_id": "", "content": "criar vaga"}
    assert WizardSessionService.derive_thread_id(msg, "sess-001") == "wiz-sess-001"


def test_derive_thread_id_whitespace_falls_back():
    """Whitespace-only thread_id treated as absent."""
    msg = {"thread_id": "   ", "content": "criar vaga"}
    assert WizardSessionService.derive_thread_id(msg, "sess-001") == "wiz-sess-001"


# ── 2. _get_prior_state — non-raising ───────────────────────────────────────

def test_get_prior_state_returns_empty_on_miss(monkeypatch):
    """Checkpointer miss → empty dict, no exception."""
    import sys, types

    class _FakeGraph:
        def get_state(self, *a, **kw):
            raise RuntimeError("DB unavailable")

    fake_mod = types.SimpleNamespace(
        job_creation_graph=types.SimpleNamespace(_graph=_FakeGraph())
    )
    monkeypatch.setitem(sys.modules, "app.domains.job_creation.graph", fake_mod)
    result = WizardSessionService._get_prior_state("wiz-test-123")
    assert result == {}


def test_get_prior_state_returns_empty_on_none_values(monkeypatch):
    """Snapshot with None values → empty dict."""
    import sys, types

    class _FakeSnapshot:
        values = None

    class _FakeGraph:
        def get_state(self, config):
            return _FakeSnapshot()

    fake_mod = types.SimpleNamespace(
        job_creation_graph=types.SimpleNamespace(_graph=_FakeGraph())
    )
    monkeypatch.setitem(sys.modules, "app.domains.job_creation.graph", fake_mod)
    result = WizardSessionService._get_prior_state("wiz-empty")
    assert result == {}


# ── 3. _build_state — fresh session ─────────────────────────────────────────

def test_build_state_fresh_session():
    """No prior state → fresh intake state with single conversation_message."""
    state = WizardSessionService._build_state(
        thread_id="wiz-001",
        user_message="criar vaga de PM sênior",
        user_id="user-42",
        company_id="100",
        session_id="sess-001",
        context=None,
        prior_state={},
    )
    assert state["user_query"] == "criar vaga de PM sênior"
    assert state["workspace_id"] == 100
    assert state["user_id"] == "user-42"
    assert state["conversation_messages"] == [
        {"role": "user", "content": "criar vaga de PM sênior"},
    ]
    assert state["current_stage"] is None
    assert "hitl_approved" not in state  # fresh session never sets hitl_approved


# ── 4. _build_state — continuing session accumulates messages (Bug 6) ────────

def test_build_state_continuing_session_accumulates_conversation():
    """
    Regression Bug 6: Turn 2 must APPEND to prior conversation_messages,
    not overwrite them with a single-element list.
    """
    prior = {
        "current_stage": "jd_enrichment",
        "conversation_messages": [
            {"role": "user", "content": "criar vaga de PM sênior"},
            {"role": "assistant", "content": "Captei. Enriquecendo a JD…"},
        ],
        "workspace_id": 100,
        "user_id": "user-42",
        "parsed_title": "Product Manager",
    }
    state = WizardSessionService._build_state(
        thread_id="wiz-001",
        user_message="na verdade é para o departamento de produto",
        user_id="user-42",
        company_id="100",
        session_id="sess-001",
        context=None,
        prior_state=prior,
    )
    assert len(state["conversation_messages"]) == 3, (
        "Turn 2 must append, not overwrite — Bug 6 regression"
    )
    assert state["conversation_messages"][2] == {
        "role": "user",
        "content": "na verdade é para o departamento de produto",
    }
    # Prior parsed fields must be preserved
    assert state["parsed_title"] == "Product Manager"
    assert state["current_stage"] == "jd_enrichment"


def test_build_state_three_turns_accumulate():
    """Three consecutive turns accumulate 5 messages (3 user + 2 assistant)."""
    prior_after_t1 = {
        "current_stage": "intake",
        "conversation_messages": [
            {"role": "user", "content": "criar vaga"},
            {"role": "assistant", "content": "Captei."},
        ],
        "workspace_id": 50,
        "user_id": "u1",
    }
    state_t2 = WizardSessionService._build_state(
        thread_id="wiz-t", user_message="salário entre 8k e 10k",
        user_id="u1", company_id="50", session_id="s",
        context=None, prior_state=prior_after_t1,
    )
    # Simulate Turn 2 response
    state_t2["conversation_messages"].append({"role": "assistant", "content": "Anotei o salário."})

    state_t3 = WizardSessionService._build_state(
        thread_id="wiz-t", user_message="perfil sênior",
        user_id="u1", company_id="50", session_id="s",
        context=None, prior_state=state_t2,
    )
    assert len(state_t3["conversation_messages"]) == 5
    assert state_t3["conversation_messages"][-1]["content"] == "perfil sênior"


# ── 5. _build_state — workspace_id always from authoritative param ───────────

def test_build_state_workspace_id_from_param_not_prior_state():
    """
    Multi-tenancy: workspace_id always derived from company_id param,
    never trusted from stale prior_state (prevents tenant escalation).
    """
    prior = {
        "workspace_id": 999,  # stale / wrong tenant
        "conversation_messages": [{"role": "user", "content": "criar vaga"}],
    }
    state = WizardSessionService._build_state(
        thread_id="wiz-x",
        user_message="novo cargo",
        user_id="u1",
        company_id="123",  # authoritative from JWT
        session_id="s",
        context=None,
        prior_state=prior,
    )
    assert state["workspace_id"] == 123, (
        "workspace_id must come from JWT-verified company_id, not stale prior_state"
    )


# ── 6. _build_state — hitl_approved reset on new message ────────────────────

def test_build_state_resets_hitl_approved():
    """
    A new regular message (not approval) must reset hitl_approved=False
    so the graph doesn't treat it as an approval resume.
    """
    prior = {
        "hitl_approved": True,  # from a previous approval cycle
        "conversation_messages": [{"role": "user", "content": "ok, aprovado"}],
        "workspace_id": 1,
    }
    state = WizardSessionService._build_state(
        thread_id="wiz-x", user_message="nova mensagem",
        user_id="u1", company_id="1", session_id="s",
        context=None, prior_state=prior,
    )
    assert state["hitl_approved"] is False


# ── 7. context carry-over ────────────────────────────────────────────────────

def test_build_state_carries_context_keys():
    """right_panel_form and attached_file_text from context flow into state."""
    ctx = {"right_panel_form": {"cargo": "Dev"}, "attached_file_text": "CV texto"}
    state = WizardSessionService._build_state(
        thread_id="wiz-x", user_message="criar vaga",
        user_id="u1", company_id="1", session_id="s",
        context=ctx, prior_state={},
    )
    assert state["right_panel_form"] == {"cargo": "Dev"}
    assert state["attached_file_text"] == "CV texto"
