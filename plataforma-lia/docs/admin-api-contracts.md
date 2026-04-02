# Contratos de API — Admin (Páginas Mantidas)

> Data: 2026-04-02
> Objetivo: Documentar endpoints que o time de dev precisará implementar no `ats_api` para cada página mantida do Admin.
> Referência: Decisão em `admin-audit-decision.md`

---

## Convenções

- Base URL: `/api/v1`
- Autenticação: Bearer Token (JWT)
- Headers obrigatórios: `X-Company-Id`, `Authorization`
- Paginação: `?page=1&limit=20`
- Filtros: query params específicos por endpoint
- Respostas seguem formato: `{ "data": ..., "meta": { "total", "page", "limit" } }`
- Erros: `{ "error": { "code": "...", "message": "..." } }`

---

## ÁREA 1: VISÃO GLOBAL

### #1 Dashboard Administrativo (`/admin`)

```
GET /api/v1/admin/dashboard/summary?start_date=&end_date=
Response: {
  kpis: { mrr, arr, activeClients, totalClients, trialClients, churnRate, churnedClients, newClientsPeriod },
  newClients: [{ id, name, plan, createdAt }],
  trialClients: [{ id, name, trialEndDate, daysRemaining }],
  churnedClients: [{ id, name, plan, churnedAt, reason }]
}

GET /api/v1/admin/dashboard/service-consumption
Response: [{ service, usage, cost, trend }]
Nota: Atualmente hardcoded no frontend. Precisa de endpoint real.

GET /api/v1/admin/dashboard/activities?limit=10
Response: [{ type, title, subtitle, timestamp }]
Nota: Atualmente hardcoded. Precisa de endpoint real.
```

### #2 Métricas da Plataforma (`/admin/metricas-plataforma`)

```
GET /api/v1/admin/metrics/revenue?period=monthly
Response: { mrr, arr, mrrGrowth, arpu, ltv, history: [{ date, value }] }

GET /api/v1/admin/metrics/clients?period=monthly
Response: { total, active, trial, churned, newThisPeriod, history: [{ date, count }] }

GET /api/v1/admin/metrics/usage?period=monthly
Response: { totalTokens, totalSessions, avgSessionDuration, history: [{ date, tokens, sessions }] }

GET /api/v1/admin/metrics/costs?period=monthly
Response: { infraCost, aiApiCost, totalCost, costPerClient, history: [{ date, cost }] }
```

---

## ÁREA 2: GESTÃO DE CLIENTES

### #5 Lista de Clientes (`/admin/clientes`)

```
GET /api/v1/admin/clients?page=1&limit=12&search=&status=&plan=
Response: {
  data: [{ id, name, tradeName, cnpj, logoUrl, status, planId, usersCount, email, phone, createdAt }],
  meta: { total, page, limit, totalPages }
}

POST /api/v1/admin/clients
Body: { name, tradeName, cnpj, email, phone, planId, userLimit }
Response: { data: { id, ...client } }

PUT /api/v1/admin/clients/:id
Body: { ...partial client fields }
Response: { data: { id, ...client } }
```

### #6 Onboarding de Clientes (`/admin/onboarding-clientes`)

```
GET /api/v1/admin/clients/onboarding?status=in_progress|completed|stalled
Response: {
  data: [{
    clientId, clientName, progress, lastActivityAt, daysSinceLastActivity,
    checklist: [{ step, label, completed, completedAt }]
  }]
}
```

### #7 SSO / SCIM (`/admin/sso`)

```
GET /api/v1/workos/admin/status?company_id=
Response: { company_id, sso_enabled, scim_enabled, sso_users_count, scim_users_count, groups_count, recent_events_count, organization_id }

GET /api/v1/workos/admin/groups?company_id=
Response: [{ id, workos_id, name, directory_id, mapped_role, mapped_permissions }]

POST /api/v1/workos/admin/groups/:groupId/role-mapping?company_id=
Body: { role, permissions }
```

---

## ÁREA 3: DETALHES POR CLIENTE

### #8 Visão Geral do Cliente (`/admin/clientes/:id`)

```
GET /api/v1/admin/clients/:id
Response: { data: { id, name, trade_name, logo_url, status, plan_id, cnpj, primary_email, primary_phone, user_limit, contract_start_date, contract_end_date, ai_credits_limit, ai_credits_used, onboarding_completed, onboarding_progress } }

GET /api/v1/admin/clients/:id/metrics
Response: { active_users, total_users, open_vacancies, total_candidates, ai_credits_used, ai_credits_limit, screenings_completed, interviews_scheduled }
Nota: Atualmente mock no frontend. Precisa de endpoint real.

GET /api/v1/admin/clients/:id/activities?limit=10
Response: [{ id, type, description, timestamp, user }]
Nota: Atualmente mock. Precisa de endpoint real.
```

### #9 Usuários (`/admin/clientes/:id/usuarios`)

```
GET /api/v1/admin/clients/:id/users?page=1&limit=20&role=&status=
Response: { data: [{ id, name, email, role, status, lastLogin, createdAt }], meta: {...} }

POST /api/v1/admin/clients/:id/users
Body: { name, email, role }

PUT /api/v1/admin/clients/:id/users/:userId
Body: { role, status }

DELETE /api/v1/admin/clients/:id/users/:userId
```

### #10 Setup Empresa (`/admin/clientes/:id/setup`)

```
GET /api/v1/admin/clients/:id/company-profile
Response: { profile, departments, benefits, culture, evpInsights }

PUT /api/v1/admin/clients/:id/company-profile
Body: { ...partial profile fields }
```

### #11 Jornada Recrutamento (`/admin/clientes/:id/jornada`)

```
GET /api/v1/admin/clients/:id/recruitment-pipeline
Response: { stages: [{ id, name, order, automations, isActive }] }

PUT /api/v1/admin/clients/:id/recruitment-pipeline
Body: { stages: [...] }
```

### #13 Integrações (`/admin/clientes/:id/integracoes`)

```
GET /api/v1/admin/clients/:id/integrations
Response: [{ id, provider, status, connectedAt, lastSync, config }]

POST /api/v1/admin/clients/:id/integrations
Body: { provider, config }

DELETE /api/v1/admin/clients/:id/integrations/:integrationId
```

### #17 Comunicações (`/admin/clientes/:id/comunicacoes`)

```
GET /api/v1/admin/clients/:id/communication-templates
Response: [{ id, name, type, channel, subject, body, isActive, createdAt }]

PUT /api/v1/admin/clients/:id/communication-templates/:templateId
Body: { ...template fields }
```

### #18 Faturamento (`/admin/clientes/:id/faturamento`)

```
GET /api/v1/admin/clients/:id/billing
Response: { plan, billingCycle, invoices: [{ id, amount, status, dueDate, paidAt }], paymentMethod }

GET /api/v1/admin/clients/:id/billing/invoices?page=1&limit=20
Response: { data: [{ id, number, amount, status, issuedAt, dueDate, paidAt }], meta: {...} }
```

### #19 Consumo de IA (`/admin/clientes/:id/consumo-ia`)

```
GET /api/v1/admin/clients/:id/ai-consumption?period=monthly
Response: {
  totalTokens, totalCost, creditUsed, creditLimit,
  byAgent: [{ agent, tokens, cost, executions }],
  history: [{ date, tokens, cost }]
}
```

### #20 Métricas SaaS (`/admin/clientes/:id/metricas`)

```
GET /api/v1/admin/clients/:id/saas-metrics
Response: {
  healthScore, churnRisk, engagementScore, nps,
  usageMetrics: { dailyActiveUsers, weeklyActiveUsers, featureAdoption },
  history: [{ date, healthScore, engagement }]
}
```

### #22 Conformidade do Cliente (`/admin/clientes/:id/conformidade`)

```
GET /api/v1/admin/clients/:id/compliance/summary
Response: {
  overallScore, lgpdStatus, controlsImplemented, totalControls,
  openIncidents, pendingActions,
  recentEvents: [{ type, description, date }]
}
```

---

## ÁREA 4: COMPLIANCE GLOBAL

### #54 Dashboard Compliance (`/admin/compliance`)

```
GET /api/v1/compliance/dashboard?company_id=
Response: {
  totalControls, totalImplemented, upcomingReviews, overdueReviews,
  byFramework: { [key]: { totalControls, implemented, verified, compliancePercentage } }
}
Nota: Endpoint já existe no lia-backend.

GET /api/v1/compliance/alerts?limit=10
Response: [{ id, title, description, severity, type, timestamp, status }]
```

### #29 Controles Hub (`/admin/compliance/controles`)

```
GET /api/v1/compliance/controls?framework=&status=&search=
Response: {
  data: [{ id, name, description, framework, status, lastReviewDate, nextReviewDate, owner }],
  meta: {...}
}
Nota: ISO/SOC/SOX filtrados via query param `framework=ISO27001|SOC2|SOX`
```

### #34 LGPD Hub (`/admin/compliance/lgpd`)

```
GET /api/v1/compliance/lgpd/stats?company_id=
Response: { dpoActive, dpoRegistered, openBreaches, totalConsents, pendingDSARs, dataProcessingRecords }
Nota: Endpoint já existe no lia-backend.
```

### #36 Consentimentos (`/admin/compliance/lgpd/consentimentos`)

```
GET /api/v1/compliance/lgpd/consents?page=1&limit=20&status=
Response: { data: [{ id, purpose, legalBasis, status, dataSubjectCount, createdAt, expiresAt }], meta: {...} }
```

### #38 Portal do Titular (`/admin/compliance/lgpd/portal-titular`)

```
GET /api/v1/compliance/lgpd/dsar?page=1&limit=20&status=
Response: { data: [{ id, requestType, subjectName, subjectEmail, status, receivedAt, deadline, completedAt }], meta: {...} }

PUT /api/v1/compliance/lgpd/dsar/:id
Body: { status, notes }
```

### #41 Alertas (`/admin/compliance/monitoramento/alertas`)

```
GET /api/v1/compliance/alerts?page=1&limit=20&severity=&status=
Response: { data: [{ id, title, description, severity, type, source, timestamp, status, assignedTo }], meta: {...} }

PUT /api/v1/compliance/alerts/:id
Body: { status, notes }
```

### #42 Incidentes (`/admin/compliance/monitoramento/incidentes`)

```
GET /api/v1/compliance/incidents?page=1&limit=20&severity=&status=
Response: { data: [{ id, title, description, severity, category, status, reportedAt, resolvedAt, impact, rootCause }], meta: {...} }

POST /api/v1/compliance/incidents
Body: { title, description, severity, category }

PUT /api/v1/compliance/incidents/:id
Body: { status, rootCause, resolution }
```

### #48 Sala de Auditoria (`/admin/compliance/auditoria`)

```
GET /api/v1/compliance/audit/summary
Response: { totalAudits, completedAudits, pendingAudits, upcomingAudits, lastAuditDate, biasAlertCount }
```

### #49 Logs (`/admin/compliance/auditoria/logs`)

```
GET /api/v1/compliance/audit/logs?page=1&limit=50&action=&user=&start_date=&end_date=
Response: { data: [{ id, action, user, resource, details, ipAddress, timestamp }], meta: {...} }
Nota: Endpoint já existe no lia-backend.
```

### #50 Bias/Fairness (`/admin/compliance/auditoria/bias`)

```
GET /api/v1/compliance/bias/summary?company_id=
Response: { totalAudits, byStatus: { pass, consider, concern }, lastAuditDate, dimensions: [...] }

GET /api/v1/compliance/bias/latest?company_id=
Response: { auditDate, overallScore, dimensions: [{ name, score, status, details }] }

GET /api/v1/compliance/bias/reports?page=1&limit=10
Response: { data: [{ id, auditDate, overallScore, status, dimensions }], meta: {...} }
Nota: Endpoints já existem no lia-backend (BiasAuditService).
```

### #53 Exportar (`/admin/compliance/auditoria/exportar`)

```
POST /api/v1/compliance/audit/export
Body: { format: "pdf"|"csv"|"xlsx", dateRange: { start, end }, includeTypes: [...] }
Response: { downloadUrl, expiresAt }
```

### #56 Guardrails IA (`/admin/compliance/guardrails`)

```
GET /api/v1/compliance/guardrails
Response: { rules: [{ id, name, description, type, isActive, severity, lastTriggered }] }

PUT /api/v1/compliance/guardrails/:id
Body: { isActive, severity, config }
```

---

## ÁREA 5: CONFIGURAÇÕES GLOBAIS

### #57 Hub Configurações (`/admin/configuracoes`)

```
GET /api/v1/admin/settings
Response: { sections: [{ key, label, progress, status }] }
```

### #58 Políticas Globais (`/admin/configuracoes/politicas`)

```
GET /api/v1/admin/settings/policies
Response: { security: {...}, ai: {...}, dataRetention: {...}, access: {...} }

PUT /api/v1/admin/settings/policies
Body: { ...partial policy fields }
Nota: Endpoint já existe no lia-backend (PoliciesService).
```

### #59 Comunicações (`/admin/configuracoes/comunicacoes`)

```
GET /api/v1/admin/settings/communications
Response: { channels: [...], webhooks: [...], automations: [...] }

PUT /api/v1/admin/settings/communications
Body: { ...partial communication config }
```

### Templates de Sistema (`/admin/templates`)

```
GET /api/v1/admin/templates?type=&category=
Response: { data: [{ id, name, type, category, content, isActive, usageCount }], meta: {...} }

PUT /api/v1/admin/templates/:id
Body: { name, content, isActive }
Nota: Endpoint já existe no lia-backend (TemplatesService).
```

---

## ÁREA 6: MONITORAMENTO

### #61 Saúde dos Agentes IA (`/admin/monitoring/agents`)

```
GET /api/v1/agent-monitoring/domains/health?company_id=&days=30
Response: {
  company_id, window_days,
  domains: [{ domain, total_executions, avg_duration_ms, avg_iterations, avg_confidence, tool_failure_rate, last_execution, days_since_last_execution, status }],
  total_domains, unhealthy_count
}
Nota: Endpoint já existe no lia-backend. Dados reais.
```

---

## Resumo de Endpoints

| Status | Quantidade | Descrição |
|--------|-----------|-----------|
| Existente (lia-backend) | ~12 | Endpoints já implementados e funcionais |
| Mock/Hardcoded | ~5 | Dados simulados no frontend, precisa de endpoint real |
| Novo (ats_api) | ~18 | Endpoints que precisam ser criados no ats_api |

### Endpoints prioritários para implementação no ats_api:
1. `GET /admin/clients/:id/metrics` — métricas reais do cliente
2. `GET /admin/clients/:id/activities` — atividades reais
3. `GET /admin/dashboard/service-consumption` — consumo real de serviços
4. `GET /admin/dashboard/activities` — atividades globais reais
5. `GET /admin/clients/:id/billing` — faturamento real
6. `GET /admin/clients/:id/saas-metrics` — métricas SaaS reais
