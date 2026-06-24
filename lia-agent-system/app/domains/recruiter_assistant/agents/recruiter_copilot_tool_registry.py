"""
RecruiterCopilot tool registry — superficie FEDERADA do chat global da LIA.

Problema (transcript Paulo 2026-06-03): o chat lateral global caia no dominio
`recruiter_assistant`, que so resolvia pra UM agente de pagina (talent OU
kanban) e NUNCA pro de vagas. "liste minhas vagas" caia num LLM sem ferramenta
-> confabulava "nenhuma vaga". As ferramentas existiam, presas em agentes de
pagina (jobs_mgmt, talent, kanban).

Este registry CURA um set focado (leitura + acoes essenciais) referenciando as
ToolDefinitions CANONICAS dos tres registries de origem — sem duplicar logica.
Cada tool ja carrega multi-tenancy (company_id fail-closed via @tool_handler /
require_company_id_from_context), audit e HITL (GovernanceToolNode) do seu
registry de origem.

Curadoria (vs dump dos ~45 tools): ReAct degrada com toolset gigante. Mantemos
~11 tools cobrindo P0 (leitura de vagas+candidatos+pipeline) e P1 (mover
candidato, pausar/reabrir vaga). Colisoes de nome (generate_report,
get_pipeline_prediction) ficam de fora de proposito.

Sensor: tests/contract/test_recruiter_copilot_federation.py
"""
from __future__ import annotations

import logging

from lia_agents_core.tool_adapter import ToolDefinition

logger = logging.getLogger(__name__)

# (registry_de_origem, tool_name) — a ordem importa para a selecao do LLM.
_FEDERATION_SPEC: list[tuple[str, str]] = [
    # --- Leitura de vagas (P0) ---
    ("jobs", "list_jobs"),
    ("jobs", "view_job_details"),
    ("jobs", "get_portfolio_metrics"),
    # --- Leitura de candidatos (P0) ---
    ("talent", "list_candidates"),
    ("talent", "search_candidates"),
    ("talent", "view_candidate_profile"),
    # --- Leitura de pipeline (P0) ---
    ("kanban", "get_pipeline_summary"),
    ("kanban", "list_stage_candidates"),
    # --- Leitura de headcount (Track B) — torna o plano consumivel pelo chat ---
    ("workforce", "get_workforce_plan_summary"),
    # --- Resultados de screening (P1-2) — WSI score + BigFive do candidato ---
    # view_screening_results: lê score WSI e detalhamento de triagem.
    # Fonte: pipeline_tool_registry (cv_screening_pipeline).
    ("cv_screening_pipeline", "view_screening_results"),
    # BigFive/OCEAN per-candidato (P2-2) -- le lia_opinions.behavioral_analysis.ocean_traits
    ("talent", "get_candidate_bigfive"),
    # --- Acoes de escrita (P1) — HITL/audit herdados do registry de origem ---
    # F3 (2026-06-09): update_candidate_stage e reject_candidate gateados via hitl_preflight
    ("cv_screening", "update_candidate_stage"),
    ("cv_screening", "reject_candidate"),
    ("kanban", "batch_move_candidates"),
    ("kanban", "send_batch_communication"),
    ("jobs", "close_job"),   # F4: encerrar vaga (já gateado com HITL)
    ("jobs", "pause_job"),
    ("jobs", "reopen_job"),
    # --- Comunicação individual (P1-3) — email + whatsapp direto ao candidato ---
    # Ambas gateadas via HITL (side_effects=send) e auditadas.
    ("communication", "send_email"),
    ("communication", "send_whatsapp"),
    # --- Agendamento de entrevista (P1-6) ---
    ("interview_scheduling", "schedule_interview"),
    ("interview_scheduling", "check_interviewer_availability"),
    # --- Criar vaga a partir de fonte (P1) — glue agentic (Opcao A / A2) ---
    # recruiter_copilot conduz a identificacao da fonte e dispara a semente.
    ("wizard", "list_job_creation_sources"),
    ("wizard", "start_creation_from_source"),
    # --- Abrir modal/painel (Fase B) — mecanismo determinístico open_ui ---
    ("ui", "open_ui"),
    # --- Ponte in-page (Fase 2 slice 1) — filtra/ordena tabela aberta ---
    ("ui", "apply_table_state"),
    ("ui", "select_rows"),  # Fase 2 surface close
]


def _source_maps() -> dict[str, dict[str, ToolDefinition]]:
    from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
        get_jobs_mgmt_tools,
    )
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        get_kanban_tools,
    )
    from app.domains.recruiter_assistant.agents.talent_tool_registry import (
        get_talent_tools,
    )
    from app.domains.job_management.agents.wizard_tool_registry import (
        get_wizard_tools,
    )
    from app.domains.workforce.agents.workforce_tool_registry import (
        get_workforce_tools,
    )
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        get_ui_tools,
    )
    from app.domains.cv_screening.tools.candidate_tools import (
        get_candidate_mutation_tools,
    )
    from app.domains.cv_screening.agents.pipeline_tool_registry import (
        get_pipeline_tools,
    )
    from app.domains.communication.agents.communication_tool_registry import (
        get_communication_tools,
    )
    from app.domains.interview_scheduling.agents.interview_scheduling_tool_registry import (
        get_interview_scheduling_tools,
    )
    return {
        "jobs": {t.name: t for t in get_jobs_mgmt_tools()},
        "talent": {t.name: t for t in get_talent_tools()},
        "kanban": {t.name: t for t in get_kanban_tools()},
        "wizard": {t.name: t for t in get_wizard_tools()},
        "workforce": {t.name: t for t in get_workforce_tools()},
        "ui": {t.name: t for t in get_ui_tools()},
        "cv_screening": {t.name: t for t in get_candidate_mutation_tools()},
        # cv_screening_pipeline: read-only screening results (WSI score, BigFive)
        # fonte: pipeline_tool_registry (todos os stages). Separado de cv_screening
        # para nao duplicar nomes de write-tools (update_candidate_stage, etc).
        "cv_screening_pipeline": {t.name: t for t in get_pipeline_tools()},
        "communication": {t.name: t for t in get_communication_tools()},
        "interview_scheduling": {t.name: t for t in get_interview_scheduling_tools()},
    }


def get_recruiter_copilot_tools() -> list[ToolDefinition]:
    """Set FEDERADO curado para o chat global.

    Falha ALTO (RuntimeError) se um tool esperado sumir do registry de origem
    (CLAUDE.md REGRA 4 anti-silent-fallback) — melhor quebrar no boot do que o
    chat global voltar a ficar 'cego' silenciosamente em producao.
    """
    maps = _source_maps()
    out: list[ToolDefinition] = []
    seen: set[str] = set()
    missing: list[str] = []
    for src, name in _FEDERATION_SPEC:
        td = maps[src].get(name)
        if td is None:
            missing.append(f"{src}:{name}")
            continue
        if td.name in seen:
            continue
        out.append(td)
        seen.add(td.name)
    if missing:
        raise RuntimeError(
            "[recruiter_copilot] ferramentas federadas ausentes nos registries "
            f"de origem: {missing}. Atualize _FEDERATION_SPEC ou o registry fonte."
        )
    return out


def get_recruiter_copilot_tool_names() -> list[str]:
    return [t.name for t in get_recruiter_copilot_tools()]
