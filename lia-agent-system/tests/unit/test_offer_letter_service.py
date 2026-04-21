"""Unit tests for the E10 OfferLetterService and offer-letter template."""
import asyncio

import pytest

from app.services.offer_letter_service import OfferLetterService
from app.templates.report_templates import report_templates


@pytest.fixture
def service():
    return OfferLetterService()


def test_offer_letter_template_renders_required_blocks():
    rendered = report_templates.offer_letter(
        {
            "candidate_name": "Maria Silva",
            "job_title": "Engenheira de Software Sênior",
            "company_name": "WeDO Talent",
            "manager_name": "João Recruiter",
            "currency": "BRL",
            "salary": 18000.0,
            "bonus_pct": 15.0,
            "bonus_target": 32000.0,
            "benefits": ["Plano de saúde", "Vale refeição"],
            "start_date": "01/06/2026",
            "response_deadline": "29/04/2026",
            "custom_clauses": ["Período de experiência de 90 dias"],
        }
    )

    assert rendered["version"] == "v1.0"
    md = rendered["markdown"]
    html = rendered["html"]
    for needle in [
        "Maria Silva",
        "Engenheira de Software Sênior",
        "WeDO Talent",
        "Plano de saúde",
        "Próximos passos",
    ]:
        assert needle in md
        assert needle in html


def test_offer_letter_template_falls_back_when_salary_missing():
    rendered = report_templates.offer_letter(
        {
            "candidate_name": "Ana",
            "job_title": "Analista",
        }
    )
    assert "a definir" in rendered["markdown"]
    assert "A combinar" in rendered["markdown"]


def test_required_approval_level_thresholds(service):
    # Low salary defaults to manager
    assert service.required_approval_level(salary=8000) == "manager"
    # Crosses the director threshold (>= R$15k/month → 180k/year)
    assert service.required_approval_level(salary=15000) == "director"
    # Crosses the VP/CFO threshold (>= R$30k/month → 360k/year)
    assert service.required_approval_level(salary=32000) == "vp_or_cfo"
    # Bonus pushes the package over the next bracket
    assert service.required_approval_level(salary=14000, bonus_target=24_000) == "director"
    # Missing data → safe default
    assert service.required_approval_level(salary=None) == "manager"


def test_append_round_appends_audit_entry(service):
    rounds = service.append_round(
        None,
        round_type="initial",
        actor="company",
        actor_name="Recruiter",
        salary=15000,
        currency="BRL",
        message="First draft",
    )
    rounds = service.append_round(
        rounds,
        round_type="counter_from_candidate",
        actor="candidate",
        actor_name="Maria",
        salary=17000,
        message="Counter offer",
    )
    assert [r["round"] for r in rounds] == [1, 2]
    assert rounds[0]["type"] == "initial"
    assert rounds[1]["actor"] == "candidate"
    assert rounds[1]["salary"] == 17000


def test_build_letter_uses_template_when_llm_disabled(service):
    rendered = asyncio.get_event_loop().run_until_complete(
        service.build_letter(
            company_id="acme",
            candidate_name="Pedro",
            job_title="Designer",
            salary=12000.0,
            benefits=["VR", "Plano de saúde"],
            db=None,
            use_llm=False,
        )
    )
    assert rendered["template_version"] == "v1.0"
    assert rendered["llm_provider"] is None
    assert "Pedro" in rendered["markdown"]
    assert "Designer" in rendered["markdown"]
    assert rendered["merged_benefits"] == ["VR", "Plano de saúde"]
    assert rendered["merged_clauses"] == []
    assert rendered["salary"] == 12000.0
    assert rendered["currency"] == "BRL"


def test_send_gate_blocks_unapproved_director_offer():
    """The /send endpoint must refuse anything that didn't pass approval,
    except low-value (manager-level) offers which can ship from DRAFT."""
    from app.api.v1.offer_proposals import _is_send_allowed
    from lia_models.offer_proposal import OfferProposal, OfferStatus

    # High-value DRAFT → blocked (needs approval round)
    p = OfferProposal(
        company_id="acme", candidate_name="X", status=OfferStatus.DRAFT.value,
        approval_required_level="director",
    )
    assert _is_send_allowed(p) is False

    # PENDING_APPROVAL → still blocked
    p.status = OfferStatus.PENDING_APPROVAL.value
    assert _is_send_allowed(p) is False

    # APPROVED → allowed
    p.status = OfferStatus.APPROVED.value
    assert _is_send_allowed(p) is True

    # Manager-level DRAFT → allowed (auto-approved tier)
    p2 = OfferProposal(
        company_id="acme", candidate_name="Y", status=OfferStatus.DRAFT.value,
        approval_required_level="manager",
    )
    assert _is_send_allowed(p2) is True


def test_offer_status_has_internal_rejected_member():
    """Internal-approval rejection (chain said no) is a distinct state from
    candidate decline. Both must exist on OfferStatus so the approval sync
    callback and `record_approval_decision` can mark the proposal correctly
    without raising AttributeError at runtime."""
    from lia_models.offer_proposal import OfferStatus

    members = {m.value for m in OfferStatus}
    assert "rejected" in members, "internal-approval rejection state missing"
    assert "declined" in members, "candidate-decline state missing"
    assert OfferStatus.REJECTED.value == "rejected"
    assert OfferStatus.DECLINED.value == "declined"


def test_initial_round_actor_identity_fields(service):
    """The initial round must put the manager/creator name in actor_name and
    NEVER stuff it into actor_email (regression guard for the typo where
    manager_name was assigned to actor_email)."""
    rounds = service.append_round(
        [],
        round_type="initial",
        actor="company",
        actor_name="João Recruiter",
        actor_email=None,
        salary=15000,
        message="Offer drafted",
    )
    entry = rounds[0]
    assert entry["actor_name"] == "João Recruiter"
    assert entry["actor_email"] is None
    # actor_email must look like an email when set, never a person's name.
    rounds2 = service.append_round(
        rounds,
        round_type="approval",
        actor="approver",
        actor_name="Diretora",
        actor_email="diretora@acme.com",
        message="ok",
    )
    assert "@" in rounds2[1]["actor_email"]


def test_resolve_approver_returns_none_when_no_users(service):
    """Resolver returns None when the DB lookup fails so the API surfaces a 422
    instead of silently picking the wrong approver."""
    from unittest.mock import AsyncMock, MagicMock

    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("no DB"))
    out = asyncio.get_event_loop().run_until_complete(
        service.resolve_approver(db, "acme", "vp_or_cfo")
    )
    assert out is None
