"""Contract tests P2-2 Sprint A — onboarding_yaml_loader.

TDD canonical (skill lia-testing): test FIRST validates contract
antes de extension do orchestrator depender deste loader.
"""
import pytest
from app.services.onboarding_yaml_loader import (
    load_config,
    get_next_question,
    calculate_progress,
    is_complete,
    OnboardingConfig,
    OnboardingBlock,
    OnboardingField,
)


class TestLoadConfig:
    """Schema sync: YAML canonical → typed dataclasses."""

    def test_loads_5_blocks(self):
        config = load_config()
        assert len(config.blocks) == 5

    def test_loads_34_fields_total(self):
        config = load_config()
        assert config.total_fields == 34

    def test_locale_is_pt_br(self):
        config = load_config()
        assert config.locale == "pt-BR"

    def test_version_is_int(self):
        config = load_config()
        assert isinstance(config.version, int)
        assert config.version >= 1

    def test_finalization_threshold_canonical(self):
        config = load_config()
        # P2-2 ADR estabeleceu 80% como threshold canonical
        assert config.finalization_threshold_percent == 80

    def test_persona_strings_non_empty(self):
        config = load_config()
        assert len(config.persona_greeting) > 0
        assert len(config.persona_closing) > 0
        assert len(config.persona_hint_skip) > 0

    def test_lru_cached(self):
        # Second call deve retornar mesmo instance (lru_cache)
        c1 = load_config()
        c2 = load_config()
        assert c1 is c2


class TestBlocksCanonical:
    """Blocks canonical: ids + fields esperados."""

    def test_block_ids_canonical(self):
        config = load_config()
        expected = {"basic", "culture", "policy", "workforce", "lia_persona"}
        actual = set(config.block_ids)
        assert actual == expected

    def test_basic_block_has_6_fields(self):
        config = load_config()
        basic = config.get_block("basic")
        assert basic is not None
        assert len(basic.fields) == 6

    def test_policy_block_has_canonical_questions(self):
        """P0-1 perguntas longas devem aparecer em block policy."""
        config = load_config()
        policy = config.get_block("policy")
        assert policy is not None
        field_keys = set(f.field_key for f in policy.fields)
        # Subset das 18 P0-1 que cobrimos no YAML
        assert "manager_approval_for_offer" in field_keys
        assert "min_interviews_before_offer" in field_keys
        assert "allowed_days" in field_keys
        assert "autonomy_level" in field_keys


class TestGetField:
    """Lookup canonical por field_key. Fail-CLOSED se nao existir."""

    def test_get_existing_field(self):
        config = load_config()
        field = config.get_field("mission")
        assert field is not None
        assert field.field_key == "mission"
        assert "missão" in field.question.lower()

    def test_get_unknown_field_returns_none(self):
        """Fail-CLOSED canonical: campo inexistente retorna None,
        NUNCA fallback silencioso."""
        config = load_config()
        assert config.get_field("totally_made_up_field") is None

    def test_get_unknown_block_returns_none(self):
        config = load_config()
        assert config.get_block("nonexistent_block") is None


class TestGetNextQuestion:
    """Orquestracao de perguntas: state machine canonical."""

    def test_first_question_is_basic_name(self):
        """Primeiro field do primeiro bloco (basic.name)."""
        result = get_next_question(answered_field_keys=set())
        assert result is not None
        block, field = result
        assert block.id == "basic"
        assert field.field_key == "name"

    def test_continues_in_current_block(self):
        """Se current_block setado, retorna next field do mesmo bloco."""
        result = get_next_question(
            answered_field_keys={"name"},
            current_block_id="basic",
        )
        assert result is not None
        block, field = result
        assert block.id == "basic"
        assert field.field_key == "trade_name"

    def test_skips_to_next_block_when_current_complete(self):
        """Se current_block esgotado, vai pra proximo."""
        config = load_config()
        basic = config.get_block("basic")
        answered = set(basic.field_keys)
        result = get_next_question(
            answered_field_keys=answered,
            current_block_id="basic",
        )
        # Deve pular pra culture
        assert result is not None
        block, _ = result
        assert block.id == "culture"

    def test_returns_none_when_all_answered(self):
        """Final: TODOS fields respondidos → None (sinal de fim)."""
        config = load_config()
        all_keys = set()
        for block in config.blocks:
            all_keys.update(block.field_keys)
        result = get_next_question(answered_field_keys=all_keys)
        assert result is None

    def test_respects_depends_on(self):
        """Campo com depends_on so e perguntado apos a dependencia."""
        # salary_tolerance_percent depends_on salary_screening_enabled
        result = get_next_question(
            answered_field_keys={"name", "trade_name", "cnpj", "website", "industry", "employee_count",
                                  "mission", "vision", "values", "work_model", "dei_initiatives", "evp_bullets",
                                  "auto_screening_enabled", "min_interviews_before_offer",
                                  "auto_stage_advance_enabled", "max_days_in_stage",
                                  "manager_approval_for_offer", "autonomy_level",
                                  "allowed_days", "allowed_hours", "preferred_channel",
                                  "auto_rejection_feedback", "rejection_feedback_deadline_hours",
                                  "default_interview_duration_min", "auto_scheduling_enabled"},
            current_block_id="policy",
        )
        # Estamos na sessao filtros_compatibilidade. salary_screening_enabled
        # devera vir ANTES de salary_tolerance_percent (depends_on).
        assert result is not None
        _, field = result
        # Se ainda nao respondemos salary_screening_enabled, NAO devemos retornar
        # salary_tolerance_percent que depende dele.
        if field.field_key == "salary_tolerance_percent":
            pytest.fail("depends_on violado — salary_tolerance_percent sugerido sem salary_screening_enabled")


class TestProgressCalculation:
    """Calculo de progress canonical."""

    def test_zero_answered_is_zero_percent(self):
        assert calculate_progress(set()) == 0

    def test_all_answered_is_100_percent(self):
        config = load_config()
        all_keys = set()
        for block in config.blocks:
            all_keys.update(block.field_keys)
        assert calculate_progress(all_keys) == 100

    def test_unknown_field_keys_ignored(self):
        """Fail-CLOSED: keys que nao existem no YAML nao contam pra progress."""
        result = calculate_progress({"made_up_field", "another_fake"})
        assert result == 0

    def test_is_complete_at_threshold(self):
        config = load_config()
        # 80% de 34 = 27.2 → 27 ja é < 80% (27/34=79.4%)
        # 28/34 = 82.3% → True
        all_keys = []
        for block in config.blocks:
            all_keys.extend(block.field_keys)
        partial = set(all_keys[:28])
        assert is_complete(partial) is True

        small = set(all_keys[:5])
        assert is_complete(small) is False


class TestFailClosedSemantics:
    """Princípio canonical-fix: falhar alto, nunca silenciosamente."""

    def test_yaml_loader_raises_if_missing(self, monkeypatch, tmp_path):
        """Se YAML missing, FileNotFoundError — nunca silent fallback."""
        from app.services import onboarding_yaml_loader
        # Limpa cache pra forcar reload
        onboarding_yaml_loader.load_config.cache_clear()

        fake_path = tmp_path / "nonexistent.yaml"
        monkeypatch.setattr(onboarding_yaml_loader, "YAML_PATH", fake_path)

        with pytest.raises(FileNotFoundError):
            onboarding_yaml_loader.load_config()

        # Cleanup: restore real loader pra outros tests
        onboarding_yaml_loader.load_config.cache_clear()
