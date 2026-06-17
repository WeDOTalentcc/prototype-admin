"""Task #435 — tests for the structured job vacancy source_system marker.

Covers:
- ``_job_source_system`` reads the new column.
- ``_job_is_imported_from_ats`` prefers ``source_system`` over the legacy
  ``additional_data`` heuristic but still recognises legacy markers.
- ``_job_ats_source_label`` returns a friendly label for known ATSs and
  falls back to "ATS externo" for unknown sources.
"""
from types import SimpleNamespace

from app.api.v1.job_vacancies.analytics import (
    ATS_SOURCE_LABELS,
    KNOWN_ATS_SOURCES,
    _job_ats_source_label,
    _job_is_imported_from_ats,
    _job_source_system,
)


def _job(*, source_system=None, additional_data=None):
    return SimpleNamespace(
        source_system=source_system,
        additional_data=additional_data,
    )


class TestSourceSystemHelpers:
    def test_known_ats_includes_main_providers(self) -> None:
        for slug in ("gupy", "pandape", "merge"):
            assert slug in KNOWN_ATS_SOURCES
            assert slug in ATS_SOURCE_LABELS

    def test_source_system_returns_normalized_slug(self) -> None:
        assert _job_source_system(_job(source_system="GUPY")) == "gupy"
        assert _job_source_system(_job(source_system=" pandape ")) == "pandape"
        assert _job_source_system(_job(source_system=None)) is None
        assert _job_source_system(_job(source_system="")) is None

    def test_imported_flag_uses_source_system_first(self) -> None:
        # source_system wins, even when additional_data is empty.
        assert _job_is_imported_from_ats(_job(source_system="gupy", additional_data={})) is True
        assert _job_is_imported_from_ats(_job(source_system="pandape")) is True
        # Internal LIA source must NOT light up the badge.
        assert _job_is_imported_from_ats(_job(source_system="lia_fast_track")) is False
        assert _job_is_imported_from_ats(_job(source_system="lia")) is False

    def test_imported_flag_falls_back_to_legacy_heuristic(self) -> None:
        # No source_system + legacy additional_data marker still works.
        assert _job_is_imported_from_ats(
            _job(additional_data={"imported_from_ats": True})
        ) is True
        assert _job_is_imported_from_ats(
            _job(additional_data={"source": "Gupy"})
        ) is True
        assert _job_is_imported_from_ats(
            _job(additional_data={"external_system_id": "abc"})
        ) is True
        # No marker at all -> False.
        assert _job_is_imported_from_ats(_job(additional_data={})) is False
        assert _job_is_imported_from_ats(_job(additional_data=None)) is False

    def test_label_named_when_source_known(self) -> None:
        assert _job_ats_source_label(_job(source_system="gupy")) == "Gupy"
        assert _job_ats_source_label(_job(source_system="pandape")) == "Pandapé"
        # Legacy: known slug only in additional_data.
        assert (
            _job_ats_source_label(_job(additional_data={"source": "merge"}))
            == "Merge"
        )

    def test_label_falls_back_to_generic_ats_external(self) -> None:
        # imported_from_ats=True without a recognisable slug.
        label = _job_ats_source_label(
            _job(additional_data={"imported_from_ats": True})
        )
        assert label == ATS_SOURCE_LABELS["ats_other"]

    def test_label_none_when_not_imported(self) -> None:
        assert _job_ats_source_label(_job()) is None
        assert _job_ats_source_label(_job(source_system="lia_fast_track")) is None
