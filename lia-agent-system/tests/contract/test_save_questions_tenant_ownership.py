"""Contract test — save_questions valida ownership do job_id (P0 cross-tenant, audit 2026-06-05).

job_screening_questions / screening_question_sets nao tem RLS; o gate canonico e
no produtor (handler save_questions) via company_id do JWT. Sensor fail-closed:
job de outra empresa => 404 e NENHUM write.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.api.v1.wsi.questions import save_questions
from app.api.v1.wsi._shared import SaveQuestionsRequest
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from app.domains.voice.repositories.wsi_repository import WsiRepository


def _req():
    return SaveQuestionsRequest(
        job_id="job-de-outra-empresa",
        questions=[{"text": "Pergunta 1"}],
        source="test",
    )


@pytest.mark.asyncio
async def test_save_questions_rejeita_job_de_outra_empresa():
    db, sqs = AsyncMock(), AsyncMock()
    with patch.object(JobVacancyCrudRepository, "owned_by_company", new=AsyncMock(return_value=False)), \
         patch.object(WsiRepository, "upsert_job_screening_question", new=AsyncMock()) as mock_upsert:
        with pytest.raises(HTTPException) as exc:
            await save_questions(request=_req(), db=db, sqs_svc=sqs, company_id="minha-empresa")
        assert exc.value.status_code == 404
        mock_upsert.assert_not_called()


@pytest.mark.asyncio
async def test_save_questions_aceita_job_da_propria_empresa():
    db, sqs = AsyncMock(), AsyncMock()
    with patch.object(JobVacancyCrudRepository, "owned_by_company", new=AsyncMock(return_value=True)), \
         patch.object(WsiRepository, "upsert_job_screening_question", new=AsyncMock()) as mock_upsert:
        result = await save_questions(request=_req(), db=db, sqs_svc=sqs, company_id="minha-empresa")
        assert result.get("success") is True
        mock_upsert.assert_called()
