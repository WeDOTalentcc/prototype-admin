"""
Onda 1 / O1.2 — JobVacancyUpdate must accept the vacancy-level deadline fields
and urgency_level so the "Informações Gerais" save persists them.

Root cause (audit 2026-06-06): the model `JobVacancy` HAS the columns
(open_date, deadline, deadline_screening, deadline_shortlist, deadline_closing,
urgency_level) and the update write-loop is generic (`setattr` for any field the
model has), but `JobVacancyUpdate` is `extra='forbid'` and these fields were
absent from the schema — so the PUT payload was rejected with HTTP 422 and the
section could never be saved. These are REAL features (deadlines feed
job_alert_service / notifications; urgency is displayed and filterable).
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.api.v1.job_vacancies._shared import JobVacancyUpdate


class TestJobVacancyUpdateDeadlines:
    def test_accepts_all_deadline_fields(self):
        model = JobVacancyUpdate(
            open_date="2026-07-01T00:00:00",
            deadline="2026-09-30T00:00:00",
            deadline_screening="2026-07-15T00:00:00",
            deadline_shortlist="2026-08-15T00:00:00",
            deadline_closing="2026-09-30T00:00:00",
        )
        assert isinstance(model.deadline_screening, datetime)
        assert model.deadline_screening.year == 2026
        assert isinstance(model.deadline_closing, datetime)

    def test_accepts_urgency_level_as_int(self):
        model = JobVacancyUpdate(urgency_level=4)
        assert model.urgency_level == 4

    def test_deadline_fields_default_none(self):
        model = JobVacancyUpdate(title="x")
        assert model.deadline_screening is None
        assert model.deadline is None
        assert model.urgency_level is None

    def test_still_forbids_unknown_field(self):
        # extra='forbid' gate must remain intact (the canonical contract).
        with pytest.raises(ValidationError):
            JobVacancyUpdate(target_sector="Tecnologia")
