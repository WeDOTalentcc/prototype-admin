# Análise de Viabilidade: Stack SaaS para WeDo Talent 2.0

> **Stack Final: Stripe + ProfitWell + HubSpot + Arrows + WorkOS + Vanta/Drata + Warden AI + Privacy Tools**

**Versão:** 2.0 (Final)  
**Data:** 12 de Janeiro de 2026  
**Autor:** Equipe WeDo Talent

---

## 🎯 RESUMO EXECUTIVO - DECISÃO FINAL

### Stack Aprovada para MVP

| Categoria | Ferramenta | Função | Custo/ano |
|-----------|------------|--------|-----------|
| **Pagamentos** | Stripe | Billing, subscriptions | 2.9% + taxas |
| **Métricas SaaS** | ProfitWell | MRR, Churn, LTV, ARR | **Grátis** |
| **CRM + Clientes** | HubSpot | CRUD clientes, dashboard | (já integrado) |
| **Onboarding** | Arrows | Jornada cliente, tracking | ~R$ 30-75k |
| **SSO/SCIM/MFA** | WorkOS | Autenticação enterprise | ~R$ 7-30k |
| **Compliance Global** | Vanta ou Drata | SOC 2, ISO 27001 | ~R$ 35-60k |
| **LGPD Brasil** | Privacy Tools | Portal titular, RIPD | ~R$ 15-30k |
| **AI Bias Audit** | Warden AI | Auditoria LIA screening | A definir |
| **Total Estimado** | | | **R$ 87-195k/ano** |

### Filosofia: Desenvolver Mínimo, Integrar Máximo

| Abordagem | % do Sistema |
|-----------|--------------|
| **Ferramentas SaaS Prontas** | ~70% |
| **Desenvolvimento Interno** | ~30% |

### O Que Será Desenvolvido Internamente (Rails + Vue.js)

1. **Core Recrutamento** - Gestão de vagas, candidatos, pipeline
2. **LIA Chat** - Interface conversacional AI
3. **Busca de Candidatos** - Integração Pearch API
4. **Portal LGPD Público** - Customizado para WeDo
5. **Trust Center Público** - Branding WeDo

### O Que Será 100% SaaS (Zero Desenvolvimento)

1. ✅ **Billing/Faturas** → Stripe Customer Portal
2. ✅ **Métricas SaaS** → ProfitWell Dashboard
3. ✅ **CRUD Clientes** → HubSpot Companies
4. ✅ **Onboarding Tracking** → Arrows
5. ✅ **SSO/SCIM/MFA** → WorkOS Dashboard
6. ✅ **Compliance/Audit** → Vanta ou Drata
7. ✅ **LGPD Interno** → Privacy Tools

---

## Sumário

### Parte I: Contexto e Inventário
1. [Visão Geral e Objetivos](#1-visão-geral-e-objetivos)
2. [Inventário WeDo Talent Admin Atual](#2-inventário-wedo-talent-admin-atual)
3. [Mapeamento de Substituição por Ferramenta](#3-mapeamento-de-substituição-por-ferramenta)

### Parte II: Guias de Ferramentas SaaS
4. [Guia Stripe Billing](#4-guia-stripe-billing)
5. [Guia ProfitWell (Paddle)](#5-guia-profitwell-paddle)
6. [Guia WorkOS](#6-guia-workos)
7. [Guia HubSpot + Arrows](#7-guia-retool) *(Inclui análise histórica do Retool)*

### Parte III: Arquitetura e Planejamento
8. [Arquitetura Final WeDo Talent 2.0](#8-arquitetura-final-wedo-talent-20)
9. [O que Manter em Rails + Vue.js](#9-o-que-manter-em-rails--vuejs)
10. [Roadmap de Migração](#10-roadmap-de-migração)

### Parte IV: Análises Financeiras e Riscos
11. [Análise de Custos](#11-análise-de-custos)
12. [Análise de Riscos](#12-análise-de-riscos-da-estratégia)

### Parte V: Decisão Final
13. [Stack Final Consolidada](#13-stack-final-consolidada)
    - 13.1 Visão Geral da Stack
    - 13.2 Detalhamento de Cada Ferramenta
    - 13.3 Matriz de Custos Consolidada
    - 13.4 Comparação: Antes vs Depois
    - 13.5 Roadmap de Implementação
    - 13.6 Checklist de Implementação
    - 13.7 O Que Será Desenvolvido Internamente

### Apêndices
14. [Glossário](#14-glossário)
15. [Histórico de Versões](#histórico-de-versões)
16. [Referências](#referências)

---

## 1. Visão Geral e Objetivos

### 1.1 Contexto

O WeDo Talent está planejando uma migração tecnológica significativa:
- **De:** Next.js + FastAPI (Python)
- **Para:** Ruby on Rails + Vue.js/Vuetify

Para acelerar essa migração e reduzir o esforço de desenvolvimento, esta análise avalia a viabilidade de substituir funcionalidades internas do Admin por ferramentas SaaS de mercado.

### 1.2 Stack Final Aprovada

| Ferramenta | Função Principal | Custo |
|------------|------------------|-------|
| **Stripe** | Billing, subscriptions, pagamentos | 2.9% + R$0.39/transação |
| **ProfitWell** | Métricas SaaS (MRR, Churn, LTV) | **Gratuito** |
| **HubSpot** | CRM, CRUD clientes, dashboard | (já integrado) |
| **Arrows** | Onboarding de clientes | $500-1.250/mês |
| **WorkOS** | SSO, SCIM, MFA, Audit Logs | $125-500/mês |
| **Vanta/Drata** | Compliance SOC 2, ISO 27001 | $600-2.500/mês |
| **Privacy Tools** | LGPD Brasil | ~R$ 1.250-2.500/mês |
| **Warden AI** | Auditoria de bias de AI | A definir |

> **Nota:** O Retool foi avaliado inicialmente mas substituído por ferramentas SaaS prontas (HubSpot, Arrows, Vanta/Drata) baseado em benchmarking de HRTechs (Popp.ai, Paradox, Findem). A análise do Retool está preservada na Seção 7 para referência histórica.

### 1.3 Objetivos da Análise

1. **Quantificar** linhas de código que podem ser eliminadas
2. **Mapear** funcionalidades substituíveis por cada ferramenta
3. **Documentar** configuração e integração de cada ferramenta
4. **Definir** o que deve permanecer em desenvolvimento próprio
5. **Estimar** economia de tempo e custo

### 1.4 Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Total de linhas no Admin atual** | ~55.700 |
| **Linhas substituíveis pela stack** | ~30.200 (54%) |
| **Linhas a manter/reconstruir** | ~25.500 (46%) |
| **Economia estimada em desenvolvimento** | R$ 80.000 |
| **Redução de tempo** | 60 dias |
| **Custo mensal da stack** | $175-1.000/mês |

---

## 2. Inventário WeDo Talent Admin Atual

### 2.1 Estrutura de Arquivos

```
plataforma-lia/src/
├── app/admin/                    # 72 páginas TSX
│   ├── page.tsx                  # Dashboard principal
│   ├── clientes/                 # Gestão de clientes
│   │   ├── page.tsx              # Lista de clientes
│   │   └── [clientId]/           # Detalhes do cliente
│   │       ├── page.tsx          # Overview
│   │       ├── faturamento/      # Billing
│   │       ├── metricas/         # Métricas SaaS
│   │       ├── usuarios/         # Gestão de usuários
│   │       ├── consumo-ia/       # Consumo de IA
│   │       ├── observabilidade/  # Logs e monitoramento
│   │       ├── conformidade/     # Compliance por cliente
│   │       ├── integracoes/      # Integrações
│   │       ├── comunicacoes/     # Templates
│   │       ├── automacoes/       # Automações
│   │       ├── testes/           # Testes específicos
│   │       ├── setup/            # Configuração inicial
│   │       ├── jornada/          # Jornada do cliente
│   │       ├── big-five/         # Avaliação Big Five
│   │       └── workforce/        # Workforce planning
│   ├── compliance/               # Hub de compliance
│   │   ├── page.tsx              # Dashboard
│   │   ├── controles/            # SOC 2, ISO, SOX
│   │   ├── lgpd/                 # LGPD
│   │   ├── auditoria/            # Audit logs
│   │   ├── riscos/               # Gestão de riscos
│   │   ├── monitoramento/        # Monitoramento segurança
│   │   ├── trust-center/         # Trust center
│   │   └── health-check/         # Health check
│   ├── configuracoes/            # Configurações globais
│   │   ├── comunicacoes/         # Templates de comunicação
│   │   ├── politicas/            # Políticas
│   │   ├── templates/            # Templates gerais
│   │   └── auditoria/            # Configuração de auditoria
│   ├── sso/                      # Gestão SSO
│   ├── metricas-plataforma/      # Métricas agregadas
│   ├── onboarding-clientes/      # Dashboard onboarding
│   ├── jornada-recrutamento/     # Jornada de recrutamento
│   └── setup-empresa/            # Setup inicial empresa
├── services/admin/               # Services administrativos
│   ├── saas-metrics-service.ts   # Métricas SaaS
│   ├── saas-metrics.ts           # Helpers
│   ├── dashboard-service.ts      # Dashboard
│   └── api-client.ts             # Cliente API
└── app/api/backend-proxy/        # Proxy para backend
    ├── billing/                  # Billing endpoints
    ├── clients/                  # Clientes endpoints
    ├── invitations/              # Convites
    └── workos/                   # WorkOS webhooks
```

### 2.2 Contagem de Linhas por Categoria

| Categoria | Arquivos | Linhas | % do Total |
|-----------|----------|--------|------------|
| **Páginas Admin** | 72 | 35.700 | 64% |
| **Services Admin** | 8 | 4.500 | 8% |
| **API Proxy Routes** | 25 | 15.500 | 28% |
| **TOTAL** | 105 | **55.700** | 100% |

### 2.3 Detalhamento por Funcionalidade

#### 2.3.1 Gestão de Clientes (~6.000 linhas)

| Página | Arquivo | Linhas | Descrição |
|--------|---------|--------|-----------|
| Lista Clientes | `clientes/page.tsx` | 800 | Grid com filtros, busca, ações |
| Detalhes Cliente | `[clientId]/page.tsx` | 600 | Overview do cliente |
| Faturamento | `[clientId]/faturamento/page.tsx` | 614 | Billing, invoices, pagamentos |
| Métricas | `[clientId]/metricas/page.tsx` | 300 | MRR, LTV, health score |
| Usuários | `[clientId]/usuarios/page.tsx` | 500 | CRUD usuários |
| Consumo IA | `[clientId]/consumo-ia/page.tsx` | 400 | Tokens, chamadas API |
| Observabilidade | `[clientId]/observabilidade/page.tsx` | 350 | Logs, erros |
| Integrações | `[clientId]/integracoes/page.tsx` | 400 | Conexões externas |
| Comunicações | `[clientId]/comunicacoes/page.tsx` | 350 | Templates por cliente |
| Automações | `[clientId]/automacoes/page.tsx` | 300 | Regras automáticas |
| Testes | `[clientId]/testes/page.tsx` | 280 | Testes específicos |
| Setup | `[clientId]/setup/page.tsx` | 350 | Configuração inicial |
| Jornada | `[clientId]/jornada/page.tsx` | 300 | Progresso onboarding |
| Big Five | `[clientId]/big-five/page.tsx` | 250 | Avaliação personalidade |
| Workforce | `[clientId]/workforce/page.tsx` | 206 | Planejamento workforce |

#### 2.3.2 Compliance Hub (~15.000 linhas)

| Subcategoria | Páginas | Linhas | Descrição |
|--------------|---------|--------|-----------|
| **Dashboard** | 1 | 500 | Overview compliance |
| **Controles** | 5 | 2.500 | SOC 2, ISO 27001, SOX, cobertura |
| **LGPD** | 5 | 2.000 | DPO, consentimentos, transferências, portal |
| **Auditoria** | 5 | 2.250 | Logs, bias, SoD, treinamentos, export |
| **Riscos** | 5 | 2.500 | Registro, seguro, continuidade, fornecedores |
| **Monitoramento** | 4 | 2.300 | Dashboard segurança, alertas, incidentes |
| **Trust Center** | 3 | 1.500 | Certificações, recursos, subprocessadores |
| **Health Check** | 1 | 500 | Status de saúde do sistema |
| **Layouts** | 2 | 450 | Layouts compartilhados |

#### 2.3.3 Configurações (~4.000 linhas)

| Página | Arquivo | Linhas | Descrição |
|--------|---------|--------|-----------|
| Overview | `configuracoes/page.tsx` | 300 | Menu de configurações |
| Comunicações | `comunicacoes/page.tsx` | 500 | Hub de comunicações |
| Templates Section | `TemplatesSection.tsx` | 400 | Gestão de templates |
| Matrix Section | `MatrixSection.tsx` | 350 | Matriz de comunicação |
| Automations | `AutomationsSection.tsx` | 350 | Automações |
| Alerts | `AlertsSection.tsx` | 300 | Configuração de alertas |
| Webhooks | `WebhooksSection.tsx` | 300 | Webhooks |
| Policies | `PoliciesSection.tsx` | 300 | Políticas |
| History | `HistorySection.tsx` | 250 | Histórico |
| Briefings | `BriefingsSection.tsx` | 250 | Briefings |
| Templates Global | `templates/page.tsx` | 400 | Templates globais |
| Políticas Global | `politicas/page.tsx` | 350 | Políticas globais |
| Auditoria Config | `auditoria/page.tsx` | 250 | Configuração auditoria |

#### 2.3.4 Métricas e Dashboards (~2.000 linhas)

| Página | Arquivo | Linhas | Descrição |
|--------|---------|--------|-----------|
| Dashboard Admin | `admin/page.tsx` | 600 | Dashboard principal |
| Métricas Plataforma | `metricas-plataforma/page.tsx` | 485 | MRR, ARR, churn agregado |
| Onboarding | `onboarding-clientes/page.tsx` | 600 | Dashboard onboarding |
| Jornada Recrutamento | `jornada-recrutamento/page.tsx` | 500 | Jornada do recrutador |

#### 2.3.5 SSO e Autenticação (~1.000 linhas)

| Página | Arquivo | Linhas | Descrição |
|--------|---------|--------|-----------|
| SSO Admin | `sso/page.tsx` | 800 | Gestão SSO com 4 tabs |
| Layout Admin | `admin/layout.tsx` | 200 | Layout com sidebar |

#### 2.3.6 Services (~4.500 linhas)

| Service | Arquivo | Linhas | Descrição |
|---------|---------|--------|-----------|
| SaaS Metrics | `saas-metrics-service.ts` | 289 | Métricas SaaS completas |
| SaaS Metrics Helpers | `saas-metrics.ts` | 200 | Funções auxiliares |
| Dashboard Service | `dashboard-service.ts` | 300 | Agregação dashboard |
| API Client | `api-client.ts` | 150 | Cliente HTTP |
| Outros Services | - | 3.500 | Diversos services |

#### 2.3.7 API Proxy (~15.500 linhas)

| Categoria | Arquivos | Linhas | Descrição |
|-----------|----------|--------|-----------|
| Billing | 7 | 1.500 | Subscription, invoices, pagamentos |
| Clients | 10 | 3.000 | CRUD clientes |
| WorkOS | 5 | 2.000 | Webhooks, SSO |
| Invitations | 3 | 500 | Sistema de convites |
| Outros | 15 | 8.500 | Diversos endpoints |

---

## 3. Mapeamento de Substituição por Ferramenta

### 3.1 Visão Geral

```
┌────────────────────────────────────────────────────────────────────┐
│                    MAPEAMENTO DE SUBSTITUIÇÃO                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐     ┌─────────────────┐                      │
│  │     STRIPE      │     │   PROFITWELL    │                      │
│  │    ~1.800 ✓     │     │    ~1.450 ✓     │                      │
│  │                 │     │                 │                      │
│  │ • Billing       │     │ • MRR/ARR       │                      │
│  │ • Invoices      │     │ • Churn         │                      │
│  │ • Subscriptions │     │ • LTV/CAC       │                      │
│  │ • Payments      │     │ • Health Score  │                      │
│  └─────────────────┘     └─────────────────┘                      │
│                                                                    │
│  ┌─────────────────┐     ┌─────────────────────────────────────┐  │
│  │     WORKOS      │     │              RETOOL                 │  │
│  │    ~3.150 ✓     │     │            ~23.800 ✓                │  │
│  │                 │     │                                     │  │
│  │ • SSO           │     │ • Admin Dashboards                  │  │
│  │ • SCIM          │     │ • Client Management                 │  │
│  │ • MFA           │     │ • Compliance Checklists             │  │
│  │ • Audit Logs    │     │ • Onboarding Flows                  │  │
│  └─────────────────┘     │ • Templates Manager                 │  │
│                          │ • Audit Logs Viewer                 │  │
│                          │ • Workflows & Automations           │  │
│                          │ • Reporting                         │  │
│                          └─────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                 MANTER EM RAILS + VUE.JS                    │  │
│  │                      ~25.500 linhas                         │  │
│  │                                                             │  │
│  │ • Core Recrutamento    • LIA Chat (IA)                      │  │
│  │ • Busca Candidatos     • Trust Center Público               │  │
│  │ • Portal LGPD          • APIs Backend                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stripe Billing (~1.800 linhas)

| Funcionalidade Atual | Arquivos | Linhas | Status |
|---------------------|----------|--------|--------|
| Gestão de Assinaturas | `billing/subscription/route.ts` | 200 | ✅ Substituível |
| Listagem de Faturas | `billing/invoices/route.ts` | 200 | ✅ Substituível |
| Detalhe de Fatura | `billing/invoices/[id]/route.ts` | 150 | ✅ Substituível |
| Pagamento de Fatura | `billing/invoices/[id]/pay/route.ts` | 100 | ✅ Substituível |
| Métodos de Pagamento | `billing/payment-methods/route.ts` | 200 | ✅ Substituível |
| Remoção de Método | `billing/payment-methods/[id]/route.ts` | 100 | ✅ Substituível |
| Resumo de Uso | `billing/usage/route.ts` | 150 | ⚠️ Parcial |
| UI de Faturamento | `[clientId]/faturamento/page.tsx` | 614 | ✅ Customer Portal |
| **TOTAL** | | **~1.800** | |

**O que Stripe oferece:**
- Customer Portal (self-service para clientes)
- Invoices automáticos
- Dunning (cobrança de inadimplentes)
- Múltiplos métodos de pagamento
- Relatórios financeiros
- Webhooks para eventos

### 3.3 ProfitWell (~1.450 linhas)

| Funcionalidade Atual | Arquivos | Linhas | Status |
|---------------------|----------|--------|--------|
| Dashboard MRR/ARR | `metricas-plataforma/page.tsx` | 485 | ✅ Substituível |
| Service Métricas | `saas-metrics-service.ts` | 289 | ✅ Substituível |
| Hook Métricas Plataforma | `usePlatformMetrics.ts` | 150 | ✅ Substituível |
| Hook SaaS Metrics | `use-saas-metrics.ts` | 100 | ✅ Substituível |
| Métricas por Cliente | `[clientId]/metricas/page.tsx` | 300 | ✅ Segmentação |
| Interfaces de Métricas | Diversos | 126 | ✅ API ProfitWell |
| **TOTAL** | | **~1.450** | |

**O que ProfitWell oferece (GRÁTIS):**
- MRR, ARR automático
- Churn rate (customer e revenue)
- LTV, CAC, ARPU
- Cohort Analysis
- Customer Signals (health score)
- Benchmarking (30k empresas)
- 107+ segmentos de filtro
- API para integração

### 3.4 WorkOS (~3.150 linhas simplificáveis)

| Funcionalidade Atual | Arquivos | Linhas | Status |
|---------------------|----------|--------|--------|
| SSO Admin Page | `sso/page.tsx` | 800 | ⚠️ Simplificar |
| SCIM Webhooks | `workos.py` | 1.200 | ✅ Manter (backend) |
| Provisioning Service | `workos_provisioning_service.py` | 600 | ✅ Manter (backend) |
| Session Refresh Hook | `useSessionRefresh.ts` | 150 | ✅ Manter |
| Audit Logs Viewer | `auditoria/logs/page.tsx` | 400 | ⚠️ WorkOS Dashboard |
| **TOTAL** | | **~3.150** | |

**Observação:** WorkOS já está integrado. O que pode ser simplificado:
- UI de SSO Admin → Deep links para WorkOS Dashboard
- Viewer de Audit Logs → Embed do WorkOS ou SIEM

### 3.5 Retool (~23.800 linhas)

#### 3.5.1 Dashboards CRUD

| Funcionalidade | Páginas | Linhas | Retool App |
|----------------|---------|--------|------------|
| Dashboard Principal | 1 | 600 | `admin-dashboard` |
| Lista de Clientes | 1 | 800 | `clients-list` |
| Detalhes do Cliente | 10 | 4.000 | `client-details` |
| Onboarding Dashboard | 1 | 600 | `onboarding-tracker` |
| **Subtotal** | 13 | **6.000** | |

#### 3.5.2 Compliance & Auditoria

| Funcionalidade | Páginas | Linhas | Retool App |
|----------------|---------|--------|------------|
| Compliance Hub | 1 | 500 | `compliance-hub` |
| Controles SOC 2/ISO/SOX | 5 | 2.500 | `compliance-controls` |
| LGPD Interno | 4 | 1.600 | `lgpd-management` |
| Auditoria | 5 | 2.250 | `audit-center` |
| Riscos | 5 | 2.500 | `risk-management` |
| Monitoramento | 4 | 2.300 | `security-monitoring` |
| Health Check | 1 | 500 | `health-check` |
| **Subtotal** | 25 | **12.150** | |

#### 3.5.3 Configurações & Templates

| Funcionalidade | Páginas | Linhas | Retool App |
|----------------|---------|--------|------------|
| Templates de Comunicação | 8 | 2.500 | `templates-manager` |
| Políticas | 1 | 350 | `policies-manager` |
| Configurações Gerais | 3 | 1.000 | `settings` |
| **Subtotal** | 12 | **3.850** | |

#### 3.5.4 Workflows & Automações

| Workflow | Substitui | Linhas | Retool Workflow |
|----------|-----------|--------|-----------------|
| Onboarding Automático | Provisionamento manual | 500 | `client-onboarding` |
| Welcome Email | Lógica de email | 200 | `welcome-email-trigger` |
| HubSpot Sync | Serviço de sync | 400 | `hubspot-sync` |
| Alertas de Churn | Monitoramento | 300 | `churn-alerts` |
| Relatórios Automáticos | Cron jobs | 400 | `scheduled-reports` |
| **Subtotal** | | **1.800** | |

**TOTAL RETOOL: ~23.800 linhas**

---

## 4. Guia Stripe Billing

### 4.1 Visão Geral

O Stripe Billing gerencia todo o ciclo de vida de assinaturas:
- Criação e gestão de planos
- Cobrança automática
- Faturas e recibos
- Customer Portal (self-service)
- Dunning (recuperação de pagamentos)
- Relatórios financeiros

### 4.2 Configuração Inicial

#### 4.2.1 Criar Conta Stripe

1. Acesse https://dashboard.stripe.com/register
2. Complete verificação de identidade
3. Configure conta brasileira para BRL
4. Ative modo de produção após testes

#### 4.2.2 Configurar Produtos e Preços

```ruby
# Rails: Criar produtos no Stripe
# config/initializers/stripe.rb
Stripe.api_key = ENV['STRIPE_SECRET_KEY']

# Criar produto
product = Stripe::Product.create({
  name: 'WeDo Talent Professional',
  description: 'Plano Professional com até 20 usuários',
  metadata: {
    plan_code: 'professional',
    max_users: '20',
    max_jobs: '25'
  }
})

# Criar preços
price_monthly = Stripe::Price.create({
  product: product.id,
  unit_amount: 299900,  # R$ 2.999,00
  currency: 'brl',
  recurring: { interval: 'month' },
  metadata: { billing_cycle: 'monthly' }
})

price_yearly = Stripe::Price.create({
  product: product.id,
  unit_amount: 2879900,  # R$ 28.799,00 (20% desconto)
  currency: 'brl',
  recurring: { interval: 'year' },
  metadata: { billing_cycle: 'yearly' }
})
```

#### 4.2.3 Estrutura de Planos Sugerida

| Plano | Preço Mensal | Preço Anual | Usuários | Vagas |
|-------|--------------|-------------|----------|-------|
| Starter | R$ 999 | R$ 9.590 | 5 | 10 |
| Professional | R$ 2.999 | R$ 28.799 | 20 | 25 |
| Enterprise | R$ 7.999 | R$ 76.799 | Ilimitado | Ilimitado |

### 4.3 Integração com Rails

#### 4.3.1 Gems Necessárias

```ruby
# Gemfile
gem 'stripe'
gem 'stripe_event'  # Para webhooks
```

#### 4.3.2 Model de Subscription

```ruby
# app/models/subscription.rb
class Subscription < ApplicationRecord
  belongs_to :client_account
  
  # Colunas: stripe_subscription_id, stripe_customer_id, 
  # status, plan_id, current_period_start, current_period_end,
  # cancel_at_period_end, canceled_at
  
  enum status: {
    trialing: 'trialing',
    active: 'active',
    past_due: 'past_due',
    canceled: 'canceled',
    unpaid: 'unpaid'
  }
  
  def sync_from_stripe!
    stripe_sub = Stripe::Subscription.retrieve(stripe_subscription_id)
    update!(
      status: stripe_sub.status,
      current_period_start: Time.at(stripe_sub.current_period_start),
      current_period_end: Time.at(stripe_sub.current_period_end),
      cancel_at_period_end: stripe_sub.cancel_at_period_end
    )
  end
end
```

#### 4.3.3 Service de Billing

```ruby
# app/services/billing_service.rb
class BillingService
  def initialize(client_account)
    @client = client_account
  end
  
  def create_customer
    customer = Stripe::Customer.create({
      email: @client.admin_email,
      name: @client.company_name,
      metadata: {
        client_id: @client.id,
        company_cnpj: @client.cnpj
      }
    })
    @client.update!(stripe_customer_id: customer.id)
    customer
  end
  
  def create_subscription(price_id)
    subscription = Stripe::Subscription.create({
      customer: @client.stripe_customer_id,
      items: [{ price: price_id }],
      payment_behavior: 'default_incomplete',
      payment_settings: { save_default_payment_method: 'on_subscription' },
      expand: ['latest_invoice.payment_intent']
    })
    
    @client.subscriptions.create!(
      stripe_subscription_id: subscription.id,
      status: subscription.status,
      plan_id: price_id
    )
    
    subscription
  end
  
  def cancel_subscription(subscription_id, immediately: false)
    if immediately
      Stripe::Subscription.cancel(subscription_id)
    else
      Stripe::Subscription.update(subscription_id, {
        cancel_at_period_end: true
      })
    end
  end
  
  def get_customer_portal_url(return_url:)
    session = Stripe::BillingPortal::Session.create({
      customer: @client.stripe_customer_id,
      return_url: return_url
    })
    session.url
  end
  
  def list_invoices(limit: 10)
    Stripe::Invoice.list({
      customer: @client.stripe_customer_id,
      limit: limit
    })
  end
end
```

### 4.4 Customer Portal

O Customer Portal do Stripe permite que clientes gerenciem suas assinaturas sem intervenção:

#### 4.4.1 Configurar Portal no Dashboard

1. Acesse **Settings > Billing > Customer Portal**
2. Configure:
   - Permitir cancelamento: Sim (com período de carência)
   - Permitir upgrade/downgrade: Sim
   - Atualizar método de pagamento: Sim
   - Ver histórico de faturas: Sim

#### 4.4.2 Endpoint de Redirecionamento

```ruby
# app/controllers/api/v1/billing_controller.rb
class Api::V1::BillingController < ApplicationController
  def customer_portal
    billing_service = BillingService.new(current_client)
    portal_url = billing_service.get_customer_portal_url(
      return_url: "#{ENV['FRONTEND_URL']}/configuracoes/faturamento"
    )
    render json: { url: portal_url }
  end
end
```

### 4.5 Webhooks

#### 4.5.1 Configurar Endpoint

```ruby
# config/routes.rb
post '/webhooks/stripe', to: 'webhooks/stripe#receive'

# app/controllers/webhooks/stripe_controller.rb
class Webhooks::StripeController < ApplicationController
  skip_before_action :verify_authenticity_token
  
  def receive
    payload = request.body.read
    sig_header = request.env['HTTP_STRIPE_SIGNATURE']
    
    begin
      event = Stripe::Webhook.construct_event(
        payload, sig_header, ENV['STRIPE_WEBHOOK_SECRET']
      )
    rescue JSON::ParserError, Stripe::SignatureVerificationError
      return head :bad_request
    end
    
    case event.type
    when 'customer.subscription.created'
      handle_subscription_created(event.data.object)
    when 'customer.subscription.updated'
      handle_subscription_updated(event.data.object)
    when 'customer.subscription.deleted'
      handle_subscription_deleted(event.data.object)
    when 'invoice.paid'
      handle_invoice_paid(event.data.object)
    when 'invoice.payment_failed'
      handle_payment_failed(event.data.object)
    end
    
    head :ok
  end
  
  private
  
  def handle_subscription_created(subscription)
    client = ClientAccount.find_by(stripe_customer_id: subscription.customer)
    return unless client
    
    client.subscriptions.create!(
      stripe_subscription_id: subscription.id,
      status: subscription.status,
      plan_id: subscription.items.data.first.price.id,
      current_period_start: Time.at(subscription.current_period_start),
      current_period_end: Time.at(subscription.current_period_end)
    )
  end
  
  def handle_subscription_updated(subscription)
    sub = Subscription.find_by(stripe_subscription_id: subscription.id)
    return unless sub
    
    sub.update!(
      status: subscription.status,
      current_period_start: Time.at(subscription.current_period_start),
      current_period_end: Time.at(subscription.current_period_end),
      cancel_at_period_end: subscription.cancel_at_period_end
    )
  end
  
  def handle_subscription_deleted(subscription)
    sub = Subscription.find_by(stripe_subscription_id: subscription.id)
    sub&.update!(status: 'canceled', canceled_at: Time.current)
  end
  
  def handle_invoice_paid(invoice)
    # Registrar pagamento, enviar recibo
    Invoice.create!(
      stripe_invoice_id: invoice.id,
      client_account_id: ClientAccount.find_by(stripe_customer_id: invoice.customer)&.id,
      amount: invoice.amount_paid,
      status: 'paid',
      paid_at: Time.at(invoice.status_transitions.paid_at)
    )
  end
  
  def handle_payment_failed(invoice)
    # Alertar sobre falha de pagamento
    client = ClientAccount.find_by(stripe_customer_id: invoice.customer)
    return unless client
    
    NotificationService.new(client).payment_failed(invoice)
  end
end
```

#### 4.5.2 Eventos a Monitorar

| Evento | Ação |
|--------|------|
| `customer.subscription.created` | Registrar nova assinatura |
| `customer.subscription.updated` | Atualizar status |
| `customer.subscription.deleted` | Marcar como cancelada |
| `invoice.paid` | Registrar pagamento |
| `invoice.payment_failed` | Alertar e iniciar dunning |
| `customer.updated` | Sincronizar dados |

### 4.6 Métodos de Pagamento Brasil

#### 4.6.1 Habilitar Métodos

No Dashboard Stripe:
1. **Settings > Payment Methods**
2. Ativar:
   - Cartões (Visa, Mastercard, Elo, Hipercard)
   - Boleto bancário
   - PIX

#### 4.6.2 Configuração de Boleto

```ruby
# Criar subscription com boleto
subscription = Stripe::Subscription.create({
  customer: customer_id,
  items: [{ price: price_id }],
  payment_settings: {
    payment_method_types: ['boleto', 'card']
  },
  collection_method: 'send_invoice',
  days_until_due: 7
})
```

### 4.7 Secrets Necessários

```bash
# .env
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

---

## 5. Guia ProfitWell (Paddle)

### 5.1 Visão Geral

ProfitWell é uma plataforma **100% gratuita** de analytics para SaaS que se integra diretamente com o Stripe para fornecer:
- MRR, ARR automático
- Churn rate (customer e revenue)
- LTV, CAC, ARPU
- Cohort Analysis
- Customer Signals (predição de churn)
- Benchmarking com 30.000+ empresas

### 5.2 Configuração Inicial

#### 5.2.1 Criar Conta

1. Acesse https://www.paddle.com/profitwell-metrics
2. Clique em "Get Started Free"
3. Complete o cadastro com email corporativo
4. Aguarde aprovação (geralmente instantânea)

#### 5.2.2 Conectar Stripe

1. No ProfitWell Dashboard, vá para **Settings > Integrations**
2. Selecione **Stripe**
3. Autorize a conexão OAuth
4. Aguarde sync inicial (pode levar algumas horas para histórico grande)

### 5.3 Métricas Disponíveis

#### 5.3.1 Métricas de Receita

| Métrica | Descrição | Fórmula |
|---------|-----------|---------|
| **MRR** | Monthly Recurring Revenue | Soma de todas as assinaturas normalizadas para mensal |
| **ARR** | Annual Recurring Revenue | MRR × 12 |
| **Net New MRR** | Novo MRR líquido | New + Expansion - Contraction - Churn |
| **Expansion MRR** | Upsells e upgrades | MRR adicional de clientes existentes |
| **Contraction MRR** | Downgrades | MRR perdido por downgrades |
| **Churned MRR** | MRR perdido | MRR de cancelamentos |

#### 5.3.2 Métricas de Clientes

| Métrica | Descrição |
|---------|-----------|
| **Active Customers** | Clientes com assinatura ativa |
| **New Customers** | Novos clientes no período |
| **Churned Customers** | Clientes que cancelaram |
| **Customer Churn Rate** | % de clientes que cancelaram |
| **Revenue Churn Rate** | % de MRR perdido |
| **Net Revenue Retention** | Retenção líquida (incluindo expansão) |

#### 5.3.3 Métricas de Valor

| Métrica | Descrição | Uso |
|---------|-----------|-----|
| **LTV** | Lifetime Value | Valor total esperado do cliente |
| **CAC** | Customer Acquisition Cost | Custo de aquisição (configurar manualmente) |
| **LTV:CAC Ratio** | Proporção LTV/CAC | Ideal > 3:1 |
| **ARPU** | Average Revenue Per User | MRR / Clientes ativos |
| **Payback Period** | Tempo para recuperar CAC | CAC / ARPU mensal |

### 5.4 Customer Signals

O recurso Customer Signals combina múltiplos indicadores para identificar:

| Signal | Descrição | Ação Sugerida |
|--------|-----------|---------------|
| **High Churn Risk** | Cliente com probabilidade de cancelar | Contato proativo |
| **Expansion Opportunity** | Cliente pronto para upgrade | Oferta de upsell |
| **Power User** | Cliente altamente engajado | Case study, referral |
| **At Risk** | Sinais de desengajamento | Reengajamento |

### 5.5 Segmentação

ProfitWell oferece 107+ segmentos pré-configurados:

#### 5.5.1 Por Plano
- Starter, Professional, Enterprise
- Mensal vs Anual
- Trial vs Pago

#### 5.5.2 Por Geografia
- País
- Região
- Timezone

#### 5.5.3 Por Comportamento
- Tempo como cliente
- Número de upgrades
- Histórico de pagamentos

### 5.6 API ProfitWell

> **Nota Importante (Janeiro 2026):** A API do ProfitWell está incluída no plano gratuito. A documentação oficial está em https://paddle.stoplight.io/docs/docs-profitwell/. Rate limits não são documentados publicamente, mas recomenda-se uso conservador (1-2 req/segundo) com exponential backoff.

#### 5.6.1 Autenticação

```bash
# Header de autenticação
# O API Token está disponível em: ProfitWell Dashboard > Settings > API
Authorization: Bearer YOUR_PROFITWELL_API_KEY
```

#### 5.6.2 Endpoints Principais

```bash
# Métricas agregadas (disponíveis no plano gratuito)
GET https://api.profitwell.com/v2/metrics/mrr
GET https://api.profitwell.com/v2/metrics/arr
GET https://api.profitwell.com/v2/metrics/churn

# Métricas por período
GET https://api.profitwell.com/v2/metrics/mrr?start_date=2025-01-01&end_date=2025-01-31

# Customers API (para export de dados)
# Docs: https://www.paddle.com/help/profitwell-metrics/export-data/customers-api
GET https://api.profitwell-events.com/v2/customers/
GET https://api.profitwell-events.com/v2/customers/{customer_id}

# Cohorts
GET https://api.profitwell.com/v2/cohorts/mrr
```

#### 5.6.3 Limitações Conhecidas

| Aspecto | Limitação |
|---------|-----------|
| **Rate Limits** | Não documentados, usar 1-2 req/s conservadoramente |
| **Customer Name** | Máx 75 caracteres |
| **Customer ID** | Máx 36 caracteres |
| **Plan ID** | Máx 48 caracteres |
| **Sync Frequency** | Dados atualizados a cada 3-6 horas |

#### 5.6.4 Alternativa: Usar Dashboard Nativo

Para muitos casos de uso, o dashboard nativo do ProfitWell é suficiente:
- Acessar via https://app.profitwell.com
- Exportar relatórios em CSV/Excel
- Configurar alertas por email
- Agendar reports automáticos para Slack

#### 5.6.5 Exemplo de Integração Rails

```ruby
# app/services/profitwell_service.rb
class ProfitwellService
  BASE_URL = 'https://api.profitwell.com/v2'
  
  def initialize
    @api_key = ENV['PROFITWELL_API_KEY']
  end
  
  def get_mrr(start_date: nil, end_date: nil)
    params = {}
    params[:start_date] = start_date.to_s if start_date
    params[:end_date] = end_date.to_s if end_date
    
    request(:get, '/metrics/mrr', params)
  end
  
  def get_churn(start_date: nil, end_date: nil)
    params = {}
    params[:start_date] = start_date.to_s if start_date
    params[:end_date] = end_date.to_s if end_date
    
    request(:get, '/metrics/churn', params)
  end
  
  def get_customer_signals
    request(:get, '/customers/signals')
  end
  
  def get_customer_metrics(customer_id)
    request(:get, "/customers/#{customer_id}/metrics")
  end
  
  private
  
  def request(method, path, params = {})
    conn = Faraday.new(url: BASE_URL) do |f|
      f.headers['Authorization'] = "Bearer #{@api_key}"
      f.headers['Content-Type'] = 'application/json'
      f.adapter Faraday.default_adapter
    end
    
    response = case method
    when :get
      conn.get(path, params)
    when :post
      conn.post(path, params.to_json)
    end
    
    JSON.parse(response.body)
  end
end
```

### 5.7 Embed de Dashboards

ProfitWell permite embedar métricas em suas próprias aplicações:

#### 5.7.1 Widget de MRR

```html
<!-- Embed MRR Widget -->
<iframe 
  src="https://app.profitwell.com/embed/mrr?api_key=YOUR_KEY"
  width="100%" 
  height="400"
  frameborder="0">
</iframe>
```

#### 5.7.2 No Retool

```javascript
// Retool - Query para ProfitWell API
const response = await fetch('https://api.profitwell.com/v2/metrics/mrr', {
  headers: {
    'Authorization': `Bearer ${PROFITWELL_API_KEY}`
  }
});
return response.json();
```

### 5.8 Comparação com Baremetrics

| Aspecto | ProfitWell | Baremetrics |
|---------|------------|-------------|
| **Preço** | Gratuito | $108-258/mês |
| **Métricas Core** | ✅ Completo | ✅ Completo |
| **Churn Types** | 1 tipo | 4 tipos |
| **Benchmarking** | 30k empresas | 600 empresas |
| **Segmentação** | 107+ filtros | Bom |
| **UI/UX** | Funcional | Superior |
| **Forecasting** | Básico | Avançado |
| **Revenue Recognition** | ✅ | ❌ |

**Recomendação:** ProfitWell para WeDo Talent (economia de $1.300-3.100/ano)

### 5.9 Secrets Necessários

```bash
# .env
PROFITWELL_API_KEY=pw_xxx
```

---

## 6. Guia WorkOS

### 6.1 Visão Geral

WorkOS já está integrado ao WeDo Talent para:
- SSO (SAML/OIDC)
- SCIM Directory Sync
- MFA
- Audit Logs

**Documentação completa:** [docs/workos_integracao_completa.md](./workos_integracao_completa.md)

### 6.2 Resumo da Integração Atual

#### 6.2.1 Componentes Implementados

| Componente | Status | Descrição |
|------------|--------|-----------|
| SSO Login | ✅ | Autenticação via SAML/OIDC |
| SCIM Webhooks | ✅ | Sincronização automática de usuários |
| Groups Sync | ✅ | Sincronização de grupos |
| Role Mapping | ✅ | Mapeamento de grupos para roles |
| Audit Logs | ✅ | Registro de eventos SSO |
| Session Refresh | ✅ | Renovação automática de sessão |
| Admin UI | ✅ | Página /admin/sso |

#### 6.2.2 Tabelas de Banco de Dados

```sql
-- Tabelas WorkOS
workos_groups              -- Grupos sincronizados
workos_group_memberships   -- Membros dos grupos
workos_group_role_mappings -- Mapeamento grupo → role
company_workos_configs     -- Configuração por empresa
sso_audit_logs            -- Logs de auditoria
```

#### 6.2.3 Endpoints de API

```
POST /api/v1/workos/webhooks/scim    -- Recebe eventos SCIM
GET  /api/v1/auth/check-sso-domain   -- Verifica domínio SSO
POST /api/v1/auth/sso/callback       -- Callback SSO
```

### 6.3 Simplificações Possíveis com Retool

#### 6.3.1 UI de SSO Admin

**Antes:** Página customizada `/admin/sso`
**Depois:** Deep links para WorkOS Dashboard

```javascript
// Retool - Botões para WorkOS Dashboard
const workosDeepLinks = {
  organizations: 'https://dashboard.workos.com/organizations',
  connections: 'https://dashboard.workos.com/sso/connections',
  directories: 'https://dashboard.workos.com/directory-sync',
  auditLogs: 'https://dashboard.workos.com/audit-logs'
};
```

#### 6.3.2 Viewer de Audit Logs

**Antes:** Página customizada com tabela
**Depois:** Query no Retool

```sql
-- Retool SQL Query
SELECT 
  event_type,
  user_email,
  ip_address,
  created_at,
  metadata
FROM sso_audit_logs
WHERE company_id = {{ currentCompanyId }}
ORDER BY created_at DESC
LIMIT 100;
```

### 6.4 Configuração para Novos Clientes

Processo de onboarding SSO:
1. Criar Organization no WorkOS
2. Configurar Connection (SAML/OIDC)
3. Configurar Directory (SCIM)
4. Mapear Groups para Roles
5. Testar login SSO

**Referência completa:** [workos_integracao_completa.md - Seção 5](./workos_integracao_completa.md#5-jornada-de-onboarding---mapeamento-completo)

### 6.5 Secrets Necessários

```bash
# .env (já configurados)
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx
WORKOS_WEBHOOK_SECRET=whsec_xxx
```

---

## 7. Guia Retool (Análise Histórica)

> ⚠️ **NOTA IMPORTANTE:** Esta seção documenta a análise inicial do Retool. Após benchmarking de HRTechs (Popp.ai, Paradox, Findem), a decisão final foi **substituir o Retool por ferramentas SaaS prontas**: HubSpot (CRM/CRUD), Arrows (onboarding), Vanta/Drata (compliance). Consulte a **Seção 13** para a stack final aprovada.

### 7.1 Visão Geral (Histórico)

Retool é uma plataforma low-code para construir ferramentas internas rapidamente. Oferece:
- Componentes drag-and-drop (50+)
- Conexão direta a bancos de dados
- APIs REST/GraphQL
- Workflows e automações
- Controle de acesso granular

### 7.2 Configuração Inicial

#### 7.2.1 Criar Conta

1. Acesse https://retool.com/
2. Clique em "Get started free"
3. Escolha plano (Free para começar, Team/Business para produção)

#### 7.2.2 Conectar Banco de Dados

**PostgreSQL (Replit/Neon):**

1. Vá para **Resources > Create new**
2. Selecione **PostgreSQL**
3. Configure:
   ```
   Name: WeDo Talent Production
   Host: <database_host>  # Ex: ep-xxx.us-east-2.aws.neon.tech
   Port: 5432
   Database: <database_name>
   Username: <username>
   Password: <password>
   SSL: Required (selecionar "require" ou "verify-full")
   ```
4. Clique em **Test Connection** para verificar
5. Salve o recurso

**Importante:** Use credenciais de read-only para queries de leitura e credenciais com permissão de escrita apenas para apps que precisam editar dados.

#### 7.2.3 Schema do Banco WeDo Talent

Tabelas principais para os apps Retool:

```sql
-- Tabelas de Clientes
client_accounts (
  id, company_name, cnpj, status, plan_name, 
  stripe_customer_id, workos_organization_id,
  welcome_email_sent, sso_configured, user_limit,
  created_at, updated_at
)

-- Tabelas de Usuários
users (
  id, client_account_id, email, full_name, role,
  is_active, last_login_at, workos_user_id,
  created_at, updated_at
)

-- Tabelas de Billing
subscriptions (
  id, client_account_id, stripe_subscription_id,
  status, plan_id, mrr, current_period_start,
  current_period_end, cancel_at_period_end
)

invoices (
  id, client_account_id, stripe_invoice_id,
  amount, status, due_date, paid_at
)

-- Tabelas de SSO
company_workos_configs (
  id, company_id, workos_organization_id,
  workos_connection_id, workos_directory_id,
  sso_enabled, scim_enabled
)

workos_groups (
  id, workos_group_id, company_id, name
)

sso_audit_logs (
  id, company_id, event_type, user_email,
  ip_address, metadata, created_at
)

-- Tabelas de Compliance
compliance_controls (
  id, framework, control_id, control_name,
  status, evidence_url, last_audit_date
)

risk_register (
  id, client_account_id, risk_name, category,
  likelihood, impact, score, mitigation, status
)
```

#### 7.2.4 Configurar APIs Externas

**WorkOS API:**
```
Name: WorkOS API
Base URL: https://api.workos.com
Headers:
  Authorization: Bearer {{ WORKOS_API_KEY }}
```

**Stripe API:**
```
Name: Stripe API
Base URL: https://api.stripe.com/v1
Headers:
  Authorization: Bearer {{ STRIPE_SECRET_KEY }}
```

**ProfitWell API:**
```
Name: ProfitWell API
Base URL: https://api.profitwell.com/v2
Headers:
  Authorization: Bearer {{ PROFITWELL_API_KEY }}
```

### 7.3 Estrutura de Apps Recomendada

```
WeDo Talent Admin (Retool)
├── 📊 admin-dashboard          # Dashboard principal
├── 👥 clients-list             # Lista de clientes
├── 📋 client-details           # Detalhes do cliente (multi-tab)
├── 🚀 onboarding-tracker       # Acompanhamento de onboarding
├── ✅ compliance-hub           # Hub de compliance
├── 📝 compliance-controls      # Checklists SOC 2/ISO/SOX
├── 🔒 lgpd-management          # Gestão LGPD interna
├── 📊 audit-center             # Centro de auditoria
├── ⚠️ risk-management          # Gestão de riscos
├── 🛡️ security-monitoring      # Monitoramento de segurança
├── 💚 health-check             # Health check do sistema
├── 📧 templates-manager        # Gestão de templates
├── ⚙️ settings                 # Configurações gerais
└── 🔄 workflows/               # Automações
    ├── client-onboarding       # Onboarding automático
    ├── welcome-email-trigger   # Envio de welcome email
    ├── hubspot-sync            # Sync com HubSpot
    ├── churn-alerts            # Alertas de churn
    └── scheduled-reports       # Relatórios programados
```

### 7.4 Templates Retool Recomendados

> **Nota:** Esta análise considera apenas o que precisa ser construído no Retool, excluindo funcionalidades já cobertas por ProfitWell (métricas SaaS), Stripe (billing/invoices) e WorkOS (SSO/SCIM/MFA).

#### 7.4.1 Mapeamento Template → Funcionalidade WeDo

| Template Retool | URL | Funcionalidade WeDo Admin | Customização Necessária |
|-----------------|-----|---------------------------|-------------------------|
| **Admin Panel** | [retool.com/use-case/admin-panel-template](https://retool.com/use-case/admin-panel-template) | clients-list, client-details, users management | Adaptar queries para schema WeDo, adicionar campos brasileiros (CNPJ) |
| **Customer Success Dashboard** | [retool.com/templates/customer-success-dashboard](https://retool.com/templates/customer-success-dashboard) | onboarding-tracker | Substituir métricas por cards de progresso de onboarding |
| **Data Visualization Dashboard** | [retool.com/templates/data-visualization-dashboard](https://retool.com/templates/data-visualization-dashboard) | compliance-hub, audit-center | Adaptar charts para frameworks compliance |

**Templates Opcionais (Fase 2+):**

| Template Retool | URL | Funcionalidade WeDo Admin | Quando Usar |
|-----------------|-----|---------------------------|-------------|
| **CRM Dashboard** | [retool.com/templates/crm-dashboard](https://retool.com/templates/crm-dashboard) | Histórico de interações, notas de clientes | Se precisar de timeline de atividades por cliente |
| **Customer Service Dashboard** | [retool.com/templates/customer-service-dashboard](https://retool.com/templates/customer-service-dashboard) | Gestão de tickets internos | Se implementar sistema de suporte interno |

#### 7.4.2 O Que NÃO Precisa no Retool (Coberto por SaaS)

| Funcionalidade | Ferramenta SaaS | Acesso |
|----------------|-----------------|--------|
| ❌ Métricas MRR/ARR/Churn | **ProfitWell** | Dashboard nativo ou API |
| ❌ Gestão de Invoices | **Stripe** | Customer Portal ou Dashboard |
| ❌ Métodos de Pagamento | **Stripe** | Customer Portal |
| ❌ Dunning/Cobrança | **Stripe** | Automático via Billing |
| ❌ SSO Configuration | **WorkOS** | Dashboard WorkOS |
| ❌ SCIM Directory Sync | **WorkOS** | Dashboard WorkOS |
| ❌ MFA Management | **WorkOS** | Dashboard WorkOS |
| ❌ SSO Audit Logs (config) | **WorkOS** | Dashboard WorkOS |

#### 7.4.3 Economia com Templates (Escopo Mínimo - 3 Templates)

| App Retool | Template Base | Sem Template | Com Template | Economia |
|------------|---------------|--------------|--------------|----------|
| admin-dashboard | Admin Panel | 3 dias | 0.5 dia | **83%** |
| clients-list | Admin Panel | 2 dias | 0.5 dia | **75%** |
| client-details | Admin Panel | 4 dias | 1 dia | **75%** |
| onboarding-tracker | Customer Success | 2 dias | 0.5 dia | **75%** |
| compliance-hub | Data Visualization | 3 dias | 1 dia | **67%** |
| audit-center | Data Visualization | 2 dias | 0.5 dia | **75%** |
| **TOTAL** | **3 Templates** | **16 dias** | **4 dias** | **75%** |

> **Nota:** Esta estimativa considera apenas os 3 templates do escopo mínimo (Admin Panel, Customer Success, Data Visualization). Os templates opcionais (CRM, Customer Service) podem adicionar 1-2 dias cada se implementados posteriormente.

#### 7.4.4 Fluxo de Implementação com Templates

```
1. Importar Template Base
   ↓
2. Conectar ao PostgreSQL WeDo Talent
   ↓
3. Substituir Queries de Exemplo pelas Queries WeDo (seções 7.5-7.9)
   ↓
4. Ajustar Componentes UI (labels em português, campos brasileiros)
   ↓
5. Configurar Permissões (roles: admin, viewer, operator)
   ↓
6. Testar e Publicar
```

#### 7.4.5 Templates: Detalhes de Implementação

##### Admin Panel Template → clients-list + client-details

**Componentes aproveitáveis do template:**
- Table com paginação, busca e filtros ✅
- Modal de criação/edição ✅
- Sidebar de detalhes ✅
- Botões de ação (edit, delete, view) ✅

**Customizações necessárias:**
```javascript
// Renomear labels
"Name" → "Razão Social"
"Email" → "Email Admin"
"Status" → "Status"

// Adicionar campos brasileiros
+ "CNPJ" (com máscara XX.XXX.XXX/XXXX-XX)
+ "Plano" (Starter, Professional, Enterprise)
+ "Limite de Usuários"
+ "SSO Configurado" (badge ✅/❌)

// Remover campos não usados
- "Address Line 2"
- "Country" (fixo: Brasil)
- "ZIP" → substituir por "CEP"
```

##### Customer Success Dashboard → onboarding-tracker

**Componentes aproveitáveis:**
- Progress bars ✅
- Status cards ✅
- Activity timeline ✅
- Alert badges ✅

**Customizações necessárias:**
```javascript
// Substituir métricas por etapas de onboarding
Etapa 1: "Welcome Email Enviado" → welcome_email_sent
Etapa 2: "WorkOS Organization Criada" → workos_organization_created  
Etapa 3: "SSO Configurado" → sso_configured
Etapa 4: "SCIM Habilitado" → scim_enabled
Etapa 5: "Primeiro Usuário Logou" → first_user_login_at
Etapa 6: "Primeira Vaga Criada" → first_job_created_at
Etapa 7: "Primeiro Candidato Avaliado" → first_candidate_evaluated_at
Etapa 8: "Treinamento Concluído" → training_completed_at

// Query para calcular progresso
SELECT 
  c.id,
  c.company_name,
  (
    CASE WHEN c.welcome_email_sent THEN 1 ELSE 0 END +
    CASE WHEN c.workos_organization_created THEN 1 ELSE 0 END +
    CASE WHEN c.sso_configured THEN 1 ELSE 0 END +
    CASE WHEN c.scim_enabled THEN 1 ELSE 0 END +
    CASE WHEN c.first_user_login_at IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN c.first_job_created_at IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN c.first_candidate_evaluated_at IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN c.training_completed_at IS NOT NULL THEN 1 ELSE 0 END
  ) as completed_steps,
  8 as total_steps,
  ROUND(
    (CASE WHEN c.welcome_email_sent THEN 1 ELSE 0 END +
     CASE WHEN c.workos_organization_created THEN 1 ELSE 0 END +
     CASE WHEN c.sso_configured THEN 1 ELSE 0 END +
     CASE WHEN c.scim_enabled THEN 1 ELSE 0 END +
     CASE WHEN c.first_user_login_at IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.first_job_created_at IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.first_candidate_evaluated_at IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN c.training_completed_at IS NOT NULL THEN 1 ELSE 0 END
    )::decimal / 8 * 100
  ) as progress_percent
FROM client_accounts c
WHERE c.status IN ('trial', 'onboarding', 'active')
ORDER BY progress_percent ASC, c.created_at DESC;
```

##### Data Visualization Dashboard → compliance-hub

**Componentes aproveitáveis:**
- Gauge charts ✅
- Stacked bar charts ✅
- Data tables ✅
- Filter dropdowns ✅

**Customizações necessárias:**
```javascript
// Substituir métricas financeiras por compliance
"Revenue" → "Controles Conformes"
"Expenses" → "Controles Não-Conformes"
"Profit" → "Score de Compliance"

// Query para dashboard de compliance
SELECT 
  cc.framework,
  COUNT(*) as total_controls,
  SUM(CASE WHEN cc.status = 'compliant' THEN 1 ELSE 0 END) as compliant,
  SUM(CASE WHEN cc.status = 'non_compliant' THEN 1 ELSE 0 END) as non_compliant,
  SUM(CASE WHEN cc.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
  ROUND(
    SUM(CASE WHEN cc.status = 'compliant' THEN 1 ELSE 0 END)::decimal / 
    COUNT(*) * 100
  ) as compliance_score
FROM compliance_controls cc
GROUP BY cc.framework
ORDER BY cc.framework;
```

#### 7.4.6 Links Diretos para Templates

| Template | Link | Tempo para Importar |
|----------|------|---------------------|
| Admin Panel | https://retool.com/use-case/admin-panel-template | 1 minuto |
| CRM Dashboard | https://retool.com/templates/crm-dashboard | 1 minuto |
| Customer Success | https://retool.com/templates/customer-success-dashboard | 1 minuto |
| Data Visualization | https://retool.com/templates/data-visualization-dashboard | 1 minuto |
| Customer Service | https://retool.com/templates/customer-service-dashboard | 1 minuto |

### 7.5 App 1: Admin Dashboard (baseado em Admin Panel Template)

#### 7.5.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  WeDo Talent Admin                                    [User ▼]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │   MRR   │ │ Clients │ │  Churn  │ │  Trial  │              │
│  │ R$245k  │ │    47   │ │  2.3%   │ │    12   │              │
│  │  +12%   │ │   +5    │ │  -0.5%  │ │   +3    │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    MRR Growth Chart                       │ │
│  │  [Line chart with last 12 months]                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────┐ ┌─────────────────────────────┐  │
│  │   Recent Activity       │ │   Onboarding Progress       │  │
│  │   • Client X signed up  │ │   ████████░░ 80% (8/10)    │  │
│  │   • Client Y upgraded   │ │   In Progress: 5            │  │
│  │   • Invoice paid        │ │   Pending SSO: 3            │  │
│  └─────────────────────────┘ └─────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.5.2 Queries

```sql
-- Total MRR (via ProfitWell ou cálculo local)
SELECT 
  SUM(s.mrr) as total_mrr,
  COUNT(DISTINCT s.client_account_id) as active_clients
FROM subscriptions s
WHERE s.status = 'active';

-- Onboarding Progress
SELECT 
  c.id,
  c.company_name,
  c.welcome_email_sent,
  c.workos_organization_created,
  c.sso_configured,
  c.created_at
FROM client_accounts c
WHERE c.status = 'onboarding'
ORDER BY c.created_at DESC;

-- Recent Activity
SELECT 
  al.event_type,
  al.description,
  al.created_at,
  c.company_name
FROM activity_logs al
JOIN client_accounts c ON c.id = al.client_account_id
ORDER BY al.created_at DESC
LIMIT 10;
```

### 7.6 App 2: Clients List (baseado em Admin Panel Template)

#### 7.6.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients                                     [+ New Client]     │
├─────────────────────────────────────────────────────────────────┤
│  [Search...] [Status ▼] [Plan ▼] [SSO ▼]                       │
├─────────────────────────────────────────────────────────────────┤
│  │ Company          │ Plan        │ MRR     │ Status   │ SSO  ││
│  ├──────────────────┼─────────────┼─────────┼──────────┼──────┤│
│  │ Banco Itaú       │ Enterprise  │ R$7.999 │ Active   │ ✅   ││
│  │ Natura           │ Professional│ R$2.999 │ Active   │ ✅   ││
│  │ Startup XYZ      │ Starter     │ R$999   │ Trial    │ ❌   ││
│  │ Tech Corp        │ Professional│ R$2.999 │ Onboard  │ ⏳   ││
│  └──────────────────┴─────────────┴─────────┴──────────┴──────┘│
│                                                                 │
│  [< Prev] Page 1 of 5 [Next >]                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.6.2 Queries

```sql
-- Lista de clientes com métricas
SELECT 
  c.id,
  c.company_name,
  c.status,
  c.plan_name,
  s.mrr,
  c.sso_configured,
  c.workos_organization_id,
  c.created_at,
  COUNT(u.id) as user_count
FROM client_accounts c
LEFT JOIN subscriptions s ON s.client_account_id = c.id AND s.status = 'active'
LEFT JOIN users u ON u.client_account_id = c.id AND u.is_active = true
WHERE 
  ({{ !searchTerm }} OR c.company_name ILIKE '%' || {{ searchTerm }} || '%')
  AND ({{ !statusFilter }} OR c.status = {{ statusFilter }})
  AND ({{ !planFilter }} OR c.plan_name = {{ planFilter }})
GROUP BY c.id, s.mrr
ORDER BY c.created_at DESC
LIMIT {{ pageSize }}
OFFSET {{ (currentPage - 1) * pageSize }};
```

### 7.7 App 3: Client Details (baseado em Admin Panel Template)

#### 7.7.1 Layout (Multi-Tab)

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back    Banco Itaú                              [Actions ▼]  │
├─────────────────────────────────────────────────────────────────┤
│  [Overview] [Users] [Billing] [SSO] [Compliance] [Logs]        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overview Tab:                                                  │
│  ┌─────────────────────────┐ ┌─────────────────────────────┐  │
│  │ Client Info             │ │ Subscription                │  │
│  │ Name: Banco Itaú        │ │ Plan: Enterprise            │  │
│  │ CNPJ: 00.000.000/0001   │ │ MRR: R$ 7.999               │  │
│  │ Admin: admin@itau.com   │ │ Status: Active              │  │
│  │ Since: Jan 2024         │ │ Next billing: Feb 1, 2026   │  │
│  └─────────────────────────┘ └─────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────┐ ┌─────────────────────────────┐  │
│  │ Usage                   │ │ Health Score                │  │
│  │ Users: 45/50            │ │ ████████░░ 85/100           │  │
│  │ Jobs: 120/unlimited     │ │ Churn Risk: Low             │  │
│  │ AI Tokens: 45k/100k     │ │ Last Login: Today           │  │
│  └─────────────────────────┘ └─────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.7.2 Tabs e Queries

**Tab: Users**
```sql
SELECT 
  u.id,
  u.full_name,
  u.email,
  u.role,
  u.is_active,
  u.last_login_at,
  u.created_at
FROM users u
WHERE u.client_account_id = {{ clientId }}
ORDER BY u.created_at DESC;
```

**Tab: Billing**
```sql
-- Invoices
SELECT 
  i.id,
  i.amount,
  i.status,
  i.due_date,
  i.paid_at,
  i.stripe_invoice_id
FROM invoices i
WHERE i.client_account_id = {{ clientId }}
ORDER BY i.created_at DESC
LIMIT 12;
```

**Tab: SSO**
```sql
-- SSO Config
SELECT 
  cwc.workos_organization_id,
  cwc.workos_connection_id,
  cwc.workos_directory_id,
  cwc.sso_enabled,
  cwc.scim_enabled,
  cwc.created_at
FROM company_workos_configs cwc
WHERE cwc.company_id = {{ clientId }};

-- SSO Audit Logs
SELECT 
  sal.event_type,
  sal.user_email,
  sal.ip_address,
  sal.created_at
FROM sso_audit_logs sal
WHERE sal.company_id = {{ clientId }}
ORDER BY sal.created_at DESC
LIMIT 50;
```

**Tab: Compliance**
```sql
-- Compliance Status
SELECT 
  framework,
  control_count,
  compliant_count,
  (compliant_count::float / control_count * 100) as compliance_percentage,
  last_audit_date
FROM compliance_status
WHERE client_account_id = {{ clientId }};
```

### 7.8 App 4: Compliance Hub (baseado em Data Visualization Template)

#### 7.8.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Compliance Hub                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ SOC 2   │ │ISO27001 │ │   SOX   │ │  LGPD   │              │
│  │  92%    │ │   88%   │ │   95%   │ │  100%   │              │
│  │ 46/50   │ │  22/25  │ │  19/20  │ │  15/15  │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                 │
│  [SOC 2] [ISO 27001] [SOX] [LGPD] [BCB 498]                    │
├─────────────────────────────────────────────────────────────────┤
│  SOC 2 Controls:                                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ID     │ Control              │ Status    │ Evidence      ││
│  ├────────┼──────────────────────┼───────────┼───────────────┤│
│  │ CC1.1  │ Security Awareness   │ ✅ Passed │ [View]        ││
│  │ CC1.2  │ Access Control       │ ✅ Passed │ [View]        ││
│  │ CC2.1  │ Change Management    │ ⚠️ Review │ [Upload]      ││
│  │ CC3.1  │ Risk Assessment      │ ✅ Passed │ [View]        ││
│  └────────┴──────────────────────┴───────────┴───────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.9 Workflows (Automações)

#### 7.9.1 Client Onboarding Workflow

```javascript
// Trigger: Webhook quando cliente é criado
// workflow: client-onboarding

// Step 1: Criar Organization no WorkOS
const workosOrg = await workosApi.createOrganization({
  name: trigger.data.company_name,
  domains: [trigger.data.domain]
});

// Step 2: Atualizar cliente com WorkOS ID
await db.query(`
  UPDATE client_accounts 
  SET workos_organization_id = $1,
      workos_organization_created = true,
      workos_organization_created_at = NOW()
  WHERE id = $2
`, [workosOrg.id, trigger.data.client_id]);

// Step 3: Criar Company no HubSpot
const hubspotCompany = await hubspotApi.createCompany({
  name: trigger.data.company_name,
  domain: trigger.data.domain,
  lia_client_id: trigger.data.client_id
});

// Step 4: Enviar Welcome Email
await emailService.send({
  template: 'welcome-client',
  to: trigger.data.admin_email,
  data: {
    company_name: trigger.data.company_name,
    admin_name: trigger.data.admin_name,
    login_url: `https://admin.wedotalent.com/login`
  }
});

// Step 5: Atualizar status
await db.query(`
  UPDATE client_accounts 
  SET welcome_email_sent = true,
      welcome_email_sent_at = NOW(),
      status = 'onboarding'
  WHERE id = $1
`, [trigger.data.client_id]);

// Step 6: Notificar time interno (Slack)
await slack.postMessage({
  channel: '#new-clients',
  text: `🎉 Novo cliente: ${trigger.data.company_name}\n` +
        `Admin: ${trigger.data.admin_email}\n` +
        `Plano: ${trigger.data.plan}`
});

return { success: true, workosOrgId: workosOrg.id };
```

#### 7.9.2 HubSpot Sync Workflow

```javascript
// Trigger: Cron - Daily at 6am
// workflow: hubspot-sync

// Step 1: Buscar clientes modificados
const modifiedClients = await db.query(`
  SELECT * FROM client_accounts
  WHERE updated_at > NOW() - INTERVAL '24 hours'
`);

// Step 2: Sync cada cliente
for (const client of modifiedClients.data) {
  // Buscar company no HubSpot
  let hubspotCompany = await hubspotApi.searchCompany({
    property: 'lia_client_id',
    value: client.id
  });
  
  // Update ou Create
  const companyData = {
    name: client.company_name,
    lia_client_id: client.id,
    lia_plan: client.plan_name,
    lia_status: client.status,
    lia_mrr: client.mrr,
    lia_users_count: client.user_count,
    lia_sso_enabled: client.sso_configured
  };
  
  if (hubspotCompany) {
    await hubspotApi.updateCompany(hubspotCompany.id, companyData);
  } else {
    await hubspotApi.createCompany(companyData);
  }
}

return { synced: modifiedClients.data.length };
```

#### 7.9.3 Churn Alert Workflow

```javascript
// Trigger: Cron - Every 6 hours
// workflow: churn-alerts

// Step 1: Identificar clientes em risco
const atRiskClients = await db.query(`
  SELECT 
    c.id,
    c.company_name,
    c.admin_email,
    c.health_score,
    c.last_login_at,
    s.mrr
  FROM client_accounts c
  JOIN subscriptions s ON s.client_account_id = c.id
  WHERE 
    c.health_score < 50
    OR c.last_login_at < NOW() - INTERVAL '14 days'
    OR s.status = 'past_due'
`);

// Step 2: Criar alertas
for (const client of atRiskClients.data) {
  const riskReasons = [];
  
  if (client.health_score < 50) {
    riskReasons.push(`Health Score baixo: ${client.health_score}`);
  }
  
  if (new Date(client.last_login_at) < new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)) {
    riskReasons.push('Sem login há 14+ dias');
  }
  
  // Criar alerta no banco
  await db.query(`
    INSERT INTO churn_alerts (client_account_id, reasons, mrr_at_risk, created_at)
    VALUES ($1, $2, $3, NOW())
  `, [client.id, riskReasons, client.mrr]);
  
  // Notificar CSM
  await slack.postMessage({
    channel: '#customer-success',
    text: `⚠️ Cliente em risco: ${client.company_name}\n` +
          `MRR: R$ ${client.mrr}\n` +
          `Motivos: ${riskReasons.join(', ')}`
  });
}

return { alertsCreated: atRiskClients.data.length };
```

### 7.10 Permissões e Controle de Acesso

#### 7.10.1 Grupos de Usuários

| Grupo | Apps Acessíveis | Permissões |
|-------|-----------------|------------|
| **Admin** | Todos | Full CRUD |
| **CS Manager** | clients-list, client-details, onboarding | Read + Limited Write |
| **Compliance** | compliance-hub, audit-center, lgpd-management | Read + Approve |
| **Finance** | clients-list (billing tab), reports | Read Only |
| **Support** | client-details (overview, logs) | Read Only |

#### 7.10.2 Configuração no Retool

1. **Settings > Access Control > Groups**
2. Criar grupos acima
3. Para cada app, definir permissões por grupo

### 7.11 Custos Estimados (Atualizado com Templates)

| Plano | Preço | Usuários | Apps | Ideal Para |
|-------|-------|----------|------|------------|
| **Free** | $0 | 5 | 3 | POC |
| **Team** | $10/user/mês | 10+ | Unlimited | Equipe pequena |
| **Business** | $50/user/mês | 10+ | Unlimited | Produção |
| **Enterprise** | Custom | Custom | Unlimited | Grandes empresas |

**Estimativa para WeDo Talent:**
- 5-10 usuários internos
- Custo: **$50-500/mês** (Team ou Business)

---

## 8. Arquitetura Final WeDo Talent 2.0

### 8.1 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEDOTALENT 2.0 ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         EXTERNAL USERS                               │   │
│  │                                                                      │   │
│  │   [Recruiters]     [Candidates]     [Client Admins]     [Public]    │   │
│  └─────────┬───────────────┬──────────────────┬──────────────┬─────────┘   │
│            │               │                  │              │             │
│            ▼               ▼                  ▼              ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    VUE.JS + VUETIFY FRONTEND                        │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│  │  │ Recruitment  │ │  Candidate   │ │   Client     │ │  Public    │  │   │
│  │  │   Portal     │ │   Portal     │ │  Settings    │ │   Pages    │  │   │
│  │  │              │ │              │ │              │ │            │  │   │
│  │  │ • Jobs       │ │ • Profile    │ │ • Team       │ │ • Trust    │  │   │
│  │  │ • Pipeline   │ │ • Apply      │ │ • SSO Config │ │   Center   │  │   │
│  │  │ • Screening  │ │ • Tests      │ │ • Billing    │ │ • LGPD     │  │   │
│  │  │ • LIA Chat   │ │ • Status     │ │ • Comms      │ │   Portal   │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       RUBY ON RAILS API                              │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│  │  │  Jobs API    │ │ Candidates   │ │   Users      │ │  Webhooks  │  │   │
│  │  │              │ │    API       │ │    API       │ │            │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│            │               │                  │              │             │
│            │               │                  │              │             │
│  ┌─────────┴───────────────┴──────────────────┴──────────────┴─────────┐   │
│  │                        POSTGRESQL DATABASE                           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         INTERNAL TEAM                                │   │
│  │                                                                      │   │
│  │   [Sales]     [CS]     [Finance]     [Compliance]     [Support]     │   │
│  └─────────┬───────┬───────────┬────────────┬──────────────┬───────────┘   │
│            │       │           │            │              │               │
│            └───────┴───────────┴────────────┴──────────────┘               │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            RETOOL                                    │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│  │  │    Admin     │ │   Clients    │ │  Compliance  │ │ Workflows  │  │   │
│  │  │  Dashboard   │ │  Management  │ │     Hub      │ │            │  │   │
│  │  │              │ │              │ │              │ │ • Onboard  │  │   │
│  │  │ • KPIs       │ │ • List       │ │ • SOC 2      │ │ • HubSpot  │  │   │
│  │  │ • Alerts     │ │ • Details    │ │ • ISO        │ │ • Alerts   │  │   │
│  │  │ • Reports    │ │ • Onboarding │ │ • LGPD       │ │ • Reports  │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│                                       │ (connects to same DB)               │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        POSTGRESQL DATABASE                           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       SAAS INTEGRATIONS                              │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │   │
│  │  │    STRIPE    │ │  PROFITWELL  │ │    WORKOS    │ │  HUBSPOT   │  │   │
│  │  │              │ │              │ │              │ │            │  │   │
│  │  │ • Billing    │ │ • MRR/ARR    │ │ • SSO        │ │ • CRM      │  │   │
│  │  │ • Invoices   │ │ • Churn      │ │ • SCIM       │ │ • Deals    │  │   │
│  │  │ • Portal     │ │ • LTV/CAC    │ │ • MFA        │ │ • Contacts │  │   │
│  │  │ • Dunning    │ │ • Signals    │ │ • Audit      │ │ • Pipeline │  │   │
│  │  │   FREE*      │ │    FREE      │ │  $125-500    │ │  Included  │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │   │
│  │                                                                      │   │
│  │  * Stripe cobra 2.9% + R$0.39 por transação                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. BILLING FLOW                                                            │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│  │  Client  │ ──▶  │  Stripe  │ ──▶  │ Webhook  │ ──▶  │   Rails  │       │
│  │ Portal   │      │ Checkout │      │          │      │    API   │       │
│  └──────────┘      └──────────┘      └──────────┘      └────┬─────┘       │
│                                                              │             │
│                           ┌──────────────────────────────────┘             │
│                           ▼                                                │
│                    ┌──────────┐      ┌──────────┐                         │
│                    │ Database │ ◀──  │ProfitWell│ (sync via Stripe)       │
│                    └──────────┘      └──────────┘                         │
│                                                                             │
│  2. SSO FLOW                                                                │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│  │   User   │ ──▶  │  WorkOS  │ ──▶  │ Callback │ ──▶  │  Vue.js  │       │
│  │  Login   │      │   SSO    │      │  Rails   │      │   App    │       │
│  └──────────┘      └──────────┘      └──────────┘      └──────────┘       │
│                           │                                                │
│                           ▼                                                │
│                    ┌──────────┐                                            │
│                    │  SCIM    │ ──▶ Auto-provision users                  │
│                    │ Webhooks │                                            │
│                    └──────────┘                                            │
│                                                                             │
│  3. ADMIN FLOW                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                         │
│  │ Internal │ ──▶  │  Retool  │ ──▶  │ Postgres │                         │
│  │   User   │      │   Apps   │      │    DB    │                         │
│  └──────────┘      └──────────┘      └──────────┘                         │
│                           │                                                │
│                           ▼                                                │
│                    ┌──────────┐      ┌──────────┐                         │
│                    │ Workflows│ ──▶  │ HubSpot  │                         │
│                    │          │      │  Slack   │                         │
│                    └──────────┘      └──────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. O que Manter em Rails + Vue.js

### 9.1 Componentes Obrigatórios

| Componente | Justificativa | Linhas Est. |
|------------|---------------|-------------|
| **Core Recrutamento** | Core business, diferencial competitivo | ~15.000 |
| **LIA Chat** | IA conversacional, proprietário | ~5.000 |
| **Busca Candidatos** | Integração Pearch específica | ~3.000 |
| **Trust Center Público** | Página pública, SEO importante | ~1.000 |
| **Portal LGPD** | Compliance, acesso público | ~400 |
| **APIs Backend** | Lógica de negócio | ~10.000 |
| **TOTAL** | | **~34.400** |

### 9.2 Detalhamento

#### 9.2.1 Core Recrutamento (Vue.js)

```
src/
├── views/
│   ├── jobs/
│   │   ├── JobsList.vue         # Lista de vagas
│   │   ├── JobCreate.vue        # Criar vaga
│   │   ├── JobDetails.vue       # Detalhes da vaga
│   │   └── JobPipeline.vue      # Pipeline de candidatos
│   ├── candidates/
│   │   ├── CandidatesList.vue   # Lista de candidatos
│   │   ├── CandidateProfile.vue # Perfil do candidato
│   │   └── CandidateEval.vue    # Avaliação
│   └── screening/
│       ├── ScreeningDashboard.vue
│       ├── InterviewSchedule.vue
│       └── FeedbackForm.vue
├── components/
│   ├── pipeline/
│   ├── filters/
│   └── charts/
└── services/
    ├── jobs.js
    ├── candidates.js
    └── screening.js
```

#### 9.2.2 LIA Chat (Vue.js + FastAPI)

```
# Vue.js Component
src/components/lia/
├── LiaChat.vue              # Container principal
├── LiaChatInput.vue         # Input de mensagem
├── LiaChatMessage.vue       # Mensagem individual
├── LiaChatSuggestions.vue   # Sugestões de ação
└── LiaChatHistory.vue       # Histórico

# FastAPI Backend (mantido)
lia-agent-system/
├── app/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── job_intake.py
│   │   ├── screening.py
│   │   └── communication.py
│   └── services/
│       ├── llm_service.py
│       └── context_service.py
```

#### 9.2.3 Trust Center Público (Vue.js)

```
src/views/public/
├── TrustCenter.vue
│   ├── CertificationsSection.vue    # SOC 2, ISO, etc.
│   ├── SecurityPractices.vue        # Práticas de segurança
│   ├── DataProcessing.vue           # Processamento de dados
│   ├── SubprocessorsList.vue        # Lista de subprocessadores
│   └── ResourcesDownload.vue        # Downloads públicos
```

#### 9.2.4 Portal LGPD (Vue.js)

```
src/views/public/lgpd/
├── DataSubjectPortal.vue
│   ├── RequestForm.vue          # Formulário de requisição
│   ├── RequestStatus.vue        # Status do pedido
│   └── DataExport.vue           # Download de dados
```

### 9.3 APIs Rails

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      # Jobs
      resources :jobs do
        resources :candidates, only: [:index, :create]
        resources :stages
        post :publish
        post :close
      end
      
      # Candidates
      resources :candidates do
        member do
          post :move_stage
          post :schedule_interview
          post :evaluate
          post :reject
          post :hire
        end
      end
      
      # Screening
      resources :screenings do
        resources :questions
        resources :responses
        post :analyze
      end
      
      # Users & Auth
      resources :users
      post 'auth/login', to: 'auth#login'
      post 'auth/sso/callback', to: 'auth#sso_callback'
      get 'auth/check-sso-domain', to: 'auth#check_sso_domain'
      
      # Webhooks
      post 'webhooks/stripe', to: 'webhooks/stripe#receive'
      post 'webhooks/workos/scim', to: 'webhooks/workos#scim'
      
      # Public
      namespace :public do
        get 'trust-center', to: 'trust_center#show'
        resources :lgpd_requests, only: [:create, :show]
      end
    end
  end
end
```

---

## 10. Roadmap de Migração

### 10.0 Impacto dos Templates Retool no Cronograma

> **Atualização Janeiro 2026:** Com o uso de templates prontos do Retool, o tempo estimado para as Fases 2 e 3 foi significativamente reduzido.

| Fase | Sem Templates | Com Templates | Economia |
|------|---------------|---------------|----------|
| **Fase 2: Retool Admin** | 2 semanas | 3-4 dias | **75%** |
| **Fase 3: Compliance** | 2 semanas | 1 semana | **50%** |
| **Total Retool** | 4 semanas | ~1.5 semanas | **62%** |

**Templates utilizados:**
- Admin Panel Template → admin-dashboard, clients-list, client-details
- Customer Success Dashboard → onboarding-tracker
- Data Visualization Dashboard → compliance-hub, audit-center

> **Nota:** Os templates CRM Dashboard e Customer Service Dashboard são opcionais e não estão incluídos no escopo mínimo. Podem ser adicionados posteriormente para funcionalidades avançadas (histórico de interações, tickets internos).

**Roadmap Revisado:** 20 semanas → **~17 semanas** (economia de ~3 semanas)

### 10.1 Fases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MIGRATION ROADMAP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: FOUNDATION (Semana 1-2)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Criar contas: Stripe, ProfitWell, Retool                          │   │
│  │ ☐ Configurar Stripe Billing (produtos, preços)                      │   │
│  │ ☐ Conectar ProfitWell ao Stripe                                     │   │
│  │ ☐ Configurar Retool e conectar ao banco de dados                    │   │
│  │ ☐ Migrar secrets para novo ambiente                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: RETOOL ADMIN (Semana 3-4)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Criar app: admin-dashboard                                        │   │
│  │ ☐ Criar app: clients-list                                           │   │
│  │ ☐ Criar app: client-details (multi-tab)                             │   │
│  │ ☐ Criar app: onboarding-tracker                                     │   │
│  │ ☐ Configurar permissões de acesso                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: COMPLIANCE (Semana 5-6)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Criar app: compliance-hub                                         │   │
│  │ ☐ Criar app: compliance-controls (SOC 2, ISO, SOX)                  │   │
│  │ ☐ Criar app: lgpd-management (interno)                              │   │
│  │ ☐ Criar app: audit-center                                           │   │
│  │ ☐ Criar app: risk-management                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: WORKFLOWS (Semana 7-8)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Criar workflow: client-onboarding                                 │   │
│  │ ☐ Criar workflow: welcome-email-trigger                             │   │
│  │ ☐ Criar workflow: hubspot-sync                                      │   │
│  │ ☐ Criar workflow: churn-alerts                                      │   │
│  │ ☐ Criar workflow: scheduled-reports                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 5: RAILS API (Semana 9-12)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Setup projeto Rails 7+                                            │   │
│  │ ☐ Migrar models e banco de dados                                    │   │
│  │ ☐ Implementar APIs de Jobs e Candidates                             │   │
│  │ ☐ Implementar integração Stripe (webhooks)                          │   │
│  │ ☐ Implementar integração WorkOS (SSO, SCIM)                         │   │
│  │ ☐ Implementar APIs públicas (Trust Center, LGPD)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 6: VUE.JS FRONTEND (Semana 13-18)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Setup projeto Vue.js 3 + Vuetify 3                                │   │
│  │ ☐ Implementar Core Recrutamento (Jobs, Candidates, Pipeline)        │   │
│  │ ☐ Implementar LIA Chat                                              │   │
│  │ ☐ Implementar Busca de Candidatos (Pearch)                          │   │
│  │ ☐ Implementar páginas públicas (Trust Center, LGPD Portal)          │   │
│  │ ☐ Implementar área de configurações do cliente                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 7: TESTING & LAUNCH (Semana 19-20)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Testes de integração                                              │   │
│  │ ☐ Testes de segurança                                               │   │
│  │ ☐ Migração de dados de produção                                     │   │
│  │ ☐ Beta com clientes selecionados                                    │   │
│  │ ☐ Go-live                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Timeline Visual

```
        Jan 2026                              Mar 2026                    Mai 2026
           │                                      │                          │
           ▼                                      ▼                          ▼
Week:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
       ├──┴──┼──┴──┼──┴──┼──┴──┼──┴──┴──┴──┼──┴──┴──┴──┴──┴──┼──┴──┤
       │     │     │     │     │           │                 │     │
       │ F1  │ F2  │ F3  │ F4  │    F5     │       F6        │ F7  │
       │     │     │     │     │           │                 │     │
       └─────┴─────┴─────┴─────┴───────────┴─────────────────┴─────┘
       
F1: Foundation (Stripe, ProfitWell, Retool setup)
F2: Retool Admin Apps
F3: Compliance Apps
F4: Workflows
F5: Rails API
F6: Vue.js Frontend
F7: Testing & Launch
```

### 10.3 Dependências

```
                    ┌─────────────────┐
                    │   Foundation    │
                    │   (Fase 1)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │ Retool   │   │ Rails    │   │  (pode   │
       │ Admin    │   │ API      │   │  começar │
       │ (Fase 2) │   │ (Fase 5) │   │  depois) │
       └────┬─────┘   └────┬─────┘   └──────────┘
            │              │
            ▼              │
       ┌──────────┐        │
       │Compliance│        │
       │ (Fase 3) │        │
       └────┬─────┘        │
            │              │
            ▼              │
       ┌──────────┐        │
       │Workflows │        │
       │ (Fase 4) │        │
       └──────────┘        │
                           │
                           ▼
                    ┌──────────┐
                    │ Vue.js   │
                    │ Frontend │
                    │ (Fase 6) │
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
                    │ Testing  │
                    │ & Launch │
                    │ (Fase 7) │
                    └──────────┘
```

---

## 11. Análise de Custos

### 11.1 Custo de Desenvolvimento

#### 11.1.1 Cenário SEM Stack SaaS

| Item | Dias | Custo/Dia | Total |
|------|------|-----------|-------|
| Admin Completo (72 páginas) | 45 | R$ 1.200 | R$ 54.000 |
| Services e APIs | 20 | R$ 1.200 | R$ 24.000 |
| Billing System | 10 | R$ 1.200 | R$ 12.000 |
| Métricas SaaS | 8 | R$ 1.200 | R$ 9.600 |
| Core Recrutamento | 25 | R$ 1.200 | R$ 30.000 |
| LIA Chat | 15 | R$ 1.200 | R$ 18.000 |
| **TOTAL** | **123 dias** | | **R$ 147.600** |

#### 11.1.2 Cenário COM Stack SaaS

| Item | Dias | Custo/Dia | Total |
|------|------|-----------|-------|
| Foundation (setup) | 5 | R$ 1.200 | R$ 6.000 |
| Retool Apps | 10 | R$ 1.200 | R$ 12.000 |
| Rails API | 20 | R$ 1.200 | R$ 24.000 |
| Vue.js Core | 25 | R$ 1.200 | R$ 30.000 |
| Integrações | 5 | R$ 1.200 | R$ 6.000 |
| **TOTAL** | **65 dias** | | **R$ 78.000** |

#### 11.1.3 Economia

| Métrica | Sem Stack | Com Stack | Economia |
|---------|-----------|-----------|----------|
| Dias de desenvolvimento | 123 | 65 | **58 dias (47%)** |
| Custo de desenvolvimento | R$ 147.600 | R$ 78.000 | **R$ 69.600** |

### 11.2 Custos Mensais da Stack

| Serviço | Custo Mensal | Observação |
|---------|--------------|------------|
| **Stripe** | ~R$ 1.000-3.000 | 2.9% + R$0.39/tx (varia com volume) |
| **ProfitWell** | R$ 0 | Gratuito |
| **WorkOS** | R$ 625-2.500 | $125-500 USD |
| **Retool** | R$ 250-2.500 | $50-500 USD (5-10 users) |
| **TOTAL** | **R$ 1.875-8.000** | |

### 11.3 ROI da Migração

| Ano | Custo Desenvolvimento | Custo Stack | Total | vs Sem Stack |
|-----|----------------------|-------------|-------|--------------|
| **Ano 1** | R$ 78.000 | R$ 48.000 | R$ 126.000 | - |
| **Sem Stack Ano 1** | R$ 147.600 | R$ 0 | R$ 147.600 | R$ 21.600 economia |
| **Ano 2** | R$ 0 | R$ 48.000 | R$ 48.000 | - |
| **Sem Stack Ano 2** | R$ 30.000 (manutenção) | R$ 0 | R$ 30.000 | R$ 18.000 mais caro |

**Break-even:** ~18 meses

**Benefícios intangíveis:**
- Menor manutenção de código
- Atualizações automáticas (Stripe, ProfitWell, WorkOS)
- Flexibilidade do Retool para mudanças rápidas
- Melhor observabilidade e métricas

---

## 12. Análise de Riscos da Estratégia SaaS

### 12.1 Matriz de Riscos

| Risco | Probabilidade | Impacto | Nível | Mitigação |
|-------|---------------|---------|-------|-----------|
| **Vendor Lock-in** | Média | Alto | 🔴 Crítico | Cláusulas contratuais, backups de metadata, paridade Rails/Vue |
| **Escalabilidade** | Média | Médio | 🟡 Moderado | Read replicas, paginação, testes de carga |
| **Segurança/Compliance** | Média | Alto | 🔴 Crítico | Verificar residência de dados Brasil, SOC 2 Retool |
| **Custos Crescentes** | Média | Médio | 🟡 Moderado | Governança de seats, revisão anual build-vs-buy |
| **Dívida Técnica** | Média | Médio | 🟡 Moderado | Contratos de API, design system compartilhado |

### 12.2 Detalhamento dos Riscos

#### 12.2.1 Vendor Lock-in (Dependência do Fornecedor)

**Descrição:** Apps e workflows do Retool são armazenados em formato proprietário. Se o Retool mudar preços drasticamente ou for descontinuado, há custos significativos de replatformização.

**Impacto:**
- Custo de migração estimado: R$ 80.000-120.000 para reconstruir em Rails/Vue
- Tempo de migração: 4-6 semanas
- Risco de interrupção de operações

**Mitigações:**
1. **Contrato Enterprise** com cláusulas de:
   - Limite de aumento de preço (máx 15%/ano)
   - SLA com penalidades (99.9% uptime)
   - Período de transição mínimo de 12 meses em caso de descontinuação
2. **Backups automáticos** via Retool API (exportar apps semanalmente)
3. **Manter paridade crítica** - workflows mais importantes também funcionam via Rails/API

#### 12.2.2 Escalabilidade

**Descrição:** Retool tem limites de rate (~5 req/seg por recurso) e performance degrada com datasets grandes (>50k linhas).

**Impacto:**
- Lentidão para operadores internos
- Timeouts em relatórios complexos
- Limite de ~150 usuários simultâneos

**Mitigações:**
1. **Read Replicas** - Conectar Retool a réplicas de leitura do banco
2. **Materialized Views** - Pré-calcular dados agregados para dashboards
3. **Paginação obrigatória** - Nunca carregar mais de 1.000 registros por query
4. **Testes de carga** - Validar com 150+ usuários antes do go-live

#### 12.2.3 Segurança e Compliance

**Descrição:** Clientes bancários exigem SOC 2 Type II e BCB 498/2025. Dados podem precisar residir no Brasil.

**Impacto:**
- Perda de deals enterprise se compliance não for atendido
- Multas regulatórias

**Mitigações:**
1. **Verificar Retool Enterprise:**
   - Confirmar certificação SOC 2 Type II
   - Confirmar opção de data residency (São Paulo ou aprovado por BCB)
   - Documentar em contrato
2. **Controle de Acesso:**
   - Integrar Retool com WorkOS SSO/SCIM
   - RBAC granular por app e por query
   - Forçar MFA para todos os operadores
3. **Audit Logs:**
   - Logs do Retool + logs adicionais em Rails SIEM
   - Retenção mínima de 5 anos
4. **Pentests:** Testes de penetração anuais incluindo apps Retool

#### 12.2.4 Custos Crescentes

**Descrição:** Retool cobra por "editor" ($50-125/mês cada). Crescimento do time interno pode aumentar custos significativamente.

**Projeção de Custos:**

| Usuários Internos | Custo Mensal USD | Custo Anual BRL |
|-------------------|------------------|-----------------|
| 5 (atual) | $250-625 | R$ 15.000-37.500 |
| 10 | $500-1.250 | R$ 30.000-75.000 |
| 20 | $1.000-2.500 | R$ 60.000-150.000 |
| 40+ | $2.000-5.000 | R$ 120.000-300.000 |

**Mitigações:**
1. **Governança de Seats:**
   - Aprovar novos acessos via processo formal
   - Usar "Viewers" (grátis) quando possível vs "Editors"
   - Revisar acessos trimestralmente
2. **Dashboard de Custos:** Monitorar usage em tempo real
3. **Revisão Anual:** Comparar custo Retool vs custo de desenvolvimento interno
   - Se custo Retool > R$ 100.000/ano, avaliar migração parcial

#### 12.2.5 Dívida Técnica

**Descrição:** Stack híbrida (Rails + Vue + Retool) aumenta complexidade e fragmenta conhecimento do time.

**Impacto:**
- Curva de aprendizado para novos devs
- Duplicação de regras de validação
- Integração frágil entre sistemas

**Mitigações:**
1. **API-First:** Rails é fonte única de verdade; Retool só consome APIs
2. **Schema Compartilhado:** Validações definidas em um lugar, usadas em todos
3. **Documentação:**
   - Manter diagrama de dependências Retool ↔ Rails atualizado
   - Runbooks para troubleshooting
4. **Treinamento Cruzado:**
   - Todo dev conhece básico de Retool
   - Design reviews de apps Retool no sprint

### 12.3 Plano de Contingência (Exit Strategy)

**Se precisar sair do Retool:**

| Fase | Ação | Prazo |
|------|------|-------|
| **Imediato** | Exportar todos os apps via API | 1 dia |
| **Semana 1-2** | Priorizar apps críticos (clients-list, onboarding) | 2 semanas |
| **Semana 3-6** | Reconstruir em Rails/Vue usando queries já documentadas | 4 semanas |
| **Semana 7-8** | Migrar compliance apps | 2 semanas |

**Custo estimado de saída:** R$ 80.000-120.000
**Tempo estimado:** 8-12 semanas

### 12.4 Ferramentas SaaS Prontas vs Retool

Antes de considerar ferramentas low-code, é importante avaliar se **ferramentas SaaS prontas** já resolvem as necessidades, assim como ProfitWell já resolve métricas SaaS.

#### 12.4.1 Mapeamento: O Que o Retool Faria vs Ferramentas Prontas

| Funcionalidade Retool | Descrição | Ferramenta SaaS Pronta | Já Temos? |
|-----------------------|-----------|------------------------|-----------|
| **admin-dashboard** | Visão geral de clientes, métricas | HubSpot CRM Dashboard | ✅ Integrado |
| **clients-list** | CRUD de clientes, listagem | HubSpot Companies | ✅ Integrado |
| **client-details** | Detalhes, edição de cliente | HubSpot Company Record | ✅ Integrado |
| **onboarding-tracker** | Acompanhar progresso de onboarding | **OnRamp** ou **Arrows** | ❌ Avaliar |
| **compliance-hub** | Status de compliance, frameworks | **Vanta** ou **Drata** | ❌ Avaliar |
| **audit-center** | Logs de auditoria, eventos | **Vanta/Drata** (incluído) | ❌ Avaliar |
| **Métricas SaaS** | MRR, Churn, LTV, ARR | ProfitWell (grátis) | ✅ Planejado |
| **Billing/Invoices** | Faturas, assinaturas | Stripe Dashboard | ✅ Planejado |

**Conclusão:** 5 de 8 funcionalidades já são cobertas por HubSpot + ProfitWell + Stripe!

#### 12.4.2 Ferramentas Prontas Recomendadas

##### 🎯 Para Onboarding de Clientes

| Ferramenta | Preço | Integra com HubSpot | Recursos |
|------------|-------|---------------------|----------|
| **Arrows** 🥇 | $500-1.250/mês | ✅ Nativo (feito para HubSpot) | Planos de onboarding, progresso em tempo real, timeline no CRM |
| **OnRamp** | Custom | ✅ Sync bidirecional | Portais clientes, workflows condicionais, alertas |
| **Dock** | ~$39/user/mês | ✅ Sync | Workspaces branded, sem login necessário |
| **Rocketlane** | $19-49/user/mês | ✅ | Gestão de projetos + colaboração |

**Recomendação:** **Arrows** - já integra nativamente com HubSpot que vocês já usam.

##### 🔒 Para Compliance e Auditoria

| Ferramenta | Preço/ano | Recursos | Certificações |
|------------|-----------|----------|---------------|
| **Vanta** 🥇 | Custom (~$7-12k) | 100+ integrações, Trust Center, coleta automática de evidências | SOC 2, ISO 27001, HIPAA |
| **Drata** | ~$7-12k | 75+ integrações, testes horários, monitoramento contínuo | SOC 2, ISO 27001 |
| **Scrut** | Custom | 80+ integrações, pronto em 6 semanas | SOC 2, GDPR, LGPD |
| **Sprinto** | Custom | Foco em automação, bom para startups | SOC 2, ISO 27001 |

**Recomendação:** **Vanta** ou **Drata** - cobrem compliance + audit logs em uma única ferramenta.

#### 12.4.3 Stack Completa com Ferramentas Prontas (Zero Retool)

| Necessidade | Ferramenta | Custo Estimado/ano |
|-------------|------------|-------------------|
| **CRM + Clientes** | HubSpot (já temos) | Incluído |
| **Métricas SaaS** | ProfitWell | **R$ 0** (grátis) |
| **Billing** | Stripe | ~2.9% + taxas |
| **SSO/SCIM** | WorkOS (já temos) | ~$125-500/mês |
| **Onboarding Tracker** | Arrows | ~$500-1.250/mês |
| **Compliance + Audit** | Vanta ou Drata | ~$7-12k/ano |

**Custo Total Anual:** ~R$ 80.000-150.000 (dependendo do plano)

#### 12.4.4 Comparação: Retool vs Ferramentas Prontas

| Critério | Retool (Low-code) | Ferramentas Prontas |
|----------|-------------------|---------------------|
| **Tempo de setup** | 2-4 semanas (construir) | 1-2 semanas (configurar) |
| **Custo inicial** | Desenvolvimento + licença | Apenas licenças |
| **Manutenção** | Time interno | Zero (SaaS gerenciado) |
| **Customização** | Total | Limitada aos recursos |
| **Integrações** | Manual (APIs) | Nativas, pré-construídas |
| **Compliance** | Você configura | Já certificado |
| **Escalabilidade** | Você gerencia | Automática |

#### 12.4.5 Análise de Custo: Retool vs Ferramentas Prontas

**Cenário: 10 usuários admin, 1 ano**

| Stack | Ano 1 | Ano 2+ | Manutenção |
|-------|-------|--------|------------|
| **Retool** | R$ 30-75k (licença) + R$ 12k (dev) | R$ 30-75k/ano | Alta (interno) |
| **Ferramentas Prontas** | R$ 80-100k (Arrows + Vanta) | R$ 80-100k/ano | Zero |

**Análise:**
- **Retool é mais barato** no Ano 1-2
- **Ferramentas Prontas** têm custo previsível e zero manutenção
- **Ferramentas Prontas** já vêm certificadas (SOC 2, etc.)

#### 12.4.6 Benchmarking: O Que as HRTechs Usam

Análise das ferramentas de compliance e segurança usadas por HRTechs de referência:

##### Popp.ai (UK - Recrutamento AI)

| Categoria | Ferramenta | Observação |
|-----------|------------|------------|
| **Compliance** | SOC 2 Type II + GDPR | Certificado |
| **Audit de Bias** | **Warden AI** | Auditorias mensais independentes |
| **Infraestrutura** | AWS + CloudFront | Enterprise-grade |
| **Integrações ATS** | **StackOne** | API unificada para 40+ ATS |
| **Criptografia** | AES-256 (rest) + TLS 1.2+ | Padrão enterprise |
| **AI Transparency** | Trust Centre público | Scores de fairness publicados |

**Diferencial:** Usam **Warden AI** para auditorias de bias de AI (95.7% gender fairness, 96.3% ethnicity fairness).

##### Findem (US - Talent Intelligence)

| Categoria | Ferramenta | Observação |
|-----------|------------|------------|
| **Compliance** | SOC 2 Type II + GDPR + ISO 27001 | Enterprise |
| **Data Sources** | 100.000+ fontes agregadas | Proprietário |
| **Infraestrutura** | AWS | Clientes: Adobe, PayPal, Nutanix |
| **Segurança** | Pentests regulares + vulnerability scans | Enterprise |

**Diferencial:** Arquitetura BI-first com "Talent Data Cloud" proprietário.

##### Paradox.ai (US - Olivia Chatbot)

| Categoria | Ferramenta | Observação |
|-----------|------------|------------|
| **Compliance** | **SOC 2 Type II + ISO 27001** | Desde 2019 |
| **GDPR** | Built-in | Privacy Shield EU-US |
| **Infraestrutura** | AWS | Multi-tenant |
| **Integrações** | Workday, SAP, ADP, Indeed | API aberta |

**Diferencial:** Não usam Vanta/Drata - têm programa interno de segurança + auditorias SOC 2 independentes anuais.

##### Resumo: O Que as HRTechs Grandes Usam

| HRTech | Vanta/Drata? | Compliance Tool | Audit de AI Bias |
|--------|--------------|-----------------|------------------|
| **Popp.ai** | ❌ Não | Programa interno | **Warden AI** |
| **Findem** | ❓ Não confirmado | Programa interno | Não público |
| **Paradox** | ❌ Não | Programa interno + auditoria externa | Não público |
| **Gupy** (BR) | ❓ Não público | - | - |

**Conclusão:** HRTechs grandes geralmente **NÃO usam** Vanta/Drata. Elas constroem programas internos de compliance e contratam auditores independentes para certificação SOC 2.

##### Alternativa Descoberta: Warden AI

**Warden AI** (usada pela Popp.ai) é especializada em **auditoria de bias de AI para recrutamento**:

| Recurso | Descrição |
|---------|-----------|
| **Foco** | Bias audit para AI de recrutamento |
| **Métricas** | Gender fairness, ethnicity fairness, age bias |
| **Frequência** | Auditorias mensais automatizadas |
| **Compliance** | EU AI Act, NYC LL144, EEOC |
| **Output** | Dashboard público de transparência |

**Relevância WeDo:** Para o módulo LIA de screening AI, considerar Warden AI para compliance com NYC LL144 e EU AI Act.

#### 12.4.7 Decisão: Quando Usar Cada Abordagem

| Use Ferramentas Prontas Se... | Use Retool/Low-code Se... |
|-------------------------------|---------------------------|
| Funcionalidades padrão atendem | Precisa de customização específica |
| Quer zero manutenção | Time técnico disponível |
| Compliance é crítico (bancos) | Budget mais limitado |
| Quer escalar sem dor de cabeça | Quer controle total |
| Já usa HubSpot/Stripe/etc. | Precisa integrar sistemas legados |

### 12.5 Alternativas Low-Code ao Retool

Existem várias alternativas no mercado, cada uma com vantagens e desvantagens:

#### 12.4.1 Comparação de Alternativas

| Ferramenta | Tipo | SOC 2 | Self-Hosted | Preço | Melhor Para |
|------------|------|-------|-------------|-------|-------------|
| **Retool** | Proprietário | ✅ | ✅ (Enterprise) | $50-125/user/mês | Baseline de comparação |
| **Appsmith** | Open-source | ✅ | ✅ Grátis | $15/user/mês ou grátis | Máximo controle + economia |
| **Budibase** | Open-source | Parcial | ✅ Grátis | $50/creator/mês | Times menores, auto-hospedado |
| **Superblocks** | Proprietário | ✅ | Híbrido | ~$55/10k workflows | Times Python, governança |
| **ToolJet** | Open-source | Parcial | ✅ Grátis | Grátis + planos pagos | Startups, features AI |
| **UI Bakery** | Proprietário | ✅ | ✅ | Custom enterprise | RBAC avançado, SSO/SAML |
| **Power Apps** | Microsoft | ✅ + HIPAA | ❌ (Azure only) | Parte do M365 | Empresas já em Microsoft |
| **DronaHQ** | Proprietário | ✅ | ✅ | Custom | 70+ conectores prontos |
| **OutSystems** | Proprietário | ✅ + ISO 27001 | ✅ | ~$36k+/ano | Enterprise legacy, alta compliance |

#### 12.4.2 Análise Detalhada - Top 3 Alternativas para WeDo

##### 🥇 Appsmith (Recomendação Principal)

**Pontos Fortes:**
- ✅ **Open-source** - código auditável, sem vendor lock-in
- ✅ **Self-hosted grátis** - dados no Brasil garantidos
- ✅ **SOC 2 Type II** nos planos pagos
- ✅ **Preço agressivo:** $15/user/mês vs $50-125 Retool
- ✅ **Git nativo** - versionamento de apps no GitHub/GitLab
- ✅ **50+ conectores** incluindo PostgreSQL, REST APIs

**Integrações WeDo:**
| Integração | Suporte Appsmith |
|------------|------------------|
| PostgreSQL (Replit) | ✅ Nativo |
| WorkOS SSO/SCIM | ✅ Via SAML/OIDC genérico |
| Stripe | ✅ Via REST API |
| ProfitWell | ✅ Via REST API |
| HubSpot | ✅ Via REST API |

**Economia vs Retool:**
| Cenário | Retool/ano | Appsmith/ano | Economia |
|---------|------------|--------------|----------|
| 5 users | R$ 15.000-37.500 | R$ 4.500 (cloud) ou R$ 0 (self-hosted) | **70-100%** |
| 10 users | R$ 30.000-75.000 | R$ 9.000 ou R$ 0 | **70-100%** |
| 20 users | R$ 60.000-150.000 | R$ 18.000 ou R$ 0 | **70-100%** |

**Riscos Appsmith:**
- ⚠️ Menos componentes prontos que Retool
- ⚠️ Comunidade menor (mas ativa)
- ⚠️ Self-hosted requer DevOps interno

##### 🥈 Budibase

**Pontos Fortes:**
- ✅ **Open-source** com visual builder intuitivo
- ✅ **Grátis** para 5 users cloud ou 20 users self-hosted
- ✅ **Automações** built-in (como Retool Workflows)
- ✅ **Fácil para não-devs** - menos código necessário

**Limitações:**
- ⚠️ SOC 2 parcial (em progresso)
- ⚠️ Menos conectores que Appsmith
- ⚠️ Menor comunidade enterprise

**Melhor para:** Times pequenos querendo começar grátis

##### 🥉 Superblocks

**Pontos Fortes:**
- ✅ **Híbrido** - dados on-prem, control plane cloud
- ✅ **SOC 2 Type II** completo
- ✅ **Python nativo** - bom para data science
- ✅ **Governança enterprise** avançada

**Limitações:**
- ⚠️ Preço similar ao Retool
- ⚠️ Menos conhecido no Brasil

**Melhor para:** Quem precisa de Python e governança, mas aceita preço similar

#### 12.4.3 Recomendação para WeDo Talent

**Curto Prazo (0-6 meses):** Iniciar com **Retool** (mais rápido para MVP)

**Médio Prazo (6-18 meses):** Avaliar migração para **Appsmith self-hosted** se:
- Custos Retool passarem de R$ 50k/ano
- Clientes bancários exigirem dados 100% on-premise Brasil
- Time DevOps estiver maduro para manter infraestrutura

**Longo Prazo (18+ meses):** Considerar **Rails/Vue puro** se:
- Volume de usuários admin passar de 50+
- Necessidade de customização extrema
- Custo-benefício de ferramentas low-code não compensar

#### 12.4.4 Tabela de Decisão

| Critério | Retool | Appsmith | Rails/Vue Puro |
|----------|--------|----------|----------------|
| **Tempo para MVP** | 2-3 semanas | 3-4 semanas | 8-12 semanas |
| **Custo Ano 1 (10 users)** | R$ 30-75k | R$ 0-9k | R$ 78k (dev) |
| **Custo Ano 2+** | R$ 30-75k/ano | R$ 0-9k/ano | ~R$ 20k (manutenção) |
| **Vendor Lock-in** | Alto | Baixo (open-source) | Nenhum |
| **Data Residency Brasil** | Via contrato | Self-hosted garantido | Garantido |
| **Curva de Aprendizado** | Baixa | Baixa | Alta |
| **Flexibilidade** | Média | Média | Total |

### 12.5 Decisão Final: Ferramentas Prontas (Sem Retool)

✅ **DECISÃO APROVADA: Substituir Retool por ferramentas SaaS prontas**

Baseado na análise de benchmarking de HRTechs e avaliação custo-benefício, a decisão final é:

| Funcionalidade | ~~Retool~~ | Ferramenta Pronta |
|----------------|------------|-------------------|
| CRUD Clientes | ~~clients-list~~ | **HubSpot Companies** |
| Dashboard Admin | ~~admin-dashboard~~ | **HubSpot Dashboard** |
| Onboarding Tracker | ~~onboarding-tracker~~ | **Arrows** |
| Compliance Hub | ~~compliance-hub~~ | **Vanta ou Drata** |
| Audit Center | ~~audit-center~~ | **Vanta ou Drata** |

**Motivo:** HRTechs de referência (Popp.ai, Paradox, Findem) não usam ferramentas low-code para admin - elas usam ferramentas SaaS prontas especializadas.

---

## 13. Stack Final Consolidada

### 13.1 Visão Geral da Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WeDo Talent 2.0 - Stack Final                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FERRAMENTAS SAAS (70%)                    │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │                                                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │   STRIPE    │  │ PROFITWELL  │  │   HUBSPOT   │          │    │
│  │  │  Pagamentos │  │Métricas SaaS│  │  CRM/CRUD   │          │    │
│  │  │   Billing   │  │   (GRÁTIS)  │  │  Clientes   │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  │                                                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │   ARROWS    │  │   WORKOS    │  │VANTA/DRATA  │          │    │
│  │  │  Onboarding │  │  SSO/SCIM   │  │ Compliance  │          │    │
│  │  │   Jornada   │  │    MFA      │  │ SOC2/ISO    │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  │                                                              │    │
│  │  ┌─────────────┐  ┌─────────────┐                           │    │
│  │  │PRIVACY TOOLS│  │  WARDEN AI  │                           │    │
│  │  │    LGPD     │  │  AI Bias    │                           │    │
│  │  │   Brasil    │  │   Audit     │                           │    │
│  │  └─────────────┘  └─────────────┘                           │    │
│  │                                                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                DESENVOLVIMENTO INTERNO (30%)                 │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │                                                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │    RAILS    │  │   VUE.JS    │  │  POSTGRES   │          │    │
│  │  │     API     │  │  Frontend   │  │  Database   │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  │                                                              │    │
│  │  Core: Recrutamento | LIA Chat | Busca Candidatos           │    │
│  │        Trust Center | Portal LGPD Público                    │    │
│  │                                                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 Detalhamento de Cada Ferramenta

#### 13.2.1 Stripe - Pagamentos e Billing

| Atributo | Valor |
|----------|-------|
| **Função** | Pagamentos, subscriptions, invoices, dunning |
| **Custo** | 2.9% + R$0.39 por transação |
| **Integrações** | ProfitWell (automática), HubSpot, WorkOS |
| **Setup** | 1-2 dias |
| **O que substitui** | ~1.800 linhas de código de billing |

**Funcionalidades Utilizadas:**
- ✅ Customer Portal (self-service para clientes)
- ✅ Billing Portal (gestão de assinaturas)
- ✅ Invoices automáticos
- ✅ Dunning (cobrança de inadimplentes)
- ✅ Webhooks para sincronização

#### 13.2.2 ProfitWell - Métricas SaaS

| Atributo | Valor |
|----------|-------|
| **Função** | MRR, Churn, LTV, ARR, NRR, CAC |
| **Custo** | **GRÁTIS** |
| **Integrações** | Stripe (automática) |
| **Setup** | 30 minutos |
| **O que substitui** | ~1.450 linhas de código de métricas |

**Funcionalidades Utilizadas:**
- ✅ Dashboard de métricas em tempo real
- ✅ Cohort analysis
- ✅ Churn analysis
- ✅ Revenue recognition
- ✅ Benchmarking contra indústria

#### 13.2.3 HubSpot - CRM e Gestão de Clientes

| Atributo | Valor |
|----------|-------|
| **Função** | CRUD clientes, dashboard, histórico |
| **Custo** | (já integrado) |
| **Integrações** | Arrows (nativa), Stripe, WorkOS |
| **Setup** | Já configurado |
| **O que substitui** | ~3.500 linhas de CRUD admin |

**Funcionalidades Utilizadas:**
- ✅ Companies (cadastro de clientes)
- ✅ Contacts (contatos por empresa)
- ✅ Deals (pipeline comercial)
- ✅ Custom Properties (campos WeDo)
- ✅ Dashboards personalizados
- ✅ Workflows de automação

**Custom Properties WeDo:**
- `lia_client_id` - ID interno
- `lia_plan` - Plano contratado
- `lia_status` - Status do cliente
- `lia_users_count` - Quantidade de usuários
- `lia_onboarding_status` - Status onboarding
- `lia_sso_enabled` - SSO ativo
- `lia_compliance_status` - Status compliance

#### 13.2.4 Arrows - Onboarding de Clientes

| Atributo | Valor |
|----------|-------|
| **Função** | Jornada de onboarding, tracking de progresso |
| **Custo** | $500-1.250/mês (~R$ 30-75k/ano) |
| **Integrações** | HubSpot (nativa) |
| **Setup** | 1-2 semanas |
| **O que substitui** | ~2.000 linhas de onboarding tracker |

**Por que Arrows:**
- ✅ **Nativo no HubSpot** (já usamos)
- ✅ Planos de onboarding com progresso em tempo real
- ✅ Timeline aparece direto no CRM
- ✅ Sem precisar construir nada
- ✅ Clientes veem seu próprio progresso

**Planos Arrows:**
| Plano | Preço/mês | Recursos |
|-------|-----------|----------|
| Growth | $500 | Básico, 1 tipo de plano |
| Business | $1.250 | Multi-planos, dynamic branching |
| Enterprise | Custom | SSO, audit logs, SLA |

#### 13.2.5 WorkOS - SSO, SCIM, MFA

| Atributo | Valor |
|----------|-------|
| **Função** | Autenticação enterprise |
| **Custo** | $125-500/mês (~R$ 7-30k/ano) |
| **Integrações** | Todas as ferramentas via SAML/OIDC |
| **Setup** | Já integrado |
| **O que substitui** | ~4.200 linhas de auth |

**Funcionalidades Utilizadas:**
- ✅ SSO (SAML, OIDC)
- ✅ SCIM Directory Sync
- ✅ MFA
- ✅ Audit Logs
- ✅ Admin Portal

**Status Atual:** ✅ Já integrado e funcionando

#### 13.2.6 Vanta ou Drata - Compliance Global

| Atributo | Vanta | Drata |
|----------|-------|-------|
| **Função** | SOC 2, ISO 27001, audit logs | SOC 2, ISO 27001, audit logs |
| **Custo** | $10-30k/ano | $7.5-25k/ano |
| **Integrações** | 100+ (AWS, GitHub, HR) | 75+ (AWS, GitHub, Okta) |
| **Setup** | 4-6 semanas | 4-6 semanas |
| **Diferencial** | Interface intuitiva, rede auditores | Automação profunda, compliance-as-code |

**Frameworks Suportados:**
- ✅ SOC 2 Type I e II
- ✅ ISO 27001
- ✅ GDPR
- ✅ HIPAA (se necessário)
- ✅ SOX (se necessário)

**Funcionalidades Utilizadas:**
- ✅ Coleta automática de evidências
- ✅ Monitoramento contínuo de controles
- ✅ Trust Center público
- ✅ Audit logs centralizados
- ✅ Vendor risk management
- ✅ Preparação para auditoria

**Recomendação:** **Vanta** para setup mais rápido, **Drata** para automação profunda

#### 13.2.7 Privacy Tools (ou DPOnet/OneTrust) - LGPD Brasil

| Atributo | Privacy Tools | DPOnet | OneTrust |
|----------|---------------|--------|----------|
| **Função** | LGPD compliance | LGPD compliance | Privacy global |
| **Origem** | 🇧🇷 Brasil | 🇧🇷 Brasil | 🇺🇸 EUA |
| **Custo** | ~R$ 15-30k/ano | ~R$ 10-25k/ano | ~R$ 50k+/ano |
| **Foco** | LGPD puro | LGPD + DPO | LGPD + GDPR + CCPA |

**Por que ferramenta específica para LGPD:**
- Vanta/Drata focam em SOC 2/ISO 27001
- LGPD tem requisitos específicos brasileiros:
  - Portal do Titular de Dados
  - RIPD (Relatório de Impacto)
  - Registro de Tratamentos
  - Notificação à ANPD

**Funcionalidades LGPD:**
- ✅ Portal do Titular (solicitações LGPD)
- ✅ Mapeamento de dados pessoais
- ✅ Inventário de tratamentos
- ✅ RIPD automatizado
- ✅ Gestão de consentimento
- ✅ Notificação de incidentes

**Recomendação:** **Privacy Tools** (brasileiro, custo-benefício)

#### 13.2.8 Warden AI - Auditoria de Bias de IA

| Atributo | Valor |
|----------|-------|
| **Função** | Auditoria de fairness em AI de recrutamento |
| **Custo** | A definir (contato comercial) |
| **Integrações** | APIs de AI/ML |
| **Setup** | 2-4 semanas |
| **Compliance** | NYC LL144, EU AI Act, EEOC |

**Por que Warden AI:**
- A LIA faz screening de candidatos com AI
- Regulações exigem auditoria de bias:
  - NYC Local Law 144 (Nova York)
  - EU AI Act (Europa)
  - EEOC Guidelines (EUA)

**Métricas Auditadas:**
- Gender fairness
- Ethnicity fairness
- Age bias
- Disability bias

**Diferencial:** Dashboard público de transparência (como Popp.ai faz)

#### 13.2.9 Sprinto - Alternativa Custo-Benefício

| Atributo | Valor |
|----------|-------|
| **Função** | Alternativa mais barata a Vanta/Drata |
| **Custo** | $6-20k/ano (~R$ 30-100k) |
| **Frameworks** | 20+ (SOC 2, ISO 27001, GDPR) |
| **Setup** | 4-6 semanas |
| **Diferencial** | Preço competitivo, bom para startups |

**Quando usar Sprinto:**
- ⚠️ Se orçamento para compliance for muito limitado
- ⚠️ Se precisar de SOC 2 rápido e barato

### 13.3 Matriz de Custos Consolidada

#### 13.3.1 Cenário Mínimo (MVP)

| Ferramenta | Custo/ano | Obrigatório? |
|------------|-----------|--------------|
| Stripe | 2.9% + taxas | ✅ Sim |
| ProfitWell | **R$ 0** | ✅ Sim |
| HubSpot | (já temos) | ✅ Sim |
| WorkOS | R$ 7.500 | ✅ Sim |
| Arrows | R$ 30.000 | ✅ Sim |
| Vanta/Drata | R$ 35.000 | ✅ Sim (clientes enterprise) |
| Privacy Tools | R$ 15.000 | ✅ Sim (LGPD) |
| Warden AI | R$ 20.000 (est.) | ⚠️ Fase 2 |
| **TOTAL MVP** | **~R$ 107.500/ano** | |

#### 13.3.2 Cenário Completo (Scale)

| Ferramenta | Custo/ano |
|------------|-----------|
| Stripe | 2.9% + taxas |
| ProfitWell | **R$ 0** |
| HubSpot | R$ 30.000 (upgrade) |
| WorkOS | R$ 30.000 |
| Arrows | R$ 75.000 |
| Vanta | R$ 60.000 |
| Privacy Tools | R$ 30.000 |
| Warden AI | R$ 40.000 (est.) |
| **TOTAL SCALE** | **~R$ 265.000/ano** |

### 13.4 Comparação: Antes vs Depois

| Métrica | Antes (Retool) | Depois (SaaS Prontas) |
|---------|----------------|----------------------|
| **Ferramentas** | 1 (Retool) | 7 especializadas |
| **Tempo Setup** | 4-6 semanas (construir) | 2-4 semanas (configurar) |
| **Manutenção** | Alta (interno) | Zero |
| **Customização** | Total | Limitada |
| **Compliance** | Você configura | Já certificado |
| **Custo Ano 1** | R$ 42-87k | R$ 107-195k |
| **Custo Ano 2+** | R$ 30-75k + dev | R$ 107-195k |
| **Risco** | Vendor lock-in Retool | Distribuído |

### 13.5 Roadmap de Implementação

#### Fase 1: Foundation (Semanas 1-2)
- [x] WorkOS (já integrado)
- [x] HubSpot (já integrado)
- [ ] Configurar Stripe Billing
- [ ] Conectar ProfitWell ao Stripe

#### Fase 2: Onboarding (Semanas 3-4)
- [ ] Contratar Arrows
- [ ] Configurar planos de onboarding
- [ ] Integrar Arrows ↔ HubSpot
- [ ] Treinar time de CS

#### Fase 3: Compliance (Semanas 5-8)
- [ ] Escolher Vanta ou Drata
- [ ] Iniciar setup de controles
- [ ] Integrar com AWS/GitHub/HR
- [ ] Contratar Privacy Tools para LGPD

#### Fase 4: AI Governance (Semanas 9-12)
- [ ] Avaliar Warden AI
- [ ] Integrar com módulo LIA
- [ ] Configurar auditorias mensais
- [ ] Publicar Trust Center de AI

#### Fase 5: Go-Live (Semana 13+)
- [ ] Revisar todas as integrações
- [ ] Treinar equipe
- [ ] Documentar processos
- [ ] Monitorar métricas

### 13.6 Checklist de Implementação

#### Pré-Requisitos
- [ ] Definir budget aprovado
- [ ] Designar owner para cada ferramenta
- [ ] Criar contas nas plataformas

#### Stripe
- [ ] Criar conta Stripe
- [ ] Configurar produtos/preços
- [ ] Ativar Customer Portal
- [ ] Configurar webhooks
- [ ] Testar fluxo de pagamento

#### ProfitWell
- [ ] Conectar ao Stripe
- [ ] Verificar métricas após 24h
- [ ] Configurar alertas

#### Arrows
- [ ] Contratar plano adequado
- [ ] Criar templates de onboarding
- [ ] Integrar com HubSpot
- [ ] Treinar time de CS

#### Vanta/Drata
- [ ] Escolher plataforma
- [ ] Iniciar assessment
- [ ] Conectar integrações (AWS, GitHub, etc.)
- [ ] Criar políticas
- [ ] Agendar auditoria SOC 2

#### Privacy Tools
- [ ] Contratar plataforma
- [ ] Mapear dados pessoais
- [ ] Configurar portal do titular
- [ ] Criar RIPD
- [ ] Treinar DPO

#### Warden AI (Fase 2)
- [ ] Avaliar necessidade
- [ ] Negociar contrato
- [ ] Integrar com LIA
- [ ] Configurar auditorias

### 13.7 O Que Será Desenvolvido Internamente (Rails + Vue.js)

Esta seção detalha os componentes que **devem ser desenvolvidos pelo time interno** por serem core do negócio ou exigirem customização específica.

#### 13.7.1 Resumo de Desenvolvimento Interno

| Componente | Linhas Estimadas | Prioridade | Prazo |
|------------|------------------|------------|-------|
| **Core Recrutamento** | ~8.000 | Alta | Fase 1-2 |
| **LIA Chat** | ~5.000 | Alta | Fase 2-3 |
| **Busca de Candidatos** | ~3.500 | Alta | Fase 2 |
| **Portal LGPD Público** | ~2.500 | Média | Fase 3 |
| **Trust Center Público** | ~2.000 | Média | Fase 3 |
| **APIs Backend** | ~4.500 | Alta | Contínuo |
| **TOTAL** | **~25.500 linhas** | | |

#### 13.7.2 Core Recrutamento

**Descrição:** Sistema central de gestão de recrutamento - é o coração do produto WeDo Talent.

**Funcionalidades:**

| Módulo | Funcionalidade | Detalhes |
|--------|---------------|----------|
| **Vagas** | CRUD de vagas | Criar, editar, publicar, arquivar vagas |
| | Job Description Generator | Geração de JD com IA |
| | Requisitos e competências | Skills, experiência, formação |
| | Workflow de aprovação | Multi-nível de aprovação |
| **Candidatos** | CRUD de candidatos | Cadastro, atualização, histórico |
| | Pipeline visual | Kanban de etapas |
| | Scoring LIA | Pontuação AI do candidato |
| | Histórico de interações | Timeline de atividades |
| **Processo Seletivo** | Etapas customizáveis | Configurar fases por vaga |
| | Agendamento | Integração Microsoft Graph |
| | Avaliações | Testes, entrevistas, pareceres |
| | Feedback estruturado | Rubricas de avaliação |

**Telas Principais:**
- `/vagas` - Lista de vagas
- `/vagas/[id]` - Detalhes da vaga
- `/vagas/nova` - Wizard de criação
- `/candidatos` - Lista de candidatos
- `/candidatos/[id]` - Perfil do candidato
- `/processo/[id]` - Gestão do processo seletivo

**Integrações:**
- Pearch API (busca de candidatos)
- ATS externos (Gupy, Pandapé, StackOne)
- Microsoft Graph (calendário)

#### 13.7.3 LIA Chat

**Descrição:** Interface conversacional principal - o diferencial do produto WeDo Talent.

**Funcionalidades:**

| Módulo | Funcionalidade | Detalhes |
|--------|---------------|----------|
| **Interface** | Chat em tempo real | WebSocket, streaming |
| | Histórico de conversas | Persistência, busca |
| | Contexto multi-sessão | Memória de conversas anteriores |
| **Intents** | Roteamento de intenções | Classificação de mensagens |
| | 15+ intents suportados | Criar vaga, buscar candidato, etc. |
| | Fallback inteligente | Quando não entende |
| **Agentes** | Job Intake Agent | Criação de vagas conversacional |
| | Screening Agent | Triagem de candidatos |
| | Scheduling Agent | Agendamento de entrevistas |
| | Communication Agent | Envio de mensagens |
| **IA** | Claude Sonnet 4.5 | Modelo principal |
| | Gemini fallback | Backup de IA |
| | Streaming responses | Respostas em tempo real |

**Telas Principais:**
- `/lia` - Interface principal do chat
- `/lia/historico` - Histórico de conversas
- `/lia/configuracoes` - Configurações do assistente

**Backend:**
- FastAPI + LangGraph (sistema multi-agente)
- Migrar para Rails Action Cable (WebSockets)
- Redis para cache de sessão

#### 13.7.4 Busca de Candidatos

**Descrição:** Sistema de busca inteligente integrado com Pearch API (800M+ perfis).

**Funcionalidades:**

| Módulo | Funcionalidade | Detalhes |
|--------|---------------|----------|
| **Busca Básica** | Filtros tradicionais | Cargo, localização, experiência |
| | Busca por texto | Full-text search |
| | Histórico de buscas | Salvar e reutilizar |
| **Busca Semântica** | Expansão de termos | Skills relacionados via LLM |
| | Sinônimos inteligentes | "Desenvolvedor" = "Programador" |
| | 8 domínios semânticos | Skills, cargos, indústrias, etc. |
| **Busca Similar** | Por perfil LinkedIn | Upload de URL |
| | Por CV | Upload de arquivo |
| | Fusão multi-perfil | Combinar vários perfis |
| **Integração Pearch** | API de busca | 800M+ candidatos |
| | Rate limiting | Controle de consumo |
| | Cache Redis | Otimização de custos |

**Telas Principais:**
- `/busca` - Interface de busca
- `/busca/avancada` - Filtros avançados
- `/busca/similar` - Busca por similaridade
- `/busca/historico` - Buscas salvas

#### 13.7.5 Portal LGPD Público

**Descrição:** Portal voltado para candidatos exercerem seus direitos sob a LGPD. Interface pública, acessível sem login.

**Funcionalidades:**

| Módulo | Funcionalidade | Detalhes |
|--------|---------------|----------|
| **Direitos do Titular** | Acesso aos dados | Ver dados pessoais armazenados |
| | Correção | Solicitar correção de dados |
| | Exclusão | Solicitar apagamento |
| | Portabilidade | Exportar dados (JSON/CSV) |
| | Revogação | Revogar consentimentos |
| **Solicitações** | Formulário de requisição | Validação por email |
| | Tracking de status | Acompanhar andamento |
| | Prazo legal (15 dias) | Alertas automáticos |
| **Transparência** | Política de privacidade | Texto legal |
| | Termos de uso | Texto legal |
| | Cookies | Gestão de cookies |
| | Finalidades | Como dados são usados |

**Telas Principais:**
- `/lgpd` - Portal principal (público)
- `/lgpd/meus-dados` - Visualizar dados (autenticado por email)
- `/lgpd/solicitar` - Nova solicitação
- `/lgpd/acompanhar` - Status da solicitação
- `/lgpd/politica` - Política de privacidade
- `/lgpd/termos` - Termos de uso

**Por que desenvolvimento interno:**
- Customização específica para contexto brasileiro
- Integração com Privacy Tools (backend)
- Branding WeDo Talent
- Controle total sobre fluxos

#### 13.7.6 Trust Center Público

**Descrição:** Página pública demonstrando compromisso com segurança e compliance.

**Funcionalidades:**

| Módulo | Funcionalidade | Detalhes |
|--------|---------------|----------|
| **Certificações** | Badges de compliance | SOC 2, ISO 27001, LGPD |
| | Relatórios sob NDA | Download mediante solicitação |
| | Histórico de auditorias | Datas e resultados |
| **Segurança** | Práticas de segurança | Criptografia, backup, etc. |
| | Arquitetura | Visão geral (sem detalhes sensíveis) |
| | Incidentes | Histórico de incidentes (se houver) |
| **AI Governance** | Dashboard de bias | Resultados Warden AI |
| | Explicabilidade | Como LIA toma decisões |
| | Human-in-the-loop | Supervisão humana |
| **Subprocessadores** | Lista de fornecedores | AWS, Anthropic, etc. |
| | Localização de dados | Onde dados são armazenados |
| | Certificações dos parceiros | SOC 2 dos fornecedores |

**Telas Principais:**
- `/trust` - Trust Center principal (público)
- `/trust/certificacoes` - Lista de certificações
- `/trust/seguranca` - Práticas de segurança
- `/trust/ia` - Governança de IA
- `/trust/subprocessadores` - Lista de fornecedores

**Por que desenvolvimento interno:**
- Branding e identidade visual WeDo
- Integração com Vanta/Drata API (puxar status)
- Customização de conteúdo
- SEO e marketing

#### 13.7.7 APIs Backend (Rails)

**Descrição:** APIs RESTful que servem todo o frontend e integrações.

**Endpoints Principais:**

| Domínio | Endpoints | Descrição |
|---------|-----------|-----------|
| **Autenticação** | `/api/v1/auth/*` | Login, logout, refresh, SSO |
| **Vagas** | `/api/v1/jobs/*` | CRUD de vagas |
| **Candidatos** | `/api/v1/candidates/*` | CRUD de candidatos |
| **Processos** | `/api/v1/processes/*` | Gestão de processos seletivos |
| **Busca** | `/api/v1/search/*` | Busca de candidatos |
| **LIA** | `/api/v1/lia/*` | Chat e agentes |
| **LGPD** | `/api/v1/lgpd/*` | Solicitações de titulares |
| **Webhooks** | `/api/v1/webhooks/*` | WorkOS, Stripe, HubSpot |
| **Admin** | `/api/v1/admin/*` | Endpoints administrativos |

**Padrões:**
- RESTful com versionamento (`/api/v1/`)
- JSON:API ou similar
- Autenticação JWT + refresh tokens
- Rate limiting por tenant
- Audit logging em todas as operações

#### 13.7.8 Cronograma de Desenvolvimento Interno

| Fase | Componente | Semanas | Equipe |
|------|------------|---------|--------|
| **1** | APIs Backend (base) | 2 | 2 devs |
| **2** | Core Recrutamento | 4 | 2 devs |
| **3** | LIA Chat | 3 | 2 devs |
| **4** | Busca de Candidatos | 2 | 1 dev |
| **5** | Portal LGPD | 2 | 1 dev |
| **6** | Trust Center | 1 | 1 dev |
| **7** | Testes e Ajustes | 2 | 2 devs |
| **TOTAL** | | **16 semanas** | |

**Custo Estimado de Desenvolvimento:**

| Item | Cálculo | Total |
|------|---------|-------|
| Desenvolvedores | 2 devs × 16 semanas × R$ 1.200/dia × 5 dias | R$ 192.000 |
| Tech Lead (parcial) | 0.5 × 16 semanas × R$ 1.500/dia × 5 dias | R$ 60.000 |
| QA | 1 × 8 semanas × R$ 800/dia × 5 dias | R$ 32.000 |
| **TOTAL** | | **R$ 284.000** |

#### 13.7.9 Dependências entre Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORDEM DE DESENVOLVIMENTO                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FASE 1: FOUNDATION                                              │
│  ┌──────────────────┐                                            │
│  │   APIs Backend   │ ← Base para tudo                          │
│  └────────┬─────────┘                                            │
│           │                                                      │
│  FASE 2: CORE                                                    │
│  ┌────────▼─────────┐    ┌──────────────────┐                   │
│  │ Core Recrutamento│    │ Busca Candidatos │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│  FASE 3: INTELIGÊNCIA             │                              │
│  ┌────────▼───────────────────────▼──────┐                      │
│  │              LIA Chat                  │                      │
│  │   (depende de Core + Busca)            │                      │
│  └────────────────────┬──────────────────┘                      │
│                       │                                          │
│  FASE 4: COMPLIANCE   │                                          │
│  ┌────────────────────▼──────────────────┐                      │
│  │   Portal LGPD    │   Trust Center      │                      │
│  │   (público)      │   (público)         │                      │
│  └───────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. Glossário

| Termo | Definição |
|-------|-----------|
| **ARR** | Annual Recurring Revenue - Receita recorrente anualizada |
| **CAC** | Customer Acquisition Cost - Custo de aquisição de cliente |
| **Churn** | Taxa de cancelamento de clientes ou receita |
| **CRUD** | Create, Read, Update, Delete - Operações básicas de dados |
| **Customer Portal** | Portal self-service do Stripe para clientes |
| **Dunning** | Processo automatizado de cobrança de inadimplentes |
| **LTV** | Lifetime Value - Valor total esperado do cliente |
| **MRR** | Monthly Recurring Revenue - Receita recorrente mensal |
| **NRR** | Net Revenue Retention - Retenção líquida de receita |
| **SCIM** | System for Cross-domain Identity Management |
| **SSO** | Single Sign-On - Login único |
| **Webhook** | Callback HTTP para notificação de eventos |

---

## Histórico de Versões

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.0 | Jan 2026 | Equipe WeDo Talent | Documento inicial com Retool |
| 2.0 | 12 Jan 2026 | Equipe WeDo Talent | **Versão Final** - Substituição de Retool por ferramentas SaaS prontas (HubSpot, Arrows, Vanta/Drata, Privacy Tools, Warden AI). Análise de riscos, benchmarking de HRTechs, stack consolidada. |

---

## Referências

### Ferramentas de Billing e Métricas
- [Stripe Billing Documentation](https://docs.stripe.com/billing)
- [ProfitWell Metrics](https://www.paddle.com/profitwell-metrics)

### Autenticação e Segurança
- [WorkOS Documentation](https://workos.com/docs)

### CRM e Onboarding
- [HubSpot Developer Docs](https://developers.hubspot.com)
- [Arrows - Customer Onboarding](https://arrows.to)

### Compliance e Auditoria
- [Vanta - SOC 2 Compliance](https://www.vanta.com)
- [Drata - Compliance Automation](https://drata.com)
- [Sprinto - Compliance Platform](https://sprinto.com)

### LGPD Brasil
- [Privacy Tools](https://privacytools.com.br)
- [DPOnet](https://www.dponet.com.br)
- [OneTrust LGPD](https://www.onetrust.com/solutions/lgpd-compliance/)

### AI Bias e Fairness
- [Warden AI](https://www.warden.ai)

### Benchmarking HRTechs
- [Popp.ai - AI Recruitment](https://www.joinpopp.com)
- [Paradox.ai - Olivia Chatbot](https://www.paradox.ai)
- [Findem - Talent Intelligence](https://www.findem.ai)

### Stack de Desenvolvimento
- [Vue.js 3 Documentation](https://vuejs.org)
- [Ruby on Rails Guides](https://guides.rubyonrails.org)
- [Vuetify 3 Documentation](https://vuetifyjs.com)

---

## Aprovação

| Nome | Cargo | Data | Assinatura |
|------|-------|------|------------|
| | CEO | | |
| | CTO | | |
| | CFO | | |

---

*Documento gerado em 12 de Janeiro de 2026*
*WeDo Talent - Transformando o futuro do recrutamento*
