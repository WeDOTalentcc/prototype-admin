"""P0.D follow-up contract tests (audit 2026-05-21) — silent fallback eliminado
nos 3 sites Category A do triage WT-2022:

1. wsi_question_adjuster.evaluate_job_description (LLM Gemini call)
2. job_management.stage_description.handle_description (LLM gemini + parse)
3. recruiter_assistant.talent_tool_registry._wrap_recommend_actions (DB query)

Pin canonical:
  - Sucesso: ``fallback_used=False`` (path normal)
  - Falha: ``fallback_used=True`` + surface explicito (failure_mode, error_message,
    needs_manual_review) — nunca silent envelope com aparencia de success.
  - Back-compat: callers que NAO checam ``fallback_used`` continuam funcionando.

Pattern canonical: app.shared.llm.safe_response.safe_llm_with_flag_async +
explicit envelope em except handler retornando immediate (nao return-after-try).
Replica filosofia REGRA 4 CLAUDE.md.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Site 1 — wsi_question_adjuster.evaluate_job_description
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_jd_success_no_fallback():
    """Sucesso: Gemini retorna texto, fallback_used=False, lia_suggestion vem do LLM."""
    from app.domains.cv_screening.services.wsi_question_adjuster import (
        WSIQuestionAdjusterService,
    )

    service = WSIQuestionAdjusterService()

    mock_response = MagicMock()
    mock_response.text = "Excelente JD! Bem estruturado para gerar perguntas WSI de qualidade."

    with patch(
        "app.domains.cv_screening.services.wsi_question_adjuster.llm_service"
    ) as mock_llm:
        mock_llm.generate_native_gemini_sync.return_value = mock_response

        result = await service.evaluate_job_description(
            job_title="Tech Lead",
            responsibilities=["arquitetura", "mentoria", "code review"],
            technical_skills=["Python", "FastAPI", "PostgreSQL"],
            behavioral_competencies=["lideranca", "comunicacao", "ownership"],
            seniority="senior",
        )

    assert result["success"] is True
    assert result["fallback_used"] is False
    assert result["llm_failure_mode"] is None
    assert result["llm_error_message"] is None
    assert "Excelente JD" in result["lia_suggestion"]


@pytest.mark.asyncio
async def test_evaluate_jd_llm_exception_explicit_fallback():
    """LLM failure: fallback_used=True, llm_failure_mode populado, template stock."""
    from app.domains.cv_screening.services.wsi_question_adjuster import (
        WSIQuestionAdjusterService,
    )

    service = WSIQuestionAdjusterService()

    with patch(
        "app.domains.cv_screening.services.wsi_question_adjuster.llm_service"
    ) as mock_llm:
        mock_llm.generate_native_gemini_sync.side_effect = ConnectionError(
            "Gemini API unreachable"
        )

        result = await service.evaluate_job_description(
            job_title="Tech Lead",
            responsibilities=["arquitetura"],
            technical_skills=["Python"],
            behavioral_competencies=["lideranca"],
            seniority=None,
        )

    # Envelope canonical: fallback_used=True surface explicito
    assert result["success"] is True  # outer envelope ainda eh success (HTTP 200)
    assert result["fallback_used"] is True
    assert result["llm_failure_mode"] is not None
    assert "unreachable" in result["llm_error_message"].lower() or "gemini" in result["llm_error_message"].lower()
    # Template fallback inclui sugestoes baseadas nos counts
    assert "responsabilidade" in result["lia_suggestion"].lower() or "senioridade" in result["lia_suggestion"].lower()
    # Score quantitativo nao mudou (eh independente do LLM)
    assert "score" in result
    assert "indicators" in result


@pytest.mark.asyncio
async def test_evaluate_jd_backward_compat_caller_ignores_flag():
    """Back-compat: caller que ignora fallback_used recebe lia_suggestion mesmo em failure."""
    from app.domains.cv_screening.services.wsi_question_adjuster import (
        WSIQuestionAdjusterService,
    )

    service = WSIQuestionAdjusterService()

    with patch(
        "app.domains.cv_screening.services.wsi_question_adjuster.llm_service"
    ) as mock_llm:
        mock_llm.generate_native_gemini_sync.side_effect = RuntimeError("boom")

        result = await service.evaluate_job_description(
            job_title="Dev",
            responsibilities=[],
            technical_skills=[],
            behavioral_competencies=[],
        )

    # Caller pré-P0.D só usa esses keys — devem continuar válidos
    assert "lia_suggestion" in result and isinstance(result["lia_suggestion"], str)
    assert len(result["lia_suggestion"]) > 0
    assert "score" in result
    assert "can_generate" in result


# ---------------------------------------------------------------------------
# Site 2 — stage_description.handle_description
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_description_parse_failure_surfaces_fallback_flag():
    """Parse failure: suggestions_data carries description_parse_fallback_used=True."""
    from app.domains.job_management.services.wizard_step_service.stage_description import (
        handle_description,
    )

    request = MagicMock()
    request.user_input = "Vaga Dev Python"

    # Patch LLMService.generate pra retornar resposta nao-JSON, forcando parse exception
    # downstream. Mas o try block parses with re.search → cai no else branch
    # ("Entendi a descrição"). Pra forcar exception path real, patchamos
    # skills_catalog_service pra levantar exception dentro do try.
    fake_llm = AsyncMock()
    fake_llm.generate = AsyncMock(
        return_value='{"job_title": "Dev Python", "detected_skills": ["Python"]}'
    )

    suggestions_data: dict = {}

    with patch(
        "app.domains.job_management.services.wizard_step_service.stage_description.LLMService",
        return_value=fake_llm,
    ), patch(
        "app.domains.job_management.services.wizard_step_service.stage_description.skills_catalog_service"
    ) as mock_skills:
        mock_skills.evaluate_skills_quality.side_effect = RuntimeError("Catalog DB down")

        lia_message, detected_criteria, returned_suggestions = await handle_description(
            request=request,
            job_draft={},
            company_context="",
            company_departments=[],
            field_origins={},
            confidence_service=MagicMock(),
            suggestions_data=suggestions_data,
        )

    # Verifica canonical envelope flag
    assert returned_suggestions.get("description_parse_fallback_used") is True
    assert "description_parse_error" in returned_suggestions
    assert "description_parse_error_type" in returned_suggestions
    # lia_message ainda eh entregue (template fallback) pra back-compat
    assert isinstance(lia_message, str) and len(lia_message) > 0
    assert detected_criteria == {}


@pytest.mark.asyncio
async def test_handle_description_no_json_match_marks_fallback_false():
    """LLM resposta sem JSON valido cai no `else` branch (sucesso parcial),
    e o success-path setdefault marca description_parse_fallback_used=False.
    Distinto de exception path (que marcaria True)."""
    from app.domains.job_management.services.wizard_step_service.stage_description import (
        handle_description,
    )

    request = MagicMock()
    request.user_input = "Vaga Dev Python"

    fake_llm = AsyncMock()
    # Resposta sem JSON valido — re.search retorna None → else branch (NAO exception)
    fake_llm.generate = AsyncMock(return_value="Sem JSON aqui apenas texto livre.")

    suggestions_data: dict = {}

    with patch(
        "app.domains.job_management.services.wizard_step_service.stage_description.LLMService",
        return_value=fake_llm,
    ):
        lia_message, detected_criteria, returned_suggestions = await handle_description(
            request=request,
            job_draft={},
            company_context="",
            company_departments=[],
            field_origins={},
            confidence_service=MagicMock(),
            suggestions_data=suggestions_data,
        )

    # Sucesso (sem exception): fallback flag setado False (canonical mark explicit)
    assert returned_suggestions.get("description_parse_fallback_used") is False
    # Mensagem else-branch entregue
    assert "Entendi a descrição" in lia_message or "ajustar" in lia_message
    assert detected_criteria == {}


# ---------------------------------------------------------------------------
# Site 3 — talent_tool_registry._wrap_recommend_actions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommend_actions_db_failure_explicit_envelope():
    """DB failure: fallback_used=True + needs_manual_review=True + reason."""
    from app.domains.recruiter_assistant.agents import talent_tool_registry

    # Patch AsyncSessionLocal pra levantar exception ao __aenter__
    fake_session_ctx = MagicMock()
    fake_session_ctx.__aenter__ = AsyncMock(side_effect=RuntimeError("DB pool exhausted"))
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)

    candidate_uuids = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]

    # Pre-set runtime context. Tests escapam o sensor R-008 (que so checa
    # source code), padrao usado em tests/test_agents/ + tests/unit/.
    from app.middleware.auth_enforcement import _current_company_id

    token = _current_company_id.set("00000000-0000-0000-0000-000000000001")
    try:
        with patch.object(
            talent_tool_registry, "AsyncSessionLocal", return_value=fake_session_ctx
        ):
            result = await talent_tool_registry._wrap_recommend_actions(
                candidate_ids=candidate_uuids,
                company_id="00000000-0000-0000-0000-000000000001",
            )
    finally:
        _current_company_id.reset(token)

    assert result["success"] is True
    assert result["fallback_used"] is True
    assert result["needs_manual_review"] is True
    assert result["fallback_reason"] is not None
    assert "RuntimeError" in result["fallback_reason"]
    assert "DB pool exhausted" in result["fallback_reason"]
    # Stock recommendations entregues pro recrutador ver review_profile
    assert len(result["data"]["recommendations"]) == 2
    for rec in result["data"]["recommendations"]:
        assert rec["actions"][0]["action"] == "review_profile"


@pytest.mark.asyncio
async def test_recommend_actions_empty_candidates_path_marks_no_fallback():
    """Path normal sem candidatos: fallback_used=False explicit."""
    from app.domains.recruiter_assistant.agents import talent_tool_registry
    from app.middleware.auth_enforcement import _current_company_id

    token = _current_company_id.set("00000000-0000-0000-0000-000000000001")  # noqa: harness-test-only
    try:
        result = await talent_tool_registry._wrap_recommend_actions(
            candidate_ids=[],
            company_id="00000000-0000-0000-0000-000000000001",
        )
    finally:
        _current_company_id.reset(token)

    assert result["success"] is True
    assert result["fallback_used"] is False
    assert result["needs_manual_review"] is False
    assert result["fallback_reason"] is None
    assert result["data"]["recommendations"] == []
