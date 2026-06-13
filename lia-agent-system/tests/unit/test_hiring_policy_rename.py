"""UC-P1-21: hiring_policy domain is canonical. policy/ is a Service Domain (no domain.py)."""


def test_hiring_policy_domain_importable():
    """hiring_policy.domain module is importable and has HiringPolicyDomain."""
    from app.domains.hiring_policy import domain
    assert hasattr(domain, "HiringPolicyDomain")


def test_hiring_policy_domain_id():
    """HiringPolicyDomain.domain_id is 'hiring_policy' (not 'policy')."""
    from app.domains.hiring_policy.domain import HiringPolicyDomain
    assert HiringPolicyDomain.domain_id == "hiring_policy"


def test_policy_is_service_domain_no_domain_py():
    """policy/ must NOT have domain.py (it is a Service Domain, not registered)."""
    from pathlib import Path
    policy_domain_py = Path(__file__).resolve().parents[2] / "app" / "domains" / "policy" / "domain.py"
    assert not policy_domain_py.exists(), (
        "policy/domain.py must not exist — policy/ is a Service Domain. "
        "The registered domain is hiring_policy/ (domain_id='hiring_policy')."
    )


def test_hiring_policy_has_required_actions():
    """HiringPolicyDomain.get_allowed_actions returns at least 5 actions."""
    from app.domains.hiring_policy.domain import HiringPolicyDomain
    domain = HiringPolicyDomain.__new__(HiringPolicyDomain)
    actions = domain.get_allowed_actions()
    assert len(actions) >= 5
