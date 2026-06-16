"""
2.1: Normalização de escala WSI — helper canônico wsi_score_to_lia_scale.

Garante que a conversão 0-10 → 0-100 é explícita e testada,
eliminando magic number × 10 inline.
"""
import pytest


class TestWsiScaleCanonical:
    """wsi_score_to_lia_scale: contrato de conversão 0-10 → 0-100."""

    def test_helper_exists_in_wsi_scale(self):
        """wsi_score_to_lia_scale deve existir em wsi_scale.py."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert callable(wsi_score_to_lia_scale), "deve ser callable"

    def test_typical_approved_score(self):
        """7.5 (aprovado auto em 0-10) → 75.0 (0-100)."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(7.5) == 75.0

    def test_neutral_score(self):
        """5.0 (neutro) → 50.0."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(5.0) == 50.0

    def test_maximum_score(self):
        """10.0 → 100.0."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(10.0) == 100.0

    def test_minimum_valid_score(self):
        """2.0 (SCALE_MIN_VALID) → 20.0."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(2.0) == 20.0

    def test_zero_score(self):
        """0.0 → 0.0 (não levanta exceção)."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(0.0) == 0.0

    def test_rounding_precision(self):
        """Score com decimal → arredondado para 1 casa."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(8.55) == 85.5

    def test_clamped_at_100(self):
        """Score > 10 é clamped a 100.0 (nunca retorna > 100)."""
        from app.domains.cv_screening.constants.wsi_scale import wsi_score_to_lia_scale
        assert wsi_score_to_lia_scale(12.0) == 100.0

    def test_completion_uses_canonical_helper(self):
        """completion.py P0-1 deve importar wsi_score_to_lia_scale (não magic ×10 inline)."""
        import ast, os
        path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "app", "domains", "recruitment", "services",
            "triagem_session_service", "completion.py",
        )
        path = os.path.abspath(path)
        with open(path) as f:
            source = f.read()
        assert "wsi_score_to_lia_scale" in source, (
            "completion.py deve usar wsi_score_to_lia_scale do wsi_scale.py, "
            "não magic number × 10.0 inline"
        )

    def test_scale_chain_constants_coherent(self):
        """SCALE_MAX (10) × NORMALIZATION_TO_LIA (10) == 100 — invariante de escala."""
        from app.domains.cv_screening.constants import wsi_scale
        max_lia = wsi_scale.wsi_score_to_lia_scale(wsi_scale.SCALE_MAX)
        assert max_lia == 100.0, (
            f"SCALE_MAX ({wsi_scale.SCALE_MAX}) convertido deve dar 100.0, deu {max_lia}"
        )
