"""
Billing models for subscription management.

Supports Iugu and Vindi as payment gateway providers.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Boolean, Integer, ForeignKey, Index, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from typing import Dict, Any, Optional

from lia_config.database import Base


class SubscriptionStatus(str, enum.Enum):
    """Status of a subscription."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PENDING = "pending"
    SUSPENDED = "suspended"


class InvoiceStatus(str, enum.Enum):
    """Status of an invoice."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethodType(str, enum.Enum):
    """Types of payment methods."""
    CREDIT_CARD = "credit_card"
    BOLETO = "boleto"
    PIX = "pix"
    BANK_TRANSFER = "bank_transfer"


class BillingProvider(str, enum.Enum):
    """Supported billing providers."""
    IUGU = "iugu"
    VINDI = "vindi"


class Subscription(Base):
    """
    Subscription model.
    
    Represents a client's subscription to a plan, managed through Iugu or Vindi.
    """
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    external_customer_id = Column(String(255), nullable=True)
    
    plan_code = Column(String(100), nullable=False, index=True)
    plan_name = Column(String(255), nullable=True)
    
    status = Column(String(50), default=SubscriptionStatus.PENDING.value, index=True)
    
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    price_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(10), default="BRL")
    
    billing_cycle = Column(String(20), default="monthly")
    billing_day = Column(Integer, nullable=True)
    
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # ALFA discount — admin-only, per-company. Zero impact when desconto_pct=0.
    desconto_pct = Column(Numeric(precision=5, scale=2), nullable=False, default=0)
    desconto_validade = Column(DateTime, nullable=True)
    
    extra_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    invoices = relationship("Invoice", back_populates="subscription", lazy="dynamic")
    payment_methods = relationship("PaymentMethod", back_populates="subscription", lazy="dynamic")
    
    __table_args__ = (
        Index('idx_subscription_client_status', 'client_id', 'status'),
        Index('idx_subscription_provider_external', 'provider', 'external_id'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<Subscription {self.id} - {self.plan_code} ({self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "provider": self.provider,
            "external_id": self.external_id,
            "external_customer_id": self.external_customer_id,
            "plan_code": self.plan_code,
            "plan_name": self.plan_name,
            "status": self.status,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "price_cents": self.price_cents,
            "currency": self.currency,
            "billing_cycle": self.billing_cycle,
            "billing_day": self.billing_day,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_reason": self.cancellation_reason,
            "desconto_pct": float(self.desconto_pct) if self.desconto_pct else 0,
            "desconto_validade": self.desconto_validade.isoformat() if self.desconto_validade else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]
    
    @property
    def is_past_due(self) -> bool:
        """Check if subscription has overdue payments."""
        return self.status == SubscriptionStatus.PAST_DUE.value


class Invoice(Base):
    """
    Invoice model.
    
    Represents a billing invoice for a subscription.
    """
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    external_id = Column(String(255), nullable=True, index=True)
    provider = Column(String(50), nullable=False)
    
    status = Column(String(50), default=InvoiceStatus.PENDING.value, index=True)
    
    amount_cents = Column(Integer, nullable=False, default=0)
    discount_cents = Column(Integer, default=0)
    total_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(10), default="BRL")
    
    due_date = Column(Date, nullable=True, index=True)
    paid_at = Column(DateTime, nullable=True)
    
    invoice_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    boleto_url = Column(String(500), nullable=True)
    boleto_barcode = Column(String(100), nullable=True)
    pix_qrcode = Column(Text, nullable=True)
    pix_qrcode_url = Column(String(500), nullable=True)
    
    payment_method = Column(String(50), nullable=True)
    
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    extra_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="invoices")
    
    __table_args__ = (
        Index('idx_invoice_client_status', 'client_id', 'status'),
        Index('idx_invoice_due_date_status', 'due_date', 'status'),
        Index('idx_invoice_provider_external', 'provider', 'external_id'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<Invoice {self.id} - R${self.total_cents/100:.2f} ({self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id),
            "client_id": str(self.client_id),
            "external_id": self.external_id,
            "provider": self.provider,
            "status": self.status,
            "amount_cents": self.amount_cents,
            "discount_cents": self.discount_cents,
            "total_cents": self.total_cents,
            "currency": self.currency,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "invoice_url": self.invoice_url,
            "pdf_url": self.pdf_url,
            "boleto_url": self.boleto_url,
            "boleto_barcode": self.boleto_barcode,
            "pix_qrcode": self.pix_qrcode,
            "pix_qrcode_url": self.pix_qrcode_url,
            "payment_method": self.payment_method,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.PAID.value
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status != InvoiceStatus.PENDING.value:
            return False
        if not self.due_date:
            return False
        return date.today() > self.due_date


class PaymentMethod(Base):
    """
    PaymentMethod model.
    
    Represents a saved payment method for a subscription.
    """
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    
    external_id = Column(String(255), nullable=True, index=True)
    provider = Column(String(50), nullable=False)
    
    type = Column(String(50), nullable=False)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    card_brand = Column(String(50), nullable=True)
    card_last_digits = Column(String(4), nullable=True)
    card_holder_name = Column(String(255), nullable=True)
    card_expiry_month = Column(Integer, nullable=True)
    card_expiry_year = Column(Integer, nullable=True)
    
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    # ── LGPD Art. 46 — CPF/CNPJ (LGPD Art. 5 II "dado pessoal") ────────────
    # billing_document_legacy: plaintext column kept temporarily for
    # backward-compat during the 169 migration backfill window. New writes
    # MUST go to billing_document_encrypted via PaymentMethodRepository.
    # Use the `billing_document` hybrid property to read/write — it routes
    # to the encrypted column and raises on plaintext-only reads.
    billing_document_legacy = Column(
        "billing_document", String(20), nullable=True
    )
    billing_document_encrypted = Column(Text, nullable=True)
    billing_phone = Column(String(50), nullable=True)

    extra_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="payment_methods")
    
    __table_args__ = (
        Index('idx_payment_method_client', 'client_id', 'is_active'),
        Index('idx_payment_method_subscription', 'subscription_id', 'is_default'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<PaymentMethod {self.id} - {self.type}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id),
            "client_id": str(self.client_id),
            "external_id": self.external_id,
            "provider": self.provider,
            "type": self.type,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "card_brand": self.card_brand,
            "card_last_digits": self.card_last_digits,
            "card_holder_name": self.card_holder_name,
            "card_expiry_month": self.card_expiry_month,
            "card_expiry_year": self.card_expiry_year,
            "billing_name": self.billing_name,
            "billing_email": self.billing_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def display_name(self) -> str:
        """Get a display name for this payment method."""
        if self.type == PaymentMethodType.CREDIT_CARD.value:
            brand = self.card_brand or "Card"
            return f"{brand} •••• {self.card_last_digits}"
        return self.type.replace("_", " ").title()

    def get_billing_document(self) -> str | None:
        """Decrypted CPF/CNPJ. Wave 4 LGPD canonical accessor.

        Reads from ``billing_document_encrypted`` (Fernet). For rows still
        on the legacy plaintext column (pre migration 169 backfill), reads
        from ``billing_document_legacy`` and emits a WARN log so ops can
        spot un-migrated rows.

        Raises:
            PIIEncryptionError: ciphertext corruption / key rotation.
        """
        from app.shared.services.pii_crypto import decrypt_pii
        if self.billing_document_encrypted:
            return decrypt_pii(self.billing_document_encrypted)
        if self.billing_document_legacy:
            # Should be zero rows after migration 169 backfill completes.
            import logging
            logging.getLogger(__name__).warning(
                "PaymentMethod %s read legacy plaintext billing_document; "
                "run migration 169 backfill",
                self.id,
            )
            return self.billing_document_legacy
        return None

    def set_billing_document(self, value: str | None) -> None:
        """Set CPF/CNPJ — writes to encrypted column ONLY.

        NEVER writes to ``billing_document_legacy`` directly. Sensor
        ``check_no_plaintext_pii.py`` enforces this at AST level.
        """
        from app.shared.services.pii_crypto import encrypt_pii
        self.billing_document_encrypted = encrypt_pii(value)
        # Defense-in-depth: clear legacy column on every write so partial
        # migrations cannot leave stale plaintext.
        self.billing_document_legacy = None


class CreditTransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    CONSUMPTION = "consumption"
    REFUND = "refund"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"
    APIFY_ENRICHMENT = "apify_enrichment"
    PEARCH_SEARCH = "pearch_search"
    SUBSCRIPTION_GRANT = "subscription_grant"
    EXPIRATION = "expiration"


class CreditAccount(Base):
    """Credit balance per company for metered features (global search, AI analysis, etc.)."""
    __tablename__ = "credit_accounts"
    __table_args__ = (
        Index("ix_credit_accounts_company", "company_id", unique=True),
    {"extend_existing": True}, )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(100), nullable=False, unique=True, index=True)
    plan_type = Column(String(50), nullable=False, default="free")
    balance = Column(Integer, nullable=False, default=0)
    lifetime_purchased = Column(Integer, nullable=False, default=0)
    lifetime_consumed = Column(Integer, nullable=False, default=0)
    lifetime_bonus = Column(Integer, nullable=False, default=0)
    low_balance_threshold = Column(Integer, nullable=False, default=20)
    reset_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "plan_type": self.plan_type,
            "balance": self.balance,
            "lifetime_purchased": self.lifetime_purchased,
            "lifetime_consumed": self.lifetime_consumed,
            "lifetime_bonus": self.lifetime_bonus,
            "low_balance_threshold": self.low_balance_threshold,
            "reset_date": self.reset_date.isoformat() if self.reset_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CreditTransaction(Base):
    """Immutable ledger of credit movements (purchases, consumption, refunds, bonuses)."""
    __tablename__ = "credit_transactions"
    __table_args__ = (
        Index("ix_credit_tx_company_created", "company_id", "created_at"),
    {"extend_existing": True}, )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(100), nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False, index=True)
    action_type = Column(String(50), nullable=True, index=True)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(String(100), nullable=True)
    performed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "transaction_type": self.transaction_type,
            "action_type": self.action_type,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "description": self.description,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "performed_by": self.performed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModuleStatus(str, enum.Enum):
    BETA = "beta"
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    COMING_SOON = "coming_soon"


class ModuleTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


AVAILABLE_MODULES = {
    "talent_intelligence_pro": {
        "label": "Talent Intelligence Pro",
        "description": "Skills Ontology + Gap Analysis + Market Intelligence",
        "initial_status": "beta",
    },
    "internal_mobility": {
        "label": "Internal Mobility Suite",
        "description": "Matching interno + Readiness scoring",
        "initial_status": "beta",
    },
    "interview_intelligence": {
        "label": "Interview Intelligence Pro",
        "description": "Análise WSI de entrevista + viés + parecer",
        "initial_status": "beta",
    },
    "workforce_planning": {
        "label": "Workforce Planning",
        "description": "Previsão + cenários + dashboard",
        "initial_status": "beta",
    },
    "candidate_nurture": {
        "label": "Candidate Nurture / CRM",
        "description": "Sequências + engajamento + CRM",
        "initial_status": "beta",
    },
    "onboarding_suite": {
        "label": "Onboarding Intelligence",
        "description": "Workflow pós-contratação completo",
        "initial_status": "coming_soon",
    },
    "predictive_analytics": {
        "label": "Predictive Attrition",
        "description": "Previsão de risco de turnover com ML",
        "initial_status": "beta",
    },
}


class CompanyModule(Base):
    """Tracks which monetizable modules are enabled per company.

    company_id uses String(100) to match the CreditAccount pattern (billing domain
    uses tenant string IDs, not UUID FKs to company_profiles). The credit_account
    relationship provides the billing integration bridge for future paid-module flows.
    """
    __tablename__ = "company_modules"
    __table_args__ = (
        Index("ix_company_modules_company", "company_id"),
        Index("ix_company_modules_company_module", "company_id", "module_name", unique=True),
    {"extend_existing": True}, )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(100), ForeignKey("credit_accounts.company_id"), nullable=False)
    module_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default=ModuleStatus.BETA.value)
    tier = Column(String(20), nullable=False, default=ModuleTier.FREE.value)
    activated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    credit_account = relationship(
        "CreditAccount",
        primaryjoin="CompanyModule.company_id == CreditAccount.company_id",
        foreign_keys=[company_id],
        uselist=False,
        viewonly=True,
        lazy="noload",
    )

    def to_dict(self) -> Dict[str, Any]:
        meta = self.metadata_json if isinstance(self.metadata_json, dict) else {}
        module_info = AVAILABLE_MODULES.get(self.module_name, {})
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "module_name": self.module_name,
            "label": module_info.get("label", self.module_name),
            "description": module_info.get("description", ""),
            "status": self.status,
            "tier": self.tier,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_accessible(self) -> bool:
        if self.status in (ModuleStatus.BETA.value, ModuleStatus.ACTIVE.value, ModuleStatus.TRIAL.value):
            if self.expires_at and self.expires_at < datetime.utcnow():
                return False
            return True
        return False


MODULE_STATUS_OPTIONS = [
    {"value": ModuleStatus.BETA.value, "label": "BETA", "description": "Acesso gratuito durante período beta"},
    {"value": ModuleStatus.TRIAL.value, "label": "Trial", "description": "Período de avaliação"},
    {"value": ModuleStatus.ACTIVE.value, "label": "Ativo", "description": "Módulo ativo e pago"},
    {"value": ModuleStatus.EXPIRED.value, "label": "Expirado", "description": "Período expirado"},
    {"value": ModuleStatus.DISABLED.value, "label": "Desabilitado", "description": "Módulo desativado"},
    {"value": ModuleStatus.COMING_SOON.value, "label": "Em Breve", "description": "Módulo em desenvolvimento"},
]


SUBSCRIPTION_STATUS_OPTIONS = [
    {"value": SubscriptionStatus.ACTIVE.value, "label": "Ativa", "description": "Assinatura em dia"},
    {"value": SubscriptionStatus.TRIALING.value, "label": "Em Trial", "description": "Período de teste"},
    {"value": SubscriptionStatus.PAST_DUE.value, "label": "Pagamento Atrasado", "description": "Fatura em atraso"},
    {"value": SubscriptionStatus.CANCELLED.value, "label": "Cancelada", "description": "Assinatura cancelada"},
    {"value": SubscriptionStatus.PENDING.value, "label": "Pendente", "description": "Aguardando ativação"},
    {"value": SubscriptionStatus.SUSPENDED.value, "label": "Suspensa", "description": "Temporariamente suspensa"},
]

INVOICE_STATUS_OPTIONS = [
    {"value": InvoiceStatus.PENDING.value, "label": "Pendente", "description": "Aguardando pagamento"},
    {"value": InvoiceStatus.PAID.value, "label": "Paga", "description": "Pagamento confirmado"},
    {"value": InvoiceStatus.FAILED.value, "label": "Falhou", "description": "Pagamento falhou"},
    {"value": InvoiceStatus.REFUNDED.value, "label": "Reembolsada", "description": "Valor devolvido"},
    {"value": InvoiceStatus.CANCELLED.value, "label": "Cancelada", "description": "Fatura cancelada"},
    {"value": InvoiceStatus.EXPIRED.value, "label": "Expirada", "description": "Prazo expirado"},
]

PAYMENT_METHOD_OPTIONS = [
    {"value": PaymentMethodType.CREDIT_CARD.value, "label": "Cartão de Crédito"},
    {"value": PaymentMethodType.BOLETO.value, "label": "Boleto Bancário"},
    {"value": PaymentMethodType.PIX.value, "label": "PIX"},
    {"value": PaymentMethodType.BANK_TRANSFER.value, "label": "Transferência Bancária"},
]
