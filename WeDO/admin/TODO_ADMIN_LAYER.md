# 📋 WeDo Talent - Admin Layer To-Do List

> **Última atualização:** Janeiro 2026  
> **Status:** Em andamento

---

## 📊 Visão Geral - Status Completo

### Contas e Setup Externo

| # | Ferramenta | Tarefa | Status |
|---|------------|--------|--------|
| 1 | HubSpot | Criar conta | ✅ Concluído |
| 2 | HubSpot | Configurar CRM (Companies, Contacts, Deals) | ✅ Concluído |
| 3 | HubSpot | Criar Workflow de Onboarding (3 workflows + pipeline) | ⏳ Pendente |
| 4 | WorkOS | Criar conta | ✅ Concluído |
| 5 | WorkOS | Configurar Organizations e conexões SSO/SCIM | ⏳ Pendente |
| 6 | ProfitWell | Criar conta | ✅ Concluído |
| 7 | ProfitWell | Integrar com HubSpot | ✅ Concluído |
| 8 | Stripe | Criar conta | ✅ Concluído |
| 9 | Stripe | Configurar produtos, preços e Customer Portal | ⏳ Pendente |
| 10 | Stripe | Configurar webhooks | ⏳ Pendente |
| 11 | Mailgun | Criar conta | ✅ Concluído |
| 12 | Mailgun | Configurar domínio e templates | ⏳ Pendente |
| 13 | Merge | Criar conta | ✅ Concluído |
| 14 | Merge | Configurar integrações ATS (Gupy, Pandapé) | ⏳ Pendente |
| 15 | Azure AD | Registrar app Microsoft Graph (Teams/Calendar) | ✅ Concluído |

> **Nota sobre SSO:** A WeDo usa **WorkOS** como middleware SSO. A WeDo **não precisa** criar apps SAML no Azure AD, Okta ou outros IdPs. Quando um cliente solicita SSO, o time WeDo cria uma Organization no WorkOS e fornece as URLs (ACS, Entity ID) para o **cliente** configurar no IdP **dele**.

### Desenvolvimento Backend (Rails + PostgreSQL)

| # | Service/Módulo | Descrição | Status |
|---|----------------|-----------|--------|
| 16 | Setup Projeto | Rails 7.x + PostgreSQL + estrutura base | ⏳ Pendente |
| 17 | WorkosProvisioningService | SSO/SCIM, callbacks, Organizations | ⏳ Pendente |
| 18 | StripeSyncService | Webhooks Stripe → sync HubSpot | ⏳ Pendente |
| 19 | HubspotService | API CRM (Companies, Contacts, Deals) | ⏳ Pendente |
| 20 | HubspotOnboardingService | API Tickets (onboarding pipeline) | ⏳ Pendente |
| 21 | EmailService | Mailgun (emails transacionais) | ⏳ Pendente |
| 22 | MergeService | ATS/HRIS sync (vagas, candidatos) | ⏳ Pendente |
| 23 | MicrosoftGraphService | Teams meetings, Outlook calendar | ⏳ Pendente |

### Fase 2 - Compliance (Após MVP)

| # | Ferramenta | Tarefa | Status |
|---|------------|--------|--------|
| 24 | Vanta ou Drata | Setup SOC 2 Type II, ISO 27001 | 🔜 Fase 2 |
| 25 | Privacy Tools | Setup LGPD, portal do titular | 🔜 Fase 2 |
| 26 | Warden AI | Auditoria de bias nos algoritmos LIA | 🔜 Fase 2 |

---

### Resumo Rápido

| Categoria | Total | ✅ Concluído | ⏳ Pendente | 🔜 Fase 2 |
|-----------|-------|-------------|-------------|-----------|
| Contas/Setup Externo | 15 | 9 | 6 | 0 |
| Backend Rails | 8 | 0 | 8 | 0 |
| Compliance | 3 | 0 | 0 | 3 |
| **TOTAL** | **26** | **9** | **14** | **3** |

---

## ✅ Já Concluído (Detalhes)

| Item | Ferramenta | Status |
|------|------------|--------|
| Conta criada | HubSpot | ✅ Pronto |
| CRM configurado | HubSpot | ✅ Pronto |
| Conta criada | WorkOS | ✅ Pronto |
| Conta criada | ProfitWell | ✅ Pronto |
| Integração ProfitWell ↔ HubSpot | ProfitWell | ✅ Pronto |
| Conta criada | Stripe | ✅ Pronto |
| Conta criada | Mailgun | ✅ Pronto |
| Conta criada | Merge | ✅ Pronto |
| App registrado | Microsoft Graph (Azure) | ✅ Pronto |

---

## 🔴 Fase 1 - Prioridade Alta

### 1. HubSpot: Workflow de Onboarding

**Objetivo:** Automatizar o onboarding de novos clientes via HubSpot Tickets + Workflows

**Passos:**
1. **Criar Pipeline de Tickets "Onboarding Cliente"** com 7 stages:
   - `1-boas-vindas` - Ticket criado automaticamente
   - `2-dados-empresa` - Coleta de informações
   - `3-config-sso` - Configuração SSO (se enterprise)
   - `4-import-dados` - Importação de dados existentes
   - `5-treinamento` - Agendamento de treinamento
   - `6-go-live` - Ativação da conta
   - `7-onboarding-completo` - Finalizado

2. **Criar 3 Workflows automatizados:**
   
   **Workflow 1: Boas-vindas**
   - Trigger: Novo deal fechado (Pipeline Vendas → Closed Won)
   - Ações:
     - Criar ticket no pipeline "Onboarding Cliente"
     - Enviar email de boas-vindas ao cliente
     - Notificar CS interno via Slack/email
   
   **Workflow 2: Progresso de Stages**
   - Trigger: Ticket muda de stage
   - Ações:
     - Enviar email específico do stage ao cliente
     - Atualizar propriedade `onboarding_progress` no Contact
     - Se stage = `6-go-live`: criar task para CS fazer check-in
   
   **Workflow 3: Onboarding Completo**
   - Trigger: Ticket chega em `7-onboarding-completo`
   - Ações:
     - Enviar email de parabéns + recursos úteis
     - Atualizar propriedade `lifecycle_stage` para "Customer"
     - Agendar NPS survey para 30 dias

3. **Criar Templates de Email:**
   - `onboarding-welcome` - Boas-vindas inicial
   - `onboarding-stage-update` - Atualização de progresso
   - `onboarding-complete` - Conclusão do onboarding
   - `onboarding-sso-instructions` - Instruções SSO (se aplicável)

---

### 2. Stripe: Configurar Billing Completo

**Objetivo:** Billing automatizado com Customer Portal para autoatendimento

**Passos:**

**4.1 Criar Produtos e Preços:**
1. Acessar [Stripe Dashboard](https://dashboard.stripe.com) → Products
2. Criar produtos:

| Produto | Preço Mensal | Preço Anual | Recursos |
|---------|--------------|-------------|----------|
| **Starter** | R$ 499 | R$ 4.990 | 3 vagas, 2 usuários |
| **Professional** | R$ 999 | R$ 9.990 | 10 vagas, 5 usuários, SSO |
| **Enterprise** | Custom | Custom | Ilimitado, SCIM, SLA |

**4.2 Configurar Customer Portal:**
1. Ir em **Settings** → **Billing** → **Customer portal**
2. Habilitar:
   - ✅ Update payment methods
   - ✅ View invoice history
   - ✅ Cancel subscriptions
   - ✅ Switch plans (upgrade/downgrade)
3. Customizar branding (logo, cores WeDo)

**4.3 Configurar Webhooks:**
1. Ir em **Developers** → **Webhooks**
2. Adicionar endpoint: `https://api.wedotalent.com/api/v1/webhooks/stripe`
3. Selecionar eventos:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.created`
   - `customer.updated`
4. Copiar **Webhook Signing Secret** → salvar como `STRIPE_WEBHOOK_SECRET`

**4.4 Obter API Keys:**
- `STRIPE_SECRET_KEY` - Developers → API Keys → Secret key
- `STRIPE_PUBLISHABLE_KEY` - Developers → API Keys → Publishable key

---

### 3. WorkOS: Configurar Dashboard

**Objetivo:** Preparar WorkOS para gerenciar SSO/SCIM de clientes enterprise

**Passos:**

**5.1 Configuração Inicial:**
1. Acessar [WorkOS Dashboard](https://dashboard.workos.com)
2. Ir em **Configuration** → **Redirects**
3. Adicionar redirect URIs:
   - `https://app.wedotalent.com/auth/callback`
   - `https://api.wedotalent.com/api/v1/auth/workos/callback`

**5.2 Obter Credenciais:**
- `WORKOS_API_KEY` - API Keys
- `WORKOS_CLIENT_ID` - Configuration → Client ID

**5.3 Criar Organization Template:**
1. Ir em **Organizations** → Entender estrutura
2. Cada cliente enterprise terá:
   - 1 Organization no WorkOS
   - Conexão SSO configurada
   - (Opcional) Directory Sync para SCIM

**5.4 Documentar Processo para CS:**
Quando cliente solicitar SSO:
1. Criar Organization no WorkOS
2. Gerar SSO Connection link
3. Enviar instruções ao cliente via HubSpot
4. Cliente configura no IdP dele (Azure AD, Okta, etc)
5. Testar e ativar

---

## 🟢 Fase 1 - Desenvolvimento Backend

### 4. Backend Rails: Setup Inicial

**Objetivo:** Criar projeto Rails com PostgreSQL e estrutura base

**Passos:**
```bash
# Criar projeto
rails new wedotalent-backend --api --database=postgresql

# Estrutura de pastas
app/
├── controllers/
│   └── api/
│       └── v1/
│           ├── webhooks_controller.rb
│           ├── auth_controller.rb
│           └── billing_controller.rb
├── services/
│   ├── workos_provisioning_service.rb
│   ├── stripe_sync_service.rb
│   ├── hubspot_service.rb
│   ├── hubspot_onboarding_service.rb
│   ├── email_service.rb
│   ├── merge_service.rb
│   └── microsoft_graph_service.rb
└── models/
    ├── company.rb
    ├── user.rb
    └── subscription.rb
```

**Gems essenciais:**
```ruby
# Gemfile
gem 'workos'
gem 'stripe'
gem 'hubspot-api-client'
gem 'mailgun-ruby'
gem 'httparty' # Para Merge e MS Graph
gem 'jwt'
gem 'rack-cors'
```

---

### 5. Backend: WorkosProvisioningService

**Objetivo:** Gerenciar SSO/SCIM via WorkOS API

**Funcionalidades:**
```ruby
class WorkosProvisioningService
  # Criar organization para novo cliente enterprise
  def create_organization(company)
  
  # Gerar link de configuração SSO
  def generate_sso_setup_link(organization_id)
  
  # Processar callback de autenticação SSO
  def handle_sso_callback(code)
  
  # Sincronizar usuários via SCIM (Directory Sync)
  def sync_directory_users(directory_id)
  
  # Desativar usuário quando removido do IdP
  def deactivate_user(user_id)
end
```

**Endpoints:**
- `POST /api/v1/auth/sso/authorize` - Iniciar fluxo SSO
- `GET /api/v1/auth/workos/callback` - Callback do WorkOS
- `POST /api/v1/webhooks/workos` - Webhooks Directory Sync

---

### 6. Backend: StripeSyncService

**Objetivo:** Sincronizar dados Stripe → HubSpot (substitui Commerce Hub indisponível no Brasil)

**Funcionalidades:**
```ruby
class StripeSyncService
  # Processar webhook de subscription criada
  def handle_subscription_created(event)
    # 1. Atualizar company no banco local
    # 2. Sincronizar com HubSpot (deal, company properties)
  
  # Processar pagamento bem-sucedido
  def handle_invoice_paid(event)
    # 1. Registrar pagamento
    # 2. Atualizar MRR no HubSpot
  
  # Processar falha de pagamento
  def handle_payment_failed(event)
    # 1. Criar task no HubSpot para CS
    # 2. Enviar alerta interno
  
  # Processar cancelamento
  def handle_subscription_deleted(event)
    # 1. Atualizar status da company
    # 2. Atualizar HubSpot
    # 3. Notificar CS
end
```

**Endpoint:**
- `POST /api/v1/webhooks/stripe` - Recebe todos os webhooks Stripe

---

### 7. Backend: HubspotService + HubspotOnboardingService

**Objetivo:** Integração completa com HubSpot CRM e Tickets

**HubspotService:**
```ruby
class HubspotService
  # CRUD de Companies
  def create_company(data)
  def update_company(hubspot_id, data)
  def find_company_by_domain(domain)
  
  # CRUD de Contacts
  def create_contact(data)
  def update_contact(hubspot_id, data)
  
  # CRUD de Deals
  def create_deal(data)
  def update_deal_stage(deal_id, stage)
  
  # Propriedades customizadas
  def update_mrr(company_id, mrr_value)
  def update_subscription_status(company_id, status)
end
```

**HubspotOnboardingService:**
```ruby
class HubspotOnboardingService
  # Criar ticket de onboarding
  def create_onboarding_ticket(company_id, contact_id)
  
  # Atualizar stage do ticket
  def update_ticket_stage(ticket_id, stage)
  
  # Buscar tickets por empresa
  def get_company_tickets(company_id)
  
  # Marcar onboarding como completo
  def complete_onboarding(ticket_id)
end
```

**Endpoints:**
- `POST /api/v1/webhooks/hubspot` - Webhooks do HubSpot
- `GET /api/v1/companies/:id/onboarding` - Status do onboarding

---

### 8. Backend: EmailService (Mailgun)

**Objetivo:** Envio de emails transacionais

**Funcionalidades:**
```ruby
class EmailService
  # Enviar email transacional
  def send_email(to:, template:, variables:)
  
  # Templates disponíveis:
  # - welcome
  # - password_reset
  # - onboarding_update
  # - invoice_paid
  # - payment_failed
  # - sso_instructions
  
  # Enviar email em batch
  def send_batch(recipients, template, variables)
end
```

**Configuração Mailgun:**
- `MAILGUN_API_KEY`
- `MAILGUN_DOMAIN` (ex: mg.wedotalent.com)

---

### 9. Backend: MergeService (ATS/HRIS)

**Objetivo:** Sincronizar vagas e candidatos com ATS dos clientes (Gupy, Pandapé, etc)

**Funcionalidades:**
```ruby
class MergeService
  # Conectar conta do cliente
  def create_link_token(company_id, integration_type)
  
  # Sincronizar vagas
  def sync_jobs(company_id)
  
  # Sincronizar candidatos
  def sync_candidates(company_id)
  
  # Criar candidato no ATS do cliente
  def push_candidate(company_id, candidate_data)
  
  # Atualizar status de candidato
  def update_candidate_stage(company_id, candidate_id, stage)
end
```

**Configuração:**
- `MERGE_API_KEY`
- `MERGE_ACCOUNT_TOKEN` (por cliente)

---

### 10. Backend: MicrosoftGraphService

**Objetivo:** Agendamento de entrevistas via Teams e Outlook

**Funcionalidades:**
```ruby
class MicrosoftGraphService
  # Autenticação OAuth
  def get_access_token(company_id)
  
  # Criar reunião no Teams
  def create_teams_meeting(organizer_email:, subject:, start_time:, end_time:, attendees:)
  
  # Criar evento no Outlook Calendar
  def create_calendar_event(user_email:, event_data:)
  
  # Verificar disponibilidade
  def get_free_busy(user_email:, start_time:, end_time:)
  
  # Cancelar reunião
  def cancel_meeting(meeting_id)
end
```

**Configuração (já registrado no Azure):**
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `MICROSOFT_TENANT_ID`

---

## ⚪ Fase 2 - Compliance (Após MVP)

### 11. Vanta/Drata: Setup Compliance

**Objetivo:** SOC 2 Type II, ISO 27001

**Passos:**
1. Escolher entre Vanta ou Drata
2. Integrar com infraestrutura (AWS/Replit)
3. Conectar repositórios GitHub
4. Mapear controles
5. Iniciar auditoria

---

### 12. Privacy Tools: Setup LGPD

**Objetivo:** Conformidade LGPD para clientes brasileiros

**Passos:**
1. Criar conta Privacy Tools
2. Configurar portal do titular de dados
3. Implementar RIPD (Relatório de Impacto)
4. Configurar consent management
5. Integrar com backend (APIs de exclusão de dados)

---

### 13. Warden AI: Auditoria de Bias

**Objetivo:** Auditar algoritmos da LIA para viés discriminatório

**Passos:**
1. Contatar Warden AI
2. Definir escopo da auditoria
3. Fornecer acesso aos modelos de screening
4. Implementar recomendações
5. Obter certificação

---

## 📊 Resumo de Secrets/API Keys Necessárias

| Secret | Serviço | Status |
|--------|---------|--------|
| `STRIPE_SECRET_KEY` | Stripe | ⏳ Obter |
| `STRIPE_PUBLISHABLE_KEY` | Stripe | ⏳ Obter |
| `STRIPE_WEBHOOK_SECRET` | Stripe | ⏳ Configurar |
| `WORKOS_API_KEY` | WorkOS | ⏳ Obter |
| `WORKOS_CLIENT_ID` | WorkOS | ⏳ Obter |
| `HUBSPOT_ACCESS_TOKEN` | HubSpot | ⏳ Obter (Private App) |
| `MAILGUN_API_KEY` | Mailgun | ⏳ Obter |
| `MAILGUN_DOMAIN` | Mailgun | ⏳ Configurar |
| `MERGE_API_KEY` | Merge | ⏳ Obter |
| `MICROSOFT_CLIENT_ID` | Azure/Graph | ✅ Já tem |
| `MICROSOFT_CLIENT_SECRET` | Azure/Graph | ⏳ Obter |
| `MICROSOFT_TENANT_ID` | Azure/Graph | ✅ Já tem |

---

## 📅 Sugestão de Cronograma

| Semana | Foco | Tarefas |
|--------|------|---------|
| **1** | Setup Externo | HubSpot Workflow, Stripe config, WorkOS config |
| **2** | Setup Externo | Mailgun domínio, Merge integrações ATS |
| **3** | Backend Core | Rails setup, WorkOS + Stripe services |
| **4** | Backend Core | HubSpot + Email services |
| **5** | Backend Integrações | Merge + Microsoft Graph services |
| **6** | Testes | Integração end-to-end, ajustes |

---

*Documento gerado automaticamente. Atualizar conforme progresso.*
