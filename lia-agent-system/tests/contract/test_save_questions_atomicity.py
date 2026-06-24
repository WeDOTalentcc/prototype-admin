"""Sensor (audit C9/#1 2026-06-05): /wsi/questions/save NAO pode retornar
success:True quando o set versionado (save_question_set) falha.

Bug: o flat (upsert_job_screening_question) e o set versionado compartilham a
mesma transacao; o db.commit() vive dentro de save_question_set. Se ele levanta,
o flat fica uncommitted, mas o except apenas logava warning e caia no
``return success:True`` — mascarando a falha (orfao flat sem set versionado).
Fix: rollback (descarta o flat) + return success:False (propaga a falha).
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.wsi import questions as q_mod

_JVCR_PATH = (
    "app.domains.job_management.repositories."
    "job_vacancy_crud_repository.JobVacancyCrudRepository"
)


def _mocks():
    # ownership gate -> True (passa)
    repo_inst = MagicMock()
    repo_inst.owned_by_company = AsyncMock(return_value=True)
    jvcr_cls = MagicMock(return_value=repo_inst)

    # WsiRepository.upsert -> no-op (flat "escrito" na transacao)
    wsi_inst = MagicMock()
    wsi_inst.upsert_job_screening_question = AsyncMock(return_value=None)
    wsi_cls = MagicMock(return_value=wsi_inst)

    # set versionado FALHA
    sqs = MagicMock()
    sqs.save_question_set = AsyncMock(side_effect=RuntimeError("boom version set"))

    db = MagicMock()
    db.rollback = AsyncMock()

    request = SimpleNamespace(
        job_id="job-123",
        questions=[{"id": "q1", "text": "Pergunta?", "category": "general"}],
        source="manual",
    )
    return jvcr_cls, wsi_cls, sqs, db, request


async def test_version_set_failure_does_not_lie_success_true():
    jvcr_cls, wsi_cls, sqs, db, request = _mocks()
    with patch.object(q_mod, "WsiRepository", wsi_cls), patch(_JVCR_PATH, jvcr_cls):
        result = await q_mod.save_questions(
            request=request, db=db, sqs_svc=sqs, company_id="company-1"
        )
    assert result.get("success") is False, (
        "save_questions mascarou falha do set versionado com success:True. "
        f"Retornou: {result}. -> Fix: no except do save_question_set, fazer "
        "await db.rollback() + return success:False (nao swallow + fall-through)."
    )


async def test_version_set_failure_rolls_back_flat():
    jvcr_cls, wsi_cls, sqs, db, request = _mocks()
    with patch.object(q_mod, "WsiRepository", wsi_cls), patch(_JVCR_PATH, jvcr_cls):
        await q_mod.save_questions(
            request=request, db=db, sqs_svc=sqs, company_id="company-1"
        )
    db.rollback.assert_awaited()  # atomicidade: flat uncommitted descartado
