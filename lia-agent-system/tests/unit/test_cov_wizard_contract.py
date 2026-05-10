"""Coverage tests for wizard_contract.py — Pydantic contract models."""
import pytest
from app.contracts.wizard_contract import (
    BigFiveProfileContract,
    TraitRankingContract,
    ScreeningQuestionContract,
    EligibilityQuestionContract,
    CalibrationCandidateContract,
    WizardStagePayloadContract,
    JobCreationStateContract,
    WIZARD_CONTRACT_MODELS,
    WizardStage,
    ScreeningMode,
    SourcingMode,
    QuestionFramework,
    QuestionBlock,
    QuestionCompetency,
    EligibilityAnswer,
    CalibrationDecision,
)


class TestBigFiveProfileContract:
    def test_default_all_none(self):
        m = BigFiveProfileContract()
        assert m.openness is None
        assert m.conscientiousness is None
        assert m.extraversion is None
        assert m.agreeableness is None
        assert m.stability is None

    def test_with_all_scores(self):
        m = BigFiveProfileContract(
            openness=0.7,
            conscientiousness=0.8,
            extraversion=0.6,
            agreeableness=0.75,
            stability=0.9,
        )
        assert m.openness == pytest.approx(0.7)
        assert m.conscientiousness == pytest.approx(0.8)

    def test_score_at_zero(self):
        m = BigFiveProfileContract(openness=0.0)
        assert m.openness == 0.0

    def test_score_at_one(self):
        m = BigFiveProfileContract(openness=1.0)
        assert m.openness == 1.0

    def test_with_evidences(self):
        m = BigFiveProfileContract(
            openness=0.7,
            evidences={"openness": ["Exemplo 1", "Exemplo 2"]}
        )
        assert m.evidences is not None
        assert "openness" in m.evidences


class TestTraitRankingContract:
    def test_basic_instantiation(self):
        m = TraitRankingContract(trait="conscientiousness", score=0.8, rank=1, weight=0.8)
        assert m.trait == "conscientiousness"
        assert m.score == pytest.approx(0.8)
        assert m.rank == 1

    def test_required_fields(self):
        with pytest.raises(Exception):
            TraitRankingContract()  # missing required fields

    def test_score_and_weight_range(self):
        m = TraitRankingContract(trait="openness", score=0.0, rank=5, weight=1.0)
        assert m.score == 0.0
        assert m.weight == 1.0


def _make_q(id_="q1", block="technical", competency="technical"):
    return ScreeningQuestionContract(
        id=id_,
        question="Descreva um desafio técnico que você resolveu.",
        ideal_answer="Deve mencionar diagnóstico, solução e resultado.",
        block=block,
        competency=competency,
        framework="CBI",
        skill="system_design",
    )


class TestScreeningQuestionContract:
    def test_basic_instantiation(self):
        m = _make_q()
        assert m.id == "q1"
        assert m.block == "technical"
        assert m.ideal_answer == "Deve mencionar diagnóstico, solução e resultado."

    def test_behavioral_block(self):
        m = _make_q(id_="q3", block="behavioral", competency="behavioral")
        assert m.block == "behavioral"

    def test_default_scoring_rubric(self):
        m = _make_q()
        assert m.scoring_rubric == {}

    def test_default_weight(self):
        m = _make_q()
        assert m.weight == pytest.approx(1.0)

    def test_default_approved_none(self):
        m = _make_q()
        assert m.approved is None


class TestEligibilityQuestionContract:
    def test_basic_instantiation(self):
        m = EligibilityQuestionContract(
            id="e1",
            question="Você tem CNH categoria B?",
            required_answer="yes",
        )
        assert m.id == "e1"
        assert m.required_answer == "yes"

    def test_required_answer_no(self):
        m = EligibilityQuestionContract(
            id="e2",
            question="Você tem disponibilidade para viagens?",
            required_answer="no",
        )
        assert m.required_answer == "no"


class TestCalibrationCandidateContract:
    def test_basic_instantiation(self):
        m = CalibrationCandidateContract(
            id="cand-001",
            name="Ana Silva",
            match_score=0.85,
        )
        assert m.id == "cand-001"
        assert m.name == "Ana Silva"
        assert m.match_score == pytest.approx(0.85)

    def test_optional_fields_default_none(self):
        m = CalibrationCandidateContract(id="cand-002", name="Bruno Costa", match_score=0.70)
        assert m.current_title is None
        assert m.decision is None

    def test_with_decision(self):
        m = CalibrationCandidateContract(id="c3", name="Carlos", match_score=0.6, decision="approved")
        assert m.decision == "approved"


class TestWizardStagePayloadContract:
    def test_basic_instantiation(self):
        m = WizardStagePayloadContract(stage="intake", completeness=0.3)
        assert m.stage == "intake"
        assert m.completeness == pytest.approx(0.3)

    def test_default_type(self):
        m = WizardStagePayloadContract(stage="review", completeness=0.8)
        assert m.type == "wizard_stage"

    def test_default_requires_approval(self):
        m = WizardStagePayloadContract(stage="intake", completeness=0.5)
        assert m.requires_approval is False

    def test_with_data(self):
        m = WizardStagePayloadContract(
            stage="bigfive",
            completeness=1.0,
            data={"openness": 0.7},
            requires_approval=True,
        )
        assert m.requires_approval is True
        assert m.data["openness"] == pytest.approx(0.7)


class TestJobCreationStateContract:
    def test_all_defaults_none_or_empty(self):
        m = JobCreationStateContract()
        assert m.session_id is None
        assert m.user_id is None
        assert m.current_stage is None
        assert m.stage_history == []
        assert m.error is None

    def test_with_session_metadata(self):
        m = JobCreationStateContract(
            session_id="sess-123",
            user_id="user-456",
            language="pt-BR",
        )
        assert m.session_id == "sess-123"
        assert m.language == "pt-BR"

    def test_with_current_stage(self):
        m = JobCreationStateContract(current_stage="intake")
        assert m.current_stage == "intake"

    def test_with_stage_history(self):
        m = JobCreationStateContract(stage_history=["intake", "jd_enrichment"])
        assert len(m.stage_history) == 2

    def test_with_parsed_fields(self):
        m = JobCreationStateContract(
            parsed_title="Backend Engineer",
            parsed_department="Engenharia",
            parsed_seniority="senior",
            parsed_location="São Paulo",
            intake_confidence=0.92,
        )
        assert m.parsed_title == "Backend Engineer"
        assert m.intake_confidence == pytest.approx(0.92)

    def test_with_jd_fields(self):
        m = JobCreationStateContract(
            jd_raw="Vaga de Backend",
            jd_quality_score=85.0,
            jd_approved=True,
        )
        assert m.jd_approved is True
        assert m.jd_quality_score == pytest.approx(85.0)

    def test_with_bigfive_profile(self):
        bf = BigFiveProfileContract(openness=0.7, conscientiousness=0.8)
        m = JobCreationStateContract(bigfive_profile=bf)
        assert m.bigfive_profile is not None
        assert m.bigfive_profile.openness == pytest.approx(0.7)

    def test_with_salary_fields(self):
        m = JobCreationStateContract(salary_min=5000, salary_max=10000, salary_currency="BRL")
        assert m.salary_min == 5000
        assert m.salary_currency == "BRL"

    def test_with_wsi_questions(self):
        q = _make_q()
        m = JobCreationStateContract(wsi_questions=[q])
        assert len(m.wsi_questions) == 1

    def test_with_error(self):
        m = JobCreationStateContract(error="Erro ao enriquecer JD")
        assert m.error == "Erro ao enriquecer JD"


class TestWizardContractModels:
    def test_wizard_contract_models_is_list(self):
        assert isinstance(WIZARD_CONTRACT_MODELS, list)

    def test_wizard_contract_models_nonempty(self):
        assert len(WIZARD_CONTRACT_MODELS) > 0

    def test_job_creation_state_in_models(self):
        model_names = [m.__name__ for m in WIZARD_CONTRACT_MODELS]
        assert "JobCreationStateContract" in model_names


class TestLiteralTypes:
    def test_wizard_stage_values(self):
        # Just importing and using the type aliases
        stages = ["intake", "jd_enrichment", "bigfive", "salary", "competency",
                  "wsi_questions", "eligibility", "review", "publish",
                  "calibration", "handoff", "done", "scheduling"]
        for stage in stages:
            m = JobCreationStateContract(current_stage=stage)
            assert m.current_stage == stage

    def test_screening_mode_values(self):
        for mode in ["compact", "full"]:
            m = JobCreationStateContract(screening_mode=mode)
            assert m.screening_mode == mode
