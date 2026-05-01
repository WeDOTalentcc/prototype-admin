"""
Tests for FairnessGuard - discriminatory pattern detection.
"""
import pytest
from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult


class TestFairnessGuardBlocking:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_blocks_gender_discrimination(self):
        result = self.guard.check("apenas homens para esta vaga")
        assert result.is_blocked
        assert result.category == "genero"
        assert len(result.blocked_terms) > 0
        assert "gênero" in result.educational_message.lower() or "legislação" in result.educational_message.lower()

    def test_blocks_gender_female_only(self):
        result = self.guard.check("somente mulheres podem se candidatar")
        assert result.is_blocked
        assert result.category == "genero"

    def test_blocks_race_discrimination(self):
        result = self.guard.check("apenas brancos para o cargo")
        assert result.is_blocked
        assert result.category == "raca_etnia"

    def test_blocks_race_exclusion(self):
        result = self.guard.check("excluir candidatos negros")
        assert result.is_blocked
        assert result.category == "raca_etnia"

    def test_blocks_age_maximum(self):
        result = self.guard.check("idade máxima 35 anos")
        assert result.is_blocked
        assert result.category == "idade"

    def test_blocks_age_range(self):
        result = self.guard.check("idade entre 25 e 35")
        assert result.is_blocked
        assert result.category == "idade"

    def test_blocks_age_exclusion(self):
        result = self.guard.check("excluir maiores de 50")
        assert result.is_blocked
        assert result.category == "idade"

    def test_blocks_religion_discrimination(self):
        result = self.guard.check("apenas cristãos para a vaga")
        assert result.is_blocked
        assert result.category == "religiao"

    def test_blocks_sexual_orientation(self):
        result = self.guard.check("excluir candidatos gays")
        assert result.is_blocked
        assert result.category == "orientacao_sexual"

    def test_blocks_marital_status(self):
        result = self.guard.check("apenas solteiros para o cargo")
        assert result.is_blocked
        assert result.category == "estado_civil"

    def test_blocks_disability_exclusion(self):
        result = self.guard.check("excluir candidatos deficientes")
        assert result.is_blocked
        assert result.category == "deficiencia"

    def test_blocks_nationality_discrimination(self):
        result = self.guard.check("apenas brasileiros para a vaga")
        assert result.is_blocked
        assert result.category == "nacionalidade"

    def test_blocks_english_gender_pattern(self):
        result = self.guard.check("male only position")
        assert result.is_blocked
        assert result.category == "genero"


class TestFairnessGuardAllowing:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_allows_skill_based_search(self):
        result = self.guard.check("buscar candidatos com Python e 5 anos de experiência")
        assert not result.is_blocked

    def test_allows_location_based_search(self):
        result = self.guard.check("candidatos em São Paulo com disponibilidade imediata")
        assert not result.is_blocked

    def test_allows_seniority_based_search(self):
        result = self.guard.check("desenvolvedor sênior com experiência em cloud")
        assert not result.is_blocked

    def test_allows_empty_query(self):
        result = self.guard.check("")
        assert not result.is_blocked

    def test_allows_none_query(self):
        result = self.guard.check("   ")
        assert not result.is_blocked

    def test_allows_experience_years(self):
        result = self.guard.check("profissional com 3 anos de experiência em gestão")
        assert not result.is_blocked

    def test_allows_salary_discussion(self):
        result = self.guard.check("faixa salarial de R$ 10.000 a R$ 15.000")
        assert not result.is_blocked


class TestFairnessGuardMetadata:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_returns_educational_message(self):
        result = self.guard.check("apenas homens")
        assert result.educational_message is not None
        assert len(result.educational_message) > 50

    def test_confidence_is_reasonable(self):
        result = self.guard.check("excluir candidatos negros da seleção")
        assert result.is_blocked
        assert 0.7 <= result.confidence <= 1.0

    def test_original_query_preserved(self):
        query = "apenas mulheres para secretária"
        result = self.guard.check(query)
        assert result.original_query == query

    def test_get_categories_returns_all(self):
        categories = self.guard.get_categories()
        assert len(categories) == 9
        assert "genero" in categories
        assert "raca_etnia" in categories
        assert "idade" in categories
        assert "religiao" in categories
