"""
HITL (Human-In-The-Loop) canonical action registry — single source of truth.

W4-032 consolidation (2026-06-20): antes cada agent declarava sua própria
frozenset `_HITL_ACTION_TYPES` sem fonte compartilhada. Isso causou:
- Divergências silenciosas (mesmo conceito, nomes diferentes por domínio)
- Ações de alto risco esquecidas (ex: reject_candidate ausente em um agente)
- Sensor `check_agent_hitl_gates.py` verificava presença do frozenset, mas
  não coerência inter-agentes

Este módulo é a FONTE ÚNICA DE VERDADE para o conjunto canônico de ações que
requerem aprovação humana ANTES de executar side-effects.

Critérios de inclusão (uma ação deve estar aqui se):
  1. É IRREVERSÍVEL — rejeição de candidato, deleção de vaga, publicação
  2. É COMUNICAÇÃO EXTERNA — envia mensagem, email, WhatsApp para candidato
  3. É OPERAÇÃO BULK — afeta múltiplos candidatos/vagas atomicamente
  4. É MUTAÇÃO EM SISTEMA EXTERNO — sync ATS, webhook, integração terceira
  5. Risco LGPD Art. 7 — decisão automatizada afetando candidato (w/ audit)

Não incluir:
  - Operações read-only (search, list, get)
  - Movimentações internas reversíveis (ex: mover candidato entre estágios
    internos sem dispatch de comunicação)
  - Ações de navegação UI (open_panel, navigate_to)

Consumidores:
  - app/domains/*/agents/*_react_agent.py → cada agente declara `_HITL_ACTION_TYPES`
    como subconjunto deste canonical (pode restringir ao seu domínio)
  - app/shared/hitl/agent_gate.py → maybe_request_hitl_approval recebe o subconjunto
  - scripts/check_hitl_canonical_strings.py → sensor AST verifica coerência
  - tests/contract/test_hitl_canonical_actions.py → pin de regressão

Manutenção:
  Para ADICIONAR nova ação HITL, 3 lugares obrigatórios:
    1. Este arquivo → HITL_REQUIRED_ACTIONS (frozenset)
    2. Agent(s) relevante(s) → _HITL_ACTION_TYPES (subconjunto)
    3. Teste T-a em test_hitl_canonical_actions.py → HIGH_RISK_ACTIONS (se alto risco)
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# HITL_REQUIRED_ACTIONS — frozenset canônica completa
# ---------------------------------------------------------------------------
# Organizado por domínio para facilitar auditoria.
# Cada entrada corresponde a um `action_type` string que agentes passam para
# maybe_request_hitl_approval() / hitl_preflight().
# ---------------------------------------------------------------------------

HITL_REQUIRED_ACTIONS: frozenset[str] = frozenset({
    # ── PIPELINE / CV Screening ──────────────────────────────────────────────
    # Rejeições bulk — irreversíveis e comunicadas externamente
    "bulk_move_candidates",
    "bulk_reject_candidates",
    "auto_advance_stage",
    "auto_reject_low_score",
    "pipeline_transition",

    # ── KANBAN / Recruiter Assistant ─────────────────────────────────────────
    "move_candidate",
    "bulk_move",
    "bulk_reject",
    "bulk_advance",
    "reject_candidate",

    # ── COMMUNICATION ────────────────────────────────────────────────────────
    # Comunicações externas ao candidato — LGPD Art. 7 + irreversíveis
    "initial_contact",
    "rejection_feedback",
    "offer_letter",
    "send_batch_communication",

    # ── ANALYTICS ────────────────────────────────────────────────────────────
    # Export com dados de candidatos (PII) + envio externo
    "export_report",
    "share_dashboard",
    "send_report_email",
    "export_candidates_csv",
    "schedule_recurring_export",

    # ── ATS INTEGRATION ──────────────────────────────────────────────────────
    # Mutação em sistema externo — irreversível, cria/atualiza/rejeita em ATS
    "sync_to_ats",
    "webhook_trigger",
    "ats_create_application",
    "ats_update_application",
    "ats_reject_application",

    # ── AUTOMATION ───────────────────────────────────────────────────────────
    # Mutações de regras de automação — afetam fluxos futuros em cascata
    "activate_automation",
    "deactivate_automation",
    "delete_automation",
    "bulk_trigger_automation",
    "schedule_recurring_task",

    # ── JOBS MANAGEMENT ──────────────────────────────────────────────────────
    # Publicação = comunicação externa; delete = irreversível
    "publish_vacancy",
    "unpublish_vacancy",
    "duplicate_vacancy",
    "bulk_vacancy_status_change",
    "delete_vacancy",

    # ── TALENT FUNNEL ────────────────────────────────────────────────────────
    "bulk_shortlist",
    "bulk_sourcing_outreach",
    "import_external_candidates",
    "talent_pool_assignment",
    "auto_reject_funnel",

    # ── RECRUITER COPILOT (federado) ─────────────────────────────────────────
    # batch_move / bulk_candidate_move são alias de bulk_move_candidates
    # — mantidos aqui para que o federated gate funcione sem renaming dos agentes
    "batch_move_candidates",
    "bulk_candidate_move",
    "pause_job",
    "reopen_job",

    # ── REST BULK ACTIONS (GAP-03-008) ───────────────────────────────────────
    # Endpoints REST com HITL gate via hitl_preflight()
    "bulk_assign",
    "bulk_delete",

    # ── COMPANY SETTINGS ─────────────────────────────────────────────────────
    # Mudancas de politica e configuracao tem impacto sistemico em todos os fluxos
    "update_company_policy",
    "toggle_lia_field",
    "update_culture_profile",
    "update_hiring_policy",
    "delete_company_data",

    # ── COMMUNICATION (action executor path) ─────────────────────────────────
    # Comunicacoes externas via orchestrator action executor
    "send_email",
    "send_whatsapp",
    "send_candidate_report",
    "send_feedback",
    "send_progress_report",
    "send_screening_invite",
    "send_interview_reminder",
    "export_candidates",
})


# ---------------------------------------------------------------------------
# Domain-scoped subsets (helpers para agentes que querem importar direto)
# ---------------------------------------------------------------------------
# Cada agente PODE importar seu subset ou continuar declarando local.
# Usar estes para novos agentes — mantém coerência automática.
# ---------------------------------------------------------------------------

HITL_PIPELINE_ACTIONS: frozenset[str] = frozenset({
    "bulk_move_candidates",
    "bulk_reject_candidates",
    "auto_advance_stage",
    "auto_reject_low_score",
    "pipeline_transition",
})

HITL_KANBAN_ACTIONS: frozenset[str] = frozenset({
    "move_candidate",
    "bulk_move",
    "bulk_reject",
    "bulk_advance",
    "reject_candidate",
})

HITL_COMMUNICATION_ACTIONS: frozenset[str] = frozenset({
    "initial_contact",
    "rejection_feedback",
    "offer_letter",
    "send_batch_communication",
})

HITL_ANALYTICS_ACTIONS: frozenset[str] = frozenset({
    "export_report",
    "share_dashboard",
    "send_report_email",
    "export_candidates_csv",
    "schedule_recurring_export",
})

HITL_ATS_INTEGRATION_ACTIONS: frozenset[str] = frozenset({
    "sync_to_ats",
    "webhook_trigger",
    "ats_create_application",
    "ats_update_application",
    "ats_reject_application",
})

HITL_AUTOMATION_ACTIONS: frozenset[str] = frozenset({
    "activate_automation",
    "deactivate_automation",
    "delete_automation",
    "bulk_trigger_automation",
    "schedule_recurring_task",
})

HITL_JOBS_MGMT_ACTIONS: frozenset[str] = frozenset({
    "publish_vacancy",
    "unpublish_vacancy",
    "duplicate_vacancy",
    "bulk_vacancy_status_change",
    "delete_vacancy",
})

HITL_TALENT_FUNNEL_ACTIONS: frozenset[str] = frozenset({
    "bulk_shortlist",
    "bulk_sourcing_outreach",
    "import_external_candidates",
    "talent_pool_assignment",
    "auto_reject_funnel",
})

HITL_COPILOT_ACTIONS: frozenset[str] = frozenset({
    "batch_move_candidates",
    "bulk_candidate_move",
    "send_batch_communication",
    "pause_job",
    "reopen_job",
    "publish_vacancy",
    "unpublish_vacancy",
})

HITL_REST_BULK_ACTIONS: frozenset[str] = frozenset({
    "bulk_assign",
    "bulk_delete",
})

HITL_COMPANY_SETTINGS_ACTIONS: frozenset[str] = frozenset({
    "update_company_policy",
    "toggle_lia_field",
    "update_culture_profile",
    "update_hiring_policy",
    "delete_company_data",
})

HITL_COMMUNICATION_EXECUTOR_ACTIONS: frozenset[str] = frozenset({
    "send_email",
    "send_whatsapp",
    "send_candidate_report",
    "send_feedback",
    "send_progress_report",
    "send_screening_invite",
    "send_interview_reminder",
    "export_candidates",
})

# Sanity check: all domain subsets must be subsets of HITL_REQUIRED_ACTIONS
_ALL_DOMAIN_SUBSETS = (
    HITL_PIPELINE_ACTIONS
    | HITL_KANBAN_ACTIONS
    | HITL_COMMUNICATION_ACTIONS
    | HITL_ANALYTICS_ACTIONS
    | HITL_ATS_INTEGRATION_ACTIONS
    | HITL_AUTOMATION_ACTIONS
    | HITL_JOBS_MGMT_ACTIONS
    | HITL_TALENT_FUNNEL_ACTIONS
    | HITL_COPILOT_ACTIONS
    | HITL_REST_BULK_ACTIONS
    | HITL_COMPANY_SETTINGS_ACTIONS
    | HITL_COMMUNICATION_EXECUTOR_ACTIONS
)

assert _ALL_DOMAIN_SUBSETS <= HITL_REQUIRED_ACTIONS, (
    "BUG: domain subset contém ação NÃO em HITL_REQUIRED_ACTIONS: "
    + str(_ALL_DOMAIN_SUBSETS - HITL_REQUIRED_ACTIONS)
)
