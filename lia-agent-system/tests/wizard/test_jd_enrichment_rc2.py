"""RC2 — jd_enrichment gera a JD das competencias confirmadas no happy path
do funil conversacional, em vez de pedir "cole a JD" (Paulo 2026-05-30).

Bug: apos o intake_gate aprovar (intake_approved=True) com titulo+senioridade+
competencias confirmadas (Fase 3), o jd_enrichment ainda disparava o guard
intent_only → ask_for_jd ("cole a JD"). O funil conversacional nunca gerava a
JD — o usuario tinha que colar uma. service.enrich JA consome confirmed_* (Fase
4), entao o material estruturado basta pra gerar.

Fix: intake_approved + title + seniority → _classifier_eligible=False → gera.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import unittest

_REPO = Path("/home/runner/workspace/lia-agent-system")
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _fake_enriched():
    return {
        "titulo_padronizado": "Desenvolvedor Python Sênior",
        "senioridade_confirmada": "senior",
        "about_role": "Atua como referência técnica em Python.",
        "responsabilidades": ["Liderar arquitetura", "Code review"],
        "skills_obrigatorias": [{"skill": "Python", "contexto": "core"}],
        "skills_desejaveis": [],
        "competencias_comportamentais": [
            {"competencia": "Comunicação", "contexto": "squad", "trait_big_five": "extraversion"},
        ],
        "context_signals": {}, "alteracoes_realizadas": [], "fairness_corrections": [],
        "wsi_quality_score": 90.0, "wsi_quality_warnings": [],
    }


def _state(intake_approved):
    return {
        "raw_input": "quero abrir uma vaga de desenvolvedor python senior",
        "user_query": "quero abrir uma vaga de desenvolvedor python senior",
        "parsed_title": "Desenvolvedor Python Sênior",
        "parsed_seniority": "Sênior",
        "parsed_model": "hibrido",
        "confirmed_technical_competencies": [{"skill": "Python", "contexto": "core"}],
        "confirmed_behavioral_competencies": [
            {"competencia": "Comunicação", "contexto": "x", "trait_big_five": "extraversion"},
        ],
        "screening_mode": "compact",
        "intake_approved": intake_approved,
        "workspace_id": "co", "company_id": "co",
    }


def _run(state):
    jde = importlib.import_module("app.domains.job_creation.nodes.jd_enrichment")
    graph_mod = importlib.import_module("app.domains.job_creation.graph")
    fake_service = mock.Mock()
    fake_service.enrich.return_value = (
        SimpleNamespace(model_dump=_fake_enriched), 90.0, [],
    )
    with mock.patch.object(graph_mod, "_get_jd_service", return_value=fake_service), \
         mock.patch.object(graph_mod, "_suggest_pipeline_template", return_value=None), \
         mock.patch.object(graph_mod, "_build_pipeline_template_db_suggestion", return_value=None), \
         mock.patch.object(graph_mod, "_apply_pipeline_template_to_state", side_effect=lambda s, *a, **k: s):
        return jde.jd_enrichment_node(state)


class RC2(unittest.TestCase):
    def test_approved_intake_generates_jd_not_ask(self):
        """intake_approved + título + senioridade → gera a JD (não pede)."""
        result = _run(_state(intake_approved=True))
        data = (result.get("ws_stage_payload") or {}).get("data") or {}
        self.assertNotEqual(data.get("awaiting_jd_input"), True,
                            "RC2: não pode pedir 'cole a JD' no funil aprovado")
        self.assertTrue(result.get("jd_enriched"),
                       "deveria ter gerado a JD das competências confirmadas")

    def test_enrich_received_confirmed_competencies(self):
        """A geração consome as confirmed_competencies (Fase 4)."""
        jde = importlib.import_module("app.domains.job_creation.nodes.jd_enrichment")
        graph_mod = importlib.import_module("app.domains.job_creation.graph")
        fake_service = mock.Mock()
        fake_service.enrich.return_value = (SimpleNamespace(model_dump=_fake_enriched), 90.0, [])
        with mock.patch.object(graph_mod, "_get_jd_service", return_value=fake_service), \
             mock.patch.object(graph_mod, "_suggest_pipeline_template", return_value=None), \
             mock.patch.object(graph_mod, "_build_pipeline_template_db_suggestion", return_value=None), \
             mock.patch.object(graph_mod, "_apply_pipeline_template_to_state", side_effect=lambda s, *a, **k: s):
            jde.jd_enrichment_node(_state(intake_approved=True))
        _, kwargs = fake_service.enrich.call_args
        self.assertTrue(kwargs.get("confirmed_technical"))
        self.assertEqual(kwargs.get("seniority"), "Sênior")

    def test_not_approved_still_asks(self):
        """Anti-regressão: SEM aprovação do intake, o guard ainda pede JD
        (não inventa do nada para intent_only)."""
        fake_intent = SimpleNamespace(intent="intent_only", confidence=0.9,
                                      conversational_reply="me passa a JD")
        fake_cls = mock.Mock(); fake_cls.classify_sync.return_value = fake_intent
        with mock.patch(
            "app.domains.job_creation.services.intake_intent_classifier.get_intake_intent_classifier",
            return_value=fake_cls,
        ):
            result = _run(_state(intake_approved=None))
        data = (result.get("ws_stage_payload") or {}).get("data") or {}
        self.assertEqual(data.get("awaiting_jd_input"), True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
