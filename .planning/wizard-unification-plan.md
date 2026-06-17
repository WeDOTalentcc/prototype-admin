# Plano de Unificação do Wizard de Criação de Vaga

> Origem: auditoria 2026-05-29. Paulo reportou DUAS experiências divergentes ao
> criar vaga: (A) conversacional (IA pede cargo/senioridade/modelo, sugere salário,
> pergunta se quer wizard) e (B) pula direto pro "Enriquecimento do JD".
> Decisão de produto: **canônico = conversacional → wizard**. Objetivo: **unificar
> os dois wizards** num único caminho.

## Diagnóstico (root cause)

Existem 3+ implementações de "criação de vaga" e o roteamento entre elas era
não-determinístico:

| Implementação | Arquivo | Status |
|---|---|---|
| **JobCreationGraph** (LangGraph 8 estágios) | `app/domains/job_creation/graph.py` + `WizardSessionService` | ✅ CANÔNICO |
| WizardReActAgent (ReAct) | `app/domains/job_management/agents/wizard_react_agent.py` | fallback WS + background Celery |
| JobWizardGraph | `app/domains/job_management/agents/job_wizard_graph.py` | LEGACY (CANONICAL-EXEMPT, já aposentado) |
| JobsManagementReActAgent (conversacional) | `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | era a "Experiência A" |

Entry point: `agent_chat_ws.py` → `CascadedRouter` (8 tiers) → domínio `wizard`
(→ WizardSessionService → LangGraph) ou domínio `job_management` (→ ReAct conversacional).

## Frente 1 — Roteamento determinístico ✅ DONE (commit b801649b1)

Descoberta: `domain_routing.yaml` estava MORTO (bug de path em `_load_domain_patterns`:
procurava em `routing/config/` em vez de `config/`). Produção rodava 100% no
`_HARDCODED_DOMAIN_PATTERNS`, degradando 3 domínios (company_settings +18p,
job_management +10p de listagem, wizard +1p).

Fixes aplicados:
- Path do YAML corrigido (`.parent.parent / "config"`).
- Patterns de criação no wizard (YAML + hardcoded defense-in-depth):
  criar/abrir/cadastrar/registrar vaga, nova vaga/oportunidade, criar/abrir posição,
  (preciso|quero|vou|gostaria) contratar.
- Wizard creation short-circuit em `FastRouter.match()` (criação é determinística,
  imune à penalidade de ambiguidade que flipava "nova vaga" → job_management).
- Sensor `tests/unit/orchestrator/test_domain_routing_yaml_loads.py` (falha alto se
  YAML voltar a não carregar).
- `tests/unit/orchestrator/test_job_creation_routing_canonical.py` (24 casos).

## Frente 2 — Intake conversacional (PRÓXIMA, a maior)

Objetivo: o `intake_node` do grafo canônico deixa de ser "magro" (extrai num passo
e pula pro jd_enrichment) e vira CONVERSACIONAL: coleta cargo/senioridade/modelo,
sugere faixa salarial, pede permissão, e SÓ ENTÃO avança pro jd_enrichment.

### Design

1. **Novo `intake_gate_node`** em `app/domains/job_creation/nodes/intake_gate.py`,
   espelhando o padrão de `nodes/jd_gate.py` (langgraph.types.interrupt() + resume
   via Command(resume=...) no WizardSessionService). ATENÇÃO: jd_gate tem 8+ "fix #N
   code review" — semântica sutil (turno fresco vs initial-pass, post-reject,
   gate_seen_user_query para evitar loop de classificação). Espelhar com cuidado.

2. **Lógica do intake_gate** (2 sub-estados):
   - Se faltam campos obrigatórios (parsed_title/parsed_seniority/parsed_model) →
     interrupt() perguntando conversacionalmente. No resume, merge da resposta
     (re-rodar IntakeExtractor sobre o texto novo) e re-checar.
   - Se campos presentes mas salário ainda não sugerido/confirmado → chamar
     `MarketBenchmarkService`/`salary_benchmark_service` (já usado por `nodes/salary.py`),
     sugerir faixa no chat, interrupt() pedindo permissão ("Posso seguir criando a vaga?").
   - Se confirmado → rotear pra jd_enrichment.

3. **Edges** (em `graph.py`, `_build_graph`):
   - Trocar `builder.add_edge("intake", "jd_enrichment")` por
     `builder.add_edge("intake", "intake_gate")` +
     `builder.add_conditional_edges("intake_gate", route_after_intake_gate,
       {"jd_enrichment": "jd_enrichment", "intake_gate": "intake_gate", "end": END})`.
   - `route_after_intake_gate` em `graph.py` (espelhar `route_after_gate`).

4. **Novos campos de state** (`state.py`):
   - `intake_approved: Optional[bool]` (permissão pra prosseguir)
   - `intake_salary_suggested: Optional[bool]` (evita re-sugerir)
   - reusar `gate_seen_user_query`/`gate_resume_message` ou criar
     `intake_gate_seen_user_query` análogos (decidir: campos próprios evitam
     colisão com o jd_gate que usa os mesmos).

5. **i18n** (`helpers/i18n.py`): mensagens conversacionais
   `intake_gate.ask_fields`, `intake_gate.salary_suggestion`, `intake_gate.ask_permission`.

6. **Portar a lógica conversacional do `JobsManagementReActAgent`** (sugestão de
   salário + tom) PARA o intake_gate — uma fonte da verdade (canonical-fix princípio 2).

### TDD (lia-testing)
- Red: teste que envia "quero criar uma vaga" SEM cargo → espera que o grafo
  INTERROMPA em intake_gate (não avance pra jd_enrichment) e emita pergunta de cargo.
- Red: com cargo+senioridade → espera sugestão de salário + pedido de permissão.
- Red: após permissão → avança pra jd_enrichment.
- Usar o checkpointer/resume pattern dos testes E2E existentes do wizard.

## Frente 3 — Remover caminho ReAct duplicado do hot path

- `agent_chat_ws.py:1161` — o fallback que cai em `WizardReActAgent` quando
  `WizardSessionService` crasha é "fallback silencioso" (mascara crash, dá UX
  divergente). Trocar por falha ALTA explícita (erro pro usuário), não fallback
  pra agente diferente.
- `WizardReActAgent` permanece SÓ para background tasks (`jobs/tasks/agents.py`).
- A lógica conversacional do `JobsManagementReActAgent` migra pro intake_gate (Frente 2);
  `job_management` domain fica só pra GESTÃO de vaga existente.

## Frente 4 — Mismatch de domain id

- Roteador emite `job_management`; agente registra como `jobs_management`
  (`@register_agent("jobs_management", aliases=['jobs_mgmt'])`). Verificar se
  `AgentRegistry.get_or_fallback("job_management")` resolve ou cai no fallback "talent".
- Alinhar: adicionar alias `job_management` ao registro OU normalizar o domain id.
- Adicionar teste pinando que `_get_agent("job_management")` resolve o agente certo.

## Follow-ups separados (descobertos no caminho, fora de escopo)

- 🟡 `"ranking de vagas"` → `sourcing` (não job_management): sourcing tem pattern
  genérico `ranking\s+d[eo]` que colide via penalty-flip. Pré-existente. Refinar o
  pattern do sourcing (`ranking\s+d[eo]\s+candidato`) num fix separado.
- 🟡 15 testes pré-existentes falhando em `tests/unit/orchestrator/` (fallback_react,
  capability_gate, DI, ui_action_schema) — NÃO relacionados a roteamento, mas vale
  triar.
- 🟢 `job_wizard_graph.py` (JobWizardGraph) LEGACY — task de cleanup separada
  (remover dos call-sites: health_langgraph, crew_examples, agents_registry.yaml).

## Bugs do chat wizard (sessão anterior, à parte desta unificação)

- Bug 5 (JSON bruto no chat) — FIXADO em `plataforma-lia/.../UnifiedChat.tsx`
  (helper `wizardUpdateToMessage`), ainda NÃO commitado.
- Bug 3 (onUpdate ausente no ReviewPanel) — já estava fixado em commit cf8ddb740.
- Bug 1 (histórico preservado), Bug 2 (edit/regenerate WSI infinito), Bug 4 (chat
  reset) — pendentes, ver transcript da sessão anterior.
