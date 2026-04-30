"""
Sensor: CompanyBenefit schema 1:1 com Rails canonical.

Audit context (Fase 1 do plano Benefits+PRV, 2026-04-30):
  Antes desta fase, o Pydantic Create persistia somente 8 campos enquanto o
  frontend enviava 14 — os outros 7 eram silenciosamente descartados. O
  contrato Rails canonical (ats-api-copia/db/migrate/20250715000005_create_benefits.rb)
  define 22 colunas; o FastAPI agora espelha 1:1 (+ icon e timestamps = 24).

Estes testes sao estruturais (puros — sem DB), seguindo o padrao do sensor
test_job_vacancy_benefits_schema.py. Garantem:

  T1. Model `CompanyBenefit` (SQLAlchemy) tem as 22 colunas Rails + icon +
      timestamps = 24 colunas total.
  T2. Pydantic `CompanyBenefitCreate` valida condicionalmente por value_type:
        monetary    -> exige value
        percentage  -> exige percentage_value
        informative -> exige value_details ou description
  T3. Pydantic `CompanyBenefitCreate` aceita todos os 20 campos editaveis
      (sem id, company_id, created_at, updated_at).

Fix se falhar:
  - T1: alguem dropou colunas em migration nova; verificar
    libs/models/lia_models/company_benefit.py + alembic versions
    100_extend_company_benefits.py + 101_fix_seniority_levels_type.py.
  - T2: model_validator foi removido ou alterado; verificar
    app/api/v1/company_benefits.py validate_value_by_type.
  - T3: campo foi removido do BaseModel; verificar
    app/api/v1/company_benefits.py CompanyBenefitBase.

Skill canonica: harness-engineering [sensor computacional, fail-loud].

Refs:
- Plan: ~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md (Fase 1.8)
- Commits: 32f212c66 (BE), 403111d5d (FE), 020503492 (propagacao FE)
- Memory: feedback_no_ats_api.md (ats-api-copia readonly; ats_api ignorado)
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from lia_models.company_benefit import CompanyBenefit


# ---------------------------------------------------------------------------
# T1 — Estrutural: model tem 22 cols Rails + icon + timestamps
# ---------------------------------------------------------------------------

# Schema-alvo (Rails canonical, 22 cols) + icon (FastAPI extra) + timestamps.
# Order independente.
EXPECTED_COLS_RAILS_PLUS_ICON = {
    # Rails canonical (22)
    "id",
    "company_id",
    "name",
    "description",
    "category",
    "icon",  # fastapi extra (harmless)
    "value",
    "percentage_value",
    "value_type",
    "value_details",
    "applicable_to",
    "seniority_levels",
    "contract_types",
    "departments",
    "waiting_period_days",
    "is_mandatory",
    "is_active",
    "is_highlighted",
    "is_discount",
    "order",
    "provider",
    "provider_contact",
    # timestamps
    "created_at",
    "updated_at",
}


def test_company_benefit_has_24_canonical_columns():
    actual = {c.name for c in CompanyBenefit.__table__.columns}
    missing = EXPECTED_COLS_RAILS_PLUS_ICON - actual
    extra = actual - EXPECTED_COLS_RAILS_PLUS_ICON
    assert not missing, (
        f"CompanyBenefit perdeu colunas alinhadas ao contrato Rails: {sorted(missing)}. "
        "Verificar se uma migration recente dropou colunas. "
        "Schema-alvo em ats-api-copia/db/migrate/20250715000005_create_benefits.rb."
    )
    assert not extra, (
        f"CompanyBenefit ganhou colunas inesperadas: {sorted(extra)}. "
        "Atualizar este teste se houver expansao intencional do schema."
    )


# ---------------------------------------------------------------------------
# T2 — Pydantic: validacao condicional por value_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label,payload,expect_fail",
    [
        ("monetary sem value", {"name": "X", "value_type": "monetary"}, True),
        ("monetary com value", {"name": "X", "value_type": "monetary", "value": 100.0}, False),
        ("percentage sem percentage_value", {"name": "X", "value_type": "percentage"}, True),
        (
            "percentage com percentage_value",
            {"name": "X", "value_type": "percentage", "percentage_value": 15.0},
            False,
        ),
        ("informative sem details/desc", {"name": "X", "value_type": "informative"}, True),
        (
            "informative com value_details",
            {"name": "X", "value_type": "informative", "value_details": "custeado"},
            False,
        ),
        (
            "informative com description (fallback)",
            {"name": "X", "value_type": "informative", "description": "info"},
            False,
        ),
    ],
)
def test_pydantic_create_validates_value_by_type(label, payload, expect_fail):
    # Importacao tardia: o router carrega o app inteiro como side-effect.
    from app.api.v1.company_benefits import CompanyBenefitCreate

    if expect_fail:
        with pytest.raises(ValidationError):
            CompanyBenefitCreate(**payload)
    else:
        instance = CompanyBenefitCreate(**payload)
        assert instance.name == "X", f"caso '{label}' deveria persistir name"


# ---------------------------------------------------------------------------
# T3 — Pydantic: aceita todos os 20 campos editaveis
# ---------------------------------------------------------------------------

# 20 campos editaveis = 22 colunas Rails - id - company_id (computados/scoped).
# Timestamps tambem nao sao editaveis. icon e extra do FastAPI.
EXPECTED_EDITABLE_FIELDS = {
    "name",
    "category",
    "description",
    "icon",
    "value",
    "percentage_value",
    "value_type",
    "value_details",
    "applicable_to",
    "seniority_levels",
    "contract_types",
    "departments",
    "waiting_period_days",
    "is_mandatory",
    "is_active",
    "is_highlighted",
    "is_discount",
    "order",
    "provider",
    "provider_contact",
}


def test_pydantic_create_exposes_all_20_editable_fields():
    from app.api.v1.company_benefits import CompanyBenefitCreate

    actual = set(CompanyBenefitCreate.model_fields.keys())
    missing = EXPECTED_EDITABLE_FIELDS - actual
    extra = actual - EXPECTED_EDITABLE_FIELDS

    assert not missing, (
        f"CompanyBenefitCreate perdeu campos editaveis: {sorted(missing)}. "
        "Frontend pode silenciosamente perder dados (drift FE/BE)."
    )
    # Extra fields sao tolerados (ex: futuras adicoes), mas avisar:
    if extra:
        pytest.fail(
            f"CompanyBenefitCreate tem campos extras nao listados: {sorted(extra)}. "
            "Atualizar EXPECTED_EDITABLE_FIELDS se for expansao intencional."
        )


def test_pydantic_create_roundtrip_all_20_fields_minimal():
    """Smoke: payload com 20 campos serializa ida-e-volta sem perda."""
    from app.api.v1.company_benefits import CompanyBenefitCreate

    full_payload = {
        "name": "Plano Saude Premium",
        "category": "health",
        "description": "Cobertura nacional",
        "icon": "stethoscope",
        "value_type": "monetary",
        "value": 1200.0,
        "percentage_value": None,
        "value_details": None,
        "applicable_to": ["clt", "pj"],
        "seniority_levels": ["senior", "staff"],
        "contract_types": ["clt"],
        "departments": {"engineering": True},
        "waiting_period_days": 30,
        "is_mandatory": False,
        "is_active": True,
        "is_highlighted": True,
        "is_discount": False,
        "order": 1,
        "provider": "Unimed",
        "provider_contact": "atendimento@unimed.test",
    }
    instance = CompanyBenefitCreate(**full_payload)
    dumped = instance.model_dump(exclude_none=False)
    for k, v in full_payload.items():
        assert dumped[k] == v, f"campo {k!r} divergiu: enviado={v!r} dump={dumped[k]!r}"


# ---------------------------------------------------------------------------
# T4 — Fairness guard (// TODO(FAIRNESS:001)) — non-negotiable rule (CLAUDE.md)
# ---------------------------------------------------------------------------
# Beneficios NAO podem ter elegibilidade por atributo protegido. Sensor
# computacional fail-loud. Alinhado com app/shared/compliance/fairness_guard.py
# e PROHIBITED_ELIGIBILITY_TERMS no router company_benefits.py.


@pytest.mark.parametrize(
    "label,field,values,expect_fail",
    [
        # PT-BR — termos protegidos
        ("genero em applicable_to", "applicable_to", ["homem"], True),
        ("raca em departments", "departments", {"raca": True}, True),
        ("idade em seniority_levels", "seniority_levels", ["jovem"], True),
        ("religiao em contract_types", "contract_types", ["catolico"], True),
        ("estado_civil em applicable_to", "applicable_to", ["solteiro"], True),
        ("saude em applicable_to", "applicable_to", ["deficiencia"], True),
        # EN — termos protegidos
        ("gender EN", "applicable_to", ["male"], True),
        ("age EN", "applicable_to", ["young"], True),
        ("pregnancy EN", "applicable_to", ["pregnancy"], True),
        # OK — termos neutros (cargo, senioridade, contrato, departamento)
        ("clt+pj OK", "applicable_to", ["clt", "pj"], False),
        ("senior+staff OK", "seniority_levels", ["senior", "staff"], False),
        ("clt OK contract", "contract_types", ["clt"], False),
        ("engineering OK dept", "departments", {"engineering": True}, False),
    ],
)
def test_fairness_guard_blocks_protected_attributes(
    label, field, values, expect_fail
):
    """Non-negotiable rule (CLAUDE.md #2 LGPD + #3 Fairness):
    Beneficios nao podem ter elegibilidade por atributo protegido."""
    from app.api.v1.company_benefits import CompanyBenefitCreate

    payload = {
        "name": "X",
        "value_type": "informative",
        "description": "test",
        field: values,
    }
    if expect_fail:
        with pytest.raises(ValidationError) as exc:
            CompanyBenefitCreate(**payload)
        # Mensagem de erro deve ser acionavel (otimizada para LLM)
        msg = str(exc.value)
        assert "discriminatorio" in msg.lower() or "fairness" in msg.lower(), (
            f"caso '{label}' falhou mas mensagem de erro nao explica fairness: {msg}"
        )
    else:
        instance = CompanyBenefitCreate(**payload)
        actual = getattr(instance, field)
        assert actual == values, f"caso '{label}' deveria preservar {field}={values}"
