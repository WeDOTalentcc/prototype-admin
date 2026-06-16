"""
Sentinel canonical — Task #1080 (wizard-session-continuity-canonical-refactor).

Substitui o antigo ``test_wizard_session_continuity_t1051.py`` (eliminado
junto com o Tier 0.5 do CascadedRouter, o Redis marker
``lia:wizard:active:*`` e a heurística ``_candidate_thread_ids``).

O novo modelo tem UMA única fonte de verdade para "esta conversa pertence
ao wizard": o checkpoint LangGraph para o ``thread_id`` derivado da função
pura ``app.shared.sessions.derive_thread_id(company_id, session_id)``.

Cobertura:
  S1 — derive_thread_id é puro, determinístico, multi-tenant safe
  S2 — derive_thread_id NÃO honra mais ``msg["thread_id"]`` custom
  S3 — is_wizard_session_active fail-open (checkpointer outage → False)
  S4 — Tier 0.5 do CascadedRouter foi removido (sentinela AST)
  S5 — Wrappers em WizardSessionService delegam ao canônico (back-compat)
  S6 — Pin do wizard NÃO existe mais no router; vive nos handlers WS/SSE
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest


# ── S1 — derive_thread_id pure / deterministic / tenant-isolating ──────────


def test_s1_derive_thread_id_is_deterministic_for_same_inputs():
    """Mesmo (company_id, session_id) → mesmo thread_id, sempre."""
    from app.shared.sessions import derive_thread_id

    cid = "00000000-0000-4000-a000-000000000001"
    sid = "sess-xyz"
    assert derive_thread_id(cid, sid) == derive_thread_id(cid, sid)


def test_s1_derive_thread_id_isolates_tenants_with_same_session():
    """Companies A e B com mesma session_id NUNCA colidem."""
    from app.shared.sessions import derive_thread_id

    sid = "sess-shared"
    cid_a = "11111111-1111-4111-8111-111111111111"
    cid_b = "22222222-2222-4222-8222-222222222222"
    assert derive_thread_id(cid_a, sid) != derive_thread_id(cid_b, sid)


def test_s1_derive_thread_id_format_is_canonical():
    """Formato canônico ``wiz-{token}-{session_id}``.

    Token = 16-char SHA-256 hex prefix de ``CompanyId.parse(cid).as_str()``
    (64 bits de entropia — colisão-segura para multi-tenant). Substitui o
    antigo prefix-de-8-chars que era 32 bits e colidia em slug-ids.
    """
    import hashlib

    from app.shared.sessions import derive_thread_id

    cid = "00000000-0000-4000-a000-000000000001"
    tid = derive_thread_id(cid, "sess-1")
    assert tid.startswith("wiz-")
    assert tid.endswith("-sess-1")
    expected_token = hashlib.sha256(cid.encode("utf-8")).hexdigest()[:16]
    assert tid == f"wiz-{expected_token}-sess-1"


def test_s1_derive_thread_id_resists_slug_prefix_collision():
    """Slug ids que compartilham prefixo NÃO devem colidir no token."""
    from app.shared.sessions import derive_thread_id

    a = derive_thread_id("acme-br-corporation", "s")
    b = derive_thread_id("acme-us-corporation", "s")
    assert a != b, "SHA-256 deve dispersar mesmo em prefixos colidentes."


def test_s1_derive_thread_id_anon_when_no_company_id():
    """Sem company_id → token 'anon' (estável, não crash)."""
    from app.shared.sessions import derive_thread_id

    assert derive_thread_id(None, "sess-1") == "wiz-anon-sess-1"
    assert derive_thread_id("", "sess-1") == "wiz-anon-sess-1"


def test_s1_derive_thread_id_raises_on_empty_session():
    """session_id vazio é erro de programação — fail-closed."""
    from app.shared.sessions import derive_thread_id

    with pytest.raises(ValueError):
        derive_thread_id("any-cid", "")


# ── S2 — Custom msg["thread_id"] NÃO é mais honrado ────────────────────────


def test_s2_custom_msg_thread_id_no_longer_honored_via_wrapper():
    """Wrapper ``WizardSessionService.derive_thread_id`` aceita a assinatura
    legada ``(msg, session_id, company_id=...)`` mas IGNORA ``msg["thread_id"]``.
    Single-source-of-truth: thread_id é função pura de (company_id, session_id).
    """
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    msg_with_custom = {"thread_id": "wiz-CUSTOM-FROM-CLIENT", "content": "x"}
    cid = "00000000-0000-4000-a000-000000000001"
    sid = "sess-xyz"

    wrapped = WizardSessionService.derive_thread_id(
        msg_with_custom, sid, company_id=cid,
    )

    from app.shared.sessions import derive_thread_id as _canon
    canonical = _canon(cid, sid)

    assert wrapped == canonical, (
        "Wrapper NÃO deve honrar msg['thread_id'] — Task #1080 elimina a "
        "fonte de verdade concorrente."
    )
    assert "CUSTOM" not in wrapped


# ── S3 — is_wizard_session_active fail-open ─────────────────────────────────


@pytest.mark.asyncio
async def test_s3_is_wizard_session_active_fails_open_on_checkpointer_outage():
    """Checkpointer indisponível NUNCA bloqueia routing — retorna False."""
    from app.shared.sessions import is_wizard_session_active

    def _boom():
        raise RuntimeError("PostgresSaver pool exhausted")

    with patch(
        "app.domains.job_creation.graph.get_job_creation_graph",
        side_effect=_boom,
    ):
        result = await is_wizard_session_active(
            "00000000-0000-4000-a000-000000000001", "sess-x",
        )
    assert result is False


@pytest.mark.asyncio
async def test_s3_is_wizard_session_active_returns_false_on_empty_session_id():
    from app.shared.sessions import is_wizard_session_active

    assert await is_wizard_session_active("any-cid", "") is False


# ── S4 — Sentinela AST: Tier 0.5 do router removido ────────────────────────


def _read_source(module_path: Path) -> str:
    return module_path.read_text(encoding="utf-8")


def test_s4_cascaded_router_no_longer_imports_wizard_session_service():
    """O router NÃO deve importar WizardSessionService nem chamar
    ``is_session_active`` em nenhum tier. Pin vive nos handlers, não aqui.
    """
    router_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "orchestrator" / "routing" / "cascaded_router.py"
    )
    src = _read_source(router_path)
    assert "from app.domains.job_creation.services.wizard_session_service" not in src, (
        "CascadedRouter não pode importar WizardSessionService — Tier 0.5 removido."
    )
    assert "wizard_session_pin" not in src or "REMOVED" in src or "removed" in src, (
        "Tier 0.5 wizard_session_pin (label do counter) deve ter sido removido."
    )
    # Garante que não há chamada ativa a is_session_active
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "is_session_active":
            pytest.fail(
                "CascadedRouter ainda referencia .is_session_active — "
                "Task #1080 exige que o pin esteja nos handlers WS/SSE."
            )


# ── S5 — Wrappers delegam ao canônico ───────────────────────────────────────


def test_s5_wizard_session_service_derive_delegates_to_canonical():
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )
    from app.shared.sessions import derive_thread_id as _canon

    cid = "00000000-0000-4000-a000-000000000001"
    sid = "sess-canon"
    # Assinatura canônica
    assert WizardSessionService.derive_thread_id(cid, sid) == _canon(cid, sid)
    # Assinatura legada (msg dict) — primeiro arg ignorado para o thread
    assert (
        WizardSessionService.derive_thread_id({}, sid, company_id=cid)
        == _canon(cid, sid)
    )


@pytest.mark.asyncio
async def test_s5_wizard_session_service_is_session_active_delegates_to_canonical():
    """A wrapper deve delegar — verifica via patch do canônico."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )
    with patch(
        "app.shared.sessions.is_wizard_session_active",
        return_value=True,
    ) as canon:
        # Imports tardios no wrapper — patch via attribute lookup acima cobre.
        # Como o wrapper faz `from app.shared.sessions import is_wizard_session_active`
        # dentro do método, patcheamos no módulo de origem.
        result = await WizardSessionService.is_session_active(
            session_id="s", company_id="c",
        )
    assert result is True
    canon.assert_called_once()


# ── S6 — Sentinela: handlers WS/SSE são os donos do pin ────────────────────


def test_s6_ws_handler_owns_the_wizard_pin():
    ws_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "api" / "v1" / "agent_chat_ws.py"
    )
    src = _read_source(ws_path)
    assert "is_wizard_session_active" in src, (
        "agent_chat_ws.py deve importar is_wizard_session_active e operar o pin."
    )
    assert "wizard_session_pin" in src, (
        "agent_chat_ws.py deve logar 'wizard_session_pin' (rastreabilidade)."
    )


def test_s6_sse_handler_owns_the_wizard_pin():
    sse_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "api" / "v1" / "agent_chat_sse.py"
    )
    src = _read_source(sse_path)
    assert "should_pin_to_wizard" in src
    assert "wizard_session_pin" in src


def test_s6_canonical_module_exists_and_exports_two_helpers():
    """Sensor: o módulo canônico existe, é puro, e exporta exatamente os
    dois helpers públicos."""
    from app.shared import sessions

    assert hasattr(sessions, "derive_thread_id")
    assert hasattr(sessions, "is_wizard_session_active")
    sig = inspect.signature(sessions.derive_thread_id)
    # Dois parâmetros posicionais — pure function
    assert list(sig.parameters.keys()) == ["company_id", "session_id"]
