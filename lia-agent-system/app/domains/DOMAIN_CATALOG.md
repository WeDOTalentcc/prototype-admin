# LIA Platform — Domain Catalog

Classification of all directories under `app/domains/`.
Support files (`base.py`, `compliance_base.py`, `registry.py`, `workflow.py`) não são listados.

## Classification Criteria

| Type | Criteria | Count |
|------|----------|-------|
| **Agentic** | `domain.py` com `@register_domain`, roteável pelo CascadedRouter, tem `agents/` com ReActAgent | 15 |
| **Special Agentic** | `domain.py` com `@register_domain`, arquitetura não-padrão (LangGraph nodes ou platform) | 2 |
| **Micro-Action** | `domain.py` com `@register_domain`, ≤10 arquivos, sem `agents/` | 2 |
| **Service** | Sem `domain.py` — apenas `services/` e `repositories/`, não roteável | 13 |
| **Agent Studio em Desenvolvimento** | Sem `domain.py` — lógica de serviço pronta; serão custom agents no Agent Studio | 4 |
| **Orphaned/Minimal** | Sem roteamento ativo ou stub mínimo sem implementação real | 0 |

**Total: 36 diretórios de domínio.**

---

## Agentic Domains (15)

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
| `hiring_policy` | `hiring_policy` | 29 | Domínio canônico de política de contratação. `HiringPolicyDomain` com 8 actions, `KeywordIntentMatcher`, `HiringPolicyRepository`. Consome `PolicyEngineService` de `policy/` |
| `interview_scheduling` | `interview_scheduling` | 51 | Agendamento de entrevistas e integração com calendários |
| `job_management` | `job_management` | 175 | Ciclo de vida de vagas: CRUD, pipeline, configuração, publicação |
| `offer` | `offer` | 33 | Ciclo de vida de cartas-oferta: criação, edição, envio ao candidato, cancelamento |
| `pipeline` | `pipeline_transition` | 58 | Visualização de pipeline e movimentação de candidatos entre etapas |
| `recruiter_assistant` | `recruiter_assistant` | 101 | Assistente geral de recrutamento (domínio de fallback do CascadedRouter) |
| `sourcing` | `sourcing` | 127 | Sourcing de candidatos em múltiplos canais (Pearch, Apify, LinkedIn, banco interno) |
| `talent_pool` | `talent_pool` | 23 | Gestão de pools de talentos: criação, listagem, movimentação de candidatos |

> **Nota `hiring_policy` + `policy/`:** `hiring_policy/` é o domain registrado no DomainRegistry (`domain_id="hiring_policy"`), com `HiringPolicyDomain`, agents, tools e repos completos. `policy/` é um Service Domain (sem `domain.py`) que contém o motor de regras — `PolicyEngineService`, `PolicySetupAgent`, FairnessGuard setorial — consumido por `hiring_policy/` e outros domínios.

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

## Service Domains (13)

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
| `modules` | 11 | Feature gating — controle de acesso a módulos por tier/tenant |
| `persona` | 10 | Gerenciamento de personas da LIA por tenant |
| `policy` | 14 | **Motor canônico de políticas de contratação.** `PolicyEngineService` (BusinessRule / RateLimitRule / EscalationRule), `PolicySetupAgent` (setup via chat), FairnessGuard setorial (`ALPHA1_SECTOR_RULES`). Consumido por `hiring_policy/`, `job_creation/`, `orchestrator/`, `fairness_guard` |
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

## Orphaned / Minimal (0)

Nenhum. `autonomous/` e `triagem/` removidos (Sprint 13 cleanup).

---

## Changelog

- **Sprint 13 (2026-06-13):** Removidos `autonomous/` e `triagem/` (órfãos). Consolidado `policy` → `hiring_policy` (domain_id único). Removidos 4 dead-code items: `pipeline/kanban_assistant_service.py`, `sourcing/tools.py`, `sourcing/prompts.py`, `modules/routes/`. Adicionado `__domain_type__` a 8 domínios. Removidos diretórios vazios pós-T14. Total: 38 → 36 domínios.
