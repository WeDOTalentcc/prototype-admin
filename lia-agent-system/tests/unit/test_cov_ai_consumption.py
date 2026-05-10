"""Coverage tests for app/schemas/ai_consumption.py — enums and Pydantic models."""
import pytest
from app.schemas.ai_consumption import (
    AgentTypeEnum,
    ModelEnum,
    AiConsumptionRecord,
    AiConsumptionListResponse,
    UsageSummaryResponse,
    UsageByAgentResponse,
    UsageByAgentListResponse,
    AgentDailyTrendResponse,
    AgentDailyTrendListResponse,
    UsageByModelResponse,
    UsageByDayResponse,
    UsageByDayListResponse,
    BalanceResponse,
    UpdateLimitsRequest,
)
from datetime import date


class TestAgentTypeEnum:
    def test_has_values(self):
        values = list(AgentTypeEnum)
        assert len(values) > 0

    def test_are_strings(self):
        for v in AgentTypeEnum:
            assert isinstance(v.value, str)


class TestModelEnum:
    def test_has_values(self):
        values = list(ModelEnum)
        assert len(values) > 0

    def test_are_strings(self):
        for v in ModelEnum:
            assert isinstance(v.value, str)


class TestAiConsumptionRecord:
    def test_basic(self):
        agent_type = list(AgentTypeEnum)[0]
        m = AiConsumptionRecord(
            agent_type=agent_type,
            operation="screen_candidate",
            model=list(ModelEnum)[0],
        )
        assert m.operation == "screen_candidate"
        assert m.input_tokens == 0  # default
        assert m.output_tokens == 0  # default

    def test_with_tokens(self):
        m = AiConsumptionRecord(
            agent_type=list(AgentTypeEnum)[0],
            operation="generate_questions",
            model=list(ModelEnum)[0],
            input_tokens=1500,
            output_tokens=800,
            cost_cents=5,
        )
        assert m.input_tokens == 1500
        assert m.output_tokens == 800
        assert m.cost_cents == 5

    def test_optional_fields(self):
        m = AiConsumptionRecord(
            agent_type=list(AgentTypeEnum)[0],
            operation="chat",
            model=list(ModelEnum)[0],
            candidate_id="cand-001",
            vacancy_id="vac-002",
            user_id="user-003",
        )
        assert m.candidate_id == "cand-001"
        assert m.vacancy_id == "vac-002"
        assert m.user_id == "user-003"

    def test_metadata_default(self):
        m = AiConsumptionRecord(
            agent_type=list(AgentTypeEnum)[0],
            operation="analysis",
            model=list(ModelEnum)[0],
        )
        assert m.metadata is not None  # has default_factory=dict


class TestUsageSummaryResponse:
    def test_basic(self):
        m = UsageSummaryResponse(
            company_id="co-001",
            period_start="2024-01-01",
            period_end="2024-01-31",
            total_tokens=50000,
            total_input_tokens=30000,
            total_output_tokens=20000,
            total_cost_cents=250,
            total_operations=100,
            monthly_limit=1000000,
            usage_percentage=5.0,
            remaining_tokens=950000,
            overage_allowed=False,
        )
        assert m.company_id == "co-001"
        assert m.total_tokens == 50000
        assert m.usage_percentage == pytest.approx(5.0)
        assert m.remaining_tokens == 950000
        assert m.overage_allowed is False


class TestUsageByAgentResponse:
    def test_basic(self):
        m = UsageByAgentResponse(
            agent_type="screening_agent",
            total_tokens=10000,
            total_cost_cents=50,
            total_operations=25,
            percentage_of_total=15.5,
        )
        assert m.agent_type == "screening_agent"
        assert m.total_operations == 25
        assert m.percentage_of_total == pytest.approx(15.5)


class TestUsageByAgentListResponse:
    def test_empty(self):
        m = UsageByAgentListResponse(data=[], total_tokens=0, total_operations=0)
        assert m.data == []

    def test_with_agents(self):
        agent = UsageByAgentResponse(
            agent_type="chat_agent", total_tokens=5000,
            total_cost_cents=25, total_operations=10,
            percentage_of_total=10.0,
        )
        m = UsageByAgentListResponse(
            data=[agent],
            total_tokens=5000,
            total_operations=10,
        )
        assert len(m.data) == 1


class TestAgentDailyTrendResponse:
    def test_basic(self):
        m = AgentDailyTrendResponse(
            date="2024-05-10",
            agent_type="screening_agent",
            total_tokens=3000,
            total_cost_cents=15,
            total_operations=8,
        )
        assert m.date == "2024-05-10"
        assert m.total_tokens == 3000
        assert m.total_operations == 8


class TestAgentDailyTrendListResponse:
    def test_empty(self):
        m = AgentDailyTrendListResponse(data=[], total_days=0)
        assert m.data == []
        assert m.total_days == 0

    def test_with_data(self):
        trend = AgentDailyTrendResponse(
            date="2024-05-01", agent_type="chat",
            total_tokens=100, total_cost_cents=1, total_operations=2,
        )
        m = AgentDailyTrendListResponse(data=[trend], total_days=1)
        assert len(m.data) == 1


class TestUsageByModelResponse:
    def test_basic(self):
        m = UsageByModelResponse(
            model="claude-3-sonnet",
            total_tokens=20000,
            total_cost_cents=100,
            total_operations=40,
            percentage_of_total=40.0,
        )
        assert m.model == "claude-3-sonnet"
        assert m.total_cost_cents == 100
        assert m.percentage_of_total == pytest.approx(40.0)


class TestUsageByDayResponse:
    def test_basic(self):
        m = UsageByDayResponse(
            date="2024-05-01",
            total_tokens=8000,
            total_cost_cents=40,
            total_operations=20,
        )
        assert m.date == "2024-05-01"
        assert m.total_operations == 20


class TestUsageByDayListResponse:
    def test_empty(self):
        m = UsageByDayListResponse(data=[], total_tokens=0, total_days=0)
        assert m.data == []
        assert m.total_days == 0

    def test_with_items(self):
        day = UsageByDayResponse(
            date="2024-05-01", total_tokens=100, total_cost_cents=1, total_operations=2,
        )
        m = UsageByDayListResponse(data=[day], total_tokens=100, total_days=1)
        assert len(m.data) == 1


class TestBalanceResponse:
    def test_basic(self):
        m = BalanceResponse(
            id="bal-001",
            company_id="co-001",
            monthly_limit=1000000,
            current_usage=50000,
            period_start="2024-05-01",
            period_end="2024-05-31",
            overage_allowed=False,
            overage_rate_cents=0,
            usage_percentage=5.0,
            remaining_tokens=950000,
        )
        assert m.id == "bal-001"
        assert m.overage_allowed is False
        assert m.remaining_tokens == 950000

    def test_with_overage(self):
        m = BalanceResponse(
            id="bal-002",
            company_id="co-002",
            monthly_limit=500000,
            current_usage=480000,
            period_start="2024-05-01",
            period_end="2024-05-31",
            overage_allowed=True,
            overage_rate_cents=2,
            usage_percentage=96.0,
            remaining_tokens=20000,
        )
        assert m.overage_allowed is True
        assert m.overage_rate_cents == 2


class TestUpdateLimitsRequest:
    def test_all_optional(self):
        m = UpdateLimitsRequest()
        assert m.monthly_limit is None
        assert m.overage_allowed is None
        assert m.reset_usage is False  # default

    def test_set_limits(self):
        m = UpdateLimitsRequest(
            monthly_limit=2000000,
            overage_allowed=True,
            overage_rate_cents=1,
            reset_usage=True,
        )
        assert m.monthly_limit == 2000000
        assert m.overage_allowed is True
        assert m.reset_usage is True
