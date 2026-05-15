"""Task #1096 — Sentinela do contrato ``ws_stage_payload.data.message`` no
``jd_enrichment_node``.

Bug original: ao mandar "vamos abrir uma vaga" no chat (intent puro, sem JD),
o wizard caía no fail-loud da Task #1089 (``[ATENÇÃO: estado inconsistente —
contate suporte]``) porque o ``jd_enrichment_node`` populava ``data`` com
``jd_raw``/``jd_enriched``/``quality_score``/``suggestions_data`` mas NUNCA
``data.message``. ``WizardSessionService`` (linha 786-789) procura
``stage_data.get("message") or stage_data.get("response_text")`` — ambos
vazios — e dispara ``_emit_silent_fallback``.

Canonical-fix: a correção é na FONTE (``jd_enrichment_node``), não no consumer.
Dois cenários:

  S1 — Input-thin guard: mensagem de intenção curta (<100 chars, sem panel
       form, sem attachment, sem parsed_title) NÃO chama o LLM e devolve
       ``data.message`` pedindo material da JD.
  S2 — Enriquecimento normal: ``data.message`` é parametrizada pelo título
       enriquecido + quality_score + flag de fallback (não é canned literal).
  S3 — Fallback determinístico (LLM timeout/erro): ``data.message`` reflete
       o estado degradado e pede confirmação.

Sentinela arquitetural reforçando o invariant: TODA execução do
``jd_enrichment_node`` que retorna ``current_stage="jd_enrichment"`` deve
incluir ``ws_stage_payload.data.message`` truthy. Se um futuro refactor
remover esse campo, o ``WizardSessionService`` volta a falhar fail-loud.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_BACKEND_ROOT))


def _base_state(**overrides):
    state = {
        "session_id": "sess-test-1096",
        "user_id": "user-test",
        "company_id": "00000000-0000-4000-a000-000000000001",
        "workspace_id": 1,
        "raw_input": "",
        "user_query": "",
        "stage_history": [],
        "conversation_messages": [],
    }
    state.update(overrides)
    return state


def _data_of(result: dict) -> dict:
    payload = (result or {}).get("ws_stage_payload") or {}
    return payload.get("data") or {}


class WizardJdEnrichmentMessageT1096(unittest.TestCase):
    # ---------------------------------------------------------------- S1
    def test_S1_input_thin_intent_message_does_not_call_llm_and_sets_message(self):
        """'vamos abrir uma vaga' (intent puro, <100 chars) → guard sem LLM."""
        from app.domains.job_creation.graph import jd_enrichment_node

        state = _base_state(
            raw_input="vamos abrir uma vaga",
            user_query="vamos abrir uma vaga",
        )

        with patch(
            "app.domains.job_creation.graph._get_jd_service"
        ) as mock_service_factory:
            result = jd_enrichment_node(state)
            mock_service_factory.assert_not_called()  # LLM NÃO foi chamado

        self.assertEqual(result.get("current_stage"), "jd_enrichment")
        self.assertFalse(result.get("requires_approval"))
        self.assertIsNone(result.get("jd_enriched"))

        data = _data_of(result)
        self.assertTrue(data.get("awaiting_jd_input"))
        self.assertTrue(
            data.get("message"),
            "data.message DEVE ser populada — sem isso WizardSessionService "
            "cai em _emit_silent_fallback (Task #1089 T3).",
        )
        self.assertNotIn("[ATENÇÃO", data["message"])

    # ---------------------------------------------------------------- S2
    def test_S2_normal_enrichment_populates_contextual_message(self):
        """Enriquecimento bem-sucedido produz ``data.message`` com título + score."""
        from app.domains.job_creation.graph import jd_enrichment_node

        state = _base_state(
            raw_input=(
                "Procuramos Engenheiro Backend Pleno para atuar com Python, "
                "FastAPI e PostgreSQL. Responsabilidades: arquitetar APIs REST, "
                "manter pipelines de dados e revisar PRs do time. Diferencial: "
                "experiência com LangGraph e RAG. Modelo híbrido em São Paulo."
            ),
            user_query="",
            parsed_title="Engenheiro Backend Pleno",
        )

        # Stub determinístico do JdEnrichmentService — evita rede.
        fake_enriched = MagicMock()
        fake_enriched.model_dump.return_value = {
            "titulo_padronizado": "Engenheiro de Software Backend Pleno",
            "about_role": "Vaga descrita.",
            "responsabilidades": ["arquitetar APIs", "revisar PRs"],
            "skills_obrigatorias": [{"skill": "Python", "contexto": "FastAPI"}],
            "skills_desejaveis": [],
            "competencias_comportamentais": [],
        }
        fake_enriched.wsi_quality_warnings = []
        fake_enriched.confidence = 0.9

        fake_service = MagicMock()
        fake_service.enrich.return_value = (fake_enriched, 78.0, [])

        with patch(
            "app.domains.job_creation.graph._get_jd_service",
            return_value=fake_service,
        ), patch(
            "app.domains.job_creation.graph.calculate_completeness",
            return_value=20.0,
        ):
            result = jd_enrichment_node(state)

        self.assertEqual(result.get("current_stage"), "jd_enrichment")
        self.assertTrue(result.get("requires_approval"))

        data = _data_of(result)
        msg = data.get("message")
        self.assertTrue(msg, "data.message obrigatória pós-enriquecimento.")
        self.assertIn("Engenheiro", msg)  # parametrizada pelo título
        self.assertIn("78", msg)  # parametrizada pelo score
        self.assertNotIn("[ATENÇÃO", msg)

    # ---------------------------------------------------------------- S3
    def test_S3_fallback_path_message_signals_degraded_mode(self):
        """LLM em fallback (timeout/erro) → ``data.message`` declara modo degradado."""
        import concurrent.futures as _cf
        from app.domains.job_creation.graph import jd_enrichment_node

        state = _base_state(
            raw_input=(
                "Procuramos Coordenador de Marketing Sênior para liderar "
                "estratégia de growth, gestão de mídia paga e branding. "
                "Pelo menos 5 anos de experiência. Modelo remoto."
            ),
            user_query="",
            parsed_title="Coordenador de Marketing",
        )

        fake_fallback = MagicMock()
        fake_fallback.model_dump.return_value = {
            "titulo_padronizado": "Coordenador de Marketing Sênior",
            "about_role": "(fallback)",
            "responsabilidades": [],
            "skills_obrigatorias": [],
            "skills_desejaveis": [],
            "competencias_comportamentais": [],
        }
        fake_fallback.wsi_quality_warnings = []

        fake_service = MagicMock()
        fake_service.enrich.side_effect = _cf.TimeoutError()
        fake_service._fallback_enrichment.return_value = fake_fallback

        with patch(
            "app.domains.job_creation.graph._get_jd_service",
            return_value=fake_service,
        ), patch(
            "app.domains.job_creation.graph.calculate_completeness",
            return_value=20.0,
        ), patch(
            "app.domains.job_creation.services.jd_enrichment.calculate_quality_score",
            return_value=(35.0, ["fallback_used"]),
        ):
            result = jd_enrichment_node(state)

        data = _data_of(result)
        msg = (data.get("message") or "").lower()
        self.assertTrue(msg, "fallback path também precisa de data.message.")
        self.assertTrue(
            "degradado" in msg or "mínimo" in msg or "fallback" in msg,
            f"Mensagem de fallback deve sinalizar modo degradado: {msg!r}",
        )
        self.assertTrue(data.get("jd_enrichment_used_fallback"))


if __name__ == "__main__":
    unittest.main()
