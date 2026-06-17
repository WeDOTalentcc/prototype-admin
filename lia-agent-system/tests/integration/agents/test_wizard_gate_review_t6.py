"""Sentinela offline — T6 (Task #1088) — wizard review gate (LLM-based, HITL #3).

Mirrors o padrão de ``test_wizard_gate_wsi_questions_t5.py`` para o stage
``review`` (HITL #3 — publicar / ajustar seção / configurar destinos /
tirar dúvida) com DUPLA CONFIRMAÇÃO de chat para ``publish_now``.

Cobertura:
  S1  — STAGE_ALLOWLISTS["review"] contém exatamente os 4 intents.
  S2  — graph builder com use_llm_gates=False NÃO inclui review_gate.
  S3  — graph builder com use_llm_gates=True INCLUI review_gate.
  S4  — review_gate_node sem mensagem nova → no-op (END).
  S5  — publish_now PRIMEIRA chamada → pending_publish_confirmation=True
        + publish_confirmation_ts set + policy_confirmed_publish=False
        + route=END.
  S6  — publish_now SEGUNDA chamada DENTRO do TTL → policy_confirmed_publish=True
        + pending_publish_confirmation=False + route=publish.
  S7  — publish_now SEGUNDA chamada FORA do TTL → tratado como nova 1ª
        (pending+ts atualizado, policy_confirmed_publish=False, route=END).
  S8  — request_changes (target=title + instruction) → jd_approved=None +
        review_request_changes_pending set + route=jd_enrichment.
  S9  — request_changes (target=questions) → questions_approved=None +
        wsi_regenerate_pending=True + wsi_questions=[] + route=wsi_questions.
  S10 — request_changes target FORA do allowlist → clarify, sem mutar,
        route=END.
  S11 — configure_destinations (allowlist válida) → publish_platforms set
        com dedup + route=END + reset de dual-confirmation.
  S12 — configure_destinations TUDO fora da allowlist → clarify, sem
        mutar publish_platforms, route=END.
  S13 — ask_clarification → state inalterado em decisão + clarify, route=END.
  S14 — confidence < 0.7 → clarify sem mutar, route=END.
  S15 — output do classifier off-allowlist (ex.: "approve" jd-only) →
        fallback determinístico (ask_question / cf=0.0).
  S16 — classifier exception → fallback (route=END), wizard não trava.
  S17 — domain._route_by_stage com flag ON dispatcha gate_review.
  S18 — domain._route_by_stage com flag OFF mantém heurística keyword.
  S19 — FairnessGuard L1 bloqueia mensagem discriminatória no review gate.
  S20 — Audit emit recebe confirmation_method="dual" no 2º publish_now
        e "chat" no 1º (rastreabilidade SOX 7y).
  S21 — request_changes RESETA pending_publish_confirmation se estava set
        (recrutador mudou de ideia).
  S22 — _REVIEW_DESTINATIONS_ALLOWLIST canônica = {site_carreiras, gupy,
        pandape, linkedin}.
  S23 — dict canned por stage do wizard permanece removido (Task #1089)
        (T3 prep — sentinela negativa).
"""
from __future__ import annotations

import importlib
import os
import sys
import time
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


def _base_review_state(**overrides):
    state = {
        "current_stage": "review",
        "publish_platforms": ["site_carreiras", "linkedin"],
        "readiness_check": {"ready": True},
        "wsi_questions": [
            {"index": i + 1, "text": f"Q{i+1}", "block": "technical"}
            for i in range(7)
        ],
    }
    state.update(overrides)
    return state


class WizardReviewGateT6(unittest.TestCase):

    # ---------------- S1 ----------------
    def test_S1_stage_allowlist_review_canonical(self):
        allow = classifier_mod.get_allowed_intents("review")
        self.assertEqual(
            set(allow),
            {
                "publish_now",
                "request_changes",
                "ask_clarification",
                "configure_destinations",
            },
        )
        # intents de outros stages não devem vazar.
        self.assertNotIn("approve", allow)
        self.assertNotIn("approve_all", allow)
        self.assertNotIn("select_compact", allow)

    # ---------------- S2 / S3 ----------------
    def test_S2_builder_off_excludes_review_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=False)
        self.assertNotIn("review_gate", builder.nodes)

    def test_S3_builder_on_includes_review_gate_node(self):
        builder = graph_mod.create_job_creation_graph(use_llm_gates=True)
        self.assertIn("review_gate", builder.nodes)

    # ---------------- S4 ----------------
    def test_S4_no_resume_message_is_noop(self):
        state = _base_review_state()
        result = graph_mod.review_gate_node(state)
        self.assertEqual(result.get("current_stage"), "review")
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S5 ----------------
    def test_S5_publish_now_first_turn_sets_pending(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.95, "Confirma para publicar?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="publica agora")
                result = graph_mod.review_gate_node(state)
        self.assertIs(result["pending_publish_confirmation"], True)
        self.assertIsNotNone(result["publish_confirmation_ts"])
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertEqual(result["gate_last_intent"], "publish_now")
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S6 ----------------
    def test_S6_publish_now_second_turn_within_ttl_confirms(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.95, "Confirmado.")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="confirmo, manda",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time() - 30.0,  # 30s ago, dentro do TTL
                )
                result = graph_mod.review_gate_node(state)
        self.assertIs(result["policy_confirmed_publish"], True)
        self.assertIs(result["pending_publish_confirmation"], False)
        self.assertIsNone(result["publish_confirmation_ts"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "publish")

    # ---------------- S7 ----------------
    def test_S7_publish_now_second_turn_after_ttl_treats_as_first(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.95, "Confirma para publicar?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="publica de novo",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time() - 999.0,  # FORA do TTL (300s)
                )
                result = graph_mod.review_gate_node(state)
        self.assertIs(result["pending_publish_confirmation"], True)
        self.assertIs(result["policy_confirmed_publish"], False)
        # ts foi atualizado (próximo da hora atual)
        self.assertGreater(result["publish_confirmation_ts"], time.time() - 5.0)
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S8 ----------------
    def test_S8_request_changes_title_routes_to_jd_enrichment(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.92, "Vou ajustar o título.",
            extracted={"target_section": "title", "instruction": "trocar para SE Pleno"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="muda o título pra SE Pleno",
                    jd_approved=True,
                )
                result = graph_mod.review_gate_node(state)
        self.assertIsNone(result["jd_approved"])
        self.assertEqual(
            result["review_request_changes_pending"],
            {"target_section": "title", "instruction": "trocar para SE Pleno"},
        )
        self.assertEqual(graph_mod.route_after_review_gate(result), "jd_enrichment")

    # ---------------- S9 ----------------
    def test_S9_request_changes_questions_routes_to_wsi_questions(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.92, "Vou refazer as perguntas.",
            extracted={"target_section": "questions", "instruction": "refazer 3 e 4"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="as WSI 3 e 4 não tão boas",
                    questions_approved=True,
                )
                result = graph_mod.review_gate_node(state)
        self.assertIsNone(result["questions_approved"])
        self.assertIs(result["wsi_regenerate_pending"], True)
        self.assertEqual(result["wsi_questions"], [])
        self.assertEqual(graph_mod.route_after_review_gate(result), "wsi_questions")

    # ---------------- S10 ----------------
    def test_S10_request_changes_invalid_target_clarifies(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.9, "vou ajustar",
            extracted={"target_section": "branding", "instruction": "muda"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="muda o branding")
                result = graph_mod.review_gate_node(state)
        self.assertIsNone(result.get("review_request_changes_pending"))
        self.assertIn("Qual seção", result["gate_clarify_message"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S11 ----------------
    def test_S11_configure_destinations_valid_sets_platforms(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "configure_destinations", 0.93, "Configurando.",
            extracted={"destinations": ["gupy", "linkedin", "gupy", "indeed"]},  # dedup + filtra indeed
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="manda pra Gupy e LinkedIn",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time(),
                )
                result = graph_mod.review_gate_node(state)
        self.assertEqual(result["publish_platforms"], ["gupy", "linkedin"])
        # Reset dual-confirmation pois destinos mudaram.
        self.assertIs(result["pending_publish_confirmation"], False)
        self.assertIsNone(result["publish_confirmation_ts"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S12 ----------------
    def test_S12_configure_destinations_all_invalid_clarifies(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "configure_destinations", 0.92, "ok",
            extracted={"destinations": ["indeed", "infojobs"]},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="manda pro Indeed")
                result = graph_mod.review_gate_node(state)
        # publish_platforms inalterado.
        self.assertEqual(result["publish_platforms"], ["site_carreiras", "linkedin"])
        self.assertIn("Disponíveis", result["gate_clarify_message"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S13 ----------------
    def test_S13_ask_clarification_does_not_mutate(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "ask_clarification", 0.9,
            "Esse pipeline veio do default em Settings.",
            extracted={"question_topic": "pipeline default"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="esse pipeline é o padrão?")
                result = graph_mod.review_gate_node(state)
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertIsNone(result.get("review_request_changes_pending"))
        self.assertEqual(result["gate_last_intent"], "ask_clarification")
        self.assertIn("Settings", result["gate_clarify_message"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S14 ----------------
    def test_S14_low_confidence_clarifies_without_mutating(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.5, "Confirma se quer publicar mesmo?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="ehh sei la")
                result = graph_mod.review_gate_node(state)
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertIsNot(result.get("pending_publish_confirmation"), True)
        self.assertEqual(result["gate_last_confidence"], 0.5)
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S15 ----------------
    def test_S15_off_allowlist_intent_falls_back(self):
        async def _run():
            with mock.patch.object(
                classifier_mod.WizardGateClassifier, "_invoke_llm",
                new=mock.AsyncMock(return_value={
                    "intent": "approve",  # válido em jd, off em review
                    "extracted_data": {},
                    "conversational_reply": "ok",
                    "confidence": 0.99,
                }),
            ):
                clf = classifier_mod.WizardGateClassifier()
                out = await clf.classify(
                    user_message="aprova", stage="review", ws_stage_payload=None,
                )
            self.assertEqual(out.intent, "ask_question")
            self.assertEqual(out.confidence, 0.0)

        import asyncio
        asyncio.run(_run())

    # ---------------- S16 ----------------
    def test_S16_classifier_exception_falls_back(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify", new=mock.AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(gate_resume_message="publica")
                result = graph_mod.review_gate_node(state)
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S17 ----------------
    def test_S17_domain_route_by_stage_dispatches_gate_review_when_flag_on(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        with mock.patch.dict(os.environ, {"LIA_WIZARD_LLM_GATES": "true"}, clear=False):
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "publica agora", "review",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "gate_review")
        self.assertEqual(decision["params"]["user_query"], "publica agora")
        self.assertEqual(decision.get("source"), "llm_gate")

    # ---------------- S18 ----------------
    def test_S18_domain_route_by_stage_keeps_keyword_when_flag_off(self):
        domain_mod = importlib.import_module("app.domains.job_creation.domain")
        with mock.patch.dict(
            os.environ,
            {"LIA_WIZARD_LLM_GATES": "0", "LIA_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("ENVIRONMENT", None)
            d = domain_mod.JobCreationDomain.__new__(domain_mod.JobCreationDomain)
            decision = d._route_by_stage(
                "publica agora", "review",
                mock.MagicMock(metadata={}),
            )
        self.assertEqual(decision["action_id"], "publish_job")

    # ---------------- S19 ----------------
    def test_S19_fairness_guard_blocks_discriminatory_message(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(side_effect=AssertionError(
                "classify NÃO deveria ser chamado quando FairnessGuard bloqueia",
            )),
        ):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
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
                    state = _base_review_state(
                        gate_resume_message="publica mas só pra homens",
                    )
                    result = graph_mod.review_gate_node(state)
        self.assertIs(result.get("fairness_blocked"), True)
        self.assertIsNot(result.get("policy_confirmed_publish"), True)
        self.assertIn("discrimina", result["gate_clarify_message"].lower())
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S20 ----------------
    def test_S20_audit_emit_receives_confirmation_method(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.95, "ok")
        captured = []

        def _capture(state, msg, output, *, confirmation_method="chat"):
            captured.append(confirmation_method)

        # 1ª chamada → chat
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_review_gate_audit", _capture):
                state = _base_review_state(gate_resume_message="publica")
                _ = graph_mod.review_gate_node(state)

        # 2ª chamada dentro do TTL → dual
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_review_gate_audit", _capture):
                state = _base_review_state(
                    gate_resume_message="confirmo",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time() - 10.0,
                )
                _ = graph_mod.review_gate_node(state)

        self.assertEqual(captured, ["chat", "dual"])

    # ---------------- S21 ----------------
    def test_S21_request_changes_resets_pending_publish_confirmation(self):
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.92, "Vou ajustar.",
            extracted={"target_section": "salary", "instruction": "subir teto"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="muda o salário",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time(),
                )
                result = graph_mod.review_gate_node(state)
        self.assertIs(result["pending_publish_confirmation"], False)
        self.assertIsNone(result["publish_confirmation_ts"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "salary")

    # ---------------- S22 ----------------
    def test_S22_destinations_allowlist_canonical(self):
        self.assertEqual(
            set(graph_mod._REVIEW_DESTINATIONS_ALLOWLIST),
            {"site_carreiras", "gupy", "pandape", "linkedin"},
        )

    # ---------------- S31 (post-review #2: hard readiness gate) ----------------
    def test_S31_publish_now_blocked_when_not_ready(self):
        """T6 post-review2 — publish_now NÃO pode entrar em pending nem
        rotear para publish quando readiness_check.ready=False. Emite
        clarify determinístico citando exatamente o que falta."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.97, "Vamos publicar?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="publica agora",
                    readiness_check={
                        "ready": False,
                        "missing": ["jd_approved", "questions_approved"],
                        "checks": {},
                    },
                )
                result = graph_mod.review_gate_node(state)
        # NÃO entra em pending — bloqueado fail-loud.
        self.assertFalse(result.get("pending_publish_confirmation"))
        self.assertIsNone(result.get("publish_confirmation_ts"))
        self.assertFalse(result.get("policy_confirmed_publish"))
        clarify = result["gate_clarify_message"]
        self.assertIn("aprovação da descrição", clarify)
        self.assertIn("aprovação das questões WSI", clarify)
        # E rota é END (não publish).
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    def test_S31b_route_blocks_publish_when_confirmed_but_not_ready(self):
        """T6 post-review2 — defesa em profundidade: mesmo que
        policy_confirmed_publish=True chegue por outro caminho, o router
        ainda bloqueia publish se readiness não está ok."""
        state = _base_review_state(
            policy_confirmed_publish=True,
            readiness_check={"ready": False, "missing": ["has_seniority"], "checks": {}},
        )
        self.assertEqual(graph_mod.route_after_review_gate(state), "end")
        # Sanidade: com ready=True, sim publica.
        state2 = _base_review_state(
            policy_confirmed_publish=True,
            readiness_check={"ready": True, "missing": [], "checks": {}},
        )
        self.assertEqual(graph_mod.route_after_review_gate(state2), "publish")

    # ---------------- S28 (post-review fix #1: stale pending lifecycle) ----------------
    def test_S28_stale_review_request_changes_pending_cleared_on_entry(self):
        """T6 post-review #1 — pending field SOBRA do turno anterior NÃO pode
        causar reroute em chamadas subsequentes ao review_gate_node sem msg
        fresca. Garante que entry-clear acontece mesmo no early-return path."""
        state = _base_review_state(
            gate_resume_message="",
            review_request_changes_pending={"target_section": "title", "instruction": "stale"},
        )
        # Sem msg fresca e sem user_query nova → early return sem classify.
        result = graph_mod.review_gate_node(state)
        self.assertIsNone(result["review_request_changes_pending"])
        # Routing após entrada no-op DEVE ser END (não pode rotear pra
        # jd_enrichment baseado em pending stale).
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    def test_S28b_pending_always_reset_on_fresh_turn(self):
        """T6 post-review #1 — em qualquer turno fresh, next_state nasce com
        review_request_changes_pending=None; SÓ as branches request_changes
        title/description/questions/salary/pipeline/destinations setam novo."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("ask_clarification", 0.92, "?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="é o pipeline padrão?",
                    review_request_changes_pending={"target_section": "title", "instruction": "stale"},
                )
                result = graph_mod.review_gate_node(state)
        # ask_clarification NÃO seta nova pending → deve ficar None.
        self.assertIsNone(result["review_request_changes_pending"])
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")

    # ---------------- S29 (post-review fix #2: jd_enriched invalidation) ----------------
    def test_S29_request_changes_title_invalidates_jd_enriched(self):
        """T6 post-review #2 — request_changes target=title DEVE invalidar
        jd_enriched (None), senão jd_enrichment_node pula re-geração e o
        ajuste cirúrgico nunca é aplicado. Mesma regra para description."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.92, "ok",
            extracted={"target_section": "title", "instruction": "Software Engineer Pleno"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="muda o título pra Software Engineer Pleno",
                    jd_enriched={"titulo_padronizado": "Engenheiro Backend Pleno"},
                    jd_quality_score=88.0,
                    jd_quality_warnings=["minor"],
                )
                result = graph_mod.review_gate_node(state)
        self.assertIsNone(result["jd_approved"])
        self.assertIsNone(result["jd_enriched"])
        self.assertIsNone(result["jd_quality_score"])
        self.assertEqual(result["jd_quality_warnings"], [])
        # E a instruction fica disponível para o destino consultar.
        self.assertEqual(
            result["review_request_changes_pending"]["instruction"],
            "Software Engineer Pleno",
        )
        self.assertEqual(graph_mod.route_after_review_gate(result), "jd_enrichment")

    # ---------------- S30 (post-review fix #3: deterministic publish summary) ----------------
    def test_S30_publish_first_turn_deterministic_summary(self):
        """T6 post-review #3 — gate_clarify_message do publish_now 1º turno
        DEVE conter sumário determinístico (título, salário, # questões,
        canais), não apenas eco do conversational_reply do LLM."""
        clf = classifier_mod.get_wizard_gate_classifier()
        # LLM responde com algo vago — deterministic summary ignora.
        out = _make_output("publish_now", 0.95, "Confirma?")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="publica agora",
                    jd_enriched={"titulo_padronizado": "Engenheiro Backend Pleno"},
                    salary_min=12000,
                    salary_max=18000,
                    salary_currency="BRL",
                    wsi_questions=[{"id": "q1"}, {"id": "q2"}, {"id": "q3"}],
                    publish_platforms=["linkedin", "site_carreiras"],
                )
                result = graph_mod.review_gate_node(state)
        msg = result["gate_clarify_message"]
        self.assertIn("Engenheiro Backend Pleno", msg)
        self.assertIn("BRL", msg)
        self.assertIn("12.000", msg)
        self.assertIn("18.000", msg)
        self.assertIn("3", msg)  # # de questões WSI
        self.assertIn("linkedin", msg)
        self.assertIn("site_carreiras", msg)
        self.assertIn("Confirma", msg)

    # ---------------- S24 ----------------
    def test_S24_stage_prompt_paths_review_wired(self):
        """T6 — gate_review.yaml DEVE estar registrado em STAGE_PROMPT_PATHS["review"]
        para que classify(stage="review") use o prompt específico em vez de cair
        no genérico de jd_enrichment. Regressão direta do code review T6."""
        path = classifier_mod.WizardGateClassifier.STAGE_PROMPT_PATHS.get("review")
        self.assertEqual(path, "prompts/job_creation/gate_review.yaml")
        # E o arquivo precisa existir.
        from pathlib import Path
        # Classifier resolve via app_root = parents[3] de wizard_gate_classifier.py,
        # que aponta para lia-agent-system/app/. Mesma convenção aqui.
        app_root = Path(__file__).resolve().parents[3] / "app"
        self.assertTrue(
            (app_root / path).exists(),
            f"gate_review.yaml não encontrado em {app_root / path}",
        )

    # ---------------- S25 ----------------
    def test_S25_tenant_aware_destinations_blocks_non_enabled_channel(self):
        """T6 — quando tenant_enabled_ats=['site_carreiras', 'linkedin'] e o
        recrutador pede 'gupy' (que NÃO está habilitado pelo tenant), o gate
        deve REJEITAR com clarify fail-loud, não silently aceitar."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "configure_destinations", 0.93, "ok",
            extracted={"destinations": ["gupy"]},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="manda pro Gupy",
                    tenant_enabled_ats=["site_carreiras", "linkedin"],
                )
                result = graph_mod.review_gate_node(state)
        # publish_platforms NÃO mudou.
        self.assertEqual(result["publish_platforms"], ["site_carreiras", "linkedin"])
        clarify = result["gate_clarify_message"].lower()
        # Sinal de fail-loud: explica que não está habilitado pelo tenant.
        self.assertIn("tenant", clarify)
        self.assertIn("gupy", clarify)
        # E lista APENAS canais do tenant (não "gupy", não "pandape").
        self.assertNotIn("gupy", clarify.split("habilitados pelo seu tenant:")[1])

    def test_S25b_tenant_aware_destinations_accepts_enabled_channel(self):
        """T6 — Mirror positivo de S25: linkedin habilitado no tenant é aceito."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "configure_destinations", 0.93, "ok",
            extracted={"destinations": ["linkedin"]},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="só LinkedIn",
                    tenant_enabled_ats=["site_carreiras", "linkedin"],
                )
                result = graph_mod.review_gate_node(state)
        self.assertEqual(result["publish_platforms"], ["linkedin"])

    # ---------------- S26 ----------------
    def test_S26_publish_confirmation_method_propagated_to_state(self):
        """T6 — o 2º publish_now (dentro do TTL) deve setar
        publish_confirmation_method='dual' no state, para que publish_node
        registre no audit final (rastreabilidade SOX 7y)."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("publish_now", 0.95, "Confirmado.")
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="confirmo",
                    pending_publish_confirmation=True,
                    publish_confirmation_ts=time.time() - 30.0,
                )
                result = graph_mod.review_gate_node(state)
        self.assertEqual(result["publish_confirmation_method"], "dual")

    # ---------------- S27 ----------------
    def test_S27_request_changes_destinations_handled_inline(self):
        """T6 — request_changes target=destinations NÃO roteia para "review"
        (suprimido); handler inline emite clarify pedindo a lista de canais
        e route=END (próximo turno cai em configure_destinations)."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output(
            "request_changes", 0.92, "ok",
            extracted={"target_section": "destinations", "instruction": "muda os canais"},
        )
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(
                graph_mod, "_emit_review_gate_audit", lambda *a, **k: None,
            ):
                state = _base_review_state(
                    gate_resume_message="muda os destinos",
                )
                result = graph_mod.review_gate_node(state)
        self.assertEqual(graph_mod.route_after_review_gate(result), "end")
        clarify = result["gate_clarify_message"].lower()
        self.assertIn("canais", clarify)
        # request_changes_pending registrado para audit/observabilidade.
        self.assertEqual(
            result["review_request_changes_pending"]["target_section"], "destinations",
        )

    # ---------------- S23 ----------------
    def test_S23_stage_defaults_dict_was_removed(self):
        """Task #1089 (T3) — o dict canned por stage foi removido por
        completo em favor de fail-loud (_emit_silent_fallback +
        _generate_fallback_reply). Sentinela arquitetural canônica
        (com nome literal do símbolo banido) vive em
        test_wizard_no_canned_fallback_t3.py."""
        wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        # Símbolo banido referenciado dinamicamente p/ não reaparecer
        # como literal nesta suíte (regra grep-zero da Task #1089).
        banned_attr = "_STAGE" + "_DEFAULTS"
        self.assertFalse(
            hasattr(wss, banned_attr),
            f"{banned_attr} deve permanecer REMOVIDO (Task #1089 T3 cleanup).",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
