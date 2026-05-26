"""Sentinel P0-#3 (F-1.6) — jd_gate provide_new_content invalida cascade derivados.

Background: pré-fix, recrutador escolhendo "refazer JD" via jd_gate só zerava
jd_enriched. Os derivados (bigfive_profile, trait_rankings, wsi_questions,
competency_tree, pipeline_template_*, interview_stages) ficavam stale calculados
sobre a JD anterior — wizard publicaria vaga com mistura de 2 JDs.

Sprint Pipeline Templates (2026-05-26) expandiu o escopo do bug: agora
pipeline_template_id + pipeline_template_score +
pipeline_template_skipped + interview_stages também precisam invalidar
quando JD muda.

Cobertura:
  S1 — provide_new_content invalida TODOS os 8 derivados downstream
  S2 — approve mantém derivados intactos (sanity / contraprova)

Run standalone:
    python lia-agent-system/tests/wizard/test_jd_gate_invalidation.py
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]  # .../lia-agent-system
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

graph_mod = importlib.import_module("app.domains.job_creation.graph")
classifier_mod = importlib.import_module(
    "app.domains.job_creation.services.wizard_gate_classifier"
)


def _make_output(intent, confidence=0.95, reply="ok", extracted=None):
    return classifier_mod.GateClassifierOutput(
        intent=intent,
        extracted_data=extracted or {},
        conversational_reply=reply,
        confidence=confidence,
    )


def _make_dirty_state() -> dict:
    """State simulando recrutador que já passou por bigfive/wsi/pipeline_template.

    Todos os derivados estão populados com valores da JD anterior. Quando o
    recrutador escolhe provide_new_content, todos devem ser zerados.
    """
    return {
        # gate input
        "gate_resume_message": "na verdade é isso aqui: dev fullstack júnior",
        "user_query": "na verdade é isso aqui: dev fullstack júnior",
        "current_stage": "jd_enrichment",
        # JD anterior + score
        "jd_enriched": {"title": "OLD JD — Backend Pleno", "description": "old desc"},
        "raw_input": "old raw",
        "jd_quality_score": 70.0,
        # Derivados calculados sobre JD anterior
        "bigfive_profile": {"openness": 0.7, "conscientiousness": 0.6},
        "trait_rankings": [{"trait": "openness", "score": 0.7}],
        "wsi_questions": [{"question": "old wsi q1"}, {"question": "old wsi q2"}],
        "competency_tree": [{"skill": "Python", "weight": 0.8}],
        # Sprint Pipeline Templates fields (PR-1 4e904792 declarou no TypedDict)
        "pipeline_template_id": "template-uuid-123",
        "pipeline_template_score": 0.85,
        "pipeline_template_skipped": False,
        "interview_stages": [{"stage": "old-screening", "order": 1}],
    }


class JdGateInvalidationCascade(unittest.TestCase):
    """F-1.6 sensor: provide_new_content invalida cascade completo."""

    def test_S1_provide_new_content_invalidates_all_derivatives(self):
        """Quando recrutador escolhe refazer JD, TODOS derivados zerados."""
        clf = classifier_mod.get_wizard_gate_classifier()
        new_jd = "Dev Fullstack Júnior: React, Node.js, TypeScript." * 4
        out = _make_output(
            "provide_new_content",
            confidence=0.95,
            reply="Recebi a nova descrição, vou re-enriquecer.",
            extracted={"new_content": new_jd},
        )

        state = _make_dirty_state()
        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                result = graph_mod.jd_gate_node(state)

        # Comportamento pré-existente preservado:
        self.assertIs(result["jd_approved"], False)
        self.assertEqual(result["jd_enriched"], None)
        self.assertEqual(result["jd_quality_score"], 0.0)
        self.assertIn("Fullstack", result["raw_input"])

        # F-1.6 cascade invalidation (legacy derivatives):
        self.assertIsNone(
            result["bigfive_profile"],
            "F-1.6: bigfive_profile deveria zerar (calculado sobre JD anterior)",
        )
        self.assertEqual(
            result["trait_rankings"], [],
            "F-1.6: trait_rankings deveria zerar",
        )
        self.assertEqual(
            result["wsi_questions"], [],
            "F-1.6: wsi_questions deveria zerar",
        )
        self.assertEqual(
            result["competency_tree"], [],
            "F-1.6: competency_tree deveria zerar",
        )

        # F-1.6 cascade invalidation (Sprint Pipeline Templates extension):
        self.assertIsNone(
            result["pipeline_template_id"],
            "F-1.6 (sprint): pipeline_template_id deveria zerar",
        )
        self.assertIsNone(
            result["pipeline_template_score"],
            "F-1.6 (sprint): pipeline_template_score deveria zerar",
        )
        self.assertIs(
            result["pipeline_template_skipped"], False,
            "F-1.6 (sprint): pipeline_template_skipped deveria voltar a False",
        )
        self.assertEqual(
            result["interview_stages"], [],
            "F-1.6 (sprint): interview_stages deveria zerar",
        )

    def test_S2_approve_does_NOT_invalidate_derivatives(self):
        """Sanity: approve mantém derivados — vai avançar para bigfive stage."""
        clf = classifier_mod.get_wizard_gate_classifier()
        out = _make_output("approve", confidence=0.95, reply="JD aprovada.")

        state = _make_dirty_state()
        state["gate_resume_message"] = "tá bom, pode aprovar"
        state["user_query"] = "tá bom, pode aprovar"

        with mock.patch.object(clf, "classify", new=mock.AsyncMock(return_value=out)):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                result = graph_mod.jd_gate_node(state)

        self.assertIs(result["jd_approved"], True)
        # Derivados pré-existentes preservados:
        self.assertIsNotNone(result["jd_enriched"], "approve não deve zerar jd_enriched")
        self.assertIsNotNone(result["bigfive_profile"], "approve não deve zerar bigfive")
        self.assertEqual(
            result["pipeline_template_id"], "template-uuid-123",
            "approve não deve zerar pipeline_template_id",
        )
        self.assertEqual(
            len(result["wsi_questions"]), 2,
            "approve não deve zerar wsi_questions",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
