"""
Tests for Sprint 2 — FairnessGuard coverage in agent outputs.

Verifies that avaliador_wsi_agent and candidate_report_service
apply FairnessGuard to text outputs (not just API endpoints).

Session A: coverage extended to rubric_evaluation_service and
triagem_curricular_agent (gap B3 from Feb/2026 audit).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.shared.compliance.fairness_guard import FairnessGuard


BIASED_PARECER = (
    "Candidato de universidade de primeira linha. "
    "Perfil jovem, adequado para time dinâmico. "
    "Apresentação impecável para o cargo."
)

CLEAN_PARECER = (
    "Candidato demonstra domínio técnico em Python e experiência "
    "relevante em sistemas distribuídos. Comunicação objetiva."
)


class TestFairnessGuardImplicitBias:
    """
    Testa que check_implicit_bias captura termos de viés implícito
    que não chegam a bloquear mas devem gerar warnings.
    """

    def setup_method(self):
        self.guard = FairnessGuard()

    def test_clean_text_has_no_warnings(self):
        # check_implicit_bias returns List[str]
        warnings = self.guard.check_implicit_bias(CLEAN_PARECER)
        assert len(warnings) == 0

    def test_blocking_check_does_not_fire_on_clean_text(self):
        result = self.guard.check(CLEAN_PARECER)
        assert not result.is_blocked

    def test_check_returns_fairness_check_result(self):
        from app.shared.compliance.fairness_guard import FairnessCheckResult
        result = self.guard.check(CLEAN_PARECER)
        assert isinstance(result, FairnessCheckResult)
        assert hasattr(result, "is_blocked")
        assert hasattr(result, "blocked_terms")

    def test_explicit_gender_discrimination_blocked(self):
        text = "Apenas homens para esta posição de liderança"
        result = self.guard.check(text)
        assert result.is_blocked
        assert result.category == "genero"

    def test_explicit_age_discrimination_blocked(self):
        text = "idade máxima 35 anos para esta vaga"
        result = self.guard.check(text)
        assert result.is_blocked
        assert result.category == "idade"


class TestFormacaoNoteImplicitBias:
    """
    FormacaoPreQualifierResult was removed (Block 3 elimination).
    These tests verify that the FairnessGuard still detects bias in free-text notes.
    """

    def setup_method(self):
        self.guard = FairnessGuard()

    def test_neutral_note_passes_fairness(self):
        result = self.guard.check("Candidato possui OAB ativa — requisito atendido.")
        assert not result.is_blocked

    def test_biased_note_triggers_warning(self):
        biased_note = "apenas candidatos jovens atendem ao perfil de formação esperado"
        result = self.guard.check(biased_note)
        assert result.is_blocked


# ---------------------------------------------------------------------------
# Session A — Gap B3: FairnessGuard em callers diretos do serviço
# ---------------------------------------------------------------------------

HARD_BLOCK_TEXT = "Apenas homens para esta posição de liderança"
REPLACED_REASONING = (
    "[Avaliação sob revisão — conteúdo sinalizado pelo FairnessGuard "
    "para análise de possível viés discriminatório.]"
)
REPLACED_CONV = "[Resposta sob revisão — conteúdo sinalizado pelo FairnessGuard.]"


class TestRubricEvaluationServiceFairness:
    """
    Testa que evaluate_candidate() aplica FairnessGuard ao reasoning gerado
    pelo LLM antes de retornar o resultado — cobrindo callers diretos que
    não passam pelo endpoint /rubric_evaluation.
    """

    @pytest.mark.asyncio
    async def test_hard_block_replaces_reasoning(self):
        """Hard-block: reasoning com texto discriminatório é substituído."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        candidate_data = {"id": "test-001", "name": "Candidato Teste"}
        requirements = [
            JobRequirementCreate(
                requirement="Python",
                priority=RequirementPriorityEnum.ESSENTIAL,
                description="Habilidade em Python",
                weight=1.0,
            )
        ]

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock) as mock_fmt, \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock) as mock_llm, \
             patch.object(service, "_parse_llm_response") as mock_parse:
            mock_fmt.return_value = ""
            mock_llm.return_value = "{}"
            mock_parse.return_value = (
                [],   # evaluations
                [],   # strengths
                [],   # concerns
                HARD_BLOCK_TEXT,  # reasoning com viés explícito
            )

            result = await service.evaluate_candidate(
                candidate_data, requirements, use_cache=False
            )

        assert result.reasoning == REPLACED_REASONING
        # Hard block não acumula warnings — substitui o texto inteiro
        assert result.fairness_warnings == []

    @pytest.mark.asyncio
    async def test_clean_reasoning_passes_through(self):
        """Reasoning sem viés não é alterado e fairness_warnings fica vazio."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        candidate_data = {"id": "test-002", "name": "Candidato Limpo"}
        requirements = [
            JobRequirementCreate(
                requirement="Python",
                priority=RequirementPriorityEnum.ESSENTIAL,
                description="Habilidade em Python",
                weight=1.0,
            )
        ]
        clean_reasoning = (
            "Candidato demonstra sólida experiência em Python e sistemas distribuídos."
        )

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock) as mock_fmt, \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock) as mock_llm, \
             patch.object(service, "_parse_llm_response") as mock_parse:
            mock_fmt.return_value = ""
            mock_llm.return_value = "{}"
            mock_parse.return_value = ([], [], [], clean_reasoning)

            result = await service.evaluate_candidate(
                candidate_data, requirements, use_cache=False
            )

        assert result.reasoning == clean_reasoning
        assert result.fairness_warnings == []


class TestTriagemCurricularAgentFairness:
    """
    DEPRECATED (Sprint 5): TriagemCurricularAgent removido.
    FairnessGuard em triagem agora protegido via rubric_evaluation_service
    (testado em test_domains/test_cv_screening_agents.py e test_fairness_guard.py).
    Testes mantidos como skip para preservar histórico de cobertura.
    """

    @pytest.mark.skip(reason="TriagemCurricularAgent removido Sprint 5 — coberto por test_fairness_guard.py")
    @pytest.mark.asyncio
    async def test_conversational_hard_block(self):
        """Hard-block: resposta com texto discriminatório é substituída."""
        from app.domains.cv_screening.agents.triagem_curricular_agent import (
            TriagemCurricularAgent,
        )

        agent = TriagemCurricularAgent()

        biased_response = MagicMock()
        biased_response.content = HARD_BLOCK_TEXT

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=biased_response)

        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        mock_llm = MagicMock()
        mock_llm.claude = MagicMock()

        context = {
            "llm_service": mock_llm,
            "current_job": "Engenheiro de Software",
            "current_candidate": "João Silva",
        }
        entities = {"message": "Quais candidatos se encaixam melhor?"}

        with patch(
            "app.domains.cv_screening.agents.triagem_curricular_agent.ChatPromptTemplate.from_messages",
            return_value=mock_prompt,
        ):
            response = await agent._handle_general_query(
                intent="query",
                entities=entities,
                context=context,
            )

        assert response.message == REPLACED_CONV

    @pytest.mark.skip(reason="TriagemCurricularAgent removido Sprint 5 — coberto por test_fairness_guard.py")
    @pytest.mark.asyncio
    async def test_clean_response_passes_through(self):
        """Resposta limpa não é alterada."""
        from app.domains.cv_screening.agents.triagem_curricular_agent import (
            TriagemCurricularAgent,
        )

        agent = TriagemCurricularAgent()
        clean_content = (
            "Com base nos requisitos da vaga, os candidatos com maior aderência são "
            "aqueles com experiência comprovada em Python e sistemas distribuídos."
        )

        clean_response = MagicMock()
        clean_response.content = clean_content

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=clean_response)

        mock_prompt = MagicMock()
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        mock_llm = MagicMock()
        mock_llm.claude = MagicMock()

        context = {
            "llm_service": mock_llm,
            "current_job": "Engenheiro de Software",
        }
        entities = {"message": "Quem são os candidatos?"}

        with patch(
            "app.domains.cv_screening.agents.triagem_curricular_agent.ChatPromptTemplate.from_messages",
            return_value=mock_prompt,
        ):
            response = await agent._handle_general_query(
                intent="query",
                entities=entities,
                context=context,
            )

        assert response.message == clean_content


# ---------------------------------------------------------------------------
# Camada 5 — Contrato de Schema
# ---------------------------------------------------------------------------

class TestRubricEvaluationResultContract:
    """
    Camada 5 (Contrato): garante que RubricEvaluationResult expõe
    fairness_warnings como campo público com default correto.
    Este teste é um gate de regressão — se o campo for removido ou
    renomeado, o teste falha antes de chegar a produção.
    """

    def test_fairness_warnings_field_exists_in_schema(self):
        """Campo fairness_warnings deve existir no schema."""
        from app.schemas.rubric import RubricEvaluationResult
        fields = RubricEvaluationResult.model_fields
        assert "fairness_warnings" in fields, (
            "Campo 'fairness_warnings' removido de RubricEvaluationResult — "
            "quebra contrato com callers do serviço."
        )

    def test_fairness_warnings_defaults_to_empty_list(self):
        """Default deve ser lista vazia (backwards-compatible)."""
        from app.schemas.rubric import RubricEvaluationResult
        result = RubricEvaluationResult(
            score=75.0,
            raw_score=75.0,
            total_weighted_points=75.0,
            max_possible_points=100.0,
            evaluations=[],
            reasoning="Avaliação técnica satisfatória.",
            recommendation="Recomendado",
        )
        assert result.fairness_warnings == []

    def test_fairness_warnings_accepts_list_of_strings(self):
        """Campo deve aceitar lista de strings sem erro de validação."""
        from app.schemas.rubric import RubricEvaluationResult
        warnings = ["Termo 'jovem e dinâmico' detectado — possível viés de idade."]
        result = RubricEvaluationResult(
            score=50.0,
            raw_score=50.0,
            total_weighted_points=50.0,
            max_possible_points=100.0,
            evaluations=[],
            reasoning="Texto limpo.",
            recommendation="Em análise",
            fairness_warnings=warnings,
        )
        assert result.fairness_warnings == warnings


# ---------------------------------------------------------------------------
# Camada 3 — Integração: evaluate_candidate_cv (Session B)
# ---------------------------------------------------------------------------

class TestEvaluateCandidateCvFairness:
    """
    Camada 3 (Integração): verifica que evaluate_candidate_cv() delega
    para evaluate_candidate() e aplica FairnessGuard ao resultado.
    """

    @pytest.mark.asyncio
    async def test_evaluate_candidate_cv_applies_fairness_guard(self):
        """Hard-block: cv_content com raciocínio discriminatório é substituído."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        requirements = [
            JobRequirementCreate(
                requirement="Python",
                priority=RequirementPriorityEnum.ESSENTIAL,
                description="Habilidade em Python",
                weight=1.0,
            )
        ]

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock) as mock_fmt, \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock) as mock_llm, \
             patch.object(service, "_parse_llm_response") as mock_parse:
            mock_fmt.return_value = ""
            mock_llm.return_value = "{}"
            mock_parse.return_value = ([], [], [], HARD_BLOCK_TEXT)

            result = await service.evaluate_candidate_cv(
                cv_content="Candidato com experiência em Python.",
                requirements=requirements,
                job_id="job-001",
            )

        assert result.reasoning == REPLACED_REASONING
        assert isinstance(result.fairness_warnings, list)

    @pytest.mark.asyncio
    async def test_evaluate_candidate_cv_passes_cv_content_to_evaluate(self):
        """cv_content é incluído no candidate_data passado a evaluate_candidate."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        requirements = [
            JobRequirementCreate(
                requirement="Python",
                priority=RequirementPriorityEnum.ESSENTIAL,
                description="Habilidade em Python",
                weight=1.0,
            )
        ]
        captured = {}

        original_evaluate = service.evaluate_candidate

        async def capturing_evaluate(candidate_data, reqs, **kwargs):
            captured["candidate_data"] = candidate_data
            return await original_evaluate(candidate_data, reqs, **kwargs)

        with patch.object(service, "evaluate_candidate", side_effect=capturing_evaluate), \
             patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response", return_value=([], [], [], "OK")):
            await service.evaluate_candidate_cv(
                cv_content="Candidato sênior.",
                requirements=requirements,
                job_id="job-002",
            )

        assert captured["candidate_data"]["cv_content"] == "Candidato sênior."
        assert captured["candidate_data"]["job_id"] == "job-002"


# ---------------------------------------------------------------------------
# Session C — C.2: Token Usage Log
# ---------------------------------------------------------------------------

class TestTokenUsageLog:
    """
    C.2 — Crença #9: evaluate_candidate() emite log estruturado de consumo de tokens
    quando company_id está disponível em candidate_data.
    """

    @pytest.mark.asyncio
    async def test_token_log_emitted_when_company_id_present(self, caplog):
        """Log de token_usage é emitido quando company_id está em candidate_data."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        import logging

        service = RubricEvaluationService()

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response", return_value=([], [], [], "Avaliação técnica satisfatória.")):

            with caplog.at_level(logging.INFO, logger="app.domains.cv_screening.services.rubric_evaluation_service"):
                await service.evaluate_candidate(
                    {
                        "id": "cand-001",
                        "company_id": "cia-abc",
                    },
                    [JobRequirementCreate(
                        requirement="Python",
                        priority=RequirementPriorityEnum.ESSENTIAL,
                        description="Python",
                        weight=1.0,
                    )],
                    use_cache=False,
                )

        token_logs = [r for r in caplog.records if "token_usage" in r.message]
        assert len(token_logs) == 1, "Deve emitir exatamente 1 log de token_usage"
        assert "company_id=cia-abc" in token_logs[0].message
        assert "latency_ms=" in token_logs[0].message

    @pytest.mark.asyncio
    async def test_no_token_log_without_company_id(self, caplog):
        """Sem company_id, nenhum log de token_usage é emitido."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        import logging

        service = RubricEvaluationService()

        with patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response", return_value=([], [], [], "Avaliação técnica satisfatória.")):

            with caplog.at_level(logging.INFO, logger="app.domains.cv_screening.services.rubric_evaluation_service"):
                await service.evaluate_candidate(
                    {"id": "cand-002"},  # sem company_id
                    [JobRequirementCreate(
                        requirement="Python",
                        priority=RequirementPriorityEnum.ESSENTIAL,
                        description="Python",
                        weight=1.0,
                    )],
                    use_cache=False,
                )

        token_logs = [r for r in caplog.records if "token_usage" in r.message]
        assert len(token_logs) == 0, "Sem company_id não deve emitir log de token_usage"


# ---------------------------------------------------------------------------
# Session C — C.3: FairnessGuard Camada 3 (LLM Semântico)
# ---------------------------------------------------------------------------

class TestFairnessGuardCamada3:
    """
    C.3 — FairnessGuard Camada 3: check_semantic() é chamado quando
    FAIRNESS_LAYER3_ENABLED=1, Camadas 1+2 passaram, e texto > 200 chars.
    """

    @pytest.mark.asyncio
    async def test_camada3_called_when_enabled_and_text_long(self):
        """Quando FAIRNESS_LAYER3_ENABLED=1 e texto > 200 chars, check_semantic() é chamado."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        long_clean_reasoning = (
            "Candidato demonstra sólida experiência em Python e sistemas distribuídos. "
            "Habilidades de comunicação objetiva verificadas em projetos anteriores. "
            "Currículo apresenta progressão consistente e alinhamento com requisitos da vaga. "
            "Recomendação: aprovado para segunda fase técnica com score 8.2."
        )
        assert len(long_clean_reasoning) > 200

        with patch.dict("os.environ", {"FAIRNESS_LAYER3_ENABLED": "1"}), \
             patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response",
                          return_value=([], [], [], long_clean_reasoning)), \
             patch("app.domains.cv_screening.services.rubric_evaluation_service._fairness_guard") as mock_guard:

            mock_guard.check.return_value = MagicMock(is_blocked=False)
            mock_guard.check_implicit_bias.return_value = []
            mock_guard.check_semantic = AsyncMock(return_value=MagicMock(soft_warnings=[]))

            await service.evaluate_candidate(
                {"id": "cand-c3-001"},
                [JobRequirementCreate(
                    requirement="Python",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        mock_guard.check_semantic.assert_called_once()

    @pytest.mark.asyncio
    async def test_camada3_not_called_when_disabled(self):
        """Quando FAIRNESS_LAYER3_ENABLED não está definido, check_semantic() não é chamado."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        long_reasoning = "A " * 110  # > 200 chars

        with patch.dict("os.environ", {}, clear=False), \
             patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response",
                          return_value=([], [], [], long_reasoning)), \
             patch("app.domains.cv_screening.services.rubric_evaluation_service._fairness_guard") as mock_guard:

            mock_guard.check.return_value = MagicMock(is_blocked=False)
            mock_guard.check_implicit_bias.return_value = []
            mock_guard.check_semantic = AsyncMock(return_value=MagicMock(soft_warnings=[]))

            import os
            os.environ.pop("FAIRNESS_LAYER3_ENABLED", None)

            await service.evaluate_candidate(
                {"id": "cand-c3-002"},
                [JobRequirementCreate(
                    requirement="Python",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        mock_guard.check_semantic.assert_not_called()

    @pytest.mark.asyncio
    async def test_camada3_not_called_for_short_text(self):
        """Para texto curto (<= 200 chars), check_semantic() não é chamado mesmo com flag ativo."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        short_reasoning = "Candidato aprovado."
        assert len(short_reasoning) <= 200

        with patch.dict("os.environ", {"FAIRNESS_LAYER3_ENABLED": "1"}), \
             patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response",
                          return_value=([], [], [], short_reasoning)), \
             patch("app.domains.cv_screening.services.rubric_evaluation_service._fairness_guard") as mock_guard:

            mock_guard.check.return_value = MagicMock(is_blocked=False)
            mock_guard.check_implicit_bias.return_value = []
            mock_guard.check_semantic = AsyncMock(return_value=MagicMock(soft_warnings=[]))

            await service.evaluate_candidate(
                {"id": "cand-c3-003"},
                [JobRequirementCreate(
                    requirement="Python",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        mock_guard.check_semantic.assert_not_called()

    @pytest.mark.asyncio
    async def test_camada3_warnings_accumulated_in_fairness_warnings(self):
        """Quando Camada 3 detecta viés semântico, avisos são acumulados em fairness_warnings."""
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum

        service = RubricEvaluationService()
        long_reasoning = (
            "Candidato apresenta perfil diferenciado com formação acadêmica sólida. "
            "Experiência em empresas de médio porte com cultura colaborativa. "
            "Demonstra maturidade e capacidade de liderança verificadas em projetos anteriores. "
            "Recomendação: candidato alinhado com os valores e necessidades da vaga."
        )
        assert len(long_reasoning) > 200

        semantic_warning = "Aviso Camada 3: possível viés implícito detectado pelo LLM."

        with patch.dict("os.environ", {"FAIRNESS_LAYER3_ENABLED": "1"}), \
             patch.object(service, "_format_criteria_examples", new_callable=AsyncMock, return_value=""), \
             patch.object(service, "_call_llm_with_retry", new_callable=AsyncMock, return_value="{}"), \
             patch.object(service, "_parse_llm_response",
                          return_value=([], [], [], long_reasoning)), \
             patch("app.domains.cv_screening.services.rubric_evaluation_service._fairness_guard") as mock_guard:

            mock_guard.check.return_value = MagicMock(is_blocked=False)
            mock_guard.check_implicit_bias.return_value = []
            mock_guard.check_semantic = AsyncMock(
                return_value=MagicMock(soft_warnings=[semantic_warning])
            )

            result = await service.evaluate_candidate(
                {"id": "cand-c3-004"},
                [JobRequirementCreate(
                    requirement="Python",
                    priority=RequirementPriorityEnum.ESSENTIAL,
                    description="Python",
                    weight=1.0,
                )],
                use_cache=False,
            )

        assert semantic_warning in result.fairness_warnings
