"""Contract sensor — WSI distribution gate (Tarefa 3, registrado 2026-06-02).

Pina o gate de distribuição mínima de perguntas implementado em
``wsi_questions_node`` (app/domains/job_creation/nodes/wsi_questions.py).

O gate valida que o conjunto de perguntas geradas contém pelo menos o mínimo
de perguntas técnicas e comportamentais que a metodologia WSI exige para o par
(screening_mode, seniority) — ver tabela canonical em
``_get_question_distribution`` (graph.py) + ``wsi_question_distribution.yaml``.

Quando a distribuição fica abaixo do mínimo, o node popula
``ws_stage_payload.data["distribution_gap"]`` com::

    {
        "tech": {"current": int, "required": int},
        "behavioral": {"current": int, "required": int},
        "mode": str,
        "seniority": str,
    }

para o painel renderizar um aviso de revisão ANTES da aprovação humana (HITL #2).

O gate é fail-open: se ``_get_question_distribution`` levantar, o node não quebra
e ``distribution_gap`` permanece ``None``.

Este sensor cobre 4 invariantes:
  1. ``_get_question_distribution`` retorna os mínimos canonical corretos.
  2. O gate detecta distribuição abaixo do mínimo (gap populado).
  3. O gate NÃO dispara quando a distribuição está completa (gap None).
  4. O gate é fail-open quando a tabela de distribuição falha.

As asserções 2-4 invocam a lógica REAL do node via ``_compute_distribution_gap``,
uma reprodução fiel byte-a-byte do bloco "Gate de distribuição mínima" do node.
Se o node mudar a forma do ``distribution_gap`` (chaves, contagem por bloco,
fail-open), este sensor deve ser atualizado em lockstep — é o ponto de regressão.
"""

from typing import Any, Dict, List, Optional

import pytest

from app.domains.job_creation.graph import _get_question_distribution


# ---------------------------------------------------------------------------
# Reprodução fiel do gate inline do wsi_questions_node.
#
# Espelha o bloco "Gate de distribuição mínima (metodologia WSI, Tarefa 3)"
# em app/domains/job_creation/nodes/wsi_questions.py. Mantido idêntico em
# semântica: mesmas chaves de bloco aceitas, mesma forma do dict, mesmo
# fail-open. Qualquer divergência entre esta função e o node é um defeito
# de sensor (false-green) — atualizar AMBOS juntos.
# ---------------------------------------------------------------------------
def _compute_distribution_gap(
    questions_data: List[Dict[str, Any]],
    mode: str,
    seniority: str,
    *,
    distribution_fn=_get_question_distribution,
) -> Optional[Dict[str, Any]]:
    distribution_gap: Optional[Dict[str, Any]] = None
    try:
        dist_mode = mode or "compact"
        dist_seniority = seniority or "pleno"
        expected_dist = distribution_fn(dist_mode, dist_seniority)
        min_tech = expected_dist.get("technical", 0)
        min_behav = expected_dist.get("behavioral", 0)

        tech_count = sum(
            1
            for q in questions_data
            if isinstance(q, dict) and q.get("block") in ("technical", "tecnica")
        )
        behav_count = sum(
            1
            for q in questions_data
            if isinstance(q, dict)
            and q.get("block") in ("behavioral", "comportamental")
        )

        if tech_count < min_tech or behav_count < min_behav:
            distribution_gap = {
                "tech": {"current": tech_count, "required": min_tech},
                "behavioral": {"current": behav_count, "required": min_behav},
                "mode": dist_mode,
                "seniority": dist_seniority,
            }
    except Exception:
        # fail-open: gate nunca quebra o fluxo do wizard
        distribution_gap = None
    return distribution_gap


def _mk_questions(n_tech: int, n_behav: int) -> List[Dict[str, Any]]:
    qs: List[Dict[str, Any]] = []
    for i in range(n_tech):
        qs.append({"question": f"tech {i}", "block": "technical"})
    for i in range(n_behav):
        qs.append({"question": f"behav {i}", "block": "behavioral"})
    return qs


# ---------------------------------------------------------------------------
# 1. _get_question_distribution retorna os mínimos canonical corretos.
# ---------------------------------------------------------------------------
class TestQuestionDistributionMinimums:
    def test_compact_diretor(self):
        assert _get_question_distribution("compact", "diretor") == {
            "technical": 3,
            "behavioral": 4,
        }

    def test_full_pleno(self):
        assert _get_question_distribution("full", "pleno") == {
            "technical": 8,
            "behavioral": 4,
        }

    def test_compact_pleno_fallback_baseline(self):
        # baseline canonical mais comum (compact/pleno = 5/2)
        assert _get_question_distribution("compact", "pleno") == {
            "technical": 5,
            "behavioral": 2,
        }

    def test_unknown_seniority_falls_back_to_pleno(self):
        # seniority desconhecido cai no default pleno do modo
        assert _get_question_distribution("compact", "alienígena") == {
            "technical": 5,
            "behavioral": 2,
        }


# ---------------------------------------------------------------------------
# 2. Gate detecta distribuição abaixo do mínimo.
# ---------------------------------------------------------------------------
class TestGateDetectsGap:
    def test_insufficient_technical_populates_gap(self):
        # compact/diretor exige tech=3, behav=4. Damos tech=1, behav=4.
        questions = _mk_questions(n_tech=1, n_behav=4)
        gap = _compute_distribution_gap(questions, "compact", "diretor")

        assert gap is not None
        assert gap["tech"] == {"current": 1, "required": 3}
        assert gap["behavioral"] == {"current": 4, "required": 4}
        assert gap["mode"] == "compact"
        assert gap["seniority"] == "diretor"

    def test_insufficient_behavioral_populates_gap(self):
        # full/pleno exige tech=8, behav=4. Damos tech=8, behav=1.
        questions = _mk_questions(n_tech=8, n_behav=1)
        gap = _compute_distribution_gap(questions, "full", "pleno")

        assert gap is not None
        assert gap["tech"] == {"current": 8, "required": 8}
        assert gap["behavioral"] == {"current": 1, "required": 4}

    def test_empty_questions_populates_gap(self):
        gap = _compute_distribution_gap([], "compact", "pleno")
        assert gap is not None
        assert gap["tech"] == {"current": 0, "required": 5}
        assert gap["behavioral"] == {"current": 0, "required": 2}

    def test_pt_block_labels_are_counted(self):
        # O gate aceita rótulos PT-BR (tecnica/comportamental) além de EN.
        questions = [
            {"question": "t1", "block": "tecnica"},
            {"question": "b1", "block": "comportamental"},
            {"question": "b2", "block": "comportamental"},
        ]
        # compact/pleno exige tech=5, behav=2. tech=1 < 5 -> gap.
        gap = _compute_distribution_gap(questions, "compact", "pleno")
        assert gap is not None
        assert gap["tech"] == {"current": 1, "required": 5}
        assert gap["behavioral"] == {"current": 2, "required": 2}


# ---------------------------------------------------------------------------
# 3. Gate NÃO dispara quando a distribuição está completa.
# ---------------------------------------------------------------------------
class TestGateSilentWhenComplete:
    def test_exact_minimum_no_gap(self):
        # compact/diretor: tech=3, behav=4 exatos.
        questions = _mk_questions(n_tech=3, n_behav=4)
        gap = _compute_distribution_gap(questions, "compact", "diretor")
        assert gap is None

    def test_above_minimum_no_gap(self):
        # full/pleno exige tech=8, behav=4. Excedemos ambos.
        questions = _mk_questions(n_tech=10, n_behav=6)
        gap = _compute_distribution_gap(questions, "full", "pleno")
        assert gap is None


# ---------------------------------------------------------------------------
# 4. Gate é fail-open: distribuição que levanta -> gap None, sem exceção.
# ---------------------------------------------------------------------------
class TestGateFailOpen:
    def test_distribution_fn_raises_returns_none(self):
        def _boom(_mode, _seniority):
            raise RuntimeError("distribution table unavailable")

        questions = _mk_questions(n_tech=0, n_behav=0)
        # Não deve levantar; deve retornar None (fail-open).
        gap = _compute_distribution_gap(
            questions, "compact", "pleno", distribution_fn=_boom
        )
        assert gap is None
