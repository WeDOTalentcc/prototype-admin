# tests/unit/rbac/test_vacancy_salary_visibility.py
from types import SimpleNamespace
from app.shared.rbac.pii_field_resolver import resolve_field_visibility
from app.api.v1.job_vacancies._shared import apply_vacancy_salary_visibility

def _user(role="recruiter", override=None):
    return SimpleNamespace(role=role, can_view_salary=False, can_view_sensitive_pii=True,
                           pii_field_visibility=override)

def test_default_vacancy_salary_visible():
    assert resolve_field_visibility(_user(), {}, "vacancy_salary", default=True) is True

def test_role_default_hides_vacancy_salary():
    assert resolve_field_visibility(_user(role="recruiter"), {"recruiter": {"vacancy_salary": False}}, "vacancy_salary") is False

def test_user_override_wins():
    assert resolve_field_visibility(_user(role="recruiter", override={"vacancy_salary": True}), {"recruiter": {"vacancy_salary": False}}, "vacancy_salary") is True

def test_apply_masks_salary_fields_when_hidden():
    d = {"id": "v1", "salary": 5000, "salary_range": {"min": 4000, "max": 6000}, "title": "Dev"}
    out = apply_vacancy_salary_visibility(d, _user(role="recruiter"), {"recruiter": {"vacancy_salary": False}})
    assert out["salary"] is None
    assert out["salary_range"] is None
    assert out["title"] == "Dev"
    assert out.get("vacancy_salary_masked") is True

def test_apply_keeps_salary_when_visible():
    d = {"id": "v1", "salary": 5000, "salary_range": {"min": 4000}}
    out = apply_vacancy_salary_visibility(d, _user(role="recruiter"), {})
    assert out["salary"] == 5000
    assert out.get("vacancy_salary_masked") in (False, None)
