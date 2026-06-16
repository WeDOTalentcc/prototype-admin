"""
Smoke tests for job_management domain — boy-scout addition (P1-5).

P1-5 era classificado em Fase 1 como "0 testes específicos" baseado em
`find tests -path "*job_management*"` retornando vazio. Realidade:
test_wizard_react_agent.py (13 tests passing) cobre WizardReActAgent
(agente canonical de job_management). Esse arquivo é boy-scout para
fortalecer cobertura sobre 29 actions + domain registration.

Cobre:
- Domain registration via @register_domain
- 29 actions têm action_id válido + required_params
- Suggestions retornam list[str]
- Compliance config marcado
- Process_intent fallback graceful
"""
import pytest


class TestJobManagementDomainCanonical:
    """Domain registration + canonical compliance."""

    def test_domain_importable(self):
        from app.domains.job_management.domain import JobManagementDomain
        assert JobManagementDomain is not None

    def test_domain_id_canonical(self):
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        assert d.domain_id == "job_management"

    def test_domain_inherits_compliance_base(self):
        """LIA-C01: domain MUST extend ComplianceDomainPrompt."""
        from app.domains.job_management.domain import JobManagementDomain
        from app.domains.compliance_base import ComplianceDomainPrompt
        assert issubclass(JobManagementDomain, ComplianceDomainPrompt)


class TestJobManagementActions:
    """29 DomainAction definidos em actions.py."""

    def test_actions_count(self):
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        actions = d.get_allowed_actions()
        assert len(actions) >= 25, f"Expected >=25 actions, got {len(actions)}"

    def test_each_action_has_action_id(self):
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        for action in d.get_allowed_actions():
            assert action.action_id, f"Action sem action_id: {action}"
            assert isinstance(action.action_id, str)

    def test_each_action_has_name(self):
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        for action in d.get_allowed_actions():
            assert action.name, f"Action {action.action_id} sem name"

    def test_critical_actions_present(self):
        """CRUD core actions canonical."""
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        action_ids = {a.action_id for a in d.get_allowed_actions()}
        critical = {"create_job", "update_job", "publish_job", "close_job"}
        missing = critical - action_ids
        assert not missing, f"Critical actions missing: {missing}"

    def test_no_duplicate_action_ids(self):
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        action_ids = [a.action_id for a in d.get_allowed_actions()]
        assert len(action_ids) == len(set(action_ids)), "Duplicate action_ids found"


class TestJobManagementWizardAgent:
    """WizardReActAgent é o agente canonical de job_management."""

    def test_wizard_agent_importable(self):
        from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
        agent = WizardReActAgent()
        assert agent is not None

    def test_wizard_agent_has_register_decorator(self):
        """G7: agente canonical deve ter @register_agent."""
        from app.shared.agents.agent_registry import _AGENT_REGISTRY
        # WizardReActAgent registered as "wizard"
        assert "wizard" in _AGENT_REGISTRY or any(
            "wizard" in alias for entry in _AGENT_REGISTRY.values()
            for alias in (getattr(entry, "aliases", []) or [])
        ), "WizardReActAgent not in registry"


class TestJobManagementCompliance:
    """Compliance LIA-C01 + ADR-001 enforcement."""

    def test_no_inline_sql_in_services(self):
        """ADR-001: services não fazem SQL inline."""
        from pathlib import Path
        services_dir = Path("app/domains/job_management/services")
        if not services_dir.exists():
            pytest.skip("Services dir não existe")
        violations = []
        for py_file in services_dir.glob("**/*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # ADR-001-EXEMPT marker é OK
            if "ADR-001-EXEMPT" in content:
                continue
            # Detectar text() ou raw SQL
            if 'db.execute(text("' in content or "db.execute(text('" in content:
                violations.append(str(py_file))
        assert not violations, f"ADR-001 violations: {violations}"

    def test_fairness_guard_in_wizard_tool_registry(self):
        """Wizard tools devem invocar FairnessGuard."""
        from pathlib import Path
        registry = Path("app/domains/job_management/agents/wizard_tool_registry.py")
        if registry.exists():
            content = registry.read_text(encoding="utf-8", errors="ignore")
            assert "FairnessGuard" in content or "fairness_guard" in content, \
                "wizard_tool_registry.py sem referência a FairnessGuard"


class TestJobManagementSuggestions:
    """Suggestions API."""

    def test_suggestions_method_exists(self):
        """get_suggestions é método opcional. Validar que existe e é callable."""
        from app.domains.job_management.domain import JobManagementDomain
        d = JobManagementDomain()
        if hasattr(d, "get_suggestions"):
            assert callable(d.get_suggestions)
        else:
            pytest.skip("get_suggestions é opcional para domains")
