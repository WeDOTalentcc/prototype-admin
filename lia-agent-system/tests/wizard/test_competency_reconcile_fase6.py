"""TDD Fase 6 — competency_node reconcilia com competências confirmadas.

Quando há confirmed_technical/confirmed_behavioral (Fase 3, consumidas pela
Fase 4), o competency_node monta question_distribution + competency_tree a
partir das CONFIRMADAS reais (respeita edições do recruiter no painel), em
vez de re-derivar do YAML por senioridade. WSI gera ~1 pergunta por
competência confirmada. Sem confirmadas → comportamento legado.

Run:
    cd lia-agent-system && python -m pytest tests/wizard/test_competency_reconcile_fase6.py -v --no-cov
"""
from __future__ import annotations
import sys
import importlib
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

CONFIRMED_TECH_5 = [
    {"skill": "Python", "contexto": "core"},
    {"skill": "PostgreSQL", "contexto": "db"},
    {"skill": "Docker", "contexto": "deploy"},
    {"skill": "FastAPI", "contexto": "api"},
    {"skill": "Git", "contexto": "vcs"},
]
CONFIRMED_BEHAV_2 = [
    {"competencia": "Comunicação", "contexto": "squad", "trait_big_five": "extraversion"},
    {"competencia": "Autonomia", "contexto": "solo", "trait_big_five": "conscientiousness"},
]


def _run_competency(state):
    node_mod = importlib.import_module("app.domains.job_creation.nodes.competency")
    # _emit_wizard_step_audit faz I/O de audit — mock pra isolar.
    # _get_question_distribution só deve ser chamado no path LEGADO.
    with mock.patch("app.domains.job_creation.graph._emit_wizard_step_audit"), \
         mock.patch(
             "app.domains.job_creation.graph._get_question_distribution",
             return_value={"technical": 99, "behavioral": 99},  # sentinela do legado
         ) as mock_legacy:
        result = node_mod.competency_node(state)
    return result, mock_legacy


def _base_state(**overrides):
    base = {
        "jd_enriched": {
            "titulo_padronizado": "Engenheiro de Software",
            "about_role": "Backend.",
            "skills_obrigatorias": [{"skill": "Python", "contexto": "core"}],
            "competencias_comportamentais": [
                {"competencia": "Comunicação", "contexto": "x", "trait_big_five": "extraversion"},
            ],
        },
        "parsed_seniority": "senior",
        "parsed_title": "Engenheiro de Software",
        "screening_mode": "compact",
        "confirmed_technical_competencies": [],
        "confirmed_behavioral_competencies": [],
    }
    base.update(overrides)
    return base


# ── 1. Distribution a partir das confirmadas ─────────────────────────────────

class TestDistributionFromConfirmed:
    def test_distribution_matches_confirmed_counts(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        result, mock_legacy = _run_competency(state)
        dist = result.get("question_distribution")
        assert dist == {"technical": 5, "behavioral": 2}, f"got {dist}"

    def test_legacy_yaml_not_called_when_confirmed(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        _, mock_legacy = _run_competency(state)
        mock_legacy.assert_not_called()

    def test_distribution_respects_recruiter_edits(self):
        """Recruiter editou para 6 téc + 3 comp → distribution reflete (não YAML)."""
        tech6 = CONFIRMED_TECH_5 + [{"skill": "Kafka", "contexto": "stream"}]
        behav3 = CONFIRMED_BEHAV_2 + [
            {"competencia": "Liderança", "contexto": "mentor", "trait_big_five": "extraversion"},
        ]
        state = _base_state(
            confirmed_technical_competencies=tech6,
            confirmed_behavioral_competencies=behav3,
        )
        result, _ = _run_competency(state)
        assert result.get("question_distribution") == {"technical": 6, "behavioral": 3}

    def test_total_questions_equals_confirmed_total(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        result, _ = _run_competency(state)
        dist = result["question_distribution"]
        total = dist["technical"] + dist["behavioral"]
        assert total == len(CONFIRMED_TECH_5) + len(CONFIRMED_BEHAV_2) == 7


# ── 2. Tree a partir das confirmadas ──────────────────────────────────────────

class TestTreeFromConfirmed:
    def test_tree_built_from_confirmed(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        result, _ = _run_competency(state)
        tree = result.get("competency_tree") or []
        assert len(tree) == 7
        tech_nodes = [n for n in tree if n["block"] == "technical"]
        behav_nodes = [n for n in tree if n["block"] == "behavioral"]
        assert len(tech_nodes) == 5
        assert len(behav_nodes) == 2
        skills = [n["skill"] for n in tech_nodes]
        assert "Python" in skills and "Kafka" not in skills

    def test_tree_behavioral_preserves_trait(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        result, _ = _run_competency(state)
        behav = [n for n in result["competency_tree"] if n["block"] == "behavioral"]
        traits = {n["skill"]: n["trait"] for n in behav}
        assert traits["Comunicação"] == "extraversion"
        assert traits["Autonomia"] == "conscientiousness"


# ── 3. Legacy path sem confirmadas ────────────────────────────────────────────

class TestLegacyPath:
    def test_legacy_uses_yaml_distribution(self):
        """Sem confirmadas → usa _get_question_distribution (YAML por senioridade)."""
        state = _base_state()  # confirmed_* vazios
        result, mock_legacy = _run_competency(state)
        mock_legacy.assert_called_once()
        assert result.get("question_distribution") == {"technical": 99, "behavioral": 99}

    def test_legacy_tree_from_jd_enriched(self):
        state = _base_state()
        result, _ = _run_competency(state)
        tree = result.get("competency_tree") or []
        # jd_enriched tem 1 técnica + 1 comportamental
        assert len(tree) == 2

    def test_empty_confirmed_lists_fall_to_legacy(self):
        """confirmed_* presentes mas vazios → legacy (não distribution {0,0})."""
        state = _base_state(
            confirmed_technical_competencies=[],
            confirmed_behavioral_competencies=[],
        )
        result, mock_legacy = _run_competency(state)
        mock_legacy.assert_called_once()


# ── 4. seniority ainda resolvido (não regrediu) ──────────────────────────────

class TestSeniorityStillResolved:
    def test_seniority_resolved_in_confirmed_path(self):
        state = _base_state(
            confirmed_technical_competencies=CONFIRMED_TECH_5,
            confirmed_behavioral_competencies=CONFIRMED_BEHAV_2,
        )
        result, _ = _run_competency(state)
        assert result.get("seniority_resolved")  # truthy (senior resolvido)
