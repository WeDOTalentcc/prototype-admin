import pytest

from app.domains.job_management.services.seniority_jd_analyzer import (
    AUTONOMY_INDICATORS,
    COMPLEXITY_INDICATORS,
    _calculate_confidence,
    _extract_experience_level,
    _find_keyword_indicators,
    analyze_jd_for_seniority,
)


class TestExperienceExtraction:

    def test_five_plus_years_portuguese_senior(self):
        level, evidence = _extract_experience_level("5+ anos de experiência")
        assert level == "senior"
        assert len(evidence) > 0

    def test_up_to_two_years_junior(self):
        level, evidence = _extract_experience_level("até 2 anos")
        assert level == "junior"
        assert len(evidence) > 0

    def test_three_to_five_years_pleno(self):
        level, evidence = _extract_experience_level("3 a 5 anos de experiência")
        assert level == "pleno"
        assert len(evidence) > 0

    def test_ten_plus_years_english(self):
        level, evidence = _extract_experience_level("10+ years of experience")
        assert level in ["executive", "lead"]
        assert len(evidence) > 0

    def test_minimum_five_years_senior(self):
        level, evidence = _extract_experience_level("mínimo 5 anos")
        assert level == "senior"
        assert len(evidence) > 0

    def test_no_experience_mention(self):
        level, evidence = _extract_experience_level("buscamos profissional motivado")
        assert level is None
        assert evidence == []

    def test_one_to_two_years_junior(self):
        level, evidence = _extract_experience_level("1 to 2 years")
        assert level == "junior"
        assert len(evidence) > 0


class TestKeywordIndicators:

    def test_complexity_junior_basico(self):
        result = _find_keyword_indicators("conhecimento básico de python", COMPLEXITY_INDICATORS)
        assert "junior" in result
        assert any("básico" in kw for kw in result["junior"])

    def test_complexity_senior_arquitetura(self):
        result = _find_keyword_indicators("arquitetura de microserviços e system design", COMPLEXITY_INDICATORS)
        assert "senior" in result
        found_keywords = result["senior"]
        assert any(kw in ["arquitetura", "microserviços", "system design"] for kw in found_keywords)

    def test_complexity_lead_estrategico(self):
        result = _find_keyword_indicators("estratégico e visão de negócio", COMPLEXITY_INDICATORS)
        assert "lead" in result
        found_keywords = result["lead"]
        assert any(kw in ["estratégico", "visão de negócio"] for kw in found_keywords)

    def test_autonomy_junior_supervisao(self):
        result = _find_keyword_indicators("trabalhar sob supervisão", AUTONOMY_INDICATORS)
        assert "junior" in result
        assert any("sob supervisão" in kw for kw in result["junior"])

    def test_autonomy_senior_autonomia_total(self):
        result = _find_keyword_indicators("autonomia total e tomada de decisão", AUTONOMY_INDICATORS)
        assert "senior" in result
        found_keywords = result["senior"]
        assert any(kw in ["autonomia total", "tomada de decisão"] for kw in found_keywords)


class TestConfidenceCalculation:

    def test_zero_indicators(self):
        assert _calculate_confidence(0) == 0.0

    def test_one_indicator(self):
        assert _calculate_confidence(1) == 0.50

    def test_two_indicators(self):
        assert _calculate_confidence(2) == 0.65

    def test_three_indicators(self):
        assert _calculate_confidence(3) == 0.65

    def test_four_indicators(self):
        assert _calculate_confidence(4) == 0.80

    def test_five_indicators(self):
        assert _calculate_confidence(5) == 0.80

    def test_six_indicators(self):
        assert _calculate_confidence(6) == 0.90

    def test_ten_indicators(self):
        assert _calculate_confidence(10) == 0.90


class TestAnalyzeJDComplete:

    def test_senior_jd(self):
        jd = (
            "Buscamos desenvolvedor com 5+ anos de experiência. "
            "Necessário conhecimento em arquitetura de sistemas e microserviços. "
            "Autonomia total para tomada de decisão técnica. "
            "Experiência com mentoria de desenvolvedores juniores."
        )
        result = analyze_jd_for_seniority(jd)
        assert result["level"] == "senior"
        assert result["confidence"] >= 0.65

    def test_junior_jd(self):
        jd = (
            "Vaga para desenvolvedor com até 2 anos de experiência. "
            "Conhecimento básico de programação. "
            "Trabalhar sob supervisão do líder técnico. "
            "Cursando graduação em computação."
        )
        result = analyze_jd_for_seniority(jd)
        assert result["level"] == "junior"

    def test_empty_jd(self):
        result = analyze_jd_for_seniority("")
        assert result["level"] is None
        assert result["confidence"] == 0.0

    def test_pleno_jd(self):
        jd = (
            "Profissional com experiência comprovada e 3 a 5 anos de atuação. "
            "Autônomo em tarefas do dia a dia."
        )
        result = analyze_jd_for_seniority(jd)
        assert result["level"] == "pleno"

    def test_mixed_indicators_highest_count_wins(self):
        jd = (
            "5+ anos de experiência em desenvolvimento. "
            "Arquitetura de sistemas distribuídos. "
            "Autonomia total e ownership. "
            "Mentoria de profissionais. "
            "Conhecimento básico de ferramentas auxiliares."
        )
        result = analyze_jd_for_seniority(jd)
        assert result["level"] == "senior"

    def test_return_dict_has_required_keys(self):
        result = analyze_jd_for_seniority("qualquer texto")
        assert "level" in result
        assert "confidence" in result
        assert "evidence" in result
        assert "indicators" in result

    def test_empty_whitespace_jd(self):
        result = analyze_jd_for_seniority("   ")
        assert result["level"] is None
        assert result["confidence"] == 0.0

    def test_none_like_empty(self):
        result = analyze_jd_for_seniority("")
        assert result == {
            "level": None,
            "confidence": 0.0,
            "evidence": [],
            "indicators": {},
        }


class TestDeterminism:

    def test_same_input_same_output(self):
        jd = (
            "Desenvolvedor senior com 5+ anos de experiência. "
            "Arquitetura de microserviços e system design. "
            "Autonomia total e mentoria de juniores."
        )
        results = [analyze_jd_for_seniority(jd) for _ in range(3)]
        assert results[0] == results[1]
        assert results[1] == results[2]

    def test_no_randomness_in_output(self):
        jd = "Vaga para desenvolvedor com até 2 anos, conhecimento básico, sob supervisão."
        results = [analyze_jd_for_seniority(jd) for _ in range(3)]
        assert all(r["level"] == results[0]["level"] for r in results)
        assert all(r["confidence"] == results[0]["confidence"] for r in results)
        assert all(r["evidence"] == results[0]["evidence"] for r in results)
        assert all(r["indicators"] == results[0]["indicators"] for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
