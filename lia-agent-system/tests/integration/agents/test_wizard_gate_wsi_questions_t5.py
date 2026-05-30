"""Sentinela offline — T5 (Task #1087) — wizard wsi_questions gate (LLM-based).

Mirrors o padrão de ``test_wizard_gate_competency_t4.py`` para o stage
``wsi_questions`` (HITL #2 — aprovar/regenerar/editar/adicionar/remover
perguntas WSI).

Cobertura:
  S1  — STAGE_ALLOWLISTS["wsi_questions"] contém exatamente os 6 intents.
  S2  — graph builder com use_llm_gates=False NÃO inclui wsi_questions_gate.
  S3  — graph builder com use_llm_gates=True INCLUI wsi_questions_gate.
  S4  — wsi_questions_gate_node sem mensagem nova → no-op (END).
  S5  — intent=approve_all → questions_approved=True + route=eligibility.
  S6  — intent=regenerate_all → questions_approved=False +
        wsi_regenerate_pending=True + wsi_questions=[] + route=wsi_questions.
  S7  — intent=edit_specific_question (idx válido + instruction) →
        edição CIRÚRGICA in-state (Task #1089): pergunta `idx` substituída,
        demais preservadas, wsi_regenerate_pending=False, route=self-loop.
  S8  — intent=edit_specific_question idx FORA do range → clarify
        determinístico, sem mutar pacote, route=END.
  S9  — intent=add_question (topic) → adição CIRÚRGICA (Task #1089):
        pacote incrementado N->N+1, wsi_regenerate_pending=False, route=self-loop.
  S10 — intent=remove_question (idx válido) → splice in-state,
        questions_approved=None, route=END.
  S11 — intent=ask_question → state inalterado em pacote + clarify,
        route=END.
  S12 — confidence < 0.7 → clarify sem mutar pacote, route=END.
  S13 — output do classifier off-allowlist (ex.: "approve" jd-only) →
        fallback determinístico (ask_question / cf=0.0).
  S14 — classifier exception → fallback (route=END), wizard não trava.
  S15 — domain._route_by_stage com flag ON dispatcha para action
        gate_wsi_questions em vez do approve_questions keyword-based.
  S16 — domain._route_by_stage com flag OFF mantém approve_questions
        keyword-based.
  S17 — FairnessGuard L1 bloqueia mensagem discriminatória do recrutador
        no gate wsi_questions.
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

graph_mod = importlib.import_module("app.domains.job_creation.graph")
classifier_mod = importlib.import_module(
    "app.domains.job_creation.services.wizard_gate_classifier"
)


def _make_output(intent, confidence=0.9, reply="ok", extracted=None):
    return classifier_mod.GateClassifierOutput(
        intent=intent,
        extracted_data=extracted or {},
        conversational_reply=reply,
        confidence=confidence,
    )


def _sample_questions(n=7):
    return [{"index": i + 1, "text": f"Q{i+1}", "block": "technical"} for i in range(n)]


class _FakeSurgicalGen:
    """Generator fake para Task #1089 — gera 1 pergunta CBI (edição/adição)."""

    def generate_single_question(self, *, block, enriched, seniority, directive,
                                 base_question=None, trait_rankings=None):
        from app.domains.job_creation.schemas import GeneratedQuestion
        prefix = "EDITADA" if base_question is not None else "NOVA"
        return GeneratedQuestion(
            question=f"{prefix} pergunta CBI sobre {directive} (situação real)?",
            ideal_answer="x", block=block, competency=block, skill="x", framework="CBI",
        )


_JD_ENRICHED_STUB = {
    "titulo_padronizado": "Engenheiro", "senioridade_confirmada": "senior",
    "about_role": "x",
    "skills_obrigatorias": [{"skill": f"S{i}", "contexto": "c"} for i in range(1, 6)],
    "competencias_comportamentais": [
        {"competencia": f"C{i}", "contexto": "c", "trait_big_five": "conscientiousness"} for i in range(1, 4)
    ],
}


class WizardWsiQuestionsGateT5(unittest.TestCase):

    # ---------------- S1 ----------------
    def test_S1_stage_allowlist_wsi_questions_canonical(self):
        allow = classifier_mod.get_allowed_intents("wsi_questions")
        self.assertEqual(
            set(allow),
            {
                "approve_all",
                "regenerate_all",
                "edit_specific_question",
                "add_question",
                "remove_question",
                "ask_question",
            },
        )
        # jd_enrichment / competency intents NÃO devem vazar.
        self.assertNotIn("approve", allow)
        self.assertNotIn("select_compact", allow)
        self.assertNotIn("undecided", allow)

    # ---------------- S2 / S3 ----------------
    def test_S2_builder_off_excludes_wsi_questions_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=False)
        self.assertNotIn("wsi_questions_gate", builder.nodes)

    def test_S3_builder_on_includes_wsi_questions_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=True)
        self.assertIn("wsi_questions_gate", builder.nodes)

    # ---------------- S4 ----------------
    def test_S4_no_resume_message_is_noop(self):
        state = {"current_stage": "wsi_questions", "wsi_questions": _sample_questions()}
        result = graph_mod.wsi_questions_gate_node(state)
        self.assertEqual(result.get("current_stage"), "wsi_questions")
        self.assertIsNone(result.get("questions_approved"))
        # Sprint F.2 fix — no resume + non-terminal self-loops to interrupt()
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S5 ----------------
    def test_S5_approve_all_sets_approved(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("approve_all", 0.95, "Aprovado! Vou seguir.")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "tá bom, manda ver",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        self.assertIs(result["questions_approved"], True)
        self.assertEqual(result["gate_last_intent"], "approve_all")
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "eligibility")

    # ---------------- S6 ----------------
    def test_S6_regenerate_all_sets_pending(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("regenerate_all", 0.92, "Vou regenerar agora.")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "refaz tudo",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        self.assertIs(result["questions_approved"], False)
        self.assertEqual(result["wsi_questions"], [])
        self.assertIs(result["wsi_regenerate_pending"], True)
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions")

    # ---------------- S7 ----------------
    def test_S7_edit_specific_question_valid(self):
        # Task #1089 — edição CIRÚRGICA: substitui só a pergunta `idx`, preserva as demais.
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "edit_specific_question", 0.92, "Vou ajustar a 3.",
            extracted={"question_index": 3, "instruction": "deixar mais técnica"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)), \
             mock.patch.object(graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None), \
             mock.patch.object(graph_mod, "_get_wsi_generator", return_value=_FakeSurgicalGen()):
            state = {
                "gate_resume_message": "mexe na pergunta 3, deixa mais técnica",
                "current_stage": "wsi_questions",
                "screening_mode": "compact",
                "seniority_resolved": "senior",
                "jd_enriched": _JD_ENRICHED_STUB,
                "wsi_questions": _sample_questions(),
            }
            result = graph_mod.wsi_questions_gate_node(state)
        qs = result["wsi_questions"]
        self.assertEqual(len(qs), 7, "tamanho do pacote preservado (cirúrgico)")
        self.assertIn("EDITADA", qs[2]["question"], "pergunta 3 substituída")
        # Demais preservadas mantêm o shape original (_sample_questions usa text).
        self.assertEqual(qs[0].get("text"), "Q1", "pergunta 1 preservada")
        self.assertEqual(qs[6].get("text"), "Q7", "pergunta 7 preservada")
        self.assertIs(result.get("wsi_regenerate_pending"), False)
        self.assertIsNone(result.get("questions_approved"))
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S8 ----------------
    def test_S8_edit_specific_question_out_of_range_clarifies(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "edit_specific_question", 0.9, "vou ajustar",
            extracted={"question_index": 99, "instruction": "muda"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "edita a 99",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        # Não muta pacote.
        self.assertEqual(len(result.get("wsi_questions") or []), 7)
        self.assertNotIn("wsi_questions_pending_edit", {k: v for k, v in result.items() if v})
        self.assertIn("Qual pergunta", result["gate_clarify_message"])
        # Sprint F.2 fix — clarify self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S9 ----------------
    def test_S9_add_question_sets_pending_add(self):
        # Task #1089 — adição CIRÚRGICA: incrementa o pacote N->N+1, preserva as demais.
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "add_question", 0.93, "Vou acrescentar.",
            extracted={"topic": "liderança"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)), \
             mock.patch.object(graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None), \
             mock.patch.object(graph_mod, "_get_wsi_generator", return_value=_FakeSurgicalGen()):
            state = {
                "gate_resume_message": "adiciona uma sobre liderança",
                "current_stage": "wsi_questions",
                "screening_mode": "compact",
                "seniority_resolved": "senior",
                "jd_enriched": _JD_ENRICHED_STUB,
                "wsi_questions": _sample_questions(),
            }
            result = graph_mod.wsi_questions_gate_node(state)
        qs = result["wsi_questions"]
        self.assertEqual(len(qs), 8, "add incrementa de 7 para 8")
        self.assertTrue(any("NOVA" in q.get("question", "") for q in qs))
        self.assertIs(result.get("wsi_regenerate_pending"), False)
        self.assertIsNone(result.get("questions_approved"))
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S10 ----------------
    def test_S10_remove_question_splices_in_place(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "remove_question", 0.95, "Removendo.",
            extracted={"question_index": 5},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "tira a 5",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(7),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        self.assertEqual(len(result["wsi_questions"]), 6)
        # Q5 deve ter sido removida.
        labels = [q.get("text") for q in result["wsi_questions"]]
        self.assertNotIn("Q5", labels)
        self.assertIsNone(result["questions_approved"])
        self.assertIs(result.get("wsi_regenerate_pending", False), False)
        # Sprint F.2 fix — reduced package (questions_approved=None) self-loops to await re-approval
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S11 ----------------
    def test_S11_ask_question_does_not_mutate_package(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "ask_question", 0.9,
            "Pelo modo Compacto + Pleno são 5 técnicas + 2 comportamentais.",
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)), \
             mock.patch.object(graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None), \
             mock.patch.object(
                 graph_mod, "_try_meta_helper",
                 return_value="Pelo modo Compacto + Pleno são 5 técnicas + 2 comportamentais.",
             ):
            state = {
                "gate_resume_message": "por que tem só 2 comportamentais?",
                "current_stage": "wsi_questions",
                "wsi_questions": _sample_questions(),
            }
            result = graph_mod.wsi_questions_gate_node(state)
        self.assertEqual(len(result["wsi_questions"]), 7)
        self.assertIsNone(result.get("questions_approved"))
        self.assertEqual(result["gate_last_intent"], "ask_question")
        self.assertIn("Compacto", result["gate_clarify_message"])
        # Sprint F.2 fix — ask_question self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S12 ----------------
    def test_S12_low_confidence_clarifies_without_mutating_package(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("approve_all", 0.5, "Confirma se aprovou mesmo?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "ehh sei la",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        self.assertIsNone(result.get("questions_approved"))
        self.assertEqual(result["gate_last_confidence"], 0.5)
        # Sprint F.2 fix — low confidence self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S13 ----------------
    def test_S13_off_allowlist_intent_falls_back(self):
        async def _run():
            with mock.patch.object(
                classifier_mod.WizardGateClassifier, "_invoke_llm",
                new=mock.AsyncMock(return_value={
                    "intent": "approve",  # válido em jd, off-allowlist em wsi_questions
                    "extracted_data": {},
                    "conversational_reply": "ok",
                    "confidence": 0.99,
                }),
            ):
                clf = classifier_mod.WizardGateClassifier()
                out = await clf.classify(
                    user_message="aprova", stage="wsi_questions", ws_stage_payload=None,
                )
            self.assertEqual(out.intent, "ask_question")
            self.assertEqual(out.confidence, 0.0)

        import asyncio
        asyncio.run(_run())

    # ---------------- S14 ----------------
    def test_S14_classifier_exception_falls_back_to_clarify(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify", new=mock.AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "tá bom",
                    "current_stage": "wsi_questions",
                    "wsi_questions": _sample_questions(),
                }
                result = graph_mod.wsi_questions_gate_node(state)
        self.assertIsNone(result.get("questions_approved"))
        clarify = str(result.get("gate_clarify_message", "")).lower()
        self.assertTrue(
            "aprovar" in clarify or "regenerar" in clarify or "pergunt" in clarify,
            f"expected clarify message com opções, got: {clarify!r}",
        )
        # Sprint F.2 fix — classifier exception falls back to non-terminal → self-loop
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "wsi_questions_gate")

    # ---------------- S15 ----------------
    def test_S15_domain_route_by_stage_dispatches_to_gate_wsi_when_flag_on(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "true"}, clear=False):
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "tá bom, manda ver", "wsi_questions",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "gate_wsi_questions")
        self.assertEqual(decision["params"]["user_query"], "tá bom, manda ver")
        self.assertEqual(decision.get("source"), "llm_gate")

    # ---------------- S16 ----------------
    def test_S16_domain_route_by_stage_keeps_keyword_when_flag_off(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        with mock.patch.dict(
            os.environ,
            {"LIA_WIZARD_LLM_GATES": "0", "LIA_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("ENVIRONMENT", None)
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "aprova tudo", "wsi_questions",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "approve_questions")
        self.assertIs(decision["params"]["approved"], True)

    # ---------------- S17 ----------------
    def test_S17_fairness_guard_blocks_discriminatory_message(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(side_effect=AssertionError(
                "classify NÃO deveria ser chamado quando FairnessGuard bloqueia",
            )),
        ):
            with mock.patch.object(
                graph_mod, "_emit_wsi_questions_gate_audit", lambda *a, **k: None,
            ):
                with mock.patch(
                    "app.shared.compliance.fairness_guard.FairnessGuard"
                ) as _FG:
                    _instance = _FG.return_value
                    _result = mock.MagicMock()
                    _result.is_blocked = True
                    _result.category = "gender"
                    _result.blocked_terms = ["só homens"]
                    _result.educational_message = (
                        "Critérios discriminatórios não são permitidos."
                    )
                    _instance.check.return_value = _result
                    state = {
                        "gate_resume_message": "aprova mas só pergunta pra homens",
                        "current_stage": "wsi_questions",
                        "wsi_questions": _sample_questions(),
                    }
                    result = graph_mod.wsi_questions_gate_node(state)
        self.assertIs(result.get("fairness_blocked"), True)
        self.assertIsNone(result.get("questions_approved"))
        self.assertIn("discrimina", result["gate_clarify_message"].lower())
        self.assertEqual(graph_mod.route_after_wsi_questions_gate(result), "end")


if __name__ == "__main__":
    unittest.main(verbosity=2)
