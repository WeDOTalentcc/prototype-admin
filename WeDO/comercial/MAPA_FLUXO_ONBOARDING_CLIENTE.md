# Autenticação, Onboarding e Multi-Tenancy — Referência Técnica Completa

> **Documento unificado** — fusão de *Mapa de Fluxo de Onboarding de Cliente* (v3.0) e *Análise Profunda de Auth/Onboarding/Multi-Tenancy* (v2.0).  
> Última atualização: **Junho 2026**  
> Fonte de verdade: código em `lia-agent-system/` e `plataforma-lia/`.

---

## 0. Resumo Executivo

### O que JÁ EXISTE (estado real do código)

| Componente | Localização canônica | Status |
|------------|---------------------|--------|
| Login email/senha + SSO Microsoft | `[locale]/login/LoginClient.tsx` | ✅ Completo |
| Forgot/reset password | `[locale]/forgot-password/` + `[locale]/reset-password/` | ✅ Completo |
| JWT + HttpOnly cookies | `auth.py` + `security.py` | ✅ Completo |
| WorkOS SSO + SCIM (8 eventos) | `workos.py` + `api/auth/workos/` | ✅ Completo |
| WorkOS Organization auto-provisionada | `workos_provisioning_service.py` — chamado no `create_client` | ✅ Completo |
| Email de boas-vindas automático | `email_service.send_welcome_email()` — chamado no `create_client` | ✅ Completo |
| Convite de usuário + email automático | `client_users.py` → `send_invite_email()` | ✅ Completo |
| Reenvio de convite | `POST /clients/{id}/users/{uid}/resend-invite` | ✅ Completo |
| Aceitar convite (PT + EN) | `[locale]/aceitar-convite/` + `[locale]/accept-invitation/` | ✅ Completo |
| Verificação de email | `[locale]/verify-email/` + endpoint backend | ✅ Completo |
| Onboarding conversacional pós-login | `[locale]/onboarding/` — chat LIA com 7 seções | ✅ Completo |
| CRUD de clientes (backend) | `/v1/clients` — list, get, create, update, soft-delete | ✅ Completo |
| Dashboard KPIs de clientes (backend) | `/v1/clients/dashboard-summary` — MRR, ARR, churn | ✅ Completo |
| Sync manual HubSpot | GET status, POST sync, PUT onboarding | ✅ Completo |
| Email provider | Mailgun (primary) + Resend (fallback) | ✅ Configurado |
| Multi-tenancy (filtragem por company_id) | `require_company_id` + middleware + RLS | ✅ Completo |
| Portal admin — compliance/governança | `(staff)/wedo-admin/fairness` + `governanca/` | ✅ Parcial |

### O que FALTA (gaps atuais, priorizados)

| Gap | Impacto | Prioridade |
|-----|---------|------------|
| Frontend gestão comercial de clientes (lista, criar, detalhe) | 🔴 Alto — criação de cliente é via API direta | Alta |
| Webhook HubSpot "deal closed" → auto-criar cliente | 🟡 Médio — processo ainda manual | Média |
| Google SSO na tela de login | 🟢 Baixo | Baixa |
| Decisão sobre registro público sem tenant | 🟢 Baixo | Baixa |

---

## 1. Mapa de Maturidade por Fase

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

## 2. Fluxo de Vida do Cliente

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE VIDA DO CLIENTE                        │
│              (✅ = implementado | ⚠️ = parcial | ❌ = falta)        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. COMERCIAL                                                       │
│     └─ HubSpot: Deal fechou                                         │
│         ├─ ✅ Sync manual via API (GET/POST/PUT HubSpot endpoints)  │
│         └─ ❌ Webhook "deal closed" → Auto-cria ClientAccount       │
│                                                                     │
│  2. PROVISIONAMENTO (Admin WeDo)                                    │
│     └─ ✅ POST /v1/clients → ClientAccount criado                   │
│         ├─ ✅ provision_workos_organization() → Organization criada │
│         ├─ ✅ send_welcome_email() → Email automático enviado       │
│         └─ ✅ sync_client_to_hubspot() → Sync opcional              │
│                                                                     │
│  3. CONFIGURAÇÃO SSO (Cliente)                                      │
│     └─ ✅ Admin clica link do email → WorkOS Admin Portal           │
│         └─ ✅ Configura IdP (Okta / Azure AD / Google Workspace)    │
│             └─ ✅ SCIM ativo (opcional) → sync automático de users  │
│                                                                     │
│  4. CONVITE DE USUÁRIOS                                             │
│     └─ ✅ POST /clients/{id}/users → ClientUser (pending)           │
│         └─ ✅ send_invite_email() → Email com token JWT (7 dias)    │
│             └─ ✅ /aceitar-convite ou /accept-invitation            │
│                 └─ ✅ Define senha → status = active                │
│                                                                     │
│  5. PRIMEIRO LOGIN                                                  │
│     └─ ✅ /login → SSO Microsoft ou email/senha                     │
│         └─ ✅ JWT emitido → Animação WelcomeSteps (/login/welcome)  │
│             └─ ✅ [setup incompleto] → redirect para /onboarding    │
│                                                                     │
│  6. SETUP INICIAL (Onboarding Conversacional)                       │
│     └─ ✅ /onboarding → Chat com LIA (OnboardingSettingsChat)       │
│         └─ ✅ 7 seções: profile, culture, tech_stack, benefits,     │
│                          workforce, policy, lia_persona             │
│             └─ ✅ Setup completo → Dashboard operacional            │
│                                                                     │
│  7. OPERAÇÃO                                                        │
│     └─ ✅ Recrutadores criam vagas, usam LIA                        │
│         └─ ✅ Dados isolados por tenant (multi-tenancy completo)    │
│             └─ ✅ Agentes IA usam contexto do tenant               │
│                                                                     │
│  8. GESTÃO (Admin WeDo)                                             │
│     └─ ⚠️  Portal /wedo-admin: fairness + governança (OK)         │
│         ├─ ❌ Dashboard comercial: MRR, ARR, churn                 │
│         ├─ ❌ Lista de clientes + filtros                           │
│         ├─ ❌ Detalhe do cliente com abas                          │
│         ├─ ❌ Setup tracker por cliente                             │
│         └─ ⚠️  Sync HubSpot manual (automático bidirecional: ❌)  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Inventário Técnico Detalhado

> Esta seção cobre cada componente com tabela de status e arquivos canônicos.

### 3.1 Tela de Login (`/login`)

| Item | Status | Observações |
|------|--------|-------------|
| Login email/senha em 2 etapas | ✅ COMPLETO | Email primeiro, depois senha. JWT com bcrypt |
| SSO Microsoft | ✅ COMPLETO | `conn_microsoft_entra` via WorkOS AuthKit |
| SSO Google | ❌ NÃO EXISTE | Apenas Microsoft implementado |
| Esqueci a senha | ✅ COMPLETO | `/forgot-password` + `/reset-password` |
| Redirect pós-login | ✅ COMPLETO | `/login/welcome` com animação WelcomeSteps |
| Lembrar de mim | ⚠️ UI EXISTE | Checkbox presente, sem persistência real |
| Home Realm Discovery | ⚠️ PARCIAL | `/check-sso-domain` existe, auto-redirect não ativo |
| Auto-login dev | ✅ FUNCIONAL | Demo user em desenvolvimento |

**Arquivos:**
- `plataforma-lia/src/app/[locale]/login/LoginClient.tsx`
- `plataforma-lia/src/app/[locale]/forgot-password/`
- `plataforma-lia/src/app/[locale]/reset-password/`
- `plataforma-lia/src/app/[locale]/login/welcome/`

---

### 3.2 Integração WorkOS (SSO + SCIM)

| Item | Status | Observações |
|------|--------|-------------|
| SSO Flow OAuth2 | ✅ COMPLETO | sso → callback → session → refresh |
| Magic Link | ✅ COMPLETO | Rota `magic-link` existe |
| SCIM Webhooks | ✅ COMPLETO | 8 eventos: user created/updated/deleted, group sync |
| Session Management | ✅ COMPLETO | Cookie `workos_session`, crypto com `jose` |
| Provisioning auto de Organization | ✅ COMPLETO | Chamado em `create_client` |
| JIT Provisioning | ✅ COMPLETO | Se user não existe no SSO callback, cria automaticamente |
| Circuit Breaker | ✅ COMPLETO | Proteção contra falhas do WorkOS |
| SSO Audit Log | ✅ COMPLETO | Tabela dedicada para compliance |
| Group → Role Mapping | ✅ COMPLETO | Mapeamento SCIM groups para roles da app |
| Notificação quando SSO ativado | ❌ NÃO EXISTE | Webhook WorkOS ou polling não implementado |

**Arquivos:**
- `lia-agent-system/app/api/v1/workos.py`
- `lia-agent-system/app/auth/workos_models.py`
- `lia-agent-system/app/domains/auth/repositories/workos_repository.py`
- `lia-agent-system/app/domains/company/services/workos_provisioning_service.py`
- `plataforma-lia/src/app/api/auth/workos/` — sso, callback, session, refresh, magic-link, ws-token
- `plataforma-lia/src/app/api/webhooks/workos/route.ts`
- `plataforma-lia/src/lib/session-crypto.ts`

---

### 3.3 Sistema de Autenticação JWT

| Item | Status | Observações |
|------|--------|-------------|
| Login endpoint | ✅ COMPLETO | `POST /auth/login` com bcrypt |
| Token generation | ✅ COMPLETO | access_token (30 min), refresh_token (7 dias) |
| HttpOnly cookies | ✅ COMPLETO | `lia_access_token`, `lia_refresh_token`, `lia_auth_method` |
| Middleware de auth | ✅ COMPLETO | Extrai token de cookies, injeta em Authorization header |
| Token refresh | ✅ COMPLETO | `POST /api/auth/session/refresh` |
| Logout | ✅ COMPLETO | Limpa cookies, stores, redireciona |
| Frontend auth context | ✅ COMPLETO | Zustand store + React context |
| Protected routes | ✅ COMPLETO | Middleware Next.js redireciona para `/login` |

**Arquivos:**
- `lia-agent-system/app/api/v1/auth.py` — login, register, public-register, verify-email
- `lia-agent-system/app/auth/security.py` — JWT utils
- `plataforma-lia/src/stores/auth-store.ts`
- `plataforma-lia/src/contexts/auth-context.tsx`
- `plataforma-lia/src/services/auth-service.ts`
- `plataforma-lia/src/middleware.ts`

---

### 3.4 Registro Público (`/register`)

| Item | Status | Observações |
|------|--------|-------------|
| Tela de registro | ✅ EXISTE | Nome, email, senha, termos |
| Endpoint `POST /auth/public-register` | ✅ EXISTE | Cria user com `is_active=False`, role `viewer` |
| Verificação de email end-to-end | ✅ COMPLETO | Ver 3.10 — `VerifyEmailClient.tsx` + endpoint |
| Associação a tenant | ❌ INCOMPLETO | User criado sem `company_id` definido |
| Onboarding pós-registro | ❌ NÃO EXISTE | Após confirmar email, sem fluxo de associação a empresa |

> **Decisão pendente:** manter, remover ou converter para freemium (ver seção 9).

**Arquivos:**
- `plataforma-lia/src/app/[locale]/register/RegisterClient.tsx`
- `lia-agent-system/app/api/v1/auth.py` (endpoint `public-register`, linha ~334)

---

### 3.5 Convites de Usuários

| Item | Status | Observações |
|------|--------|-------------|
| Envio de convite + email | ✅ COMPLETO | `POST /clients/{id}/users` cria user + chama `send_invite_email()` |
| Template de convite | ✅ COMPLETO | Via `email_service` |
| Tela aceitar convite (PT) | ✅ COMPLETO | `/aceitar-convite?token=...` |
| Tela aceitar convite (EN) | ✅ COMPLETO | `/accept-invitation?token=...` com setup de senha |
| Expiração do token | ✅ COMPLETO | JWT de 7 dias validado no backend |
| Reenvio de convite | ✅ COMPLETO | `POST /{user_id}/resend-invite` |

**Arquivos:**
- `lia-agent-system/app/api/v1/client_users.py`
- `plataforma-lia/src/app/[locale]/aceitar-convite/AceitarConviteClient.tsx`
- `plataforma-lia/src/app/[locale]/accept-invitation/AcceptInvitationClient.tsx`

---

### 3.6 Gestão de Clientes — Backend

| Item | Status | Observações |
|------|--------|-------------|
| CRUD de clientes | ✅ COMPLETO | List, get, create, update, soft-delete |
| Dashboard KPIs | ✅ COMPLETO | `/v1/clients/dashboard-summary` — MRR, ARR, churn |
| Setup progress (5 seções) | ✅ COMPLETO | company-profile, benefits, culture, departments, documents |
| Sync manual HubSpot | ✅ COMPLETO | GET status, POST sync, PUT onboarding status |
| Webhook HubSpot "deal closed" | ❌ NÃO EXISTE | Auto-criação de cliente não implementada |
| Automações por cliente | ✅ COMPLETO | Workflows por evento |
| Integrações externas | ✅ COMPLETO | Gupy, LinkedIn, Greenhouse, Slack, WhatsApp |
| Templates de sistema | ✅ COMPLETO | CRUD + publish para todos os tenants |
| RBAC / Roles | ✅ COMPLETO | Roles customizados, matrix de permissões |
| Segurança (admin) | ✅ COMPLETO | 2FA, session timeout, password policy, IP whitelist |
| Audit logs | ✅ COMPLETO | Filtro por resource, user, ação |

**Endpoints:**
```
GET/POST       /v1/clients                          — CRUD
GET            /v1/clients/dashboard-summary        — KPIs
GET/PATCH      /v1/clients/{id}/setup               — Setup progress
GET            /v1/clients/{id}/hubspot/status       — Status sync HubSpot
POST           /v1/clients/{id}/hubspot/sync         — Sync manual
PUT            /v1/clients/{id}/hubspot/onboarding   — Atualiza status no HubSpot
GET/POST       /v1/clients/{id}/automations          — Workflows
GET/POST       /v1/clients/{id}/integrations         — Conexões externas
GET/POST       /v1/clients/{id}/users                — User management
GET/POST/PUT   /v1/admin/templates                   — System templates
GET/POST/PUT   /v1/admin/roles                       — RBAC
```

**Arquivos:**
- `lia-agent-system/app/api/v1/clients/clients_crud.py` — CRUD + auto-provisioning + welcome email
- `lia-agent-system/app/api/v1/clients/clients_dashboard.py`
- `lia-agent-system/app/api/v1/clients/clients_setup.py`
- `lia-agent-system/app/api/v1/clients/clients_hubspot.py`
- `lia-agent-system/app/api/v1/clients/clients_automations.py`
- `lia-agent-system/app/api/v1/clients/clients_integrations.py`
- `lia-agent-system/app/shared/services/hubspot_service.py`
- `lia-agent-system/app/api/v1/admin_settings.py`
- `lia-agent-system/app/api/v1/admin_templates.py`
- `lia-agent-system/app/api/v1/client_users.py`

---

### 3.7 Multi-Tenancy

| Item | Status | Observações |
|------|--------|-------------|
| Filtragem por company_id | ✅ COMPLETO | Todas as queries filtram via `require_company_id` |
| RLS no PostgreSQL | ✅ COMPLETO | Row-Level Security ativo |
| Isolamento testado | ✅ COMPLETO | Testes de segurança cross-tenant |
| Backend proxy (Next.js) | ✅ COMPLETO | Injeta auth headers automaticamente |
| Cross-tenant admin access | ✅ COMPLETO | Com audit log `[AUDIT:CROSS-TENANT]` |
| DomainContext para agentes IA | ✅ COMPLETO | `tenant_id` propagado para LLM tools |

**Arquivos:**
- `lia-agent-system/app/auth/dependencies.py`
- `lia-agent-system/app/core/tenant.py`
- `lia-agent-system/app/shared/security/require_company_id.py`
- `plataforma-lia/src/lib/api/proxy-handler.ts`

---

### 3.8 Portal Admin WeDo — `(staff)/wedo-admin`

| Item | Status | Observações |
|------|--------|-------------|
| Layout staff com sidebar própria | ✅ COMPLETO | `StaffLayoutClient.tsx` com route group `(staff)` |
| Rota home `/wedo-admin` | ✅ EXISTE | `wedo-admin/page.tsx` |
| Fairness / Bias Audit | ✅ COMPLETO | `fairness/page.tsx` + `fairness/bias-audit/page.tsx` |
| Governança / Audit Logs | ✅ COMPLETO | `governanca/audit-logs/page.tsx` |
| Governança / AI Transparency | ✅ COMPLETO | `governanca/ai-transparency/page.tsx` |
| Governança / Policy Engine | ✅ COMPLETO | `governanca/policy-engine/page.tsx` |
| Governança / Automation Rules | ✅ COMPLETO | `governanca/automation-rules/page.tsx` |
| Governança / AI Performance | ✅ COMPLETO | `governanca/ai-performance/page.tsx` |
| Dashboard comercial (MRR, ARR, churn) | ❌ NÃO EXISTE | Backend tem endpoints, frontend não foi construído |
| Lista de clientes | ❌ NÃO EXISTE | Backend tem CRUD, frontend não existe |
| Detalhe do cliente (abas) | ❌ NÃO EXISTE | — |
| Gestão de usuários por cliente | ❌ NÃO EXISTE | — |
| Setup tracker por cliente | ❌ NÃO EXISTE | — |

> O portal admin foi construído com foco em **compliance e governança de IA**. A gestão comercial de clientes (dashboard MRR/ARR, lista, setup tracker) não existe no frontend — apenas no backend.

**Arquivos:**
- `plataforma-lia/src/app/[locale]/(staff)/StaffLayoutClient.tsx`
- `plataforma-lia/src/app/[locale]/(staff)/wedo-admin/`

---

### 3.9 Onboarding Conversacional (`/onboarding`)

| Item | Status | Observações |
|------|--------|-------------|
| Rota `/onboarding` | ✅ COMPLETO | `[locale]/onboarding/page.tsx` — criada 2026-05-24 |
| Chat conversacional | ✅ COMPLETO | `OnboardingSettingsChat` |
| Endpoint dedicado backend | ✅ COMPLETO | `POST /onboarding/{userId}/chat` |
| Section → actionId mapping | ✅ COMPLETO | 7 seções mapeadas |
| Detecção de setup incompleto | ✅ EXISTE | Redirect para `/onboarding` automático |

**7 seções do onboarding:**

| Seção | Action ID |
|-------|-----------|
| profile | configure_profile |
| culture | configure_culture |
| tech_stack | configure_tech_stack |
| benefits | configure_benefits |
| workforce | configure_workforce |
| policy | configure_hiring_policy |
| lia_persona | configure_persona |

> **Histórico:** redirect para `/onboarding` existia desde 2026-04-20 mas a rota não existia — usuários novos caíam em 404 por 35 dias. Gap fechado em 2026-05-24 (Sprint 2 FE-3).

**Arquivos:**
- `plataforma-lia/src/app/[locale]/onboarding/page.tsx`
- `lia-agent-system/app/api/v1/onboarding.py`
- `plataforma-lia/src/components/onboarding/onboarding-controller.tsx`
- `plataforma-lia/src/stores/onboarding-store.ts`

---

### 3.10 Verificação de Email

| Item | Status | Observações |
|------|--------|-------------|
| Endpoint `POST /auth/verify-email` | ✅ COMPLETO | Em `auth.py` |
| Frontend `VerifyEmailClient.tsx` | ✅ COMPLETO | `[locale]/verify-email/VerifyEmailClient.tsx` |
| Chamada ao backend | ✅ COMPLETO | `/api/backend-proxy/auth/verify-email` |
| Redirect pós-verificação | ✅ EXISTE | Implementado no client |

**Arquivos:**
- `plataforma-lia/src/app/[locale]/verify-email/VerifyEmailClient.tsx`
- `lia-agent-system/app/api/v1/auth.py`

---

### 3.11 Seletor de Portal (`/access`)

| Item | Status | Observações |
|------|--------|-------------|
| Tela de seleção | ✅ EXISTE | Cards "WedoTalent" e "Admin" |
| Portal do Cliente | ✅ FUNCIONA | Redireciona para plataforma de recrutamento |
| Portal Admin | ⚠️ PARCIAL | Redireciona para `(staff)/wedo-admin` — compliance ok, gestão de clientes não |

---

## 4. Detalhamento por Fase

### FASE 1: COMERCIAL (HubSpot) — 40%

```
HubSpot CRM
    ↓
Lead → Demo → Proposta → Contrato (Deal Closed Won)
    ↓
[MANUAL] Time WeDo cria cliente via API /v1/clients
```

**O que JÁ EXISTE:**
- ✅ HubSpot como CRM (pipeline de vendas configurado)
- ✅ `GET /clients/{id}/hubspot/status` — status de sync
- ✅ `POST /clients/{id}/hubspot/sync` — sync manual WeDo → HubSpot
- ✅ `PUT /clients/{id}/hubspot/onboarding` — atualiza status no HubSpot

**O que FALTA:**

| Gap | Descrição |
|-----|-----------|
| 🟡 Webhook HubSpot "deal closed" | Receber evento e criar cliente automaticamente |
| 🟡 Sync automático bidirecional | Hoje o sync é manual (POST endpoint) |

**Solução proposta (pendente):**
```
HubSpot (Deal Closed Won)
    ↓ [Webhook — endpoint /webhooks/hubspot não existe ainda]
POST /v1/clients  →  [já automatizado após criação:]
    ├── ✅ provision_workos_organization()
    ├── ✅ send_welcome_email()
    └── ⬜ atualizar HubSpot com link de acesso
```

---

### FASE 2: PROVISIONAMENTO (WeDo Admin) — 95%

```
POST /v1/clients  →  ClientAccount criado no banco
    ↓ [automático]
├── provision_workos_organization()
│   └── organization_id salvo em CompanyWorkOSConfig ✅
├── send_welcome_email() ✅
└── sync_client_to_hubspot() — opcional, falha silenciosa ✅
```

**O que JÁ EXISTE:**
- ✅ Backend `/clients POST` — CRUD completo
- ✅ `provision_workos_organization()` — chamado automaticamente, salva `workos_organization_id`
- ✅ `send_welcome_email()` — chamado automaticamente via `email_service`
- ✅ `workos_organization_created` tracking no modelo `ClientAccount`

**O que FALTA:**

| Gap | Descrição |
|-----|-----------|
| 🔴 Frontend de gestão de clientes | Criar cliente hoje exige chamada direta à API |

---

### FASE 3: CONFIGURAÇÃO SSO (WorkOS) — 80%

```
Cliente recebe email → Acessa WorkOS Admin Portal (embedado)
    ↓
Configura IdP (Okta / Azure AD / Google Workspace)
    ↓
Testa conexão SSO
    ↓ [opcional]
Ativa SCIM Directory Sync
```

**O que JÁ EXISTE:**
- ✅ WorkOS Admin Portal embedado com links tenant-specific
- ✅ Documentação SSO em português
- ✅ SCIM Webhooks (8 eventos processados)
- ✅ Group-to-Role mapping
- ✅ JIT provisioning — cria usuário automaticamente no callback SSO

**O que FALTA:**

| Gap | Descrição |
|-----|-----------|
| 🟡 Notificação quando SSO ativado | Webhook WorkOS ou polling |
| 🟢 Vídeo tutorial | Gravação da configuração |

---

### FASE 4: CONVITES — 95%

```
POST /clients/{id}/users  →  ClientUser (status=pending)
    ↓ [automático]
send_invite_email()  →  Email com token JWT (7 dias)
    ↓
Usuário clica link:
    ├── /aceitar-convite?token=...   (PT)
    └── /accept-invitation?token=... (EN)
    ↓
Define senha → status = active → pode fazer login
```

**Status: ✅ COMPLETO**

---

### FASE 5: PRIMEIRO LOGIN — 95%

```
/login
    ├── [SSO] "Continuar com Microsoft"
    │       └── WorkOS AuthKit → IdP → Callback → JWT
    └── [Email/senha] Fluxo de 2 etapas
    ↓
JWT emitido → Animação WelcomeSteps (/login/welcome)
    ↓
[Se setup incompleto] Redirect → /onboarding
```

**O que JÁ EXISTE:**
- ✅ SSO Microsoft (único SSO disponível)
- ✅ Email/senha com JWT + bcrypt
- ✅ MFA via AuthKit
- ✅ Animação WelcomeSteps (6 slides)
- ✅ Redirect automático para `/onboarding` se setup incompleto

**O que FALTA:**

| Gap | Descrição |
|-----|-----------|
| 🟢 Google SSO | Botão "Continuar com Google" não existe |
| 🟢 Auto-redirect por domínio | Home Realm Discovery não é automático |

---

### FASE 6: SETUP INICIAL (Onboarding Conversacional) — 95%

```
/onboarding → Chat com LIA (OnboardingSettingsChat)
    ↓
POST /onboarding/{userId}/chat (7 seções):
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

**Status: ✅ COMPLETO**

> Abordagem foi implementada como **chat conversacional com LIA** — não o wizard de 5 steps originalmente planejado. Mais rico e alinhado com o princípio "chat é a interface principal".

---

## 5. O Que Falta — Lacunas Atuais Priorizadas

### 5.1 FRONTEND GESTÃO COMERCIAL DE CLIENTES — Prioridade ALTA

**Situação:** Backend 100% funcional. Layout do portal admin existe (`(staff)/wedo-admin`). Falta construir as páginas de gestão comercial dentro desse portal.

**O que construir:**
1. Dashboard admin comercial — MRR, ARR, churn, distribuição por plano/status
2. Lista de clientes com filtros — status, plano, indústria, tamanho
3. Detalhe do cliente com abas — dados, setup progress, usuários, integrações, automações
4. Formulário de criação de cliente
5. Gestão de usuários por cliente — convidar, listar, desativar, alterar role
6. Setup tracker visual por cliente (quais das 5 seções cada cliente completou)

### 5.2 WEBHOOK HUBSPOT "DEAL CLOSED" — Prioridade MÉDIA

**Situação:** Sync manual funciona. Falta o webhook para automação completa.

**O que construir:**
1. Endpoint `POST /webhooks/hubspot` com validação de assinatura HMAC
2. Handler que auto-cria `ClientAccount` ao receber "deal closed"
3. Atualização do HubSpot com link de acesso do novo cliente

### 5.3 GOOGLE SSO — Prioridade BAIXA

**O que construir:**
1. Botão "Continuar com Google" em `LoginClient.tsx` (`conn_google_workspace`)
2. Configuração de connection Google no WorkOS dashboard

### 5.4 REGISTRO PÚBLICO SEM TENANT — Prioridade BAIXA

**Situação:** `public-register` cria user com `company_id=None`. Usuário fica "órfão".

**Opções:**
- **Opção A (recomendada se não há freemium):** Remover — todos os usuários entram via convite
- **Opção B:** Self-service freemium — registro cria empresa + tenant automaticamente
- **Opção C:** Registro cria user pendente, admin WeDo associa manualmente

---

## 6. Plano de Implementação — Status dos Sprints

### ~~Sprint 1: Integração HubSpot~~ — ⚠️ PARCIALMENTE FEITO

| Tarefa | Status |
|--------|--------|
| ~~Sync WeDo → HubSpot (manual)~~ | ✅ Feito |
| Webhook HubSpot "deal closed" → auto-criar cliente | ❌ Pendente |
| Sync automático bidirecional | ❌ Pendente (hoje é manual) |

### ~~Sprint 2: Automação WorkOS~~ — ✅ CONCLUÍDO

| Tarefa | Status |
|--------|--------|
| ~~Criar Organization automaticamente ao criar cliente~~ | ✅ `provision_workos_organization()` |
| ~~Salvar organization_id em CompanyWorkOSConfig~~ | ✅ Feito |
| ~~Email de boas-vindas automático~~ | ✅ `send_welcome_email()` |

### ~~Sprint 3: Sistema de Convites~~ — ✅ CONCLUÍDO

| Tarefa | Status |
|--------|--------|
| ~~Enviar email de convite~~ | ✅ `send_invite_email()` |
| ~~Página /aceitar-convite~~ | ✅ Existe (PT + EN) |
| ~~Expiração de convite (7 dias)~~ | ✅ JWT com expiração |
| ~~Reenviar convite~~ | ✅ Endpoint de resend |

### Sprint 4: Frontend Gestão de Clientes — ❌ PENDENTE

| Tarefa | Status |
|--------|--------|
| Lista de clientes com filtros | ❌ |
| Formulário de criação de cliente | ❌ |
| Detalhe do cliente com abas | ❌ |
| Setup tracker visual por cliente | ❌ |
| Gestão de usuários por cliente | ❌ |

> Backend 100% pronto (`/v1/clients` CRUD, setup, users). Falta apenas o frontend.

### Sprint 5: HubSpot Webhook — ❌ PENDENTE (desejável)

| Tarefa | Status |
|--------|--------|
| `POST /webhooks/hubspot` com validação HMAC | ❌ |
| Handler auto-criação de cliente | ❌ |
| Sync bidirecional automático | ❌ |

---

## 7. Arquitetura de Integrações

```
┌─────────────────────────────────────────────────────────────────────┐
│                           HubSpot CRM                               │
│              (Leads, Deals, Pipeline Comercial)                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ sync manual ✅ / webhook automático ❌
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                 │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │ ClientAccount  │  │ CompanyWorkOS  │  │     ClientUser      │  │
│  │  CRUD ✅       │  │  Config        │  │  convite + email ✅ │  │
│  └───────┬────────┘  │  org_id ✅     │  └──────────┬──────────┘  │
│          │           └────────────────┘             │             │
│          │ ao criar cliente (automático):            │ ao convidar:│
│          ▼                                          ▼             │
│  ┌──────────────────────┐          ┌──────────────────────────┐  │
│  │  workos_provisioning │          │      Email Service        │  │
│  │  create_organization │          │  Mailgun (primary)        │  │
│  │  save org_id ✅      │          │  Resend (fallback)        │  │
│  └──────────┬───────────┘          │  send_welcome ✅          │  │
│             │                      │  send_invite ✅           │  │
│             ▼                      └──────────────────────────┘  │
│  ┌─────────────────────────────────────────────┐                 │
│  │               WorkOS                         │                 │
│  │  SSO (sso→callback→session→refresh) ✅       │                 │
│  │  SCIM Webhooks (8 eventos) ✅                │                 │
│  │  Group → Role Mapping ✅                     │                 │
│  │  JIT Provisioning ✅                         │                 │
│  └──────────┬──────────────────────────────────┘                 │
│             │ SSO callback / SCIM events                          │
│             ▼                                                      │
│  ┌──────────────────────────────────────────────┐                │
│  │            Auth System                        │                │
│  │  JWT tokens + WorkOS sessions ✅              │                │
│  │  HttpOnly cookies ✅                          │                │
│  │  company_id em todas as queries ✅            │                │
│  │  RLS no PostgreSQL ✅                         │                │
│  └──────────────────────────────────────────────┘                │
│                                                                     │
│  ┌──────────────────────────────────────────────┐                │
│  │            Onboarding API ✅                  │                │
│  │  POST /onboarding/{userId}/chat               │                │
│  │  7 sections: profile, culture, benefits…      │                │
│  └──────────────────────────────────────────────┘                │
│                                                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ proxy com auth headers
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Next.js Frontend  (src/app/[locale]/)                │
│                                                                     │
│  Auth/Onboarding:                                                   │
│  ✅ /login           ✅ /register        ✅ /verify-email           │
│  ✅ /forgot-password ✅ /reset-password  ✅ /login/welcome          │
│  ✅ /aceitar-convite ✅ /accept-invitation                          │
│  ✅ /onboarding (chat conversacional LIA — 7 seções)               │
│  ✅ /access (seletor de portal)                                     │
│                                                                     │
│  Portal Admin  (staff)/wedo-admin/:                                 │
│  ✅ fairness/ + bias-audit/                                         │
│  ✅ governanca/ (audit-logs, ai-transparency, policy-engine…)       │
│  ❌ clientes/ (lista, criar, detalhe, setup tracker)               │
│                                                                     │
│  Plataforma de Recrutamento  (dashboard)/:                          │
│  ✅ vagas, candidatos, pipeline, LIA chat                          │
│  ✅ tudo filtrado por company_id (multi-tenancy)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Métricas de Sucesso

| Métrica | Jan 2026 | Jun 2026 | Meta Final |
|---------|----------|----------|------------|
| Etapas manuais para criar cliente | 6+ | 2 (API + HubSpot manual) | 1 (só HubSpot) |
| WorkOS Organization automática | ❌ Manual | ✅ Automático | ✅ |
| Email de boas-vindas automático | ❌ Manual | ✅ Automático | ✅ |
| Email de convite automático | ❌ Manual | ✅ Automático | ✅ |
| Onboarding guiado pós-login | ❌ Não existia | ✅ Chat conversacional | ✅ |
| Frontend gestão de clientes | ❌ | ❌ | 🎯 Sprint 4 |
| Webhook HubSpot deal closed | ❌ | ❌ | 🎯 Sprint 5 |
| Google SSO | ❌ | ❌ | 🎯 Futura |

---

## 9. Decisões Pendentes

| Decisão | Opções | Recomendação |
|---------|--------|--------------|
| Registro público: manter? | A) Remover — todos via convite B) Freemium — cria empresa automaticamente C) Pendente manual | A) se não há plano freemium |
| Google SSO: priorizar? | Sim / Depois | Sim — Google Workspace é comum em PMEs |
| Admin portal: gestão comercial onde? | Nova sub-rota em `wedo-admin/clientes/` | Mesma estrutura `(staff)`, sub-páginas novas |
| HubSpot webhook: automático? | Full-auto / Semi-auto com aprovação admin | Semi-auto para o MVP |
| Setup wizard: obrigatório? | Bloquear acesso / Lembrete suave | Lembrete persistente + bloquear criação de vaga sem perfil |

---

## 10. Variáveis de Ambiente

```bash
# WorkOS (já configurado)
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx

# Email — Mailgun (primary) + Resend (fallback)
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=xxx
RESEND_API_KEY=re_xxx

# HubSpot — sync manual existe; webhook ainda não implementado
HUBSPOT_API_KEY=pat-xxx
HUBSPOT_WEBHOOK_SECRET=xxx   # para quando o webhook for implementado
```

---

## 11. Índice de Arquivos por Área

### Auth / Login
| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/app/[locale]/login/LoginClient.tsx` | Tela login (email/senha + SSO Microsoft) |
| `plataforma-lia/src/app/[locale]/forgot-password/` | Esqueci a senha |
| `plataforma-lia/src/app/[locale]/reset-password/` | Reset de senha |
| `plataforma-lia/src/app/[locale]/login/welcome/` | Animação pós-login (WelcomeSteps) |
| `plataforma-lia/src/stores/auth-store.ts` | Zustand store de auth |
| `plataforma-lia/src/contexts/auth-context.tsx` | React context de auth |
| `plataforma-lia/src/services/auth-service.ts` | Auth service frontend |
| `plataforma-lia/src/middleware.ts` | Middleware Next.js (protected routes) |
| `lia-agent-system/app/api/v1/auth.py` | Endpoints: login, register, public-register, verify-email |
| `lia-agent-system/app/auth/security.py` | JWT utils |

### WorkOS
| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/api/v1/workos.py` | API principal WorkOS |
| `lia-agent-system/app/auth/workos_models.py` | Modelos (Config, Groups, Audit) |
| `lia-agent-system/app/domains/auth/repositories/workos_repository.py` | Repository WorkOS |
| `lia-agent-system/app/domains/company/services/workos_provisioning_service.py` | Auto-provisioning de Organization |
| `plataforma-lia/src/app/api/auth/workos/` | Rotas: sso, callback, session, refresh, magic-link, ws-token |
| `plataforma-lia/src/app/api/webhooks/workos/route.ts` | Webhook receiver SCIM |
| `plataforma-lia/src/lib/session-crypto.ts` | Crypto de sessão |

### Gestão de Clientes (Backend)
| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/api/v1/clients/clients_crud.py` | CRUD + auto-provisioning + welcome email |
| `lia-agent-system/app/api/v1/clients/clients_dashboard.py` | KPIs: MRR, ARR, churn |
| `lia-agent-system/app/api/v1/clients/clients_setup.py` | Progress de setup (5 seções) |
| `lia-agent-system/app/api/v1/clients/clients_hubspot.py` | Sync manual HubSpot |
| `lia-agent-system/app/api/v1/clients/clients_automations.py` | Workflows por evento |
| `lia-agent-system/app/api/v1/clients/clients_integrations.py` | Conexões externas |
| `lia-agent-system/app/shared/services/hubspot_service.py` | HubSpot service |
| `lia-agent-system/app/api/v1/client_users.py` | Users: convite, resend, ativar |
| `lia-agent-system/app/api/v1/admin_settings.py` | Configurações admin |
| `lia-agent-system/app/api/v1/admin_templates.py` | Templates de sistema |

### Registro, Convites e Verificação de Email
| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/app/[locale]/register/RegisterClient.tsx` | Registro público |
| `plataforma-lia/src/app/[locale]/aceitar-convite/AceitarConviteClient.tsx` | Aceitar convite (PT) |
| `plataforma-lia/src/app/[locale]/accept-invitation/AcceptInvitationClient.tsx` | Aceitar convite (EN) |
| `plataforma-lia/src/app/[locale]/verify-email/VerifyEmailClient.tsx` | Verificação de email |

### Portal Admin Frontend
| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/app/[locale]/(staff)/StaffLayoutClient.tsx` | Layout staff com sidebar |
| `plataforma-lia/src/app/[locale]/(staff)/wedo-admin/page.tsx` | Home do portal admin |
| `plataforma-lia/src/app/[locale]/(staff)/wedo-admin/fairness/` | Fairness + Bias Audit |
| `plataforma-lia/src/app/[locale]/(staff)/wedo-admin/governanca/` | Governança (audit-logs, ai-transparency, policy-engine, automation-rules, ai-performance) |

### Onboarding Conversacional
| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/app/[locale]/onboarding/page.tsx` | Rota /onboarding |
| `lia-agent-system/app/api/v1/onboarding.py` | Backend: 7 seções, section→actionId mapping |
| `plataforma-lia/src/components/onboarding/onboarding-controller.tsx` | Controller do onboarding |
| `plataforma-lia/src/stores/onboarding-store.ts` | Store de estado |

### Multi-Tenancy
| Arquivo | Responsabilidade |
|---------|-----------------|
| `lia-agent-system/app/auth/dependencies.py` | `get_current_user` + tenant injection |
| `lia-agent-system/app/core/tenant.py` | TenantContext |
| `lia-agent-system/app/shared/security/require_company_id.py` | Dependency de company_id |
| `plataforma-lia/src/lib/api/proxy-handler.ts` | Proxy Next.js com auth headers |

### Documentação Relacionada
- `docs/architecture/tenant-context-history.md` — histórico completo do tenant context e bugs T-A → T-F
- `docs/runbooks/missing_tenant_context.md` — runbook on-call tenant
- `docs/specs/process/ONBOARDING.md` — guia de entrada para devs
- `plataforma-lia/docs/comercial/onboarding-roteiro.md` — roteiro comercial

---

## Histórico

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | Jan 2026 | Análise inicial do fluxo de onboarding |
| 2.0 | Jan 2026 | Correção: identificado sistema existente, plano atualizado com HubSpot |
| 3.0 | Jun 2026 | Revisão completa com base no código: WorkOS auto-provisioning ✅, emails automáticos ✅, convites ✅, onboarding conversacional ✅ |
| 4.0 | Jun 2026 | Fusão com *Análise de Auth/Onboarding/Multi-Tenancy*: inventário técnico detalhado por componente, índice de arquivos, JWT, multi-tenancy, decisões pendentes |
