"""
Sensor: CompensationPolicy schema + fairness guard + versioning.

Contexto (Fase 2 do plano Benefits+PRV, 2026-04-30):
  T1. Model `CompensationPolicy` tem as 26 colunas esperadas (Rails 23 + updated_by + timestamps).
  T2. Pydantic `CompensationPolicyCreate` valida `kind` discriminator em variable_compensation.
  T3. Fairness guard bloqueia elegibilidade por atributo protegido em applicable_*[].
  T4. VARIABLE_COMP_KINDS / VARIABLE_COMP_FREQUENCIES sao completos.

Fix se falhar:
  - T1: migration 102 nao foi aplicada ou model divergiu;
    verificar libs/models/lia_models/compensation_policy.py.
  - T2: validador kind foi removido;
    verificar app/api/v1/company_compensation_policies.py CompensationPolicyCreate.
  - T3: PROHIBITED_ELIGIBILITY_TERMS foi esvaziado ou field_validator removido.
  - T4: constante foi reduzida no model.

Skill canonica: harness-engineering [sensor computacional, fail-loud].

Refs:
- Plan: ~/.claude/plans/vams-conectar-ao-replit-effervescent-fairy.md (Fase 2.9)
- Rails canonical: ats-api-copia/db/migrate/20250715000009 (READ-ONLY)
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# T1 — Estrutural: model tem 26 colunas esperadas
# ---------------------------------------------------------------------------

EXPECTED_COLS = {
    # Rails canonical (23)
    "id", "company_id", "name", "description", "policy_type", "currency",
    "salary_bands", "bonus_structure", "equity_rules", "benefits_package",
    "variable_compensation", "applicable_departments", "applicable_seniority",
    "applicable_roles", "is_active", "is_default", "effective_from",
    "effective_until", "approved_by", "approved_at", "version",
    "revision_history", "created_by",
    # FastAPI extra (auditabilidade)
    "updated_by",
    # timestamps
    "created_at", "updated_at",
}


def test_compensation_policy_has_26_columns():
    from lia_models.compensation_policy import CompensationPolicy

    actual = {c.name for c in CompensationPolicy.__table__.columns}
    missing = EXPECTED_COLS - actual
    extra = actual - EXPECTED_COLS
    assert not missing, (
        f"CompensationPolicy perdeu colunas: {sorted(missing)}. "
        "Verificar migration 102 e libs/models/lia_models/compensation_policy.py."
    )
    assert not extra, (
        f"CompensationPolicy tem colunas inesperadas: {sorted(extra)}. "
        "Atualizar EXPECTED_COLS se for expansao intencional."
    )


# ---------------------------------------------------------------------------
# T2 — Pydantic: kind discriminator em variable_compensation.items
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label,vc,expect_fail",
    [
        (
            "kind valido plr",
            {"items": [{"kind": "plr", "name": "PLR Anual"}]},
            False,
        ),
        (
            "kind valido bonus",
            {"items": [{"kind": "bonus", "name": "Bonus Meta"}]},
            False,
        ),
        (
            "kind invalido",
            {"items": [{"kind": "salario_fixo", "name": "Invalido"}]},
            True,
        ),
        (
            "kind vazio",
            {"items": [{"kind": "", "name": "Sem kind"}]},
            True,
        ),
        (
            "items vazio OK",
            {"items": []},
            False,
        ),
    ],
)
def test_pydantic_validates_variable_compensation_kind(label, vc, expect_fail):
    from app.api.v1.company_compensation_policies import CompensationPolicyCreate

    payload = {"name": "Teste PRV", "variable_compensation": vc}
    if expect_fail:
        with pytest.raises(ValidationError) as exc:
            CompensationPolicyCreate(**payload)
        assert "kind" in str(exc.value).lower() or "invalid" in str(exc.value).lower(), (
            f"caso '{label}' falhou mas mensagem nao menciona kind: {exc.value}"
        )
    else:
        instance = CompensationPolicyCreate(**payload)
        assert instance.name == "Teste PRV"


# ---------------------------------------------------------------------------
# T3 — Fairness guard: applicable_* por atributo protegido e bloqueado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label,field,values,expect_fail",
    [
        # PT-BR — bloqueados
        ("genero em seniority",    "applicable_seniority",   ["homem", "senior"], True),
        ("raca em departments",    "applicable_departments",  ["raca_branca"],     True),
        ("idade em roles",         "applicable_roles",        ["jovem"],           True),
        ("gravidez em seniority",  "applicable_seniority",   ["gestante"],        True),
        # EN — bloqueados
        ("gender EN",              "applicable_seniority",   ["male"],            True),
        ("age EN",                 "applicable_roles",        ["elderly"],         True),
        ("pregnancy EN",           "applicable_seniority",   ["pregnant"],        True),
        # Neutros — OK
        ("senior ok",              "applicable_seniority",   ["senior", "staff"], False),
        ("engineering dept ok",    "applicable_departments",  ["engineering"],     False),
        ("backend role ok",        "applicable_roles",        ["backend-dev"],     False),
        ("vazio ok",               "applicable_seniority",   [],                  False),
    ],
)
def test_prv_fairness_guard(label, field, values, expect_fail):
    """Non-negotiable rule (CLAUDE.md): PRV nao pode ter elegibilidade por atributo protegido."""
    from app.api.v1.company_compensation_policies import CompensationPolicyCreate

    payload = {"name": "Teste PRV Fairness", field: values}
    if expect_fail:
        with pytest.raises(ValidationError) as exc:
            CompensationPolicyCreate(**payload)
        msg = str(exc.value).lower()
        assert "discriminat" in msg or "fairness" in msg or "protegido" in msg, (
            f"caso '{label}' bloqueado mas mensagem nao explica fairness: {exc.value}"
        )
    else:
        instance = CompensationPolicyCreate(**payload)
        actual = getattr(instance, field)
        assert actual == values, f"campo {field} divergiu para '{label}'"


# ---------------------------------------------------------------------------
# T4 — Constantes completas (kind + frequency)
# ---------------------------------------------------------------------------


def test_variable_comp_kinds_complete():
    from lia_models.compensation_policy import VARIABLE_COMP_KINDS

    required = {"plr", "ppr", "bonus", "commission", "spot_bonus", "equity"}
    missing = required - set(VARIABLE_COMP_KINDS)
    assert not missing, f"VARIABLE_COMP_KINDS faltando: {missing}"


def test_variable_comp_frequencies_complete():
    from lia_models.compensation_policy import VARIABLE_COMP_FREQUENCIES

    required = {"monthly", "quarterly", "annual", "biannual", "one_off", "on_target_achievement"}
    missing = required - set(VARIABLE_COMP_FREQUENCIES)
    assert not missing, f"VARIABLE_COMP_FREQUENCIES faltando: {missing}"


# ---------------------------------------------------------------------------
# T5 — DEFAULT_BR_COMPENSATION_TEMPLATES sao validos pelo Pydantic
# ---------------------------------------------------------------------------


def test_default_br_templates_are_valid():
    from lia_models.compensation_policy import DEFAULT_BR_COMPENSATION_TEMPLATES
    from app.api.v1.company_compensation_policies import CompensationPolicyCreate

    for tpl in DEFAULT_BR_COMPENSATION_TEMPLATES:
        try:
            CompensationPolicyCreate(**tpl)
        except ValidationError as e:
            pytest.fail(
                f"Template padrao '{tpl.get('name')}' falhou na validacao Pydantic: {e}"
            )
