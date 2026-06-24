# Fase A — Supervisor (delegação hierárquica A2)
Plano canônico. Decisão CEO review 2026-06-04: A2 (supervisor + sub-agentes). Branch: feat/benefits-prv-canonical.
Auditoria: ~/Documents/wedotalent_audit_2026-06-04/chat_enterprise_integration_audit.md

## Objetivo
Um cérebro único no chat live. O supervisor (= o agentic_loop LIA-A04 existente, com toolset CURADO)
decide responder direto OU delegar a um domain sub-agent via tool de handoff. Mata o dual-path
Phase-1.5↔Phase-2 (Phase 2 vira delegação explícita, não fallback frágil).

## Mecânica confirmada no código (grounding)
- `agentic_loop.py::AgenticLoop.run()` = loop tool-calling padrão sobre `app.tools.registry.tool_registry`.
  Itera: LLM escolhe tool -> executa via exec_context (ToolExecutionContext company_id/user_id) -> realimenta.
- Tools registram via `tool_registry.register(ToolDefinition(name, description, parameters_schema, handler, allowed_agents))`.
- Delegação a domain agent (já usada na Phase 2 `workflow.py::_try_react_agent`):
    from app.shared.agents.agent_registry import AgentRegistry
    from app.api.v1.agent_chat_ws import _ensure_agents_loaded
    from lia_agents_core.agent_interface import AgentInput
    _ensure_agents_loaded(); agent = AgentRegistry().get_instance(agent_domain)
    out = await agent.process(AgentInput(message=task, context={...}, session_id, company_id, user_id))
    # AgentOutput: .message .state_updates .error .confidence .reasoning_steps .tool_results .metadata
- Agents registrados (boot): pipeline (PipelineReActAgent, alias cv_screening), sourcing, recruiter_copilot, etc.

## Design do supervisor
- Toolset CURADO (~30, não 300): ~20 tools GLOBAL de alta frequência + ~10 `delegate_to_<domínio>`.
  -> seleção confiável do LLM + custo/turno controlado.
- Cada `delegate_to_<domínio>(task, [hints])` = adapter fino que chama o domain agent via AgentRegistry.
- Domain sub-agents mantêm seu kit completo (~280 ToolDefinitions já existentes) — REUSO, não rebuild.
- UMA voz: sub-agente devolve dado estruturado; o supervisor compõe o texto final.
- view_context (P0.1, Fase B) repassado ao sub-agente no AgentInput.context.
- RLS (balde 1) já herdado do produtor (engine begin listener) — toda sessão de sub-agente nasce com o GUC.
- Governança no boundary: scope + permission + HITL por delegação (Fase C/D endurece).

## SLICE FINO (esta tarefa) — provar o padrão com 1 domínio
Domínio: `pipeline` (alto valor, agent registrado). UMA tool: `delegate_to_pipeline`.

Arquivo novo: `app/orchestrator/supervisor/handoff_tools.py`
  - `async def delegate_to_domain(agent_domain, task, *, company_id, user_id, session_id="", view_context=None) -> dict`
      adapter puro: _ensure_agents_loaded -> AgentRegistry().get_instance(agent_domain) ->
      AgentInput(message=task, context={view_context, source:"supervisor_handoff"}, ...) ->
      agent.process() -> return {success, message, data, confidence, reasoning_steps}.
      Fail-loud: agente não registrado -> {success:False, message:"<domínio> indisponível", unavailable:True}.
  - `@tool_handler("orchestrator")` wrapper `_wrap_delegate_to_pipeline(**kwargs)`:
      company_id=kwargs["company_id"] (do ContextVar), user_id, task=kwargs["task"], view_context=kwargs.get("view_context").
  - `register_handoff_tools()`: tool_registry.register(ToolDefinition(
      name="delegate_to_pipeline", description="Delega ao agente de pipeline (mover candidato, etapas, funil...).",
      parameters_schema={type:object, properties:{task:{type:string}, view_context:{type:object}}, required:[task]},
      handler=_wrap_delegate_to_pipeline, allowed_agents=["orchestrator"])).

Wiring: chamar register_handoff_tools() onde os tools globais são registrados no startup (tool loader).

## TDD (red->green->refactor)
RED `tests/orchestrator/test_supervisor_handoff.py`:
  1. test_delegate_to_domain_calls_agent_process: mock AgentRegistry.get_instance -> fake agent cujo
     process() retorna AgentOutput(message="ok", state_updates={...}); assert delegate_to_domain devolve
     {success:True, message:"ok", data:{...}} e que process foi chamado com AgentInput certo (task, company_id).
  2. test_delegate_unregistered_domain_fail_loud: get_instance -> None; assert {success:False, unavailable:True}.
  3. test_register_handoff_tools_registers_delegate_to_pipeline: após register_handoff_tools(),
     tool_registry.get_tool("delegate_to_pipeline") existe, allowed_agents inclui "orchestrator",
     parameters_schema exige "task".
  (Determinístico: mock AgentRegistry; sem DB/loop/event-loop — evita poluição de pool.)

## GUIDE + SENSOR (harness)
- GUIDE (CLAUDE.md): supervisor é o cérebro único; toolset curado; handoff por domínio; proibido loop flat 300 / novo fallback.
- SENSOR `scripts/check_chat_tool_federation.py`: toda tool chat_exposed alcançável pelo supervisor
  (global OU via delegate_to_<domínio>); órfã=erro; sinaliza dual-path p/ remoção. Warn->blocking.

## Depois do slice (Fase A completa)
- Curar os ~20 globais de alta frequência (quais ficam diretos no supervisor).
- Criar os ~9 delegate_to_<domínio> restantes (sourcing, talent, comms, offers, settings, analytics, autonomous, ats, job).
- Religar recruiter_copilot/P0.1/P0.2 ao caminho do supervisor.
- Aposentar o fallback Phase-2 (vira delegação explícita).
