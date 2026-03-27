import pytest
import time
from app.shared.intelligence.smart_extractor import SmartExtractor, ParamExtractor, ExtractedParams, ExtractionCache
from app.shared.intelligence.param_patterns import (
    ParamPattern, ParamType, ExtractionResult, get_patterns_for_domain, UNIVERSAL_PATTERNS,
    DOMAIN_PARAM_PATTERNS,
)


class TestParamPatterns:
    def test_universal_patterns_exist(self):
        assert len(UNIVERSAL_PATTERNS) == 9

    def test_domain_patterns_sourcing(self):
        patterns = DOMAIN_PARAM_PATTERNS["sourcing"]
        names = [p.name for p in patterns]
        assert "quantity" in names
        assert "skills" in names
        assert "seniority" in names

    def test_domain_patterns_job_management(self):
        patterns = DOMAIN_PARAM_PATTERNS["job_management"]
        names = [p.name for p in patterns]
        assert "salary" in names
        assert "seniority" in names

    def test_domain_patterns_unknown_domain(self):
        patterns = get_patterns_for_domain("unknown_domain")
        names = [p.name for p in patterns]
        assert "salary" in names
        assert "quantity" in names

    def test_get_patterns_for_domain_dedup(self):
        patterns = get_patterns_for_domain("sourcing")
        names = [p.name for p in patterns]
        assert len(names) == len(set(names))

    def test_get_patterns_for_domain_includes_universal(self):
        patterns = get_patterns_for_domain("analytics")
        names = [p.name for p in patterns]
        assert "salary" in names
        assert "date" in names


class TestParamExtractor:
    def setup_method(self):
        self.extractor = ParamExtractor()

    def test_salary_real(self):
        result = self.extractor.extract("salário R$ 12.000")
        assert result.has_params
        assert "salary" in result.params
        assert result.params["salary"] == 12000.0

    def test_salary_k(self):
        result = self.extractor.extract("salário de 15k")
        assert result.has_params
        assert "salary" in result.params
        assert result.params["salary"] == 15000.0

    def test_salary_mil(self):
        result = self.extractor.extract("pagando 12 mil")
        assert result.has_params
        assert "salary" in result.params
        assert result.params["salary"] == 12000.0

    def test_salary_range(self):
        result = self.extractor.extract("salário de R$ 10.000 a R$ 15.000")
        assert result.has_params
        assert "salary" in result.params

    def test_top_n(self):
        result = self.extractor.extract("top 5 candidatos")
        assert result.has_params
        assert "quantity" in result.params
        assert result.params["quantity"] == 5

    def test_n_candidates(self):
        result = self.extractor.extract("10 candidatos para a vaga")
        assert result.has_params
        assert "quantity" in result.params
        assert result.params["quantity"] == 10

    def test_limite(self):
        result = self.extractor.extract("limite de 20 resultados")
        assert result.has_params
        assert "quantity" in result.params
        assert result.params["quantity"] == 20

    def test_score_above(self):
        result = self.extractor.extract("score acima de 80")
        assert result.has_params
        assert "score" in result.params
        assert result.params["score"] == 80

    def test_score_below(self):
        result = self.extractor.extract("score abaixo de 50")
        assert result.has_params
        assert "score" in result.params
        assert result.params["score"] == 50

    def test_aderencia(self):
        result = self.extractor.extract("80% de aderência")
        assert result.has_params
        assert "score" in result.params
        assert result.params["score"] == 80

    def test_junior(self):
        result = self.extractor.extract("desenvolvedor júnior")
        assert result.has_params
        assert "seniority" in result.params
        assert result.params["seniority"] == "junior"

    def test_senior(self):
        result = self.extractor.extract("engenheiro sênior")
        assert result.has_params
        assert "seniority" in result.params
        assert result.params["seniority"] == "senior"

    def test_pleno(self):
        result = self.extractor.extract("analista pleno")
        assert result.has_params
        assert "seniority" in result.params
        assert result.params["seniority"] == "mid"

    def test_staff(self):
        result = self.extractor.extract("staff engineer")
        assert result.has_params
        assert "seniority" in result.params
        assert result.params["seniority"] == "staff"

    def test_remoto(self):
        result = self.extractor.extract("vaga remoto")
        assert result.has_params
        assert "work_model" in result.params
        assert result.params["work_model"] == "remote"

    def test_hibrido(self):
        result = self.extractor.extract("trabalho híbrido")
        assert result.has_params
        assert "work_model" in result.params
        assert result.params["work_model"] == "hybrid"

    def test_presencial(self):
        result = self.extractor.extract("vaga presencial")
        assert result.has_params
        assert "work_model" in result.params
        assert result.params["work_model"] == "onsite"

    def test_sao_paulo(self):
        result = self.extractor.extract("vaga em São Paulo")
        assert result.has_params
        assert "location" in result.params
        assert "São Paulo" in str(result.params["location"])

    def test_rio(self):
        result = self.extractor.extract("trabalhar em Rio de Janeiro")
        assert result.has_params
        assert "location" in result.params
        assert "Rio de Janeiro" in str(result.params["location"])

    def test_hoje(self):
        result = self.extractor.extract("relatório de hoje")
        assert result.has_params
        assert "date" in result.params

    def test_ultima_semana(self):
        result = self.extractor.extract("última semana")
        assert result.has_params
        assert "date" in result.params

    def test_ultimos_30_dias(self):
        result = self.extractor.extract("últimos 30 dias")
        assert result.has_params
        assert "date" in result.params

    def test_desde_janeiro(self):
        result = self.extractor.extract("desde janeiro")
        assert result.has_params
        assert "date" in result.params

    def test_single_skill(self):
        result = self.extractor.extract("candidatos com python")
        assert result.has_params
        assert "skills" in result.params

    def test_multiple_skills(self):
        result = self.extractor.extract("preciso de alguém com python e react")
        assert result.has_params
        assert "skills" in result.params
        skills = result.params["skills"]
        if isinstance(skills, list):
            skills_lower = [s.lower() for s in skills]
            assert "python" in skills_lower
            assert "react" in skills_lower
        else:
            assert skills.lower() in ("python", "react")

    def test_com_experiencia(self):
        result = self.extractor.extract("com experiência em gestão")
        assert result.has_params
        assert "boolean_flags" in result.params

    def test_sem_formacao(self):
        result = self.extractor.extract("sem formação superior")
        assert result.has_params
        assert "boolean_flags" in result.params

    def test_complex_query(self):
        result = self.extractor.extract(
            "top 5 candidatos python sênior em São Paulo remoto"
        )
        assert result.has_params
        assert "quantity" in result.params
        assert "skills" in result.params
        assert "seniority" in result.params
        assert "work_model" in result.params
        assert result.confidence > 0.8

    def test_no_params(self):
        result = self.extractor.extract("olá, como vai?")
        assert not result.has_params
        assert result.confidence == 0.0
        assert result.source == "none"

    def test_confidence_single_param(self):
        result = self.extractor.extract("buscar candidatos python")
        assert 0.3 < result.confidence < 0.8

    def test_confidence_multiple_params(self):
        result = self.extractor.extract(
            "top 10 candidatos python sênior em São Paulo remoto score acima de 80"
        )
        assert result.confidence >= 0.8

    def test_extraction_time(self):
        result = self.extractor.extract("top 5 candidatos python sênior")
        assert result.extraction_time_ms >= 0
        assert result.extraction_time_ms < 100

    def test_with_domain_id(self):
        result = self.extractor.extract("top 5 candidatos python", domain_id="sourcing")
        assert result.has_params


class TestExtractionCache:
    def test_set_get(self):
        cache = ExtractionCache(ttl_seconds=60)
        params = ExtractedParams(params={"key": "val"}, source="regex", confidence=0.9)
        cache.set("test query", "domain1", params)
        result = cache.get("test query", "domain1")
        assert result is not None
        assert result.params == {"key": "val"}
        assert result.cached is True
        assert result.source == "cached"

    def test_ttl_expiry(self):
        cache = ExtractionCache(ttl_seconds=1)
        params = ExtractedParams(params={"key": "val"}, source="regex", confidence=0.9)
        cache.set("test query", "domain1", params)
        time.sleep(1.1)
        result = cache.get("test query", "domain1")
        assert result is None

    def test_max_entries_eviction(self):
        cache = ExtractionCache(ttl_seconds=60, max_entries=3)
        for i in range(5):
            params = ExtractedParams(params={"i": i}, source="regex", confidence=0.9)
            cache.set(f"query {i}", "domain", params)
        assert cache.size() <= 3

    def test_normalize(self):
        cache = ExtractionCache()
        assert cache._normalize("  Hello  WORLD  ") == "hello world"
        assert cache._normalize("São Paulo") == cache._normalize("são paulo")

    def test_cache_miss(self):
        cache = ExtractionCache()
        result = cache.get("nonexistent", "domain1")
        assert result is None

    def test_clear(self):
        cache = ExtractionCache()
        params = ExtractedParams(params={"key": "val"}, source="regex", confidence=0.9)
        cache.set("q1", "d1", params)
        cache.set("q2", "d1", params)
        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0


class TestSmartExtractor:
    def setup_method(self):
        self.extractor = SmartExtractor()

    def test_regex_only_high_confidence(self):
        result = self.extractor.extract(
            "top 10 candidatos python sênior em São Paulo remoto"
        )
        assert result.has_params
        assert result.confidence >= 0.8
        assert result.source == "regex"

    def test_hybrid_low_confidence(self):
        result = self.extractor.extract("buscar candidatos python")
        assert result.has_params
        if result.confidence < 0.8:
            assert result.source in ("hybrid", "none")

    def test_cached_result(self):
        query = "top 10 candidatos python sênior em São Paulo remoto"
        result1 = self.extractor.extract(query)
        result2 = self.extractor.extract(query)
        assert result2.cached is True
        assert result2.source == "cached"

    def test_no_params(self):
        result = self.extractor.extract("olá, como vai?")
        assert not result.has_params
        assert result.source == "none"

    def test_with_domain(self):
        result = self.extractor.extract(
            "top 5 candidatos python sênior", domain_id="sourcing"
        )
        assert result.has_params

    def test_stats(self):
        extractor = SmartExtractor()
        extractor.extract("top 10 candidatos python sênior em São Paulo remoto")
        extractor.extract("olá")
        stats = extractor.get_stats()
        assert stats["total_extractions"] == 2
        assert "regex_only_count" in stats
        assert "cache_hit_count" in stats
        assert "regex_only_rate" in stats

    def test_clear_cache(self):
        self.extractor.extract("top 10 candidatos python")
        assert self.extractor.get_stats()["cache_size"] > 0
        self.extractor.clear_cache()
        assert self.extractor.get_stats()["cache_size"] == 0

    def test_sourcing_query(self):
        result = self.extractor.extract(
            "buscar top 10 candidatos python sênior", domain_id="sourcing"
        )
        assert result.has_params
        assert "quantity" in result.params
        assert "skills" in result.params
        assert "seniority" in result.params

    def test_job_query(self):
        result = self.extractor.extract(
            "criar vaga desenvolvedor R$ 15k remoto", domain_id="job_management"
        )
        assert result.has_params
        assert "salary" in result.params
        assert "work_model" in result.params

    def test_analytics_query(self):
        result = self.extractor.extract(
            "relatório dos últimos 30 dias", domain_id="analytics"
        )
        assert result.has_params
        assert "date" in result.params

    def test_screening_query(self):
        result = self.extractor.extract(
            "triagem com score acima de 70", domain_id="cv_screening"
        )
        assert result.has_params
        assert "score" in result.params

    def test_extraction_details(self):
        result = self.extractor.extract("candidatos python sênior")
        assert len(result.extraction_details) > 0
        for detail in result.extraction_details:
            assert detail.source == "regex"
            assert detail.confidence > 0

    def test_available_actions_param(self):
        result = self.extractor.extract(
            "top 5 candidatos",
            available_actions=["search", "filter"],
        )
        assert result.has_params
