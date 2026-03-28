"""Tests for Bloco 1 — ReAct agents as default path in all 3 orchestrated endpoints.

These tests validate that:
- USE_REACT_AGENTS flag was removed (agents are always the default)
- Phase 2 (ReAct agent) is present before the legacy fallback
- Phase 0 (pending actions) and Phase 1 (actionable intents) are preserved
- Graceful fallback exists (no HTTP 500)
- candidate_education is included in view_candidate_profile
- kanban_tool_registry has view_candidate_full_profile with education
- libs/orchestrator exists as a proper monorepo lib
"""
import os
from pathlib import Path

# Project root for resolving paths
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text()


# ── Endpoint: orchestrated_talent_chat ──────────────────────────────────────

def test_talent_chat_react_is_default():
    """TalentReActAgent deve ser chamado incondicionalmente (sem flag USE_REACT_AGENTS)."""
    content = _read("app/api/v1/orchestrated_talent_chat.py")
    assert "USE_REACT_AGENTS" not in content, "USE_REACT_AGENTS flag ainda presente no talent_chat"
    assert "PHASE 2: TalentReActAgent" in content
    assert "PHASE 3 (FALLBACK)" in content


def test_talent_chat_phase0_preserved():
    """Phase 0 (pending actions/confirmations) deve ser preservado."""
    content = _read("app/api/v1/orchestrated_talent_chat.py")
    assert "PHASE 0" in content or "pending_action_store.get" in content


def test_talent_chat_phase1_preserved():
    """Phase 1 (actionable UI intents) deve ser preservado antes do ReAct agent."""
    content = _read("app/api/v1/orchestrated_talent_chat.py")
    assert "detect_actionable_intent" in content


def test_talent_chat_graceful_fallback():
    """Se TalentReActAgent falha, deve cair no TalentAssistantService (não HTTP 500)."""
    content = _read("app/api/v1/orchestrated_talent_chat.py")
    assert "falling back to legacy" in content


# ── Endpoint: orchestrated_job_chat ─────────────────────────────────────────

def test_job_chat_react_is_default():
    """KanbanReActAgent deve ser chamado incondicionalmente."""
    content = _read("app/api/v1/orchestrated_job_chat.py")
    assert "USE_REACT_AGENTS" not in content, "USE_REACT_AGENTS flag ainda presente no job_chat"
    assert "PHASE 2: KanbanReActAgent" in content
    assert "PHASE 3 (FALLBACK)" in content


def test_job_chat_graceful_fallback():
    """Se KanbanReActAgent falha, deve cair no KanbanAssistant (não HTTP 500)."""
    content = _read("app/api/v1/orchestrated_job_chat.py")
    assert "falling back to legacy" in content


# ── Endpoint: orchestrated_jobs_management ──────────────────────────────────

def test_jobs_mgmt_react_is_default():
    """JobsManagementReActAgent deve ser chamado incondicionalmente."""
    content = _read("app/api/v1/orchestrated_jobs_management.py")
    assert "USE_REACT_AGENTS" not in content, "USE_REACT_AGENTS flag ainda presente em jobs_management"
    assert "PHASE 2: JobsManagementReActAgent" in content
    assert "PHASE 3 (FALLBACK)" in content


def test_jobs_mgmt_graceful_fallback():
    """Se JobsManagementReActAgent falha, deve cair no legacy (não HTTP 500)."""
    content = _read("app/api/v1/orchestrated_jobs_management.py")
    assert "falling back to legacy" in content


# ── Tool registries ──────────────────────────────────────────────────────────

def test_talent_tool_view_profile_includes_education():
    """view_candidate_profile em talent_tool_registry deve buscar candidate_education."""
    content = _read("app/domains/recruiter_assistant/agents/talent_tool_registry.py")
    assert "candidate_education" in content, "Tabela candidate_education não está sendo consultada"
    assert '"education"' in content, "Campo education não presente no perfil retornado"
    assert "work_history" in content, "Campo work_history não presente no perfil retornado"


def test_talent_tool_profile_has_salary_fields():
    """view_candidate_profile deve incluir salary_expectation_clt/pj e work_model."""
    content = _read("app/domains/recruiter_assistant/agents/talent_tool_registry.py")
    assert "salary_expectation" in content
    assert "work_model" in content


def test_kanban_tool_has_view_full_profile():
    """kanban_tool_registry deve ter view_candidate_full_profile com education."""
    content = _read("app/domains/recruiter_assistant/agents/kanban_tool_registry.py")
    assert "view_candidate_full_profile" in content, "Tool view_candidate_full_profile não encontrada no kanban registry"
    assert "candidate_education" in content, "Kanban não busca candidate_education"
    assert '"education"' in content


# ── libs/orchestrator (Fase 6b) ──────────────────────────────────────────────

def test_libs_orchestrator_pyproject_exists():
    """libs/orchestrator deve ter pyproject.toml."""
    assert (PROJECT_ROOT / "libs/orchestrator/pyproject.toml").exists(), \
        "libs/orchestrator/pyproject.toml não existe"


def test_libs_orchestrator_init_exists():
    """libs/orchestrator deve ter lia_orchestrator/__init__.py."""
    assert (PROJECT_ROOT / "libs/orchestrator/lia_orchestrator/__init__.py").exists(), \
        "libs/orchestrator/lia_orchestrator/__init__.py não existe"


def test_libs_orchestrator_in_workspace():
    """lia-orchestrator deve estar no pyproject.toml workspace root."""
    content = _read("pyproject.toml")
    assert "lia-orchestrator" in content, "lia-orchestrator não registrado no pyproject.toml"


def test_backend_company_id_field_talent():
    """OrchestratedTalentChatRequest deve ter campo company_id."""
    content = _read("app/api/v1/orchestrated_talent_chat.py")
    assert 'company_id: str = Field' in content
    assert 'company_id="demo"' not in content
    assert 'request.company_id' in content


def test_backend_company_id_field_job():
    """OrchestratedJobChatRequest deve ter campo company_id."""
    content = _read("app/api/v1/orchestrated_job_chat.py")
    assert 'company_id: str = Field' in content
    assert 'company_id="demo"' not in content
    assert 'request.company_id' in content


def test_backend_company_id_field_jobs_mgmt():
    """OrchestratedJobsManagementRequest deve ter campo company_id."""
    content = _read("app/api/v1/orchestrated_jobs_management.py")
    assert 'company_id: str = Field' in content
    assert 'company_id="demo"' not in content
    assert 'request.company_id' in content


def test_frontend_company_id_in_types():
    """kanban-assistant.ts deve declarar company_id nos 3 tipos de request."""
    content = _read("../plataforma-lia/src/lib/api/kanban-assistant.ts")
    # Conta quantas vezes company_id? aparece nos request interfaces
    assert content.count("company_id?: string") >= 3


def test_frontend_conversation_id_talent_state():
    """candidates-page deve ter estado talentConversationId para multi-turn."""
    content = _read("../plataforma-lia/src/components/pages/candidates-page.tsx")
    assert "talentConversationId" in content
    assert "setTalentConversationId" in content


def test_frontend_conversation_id_jobs_state():
    """jobs-page deve ter estado jobsConversationId para multi-turn."""
    content = _read("../plataforma-lia/src/components/pages/jobs-page.tsx")
    assert "jobsConversationId" in content
    assert "setJobsConversationId" in content


def test_talent_system_prompt_tool_instruction():
    """talent_system_prompt deve instruir o agente a usar view_candidate_profile para dados de perfil."""
    content = _read("app/domains/recruiter_assistant/agents/talent_system_prompt.py")
    assert "view_candidate_profile" in content
    assert "formacao" in content.lower() or "formação" in content.lower()


def test_kanban_system_prompt_tool_instruction():
    """kanban_system_prompt deve instruir o agente a usar view_candidate_full_profile."""
    content = _read("app/domains/recruiter_assistant/agents/kanban_system_prompt.py")
    assert "view_candidate_full_profile" in content


def test_react_loop_injects_company_id_into_tool_args():
    """react_loop deve injetar company_id do context nos tool_args antes de chamar a função."""
    content = _read("libs/agents-core/lia_agents_core/react_loop.py")
    assert 'context.get("company_id")' in content
    assert '"company_id" not in tool_args' in content
    assert 'tool_args["company_id"] = context["company_id"]' in content


def test_libs_orchestrator_pth_file():
    """lia-orchestrator.pth deve existir no site-packages para importação."""
    # .pth files ficam no workspace-level .pythonlibs (compartilhado entre projetos Replit)
    candidates = [
        Path("/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages/lia-orchestrator.pth"),
        Path("/home/runner/workspace/lia-agent-system/.pythonlibs/lib/python3.11/site-packages/lia-orchestrator.pth"),
    ]
    found = any(p.exists() for p in candidates)
    assert found, f"Arquivo lia-orchestrator.pth não encontrado em nenhum dos caminhos: {candidates}"
