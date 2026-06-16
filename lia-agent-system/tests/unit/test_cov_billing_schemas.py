"""Coverage tests for app/schemas/billing.py — enums and Pydantic models."""
import pytest
from app.schemas.billing import (
    SubscriptionStatusEnum,
    InvoiceStatusEnum,
    PaymentMethodTypeEnum,
    BillingProviderEnum,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionCancel,
    SubscriptionResponse,
)


class TestSubscriptionStatusEnum:
    def test_active(self):
        assert SubscriptionStatusEnum.ACTIVE == "active"

    def test_cancelled(self):
        assert SubscriptionStatusEnum.CANCELLED == "cancelled"

    def test_past_due(self):
        assert SubscriptionStatusEnum.PAST_DUE == "past_due"

    def test_trialing(self):
        assert SubscriptionStatusEnum.TRIALING == "trialing"

    def test_pending(self):
        assert SubscriptionStatusEnum.PENDING == "pending"

    def test_suspended(self):
        assert SubscriptionStatusEnum.SUSPENDED == "suspended"


class TestInvoiceStatusEnum:
    def test_has_values(self):
        values = list(InvoiceStatusEnum)
        assert len(values) > 0

    def test_are_strings(self):
        for v in InvoiceStatusEnum:
            assert isinstance(v.value, str)


class TestPaymentMethodTypeEnum:
    def test_has_values(self):
        values = list(PaymentMethodTypeEnum)
        assert len(values) > 0


class TestBillingProviderEnum:
    def test_has_values(self):
        values = list(BillingProviderEnum)
        assert len(values) > 0


class TestSubscriptionCreate:
    def test_basic(self):
        m = SubscriptionCreate(
            client_id="client-001",
            plan_code="starter",
        )
        assert m.client_id == "client-001"
        assert m.plan_code == "starter"

    def test_with_optional(self):
        m = SubscriptionCreate(
            client_id="client-002",
            plan_code="professional",
            trial_days=14,
        )
        assert m.trial_days == 14

    def test_enterprise_plan(self):
        m = SubscriptionCreate(
            client_id="client-enterprise",
            plan_code="enterprise",
            provider=BillingProviderEnum.STRIPE if hasattr(BillingProviderEnum, "STRIPE") else list(BillingProviderEnum)[0],
        )
        assert m.plan_code == "enterprise"


class TestSubscriptionUpdate:
    def test_all_optional(self):
        m = SubscriptionUpdate()
        assert m.plan_code is None
        assert m.status is None

    def test_update_plan(self):
        m = SubscriptionUpdate(plan_code="enterprise")
        assert m.plan_code == "enterprise"

    def test_update_status(self):
        m = SubscriptionUpdate(status=SubscriptionStatusEnum.SUSPENDED)
        assert m.status == "suspended"


class TestSubscriptionCancel:
    def test_basic(self):
        m = SubscriptionCancel()
        # Should have defaults or be empty
        assert m is not None

    def test_with_reason(self):
        m = SubscriptionCancel(
            reason="Too expensive",
            at_period_end=True,
        )
        assert m.reason == "Too expensive"
        assert m.at_period_end is True


class TestSubscriptionResponse:
    def test_basic(self):
        m = SubscriptionResponse(
            id="sub-001",
            client_id="client-001",
            provider=list(BillingProviderEnum)[0].value,
            plan_code="starter",
            status=SubscriptionStatusEnum.ACTIVE.value,
            price_cents=9900,
            billing_cycle="monthly",
        )
        assert m.id == "sub-001"
        assert m.price_cents == 9900
        assert m.billing_cycle == "monthly"

    def test_trialing(self):
        m = SubscriptionResponse(
            id="sub-002",
            client_id="client-002",
            provider=list(BillingProviderEnum)[0].value,
            plan_code="professional",
            status=SubscriptionStatusEnum.TRIALING.value,
            price_cents=19900,
            billing_cycle="annual",
        )
        assert m.status == "trialing"

    def test_optional_fields_none(self):
        m = SubscriptionResponse(
            id="sub-003",
            client_id="client-003",
            provider=list(BillingProviderEnum)[0].value,
            plan_code="starter",
            status=SubscriptionStatusEnum.ACTIVE.value,
            price_cents=9900,
            billing_cycle="monthly",
        )
        assert m.cancelled_at is None
        assert m.trial_end is None
