"""UC-P1-21: hiring_policy domain is canonical and policy/ has deprecation shim."""


def test_hiring_policy_domain_importable():
    """hiring_policy.domain module is importable and has HiringPolicyDomain."""
    from app.domains.hiring_policy import domain
    assert hasattr(domain, "HiringPolicyDomain")


def test_hiring_policy_domain_id():
    """HiringPolicyDomain.domain_id is 'hiring_policy' (not 'policy')."""
    from app.domains.hiring_policy.domain import HiringPolicyDomain
    assert HiringPolicyDomain.domain_id == "hiring_policy"


def test_policy_domain_marked_deprecated():
    """Legacy policy/ domain is marked as deprecated in __init__."""
    import importlib
    policy_pkg = importlib.import_module("app.domains.policy")
    domain_type = getattr(policy_pkg, "__domain_type__", None)
    assert domain_type == "deprecated", (
        f"Expected __domain_type__='deprecated', got {domain_type!r}. "
        "The policy/ domain must be marked deprecated so tools can warn callers."
    )


def test_policy_shim_re_exports_hiring_policy():
    """policy/ shim re-exports HiringPolicyDomain for backward compat."""
    from app.domains.policy import HiringPolicyDomain as ShimDomain
    from app.domains.hiring_policy.domain import HiringPolicyDomain as RealDomain
    assert ShimDomain is RealDomain, (
        "policy/__init__.py must re-export HiringPolicyDomain from hiring_policy"
    )


def test_hiring_policy_has_required_actions():
    """HiringPolicyDomain.get_allowed_actions returns at least 5 actions."""
    from app.domains.hiring_policy.domain import HiringPolicyDomain
    domain = HiringPolicyDomain.__new__(HiringPolicyDomain)
    actions = domain.get_allowed_actions()
    assert len(actions) >= 5
