"""Testes Sprint IV — Observabilidade e Compliance."""
import pytest
from unittest.mock import AsyncMock, patch


class TestAgentMetrics:
    def test_module_importable(self):
        from app.shared.observability.agent_metrics import (
            record_agent_request,
            record_fairness_block,
            record_hitl_trigger,
            record_tokens,
            record_confidence,
            agent_latency_timer,
        )
        assert record_agent_request is not None

    def test_record_functions_are_noop_without_prometheus(self):
        from app.shared.observability.agent_metrics import record_agent_request
        # Não deve levantar exceção
        record_agent_request("test_agent", "test_domain", "success")

    @pytest.mark.asyncio
    async def test_latency_timer_context_manager(self):
        from app.shared.observability.agent_metrics import agent_latency_timer
        async with agent_latency_timer("test_agent", "test_domain"):
            pass  # não deve levantar exceção


class TestGoldenDataset:
    def test_seeder_importable(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        assert generate_golden_dataset is not None

    def test_generates_100_candidates(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        candidates = generate_golden_dataset()
        assert len(candidates) == 100

    def test_gender_balance(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        candidates = generate_golden_dataset()
        males = sum(1 for c in candidates if c["gender"] == "M")
        females = sum(1 for c in candidates if c["gender"] == "F")
        assert males == 50
        assert females == 50

    def test_pcd_representation(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        candidates = generate_golden_dataset()
        pcds = sum(1 for c in candidates if c["disability"])
        assert pcds == 10

    def test_all_candidates_have_required_fields(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        required = {"id", "name", "gender", "birth_date", "region", "disability", "lia_score"}
        candidates = generate_golden_dataset()
        for c in candidates:
            for field in required:
                assert field in c, f"Candidato sem campo {field}"

    def test_lia_scores_in_valid_range(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        candidates = generate_golden_dataset()
        for c in candidates:
            assert 0 <= c["lia_score"] <= 100


class TestRAGASGoldenQueries:
    def test_golden_queries_importable(self):
        from tests.ragas.golden_queries import GOLDEN_QUERIES
        assert len(GOLDEN_QUERIES) == 5

    def test_all_critical_flows_covered(self):
        from tests.ragas.golden_queries import GOLDEN_QUERIES
        assert "wsi_scoring" in GOLDEN_QUERIES
        assert "cv_matching" in GOLDEN_QUERIES
        assert "salary_benchmark" in GOLDEN_QUERIES
