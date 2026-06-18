# Mapa Completo: Fluxo de Onboarding de Cliente WeDo Talent

> **Documento de Análise e Plano de Melhorias**  
> Última atualização: **Junho 2026** (v3.0 — revisão completa com base no código atual)

---

## Resumo Executivo

### O que JÁ EXISTE (Funcional) — Estado Real do Código

| Componente | Localização | Status |
|------------|-------------|--------|
| CRUD de clientes (backend) | `POST/GET/PUT /v1/clients` | ✅ Completo |
| WorkOS Organization auto-provisionada | `workos_provisioning_service.py` — chamado no `create_client` | ✅ Implementado |
| Email de boas-vindas automático | `email_service.send_welcome_email()` — chamado no `create_client` | ✅ Implementado |
| Email de convite ao convidar usuário | `email_service.send_invite_email()` — chamado em `client_users.py` | ✅ Implementado |
| Reenvio de convite | `POST /clients/{id}/users/{uid}/resend-invite` | ✅ Completo |
| Páginas de aceite de convite | `/aceitar-convite` (PT) e `/accept-invitation` (EN) | ✅ Completo |
| Verificação de email | `/verify-email` + endpoint backend | ✅ Completo |
| WorkOS SSO | Fluxo completo (sso, callback, session, refresh, magic-link) | ✅ Completo |
| SCIM Webhooks | 8 eventos processados | ✅ Completo |
| Onboarding conversacional pós-login | `/onboarding` — chat LIA com 7 seções | ✅ Implementado (novo) |
| Sync manual HubSpot | GET status, POST sync, PUT onboarding status | ✅ Completo |
| Email provider | Mailgun (primary) + Resend (fallback) | ✅ Configurado |
| Portal admin (compliance) | `(staff)/wedo-admin` — fairness + governança | ✅ Parcial |

### O que FALTA (Gaps Atuais)

| Gap | Impacto | Prioridade |
|-----|---------|------------|
| Lista/gestão de clientes no frontend | Alto — criação de cliente é via API direta | 🔴 Alta |
| Webhook HubSpot "deal closed" → auto-criar cliente | Médio — processo ainda manual | 🟡 Média |
| Dashboard de status de onboarding consolidado | Baixo | 🟢 Baixa |
| Botão Google SSO na tela de login | Baixo | 🟢 Baixa |

> **Nota v3.0:** O documento v2.0 (Jan 2026) listava como "existente" um frontend admin com lista de clientes em `/admin/clientes`. Isso **não existe** no código atual — o portal `(staff)/wedo-admin` foi construído com foco em compliance/fairness/governança de IA, **não** em gestão comercial de clientes.

---

## Visão Geral das 6 Fases

```
┌─────────────────────────────────────────────────────────────┐
│                    MAPA DE MATURIDADE                       │
│                   (atualizado Jun 2026)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FASE 1: COMERCIAL (HubSpot)     [████░░░░░░] 40%          │
│  FASE 2: PROVISIONAMENTO (WeDo)  [█████████░] 95%          │
│  FASE 3: CONFIG SSO (WorkOS)     [████████░░] 80%          │
│  FASE 4: CONVITES                [█████████░] 95%          │
│  FASE 5: PRIMEIRO LOGIN          [█████████░] 95%          │
│  FASE 6: SETUP INICIAL           [█████████░] 95%          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## FASE 1: COMERCIAL (HubSpot)

### Fluxo Atual

```
HubSpot CRM
    ↓
Lead qualificado → Demo → Proposta → Contrato
    ↓
[MANUAL] Time WeDo cria cliente via API /v1/clients
    ↓
[MANUAL] Admin WeDo acessa portal (quando frontend de clientes existir)
```

### O que JÁ EXISTE

- ✅ HubSpot como CRM comercial
- ✅ Pipeline de vendas configurado
- ✅ `GET /clients/{id}/hubspot/status` — status de sync
- ✅ `POST /clients/{id}/hubspot/sync` — sync manual WeDo → HubSpot
- ✅ `PUT /clients/{id}/hubspot/onboarding` — atualiza status de onboarding no HubSpot

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🟡 **Webhook HubSpot "deal closed"** | Receber evento e criar cliente automaticamente |
| 🟡 **Sync automático bidirecional** | Hoje o sync é manual (POST endpoint) |

### Solução Proposta (ainda pendente)

```
HubSpot (Deal Closed Won)
    ↓ [Webhook — endpoint /webhooks/hubspot não existe ainda]
WeDo Backend
    ↓ [Já automatizado ao criar cliente:]
├── ✅ Criar ClientAccount
├── ✅ Criar Organization no WorkOS
├── ✅ Enviar email de boas-vindas
└── ⬜ Atualizar HubSpot com link de acesso (via PUT /hubspot/onboarding)
```

---

## FASE 2: PROVISIONAMENTO (WeDo Admin)

### Fluxo Atual

```
[API ou futuro frontend admin]
    ↓
POST /v1/clients  →  ClientAccount criado no banco
    ↓ [automático — implementado]
├── provision_workos_organization() → Organization criada no WorkOS
│   └── organization_id salvo em CompanyWorkOSConfig
├── send_welcome_email() → Email automático enviado para o admin
└── hubspot_result = sync_client_to_hubspot() → Sync opcional
```

### O que JÁ EXISTE

- ✅ **Backend `/clients` POST** — CRUD funcional, retorna dados completos
- ✅ **`provision_workos_organization()`** — chamado automaticamente no `create_client`, salva `workos_organization_id` em `CompanyWorkOSConfig`
- ✅ **`send_welcome_email()`** — chamado automaticamente no `create_client` via `email_service`
- ✅ **`workos_organization_created` tracking** — campo no modelo `ClientAccount` rastreia se org foi criada
- ✅ **Sync HubSpot** — tentado automaticamente no create; falha silenciosa (não bloqueia criação)

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🔴 **Frontend de gestão de clientes** | Criar cliente hoje exige chamada direta à API — não há tela |

---

## FASE 3: CONFIGURAÇÃO SSO (WorkOS)

### Fluxo Atual

```
Cliente recebe email com link Admin Portal (WorkOS)
    ↓
Acessa WorkOS Admin Portal (embedado ou via link)
    ↓
Configura IdP (Okta/Azure AD/Google)
    ↓
Testa conexão SSO
    ↓
[Opcional] Ativa SCIM Directory Sync
```

### O que JÁ EXISTE

- ✅ **WorkOS Admin Portal** — modal funcional com links tenant-specific
- ✅ **Documentação SSO** — guia completo em português
- ✅ **SCIM Webhooks** — 8 eventos processados
- ✅ **Group-to-Role mapping** — funcional
- ✅ **JIT provisioning** — se usuário faz SSO e não existe, cria automaticamente

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🟡 **Notificação quando SSO ativado** | Webhook do WorkOS ou polling para atualizar status |
| 🟢 **Vídeo tutorial** | Gravação mostrando configuração |

---

## FASE 4: CONVITES

### Fluxo Atual

```
Admin (via API ou futuro frontend)
    ↓
POST /clients/{id}/users  →  ClientUser criado (status=pending)
    ↓ [automático — implementado]
send_invite_email()  →  Email enviado com link + token JWT (7 dias)
    ↓
Usuário clica link → /aceitar-convite?token=... (PT)
                  ou /accept-invitation?token=... (EN)
    ↓
Define senha → status = active → pode fazer login
```

### O que JÁ EXISTE

- ✅ **`POST /clients/{id}/users`** — cria ClientUser + envia email automaticamente
- ✅ **`email_service.send_invite_email()`** — chamado no create user
- ✅ **`POST /{user_id}/resend-invite`** — reenvio funcional
- ✅ **`/aceitar-convite`** — página PT com validação de token
- ✅ **`/accept-invitation`** — página EN com setup de senha
- ✅ **Expiração de token** — JWT de 7 dias validado no backend

### Status: ✅ COMPLETO

> **v3.0:** O documento anterior classificava toda esta fase como "NÃO IMPLEMENTADO". Na realidade, está completamente funcional — email de convite, link de aceite e ativação de conta funcionam.

---

## FASE 5: PRIMEIRO LOGIN

### Fluxo Atual

```
Usuário acessa plataforma → /login
    ↓
├── [SSO] Clica "Continuar com Microsoft"
│       └── WorkOS AuthKit → IdP → Callback → JWT
└── [Email/senha] Fluxo de 2 etapas (email, depois senha)
    ↓
Backend sync-user → JWT → Animação WelcomeSteps (/login/welcome)
    ↓
[Se setup incompleto] Redirect para /onboarding
```

### O que JÁ EXISTE

- ✅ **Fluxo SSO Microsoft** — completo (único SSO disponível atualmente)
- ✅ **Fluxo email/senha** — funcional com JWT, bcrypt
- ✅ **sync-user endpoint** — cria/atualiza usuário
- ✅ **Animação WelcomeSteps** — 6 slides em `/login/welcome`
- ✅ **MFA via AuthKit** — suportado
- ✅ **Redirect para onboarding** — detecta setup incompleto

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🟢 **Google SSO** | Botão "Continuar com Google" não existe na tela de login |
| 🟢 **Detecção de domínio** | Auto-redirect para SSO correto por email (Home Realm Discovery existe mas não é automático) |

---

## FASE 6: SETUP INICIAL — ONBOARDING CONVERSACIONAL

### Fluxo Atual

```
Usuário completa animação WelcomeSteps
    ↓
[Se setup incompleto] Redirect para /onboarding
    ↓
Chat com LIA — OnboardingSettingsChat
    ↓
7 seções via POST /onboarding/{userId}/chat:
├── profile      → configure_profile
├── culture      → configure_culture
├── tech_stack   → configure_tech_stack
├── benefits     → configure_benefits
├── workforce    → configure_workforce
├── policy       → configure_hiring_policy
└── lia_persona  → configure_persona
    ↓
Setup completo → Dashboard operacional
```

### O que JÁ EXISTE

- ✅ **`/onboarding`** — rota existe (criada 2026-05-24, Sprint 2 FE-3)
- ✅ **Chat conversacional** — `OnboardingSettingsChat` com endpoint dedicado
- ✅ **`POST /onboarding/{userId}/chat`** — backend com 7 seções mapeadas
- ✅ **Análise de cultura por IA** — funcional
- ✅ **Benefícios sugeridos** — automático via LIA

### Mudança de Abordagem

> **v3.0:** O documento anterior descrevia um "wizard de 3 passos" (configurar empresa, criar primeira vaga, ativar recrutamento). Na prática, o onboarding foi implementado como **chat conversacional com LIA** cobrindo 7 seções. A abordagem é mais rica e alinhada com o princípio "chat é a interface principal".

### Status: ✅ COMPLETO

---

## PLANO DE IMPLEMENTAÇÃO — Status Atual

### ~~Sprint 1: Integração HubSpot~~ — ⚠️ PARCIALMENTE FEITO

| Tarefa | Status |
|--------|--------|
| ~~Sync WeDo → HubSpot (manual)~~ | ✅ Feito — endpoints POST/GET/PUT existem |
| Webhook HubSpot "deal closed" → auto-criar cliente | ❌ Ainda falta |
| Sync automático bidirecional | ❌ Hoje é manual via POST endpoint |

### ~~Sprint 2: Automação WorkOS~~ — ✅ CONCLUÍDO

| Tarefa | Status |
|--------|--------|
| ~~Criar Organization automaticamente ao criar cliente~~ | ✅ `provision_workos_organization()` chamado no create |
| ~~Salvar organization_id em CompanyWorkOSConfig~~ | ✅ Feito |
| ~~Email de boas-vindas automático~~ | ✅ `send_welcome_email()` chamado no create |

### ~~Sprint 3: Sistema de Convites~~ — ✅ CONCLUÍDO

| Tarefa | Status |
|--------|--------|
| ~~Enviar email de convite ao convidar usuário~~ | ✅ `send_invite_email()` chamado no create user |
| ~~Template de convite~~ | ✅ Implementado via email_service |
| ~~Página /aceitar-convite~~ | ✅ Existe (PT + EN) |
| ~~Expiração de convite (7 dias)~~ | ✅ JWT com expiração validado |
| ~~Reenviar convite~~ | ✅ Endpoint de resend funcional |

### Sprint 4: Frontend Gestão de Clientes — ❌ PENDENTE (Renomeado)

> O sprint original chamava de "Dashboard de Onboarding". O que realmente falta é a **interface frontend para gestão comercial de clientes**.

| Tarefa | Status |
|--------|--------|
| Lista de clientes com filtros (status, plano, indústria) | ❌ Falta |
| Formulário de criação de cliente | ❌ Falta |
| Detalhe do cliente com abas (dados, setup, usuários, integrações) | ❌ Falta |
| Setup tracker visual por cliente | ❌ Falta |
| Gestão de usuários por cliente no frontend | ❌ Falta |

> **Nota:** O backend para tudo isso está 100% funcional (`/v1/clients` CRUD + setup + users). Falta apenas o frontend.

---

## Variáveis de Ambiente Necessárias

```bash
# HubSpot (para webhook automático — ainda não implementado)
HUBSPOT_API_KEY=pat-xxx
HUBSPOT_WEBHOOK_SECRET=xxx

# WorkOS (já configurado)
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx

# Email — Mailgun (primary) + Resend (fallback)
# Nota: o documento anterior mencionava Resend/SendGrid — está desatualizado.
# Provider atual: Mailgun primary, Resend como fallback
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=xxx
RESEND_API_KEY=re_xxx
```

---

## Arquitetura de Integrações — Estado Atual

```
┌─────────────────────────────────────────────────────────────┐
│                      HubSpot CRM                            │
│  (Comercial: Leads, Deals, Pipeline)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ sync manual ✅ / webhook automático ❌
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   WeDo Talent Backend                        │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ ClientAccount│  │ CompanyWorkOS    │  │ ClientUser   │  │
│  │  (Dados)    │  │  Config          │  │  (Convites)  │  │
│  └──────┬──────┘  │  org_id ✅       │  │  email ✅    │  │
│         │         └──────────────────┘  └──────┬───────┘  │
│         │ auto ao criar:                         │ ao convidar:
│         ▼                                        ▼          │
│  ┌──────────────────────┐        ┌──────────────────────┐  │
│  │ workos_provisioning  │        │   Email Service       │  │
│  │  create_organization │        │   Mailgun (primary)   │  │
│  │  save org_id ✅      │        │   Resend (fallback)   │  │
│  └──────────────────────┘        │   send_welcome ✅     │  │
│                                  │   send_invite ✅      │  │
│                                  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ proxy com auth headers
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Next.js Frontend (src/app/[locale]/)            │
│                                                             │
│  ✅ /login (email/senha + SSO Microsoft)                    │
│  ✅ /register                                               │
│  ✅ /verify-email                                           │
│  ✅ /aceitar-convite  /accept-invitation                    │
│  ✅ /login/welcome (animação WelcomeSteps)                  │
│  ✅ /onboarding (chat conversacional LIA — 7 seções)        │
│                                                             │
│  (staff)/wedo-admin:                                        │
│  ✅ fairness + bias-audit                                   │
│  ✅ governança (audit-logs, ai-transparency, etc.)          │
│  ❌ gestão comercial de clientes (lista, detalhe, criar)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Métricas de Sucesso — Estado Atual

| Métrica | Jan 2026 | Jun 2026 | Meta Final |
|---------|----------|----------|------------|
| Etapas manuais para criar cliente | 6+ | 2 (criar via API + HubSpot manual) | 1 (criar no HubSpot) |
| WorkOS Organization automática | ❌ Manual | ✅ Automático | ✅ |
| Email de boas-vindas automático | ❌ Manual | ✅ Automático | ✅ |
| Email de convite automático | ❌ Manual | ✅ Automático | ✅ |
| Onboarding guiado pós-login | ❌ Não existia | ✅ Chat conversacional | ✅ |
| Frontend gestão de clientes | ❌ | ❌ | 🎯 Próximo sprint |
| Webhook HubSpot deal closed | ❌ | ❌ | 🎯 Desejável |

---

## Arquivos de Referência

### Backend
- `lia-agent-system/app/api/v1/clients/clients_crud.py` — CRUD + provisioning + welcome email no create
- `lia-agent-system/app/api/v1/clients/clients_setup.py` — Progress de setup (5 seções)
- `lia-agent-system/app/api/v1/clients/clients_hubspot.py` — Sync manual HubSpot
- `lia-agent-system/app/api/v1/client_users.py` — Convites + send_invite_email
- `lia-agent-system/app/api/v1/onboarding.py` — Chat onboarding (7 seções)
- `lia-agent-system/app/domains/company/services/workos_provisioning_service.py` — Auto-provisioning WorkOS
- `lia-agent-system/app/domains/communication/services/email_service.py` — Email service (Mailgun + Resend)
- `lia-agent-system/app/shared/services/hubspot_service.py` — HubSpot service

### Frontend
- `plataforma-lia/src/app/[locale]/login/LoginClient.tsx` — Login
- `plataforma-lia/src/app/[locale]/login/welcome/` — Animação pós-login
- `plataforma-lia/src/app/[locale]/onboarding/page.tsx` — Chat onboarding
- `plataforma-lia/src/app/[locale]/aceitar-convite/AceitarConviteClient.tsx`
- `plataforma-lia/src/app/[locale]/accept-invitation/AcceptInvitationClient.tsx`
- `plataforma-lia/src/app/[locale]/verify-email/VerifyEmailClient.tsx`
- `plataforma-lia/src/app/[locale]/(staff)/wedo-admin/` — Portal admin (fairness + governança)
- `plataforma-lia/src/app/[locale]/(staff)/StaffLayoutClient.tsx` — Layout staff

---

## Histórico

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | Jan 2026 | Análise inicial |
| 2.0 | Jan 2026 | Correção: identificado sistema existente, plano atualizado com HubSpot |
| 3.0 | Jun 2026 | Revisão completa com base no código atual: WorkOS auto-provisioning ✅, emails automáticos ✅, convites ✅, onboarding conversacional ✅. Corrigido equívoco: frontend de gestão de clientes nunca foi construído. |
