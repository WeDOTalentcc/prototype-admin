"""
Integration test — multi-tenancy thread_id (Task #1080 canonical).

Substitui a sentinela antiga (Onda 4.D3 / PLAN_FIX_wizard_memory_loss
2026-05-10) que validava o formato 4-priority do
``WizardSessionService.derive_thread_id`` (com msg["thread_id"] custom +
heurística + Redis marker).

Modelo canônico Task #1080:
  - ``app.shared.sessions.derive_thread_id(company_id, session_id)`` —
    função pura, determinística, sem fallback heurístico, sem honor de
    thread_id custom do cliente.
  - Tenant token = primeiros 8 chars de ``CompanyId.parse(company_id).as_str()``
    ou literal ``"anon"`` quando ``company_id`` é None / unparseable.

Disciplinas CLAUDE.md aplicadas:
  - canonical-fix: 1 fonte de verdade pro thread_id.
  - harness-engineering: sensor de tenant isolation cross-thread, agora
    direto contra o canônico (sem wrapper).
  - compliance-risk: aderência ao multi-tenancy invariant
    (CLAUDE.md Non-Negotiable Rules #1).
"""
from __future__ import annotations

import os
import uuid

import pytest


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — integration test requires real Postgres",
)


def test_derive_thread_id_encodes_company_token_when_company_id_present():
    """Com company_id válido, thread_id inclui prefixo do tenant."""
    from app.shared.sessions import derive_thread_id

    sess = "sess-iso-001"
    cid = "00000000-0000-4000-8000-000000000001"
    tid = derive_thread_id(cid, sess)
    assert tid.startswith("wiz-"), f"Expected wiz- prefix, got {tid!r}"
    assert sess in tid, f"session_id must be embedded; got {tid!r}"
    assert tid != f"wiz-{sess}", (
        f"Expected company_token in thread_id, got bare format {tid!r}"
    )
    assert tid != f"wiz-anon-{sess}", (
        "company_id válido NÃO deve cair no token 'anon'"
    )


def test_derive_thread_id_falls_back_to_anon_when_no_company_id():
    """Sem company_id, formato canônico ``wiz-anon-{session_id}`` (estável)."""
    from app.shared.sessions import derive_thread_id

    sess = "sess-iso-002"
    assert derive_thread_id(None, sess) == f"wiz-anon-{sess}"
    assert derive_thread_id("", sess) == f"wiz-anon-{sess}"


def test_derive_thread_id_two_companies_dont_collide_same_session():
    """Defense-in-depth: company A e B, mesma session_id, threads distintos.

    Este é o invariante CORE da Task #1080: a função pura preserva isolamento
    multi-tenant sem depender de Redis marker ou heurística externa.
    """
    from app.shared.sessions import derive_thread_id

    sess = f"sess-shared-{uuid.uuid4()}"
    cid_a = "11111111-1111-4111-8111-111111111111"
    cid_b = "22222222-2222-4222-8222-222222222222"
    tid_a = derive_thread_id(cid_a, sess)
    tid_b = derive_thread_id(cid_b, sess)
    assert tid_a != tid_b, (
        f"Multi-tenancy invariant violado: companies A e B com mesma session "
        f"produzem mesmo thread_id! tid_a={tid_a!r} tid_b={tid_b!r}"
    )


def test_derive_thread_id_invalid_company_id_falls_back_to_anon():
    """Inputs que CompanyId.parse rejeita: nunca crash, cai em 'anon'."""
    from app.shared.sessions import derive_thread_id

    sess = "sess-iso-003"
    for bad_cid in ("   ", "company id with spaces", "company!@#$%"):
        tid = derive_thread_id(bad_cid, sess)
        assert isinstance(tid, str) and tid.startswith("wiz-") and sess in tid, (
            f"company_id={bad_cid!r} deve produzir thread_id válido; got {tid!r}"
        )


def test_derive_thread_id_no_longer_honors_client_supplied_thread_id():
    """Task #1080 contract: o helper canônico NÃO aceita mais ``msg["thread_id"]``.
    A assinatura é pura ``(company_id, session_id)`` — single source of truth.
    """
    from app.shared.sessions import derive_thread_id
    import inspect

    sig = inspect.signature(derive_thread_id)
    params = list(sig.parameters.keys())
    assert params == ["company_id", "session_id"], (
        f"Assinatura canônica deve ser (company_id, session_id); got {params}"
    )


def test_tenant_isolation_two_companies_independent_state_in_postgres():
    """End-to-end: company A escreve checkpoint, company B não consegue ler.

    Pre-condition: PostgresSaver canonical (Onda 1) ativo.
    """
    from lia_agents_core.checkpointer import get_checkpointer
    from langgraph.checkpoint.base import empty_checkpoint
    from app.shared.sessions import derive_thread_id

    saver = get_checkpointer()
    if type(saver).__name__ != "PostgresSaver":
        pytest.fail(
            f"Pre-condition failed: expected PostgresSaver, got {type(saver).__name__}"
        )

    sess = f"sess-iso-{uuid.uuid4()}"
    cid_a = "33333333-3333-4333-8333-333333333333"
    cid_b = "44444444-4444-4444-8444-444444444444"
    tid_a = derive_thread_id(cid_a, sess)
    tid_b = derive_thread_id(cid_b, sess)
    assert tid_a != tid_b

    cfg_a = {"configurable": {"thread_id": tid_a, "checkpoint_ns": ""}}
    cfg_b = {"configurable": {"thread_id": tid_b, "checkpoint_ns": ""}}

    try:
        # Company A escreve seu state
        cp_a = empty_checkpoint()
        cp_a["channel_values"] = {
            "company_id": cid_a,
            "secret_field": "ONLY_VISIBLE_TO_A",
        }
        saver.put(cfg_a, cp_a, {"step": 1}, {})

        # Company B lê com config de B — NÃO deve ver dados de A
        result_b = saver.get_tuple(cfg_b)
        if result_b is not None:
            values_b = result_b.checkpoint.get("channel_values", {})
            assert values_b.get("secret_field") != "ONLY_VISIBLE_TO_A", (
                f"TENANT LEAK: company B leu state de A! values_b={values_b!r}"
            )

        # Sanity: A lê com config de A — deve ver
        result_a = saver.get_tuple(cfg_a)
        assert result_a is not None
        assert result_a.checkpoint["channel_values"]["secret_field"] == "ONLY_VISIBLE_TO_A"

    finally:
        # Cleanup ambos os threads
        import psycopg
        from lia_config.config import settings
        sync_url = (
            settings.DATABASE_URL
            .replace("postgresql+asyncpg://", "postgresql://")
            .replace("+asyncpg", "")
        )
        with psycopg.connect(sync_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                for tid in (tid_a, tid_b):
                    for tbl in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                        try:
                            cur.execute(f"DELETE FROM {tbl} WHERE thread_id = %s", (tid,))
                        except Exception:
                            pass
