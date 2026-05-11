"""
Integration test — LangGraph checkpointer canonical (Onda 1 do plan
PLAN_FIX_wizard_memory_loss 2026-05-10).

Confirma que ``get_checkpointer()`` retorna PostgresSaver REAL e que state
persiste em Postgres entre invocacoes do wizard.

Sensor harness (computacional, BLOCKING):
    RED em main pre-Onda-1: ``PostgresSaver.from_conn_string()`` retornava
    context manager em ``langgraph-checkpoint-postgres>=2.0.8`` mas o
    codigo antigo tratava como saver direto e chamava ``.setup()`` →
    AttributeError → fallback silencioso para MemorySaver.

    FIX Onda 1: ConnectionPool + ``PostgresSaver(pool).setup()``.
    GREEN apos fix.

Disciplinas CLAUDE.md aplicadas:
    - TDD-IA red-green-refactor.
    - harness-engineering: sensor computacional sem mocks (no_mock semantics).
    - canonical-fix: minimal assertions.
    - compliance-risk: cleanup pos-test (LGPD Art. 16).
    - canonical-agent: usa WizardSessionService onde aplicavel.

Evidencia empirica do bug (auditoria 2026-05-10): tabela ``checkpoints``
em prod-live tinha TOTAL = 1 row (audit-smoke). Zero wizards reais haviam
persistido em todo historico.
"""
from __future__ import annotations

import os
import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers — cleanup canonical via psycopg sync
# ---------------------------------------------------------------------------

def _sync_url() -> str:
    from lia_config.config import settings
    return (
        (settings.DATABASE_URL or "")
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("+asyncpg", "")
    )


def _delete_thread(thread_id: str) -> None:
    """Cleanup canonical: apaga linhas das tabelas LangGraph para o thread."""
    import psycopg
    with psycopg.connect(_sync_url(), autocommit=True) as conn:
        with conn.cursor() as cur:
            for tbl in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                try:
                    cur.execute(f"DELETE FROM {tbl} WHERE thread_id = %s", (thread_id,))
                except Exception:
                    pass


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — integration test requires real Postgres",
)


# ---------------------------------------------------------------------------
# Sensor canonical do bug V1.d
# ---------------------------------------------------------------------------

def test_get_checkpointer_returns_postgres_saver_not_memory():
    """RED pre-Onda-1: retorna MemorySaver. GREEN apos fix: retorna PostgresSaver."""
    from lia_agents_core.checkpointer import get_checkpointer

    saver = get_checkpointer()
    saver_type = type(saver).__name__

    assert saver_type == "PostgresSaver", (
        f"Expected PostgresSaver (canonical), got {saver_type!r}. "
        f"V1.d bug: PostgresSaver.from_conn_string() returns context manager "
        f"in langgraph-checkpoint-postgres>=2.0.8. Fix: ConnectionPool pattern."
    )


def test_checkpointer_persists_put_get_in_postgres():
    """Confirma que put/get_tuple persistem no Postgres real."""
    from lia_agents_core.checkpointer import get_checkpointer
    from langgraph.checkpoint.base import empty_checkpoint

    saver = get_checkpointer()
    if type(saver).__name__ != "PostgresSaver":
        pytest.fail(
            f"Pre-condition failed: expected PostgresSaver, got "
            f"{type(saver).__name__}."
        )

    thread_id = f"canonical-test-{uuid.uuid4()}"
    cfg = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    try:
        cp = empty_checkpoint()
        cp["channel_values"] = {
            "test_canonical_field": "wizard_continuity_proof_2026_05_10",
        }

        saver.put(cfg, cp, {}, {})

        retrieved = saver.get_tuple(cfg)
        assert retrieved is not None, "Postgres did not persist checkpoint"
        assert (
            retrieved.checkpoint.get("channel_values", {}).get("test_canonical_field")
            == "wizard_continuity_proof_2026_05_10"
        ), f"Persisted value mismatch: {retrieved.checkpoint!r}"
    finally:
        _delete_thread(thread_id)


def test_three_invocations_share_state_via_postgres_saver():
    """RED pre-Onda-1: state perdido. GREEN apos fix: state persiste.

    Simula 3 turnos via saver.put direto (sem LLM externo) — isola o
    invariante computacional do checkpointer da alucinacao do LLM.
    Continuidade do LLM e coberta pelo smoke test manual da Onda 1.H.
    """
    from lia_agents_core.checkpointer import get_checkpointer
    from langgraph.checkpoint.base import empty_checkpoint

    saver = get_checkpointer()
    if type(saver).__name__ != "PostgresSaver":
        pytest.fail(
            f"Pre-condition failed: expected PostgresSaver, got "
            f"{type(saver).__name__}."
        )

    thread_id = f"wiz-canonical-3turns-{uuid.uuid4()}"
    cfg = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    try:
        # Turn 1 — LIA extrai titulo + senioridade
        cp1 = empty_checkpoint()
        cp1["id"] = f"turn1-{uuid.uuid4()}"
        cp1["channel_values"] = {
            "parsed_title": "Desenvolvedor Python Senior",
            "parsed_seniority": "Senior",
            "current_stage": "intake",
        }
        saver.put(cfg, cp1, {"source": "input", "step": 1}, {})

        # Turn 2 — usuario adiciona local + salary
        prior_get = saver.get_tuple(cfg)
        assert prior_get is not None, "Turn 2 nao encontrou state do turn 1"
        merged_values = dict(prior_get.checkpoint.get("channel_values", {}))
        merged_values.update({
            "location": "Sao Paulo",
            "work_model": "hibrido",
            "salary": 13000,
            "current_stage": "jd_enrichment",
        })
        cp2 = empty_checkpoint()
        cp2["id"] = f"turn2-{uuid.uuid4()}"
        cp2["channel_values"] = merged_values
        saver.put(cfg, cp2, {"source": "input", "step": 2}, {})

        # Turn 3 — assert state acumulado (reproduz sintoma do Paulo)
        prior_t3 = saver.get_tuple(cfg)
        assert prior_t3 is not None, "Turn 3 nao encontrou state — bug repro!"

        values = prior_t3.checkpoint.get("channel_values", {})
        assert values.get("parsed_title") == "Desenvolvedor Python Senior", (
            f"BUG REPRO: titulo do turn 1 foi perdido. Got values={values!r}"
        )
        assert values.get("parsed_seniority") == "Senior", (
            "BUG REPRO: senioridade do turn 1 foi perdida."
        )
        assert values.get("location") == "Sao Paulo", (
            "Turn 2 location nao persistiu."
        )
        assert values.get("current_stage") == "jd_enrichment", (
            "Stage transition nao persistiu."
        )
    finally:
        _delete_thread(thread_id)


def test_health_langgraph_endpoint_reports_postgres_saver():
    """Sensor secundario: /health/langgraph reflete o estado real."""
    from lia_agents_core.checkpointer import get_checkpointer

    saver = get_checkpointer()
    cp_type = type(saver).__name__

    assert cp_type == "PostgresSaver", (
        f"/health/langgraph would report {cp_type!r}. Boy scout P2-L da "
        f"Onda 1: endpoint deve retornar 503 quando APP_ENV in "
        f"(production, staging) e cp_type == MemorySaver."
    )
