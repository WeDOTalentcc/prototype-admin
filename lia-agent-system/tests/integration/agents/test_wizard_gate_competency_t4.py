"""Sentinela offline — T4 (Task #1086) — wizard competency gate (LLM-based).

Mirrors o padrão de ``test_wizard_gate_engine_t2.py`` para o stage
``competency`` (escolha de modo de triagem WSI: compact vs full).

Cobertura:
  S1  — STAGE_ALLOWLISTS["competency"] contém exatamente os 4 intents.
  S2  — graph builder com use_llm_gates=False NÃO inclui competency_gate.
  S3  — graph builder com use_llm_gates=True INCLUI competency_gate.
  S4  — competency_gate_node sem mensagem nova → no-op (END).
  S5  — intent=select_compact (mock) → screening_mode="compact" + route=wsi_questions.
  S6  — intent=select_full → screening_mode="full" + route=wsi_questions.
  S7  — intent=ask_question → state inalterado em screening_mode + clarify
        com recomendação por seniority.
  S8  — intent=undecided → state inalterado em screening_mode + clarify.
  S9  — confidence < 0.7 → re-pergunta sem mutar screening_mode.
  S10 — output do classifier off-allowlist (ex.: "approve" no stage
        competency) → fallback determinístico (ask_question / cf=0.0).
  S11 — classifier exception → fallback (route=END), wizard não trava.
  S12 — domain._route_by_stage com flag ON dispatcha para action
        gate_competency em vez do classifier brittle keyword-based.
  S13 — FairnessGuard L1 bloqueia mensagem discriminatória do recrutador
        no gate competency.
"""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Permite rodar standalone (sem PYTHONPATH externo).
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]  # .../lia-agent-system
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


class WizardCompetencyGateT4(unittest.TestCase):

    # ---------------- S1 ----------------
    def test_S1_stage_allowlist_competency_canonical(self):
        allow = classifier_mod.get_allowed_intents("competency")
        self.assertEqual(
            set(allow),
            {"select_compact", "select_full", "ask_question", "undecided"},
        )
        # jd_enrichment intents NÃO devem vazar para competency.
        self.assertNotIn("approve", allow)
        self.assertNotIn("reject_with_feedback", allow)

    # ---------------- S2 / S3 ----------------
    def test_S2_builder_off_excludes_competency_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=False)
        self.assertNotIn("competency_gate", builder.nodes)

    def test_S3_builder_on_includes_competency_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=True)
        self.assertIn("competency_gate", builder.nodes)

    # ---------------- S4 ----------------
    def test_S4_no_resume_message_is_noop(self):
        state = {"current_stage": "competency", "seniority_resolved": "pleno"}
        result = graph_mod.competency_gate_node(state)
        self.assertEqual(result.get("current_stage"), "competency")
        self.assertNotIn("screening_mode", result)
        # Sprint F.2 fix — non-terminal (no mode + no fairness block) self-loops
        self.assertEqual(graph_mod.route_after_competency_gate(result), "competency_gate")

    # ---------------- S5 ----------------
    def test_S5_select_compact_sets_screening_mode(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "select_compact", 0.95,
            "Show, modo Compacto (7 perguntas). Vou gerar agora.",
            extracted={"mode": "compact"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "vamos com o curto",
                    "current_stage": "competency",
                    "seniority_resolved": "pleno",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertEqual(result["screening_mode"], "compact")
        self.assertEqual(result["gate_last_intent"], "select_compact")
        self.assertEqual(result["gate_resume_message"], "")
        self.assertEqual(graph_mod.route_after_competency_gate(result), "wsi_questions")

    # ---------------- S6 ----------------
    def test_S6_select_full_sets_screening_mode(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "select_full", 0.95,
            "Beleza, modo Completo (12 perguntas). Vou gerar agora.",
            extracted={"mode": "full"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "manda o de 12",
                    "current_stage": "competency",
                    "seniority_resolved": "senior",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertEqual(result["screening_mode"], "full")
        self.assertEqual(result["gate_last_intent"], "select_full")
        self.assertEqual(graph_mod.route_after_competency_gate(result), "wsi_questions")

    # ---------------- S7 ----------------
    def test_S7_ask_question_does_not_mutate_mode_and_recommends(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "ask_question", 0.9,
            "Pra Pleno eu recomendo o Compacto (7 perguntas). Quer ir de Compacto?",
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "qual você recomenda pra Pleno?",
                    "current_stage": "competency",
                    "seniority_resolved": "pleno",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertNotIn("screening_mode", result)  # não muta
        self.assertEqual(result["gate_last_intent"], "ask_question")
        self.assertIn("Compacto", result["gate_clarify_message"])
        # Sprint F.2 fix — ask_question self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_competency_gate(result), "competency_gate")

    # ---------------- S8 ----------------
    def test_S8_undecided_does_not_mutate_mode_and_provides_default(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        # LLM omite reply → o gate cai no fallback determinístico que
        # contém a recomendação por seniority.
        out = _make_output("undecided", 0.85, "")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "deixa em aberto por enquanto",
                    "current_stage": "competency",
                    "seniority_resolved": "junior",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertNotIn("screening_mode", result)
        self.assertEqual(result["gate_last_intent"], "undecided")
        # Recomendação por seniority junior → Compacto.
        self.assertIn("Compacto", result["gate_clarify_message"])
        # Sprint F.2 fix — undecided self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_competency_gate(result), "competency_gate")

    # ---------------- S9 ----------------
    def test_S9_low_confidence_clarifies_without_mutating_mode(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("select_compact", 0.5, "Confirma se é compacto mesmo?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "ehh sei la",
                    "current_stage": "competency",
                    "seniority_resolved": "senior",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertNotIn("screening_mode", result)
        self.assertEqual(result["gate_last_confidence"], 0.5)
        # Sprint F.2 fix — low confidence self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_competency_gate(result), "competency_gate")

    # ---------------- S10 ----------------
    def test_S10_off_allowlist_intent_falls_back(self):
        # O classifier deve rejeitar "approve" (válido em jd_enrichment) no
        # stage competency e cair no fallback ask_question/0.0.
        async def _run():
            with mock.patch.object(
                classifier_mod.WizardGateClassifier, "_invoke_llm",
                new=mock.AsyncMock(return_value={
                    "intent": "approve",  # válido em jd, off-allowlist em competency
                    "extracted_data": {},
                    "conversational_reply": "ok",
                    "confidence": 0.99,
                }),
            ):
                clf = classifier_mod.WizardGateClassifier()
                out = await clf.classify(
                    user_message="aprova", stage="competency", ws_stage_payload=None,
                )
            self.assertEqual(out.intent, "ask_question")
            self.assertEqual(out.confidence, 0.0)

        import asyncio
        asyncio.run(_run())

    # ---------------- S11 ----------------
    def test_S11_classifier_exception_falls_back_to_clarify(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify", new=mock.AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                state = {
                    "gate_resume_message": "vamos com o curto",
                    "current_stage": "competency",
                    "seniority_resolved": "pleno",
                }
                result = graph_mod.competency_gate_node(state)
        self.assertNotIn("screening_mode", result)
        clarify = str(result.get("gate_clarify_message", "")).lower()
        self.assertTrue(
            "compacto" in clarify or "completo" in clarify or "perguntas" in clarify,
            f"expected clarify message com modos, got: {clarify!r}",
        )
        # Sprint F.2 fix — classifier exception falls back to ask_question (non-terminal) → self-loop
        self.assertEqual(graph_mod.route_after_competency_gate(result), "competency_gate")

    # ---------------- S12 ----------------
    def test_S12_domain_route_by_stage_dispatches_to_gate_competency_when_flag_on(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "true"}, clear=False):
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "vamos com o compacto", "competency",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "gate_competency")
        self.assertEqual(decision["params"]["user_query"], "vamos com o compacto")
        self.assertEqual(decision.get("source"), "llm_gate")

    def test_S12b_domain_route_by_stage_keeps_keyword_when_flag_off(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        # Garantir flag OFF E ambiente prod (default OFF) — usa LIA_ENV=production.
        with mock.patch.dict(
            os.environ,
            {"LIA_WIZARD_LLM_GATES": "0", "LIA_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("ENVIRONMENT", None)
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "vamos com o compacto", "competency",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "set_screening_mode")
        self.assertEqual(decision["params"]["mode"], "compact")

    # ---------------- S13 ----------------
    def test_S13_fairness_guard_blocks_discriminatory_message(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        # Importante: mockamos classify para garantir que NÃO é chamado
        # (FairnessGuard L1 deve interceptar antes do classifier).
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(side_effect=AssertionError(
                "classify NÃO deveria ser chamado quando FairnessGuard bloqueia",
            )),
        ):
            with mock.patch.object(
                graph_mod, "_emit_competency_gate_audit", lambda *a, **k: None,
            ):
                # Mock FairnessGuard para retornar bloqueio determinístico.
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
                        "gate_resume_message": "manda compact mas só homens",
                        "current_stage": "competency",
                    }
                    result = graph_mod.competency_gate_node(state)
        self.assertIs(result.get("fairness_blocked"), True)
        self.assertNotIn("screening_mode", result)
        self.assertIn("discrimina", result["gate_clarify_message"].lower())
        self.assertEqual(graph_mod.route_after_competency_gate(result), "end")


if __name__ == "__main__":
    unittest.main(verbosity=2)
