# Fluxo Técnico Completo — Plataforma LIA Alpha 1

**Data:** 31/03/2026  
**Versão:** 1.0  
**Escopo:** Fluxo end-to-end Alpha 1 — desde Login até Scheduling/Feedback  
**Formato:** Diagrama passo-a-passo por macro-etapa (estilo "11 STEPS" do WSI)  
**Referência:** `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` v6.3 (complementar)

---

## COMO LER ESTE DOCUMENTO

Cada macro-etapa do Alpha 1 (E1–E9B) é apresentada como um diagrama técnico passo-a-passo, seguindo o formato visual dos "11 STEPS" do fluxo de triagem WSI (ver imagem de referência). Cada step mostra:

1. **O request HTTP real** — endpoint, método, payload
2. **O roteamento** — DomainOrchestrator, CascadedRouter (6 tiers), domínio destino
3. **Os mixins/capabilities injetados** — EnhancedAgentMixin, AuditTrail, WorkingMemory, etc.
4. **FairnessGuard** — quais camadas (L1 explicit, L2 implicit, L3 semantic) atuam ANTES e DEPOIS do LLM
5. **PII Masking** — 4 camadas pré-LLM (CPF, nome, endereço, campos sensíveis)
6. **Processamento** — qual agente/serviço, qual LLM, qual graph/loop
7. **FactChecker** — 4 tipos de verificação pós-LLM
8. **ConfidenceNode + BiasAuditSnapshot** — calibração, Four-Fifths Rule
9. **AuditTrail** — o que é registrado, append-only, retenção SOX
10. **Response final** — dados demasked, scores, recomendação

### Legenda de Status

| Símbolo | Significado |
|---------|------------|
| ● | Ativo — funcionando no código |
| ◐ | Disponível — código existe, precisa ativar/configurar |
| ○ | A implementar — código não existe |
| ⚠ | Gap bloqueante — requer ação antes do MVP |
| 🔒 | Camada de proteção/compliance |
| 🧠 | Camada de inteligência/learning |

### Convenção de Agentes

| Rótulo | Classe no código | Domínio | LLM Provider |
|--------|-----------------|---------|--------------|
| Ag.0 | MainOrchestrator | orchestrator | Gemini (produção) |
| Ag.2 | SourcingReActAgent | sourcing | Gemini |
| Ag.3 | TriagemCurricular (CV Screening) | cv_screening | Gemini |
| Ag.4 | WSIInterviewGraph | cv_screening | Gemini |
| Ag.5 | WSIService (scoring) | cv_screening | Determinístico (sem LLM) |
| Ag.6 | InterviewGraph | interview_scheduling | Gemini |
| Ag.7 | CommunicationReActAgent / PersonalizedFeedbackService | communication / cv_screening | Gemini |
| Ag.8 | ATSIntegrationReActAgent ⚠ PÓS-MVP | ats_integration | Gemini |
| — | WSIQuestionGenerator / WSIScreeningQuestionGenerator | cv_screening | Gemini |
| — | WSIScreeningPipeline | cv_screening | Gemini |
| — | WSIVoiceOrchestrator | cv_screening | Gemini + Deepgram |
| — | JobDescriptionGeneratorService | job_management | Claude (Anthropic) |

---

## E0 — ARQUITETURA DE IA (CAMADA COGNITIVA)

> **Por que este capítulo existe.** As etapas E1–E9 descrevem *o que* acontece em cada jornada do recrutador. Este capítulo descreve **a base cognitiva** sobre a qual todas as etapas rodam: como uma mensagem entra no sistema, é roteada para um domínio, executa um agente, dispara ferramentas (tools), passa pelos escudos de compliance e gera resposta. Tudo o que aparece em E1–E9 ("CascadedRouter (6 tiers)", "FairnessGuard", "PII Masking", "AuditTrail", "Persona LIA") é apresentado aqui como **componente arquitetural** com arquivo canônico, status real (ativo / stub) e participação em cada etapa.
>
> **Fontes canônicas (não duplicar — apontar):**
> - Decisões de arquitetura: `lia-agent-system/ARCHITECTURE.md` (ADRs 001–020)
> - Roteamento por domínio: `lia-agent-system/app/orchestrator/cascaded_router.py` + `app/orchestrator/config/domain_routing.yaml`
> - Mapeamento agent_type → domain: `lia-agent-system/app/orchestrator/domain_mappings.py`
> - Permissões de tools por tenant: `lia-agent-system/app/tools/tool_permissions.yaml`
>
> Se houver conflito entre este capítulo e o código real, **vence o código** — abrir issue para corrigir o doc.

### E0.1 — As 4 grandes camadas

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  CAMADA COGNITIVA DA PLATAFORMA LIA — VISÃO MACRO                            │
└──────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │  1. ROTEAMENTO   CascadedRouter (8 tiers cascateados)               │
   │                  domain_routing.yaml + domain_mappings.py           │
   └────────────────────────────┬────────────────────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  2. DOMÍNIOS    DomainRegistry (@register_domain)                   │
   │                 19 domínios canônicos — domain.py por pasta         │
   └────────────────────────────┬────────────────────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  3. AGENTES     AgentRegistry (@register_agent + aliases)           │
   │                 ReAct (LangGraph) + EnhancedAgentMixin              │
   └────────────────────────────┬────────────────────────────────────────┘
                                ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  4. TOOLS       ToolRegistry + tool_permissions.yaml (por tenant)   │
   │                 LLM Cascade (Haiku → Sonnet → Opus / Gemini)        │
   └─────────────────────────────────────────────────────────────────────┘

   Em paralelo (transversal a todas as camadas):
   • ContextAggregatorService — empacota tenant + memória + RAG → prompt
   • Memory subsystem          — ConversationState + WorkingMemory + RAG
   • 6 Escudos de Compliance   — FairnessGuard 3L, PII Masking 4L, FactChecker,
                                 BiasAudit Four-Fifths, AuditTrail SOX, Policy
   • Persona LIA + Anti-Sycophancy + Defensive Prompts (anti prompt-injection)
   • Observabilidade            — tracing OTel, structured_logging, drift_alert
```

### E0.2 — CascadedRouter — pipeline de 8 tiers

Implementação canônica: `lia-agent-system/app/orchestrator/cascaded_router.py`. Cada mensagem do recrutador percorre a cascata em ordem de **custo crescente** — só desce para o próximo tier se o anterior não resolveu com confiança suficiente. A implementação real tem **8 tiers** (não 5 como em rascunhos antigos do roadmap, e não 6 como ainda aparece em E1.2 — esse número deve ser corrigido para 8 nas próximas revisões).

| Tier | Nome | Custo | Tipo de match | Threshold | Status |
|------|------|------|---------------|-----------|--------|
| 0 | MemoryResolver | ~0ms | resolve pronomes via WorkingMemory antes de rotear ("ele", "essa vaga") | n/a | ● |
| 1 | LRU in-process | <1ms | hash MD5 da mensagem normalizada | exato | ● |
| 2 | Redis hash cache | ~2ms | hash distribuído (compartilhado entre workers) | exato | ● |
| 3 | VectorSemanticCache | ~10ms | pgvector cosine similarity | `ROUTER_VECTOR_SIMILARITY_THRESHOLD` (default 0.85) | ◐ (gated por `ROUTER_VECTOR_CACHE_ENABLED`) |
| 4 | FastRouter (regex) | ~5ms | patterns YAML por domínio | `ROUTER_FAST_CONFIDENCE_THRESHOLD` | ● |
| 5 | LLM Cascade (Haiku→Sonnet→Opus) | 100ms–2s | classificação por LLM com A/B de system prompt | `ROUTER_LLM_CASCADE_MIN_CONFIDENCE` (default 0.5) | ● |
| 6 | AutonomousReActAgent | 2s+ | agente cross-domain como último fallback antes de pedir clarificação | n/a | ◐ (gated por `AUTONOMOUS_REACT_ENABLED`) |
| Fallback | Clarification | — | gera pergunta para o usuário com base em matches parciais | n/a | ● |

Configuração declarativa: `app/orchestrator/config/domain_routing.yaml` (config-as-data — editar YAML + restart, sem deploy de código). Fallback hardcoded em `_HARDCODED_DOMAIN_PATTERNS` dentro de `fast_router.py` se o YAML estiver ausente/inválido.

Tradução de `agent_type` (saída do Tier 5) → `domain_id` canônico: `app/orchestrator/domain_mappings.py`. Se um `agent_type` desconhecido cair no `DEFAULT_DOMAIN` (`recruiter_assistant`), um `logger.warning` estruturado + contador agregado é emitido (ADR-019, observável via `GET /api/v1/orchestrator/health`).

### E0.3 — Domain Registry (19 domínios canônicos)

Implementação: `lia-agent-system/app/domains/registry.py` (`@register_domain` decorator) + `app/domains/__init__.py` (auto-discovery por import side-effect). Cada domínio expõe `domain_id`, `actions` e `agent_aliases`.

| Domínio | Arquivo | Status | Etapas em que participa |
|---------|---------|--------|------------------------|
| `analytics` | `app/domains/analytics/domain.py` | ● | E8 (relatórios), transversal |
| `ats_integration` | `app/domains/ats_integration/domain.py` | ◐ PÓS-MVP | E2, E4 (sync) |
| `automation` | `app/domains/automation/domain.py` | ● | transversal (tarefas, lembretes) |
| `candidate_self_service` | `app/domains/candidate_self_service/domain.py` | ● | E7 (autoatendimento candidato) |
| `communication` | `app/domains/communication/domain.py` | ● | E6, E7B, E9B |
| `company_settings` | `app/domains/company_settings/domain.py` | ◐ (5 das 7 actions retornam `_configure_unavailable`; ver Task #712) | Onboarding + Configurações |
| `cv_screening` | `app/domains/cv_screening/domain.py` | ● | E7, E7A, E7B |
| `digital_twin` | `app/domains/digital_twin/domain.py` | ◐ Phase 6 | pós-MVP |
| `hiring_policy` | `app/domains/hiring_policy/domain.py` | ● | E2, E5, E8 (gates) |
| `interview_scheduling` | `app/domains/interview_scheduling/domain.py` | ● | E9A |
| `job_creation` (Wizard WSI) | `app/domains/job_creation/domain.py` | ◐ (intent-routed wizard, ADR-020) | E2, E3 |
| `job_management` | `app/domains/job_management/domain.py` | ● | E2 |
| `pipeline` (transition) | `app/domains/pipeline/domain.py` | ● | E5, E8 |
| `recruiter_assistant` | `app/domains/recruiter_assistant/domain.py` | ● | transversal — `DEFAULT_DOMAIN` |
| `recruitment_campaign` | `app/domains/recruitment_campaign/domain.py` | ◐ Phase 6 | pós-MVP |
| `sourcing` | `app/domains/sourcing/domain.py` | ● | E4 |
| `agent_studio` | `app/domains/agent_studio/domain.py` | ◐ Phase 6 | pós-MVP |
| `talent_pool` | `app/domains/talent_pool/domain.py` | ◐ Phase 6 | E4 (pool) |
| `job_management` (subagentes kanban) | `kanban_search/insight/action` | ● | E5, E8 |

> **Stubs em destaque.** `company_settings` (5 de 7 actions ainda retornam erro proposital — alvo de Task #712) e os 4 domínios Phase 6 (`digital_twin`, `agent_studio`, `talent_pool`, `recruitment_campaign`) estão **fora do MVP Alpha1**.

### E0.4 — Agent Registry — 1 agente por domínio (+ subagentes)

Implementação: `lia-agent-system/app/shared/agents/agent_registry.py` (`@register_agent(id, aliases=[...])` + lazy singleton). Todos os agentes herdam de `LangGraphReActBase` + `EnhancedAgentMixin` (injeta auditoria, working memory, fairness, persona).

| Agente | Arquivo | Domínio que serve |
|--------|---------|-------------------|
| `wizard` (alias `job_management`, `job_mgmt`) | `domains/job_management/agents/wizard_react_agent.py` | job_management |
| `pipeline` (alias `cv_screening`) | `domains/cv_screening/agents/pipeline_react_agent.py` | cv_screening |
| `sourcing` | `domains/sourcing/agents/sourcing_react_agent.py` | sourcing |
| `sourcing_planner` / `sourcing_search` / `sourcing_enrich` / `sourcing_engagement` | `domains/sourcing/agents/*.py` | sourcing (subagentes Z2) |
| `kanban` + `kanban_search` / `kanban_insight` / `kanban_action` | `domains/recruiter_assistant/agents/kanban_*.py` | recruiter_assistant (subagentes Z1) |
| `pipeline_context` / `pipeline_decision` / `pipeline_action` / `pipeline_transition` | `domains/pipeline/agents/*.py` | pipeline (subagentes Z1) |
| `communication` (alias `comms`) | `domains/communication/agents/communication_react_agent.py` | communication |
| `analytics` | `domains/analytics/agents/analytics_react_agent.py` | analytics |
| `ats_integration` (alias `ats`) | `domains/ats_integration/agents/ats_integration_react_agent.py` | ats_integration |
| `automation` (alias `task_planning`) | `domains/automation/agents/automation_react_agent.py` | automation |
| `talent` | `domains/recruiter_assistant/agents/talent_react_agent.py` | recruiter_assistant |
| `jobs_management` (alias `jobs_mgmt`, `job_management`) | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | recruiter_assistant |
| `policy` | `domains/hiring_policy/agents/policy_react_agent.py` | hiring_policy |
| `company_settings` | `domains/company_settings/agents/company_react_agent.py` | company_settings |
| `candidate_self_service` | `domains/candidate_self_service/agents/candidate_react_agent.py` | candidate_self_service |

Total: **27 agentes registrados** (12 principais + 15 subagentes Z1/Z2). Cada um declara seus aliases — colisão dispara `WARNING` no `agent_registry.py` e teste de CI `test_no_orphan_agent_types`.

### E0.5 — Tool Registry e permissões por tenant

Implementação: `lia-agent-system/app/tools/registry.py` (`ToolRegistry`) + `app/tools/tool_registry_loader.py` (loader declarativo) + `app/tools/tool_registry_metadata.yaml` (metadados das tools).

Permissões por tenant: `app/tools/tool_permissions.yaml` (loader: `tool_permissions_loader.py`). Define **quais tools cada tenant pode invocar** + `llm_provider` + `llm_fallback_order` por tenant. Bypass direto a `tool_registry.register(...)` fora do entry point canônico é bloqueado pelo CI (ADR-015 S7.5).

Autoria de tools (ADR-015 S7.4): proibido `from langchain_core.tools import tool` em tools de domínio — autoria canônica é via decorator interno + metadata YAML. `GlobalToolRegistry` foi aposentado (Task #350).

Categorias de tools transversais em `app/shared/tools/`:
- `proactive_tools.py` — sugestões proativas no chat
- `predictive_tools.py` — predição (time-to-hire, churn de candidato)
- `insight_tools.py` — análise de funil/pipeline
- `export_tools.py` — exportação CSV/JSON

### E0.6 — Context Aggregator e Memory subsystem

`lia-agent-system/app/shared/services/context_aggregator_service.py` é o serviço que **monta o contexto completo** que vai junto com cada chamada ao LLM:
- Identidade do tenant + recrutador (via `tenant_context_service.py`)
- Estado da conversa (`ConversationState` em `app/shared/memory/conversation_state.py`)
- Histórico curto (últimas N mensagens)
- RAG: trechos relevantes recuperados por similaridade (via VectorSemanticCache / pgvector)
- Memória de longo prazo: preferências do recrutador, contexto de vagas ativas

Memory subsystem (`app/shared/memory/`):
- `conversation_state.py` — `ConversationState` por sessão (shortlist, candidatos exibidos, última action)
- `candidate_list_store.py` — cache da última listagem de candidatos exibida
- `reference_resolver.py` — resolve pronomes ("ele", "esses dois") usando o `ConversationState`

Working Memory (Tier 0 do CascadedRouter) usa `memory_resolver.py` em `app/orchestrator/` — reescreve a mensagem do recrutador antes do roteamento (ex.: "agenda entrevista com ele" → "agenda entrevista com candidato_id=4711").

### E0.7 — Os 6 Escudos de Compliance

Implementação em `lia-agent-system/app/shared/compliance/`. Detalhes técnicos completos estão na **SEÇÃO TRANSVERSAL: COMPLIANCE TÉCNICO** mais abaixo neste mesmo doc — esta tabela é o índice e o ponto de entrada:

| # | Escudo | Arquivo canônico | Roda quando | Status |
|---|--------|-----------------|-------------|--------|
| 1 | **FairnessGuard** (3 camadas: L1 explicit, L2 implicit, L3 semantic) | `compliance/fairness_guard.py` + `fairness_guard_middleware.py` | Antes E depois do LLM em qualquer action que envolva candidato | ● |
| 2 | **PII Masking** (4 camadas: CPF, nome, endereço, campos sensíveis) | `app/shared/pii_masking.py` (filtro global) + `compliance/protected_attributes.py` | Sempre — pipeline pré-LLM e em logs | ● |
| 3 | **FactChecker** (4 tipos de verificação) | `compliance/fact_checker.py` | Pós-LLM em outputs com afirmações sobre candidatos/vagas | ● |
| 4 | **BiasAudit / Four-Fifths Rule** | `compliance/bias_audit_service.py` | Após decisões agregadas (E5 Gate 1, E8 Gate 2) | ● |
| 5 | **AuditTrail SOX-compliant** (append-only) | `compliance/audit_service.py` + `audit_storage.py` + `audit_writer.py` | Toda mutação de dados sensíveis (login, hire, reject, score, transition) | ● (gap em E1 — ver "GAPS CONSOLIDADOS") |
| 6 | **Policy Engine** (motor de políticas por setor) | `app/shared/policy_helper.py` + `compliance/guardrail_repository.py` | Antes de qualquer action — gate por setor/tenant | ● |

Adicionalmente (não conta como "escudo" formal mas é compliance):
- **PromptInjectionGuard** — `compliance/prompt_injection_guard.py` (sanitiza inputs do recrutador antes do LLM)
- **C3B Layer** — `compliance/c3b_layer.py` (Camada 3 Blindada para outputs sensíveis)
- **Scoring Safeguards** — `compliance/scoring_safeguards.py` (caps + sanity checks em scores WSI)

### E0.8 — Persona LIA + Anti-Sycophancy + Defensive Prompts

Camada de **comportamento conversacional** — não é compliance, mas é o que dá a "voz" da LIA e a torna resistente a manipulação:

| Componente | Arquivo | O que faz | Status |
|-----------|---------|-----------|--------|
| Persona LIA (system prompt mestre) | `app/shared/prompts/system_prompt_builder.py` + `templates.py` | Define tom, escopo (recrutamento brasileiro), limites éticos | ● |
| Training Persona | `app/shared/prompts/training_persona.py` | Modo "explicar como funciona o módulo" (responde a `/help`, "o que é a LIA") | ● |
| Anti-Sycophancy (3 variantes) | `app/shared/prompts/anti_sycophancy_block.py` | Bloqueia bajulação automática ("ótima pergunta!") em outputs de avaliação | ● |
| Few-shot examples (CoT, intent) | `app/shared/prompts/few_shot_examples.py` + `cot.py` + `intent_few_shot_examples.py` | Calibra o LLM com exemplos de respostas LIA-style | ● |
| Interaction Patterns | `app/shared/prompts/interaction_patterns.py` | Padrões de pergunta/resposta (clarification, confirmação, recusa) | ● |
| Defensive Prompts | `compliance/prompt_injection_guard.py` (input) + Persona (output) | Sanitiza e blinda contra prompt injection | ● |

A/B testing de variantes do system prompt do CascadedRouter está ativo: experimento `cascade_router_system_prompt` registrado em `app/prompts/experiments/cascade_router_system_prompt.yaml` — usa `app/shared/prompt_experiment.py` para selecionar variante por hash do `user_id`.

### E0.9 — Observabilidade da camada cognitiva

Implementação: `lia-agent-system/app/shared/observability/`. Não é parte do "ato cognitivo" em si, mas sem ela é impossível debugar regressões dos 8 tiers, do roteamento ou do drift do modelo.

| Componente | Arquivo | O que captura | Status |
|-----------|---------|---------------|--------|
| Distributed tracing (OTel) | `observability/tracing.py` (via `get_tracer`) | Span por tier do CascadedRouter, latência por agente, latência por tool | ● |
| Structured logging | `observability/structured_logging.py` | Logs JSON com `tenant_id`, `conversation_id`, `agent_type`, `domain_id` (sem PII) | ● |
| Agent monitoring | `observability/agent_monitoring_service.py` + `agent_health_alert_service.py` | Health por agente (success rate, latency p50/p95) | ● |
| Model drift | `observability/model_drift_service.py` + `drift_alert_service.py` | Alerta quando distribuição de scores WSI deriva | ◐ |
| LangSmith integration | `observability/langsmith.py` | Trace de cadeias LangGraph (opt-in) | ◐ |
| AI consumption outbox | `observability/ai_consumption_outbox_worker.py` | Custo por tenant/agente (tokens × modelo) | ● |
| Silent-fallback counter (ADR-019) | `app/orchestrator/domain_mappings.py` | `agent_type` desconhecido → DEFAULT_DOMAIN | ● |

### E0.10 — Diagrama: 1 mensagem do recrutador → resposta

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ANATOMIA DE 1 MENSAGEM — DO TECLADO DO RECRUTADOR ATÉ A RESPOSTA            │
│  (tudo o que aparece em E1–E9 desce por este pipeline)                       │
└──────────────────────────────────────────────────────────────────────────────┘

  Recrutador digita: "manda whatsapp para o João aprovando ele para a próxima etapa"

  ─── ENTRADA ──────────────────────────────────────────────────────────────────

   1  HTTP/WS chega ao FastAPI
      POST /api/v1/agent/chat (ou WS /ws/agent_chat)
      Headers: Authorization Bearer <JWT> (tenant + user)
      Middleware global: PIIMaskingFilter (logs), RateLimit, RequestID

  ─── ROTEAMENTO (CascadedRouter — 8 tiers) ───────────────────────────────────

   2  Tier 0: MemoryResolver
      "ele" → resolve para candidate_id=4711 via WorkingMemory da sessão
      Mensagem reescrita: "manda whatsapp para João (id=4711) aprovando..."
      🔒 PromptInjectionGuard sanitiza tokens suspeitos

   3  Tier 1–3: caches (LRU → Redis hash → pgvector)
      Hash MD5 → miss; Redis → miss; vector cosine 0.78 < 0.85 → miss

   4  Tier 4: FastRouter (regex YAML)
      Pattern "mand[ao].*\bwhatsapp\b" do domínio `communication` casa
      confidence=0.92 ≥ ROUTER_FAST_CONFIDENCE_THRESHOLD → PARA AQUI
      RouteResult(domain_id="communication", source="fast_router")

      (Se Tier 4 falhasse → Tier 5 LLM Cascade Haiku→Sonnet→Opus →
       Tier 6 AutonomousReActAgent → Fallback Clarification)

  ─── EXECUÇÃO NO DOMÍNIO ─────────────────────────────────────────────────────

   5  DomainOrchestrator → CommunicationDomain (`@register_domain`)
      action = "send_whatsapp_to_candidate" (intent extraída do Tier 4/5)

   6  AgentRegistry resolve → CommunicationReActAgent (`@register_agent("communication")`)
      Mixins: EnhancedAgentMixin (audit + memory + fairness + persona)

   7  ContextAggregatorService monta o prompt
      = persona LIA + anti-sycophancy + tenant_context + ConversationState
        + RAG (últimas mensagens com o candidato) + few-shot examples

  ─── ESCUDOS PRÉ-LLM ─────────────────────────────────────────────────────────

   8  🔒 PII Masking (4 camadas)
      CPF, telefone, endereço do João são substituídos por tokens

   9  🔒 FairnessGuard L1 (explicit) + L2 (implicit)
      Verifica que o critério de aprovação não cita atributo protegido
      (gênero, raça, idade, religião, orientação)

  ─── LLM CASCADE ────────────────────────────────────────────────────────────

  10  LLM seleciona tool: communication.send_whatsapp_template
      Tool Registry valida permissão via tool_permissions.yaml para o tenant
      Tool executa → WhatsApp Business API → Twilio gateway

  ─── ESCUDOS PÓS-LLM ────────────────────────────────────────────────────────

  11  🔒 FairnessGuard L3 (semantic) sobre o texto gerado
      Bloqueia frases potencialmente discriminatórias

  12  🔒 FactChecker (4 tipos) — afirmações sobre o candidato batem com o BD?
      "João, aprovado para etapa Entrevista Técnica" ✓

  13  🔒 PII Demasking — tokens voltam a ser dados reais para a resposta ao
      recrutador (mas NÃO para o log)

  14  🔒 AuditTrail (SOX append-only) — registra:
      tenant + user + candidate_id + action + before_state + after_state
      + agent_type + tool_used + latência + custo (tokens × modelo)

  ─── INTELIGÊNCIA (transversal) ─────────────────────────────────────────────

  15  🧠 Learning Loop (silencioso) — captura par (input → action → outcome)
      para retraining e calibração futura
      🧠 BiasAuditSnapshot — se for decisão agregada (Gate 1/2), Four-Fifths
      🧠 ModelDrift — log de scores WSI para alerta de drift

  ─── RESPOSTA ───────────────────────────────────────────────────────────────

  16  Response envelope (ADR-008) volta ao frontend
      { ok: true, data: {...}, meta: { agent: "communication", latency_ms, cost } }
      Frontend (Chat Unified) renderiza no card do João + atualiza Kanban
```

### E0.11 — Mapa: componente cognitivo × etapa E1–E9

| Componente | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 |
|-----------|----|----|----|----|----|----|----|----|----|
| CascadedRouter | — | ● | ● | ● | ● | ● | ● | ● | ● |
| MemoryResolver (Tier 0) | — | — | — | ● | ● | ● | ● | ● | ● |
| FastRouter (Tier 4) | — | ● | ● | ● | ● | ● | ● | ● | ● |
| LLM Cascade (Tier 5) | — | ● | ● | ● | ● | ● | ● | ● | ● |
| ContextAggregator | — | ● | ● | ● | ● | ● | ● | ● | ● |
| ConversationState | — | ● | ● | ● | ● | ● | ● | ● | ● |
| RAG (pgvector) | — | ◐ | ● | ● | ● | ● | ● | ● | ● |
| FairnessGuard 3L | — | — | ● | ● | ● | — | ● | ● | — |
| PII Masking 4L | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| FactChecker | — | ● | — | ● | ● | ● | ● | ● | — |
| BiasAudit Four-Fifths | — | — | — | — | ● | — | ● | ● | — |
| AuditTrail SOX | ◐ (gap) | ● | ● | ● | ● | ● | ● | ● | ● |
| Policy Engine | — | ● | ● | ● | ● | ● | ● | ● | ● |
| PromptInjectionGuard | — | ● | ● | ● | ● | ● | ● | ● | ● |
| Persona + Anti-Sycophancy | — | ● | ● | ● | ● | ● | ● | ● | ● |

Legenda: ● ativo na etapa · ◐ disponível mas precisa ativar · — não se aplica.

### E0.12 — Cross-references finais

- **ADRs** que governam esta arquitetura: `lia-agent-system/ARCHITECTURE.md`
  - ADR-001 Repository Pattern · ADR-008 Response Envelope · ADR-015 Tool Registry hardening · ADR-017 Observability paths · ADR-019 Domain-resolver observability · ADR-020 Intent-routed wizards
- **Capacidades reais vs prompts**: relatório de alinhamento `lia-agent-system/RELATORIO_CAPACIDADES_PROMPTS_LIA.md` (vence em caso de conflito com este doc)
- **Manifest de plataforma** (capabilities expostas para o frontend): `lia-agent-system/app/shared/platform_manifest.py`
- **Frontend ↔ backend**: `lia-agent-system/FRONTEND_INTEGRATION.md` + `lia-agent-system/RAILS_API_INTEGRATION.md`

> **Próximas etapas (E1–E9) — como ler.** A partir daqui, cada etapa Ex assume os componentes acima como dado. Quando uma etapa cita "CascadedRouter", "FairnessGuard L1+L2+L3", "PII Masking", "AuditTrail" ou um agente específico (Ag.0–Ag.8), volte para E0 para ver o **arquivo canônico**, o **status real** e a **posição no pipeline**. As **SEÇÕES TRANSVERSAIS** (Governança, Compliance, Inteligência, LGPD) detalham os contratos de cada componente — E0 é o índice.

---

## E0.5 — ONBOARDING PROATIVO + CONFIGURAÇÕES 100% CONECTADAS — 7 ACTIONS

> **Objetivo.** Garantir que toda configuração da empresa (perfil, cultura, tech stack, benefícios, workforce, análise de site, processamento de documento) seja executável **tanto pelo painel `/configuracoes` quanto pela LIA via chat**, com FairnessGuard + AuditTrail + tier validation aplicados de forma idêntica nos dois caminhos. Sem duplicação de lógica de escrita: o domínio `company_settings` delega 100% para as tools canônicas em `agents/company_tool_registry.py`.

### A. Catálogo das 7 actions canônicas

Domain: `lia-agent-system/app/domains/company_settings/domain.py` (`CompanySettingsDomain`).

| Action ID                | Tool delegada (registry)              | Section UI                | Tier de aprovação                |
| ------------------------ | ------------------------------------- | ------------------------- | -------------------------------- |
| `configure_profile`      | `_wrap_save_company_section('profile')` | Minha Empresa › Perfil    | TIER 1 para `cnpj`/`name` pós-setup |
| `configure_culture`      | `_wrap_save_company_section('culture')` | Minha Empresa › Cultura   | TIER 2 (humano + audit)          |
| `configure_tech_stack`   | `_wrap_save_company_section('culture')` | Minha Empresa › Tech      | TIER 2                           |
| `configure_benefits`     | `_wrap_save_company_benefits` (tabela dedicada `company_benefits`, modes `append`/`replace`) | Minha Empresa › Benefícios | TIER 2 + FairnessGuard L1 |
| `configure_workforce`    | `_wrap_import_workforce_plan`         | Minha Empresa › Workforce | TIER 2 (audit detalhado)         |
| `analyze_website`        | `CompanyScraperService.scrape_website` direto + SSRF guard (gravação via UI/TIER 3) | Minha Empresa (CTA topo)  | TIER 3 — humano confirma antes de gravar |
| `process_document`       | `_wrap_process_uploaded_document`      | Minha Empresa (upload)    | TIER 3 — `requires_human_approval=True` |

**Princípio canônico (anti-duplicação).** Os handlers do `domain.py` **não** instanciam serviços de gravação dos campos cobertos por `_wrap_save_company_section`. Cada `_handle_configure_{profile,culture,tech_stack}` chama `_delegate_section_write`, que invoca a tool canônica do registry — assim FairnessGuard L1+L2+L3, PII Masking, AuditTrail e tier validation são **idênticos** em chat e UI.

**Exceções declaradas (sem silent fallback).**
- `configure_benefits` — usa **tool dedicada** `_wrap_save_company_benefits` (a tabela `company_benefits` não pertence a `company_culture_profiles`). Aceita `benefits=[strings|objetos]` + `mode='append'|'replace'`; aplica FairnessGuard L1 em `name`/`description`, escopa por `company_id`, registra audit (`save_benefits` com inserted/deactivated/names). Se o usuário não envia lista, handler responde `clarification_response` com `navigation_hint.subsection="beneficios"` (em vez de gravar parcial).
- `analyze_website` — usa `CompanyScraperService.scrape_website` direto **só para leitura**, com SSRF guard (`_is_safe_public_url`) bloqueando endereços internos. Nenhuma gravação acontece neste handler — o usuário aprova os campos extraídos antes que `_wrap_save_company_section` seja chamado num turn subsequente (TIER 3 — humano confirma).

### B. Pipeline conversacional (chat → action → painel)

```
Usuário (chat) ──► CascadedRouter (E0 §A)
                  └─ FastRouter (regex) → company_settings  (precisão pt-BR)
                  └─ LLM Router (gpt-5-mini) → fallback
                  ──► CompanySettingsDomain.execute_action(action_id, params, ctx)
                       ├─ params completos? → _wrap_save_company_section(...)
                       │                       ├─ FairnessGuard L1+L2+L3
                       │                       ├─ PII Masking + Audit (LGPD Art. 37)
                       │                       └─ commit no `CompanyConfigurationService`
                       └─ params incompletos? → DomainResponse.clarification_response(...)
                                                  (LIA pergunta os campos faltantes)
                       ──► resposta inclui `navigation_hint: { page, section }`
Frontend (chat) ──► dispatch CustomEvent('lia:settings-action', { actionId, section, field })
                    + dispatch CustomEvent('settings-open-tab', section)
SettingsPageEnhanced ──► listener abre a tab + scrolla até `[data-field=...]`
                          + flag `recentlyHighlighted` por 3s (highlight visual)
```

**Hook canônico no frontend**: `plataforma-lia/src/hooks/settings/use-settings-conversational.ts` exporta `useSettingsConversational()` com `triggerAction(actionId, opts)` que:
1. Dispara `lia:settings-action` (consumido por `settings-page-enhanced.tsx`).
2. Dispara `settings-open-tab` (compatibilidade reversa).
3. Opcionalmente envia prompt para o chat via `lia:prefill-message` (evento canônico já consumido pelo `UnifiedChat`/`InlineChatBridge`).

### C. Onboarding proativo (Setup Intro → Chat de Onboarding)

Antes (bug coberto até #711): `SetupIntroModal.handleStartWizard` apenas fechava o modal e devolvia o usuário a um dashboard vazio — a intenção declarada de "configurar agora" era engolida.

Agora (`onboarding-controller.tsx` §`handleStartWizard`):
- Fecha o modal **e** redireciona para `/onboarding`, que renderiza `OnboardingChatPage`.
- A `OnboardingChatPage` instancia o chat conectado ao `CompanySettingsReActAgent` e pode invocar as 7 actions iterativamente (Q&A guiado).
- A finalização do chat zera `canReplayOnboarding` e setta `setupComplete=true` no store.

### D. Banner persistente (`SetupProgressBanner`)

Componente: `plataforma-lia/src/components/onboarding/SetupProgressBanner.tsx`.

- **Quando aparece**: em qualquer página do dashboard exceto Chat LIA e Configurações, **enquanto** o `overall progress` retornado por `GET /api/backend-proxy/settings/progress/` for **< 80%**.
- **Quando desaparece**: ao atingir ≥ 80% **ou** quando o usuário clica `X` (gravado em `localStorage['lia.setup-banner.dismissed-at']` por 24h).
- **Acessibilidade**: `role="status"`, `aria-live="polite"`, contraste AA, `motion-reduce:transition-none`, dark/light tokens LIA DS v4.2.1.
- **CTA**: link direto para `/onboarding` (mesma rota do `handleStartWizard`).

### E. CTA proativa "Analisar nosso site" (Minha Empresa Hub)

Em `MinhaEmpresaHub.tsx`, ao lado do botão de refresh, há um botão `[data-testid="analyze-website-cta"]` que chama `triggerAction('analyze_website', { prompt: '...' })`. Esse fluxo:
1. Abre o chat lateral com o prompt pré-preenchido.
2. Roda `_wrap_analyze_company_website` (Apify Crawler) com o `website_url` do perfil.
3. Devolve `data.suggested_fields` ao chat — usuário aprova **antes** que `_wrap_save_company_section` seja chamado (TIER 3).

### F. Pipeline de `process_document`

Aceita dois caminhos:
- `document_text` (pré-extraído).
- `document_b64` + `document_format` (`pdf` via `pypdf`, `docx` via `python-docx`, `txt` UTF-8).

**Two-phase obrigatório (LGPD Art. 8 — consentimento informado):**

- **Fase 1 (extract)**: handler retorna `requires_human_approval: True` + `expected_fields` no `data`. Nada é gravado.
- **Fase 2 (persist)**: chat re-chama `process_document` com `confirm: true` + `confirmed_fields={...}`. Handler particiona campos por seção (`profile`/`culture`) usando `_SECTION_FIELD_HINTS` e delega para `_wrap_save_company_section` por seção. Audit extra `persist_document_extraction` é emitido com `user_id`, `sections` gravadas e `fields_count`.
- **Tenant authority**: ambas as fases passam por `_resolve_tenant` — `params.company_id` divergente do `context.tenant_id` é bloqueado com `reason=tenant_mismatch` e auditado (defesa em profundidade — IDOR guard).

### G. Inegociáveis (anti-regressão)

1. **Delegar, nunca duplicar**: qualquer write em settings via chat **deve** passar por uma tool em `company_tool_registry.py`. PRs novos que instanciem services de gravação direto no domínio devem ser bloqueados em code review.
2. **Sem fallback silencioso**: se a tool falha, `DomainResponse.error_response` carrega a mensagem real — nunca um "feito!" mockado.
3. **Clarification-first**: handler sem dados suficientes responde `clarification_response`, jamais grava parcial.
4. **TIER 1 pós-setup**: alterações de `cnpj` e `name` exigem `confirmed=true` + `is_admin=true` mesmo via chat (validado dentro do `_wrap_save_company_field`).
5. **AuditTrail obrigatório**: todo write registra `actor`, `before`, `after`, `tier`, `source=chat|ui` (gravado pela tool, não pelo handler).
6. **Tenant authority — IDOR guard**: `_resolve_tenant(action_id, params, context)` é a única fonte de verdade do `company_id` em writes. `params.company_id` é input não-confiável: se diferente do `context.tenant_id` autenticado, o handler bloqueia com `reason=tenant_mismatch`, emite warning e não chama nenhuma tool. Cobertura por testes parametrizados nas 6 actions de write.

### J. Orquestração 7-actions e sync bidirecional UI↔chat

**Frontend (Task #712):**

- `OnboardingActionOrchestrator` (`components/onboarding/OnboardingActionOrchestrator.tsx`) — sidebar mostrada em `/[locale]/onboarding`. Renderiza state machine de 7 passos (perfil → cultura → tech → benefícios → workforce → website → documento) com `[Começar] [Pular] [Voltar]`. Persistência em `localStorage` (`lia:onboarding-712:v1`) + `PATCH /api/backend-proxy/onboarding/progress` por step. Cada `Começar` dispara `triggerAction(actionId, prompt)` (abre aba certa via `lia:settings-action` + escreve no chat via `lia:prefill-message`). Cada step avança ao receber `lia:settings-success` com o `actionId` correspondente.
- `SettingsSyncBroadcaster` (`components/settings/SettingsSyncBroadcaster.tsx`) — wrapper instalado uma vez no app shell que intercepta `fetch` e detecta gravações bem-sucedidas em `/api/backend-proxy/company/{profile,culture-profile,tech-stack,benefits,hiring-policies}` e `/api/backend-proxy/workforce` (POST/PUT/PATCH 2xx). Emite dois eventos:
  - `lia:settings-success` (consumido pelo orchestrator para avançar o step).
  - `lia:settings-updated` (consumido pelo `LiaFloatProvider` que injeta uma "system note" silenciosa no histórico do chat: `[contexto] Configurações atualizadas via UI: <section> (<method>)`, com `metadata.system=true, source=settings-sync, silent=true`).
- Resultado: usuário pode editar perfil/cultura/benefícios pela UI ou pelo chat e os dois lados convergem na próxima fala da LIA — sem polling, sem refetch manual.

### H. Mapa de testes mínimos

- `tests/unit/test_company_settings_actions.py` (Task #712): cada uma das 7 actions cobre `success`, `clarification` (sem dados) e `error` (`company_id` ausente).
- `tests/unit/test_company_settings_routing.py` (#320, já existia): garante que prompts pt-BR caem em `company_settings`.
- E2E (futuro): o fluxo "chat → action → tab abre + campo destacado" deve virar smoke do Playwright na #714.

### I. Status

- Backend domain handlers: **OK** (commit Task #712 + fix code-review).
- Tools canônicas: **OK** (já existiam, agora consumidas pelo domain via `_delegate_section_write`).
- `configure_benefits`: **OK** — write real via `_wrap_save_company_benefits` em `company_benefits` (FairnessGuard L1 + Audit + tenant scope; modes append/replace).
- `analyze_website`: **OK** (scrape direto + SSRF guard, gravação só após aprovação humana).
- Hook + bridge frontend: **OK** (`use-settings-conversational.ts` dispara `lia:settings-action` + `lia:prefill-message`).
- CTA analyze_website: **OK** (`MinhaEmpresaHub`).
- Banner persistente: **OK** (`SetupProgressBanner` no `DashboardApp`).
- Rota onboarding: **OK** (`/[locale]/onboarding/page.tsx` renderiza `OnboardingChatPage` + `UnifiedChat`).
- Testes unitários: **OK** (21/21 em `tests/unit/test_company_settings_actions.py`, cobre clarification + error + success por action).
- Doc canônico: **OK** (este capítulo, alinhado ao código pós-review).

---

## E1 — LOGIN — 4 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Login (auth) — 4 STEPS                                       │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/v1/auth/login
    Body: { "email": "user@company.com", "password": "secret" }
    Request logado automaticamente via middleware (X-Request-ID)

 2  AuthService autentica + gera JWT
    Valida email/password via bcrypt (has_secure_password)
    Gera access_token (JWT, 1800s) + refresh_token
    Valida is_active=True (dependency: get_current_active_user)
    WorkOS SSO disponível como alternativa (rotas /auth/workos)
    CircuitBreaker: circuit "workos" (failure_threshold=5, recovery=30s)

 3  RateLimitMiddleware protege contra brute-force
    Redis-backed sliding window (por IP + email)
    Fallback in-memory se Redis indisponível
    Prometheus: login_attempts_total counter

 4  Resposta ao recrutador
    TokenResponse: { access_token, refresh_token, token_type: "bearer", expires_in: 1800 }
    Frontend armazena token via useCookie('auth_token')
    Redireciona para /user/dashboard

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E1)                                          │
│  1. RateLimitMiddleware — sliding window por IP + email ●                     │
│  2. PII Masking — logs de login mascarados (PIIMaskingFilter global) ●        │
│  3. CircuitBreaker — circuit "workos" para SSO ●                              │
│  4. Audit Trail — login events ◐ (código existe, precisa ativar em auth.py)  │
│  5. LGPD — JWT stateless, sem cookies de sessão ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E2 — EDITAR/CRIAR VAGA — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Edição/Criação de Vaga (job_management) — 8 STEPS            │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa POST /api/v1/job-vacancies (criar) ou
    PUT /api/v1/job-vacancies/{vacancy_id} (editar)
    Body: { title, description, department, seniority_level, employment_type,
            work_model, location_city, salary_min, salary_max, required_skills }
    Authorization: Bearer <jwt_token>
    Se "Gerar JD" acionado: POST /api/v1/briefing/generate-jd

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = job_management
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy carregado por company_id
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    16 capabilities injetadas automaticamente:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy (FULL variant) | WorkingMemory | CircuitBreaker
    LearningLoop | TemplateLearning | PredictiveAnalytics
    SemanticSearch | ConversationMemory

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Regex ~350 patterns em 13 categorias
       Bloqueia requisitos discriminatórios no JD (gênero, idade, etnia, religião,
       deficiência, estado civil, orientação sexual, gravidez, aparência,
       classe social, política, nacionalidade, saúde)
    🔒 L2 Implicit: Detecta termos proxy enviesados ("dinâmico" → age proxy,
       "boa aparência" → appearance proxy) — alerta (log only)
    Input + Output check via check_fairness em jd_generation.py

 5  PII Masking remove dados sensíveis
    4 camadas pré-LLM: CPF → [CPF_MASKED]
    nome → [NAME_1] | endereço → [ADDR_MASKED]
    Campos sensíveis strip via strip_pii_for_llm_prompt
    O LLM NUNCA vê dados pessoais reais

 6  JobDescriptionGeneratorService processa (Claude LLM)
    LLM recebe dados mascarados da vaga
    Gera JD estruturada em markdown:
    → Seções: Sobre, Responsabilidades, Requisitos, Benefícios, Diversidade
    → SEO title + tags
    Anti-sycophancy block (FULL variant) no system prompt
    CircuitBreaker: circuit "anthropic" (failure_threshold=5, recovery=30s)
    🧠 SemanticSearch expande skills sugeridas (Gemini 768-dim)
    🧠 PredictiveAnalytics: predict_time_to_fill, predict_optimal_salary

 7  AuditTrail registra decisão
    🔒 audit_service.log_decision ativo em jd_generation.py
    Registro: LLM input mascarado, output gerado, FairnessGuard results
    Append-only, retenção 730-1825 dias (SOX)
    🧠 LearningLoop captura edições do wizard (salary, skills, benefits)
    🧠 TemplateLearning: após 3 vagas similares, gera template automático

 8  Resposta ao recrutador (PII demasked)
    JD gerada com dados restaurados (nomes, endereços reais)
    FairnessGuard warnings incluídos (se houver L2 alerts)
    Frontend renderiza JD no modal de edição
    Dados persistidos via save_job_draft

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E2)                                          │
│  1. FairnessGuard L1/L2 — input+output check no JD ●                        │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. AntiSycophancy FULL — verificação de premissas ●                         │
│  4. CircuitBreaker — circuit "anthropic" ●                                   │
│  5. AuditTrail — log de geração de JD ● (edições manuais ◐)                │
│  6. LearningLoop — captura silenciosa de edições ●                           │
│  7. TemplateLearning — auto-template após 3 vagas similares ●               │
│  8. PredictiveAnalytics — predict TTF + salary ●                             │
│  9. SemanticSearch — expansão de skills ●                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E3 — CONFIGURAR ROTEIRO WSI — 9 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Configuração de Roteiro WSI (cv_screening) — 9 STEPS         │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa TAB CONFIGURAÇÕES → SEÇÃO PERGUNTAS Triagem
    POST /api/v1/wsi/generate-questions
    Body: { job_id, mode: "complete"|"compact", job_description, requirements }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker
    LearningLoop | ConversationMemory | SemanticSearch

 4  JobDescriptionGeneratorService (se JD ausente)
    Se o JD não existe ou precisa ajuste, gera/melhora antes
    Mesmo fluxo da E2 (Claude LLM, FG L1/L2, PII Masking)
    Resultado: JD completa como base para perguntas WSI

 5  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Valida cada pergunta candidata contra ~350 patterns
    🔒 L2 Implicit: Detecta perguntas com proxy bias
    check_fairness per-question em wsi_questions.py
    Bloqueia perguntas que violem 13 categorias protegidas

 6  PII Masking + strip do JD
    strip_pii_for_llm_prompt aplica 4 camadas
    JD enviado ao LLM sem dados identificáveis

 7  WSIQuestionGenerator processa (Gemini LLM)
    Recebe JD mascarada + requisitos da vaga
    Gera perguntas WSI em blocos estruturados:
    → Bloco 2: Técnico (Bloom 1-6, Dreyfus 1-5)
    → Bloco 3: Comportamental (Big Five traits)
    → Bloco 4: Situacional (cenários práticos)
    → Bloco 5: Cultural Fit
    Cada WSIQuestionBlock: block_id, block_type, question, competency,
    bloom_level, dreyfus_level, big_five_trait, max_score, trait_weight
    🧠 SemanticSearch expande competências sugeridas

 8  FactChecker verifica APÓS o LLM
    🔒 4 tipos de verificação:
    → Experiência declarada: claims vs dados de contexto
    → Certificações: validade técnica
    → Período na empresa: coerência temporal
    → Habilidades técnicas: relevância para a vaga
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default em DomainWorkflow._post_check

 9  AuditTrail registra + Resposta ao consultor
    🔒 audit_service.log_decision ativo em wsi_questions.py
    Registro: perguntas geradas, FG results, fact-check flags
    Append-only, retenção SOX
    🧠 LearningLoop captura edições nas perguntas
    Resposta: lista de perguntas WSI para revisão/ajuste no modal

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E3)                                          │
│  1. FairnessGuard L1/L2 — per-question check ●                              │
│  2. PII Masking — 4 camadas pré-LLM ●                                       │
│  3. FactChecker — 4 tipos de verificação pós-LLM ●                          │
│  4. AuditTrail — log de geração de roteiro WSI ●                             │
│  5. LearningLoop — captura edições de perguntas ●                            │
│  6. SemanticSearch — expansão de competências ●                              │
│  7. ConversationMemory — tracking da vaga ativa ●                            │
│  STATUS: Compliance completo para esta etapa ✓                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E4 — BUSCAR CANDIDATOS (Funil de Talentos) — 10 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Busca de Candidatos (sourcing) — 10 STEPS                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor acessa Funil de Talentos
    GET /api/v1/candidates/search?query=...&skills=...&location=...
    Modos de busca: IA Natural | Boolean | Perfil Similar |
                    Job Description | Archetypes
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia via CascadedRouter (6 tiers)
    Tier 0: MemoryResolver — resolve pronomes ("ele", "essa vaga")
    Tier 1: LRU in-process — hash MD5, O(1)
    Tier 2: Redis hash cache — distribuído
    Tier 3: VectorSemanticCache — pgvector, cosine ≥ 0.92
    Tier 4: FastRouter — regex/keyword, confiança ≥ 0.7
    Tier 5: LLM Cascade — Gemini (produção)
    Domínio destino = sourcing
    GuardrailRepository (3 níveis) + HiringPolicy carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities completas injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy OPERATIONAL | WorkingMemory | LongTermMemory
    CircuitBreaker | LearningLoop | Calibration
    ScoreNormalization | RoutingAdaptativo | ModelDrift
    PredictiveAnalytics | ConversationMemory | SemanticSearch

 4  FairnessGuard filtra ANTES do LLM
    🔒 L1 Explicit: Bloqueia buscas discriminatórias (MainOrchestrator L35-47)
    🔒 L2 Implicit: Alerta proxy terms na busca (MainOrchestrator L48-62)
    🔒 L3 Semantic (setor-condicionada): Análise semântica profunda
       Setores com L3 ativo: tech, financeiro, saude, rpo
       check_with_sector() ativo em sourcing_agent, RAG pipeline
    _LEARNING_PROTECTED_FIELDS bloqueia learning de: gender, age, ethnicity,
    marital_status, photo, institution, address, religion, disability, cv_gaps

 5  PII Masking + anonimização
    4 camadas pré-LLM para candidatos
    strip_pii_for_llm_prompt em todos os perfis
    ToonService anonymize=True para modo anônimo (LGPD)

 6  Motor de Busca multi-tier
    Busca 2-tier: Local (PostgreSQL, gratuito) → Global (Pearch AI 190M+, pago)
    Elasticsearch + PGVector + WRF (Weighted Rank Fusion):
    → ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)
    → WRF Dynamic K (ajuste por nível de qualificação)
    → LLM Job Classification para otimização de K values
    🧠 SemanticSearch: expansão semântica de skills/títulos/indústrias
       (Gemini text-embedding-004, 768-dim, Redis cache)
    CircuitBreaker: circuit "pearch" (failure_threshold=3, recovery=60s)

 7  Ag.2 SourcingReActAgent processa
    ReAct loop: max_iterations=5, max_tool_calls=3
    Tools: search_candidates, analyze_profile, score_candidate,
           compare_candidates, rank_candidates, generate_message
    WorkingMemory + LongTermMemory ativos
    🧠 RoutingAdaptativo: confidence multipliers 0.8x-1.2x por domínio

 8  FactChecker + ConfidenceNode + BiasAuditSnapshot
    🔒 FactChecker: valida claims nas análises LIA
       enable_fact_checker=True por default em DomainWorkflow._post_check
    🔒 ConfidenceNode: score calibrado para comparabilidade real
       confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 BiasAuditSnapshot: Four-Fifths Rule
       Detecta se taxa de aprovação de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback explícito/implícito sobre scores

 9  AuditTrail + Learning
    🔒 Audit: log de buscas + scores ◐ (precisa ativar em candidates.py)
    🧠 LearningLoop: captura accept/modify/reject de candidatos
    🧠 ModelDrift: monitora score_drift + approval_drift (7-day window)
    🧠 PredictiveAnalytics: predict_skill_success integrado

 10 Resposta ao recrutador (PII demasked)
    Tabela de candidatos: 10 por vez + "Carregar +10"
    Preview inline com 4 tabs: Perfil | Atividades | Arquivos | Pareceres
    Like/Dislike feedback por candidato (otimiza busca)
    Prompt expandido da LIA (análise, comparação, ranking)
    Dados PII restaurados na response final

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E4)                                          │
│  1. FairnessGuard L1/L2/L3 — busca + análise + response ●                   │
│  2. PII Masking — 4 camadas + ToonService anonymize ●                        │
│  3. FactChecker — valida claims pós-LLM ●                                    │
│  4. BiasAuditSnapshot — Four-Fifths Rule ●                                   │
│  5. ConfidenceNode — calibração de score ●                                   │
│  6. ScoreNormalization — difficulty_coefficient ●                             │
│  7. AuditTrail — buscas + scores ◐ (precisa ativar)                         │
│  8. LearningLoop — captura silenciosa ●                                      │
│  9. Calibration — feedback dual (explícito + implícito) ●                    │
│ 10. ModelDrift — 4 dimensões monitoradas ●                                   │
│ 11. SemanticSearch — expansão 768-dim ●                                      │
│ 12. RoutingAdaptativo — confidence multipliers ●                             │
│ 13. PredictiveAnalytics — predict_skill_success ●                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E5 — APROVAR MAPEADOS (Gate 1) — 9 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 1 (pipeline + kanban) — 9 STEPS               │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor no Kanban board move candidato(s)
    POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage, to_stage, action: "approve"|"reject",
            reason, job_id }
    Aprovação INDIVIDUAL ou EM MASSA (max 100)
    Drag-and-drop manual para qualquer coluna
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban
    🔒 PolicyEngine: ALPHA1_SECTOR_RULES por setor
       Autonomy levels + HITL thresholds
       Determina se ação precisa confirmação humana
    SmartTransitionModal: etapas críticas pedem confirmação
    GuardrailRepository (3 níveis) carregado

 3  EnhancedAgentMixin._setup_enhanced()
    Capabilities injetadas:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | ConfidenceNode | BiasAuditSnapshot
    AntiSycophancy OPERATIONAL | WorkingMemory
    CircuitBreaker | LearningLoop | Calibration
    RoutingAdaptativo | ModelDrift | ConversationMemory

 4  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    check_rejection_fairness: motivo de rejeição analisado contra
    13 categorias protegidas
    Se motivo discriminatório → BLOCK + alerta ao consultor

 5  PipelineTransitionAgent interpreta contexto
    LangGraph ReAct (invocação direta, não via registry)
    POST /api/v1/pipeline/interpret-context
    Tools: validate_transition, get_candidate_profile,
           get_candidate_wsi_scores, suggest_sub_status,
           check_rejection_fairness, extract_preferences
    20 tools disponíveis no registry

 6  LGPD: Consentimento antes de contato
    🔒 CandidateChannelSelector.select_channels verifica:
       → LGPDConsent (consentimento registrado)
       → CandidateOptOut (opt-out por canal)
    WhatsApp: estado AWAITING_CONSENT com mensagem explícita
    Sem consentimento → contato bloqueado

 7  PolicyEngine: Escalation + HITL
    🔒 trigger_escalation quando AI confidence < threshold
    Threshold configurável por setor (ALPHA1_SECTOR_RULES)
    Se HITL necessário → pausa para decisão humana
    Notification: Bell + Teams

 8  AuditTrail + Learning
    🔒 Audit: log de aprovações/rejeições + overrides ◐ (precisa ativar)
    🧠 LearningLoop: captura decisões aceitar/rejeitar/modificar suggestion
    🧠 Calibration: implicit feedback (avançar low-score = sinal)
    🧠 ModelDrift: trigger se approval_drift > 10 p.p.
    🧠 RoutingAdaptativo: correções de rota alimentam ajustes

 9  Resposta + Disparo de próxima etapa
    Aprovados → LIA dispara contato (E6)
    Reprovados → LIA envia feedback (E9B)
    ⚡ Inscritos via web BYPASS Gate 1 → triagem automática
    Kanban board atualizado em real-time (ActionCable/WebSocket)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E5)                                          │
│  1. FairnessGuard — auto-check em rejeções + FG L3 pré-check ●              │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — consent check antes de contato ●                                  │
│  4. PII Masking — ativo globalmente ●                                        │
│  5. Escalation — trigger quando AI confidence < threshold ●                  │
│  6. AuditTrail — aprovações/rejeições ◐ (precisa ativar)                    │
│  7. LearningLoop — captura decisões ●                                        │
│  8. Calibration — implicit feedback ●                                        │
│  9. ModelDrift — approval_drift monitoring ●                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E6 — CONTATO VIA EMAIL + FOLLOW-UP — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Contato Email + Follow-up (communication) — 8 STEPS          │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Ag.0 MainOrchestrator dispara contato após Gate 1
    POST /api/v1/communications/send
    Body: { candidate_id, job_id, channel: "email", template_id,
            personalization: { candidate_name, job_title, screening_link } }
    Contato primário: SEMPRE email

 2  DomainOrchestrator roteia
    Domínio = communication
    GuardrailRepository carregado
    Rate limiting verificado: RateLimitRule sliding window por empresa/dia
    CircuitBreaker: circuits "sendgrid" + "resend" (critical tier)

 3  CommunicationReActAgent (Ag.7) processa
    ReAct loop: max_iterations=5
    Tools registradas (communication_tool_registry.py):
    → send_email, send_whatsapp, get_communication_history,
      schedule_message, check_rate_limit
    Legacy tools (communication_tools.py): send_feedback, send_bulk_email

 4  PII Masking em logs
    🔒 PIIMaskingFilter: emails não logam dados pessoais
    Conteúdo do email NÃO mascarado (é para o candidato)
    Logs de envio: PII stripped

 5  LGPD: Opt-out + Consent
    🔒 Opt-out link incluído no email (obrigatório)
    communication_optout.py: HMAC-signed tokens
    ConsentEvent auditável: registro de consentimento/revogação
    Se opt-out registrado → canal bloqueado para futuro

 6  Email enviado com 2 opções
    A) Link para triagem via CHAT WEB (canal principal)
    B) Solicita nº celular → WhatsApp (canal secundário)
    🧠 A/B Testing: variantes de template de email
       seed_email_ab_tests cria 3 experimentos no startup
    🧠 TemplateLearning: templates de email aprendidos

 7  Follow-up automático (7 dias)
    Se candidato NÃO abre/clica email:
    → Re-envio automático a cada 24h por 7 dias consecutivos
    → Após 7 dias sem resposta → status "sem_resposta"
    → Consultor notificado (Teams)
    Celery Beat schedule para verificação periódica

 8  AuditTrail + Response
    🔒 Audit: log de envios + opens + clicks ◐ (precisa ativar)
    🧠 ConversationMemory: tracking de candidatos contatados
    Resposta ao consultor: confirmação de envio + tracking status

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E6)                                          │
│  1. LGPD — opt-out link obrigatório + HMAC-signed tokens ●                  │
│  2. PII Masking — logs mascarados ●                                          │
│  3. RateLimiting — sliding window por empresa/dia ●                          │
│  4. CircuitBreaker — circuits "sendgrid" + "resend" ●                        │
│  5. A/B Testing — variantes de template ●                                    │
│  6. TemplateLearning — templates aprendidos ●                                │
│  7. AuditTrail — envios/opens/clicks ◐ (precisa ativar)                     │
│  8. Follow-up automático — 7 dias, Celery Beat ●                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7 — TRIAGEM WSI (cv_screening + WSI) — 11 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem (cv_screening + WSI) — 11 STEPS                      │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Frontend (Next.js 15) envia POST /api/chat
    Request logado via middleware (X-Request-ID auto-gerado)
    Canais: Chat web (link do email) | WhatsApp | Voz (Twilio/OpenMic.ai)
    Candidato clica link do email → página /triagem/[token]

 2  DomainOrchestrator roteia + GuardrailCheck
    Identifica domínio = cv_screening
    GuardrailRepository (3 níveis): global → tenant → domain
    HiringPolicy (per-tenant) carregado
    PromptInjectionGuard ativado

 3  EnhancedAgentMixin._setup_enhanced()
    16 capabilities injetadas automaticamente:
    FairnessGuard (3 layers) | PII Masking (4 layers)
    AuditTrail | BiasAuditSnapshot | ConfidenceNode
    AntiSycophancy | WorkingMemory | CircuitBreaker
    LearningLoop | Calibration | ScoreNormalization | ModelDrift

 4  FairnessGuard filtra ANTES do LLM
    3 camadas: (1) Regex → bloqueia "rejeitar por idade"
    (2) Implícito → detecta vieses indiretos ("bairro nobre")
    (3) LLM → análise semântica de fairness
    check_with_sector() ativo em rubric_evaluation.py
    Setores com L3: tech, financeiro, saude, rpo

 5  PII Masking remove dados sensíveis
    4 camadas pré-LLM: CPF → [CPF_MASKED]
    nome → [NAME_1] | endereço → [ADDR_MASKED]
    O LLM NUNCA vê dados pessoais reais

 6  WSI Interview Graph processa (1.141L)
    8 stages: INIT → LOAD → GENERATE → AWAIT →
    VALIDATE → SCORE → ADVANCE → COMPLETE
    Bloom (1-6) + Dreyfus (1-5) + Big Five (OCEAN)
    PostgresSaver checkpoint — sessões de 30-120 min via WebSocket
    interview_level: "quick" | "standard" | "full"
    HITL: interrupt_before=["lg_generate_feedback"]

 7  Gemini/Claude processa (dados mascarados)
    LLM recebe [CPF_MASKED], [NAME_1], etc.
    Anti-sycophancy block no system prompt
    CircuitBreaker protege contra falha
    Temperature: 0.3 (LLM_AGENT_TEMPERATURE)

 8  FactChecker verifica APÓS o LLM
    🔒 4 tipos: experiência declarada, certificações,
    período na empresa, habilidades técnicas
    Claim inconsistente → flag para revisão
    enable_fact_checker=True por default

 9  ConfidenceNode calibra + BiasAuditSnapshot
    Score calibrado para comparabilidade real
    confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
    🔒 Four-Fifths Rule — detecta se taxa de aprovação
    de grupo demográfico < 80% de outro
    🧠 ScoreNormalization: ajusta por difficulty_coefficient
    🧠 Calibration: feedback dual sobre scores WSI

 10 AuditTrail registra TUDO (append-only)
    Registro imutável: request, fairness check, PII masks,
    LLM response, fact-check, scores, bias audit
    Retenção: 7 anos (SOX). Não pode ser alterado
    🧠 LearningLoop: captura padrões de resposta por competência
    🧠 ModelDrift: monitora drift em scores WSI (7-day window)

 11 Resposta ao recrutador (PII demasked)
    WSIFinalReport com recomendação + 3 scores
    (tech/behavioral) + wsi_final_score
    Dados PII restaurados na resposta (nunca no audit)
    Recomendação: "aprovado" | "aguardando" | "reprovado"

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7)                                          │
│  1. PII nunca chega ao LLM — 4 camadas de mascaramento pré-LLM ●            │
│  2. FairnessGuard 3 layers — bloqueia vieses explícitos e implícitos ●       │
│  3. BiasAuditSnapshot — Four-Fifths Rule detecta discriminação estatística ● │
│  4. ConfidenceNode — calibra scores para serem comparáveis e significativos ●│
│  5. FactChecker pós-LLM — verifica claims factuais do candidato ●            │
│  6. Audit Trail SOX — registro imutável, 7 anos, append-only ◐              │
│  7. WSI com Bloom+Dreyfus — progressão de dificuldade + cobertura ●          │
│  8. LGPD consent — WelcomeCard com checkbox explícito obrigatório ●          │
│  9. Anti-sycophancy — bloqueia concordância automática ●                     │
│ 10. ScoreNormalization — difficulty_coefficient por versão de roteiro ●       │
│ 11. Voice Analysis — STT Deepgram/Whisper + TTS OpenAI ●                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7A — TRIAGEM ABANDONADA — 5 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Triagem Abandonada (cv_screening) — 5 STEPS                  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Detecção de abandono
    Candidato inicia WSI mas para de responder
    Celery Beat: task "wsi-abandoned-check" roda a cada 4h
    Verifica WSIInterviewState: last_activity_at vs now()
    Progresso parcial SALVO via PostgresSaver checkpoint

 2  1º Lembrete (48h sem atividade)
    Timeout: 48h sem atividade detectado
    Ag.7 CommunicationReActAgent envia lembrete
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)
    Mensagem personalizada com progresso parcial

 3  2º Lembrete (+48h sem retorno)
    96h total sem atividade
    Segundo lembrete automático enviado
    Tom mais urgente, informa deadline

 4  Alerta ao consultor
    Após 2º lembrete sem retorno
    Alerta via Teams ao consultor responsável
    Candidato marcado como "triagem_abandonada"
    Consultor decide: re-engajar ou descartar

 5  Estado final
    Progresso parcial permanece salvo
    Scores parciais disponíveis para consultor
    Candidato pode retomar se consultor re-enviar link
    Audit: abandono registrado com timestamps

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7A)                                         │
│  1. Checkpoint — progresso parcial salvo (PostgresSaver) ●                   │
│  2. Celery Beat — verificação automática a cada 4h ●                         │
│  3. Notification — alerta ao consultor via Teams ●                            │
│  4. LGPD — dados parciais com consentimento original ●                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E7B — FEEDBACK PÓS-TRIAGEM — 4 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback Pós-Triagem (cv_screening) — 4 STEPS                │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Triagem WSI completa
    Ag.4 WSIInterviewGraph atinge stage GENERATE_FEEDBACK
    HITL: interrupt_before=["lg_generate_feedback"]
    Score WSI calculado + recomendação gerada

 2  Feedback gerado ao candidato
    Ag.4 agradece participação
    Dá feedback construtivo sobre performance
    Informa próximos passos do processo
    Canal: mesmo da triagem (chat web, WhatsApp ou voz)

 3  FairnessGuard valida feedback
    🔒 FG L1/L2 em rubric_evaluation.py
    Feedback não pode conter viés ou dados discriminatórios
    PipelineFeedbackTool._remove_score_references: strip scores numéricos
    FairnessGuard sanitiza texto do feedback

 4  Notificação ao consultor
    Alerta via Teams: "Triagem WSI concluída para [candidato]"
    Score WSI + parecer LIA disponíveis na plataforma
    Candidato aguarda decisão Gate 2

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E7B)                                         │
│  1. FairnessGuard — feedback sem viés ●                                      │
│  2. Score stripping — remove scores numéricos do feedback ●                  │
│  3. HITL — interrupt_before para review humano ●                             │
│  4. Notification — alerta ao consultor ●                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E8 — APROVAR/REPROVAR TRIADOS (Gate 2) — 8 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Aprovação Gate 2 (pipeline + kanban + analytics) — 8 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Consultor recebeu alerta Teams (E7B)
    Acessa Kanban board: POST /api/v1/pipeline/transition
    Body: { candidate_ids, from_stage: "triagem", to_stage: "shortlist"|"rejected",
            action, reason, wsi_reviewed: true }
    Revisa score WSI + parecer LIA antes de decidir

 2  DomainOrchestrator + PolicyEngine
    Domínio = pipeline + kanban + analytics
    🔒 PolicyEngine: HITL thresholds por setor (ALPHA1_SECTOR_RULES)
    Determina autonomia: AI pode decidir sozinha vs precisa HITL

 3  FairnessGuard valida rejeições
    🔒 Auto-check em reject_candidate (candidate_tools.py)
    🔒 FG L3 pré-check no PipelineTransitionAgent
    Motivo de rejeição analisado contra 13 categorias
    Se discriminatório → BLOCK + alerta

 4  LGPD: Sanitização de dados para próxima etapa
    🔒 PipelineFeedbackTool._remove_score_references: strip scores numéricos
    🔒 FairnessGuard sanitiza feedback
    🔒 ats_integration_stage_context.py: define campos internos vs ATS
    Dados compartilhados com próxima etapa minimizados

 5  PersonalizedFeedbackService (Ag.7) gera parecer
    Se REPROVADO: gera feedback personalizado para candidato
    FairnessGuard valida feedback antes de enviar
    Embedding do perfil gerado para re-discovery futuro
    _generate_rediscovery_embedding via embedding_service.py

 6  ConfidenceNode + BiasAuditSnapshot
    🔒 Score calibrado para comparabilidade
    🔒 Four-Fifths Rule: verifica equidade estatística Gate 2
    Se anomalia → alerta ao consultor

 7  AuditTrail + Learning
    🔒 Audit: log de aprovação/rejeição Gate 2 ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre decisões Gate 2
    🧠 Calibration: implicit feedback (avançar low-WSI = sinal)
    🧠 ModelDrift: monitora approval_drift Gate 2
    🧠 RoutingAdaptativo: correções entre domínios

 8  Resultado + Disparo
    Aprovados → SHORT LIST → E9A (agendar entrevista)
    Reprovados → E9B (enviar feedback)
    Kanban atualizado em real-time
    🧠 LongTermMemory: episódio salvo para referência futura

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E8)                                          │
│  1. FairnessGuard — auto-check rejeções + FG L3 ●                           │
│  2. PolicyEngine — HITL thresholds por setor ●                               │
│  3. LGPD — data minimization + score stripping ●                             │
│  4. BiasAuditSnapshot — Four-Fifths Rule Gate 2 ●                            │
│  5. AuditTrail — aprovações Gate 2 ◐ (precisa ativar)                       │
│  6. LearningLoop + Calibration + ModelDrift ●                                │
│  7. Embedding — rediscovery de candidatos reprovados ●                       │
│  8. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9A — AGENDAR ENTREVISTA — 7 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Agendamento de Entrevista (interview_scheduling) — 7 STEPS    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request chega ao FastAPI
    Candidato APROVADO no Gate 2 → trigger automático
    POST /api/v1/scheduling/create
    Body: { candidate_id, job_id, interview_type, preferred_dates }
    Authorization: Bearer <jwt_token>

 2  DomainOrchestrator roteia
    Domínio = interview_scheduling
    Ag.6 InterviewGraph ativado
    GuardrailRepository carregado
    CircuitBreaker: circuit "google_calendar" (recovery=60s)

 3  Ag.6 InterviewGraph processa
    LangGraph StateGraph: 6 nós
    Tools: schedule_interview, check_availability,
           reschedule_interview, cancel_interview
    Busca horários disponíveis no Google Calendar
    Se NÃO encontra horário → alerta ao consultor via Teams

 4  LGPD: Data Minimization no ICS
    🔒 SchedulingService.generate_ics_content:
    Apenas dtstart/dtend/summary/location/attendee
    SEM dados sensíveis do candidato no arquivo ICS
    Mínimo necessário para o agendamento funcionar

 5  Comunicação multi-canal
    Email + WhatsApp ao candidato (data/hora + link reunião)
    Ag.7 CommunicationReActAgent envia por ambos canais
    Template personalizado com dados da vaga e entrevistador

 6  AuditTrail + Learning
    🔒 Audit: log de agendamento ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre qualidade da sugestão
    🧠 LongTermMemory: episódio salvo (EnhancedAgentMixin._post_loop_learning)

 7  Resposta ao consultor
    Confirmação de agendamento + detalhes
    Calendar invite enviado a todos os participantes
    Status atualizado no Kanban

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9A)                                         │
│  1. LGPD — data minimization no ICS ●                                        │
│  2. CircuitBreaker — circuit "google_calendar" ●                             │
│  3. PII Masking — ativo globalmente ●                                        │
│  4. AuditTrail — agendamento ◐ (precisa ativar)                             │
│  5. LongTermMemory — episódios salvos ●                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E9B — ENVIAR FEEDBACK (Reprovado) — 6 STEPS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback para Reprovado (communication) — 6 STEPS             │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: Candidato REPROVADO no Gate 2
    Ag.0 MainOrchestrator dispara feedback
    Domínio = communication + cv_screening

 2  PersonalizedFeedbackService (Ag.7) gera feedback
    Analisa perfil + scores WSI + motivo de rejeição
    Gera feedback construtivo e personalizado
    🔒 FairnessGuard L1/L2: valida feedback antes de envio
    PipelineFeedbackTool._remove_score_references: strip scores

 3  PII Masking + FairnessGuard
    🔒 PII: dados pessoais protegidos em logs
    🔒 FG: feedback não contém viés ou discriminação
    Texto sanitizado por FairnessGuard

 4  CommunicationReActAgent envia
    Email (primário) + WhatsApp (se número disponível)
    Template personalizado com feedback construtivo
    🧠 A/B Testing: variantes de template de feedback
    🧠 TemplateLearning: templates aprendidos

 5  Embedding para rediscovery
    🧠 _generate_rediscovery_embedding:
    Gera embedding do perfil (Gemini text-embedding-004, 768-dim)
    Salvo via embedding_cache_service.py
    Permite re-discovery em vagas futuras similares

 6  AuditTrail + Response
    🔒 Audit: log de feedback enviado ◐ (precisa ativar)
    🧠 LearningLoop: feedback sobre qualidade do feedback gerado
    Status final do candidato atualizado no Kanban
    🧠 LongTermMemory: episódio completo salvo

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E9B)                                         │
│  1. FairnessGuard L1/L2 — feedback sem viés ●                                │
│  2. Score stripping — remove scores numéricos ●                              │
│  3. PII Masking — dados protegidos ●                                         │
│  4. A/B Testing — variantes de feedback ●                                    │
│  5. TemplateLearning — templates aprendidos ●                                │
│  6. Embedding — rediscovery futuro ●                                         │
│  7. AuditTrail — feedback ◐ (precisa ativar)                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E10 — PROPOSTA & NEGOCIAÇÃO — 6 STEPS  ⚠ MAJORITARIAMENTE STUB

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Proposta & Negociação — 6 STEPS                              │
│  Status global: STUB (sem domínio dedicado, sem orquestração, sem template)  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: candidato APROVADO em todas as entrevistas (E9A concluída)
    Fonte real hoje: transição manual de pipeline (PipelineTransitionAgent)
    Status: ◐ existe a transição, NÃO existe action `generate_offer`

 2  Geração de carta-proposta
    ⚠ STUB — não há `OfferLetterService` nem template em `report_templates.py`
    Plano (PÓS-MVP): Ag.7 + JobDescriptionGeneratorService como base
    LLM previsto: Claude (mesma stack do JD), com merge de:
      - Compensação (vem de hiring_policy / company_benefits)
      - Benefícios (company_benefits.py — preenchido em E0.5)
      - Cláusulas obrigatórias (legal/compliance — sem catálogo hoje)

 3  Aprovação interna (multi-step approver)
    Fonte real hoje: domínio `approvals` + `company_approvers.py` + `agent_approvals.py`
    Status: ● infra de aprovação existe (ApprovalChainService)
    Falta: workflow específico "offer_approval" cadastrado

 4  Envio ao candidato (multi-canal)
    Reaproveita Ag.7 CommunicationReActAgent
    Email + WhatsApp (templates de proposta = STUB)
    🔒 LGPD: envio só com consent ativo (mesma regra de E6)

 5  Negociação (rodadas de contraproposta)
    ⚠ STUB completo — sem state machine de negociação, sem histórico estruturado
    Workaround atual: thread livre no UnifiedChat (sem tipagem)

 6  Aceite / recusa
    Aceite → trigger E11 (Hire & Pré-Onboarding)
    Recusa → trigger E12 (Arquivamento) + audit + rediscovery embedding

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES PREVISTAS PARA E10 (a implementar)                                 │
│  1. ApprovalChain — chain configurável por valor da proposta ◐               │
│  2. AuditTrail — log completo de cada rodada de negociação ✗                 │
│  3. PII Masking — proteger CPF/RG na carta gerada ●                          │
│  4. ConsentManagement — opt-in já existe (E6) ●                              │
│  5. OfferLetterTemplate — versionado em `report_templates.py` ✗              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E11 — HIRE & PRÉ-ONBOARDING — 5 STEPS  ⚠ STUB (sem integração HRIS)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo Hire & Pré-Onboarding — 5 STEPS                                 │
│  Status global: STUB — não há conector HRIS, não há `OnboardingKitService`   │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: aceite de proposta confirmado (E10 → E11)
    Fonte real: ainda manual (pipeline transition para "hired")

 2  Coleta de documentos do contratado
    ⚠ STUB — não há fluxo "document collection" pós-hire
    Existe `process_document` (E0.5) usado para a EMPRESA, NÃO para o candidato
    Plano: reaproveitar pipeline OCR + `_wrap_save_company_section` adaptado

 3  Sincronização para HRIS / folha de pagamento
    ⚠ STUB completo — `integrations_hub` existe como infra, sem conector HR
    Conectores pendentes: Gupy/Senior/TOTVS RH/SAP SuccessFactors
    Hoje: ats_integration cobre só ATS de recrutamento (Ag.8 ATSIntegrationReActAgent)

 4  Geração de "kit de boas-vindas"
    ⚠ STUB — sem template, sem orquestração
    Plano: Ag.7 envia email com checklist + dados de acesso

 5  Handoff para RH operacional
    Hoje: notificação manual via Teams/email (sem automação)
    Falta: webhook saída para sistema de onboarding do cliente

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES PREVISTAS PARA E11 (a implementar)                                 │
│  1. CircuitBreaker para HRIS connectors ✗                                    │
│  2. PII Masking em logs de sync HR ●                                         │
│  3. Audit do handoff (quem recebeu, quando) ✗                                │
│  4. LGPD: base legal "execução de contrato" para dados sensíveis ◐           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E12 — ARQUIVAMENTO & TALENT POOL — 7 STEPS  ✓ PARCIAL

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo Arquivamento & Talent Pool — 7 STEPS                            │
│  Status global: ● PARCIAL — `talent_pool` domain existe e funciona           │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: candidato encerrado em qualquer etapa
    Fontes: rejeição em Gate 1 (E5), Gate 2 (E8), pós-entrevista (E9B),
            recusa de proposta (E10), perda para concorrente
    Domínio destino: `talent_pool`

 2  Classificação de motivo de saída
    Tool: tag/reason capturado em `talent_pool/actions.py`
    🧠 LearningLoop usa motivo para ajustar score em rediscovery
    🔒 FairnessGuard: motivos não-discriminatórios (regra L2)

 3  Adicionar a Talent Pool
    POST /api/v1/talent_pools/{pool_id}/add_candidates  ●
    TalentPoolDomain.process_intent → `add_candidates_to_pool`
    Pool é tipado: por skill, por sector, por nível, custom
    Capabilities: `lia-agent-system/app/domains/talent_pool/config/capabilities.yaml`

 4  Gerar embedding de rediscovery (rediscovery embedding)
    🧠 _generate_rediscovery_embedding (Gemini text-embedding-004, 768-dim)
    Salvo via embedding_cache_service.py
    Reutilizado por SourcingReActAgent quando vaga similar abrir (E4)

 5  Comunicação ao candidato (opt-in para pool)
    Ag.7 envia email/WhatsApp explicando: "ficou na nossa base"
    🔒 ConsentManagement: candidato pode revogar a qualquer momento
    🔒 LGPD: TTL de retenção configurável (default 24 meses)

 6  Migração para nova vaga (silver medalist)
    POST /api/v1/talent_pools/{pool_id}/move_to_job  ●
    POST /api/v1/talent_pools/{pool_id}/create_job_from_pool  ●
    Service: `silver_medalist_service.py` ●
    Reativa fluxo a partir de E4 (busca) com embedding já calculado

 7  AuditTrail + métricas de pool
    🔒 Audit: log de inclusão / migração ◐
    🧠 Pool stats: tamanho, taxa de rediscovery, time-to-rediscovery

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E12)                                         │
│  1. ConsentManagement — opt-in obrigatório ●                                 │
│  2. FairnessGuard L2 — motivos não-discriminatórios ●                        │
│  3. LGPD TTL — retenção configurável ●                                       │
│  4. PII Masking — ativo globalmente ●                                        │
│  5. Rediscovery embedding — silver medalist ●                                │
│  6. AuditTrail — inclusão em pool ◐ (precisa ativar)                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E13 — PÓS-DECISÃO ANALÍTICO — 6 STEPS  ⚠ STUB (NPS) / PARCIAL (analytics)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo Pós-Decisão Analítico — 6 STEPS                                 │
│  Status global: NPS = STUB | Analytics base = ● parcial                      │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: vaga FECHADA (vai para E14) ou candidato HIRED/REJECTED
    Domínios envolvidos: `analytics`, `journey_mapping`, `recruitment_journey`

 2  Cálculo de Quality of Hire (QoH)
    ⚠ STUB — não há `quality_of_hire_service.py`; métrica não calculada
    Plano: ML model em `services/ml/` (diretório existe, sem modelo de QoH ainda)
    Sinais previstos: tempo de permanência, performance review, NPS gestor

 3  Cálculo de Time-to-Hire e Cost-per-Hire
    ◐ Parcial — `recruiter_metrics.py` e `saas_metrics.py` existem
    Métricas de funil já calculadas (talent_funnel.py)
    Falta: agregação por vaga + custo (custo = STUB)

 4  Coleta de NPS (recrutador & candidato)
    ⚠ STUB completo — não há endpoint NPS, não há schema
    Existe `lia_feedback.py` (thumbs/rating/correction) — mas é feedback
       sobre o AGENTE LIA, não NPS do processo de recrutamento
    Plano: novo domínio `nps` + survey via Ag.7 após T+7 dias do hire

 5  Análise de viés agregada (Bias Audit)
    Endpoint: GET /api/v1/admin/bias_audit  ●
    Dashboard: `admin_bias_audit.py` ● (rota existe; UI = STUB)
    Four-Fifths Rule: implementada em `bias_audit.py`
    Audit dimensions: gender, ethnicity, age, region

 6  Persistência em data lake / warehouse
    ⚠ STUB — sem export programado para BI externo
    Hoje: dados ficam em Postgres (consultados via reports.py)

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS / PREVISTAS NESTE FLUXO (E13)                             │
│  1. Bias Audit — Four-Fifths Rule ● (cálculo) ◐ (UI)                         │
│  2. PII Masking em métricas agregadas ●                                      │
│  3. LGPD: anonimização para analytics ◐                                      │
│  4. NPS pipeline ✗ (STUB)                                                    │
│  5. QoH ML model ✗ (STUB)                                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E14 — CLOSING DA VAGA — 5 STEPS  ⚠ MAJORITARIAMENTE STUB

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo Closing da Vaga — 5 STEPS                                       │
│  Status global: STUB — falta orquestração de "fechamento" formal             │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Trigger: vaga atinge condição de fechamento
    Condições: hired_count >= openings | cancelled by company | expirou SLA
    Hoje: status muda manualmente em `job_management` (sem automação)

 2  Notificar candidatos ainda em processo
    Reaproveita Ag.7 CommunicationReActAgent + template "vaga encerrada"
    ⚠ Template específico = STUB (usa template genérico de feedback)
    🔒 LGPD: comunicação por base legal "interesse legítimo"

 3  Mover candidatos remanescentes para Talent Pool
    Reusa fluxo de E12 (silver medalist)
    ● Funciona via `move_to_job` reverso (mover para pool default)

 4  Lockdown da vaga (read-only)
    ⚠ STUB — não há flag `is_closed` aplicando read-only nos endpoints
    Plano: middleware em `pipeline.py` + `job_management.py`

 5  Gerar relatório executivo de fechamento
    ◐ Parcial — `reports.py` tem `/preview/{report_type}` mas sem template "closing"
    Plano: novo `report_templates.py::closing_report` (Claude)
    Conteúdo previsto: time-to-fill, custos, candidatos avaliados, decisões

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS / PREVISTAS NESTE FLUXO (E14)                             │
│  1. Audit do fechamento (quem, quando, motivo) ✗ (STUB)                      │
│  2. Lockdown / read-only ✗ (STUB)                                            │
│  3. LGPD: comunicação em base legal correta ●                                │
│  4. Talent Pool migration ● (reusa E12)                                      │
│  5. Closing report ✗ (template ausente)                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E15 — REPORTING & DASHBOARDS — 7 STEPS  ✓ PARCIAL

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo Reporting & Dashboards — 7 STEPS                                │
│  Status global: ● PARCIAL — endpoints existem; UI parcial; BI externo = STUB │
└──────────────────────────────────────────────────────────────────────────────┘

 1  HTTP Request: relatório operacional
    POST /api/v1/reports/candidate                ●
    POST /api/v1/reports/comparison               ●
    POST /api/v1/reports/daily-briefing/send      ● (digest/diário)
    POST /api/v1/reports/weekly/send              ●
    POST /api/v1/reports/monthly/send             ●
    GET  /api/v1/reports/preview/{report_type}    ● (HTML/JSON)

 2  Ag.7 + Templates de relatório
    Templates em `app/templates/report_templates.py` ●
    LLM: Claude (mesma stack do JD/feedback)
    🔒 PII Masking ativo no preview HTML

 3  Dashboards executivos (frontend Next.js)
    GET /api/v1/admin/agent_quality_dashboard     ●
    GET /api/v1/agent_quality_dashboard/*         ●
    GET /api/v1/calibration_dashboard_v2          ●
    GET /api/v1/ml_predictions_dashboard          ●
    GET /api/v1/rh_dashboard                      ●
    UI: alguns hubs em `/admin/*` ◐ (parcial)

 4  Métricas SaaS internas (governança)
    Endpoints `saas_metrics.py` ● — MRR, churn, NPS produto, ativação
    Schema dedicado: `app/schemas/saas_metrics.py`
    Uso: WeDO Talent (governança) — não exposto ao cliente final

 5  WSI Reports (qualidade do screening)
    Sub-router: `app/api/v1/wsi/reports.py` ●
    Métricas: distribuição de scores, taxa de aprovação por dimensão Bloom

 6  Export para BI externo
    ⚠ STUB — não há job de export para Snowflake/BigQuery/Looker
    Hoje: clientes consomem via API REST direto (rate-limited)

 7  Alerts proativos
    Endpoint: `alerts.py` ● — define regras
    Engine: `early_warning.py` ● — dispara via webhook/email
    🧠 ProactiveActions (`proactive_actions.py`) — sugere ações no chat

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E15)                                         │
│  1. PII Masking em todo preview ●                                            │
│  2. RBAC por relatório (admin vs recruiter) ●                                │
│  3. Audit de download de relatório ◐                                         │
│  4. LGPD: anonimização em métricas agregadas ◐                               │
│  5. BI export ✗ (STUB)                                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## E16 — FEEDBACK LOOP (CONTÍNUO) — 6 STEPS  ✓ PARCIAL

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LIA — Fluxo de Feedback Loop Contínuo — 6 STEPS                             │
│  Status global: ● PARCIAL — feedback do AGENTE = sólido; do PROCESSO = STUB  │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Captura de feedback do usuário sobre o agente LIA
    POST /api/v1/lia_feedback/thumbs       ●  (👍/👎 por mensagem)
    POST /api/v1/lia_feedback/rating       ●  (1-5 estrelas)
    POST /api/v1/lia_feedback/correction   ●  (correção textual)
    GET  /api/v1/lia_feedback/metrics      ●
    GET  /api/v1/lia_feedback/by-conversation/{session_id}  ●
    POST /api/v1/lia_feedback/regenerate   ●  (regerar resposta após 👎)

 2  Persistência + agregação
    Tabela `lia_feedback` em Postgres
    Agregado por agente / domínio / tier do CascadedRouter

 3  Drift detection
    Service: `golden_drift_monitor.py` ●
    Endpoint: `app/api/v1/drift.py` ●
    Dispara alerta quando taxa de 👎 sobe acima do baseline

 4  Few-shot evolution (auto-improvement)
    Service: `fewshot_evolution_service.py` ●
    Pega correções (correction) e propõe novos few-shots para o prompt
    🔒 Aprovação humana obrigatória (HITL) antes de promover

 5  Suggestion feedback (E2E sourcing/triagem)
    Endpoint: `suggestion_feedback.py` ●
    Captura aceitação/rejeição de sugestões do agente em E4/E5/E8

 6  Feedback do PROCESSO (recrutador & candidato sobre experiência)
    ⚠ STUB — não há captura estruturada de NPS do processo de recrutamento
    (mesma lacuna apontada em E13.4)
    Plano: convergir com pipeline NPS de E13

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES ATIVADAS NESTE FLUXO (E16)                                         │
│  1. PII Masking em correções textuais ●                                      │
│  2. HITL em few-shot evolution ●                                             │
│  3. Drift detection automático ●                                             │
│  4. RBAC: feedback agregado só para admin ●                                  │
│  5. Audit de cada thumbs/rating/correction ◐                                 │
│  6. NPS do processo ✗ (STUB — converge com E13)                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: GOVERNANÇA TÉCNICA

### Policy Engine — Motor de Políticas por Setor

```
Arquivo: app/services/policy_engine_service.py

ALPHA1_SECTOR_RULES — Regras por setor:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Setor        │ Autonomy  │ HITL Threshold │ FG L3  │ Rate Limit │ Escalation│
│──────────────┼───────────┼────────────────┼────────┼────────────┼───────────│
│  tech         │ medium    │ medium         │ ativo  │ standard   │ ativo     │
│  financeiro   │ low       │ high           │ ativo  │ strict     │ ativo     │
│  saude        │ low       │ high           │ ativo  │ strict     │ ativo     │
│  rpo          │ high      │ low            │ ativo  │ relaxed    │ ativo     │
│  varejo       │ medium    │ medium         │ inativo│ standard   │ ativo     │
│  logistica    │ medium    │ medium         │ inativo│ standard   │ ativo     │
└──────────────────────────────────────────────────────────────────────────────┘

Funcionalidades:
- Autonomy Levels: low (tudo precisa HITL) | medium (ações críticas) | high (auto)
- HITL Thresholds: % de confiança abaixo do qual AI escala para humano
- trigger_escalation: quando AI confidence < threshold por setor
- Rate Limiter: sliding window por empresa/dia/endpoint
- Planos: Starter / Pro / Enterprise (tokens mensais, agentes, automações)
  PLAN_LIMITS_ENFORCE=true
```

### CircuitBreaker — 14+1 Circuits

```
Arquivo: app/shared/resilience/circuit_breaker.py

Padrão de 3 Estados: CLOSED → OPEN → HALF_OPEN → CLOSED
  CLOSED: chamadas passam; cada falha incrementa contador
  OPEN: todas rejeitadas com CircuitBreakerError + retry_after
  HALF_OPEN: permite chamadas limitadas para testar recuperação

14 circuits pré-configurados:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Circuit         │ Failures │ Recovery │ Success │ Timeout │ Tier      │
│─────────────────┼──────────┼──────────┼─────────┼─────────┼───────────│
│  anthropic       │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  openai          │ 5        │ 30s      │ 2       │ 60s     │ critical  │
│  gemini          │ 5        │ 30s      │ 2       │ 60s     │ high      │
│  pearch          │ 3        │ 60s      │ 2       │ 30s     │ high      │
│  workos          │ 5        │ 30s      │ 2       │ 15s     │ critical  │
│  merge           │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  google_calendar │ 5        │ 60s      │ 2       │ 30s     │ medium    │
│  gupy            │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  pandape         │ 5        │ 45s      │ 2       │ 30s     │ high      │
│  sendgrid        │ 5        │ 30s      │ 2       │ 30s     │ critical  │
│  resend          │ 5        │ 30s      │ 2       │ 30s     │ high      │
│  iugu            │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  vindi           │ 3        │ 60s      │ 2       │ 30s     │ medium    │
│  llm_react_reason│ 3        │ 60s      │ 2       │ 30s     │ (ReAct)   │
└──────────────────────────────────────────────────────────────────────────────┘

Notificação de Circuit Open (COMP-3):
  Redis dedup: máximo 1 alerta por circuit por hora
  Canais: Bell (in-app) + Teams (webhook)
  Mensagem: "⚡ Circuit Breaker ABERTO: {service_name}"
  Prometheus: circuit_breaker_state (0=closed, 1=half_open, 2=open)

Degraded Mode Responses (14 mensagens PT-BR):
  Cada serviço tem mensagem amigável quando circuit OPEN
  Fallback genérico: "Este serviço está temporariamente indisponível."
```

### PromptInjectionGuard

```
Ativado em todo request que chega ao DomainOrchestrator
Detecta tentativas de prompt injection no input do usuário
Bloqueia execução se injeção detectada
Registra tentativa no audit log
```

### Anti-Sycophancy — 3 Variantes

```
Arquivo: app/shared/prompts/anti_sycophancy_block.py

ANTI_SYCOPHANCY_OPERATIONAL → Talent, Kanban, Jobs Management
  5 regras: não concordar com filtros discriminatórios,
  verificar antes de confirmar, discordância com dados

ANTI_SYCOPHANCY_FULL → Wizard, Policy
  5 regras + VERIFICAÇÃO DE PREMISSAS (5 sub-regras)
  Mais restritivo: verificar histórico, nunca mudar silenciosamente

ANTI_SYCOPHANCY_ORCHESTRATOR → Orchestrator
  Versão compacta (1 frase) — ponto de entrada global

Crença #11 do Manifesto WeDOTalent:
"Anti-sycophancy em 100% das interações IA."
```

---

## SEÇÃO TRANSVERSAL: COMPLIANCE TÉCNICO

### FairnessGuard — 3 Camadas

```
Arquivo: app/shared/compliance/fairness_guard.py

Layer 1: Explicit Bias Block
  ~350+ patterns em 13 categorias:
  gender, age, ethnicity, religion, disability, marital_status,
  sexual_orientation, pregnancy, appearance, social_class,
  political, nationality, health
  Ação: BLOCK — impede processamento
  Integração: MainOrchestrator (pré-roteamento)

Layer 2: Implicit Bias Soft Warning
  Proxy terms detectados:
  "dinâmico" → age proxy | "boa aparência" → appearance proxy
  Ação: WARN — permite com alerta (log only)
  Integração: MainOrchestrator (pré-roteamento)

Layer 3: Semantic Analysis (LLM-based)
  Provider: Gemini (análise semântica profunda)
  Ação: WARN ou BLOCK dependendo da severidade
  Condicionada por setor: ALPHA1_SECTOR_RULES[sector].fairness_layer3_enabled
  Ativo em: tech, financeiro, saude, rpo
  Inativo em: varejo, logistica

Protected Fields (Learning Loop):
  _LEARNING_PROTECTED_FIELDS = {gender, age, ethnicity, marital_status,
  photo, institution, address, religion, disability, cv_gaps}
  validate_learning_batch() bloqueia patterns discriminatórios ANTES de persistir

Pontos de integração:
  - MainOrchestrator L35-62 (L1/L2 pré-roteamento)
  - jd_generation.py (L1/L2 input+output)
  - wsi_questions.py (per-question check)
  - rubric_evaluation.py (reasoning check)
  - candidate_tools.py (reject_candidate auto-check)
  - PipelineTransitionAgent (L3 pré-check)
  - sourcing_agent (L3 via check_with_sector)
  - communication_tools (L3)
  - RAG pipeline (L3)
```

### PII Masking — 4 Camadas

```
Arquivo: app/shared/pii_masking.py

Camada 1: CPF → [CPF_MASKED]
Camada 2: nome → [NAME_1], [NAME_2], etc.
Camada 3: endereço → [ADDR_MASKED]
Camada 4: campos sensíveis → [FIELD_MASKED]

Função: strip_pii_for_llm_prompt (global)
PIIMaskingFilter: filtro global de logs
Presidio: opt-in para detecção avançada

Regra absoluta: O LLM NUNCA vê dados pessoais reais
Demasking: dados restaurados na response final ao recrutador
Audit: dados mascarados no registro (nunca reais)
```

### FactChecker — 4 Tipos de Verificação

```
Arquivo: app/shared/compliance/fact_checker.py

Tipo 1: Experiência declarada — claims vs dados de contexto
Tipo 2: Certificações — validade técnica
Tipo 3: Período na empresa — coerência temporal
Tipo 4: Habilidades técnicas — relevância para a vaga

Integração: DomainWorkflow._post_check (enable_fact_checker=True por default)
Claim inconsistente → flag para revisão
V5: verificações granulares adicionais (salary, count, %, date)

Pontos de integração:
  - wsi_questions.py (valida claims nas perguntas)
  - sourcing (valida claims nas análises)
  - rubric_evaluation.py (valida scores e claims WSI)
```

### BiasAuditSnapshot — Four-Fifths Rule

```
ConfidenceNode + BiasAuditSnapshot integrados

ConfidenceNode:
  confidence_score = tool_success_ratio × 0.7 + completion_ratio × 0.3
  Score calibrado para comparabilidade real

BiasAuditSnapshot:
  Four-Fifths Rule: se taxa de aprovação de grupo demográfico < 80% de outro
  → alerta automático
  Dados coletados em cada Gate (1 e 2)
  Dashboard de Bias Audit: ○ (pendente — backend coleta dados)
```

### AuditTrail — SOX-Compliant

```
Arquivo: app/shared/compliance/audit_service.py

8 decision types registráveis
Append-only: registros NUNCA podem ser alterados
Retenção: 730-1825 dias (SOX — ~2-5 anos)
record_human_review: registra overrides humanos

O que é registrado:
  - Request original (mascarado)
  - FairnessGuard results (L1/L2/L3)
  - PII masks aplicados
  - LLM response completa
  - FactChecker flags
  - Scores + bias audit
  - Decisão final + motivo

Status de ativação por etapa:
  ● Ativo: jd_generation.py, wsi_questions.py
  ◐ Precisa ativar: auth.py, candidates.py, pipeline tools,
    rubric_evaluation.py, communication
```

---

## SEÇÃO TRANSVERSAL: INTELIGÊNCIA

### 1. Learning Loop (Captura Silenciosa)

```
Arquivo: app/shared/learning/learning_loop_service.py (1137 linhas)
Mecanismo: Observa accept/modify/reject do recrutador sem pedir feedback
Outcomes: accepted | modified | rejected | ignored
Pattern Types: salary_preference, skill_preference, benefit_preference,
               work_model_preference, screening_preference,
               jd_style_preference, source_trust
Confidence: ≥20 samples=high, ≥10=medium, ≥5=low
FairnessGuard: validate_learning_batch() bloqueia discriminação ANTES de persistir
ModelDrift: trigger automático quando feedback rejected/ignored
Snapshot: learning_snapshot_service salva snapshot pré-learning (rollback Z2-01)

Etapas ativas: E2, E3, E4, E5, E7, E8, E9
```

### 2. A/B Testing

```
Arquivo: app/shared/learning/ab_testing_service.py (307 linhas)
Mecanismo: Hash-based traffic splitting (MD5 → bucket 0-9999)
Estatísticas: z-score, p-value (erfc), 95% CI, improvement %
Significância: p < 0.05 AND |improvement| > 5%
Modelo: PromptVariant + ABTestResult
API: GET/POST testes + GET variant via api/v1/ab_testing.py
seed_email_ab_tests: 3 experimentos criados no startup

Etapas ativas: E2, E3, E4, E6, E7, E9
```

### 3. Routing Adaptativo

```
Arquivo: app/services/routing_learning_service.py
Mecanismo: Quando recrutador corrige roteamento, ajusta multipliers
Range: 0.8x (muitos erros) a 1.2x (alta precisão) por domínio
Método: compute_domain_confidence_adjustments(company_id, db)

Etapas ativas: E4, E5, E8
```

### 4. Template Learning

```
Arquivo: app/shared/learning/template_learning_service.py
Mecanismo: Após 3 vagas similares (mesmo setor/seniority), gera template
Métodos: learn_from_job_creation(), suggest_templates_for_improvement()
UNION de fontes corrigida (email + JD + feedback)

Etapas ativas: E2, E6, E9
```

### 5. Calibration

```
Arquivo: app/services/calibration_service.py
Mecanismo: Dual feedback
  Explícito: thumbs up/down do recrutador
  Implícito: avançar candidato low-score = sinal positivo
Output: CalibrationSuggestion (ex: "Reduzir peso de skill técnica em 15%")
Métodos: record_explicit_feedback(), record_implicit_feedback(), generate_suggestions()

Etapas ativas: E4, E5, E7, E8
```

### 6. Score Normalization

```
Arquivo: app/domains/cv_screening/services/score_normalization_service.py
Mecanismo: Ajusta scores baseado no difficulty_coefficient da versão do questionário
Objetivo: Candidatos com versões mais difíceis não penalizados

Etapas ativas: E4, E7
```

### 7. Predictive Analytics

```
Arquivo: app/domains/analytics/services/predictive_analytics_service.py
        + app/services/ml/outcome_predictor.py
API: app/api/v1/predictive_analytics.py
Agent Tools: predictive_tools.py — integrado em agentes

Métodos:
  predict_time_to_fill(db, job_data, company_id) → dias + confidence
  predict_optimal_salary(db, job_data, company_id) → faixa competitiva
  predict_skill_success(db, skill_name, company_id) → probabilidade

Etapas ativas: E2, E4
```

### 8. Model Drift

```
Arquivo: app/services/model_drift_service.py
4 dimensões monitoradas (janela de 7 dias):
  Score Drift: variação > 0.5 pts
  Approval Drift: variação > 10 p.p.
  Cost Drift: aumento significativo de custo LLM
  Latency Drift: degradação de tempo de resposta
Trigger: automático pelo Learning Loop quando feedback negativo acumula
Batch: drift.run_batch — diário 06h Brasília (Celery Beat)
Alerta: 1 trigger=WARNING, 2+=URGENT → Bell + Teams

Etapas ativas: E4, E5, E7, E8
```

### 9. Conversation Memory

```
Arquivo: app/shared/memory/conversation_state.py
Mecanismo: Estado efêmero da sessão de chat
Recursos:
  Entity tracking (última vaga, último candidato mencionado)
  Pronoun resolution ("conte mais sobre ele" → resolve)
  Active filters tracking (filtros persistem na sessão)

Etapas ativas: E2, E3, E4, E5, E6, E7
```

### 10. Semantic Search

```
Arquivo: app/shared/intelligence/semantic_search_service.py
Provider: Gemini text-embedding-004 (768 dimensões)
Cache: Redis para evitar re-embedding
Domínios: Skills, Job Titles, Industries, Locations
Métodos: expand_query(domain, query), expand_skills(), expand_job_titles()
Embedding Service: app/shared/intelligence/embedding_service.py

Etapas ativas: E2, E3, E4
```

### 11. Voice Analysis

```
Arquivo: app/services/voice_service.py
STT Providers: Deepgram (primário), Whisper (fallback)
TTS Provider: OpenAI (voice="nova")
Uso: Triagem WSI por voz — candidato responde por áudio
WSIVoiceOrchestrator: coordena triagem por voz

Etapas ativas: E7
```

### 12. Long-Term Memory

```
Arquivo: libs/agents-core/lia_agents_core/long_term_memory.py
Mecanismo: Episódios + compressão LLM após 30 dias
Integração:
  EnhancedAgentMixin._post_loop_learning: salva learnings após cada ReAct loop
  _get_memory_context: enriquece system prompt com memórias históricas
Background processing via Celery tasks

Etapas ativas: E4, E8, E9A, E9B
```

---

## SEÇÃO TRANSVERSAL: LGPD / DATA PROTECTION

### Consent Flow

```
Arquivo: app/api/v1/lgpd.py + communication_optout.py

1. Consentimento para triagem WSI:
   WelcomeCard com checkbox explícito obrigatório
   Botões desabilitados até aceite LGPD
   ConsentEvent auditável registrado

2. Consentimento para contato:
   CandidateChannelSelector.select_channels verifica:
   → LGPDConsent (consentimento registrado por canal)
   → CandidateOptOut (opt-out por canal)
   WhatsApp: estado AWAITING_CONSENT com mensagem explícita
   Sem consentimento → canal bloqueado

3. Opt-out em emails:
   Link obrigatório em todo email
   HMAC-signed tokens (anti-tampering)
   ConsentEvent auditável: revogação registrada
```

### DSR — Data Subject Requests

```
Endpoints LGPD (api/v1/lgpd.py):
  GET /api/v1/lgpd/data-export/{candidate_id} — export completo
  DELETE /api/v1/lgpd/data-delete/{candidate_id} — anonymize/delete
  GET /api/v1/lgpd/consent/{candidate_id} — consultar consentimentos
  POST /api/v1/lgpd/consent — registrar consentimento
  Portal público: /portal/data-request/[token]

Status: Endpoints existem ○ (pendente integração completa)
```

### Data Minimization

```
Princípios aplicados:
  1. ICS Calendar: apenas dtstart/dtend/summary/location/attendee
     Sem dados sensíveis do candidato
  2. ATS Sync: ATSSyncService filtra dados sensíveis (salário)
     "Dado sensível - não sincronizar"
  3. Feedback: PipelineFeedbackTool._remove_score_references
     Strip scores numéricos do feedback ao candidato
  4. PII Masking: 4 camadas pré-LLM
     LLM nunca vê dados reais
  5. ToonService: anonymize=True para visualização anônima
```

### Retenção por Tipo de Dado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Tipo de Dado              │ Retenção        │ Base Legal                    │
│───────────────────────────┼─────────────────┼───────────────────────────────│
│  Audit Trail (SOX)         │ 730-1825 dias   │ SOX compliance, Art. 12 LGPD │
│  Scores WSI                │ Duração processo│ Legítimo interesse            │
│  Dados de candidato (PII)  │ Até revogação   │ Consentimento                 │
│  Logs de comunicação       │ 365 dias        │ Legítimo interesse            │
│  Embeddings de perfil      │ Indefinido      │ Anonimizados (sem PII)        │
│  Learning patterns         │ Indefinido      │ Agregados (sem PII individual)│
│  LLM prompts/responses     │ 90 dias         │ Auditoria + melhoria          │
│  Conversation memory       │ Sessão          │ Efêmero                       │
│  Long-term memory          │ Compressão 30d  │ Anonimizado                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: CT — CHAT UNIFIED COMO ENTRADA MVP

> **Premissa do MVP**: o `UnifiedChat` é a **superfície primária** de interação com a LIA. Todo
> hub de UI (Configurações, Vagas, Kanban, Triagem, Onboarding) é um *fallback formal* —
> a entrada conversacional precede e gera as ações da UI.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  CT — Chat Unified (transversal a TODAS as etapas E0–E16)                    │
└──────────────────────────────────────────────────────────────────────────────┘

 1  Componentização (frontend)
    Pasta: plataforma-lia/src/components/unified-chat/
      • UnifiedChat.tsx               (raiz; 3 render modes: floating, panel, page)
      • UnifiedChatHeader.tsx         (título contextual + ações rápidas)
      • UnifiedChatBubble.tsx         (renderização por role + cards especiais)
      • UnifiedChatInput.tsx          (input + slash commands + mentions + uploads)
      • UnifiedMessageList.tsx        (virtualizada; auto-scroll inteligente)
      • UnifiedChatEmptyState.tsx     (sugestões iniciais por contexto)
      • UnifiedChatConditional.tsx    (gating por feature flag / role)
      • DashboardChatPanel.tsx        (modo "panel" usado no dashboard)
      • ChatPageFullscreen.tsx        (modo "page" — onboarding, /chat)
      • InlineChatBridge.tsx          (chat embutido em hubs de Configurações)
      • SmartSuggestions.tsx          (chips de próxima ação)
      • SlashCommandDropdown.tsx + slash-commands.ts (catálogo /comandos)
      • MentionDropdown.tsx + useMentionAutocomplete.ts (@vaga, @candidato)
      • useSmartFileUpload.ts         (drop de PDF/DOCX → process_document)
      • useInputDropdown.ts           (orquestração unificada dos popups)
      • LgpdConsentDialog.tsx         (modal de consent inline no chat)
      • FairnessWarningBanner.tsx     (banner quando FairnessGuard L1/L2 alerta)
      • ContextConfigPanel.tsx        (debug: ver contexto enviado ao agente)
      • NavigationHintCard.tsx        (sugere navegar para hub específico)
      • OutreachCard.tsx, TastingInsightCard.tsx, ThinkingStepsCard.tsx
        (cards estruturados retornados pelos agentes)
      • TransportModeIndicator.tsx    (indica SSE vs WebSocket vs polling)
      • wizard/                       (subfluxo do WizardReActAgent dentro do chat)

 2  Transporte (frontend ↔ backend)
    Primário:  POST /api/v1/agent_chat_sse  (SSE streaming)             ●
    Fallback:  WS   /api/v1/agent_chat_ws   (full duplex)               ●
    Retry:     auto downgrade SSE → WS → polling
    Indicador visual: TransportModeIndicator.tsx mostra modo ativo

 3  Roteamento por intenção (backend)
    Toda mensagem → CascadedRouter (8 tiers — ver E0)
    Tier 0: MemoryResolver (resolve "ele/ela/aquele candidato")
    Tier 1-3: caches (LRU + Redis + pgvector)
    Tier 4: FastRouter (regex/keyword)
    Tier 5: LLM Cascade (Haiku → Sonnet → Opus) — A/B variant via prompt_experiment
    Tier 6: AutonomousReActAgent (cross-domain fallback)
    Tier 7 (fallback): clarification_needed → pergunta no chat

 4  Slash commands (entrada direta de ação)
    Catálogo: slash-commands.ts (testes em slash-commands.test.ts)
    Exemplos: /vaga novo, /candidato buscar, /triagem iniciar,
              /agendar, /relatorio diario, /onboarding continuar
    Cada / equivale a uma `action_id` específica — pula CascadedRouter

 5  Mentions e contexto
    @vaga:<id> e @candidato:<id> injetam entidade no contexto do turno
    useMentionAutocomplete.ts faz lookup via /api/v1/autocomplete

 6  Eventos cross-component (event bus de janela)
    `lia:settings-action`     → hub dispara ação para o chat executar
    `lia:settings-success`    → chat avisa hub que persistiu (E0.5, T003)
    `lia:settings-error`      → chat avisa hub que falhou
    `lia:settings-updated`    → hub avisa chat que houve save pela UI (T004)
    `lia:onboarding-progress` → progresso 7-actions (E0.5)
    `lia:navigate`            → NavigationHintCard solicita rota
    Broadcaster condicional: SettingsSyncBroadcaster (shell incondicional
    em dashboard-app.tsx — ativo em Configurações, Chat e demais hubs)

 7  Integração com OnboardingChatPage (E0.5)
    OnboardingChatPage.tsx hospeda UnifiedChat em modo "page" + state machine
    de 7 ações; cada step do onboarding emite/escuta eventos do item 6 acima.

 8  Cards estruturados retornados por agentes
    OutreachCard         → Ag.7 sugere mensagem de outreach
    TastingInsightCard   → Ag.4/Ag.5 explica score WSI
    ThinkingStepsCard    → mostra passos do ReAct (debug-friendly)
    NavigationHintCard   → Ag.0 sugere abrir hub específico

 9  Proteções aplicadas em CADA turno
    🔒 FairnessGuard L1 (pré-roteamento) — mensagem do usuário
    🔒 PII Masking — sempre ativo nas requests/logs
    🔒 ConsentManagement — bloqueia ações de outreach sem opt-in
    🔒 LgpdConsentDialog — modal inline antes de coletar dados sensíveis
    🔒 FairnessWarningBanner — alerta visível ao usuário (transparência)
    🧠 LongTermMemory — episódios salvos por agente
    🧠 Few-shot evolution — correções via lia_feedback alimentam prompts

10  Status de cobertura por hub (entrada conversacional)
    ● Vagas (E2/E3)           — WizardReActAgent dentro do chat
    ● Funil (E4)              — TalentReActAgent
    ● Kanban (E5/E8)          — KanbanReActAgent
    ● Triagem (E7)            — WSIInterviewGraph
    ● Agendamento (E9A)       — InterviewGraph
    ● Configurações (E0.5)    — 7 actions via process_document/save_*
    ◐ Talent Pool (E12)       — domain existe; comandos de chat parciais
    ◐ Reports (E15)           — endpoints existem; comandos de chat parciais
    ✗ Proposta (E10)          — STUB
    ✗ Hire / HRIS (E11)       — STUB
    ✗ Closing (E14)           — STUB

┌──────────────────────────────────────────────────────────────────────────────┐
│  PROTEÇÕES TRANSVERSAIS DO CHAT UNIFIED                                       │
│  1. Anti-Sycophancy — perfil ORCHESTRATOR no router ●                        │
│  2. FairnessGuard L1+L2 (todo turno) ●                                       │
│  3. PII Masking ●                                                            │
│  4. ConsentManagement ●                                                      │
│  5. Rate limiting por user/company ●                                         │
│  6. CircuitBreaker em cada provider LLM ●                                    │
│  7. Audit por turno ◐ (precisa expansão por agente)                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SEÇÃO TRANSVERSAL: CT-ML — CAMADA DE INTELIGÊNCIA (11 CAMADAS, AUDITORIA HONESTA)

> Esta seção complementa a **SEÇÃO TRANSVERSAL: INTELIGÊNCIA** (acima) — lá estão os
> detalhes de mecanismo por camada. Aqui está a **auditoria consolidada de status real**
> (ativo / dormindo / stub) por camada, com localização canônica do código, integração
> com agentes e endpoints, e o **ciclo virtuoso de aprendizado** que costura as 11.
>
> Fonte canônica de auditoria: [`lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md`](../../../lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md) (4995 linhas).
>
> Legenda: ● ativo (em produção, com tráfego real) · ◑ dormindo (código pronto, gating/uso parcial) · ✗ stub (esqueleto sem produção) · ⌬ shim (re-export retro-compat — usar canônico)

### Tabela mestre — 11 camadas de inteligência

| # | Camada | Localização canônica | Endpoint / Integração | Etapas | Status |
|---|---|---|---|---|---|
| 1 | **Learning Loop** (captura silenciosa) | `app/shared/learning/learning_loop_service.py` (1133 L) | `learning_snapshot_service.py` para rollback Z2-01; FairnessGuard `validate_learning_batch()` | E2 E3 E4 E5 E7 E8 E9 | ● |
| 2 | **A/B Testing** | `app/shared/learning/ab_testing_service.py` (340 L) + `app/shared/intelligence/ab_testing/email_template_seeder.py` | `app/api/v1/ab_testing.py`; seed 3 experimentos no startup | E2 E3 E4 E6 E7 E9 | ● |
| 3 | **Semantic Search** (skills/titles/industries) | `app/shared/intelligence/semantic_search_service.py` (414 L) | usado por sourcing/funil + WizardReActAgent | E2 E3 E4 | ● |
| 4 | **Embedding Service** (Gemini text-embedding-004) | `app/shared/intelligence/embedding_service.py` (295 L) | base de Semantic Search e Calibration; cache Redis | transversal | ● |
| 5 | **RAG** (retrieval-augmented generation) | `app/domains/ai/services/rag_service.py` (297 L) + `rag_pipeline_service.py` (657 L) + `ragas_evaluation_service.py` | `app/api/v1/rag_search.py`; PGVector como store; consumido por agentes de busca/insight | E4 E7 E15 | ◑ (ativo em search; insight ainda parcial) |
| 6 | **Calibration** (dual feedback explícito + implícito) | `app/domains/analytics/services/calibration_service.py` (474 L) + `app/domains/cv_screening/services/calibration_profiles.py` (948 L) | `app/api/v1/calibration.py` + `app/api/v1/calibration_dashboard_v2.py` | E4 E5 E7 E8 | ● |
| 7 | **Predictive Analytics** (time-to-fill, salary, skill success) | `app/domains/analytics/services/predictive_analytics_service.py` (945 L) + `app/services/ml/outcome_predictor.py` | `app/api/v1/predictive_analytics.py`; tools: `app/shared/tools/predictive_tools.py` | E2 E4 | ● |
| 8 | **Score Normalization** (difficulty coefficient) | `app/domains/cv_screening/services/score_normalization_service.py` (183 L) | normaliza WSI por versão do roteiro; usado em E4/E7 | E4 E7 | ● |
| 9 | **Conversation Memory** (pronoun resolution + entidades sticky) | `app/domains/recruiter_assistant/services/conversation_memory.py` + `app/shared/memory/conversation_state.py` | resolve "ele/ela/aquele candidato" no Tier 0 do CascadedRouter | E2 E3 E4 E5 E6 E7 | ● |
| 10 | **Template Learning** (3+ vagas similares → template) | `app/shared/learning/template_learning_service.py` (401 L) ⌬ shim em `app/shared/intelligence/template_learning/template_learning_service.py` e `app/domains/job_management/services/template_learning_service.py` | `app/api/v1/job_templates.py` | E2 E6 E9 | ● |
| 11 | **Routing Adaptativo** (multipliers por domínio) | `app/services/routing_learning_service.py` consumido em `app/orchestrator/cascaded_router.py::_apply_adaptive_adjustments` | range 0.8x–1.2x; `Task #672` adicionou warning + CI gate de capabilities | E4 E5 E8 | ● |
| ＋ | **Voice Analysis** (STT/TTS para WSI por voz) | `app/domains/cv_screening/services/voice_service.py` + `wsi_voice_orchestrator.py` + `app/services/voice_interview_state_machine.py` | endpoints: `voice_stream.py`, `gemini_voice.py`, `twilio_voice.py`, `voice_screening.py`; STT Deepgram (Whisper fallback), TTS OpenAI nova | E7 | ◑ (ativo em piloto; generalização gated) |
| ＋ | **Long-Term Memory** (episódios + compressão LLM) | `libs/agents-core/lia_agents_core/long_term_memory.py` consumido por `EnhancedAgentMixin._post_loop_learning` | Celery tasks de compressão após 30 dias | E4 E8 E9A E9B | ● |

> Notas de auditoria
> - Os arquivos `app/shared/services/calibration_service.py`, `embedding_service.py`,
>   `learning_loop_service.py`, `rag_service.py`, `rag_pipeline_service.py`,
>   `ragas_evaluation_service.py` são **shims retro-compatíveis** (⌬). Sempre importar
>   da localização canônica listada acima — `app.shared.services.*` redireciona via
>   `re-export` por compatibilidade histórica e será removido em consolidação futura
>   (vide ADR-018 — tool registry consolidation).
> - O caminho `app/shared/services/predictive_analytics_service.py` **não existe** — o
>   serviço está em `app/domains/analytics/services/`. Mesma observação para
>   `conversation_memory_service.py` (canônico em `app/domains/recruiter_assistant/services/conversation_memory.py`)
>   e `score_normalization_service.py` (canônico em `app/domains/cv_screening/services/`).
> - **Model Drift** (cobre toda a tabela como guardião) está documentado na seção
>   INTELIGÊNCIA #8 — não é uma 12ª camada de aprendizado, é o monitor das demais.

### Ciclo virtuoso (como as 11 camadas se costuram)

```
  ┌────────────────────── TURNO DO RECRUTADOR ──────────────────────┐
  │  Mensagem → CascadedRouter (8 tiers — ver E0)                   │
  │     Tier 0  Conversation Memory  (resolve pronome/entidade)     │
  │     Tier 1-3 caches (LRU + Redis + pgvector — Embedding+RAG)    │
  │     Tier 4  FastRouter (regex/keyword)                          │
  │     Tier 5  LLM Cascade  ←── A/B Testing (variant via prompt)   │
  │     Tier 6  AutonomousReActAgent                                │
  │     ↓                                                           │
  │  Routing Adaptativo aplica multipliers (0.8x–1.2x)              │
  │     ↓                                                           │
  │  Agente executa action → resposta + persistência                │
  └────────────────────────────────┬────────────────────────────────┘
                                   ↓
  ┌─────────────────── OBSERVAÇÃO PÓS-AÇÃO ─────────────────────────┐
  │  Recrutador: aceita / modifica / rejeita / ignora               │
  │     ↓                                                           │
  │  Learning Loop captura outcome (silencioso, sem perguntar)      │
  │     ↓                                                           │
  │  ├─→ Calibration  recebe sinal explícito + implícito            │
  │  ├─→ Template Learning conta variantes (3+ similares = template)│
  │  ├─→ Score Normalization atualiza difficulty_coefficient        │
  │  ├─→ Predictive Analytics atualiza histórico de outcomes        │
  │  └─→ Voice Analysis: transcrição alimenta WSI scoring (E7)      │
  │     ↓                                                           │
  │  FairnessGuard.validate_learning_batch()  ← bloqueia se viés    │
  │     ↓                                                           │
  │  learning_snapshot_service salva snapshot (rollback Z2-01)      │
  │     ↓                                                           │
  │  Persistência → próximo turno usa pesos atualizados             │
  └────────────────────────────────┬────────────────────────────────┘
                                   ↓
  ┌──────────────── MONITORAMENTO CONTÍNUO (24/7) ──────────────────┐
  │  Model Drift Service (4 dimensões, janela 7 dias)               │
  │    Score / Approval / Cost / Latency Drift                      │
  │  Trigger: 1 = WARNING · 2+ = URGENT → Bell + Teams              │
  │  Long-Term Memory: episódios comprimidos após 30 dias           │
  └─────────────────────────────────────────────────────────────────┘
```

### Gaps e dívidas técnicas explícitas (CT-ML)

| Camada | Gap | Trilha |
|---|---|---|
| RAG | Insight (E15) consome RAG só parcialmente; falta cobertura RAG em E12 (Talent Pool) | Follow-up: ampliar `rag_pipeline` para insights de pool |
| Voice Analysis | Generalização além de WSI; falta TTS multi-idioma além de pt-BR/en-US | Roadmap pós-MVP |
| Shims `app/shared/services/*` | 6 shims ainda em uso por imports legados | ADR-018 consolida em sweep único |
| Score Normalization | Apenas 183 L — falta exposição via API e dashboard | Follow-up `score_normalization` API |
| Routing Adaptativo | Métrica de "qualidade do ajuste" não exposta no dashboard | Estender `agent_quality_dashboard.py` |

---

## SEÇÃO TRANSVERSAL: CT-CHANGELOG — MELHORIAS Q1–Q2/2026

> Categorização das mudanças entregues no branch `replit-sync` entre **mar/2026** e
> **abr/2026** (Q1 fim → Q2 início). Fonte: `git log replit-sync` + `.local/tasks/` +
> `lia-agent-system/ARCHITECTURE.md` (ADRs 001–020).

### A) Production Readiness (qualidade estrutural)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| Refactor abaixo de 1000 linhas | 39→5 arquivos > 1kL · `useEAPCallbacks`, `useExpandedChatModalCore`, `modern-conversations`, `CandidatesFilterPanel`, `JDEvaluationPanel`, `KanbanColumnRenderer`, `KanbanTableView`, `JobEditTab`, `BenefitsTab`, `DepartmentsTab`, `triagem-modal`, `expandable-ai-prompt`, `job-status-modal`, `lia-screening-guide`, `goals-management`, `CompanyDataSection`, `CandidateSearchResultsView` | commits `0cbe0ff75`, `e6c0ce72d`, `a849e3b8b`, `38c7cd2bb`, `669494b28`, `3897bc42a`, `5bfff47b2`, `a2447576a`, `b3d3b14f4`, `2cdad7231`, `326804725`, `46f637841`, `1ec46c597`, `60ad6e82d`, `311758d20` |
| Cobertura de testes | 38→50+ test files unit · 756 testes totais · 12 novos arquivos hooks/utils/components · cobertura `execute_action` para 11 domínios (Task #687 + #596) | `55045840b`, `4375bf0ee`, `596c9c5e5` |
| TypeScript / ESLint | 0 TS errors após refactors, 0 ESLint errors · guards de useMemo, fix duplicate className, IIFE, JSX comments | `b88d777db`, `485e37085`, `db9dfae7b`, `3762d311c` |
| Auditoria Vue-readiness | v6→v7 (55→59/70), HOOKS_NEEDING_REFACTOR = [] · 100% Pinia-ready | `0cbe0ff75`, `8dcba821d`, `ed443047b`, `845fe57c8` |

### B) Tenant Isolation (multi-tenancy fail-closed)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| Consolidação residual | Task #673 fecha #329, #335, #336, #359, #361 · sweep dos últimos vazamentos cross-tenant | `2f19de689` |
| Tool registries fail-closed sem `company_id` | Asserts em todos os registries de tools · IDOR fix em `/finetuning/stats` e `/finetuning/export` (Task #306) | `6fd638fbc`, `97205ecc1` |
| Forward de tenant ID | WSI on-the-fly question pipeline (Task #334) propaga `company_id` · admin client creation cria `company_profiles` com UUID explícito | `9c7e65855`, `d53d0af64`, `b90e8e2cb` |
| Rails sync | ClientAccount sync no admin tenant (P0 fix) — ATS sincroniza criação de cliente | `04b5f8bb0` |

### C) Routing Canônico (CascadedRouter + capabilities)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| Fixes canônicos P0/P1 | `feat(tools): canonical routing fixes — P0 + P1.A + P1.B + P1.C` · DEFAULT_DOMAIN warning + CI gate de chat-capabilities (Task #672) | `527f2c3ce`, `21f90805f`, `b3d068c9c` |
| Echo de specialist | Chat replies declaram qual specialist tratou (Task #552) — observabilidade de routing | `2bf526354` |
| Slash commands alinhados | Comandos `/...` consistentes entre produto, código e docs (Task #300) · `duplicate_job` / `clone_job` cabeados (Task #624) | `9bc805b29`, `43d9891d3` |
| Cleanup de tools | Remoção de `score_cv` órfã do cv_screening (Task #623) · stub `recruiter-goals` substituído por OKR/quota real (Task #599) · restauração do toolset Sourcing | `9bbb304be`, `92e6fe1c8`, `985cb54bd` |
| Proteção de diretórios estratégicos | Task #670 protege 8 dirs e recategoriza · ADR-018 plano operacional para registry | `4b95f2868`, `8cd82e847` |

### D) Compliance (FairnessGuard + PII + LGPD + Audit)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| PII real (não-stub) | `feat(task-712): real PII masking + structured extraction + tool metadata` em todo turno do chat | `cb56abc90` |
| FairnessGuard v5 vs LIA | Diagnóstico comparativo (Task #84) · WarningBanner inline no chat · `validate_learning_batch` bloqueia learning enviesado | `af9361a8d`, `f947f9a21` |
| XSS defense-in-depth | Sanitização de `onHighlightSearchTerm` em `ChatMessageList` | `15435fae5` |
| Bell notification in-app | Ativação completa (Task #82) — canal de alertas Drift/Audit/Compliance | `803aa38a4` |
| Persona/identity hardening | LIA identity override impede leak do modelo subjacente (Gemini) · Phase-1 intercept para perguntas de identidade | `881aef9d0`, `44e381ce5`, `0ad291737`, `89c427955` |

### E) ML / IA (camada cognitiva — ver CT-ML acima)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| Eval pipeline | LIA Eval 62→70/73 · 15 fixes documentados · regex Português-aware (WZ-002/003) · KB-006 UUID filter · suggest_salary/generate_jd_direct registrados | `04ff86a65`, `24a16fd56`, `aee9ab45f`, `3b53ca02e`, `a41b000bd` |
| Camada de extração semântica | Layer dedicada extrai sinais semânticos das respostas do candidato · scoring fairness + remoção de legacy | `e762705ef`, `4af2b303d`, `f947f9a21` |
| Calibration dashboard v2 | Endpoint dedicado `app/api/v1/calibration_dashboard_v2.py` para visualização de profiles | `527f2c3ce` linhagem |
| Quality dashboard de agentes | Endpoint `agent_quality_dashboard.py` · billing por agente verificado E2E (Task #558) | `3d6328f02` |
| Wizard ReAct estável | JD+salary Phase 1 estabilizado · MT-002/003 bypass · entity_id sanitization (strip non-UUID) | `a760fe110`, `d2a8954d9` |

### F) Integrações (ATS, voz, email, scheduling)

| Tema | Entregas notáveis | Refs |
|---|---|---|
| Microsoft Teams | Configurar e validar app LIA Teams para produção (Task #706) | `4a7191d99` |
| WhatsApp + Teams reminders | Lembretes de entrevista por WhatsApp e Teams, não só email (Task #626) · scheduling-link DB schema corrigido (Task #625) | `c8559a442`, `933949c9f` |
| Candidate Portal Rails | Spec completa (`CANDIDATE_PORTAL_RAILS_SPEC.md`) · commits hashes incluídos · admin/settings null profile fix | `1b0ca9629`, `63c21738e`, `c134dc252` |
| Voz | Pipeline `voice_stream` / `gemini_voice` / `twilio_voice` / `voice_screening` operacional · WSI voice orchestrator | linhagem `wsi_voice_orchestrator.py` |
| Auth | JWT blacklist check em `get_current_user` (P0) · `CandidatePreview` re-export | `2f1bd439c` |

### G) Documentação / Glossário / ADRs

| Tema | Entregas notáveis | Refs |
|---|---|---|
| FLUXO_TECNICO_COMPLETO_ALPHA1 | v2.0 (rewrite alpha-1 atual) · adicionado E0 (cognitiva) · E10–E16 + CT Chat Unified + tabela 16 etapas (Task #713) · CT-ML + CT-CHANGELOG (Task #714, este commit) | `1699d7fc9`, `694561e28`, `28e67f22a` |
| Glossário central | Task #692 — glossário + sync automático + CI guard · GLOSSARIO_ACTIONS_TOOLS (281 actions / 94 tools) · descrições enriquecidas (Task #690) | `4930b4092`, `6e9287f50`, `27aaa3461` |
| MAPA 18 domínios | `fase2c_domain_verification_report.md` reescrito · MAPA_CAMADA_INTELIGENCIA atualizado (4995 L) | `974282fe1`, `6e9287f50` |
| ADRs novos | ADR-018 (tool registry consolidation, Task #382) · ADR-019 (glossário/MAPA) · ADR-020 (intent-routed wizards stateful) | `8cd82e847`, `6e9287f50` |
| Padronização de domínios | Production-ready para domínios em evolução (Task #691) | `f05db64d8` |
| Migration guide | GUIA_MIGRACAO_V5_COMPLIANCE v2.2 · Mapa de Aproveitamento · 13 problemas + 24 sub-problemas (Task #87) | `e5a26e80d`, `4fe4eedfb`, `aed2ee874` |

### Ondas e marcos (timeline resumido)

```
mar/2026  ├─ refactor wave (Vue-readiness, < 1000L, 0 TS errors)
          ├─ FairnessGuard v5 diagnose · Bell notif · Migration guide v2
abr/2026  ├─ FLUXO v2.0 + E0 cognitiva
          ├─ Routing canônico P0/P1 + ADR-018 + capabilities CI gate
          ├─ Tenant isolation residual (Task #673)
          ├─ Glossário Central (Task #692) + ADR-019/020
          ├─ Eval LIA 62→70/73 + 15 fixes documentados
          ├─ Microsoft Teams produção · WhatsApp/Teams reminders
          ├─ PII real + identity hardening + JWT blacklist
          ├─ Onboarding proativo + 7 actions company_settings (Task #712)
          ├─ FLUXO E10–E16 + CT Chat Unified (Task #713)
          └─ FLUXO CT-ML + CT-CHANGELOG (Task #714 — este documento)
```

---

## TABELA CONSOLIDADA — STATUS DAS 16 ETAPAS + TRANSVERSAIS

Legenda: ● implementado · ◐ parcial · ✗ stub / ausente

| Etapa | Nome | Domínio principal | Agente principal | Status |
|-------|------|-------------------|------------------|--------|
| E0    | Arquitetura de IA (camada cognitiva)         | orchestrator              | Ag.0 MainOrchestrator       | ●  |
| E0.5  | Onboarding proativo + Configurações 7-actions| company_settings          | Ag.0 + process_document     | ●  |
| E1    | Login                                        | auth                      | —                           | ●  |
| E2    | Editar/criar vaga                            | job_management            | WizardReActAgent            | ●  |
| E3    | Configurar roteiro WSI                       | cv_screening              | WSIQuestionGenerator        | ●  |
| E4    | Buscar candidatos (funil)                    | sourcing + cv_screening   | Ag.2 SourcingReAct + Ag.3   | ●  |
| E5    | Aprovar mapeados (Gate 1)                    | pipeline                  | KanbanReAct + PipelineTrans.| ●  |
| E6    | Contato via email + follow-up                | communication             | Ag.7 CommunicationReAct     | ●  |
| E7    | Triagem WSI                                  | cv_screening              | Ag.4 WSIInterviewGraph      | ●  |
| E7A   | Triagem abandonada                           | cv_screening              | Ag.4 (timeout handler)      | ●  |
| E7B   | Feedback pós-triagem                         | cv_screening              | Ag.4 + Ag.7                 | ●  |
| E8    | Aprovar/reprovar triados (Gate 2)            | pipeline                  | KanbanReAct + PipelineTrans.| ●  |
| E9A   | Agendar entrevista                           | interview_scheduling      | Ag.6 InterviewGraph         | ●  |
| E9B   | Enviar feedback (reprovado)                  | communication + cv_screen | Ag.7 + PersonalizedFeedback | ●  |
| E10   | Proposta & Negociação                        | (sem domínio dedicado)    | Ag.7 (parcial)              | ✗  |
| E11   | Hire & Pré-Onboarding                        | (sem domínio dedicado)    | (sem agente)                | ✗  |
| E12   | Arquivamento & Talent Pool                   | talent_pool               | TalentPoolDomain            | ◐  |
| E13   | Pós-decisão Analítico                        | analytics + journey_map.  | (parcial via reports/bias)  | ◐  |
| E14   | Closing da vaga                              | job_management            | (sem orquestração)          | ✗  |
| E15   | Reporting & Dashboards                       | analytics + saas_metrics  | Ag.7 (templates)            | ◐  |
| E16   | Feedback Loop (contínuo)                     | ai (lia_feedback)         | drift + fewshot evolution   | ◐  |
| **CT**| **Chat Unified (entrada MVP — transversal)** | **chat / orchestrator**   | **Ag.0 + 8-tier Cascade**   | ●  |

**Resumo de cobertura MVP**:
- **Sólidas (●)**: 14 etapas — E0, E0.5, E1–E9B, CT
- **Parciais (◐)**: 4 etapas — E12, E13, E15, E16
- **Stubs (✗)**: 3 etapas — E10, E11, E14 (todas pós-decisão / contratação)

> **Conclusão técnica**: o MVP cobre o ciclo completo *atrair → triar → decidir*
> com qualidade. O ciclo *contratar → onboardear → analisar QoH* (E10/E11/E14)
> permanece como STUB e é o principal vetor de trabalho pós-MVP, junto com a
> camada de ML para Quality of Hire e o pipeline de NPS estruturado (E13/E16).

---

## MAPA CONSOLIDADO DE AGENTES

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MAPA DE AGENTES — ALPHA 1                                                    │
│                                                                               │
│  Ag.0 MainOrchestrator                                                        │
│    Classe: MainOrchestrator                                                   │
│    Domínio: orchestrator                                                      │
│    LLM: Gemini (CascadedRouter T5)                                           │
│    Tools: CascadedRouter (6-tier), ActionExecutor, PendingAction             │
│    Etapas: E5, E6, E7 (coordenação geral)                                   │
│    FG: L1+L2 (pré-roteamento) | Anti-Sycophancy: ORCHESTRATOR               │
│                                                                               │
│  Ag.2 SourcingReActAgent                                                      │
│    Classe: SourcingReActAgent (LangGraphReActBase + EnhancedAgentMixin)       │
│    Domínio: sourcing                                                          │
│    Registry: "sourcing"                                                       │
│    LLM: Gemini | max_iterations: 5 | max_tool_calls: 3                      │
│    Tools: 15 (search, analyze, compare, rank, outreach, generate_message)    │
│    Etapas: E4 (busca de candidatos)                                          │
│    FG: L1+L2+L3 | PII: ativo | Audit: ◐                                    │
│                                                                               │
│  Ag.3 TriagemCurricular (CV Screening)                                        │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini                                                                │
│    Etapas: E4 (triagem curricular na busca)                                  │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ◐                │
│                                                                               │
│  Ag.4 WSIInterviewGraph                                                       │
│    Classe: WSIInterviewGraph (LangGraph StateGraph)                          │
│    Domínio: cv_screening                                                      │
│    LLM: Gemini | 8 stages | Bloom+Dreyfus+BigFive                           │
│    HITL: interrupt_before=["lg_generate_feedback"]                           │
│    Checkpoint: PostgresSaver (sessões 30-120 min)                            │
│    Etapas: E7 (conduz entrevista WSI), E7B (feedback pós-triagem)            │
│    FG: L1+L2+L3 | PII: ativo | Fact-Check: ativo | Audit: ◐                │
│                                                                               │
│  Ag.5 WSIService (Scoring)                                                    │
│    Classe: WSIService + WSIDeterministicScorer                                │
│    Domínio: cv_screening                                                      │
│    LLM: SEM LLM (determinístico — zero latência, zero custo)                 │
│    Etapas: E4 (score WSI na busca), E7 (calcula score final)                 │
│    ScoreNormalization: difficulty_coefficient ativo                           │
│                                                                               │
│  Ag.6 InterviewGraph                                                          │
│    Classe: InterviewGraph (LangGraph StateGraph)                             │
│    Domínio: interview_scheduling                                              │
│    LLM: Gemini | 6 nós                                                       │
│    Tools: schedule_interview, check_availability, reschedule, cancel         │
│    Etapas: E9A (agendar entrevista)                                          │
│    CircuitBreaker: "google_calendar"                                         │
│                                                                               │
│  Ag.7 CommunicationReActAgent + PersonalizedFeedbackService                  │
│    Classes: CommunicationReActAgent (ReAct) + PersonalizedFeedbackService    │
│    Domínios: communication + cv_screening                                    │
│    LLM: Gemini | max_iterations: 5                                           │
│    Tools: send_email, send_whatsapp, get_history, schedule_message           │
│    Etapas: E5 (feedback rejeição Gate 1), E6 (contato email),               │
│            E8 (feedback Gate 2), E9B (feedback reprovado)                    │
│    FG: L1+L2 | LGPD: opt-out obrigatório                                    │
│                                                                               │
│  Ag.8 ATSIntegrationReActAgent ⚠ PÓS-MVP                                   │
│    Classe: ATSIntegrationReActAgent                                           │
│    Domínio: ats_integration                                                   │
│    LLM: Gemini                                                                │
│    Tools: sync_candidate_to_ats, fetch_candidate_from_ats, validate_fields   │
│    Etapas: E2 (sync ATS), E5 (sync status), E8 (sync status)                │
│    Status: Código existe, depende de credenciais de produção                 │
│                                                                               │
│  SERVIÇOS AUXILIARES (sem rótulo Ag.):                                        │
│                                                                               │
│  WSIQuestionGenerator / WSIScreeningQuestionGenerator                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E3 (gera perguntas WSI)                                           │
│                                                                               │
│  WSIScreeningPipeline                                                         │
│    Domínio: cv_screening | LLM: Gemini                                       │
│    Etapas: E4 (triagem/screening na busca)                                   │
│                                                                               │
│  WSIVoiceOrchestrator                                                         │
│    Domínio: cv_screening | LLM: Gemini + Deepgram + OpenAI TTS              │
│    Etapas: E7 (triagem por voz)                                              │
│                                                                               │
│  JobDescriptionGeneratorService                                              │
│    Domínio: job_management | LLM: Claude (Anthropic)                         │
│    Etapas: E2 (gera JD), E3 (JD como base para WSI)                         │
│                                                                               │
│  PipelineTransitionAgent                                                      │
│    Classe: PipelineTransitionAgent (LangGraphReActBase + EnhancedAgentMixin) │
│    Domínio: pipeline | LLM: Gemini                                           │
│    Invocação: POST /api/v1/pipeline/interpret-context (direta)               │
│    Tools: 20 | Etapas: E5, E8 (transições de pipeline)                       │
│                                                                               │
│  WizardReActAgent                                                             │
│    Registry: "wizard" | Domínio: job_management | LLM: Gemini               │
│    6 stages: input-evaluation → jd-enrichment → salary → competencies →      │
│              wsi-questions → review-publish                                   │
│    Tools: 10 | Etapas: E2, E3 (criação/edição de vagas)                      │
│                                                                               │
│  KanbanReActAgent                                                             │
│    Registry: "kanban" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 22 (maior número) | Etapas: E5, E8 (Kanban board)                 │
│                                                                               │
│  TalentReActAgent                                                             │
│    Registry: "talent" | Domínio: recruiter_assistant | LLM: Gemini           │
│    Tools: 13 | Stages: discovery → analysis → action_planning               │
│    Etapas: E4 (funil de talentos)                                            │
│                                                                               │
│  PolicyReActAgent                                                             │
│    Registry: "policy" | Domínio: hiring_policy | LLM: Gemini                │
│    Tools: 13 | Setup wizard por blocos                                       │
│    Etapas: Transversal (configuração de políticas)                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Grafo de Dependências

```
                    ┌──────────────┐
                    │    Ag.0      │
                    │ Orchestrator │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │  Ag.2    │ │  Ag.4   │ │  Ag.8   │
        │ Sourcing │ │Entrev.  │ │ ATS Int.│
        └─────┬────┘ │  WSI    │ └────┬────┘
              │      └────┬────┘      │
              │           │           │
        ┌─────▼────┐ ┌────▼─────┐    │
        │  Ag.3    │ │  Ag.5   │    │
        │ Triagem  │ │Avaliador│    │
        │Curricular│ │  WSI    │    │
        └──────────┘ └────┬────┘    │
                          │         │
                    ┌─────▼────┐    │
                    │  Ag.7    │◄───┘
                    │Analista  │
                    │Feedback  │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Ag.6    │
                    │Scheduling│
                    └──────────┘
```

---

## GAPS CONSOLIDADOS — AÇÕES PENDENTES

### Audit Trail (Prioridade: MVP)

| Etapa | O que falta | Arquivo |
|-------|------------|---------|
| E1 Login | Ativar audit de login | auth.py |
| E4 Busca | Ativar audit de buscas | candidates.py |
| E5 Gate 1 | Ativar audit de aprovações/rejeições | pipeline tools |
| E6 Contato | Ativar audit de envios | communication |
| E7 Triagem | Ativar audit por pergunta/resposta/score | rubric_evaluation.py |
| E8 Gate 2 | Ativar audit de aprovações Gate 2 | pipeline tools |
| E9A Scheduling | Ativar audit de agendamentos | scheduling |
| E9B Feedback | Ativar audit de feedback enviado | communication |

### Infraestrutura (Prioridade: PÓS MVP)

| Item | Status |
|------|--------|
| API keys produção (Twilio, Resend, ATS) | Pendente |
| Elasticsearch + PGVector produção | Pendente |
| Bell notification (in-app) | Pendente |
| Bias Audit Dashboard (Four-Fifths Rule) | Pendente |
| EU AI Act Risk Classification | Pendente |
| LGPD DSR completo (export/delete) | Parcial |
| SOX Audit Export | Pendente |
| Predictive Analytics UI | Pendente |

---

*Documento gerado a partir do código real do lia-agent-system (Replit) e documentação specs existente. Complementa o `ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` com nível de detalhe técnico passo-a-passo por etapa.*
