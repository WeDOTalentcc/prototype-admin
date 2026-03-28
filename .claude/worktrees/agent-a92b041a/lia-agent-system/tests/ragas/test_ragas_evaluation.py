"""
RAGAS Evaluation — avalia qualidade das respostas dos agentes LIA.
Roda no CI com continue-on-error=true.
"""
import pytest
from tests.ragas.golden_queries import GOLDEN_QUERIES


class TestRAGASGoldenQueries:
    """Verifica que golden queries têm estrutura válida."""

    def test_all_flows_present(self):
        expected_flows = {"wsi_scoring", "cv_matching", "salary_benchmark",
                          "pipeline_analysis", "candidate_search"}
        assert expected_flows.issubset(set(GOLDEN_QUERIES.keys()))

    def test_each_query_has_required_fields(self):
        for flow, queries in GOLDEN_QUERIES.items():
            assert len(queries) >= 1, f"Fluxo {flow} sem queries"
            for q in queries:
                assert "query" in q, f"Query de {flow} sem campo 'query'"
                assert "expected_tools" in q, f"Query de {flow} sem expected_tools"
                assert "expected_output_keywords" in q, f"Query de {flow} sem expected_output_keywords"

    def test_expected_tools_are_lists(self):
        for flow, queries in GOLDEN_QUERIES.items():
            for q in queries:
                assert isinstance(q["expected_tools"], list)
                assert len(q["expected_tools"]) >= 1

    def test_keywords_are_non_empty(self):
        for flow, queries in GOLDEN_QUERIES.items():
            for q in queries:
                assert len(q["expected_output_keywords"]) >= 3, \
                    f"Query de {flow} com poucos keywords esperados"
