"""
Sensor: WizardSessionService — Sprint A.1 Bug 6 regression tests.

Validates:
1. derive_thread_id wrapper — delegates to canonical (Task #1080)
2. _get_prior_state — non-raising on checkpointer miss
3. _build_state — fresh session builds correct initial_state
4. _build_state — continuing session accumulates conversation_messages
5. _build_state — workspace_id always from authoritative company_id param
6. _build_state — hitl_approved reset on new message (not approval)
7. Multi-turn accumulation (Turn 1 → Turn 2 → Turn 3)

Skill canônica: harness-engineering [sensor computacional] + lia-testing TDD.

Task #1080: a lógica do thread_id agora é puramente delegada para
``app.shared.sessions.derive_thread_id``. Os testes do contrato canônico
vivem em ``tests/integration/agents/test_wizard_session_continuity_t1080.py``.
Os testes abaixo só verificam que o wrapper de back-compat continua se
comportando como esperado pelos call-sites legados.
"""
import pytest

from app.domains.job_creation.services.wizard_session_service import WizardSessionService


# ── 1. derive_thread_id wrapper (Task #1080 — delegating) ───────────────────

_CID = "00000000-0000-4000-a000-000000000001"


def test_derive_thread_id_wrapper_legacy_signature_ignores_custom_thread_id():
    """Wrapper aceita ``(msg, session_id, company_id=...)`` mas NÃO honra
    ``msg["thread_id"]`` — Task #1080 colapsa as fontes de verdade."""
    msg = {"thread_id": "wiz-CUSTOM-XYZ", "content": "criar vaga"}
    tid = WizardSessionService.derive_thread_id(msg, "sess-001", company_id=_CID)
    assert "CUSTOM" not in tid
    assert tid.endswith("sess-001")


def test_derive_thread_id_wrapper_canonical_signature():
    """Wrapper aceita também a assinatura canônica ``(company_id, session_id)``.

    Token = SHA-256(normalized_cid)[:16] (Task #1080: hash colisão-safe).
    """
    import hashlib

    tid = WizardSessionService.derive_thread_id(_CID, "sess-001")
    expected_token = hashlib.sha256(_CID.encode("utf-8")).hexdigest()[:16]
    assert tid == f"wiz-{expected_token}-sess-001"


def test_derive_thread_id_wrapper_no_company_falls_back_to_anon():
    """Sem company_id, wrapper retorna ``wiz-anon-{session_id}``."""
    tid = WizardSessionService.derive_thread_id(None, "sess-001")
    assert tid == "wiz-anon-sess-001"


def test_derive_thread_id_wrapper_legacy_signature_no_company():
    """Assinatura legada com msg dict + company_id=None → 'anon' token."""
    tid = WizardSessionService.derive_thread_id({"content": "x"}, "sess-001")
    assert tid == "wiz-anon-sess-001"


# ── 2. _get_prior_state — non-raising ───────────────────────────────────────

@pytest.mark.asyncio
async def test_get_prior_state_returns_empty_on_miss(monkeypatch):
    """Checkpointer miss → empty dict, no exception."""
    import sys, types

    class _FakeGraph:
        def get_state(self, *a, **kw):
            raise RuntimeError("DB unavailable")

    fake_mod = types.SimpleNamespace(
        job_creation_graph=types.SimpleNamespace(_graph=_FakeGraph())
    )
    monkeypatch.setitem(sys.modules, "app.domains.job_creation.graph", fake_mod)
    result = await WizardSessionService._get_prior_state("wiz-test-123")
    assert result == {}


@pytest.mark.asyncio
async def test_get_prior_state_returns_empty_on_none_values(monkeypatch):
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
    result = await WizardSessionService._get_prior_state("wiz-empty")
    assert result == {}


# ── 3. _build_state — fresh session ─────────────────────────────────────────

def test_build_state_fresh_session():
    """No prior state → fresh intake state with single conversation_message."""
    state = WizardSessionService._build_state(
        thread_id="wiz-001",
        user_message="criar vaga de PM sênior",
        user_id="user-42",
        company_id="test-company",
        session_id="sess-001",
        context=None,
        prior_state={},
    )
    assert state["user_query"] == "criar vaga de PM sênior"
    assert state["workspace_id"] == 0  # slug → workspace_id=0 (not numeric)
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
        "workspace_id": 0,
        "user_id": "user-42",
        "parsed_title": "Product Manager",
    }
    state = WizardSessionService._build_state(
        thread_id="wiz-001",
        user_message="na verdade é para o departamento de produto",
        user_id="user-42",
        company_id="test-company",
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
        "workspace_id": 0,
        "user_id": "u1",
    }
    state_t2 = WizardSessionService._build_state(
        thread_id="wiz-t", user_message="salário entre 8k e 10k",
        user_id="u1", company_id="test-co-a", session_id="s",
        context=None, prior_state=prior_after_t1,
    )
    # Simulate Turn 2 response
    state_t2["conversation_messages"].append({"role": "assistant", "content": "Anotei o salário."})

    state_t3 = WizardSessionService._build_state(
        thread_id="wiz-t", user_message="perfil sênior",
        user_id="u1", company_id="test-co-a", session_id="s",
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
        company_id="demo-company",  # authoritative from JWT
        session_id="s",
        context=None,
        prior_state=prior,
    )
    assert state["workspace_id"] != 999, (
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
        user_id="u1", company_id="test-co", session_id="s",
        context=None, prior_state=prior,
    )
    assert state["hitl_approved"] is False


# ── 7. context carry-over ────────────────────────────────────────────────────

def test_build_state_carries_context_keys():
    """right_panel_form and attached_file_text from context flow into state."""
    ctx = {"right_panel_form": {"cargo": "Dev"}, "attached_file_text": "CV texto"}
    state = WizardSessionService._build_state(
        thread_id="wiz-x", user_message="criar vaga",
        user_id="u1", company_id="test-co", session_id="s",
        context=ctx, prior_state={},
    )
    assert state["right_panel_form"] == {"cargo": "Dev"}
    assert state["attached_file_text"] == "CV texto"


# ── 8. Task #967 — Wizard tenant auto-detection regression ─────────────────
#
# Bug "LIA pergunta company_id no chat do wizard" caiu 3× — origem em 3 root
# causes (CompanyId.parse rejeitando UUID, snippet não propagado pelo carry,
# review_node sem fallback string para workspace_id=0). Os asserts abaixo
# fixam o contrato dos 3 patches no nível do unit-test (complementam o
# integration e2e em tests/integration/wizard/test_wizard_tenant_context_e2e.py).

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"


def test_context_carry_keys_includes_tenant_context_snippet():
    """Sentinel: o snippet de tenant context DEVE estar em
    ``_CONTEXT_CARRY_KEYS`` — sem isso o handler SSE/WS injeta o snippet
    mas o ``_build_state`` o descarta no merge, e o wizard volta a perguntar
    o ID da empresa no chat. Quebra build se alguém remover essa chave."""
    from app.domains.job_creation.services.wizard_session_service import (
        _CONTEXT_CARRY_KEYS,
    )

    assert "tenant_context_snippet" in _CONTEXT_CARRY_KEYS, (
        "_CONTEXT_CARRY_KEYS deve conter 'tenant_context_snippet' — "
        "do contrário o snippet injetado pelo handler SSE/WS é perdido "
        "no merge e a LIA volta a perguntar 'qual o ID da empresa?'."
    )


def test_build_state_uuid_company_id_workspace_zero_and_carries_id(monkeypatch):
    """Regressão Task #967 (root cause #1): para UUID company_id (Demo
    Company canônica), ``workspace_id`` permanece 0 (UUID não é digit) e
    ``company_id`` é normalizado em lowercase e propagado ao state — o
    grafo usa ``company_id`` como fallback string em ``review_node`` quando
    ``workspace_id == 0``."""
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    state = WizardSessionService._build_state(
        thread_id="wiz-uuid",
        user_message="criar vaga",
        user_id="u1",
        # UUID em uppercase → CompanyId.parse normaliza pra lowercase
        company_id="00000000-0000-4000-A000-000000000001",
        session_id="s",
        context=None,
        prior_state={},
    )
    assert state["workspace_id"] == 0, (
        "UUID company_id não é numérico — workspace_id DEVE permanecer 0 "
        "(review_node faz fallback string via 'workspace_id or company_id')"
    )
    assert state["company_id"] == DEMO_COMPANY_UUID, (
        "company_id deve ser propagado normalizado (lowercase) ao state — "
        "review_node usa essa string como lookup_id quando workspace_id=0"
    )


def test_build_state_propagates_tenant_context_snippet_to_state(monkeypatch):
    """Regressão Task #967 (root cause #2): o snippet injetado pelo handler
    SSE no ``context`` DEVE chegar ao ``state`` que vai para o grafo. Sem
    isso, o agente do wizard renderiza o prompt sem tenant context e a LIA
    pergunta o ID da empresa no chat."""
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    snippet = (
        "Empresa: Demo Company (Tecnologia)\n"
        "Plano: enterprise\nTimezone: America/Sao_Paulo"
    )
    state = WizardSessionService._build_state(
        thread_id="wiz-snip",
        user_message="criar vaga",
        user_id="u1",
        company_id=DEMO_COMPANY_UUID,
        session_id="s",
        context={"tenant_context_snippet": snippet, "metadata": {"channel": "sse"}},
        prior_state={},
    )
    assert state.get("tenant_context_snippet") == snippet


def test_review_node_uses_company_id_string_when_workspace_id_zero(monkeypatch):
    """Regressão Task #967 (root cause #3): para tenants UUID
    (``workspace_id == 0``), ``review_node`` DEVE fazer fallback para a
    string ``company_id`` ao chamar ``api_client.get_company_defaults``.
    Sem o fallback, defaults nunca são carregados e o wizard volta a
    'esquecer' o contexto na etapa de revisão."""
    from app.domains.job_creation import graph as graph_mod

    captured = {"lookup_id": None}

    class _FakeResp:
        success = True
        data = {
            "default_screening_mode": "auto",
            "default_platforms": ["linkedin"],
            "default_eligibility": ["clt"],
        }

    class _FakeAPI:
        def get_company_defaults(self, lookup_id):
            captured["lookup_id"] = lookup_id
            return _FakeResp()

    monkeypatch.setattr(graph_mod, "_get_api_client", lambda _state: _FakeAPI())

    state = {
        "workspace_id": 0,
        "company_id": DEMO_COMPANY_UUID,
        "company_defaults_applied": [],
        "stage_history": [],
    }
    out = graph_mod.review_node(state)

    assert captured["lookup_id"] == DEMO_COMPANY_UUID, (
        "review_node deve preferir company_id (UUID string) quando "
        f"workspace_id=0 — recebeu {captured['lookup_id']!r}"
    )
    # Defaults aplicados ao state — prova end-to-end do fallback
    assert "screening_mode" in out["company_defaults_applied"]
    assert "publish_platforms" in out["company_defaults_applied"]
    assert "eligibility_questions" in out["company_defaults_applied"]
