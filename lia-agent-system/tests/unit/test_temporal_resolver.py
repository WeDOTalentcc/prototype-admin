"""
Tests for TemporalResolver — LIA-R01
Target: temporal_resolver.py (0% → ~90%)
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')

from datetime import date, timedelta
import pytest


def setup_module(module):
    pass


class TestTemporalGranularity:
    def test_granularity_values(self):
        from app.orchestrator.context.temporal_resolver import TemporalGranularity
        assert TemporalGranularity.DAY == "day"
        assert TemporalGranularity.WEEK == "week"
        assert TemporalGranularity.MONTH == "month"
        assert TemporalGranularity.QUARTER == "quarter"
        assert TemporalGranularity.YEAR == "year"
        assert TemporalGranularity.EXACT == "exact"


class TestTemporalResult:
    def test_as_iso_range(self):
        from app.orchestrator.context.temporal_resolver import TemporalResult, TemporalGranularity
        today = date(2026, 4, 4)
        result = TemporalResult(
            original="hoje",
            resolved_start=today,
            resolved_end=today,
            granularity=TemporalGranularity.DAY,
            confidence=1.0,
        )
        assert result.as_iso_range() == "2026-04-04/2026-04-04"

    def test_as_iso_range_week(self):
        from app.orchestrator.context.temporal_resolver import TemporalResult, TemporalGranularity
        result = TemporalResult(
            original="esta semana",
            resolved_start=date(2026, 3, 30),
            resolved_end=date(2026, 4, 5),
            granularity=TemporalGranularity.WEEK,
            confidence=1.0,
        )
        assert result.as_iso_range() == "2026-03-30/2026-04-05"


class TestTemporalResolverCore:
    def setup_method(self):
        from app.orchestrator.context.temporal_resolver import TemporalResolver
        self.today = date(2026, 4, 4)  # Saturday
        self.resolver = TemporalResolver(reference_date=self.today)

    def test_hoje(self):
        r = self.resolver.resolve("candidatos de hoje")
        assert r is not None
        assert r.resolved_start == self.today
        assert r.resolved_end == self.today
        assert r.confidence == 1.0

    def test_ontem(self):
        r = self.resolver.resolve("relatório de ontem")
        assert r is not None
        assert r.resolved_start == self.today - timedelta(days=1)
        assert r.resolved_end == self.today - timedelta(days=1)

    def test_amanha(self):
        r = self.resolver.resolve("reunião amanhã")
        assert r is not None
        assert r.resolved_start == self.today + timedelta(days=1)

    def test_amanha_sem_acento(self):
        r = self.resolver.resolve("agenda de amanha")
        assert r is not None
        assert r.resolved_start == self.today + timedelta(days=1)

    def test_esta_semana(self):
        r = self.resolver.resolve("esta semana candidatos")
        assert r is not None
        from app.orchestrator.context.temporal_resolver import TemporalGranularity
        assert r.granularity == TemporalGranularity.WEEK

    def test_semana_passada(self):
        r = self.resolver.resolve("candidatos da semana passada")
        assert r is not None
        # Start should be 7+ days before today
        assert r.resolved_start < self.today - timedelta(days=5)

    def test_semana_que_vem(self):
        r = self.resolver.resolve("entrevistas semana que vem")
        assert r is not None
        assert r.resolved_start > self.today

    def test_este_mes(self):
        r = self.resolver.resolve("este mês resultado")
        assert r is not None
        from app.orchestrator.context.temporal_resolver import TemporalGranularity
        assert r.granularity == TemporalGranularity.MONTH
        assert r.resolved_start.day == 1
        assert r.resolved_start.month == self.today.month

    def test_esse_mes(self):
        r = self.resolver.resolve("candidatos esse mês")
        assert r is not None
        assert r.resolved_start.month == self.today.month

    def test_mes_passado(self):
        r = self.resolver.resolve("vagas do mês passado")
        assert r is not None
        assert r.resolved_start.month != self.today.month

    def test_ultimos_7_dias(self):
        r = self.resolver.resolve("últimos 7 dias")
        assert r is not None
        assert r.resolved_start == self.today - timedelta(days=7)
        assert r.resolved_end == self.today

    def test_ultimos_30_dias(self):
        r = self.resolver.resolve("últimos 30 dias")
        assert r is not None
        assert r.resolved_start == self.today - timedelta(days=30)

    def test_generic_n_dias(self):
        r = self.resolver.resolve("últimos 14 dias")
        assert r is not None
        assert r.resolved_start == self.today - timedelta(days=14)
        assert r.confidence == 0.9

    def test_generic_n_days_english(self):
        r = self.resolver.resolve("last 7 days performance")
        assert r is not None

    def test_iso_date_range(self):
        r = self.resolver.resolve("período 2026-01-01 a 2026-01-31")
        assert r is not None
        assert r.resolved_start == date(2026, 1, 1)
        assert r.resolved_end == date(2026, 1, 31)
        from app.orchestrator.context.temporal_resolver import TemporalGranularity
        assert r.granularity == TemporalGranularity.EXACT
        assert r.confidence == 1.0

    def test_single_iso_date(self):
        r = self.resolver.resolve("entrevista em 2026-03-15")
        assert r is not None
        assert r.resolved_start == date(2026, 3, 15)
        assert r.resolved_end == date(2026, 3, 15)

    def test_no_temporal_expression(self):
        r = self.resolver.resolve("candidatos Python sênior")
        assert r is None

    def test_empty_string(self):
        r = self.resolver.resolve("")
        assert r is None

    def test_today_english(self):
        r = self.resolver.resolve("today's briefing")
        assert r is not None
        assert r.resolved_start == self.today

    def test_last_week_english(self):
        r = self.resolver.resolve("last week report")
        assert r is not None
        assert r.resolved_start < self.today - timedelta(days=5)


class TestResolveAll:
    def setup_method(self):
        from app.orchestrator.context.temporal_resolver import TemporalResolver
        self.today = date(2026, 4, 4)
        self.resolver = TemporalResolver(reference_date=self.today)

    def test_resolve_all_no_expressions(self):
        results = self.resolver.resolve_all("candidatos Python")
        assert results == []

    def test_resolve_all_single(self):
        results = self.resolver.resolve_all("candidatos de hoje")
        assert len(results) == 1

    def test_inject_date_context_no_match(self):
        text = "busca de candidatos Python"
        result = self.resolver.inject_date_context(text)
        assert result == text

    def test_inject_date_context_with_match(self):
        text = "candidatos de hoje disponíveis"
        result = self.resolver.inject_date_context(text)
        assert "hoje" in result
        assert "[" in result  # date range injected
        assert "2026-04-04" in result


class TestTemporalResolverNoRef:
    def test_default_reference_is_today(self):
        from app.orchestrator.context.temporal_resolver import TemporalResolver
        resolver = TemporalResolver()
        today = date.today()
        r = resolver.resolve("hoje")
        assert r is not None
        assert r.resolved_start == today

    def test_december_month_end(self):
        from app.orchestrator.context.temporal_resolver import TemporalResolver
        resolver = TemporalResolver(reference_date=date(2026, 12, 15))
        r = resolver.resolve("este mês")
        assert r is not None
        assert r.resolved_end == date(2026, 12, 31)
