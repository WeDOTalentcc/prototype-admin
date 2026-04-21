"""
FIX 7 — Semantic overlap disambiguation.

The 3 identified clusters should have cross-reference text in their descriptions
so the LLM can distinguish between similar actions.
"""
import pytest


def _find_action(module_path: str, class_name: str, action_id: str):
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    domain = cls()
    for a in domain.get_allowed_actions():
        if a.action_id == action_id:
            return a
    return None


class TestJDClusterDisambiguation:
    """FIX 7 Cluster 2: JD improvement overlap."""

    @pytest.mark.parametrize("action_id,other_ids", [
        ("generate_jd", ["enrich_jd", "suggest_jd_improvements"]),
        ("enrich_jd", ["generate_jd", "suggest_jd_improvements"]),
        ("suggest_jd_improvements", ["enrich_jd", "generate_jd"]),
    ])
    def test_jd_action_has_cross_reference(self, action_id, other_ids):
        a = _find_action(
            "app.domains.job_management.domain",
            "JobManagementDomain",
            action_id,
        )
        assert a is not None, f"Action {action_id} not found in JobManagementDomain"
        desc = a.description.lower()
        # At least one of the sibling ids should appear in the description
        mentions = [oid for oid in other_ids if oid in desc]
        assert len(mentions) >= 1, (
            f"{action_id} description must reference at least 1 of {other_ids}, got: {desc[-200:]}"
        )


class TestCandidateSearchClusterDisambiguation:
    """FIX 7 Cluster 1: candidate search overlap."""

    @pytest.mark.parametrize("action_id,other_ids", [
        ("auto_source", ["suggest_candidates", "talent_pool_search"]),
        ("suggest_candidates", ["auto_source", "talent_pool_search"]),
        ("talent_pool_search", ["auto_source", "suggest_candidates"]),
    ])
    def test_candidate_search_action_has_cross_reference(self, action_id, other_ids):
        a = _find_action(
            "app.domains.sourcing.domain",
            "SourcingDomain",
            action_id,
        )
        if a is None:
            pytest.skip(f"Action {action_id} not in SourcingDomain")
        desc = a.description.lower()
        mentions = [oid for oid in other_ids if oid in desc]
        assert len(mentions) >= 1, (
            f"{action_id} description must reference at least 1 of {other_ids}, got: {desc[-200:]}"
        )
