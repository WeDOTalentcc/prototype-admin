# LIA Platform — Instruções para Claude Code

> Leia este arquivo no início de cada conversa. Ele define o contexto completo da plataforma.

---

## Identidade da Plataforma

**LIA (Learning Intelligence Assistant)** — Plataforma B2B SaaS multi-tenant de recrutamento e seleção com IA.
Empresa: **WeDOTalent** ← escrever SEMPRE assim (nunca "Wedo Talent", "WeDo Talent" ou variações).

**Mercado alvo:** alto volume (varejo, logística, call centers), RPO white-label, empresas que precisam escalar triagem sem aumentar equipe.
**Compliance:** LGPD, BCB 498, SOX, ISO 27001, EU AI Act.

---

## Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend (atual) | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui (Radix UI) |
| Frontend (futuro) | Vue 3 + Vuetify 3 + Nuxt 3 + Pinia ← preparar código para migração |
| Backend (permanente) | FastAPI (Python 3.11), SQLAlchemy 2.0 async, Alembic |
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
    ├── analises/               ← Gaps, QA, diagnósticos
    └── archived/sprint-history.md  ← Histórico completo de sprints A–FAR
```

---

## Skills Disponíveis (`.agents/skills/`)

### Skills de Desenvolvimento
| Skill | Quando Usar |
|-------|-------------|
| `/feature-impact` | ANTES de implementar qualquer feature/ajuste. Mapeia impacto em 12 dimensões. |
| `/feature-audit` | DEPOIS de implementar. Auditoria de 14 dimensões antes de marcar como concluído. |
| `/vue-migration-prep` | Ao criar/refatorar componentes FE. Garante estrutura compatível com Vue/Vuetify. |
| `/design-standardize` | Ao criar/ajustar UI. Aplica Design System v4.2.1 (90/10, tokens, acessibilidade). |
| `/testing-patterns` | Ao criar endpoints, componentes ou agentes. Pirâmide 5 camadas. |

### Skills de Governança e Compliance (Guia v3.4)
| Skill | Quando Usar |
|-------|-------------|
| `/wedo-governance` | Features novas ou revisão estrutural. 13 Crenças + Production Readiness (18 critérios). |
| `/screening-compliance` | Pipelines de screening, WSI, pre-qualification, feedback ao candidato. |
| `/dei-fairness` | Avaliação, ranking, filtragem ou comunicação com candidatos. FairnessGuard + Bias Audit. |
| `/lgpd-data-protection` | Funcionalidades que coletam, processam ou transmitem dados pessoais. |

**Fluxo padrão:**
1. `/feature-impact` → mapear impactos + aprovar plano
2. Implementar
3. `/vue-migration-prep` → portabilidade FE
4. `/design-standardize` → conformidade visual
5. `/testing-patterns` → cobertura das 5 camadas
6. `/feature-audit` → auditoria final

---

## Design System v4.2.1

**Arquivo canônico:** `plataforma-lia/docs/design-system/00-design-system-v4.md`

- **90% monocromático** (grays) + **10% acento WeDo**
- Botões primários: `bg-gray-900`. Cyan (`#60BED1`) apenas para elementos LIA
- Tipografia: Open Sans 85% + Inter 10% + JetBrains Mono 5%
- Border radius: `rounded-md` (8px) — universal
- Sem `box-shadow`: bordas substituem sombras
- Fonte base: 11px (`text-xs` redefinido no tailwind.config.ts)
- Sidebar: 64px colapsada, bg-white, flat design
- Cores: tokens `wedo-*` do tailwind.config.ts. **NUNCA hex hardcoded**
- Dark mode obrigatório em todos os componentes

---

## Padrões de Desenvolvimento (Anti-Vibe-Coding)

### Frontend — Regras para Portabilidade Vue
1. **Separação de concerns**: lógica em hooks (`use-*.ts`), componente = template + binding
2. **Props tipadas**: sempre `interface Props {}`, nunca `type` inline ou `any`
3. **Callbacks `on*`**: `onSelect`, `onMove`, `onChange` → mapeiam para `@event` em Vue
4. **Sem React-only patterns**: evitar `cloneElement`, `Children.map`, `forwardRef`, HOCs
5. **State management**: hooks `use*Store` com `interface State/Actions` → Pinia
6. **Composição via slots**: `children`, `header`, `footer` como props → `<slot>` em Vue
7. **Sem `useContext` excessivo**: preferir props ou hook de store

### Backend — Boas Práticas (FastAPI/Python)
1. **Separação de camadas**: routers finos, lógica em services, models apenas dados
2. **Services stateless**: sem estado global, tudo via parâmetros
3. **Sem código monolítico**: funções <50 linhas, responsabilidade única
4. **Schemas Pydantic explícitos**: request e response tipados em todos os endpoints
5. **Multi-tenant obrigatório**: `company_id` em TODOS os modelos e queries

### Geral
- Componentes/arquivos >150 linhas: extrair lógica para hook/service
- Sem duplicação: verificar se já existe antes de criar
- Nomenclatura: kebab-case (FE), snake_case (BE)

---

## Integrações Externas

| Categoria | Ferramentas |
|-----------|------------|
| LLMs | Anthropic Claude Sonnet 4.5 (primário), Google Gemini (multimodal), OpenAI (fallback) |
| IA/ML | Pearch AI (190M+ perfis), Deepgram (STT), OpenMic.ai (triagem voz), Apify (scraping), LangSmith (observabilidade) |
| Comunicação | Microsoft Teams, Microsoft Graph/Outlook, WhatsApp (Meta+Twilio), Email (SendGrid+Resend+Mailgun), Gupy/Pandapé ATS, Merge |
| Admin/SaaS | WorkOS (SSO/SCIM), HubSpot (CRM), Stripe (billing) |
| Infraestrutura | PostgreSQL (Neon) + pgvector, Redis, RabbitMQ, Celery, Prometheus |

---

## Convenções e Preferências (OBRIGATÓRIAS)

- **Idioma**: Português em toda comunicação
- **Marca**: sempre **WeDOTalent** (nunca variações)
- **Design**: SEMPRE perguntar antes de mudar layout/design — apresentar proposta primeiro
- **Frontend ↔ Backend**: separação total. FE consome API REST. Sem código misto.
- **Chat como interface principal**: LIA interage via conversa natural, não via botões
- **Portabilidade FE**: todo código novo compatível com migração futura Vue/Nuxt

---

## Agentes ReAct (7 Domínios) — Padrão 4 Arquivos

Cada agente em `app/domains/<domain>/agents/`:
`agent.py` | `tool_registry.py` | `system_prompt.py` | `stage_context.py`

**Agentes ativos**: Wizard, Pipeline (PipelineTransitionAgent), Sourcing, Talent, JobsManagement, Kanban, Policy

---

## Sistema de Notificações

5 canais: Bell in-app | Email | Teams | WhatsApp | Chat inline
Serviço central: `app/services/notification_service.py`

---

## Compliance & Governança — Mapa de Arquivos

| Sistema | Arquivo principal | Endpoint |
|---------|------------------|----------|
| LGPD / DSR | `data_request.py`, `consent_management.py` | Portal de titular |
| Granular Consent | `granular_consent_service.py` | `GET/POST /api/v1/consent/granular/{id}` |
| FairnessGuard (3 camadas) | `app/shared/fairness/fairness_guard.py` | Layer 3 opt-in via `FAIRNESS_LAYER3_ENABLED` |
| Bias Audit (Four-Fifths) | `bias_audit_service.py`, `bias_audit.py` | `GET /api/v1/bias-audit/job/{job_id}` |
| BiasAuditSnapshot | `bias_audit_snapshot.py` | `GET /api/v1/bias-audit/job/{job_id}/history` |
| Model Drift Detection | `app/shared/observability/model_drift_service.py`, `app/shared/observability/drift_alert_service.py` | `GET /api/v1/drift/status` |
| Observabilidade (canônica) | `app/shared/observability/` (11 módulos: tracing, structured_logging, callbacks, agent_monitoring_service, agent_health_alert_service, model_drift_service, drift_alert_service, token_tracking_service, token_budget_service, wsi_observability, langsmith) | CI guard: `lia-agent-system/scripts/check_forbidden_imports.py` (Tarefa #343, ADR-017) |
| HITL | `hitl_service.py`, `hitl.py` | `POST /api/v1/hitl/{thread_id}/approve` |
| AuditService | `audit_service.py` | 14/14 agentes com audit trail |
| Circuit Breakers | `circuit_breaker.py`, `admin_circuit_breakers.py` | `GET /api/v1/admin/circuit-breakers` |
| PolicyEngine | `policy_engine_service.py` | `POST /api/v1/policy-engine/apply-sector/{id}` |
| RAG Híbrido | `rag_pipeline_service.py` | `GET /api/v1/candidates/rag-search` |
| Event Store | `event_store_service.py` | `GET /api/v1/candidates/{id}/event-history` |
| PII Masking | `pii_masking.py` | `install_global_pii_masking()` + Celery workers |
| SOC 2 / ISO 27001 | `compliance_controls.py`, `audit_logs.py`, `trust_center.py` | — |

---

## Documentos de Referência Críticos

| Documento | Caminho |
|-----------|---------|
| **Guia WeDOTalent v3.4** | `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` |
| Design System v4.2.1 | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| Inventário de Integrações | `docs/integracao/INVENTARIO_FERRAMENTAS_INTEGRACOES.md` |
| Compliance Architecture | `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md` |
| Mapa de Alertas | `docs/integracao/communication-alerts-map.md` |
| Gaps e Pendências | `docs/analises/ANALISE-GAPS-COMPLETA.md` |
| Metodologia WSI | `docs/WSI_METHODOLOGY_REFERENCE.md` |
| **Glossário Central (fonte única de terminologia)** | `docs/GLOSSARY.md` — sync via `python3 scripts/glossary_sync.py` |
| Manutenção do Glossário | `docs/GLOSSARY_MAINTENANCE.md` |
| **Histórico de Sprints** | `docs/archived/sprint-history.md` |
| Runbook Operacional | `docs/RUNBOOK_DEGRADATION.md`, `docs/RUNBOOK_INCIDENT_PLAYBOOKS.md` |

> **Fonte de verdade para IA = o código**: `app/domains/`, `app/shared/agents/`, `app/tools/`

---

## Estado Atual do Projeto (25/03/2026)

**Sprints concluídos:** A–F + G1–G7 + SEG-1–SEG-5 + AUD-1–AUD-5 + Y1–Y5 + FAR
**Coverage:** 30.99%+ (gate: 30%) | **4680+ testes passando**
**Próxima sprint:** a definir

> Histórico detalhado de implementações → `docs/archived/sprint-history.md`

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
8. /testing-patterns → cobertura das 5 camadas
9. /feature-audit    → auditoria 14 dimensões antes de concluir
```


---

## Regras de Design System (OPT-028 — 2026-03-29)

### Tailwind: transition-colors vs transition-all

```
// DS Rule: Use transition-colors para mudanças de cor/bg, transition-all apenas quando
// height/width/transform também animam. Racional: transition-all em GPU layers causa
// sub-pixel text blur (corrigido em globals.css seletor *, Sprint 1).
// Impacto: 797 ocorrências de transition-all em src/ — NÃO fazer replace em massa.
// Migrar apenas em novos componentes e durante refatorações planejadas.
```

Padrão correto:
- `className="transition-colors duration-200"` — para hover de cor, bg, border
- `className="transition-all duration-200"` — SOMENTE quando width/height/transform também mudam (ex: expansão de painel, slide-in)

---

## Observabilidade — Fonte Única (Task #343, ADR-017)

Tracing, structured logging, LLM callbacks, agent monitoring, drift detection (modelo + alertas), token tracking, token budget, WSI observability e configuração do LangSmith vivem **exclusivamente** em `lia-agent-system/app/shared/observability/`. Os 11 caminhos antigos (`app.shared.tracing`, `app.shared.llm.callbacks`, `app.shared.governance.agent_monitoring_service`, `app.shared.services.*`, `app.domains.{ai,lgpd,analytics,credits}.services.*`, `app.config.langsmith`) foram removidos.

- **Detalhes / mapa módulo a módulo:** `lia-agent-system/docs/CANONICAL_SOURCES_SPEC.md` (§1) e `ARCHITECTURE.md` ADR-017.
- **Lint enforcement:** `lia-agent-system/scripts/check_forbidden_imports.py` (pre-commit hook `G5` + CI). Bloqueia import de qualquer um dos 11 caminhos legados — junto com os caminhos `libs.models.lia_models.*` / `libs.messaging.lia_messaging.*` / `app.models.*` / `app.shared.global_tool_registry` cobertos por ADR-002 / ADR-012.
- **Rodar localmente:** `cd lia-agent-system && python3 scripts/check_forbidden_imports.py`.

Importe sempre via `from app.shared.observability.<modulo> import …`. Reintroduzir um dos caminhos antigos quebra o build.

---

## ⛔ DO NOT MODIFY — Configurações Críticas de Integração

> **ATENÇÃO:** As configurações abaixo são essenciais para o funcionamento da integração Microsoft Teams via Azure Bot.
> **NÃO remova, altere ou comente** nenhum dos itens listados. Qualquer modificação pode quebrar a comunicação entre o Azure Bot e a plataforma LIA.

### 1. Middleware de Autenticação — Rotas Públicas

**Arquivo:** `lia-agent-system/app/middleware/auth_enforcement.py`

A variável `PUBLIC_PREFIXES` **DEVE** incluir `"/api/v1/teams/"`. Esta rota é acessada diretamente pelo Azure Bot Service e não passa por autenticação de usuário.

```python
PUBLIC_PREFIXES = (
    "/api/v1/teams/",   # ← NÃO REMOVER — necessário para Azure Bot (Microsoft Teams)
    ...
)
```

### 2. Secrets do Replit — Credenciais Azure Bot

Os seguintes secrets são credenciais do Azure Bot Registration e **NÃO devem ser removidos**:

| Secret | Descrição |
|--------|-----------|
| `MICROSOFT_APP_ID` | Application (client) ID do Azure Bot Registration |
| `MICROSOFT_APP_PASSWORD` | Client secret do Azure Bot Registration |
| `MICROSOFT_TENANT_ID` | Directory (tenant) ID do Azure AD |

Esses secrets são consumidos pela integração Teams em `app/api/v1/teams/` e são obrigatórios para autenticação com o Microsoft Bot Framework.

---

## Guardrail #766 — Beneficios via tools conversacionais

**Regra (clarification-first, sem fallback silencioso):** as tools `save_company_benefits` (chat) e `import_benefits_from_data` (planilha/site) DEVEM aceitar TODOS os campos do modelo canonico `CompanyBenefit` (provider, value, value_type, percentage_value, value_details, seniority_levels, waiting_period_days, is_mandatory, is_discount, is_highlighted, ...). Paridade com o formulario do Hub eh contratual.

- Se faltar par obrigatorio (`value` sem `value_type`, `value_type=monetary` sem `value`/`value_details`, `value_type=percentage` sem `percentage_value`/`value`), devolver `needs_clarification=True` com `expected_fields` — NUNCA gravar com defaults.
- Toda gravacao audita com `source` ∈ {chat, spreadsheet, website}.
- Texto livre passa por PII masking (LGPD) + FairnessGuard L1 (`name`, `description`, `value_details`).
- Quando adicionar coluna nova ao modelo `CompanyBenefit`, atualizar `CANONICAL_BENEFIT_FIELDS` e o INSERT em `_wrap_save_company_benefits`. O teste `test_canonical_benefit_fields_cover_company_benefit_columns` quebra se isso for esquecido.
