"""Unit tests — Phase 4H source + wizard_stage on JobVacancy.

Harness: SENSOR (computacional) for Phase 4H.

Covers:
1. JDImportService._map_source_to_vacancy maps ImportSource enum values
   correctly to JobVacancy.source ('ats_external' for live ATS sync,
   'ats_import' for one-time imports).
2. JDImportService._mirror_to_job_vacancy raises ValueError when company_id
   is empty (multi-tenancy enforcement, fail-closed on writes).
3. JDImportService._mirror_to_job_vacancy is idempotent — duplicate external_id
   for same source skips creation.
4. JobVacancy model has source + wizard_stage columns with correct types.

Why these tests exist (Harness rationale):
  GUIDE — JobVacancy.source enum is documented in model docstring.
  SENSOR — these tests fail with hint message if a future change breaks the
  invariant. Each assert carries a "Fix:" hint optimized for LLM regression.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4


# ---------------------------------------------------------------------------
# Test 1: Source mapping (pure function, no DB)
# ---------------------------------------------------------------------------

class TestSourceMapping:
    """_map_source_to_vacancy must classify ATS sources correctly."""

    def test_live_ats_sources_map_to_ats_external(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        live_sources = ["ats_gupy", "ats_pandape", "ats_greenhouse", "ats_lever", "ats_other"]
        for src in live_sources:
            result = JDImportService._map_source_to_vacancy(src)
            assert result == "ats_external", (
                f"Fix: live ATS source '{src}' must map to 'ats_external' "
                f"(got '{result}'). Edit _map_source_to_vacancy in "
                f"app/domains/job_management/services/jd_import_service.py"
            )

    def test_one_time_imports_map_to_ats_import(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        one_time = ["spreadsheet", "manual_upload", "api_import", "hris_sap"]
        for src in one_time:
            result = JDImportService._map_source_to_vacancy(src)
            assert result == "ats_import", (
                f"Fix: one-time import source '{src}' must map to 'ats_import' "
                f"(got '{result}'). Edit _map_source_to_vacancy."
            )

    def test_unknown_source_defaults_to_ats_import(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        result = JDImportService._map_source_to_vacancy("totally_unknown_source")
        assert result == "ats_import", (
            "Fix: unknown sources must default to 'ats_import' "
            "(defensive — preserves filterability)."
        )


# ---------------------------------------------------------------------------
# Test 2: Multi-tenancy enforcement on _mirror_to_job_vacancy
# ---------------------------------------------------------------------------

class TestMirrorMultiTenancy:
    """_mirror_to_job_vacancy must fail-closed on missing company_id."""

    def test_empty_company_id_raises_value_error(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        svc = JDImportService()
        mock_db = AsyncMock()
        mock_jd = MagicMock()
        mock_jd.id = uuid4()
        mock_jd.external_id = "ext-123"

        async def _run():
            await svc._mirror_to_job_vacancy(
                db=mock_db,
                company_id=None,  # ← FAIL-CLOSED trigger
                imported_jd=mock_jd,
                import_source="manual_upload",
            )

        try:
            asyncio.run(_run())
            raise AssertionError(
                "Fix: _mirror_to_job_vacancy MUST raise ValueError when "
                "company_id is None — multi-tenancy enforcement. Add: "
                "if not company_id: raise ValueError(...)"
            )
        except ValueError as exc:
            assert "company_id" in str(exc).lower(), (
                f"Fix: ValueError message must mention 'company_id' "
                f"(got '{exc}'). LLM-friendly hint."
            )

    def test_empty_string_company_id_raises(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        svc = JDImportService()
        mock_db = AsyncMock()
        mock_jd = MagicMock()

        async def _run():
            await svc._mirror_to_job_vacancy(
                db=mock_db,
                company_id="",  # falsy
                imported_jd=mock_jd,
                import_source="manual_upload",
            )

        try:
            asyncio.run(_run())
            raise AssertionError(
                "Fix: empty string company_id MUST also raise ValueError. "
                "Falsy check (`if not company_id`) covers both None and ''."
            )
        except ValueError:
            pass  # expected


# ---------------------------------------------------------------------------
# Test 3: Idempotency (duplicate external_id)
# ---------------------------------------------------------------------------

class TestMirrorIdempotency:
    """Duplicate external_id for same source should skip creation."""

    def test_duplicate_external_id_same_source_skips(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        svc = JDImportService()
        company_id = uuid4()

        # Mock imported_jd
        mock_jd = MagicMock()
        mock_jd.id = uuid4()
        mock_jd.external_id = "ext-abc-123"
        mock_jd.import_batch_id = uuid4()

        # Mock existing JobVacancy
        existing_vacancy = MagicMock()

        # Mock async db: scalar_one_or_none returns existing
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_vacancy)
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        async def _run():
            await svc._mirror_to_job_vacancy(
                db=mock_db,
                company_id=company_id,
                imported_jd=mock_jd,
                import_source="manual_upload",
            )

        asyncio.run(_run())

        # Assertion: db.add was NOT called (idempotent skip)
        mock_db.add.assert_not_called()
        # No commit either
        assert mock_db.commit.call_count == 0, (
            "Fix: when JobVacancy with same external_id exists, "
            "_mirror_to_job_vacancy must early-return WITHOUT committing. "
            "Check the idempotency guard in _mirror_to_job_vacancy."
        )


# ---------------------------------------------------------------------------
# Test 4: Model column types (structural assertion)
# ---------------------------------------------------------------------------

class TestJobVacancyModelColumns:
    """JobVacancy model must have source + wizard_stage with correct types."""

    def test_source_column_exists_with_correct_defaults(self):
        from lia_models.job_vacancy import JobVacancy

        assert hasattr(JobVacancy, "source"), (
            "Fix: JobVacancy model missing `source` column. "
            "Add to libs/models/lia_models/job_vacancy.py: "
            "source = Column(String(50), nullable=False, default='wizard', server_default='wizard', index=True)"
        )

        col = JobVacancy.source.property.columns[0]
        assert str(col.type) == "VARCHAR(50)", (
            f"Fix: source column type must be VARCHAR(50) (got {col.type})"
        )
        assert col.nullable is False, (
            "Fix: source must be NOT NULL (multi-tenancy + filter consistency)"
        )
        assert col.default is not None, (
            "Fix: source must have default='wizard' for backward compatibility"
        )

    def test_wizard_stage_column_exists(self):
        from lia_models.job_vacancy import JobVacancy

        assert hasattr(JobVacancy, "wizard_stage"), (
            "Fix: JobVacancy model missing `wizard_stage` column. "
            "Add to libs/models/lia_models/job_vacancy.py: "
            "wizard_stage = Column(String(50), nullable=True, index=True)"
        )

        col = JobVacancy.wizard_stage.property.columns[0]
        assert str(col.type) == "VARCHAR(50)", (
            f"Fix: wizard_stage column type must be VARCHAR(50) (got {col.type})"
        )
        assert col.nullable is True, (
            "Fix: wizard_stage must be nullable (NULL for non-wizard sources)"
        )


# ---------------------------------------------------------------------------
# Test 5: Pydantic schemas (Create/Update/Response)
# ---------------------------------------------------------------------------

class TestPydanticSchemas:
    """JobVacancyCreate/Update/Response must accept source + wizard_stage."""

    def test_create_default_source_is_wizard(self):
        # Direct import bypassing __init__ chain (avoids unrelated import errors)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_shared", "app/api/v1/job_vacancies/_shared.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        c = mod.JobVacancyCreate(title="Test Job")
        assert c.source == "wizard", (
            f"Fix: JobVacancyCreate.source default must be 'wizard' "
            f"(got '{c.source}'). Edit app/api/v1/job_vacancies/_shared.py"
        )
        assert c.wizard_stage is None, (
            "Fix: JobVacancyCreate.wizard_stage default must be None "
            "(populated only after wizard runs)."
        )

    def test_update_accepts_source_and_wizard_stage(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_shared", "app/api/v1/job_vacancies/_shared.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        u = mod.JobVacancyUpdate(source="ats_import", wizard_stage="intake")
        assert u.source == "ats_import"
        assert u.wizard_stage == "intake"
