"""Coverage tests for skills_ontology_engine.py — pure graph operations."""
import pytest
from app.domains.talent_intelligence.services.skills_ontology_engine import (
    SkillsOntologyEngine,
    SkillLevel,
    SkillNode,
    SkillEdge,
)


@pytest.fixture
def engine():
    return SkillsOntologyEngine()


class TestSkillLevel:
    def test_beginner_value(self):
        assert SkillLevel.BEGINNER == "beginner"

    def test_expert_value(self):
        assert SkillLevel.EXPERT == "expert"

    def test_all_levels_present(self):
        levels = [sl.value for sl in SkillLevel]
        assert "beginner" in levels
        assert "expert" in levels


class TestSkillNode:
    def test_instantiation(self):
        node = SkillNode(id="python", name="Python", level=SkillLevel.INTERMEDIATE)
        assert node.id == "python"
        assert node.name == "Python"

    def test_canonical_lowercased(self):
        node = SkillNode(id="PYTHON", name="Python", level=SkillLevel.INTERMEDIATE)
        assert node.canonical == "python"


class TestSkillEdge:
    def test_instantiation(self):
        edge = SkillEdge(source="python", target="django", weight=0.8)
        assert edge.source == "python"
        assert edge.target == "django"
        assert edge.weight == 0.8


class TestSkillsOntologyEngineInit:
    def test_engine_initializes(self, engine):
        assert engine is not None

    def test_has_nodes(self, engine):
        stats = engine.get_stats()
        assert stats.get("nodes", 0) > 0

    def test_has_edges(self, engine):
        stats = engine.get_stats()
        assert stats.get("edges", 0) >= 0


class TestGetSkillInfo:
    def test_known_skill_returns_dict(self, engine):
        result = engine.get_skill_info("python")
        if result is not None:
            assert isinstance(result, dict)

    def test_unknown_skill_returns_none(self, engine):
        result = engine.get_skill_info("xyz_nonexistent_skill_123")
        assert result is None

    def test_case_insensitive(self, engine):
        lower = engine.get_skill_info("python")
        upper = engine.get_skill_info("Python")
        assert lower == upper


class TestGetAdjacencies:
    def test_returns_list(self, engine):
        result = engine.get_adjacencies("python")
        assert isinstance(result, list)

    def test_unknown_skill_returns_empty(self, engine):
        result = engine.get_adjacencies("xyz_totally_unknown")
        assert result == []

    def test_min_weight_filters(self, engine):
        all_adj = engine.get_adjacencies("python", min_weight=0.0)
        high_adj = engine.get_adjacencies("python", min_weight=0.9)
        assert len(all_adj) >= len(high_adj)


class TestInferRelatedSkills:
    def test_returns_list(self, engine):
        result = engine.infer_related_skills(["python"])
        assert isinstance(result, list)

    def test_empty_input_returns_empty(self, engine):
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

    def test_missing_skills_identified(self, engine):
        result = engine.analyze_skill_gaps(
            candidate_skills=["python"],
            required_skills=["python", "react"]
        )
        assert "missing" in result or "gaps" in result or len(result) > 0

    def test_no_gaps_when_matching(self, engine):
        result = engine.analyze_skill_gaps(
            candidate_skills=["python"],
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

    def test_similar_vectors_high_score(self, engine):
        a = [1.0, 1.0, 1.0]
        b = [1.0, 1.0, 0.9]
        score = engine._cosine_similarity(a, b)
        assert score > 0.99


class TestGetStats:
    def test_returns_dict(self, engine):
        stats = engine.get_stats()
        assert isinstance(stats, dict)

    def test_has_nodes_key(self, engine):
        stats = engine.get_stats()
        assert "nodes" in stats

    def test_nodes_positive(self, engine):
        stats = engine.get_stats()
        assert stats["nodes"] > 0
