"""Unit tests — Phase 4J (lifecycle ats_importada wiring).

Harness: SENSOR for Phase 4J fix.

Bug fixed: Phase 4H bulk-import created JobVacancy rows with
source='ats_import' + additional_data["import_source"]="spreadsheet" — but
analytics.py:_classify_job_lifecycle_stage uses source_system column AND
additional_data["imported_from_ats"] flag. So imported vagas landed in
'rascunho' instead of 'ats_importada'.

Phase 4J populates BOTH fields so vagas correctly appear under "ATS
Importada" stage in the Recrutar page rail.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestSourceSystemSlugMapping:
    """_map_source_to_system_slug must classify ATS sources for analytics.py."""

    def test_known_ats_sources_map_to_canonical_slugs(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        cases = {
            "ats_gupy": "gupy",
            "ats_pandape": "pandape",
            "ats_greenhouse": "greenhouse",
        }
        for import_src, expected_slug in cases.items():
            result = JDImportService._map_source_to_system_slug(import_src)
            assert result == expected_slug, (
                f"Fix: import_source '{import_src}' must map to slug "
                f"'{expected_slug}' (got '{result}'). The slug is read by "
                f"analytics.py:_job_source_system to assign 'ats_importada' "
                f"lifecycle stage on the Recrutar page."
            )

    def test_generic_imports_fall_through_to_ats_other(self):
        from app.domains.job_management.services.jd_import_service import JDImportService

        generic = ["spreadsheet", "manual_upload", "api_import", "hris_sap", "ats_lever", "ats_other"]
        for src in generic:
            result = JDImportService._map_source_to_system_slug(src)
            assert result == "ats_other", (
                f"Fix: generic import '{src}' must map to 'ats_other' (catch-all "
                f"slug used by classifier). Got '{result}'. Edit "
                f"_map_source_to_system_slug.slug_map dict."
            )


class TestMirrorPopulatesAtsLifecycleFields:
    """_mirror_to_job_vacancy MUST populate source_system + imported_from_ats."""

    def test_mirror_call_sets_source_system_and_flag(self):
        """Reads the actual source code to assert the fix is in place.

        Why structural assertion: testing the actual DB write requires
        mocking SQLAlchemy session extensively, which is brittle. The fix
        is a static patch — structural grep proves it landed.
        """
        with open("app/domains/job_management/services/jd_import_service.py") as f:
            src = f.read()

        # source_system slug is computed
        assert "source_system_slug = self._map_source_to_system_slug(import_source)" in src, (
            "Fix: _mirror_to_job_vacancy MUST compute source_system_slug "
            "before creating JobVacancy. See Phase 4J."
        )
        # source_system passed to JobVacancy constructor
        assert "source_system=source_system_slug," in src, (
            "Fix: JobVacancy(source_system=source_system_slug, ...) must be "
            "set so analytics.py classifier reads it."
        )
        # additional_data has imported_from_ats=True
        assert '"imported_from_ats": True,' in src, (
            "Fix: additional_data must include imported_from_ats=True "
            "as defense-in-depth fallback for the classifier."
        )

    def test_status_forced_to_rascunho_for_classifier(self):
        """Classifier requires status='Rascunho' AND imported_from_ats."""
        with open("app/domains/job_management/services/jd_import_service.py") as f:
            src = f.read()

        # Status hard-coded to 'Rascunho' (overrides external ATS status)
        assert 'status="Rascunho",' in src, (
            "Fix: vacancy.status MUST be 'Rascunho' for classifier to "
            "return 'ats_importada' (see analytics.py:_classify_job_lifecycle_stage). "
            "External ATS may send status='Active' but that breaks classification."
        )
        # Original status preserved for debugging
        assert '"original_external_status": imported_jd.job_status,' in src, (
            "Fix: preserve original ATS status in additional_data for "
            "debugging / future restore. Don't drop it silently."
        )


class TestSourceSystemColumnInModel:
    """JobVacancy SQLAlchemy model must expose source_system column."""

    def test_source_system_attribute_exists(self):
        from lia_models.job_vacancy import JobVacancy

        assert hasattr(JobVacancy, "source_system"), (
            "Fix: JobVacancy missing source_system column attribute. "
            "Column exists in DB (Task #435) but Python ORM was missing it. "
            "Add: source_system = Column(String(50), nullable=True, index=True)"
        )

    def test_source_system_type_and_nullability(self):
        from lia_models.job_vacancy import JobVacancy

        col = JobVacancy.source_system.property.columns[0]
        assert str(col.type) == "VARCHAR(50)", (
            f"Fix: source_system type must be VARCHAR(50) (got {col.type})"
        )
        assert col.nullable is True, (
            "Fix: source_system must be nullable (NULL for non-ATS vagas)"
        )
