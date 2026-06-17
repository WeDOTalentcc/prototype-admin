"""5.0: Quality-adaptive K — trunca resultados no joelho da curva de similaridade."""
import pytest


class TestAdaptiveK:
    """Pure function: adaptive_k(scores, max_k, min_quality) -> int."""

    def test_function_exists(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        assert callable(adaptive_k)

    def test_empty_scores_returns_zero(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        assert adaptive_k([], max_k=10) == 0

    def test_all_high_scores_returns_all(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        scores = [0.95, 0.90, 0.85, 0.80]
        assert adaptive_k(scores, max_k=10) == 4

    def test_steep_dropoff_truncates(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        scores = [0.90, 0.85, 0.20, 0.10]  # drop below 0.30 * 0.90 = 0.27
        result = adaptive_k(scores, max_k=10, min_quality=0.3)
        assert result == 2  # only first 2 survive

    def test_top_score_below_threshold_returns_zero(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        scores = [0.15, 0.10, 0.05]
        assert adaptive_k(scores, max_k=10, min_quality=0.3) == 0

    def test_respects_max_k(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        scores = [0.95, 0.90, 0.85, 0.80, 0.75]
        assert adaptive_k(scores, max_k=3) == 3

    def test_single_score_above_threshold(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        assert adaptive_k([0.80], max_k=10) == 1

    def test_max_k_zero_returns_zero(self):
        from app.domains.ai.services.candidate_embedding_service import adaptive_k
        assert adaptive_k([0.95], max_k=0) == 0
