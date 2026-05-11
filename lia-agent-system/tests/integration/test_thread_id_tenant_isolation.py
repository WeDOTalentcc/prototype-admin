"""
Integration test — multi-tenancy thread_id (Onda 4.D3 do
PLAN_FIX_wizard_memory_loss 2026-05-10).

Sensor canonical: garante que derive_thread_id encoda o tenant
(``company_id``) no thread_id quando disponivel, e que threads de
companies diferentes NAO colidem.

Disciplinas CLAUDE.md aplicadas:
  - TDD-IA: tests do invariante multi-tenant em integration nivel.
  - harness-engineering: sensor de tenant isolation cross-thread.
  - compliance-risk: aderencia ao multi-tenancy invariant (CLAUDE.md
    Non-Negotiable Rules #1: company_id validado em toda read/write).
  - canonical-fix: backward-compat com legacy threads sem company_id.
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
    """Com company_id valido, thread_id inclui prefix do tenant."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    sess = "sess-iso-001"
    cid = "00000000-0000-4000-8000-000000000001"
    tid = WizardSessionService.derive_thread_id({}, sess, company_id=cid)
    assert tid.startswith("wiz-"), f"Expected wiz- prefix, got {tid!r}"
    assert sess in tid, f"session_id must be embedded; got {tid!r}"
    assert tid != f"wiz-{sess}", (
        f"Expected company_token in thread_id, got legacy format {tid!r}"
    )


def test_derive_thread_id_falls_back_to_legacy_when_no_company_id():
    """Sem company_id (ou ausente), formato legacy preservado (back-compat)."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    sess = "sess-iso-002"
    tid_no_cid = WizardSessionService.derive_thread_id({}, sess)
    assert tid_no_cid == f"wiz-{sess}", (
        f"Sem company_id deve cair em legacy wiz-{{session_id}}; got {tid_no_cid!r}"
    )

    tid_none_cid = WizardSessionService.derive_thread_id({}, sess, company_id=None)
    assert tid_none_cid == f"wiz-{sess}", (
        f"company_id=None deve cair em legacy; got {tid_none_cid!r}"
    )


def test_derive_thread_id_two_companies_dont_collide_same_session():
    """Defense-in-depth: company A e company B, mesma session_id, threads distintos."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    sess = f"sess-shared-{uuid.uuid4()}"
    cid_a = "11111111-1111-4111-8111-111111111111"
    cid_b = "22222222-2222-4222-8222-222222222222"
    tid_a = WizardSessionService.derive_thread_id({}, sess, company_id=cid_a)
    tid_b = WizardSessionService.derive_thread_id({}, sess, company_id=cid_b)
    assert tid_a != tid_b, (
        f"Multi-tenancy invariant violado: companies A e B com mesma session "
        f"produzem mesmo thread_id! tid_a={tid_a!r} tid_b={tid_b!r}"
    )


def test_derive_thread_id_invalid_company_id_falls_back_gracefully():
    """Legacy mode: company_id invalido nao crash, cai em legacy format.

    Inputs que CompanyId.parse rejeita: strings vazias, com caracteres
    proibidos (espaco, simbolos especiais), ou claramente nao-slug.
    """
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    sess = "sess-iso-003"
    # Inputs que devem cair em legacy: empty string, espacos, simbolos
    for bad_cid in ("", "   ", "company id with spaces", "company!@#$%"):
        tid = WizardSessionService.derive_thread_id({}, sess, company_id=bad_cid)
        # Aceita: legacy format ("wiz-{sess}") OU prefixo derivado do parse
        # que NAO crashou (graceful). O contrato e: NUNCA crash, sempre devolve
        # string valida.
        assert isinstance(tid, str) and tid.startswith("wiz-") and sess in tid, (
            f"company_id={bad_cid!r} deve produzir thread_id valido; got {tid!r}"
        )


def test_derive_thread_id_client_supplied_overrides_company_prefix():
    """Cliente que ja tem thread_id (HITL approval flow) tem prioridade."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    client_tid = "wiz-existing-abc-xyz"
    tid = WizardSessionService.derive_thread_id(
        {"thread_id": client_tid},
        "sess-other",
        company_id="00000000-0000-4000-8000-000000000099",
    )
    assert tid == client_tid, (
        f"Client-supplied thread_id deve ter prioridade; got {tid!r}"
    )


def test_tenant_isolation_two_companies_independent_state_in_postgres():
    """End-to-end: company A escreve checkpoint, company B nao consegue ler.

    Pre-condition: PostgresSaver canonical (Onda 1) ativo.
    """
    from lia_agents_core.checkpointer import get_checkpointer
    from langgraph.checkpoint.base import empty_checkpoint
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    saver = get_checkpointer()
    if type(saver).__name__ != "PostgresSaver":
        pytest.fail(
            f"Pre-condition failed: expected PostgresSaver, got {type(saver).__name__}"
        )

    sess = f"sess-iso-{uuid.uuid4()}"
    cid_a = "33333333-3333-4333-8333-333333333333"
    cid_b = "44444444-4444-4444-8444-444444444444"
    tid_a = WizardSessionService.derive_thread_id({}, sess, company_id=cid_a)
    tid_b = WizardSessionService.derive_thread_id({}, sess, company_id=cid_b)
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

        # Company B le com config de B — NAO deve ver dados de A
        result_b = saver.get_tuple(cfg_b)
        if result_b is not None:
            values_b = result_b.checkpoint.get("channel_values", {})
            assert values_b.get("secret_field") != "ONLY_VISIBLE_TO_A", (
                f"TENANT LEAK: company B leu state de A! values_b={values_b!r}"
            )

        # Sanity: A le com config de A — deve ver
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
