"""
Compensation Policy model for salary and bonus management.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class CompensationPolicy(Base):
    """
    Compensation policies defining salary ranges, bonus structures,
    and variable compensation. Schema mirrors Rails migration 102
    (canonical) + FastAPI auditability additions.
    """
    __tablename__ = "compensation_policies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    # ── identity ──────────────────────────────────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)

    # ── classification ────────────────────────────────────────────────────
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(100), nullable=True)        # hierarchical_bands | mixed | flat
    currency = Column(String(10), default="BRL")

    # ── compensation bands (JSON) ─────────────────────────────────────────
    salary_bands = Column(JSON, default=list)               # [{level, min, max}]
    bonus_structure = Column(JSON, default=dict)            # {type, target_pct, ...}
    equity_rules = Column(JSON, default=dict)               # stock/options rules
    benefits_package = Column(JSON, default=dict)           # health, meal, etc.
    variable_compensation = Column(JSON, default=dict)      # {items: [{kind, ...}]}

    # ── applicability ─────────────────────────────────────────────────────
    applicable_departments = Column(JSON, default=list)     # ["Engenharia", ...]
    applicable_seniority = Column(JSON, default=list)       # ["junior", "pleno", ...]
    applicable_roles = Column(JSON, default=list)           # ["Backend Engineer", ...]

    # ── lifecycle ─────────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)

    # ── governance ────────────────────────────────────────────────────────
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    revision_history = Column(JSON, default=list)           # [{version, changed_by, at, diff}]
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    # ── timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("CompanyProfile", back_populates="compensation_policies")


# ---------------------------------------------------------------------------
# Variable compensation enumerations
# ---------------------------------------------------------------------------

VARIABLE_COMP_KINDS: list[str] = [
    "plr", "ppr", "bonus", "commission", "spot_bonus", "equity"
]

VARIABLE_COMP_FREQUENCIES: list[str] = [
    "monthly", "quarterly", "annual", "biannual", "one_off", "on_target_achievement"
]


# ---------------------------------------------------------------------------
# Default Brazilian compensation policy templates
# ---------------------------------------------------------------------------

DEFAULT_BR_COMPENSATION_TEMPLATES: list[dict] = [
    {
        "name": "Política Padrão — Engenharia",
        "policy_type": "hierarchical_bands",
        "currency": "BRL",
        "applicable_departments": ["Engenharia", "Tecnologia"],
        "applicable_seniority": ["junior", "pleno", "senior"],
        "salary_bands": [
            {"level": "junior", "min": 4000, "max": 7000},
            {"level": "pleno", "min": 7000, "max": 12000},
            {"level": "senior", "min": 12000, "max": 20000},
        ],
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Política Padrão — Comercial",
        "policy_type": "mixed",
        "currency": "BRL",
        "applicable_departments": ["Vendas", "Comercial"],
        "applicable_seniority": ["junior", "pleno", "senior"],
        "salary_bands": [
            {"level": "junior", "min": 2500, "max": 4000},
            {"level": "pleno", "min": 4000, "max": 8000},
            {"level": "senior", "min": 8000, "max": 15000},
        ],
        "variable_compensation": {
            "items": [{"kind": "commission", "percentage": 5.0, "frequency": "monthly"}]
        },
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Política Padrão — Produto",
        "policy_type": "hierarchical_bands",
        "currency": "BRL",
        "applicable_departments": ["Produto"],
        "applicable_seniority": ["pleno", "senior"],
        "salary_bands": [
            {"level": "pleno", "min": 8000, "max": 14000},
            {"level": "senior", "min": 14000, "max": 22000},
        ],
        "is_active": True,
        "is_default": True,
    },
]
