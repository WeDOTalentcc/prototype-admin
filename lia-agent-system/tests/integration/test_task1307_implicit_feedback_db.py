"""Task #1307 · Integration · implicit feedback end-to-end DB persistence.

Task #1299 added capture of THREE implicit feedback signals (regeneration,
correction_delta, abandonment). The pre-existing sentinels are OFFLINE only
(pure criterion, FairnessGuard gate, route registration, capture-method
contract, pre-DB short-circuits) — none exercise the real DB write path.

This suite drives ``ImplicitFeedbackService`` capture methods against a real
PostgreSQL and asserts what actually lands on disk.

Intended contract per signal type:

- ``regeneration``     → learning_signals(domain=implicit_regeneration)
                         + interaction_feedback(feedback_category=
                           implicit_regeneration, thumbs/rating NULL)
                         + learning_patterns.negative_feedback_count += 1
- ``correction_delta`` → same three writes (domain/category =
                           implicit_correction_delta)
- ``abandonment``      → learning_signals(domain=implicit_abandonment) ONLY.
                         It is signals-ONLY by design (the capture method never
                         calls ``record_implicit_negative``), so it writes
                         NEITHER interaction_feedback NOR learning_patterns — a
                         single ignored answer must never flip a pattern.

KNOWN PRE-EXISTING BUG (see the two xfail tests below).
``regeneration`` and ``correction_delta`` route through
``FeedbackService.record_implicit_negative`` →
``_update_patterns_from_feedback``, which writes ``learning_patterns``. That
write currently FAILS at the DB layer because TWO different SQLAlchemy models
both map to the ``learning_patterns`` table via ``extend_existing=True``:

  * ``lia_models.feedback.LearningPattern``         → company_id ``UUID``,
                                                       confidence ``Float``
  * ``lia_models.intelligent_cache.LearningPattern`` → company_id ``String``,
                                                       confidence ``String``

The intelligent_cache String columns win in the shared Table metadata, so the
INSERT binds ``company_id`` (and ``confidence``) as VARCHAR against the real
UUID/double-precision columns → ``asyncpg DatatypeMismatchError``. The error is
swallowed by ``_update_patterns_from_feedback``'s broad ``except`` (after a
rollback that expires the feedback row), and the capture method then raises
``MissingGreenlet`` on the expired attribute. Net effect: implicit (and
explicit) ``learning_patterns`` demotion silently never happens in production.

Resolving the mapper conflict belongs to the separate "Audit all model shims
for mapper conflicts" task. The two regeneration/correction tests are marked
``xfail(strict=True)`` so they (a) document the intended end-to-end contract and
(b) flip to a hard build FAILURE the moment the conflict is fixed, forcing the
``xfail`` marker to be removed and the test promoted to a permanent regression
guard.

Skip se sem DATABASE_URL (mesmo padrão de
tests/integration/test_w3021_learning_signal_repository.py).
"""
from __future__ import annotations

import os
import uuid

import pytest

from app.shared.learning.implicit_feedback_service import (
    ImplicitFeedbackService,
    SIGNAL_ABANDONMENT,
    SIGNAL_CORRECTION_DELTA,
    SIGNAL_REGENERATION,
)

_MAPPER_CONFLICT_REASON = (
    "learning_patterns write blocked by a pre-existing LearningPattern mapper "
    "conflict (lia_models.feedback uuid/Float vs lia_models.intelligent_cache "
    "String) sharing the learning_patterns table via extend_existing — the "
    "INSERT binds company_id as VARCHAR against the UUID column "
    "(asyncpg DatatypeMismatchError, swallowed). Tracked by 'Audit all model "
    "shims for mapper conflicts'. Remove this xfail once that conflict is fixed."
)


def _get_async_database_url():
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment)
    )
    return url


@pytest.fixture
async def pg_session_and_company():
    """Yield (session, company_uuid). Cleans all three tables for that company
    on both setup and teardown so a re-run is idempotent."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    company_id = str(uuid.uuid4())
    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async def _cleanup(session):
        await session.execute(
            text("DELETE FROM learning_signals WHERE company_id = :cid"),
            {"cid": company_id},
        )
        await session.execute(
            text("DELETE FROM interaction_feedback WHERE company_id = CAST(:cid AS uuid)"),
            {"cid": company_id},
        )
        await session.execute(
            text("DELETE FROM learning_patterns WHERE company_id = CAST(:cid AS uuid)"),
            {"cid": company_id},
        )
        await session.commit()

    async with sm() as session:
        await _cleanup(session)
        try:
            yield session, company_id
        finally:
            try:
                await session.rollback()
            except Exception:
                pass
            await _cleanup(session)

    await engine.dispose()


async def _learning_signal_rows(session, company_id, domain):
    from sqlalchemy import text

    result = await session.execute(
        text(
            "SELECT id, feedback_type, original_response, corrected_response, "
            "signal_metadata FROM learning_signals "
            "WHERE company_id = :cid AND domain = :dom"
        ),
        {"cid": company_id, "dom": domain},
    )
    return result.fetchall()


async def _interaction_feedback_rows(session, company_id, category):
    from sqlalchemy import text

    result = await session.execute(
        text(
            "SELECT id, thumbs, rating, correction, feedback_category "
            "FROM interaction_feedback "
            "WHERE company_id = CAST(:cid AS uuid) AND feedback_category = :cat"
        ),
        {"cid": company_id, "cat": category},
    )
    return result.fetchall()


async def _learning_pattern_negative_total(session, company_id):
    from sqlalchemy import text

    result = await session.execute(
        text(
            "SELECT COALESCE(SUM(negative_feedback_count), 0) "
            "FROM learning_patterns WHERE company_id = CAST(:cid AS uuid)"
        ),
        {"cid": company_id},
    )
    return int(result.scalar() or 0)


async def _learning_pattern_count(session, company_id):
    from sqlalchemy import text

    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM learning_patterns "
            "WHERE company_id = CAST(:cid AS uuid)"
        ),
        {"cid": company_id},
    )
    return int(result.scalar() or 0)


# ===== regeneration (strong negative) — full three-write contract =====


@pytest.mark.xfail(strict=True, reason=_MAPPER_CONFLICT_REASON)
@pytest.mark.asyncio
async def test_regeneration_persists_all_three_writes(pg_session_and_company):
    session, company_id = pg_session_and_company
    svc = ImplicitFeedbackService()

    result = await svc.capture_regeneration(
        db=session,
        company_id=company_id,
        user_id="user-1307-regen",
        session_id="sess-1307-regen",
        superseded_message_id="msg-regen-1",
        superseded_response="A resposta inicial da LIA descrevendo o pipeline da vaga.",
        prior_user_message="Refaça o resumo da vaga por favor",
        intent="job_summary",
        stage="intake",
        confidence_at_generation=0.7,
    )

    assert result.persisted is True, result.skipped_reason
    assert result.signal_type == SIGNAL_REGENERATION
    assert result.signal_id is not None
    assert result.feedback_id is not None

    # learning_signals row
    signals = await _learning_signal_rows(
        session, company_id, "implicit_regeneration"
    )
    assert len(signals) == 1
    assert signals[0][1] == SIGNAL_REGENERATION

    # interaction_feedback row tagged implicit_regeneration, NULL thumbs/rating
    fb = await _interaction_feedback_rows(
        session, company_id, "implicit_regeneration"
    )
    assert len(fb) == 1
    assert fb[0][1] is None  # thumbs
    assert fb[0][2] is None  # rating
    assert fb[0][3] is None  # correction
    assert fb[0][4] == "implicit_regeneration"

    # learning_patterns demotion (regeneration is a STRONG signal)
    assert await _learning_pattern_negative_total(session, company_id) == 1


# ===== correction_delta (negative) — full three-write contract =====


@pytest.mark.xfail(strict=True, reason=_MAPPER_CONFLICT_REASON)
@pytest.mark.asyncio
async def test_correction_delta_persists_all_three_writes(pg_session_and_company):
    session, company_id = pg_session_and_company
    svc = ImplicitFeedbackService()

    result = await svc.capture_correction_delta(
        db=session,
        company_id=company_id,
        user_id="user-1307-delta",
        session_id="sess-1307-delta",
        source_message_id="msg-delta-1",
        original_response="Sugestão original da LIA para a mensagem ao candidato.",
        used_text="Versão editada pelo recrutador antes de enviar ao candidato.",
        intent="candidate_message",
        stage="outreach",
        confidence_at_generation=0.65,
    )

    assert result.persisted is True, result.skipped_reason
    assert result.signal_type == SIGNAL_CORRECTION_DELTA
    assert result.signal_id is not None
    assert result.feedback_id is not None

    signals = await _learning_signal_rows(
        session, company_id, "implicit_correction_delta"
    )
    assert len(signals) == 1
    assert signals[0][1] == SIGNAL_CORRECTION_DELTA

    fb = await _interaction_feedback_rows(
        session, company_id, "implicit_correction_delta"
    )
    assert len(fb) == 1
    assert fb[0][1] is None  # thumbs
    assert fb[0][2] is None  # rating
    assert fb[0][3] is None  # correction
    assert fb[0][4] == "implicit_correction_delta"

    assert await _learning_pattern_negative_total(session, company_id) == 1


# ===== abandonment (weak negative — signals-ONLY) — fully working today =====


@pytest.mark.asyncio
async def test_abandonment_persists_signal_only(pg_session_and_company):
    session, company_id = pg_session_and_company
    svc = ImplicitFeedbackService()

    # Crafted to satisfy is_abandonment_candidate: substantive answer (no
    # trailing '?'), next message is a real utterance on a disjoint topic.
    result = await svc.capture_abandonment(
        db=session,
        company_id=company_id,
        user_id="user-1307-abandon",
        session_id="sess-1307-abandon",
        abandoned_message_id="msg-abandon-1",
        abandoned_response=(
            "Para configurar o pipeline da vaga recomendo definir cinco etapas "
            "claras com responsaveis nomeados para cada fase do processo."
        ),
        next_user_message="qual horario funciona melhor amanha cedo",
        intent="pipeline_setup",
        stage="config",
    )

    assert result.persisted is True, result.skipped_reason
    assert result.signal_type == SIGNAL_ABANDONMENT
    assert result.signal_id is not None
    # signals-ONLY: no interaction_feedback row → no feedback_id
    assert result.feedback_id is None

    # learning_signals row exists
    signals = await _learning_signal_rows(
        session, company_id, "implicit_abandonment"
    )
    assert len(signals) == 1
    assert signals[0][1] == SIGNAL_ABANDONMENT

    # NO interaction_feedback row (abandonment never calls record_implicit_negative)
    fb = await _interaction_feedback_rows(
        session, company_id, "implicit_abandonment"
    )
    assert len(fb) == 0

    # NO learning_patterns touched — a single ignored answer must not flip a pattern
    assert await _learning_pattern_count(session, company_id) == 0
    assert await _learning_pattern_negative_total(session, company_id) == 0
