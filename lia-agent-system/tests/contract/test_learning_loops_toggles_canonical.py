"""
Anti-drift sensor para o helper canonical
``app/shared/services/learning_loops_toggles.py``.

Registrado 2026-05-21 (audit follow-up). Substitui duas implementações
paralelas em domain services que estavam divergindo silenciosamente
(``BigFiveDepartmentService._get_toggles`` + ``TransitionDispatchService._load_learning_loops_toggles``).

Esses testes garantem que:
1. O helper canonical existe e é importável do shared module.
2. Defaults canonical são retornados quando company_id é vazio.
3. Defaults canonical são retornados quando DB raise (fail-safe).
4. Os 2 callers conhecidos (BigFive + TransitionDispatch) delegam ao
   helper em vez de reimplementar a leitura — qualquer refactor que
   reintroduza a duplicação falha aqui.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_helper_returns_defaults_for_empty_company_id():
    from app.shared.services.learning_loops_toggles import (
        load_learning_loops_toggles,
    )
    from lia_models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    out = await load_learning_loops_toggles("", db=MagicMock())
    assert out == AUTOMATION_RULES_DEFAULTS["learning_loops"]


@pytest.mark.asyncio
async def test_helper_returns_defaults_on_db_error():
    """Fail-soft: any DB error from the repository returns canonical
    defaults. Callers can rely on the helper to never raise."""
    from app.shared.services.learning_loops_toggles import (
        load_learning_loops_toggles,
    )
    from lia_models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    db = MagicMock()
    # Patch repo to raise.
    import app.domains.hiring_policy.repositories.hiring_policy_repository as repo_mod
    failing_repo = MagicMock()
    failing_repo.get_by_company = AsyncMock(side_effect=RuntimeError("db down"))
    repo_mod.HiringPolicyRepository = MagicMock(return_value=failing_repo)

    out = await load_learning_loops_toggles("co-1", db)
    assert out == AUTOMATION_RULES_DEFAULTS["learning_loops"]


@pytest.mark.asyncio
async def test_helper_returns_policy_learning_loops_when_set():
    from app.shared.services.learning_loops_toggles import (
        load_learning_loops_toggles,
    )

    policy = MagicMock()
    policy.automation_rules = {
        "learning_loops": {
            "enabled": True,
            "wsi_question_effectiveness": True,
            "bigfive_company_culture": False,
        }
    }
    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=policy)
    import app.domains.hiring_policy.repositories.hiring_policy_repository as repo_mod
    repo_mod.HiringPolicyRepository = MagicMock(return_value=repo)

    out = await load_learning_loops_toggles("co-1", MagicMock())
    assert out.get("wsi_question_effectiveness") is True
    assert out.get("bigfive_company_culture") is False


def test_bigfive_service_delegates_to_canonical_helper():
    """Source-level pin: the migrated wrapper ``_get_toggles`` must contain
    the canonical import. If a future commit re-inlines the policy fetch,
    this test catches it before the duplicate logic ships."""
    import inspect
    from app.domains.job_creation.services import bigfive_service
    src = inspect.getsource(bigfive_service.BigFiveDepartmentService._get_toggles)
    assert "load_learning_loops_toggles" in src, (
        "BigFiveDepartmentService._get_toggles no longer delegates to the "
        "canonical helper. Re-introducing the inline policy fetch is "
        "exactly the duplication this sensor prevents."
    )


def test_transition_dispatch_delegates_to_canonical_helper():
    """Source-level pin for the second caller — same rationale as above."""
    import inspect
    from app.domains.communication.services import transition_dispatch_service
    src = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._load_learning_loops_toggles
    )
    assert "load_learning_loops_toggles" in src, (
        "TransitionDispatchService._load_learning_loops_toggles no longer "
        "delegates to the canonical helper."
    )
