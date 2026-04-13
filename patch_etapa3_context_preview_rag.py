#!/usr/bin/env python3
"""
Etapa 3: context_level + Prompt Preview + RAG Smoke

Patches:
  3.1 custom_agent_runtime.py — _get_system_prompt() respects context_level
  3.2 custom_agents.py — GET /preview-prompt endpoint
  3.3 custom_agent.py (schema) — add context_level to Create/Update/Response
  3.4 RAG smoke test (validation only, no code change)
"""
import os
import sys

BASE = "/home/runner/workspace/lia-agent-system"
results = []


def read_file(path):
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    with open(full) as f:
        return f.read()


def write_file(path, content):
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    with open(full, "w") as f:
        f.write(content)


def patch(path, old, new, label=""):
    full = os.path.join(BASE, path) if not path.startswith("/") else path
    content = read_file(full)
    if old not in content:
        print(f"  ERROR: pattern not found — {label}")
        results.append(False)
        return False
    content = content.replace(old, new, 1)
    write_file(full, content)
    print(f"  OK: {label}")
    results.append(True)
    return True


# ============================================================
# 3.1a: Add context_level param to CustomAgentRuntime.__init__
# ============================================================
print("\n=== 3.1a: context_level in __init__ ===")
patch(
    "app/domains/agent_studio/custom_agent_runtime.py",
    """        excluded_tools: list[str] | None = None,
    ) -> None:
        super().__init__()
        self._agent_id = agent_id""",
    """        excluded_tools: list[str] | None = None,
        context_level: str = "full",
    ) -> None:
        super().__init__()
        self._agent_id = agent_id""",
    "context_level in __init__ params",
)

patch(
    "app/domains/agent_studio/custom_agent_runtime.py",
    """        self._excluded_tools = set(excluded_tools or [])""",
    """        self._excluded_tools = set(excluded_tools or [])
        self._context_level = context_level if context_level in ("full", "standard", "minimal") else "full\"""",
    "store _context_level",
)


# ============================================================
# 3.1b: _get_system_prompt() respects context_level
# ============================================================
print("\n=== 3.1b: _get_system_prompt() context_level logic ===")
patch(
    "app/domains/agent_studio/custom_agent_runtime.py",
    """    def _get_system_prompt(self, input: AgentInput) -> str:
        \"\"\"Compose system prompt: LIA persona base + domain + tenant + user + custom instructions.

        The client's custom prompt is injected as extra_instructions, NOT replacing the persona.
        \"\"\"
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

        ctx = input.context or {}

        # Map domain to agent_type for SystemPromptBuilder
        agent_type = self._domain if self._domain != "custom" else "general"
        if ":" in agent_type:
            agent_type = agent_type.split(":")[0]  # "custom:MyAgent" -> "custom"
        # Map known domain values to builder agent_types
        domain_map = {
            "sourcing": "sourcing",
            "screening": "cv_screening",
            "pipeline": "pipeline",
            "analytics": "analytics",
            "communication": "communication",
            "job_management": "job_planner",
            "general": "recruiter_assistant",
            "custom": "recruiter_assistant",
        }
        builder_agent_type = domain_map.get(agent_type, "recruiter_assistant")

        # Build base prompt with full LIA intelligence
        base = SystemPromptBuilder.build(
            agent_type=builder_agent_type,
            tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
            user_name=ctx.get("user_name", ""),
            user_role=ctx.get("user_role", ""),
            recruiter_context=ctx.get("recruiter_context", ""),
            conversation_summary=ctx.get("conversation_summary", ""),
            conversation_history=ctx.get("conversation_history"),
            context_page=ctx.get("context_page", "general"),
            extra_instructions=f"INSTRUCOES ADICIONAIS DO OPERADOR:\\n{self._system_prompt_template}",
        )

        # GAP 6: Inject domain-specific few-shot examples + reasoning
        domain_instructions = self._load_domain_instructions()
        if domain_instructions:
            return f"{base}\\n\\n---\\n\\n{domain_instructions}"
        return base""",
    """    def _get_system_prompt(self, input: AgentInput) -> str:
        \"\"\"Compose system prompt respecting context_level:

        - full: persona + domain + tenant + user + history + few-shot + custom (default)
        - standard: persona + tenant + user + custom (no history, no few-shot)
        - minimal: persona + custom instructions only
        \"\"\"
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

        ctx = input.context or {}

        # Map domain to agent_type for SystemPromptBuilder
        agent_type = self._domain if self._domain != "custom" else "general"
        if ":" in agent_type:
            agent_type = agent_type.split(":")[0]
        domain_map = {
            "sourcing": "sourcing",
            "screening": "cv_screening",
            "pipeline": "pipeline",
            "analytics": "analytics",
            "communication": "communication",
            "job_management": "job_planner",
            "general": "recruiter_assistant",
            "custom": "recruiter_assistant",
        }
        builder_agent_type = domain_map.get(agent_type, "recruiter_assistant")

        # === context_level routing ===
        if self._context_level == "minimal":
            # Minimal: persona base + custom instructions only
            base = SystemPromptBuilder.build(
                agent_type=builder_agent_type,
                extra_instructions=f"INSTRUCOES ADICIONAIS DO OPERADOR:\\n{self._system_prompt_template}",
            )
            return base

        if self._context_level == "standard":
            # Standard: persona + tenant + user + custom (no history, no few-shot)
            base = SystemPromptBuilder.build(
                agent_type=builder_agent_type,
                tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
                user_name=ctx.get("user_name", ""),
                user_role=ctx.get("user_role", ""),
                context_page=ctx.get("context_page", "general"),
                extra_instructions=f"INSTRUCOES ADICIONAIS DO OPERADOR:\\n{self._system_prompt_template}",
            )
            return base

        # Full: everything (default — same as before)
        base = SystemPromptBuilder.build(
            agent_type=builder_agent_type,
            tenant_context_snippet=ctx.get("tenant_context_snippet", ""),
            user_name=ctx.get("user_name", ""),
            user_role=ctx.get("user_role", ""),
            recruiter_context=ctx.get("recruiter_context", ""),
            conversation_summary=ctx.get("conversation_summary", ""),
            conversation_history=ctx.get("conversation_history"),
            context_page=ctx.get("context_page", "general"),
            extra_instructions=f"INSTRUCOES ADICIONAIS DO OPERADOR:\\n{self._system_prompt_template}",
        )

        # Inject domain-specific few-shot examples + reasoning
        domain_instructions = self._load_domain_instructions()
        if domain_instructions:
            return f"{base}\\n\\n---\\n\\n{domain_instructions}"
        return base""",
    "context_level routing in _get_system_prompt",
)


# ============================================================
# 3.1c: Pass context_level through get_or_create_runtime
# ============================================================
print("\n=== 3.1c: context_level in get_or_create_runtime ===")
patch(
    "app/domains/agent_studio/custom_agent_runtime.py",
    """    force_new: bool = False,
    enable_memory: bool = True,
    excluded_tools: list[str] | None = None,
) -> CustomAgentRuntime:""",
    """    force_new: bool = False,
    enable_memory: bool = True,
    excluded_tools: list[str] | None = None,
    context_level: str = "full",
) -> CustomAgentRuntime:""",
    "context_level in get_or_create_runtime params",
)

patch(
    "app/domains/agent_studio/custom_agent_runtime.py",
    """            enable_memory=enable_memory,
            excluded_tools=excluded_tools,
            company_id=company_id,
        )""",
    """            enable_memory=enable_memory,
            excluded_tools=excluded_tools,
            context_level=context_level,
            company_id=company_id,
        )""",
    "pass context_level to constructor",
)


# ============================================================
# 3.1d: custom_agents.py — pass context_level from DB model
# ============================================================
print("\n=== 3.1d: custom_agents.py passes context_level ===")
# In test endpoint
patch(
    "app/api/v1/custom_agents.py",
    """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),""",
    """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
            context_level=getattr(agent, "context_level", "full"),""",
    "context_level in test endpoint",
)
# In execute endpoint (second occurrence)
patch(
    "app/api/v1/custom_agents.py",
    """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),""",
    """            enable_memory=getattr(agent, "enable_memory", True),
            excluded_tools=getattr(agent, "excluded_tools", None),
            context_level=getattr(agent, "context_level", "full"),""",
    "context_level in execute endpoint",
)


# ============================================================
# 3.2: Schema — add context_level to Create/Update/Response
# ============================================================
print("\n=== 3.2: Schema updates ===")
# CreateCustomAgentRequest
patch(
    "app/schemas/custom_agent.py",
    """    model_override: Optional[str] = None


class UpdateCustomAgentRequest(BaseModel):""",
    """    model_override: Optional[str] = None
    enable_memory: bool = True
    context_level: str = Field(default="full", pattern="^(full|standard|minimal)$")
    excluded_tools: list[str] = Field(default_factory=list)


class UpdateCustomAgentRequest(BaseModel):""",
    "context_level in CreateRequest",
)

# UpdateCustomAgentRequest
patch(
    "app/schemas/custom_agent.py",
    """    model_override: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")""",
    """    model_override: Optional[str] = None
    enable_memory: Optional[bool] = None
    context_level: Optional[str] = Field(None, pattern="^(full|standard|minimal)$")
    excluded_tools: Optional[list[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")""",
    "context_level in UpdateRequest",
)

# CustomAgentResponse
patch(
    "app/schemas/custom_agent.py",
    """    model_override: Optional[str] = None
    total_executions: int = 0""",
    """    model_override: Optional[str] = None
    enable_memory: bool = True
    context_level: str = "full"
    excluded_tools: list[str] = []
    total_executions: int = 0""",
    "context_level in Response",
)


# ============================================================
# 3.3: Prompt Preview endpoint
# ============================================================
print("\n=== 3.3: Prompt Preview endpoint ===")
# Append to custom_agents.py
custom_agents_path = os.path.join(BASE, "app/api/v1/custom_agents.py")
ca_content = read_file(custom_agents_path)

preview_endpoint = '''

@router.get("/{agent_id}/preview-prompt")
async def preview_agent_prompt(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview the composed system prompt for a custom agent.

    Returns the first 80 lines of the fully-composed prompt so the creator
    can inspect what the LLM actually sees.  Only the agent creator (same
    company) may preview.
    """
    agent = await agent_marketplace_service.get_agent(
        db=db, agent_id=agent_id, company_id=current_user.company_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime
    from lia_agents_core.agent_interface import AgentInput

    runtime = get_or_create_runtime(
        agent_id=str(agent.id),
        agent_name=agent.name,
        system_prompt=agent.system_prompt,
        allowed_tools=agent.allowed_tools or [],
        domain=agent.domain or "general",
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        model_override=agent.model_override,
        enable_memory=getattr(agent, "enable_memory", True),
        excluded_tools=getattr(agent, "excluded_tools", None),
        context_level=getattr(agent, "context_level", "full"),
        company_id=current_user.company_id,
    )

    dummy_input = AgentInput(
        message="(preview)",
        user_id=str(current_user.id),
        company_id=current_user.company_id,
        session_id="preview",
        context={},
    )
    full_prompt = runtime._get_system_prompt(dummy_input)
    lines = full_prompt.split("\\n")
    preview_lines = lines[:80]

    return {
        "agent_id": agent_id,
        "context_level": getattr(agent, "context_level", "full"),
        "total_lines": len(lines),
        "preview_lines": 80,
        "prompt_preview": "\\n".join(preview_lines),
    }
'''

if "preview-prompt" not in ca_content:
    ca_content += preview_endpoint
    write_file(custom_agents_path, ca_content)
    print("  OK: preview-prompt endpoint added")
    results.append(True)
else:
    print("  SKIP: preview-prompt endpoint already exists")
    results.append(True)


# ============================================================
# Verify all patched files
# ============================================================
import ast
print("\n=== Verify AST ===")
for f in [
    "app/domains/agent_studio/custom_agent_runtime.py",
    "app/api/v1/custom_agents.py",
    "app/schemas/custom_agent.py",
]:
    try:
        ast.parse(read_file(f))
        print(f"  OK: {f}")
        results.append(True)
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")
        results.append(False)

total = len(results)
ok = sum(1 for r in results if r)
print(f"\n{'=' * 60}")
print(f"Results: {ok}/{total} patches applied successfully")
if ok < total:
    print("FAILED patches need manual review")
    sys.exit(1)
else:
    print("All Etapa 3 patches applied!")
    sys.exit(0)
