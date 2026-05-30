"""TDD Task #1089 — geração cirúrgica de perguntas WSI (editar/adicionar 1) +
auto-complete até o mínimo do modo. Preserva metodologia WSI (CBI + validação).

Run:
    cd lia-agent-system && python -m pytest tests/unit/test_wsi_surgical_generation.py -v --no-cov
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _enriched(n_tech=8, n_behav=4):
    from app.domains.job_creation.schemas import (
        EnrichedJobDescription, TechnicalSkill, BehavioralCompetency,
    )
    return EnrichedJobDescription(
        titulo_padronizado="Engenheiro de Software",
        senioridade_confirmada="senior",
        about_role="Backend.",
        responsabilidades=["r1", "r2", "r3"],
        skills_obrigatorias=[TechnicalSkill(skill=f"Skill{i}", contexto="x") for i in range(1, n_tech + 1)],
        competencias_comportamentais=[
            BehavioralCompetency(competencia=f"Comp{i}", contexto="x", trait_big_five="conscientiousness")
            for i in range(1, n_behav + 1)
        ],
    )


def _one_question_json(question="Descreva uma situação real onde você liderou um time técnico. Qual foi o resultado?",
                        block="technical", skill="Liderança técnica", trait=None):
    q = {
        "question": question,
        "ideal_answer": "STAR: situação concreta, ações, resultado.",
        "skill": skill,
        "scoring_rubric": {"1-3": "baixo", "4-6": "médio", "7-9": "alto", "10": "máximo"},
        "bloom_level": 4,
        "dreyfus_level": 3,
    }
    if trait:
        q["trait_ocean"] = trait
    return json.dumps({"questions": [q], "block": block})


def _make_generator(llm_json):
    from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator
    gen = WSIQuestionGenerator()
    fake_llm = mock.MagicMock()
    fake_llm.invoke.return_value = SimpleNamespace(content=llm_json)
    # _get_llm devolve o mesmo fake pra qualquer purpose
    gen._get_llm = lambda purpose: fake_llm  # type: ignore
    return gen


def _existing(n_tech, n_behav):
    from app.domains.job_creation.schemas import GeneratedQuestion
    qs = []
    for i in range(n_tech):
        qs.append(GeneratedQuestion(
            question=f"Conte uma situação real em que usou Skill{i+1}.",
            ideal_answer="x", block="technical", competency="technical", skill=f"Skill{i+1}",
        ))
    for i in range(n_behav):
        qs.append(GeneratedQuestion(
            question=f"Conte uma situação real sobre Comp{i+1}.",
            ideal_answer="x", block="behavioral", competency="behavioral",
            skill=f"Comp{i+1}", trait_ocean="conscientiousness",
        ))
    return qs


# ── 1. generate_single_question — edição ─────────────────────────────────────

class TestGenerateSingleQuestionEdit:
    def test_edit_returns_one_validated_question(self):
        from app.domains.job_creation.schemas import GeneratedQuestion
        gen = _make_generator(_one_question_json(block="technical"))
        base = GeneratedQuestion(
            question="Conte sobre Skill1.", ideal_answer="x",
            block="technical", competency="technical", skill="Skill1",
        )
        result = gen.generate_single_question(
            block="technical", enriched=_enriched(), seniority="senior",
            directive="foque em liderança de squad", base_question=base,
        )
        assert result is not None
        assert result.block == "technical"
        assert result.framework == "CBI"
        assert "liderou" in result.question.lower() or "lideran" in result.question.lower()

    def test_edit_rejects_hypothetical_returns_none(self):
        """Se o LLM devolver pergunta hipotética (viola CBI), retorna None (caller mantém original)."""
        gen = _make_generator(_one_question_json(
            question="O que você faria se tivesse um conflito no time?", block="technical",
        ))
        result = gen.generate_single_question(
            block="technical", enriched=_enriched(), seniority="senior",
            directive="x", base_question=None,
        )
        assert result is None, "pergunta hipotética deve falhar validação WSI → None"

    def test_edit_rejects_cultural_fit_returns_none(self):
        gen = _make_generator(_one_question_json(
            question="Você se encaixa na cultura da empresa e valores da empresa?", block="behavioral",
        ))
        result = gen.generate_single_question(
            block="behavioral", enriched=_enriched(), seniority="senior",
            directive="x",
        )
        assert result is None


# ── 2. generate_single_question — adição ─────────────────────────────────────

class TestGenerateSingleQuestionAdd:
    def test_add_returns_one_question(self):
        gen = _make_generator(_one_question_json(
            question="Descreva uma situação real em que liderou uma migração técnica.",
            block="technical", skill="Liderança",
        ))
        result = gen.generate_single_question(
            block="technical", enriched=_enriched(), seniority="senior",
            directive="liderança técnica",
        )
        assert result is not None
        assert result.skill  # skill preenchida


# ── 3. generate_missing_questions — auto-complete até o mínimo ───────────────

class TestGenerateMissingQuestions:
    def test_fills_technical_deficit_to_reach_mode_minimum(self):
        """Compact = 5 téc + 2 comp (=7). Existing 3 téc + 2 comp → faltam 2 téc."""
        gen = _make_generator(_one_question_json(block="technical", skill="NovaSkill"))
        existing = _existing(3, 2)  # 5 total, faltam 2 técnicas
        missing = gen.generate_missing_questions(
            enriched=_enriched(), seniority="senior",
            existing_questions=existing, screening_mode="compact",
        )
        # Deve gerar 2 técnicas faltantes
        assert len(missing) == 2
        assert all(q.block == "technical" for q in missing)

    def test_no_deficit_returns_empty(self):
        """Pacote já no mínimo (5+2=7 compact) → nada a gerar."""
        gen = _make_generator(_one_question_json())
        existing = _existing(5, 2)
        missing = gen.generate_missing_questions(
            enriched=_enriched(), seniority="senior",
            existing_questions=existing, screening_mode="compact",
        )
        assert missing == []

    def test_full_mode_minimum_is_12(self):
        """Full = 8 téc + 4 comp (=12). Existing 8 téc + 2 comp → faltam 2 comp."""
        gen = _make_generator(_one_question_json(block="behavioral", skill="NovaComp", trait="openness"))
        existing = _existing(8, 2)  # 10 total, faltam 2 comportamentais
        missing = gen.generate_missing_questions(
            enriched=_enriched(), seniority="senior",
            existing_questions=existing, screening_mode="full",
        )
        assert len(missing) == 2
        assert all(q.block == "behavioral" for q in missing)
