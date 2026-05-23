"""
P0 production fix · voice_wsi_results canonical tests (2026-05-23).

Audit 2026-05-23 (MISSING_TABLES_INVESTIGATION_2026-05-23.md):
- voice_wsi_results table was missing in production
- _persist_wsi_result had silent try/except (REGRA 4 anti-pattern)
- 5 consumers crashed silently → scores WSI Voice perdidos

Sensors canonical:
1. Schema sentinels — table exists, columns canonical, indexes presentes (psycopg2 sync)
2. Persist success — happy path INSERTs row (async + cleanup)
3. Persist failure NÃO silenciado — REGRA 4 fail-loud (source inspection)
4. Pipeline surface flag — persist_failed propagado pro caller (mock-based)
5. Prometheus counter wired — observability funcional

Refs:
- /Users/paulomoraes/Documents/wedotalent_audit_2026-05-21/MISSING_TABLES_INVESTIGATION_2026-05-23.md
- Migration: alembic/versions/185_voice_wsi_results_canonical.py
- Fix: app/services/voice/wsi_pipeline.py:_persist_wsi_result + run_voice_wsi_pipeline
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

try:
    import psycopg2  # type: ignore[import-not-found]

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


_SCHEMA_TESTS_SKIP_REASON = "DATABASE_URL or psycopg2 not available"
_skip_if_no_db = pytest.mark.skipif(
    not HAS_PSYCOPG2 or not os.environ.get("DATABASE_URL"),
    reason=_SCHEMA_TESTS_SKIP_REASON,
)


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# ─────────────────────────────────────────────────────────────────────────────
# Schema sentinels (sync psycopg2 — avoids async loop conflicts)
# ─────────────────────────────────────────────────────────────────────────────


@_skip_if_no_db
def test_voice_wsi_results_table_exists():
    """F-04 P0: tabela voice_wsi_results DEVE existir após migration 185."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('voice_wsi_results')")
            row = cur.fetchone()
            assert row is not None and row[0] is not None, (
                "voice_wsi_results table missing. Run alembic upgrade head. "
                "Migration: alembic/versions/185_voice_wsi_results_canonical.py"
            )
    finally:
        conn.close()


@_skip_if_no_db
def test_voice_wsi_results_has_canonical_columns():
    """F-04 P0: schema canonical — colunas usadas em INSERT/DELETE pelos 3 consumers."""
    expected = {
        "id",
        "company_id",
        "candidate_id",
        "job_id",
        "call_id",
        "source",
        "final_score",
        "classification",
        "bloom_level",
        "context_score",
        "transcript_length",
        "created_at",
        "updated_at",
    }
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'voice_wsi_results'
                """
            )
            actual = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()

    missing = expected - actual
    assert not missing, (
        f"voice_wsi_results faltam colunas canonical: {missing}. "
        "Consumers (wsi_pipeline.py:144, voice_retention.py, lgpd_cleanup) "
        "esperam estas colunas."
    )


@_skip_if_no_db
def test_voice_wsi_results_call_id_unique():
    """F-04 P0: call_id DEVE ser UNIQUE — wsi_pipeline usa ON CONFLICT (call_id)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM pg_indexes
                WHERE tablename = 'voice_wsi_results'
                  AND indexdef ILIKE '%UNIQUE%(call_id)%'
                """
            )
            count = cur.fetchone()[0]
            assert count >= 1, (
                "voice_wsi_results.call_id deve ter constraint UNIQUE. "
                "wsi_pipeline.py:144 usa 'ON CONFLICT (call_id) DO UPDATE'."
            )
    finally:
        conn.close()


@_skip_if_no_db
def test_voice_wsi_results_company_id_index():
    """F-04 P0: company_id index — multi-tenant query path."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'voice_wsi_results'
                  AND indexname = 'ix_voice_wsi_results_company_id'
                """
            )
            row = cur.fetchone()
            assert row is not None, (
                "Missing index ix_voice_wsi_results_company_id (multi-tenant scans)."
            )
    finally:
        conn.close()


@_skip_if_no_db
def test_voice_wsi_results_created_at_index():
    """F-04 P0: created_at index — voice_retention.py 365d cron range scan."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'voice_wsi_results'
                  AND indexname = 'ix_voice_wsi_results_created_at'
                """
            )
            row = cur.fetchone()
            assert row is not None, (
                "Missing index ix_voice_wsi_results_created_at — voice_retention.py:228 "
                "faz DELETE WHERE created_at < cutoff (LGPD Art. 16 365d)."
            )
    finally:
        conn.close()


@_skip_if_no_db
def test_voice_wsi_results_candidate_id_index():
    """F-04 P0: candidate_id index — LGPD Art. 18 erasure cascade."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'voice_wsi_results'
                  AND indexname = 'ix_voice_wsi_results_candidate_id'
                """
            )
            row = cur.fetchone()
            assert row is not None, (
                "Missing index ix_voice_wsi_results_candidate_id — "
                "lgpd_cleanup_service.py:456 faz DELETE WHERE candidate_id IN (...) "
                "(LGPD Art. 18 erasure)."
            )
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Persistence behavior (REGRA 4 fail-loud) — source inspection + mock-based
# ─────────────────────────────────────────────────────────────────────────────


def test_persist_wsi_result_failure_NO_silent_swallow():
    """REGRA 4 sentinel: source DEVE conter raise no except branch.

    Antes do fix 2026-05-23, _persist_wsi_result tinha try/except Exception
    sem raise — silenciava o gap "table missing" mascarando scores perdidos.
    Esse teste é o guard regressão contra reintrodução do pattern.
    """
    import inspect

    from app.services.voice import wsi_pipeline

    src = inspect.getsource(wsi_pipeline._persist_wsi_result)
    # REGRA 4: must raise on persist failure
    assert "raise" in src, (
        "REGRA 4 violation: _persist_wsi_result NÃO contém 'raise' no except. "
        "Antes do fix 2026-05-23, try/except mudo escondia 'table missing'. "
        "Persistence failures DEVEM ser fail-loud."
    )
    # Must reference fail-loud canonical
    assert "REGRA 4" in src or "fail-loud" in src.lower(), (
        "Docstring/comment perdeu referência a REGRA 4 fail-loud canonical. "
        "Mantém para que próximo developer não reintroduza silent except."
    )


def test_persist_wsi_result_records_metrics():
    """REGRA 4: Prometheus counter wired para success + failure outcomes."""
    from app.services.voice.wsi_pipeline import (
        _WSI_PERSIST_COUNTER,
        _WSI_PERSIST_METRICS_AVAILABLE,
    )

    assert _WSI_PERSIST_METRICS_AVAILABLE, (
        "Prometheus metrics NÃO disponíveis. Verifique se prometheus_client "
        "está instalado + import block compila em wsi_pipeline.py."
    )
    assert _WSI_PERSIST_COUNTER is not None, (
        "_WSI_PERSIST_COUNTER é None — registro idempotente Prometheus quebrou. "
        "Pattern canonical: app/tools/executor.py:_TOOL_EXEC_COUNTER."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline integration (asyncio + mocks)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_voice_wsi_pipeline_surfaces_persist_failure_flag():
    """REGRA 4: pipeline payload DEVE conter persist_failed=True quando persist falha.

    Antes do fix 2026-05-23, falha de persistência era engolida silenciosamente.
    Agora caller (Celery task / webhook) recebe flag explícita para acionar
    manual review / DLQ.
    """
    from app.services.voice import wsi_pipeline

    task_data = {
        "call_id": "CALL_PIPELINE_PERSIST_FAIL_001",
        "candidate_id": "cand_pipeline_001",
        "job_id": "job_pipeline_001",
        "company_id": "company_pipeline_001",
        "transcript": (
            "Transcript de teste com tamanho suficiente para passar do limite "
            "minimo de caracteres e ser scored sem trigger de deepgram. " * 5
        ),
        "audio_url": "",
        "duration_seconds": 60,
    }

    async def _fail_persist(**kwargs):
        raise RuntimeError("simulated voice_wsi_results table dropped")

    async def _noop_notify(*args, **kwargs):
        return None

    with patch.object(wsi_pipeline, "_persist_wsi_result", side_effect=_fail_persist), \
         patch.object(wsi_pipeline, "_notify_recruiter", side_effect=_noop_notify):
        result = await wsi_pipeline.run_voice_wsi_pipeline(task_data)

    # REGRA 4 sentinel: flag DEVE estar presente no payload
    assert result.get("persist_failed") is True, (
        "REGRA 4 violation: persist failure NÃO surfaced no payload. "
        f"got: {result}. "
        "Caller (Celery task) precisa do flag para acionar manual review."
    )
    assert result.get("needs_manual_review") is True, (
        "REGRA 4: needs_manual_review flag faltando — necessário para DLQ/triage."
    )
    assert "persist_error" in result, (
        "REGRA 4: persist_error string faltando — necessário para log estruturado."
    )
    # Scoring DEVE ter rodado (status=completed, score presente)
    assert result.get("status") == "completed"
    assert "wsi_score" in result


@pytest.mark.asyncio
async def test_run_voice_wsi_pipeline_success_no_persist_failed_flag():
    """REGRA 4 inverse: happy path NÃO deve setar persist_failed flag."""
    from app.services.voice import wsi_pipeline

    task_data = {
        "call_id": "CALL_PIPELINE_SUCCESS_001",
        "candidate_id": "cand_success_001",
        "job_id": "job_success_001",
        "company_id": "company_success_001",
        "transcript": "Transcript de teste com tamanho suficiente para scoring. " * 10,
        "audio_url": "",
        "duration_seconds": 60,
    }

    async def _ok_persist(**kwargs):
        return None

    async def _noop_notify(*args, **kwargs):
        return None

    with patch.object(wsi_pipeline, "_persist_wsi_result", side_effect=_ok_persist), \
         patch.object(wsi_pipeline, "_notify_recruiter", side_effect=_noop_notify):
        result = await wsi_pipeline.run_voice_wsi_pipeline(task_data)

    assert "persist_failed" not in result, (
        "Happy path NÃO deve incluir persist_failed flag. "
        f"got keys: {sorted(result.keys())}"
    )
    assert result.get("status") == "completed"


@_skip_if_no_db
@pytest.mark.asyncio
async def test_persist_wsi_result_success_inserts_row():
    """F-04: happy path — INSERT row + log success.

    Usa psycopg2 sync para verify (evita async loop conflict).
    """
    from app.services.voice.wsi_pipeline import _persist_wsi_result

    wsi_result = {
        "final_score": 4.2,
        "classification": "alto",
        "bloom_level": 5,
        "context_score": 3.8,
    }
    test_call_id = "TEST_CALL_PERSIST_SUCCESS_001"
    test_company_id = "test_company_persist_001"

    try:
        await _persist_wsi_result(
            wsi_result=wsi_result,
            candidate_id="cand_test_001",
            job_id="job_test_001",
            company_id=test_company_id,
            call_id=test_call_id,
            transcript_length=350,
        )

        # Verify via sync psycopg2 (independent loop)
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT final_score, classification, company_id "
                    "FROM voice_wsi_results WHERE call_id = %s",
                    (test_call_id,),
                )
                row = cur.fetchone()
                assert row is not None, "Row não foi inserida"
                assert float(row[0]) == 4.2, f"final_score esperado 4.2, got {row[0]}"
                assert row[1] == "alto"
                assert row[2] == test_company_id
        finally:
            conn.close()
    finally:
        # Cleanup
        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM voice_wsi_results WHERE call_id = %s",
                    (test_call_id,),
                )
                conn.commit()
        finally:
            conn.close()
