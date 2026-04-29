"""
Sensor: JobVacancy.benefits column maps to JSON (not ARRAY) — schema/DB sync.

Audit context (2026-04-29 wizard-domain-hint-leak post-mortem):
  Wizard job creation was failing with:
    asyncpg.DatatypeMismatchError: column "benefits" is of type jsonb
    but expression is of type character varying[]
  Cause: DB schema was manually altered to JSONB at some point, but the
  SQLAlchemy model still declared `Column(ARRAY(String))`. Every INSERT
  with benefits would fail at the driver level.

This sensor is *structural*: it checks the model declaration, not a live
DB INSERT (which would require fixtures, migrations, etc.). The structural
guard catches the regression at unit-test speed without infra setup.

Guards:
  1. JobVacancy.benefits column type is JSON (not ARRAY).
  2. Default factory still returns an empty list (caller contract).
  3. Sibling JSON fields (technical_requirements, languages,
     behavioral_competencies) keep the same JSON pattern — co-evolves to
     prevent the schema/model drift from happening on adjacent fields.

Fix se falhar:
  Verificar `libs/models/lia_models/job_vacancy.py` — coluna `benefits`
  deve ser `Column(JSON, default=list)`. Se foi revertida para ARRAY,
  é o regression do bug original. Confirmar tipo real da coluna no DB
  com `SELECT data_type FROM information_schema.columns WHERE
  table_name='job_vacancies' AND column_name='benefits';` — se DB for
  JSONB e modelo for ARRAY, este teste falha e o asyncpg vai falhar
  em runtime.

Skill canônica: harness-engineering [sensor computacional].
"""
from sqlalchemy import JSON
from sqlalchemy.types import TypeEngine

# Use the canonical import path the runtime uses (job_vacancy_service.py does
# `from lia_models.job_vacancy import JobVacancy`). Importing via the
# alternative `libs.models.lia_models.job_vacancy` path makes SQLAlchemy
# register the table twice and raises InvalidRequestError.
from lia_models.job_vacancy import JobVacancy


def _column(name: str):
    """Return the SQLAlchemy Column object for a model attribute."""
    return JobVacancy.__table__.columns[name]


def _is_json_type(col_type: TypeEngine) -> bool:
    """JSON or JSONB — both are JSON-flavored Postgres columns."""
    type_name = type(col_type).__name__.upper()
    return type_name in ("JSON", "JSONB")


def test_benefits_column_is_json_not_array():
    """benefits column must be JSON (or JSONB) so JSONB DB schema accepts inserts."""
    col = _column("benefits")
    type_name = type(col.type).__name__.upper()
    assert _is_json_type(col.type), (
        f"JobVacancy.benefits has type {type_name!r} — expected JSON/JSONB. "
        f"DB schema is JSONB; ARRAY(String) causes asyncpg "
        f"DatatypeMismatchError on every wizard job creation. "
        f"Fix: change `benefits = Column(ARRAY(String), ...)` to "
        f"`benefits = Column(JSON, default=list)` in "
        f"libs/models/lia_models/job_vacancy.py."
    )


def test_benefits_default_is_list_factory():
    """benefits default must be the `list` factory (or empty list)."""
    col = _column("benefits")
    default = col.default
    assert default is not None, (
        "benefits must have a default — many callsites do `vacancy.benefits or []` "
        "but None vs missing default vs broken default behave differently across "
        "SQLAlchemy / DB driver versions. Keep `default=list` for safety."
    )
    arg = default.arg
    # Accept: `list` (factory class), `[]` (literal), or any callable.
    is_list_factory = arg is list
    is_empty_list_literal = isinstance(arg, list) and arg == []
    is_callable = callable(arg)
    assert is_list_factory or is_empty_list_literal or is_callable, (
        f"benefits default must be `list`, `[]`, or a callable returning a list. "
        f"Got: {arg!r} (type {type(arg).__name__}). "
        f"Fix: in libs/models/lia_models/job_vacancy.py, declare "
        f"`benefits = Column(JSON, default=list)`."
    )


def test_sibling_json_fields_stay_json():
    """Adjacent structured fields keep JSON typing (drift-prevention)."""
    sibling_fields = (
        "technical_requirements",
        "languages",
        "behavioral_competencies",
        "interview_stages",
        "screening_questions",
    )
    drifted = []
    for name in sibling_fields:
        try:
            col = _column(name)
        except KeyError:
            # Field may have been removed/renamed; not this test's concern.
            continue
        if not _is_json_type(col.type):
            drifted.append((name, type(col.type).__name__))
    assert not drifted, (
        f"Sibling JSON fields drifted away from JSON typing: {drifted}. "
        f"All structured fields next to benefits should use Column(JSON, ...) "
        f"for consistency and to avoid the same type-mismatch trap."
    )
