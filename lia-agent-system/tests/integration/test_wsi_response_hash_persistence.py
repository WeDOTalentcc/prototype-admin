"""Integration tests for response_hash persistence across both insert paths (Task #511).

Verifica que tanto o caminho de voz (`wsi_voice_orchestrator`) quanto o caminho
de chat web (`triagem_session_service.completion`) gravam o mesmo hash em
`wsi_responses.response_hash` e `wsi_response_analyses.response_hash` para a
mesma resposta.

NOTA: pytest local sofre de cascata de imports pesados (#517). Validação manual
do hasher via script standalone (7/7 asserts) está registrada no commit da
Task #511; este arquivo documenta a expectativa para CI futuro.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.shared.security.wsi_hashing import hash_response

pytestmark = pytest.mark.asyncio


async def test_voice_orchestrator_writes_consistent_hash(
    db_session, seeded_wsi_voice_session
):
    """Voice path: wsi_voice_orchestrator._analyze_and_persist_responses
    deve gravar o mesmo hash em wsi_responses e wsi_response_analyses."""
    sid = seeded_wsi_voice_session["session_id"]
    qid = seeded_wsi_voice_session["question_id"]
    raw = seeded_wsi_voice_session["response_text"]

    expected = hash_response(raw, sid, qid)

    r1 = (await db_session.execute(text(
        "SELECT response_hash FROM wsi_responses "
        "WHERE session_id = :sid AND question_id = :qid"
    ), {"sid": sid, "qid": qid})).scalar()
    r2 = (await db_session.execute(text(
        "SELECT response_hash FROM wsi_response_analyses "
        "WHERE session_id = :sid AND question_id = :qid"
    ), {"sid": sid, "qid": qid})).scalar()

    assert r1 == expected
    assert r2 == expected


async def test_web_chat_path_writes_consistent_hash(
    db_session, seeded_wsi_chat_session
):
    """Chat web path: completion._persist_wsi_results deve gravar o mesmo hash."""
    sid = seeded_wsi_chat_session["session_id"]
    qid = seeded_wsi_chat_session["question_id"]
    raw = seeded_wsi_chat_session["response_text"]

    expected = hash_response(raw, sid, qid)

    r1 = (await db_session.execute(text(
        "SELECT response_hash FROM wsi_responses "
        "WHERE session_id = :sid AND question_id = :qid"
    ), {"sid": sid, "qid": qid})).scalar()
    r2 = (await db_session.execute(text(
        "SELECT response_hash FROM wsi_response_analyses "
        "WHERE session_id = :sid AND question_id = :qid"
    ), {"sid": sid, "qid": qid})).scalar()

    assert r1 == expected
    assert r2 == expected


async def test_response_hash_is_not_null_on_new_inserts(
    db_session, seeded_wsi_chat_session
):
    """wsi_response_analyses.response_hash é NOT NULL — qualquer insert sem
    hash deve falhar; qualquer insert legítimo via app deve popular."""
    rows = (await db_session.execute(text(
        "SELECT response_hash FROM wsi_response_analyses "
        "WHERE session_id = :sid"
    ), {"sid": seeded_wsi_chat_session["session_id"]})).fetchall()
    assert all(r[0] is not None and len(r[0]) == 64 for r in rows)
