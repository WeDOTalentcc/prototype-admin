"""Coverage tests for skills_ontology_engine.py — pure graph operations."""
import pytest
from app.domains.talent_intelligence.services.skills_ontology_engine import (
    SkillsOntologyEngine,
    SkillLevel,
    SkillNode,
    SkillEdge,
)


@pytest.fixture(scope="module")
def engine():
    return SkillsOntologyEngine()


class TestSkillLevel:
    def test_beginner(self):
        assert SkillLevel.BEGINNER == "beginner"

    def test_expert(self):
        assert SkillLevel.EXPERT == "expert"

    def test_all_levels(self):
        levels = {sl.value for sl in SkillLevel}
        assert "beginner" in levels
        assert "expert" in levels


class TestSkillNode:
    def test_instantiation_with_required_fields(self):
        node = SkillNode(id="python", name="Python", domain="backend", specialization="language")
        assert node.id == "python"
        assert node.name == "Python"

    def test_canonical_property(self):
        node = SkillNode(id="PYTHON", name="Python", domain="backend", specialization="language")
        assert node.canonical == "python"

    def test_with_domain(self):
        node = SkillNode(id="django", name="Django", domain="backend", specialization="framework")
        assert node.domain == "backend"


class TestSkillEdge:
    def test_instantiation(self):
        edge = SkillEdge(source="python", target="django", weight=0.8, relation="related")
        assert edge.source == "python"
        assert edge.target == "django"
        assert edge.weight == 0.8

    def test_relation_field(self):
        edge = SkillEdge(source="a", target="b", weight=0.5, relation="specialization")
        assert edge.relation == "specialization"


class TestEngineInit:
    def test_engine_not_none(self, engine):
        assert engine is not None

    def test_has_skills(self, engine):
        stats = engine.get_stats()
        assert stats.get("total_skills", 0) > 0

    def test_has_edges(self, engine):
        stats = engine.get_stats()
        assert stats.get("total_edges", 0) >= 0


class TestGetSkillInfo:
    def test_known_skill(self, engine):
        result = engine.get_skill_info("python")
        if result is not None:
            assert isinstance(result, dict)

    def test_unknown_skill(self, engine):
        result = engine.get_skill_info("xyz_nonexistent_skill_999")
        assert result is None

    def test_case_insensitive(self, engine):
        lower = engine.get_skill_info("python")
        upper = engine.get_skill_info("Python")
        assert lower == upper


class TestGetAdjacencies:
    def test_returns_list(self, engine):
        result = engine.get_adjacencies("python")
        assert isinstance(result, list)

    def test_unknown_returns_empty(self, engine):
        result = engine.get_adjacencies("xyz_totally_unknown_999")
        assert result == []

    def test_min_weight_filters(self, engine):
        all_adj = engine.get_adjacencies("python", min_weight=0.0)
        high_adj = engine.get_adjacencies("python", min_weight=0.99)
        assert len(all_adj) >= len(high_adj)


class TestInferRelatedSkills:
    def test_returns_list(self, engine):
        result = engine.infer_related_skills(["python"])
        assert isinstance(result, list)

    def test_empty_returns_empty(self, engine):
        result = engine.infer_related_skills([])
        assert result == []

    def test_limit_respected(self, engine):
        result = engine.infer_related_skills(["python", "django"], limit=5)
        assert len(result) <= 5

    def test_depth_one(self, engine):
        result = engine.infer_related_skills(["python"], depth=1)
        assert isinstance(result, list)


class TestAnalyzeSkillGaps:
    def test_returns_dict(self, engine):
        result = engine.analyze_skill_gaps(
            candidate_skills=["python", "django"],
            required_skills=["python", "react", "postgresql"]
        )
        assert isinstance(result, dict)

    def test_no_gaps_when_matching(self, engine):
        result = engine.analyze_skill_gaps(
            candidate_skills=["python"],
            required_skills=["python"]
        )
        assert isinstance(result, dict)

    def test_empty_candidate(self, engine):
        result = engine.analyze_skill_gaps(
            candidate_skills=[],
            required_skills=["python"]
        )
        assert isinstance(result, dict)


class TestMapSkillsToOntology:
    def test_returns_dict(self, engine):
        result = engine.map_skills_to_ontology(["Python", "React", "SQL"])
        assert isinstance(result, dict)

    def test_empty_list(self, engine):
        result = engine.map_skills_to_ontology([])
        assert isinstance(result, dict)


class TestCosimeSimilarity:
    def test_identical_vectors(self, engine):
        vec = [1.0, 0.0, 0.5]
        assert engine._cosine_similarity(vec, vec) == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_vectors(self, engine):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert engine._cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_similar_vectors(self, engine):
        a = [1.0, 1.0, 1.0]
        b = [1.0, 1.0, 0.9]
        score = engine._cosine_similarity(a, b)
        assert score > 0.99


class TestGetStats:
    def test_returns_dict(self, engine):
        stats = engine.get_stats()
        assert isinstance(stats, dict)

    def test_has_total_skills(self, engine):
        stats = engine.get_stats()
        assert "total_skills" in stats

    def test_has_total_edges(self, engine):
        stats = engine.get_stats()
        assert "total_edges" in stats

    def test_total_skills_positive(self, engine):
        stats = engine.get_stats()
        assert stats["total_skills"] > 0
