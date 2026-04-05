import pytest
from app.domains.cv_screening.services.seniority_utils import (
    WSI_SENIORITY_LEVELS,
    normalize_seniority,
    get_seniority_numeric,
    infer_seniority_from_title,
    is_valid_seniority_level,
    compare_seniority,
    normalize_and_validate,
)


class TestNormalizeSeniority:
    
    def test_normalize_junior_portuguese(self):
        assert normalize_seniority("Júnior") == "junior"
    
    def test_normalize_junior_english(self):
        assert normalize_seniority("junior") == "junior"
    
    def test_normalize_junior_abbreviation(self):
        assert normalize_seniority("Jr") == "junior"
    
    def test_normalize_senior_uppercase(self):
        assert normalize_seniority("SR") == "senior"
    
    def test_normalize_senior_abbreviation_with_period(self):
        assert normalize_seniority("sr.") == "senior"
    
    def test_normalize_senior_portuguese(self):
        assert normalize_seniority("Sênior") == "senior"
    
    def test_normalize_tech_lead(self):
        assert normalize_seniority("Tech Lead") == "lead"
    
    def test_normalize_pleno(self):
        assert normalize_seniority("Pleno") == "pleno"
    
    def test_normalize_mid_level(self):
        assert normalize_seniority("mid-level") == "pleno"
    
    def test_normalize_cto(self):
        assert normalize_seniority("CTO") == "executive"
    
    def test_normalize_diretor(self):
        assert normalize_seniority("Diretor") == "executive"
    
    def test_normalize_gerente(self):
        assert normalize_seniority("Gerente") == "executive"
    
    def test_normalize_none_fallback(self):
        assert normalize_seniority(None) == "pleno"
    
    def test_normalize_empty_string_fallback(self):
        assert normalize_seniority("") == "pleno"
    
    def test_normalize_unknown_fallback(self):
        assert normalize_seniority("xyz random") == "pleno"
    
    def test_normalize_entry_level(self):
        assert normalize_seniority("entry level") == "junior"
    
    def test_normalize_trainee(self):
        assert normalize_seniority("trainee") == "junior"
    
    def test_normalize_estagiario(self):
        assert normalize_seniority("estagiário") == "junior"


class TestInferSeniorityFromTitle:
    
    def test_infer_senior_software_engineer(self):
        assert infer_seniority_from_title("Senior Software Engineer") == "senior"
    
    def test_infer_junior_developer(self):
        assert infer_seniority_from_title("Junior Developer") == "junior"
    
    def test_infer_tech_lead(self):
        assert infer_seniority_from_title("Tech Lead da Equipe") == "lead"
    
    def test_infer_diretor_de_ti(self):
        assert infer_seniority_from_title("Diretor de TI") == "executive"
    
    def test_infer_gerente_de_projetos(self):
        assert infer_seniority_from_title("Gerente de Projetos") == "executive"
    
    def test_infer_engenheiro_de_software_no_indicator(self):
        assert infer_seniority_from_title("Engenheiro de Software") is None
    
    def test_infer_analista_de_dados_no_indicator(self):
        assert infer_seniority_from_title("Analista de Dados") is None
    
    def test_infer_none(self):
        assert infer_seniority_from_title(None) is None
    
    def test_infer_empty_string(self):
        assert infer_seniority_from_title("") is None
    
    def test_infer_head_of_engineering(self):
        assert infer_seniority_from_title("Head of Engineering") == "executive"
    
    def test_infer_coordenador_de_desenvolvimento(self):
        assert infer_seniority_from_title("Coordenador de Desenvolvimento") == "lead"


class TestGetSeniorityNumeric:
    
    def test_get_numeric_junior(self):
        assert get_seniority_numeric("junior") == 1
    
    def test_get_numeric_pleno(self):
        assert get_seniority_numeric("pleno") == 2
    
    def test_get_numeric_senior(self):
        assert get_seniority_numeric("senior") == 3
    
    def test_get_numeric_lead(self):
        assert get_seniority_numeric("lead") == 4
    
    def test_get_numeric_executive(self):
        assert get_seniority_numeric("executive") == 5
    
    def test_get_numeric_none_fallback(self):
        assert get_seniority_numeric(None) == 2
    
    def test_get_numeric_invalid_fallback(self):
        assert get_seniority_numeric("invalid") == 2


class TestIsValidSeniorityLevel:
    
    def test_is_valid_junior(self):
        assert is_valid_seniority_level("junior") is True
    
    def test_is_valid_pleno(self):
        assert is_valid_seniority_level("pleno") is True
    
    def test_is_valid_senior(self):
        assert is_valid_seniority_level("senior") is True
    
    def test_is_valid_lead(self):
        assert is_valid_seniority_level("lead") is True
    
    def test_is_valid_executive(self):
        assert is_valid_seniority_level("executive") is True
    
    def test_is_invalid_master(self):
        assert is_valid_seniority_level("master") is False
    
    def test_is_invalid_intern(self):
        assert is_valid_seniority_level("intern") is False
    
    def test_is_invalid_none(self):
        assert is_valid_seniority_level(None) is False
    
    def test_is_invalid_empty_string(self):
        assert is_valid_seniority_level("") is False


class TestCompareSeniority:
    
    def test_compare_junior_less_than_senior(self):
        assert compare_seniority("junior", "senior") == -1
    
    def test_compare_executive_greater_than_junior(self):
        assert compare_seniority("executive", "junior") == 1
    
    def test_compare_pleno_equals_pleno(self):
        assert compare_seniority("pleno", "pleno") == 0
    
    def test_compare_lead_greater_than_senior(self):
        assert compare_seniority("lead", "senior") == 1


class TestNormalizeAndValidate:
    
    def test_normalize_and_validate_senior(self):
        assert normalize_and_validate("Senior") == "senior"
    
    def test_normalize_and_validate_unknown(self):
        assert normalize_and_validate("xyz") is None
    
    def test_normalize_and_validate_none(self):
        assert normalize_and_validate(None) is None
    
    def test_normalize_and_validate_empty_string(self):
        assert normalize_and_validate("") is None


class TestConstantsAndMapping:
    
    def test_wsi_seniority_levels_constant(self):
        assert WSI_SENIORITY_LEVELS == ["junior", "pleno", "senior", "lead", "executive"]
    
    def test_wsi_seniority_levels_count(self):
        assert len(WSI_SENIORITY_LEVELS) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
