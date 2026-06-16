# Path A Execution Log — Audit Trail

## SESSAO COMPLETA — ESTADO FINAL (2026-04-12)

### Infraestrutura (global)
- ChatAdapter: chat.py -> MainOrchestrator (REST) — ATIVO
- FairnessGuard: ativo em REST + WebSocket
- SecurityPatterns: ativo em REST + WebSocket
- PromptInjectionGuard: corrigido (is_blocked property) — era fail-open
- TenantContext: propagando para todos os agents via to_orchestrator_context()

### Inteligencia (global)
- SystemPromptBuilder: 17 agents com persona rica (287 linhas lia_persona.yaml)
- Domain-specific instructions: extraidas sem duplicacao (DOMAIN_INSTRUCTIONS class attr)
- ReAct instructions: centralizadas no builder (injetadas para agent_type != orchestrator)
- Token budget: ~5,100 tokens por agent (2.6% budget Sonnet 200K)

### Custo
- 5 agents migrados para Haiku (kanban, policy, automation, communication, ats_integration)
- Economia estimada: 73% por chamada nesses agents
- Tenant config sobrescreve quando existe (LLM Factory respeitado)

### Actions
- handle_action_flow removido (calls em send_message e WS)
- Phase 0+1 (ActionExecutor) cobre 46/46 actions — zero gaps

### LLM Factory compliance
- 6/22 chamadas unmanaged CORRIGIDAS (WSI question_generator -> safe_invoke)
- 8 calls Tipo B (LangChain chain pattern) — marcados TODO(Item3-B)
- 8 calls Tipo C (Gemini native generate_content) — marcados TODO(Item3-C)
- 1 arquivo duplicado deletado (vacancy_search_service.py)

---

## COMMITS DA SESSAO

### Path A Migration
- a1ce3a752: Passo 0 — TenantContext fix (tenant_context_snippet propagation)
- 4d030a846: Passo 1 — ChatAdapter + skip_memory_persist flag
- 81396f56c: Passo 2A — Reconectar chat.py via adapter
- cbf23f7ed: Passo 2B — Desabilitar handle_action_flow (early return)
- c91bd09c5: Fix PromptInjectionGuard is_blocked property

### M2 Memory Migration (tentativa + revert)
- Passo 3 Items 1-4 aplicados e testados
- SQL migration: 243 human->user, 239 ai->assistant (MANTIDO)
- ChatRepository roles atualizados: user/assistant (MANTIDO)
- skip_memory_persist REVERTIDO para True (session sharing blocker)

### SystemPromptBuilder
- 18e94da13: Separar talent prompt + ReAct no builder
- 5de300b20: PoC talent via SystemPromptBuilder
- 889d38a63: Extrair DOMAIN_SPECIFIC de 10 agents (batch)
- c13c7d20b: Mover para base class — 17 agents com persona
- Fix imports para 11 agents

### 5 Items Pendentes
- Item 1: Agent model config (Haiku) confirmado correto
- Item 2: handle_action_flow calls removidos
- Item 3: 6 WSI calls fixados + 16 marcados tech debt
- Item 4: WS inline FairnessGuard + SecurityPatterns
- Item 5: M2 diagnosticado (commit timing, nao sessoes diferentes)

---

## BACKLOG

### Alta prioridade
- M2 memoria: pick one writer approach. Fix = nao chamar repo writes quando
  MainOrchestrator persiste. Blocker = commit timing entre sessions.
- Item 3 restante: 16 calls precisam de audited ChatModel wrapper (Tipo B)
  e Gemini generate wrapper (Tipo C)

### Media prioridade
- generate_with_cascade(): dead code para remover
- 4 dominios shell (agent_studio, digital_twin, campaign, talent_pool)
- ~20 tools declaradas em YAML sem handlers
- WebSocket: considerar WS adapter completo (atual = inline security only)

### Baixa prioridade
- ~50 diretorios stub vazios em domains/
- Sourcing sub-agents sem prompt especializado
- A/B testing de prompts persona vs legacy

---

## VERIFICACOES REALIZADAS

### Path A (5/5 testes)
1. Smoke test: servidor sobe com 1482 endpoints, 17 agents
2. Mensagem simples: MainOrchestrator nos logs, resposta OK
3. Dominio: intent search_candidates detectado
4. Garbage input: resposta contextual inteligente
5. Dual-write: zero duplicatas, roles corretos

### SystemPromptBuilder (3/3 testes)
1. talent: busca candidatos funciona, tools OK
2. wizard: criar vaga funciona, stages reconhecidos
3. analytics: tempo medio contratacao — resposta contextual

### Security
- PromptInjectionGuard: injection bloqueado (jailbreak, confidence=0.95)
- Mensagem normal: nao bloqueada (zero false positive)
