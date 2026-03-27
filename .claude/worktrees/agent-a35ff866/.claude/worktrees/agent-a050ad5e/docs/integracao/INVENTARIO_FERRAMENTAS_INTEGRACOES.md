# Inventário Completo de Ferramentas, LLMs e Integrações

> **Documento de Referência Central - WeDo Talent**

**Versão:** 4.1 (Atualizado — Sprint de Qualidade v2)
**Data:** 28 de Fevereiro de 2026
**Autor:** Equipe WeDOTalent

> **Changelog v4.1 (2026-02-28):** Sentry (BE+FE) integrado ✅; LangSmith com `@traceable` integrado ✅; Redis rate limiter sliding window integrado ✅; Prometheus com 8 métricas + endpoint `/metrics` documentado. Status: 18 integrações ativas (era 15).

---

## RESUMO EXECUTIVO

Este documento consolida toda a análise de integrações, custos e arquitetura do WeDo Talent, organizado em dois capítulos principais:

| Capítulo | Escopo | Ferramentas | Linhas Atuais |
|----------|--------|-------------|---------------|
| **Capítulo 1: WeDo Talent Admin** | Gestão de clientes, billing, compliance | Stripe, ProfitWell, HubSpot, Arrows, WorkOS, Vanta/Drata, Privacy Tools, Warden AI | ~30.200 substituídas |
| **Capítulo 2: WeDo Talent Plataforma** | Funil de Talentos e Vagas | Claude, Gemini, LangGraph, Pearch, Deepgram, OpenMic, SendGrid, WhatsApp, MS Graph, StackOne | Core do produto |

### Filosofia: Desenvolver Mínimo, Integrar Máximo

> **70% SaaS + 30% Interno** = Menos código para manter, mais tempo para features de valor

---

## Sumário

1. [Resumo Executivo](#resumo-executivo)
2. [Mapa de Integrações Visual](#mapa-de-integrações-visual-completo)
3. [Tabela Consolidada Expandida](#tabela-consolidada-expandida)
4. [Custos por Capítulo](#custos-por-capítulo)
5. [O Que Desenvolver Internamente (30%)](#o-que-desenvolver-internamente-30)
6. [Capítulo 1: Admin](#capítulo-1-wedo-talent-admin)
7. [Capítulo 2: Plataforma](#capítulo-2-wedo-talent-plataforma)
8. [Guias de Configuração](#guias-de-configuração)
9. [Webhooks a Configurar](#webhooks-a-configurar)
10. [Métricas Disponíveis por Ferramenta](#métricas-disponíveis-por-ferramenta)
11. [Checklist de Setup/Handoff](#checklist-de-setuphandoff)
12. [Ordem de Implementação](#ordem-de-implementação)
13. [Subprocessadores de Dados](#subprocessadores-de-dados)
14. [Bibliotecas e Frameworks](#bibliotecas-e-frameworks)
15. [Apêndices](#apêndices)
16. [Histórico de Versões](#histórico-de-versões)

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
│    │          (Capítulo 1 - 8 SaaS)                  │    │        (Capítulo 2 - 25+ APIs)                  │   │
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
│    │    │  ┌─────────┐      ┌──────────┐      │     │    │    │  ┌─────────┐ ┌─────────┐ ┌────────┐│     │   │
│    │    │  │ HubSpot │      │  Arrows  │      │     │    │    │  │LangGraph│ │LangChain│ │LangSmith││     │   │
│    │    │  │   CRM   │      │Onboarding│      │     │    │    │  │  Graph  │ │ Chains  │ │ Traces ││     │   │
│    │    │  │  📇     │      │  🎯     │      │     │    │    │  │  🔄     │ │  ⛓️    │ │  🔍   ││     │   │
│    │    │  └─────────┘      └──────────┘      │     │    │    │  └─────────┘ └─────────┘ └────────┘│     │   │
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
│    │                                                 │    │    │  │MS Graph│ │WhatsApp│ │SendGrid │ │     │   │
│    └─────────────────────────────────────────────────┘    │    │  │Calendar│ │  API   │ │  Email  │ │     │   │
│                                                            │    │  │  📅    │ │  💬   │ │  ✉️    │ │     │   │
│                                                            │    │  └────────┘ └────────┘ └─────────┘ │     │   │
│                                                            │    └─────────────────────────────────────┘     │   │
│                                                            │                                                 │   │
│                                                            │    ┌─────────────────────────────────────┐     │   │
│                                                            │    │         INTEGRAÇÕES ATS             │     │   │
│                                                            │    │  ┌─────────┐ ┌────────┐ ┌─────────┐ │     │   │
│                                                            │    │  │StackOne │ │ Merge  │ │Gupy/    │ │     │   │
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
│   │  Arrows  │        │                                               │         │                   │
│   │Onboarding│        │         👥 FUNIL DE TALENTOS                  │         ▼                   │
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
│        │              │  │  MS Graph │ WhatsApp │ SendGrid         │  │                              │
│        │              │  └─────────────────────────────────────────┘  │                              │
│        │              │                    │                          │                              │
│        │              │                    ▼                          │                              │
│        │              │  ┌─────────────────────────────────────────┐  │                              │
│        │              │  │         INTEGRAÇÕES ATS                 │  │                              │
│        │              │  │  StackOne │ Merge │ Gupy │ Pandapé      │  │                              │
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

---

## TABELA CONSOLIDADA EXPANDIDA

### Capítulo 1: Admin (70% SaaS)

| Ferramenta | Website | Para que serve | Modelo/Versão | Env Var | Tipo Custo | Pricing | Free Tier | Status | Notas |
|------------|---------|----------------|---------------|---------|------------|---------|-----------|--------|-------|
| **Stripe** | stripe.com | Billing, subscriptions, invoices, customer portal | API v2024 | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` | % transação | 2.9% + $0.30/tx | - | 🔶 PLANEJADO | Customer Portal elimina UI |
| **ProfitWell** | profitwell.com | Métricas SaaS: MRR, Churn, LTV, ARR, ARPU | - | - | Gratuito | $0 (100% grátis) | ✅ Ilimitado | 🔶 PLANEJADO | Conecta 1-click Stripe |
| **HubSpot** | hubspot.com | CRM clientes, dashboard, deals, companies | Free/Starter/Pro | `HUBSPOT_ACCESS_TOKEN` | Freemium | Free, Starter: $20, Pro: $890 | ✅ Free CRM | 🔶 PLANEJADO | Central de dados clientes |
| **Arrows** | arrows.to | Onboarding tracking, playbooks, tasks | - | - | Pago mensal | $300-750/mês | - | 🔶 PLANEJADO | Integra nativo HubSpot |
| **WorkOS** | workos.com | SSO Enterprise (SAML, OIDC), MFA, SCIM | API v2 | `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_WEBHOOK_SECRET` | Por usuário | SSO: $50+$0.30/user, SCIM: $50 | - | ✅ INTEGRADO | 40+ IdPs suportados |
| **Vanta** | vanta.com | Compliance SOC 2, ISO 27001, HIPAA | - | - | Pago anual | $12-24k/ano | - | 🔶 PLANEJADO | Líder mercado, 100+ integs |
| **Drata** | drata.com | Compliance SOC 2, ISO 27001 (alt. Vanta) | - | - | Pago anual | $12-24k/ano | - | 🔶 PLANEJADO | Alternativa ao Vanta |
| **Privacy Tools** | privacytools.com.br | Portal LGPD, RIPD, consentimentos, titular | - | - | Pago anual | R$ 3.600-7.200/ano | - | 🔶 PLANEJADO | Específico Brasil |
| **Warden AI** | warden.ai | Auditoria viés IA, fairness, bias monitoring | - | - | Pago | A definir | - | ⭕ FUTURO | NYC LL144, EU AI Act |

### Capítulo 2: Plataforma (Core Product)

| Ferramenta | Website | Para que serve | Modelo/Versão | Env Var | Tipo Custo | Pricing | Free Tier | Status | Notas |
|------------|---------|----------------|---------------|---------|------------|---------|-----------|--------|-------|
| **Claude (Anthropic)** | anthropic.com | LLM principal - LIA conversacional, triagem WSI, parecer, análise CV | Claude 3.5 Sonnet (claude-3-5-sonnet-20241022) | `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | Token | $3/M input, $15/M output | - | ✅ INTEGRADO | Replit Integration |
| **Google Gemini** | ai.google.dev | Semantic Search, fallback LLM, voice-to-text | Gemini 1.5/2.0 Flash | `AI_INTEGRATIONS_GEMINI_API_KEY` | Token | $0.075/M input, $0.30/M output | ✅ Generoso | ✅ INTEGRADO | Replit Integration |
| **OpenAI** | openai.com | Fallback LLM, embeddings (reserva) | GPT-4o, GPT-4o-mini | `OPENAI_API_KEY` | Token | $5/M input, $15/M output | - | 🔶 PLANEJADO | Fallback chain |
| **LangGraph** | github.com/langchain-ai/langgraph | Orquestração de agentes, workflows multi-step | v0.2.53+ | - | OSS | $0 (gratuito) | ✅ OSS | ✅ INTEGRADO | Core orchestration |
| **LangChain** | langchain.com | Framework LLM, chains, prompts, memory | v0.3.9+ | - | OSS | $0 (gratuito) | ✅ OSS | ✅ INTEGRADO | Core framework |
| **LangSmith** | smith.langchain.com | Monitoramento LLM, tracing agentes, debugging | Cloud | `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_TRACING_V2` | Freemium | Free: 5k traces, Plus: $39/mês | ✅ 5k traces | ✅ INTEGRADO | `@traceable` em ReActLoop.run() + ClaudeLLMProvider.generate*() — spans visíveis no dashboard LangSmith |
| **Pearch AI** | pearch.ai | Busca candidatos, 800M+ perfis, sourcing | API | `PEARCH_API_KEY`, `PEARCH_API_URL` | Por crédito | ~$0.10-0.50/profile | - | 🔶 PLANEJADO | Feature flag: `ENABLE_PEARCH_AI` |
| **Apify** | apify.com | Web scraping LinkedIn, enriquecimento perfis | Cloud | `APIFY_API_KEY` | Freemium | Free: $5/mês, Starter: $49 | ✅ $5/mês | ✅ INTEGRADO | - |
| **Deepgram** | deepgram.com | Speech-to-text (WhatsApp, entrevistas) | Nova-2 (pt-BR) | `DEEPGRAM_API_KEY`, `DEEPGRAM_WEBHOOK_SECRET` | Por minuto | $0.0043/min | ✅ $200 créditos | 🔶 PLANEJADO | Melhor para pt-BR |
| **OpenMic.ai** | openmic.ai | Voice screening automatizado, ligações | API | `OPENMIC_API_KEY`, `OPENMIC_WEBHOOK_SECRET`, `OPENMIC_WEBHOOK_URL` | Por minuto | $0.08-0.15/min | - | 🔶 PLANEJADO | TTS + STT + AI |
| **Synthflow** | synthflow.ai | AI Voice Agent (alt. OpenMic) | - | `SYNTHFLOW_API_KEY`, `SYNTHFLOW_API_URL` | Pago | Consultar | - | 🔶 PLANEJADO | Alternativa |
| **Resend** | resend.com | Email transacional (primário) | API | `RESEND_API_KEY` | Freemium | Free: 100/dia, Pro: $20/mês | ✅ 100/dia | 🔶 PLANEJADO | - |
| **SendGrid** | sendgrid.com | Email transacional (alternativo) | API | `SENDGRID_API_KEY` | Freemium | Free: 100/dia, Essentials: $19.95 | ✅ 100/dia | 🔶 PLANEJADO | - |
| **Twilio** | twilio.com | WhatsApp Business API, SMS | API | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` | Por msg | WhatsApp: $0.005-0.08/msg | ✅ 1000 msg grátis | 🔶 PLANEJADO | - |
| **Microsoft Graph** | developer.microsoft.com/graph | Calendário, agendamento entrevistas | API v1.0 | `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` | Gratuito | $0 (rate limits) | ✅ 100% grátis | 🔶 PLANEJADO | - |
| **Microsoft Teams** | teams.microsoft.com | Notificações recrutamento | Webhook/Bot | `TEAMS_WEBHOOK_URL`, `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` | Gratuito | Webhook: $0 | ✅ Webhook grátis | 🔶 PLANEJADO | - |
| **Merge.dev** | merge.dev | Unified ATS/HRIS API (60+ ATSs, 80+ HRISs) | API | `MERGE_API_KEY`, `MERGE_WEBHOOK_SECRET` | Por linked account | ~$650/mês (10 accounts) | ✅ 3 conexões | ✅ INTEGRADO | Cobertura ampla |
| **StackOne** | stackone.com | Unified ATS API (alt. Merge, Gupy/Pandapé) | API | `STACKONE_API_KEY`, `STACKONE_API_URL` | Por conexão | Consultar | - | 🔶 PLANEJADO | Melhor para BR |
| **Gupy** | gupy.io | ATS brasileiro (direto) | API | `GUPY_API_KEY`, `GUPY_BASE_URL`, `GUPY_WEBHOOK_SECRET` | Via cliente | Via cliente | - | 🔶 PLANEJADO | Preferir Merge |
| **Pandapé** | pandape.com | ATS brasileiro (direto) | API | `PANDAPE_API_KEY`, `PANDAPE_BASE_URL`, `PANDAPE_WEBHOOK_SECRET` | Via cliente | Via cliente | - | 🔶 PLANEJADO | Preferir Merge |

### Infraestrutura Compartilhada

| Ferramenta | Website | Para que serve | Modelo/Versão | Env Var | Tipo Custo | Pricing | Free Tier | Status | Notas |
|------------|---------|----------------|---------------|---------|------------|---------|-----------|--------|-------|
| **Replit** | replit.com | Ambiente dev, hosting, PostgreSQL | Core/Teams | - | Pago mensal | $25-100/mês | - | ✅ INTEGRADO | @wedo_talent |
| **PostgreSQL (Neon)** | neon.tech | Banco de dados principal, pgvector | Neon via Replit | `DATABASE_URL`, `PGHOST`, `PGUSER`, `PGPASSWORD` | Incluído | Incluído Replit | ✅ Incluído | ✅ INTEGRADO | Vector search |
| **Redis (Upstash)** | upstash.com | Cache semantic search, sessões, rate limiting com sliding window | Serverless | `REDIS_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Freemium | Free: 10k cmds/dia | ✅ 10k/dia | ✅ INTEGRADO | Rate limiter migrado de 4 dicts in-memory para Redis ZSET sliding window atômica (Sprint A-4) |
| **RabbitMQ (CloudAMQP)** | cloudamqp.com | Message queue, event-driven, jobs async | Little Lemur+ | `CLOUDAMQP_URL`, `RABBITMQ_URL` | Freemium | Free: Little Lemur, Tiger: $19 | ✅ Little Lemur | 🔶 PLANEJADO | Alt: Celery+Redis |
| **GCP/Azure** | cloud.google.com | Cloud storage, CDN, serviços adicionais | - | `GCP_PROJECT_ID`, `GCP_CREDENTIALS`, `AZURE_STORAGE_KEY` | Freemium | Free tier generoso | ✅ Free tier | 🔶 PLANEJADO | Complemento Replit |

### DevTools & Observabilidade

| Ferramenta | Website | Para que serve | Modelo/Versão | Env Var | Tipo Custo | Pricing | Free Tier | Status | Notas |
|------------|---------|----------------|---------------|---------|------------|---------|-----------|--------|-------|
| **Figma** | figma.com | Design UI/UX, protótipos, design system | - | - | Freemium | Free: Starter, Pro: $15/user | ✅ 3 projetos | 🔶 PLANEJADO | Handoff Storybook |
| **Jira** | atlassian.com/jira | Gestão de projetos, sprints, backlog | Cloud | - | Freemium | Free: 10 users | ✅ 10 users | ✅ INTEGRADO | Sync GitHub |
| **GitHub** | github.com | Controle de versão, CI/CD, code review | - | - | Freemium | Free: repos ilimitados | ✅ Ilimitado | ✅ INTEGRADO | GitHub Actions |
| **Notion** | notion.so | Documentação, knowledge base, Trust Center | - | Notion OAuth | Freemium | Free, Plus: $10/mês | ✅ Times pequenos | ✅ INTEGRADO | Via Replit Connector |
| **Prometheus** | prometheus.io | Métricas de aplicação e performance (LLM, agentes, compliance, resiliência, HTTP) | OSS | - | Gratuito | Gratuito | ✅ OSS | ✅ INTEGRADO | 8 métricas estratégicas em `app/observability/metrics.py` + endpoint `/metrics`; instrumentado em llm_claude.py, react_loop.py, fairness_guard.py, circuit_breaker.py (Sprint B-2) |
| **Sentry** | sentry.io | Error tracking + performance monitoring — backend FastAPI e frontend Next.js | Cloud | `SENTRY_DSN` (BE), `NEXT_PUBLIC_SENTRY_DSN` (FE) | Freemium | Free: 5k errors, Team: $26 | ✅ 5k errors | ✅ INTEGRADO | Backend: FastApiIntegration + StarletteIntegration + `capture_exception` no handler global; Frontend: `@sentry/nextjs` + `ErrorBoundary` React com `Sentry.captureException` (Sprint A-3, C-4) |

### Resumo por Status

| Status | Quantidade | Descrição |
|--------|------------|-----------|
| ✅ INTEGRADO | 18 (+3) | Configurado e funcionando — Sentry, LangSmith e Redis atualizados neste sprint |
| 🔶 PLANEJADO | 25 (-3) | Código pronto, aguardando ativação (env vars) |
| ⭕ FUTURO | 1 | Em roadmap, ainda não implementado |
| **TOTAL** | **44** | Atualizado em 2026-02-28 (Sprint de Qualidade v2) |

---

## CUSTOS POR CAPÍTULO

### Tabela Resumo por Capítulo

| Área | Custo MÍNIMO | Custo Recomendado | Custo Scale |
|------|--------------|-------------------|-------------|
| **Admin (SaaS)** | $0 | R$ 107k/ano | R$ 195k/ano |
| **Plataforma (APIs)** | $30/mês | $2.700/mês | $12.750/mês |
| **Infraestrutura Fixa** | $20/mês | $265/mês | $1.159/mês |
| **TOTAL MVP** | **$50/mês** | - | - |

### Custos Consolidados por Número de Clientes

| Cenário | Clientes | Custo Mensal | Custo Anual | Por Cliente/Mês |
|---------|----------|--------------|-------------|-----------------|
| **MVP/Bootstrap** | 1 | **$30** | **$360** | $30 |
| **Startup** | 10 | $3.985 | **$47.820** | $399 |
| **Growth** | 50 | $26.896 | **$322.752** | $538 |
| **Scale** | 100 | $58.599 | **$703.188** | $586 |

### Custo Variável por Cliente (Mensal)

| Integração | Mínimo | Pequeno | Médio | Grande |
|------------|--------|---------|-------|--------|
| **Claude (LLM)** | $10 | $25 | $45 | $100 |
| **Gemini** | $0 | $0.50 | $0.50 | $1 |
| **LangSmith** | $0 | $0 | $5 | $20 |
| **Pearch** | $0 | $50 | $200 | $500 |
| **Deepgram** | $0 | $0.50 | $2 | $9 |
| **OpenMic** | $0 | $50 | $100 | $200 |
| **WhatsApp** | $0 | $5 | $20 | $50 |
| **SendGrid** | $0 | $5 | $10 | $20 |
| **WorkOS** | $0 | $0 | $250 | $250 |
| **StackOne/Merge** | $0 | $0 | $65 | $100 |
| **TOTAL** | **$10** | **$136** | **$700** | **$1.258** |

### Custo Fixo da Plataforma (Mensal)

| Item | Mínimo | Recomendado | Premium |
|------|--------|-------------|---------|
| Replit (hosting) | $20 | $100 | $200 |
| PostgreSQL | $0 | $0 | $50 |
| Redis | $0 | $7 | $30 |
| RabbitMQ (CloudAMQP) | $0 | $19 | $49 |
| LangSmith | $0 | $39 | $200 |
| GCP/Azure | $0 | $50 | $300 |
| Figma (time) | $0 | $50 | $200 |
| **TOTAL FIXO** | **$20** | **$265** | **$1.159** |

---

## O QUE DESENVOLVER INTERNAMENTE (30%)

### Capítulo 1: Admin (~9.000 linhas estimadas)

| Componente | Linhas Estimadas | O que é |
|------------|------------------|---------|
| Multi-tenant isolation | ~1.500 | ActsAsTenant + row-level security |
| Webhook processing | ~2.000 | Stripe, WorkOS, HubSpot, Arrows |
| Sync services | ~2.500 | Bidirecional com HubSpot |
| API endpoints | ~1.500 | REST APIs para admin |
| Background jobs | ~1.500 | Sidekiq/Celery jobs |
| **TOTAL ADMIN** | **~9.000** | |

### Capítulo 2: Plataforma (~25.000 linhas)

| Componente | Linhas Estimadas | O que é |
|------------|------------------|---------|
| Agentes LIA (LangGraph) | ~5.000 | Job Intake, Screening, Communication, Scheduling |
| WSI Analysis | ~3.000 | Análise de competências, scoring |
| Integração ATS | ~4.000 | StackOne, Merge, diretos |
| Comunicação multi-canal | ~3.000 | Email, WhatsApp, Calendar |
| Voice/STT | ~2.500 | Deepgram, OpenMic |
| Semantic Search | ~2.500 | Gemini + pgvector |
| API REST | ~3.000 | Endpoints plataforma |
| Background jobs | ~2.000 | Celery jobs |
| **TOTAL PLATAFORMA** | **~25.000** | |

---

## CAPÍTULO 1: WEDO TALENT ADMIN

### Arquitetura Admin (70% SaaS)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               WEDO TALENT ADMIN - ARQUITETURA                                │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│   │   STRIPE    │    │  PROFITWELL │    │   HUBSPOT   │    │   ARROWS    │                 │
│   │   Billing   │───►│   Metrics   │    │     CRM     │◄──►│  Onboarding │                 │
│   │  💳 2.9%   │    │  📊 $0     │    │  📇 $0-890  │    │  🎯 $300-750 │                 │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘                 │
│          │                  ▲                  │                  │                         │
│          │                  │                  │                  │                         │
│          ▼                  │                  ▼                  │                         │
│   ┌─────────────────────────┴──────────────────┴──────────────────┴─────────────────┐      │
│   │                                                                                  │      │
│   │                            BACKEND ADMIN (~9k linhas)                            │      │
│   │                                                                                  │      │
│   │   • Multi-tenant isolation    • Webhook processing    • Sync services           │      │
│   │   • API REST                  • Background jobs        • Audit logs             │      │
│   │                                                                                  │      │
│   └─────────────────────────────────────────────────────────────────────────────────┘      │
│          │                                      │                                           │
│          ▼                                      ▼                                           │
│   ┌─────────────┐                        ┌─────────────┐                                   │
│   │   WORKOS    │                        │PRIVACY TOOLS│                                   │
│   │  SSO/SCIM   │                        │    LGPD     │                                   │
│   │  🔐 $50+   │                        │  🇧🇷 R$3.6k │                                   │
│   └─────────────┘                        └─────────────┘                                   │
│          │                                      │                                           │
│          └──────────────────┬───────────────────┘                                           │
│                             ▼                                                               │
│                      ┌─────────────┐                                                        │
│                      │VANTA/DRATA  │                                                        │
│                      │ Compliance  │                                                        │
│                      │ ✅ $12-24k  │                                                        │
│                      └─────────────┘                                                        │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## CAPÍTULO 2: WEDO TALENT PLATAFORMA

### Arquitetura Plataforma (Core Product)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            WEDO TALENT PLATAFORMA - ARQUITETURA                              │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                   LLMs & ORQUESTRAÇÃO                                │   │
│   │                                                                                      │   │
│   │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │   │
│   │   │ Claude  │    │ Gemini  │    │LangGraph│    │LangChain│    │LangSmith│          │   │
│   │   │  🧠    │    │  🔮    │    │  🔄    │    │  ⛓️    │    │  🔍    │          │   │
│   │   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘          │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                   │
│                                          ▼                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                  AGENTES LIA                                         │   │
│   │                                                                                      │   │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │   │
│   │   │  Job Intake   │  │   Screening   │  │ Communication │  │  Scheduling   │       │   │
│   │   │    Agent      │  │     Agent     │  │     Agent     │  │    Agent      │       │   │
│   │   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘       │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                   │
│              ┌───────────────────────────┼───────────────────────────┐                      │
│              ▼                           ▼                           ▼                      │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐             │
│   │    SOURCING         │   │      VOZ & STT      │   │    COMUNICAÇÃO      │             │
│   │  ┌───────┐ ┌──────┐ │   │  ┌───────┐ ┌─────┐ │   │  ┌──────┐ ┌───────┐ │             │
│   │  │Pearch │ │Apify │ │   │  │Deepgrm│ │OpnMc│ │   │  │MSGrph│ │WhtsAp │ │             │
│   │  │ 🔎   │ │ 🕷️  │ │   │  │ 🎤   │ │ 📞 │ │   │  │ 📅   │ │ 💬   │ │             │
│   │  └───────┘ └──────┘ │   │  └───────┘ └─────┘ │   │  └──────┘ └───────┘ │             │
│   └─────────────────────┘   └─────────────────────┘   │  ┌──────┐ ┌───────┐ │             │
│                                                        │  │SndGrd│ │Resend │ │             │
│                                                        │  │ ✉️   │ │ ✉️   │ │             │
│                                                        │  └──────┘ └───────┘ │             │
│                                                        └─────────────────────┘             │
│                                          │                                                   │
│                                          ▼                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                               INTEGRAÇÕES ATS                                        │   │
│   │                                                                                      │   │
│   │   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐                     │   │
│   │   │   StackOne    │     │    Merge      │     │  Gupy/Pandapé │                     │   │
│   │   │   Unified     │     │   60+ ATSs    │     │   Brasileiro  │                     │   │
│   │   │    🔗        │     │    🔗        │     │    🇧🇷       │                     │   │
│   │   └───────────────┘     └───────────────┘     └───────────────┘                     │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## GUIAS DE CONFIGURAÇÃO

### Stripe (Billing)

**Passo a Passo:**

1. **Criar conta Stripe:** stripe.com → Dashboard
2. **Criar produtos e preços:**
   - Starter: R$ 1.490/mês
   - Professional: R$ 3.490/mês
   - Enterprise: R$ 7.990/mês
3. **Configurar Customer Portal:** Settings > Customer Portal
4. **Criar webhooks:** Developers > Webhooks

**Secrets Replit:**
```bash
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### HubSpot (CRM)

**Passo a Passo:**

1. **Criar Private App:** Settings > Integrations > Private Apps
2. **Scopes necessários:**
   - `crm.objects.companies.read/write`
   - `crm.objects.contacts.read/write`
   - `crm.objects.deals.read/write`
3. **Criar propriedades customizadas:**
   - `wedo_client_id`, `wedo_plan`, `wedo_status`, `wedo_mrr`
4. **Configurar pipeline de Deals:**
   - Stages: Proposta Enviada → Contrato Assinado → Cliente Ativo → Perdido

**Secrets Replit:**
```bash
HUBSPOT_ACCESS_TOKEN=pat-xxx
```

### WorkOS (SSO/SCIM)

**Já configurado. Secrets existentes:**
```bash
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx
WORKOS_WEBHOOK_SECRET=xxx
```

---

## WEBHOOKS A CONFIGURAR

### Stripe Webhooks

| Evento | Ação | Endpoint |
|--------|------|----------|
| `customer.subscription.created` | Ativar cliente | `/api/webhooks/stripe` |
| `customer.subscription.updated` | Atualizar plano | `/api/webhooks/stripe` |
| `customer.subscription.deleted` | Suspender acesso | `/api/webhooks/stripe` |
| `invoice.paid` | Registrar pagamento | `/api/webhooks/stripe` |
| `invoice.payment_failed` | Iniciar dunning | `/api/webhooks/stripe` |

### HubSpot Webhooks

| Evento | Ação | Endpoint |
|--------|------|----------|
| `company.propertyChange` | Sync bidirecional | `/api/webhooks/hubspot` |
| `deal.propertyChange` | Atualizar estágio | `/api/webhooks/hubspot` |
| `deal.creation` | Registrar oportunidade | `/api/webhooks/hubspot` |
| `contact.creation` | Sync usuário | `/api/webhooks/hubspot` |

### WorkOS Webhooks

| Evento | Ação | Endpoint |
|--------|------|----------|
| `connection.activated` | Habilitar SSO | `/api/webhooks/workos` |
| `dsync.user.created` | Provisionar usuário | `/api/webhooks/workos` |
| `dsync.user.deleted` | Desprovision usuário | `/api/webhooks/workos` |
| `dsync.group.user_added` | Atualizar grupo | `/api/webhooks/workos` |

---

## MÉTRICAS DISPONÍVEIS POR FERRAMENTA

### ProfitWell (100% Grátis)

| Métrica | Descrição |
|---------|-----------|
| **MRR** | Receita recorrente mensal |
| **Net MRR** | MRR novo - churned - contraction + expansion |
| **Churn Rate** | % de clientes que cancelaram |
| **LTV** | Valor esperado do cliente |
| **ARPU** | Receita média por usuário |
| **CAC Payback** | Tempo para recuperar CAC |

### LangSmith (Observabilidade LLM)

| Métrica | Descrição |
|---------|-----------|
| **Traces** | Execuções de agentes |
| **Latência** | Tempo de resposta P50/P95/P99 |
| **Token Usage** | Consumo por modelo |
| **Error Rate** | Taxa de erros |
| **Cost** | Custo por trace |

### KPIs para Monitorar

| KPI | Meta | Alerta |
|-----|------|--------|
| **Custo LLM/cliente** | <$60/mês | >$100/mês |
| **Custo Pearch/cliente** | <$200/mês | >$400/mês |
| **Custo total/cliente** | <$600/mês | >$1.000/mês |
| **Margem bruta** | >65% | <50% |
| **API uptime** | >99.5% | <99% |
| **Latência P95** | <500ms | >1s |

---

## CHECKLIST DE SETUP/HANDOFF

### Checklist Completo

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
│  ARROWS                                                                                  │
│  □ API Key: xxx                                                                          │
│  □ Template IDs de onboarding                                                            │
│  □ Conectado ao HubSpot (confirmação)                                                    │
│                                                                                          │
│  LLMs & PLATAFORMA                                                                       │
│  □ ANTHROPIC_API_KEY (via Replit Integration - já existe)                                │
│  □ GEMINI_API_KEY (via Replit Integration - já existe)                                   │
│  □ DEEPGRAM_API_KEY                                                                      │
│  □ PEARCH_API_KEY                                                                        │
│  □ SENDGRID_API_KEY                                                                      │
│  □ TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN                                                 │
│  □ MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET                                          │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ORDEM DE IMPLEMENTAÇÃO

### Roadmap de Integrações 2025-2026

```
         Q1 2025        Q2 2025        Q3 2025        Q4 2025
    ┌──────────────┬──────────────┬──────────────┬──────────────┐
    │   FASE 1     │   FASE 2     │   FASE 3     │   FASE 4     │
    │ Core Stack   │ Comunicação  │  Enterprise  │ Otimização   │
    ├──────────────┼──────────────┼──────────────┼──────────────┤
    │ • Claude     │ • MS Graph   │ • StackOne   │ • LLM tuning │
    │ • Gemini     │ • WhatsApp   │ • Merge      │ • Multi-cloud│
    │ • LangGraph  │ • SendGrid   │ • OpenMic    │ • Analytics  │
    │ • LangChain  │ • RabbitMQ   │ • GCP/Azure  │ • Dashboards │
    │ • LangSmith  │ • Apify      │              │              │
    │ • Pearch     │              │              │              │
    │ • Deepgram   │              │              │              │
    │ • WorkOS     │              │              │              │
    └──────────────┴──────────────┴──────────────┴──────────────┘
         $3-5K           $8-15K         $20-35K        $40-80K
```

### Ordem de Implementação - Admin (Semana 1-2)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│   SEMANA 1: BILLING & CRM                                                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ETAPA 1: Stripe Billing (2-3 dias)                                                     │
│   ────────────────────────────────────                                                   │
│   □ pip install stripe / npm install @stripe/stripe-js                                   │
│   □ Criar endpoints:                                                                     │
│     - POST /api/billing/create-checkout-session                                          │
│     - POST /api/billing/create-portal-session                                            │
│     - POST /api/webhooks/stripe                                                          │
│   □ Testar checkout flow em test mode                                                    │
│                                                                                          │
│   ETAPA 2: HubSpot CRM Sync (2-3 dias)                                                   │
│   ────────────────────────────────────                                                   │
│   □ pip install hubspot-api-client                                                       │
│   □ Criar endpoints:                                                                     │
│     - POST /api/clients/sync-hubspot                                                     │
│     - GET /api/clients/{id}/hubspot-status                                               │
│   □ Testar sync bidirecional                                                             │
│                                                                                          │
│   ETAPA 3: WorkOS SSO (1-2 dias - revisar)                                               │
│   ────────────────────────────────────                                                   │
│   □ Verificar SSO login flow                                                             │
│   □ Verificar SCIM webhooks                                                              │
│   □ Testar com org de teste                                                              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Ordem de Implementação - Plataforma (Semana 2-5)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│   SEMANA 2-3: CORE AI                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ETAPA 1: Claude + LangGraph (3-5 dias)                                                 │
│   ───────────────────────────────────────                                                │
│   Status: ⚠️ PARCIALMENTE IMPLEMENTADO                                                   │
│   □ Verificar app/agents/ - estrutura de agentes                                         │
│   □ Completar: Job Intake, Screening, Communication, Scheduling Agents                   │
│                                                                                          │
│   ETAPA 2: Deepgram STT (2-3 dias)                                                       │
│   ─────────────────────────────────                                                      │
│   □ pip install deepgram-sdk                                                             │
│   □ Endpoints:                                                                           │
│     - POST /api/voice/transcribe                                                         │
│     - WebSocket /ws/voice/stream                                                         │
│                                                                                          │
│   ETAPA 3: WSI Analysis (3-5 dias)                                                       │
│   ─────────────────────────────────                                                      │
│   □ Criar app/services/wsi_service.py                                                    │
│   □ Endpoints:                                                                           │
│     - POST /api/screening/analyze                                                        │
│     - GET /api/screening/{id}/wsi-score                                                  │
│     - GET /api/screening/{id}/lia-opinion                                                │
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│   SEMANA 4-5: COMUNICAÇÃO                                                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ETAPA 4: Email Notifications (2-3 dias)                                                │
│   ─────────────────────────────────────────                                              │
│   □ pip install sendgrid                                                                 │
│   □ Templates: Convite screening, Resultado triagem, Convite entrevista                  │
│                                                                                          │
│   ETAPA 5: WhatsApp + Calendar (3-5 dias)                                                │
│   ───────────────────────────────────────                                                │
│   □ pip install twilio msal                                                              │
│   □ Endpoints:                                                                           │
│     - POST /api/communication/send-whatsapp                                              │
│     - POST /api/calendar/schedule-interview                                              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## SUBPROCESSADORES DE DADOS

Esta seção lista todos os terceiros que processam dados em nome da WeDoTalent/LIA (relevante para LGPD/GDPR):

| Subprocessador | Tipo de Dados | Localização | DPA |
|----------------|---------------|-------------|-----|
| **Anthropic** | Prompts/Responses (LLM) | US | Sim |
| **Google Cloud** | Prompts/Responses (Gemini) | US/EU | Sim |
| **Replit/Neon** | Dados completos (DB) | US | Sim |
| **Stripe** | Dados de pagamento | US | Sim |
| **Merge.dev** | Dados ATS (candidatos) | US | Sim |
| **WorkOS** | Dados de autenticação | US | Sim |
| **Vanta/Drata** | Logs de compliance | US | Sim |
| **Privacy Tools** | Dados LGPD (consentimentos) | BR | Sim |
| **Deepgram** | Áudio de entrevistas | US | Sim |
| **OpenMic.ai** | Áudio de screening | US | Consultar |
| **Twilio** | Telefone/WhatsApp | US | Sim |
| **HubSpot** | Dados de clientes | US/EU | Sim |
| **Arrows** | Dados de onboarding | US | Consultar |
| **Resend/SendGrid** | Email (endereço + conteúdo) | US | Sim |
| **Pearch AI** | Dados de perfil profissional | US | Consultar |
| **Apify** | Dados públicos scraping | EU | Sim |

---

## BIBLIOTECAS E FRAMEWORKS

### Frontend (plataforma-lia)

| Biblioteca | Versão | Propósito |
|------------|--------|-----------|
| Next.js | 15.3.2 | Framework React |
| React | 19.0.0 | UI Library |
| TypeScript | 5.8.3 | Type Safety |
| Tailwind CSS | 3.4.17 | Styling |
| Radix UI | latest | Componentes acessíveis |
| shadcn/ui | latest | Design System |
| Recharts | 3.2.1 | Gráficos |
| Framer Motion | 12.23.22 | Animações |
| Storybook | 10.1.4 | Component Dev |
| Lucide React | 0.475.0 | Ícones |

### Backend (lia-agent-system)

| Biblioteca | Versão | Propósito |
|------------|--------|-----------|
| FastAPI | 0.115.5 | Web Framework |
| LangChain | 0.3.9 | LLM Framework |
| LangGraph | 0.2.53 | Agent Workflows |
| SQLAlchemy | 2.0.36 | ORM |
| Pydantic | 2.10.3 | Validation |
| Redis | 5.2.0 | Caching |
| Celery | 5.4.0 | Task Queue |
| HTTPX | 0.28.1 | HTTP Client |
| pgvector | 0.3.6 | Vector Search |
| python-jose | 3.3.0 | JWT |
| msal | 1.31.0 | Microsoft Auth |
| twilio | 9.4.0 | WhatsApp/SMS |
| resend | 2.19.0 | Email |
| sendgrid | 6.11.0 | Email |

---

## APÊNDICES

### Apêndice A: Glossário

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
| **LGPD** | Lei Geral de Proteção de Dados |
| **DPA** | Data Processing Agreement |

### Apêndice B: Free Tiers Disponíveis

| Ferramenta | Free Tier | Limite |
|------------|-----------|--------|
| **ProfitWell** | ✅ Ilimitado | Sempre grátis |
| **Gemini** | ✅ Generoso | Uso leve coberto |
| **LangGraph/LangChain** | ✅ Open source | Sempre grátis |
| **LangSmith** | ✅ Developer | 5.000 traces/mês |
| **Deepgram** | ✅ Créditos | $200 para novos usuários |
| **MS Graph** | ✅ Total | 100% grátis |
| **WhatsApp** | ✅ Conversas | 1.000/mês grátis |
| **SendGrid** | ✅ Emails | 100/dia grátis |
| **Merge** | ✅ Conexões | 3 conexões grátis |
| **Redis (Upstash)** | ✅ Requests | 10k/dia grátis |
| **RabbitMQ (CloudAMQP)** | ✅ Little Lemur | Compartilhado grátis |
| **Figma** | ✅ Starter | 3 projetos grátis |
| **Jira** | ✅ Free | Até 10 usuários |
| **GitHub** | ✅ Free | Repos ilimitados |
| **Notion** | ✅ Free | Times pequenos |
| **HubSpot** | ✅ Free CRM | Recursos básicos |
| **Sentry** | ✅ Developer | 5k errors/mês |

> **Nota:** Com os free tiers disponíveis, é possível rodar o MVP com custo mínimo de ~$30/mês.

### Apêndice C: Contatos Comerciais

| Serviço | Docs | Sales |
|---------|------|-------|
| Anthropic | docs.anthropic.com | sales@anthropic.com |
| LangChain | docs.langchain.com | sales@langchain.com |
| Pearch | docs.pearch.ai | sales@pearch.ai |
| StackOne | docs.stackone.com | contact@stackone.com |
| Merge | docs.merge.dev | sales@merge.dev |
| WorkOS | workos.com/docs | sales@workos.com |
| Deepgram | developers.deepgram.com | sales@deepgram.com |
| Figma | figma.com/developers | sales@figma.com |

### Apêndice D: Secrets Completos

```bash
# LLMs (via Replit Integrations - já configurados)
AI_INTEGRATIONS_ANTHROPIC_API_KEY=xxx
AI_INTEGRATIONS_GEMINI_API_KEY=xxx

# Sourcing
PEARCH_API_KEY=xxx

# Voice
DEEPGRAM_API_KEY=xxx
OPENMIC_API_KEY=xxx

# Comunicação
SENDGRID_API_KEY=SG.xxx
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx

# Microsoft
MICROSOFT_CLIENT_ID=xxx
MICROSOFT_CLIENT_SECRET=xxx
MICROSOFT_TENANT_ID=xxx

# Billing
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Auth (já configurados)
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx
WORKOS_WEBHOOK_SECRET=whsec_xxx

# CRM
HUBSPOT_ACCESS_TOKEN=pat-xxx

# ATS
STACKONE_API_KEY=xxx
```

---

## HISTÓRICO DE VERSÕES

| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | Dez 2024 | Documento inicial de integrações |
| 2.0 | Jan 2026 | Tabela consolidada básica |
| 3.0 | 13 Jan 2026 | Detalhes por categoria |
| 4.0 | 21 Jan 2026 | **Reestruturação completa:** Tabela expandida com 10 colunas, diagramas visuais ASCII do ecossistema, mapa de fluxo de dados, custos por capítulo, guias de configuração, webhooks, métricas, checklists, ordem de implementação, apêndices |

---

## Notas de Implementação

1. **BYOK (Bring Your Own Key):** LLMs podem usar chave do cliente para custo zero WeDoTalent
2. **Feature Flags:** Integrações opcionais controladas via config
3. **Fallback Chain:** Claude → Gemini → OpenAI para resiliência
4. **Multi-tenant:** Todas as integrações respeitam `company_id` para isolamento
5. **Filosofia:** Começar com custo mínimo, escalar conforme receita

---

## Legenda de Status

| Status | Significado |
|--------|-------------|
| ✅ INTEGRADO | Configurado e funcionando em produção |
| 🔶 PLANEJADO | Código implementado, aguardando ativação/configuração |
| ⭕ FUTURO | Em roadmap, ainda não implementado |

---

*Documento consolidado como referência central de todas as integrações WeDo Talent. Manter atualizado a cada nova integração.*
