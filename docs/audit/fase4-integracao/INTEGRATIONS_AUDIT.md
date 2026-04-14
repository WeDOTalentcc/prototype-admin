# P18 — Auditoria de Integrações e Automações
## WeDOTalent / LIA Platform
**Data:** 2026-04-14 | **Auditor:** P18 Integration Audit Protocol

---

## Seção 1: Sumário Executivo

| Integração | Provider | Status | Modo Atual | Bloqueador Prod? |
|---|---|---|---|---|
| Email | Mailgun (primário) / Resend (fallback) / SMTP | **SIMULADO** | Sem envkey configurada — enfileira no DB | SIM |
| Email Tracking | Mailgun Webhooks + pixel próprio | **REAL (infraestrutura pronta)** | Aguarda MAILGUN_WEBHOOK_SIGNING_KEY | SIM parcial |
| WhatsApp | Twilio | **SIMULADO** | `ENVIRONMENT=development` → log only | SIM (1 linha fix) |
| Calendário Google | Google Calendar API (OAuth + Service Account) | **DESABILITADO** | `ENABLE_GOOGLE_CALENDAR=False` por padrão | SIM |
| Calendário Microsoft | Microsoft Graph / Teams | **DESABILITADO** | Aguarda AZURE_CLIENT_ID/SECRET/TENANT_ID | SIM |
| Agendamento (agente) | `scheduling_tools.py` | **STUB** | `random.Random` — simulação determinística | SIM |
| Microsoft Teams (notificações) | Microsoft Graph API | **PARCIAL** | Código implementado, creds ausentes | SIM |
| ATS Externos (Merge.dev) | Referenciado em UI/config apenas | **AUSENTE** | Nenhum código de integração real encontrado | SIM |
| LLM Anthropic (Claude) | claude-sonnet-4-6 / claude-haiku-4-5 / claude-opus-4-6 | **REAL** | Produção (key configurada) | NÃO |
| LLM Gemini | gemini-2.5-flash | **REAL** | LLM_FAST_MODEL — tier roteamento | NÃO |
| LLM OpenAI | GPT-4 (opcional) | **CONDICIONAL** | Apenas se OPENAI_API_KEY configurada | NÃO |
| HubSpot CRM | hubspot Python SDK | **CONDICIONAL** | Funciona se HUBSPOT_ACCESS_TOKEN configurado | Parcial |
| WorkOS (SSO) | WorkOS SDK | **REAL** | Estrutura completa — webhook handler implementado | NÃO |
| Pearch AI (sourcing) | API REST v2 | **REAL** | httpx + tenacity retry + circuit breaker | NÃO |
| LinkedIn (scraping) | Scraping próprio | **REAL (limitado)** | Via URL + web scraping — sem API oficial | Parcial |
| Follow-up / Nurture | NurtureSequenceAgent interno | **IMPLEMENTADO** | Celery beat a cada hora — depende de email/WA real | SIM |
| Celery Beat (14 tasks) | Redis / RabbitMQ | **IMPLEMENTADO** | Infra Celery pronta, tasks definidas | NÃO (infra ok) |
| Billing | Iugu / Vindi | **CONDICIONAL** | Providers implementados, creds opcionais | NÃO |

---

## Seção 2: Integrações Externas — Detalhe

### 2.1 Email

**Provider/tecnologia:**
- Mailgun (primário) — `app/domains/communication/services/email_providers/mailgun_provider.py`
- Resend (fallback automático via circuit breaker) — `app/domains/communication/services/email_providers/resend_provider.py`
- Fallback provider genérico — `app/domains/communication/services/email_providers/fallback_provider.py`
- SMTP direto (suportado por config mas não implementado como provider)

**Configuração (env vars necessárias):**
```
MAILGUN_API_KEY     — chave API Mailgun
MAILGUN_DOMAIN      — domínio verificado no Mailgun
RESEND_API_KEY      — fallback automático
SMTP_HOST           — SMTP direto (alternativo)
MAILGUN_WEBHOOK_SIGNING_KEY — para validar webhooks de bounce/open
```

**Modo atual: SIMULADO**
- Código em `app/api/v1/email.py` confirma: `smtp_configured=False` hardcoded no response
- Ao chamar `/email/send`, o email é apenas gravado no banco com status `queued`
- Log: `"QUEUED (SMTP not configured — Funcional — Aguardando Configuracao SMTP)"`
- Nenhuma env var de email está configurada no Replit em produção atual

**O agente pode disparar?** Sim — via `EmailTemplates` (communication_templates.py)
**O agente recebe feedback?** Não — sem provider real, sem webhook de entrega

**Template/conteúdo:**
- Templates Python hardcoded em `app/templates/communication_templates.py`
- Métodos estáticos: `initial_contact`, `screening_passed`, `follow_up`, `interview_scheduled`, `offer_sent`, `candidate_hired_welcome`, `candidate_rejected`, `no_show_first`, `no_show_final`
- Templates HTML em `app/templates/triagem_feedback_email.html`
- Templates por tenant/DB: tabela `email_template` e `recruitment_email_template` — LGPD-safe
- Agente usa templates predefinidos (não gera livre)

**O que falta para produção:**
1. Configurar `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` no Replit Secrets
2. Configurar `MAILGUN_WEBHOOK_SIGNING_KEY` para receber eventos bounce/open
3. Verificar domínio no Mailgun (DNS records)

---

### 2.2 Email Tracking

**Provider/tecnologia:** Mailgun Webhooks + pixel 1x1 GIF próprio

**Infraestrutura (implementada):**
- Pixel de abertura: `GET /api/v1/email-tracking/pixel/{token}.gif`
- Click tracking: `GET /api/v1/email-tracking/click/{token}` → redirect
- Mailgun Event Webhook: `POST /webhooks/mailgun`
- Bounce handler: eventos `failed`, `bounced`, `dropped`, `complained`, `unsubscribed` → atualiza status no DB
- IP armazenado como SHA256 (LGPD-safe)

**Status: REAL (infraestrutura pronta)** — aguarda Mailgun configurado + webhook URL apontando para o sistema

---

### 2.3 WhatsApp

**Provider/tecnologia:** Twilio WhatsApp Business API

**Configuração (env vars):**
```
TWILIO_ACCOUNT_SID    — Account SID
TWILIO_AUTH_TOKEN     — Auth token
TWILIO_WHATSAPP_FROM  — Número WhatsApp (default sandbox: whatsapp:+14155238886)
ENVIRONMENT           — "production" para habilitar envio real
```

**Modo atual: SIMULADO**
- `WhatsAppService.is_development` retorna `True` quando `ENVIRONMENT` é `development/dev/local/test`
- Em modo dev: loga mensagem completa com `[DEV WHATSAPP]`, retorna `status=queued_development`
- SDK Twilio instalado (`TWILIO_SDK_AVAILABLE=True`)
- Credenciais Twilio presentes no Replit (configuradas P17)
- **O único bloqueador é `ENVIRONMENT=development`**

**Fix:** Alterar `ENVIRONMENT` para `production` no Replit Secrets

**Templates HSM:**
- Templates em `WhatsAppTemplates` (communication_templates.py)
- Métodos: `interview_scheduled`, `screening_passed`, `screening_feedback`, `initial_outreach`, `follow_up_reminder`, `offer_extended`
- Templates são texto livre formatado (não HSM aprovados pelo WhatsApp)
- **Gap crítico:** Para outbound proativo fora da janela 24h, precisa templates HSM aprovados pelo WhatsApp Business

**Sessão 24h / janela:**
- Código implementa envio livre em sessão ativa
- Sem controle explícito de janela 24h no código atual
- Para mensagens proativas (fora da sessão), exige HSM — não implementado

**O agente pode disparar?** Sim — via `WhatsAppService.send_template()`
**O agente recebe feedback?** Sim — webhook em `app/api/v1/whatsapp_webhook.py` + `WhatsAppStatus` tracking

---

### 2.4 Calendário — Google Calendar

**Provider/tecnologia:** Google Calendar API (google-api-python-client)

**Configuração (env vars):**
```
ENABLE_GOOGLE_CALENDAR=True              — flag de habilitação (default: False)
GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON    — JSON da service account (Google Workspace)
GOOGLE_CALENDAR_CLIENT_ID               — OAuth 2.0 client ID
GOOGLE_CALENDAR_CLIENT_SECRET           — OAuth 2.0 client secret
GOOGLE_CALENDAR_OAUTH_REDIRECT_URI      — URI de redirect
GOOGLE_CALENDAR_DEFAULT_TIMEZONE        — padrão: America/Sao_Paulo
```

**Modo atual: DESABILITADO**
- `ENABLE_GOOGLE_CALENDAR` não está definido → retorna 400 em todos os endpoints
- Código completamente implementado com OAuth 2.0 + Service Account
- Auto-refresh de token OAuth implementado
- Circuit breaker: `GOOGLE_CALENDAR_CIRCUIT`
- Credenciais por empresa via `company_calendar_credentials` (encrypted)

**O que falta:** Configurar `ENABLE_GOOGLE_CALENDAR=True` + credenciais no Replit

---

### 2.5 Calendário — Microsoft / Teams

**Provider/tecnologia:** Microsoft Graph API (msal + httpx)

**Configuração (env vars):**
```
AZURE_CLIENT_ID       — Azure AD App client ID
AZURE_CLIENT_SECRET   — Azure AD App client secret
AZURE_TENANT_ID       — Azure AD tenant ID
MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI — redirect URI
```

**Modo atual: DESABILITADO**
- Todos os endpoints verificam as 3 env vars antes de prosseguir
- `TeamsCalendarService.is_configured()` retorna False → retorna mensagem de erro amigável
- Código implementado para criar Teams Meetings + Outlook events
- `teams_service.send_message()` é chamado em `job_vacancies/lifecycle.py`

**O que falta:** Configurar app Azure AD com permissões `Calendars.ReadWrite` e `OnlineMeetings.ReadWrite`

---

### 2.6 Agendamento (Agent Tools)

**Provider:** STUB interno — `scheduling_tools.py`

**Status: STUB**
- `check_interviewer_availability`: usa `random.Random(hash(interviewer_id))` — SIMULADO
- `schedule_interview`: retorna ID fake `IV-{hex}` + link fictício `https://calendar.lia.app/interviews/{id}` — SIMULADO
- `send_interview_invitation`: retorna `status=sent` sem enviar nada — SIMULADO
- `reschedule_interview`, `cancel_interview`, `get_interview_status`: todos simulados
- Seed fixo `_SIMULATION_SEED = 42` para reprodutibilidade em testes

**Gap:** Quando Google/Microsoft Calendar estiverem configurados, estas tools precisam ser **substituídas** para chamar `google_calendar_client.py` ou `microsoft_graph_service.py`

---

### 2.7 Microsoft Teams (Notificações)

**Status: PARCIAL — código implementado, creds ausentes**

- `teams_service.send_message()` chamado em lifecycle de vagas
- `TeamsDigestFormatter` em `digest.py`
- Notification channels incluem `teams` como opção válida
- Depende das mesmas creds Azure (AZURE_CLIENT_ID etc.)
- Sem creds → notificações Teams são silenciosamente ignoradas

---

### 2.8 ATS Externos (Merge.dev)

**Status: AUSENTE como integração real**

- Merge.dev aparece apenas como string em configs de UI (`ats_platform: "gupy, pandape, merge"`)
- `journey_mapping.py` lista `"merge": "ats"` como provider conhecido
- **Nenhum código de integração com Merge API** encontrado no codebase
- Circuit breaker em `admin_circuit_breakers.py` menciona "merge" como circuito monitorado mas sem implementação real
- ATS imports/exports são feitos via CSV ou mapeamento manual

---

### 2.9 LLM Providers

Ver Seção 3 para análise detalhada.

---

### 2.10 HubSpot CRM

**Provider/tecnologia:** HubSpot Python SDK (`hubspot` package)

**Configuração (env vars):**
```
HUBSPOT_ACCESS_TOKEN  — Private App token (obrigatório)
HUBSPOT_API_KEY       — legado (suportado em config)
```

**Status: CONDICIONAL**
- `HubSpotService.is_configured` = `bool(HUBSPOT_ACCESS_TOKEN)`
- Se não configurado: sync é silenciosamente ignorado (logs warning, não quebra)
- Implementado: sincronização de Companies, Contacts e Deals
- Trigger: criação de novo cliente via `/clients` → auto-sync HubSpot
- Endpoints manuais: `GET /{client_id}/hubspot/status`, `POST /{client_id}/hubspot/sync`
- Atualiza status de onboarding (welcome_email, workos_configured, sso_enabled)

**O agente pode disparar?** Não diretamente — sync é disparado por eventos de CRUD no Rails/Python
**Status real:** Funcional se token configurado — provavelmente configurado em prod (usado pelo time de vendas)

---

### 2.11 WorkOS (Autenticação / SSO)

**Status: REAL — estrutura completa implementada**

- `app/api/v1/workos.py` — endpoints completos para SSO, SCIM, magic link, directory sync
- `WorkOSRepository` — armazena configurações SSO por tenant
- Webhook handler com validação HMAC: `verify_workos_webhook_signature()`
- Routers: SSO auth, SCIM provisioning, admin management
- Circuit breaker registrado: "workos"
- Rails: `OnboardingMailer` inclui `magic_link_url` no email de welcome

**Env vars necessárias:**
```
WORKOS_API_KEY
WORKOS_CLIENT_ID
WORKOS_WEBHOOK_SECRET
```

---

### 2.12 Pearch AI (Sourcing/Enrichment)

**Status: REAL — integração funcional com fallback**

- `app/domains/sourcing/services/pearch_service.py`
- API v2: `POST /v2/search` com httpx
- Retry: tenacity com exponential backoff (`stop_after_attempt`, `wait_exponential`)
- Circuit breaker: `PEARCH_CIRCUIT` — quando aberto, fallback para RAG Híbrido interno (pgvector + BM25)
- Usado em: search, jd_search, similar_search, evaluation, contact, archetypes, import_export

**Env vars:**
```
PEARCH_API_KEY (ou similar)
PEARCH_BASE_URL
```

**O agente pode disparar?** Sim — NurtureSequenceAgent e SourcingAgent usam Pearch
**Fallback:** RAG interno funciona mesmo sem Pearch

---

### 2.13 LinkedIn (Enrichment)

**Status: SCRAPING — sem API oficial**

- `app/api/v1/company_culture.py` usa scraping de LinkedIn via URL
- Extrai: industry, employee_count, headquarters, locations
- Sem uso de LinkedIn API oficial / Proxycurl / Lusha
- Limitado a informações públicas de empresas (não candidatos)

---

### 2.14 Billing (Iugu / Vindi)

**Status: CONDICIONAL — providers implementados**

- `app/services/billing_providers/iugu_provider.py`
- `app/services/billing_providers/vindi_provider.py`
- `ConsumptionTrackingService` — rastreia uso por tenant para billing

---

## Seção 3: LLM Factory — Análise Detalhada

### 3.1 Providers Configurados

| Provider | Model padrão | Uso | Status |
|---|---|---|---|
| Anthropic Claude | claude-sonnet-4-6 | Agentes principais (reasoning) | REAL |
| Anthropic Claude | claude-haiku-4-5 | Agentes simples (kanban, policy) | REAL |
| Anthropic Claude | claude-opus-4-6 | Tier 3c cascade (último recurso) | REAL |
| Google Gemini | gemini-2.5-flash | Tier 3a cascade (routing barato) | REAL |
| OpenAI GPT | gpt-4 (variável) | Opcional — apenas se OPENAI_API_KEY set | CONDICIONAL |

**Env vars:**
```
ANTHROPIC_API_KEY ou AI_INTEGRATIONS_ANTHROPIC_API_KEY
GEMINI_API_KEY ou GOOGLE_API_KEY ou AI_INTEGRATIONS_GEMINI_API_KEY
OPENAI_API_KEY ou AI_INTEGRATIONS_OPENAI_API_KEY
```

### 3.2 Routing de Modelos por Agente

Arquivo: `app/core/agent_model_config.py`

| Agente | Modelo | Justificativa |
|---|---|---|
| wsi_interview | claude-sonnet-4-6 | Entrevistas — precisão |
| sourcing | claude-sonnet-4-6 | Análise complexa |
| pipeline / pipeline_decision / pipeline_action | claude-sonnet-4-6 | Decisões críticas + fairness |
| job_wizard | claude-sonnet-4-6 | Criação estruturada de vagas |
| analytics | claude-sonnet-4-6 | Insights estratégicos |
| talent / recruiter_assistant | claude-sonnet-4-6 | Conversação rica |
| sourcing_enrich / sourcing_engagement | claude-sonnet-4-6 | Personalização outreach |
| kanban / kanban_* | claude-haiku-4-5 | Tarefas simples — custo baixo |
| policy | claude-haiku-4-5 | Regras estruturadas |
| communication | claude-haiku-4-5 | Geração de mensagens |
| ats_integration / automation | claude-haiku-4-5 | Operações mecânicas |
| pipeline_context / sourcing_planner / sourcing_search | claude-haiku-4-5 | Leitura/estruturação |

**Overridável por env:** `AGENT_MODEL_{NAME_UPPER}=claude-opus-4-6`

### 3.3 Cascade de Custo (LLM Router)

Arquivo: `app/orchestrator/llm_cascade.py`

```
Tier 3a: Gemini Flash  (LLM_FAST_MODEL)    → confidence >= 0.80 → para aqui
Tier 3b: Claude Sonnet (LLM_PRIMARY_MODEL) → confidence >= 0.70 → para aqui
Tier 3c: Claude Opus   (LLM_POWERFUL_MODEL)→ sempre usa se chegou aqui
```

- Fallback seguro: se todos falharem → `domain=recruiter_assistant, confidence=0.3`
- Preferred model (E5): pode injetar modelo preferido antes da cascata

### 3.4 Fallback Implementado

**SIM — 3 níveis:**
1. preferred_model (E5) → falha → cascata padrão
2. Gemini Flash → baixa confiança → Sonnet
3. Sonnet → baixa confiança → Opus
4. Pearch → circuit aberto → RAG interno

### 3.5 Cost Tracking

**SIM — implementado via TenantBudget (Redis):**
- Chave: `token_budget:{company_id}:{YYYY-MM}`
- Por request: `req_cost:{company_id}:{request_id}` → {tokens_input, tokens_output, cost_usd}
- `_estimate_cost(model, tokens_in, tokens_out)` — estimativa por modelo
- Alerta em 80% do budget mensal (`TENANT_TOKEN_BUDGET_ALERT_THRESHOLD`)
- Bloqueio em 100%
- TTL: 32 dias (reset mensal implícito)

### 3.6 Rate Limiting por Tenant

**PARCIAL:**
- `PolicyEngine` com `RateLimitRule` por tenant → configurável via API
- Não há rate limiting automático na LLM layer — é político (definido pelo admin)
- TenantBudget funciona como soft-limit de tokens

---

## Seção 4: Automações Internas

### 4.1 Celery Beat Schedule — 14 Tasks

| Task | Trigger | Ação | Agente? | Status | Gap |
|---|---|---|---|---|---|
| `drift.run_batch` | Diário 06h Brasília | Detecta drift em prompts/modelos | Não | IMPLEMENTADO | Aguarda agendador ativo |
| `audit.apply_lifecycle_policy` | Mensal (dia 1, 03h) | Política de retenção de auditoria | Não | IMPLEMENTADO | — |
| `lgpd.run_cleanup_daily` | Diário 02h Brasília | Limpeza LGPD de dados expirados | Não | IMPLEMENTADO | — |
| `conversation.ttl_cleanup` | Diário 03h Brasília | Expira conversas (LGPD Art. 18) | Não | IMPLEMENTADO | — |
| `briefing.send_daily` | Diário 06h Brasília | Briefing matinal do recrutador | SIM (LIA) | IMPLEMENTADO | Depende email |
| `followup.process_pending` | A cada hora | Reenvia convites WSI não abertos | Não | IMPLEMENTADO | Depende email real |
| `wsi.check_abandoned` | A cada 4h | Detecta WSI abandonado → lembrete | Não | IMPLEMENTADO | Depende email real |
| `feedback.process_pending_sends` | A cada 2h (min 30) | Envia feedbacks aprovados | Não | IMPLEMENTADO | Depende email real |
| `ragas.evaluate_batch` | Diário 03h UTC | Avalia qualidade de respostas (RAGAS) | Não | IMPLEMENTADO | — |
| `routing.recompute_adjustments` | Diário 07h UTC | Recomputa ajustes de confiança do router | Não | IMPLEMENTADO | — |
| `data.retention.run` | Mensal (dia 1, 02h) | Retenção de dados LGPD | Não | IMPLEMENTADO | — |
| `agents.registry.check_reload` | A cada minuto | Hot-reload de agents_registry.yaml | Não | IMPLEMENTADO | — |
| `rag.rebuild_all_domains` | Diário 04h UTC | Reconstrói índices RAG por domínio | Não | IMPLEMENTADO | — |
| `digest.send_weekly` | Segunda-feira 08h | Digest semanal para recrutadores | Não | IMPLEMENTADO | Depende email |
| `ml.feedback.recompute_active_jobs` | Domingo 02h UTC | Recomputa pesos ML adaptativos | Não | IMPLEMENTADO | — |
| `memory.compress_old_episodes` | Diário 03h UTC | Comprime episódios LTM antigos | Não | IMPLEMENTADO | — |

**Total encontrado no celery_app.py: 16 schedules** (P03 mencionava 14 — diferença de contagem de versão)

### 4.2 Follow-up / Nurture

- **NurtureSequenceAgent**: sub-agente de sequências até 5 touchpoints (email + WhatsApp + LinkedIn + SMS)
- HITL: cada step requer aprovação antes do envio
- LGPD: expiração em 180 dias, opt-out imediato disponível
- Tasks Celery correspondentes: `followup.process_pending` (a cada hora) e `wsi.check_abandoned` (a cada 4h)
- **Status:** Lógica implementada, bloqueada por email/WhatsApp não configurados em prod

### 4.3 Automações de Pipeline (Event-driven)

- `app/api/v1/automation/event_handlers/` — handlers para eventos de ciclo de vida
- `handlers_lifecycle.py`: no-show_first, no-show_final, offer_sent, candidate_hired, candidate_rejected → dispara emails automaticamente
- `handlers_interview.py`: interview_scheduled → email de convite
- **Status:** Lógica completa, bloqueada por email simulado

---

## Seção 5: Template Engine

### 5.1 Engine Utilizada

**Python strings (f-strings hardcoded)** — sem Jinja2 nem Mustache no core

- Templates em `app/templates/communication_templates.py` — métodos estáticos Python
- Email HTML em `app/templates/triagem_feedback_email.html` — HTML estático com variáveis
- Rails usa ERB para `OnboardingMailer`

### 5.2 Templates Centralizados vs. Hardcoded

| Tipo | Localização | Centralizado? |
|---|---|---|
| Email de comunicação | `communication_templates.py` EmailTemplates | SIM (Python) |
| WhatsApp | `communication_templates.py` WhatsAppTemplates | SIM (Python) |
| Email HTML triagem | `templates/triagem_feedback_email.html` | SIM (HTML) |
| Templates por tenant | DB: `email_template`, `recruitment_email_template` | SIM (DB) |
| Rails onboarding | `OnboardingMailer` ERB | SIM (Rails) |
| Fixtures padrão | `data/fixtures/email_default_templates.json` | SIM (JSON) |

### 5.3 O Agente Usa Templates ou Gera Texto Livre?

**Misto:**
- Para comunicações estruturadas (convites, feedbacks, ofertas): usa `EmailTemplates.*` e `WhatsAppTemplates.*`
- Para conversação no chat: gera texto livre via LLM
- NurtureSequenceAgent: gera mensagens de outreach personalizadas (texto livre com contexto do candidato)

### 5.4 Personalização por Tenant

**PARCIAL:**
- Templates DB por tenant/empresa (tabela `email_template` com `company_id`)
- `HiringPolicy` — configura tom e regras de comunicação por empresa
- Sem theming HTML por tenant (todas empresas usam mesmo HTML base)

### 5.5 I18n

**AUSENTE — somente português brasileiro**
- Todos os templates em pt-BR hardcoded
- Sem sistema de internacionalização
- `DATA_PROCESSING_NOTICE` em pt-BR (LGPD)

---

## Seção 6: Gaps e Oportunidades

### A. Integrações Quebradas (existem, não funcionam)

| ID | Integração | Problema | Impacto |
|---|---|---|---|
| A1 | Email (todos providers) | Sem env vars configuradas → status sempre `queued`, nunca enviado | CRÍTICO |
| A2 | WhatsApp Twilio | `ENVIRONMENT=development` → sem envio real | CRÍTICO |
| A3 | scheduling_tools.py | Retorna dados `random` em vez de calendar real | ALTO |
| A4 | Follow-up tasks Celery | Dependem de email/WA — executam mas não enviam | ALTO |
| A5 | Briefing diário | Celery task existe mas email não entrega | MÉDIO |

### B. Integrações Fantasma (código existe, nunca é chamado)

| ID | Integração | Evidência | Observação |
|---|---|---|---|
| B1 | Google Calendar | `ENABLE_GOOGLE_CALENDAR` default False → never reached | Código completo mas flag off |
| B2 | Microsoft Teams Meetings | Creds ausentes → service.is_configured() sempre False | Código completo |
| B3 | Merge.dev ATS | Listado em configs/UI, sem SDK ou chamadas API | Só string reference |
| B4 | Resend provider | Fallback implementado, mas Mailgun também está off | Nunca alcançado |
| B5 | `agent-registry-hot-reload` (a cada min) | Roda sem parar mas sem efeito se registry não muda | Overhead desnecessário em dev |

### C. Integrações Prometidas mas Ausentes (agente promete, infra não suporta)

| ID | Promessa | Realidade | Gap |
|---|---|---|---|
| C1 | Agente agenda entrevista com link real | `schedule_interview` retorna `https://calendar.lia.app/interviews/IV-{fake}` — URL inexistente | Google/MS Calendar não configurados |
| C2 | "Convite enviado ao candidato" | `send_interview_invitation` retorna `status=sent` sem enviar nada | Depende de email real |
| C3 | WhatsApp proativo (outbound HSM) | Templates Python não são HSM aprovados — rejeitados pelo WhatsApp fora da janela 24h | Precisa aprovar templates no WhatsApp Business |
| C4 | "Follow-up automático enviado" | Task Celery roda, mas sem delivery real | A1 + A2 |
| C5 | Integração com Gupy/Pandape/Greenhouse via Merge | UI menciona, código não implementa | Merge.dev ausente |

### D. Oportunidades de Agentificação

| ID | Automação Atual | Oportunidade IA | Valor |
|---|---|---|---|
| D1 | Briefing diário fixo | LIA gera briefing personalizado com insights do dia (já parcialmente implementado) | ALTO |
| D2 | Follow-up WSI com template fixo | LIA personaliza mensagem baseada em perfil do candidato + cargo | MÉDIO |
| D3 | Classificação de rejeições | ML Feedback task recomputa — LIA pode explicar padrão ao recruiter | MÉDIO |
| D4 | Triagem de bounces de email | Identificar candidatos com email inválido → sugerir WhatsApp como fallback | ALTO |
| D5 | Digest semanal | LIA gera narrativa contextualizada (não só dados) | MÉDIO |

---

## Seção 7: Top 10 Fixes por ROI

| Prioridade | Fix | Esforço | Impacto | Desbloqueio |
|---|---|---|---|---|
| 1 | Configurar `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` + `MAILGUN_WEBHOOK_SIGNING_KEY` no Replit | 30 min | CRÍTICO | Desbloqueia A1, A4, A5, C2, C4, follow-up, briefing, digest |
| 2 | Alterar `ENVIRONMENT=production` no Replit Secrets | 2 min | CRÍTICO | Desbloqueia A2, WhatsApp real (já tem creds Twilio) |
| 3 | Aprovar templates HSM no WhatsApp Business Manager | 1-5 dias (burocracia WA) | ALTO | C3 — outbound proativo sem limite de janela 24h |
| 4 | Configurar `ENABLE_GOOGLE_CALENDAR=True` + service account JSON | 2-4h (setup GCP) | ALTO | B1, A3 parcial — agendamento real |
| 5 | Implementar integração real em `scheduling_tools.py` | 1-2 dias dev | ALTO | A3, C1 — fim das respostas fake |
| 6 | Configurar creds Azure AD (AZURE_CLIENT_ID/SECRET/TENANT_ID) | 2-4h (setup Azure) | MÉDIO | B2 — Teams meetings reais |
| 7 | Configurar `HUBSPOT_ACCESS_TOKEN` | 30 min | MÉDIO | HubSpot sync em prod (se não estiver ativo) |
| 8 | Implementar Merge.dev SDK para ATS externos | 3-5 dias dev | MÉDIO | B3, C5 — imports reais de Gupy/Pandape |
| 9 | Reduzir frequência de `agent-registry-hot-reload` de 1min para 5min | 5 min | BAIXO | B5 — overhead Redis |
| 10 | Adicionar controle de janela 24h no WhatsApp + fallback para HSM | 1 dia dev | MÉDIO | C3 — conformidade WhatsApp Business Policy |

---

## Seção 8: Tabela Completa de Findings

| ID | Severidade | Integração | Descrição | Fix Recomendado | Esforço |
|---|---|---|---|---|---|
| F01 | CRÍTICO | Email | Sem provider configurado — todo email fica em `queued` no DB forever | Configurar MAILGUN_API_KEY + MAILGUN_DOMAIN no Replit | 30 min |
| F02 | CRÍTICO | WhatsApp | `ENVIRONMENT=development` → Twilio nunca envia | Mudar ENVIRONMENT=production | 2 min |
| F03 | ALTO | Calendário | scheduling_tools.py retorna dados `random` — agente confirma agendamentos falsos | Conectar Google Calendar API | 1-2 dias |
| F04 | ALTO | Email Tracking | Pixel e webhooks implementados mas Mailgun não configurado → sem dados de abertura | F01 desbloqueia automaticamente | — |
| F05 | ALTO | Follow-up | Celery tasks rodam a cada hora, mas sem delivery real de email/WA | F01 + F02 desbloqueia | — |
| F06 | ALTO | Merge.dev | Plataforma referenciada em UI como opção de ATS mas sem código de integração | Implementar SDK Merge.dev | 3-5 dias |
| F07 | MÉDIO | WhatsApp HSM | Templates Python não são HSM aprovados — outbound proativo rejeitado fora da janela 24h | Registrar e aprovar templates no WA Business | 1-5 dias burocracia |
| F08 | MÉDIO | Google Calendar | Flag ENABLE_GOOGLE_CALENDAR=False por default — código nunca é executado | Habilitar flag + configurar creds | 2-4h |
| F09 | MÉDIO | Microsoft Teams | Código completo mas AZURE_* creds ausentes | Registrar app Azure AD + configurar creds | 2-4h |
| F10 | MÉDIO | Rails Mailer | `application_mailer.rb` usa `from: "from@example.com"` hardcoded — email inválido | Atualizar para domínio real + configurar Action Mailer | 1h |
| F11 | MÉDIO | Rails Jobs | Apenas `MessageJob` existe — usa `MessageSampleService` (provavelmente stub) | Verificar e implementar serviço real | 1-2 dias |
| F12 | BAIXO | HubSpot | Funcional se token configurado, mas sem confirmação de que está ativo em prod | Verificar HUBSPOT_ACCESS_TOKEN no Replit | 5 min |
| F13 | BAIXO | Celery hot-reload | Frequência de 1 minuto gera overhead desnecessário | Alterar para crontab(minute="*/5") | 5 min |
| F14 | BAIXO | I18n Templates | Todos templates hardcoded em pt-BR — sem suporte a outras línguas | Implementar i18n se necessário | 2-3 dias |
| F15 | INFO | WorkOS | Estrutura completa implementada — verificar WORKOS_API_KEY/CLIENT_ID configurados | Confirmar creds no Replit | 5 min |
| F16 | INFO | Pearch AI | Circuit breaker + fallback RAG implementados — robustez adequada | Nenhum fix necessário | — |
| F17 | INFO | LLM Cascade | 3-tier cascade Gemini→Sonnet→Opus implementado com cost tracking | Nenhum fix necessário | — |

---

## Validação Final

1. **Cada integração com status REAL/SIMULADO/STUB/QUEBRADO?** SIM — coberto na Seção 1 e 2
2. **LLM Factory analisado (providers, routing, fallback, cost)?** SIM — Seção 3
3. **Automações Celery/APScheduler inventariadas?** SIM — 16 tasks na Seção 4
4. **Template engine analisada?** SIM — Seção 5 (Python f-strings, sem Jinja2)
5. **Follow-up/nurture sequences analisadas?** SIM — Seção 4.2
6. **Gaps A, B, C, D mapeados?** SIM — Seção 6
7. **Top 10 fixes por ROI?** SIM — Seção 7

---

*Gerado por P18 Integration Audit Protocol — 2026-04-14*
