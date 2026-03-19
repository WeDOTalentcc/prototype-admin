# Plano de Implementação - WedoTalent Admin

## Visão Geral

Este documento consolida o plano completo de implementação da área administrativa WedoTalent Admin, incluindo gestão de clientes B2B, observabilidade, governança e faturamento.

---

## Estrutura de Navegação (Sidebar)

```
📊 OVERVIEW
├── Dashboard Geral
└── Métricas da Plataforma

👥 GESTÃO DE CLIENTES
├── Lista de Clientes (com busca/filtros)
└── [Seletor de Cliente Ativo] ← Dropdown global no topo

📋 OPERAÇÕES DO CLIENTE (contexto do cliente selecionado)
├── Visão Geral
├── Usuários & Permissões
├── Setup Empresa
├── Jornada de Recrutamento
├── Comunicações (7 abas)
├── Integrações
├── Automações
├── Big Five & Arquétipos
└── Testes Técnicos

💰 FATURAMENTO & MÉTRICAS
├── Planos & Assinaturas
├── Faturamento
├── Consumo de IA (créditos LIA)
└── Métricas SaaS por Cliente

🛠️ OPERAÇÕES & SUPORTE
├── Implementações (onboarding)
├── Incidentes & Problemas
├── Chamados/Tickets
├── Monitoramento
└── Observabilidade

⚙️ CONFIGURAÇÕES GLOBAIS
├── Templates Padrão
├── Políticas Globais
├── Configurações do Sistema
└── Auditoria & Logs
```

---

## Arquitetura de URLs

| Área | URL | Status |
|------|-----|--------|
| Lista de Clientes | `/admin/clientes` | ✅ Implementado |
| Perfil do Cliente | `/admin/clientes/[clientId]` | ✅ Implementado |
| Usuários | `/admin/clientes/[clientId]/usuarios` | ⏳ Pendente |
| Comunicações | `/admin/clientes/[clientId]/comunicacoes` | ✅ Implementado |
| Jornada | `/admin/clientes/[clientId]/jornada` | ✅ Implementado |
| Setup | `/admin/clientes/[clientId]/setup` | ✅ Implementado |
| Faturamento | `/admin/clientes/[clientId]/faturamento` | ✅ Implementado |
| Métricas SaaS | `/admin/clientes/[clientId]/metricas` | ⏳ Pendente |
| Consumo IA | `/admin/clientes/[clientId]/consumo-ia` | ⏳ Pendente |
| Observabilidade | `/admin/clientes/[clientId]/observabilidade` | ✅ Implementado |
| Integrações | `/admin/clientes/[clientId]/integracoes` | ✅ Implementado |
| Automações | `/admin/clientes/[clientId]/automacoes` | ✅ Implementado |
| Big Five | `/admin/clientes/[clientId]/big-five` | ⏳ Pendente |
| Testes Técnicos | `/admin/clientes/[clientId]/testes` | ⏳ Pendente |

---

## Modelos de Dados

### Já Implementados ✅

| Modelo | Campos | Localização |
|--------|--------|-------------|
| `ClientAccount` | id, name, cnpj, status, plan_id, created_at | `models/client.py` |
| `Subscription` | id, company_id, plan_code, status, price_cents | `models/billing.py` |
| `Invoice` | id, company_id, amount_cents, status, due_date | `models/billing.py` |
| `PaymentMethod` | id, company_id, type, last_four, is_default | `models/billing.py` |
| `AIInferenceLog` | id, company_id, agent_type, decision, confidence | `models/observability.py` |
| `DataAccessLog` | id, company_id, user_id, data_type, operation | `models/observability.py` |
| `ConsentRecord` | id, company_id, candidate_id, consent_type, granted_at | `models/observability.py` |
| `IncidentReport` | id, company_id, severity, description, status | `models/observability.py` |
| `ModelEvaluation` | id, company_id, model_version, dimension, metric_value | `models/observability.py` |
| `ComplianceControl` | id, company_id, framework, control_code, status | `models/observability.py` |

### Pendentes ⏳

| Modelo | Campos | Propósito |
|--------|--------|-----------|
| `ClientUser` | id, client_id, user_id, role, permissions | Usuários do cliente |
| `AiConsumption` | id, client_id, type, tokens, cost, date | Consumo de IA |
| `OnboardingChecklist` | id, client_id, step, status, completed_at | Progresso de onboarding |
| `SupportTicket` | id, client_id, subject, status, priority | Chamados |

---

## APIs Implementadas

### Billing API (13 endpoints) ✅

```
GET  /api/v1/billing/status
GET  /api/v1/billing/subscriptions
GET  /api/v1/billing/subscriptions/{client_id}
POST /api/v1/billing/subscriptions
PUT  /api/v1/billing/subscriptions/{id}
DELETE /api/v1/billing/subscriptions/{id}
GET  /api/v1/billing/invoices
GET  /api/v1/billing/invoices/client/{client_id}
GET  /api/v1/billing/invoices/{id}
POST /api/v1/billing/invoices/{id}/refund
GET  /api/v1/billing/payment-methods/{client_id}
POST /api/v1/billing/payment-methods
DELETE /api/v1/billing/payment-methods/{id}
POST /api/v1/billing/webhooks/iugu
POST /api/v1/billing/webhooks/vindi
```

### Observability API (19 endpoints) ✅

```
GET  /api/v1/observability/ai-logs
GET  /api/v1/observability/ai-logs/{id}
GET  /api/v1/observability/ai-logs/stats
GET  /api/v1/observability/data-access
GET  /api/v1/observability/data-access/stats
GET  /api/v1/observability/consents
GET  /api/v1/observability/consents/{candidate_id}
POST /api/v1/observability/consents
PUT  /api/v1/observability/consents/{id}/revoke
GET  /api/v1/observability/incidents
POST /api/v1/observability/incidents
PUT  /api/v1/observability/incidents/{id}
PUT  /api/v1/observability/incidents/{id}/resolve
GET  /api/v1/observability/evaluations
GET  /api/v1/observability/evaluations/summary
GET  /api/v1/observability/compliance
GET  /api/v1/observability/compliance/summary
PUT  /api/v1/observability/compliance/{id}
GET  /api/v1/observability/dashboard
```

---

## Área de Observabilidade e Governança

### Arquitetura em 4 Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARDS (Frontend)                     │
│  Compliance Center │ AI Governance │ LGPD Console │ Health  │
├─────────────────────────────────────────────────────────────┤
│                  GOVERNANCE SERVICES (Backend)               │
│  Audit Engine │ Bias Detector │ DSR Handler │ Alert Manager │
├─────────────────────────────────────────────────────────────┤
│               OBSERVABILITY LAKEHOUSE (Storage)              │
│  audit_events │ ai_inference_logs │ consent_records │ etc   │
├─────────────────────────────────────────────────────────────┤
│                   DATA INGESTION (Collectors)                │
│  Auth Events │ AI Traces │ Data Access │ Integration Health │
└─────────────────────────────────────────────────────────────┘
```

### Dashboards (4 Tabs) ✅ Implementados

| Tab | Funcionalidades | Status |
|-----|-----------------|--------|
| **Compliance Control Center** | ISO 27001, SOC 2, LGPD progress; controles ativos/pendentes | ✅ |
| **AI Governance Monitor** | Decisões IA, override rate, bias alerts, explainability | ✅ |
| **LGPD & Privacy Console** | Consentimentos, DSRs, retenção de dados | ✅ |
| **Health & Incidents** | Uptime, integrações, incidentes abertos | ✅ |

### Indicadores por Framework

#### ISO 27001 (Segurança da Informação)
- Inventário de Ativos
- Controles de Acesso
- Incidentes de Segurança
- MTTR (Mean Time to Respond)

#### SOC 2 (Trust Services Criteria)
- Disponibilidade (SLA 99.9%)
- Integridade de Processamento
- Confidencialidade
- Privacidade

#### Ética em IA
- Bias Drift
- Fairness Parity
- Explainability Coverage
- Human-in-Loop SLA
- Override Rate

#### LGPD
- Minimização de Dados
- Consentimento Ativo
- DSR Handling
- Tempo de Resposta DSR
- Retenção de Dados

---

## Plano de Implementação por Fases

### Fase 1: Fundação ✅ COMPLETA
- [x] Criar modelo ClientAccount no backend
- [x] Implementar seletor global de cliente no header
- [x] Criar página /admin/clientes com listagem
- [x] Criar layout /admin/clientes/[clientId] com sidebar contextual
- [x] Implementar context provider para cliente selecionado

### Fase 2: Operações Core do Cliente ⏳ PARCIAL
- [x] Montar módulos existentes dentro do contexto do cliente
- [ ] Implementar gestão de usuários (ClientUser + CRUD)
- [x] Criar dashboard de visão geral do cliente
- [x] Adaptar integrações para contexto multi-tenant

### Fase 3: Faturamento & Métricas ✅ COMPLETA
- [x] Implementar modelos de billing (Subscription, Invoice, PaymentMethod)
- [x] Criar API de billing (13 endpoints)
- [x] Criar página de faturamento do cliente
- [ ] Criar dashboard de consumo de IA
- [ ] Implementar métricas SaaS por cliente

### Fase 4: Observabilidade & Governança ✅ COMPLETA
- [x] Implementar modelos de observabilidade (6 modelos)
- [x] Criar API de observabilidade (19 endpoints)
- [x] Dashboard Compliance Control Center
- [x] Dashboard AI Governance Monitor
- [x] Dashboard LGPD & Privacy Console
- [x] Dashboard Health & Incidents
- [x] Implementar segurança multi-tenant

### Fase 5: Configurações Globais ⏳ PENDENTE
- [ ] Templates padrão da plataforma
- [x] Políticas globais (parcialmente construído)
- [ ] Configurações avançadas de governança
- [ ] Sistema de auditoria expandido

---

## Próximos Passos (Prioridade)

### Alta Prioridade
1. **Gestão de Usuários do Cliente** - CRUD completo para ClientUser
2. **Dashboard de Consumo de IA** - Tracking de tokens/créditos por cliente
3. **Métricas SaaS** - MRR, churn, LTV por cliente
4. **Integrar SDKs reais** - Iugu/Vindi para billing real

### Média Prioridade
5. **Big Five Configuration** - Gestão de arquétipos por cliente
6. **Testes Técnicos** - Biblioteca de testes customizáveis
7. **Sistema de Tickets** - Integração HubSpot ou interno

### Baixa Prioridade
8. **Onboarding Tracker** - Checklist de implementação
9. **Auditoria Expandida** - Logs detalhados de todas ações
10. **Relatórios Exportáveis** - PDF/Excel para compliance

---

## Política de Retenção de Dados

| Tipo de Dado | Retenção | Motivo |
|--------------|----------|--------|
| Logs de Autenticação | 2 anos | SOC2, ISO 27001 |
| Traces de IA | 5 anos | Auditoria, explicabilidade |
| Dados de Candidatos | 2 anos após última interação | LGPD Art. 15 |
| Registros de Consentimento | 5 anos após revogação | Prova legal |
| Incidentes de Segurança | 5 anos | Regulatório |
| Métricas de Bias | Indefinido (anonimizado) | Melhoria contínua |

---

## Isolamento Multi-Tenant ✅ IMPLEMENTADO

```
┌─────────────────────────────────────────┐
│     Header: [Seletor de Cliente ▼]      │
├─────────────────────────────────────────┤
│                                         │
│  Sidebar        │    Conteúdo           │
│  (contextual    │    (filtrado por      │
│   ao cliente)   │     company_id)       │
│                 │                       │
└─────────────────────────────────────────┘
```

- [x] Todas as APIs recebem X-Company-ID via headers
- [x] Backend valida acesso (401 se header ausente)
- [x] Verificação de ownership antes de modificações
- [x] Logging de tentativas cross-tenant
- [x] Frontend armazena cliente selecionado em Context

---

## Arquivos Principais

### Backend
- `lia-agent-system/app/models/billing.py` - Modelos de billing
- `lia-agent-system/app/models/observability.py` - Modelos de observabilidade
- `lia-agent-system/app/api/v1/billing.py` - API de billing
- `lia-agent-system/app/api/v1/observability.py` - API de observabilidade
- `lia-agent-system/app/services/billing_service.py` - Serviço de billing
- `lia-agent-system/app/services/billing_providers/` - Providers Iugu/Vindi

### Frontend
- `plataforma-lia/src/app/admin/clientes/` - Área admin de clientes
- `plataforma-lia/src/app/admin/clientes/[clientId]/faturamento/page.tsx` - Faturamento
- `plataforma-lia/src/app/admin/clientes/[clientId]/observabilidade/page.tsx` - Observabilidade
- `plataforma-lia/src/contexts/ClientContext.tsx` - Context do cliente selecionado

---

*Última atualização: 18 de Dezembro de 2025*
