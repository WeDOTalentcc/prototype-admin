"""tests/services/test_onboarding_field_extractor.py — P2-2 Sprint A.3.

Cobertura canonical do extractor:
- build_extraction_prompt: estrutura + i18n PT-BR
- validate_extracted_value: 14 validation rules
- extract_field_from_message (mock): API contract estável
"""
from __future__ import annotations

import logging

import pytest

from unittest.mock import AsyncMock, MagicMock

from app.services.onboarding_field_extractor import (
    ExtractionResult,
    build_extraction_prompt,
    extract_field_from_message,
    extract_field_from_message_llm,
    validate_extracted_value,
)
from app.services.onboarding_yaml_loader import OnboardingField


def _f(
    field_key: str,
    question: str = "Pergunta?",
    validation: str | None = None,
    example_response: str | None = None,
    extract_hint: str | None = None,
) -> OnboardingField:
    return OnboardingField(
        field_key=field_key,
        question=question,
        validation=validation,
        example_response=example_response,
        extract_hint=extract_hint,
    )


# --- TestBuildExtractionPrompt ---------------------------------------------


class TestBuildExtractionPrompt:
    def test_prompt_includes_question(self):
        fld = _f("industry", question="Em qual setor vocês atuam?")
        p = build_extraction_prompt(fld, "Somos fintech")
        assert "Em qual setor vocês atuam?" in p

    def test_prompt_pt_br(self):
        fld = _f("industry", question="Setor?")
        p = build_extraction_prompt(fld, "fintech")
        # Sinais inequívocos de PT-BR
        assert "usuário" in p.lower() or "extrair" in p.lower()
        assert "PT-BR" in p or "português" in p.lower() or "pt-br" in p.lower()

    def test_prompt_includes_example_response_when_present(self):
        fld = _f("industry", example_response="Ex: fintech, saúde, varejo")
        p = build_extraction_prompt(fld, "fintech")
        assert "fintech, saúde, varejo" in p

    def test_prompt_includes_additional_fields_when_provided(self):
        target = _f("industry", question="Setor?")
        extra = [
            _f("headquarters_city", question="Cidade?"),
            _f("employee_count", question="Quantos funcionários?", validation="integer"),
        ]
        p = build_extraction_prompt(target, "Fintech SP 50 funcionários", extra)
        assert "headquarters_city" in p
        assert "employee_count" in p
        assert "Cidade?" in p

    def test_prompt_requests_json_structured_output(self):
        fld = _f("industry")
        p = build_extraction_prompt(fld, "fintech")
        assert "extracted_fields" in p
        assert "confidence" in p
        assert "JSON" in p or "json" in p


# --- TestValidation --------------------------------------------------------


class TestValidation:
    def test_required_rejects_empty(self):
        ok, err = validate_extracted_value(_f("k", validation="required"), "")
        assert ok is False
        assert err

    def test_required_accepts_value(self):
        ok, err = validate_extracted_value(_f("k", validation="required"), "fintech")
        assert ok is True
        assert err is None

    def test_cnpj_format_accepts_14_digits(self):
        ok, _ = validate_extracted_value(
            _f("k", validation="cnpj_format"), "12345678000190"
        )
        assert ok is True

    def test_cnpj_format_accepts_masked(self):
        ok, _ = validate_extracted_value(
            _f("k", validation="cnpj_format"), "12.345.678/0001-90"
        )
        assert ok is True

    def test_cnpj_format_rejects_invalid(self):
        ok, err = validate_extracted_value(_f("k", validation="cnpj_format"), "123")
        assert ok is False
        assert err

    def test_url_format_accepts_https(self):
        ok, _ = validate_extracted_value(
            _f("k", validation="url_format"), "https://wedotalent.cc"
        )
        assert ok is True

    def test_url_format_rejects_no_scheme(self):
        ok, err = validate_extracted_value(
            _f("k", validation="url_format"), "wedotalent.cc"
        )
        assert ok is False
        assert err

    def test_integer_accepts_number(self):
        ok, _ = validate_extracted_value(_f("k", validation="integer"), 42)
        assert ok is True

    def test_integer_1_to_10_rejects_11(self):
        ok, err = validate_extracted_value(_f("k", validation="integer_1_to_10"), 11)
        assert ok is False
        assert err

    def test_integer_15_to_180_canonical_durations(self):
        ok, _ = validate_extracted_value(_f("k", validation="integer_15_to_180"), 60)
        assert ok is True
        ok2, _ = validate_extracted_value(_f("k", validation="integer_15_to_180"), 14)
        assert ok2 is False

    def test_integer_0_to_50_accepts_boundaries(self):
        assert validate_extracted_value(_f("k", validation="integer_0_to_50"), 0)[0] is True
        assert validate_extracted_value(_f("k", validation="integer_0_to_50"), 50)[0] is True
        assert validate_extracted_value(_f("k", validation="integer_0_to_50"), 51)[0] is False

    def test_integer_1_to_72_accepts_boundaries(self):
        assert validate_extracted_value(_f("k", validation="integer_1_to_72"), 1)[0] is True
        assert validate_extracted_value(_f("k", validation="integer_1_to_72"), 72)[0] is True
        assert validate_extracted_value(_f("k", validation="integer_1_to_72"), 0)[0] is False

    def test_text_min_20_rejects_short(self):
        ok, err = validate_extracted_value(_f("k", validation="text_min_20"), "curto")
        assert ok is False
        assert err

    def test_text_min_20_accepts_long(self):
        ok, _ = validate_extracted_value(
            _f("k", validation="text_min_20"), "Texto longo o suficiente para passar"
        )
        assert ok is True

    def test_list_min_3_rejects_2_items(self):
        ok, err = validate_extracted_value(_f("k", validation="list_min_3"), ["a", "b"])
        assert ok is False
        assert err

    def test_list_min_3_accepts_3(self):
        ok, _ = validate_extracted_value(
            _f("k", validation="list_min_3"), ["a", "b", "c"]
        )
        assert ok is True

    def test_enum_work_model_normalizes(self):
        for raw in ["presencial", "Híbrido", "hibrido", "remoto", "Remote", "hybrid"]:
            ok, _ = validate_extracted_value(_f("k", validation="enum_work_model"), raw)
            assert ok is True, f"deveria aceitar {raw!r}"

    def test_enum_work_model_rejects_garbage(self):
        ok, err = validate_extracted_value(
            _f("k", validation="enum_work_model"), "qualquer-coisa"
        )
        assert ok is False
        assert err

    def test_enum_low_medium_high_canonical(self):
        for raw in ["baixa", "Média", "alta", "low", "medium", "HIGH"]:
            ok, _ = validate_extracted_value(
                _f("k", validation="enum_low_medium_high"), raw
            )
            assert ok is True, f"deveria aceitar {raw!r}"
        ok, err = validate_extracted_value(
            _f("k", validation="enum_low_medium_high"), "talvez"
        )
        assert ok is False
        assert err

    def test_ai_persona_name_length(self):
        # válido
        assert validate_extracted_value(_f("k", validation="ai_persona_name"), "LIA")[0] is True
        assert validate_extracted_value(_f("k", validation="ai_persona_name"), "Sofía")[0] is True
        # muito curto
        assert validate_extracted_value(_f("k", validation="ai_persona_name"), "A")[0] is False
        # muito longo
        assert (
            validate_extracted_value(
                _f("k", validation="ai_persona_name"), "X" * 21
            )[0]
            is False
        )

    def test_ai_persona_tone_canonical(self):
        for tone in ["formal", "profissional", "amigavel", "casual", "inspirador", "direto"]:
            ok, _ = validate_extracted_value(_f("k", validation="ai_persona_tone"), tone)
            assert ok is True, f"deveria aceitar {tone!r}"
        ok, err = validate_extracted_value(
            _f("k", validation="ai_persona_tone"), "sarcástico"
        )
        assert ok is False
        assert err


# --- TestExtractMock -------------------------------------------------------


class TestExtractMock:
    @pytest.mark.asyncio
    async def test_returns_extraction_result_dataclass(self):
        fld = _f("industry", validation="required")
        res = await extract_field_from_message(fld, "fintech")
        assert isinstance(res, ExtractionResult)

    @pytest.mark.asyncio
    async def test_simple_text_value_extracted(self):
        fld = _f("industry", validation="required")
        res = await extract_field_from_message(fld, "Somos fintech B2B")
        assert res.success is True
        assert "industry" in res.extracted_fields
        assert res.extracted_fields["industry"] == "Somos fintech B2B"

    @pytest.mark.asyncio
    async def test_boolean_inference_from_sim_nao(self):
        fld = _f("manager_approval_for_offer", validation="required")
        res_sim = await extract_field_from_message(fld, "sim")
        assert res_sim.success is True
        assert res_sim.extracted_fields["manager_approval_for_offer"] is True

        res_nao = await extract_field_from_message(fld, "não")
        assert res_nao.success is True
        assert res_nao.extracted_fields["manager_approval_for_offer"] is False

    @pytest.mark.asyncio
    async def test_needs_confirmation_always_true_on_success(self):
        fld = _f("industry", validation="required")
        res = await extract_field_from_message(fld, "fintech")
        assert res.success is True
        assert res.needs_confirmation is True

    @pytest.mark.asyncio
    async def test_low_confidence_logs_warning(self, caplog):
        # Mensagem que NÃO bate com enum nem boolean → confidence baixa
        fld = _f("work_model", validation="enum_work_model")
        with caplog.at_level(logging.WARNING):
            res = await extract_field_from_message(fld, "qualquer outra coisa")
        # ou falhou validation, ou retornou low confidence — em ambos os casos
        # houve log warn
        assert any("low confidence" in r.message or "validation failed" in r.message for r in caplog.records)
        # E não passa validation enum
        assert res.success is False

    @pytest.mark.asyncio
    async def test_integer_extraction_from_natural_message(self):
        fld = _f("employee_count", validation="integer")
        res = await extract_field_from_message(fld, "temos 50 funcionários")
        assert res.success is True
        assert res.extracted_fields["employee_count"] == 50

    @pytest.mark.asyncio
    async def test_empty_message_returns_failure(self):
        fld = _f("industry", validation="required")
        res = await extract_field_from_message(fld, "   ")
        assert res.success is False
        assert res.error



# --- Sprint A.6: LLM path tests --------------------------------------------


def _mock_llm_with_tool_call(arguments_dict: dict | str, *, use_parameters: bool = True):
    """Cria mock LLMService que retorna ToolCallResponse-like com tool_calls."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.is_tool_call = True
    mock_response.text_response = None

    mock_tool_call = MagicMock(spec=[])
    if use_parameters:
        # ToolCallRequest canonical: parameters: dict
        mock_tool_call.parameters = arguments_dict
        mock_tool_call.arguments = None
    else:
        # OpenAI-style: arguments is JSON string
        mock_tool_call.parameters = None
        mock_tool_call.arguments = arguments_dict

    mock_response.tool_calls = [mock_tool_call]
    mock_llm.generate_with_tools = AsyncMock(return_value=mock_response)
    return mock_llm


class TestExtractWithLLM:
    """Sprint A.6 — extract_field_from_message_llm com LLMService mockado."""

    @pytest.mark.asyncio
    async def test_llm_tool_call_success_with_parameters_dict(self):
        fld = _f("industry", validation="required")
        mock_llm = _mock_llm_with_tool_call(
            {"extracted_fields": {"industry": "fintech"}, "confidence": 0.9},
            use_parameters=True,
        )

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="Somos fintech",
            llm_service=mock_llm,
        )

        assert res.success is True
        assert res.extracted_fields == {"industry": "fintech"}
        assert res.confidence == 0.9
        assert res.needs_confirmation is True
        mock_llm.generate_with_tools.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_llm_tool_call_success_with_json_string_arguments(self):
        fld = _f("industry", validation="required")
        mock_llm = _mock_llm_with_tool_call(
            '{"extracted_fields": {"industry": "saas"}, "confidence": 0.8}',
            use_parameters=False,
        )

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="SaaS",
            llm_service=mock_llm,
        )

        assert res.success is True
        assert res.extracted_fields == {"industry": "saas"}
        assert res.confidence == 0.8

    @pytest.mark.asyncio
    async def test_llm_call_exception_returns_error(self):
        fld = _f("industry", validation="required")
        mock_llm = MagicMock()
        mock_llm.generate_with_tools = AsyncMock(side_effect=RuntimeError("upstream down"))

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="fintech",
            llm_service=mock_llm,
        )

        assert res.success is False
        assert res.error is not None
        assert "RuntimeError" in res.error
        assert res.extracted_fields == {}

    @pytest.mark.asyncio
    async def test_invalid_json_in_tool_args_returns_error(self):
        fld = _f("industry", validation="required")
        mock_llm = _mock_llm_with_tool_call(
            "{not valid json at all",
            use_parameters=False,
        )

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="fintech",
            llm_service=mock_llm,
        )

        assert res.success is False
        assert res.error is not None
        assert "Parse failed" in res.error

    @pytest.mark.asyncio
    async def test_validation_filters_extracted_fields(self):
        # LLM "extrai" valor inválido pra enum_work_model → ignorado, success=False
        fld = _f("work_model", validation="enum_work_model")
        mock_llm = _mock_llm_with_tool_call(
            {"extracted_fields": {"work_model": "valor_invalido_xyz"}, "confidence": 0.7},
            use_parameters=True,
        )

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="qualquer coisa",
            llm_service=mock_llm,
        )

        assert res.success is False
        assert res.extracted_fields == {}
        assert res.error == "Nenhum campo válido extraído"

    @pytest.mark.asyncio
    async def test_hallucinated_field_ignored(self, caplog):
        # LLM retorna field que NÃO está no target nem additional_context → ignorado
        fld = _f("industry", validation="required")
        mock_llm = _mock_llm_with_tool_call(
            {
                "extracted_fields": {
                    "industry": "fintech",
                    "totally_made_up_field": "garbage",
                },
                "confidence": 0.85,
            },
            use_parameters=True,
        )

        with caplog.at_level(logging.WARNING):
            res = await extract_field_from_message_llm(
                target_field=fld,
                user_message="fintech",
                llm_service=mock_llm,
            )

        assert res.success is True
        assert res.extracted_fields == {"industry": "fintech"}
        assert "totally_made_up_field" not in res.extracted_fields
        assert any("hallucination" in r.message or "unknown field" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_no_tool_call_falls_back_to_text_parse(self):
        fld = _f("industry", validation="required")
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.is_tool_call = False
        mock_response.tool_calls = []
        mock_response.text_response = "fintech B2B"
        mock_llm.generate_with_tools = AsyncMock(return_value=mock_response)

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="fintech B2B",
            llm_service=mock_llm,
        )

        assert res.success is True
        # Text fallback: usa text como valor literal do field
        assert res.extracted_fields == {"industry": "fintech B2B"}
        assert res.confidence == 0.3  # low confidence (text fallback)

    @pytest.mark.asyncio
    async def test_empty_message_short_circuits_without_calling_llm(self):
        fld = _f("industry", validation="required")
        mock_llm = MagicMock()
        mock_llm.generate_with_tools = AsyncMock()

        res = await extract_field_from_message_llm(
            target_field=fld,
            user_message="   ",
            llm_service=mock_llm,
        )

        assert res.success is False
        assert res.error == "Mensagem vazia"
        mock_llm.generate_with_tools.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_use_llm_param_opts_in_delegates_to_llm_path(self):
        fld = _f("industry", validation="required")
        mock_llm = _mock_llm_with_tool_call(
            {"extracted_fields": {"industry": "edtech"}, "confidence": 0.95},
            use_parameters=True,
        )

        res = await extract_field_from_message(
            fld,
            "edtech",
            use_llm=True,
            llm_service=mock_llm,
        )

        assert res.success is True
        assert res.extracted_fields == {"industry": "edtech"}
        mock_llm.generate_with_tools.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_use_llm_default_false_uses_mock_heuristic(self):
        # Sem use_llm, mantém heurística mock canonical (não chama LLMService)
        fld = _f("manager_approval_for_offer", validation="required")
        # Se chamasse LLM com llm_service=None, importaria LLMService real (caro);
        # default mock heurístico evita isso. Cobre boolean inference.
        res = await extract_field_from_message(fld, "sim")
        assert res.success is True
        assert res.extracted_fields["manager_approval_for_offer"] is True
