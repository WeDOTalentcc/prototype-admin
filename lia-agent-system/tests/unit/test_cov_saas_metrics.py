"""Coverage tests for app/schemas/saas_metrics.py — Pydantic models."""
import pytest
from datetime import date, datetime
from app.schemas.saas_metrics import (
    ChurnAnalysis,
    ClientAllMetricsResponse,
    ClientHealthMetricsBase,
    ClientHealthMetricsCreate,
    ClientHealthMetricsResponse,
    ClientMetrics,
    ClientMetricsList,
    ClientSaasMetricsBase,
    ClientSaasMetricsCreate,
    ClientSaasMetricsResponse,
    ClientUsageMetricsBase,
    ClientUsageMetricsCreate,
    ClientUsageMetricsResponse,
    HealthMetricsUpdate,
    MetricsTrend,
    MetricsTrendResponse,
    PaymentHistoryBase,
    PaymentHistoryCreate,
    PaymentHistoryListResponse,
    PaymentHistoryResponse,
    PlatformAggregateMetrics,
    PlatformMetricsSummary,
    RevenueAnalysis,
    RevenueBreakdown,
    SaasMetricsUpdate,
    UsageMetricsUpdate,
)

_DATE = date(2024, 6, 1)
_DATE_STR = "2024-06-01"


class TestChurnAnalysis:
    def test_basic(self):
        m = ChurnAnalysis(
            current_month_churned=5,
            previous_month_churned=3,
            churn_rate=0.02,
            at_risk_clients=12,
        )
        assert m.current_month_churned == 5
        assert m.churn_rate == pytest.approx(0.02)
        assert m.at_risk_clients == 12

    def test_no_churn(self):
        m = ChurnAnalysis(
            current_month_churned=0,
            previous_month_churned=0,
            churn_rate=0.0,
            at_risk_clients=2,
        )
        assert m.churn_rate == pytest.approx(0.0)


class TestClientHealthMetricsBase:
    def test_empty(self):
        m = ClientHealthMetricsBase()
        assert m is not None

    def test_with_values(self):
        m = ClientHealthMetricsBase(
            health_score=85.0,
            nps_score=42.0,
            feature_adoption_rate=0.75,
            logins_last_30_days=20,
            engagement_level="high",
        )
        assert m.health_score == pytest.approx(85.0)
        assert m.logins_last_30_days == 20


class TestClientHealthMetricsCreate:
    def test_basic(self):
        m = ClientHealthMetricsCreate(client_id="client-001")
        assert m.client_id == "client-001"

    def test_with_score(self):
        m = ClientHealthMetricsCreate(client_id="client-002", health_score=90.0)
        assert m.health_score == pytest.approx(90.0)


class TestClientHealthMetricsResponse:
    def test_basic(self):
        m = ClientHealthMetricsResponse(id="hr-001", client_id="client-001")
        assert m.id == "hr-001"
        assert m.client_id == "client-001"


class TestClientMetrics:
    def test_basic(self):
        m = ClientMetrics(
            client_id="client-001",
            client_name="Acme Corp",
            status="active",
        )
        assert m.client_id == "client-001"
        assert m.client_name == "Acme Corp"
        assert m.status == "active"

    def test_with_metrics(self):
        m = ClientMetrics(
            client_id="client-002",
            client_name="TechCo",
            status="trial",
            mrr=9900.0,
            health_score=75.0,
        )
        assert m.mrr == pytest.approx(9900.0)
        assert m.health_score == pytest.approx(75.0)


class TestClientMetricsList:
    def test_empty(self):
        m = ClientMetricsList(clients=[], total=0, limit=20, offset=0)
        assert m.clients == []
        assert m.total == 0

    def test_with_items(self):
        client = ClientMetrics(
            client_id="c1", client_name="Co", status="active"
        )
        m = ClientMetricsList(clients=[client], total=1, limit=10, offset=0)
        assert m.total == 1


class TestClientSaasMetricsBase:
    def test_empty(self):
        m = ClientSaasMetricsBase()
        assert m is not None

    def test_with_values(self):
        m = ClientSaasMetricsBase(
            mrr=9900.0,
            arr=118800.0,
            plan_name="Starter",
            billing_cycle="monthly",
        )
        assert m.mrr == pytest.approx(9900.0)
        assert m.plan_name == "Starter"


class TestClientSaasMetricsCreate:
    def test_basic(self):
        m = ClientSaasMetricsCreate(client_id="client-001")
        assert m.client_id == "client-001"


class TestClientSaasMetricsResponse:
    def test_basic(self):
        m = ClientSaasMetricsResponse(id="sr-001", client_id="client-001")
        assert m.id == "sr-001"
        assert m.client_id == "client-001"


class TestClientUsageMetricsBase:
    def test_empty(self):
        m = ClientUsageMetricsBase()
        assert m is not None

    def test_with_values(self):
        m = ClientUsageMetricsBase(
            users_active=50,
            users_limit=100,
            jobs_active=30,
            ai_credits_used=1500,
        )
        assert m.users_active == 50
        assert m.ai_credits_used == 1500


class TestClientUsageMetricsCreate:
    def test_basic(self):
        m = ClientUsageMetricsCreate(client_id="client-001")
        assert m.client_id == "client-001"


class TestClientUsageMetricsResponse:
    def test_basic(self):
        m = ClientUsageMetricsResponse(id="ur-001", client_id="client-001")
        assert m.id == "ur-001"


class TestHealthMetricsUpdate:
    def test_empty(self):
        m = HealthMetricsUpdate()
        assert m is not None

    def test_update(self):
        m = HealthMetricsUpdate(health_score=92.0, nps_score=50.0)
        assert m.health_score == pytest.approx(92.0)


class TestMetricsTrend:
    def test_basic(self):
        m = MetricsTrend(date=_DATE_STR, value=9900.0)
        assert m.date == _DATE_STR
        assert m.value == pytest.approx(9900.0)

    def test_another(self):
        m = MetricsTrend(date="2024-07-01", value=10500.0)
        assert m.value == pytest.approx(10500.0)


class TestMetricsTrendResponse:
    def test_basic(self):
        trend = MetricsTrend(date=_DATE_STR, value=9900.0)
        m = MetricsTrendResponse(
            metric_name="mrr",
            period_start="2024-01-01",
            period_end="2024-12-31",
            data_points=[trend],
            total_change=600.0,
            percentage_change=0.06,
        )
        assert m.metric_name == "mrr"
        assert m.total_change == pytest.approx(600.0)
        assert len(m.data_points) == 1


class TestPaymentHistoryBase:
    def test_basic(self):
        m = PaymentHistoryBase(payment_date=_DATE, amount=9900.0)
        assert m.payment_date == _DATE
        assert m.amount == pytest.approx(9900.0)


class TestPaymentHistoryCreate:
    def test_basic(self):
        m = PaymentHistoryCreate(
            payment_date=_DATE,
            amount=9900.0,
            client_id="client-001",
        )
        assert m.client_id == "client-001"
        assert m.amount == pytest.approx(9900.0)


class TestPaymentHistoryResponse:
    def test_basic(self):
        m = PaymentHistoryResponse(
            payment_date=_DATE,
            amount=9900.0,
            id="pay-001",
            client_id="client-001",
        )
        assert m.id == "pay-001"
        assert m.amount == pytest.approx(9900.0)


class TestPaymentHistoryListResponse:
    def test_empty(self):
        m = PaymentHistoryListResponse(payments=[], total=0, limit=20, offset=0)
        assert m.payments == []


class TestPlatformAggregateMetrics:
    def test_empty(self):
        m = PlatformAggregateMetrics()
        assert m is not None

    def test_with_values(self):
        m = PlatformAggregateMetrics(
            total_clients=100,
            active_clients=85,
            total_mrr=990000.0,
            churn_rate=0.02,
        )
        assert m.total_clients == 100
        assert m.churn_rate == pytest.approx(0.02)


class TestPlatformMetricsSummary:
    def test_empty(self):
        m = PlatformMetricsSummary()
        assert m is not None

    def test_with_values(self):
        m = PlatformMetricsSummary(
            total_clients=150,
            arr=15000000.0,
            avg_health_score=82.5,
        )
        assert m.total_clients == 150


class TestRevenueBreakdown:
    def test_basic(self):
        m = RevenueBreakdown(
            category="starter",
            revenue=50000.0,
            percentage=0.25,
            client_count=25,
        )
        assert m.category == "starter"
        assert m.revenue == pytest.approx(50000.0)
        assert m.percentage == pytest.approx(0.25)
        assert m.client_count == 25


class TestRevenueAnalysis:
    def test_basic(self):
        bd1 = RevenueBreakdown(category="enterprise", revenue=120000.0, percentage=0.6, client_count=10)
        bd2 = RevenueBreakdown(category="medium", revenue=80000.0, percentage=0.4, client_count=20)
        m = RevenueAnalysis(
            total_mrr=200000.0,
            total_arr=2400000.0,
            by_plan=[bd1],
            by_company_size=[bd2],
            growth_rate=0.15,
        )
        assert m.total_mrr == pytest.approx(200000.0)
        assert m.growth_rate == pytest.approx(0.15)
        assert len(m.by_plan) == 1


class TestSaasMetricsUpdate:
    def test_empty(self):
        m = SaasMetricsUpdate()
        assert m is not None

    def test_update(self):
        m = SaasMetricsUpdate(mrr=10000.0, arr=120000.0)
        assert m.mrr == pytest.approx(10000.0)


class TestUsageMetricsUpdate:
    def test_empty(self):
        m = UsageMetricsUpdate()
        assert m is not None

    def test_update(self):
        m = UsageMetricsUpdate(users_active=60, jobs_active=35)
        assert m.users_active == 60


class TestClientAllMetricsResponse:
    def test_empty(self):
        m = ClientAllMetricsResponse()
        assert m is not None

    def test_with_metrics(self):
        saas = ClientSaasMetricsResponse(id="sr-001", client_id="client-001", mrr=9900.0)
        usage = ClientUsageMetricsResponse(id="ur-001", client_id="client-001", users_active=50)
        health = ClientHealthMetricsResponse(id="hr-001", client_id="client-001", health_score=85.0)
        m = ClientAllMetricsResponse(revenue=saas, usage=usage, health=health)
        assert m.revenue.client_id == "client-001"
        assert m.health.health_score == pytest.approx(85.0)
