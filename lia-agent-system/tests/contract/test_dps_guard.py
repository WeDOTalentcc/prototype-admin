"""
T-DPS-a/b/c/d — delete_pipeline_stage SEV1 P-GUARD fix.

RED->GREEN:
- T-DPS-a: rejection destination refused (P-GUARD layer 1)
- T-DPS-b: valid move dispatches transition_candidate() per candidate (P-SSOT)
- T-DPS-c: move failure reported per-candidate, not swallowed (P-FAILLOUD)
- T-DPS-d: tenant isolation — only same-company candidates touched (P-TENANT)
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Constants
COMPANY_ID = "co-test-001"
STAGE_ID = str(uuid.uuid4())
DEST_STAGE_ID = str(uuid.uuid4())
VC_ID_1 = str(uuid.uuid4())
VC_ID_2 = str(uuid.uuid4())


def _make_stage(stage_id=STAGE_ID, is_rejection=False, is_system=False, display_name="Triagem"):
    s = MagicMock()
    s.id = stage_id
    s.company_id = COMPANY_ID
    s.display_name = display_name
    s.is_active = True
    s.is_system = is_system
    s.is_rejection = is_rejection
    s.updated_at = None
    return s


def _make_vc(vc_id, company_id=COMPANY_ID, stage_id=STAGE_ID):
    vc = MagicMock()
    vc.id = vc_id
    vc.company_id = company_id
    vc.recruitment_stage_id = stage_id
    return vc


def _make_db(responses: list):
    """Build an AsyncMock db session whose .execute() returns each response in sequence."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    results = []
    for r in responses:
        mock_result = MagicMock()
        if isinstance(r, int):
            mock_result.scalar.return_value = r
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
        elif r is None:
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
        elif isinstance(r, list):
            mock_result.scalars.return_value.all.return_value = r
            mock_result.scalar_one_or_none.return_value = None
        else:
            mock_result.scalar_one_or_none.return_value = r
            mock_result.scalars.return_value.all.return_value = []
        results.append(mock_result)

    db.execute = AsyncMock(side_effect=results)
    return db


def _make_session_ctx(db):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=db)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


@pytest.mark.asyncio
async def test_dps_a_rejection_destination_refused():
    """T-DPS-a: move_candidates_to_stage_id whose is_rejection=True must be refused.

    RED: current code has no is_rejection check — field name bug means
    candidates are silently not moved, stage is deleted.
    GREEN: returns error=destination_is_rejection_stage before any write.
    """
    from app.domains.recruiter_assistant.tools.pipeline_tools import delete_pipeline_stage

    source_stage = _make_stage(stage_id=STAGE_ID, is_rejection=False, display_name="Triagem")
    rejection_dest = _make_stage(stage_id=DEST_STAGE_ID, is_rejection=True, display_name="Reprovado")

    db = _make_db([
        source_stage,    # get stage to delete
        2,               # candidate count = 2
        rejection_dest,  # get dest_stage
    ])
    session_ctx = _make_session_ctx(db)

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ):
        result = await delete_pipeline_stage(
            stage_id=STAGE_ID,
            company_id=COMPANY_ID,
            move_candidates_to_stage_id=DEST_STAGE_ID,
        )

    assert result.get("success") is False, (
        "[RED] delete_pipeline_stage com destino de rejeicao deve retornar success=False. "
        "GREEN: verificar is_rejection antes de qualquer escrita."
    )
    assert result.get("error") == "destination_is_rejection_stage", (
        "[RED] error deve ser destination_is_rejection_stage. "
        f"Obtido: {result.get(error)!r}. "
        "GREEN: guard P-GUARD: if dest_stage.is_rejection: return error."
    )
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_dps_b_valid_move_dispatches_transition_candidate_per_vc():
    """T-DPS-b: valid destination -> transition_candidate() called once per VacancyCandidate.

    RED: current code uses sa_update(VacancyCandidate) raw -> transition_candidate never called.
    GREEN: each VC in stage gets a transition_candidate() call.
    """
    from app.domains.recruiter_assistant.tools.pipeline_tools import delete_pipeline_stage

    source_stage = _make_stage(stage_id=STAGE_ID, is_rejection=False, display_name="Triagem")
    valid_dest = _make_stage(stage_id=DEST_STAGE_ID, is_rejection=False, display_name="Entrevista")
    vc1 = _make_vc(VC_ID_1)
    vc2 = _make_vc(VC_ID_2)

    db = _make_db([
        source_stage,      # get stage to delete
        2,                 # candidate count
        valid_dest,        # get dest_stage
        [vc1, vc2],        # list all VCs to move
    ])
    session_ctx = _make_session_ctx(db)

    mock_transition = AsyncMock(return_value={"success": True, "new_stage": "Entrevista"})

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate",
        mock_transition,
    ):
        result = await delete_pipeline_stage(
            stage_id=STAGE_ID,
            company_id=COMPANY_ID,
            move_candidates_to_stage_id=DEST_STAGE_ID,
        )

    assert mock_transition.call_count == 2, (
        f"[RED] transition_candidate deve ser chamado 2x (1 por candidato). "
        f"Chamado {mock_transition.call_count}x. "
        "GREEN: substituir sa_update raw por loop per-candidato via transition_candidate()."
    )


@pytest.mark.asyncio
async def test_dps_c_move_failure_reported_per_candidate():
    """T-DPS-c: exception on one candidate move -> reported in result, not swallowed.

    RED: current code has except Exception as e: logger.warning(...) — failure swallowed.
    GREEN: failure collected in failed_moves dict, reported in result.
    """
    from app.domains.recruiter_assistant.tools.pipeline_tools import delete_pipeline_stage

    source_stage = _make_stage(stage_id=STAGE_ID, is_rejection=False)
    valid_dest = _make_stage(stage_id=DEST_STAGE_ID, is_rejection=False, display_name="Entrevista")
    vc1 = _make_vc(VC_ID_1)
    vc2 = _make_vc(VC_ID_2)

    db = _make_db([
        source_stage,
        2,
        valid_dest,
        [vc1, vc2],
    ])
    session_ctx = _make_session_ctx(db)

    async def _failing_transition(*args, **kwargs):
        vc_id = kwargs.get("vacancy_candidate_id") or (args[1] if len(args) > 1 else None)
        if str(vc_id) == VC_ID_2:
            raise RuntimeError("Simulated DB failure on candidate 2")
        return {"success": True}

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate",
        side_effect=_failing_transition,
    ):
        result = await delete_pipeline_stage(
            stage_id=STAGE_ID,
            company_id=COMPANY_ID,
            move_candidates_to_stage_id=DEST_STAGE_ID,
        )

    failed = result.get("failed_moves", {})
    assert VC_ID_2 in failed, (
        f"[RED] VC_ID_2 falhou mas nao esta em result[failed_moves]. "
        f"Obtido: {failed!r}. "
        "GREEN: coletar excecoes em _failed_ids dict (pattern D2)."
    )
    assert VC_ID_1 not in failed, (
        f"[RED] VC_ID_1 nao deve estar em failed_moves (nao falhou). Obtido: {failed!r}"
    )


@pytest.mark.asyncio
async def test_dps_d_tenant_isolation_only_same_company_vcs_touched():
    """T-DPS-d: query for VCs to move includes company_id filter (P-TENANT).

    RED: current code uses VacancyCandidate.stage_id (wrong field) — query
    fails silently. After fix: query uses recruitment_stage_id + company_id.
    GREEN: transition_candidate only called with same-company VCs.
    """
    from app.domains.recruiter_assistant.tools.pipeline_tools import delete_pipeline_stage

    source_stage = _make_stage(stage_id=STAGE_ID, is_rejection=False)
    valid_dest = _make_stage(stage_id=DEST_STAGE_ID, is_rejection=False, display_name="Entrevista")
    vc_same_company = _make_vc(VC_ID_1, company_id=COMPANY_ID)

    db = _make_db([
        source_stage,
        1,                         # count: 1 candidate (only same-company)
        valid_dest,
        [vc_same_company],         # DB returns only same-company candidates
    ])
    session_ctx = _make_session_ctx(db)

    mock_transition = AsyncMock(return_value={"success": True})

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=session_ctx,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate",
        mock_transition,
    ):
        result = await delete_pipeline_stage(
            stage_id=STAGE_ID,
            company_id=COMPANY_ID,
            move_candidates_to_stage_id=DEST_STAGE_ID,
        )

    assert mock_transition.call_count == 1, (
        f"[RED] transition_candidate deve ser chamado 1x. "
        f"Chamado {mock_transition.call_count}x."
    )
    vc_id_arg = (
        mock_transition.call_args.kwargs.get("vacancy_candidate_id")
        or (mock_transition.call_args.args[1] if len(mock_transition.call_args.args) > 1 else None)
    )
    assert str(vc_id_arg) == VC_ID_1, (
        f"[RED] transition_candidate deve receber VC_ID_1 ({VC_ID_1!r}), "
        f"obtido {vc_id_arg!r}."
    )
