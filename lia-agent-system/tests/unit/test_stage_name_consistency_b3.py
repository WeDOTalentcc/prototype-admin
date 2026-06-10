"""Tests for B3: stage name consistency between producer and consumers."""


class TestPipelineToolsStageProducer:
    """Test that pipeline/tools/pipeline_tools.py uses Contratado (not hired) for stage."""

    def test_pipeline_tools_uses_contratado_stage(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py"
        content = open(path).read()
        assert 'vc.stage = "Contratado"' in content, (
            'pipeline_tools.py must assign stage="Contratado" (PT-BR display name), not stage="hired"'
        )

    def test_pipeline_tools_does_not_assign_stage_hired(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py"
        content = open(path).read()
        assert 'vc.stage = "hired"' not in content, (
            'pipeline_tools.py still assigns stage="hired" -- fix not applied'
        )

    def test_stage_id_resolver_called_with_contratado(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py"
        content = open(path).read()
        assert ', "Contratado"' in content, (
            'stage_id_resolver must be called with "Contratado", not "hired"'
        )


class TestFinancialTrendsCoversHired:
    """Test that financial_trends.py covers both stage values."""

    def test_financial_trends_uses_in_for_stage_filter(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/analytics_query_tools/financial_trends.py"
        content = open(path).read()
        assert '.in_(["Contratado", "hired"])' in content, (
            'financial_trends.py must use .in_(["Contratado", "hired"]) for stage filter'
        )

    def test_financial_trends_no_plain_equality_for_stage(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/analytics_query_tools/financial_trends.py"
        content = open(path).read()
        assert 'VacancyCandidate.stage == "Contratado"' not in content, (
            "financial_trends.py still uses plain equality -- must use .in_()"
        )


class TestIntelligenceCoversHired:
    """Test that intelligence.py in-memory stage checks cover both values."""

    def test_intelligence_hired_check_covers_both(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/analytics_query_tools/intelligence.py"
        content = open(path).read()
        assert 'stage in ["Contratado", "hired"]' in content, (
            'intelligence.py must check stage in ["Contratado", "hired"]'
        )

    def test_intelligence_no_plain_equality(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/analytics_query_tools/intelligence.py"
        content = open(path).read()
        assert 'stage == "Contratado"' not in content, (
            'intelligence.py still uses plain equality -- must use "in"'
        )

    def test_intelligence_exclusion_lists_include_hired(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/analytics_query_tools/intelligence.py"
        content = open(path).read()
        assert '"Desistente", "hired"]' in content, (
            'intelligence.py terminal stage exclusion lists must include "hired"'
        )


class TestReportServiceCoversHired:
    """Test that report_service.py SQL covers both stage values."""

    def test_report_service_uses_in_for_stage(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/analytics/services/report_service.py"
        content = open(path).read()
        assert "IN ('Contratado', 'hired')" in content, (
            "report_service.py SQL must use IN ('Contratado', 'hired') for stage filter"
        )


class TestAnalyticsActionsCoversHired:
    """Test that analytics_actions.py SQL covers both stage values."""

    def test_analytics_actions_uses_in_for_stage(self):
        path = "/home/runner/workspace/lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py"
        content = open(path).read()
        assert "IN ('Contratado', 'hired')" in content, (
            "analytics_actions.py SQL must use IN ('Contratado', 'hired') for stage filter"
        )


class TestQueryToolsCoversHired:
    """Test that sourcing query_tools.py in_process_stages includes hired."""

    def test_query_tools_in_process_stages_has_hired(self):
        path = "/home/runner/workspace/lia-agent-system/app/domains/sourcing/tools/query_tools.py"
        content = open(path).read()
        assert '"Contratado", "hired"}' in content, (
            'query_tools.py in_process_stages must include both "Contratado" and "hired"'
        )
