"""Sentinela — Task #1326: falhas na escrita de learning_patterns não podem
mais falhar em silêncio.

Antes: ``_update_patterns_from_feedback`` engolia QUALQUER exceção (rollback +
um único ``logger.error``) e retornava ``None``. O rollback expirava a
``interaction_feedback`` recém-commitada, então o caller
(``capture_regeneration`` / ``capture_correction_delta``) estourava
``MissingGreenlet`` ao ler ``fb.id`` — um erro secundário que mascarava a causa
raiz no banco.

Agora:
- ``_update_patterns_from_feedback`` RETORNA ``bool`` (True = commit, False =
  falha) e, na falha, emite log estruturado com a causa raiz +
  ``sentry_sdk.capture_exception`` (sinal atribuível), sem relançar.
- O reporter recebe apenas snapshots pré-rollback (nunca o objeto ORM), então
  ele próprio não dispara um lazy-load → MissingGreenlet.
- Os callers restauram o id commitado via ``set_committed_value`` (sem ida ao
  banco) quando o pattern-write falha, devolvendo um resultado honesto.

Tudo offline (db/repo/sentry mockados) — não toca prod-local, sem row leak.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


def _make_feedback():
    from lia_models.feedback import InteractionFeedback

    fb = InteractionFeedback()
    fb.id = uuid4()
    fb.company_id = uuid4()
    fb.intent = None
    fb.stage = None
    fb.thumbs = "down"
    fb.rating = None
    fb.correction = None
    fb.lia_response = "Resposta ruim."
    fb.user_message = "oi"
    return fb


@pytest.mark.asyncio
async def test_pattern_write_success_returns_true():
    from app.domains.analytics.services import feedback_service as fs_mod

    fb = _make_feedback()

    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    fake_repo = MagicMock()
    fake_repo.find_active_pattern = AsyncMock(return_value=None)

    with patch.object(fs_mod, "FeedbackRepository", return_value=fake_repo):
        ok = await fs_mod.feedback_service._update_patterns_from_feedback(fb, db)

    assert ok is True
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_pattern_write_failure_returns_false_and_reports():
    """Falha no commit → rollback, log estruturado, Sentry capture, retorna
    False e NÃO relança."""
    from app.domains.analytics.services import feedback_service as fs_mod

    fb = _make_feedback()

    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock(side_effect=RuntimeError("DatatypeMismatchError boom"))
    db.rollback = AsyncMock()

    fake_repo = MagicMock()
    fake_repo.find_active_pattern = AsyncMock(return_value=None)

    captured = []

    def _fake_capture(exc, **kwargs):
        captured.append((exc, kwargs))

    fake_sentry = MagicMock()
    fake_sentry.capture_exception = _fake_capture

    with patch.object(fs_mod, "FeedbackRepository", return_value=fake_repo), patch.dict(
        "sys.modules", {"sentry_sdk": fake_sentry}
    ):
        ok = await fs_mod.feedback_service._update_patterns_from_feedback(fb, db)

    assert ok is False  # honest signal, not None
    db.rollback.assert_awaited_once()
    # Attributable Sentry capture with the right alert tag + tenant.
    assert len(captured) == 1
    exc, kwargs = captured[0]
    assert isinstance(exc, RuntimeError)
    tags = kwargs.get("tags", {})
    assert tags.get("alert_type") == "feedback_learning_pattern_write_failed"
    assert tags.get("company_id") == str(fb.company_id)


@pytest.mark.asyncio
async def test_reporter_uses_snapshots_not_live_orm_object():
    """O reporter NUNCA toca o objeto ORM (que o rollback pode ter expirado) —
    recebe apenas snapshots, então não dispara um lazy-load secundário."""
    from app.domains.analytics.services import feedback_service as fs_mod

    svc = fs_mod.feedback_service
    company = uuid4()
    fid = uuid4()

    # A sentinel that explodes if ANY attribute is read — proves the reporter
    # never touches the live (possibly expired) ORM instance.
    class _Exploding:
        def __getattr__(self, name):  # pragma: no cover - guard
            raise AssertionError(f"reporter touched ORM attr {name!r}")

    fake_sentry = MagicMock()
    with patch.dict("sys.modules", {"sentry_sdk": fake_sentry}):
        # Should not raise — only snapshots are used.
        svc._report_pattern_write_failure(
            RuntimeError("x"), company, "general", fid
        )

    fake_sentry.capture_exception.assert_called_once()


def test_restore_committed_feedback_id_avoids_lazy_load():
    """Restaurar o id via set_committed_value deixa ``fb.id`` legível sem IO."""
    from app.domains.analytics.services import feedback_service as fs_mod

    fb = _make_feedback()
    fid = fb.id
    # Simulate expiry by clearing the instance __dict__ entry.
    from sqlalchemy import inspect as sa_inspect

    state = sa_inspect(fb)
    state.dict.pop("id", None)

    fs_mod.feedback_service._restore_committed_feedback_id(fb, fid)

    assert fb.id == fid


@pytest.mark.asyncio
async def test_caller_restores_id_when_pattern_write_fails():
    """``record_implicit_negative`` chama o restore quando o pattern-write
    falha, devolvendo o feedback com id legível (resultado honesto)."""
    from app.domains.analytics.services import feedback_service as fs_mod

    svc = fs_mod.FeedbackService()

    fb = _make_feedback()
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    restored = {}

    def _fake_restore(feedback, feedback_id):
        restored["id"] = feedback_id

    with patch.object(
        fs_mod, "InteractionFeedback", return_value=fb
    ), patch.object(
        svc, "_update_patterns_from_feedback", AsyncMock(return_value=False)
    ), patch.object(
        svc, "_restore_committed_feedback_id", side_effect=_fake_restore
    ):
        result = await svc.record_implicit_negative(
            session_id="s",
            company_id=str(fb.company_id),
            user_id="u",
            signal_type="regeneration",
            message_context={"message_id": "m", "lia_response": "r"},
            db=db,
        )

    assert result is fb
    assert restored.get("id") == fb.id
