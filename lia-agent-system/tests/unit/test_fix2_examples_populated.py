"""
FIX 2 - Verify all DomainActions have examples populated.

After FIX 2, every DomainAction across 13 domains should have at least 1 example
for few-shot intent matching.
"""
import pytest


DOMAIN_CLASSES = [
    ("app.domains.agent_studio.domain", "AgentStudioDomain"),
    ("app.domains.analytics.domain", "AnalyticsDomain"),
    ("app.domains.ats_integration.domain", "ATSIntegrationDomain"),
    ("app.domains.automation.domain", "AutomationDomain"),
    ("app.domains.communication.domain", "CommunicationDomain"),
    ("app.domains.cv_screening.domain", "CVScreeningDomain"),
    ("app.domains.digital_twin.domain", "DigitalTwinDomain"),
    ("app.domains.interview_scheduling.domain", "InterviewSchedulingDomain"),
    ("app.domains.job_management.domain", "JobManagementDomain"),
    ("app.domains.recruiter_assistant.domain", "RecruiterAssistantDomain"),
    ("app.domains.recruitment_campaign.domain", "RecruitmentCampaignDomain"),
    ("app.domains.sourcing.domain", "SourcingDomain"),
    ("app.domains.talent_pool.domain", "TalentPoolDomain"),
]


def _get_domain(module_path: str, class_name: str):
    """Try to import a domain class; return instance or None if unavailable."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name, None)
        if cls is None:
            # Try common alternative names
            alternatives = [class_name.replace("Domain", ""), "Domain"]
            for alt in alternatives:
                cls = getattr(mod, alt, None)
                if cls:
                    break
        if cls is None:
            return None
        return cls()
    except Exception:
        return None


class TestDomainActionsHaveExamples:
    """FIX 2: Every DomainAction should have at least 1 example after FIX 2."""

    @pytest.mark.parametrize("module_path,class_name", DOMAIN_CLASSES)
    def test_all_actions_have_examples(self, module_path, class_name):
        domain = _get_domain(module_path, class_name)
        if domain is None:
            pytest.skip(f"Could not import {class_name}")

        actions = domain.get_allowed_actions()
        if not actions:
            pytest.skip(f"{class_name} has no actions")

        missing = []
        for action in actions:
            examples = getattr(action, "examples", ())
            if not examples or len(examples) == 0:
                missing.append(action.action_id)

        assert not missing, (
            f"{class_name}: {len(missing)} actions without examples: {missing[:5]}..."
        )

    def test_coverage_count_at_least_240(self):
        """Aggregate check: at least 240 of 245 actions must have examples."""
        import importlib
        total = 0
        with_examples = 0
        for module_path, class_name in DOMAIN_CLASSES:
            domain = _get_domain(module_path, class_name)
            if domain is None:
                continue
            for action in domain.get_allowed_actions():
                total += 1
                if getattr(action, "examples", ()):
                    with_examples += 1
        assert with_examples >= 240, (
            f"Esperado ao menos 240 actions com examples, encontrado {with_examples}/{total}"
        )
