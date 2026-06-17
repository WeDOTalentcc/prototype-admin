"""
2.5: Schema Pydantic canônico para score_breakdown JSONB.

Garante que:
1. ScoreBreakdownSchema existe em app.schemas.score_breakdown_schema
2. RankingScoreBreakdown.to_dict() produz dict válido pelo schema
3. update_score_breakdown valida antes de persistir
4. Dict inválido (campo faltando) é rejeitado com ValidationError
5. Campos opcionais adicionados pelo bloco 2.3 (wsi_score_raw, formula) são aceitos
6. Leitura via parse_ai_analysis retorna ScoreBreakdownSchema ou None (se inválido)
"""
from __future__ import annotations

import pytest


class TestScoreBreakdownSchema:
    """2.5: ScoreBreakdownSchema valida score_breakdown JSONB."""

    def test_schema_exists(self):
        """ScoreBreakdownSchema deve existir no módulo schemas."""
        from app.schemas.score_breakdown_schema import ScoreBreakdownSchema  # noqa: F401

    def test_valid_breakdown_from_service(self):
        """RankingScoreBreakdown.to_dict() passa pelo schema sem erros."""
        from app.schemas.score_breakdown_schema import ScoreBreakdownSchema
        from app.domains.cv_screening.services.lia_score_service import get_lia_score_service

        svc = get_lia_score_service()
        result = svc.calculate_ranking_score(
            candidate={"id": "test-cand"},
            rubricas_score=70.0,
            wsi_score=80.0,
        )
        breakdown_dict = result.breakdown.to_dict()
        schema = ScoreBreakdownSchema.model_validate(breakdown_dict)
        assert schema.final_score == breakdown_dict["final_score"]

    def test_invalid_dict_raises_validation_error(self):
        """Dict sem campos obrigatórios deve levantar ValidationError."""
        from pydantic import ValidationError
        from app.schemas.score_breakdown_schema import ScoreBreakdownSchema

        with pytest.raises(ValidationError):
            ScoreBreakdownSchema.model_validate({"rubricas_score": 70.0})  # falta tudo

    def test_optional_fields_accepted(self):
        """Campos opcionais do bloco 2.3 (wsi_score_raw, formula) são aceitos."""
        from app.schemas.score_breakdown_schema import ScoreBreakdownSchema
        from app.domains.cv_screening.services.lia_score_service import get_lia_score_service

        svc = get_lia_score_service()
        result = svc.calculate_ranking_score(
            candidate={"id": "test-cand"},
            rubricas_score=60.0,
            wsi_score=75.0,
        )
        bd = result.breakdown.to_dict()
        bd["wsi_score_raw"] = 7.5   # 0-10, adicionado pelo bloco 2.3
        bd["formula"] = "ranking_v1"
        schema = ScoreBreakdownSchema.model_validate(bd)
        assert schema.formula == "ranking_v1"

    def test_parse_ai_analysis_returns_schema_on_valid_dict(self):
        """parse_ai_analysis helper retorna ScoreBreakdownSchema para dict válido."""
        from app.schemas.score_breakdown_schema import parse_ai_analysis
        from app.domains.cv_screening.services.lia_score_service import get_lia_score_service

        svc = get_lia_score_service()
        result = svc.calculate_ranking_score(
            candidate={"id": "test-cand"},
            rubricas_score=50.0,
        )
        parsed = parse_ai_analysis(result.breakdown.to_dict())
        assert parsed is not None
        assert parsed.rubricas_score == pytest.approx(50.0, abs=1)

    def test_parse_ai_analysis_returns_none_on_garbage(self):
        """parse_ai_analysis retorna None sem levantar exceção para dict inválido."""
        from app.schemas.score_breakdown_schema import parse_ai_analysis

        result = parse_ai_analysis({"garbage": True})
        assert result is None

    def test_completeness_factor_bounds(self):
        """completeness_factor deve ser rejeitado se fora de 0.0-1.0."""
        from pydantic import ValidationError
        from app.schemas.score_breakdown_schema import ScoreBreakdownSchema
        from app.domains.cv_screening.services.lia_score_service import get_lia_score_service

        svc = get_lia_score_service()
        result = svc.calculate_ranking_score(candidate={"id": "t"}, rubricas_score=70.0)
        bd = result.breakdown.to_dict()
        bd["completeness_factor"] = 1.5  # inválido
        with pytest.raises(ValidationError):
            ScoreBreakdownSchema.model_validate(bd)
