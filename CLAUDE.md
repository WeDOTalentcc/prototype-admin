# LIA Platform — Instruções para Claude Code

> Leia este arquivo no início de cada conversa. Ele define o contexto completo da plataforma.

---

## Identidade da Plataforma

**LIA (Learning Intelligence Assistant)** — Plataforma B2B SaaS multi-tenant de recrutamento e seleção com IA.
Empresa: **WeDOTalent** ← escrever SEMPRE assim (nunca "Wedo Talent", "WeDo Talent" ou variações).

### Mercado Alvo
Todos os segmentos, com maior potencial em:
- **Alto volume**: varejo, logística, call centers — nenhum player nacional resolve completamente
- **RPO white-label**: consultorias de RH multi-cliente (mercado RPO cresce 6,62% a.a.)
- **Empresas que precisam escalar triagem e avaliação** sem aumentar equipe de recrutamento

### Compliance
Plataforma homologada para instituições financeiras reguladas: LGPD, BCB 498, SOX, ISO 27001, EU AI Act.

---

## Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend (atual) | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui (Radix UI) |
| Frontend (futuro) | Vue 3 + Vuetify 3 + Nuxt 3 + Pinia ← preparar código para migração |
| Backend (atual) | FastAPI (Python 3.11), SQLAlchemy 2.0 async, Alembic |
| Backend (permanente) | FastAPI / Python — stack definitiva, sem migração planejada |
| Banco de Dados | PostgreSQL (Neon) + pgvector, Redis (cache/sessão), RabbitMQ (filas) |
| IA/Agentes | LangGraph + LangChain, Claude Sonnet 4.5 (Anthropic) primário |
| Tarefas Async | Celery 5.4 |
| Auth | WorkOS (SSO/SCIM) |
| Deploy | Docker Compose (BE) + Netlify (FE) |

---

## Arquitetura em Camadas

```
Frontend (Next.js)  →  API Proxy (/api/backend-proxy/*)
         ↓
Backend (FastAPI)   →  Orchestrator Layer
         ↓
Agent Layer (LangGraph ReAct Agents — 7 domínios):
  Wizard | Pipeline | Sourcing | Talent | JobsManagement | Kanban | Policy
         ↓
Shared Services → Communication → Persistence
```

---

## Estrutura de Diretórios Chave

```
/home/runner/workspace/
├── lia-agent-system/           ← BACKEND
│   └── app/
│       ├── api/v1/             ← 362 endpoints REST
│       ├── models/             ← 95 modelos SQLAlchemy
│       ├── services/           ← 230+ serviços
│       ├── domains/            ← DDD: sourcing, job_management, pipeline, etc.
│       ├── shared/agents/      ← Infraestrutura de agentes (nodes, state_machine)
│       ├── tools/              ← Tool registry (candidate, job, communication, etc.)
│       └── core/               ← Config, DB, logging
├── plataforma-lia/             ← FRONTEND
│   └── src/
│       ├── app/                ← 85+ páginas Next.js (App Router)
│       │   └── api/            ← 362 rotas proxy
│       ├── components/         ← 437 componentes
│       └── hooks/              ← 60+ hooks
├── .agents/skills/             ← SKILLS completas (Replit/Claude Code)
├── .cursor/rules/              ← SKILLS condensadas para Cursor IDE (.mdc)
└── docs/                       ← Documentação completa
    ├── architecture/           ← C4, arquitetura completa, ADRs
    ├── integracao/             ← INVENTARIO_FERRAMENTAS_INTEGRACOES.md ← REFERÊNCIA
    ├── compliance/             ← LGPD, SOC2, ISO 27001
    └── analises/               ← Gaps, QA, diagnósticos
```

---

## Skills Disponíveis (`.agents/skills/`)

**Portabilidade:** cada skill tem versão completa em `.agents/skills/` (Replit/Claude Code) e versão condensada em `.cursor/rules/` (Cursor IDE).

### Skills de Desenvolvimento
| Skill | Quando Usar |
|-------|-------------|
| `/feature-impact` | ANTES de implementar qualquer feature/ajuste. Mapeia impacto em 12 dimensões. |
| `/feature-audit` | DEPOIS de implementar. Auditoria de 14 dimensões antes de marcar como concluído. |
| `/vue-migration-prep` | Ao criar/refatorar componentes FE. Garante estrutura compatível com Vue/Vuetify. |
| `/design-standardize` | Ao criar/ajustar UI. Aplica Design System v4.2.1 (90/10, tokens, acessibilidade). |
| `/testing-patterns` | Ao criar endpoints, componentes ou agentes. Pirâmide 5 camadas: Jam.dev → Unit → Integração → E2E → Fairness. |

### Skills de Governança e Compliance (Guia v3.4)
| Skill | Quando Usar |
|-------|-------------|
| `/wedo-governance` | Verificar compliance com 13 Crenças, Inegociáveis, Production Readiness (18 critérios) e governança de agentes IA. Usar em qualquer feature nova ou revisão estrutural. |
| `/screening-compliance` | Ao criar/modificar pipelines de screening, avaliação WSI, pre-qualification, feedback ao candidato. Cobre fairness, red teaming, model drift. |
| `/dei-fairness` | Ao criar/modificar funcionalidades de avaliação, ranking, filtragem ou comunicação com candidatos. Cobre FairnessGuard (3 camadas) e Bias Audit. |
| `/lgpd-data-protection` | Ao criar/modificar funcionalidades que coletam, processam ou transmitem dados pessoais. Cobre LGPD, EU AI Act, SOC-2/SOX/ISO-27001/BCB-498. |

**Fluxo padrão de desenvolvimento:**
1. `/feature-impact` → mapear impactos + aprovar plano
2. Implementar
3. `/vue-migration-prep` → verificar portabilidade do código FE
4. `/design-standardize` → validar conformidade visual
5. `/testing-patterns` → garantir cobertura das 5 camadas
6. `/feature-audit` → auditoria final antes de marcar concluído

**Skills de compliance adicionais (usar quando relevante):**
- Features com IA/avaliação → `/wedo-governance` + `/dei-fairness`
- Features com dados de candidatos → `/lgpd-data-protection`
- Features com screening/WSI → `/screening-compliance`

---

## Design System v4.2.1

**Arquivo canônico:** `plataforma-lia/docs/design-system/00-design-system-v4.md`

Princípios fundamentais:
- **90% monocromático** (grays) + **10% acento WeDo**
- Botões primários: preto (`bg-gray-900`). Cyan (`#60BED1`) apenas para elementos LIA (brain icon)
- Tipografia: Open Sans 85% (UI geral) + Inter 10% (dados/números) + JetBrains Mono 5% (código)
- Border radius: `rounded-md` (8px) padrão universal — botões/inputs/cards/modais
- Sem sombras (`box-shadow`): bordas substituem sombras para separação visual
- Fonte base: 11px (`text-xs` redefinido no tailwind.config.ts)
- Sidebar: 64px colapsada, bg-white, flat design
- Cores: usar tokens `wedo-*` do tailwind.config.ts. **NUNCA hex hardcoded**
- Dark mode obrigatório em todos os componentes

---

## Padrões de Desenvolvimento (Anti-Vibe-Coding)

### Frontend — Regras para Portabilidade Vue
**SEMPRE aplicar ao criar/modificar componentes:**

1. **Separação de concerns**: lógica em hooks (`use-*.ts`), componente = template + binding
2. **Props tipadas**: sempre `interface Props {}`, nunca `type` inline ou `any`
3. **Callbacks `on*`**: `onSelect`, `onMove`, `onChange` → mapeiam para `@event` em Vue
4. **Sem React-only patterns**: evitar `cloneElement`, `Children.map`, `forwardRef`, HOCs
5. **State management**: hooks `use*Store` com `interface State/Actions` → Pinia
6. **Composição via slots**: `children`, `header`, `footer` como props → `<slot>` em Vue
7. **Sem `useContext` excessivo**: preferir props ou hook de store

### Backend — Boas Práticas (FastAPI/Python)
1. **Separação de camadas**: routers finos, lógica em services, models apenas dados
2. **Services stateless**: sem estado global em services, tudo via parâmetros
3. **Sem código monolítico**: funções com responsabilidade única (<50 linhas por função)
4. **Schemas Pydantic explícitos**: request e response tipados em todos os endpoints
5. **Multi-tenant obrigatório**: `company_id` em TODOS os modelos e queries

### Geral
- Componentes/arquivos grandes (>150 linhas): extrair lógica para hook/service
- Sem duplicação: verificar se já existe antes de criar
- Nomenclatura consistente: kebab-case (FE), snake_case (BE)

---

## Integrações Externas

### LLMs
- **Anthropic Claude Sonnet 4.5** — primário
- **Google Gemini** — multimodal (vídeo, imagem)
- **OpenAI** — fallback

### IA/ML Especializada
- **Pearch AI** — busca candidatos (190M+ perfis)
- **Deepgram** — speech-to-text
- **OpenMic.ai** — triagem por voz (ligações)
- **Apify** — web scraping
- **LangSmith** — observabilidade LLMs

### Comunicação
- **Microsoft Teams** — bot, reuniões, notificações
- **Microsoft Graph / Outlook** — calendário, agendamento
- **WhatsApp** — Meta API + Twilio
- **Email** — SendGrid + Resend + Mailgun
- **Gupy / Pandapé ATS** — sincronização bidirecional
- **Merge** — conector multi-ATS

### Admin / SaaS
- **WorkOS** — SSO, SCIM
- **HubSpot** — CRM
- **Stripe** — billing

### Infraestrutura
- **PostgreSQL (Neon)** + pgvector | **Redis** | **RabbitMQ** | **Celery** | **Prometheus**

---

## Convenções e Preferências (OBRIGATÓRIAS)

- **Idioma**: Português em toda comunicação
- **Marca**: sempre **WeDOTalent** (nunca variações)
- **Design**: SEMPRE perguntar antes de mudar layout/design — apresentar proposta primeiro
- **Frontend ↔ Backend**: separação total. FE consome API REST. Sem código misto.
- **Chat como interface principal**: LIA interage via conversa natural, não via botões
- **Portabilidade FE**: todo código novo deve ser compatível com migração futura Vue/Nuxt (apenas frontend)

---

## Agentes ReAct (7 Domínios) — Padrão 4 Arquivos

Cada agente em `app/domains/<domain>/agents/`:
- `agent.py` | `tool_registry.py` | `system_prompt.py` | `stage_context.py`

**Agentes ativos**: Wizard, Pipeline (PipelineTransitionAgent), Sourcing, Talent, JobsManagement, Kanban, Policy

---

## Sistema de Notificações

5 canais: Bell in-app | Email | Teams | WhatsApp | Chat inline
Serviço central: `app/services/notification_service.py`

---

## Compliance & Governança

- **LGPD**: `data_request.py`, `consent_management.py`, portal de titular
- **SOC 2 / ISO 27001**: `compliance_controls.py`, `audit_logs.py`, `trust_center.py`
- **FairnessGuard**: 3 camadas — Camada 1 (regex 40+ patterns), Camada 2 (léxico implícito), Camada 3 LLM (opt-in `FAIRNESS_LAYER3_ENABLED`)
- **FactChecker**: verificação de fatos em avaliações
- **Model Drift Detection**: `app/services/model_drift_service.py` — 4 triggers (score, aprovação, custo, latência P95). Endpoint: `GET /api/v1/drift/status`. Proxy FE: `api/backend-proxy/drift/route.ts`
- **Drift Alert Service**: `app/services/drift_alert_service.py` — notificação automática Bell+Teams quando drift detectado. 1 trigger=WARNING, 2+=URGENT. `drift_alert_service.evaluate_and_alert(db, company_id, notify_user_id)`
- **Drift Batch Job**: `app/jobs/drift_job.py` — `run_drift_check_all_companies(db, notify_user_id)`. Endpoint admin: `POST /api/v1/drift/run-batch`. Celery task: `app/jobs/celery_tasks.py` (`drift.run_batch`).
- **Celery App**: `app/core/celery_app.py` — `Celery("lia_tasks", broker=REDIS_URL)`. Worker: `celery -A app.core.celery_app worker`. Tasks em `app/jobs/celery_tasks.py`. Beat schedule: `drift-run-batch-daily` às 06h Brasília (G.2).
- **Bias Audit API**: `app/services/bias_audit_service.py` + `app/api/v1/bias_audit.py` — `GET /api/v1/bias-audit/job/{job_id}`. Four-Fifths Rule em 4 dimensões (gender, age_group, disability, region) com dados reais. Stats agregadas (LGPD-safe). Proxy FE: `api/backend-proxy/bias-audit/[job_id]/route.ts`. UI: `plataforma-lia/src/app/admin/compliance/auditoria/bias/page.tsx` (dados reais, F.2)
- **BiasAuditSnapshot**: `app/models/bias_audit_snapshot.py` + migration `018_add_bias_audit_snapshot.py`. `bias_audit_service.save_snapshot()` + `get_snapshot_history()`. Endpoint: `GET /api/v1/bias-audit/job/{job_id}/history`. Proxy FE: `api/backend-proxy/bias-audit/[job_id]/history/route.ts`. Histórico auditável SOX/ISO 27001 (G.4).
- **Bias Audit Baseline (sintético)**: `tests/fixtures/golden_dataset.py` + `tests/fairness/test_four_fifths_rule.py` — Four-Fifths Rule (adverse_impact_ratio >= 0.80 por gênero, idade, PCD, região)
- **Wizard Orchestrator**: `app/domains/job_management/services/wizard_orchestrator_service.py` — WizardIntent (8 valores), INTENT_TO_TOOL_MAPPING, keyword detection. Arquivo reconstruído em Ciclo F (estava truncado).
- **Anti-sycophancy**: `app/services/sector_benchmark_service.py` — benchmark setorial injetado no prompt de `evaluate_candidate()` (Crença #11)
- **FairnessGuard em callers diretos**: `rubric_evaluation_service.evaluate_candidate()` e `triagem_curricular_agent._handle_general_query()` protegidos (Sessions A-C)
- **RAG Híbrido**: `app/services/rag_pipeline_service.py` — BM25 + pgvector alpha blend. `GET /api/v1/candidates/rag-search`. FairnessGuard top-10 gender diversity (stub log-only, G6).
- **TOON Format**: `app/services/toon_service.py` — TOONCard por candidato+vaga. Redis TTL 1h. LGPD anonymize=True. `GET /api/v1/candidates/{id}/toon`. (G7)
- **YAML Tool Registry**: `app/tools/tool_registry_metadata.yaml` — 32 tools declaradas (metadata, allowed_agents, scope). Validação via `registry.validate_yaml()`. (G5)
- **HITL audit multi-tenant**: `request_approval()` com `domain`/`company_id` nos 3 agentes HITL (G1)
- **Float Chat Nível 3** (Sprint J — 09/03/2026): `LiaChatPanel` migrado REST→WebSocket. `use-float-streaming.ts` — HITL + streaming. `HITLConfirmCard.tsx` — card de aprovação. `navigation_intent.py` — 4 novos grupos: Configurações, Indicadores, WSI, reordenado por especificidade. Wizard detectado redireciona para `openSplitView("Vagas")`. 9 testes Vitest.
- **PolicyEngine Alpha 1** (Gap 16.3 — 11/03/2026): `app/services/policy_engine_service.py` — `save_policy_block(company_id, sector, db)` persiste defaults setoriais (6 setores: tech/varejo/logistica/financeiro/saude/rpo). Seeding idempotente no lifespan. Endpoint `POST /api/v1/policy-engine/apply-sector/{company_id}?sector=`. 22 testes.
- **Data Retention LGPD Celery fix** (Gap 16.3 — 11/03/2026): `app/jobs/celery_tasks.py` — bug fix: import `run_cleanup` direto (não objeto). `app/api/v1/admin_lgpd.py` — `GET /admin/lgpd/cleanup-status` + `GET /admin/lgpd/retention-policy`. Beat schedule: `lgpd-cleanup-daily` às 05h UTC.
- **DSR Notifications** (Gap 16.3 — 11/03/2026): `app/api/v1/data_subject_requests.py` — `_notify_subject()` fail-safe, `_REQUEST_TYPE_LABELS` (PT-BR), `calculate_sla_deadline()`. Wired em create/complete/reject DSR. 16 testes.
- **Email Tracking integration** (Gap 16.3 / COMP-7 — 11/03/2026): `app/services/email_tracking_service.py` — `inject_pixel_and_links(html, token, action_url)`. `libs/messaging/lia_messaging/notification_service.py` `_send_to_email()` — pixel injetado automaticamente, fail-safe. 13 testes.
- **Gate-differentiated feedback** (Gap 16.1 — 11/03/2026): `app/services/candidate_feedback_service.py` — `send_gate_feedback(gate_level, ...)` com 4 gates: screening_invited / gate1_rejected / gate2_rejected / approved. PII masking nos logs. Wired em `wsi_interview_graph.generate_feedback()` ao reprovar. 13 testes.
- **Web inscription Gate 1 alignment** (Gap 16.1 — 11/03/2026): Ambos endpoints (`applications.py` e `job_vacancies.py`) agora usam `stage="pending_gate1"` + `screening_invite_token` em `additional_data`. Verificação de saturação adicionada a `applications.py` (status=`awaiting_screening` se saturado). `process_screening_queue` consome o token do `additional_data` e usa `send_gate_feedback("screening_invited")` como mecanismo canônico de email. `handle_recruiter_override_approve` alinhado com mesmo padrão. Card SAT-007 no doc Jira documenta máquina de estados completa. **3 bugs corrigidos pós-review**: import errado de CompanyProfile, NameError de job_title no branch email, fallback de saturação inconsistente — todos documentados na Seção 15 do doc Jira.
- **Circuit Breakers admin** (Gap 16.3 — 11/03/2026): `app/api/v1/admin_circuit_breakers.py` — `GET /api/v1/admin/circuit-breakers` (status), `POST /api/v1/admin/circuit-breakers/{name}/reset`, `POST /api/v1/admin/circuit-breakers/reset-all`. Combina ALL_CIRCUITS (class) + _circuits (functional). 7 testes.
- **Diagnóstico #7 fixes** (12/03/2026): 4 bugs corrigidos: (1) UUID parse safety em `policy_engine_service.py` — try/except antes do AsyncSessionLocal; (2) Double-submit guard em `use-float-streaming.ts` — `hitlRef.current=null` antes de `sendRaw()`, estado `hitlPending` preservado até evento `message`; (3) Warning log em `enhanced_agent_mixin.py` — `_resolve_guardrails()` loga quando usa static defaults; (4) Per-circuit try/except em `admin_circuit_breakers.py` — `reset_all` coleta `failed_circuits` e reporta `total_reset` correto. 7 testes em `tests/unit/test_diagnostico7_fixes.py`.
- **P3-1 Briefing Diário** (12/03/2026): `app/jobs/celery_tasks.py` — `briefing.send_daily` Celery task (itera usuários ativos, `BriefingService.generate_daily_briefing()` por user, Bell notification best-effort). `libs/config/lia_config/celery_app.py` — beat schedule `briefing-daily` às 09h UTC (06h Brasília). FE: `src/hooks/use-daily-briefing.ts` — `useDailyBriefing()` composable com fetch/refresh tipado. `src/components/daily-briefing-card.tsx` — corrigido `user_id` hardcoded para `jwtUser?.id`. Wired em `src/components/pages/dashboards-page.tsx` — card renderizado no topo do conteúdo com callbacks `onNavigate`.
- **P3-2 JD Import via Upload** (12/03/2026): `app/api/v1/jd_import.py` — `POST /import/upload-file` (.txt/.md/.pdf/.docx, 5MB limit, `strip_pii_for_llm_prompt()` antes de importar). Proxy FE: `src/app/api/backend-proxy/jd-import/upload/route.ts`. Wired em `src/components/pages/jobs-page.tsx` aba "Descrição do Cargo" — paperclip conectado a `handleJDFileUpload()`, LGPD notice inline.
- **P3-3 Policy Templates por Setor** (12/03/2026): Proxy FE `src/app/api/backend-proxy/policy-engine/apply-sector/route.ts`. UI em `src/app/admin/configuracoes/politicas/page.tsx` — seção "Templates por Setor" com Select (6 setores) + botão "Aplicar Template".
- **P3-4 ML Preditiva FE** (12/03/2026): `src/hooks/use-ml-predictions.ts` — `useMLPredictions()` composable com `fetchInsights`, `fetchTimeToFill`, `fetchSalary`. Proxies: `src/app/api/backend-proxy/ml/insights/route.ts`, `ml/predict/time-to-fill/route.ts`, `ml/predict/salary/route.ts`.
- **Testes P3** (12/03/2026): BE: `tests/unit/test_p3_features.py` — 13 testes (beat schedule, task registration, JD upload validations). FE Vitest: `src/hooks/__tests__/use-daily-briefing.test.ts` (6 testes) + `src/hooks/__tests__/use-ml-predictions.test.ts` (8 testes).
- **Short List UI Wiring** (12/03/2026): `src/components/pages/job-kanban-page.tsx` — `useShortList` importado e wired com `_companyIdForSL`/`_jobIdForSL`. `handleToggleShortList()` cria lista automaticamente se não existir (auto-create). DropdownMenuItem "Adicionar à Short List" com `Bookmark` icon adicionado ao menu de ações de cada candidato. State: `shortListedCandidateIds: Set<string>` + `activeShortListId: string | null`. 6 testes em `src/hooks/__tests__/use-short-list.test.ts`.
- **MLInsightsCard + P4 wiring** (12/03/2026): `src/components/ml-insights-card.tsx` — card expansível de previsões IA (time-to-fill, salary range, market percentile). Lazy-fetch: só chama API ao expandir, cache local (`hasFetched`). Wired em `job-kanban-page.tsx` entre header da vaga e tabs de navegação. 7 testes em `src/components/__tests__/ml-insights-card.test.tsx`.
- **Follow-up Automático WSI — Gap A / Passo 6B Alpha 1** (12/03/2026): `app/jobs/followup_service.py` — `process_email_followups(db)` consulta notificações `wsi_invite` não abertas há >24h via `email_tracking_events`. MAX_FOLLOWUPS=7. `_mark_no_response()` após esgotar reenvios. LGPD opt-out check. Celery task `followup.process_pending` + beat `followup-check-hourly` (crontab minute=0, expires=3500). 9 testes em `tests/unit/test_followup_service.py`.
- **WSI Triagem Abandonada — Gap B / Passo 7A Alpha 1** (12/03/2026): `app/jobs/wsi_abandoned_service.py` — `check_abandoned_sessions(db)` consulta `wsi_sessions` `in_progress` sem atividade. FIRST_REMINDER_HOURS=48 (1º lembrete candidato), SECOND_REMINDER_HOURS=96 (2º lembrete + Bell+Teams ao recruiter via `job_vacancies.created_by`). `reminder_count` persistido via `jsonb_set()` no `metadata`. Celery task `wsi.check_abandoned` + beat `wsi-abandoned-check` (crontab minute=0 hour=*/4, expires=14000). 8 testes em `tests/unit/test_wsi_abandoned_service.py`.
- **Auditoria de Profundidade — Sprints AUD-1 a AUD-5** (12/03/2026): 13 findings confirmados de relatório externo. Implementados:
  - **AUD-1 (ACH-001)**: `ANTI_SYCOPHANCY_OPERATIONAL` injetado nos 6 prompts faltantes: `analytics`, `communication`, `automation`, `ats_integration`, `sourcing`, `pipeline` system_prompts.
  - **AUD-2 (ACH-004/010/011/014)**: Circuit breakers aplicados — `OPENAI_CIRCUIT` em `llm_openai.py` (4 métodos), `GEMINI_CIRCUIT` em `llm_gemini.py` (4 métodos). Novos circuits: `GUPY_CIRCUIT`, `PANDAPE_CIRCUIT`, `STACKONE_CIRCUIT`, `SENDGRID_CIRCUIT`, `RESEND_CIRCUIT` em `circuit_breaker.py` + `ALL_CIRCUITS`. Decoradores `@circuit_breaker_decorator` aplicados em: `app/services/ats_clients/` (gupy, pandape, stackone, merge), `app/services/email_providers/` (sendgrid, resend), `app/domains/ats_integration/services/ats_clients/` (gupy, pandape, stackone, merge), `app/domains/communication/services/email_providers/` (sendgrid, resend). `WORKOS_CIRCUIT` aplicado via `_fetch_workos_metrics()` helper em `workos.py`.
  - **AUD-4 (ACH-005)**: HITL adicionado em `SourcingReActAgent.process()` — bloqueia envio de abordagem (stage="outreach" + confirmação) e solicita aprovação via `hitl_service.request_approval()` + `store_resume_info()`. Fail-open se HITL service indisponível. `CommunicationReActAgent.process()` — bloqueia `initial_contact`, `rejection_feedback`, `offer_letter` via `_HITL_MESSAGE_TYPES`. Ambos integram `audit_service.log_decision()`. 17 testes em `tests/unit/test_aud4_hitl_and_domain_circuits.py`.
  - **AUD-3 (ACH-006)**: `audit_service.log_decision()` adicionado em `PolicySetupAgent._process_answer()` — registra cada campo configurado com `decision_type="policy_update"`, fail-safe.
  - **AUD-5 (ACH-025/023/018)**: `bandit` scan adicionado ao CI (`continue-on-error: true`). Job `load-tests` não-bloqueante criado (só roda em `main`). `mockUsers` e `MOCK_BILLING_DATA` removidos de `admin/clientes/[clientId]/usuarios/page.tsx` e `faturamento/page.tsx` — substituídos por estado de erro real.
  - 36 testes em `tests/unit/test_aud_audit_fixes.py`.

---

## Documentos de Referência Críticos

| Documento | Caminho | Confiabilidade |
|-----------|---------|----------------|
| Preferências + Contexto | `replit.md` | ✅ Atualizado |
| **Guia WeDOTalent v3.4** | `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` | ✅ Mar 2026 |
| Design System v4.2.1 | `plataforma-lia/docs/design-system/00-design-system-v4.md` | ✅ Atualizado |
| Inventário de Integrações | `docs/integracao/INVENTARIO_FERRAMENTAS_INTEGRACOES.md` | ✅ Jan 2026 |
| Compliance | `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` | ✅ Dez 2025 |
| Mapa de Alertas/Comunicações | `docs/integracao/communication-alerts-map.md` | ✅ Referência |
| Gaps e Pendências | `docs/analises/ANALISE-GAPS-COMPLETA.md` | ✅ Referência |
| Metodologia WSI | `docs/WSI_METHODOLOGY_REFERENCE.md` | ✅ Referência |

> **Arquitetura de IA**: documentos existentes estão desatualizados e em revisão por especialista.
> **Fonte de verdade para IA = o código**: `app/domains/`, `app/shared/agents/`, `app/tools/`
> Quando a revisão estiver completa, incorporar `mapa_camada_inteligencia_ia.md` e `ai_architecture_audit.md`.

---

## Regra de Ouro — Fluxo de Desenvolvimento

> **"Planejamento → Feature Impact → Aprovação → Código"**

```
1. Entender pedido + ler código relevante
2. Montar planejamento (o que, como, em que ordem)
3. /feature-impact   → mapear impactos nas 12 dimensões
4. Aguardar aprovação ← NUNCA escrever código antes disso
5. Implementar       → seguindo padrões de portabilidade
6. /vue-migration-prep → código FE portável para Vue?
7. /design-standardize → UI conforme DS v4.2.1?
8. /testing-patterns → cobertura das 5 camadas (Jam.dev → Unitário → Integração → E2E → Fairness)
9. /feature-audit    → auditoria 14 dimensões antes de concluir
```

---

## Sprint Y2 — Quick Wins + Infra (15/03/2026)

- **Y2/E8 — Validação de escopo de tools no backend** (15/03/2026): `libs/agents-core/lia_agents_core/react_loop.py` — `active_scope: Optional[str]` em `ReActConfig`; verificação `is_tool_allowed_in_scope()` antes de `_act()` (fail-open, loga `[SCOPE-VIOLATION]`). `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — método `_validate_tool_scope(tool_name, active_scope)` fail-open. `app/services/tool_executor_service.py` — `active_scope: Optional[str]` em `ToolExecutionRequest` + validação em `execute()`. 9 testes em `tests/unit/test_e8_scope_validation.py`.
- **Y2/D10 — Fallback Chain Pearch AI → Busca Interna** (15/03/2026): `app/domains/sourcing/services/pearch_service.py` — `_pearch_search_fallback()` reescrito: quando circuit aberto tenta `RAGPipelineService.search()` via `AsyncSessionLocal`; converte `RAGSearchResult` → `PearchSearchResponse(status="internal_fallback")`; se RAG falhar retorna `status="unavailable"`. ACH-004 parcialmente fechado. 5 testes em `tests/unit/test_d10_pearch_fallback.py`.
- **Y2/D8 — Insights Proativos no Kanban — Wiring** (15/03/2026): `app/api/v1/proactive_actions.py` — novo endpoint `GET /api/v1/proactive-actions/insights?company_id=&job_id=&limit=` retorna `ProactiveInsight[]` (urgency, type, message, action_url); filtra por job_id se fornecido; fail-safe retorna `[]` em erro. `src/app/api/backend-proxy/proactive-insights/route.ts` (novo) — proxy GET. `src/hooks/use-proactive-insights.ts` (novo) — `useProactiveInsights(jobId, companyId)` com auto-refresh 5min, dismiss por sessão via `sessionStorage`. `job-kanban-page.tsx` — importa `useProactiveInsights`, renderiza painel dismissível abaixo do tab navigation quando há insights. 5 testes BE em `tests/unit/test_d8_proactive_insights.py`.
- **Y2/D1 — JobReportModal: wire backend real** (15/03/2026): `app/api/v1/job_vacancies.py` — novo endpoint `GET /api/v1/jobs/{job_id}/report` retorna `JobReportResponse` (funnel_metrics, channel_performance, top_candidates) com dados reais do DB (VacancyCandidate + Candidate + CandidateStageHistory). `src/hooks/use-job-report.ts` (novo) — `useJobReport()` com fetch/loading/error tipados. `src/app/api/backend-proxy/jobs/[jobId]/report/route.ts` (novo) — proxy GET. `job-report-modal.tsx` — importa `useJobReport`, substitui `reportData` mockado por dados do hook (funnel, canais, top candidatos reais; budget/timeline mantidos como placeholder). 5 testes BE em `tests/unit/test_d1_job_report_endpoint.py`.
- **Y2/C4 — Métricas Prometheus por agente — wiring** (15/03/2026): `libs/agents-core/lia_agents_core/langgraph_react_base.py` — `agent_latency_timer` wrapping `_run_graph()` em `_process_langgraph()` (fail-safe noop se não disponível). `libs/agents-core/lia_agents_core/react_loop.py` — `record_tokens()` após tool execution (usa `tokens` ou `usage` do result). `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `record_agent_request(status="guardrail_fallback")` no static fallback de `_resolve_guardrails()`. `app/api/v1/metrics.py` (novo) — `GET /api/v1/metrics` → `generate_latest()` Prometheus (graceful ImportError). 8 testes em `tests/unit/test_c4_agent_metrics.py`.

---

## Sprint Y3 — Fairness, Calibração e Produto (15/03/2026)

- **Y3/D3 — Bias Audit Disparate Impact (EEOC)** (15/03/2026): `app/services/bias_audit_service.py` — `_chi_square_test(groups)` (scipy + Python puro fallback via gamma incompleta), `DemographicAuditResult.disparate_impact + eeoc_compliant`, `_audit_dimension()` calcula EEOC. `app/api/v1/bias_audit.py` — response schema atualizado. `libs/models/lia_models/bias_audit_snapshot.py` — `disparate_impact_data JSONB nullable`. `alembic/versions/042_add_disparate_impact_to_snapshot.py`. 7 testes em `tests/unit/test_d3_disparate_impact.py`.
- **Y3/D2 — Confidence Calibration (12 agentes)** (15/03/2026): `libs/agents-core/lia_agents_core/react_loop.py` — `confidence_score: float = 0.5` em `ReActState`; bloco de cálculo `tool_success_ratio * 0.7 + completion_ratio * 0.3`. `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `_record_confidence(state)` fail-silent; integrado em `_post_loop_learning()` (cobre 8 agentes automaticamente). 4 agentes sem `_post_loop_learning` wired explicitamente: `analytics_react_agent.py`, `communication_react_agent.py`, `ats_integration_react_agent.py`, `automation_react_agent.py`. 9 testes em `tests/unit/test_d2_confidence_calibration.py`.
- **Y3/D5 — Granular Consent LGPD** (15/03/2026): `app/services/granular_consent_service.py` — `GranularConsentService` com mapa granular (7 tipos distintos vs. todos para SCREENING), `get_summary()`, `bulk_update()`, `check_purpose()` fail-open. `app/api/v1/granular_consent.py` — `GET /api/v1/consent/granular/{candidate_id}` + `POST /api/v1/consent/granular/{candidate_id}/update`. Registrado em `main.py`. 11 testes em `tests/unit/test_d5_granular_consent.py`.
- **Y3/E1 — Score Clicável Kanban** (15/03/2026): `app/api/v1/rubric_evaluation.py` — `GET /api/v1/rubrics/{job_id}/candidates/{candidate_id}/breakdown` retorna score detalhado (strengths, concerns, evaluations, reasoning). `src/app/api/backend-proxy/rubrics/[jobId]/candidates/[candidateId]/breakdown/route.ts` (proxy). `src/hooks/use-score-breakdown.ts` — lazy-load hook. `src/components/score/ScoreBreakdownBadge.tsx` — `ScoreBreakdownBadgeLazy` com Popover lazy-load. `job-kanban-page.tsx` — wired no kanban card. 4 testes BE em `tests/unit/test_e1_score_breakdown.py`.
- **Y3/D9 — Análise Comparativa Visual** (15/03/2026): `app/api/v1/candidate_compare.py` — `POST /api/v1/candidates/compare` (2-4 candidatos, job_id opcional); delega para `CandidateComparisonService`. `src/app/api/backend-proxy/candidates/compare/route.ts` (proxy). `src/hooks/use-candidate-compare.ts` — lazy hook. `src/components/modals/candidate-compare-modal.tsx` — modal completo com winner banner, scores por dimensão, análise. `job-kanban-page.tsx` — wired com estado + modal renderizado. 6 testes em `tests/unit/test_d9_candidate_compare.py`.
- **Y3/D6 — ML Adaptativo (Feedback Loop)** (15/03/2026): `app/services/ml_feedback_service.py` — `MLFeedbackService` com `record_signal()` (delega CalibrationService), `compute_job_weights()` (pesos adaptativos em [0.7, 1.3] baseados em divergências de feedback), `get_weights_for_job()` fail-open. `app/api/v1/ml_feedback.py` — `POST /api/v1/ml-feedback/signal` + `GET /api/v1/ml-feedback/weights?job_id=`. Celery task `ml.feedback.process_weights` em `celery_tasks.py`. Registrado em `main.py`. 10 testes em `tests/unit/test_d6_ml_feedback.py`.

> Estado atual: Sprints A–F + G1–G7 + SEG-1–SEG-5 + SEG-GAPS + AUD-1–AUD-5 + AUD-4 + Y1(C2, D4, C1, C3) + Y2(E8, D10, C4, D1, D8) + Y3(D3, D2, D5, E1, D9, D6) concluídos — **Sprint Y3 completo**. Coverage: **29%+** (gate pytest.ini: 25%). 4395+ testes passando.

---

## Sprint Y4 — Capacidades Novas (15/03/2026)

- **Y4/D7 — Benchmark Salarial Real** (15/03/2026): `app/services/salary_benchmark_service.py` — `SalaryBenchmarkService` com 3 camadas: Redis TTL=7d → Apify `scrape_salary_data()` → fallback setorial estático (5 níveis). `SalaryBenchmark` dataclass (p25/p50/p75/source). `app/api/v1/salary_benchmark.py` — `GET /api/v1/salary-benchmark?job_title=&seniority=&location=` com `X-Company-ID` header. `app/domains/sourcing/services/apify_service.py` — método `scrape_salary_data()` adicionado. Registrado em `main.py`. 7 testes em `tests/unit/test_d7_salary_benchmark.py`.
- **Y4/E11 — Priority Queue por Urgência** (15/03/2026): `app/shared/async_processing/priority_calculator.py` — `PriorityCalculator.compute(task_type, metadata)` com escala 1-5: sourcing deadline<7d→1, cv_screening backlog>50→2, followup/wsi_abandoned→3, padrão→5. Singleton `priority_calculator`. `task_queue.py` atualizado para aceitar `priority` opcional com fallback ao calculador. 11 testes em `tests/unit/test_e11_priority_queue.py`.
- **Y4/E5 — Multi-Model por Agente** (15/03/2026): `app/core/agent_model_config.py` — `AGENT_MODEL_CONFIG` com 12 agentes mapeados; `build_agent_model_config()` lê envvars `AGENT_MODEL_{NAME_UPPER}`; `get_model_for_agent(agent_name)` com fallback. `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `@property model_id` usando `get_model_for_agent(self._enhanced_domain)`. 9 testes em `tests/unit/test_e5_multi_model.py`.
- **Y4/E7 — Streaming Pensamentos ReAct via WS** (15/03/2026): `src/components/react-thinking-stream.tsx` — componente colapsável `ReactThinkingStream(steps, isThinking)` com spinner/check, expansão de etapas. `src/hooks/use-float-streaming.ts` — `thinkingSteps: string[]` + `isThinking: bool` + handler `type:"thinking"`. WS handler em `agent_chat_ws.py` preparado para retransmitir eventos thinking ao cliente. 5 testes BE em `tests/unit/test_e7_react_streaming.py`.
- **Y4/E3 — WSI Assíncrono** (15/03/2026): `app/api/v1/wsi_async.py` — 4 endpoints: `POST /wsi/async/invite`, `GET /wsi/async/{token}`, `POST /wsi/async/{token}/answer`, `GET /wsi/async/{token}/complete`. Registrado em `main.py`. `src/hooks/use-wsi-async.ts` — `useWSIAsync(token)` com `loadSession/submitAnswer/completeSession`. `src/app/api/backend-proxy/wsi-async/[token]/route.ts` (proxy). 6 testes BE em `tests/unit/test_e3_wsi_async.py`.
- **Y4/E2 — Fit Cultural Integrado** (15/03/2026): `app/services/cultural_fit_integration_service.py` — `CulturalFitIntegrationService.compute_integrated_fit()` combina WSI (wsi_weight=0.4) + notas entrevistadores PII-masked (interview_weight=0.4) + cultura empresa via `CultureAnalyzerService` (culture_weight=0.2). `CulturalFitResult` dataclass. `app/api/v1/cultural_fit.py` — `GET /api/v1/candidates/{id}/cultural-fit?job_id=` com `X-Company-ID`. Registrado em `main.py`. 9 testes em `tests/unit/test_e2_cultural_fit.py`.
- **Y3 Gaps Fechados** (15/03/2026): D5-G1: migration 043 `candidate_consent_grants`; D5-G2: `ats_pii_filter.py` wiring `check_consent("ats_sharing")` + `test_d5_consent_wiring.py`; D6-G1: `RecruiterDecisionFeedback` model + migration 044; D6-G2: wiring em `pipeline_transition_agent.py` (hired/rejected → `record_decision()`); D6-G3: `_get_calibration_adjustment_async()` em `lia_score_service.py` usa `ml_feedback_service`; D9-G1: checkbox multi-select + botão "Comparar (N)" em `job-kanban-page.tsx`; E1-G2: `ScoreBreakdownBadgeLazy` wired em `candidates-page.tsx`.

---

## Sprint Y5 — Arquitetura Avançada (15/03/2026)

- **Y5/C5 — Runbook Operacional — Expansão** (15/03/2026): `docs/RUNBOOK_DEGRADATION.md` expandido com 6 novas seções (Circuit Breakers, Drift Detection, Bias Audit, HITL queue, PolicyEngine, Celery workers stuck). `docs/RUNBOOK_INCIDENT_PLAYBOOKS.md` criado com 5 playbooks: LLM primário down, Banco indisponível, Redis indisponível, CircuitBreaker OPEN, Drift URGENT. 54 testes em `tests/unit/test_c5_runbook_links.py`.
- **Y5/E4 — YAML Hot-Reload de Agentes** (15/03/2026): `app/agents_registry.yaml` (7 agentes declarados). `app/core/agent_registry_watcher.py` — `AgentRegistryWatcher` com `check_and_reload()` mtime-gated + `reload_agents_registry()`. `libs/agents-core/lia_agents_core/react_agent_registry.py` — `reload_from_yaml(path)` adicionado (fail-open). `app/api/v1/admin_agents.py` — `POST /api/v1/admin/agents/reload`. Registrado em `main.py`. 8 testes em `tests/unit/test_e4_agent_hot_reload.py`.
- **Y5/E6 — RAG por Domínio — Embeddings Separados** (15/03/2026): Migration 045 (`domain` column em `routing_cache_vectors`). `app/services/rag_pipeline_service.py` — `DOMAIN_ALIASES` + `normalize_domain()` + `domain: Optional[str]` param em `search()/_bm25_search()/_semantic_search()` com filtro `WHERE domain = :domain`. `app/services/domain_embedding_service.py` — `DomainEmbeddingService.embed_document()` + `rebuild_domain_index()` + singleton. Celery task `rag.rebuild_domain_index`. 10 testes em `tests/unit/test_e6_rag_domain.py`.
- **Y5/E9 — Auto-Routing Adaptativo** (15/03/2026): `app/models/routing_feedback.py` — `RoutingFeedback` model (company_id, session_id, message_hash, routed_domain, actual_domain, corrected). Migration 046. `app/services/routing_learning_service.py` — `record_correction()` + `compute_domain_confidence_adjustments()` (SQLAlchemy case(), ajuste 0.8–1.2, min 10 samples) + Redis cache TTL=24h. Wiring em `cascaded_router.py` (`_apply_adaptive_adjustments()` nos Tiers 4 e 5). Celery task `routing.recompute_adjustments` + beat `routing-recompute-daily` (07h UTC). `app/core/redis_client.py` criado (wrapper aioredis lazy). 12 testes em `tests/unit/test_e9_adaptive_routing.py`.
- **Y5/E10 — Agent-to-Agent Communication** (15/03/2026): `app/shared/agents/agent_bus.py` — `AgentBus` singleton com `publish()` (Redis Pub/Sub) + `subscribe()` + `dispatch_local()` + audit trail automático. `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` — `async def emit(to_agent, event_type, payload, company_id)` adicionado. Wiring: Sourcing→Pipeline (`candidate_imported`) em `sourcing_react_agent.py`; Wizard→JobsManagement (`job_creation_ready`) em `job_wizard_graph.py`. 12 testes em `tests/unit/test_e10_agent_bus.py`.
- **Y5/E12 — Event Sourcing Imutável** (15/03/2026): `app/models/event_store.py` — `DomainEvent(id, aggregate_type, aggregate_id, event_type, event_data JSONB, company_id, created_by, created_at, sequence_number BIGINT)` + UniqueConstraint por sequência. Migration 047. `app/services/event_store_service.py` — `EventStoreService.append()` (only INSERT) + `get_history()` (replay ordenado) + `reconstruct_state()` (fold com folder padrão). `app/api/v1/event_history.py` — `GET /api/v1/candidates/{id}/event-history?from_sequence=&limit=`. Dual write em `pipeline_transition_agent.py` (`CandidateMoved`) e `job_wizard_graph.py` (`JobCreated`). Registrado em `main.py`. 12 testes em `tests/unit/test_e12_event_sourcing.py`.

> Estado atual: Sprints A–F + G1–G7 + SEG-1–SEG-5 + SEG-GAPS + AUD-1–AUD-5 + Y1 + Y2 + Y3 + Y4 + Y5 + **FAR** concluídos. Coverage: **30.99%+** (gate: 30%). **4680+ testes passando. Plano Y1–Y5 COMPLETO + Sprint FAR concluído.**

---

## Sprint FAR — Fairness Audit Remediation (20/03/2026)

- **FAR-1 — Expansão FairnessGuard** (20/03/2026): 4 novas categorias bloqueadoras: `antecedentes_criminais` (CNJ Res. 65/08), `saude_doenca` (Lei 9.029/95), `filiacao_sindical` (CLT Art. 543), `aparencia_fisica` (Lei 9.029/95). 18+ novos termos em `IMPLICIT_BIAS_TERMS` (zona_rural, periferia, candomble, umbanda, disponibilidade_total, etc.). Fix regex idade: lookahead `(?:de|no|na|em)` previne falso positivo "X anos no mercado". `_PATTERNS_VERSION = 3`. `log_check()` reescrito: aceita `db=None` (usa AsyncSessionLocal), `context` como dict ou str, `input_text` ignored (retrocompat). 44 testes em `tests/unit/test_far1_new_categories.py`.
- **FAR-2 — Proteção de Entry Points** (20/03/2026): `RAGPipelineService.search()` — FairnessGuard antes do retrieval BM25+pgvector, retorna `RAGSearchResult(source="blocked", fairness_ok=False)`. `PearchService.search_candidates()` — guard antes da chamada HTTP, retorna `PearchSearchResponse(status="fairness_blocked")`. `CommunicationReActAgent.process()` — guard em mensagens de saída. `jd_import.py` batch + single — guard com HTTP 422 em JDs discriminatórios. `PolicyReActAgent` já tinha guard. 13 testes em `tests/unit/test_far2_entry_points.py`.
- **FAR-3 — Soft Warnings Visíveis ao Recrutador** (20/03/2026): `SourcingReActAgent` e `PipelineTransitionAgent` — `_fg_result.soft_warnings` injetados em `output.metadata["fairness_warnings"]`. `agent_chat_ws.py` — payload WS inclui `"fairness_warnings": [...]` quando presente. `log_check()` persiste soft_warnings em `FairnessAuditLog`. 7 testes em `tests/unit/test_far3_soft_warnings.py`.
- **FAR-4 — Layer 3 LLM Ativado** (20/03/2026): `HIGH_IMPACT_ACTIONS` expandido com `"sourcing_search"` e `"jd_import"`. `SourcingReActAgent.process()` usa `check_with_layer3(action_type="sourcing_search")` (era `check()`). `check_with_layer3()` respeita flag `FAIRNESS_LAYER3_ENABLED` (padrão `False` — opt-in). Fail-open: se LLM indisponível ou flag desabilitada, retorna Layer 1+2. 8 testes em `tests/unit/test_far4_layer3.py`.
- **FAR-5 — Auditoria de Disparate Impact** (20/03/2026): `BiasAuditService.audit_ranking_results()` — Four-Fifths Rule (EEOC 80%) em top-N resultados por dimensão (gender, etc.). Chamado em `RAGPipelineService` após merge. `libs/models/lia_models/fairness_audit.py` — campo `soft_warnings JSONB nullable` adicionado. `alembic/versions/048_add_soft_warnings_to_fairness_audit.py` (revision=048, down_revision=047). 8 testes em `tests/unit/test_far5_output_audit.py`.
- **FAR-AUDIT (feature-audit)** (20/03/2026): 2 gaps fechados pós-auditoria: (1) `query[:60]` removido de logger.warning em `fairness_guard.py` — apenas `query_len` logado (LGPD/PII); (2) `FAIRNESS_LAYER3_ENABLED` feature flag honrada em `check_with_layer3()` — Layer 3 é opt-in por env var.

---

## Sprint Y1 — Compliance Crítico (15/03/2026)

- **Y1/D4 — PII masking em logs de aplicação** (15/03/2026): `app/shared/pii_masking.py` — `install_global_pii_masking()` agora adiciona `PIIMaskingFilter` nos handlers do root logger (além do logger raiz), cobrindo records propagados de child loggers que bypassam filtros do logger. `PIIMaskingFilter.filter()` agora também mascara `exc_info` (exception messages com CPF/email/telefone em stack traces). `app/core/logging_config.py` — `configure_logging()` adiciona filtro no `StreamHandler` no momento da criação. 12 testes em `tests/unit/test_d4_pii_log_masking.py`.
- **Y1/C2 — Audit trail interview_graph** (15/03/2026): `app/domains/interview_scheduling/agents/interview_graph.py` — 3 novos pontos `audit_service.log_decision()`: `decision="pending_review"` (pré-HITL, legacy path), `decision="validation_failed"` (validator reprova, legacy path), `decision="error"` (LangGraph ainvoke exception). Todos fail-safe (`except Exception: pass`). ACH-006 fechado: **14/14 agentes com audit trail (100%)**. 4 testes em `tests/unit/test_c2_interview_audit.py`.
- **Y1/C1 — LGPD em ATS: campos sensíveis dinâmicos** (15/03/2026): `app/services/ats_clients/lgpd_field_registry.py` (novo) — registro centralizado: `OUTBOUND_SENSITIVE_FIELDS` (phone, email, salary_expectation, wsi_score, cpf, birth_date, disability_info), `INBOUND_TEXT_FIELDS` por ATS, `get_inbound_text_fields()`. `app/services/ats_clients/ats_pii_filter.py` (novo) — `filter_outbound(payload, ats_name, has_consent=True)` + `filter_inbound_text(payload, ats_name)`, ambos fail-safe. Wired em `gupy.py` + `pandape.py` (services/ e domains/ats_integration/). ACH-030 fechado. 14 testes em `tests/unit/test_c1_ats_lgpd_fields.py`.
- **Y1/C3 — Interview Scheduling Agent: FairnessGuard + Confidence Score** (15/03/2026): `interview_scheduling_nodes.py` — `_compute_confidence_score()` (0.10+coleta*0.85, 1.0 após sucesso, 0.1 em erro/fairness). FairnessGuard SEG-2 adicionado em `interview_details_collector` (blocked=response_data fairness_blocked, fail-safe). `interview_scheduler_executor` define `confidence_score=1.0` após agendamento OK. `interview_graph.py` — substituiu `confidence=0.9/0.3` hardcoded por `_wfd.get("confidence_score")` + `record_confidence()` em ambos os paths (legacy + langgraph). HITL já tinha `domain`/`company_id` (G1-compliant). 11 testes em `tests/unit/test_c3_interview_scheduling_agent.py`.

---

## Sprints G1–G7 — COMPLETOS (08/03/2026)

> Estado atual: Sprints A–F + G1–G7 + SEG-1–SEG-5 + SEG-GAPS + AUD-1–AUD-5 + AUD-4 + Y1(C2, D4, C1, C3) + Y2(E8, D10, C4, D1, D8) + Y3(D3, D2, D5, E1, D9, D6) concluídos. Coverage: **29%+** (gate pytest.ini: 25%). 4395+ testes passando.

### G1 — HITL Multi-tenant Fix ✅
- `domain` + `company_id` adicionados a `request_approval()` em: `job_wizard_graph.py`, `wsi_interview_graph.py`, `pipeline_transition_agent.py`

### G2 — Coverage Gate 29% ✅
- 7 novos arquivos de teste: `test_navigation_intent.py`, `test_admin_prompts_extended.py`, `test_token_budget_extended.py`, `test_hitl_service_extended.py`, `test_wsi_interview_graph.py`, `test_short_list_service.py`, `test_admin_token_budget_api.py`, `test_main_orchestrator_extended.py`
- pytest.ini: `--cov-fail-under=25` + `--ignore` de 3 arquivos com falhas por infraestrutura (multi_tenancy, policy_gaps, sync_canonical)

### G3 — SearchResultsHeader ✅
- `src/components/pages/candidates/SearchResultsHeader.tsx` — extraído de candidates-page.tsx (202 linhas → 9 linhas)
- Props: `lastSearchQuery`, `lastSearchEntities: ParsedEntities | null`, `onBack`, `onOpenEditQueryModal`, `onOpenAdvancedSearch`

### G4 — useCandidatesListMapped ✅
- `src/lib/transforms/candidate-transforms.ts` — `mapCandidateLocalToCandidate()` (CandidateLocal→Candidate, 150L)
- `src/hooks/use-candidates-list-mapped.ts` — wrapper com `useMemo`; retorna `Candidate[]`
- Additive: disponível para migração incremental de candidates-page.tsx

### G5 — YAML Tool Registry ✅
- `app/tools/tool_registry_metadata.yaml` — 32 tools com name, description, allowed_agents, scope, version
- `app/tools/tool_registry_loader.py` — `load_tool_metadata()`, `export_registry_to_yaml()`, `validate_registry_against_yaml()`
- `app/tools/registry.py` — `.export_to_yaml()` + `.validate_yaml()` adicionados
- Scopes: TALENT_FUNNEL, JOB_TABLE, IN_JOB, GLOBAL

### G6 — RAG Híbrido ✅
- `app/services/rag_pipeline_service.py` — `RAGPipelineService.search(query, company_id, db, limit, alpha=0.5)`
  - alpha=0: BM25 (tsvector); alpha=1: pgvector cosine; 0<alpha<1: hybrid blend
  - FairnessGuard stub: top-10 gender diversity log-only
- `app/api/v1/rag_search.py` — `GET /api/v1/candidates/rag-search?q=&company_id=&limit=20&alpha=0.5`
- 31 testes em `tests/unit/test_rag_pipeline.py`

### G7 — TOON Format ✅
- `app/services/toon_service.py` — `TOONCard` dataclass, `TOONService.get_or_generate()`, Redis TTL=3600s
  - LGPD: `anonymize=True` → `name_display="Candidato X"`. Sem avatar, sem age raw.
  - Chave Redis: `toon:{company_id}:{candidate_id}:{job_id}`
- `app/api/v1/toon.py` — `GET /api/v1/candidates/{candidate_id}/toon?job_id=&company_id=&anonymize=false`
- `src/app/api/backend-proxy/candidates/[candidateId]/toon/route.ts` — proxy FE
- 34 testes em `tests/unit/test_toon_service.py`

---

## Sprints Ativos — Plano F (08/03/2026) — COMPLETOS

> Estado atual: Sprints A–F + G1–G7 concluídos. Coverage: 29.05% (gate 25%). 1344 testes passando.

### Sprint F1 — HITL Persistence ✅ (já implementado antes da sprint)
**Verificado em 12/03/2026:** `app/models/hitl.py` (models), `alembic/versions/032_add_hitl_tables.py` (migration), `app/services/hitl_service.py` (DB best-effort + Redis fast-path) — tudo já existia. Nada a fazer.

### Sprint F2 — Coverage Gate Unification
**Arquivos:** `pytest.ini`
- `--cov-fail-under=12` → `--cov-fail-under=25` (full suite já atinge 25.39%)
- Alinhamento com `ci.yml` que já usa 25%

### Sprint F3 — Sprint E FE Hooks Wiring ✅ (12/03/2026)
- `useCandidatesListMapped` wired como `candidatesListHook`; manual initial useEffect (143L) removido
- Sync effect: `candidatesListHook.{candidates,loading}` → `{setCandidates, setIsLoading}` quando hook atualiza
- `totalCandidatesInBase` removida (era dead state — nunca lida no JSX)
- `useBulkCandidateDataRequests` já estava wired desde Sprint E
- 10 testes: `src/hooks/__tests__/use-candidates-list.test.ts`

### Sprint F4 — Short List Endpoint
**Arquivos BE:** `app/api/v1/short_lists.py`, `app/services/short_list_service.py`, `app/models/short_list.py`, `alembic/versions/032_add_short_list_tables.py`
**Arquivos FE:** `src/app/api/backend-proxy/short-lists/[jobId]/route.ts`, `src/hooks/use-short-list.ts`
- Endpoints: `POST/GET /api/v1/short-lists`, `POST/DELETE /api/v1/short-lists/{job_id}/candidates`
- Registrar router em `app/main.py`
- 20+ testes unitários BE

### Sprint F5 — Sprint E Phase 3 ✅ (já implementado antes da sprint)
**Verificado em 12/03/2026:** `CandidateSearchBar.tsx` e `CandidateTabs.tsx` já extraídos e usados no JSX (linhas 6911, 6924). `SearchResultsHeader.tsx` também extraído (Sprint G3). Nada a fazer.

---

## Sprints SEG-1 a SEG-5 — Segurança e Governança (11/03/2026) ✅ COMPLETOS

> Implementação dos 5 gaps críticos de segurança do diagnóstico de agentes (seção 16.2).

### SEG-1 — PromptInjectionGuard ✅
- `app/api/v1/agent_chat_ws.py`: singleton `_injection_guard = PromptInjectionGuard()` no módulo; check após `content = msg.get("content",...)` — high=block+error_code, medium=log+continue
- `app/domains/cv_screening/agents/wsi_interview_graph.py`: check em `validate_response()` antes de SCORE_RESPONSE — injeção alta = score 0 + avança sem comprometer scoring
- Testes: `tests/unit/test_injection_guard_integration.py` (6 casos)

### SEG-2 — FairnessGuard nos agentes ReAct ✅
- `app/domains/sourcing/agents/sourcing_react_agent.py`: check no início de `process()` — blocked=retorna educational_message, soft_warnings=log
- `app/domains/pipeline/agents/pipeline_transition_agent.py`: mesma estrutura — blocked=retorna educational_message sobre critérios discriminatórios
- Falha silenciosa (fail-safe) em ambos
- Testes: `tests/unit/test_fairness_guard_agents.py` (5 casos)

### SEG-3A — PII Masking para workers Celery ✅
- `libs/config/lia_config/celery_app.py`: `@signals.worker_process_init.connect` → `install_global_pii_masking()` em cada processo filho (prefork)
- Testes: `tests/unit/test_pii_masking_celery.py` (2 casos)

### SEG-3B — Data minimization em prompts LLM ✅
- `app/shared/pii_masking.py`: `strip_pii_for_llm_prompt(text)` — Layer 1 (CPF/email/telefone/RG/CNPJ) + Layer 3 basic (quasi-identifiers: ano formatura, idade explícita, endereço). Flag `LLM_PROMPT_PII_STRIPPING_ENABLED` (padrão: true)
- `app/domains/cv_screening/services/rubric_evaluation_service.py`: `cv_content = strip_pii_for_llm_prompt(cv_content)` antes do prompt assembly
- Testes: `tests/unit/test_pii_llm_prompt_stripping.py` (7 casos)

### SEG-4 — ConsentCheckerService no Gate 1 WSI ✅
- `app/domains/cv_screening/agents/wsi_interview_graph.py`: `load_context()` — check `ai_screening` consent via `AsyncSessionLocal()` antes de carregar perguntas
- revoked → `state.error="LGPD_CONSENT_REVOKED"` + `stage=ERROR`; absent=soft warning + prossegue; falha=fail-safe
- Testes: `tests/unit/test_wsi_consent_gate.py` (4 casos)

### SEG-GAPS — Fechamento dos 3 gaps pós-SEG ✅ (11/03/2026)
- **Gap 1 (SEG-5/LangGraph)**: `sourcing_react_agent.py` e `pipeline_transition_agent.py` — override `_process_langgraph()` em ambos → audit após `super()._process_langgraph()`. Cobre o caminho `USE_LANGGRAPH_NATIVE=True`.
- **Gap 2 (SEG-3B/callers)**: `strip_pii_for_llm_prompt()` aplicado em 3 novos callers LLM críticos:
  - `app/services/analysis_service.py` → `_cv_text_clean = strip_pii_for_llm_prompt(cv_text[:3000])`
  - `app/services/voice_screening_analysis.py` → `transcript = strip_pii_for_llm_prompt(transcript)` antes do prompt
  - `app/services/candidate_comparison_service.py` → strip em `candidates_summary`
- **Gap 3 (SEG-5/HITL rejected)**: `agent_chat_ws.py` bloco `elif not ws_approved:` → audit `decision=rejected`, `agent_name=hitl_ws`, `candidate_id` extraído de `resume_input_dict`
- 10 novos testes em `tests/unit/test_audit_trail_gates.py` (classes `TestAuditTrailLangGraphPath` e `TestAuditTrailPIIStripping`)

### SEG-5 — AuditService nos gates de decisão ✅
- `app/domains/pipeline/agents/pipeline_transition_agent.py`: 2 pontos — (1) pre-HITL request: `decision_type=move_stage, decision=pending_review`; (2) transition completed: `decision=approved|completed`
- `app/domains/sourcing/agents/sourcing_react_agent.py`: final de `_process_react_loop()` — `decision_type=score_candidate, action=sourcing:{stage}`
- `criteria_ignored=list(PROTECTED_CRITERIA)` sempre
- Testes: `tests/unit/test_audit_trail_gates.py` (5 casos)

---

### Sprint F6 — LangSmith CI Step
**Arquivos:** `.github/workflows/ci.yml`
- Step `Verify LangSmith config` (non-blocking: `continue-on-error: true`)
- Usa `LANGSMITH_API_KEY` de secrets
- `tests/unit/test_langsmith_config.py` já cobre a lógica (18 testes ✅)

---

## Estado Atual dos Sistemas (08/03/2026)

### HITL (Human-in-the-Loop) — Sprint C + HITL Sprint
- `app/services/hitl_service.py` — Redis backing, `store_resume_info`/`get_resume_info`, `request_approval`/`receive_approval`
- `app/api/v1/hitl.py` — `POST /api/v1/hitl/{thread_id}/approve` registrado em `main.py`
- `app/domains/job_management/agents/job_wizard_graph.py` — `interrupt_before=["stage_transition"]`
- `app/domains/cv_screening/agents/wsi_interview_graph.py` — `interrupt_before=["lg_generate_feedback"]`
- `app/domains/pipeline/agents/pipeline_transition_agent.py` — pre-check HITL antes de `_process_langgraph()`
- `app/api/v1/agent_chat_ws.py` — 3 casos de resume: cv_screening (ainvoke None), wizard (ainvoke None), genérico (agent.process)
- Sprint F1 ✅: tabelas de persistência já implementadas (032_add_hitl_tables.py)

### Sprint E (FE God Object) — Phase 1 + 2 concluídas
- Hooks extraídos e wired: `use-candidate-filters.ts`, `use-candidate-selection.ts`
- Sprint F3 ✅: `useCandidatesListMapped` wired; manual useEffect (143L) removido; 10 testes
- Sprint F5 ✅: `CandidateSearchBar` + `CandidateTabs` extraídos e usados no JSX
