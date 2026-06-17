"""
Unit tests for RubricDispatchService — Sprint IV of LIA-D06 migration.

Tests cobrem:
- Entity extraction success path → params dict
- Entity extraction failures (LLM error, no JSON, JSON parse fail)
- No candidate found → returns {"success": False}
- Tool execution success → returns structured response with C-05 fields
- Tool execution failure → returns {"success": False}
- Multi-tenant: company_id propagado a ToolExecutionContext
- Graceful degradation: any exception → {"success": False}

Reference: ADR-019 — Sprint IV
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.cv_screening.services.rubric_dispatch import (
    DEFAULT_SUGGESTED_PROMPTS,
    ENTITY_EXTRACTION_PROMPT,
    RUBRIC_TOOL_NAME,
    RubricDispatchService,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_llm_service(extraction_response: str | None = None,
                     extraction_exception: Exception | None = None) -> MagicMock:
    """Mock LLM service com generate() configurável."""
    svc = MagicMock()
    if extraction_exception is not None:
        svc.generate = AsyncMock(side_effect=extraction_exception)
    else:
        svc.generate = AsyncMock(return_value=extraction_response or "")
    return svc


# ─────────────────────────────────────────────────────────────────────────────
# Constants tests
# ─────────────────────────────────────────────────────────────────────────────


class TestConstants:
    """Constantes canônicas estáveis."""

    def test_rubric_tool_name(self):
        assert RUBRIC_TOOL_NAME == "analyze_cv_match"

    def test_extraction_prompt_includes_message_placeholder(self):
        assert "{message}" in ENTITY_EXTRACTION_PROMPT
        # Sanity: deve mencionar todas 4 entities canônicas
        for key in ("candidate_id", "candidate_name", "vacancy_id", "vacancy_title"):
            assert key in ENTITY_EXTRACTION_PROMPT

    def test_default_suggestions_count(self):
        """V1 retornava 3 suggestions — manter para compat UX."""
        assert len(DEFAULT_SUGGESTED_PROMPTS) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────


class TestInit:
    """Construção do service."""

    def test_requires_llm_service(self):
        with pytest.raises(TypeError):
            RubricDispatchService()  # type: ignore[call-arg]

    def test_stores_llm_service_reference(self):
        llm = MagicMock()
        svc = RubricDispatchService(llm_service=llm)
        assert svc._llm_service is llm


# ─────────────────────────────────────────────────────────────────────────────
# Entity extraction failures
# ─────────────────────────────────────────────────────────────────────────────


class TestEntityExtractionFailures:
    """Falhas de extraction → {"success": False} sem crash."""

    @pytest.mark.asyncio
    async def test_llm_exception_returns_failure(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(extraction_exception=RuntimeError("LLM down"))
        )
        result = await svc.dispatch("analise o cv", {"company_id": "t1"})
        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_no_json_in_response_returns_failure(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(extraction_response="apenas texto sem JSON")
        )
        result = await svc.dispatch("analise o cv", {"company_id": "t1"})
        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_invalid_json_returns_failure(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(extraction_response='{invalid json}')
        )
        result = await svc.dispatch("analise o cv", {"company_id": "t1"})
        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self):
        """LLM às vezes wraps em ```json — service deve stripar."""
        json_response = '```json\n{"candidate_name": "Maria", "vacancy_title": "Dev"}\n```'
        svc = RubricDispatchService(
            llm_service=_make_llm_service(extraction_response=json_response)
        )
        # Patch tool executor to return success
        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = {"match_score": 75, "matched_skills": ["Python"]}
                mock_exec.execute = AsyncMock(return_value=mock_result)

                result = await svc.dispatch("analise", {"company_id": "t1"})
                assert result["success"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Candidate validation
# ─────────────────────────────────────────────────────────────────────────────


class TestCandidateValidation:
    """Service exige candidate_id ou candidate_name no extraction."""

    @pytest.mark.asyncio
    async def test_no_candidate_returns_failure(self):
        """Apenas vacancy info — service rejeita."""
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"vacancy_title": "Dev Backend"}'
            )
        )
        result = await svc.dispatch("analise vaga", {"company_id": "t1"})
        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_only_null_values_returns_failure(self):
        """Todos params null/empty — após filtragem não há candidate."""
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_id": null, "candidate_name": "", "vacancy_title": null}'
            )
        )
        result = await svc.dispatch("nada", {"company_id": "t1"})
        assert result == {"success": False}


# ─────────────────────────────────────────────────────────────────────────────
# Tool execution success path
# ─────────────────────────────────────────────────────────────────────────────


class TestToolExecutionSuccess:
    """Happy path: extraction OK + candidate present + tool success."""

    @pytest.mark.asyncio
    async def test_success_returns_structured_response(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "Maria Silva", "vacancy_title": "Dev"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = {
                    "match_score": 85,
                    "matched_skills": ["Python", "Django"],
                    "missing_skills": ["Go"],
                    "recommendation": "APROVADO",
                    "message": "Candidato fit alto.",
                }
                mock_exec.execute = AsyncMock(return_value=mock_result)

                result = await svc.dispatch(
                    "Analise CV da Maria",
                    {"company_id": "t1", "user_id": "u1"},
                )

        assert result["success"] is True
        assert result["match_score"] == 85
        assert result["matched_skills"] == ["Python", "Django"]
        assert result["missing_skills"] == ["Go"]
        assert result["recommendation"] == "APROVADO"
        assert result["agent_used"] == "CV Match Tool (BARS Rubric)"
        assert result["agent_type"] == "tool"
        assert result["suggested_prompts"] == DEFAULT_SUGGESTED_PROMPTS
        assert result["message"] == "Candidato fit alto."

    @pytest.mark.asyncio
    async def test_tool_returns_failure_returns_success_false(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "Maria"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = False
                mock_result.error = "candidate not found in DB"
                mock_exec.execute = AsyncMock(return_value=mock_result)

                result = await svc.dispatch(
                    "Analise Maria", {"company_id": "t1"}
                )

        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_tool_returns_empty_result_returns_failure(self):
        """tool.success True mas result None/empty — retorna failure."""
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "Maria"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = None  # vazio
                mock_exec.execute = AsyncMock(return_value=mock_result)

                result = await svc.dispatch(
                    "Analise Maria", {"company_id": "t1"}
                )

        assert result == {"success": False}


# ─────────────────────────────────────────────────────────────────────────────
# Multi-tenant isolation (P0 LGPD)
# ─────────────────────────────────────────────────────────────────────────────


class TestMultiTenantIsolation:
    """P0 LGPD: company_id propagado ao ToolExecutionContext."""

    @pytest.mark.asyncio
    async def test_company_id_propagated_to_tool_context(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "X"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ) as mock_ctx_cls:
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = {"match_score": 50}
                mock_exec.execute = AsyncMock(return_value=mock_result)

                await svc.dispatch(
                    "msg",
                    {
                        "company_id": "tenant-isolation-test",
                        "user_id": "u-xyz",
                        "session_id": "sess-1",
                    },
                )

        # ToolExecutionContext criado com company_id correto
        call_kwargs = mock_ctx_cls.call_args.kwargs
        assert call_kwargs["company_id"] == "tenant-isolation-test"
        assert call_kwargs["user_id"] == "u-xyz"
        assert call_kwargs["session_id"] == "sess-1"

    @pytest.mark.asyncio
    async def test_missing_user_id_uses_system_default(self):
        """V1 default era 'system' quando user_id ausente."""
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "X"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ) as mock_ctx_cls:
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = {"match_score": 50}
                mock_exec.execute = AsyncMock(return_value=mock_result)

                await svc.dispatch("msg", {"company_id": "t1"})  # sem user_id

        call_kwargs = mock_ctx_cls.call_args.kwargs
        assert call_kwargs["user_id"] == "system"


# ─────────────────────────────────────────────────────────────────────────────
# Graceful degradation
# ─────────────────────────────────────────────────────────────────────────────


class TestGracefulDegradation:
    """P1: any exception → returns failure (caller usa LLM fallback)."""

    @pytest.mark.asyncio
    async def test_tool_executor_exception_returns_failure(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "Maria"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_exec.execute = AsyncMock(side_effect=RuntimeError("tool crash"))

                result = await svc.dispatch("msg", {"company_id": "t1"})

        # Exception capturada — caller fallback para LLM
        assert result == {"success": False}

    @pytest.mark.asyncio
    async def test_none_context_does_not_crash(self):
        svc = RubricDispatchService(
            llm_service=_make_llm_service(
                extraction_response='{"candidate_name": "Maria"}'
            )
        )

        with patch(
            "app.tools.executor.ToolExecutionContext"
        ):
            with patch(
                "app.tools.executor.tool_executor"
            ) as mock_exec:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.result = {"match_score": 70}
                mock_exec.execute = AsyncMock(return_value=mock_result)

                result = await svc.dispatch("msg", None)  # context=None
                # Não deve crashar — usa context vazio
                assert result["success"] is True
