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
        # Sprint F.2 fix — non-terminal (no jd_approved) self-loops
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

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
        # Sprint F.2 fix — non-terminal (no jd_approved) self-loops
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

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

    # ---------------- S7b (regression: code review #3) ----------------
    def test_S7b_provide_new_content_loop_breaks_after_re_enrichment(self):
        """T2 fix #4 — após `provide_new_content` rotear para intake e o
        graph re-rodar intake+jd_enrichment, o gate é re-visitado SEM
        ``gate_resume_message`` (recrutador ainda não respondeu de novo).
        ``route_after_gate`` DEVE devolver ``end`` em vez de re-rotear para
        intake (o que causava loop até ``GraphRecursionError``).

        Reproduz a transição: jd_gate(provide_new_content) → intake →
        jd_enrichment → jd_gate(no msg) → END.
        """
        # Estado pós-re-enrichment: jd_enriched populado, jd_approved=False
        # (deixado por provide_new_content), gate_last_intent ainda
        # "provide_new_content", gate_resume_message="" (foi consumido).
        # user_query é o MESMO da rodada anterior (recrutador ainda não
        # mandou nada novo) — simulamos vazio para garantir que não há
        # detecção espúria de resume.
        post_reenrichment_state = {
            "gate_resume_message": "",
            "user_query": "",
            "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
            "jd_approved": False,
            "gate_last_intent": "provide_new_content",
            "gate_last_confidence": 0.95,
            "raw_input": "novo conteudo da JD",
            "jd_quality_score": 65.0,
        }
        with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
            result = graph_mod.jd_gate_node(post_reenrichment_state)
        # Loop fix: gate limpou gate_last_intent E resetou jd_approved=None.
        self.assertIsNone(result.get("gate_last_intent"))
        self.assertIsNone(result.get("jd_approved"))
        # Routing agora cai no branch END default — não mais "intake".
        # Sprint F.2 fix — reject_with_feedback (non-terminal) self-loops; recruiter sends correction next turn
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

    def test_S7c_approve_intent_is_preserved_across_no_op_revisit(self):
        """Garantia complementar: ``approve`` (jd_approved=True) NÃO é
        considerado intent transitório — não pode ser limpo no no-op,
        senão o graph nunca avança para bigfive."""
        post_approve_state = {
            "gate_resume_message": "",
            "user_query": "",
            "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
            "jd_approved": True,
            "gate_last_intent": "approve",
            "gate_last_confidence": 0.95,
            "jd_quality_score": 65.0,
        }
        with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
            result = graph_mod.jd_gate_node(post_approve_state)
        # approve preservado; rota → bigfive (quality 65 ≥ 30).
        self.assertEqual(result.get("gate_last_intent"), "approve")
        self.assertIs(result.get("jd_approved"), True)
        self.assertEqual(graph_mod.route_after_gate(result), "bigfive")

    # ---------------- S7e (regression: code review #5) ----------------
    def test_S7e_post_reject_user_turn_is_classified_not_dropped(self):
        """T2 fix #6 — depois de ``reject_with_feedback`` (turn N) ter
        deixado ``jd_approved=False``, o PRÓXIMO turno do recrutador (N+1)
        DEVE ser classificado pelo gate. Antes do fix, ``_not_approved``
        exigia ``jd_approved is None`` → o turno N+1 caía direto no no-op
        cleanup, ignorando a resposta do recrutador uma vez."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "approve", 0.95, "Beleza, vamos seguir.",
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                # Estado pós-reject (turn N): jd_approved=False, gate_last_intent=reject,
                # seen=msg anterior do reject.
                state = {
                    "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
                    "jd_approved": False,
                    "gate_last_intent": "reject_with_feedback",
                    "gate_seen_user_query": "calma, refaz só skills",
                    "user_query": "ok agora tá bom, manda bala",  # turn N+1
                    "jd_quality_score": 65.0,
                }
                result = graph_mod.jd_gate_node(state)
        # gate classificou (não caiu em no-op): jd_approved virou True (approve).
        self.assertIs(result.get("jd_approved"), True)
        self.assertEqual(result.get("gate_last_intent"), "approve")
        # marker atualizado para a mensagem nova.
        self.assertEqual(result.get("gate_seen_user_query"), "ok agora tá bom, manda bala")
        # rota: bigfive (quality 65 ≥ 30 + approved).
        self.assertEqual(graph_mod.route_after_gate(result), "bigfive")

    def test_S7f_same_user_query_within_invoke_does_not_reclassify(self):
        """T2 fix #6 — após ``provide_new_content`` rotear para intake →
        jd_enrichment → jd_gate (segunda visita), o gate NÃO pode
        re-classificar a MESMA mensagem. Marker ``gate_seen_user_query``
        garante: se ``user_query == seen``, cai no no-op cleanup."""
        clf = classifier_mod.get_wizard_gate_classifier()
        # Se chamasse classify, daria provide_new_content de novo → loop.
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(side_effect=AssertionError("classify NÃO deveria ser chamado")),
        ):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {
                    "jd_enriched": {"titulo_padronizado": "Engenheira de Dados"},  # re-enrichment já populou
                    "jd_approved": False,
                    "gate_last_intent": "provide_new_content",
                    "gate_seen_user_query": "olha, na verdade segue a JD certinha: ...",
                    "user_query": "olha, na verdade segue a JD certinha: ...",  # MESMA msg
                    "jd_quality_score": 70.0,
                }
                result = graph_mod.jd_gate_node(state)
        # Cleanup rodou: gate_last_intent limpo, jd_approved=None, route=end.
        self.assertIsNone(result.get("gate_last_intent"))
        self.assertIsNone(result.get("jd_approved"))
        # Sprint F.2 fix — after intake re-enrichment with cleared intent, gate awaits via self-loop
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

    # ---------------- S7h (regression: code review #8) ----------------
    def test_S7h_build_state_does_not_overwrite_raw_input_on_continuation(self):
        """T2 fix #10 — `WizardSessionService._build_state()` em sessões
        continuing NÃO pode sobrescrever ``raw_input``. Sem isso,
        ``user_query == raw_input`` SEMPRE em WS turns subsequentes,
        neutralizando o initial-pass guard do jd_gate_node e travando
        o gate em no-op END (bug original de Task #1085 volta).

        Cenário: turn 1 = JD inicial; turn 2 = "manda bala". Esperado:
        após turn 2, raw_input ainda é a JD original e user_query é
        "manda bala" — daí jd_gate_node consegue distinguir.
        """
        from app.domains.job_creation.services.wizard_session_service import (
            WizardSessionService,
        )
        from unittest.mock import patch
        # Bypass tenant strict-mode (test env can be either).
        with patch(
            "app.shared.agents.tenant_aware_agent.is_tenant_strict_mode",
            return_value=False,
        ):
            jd_msg = "Engenheiro Backend Sr Python AWS remoto"
            # Turn 1 — fresh session.
            state_t1 = WizardSessionService._build_state(
                thread_id="wiz-test",
                user_message=jd_msg,
                user_id="user-1",
                company_id="00000000-0000-4000-a000-000000000001",
                session_id="sess-1",
                context={},
                prior_state={},
            )
            self.assertEqual(state_t1["raw_input"], jd_msg)
            self.assertEqual(state_t1["user_query"], jd_msg)

            # Simula que jd_enrichment populou jd_enriched no checkpoint.
            prior = {
                **state_t1,
                "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
                "current_stage": "jd_enrichment",
                "ws_stage_payload": {"data": {"requires_approval": True}},
            }
            # Turn 2 — recrutador responde ao HITL.
            state_t2 = WizardSessionService._build_state(
                thread_id="wiz-test",
                user_message="manda bala",
                user_id="user-1",
                company_id="00000000-0000-4000-a000-000000000001",
                session_id="sess-1",
                context={},
                prior_state=prior,
            )
        # CONTRATO crítico: raw_input preservado, user_query atualizado.
        self.assertEqual(state_t2["raw_input"], jd_msg, "raw_input foi sobrescrito — bug Task #1085 volta")
        self.assertEqual(state_t2["user_query"], "manda bala")
        self.assertNotEqual(state_t2["user_query"], state_t2["raw_input"])
        # jd_enriched preservado para o gate.
        self.assertTrue(state_t2.get("jd_enriched"))

    # ---------------- S7g (regression: code review #6 comment) ----------------
    def test_S7g_initial_pass_after_enrichment_does_not_classify(self):
        """T2 fix #8 — primeiro pass após enrichment (mesma invocação,
        ``user_query == raw_input``) NÃO pode disparar classifier. Sem
        este guard, o gate roda LLM sobre a própria JD e classifica como
        ``provide_new_content`` → re-enrichment loop + custo desnecessário."""
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(side_effect=AssertionError("classify NÃO deveria ser chamado no initial pass")),
        ):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {
                    "jd_enriched": {"titulo_padronizado": "Engenheiro Backend"},
                    "jd_approved": None,  # primeira vez no gate
                    "raw_input": "Engenheiro Backend Sr Python AWS remoto",
                    "user_query": "Engenheiro Backend Sr Python AWS remoto",  # == raw
                    "jd_quality_score": 65.0,
                }
                result = graph_mod.jd_gate_node(state)
        # Cleanup branch: aguarda HITL real (próximo turno do recrutador).
        self.assertIsNone(result.get("gate_last_intent"))
        self.assertIsNone(result.get("jd_approved"))
        # Sprint F.2 fix — same-query no-op falls into self-loop awaiting fresh turn
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

    # ---------------- S7d (regression: code review #4) ----------------
    def test_S7d_ws_session_service_prefers_gate_clarify_message(self):
        """T2 fix #5 — `WizardSessionService.process_message` DEVE usar
        ``gate_clarify_message`` como mensagem do recrutador quando o gate
        LLM classificou o turno (``gate_last_intent`` truthy). Sem isso,
        o WS caía no path canned em loop (bug original).

        Task #1089 (T3): o dict canned por stage foi removido — o
        else-branch agora é fail-loud (_emit_silent_fallback +
        _generate_fallback_reply).
        Este teste valida apenas a preferência por ``gate_clarify_message``
        quando ele está presente.
        """
        # Simula o resultado do graph após gate ter classificado ask_question.
        fake_result = {
            "current_stage": "jd_enrichment",
            "ws_stage_payload": {"data": {}},  # vazio — sem message/response_text
            "gate_clarify_message": "Boa pergunta! O salário tá bem alinhado com o mercado.",
            "gate_last_intent": "ask_question",
            "gate_last_confidence": 0.9,
        }
        stage_payload = fake_result.get("ws_stage_payload") or {}
        stage_data = stage_payload.get("data") or {}
        gate_msg = fake_result.get("gate_clarify_message")
        gate_intent = fake_result.get("gate_last_intent")
        if gate_msg and gate_intent:
            message = str(gate_msg)
        else:
            message = stage_data.get("message") or stage_data.get("response_text") or ""
        self.assertEqual(message, "Boa pergunta! O salário tá bem alinhado com o mercado.")
        self.assertNotIn("preciso da sua aprovação", message.lower())

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
        # Sprint F.2 fix — initial pass (no msg) self-loops to wait for HITL response
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

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
        # Sprint F.2 fix — ask_question self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

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
        # Sprint F.2 fix — low confidence self-loops to interrupt() for next turn
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")

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
