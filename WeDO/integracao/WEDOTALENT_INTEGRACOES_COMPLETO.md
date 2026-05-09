# WeDo Talent - Guia Completo de Integrações e Arquitetura

> **Documento Unificado de Análise de Viabilidade, Custos e Arquitetura**

**Versão:** 3.7 (Auditoria de Código — Maio 2026)
**Data:** 9 de Maio de 2026
**Autor:** Equipe WeDo Talent

> ⚠️ **Atualização v3.7:** Documento revisado contra o código real do monorepo
> (`lia-agent-system/` FastAPI + `plataforma-lia/` Next.js + `ats_api/` Rails legacy).
> Versões 3.0–3.6 foram escritas em janeiro/2026 e tinham status incorretos para
> várias integrações (Merge, MS Graph, Mailgun, OpenMic, Sentry, Elasticsearch,
> Celery, Resend, Twilio Voice). Veja a nova **Seção 0 — Auditoria de
> Conformidade Maio/2026** logo abaixo do Resumo Executivo para o estado real
> das integrações verificadas no código. Onde havia conflito entre tabelas
> antigas e a auditoria, **a Seção 0 é a fonte de verdade**.

---

## RESUMO EXECUTIVO

Este documento consolida toda a análise de integrações, custos e arquitetura do WeDo Talent, organizado em dois capítulos principais:

| Capítulo | Escopo | Ferramentas | Status Predominante |
|----------|--------|-------------|---------------------|
| **Capítulo 1: WeDo Talent Admin** | Gestão de clientes, billing, compliance | HubSpot (CRM), WorkOS (SSO/SCIM), Vanta/Drata, Privacy Tools, Warden AI; Stripe e ProfitWell **planejados** (não implementados) | Parcial |
| **Capítulo 2: WeDo Talent Plataforma** | Funil de Talentos e Vagas | Claude, Gemini (incl. Live Audio), OpenAI, LangGraph/LangChain/LangSmith, Pearch, Apify, Deepgram, OpenMic, Mailgun, Resend, Twilio (WhatsApp + Voice), MS Graph, MS Teams, Merge.dev, Gupy, Pandapé, Sentry, Elasticsearch, Redis, RabbitMQ, Celery | Core do produto — produção |

### Filosofia: Desenvolver Mínimo, Integrar Máximo

> **70% SaaS + 30% Interno** = Menos código para manter, mais tempo para features de valor

---

## SEÇÃO 0 — AUDITORIA DE CONFORMIDADE (Maio/2026)

> **Fonte de verdade.** Tabela construída inspecionando o código real em
> `lia-agent-system/`, `plataforma-lia/` e `ats_api/` (legacy). Substitui as
> colunas de status das tabelas legadas (Cap. 1/2 e Apêndice A) onde houver
> divergência. Preços/uso permanecem nas seções originais — aqui só consta
> *o que de fato existe no código* em Maio/2026.

### 0.1 Integrações em Produção (verificadas no código)

| # | Provider | Categoria | Onde no código | Auth | Status |
|---|----------|-----------|----------------|------|--------|
| 1 | **Anthropic Claude** | LLM principal | `lia-agent-system` via `langchain-anthropic>=1.1.0`; `LLM_PRIMARY_MODEL=claude-sonnet-4-6` | `ANTHROPIC_API_KEY` | ✅ Produção |
| 2 | **Google Gemini** | LLM rápido + roteador + STT live | `langchain-google-vertexai>=3.0.3`; `LLM_FAST_MODEL=gemini-2.5-flash`; `app/domains/voice/services/gemini_live_audio_service.py` | `AI_INTEGRATIONS_GEMINI_API_KEY` ou `GOOGLE_APPLICATION_CREDENTIALS` | ✅ Produção |
| 3 | **OpenAI** | LLM alternativo / Whisper / TTS PSTN | `langchain-openai>=1.0.3`; usado como fallback PSTN no pipeline de voz | `OPENAI_API_KEY` ou `AI_INTEGRATIONS_OPENAI_API_KEY` | ✅ Produção (não “opcional”) |
| 4 | **LangChain** | Framework LLM | `langchain>=1.0.8` | n/a | ✅ Produção |
| 5 | **LangGraph** | Orquestração multi-agente | `langgraph>=0.4.1` + `langgraph-checkpoint-postgres>=2.0.8` | n/a | ✅ Produção |
| 6 | **LangSmith** | Tracing / eval | `langsmith>=0.7.25` | `LANGCHAIN_API_KEY` | ✅ Produção (não “em progresso”) |
| 7 | **Pearch AI** | Sourcing 800M+ perfis | Config `HTTP_TIMEOUT_PEARCH_*` em `lia_config/config.py` + `ats_api/app/services/pearch/search_service.rb` | `PEARCH_API_KEY` | ✅ Produção |
| 8 | **Apify** | LinkedIn scraping | Config `HTTP_TIMEOUT_APIFY_*` + `ats_api/app/services/apify/linkedin_search_service.rb` | `APIFY_API_TOKEN` | ✅ Produção (não “planejado”) |
| 9 | **Deepgram** | STT entrevistas | `app/services/voice/deepgram_service.py` | `DEEPGRAM_API_KEY` | ✅ Produção |
| 10 | **OpenMic.ai** | Voice screening assíncrono | `app/services/voice/openmic_service.py` + `app/api/v1/openmic_webhook.py` + `app/jobs/tasks/voice.py` | `OPENMIC_API_KEY` + webhook secret | ✅ Produção (não “planejado”) |
| 11 | **Mailgun** | Email transacional (primário) | `app/services/email_providers/mailgun_provider.py` + `app/api/v1/mailgun_webhooks.py` | `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` + signing key | ✅ Produção |
| 12 | **Resend** | Email transacional (fallback) | `app/services/email_providers/resend_provider.py` (`resend==2.19.0`) | `RESEND_API_KEY` | ✅ Produção (não documentado anteriormente) |
| 13 | **Twilio** | WhatsApp + SMS + Voice PSTN | `twilio==9.4.0`; `app/services/whatsapp_client.py` + `app/api/v1/whatsapp_webhook.py` | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | ✅ Produção |
| 14 | **Twilio Voice SDK (browser)** | VoIP do recrutador | `plataforma-lia` `@twilio/voice-sdk@^2.11.1` | OAuth Twilio | ✅ Produção (frontend) |
| 15 | **WhatsApp Business API** | Mensagens candidatos | Via Twilio (item 13) | mesmo do Twilio | ✅ Produção (não “em progresso”) |
| 16 | **Microsoft Graph** | Calendar + Email + Teams | `msgraph-sdk==1.12.0` + `msal>=1.31.1`; `MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI` | `AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET` | ✅ Produção (não “em progresso”) |
| 17 | **Microsoft Teams JS SDK** | Embed do app no Teams | `plataforma-lia` `@microsoft/teams-js@^2.51.0` | n/a | ✅ Produção (frontend) |
| 18 | **Merge.dev** | Unified ATS/HRIS | `app/domains/ats_integration/services/ats_clients/merge.py` + `app/api/v1/merge_webhooks.py` | `MERGE_API_KEY` + Account Token | ✅ Produção (não “planejado”) |
| 19 | **Gupy** | ATS BR (direto) | `app/domains/ats_integration/services/ats_clients/gupy.py` | API Key Bearer | ✅ Produção (não “via Merge”) |
| 20 | **Pandapé** | ATS BR (direto) | `app/domains/ats_integration/services/ats_clients/pandape.py` | API Key Bearer | ✅ Produção (não “via Merge”) |
| 21 | **wedotalent_rails** | Ponte ATS legado | `app/domains/ats_integration/services/ats_clients/wedotalent_rails.py` | Rails JWT compartilhado | ✅ Produção (interno) |
| 22 | **WorkOS** | SSO/SCIM/MFA/Audit | Backend `workos` + frontend `@workos-inc/node@^7.82.0`; `app/middleware/auth_enforcement.py` | `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` + `WORKOS_WEBHOOK_SECRET` | ✅ Produção |
| 23 | **HubSpot CRM** | Sync clientes | `app/shared/services/hubspot_service.py` + `app/domains/company/services/hubspot_service.py` + `app/api/v1/clients/clients_hubspot.py` | `HUBSPOT_ACCESS_TOKEN` (Private App) | ✅ Produção |
| 24 | **PostgreSQL** | DB principal + RLS | `sqlalchemy==2.0.36` + `alembic==1.14.0` | `DATABASE_URL` | ✅ Produção |
| 25 | **Redis** | Cache + sessões + Fernet PII | `redis==5.2.0`; `REDIS_URL` + `REDIS_ENCRYPTION_KEY` (Fernet) | URL + key | ✅ Produção (chave obrigatória em prod) |
| 26 | **RabbitMQ (CloudAMQP)** | Broker de eventos | `aio-pika==9.5.3`; `RABBITMQ_URL` + `RABBITMQ_EXCHANGE=rh_platform` | URL AMQP | ✅ Produção (não “planejado”) |
| 27 | **Celery** | Workers + cron | `celery==5.4.0`; `app/jobs/celery_tasks.py` + `tasks/voice.py` etc. | usa Redis ou RabbitMQ como broker | ✅ Produção (não documentado) |
| 28 | **Elasticsearch** | Search avançada candidatos | `ELASTICSEARCH_URL` em config; `SEARCH_BACKEND=postgres|elasticsearch`; jobs em `ats_api/app/jobs/elasticsearch/` | URL + API key | ✅ Produção (não documentado) |
| 29 | **Sentry** | Error tracking + perf | Backend `sentry-sdk[fastapi]==2.19.2` em `app/main.py`; frontend `@sentry/nextjs@^10.46.0` (3 configs: client/edge/server) | `SENTRY_DSN` | ✅ Produção (não “planejado”) |
| 30 | **Replit (host)** | Hosting MVP / dev | Workflows `dev-server`/`lia-backend` | n/a | ✅ Produção |
| 31 | **GitHub** | VCS + integração nativa | Plugin `github==1.0.0` instalado | OAuth | ✅ Produção |
| 32 | **Jira (jira.js)** | Embed gestão de projetos | `plataforma-lia` `jira.js@^5.3.1` + plugin `jira==1.0.0` | OAuth | ✅ Produção (não “opcional”) |
| 33 | **OTel (Tracing)** | Tracing distribuído | `OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_TRACES_ENABLED=true` (config) | OTLP HTTP | 🔄 Pronto na infra (endpoint vazio = desligado por padrão) |

### 0.2 Integrações em Desenvolvimento (stubs em código)

| Provider | Onde | Status real | Nota |
|----------|------|-------------|------|
| **Vindi** (billing BR) | `app/services/billing_providers/vindi_provider.py` | 🔄 Stub | Provider abstraído, sem chave em produção |
| **Iugu** (billing BR) | `app/services/billing_providers/iugu_provider.py` | 🔄 Stub | idem |

### 0.3 Integrações Documentadas mas NÃO Implementadas

| Provider | Status no doc antigo | Status real (Maio/2026) | Recomendação |
|----------|----------------------|--------------------------|--------------|
| **Stripe** | ✅ “Integrado” | ❌ Não há cliente Stripe em `lia-agent-system`, `ats_api` ou `plataforma-lia` | Reclassificar como 📋 Planejado (stack BR usa Vindi/Iugu); Stripe vira opção para mercado US/EU |
| **ProfitWell** | ✅ “Integrado” | ❌ Sem código | Reclassificar como 📋 Planejado |
| **Vanta / Drata** | 📋 Planejado | ❌ Apenas strings cosméticas em UI | Manter 📋 Planejado |
| **Privacy Tools** | 📋 Planejado | ❌ Sem código | Manter 📋 Planejado |
| **Warden AI** | 📋 Planejado | ❌ Sem código | Manter 📋 Planejado |

### 0.4 Erros Conhecidos das Versões 3.0–3.6 (corrigidos pontualmente)

| Bug no doc | Onde aparecia | Correção |
|------------|---------------|----------|
| `SENDGRID_API_KEY` na seção Mailgun | §2.6.3 e Apêndice D | Trocado por `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` |
| `STACKONE_API_KEY` no checklist ATS | Apêndice D | Trocado por `MERGE_API_KEY` + `MERGE_ACCOUNT_TOKEN` |
| “Merge | Merge” duplicado | §2.1.1 mapa, Cap. 2.7.1/2.7.2, Apêndice A linhas 13–14, Apêndice B linhas 8–9 | Marcado 2.7.2 como **DEPRECATED — duplicação errada do mesmo produto** |
| “Backend Rails” (em diversos guias) | Cap. 1.4 (HubSpot), Apêndice G | Backend de produção é **FastAPI/Python** (`lia-agent-system`); Rails (`ats_api`) é legacy/system-of-record. Snippets Ruby permanecem como referência futura para migração. |
| Status “🔄 Em Progresso” para MS Graph, WhatsApp, Mailgun, Deepgram | Tabela inicial e §2.16.1 | Reclassificados como ✅ Produção |
| Status “📋 Planejado” para Merge, Apify, Sentry, RabbitMQ, OpenMic | Tabela inicial e §2.16 | Reclassificados como ✅ Produção |

### 0.5 Integrações Sub-Documentadas (presentes no código, mas sem capítulo próprio)

Estas integrações **funcionam em produção** mas não têm seção de viabilidade/custo no doc original. Devem ganhar §§ próprios em uma futura v3.8:

- **Resend** (fallback de email) — `resend==2.19.0`
- **Sentry** (error tracking BE+FE) — `sentry-sdk[fastapi]` + `@sentry/nextjs`
- **Elasticsearch** (search candidatos) — `ELASTICSEARCH_URL`
- **Celery** (background jobs) — `celery==5.4.0`
- **Twilio Voice SDK browser** (`@twilio/voice-sdk`) — VoIP do recrutador
- **Microsoft Teams JS SDK** (`@microsoft/teams-js`) — embed do app no Teams
- **Gemini Live Audio API** — STT em tempo real para voice screening
- **OpenTelemetry** — `OTEL_*` configs prontos

### 0.6 Visão Numérica Atualizada

- Integrações **realmente em produção** (verificadas no código): **31** ativas + **2** stubs (Vindi/Iugu) + **1** opcional (OTel) = **34**
- Integrações **planejadas** (no doc, sem código): Stripe, ProfitWell, Vanta, Drata, Privacy Tools, Warden AI = **6**
- Integrações **opcionais** (Apêndice F): 50+ ferramentas comparativas — manter como referência

> Quando os números/contagens nas tabelas legadas (“25+ Integrações”,
> “35+ Integrações”) divergirem de 0.6, **0.6 é a contagem correta**.

---

## TABELA CONSOLIDADA DE FERRAMENTAS E INTEGRAÇÕES

> **Referência Central** - Todas as ferramentas, plataformas e integrações do ecossistema WeDo Talent

### Legenda de Status
- ✅ **Integrado** - Já implementado e funcionando
- 🔄 **Em Progresso** - Implementação em andamento
- 📋 **Planejado** - Previsto para implementação futura
- ⏸️ **Opcional** - Implementar conforme demanda de clientes

### Tabela Completa

| # | Ferramenta | Categoria | Para Que Serve | Website | Usuário | Email Login | Status | Tipo Cobrança | Pricing | Custo Base/Mês | 1 Cliente (MVP) | 5 Clientes | 10 Clientes | 50 Clientes | Free Tier/Limite |
|---|------------|-----------|----------------|---------|---------|-------------|--------|---------------|---------|----------------|-----------------|------------|-------------|-------------|------------------|
| **CAPÍTULO 1: ADMIN** |
| 1 | **Stripe** | Billing | Pagamentos, assinaturas, invoices | stripe.com | - | - | ✅ Integrado | % transação | 2.9% + $0.30/tx | $0 (só tx) | ~$29 | ~$145 | ~$290 | ~$1.450 | Grátis, paga por transação |
| 2 | **ProfitWell** | Métricas SaaS | MRR, churn, LTV, ARPU analytics | profitwell.com | - | - | ✅ Integrado | Gratuito | $0 | $0 | $0 | $0 | $0 | $0 | 100% grátis para sempre |
| 3 | **HubSpot CRM** | CRM | Gestão de clientes, deals, contatos | hubspot.com | - | - | ✅ Integrado | Freemium | Free → $15/user | $0 | $0 | $0 | $45 | $225 | Free CRM ilimitado |
| 4 | **HubSpot Onboarding** | Onboarding | Pipeline de Tickets + Workflows nativos | hubspot.com | - | - | ✅ Integrado | Grátis | $0 (incluso no HubSpot CRM) | $0 | $0 | $0 | $0 | $0 | 100% grátis no CRM |
| 5 | **WorkOS** | Auth SSO/SCIM | SSO enterprise, MFA, Directory Sync | workos.com | - | - | ✅ Integrado | Por conexão | $50/conexão SSO | $0 | $50 | $250 | $500 | $2.500 | Free sem SSO ativo |
| 6 | **Vanta** | Compliance | SOC 2, ISO 27001, automação compliance | vanta.com | - | - | 📋 Planejado | Assinatura anual | ~$1.500/mês | $0 | $0 | $1.500 | $1.500 | $2.000 | Trial disponível |
| 7 | **Drata** | Compliance | Alternativa ao Vanta, SOC 2, GDPR | drata.com | - | - | ⏸️ Opcional | Assinatura anual | ~$1.500/mês | $0 | $0 | $1.500 | $1.500 | $2.000 | Trial disponível |
| 8 | **Privacy Tools** | LGPD | Portal do titular, RIPD, compliance BR | privacytools.com.br | - | - | 📋 Planejado | Assinatura | R$ 300-600/mês | R$ 300 | R$ 300 | R$ 300 | R$ 400 | R$ 600 | Demo disponível |
| 9 | **Warden AI** | Bias Audit | Auditoria de viés, NYC LL144, EU AI Act | warden.ai | - | - | 📋 Planejado | Por análise | Sob consulta | $0 | $0 | $200 | $400 | $1.000 | Demo disponível |
| **CAPÍTULO 2: PLATAFORMA - LLMs & IA** |
| 10 | **Claude (Anthropic)** | LLM Principal | Screening, JD generation, chat, análises | anthropic.com | - | - | ✅ Integrado | Por token | $3/1M input, $15/1M output | $10 | $25 | $125 | $250 | $1.250 | $5 créditos iniciais |
| 11 | **Gemini (Google)** | LLM Fallback | Voice-to-text, search, fallback | ai.google.dev | - | - | ✅ Integrado | Por token | $0.075/1M chars | $0 | $0.50 | $2.50 | $5 | $25 | 1M tokens/mês grátis |
| 12 | **OpenAI** | LLM Alternativo | Embeddings, fallback opcional | openai.com | - | - | ⏸️ Opcional | Por token | $0.50/1M tokens | $0 | $0 | $0 | $0 | $0 | $5 créditos iniciais |
| **CAPÍTULO 2: PLATAFORMA - ORQUESTRAÇÃO** |
| 13 | **LangGraph** | Orquestração | Multi-agent workflows, state machine | langchain.com | - | - | ✅ Integrado | Open Source | $0 | $0 | $0 | $0 | $0 | $0 | 100% grátis |
| 14 | **LangChain** | Framework | Chains, prompts, tools, memory | langchain.com | - | - | ✅ Integrado | Open Source | $0 | $0 | $0 | $0 | $0 | $0 | 100% grátis |
| 15 | **LangSmith** | Observabilidade | Traces, debugging, evaluations LLM | smith.langchain.com | - | - | 🔄 Em Progresso | Por trace | $0-$39/mês | $0 | $0 | $0 | $39 | $200 | 5.000 traces/mês grátis |
| **CAPÍTULO 2: PLATAFORMA - SOURCING & BUSCA** |
| 16 | **Pearch AI** | Sourcing | Banco 800M+ perfis, semantic search | pearch.ai | - | - | ✅ Integrado | Por crédito | $0.10-0.50/perfil | $0 | $50 | $250 | $500 | $2.500 | Demo disponível |
| 17 | **Apify** | Scraping | LinkedIn scraping, enriquecimento | apify.com | - | - | 📋 Planejado | Por uso | $0.25/1000 results | $0 | $0.50 | $2.50 | $5 | $25 | $5 créditos/mês grátis |
| **CAPÍTULO 2: PLATAFORMA - VOZ & SPEECH** |
| 18 | **Deepgram** | STT | Speech-to-text, transcrição entrevistas | deepgram.com | - | - | 🔄 Em Progresso | Por minuto | $0.0043/min | $0 | $0.50 | $2.50 | $5 | $25 | $200 créditos grátis |
| 19 | **OpenMic.ai** | Voice Interview | Entrevistas por voz, screening automático | openmic.ai | - | - | 📋 Planejado | Por entrevista | ~$5/entrevista | $0 | $50 | $250 | $500 | $2.500 | Demo disponível |
| 20 | **ElevenLabs** | TTS | Text-to-speech, voice cloning | elevenlabs.io | - | - | ⏸️ Opcional | Por caractere | $0.30/1K chars | $0 | $0 | $0 | $22 | $110 | 10K chars/mês grátis |
| **CAPÍTULO 2: PLATAFORMA - COMUNICAÇÃO** |
| 21 | **Mailgun** | Email | Envio de emails transacionais | mailgun.com | - | - | ✅ Integrado | Por email | $0.80/1000 emails | $0 | $4 | $8 | $16 | $80 | 5.000 emails/mês grátis (3 meses) |
| 22 | **Twilio** | SMS/Voice | SMS, WhatsApp API, voice calls | twilio.com | - | - | ✅ Integrado | Por mensagem | $0.0079/SMS | $0 | $5 | $25 | $50 | $250 | Trial $15 créditos |
| 23 | **WhatsApp Business API** | Mensagens | Comunicação candidatos via WhatsApp | business.whatsapp.com | - | - | 🔄 Em Progresso | Por conversa | $0.05-0.15/conv | $0 | $5 | $25 | $50 | $250 | 1.000 msg/mês grátis |
| 24 | **MS Graph** | Calendar/Email | Agendamento entrevistas, calendário | graph.microsoft.com | - | - | 🔄 Em Progresso | Gratuito | $0 (M365 incluso) | $0 | $0 | $0 | $0 | $0 | 100% grátis com M365 |
| **CAPÍTULO 2: PLATAFORMA - INTEGRAÇÕES ATS** |
| 25 | **Merge** | ATS Unified | API unificada 50+ ATS/HRIS | merge.dev | - | - | 📋 Planejado | Por conexão | $65/conexão | $0 | $0 | $195 | $390 | $1.950 | 3 conexões grátis |
| 26 | **Gupy** | ATS Brasil | Integração direta Gupy (BR) | gupy.io | - | - | 📋 Planejado | Via Merge | Incluído | $0 | $0 | $0 | $0 | $0 | Via Merge |
| 27 | **Pandapé** | ATS Brasil | Integração direta Pandapé (BR) | pandape.com | - | - | 📋 Planejado | Via Merge | Incluído | $0 | $0 | $0 | $0 | $0 | Via Merge |
| **INFRAESTRUTURA** |
| 29 | **Replit** | Hosting | Desenvolvimento e hospedagem | replit.com | - | - | ✅ Integrado | Por uso | $20-100/mês | $20 | $20 | $50 | $100 | $200 | Plano grátis limitado |
| 30 | **PostgreSQL** | Database | Banco de dados principal | postgresql.org | - | - | ✅ Integrado | Incluído Replit | $0 | $0 | $0 | $0 | $0 | $50 | Incluído no Replit |
| 31 | **Redis** | Cache | Cache, sessões, rate limiting | redis.io / upstash.com | - | - | 📋 Planejado | Por uso | $0-30/mês | $0 | $0 | $7 | $15 | $30 | 10K cmd/dia grátis |
| 32 | **RabbitMQ** | Queue | Filas de mensagens, background jobs | cloudamqp.com | - | - | 📋 Planejado | Por plano | $0-99/mês | $0 | $0 | $19 | $49 | $99 | Little Lemur grátis |
| 33 | **GCP** | Cloud | Infra, storage, compute escalável | cloud.google.com | - | - | ⏸️ Opcional | Por uso | Pay-as-you-go | $0 | $0 | $25 | $50 | $300 | $300 créditos iniciais |
| 34 | **Azure** | Cloud | Alternativa GCP, MS integrations | azure.microsoft.com | - | - | ⏸️ Opcional | Por uso | Pay-as-you-go | $0 | $0 | $25 | $50 | $300 | $200 créditos iniciais |
| **DEVTOOLS** |
| 35 | **GitHub** | Repositório | Código fonte, CI/CD, Issues | github.com | - | - | ✅ Integrado | Gratuito | $0 | $0 | $0 | $0 | $0 | $0 | Repos ilimitados grátis |
| 36 | **Sentry** | Error Tracking | Monitoramento de erros, performance | sentry.io | - | - | 📋 Planejado | Por evento | $0-26/mês | $0 | $0 | $0 | $26 | $80 | 5K eventos/mês grátis |
| 37 | **PostHog** | Analytics | Product analytics, feature flags | posthog.com | - | - | ⏸️ Opcional | Por evento | $0-450/mês | $0 | $0 | $0 | $0 | $450 | 1M eventos/mês grátis |
| 38 | **Storybook** | Component Dev | Documentação de componentes UI | storybook.js.org | - | - | ✅ Integrado | Open Source | $0 | $0 | $0 | $0 | $0 | $0 | 100% grátis |
| 39 | **Figma** | Design | UI/UX design, protótipos | figma.com | - | - | ✅ Integrado | Por editor | $0-15/editor | $0 | $0 | $0 | $45 | $150 | 3 projetos grátis |
| 40 | **Notion** | Docs/KB | Documentação, knowledge base | notion.so | - | - | ✅ Integrado | Por membro | $0-10/membro | $0 | $0 | $0 | $0 | $100 | Free para times pequenos |
| 41 | **Jira** | Gestão | Gestão de projetos, sprints | atlassian.com/jira | - | - | ⏸️ Opcional | Por usuário | $0-8.15/user | $0 | $0 | $0 | $0 | $82 | Free até 10 users |
| 42 | **Linear** | Issue Tracking | Alternativa Jira, dev-first | linear.app | - | - | ⏸️ Opcional | Por usuário | $0-8/user | $0 | $0 | $0 | $0 | $80 | 250 issues grátis |
| **FERRAMENTAS FUTURAS/OPCIONAIS** |
| 43 | **Squadcast** | Alerting | Alertas e incidentes | squadcast.com | - | - | ⏸️ Opcional | Por usuário | $9-21/user | $0 | $0 | $0 | $45 | $225 | 5 users grátis |
| 44 | **New Relic** | APM | Application performance monitoring | newrelic.com | - | - | ⏸️ Opcional | Por uso | Usage-based | $0 | $0 | $0 | $0 | $100 | 100GB/mês grátis |
| 45 | **SignNow** | E-Signature | Assinatura eletrônica de contratos | signnow.com | - | - | ⏸️ Opcional | Por usuário | $8/user | $0 | $0 | $0 | $24 | $80 | Trial disponível |
| 46 | **DocuSign** | E-Signature | Assinatura digital enterprise | docusign.com | - | - | ⏸️ Opcional | Por usuário | $10+/user | $0 | $0 | $0 | $30 | $100 | Trial 30 dias |
| 47 | **Freshdesk** | Help Desk | Suporte ao cliente, tickets | freshdesk.com | - | - | ⏸️ Opcional | Por agente | $0-15/agent | $0 | $0 | $0 | $0 | $75 | 10 agents grátis |
| 48 | **Zendesk** | Help Desk | Suporte enterprise | zendesk.com | - | - | ⏸️ Opcional | Por agente | $19-149/agent | $0 | $0 | $0 | $57 | $285 | Trial 14 dias |
| 49 | **Slack** | Comunicação | Chat interno, integrações | slack.com | - | - | ⏸️ Opcional | Por usuário | $0-15/user | $0 | $0 | $0 | $0 | $150 | Free com 90 dias histórico |
| 50 | **Typeform** | Formulários | Pesquisas, NPS, feedback | typeform.com | - | - | ⏸️ Opcional | Por mês | $25-83/mês | $0 | $0 | $0 | $25 | $83 | 10 respostas/mês grátis |
| 51 | **Willo** | Video Interview | Entrevistas assíncronas em vídeo | willo.video | - | - | ⏸️ Opcional | Por candidato | ~$2/candidato | $0 | $0 | $20 | $40 | $200 | Trial disponível |
| 52 | **DataDog** | Monitoring | APM, logs, métricas (enterprise) | datadoghq.com | - | - | ⏸️ Opcional | Por host | $15+/host | $0 | $0 | $0 | $0 | $300 | Trial 14 dias |

### Resumo de Custos por Cenário

| Cenário | Custo Fixo/Mês | Custo Variável/Mês | Total/Mês | Por Cliente |
|---------|----------------|--------------------|-----------|-|
| **MVP (1 cliente)** | $30 | $10 | **$40** | $40 |
| **Startup (5 clientes)** | $265 | $680 | **$945** | $189 |
| **Growth (10 clientes)** | $400 | $1.360 | **$1.760** | $176 |
| **Scale (50 clientes)** | $1.159 | $6.250 | **$7.409** | $148 |

### Ferramentas com Free Tier Generoso (17 Total)

| Ferramenta | Limite Grátis | Suficiente Para |
|------------|---------------|-----------------|
| ProfitWell | Ilimitado | Sempre |
| HubSpot CRM | Ilimitado | Sempre |
| LangGraph/LangChain | Open Source | Sempre |
| LangSmith | 5K traces/mês | MVP |
| GitHub | Ilimitado | Sempre |
| Gemini | 1M tokens/mês | MVP |
| Deepgram | $200 créditos | 3-6 meses |
| Mailgun | 5.000/mês | MVP |
| WhatsApp | 1K msg/mês | MVP |
| MS Graph | Ilimitado | Sempre |
| Merge | 3 conexões | MVP |
| Redis (Upstash) | 10K cmd/dia | MVP |
| RabbitMQ | Little Lemur | MVP |
| Sentry | 5K eventos/mês | MVP |
| PostHog | 1M eventos/mês | Growth |
| Storybook | Open Source | Sempre |
| Figma | 3 projetos | MVP |

---

## MAPA DE INTEGRAÇÕES VISUAL COMPLETO

### Visão Geral do Ecossistema WeDo Talent

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                 │
│                                    🏢  WEDO TALENT - ECOSSISTEMA COMPLETO                                       │
│                                         35+ Integrações | 2 Capítulos                                           │
│                                                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│    ┌─────────────────────────────────────────────────┐    ┌─────────────────────────────────────────────────┐   │
│    │                                                 │    │                                                 │   │
│    │            WEDO TALENT ADMIN                    │    │          WEDO TALENT PLATAFORMA                 │   │
│    │          (Capítulo 1 - 7 SaaS)                  │    │        (Capítulo 2 - 25+ APIs)                  │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │         BILLING & MÉTRICAS          │     │    │    │           LLMs & IA                 │     │   │
│    │    │  ┌─────────┐      ┌──────────┐      │     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │  │ Stripe  │      │ProfitWell│      │     │    │    │  │ Claude  │      │ Gemini  │      │     │   │
│    │    │  │ Billing │      │ Metrics  │      │     │    │    │  │Anthropic│      │ Google  │      │     │   │
│    │    │  │  💳     │      │  📊     │      │     │    │    │  │  🧠     │      │  🔮     │      │     │   │
│    │    │  └─────────┘      └──────────┘      │     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │         CRM & ONBOARDING            │     │    │    │        ORQUESTRAÇÃO AGENTES         │     │   │
│    │    │          ┌──────────────┐           │     │    │    │  ┌─────────┐ ┌─────────┐ ┌────────┐│     │   │
│    │    │          │   HubSpot    │           │     │    │    │  │LangGraph│ │LangChain│ │LangSmith││     │   │
│    │    │          │CRM + Tickets │           │     │    │    │  │  Graph  │ │ Chains  │ │ Traces ││     │   │
│    │    │          │ + Workflows  │           │     │    │    │  │  🔄     │ │  ⛓️    │ │  🔍   ││     │   │
│    │    │          │  📇 🎯      │           │     │    │    │  └─────────┘ └─────────┘ └────────┘│     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │      AUTENTICAÇÃO ENTERPRISE        │     │    │    │          SOURCING & BUSCA           │     │   │
│    │    │             ┌──────────┐             │     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │             │  WorkOS  │             │     │    │    │  │ Pearch  │      │  Apify  │      │     │   │
│    │    │             │SSO/SCIM  │             │     │    │    │  │ 800M+   │      │LinkedIn │      │     │   │
│    │    │             │  🔐     │             │     │    │    │  │  🔎     │      │  🕷️    │      │     │   │
│    │    │             └──────────┘             │     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │      COMPLIANCE & GOVERNANÇA        │     │    │    │           VOZ & SPEECH              │     │   │
│    │    │  ┌─────────┐ ┌─────────┐ ┌────────┐│     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │  │ Vanta/  │ │Privacy  │ │ Warden ││     │    │    │  │Deepgram │      │ OpenMic │      │     │   │
│    │    │  │ Drata   │ │ Tools   │ │   AI   ││     │    │    │  │   STT   │      │  Voice  │      │     │   │
│    │    │  │  ✅    │ │  🇧🇷   │ │  🤖   ││     │    │    │  │  🎤     │      │  📞    │      │     │   │
│    │    │  └─────────┘ └─────────┘ └────────┘│     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ─────────────────────────────────────       │    │    ┌─────────────────────────────────────┐     │   │
│    │    🔧 70% SaaS  |  30% Interno (~9k linhas)    │    │    │          COMUNICAÇÃO                │     │   │
│    │    💰 R$ 107-195k/ano                          │    │    │  ┌────────┐ ┌────────┐ ┌─────────┐ │     │   │
│    │                                                 │    │    │  │MS Graph│ │WhatsApp│ │Mailgun │ │     │   │
│    └─────────────────────────────────────────────────┘    │    │  │Calendar│ │  API   │ │  Email  │ │     │   │
│                                                            │    │  │  📅    │ │  💬   │ │  ✉️    │ │     │   │
│                                                            │    │  └────────┘ └────────┘ └─────────┘ │     │   │
│                                                            │    └─────────────────────────────────────┘     │   │
│                                                            │                                                 │   │
│                                                            │    ┌─────────────────────────────────────┐     │   │
│                                                            │    │         INTEGRAÇÕES ATS             │     │   │
│                                                            │    │  ┌─────────┐ ┌────────┐ ┌─────────┐ │     │   │
│                                                            │    │  │Merge  │           │ │Gupy/    │ │     │   │
│                                                            │    │  │ Unified │ │  API   │ │Pandapé  │ │     │   │
│                                                            │    │  │  🔗    │ │  🔗   │ │  🇧🇷   │ │     │   │
│                                                            │    │  └─────────┘ └────────┘ └─────────┘ │     │   │
│                                                            │    └─────────────────────────────────────┘     │   │
│                                                            │                                                 │   │
│                                                            │    ─────────────────────────────────────       │   │
│                                                            │    🔧 30% SaaS  |  70% Interno (~25k linhas)   │   │
│                                                            │    💰 $2.700-12.750/mês                        │   │
│                                                            │                                                 │   │
│                                                            └─────────────────────────────────────────────────┘   │
│                                                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│                                        INFRAESTRUTURA COMPARTILHADA                                             │
│                                                                                                                 │
│    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│    │    Replit     │  │  PostgreSQL   │  │    Redis      │  │   RabbitMQ    │  │  GCP/Azure    │              │
│    │   Hosting     │  │   Database    │  │    Cache      │  │    Queue      │  │    Cloud      │              │
│    │     ☁️        │  │     🗄️       │  │     ⚡       │  │     📨       │  │     🌐       │              │
│    └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘              │
│                                                                                                                 │
│                                         💰 Custo Fixo: ~$1.329/mês                                             │
│                                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Mapa de Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FLUXO DE INTEGRAÇÕES                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│   ADMIN (Gestão)                        PLATAFORMA (Core)                        INFRAESTRUTURA     │
│   ──────────────                        ────────────────                         ───────────────     │
│                                                                                                      │
│   ┌──────────┐                                                                                      │
│   │  Stripe  │ ─────────────────────────────────────────────────────────────────┐                   │
│   │ Billing  │                                                                   │                   │
│   └──────────┘                                                                   │                   │
│        │                                                                         │                   │
│        ▼                                                                         ▼                   │
│   ┌──────────┐        ┌───────────────────────────────────────────────┐    ┌──────────┐             │
│   │ProfitWell│        │                                               │    │PostgreSQL│             │
│   │ Metrics  │        │         📋 FUNIL DE VAGAS                     │    │ Database │             │
│   └──────────┘        │                                               │    └──────────┘             │
│        │              │  Wizard ──► Claude ──► JD ──► Publicar        │         │                   │
│        ▼              │    │         │         │          │           │         │                   │
│   ┌──────────┐        │    └────► LangGraph ◄──┘          │           │         ▼                   │
│   │ HubSpot  │        │              │                     │           │    ┌──────────┐             │
│   │   CRM    │ ◄──────┼──────────────┘                     │           │    │  Redis   │             │
│   └──────────┘        │                                    │           │    │  Cache   │             │
│        │              └────────────────────────────────────│───────────┘    └──────────┘             │
│        ▼                                                   │                     │                   │
│   ┌──────────┐        ┌───────────────────────────────────▼───────────┐         │                   │
│   │  HubSpot │        │                                               │         │                   │
│   │ Tickets  │        │         👥 FUNIL DE TALENTOS                  │         ▼                   │
│   └──────────┘        │                                               │    ┌──────────┐             │
│        │              │  Pearch ──► Triagem ──► Entrevista ──► Hire   │    │ RabbitMQ │             │
│        │              │    │          │            │           │      │    │  Queue   │             │
│        │              │    │      ┌───┴───┐    ┌───┴───┐       │      │    └──────────┘             │
│        │              │    │      │Claude │    │OpenMic│       │      │         │                   │
│        │              │    │      │Scoring│    │Deepgrm│       │      │         │                   │
│        │              │    │      └───────┘    └───────┘       │      │         ▼                   │
│        │              │    │                                   │      │    ┌──────────┐             │
│        │              │    ▼                                   ▼      │    │  Replit  │             │
│        │              │  ┌─────────────────────────────────────────┐  │    │ Hosting  │             │
│        │              │  │         COMUNICAÇÃO                     │  │    └──────────┘             │
│        │              │  │  MS Graph │ WhatsApp │ Mailgun         │  │                              │
│        │              │  └─────────────────────────────────────────┘  │                              │
│        │              │                    │                          │                              │
│        │              │                    ▼                          │                              │
│        │              │  ┌─────────────────────────────────────────┐  │                              │
│        │              │  │         INTEGRAÇÕES ATS                 │  │                              │
│        │              │  │  Merge │ Gupy │ Pandapé              │  │                              │
│        │              │  └─────────────────────────────────────────┘  │                              │
│        │              │                                               │                              │
│        │              └───────────────────────────────────────────────┘                              │
│        │                                     │                                                       │
│        ▼                                     ▼                                                       │
│   ┌──────────┐        ┌───────────────────────────────────────────────┐                             │
│   │  WorkOS  │ ◄──────┤         ⚙️ MENU CONFIGURAÇÕES                 │                             │
│   │ SSO/SCIM │        │                                               │                             │
│   └──────────┘        │  SSO Setup │ Templates │ Conexões ATS         │                             │
│        │              └───────────────────────────────────────────────┘                             │
│        ▼                                                                                             │
│   ┌──────────────────────────────────────────────────────────────┐                                  │
│   │                    COMPLIANCE & GOVERNANÇA                    │                                  │
│   │  Vanta/Drata (SOC 2) │ Privacy Tools (LGPD) │ Warden AI (Bias)│                                  │
│   └──────────────────────────────────────────────────────────────┘                                  │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tabela Resumo por Capítulo

| Área | Capítulo | Integrações | Custo Mensal | Filosofia |
|------|----------|-------------|--------------|-----------|
| **Admin** | 1 | Stripe, ProfitWell, HubSpot (CRM + Onboarding), WorkOS, Vanta/Drata, Privacy Tools, Warden AI | R$ 9.000-16.000 | 70% SaaS + 30% Interno |
| **Plataforma - Vagas** | 2 | Claude, Gemini, LangGraph, LangChain, Mailgun, Merge, RabbitMQ | $800-3.000 | 30% SaaS + 70% Interno |
| **Plataforma - Talentos** | 2 | Claude, Pearch, Apify, OpenMic, Deepgram, MS Graph, WhatsApp, Merge | $1.500-8.000 | 30% SaaS + 70% Interno |
| **Plataforma - Config** | 2 | WorkOS, Mailgun, WhatsApp, MS Graph, Merge | $300-1.500 | 30% SaaS + 70% Interno |
| **Infraestrutura** | Compartilhado | Replit, PostgreSQL, Redis, RabbitMQ, GCP/Azure | $1.329 (fixo) | 100% Cloud |

---

### Contagem Total de Integrações

| Categoria | Quantidade | Lista |
|-----------|------------|-------|
| **LLMs** | 2 | Claude, Gemini |
| **Orquestração** | 3 | LangGraph, LangChain, LangSmith |
| **Sourcing** | 2 | Pearch AI, Apify |
| **Voz/STT** | 2 | Deepgram, OpenMic |
| **Comunicação** | 3 | MS Graph, WhatsApp, Mailgun |
| **ATS/HRIS** | 4 | Merge, Gupy, Pandapé |
| **Identity** | 1 | WorkOS |
| **Billing** | 2 | Stripe, ProfitWell |
| **CRM/Onboarding** | 1 | HubSpot (CRM + Tickets + Workflows) |
| **Compliance** | 3 | Vanta/Drata, Privacy Tools, Warden AI |
| **Infraestrutura** | 5 | Replit, PostgreSQL, Redis, RabbitMQ, GCP/Azure |
| **DevTools** | 4 | Figma, Jira, Notion, GitHub |
| **TOTAL** | **33+** | |

---

### Custos Consolidados

| Área | Custo MÍNIMO | Custo Recomendado | Custo Scale |
|------|--------------|-------------------|-------------|
| **Plataforma (APIs + Infra)** | **$30/mês** | $673/mês (3 clientes) | $21.800/mês (30 clientes) |
| **Admin (SaaS)** | **$0** (sem Vanta) | R$ 3.000/mês | R$ 16.000/mês |
| **Desenvolvimento Interno** | - | - | R$ 284k (único) |
| **TOTAL MÍNIMO** | **~R$ 150/mês** | **~R$ 6.500/mês** | **~R$ 130k/mês** |

> **Base de Cálculo:** Mínimo = free tiers + 1 cliente pequeno. Usar planos pagos conforme escalar.

---

### Tabela Completa de Custos por Ferramenta

> **Legenda:** MVP = 1 cliente mínimo | Custo anual = (variável × clientes × 12) + (fixo × 12)

#### Capítulo 1: WeDo Talent Admin (7 ferramentas)

| # | Ferramenta | Categoria | MVP (1 cli) | Tipo | 10 cli/ano | 50 cli/ano | 100 cli/ano |
|---|------------|-----------|-------------|------|------------|------------|-------------|
| 1 | **Stripe** | Billing | $0 | % transação | 2.9% + $0.30 | 2.9% + $0.30 | 2.9% + $0.30 |
| 2 | **ProfitWell** | Métricas | $0 | Grátis | $0 | $0 | $0 |
| 3 | **HubSpot** | CRM | $0 | Free tier | $0 | $5.400 | $14.400 |
| 4 | **HubSpot Onboarding** | Onboarding (Tickets) | $0 | Grátis (nativo) | $0 | $0 | $0 |
| 5 | **WorkOS** | SSO/SCIM | $0 | Por conexão | $6.000 | $30.000 | $60.000 |
| 6 | **Vanta** | Compliance | $0 | Opcional | $12.000 | $18.000 | $24.000 |
| 7 | **Privacy Tools** | LGPD | $0 | Opcional | $3.600 | $4.800 | $7.200 |
| 8 | **Warden AI** | AI Bias | $0 | Fase 2 | TBD | TBD | TBD |
| | **SUBTOTAL ADMIN** | | **$0** | | **$25.200** | **$64.200** | **$114.600** |

> **Nota Admin:** Ferramentas opcionais no MVP. Ativar conforme demanda de clientes enterprise.

#### Capítulo 2: WeDo Talent Plataforma (25+ ferramentas)

| # | Ferramenta | Categoria | MVP (1 cli) | Tipo Custo | 10 cli/ano | 50 cli/ano | 100 cli/ano |
|---|------------|-----------|-------------|------------|------------|------------|-------------|
| **LLMs & IA** |||||||||
| 1 | **Claude (Anthropic)** | LLM | $10 | Por token | $3.000 | $27.000 | $60.000 |
| 2 | **Gemini (Google)** | LLM | $0 | Free tier | $60 | $300 | $600 |
| **Orquestração** |||||||||
| 3 | **LangGraph** | Orquestração | $0 | Open source | $0 | $0 | $0 |
| 4 | **LangChain** | Framework | $0 | Open source | $0 | $0 | $0 |
| 5 | **LangSmith** | Observability | $0 | Free 5k/mês | $0 | $2.340 | $4.680 |
| **Sourcing** |||||||||
| 6 | **Pearch AI** | Candidatos | $0 | Opcional | $6.000 | $120.000 | $300.000 |
| 7 | **Apify** | Scraping | $0 | Free tier | $60 | $1.200 | $4.800 |
| **Voz & STT** |||||||||
| 8 | **Deepgram** | STT | $0 | $200 grátis | $60 | $1.200 | $5.400 |
| 9 | **OpenMic** | Voice Screen | $0 | Opcional | $6.000 | $60.000 | $120.000 |
| **Comunicação** |||||||||
| 10 | **MS Graph** | Calendar | $0 | Grátis | $0 | $0 | $0 |
| 11 | **WhatsApp API** | Mensagens | $0 | 1k grátis | $600 | $12.000 | $30.000 |
| 12 | **Mailgun** | Email | $0 | Free 5.000/mês | $600 | $6.000 | $12.000 |
| **ATS/HRIS** |||||||||
| 13 | **Merge** | Unified API | $0 | Opcional | $6.000 | $18.000 | $24.000 |
| 14 | **Merge** | Unified API | $0 | 3 grátis | $0 | $7.800 | $15.600 |
| **Infraestrutura (Fixo)** |||||||||
| 15 | **Replit** | Hosting | $20 | Fixo | $240 | $1.200 | $2.400 |
| 16 | **PostgreSQL** | Database | $0 | Incluso Replit | $0 | $0 | $600 |
| 17 | **Redis** | Cache | $0 | Free tier | $0 | $84 | $360 |
| 18 | **RabbitMQ** | Queue | $0 | Free tier | $0 | $228 | $588 |
| 19 | **GCP/Azure** | Cloud | $0 | Free tier | $0 | $600 | $3.600 |
| **DevTools (Time Interno)** |||||||||
| 20 | **Figma** | Design | $0 | Starter grátis | $0 | $600 | $2.400 |
| 21 | **Jira** | Gestão | $0 | Free 10 users | $0 | $0 | $600 |
| 22 | **GitHub** | DevOps | $0 | Free | $0 | $0 | $600 |
| 23 | **Notion** | Docs | $0 | Free | $0 | $0 | $360 |
| | **SUBTOTAL PLATAFORMA** | | **$30** | | **$22.620** | **$258.552** | **$588.588** |

#### Resumo Geral Consolidado

| Cenário | Clientes | Custo Mensal | Custo Anual | Por Cliente/Mês |
|---------|----------|--------------|-------------|-----------------|
| **MVP/Bootstrap** | 1 | **$30** | **$360** | $30 |
| **Startup** | 10 | $3.985 | **$47.820** | $399 |
| **Growth** | 50 | $26.896 | **$322.752** | $538 |
| **Scale** | 100 | $58.599 | **$703.188** | $586 |

#### Ferramentas com Free Tier (Custo $0 no MVP)

| Ferramenta | Free Tier | Limite |
|------------|-----------|--------|
| ProfitWell | Ilimitado | Sempre grátis |
| Gemini | Generoso | Uso leve coberto |
| LangGraph/LangChain | Open source | Sempre grátis |
| LangSmith | Developer | 5.000 traces/mês |
| Deepgram | Créditos | $200 para novos usuários |
| MS Graph | Total | 100% grátis |
| WhatsApp | Conversas | 1.000/mês grátis |
| Mailgun | Emails | 5.000/mês grátis |
| Merge | Conexões | 3 conexões grátis |
| Redis (Upstash) | Requests | 10k/dia grátis |
| RabbitMQ (CloudAMQP) | Little Lemur | Compartilhado grátis |
| Figma | Starter | 3 projetos grátis |
| Jira | Free | Até 10 usuários |
| GitHub | Free | Repos ilimitados |
| Notion | Free | Times pequenos |

---

## Sumário Geral

### Capítulo 1: WeDo Talent Admin
- 1.1 [Visão Geral e Stack Final](#11-visão-geral-e-stack-final)
- 1.2 [Guia Stripe Billing](#12-guia-stripe-billing)
- 1.3 [Guia ProfitWell](#13-guia-profitwell)
- 1.4 [Guia HubSpot CRM](#14-guia-hubspot-crm)
- 1.5 [Guia HubSpot Onboarding (Tickets + Workflows)](#15-guia-hubspot-onboarding-tickets--workflows)
- 1.6 [Guia WorkOS SSO/SCIM](#16-guia-workos-ssoscim)
  - 1.6.1 [Visão Geral](#161-visão-geral)
  - 1.6.2 [Arquitetura do Sistema](#162-arquitetura-do-sistema)
  - 1.6.4 [Checklist de Configuração](#164-checklist-de-configuração)
  - 1.6.5 [Jornada de Onboarding](#165-jornada-de-onboarding---mapeamento-completo)
  - 1.6.6 [Fluxos Técnicos Detalhados](#166-fluxos-técnicos-detalhados)
  - 1.6.7 [Configuração SSO/SCIM no IdP do Cliente](#167-configuração-ssoscim-no-idp-do-cliente)
  - 1.6.12 [Modelos de Dados e Endpoints](#1612-modelos-de-dados-e-endpoints)
  - 1.6.14 [Resolução de Problemas](#1614-resolução-de-problemas)
  - 1.6.15 [Compliance e Segurança](#1615-compliance-e-segurança)
  - 1.6.19 [Glossário](#1619-glossário)
- 1.7 [Guia Vanta/Drata Compliance](#17-guia-vantadrata-compliance)
- 1.8 [Guia Privacy Tools LGPD](#18-guia-privacy-tools-lgpd)
- 1.9 [Guia Warden AI](#19-guia-warden-ai)
- 1.10 [O Que Desenvolver Internamente](#110-o-que-desenvolver-internamente)

### Capítulo 2: WeDo Talent Plataforma
- 2.1 [Visão Geral das Integrações](#21-visão-geral-das-integrações)
- 2.2 [LLMs e Inteligência Artificial](#22-llms-e-inteligência-artificial)
- 2.3 [Orquestração e Observabilidade de Agentes](#23-orquestração-e-observabilidade-de-agentes)
- 2.4 [Banco de Candidatos e Sourcing](#24-banco-de-candidatos-e-sourcing)
- 2.5 [Speech-to-Text e Voz](#25-speech-to-text-e-voz)
- 2.6 [Comunicação e Agendamento](#26-comunicação-e-agendamento)
- 2.7 [Integrações ATS/HRIS (Unified APIs)](#27-integrações-atshris-unified-apis)
- 2.8 [Autenticação e Identity](#28-autenticação-e-identity)
- 2.9 [Infraestrutura Cloud](#29-infraestrutura-cloud)
- 2.10 [Message Queue e Event-Driven](#210-message-queue-e-event-driven)
- 2.11 [Design e Prototipação](#211-design-e-prototipação)
- 2.12 [Gestão de Projetos e Colaboração](#212-gestão-de-projetos-e-colaboração)
- 2.13 [Controle de Versão e DevOps](#213-controle-de-versão-e-devops)
- 2.14 [Documentação e Knowledge Base](#214-documentação-e-knowledge-base)
- 2.15 [Resumo de Custos por Cliente](#215-resumo-de-custos-por-cliente)
- 2.16 [Análise de Viabilidade](#216-análise-de-viabilidade)
- 2.17 [Recomendações Estratégicas](#217-recomendações-estratégicas)

### Apêndices
- A. [Tabela Consolidada de APIs (35+)](#apêndice-a-tabela-consolidada-de-apis)
- B. [Contatos Comerciais](#apêndice-b-contatos-comerciais)
- C. [Análise de Subprocessadores dos Concorrentes](#apêndice-c-análise-de-subprocessadores)
- D. [Checklist de Setup](#apêndice-d-checklist-de-setup)
- E. [Glossário](#apêndice-e-glossário)

---

# CAPÍTULO 1: WEDO TALENT ADMIN

> **Escopo:** Gestão de clientes, billing, onboarding, SSO/SCIM, compliance  
> **Filosofia:** 70% SaaS + 30% Desenvolvimento Interno  
> **Documento Detalhado:** [analise-viabilidade-saas-stack.md](./analise-viabilidade-saas-stack.md)

> **NOTA ARQUITETURAL:** A plataforma WeDo Talent **não possui área admin frontend**. Toda a gestão do Admin Layer é feita via ferramentas SaaS externas:
> - **HubSpot CRM**: Gestão de clientes e contatos
> - **HubSpot Tickets + Workflows**: Onboarding de clientes
> - **WorkOS Dashboard**: Configuração SSO/SCIM
> - **Stripe Dashboard**: Billing, assinaturas, Customer Portal
> - **ProfitWell**: Métricas SaaS (MRR, Churn, LTV)
> - **Backend Rails**: APIs (`/api/v1/*`) para integrações e webhooks

---

## 1.1 Visão Geral e Stack Final

### Stack Aprovada para Admin

| Categoria | Ferramenta | Função | Custo/ano |
|-----------|------------|--------|-----------|
| **Pagamentos** | Stripe | Billing, subscriptions | 2.9% + taxas |
| **Métricas SaaS** | ProfitWell | MRR, Churn, LTV, ARR | **Grátis** |
| **CRM + Clientes** | HubSpot | CRUD clientes, dashboard | (já integrado) |
| **Onboarding** | HubSpot Tickets + Workflows | Pipeline nativo, automações | **$0 (grátis)** |
| **SSO/SCIM/MFA** | WorkOS | Autenticação enterprise | ~R$ 7-30k |
| **Compliance Global** | Vanta ou Drata | SOC 2, ISO 27001 | ~R$ 35-60k |
| **LGPD Brasil** | Privacy Tools | Portal titular, RIPD | ~R$ 15-30k |
| **AI Bias Audit** | Warden AI | Auditoria LIA screening | A definir |
| **Total Estimado** | | | **R$ 87-195k/ano** |

### Arquitetura Admin

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ADMIN LAYER (70% SaaS)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Stripe    │  │  ProfitWell  │  │        HubSpot (CRM + Onboarding)       │    │
│  │   Customer   │  │              │  │                                         │    │
│  │    Portal    │  │  Dashboards  │  │  Companies │ Tickets │ Workflows        │    │
│  │              │  │  Métricas    │  │  Contacts  │ Pipeline│ Automações       │    │
│  │ • Faturas    │  │  MRR/Churn   │  │  Deals     │ Stages  │                  │    │
│  │ • Planos     │  │              │  │            │         │                  │    │
│  │ • Pagamentos │  │  (FREE)      │  │            │ (FREE)  │                  │    │
│  └──────────────┘  └──────────────┘  └─────────────────────────────────────────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴────────┬────────┴─────────────────┘             │
│                                    │                                         │
│  ┌──────────────┐  ┌──────────────┐│ ┌──────────────┐  ┌──────────────┐    │
│  │    WorkOS    │  │ Vanta/Drata  ││ │Privacy Tools │  │  Warden AI   │    │
│  │              │  │              ││ │              │  │              │    │
│  │  SSO/SCIM    │  │  SOC 2       ││ │  LGPD        │  │  AI Bias     │    │
│  │  MFA         │  │  ISO 27001   ││ │  Portal      │  │  Audit       │    │
│  │  Audit Logs  │  │  Controls    ││ │  RIPD        │  │              │    │
│  └──────────────┘  └──────────────┘│ └──────────────┘  └──────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│                    ┌────────────────────────────┐                           │
│                    │   WeDo Talent Backend      │                           │
│                    │   (Rails + PostgreSQL)     │                           │
│                    │                            │                           │
│                    │ • Webhooks (Stripe, WorkOS)│                           │
│                    │ • API REST /api/v1/admin/  │                           │
│                    │ • Multi-tenant isolation   │                           │
│                    └────────────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O Que Será Desenvolvido Internamente (30%)

| Componente | Linhas | Prazo | Observação |
|------------|--------|-------|------------|
| ~~Portal LGPD Público~~ | ~~2.500~~ | ~~2 semanas~~ | ❌ **Substituído por Privacy Tools** |
| ~~Trust Center Público~~ | ~~2.000~~ | ~~1 semana~~ | ❌ **Substituído por Notion** |
| Integração Privacy Tools | ~500 | 3 dias | Webhook, SSO, theming |
| APIs Backend Admin | ~4.500 | Contínuo | |
| **TOTAL** | **~5.000** | | **Economia: 4.500 linhas** |

> **Decisão:** Privacy Tools já inclui Portal do Titular LGPD. Não há necessidade de desenvolver internamente.
> 
> **Decisão:** Trust Center será mantido no Notion e integrado via embed no website. Economia de ~2.000 linhas.

> **Referência Completa:** [analise-viabilidade-saas-stack.md](./analise-viabilidade-saas-stack.md)

---

## 1.2 Guia Stripe Billing

### Visão Geral

Stripe é a plataforma de pagamentos que gerencia todo o ciclo de vida de billing:
- Subscriptions (planos mensais/anuais)
- Invoices (faturas automáticas)
- Customer Portal (self-service)
- Webhooks (eventos em tempo real)

### Configuração

```bash
# Secrets necessários
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### Produtos e Preços Sugeridos

| Plano | Preço/mês | Usuários | Vagas |
|-------|-----------|----------|-------|
| Starter | R$ 990 | 3 | 5 |
| Professional | R$ 2.490 | 10 | 20 |
| Enterprise | Customizado | Ilimitado | Ilimitado |

### Customer Portal

O Stripe Customer Portal elimina a necessidade de desenvolver:
- ❌ Tela de faturas
- ❌ Troca de plano
- ❌ Atualização de cartão
- ❌ Cancelamento

**Economia:** ~3.000 linhas de código

### Webhooks a Configurar

| Evento | Ação |
|--------|------|
| `customer.subscription.created` | Ativar cliente |
| `customer.subscription.updated` | Atualizar plano |
| `customer.subscription.deleted` | Suspender acesso |
| `invoice.paid` | Registrar pagamento |
| `invoice.payment_failed` | Iniciar dunning |

---

## 1.3 Guia ProfitWell

### Visão Geral

ProfitWell (agora Paddle) oferece métricas SaaS **gratuitas**:
- MRR (Monthly Recurring Revenue)
- Churn Rate
- LTV (Lifetime Value)
- ARR, NRR, ARPU

### Configuração

1. Criar conta em profitwell.com
2. Conectar ao Stripe (1-click)
3. Aguardar 24h para métricas

**Custo:** $0 (grátis para sempre)

### Métricas Disponíveis

| Métrica | Descrição |
|---------|-----------|
| **MRR** | Receita recorrente mensal |
| **Net MRR** | MRR novo - churned - contraction + expansion |
| **Churn Rate** | % de clientes que cancelaram |
| **LTV** | Valor esperado do cliente |
| **ARPU** | Receita média por usuário |

---

## 1.4 Guia HubSpot CRM

### Visão Geral

HubSpot é o **CRM central** que gerencia todo o ciclo de vida do cliente WeDo Talent:
- Companies (empresas clientes)
- Contacts (usuários/admins)
- Deals (contratos e renovações)
- Custom Objects (Subscriptions, Licenses)

### Pré-requisitos

| Item | Requisito | Notas |
|------|-----------|-------|
| Plano HubSpot | Free CRM (mínimo) | Custom Objects requer Enterprise |
| Stripe | Conta ativa | Para billing |
| WorkOS | Conta configurada | Para SSO/SCIM |
| HubSpot Onboarding | Pipeline configurado | Pipeline "Onboarding Cliente" + Workflows |
| ProfitWell | Conectado ao Stripe | Para métricas |

---

### FASE 1: Configuração Inicial do HubSpot (Dia 1)

#### Passo 1.1: Criar Conta e Private App

```bash
# 1. Criar conta em app.hubspot.com (grátis)
# 2. Acessar Settings > Integrations > Private Apps
# 3. Create Private App com nome "WeDo Talent Backend"
# 4. Escopos necessários:
```

**Escopos da Private App:**

| Escopo | Permissão | Uso |
|--------|-----------|-----|
| `crm.objects.companies.read` | Read | Consultar clientes |
| `crm.objects.companies.write` | Write | Criar/atualizar clientes |
| `crm.objects.contacts.read` | Read | Consultar usuários |
| `crm.objects.contacts.write` | Write | Criar/atualizar usuários |
| `crm.objects.deals.read` | Read | Consultar contratos |
| `crm.objects.deals.write` | Write | Criar/atualizar contratos |
| `crm.schemas.custom.read` | Read | Custom Objects |
| `crm.objects.custom.read` | Read | Custom Objects |
| `crm.objects.custom.write` | Write | Custom Objects |

```bash
# Salvar token gerado como secret:
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx
```

#### Passo 1.2: Criar Propriedades Customizadas em Companies

Acessar **Settings > Data Management > Properties > Companies**:

| Propriedade | Nome Interno | Tipo | Opções | Grupo |
|-------------|--------------|------|--------|-------|
| WeDo Client ID | `wedo_client_id` | Single-line text | - | WeDo Talent |
| Plano WeDo | `wedo_plan` | Dropdown | Starter, Professional, Enterprise | WeDo Talent |
| Status WeDo | `wedo_status` | Dropdown | trial, active, suspended, cancelled | WeDo Talent |
| MRR | `wedo_mrr` | Number | Currency BRL | WeDo Talent |
| Limite de Usuários | `wedo_user_limit` | Number | - | WeDo Talent |
| Usuários Ativos | `wedo_users_count` | Number | - | WeDo Talent |
| SSO Habilitado | `wedo_sso_enabled` | Single checkbox | - | WeDo Talent |
| WorkOS Org ID | `wedo_workos_org_id` | Single-line text | - | WeDo Talent |
| Stripe Customer ID | `wedo_stripe_customer_id` | Single-line text | - | WeDo Talent |
| Data Onboarding | `wedo_onboarding_started` | Date picker | - | WeDo Talent |
| Onboarding Completo | `wedo_onboarding_completed` | Single checkbox | - | WeDo Talent |

#### Passo 1.3: Criar Propriedades Customizadas em Contacts

Acessar **Settings > Data Management > Properties > Contacts**:

| Propriedade | Nome Interno | Tipo | Opções |
|-------------|--------------|------|--------|
| Papel WeDo | `wedo_role` | Dropdown | admin, recruiter, manager, viewer |
| Client ID | `wedo_client_id` | Single-line text | - |
| Último Login | `wedo_last_login` | Date picker | - |
| Provisionado via SCIM | `wedo_scim_provisioned` | Single checkbox | - |

#### Passo 1.4: Criar Pipeline de Deals (Contratos)

Acessar **Settings > Objects > Deals > Pipelines**:

**Pipeline: "WeDo Talent Contracts"**

| Stage | Probabilidade | Ações Automáticas |
|-------|---------------|-------------------|
| 1. Proposta Enviada | 20% | - |
| 2. Proposta Aceita | 40% | - |
| 3. Contrato Assinado | 60% | Criar cliente no Stripe |
| 4. Pagamento Recebido | 80% | Ativar conta |
| 5. **Cliente Ativo** | 100% | Disparar Ticket de Onboarding (workflow) |
| 6. Renovação | 100% | - |
| Perdido | 0% | - |

#### Passo 1.5: Criar Pipeline de Onboarding (Service Hub)

Acessar **Settings > Objects > Services**:

**Pipeline: "Customer Onboarding"**

| Stage | Descrição |
|-------|-----------|
| 1. Aguardando Kickoff | Cliente pagou, aguardando reunião |
| 2. Kickoff Realizado | Reunião inicial feita |
| 3. Configuração SSO | Configurando WorkOS |
| 4. Importação Dados | Importando candidatos/vagas |
| 5. Treinamento | Sessões de capacitação |
| 6. Go-Live | Em produção |
| 7. **Onboarding Completo** | Sucesso! |

---

### FASE 2: Integração HubSpot ↔ Stripe via Rails (Dia 2-3)

> ⚠️ **IMPORTANTE: Limitação Geográfica**  
> O **Commerce Hub nativo do HubSpot** (integração direta HubSpot-Stripe) **NÃO está disponível no Brasil**.  
> A solução adotada é usar o **backend Rails como middleware**: Stripe Webhooks → Rails (StripeSyncService) → HubSpot API.

#### Passo 2.1: Criar Produtos no Stripe

Acessar **Stripe Dashboard > Products**:

| Produto | Preço | Tipo | Stripe Price ID |
|---------|-------|------|-----------------|
| WeDo Starter | R$ 990/mês | Recurring | price_xxx |
| WeDo Professional | R$ 2.490/mês | Recurring | price_xxx |
| WeDo Enterprise | Customizado | Quote-based | - |
| Setup Fee | R$ 5.000 | One-time | price_xxx |

#### Passo 2.2: Configurar Webhooks Stripe → Rails

1. Acessar **Stripe Dashboard > Developers > Webhooks**
2. Criar endpoint: `https://api.wedotalent.com/api/v1/webhooks/stripe`
3. Selecionar eventos a monitorar (ver tabela abaixo)
4. Salvar **Webhook Signing Secret** em `STRIPE_WEBHOOK_SECRET`

#### Passo 2.3: Implementar StripeSyncService no Rails

O Rails atua como middleware entre Stripe e HubSpot, processando os webhooks e atualizando o CRM.

**Arquitetura do Fluxo:**
```
┌─────────┐     Webhook      ┌─────────────┐    HubSpot API    ┌─────────┐
│  Stripe │ ───────────────► │    Rails    │ ────────────────► │ HubSpot │
│         │                  │ StripeSyncS │                   │   CRM   │
└─────────┘                  └─────────────┘                   └─────────┘
```

**Mapeamento de Eventos (via Rails):**

| Evento Stripe | Método StripeSyncService | Ação no HubSpot |
|---------------|--------------------------|-----------------|
| `customer.subscription.created` | `sync_subscription_created` | Atualizar Company: status=active |
| `customer.subscription.updated` | `sync_subscription_updated` | Atualizar Company: plan, mrr |
| `customer.subscription.deleted` | `sync_subscription_deleted` | Atualizar Company: status=cancelled |
| `invoice.paid` | `sync_invoice_paid` | Criar atividade "Pagamento recebido" |
| `invoice.payment_failed` | `sync_invoice_failed` | Criar tarefa "Cobrar cliente" |

```ruby
# wedotalent-backend/app/services/stripe_sync_service.rb
class StripeSyncService
  def initialize(hubspot_service = HubspotService.new)
    @hubspot = hubspot_service
  end

  def process_webhook(event)
    case event.type
    when 'customer.subscription.created'
      sync_subscription_created(event.data.object)
    when 'customer.subscription.updated'
      sync_subscription_updated(event.data.object)
    when 'customer.subscription.deleted'
      sync_subscription_deleted(event.data.object)
    when 'invoice.paid'
      sync_invoice_paid(event.data.object)
    when 'invoice.payment_failed'
      sync_invoice_failed(event.data.object)
    end
  end

  private

  def sync_subscription_created(subscription)
    customer_id = subscription.customer
    company = @hubspot.find_company_by_stripe_id(customer_id)
    return unless company

    mrr = subscription.items.data.first.price.unit_amount / 100
    @hubspot.update_company(company.id, {
      wedo_status: 'active',
      wedo_mrr: mrr,
      wedo_plan: subscription.items.data.first.price.nickname
    })
  end

  def sync_invoice_paid(invoice)
    customer_id = invoice.customer
    company = @hubspot.find_company_by_stripe_id(customer_id)
    return unless company

    @hubspot.create_activity(company.id, {
      type: 'payment_received',
      amount: invoice.amount_paid / 100,
      invoice_id: invoice.id
    })
  end

  def sync_subscription_updated(subscription)
    customer_id = subscription.customer
    company = @hubspot.find_company_by_stripe_id(customer_id)
    return unless company

    mrr = subscription.items.data.first.price.unit_amount / 100
    @hubspot.update_company(company.id, {
      wedo_mrr: mrr,
      wedo_plan: subscription.items.data.first.price.nickname,
      wedo_billing_interval: subscription.items.data.first.price.recurring&.interval
    })
  end

  def sync_subscription_deleted(subscription)
    customer_id = subscription.customer
    company = @hubspot.find_company_by_stripe_id(customer_id)
    return unless company

    @hubspot.update_company(company.id, {
      wedo_status: 'cancelled',
      wedo_cancelled_at: Time.current.iso8601,
      wedo_mrr: 0
    })

    @hubspot.create_activity(company.id, {
      type: 'subscription_cancelled',
      subscription_id: subscription.id,
      cancelled_at: Time.current.iso8601
    })
  end

  def sync_invoice_failed(invoice)
    customer_id = invoice.customer
    company = @hubspot.find_company_by_stripe_id(customer_id)
    return unless company

    @hubspot.create_task(company.id, {
      subject: "Cobrar cliente - Pagamento falhou",
      body: "Invoice #{invoice.id} falhou. Valor: #{invoice.amount_due / 100} #{invoice.currency.upcase}",
      due_date: (Time.current + 3.days).iso8601,
      priority: 'high'
    })

    @hubspot.create_activity(company.id, {
      type: 'payment_failed',
      amount: invoice.amount_due / 100,
      invoice_id: invoice.id,
      failure_reason: invoice.last_finalization_error&.message
    })
  end
end
```

```ruby
# wedotalent-backend/app/controllers/api/v1/webhooks_controller.rb
class Api::V1::WebhooksController < ApplicationController
  skip_before_action :verify_authenticity_token

  def stripe
    payload = request.body.read
    sig_header = request.headers['Stripe-Signature']
    
    begin
      event = Stripe::Webhook.construct_event(
        payload, sig_header, ENV['STRIPE_WEBHOOK_SECRET']
      )
    rescue Stripe::SignatureVerificationError => e
      render json: { error: 'Invalid signature' }, status: :bad_request
      return
    end

    StripeSyncService.new.process_webhook(event)
    render json: { received: true }
  end
end
```

---

### FASE 3: Integração HubSpot ↔ ProfitWell (Dia 3)

#### Passo 3.1: Conectar ProfitWell

1. Acessar **profitwell.com** e criar conta
2. Ir em **Account Settings > Integrations**
3. Clicar no card **HubSpot > Get Started**
4. Autorizar acesso ao HubSpot
5. Aguardar sync (email de confirmação)

**Custo:** $0 (grátis)

#### Passo 3.2: Configurar Sync de Dados

Em ProfitWell **Integrations > HubSpot > Configure**:

| Campo ProfitWell | Propriedade HubSpot | Objeto |
|------------------|---------------------|--------|
| MRR | `wedo_mrr` | Company |
| Plan Tier | `wedo_plan` | Company |
| Status | `wedo_status` | Company |
| Customer Since | `createdate` | Company |

#### Passo 3.3: Usar Métricas em Dashboards

Dados disponíveis após sync:
- MRR por cliente
- Churn prediction score
- Expansion/contraction
- LTV estimado

**Dica:** Criar lista HubSpot "Clientes com risco de churn" usando score do ProfitWell.

---

### FASE 4: Configuração HubSpot Onboarding - Tickets + Workflows (Dia 4-5)

> **Decisão Arquitetural:** Substituímos o Arrows ($99-299/mês) por recursos nativos do HubSpot (grátis). 
> O onboarding agora é gerenciado via **Pipeline de Tickets** + **Workflows automatizados**.

#### Passo 4.1: Criar Pipeline de Tickets "Onboarding Cliente"

Acessar **HubSpot > Service > Tickets > Pipelines > Create Pipeline**:

**Pipeline: "Onboarding Cliente"**

| Stage | Ordem | Status | Descrição |
|-------|-------|--------|-----------|
| Boas-vindas Enviadas | 1 | Open | Email de boas-vindas disparado |
| Dados Básicos Coletados | 2 | Open | Empresa preencheu dados iniciais |
| Configuração Inicial | 3 | Open | Logo, cores, configurações básicas |
| Importação de Dados | 4 | Open | Candidatos/vagas importados |
| Treinamento Agendado | 5 | Open | Sessão de treinamento confirmada |
| Go-Live | 6 | Open | Primeira vaga publicada |
| Onboarding Completo | 7 | Closed | Cliente ativo e autônomo |

#### Passo 4.2: Criar Propriedades Customizadas no Ticket

Acessar **HubSpot > Settings > Data Management > Properties > Tickets**:

| Propriedade | Nome Interno | Tipo | Descrição |
|-------------|--------------|------|-----------|
| Progresso Onboarding | `wedo_onboarding_progress` | Number (%) | 0-100% |
| Fase Atual | `wedo_onboarding_stage` | Dropdown | Stages do pipeline |
| CSM Responsável | `wedo_assigned_csm` | HubSpot User | Customer Success Manager |
| Data Prevista Go-Live | `wedo_golive_target_date` | Date | SLA de onboarding |

#### Passo 4.3: Criar Workflows Automatizados

Acessar **HubSpot > Automation > Workflows**:

**Workflow 1: "Deal Fechado → Criar Ticket Onboarding"**
```
Trigger: Deal stage = "Cliente Ativo"
Actions:
  1. Create Ticket (Pipeline: "Onboarding Cliente", Stage: "Boas-vindas Enviadas")
  2. Set Ticket property: wedo_assigned_csm = [Deal owner ou CSM padrão]
  3. Set Ticket property: wedo_onboarding_progress = 0
  4. Create Task for CSM: "Enviar email de boas-vindas"
  5. Send internal notification to CS team
```

**Workflow 2: "Ticket Stage Changed → Enviar Email"**
```
Trigger: Ticket pipeline stage changed
Actions (branching por stage):
  - "Dados Básicos Coletados" → Email template "Próximos passos: Configuração"
  - "Configuração Inicial" → Email template "Hora de importar dados"
  - "Treinamento Agendado" → Email template "Confirmação do treinamento"
  - "Go-Live" → Email template "Parabéns! Você está ao vivo"
  - Update: wedo_onboarding_progress = [cálculo baseado no stage]
```

**Workflow 3: "Onboarding Completo → Atualizar Company"**
```
Trigger: Ticket stage = "Onboarding Completo"
Actions:
  1. Update associated Company: wedo_status = "active"
  2. Update associated Company: wedo_onboarding_complete = true
  3. Update associated Company: wedo_onboarding_date = [today]
  4. Send internal notification: "🎉 Cliente completou onboarding"
  5. Create Task: "Agendar check-in 30 dias"
```

#### Passo 4.4: Mapear Propriedades Ticket → Company

| Propriedade Ticket | Propriedade Company | Sincronização |
|--------------------|---------------------|---------------|
| `wedo_onboarding_progress` | `wedo_onboarding_progress` | Via workflow |
| `wedo_onboarding_stage` | `wedo_onboarding_phase` | Via workflow |
| Pipeline Stage | `wedo_onboarding_status` | Via workflow |
| Ticket Closed Date | `wedo_onboarding_date` | Via workflow |

> **Benefício:** Economia de ~R$ 30-75k/ano (custo Arrows) + menos integrações para manter.

---

### FASE 5: Integração HubSpot ↔ WorkOS (Dia 5-6)

#### Passo 5.1: Criar Organization no WorkOS

Quando cliente fecha contrato, criar organização no WorkOS:

```python
# Backend WeDo Talent
async def create_workos_org(company_id: str, company_name: str):
    org = workos.organizations.create_organization(
        name=company_name,
        domains=[company_domain],
        allow_profiles_outside_organization=False
    )
    
    # Salvar no HubSpot
    hubspot.update_company(company_id, {
        "wedo_workos_org_id": org.id
    })
    
    return org
```

#### Passo 5.2: Atualizar HubSpot via Webhooks SCIM

Quando usuários são provisionados/desprovisionados via SCIM:

```python
# Webhook SCIM do WorkOS
@router.post("/api/v1/workos/webhooks/scim")
async def scim_webhook(request: Request):
    event = await verify_and_parse_webhook(request)
    
    if event["event"] == "dsync.user.created":
        user = event["data"]
        
        # Criar Contact no HubSpot
        contact = hubspot.create_contact({
            "email": user["emails"][0]["value"],
            "firstname": user["name"]["givenName"],
            "lastname": user["name"]["familyName"],
            "wedo_role": "user",
            "wedo_client_id": company_id,
            "wedo_scim_provisioned": True
        })
        
        # Incrementar contador na Company
        company = hubspot.get_company(company_id)
        hubspot.update_company(company_id, {
            "wedo_users_count": company.wedo_users_count + 1
        })
    
    elif event["event"] == "dsync.user.deleted":
        # Arquivar contact, decrementar contador
        pass
```

#### Passo 5.3: Mapa de Eventos WorkOS → HubSpot

| Evento WorkOS | Ação HubSpot |
|---------------|--------------|
| `dsync.user.created` | Criar Contact, incrementar users_count |
| `dsync.user.deleted` | Arquivar Contact, decrementar users_count |
| `dsync.group.created` | Log atividade na Company |
| `connection.activated` | wedo_sso_enabled = true |
| `connection.deactivated` | wedo_sso_enabled = false |

---

### FASE 6: Integração Backend WeDo Talent (Rails + PostgreSQL)

Esta fase detalha como integrar o backend WeDo Talent com HubSpot para manter dados sincronizados bidirecionalmente.

#### Passo 6.1: Adicionar Gem HubSpot ao Rails

```ruby
# Gemfile
gem 'hubspot-api-client', '~> 19.0'
```

```bash
bundle install
```

#### Passo 6.2: Configurar Inicializador HubSpot

```ruby
# config/initializers/hubspot.rb
require 'hubspot-api-client'

HUBSPOT_CLIENT = Hubspot::Client.new(
  access_token: ENV['HUBSPOT_ACCESS_TOKEN']
)
```

```bash
# .env ou secrets
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx
HUBSPOT_CLIENT_SECRET=xxxxxxxx  # Para validar webhooks
```

#### Passo 6.3: Criar Migrations para Sync

```bash
rails generate migration AddHubspotFieldsToClientAccounts
rails generate migration CreateHubspotEvents
```

```ruby
# db/migrate/xxx_add_hubspot_fields_to_client_accounts.rb
class AddHubspotFieldsToClientAccounts < ActiveRecord::Migration[7.1]
  def change
    add_column :client_accounts, :hubspot_company_id, :string
    add_column :client_accounts, :hubspot_deal_id, :string
    add_column :client_accounts, :hubspot_synced_at, :datetime
    add_column :client_accounts, :hubspot_sync_error, :text
    
    add_index :client_accounts, :hubspot_company_id, unique: true
  end
end

# db/migrate/xxx_create_hubspot_events.rb
class CreateHubspotEvents < ActiveRecord::Migration[7.1]
  def change
    create_table :hubspot_events do |t|
      t.bigint :event_id, null: false
      t.string :event_type, null: false
      t.bigint :object_id
      t.string :property_name
      t.text :property_value
      t.bigint :occurred_at
      t.string :status, default: 'pending'
      t.text :error_message
      
      t.timestamps
    end
    
    add_index :hubspot_events, :event_id, unique: true
    add_index :hubspot_events, :event_type
    add_index :hubspot_events, :status
  end
end
```

```bash
rails db:migrate
```

#### Passo 6.4: Criar Service Object para HubSpot

```ruby
# app/services/hubspot_service.rb
class HubspotService
  def initialize
    @client = HUBSPOT_CLIENT
  end

  # ==========================================
  # COMPANIES (ClientAccounts)
  # ==========================================
  
  def sync_client_to_hubspot(client_account)
    properties = build_company_properties(client_account)
    
    if client_account.hubspot_company_id.present?
      update_company(client_account.hubspot_company_id, properties)
    else
      company = create_company(properties)
      client_account.update!(
        hubspot_company_id: company.id,
        hubspot_synced_at: Time.current
      )
      company
    end
  rescue StandardError => e
    client_account.update!(hubspot_sync_error: e.message)
    Rails.logger.error("HubSpot sync error for client #{client_account.id}: #{e.message}")
    raise
  end

  def find_company_by_wedo_id(wedo_client_id)
    body = {
      filterGroups: [{
        filters: [{
          propertyName: "wedo_client_id",
          operator: "EQ",
          value: wedo_client_id.to_s
        }]
      }]
    }
    
    result = @client.crm.companies.search_api.do_search(
      public_object_search_request: body
    )
    
    result.results.first
  end

  # ==========================================
  # CONTACTS (Users)
  # ==========================================
  
  def sync_user_to_hubspot(user, client_account)
    properties = build_contact_properties(user, client_account)
    
    existing = find_contact_by_email(user.email)
    
    if existing
      update_contact(existing.id, properties)
    else
      create_contact(properties)
    end
  end

  def find_contact_by_email(email)
    body = {
      filterGroups: [{
        filters: [{
          propertyName: "email",
          operator: "EQ",
          value: email
        }]
      }]
    }
    
    result = @client.crm.contacts.search_api.do_search(
      public_object_search_request: body
    )
    
    result.results.first
  end

  # ==========================================
  # DEALS
  # ==========================================
  
  def create_deal_for_client(client_account, deal_name:, amount:, stage: "Proposta Enviada")
    pipeline_id = find_pipeline_id("WeDo Talent Contracts")
    stage_id = find_stage_id(pipeline_id, stage)
    
    properties = {
      dealname: deal_name,
      amount: amount,
      pipeline: pipeline_id,
      dealstage: stage_id,
      wedo_client_id: client_account.id.to_s
    }
    
    deal = @client.crm.deals.basic_api.create(
      simple_public_object_input_for_create: { properties: properties }
    )
    
    # Associar deal à company
    if client_account.hubspot_company_id.present?
      associate_deal_to_company(deal.id, client_account.hubspot_company_id)
    end
    
    client_account.update!(hubspot_deal_id: deal.id)
    deal
  end

  def update_deal_stage(deal_id, new_stage)
    pipeline_id = find_pipeline_id("WeDo Talent Contracts")
    stage_id = find_stage_id(pipeline_id, new_stage)
    
    @client.crm.deals.basic_api.update(
      deal_id: deal_id,
      simple_public_object_input: {
        properties: { dealstage: stage_id }
      }
    )
  end

  private

  def build_company_properties(client_account)
    {
      name: client_account.company_name,
      domain: client_account.domain,
      wedo_client_id: client_account.id.to_s,
      wedo_plan: client_account.subscription_plan,
      wedo_status: client_account.status,
      wedo_mrr: client_account.mrr_cents.to_f / 100,
      wedo_user_limit: client_account.user_limit,
      wedo_users_count: client_account.users.active.count,
      wedo_sso_enabled: client_account.sso_enabled?,
      wedo_workos_org_id: client_account.workos_organization_id,
      wedo_stripe_customer_id: client_account.stripe_customer_id
    }
  end

  def build_contact_properties(user, client_account)
    {
      email: user.email,
      firstname: user.first_name,
      lastname: user.last_name,
      wedo_role: user.role,
      wedo_client_id: client_account.id.to_s,
      wedo_last_login: user.last_login_at&.iso8601,
      wedo_scim_provisioned: user.scim_provisioned?
    }
  end

  def create_company(properties)
    @client.crm.companies.basic_api.create(
      simple_public_object_input_for_create: { properties: properties }
    )
  end

  def update_company(company_id, properties)
    @client.crm.companies.basic_api.update(
      company_id: company_id,
      simple_public_object_input: { properties: properties }
    )
  end

  def create_contact(properties)
    @client.crm.contacts.basic_api.create(
      simple_public_object_input_for_create: { properties: properties }
    )
  end

  def update_contact(contact_id, properties)
    @client.crm.contacts.basic_api.update(
      contact_id: contact_id,
      simple_public_object_input: { properties: properties }
    )
  end

  def associate_deal_to_company(deal_id, company_id)
    @client.crm.associations.v4.basic_api.create(
      object_type: "deals",
      object_id: deal_id,
      to_object_type: "companies",
      to_object_id: company_id,
      association_spec: [{ associationCategory: "HUBSPOT_DEFINED", associationTypeId: 5 }]
    )
  end

  def find_pipeline_id(pipeline_name)
    # Cache this in production
    pipelines = @client.crm.pipelines.pipelines_api.get_all(object_type: "deals")
    pipeline = pipelines.results.find { |p| p.label == pipeline_name }
    pipeline&.id
  end

  def find_stage_id(pipeline_id, stage_name)
    # Cache this in production
    pipelines = @client.crm.pipelines.pipelines_api.get_all(object_type: "deals")
    pipeline = pipelines.results.find { |p| p.id == pipeline_id }
    stage = pipeline&.stages&.find { |s| s.label == stage_name }
    stage&.id
  end
end
```

#### Passo 6.5: Criar Webhook Controller

```ruby
# config/routes.rb
namespace :api do
  namespace :v1 do
    namespace :webhooks do
      post 'hubspot', to: 'hubspot#receive'
    end
  end
end
```

```ruby
# app/controllers/api/v1/webhooks/hubspot_controller.rb
module Api
  module V1
    module Webhooks
      class HubspotController < ApplicationController
        skip_before_action :verify_authenticity_token
        before_action :verify_hubspot_signature

        def receive
          events = JSON.parse(request.body.read)
          
          events.each do |event|
            # Deduplicate by event_id
            next if HubspotEvent.exists?(event_id: event['eventId'])
            
            HubspotEvent.create!(
              event_id: event['eventId'],
              event_type: event['subscriptionType'],
              object_id: event['objectId'],
              property_name: event['propertyName'],
              property_value: event['propertyValue'],
              occurred_at: event['occurredAt']
            )
          end
          
          # Process async
          ProcessHubspotEventsJob.perform_later
          
          head :ok
        rescue JSON::ParserError => e
          Rails.logger.error("Invalid HubSpot webhook payload: #{e.message}")
          head :bad_request
        end

        private

        def verify_hubspot_signature
          signature = request.headers['X-HubSpot-Signature']
          body = request.body.read
          request.body.rewind
          
          secret = ENV['HUBSPOT_CLIENT_SECRET']
          expected = OpenSSL::HMAC.hexdigest('sha256', secret, body)
          
          unless Rack::Utils.secure_compare(signature.to_s, expected)
            Rails.logger.warn("Invalid HubSpot webhook signature")
            head :unauthorized
          end
        end
      end
    end
  end
end
```

#### Passo 6.6: Criar Background Job para Processar Eventos

```ruby
# app/jobs/process_hubspot_events_job.rb
class ProcessHubspotEventsJob < ApplicationJob
  queue_as :webhooks

  def perform
    HubspotEvent.pending.find_each do |event|
      process_event(event)
    end
  end

  private

  def process_event(event)
    case event.event_type
    when 'company.propertyChange'
      handle_company_change(event)
    when 'deal.propertyChange'
      handle_deal_change(event)
    when 'contact.creation'
      handle_contact_created(event)
    end
    
    event.update!(status: 'processed')
  rescue StandardError => e
    event.update!(status: 'failed', error_message: e.message)
    Rails.logger.error("Failed to process HubSpot event #{event.id}: #{e.message}")
  end

  def handle_company_change(event)
    # Find local client by HubSpot ID
    client = ClientAccount.find_by(hubspot_company_id: event.object_id.to_s)
    return unless client

    # Map HubSpot property to local field
    case event.property_name
    when 'wedo_status'
      client.update!(status: event.property_value)
    when 'wedo_plan'
      client.update!(subscription_plan: event.property_value)
    end
  end

  def handle_deal_change(event)
    # Quando deal muda de stage, pode disparar ações
    if event.property_name == 'dealstage'
      client = ClientAccount.find_by(hubspot_deal_id: event.object_id.to_s)
      return unless client

      # Map stage to action
      case stage_name_from_id(event.property_value)
      when 'Cliente Ativo'
        ActivateClientJob.perform_later(client.id)
      when 'Perdido'
        DeactivateClientJob.perform_later(client.id)
      end
    end
  end

  def handle_contact_created(event)
    # Sync contact from HubSpot to local DB if needed
    hubspot = HubspotService.new
    contact = hubspot.find_contact_by_id(event.object_id)
    # Process as needed
  end

  def stage_name_from_id(stage_id)
    # Cache pipeline stages
    Rails.cache.fetch("hubspot_stage_#{stage_id}", expires_in: 1.hour) do
      # Lookup stage name
    end
  end
end
```

#### Passo 6.7: Callbacks nos Models para Auto-Sync

```ruby
# app/models/client_account.rb
class ClientAccount < ApplicationRecord
  after_commit :sync_to_hubspot, on: [:create, :update], if: :should_sync?

  private

  def should_sync?
    # Don't sync during HubSpot webhook processing (avoid loops)
    !Thread.current[:hubspot_sync_in_progress]
  end

  def sync_to_hubspot
    SyncClientToHubspotJob.perform_later(id)
  end
end

# app/jobs/sync_client_to_hubspot_job.rb
class SyncClientToHubspotJob < ApplicationJob
  queue_as :hubspot_sync

  def perform(client_id)
    client = ClientAccount.find(client_id)
    hubspot = HubspotService.new
    hubspot.sync_client_to_hubspot(client)
  end
end
```

#### Passo 6.8: Schema PostgreSQL Completo

```sql
-- Tabelas para sincronização HubSpot

-- client_accounts (já existente, adicionar campos)
ALTER TABLE client_accounts ADD COLUMN hubspot_company_id VARCHAR(50) UNIQUE;
ALTER TABLE client_accounts ADD COLUMN hubspot_deal_id VARCHAR(50);
ALTER TABLE client_accounts ADD COLUMN hubspot_synced_at TIMESTAMP;
ALTER TABLE client_accounts ADD COLUMN hubspot_sync_error TEXT;

-- users (já existente, adicionar campos)
ALTER TABLE users ADD COLUMN hubspot_contact_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN hubspot_synced_at TIMESTAMP;

-- hubspot_events (log de webhooks)
CREATE TABLE hubspot_events (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT UNIQUE NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  object_id BIGINT,
  property_name VARCHAR(100),
  property_value TEXT,
  occurred_at BIGINT,
  status VARCHAR(20) DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hubspot_events_status ON hubspot_events(status);
CREATE INDEX idx_hubspot_events_type ON hubspot_events(event_type);

-- hubspot_sync_log (auditoria)
CREATE TABLE hubspot_sync_logs (
  id BIGSERIAL PRIMARY KEY,
  syncable_type VARCHAR(100) NOT NULL,
  syncable_id BIGINT NOT NULL,
  direction VARCHAR(20) NOT NULL, -- 'to_hubspot' ou 'from_hubspot'
  action VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
  payload JSONB,
  response JSONB,
  status VARCHAR(20) DEFAULT 'success',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hubspot_sync_logs_syncable ON hubspot_sync_logs(syncable_type, syncable_id);
```

#### Passo 6.9: Diagrama de Fluxo de Dados

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUXO BIDIRECIONAL HUBSPOT ↔ RAILS                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RAILS → HUBSPOT (Push)                                                  │
│  ═══════════════════════                                                 │
│                                                                          │
│  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐       │
│  │ ClientAccount│────►│SyncToHubspotJob  │────►│ HubSpot API     │       │
│  │ after_commit │     │ (Sidekiq/Resque) │     │ Companies/Deals │       │
│  └─────────────┘     └──────────────────┘     └─────────────────┘       │
│                                                                          │
│  Eventos que disparam sync:                                              │
│  • Cliente criado/atualizado                                             │
│  • Plano alterado                                                        │
│  • Status mudou (active, cancelled)                                      │
│  • Usuário convidado/removido                                            │
│                                                                          │
│  ───────────────────────────────────────────────────────────────────     │
│                                                                          │
│  HUBSPOT → RAILS (Pull via Webhooks)                                     │
│  ═══════════════════════════════════                                     │
│                                                                          │
│  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐       │
│  │ HubSpot     │────►│ POST /webhooks   │────►│ProcessEventsJob │       │
│  │ Webhooks    │     │ /hubspot         │     │ → Update DB     │       │
│  └─────────────┘     └──────────────────┘     └─────────────────┘       │
│                                                                          │
│  Eventos que recebemos:                                                  │
│  • company.propertyChange                                                │
│  • deal.propertyChange (stage mudou)                                     │
│  • contact.creation                                                      │
│                                                                          │
│  ───────────────────────────────────────────────────────────────────     │
│                                                                          │
│  ANTI-LOOP PROTECTION                                                    │
│  ═══════════════════                                                     │
│                                                                          │
│  Thread.current[:hubspot_sync_in_progress] = true                        │
│  • Se recebemos webhook, marcamos flag                                   │
│  • Callback after_commit verifica flag                                   │
│  • Não envia de volta ao HubSpot (evita loop infinito)                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Passo 6.10: Configurar Webhooks no HubSpot

1. Acessar **HubSpot > Settings > Integrations > Private Apps**
2. Editar a Private App "WeDo Talent Backend"
3. Ir na aba **Webhooks**
4. Adicionar subscription:

| Evento | URL | Método |
|--------|-----|--------|
| `company.propertyChange` | `https://api.wedotalent.com/api/v1/webhooks/hubspot` | POST |
| `deal.propertyChange` | `https://api.wedotalent.com/api/v1/webhooks/hubspot` | POST |
| `deal.creation` | `https://api.wedotalent.com/api/v1/webhooks/hubspot` | POST |
| `contact.creation` | `https://api.wedotalent.com/api/v1/webhooks/hubspot` | POST |

**Importante:** URL deve ser HTTPS. Para desenvolvimento local, usar ngrok:
```bash
ngrok http 3000
# URL: https://abc123.ngrok.io/api/v1/webhooks/hubspot
```

---

### FASE 7: Fluxo Completo End-to-End (Referência)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO: NOVO CLIENTE WEDO TALENT                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. VENDAS (HubSpot)                                                        │
│     └─► Deal criado no pipeline "WeDo Talent Contracts"                     │
│         └─► Stage: "Proposta Enviada"                                       │
│                                                                             │
│  2. FECHAMENTO                                                              │
│     └─► Deal stage → "Contrato Assinado"                                    │
│         ├─► [Auto] Criar Customer no Stripe                                 │
│         └─► [Auto] Criar Company no HubSpot (se não existir)                │
│                                                                             │
│  3. PAGAMENTO (Stripe → Rails → HubSpot)                                    │
│     └─► Cliente paga primeira fatura                                        │
│         ├─► Stripe Webhook: invoice.paid → Rails                            │
│         ├─► Rails StripeSyncService: atualiza HubSpot                       │
│         ├─► [Auto] HubSpot Company: status = "active"                       │
│         ├─► [Auto] HubSpot Deal: stage = "Cliente Ativo"                    │
│         └─► [Auto] ProfitWell: MRR atualizado                               │
│                                                                             │
│  4. ONBOARDING (HubSpot Tickets + Workflows)                                │
│     └─► Deal stage = "Cliente Ativo"                                        │
│         ├─► [Workflow] Criar Ticket "Onboarding Cliente"                    │
│         ├─► [Workflow] Enviar email boas-vindas                             │
│         └─► Ticket progride pelas stages conforme cliente avança            │
│                                                                             │
│  5. SSO ENTERPRISE (WorkOS → HubSpot)                                       │
│     └─► Se cliente enterprise:                                              │
│         ├─► Criar WorkOS Organization                                       │
│         ├─► HubSpot: wedo_workos_org_id = org_xxx                           │
│         ├─► Cliente configura IdP (Azure AD, Okta, Google)                  │
│         ├─► Webhook: connection.activated                                   │
│         └─► HubSpot: wedo_sso_enabled = true                                │
│                                                                             │
│  6. OPERAÇÃO CONTÍNUA                                                       │
│     ├─► Stripe: cobranças automáticas mensais                               │
│     ├─► ProfitWell: métricas atualizadas diariamente                        │
│     ├─► WorkOS/SCIM: usuários sincronizados em tempo real                   │
│     └─► HubSpot: visão 360° do cliente sempre atualizada                    │
│                                                                             │
│  7. RENOVAÇÃO/CHURN                                                         │
│     ├─► ProfitWell detecta risco de churn                                   │
│     ├─► HubSpot: criar tarefa para CS intervir                              │
│     ├─► Stripe: subscription.deleted                                        │
│     └─► HubSpot: status = "cancelled"                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Checklist de Implementação

| Fase | Item | Tempo | Status |
|------|------|-------|--------|
| **1. HubSpot Setup** | | **4h** | |
| | Criar Private App | 30min | ⬜ |
| | Criar propriedades Companies | 1h | ⬜ |
| | Criar propriedades Contacts | 30min | ⬜ |
| | Criar pipeline Deals | 30min | ⬜ |
| | Criar pipeline Services | 30min | ⬜ |
| | Testar API | 1h | ⬜ |
| **2. Stripe + Sync** | | **3h** | |
| | Criar produtos Stripe | 30min | ⬜ |
| | Configurar webhooks → Rails | 1h | ⬜ |
| | Implementar StripeSyncService | 1.5h | ⬜ |
| **3. ProfitWell** | | **1h** | |
| | Conectar ao Stripe | 15min | ⬜ |
| | Conectar ao HubSpot | 15min | ⬜ |
| | Configurar sync | 30min | ⬜ |
| **4. HubSpot Onboarding** | | **2h** | |
| | Criar pipeline Tickets "Onboarding Cliente" | 30min | ⬜ |
| | Criar propriedades customizadas nos Tickets | 30min | ⬜ |
| | Criar workflows automatizados (3 workflows) | 45min | ⬜ |
| | Testar fluxo Deal → Ticket → Emails | 15min | ⬜ |
| **5. WorkOS** | | **2h** | |
| | Criar endpoint webhook | 1h | ⬜ |
| | Mapear eventos → HubSpot | 30min | ⬜ |
| | Testar SCIM sync | 30min | ⬜ |
| **6. Backend Rails** | | **8h** | |
| | Adicionar gem hubspot-api-client | 15min | ⬜ |
| | Configurar inicializador | 15min | ⬜ |
| | Criar migrations (hubspot_id, events) | 30min | ⬜ |
| | Criar HubspotService | 2h | ⬜ |
| | Criar WebhooksController | 1h | ⬜ |
| | Criar ProcessHubspotEventsJob | 1h | ⬜ |
| | Adicionar callbacks nos models | 1h | ⬜ |
| | Configurar webhooks no HubSpot | 30min | ⬜ |
| | Testar sync bidirecional | 1.5h | ⬜ |
| **TOTAL** | | **20h** | |

---

## 1.5 Guia HubSpot Onboarding (Tickets + Workflows)

### Visão Geral

O onboarding de clientes WeDo Talent é gerenciado 100% dentro do HubSpot usando recursos nativos:
- **Pipeline de Tickets:** Stages visuais do processo de onboarding
- **Workflows:** Automações para criar tickets, enviar emails e atualizar dados
- **Propriedades Customizadas:** Tracking de progresso, CSM responsável, datas

> **Decisão Estratégica:** Optamos por usar HubSpot Tickets + Workflows ao invés de Arrows.
> **Benefício:** Economia de ~R$ 30-75k/ano + menos integrações + tudo em um só lugar.

### Arquitetura de Onboarding

```
Deal Fechado ──► Workflow 1 ──► Ticket Criado ──► Stage 1: Boas-vindas
                                      │
                                      ▼
                               Stage 2: Dados Básicos ──► Email automático
                                      │
                                      ▼
                               Stage 3: Configuração ──► Email automático
                                      │
                                      ▼
                               Stage 4: Importação ──► Email automático
                                      │
                                      ▼
                               Stage 5: Treinamento ──► Email automático
                                      │
                                      ▼
                               Stage 6: Go-Live ──► Email automático
                                      │
                                      ▼
                               Stage 7: Completo ──► Workflow 3 ──► Company atualizada
```

### Configuração Detalhada

Consulte **FASE 4** na seção 1.4 acima para o passo a passo completo.

### Pipeline de Onboarding WeDo Talent

| Stage | Descrição | Email Automático | Duração Esperada |
|-------|-----------|------------------|------------------|
| **Boas-vindas Enviadas** | Deal fechado, ticket criado | "Bem-vindo à WeDo Talent!" | Dia 0-1 |
| **Dados Básicos Coletados** | Cliente preencheu formulário inicial | "Próximos passos: Configuração" | Dias 1-3 |
| **Configuração Inicial** | Logo, cores, templates configurados | "Hora de importar seus dados" | Dias 3-5 |
| **Importação de Dados** | Candidatos/vagas importados | "Agora vamos agendar seu treinamento" | Dias 5-7 |
| **Treinamento Agendado** | Sessão de treinamento confirmada | "Confirmação do treinamento" | Dias 7-10 |
| **Go-Live** | Primeira vaga publicada | "Parabéns! Você está ao vivo 🎉" | Dias 10-14 |
| **Onboarding Completo** | Cliente autônomo | Task: "Check-in 30 dias" | Dia 14+ |

---

## 1.6 Guia WorkOS SSO/SCIM

> **Status:** ✅ **Já integrado e funcionando** no WeDo Talent

### 1.6.1 Visão Geral

#### O que é SSO (Single Sign-On)?

O SSO permite que colaboradores acessem a plataforma LIA usando as mesmas credenciais corporativas que já utilizam para outros sistemas da empresa (email, intranet, etc.). Isso significa:

- **Login único**: Usuários não precisam criar ou lembrar senhas separadas para a LIA
- **Acesso simplificado**: Um clique para entrar na plataforma
- **Segurança centralizada**: Controle de acesso gerenciado pelo departamento de TI

#### O que é SCIM (Directory Sync)?

O SCIM sincroniza automaticamente usuários e grupos do diretório corporativo com a LIA:

- **Provisionamento automático**: Novos colaboradores ganham acesso automaticamente
- **Desprovisionamento automático**: Colaboradores desligados perdem acesso instantaneamente
- **Sincronização de grupos**: Times e departamentos são refletidos na plataforma

#### Benefícios para a Empresa

| Benefício | Descrição |
|-----------|-----------|
| **Segurança** | Autenticação centralizada com políticas corporativas de senha e MFA |
| **Produtividade** | Menos tempo perdido com problemas de login e senhas esquecidas |
| **Compliance** | Trilha de auditoria completa para BCB 498, SOC 2 e LGPD |
| **Automação** | Gestão de usuários automática via diretório corporativo |

#### Autenticação: Nativa vs WorkOS

| Tipo de Cliente | Autenticação | WorkOS |
|-----------------|--------------|--------|
| Starter/Professional | Email/Senha (nativo) | Não usa |
| Enterprise | SSO via WorkOS (opcional) | SAML/OIDC configurável |

> **O WorkOS é preparado automaticamente** quando o cliente é criado, mas só é ativado se o cliente solicitar configuração SSO.

---

### 1.6.2 Arquitetura do Sistema

#### 1.6.2.1 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITETURA WEDOTALENT                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   INTERNET      │
                                    └────────┬────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
    ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
    │     WorkOS      │          │    HubSpot      │          │  IdP Cliente    │
    │  (SSO/SCIM)     │          │    (CRM)        │          │ (Azure/Okta)    │
    └────────┬────────┘          └────────┬────────┘          └────────┬────────┘
             │                            │                            │
             │ SCIM Webhooks              │ REST API                   │ SAML/OIDC
             │                            │                            │
    ┌────────┴────────────────────────────┴────────────────────────────┴────────┐
    │                                                                            │
    │                         ┌──────────────────────────┐                       │
    │                         │   FRONTEND (Next.js)     │                       │
    │                         │   Port 5000              │                       │
    │                         │                          │                       │
    │  ┌──────────────────────┼──────────────────────────┼──────────────────────┐│
    │  │                      │                          │                      ││
    │  │                        │   ┌───────────────┐      │   ┌───────────────┐  ││
    │  │                        │   │  PLATAFORMA   │      │   │ CONFIGURAÇÕES │  ││
    │  │   (Admin Layer via     │   │  WEDOTALENT   │      │   │               │  ││
    │  │    HubSpot/WorkOS)     │   │  /vagas, etc  │      │   │ /configuracoes│  ││
    │  │                        │   └───────────────┘      │   └───────────────┘  ││
    │  │                        │          │               │          │           ││
    │  │        Time WeDo usa   │          │ Clientes      │          │ Clientes  ││
    │  │        SaaS externo    │          │               │          │ (Admin)   ││
    │  └────────┼─────────────┼──────────┼───────────────┼──────────┼───────────┘│
    │           │             │          │               │          │            │
    │           └─────────────┴──────────┴───────────────┴──────────┘            │
    │                                    │                                        │
    │                         ┌──────────┴──────────┐                            │
    │                         │  Backend-Proxy      │                            │
    │                         │  /api/backend-proxy │                            │
    │                         │  (Injeta headers)   │                            │
    │                         └──────────┬──────────┘                            │
    │                                    │                                        │
    └────────────────────────────────────┼────────────────────────────────────────┘
                                         │
                                         │ HTTP + Headers (X-Company-ID, X-User-Role)
                                         ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         BACKEND (Ruby on Rails)                              │
    │                         Port 3000                                            │
    │                                                                              │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
    │  │ API Clients     │  │ API WorkOS      │  │ API Users       │              │
    │  │ /api/v1/clients │  │ /api/v1/workos  │  │ /api/v1/users   │              │
    │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
    │           │                    │                    │                        │
    │  ┌────────┴────────────────────┴────────────────────┴────────┐              │
    │  │                      SERVICES LAYER                       │              │
    │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │              │
    │  │  │ WorkOS       │ │ HubSpot      │ │ Email        │       │              │
    │  │  │ Provisioning │ │ Service      │ │ Service      │       │              │
    │  │  └──────────────┘ └──────────────┘ └──────────────┘       │              │
    │  └───────────────────────────────────────────────────────────┘              │
    │                                    │                                         │
    └────────────────────────────────────┼─────────────────────────────────────────┘
                                         │
                                         ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                      ADMIN LAYER (7 SaaS Tools)                              │
    │                                                                              │
    │  ┌──────────┐ ┌──────────┐ ┌─────────────────────────┐                       │
    │  │  Stripe  │ │ProfitWell│ │        HubSpot         │                       │
    │  │ Billing  │ │ Metrics  │ │  CRM + Tickets + Wkfl  │                       │
    │  └──────────┘ └──────────┘ └─────────────────────────┘                       │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
    │  │  WorkOS  │ │Vanta/    │ │ Privacy  │ │ Warden   │                        │
    │  │ SSO/SCIM │ │Drata     │ │  Tools   │ │   AI     │                        │
    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                        │
    │                                                                              │
    │  📌 FLUXO STRIPE → HUBSPOT (via Rails):                                      │
    │     Stripe ──webhooks──► Rails (StripeSyncService) ──API──► HubSpot          │
    │     (Integração nativa HubSpot-Stripe não disponível no Brasil)              │
    └─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         POSTGRESQL (Replit)                                  │
    │                                                                              │
    │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
    │  │client_accounts│ │ client_users  │ │company_workos │ │ sso_audit_logs│    │
    │  │               │ │               │ │ _config       │ │               │    │
    │  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘    │
    │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                      │
    │  │ workos_groups │ │workos_group_  │ │workos_group_  │                      │
    │  │               │ │ memberships   │ │ role_mappings │                      │
    │  └───────────────┘ └───────────────┘ └───────────────┘                      │
    └─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.6.2.2 Os Três Ambientes da Plataforma

A plataforma WeDo Talent possui **três ambientes distintos** que atendem diferentes públicos e necessidades:

##### **Ambiente 1: Admin Layer** (Ferramentas SaaS Externas)

| Aspecto | Detalhes |
|---------|----------|
| **Público** | Equipe interna WeDo Talent |
| **Acesso** | Credenciais das ferramentas SaaS |
| **Propósito** | Gestão de clientes, onboarding, configuração SSO, billing |

> **Arquitetura sem Admin Frontend:** O WeDo Talent **não possui área admin frontend**. A gestão é feita via ferramentas SaaS externas:

| Função | Ferramenta | URL |
|--------|------------|-----|
| CRUD de clientes | HubSpot CRM | https://app.hubspot.com/contacts |
| Dashboard de onboarding | HubSpot Tickets | https://app.hubspot.com/tickets |
| Métricas SaaS (MRR, Churn) | ProfitWell | https://app.profitwell.com |
| Configuração SSO/SCIM | WorkOS Dashboard | https://dashboard.workos.com |
| Billing e Subscriptions | Stripe Dashboard | https://dashboard.stripe.com |

**Características:**
- Gestão centralizada via ferramentas SaaS especializadas
- Backend Rails fornece APIs (`/api/v1/*`) para integrações
- Workflows automatizados via HubSpot
- Sem necessidade de desenvolver interface admin custom

##### **Ambiente 2: Plataforma WeDo Talent** (`/vagas`, `/candidatos`, `/pipeline`, etc.)

| Aspecto | Detalhes |
|---------|----------|
| **Público** | Clientes (empresas contratantes) |
| **Acesso** | Requer autenticação (email/senha ou SSO) |
| **Propósito** | Uso diário da plataforma de recrutamento |

**Páginas Principais:**

| URL | Função |
|-----|--------|
| `/vagas` | Gestão de vagas |
| `/candidatos` | Base de candidatos |
| `/pipeline` | Kanban de processos |
| `/buscar` | Busca de talentos |
| `/chat` | Conversa com LIA |

**Características:**
- Acesso **isolado** aos dados da própria empresa (multi-tenant)
- Funcionalidades de recrutamento com IA
- Integração com LIA para triagem e análise

##### **Ambiente 3: Menu Configurações** (`/configuracoes`)

| Aspecto | Detalhes |
|---------|----------|
| **Público** | Administradores do cliente |
| **Acesso** | Requer role `admin` dentro da empresa |
| **Propósito** | Self-service para configurações da conta |

**Abas Disponíveis:**

| Aba | Função | Componente |
|-----|--------|------------|
| **Empresa** | Dados, logo, tech stack | `CompanyTeamHub` |
| **Equipe** | Convidar/gerenciar usuários | `UserManagement` |
| **Departamentos** | Estrutura organizacional | - |
| **Cultura** | Valores, Big Five | `BigFiveRadar` |
| **Benefícios** | Pacote de benefícios | `BenefitsTab` |
| **Aprovadores** | Fluxo de aprovação | - |

**Características:**
- Self-service: cliente gerencia sua própria equipe
- Limite de licenças (`user_limit`) aplicado
- Configurações SSO são gerenciadas pelo time WeDo via WorkOS Dashboard (cliente não tem acesso direto)

#### 1.6.2.3 Comparativo dos Três Ambientes

| Característica | Admin Layer (SaaS) | Plataforma | Configurações |
|----------------|-------------------|------------|---------------|
| **Acesso** | Equipe interna WeDo | Todos usuários cliente | Admin cliente |
| **Multi-tenant** | Vê todos (HubSpot) | Isolado por empresa | Isolado |
| **Pode criar clientes** | ✅ (HubSpot) | ❌ | ❌ |
| **Pode convidar usuários** | ✅ | ❌ | ✅ |
| **Pode configurar SSO** | ✅ (WorkOS) | ❌ | ❌ |
| **Acesso às vagas** | ❌ (interno) | ✅ | ❌ |
| **Baseado em** | HubSpot, WorkOS, Stripe | Rotas principais | `/configuracoes` |

#### 1.6.2.4 Diagrama de Integrações Externas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRAÇÕES EXTERNAS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              WEDOTALENT
                         ┌─────────────────┐
                         │                 │
                         │  Ruby on Rails  │
                         │   Backend       │
                         │                 │
                         └────────┬────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     WorkOS      │     │    HubSpot      │     │  Email Provider │
│                 │     │                 │     │   (Mailgun)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ • SSO (SAML)    │     │ • Companies     │     │ • Boas-vindas   │
│ • SCIM Sync     │     │ • Contacts      │     │ • Convites      │
│ • MFA           │     │ • Deals         │     │ • Notificações  │
│ • Audit Logs    │     │ • Custom Props  │     │                 │
│ • Directory     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  IdP Cliente    │
│ ┌─────────────┐ │
│ │ Azure AD    │ │
│ │ Okta        │ │
│ │ Google WS   │ │
│ └─────────────┘ │
└─────────────────┘
```

#### 1.6.2.5 Fluxo de Dados: Login SSO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SEQUÊNCIA: AUTENTICAÇÃO SSO                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    Usuário         Frontend         WorkOS           IdP            Backend
    ───────         ────────         ──────           ───            ───────
       │                │                │              │                │
       │ Acessa /login  │                │              │                │
       ├───────────────►│                │              │                │
       │                │                │              │                │
       │ Insere email   │                │              │                │
       │ corporativo    │                │              │                │
       ├───────────────►│                │              │                │
       │                │                │              │                │
       │                │ Verifica SSO   │              │                │
       │                │ domain         │              │                │
       │                ├───────────────────────────────────────────────►│
       │                │◄───────────────────────────────────────────────┤
       │                │ sso_enabled=   │              │                │
       │                │ true           │              │                │
       │                │                │              │                │
       │ Clica "SSO"    │                │              │                │
       ├───────────────►│                │              │                │
       │                │                │              │                │
       │                │ GET /api/auth/ │              │                │
       │                │ workos/sso     │              │                │
       │                ├───────────────►│              │                │
       │                │                │              │                │
       │◄───────────────┼────────────────┤              │                │
       │ Redirect IdP   │                │              │                │
       │                │                │              │                │
       ├────────────────┼────────────────┼─────────────►│                │
       │                │                │              │                │
       │ Autentica      │                │              │                │
       │ no IdP         │                │              │                │
       │                │                │◄─────────────┤                │
       │                │                │ SAML Response│                │
       │                │                │              │                │
       │◄───────────────┼────────────────┤              │                │
       │ Redirect       │                │              │                │
       │ callback       │                │              │                │
       │                │                │              │                │
       ├───────────────►│ GET /api/auth/ │              │                │
       │                │ workos/callback│              │                │
       │                ├───────────────►│              │                │
       │                │◄───────────────┤              │                │
       │                │ profile+token  │              │                │
       │                │                │              │                │
       │                │ POST /api/v1/  │              │                │
       │                │ auth/workos/   │              │                │
       │                │ sync-user      │              │                │
       │                ├───────────────────────────────────────────────►│
       │                │◄───────────────────────────────────────────────┤
       │                │ user synced    │              │                │
       │                │                │              │                │
       │◄───────────────┤ Cookie +       │              │                │
       │                │ Redirect       │              │                │
       │ /login/welcome │ /login/welcome │              │                │
       │                │                │              │                │
```

#### 1.6.2.6 Boundaries de Segurança

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAMADAS DE SEGURANÇA                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTERNET (Público)                                 │
│                                                                              │
│  Endpoints públicos:                                                         │
│  • GET /login                    (Página de login)                           │
│  • GET /aceitar-convite          (Aceite de convite)                         │
│  • GET /api/v1/auth/check-sso-domain  (Verificação de SSO)                   │
│  • POST /api/v1/workos/webhooks/scim  (Webhook SCIM - validado por HMAC)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUTENTICAÇÃO (Cookie workos_session)                     │
│                                                                              │
│  Endpoints que requerem login:                                               │
│  • GET /api/v1/clients/{id}                                                  │
│  • GET /api/v1/clients/{id}/users                                            │
│  • POST /api/v1/invitations/accept                                           │
│  • Todas as rotas da Plataforma (/vagas, /candidatos, etc.)                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUTORIZAÇÃO (Role-based)                                 │
│                                                                              │
│  Endpoints Admin (requerem X-User-Role = admin):                             │
│  • POST /api/v1/clients           (Criar cliente)                            │
│  • PUT /api/v1/clients/{id}       (Editar cliente)                           │
│  • GET /api/v1/workos/admin/*     (Admin WorkOS)                             │
│  • POST /api/v1/clients/{id}/users (Convidar usuário)                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ISOLAMENTO MULTI-TENANT                                  │
│                                                                              │
│  Todas as queries filtradas por company_id:                                  │
│  • Clientes só veem seus próprios dados                                      │
│  • Header X-Company-ID injetado pelo backend-proxy                           │
│  • Validação adicional no backend antes de retornar dados                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 1.6.2.7 Tecnologias Utilizadas

| Camada | Tecnologia | Versão | Propósito |
|--------|------------|--------|-----------|
| **Frontend** | Next.js | 14.x | SSR, API Routes, React |
| **UI** | Tailwind CSS + shadcn/ui | - | Design system |
| **Backend** | Ruby on Rails | 7.x | API REST, ActiveRecord, background jobs |
| **ORM** | ActiveRecord | 7.x | Mapeamento objeto-relacional |
| **Database** | PostgreSQL | 15+ | Persistência |
| **Auth** | WorkOS SDK | - | SSO, SCIM, MFA |
| **CRM** | HubSpot API | v3 | Sync de clientes |
| **Billing** | Stripe API | - | Pagamentos, subscriptions |
| **Billing Sync** | StripeSyncService | - | Stripe → Rails → HubSpot |
| **Email** | Mailgun | - | Transacional |

---

### 1.6.3 Diagrama de Jornada de Onboarding

**[Visualizar Diagrama FigJam - Jornada Completa de Onboarding WeDo Talent](https://www.figma.com/online-whiteboard/create-diagram/db01723f-6109-4267-a803-8c0f494a9686)**

Este diagrama mostra:
- Fluxo do time WeDo Talent (Admin)
- Jornada COM SSO (clientes Enterprise)
- Jornada SEM SSO (clientes Standard)
- Integração com HubSpot CRM

---

### 1.6.4 Checklist de Configuração

#### 1.6.4.1 Secrets Necessários (Replit)

| Secret | Descrição | Status |
|--------|-----------|--------|
| `WORKOS_API_KEY` | Chave de API do WorkOS | 📋 A configurar |
| `WORKOS_CLIENT_ID` | ID do cliente WorkOS | 📋 A configurar |
| `WORKOS_WEBHOOK_SECRET` | Secret para validação SCIM | 📋 A configurar |
| `HUBSPOT_ACCESS_TOKEN` | Token do HubSpot Private App | 📋 A configurar |

#### 1.6.4.2 Webhook WorkOS

| Configuração | Valor |
|--------------|-------|
| **Endpoint URL** | `https://{seu-dominio}/api/v1/workos/webhooks/scim` |
| **Eventos** | Directory User, Directory Group |
| **Validação** | HMAC SHA256 com `WORKOS_WEBHOOK_SECRET` |

#### 1.6.4.3 Propriedades HubSpot

Propriedades customizadas necessárias no HubSpot:

| Propriedade | Objeto | Descrição |
|-------------|--------|-----------|
| `lia_client_id` | Empresas, Contatos, Negócios | ID do cliente na LIA |
| `lia_plan` | Empresas, Negócios | Plano do cliente |
| `lia_status` | Empresas | Status do cliente |
| `lia_company_size` | Empresas | Tamanho da empresa |
| `lia_welcome_email_sent` | Empresas | Email de boas-vindas enviado |
| `lia_workos_configured` | Empresas | WorkOS configurado |
| `lia_sso_enabled` | Empresas | SSO habilitado |
| `lia_users_count` | Empresas | Número de usuários |
| `lia_role` | Contatos | Papel do contato |

#### 1.6.4.4 Provedores de Identidade Suportados

| Provedor | SSO (SAML/OIDC) | SCIM (Directory Sync) |
|----------|:---------------:|:---------------------:|
| **Microsoft Azure AD / Entra ID** | ✅ | ✅ |
| **Okta** | ✅ | ✅ |
| **OneLogin** | ✅ | ✅ |
| **PingIdentity** | ✅ | ✅ |

---

### 1.6.5 Jornada de Onboarding - Mapeamento Completo

> **Nota:** O onboarding de clientes é gerenciado 100% via **HubSpot Tickets + Workflows** nativos. Criamos um Pipeline de Tickets "Onboarding Cliente" com 7 stages (Boas-vindas → Onboarding Completo) e 3 workflows automatizados que disparam emails e atualizam status conforme o cliente progride.

#### Resumo: Onde Cada Coisa Acontece

| O que | Onde | Observação |
|-------|------|------------|
| Login do cliente | `/login` (Plataforma WedoTalent) | Email/senha ou SSO (se enterprise) |
| Gestão de equipe | `/configuracoes` → Equipe | Plataforma WedoTalent |
| Aceitar convite | `/aceitar-convite` | Plataforma WedoTalent |
| Configurar SSO | WorkOS Dashboard | Time WeDo configura para clientes enterprise |
| Gerenciar clientes | HubSpot CRM | Time WeDo (não existe frontend admin) |
| Planos de onboarding | HubSpot Tickets + Workflows | Pipeline "Onboarding Cliente" (nativo, grátis) |

#### FASE 1: Cadastro do Cliente (Time WedoTalent)

**Localização:** HubSpot CRM (https://app.hubspot.com/contacts)

**O que acontece automaticamente:**

```
POST /api/v1/clients
├── 1. ClientAccount criado no banco
├── 2. CompanyWorkOSConfig criado (SSO desabilitado por padrão)
├── 3. WorkOS Organization provisionada automaticamente
│   └── provision_workos_organization()
├── 4. Templates de email clonados para o cliente
│   └── clone_templates_for_client()
├── 5. HubSpot sync (Company + Contact + Deal)
│   └── hubspot_service.sync_client_to_hubspot()
├── 6. Stripe Customer criado (se billing ativo)
│   └── stripe_sync_service.create_customer()
└── 7. Email de boas-vindas enviado
    └── send_welcome_email() → Template "Boas-vindas ao Cliente"
```

#### FASE 2: Monitoramento do Onboarding (Time WedoTalent)

**Localização:** HubSpot Tickets - Pipeline "Onboarding Cliente"

| Etapa | Descrição | Status Automático |
|-------|-----------|-------------------|
| 1. Cliente criado | Conta cadastrada no sistema | ✅ Automático |
| 2. WorkOS Organization | Org criada no WorkOS | ⚠️ Dados indisponíveis* |
| 3. Email boas-vindas | Email enviado ao cliente | ⚠️ Dados indisponíveis* |
| 4. SSO configurado | SAML/OIDC configurado | ⚠️ Dados indisponíveis* |
| 5. Admin convidado | Primeiro usuário criado | ✅ Baseado em usersCount |
| 6. Admin primeiro login | Usuário fez login | ✅ Baseado em usersCount |
| 7. Setup inicial | Configurações básicas | ✅ status === 'active' |
| 8. Primeira vaga | Primeira vaga criada | ✅ activeJobsCount > 0 |

#### FASE 3: Primeiro Acesso (Cliente Admin)

**Localização:** `/login` → Plataforma WedoTalent

> **IMPORTANTE:** O WorkOS SSO é **OPCIONAL** e configurado posteriormente apenas para clientes enterprise. O primeiro acesso sempre é feito com email/senha na plataforma WedoTalent.

#### FASE 4: Convite de Usuários (Admin do Cliente)

**Localização:** `/configuracoes` → Aba "Equipe" (Plataforma WedoTalent)

> **IMPORTANTE:** Esta fase acontece 100% dentro da plataforma WedoTalent. O WorkOS NÃO é usado para convites de usuários. O sistema de convites é nativo da WedoTalent.

```
Frontend: UserManagement
├── POST /api/backend-proxy/clients/{id}/users
│   ├── Headers injetados no servidor (seguro)
│   └── Body: { email, name, role }
│
Backend: POST /api/v1/clients/{id}/users
├── 1. Valida limite de licenças (user_limit)
├── 2. Cria ClientUser com status 'pending'
├── 3. Gera invitation_token (UUID)
├── 4. Define invitation_expires_at (+7 dias)
├── 5. Envia email de convite
│   └── Template "Convite para WeDo Talent"
└── 6. Retorna dados do usuário + invitation_url
```

#### FASE 5: Aceite do Convite (Usuário Convidado)

**Localização:** `/aceitar-convite?token=xxx`

**Estados do token:**
- Válido → Mostra botão "Aceitar"
- Expirado → Mostra mensagem + "Solicitar novo convite"
- Inválido → Mostra erro

#### FASE 6: Configuração Inicial (Admin do Cliente)

**Localização:** `/configuracoes`

| Aba | Descrição | Componente |
|-----|-----------|------------|
| Empresa | Dados da empresa, logo, tech stack | CompanyTeamHub |
| Equipe | Gerenciar usuários | UserManagement |
| Departamentos | Estrutura organizacional | - |
| Cultura | Valores, Big Five | BigFiveRadar |
| Benefícios | Pacote de benefícios | BenefitsTab |
| Aprovadores | Fluxo de aprovação | - |

#### FASE 7: Configuração SSO/WorkOS (Opcional - Clientes Enterprise)

**Localização:** WorkOS Dashboard (https://dashboard.workos.com) - gerenciado pelo Time WeDo

**Funcionalidades:**
- Criar Organization para o cliente no WorkOS
- Configurar conexão SAML/OIDC
- Gerenciar Directory Sync (SCIM)
- Visualizar grupos sincronizados
- Mapear grupos para roles (via backend Rails)
- Auditoria de logins

> **Nota:** O cliente não tem acesso direto ao WorkOS Dashboard. O time WeDo configura SSO/SCIM e fornece as credenciais (ACS URL, Entity ID, SCIM Endpoint) para o cliente configurar no IdP dele (Azure AD, Okta).

---

### 1.6.6 Fluxos Técnicos Detalhados

#### FLUXO A: Cliente SEM WorkOS (Starter/Professional)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO SEM WORKOS (AUTENTICAÇÃO NATIVA)                   │
└─────────────────────────────────────────────────────────────────────────────┘

FASE 1: CRIAÇÃO DO CLIENTE (Time WedoTalent via HubSpot)
════════════════════════════════════════════════════════
                                                    
    [Time WedoTalent]                              
          │                                          
          ▼                                          
    HubSpot CRM                                  
          │                                          
          │ Cria novo Contato + Company                     
          ▼                                          
    ┌─────────────┐                                  
    │ Formulário  │                                  
    │ - Nome      │                                  
    │ - CNPJ      │                                  
    │ - Email     │                                  
    │ - Plano     │                                  
    └──────┬──────┘                                  
           │                                          
           ▼                                          
    POST /api/v1/clients                             
           │                                          
           ├──► 1. Criar ClientAccount               
           │                                          
           ├──► 2. Criar CompanyWorkOSConfig         
           │       (sso_enabled=false)               
           │                                          
           ├──► 3. Provisionar WorkOS Org            
           │       (fica "dormindo")                 
           │                                          
           ├──► 4. Clonar templates de email         
           │                                          
           ├──► 5. Sync HubSpot (Company + Deal)     
           │                                          
           └──► 6. Enviar email boas-vindas          
                   │                                  
                   ▼                                  
           [Email enviado para cliente]              
```

**Arquivos envolvidos (Fluxo SEM WorkOS):**

| Componente | Arquivo/Ferramenta | Função |
|------------|-------------------|--------|
| Gestão de Clientes | HubSpot CRM | Criar/editar clientes |
| Backend - Clientes | `wedotalent-backend/app/controllers/api/v1/clients_controller.rb` | CRUD de clientes (API)
| Backend - Usuários | `wedotalent-backend/app/controllers/api/v1/client_users_controller.rb` | CRUD de usuários |
| Backend - Convites | `wedotalent-backend/app/controllers/api/v1/invitations_controller.rb` | Validar/aceitar |
| Frontend - Aceitar | `plataforma-lia/src/app/aceitar-convite/page.tsx` | Página de aceite |
| Frontend - Equipe | `plataforma-lia/src/components/settings/user-management.tsx` | Gestão de equipe |
| Email | `wedotalent-backend/app/services/email_service.rb` | Envio de emails |
| HubSpot | `wedotalent-backend/app/services/hubspot_service.rb` | Sync CRM |

#### FLUXO B: Cliente COM WorkOS (Enterprise + SSO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO COM WORKOS (SSO ENTERPRISE)                        │
└─────────────────────────────────────────────────────────────────────────────┘

FASE 2: CONFIGURAÇÃO SSO (Admin do Cliente solicita)
═════════════════════════════════════════════════════

    [Time WedoTalent]
          │
          ▼
    WorkOS Dashboard (https://dashboard.workos.com)
          │
          ├──► Organizations
          │    - Criar Organization para cliente
          │    - Copiar org_id
          │
          ├──► SSO Connections
          │    - Configurar SAML/OIDC
          │    - Gerar ACS URL e Entity ID
          │    - Enviar ao cliente para configurar no IdP
          │
          └──► Ativação SSO
               │
               ▼
          PUT /api/v1/workos/config/{company_id}
               │
               ├──► Atualizar sso_enabled = true
               │
               └──► Configurar connection_id do WorkOS


FASE 3: LOGIN VIA SSO
═════════════════════

    [Usuário do cliente enterprise]
          │
          ▼
    /login (Plataforma WedoTalent)
          │
          │ Clica "Login com SSO" ou insere email corporativo
          ▼
    ┌─────────────────────────────────┐
    │ Frontend detecta SSO habilitado │
    │ e redireciona para:             │
    └──────────────┬──────────────────┘
                   │
                   ▼
          GET /api/auth/workos/sso?organization=xxx
          (Next.js API Route)
                   │
                   ├──► Gera authorization URL via WorkOS SDK
                   │    workos.sso.getAuthorizationUrl()
                   │
                   └──► Redireciona para IdP
                        │
                        ▼
               [IdP do Cliente]
               (Azure AD / Okta / Google)
                        │
                        │ Usuário autentica no IdP
                        ▼
               Callback do IdP
                        │
                        ▼
          GET /api/auth/workos/callback?code=xxx
          (Next.js API Route)
                        │
                        ├──► workos.sso.getProfileAndToken(code)
                        │
                        ├──► Cria sessão (cookie workos_session)
                        │
                        ├──► POST /api/v1/auth/workos/sync-user
                        │    (sincroniza usuário no backend)
                        │
                        └──► Redireciona para /login/welcome?sso=true
                             │
                             ▼
                     [Dashboard do cliente]

NOTA: O fluxo SSO é gerenciado pelo Next.js frontend via WorkOS SDK.
O backend só recebe a requisição de sync-user para manter o banco atualizado.


FASE 4: DIRECTORY SYNC (SCIM) - Opcional
════════════════════════════════════════

    [IdP do Cliente]
          │
          │ WorkOS envia webhooks para cada evento
          ▼
    
    Evento: Usuário criado/atualizado/deletado
    ──────────────────────────────────────────
    POST /api/v1/workos/webhooks/scim
          │
          └──► Cria/atualiza usuário automaticamente
               Associa com empresa via directory_id
    
    Evento: Grupo criado/atualizado/deletado
    ────────────────────────────────────────
    POST /api/v1/workos/webhooks/scim
          │
          └──► Atualiza tabela: workos_groups
    
    Evento: Membro adicionado/removido de grupo
    ───────────────────────────────────────────
    POST /api/v1/workos/webhooks/scim
          │
          └──► Atualiza tabela: workos_group_memberships
               (vincula user_id da tabela users ao grupo)
    
    TABELAS AFETADAS:
    - workos_groups (grupos do IdP)
    - workos_group_memberships (usuário ↔ grupo)
    - workos_group_role_mappings (grupo → role)
    - sso_audit_logs (auditoria)
```

**Arquivos envolvidos (Fluxo COM WorkOS):**

| Componente | Arquivo/Ferramenta | Função |
|------------|-------------------|--------|
| Gestão SSO/SCIM | WorkOS Dashboard | Criar org, configurar SSO/SCIM |
| WorkOS Provisioning | `wedotalent-backend/app/services/workos_provisioning_service.rb` | Criar org no WorkOS |
| WorkOS API | `wedotalent-backend/app/controllers/api/v1/workos_controller.rb` | Endpoints SSO/SCIM |
| WorkOS Models | `wedotalent-backend/app/models/workos/` | ActiveRecord models |
| SCIM Webhook | `wedotalent-backend/app/controllers/api/v1/workos_controller.rb` | Receber eventos SCIM |
| Audit Logs | Tabela `sso_audit_logs` | Compliance SOC2/BCB498 |

#### Comparativo: SEM WorkOS vs COM WorkOS

| Aspecto | SEM WorkOS | COM WorkOS | Status |
|---------|------------|------------|--------|
| **Autenticação** | Email/senha nativo | SAML/OIDC via IdP | ✅ Completo |
| **Gestão de usuários** | Manual no WedoTalent | Manual + Sync grupos | ✅ Completo |
| **Convites** | Token por email | Token por email | ✅ Completo |
| **Grupos/Roles** | Manual no WedoTalent | Sync do IdP | ✅ Completo |
| **MFA** | Não implementado | Via IdP | ✅ Via IdP |
| **Audit logs** | Logs básicos | SSO Audit completo | ✅ Completo |
| **Compliance** | Básico | SOC2/BCB498 ready | ✅ Completo |
| **Planos** | Starter, Professional | Enterprise | N/A |

---

### 1.6.7 Configuração SSO/SCIM no IdP do Cliente

> **IMPORTANTE:** Esta seção contém **templates de instruções para CLIENTES** configurarem SSO nos IdPs **deles**. A WeDo Talent **não precisa** criar apps SAML no Azure AD, Okta ou outros IdPs. O WorkOS é o middleware que abstrai essas conexões.
>
> **Fluxo correto:**
> 1. Cliente solicita SSO
> 2. Time WeDo cria Organization no WorkOS Dashboard
> 3. WorkOS gera URLs (ACS URL, Entity ID) específicas para o cliente
> 4. Time WeDo envia estas instruções ao cliente com as URLs preenchidas
> 5. Cliente configura no IdP dele (Azure AD, Okta, etc.)

#### 1.6.7.1 Template: Configuração no Microsoft Azure AD / Entra ID

> **Para o cliente:** Siga estes passos no SEU Azure Portal para conectar ao LIA via SSO.

##### Passo 1: Criar Aplicação Empresarial

1. Acesse o [Portal do Azure](https://portal.azure.com)
2. Navegue para **Azure Active Directory** → **Aplicativos empresariais**
3. Clique em **+ Novo aplicativo**
4. Selecione **Criar seu próprio aplicativo**
5. Digite o nome: `LIA - Plataforma de Recrutamento`
6. Selecione **Integrar qualquer outro aplicativo que você não encontrar na galeria**
7. Clique em **Criar**

##### Passo 2: Configurar SSO SAML

1. Na página do aplicativo, clique em **Logon único** no menu lateral
2. Selecione **SAML** como método de logon
3. Na seção **Configuração Básica de SAML**, clique em **Editar**
4. Preencha os campos:

| Campo | Valor |
|-------|-------|
| **Identificador (ID da Entidade)** | `https://api.workos.com/sso/saml/metadata/{org_id}` |
| **URL de Resposta (URL ACS)** | `https://api.workos.com/sso/saml/acs/{org_id}` |
| **URL de Logon** | (deixe em branco) |

5. Clique em **Salvar**

##### Passo 3: Baixar Certificado e Metadados

1. Na seção **Certificados SAML**, baixe:
   - **Certificado (Base64)** - clique em Download
   - **XML de Metadados de Federação** - clique em Download

2. Anote os seguintes valores da seção **Configurar LIA**:
   - URL de Logon: `_______________________`
   - Identificador do Azure AD: `_______________________`
   - URL de Logoff: `_______________________`

##### Passo 4: Atribuir Usuários e Grupos

1. Clique em **Usuários e grupos** no menu lateral
2. Clique em **+ Adicionar usuário/grupo**
3. Selecione os grupos ou usuários que terão acesso à LIA
4. Clique em **Atribuir**

##### Passo 5: Configurar SCIM (Opcional - Recomendado)

1. Clique em **Provisionamento** no menu lateral
2. Clique em **Introdução**
3. Selecione **Modo de provisionamento**: Automático
4. Na seção **Credenciais de Administrador**:

| Campo | Valor |
|-------|-------|
| **URL do Locatário** | `https://api.workos.com/scim/v2/{directory_id}` |
| **Token Secreto** | (fornecido pela LIA - veja seção 1.6.8.4) |

5. Clique em **Testar Conexão** para verificar
6. Clique em **Salvar**
7. Na seção **Mapeamentos**, configure:
   - Provisionar Grupos do Azure AD → Ativado
   - Provisionar Usuários do Azure AD → Ativado
8. Defina o **Status de Provisionamento** como **Ativado**

#### 1.6.7.2 Template: Configuração no Okta

> **Para o cliente:** Siga estes passos no SEU Okta Admin Console para conectar ao LIA via SSO.

##### Passo 1: Adicionar Aplicação

1. Acesse o [Okta Admin Console](https://admin.okta.com)
2. Navegue para **Applications** → **Applications**
3. Clique em **Create App Integration**
4. Selecione:
   - Sign-in method: **SAML 2.0**
5. Clique em **Next**

##### Passo 2: Configurar SAML

1. Na tela **General Settings**:
   - App name: `LIA - Plataforma de Recrutamento`
   - App logo: (opcional)
2. Clique em **Next**

3. Na tela **Configure SAML**:

| Campo | Valor |
|-------|-------|
| **Single sign-on URL** | `https://api.workos.com/sso/saml/acs/{org_id}` |
| **Audience URI (SP Entity ID)** | `https://api.workos.com/sso/saml/metadata/{org_id}` |
| **Name ID format** | EmailAddress |
| **Application username** | Email |

4. Em **Attribute Statements**, adicione:

| Name | Value |
|------|-------|
| `email` | `user.email` |
| `firstName` | `user.firstName` |
| `lastName` | `user.lastName` |

5. Clique em **Next** e depois em **Finish**

##### Passo 3: Obter Metadados

1. Na página da aplicação, clique na aba **Sign On**
2. Clique em **View SAML setup instructions** ou **Identity Provider metadata**
3. Copie ou baixe:
   - Identity Provider Single Sign-On URL
   - Identity Provider Issuer
   - X.509 Certificate

##### Passo 4: Atribuir Usuários

1. Clique na aba **Assignments**
2. Clique em **Assign** → **Assign to Groups**
3. Selecione os grupos que terão acesso
4. Clique em **Save and Go Back**

##### Passo 5: Configurar SCIM (Opcional - Recomendado)

1. Na aba **General**, clique em **Edit**
2. Habilite **Enable SCIM provisioning**
3. Clique em **Save**
4. Vá para a aba **Provisioning** → **Integration**
5. Clique em **Configure API Integration**
6. Marque **Enable API integration**
7. Preencha:

| Campo | Valor |
|-------|-------|
| **SCIM connector base URL** | `https://api.workos.com/scim/v2/{directory_id}` |
| **Bearer Token** | (fornecido pela LIA - veja seção 1.6.8.4) |

8. Clique em **Test API Credentials**
9. Clique em **Save**
10. Configure as opções de provisionamento:
    - Create Users ✅
    - Update User Attributes ✅
    - Deactivate Users ✅
    - Sync Groups ✅

---

### 1.6.8 Gestão SSO/SCIM via WorkOS Dashboard

> **Arquitetura:** A plataforma LIA **não possui área admin frontend**. Toda a gestão de SSO/SCIM é realizada via:
> - **WorkOS Dashboard**: Configuração técnica de SSO/SCIM
> - **HubSpot CRM**: Gestão de clientes e tickets de onboarding
> - **Backend Rails**: APIs e serviços de integração

#### 1.6.8.1 Fluxo de Habilitação SSO (Time WeDo)

Quando um cliente enterprise solicita SSO, o time WeDo executa:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE HABILITAÇÃO SSO/SCIM                            │
└─────────────────────────────────────────────────────────────────────────────┘

   Cliente          HubSpot               WorkOS              Backend Rails
      │                │                     │                      │
      │  1. Solicita   │                     │                      │
      │     SSO        │                     │                      │
      │────────────────▶                     │                      │
      │                │                     │                      │
      │                │ 2. Ticket criado    │                      │
      │                │    (Pipeline SSO)   │                      │
      │                │                     │                      │
      │                │                     │  3. Criar Organization│
      │                │                     │◀─────────────────────│
      │                │                     │                      │
      │                │                     │  4. Retornar org_id, │
      │                │                     │     ACS URL, Entity  │
      │                │                     │─────────────────────▶│
      │                │                     │                      │
      │  5. Enviar dados para configurar no IdP                     │
      │◀────────────────────────────────────────────────────────────│
      │                │                     │                      │
      │  6. Cliente configura no Azure/Okta (Seção 1.6.7)           │
      │                │                     │                      │
      │  7. Teste de login                   │                      │
      │────────────────────────────────────▶│                      │
      │                │                     │  8. Validar e ativar │
      │                │                     │─────────────────────▶│
      │                │                     │                      │
      │                │ 9. Ticket fechado   │                      │
      │                │    (SSO Ativo)      │                      │
```

#### 1.6.8.2 Criar Organization no WorkOS (Time WeDo)

1. Acesse o **WorkOS Dashboard**: https://dashboard.workos.com
2. Navegue para **Organizations** → **Create Organization**
3. Preencha:
   - **Name**: Nome do cliente
   - **Domains**: Domínio de email corporativo (ex: `suaempresa.com.br`)
4. Copie o **Organization ID** gerado (`org_xxx`)
5. Configure a **SSO Connection**:
   - Selecione o tipo de IdP (SAML 2.0 ou OIDC)
   - Copie a **ACS URL** e **Entity ID**

#### 1.6.8.3 Fornecer Dados ao Cliente

Envie ao cliente (via HubSpot ou email):

| Informação | Descrição | Exemplo |
|------------|-----------|---------|
| **ACS URL** | URL para configurar no IdP | `https://api.workos.com/sso/saml/acs/xxx` |
| **Entity ID** | Identificador SAML | `https://api.workos.com/sso/saml/entity/xxx` |
| **Tipo** | Protocolo suportado | SAML 2.0 ou OIDC |

O cliente então configura no IdP dele (Azure AD ou Okta) conforme Seção 1.6.7.

#### 1.6.8.4 Habilitar SCIM (Directory Sync)

1. No WorkOS Dashboard, acesse a **Organization** do cliente
2. Vá para **Directory Sync** → **Create Directory**
3. Selecione o tipo de diretório (Azure AD, Okta, Google)
4. Copie e envie ao cliente:
   - **SCIM Endpoint URL**
   - **Bearer Token**
5. O cliente configura esses valores no IdP dele

#### 1.6.8.5 Testar a Configuração

**Teste de SSO (Cliente executa):**

1. Abrir janela anônima/privada no navegador
2. Acessar a página de login da LIA
3. Clicar em **Entrar com SSO** ou **Login Corporativo**
4. Digitar email corporativo
5. Ser redirecionado para o IdP (Azure/Okta)
6. Fazer login com credenciais corporativas
7. Ser redirecionado de volta para a LIA, autenticado

**Teste de SCIM (Time WeDo verifica):**

1. No WorkOS Dashboard, acessar **Directory Sync**
2. Verificar se os usuários estão sincronizando
3. Confirmar status **Active** no diretório

---

### 1.6.9 Mapeamento de Grupos

#### 1.6.9.1 O que é Mapeamento de Grupos?

O mapeamento de grupos permite associar grupos do diretório corporativo do cliente a roles (papéis) na plataforma LIA. Quando um usuário é adicionado a um grupo no IdP, ele automaticamente recebe as permissões correspondentes na LIA.

#### 1.6.9.2 Roles Disponíveis na LIA

| Role | Permissões |
|------|------------|
| **Admin** | Acesso total à plataforma, incluindo configurações e gestão de usuários |
| **Recrutador** | Criar e gerenciar vagas, buscar candidatos, realizar triagens |
| **Visualizador** | Apenas visualizar informações, sem edição |

#### 1.6.9.3 Configurar Mapeamento (Backend Rails)

O mapeamento é configurado via API ou banco de dados pelo time WeDo:

```ruby
# wedotalent-backend/app/services/workos_provisioning_service.rb

def configure_group_mapping(organization_id, mappings)
  # mappings = [
  #   { group_name: 'RH-Gestores', role: 'admin' },
  #   { group_name: 'RH-Recrutadores', role: 'recruiter' },
  #   { group_name: 'RH-Analistas', role: 'viewer' }
  # ]
  
  mappings.each do |mapping|
    GroupRoleMapping.create!(
      organization_id: organization_id,
      group_name: mapping[:group_name],
      role: mapping[:role]
    )
  end
end
```

#### 1.6.9.4 Exemplos de Mapeamento

| Grupo no IdP | Role na LIA | Resultado |
|--------------|-------------|-----------|
| `RH-Gestores` | Admin | Gestores de RH têm acesso administrativo |
| `RH-Recrutadores` | Recrutador | Recrutadores podem gerenciar processos |
| `RH-Analistas` | Visualizador | Analistas podem apenas visualizar |
| `TI-Suporte` | Admin | TI pode administrar a plataforma |

#### 1.6.9.5 Boas Práticas

- Use grupos existentes do diretório do cliente quando possível
- Crie grupos específicos para a LIA se necessário (ex: `LIA-Admins`)
- Documente os mapeamentos no HubSpot (notas do cliente)
- Revise os mapeamentos periodicamente
- Evite atribuir role Admin a grupos muito amplos

---

### 1.6.10 WorkOS Dashboard (Gestão Centralizada)

#### 1.6.10.1 Visão Geral

O **WorkOS Dashboard** é o ponto central de gestão de SSO/SCIM. O time WeDo utiliza este dashboard para:

- Criar e gerenciar Organizations (clientes)
- Configurar SSO Connections
- Gerenciar Directory Sync (SCIM)
- Visualizar logs de auditoria
- Configurar Log Streaming para SIEM

> **Nota:** Clientes não têm acesso direto ao WorkOS Dashboard. Toda gestão é feita pelo time WeDo.

#### 1.6.10.2 URLs do WorkOS Dashboard

| Funcionalidade | URL |
|----------------|-----|
| **Dashboard Principal** | https://dashboard.workos.com |
| **Gestão de Usuários** | https://dashboard.workos.com/users |
| **Logs de Auditoria** | https://dashboard.workos.com/events |
| **Log Streams (SIEM)** | https://dashboard.workos.com/log-streams |

#### 1.6.10.3 Gerenciamento de Usuários

No WorkOS Dashboard, o time WeDo pode:

- Visualizar todos os usuários provisionados via SCIM
- Ver detalhes de cada usuário (email, grupos, status)
- Filtrar usuários por diretório, status ou grupo
- Exportar lista de usuários
- Ver histórico de sincronização

**Acesso**: https://dashboard.workos.com/users

#### 1.6.10.4 Logs de Auditoria

O WorkOS Dashboard fornece logs detalhados de todos os eventos de autenticação:

| Tipo de Evento | Descrição |
|----------------|-----------|
| `sso.authentication.succeeded` | Login SSO bem-sucedido |
| `sso.authentication.failed` | Tentativa de login SSO falhou |
| `dsync.user.created` | Novo usuário criado via SCIM |
| `dsync.user.updated` | Usuário atualizado via SCIM |
| `dsync.user.deleted` | Usuário removido via SCIM |
| `dsync.group.created` | Novo grupo criado via SCIM |
| `dsync.group.updated` | Grupo atualizado via SCIM |
| `dsync.group.deleted` | Grupo removido via SCIM |

**Funcionalidades de auditoria:**

- ✅ Busca por usuário, tipo de evento ou período
- ✅ Filtros avançados por organização
- ✅ Exportação de logs em CSV/JSON
- ✅ Retenção de logs por período configurável

**Acesso**: https://dashboard.workos.com/events

#### 1.6.10.5 Log Streaming (SIEM)

O Log Streaming permite enviar eventos de autenticação em tempo real para seu SIEM:

**Integrações suportadas:**

| SIEM/Destino | Status |
|--------------|--------|
| Datadog | ✅ Suportado |
| Splunk | ✅ Suportado |
| AWS S3 | ✅ Suportado |
| Azure Blob Storage | ✅ Suportado |
| Google Cloud Storage | ✅ Suportado |
| Webhook personalizado | ✅ Suportado |

**Para configurar Log Streaming:**

1. Acesse https://dashboard.workos.com/log-streams
2. Clique em **"Create Log Stream"**
3. Selecione o destino (Datadog, Splunk, S3, etc.)
4. Configure as credenciais do destino
5. Selecione os tipos de eventos a serem enviados
6. Clique em **"Create"**

---

### 1.6.11 Integração HubSpot CRM

#### 1.6.11.1 Visão Geral

A integração com HubSpot sincroniza automaticamente dados de clientes para o CRM, permitindo acompanhamento comercial e de onboarding.

#### 1.6.11.2 O que é Sincronizado

| Objeto HubSpot | Dados Sincronizados |
|----------------|---------------------|
| **Company** | Nome, CNPJ, tamanho, plano, status, métricas de onboarding |
| **Contact** | Admin principal (nome, email, telefone) |
| **Deal** | Pipeline de onboarding, valor do contrato, estágio |

#### 1.6.11.3 Comportamento da Sincronização

- **Automático**: Sync acontece na criação do cliente
- **Deduplicação**: Sistema busca registros existentes antes de criar novos
- **Atualização**: Registros existentes são atualizados, não duplicados

#### 1.6.11.4 Endpoints de API

```
GET  /api/v1/clients/{id}/hubspot/status     # Status da sincronização
POST /api/v1/clients/{id}/hubspot/sync       # Sincronização manual
PUT  /api/v1/clients/{id}/hubspot/onboarding # Atualizar status onboarding
```

#### 1.6.11.5 Configuração

**Requisito:** Secret `HUBSPOT_ACCESS_TOKEN` configurado (Private App Token do HubSpot)

**Propriedades customizadas necessárias no HubSpot:**
- Veja seção 1.6.4.3 para lista completa

---

### 1.6.12 Modelos de Dados e Endpoints

#### 1.6.12.1 Modelos de Dados (ActiveRecord)

##### ClientAccount
```ruby
# app/models/client_account.rb
class ClientAccount < ApplicationRecord
  # Atributos:
  # - id: uuid, primary key
  # - name: string
  # - trade_name: string
  # - cnpj: string
  # - primary_email: string
  # - status: enum (pending_setup, trial, active, suspended, churned)
  # - plan_id: string
  # - user_limit: integer
  # - job_limit: integer
  # - ai_credits_monthly: integer
  # - welcome_email_sent: datetime, nullable
  # - workos_organization_created: datetime, nullable
  # - sso_configured: datetime, nullable

  has_many :client_users
  has_one :company_workos_config
end
```

##### ClientUser
```ruby
# app/models/client_user.rb
class ClientUser < ApplicationRecord
  # Atributos:
  # - id: uuid, primary key
  # - company_id: uuid (FK → ClientAccount)
  # - email: string
  # - name: string
  # - role: enum (admin, manager, recruiter, viewer)
  # - status: enum (pending, active, inactive)
  # - invitation_token: string, nullable
  # - invitation_expires_at: datetime, nullable
  # - is_scim_managed: boolean

  belongs_to :client_account, foreign_key: :company_id
end
```

##### CompanyWorkOSConfig
```ruby
# app/models/workos/company_workos_config.rb
class Workos::CompanyWorkosConfig < ApplicationRecord
  # Atributos:
  # - id: uuid, primary key
  # - company_id: string (FK → ClientAccount, unique)
  # - workos_organization_id: string
  # - workos_directory_id: string, nullable
  # - sso_connection_id: string, nullable
  # - sso_enabled: boolean, default: false
  # - scim_enabled: boolean, default: false
  # - sso_domains: string[] (array)
  # - created_at: datetime
  # - updated_at: datetime

  belongs_to :client_account, foreign_key: :company_id
end
```

##### WorkOSGroup
```ruby
# app/models/workos/workos_group.rb
class Workos::WorkosGroup < ApplicationRecord
  # Atributos:
  # - id: uuid, primary key
  # - workos_id: string (unique, indexed)
  # - directory_id: string, nullable
  # - name: string
  # - raw_attributes: jsonb
  # - is_active: boolean, default: true
  # - created_at: datetime
  # - updated_at: datetime

  has_many :workos_group_memberships
  has_many :workos_group_role_mappings
end
```

##### SSOAuditLog
```ruby
# app/models/workos/sso_audit_log.rb
class Workos::SsoAuditLog < ApplicationRecord
  # Atributos:
  # - id: uuid, primary key
  # - company_id: string (indexed)
  # - event_type: string (indexed)
  # - actor_id: string, nullable (indexed)
  # - actor_email: string, nullable
  # - target_id: string, nullable (indexed)
  # - target_email: string, nullable
  # - source_ip: string, nullable
  # - user_agent: text, nullable
  # - workos_event_id: string, nullable (indexed)
  # - payload: jsonb
  # - created_at: datetime (indexed)
end
```

#### 1.6.12.2 Endpoints da API

##### Gestão de Clientes (via HubSpot + Backend API)
```
GET    /api/v1/clients                    # Listar clientes
POST   /api/v1/clients                    # Criar cliente
GET    /api/v1/clients/{id}               # Detalhes do cliente
PUT    /api/v1/clients/{id}               # Atualizar cliente
GET    /api/v1/clients/dashboard-summary  # KPIs e métricas
```

##### Gestão de Usuários do Cliente
```
GET    /api/v1/clients/{id}/users              # Listar usuários
POST   /api/v1/clients/{id}/users              # Criar/convidar usuário
GET    /api/v1/clients/{id}/users/{userId}     # Detalhes do usuário
PUT    /api/v1/clients/{id}/users/{userId}     # Atualizar usuário
DELETE /api/v1/clients/{id}/users/{userId}     # Remover usuário
POST   /api/v1/clients/{id}/users/{userId}/resend-invite  # Reenviar convite
```

##### Convites
```
GET    /api/v1/invitations/validate?token=xxx  # Validar token
POST   /api/v1/invitations/accept              # Aceitar convite
```

##### SSO (Frontend - Next.js)
```
GET  /api/auth/workos/sso                   # Inicia SSO (redireciona para IdP)
GET  /api/auth/workos/callback              # Callback do WorkOS
GET  /api/auth/workos/session               # Obter sessão atual
POST /api/auth/workos/refresh               # Refresh da sessão
```

##### WorkOS (Backend)
```
POST /api/v1/auth/workos/sync-user          # Sincroniza usuário após SSO
POST /api/v1/workos/webhooks/scim           # SCIM webhooks (8 eventos)
GET  /api/v1/workos/admin/status            # Status da integração
GET  /api/v1/workos/admin/realtime-metrics  # Métricas em tempo real
GET  /api/v1/workos/admin/groups            # Listar grupos
POST /api/v1/workos/admin/groups/{id}/role-mapping  # Mapear grupo → role
GET  /api/v1/workos/admin/audit-logs        # Logs de auditoria
GET  /api/v1/workos/admin/users             # Listar usuários SCIM
GET  /api/v1/auth/check-sso-domain          # Detectar SSO por domínio
```

---

### 1.6.13 Arquitetura de Segurança

#### 1.6.13.1 HMAC Validation (SCIM Webhooks)

- Dependência `verify_scim_webhook` aplicada a todos os endpoints SCIM
- Valida header `WorkOS-Signature` usando HMAC SHA256
- Tolerância de 180 segundos para timestamp
- Fallback em desenvolvimento (logs warning, permite requisição)
- **Configuração necessária:** Definir `WORKOS_WEBHOOK_SECRET` em produção

#### 1.6.13.2 Session-Based Auth (Proxy)

- Proxy `/api/backend-proxy/clients/[id]/users` lê cookie `workos_session`
- Extrai `organizationId`, `id`, `role` do perfil WorkOS
- Headers `X-Company-ID`, `X-User-ID`, `X-User-Role` preenchidos dinamicamente
- Fallback em desenvolvimento com console warning

#### 1.6.13.3 SSO Domain Detection

- Endpoint público `GET /api/v1/auth/check-sso-domain?email=user@domain.com`
- Verifica array `sso_domains` em `CompanyWorkOSConfig`
- Fallback: verifica domínio do email admin em `client_accounts`
- Login page mostra botão SSO automaticamente quando detectado

---

### 1.6.14 Resolução de Problemas

#### 1.6.14.1 Problemas de Login SSO

##### Problema: "Erro de configuração SAML"

**Causa provável**: URLs ou certificados incorretos na configuração.

**Solução**:
1. Verifique se a ACS URL no IdP está correta
2. Verifique se o Entity ID no IdP está correto
3. Confirme que o certificado não expirou
4. Tente baixar novamente os metadados e reconfigurar

##### Problema: "Usuário não autorizado"

**Causa provável**: Usuário não está atribuído à aplicação no IdP.

**Solução**:
1. No seu IdP, verifique se o usuário está atribuído à aplicação LIA
2. Se usando grupos, confirme que o usuário pertence a um grupo atribuído
3. Aguarde alguns minutos e tente novamente

##### Problema: "Loop de redirecionamento"

**Causa provável**: Configuração de sessão ou cookies.

**Solução**:
1. Limpe cookies e cache do navegador
2. Tente em uma janela anônima/privada
3. Verifique se há conflito com outras aplicações SSO

#### 1.6.14.2 Problemas de SCIM

##### Problema: "Usuários não estão sincronizando"

**Causa provável**: Token SCIM inválido ou expirado.

**Solução**:
1. Verifique se o Bearer Token está correto no IdP
2. Teste a conexão SCIM no IdP
3. Verifique logs de provisionamento no IdP
4. Entre em contato com suporte LIA para gerar novo token

##### Problema: "Grupos não aparecem na LIA"

**Causa provável**: SCIM de grupos não está habilitado.

**Solução**:
1. No IdP, verifique se "Push Groups" ou "Sync Groups" está ativado
2. Confirme que os grupos estão atribuídos à aplicação
3. Aguarde a próxima sincronização (pode levar até 40 minutos)
4. Force uma sincronização manual no IdP se disponível

#### 1.6.14.3 Contato de Suporte

Se os problemas persistirem, entre em contato:

- **Email**: suporte@wedotalent.com
- **Portal**: https://suporte.wedotalent.com

Ao contatar o suporte, tenha em mãos:
- Nome da empresa e domínio
- IdP utilizado (Azure AD, Okta, OneLogin, PingIdentity)
- Descrição detalhada do problema
- Screenshots de erros (se aplicável)
- Logs de auditoria relevantes

---

### 1.6.15 Compliance e Segurança

#### 1.6.15.1 Conformidade Regulatória

A integração SSO/SCIM da LIA foi projetada para atender aos mais rigorosos padrões de segurança e compliance do setor financeiro:

##### BCB 498/2025 (Resolução do Banco Central)

| Requisito | Como o SSO/SCIM atende |
|-----------|------------------------|
| **Controle de acesso** | Autenticação centralizada com políticas corporativas |
| **Gestão de identidades** | Provisionamento automático via SCIM |
| **Trilha de auditoria** | Logs completos de login, provisionamento e alterações |
| **Segregação de funções** | Mapeamento de grupos para roles específicos |
| **Revogação de acesso** | Desprovisionamento automático de usuários |

##### SOC 2 Type II

| Critério | Implementação |
|----------|---------------|
| **Segurança** | Criptografia TLS 1.3, tokens com expiração |
| **Disponibilidade** | Infraestrutura redundante WorkOS |
| **Confidencialidade** | Dados de autenticação não armazenados |
| **Integridade do processamento** | Validação de assinaturas SAML |
| **Privacidade** | Minimização de dados, consentimento |

##### LGPD (Lei Geral de Proteção de Dados)

| Princípio | Como atendemos |
|-----------|----------------|
| **Finalidade** | Dados usados apenas para autenticação e autorização |
| **Adequação** | Coleta mínima de dados necessários |
| **Necessidade** | Apenas email, nome e grupos são sincronizados |
| **Segurança** | Criptografia em trânsito e em repouso |
| **Transparência** | Logs de auditoria acessíveis |
| **Responsabilização** | Relatórios de compliance disponíveis |

#### 1.6.15.2 Recursos de Segurança

##### Autenticação Forte

- ✅ Suporte a MFA (Multi-Factor Authentication) via IdP
- ✅ Políticas de senha gerenciadas centralmente
- ✅ Bloqueio após tentativas falhas (configurável no IdP)
- ✅ Sessões com expiração configurável

##### Proteção de Dados

- ✅ Criptografia TLS 1.3 em todas as comunicações
- ✅ Tokens com expiração e rotação automática
- ✅ Nenhuma senha armazenada na LIA
- ✅ Certificados SAML validados

##### Monitoramento

- ✅ Logs de todos os eventos de autenticação
- ✅ Alertas de atividades suspeitas
- ✅ Relatórios de acesso por período
- ✅ Dashboard de status em tempo real

#### 1.6.15.3 Certificações e Parceiros

A integração SSO/SCIM da LIA é fornecida em parceria com **WorkOS**, que possui:

| Certificação | Status |
|--------------|--------|
| SOC 2 Type II | ✅ Certificado |
| ISO 27001 | ✅ Certificado |
| GDPR Compliant | ✅ Certificado |
| HIPAA Eligible | ✅ Disponível |

#### 1.6.15.4 Relatórios de Compliance

Para auditorias e relatórios de compliance:

1. Acesse o WorkOS Dashboard em https://dashboard.workos.com/events
2. Use os filtros para selecionar o período desejado
3. Clique em **Export** para baixar logs em formato CSV/JSON

Os relatórios incluem:
- Data/hora do evento
- Tipo de evento (login, provisioning, etc.)
- Usuário afetado
- IP de origem
- User Agent
- Resultado (sucesso/falha)

#### 1.6.15.5 Melhores Práticas de Segurança

1. **Habilite MFA no IdP** para todos os usuários
2. **Revise acessos periodicamente** (recomendado: mensal)
3. **Monitore logs de auditoria** regularmente
4. **Configure alertas** para eventos críticos
5. **Mantenha certificados atualizados** (antes da expiração)
6. **Documente os mapeamentos** de grupos para roles
7. **Teste o desprovisionamento** com um usuário de teste
8. **Limite roles Admin** ao mínimo necessário

---

### 1.6.16 Templates de Email

#### 1.6.16.1 Template: Boas-vindas ao Cliente

**Gatilho:** Criação de novo cliente (via HubSpot CRM → Webhook → Rails API)

| Propriedade | Valor |
|-------------|-------|
| **Nome** | Boas-vindas ao Cliente |
| **Assunto** | Bem-vindo à WEDOTALENT - Configure seu Acesso SSO |
| **Categoria** | onboarding |
| **Canal** | email |

**Variáveis disponíveis:**

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `{{company_name}}` | Nome da empresa do cliente | Empresa ABC Ltda |
| `{{admin_name}}` | Nome do administrador principal | João Silva |
| `{{admin_portal_url}}` | URL do portal de login | https://app.wedotalent.com/login |
| `{{support_email}}` | Email de suporte | suporte@wedotalent.com |

#### 1.6.16.2 Template: Convite para WeDo Talent

**Gatilho:** Convite de usuário via `/configuracoes` → Aba "Equipe"

| Propriedade | Valor |
|-------------|-------|
| **Nome** | Convite para WeDo Talent |
| **Assunto** | Você foi convidado para a plataforma WeDo Talent |
| **Categoria** | invite |
| **Canal** | email |

**Variáveis disponíveis:**

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `{{user_name}}` | Nome do usuário convidado | Maria Souza |
| `{{company_name}}` | Nome da empresa | Empresa ABC Ltda |
| `{{inviter_name}}` | Nome de quem convidou | João Silva |
| `{{accept_url}}` | URL para aceitar convite | https://app.wedotalent.com/aceitar-convite?token=xxx |
| `{{role_name}}` | Papel atribuído | Recrutador |
| `{{expires_at}}` | Data de expiração | 19/01/2026 às 14:30 |

---

### 1.6.17 Mapa de URLs e Telas de UI

#### 1.6.17.1 Admin Layer (Ferramentas SaaS Externas)

> **Nota:** A plataforma LIA **não possui área admin frontend**. A gestão é feita via ferramentas SaaS:

| Função | Ferramenta | URL | Responsável |
|--------|------------|-----|-------------|
| Gestão de Clientes | HubSpot CRM | https://app.hubspot.com/contacts | Time WeDo |
| Onboarding de Clientes | HubSpot Tickets | https://app.hubspot.com/tickets | Time WeDo |
| Configuração SSO/SCIM | WorkOS Dashboard | https://dashboard.workos.com | Time WeDo |
| Billing e Subscriptions | Stripe Dashboard | https://dashboard.stripe.com | Time WeDo |
| Métricas SaaS | ProfitWell | https://app.profitwell.com | Time WeDo |

#### 1.6.17.2 Ambiente Plataforma (Cliente)

| URL | Tela | Descrição | Arquivo |
|-----|------|-----------|---------|
| `/login` | Login | Autenticação email/senha ou SSO | `plataforma-lia/src/app/login/page.tsx` |
| `/login/welcome` | Boas-vindas SSO | Tela pós-login SSO | `plataforma-lia/src/app/login/welcome/page.tsx` |
| `/aceitar-convite` | Aceitar Convite | Validação e aceite de convite | `plataforma-lia/src/app/aceitar-convite/page.tsx` |
| `/configuracoes` | Configurações | Hub de configurações da empresa | `plataforma-lia/src/app/configuracoes/page.tsx` |

#### 1.6.17.3 Componentes de UI Relevantes

| Componente | Localização | Função |
|------------|-------------|--------|
| `UserManagement` | `/configuracoes` → Aba "Equipe" | Convidar/gerenciar usuários |
| `CompanyTeamHub` | `/configuracoes` | Container das abas de configuração |
| `LoginPage` | `/login` | Autenticação email/senha ou SSO |

#### 1.6.17.4 Fluxo Visual SSO Enterprise

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO SSO ENTERPRISE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────┐
    │  /login  │──►   │   WorkOS     │──►   │ IdP Cliente  │──►   │ Callback │
    │          │      │   Redirect   │      │ (Azure/Okta) │      │          │
    │ Insere   │      │              │      │              │      │ /api/    │
    │ email    │      │ authorization│      │ Usuário      │      │ auth/    │
    │ corp.    │      │ URL gerada   │      │ autentica    │      │ workos/  │
    │          │      │              │      │              │      │ callback │
    └──────────┘      └──────────────┘      └──────────────┘      └────┬─────┘
         │                                                              │
         │                                                              │
         │                                                              ▼
         │                                                        ┌──────────┐
         │                                                        │ Sessão   │
         │                                                        │ criada   │
         │                                                        │ Cookie   │
         │                                                        │ workos_  │
         │                                                        │ session  │
         │                                                        └────┬─────┘
         │                                                              │
         │                                                              ▼
         │                                                        ┌──────────┐
         │                                                        │ /login/  │
         │                                                        │ welcome  │
         │                                                        │ ?sso=true│
         │                                                        └────┬─────┘
         │                                                              │
         ▼                                                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           PLATAFORMA WEDOTALENT                          │
    │                                                                          │
    │   Usuário autenticado com SSO pode acessar todas as funcionalidades     │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

### 1.6.18 Homologação Bancária

> **Contexto:** Este documento detalha como a integração WorkOS atende aos requisitos de homologação com bancos e instituições financeiras brasileiras.

#### 1.6.18.1 Resumo Executivo

A WeDo Talent está em processo de homologação com bancos e instituições financeiras brasileiras, que exigem:
- Compliance (SOX, ISO 27001, LGPD, BCB 498/2025, BCB 538/2025)
- SSO Enterprise com IdPs corporativos
- MFA obrigatório
- Provisionamento automático (SCIM)
- SOC 2 Type II

##### Solução Implementada - Modelo Híbrido

```
┌─────────────────────────────────────────────────────────────────┐
│                     WORKOS DASHBOARD (Primário)                  │
│  - Gestão completa de usuários SSO/SCIM                         │
│  - Audit logs detalhados com filtros avançados                  │
│  - Log Streaming (SIEM) para Datadog/Splunk/S3                  │
│  - Métricas de segurança e autenticação                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Deep Links
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WEDO TALENT ADMIN (Local)                    │
│  - Cards de status resumidos (contagens, status ativo)          │
│  - Mapeamento grupos→roles (lógica de negócio LIA)              │
│  - Backup de audit logs (7 anos para compliance)                │
│  - Links para navegação ao WorkOS Dashboard                      │
└─────────────────────────────────────────────────────────────────┘
```

##### Benefícios Alcançados
- **4 gaps críticos resolvidos:** SSO, MFA, SCIM, SOC 2 Type II
- **Economia:** 4-5 semanas vs 3-4 meses de desenvolvimento
- **Compliance:** SOC 2 Type II herdado do WorkOS
- **Manutenção:** Zero para IdPs (WorkOS mantém)

#### 1.6.18.2 Requisitos Regulatórios Bancários

##### Principais Resoluções (Brasil 2025)

| Resolução | Foco | Vigência |
|-----------|------|----------|
| **BCB 498/2025** | PSTIs - Provedores de Serviços de TI | Set/2025 |
| **BCB 538/2025** | 14 controles de cibersegurança | Dez/2025 |
| **CMN 5.274/2025** | Segurança cibernética expandida | 2025 |
| **CMN 4.893/2021** | Política de segurança cibernética | Jul/2021 |

##### Os 14 Controles Mandatórios (BCB 538)

| # | Controle | Status |
|---|----------|--------|
| 1 | Criptografia de dados em trânsito e repouso | ✅ |
| 2 | Certificados digitais distintos (prod/homol) | ✅ |
| 3 | Segregação de chaves privadas | ✅ |
| 4 | **Autenticação multifatorial (MFA) obrigatória** | ✅ WorkOS |
| 5 | Rastreabilidade completa com trilhas de auditoria | ✅ WorkOS |
| 6 | **Controle de acesso rigoroso e segregação de funções** | ✅ WorkOS |
| 7 | Testes de intrusão (pentest) anuais | 🟡 Planejado |
| 8 | Gestão do ciclo de vida de ativos | ✅ |
| 9 | Patch management regular | ✅ |
| 10 | Proteção de rede e segmentação | ✅ |
| 11 | Monitoramento 24/7 | 🟡 Planejado |
| 12 | Inteligência cibernética (Deep/Dark Web) | 🟡 Planejado |
| 13 | Retenção segura de logs | ✅ WorkOS + WeDo |
| 14 | Mecanismos de detecção de intrusões | 🟡 Planejado |

#### 1.6.18.3 Matriz de Cobertura

##### Autenticação e Controle de Acesso

| Requisito | WeDo (Antes) | WorkOS | Status |
|-----------|--------------|--------|--------|
| SSO/SAML com IdP corporativo | ❌ | ✅ $125/conexão | ✅ Implementado |
| MFA obrigatório | ❌ | ✅ AuthKit | ✅ Implementado |
| Provisionamento SCIM | ❌ | ✅ $125/dir | ✅ Implementado |
| Desprovisionamento automático | ❌ | ✅ SCIM | ✅ Implementado |
| Segregação de funções (SoD) | ⚠️ RBAC básico | ✅ FGA | ✅ Parcial |
| Admin Portal self-service | ❌ | ✅ Incluído | ✅ Implementado |

##### Trilha de Auditoria e Logs

| Requisito | WeDo | WorkOS | Status |
|-----------|------|--------|--------|
| Logs de autenticação | ✅ | ✅ | ✅ Coberto |
| Logs de acesso a dados | ✅ | ⚠️ | ✅ WeDo cobre |
| Logs de decisões IA | ✅ | ❌ | ✅ WeDo cobre |
| Retenção 5+ anos | ✅ 7 anos | ✅ 12 meses | ✅ Híbrido |
| Export SIEM | ❌ | ✅ $75/org | ✅ Via WorkOS |

##### Compliance e Certificações

| Requisito | WeDo | WorkOS | Status |
|-----------|------|--------|--------|
| SOC 2 Type II | ❌ | ✅ | ✅ Herdado |
| ISO 27001 | ⚠️ 177 controles | ⚠️ ~80% | 🟡 Parcial |
| LGPD | ✅ | ✅ DPA | ✅ Coberto |
| SOX 404 | ✅ | ❌ | ✅ WeDo cobre |
| NYC LL144 / EU AI Act | ✅ | ❌ | ✅ WeDo cobre |

#### 1.6.18.4 Custos WorkOS

##### Custos Mensais Estimados

| Cenário | SSO | SCIM | Audit | Total/mês |
|---------|-----|------|-------|-----------|
| 5 clientes | $625 | $625 | $400 | ~$1.650 |
| 10 clientes | $1.250 | $1.250 | $800 | ~$3.300 |
| 20 clientes | $2.000 | $2.000 | $1.600 | ~$5.600 |
| 50 clientes | $4.000 | $4.000 | $4.000 | ~$12.100 |

##### Descontos por Volume

| Faixa | Preço/conexão |
|-------|---------------|
| 1-15 | $125/mês |
| 16-30 | $100/mês |
| 31-50 | $80/mês |
| 51-100 | $65/mês |
| 100+ | Custom |

##### WorkOS vs Desenvolvimento Interno

| Item | WorkOS (10 clientes) | Interno |
|------|---------------------|---------|
| Custo inicial | $0 | $50-80k |
| Custo mensal | ~$3.300 | $5.000+ |
| Tempo | 4-5 semanas | 3-4 meses |
| SOC 2 Type II | Incluído | +$50k/ano |

#### 1.6.18.5 Gaps Não Cobertos pelo WorkOS

| Requisito | Solução | Custo Estimado | Status |
|-----------|---------|----------------|--------|
| Seguro Cibernético | Contratar apólice | R$ 50-200k/ano | ❌ Pendente |
| ISO 27001 certificado | Processo certificação | R$ 80-150k | 🟡 Planejado |
| Pentest anual | Empresa especializada | R$ 30-80k/ano | 🟡 Planejado |
| SOC 24/7 | MSSP ou ferramenta | R$ 15-50k/mês | 🟡 Planejado |
| IDS/IPS | Infraestrutura | Variável | 🟡 Infra |
| Canal de Denúncias | Desenvolver/contratar | R$ 5-20k | ❌ Pendente |

##### O que WeDo Talent JÁ cobre (sem WorkOS)

- ✅ Audit logs de negócio (ai_decision, financial, data_access)
- ✅ Compliance IA (NYC LL144, EU AI Act)
- ✅ LGPD Portal do Titular
- ✅ SOX 404 Controls
- ✅ Risk Register
- ✅ BCP/DRP
- ✅ 177 controles ISO 27001 pré-cadastrados

#### 1.6.18.6 Checklist de Validação para Homologação

##### Funcionalidade
- [x] SSO login funciona com Okta/Azure AD
- [x] MFA pode ser habilitado via AuthKit
- [x] SCIM webhooks processando 8 tipos de eventos
- [x] Mapeamento grupos→roles operacional
- [x] Links para WorkOS Dashboard funcionando
- [x] Admin Portal self-service disponível
- [x] Deep Links tenant-specific (URLs com organization_id)
- [x] Admin Portal embedado (modal com iframe)
- [x] Métricas real-time da API WorkOS

##### Compliance
- [x] Logs locais mantidos para backup (7 anos)
- [x] HMAC SHA256 validação de webhooks
- [x] Tenant isolation implementado
- [x] Audit trail documentado
- [x] SOC 2 Type II herdado

##### Certificações WorkOS
- ✅ SOC 2 Type II
- ✅ GDPR
- ✅ CCPA
- ✅ HIPAA Ready (BAA disponível)

---

### 1.6.19 Glossário

| Termo | Definição |
|-------|-----------|
| **SSO** | Single Sign-On - Login único para múltiplas aplicações |
| **SCIM** | System for Cross-domain Identity Management - Protocolo de sincronização de diretório |
| **IdP** | Identity Provider - Provedor de identidade (Azure AD, Okta, etc.) |
| **SAML** | Security Assertion Markup Language - Protocolo de autenticação |
| **OIDC** | OpenID Connect - Protocolo de autenticação baseado em OAuth 2.0 |
| **MFA** | Multi-Factor Authentication - Autenticação de múltiplos fatores |
| **ACS URL** | Assertion Consumer Service URL - Endpoint que recebe respostas SAML |
| **Entity ID** | Identificador único da aplicação no protocolo SAML |
| **Bearer Token** | Token de autenticação para API SCIM |
| **Role** | Papel/função do usuário que define suas permissões |
| **Provisionamento** | Criação automática de conta de usuário |
| **Desprovisionamento** | Desativação automática de conta de usuário |
| **Directory Sync** | Sincronização de diretório corporativo |
| **HMAC** | Hash-based Message Authentication Code - Validação de integridade |

---

## 1.7 Guia Vanta/Drata Compliance

### Visão Geral

Plataformas de automação de compliance:
- SOC 2 Type II
- ISO 27001
- HIPAA
- BCB 498/2025

### Comparativo

| Critério | Vanta | Drata |
|----------|-------|-------|
| Preço inicial | ~$12k/ano | ~$10k/ano |
| Integrações | 200+ | 100+ |
| SOC 2 | ✅ | ✅ |
| ISO 27001 | ✅ | ✅ |
| BCB 498 | ❌ (adicional) | ❌ (adicional) |

---

## 1.8 Guia Privacy Tools LGPD

### Visão Geral

Plataforma brasileira para conformidade LGPD:
- Portal do Titular (público, para candidatos)
- Gestão de Consentimentos
- RIPD (Relatório de Impacto)
- Mapeamento de Dados

### Funcionalidades

| Módulo | Descrição | Substitui Dev Interno? |
|--------|-----------|------------------------|
| **Portal Titular** | Candidatos exercem direitos LGPD | ✅ **SIM** - não desenvolver |
| **Consentimentos** | Gestão de opt-in/opt-out | ✅ SIM |
| **RIPD** | Relatório automático | ✅ SIM |
| **Breach** | Gestão de incidentes | ✅ SIM |

> **IMPORTANTE:** Privacy Tools já inclui o Portal do Titular LGPD que estava planejado para desenvolvimento interno (~2.500 linhas). Isso representa **economia de R$ 30-50k** em desenvolvimento.

### Customizações Necessárias

| Item | Esforço | Descrição |
|------|---------|-----------|
| **Theming/Branding** | ~200 linhas | CSS customizado, logo WeDo Talent |
| **Webhook Integration** | ~200 linhas | Sincronizar solicitações com backend |
| **SSO/Deep Links** | ~100 linhas | Login integrado, redirecionamentos |
| **TOTAL** | **~500 linhas** | vs 2.500 planejadas (economia 80%) |

---

## 1.9 Guia Warden AI

### Visão Geral

Warden AI audita viés em sistemas de IA:
- Análise de decisões automatizadas
- Relatórios de fairness
- Conformidade com NYC LL144, EU AI Act

### Aplicação no WeDo Talent

- Auditoria do sistema LIA (triagem de candidatos)
- Relatórios mensais de bias
- Dashboard de AI Governance

---

## 1.10 O Que Desenvolver Internamente

### ~~Portal LGPD Público~~ ❌ CANCELADO

> **Decisão:** Substituído por Privacy Tools (SaaS). O módulo "Portal do Titular" já inclui todas as funcionalidades necessárias:
> - Visualização de dados pessoais
> - Solicitação de direitos (acesso, correção, exclusão, portabilidade)
> - Acompanhamento de solicitações
> - Gestão de consentimentos

**Economia:** ~2.500 linhas de código, ~2 semanas de desenvolvimento, ~R$ 30-50k

### ~~Trust Center Público~~ ❌ CANCELADO

> **Decisão:** Trust Center será mantido no Notion e integrado via embed/iframe no website público.
> 
> **Economia:** ~2.000 linhas de código, ~1 semana de desenvolvimento

| Aspecto | Trust Center (Notion) | Vantagens |
|---------|----------------------|-----------|
| **Manutenção** | Equipe não-técnica pode editar | ✅ Sem deploys para atualizar conteúdo |
| **Velocidade** | Atualizações instantâneas | ✅ Compliance sempre atualizado |
| **Custo** | R$ 0 (Notion gratuito para páginas públicas) | ✅ Sem custo adicional |
| **SEO** | Notion tem boa indexação | ✅ Bom para discovery |

**Implementação:**
- Página Notion: https://www.notion.so/2e8f66d01d6b81adadc7d7543839ac02
- Embed no website: `/trust` → iframe ou redirect para Notion
- Alternativa: Usar Notion API para renderizar conteúdo no frontend

**Conteúdo no Notion:**
- Certificações (SOC 2, ISO 27001, LGPD)
- 16 Subprocessadores documentados
- 4 Metodologias de IA (WSI, Rubric, LIA Scoring, LIA Opinion)
- Conformidade regulatória (LGPD Art. 20, NYC LL144, EU AI Act Art. 14)
- Direitos do candidato
- Documentos para download

### Integração Privacy Tools (~500 linhas)

Desenvolvimento mínimo para integrar o SaaS:
- Webhook receiver para eventos LGPD
- SSO/deep links para candidatos
- Theming customizado (CSS, logo)

### Resumo de Desenvolvimento Interno

| Componente | Linhas | Status |
|------------|--------|--------|
| ~~Portal LGPD~~ | ~~2.500~~ | ❌ Substituído por Privacy Tools |
| ~~Trust Center~~ | ~~2.000~~ | ❌ Substituído por Notion |
| Integração Privacy Tools | 500 | ✅ Desenvolver |
| Integração Notion Trust Center | ~100 | ✅ Embed/redirect simples |
| APIs Backend Admin | 4.500 | ✅ Desenvolver |
| **TOTAL** | **5.100** | **Economia: 4.400 linhas** |

---

# CAPÍTULO 2: WEDO TALENT PLATAFORMA

> **Escopo:** Funil de Vagas (📋), Funil de Talentos (👥), Menu Configurações (⚙️)  
> **Filosofia:** 30% SaaS + 70% Desenvolvimento Interno  
> **Core do Produto:** Onde está o diferencial competitivo

---

## 2.1 Visão Geral das Integrações

### 2.1.1 Mapa de Integrações (Atualizado)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            WEDO TALENT - ECOSSISTEMA COMPLETO                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    │                                    │                                    │
    ▼                                    ▼                                    ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│    LLMs / IA      │          │   ORQUESTRAÇÃO    │          │    SOURCING       │
│                   │          │                   │          │                   │
│ • Claude (Anthr.) │          │ • LangGraph       │          │ • Pearch AI       │
│ • Gemini (Google) │          │ • LangChain       │          │ • Apify/LinkedIn  │
│                   │          │ • LangSmith       │          │                   │
└───────────────────┘          └───────────────────┘          └───────────────────┘
    │                                    │                                    │
    └────────────────────────────────────┼────────────────────────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    │                                    │                                    │
    ▼                                    ▼                                    ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│   COMUNICAÇÃO     │          │    ATS / HRIS     │          │   IDENTITY        │
│                   │          │   (Unified APIs)  │          │                   │
│ • MS Graph        │          │ • Merge.dev       │          │ • WorkOS          │
│ • WhatsApp + Voice│          │   (unified)       │          │ (SSO/SCIM/MFA)    │
│   (Twilio)        │          │ • Gupy (direto)   │          │                   │
│ • Mailgun + Resend│          │ • Pandapé (direto)│          │                   │
└───────────────────┘          └───────────────────┘          └───────────────────┘
    │                                    │                                    │
    └────────────────────────────────────┼────────────────────────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    │                                    │                                    │
    ▼                                    ▼                                    ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│    VOZ / STT      │          │  MESSAGE QUEUE    │          │   CLOUD INFRA     │
│                   │          │                   │          │                   │
│ • Deepgram        │          │ • RabbitMQ        │          │ • Replit          │
│ • OpenMic.ai      │          │   (CloudAMQP)     │          │ • Google Cloud    │
│                   │          │                   │          │ • Microsoft Azure │
└───────────────────┘          └───────────────────┘          └───────────────────┘
    │                                    │                                    │
    └────────────────────────────────────┼────────────────────────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    │                                    │                                    │
    ▼                                    ▼                                    ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│  DESIGN / PROTO   │          │   GESTÃO PROJ.    │          │  DEVOPS / VCS     │
│                   │          │                   │          │                   │
│ • Figma           │          │ • Atlassian Jira  │          │ • GitHub          │
│ • Replit (proto)  │          │ • Notion          │          │ • Bitbucket       │
│                   │          │                   │          │                   │
└───────────────────┘          └───────────────────┘          └───────────────────┘
```

### 2.1.2 Resumo Executivo (25+ Integrações)

| Categoria | Integrações | Custo Mensal | Criticidade | 📋 Vagas | 👥 Funil Talentos | ⚙️ Configurações |
|-----------|-------------|--------------|-------------|----------|-------------------|------------------|
| **LLMs / IA** | Claude, Gemini | $500-2.000 | **Crítico** | ✅ Geração JD, WSI, extração requisitos | ✅ Scoring, análise CV, triagem | ❌ |
| **Orquestração** | LangGraph, LangChain, LangSmith | $50-500 | **Crítico** | ✅ Workflow criação vaga (14 passos) | ✅ Orquestração agentes triagem | ❌ |
| **Sourcing** | Pearch, Apify | $1.000-5.000 | **Crítico** | ❌ | ✅ Busca 800M+ perfis, similar search, calibração | ❌ |
| **Voz / STT** | Deepgram, OpenMic | $50-500 | Médio | ❌ | ✅ Voice screening, transcrição entrevistas | ❌ |
| **Comunicação** | MS Graph, WhatsApp, Mailgun | $0-200 | Alto | ✅ Publicação, notificações | ✅ Agendamento, follow-ups, convites | ✅ Templates de comunicação |
| **ATS/HRIS** | Merge | $650-2.000 | Alto | ✅ Sync vagas bidirectional | ✅ Import/export candidatos | ✅ Conexão ATS cliente |
| **Identity** | WorkOS | $250-1.000 | Alto | ❌ | ❌ | ✅ SSO, SCIM, MFA, audit logs |
| **Cloud Infra** | Replit, GCP, Azure | $100-1.000 | **Crítico** | ✅ Backend, storage | ✅ Backend, storage | ✅ Hosting, database |
| **Message Queue** | RabbitMQ (CloudAMQP) | $0-200 | Médio | ✅ Jobs publicação | ✅ Fila processamento CVs | ❌ |
| **Design** | Figma, Replit | $50-200 | Baixo | ❌ | ❌ | ❌ (Time interno) |
| **Gestão Proj.** | Jira, Notion | $0-100 | Baixo | ❌ | ❌ | ❌ (Time interno) |
| **DevOps/VCS** | GitHub, Bitbucket | $0-50 | Baixo | ❌ | ❌ | ❌ (Time interno) |
| **TOTAL** | **25+** | **$2.700-12.750** | - | - | - | - |

### 2.1.3 Detalhamento por Área da Plataforma

#### 📋 Vagas (Criação e Gestão)

| Integração | Uso Específico | Etapas do Wizard |
|------------|----------------|------------------|
| **Claude** | Geração de JD, extração de requisitos, perguntas WSI | Etapas 4-8 |
| **Gemini** | Expansão semântica de skills | Etapa 5 |
| **LangGraph** | Workflow de 14 passos do wizard | Todas |
| **MS Graph** | Notificações de aprovação | Etapa 11 |
| **Mailgun** | Email de publicação da vaga | Etapa 14 |
| **Merge** | Sync bidirectional com ATS | Etapa 14 |
| **RabbitMQ** | Fila de jobs de publicação | Etapa 14 |

#### 👥 Funil de Talentos (Sourcing → Contratação)

| Integração | Uso Específico | Etapas do Funil |
|------------|----------------|-----------------|
| **Pearch AI** | Busca global, similar search | Sourcing (etapa 15-17) |
| **Apify** | Enriquecimento LinkedIn | Sourcing (etapa 17) |
| **Claude** | Scoring CV, análise comparativa | Triagem (etapa 18-20) |
| **OpenMic** | Voice screening assíncrono | Triagem (etapa 19) |
| **Deepgram** | Transcrição de entrevistas | Entrevista (etapa 20) |
| **MS Graph** | Agendamento calendário Teams | Agendamento (etapa 24) |
| **WhatsApp** | Comunicação candidatos | Todas as etapas |
| **Mailgun** | Emails de feedback | Etapas 21, 25, 27 |
| **LangGraph** | Orquestração dos 6 agentes | Todas |

#### ⚙️ Menu Configurações

| Integração | Uso Específico | Tela |
|------------|----------------|------|
| **WorkOS** | SSO SAML/OIDC, SCIM provisioning, MFA | /configuracoes/sso |
| **Mailgun** | Configuração templates email | /configuracoes/comunicacao |
| **WhatsApp** | Configuração templates WhatsApp | /configuracoes/comunicacao |
| **Merge** | Conexão ATS do cliente | /configuracoes/integracoes |
| **MS Graph** | Conexão calendário | /configuracoes/integracoes |

---

## 2.2 LLMs e Inteligência Artificial

### 2.2.1 Anthropic Claude

**Uso na Plataforma:**
- LIA (assistente conversacional principal)
- Análise de CVs e scoring
- Geração de perguntas WSI
- Extração de requisitos de JD
- Multi-agent orchestration

**Modelos e Preços:**

| Modelo | Input $/MTok | Output $/MTok | Uso Recomendado |
|--------|--------------|---------------|-----------------|
| **Claude 4 Sonnet** | $3 | $15 | Default para tudo |
| **Claude 4.5 Haiku** | $1 | $5 | Tasks simples, alto volume |
| **Claude 4 Opus** | $15 | $75 | Análises muito complexas |

**Otimizações Disponíveis:**
- **Prompt Caching**: -90% em inputs repetidos (cache read)
- **Batch API**: -50% para processamento assíncrono

**Custo Estimado:** $25-100/cliente/mês (com otimizações: $15-50)

**Configuração:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
```

**Uso por Área:**

| Área | Uso | Volume Estimado |
|------|-----|-----------------|
| 📋 Vagas | Geração JD, WSI, requisitos | 20-50 calls/vaga |
| 👥 Funil | Scoring CV, análise comparativa | 10-30 calls/candidato |
| 💬 Chat LIA | Conversação, briefings | 50-200 calls/dia/recrutador |

### 2.2.2 Google Gemini

**Uso na Plataforma:**
- Semantic Search (expansão de termos)
- Fallback conversacional
- Transcrição de áudio

**Modelos e Preços:**

| Modelo | Input $/MTok | Output $/MTok | Uso Recomendado |
|--------|--------------|---------------|-----------------|
| **Gemini 2.5 Flash** | $0.15 | $0.60 | Semantic search (P95 <300ms) |
| **Gemini 2.5 Flash-Lite** | $0.10 | $0.40 | Alto volume, simples |
| **Gemini 2.5 Pro** | $1.25 | $10.00 | Análises complexas |

**Custo Estimado:** $0.50-5/cliente/mês (muito barato!)

**Configuração:**
```bash
GEMINI_API_KEY=xxx
```

**Uso por Área:**

| Área | Uso | Volume Estimado |
|------|-----|-----------------|
| 📋 Vagas | Expansão semântica skills | 5-10 calls/vaga |
| 👥 Funil | Expansão termos busca | 10-50 calls/busca |

---

## 2.3 Orquestração e Observabilidade de Agentes

### 2.3.1 LangGraph

**O que é:** Framework para construção de agentes LLM com estados e grafos de decisão

**Uso na Plataforma:**
- Orquestração dos 6 agentes especializados
- Fluxos conversacionais complexos
- State machines para workflows

**Preços:**

| Item | Custo |
|------|-------|
| LangGraph (biblioteca) | **Grátis** (open source) |
| LangGraph Cloud (hosting) | $0.02/invocação |

**Custo Estimado:** $0 (self-hosted) ou $50-200/mês (cloud)

**Uso por Área:**

| Área | Uso |
|------|-----|
| 📋 Vagas | Workflow wizard 14 passos, Job Intake Agent |
| 👥 Funil | Sourcing Agent, Screening Agent, Scheduling Agent |
| 💬 Chat LIA | Orchestrator, Intent Router |

### 2.3.2 LangChain

**O que é:** Framework para desenvolvimento de aplicações LLM

**Uso na Plataforma:**
- Chains para processamento de documentos
- Prompts templates
- Memory management
- RAG (Retrieval Augmented Generation)

**Preços:**

| Item | Custo |
|------|-------|
| LangChain (biblioteca) | **Grátis** (open source) |

**Custo Estimado:** $0

### 2.3.3 LangSmith

**O que é:** Plataforma de observabilidade e debugging para aplicações LLM

**Uso na Plataforma:**
- Tracing de todas as chamadas LLM
- Debugging de agentes
- Avaliação de qualidade
- Monitoramento de custos

**Preços:**

| Plano | Preço | Traces/Mês | Seats |
|-------|-------|------------|-------|
| **Developer** | Grátis | 5.000 | 1 |
| **Plus** | $39/user/mês | 10.000 | Até 10 |
| **Enterprise** | Custom | Ilimitado | Ilimitado |

**Traces Adicionais:**
- Base traces (14 dias): $0.50/1.000
- Extended traces (400 dias): $5/1.000

**Custo Estimado:** $0-200/mês (depende do volume)

---

## 2.4 Banco de Candidatos e Sourcing

### 2.4.1 Pearch AI

**O que é:** Banco de candidatos com 800M+ perfis globais

**Uso na Plataforma:**
- Busca global de candidatos
- Similar search (perfis semelhantes)
- Sourcing automatizado

**Preços (Estimativa por Créditos):**

| Pacote | Créditos | Preço | Por Crédito |
|--------|----------|-------|-------------|
| Starter | 1.000 | $100 | $0.10 |
| Growth | 5.000 | $400 | $0.08 |
| Business | 20.000 | $1.200 | $0.06 |
| Enterprise | 100.000 | $5.000 | $0.05 |

**Custo Estimado:** $50-500/cliente/mês

**Configuração:**
```bash
PEARCH_API_KEY=xxx
PEARCH_API_URL=https://api.pearch.ai/v1
```

**Uso na Área 👥 Funil de Talentos:**

| Funcionalidade | Descrição | Créditos/Uso |
|----------------|-----------|--------------|
| **Busca por filtros** | Skills, cargo, localização | 1 crédito/perfil |
| **Similar Search** | Encontra perfis semelhantes | 5 créditos/busca |
| **Enriquecimento** | Dados adicionais do perfil | 2 créditos/perfil |

### 2.4.2 Apify (LinkedIn Scraper)

**Uso na Plataforma:**
- Similar Search (extração de perfis)
- Enriquecimento de dados
- Calibração de candidatos

**Preços:**

| Tipo | Custo/1.000 perfis |
|------|-------------------|
| Perfil básico (no-cookie) | $3-4 |
| Perfil + Email | $10 |

**Custo Estimado:** $0.50-10/cliente/mês

---

## 2.5 Speech-to-Text e Voz

### 2.5.1 Deepgram

**Uso na Plataforma:**
- Transcrição de entrevistas
- Voice input no chat LIA

**Preços:**

| Modelo | Pré-gravado | Streaming |
|--------|-------------|-----------|
| Nova-2 | $0.0043/min | $0.0077/min |

**Bônus:** $200 em créditos grátis para novos usuários

**Custo Estimado:** $0.50-10/cliente/mês

**Configuração:**
```bash
DEEPGRAM_API_KEY=xxx
```

**Uso na Área 👥 Funil de Talentos:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Transcrição entrevista | Converte áudio em texto para análise |
| Voice screening | Transcreve respostas de candidatos |

### 2.5.2 OpenMic.ai

**Uso na Plataforma:**
- Plataforma de voice screening
- Entrevistas assíncronas por voz

**Preços (Estimativa):**

| Tier | Preço/Mês |
|------|-----------|
| Starter | $200 |
| Growth | $500 |
| Enterprise | Custom |

**Custo Estimado:** $50-200/cliente/mês

**Uso na Área 👥 Funil de Talentos:**

| Funcionalidade | Descrição |
|----------------|-----------|
| Voice screening | Entrevistas assíncronas com IA |
| Análise de resposta | Avaliação automática por LLM |

---

## 2.6 Comunicação e Agendamento

### 2.6.1 Microsoft Graph API

**Uso na Plataforma:**
- Agendamento de entrevistas (Calendar)
- Integração com Teams
- Notificações e lembretes

**Preços:**

| Operação | Custo |
|----------|-------|
| Calendar (eventos, scheduling) | **GRÁTIS** |
| Teams chat básico | **GRÁTIS** |
| Meeting transcripts | **GRÁTIS** |
| Export mensagens Teams | $0.00075/msg |

**Custo para WeDo:** $0 (cliente já tem M365)

**Configuração:**
```bash
MICROSOFT_CLIENT_ID=xxx
MICROSOFT_CLIENT_SECRET=xxx
MICROSOFT_TENANT_ID=xxx
```

**Uso por Área:**

| Área | Uso |
|------|-----|
| 📋 Vagas | Notificações aprovação |
| 👥 Funil | Agendamento entrevistas, verificação disponibilidade |
| ⚙️ Config | Conexão calendário cliente |

### 2.6.2 WhatsApp Business API

**Uso na Plataforma:**
- Triagem via WhatsApp
- Comunicação com candidatos

**Preços (Brasil):**

| Tipo | Custo/Conversa |
|------|---------------|
| Utility | $0.0080 |
| Marketing | $0.0625 |
| Service | $0.0300 |

**Custo Estimado:** $5-50/cliente/mês

**Uso por Área:**

| Área | Uso |
|------|-----|
| 👥 Funil | Triagem, convites, lembretes, feedback |
| ⚙️ Config | Templates de mensagem |

### 2.6.3 Mailgun

**Uso na Plataforma:**
- Emails transacionais
- Notificações e templates

**Preços:**

| Plano | Emails/Mês | Preço |
|-------|------------|-------|
| Free | 5.000/mês (3 meses) | $0 |
| Flex | Pay-as-you-go | $0.80/1000 |
| Foundation | 50K | $35 |
| Scale | 100K | $90 |

**Custo Estimado:** $5-20/cliente/mês

**Configuração:**
```bash
# Mailgun (provider primário) — corrigido em v3.7
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=mg.wedotalent.com
MAILGUN_WEBHOOK_SIGNING_KEY=xxx
# Resend (fallback) — adicionado em v3.7
RESEND_API_KEY=re_xxx
```
> ⚠️ Versões 3.0–3.6 listavam erroneamente `SENDGRID_API_KEY` aqui — projeto **não usa SendGrid**. Provider é Mailgun (`app/services/email_providers/mailgun_provider.py`) com Resend como fallback.

**Uso por Área:**

| Área | Uso |
|------|-----|
| 📋 Vagas | Publicação, notificações internas |
| 👥 Funil | Convites, feedback, follow-ups |
| ⚙️ Config | Templates de email |

---

## 2.7 Integrações ATS/HRIS (Unified APIs)

### 2.7.1 Merge

**O que é:** Unified API para integrações de ATS e HRIS

**Uso na Plataforma:**
- Integração com 200+ ATS e HRIS
- Sync de candidatos e vagas
- Onboarding automatizado

**ATS/HRIS Suportados:**
- **ATS:** Greenhouse, Lever, Ashby, Workday, Taleo, Gupy, Pandapé
- **HRIS:** BambooHR, Personio, SAP SuccessFactors, Oracle HCM

**Preços:** Custom (contato comercial)

**Estimativa baseada em mercado:**

| Tier | Preço/Mês | Contas Conectadas |
|------|-----------|-------------------|
| Starter | $500 | 10 |
| Growth | $1.500 | 50 |
| Enterprise | $5.000+ | Ilimitado |

**Custo por cliente conectado:** ~$50-100/mês

**Uso por Área:**

| Área | Uso |
|------|-----|
| 📋 Vagas | Sync bidirectional de vagas |
| 👥 Funil | Import/export candidatos |
| ⚙️ Config | Conexão com ATS do cliente |

### 2.7.2 ~~Merge (Concorrente)~~ — DEPRECATED em v3.7

> ⚠️ **Esta seção era duplicação errada do mesmo produto Merge.dev** (provavelmente
> resultado de um find/replace mal-aplicado em versão anterior, talvez quando
> "StackOne" foi renomeado para "Merge"). Não existem dois "Merge" — há um único
> provider unified API (Merge.dev) implementado em
> `app/domains/ats_integration/services/ats_clients/merge.py`. Pricing real:
> Free 3 conexões → Launch $650/mês (10 conexões) → $65/conta adicional.
> Os blocos abaixo são mantidos apenas para referência histórica.

**~~Uso Potencial:~~**
- ~~Alternativa ao Merge~~
- ~~220+ integrações disponíveis~~

**Preços:**

| Plano | Preço/Mês | Contas Incluídas | Adicional |
|-------|-----------|------------------|-----------|
| **Free** | $0 | 3 | - |
| **Launch** | $650 | 10 | $65/conta |
| **Professional** | Custom | Volume | Negociável |
| **Enterprise** | Custom | Ilimitado | Negociável |

**Merge - Detalhes:**

| Critério | Merge |
|----------|-------|
| Preço público | ✅ Sim ($65/conexão) |
| Foco | ATS/HRIS Unified API |
| Compliance | SOC 2, HIPAA, ISO |
| Starter | 3 conexões grátis |

---

## 2.8 Autenticação e Identity

### 2.8.1 WorkOS

**Uso na Plataforma:**
- SSO enterprise (Okta, Azure AD)
- SCIM (provisioning automático)
- MFA, Audit Logs

**Preços:**

| Feature | Preço/Conexão |
|---------|---------------|
| SSO | $125/mês |
| SCIM | $125/mês |
| Combo (SSO+SCIM) | $250/mês |

**Custo por Cliente Enterprise:** $250/mês

**Uso na Área ⚙️ Configurações:**

| Funcionalidade | Descrição |
|----------------|-----------|
| SSO Setup | Configuração SAML/OIDC |
| SCIM Directory | Sync automático de usuários |
| MFA | Autenticação multi-fator |
| Audit Logs | Logs de acesso para compliance |

**Detalhes completos:** Ver [Seção 1.6 - Guia WorkOS SSO/SCIM](#16-guia-workos-ssoscim)

---

## 2.9 Infraestrutura Cloud

### 2.9.1 Replit

**Uso na Plataforma:**
- Desenvolvimento e prototipação
- Hosting de aplicação
- PostgreSQL database

**Preços:**

| Plano | Preço/Mês |
|-------|-----------|
| Hacker | $7 |
| Pro | $20 |
| Teams | $15/seat |
| Deployments | Por uso |

**Custo Estimado:** $50-200/mês

### 2.9.2 Google Cloud Platform (GCP)

**Uso na Plataforma:**
- Gemini API (já coberto em LLMs)
- Cloud Storage (arquivos de CVs)
- Cloud Run (containers)
- BigQuery (analytics)

**Preços Relevantes:**

| Serviço | Preço |
|---------|-------|
| Cloud Storage | $0.02/GB/mês |
| Cloud Run | $0.00002400/vCPU-segundo |
| BigQuery | $5/TB processado |
| Cloud Functions | $0.40/milhão invocações |

**Custo Estimado:** $50-300/mês (depende de uso)

### 2.9.3 Microsoft Azure

**Uso na Plataforma:**
- Azure OpenAI (alternativa)
- Azure Blob Storage
- Azure Functions
- Azure AD (integração via WorkOS)

**Preços Relevantes:**

| Serviço | Preço |
|---------|-------|
| Blob Storage | $0.018/GB/mês |
| Functions | $0.20/milhão execuções |
| Cognitive Services | Por uso |

**Custo Estimado:** $50-300/mês (se usado)

---

## 2.10 Message Queue e Event-Driven

### 2.10.1 RabbitMQ (CloudAMQP)

**O que é:** Message broker para processamento assíncrono

**Uso na Plataforma:**
- Fila de processamento de CVs
- Eventos entre agentes
- Jobs assíncronos

**Preços (CloudAMQP):**

| Plano | Preço/Mês | Tipo |
|-------|-----------|------|
| Little Lemur | Grátis | Shared (limitado) |
| Tough Tiger | $19 | Shared |
| **Sassy Squirrel** | $49 | Dedicated |
| Roaring Rabbit | $99 | Dedicated |

**Custo Estimado:** $0-99/mês

**Uso por Área:**

| Área | Uso |
|------|-----|
| 📋 Vagas | Jobs de publicação, sync ATS |
| 👥 Funil | Fila processamento CVs, eventos agentes |

---

## 2.11 Design e Prototipação

### 2.11.1 Figma

**Uso na Plataforma:**
- Design de interfaces
- Protótipos interativos
- Design system
- Handoff para desenvolvedores

**Preços:**

| Plano | Preço/Editor/Mês | API |
|-------|------------------|-----|
| Starter | Grátis | ✅ REST (limitado) |
| Professional | $12 | ✅ REST |
| Organization | $45 | ✅ REST + Webhooks |
| Enterprise | $75-90 | ✅ Completo + Variables |

**Custo Estimado (time WeDo):** $50-200/mês

### 2.11.2 Replit (Prototipação)

**Uso na Plataforma:**
- Prototipação rápida
- Demos para clientes
- Ambiente de desenvolvimento

**Custo:** Já incluído em infraestrutura

---

## 2.12 Gestão de Projetos e Colaboração

### 2.12.1 Atlassian Jira

**Uso na Plataforma:**
- Gestão de tarefas e sprints
- Tracking de bugs
- Roadmap de produto

**Preços:**

| Plano | Preço/User/Mês | API |
|-------|----------------|-----|
| Free | $0 (até 10 users) | ✅ REST |
| Standard | $7-8 | ✅ REST |
| Premium | $16 | ✅ REST |
| Enterprise | $155+/user/ano | ✅ REST + Audit |

**Custo Estimado (time WeDo):** $0-100/mês

### 2.12.2 Notion

**Uso na Plataforma:**
- Documentação interna
- Knowledge base
- Help Center (público)
- Websites simples

**Preços:**

| Plano | Preço/User/Mês | API |
|-------|----------------|-----|
| Free | $0 | ✅ Grátis |
| Plus | $10 | ✅ Grátis |
| Business | $15 | ✅ Grátis |
| Enterprise | Custom | ✅ + SCIM |

**Custo Estimado (time WeDo):** $0-50/mês

---

## 2.13 Controle de Versão e DevOps

### 2.13.1 GitHub

**Uso na Plataforma:**
- Repositórios de código
- CI/CD (GitHub Actions)
- Code review
- Project management

**Preços:**

| Plano | Preço/User/Mês | Repos Privados | Actions |
|-------|----------------|----------------|---------|
| Free | $0 | ✅ Ilimitado | 2.000 min |
| Team | $4 | ✅ Ilimitado | 3.000 min |
| Enterprise | $21 | ✅ Ilimitado | 50.000 min |

**Custo Estimado (time WeDo):** $0-50/mês

### 2.13.2 Bitbucket

**Uso na Plataforma:**
- Alternativa ao GitHub
- Integração com Jira

**Preços:**

| Plano | Preço/User/Mês |
|-------|----------------|
| Free | $0 (até 5 users) |
| Standard | $3 |
| Premium | $6 |

**Custo Estimado:** $0-30/mês

---

## 2.14 Documentação e Knowledge Base

### 2.14.1 Notion (Knowledge Base)

**Uso na Plataforma:**
- Help Center público
- FAQ
- Tutoriais
- Changelog

**Integração com Website:**
- Notion Sites (nativo)
- Super.so, Potion (terceiros)

**Custo:** Já incluído em Notion (seção 2.12.2)

---

## 2.15 Resumo de Custos por Cliente

### 2.15.1 Custo Variável por Cliente (Mensal)

> **Base de Cálculo:** Valores estimados por cliente com uso típico. "Mínimo" = 1 cliente pequeno com uso básico.

| Integração | Mínimo | Pequeno | Médio | Grande | Base de Cálculo | 📋 | 👥 | ⚙️ |
|------------|--------|---------|-------|--------|-----------------|----|----|-----|
| **Claude (LLM)** | $10 | $25 | $45 | $100 | ~500 calls/mês @$0.02 | ✅ | ✅ | ❌ |
| **Gemini** | $0 | $0.50 | $0.50 | $1 | Free tier cobre início | ✅ | ✅ | ❌ |
| **LangSmith** | $0 | $0 | $5 | $20 | Free: 5k traces/mês | ✅ | ✅ | ❌ |
| **Pearch** | $0 | $50 | $200 | $500 | Pode iniciar sem | ❌ | ✅ | ❌ |
| **Apify** | $0 | $0.50 | $2 | $8 | Free tier disponível | ❌ | ✅ | ❌ |
| **Deepgram** | $0 | $0.50 | $2 | $9 | $200 créditos grátis | ❌ | ✅ | ❌ |
| **OpenMic** | $0 | $50 | $100 | $200 | Pode iniciar sem | ❌ | ✅ | ❌ |
| **MS Graph** | $0 | $0 | $0 | $0 | 100% grátis | ✅ | ✅ | ✅ |
| **WhatsApp** | $0 | $5 | $20 | $50 | 1000 msg grátis/mês | ❌ | ✅ | ✅ |
| **Mailgun** | $0 | $4 | $8 | $16 | Free: 5.000/mês | ✅ | ✅ | ✅ |
| **WorkOS** | $0 | $0 | $250 | $250 | Só se cliente pedir SSO | ❌ | ❌ | ✅ |
| **Merge** | $0 | $0 | $65 | $100 | Merge Free: 3 conexões | ✅ | ✅ | ✅ |
| **TOTAL** | **$10** | **$136** | **$700** | **$1.258** | - | - | - | - |

### 2.15.2 Custo Fixo da Plataforma (Mensal)

> **Base de Cálculo:** "Mínimo" = planos gratuitos + mínimo necessário para operar.

| Item | Mínimo | Recomendado | Premium | Base de Cálculo |
|------|--------|-------------|---------|-----------------|
| Replit (hosting) | $20 | $100 | $200 | Pro: $20, Teams: $100+ |
| PostgreSQL | $0 | $0 | $50 | Replit incluso |
| Redis | $0 | $7 | $30 | Free tier Upstash/Redis |
| RabbitMQ (CloudAMQP) | $0 | $19 | $49 | Little Lemur = grátis |
| LangSmith | $0 | $39 | $200 | Developer = grátis |
| GCP/Azure | $0 | $50 | $300 | Free tier generoso |
| Figma (time) | $0 | $50 | $200 | Starter = grátis |
| Jira (time) | $0 | $0 | $50 | Free até 10 users |
| GitHub (time) | $0 | $0 | $50 | Free ilimitado |
| Notion (time) | $0 | $0 | $30 | Free para times pequenos |
| **TOTAL FIXO** | **$20** | **$265** | **$1.159** | - |

### 2.15.3 Cenários de Custo Total

**Cenário 0: Bootstrap/MVP (0-1 cliente)**
```
Custo variável: 1 × $10 = $10
Custo fixo: $20 (mínimo)
─────────────────────────────
TOTAL: $30/mês (~R$ 150)
```
> **Nota:** Usando free tiers e planos básicos. Ideal para validação.

**Cenário 1: Primeiros Clientes (3 clientes pequenos)**
```
Custo variável: 3 × $136 = $408
Custo fixo: $265 (recomendado)
─────────────────────────────
TOTAL: $673/mês (~R$ 3.365)
Por cliente: $224/mês
```

**Cenário 2: Growth (30 clientes médios)**
```
Custo variável: 30 × $700 = $21.000
Custo fixo: $800
─────────────────────────────
TOTAL: $21.800/mês
Por cliente: $727/mês
```

**Cenário 3: Scale (100 clientes mix)**
```
Custo variável: 100 × $500 (média) = $50.000
Custo fixo: $1.159
─────────────────────────────
TOTAL: $51.159/mês
Por cliente: $512/mês
```

### 2.15.4 Tabela Resumo de Custos Mínimos

| Área | Custo Mínimo/Mês | Com Que | Escalável Para |
|------|------------------|---------|----------------|
| **Plataforma (APIs)** | **$10** | 1 cliente, free tiers | $1.258/cliente grande |
| **Infraestrutura Fixa** | **$20** | Replit Pro básico | $1.159/mês premium |
| **Admin (SaaS)** | **$0** | Sem Vanta inicialmente | R$ 16k/mês full |
| **TOTAL MÍNIMO** | **$30/mês** | MVP viável | Escala conforme clientes |

> **Filosofia:** Começar com custo mínimo, escalar conforme receita. Não pagar por ferramentas antes de precisar.

---

## 2.16 Análise de Viabilidade

### 2.16.1 Curto Prazo (0-6 meses)

| Integração | Prioridade | Viabilidade | Status |
|------------|------------|-------------|--------|
| **Claude** | P0 | ✅ Viável | ✅ Integrado |
| **Gemini** | P0 | ✅ Viável | ✅ Integrado |
| **Pearch** | P0 | ✅ Viável | ✅ Integrado |
| **LangGraph** | P0 | ✅ Viável | ✅ Integrado |
| **LangChain** | P0 | ✅ Viável | ✅ Integrado |
| **WorkOS** | P0 | ✅ Viável | ✅ Integrado |
| **Deepgram** | P1 | ✅ Viável | 🔄 Implementar |
| **MS Graph** | P1 | ✅ Viável | 🔄 Implementar |
| **WhatsApp** | P1 | ✅ Viável | 🔄 Implementar |
| **LangSmith** | P1 | ✅ Viável | 🔄 Implementar |
| **RabbitMQ** | P2 | ✅ Viável | 🔄 Implementar |

**Custo estimado curto prazo:** $3.000-5.000/mês

### 2.16.2 Médio Prazo (6-18 meses)

| Integração | Prioridade | Viabilidade | Ação |
|------------|------------|-------------|------|
| **Merge** | P1 | ✅ Viável | Unified ATS |
| **OpenMic** | P2 | ✅ Viável | Voice screening |
| **GCP/Azure** | P2 | ✅ Viável | Escalar infra |

**Custo estimado médio prazo:** $15.000-30.000/mês

### 2.16.3 Longo Prazo (18+ meses)

| Integração | Prioridade | Viabilidade | Ação |
|------------|------------|-------------|------|
| **Multi-cloud** | P2 | ⚠️ Avaliar | Redundância |
| **LLM fine-tuning** | P3 | ⚠️ Avaliar | Reduzir custos |
| **Infra própria** | P3 | ⚠️ Avaliar | Migrar de Replit |

**Custo estimado longo prazo:** $40.000-80.000/mês (100+ clientes)

---

## 2.17 Recomendações Estratégicas

### 2.17.1 Otimizações de Custo

| Ação | Economia | Esforço | Prioridade |
|------|----------|---------|------------|
| **Prompt Caching (Claude)** | -50% LLM | Médio | P0 |
| **Batch API (Claude)** | -50% async | Baixo | P0 |
| **Gemini para search** | -90% vs Claude | Baixo | ✅ Feito |
| **LangGraph self-hosted** | -100% vs cloud | Baixo | ✅ Feito |
| **Cache Redis** | -30% APIs | Médio | P1 |
| **Negociar volume Pearch** | -20% sourcing | Baixo | P1 |
| **Merge Free tier** | -100% primeiros 3 | Baixo | P2 |

### 2.17.2 Modelo de Precificação Sugerido

| Plano | Preço Cliente | Custo WeDo | Margem |
|-------|---------------|------------|--------|
| **Starter** | R$ 1.490/mês | ~$200 | 75% |
| **Professional** | R$ 3.490/mês | ~$500 | 70% |
| **Enterprise** | R$ 7.990/mês | ~$1.000 | 75% |

### 2.17.3 Roadmap de Integrações 2025-2026

```
         Q1 2025        Q2 2025        Q3 2025        Q4 2025
    ┌──────────────┬──────────────┬──────────────┬──────────────┐
    │   FASE 1     │   FASE 2     │   FASE 3     │   FASE 4     │
    │ Core Stack   │ Comunicação  │  Enterprise  │ Otimização   │
    ├──────────────┼──────────────┼──────────────┼──────────────┤
    │ • Claude     │ • MS Graph   │ • Merge   │ • LLM tuning │
    │ • Gemini     │ • WhatsApp   │ • Merge      │ • Multi-cloud│
    │ • LangGraph  │ • Mailgun   │ • OpenMic    │ • Analytics  │
    │ • LangChain  │ • RabbitMQ   │ • GCP/Azure  │ • Dashboards │
    │ • LangSmith  │ • Apify      │              │              │
    │ • Pearch     │              │              │              │
    │ • Deepgram   │              │              │              │
    │ • WorkOS     │              │              │              │
    └──────────────┴──────────────┴──────────────┴──────────────┘
         $3-5K           $8-15K         $20-35K        $40-80K
```

### 2.17.4 KPIs para Monitorar

| KPI | Meta | Alerta |
|-----|------|--------|
| **Custo LLM/cliente** | <$60/mês | >$100/mês |
| **Custo Pearch/cliente** | <$200/mês | >$400/mês |
| **Custo total/cliente** | <$600/mês | >$1.000/mês |
| **Margem bruta** | >65% | <50% |
| **API uptime** | >99.5% | <99% |
| **LangSmith traces/dia** | <5.000 | >10.000 (upgrade) |
| **Latência P95** | <500ms | >1s |

---

# APÊNDICES

## Apêndice A: Tabela Consolidada de APIs

| # | Serviço | Categoria | Modelo Pricing | Custo Est./Mês | 📋 | 👥 | ⚙️ |
|---|---------|-----------|----------------|----------------|----|----|-----|
| 1 | Anthropic Claude | LLM | Por token | $500-2.000 | ✅ | ✅ | ❌ |
| 2 | Google Gemini | LLM | Por token | $10-50 | ✅ | ✅ | ❌ |
| 3 | LangGraph | Orquestração | Open source | $0 | ✅ | ✅ | ❌ |
| 4 | LangChain | Orquestração | Open source | $0 | ✅ | ✅ | ❌ |
| 5 | LangSmith | Observabilidade | Por trace | $0-200 | ✅ | ✅ | ❌ |
| 6 | Pearch AI | Sourcing | Por crédito | $1.000-5.000 | ❌ | ✅ | ❌ |
| 7 | Apify | Scraping | Por perfil | $10-100 | ❌ | ✅ | ❌ |
| 8 | Deepgram | STT | Por minuto | $10-100 | ❌ | ✅ | ❌ |
| 9 | OpenMic.ai | Voice | Por entrevista | $200-500 | ❌ | ✅ | ❌ |
| 10 | MS Graph | Comunicação | Grátis + M365 | $0 | ✅ | ✅ | ✅ |
| 11 | WhatsApp API | Comunicação | Por conversa | $50-500 | ❌ | ✅ | ✅ |
| 12 | Mailgun | Email | Por email | $20-90 | ✅ | ✅ | ✅ |
| 13 | Merge.dev | ATS/HRIS Unified | Por conexão | $0-2.000 (Free 3 conexões → $650/10 → $65/conta) | ✅ | ✅ | ✅ |
| 14 | ~~Merge (duplicado)~~ | ~~Removido em v3.7~~ | — | — | — | — | — |
| 15 | WorkOS | Identity | Por conexão | $250-1.000 | ❌ | ❌ | ✅ |
| 16 | Replit | Infra/Proto | Por uso | $50-200 | ✅ | ✅ | ✅ |
| 17 | Google Cloud | Infra | Por uso | $50-300 | ✅ | ✅ | ✅ |
| 18 | Microsoft Azure | Infra | Por uso | $50-300 | ✅ | ✅ | ✅ |
| 19 | CloudAMQP (RabbitMQ) | Queue | Por plano | $0-99 | ✅ | ✅ | ❌ |
| 20 | Redis Cloud | Cache | Por memória | $7-60 | ✅ | ✅ | ❌ |
| 21 | Figma | Design | Por editor | $50-200 | ❌ | ❌ | ❌ |
| 22 | Atlassian Jira | Gestão | Por user | $0-100 | ❌ | ❌ | ❌ |
| 23 | Notion | Docs/KB | Por user | $0-50 | ❌ | ❌ | ❌ |
| 24 | GitHub | DevOps | Por user | $0-50 | ❌ | ❌ | ❌ |
| 25 | Bitbucket | DevOps | Por user | $0-30 | ❌ | ❌ | ❌ |

---

## Apêndice B: Contatos Comerciais

| Serviço | Docs | Sales |
|---------|------|-------|
| Anthropic | docs.anthropic.com | sales@anthropic.com |
| LangChain | docs.langchain.com | sales@langchain.com |
| Pearch | docs.pearch.ai | sales@pearch.ai |
| Merge.dev | docs.merge.dev | sales@merge.dev |
| WorkOS | workos.com/docs | sales@workos.com |
| Deepgram | developers.deepgram.com | sales@deepgram.com |
| Figma | figma.com/developers | sales@figma.com |

---

## Apêndice C: Análise de Subprocessadores

> Para análise detalhada de subprocessadores dos concorrentes (Tezi, Popp AI, Findem, HireZ, JuiceBox, Eightfold, Paradox, GoodTime, Braintrust, Wellfound, DigAI, Solides, Gupy, Coploy, InHire, LLIA), consulte o documento original: [INTEGRACOES-CUSTOS-VIABILIDADE.md](./INTEGRACOES-CUSTOS-VIABILIDADE.md#anexo-c-análise-de-subprocessadores-dos-concorrentes)

---

## Apêndice D: Checklist de Setup

### Secrets Necessários

```bash
# LLMs
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=xxx

# Sourcing
PEARCH_API_KEY=xxx

# Voice
DEEPGRAM_API_KEY=xxx
OPENMIC_API_KEY=xxx

# Comunicação — Email (Mailgun primário + Resend fallback) — corrigido v3.7
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=mg.wedotalent.com
MAILGUN_WEBHOOK_SIGNING_KEY=xxx
RESEND_API_KEY=re_xxx
# Comunicação — WhatsApp/SMS/Voice (Twilio)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Microsoft
MICROSOFT_CLIENT_ID=xxx
MICROSOFT_CLIENT_SECRET=xxx
MICROSOFT_TENANT_ID=xxx

# Billing
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Auth
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx
WORKOS_WEBHOOK_SECRET=whsec_xxx

# CRM
HUBSPOT_ACCESS_TOKEN=pat-xxx

# ATS — Merge.dev (unified) + integradores BR diretos (Gupy/Pandapé) — corrigido v3.7
MERGE_API_KEY=xxx
MERGE_ACCOUNT_TOKEN=xxx
GUPY_API_KEY=xxx
PANDAPE_API_KEY=xxx

# Voice STT real-time (Gemini Live Audio) — adicionado v3.7
# (usa AI_INTEGRATIONS_GEMINI_API_KEY já listado em LLMs)

# Observabilidade — adicionado v3.7
SENTRY_DSN=https://xxx@sentry.io/yyy
LANGCHAIN_API_KEY=ls__xxx          # LangSmith
OTEL_EXPORTER_OTLP_ENDPOINT=        # vazio = OTel desabilitado

# Search & infra — adicionado v3.7
ELASTICSEARCH_URL=https://...
REDIS_URL=redis://...
REDIS_ENCRYPTION_KEY=               # Fernet — OBRIGATÓRIO em prod (PII em Redis)
RABBITMQ_URL=amqp://...
DATABASE_URL=postgresql+asyncpg://...
```

> ⚠️ Versões 3.0–3.6 listavam `STACKONE_API_KEY` — produto correto é **Merge.dev** (`app/domains/ats_integration/services/ats_clients/merge.py`). “StackOne” aparece em algumas tabelas legadas como duplicação errada do mesmo concorrente — desconsiderar.

---

## Apêndice E: Glossário

| Termo | Definição |
|-------|-----------|
| **ATS** | Applicant Tracking System |
| **HRIS** | Human Resources Information System |
| **LLM** | Large Language Model |
| **MRR** | Monthly Recurring Revenue |
| **SCIM** | System for Cross-domain Identity Management |
| **SSO** | Single Sign-On |
| **STT** | Speech-to-Text |
| **WSI** | Work Sample Interview |

---

## Apêndice F: Ferramentas Futuras e Recomendadas

> **Baseado em análise de concorrentes:** Tezi.ai, Popp AI, Findem, Paradox, HireZ, JuiceBox, Eightfold, GoodTime, Braintrust, Wellfound
> **Filosofia:** Priorizar ferramentas com free tiers robustos e alternativas brasileiras quando disponíveis

---

### F.1 Monitoring & Alerting (Incidentes)

**Função:** Alertas e gerenciamento de incidentes para times de Engineering & CS

| Ferramenta | Website | Preço (user/mês) | Free Tier | Prioridade | Recomendação |
|------------|---------|------------------|-----------|------------|--------------|
| **Squadcast** ⭐ | squadcast.com | $9-21 | 5 users | 🟡 Média | **RECOMENDADO** - Melhor custo-benefício, SRE-focused |
| **Better Stack** | betterstack.com | $19 | Sim | 🟡 Média | Monitoring + alerting unificado |
| **Zenduty/Xurrent** | zenduty.com | $5 | Sim | 🟢 Baixa | Mais barato, 150+ integrações |
| PagerDuty | pagerduty.com | $21-41 | 5 users | 🔴 Alta | Enterprise standard, caro |
| Opsgenie | opsgenie.com | $9-29 | Básico | ❌ Evitar | **Descontinuado em 2027** |
| Grafana On-Call | grafana.com | $29/mês | Sim | 🟢 Baixa | Se já usa Grafana |

**Decisão WeDo Talent:** Começar com **Squadcast** ($9/user) por ser mais acessível que PagerDuty e ter ferramentas de SRE robustas.

**Alternativas Open-Source:**
- **ElastAlert** - Para quem usa Elasticsearch
- **Cabot** - Self-hosted básico
- **Dispatch (Netflix)** - Para incidentes via Slack

---

### F.2 Monitoring & Observability (APM)

**Função:** Monitoramento de aplicação, logs, traces e métricas da stack

| Ferramenta | Website | Preço | Free Tier | Prioridade | Recomendação |
|------------|---------|-------|-----------|------------|--------------|
| **SigNoz** ⭐ | signoz.io | Self-host grátis | Ilimitado | 🟡 Média | **RECOMENDADO** - Open-source, OpenTelemetry nativo |
| **New Relic** | newrelic.com | Usage-based | 100GB/mês | 🟡 Média | Bom free tier, 750+ integrações |
| **Sematext** | sematext.com | $3.60/host | Trial | 🟢 Baixa | Mais barato por host |
| Datadog | datadoghq.com | $15+/host | Trial | 🔴 Alta | Completo mas caro, billing imprevisível |
| Dynatrace | dynatrace.com | $69/mês | Trial | 🔴 Alta | Enterprise, AI-powered |
| AWS CloudWatch | aws.amazon.com | Pay-as-you-go | Básico | 🟢 Baixa | Apenas se 100% AWS |

**Decisão WeDo Talent:** Começar com **New Relic Free** (100GB/mês) ou **SigNoz** self-hosted. Migrar para pago conforme crescimento.

**Métricas a monitorar:**
- APM: Response time, error rate, throughput
- Logs: Erros, warnings, audit trails
- Infra: CPU, memory, disk, network
- User sessions: Page load, Core Web Vitals

---

### F.3 E-Signature (Assinatura Eletrônica)

**Função:** Assinatura digital de contratos, propostas e documentos

| Ferramenta | Website | Preço (user/mês) | ICP-Brasil | Prioridade | Recomendação |
|------------|---------|------------------|------------|------------|--------------|
| **SignNow** ⭐ | signnow.com | $8 | Limitado | 🟡 Média | **RECOMENDADO** - Melhor custo-benefício |
| **Certinal** | certinal.com | Enterprise | ✅ Completo | 🔴 Alta | Melhor para compliance Brasil |
| DocuSign | docusign.com | $10+ | ✅ Sim | 🔴 Alta | Líder de mercado |
| PandaDoc | pandadoc.com | $19 | ✅ Sim | 🟡 Média | Propostas + assinaturas |
| Dropbox Sign | hellosign.com | $22 | Verificar | 🟢 Baixa | Assinaturas ilimitadas |
| **Signaturely** | signaturely.com | $20 | Verificar | 🟢 Baixa | Bom para startups |
| **DocuSeal** | docuseal.com | Open-source | Self-hosted | 🟢 Baixa | Grátis, API-first |

**Requisitos Legais Brasil (Lei 14.063/2020):**
- **SES** (Simples): Contratos de baixo risco, HR, vendas
- **AES** (Avançado): MFA obrigatório, maioria dos contratos B2B
- **QES** (Qualificado/ICP-Brasil): Contratos com governo, câmbio, financeiro

**Decisão WeDo Talent:** 
- **Contratos simples:** SignNow ($8/user)
- **Clientes enterprise/financeiro:** Certinal ou DocuSign com ICP-Brasil

**Alternativas Brasileiras:**
- **ClickSign** - clicksign.com - Focada no Brasil
- **D4Sign** - d4sign.com.br - ICP-Brasil nativo
- **Autentique** - autentique.com.br - Gratuito até 5 docs/mês

---

### F.4 Issue Tracking & Product Roadmap

**Função:** Gestão de produto, roadmap, bugs e feature requests

| Ferramenta | Website | Preço (user/mês) | Free Tier | Prioridade | Recomendação |
|------------|---------|------------------|-----------|------------|--------------|
| **Linear** ⭐ | linear.app | $8-12 | 250 issues | 🟡 Média | **RECOMENDADO** - UI moderna, dev-first |
| **Plane** | plane.so | Self-host grátis | Ilimitado | 🟢 Baixa | Open-source Linear alternative |
| Jira | atlassian.com/jira | $8.15 | 10 users | 🟡 Média | Enterprise, customizável |
| ClickUp | clickup.com | $7-12 | Sim | 🟢 Baixa | All-in-one, não só dev |
| Asana | asana.com | $10.99 | 15 users | 🟢 Baixa | Cross-functional |
| GitHub Issues | github.com | Incluído | Sim | ✅ Já usado | Básico mas integrado |
| **Productboard** | productboard.com | $20+ | Starter | 🟡 Média | Foco em product discovery |

**Decisão WeDo Talent:** 
- **Atual:** GitHub Issues (grátis, já integrado)
- **Futuro:** Linear ($8/user) quando precisar de roadmaps públicos e melhor UX

**Open-Source:**
- **Plane** (30k+ GitHub stars) - plane.so
- **Tegon** - tegon.ai - Dev-first, automações
- **OpenProject** - openproject.org - Enterprise features

---

### F.5 Customer Support & Help Desk

**Função:** Suporte ao cliente, Help Center, chat e tickets

| Ferramenta | Website | Preço (agent/mês) | Free Tier | Prioridade | Recomendação |
|------------|---------|-------------------|-----------|------------|--------------|
| **BoldDesk** ⭐ | bolddesk.com | $12 | Trial 90d | 🟡 Média | **RECOMENDADO** - Mais barato, AI incluso |
| **Crisp** | crisp.chat | $25 | Sim | 🟡 Média | Chat moderno, bom preço |
| **Freshdesk** | freshdesk.com | $12+ | 10 agents | 🟢 Baixa | Robusto, free tier generoso |
| Zendesk | zendesk.com | $19-149 | Trial | 🔴 Alta | Enterprise standard |
| Intercom | intercom.com | $74+ | ❌ | 🔴 Alta | Caro, pricing complexo |
| HubSpot Service | hubspot.com | $15-150 | 2 users | 🟡 Média | Já temos HubSpot CRM |
| **Help Scout** | helpscout.com | $22 | Trial | 🟢 Baixa | Pricing transparente |

**Decisão WeDo Talent:**
- **Fase 1:** HubSpot Service Hub Free (já integrado ao CRM)
- **Fase 2:** Se precisar escalar → BoldDesk ($12) ou Crisp ($25)

**Para E-commerce/SaaS específico:**
- **Gorgias** - E-commerce (Shopify nativo)
- **Tidio** - Chatbots AI sem custo por resolução

**Alternativas Brasileiras:**
- **Zenvia** - zenvia.com - Omnichannel BR
- **Movidesk** - movidesk.com - Help desk brasileiro
- **Octadesk** - octadesk.com - Chat + tickets

---

### F.6 Low-Code & Internal Tools

**Função:** Construção de apps internos, workflows e integrações

| Ferramenta | Website | Preço | Free Tier | Prioridade | Recomendação |
|------------|---------|-------|-----------|------------|--------------|
| **Appsmith** ⭐ | appsmith.com | $15/user | Self-host | 🟡 Média | **RECOMENDADO** - Open-source, flexível |
| **UI Bakery** | uibakery.io | $5/user + $10/dev | 5 users | 🟡 Média | Mais barato que Retool |
| **Budibase** | budibase.com | $0.40/hora (max $20) | Open-source | 🟢 Baixa | Usage-based justo |
| Retool | retool.com | $50/user | 5 users | 🔴 Alta | Poderoso mas caro |
| **Noloco** | noloco.io | $49/mês flat | Trial | 🟢 Baixa | Airtable/Sheets users |
| **ToolJet** | tooljet.com | Self-host grátis | Ilimitado | 🟢 Baixa | AI-powered, on-prem |

**Decisão WeDo Talent (conforme análise SaaS stack):**
- **Não usar Retool** - Substituído por ferramentas SaaS especializadas
- **Admin CRUD:** HubSpot (já integrado)
- **Dashboards internos:** Appsmith self-hosted ou UI Bakery

**Casos de uso que resolvemos com SaaS:**
| Antes (Retool) | Depois (SaaS) |
|----------------|---------------|
| Dashboard clientes | HubSpot CRM |
| Onboarding tracking | HubSpot Tickets + Workflows |
| Métricas SaaS | ProfitWell |
| Compliance | Vanta/Drata |

---

### F.7 Security & Compliance Automation

**Função:** Automação de compliance SOC 2, ISO 27001, LGPD, BCB 498

| Ferramenta | Website | Preço (ano) | Cobertura | Prioridade | Recomendação |
|------------|---------|-------------|-----------|------------|--------------|
| **Vanta** ⭐ | vanta.com | $15-50k | SOC2, ISO, LGPD | 🔴 Alta | **RECOMENDADO** - Líder, completo |
| **Drata** | drata.com | $15-50k | SOC2, ISO, GDPR | 🔴 Alta | Alternativa ao Vanta |
| **Scrut** | scrut.io | $10-30k | 50+ frameworks | 🟡 Média | 70% automação tarefas |
| Secureframe | secureframe.com | Similar | SOC2, HIPAA | 🟡 Média | Foco em startups |
| **Privacy Tools** | privacytools.com.br | Verificar | LGPD específico | 🔴 Alta | **Brasil-focused** |

**Requisitos WeDo Talent:**
- ✅ SOC 2 Type II (clientes enterprise)
- ✅ LGPD (lei brasileira)
- ✅ BCB 498/2025 (bancos)
- ⬜ ISO 27001 (futuro)

**Decisão WeDo Talent:** Vanta ou Drata + Privacy Tools para LGPD específico

**Ferramentas Complementares:**
| Categoria | Ferramenta | Função |
|-----------|------------|--------|
| **DSAR Automation** | DataGrail, Osano | Solicitações de dados LGPD |
| **Consent Management** | OneTrust, Cookiebot | Cookies e consentimento |
| **Vulnerability Scanning** | Snyk, Dependabot | Segurança de código |
| **Penetration Testing** | HackerOne, Bugcrowd | Bug bounty programs |

---

### F.8 AI Bias Auditing

**Função:** Auditoria de viés em algoritmos de recrutamento

| Ferramenta | Website | Preço | Compliance | Prioridade | Recomendação |
|------------|---------|-------|------------|------------|--------------|
| **Warden AI** ⭐ | warden.ai | Sob consulta | NYC LL144, EU AI Act | 🔴 Alta | **RECOMENDADO** - Usado por Popp AI |
| **Holistic AI** | holisticai.com | Enterprise | EU AI Act | 🟡 Média | Consultoria + software |
| **ORCAA** | orcaarisk.com | Sob consulta | NYC LL144 | 🟡 Média | Pioneiro NYC compliance |

**Por que é importante:**
- **NYC Local Law 144:** Auditorias anuais obrigatórias para AEDTs (Automated Employment Decision Tools)
- **EU AI Act:** IA de recrutamento = "alto risco"
- **Brasil:** Discussões em andamento na ANPD

**Decisão WeDo Talent:** Warden AI na Fase 2 (antes de expansão internacional)

---

### F.9 Communication & Messaging Infrastructure

**Função:** Infraestrutura de comunicação multi-canal

| Ferramenta | Website | Preço | Canais | Prioridade | Status |
|------------|---------|-------|--------|------------|--------|
| **Mailgun** | sendgrid.com | $0 (5.000/mês) | Email | ✅ Essencial | Já planejado |
| **Twilio** | twilio.com | Pay-as-you-go | SMS, Voice, WhatsApp | ✅ Essencial | Já planejado |
| **Postmark** | postmarkapp.com | $15/mês | Email transacional | 🟢 Baixa | Alternativa Mailgun |
| **MessageBird** | messagebird.com | Pay-as-you-go | Omnichannel | 🟢 Baixa | Alternativa Twilio |

**Alternativas Brasileiras:**
- **Zenvia** - zenvia.com - SMS/WhatsApp Brasil
- **Infobip** - infobip.com - Omnichannel global

---

### F.10 Background Check & Verification

**Função:** Verificação de antecedentes e validação de candidatos

| Ferramenta | Website | Preço | Cobertura | Prioridade | Recomendação |
|------------|---------|-------|-----------|------------|--------------|
| **Checkr** | checkr.com | Por verificação | EUA/Internacional | 🟡 Média | Líder de mercado |
| **Certn** | certn.co | Por verificação | Global | 🟡 Média | Mais rápido |
| **Good Hire** | goodhire.com | $29.99+ | EUA | 🟢 Baixa | SMB-focused |

**Alternativas Brasileiras:**
- **Valid** - valid.com - Background check BR
- **Certisign** - certisign.com.br - Verificação ICP-Brasil
- **Idwall** - idwall.co - KYC e verificação

---

### F.11 Video Interviewing (além de OpenMic)

**Função:** Entrevistas em vídeo assíncronas e ao vivo

| Ferramenta | Website | Preço | Tipo | Prioridade | Status |
|------------|---------|-------|------|------------|--------|
| **OpenMic** | openmic.ai | Sob consulta | Voice screening | ✅ Essencial | Já integrado |
| **HireVue** | hirevue.com | Enterprise | Video + AI | 🔴 Alta | Líder enterprise |
| **Spark Hire** | sparkhire.com | $149+/mês | Video assíncrono | 🟡 Média | Mais acessível |
| **Willo** | willo.video | $75+/mês | Video assíncrono | 🟢 Baixa | SMB-focused |
| **Ribbon AI** | ribbon.ai | Sob consulta | AI interviews | 🟡 Média | Usado por Wellfound |
| **Braintrust AIR** | braintrust.dev | Sob consulta | First-round AI | 🟢 Baixa | Eliminação de viés |

---

### F.12 Cloud & Infraestrutura

**Função:** Hospedagem, armazenamento, CDN e processamento

| Ferramenta | Website | Preço | Usado Por | Status WeDo | Recomendação |
|------------|---------|-------|-----------|-------------|--------------|
| **AWS** | aws.amazon.com | Pay-as-you-go | Tezi, HireZ, JuiceBox, Eightfold, Braintrust, Wellfound | 🟡 Avaliar | Standard enterprise |
| **Google Cloud** | cloud.google.com | Pay-as-you-go | JuiceBox, Wellfound | 🟢 Opcional | Alternativa AWS |
| **Azure** | azure.microsoft.com | Pay-as-you-go | Eightfold, Wellfound | 🟢 Opcional | Se já usa Microsoft |
| **Vercel** | vercel.com | $0-20/mês | Braintrust | 🟢 Opcional | Deploy frontend |
| **Supabase** | supabase.com | Free tier | Braintrust | 🟢 Opcional | PostgreSQL + Auth |
| **Cloudflare** | cloudflare.com | Free tier | HireZ | ✅ Recomendado | CDN + Security |

**Decisão WeDo Talent:** Replit para desenvolvimento. Para produção, avaliar AWS ou manter Replit Deployments.

---

### F.13 Calendar & Scheduling APIs

**Função:** Integração com calendários para agendamento de entrevistas

| Ferramenta | Website | Preço | Calendários | Usado Por | Recomendação |
|------------|---------|-------|-------------|-----------|--------------|
| **Nylas** ⭐ | nylas.com | $0.50/conta ativa | Google, Outlook, Exchange | HireZ | **RECOMENDADO** - Mais completo |
| **Kombo** | kombo.dev | Sob consulta | + HRIS integrado | HireZ | Alternativa unificada |
| **MS Graph** | microsoft.com | Incluído M365 | Outlook/Teams | Tezi (via M365) | ✅ Já planejado |
| **Google Calendar API** | developers.google.com | Grátis | Google Calendar | Tezi (via Workspace) | ✅ Já planejado |
| **Cal.com** | cal.com | Free tier | Multi-calendar | - | Open-source alternativa |

**Decisão WeDo Talent:** MS Graph (já planejado) + Nylas se precisar Google Calendar sync.

---

### F.14 Analytics & Product Intelligence

**Função:** Analytics de produto, erros, e pipelines de dados

| Ferramenta | Website | Preço | Função | Usado Por | Recomendação |
|------------|---------|-------|--------|-----------|--------------|
| **PostHog** ⭐ | posthog.com | Free 1M eventos | Product analytics | JuiceBox | **RECOMENDADO** - Self-host option |
| **Rollbar** | rollbar.com | $13+/mês | Error tracking | Wellfound | Alternativa Sentry |
| **Sentry** | sentry.io | Free tier | Error tracking | - | Standard error tracking |
| **dbt** | getdbt.com | Free (Core) | Data pipelines | Wellfound | Data transformation |
| **Metabase** | metabase.com | Free (Open-source) | BI/Reporting | - | Alternativa open-source |
| **DataIris** | datairis.ai | Sob consulta | BI generativo | Eightfold | BI com IA |

#### Dashboards Self-Service & Embedded Analytics

| Ferramenta | Website | Preço | Função | Diferencial | Recomendação |
|------------|---------|-------|--------|-------------|--------------|
| **Embeddable** ⭐ | embeddable.com | Sob consulta (flat) | Embedded dashboards | **Preço fixo** sem custo por usuário, SOC 2 | **RECOMENDADO** - Para clientes |
| **Trevor.io** ⭐ | trevor.io | Free + $75-250/mês | Self-service analytics | No-code query builder, Slack, Zapier | **RECOMENDADO** - Time interno |
| **Retool Embedded** | retool.com | $50+/user | Embedded apps | Low-code, dashboards internos | Se já usa Retool |
| **Explo** | explo.co | Sob consulta | Embedded analytics | White-label, multi-tenant | Alternativa Embeddable |
| **Sisense** | sisense.com | Enterprise | Embedded BI | AI-powered, enterprise | Enterprise apenas |

**Detalhes das Ferramentas:**

**Embeddable.com:**
- ✅ Preço fixo mensal (sem custo por usuário/view)
- ✅ Web components nativos (não iFrames)
- ✅ React/Vue embeds, headless architecture
- ✅ Row-level security, multi-tenant
- ✅ SOC 2 Type II, GDPR
- ✅ Conecta: PostgreSQL, MySQL, BigQuery, Snowflake, ClickHouse, etc.
- 🎯 **Ideal para:** Dashboards customer-facing no WeDo Talent

**Trevor.io:**
- ✅ Free tier: 3,000 créditos/mês
- ✅ Query builder no-code + SQL avançado
- ✅ Dashboards shareable (clientes, investidores)
- ✅ Google Sheets sync, Slack alerts, Zapier
- ✅ Embedded dashboards sem código
- ✅ Usado por GoodTime
- 🎯 **Ideal para:** Analytics interno e self-service para time

#### Analytics Brasil (Contabilidade & Gestão)

| Ferramenta | Website | Preço | Função | Diferencial | Recomendação |
|------------|---------|-------|--------|-------------|--------------|
| **HubCount BI** ⭐ | hubcount.com.br | Sob consulta | BI contábil/empresarial | **IA conversacional PT-BR**, 100+ ERPs | Se precisar analytics contábil |

**HubCount BI (Brasil):**
- ✅ IA generativa em português (entende DRE, eSocial, CNPJ)
- ✅ +100 indicadores prontos (contábil, folha, financeiro)
- ✅ +100 ERPs brasileiros integrados
- ✅ White-label para escritórios
- ✅ LGPD compliant
- ✅ +250 mil empresas impactadas no Brasil
- 🎯 **Ideal para:** Se WeDo Talent precisar analytics contábil para clientes

**Decisão WeDo Talent:** 
- **Product analytics:** PostHog (free tier generoso, self-host option)
- **Error tracking:** Sentry (standard, free tier)
- **Self-service interno:** Trevor.io (free tier, no-code)
- **Embedded para clientes:** Embeddable (preço fixo, SOC 2)
- **BI Brasil (opcional):** HubCount se precisar analytics contábil

---

### F.15 Sales Enablement & Outbound

**Função:** Ferramentas de vendas, outreach e intelligence

| Ferramenta | Website | Preço | Função | Usado Por | Prioridade |
|------------|---------|-------|--------|-----------|------------|
| **Gong** | gong.io | Enterprise | Conversation intelligence | Wellfound | 🔴 Alta (futuro) |
| **RB2B** | rb2b.com | Sob consulta | Website visitor ID | Wellfound | 🟢 Baixa |
| **Amplemarket** | amplemarket.com | Sob consulta | Email campaigns | GoodTime | 🟡 Média |
| **Apollo.io** | apollo.io | Free tier | Outbound sales | - | 🟡 Média |
| **Outreach** | outreach.io | Enterprise | Sales engagement | - | 🔴 Alta (enterprise) |

**Decisão WeDo Talent:** HubSpot já cobre CRM e sales básico. Gong para fase enterprise.

---

### F.16 Form Building & Surveys

**Função:** Formulários, pesquisas e coleta de dados

| Ferramenta | Website | Preço | Função | Usado Por | Recomendação |
|------------|---------|-------|--------|-----------|--------------|
| **Typeform** ⭐ | typeform.com | $25+/mês | Forms avançados | Tezi | **RECOMENDADO** - UX superior |
| **Tally** | tally.so | Free tier | Forms gratuitos | - | Alternativa grátis |
| **Jotform** | jotform.com | Free tier | Forms tradicionais | - | Alternativa robusta |
| **Google Forms** | google.com/forms | Grátis | Forms básicos | - | MVP option |
| **Fillout** | fillout.com | Free tier | Forms + Airtable | - | Integrações nativas |

**Decisão WeDo Talent:** Typeform para experiência premium. Tally/Google Forms para MVP.

---

### F.17 Meeting Notes & Transcription

**Função:** Notas de reunião, transcrição e resumos com IA

| Ferramenta | Website | Preço | Função | Usado Por | Recomendação |
|------------|---------|-------|--------|-----------|--------------|
| **Circleback** ⭐ | circleback.ai | $25+/mês | AI meeting notes | Tezi | **RECOMENDADO** - Focado em reuniões |
| **Fireflies.ai** | fireflies.ai | Free tier | Transcription + AI | - | Alternativa popular |
| **Otter.ai** | otter.ai | Free tier | Transcription | - | Boa opção grátis |
| **Grain** | grain.com | $15+/mês | Video highlights | - | Para sales calls |
| **Fathom** | fathom.video | Free | Meeting recorder | - | 100% grátis |

**Decisão WeDo Talent:** Deepgram já planejado para transcrição. Circleback para notas de reuniões internas.

---

### F.18 Voice AI & TTS

**Função:** Geração de voz com IA, text-to-speech

| Ferramenta | Website | Preço | Função | Usado Por | Prioridade |
|------------|---------|-------|--------|-----------|------------|
| **Eleven Labs** ⭐ | elevenlabs.io | $5+/mês | Voice AI premium | Eightfold | 🟡 Média |
| **Play.ht** | play.ht | $14+/mês | TTS/Voice clone | - | 🟢 Baixa |
| **Murf.ai** | murf.ai | $23+/mês | Voice over | - | 🟢 Baixa |
| **Deepgram** | deepgram.com | Pay-as-you-go | STT | ✅ Já planejado | ✅ Essencial |

**Decisão WeDo Talent:** Deepgram para STT. Eleven Labs se precisar voz sintetizada para LIA.

---

### F.19 Database & Search Infrastructure

**Função:** Bancos de dados, cache e search engines

| Ferramenta | Website | Preço | Função | Usado Por | Status |
|------------|---------|-------|--------|-----------|--------|
| **Elastic** | elastic.co | Free tier | Search engine | Wellfound | 🟡 Avaliar |
| **Redis** | redis.com | Free tier | Cache/NoSQL | Wellfound | ✅ Já usado |
| **MongoDB** | mongodb.com | Free tier | NoSQL database | HireZ | 🟢 Opcional |
| **DataStax** | datastax.com | Free tier | Cassandra-based | HireZ | 🟢 Opcional |
| **Pinecone** | pinecone.io | Free tier | Vector DB | - | 🟡 Embeddings |

**Decisão WeDo Talent:** PostgreSQL + Redis (já planejado). Elastic se precisar search avançado.

---

### F.20 Knowledge Base & Documentation

**Função:** Base de conhecimento para clientes e suporte

| Ferramenta | Website | Preço | Função | Usado Por | Recomendação |
|------------|---------|-------|--------|-----------|--------------|
| **Notion** | notion.so | Free tier | Docs + KB | Tezi, Wellfound | ✅ Recomendado |
| **Helpjuice** | helpjuice.com | $120+/mês | KB enterprise | Eightfold | 🟢 Baixa |
| **GitBook** | gitbook.com | Free tier | Docs técnicos | - | Para developers |
| **Slite** | slite.com | Free tier | KB interno | - | Alternativa Notion |

**Decisão WeDo Talent:** Notion para docs internos. HubSpot KB para clientes (já integrado).

---

### F.21 Resumo Comparativo: Subprocessadores dos Concorrentes

> Análise baseada em Tezi (19), Wellfound (25+), Eightfold (9), GoodTime (9), HireZ (8), JuiceBox (6)

| Categoria | Líderes | Usado Por | WeDo Talent Status |
|-----------|---------|-----------|-------------------|
| **Cloud** | AWS | 6 plataformas | Replit (dev) |
| **LLM** | OpenAI | 4 plataformas | ✅ Claude/Gemini |
| **ATS Integração** | Merge | 3 plataformas | ✅ Merge |
| **CRM** | HubSpot, Salesforce | 5 plataformas | ✅ HubSpot |
| **Email** | Mailgun, Twilio | 4 plataformas | ✅ Planejado |
| **Auth** | WorkOS | 1 plataforma | ✅ Já integrado |
| **Monitoring** | Datadog | 2 plataformas | 🔜 New Relic/SigNoz |
| **Support** | Intercom | 3 plataformas | 🔜 HubSpot Service |
| **Pagamentos** | Stripe | 3 plataformas | ✅ Já integrado |
| **Issue Tracking** | Linear | 1 plataforma | 🔜 Linear |
| **E-Signature** | PandaDoc | 1 plataforma | 🔜 SignNow |

**Insights:**
- ✅ **Já alinhados:** LLM, CRM, Auth, ATS, Pagamentos
- 🔜 **Próximos:** Monitoring, Support, Issue Tracking
- 🟡 **Avaliar:** Voice AI (Eleven Labs), Calendar API (Nylas)

---

### F.22 Matriz de Priorização

| Prioridade | Ferramentas | Justificativa | Timeline |
|------------|-------------|---------------|----------|
| 🔴 **Alta** | Vanta/Drata, Privacy Tools, Certinal | Compliance obrigatório para enterprise | Q1 2026 |
| 🔴 **Alta** | Warden AI | NYC LL144, EU AI Act | Q2 2026 |
| 🟡 **Média** | Squadcast, SigNoz | Operação estável | Q2 2026 |
| 🟡 **Média** | SignNow, Linear | UX e produtividade | Q3 2026 |
| 🟢 **Baixa** | Background check, alternatives | Nice-to-have | Q4 2026+ |

---

### F.23 Custos Estimados (Ferramentas Futuras)

| Categoria | Ferramenta Recomendada | Custo Mensal | Custo Anual |
|-----------|------------------------|--------------|-------------|
| Monitoring (Alertas) | Squadcast | $90 (10 users) | $1,080 |
| Monitoring (APM) | New Relic Free | $0 | $0 |
| E-Signature | SignNow | $80 (10 users) | $960 |
| Issue Tracking | Linear | $80 (10 users) | $960 |
| Customer Support | HubSpot Service Free | $0 | $0 |
| Compliance | Vanta | $1,250 | $15,000 |
| AI Bias Audit | Warden AI | $500 (est.) | $6,000 |
| Product Analytics | PostHog | $0 | $0 |
| Forms | Typeform | $25 | $300 |
| Meeting Notes | Circleback | $25 | $300 |
| Voice AI | Eleven Labs | $50 | $600 |
| **TOTAL ESTIMADO** | | **$2,100/mês** | **$25,200/ano** |

**Observação:** Custos podem variar. Muitas ferramentas têm free tiers generosos para começar.

---

### F.24 Contatos Comerciais (Ferramentas Futuras)

| Ferramenta | Website | Sales Contact |
|------------|---------|---------------|
| Squadcast | squadcast.com | sales@squadcast.com |
| Vanta | vanta.com | sales@vanta.com |
| Drata | drata.com | sales@drata.com |
| Warden AI | warden.ai | contact@warden.ai |
| Linear | linear.app | sales@linear.app |
| SignNow | signnow.com | sales@signnow.com |
| Certinal | certinal.com | sales@certinal.com |
| Privacy Tools | privacytools.com.br | contato@privacytools.com.br |
| PostHog | posthog.com | sales@posthog.com |
| Nylas | nylas.com | sales@nylas.com |
| Typeform | typeform.com | sales@typeform.com |
| Circleback | circleback.ai | hello@circleback.ai |
| Eleven Labs | elevenlabs.io | sales@elevenlabs.io |
| New Relic | newrelic.com | sales@newrelic.com |
| SigNoz | signoz.io | hello@signoz.io |
| Gong | gong.io | sales@gong.io |
| Embeddable | embeddable.com | sales@embeddable.com |
| Trevor.io | trevor.io | support@trevor.io |
| HubCount | hubcount.com.br | contato@hubcount.com.br |
| Explo | explo.co | sales@explo.co |

---

## Apêndice G: Guia Passo a Passo - Ruby on Rails (Produção)

> **Objetivo:** Ordem de implementação para o time de desenvolvimento Vue.js/Nuxt + Ruby on Rails  
> **Filosofia:** Capítulo 1 (70% SaaS) → Capítulo 2 (70% Interno)  
> **Prazo Total Estimado:** 12-16 semanas

### G.1 Pré-requisitos de Ambiente

```bash
# Ruby on Rails Backend
ruby --version   # 3.2+ recomendado
rails --version  # 7.1+ recomendado
bundle --version

# Frontend Vue.js/Nuxt
node --version   # 20+
npm --version

# Database
psql --version   # PostgreSQL 15+

# Cache/Queue
redis-cli --version
```

### G.2 Ordem de Implementação - Capítulo 1 (Admin)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                  CAPÍTULO 1: ADMIN - ORDEM DE IMPLEMENTAÇÃO (70% SaaS)                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   SEMANA 1-2: FUNDAÇÃO                                                                   │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 1: Stripe Billing (3-5 dias)                                              │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Base de todo o Admin                                   │   │
│   │                                                                                  │   │
│   │  □ 1.1 Criar conta Stripe + Test Mode                                            │   │
│   │  □ 1.2 Configurar Products & Prices (Starter, Professional, Enterprise)         │   │
│   │  □ 1.3 Ativar Customer Portal                                                    │   │
│   │  □ 1.4 Configurar Webhooks endpoint (/api/webhooks/stripe)                       │   │
│   │  □ 1.5 Implementar model Subscription (Rails)                                    │   │
│   │  □ 1.6 Implementar webhook handler: subscription.created/updated/deleted         │   │
│   │  □ 1.7 Implementar webhook handler: invoice.paid/payment_failed                  │   │
│   │  □ 1.8 Testar fluxo completo checkout → portal                                   │   │
│   │                                                                                  │   │
│   │  Secrets Necessários:                                                            │   │
│   │  • STRIPE_SECRET_KEY (sk_test_xxx / sk_live_xxx)                                 │   │
│   │  • STRIPE_PUBLISHABLE_KEY (pk_test_xxx / pk_live_xxx)                            │   │
│   │  • STRIPE_WEBHOOK_SECRET (whsec_xxx)                                             │   │
│   │                                                                                  │   │
│   │  Gems Rails:                                                                     │   │
│   │  • stripe (~> 10.0)                                                              │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Criar subscription via checkout funciona                                     │   │
│   │  ✓ Webhooks recebidos e processados                                             │   │
│   │  ✓ Customer Portal acessível via link                                           │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 2: ProfitWell Metrics (1 dia)                                             │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟢 BAIXA - Apenas conectar, zero código                             │   │
│   │                                                                                  │   │
│   │  □ 2.1 Criar conta ProfitWell (profitwell.com)                                   │   │
│   │  □ 2.2 Conectar ao Stripe (1-click integration)                                  │   │
│   │  □ 2.3 Aguardar 24h para métricas aparecerem                                     │   │
│   │  □ 2.4 Configurar alertas de churn                                               │   │
│   │                                                                                  │   │
│   │  Custo: $0 (gratuito para sempre)                                                │   │
│   │  Código: 0 linhas                                                                │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Dashboard mostrando MRR, Churn, LTV                                           │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 2-3: CRM & ONBOARDING                                                           │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 3: HubSpot CRM (5-7 dias)                                                 │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Central de clientes                                       │   │
│   │                                                                                  │   │
│   │  □ 3.1 Criar conta HubSpot + Private App                                         │   │
│   │  □ 3.2 Criar propriedades customizadas (Companies & Contacts)                    │   │
│   │  □ 3.3 Criar Pipeline "WeDo Talent Contracts"                                    │   │
│   │  □ 3.4 Implementar service HubspotService (Rails)                                │   │
│   │  □ 3.5 Sync bidirecional: Rails ↔ HubSpot                                        │   │
│   │  □ 3.6 Implementar StripeSyncService: Stripe → Rails → HubSpot                   │   │
│   │  □ 3.7 Webhook: HubSpot → Rails (deal closed)                                    │   │
│   │                                                                                  │   │
│   │  Secrets Necessários:                                                            │   │
│   │  • HUBSPOT_ACCESS_TOKEN (pat-na1-xxx)                                            │   │
│   │  • HUBSPOT_PORTAL_ID                                                             │   │
│   │                                                                                  │   │
│   │  Gems Rails:                                                                     │   │
│   │  • hubspot-api-client (~> 17.0)                                                  │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Criar cliente no Rails cria Company no HubSpot                                │   │
│   │  ✓ Pipeline de deals funcionando                                                 │   │
│   │  ✓ Propriedades customizadas sincronizando                                       │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 4: HubSpot Onboarding - Tickets + Workflows (2-3 dias)                    │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 MÉDIA - Pode postergar para depois de WorkOS                     │   │
│   │                                                                                  │   │
│   │  □ 4.1 Criar Pipeline de Tickets "Onboarding Cliente" (7 stages)                 │   │
│   │  □ 4.2 Criar propriedades customizadas nos Tickets                               │   │
│   │  □ 4.3 Criar Workflow: Deal fechado → Criar Ticket                               │   │
│   │  □ 4.4 Criar Workflow: Ticket stage changed → Enviar email                       │   │
│   │  □ 4.5 Criar Workflow: Onboarding completo → Atualizar Company                   │   │
│   │  □ 4.6 Configurar templates de email para cada stage                             │   │
│   │                                                                                  │   │
│   │  Secrets Necessários:                                                            │   │
│   │  • (Nenhum adicional - usa HubSpot já configurado)                               │   │
│   │                                                                                  │   │
│   │  Custo: $0 (incluso no HubSpot CRM Free)                                         │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Deal fechado no HubSpot cria Ticket de onboarding                             │   │
│   │  ✓ Mudança de stage dispara email automático                                     │   │
│   │  ✓ Ticket completo atualiza status da Company                                    │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 4-5: AUTENTICAÇÃO ENTERPRISE                                                    │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 5: WorkOS SSO/SCIM (7-10 dias)                                            │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Necessário para clientes enterprise                    │   │
│   │                                                                                  │   │
│   │  □ 5.1 Criar conta WorkOS + Environment (staging/production)                     │   │
│   │  □ 5.2 Configurar Redirect URIs                                                  │   │
│   │  □ 5.3 Implementar WorkosService (Rails)                                         │   │
│   │  □ 5.4 SSO Flow: /auth/sso/start → callback → session                            │   │
│   │  □ 5.5 Admin Kit: Auto-provisionamento de Organizations                          │   │
│   │  □ 5.6 SCIM: Directory Sync endpoint (/api/scim/v2)                              │   │
│   │  □ 5.7 MFA: Configurar para admins                                               │   │
│   │  □ 5.8 Audit Logs: Implementar tracking                                          │   │
│   │  □ 5.9 Testar com IdP de cliente sandbox (via WorkOS)                            │   │
│   │                                                                                  │   │
│   │  Secrets Necessários:                                                            │   │
│   │  • WORKOS_API_KEY                                                                │   │
│   │  • WORKOS_CLIENT_ID                                                              │   │
│   │  • WORKOS_WEBHOOK_SECRET                                                         │   │
│   │                                                                                  │   │
│   │  Gems Rails:                                                                     │   │
│   │  • workos (~> 5.0)                                                               │   │
│   │                                                                                  │   │
│   │  Custo: $50/conexão SSO ativa (~$500/mês com 10 clientes enterprise)             │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ SSO login funciona com IdP de teste                                           │   │
│   │  ✓ SCIM provisioning cria/remove usuários                                        │   │
│   │  ✓ Audit logs registrando eventos                                               │   │
│   │  ✓ MFA funcionando para admins                                                   │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 6-8: COMPLIANCE & GOVERNANÇA                                                    │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 6: Vanta/Drata - SOC 2 & ISO 27001 (Contínuo)                             │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 MÉDIA - Necessário para clientes enterprise grandes              │   │
│   │                                                                                  │   │
│   │  □ 6.1 Escolher Vanta OU Drata (não ambos)                                       │   │
│   │  □ 6.2 Conectar integrações (GitHub, AWS, Google Workspace)                      │   │
│   │  □ 6.3 Mapear controles SOC 2 Type II                                            │   │
│   │  □ 6.4 Configurar Evidence Collection automático                                 │   │
│   │  □ 6.5 Trust Center via Notion (embed no website)                                 │   │
│   │  □ 6.6 Preparar para auditoria (~3-6 meses)                                      │   │
│   │                                                                                  │   │
│   │  Custo: ~$1.000-2.000/mês                                                        │   │
│   │  Código: ~500 linhas (integrações de audit logs)                                 │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Dashboard de compliance >80% verde                                           │   │
│   │  ✓ Evidências coletando automaticamente                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 7: Privacy Tools - LGPD Brasil (3-5 dias)                                 │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA para mercado brasileiro                                  │   │
│   │                                                                                  │   │
│   │  □ 7.1 Contratar Privacy Tools (privacytools.com.br)                             │   │
│   │  □ 7.2 Configurar Portal do Titular de Dados                                     │   │
│   │  □ 7.3 Mapear processos de tratamento de dados                                   │   │
│   │  □ 7.4 Implementar webhook: solicitações LGPD → Rails                            │   │
│   │  □ 7.5 Customizar portal com branding WeDo                                       │   │
│   │  □ 7.6 Gerar RIPD (Relatório de Impacto)                                         │   │
│   │                                                                                  │   │
│   │  Custo: ~R$ 300-600/mês                                                          │   │
│   │  Código: ~200 linhas (webhook handler)                                           │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Portal público acessível em /privacidade                                     │   │
│   │  ✓ Solicitações de dados processadas automaticamente                            │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 8: Warden AI - Bias Audit (Fase 2)                                        │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟢 BAIXA - Após plataforma de screening funcionar                   │   │
│   │                                                                                  │   │
│   │  □ 8.1 Contatar Warden AI para demo                                              │   │
│   │  □ 8.2 Integrar API de análise de bias                                           │   │
│   │  □ 8.3 Gerar relatórios NYC LL144 / EU AI Act                                    │   │
│   │  □ 8.4 Dashboard de fairness metrics                                             │   │
│   │                                                                                  │   │
│   │  Dependência: Capítulo 2 (Screening com Claude) funcionando                      │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Relatório de bias disponível por vaga                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### G.3 Ordem de Implementação - Capítulo 2 (Plataforma)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                CAPÍTULO 2: PLATAFORMA - ORDEM DE IMPLEMENTAÇÃO (70% Interno)             │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   SEMANA 1-3: CORE AI ENGINE                                                             │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 1: Claude (Anthropic) - LLM Principal (5-7 dias)                          │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Motor de toda a IA                                     │   │
│   │                                                                                  │   │
│   │  □ 1.1 Criar conta Anthropic Console                                             │   │
│   │  □ 1.2 Gerar API Key                                                             │   │
│   │  □ 1.3 Implementar ClaudeService (Ruby)                                          │   │
│   │  □ 1.4 System prompts para cada agent (Job Intake, Screening, etc)               │   │
│   │  □ 1.5 Rate limiting e retry logic                                               │   │
│   │  □ 1.6 Token counting e cost tracking                                            │   │
│   │  □ 1.7 Streaming responses para UX                                               │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • ANTHROPIC_API_KEY                                                             │   │
│   │                                                                                  │   │
│   │  Gems Rails:                                                                     │   │
│   │  • anthropic (~> 0.3)                                                            │   │
│   │                                                                                  │   │
│   │  Custo: ~$10/mês (desenvolvimento) → $250-500/mês (10 clientes)                  │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Chat básico funcionando                                                       │   │
│   │  ✓ Streaming responses                                                           │   │
│   │  ✓ Token usage tracking                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 2: Gemini (Google) - Fallback/Voice (3-5 dias)                            │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 MÉDIA - Usado para voice-to-text e fallback                      │   │
│   │                                                                                  │   │
│   │  □ 2.1 Criar projeto Google Cloud                                               │   │
│   │  □ 2.2 Ativar Gemini API                                                         │   │
│   │  □ 2.3 Implementar GeminiService (Ruby)                                          │   │
│   │  □ 2.4 Multimodal: Audio → Text transcription                                    │   │
│   │  □ 2.5 Fallback logic quando Claude falha                                        │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • GOOGLE_AI_API_KEY ou GOOGLE_APPLICATION_CREDENTIALS                           │   │
│   │                                                                                  │   │
│   │  Custo: $0 (free tier generoso)                                                  │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Audio file → Text transcription funciona                                      │   │
│   │  ✓ Fallback automático se Claude timeout                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 3: LangGraph + LangChain (Python Service) (7-10 dias)                     │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Orquestração multi-agente                              │   │
│   │                                                                                  │   │
│   │  □ 3.1 Criar Python service separado (FastAPI)                                   │   │
│   │  □ 3.2 Implementar StateGraph com nós de agentes                                 │   │
│   │  □ 3.3 Definir Agent Types: Orchestrator, JobIntake, Screening, etc             │   │
│   │  □ 3.4 Implementar conditional routing entre agentes                            │   │
│   │  □ 3.5 Persistência de estado (checkpointer)                                     │   │
│   │  □ 3.6 API REST para Rails chamar o serviço                                      │   │
│   │  □ 3.7 WebSocket para streaming de respostas                                     │   │
│   │                                                                                  │   │
│   │  Python packages:                                                                │   │
│   │  • langgraph                                                                     │   │
│   │  • langchain                                                                     │   │
│   │  • langchain-anthropic                                                           │   │
│   │  • fastapi                                                                       │   │
│   │  • uvicorn                                                                       │   │
│   │                                                                                  │   │
│   │  Custo: $0 (open source)                                                         │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Multi-agent workflow executando                                              │   │
│   │  ✓ Estado persistindo entre chamadas                                            │   │
│   │  ✓ Rails → Python service comunicando via HTTP                                   │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 4: LangSmith - Observability (2-3 dias)                                   │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟢 BAIXA - Pode postergar para debug                                │   │
│   │                                                                                  │   │
│   │  □ 4.1 Criar conta LangSmith                                                     │   │
│   │  □ 4.2 Configurar tracing no LangGraph                                           │   │
│   │  □ 4.3 Dashboard de traces por cliente/vaga                                      │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • LANGCHAIN_API_KEY                                                             │   │
│   │  • LANGCHAIN_PROJECT                                                             │   │
│   │                                                                                  │   │
│   │  Custo: $0 (5.000 traces/mês grátis)                                             │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Traces visíveis no dashboard LangSmith                                        │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 4-6: SOURCING & TRIAGEM                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 5: Pearch AI - Banco de Candidatos (5-7 dias)                             │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Sourcing de candidatos                                    │   │
│   │                                                                                  │   │
│   │  □ 5.1 Contatar Pearch AI para API access                                        │   │
│   │  □ 5.2 Implementar PearchService (Ruby)                                          │   │
│   │  □ 5.3 Semantic search integration                                               │   │
│   │  □ 5.4 Similar profile search                                                    │   │
│   │  □ 5.5 Bias controls (excluir campos sensíveis)                                  │   │
│   │  □ 5.6 Rate limiting e quota tracking                                            │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • PEARCH_API_KEY                                                                │   │
│   │                                                                                  │   │
│   │  Custo: ~$500/mês (startup) → $10.000/mês (scale)                                │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Search por skills retorna candidatos                                         │   │
│   │  ✓ Similar search funciona com LinkedIn URL                                      │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 6: Deepgram STT (3-5 dias)                                                │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Transcrição de voice screening                            │   │
│   │                                                                                  │   │
│   │  □ 6.1 Criar conta Deepgram                                                      │   │
│   │  □ 6.2 Implementar DeepgramService (Ruby)                                        │   │
│   │  □ 6.3 Audio file upload → transcription                                         │   │
│   │  □ 6.4 Real-time streaming transcription                                         │   │
│   │  □ 6.5 Speaker diarization                                                       │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • DEEPGRAM_API_KEY                                                              │   │
│   │                                                                                  │   │
│   │  Custo: $0 (créditos iniciais) → ~$5-50/mês                                      │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Audio → Text com timestamps                                                   │   │
│   │  ✓ Diarization identifica speakers                                              │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 7: OpenMic - Voice Screening (5-7 dias)                                   │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Entrevistas por voz                                       │   │
│   │                                                                                  │   │
│   │  □ 7.1 Contatar OpenMic para acesso API                                          │   │
│   │  □ 7.2 Implementar OpenmicService (Ruby)                                         │   │
│   │  □ 7.3 Criar screening session                                                   │   │
│   │  □ 7.4 Webhook: screening completed → process                                    │   │
│   │  □ 7.5 Integrar com Deepgram para transcrição                                    │   │
│   │  □ 7.6 Integrar com Claude para análise WSI                                      │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • OPENMIC_API_KEY                                                               │   │
│   │  • OPENMIC_WEBHOOK_SECRET                                                        │   │
│   │                                                                                  │   │
│   │  Custo: ~$500/mês (startup) → $5.000+/mês (scale)                                │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Candidato recebe link de screening                                           │   │
│   │  ✓ Audio transcrito e analisado automaticamente                                 │   │
│   │  ✓ Score WSI gerado                                                              │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 7-9: COMUNICAÇÃO                                                                │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 8: Mailgun Email (3-5 dias)                                              │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Notificações e convites                                │   │
│   │                                                                                  │   │
│   │  □ 8.1 Criar conta Mailgun                                                      │   │
│   │  □ 8.2 Verificar domínio (DNS records)                                           │   │
│   │  □ 8.3 Criar templates (convite, screening, etc)                                 │   │
│   │  □ 8.4 Implementar MailgunService (Python — provider real)                       │   │
│   │  □ 8.5 Webhooks: delivery, bounce, open tracking                                 │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • MAILGUN_API_KEY + MAILGUN_DOMAIN + RESEND_API_KEY (fallback) — corrigido v3.7 │   │
│   │                                                                                  │   │
│   │  Custo: $0 (5.000/mês grátis) → ~$20-50/mês                                        │   │
│   │                                                                                  │   │
│   │  Gems Rails:                                                                     │   │
│   │  • sendgrid-ruby                                                                 │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Emails enviando com template                                                 │   │
│   │  ✓ Tracking de opens/clicks funcionando                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 9: WhatsApp Business API (5-7 dias)                                       │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Comunicação com candidatos brasileiros                    │   │
│   │                                                                                  │   │
│   │  □ 9.1 Criar conta Meta Business                                                 │   │
│   │  □ 9.2 Configurar WhatsApp Business API (via 360dialog ou Twilio)                │   │
│   │  □ 9.3 Aprovar templates de mensagem                                             │   │
│   │  □ 9.4 Implementar WhatsappService (Ruby)                                        │   │
│   │  □ 9.5 Webhook: message received → LIA agent                                     │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • WHATSAPP_TOKEN                                                                │   │
│   │  • WHATSAPP_PHONE_NUMBER_ID                                                      │   │
│   │                                                                                  │   │
│   │  Custo: $0 (1.000 conversas/mês grátis) → ~$50-500/mês                           │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Enviar template message funciona                                             │   │
│   │  ✓ Receber resposta e processar com LIA                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 10: Microsoft Graph - Calendar (3-5 dias)                                 │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 MÉDIA - Agendamento de entrevistas                               │   │
│   │                                                                                  │   │
│   │  ✓ 10.1 Registrar app no Azure AD (Microsoft Graph - já feito)                   │   │
│   │  □ 10.2 Configurar OAuth flow                                                    │   │
│   │  □ 10.3 Implementar MsGraphService (Ruby)                                        │   │
│   │  □ 10.4 Create/Update/Delete calendar events                                     │   │
│   │  □ 10.5 Find available slots                                                     │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • AZURE_CLIENT_ID                                                               │   │
│   │  • AZURE_CLIENT_SECRET                                                           │   │
│   │  • AZURE_TENANT_ID                                                               │   │
│   │                                                                                  │   │
│   │  Custo: $0 (grátis com Microsoft 365)                                            │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Criar evento no calendário do recrutador                                     │   │
│   │  ✓ Verificar disponibilidade funciona                                           │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 10-12: INTEGRAÇÕES ATS                                                          │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 11: Merge Unified API (5-7 dias)                                       │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Integração com 40+ ATS                                    │   │
│   │                                                                                  │   │
│   │  □ 11.1 Criar conta Merge                                                     │   │
│   │  □ 11.2 Implementar StackoneService (Ruby)                                       │   │
│   │  □ 11.3 OAuth flow para conectar ATS do cliente                                  │   │
│   │  □ 11.4 Sync candidatos: ATS → WeDo                                              │   │
│   │  □ 11.5 Sync status: WeDo → ATS                                                  │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • MERGE_API_KEY + MERGE_ACCOUNT_TOKEN (corrigido v3.7 — produto é Merge.dev)   │   │
│   │                                                                                  │   │
│   │  Custo: ~$500/mês (startup) → $1.500-2.000/mês                                   │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Conectar Greenhouse sandbox                                                  │   │
│   │  ✓ Sync bidirecional funcionando                                                │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 12: Gupy/Pandapé Direct (Brasil) (3-5 dias cada)                          │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA para mercado BR (se Merge não suportar)                  │   │
│   │                                                                                  │   │
│   │  □ 12.1 Contatar Gupy para API access                                            │   │
│   │  □ 12.2 Implementar GupyService (Ruby)                                           │   │
│   │  □ 12.3 Contatar Pandapé para API access                                         │   │
│   │  □ 12.4 Implementar PandapeService (Ruby)                                        │   │
│   │                                                                                  │   │
│   │  Secrets:                                                                        │   │
│   │  • GUPY_API_KEY                                                                  │   │
│   │  • PANDAPE_API_KEY                                                               │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Listar vagas do cliente                                                       │   │
│   │  ✓ Enviar candidatos triados                                                     │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### G.4 Estrutura de Arquivos Rails

```bash
# Estrutura recomendada para integrações
app/
├── services/
│   ├── admin/
│   │   ├── stripe_service.rb
│   │   ├── hubspot_service.rb
│   │   ├── hubspot_onboarding_service.rb
│   │   ├── workos_service.rb
│   │   ├── vanta_service.rb
│   │   └── privacy_tools_service.rb
│   ├── platform/
│   │   ├── claude_service.rb
│   │   ├── gemini_service.rb
│   │   ├── pearch_service.rb
│   │   ├── deepgram_service.rb
│   │   ├── openmic_service.rb
│   │   ├── sendgrid_service.rb
│   │   ├── whatsapp_service.rb
│   │   ├── ms_graph_service.rb
│   │   └── stackone_service.rb
│   └── shared/
│       ├── webhook_handler.rb
│       └── api_client.rb
├── controllers/
│   └── api/
│       └── webhooks/
│           ├── stripe_controller.rb
│           ├── workos_controller.rb
│           ├── hubspot_controller.rb
│           ├── openmic_controller.rb
│           └── whatsapp_controller.rb

# Configuração de secrets
config/
├── credentials/
│   ├── development.yml.enc
│   ├── staging.yml.enc
│   └── production.yml.enc
```

### G.5 Gemfile Completo

```ruby
# Gemfile - Integrações WeDo Talent

# === CAPÍTULO 1: ADMIN ===
gem 'stripe', '~> 10.0'          # Billing
gem 'hubspot-api-client', '~> 17.0'  # CRM
gem 'workos', '~> 5.0'           # SSO/SCIM

# === CAPÍTULO 2: PLATAFORMA ===
gem 'anthropic', '~> 0.3'        # Claude LLM
gem 'google-cloud-ai_platform'   # Gemini (via Vertex AI)
gem 'sendgrid-ruby', '~> 6.6'    # Email
gem 'twilio-ruby', '~> 6.0'      # WhatsApp (via Twilio)
gem 'microsoft_graph'            # MS Graph Calendar

# === INFRAESTRUTURA ===
gem 'redis', '~> 5.0'            # Cache
gem 'bunny', '~> 2.22'           # RabbitMQ
gem 'sidekiq', '~> 7.0'          # Background jobs
gem 'faraday', '~> 2.7'          # HTTP client genérico
gem 'faraday-retry'              # Retry middleware
```

---

## Apêndice H: Guia Passo a Passo - Replit (Prototipagem)

> **Objetivo:** Ordem de implementação para protótipo funcional no Replit  
> **Stack:** Next.js + FastAPI (Python) + React  
> **Filosofia:** Validação rápida de conceitos antes de migrar para produção  
> **Prazo Estimado:** 4-6 semanas para MVP funcional

### H.1 Ambiente Atual Replit

```
plataforma-lia/          # Frontend Next.js + React
lia-agent-system/        # Backend FastAPI + LangGraph
docs/                    # Documentação
```

### H.2 Ordem de Implementação - Capítulo 1 (Admin) no Replit

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│              CAPÍTULO 1: ADMIN - PROTOTIPAGEM REPLIT (React + FastAPI)                   │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   SEMANA 1: SETUP BÁSICO                                                                 │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 1: Stripe Checkout (2-3 dias)                                             │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA                                                          │   │
│   │                                                                                  │   │
│   │  Gestão via Stripe Dashboard (sem admin frontend):                               │   │
│   │  □ Configurar produtos e preços no Stripe Dashboard                             │   │
│   │  □ Configurar Customer Portal no Stripe                                         │   │
│   │  □ Clientes usam Customer Portal para gerenciar assinaturas                     │   │
│   │                                                                                  │   │
│   │  Backend (lia-agent-system):                                                     │   │
│   │  □ pip install stripe                                                            │   │
│   │  □ Criar app/services/stripe_service.py                                          │   │
│   │  □ Endpoints:                                                                    │   │
│   │    - POST /api/billing/create-checkout-session                                   │   │
│   │    - POST /api/billing/create-portal-session                                     │   │
│   │    - POST /api/webhooks/stripe                                                   │   │
│   │                                                                                  │   │
│   │  Secrets Replit:                                                                 │   │
│   │  • STRIPE_SECRET_KEY                                                             │   │
│   │  • STRIPE_PUBLISHABLE_KEY                                                        │   │
│   │  • STRIPE_WEBHOOK_SECRET                                                         │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Checkout flow funciona em test mode                                          │   │
│   │  ✓ Customer Portal acessível                                                    │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 2: HubSpot CRM Sync (2-3 dias)                                            │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA                                                             │   │
│   │                                                                                  │   │
│   │  Backend (lia-agent-system):                                                     │   │
│   │  □ pip install hubspot-api-client                                                │   │
│   │  □ Criar app/services/hubspot_service.py                                         │   │
│   │  □ Endpoints:                                                                    │   │
│   │    - POST /api/clients/sync-hubspot                                              │   │
│   │    - GET /api/clients/{id}/hubspot-status                                        │   │
│   │                                                                                  │   │
│   │  Secrets Replit:                                                                 │   │
│   │  • HUBSPOT_ACCESS_TOKEN (já existe!)                                             │   │
│   │                                                                                  │   │
│   │  Frontend:                                                                       │   │
│   │  □ Adicionar badge de sync status na lista de clientes                           │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Criar cliente no app cria Company no HubSpot                                  │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 3: WorkOS SSO (já implementado - revisar) (1-2 dias)                      │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟢 JÁ EXISTE - apenas validar                                       │   │
│   │                                                                                  │   │
│   │  Verificar funcionamento:                                                        │   │
│   │  □ SSO login flow                                                                │   │
│   │  □ SCIM webhooks                                                                 │   │
│   │  □ Audit logs                                                                    │   │
│   │                                                                                  │   │
│   │  Secrets Replit (já existem!):                                                   │   │
│   │  • WORKOS_API_KEY ✓                                                              │   │
│   │  • WORKOS_CLIENT_ID ✓                                                            │   │
│   │  • WORKOS_WEBHOOK_SECRET ✓                                                       │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Login via SSO funciona                                                        │   │
│   │  ✓ Usuário provisionado via SCIM aparece                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 2: COMPLIANCE                                                                   │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 4: Trust Center via Notion (0 dias dev)                                   │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Status: ✅ COMPLETO - Substituído por Notion                                    │   │
│   │                                                                                  │   │
│   │  Decisão: Trust Center será mantido no Notion (não desenvolvido internamente)   │   │
│   │                                                                                  │   │
│   │  Página Notion: https://notion.so/2e8f66d01d6b81adadc7d7543839ac02               │   │
│   │  Website: /trust → embed ou redirect para Notion                                │   │
│   │                                                                                  │   │
│   │  Economia: ~2.000 linhas, ~1 semana de desenvolvimento                           │   │
│   │                                                                                  │   │
│   │  Vantagens:                                                                      │   │
│   │  ✓ Equipe não-técnica pode editar compliance                                    │   │
│   │  ✓ Atualizações instantâneas sem deploy                                         │   │
│   │  ✓ Custo zero (Notion grátis para páginas públicas)                             │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Página Notion pública acessível                                              │   │
│   │  ✓ Embed/redirect configurado no website                                        │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 5: Privacy Tools Mock (1-2 dias)                                          │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 MÉDIA - Mock para prototipagem                                   │   │
│   │                                                                                  │   │
│   │  Frontend:                                                                       │   │
│   │  □ Criar /privacy/page.tsx (portal público)                                      │   │
│   │  □ Formulário de solicitação LGPD                                                │   │
│   │  □ Status tracking                                                               │   │
│   │                                                                                  │   │
│   │  Backend:                                                                        │   │
│   │  □ Criar app/services/privacy_service.py (mock)                                  │   │
│   │  □ Endpoints:                                                                    │   │
│   │    - POST /api/privacy/request                                                   │   │
│   │    - GET /api/privacy/request/{id}/status                                        │   │
│   │                                                                                  │   │
│   │  Nota: Em produção, isso será substituído por Privacy Tools SaaS                 │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Formulário LGPD funciona                                                     │   │
│   │  ✓ Email de confirmação enviado (mock)                                          │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### H.3 Ordem de Implementação - Capítulo 2 (Plataforma) no Replit

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│            CAPÍTULO 2: PLATAFORMA - PROTOTIPAGEM REPLIT (React + FastAPI)                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   SEMANA 2-3: CORE AI (já parcialmente implementado)                                     │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 1: Claude + LangGraph (revisar/completar) (3-5 dias)                      │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Status: ⚠️ PARCIALMENTE IMPLEMENTADO                                            │   │
│   │                                                                                  │   │
│   │  Verificar lia-agent-system/:                                                    │   │
│   │  □ app/agents/ - estrutura de agentes                                            │   │
│   │  □ app/graphs/ - LangGraph workflows                                             │   │
│   │  □ System prompts para cada agent                                                │   │
│   │                                                                                  │   │
│   │  Integrations já instaladas:                                                     │   │
│   │  • python_anthropic_ai_integrations ✓                                            │   │
│   │  • python_gemini_ai_integrations ✓                                               │   │
│   │                                                                                  │   │
│   │  Completar:                                                                      │   │
│   │  □ Job Intake Agent                                                              │   │
│   │  □ Screening Agent                                                               │   │
│   │  □ Communication Agent                                                           │   │
│   │  □ Scheduling Agent                                                              │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Chat com LIA funciona                                                         │   │
│   │  ✓ Multi-agent routing funciona                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 2: Deepgram STT (2-3 dias)                                                │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA                                                             │   │
│   │                                                                                  │   │
│   │  Backend (lia-agent-system):                                                     │   │
│   │  □ pip install deepgram-sdk                                                      │   │
│   │  □ Criar app/services/deepgram_service.py                                        │   │
│   │  □ Endpoints:                                                                    │   │
│   │    - POST /api/voice/transcribe                                                  │   │
│   │    - WebSocket /ws/voice/stream                                                  │   │
│   │                                                                                  │   │
│   │  Secrets Replit:                                                                 │   │
│   │  • DEEPGRAM_API_KEY ✓ (já existe!)                                               │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Upload audio → transcrição                                                   │   │
│   │  ✓ Streaming transcription funciona                                             │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 3: WSI Analysis com Claude (3-5 dias)                                     │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🔴 CRÍTICA - Core do produto                                        │   │
│   │                                                                                  │   │
│   │  Backend:                                                                        │   │
│   │  □ Criar app/services/wsi_service.py                                             │   │
│   │  □ Implementar análise de competências                                           │   │
│   │  □ Cálculo de score WSI                                                          │   │
│   │  □ Geração de parecer LIA                                                        │   │
│   │                                                                                  │   │
│   │  Endpoints:                                                                      │   │
│   │  - POST /api/screening/analyze                                                   │   │
│   │  - GET /api/screening/{id}/wsi-score                                             │   │
│   │  - GET /api/screening/{id}/lia-opinion                                           │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Score WSI calculado corretamente                                             │   │
│   │  ✓ Parecer LIA gerado                                                            │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 4-5: COMUNICAÇÃO                                                                │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 4: Email Notifications (2-3 dias)                                         │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA                                                             │   │
│   │                                                                                  │   │
│   │  Backend:                                                                        │   │
│   │  □ pip install sendgrid                                                          │   │
│   │  □ Criar app/services/email_service.py                                           │   │
│   │  □ Templates:                                                                    │   │
│   │    - Convite para screening                                                      │   │
│   │    - Resultado de triagem                                                        │   │
│   │    - Convite para entrevista                                                     │   │
│   │                                                                                  │   │
│   │  Secrets Replit:                                                                 │   │
│   │  • MAILGUN_API_KEY + MAILGUN_DOMAIN (solicitar) — corrigido v3.7                 │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Email de convite enviado                                                     │   │
│   │  ✓ Email de resultado enviado                                                   │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 5: Pearch AI Integration (3-5 dias)                                       │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟡 ALTA - Sourcing de candidatos                                    │   │
│   │                                                                                  │   │
│   │  Backend:                                                                        │   │
│   │  □ Criar app/services/pearch_service.py                                          │   │
│   │  □ Endpoints:                                                                    │   │
│   │    - POST /api/talent/search                                                     │   │
│   │    - POST /api/talent/similar-search                                             │   │
│   │                                                                                  │   │
│   │  Frontend:                                                                       │   │
│   │  □ Componente de busca semântica                                                 │   │
│   │  □ Componente de busca similar                                                   │   │
│   │                                                                                  │   │
│   │  Secrets Replit:                                                                 │   │
│   │  • PEARCH_API_KEY (solicitar)                                                    │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ Busca por skills retorna candidatos                                          │   │
│   │  ✓ Similar search com LinkedIn URL funciona                                     │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│   SEMANA 5-6: INTEGRAÇÕES ATS                                                            │
│   ─────────────────────────────────────────────────────────────────────────────────────  │
│                                           │                                              │
│                                           ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ETAPA 6: Merge Mock (2-3 dias)                                         │   │
│   │  ─────────────────────────────────────────────────────────────────────────────── │   │
│   │  Prioridade: 🟢 MÉDIA - Mock para demonstração                                   │   │
│   │                                                                                  │   │
│   │  Backend:                                                                        │   │
│   │  □ Criar app/services/ats_service.py (mock)                                      │   │
│   │  □ Simular conexão com ATS                                                       │   │
│   │  □ Mock data de vagas e candidatos                                               │   │
│   │                                                                                  │   │
│   │  Frontend:                                                                       │   │
│   │  □ Tela de configuração de ATS                                                   │   │
│   │  □ Status de sync                                                                │   │
│   │                                                                                  │   │
│   │  Nota: Em produção, substituir por Merge real                                 │   │
│   │                                                                                  │   │
│   │  Validação:                                                                      │   │
│   │  ✓ UI de conexão ATS funciona                                                   │   │
│   │  ✓ Mock sync exibe dados                                                        │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### H.4 Estrutura de Arquivos Replit

```bash
# Frontend (plataforma-lia/)
src/
├── app/
│   ├── admin/
│   │   ├── billing/
│   │   │   └── page.tsx          # Stripe billing
│   │   ├── clients/
│   │   │   └── page.tsx          # Lista de clientes (HubSpot sync)
│   │   └── compliance/
│   │       └── trust-center/
│   │           └── page.tsx      # ✓ JÁ EXISTE
│   ├── privacy/
│   │   └── page.tsx              # Portal LGPD público
│   └── jobs/
│       └── [id]/
│           └── screening/
│               └── page.tsx      # WSI Analysis
├── components/
│   ├── billing/
│   │   ├── PricingTable.tsx
│   │   └── CustomerPortalButton.tsx
│   └── screening/
│       ├── WsiScoreCard.tsx
│       └── LiaOpinionCard.tsx
└── lib/
    └── api/
        ├── stripe.ts
        ├── hubspot.ts
        └── screening.ts

# Backend (lia-agent-system/)
app/
├── services/
│   ├── stripe_service.py        # Billing
│   ├── hubspot_service.py       # CRM
│   ├── deepgram_service.py      # STT
│   ├── wsi_service.py           # WSI Analysis
│   ├── email_service.py         # Notifications
│   ├── pearch_service.py        # Sourcing
│   └── ats_service.py           # ATS Mock
├── routers/
│   ├── billing.py
│   ├── clients.py
│   ├── screening.py
│   ├── voice.py
│   └── webhooks.py
└── agents/
    ├── orchestrator.py
    ├── job_intake.py
    ├── screening.py
    ├── communication.py
    └── scheduling.py
```

### H.5 Secrets Necessários no Replit

```bash
# JÁ EXISTEM ✓
DEEPGRAM_API_KEY
HUBSPOT_ACCESS_TOKEN
JIRA_API_TOKEN
JIRA_EMAIL
WORKOS_API_KEY
WORKOS_CLIENT_ID
WORKOS_WEBHOOK_SECRET

# SOLICITAR AO USUÁRIO
# Billing (planejado — não implementado ainda; ver Seção 0.3)
STRIPE_SECRET_KEY          # Stripe billing
STRIPE_PUBLISHABLE_KEY     # Stripe frontend
STRIPE_WEBHOOK_SECRET      # Stripe webhooks
# Email (Mailgun primário + Resend fallback) — corrigido v3.7
MAILGUN_API_KEY            # Email primário
MAILGUN_DOMAIN             # Domínio Mailgun
RESEND_API_KEY             # Email fallback
# Sourcing
PEARCH_API_KEY             # Candidate sourcing
APIFY_API_TOKEN            # LinkedIn scraping
# Voz
OPENMIC_API_KEY            # Voice screening
DEEPGRAM_API_KEY           # STT entrevistas
# WhatsApp/SMS/Voice PSTN
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
# ATS
MERGE_API_KEY              # Unified ATS/HRIS
MERGE_ACCOUNT_TOKEN
GUPY_API_KEY               # Direto BR
PANDAPE_API_KEY            # Direto BR
# Observabilidade
SENTRY_DSN
LANGCHAIN_API_KEY          # LangSmith
# Infra
REDIS_ENCRYPTION_KEY       # Fernet — OBRIGATÓRIO em prod (PII em Redis)
```

### H.6 Comandos de Setup Rápido

```bash
# Frontend (plataforma-lia/)
cd plataforma-lia
npm install @stripe/stripe-js

# Backend (lia-agent-system/)
cd lia-agent-system
pip install stripe sendgrid hubspot-api-client deepgram-sdk

# Verificar workflows rodando
# dev-server: npm run dev (porta 5000)
# lia-backend: uvicorn app.main:app (porta 8000)
# storybook: npm run storybook (porta 6000)
```

### H.7 Checklist de Validação Final

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHECKLIST MVP REPLIT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CAPÍTULO 1: ADMIN                                               │
│  ─────────────────                                               │
│  □ Stripe checkout funciona                                      │
│  □ Customer Portal acessível                                     │
│  □ HubSpot sync funcionando                                      │
│  □ SSO login com WorkOS                                          │
│  □ Trust Center (Notion) integrado                               │
│  □ Portal LGPD básico                                            │
│                                                                  │
│  CAPÍTULO 2: PLATAFORMA                                          │
│  ───────────────────────                                         │
│  □ Chat com LIA funciona                                         │
│  □ Job Intake wizard                                             │
│  □ Screening flow completo                                       │
│  □ WSI Score calculado                                           │
│  □ Parecer LIA gerado                                            │
│  □ Voice transcription                                           │
│  □ Email notifications                                           │
│  □ Busca de candidatos (mock/real)                               │
│                                                                  │
│  INFRAESTRUTURA                                                  │
│  ──────────────                                                  │
│  □ Todos workflows rodando                                       │
│  □ Database PostgreSQL conectado                                 │
│  □ Secrets configurados                                          │
│  □ Logs sem erros críticos                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# APÊNDICE I: SEPARAÇÃO DE TAREFAS - CONFIGURAÇÃO SaaS vs DESENVOLVIMENTO

> **Objetivo:** Acelerar a implementação do WeDo Talent Admin separando claramente o trabalho de configuração nas ferramentas SaaS (que pode ser feito agora) do trabalho de desenvolvimento no backend Rails (que os devs farão depois).

## I.1 Visão Geral da Divisão de Trabalho

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIVISÃO DE TRABALHO - WEDO TALENT ADMIN                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌───────────────────────────────────┐    ┌───────────────────────────────────────┐   │
│   │                                    │    │                                        │   │
│   │   👔 GESTOR/PRODUTO               │    │   👨‍💻 TIME DE DEVS                      │   │
│   │   (Configuração SaaS)              │    │   (Desenvolvimento Rails)              │   │
│   │                                    │    │                                        │   │
│   ├───────────────────────────────────┤    ├───────────────────────────────────────┤   │
│   │                                    │    │                                        │   │
│   │  • Criar contas nos SaaS          │    │  • API REST multi-tenant              │   │
│   │  • Configurar produtos/preços     │    │  • Modelos de dados (PostgreSQL)      │   │
│   │  • Definir campos customizados    │    │  • Recebimento de webhooks            │   │
│   │  • Criar templates/workflows      │    │  • Serviços de sincronização          │   │
│   │  • Obter API keys/secrets         │    │  • Jobs em background                 │   │
│   │  • Documentar IDs importantes     │    │  • Testes automatizados               │   │
│   │                                    │    │                                        │   │
│   │  ⏱️ ~2-3 dias                      │    │  ⏱️ ~2-4 semanas                       │   │
│   │  🔧 Sem código                     │    │  🔧 Ruby on Rails + PostgreSQL         │   │
│   │                                    │    │                                        │   │
│   └───────────────────────────────────┘    └───────────────────────────────────────┘   │
│                                                                                          │
│   ════════════════════════════════════════════════════════════════════════════════════  │
│                                    DEPENDÊNCIA                                           │
│   ════════════════════════════════════════════════════════════════════════════════════  │
│                                                                                          │
│   O trabalho do GESTOR fornece para os DEVS:                                            │
│   • API Keys e Secrets das ferramentas                                                   │
│   • IDs de produtos, preços, pipelines, estágios                                        │
│   • Webhook endpoints configurados                                                       │
│   • Documentação de campos customizados                                                  │
│   • Credenciais OAuth configuradas                                                       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## I.2 TRABALHO DO GESTOR: Configuração nas Ferramentas SaaS

> **IMPORTANTE:** Estas tarefas podem ser feitas AGORA, antes dos devs começarem. Quanto mais cedo fizer, mais rápido eles poderão integrar.

### I.2.1 STRIPE - Configuração de Billing

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar conta Stripe | stripe.com | 10 min | Account ID |
| 2 | Verificar conta (documentos) | Dashboard → Settings → Business | 1-2 dias | Conta ativa |
| 3 | Criar produtos e preços | Dashboard → Products | 30 min | Product IDs, Price IDs |
| 4 | Configurar Customer Portal | Dashboard → Settings → Billing → Customer portal | 15 min | Portal URL |
| 5 | Criar webhook endpoint | Dashboard → Developers → Webhooks | 10 min | Webhook Secret |
| 6 | Gerar API keys | Dashboard → Developers → API keys | 5 min | Secret Key, Publishable Key |
| 7 | Configurar taxas Brasil | Dashboard → Settings → Payments | 15 min | Boleto, PIX habilitados |

**Produtos a Criar no Stripe:**

| Produto | Preço Mensal | Preço Anual | Tipo | Notas |
|---------|--------------|-------------|------|-------|
| Starter | R$ 497/mês | R$ 4.970/ano | Recorrente | Até 10 vagas/mês |
| Professional | R$ 1.497/mês | R$ 14.970/ano | Recorrente | Até 50 vagas/mês |
| Enterprise | Sob consulta | Sob consulta | Customizado | Ilimitado |
| Triagem Avulsa | R$ 49/triagem | - | Uso único | Créditos extras |

**Eventos de Webhook a Habilitar:**
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`
- `customer.created`
- `customer.updated`

**Entregáveis para os Devs:**
```
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

PRODUTOS:
- Starter: prod_xxx (price_xxx mensal, price_xxx anual)
- Professional: prod_xxx (price_xxx mensal, price_xxx anual)
- Enterprise: prod_xxx (price_xxx customizado)
- Triagem Avulsa: prod_xxx (price_xxx único)
```

---

### I.2.2 HUBSPOT - Configuração do CRM

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar conta HubSpot | hubspot.com | 10 min | Portal ID |
| 2 | Criar Private App | Settings → Integrations → Private Apps | 15 min | Access Token |
| 3 | Criar propriedades customizadas | Settings → Properties → Companies | 30 min | Lista de campos |
| 4 | Criar pipeline de vendas | CRM → Pipelines | 20 min | Pipeline ID, Stage IDs |
| 5 | Criar pipeline de onboarding | CRM → Pipelines | 20 min | Pipeline ID, Stage IDs |
| 6 | Configurar workflows | Automation → Workflows | 1 hora | Workflow IDs |
| 7 | Criar listas/segmentos | Contacts → Lists | 20 min | List IDs |

**Propriedades Customizadas a Criar (Companies):**

| Nome Interno | Label | Tipo | Grupo |
|--------------|-------|------|-------|
| `wedo_tenant_id` | WeDo Tenant ID | Single-line text | WeDo Talent |
| `wedo_stripe_customer_id` | Stripe Customer ID | Single-line text | WeDo Talent |
| `wedo_workos_org_id` | WorkOS Org ID | Single-line text | WeDo Talent |
| `wedo_plan` | Plano Contratado | Dropdown (Starter, Professional, Enterprise) | WeDo Talent |
| `wedo_mrr` | MRR | Number | WeDo Talent |
| `wedo_status` | Status Cliente | Dropdown (Trial, Active, Churned, Paused) | WeDo Talent |
| `wedo_onboarding_stage` | Estágio Onboarding | Dropdown (Kickoff, Configuração, Treinamento, Go-Live) | WeDo Talent |
| `wedo_csm_owner` | CSM Responsável | HubSpot user | WeDo Talent |
| `wedo_contract_start` | Data Início Contrato | Date | WeDo Talent |
| `wedo_contract_end` | Data Fim Contrato | Date | WeDo Talent |
| `wedo_license_count` | Qtd Licenças | Number | WeDo Talent |
| `wedo_sso_enabled` | SSO Ativo | Checkbox | WeDo Talent |

**Pipeline de Vendas a Criar:**

| Estágio | Probabilidade | Ação Automática |
|---------|---------------|-----------------|
| Lead Qualificado | 20% | - |
| Demo Agendada | 40% | - |
| Proposta Enviada | 60% | - |
| Negociação | 80% | - |
| Contrato Assinado | 90% | Criar Stripe Customer |
| Won (Cliente Ativo) | 100% | Disparar Onboarding |
| Lost | 0% | - |

**Pipeline de Onboarding a Criar:**

| Estágio | Descrição |
|---------|-----------|
| Kickoff | Reunião inicial |
| Configuração SSO | Configurando WorkOS |
| Integração ATS | Conectando ao ATS do cliente |
| Treinamento | Capacitação usuários |
| Go-Live | Produção ativa |
| Sucesso | Onboarding concluído |

**Entregáveis para os Devs:**
```
HUBSPOT_ACCESS_TOKEN=pat-xxx (já existe)
HUBSPOT_PORTAL_ID=xxx

PIPELINES:
- Vendas: pipeline_xxx
  - Lead Qualificado: stage_xxx
  - Demo Agendada: stage_xxx
  - Proposta Enviada: stage_xxx
  - Negociação: stage_xxx
  - Contrato Assinado: stage_xxx
  - Won: stage_xxx
  - Lost: stage_xxx
  
- Onboarding: pipeline_xxx
  - Kickoff: stage_xxx
  - Configuração SSO: stage_xxx
  - Integração ATS: stage_xxx
  - Treinamento: stage_xxx
  - Go-Live: stage_xxx
  - Sucesso: stage_xxx

PROPRIEDADES CUSTOMIZADAS:
- wedo_tenant_id
- wedo_stripe_customer_id
- wedo_workos_org_id
- wedo_plan
- wedo_mrr
- wedo_status
- wedo_onboarding_stage
- wedo_csm_owner
- wedo_contract_start
- wedo_contract_end
- wedo_license_count
- wedo_sso_enabled
```

---

### I.2.3 WORKOS - Configuração de SSO/SCIM

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar conta WorkOS | workos.com | 10 min | API Key, Client ID (já existe) |
| 2 | Configurar redirect URIs | Dashboard → Configuration | 10 min | URIs documentados |
| 3 | Configurar webhook endpoint | Dashboard → Webhooks | 10 min | Webhook Secret (já existe) |
| 4 | Criar Organization de teste | Dashboard → Organizations | 15 min | Org ID de teste |
| 5 | Configurar SSO connection teste | Dashboard → SSO | 30 min | Connection ID |
| 6 | Configurar SCIM (se aplicável) | Dashboard → Directory Sync | 30 min | Directory ID |
| 7 | Definir domínios permitidos | Dashboard → Configuration | 10 min | Lista de domínios |

**Eventos de Webhook a Habilitar:**
- `user.created`
- `user.updated`
- `user.deleted`
- `dsync.user.created`
- `dsync.user.updated`
- `dsync.user.deleted`
- `dsync.group.created`
- `dsync.group.updated`
- `dsync.group.deleted`
- `connection.activated`
- `connection.deactivated`

**Entregáveis para os Devs:**
```
WORKOS_API_KEY=sk_xxx (já existe)
WORKOS_CLIENT_ID=client_xxx (já existe)
WORKOS_WEBHOOK_SECRET=xxx (já existe)

REDIRECT URIs CONFIGURADOS:
- Produção: https://app.wedotalent.com/auth/callback
- Staging: https://staging.wedotalent.com/auth/callback
- Dev: http://localhost:3000/auth/callback

ORGANIZATION DE TESTE:
- Org ID: org_xxx
- SSO Connection ID: conn_xxx (se configurado)
- Directory ID: dir_xxx (se SCIM configurado)
```

---

### I.2.4 PROFITWELL - Configuração de Métricas

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar conta ProfitWell | profitwell.com | 10 min | Account ID |
| 2 | Conectar ao Stripe | Dashboard → Integrations | 5 min | Integração ativa |
| 3 | Configurar segments | Dashboard → Segments | 20 min | Segment IDs |
| 4 | Gerar API key (opcional) | Dashboard → API | 5 min | API Key |

**Entregáveis para os Devs:**
```
PROFITWELL_API_KEY=xxx (opcional - métricas são automáticas via Stripe)

SEGMENTS CRIADOS:
- Por plano: Starter, Professional, Enterprise
- Por região: Brasil, LATAM
- Por tamanho: SMB, Mid-Market, Enterprise
```

> **Nota:** ProfitWell é gratuito e puxa dados automaticamente do Stripe. Não requer desenvolvimento adicional - apenas visualização de métricas.

---

### I.2.5 PRIVACY TOOLS - Configuração de LGPD

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar conta Privacy Tools | privacytools.com.br | 10 min | Account ID |
| 2 | Configurar empresa | Dashboard → Configurações | 15 min | Dados empresa |
| 3 | Criar portal do titular | Dashboard → Portal | 30 min | URL do portal |
| 4 | Configurar webhook | Dashboard → Integrações | 10 min | Webhook Secret |
| 5 | Gerar API key | Dashboard → API | 5 min | API Key |
| 6 | Personalizar branding | Dashboard → Branding | 20 min | Tema aplicado |
| 7 | Criar templates de resposta | Dashboard → Templates | 30 min | Template IDs |

**Entregáveis para os Devs:**
```
PRIVACYTOOLS_API_KEY=xxx
PRIVACYTOOLS_WEBHOOK_SECRET=xxx

PORTAL DO TITULAR:
- URL: https://privacidade.wedotalent.com ou embed no site
- Tipos de solicitação: Acesso, Correção, Exclusão, Portabilidade

WEBHOOK EVENTOS:
- request.created
- request.updated
- request.completed
```

---

### I.2.6 HUBSPOT ONBOARDING - Configuração de Tickets + Workflows

> **Nota:** Onboarding agora é gerenciado 100% via HubSpot nativo (Tickets + Workflows), sem Arrows.

| # | Tarefa | Onde Fazer | Tempo | Entregável para Devs |
|---|--------|------------|-------|----------------------|
| 1 | Criar Pipeline de Tickets | HubSpot > Service > Tickets > Pipelines | 20 min | Pipeline ID |
| 2 | Criar propriedades customizadas | HubSpot > Settings > Properties > Tickets | 15 min | Property names |
| 3 | Criar Workflow 1: Deal → Ticket | HubSpot > Automation > Workflows | 20 min | Workflow ID |
| 4 | Criar Workflow 2: Stage → Email | HubSpot > Automation > Workflows | 30 min | Workflow ID |
| 5 | Criar Workflow 3: Completo → Company | HubSpot > Automation > Workflows | 15 min | Workflow ID |
| 6 | Criar templates de email | HubSpot > Marketing > Email | 30 min | Template IDs |

**Pipeline de Onboarding a Criar:**

| Stage | Descrição | Email Automático | Prazo |
|-------|-----------|------------------|-------|
| **Boas-vindas Enviadas** | Deal fechado, ticket criado | "Bem-vindo à WeDo Talent!" | D+0 |
| **Dados Básicos Coletados** | Cliente preencheu formulário | "Próximos passos: Configuração" | D+3 |
| **Configuração Inicial** | Empresa configurada | "Hora de importar dados" | D+7 |
| **Importação de Dados** | Candidatos/vagas importados | "Agendar treinamento" | D+14 |
| **Treinamento Agendado** | Sessão confirmada | "Confirmação do treinamento" | D+21 |
| **Go-Live** | Primeira vaga publicada | "Parabéns! Você está ao vivo 🎉" | D+28 |
| **Onboarding Completo** | Cliente autônomo | Task: "Check-in 30 dias" | D+30 |

**Entregáveis para os Devs:**
```
(Nenhuma API key adicional necessária - usa HubSpot API já configurada)

PIPELINE:
- "Onboarding Cliente" com 7 stages

WORKFLOWS:
- "Deal Fechado → Criar Ticket": workflow_xxx
- "Ticket Stage Changed → Email": workflow_xxx
- "Onboarding Completo → Atualizar Company": workflow_xxx

PROPRIEDADES TICKET:
- wedo_onboarding_progress (number)
- wedo_onboarding_stage (dropdown)
- wedo_assigned_csm (user)
- wedo_golive_target_date (date)
```

---

## I.3 TRABALHO DOS DEVS: Desenvolvimento Rails

> **IMPORTANTE:** Os devs só começam quando o Gestor entregar as configurações acima. Com isso, eles podem desenvolver tudo de uma vez, sem bloqueios.

### I.3.1 Estrutura de Banco de Dados (PostgreSQL)

```ruby
# db/migrate/xxx_create_admin_tables.rb

# 1. Tenants (Multi-tenant isolation)
create_table :tenants do |t|
  t.string :name, null: false
  t.string :subdomain, null: false, index: { unique: true }
  t.string :status, default: 'active' # active, suspended, churned
  t.string :plan # starter, professional, enterprise
  t.string :stripe_customer_id, index: true
  t.string :hubspot_company_id, index: true
  t.string :workos_org_id, index: true
  t.string :hubspot_onboarding_ticket_id
  t.jsonb :settings, default: {}
  t.jsonb :feature_flags, default: {}
  t.integer :license_count, default: 5
  t.date :contract_start_date
  t.date :contract_end_date
  t.timestamps
end

# 2. Users (dentro de cada tenant)
create_table :users do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :email, null: false
  t.string :name
  t.string :role # admin, recruiter, hiring_manager, viewer
  t.string :workos_user_id, index: true
  t.string :workos_idp_id # ID do IdP externo (SCIM)
  t.boolean :sso_only, default: false
  t.datetime :last_login_at
  t.string :status, default: 'active'
  t.timestamps
  
  t.index [:tenant_id, :email], unique: true
end

# 3. Subscriptions (Stripe)
create_table :subscriptions do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :stripe_subscription_id, null: false, index: { unique: true }
  t.string :stripe_price_id
  t.string :status # active, past_due, canceled, trialing
  t.datetime :current_period_start
  t.datetime :current_period_end
  t.datetime :canceled_at
  t.jsonb :metadata, default: {}
  t.timestamps
end

# 4. Invoices (Stripe)
create_table :invoices do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :stripe_invoice_id, null: false, index: { unique: true }
  t.integer :amount_cents
  t.string :currency, default: 'brl'
  t.string :status # draft, open, paid, void, uncollectible
  t.datetime :due_date
  t.datetime :paid_at
  t.string :pdf_url
  t.timestamps
end

# 5. SSO Connections (WorkOS)
create_table :sso_connections do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :workos_connection_id, null: false, index: { unique: true }
  t.string :connection_type # SAML, OIDC
  t.string :provider # Okta, Azure AD, Google, etc.
  t.string :status # active, inactive
  t.string :domain
  t.jsonb :metadata, default: {}
  t.timestamps
end

# 6. Directory Syncs (WorkOS SCIM)
create_table :directory_syncs do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :workos_directory_id, null: false, index: { unique: true }
  t.string :directory_type # Azure SCIM, Okta SCIM, etc.
  t.string :status # active, inactive
  t.datetime :last_sync_at
  t.timestamps
end

# 7. Audit Logs
create_table :audit_logs do |t|
  t.references :tenant, foreign_key: true
  t.references :user, foreign_key: true
  t.string :action, null: false # login, logout, create, update, delete, etc.
  t.string :resource_type
  t.string :resource_id
  t.jsonb :changes, default: {}
  t.inet :ip_address
  t.string :user_agent
  t.timestamps
end

# 8. Webhook Events (para debug e replay)
create_table :webhook_events do |t|
  t.string :source, null: false # stripe, workos, hubspot
  t.string :event_type, null: false
  t.string :external_id, index: true
  t.jsonb :payload, null: false
  t.string :status, default: 'pending' # pending, processed, failed
  t.text :error_message
  t.integer :retry_count, default: 0
  t.datetime :processed_at
  t.timestamps
end

# 9. LGPD Requests (Privacy Tools)
create_table :lgpd_requests do |t|
  t.references :tenant, null: false, foreign_key: true
  t.string :privacy_tools_id, index: true
  t.string :request_type # access, correction, deletion, portability
  t.string :requester_email
  t.string :requester_name
  t.string :status # pending, in_progress, completed, rejected
  t.datetime :due_date
  t.datetime :completed_at
  t.jsonb :data_exported
  t.timestamps
end
```

### I.3.2 API REST Endpoints

```ruby
# config/routes.rb

namespace :api do
  namespace :v1 do
    # === STRIPE WEBHOOKS ===
    post 'webhooks/stripe', to: 'webhooks/stripe#receive'
    
    # === WORKOS WEBHOOKS ===
    post 'webhooks/workos', to: 'webhooks/workos#receive'
    
    # === HUBSPOT WEBHOOKS ===
    post 'webhooks/hubspot', to: 'webhooks/hubspot#receive'
    
    # === HUBSPOT ONBOARDING (via HubSpot webhooks, sem endpoint separado) ===
    # Onboarding usa pipeline de tickets nativo do HubSpot
    
    # === PRIVACY TOOLS WEBHOOKS ===
    post 'webhooks/privacytools', to: 'webhooks/privacy_tools#receive'
    
    # === TENANT MANAGEMENT (interno) ===
    resources :tenants, only: [:index, :show, :create, :update] do
      member do
        post :suspend
        post :reactivate
        get :usage_stats
      end
      resources :users, only: [:index, :show, :create, :update, :destroy]
      resources :subscriptions, only: [:index, :show]
      resources :invoices, only: [:index, :show]
      resources :sso_connections, only: [:index, :show]
      resources :audit_logs, only: [:index]
    end
    
    # === BILLING ===
    namespace :billing do
      post :create_checkout_session
      post :create_customer_portal_session
      get :subscription_status
    end
    
    # === SSO/AUTH ===
    namespace :auth do
      get :sso_url
      post :callback
      post :logout
    end
  end
end
```

### I.3.3 Services a Desenvolver

| Service | Responsabilidade | Prioridade |
|---------|------------------|------------|
| `TenantService` | CRUD de tenants, multi-tenant isolation | P0 |
| `StripeWebhookService` | Processar eventos do Stripe | P0 |
| `StripeBillingService` | Criar checkout, portal, subscriptions | P0 |
| `WorkOSAuthService` | SSO login/logout, session management | P0 |
| `WorkOSWebhookService` | Processar eventos SCIM/SSO | P0 |
| `HubSpotSyncService` | Sincronizar dados com HubSpot | P1 |
| `HubSpotWebhookService` | Processar eventos do HubSpot | P1 |
| `HubSpotOnboardingService` | Gerenciar tickets de onboarding via HubSpot API | P2 |
| `PrivacyToolsService` | Processar solicitações LGPD | P2 |
| `AuditLogService` | Registrar todas as ações | P1 |

### I.3.4 Background Jobs

```ruby
# app/jobs/

# Stripe
ProcessStripeWebhookJob        # Processar eventos Stripe
SyncStripeSubscriptionJob      # Sincronizar subscription com DB
GenerateInvoicePdfJob          # Baixar PDF de invoice

# WorkOS
ProcessWorkOSWebhookJob        # Processar eventos WorkOS
SyncScimUsersJob               # Sincronizar usuários SCIM
DeactivateUserJob              # Desativar usuário removido do SCIM

# HubSpot
SyncTenantToHubSpotJob         # Criar/atualizar Company no HubSpot
SyncDealStageJob               # Atualizar estágio do deal
UpdateMrrJob                   # Atualizar MRR no HubSpot

# HubSpot Onboarding
CreateOnboardingTicketJob      # Criar ticket quando tenant criado (opcional, feito via workflow)
UpdateOnboardingProgressJob    # Atualizar progresso do ticket (opcional)

# Privacy Tools
ProcessLgpdRequestJob          # Processar solicitação LGPD
ExportUserDataJob              # Exportar dados do titular
DeleteUserDataJob              # Deletar dados do titular

# Cleanup
CleanupOldWebhookEventsJob     # Limpar eventos antigos
CleanupExpiredSessionsJob      # Limpar sessões expiradas
```

### I.3.5 Ordem de Implementação Recomendada

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        ORDEM DE IMPLEMENTAÇÃO - DEVS                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  SEMANA 1: FUNDAÇÃO                                                                      │
│  ──────────────────                                                                      │
│  □ 1. Configurar projeto Rails + PostgreSQL                                              │
│  □ 2. Implementar multi-tenant isolation (ActsAsTenant ou similar)                       │
│  □ 3. Criar migrations do schema de banco                                                │
│  □ 4. Implementar TenantService básico                                                   │
│  □ 5. Configurar Sidekiq para background jobs                                           │
│                                                                                          │
│  SEMANA 2: AUTENTICAÇÃO (WorkOS)                                                         │
│  ────────────────────────────                                                            │
│  □ 6. Implementar WorkOSAuthService (SSO login)                                          │
│  □ 7. Implementar WorkOSWebhookService                                                   │
│  □ 8. Criar endpoints /auth/sso_url, /auth/callback                                      │
│  □ 9. Implementar session management                                                     │
│  □ 10. Testar login SSO com org de teste                                                 │
│                                                                                          │
│  SEMANA 3: BILLING (Stripe)                                                              │
│  ──────────────────────────                                                              │
│  □ 11. Implementar StripeWebhookService                                                  │
│  □ 12. Implementar StripeBillingService                                                  │
│  □ 13. Criar endpoints /billing/*                                                        │
│  □ 14. Testar checkout flow completo                                                     │
│  □ 15. Testar Customer Portal                                                            │
│                                                                                          │
│  SEMANA 4: CRM + ONBOARDING (HubSpot Tickets + Workflows)                                │
│  ────────────────────────────────────────────────────────                                │
│  □ 16. Implementar HubSpotSyncService                                                    │
│  □ 17. Implementar HubSpotOnboardingService (opcional, workflows fazem o trabalho)       │
│  □ 18. Configurar jobs de sincronização                                                  │
│  □ 19. Testar fluxo completo: Checkout → HubSpot → Ticket Onboarding                     │
│                                                                                          │
│  SEMANA 5: COMPLIANCE + POLISH                                                           │
│  ────────────────────────────                                                            │
│  □ 20. Implementar PrivacyToolsService                                                   │
│  □ 21. Implementar AuditLogService                                                       │
│  □ 22. Adicionar rate limiting e segurança                                               │
│  □ 23. Escrever testes automatizados                                                     │
│  □ 24. Documentar API                                                                    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## I.4 Checklist de Handoff (Gestor → Devs)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        CHECKLIST DE HANDOFF                                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  STRIPE                                                                                  │
│  □ Secret Key: sk_live_xxx                                                               │
│  □ Publishable Key: pk_live_xxx                                                          │
│  □ Webhook Secret: whsec_xxx                                                             │
│  □ Lista de Product IDs e Price IDs                                                      │
│  □ Customer Portal configurado e URL documentado                                         │
│                                                                                          │
│  HUBSPOT                                                                                 │
│  □ Access Token: pat-xxx                                                                 │
│  □ Portal ID: xxx                                                                        │
│  □ Pipeline IDs (Vendas + Onboarding)                                                    │
│  □ Stage IDs de cada pipeline                                                            │
│  □ Lista de propriedades customizadas criadas                                            │
│                                                                                          │
│  WORKOS                                                                                  │
│  □ API Key: sk_xxx (já existe)                                                           │
│  □ Client ID: client_xxx (já existe)                                                     │
│  □ Webhook Secret: xxx (já existe)                                                       │
│  □ Redirect URIs configurados                                                            │
│  □ Org ID de teste para desenvolvimento                                                  │
│                                                                                          │
│  PROFITWELL                                                                              │
│  □ Conectado ao Stripe (confirmação)                                                     │
│  □ Segments criados                                                                      │
│                                                                                          │
│  PRIVACY TOOLS                                                                           │
│  □ API Key: xxx                                                                          │
│  □ Webhook Secret: xxx                                                                   │
│  □ URL do Portal do Titular                                                              │
│                                                                                          │
│  HUBSPOT ONBOARDING (Tickets + Workflows)                                                │
│  □ Pipeline "Onboarding Cliente" criado com 7 stages                                     │
│  □ Workflows automatizados configurados (3 workflows)                                   │
│  □ Propriedades de ticket customizadas criadas                                           │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## I.5 Notas Finais

### O que NÃO precisa mais desenvolver (Trust Center removido):
- ~~Portal Trust Center~~ → Mantido no Notion + Website
- ~~Página de Subprocessadores~~ → Mantido no Notion
- ~~Página de Certificações~~ → Mantido no Notion

### Estimativa de Esforço Total:

| Responsável | Tempo Estimado | Dependências |
|-------------|----------------|--------------|
| **Gestor (Configuração SaaS)** | 2-3 dias | Nenhuma - pode começar agora |
| **Devs (Backend Rails)** | 4-5 semanas | Handoff do Gestor |
| **Total** | ~5-6 semanas | Paralelo após handoff |

### Benefícios desta Separação:
1. **Paralelismo**: Gestor configura enquanto devs preparam ambiente
2. **Clareza**: Cada um sabe exatamente o que fazer
3. **Sem bloqueios**: Devs não ficam esperando configurações
4. **Qualidade**: Menos ida e volta entre times
5. **Velocidade**: Entrega mais rápida do MVP Admin

---

## Histórico de Versões

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | Dez 2024 | Documento inicial de integrações |
| 2.0 | Jan 2026 | Análise Admin com Retool |
| 3.0 | 13 Jan 2026 | Consolidação Admin + Plataforma |
| 3.1 | 13 Jan 2026 | Reestruturado - Capítulo 2 com 17 seções, tabela resumo |
| 3.2 | 13 Jan 2026 | Guia HubSpot 6 fases + Integração Rails bidirecional + Apêndice F inicial (14 categorias) |
| 3.3 | 13 Jan 2026 | Apêndice F expandido para 24 seções - Cloud, Calendar, Analytics, Sales, Forms, Voice, etc. |
| 3.4 | 13 Jan 2026 | **F.14 expandido com Embedded Analytics**: Embeddable.com (dashboards para clientes), Trevor.io (self-service interno), HubCount BI (Brasil), Explo, Retool Embedded |
| 3.5 | 14 Jan 2026 | **Apêndices G e H**: Guias passo a passo detalhados para Ruby on Rails (produção) e Replit (prototipagem) com ordem de implementação, estrutura de arquivos, Gemfile, secrets e checklists |
| 3.6 | 14 Jan 2026 | **Apêndice I**: Separação de tarefas - Configuração SaaS (Gestor) vs Desenvolvimento (Devs Rails), com checklists detalhados e ordem de implementação |
| **3.7** | **9 Mai 2026** | **Auditoria de Conformidade vs código real.** Adicionada **Seção 0** (fonte de verdade — 31 integrações em produção, 2 stubs, 6 planejadas, 3 sub-documentadas). Corrigidos erros: `SENDGRID_API_KEY`→`MAILGUN_API_KEY` (§2.6.3 + Apêndice D); `STACKONE_API_KEY`→`MERGE_API_KEY` + chaves Gupy/Pandapé (Apêndice D); duplicação “Merge | Merge” (§2.7.2 marcada DEPRECATED, Apêndice A linha 14 zerada, Apêndice B consolidado, mapa ASCII §2.1.1). Reclassificações de status (Merge/Apify/Sentry/RabbitMQ/OpenMic/MS Graph/WhatsApp/Mailgun/Deepgram/LangSmith) de 🔄/📋 para ✅. Adicionados secrets Sentry, LangSmith, OTel, Elasticsearch, Redis (com `REDIS_ENCRYPTION_KEY` Fernet obrigatório em prod), RabbitMQ, Database. Documentadas integrações ausentes do doc original: **Resend**, **Sentry BE+FE**, **Elasticsearch**, **Celery**, **Twilio Voice SDK**, **MS Teams JS**, **Gemini Live Audio**, **OpenTelemetry**, **Vindi/Iugu** (stubs). Esclarecido que backend de produção é **FastAPI/Python** (`lia-agent-system`); Rails (`ats_api`) é legado. |

---

## Referências

- [analise-viabilidade-saas-stack.md](./analise-viabilidade-saas-stack.md) - Detalhamento Admin
- [INTEGRACOES-CUSTOS-VIABILIDADE.md](./INTEGRACOES-CUSTOS-VIABILIDADE.md) - Custos detalhados e análise concorrentes
- [LIA_AGENT_ARCHITECTURE_COMPLETE.md](./LIA_AGENT_ARCHITECTURE_COMPLETE.md) - Arquitetura de Agentes
- [COMPLETE_SYSTEM_ARCHITECTURE.md](./architecture/COMPLETE_SYSTEM_ARCHITECTURE.md) - Arquitetura técnica
