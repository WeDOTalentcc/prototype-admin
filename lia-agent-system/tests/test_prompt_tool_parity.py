"""
Test: Prompt ↔ Tool Parity Validation.

Validates that prompts only reference tools that exist in the tool registry
and are accessible by the corresponding agent at runtime.

Task #145: Alinhar Prompts com Capacidades Reais.

NOTE: These tests are pure string/YAML parsing — no DB, no async, no imports
from app modules that trigger heavy initialization. This ensures fast execution.

Tool sources:
  - YAML registry (tool_registry_metadata.yaml): centralized tool metadata
  - YAML permissions (tool_permissions.yaml): scope-based access control
  - Domain tool registries (e.g. pipeline_tool_registry.py): agent-specific tools
  - Enhanced mixin tools (proactive_tools.py, predictive_tools.py, insight_tools.py):
    injected into all ReAct agents via EnhancedAgentMixin
"""
import os
import re

import pytest
import yaml

BASE = os.path.join(os.path.dirname(__file__), "..")
TOOLS_DIR = os.path.join(BASE, "app", "tools")


def _load_tool_registry_names() -> set[str]:
    path = os.path.join(TOOLS_DIR, "tool_registry_metadata.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    return {tool["name"] for tool in data.get("tools", [])}


def _load_scope_tools(scope: str) -> set[str]:
    path = os.path.join(TOOLS_DIR, "tool_permissions.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    scope_data = data.get("global", {}).get("scopes", {}).get(scope, {})
    query = set(scope_data.get("query", []) or [])
    action = set(scope_data.get("action", []) or [])
    return query | action


def _scan_tool_names_in_file(filepath: str) -> set[str]:
    """Extract tool names from a Python file via name= patterns."""
    with open(filepath) as f:
        content = f.read()
    return set(re.findall(r'name\s*=\s*"([a-z][a-z_]+)"', content))


def _scan_domain_tool_registry(registry_path: str) -> set[str]:
    """Scan a specific tool registry file for tool names."""
    if os.path.isfile(registry_path):
        return _scan_tool_names_in_file(registry_path)
    return set()


def _get_enhanced_mixin_tools() -> set[str]:
    """Get tool names from the shared enhanced mixin (proactive, predictive, insight)."""
    tools = set()
    shared_tools_dir = os.path.join(BASE, "app", "shared", "tools")
    for fname in ["proactive_tools.py", "predictive_tools.py", "insight_tools.py"]:
        fpath = os.path.join(shared_tools_dir, fname)
        if os.path.isfile(fpath):
            tools |= _scan_tool_names_in_file(fpath)
    return tools


def _read_prompt_file(rel_path: str) -> str:
    full = os.path.join(BASE, rel_path)
    with open(full) as f:
        return f.read()


def _extract_tool_refs_from_prompt_block(text: str) -> set[str]:
    """Extract tool-like identifiers referenced in prompt text (e.g. 'Use tool_name')."""
    patterns = [
        r'\bUse\s+([a-z][a-z_]{3,})\b',
        r'\(([a-z][a-z_]{3,})\)',
        r'"name":\s*"([a-z][a-z_]{3,})"',
    ]
    found = set()
    noise = {
        "type", "object", "string", "integer", "number", "boolean",
        "array", "items", "enum", "null", "true", "false",
        "alta", "media", "baixa", "high", "medium", "auto",
        "call_tool", "respond", "tool_name", "tool_args",
        "ferramenta", "ferramentas", "forma", "dados",
        "nome", "nenhuma", "apenas", "sempre", "nunca", "voce",
        "analise", "cada", "opcao", "obvia",
        "para", "sobre", "quando", "antes",
        "suposicoes", "reais", "status",
        "deve", "caso", "como", "suas", "seus",
        "peca", "liste", "ask_clarification",
    }
    for pattern in patterns:
        for m in re.findall(pattern, text):
            if m not in noise and "_" in m:
                found.add(m)
    return found


STUB_TOOLS = [
    "update_candidate_field",
    "favorite_candidate",
    "send_screening_invite", "share_candidate_profile",
    "send_candidate_report", "send_progress_report",
    "reschedule_interview", "cancel_interview",
    "send_interview_reminder", "list_today_interviews",
    "generate_self_scheduling_link", "create_generic_event",
    "reopen_job", "duplicate_job", "set_job_urgent",
    "tag_candidates", "add_candidate",
    "generate_kpi_report", "job_health_check", "analyze_funnel",
    "generate_daily_briefing", "create_task", "create_note",
    "check_proactive_alerts", "create_automation",
]


class TestPipelinePromptParity:
    """Pipeline prompt must reference tools from pipeline_tool_registry + enhanced mixin."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/domains/cv_screening/agents/pipeline_system_prompt.py")
        self.sys_match = re.search(
            r'PIPELINE_SYSTEM_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert self.sys_match, "Could not find PIPELINE_SYSTEM_PROMPT"
        self.sys_prompt = self.sys_match.group(1)

        self.pipeline_tools = _scan_domain_tool_registry(
            os.path.join(BASE, "app", "domains", "cv_screening", "agents", "pipeline_tool_registry.py")
        )
        self.enhanced_tools = _get_enhanced_mixin_tools()
        self.allowed_tools = self.pipeline_tools | self.enhanced_tools

    def test_no_stub_tools_in_pipeline_prompt(self):
        for stub in STUB_TOOLS:
            assert stub not in self.sys_prompt, (
                f"Pipeline prompt still references stub tool: {stub}"
            )

    def test_system_prompt_tools_match_registry(self):
        refs = _extract_tool_refs_from_prompt_block(self.sys_prompt)
        unknown = refs - self.allowed_tools
        assert not unknown, (
            f"Pipeline system prompt references tools not in pipeline_tool_registry "
            f"or enhanced mixin: {unknown}"
        )

    def test_reasoning_tools_match_registry(self):
        reasoning_match = re.search(
            r'PIPELINE_REASONING_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert reasoning_match, "Could not find PIPELINE_REASONING_PROMPT"
        refs = _extract_tool_refs_from_prompt_block(reasoning_match.group(1))
        unknown = refs - self.allowed_tools
        assert not unknown, (
            f"Pipeline reasoning references tools not in pipeline_tool_registry "
            f"or enhanced mixin: {unknown}"
        )

    def test_uses_pipeline_registry_names_not_permission_names(self):
        assert "move_candidate" in self.sys_prompt
        assert "batch_move" in self.sys_prompt
        assert "run_wsi_screening" in self.sys_prompt
        assert "update_candidate_stage" not in self.sys_prompt
        assert "bulk_update_candidates_stage" not in self.sys_prompt

    def test_has_confirmation_and_failure_handling(self):
        assert "CONFIRMACAO" in self.sys_prompt or "confirmação" in self.sys_prompt.lower()
        assert "FALHA" in self.sys_prompt or "falha" in self.sys_prompt.lower() or "NUNCA invente" in self.sys_prompt


class TestSourcingPromptParity:
    """Sourcing prompt must reference tools from sourcing_tool_registry + enhanced mixin."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/domains/sourcing/agents/sourcing_system_prompt.py")
        self.sourcing_tools = _scan_domain_tool_registry(
            os.path.join(BASE, "app", "domains", "sourcing", "agents", "sourcing_tool_registry.py")
        )
        self.enhanced_tools = _get_enhanced_mixin_tools()
        self.allowed_tools = self.sourcing_tools | self.enhanced_tools

    def test_pearch_uses_correct_tool_name(self):
        assert "include_pearch" in self.prompt, (
            "Sourcing prompt should reference Pearch via search_candidates with include_pearch param"
        )

    def test_pearch_not_as_separate_tool(self):
        few_shot_match = re.search(
            r'SOURCING_FEW_SHOT_EXAMPLES\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        if few_shot_match:
            few_shot = few_shot_match.group(1)
            tool_calls = re.findall(r'"name":\s*"([^"]+)"', few_shot)
            assert "search_candidates_pearch" not in tool_calls, (
                "Few-shot should use search_candidates with include_pearch, "
                "not separate search_candidates_pearch tool"
            )

    def test_pearch_marked_conditional(self):
        assert "CONDICIONAL" in self.prompt or "condicional" in self.prompt

    def test_no_false_190m_claim(self):
        assert "190M+" not in self.prompt

    def test_has_data_disclaimer(self):
        assert "benchmark" in self.prompt.lower() and (
            "tempo real" in self.prompt.lower() or "DISCLAIMER" in self.prompt
        )

    def test_reasoning_tools_match_sourcing_registry(self):
        reasoning_match = re.search(
            r'SOURCING_REASONING_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert reasoning_match, "Could not find SOURCING_REASONING_PROMPT"
        refs = _extract_tool_refs_from_prompt_block(reasoning_match.group(1))
        yaml_registry = _load_tool_registry_names()
        allowed = self.allowed_tools | yaml_registry
        unknown = refs - allowed
        assert not unknown, (
            f"Sourcing reasoning references tools not in sourcing_tool_registry, "
            f"enhanced mixin, or YAML registry: {unknown}"
        )

    def test_has_failure_handling_in_reasoning(self):
        reasoning_match = re.search(
            r'SOURCING_REASONING_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert reasoning_match
        reasoning = reasoning_match.group(1)
        assert "erro" in reasoning.lower() or "alternativa" in reasoning.lower()


class TestKanbanPromptParity:
    """Kanban assistant prompt is used by KanbanAssistantService (not a ReAct agent).
    Tool names serve as informational context and should match IN_JOB scope
    (ActionExecutor handles actual tool execution)."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py")
        self.sys_match = re.search(
            r'LIA_SYSTEM_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert self.sys_match, "Could not find LIA_SYSTEM_PROMPT"
        self.sys_prompt = self.sys_match.group(1)

        self.in_job_tools = _load_scope_tools("in_job")
        self.registry_tools = _load_tool_registry_names()
        self.allowed_tools = self.in_job_tools | self.registry_tools

    def test_no_stub_tools_in_system_prompt(self):
        for stub in STUB_TOOLS:
            assert stub not in self.sys_prompt, (
                f"Kanban system prompt still references stub tool: {stub}"
            )

    def test_tool_refs_exist_in_in_job_scope(self):
        refs = _extract_tool_refs_from_prompt_block(self.sys_prompt)
        unknown = refs - self.allowed_tools
        assert not unknown, (
            f"Kanban prompt references tools not in IN_JOB scope or global registry: {unknown}"
        )

    def test_has_confirmation_instructions(self):
        assert "confirmacao" in self.sys_prompt.lower() or "confirmação" in self.sys_prompt.lower()

    def test_has_tool_failure_handling(self):
        assert "FALHA" in self.sys_prompt or "falha" in self.sys_prompt.lower() or "NUNCA invente" in self.sys_prompt


class TestTalentPromptParity:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py")
        self.sys_match = re.search(
            r'TALENT_SYSTEM_PROMPT\s*=\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert self.sys_match, "Could not find TALENT_SYSTEM_PROMPT"
        self.sys_prompt = self.sys_match.group(1)

    def test_no_unqualified_real_time_market_claims(self):
        assert "Global Market Trends" not in self.sys_prompt
        occurrences = [
            i for i in range(len(self.sys_prompt))
            if self.sys_prompt[i:].startswith("dados de mercado em tempo real")
        ]
        for pos in occurrences:
            context = self.sys_prompt[max(0, pos - 50):pos + 60]
            assert "NAO" in context or "NUNCA" in context or "nao" in context.lower(), (
                f"Found unqualified 'dados de mercado em tempo real' claim at: ...{context}..."
            )

    def test_has_data_disclaimer(self):
        assert "DISCLAIMER" in self.sys_prompt or "benchmark" in self.sys_prompt.lower()

    def test_has_scope_limits(self):
        assert "ESCOPO" in self.sys_prompt or "TALENT_FUNNEL" in self.sys_prompt

    def test_market_insights_template_qualified(self):
        mi_match = re.search(
            r'"market_insights":\s*"""(.*?)"""',
            self.prompt,
            re.DOTALL,
        )
        assert mi_match, "Could not find market_insights template"
        assert "NAO" in mi_match.group(1)

    def test_has_tool_failure_handling(self):
        assert "FALHA" in self.sys_prompt or "NUNCA invente" in self.sys_prompt


class TestJobWizardPromptParity:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/shared/prompts/job_wizard.py")

    def test_salary_analysis_qualified(self):
        assert "benchmarks estimados" in self.prompt or "histórico interno" in self.prompt
        assert "tempo real" in self.prompt.lower()


class TestScopeDescriptionsParity:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _read_prompt_file("app/tools/scope_config.py")

    def test_talent_funnel_tools_in_description(self):
        assert "search_candidates" in self.prompt
        assert "get_candidate_details" in self.prompt
        assert "compare_candidates" in self.prompt

    def test_in_job_tools_in_description(self):
        assert "update_candidate_stage" in self.prompt
        assert "schedule_interview" in self.prompt
        assert "get_vacancy_funnel" in self.prompt

    def test_confirmation_documented(self):
        assert "confirmação" in self.prompt.lower() or "confirma" in self.prompt.lower()

    def test_market_data_disclaimer_in_restrictions(self):
        assert "benchmark" in self.prompt.lower()


class TestCrossFileConsistency:
    def test_all_registry_tool_names_are_valid(self):
        names = _load_tool_registry_names()
        assert len(names) > 20, "Expected at least 20 tools in registry"
        for name in names:
            assert re.match(r'^[a-z_]+$', name), f"Tool name {name} doesn't match pattern"

    def test_permissions_tools_exist_somewhere(self):
        registry = _load_tool_registry_names()
        all_dynamic = set()
        app_dir = os.path.join(BASE, "app")
        for dirpath, _, filenames in os.walk(app_dir):
            for fname in filenames:
                if fname.endswith(".py"):
                    all_dynamic |= _scan_tool_names_in_file(
                        os.path.join(dirpath, fname)
                    )
        all_known = registry | all_dynamic
        for scope in ["talent_funnel", "job_table", "in_job", "global"]:
            scope_tools = _load_scope_tools(scope)
            unknown = scope_tools - all_known
            assert not unknown, (
                f"Scope '{scope}' has tools not in YAML registry or any Python registrations: {unknown}"
            )
