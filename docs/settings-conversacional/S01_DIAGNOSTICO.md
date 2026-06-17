# S01 — Diagnóstico: Migração Settings Conversacional

**Data:** 2026-04-15  
**Versão:** 1.0.0  
**Status:** Diagnóstico completo — pré-requisito para implementação  
**Escopo:** Auditoria profunda do estado atual vs. proposta de migração do menu Configurações para modelo conversacional-first

---

## Sumário Executivo

A auditoria revelou que o domínio `company_settings` existe em código (domain, agent, tools, prompts) mas está **completamente desconectado** do runtime da plataforma. São **6 lacunas críticas** na cadeia de registro canônica que impedem o domínio de funcionar: import ausente no `__init__.py`, agent não carregado, sem routing, sem mapeamento LLM, sem capabilities.yaml, e sem permissões RBAC. Além disso, o frontend não possui context type para settings e o `HiringPoliciesHub` usa chat embutido próprio, não o UnifiedChat.

---

## Seção A — Mapa do Estado Atual dos Hubs Frontend

### A.1 CompanyTeamHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/CompanyTeamHub.tsx` |
| **Subseções reais** | Company Data, Departments, Benefits, Tech Stack, User Management |
| **Hooks** | `useCompanyData()`, `useDepartmentManagement()` |
| **Endpoints** | `GET/PATCH /api/backend-proxy/company/profile`, `GET/POST /api/backend-proxy/company/departments`, `GET /api/backend-proxy/company/users/list` |
| **Estado funcional** | Operacional — formulários tradicionais, sem integração conversacional |
| **Destino na migração** | Seções "Perfil da Empresa", "Cultura & EVP", "Tech Stack", "Benefícios" do modelo conversacional |

### A.2 RecruitmentHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/RecruitmentHub.tsx` |
| **Subseções reais** | Pipeline Configuration, Screening Questions, Hiring Policies (embeds HiringPoliciesHub) |
| **Hooks** | `useRecruitmentHub(activeSubsection)` |
| **Endpoints** | `GET /api/backend-proxy/company-pipeline`, `GET/POST /api/backend-proxy/company/screening-questions` |
| **Estado funcional** | Operacional — orquestra 3 tabs incluindo HiringPoliciesHub |
| **Destino na migração** | "Políticas de Contratação" já é conversacional; Pipeline e Screening migram como subseções |

### A.3 HiringPoliciesHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/HiringPoliciesHub.tsx` |
| **Subseções reais** | Chat Panel (esquerda) + Policy Dashboard (direita) — dual-interface |
| **Hooks** | `useHiringPolicies()` |
| **Endpoints** | `GET /api/backend-proxy/hiring-policy/progress`, `POST /api/backend-proxy/hiring-policy/chat`, `PATCH /api/backend-proxy/hiring-policy/block` |
| **Estado funcional** | **Único hub já conversacional** — modelo de referência para migração |
| **Destino na migração** | Mantém chat dedicado OU migra para UnifiedChat com context `settings_config` |
| **DECISÃO PENDENTE** | Chat embutido usa `LiaChatMessage` + `LiaChatInput` diretamente, NÃO o UnifiedChat. Migrar para UnifiedChat requer: (1) novo ChatContextType, (2) routing no backend, (3) preservação do sync bidirecional chat↔dashboard |

### A.4 CommunicationHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/CommunicationHub.tsx` |
| **Subseções reais** | Templates, Signature, Schedule, Alerts, A/B Testing |
| **Hooks** | `useCommunicationHub(activeSubsection)` |
| **Endpoints** | `GET /api/backend-proxy/email-templates`, `POST /api/backend-proxy/email-templates/generate`, `GET /api/backend-proxy/company/communication-settings`, `POST /api/backend-proxy/alerts/config` |
| **Estado funcional** | Operacional — formulários + geração AI de templates |
| **Destino na migração** | Subseção "Comunicação" — templates podem ser configurados via conversa |

### A.5 GoalsPlanningHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` |
| **Subseções reais** | Goals Management, Smart Import Zone, Workforce Section |
| **Hooks** | `useGoalsPlanningHub({ users, onGoalUpdate, activeSubsection })` |
| **Endpoints** | `POST /api/backend-proxy/goals/import`, `GET /api/backend-proxy/goals/import/template`, `GET /api/backend-proxy/goals/by-user` |
| **Estado funcional** | Operacional — importação de planilha + gestão manual |
| **Destino na migração** | "Planejamento de Contratações" — workforce via conversa + import inteligente |

### A.6 GlobalSearchHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/GlobalSearchHub.tsx` |
| **Subseções reais** | Limits, Options, Costs |
| **Hooks** | `useGlobalSearchSettings(onChangesUpdate)` |
| **Endpoints** | `GET/PATCH /api/backend-proxy/company/global-search-settings` |
| **Estado funcional** | Operacional — toggles e limites de crédito |
| **Destino na migração** | "Busca Global" — configuração simples, baixa prioridade conversacional |

### A.7 IntegrationsHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/IntegrationsHub.tsx` |
| **Subseções reais** | AI Models, ATS, Calendar, General Integrations |
| **Hooks** | React hooks padrão (`useState`, `useEffect`, `useCallback`, `useMemo`) |
| **Endpoints** | `GET /api/backend-proxy/calendar/health`, `GET /api/backend-proxy/integrations/status`, `GET /api/backend-proxy/llm-config`, `GET /api/backend-proxy/ats/connections`, `GET /api/backend-proxy/calendar/google/auth-url` |
| **Estado funcional** | Operacional — cards de status + drawer de detalhes |
| **Destino na migração** | "Integrações" — mantém UI visual, chat como suporte/troubleshooting |

### A.8 FairnessComplianceHub

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/settings/FairnessComplianceHub.tsx` |
| **Subseções reais** | Resumo de auditoria, gráficos (Recharts), export, StudioComplianceView |
| **Hooks** | `useState`, `useEffect` |
| **Endpoints** | `GET /api/backend-proxy/fairness-report/summary?days={period}`, `GET /api/backend-proxy/fairness-report/export?format={format}&days={period}` |
| **Estado funcional** | Operacional — dashboards de compliance |
| **Destino na migração** | Mantém como visualização; chat pode gerar explicações/relatórios sob demanda |

### A.9 Orquestração: settings-page-enhanced.tsx

| Item | Detalhe |
|------|---------|
| **Arquivo** | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| **Função** | Orquestra todos os 8 hubs acima como seções/tabs da página Settings |
| **Estado** | Funcional — menu lateral + conteúdo dinâmico por seção |

---

## Seção B — UnifiedChat: Capacidades Atuais

### B.1 Context Types Registrados

```typescript
// plataforma-lia/src/contexts/lia-float-context.tsx:55-60
export type ChatContextType =
  | "general"
  | "job_chat"
  | "talent_chat"
  | "kanban_chat"
  | "candidates_chat"
```

**GAP:** Não existe `settings_config` ou qualquer tipo para contexto de configurações. A migração requer adicionar ao menos um novo tipo.

### B.2 Mecanismo de switchChatContext

**Arquivo:** `plataforma-lia/src/contexts/lia-float-context.tsx:223-255`

O `switchChatContext` implementa:

1. **Preservação de conversationId por contexto** — usa `contextConversationMapRef` (Map<ChatContextType, string>) para salvar o conversationId atual antes de trocar
2. **Opções de switching:**
   - `conversationId` explícito — força ID específico
   - `continuePrevious: true` — restaura último conversationId do contexto destino
   - Default — limpa mensagens (`setChatMessages([])`) e inicia conversa nova
3. **Isolation** — cada contexto mantém histórico separado via mapa de referência

**ADEQUAÇÃO PARA MIGRAÇÃO:** O mecanismo é adequado. Basta adicionar `"settings_config"` ao type union e o switchChatContext funcionará automaticamente.

### B.3 Preservação de Histórico

- **In-memory:** `chatMessages` (React state) — limpo ao trocar contexto sem `continuePrevious`
- **Backend:** `loadChatHistory(id)` via `/api/backend-proxy/conversations/[id]/messages`
- **Mapa contextual:** `contextConversationMapRef` — persiste durante sessão, não entre reloads

**GAP:** Para settings, o histórico precisa persistir entre sessões (o recrutador volta dias depois para continuar configuração). Requer: (1) salvar `conversationId` do contexto settings no backend/localStorage, (2) carregar ao reabrir.

### B.4 Suggestions e Chips

- **Hook:** `useLiaSuggestions` (`plataforma-lia/src/hooks/ai/use-lia-suggestions.ts`)
- **Fonte:** `/api/backend-proxy/lia/suggestions`
- **Tipos:** Prompt Chips, Follow-up Suggestions, Wizard Chips
- **GAP:** Não existem suggestions específicas para contexto de settings. Precisa: chips como "Configurar perfil", "Atualizar cultura", "Importar benefícios".

### B.5 HiringPoliciesHub — Chat Embutido vs. UnifiedChat

O `HiringPoliciesHub` usa componentes de chat (`LiaChatMessage`, `LiaChatInput`) **diretamente**, sem passar pelo UnifiedChat:

- Chat comunica via `POST /api/backend-proxy/hiring-policy/chat` (endpoint dedicado)
- Dashboard sincroniza via `updated_fields` no response do chat
- Inline editing via `PATCH /api/backend-proxy/hiring-policy/block`

**DECISÃO ARQUITETURAL:** A migração para "Minha Empresa" pode:
- **Opção A:** Manter chat embutido dedicado (menor risco, duplicação de código)
- **Opção B:** Migrar para UnifiedChat com context `settings_config` (consistência, maior esforço)
- **Recomendação:** Opção B com fase intermediária — manter chat embutido enquanto implementa routing no UnifiedChat

---

## Seção C — Agente company_settings no Backend

### C.1 Domain (domain.py)

**Arquivo:** `lia-agent-system/app/domains/company_settings/domain.py`

| Aspecto | Estado |
|---------|--------|
| `@register_domain` | Presente (L78) — decorator existe |
| Herança `ComplianceDomainPrompt` | Sim — compliance by inheritance ativo |
| `_compliance_config` | `{'high_impact': False, 'fairness_action_type': 'data_check'}` |
| `domain_id` | `"company_settings"` |
| Actions definidas | 7: `configure_profile`, `configure_culture`, `configure_tech_stack`, `configure_benefits`, `configure_workforce`, `analyze_website`, `process_document` |
| `process_intent` | Usa `KeywordIntentMatcher` com fallback para `configure_profile` (conf=0.3) |
| `execute_action` | Stub — retorna sucesso genérico, delega ao agente ReAct |
| `capabilities.yaml` | **NÃO EXISTE** — `_capabilities_yaml_path` aponta para `config/capabilities.yaml` que não existe; faz fallback para dict vazio |

### C.2 Agent (company_react_agent.py)

**Arquivo:** `lia-agent-system/app/domains/company_settings/agents/company_react_agent.py`

| Aspecto | Estado |
|---------|--------|
| `@register_agent("company_settings")` | Presente (L35) — decorator existe |
| Base classes | `LangGraphReActBase`, `EnhancedAgentMixin` |
| Tools | Via `get_company_settings_tools()` + `_get_all_enhanced_tools()` |
| FairnessGuard | Instanciado (`self._fairness_guard = FairnessGuard()`) |
| WorkingMemory | Instanciado (`self._memory_service = WorkingMemoryService()`) |
| Confidence policy | Usa `confidence_policy_service` — base 0.75, com tools 0.82, erro 0.40 |
| Legacy support | `process_legacy_format()` para compatibilidade |

### C.3 Tool Registry (company_tool_registry.py)

**Arquivo:** `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py` (525 linhas)

| Tool | Função | FairnessGuard | Audit Log |
|------|--------|:---:|:---:|
| `get_company_profile` | Lê perfil + cultura + benefícios do DB | N/A (read) | Não |
| `save_company_field` | Salva campo individual (profile/culture) | Sim (L133-139) | **Não** |
| `save_company_section` | Salva múltiplos campos de uma seção | Sim (L194-201) | **Não** |
| `analyze_company_website` | Chama endpoint de análise via httpx | N/A | **Não** |
| `process_uploaded_document` | Processa texto com FairnessGuard | Sim (L274) | **Não** |
| `import_workforce_plan` | Importa plano de contratações | N/A | **Não** |
| `get_company_completion` | Calcula completude por seção | N/A (read) | N/A |

**GAPS IDENTIFICADOS:**
1. **Nenhuma tool tem audit logging** — `audit_service` não é chamado em nenhum save
2. **`save_company_field` não implementa tier system** — aceita qualquer campo válido sem distinção de imutabilidade (TIER 1), validação especial (TIER 2), livre (TIER 3) ou readonly (TIER 4)
3. **SQL injection potencial** — `save_company_field` usa f-string para nome de campo (`f"UPDATE company_profiles SET {field} = :value"`). Mitigado parcialmente pela validação de `valid_profile_fields`/`valid_culture_fields`, mas o padrão é inseguro
4. **Sem PII masking** — `pii_masking.py` não é integrado nas tools de save
5. **`analyze_company_website` faz chamada localhost** — `http://127.0.0.1:8001` hardcoded

### C.4 System Prompt (company_system_prompt.py)

**Arquivo:** `lia-agent-system/app/domains/company_settings/agents/company_system_prompt.py`

- Carrega de `app/prompts/domains/company_settings.yaml` via `PromptLoader`
- YAML existe e contém: `identity`, `scope_in`, `behavioral_rules`, `ethical_validation`, `system_prompt`
- Integra `ANTI_SYCOPHANCY_BLOCK` e `NEGATION_DETECTION_BLOCK`
- **ADEQUADO** — prompt bem estruturado com regras de compliance inline

---

## Seção D — Delta Completo: Proposta vs. Realidade

### D.1 As 6 Lacunas Críticas da Cadeia de Registro

| # | Lacuna | Arquivo | Evidência | Solução |
|---|--------|---------|-----------|---------|
| 1 | `company_settings` NÃO importado em `domains/__init__.py` | `lia-agent-system/app/domains/__init__.py` (35 linhas) | `grep -n "company_settings" __init__.py` retorna 0 matches. O arquivo importa 15 domínios (L1-34) — `CompanySettingsDomain` não está entre eles. Referência existente: `from app.domains.hiring_policy.domain import HiringPolicyDomain` (L14) | Adicionar `from app.domains.company_settings.domain import CompanySettingsDomain  # noqa: F401` após L14 |
| 2 | `CompanySettingsReActAgent` NÃO em `_ensure_agents_loaded()` | `lia-agent-system/app/api/v1/agent_chat_ws.py` (L328-367) | `grep -n "company_settings" agent_chat_ws.py` retorna 0 matches. A função importa 11 top-level agents (L339-349: Wizard, Pipeline, Sourcing, Talent, Kanban, JobsMgmt, Policy, PipelineTransition, Analytics, Communication, ATSIntegration) + 7 sub-agents (L352-365). `CompanySettingsReActAgent` não consta | Adicionar `from app.domains.company_settings.agents.company_react_agent import CompanySettingsReActAgent  # noqa: F401` após L349 |
| 3 | `company_settings` NÃO no `domain_routing.yaml` | `lia-agent-system/app/orchestrator/config/domain_routing.yaml` (317 linhas) | `grep -n "company_settings" domain_routing.yaml` retorna 0 matches. O arquivo define patterns para 20 domínios (L11-317): `job_management`, `sourcing`, `sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement`, `cv_screening`, `wsi_assessment`, `interviewing`, `scheduling`, `communication`, `kanban_search`, `kanban_insight`, `kanban_action`, `pipeline_context`, `pipeline_decision`, `pipeline_action`, `analytics`, `ats_integration`, `recruiter_assistant`, `task_planning`, `interview_scheduling`, `talent_pool`, `agent_studio`, `digital_twin`, `recruitment_campaign`. Nenhum para settings | Adicionar seção `company_settings:` após L317 com patterns: `"configura[rç].*empresa"`, `"perfil.*empresa"`, `"dados.*empresa"`, `"cultura.*empresa"`, `"benefícios.*empresa"`, `"tech.*stack"`, `"minha.*empresa"`. **ATENÇÃO:** pattern `"benefícios"` já existe em `job_management` (L29) — usar pattern mais específico `"benefícios\\s+(da\\s+)?empresa"` para evitar conflito |
| 4 | `company_settings` NÃO no `AGENT_TYPE_TO_DOMAIN` | `lia-agent-system/app/orchestrator/domain_mappings.py` (L8-36) | `grep -n "company_settings" domain_mappings.py` retorna 0 matches. O dict mapeia 30 agent types (L9-36) para domínios — nenhum para company_settings | Adicionar `"company_settings": "company_settings"`, `"company_profile": "company_settings"`, `"company_config": "company_settings"` após L36 |
| 5 | `capabilities.yaml` NÃO existe | `lia-agent-system/app/domains/company_settings/config/capabilities.yaml` | `ls lia-agent-system/app/domains/company_settings/config/` → diretório não existe. O `domain.py` (L16-21) tenta carregar mas faz fallback silencioso para dict vazio. Referência funcional: `lia-agent-system/app/domains/hiring_policy/config/capabilities.yaml` existe | Criar diretório `config/` e arquivo `capabilities.yaml` com `intent_keywords` para as 7 actions definidas em `domain.py` (L25-74) |
| 6 | `company_settings` NÃO em `tool_permissions.yaml` | `lia-agent-system/app/tools/tool_permissions.yaml` (231 linhas) | `grep -n "company_settings" tool_permissions.yaml` retorna 0 matches. O arquivo define 5 scopes (L4-171: `talent_funnel`, `job_table`, `in_job`, `global`, `universal`) + 28 restricted tools (L183-228). Nenhuma referência a tools de company_settings (`get_company_profile`, `save_company_field`, etc.) | Adicionar scope `company_settings:` com query (`get_company_profile`, `get_company_completion`) e action (`save_company_field`, `save_company_section`, `analyze_company_website`, `process_uploaded_document`, `import_workforce_plan`). Adicionar `save_company_field` e `save_company_section` à lista `restricted_tools` (L183+) |

### D.2 Gaps Funcionais Adicionais

| # | Gap | Detalhe | Estimativa |
|---|-----|---------|------------|
| 7 | `save_company_field` sem tier system | Não distingue campos imutáveis (CNPJ) vs livres (website). Proposta prevê TIER 1-4 | 4h |
| 8 | Sem audit logging nas tools | `audit_service.py` existe mas nenhuma tool de company_settings o chama | 2h |
| 9 | `settings_progress.py` hardcodes | `communication_score=100` (L114), `goals_planning_score=100` (L118) — sempre 100% independente do estado real | 3h |
| 10 | `ChatContextType` sem `settings_config` | Frontend só tem 5 tipos; não inclui contexto para settings | 1h |
| 11 | Sem suggestions/chips para settings | `useLiaSuggestions` não tem lógica para contexto de configuração | 2h |
| 12 | HiringPoliciesHub com chat próprio | Usa `LiaChatMessage`/`LiaChatInput` direto, não UnifiedChat | 8h (migração), 0h (manter) |
| 13 | Sem PII masking nas tools de save | `pii_masking.py` não integrado no fluxo de salvamento | 2h |
| 14 | URL hardcoded em `analyze_company_website` | `http://127.0.0.1:8001` não funciona em produção | 0.5h |
| 15 | Fallback de erro em `settings_progress.py` | Retorna scores fixos (overall=50, company-team=60, etc.) mascarando erros reais | 1h |

### D.3 Comparativo: hiring_policy (funcional) vs. company_settings (desconectado)

| Aspecto | hiring_policy | company_settings |
|---------|:---:|:---:|
| Import em `__init__.py` | Sim (L14) | **Não** |
| Agent em `_ensure_agents_loaded` | Sim — `PolicyReActAgent` (L345) | **Não** |
| `domain_routing.yaml` | N/A (usa chat dedicado) | **Não** |
| `AGENT_TYPE_TO_DOMAIN` | N/A | **Não** |
| `capabilities.yaml` | Sim (`hiring_policy/config/capabilities.yaml`) | **Não** |
| `tool_permissions.yaml` | N/A (chat dedicado) | **Não** |
| FairnessGuard | Sim — agent + tools | Sim — agent + tools (parcial) |
| Audit logging | Parcial | **Não** |
| Chat integrado | Sim (embutido no hub) | **Não** (nenhum chat) |

---

## Seção E — Dependências e Riscos

### E.1 Camadas Crossfunction

| Camada | Status no company_settings |
|--------|---------------------------|
| **ComplianceDomainPrompt** | Integrado — `CompanySettingsDomain` herda de `ComplianceDomainPrompt` |
| **FairnessGuard** | Parcialmente integrado — `save_company_field` e `save_company_section` checam bias em strings > 10 chars; `process_uploaded_document` também checa |
| **C3b Layer** | **NÃO INTEGRADO** — `c3b_layer.py` só aplica FairnessGuard a domínios sensíveis (recruitment, talent_ranking, job_scoring). `company_settings` não está na lista de alvos |
| **PII Masking** | **NÃO INTEGRADO** — nenhuma tool usa `pii_masking.py` |
| **Audit Service** | **NÃO INTEGRADO** — nenhuma operação de escrita chama `audit_service` |
| **Prompt Injection Guard** | Integrado via `ComplianceDomainPrompt` (Layer 3 Pre) |
| **RBAC / ToolPermissions** | **NÃO INTEGRADO** — tools existem fora do sistema de permissões |

### E.2 Componentes Compartilhados Impactados

| Componente | Impacto |
|-----------|---------|
| `lia-float-context.tsx` | Precisa adicionar `"settings_config"` ao `ChatContextType` union |
| `settings-page-enhanced.tsx` | Precisa integrar UnifiedChat sidebar/embutido |
| `useLiaChatConnection` | Nenhum — já suporta `domain` parameter no `sendMessage` |
| `domain_routing.yaml` | Precisa de novos patterns (nenhum conflito com existentes) |
| `agent_chat_ws.py` | Precisa de 1 linha de import |
| `domains/__init__.py` | Precisa de 1 linha de import |

### E.3 Riscos

| # | Risco | Severidade | Mitigação |
|---|-------|:---:|-----------|
| R1 | Routing ambíguo — "benefícios" já está em `job_management` patterns | Alta | Usar patterns mais específicos: `"benefícios.*empresa"` vs `"benefícios.*vaga"` |
| R2 | SQL injection via f-string em `save_company_field` | Média | Validação de campo já mitiga, mas refatorar para usar ORM/mapping dict |
| R3 | Perda de histórico ao trocar contexto settings ↔ general | Baixa | Implementar persistência do conversationId em localStorage |
| R4 | Breaking change no `ChatContextType` | Baixa | Type union é extensível; componentes que não usam settings_config não são afetados |
| R5 | Performance — adicionar mais patterns ao `domain_routing.yaml` | Baixa | FastRouter é O(n) patterns, ~20 patterns adicionais são negligíveis vs 318 existentes |

### E.4 Endpoints Rails (ats-api-copia) — Compatibilidade

| Recurso | Model | Controller | Status |
|---------|-------|-----------|--------|
| Company Profiles | `app/models/company_profile.rb` | `app/controllers/v1/users/company_profiles_controller.rb` | Existe — CRUD completo |
| Departments | `app/models/department.rb` | `app/controllers/v1/users/departments_controller.rb` | Existe — com hierarquia |
| Benefits | `app/models/benefit.rb` | N/A (via CompanyProfile `has_many`) | Existe — sem controller dedicado |
| Culture | `app/models/culture_value.rb` | N/A (via CompanyProfile) | Existe — sem controller dedicado |
| Workforce | `app/models/workforce_entry.rb`, `hiring_plan.rb`, `planned_headcount.rb` | N/A | Existe — sem controller REST dedicado |

**GAP CRÍTICO (GATE ARQUITETURAL):** As tools do `company_tool_registry.py` acessam o banco PostgreSQL diretamente via SQLAlchemy, **não** os endpoints Rails. Isso significa que dados salvos pelo agent podem estar **desincronizados** com o ats-api-copia. Esta decisão é **bloqueante antes de qualquer implementação de persistência conversacional**:

- **Opção A — Agent DB como fonte de verdade:** Todas as tools leem/escrevem no PostgreSQL do agent-system. O ats-api-copia sincroniza via evento/webhook.
- **Opção B — Rails API como fonte de verdade:** Tools chamam endpoints REST do ats-api-copia em vez de SQL direto. Mais seguro mas mais lento.
- **Opção C — Dual-write com reconciliação:** Escreve em ambos com job de reconciliação. Mais complexo.
- **Estado atual:** Opção A (implícita, sem sync). Precisa de decisão explícita antes de Fase 1.

---

## Seção F — Plano de Implementação Revisado

### Pré-requisito: Decisão Arquitetural — Single Source of Truth
**GATE BLOQUEANTE** antes de Fases 1-4: definir se a fonte de verdade dos dados de empresa é o PostgreSQL do agent-system ou o Rails API (ats-api-copia). Ver Seção E.4 para opções.

### Fase 0 — Registro Canônico (BLOQUEANTE)
**Estimativa:** 2h  
**Dependências:** Nenhuma  
**Prioridade:** P0 — sem isso, nada funciona

| # | Ação | Arquivo | Tipo |
|---|------|---------|------|
| F0.1 | Adicionar `from app.domains.company_settings.domain import CompanySettingsDomain  # noqa: F401` | `app/domains/__init__.py` | 1 linha |
| F0.2 | Adicionar import do `CompanySettingsReActAgent` em `_ensure_agents_loaded()` | `app/api/v1/agent_chat_ws.py` | 1 linha |
| F0.3 | Adicionar seção `company_settings:` com patterns regex | `app/orchestrator/config/domain_routing.yaml` | ~15 linhas |
| F0.4 | Adicionar mappings `"company_settings"`, `"company_profile"`, `"company_config"` | `app/orchestrator/domain_mappings.py` | 3 linhas |
| F0.5 | Criar `app/domains/company_settings/config/capabilities.yaml` | Novo arquivo | ~30 linhas |
| F0.6 | Adicionar scope `company_settings` + restricted tools | `app/tools/tool_permissions.yaml` | ~20 linhas |

### Fase 1 — Tier System e Compliance nas Tools
**Estimativa:** 8h  
**Dependências:** Fase 0  
**Prioridade:** P1

| # | Ação | Arquivo |
|---|------|---------|
| F1.1 | Implementar tier system em `save_company_field`: TIER 1 (imutável: CNPJ), TIER 2 (validação: website, email), TIER 3 (livre), TIER 4 (readonly: id, created_at) | `company_tool_registry.py` |
| F1.2 | Integrar `audit_service` em todas as operações de escrita | `company_tool_registry.py` |
| F1.3 | Integrar `pii_masking` no fluxo de documentos | `company_tool_registry.py` |
| F1.4 | Refatorar f-string SQL para dict-mapping seguro | `company_tool_registry.py` |
| F1.5 | Substituir URL hardcoded por `settings.BACKEND_URL` | `company_tool_registry.py` |

### Fase 2 — Frontend: Context Type e Integração UnifiedChat
**Estimativa:** 8h  
**Dependências:** Fase 0  
**Prioridade:** P1

| # | Ação | Arquivo |
|---|------|---------|
| F2.1 | Adicionar `"settings_config"` ao `ChatContextType` | `lia-float-context.tsx` |
| F2.2 | Implementar auto-switch para `settings_config` ao entrar em Settings page | `settings-page-enhanced.tsx` |
| F2.3 | Adicionar persistência do conversationId de settings em localStorage | `lia-float-context.tsx` |
| F2.4 | Criar suggestions/chips para contexto settings | Backend + `useLiaSuggestions` |
| F2.5 | Implementar sidebar chat na Settings page (usando UnifiedChat mode=sidebar) | `settings-page-enhanced.tsx` |

### Fase 3 — Correção de settings_progress.py
**Estimativa:** 4h  
**Dependências:** Nenhuma (pode ser paralela)  
**Prioridade:** P2

| # | Ação | Arquivo | Detalhe |
|---|------|---------|---------|
| F3.1 | Remover `communication_score = 100` hardcoded (L114) | `settings_progress.py` | Calcular com base em templates + notification rules reais |
| F3.2 | Remover `goals_planning_score = 100` hardcoded (L118) | `settings_progress.py` | Calcular com base em goals definidos + workforce plan |
| F3.3 | Remover fallback de erro com scores fixos (L174-197) | `settings_progress.py` | Retornar 0 em todas as seções + flag `error: true` |
| F3.4 | Adicionar seções faltantes: hiring_policies, integrations, fairness_compliance | `settings_progress.py` | Incluir no cálculo overall com pesos ajustados |

### Fase 4 — Migração dos Cards de Políticas para "Minha Empresa"
**Estimativa:** 12h  
**Dependências:** Fase 2  
**Prioridade:** P2

| # | Ação |
|---|------|
| F4.1 | Decidir: manter chat embutido do HiringPoliciesHub OU migrar para UnifiedChat |
| F4.2 | Se migrar: implementar routing do UnifiedChat para endpoint `/hiring-policy/chat` quando context=settings_config + subseção=policies |
| F4.3 | Implementar sync bidirecional: UnifiedChat response → policy dashboard update |
| F4.4 | Manter inline editing via PATCH como fallback |

### Fase 5 — Polish e Documentação
**Estimativa:** 4h  
**Dependências:** Fases 1-4  
**Prioridade:** P3

| # | Ação |
|---|------|
| F5.1 | Adicionar `company_settings` à lista de domínios do C3b layer (se aplicável) |
| F5.2 | Testes E2E: routing → agent → tools → save → progress update |
| F5.3 | Documentar decisões arquiteturais (chat embutido vs UnifiedChat) |

### Cronograma Resumido

| Fase | Estimativa | Paralela? | Bloqueada por |
|------|-----------|:---------:|:---:|
| Fase 0 — Registro Canônico | 2h | — | — |
| Fase 1 — Tier System + Compliance | 8h | Sim (com F2) | F0 |
| Fase 2 — Frontend Context + Chat | 8h | Sim (com F1) | F0 |
| Fase 3 — settings_progress.py | 4h | Sim (independente) | — |
| Fase 4 — Migração Políticas | 12h | Não | F2 |
| Fase 5 — Polish | 4h | Não | F1, F2, F3, F4 |
| **Total** | **~30h** (com paralelismo: ~22h) | | |

---

## Anexo: Validação de Arquivos

Cada arquivo listado na proposta original foi verificado quanto à existência:

| Arquivo | Existe? | Observação |
|---------|:---:|-----------|
| `app/domains/company_settings/domain.py` | Sim | 133 linhas, `@register_domain` presente |
| `app/domains/company_settings/agents/company_react_agent.py` | Sim | 145 linhas, `@register_agent` presente |
| `app/domains/company_settings/agents/company_tool_registry.py` | Sim | 525 linhas, 7 tools definidas |
| `app/domains/company_settings/agents/company_system_prompt.py` | Sim | 70 linhas, carrega YAML |
| `app/domains/company_settings/config/capabilities.yaml` | **Não** | Diretório `config/` não existe |
| `app/domains/__init__.py` | Sim | `company_settings` **não importado** |
| `app/api/v1/agent_chat_ws.py` | Sim | `CompanySettingsReActAgent` **não carregado** |
| `app/orchestrator/domain_mappings.py` | Sim | `company_settings` **não mapeado** |
| `app/orchestrator/config/domain_routing.yaml` | Sim | `company_settings` **não presente** |
| `app/tools/tool_permissions.yaml` | Sim | `company_settings` **não registrado** |
| `app/api/v1/settings_progress.py` | Sim | 198 linhas, 2 hardcodes confirmados |
| `app/shared/compliance/fairness_guard.py` | Sim | 3 camadas: explícita, implícita, semântica |
| `app/shared/compliance/c3b_layer.py` | Sim | `company_settings` **não nos alvos** |
| `app/shared/compliance/audit_service.py` | Sim | Funcional, não utilizado por company_settings |
| `app/shared/pii_masking.py` | Sim | 4 camadas, não integrado em company_settings |
| `app/domains/compliance_base.py` | Sim | CompanySettingsDomain herda corretamente |
| `app/prompts/domains/company_settings.yaml` | Sim | Prompt completo com identity, rules, ethical |
| `plataforma-lia/src/components/settings/CompanyTeamHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/RecruitmentHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/HiringPoliciesHub.tsx` | Sim | Chat embutido próprio |
| `plataforma-lia/src/components/settings/CommunicationHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/GlobalSearchHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/IntegrationsHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/settings/FairnessComplianceHub.tsx` | Sim | Funcional |
| `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` | Sim | Orquestrador |
| `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` | Sim | Funcional |
| `plataforma-lia/src/contexts/lia-float-context.tsx` | Sim | 543 linhas, switchChatContext em L223 |
| `plataforma-lia/src/hooks/chat/useChatMessages.ts` | Sim | + versão em chat-page/chat-core/ |
| `plataforma-lia/src/hooks/company/use-hiring-policies.ts` | Sim | Funcional |
| `plataforma-lia/src/hooks/settings/useCompanyData.ts` | Sim | Funcional |
| `plataforma-lia/src/utils/permissions.ts` | Sim | + versão em lib/permissions.ts |
| `ats-api-copia/app/models/company_profile.rb` | Sim | Funcional |
| `ats-api-copia/app/controllers/v1/users/company_profiles_controller.rb` | Sim | CRUD completo |
