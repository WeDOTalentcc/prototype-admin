# LIA Chat — Build-spec de Paridade Federado×Supervisor + Gaps (handoff autocontido)
**Data:** 2026-06-06 · **Branch:** `feat/benefits-prv-canonical` · **Fonte única:** Replit `ssh replit-wedo-0405` → `/home/runner/workspace/`
**Origem:** auditoria de paridade (workflow escopado, 21 agentes, source-gated + verificação adversarial + ground-truth do orquestrador). Output bruto: `tasks/waz5afuc7.output` (303 linhas).

> Este doc é **autocontido**: regras + arquitetura + cada gap com `arquivo:linha` + fix canônico + teste. Pra retomar numa sessão nova sem contexto.

---

## 0. REGRAS INVIOLÁVEIS (ler primeiro)
1. **Replit é a única fonte da verdade.** Editar/ler SÓ em `/home/runner/workspace/{lia-agent-system,plataforma-lia,ats_api}`, branch `feat/benefits-prv-canonical`. GitHub fora do fluxo.
2. **NUNCA** `git push` / `gh` / remote. Commits ficam **locais no Replit**.
3. **TDD** (Red→Green). **Commit atômico com pathspec explícito** (REGRA 8): `git commit -m "..." -- <paths>`. Arquivo novo: `git add <path> && git commit -- <path>`. Nunca `git add .`/`-A`.
4. **`rg` corrompe tokens neste SSH** → usar `sed`/`cat -n`/`grep -n`.
5. **Editar** via `cat <<'PYEOF'` (heredoc quoted — sem backticks no conteúdo) ou python string-replace com asserts de anchor.
6. **WatchFiles** recarrega `app/` no write; `libs/` + **Secrets** exigem restart completo do servidor.
7. **coverage-FAIL** ao rodar um subset de teste (`Required test coverage of 10% not reached`) = **gate global**, NÃO falha do teste. Olhar a linha `N passed`.
8. **Lição de ouro:** ground-truth o **PRODUTOR INTEIRO** (classe-base + override + handoff), não grep parcial — errei status 2× nesta sessão por ler só o arquivo-folha. Toda evidência prova path `/home/runner/workspace/`.
9. CLAUDE.md cascata: canonical-fix (fix no produtor, 1 fonte da verdade), harness-engineering (guide+sensor), production-quality. Multi-tenancy `company_id` SEMPRE do JWT, nunca payload. LGPD.

---

## 1. ARQUITETURA — as 2 trilhas (ground-truth)
Chat unificado (bolha/lateral/full) = **1 transporte SSE**: `app/api/v1/agent_chat_sse.py` → `/chat/{session}/stream`.

Branch de trilha em `agent_chat_sse.py` (ordem):
1. **Wizard** (state machine pré-router, L417-509) — intercepta ANTES da trilha; sempre dá `return`. Trail-agnostic.
2. **Supervisor** (`LIA_BUBBLE_VIA_SUPERVISOR`=on, L511-512) → `_run_via_supervisor` (L595-624) → `MainOrchestrator.process` (`app/orchestrator/execution/main_orchestrator.py`, 3259L) → delega a **sub-agentes de domínio** (talent_funnel/kanban/jobs `app/domains/recruiter_assistant/agents/*_react_agent.py`). Serialização da saída: `_orchestrator_result_to_frames` (`app/api/v1/chat.py:892`).
3. **Federado** (`LIA_FEDERATED_PRIMARY`=on, L517-527) → `agent = _get_agent("recruiter_copilot")` (1 agente único, escopo dinâmico de tools).
4. **Default** (flags off — caminho LIVE hoje) → `agent = _get_agent(resolved_domain)` (agentes de domínio isolados via CascadedRouter).

Dispatch (L760-762): `agent_task = asyncio.create_task(_run_via_supervisor() if _bubble_via_supervisor else _run_agent())`.
Drain SSE (L795-846): ramo agente (`else: output=item["_output"]`, ~L820+) vs ramo supervisor (`elif _orch_result`, ~L806).

ReAct agents (federado + sub-agentes) estendem `libs/agents-core/lia_agents_core/langgraph_react_base.py` (`_get_system_prompt` → `SystemPromptBuilder.build`). MainOrchestrator NÃO é langgraph_base (orquestrador próprio).

**Chokepoint compartilhado de tool:** `@tool_handler` (`app/shared/tool_handler.py`) — AS DUAS trilhas executam a tool por ele (supervisor via `ToolExecutor.execute`→`tool.handler`; ReAct via tool node). É AQUI que fixes que valem pros dois devem ir.

---

## 2. MATRIZ DE PARIDADE VERIFICADA (✅ ok / 🟡 parcial / 🔴 gap)
| Dimensão | Federado | Supervisor |
|---|---|---|
| RRP / moat | ✅ (moat via `_GLOBAL_ESSENTIALS`) | 🟡 sub-agente DROPA blocks (legacy orch L304-310) |
| **HITL** | 🔴 gate inerte | 🔴 LLM-aberto sem gate |
| Wizard | 🟡 seam turno-1 | ✅ bootstrap turno-1 |
| **Streaming/reasoning** | 🟡 sem token; reasoning OFF | 🔴 callback dropado |
| Governança (C3B) | ✅ | ✅ |
| Memória + entity | ✅ | ✅ |
| Navegação [NAVIGATE] | ✅ | 🔴 vaza como texto |
| Panels | 🔴 dead code (mitigado) | ✅ |
| Persistência | ✅ | ✅ (com ressalva) |
| Multi-tenancy | ✅ | ✅ |
| def-assembly / stage-nav (só federado) | ✅ FIXADO / 🟡 stage-nav deferido | n/a |

---

## 3. GAPS COMPARTILHADOS — FAZER PRIMEIRO (valem pra qualquer decisão)

### 3.1 🔴 HITL (P0 SEGURANÇA) — 1a FEITO; falta 1b + 1c
**Problema:** ações sensíveis (close_job, send_email, bulk, reject_candidate) executam SEM gate de aprovação no caminho **LLM-aberto**, nas DUAS trilhas. `close_job` dá `db.commit()` (`app/domains/job_management/tools/job_tools.py:455`) ANTES do flag `requires_confirmation` (L472) → flag é pós-commit (vaga já fechou). Federado: gate `maybe_request_hitl_approval` existe (`recruiter_copilot_react_agent.py:315-324`) mas é INERTE (`app/shared/hitl/agent_gate.py:90` só dispara se `context['action_type']∈set`; nada server-side seta action_type; set incompleto). Supervisor: `agentic_loop.py:443` chama `ToolExecutor.execute(agent_type='orchestrator')` sem pré-flight; `workflow.py:712` monta context com `action_id` (≠ `action_type`) → gate passthrough. `ToolDefinition` (`app/tools/registry.py:16-32`) nem tinha campo HITL.

**Decisão:** gate CANÔNICO no chokepoint compartilhado `@tool_handler`. Reusar `PendingAction`/`approval_required` (não reinventar).

**✅ 1a FEITO** (commit `2746e42e7`, sem push, TDD 3/3, ATIVA NADA):
- `ToolDefinition.requires_confirmation: bool=False` (`registry.py`).
- `@tool_handler(..., requires_confirmation=False)` + gate pré-flight (depois do company_id fail-closed): se marcada E `not is_hitl_approved()` → BLOQUEIA, retorna `{"success":False,"needs_confirmation":True,"requires_user_input":True,"message":...,"hitl":{...}}`.
- `app/shared/hitl/hitl_approval_context.py`: ContextVar `_hitl_approved` + `set_hitl_approved/is_hitl_approved/reset_hitl_approved` — setada pelo TRANSPORTE qdo o USUÁRIO confirma, **nunca pela LLM**.
- Teste: `tests/unit/test_hitl_tool_gate.py`.

**⬜ 1b — fiação SSE (cross-stack, sutil) — FAZER:**
- (a) **Surfacing:** transformar `needs_confirmation` do result da tool em frame `approval_required` nos 2 ramos do drain SSE (agente ~L820+ e orch ~L806). O ramo agente já tem o caminho de `needs_confirmation`→`approval_required` via ChatResponse? Reusar `chat.py:947-955` (`if needs_confirmation: frame approval_required {pending_id}`).
- (b) **Detecção server-side da aprovação:** quando o usuário confirma (turno seguinte), o SSE deve `set_hitl_approved(True)` ANTES de re-rodar o agente. Reusar `PendingAction` (`app/orchestrator/execution/pending_action.py`, keyed por conversation_id, TTL 5min, 1 pending/conversation) + Phase 0 do orquestrador (`main_orchestrator.py:411`). Criar o PendingAction quando o gate bloqueia.
- (c) **Re-execução DIFERE por trilha** (atenção): supervisor Phase 0 replaya a ação pendente; federado a LLM re-chama a tool (com `_hitl_approved` setado). Tratar os dois.
- Ideal: botão "aprovar/recusar" no FE (`plataforma-lia`) lendo o frame `approval_required` (pending_id) e mandando aprovação explícita (server-authoritative). Hoje o FE lê `r.action_type` da RESPOSTA, não manda aprovação no input — precisa adicionar.
- Sensor: contract test SSE — tool sensível sem aprovação → frame `approval_required` + tool NÃO executou; com aprovação → executou.

**⬜ 1c — ativar (SÓ após 1b, senão trava as tools):**
- Marcar `requires_confirmation=True` nas tools: `close_job`, `delete_vacancy`, `publish_vacancy`/`unpublish_vacancy`, `reject_candidate`, `batch_move_candidates`/`bulk_*`, `send_email`/`send_whatsapp`/`send_bulk_email`. (em `job_tools.py`, `communication_tools.py`, kanban/talent registries — via o decorator `@tool_handler(..., requires_confirmation=True)`).
- **Fix-no-produtor adicional (close_job pré-commit):** mover o bloqueio pra ANTES do `db.commit()` — padrão `OfferService.check_can_send` (pre-flight raise antes do side-effect), não flag no retorno.
- Sensor: por tool sensível, contract test (gate dispara antes do commit).

### 3.2 🟡 Streaming / reasoning_step — MORTO em ambas
**Problema:** `reasoning_step` só é emitido por `_run_graph_streaming` (`langgraph_base.py:229`), gated por `LIA_WS_ASTREAM` (AUSENTE no `.env` → OFF). `token` NÃO está em `_SSE_FORWARD_TYPES` (`streaming_callback.py:44`) → tokens vão só pro `ws_manager`, não pro SSE. Supervisor: o `streaming_callback` passado em `agent_chat_sse.py:616` é DROPADO — `MainOrchestrator` nunca o invoca (`main_orchestrator.py:2667/2832` não o threadam pro `Orchestrator.process_request`); só tool frames oportunistas via sink herdado quando roteia p/ domain ReAct.
**Fix:**
- (a) **Threadar** `streaming_callback` de `MainOrchestrator.process` → `Orchestrator.process_request`/`DomainWorkflow` (hoje cortado em `main_orchestrator.py:2832`).
- (b) Decidir **token-by-token no SSE**: ou adicionar `token` a `_SSE_FORWARD_TYPES` (+ forward no sink), ou ligar `_llm_streaming_callback` no caminho LangGraph. (Hoje só a mensagem final chega.)
- (c) `reasoning_step` exige **`LIA_WS_ASTREAM=on`** (Secret, decisão do Paulo) pra ter efeito. Isso é o que faz os "pontos piscando"/timeline serem ricos. Sensor: `tests/contract/test_reasoning_streaming.py` (já existe, declara o astream behind-flag).

---

## 4. GAPS PATH-SPECIFIC (depois da decisão fed×sup)

### 4.1 Supervisor — 🔴 Navegação [NAVIGATE] vaza como texto
`main_orchestrator.py:1428` usa `content` cru; system prompt (`main_orchestrator.py:1141-1171`) MANDA a LLM emitir `[NAVIGATE:<page>]` como texto; `_orchestrator_result_to_frames` (`chat.py:910-928`) só monta navigation `if ui_action` já presente, repassa content sem strip.
**Fix canônico (1 lugar):** aplicar `_extract_navigate_marker` (`app/orchestrator/context/chat_adapter.py:221-271`) em `_orchestrator_result_to_frames` sobre `content` quando `ui_action` ausente → strip + injeta `ui_action='navigate_to'`/`ui_action_params` (espelha `agent_chat_sse.py:864-877` do ramo agente). Sensor: serialização (marker→ui_action, sem leak).

### 4.2 Supervisor — 🟡 RRP de sub-agente dropado
`workflow.py:736` põe blocks em `DomainResponse.metadata`; `legacy/orchestrator.py:304-310` result dict carrega `dr.data` mas **DESCARTA `dr.metadata`** → response_blocks do sub-agente se perdem antes de `ChatResponse.from_orchestrator_result` (`main_orchestrator.py:226`). (Funciona só via Phase 1 ActionExecutor `sourcing_actions.py:257`.)
**Fix:** carregar `response_blocks` no result dict do legacy orchestrator (`result["response_blocks"] = dr.metadata.get("response_blocks")` ou `result["structured_data"]={...}`), p/ `from_orchestrator_result` pegar.

### 4.3 Federado — 🟡 Wizard turno-1 (seam de entrada)
`is_wizard_session_active` (`thread_id.py:181`) exige checkpoint → turno-1 `pin=False` → "criar vaga" turno-1 cai pra trilha. Federado `recruiter_copilot` (344L) não tem bootstrap turno-1 do WizardSessionService (supervisor tem Phase 1.4 `main_orchestrator.py:2344-2468`).
**Fix:** dar ao federado entrada turno-1 de wizard OU um pré-intercept turno-1 no SSE cobrindo as 2 trilhas. (Mid-wizard já é canônico/idêntico nas duas.)

### 4.4 Federado — 🔴 Panels (panel_update) = dead code
`recruiter_copilot_react_agent.py:298-308` `_state_to_output` nunca seta `output.metadata['panel_update']`; `agent_chat_sse.py:900` lê = código morto. (Mitigado: painel do wizard servido pelo ramo `resolved_domain=='wizard'` L417-503, curto-circuita as trilhas.)
**Fix (se federado escolhido):** federado popular `output.metadata['panel_update']` OU criar `panel_sink` espelhando `app/shared/rrp_block_sink.py` + drain em `langgraph_react_base.py:322-335`.

### 4.5 Federado — 🟡 stage-nav output-side (deferido)
`recruiter_copilot` `_state_to_output` retorna `AgentOutput` sem `navigation=`; sub-agentes (kanban/talent/jobs `_react_agent.py:157-175`) emitem `NavigationCommand(target_stage, auto_navigate)`. SSE já consome `output.navigation` (`agent_chat_sse.py:921`).
**Fix (se federado + se auto-advance de funil for requisito):** portar a lógica `NavigationCommand` pro `_state_to_output` do recruiter_copilot.

### 4.6 Federado — fragilidade do def-assembly (OK hoje, registrar)
def-assembly está **FIXADO** (`18f9cfb33`; empírico GLOBAL=11/talent=47/job=30/in_job=39; `_GLOBAL_ESSENTIALS` tem rank/compare). Ressalva: o fallback `_FEDERATION_SPEC` (scoping OFF) omite rank/compare; só não morde porque `LIA_FEDERATED_PRIMARY` FORÇA scoping (`scope_config.py:394`). Se alguém desacoplar, o moat sai. Não-urgente.

---

## 5. OUTROS ACHADOS (defense-in-depth — FALTAVAM no resumo)

### 5.1 🟡 C3B SSE-vs-WS (input guards)
O SSE faz FairnessGuard de input **inline** (`agent_chat_sse.py:288`), NÃO via `pre_compliance()` → **NÃO** roda `HateSpeechGuard` nem `PromptInjectionGuard` (`c3b_layer.py:112-175`), que só rodam em callers que usam `pre_compliance` (ex: WS). Vale igual p/ federado e supervisor (não quebra paridade fed×sup), mas é gap de defesa SSE vs WS.
**Fix:** SSE usar `pre_compliance` no input (ou adicionar os 2 guards inline). Risco: `LIA_DISABLE_C3B=1` vira passthrough em ambas (mas audita kill-switch).

### 5.2 🟡 Persistência — durabilidade assimétrica
Federado: se `agent.process` der timeout/erro, `_cmem.add_message` NÃO roda → NEM user NEM assistant gravados naquele turno. Supervisor: user gravado cedo (`main_orchestrator.py:2763`); `_persist_response` só grava assistant se `result['success']` (`:2851`) → `success=False` perde o assistant. Ambos fail-open (warning, sem retry).
**Fix (opcional):** gravar user antes no federado também; gravar assistant mesmo em success=False (com flag).

### 5.3 🟢 Multi-tenancy — P2 residuais (sem gap cross-tenant)
`agent_chat_sse.py:254` `_extract_auth` pula a normalização `CompanyId.parse` que `require_company_id` aplica (inconsistência, não vazamento). DEV mode injeta `DEMO_COMPANY_UUID` sintético (esperado). Prova "JWT-only" só vale em prod.

### 5.4 🟡 Split-brain RRP (ADR-001 / canonical-fix)
DOIS produtores do ranking: `rrp_ranking_builder.build_candidate_ranking_blocks` (tools talent/kanban → federado) E re-implementação inline em `sourcing_actions._rank_candidates` (`main_orchestrator.py:230-258` monta ComparisonTable/ScoreExplainer/EvidenceStack à mão → supervisor ActionExecutor). Deviam convergir no builder único.

---

## 6. TRABALHO DESTA SESSÃO — COMMITADO, AGUARDANDO VALIDAÇÃO LIVE (porta 5000)
Tudo sem push, branch `feat/benefits-prv-canonical`. **Não duplicar.**

**Chat rendering (FE + prompt + tool):**
- `5c6dcdbae` reasoning bleed (reset thinkingSteps no envio, useChatSocket).
- `ec2260c40` reasoning visual (ActivityDots inline na linha em foco; removeu WorkingDots).
- `fc8cce6c6` autoscroll (ResizeObserver no conteúdo).
- `7e76e1e98` over-nav (REGRA 8/9 no system_prompt_builder: não oferecer navegação).
- `b03647c0b` 2-table (render_hint co-locado no result das tools RRP).

**Embedding (busca semântica):**
- `cf90648e5` openai aceita `OPENAI_API_KEY` fallback → busca semântica restaurada.
- `60d2a10a4` B1: PII chokepoint no EmbeddingService (estruturada universal).
- `f79bbce1e` B2: memory_service (conversa) com mask_names=True (nomes via Presidio).

**Federado/consolidação + nivelamento:**
- `d805f8d30` hoist memória-load + entity-resolve pra ANTES do dispatch (shared agente+supervisor).
- `2e42d62dc` C3B post_compliance na trilha supervisor (paridade governança).
- `2746e42e7` HITL gate core 1a (fundação, ativa nada).

**Recomendação de env (decisão do Paulo, Secret):** `EMBEDDING_DEFAULT_PROVIDER=openai` (pula o gemini quebrado — proxy Replit rejeita `text-embedding-004:batchEmbedContents`). `LIA_WS_ASTREAM=on` (liga reasoning_step rico).

---

## 7. EPIC SEPARADO PENDENTE: BYOK embedding + PII granular + modal
Decisão Paulo: BYOK **opção 1** (desacoplado, default gerenciado, opt-in) + PII **granular por superfície** (candidato/conversa=estruturada+nomes; vaga/JD=estruturada). Detalhes completos em `~/.claude/.../memory/project_byok_embedding_pii.md`. Pendente:
- **A) Wirar BYOK embedding ponta-a-ponta:** passar `company_id` por `EmbeddingService`→`embed_with_fallback`→ler `routing["embedding"]` + chave do tenant; branch openai por-tenant (hoje só gemini em `_get_tenant_provider`); fixar tenant a 1 modelo (dim 768) + re-embed ao trocar. (Hoje embedding usa chave GLOBAL, ignora tenant config = ghost setting.)
- **B2-sourcing:** mascarar nomes na query exige `candidate_embeddings` gravado no mesmo nível — investigar onde é populado (fallback diz "table may not exist").
- **C) Modal de transparência** em `plataforma-lia/src/components/settings/IntegrationsHub.tsx`: onde embedding roda + provedor + política PII por superfície (a matriz). Claude NÃO faz embedding (Anthropic não tem API nativa; parceira = Voyage AI).

---

## 8. DECISÃO PENDENTE (Paulo) + PROTOCOLO A/B
**Decisão #1: federado vs supervisor.** Os gaps próprios quase se equilibram; o que pesa são os 2 compartilhados (HITL+streaming) — fazer ANTES de decidir.
**Protocolo A/B (após fixes compartilhados):**
1. Federado: Secret `LIA_FEDERATED_PRIMARY=true` + restart. (⚠️ re-validar o def-assembly `18f9cfb33` que falhou 1×.)
2. Supervisor: Secret `LIA_BUBBLE_VIA_SUPERVISOR=true` + restart.
3. 6 queries-âncora em cada: "tem felipe almeida?", "temos vaga de diretor jurídico?", "rankeie Diretor Jurídico", "perfil do Felipe Almeida", "como está o pipeline", "me leve pra vagas/abrir vaga X". Comparar.
Cenário de-riscado: vaga **Diretor Jurídico** `610705ab-7a98-45e9-999a-5bdb62975989` tem 24 no pipeline, 3 com parecer (Felipe Almeida=Altamente Recomendado) → acende o moat RRP.

---

## 9. SEQUÊNCIA RECOMENDADA (próxima sessão)
1. **HITL 1b** (surfacing SSE + detecção de aprovação server-side, reusar PendingAction) → **1c** (marcar tools + close_job pre-flight). [P0 segurança, compartilhado]
2. **Streaming/reasoning** (threadar callback + token + `LIA_WS_ASTREAM`). [compartilhado, UX]
3. **Validação live** dos fixes desta sessão (seção 6) + dos 2 compartilhados.
4. **Decisão fed×sup** (A/B) → fechar gaps próprios da trilha escolhida (seção 4).
5. Defense-in-depth (seção 5) + split-brain RRP (oportunístico).
6. Epic BYOK embedding (seção 7) quando priorizado.

Cada item: ground-truth o produtor inteiro → Red test → fix no produtor → Green → commit atômico pathspec (sem push) → validação live do Paulo.
