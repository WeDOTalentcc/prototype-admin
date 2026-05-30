"""TDD — gate WSI cirúrgico (Task #1089) + hard gate de mínimo + auto-complete.

edit/add deixam de fazer full-regen e passam a operar in-state (preservando
as demais perguntas). approve_all abaixo do mínimo do modo (7/12) NÃO aprova:
auto-completa e pede re-aprovação. remove abaixo do mínimo avisa.

Run:
    cd lia-agent-system && python -m pytest tests/wizard/test_wsi_gate_surgical_fase6.py -v --no-cov
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

graph_mod = importlib.import_module("app.domains.job_creation.graph")
classifier_mod = importlib.import_module(
    "app.domains.job_creation.services.wizard_gate_classifier"
)


def _out(intent, confidence=0.95, reply="ok", extracted=None):
    return classifier_mod.GateClassifierOutput(
        intent=intent, extracted_data=extracted or {},
        conversational_reply=reply, confidence=confidence,
    )


def _q(i, block="technical"):
    return {
        "question": f"Conte uma situação real sobre {block} {i}.",
        "ideal_answer": "x", "block": block, "competency": block,
        "skill": f"S{i}", "trait_ocean": "conscientiousness" if block == "behavioral" else None,
        "scoring_rubric": {}, "framework": "CBI", "weight": 1.0,
    }


def _pack(n_tech, n_behav):
    qs = [_q(i, "technical") for i in range(1, n_tech + 1)]
    qs += [_q(i, "behavioral") for i in range(1, n_behav + 1)]
    return qs


class _FakeGen:
    def generate_single_question(self, *, block, enriched, seniority, directive,
                                 base_question=None, trait_rankings=None):
        from app.domains.job_creation.schemas import GeneratedQuestion
        return GeneratedQuestion(
            question=f"NOVA pergunta CBI sobre {directive} (situação real)?",
            ideal_answer="x", block=block, competency=block, skill="nova", framework="CBI",
        )

    def generate_missing_questions(self, *, enriched, seniority, existing_questions,
                                   screening_mode, trait_rankings=None):
        from app.domains.job_creation.schemas import GeneratedQuestion
        from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
        total = SCREENING_MODE_CONFIG[screening_mode]["total_questions"]
        deficit = max(0, total - len(existing_questions))
        return [
            GeneratedQuestion(question=f"AUTO {i} situação real?", ideal_answer="x",
                              block="technical", competency="technical", skill=f"auto{i}", framework="CBI")
            for i in range(deficit)
        ]

    def _fallback_questions(self, block, count):
        from app.domains.job_creation.schemas import GeneratedQuestion
        return [GeneratedQuestion(question="fallback situação real?", ideal_answer="x",
                                  block=block, competency=block, skill="fb", framework="CBI")]


def _run(intent, state_extra, extracted=None, reply="ok"):
    clf = classifier_mod.get_wizard_gate_classifier()
    out = _out(intent, extracted=extracted, reply=reply)
    base = {
        "gate_resume_message": "msg do recrutador",
        "current_stage": "wsi_questions",
        "screening_mode": "compact",
        "jd_enriched": {
            "titulo_padronizado": "Engenheiro", "senioridade_confirmada": "senior",
            "about_role": "x", "skills_obrigatorias": [{"skill": f"S{i}", "contexto": "c"} for i in range(1, 10)],
            "competencias_comportamentais": [{"competencia": f"C{i}", "contexto": "c", "trait_big_five": "conscientiousness"} for i in range(1, 6)],
        },
        "seniority_resolved": "senior",
    }
    base.update(state_extra)
    with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)), \
         mock.patch.object(graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None), \
         mock.patch.object(graph_mod, "_get_wsi_generator", return_value=_FakeGen()):
        return graph_mod.wsi_questions_gate_node(base)


# ── edit cirúrgico ────────────────────────────────────────────────────────────

class TestEditSurgical:
    def test_edit_replaces_in_place_preserves_others(self):
        result = _run("edit_specific_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"question_index": 3, "instruction": "mais foco em arquitetura"})
        qs = result["wsi_questions"]
        assert len(qs) == 7, "não pode mudar o tamanho do pacote"
        assert "NOVA pergunta" in qs[2]["question"], "pergunta 3 substituída cirurgicamente"
        assert "NOVA pergunta" not in qs[0]["question"], "outras preservadas"

    def test_edit_no_full_regen(self):
        result = _run("edit_specific_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"question_index": 3, "instruction": "x"})
        assert result.get("wsi_regenerate_pending") is False
        assert result.get("questions_approved") is None
        assert result.get("wsi_questions") != []

    def test_edit_routes_self_loop_for_reapproval(self):
        result = _run("edit_specific_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"question_index": 3, "instruction": "x"})
        assert graph_mod.route_after_wsi_questions_gate(result) == "wsi_questions_gate"


# ── add cirúrgico (incrementa) ────────────────────────────────────────────────

class TestAddSurgical:
    def test_add_increments_pack(self):
        result = _run("add_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"topic": "liderança de squad"})
        qs = result["wsi_questions"]
        assert len(qs) == 8, "add deve incrementar de 7 para 8"
        assert any("NOVA pergunta" in q["question"] for q in qs)

    def test_add_no_full_regen(self):
        result = _run("add_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"topic": "kubernetes"})
        assert result.get("wsi_regenerate_pending") is False
        assert result.get("questions_approved") is None


# ── approve hard gate + auto-complete ─────────────────────────────────────────

class TestApproveHardGate:
    def test_approve_full_pack_approves(self):
        result = _run("approve_all", {"wsi_questions": _pack(5, 2)})  # 7 == min compact
        assert result.get("questions_approved") is True
        assert graph_mod.route_after_wsi_questions_gate(result) == "eligibility"

    def test_approve_below_min_does_not_approve(self):
        result = _run("approve_all", {"wsi_questions": _pack(3, 2)})  # 5 < 7
        assert result.get("questions_approved") is not True, "hard gate: não aprova abaixo do mínimo"

    def test_approve_below_min_auto_completes(self):
        result = _run("approve_all", {"wsi_questions": _pack(3, 2)})  # 5 < 7 → completa p/ 7
        qs = result["wsi_questions"]
        assert len(qs) == 7, f"deve auto-completar até o mínimo (7), got {len(qs)}"
        assert result.get("questions_approved") is None
        assert graph_mod.route_after_wsi_questions_gate(result) == "wsi_questions_gate"

    def test_approve_full_mode_min_is_12(self):
        result = _run("approve_all", {"wsi_questions": _pack(8, 2), "screening_mode": "full"})  # 10 < 12
        assert result.get("questions_approved") is not True
        assert len(result["wsi_questions"]) == 12


# ── remove avisa abaixo do mínimo ─────────────────────────────────────────────

class TestRemoveBelowMin:
    def test_remove_below_min_warns(self):
        result = _run("remove_question", {"wsi_questions": _pack(5, 2)},
                      extracted={"question_index": 1})  # 7 -> 6 < 7
        assert len(result["wsi_questions"]) == 6
        msg = (result.get("gate_clarify_message") or "").lower()
        assert "mínimo" in msg or "minimo" in msg or "complet" in msg, f"deve avisar do mínimo: {msg!r}"
