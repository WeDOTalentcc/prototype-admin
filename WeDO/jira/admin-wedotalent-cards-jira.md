# CARDS JIRA - WEDO TALENT ADMIN (INTEGRAÇÕES SaaS)

> **Total de Cards:** 56 cards  
> **Organização:** Por Responsável (GESTOR vs DEVS) e por Ferramenta/Sprint  
> **Data:** 14 Janeiro 2026  
> **Baseado em:** Apêndice I - Separação de Tarefas (WEDOTALENT_INTEGRACOES_COMPLETO.md)  
> **Estimativa Total:** 2-3 dias (Gestor) + 4-5 semanas (Devs)

---

## RESUMO EXECUTIVO

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              VISÃO GERAL DOS CARDS                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   👔 GESTOR (Configuração SaaS)              👨‍💻 DEVS (Desenvolvimento Rails)            │
│   ─────────────────────────────              ────────────────────────────────            │
│   34 cards | 2-3 dias                        22 cards | 4-5 semanas                      │
│                                                                                          │
│   ├── STRIPE: 7 cards                        ├── SEMANA 1 - Fundação: 5 cards            │
│   ├── HUBSPOT: 10 cards                      ├── SEMANA 2 - Auth WorkOS: 5 cards         │
│   ├── WORKOS: 7 cards                        ├── SEMANA 3 - Billing Stripe: 5 cards      │
│   ├── PROFITWELL: 4 cards                    ├── SEMANA 4 - CRM/Onboarding: 3 cards      │
│   └── PRIVACY TOOLS: 6 cards                 └── SEMANA 5 - Compliance: 4 cards          │
│                                                                                          │
│   DEPENDÊNCIA: Gestor finaliza → Handoff → Devs começam                                  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ÍNDICE DE CARDS

### PARTE 1: CARDS GESTOR - Configuração SaaS (34 cards)

| Prefixo | Ferramenta | Quantidade | Tempo Estimado |
|---------|------------|------------|----------------|
| GST-STR | Stripe | 7 cards | 2 horas |
| GST-HUB | HubSpot | 10 cards | 4 horas |
| GST-WOS | WorkOS | 7 cards | 2 horas |
| GST-PWL | ProfitWell | 4 cards | 1 hora |
| GST-PVT | Privacy Tools | 6 cards | 2 horas |

### PARTE 2: CARDS DEVS - Desenvolvimento Rails (22 cards)

| Prefixo | Sprint/Semana | Quantidade | Foco |
|---------|---------------|------------|------|
| DEV-S1 | Semana 1 - Fundação | 5 cards | Rails + PostgreSQL + Multi-tenant |
| DEV-S2 | Semana 2 - Auth | 5 cards | WorkOS SSO/SCIM |
| DEV-S3 | Semana 3 - Billing | 5 cards | Stripe Integration |
| DEV-S4 | Semana 4 - CRM | 3 cards | HubSpot Workflows |
| DEV-S5 | Semana 5 - Compliance | 4 cards | Privacy Tools + Audit |

---

# PARTE 1: CARDS GESTOR - CONFIGURAÇÃO SaaS

> **Responsável:** Gestor de Produto / Founder  
> **Requisito:** Sem conhecimento técnico necessário  
> **Prazo Total:** 2-3 dias úteis  
> **Resultado:** Handoff Document para time de Devs

---

## STRIPE - Configuração de Billing (7 cards)

---

### CARD GST-STR-001: Criar Conta Stripe

```yaml
Titulo: [GESTOR] Criar e Verificar Conta Stripe
Tipo: Configuração SaaS
Tempo: 30 minutos (criação) + 1-2 dias (verificação)
Prioridade: Crítica
Ferramenta: Stripe
Sequência: 1 de 7

Descrição: |
  Criar conta no Stripe para processar pagamentos do WeDo Talent.
  A verificação pode levar 1-2 dias dependendo da documentação.

Objetivo: |
  Ter uma conta Stripe ativa e verificada para processar pagamentos
  em Reais (BRL) com métodos brasileiros (Boleto, PIX, Cartão).

Passo a Passo:
  1. Acessar https://dashboard.stripe.com/register
  2. Criar conta com email corporativo (ex: billing@wedotalent.com)
  3. Verificar email
  4. Acessar Dashboard → Settings → Business Settings
  5. Preencher dados da empresa:
     - Razão Social
     - CNPJ
     - Endereço comercial
     - Representante legal
  6. Enviar documentos solicitados:
     - Contrato social
     - Documento do representante
     - Comprovante de endereço
  7. Aguardar aprovação (1-2 dias úteis)

Entregáveis para Devs:
  - Account ID (ex: acct_xxx)
  - Confirmação de conta verificada
  - País configurado: Brasil
  - Moeda padrão: BRL

Critérios de Aceitação:
  - [ ] Conta criada com email corporativo
  - [ ] Documentos enviados para verificação
  - [ ] Status "Verified" no dashboard
  - [ ] Métodos de pagamento BR habilitados
```

---

### CARD GST-STR-002: Criar Produtos e Preços

```yaml
Titulo: [GESTOR] Configurar Produtos e Planos no Stripe
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Crítica
Ferramenta: Stripe
Sequência: 2 de 7
Dependências: GST-STR-001

Descrição: |
  Criar os produtos e preços que representam os planos
  do WeDo Talent no Stripe Billing.

Objetivo: |
  Ter todos os produtos e preços configurados para que
  o checkout funcione automaticamente.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 2, Passo 2.2

Passo a Passo:
  1. Acessar Dashboard → Products
  2. Clicar "Add Product"

╔══════════════════════════════════════════════════════════════════════════════╗
║                      TABELA DE PRODUTOS STRIPE (4)                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Produto        │ Preço Mensal  │ Preço Anual  │ Tipo      │ Stripe Price ID  ║
╠════════════════╪═══════════════╪══════════════╪═══════════╪══════════════════╣
║ WeDo Starter   │ R$ 990/mês    │ R$ 9.900/ano │ Recurring │ price_xxx        ║
╠════════════════╪═══════════════╪══════════════╪═══════════╪══════════════════╣
║ WeDo Profess.  │ R$ 2.490/mês  │ R$ 24.900/ano│ Recurring │ price_xxx        ║
╠════════════════╪═══════════════╪══════════════╪═══════════╪══════════════════╣
║ WeDo Enterprise│ Customizado   │ Quote-based  │ Custom    │ -                ║
╠════════════════╪═══════════════╪══════════════╪═══════════╪══════════════════╣
║ Setup Fee      │ R$ 5.000      │ -            │ One-time  │ price_xxx        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Detalhes de Cada Produto:
  
  PRODUTO 1 - WeDo Starter:
    Name: WeDo Talent Starter
    Description: Plano inicial para pequenas empresas
    Pricing:
      - Preço Mensal: R$ 990,00 (Recurring, Monthly)
      - Preço Anual: R$ 9.900,00 (Recurring, Yearly) - 2 meses grátis
    Metadata:
      - plan_tier: starter
      - max_jobs: 10
      - max_users: 5
    Tax behavior: Exclusive (impostos não inclusos)
  
  PRODUTO 2 - WeDo Professional:
    Name: WeDo Talent Professional
    Description: Plano profissional para empresas médias
    Pricing:
      - Preço Mensal: R$ 2.490,00 (Recurring, Monthly)
      - Preço Anual: R$ 24.900,00 (Recurring, Yearly) - 2 meses grátis
    Metadata:
      - plan_tier: professional
      - max_jobs: 50
      - max_users: 20
    Tax behavior: Exclusive
  
  PRODUTO 3 - WeDo Enterprise:
    Name: WeDo Talent Enterprise
    Description: Plano customizado para grandes empresas
    Pricing: Custom (usar Quotes no Stripe para propostas)
    Metadata:
      - plan_tier: enterprise
      - max_jobs: unlimited
      - max_users: unlimited
    Nota: Não criar preço fixo, usar Quote API
  
  PRODUTO 4 - Setup Fee:
    Name: Setup Fee - Implementação
    Description: Taxa única de implementação e onboarding
    Pricing:
      - Preço Único: R$ 5.000,00 (One-time)
    Metadata:
      - type: setup
    Nota: Cobrado junto com primeira fatura ou separadamente

Sincronização com HubSpot:
  Após criar produtos no Stripe, criar os mesmos em:
  HubSpot → Commerce → Products
  
  | Produto HubSpot     | Stripe Price ID | Tipo      |
  |---------------------|-----------------|-----------|
  | WeDo Starter        | price_xxx       | Recurring |
  | WeDo Professional   | price_xxx       | Recurring |
  | WeDo Enterprise     | -               | Quote     |
  | Setup Fee           | price_xxx       | One-time  |

Entregáveis para Devs:
  Formato YAML para configuração:
  
  STRIPE_PRODUCTS:
    STARTER:
      product_id: prod_xxx
      price_monthly_id: price_xxx
      price_yearly_id: price_xxx
      mrr: 990
      max_users: 5
      max_jobs: 10
    
    PROFESSIONAL:
      product_id: prod_xxx
      price_monthly_id: price_xxx
      price_yearly_id: price_xxx
      mrr: 2490
      max_users: 20
      max_jobs: 50
    
    ENTERPRISE:
      product_id: prod_xxx
      price_id: custom/quote
      mrr: variable
      max_users: unlimited
      max_jobs: unlimited
    
    SETUP_FEE:
      product_id: prod_xxx
      price_id: price_xxx
      amount: 5000

Critérios de Aceitação:
  - [ ] 4 produtos criados no Stripe
  - [ ] Preços mensais e anuais para Starter e Professional
  - [ ] Metadata com tier, max_jobs, max_users
  - [ ] Produtos espelhados no HubSpot Commerce
  - [ ] IDs documentados para devs
```

---

### CARD GST-STR-003: Configurar Customer Portal

```yaml
Titulo: [GESTOR] Configurar Stripe Customer Portal
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Stripe
Sequência: 3 de 7
Dependências: GST-STR-002

Descrição: |
  Configurar o Customer Portal do Stripe para que clientes
  possam gerenciar suas assinaturas sem desenvolvimento adicional.

Objetivo: |
  Permitir que clientes WeDo Talent acessem um portal self-service
  para atualizar cartão, cancelar plano, ver faturas, etc.

Passo a Passo:
  1. Acessar Dashboard → Settings → Billing → Customer portal
  2. Clicar "Activate test link" (depois ativar produção)
  3. Configurar seções habilitadas:
     
     INVOICE HISTORY:
       - [x] Customers can view invoice history
       - [x] Customers can download invoices
     
     CUSTOMER INFORMATION:
       - [x] Customers can update email
       - [x] Customers can update billing address
       - [x] Customers can update tax IDs
     
     PAYMENT METHODS:
       - [x] Customers can update payment methods
       - [x] Customers can delete payment methods
     
     SUBSCRIPTIONS:
       - [x] Customers can switch plans (upsell/downsell)
       - [x] Customers can cancel subscriptions
       - Cancellation: At end of billing period
       - Proration: Always (calcular proporcional)
     
  4. Personalizar branding:
     - Business name: WeDo Talent
     - Logo: Upload logo WeDo
     - Colors: Primary #60BED1 (WeDo Cyan)
     - Terms of Service URL: https://wedotalent.com/termos
     - Privacy Policy URL: https://wedotalent.com/privacidade
  
  5. Salvar configurações

Entregáveis para Devs:
  - Customer Portal habilitado: SIM
  - URL do Portal: (gerado via API - billingPortalSession)
  - Recursos habilitados: Invoice, Payment, Subscription management

Critérios de Aceitação:
  - [ ] Portal ativado
  - [ ] Branding configurado (logo, cores)
  - [ ] Clientes podem trocar de plano
  - [ ] Clientes podem cancelar
  - [ ] Clientes podem atualizar cartão
```

---

### CARD GST-STR-004: Configurar Webhook Endpoint

```yaml
Titulo: [GESTOR] Criar Webhook Endpoint no Stripe
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Crítica
Ferramenta: Stripe
Sequência: 4 de 7
Dependências: GST-STR-001

Descrição: |
  Configurar endpoint de webhook para que o Stripe notifique
  o backend sobre eventos de pagamento, assinatura, etc.

Objetivo: |
  Receber notificações em tempo real sobre eventos de billing
  para manter o banco de dados sincronizado.

Passo a Passo:
  1. Acessar Dashboard → Developers → Webhooks
  2. Clicar "Add endpoint"
  3. Configurar endpoint:
     
     Endpoint URL: https://api.wedotalent.com/api/v1/webhooks/stripe
     (ou URL de staging para testes)
     
     Description: WeDo Talent Admin - Billing Events
     
  4. Selecionar eventos a escutar:
     
     CHECKOUT:
       - [x] checkout.session.completed
       - [x] checkout.session.expired
     
     CUSTOMER:
       - [x] customer.created
       - [x] customer.updated
       - [x] customer.deleted
     
     SUBSCRIPTION:
       - [x] customer.subscription.created
       - [x] customer.subscription.updated
       - [x] customer.subscription.deleted
       - [x] customer.subscription.paused
       - [x] customer.subscription.resumed
       - [x] customer.subscription.trial_will_end
     
     INVOICE:
       - [x] invoice.created
       - [x] invoice.paid
       - [x] invoice.payment_failed
       - [x] invoice.payment_action_required
       - [x] invoice.finalized
     
     PAYMENT:
       - [x] payment_intent.succeeded
       - [x] payment_intent.payment_failed
     
  5. Clicar "Add endpoint"
  6. Copiar "Signing secret" (whsec_xxx)

Entregáveis para Devs:
  STRIPE_WEBHOOK_SECRET: whsec_xxx
  
  Eventos habilitados:
    - checkout.session.completed
    - checkout.session.expired
    - customer.created
    - customer.updated
    - customer.deleted
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - customer.subscription.paused
    - customer.subscription.resumed
    - customer.subscription.trial_will_end
    - invoice.created
    - invoice.paid
    - invoice.payment_failed
    - invoice.payment_action_required
    - invoice.finalized
    - payment_intent.succeeded
    - payment_intent.payment_failed

Critérios de Aceitação:
  - [ ] Endpoint criado
  - [ ] Todos os eventos selecionados
  - [ ] Webhook secret copiado
  - [ ] Documentado para devs
```

---

### CARD GST-STR-005: Gerar API Keys

```yaml
Titulo: [GESTOR] Gerar API Keys do Stripe
Tipo: Configuração SaaS
Tempo: 5 minutos
Prioridade: Crítica
Ferramenta: Stripe
Sequência: 5 de 7
Dependências: GST-STR-001

Descrição: |
  Gerar as chaves de API (Secret e Publishable) para
  integração do backend e frontend com o Stripe.

Objetivo: |
  Fornecer as credenciais necessárias para os devs
  implementarem a integração Stripe.

Passo a Passo:
  1. Acessar Dashboard → Developers → API keys
  
  2. MODO TESTE (para desenvolvimento):
     - Copiar "Publishable key" (pk_test_xxx)
     - Copiar "Secret key" (sk_test_xxx)
     - Revelar clicando no ícone de olho
  
  3. MODO PRODUÇÃO (quando estiver pronto):
     - Alternar para "Live mode" no toggle
     - Copiar "Publishable key" (pk_live_xxx)
     - Copiar "Secret key" (sk_live_xxx)
     - ATENÇÃO: Secret key só aparece UMA VEZ
  
  4. (Opcional) Criar Restricted Key:
     - Clicar "Create restricted key"
     - Nome: "WeDo Talent Backend"
     - Permissões: Read/Write apenas para recursos necessários
     - Copiar chave restrita

Entregáveis para Devs:
  AMBIENTE DE TESTE:
    STRIPE_PUBLISHABLE_KEY: pk_test_xxx
    STRIPE_SECRET_KEY: sk_test_xxx
  
  AMBIENTE DE PRODUÇÃO:
    STRIPE_PUBLISHABLE_KEY: pk_live_xxx
    STRIPE_SECRET_KEY: sk_live_xxx

Notas de Segurança:
  - Secret Key NUNCA deve ir no frontend
  - Publishable Key pode ir no frontend (é pública)
  - Usar variáveis de ambiente, nunca hardcode
  - Rotacionar keys anualmente

Critérios de Aceitação:
  - [ ] Keys de teste geradas
  - [ ] Keys de produção geradas
  - [ ] Documentadas de forma segura
  - [ ] Entregues aos devs via canal seguro
```

---

### CARD GST-STR-006: Configurar Métodos de Pagamento Brasil

```yaml
Titulo: [GESTOR] Habilitar Métodos de Pagamento Brasileiros
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Stripe
Sequência: 6 de 7
Dependências: GST-STR-001

Descrição: |
  Habilitar métodos de pagamento específicos para o Brasil:
  Boleto, PIX, e cartões brasileiros.

Objetivo: |
  Maximizar conversão de pagamentos oferecendo os métodos
  preferidos pelos clientes brasileiros.

Passo a Passo:
  1. Acessar Dashboard → Settings → Payment methods
  
  2. Verificar se está no contexto Brasil:
     - Se não, configurar país de operação
  
  3. Habilitar métodos:
     
     CARTÕES:
       - [x] Visa
       - [x] Mastercard
       - [x] American Express
       - [x] Elo (Brasil)
       - [x] Hipercard (Brasil)
     
     BOLETO BANCÁRIO:
       - [x] Boleto
       - Configurar vencimento padrão: 3 dias
       - Habilitar lembretes automáticos
     
     PIX:
       - [x] Pix
       - Validade do QR Code: 24 horas
     
  4. Configurar preferências:
     - Ordem de exibição: Cartão > PIX > Boleto
     - Moeda padrão: BRL

Entregáveis para Devs:
  Métodos habilitados:
    - card (Visa, Mastercard, Amex, Elo, Hipercard)
    - boleto (vencimento 3 dias)
    - pix (validade 24h)
  
  Configuração de checkout:
    payment_method_types: ['card', 'boleto', 'pix']

Critérios de Aceitação:
  - [ ] Cartões internacionais habilitados
  - [ ] Elo e Hipercard habilitados
  - [ ] Boleto habilitado com vencimento 3 dias
  - [ ] PIX habilitado
```

---

### CARD GST-STR-007: Documentar Configuração Stripe

```yaml
Titulo: [GESTOR] Criar Documento de Handoff Stripe
Tipo: Documentação
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Stripe
Sequência: 7 de 7
Dependências: GST-STR-001 a GST-STR-006

Descrição: |
  Consolidar todas as informações do Stripe em um documento
  de handoff para o time de desenvolvimento.

Objetivo: |
  Fornecer aos devs todas as credenciais e IDs necessários
  para implementar a integração Stripe.

Template do Documento:

  ```
  ═══════════════════════════════════════════════════════════════
  HANDOFF STRIPE - WEDO TALENT
  Data: [DATA]
  Responsável: [NOME]
  ═══════════════════════════════════════════════════════════════
  
  1. CREDENCIAIS
  ─────────────────────────────────────────────────────────────────
  
  TESTE:
    STRIPE_PUBLISHABLE_KEY=pk_test_xxx
    STRIPE_SECRET_KEY=sk_test_xxx
    STRIPE_WEBHOOK_SECRET=whsec_xxx
  
  PRODUÇÃO:
    STRIPE_PUBLISHABLE_KEY=pk_live_xxx
    STRIPE_SECRET_KEY=sk_live_xxx
    STRIPE_WEBHOOK_SECRET=whsec_xxx
  
  2. PRODUTOS E PREÇOS
  ─────────────────────────────────────────────────────────────────
  
  STARTER:
    product_id: prod_xxx
    price_monthly: price_xxx (R$ 497/mês)
    price_yearly: price_xxx (R$ 4.970/ano)
  
  PROFESSIONAL:
    product_id: prod_xxx
    price_monthly: price_xxx (R$ 1.497/mês)
    price_yearly: price_xxx (R$ 14.970/ano)
  
  ENTERPRISE:
    product_id: prod_xxx
    price: custom/quote
  
  TRIAGEM_AVULSA:
    product_id: prod_xxx
    price: price_xxx (R$ 49/unidade)
  
  3. WEBHOOK ENDPOINT
  ─────────────────────────────────────────────────────────────────
  
  URL: https://api.wedotalent.com/api/v1/webhooks/stripe
  
  Eventos:
    - checkout.session.completed
    - customer.created
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.paid
    - invoice.payment_failed
  
  4. CUSTOMER PORTAL
  ─────────────────────────────────────────────────────────────────
  
  Status: Ativado
  Recursos: Invoice, Payment, Subscription management
  
  5. MÉTODOS DE PAGAMENTO
  ─────────────────────────────────────────────────────────────────
  
  - Cartões (Visa, Mastercard, Amex, Elo, Hipercard)
  - Boleto (vencimento 3 dias)
  - PIX (validade 24h)
  
  ═══════════════════════════════════════════════════════════════
  ```

Critérios de Aceitação:
  - [ ] Documento criado
  - [ ] Todas as credenciais preenchidas
  - [ ] Todos os IDs documentados
  - [ ] Entregue ao time de devs
```

---

## HUBSPOT - Configuração do CRM (10 cards)

---

### CARD GST-HUB-001: Configurar Private App

```yaml
Titulo: [GESTOR] Criar Private App no HubSpot
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Crítica
Ferramenta: HubSpot
Sequência: 1 de 10

Descrição: |
  Criar um Private App no HubSpot para obter o Access Token
  que permite a integração via API.

Objetivo: |
  Gerar credenciais de API para que o backend possa
  criar, atualizar e sincronizar dados de clientes.

Passo a Passo:
  1. Acessar HubSpot → Settings (engrenagem)
  2. Navegar para Integrations → Private Apps
  3. Clicar "Create a private app"
  
  4. Configurar Basic Info:
     - App name: WeDo Talent Admin Backend
     - Description: Integração backend para sync de clientes, billing e onboarding
     - Logo: Upload logo WeDo (opcional)
  
  5. Configurar Scopes (permissões):
     
     CRM:
       - [x] crm.objects.companies.read
       - [x] crm.objects.companies.write
       - [x] crm.objects.contacts.read
       - [x] crm.objects.contacts.write
       - [x] crm.objects.deals.read
       - [x] crm.objects.deals.write
       - [x] crm.schemas.companies.read
       - [x] crm.schemas.deals.read
     
     PIPELINES:
       - [x] crm.objects.deals.read
       - [x] crm.lists.read
       - [x] crm.lists.write
     
     PROPERTIES:
       - [x] settings.users.read
       - [x] properties.read (legacy)
  
  6. Clicar "Create app"
  7. Copiar Access Token (pat-xxx)
     - ATENÇÃO: Token só aparece UMA VEZ

Entregáveis para Devs:
  HUBSPOT_ACCESS_TOKEN: pat-na1-xxx
  HUBSPOT_PORTAL_ID: xxx (visível na URL do dashboard)

Nota: Já existe HUBSPOT_ACCESS_TOKEN configurado nos secrets.
      Verificar se tem as permissões necessárias.

Critérios de Aceitação:
  - [ ] Private App criada
  - [ ] Scopes configurados corretamente
  - [ ] Access Token copiado
  - [ ] Portal ID documentado
```

---

### CARD GST-HUB-002: Criar Propriedades Customizadas - Companies

```yaml
Titulo: [GESTOR] Criar Propriedades Customizadas (Companies)
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Crítica
Ferramenta: HubSpot
Sequência: 2 de 10
Dependências: GST-HUB-001

Descrição: |
  Criar propriedades customizadas nas Companies do HubSpot
  para armazenar dados específicos do WeDo Talent.

Objetivo: |
  Ter campos customizados para sincronizar tenant_id, stripe_id,
  workos_id, plano, MRR, status, etc.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 1, Passo 1.2

Passo a Passo:
  1. Acessar Settings → Data Management → Properties
  2. Selecionar "Company properties"
  3. Clicar "Create property group":
     - Group name: WeDo Talent
     - Description: Dados específicos da integração WeDo Talent
  
  4. Criar cada propriedade no grupo "WeDo Talent":

╔══════════════════════════════════════════════════════════════════════════════╗
║                    TABELA DE PROPRIEDADES - COMPANIES (11)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ # │ Internal Name          │ Label                │ Tipo         │ Opções   ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 1 │ wedo_client_id         │ WeDo Client ID       │ Single-line  │ -        ║
║   │                        │                      │ text         │          ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 2 │ wedo_plan              │ Plano WeDo           │ Dropdown     │ Starter  ║
║   │                        │                      │              │ Profess. ║
║   │                        │                      │              │ Enterpr. ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 3 │ wedo_status            │ Status WeDo          │ Dropdown     │ trial    ║
║   │                        │                      │              │ active   ║
║   │                        │                      │              │ suspended║
║   │                        │                      │              │ cancelled║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 4 │ wedo_mrr               │ MRR                  │ Number       │ BRL      ║
║   │                        │                      │ (Currency)   │          ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 5 │ wedo_user_limit        │ Limite de Usuários   │ Number       │ -        ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 6 │ wedo_users_count       │ Usuários Ativos      │ Number       │ -        ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 7 │ wedo_sso_enabled       │ SSO Habilitado       │ Single       │ -        ║
║   │                        │                      │ checkbox     │          ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 8 │ wedo_workos_org_id     │ WorkOS Org ID        │ Single-line  │ -        ║
║   │                        │                      │ text         │          ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║ 9 │ wedo_stripe_customer_id│ Stripe Customer ID   │ Single-line  │ -        ║
║   │                        │                      │ text         │          ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║10 │ wedo_onboarding_started│ Data Onboarding      │ Date picker  │ -        ║
╠═══╪════════════════════════╪══════════════════════╪══════════════╪══════════╣
║11 │ wedo_onboarding_       │ Onboarding Completo  │ Single       │ -        ║
║   │ completed              │                      │ checkbox     │          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Detalhes de Cada Propriedade:

  PROPRIEDADE 1 - wedo_client_id:
    Internal name: wedo_client_id
    Label: WeDo Client ID
    Field type: Single-line text
    Description: ID único do cliente no sistema WeDo Talent (UUID)
    Group: WeDo Talent
  
  PROPRIEDADE 2 - wedo_plan:
    Internal name: wedo_plan
    Label: Plano WeDo
    Field type: Dropdown select
    Options (exatamente nesta ordem):
      - Starter (R$ 990/mês)
      - Professional (R$ 2.490/mês)
      - Enterprise (Customizado)
    Group: WeDo Talent
  
  PROPRIEDADE 3 - wedo_status:
    Internal name: wedo_status
    Label: Status WeDo
    Field type: Dropdown select
    Options (exatamente nesta ordem):
      - trial (período de teste)
      - active (cliente ativo pagante)
      - suspended (suspenso por falta de pagamento)
      - cancelled (cancelado/churned)
    Group: WeDo Talent
  
  PROPRIEDADE 4 - wedo_mrr:
    Internal name: wedo_mrr
    Label: MRR
    Field type: Number (Currency BRL)
    Description: Monthly Recurring Revenue em Reais
    Group: WeDo Talent
  
  PROPRIEDADE 5 - wedo_user_limit:
    Internal name: wedo_user_limit
    Label: Limite de Usuários
    Field type: Number
    Description: Quantidade máxima de usuários permitidos no plano
    Group: WeDo Talent
  
  PROPRIEDADE 6 - wedo_users_count:
    Internal name: wedo_users_count
    Label: Usuários Ativos
    Field type: Number
    Description: Quantidade atual de usuários ativos (atualizado via SCIM)
    Group: WeDo Talent
  
  PROPRIEDADE 7 - wedo_sso_enabled:
    Internal name: wedo_sso_enabled
    Label: SSO Habilitado
    Field type: Single checkbox
    Description: Se o cliente tem SSO configurado via WorkOS
    Group: WeDo Talent
  
  PROPRIEDADE 8 - wedo_workos_org_id:
    Internal name: wedo_workos_org_id
    Label: WorkOS Org ID
    Field type: Single-line text
    Description: ID da organização no WorkOS (org_xxx)
    Group: WeDo Talent
  
  PROPRIEDADE 9 - wedo_stripe_customer_id:
    Internal name: wedo_stripe_customer_id
    Label: Stripe Customer ID
    Field type: Single-line text
    Description: ID do cliente no Stripe (cus_xxx)
    Group: WeDo Talent
  
  PROPRIEDADE 10 - wedo_onboarding_started:
    Internal name: wedo_onboarding_started
    Label: Data Onboarding
    Field type: Date picker
    Description: Data de início do onboarding
    Group: WeDo Talent
  
  PROPRIEDADE 11 - wedo_onboarding_completed:
    Internal name: wedo_onboarding_completed
    Label: Onboarding Completo
    Field type: Single checkbox
    Description: Marca quando onboarding foi finalizado com sucesso
    Group: WeDo Talent

Entregáveis para Devs:
  Grupo: WeDo Talent
  
  Propriedades criadas (11 total):
    | Internal Name            | Type     | Uso API                          |
    |--------------------------|----------|----------------------------------|
    | wedo_client_id           | text     | Buscar company pelo ID WeDo      |
    | wedo_plan                | dropdown | Starter, Professional, Enterprise|
    | wedo_status              | dropdown | trial, active, suspended, cancelled|
    | wedo_mrr                 | number   | Valor em centavos ou reais       |
    | wedo_user_limit          | number   | Limite do plano                  |
    | wedo_users_count         | number   | Contador atualizado via SCIM     |
    | wedo_sso_enabled         | boolean  | true/false                       |
    | wedo_workos_org_id       | text     | org_xxx                          |
    | wedo_stripe_customer_id  | text     | cus_xxx                          |
    | wedo_onboarding_started  | date     | ISO 8601                         |
    | wedo_onboarding_completed| boolean  | true/false                       |

Critérios de Aceitação:
  - [ ] Grupo "WeDo Talent" criado em Company properties
  - [ ] 11 propriedades criadas
  - [ ] Dropdowns com opções EXATAS conforme especificado
  - [ ] Internal names EXATOS para integração API
  - [ ] Propriedades visíveis no card de Company
```

---

### CARD GST-HUB-003: Criar Pipeline de Vendas (WeDo Talent Contracts)

```yaml
Titulo: [GESTOR] Criar Pipeline de Vendas (Deals)
Tipo: Configuração SaaS
Tempo: 20 minutos
Prioridade: Alta
Ferramenta: HubSpot
Sequência: 3 de 10
Dependências: GST-HUB-001

Descrição: |
  Criar pipeline de vendas no HubSpot para acompanhar
  o funil de novos clientes WeDo Talent.

Objetivo: |
  Ter visibilidade do pipeline de vendas com estágios
  e probabilidades de fechamento.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 1, Passo 1.4

Passo a Passo:
  1. Acessar Settings → Objects → Deals → Pipelines
  2. Clicar "Create pipeline"
  
  3. Configurar pipeline:
     - Pipeline name: WeDo Talent Contracts
     - Tipo: Sales

╔══════════════════════════════════════════════════════════════════════════════╗
║           PIPELINE: "WeDo Talent Contracts" - ESTÁGIOS (7)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ # │ Stage Name           │ Prob. │ Ações Automáticas                        ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 1 │ Proposta Enviada     │ 20%   │ -                                        ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 2 │ Proposta Aceita      │ 40%   │ -                                        ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 3 │ Contrato Assinado    │ 60%   │ → Criar cliente no Stripe                ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 4 │ Pagamento Recebido   │ 80%   │ → Ativar conta WeDo Talent               ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 5 │ Cliente Ativo (Won)  │ 100%  │ → Disparar Workflow "Criar Ticket        ║
║   │                      │       │   de Onboarding" no HubSpot              ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 6 │ Renovação            │ 100%  │ → Atualizar wedo_contract_end            ║
╠═══╪══════════════════════╪═══════╪══════════════════════════════════════════╣
║ 7 │ Perdido (Lost)       │ 0%    │ → Atualizar wedo_status = cancelled      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Detalhes de Cada Estágio:

  ESTÁGIO 1 - Proposta Enviada:
    Name: Proposta Enviada
    Probability: 20%
    Ordem: 1
    Descrição: Proposta comercial enviada ao prospect
  
  ESTÁGIO 2 - Proposta Aceita:
    Name: Proposta Aceita
    Probability: 40%
    Ordem: 2
    Descrição: Cliente aceitou proposta, aguardando assinatura
  
  ESTÁGIO 3 - Contrato Assinado:
    Name: Contrato Assinado
    Probability: 60%
    Ordem: 3
    Descrição: Contrato assinado, aguardando pagamento
    Ação Automática: Criar Customer no Stripe (via backend)
  
  ESTÁGIO 4 - Pagamento Recebido:
    Name: Pagamento Recebido
    Probability: 80%
    Ordem: 4
    Descrição: Primeiro pagamento confirmado
    Ação Automática: Ativar conta no WeDo Talent
  
  ESTÁGIO 5 - Cliente Ativo (Closed Won):
    Name: Cliente Ativo
    Probability: 100%
    Ordem: 5
    Tipo: Won
    Descrição: Cliente ativo e pagando
    Ações Automáticas:
      - Disparar Workflow "Criar Plano Onboarding"
      - Atualizar wedo_status = active
      - Definir wedo_onboarding_started = hoje
  
  ESTÁGIO 6 - Renovação:
    Name: Renovação
    Probability: 100%
    Ordem: 6
    Descrição: Deal de renovação anual
    Ação: Atualizar wedo_contract_end
  
  ESTÁGIO 7 - Perdido (Closed Lost):
    Name: Perdido
    Probability: 0%
    Ordem: 7
    Tipo: Lost
    Descrição: Negócio não fechado
    Ação: Registrar motivo de perda

Entregáveis para Devs:
  PIPELINE_VENDAS:
    pipeline_id: xxx
    pipeline_name: "WeDo Talent Contracts"
  
  STAGE_IDS:
    proposta_enviada: xxx
    proposta_aceita: xxx
    contrato_assinado: xxx
    pagamento_recebido: xxx
    cliente_ativo: xxx (won)
    renovacao: xxx
    perdido: xxx (lost)
  
  Trigger para Backend:
    - Quando stage = "Contrato Assinado": criar Stripe Customer
    - Quando stage = "Cliente Ativo": criar Ticket de Onboarding no HubSpot

Critérios de Aceitação:
  - [ ] Pipeline "WeDo Talent Contracts" criado
  - [ ] 7 estágios configurados com nomes EXATOS
  - [ ] Probabilidades conforme tabela
  - [ ] IDs de stages documentados para backend
```

---

### CARD GST-HUB-004: Criar Pipeline de Onboarding (Customer Onboarding)

```yaml
Titulo: [GESTOR] Criar Pipeline de Onboarding (Service Hub)
Tipo: Configuração SaaS
Tempo: 20 minutos
Prioridade: Alta
Ferramenta: HubSpot
Sequência: 4 de 10
Dependências: GST-HUB-001

Descrição: |
  Criar pipeline de onboarding no HubSpot para acompanhar
  a jornada de implementação de novos clientes.

Objetivo: |
  Ter visibilidade do progresso de onboarding e garantir
  que todos os passos sejam executados.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 1, Passo 1.5

Passo a Passo:
  1. Acessar Settings → Objects → Services (ou Tickets)
  2. Clicar "Create pipeline"
  
  3. Configurar pipeline:
     - Pipeline name: Customer Onboarding
     - Tipo: Service / Onboarding

╔══════════════════════════════════════════════════════════════════════════════╗
║             PIPELINE: "Customer Onboarding" - ESTÁGIOS (7)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ # │ Stage Name              │ Descrição                                     ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 1 │ Aguardando Kickoff      │ Cliente pagou, aguardando reunião inicial     ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 2 │ Kickoff Realizado       │ Reunião inicial feita, objetivos definidos    ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 3 │ Configuração SSO        │ Configurando WorkOS, provisionando usuários   ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 4 │ Importação Dados        │ Importando candidatos/vagas existentes        ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 5 │ Treinamento             │ Sessões de capacitação realizadas             ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 6 │ Go-Live                 │ Em produção com primeira vaga real            ║
╠═══╪═════════════════════════╪═══════════════════════════════════════════════╣
║ 7 │ Onboarding Completo     │ Sucesso! Cliente operando independentemente   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Sincronização com HubSpot Workflows:
  Este pipeline gerencia o onboarding através de Tickets e Workflows nativos do HubSpot:
  
  | Stage HubSpot           | Fase Onboarding      | Propriedade Sync       |
  |-------------------------|----------------------|------------------------|
  | Aguardando Kickoff      | 1. Welcome           | wedo_onboarding_phase  |
  | Kickoff Realizado       | 2. Kickoff           | wedo_onboarding_phase  |
  | Configuração SSO        | 3. SSO               | wedo_onboarding_phase  |
  | Importação Dados        | 4. Setup             | wedo_onboarding_phase  |
  | Treinamento             | 5. Treinamento       | wedo_onboarding_phase  |
  | Go-Live                 | 6. Go-Live           | wedo_onboarding_phase  |
  | Onboarding Completo     | Completo             | wedo_onboarding_completed = true |

Detalhes de Cada Estágio:

  ESTÁGIO 1 - Aguardando Kickoff:
    Name: Aguardando Kickoff
    Descrição: Cliente pagou, aguardando agendamento de reunião inicial
    Duração esperada: 1-3 dias
    Tarefas:
      - Enviar email de boas-vindas
      - Criar convite calendário
      - Preparar material kickoff
  
  ESTÁGIO 2 - Kickoff Realizado:
    Name: Kickoff Realizado
    Descrição: Reunião inicial feita, objetivos de sucesso definidos
    Duração esperada: 1 dia
    Tarefas:
      - Definir KPIs de sucesso
      - Identificar stakeholders
      - Alinhar cronograma
  
  ESTÁGIO 3 - Configuração SSO:
    Name: Configuração SSO
    Descrição: Configurando SSO via WorkOS (se enterprise)
    Duração esperada: 2-5 dias
    Tarefas:
      - Conectar IdP do cliente (Okta/Azure AD)
      - Testar login SSO
      - Habilitar SCIM provisioning
    Nota: Apenas para planos Enterprise/Professional
  
  ESTÁGIO 4 - Importação Dados:
    Name: Importação Dados
    Descrição: Importando candidatos e vagas existentes
    Duração esperada: 1-3 dias
    Tarefas:
      - Exportar dados do ATS atual
      - Mapear campos
      - Validar importação
  
  ESTÁGIO 5 - Treinamento:
    Name: Treinamento
    Descrição: Sessões de capacitação
    Duração esperada: 3-7 dias
    Tarefas:
      - Treinamento admins (2h)
      - Treinamento recrutadores (1h)
      - Entregar documentação
  
  ESTÁGIO 6 - Go-Live:
    Name: Go-Live
    Descrição: Em produção com primeira vaga real
    Duração esperada: 7 dias
    Tarefas:
      - Criar primeira vaga real
      - Acompanhar triagem
      - Suporte intensivo
  
  ESTÁGIO 7 - Onboarding Completo:
    Name: Onboarding Completo
    Descrição: Sucesso! Cliente operando independentemente
    Ações:
      - Marcar wedo_onboarding_completed = true
      - Enviar NPS após 30 dias
      - Transição para suporte regular

Entregáveis para Devs:
  PIPELINE_ONBOARDING:
    pipeline_id: xxx
    pipeline_name: "Customer Onboarding"
  
  STAGE_IDS:
    aguardando_kickoff: xxx
    kickoff_realizado: xxx
    configuracao_sso: xxx
    importacao_dados: xxx
    treinamento: xxx
    go_live: xxx
    onboarding_completo: xxx

Critérios de Aceitação:
  - [ ] Pipeline "Customer Onboarding" criado
  - [ ] 7 estágios configurados com nomes EXATOS
  - [ ] Descrições em cada estágio
  - [ ] IDs de stages documentados
```

---

### CARD GST-HUB-005: Criar Propriedades de Contatos

```yaml
Titulo: [GESTOR] Criar Propriedades Customizadas (Contacts)
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Média
Ferramenta: HubSpot
Sequência: 5 de 10
Dependências: GST-HUB-001

Descrição: |
  Criar propriedades customizadas nos Contacts do HubSpot
  para armazenar dados de usuários dos clientes.

Objetivo: |
  Ter campos para identificar role, status e dados
  de sync dos usuários dos clientes WeDo Talent.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 1, Passo 1.3

Passo a Passo:
  1. Acessar Settings → Data Management → Properties
  2. Selecionar "Contact properties"
  3. Criar propriedades no grupo "WeDo Talent":

╔══════════════════════════════════════════════════════════════════════════════╗
║                     TABELA DE PROPRIEDADES - CONTACTS (4)                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ # │ Internal Name         │ Label               │ Tipo        │ Fonte Sync  ║
╠═══╪═══════════════════════╪═════════════════════╪═════════════╪═════════════╣
║ 1 │ wedo_role             │ Role WeDo           │ Dropdown    │ Backend     ║
╠═══╪═══════════════════════╪═════════════════════╪═════════════╪═════════════╣
║ 2 │ wedo_client_id        │ WeDo Client ID      │ Single-line │ Backend     ║
╠═══╪═══════════════════════╪═════════════════════╪═════════════╪═════════════╣
║ 3 │ wedo_last_login       │ Último Login        │ Date picker │ WorkOS      ║
╠═══╪═══════════════════════╪═════════════════════╪═════════════╪═════════════╣
║ 4 │ wedo_scim_provisioned │ SCIM Provisioned    │ Checkbox    │ WorkOS SCIM ║
╚══════════════════════════════════════════════════════════════════════════════╝

Propriedades a Criar:

  PROPRIEDADE 1 - wedo_role:
    Internal name: wedo_role
    Label: Role WeDo
    Field type: Dropdown select
    Options (exatamente):
      - admin
      - recruiter
      - hiring_manager
      - viewer
    Description: Papel do usuário no cliente WeDo Talent
    Group: WeDo Talent
  
  PROPRIEDADE 2 - wedo_client_id:
    Internal name: wedo_client_id
    Label: WeDo Client ID
    Field type: Single-line text
    Description: ID do cliente (empresa) a que este contato pertence
    Group: WeDo Talent
    Nota: Usado para associar contato à company correta
  
  PROPRIEDADE 3 - wedo_last_login:
    Internal name: wedo_last_login
    Label: Último Login
    Field type: Date picker
    Description: Data do último login do usuário
    Group: WeDo Talent
    Fonte: Atualizado via WorkOS webhook
  
  PROPRIEDADE 4 - wedo_scim_provisioned:
    Internal name: wedo_scim_provisioned
    Label: SCIM Provisioned
    Field type: Single checkbox
    Description: Indica se usuário foi provisionado via SCIM/Directory Sync
    Group: WeDo Talent
    Fonte: Atualizado via WorkOS dsync webhook

Relação Contact ↔ Company:
  - Contatos devem ser associados à Company correta
  - wedo_client_id no Contact = wedo_client_id na Company
  - Permite filtros e reports por empresa

Entregáveis para Devs:
  Grupo: WeDo Talent
  
  Propriedades de contato criadas (4 total):
    | Internal Name         | Type     | Uso API                     |
    |-----------------------|----------|-----------------------------|
    | wedo_role             | dropdown | admin, recruiter, etc       |
    | wedo_client_id        | text     | UUID do cliente             |
    | wedo_last_login       | date     | ISO 8601                    |
    | wedo_scim_provisioned | boolean  | true se via SCIM            |

Critérios de Aceitação:
  - [ ] 4 propriedades de contato criadas
  - [ ] Internal names EXATOS conforme tabela
  - [ ] Dropdown wedo_role com 4 opções
  - [ ] Propriedades visíveis no card de Contact
```

---

### CARD GST-HUB-006: Criar Listas e Segmentos

```yaml
Titulo: [GESTOR] Criar Listas de Segmentação
Tipo: Configuração SaaS
Tempo: 20 minutos
Prioridade: Média
Ferramenta: HubSpot
Sequência: 6 de 10
Dependências: GST-HUB-002

Descrição: |
  Criar listas dinâmicas no HubSpot para segmentar
  clientes por plano, status, etc.

Objetivo: |
  Facilitar comunicações segmentadas e dashboards
  por categoria de cliente.

Passo a Passo:
  1. Acessar Contacts → Lists
  2. Clicar "Create list"
  3. Selecionar "Company-based" para cada lista

Listas a Criar:

  LISTA 1:
    Name: Clientes Ativos
    Type: Active list (dinâmica)
    Filtro: wedo_status = "active"
  
  LISTA 2:
    Name: Clientes Trial
    Type: Active list
    Filtro: wedo_status = "trial"
  
  LISTA 3:
    Name: Clientes Churned
    Type: Active list
    Filtro: wedo_status = "churned"
  
  LISTA 4:
    Name: Plano Starter
    Type: Active list
    Filtro: wedo_plan = "starter"
  
  LISTA 5:
    Name: Plano Professional
    Type: Active list
    Filtro: wedo_plan = "professional"
  
  LISTA 6:
    Name: Plano Enterprise
    Type: Active list
    Filtro: wedo_plan = "enterprise"
  
  LISTA 7:
    Name: Onboarding em Andamento
    Type: Active list
    Filtro: wedo_onboarding_stage NOT IN ("not_started", "completed")
  
  LISTA 8:
    Name: SSO Habilitado
    Type: Active list
    Filtro: wedo_sso_enabled = true

Entregáveis para Devs:
  LIST_IDS:
    clientes_ativos: xxx
    clientes_trial: xxx
    clientes_churned: xxx
    plano_starter: xxx
    plano_professional: xxx
    plano_enterprise: xxx
    onboarding_andamento: xxx
    sso_habilitado: xxx

Critérios de Aceitação:
  - [ ] 8 listas criadas
  - [ ] Listas dinâmicas (atualizam automaticamente)
  - [ ] Filtros corretos
```

---

### CARD GST-HUB-007: Conectar Stripe ao HubSpot

```yaml
Titulo: [GESTOR] Conectar Integração Stripe ↔ HubSpot
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: HubSpot + Stripe
Sequência: 7 de 10
Dependências: GST-STR-001, GST-HUB-001

Descrição: |
  Conectar a integração nativa Stripe + HubSpot para
  sincronizar automaticamente pagamentos e receita.

Objetivo: |
  Ter visibilidade de MRR, pagamentos e faturas
  diretamente no HubSpot sem desenvolvimento.

Passo a Passo:
  1. Acessar HubSpot App Marketplace:
     https://ecosystem.hubspot.com/marketplace/apps/sales/payments/stripe
  
  2. Clicar "Install app" ou "Connect app"
  
  3. Autorizar conexão:
     - Fazer login no Stripe
     - Autorizar acesso do HubSpot
     - Selecionar conta Stripe correta
  
  4. Configurar sincronização:
     - Sync invoices: ON
     - Sync subscriptions: ON
     - Create deals from payments: Opcional (avaliar)
     - Match customers by email: ON
  
  5. Mapear campos (via Rails StripeSyncService):
     - Stripe customer → Rails → HubSpot Company
     - Stripe subscription → Rails → Deal ou propriedade custom
     - Stripe MRR → Rails → wedo_mrr
     
     > **Nota:** A integração nativa HubSpot-Stripe não está disponível no Brasil.
     > O fluxo correto é: Stripe webhooks → Rails (StripeSyncService) → HubSpot API

Entregáveis para Devs:
  Status: Integração nativa ativa
  
  Sync automático:
    - Pagamentos Stripe aparecem em Companies
    - MRR calculado automaticamente (se mapeado)
    - Invoices visíveis no HubSpot

Nota: Esta integração nativa reduz desenvolvimento
      necessário no backend.

Critérios de Aceitação:
  - [ ] Integração instalada
  - [ ] Stripe conectado ao HubSpot
  - [ ] Sincronização ativa
  - [ ] Pagamentos aparecendo nas Companies
```

---

### CARD GST-HUB-008: Criar Workflows de Automação

```yaml
Titulo: [GESTOR] Criar Workflows de Automação
Tipo: Configuração SaaS
Tempo: 45 minutos
Prioridade: Crítica
Ferramenta: HubSpot
Sequência: 8 de 10
Dependências: GST-HUB-002, GST-HUB-003, GST-HUB-004

Descrição: |
  Criar workflows automáticos no HubSpot para notificações,
  tarefas e atualizações baseadas em eventos.

Objetivo: |
  Automatizar comunicação interna e atribuição de tarefas
  quando clientes mudam de status.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 1, Passo 1.6

Passo a Passo:
  1. Acessar Automation → Workflows
  2. Clicar "Create workflow"
  3. Selecionar "Company-based" para workflows de empresa

╔══════════════════════════════════════════════════════════════════════════════╗
║                       WORKFLOWS HUBSPOT (6)                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ # │ Nome                        │ Trigger                │ Ações Principais ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 1 │ Criar Ticket Onboarding     │ Deal stage = "Cliente  │ → HubSpot: criar ║
║   │                             │ Ativo" (Won)           │   ticket         ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 2 │ Novo Cliente - Notificar CS │ Deal stage = "Cliente  │ → Notify CS      ║
║   │                             │ Ativo" (Won)           │ → Create task    ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 3 │ Onboarding Atrasado         │ wedo_onboarding_started│ → Notify CSM     ║
║   │                             │ > 30 dias              │ → Create task    ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 4 │ Churn - Notificar Gestão    │ wedo_status =          │ → Notify Manager ║
║   │                             │ "cancelled"            │ → Create task    ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 5 │ Trial Expirando             │ wedo_status = "trial"  │ → Notify Sales   ║
║   │                             │ + 3 dias antes exp.    │ → Create task    ║
╠═══╪═════════════════════════════╪════════════════════════╪══════════════════╣
║ 6 │ Upsell Opportunity          │ wedo_users_count >     │ → Notify AE      ║
║   │                             │ 80% de wedo_user_limit │ → Create task    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Workflows Detalhados:

  ═══════════════════════════════════════════════════════════════════
  WORKFLOW 1: Criar Ticket de Onboarding (PRINCIPAL)
  ═══════════════════════════════════════════════════════════════════
  Nome: Criar Ticket de Onboarding
  Prioridade: CRÍTICA - Este é o workflow principal
  Tipo: Deal-based
  
  Trigger:
    Pipeline: WeDo Talent Contracts
    Deal Stage changed to: Cliente Ativo (Won)
  
  Actions (em sequência):
    1. Wait 1 minute (para dados sincronizarem)
    
    2. Create HubSpot Ticket (Onboarding)
       Pipeline: Customer Onboarding
       Stage: Aguardando Kickoff
       Company: [Associated Company]
       Owner: [Deal Owner ou CSM]
    
    3. Update Company Property:
       - wedo_status = "active"
       - wedo_onboarding_started = [Today]
    
    4. Send Internal Notification:
       To: CS Team
       Subject: "Novo Cliente Ativo: [Company Name]"
       Body: "Deal fechado. Ticket de onboarding criado no HubSpot."
    
    5. Create Task:
       Title: "Kickoff [Company Name]"
       Due: 2 days from now
       Assigned to: Deal Owner ou CSM
       Queue: Onboarding
  
  Notas:
    - Este workflow usa funcionalidades nativas do HubSpot
    - Tickets são gerenciados no pipeline Customer Onboarding
    - Economia de ~R$30-75k/ano vs. ferramentas externas
  ═══════════════════════════════════════════════════════════════════

  WORKFLOW 2: Novo Cliente - Notificar CS
    Nome: Novo Cliente - Notificar CS
    Tipo: Deal-based
    
    Trigger: 
      Pipeline: WeDo Talent Contracts
      Deal Stage = "Cliente Ativo" (Won)
    
    Actions:
      1. Send internal notification to CS Team
         Subject: "Novo Cliente: [Company Name]"
      2. Create task: "Agendar Kickoff"
         Due: 2 days
         Assigned to: CSM Owner
      3. Update property: wedo_status = "active"
  
  WORKFLOW 3: Onboarding Atrasado - Alerta
    Nome: Onboarding Atrasado
    Tipo: Company-based
    
    Trigger: 
      - wedo_onboarding_completed = false
      - AND wedo_onboarding_started is more than 30 days ago
    
    Actions:
      1. Send internal notification to CSM owner
         Subject: "Onboarding Atrasado: [Company Name]"
         Body: "Cliente iniciou onboarding há mais de 30 dias"
      2. Create task: "Verificar bloqueio de onboarding"
         Due: 1 day
         Priority: High
  
  WORKFLOW 4: Churn - Notificar Gestão
    Nome: Churn - Notificar Gestão
    Tipo: Company-based
    
    Trigger: 
      wedo_status changed to "cancelled"
    
    Actions:
      1. Send internal notification to CS Manager
      2. Send internal notification to Founder
      3. Create task: "Análise de churn - [Company Name]"
         Priority: High
         Checklist:
           - Motivo do cancelamento
           - Último contato
           - Lições aprendidas
  
  WORKFLOW 5: Trial Expirando - Alerta
    Nome: Trial Expirando
    Tipo: Company-based
    
    Trigger: 
      - wedo_status = "trial"
      - AND wedo_trial_end is 3 days from now
    
    Actions:
      1. Send internal notification to Sales owner
         Subject: "Trial Expirando: [Company Name]"
      2. Create task: "Follow-up trial expirando"
         Due: 1 day
  
  WORKFLOW 6: Upsell Opportunity
    Nome: Upsell Opportunity
    Tipo: Company-based
    
    Trigger:
      - wedo_plan = "Starter"
      - AND wedo_users_count > (wedo_user_limit * 0.8)
    
    Enrollment: Once per company
    
    Actions:
      1. Send internal notification to AE
         Subject: "Oportunidade Upsell: [Company Name]"
         Body: "Cliente usando 80%+ das licenças"
      2. Create task: "Propor upgrade para Professional"
         Due: 3 days

Entregáveis para Devs:
  WORKFLOW_IDS:
    criar_plano_onboarding: xxx (CRÍTICO)
    novo_cliente_notificar: xxx
    onboarding_atrasado: xxx
    churn_notificar: xxx
    trial_expirando: xxx
    upsell_opportunity: xxx
  
  Dependências de Propriedades:
    Para workflows funcionarem, devs devem garantir:
    - wedo_status atualizado via Stripe webhooks
    - wedo_onboarding_started definido ao criar client
    - wedo_onboarding_completed via Ticket stage change
    - wedo_users_count via SCIM sync

Critérios de Aceitação:
  - [ ] 6 workflows criados
  - [ ] Workflow "Criar Ticket de Onboarding" funcionando
  - [ ] Triggers corretos para cada workflow
  - [ ] Actions de notificação enviando
  - [ ] Tasks sendo criadas automaticamente
  - [ ] Tickets de onboarding sendo criados
```

---

### CARD GST-HUB-009: Configurar Dashboards e Reports

```yaml
Titulo: [GESTOR] Criar Dashboards de Métricas
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Baixa
Ferramenta: HubSpot
Sequência: 9 de 10
Dependências: GST-HUB-002, GST-HUB-006

Descrição: |
  Criar dashboards no HubSpot para visualizar métricas
  de clientes, vendas e onboarding.

Objetivo: |
  Ter visibilidade em tempo real de KPIs de negócio
  sem depender de ferramentas externas.

Passo a Passo:
  1. Acessar Reports → Dashboards
  2. Clicar "Create dashboard"
  
  DASHBOARD 1: Visão Geral Clientes
    Reports:
      - Total de Clientes por Status (pie chart)
      - Total de Clientes por Plano (bar chart)
      - MRR Total (single value)
      - Novos Clientes (últimos 30 dias)
      - Churn Rate (últimos 30 dias)
  
  DASHBOARD 2: Pipeline de Vendas
    Reports:
      - Deals por Estágio (funnel)
      - Valor do Pipeline (by stage)
      - Taxa de Conversão por Estágio
      - Tempo Médio por Estágio
  
  DASHBOARD 3: Onboarding
    Reports:
      - Clientes em Onboarding (by stage)
      - Tempo Médio de Onboarding
      - Onboardings Atrasados (>30 dias)
      - Taxa de Sucesso de Onboarding

Entregáveis para Devs:
  Dashboards são visualização apenas.
  Não requerem integração de código.
  
  Devs devem garantir:
    - Propriedades wedo_* atualizadas corretamente
    - Estágios de pipeline movidos conforme fluxo

Critérios de Aceitação:
  - [ ] Dashboard Clientes criado
  - [ ] Dashboard Vendas criado
  - [ ] Dashboard Onboarding criado
  - [ ] Reports populando corretamente
```

---

### CARD GST-HUB-010: Documentar Configuração HubSpot

```yaml
Titulo: [GESTOR] Criar Documento de Handoff HubSpot
Tipo: Documentação
Tempo: 20 minutos
Prioridade: Alta
Ferramenta: HubSpot
Sequência: 10 de 10
Dependências: GST-HUB-001 a GST-HUB-009

Descrição: |
  Consolidar todas as informações do HubSpot em um documento
  de handoff para o time de desenvolvimento.

Template do Documento:

  ```
  ═══════════════════════════════════════════════════════════════
  HANDOFF HUBSPOT - WEDO TALENT
  Data: [DATA]
  Responsável: [NOME]
  ═══════════════════════════════════════════════════════════════
  
  1. CREDENCIAIS
  ─────────────────────────────────────────────────────────────────
  
  HUBSPOT_ACCESS_TOKEN: pat-na1-xxx (já existe nos secrets)
  HUBSPOT_PORTAL_ID: xxx
  
  2. PROPRIEDADES CUSTOMIZADAS - COMPANIES
  ─────────────────────────────────────────────────────────────────
  
  | Internal Name | Label | Type |
  |---------------|-------|------|
  | wedo_tenant_id | WeDo Tenant ID | text |
  | wedo_stripe_customer_id | Stripe Customer ID | text |
  | wedo_workos_org_id | WorkOS Org ID | text |
  | wedo_plan | Plano | dropdown |
  | wedo_mrr | MRR | number |
  | wedo_status | Status | dropdown |
  | wedo_onboarding_stage | Estágio Onboarding | dropdown |
  | wedo_contract_start | Data Início | date |
  | wedo_contract_end | Data Fim | date |
  | wedo_license_count | Qtd Licenças | number |
  | wedo_sso_enabled | SSO Ativo | boolean |
  | wedo_csm_owner | CSM | hubspot_user |
  
  3. PROPRIEDADES CUSTOMIZADAS - CONTACTS
  ─────────────────────────────────────────────────────────────────
  
  | Internal Name | Label | Type |
  |---------------|-------|------|
  | wedo_user_id | WeDo User ID | text |
  | wedo_role | Role | dropdown |
  | wedo_user_status | Status | dropdown |
  | wedo_last_login | Último Login | date |
  
  4. PIPELINES
  ─────────────────────────────────────────────────────────────────
  
  VENDAS (pipeline_id: xxx):
    - lead_qualificado: stage_xxx
    - demo_agendada: stage_xxx
    - proposta_enviada: stage_xxx
    - negociacao: stage_xxx
    - contrato_assinado: stage_xxx
    - cliente_ativo: stage_xxx (won)
    - perdido: stage_xxx (lost)
  
  ONBOARDING (pipeline_id: xxx):
    - kickoff: stage_xxx
    - configuracao_sso: stage_xxx
    - integracao_ats: stage_xxx
    - treinamento: stage_xxx
    - go_live: stage_xxx
    - sucesso: stage_xxx (won)
    - cancelado: stage_xxx (lost)
  
  5. LISTAS
  ─────────────────────────────────────────────────────────────────
  
  | Lista | ID | Filtro |
  |-------|-----|--------|
  | Clientes Ativos | xxx | wedo_status = active |
  | Clientes Trial | xxx | wedo_status = trial |
  | Clientes Churned | xxx | wedo_status = churned |
  | Plano Starter | xxx | wedo_plan = starter |
  | Plano Professional | xxx | wedo_plan = professional |
  | Plano Enterprise | xxx | wedo_plan = enterprise |
  
  6. INTEGRAÇÃO STRIPE
  ─────────────────────────────────────────────────────────────────
  
  Status: Conectado via App nativo
  Sync: Invoices, Subscriptions, Customers
  
  ═══════════════════════════════════════════════════════════════
  ```

Critérios de Aceitação:
  - [ ] Documento criado
  - [ ] Todos os IDs preenchidos
  - [ ] Entregue ao time de devs
```

---

## WORKOS - Configuração de SSO/SCIM (7 cards)

---

### CARD GST-WOS-001: Verificar Conta Existente

```yaml
Titulo: [GESTOR] Verificar Configuração Atual do WorkOS
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Crítica
Ferramenta: WorkOS
Sequência: 1 de 7

Descrição: |
  Verificar a configuração atual do WorkOS já existente
  e garantir que está pronto para a integração.

Objetivo: |
  Confirmar que as credenciais existentes funcionam
  e documentar a configuração atual.

Contexto:
  Já existem os seguintes secrets configurados:
    - WORKOS_API_KEY
    - WORKOS_CLIENT_ID
    - WORKOS_WEBHOOK_SECRET

Passo a Passo:
  1. Acessar https://dashboard.workos.com
  2. Fazer login com conta configurada
  3. Verificar configurações atuais:
     
     Settings → API Keys:
       - Confirmar que WORKOS_API_KEY está ativo
       - Verificar permissões do API Key
     
     Settings → Redirect URIs:
       - Listar URIs configurados
       - Adicionar novos se necessário
     
     Settings → Webhooks:
       - Confirmar endpoint configurado
       - Verificar eventos habilitados
  
  4. Documentar configuração atual

Entregáveis para Devs:
  STATUS ATUAL:
    WORKOS_API_KEY: (existente) ✓
    WORKOS_CLIENT_ID: (existente) ✓
    WORKOS_WEBHOOK_SECRET: (existente) ✓
  
  Redirect URIs configurados:
    - [listar URIs atuais]
  
  Webhook endpoint:
    - [URL atual]
  
  Eventos habilitados:
    - [listar eventos]

Critérios de Aceitação:
  - [ ] Conta acessada com sucesso
  - [ ] API Key ativo
  - [ ] Configuração documentada
```

---

### CARD GST-WOS-002: Configurar Redirect URIs

```yaml
Titulo: [GESTOR] Configurar Redirect URIs no WorkOS
Tipo: Configuração SaaS
Tempo: 10 minutos
Prioridade: Crítica
Ferramenta: WorkOS
Sequência: 2 de 7
Dependências: GST-WOS-001

Descrição: |
  Configurar os Redirect URIs para os ambientes de
  desenvolvimento, staging e produção.

Objetivo: |
  Permitir que o fluxo de SSO redirecione corretamente
  após autenticação.

Passo a Passo:
  1. Acessar WorkOS Dashboard → Configuration
  2. Na seção "Redirect URIs", adicionar:

URIs a Configurar:

  PRODUÇÃO:
    https://app.wedotalent.com/auth/callback
    https://api.wedotalent.com/api/v1/auth/callback
  
  STAGING:
    https://staging.wedotalent.com/auth/callback
    https://staging-api.wedotalent.com/api/v1/auth/callback
  
  DESENVOLVIMENTO:
    http://localhost:3000/auth/callback
    http://localhost:5000/auth/callback
    https://*.replit.dev/auth/callback

  3. Salvar configurações

Entregáveis para Devs:
  Redirect URIs configurados:
    Produção:
      - https://app.wedotalent.com/auth/callback
      - https://api.wedotalent.com/api/v1/auth/callback
    
    Staging:
      - https://staging.wedotalent.com/auth/callback
    
    Dev:
      - http://localhost:3000/auth/callback
      - http://localhost:5000/auth/callback
      - https://*.replit.dev/auth/callback

Critérios de Aceitação:
  - [ ] URIs de produção configurados
  - [ ] URIs de staging configurados
  - [ ] URIs de desenvolvimento configurados
```

---

### CARD GST-WOS-003: Verificar Webhook Endpoint

```yaml
Titulo: [GESTOR] Verificar Configuração de Webhooks
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Crítica
Ferramenta: WorkOS
Sequência: 3 de 7
Dependências: GST-WOS-001

Descrição: |
  Verificar e atualizar a configuração de webhooks
  para receber eventos de SSO e SCIM.

Objetivo: |
  Garantir que o backend receberá notificações de
  conexões SSO, sync de diretório, etc.

Referência: WEDOTALENT_INTEGRACOES_COMPLETO.md - FASE 3, Passo 3.3

Passo a Passo:
  1. Acessar WorkOS Dashboard → Webhooks
  2. Verificar endpoint configurado
  3. Se não configurado ou diferente:
     - Clicar "Add endpoint"
     - URL: https://api.wedotalent.com/api/v1/webhooks/workos
  
  4. Verificar eventos habilitados:

╔══════════════════════════════════════════════════════════════════════════════╗
║                    MAPEAMENTO EVENTOS WORKOS → AÇÕES (14)                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Evento WorkOS               │ Ação Backend                │ Ação HubSpot    ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ connection.activated        │ Ativar SSO para org         │ wedo_sso_enabled║
║                             │                             │ = true          ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ connection.deactivated      │ Desativar SSO para org      │ wedo_sso_enabled║
║                             │                             │ = false         ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ connection.deleted          │ Remover config SSO          │ -               ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.activated             │ Ativar SCIM sync            │ Log nota        ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.deactivated           │ Desativar SCIM sync         │ Log nota        ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.user.created          │ Criar usuário no WeDo       │ Criar Contact   ║
║                             │                             │ + wedo_scim=true║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.user.updated          │ Atualizar usuário           │ Update Contact  ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.user.deleted          │ Desativar usuário           │ Update Contact  ║
║                             │                             │ status=inactive ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.group.created         │ Criar grupo/role            │ -               ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.group.updated         │ Atualizar grupo             │ -               ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ dsync.group.deleted         │ Remover grupo               │ -               ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ user.created                │ Login inicial (SSO)         │ wedo_last_login ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ user.updated                │ Atualizar profile           │ Update Contact  ║
╠═════════════════════════════╪═════════════════════════════╪═════════════════╣
║ organization.updated        │ Sync metadata org           │ Update Company  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Eventos a Habilitar (14 total):

  SSO EVENTS (3):
    - [x] connection.activated
    - [x] connection.deactivated
    - [x] connection.deleted
  
  USER EVENTS (2):
    - [x] user.created
    - [x] user.updated
  
  DSYNC EVENTS - Directory Sync / SCIM (8):
    - [x] dsync.activated
    - [x] dsync.deactivated
    - [x] dsync.user.created
    - [x] dsync.user.updated
    - [x] dsync.user.deleted
    - [x] dsync.group.created
    - [x] dsync.group.updated
    - [x] dsync.group.deleted
  
  ORGANIZATION EVENTS (1):
    - [x] organization.updated

  5. Copiar/verificar Webhook Secret

Fluxo de Dados SCIM:
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  IdP Cliente        WorkOS           Backend         HubSpot   │
  │  (Okta/Azure)                                                   │
  │                                                                 │
  │      │                 │                 │              │       │
  │      │ SCIM Push       │                 │              │       │
  │      │─────────────────►                 │              │       │
  │      │                 │ dsync.user.*    │              │       │
  │      │                 │─────────────────►              │       │
  │      │                 │                 │ Create User  │       │
  │      │                 │                 │─────────────►│       │
  │      │                 │                 │              │       │
  │      │                 │                 │ Update       │       │
  │      │                 │                 │ wedo_users   │       │
  │      │                 │                 │ _count       │       │
  │      │                 │                 │─────────────►│       │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘

Entregáveis para Devs:
  WORKOS_WEBHOOK_SECRET: (já existe nos secrets)
  
  Webhook endpoint:
    URL: https://api.wedotalent.com/api/v1/webhooks/workos
    Método: POST
    Content-Type: application/json
  
  Eventos habilitados (14 total):
    SSO: connection.activated/deactivated/deleted
    Users: user.created/updated
    SCIM: dsync.activated/deactivated
          dsync.user.created/updated/deleted
          dsync.group.created/updated/deleted
    Org: organization.updated
  
  Handler Actions:
    | Event Type            | Backend Action                  |
    |-----------------------|---------------------------------|
    | dsync.user.created    | Create User + Sync HubSpot      |
    | dsync.user.deleted    | Soft-delete + Update HubSpot    |
    | connection.activated  | Update Client.sso_enabled=true  |
    | organization.updated  | Sync org metadata               |

Critérios de Aceitação:
  - [ ] Endpoint verificado/configurado
  - [ ] 14 eventos habilitados
  - [ ] Webhook secret documentado
  - [ ] Mapeamento evento→ação documentado para devs
```

---

### CARD GST-WOS-004: Criar Organization de Teste

```yaml
Titulo: [GESTOR] Criar Organization de Teste
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: WorkOS
Sequência: 4 de 7
Dependências: GST-WOS-001

Descrição: |
  Criar uma Organization de teste no WorkOS para que
  os devs possam testar o fluxo de SSO.

Objetivo: |
  Ter uma org de teste para desenvolvimento e QA
  sem afetar dados de produção.

Passo a Passo:
  1. Acessar WorkOS Dashboard → Organizations
  2. Clicar "Create organization"
  
  3. Configurar:
     Name: WeDo Talent - Teste
     Domain(s): teste.wedotalent.com (ou deixar vazio)
     Allow profiles outside organization: Yes (para teste)
  
  4. Clicar "Create"
  5. Copiar Organization ID (org_xxx)
  
  6. (Opcional) Configurar SSO de teste:
     - Em "SSO", clicar "Configure"
     - Selecionar "WorkOS Test IdP" para testes rápidos
     - Ou configurar com Google Workspace, Okta, etc.

Entregáveis para Devs:
  TEST_ORGANIZATION:
    org_id: org_xxx
    name: WeDo Talent - Teste
    sso_connection_id: conn_xxx (se configurado)

Critérios de Aceitação:
  - [ ] Organization criada
  - [ ] Org ID documentado
  - [ ] (Opcional) SSO de teste configurado
```

---

### CARD GST-WOS-005: Configurar SSO Connection de Teste

```yaml
Titulo: [GESTOR] Configurar SSO Connection de Teste
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Média
Ferramenta: WorkOS
Sequência: 5 de 7
Dependências: GST-WOS-004

Descrição: |
  Configurar uma conexão SSO de teste para validar
  o fluxo de autenticação end-to-end.

Objetivo: |
  Permitir que devs testem login SSO sem precisar
  de um IdP de cliente real.

Opções de SSO de Teste:

  OPÇÃO A: WorkOS Test IdP (mais simples)
    1. Na Organization de teste → SSO → Configure
    2. Selecionar "WorkOS Test IdP"
    3. Pronto! Pode logar com qualquer email
  
  OPÇÃO B: Google Workspace (se disponível)
    1. Na Organization de teste → SSO → Configure
    2. Selecionar "Google Workspace"
    3. Seguir wizard de configuração
    4. Requer acesso admin ao Google Workspace
  
  OPÇÃO C: Okta Developer (gratuito) - APENAS PARA TESTES INTERNOS
    Nota: Esta opção é para a WeDo testar SSO internamente.
    Em produção, CLIENTES configuram no IdP DELES via WorkOS.
    1. Criar conta em developer.okta.com
    2. Na Organization de teste → SSO → Configure
    3. Selecionar "Okta"
    4. Seguir wizard, copiar metadata do Okta
  
  OPÇÃO D: OneLogin Sandbox (gratuito) - APENAS PARA TESTES INTERNOS
    1. Criar conta sandbox em onelogin.com
    2. Na Organization de teste → SSO → Configure
    3. Selecionar "OneLogin"
    4. Seguir wizard

Passo a Passo (WorkOS Test IdP - Recomendado):
  1. Acessar Organization de teste
  2. Ir em SSO → Configure
  3. Selecionar "WorkOS Test IdP"
  4. Clicar "Enable Test IdP"
  5. Copiar Connection ID

Entregáveis para Devs:
  TEST_SSO_CONNECTION:
    connection_id: conn_xxx
    type: WorkOS Test IdP (ou outro)
    org_id: org_xxx
  
  Como testar:
    1. Iniciar fluxo SSO com org_id de teste
    2. WorkOS Test IdP aceita qualquer email
    3. Usuário é criado/retornado

Critérios de Aceitação:
  - [ ] Connection SSO criada
  - [ ] Tipo de IdP documentado
  - [ ] Connection ID documentado
  - [ ] Instruções de teste claras
```

---

### CARD GST-WOS-006: Configurar SCIM de Teste (Opcional)

```yaml
Titulo: [GESTOR] Configurar Directory Sync / SCIM de Teste
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Baixa
Ferramenta: WorkOS
Sequência: 6 de 7
Dependências: GST-WOS-004
Opcional: Sim - fazer se precisar testar SCIM

Descrição: |
  Configurar Directory Sync (SCIM) de teste para
  sincronização automática de usuários.

Objetivo: |
  Permitir que devs testem provisionamento automático
  de usuários via SCIM.

Nota: SCIM é mais complexo que SSO. Só configurar
      se for realmente necessário para o MVP.

Opções de Directory de Teste:

  OPÇÃO A: Okta SCIM (recomendado para testes)
    - Criar app SCIM no Okta Developer
    - Conectar ao WorkOS
  
  OPÇÃO B: Azure AD SCIM
    - Requer tenant Azure AD de teste
    - Mais complexo de configurar
  
  OPÇÃO C: Google Workspace
    - Usar Directory da própria empresa

Se decidir configurar:
  1. Acessar Organization de teste
  2. Ir em Directory Sync → Configure
  3. Selecionar provider (Okta, Azure, etc.)
  4. Seguir wizard de configuração
  5. Copiar Directory ID

Entregáveis para Devs:
  TEST_DIRECTORY_SYNC:
    directory_id: dir_xxx (se configurado)
    type: Okta SCIM (ou outro)
    status: Opcional para MVP

Critérios de Aceitação:
  - [ ] (Se aplicável) Directory configurado
  - [ ] (Se aplicável) Directory ID documentado
  - OU
  - [ ] Decidido que SCIM não é necessário para MVP
```

---

### CARD GST-WOS-007: Documentar Configuração WorkOS

```yaml
Titulo: [GESTOR] Criar Documento de Handoff WorkOS
Tipo: Documentação
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: WorkOS
Sequência: 7 de 7
Dependências: GST-WOS-001 a GST-WOS-006

Descrição: |
  Consolidar todas as informações do WorkOS em um documento
  de handoff para o time de desenvolvimento.

Template do Documento:

  ```
  ═══════════════════════════════════════════════════════════════
  HANDOFF WORKOS - WEDO TALENT
  Data: [DATA]
  Responsável: [NOME]
  ═══════════════════════════════════════════════════════════════
  
  1. CREDENCIAIS (já nos secrets)
  ─────────────────────────────────────────────────────────────────
  
  WORKOS_API_KEY: sk_xxx (existente)
  WORKOS_CLIENT_ID: client_xxx (existente)
  WORKOS_WEBHOOK_SECRET: xxx (existente)
  
  2. REDIRECT URIs
  ─────────────────────────────────────────────────────────────────
  
  Produção:
    - https://app.wedotalent.com/auth/callback
    - https://api.wedotalent.com/api/v1/auth/callback
  
  Staging:
    - https://staging.wedotalent.com/auth/callback
  
  Desenvolvimento:
    - http://localhost:3000/auth/callback
    - http://localhost:5000/auth/callback
    - https://*.replit.dev/auth/callback
  
  3. WEBHOOK ENDPOINT
  ─────────────────────────────────────────────────────────────────
  
  URL: https://api.wedotalent.com/api/v1/webhooks/workos
  
  Eventos habilitados:
    - connection.activated/deactivated/deleted
    - user.created/updated/deleted
    - dsync.activated/deactivated
    - dsync.user.created/updated/deleted
    - dsync.group.created/updated/deleted
    - organization.updated
  
  4. ORGANIZATION DE TESTE
  ─────────────────────────────────────────────────────────────────
  
  Name: WeDo Talent - Teste
  Org ID: org_xxx
  SSO Connection ID: conn_xxx
  SSO Type: WorkOS Test IdP
  
  Como testar SSO:
    1. Chamar API para obter SSO URL com org_id de teste
    2. Usar qualquer email no Test IdP
    3. Verificar callback com user data
  
  5. DIRECTORY SYNC (SCIM) - OPCIONAL
  ─────────────────────────────────────────────────────────────────
  
  Status: [Configurado / Não necessário para MVP]
  Directory ID: dir_xxx (se configurado)
  
  ═══════════════════════════════════════════════════════════════
  ```

Critérios de Aceitação:
  - [ ] Documento criado
  - [ ] Todas as informações preenchidas
  - [ ] Entregue ao time de devs
```

---

## PROFITWELL - Configuração de Métricas (4 cards)

---

### CARD GST-PWL-001: Criar Conta ProfitWell

```yaml
Titulo: [GESTOR] Criar Conta no ProfitWell
Tipo: Configuração SaaS
Tempo: 10 minutos
Prioridade: Média
Ferramenta: ProfitWell (Paddle)
Sequência: 1 de 4

Descrição: |
  Criar conta gratuita no ProfitWell para métricas SaaS
  (MRR, Churn, LTV, etc.).

Objetivo: |
  Ter visibilidade de métricas SaaS automaticamente
  calculadas a partir dos dados do Stripe.

Nota: ProfitWell é gratuito e não requer desenvolvimento.
      Apenas conecta ao Stripe e exibe métricas.

Passo a Passo:
  1. Acessar https://www.profitwell.com (ou paddle.com/profitwell)
  2. Clicar "Get Started Free"
  3. Criar conta com email corporativo
  4. Verificar email
  5. Acessar dashboard

Entregáveis para Devs:
  Status: Conta criada
  Nota: Não requer integração de código.
        Métricas são calculadas automaticamente
        após conectar ao Stripe.

Critérios de Aceitação:
  - [ ] Conta criada
  - [ ] Email verificado
  - [ ] Dashboard acessível
```

---

### CARD GST-PWL-002: Conectar ao Stripe

```yaml
Titulo: [GESTOR] Conectar ProfitWell ao Stripe
Tipo: Configuração SaaS
Tempo: 5 minutos
Prioridade: Média
Ferramenta: ProfitWell + Stripe
Sequência: 2 de 4
Dependências: GST-PWL-001, GST-STR-001

Descrição: |
  Conectar o ProfitWell ao Stripe para importar
  dados de subscriptions automaticamente.

Objetivo: |
  Ter métricas de MRR, Churn, LTV calculadas
  automaticamente sem desenvolvimento.

Passo a Passo:
  1. Acessar ProfitWell Dashboard
  2. Ir em Settings → Integrations
  3. Clicar "Connect Stripe"
  4. Autorizar acesso (login no Stripe)
  5. Selecionar conta Stripe correta
  6. Aguardar sync inicial (pode levar algumas horas)

Entregáveis para Devs:
  Status: Conectado
  Sync: Automático (não requer código)
  
  Métricas disponíveis:
    - MRR (Monthly Recurring Revenue)
    - ARR (Annual Recurring Revenue)
    - Churn Rate
    - LTV (Lifetime Value)
    - New MRR / Expansion / Contraction / Churn
    - Customer Count

Critérios de Aceitação:
  - [ ] Stripe conectado
  - [ ] Sync inicial completado
  - [ ] Métricas aparecendo no dashboard
```

---

### CARD GST-PWL-003: Configurar Segmentos

```yaml
Titulo: [GESTOR] Criar Segmentos no ProfitWell
Tipo: Configuração SaaS
Tempo: 20 minutos
Prioridade: Baixa
Ferramenta: ProfitWell
Sequência: 3 de 4
Dependências: GST-PWL-002

Descrição: |
  Criar segmentos no ProfitWell para analisar
  métricas por plano, região, etc.

Objetivo: |
  Ter visibilidade de métricas segmentadas
  (ex: MRR por plano, churn por tamanho).

Passo a Passo:
  1. Acessar ProfitWell Dashboard
  2. Ir em Segments
  3. Criar segmentos:

Segmentos a Criar:

  SEGMENTO 1: Por Plano
    - Starter (filtrar por price_id do Starter)
    - Professional (filtrar por price_id do Professional)
    - Enterprise (filtrar por price_id do Enterprise)
  
  SEGMENTO 2: Por Billing Cycle
    - Monthly (subscriptions mensais)
    - Yearly (subscriptions anuais)
  
  SEGMENTO 3: Por Tamanho (se metadata disponível)
    - SMB (pequenas empresas)
    - Mid-Market (médias)
    - Enterprise (grandes)

Entregáveis para Devs:
  Segmentos são apenas para visualização.
  Não requerem integração de código.
  
  Nota: Para segmentos avançados, pode ser
        necessário adicionar metadata nas
        subscriptions do Stripe.

Critérios de Aceitação:
  - [ ] Segmentos por plano criados
  - [ ] Segmentos por billing cycle criados
```

---

### CARD GST-PWL-004: Documentar Configuração ProfitWell

```yaml
Titulo: [GESTOR] Criar Documento de Handoff ProfitWell
Tipo: Documentação
Tempo: 10 minutos
Prioridade: Baixa
Ferramenta: ProfitWell
Sequência: 4 de 4
Dependências: GST-PWL-001 a GST-PWL-003

Descrição: |
  Documentar a configuração do ProfitWell para referência.

Template do Documento:

  ```
  ═══════════════════════════════════════════════════════════════
  HANDOFF PROFITWELL - WEDO TALENT
  Data: [DATA]
  Responsável: [NOME]
  ═══════════════════════════════════════════════════════════════
  
  1. STATUS
  ─────────────────────────────────────────────────────────────────
  
  Conta: Ativa
  Conectado ao Stripe: Sim
  Custo: Gratuito
  
  2. MÉTRICAS DISPONÍVEIS
  ─────────────────────────────────────────────────────────────────
  
  Automáticas (sem código):
    - MRR / ARR
    - Churn Rate
    - LTV
    - Customer Count
    - New / Expansion / Contraction / Churn MRR
  
  3. SEGMENTOS
  ─────────────────────────────────────────────────────────────────
  
  - Por Plano: Starter, Professional, Enterprise
  - Por Billing: Monthly, Yearly
  
  4. INTEGRAÇÃO COM CÓDIGO
  ─────────────────────────────────────────────────────────────────
  
  PROFITWELL_API_KEY: xxx (opcional)
  
  Uso: Apenas se quiser embedar métricas na UI
       ou criar automações. Não é necessário para
       visualização básica no dashboard ProfitWell.
  
  ═══════════════════════════════════════════════════════════════
  ```

Critérios de Aceitação:
  - [ ] Documento criado
  - [ ] Status documentado
```

---

## PRIVACY TOOLS - Configuração de LGPD (6 cards)

---

### CARD GST-PVT-001: Criar Conta Privacy Tools

```yaml
Titulo: [GESTOR] Criar Conta no Privacy Tools
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 1 de 6

Descrição: |
  Criar conta no Privacy Tools para gestão de LGPD
  e portal do titular de dados.

Objetivo: |
  Ter uma plataforma de compliance LGPD que permite
  aos candidatos exercerem seus direitos de privacidade.

Passo a Passo:
  1. Acessar https://privacytools.com.br
  2. Clicar "Criar Conta" ou "Solicitar Demo"
  3. Preencher dados da empresa:
     - Razão Social: WeDo Talent
     - CNPJ
     - Email do DPO/Responsável
  4. Aguardar aprovação/ativação
  5. Acessar dashboard

Entregáveis para Devs:
  Status: Conta criada
  URL Dashboard: [URL do Privacy Tools]

Critérios de Aceitação:
  - [ ] Conta criada
  - [ ] Acesso ao dashboard
```

---

### CARD GST-PVT-002: Configurar Dados da Empresa

```yaml
Titulo: [GESTOR] Configurar Dados da Empresa
Tipo: Configuração SaaS
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 2 de 6
Dependências: GST-PVT-001

Descrição: |
  Configurar os dados da empresa no Privacy Tools
  para exibição no Portal do Titular.

Passo a Passo:
  1. Acessar Dashboard → Configurações
  2. Preencher dados da empresa:
     - Nome: WeDo Talent
     - CNPJ: xxx
     - Endereço: xxx
     - DPO/Encarregado: Nome e email
  3. Configurar política de privacidade:
     - URL: https://wedotalent.com/privacidade
  4. Configurar termos de uso:
     - URL: https://wedotalent.com/termos

Entregáveis para Devs:
  Dados configurados no Privacy Tools.
  Portal exibirá informações corretas.

Critérios de Aceitação:
  - [ ] Dados da empresa preenchidos
  - [ ] DPO configurado
  - [ ] Políticas linkadas
```

---

### CARD GST-PVT-003: Configurar Portal do Titular

```yaml
Titulo: [GESTOR] Configurar Portal do Titular LGPD
Tipo: Configuração SaaS
Tempo: 30 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 3 de 6
Dependências: GST-PVT-002

Descrição: |
  Configurar o Portal do Titular de Dados onde
  candidatos podem exercer seus direitos LGPD.

Objetivo: |
  Permitir que candidatos solicitem acesso,
  correção, exclusão ou portabilidade de dados.

Passo a Passo:
  1. Acessar Dashboard → Portal do Titular
  2. Configurar tipos de solicitação:
     
     SOLICITAÇÃO 1: Acesso aos Dados
       - Descrição: Solicitar cópia de todos os dados pessoais
       - Prazo: 15 dias
       - Status: Habilitado
     
     SOLICITAÇÃO 2: Correção de Dados
       - Descrição: Solicitar correção de dados incorretos
       - Prazo: 15 dias
       - Status: Habilitado
     
     SOLICITAÇÃO 3: Exclusão de Dados
       - Descrição: Solicitar eliminação dos dados pessoais
       - Prazo: 15 dias
       - Status: Habilitado
     
     SOLICITAÇÃO 4: Portabilidade
       - Descrição: Solicitar dados em formato estruturado
       - Prazo: 15 dias
       - Status: Habilitado
     
     SOLICITAÇÃO 5: Revogação de Consentimento
       - Descrição: Revogar consentimento para processamento
       - Prazo: 5 dias
       - Status: Habilitado
     
     SOLICITAÇÃO 6: Oposição ao Tratamento
       - Descrição: Opor-se a decisões automatizadas
       - Prazo: 15 dias
       - Status: Habilitado
  
  3. Configurar campos do formulário:
     - Nome completo (obrigatório)
     - Email (obrigatório)
     - CPF (obrigatório para verificação)
     - Tipo de solicitação
     - Descrição adicional

Entregáveis para Devs:
  Portal URL: https://privacidade.wedotalent.com
              ou embed no site
  
  Tipos de solicitação:
    - access (acesso)
    - correction (correção)
    - deletion (exclusão)
    - portability (portabilidade)
    - consent_revocation (revogação)
    - opposition (oposição)

Critérios de Aceitação:
  - [ ] 6 tipos de solicitação configurados
  - [ ] Formulário funcional
  - [ ] Portal acessível
```

---

### CARD GST-PVT-004: Configurar Webhook

```yaml
Titulo: [GESTOR] Configurar Webhook do Privacy Tools
Tipo: Configuração SaaS
Tempo: 10 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 4 de 6
Dependências: GST-PVT-001

Descrição: |
  Configurar webhook para que o backend seja notificado
  quando novas solicitações LGPD forem criadas.

Objetivo: |
  Permitir que o backend processe solicitações
  automaticamente (ex: exportar dados do candidato).

Passo a Passo:
  1. Acessar Dashboard → Integrações → Webhooks
  2. Clicar "Adicionar Webhook"
  3. Configurar:
     
     URL: https://api.wedotalent.com/api/v1/webhooks/privacytools
     
     Eventos:
       - [x] request.created (nova solicitação)
       - [x] request.updated (status alterado)
       - [x] request.completed (solicitação concluída)
     
     Formato: JSON
     
  4. Salvar e copiar Webhook Secret

Entregáveis para Devs:
  PRIVACYTOOLS_WEBHOOK_SECRET: xxx
  
  Webhook endpoint:
    URL: https://api.wedotalent.com/api/v1/webhooks/privacytools
  
  Eventos:
    - request.created
    - request.updated
    - request.completed
  
  Payload exemplo:
    {
      "event": "request.created",
      "request_id": "xxx",
      "type": "access",
      "requester_email": "candidato@email.com",
      "requester_name": "Nome do Candidato",
      "created_at": "2026-01-14T10:00:00Z"
    }

Critérios de Aceitação:
  - [ ] Webhook configurado
  - [ ] Eventos selecionados
  - [ ] Secret documentado
```

---

### CARD GST-PVT-005: Gerar API Key

```yaml
Titulo: [GESTOR] Gerar API Key do Privacy Tools
Tipo: Configuração SaaS
Tempo: 5 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 5 de 6
Dependências: GST-PVT-001

Descrição: |
  Gerar API Key para que o backend possa atualizar
  status de solicitações e exportar dados.

Objetivo: |
  Permitir que o backend responda automaticamente
  a solicitações LGPD.

Passo a Passo:
  1. Acessar Dashboard → Integrações → API
  2. Clicar "Gerar Nova Chave"
  3. Nome: WeDo Talent Backend
  4. Permissões:
     - [x] Listar solicitações
     - [x] Atualizar status
     - [x] Anexar documentos
     - [x] Marcar como concluída
  5. Copiar API Key

Entregáveis para Devs:
  PRIVACYTOOLS_API_KEY: xxx
  
  Endpoints da API:
    - GET /requests - Listar solicitações
    - GET /requests/{id} - Detalhes de uma solicitação
    - PATCH /requests/{id} - Atualizar status
    - POST /requests/{id}/attachments - Anexar arquivo
    - POST /requests/{id}/complete - Marcar concluída

Critérios de Aceitação:
  - [ ] API Key gerada
  - [ ] Permissões configuradas
  - [ ] Documentada para devs
```

---

### CARD GST-PVT-006: Documentar Configuração Privacy Tools

```yaml
Titulo: [GESTOR] Criar Documento de Handoff Privacy Tools
Tipo: Documentação
Tempo: 15 minutos
Prioridade: Alta
Ferramenta: Privacy Tools
Sequência: 6 de 6
Dependências: GST-PVT-001 a GST-PVT-005

Descrição: |
  Consolidar todas as informações do Privacy Tools
  em um documento de handoff.

Template do Documento:

  ```
  ═══════════════════════════════════════════════════════════════
  HANDOFF PRIVACY TOOLS - WEDO TALENT
  Data: [DATA]
  Responsável: [NOME]
  ═══════════════════════════════════════════════════════════════
  
  1. CREDENCIAIS
  ─────────────────────────────────────────────────────────────────
  
  PRIVACYTOOLS_API_KEY: xxx
  PRIVACYTOOLS_WEBHOOK_SECRET: xxx
  
  2. PORTAL DO TITULAR
  ─────────────────────────────────────────────────────────────────
  
  URL: https://privacidade.wedotalent.com
       ou embed no website
  
  Tipos de solicitação:
    - access: Acesso aos dados
    - correction: Correção de dados
    - deletion: Exclusão de dados
    - portability: Portabilidade
    - consent_revocation: Revogação
    - opposition: Oposição
  
  3. WEBHOOK
  ─────────────────────────────────────────────────────────────────
  
  Endpoint: https://api.wedotalent.com/api/v1/webhooks/privacytools
  
  Eventos:
    - request.created
    - request.updated
    - request.completed
  
  4. FLUXO DE PROCESSAMENTO
  ─────────────────────────────────────────────────────────────────
  
  1. Candidato acessa Portal → cria solicitação
  2. Webhook notifica backend (request.created)
  3. Backend processa (busca dados, prepara export)
  4. Backend atualiza status via API
  5. Backend anexa documentos (se aplicável)
  6. Backend marca como concluída
  7. Privacy Tools notifica candidato
  
  ═══════════════════════════════════════════════════════════════
  ```

Critérios de Aceitação:
  - [ ] Documento criado
  - [ ] Todas as credenciais documentadas
  - [ ] Entregue ao time de devs
```

---

# PARTE 2: CARDS DEVS - DESENVOLVIMENTO RAILS

> **Responsável:** Time de Desenvolvimento  
> **Stack:** Ruby on Rails + PostgreSQL + Sidekiq  
> **Prazo Total:** 4-5 semanas  
> **Pré-requisito:** Handoff do Gestor completo

---

## SEMANA 1: FUNDAÇÃO (5 cards)

---

### CARD DEV-S1-001: Setup do Projeto Rails

```yaml
Titulo: [DEVS] Setup Inicial do Projeto Rails
Tipo: Infraestrutura
Sprint: Semana 1
Pontos: 5
Prioridade: Crítica
Sequência: 1 de 5

Descrição: |
  Criar o projeto Rails base para o backend do WeDo Talent Admin
  com todas as gems e configurações iniciais.

Objetivo: |
  Ter um projeto Rails funcional com todas as dependências
  necessárias para as integrações.

Requisitos Técnicos:
  Rails:
    - Ruby 3.2+
    - Rails 7.1+
    - API mode (--api)
  
  Database:
    - PostgreSQL 15+
    - Connection pool: 10
  
  Background Jobs:
    - Sidekiq
    - Redis para queue

Comandos de Setup:
  ```bash
  rails new wedotalent_admin --api --database=postgresql
  cd wedotalent_admin
  
  # Adicionar ao Gemfile
  gem 'pg'
  gem 'sidekiq'
  gem 'redis'
  gem 'stripe'
  gem 'workos'
  gem 'hubspot-api-client'
  gem 'jwt'
  gem 'rack-cors'
  gem 'dotenv-rails'
  gem 'acts_as_tenant'
  
  bundle install
  ```

Estrutura de Pastas:
  ```
  app/
  ├── controllers/
  │   └── api/
  │       └── v1/
  │           ├── webhooks/
  │           ├── tenants_controller.rb
  │           ├── auth_controller.rb
  │           └── billing_controller.rb
  ├── models/
  ├── services/
  │   ├── stripe/
  │   ├── workos/
  │   ├── hubspot/
  │   └── privacy_tools/
  ├── jobs/
  └── serializers/
  ```

DoD (Definition of Done):
  - [ ] Projeto Rails criado
  - [ ] Gems instaladas
  - [ ] Database configurado
  - [ ] Sidekiq funcionando
  - [ ] CORS configurado
  - [ ] Estrutura de pastas criada

Critérios de Aceitação:
  - [ ] rails server roda sem erros
  - [ ] sidekiq inicia corretamente
  - [ ] conexão com PostgreSQL OK
```

---

### CARD DEV-S1-002: Configurar Multi-tenant

```yaml
Titulo: [DEVS] Implementar Multi-tenant Isolation
Tipo: Infraestrutura
Sprint: Semana 1
Pontos: 8
Prioridade: Crítica
Sequência: 2 de 5
Dependências: DEV-S1-001

Descrição: |
  Implementar isolamento multi-tenant para garantir que
  dados de cada cliente fiquem separados.

Objetivo: |
  Cada tenant (cliente) só tem acesso aos seus próprios
  dados, garantindo segurança e isolamento.

Requisitos Técnicos:
  Gem: acts_as_tenant
  
  Estratégia: Tenant por subdomain ou header
  
  Configuração:
    ```ruby
    # config/initializers/acts_as_tenant.rb
    ActsAsTenant.configure do |config|
      config.require_tenant = true
    end
    
    # app/controllers/application_controller.rb
    class ApplicationController < ActionController::API
      set_current_tenant_through_filter
      before_action :set_tenant
      
      private
      
      def set_tenant
        # Por header (API)
        tenant = Tenant.find_by!(subdomain: request.headers['X-Tenant-ID'])
        set_current_tenant(tenant)
      rescue ActiveRecord::RecordNotFound
        render json: { error: 'Tenant not found' }, status: :not_found
      end
    end
    ```
  
  Models com Tenant:
    ```ruby
    class User < ApplicationRecord
      acts_as_tenant :tenant
    end
    
    class Subscription < ApplicationRecord
      acts_as_tenant :tenant
    end
    ```

Testes a Criar:
  - Tenant A não acessa dados do Tenant B
  - Queries são automaticamente filtradas
  - Requests sem tenant retornam erro

DoD (Definition of Done):
  - [ ] acts_as_tenant configurado
  - [ ] ApplicationController com set_tenant
  - [ ] Testes de isolamento passando

Critérios de Aceitação:
  - [ ] Dados isolados por tenant
  - [ ] Requests sem tenant bloqueados
```

---

### CARD DEV-S1-003: Criar Migrations do Schema

```yaml
Titulo: [DEVS] Criar Migrations do Banco de Dados
Tipo: Backend
Sprint: Semana 1
Pontos: 5
Prioridade: Crítica
Sequência: 3 de 5
Dependências: DEV-S1-001

Descrição: |
  Criar todas as migrations para as tabelas necessárias
  conforme definido no Apêndice I.

Objetivo: |
  Ter o schema do banco de dados pronto para receber
  dados das integrações.

Migrations a Criar:

  1. create_tenants
  2. create_users
  3. create_subscriptions
  4. create_invoices
  5. create_sso_connections
  6. create_directory_syncs
  7. create_audit_logs
  8. create_webhook_events
  9. create_lgpd_requests

Schema (resumo):
  ```ruby
  # Ver Apêndice I para schema completo
  
  create_table :tenants do |t|
    t.string :name, null: false
    t.string :subdomain, null: false, index: { unique: true }
    t.string :status, default: 'active'
    t.string :plan
    t.string :stripe_customer_id, index: true
    t.string :hubspot_company_id, index: true
    t.string :workos_org_id, index: true
    t.timestamps
  end
  
  create_table :users do |t|
    t.references :tenant, null: false, foreign_key: true
    t.string :email, null: false
    t.string :workos_user_id, index: true
    t.timestamps
    t.index [:tenant_id, :email], unique: true
  end
  
  # ... restante conforme Apêndice I
  ```

Comandos:
  ```bash
  rails db:migrate
  ```

DoD (Definition of Done):
  - [ ] 9 migrations criadas
  - [ ] Migrations executam sem erro
  - [ ] Índices criados
  - [ ] Foreign keys configuradas

Critérios de Aceitação:
  - [ ] rails db:migrate OK
  - [ ] rails db:rollback OK
  - [ ] Schema.rb atualizado
```

---

### CARD DEV-S1-004: Implementar TenantService

```yaml
Titulo: [DEVS] Implementar TenantService
Tipo: Backend
Sprint: Semana 1
Pontos: 5
Prioridade: Alta
Sequência: 4 de 5
Dependências: DEV-S1-003

Descrição: |
  Criar service para gerenciamento de tenants (CRUD)
  e operações administrativas.

Objetivo: |
  Centralizar lógica de negócio de tenants em um service
  reutilizável.

Implementação:
  ```ruby
  # app/services/tenant_service.rb
  class TenantService
    def self.create(params)
      tenant = Tenant.new(params)
      
      ActiveRecord::Base.transaction do
        tenant.save!
        
        # Criar no Stripe
        stripe_customer = Stripe::Customer.create(
          name: tenant.name,
          email: params[:admin_email],
          metadata: { tenant_id: tenant.id }
        )
        tenant.update!(stripe_customer_id: stripe_customer.id)
        
        # Sync para HubSpot (async)
        SyncTenantToHubSpotJob.perform_later(tenant.id)
      end
      
      tenant
    end
    
    def self.suspend(tenant)
      tenant.update!(status: 'suspended')
      # Pausar subscription no Stripe
      # Notificar no HubSpot
    end
    
    def self.reactivate(tenant)
      tenant.update!(status: 'active')
      # Reativar subscription
    end
    
    def self.usage_stats(tenant)
      {
        users_count: tenant.users.count,
        jobs_count: tenant.jobs.count,
        screenings_count: tenant.screenings.count
      }
    end
  end
  ```

Testes a Criar:
  - TenantService.create cria tenant + Stripe customer
  - TenantService.suspend atualiza status
  - TenantService.usage_stats retorna dados

DoD (Definition of Done):
  - [ ] TenantService implementado
  - [ ] Métodos create, suspend, reactivate, usage_stats
  - [ ] Testes unitários passando

Critérios de Aceitação:
  - [ ] CRUD de tenant funcional
  - [ ] Integração Stripe no create
```

---

### CARD DEV-S1-005: Configurar Sidekiq

```yaml
Titulo: [DEVS] Configurar Sidekiq para Background Jobs
Tipo: Infraestrutura
Sprint: Semana 1
Pontos: 3
Prioridade: Alta
Sequência: 5 de 5
Dependências: DEV-S1-001

Descrição: |
  Configurar Sidekiq com filas e workers para
  processamento de jobs em background.

Objetivo: |
  Processar webhooks, syncs e outras tarefas
  de forma assíncrona.

Configuração:
  ```ruby
  # config/sidekiq.yml
  :concurrency: 5
  :queues:
    - critical
    - webhooks
    - sync
    - default
    - low
  
  # config/initializers/sidekiq.rb
  Sidekiq.configure_server do |config|
    config.redis = { url: ENV['REDIS_URL'] }
  end
  
  Sidekiq.configure_client do |config|
    config.redis = { url: ENV['REDIS_URL'] }
  end
  ```

Filas:
  - critical: Webhooks de pagamento
  - webhooks: Outros webhooks
  - sync: Sincronização HubSpot, etc.
  - default: Jobs gerais
  - low: Cleanup, métricas

Jobs Base:
  ```ruby
  # app/jobs/application_job.rb
  class ApplicationJob < ActiveJob::Base
    queue_as :default
    
    retry_on StandardError, wait: :exponentially_longer, attempts: 3
    discard_on ActiveJob::DeserializationError
  end
  ```

DoD (Definition of Done):
  - [ ] Sidekiq configurado
  - [ ] Redis conectado
  - [ ] Filas definidas
  - [ ] Jobs base criados

Critérios de Aceitação:
  - [ ] sidekiq inicia sem erros
  - [ ] Jobs são enfileirados
  - [ ] Dashboard Sidekiq acessível
```

---

## SEMANA 2: AUTENTICAÇÃO - WorkOS (5 cards)

---

### CARD DEV-S2-001: Implementar WorkOSAuthService

```yaml
Titulo: [DEVS] Implementar WorkOSAuthService
Tipo: Backend
Sprint: Semana 2
Pontos: 8
Prioridade: Crítica
Sequência: 1 de 5
Dependências: Handoff GST-WOS

Descrição: |
  Implementar service para autenticação SSO via WorkOS
  com suporte a múltiplas organizações.

Objetivo: |
  Permitir login SSO para usuários enterprise com
  provedores como Okta, Azure AD, Google Workspace.

Credenciais Necessárias (do Handoff):
  - WORKOS_API_KEY
  - WORKOS_CLIENT_ID
  - Redirect URIs configurados

Implementação:
  ```ruby
  # app/services/work_os_auth_service.rb
  class WorkOSAuthService
    def initialize
      WorkOS.configure do |config|
        config.key = ENV['WORKOS_API_KEY']
      end
    end
    
    # Gerar URL de SSO
    def sso_url(organization_id:, redirect_uri:, state: nil)
      WorkOS::SSO.authorization_url(
        organization: organization_id,
        client_id: ENV['WORKOS_CLIENT_ID'],
        redirect_uri: redirect_uri,
        state: state
      )
    end
    
    # Processar callback
    def authenticate(code:)
      profile_and_token = WorkOS::SSO.profile_and_token(
        client_id: ENV['WORKOS_CLIENT_ID'],
        code: code
      )
      
      profile = profile_and_token.profile
      
      {
        workos_user_id: profile.id,
        email: profile.email,
        first_name: profile.first_name,
        last_name: profile.last_name,
        organization_id: profile.organization_id,
        connection_id: profile.connection_id,
        raw_attributes: profile.raw_attributes
      }
    end
    
    # Buscar ou criar usuário
    def find_or_create_user(profile_data)
      tenant = Tenant.find_by!(workos_org_id: profile_data[:organization_id])
      
      user = User.find_or_initialize_by(
        tenant: tenant,
        email: profile_data[:email]
      )
      
      user.update!(
        name: "#{profile_data[:first_name]} #{profile_data[:last_name]}",
        workos_user_id: profile_data[:workos_user_id],
        last_login_at: Time.current
      )
      
      user
    end
  end
  ```

DoD (Definition of Done):
  - [ ] WorkOSAuthService implementado
  - [ ] sso_url funcional
  - [ ] authenticate funcional
  - [ ] find_or_create_user funcional
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Gera URL de SSO válida
  - [ ] Processa callback corretamente
  - [ ] Cria/atualiza usuário
```

---

### CARD DEV-S2-002: Criar Endpoints de Auth

```yaml
Titulo: [DEVS] Criar Endpoints de Autenticação
Tipo: Backend
Sprint: Semana 2
Pontos: 5
Prioridade: Crítica
Sequência: 2 de 5
Dependências: DEV-S2-001

Descrição: |
  Criar endpoints da API para fluxo de SSO.

Objetivo: |
  Expor APIs para o frontend iniciar e completar
  o fluxo de autenticação SSO.

Endpoints:
  ```ruby
  # config/routes.rb
  namespace :api do
    namespace :v1 do
      namespace :auth do
        get :sso_url
        post :callback
        post :logout
      end
    end
  end
  ```

Controller:
  ```ruby
  # app/controllers/api/v1/auth_controller.rb
  class Api::V1::AuthController < ApplicationController
    skip_before_action :authenticate!, only: [:sso_url, :callback]
    
    # GET /api/v1/auth/sso_url
    def sso_url
      service = WorkOSAuthService.new
      
      url = service.sso_url(
        organization_id: params[:organization_id],
        redirect_uri: params[:redirect_uri],
        state: params[:state]
      )
      
      render json: { url: url }
    end
    
    # POST /api/v1/auth/callback
    def callback
      service = WorkOSAuthService.new
      
      profile = service.authenticate(code: params[:code])
      user = service.find_or_create_user(profile)
      
      # Gerar JWT
      token = JwtService.encode(user_id: user.id, tenant_id: user.tenant_id)
      
      render json: {
        token: token,
        user: UserSerializer.new(user)
      }
    end
    
    # POST /api/v1/auth/logout
    def logout
      # Invalidar token (se usando blacklist)
      render json: { message: 'Logged out' }
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Endpoints criados
  - [ ] JWT gerado no callback
  - [ ] Testes de integração

Critérios de Aceitação:
  - [ ] GET /sso_url retorna URL válida
  - [ ] POST /callback retorna JWT
```

---

### CARD DEV-S2-003: Implementar WorkOSWebhookService

```yaml
Titulo: [DEVS] Implementar WorkOSWebhookService
Tipo: Backend
Sprint: Semana 2
Pontos: 8
Prioridade: Alta
Sequência: 3 de 5
Dependências: Handoff GST-WOS

Descrição: |
  Implementar service para processar webhooks do WorkOS
  (SSO connections, SCIM sync).

Objetivo: |
  Receber e processar eventos de ativação de SSO,
  criação/atualização/deleção de usuários via SCIM.

Eventos a Processar:
  - connection.activated
  - connection.deactivated
  - user.created / updated / deleted
  - dsync.user.created / updated / deleted
  - dsync.group.created / updated / deleted

Implementação:
  ```ruby
  # app/services/work_os_webhook_service.rb
  class WorkOSWebhookService
    def initialize(payload, signature)
      @payload = payload
      @signature = signature
    end
    
    def verify_signature!
      WorkOS::Webhooks.verify_event(
        payload: @payload,
        sig_header: @signature,
        secret: ENV['WORKOS_WEBHOOK_SECRET']
      )
    end
    
    def process
      event = JSON.parse(@payload)
      event_type = event['event']
      data = event['data']
      
      case event_type
      when 'connection.activated'
        handle_connection_activated(data)
      when 'connection.deactivated'
        handle_connection_deactivated(data)
      when 'dsync.user.created'
        handle_dsync_user_created(data)
      when 'dsync.user.updated'
        handle_dsync_user_updated(data)
      when 'dsync.user.deleted'
        handle_dsync_user_deleted(data)
      end
    end
    
    private
    
    def handle_connection_activated(data)
      tenant = Tenant.find_by!(workos_org_id: data['organization_id'])
      
      SsoConnection.create!(
        tenant: tenant,
        workos_connection_id: data['id'],
        connection_type: data['connection_type'],
        provider: data['name'],
        status: 'active'
      )
    end
    
    def handle_dsync_user_created(data)
      tenant = Tenant.find_by!(workos_org_id: data['organization_id'])
      
      User.create!(
        tenant: tenant,
        email: data['emails'].first['value'],
        name: "#{data['first_name']} #{data['last_name']}",
        workos_user_id: data['id'],
        workos_idp_id: data['idp_id']
      )
    end
    
    def handle_dsync_user_deleted(data)
      User.find_by(workos_user_id: data['id'])&.update!(status: 'inactive')
    end
  end
  ```

Controller de Webhook:
  ```ruby
  # app/controllers/api/v1/webhooks/workos_controller.rb
  class Api::V1::Webhooks::WorkosController < ApplicationController
    skip_before_action :authenticate!
    
    def receive
      service = WorkOSWebhookService.new(
        request.raw_post,
        request.headers['WorkOS-Signature']
      )
      
      service.verify_signature!
      ProcessWorkOSWebhookJob.perform_later(request.raw_post)
      
      head :ok
    rescue WorkOS::SignatureVerificationError
      head :unauthorized
    end
  end
  ```

DoD (Definition of Done):
  - [ ] WebhookService implementado
  - [ ] Verificação de assinatura
  - [ ] Handlers para cada evento
  - [ ] Job para processamento async

Critérios de Aceitação:
  - [ ] Webhooks verificados
  - [ ] Eventos processados corretamente
```

---

### CARD DEV-S2-004: Implementar JWT Session Management

```yaml
Titulo: [DEVS] Implementar Gerenciamento de Sessão JWT
Tipo: Backend
Sprint: Semana 2
Pontos: 5
Prioridade: Alta
Sequência: 4 de 5
Dependências: DEV-S2-001

Descrição: |
  Implementar geração e validação de JWT para
  autenticação de requisições.

Objetivo: |
  Manter sessões de usuário de forma stateless
  usando JWT tokens.

Implementação:
  ```ruby
  # app/services/jwt_service.rb
  class JwtService
    SECRET = ENV['JWT_SECRET']
    ALGORITHM = 'HS256'
    EXPIRATION = 24.hours
    
    def self.encode(payload)
      payload[:exp] = EXPIRATION.from_now.to_i
      payload[:iat] = Time.now.to_i
      JWT.encode(payload, SECRET, ALGORITHM)
    end
    
    def self.decode(token)
      decoded = JWT.decode(token, SECRET, true, { algorithm: ALGORITHM })
      HashWithIndifferentAccess.new(decoded.first)
    rescue JWT::ExpiredSignature
      raise AuthenticationError, 'Token expired'
    rescue JWT::DecodeError
      raise AuthenticationError, 'Invalid token'
    end
  end
  
  # app/controllers/concerns/authenticatable.rb
  module Authenticatable
    extend ActiveSupport::Concern
    
    included do
      before_action :authenticate!
    end
    
    def authenticate!
      token = request.headers['Authorization']&.split(' ')&.last
      raise AuthenticationError, 'Token missing' unless token
      
      payload = JwtService.decode(token)
      @current_user = User.find(payload[:user_id])
      set_current_tenant(@current_user.tenant)
    rescue AuthenticationError => e
      render json: { error: e.message }, status: :unauthorized
    end
    
    def current_user
      @current_user
    end
  end
  ```

DoD (Definition of Done):
  - [ ] JwtService implementado
  - [ ] Authenticatable concern
  - [ ] Tokens expiram corretamente
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] JWT gerado com payload correto
  - [ ] JWT validado com sucesso
  - [ ] Tokens expirados rejeitados
```

---

### CARD DEV-S2-005: Testar Fluxo SSO End-to-End

```yaml
Titulo: [DEVS] Testar Fluxo SSO Completo
Tipo: Teste
Sprint: Semana 2
Pontos: 5
Prioridade: Alta
Sequência: 5 de 5
Dependências: DEV-S2-001 a DEV-S2-004

Descrição: |
  Testar o fluxo completo de SSO usando a Organization
  de teste configurada pelo Gestor.

Objetivo: |
  Validar que o fluxo de login funciona end-to-end
  antes de seguir para as próximas integrações.

Dados de Teste (do Handoff):
  - Test Org ID: org_xxx
  - Test Connection ID: conn_xxx (WorkOS Test IdP)

Cenários de Teste:

  CENÁRIO 1: Login SSO Novo Usuário
    1. Chamar GET /api/v1/auth/sso_url com org_id
    2. Redirecionar para WorkOS Test IdP
    3. Usar email de teste
    4. Callback cria novo usuário
    5. Retorna JWT válido
  
  CENÁRIO 2: Login SSO Usuário Existente
    1. Repetir login com mesmo email
    2. Usuário existente é encontrado
    3. last_login_at é atualizado
    4. Retorna JWT válido
  
  CENÁRIO 3: Webhook SCIM - Criar Usuário
    1. Enviar webhook dsync.user.created
    2. Usuário é criado no tenant correto
  
  CENÁRIO 4: Webhook SCIM - Deletar Usuário
    1. Enviar webhook dsync.user.deleted
    2. Usuário é marcado como inactive
  
  CENÁRIO 5: Token Expirado
    1. Usar token expirado
    2. Retorna 401 Unauthorized

Testes Automatizados:
  ```ruby
  # spec/requests/auth_spec.rb
  RSpec.describe 'Auth API' do
    describe 'GET /api/v1/auth/sso_url' do
      it 'returns SSO URL' do
        get '/api/v1/auth/sso_url', params: { organization_id: 'org_xxx' }
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['url']).to include('workos.com')
      end
    end
    
    describe 'POST /api/v1/auth/callback' do
      it 'returns JWT for valid code' do
        # Mock WorkOS response
        post '/api/v1/auth/callback', params: { code: 'valid_code' }
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['token']).to be_present
      end
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Todos os cenários testados
  - [ ] Testes automatizados escritos
  - [ ] Bugs corrigidos

Critérios de Aceitação:
  - [ ] Login SSO funciona end-to-end
  - [ ] Webhooks processados corretamente
  - [ ] JWT válido retornado
```

---

## SEMANA 3: BILLING - Stripe (5 cards)

---

### CARD DEV-S3-001: Implementar StripeWebhookService

```yaml
Titulo: [DEVS] Implementar StripeWebhookService
Tipo: Backend
Sprint: Semana 3
Pontos: 8
Prioridade: Crítica
Sequência: 1 de 5
Dependências: Handoff GST-STR

Descrição: |
  Implementar service para processar webhooks do Stripe
  (pagamentos, subscriptions, invoices).

Objetivo: |
  Receber e processar eventos de billing para manter
  o banco de dados sincronizado com o Stripe.

Credenciais Necessárias (do Handoff):
  - STRIPE_SECRET_KEY
  - STRIPE_WEBHOOK_SECRET
  - Product IDs e Price IDs

Eventos a Processar:
  - checkout.session.completed
  - customer.created
  - customer.subscription.created / updated / deleted
  - invoice.paid / payment_failed

Implementação:
  ```ruby
  # app/services/stripe_webhook_service.rb
  class StripeWebhookService
    def initialize(payload, signature)
      @payload = payload
      @signature = signature
    end
    
    def verify_and_construct_event
      Stripe::Webhook.construct_event(
        @payload,
        @signature,
        ENV['STRIPE_WEBHOOK_SECRET']
      )
    rescue Stripe::SignatureVerificationError
      raise WebhookError, 'Invalid signature'
    end
    
    def process(event)
      case event.type
      when 'checkout.session.completed'
        handle_checkout_completed(event.data.object)
      when 'customer.subscription.created'
        handle_subscription_created(event.data.object)
      when 'customer.subscription.updated'
        handle_subscription_updated(event.data.object)
      when 'customer.subscription.deleted'
        handle_subscription_deleted(event.data.object)
      when 'invoice.paid'
        handle_invoice_paid(event.data.object)
      when 'invoice.payment_failed'
        handle_invoice_failed(event.data.object)
      end
    end
    
    private
    
    def handle_checkout_completed(session)
      tenant = Tenant.find_by(stripe_customer_id: session.customer)
      return unless tenant
      
      # Atualizar status do tenant
      tenant.update!(status: 'active', plan: extract_plan(session))
      
      # Sync para HubSpot
      SyncTenantToHubSpotJob.perform_later(tenant.id)
    end
    
    def handle_subscription_created(subscription)
      tenant = Tenant.find_by(stripe_customer_id: subscription.customer)
      return unless tenant
      
      Subscription.create!(
        tenant: tenant,
        stripe_subscription_id: subscription.id,
        stripe_price_id: subscription.items.data.first.price.id,
        status: subscription.status,
        current_period_start: Time.at(subscription.current_period_start),
        current_period_end: Time.at(subscription.current_period_end)
      )
    end
    
    def handle_invoice_paid(invoice)
      tenant = Tenant.find_by(stripe_customer_id: invoice.customer)
      return unless tenant
      
      Invoice.create!(
        tenant: tenant,
        stripe_invoice_id: invoice.id,
        amount_cents: invoice.amount_paid,
        status: 'paid',
        paid_at: Time.at(invoice.status_transitions.paid_at),
        pdf_url: invoice.invoice_pdf
      )
    end
  end
  ```

DoD (Definition of Done):
  - [ ] WebhookService implementado
  - [ ] Verificação de assinatura
  - [ ] Handlers para cada evento
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Webhooks verificados
  - [ ] Subscriptions criadas/atualizadas
  - [ ] Invoices registradas
```

---

### CARD DEV-S3-002: Implementar StripeBillingService

```yaml
Titulo: [DEVS] Implementar StripeBillingService
Tipo: Backend
Sprint: Semana 3
Pontos: 8
Prioridade: Crítica
Sequência: 2 de 5
Dependências: Handoff GST-STR

Descrição: |
  Implementar service para criar checkout sessions
  e gerenciar o Customer Portal.

Objetivo: |
  Permitir que novos clientes assinem e clientes
  existentes gerenciem suas assinaturas.

Implementação:
  ```ruby
  # app/services/stripe_billing_service.rb
  class StripeBillingService
    # IDs do Handoff
    PRICES = {
      starter_monthly: 'price_xxx',
      starter_yearly: 'price_xxx',
      professional_monthly: 'price_xxx',
      professional_yearly: 'price_xxx'
    }
    
    def create_checkout_session(tenant:, price_key:, success_url:, cancel_url:)
      Stripe::Checkout::Session.create(
        customer: tenant.stripe_customer_id,
        mode: 'subscription',
        line_items: [{
          price: PRICES[price_key],
          quantity: 1
        }],
        success_url: success_url,
        cancel_url: cancel_url,
        metadata: {
          tenant_id: tenant.id
        }
      )
    end
    
    def create_customer_portal_session(tenant:, return_url:)
      Stripe::BillingPortal::Session.create(
        customer: tenant.stripe_customer_id,
        return_url: return_url
      )
    end
    
    def get_subscription_status(tenant)
      subscription = Subscription.find_by(tenant: tenant)
      return nil unless subscription
      
      stripe_sub = Stripe::Subscription.retrieve(subscription.stripe_subscription_id)
      
      {
        status: stripe_sub.status,
        plan: extract_plan_name(stripe_sub),
        current_period_end: Time.at(stripe_sub.current_period_end),
        cancel_at_period_end: stripe_sub.cancel_at_period_end
      }
    end
  end
  ```

DoD (Definition of Done):
  - [ ] BillingService implementado
  - [ ] Checkout session funcional
  - [ ] Customer portal funcional
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Checkout session cria URL válida
  - [ ] Portal session cria URL válida
  - [ ] Status da subscription retornado
```

---

### CARD DEV-S3-003: Criar Endpoints de Billing

```yaml
Titulo: [DEVS] Criar Endpoints de Billing
Tipo: Backend
Sprint: Semana 3
Pontos: 5
Prioridade: Alta
Sequência: 3 de 5
Dependências: DEV-S3-002

Descrição: |
  Criar endpoints da API para operações de billing.

Objetivo: |
  Expor APIs para o frontend gerenciar checkout
  e acesso ao Customer Portal.

Endpoints:
  ```ruby
  # config/routes.rb
  namespace :api do
    namespace :v1 do
      namespace :billing do
        post :create_checkout_session
        post :create_customer_portal_session
        get :subscription_status
      end
      
      # Webhook separado
      post 'webhooks/stripe', to: 'webhooks/stripe#receive'
    end
  end
  ```

Controller:
  ```ruby
  # app/controllers/api/v1/billing_controller.rb
  class Api::V1::BillingController < ApplicationController
    def create_checkout_session
      service = StripeBillingService.new
      
      session = service.create_checkout_session(
        tenant: current_user.tenant,
        price_key: params[:price_key].to_sym,
        success_url: params[:success_url],
        cancel_url: params[:cancel_url]
      )
      
      render json: { checkout_url: session.url }
    end
    
    def create_customer_portal_session
      service = StripeBillingService.new
      
      session = service.create_customer_portal_session(
        tenant: current_user.tenant,
        return_url: params[:return_url]
      )
      
      render json: { portal_url: session.url }
    end
    
    def subscription_status
      service = StripeBillingService.new
      status = service.get_subscription_status(current_user.tenant)
      
      render json: status
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Endpoints criados
  - [ ] Autenticação requerida
  - [ ] Testes de integração

Critérios de Aceitação:
  - [ ] Checkout URL retornada
  - [ ] Portal URL retornada
  - [ ] Status retornado
```

---

### CARD DEV-S3-004: Implementar Webhook Controller

```yaml
Titulo: [DEVS] Implementar Controller de Webhooks Stripe
Tipo: Backend
Sprint: Semana 3
Pontos: 3
Prioridade: Alta
Sequência: 4 de 5
Dependências: DEV-S3-001

Descrição: |
  Criar controller para receber webhooks do Stripe
  e enfileirar para processamento.

Implementação:
  ```ruby
  # app/controllers/api/v1/webhooks/stripe_controller.rb
  class Api::V1::Webhooks::StripeController < ApplicationController
    skip_before_action :authenticate!
    
    def receive
      # Salvar evento para debug
      webhook_event = WebhookEvent.create!(
        source: 'stripe',
        event_type: params[:type],
        external_id: params[:id],
        payload: request.raw_post,
        status: 'pending'
      )
      
      # Processar async
      ProcessStripeWebhookJob.perform_later(webhook_event.id)
      
      head :ok
    rescue JSON::ParserError
      head :bad_request
    end
  end
  
  # app/jobs/process_stripe_webhook_job.rb
  class ProcessStripeWebhookJob < ApplicationJob
    queue_as :webhooks
    
    def perform(webhook_event_id)
      webhook_event = WebhookEvent.find(webhook_event_id)
      
      service = StripeWebhookService.new(
        webhook_event.payload,
        webhook_event.payload # signature já verificada na chegada
      )
      
      event = service.verify_and_construct_event
      service.process(event)
      
      webhook_event.update!(status: 'processed', processed_at: Time.current)
    rescue => e
      webhook_event.update!(
        status: 'failed',
        error_message: e.message,
        retry_count: webhook_event.retry_count + 1
      )
      raise e if webhook_event.retry_count < 3
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Controller implementado
  - [ ] Job de processamento
  - [ ] Eventos salvos no banco
  - [ ] Retry em caso de falha

Critérios de Aceitação:
  - [ ] Webhooks recebidos com 200
  - [ ] Eventos processados async
  - [ ] Falhas registradas
```

---

### CARD DEV-S3-005: Testar Fluxo de Checkout

```yaml
Titulo: [DEVS] Testar Fluxo de Checkout End-to-End
Tipo: Teste
Sprint: Semana 3
Pontos: 5
Prioridade: Alta
Sequência: 5 de 5
Dependências: DEV-S3-001 a DEV-S3-004

Descrição: |
  Testar o fluxo completo de checkout usando o
  modo de teste do Stripe.

Objetivo: |
  Validar que pagamentos funcionam end-to-end
  antes de ir para produção.

Dados de Teste (do Handoff):
  - Stripe Test Keys
  - Test Price IDs
  - Cartão de teste: 4242 4242 4242 4242

Cenários de Teste:

  CENÁRIO 1: Checkout Sucesso
    1. Criar checkout session
    2. Completar checkout com cartão de teste
    3. Webhook checkout.session.completed
    4. Tenant atualizado para 'active'
    5. Subscription criada no banco
  
  CENÁRIO 2: Customer Portal
    1. Criar portal session
    2. Acessar portal
    3. Atualizar cartão
    4. Webhook customer.updated
  
  CENÁRIO 3: Cancelamento
    1. Cancelar via portal
    2. Webhook subscription.updated (cancel_at_period_end)
    3. Webhook subscription.deleted (ao expirar)
  
  CENÁRIO 4: Pagamento Falhou
    1. Usar cartão 4000 0000 0000 0002 (decline)
    2. Webhook invoice.payment_failed
    3. Tenant notificado

Stripe CLI para testes:
  ```bash
  # Instalar Stripe CLI
  stripe login
  
  # Forward webhooks para local
  stripe listen --forward-to localhost:3000/api/v1/webhooks/stripe
  
  # Disparar eventos de teste
  stripe trigger checkout.session.completed
  stripe trigger invoice.paid
  stripe trigger invoice.payment_failed
  ```

DoD (Definition of Done):
  - [ ] Todos os cenários testados
  - [ ] Stripe CLI funcionando
  - [ ] Fluxo validado

Critérios de Aceitação:
  - [ ] Checkout funciona
  - [ ] Portal funciona
  - [ ] Webhooks processados
```

---

## SEMANA 4: CRM + ONBOARDING - HubSpot Workflows (3 cards)

---

### CARD DEV-S4-001: Implementar HubSpotSyncService

```yaml
Titulo: [DEVS] Implementar HubSpotSyncService
Tipo: Backend
Sprint: Semana 4
Pontos: 8
Prioridade: Alta
Sequência: 1 de 5
Dependências: Handoff GST-HUB

Descrição: |
  Implementar service para sincronizar dados de
  tenants com o HubSpot CRM.

Objetivo: |
  Manter HubSpot atualizado com dados de clientes,
  status, plano, MRR, etc.

Credenciais Necessárias (do Handoff):
  - HUBSPOT_ACCESS_TOKEN
  - Property names
  - Pipeline IDs

Implementação:
  ```ruby
  # app/services/hub_spot_sync_service.rb
  class HubSpotSyncService
    def initialize
      @client = Hubspot::Client.new(access_token: ENV['HUBSPOT_ACCESS_TOKEN'])
    end
    
    # Criar ou atualizar Company
    def sync_tenant(tenant)
      properties = {
        name: tenant.name,
        wedo_tenant_id: tenant.id.to_s,
        wedo_stripe_customer_id: tenant.stripe_customer_id,
        wedo_workos_org_id: tenant.workos_org_id,
        wedo_plan: tenant.plan,
        wedo_mrr: calculate_mrr(tenant),
        wedo_status: tenant.status,
        wedo_license_count: tenant.license_count,
        wedo_sso_enabled: tenant.sso_enabled?.to_s
      }
      
      if tenant.hubspot_company_id.present?
        update_company(tenant.hubspot_company_id, properties)
      else
        company = create_company(properties)
        tenant.update!(hubspot_company_id: company.id)
      end
    end
    
    # Atualizar estágio de deal
    def update_deal_stage(tenant, pipeline_id, stage_id)
      deal = find_deal_by_tenant(tenant)
      return unless deal
      
      @client.crm.deals.basic_api.update(
        deal_id: deal.id,
        properties: {
          pipeline: pipeline_id,
          dealstage: stage_id
        }
      )
    end
    
    private
    
    def create_company(properties)
      @client.crm.companies.basic_api.create(
        properties: properties
      )
    end
    
    def update_company(company_id, properties)
      @client.crm.companies.basic_api.update(
        company_id: company_id,
        properties: properties
      )
    end
    
    def calculate_mrr(tenant)
      subscription = tenant.subscriptions.active.first
      return 0 unless subscription
      
      # Converter price para MRR
      # (anual / 12 ou mensal * 1)
      subscription.monthly_amount
    end
  end
  ```

DoD (Definition of Done):
  - [ ] SyncService implementado
  - [ ] Create/Update company funcional
  - [ ] Propriedades customizadas mapeadas
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Tenant sincroniza para HubSpot
  - [ ] Propriedades atualizadas
```

---

### CARD DEV-S4-002: Implementar Jobs de Sincronização

```yaml
Titulo: [DEVS] Implementar Jobs de Sync HubSpot
Tipo: Backend
Sprint: Semana 4
Pontos: 5
Prioridade: Alta
Sequência: 2 de 5
Dependências: DEV-S4-001

Descrição: |
  Criar jobs para sincronização assíncrona com HubSpot.

Objetivo: |
  Manter HubSpot atualizado sem bloquear requests.

Jobs a Criar:
  ```ruby
  # app/jobs/sync_tenant_to_hub_spot_job.rb
  class SyncTenantToHubSpotJob < ApplicationJob
    queue_as :sync
    
    def perform(tenant_id)
      tenant = Tenant.find(tenant_id)
      HubSpotSyncService.new.sync_tenant(tenant)
    end
  end
  
  # app/jobs/update_hub_spot_deal_stage_job.rb
  class UpdateHubSpotDealStageJob < ApplicationJob
    queue_as :sync
    
    def perform(tenant_id, stage_name)
      tenant = Tenant.find(tenant_id)
      
      pipeline_id = ENV['HUBSPOT_PIPELINE_ONBOARDING_ID']
      stage_id = stage_mapping[stage_name]
      
      HubSpotSyncService.new.update_deal_stage(tenant, pipeline_id, stage_id)
    end
    
    private
    
    def stage_mapping
      {
        'kickoff' => ENV['HUBSPOT_STAGE_KICKOFF_ID'],
        'configuration' => ENV['HUBSPOT_STAGE_CONFIG_ID'],
        'training' => ENV['HUBSPOT_STAGE_TRAINING_ID'],
        'go_live' => ENV['HUBSPOT_STAGE_GOLIVE_ID'],
        'success' => ENV['HUBSPOT_STAGE_SUCCESS_ID']
      }
    end
  end
  
  # app/jobs/update_hub_spot_mrr_job.rb
  class UpdateHubSpotMrrJob < ApplicationJob
    queue_as :sync
    
    def perform(tenant_id)
      tenant = Tenant.find(tenant_id)
      
      HubSpotSyncService.new.sync_tenant(tenant)
    end
  end
  ```

Disparos dos Jobs:
  ```ruby
  # Em callbacks ou outros services
  
  # Quando tenant é criado
  after_create :sync_to_hubspot
  
  def sync_to_hubspot
    SyncTenantToHubSpotJob.perform_later(id)
  end
  
  # Quando subscription muda
  after_save :update_hubspot_mrr, if: :saved_change_to_status?
  
  def update_hubspot_mrr
    UpdateHubSpotMrrJob.perform_later(tenant_id)
  end
  ```

DoD (Definition of Done):
  - [ ] Jobs criados
  - [ ] Filas configuradas
  - [ ] Callbacks disparando jobs
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Sync roda em background
  - [ ] Não bloqueia requests
```

---

### CARD DEV-S4-005: Implementar HubSpotWebhookService (Opcional)

```yaml
Titulo: [DEVS] Implementar Webhooks HubSpot (Opcional)
Tipo: Backend
Sprint: Semana 4
Pontos: 5
Prioridade: Baixa
Sequência: 5 de 5
Dependências: DEV-S4-001
Nota: Implementar apenas se precisar de sync bidirecional

Descrição: |
  Implementar service para receber webhooks do HubSpot
  quando dados são alterados no CRM.

Objetivo: |
  Manter sincronização bidirecional entre sistema
  e HubSpot (opcional para MVP).

Casos de Uso:
  - CSM atualiza wedo_csm_owner no HubSpot
  - Sistema recebe webhook e atualiza local
  - Deal stage muda no HubSpot
  - Sistema atualiza onboarding_stage local

Implementação:
  ```ruby
  # app/services/hub_spot_webhook_service.rb
  class HubSpotWebhookService
    def process(events)
      events.each do |event|
        case event['subscriptionType']
        when 'company.propertyChange'
          handle_company_change(event)
        when 'deal.propertyChange'
          handle_deal_change(event)
        end
      end
    end
    
    private
    
    def handle_company_change(event)
      company_id = event['objectId']
      property = event['propertyName']
      new_value = event['propertyValue']
      
      tenant = Tenant.find_by(hubspot_company_id: company_id)
      return unless tenant
      
      case property
      when 'wedo_csm_owner'
        # Atualizar CSM local
      end
    end
  end
  ```

DoD (Definition of Done):
  - [ ] WebhookService implementado
  - [ ] Eventos relevantes processados

Critérios de Aceitação:
  - [ ] Sync bidirecional funciona
```

---

## SEMANA 5: COMPLIANCE + POLISH (4 cards)

---

### CARD DEV-S5-001: Implementar PrivacyToolsService

```yaml
Titulo: [DEVS] Implementar PrivacyToolsService
Tipo: Backend
Sprint: Semana 5
Pontos: 8
Prioridade: Alta
Sequência: 1 de 4
Dependências: Handoff GST-PVT

Descrição: |
  Implementar service para processar solicitações LGPD
  recebidas via Privacy Tools.

Objetivo: |
  Automatizar o processamento de solicitações de
  acesso, correção e exclusão de dados.

Credenciais Necessárias (do Handoff):
  - PRIVACYTOOLS_API_KEY
  - PRIVACYTOOLS_WEBHOOK_SECRET

Implementação:
  ```ruby
  # app/services/privacy_tools_service.rb
  class PrivacyToolsService
    BASE_URL = 'https://api.privacytools.com.br/v1'
    
    def initialize
      @api_key = ENV['PRIVACYTOOLS_API_KEY']
    end
    
    # Processar solicitação de acesso
    def process_access_request(request_id, email)
      # Buscar todos os dados do candidato
      data = collect_candidate_data(email)
      
      # Anexar ao Privacy Tools
      attach_data_export(request_id, data)
      
      # Marcar como concluída
      complete_request(request_id)
    end
    
    # Processar solicitação de exclusão
    def process_deletion_request(request_id, email)
      # Deletar/anonimizar dados
      anonymize_candidate_data(email)
      
      # Marcar como concluída
      complete_request(request_id)
    end
    
    private
    
    def collect_candidate_data(email)
      # Buscar em todas as tabelas
      candidate = Candidate.find_by(email: email)
      return {} unless candidate
      
      {
        personal_info: candidate.attributes.except('id'),
        applications: candidate.applications.map(&:attributes),
        screenings: candidate.screenings.map(&:attributes),
        communications: candidate.communications.map(&:attributes)
      }
    end
    
    def attach_data_export(request_id, data)
      HTTParty.post(
        "#{BASE_URL}/requests/#{request_id}/attachments",
        headers: auth_headers,
        body: {
          filename: "dados_#{Time.current.strftime('%Y%m%d')}.json",
          content: data.to_json,
          content_type: 'application/json'
        }.to_json
      )
    end
    
    def complete_request(request_id)
      HTTParty.post(
        "#{BASE_URL}/requests/#{request_id}/complete",
        headers: auth_headers
      )
    end
    
    def anonymize_candidate_data(email)
      candidate = Candidate.find_by(email: email)
      return unless candidate
      
      candidate.update!(
        name: 'ANONIMIZADO',
        email: "anonimizado_#{candidate.id}@deleted.local",
        phone: nil,
        resume_url: nil,
        deleted_at: Time.current
      )
    end
    
    def auth_headers
      {
        'Authorization' => "Bearer #{@api_key}",
        'Content-Type' => 'application/json'
      }
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Service implementado
  - [ ] Acesso, correção, exclusão funcionais
  - [ ] Dados anonimizados corretamente
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Solicitação de acesso exporta dados
  - [ ] Solicitação de exclusão anonimiza
  - [ ] Privacy Tools notificado
```

---

### CARD DEV-S5-002: Implementar Webhook Privacy Tools

```yaml
Titulo: [DEVS] Implementar Webhook Privacy Tools
Tipo: Backend
Sprint: Semana 5
Pontos: 5
Prioridade: Alta
Sequência: 2 de 4
Dependências: DEV-S5-001

Descrição: |
  Criar controller para receber webhooks do Privacy Tools
  quando novas solicitações são criadas.

Implementação:
  ```ruby
  # app/controllers/api/v1/webhooks/privacy_tools_controller.rb
  class Api::V1::Webhooks::PrivacyToolsController < ApplicationController
    skip_before_action :authenticate!
    
    def receive
      verify_signature!
      
      payload = JSON.parse(request.raw_post)
      
      LgpdRequest.create!(
        privacy_tools_id: payload['request_id'],
        request_type: payload['type'],
        requester_email: payload['requester_email'],
        requester_name: payload['requester_name'],
        status: 'pending',
        due_date: Time.parse(payload['due_date'])
      )
      
      ProcessLgpdRequestJob.perform_later(payload['request_id'])
      
      head :ok
    end
    
    private
    
    def verify_signature!
      signature = request.headers['X-Privacy-Signature']
      expected = OpenSSL::HMAC.hexdigest(
        'sha256',
        ENV['PRIVACYTOOLS_WEBHOOK_SECRET'],
        request.raw_post
      )
      
      head :unauthorized unless signature == expected
    end
  end
  
  # app/jobs/process_lgpd_request_job.rb
  class ProcessLgpdRequestJob < ApplicationJob
    queue_as :critical
    
    def perform(request_id)
      lgpd_request = LgpdRequest.find_by!(privacy_tools_id: request_id)
      service = PrivacyToolsService.new
      
      case lgpd_request.request_type
      when 'access'
        service.process_access_request(request_id, lgpd_request.requester_email)
      when 'deletion'
        service.process_deletion_request(request_id, lgpd_request.requester_email)
      when 'correction'
        # Notificar admin para correção manual
      end
      
      lgpd_request.update!(status: 'completed', completed_at: Time.current)
    end
  end
  ```

DoD (Definition of Done):
  - [ ] Webhook controller implementado
  - [ ] Verificação de assinatura
  - [ ] Job de processamento
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Webhooks recebidos
  - [ ] Solicitações processadas
  - [ ] Status atualizado
```

---

### CARD DEV-S5-003: Implementar AuditLogService

```yaml
Titulo: [DEVS] Implementar AuditLogService
Tipo: Backend
Sprint: Semana 5
Pontos: 5
Prioridade: Alta
Sequência: 3 de 4

Descrição: |
  Implementar service para registrar todas as ações
  relevantes para compliance e debugging.

Objetivo: |
  Ter um trail de auditoria completo para
  SOC 2 e LGPD compliance.

Implementação:
  ```ruby
  # app/services/audit_log_service.rb
  class AuditLogService
    def self.log(action:, user: nil, tenant: nil, resource: nil, changes: {}, request: nil)
      AuditLog.create!(
        tenant: tenant || user&.tenant,
        user: user,
        action: action,
        resource_type: resource&.class&.name,
        resource_id: resource&.id&.to_s,
        changes: changes,
        ip_address: request&.remote_ip,
        user_agent: request&.user_agent
      )
    end
  end
  
  # Uso em controllers
  class Api::V1::TenantsController < ApplicationController
    def update
      @tenant.update!(tenant_params)
      
      AuditLogService.log(
        action: 'tenant.updated',
        user: current_user,
        resource: @tenant,
        changes: @tenant.previous_changes,
        request: request
      )
      
      render json: @tenant
    end
  end
  
  # Uso em models (callbacks)
  class User < ApplicationRecord
    after_create :log_creation
    after_destroy :log_deletion
    
    private
    
    def log_creation
      AuditLogService.log(
        action: 'user.created',
        tenant: tenant,
        resource: self
      )
    end
    
    def log_deletion
      AuditLogService.log(
        action: 'user.deleted',
        tenant: tenant,
        resource: self
      )
    end
  end
  ```

Ações a Auditar:
  - user.created / updated / deleted
  - tenant.created / updated / suspended
  - subscription.created / updated / canceled
  - sso_connection.activated / deactivated
  - lgpd_request.created / completed
  - login.success / login.failure

DoD (Definition of Done):
  - [ ] AuditLogService implementado
  - [ ] Ações principais logadas
  - [ ] IP e User-Agent capturados
  - [ ] Testes passando

Critérios de Aceitação:
  - [ ] Todas as ações críticas logadas
  - [ ] Logs queryáveis por tenant
```

---

### CARD DEV-S5-004: Testes Finais e Documentação

```yaml
Titulo: [DEVS] Testes Finais e Documentação da API
Tipo: Documentação + Teste
Sprint: Semana 5
Pontos: 8
Prioridade: Alta
Sequência: 4 de 4
Dependências: Todas as tarefas anteriores

Descrição: |
  Realizar testes finais de integração e
  documentar a API para uso do frontend.

Objetivo: |
  Garantir qualidade e facilitar integração
  com o time de frontend.

Tarefas:

  1. TESTES DE INTEGRAÇÃO
     - [ ] Fluxo completo: Sign up → Checkout → Active
     - [ ] Fluxo SSO: Login → JWT → Acesso
     - [ ] Fluxo LGPD: Request → Process → Complete
     - [ ] Webhooks de todas as fontes
  
  2. TESTES DE CARGA (básico)
     - [ ] 100 requests/segundo nos endpoints principais
     - [ ] Webhooks não bloqueiam (async)
  
  3. SEGURANÇA
     - [ ] Rate limiting configurado
     - [ ] CORS restrito
     - [ ] Tokens expiram
     - [ ] Secrets não expostos em logs
  
  4. DOCUMENTAÇÃO API
     - [ ] OpenAPI/Swagger spec
     - [ ] Exemplos de request/response
     - [ ] Erros documentados

Documentação (OpenAPI):
  ```yaml
  openapi: 3.0.0
  info:
    title: WeDo Talent Admin API
    version: 1.0.0
  
  paths:
    /api/v1/auth/sso_url:
      get:
        summary: Get SSO URL
        parameters:
          - name: organization_id
            in: query
            required: true
        responses:
          200:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    url:
                      type: string
    
    /api/v1/billing/create_checkout_session:
      post:
        summary: Create Checkout Session
        security:
          - bearerAuth: []
        # ...
  ```

DoD (Definition of Done):
  - [ ] Testes de integração passando
  - [ ] Segurança validada
  - [ ] API documentada
  - [ ] README atualizado

Critérios de Aceitação:
  - [ ] Cobertura de testes > 80%
  - [ ] Documentação completa
  - [ ] Pronto para frontend integrar
```

---

# RESUMO FINAL

## Totais

| Categoria | Quantidade | Tempo Estimado |
|-----------|------------|----------------|
| **CARDS GESTOR** | 34 cards | 2-3 dias |
| **CARDS DEVS** | 22 cards | 4-5 semanas |
| **TOTAL** | 56 cards | ~5-6 semanas |

## Ordem de Execução

```
SEMANA 0: GESTOR (Paralelo ao setup dos devs)
├── GST-STR: Stripe (7 cards)
├── GST-HUB: HubSpot (10 cards)
├── GST-WOS: WorkOS (7 cards)
├── GST-PWL: ProfitWell (4 cards)
└── GST-PVT: Privacy Tools (6 cards)
    ↓
HANDOFF DOCUMENT COMPLETO
    ↓
SEMANA 1: Fundação (Rails + PostgreSQL)
SEMANA 2: Auth (WorkOS SSO)
SEMANA 3: Billing (Stripe)
SEMANA 4: CRM (HubSpot Workflows + Onboarding)
SEMANA 5: Compliance + Polish
```

## Labels Sugeridas para Jira

| Label | Uso |
|-------|-----|
| `gestor` | Cards de configuração SaaS |
| `devs` | Cards de desenvolvimento |
| `stripe` | Relacionado ao Stripe |
| `hubspot` | Relacionado ao HubSpot |
| `workos` | Relacionado ao WorkOS |
| `privacytools` | Relacionado ao Privacy Tools |
| `profitwell` | Relacionado ao ProfitWell |
| `backend` | Desenvolvimento backend |
| `infra` | Infraestrutura |
| `teste` | Cards de teste |
| `docs` | Documentação |

---

**Documento gerado em:** 14 de Janeiro de 2026  
**Baseado em:** Apêndice I - WEDOTALENT_INTEGRACOES_COMPLETO.md  
**Próximo passo:** Importar cards no Jira e iniciar execução
