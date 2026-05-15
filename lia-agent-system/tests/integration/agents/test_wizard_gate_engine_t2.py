"""Sentinela offline — T2 (Task #1085) — wizard gate engine LLM-based.

Pytest collection no diretório `app/domains/__init__.py` trava em alguns
ambientes; este sentinela usa importlib direto para os módulos relevantes.
Para rodar standalone fora do pytest:

    python lia-agent-system/tests/integration/agents/test_wizard_gate_engine_t2.py

Cobertura:
  S1 — feature flag LIA_WIZARD_LLM_GATES respeita 1/0/true/false; default
       em prod = OFF (preserva comportamento legacy de route_after_jd).
  S2 — graph builder com use_llm_gates=False NÃO inclui jd_gate node.
  S3 — graph builder com use_llm_gates=True INCLUI jd_gate e roteia
       jd_enrichment → jd_gate.
  S4 — jd_gate_node sem gate_resume_message → no-op (END).
  S5 — jd_gate_node com intent=approve (mock classifier) → jd_approved=True.
  S6 — intent=reject_with_feedback → jd_approved=False + feedback persistido.
  S7 — intent=provide_new_content → jd_approved=False + raw_input substituído
       + jd_enriched=None (cache invalidado) + route_after_gate→intake.
  S8 — intent=ask_question → state inalterado em jd_approved + clarify msg.
  S9 — confidence < 0.7 → re-pergunta sem mutar jd_approved.
  S10 — output do classifier off-allowlist → fallback determinístico.
  S11 — classifier timeout/exception → fallback (clarify message), wizard
        não trava.
  S12 — domain._route_by_stage com flag ON dispatcha para action gate_jd
        em vez do classifier brittle keyword-based.
  S13 — FairnessGuard L1 bloqueia mensagem discriminatória do recrutador
        no gate (ex.: "aprova mas só candidatos masculinos").
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


class WizardGateEngineT2(unittest.TestCase):

    # ---------------- S1 ----------------
    def test_S1_feature_flag_parses_correctly(self):
        for raw, expected in [
            ("1", True), ("true", True), ("TRUE", True), ("on", True), ("yes", True),
            ("0", False), ("false", False), ("off", False), ("no", False),
        ]:
            with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": raw}, clear=False):
                self.assertEqual(
                    graph_mod._llm_gates_enabled(), expected,
                    f"flag={raw!r} expected {expected}",
                )

    def test_S1b_default_inferred_by_environment(self):
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "", "LIA_ENV": "production"}, clear=False):
            os.environ.pop("ENVIRONMENT", None)
            self.assertFalse(graph_mod._llm_gates_enabled())
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "", "LIA_ENV": "development"}, clear=False):
            os.environ.pop("ENVIRONMENT", None)
            self.assertTrue(graph_mod._llm_gates_enabled())

    # ---------------- S2 / S3 ----------------
    def test_S2_builder_off_excludes_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=False)
        self.assertNotIn("jd_gate", builder.nodes)

    def test_S3_builder_on_includes_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=True)
        self.assertIn("jd_gate", builder.nodes)

    # ---------------- S4 ----------------
    def test_S4_no_resume_message_is_noop(self):
        state = {"raw_input": "criar vaga PM senior"}
        result = graph_mod.jd_gate_node(state)
        self.assertEqual(result.get("current_stage"), "jd_enrichment")
        self.assertNotIn("jd_approved", result)
        self.assertEqual(graph_mod.route_after_gate(result), "end")

    # ---------------- S5 ----------------
    def test_S5_approve_intent_mutates_jd_approved_true(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(return_value=_make_output("approve", 0.95, "Combinado!")),
        ):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {
                    "gate_resume_message": "manda bala",
                    "jd_quality_score": 80.0,
                    "ws_stage_payload": {"data": {"parsed_title": "PM"}},
                }
                result = graph_mod.jd_gate_node(state)
        self.assertIs(result["jd_approved"], True)
        self.assertEqual(result["gate_last_intent"], "approve")
        self.assertEqual(result["gate_resume_message"], "")
        self.assertEqual(graph_mod.route_after_gate(result), "bigfive")

    # ---------------- S6 ----------------
    def test_S6_reject_with_feedback_persists_feedback(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "reject_with_feedback", 0.9,
            "Beleza, vou revisar a parte de skills.",
            extracted={"feedback": "ajustar seção de skills"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {"gate_resume_message": "calma, refaz só skills"}
                result = graph_mod.jd_gate_node(state)
        self.assertIs(result["jd_approved"], False)
        self.assertIn("skills", result["jd_rejection_feedback"].lower())
        self.assertEqual(graph_mod.route_after_gate(result), "end")

    # ---------------- S7 ----------------
    def test_S7_provide_new_content_invalidates_cache_and_routes_to_intake(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        new_jd = "Engenheiro Backend Pleno: Python, FastAPI, AWS, microsserviços." * 5
        out = _make_output(
            "provide_new_content", 0.95, "Recebi, vou re-enriquecer.",
            extracted={"new_content": new_jd},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {
                    "gate_resume_message": "olha, na verdade é isso aqui: ...",
                    "jd_enriched": {"title": "old"},
                    "raw_input": "old raw",
                    "jd_quality_score": 70.0,
                }
                result = graph_mod.jd_gate_node(state)
        self.assertIs(result["jd_approved"], False)
        self.assertEqual(result["jd_enriched"], None)
        self.assertEqual(result["jd_quality_score"], 0.0)
        self.assertIn("Backend", result["raw_input"])
        self.assertEqual(graph_mod.route_after_gate(result), "intake")

    # ---------------- S8 ----------------
    def test_S8_ask_question_does_not_mutate_jd_approved(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "ask_question", 0.85, "Boa pergunta — quer que eu mande o benchmark?",
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {"gate_resume_message": "o salário tá baixo?"}
                result = graph_mod.jd_gate_node(state)
        self.assertNotIn("jd_approved", result)  # state preservado
        self.assertEqual(result["gate_last_intent"], "ask_question")
        self.assertIn("benchmark", result["gate_clarify_message"])
        self.assertEqual(graph_mod.route_after_gate(result), "end")

    # ---------------- S9 ----------------
    def test_S9_low_confidence_clarifies_without_mutating_approval(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("approve", 0.5, "Confirma se isso é aprovação?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {"gate_resume_message": "ehh sei la"}
                result = graph_mod.jd_gate_node(state)
        self.assertNotIn("jd_approved", result)
        self.assertEqual(result["gate_last_confidence"], 0.5)
        self.assertEqual(graph_mod.route_after_gate(result), "end")

    # ---------------- S10 ----------------
    def test_S10_off_allowlist_intent_falls_back(self):
        # Pydantic Literal levanta ValidationError → classifier devolve fallback.
        # Aqui simulamos a situação no nível do classifier.
        async def _run():
            with mock.patch.object(
                classifier_mod.WizardGateClassifier, "_invoke_llm",
                new=mock.AsyncMock(return_value={
                    "intent": "DELETE_DATABASE",  # off-allowlist
                    "extracted_data": {},
                    "conversational_reply": "evil",
                    "confidence": 0.99,
                }),
            ):
                clf = classifier_mod.WizardGateClassifier()
                out = await clf.classify(
                    user_message="aprova", stage="jd_enrichment",
                    ws_stage_payload=None,
                )
            self.assertEqual(out.intent, "ask_question")
            self.assertEqual(out.confidence, 0.0)
        import asyncio
        asyncio.run(_run())

    # ---------------- S11 ----------------
    def test_S11_classifier_timeout_falls_back_to_clarify(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify", new=mock.AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {"gate_resume_message": "manda bala"}
                result = graph_mod.jd_gate_node(state)
        self.assertNotIn("jd_approved", result)
        clarify = str(result.get("gate_clarify_message", "")).lower()
        self.assertTrue(
            "interpretar" in clarify or "aprovar" in clarify or "ajustar" in clarify,
            f"expected clarify message, got: {clarify!r}",
        )
        self.assertEqual(graph_mod.route_after_gate(result), "end")

    # ---------------- S12 ----------------
    def test_S12_domain_route_by_stage_dispatches_to_gate_jd_when_flag_on(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        ctx = mock.MagicMock()
        ctx.metadata = {"wizard_state": {"current_stage": "jd_enrichment"}}
        ctx.session_id = "wiz-test-123"
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "true"}, clear=False):
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage("aprova", "jd_enrichment", ctx)
        self.assertEqual(decision["action_id"], "gate_jd")
        self.assertEqual(decision["source"], "llm_gate")

    def test_S12b_domain_route_by_stage_legacy_when_flag_off(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        ctx = mock.MagicMock()
        ctx.metadata = {"wizard_state": {"current_stage": "jd_enrichment"}}
        ctx.session_id = "wiz-test-123"
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "false"}, clear=False):
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage("aprova", "jd_enrichment", ctx)
        self.assertEqual(decision["action_id"], "approve_jd")

    # ---------------- S13 ----------------
    def test_S13_fairness_guard_blocks_discriminatory_resume_message(self):
        # FairnessGuard.check é chamado no início de jd_gate_node. Mockamos
        # para forçar bloqueio e validar que jd_approved NÃO é setado.
        try:
            fg_mod = importlib.import_module("app.shared.compliance.fairness_guard")
        except Exception:
            self.skipTest("FairnessGuard module not importable in this environment")
        block_result = mock.MagicMock(
            is_blocked=True, category="gender_bias",
            blocked_terms=["masculinos"],
            educational_message="Bloqueado: critério discriminatório de gênero.",
        )
        with mock.patch.object(fg_mod.FairnessGuard, "check", return_value=block_result):
            state = {"gate_resume_message": "aprova mas só candidatos masculinos"}
            result = graph_mod.jd_gate_node(state)
        self.assertTrue(result.get("jd_fairness_blocked"))
        self.assertNotIn("jd_approved", result)
        self.assertIn("discriminatório", result["gate_clarify_message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
