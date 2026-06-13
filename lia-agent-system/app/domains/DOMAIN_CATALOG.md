# LIA Platform — Domain Catalog

Classification of all directories under `app/domains/`.
Support files (`base.py`, `compliance_base.py`, `registry.py`, `workflow.py`) não são listados.

## Classification Criteria

| Type | Criteria | Count |
|------|----------|-------|
| **Agentic** | `domain.py` com `@register_domain`, roteável pelo CascadedRouter, tem `agents/` com ReActAgent | 16 |
| **Special Agentic** | `domain.py` com `@register_domain`, arquitetura não-padrão (LangGraph nodes ou platform) | 2 |
| **Micro-Action** | `domain.py` com `@register_domain`, ≤10 arquivos, sem `agents/` | 2 |
| **Service** | Sem `domain.py` — apenas `services/` e `repositories/`, não roteável | 12 |
| **Agent Studio em Desenvolvimento** | Sem `domain.py` — lógica de serviço pronta; serão custom agents no Agent Studio | 4 |
| **Orphaned/Minimal** | Sem roteamento ativo ou stub mínimo sem implementação real | 2 |

**Total: 38 diretórios de domínio.**

---

## Agentic Domains (16)

Registrados no `DomainRegistry` via `@register_domain`. Roteáveis pelo CascadedRouter.
Implementação completa com `agents/` (ReActAgent), `services/`, `tools/` e `domain.py`.

| Domain | `domain_id` | Arquivos | Descrição |
|--------|-------------|----------|-----------|
| `analytics` | `analytics` | 161 | Analytics de recrutamento, relatórios, dashboards de KPIs |
| `ats_integration` | `ats_integration` | 60 | Integração e sincronização com sistemas ATS externos (Gupy, Pandapé, Merge) |
| `automation` | `automation` | 82 | Tarefas, lembretes, notas e automação de fluxos de trabalho |
| `candidate_self_service` | `candidate_self_service` | 35 | Portal de autoatendimento: candidato consulta status do próprio processo seletivo (LGPD Art. 20) |
| `communication` | `communication` | 172 | Mensageria multicanal: e-mail, WhatsApp, Teams |
| `company_settings` | `company_settings` | 23 | Configurações institucionais da empresa via chat (CompanySettingsReActAgent); dados, cultura, benefícios, workforce planning |
| `cv_screening` | `cv_screening` | 194 | Análise de currículo, avaliação WSI, scoring de candidatos |
| `hiring_policy` | `hiring_policy` | 29 | Entry point de roteamento conversacional para tópicos de política de contratação. **Delega ao motor real em `policy/`** — não contém lógica de negócio própria |
| `interview_scheduling` | `interview_scheduling` | 51 | Agendamento de entrevistas e integração com calendários |
| `job_management` | `job_management` | 175 | Ciclo de vida de vagas: CRUD, pipeline, configuração, publicação |
| `offer` | `offer` | 33 | Ciclo de vida de cartas-oferta: criação, edição, envio ao candidato, cancelamento |
| `pipeline` | `pipeline_transition` | 59 | Visualização de pipeline e movimentação de candidatos entre etapas |
| `policy` | `policy` | 28 | **Motor canônico de políticas de contratação.** `PolicyEngineService` (BusinessRule / RateLimitRule / EscalationRule), `PolicySetupAgent` (setup via chat), FairnessGuard setorial (`ALPHA1_SECTOR_RULES`). Toda lógica nova de política vai aqui — **nunca em `hiring_policy/`** |
| `recruiter_assistant` | `recruiter_assistant` | 101 | Assistente geral de recrutamento (domínio de fallback do CascadedRouter) |
| `sourcing` | `sourcing` | 129 | Sourcing de candidatos em múltiplos canais (Pearch, Apify, LinkedIn, banco interno) |
| `talent_pool` | `talent_pool` | 23 | Gestão de pools de talentos: criação, listagem, movimentação de candidatos |

> **Nota `hiring_policy` vs `policy`:** `hiring_policy/` é um entry point fino (~40 LOC) que apenas roteia intenções conversacionais. O motor real — regras de negócio, FairnessGuard, `PolicySetupAgent`, `PolicyEngineService` — vive integralmente em `policy/`. Qualquer lógica nova vai em `policy/`.

---

## Special Agentic Domains (2)

Registrados no `DomainRegistry` via `@register_domain` e roteáveis, mas com arquitetura interna não-padrão.

| Domain | `domain_id` | Arquivos | Arquitetura | Descrição |
|--------|-------------|----------|-------------|-----------|
| `agent_studio` | `agent_studio` | 27 | Platform domain — sem `agents/` internos; contém `custom_agent_runtime.py`, `actions.py` | Plataforma de criação e gerenciamento de agentes customizados por tenant. É o próprio sistema que hospeda outros agentes |
| `job_creation` | `job_creation` | 167 | LangGraph wizard — usa `nodes/` + `orchestrator/` + `graph.py` em vez de `agents/`. Fluxo linear com 15 nós e 4 gates HITL | Wizard de criação de vaga. **Fluxo canônico inviolável** — Plan & Execute nunca cria vaga. Detalhes: `docs/architecture/wizard-flow.md` |

---

## Micro-Action Domains (2)

Registrados no `DomainRegistry`. Implementação mínima: apenas `domain.py` + `actions.py`. Sem `agents/`, `services/` ou `tools/`.

| Domain | `domain_id` | Arquivos | Descrição |
|--------|-------------|----------|-----------|
| `digital_twin` | `digital_twin` | 7 | Criação e avaliação de digital twin de candidato |
| `recruitment_campaign` | `recruitment_campaign` | 7 | Campanhas de recrutamento multi-etapa |

---

## Service Domains (12)

Proveem acesso a dados e lógica de negócio via `services/` e `repositories/`.
**Não têm `domain.py`** — não são roteáveis pelo CascadedRouter.

| Domain | Arquivos | Descrição |
|--------|----------|-----------|
| `ai` | 64 | Serviços LLM, cache de resposta, pipeline RAG, gerenciamento de prompts |
| `billing` | 32 | Assinaturas e cobrança |
| `candidates` | 30 | CRUD de candidatos e serviços de perfil |
| `company` | 74 | Configurações e perfil de empresa (dados brutos; lógica conversacional em `company_settings/`) |
| `compliance` | 9 | Registros de auditoria de compliance |
| `consent` | 9 | Registros de consentimento do usuário (LGPD) |
| `credits` | 18 | Rastreamento de consumo de créditos/tokens por tenant |
| `integrations_hub` | 22 | Hub central de integrações externas (catálogo, status, configuração) |
| `lgpd` | 32 | Proteção de dados, purge LGPD/GDPR, compliance Art. 16 |
| `modules` | 12 | Feature gating — controle de acesso a módulos por tier/tenant |
| `persona` | 10 | Gerenciamento de personas da LIA por tenant |
| `recruitment` | 54 | Dados e fluxos do processo seletivo |

---

## Agent Studio em Desenvolvimento (4)

Lógica de serviço substancial já implementada. **Não têm `domain.py` por decisão arquitetural**: serão criados como agentes customizados no Agent Studio (`agent_studio` domain), sem promover ao namespace de agentic domains canônicos (preserva o inventário sentinela de 16 ReActAgents em `test_tenant_aware_rollout_t_d.py`).

| Domain | Arquivos | Conteúdo atual | Plano |
|--------|----------|----------------|-------|
| `interview_intelligence` | 20 | `services/`: bias_detector, comparative_analysis, feedback_generator, interview_wsi, strategic_opinion, transcription | Agente de inteligência de entrevistas no Agent Studio |
| `talent_intelligence` | 22 | `services/`: skills_ontology_engine. `tools/`: candidate_nurture, internal_mobility, interview_intelligence_tools, market_intelligence, skills_ontology, workforce_planning | Agente de inteligência de talentos no Agent Studio |
| `voice` | 40 | `services/`: gemini_live_audio, voice_core_orchestrator, voice_screening, voice_service, realtime_credit_session. `plugins/`: data_collection, studio_voice, wsi_voice. `protocols/`: voice_core_plugin | Agente de triagem por voz no Agent Studio |
| `workforce` | 13 | `agents/`: workforce_tool_registry. `services/`: headcount_import_service | Agente de planejamento de workforce no Agent Studio |

---

## Orphaned / Minimal (2)

| Domain | Arquivos | Status |
|--------|----------|--------|
| `autonomous` | 4 | **Código órfão.** O Tier 6 do CascadedRouter foi removido (Sprint 12.3-B). `AUTONOMOUS_REACT_ENABLED` nunca foi SET em prod (invocações = 0). `_route_via_autonomous_agent` e `autonomous_react_agent.py` foram removidos em Sprint 12.6. O diretório `agents/` ainda existe mas **não é roteado por nenhum caller ativo**. Candidato a remoção |
| `triagem` | 5 | **Stub mínimo.** Contém apenas `__init__.py` + `repositories/` sem serviços ou agentes. Sem roteamento |
