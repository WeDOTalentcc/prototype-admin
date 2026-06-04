"""Unit tests for the JobCreationSeed canonical schema (Task A1)."""
import pytest
from pydantic import ValidationError

from app.domains.job_creation.schemas import (
    ALWAYS_FRESH_FIELDS,
    FieldProvenance,
    JobCreationSeed,
    SourceDescriptor,
)


def test_seed_rejects_company_id_and_extra():
    with pytest.raises(ValidationError):
        JobCreationSeed(title="Dev", company_id="x")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        JobCreationSeed(title="Dev", ghost="x")  # type: ignore[call-arg]


def test_always_fresh_not_in_schema():
    fields = set(JobCreationSeed.model_fields.keys())
    assert not (ALWAYS_FRESH_FIELDS & fields)
    assert ALWAYS_FRESH_FIELDS == {
        "manager_name",
        "manager_email",
        "headcount",
        "deadline",
        "cost_center",
    }


def test_provenance_key_must_be_real_field():
    p = FieldProvenance(source_type="template", source_id="t", source_name="X")
    with pytest.raises(ValidationError):
        JobCreationSeed(title="Dev", provenance={"sallary_min": p})


def test_provenance_key_real_field_accepted():
    p = FieldProvenance(source_type="template", source_id="t", source_name="X")
    seed = JobCreationSeed(salary_min=1000, provenance={"salary_min": p})
    assert seed.provenance["salary_min"].source_type == "template"


def test_source_descriptor_typed_extra_forbid():
    with pytest.raises(ValidationError):
        SourceDescriptor(type="template", id="1", name="X", junk="y")  # type: ignore[call-arg]


def test_source_type_enum_includes_user_and_derived():
    for st in ("template", "vacancy", "user", "derived"):
        FieldProvenance(source_type=st, source_id="x", source_name="x")


def test_salary_needs_review_flag_roundtrip():
    p = FieldProvenance(
        source_type="template", source_id="t1", source_name="X", needs_review=True
    )
    seed = JobCreationSeed(
        salary_min=12000, salary_max=16000, provenance={"salary_min": p}
    )
    assert seed.provenance["salary_min"].needs_review is True
