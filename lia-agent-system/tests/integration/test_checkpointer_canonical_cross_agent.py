"""
Feature-impact sensor — Onda 3 do PLAN_FIX_wizard_memory_loss.

Confirma que o fix de Onda 1 (PostgresSaver canonical via ConnectionPool)
propagou para TODOS os agents que usam `get_checkpointer()`:
  - WSIInterviewGraph (cv_screening) — entrevista WSI por telefone
  - InterviewGraph (interview_scheduling) — agendamento de entrevistas
  - JobWizardGraph (job_management) — caminho legacy/HITL resume do wizard

Sensor canonical: cada um destes agents importa
`lia_agents_core.checkpointer.get_checkpointer` e compila um StateGraph
com checkpointer. Verifica que o tipo retornado e PostgresSaver — nao
MemorySaver (regressao do bug V1.d).

Disciplinas CLAUDE.md aplicadas:
  - feature-impact: cobre 3 agents na mesma classe de bug.
  - harness-engineering: sensor de regressao computacional.
  - canonical-fix: zero codigo de producao alterado nesta onda (apenas
    sensor de seguranca contra regressao).
  - production-quality (ai-architecture): garante que os 3 agents
    persistem checkpoints em Postgres real.
"""
from __future__ import annotations

import os
import pytest


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — integration test requires real Postgres",
)


def test_canonical_get_checkpointer_returns_postgres_saver():
    """Re-confirma Onda 1: get_checkpointer() canonical = PostgresSaver."""
    from lia_agents_core.checkpointer import get_checkpointer
    saver = get_checkpointer()
    assert type(saver).__name__ == "PostgresSaver", (
        f"Regressao do fix Onda 1: get_checkpointer() retorna "
        f"{type(saver).__name__} em vez de PostgresSaver."
    )


def test_wsi_interview_graph_uses_canonical_postgres_saver():
    """WSIInterviewGraph (cv_screening) usa PostgresSaver via canonical."""
    from app.domains.cv_screening.agents.wsi_interview_graph import (
        WSIInterviewGraph,
    )
    from langgraph.pregel import Pregel  # compiled graph base

    graph = WSIInterviewGraph()
    compiled = graph._build_langgraph()

    # CompiledStateGraph wraps the checkpointer on the .checkpointer attr
    cp = getattr(compiled, "checkpointer", None)
    assert cp is not None, (
        "WSIInterviewGraph compilou sem checkpointer — bug critico."
    )
    assert type(cp).__name__ == "PostgresSaver", (
        f"WSIInterviewGraph usa {type(cp).__name__} em vez de PostgresSaver. "
        f"Regressao do fix Onda 1 propagaria para WSI."
    )


def test_interview_scheduling_graph_uses_canonical_postgres_saver():
    """InterviewGraph (interview_scheduling) usa PostgresSaver via canonical."""
    from app.domains.interview_scheduling.agents.interview_graph import (
        InterviewGraph,
    )

    graph = InterviewGraph()
    compiled = graph._build_langgraph()

    cp = getattr(compiled, "checkpointer", None)
    assert cp is not None, "InterviewGraph compilou sem checkpointer."
    assert type(cp).__name__ == "PostgresSaver", (
        f"InterviewGraph usa {type(cp).__name__} em vez de PostgresSaver."
    )


def test_job_creation_graph_uses_canonical_postgres_saver():
    """JobCreationGraph (caminho canonical do wizard de vaga) usa PostgresSaver.

    Sensor extra para o caminho canonico que sustenta o sintoma do Paulo
    (criar vaga > 3 turnos). Onda 1 P2-K removeu o _get_checkpointer
    local; este test garante que o fix continua valendo aqui.
    """
    from app.domains.job_creation.graph import get_job_creation_graph

    g = get_job_creation_graph()
    compiled = g._graph
    cp = getattr(compiled, "checkpointer", None)
    assert cp is not None, "JobCreationGraph compilou sem checkpointer."
    assert type(cp).__name__ == "PostgresSaver", (
        f"JobCreationGraph usa {type(cp).__name__} em vez de PostgresSaver."
    )
