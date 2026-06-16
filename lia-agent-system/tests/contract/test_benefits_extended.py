"""
Testes do modulo de beneficios expandido.
P2 Audit 2026-05-24: filiais, validade, historico.
"""
import uuid
from datetime import date
import pytest


def test_benefit_history_model_exists():
    """CompanyBenefitHistory model importa sem erro."""
    from libs.models.lia_models.company_benefit import CompanyBenefitHistory
    assert CompanyBenefitHistory.__tablename__ == "company_benefit_history"


def test_company_benefit_new_columns_exist():
    """CompanyBenefit tem todos os novos campos da migration 191."""
    from libs.models.lia_models.company_benefit import CompanyBenefit
    cols = {c.name for c in CompanyBenefit.__table__.columns}
    required = {"subsidiaries", "valid_from", "valid_until", "review_frequency_months", "next_review_date", "provider_cnpj"}
    missing = required - cols
    assert not missing, f"Campos faltando no modelo: {missing}"


def test_benefit_history_columns_exist():
    """CompanyBenefitHistory tem todos os campos esperados."""
    from libs.models.lia_models.company_benefit import CompanyBenefitHistory
    cols = {c.name for c in CompanyBenefitHistory.__table__.columns}
    required = {"id", "benefit_id", "company_id", "changed_at", "changed_by", "change_type", "previous_snapshot", "change_notes"}
    missing = required - cols
    assert not missing, f"Campos faltando em CompanyBenefitHistory: {missing}"


def test_subsidiary_entry_schema():
    """SubsidiaryEntry valida campos name e cnpj."""
    import sys, importlib.util
    sys.path.insert(0, ".")
    spec = importlib.util.spec_from_file_location("cb_api", "app/api/v1/company_benefits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    SubsidiaryEntry = mod.SubsidiaryEntry
    entry = SubsidiaryEntry(name="Filial SP")
    assert entry.name == "Filial SP"
    assert entry.cnpj is None
    entry2 = SubsidiaryEntry(name="Filial RJ", cnpj="12345678000190")
    assert entry2.cnpj == "12345678000190"


def test_benefit_create_schema_accepts_new_fields():
    """CompanyBenefitCreate aceita subsidiaries, valid_from, valid_until, provider_cnpj."""
    import sys, importlib.util
    sys.path.insert(0, ".")
    spec = importlib.util.spec_from_file_location("cb_api", "app/api/v1/company_benefits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Create = mod.CompanyBenefitCreate
    Sub = mod.SubsidiaryEntry
    payload = Create(
        name="Plano de Saude",
        description="Cobertura medica",
        value_type="informative",
        provider_cnpj="12345678000190",
        subsidiaries=[Sub(name="Matriz SP"), Sub(name="Filial RJ", cnpj="98765432000100")],
        valid_from=date(2026, 1, 1),
        valid_until=date(2026, 12, 31),
        review_frequency_months=12,
    )
    assert payload.provider_cnpj == "12345678000190"
    assert len(payload.subsidiaries) == 2
    assert payload.valid_from == date(2026, 1, 1)
    assert payload.review_frequency_months == 12


def test_benefit_update_schema_accepts_new_fields():
    """CompanyBenefitUpdate aceita os novos campos da migration 191."""
    import sys, importlib.util
    sys.path.insert(0, ".")
    spec = importlib.util.spec_from_file_location("cb_api", "app/api/v1/company_benefits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Update = mod.CompanyBenefitUpdate
    Sub = mod.SubsidiaryEntry
    upd = Update(
        valid_until=date(2027, 6, 30),
        review_frequency_months=6,
        subsidiaries=[Sub(name="Nova Filial")],
    )
    assert upd.valid_until == date(2027, 6, 30)
    assert upd.review_frequency_months == 6


def test_benefit_response_schema_includes_new_fields():
    """CompanyBenefitResponse tem history, subsidiaries, valid_from, provider_cnpj."""
    import sys, importlib.util
    sys.path.insert(0, ".")
    spec = importlib.util.spec_from_file_location("cb_api", "app/api/v1/company_benefits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Response = mod.CompanyBenefitResponse
    fields = Response.model_fields
    for f in ["history", "subsidiaries", "valid_from", "valid_until", "provider_cnpj", "review_frequency_months"]:
        assert f in fields, f"Field {f} missing from CompanyBenefitResponse"


def test_benefit_history_entry_schema():
    """BenefitHistoryEntry valida campos esperados."""
    import sys, importlib.util
    sys.path.insert(0, ".")
    spec = importlib.util.spec_from_file_location("cb_api", "app/api/v1/company_benefits.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Entry = mod.BenefitHistoryEntry
    entry = Entry(
        id=str(uuid.uuid4()),
        changed_at="2026-05-24T12:00:00",
        changed_by="user@example.com",
        change_type="created",
    )
    assert entry.change_type == "created"
    assert entry.changed_by == "user@example.com"


def test_migration_191_exists():
    """Migration 191 existe e tem revision_id correto."""
    import glob, importlib.util
    files = glob.glob("alembic/versions/191_*.py")
    assert files, "Migration 191 nao encontrada em alembic/versions/"
    spec = importlib.util.spec_from_file_location("m191", files[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "191_company_benefits_extended"
    assert mod.down_revision == "190_suggestion_clicks_feedback_check"
