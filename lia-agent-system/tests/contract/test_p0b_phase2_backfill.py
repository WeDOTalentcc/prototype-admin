"""P0.B Phase 2 contract sensor (audit 2026-05-21) — backfill task canonical.

Garante que a task ``pii.backfill_encrypt_interview_offer_existing``
esta registrada e exposta corretamente no Celery + tasks package.

NAO exercita encryption real (precisa DB live + FIELD_ENCRYPTION_KEY) —
apenas o contract canonical da task. End-to-end ficou para integration
tests separados.
"""
from __future__ import annotations

import pytest


class TestP0BPhase2TaskContract:
    """Task canonical registrada e exportada."""

    def test_task_importable_from_package(self):
        """Task acessivel via app.jobs.tasks.* (canonical export)."""
        from app.jobs.tasks import (
            pii_backfill_encrypt_interview_offer_existing_task,
        )
        assert pii_backfill_encrypt_interview_offer_existing_task is not None

    def test_task_in_all(self):
        """Task no __all__ list canonical."""
        from app.jobs import tasks as tasks_pkg
        assert "pii_backfill_encrypt_interview_offer_existing_task" in tasks_pkg.__all__

    def test_task_canonical_celery_name(self):
        """Celery task name segue convencao canonical 'pii.*'.

        Pattern: pii_backfill_encrypt_existing (Candidate, migration 060/061)
                 pii_backfill_encrypt_interview_offer_existing (este, migration 160).
        """
        from app.jobs.tasks import (
            pii_backfill_encrypt_interview_offer_existing_task,
        )
        task = pii_backfill_encrypt_interview_offer_existing_task
        # Celery task object exposes .name
        assert hasattr(task, "name")
        assert task.name == "pii.backfill_encrypt_interview_offer_existing"

    def test_task_signature_accepts_batch_size_and_dry_run(self):
        """Pattern canonical: batch_size + dry_run kwargs (mesmo que Phase 1).

        Permite operacao seguranca (dry-run primeiro pra validar count antes
        de aplicar). batch_size canonical default 500.
        """
        import inspect
        from app.jobs.tasks.compliance import (
            pii_backfill_encrypt_interview_offer_existing_task,
        )
        # Celery wraps the underlying function via .run; introspect it
        underlying = pii_backfill_encrypt_interview_offer_existing_task.run
        sig = inspect.signature(underlying)
        params = sig.parameters
        assert "batch_size" in params
        assert params["batch_size"].default == 500
        assert "dry_run" in params
        assert params["dry_run"].default is False
