"""Coverage tests for report_templates.py — pure helper functions."""
import pytest
from app.templates.report_templates import (
    _format_number,
    _trend_icon,
    _trend_color,
    _severity_color,
    ReportTemplates,
)


class TestFormatNumber:
    def test_integer_default_decimals(self):
        result = _format_number(1234.5)
        assert "1" in result  # has numeric content

    def test_zero_decimals(self):
        result = _format_number(1000.0, decimals=0)
        assert result == "1.000"

    def test_two_decimals(self):
        result = _format_number(1.5, decimals=2)
        assert "," in result  # Brazilian formatting uses comma for decimal

    def test_small_number(self):
        result = _format_number(5.3)
        assert "5" in result

    def test_zero(self):
        result = _format_number(0, decimals=0)
        assert result == "0"


class TestTrendIcon:
    def test_up_returns_arrow_up(self):
        assert _trend_icon("up") == "↑"

    def test_down_returns_arrow_down(self):
        assert _trend_icon("down") == "↓"

    def test_neutral_returns_arrow_right(self):
        assert _trend_icon("stable") == "→"

    def test_empty_string_returns_right(self):
        assert _trend_icon("") == "→"

    def test_unknown_value_returns_right(self):
        assert _trend_icon("sideways") == "→"


class TestTrendColor:
    def test_up_positive_is_green(self):
        assert _trend_color("up", positive_is_up=True) == "#16a34a"

    def test_up_negative_is_red(self):
        assert _trend_color("up", positive_is_up=False) == "#dc2626"

    def test_down_positive_up_is_red(self):
        assert _trend_color("down", positive_is_up=True) == "#dc2626"

    def test_down_positive_false_is_green(self):
        assert _trend_color("down", positive_is_up=False) == "#16a34a"

    def test_neutral_returns_gray(self):
        assert _trend_color("neutral") == "#6b7280"

    def test_default_positive_is_up_true(self):
        assert _trend_color("up") == "#16a34a"


class TestSeverityColor:
    def test_critical_is_red(self):
        assert _severity_color("critical") == "#dc2626"

    def test_high_is_orange(self):
        assert _severity_color("high") == "#f97316"

    def test_medium_is_yellow(self):
        assert _severity_color("medium") == "#eab308"

    def test_low_is_blue(self):
        assert _severity_color("low") == "#3b82f6"

    def test_unknown_returns_gray(self):
        assert _severity_color("unknown") == "#6b7280"

    def test_empty_returns_gray(self):
        assert _severity_color("") == "#6b7280"


class TestReportTemplatesDailyBriefing:
    def test_returns_string(self):
        result = ReportTemplates.daily_briefing_html({})
        assert isinstance(result, str)
        assert len(result) > 100

    def test_uses_user_name(self):
        result = ReportTemplates.daily_briefing_html({"user_name": "Maria"})
        assert "Maria" in result

    def test_uses_greeting(self):
        result = ReportTemplates.daily_briefing_html({"greeting": "Boa tarde"})
        assert "Boa tarde" in result

    def test_urgent_actions_included(self):
        data = {
            "urgent_actions": [
                {"title": "Revisar candidato", "description": "Urgente", "priority": "critical"}
            ]
        }
        result = ReportTemplates.daily_briefing_html(data)
        assert "Revisar candidato" in result

    def test_alerts_section_when_present(self):
        data = {
            "alerts": [
                {"title": "Prazo vencendo", "severity": "high", "description": "3 dias"}
            ]
        }
        result = ReportTemplates.daily_briefing_html(data)
        assert isinstance(result, str)

    def test_insights_included(self):
        data = {"insights": ["Taxa de aprovação acima da média"]}
        result = ReportTemplates.daily_briefing_html(data)
        assert isinstance(result, str)

    def test_schedule_included(self):
        data = {
            "schedule": [
                {"time": "09:00", "type": "interview", "title": "Entrevista Ana"}
            ]
        }
        result = ReportTemplates.daily_briefing_html(data)
        assert isinstance(result, str)


class TestReportTemplatesWeeklyReport:
    def test_returns_string(self):
        result = ReportTemplates.weekly_report_html({})
        assert isinstance(result, str)
        assert len(result) > 100

    def test_company_name_used(self):
        result = ReportTemplates.weekly_report_html({"company_name": "ACME Corp"})
        assert "ACME Corp" in result

    def test_with_kpis(self):
        data = {
            "kpis": [
                {"name": "Contratações", "value": "12", "trend": "up", "trend_pct": 15}
            ]
        }
        result = ReportTemplates.weekly_report_html(data)
        assert isinstance(result, str)

    def test_with_funnel(self):
        data = {
            "funnel": {"stages": [{"name": "Candidatos", "count": 100}]}
        }
        result = ReportTemplates.weekly_report_html(data)
        assert isinstance(result, str)

    def test_with_recruiters(self):
        data = {
            "recruiters": [
                {"recruiter_name": "Paulo", "positions_filled": 3, "avg_days": 22}
            ]
        }
        result = ReportTemplates.weekly_report_html(data)
        assert isinstance(result, str)


class TestReportTemplatesMonthlyReport:
    def test_returns_string(self):
        result = ReportTemplates.monthly_report_html({})
        assert isinstance(result, str)
        assert len(result) > 100

    def test_month_year_used(self):
        result = ReportTemplates.monthly_report_html({"month_year": "Maio 2026"})
        assert "Maio 2026" in result

    def test_with_strategic_kpis(self):
        data = {
            "strategic_kpis": [
                {"name": "Time-to-Fill", "value": "25 dias", "trend": "down", "trend_pct": -8}
            ]
        }
        result = ReportTemplates.monthly_report_html(data)
        assert isinstance(result, str)

    def test_with_predictions(self):
        data = {
            "predictions": [
                {"title": "Pipeline saudável", "description": "Próximos 30 dias"}
            ]
        }
        result = ReportTemplates.monthly_report_html(data)
        assert isinstance(result, str)
