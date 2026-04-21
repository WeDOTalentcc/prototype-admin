"""Task #765 — regression tests for the JobVacancy.benefits JSONB
migration and the Pydantic / endpoint normalization that surrounds it.

Covers:
* ``normalize_benefits_payload`` accepts mixed string + dict input and
  always emits the canonical dict shape (string → minimal object,
  unknown ``value_type`` clamped to ``informative``, anonymous entries
  dropped).
* ``benefit_display_names`` returns a flat list for downstream
  consumers that still want strings (notifications, embeddings).
* ``JobVacancyCreate`` / ``JobVacancyUpdate`` / ``JobVacancyResponse``
  schemas accept both legacy strings and the structured dict shape.
* The model column is declared as JSONB so the ARRAY(String)
  regression cannot reappear without a failing test.
* The Alembic migration's upgrade SQL converts the ARRAY(String)
  column to JSONB while backfilling each name into a structured
  object (with company_benefits join when available), and the
  downgrade preserves the names.
"""
from pathlib import Path

import pytest

from sqlalchemy.dialects.postgresql import JSONB

from app.api.v1.job_vacancies._shared import (
    JobVacancyCreate,
    JobVacancyResponse,
    JobVacancyUpdate,
)
from app.utils.benefits import benefit_display_names, normalize_benefits_payload
from lia_models.job_vacancy import JobVacancy


# ─── normalize_benefits_payload ───────────────────────────────────────


def test_normalize_benefits_payload_handles_legacy_strings():
    out = normalize_benefits_payload(["VR", "  VT ", ""])
    assert out == [
        {"name": "VR", "category": None, "value_type": "informative"},
        {"name": "VT", "category": None, "value_type": "informative"},
    ]


def test_normalize_benefits_payload_preserves_full_structured_dict():
    structured = [
        {
            "id": "b-1",
            "name": "Plano de Saúde Premium",
            "description": "Unimed Nacional",
            "category": "health",
            "value_type": "monetary",
            "value": 800,
            "provider": "Unimed",
            "is_highlighted": True,
            "is_mandatory": True,
            "is_active": True,
            "is_discount": False,
            "seniority_levels": ["all"],
            "waiting_period_days": 30,
            "percentage_value": None,
            "value_details": None,
        }
    ]
    out = normalize_benefits_payload(structured)
    assert len(out) == 1
    assert out[0]["category"] == "health"
    assert out[0]["value_type"] == "monetary"
    assert out[0]["value"] == 800
    assert out[0]["provider"] == "Unimed"
    assert out[0]["is_highlighted"] is True
    assert out[0]["is_mandatory"] is True


def test_normalize_benefits_payload_clamps_invalid_value_type():
    out = normalize_benefits_payload([{"name": "Gympass", "value_type": "bogus"}])
    assert out == [{"name": "Gympass", "value_type": "informative"}]


def test_normalize_benefits_payload_drops_anonymous_entries():
    out = normalize_benefits_payload([{"value": 100}, None, "", "  "])
    assert out == []


def test_normalize_benefits_payload_accepts_mixed_input():
    out = normalize_benefits_payload(
        ["VR", {"name": "VT", "category": "transport", "value_type": "monetary", "value": 500}]
    )
    assert out[0] == {"name": "VR", "category": None, "value_type": "informative"}
    assert out[1]["name"] == "VT"
    assert out[1]["category"] == "transport"
    assert out[1]["value"] == 500


def test_normalize_benefits_payload_handles_none_and_empty():
    assert normalize_benefits_payload(None) == []
    assert normalize_benefits_payload([]) == []


# ─── benefit_display_names ────────────────────────────────────────────


def test_benefit_display_names_extracts_from_dicts_and_strings():
    out = benefit_display_names([
        "VR",
        {"name": "Plano de Saúde", "category": "health"},
        {"category": "food"},  # no name → dropped
        {"name": "  "},        # blank name → dropped
        None,
    ])
    assert out == ["VR", "Plano de Saúde"]


def test_benefit_display_names_handles_empty():
    assert benefit_display_names(None) == []
    assert benefit_display_names([]) == []


# ─── Pydantic schema contracts ────────────────────────────────────────


def test_create_schema_accepts_legacy_string_benefits():
    payload = JobVacancyCreate(title="QA", benefits=["VR", "VT"])
    assert payload.benefits == ["VR", "VT"]


def test_create_schema_accepts_structured_dict_benefits():
    structured = [
        {"name": "Plano", "category": "health", "value_type": "monetary", "value": 500}
    ]
    payload = JobVacancyCreate(title="QA", benefits=structured)
    assert payload.benefits == structured


def test_update_schema_accepts_mixed_benefits():
    payload = JobVacancyUpdate(
        benefits=["VR", {"name": "VT", "category": "transport", "value_type": "monetary"}]
    )
    assert isinstance(payload.benefits, list)
    assert payload.benefits[0] == "VR"
    assert payload.benefits[1]["name"] == "VT"


def test_response_schema_round_trips_structured_benefits():
    structured = [
        {
            "name": "Plano de Saúde",
            "category": "health",
            "value_type": "monetary",
            "value": 800,
            "is_highlighted": True,
            "is_mandatory": True,
            "provider": "Unimed",
        }
    ]
    resp = JobVacancyResponse(id="abc", title="QA", benefits=structured)
    assert resp.benefits == structured


def test_response_schema_accepts_legacy_strings_for_unmigrated_rows():
    """Defensive: a fresh dev DB created via Base.metadata.create_all
    before alembic 100_* runs may still hold ARRAY(String). The
    response schema must not 422 on those rows."""
    resp = JobVacancyResponse(id="abc", title="QA", benefits=["VR", "VT"])
    assert resp.benefits == ["VR", "VT"]


# ─── Model contract guard ─────────────────────────────────────────────


def test_job_vacancy_benefits_column_is_jsonb():
    """Guardrail — if anyone tries to revert this column back to
    ARRAY(String), this test fails. The wizard's structured payloads
    cannot survive that regression (see audit
    docs/audits/beneficios-departamentos-workforce-audit-2026-04.md)."""
    column = JobVacancy.__table__.columns["benefits"]
    assert isinstance(column.type, JSONB), (
        f"Expected JobVacancy.benefits to be JSONB, got {column.type!r}. "
        "Reverting this column to ARRAY(String) drops every structured "
        "field (category, value_type, provider, is_highlighted, ...)."
    )


# ─── Alembic migration 100_* — SQL semantics ──────────────────────────

MIGRATION_PATH = Path(__file__).resolve().parents[2] / (
    "alembic/versions/100_job_vacancy_benefits_jsonb.py"
)


@pytest.fixture(scope="module")
def migration_source() -> str:
    assert MIGRATION_PATH.exists(), f"Migration file missing: {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text()


def test_migration_revision_metadata(migration_source: str):
    assert 'revision = "100_job_vacancy_benefits_jsonb"' in migration_source
    assert 'down_revision = "099_extend_company_benefits_schema"' in migration_source


def test_migration_upgrade_converts_array_to_jsonb(migration_source: str):
    """The upgrade must materialise the column as JSONB. Postgres
    forbids subqueries in ALTER … USING so the migration uses the
    canonical add-new / backfill / drop / rename pattern."""
    assert "ALTER TABLE job_vacancies" in migration_source
    assert "ADD COLUMN benefits_new JSONB" in migration_source
    assert "DROP COLUMN benefits" in migration_source
    assert "RENAME COLUMN benefits_new TO benefits" in migration_source


def test_migration_upgrade_is_idempotent(migration_source: str):
    """Re-running the upgrade on an already-migrated DB must be a no-op."""
    # Detects current column type and returns when already jsonb / json.
    assert 'udt_name' in migration_source
    assert 'if udt in ("jsonb", "json"):' in migration_source


def test_migration_upgrade_backfills_with_company_benefits_join(
    migration_source: str,
):
    """Each existing string element must be turned into a structured
    object. When company_benefits has a matching row, the richer
    schema (category, value_type, provider, is_highlighted,
    is_mandatory) must be copied over."""
    # Joins on lower(name) within the same tenant
    assert "lower(cb.name) = lower(name_elem)" in migration_source
    assert "cb.company_id = job_vacancies.company_id" in migration_source
    # Copies the structured fields the wizard depends on
    for field in (
        "'category'",
        "'value_type'",
        "'provider'",
        "'is_highlighted'",
        "'is_mandatory'",
        "'value'",
        "'percentage_value'",
    ):
        assert field in migration_source, f"Backfill drops {field!r}"


def test_migration_upgrade_has_fallback_when_no_company_benefit_match(
    migration_source: str,
):
    """When no company_benefits row exists for the name, the element
    must still be turned into a minimal object (so reads do not 500)."""
    assert "'value_type', 'informative'" in migration_source
    # Fallback path emits {name, category: NULL, value_type: 'informative'}
    assert "'name', name_elem" in migration_source


def test_migration_upgrade_handles_missing_company_benefits_table(
    migration_source: str,
):
    """Very old envs may not have company_benefits yet — the migration
    must still succeed using the minimal shape."""
    assert 'has_company_benefits = "company_benefits" in inspector.get_table_names()' in migration_source


def test_migration_upgrade_preserves_element_order(migration_source: str):
    """Backfill must preserve the original array order."""
    assert "WITH ORDINALITY" in migration_source
    assert "ORDER BY ord" in migration_source


def test_migration_downgrade_preserves_names(migration_source: str):
    """Downgrade is intentionally lossy on structured fields, but it
    must keep the names so reads after a rollback don't go blank.
    Uses the same add-new / backfill / drop / rename pattern as
    the upgrade because Postgres forbids subqueries in ALTER … USING."""
    assert "ADD COLUMN benefits_old TEXT[]" in migration_source
    assert "RENAME COLUMN benefits_old TO benefits" in migration_source
    assert "elem->>'name'" in migration_source


def test_migration_sets_jsonb_default(migration_source: str):
    """New rows after the migration default to an empty JSONB array,
    not NULL — keeps the existing `or []` read paths happy."""
    assert "SET DEFAULT '[]'::jsonb" in migration_source


# ─── Alembic migration 100_* — real-DB roundtrip ──────────────────────
#
# These tests run the migration's ALTER TABLE SQL against a temporary
# schema seeded with TEXT[] rows, then assert that the resulting JSONB
# column carries the structured shape (with company_benefits join when
# available, fallback minimal shape otherwise). The temp schema is
# wrapped in a transaction and dropped on rollback so it never touches
# real data.

import os
import re
import sqlalchemy as sa


def _can_connect_to_postgres() -> bool:
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith(("postgres://", "postgresql://", "postgresql+psycopg")):
        return False
    try:
        sync_url = url.replace("+asyncpg", "+psycopg2").replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
        engine = sa.create_engine(sync_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


pytestmark_db = pytest.mark.skipif(
    not _can_connect_to_postgres(),
    reason="No reachable Postgres in DATABASE_URL — skipping live migration roundtrip",
)


def _import_migration_module():
    """Import the alembic migration module so the test exercises the
    *exact* backfill SQL constants production will run."""
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "alembic" / "versions" / "100_job_vacancy_benefits_jsonb.py"
    spec = importlib.util.spec_from_file_location("migration_100", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytestmark_db
def test_migration_array_to_jsonb_roundtrip_with_company_benefit_match():
    """Seed a TEXT[] benefits column with a name that matches a
    company_benefits row, replay the migration's add-new / backfill /
    drop / rename pattern, and assert the JSONB inherits category /
    value_type / provider / is_highlighted / is_mandatory from the
    matched row."""
    mod = _import_migration_module()
    backfill_select = mod.BACKFILL_SELECT_WITH_COMPANY_BENEFITS

    sync_url = os.getenv("DATABASE_URL", "").replace(
        "+asyncpg", "+psycopg2"
    ).replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = sa.create_engine(sync_url)
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(sa.text("CREATE SCHEMA tsk765_test"))
                conn.execute(sa.text("SET search_path TO tsk765_test"))
                # Minimal mirrors of the production tables.
                conn.execute(sa.text("""
                    CREATE TABLE company_benefits (
                        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                        company_id uuid NOT NULL,
                        name text NOT NULL,
                        description text,
                        category text,
                        value_type text,
                        value numeric,
                        percentage_value numeric,
                        value_details text,
                        provider text,
                        seniority_levels jsonb,
                        waiting_period_days integer,
                        is_mandatory boolean,
                        is_active boolean,
                        is_highlighted boolean,
                        is_discount boolean
                    )
                """))
                conn.execute(sa.text("""
                    CREATE TABLE job_vacancies (
                        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                        company_id uuid NOT NULL,
                        benefits text[]
                    )
                """))
                # Seed company catalogue + a vacancy referencing it by name.
                conn.execute(sa.text("""
                    INSERT INTO company_benefits
                        (company_id, name, category, value_type, value,
                         provider, is_highlighted, is_mandatory, is_active)
                    VALUES
                        ('11111111-1111-1111-1111-111111111111',
                         'Plano de Saúde', 'health', 'monetary', 800,
                         'Unimed', true, true, true)
                """))
                conn.execute(sa.text("""
                    INSERT INTO job_vacancies (company_id, benefits)
                    VALUES
                        ('11111111-1111-1111-1111-111111111111',
                         ARRAY['Plano de Saúde', 'Vale Aleatório'])
                """))
                # Replay the migration's add-new / backfill / drop /
                # rename pattern. exec_driver_sql is used because the
                # SQL contains `::` casts that text() would mis-parse
                # as bind parameters.
                conn.exec_driver_sql("ALTER TABLE job_vacancies ADD COLUMN benefits_new JSONB")
                conn.exec_driver_sql(
                    "UPDATE job_vacancies SET benefits_new = "
                    f"COALESCE(({backfill_select}), '[]'::jsonb)"
                )
                conn.exec_driver_sql("ALTER TABLE job_vacancies DROP COLUMN benefits")
                conn.exec_driver_sql(
                    "ALTER TABLE job_vacancies RENAME COLUMN benefits_new TO benefits"
                )

                row = conn.execute(sa.text("SELECT benefits FROM job_vacancies")).first()
                assert row is not None
                benefits = row[0]
                assert isinstance(benefits, list)
                assert len(benefits) == 2

                health = next(b for b in benefits if b["name"] == "Plano de Saúde")
                assert health["category"] == "health"
                assert health["value_type"] == "monetary"
                assert health["value"] == 800
                assert health["provider"] == "Unimed"
                assert health["is_highlighted"] is True
                assert health["is_mandatory"] is True

                # Unmatched name → fallback minimal shape, no data loss.
                aleatorio = next(b for b in benefits if b["name"] == "Vale Aleatório")
                assert aleatorio["category"] is None
                assert aleatorio["value_type"] == "informative"

                # Order preserved from the original ARRAY.
                assert [b["name"] for b in benefits] == [
                    "Plano de Saúde",
                    "Vale Aleatório",
                ]
            finally:
                trans.rollback()
    finally:
        engine.dispose()


@pytestmark_db
def test_migration_downgrade_jsonb_to_array_preserves_names():
    """Seed a JSONB benefits column with structured objects, replay
    the downgrade's add-new / backfill / drop / rename pattern, and
    assert the resulting TEXT[] keeps the names while empty/missing
    names are dropped."""
    mod = _import_migration_module()
    backfill_update = mod.DOWNGRADE_BACKFILL_UPDATE
    sync_url = os.getenv("DATABASE_URL", "").replace(
        "+asyncpg", "+psycopg2"
    ).replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = sa.create_engine(sync_url)
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(sa.text("CREATE SCHEMA tsk765_down"))
                conn.execute(sa.text("SET search_path TO tsk765_down"))
                conn.execute(sa.text("""
                    CREATE TABLE job_vacancies (
                        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                        benefits jsonb
                    )
                """))
                conn.execute(sa.text("""
                    INSERT INTO job_vacancies (benefits) VALUES (
                        '[
                          {"name": "Plano", "category": "health", "value_type": "monetary"},
                          {"name": "VR", "category": "food"},
                          {"category": "other"}
                        ]'::jsonb
                    )
                """))
                # Replay the downgrade's add-new / backfill / drop /
                # rename pattern using the exact SQL from the migration.
                conn.exec_driver_sql(
                    "ALTER TABLE job_vacancies ADD COLUMN benefits_old TEXT[]"
                )
                conn.exec_driver_sql(backfill_update)
                conn.exec_driver_sql(
                    "ALTER TABLE job_vacancies DROP COLUMN benefits"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE job_vacancies RENAME COLUMN benefits_old TO benefits"
                )
                row = conn.execute(sa.text("SELECT benefits FROM job_vacancies")).first()
                assert row is not None
                # Names preserved, anonymous entry dropped.
                assert row[0] == ["Plano", "VR"]
            finally:
                trans.rollback()
    finally:
        engine.dispose()
