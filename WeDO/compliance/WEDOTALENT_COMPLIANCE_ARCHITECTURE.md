# WeDo Talent Admin - Documento de Arquitetura de Compliance

**Versão:** 1.1  
**Data:** Dezembro 2025 (Atualizado em 20/12/2025)  
**Classificação:** Confidencial - Uso Interno  
**Objetivo:** Documentação completa da plataforma para auditorias SOC2, SOX, BCB 498, ISO 27001, LGPD e Governança de IA

### Histórico de Versões
| Versão | Data | Alterações |
|--------|------|------------|
| 1.0 | Dezembro 2025 | Versão inicial |
| 1.1 | 20/12/2025 | Adicionado Compliance Health Check (242 itens, 7 frameworks), sincronização com biblioteca de controles, APIs de health check |
| 1.2 | Janeiro 2026 | Delegação de funcionalidades SSO/SCIM para WorkOS Dashboard, remoção de /admin/compliance/monitoramento/soc-siem, simplificação da página /admin/sso (4→2 abas) |

---

## 1. VISÃO GERAL DA PLATAFORMA

### 1.1 Descrição
A Plataforma LIA (Learning Intelligence Assistant) é um sistema B2B SaaS multi-tenant de recrutamento e seleção com inteligência artificial. Desenvolvida para atender requisitos rigorosos de compliance para homologação em instituições financeiras reguladas pelo Banco Central do Brasil.

### 1.2 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 15)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Clientes   │  │  Compliance  │  │   Configurações      │  │
│  │  (Multi-T)   │  │  & Security  │  │   Globais            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + LangGraph)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  REST APIs   │  │  Agentes IA  │  │   Serviços Core      │  │
│  │  (200+ EP)   │  │  (11 agents) │  │   (Auth, Email...)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PERSISTÊNCIA                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               PostgreSQL (Neon-backed)                    │  │
│  │         80+ tabelas com isolamento multi-tenant           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Frontend | Next.js + React + TypeScript | 15.x |
| UI Components | Radix UI + shadcn/ui + Tailwind CSS | Latest |
| Backend | FastAPI + Python | 3.11 |
| IA/ML | LangGraph + Claude Sonnet (Anthropic) | 4.x |
| Banco de Dados | PostgreSQL (Neon) | 15.x |
| ORM | SQLAlchemy (async) | 2.x |

---

## 2. ARQUITETURA ADMIN (3 PILARES)

### 2.1 Pilar 1: Visão Geral (Overview)
Dashboard consolidado com métricas globais da plataforma.

| Módulo | Descrição | Dados Coletados |
|--------|-----------|-----------------|
| Métricas Plataforma | KPIs consolidados | MRR, ARR, Churn, Clientes ativos |
| Setup Empresa | Configuração inicial | Dados corporativos, planos |
| Jornada Recrutamento | Templates de processo | Fluxos, SLAs, automações |

### 2.2 Pilar 2: Operações (Por Cliente)
Gestão operacional de cada cliente com isolamento multi-tenant.

| Módulo | Descrição | Dados Coletados |
|--------|-----------|-----------------|
| `/clientes/[clientId]` | Dashboard do cliente | Métricas individuais |
| `/metricas` | SaaS Metrics | Revenue, usage, health |
| `/usuarios` | Gestão de usuários | Usuários, roles, permissões |
| `/automacoes` | Automações | Regras de comunicação |
| `/integracoes` | Integrações ATS | Conexões, sync logs |
| `/big-five` | Cultura organizacional | Perfil comportamental |
| `/faturamento` | Billing | Faturas, pagamentos |
| `/consumo-ia` | Consumo de IA | Créditos, uso por agente |
| `/testes` | Testes técnicos | Resultados, configurações |
| `/workforce` | Workforce Planning | Headcount, planos |
| `/observabilidade` | Observability | Logs, métricas, alertas |
| `/jornada` | Jornada do candidato | Stages, SLAs |
| `/comunicacoes` | Comunicações | Templates, histórico |
| `/conformidade` | Compliance cliente | Controles, incidentes, LGPD |

### 2.3 Pilar 3: Compliance & Security
Módulos de governança, compliance e segurança.

#### 2.3.1 Compliance Controls (`/compliance/controles`)
| Submódulo | Frameworks | Controles |
|-----------|------------|-----------|
| SOC 2 | SOC 2 Type II | CC1-CC9 |
| SOX | SOX 404 | ITGCs, SoD |
| ISO 27001 | ISO 27001:2022 | A.5-A.18 |
| Cobertura | Todos | 177 controles pré-cadastrados |

#### 2.3.2 LGPD & Privacidade (`/compliance/lgpd`)
| Submódulo | Descrição | Artigos LGPD |
|-----------|-----------|--------------|
| Portal do Titular | Direitos Art. 18 | Art. 18 (7 tipos) |
| Consentimentos | Gestão de consentimento | Art. 7, 8 |
| DPO | Registro do Encarregado | Art. 41 |
| Transferências | Transferência internacional | Art. 33-36 |

#### 2.3.3 Gestão de Riscos (`/compliance/riscos`)
| Submódulo | Framework | Componentes |
|-----------|-----------|-------------|
| Registro | ISO 27001, SOX | Matriz 5x5, tratamentos |
| Seguro | BCB 498/2025 | Apólices, coberturas, sinistros |
| Continuidade | ISO 22301 | BIA, DRP, testes |
| Fornecedores | ISO 27001 | Due diligence, avaliação |

#### 2.3.4 Monitoramento (`/compliance/monitoramento`)
| Submódulo | Descrição | Dados |
|-----------|-----------|-------|
| ~~SOC/SIEM~~ | ~~Security monitoring~~ | **Removido em Janeiro 2026** - delegado ao WorkOS Dashboard |
| Incidentes | Gestão de incidentes | Tickets, RCA |
| Alertas | Sistema de alertas | Regras, notificações |
| Dashboard Segurança | Métricas de segurança | KPIs, tendências |

> **Nota (Janeiro 2026):** O submódulo SOC/SIEM (`/admin/compliance/monitoramento/soc-siem`) foi removido. A funcionalidade de Log Streaming e integração SIEM agora é gerenciada diretamente pelo WorkOS Dashboard em https://dashboard.workos.com/log-streams.

#### 2.3.5 Auditoria (`/compliance/auditoria`)
| Submódulo | Descrição | Retenção |
|-----------|-----------|----------|
| Logs | SOX Audit Logs | 7 anos (financeiro) |
| Bias | Auditoria de viés IA | Contínuo |
| SoD | Segregação de funções | Tempo real |
| Treinamentos | Compliance training | Anual |
| Exportar | Export de evidências | Sob demanda |

#### 2.3.6 Trust Center (`/compliance/trust-center`)
| Submódulo | Público | Conteúdo |
|-----------|---------|----------|
| Certificações | Externo | Selos, certificados |
| Subprocessadores | Externo | Lista de terceiros |
| Recursos | Externo | Políticas, whitepapers |

#### 2.3.7 WorkOS Enterprise Authentication (`/admin/sso`)

A plataforma utiliza WorkOS para autenticação empresarial (SSO/SAML) e sincronização de diretórios (SCIM).

| Funcionalidade | Descrição |
|----------------|-----------|
| **SSO/SAML** | Autenticação via Azure AD, Okta, Google Workspace |
| **SCIM** | Sincronização automática de usuários e grupos |
| **Mapeamento de Grupos** | Associação de grupos do IdP a roles na plataforma |

**Página Admin SSO (`/admin/sso`):**
A página de administração SSO possui **2 abas**:
1. **Status** - Cards com métricas resumidas (usuários SSO, grupos sincronizados)
2. **Grupos** - Mapeamento de grupos para roles (lógica de negócio)

### WorkOS Dashboard Delegation (Janeiro 2026)

A partir de Janeiro 2026, certas funcionalidades de SSO/SCIM foram delegadas ao WorkOS Dashboard para simplificar a arquitetura e garantir dados sempre atualizados.

**Funcionalidades delegadas ao WorkOS Dashboard:**

| Funcionalidade | URL WorkOS Dashboard | Motivo da Delegação |
|----------------|---------------------|---------------------|
| Gestão de usuários SSO/SCIM | https://dashboard.workos.com/users | Dados em tempo real, sem duplicação |
| Logs de auditoria SSO/SCIM | https://dashboard.workos.com/events | Retenção e busca avançada nativa |
| Log Streaming (SIEM) | https://dashboard.workos.com/log-streams | Configuração de integrações SIEM |
| Métricas de segurança de autenticação | https://dashboard.workos.com | Dashboards nativos do WorkOS |

**O que permanece no WeDo Talent Admin (`/admin/sso`):**

| Funcionalidade | Descrição |
|----------------|-----------|
| Status cards com métricas resumidas | Visão rápida de usuários SSO e grupos |
| Mapeamento grupo→role | Lógica de negócio específica da plataforma |
| Links para WorkOS Dashboard | Acesso direto às funcionalidades delegadas |

**Benefícios desta arquitetura:**

1. **Redução de manutenção de código** - Menos código para manter e atualizar
2. **Dados sempre atuais** - Sem necessidade de sincronização/cache local
3. **Funcionalidades avançadas** - Acesso a recursos nativos do WorkOS (busca, filtros, exportação)
4. **Compliance simplificado** - WorkOS já é certificado SOC 2, ISO 27001

**Remoções:**
- `/admin/compliance/monitoramento/soc-siem` - Removido (delegado a WorkOS Log Streams)
- Abas "Usuários" e "Auditoria" em `/admin/sso` - Removidas (delegadas ao WorkOS Dashboard)

---

#### 2.3.8 Compliance Health Check (`/compliance/health-check`)
Dashboard interativo de verificação de conformidade com 242 itens distribuídos em 7 frameworks regulatórios.

| Framework | Itens | Descrição |
|-----------|-------|-----------|
| **ISO 27001:2022** | 96 | Controles de segurança da informação (A.5-A.8) |
| **SOC 2 Type II** | 61 | Trust Services Criteria (CC1-CC9, A1, C1, PI1, P1-P8) |
| **SOX 404** | 27 | Controles internos, ITGCs, SoD, evidências |
| **LGPD** | 17 | Princípios, direitos do titular, obrigações |
| **BCB 498/2025** | 13 | Seguro cibernético, coberturas obrigatórias |
| **EU AI Act** | 13 | Governança de IA, alto risco, transparência |
| **NYC LL144** | 11 | Auditoria de viés em AEDT, métricas de impacto |
| **TOTAL** | **242** | **100% sincronizado com biblioteca de controles** |

**Funcionalidades:**
- Verificação interativa de status por item (compliant, partial, non_compliant, not_applicable)
- Links para documentação oficial de cada framework
- Sincronização automática com biblioteca de controles (`/sync-from-library`)
- Filtros por framework, status e prioridade
- Estatísticas em tempo real por categoria
- Mapeamento de prioridade (mandatory → critical, optional → medium)

**APIs:**
```
GET    /api/v1/health-check/items              # Lista todos os itens
GET    /api/v1/health-check/items/{id}         # Item específico
PUT    /api/v1/health-check/items/{id}         # Atualiza status
GET    /api/v1/health-check/summary            # Resumo por framework
POST   /api/v1/health-check/sync-from-library  # Sincroniza da biblioteca
```

---

## 3. MAPEAMENTO DE DADOS

### 3.1 Classificação de Dados

| Classificação | Descrição | Exemplos |
|---------------|-----------|----------|
| **Público** | Dados não sensíveis | Nome da empresa, cargo |
| **Interno** | Uso interno apenas | Métricas, configurações |
| **Confidencial** | Dados de negócio | Candidatos, vagas |
| **Sensível (LGPD)** | Dados pessoais | CPF, email, telefone |
| **Altamente Sensível** | Dados especiais | Saúde, biometria, raça |

### 3.2 Tabelas do Banco de Dados (80+ tabelas)

#### 3.2.1 Dados de Candidatos (Sensíveis - LGPD)
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `candidates` | Nome, email, telefone, CPF, endereço | Sensível | Conforme política |
| `candidate_experiences` | Histórico profissional | Sensível | Conforme política |
| `candidate_education` | Formação acadêmica | Sensível | Conforme política |
| `candidate_attachments` | CVs, documentos | Sensível | Conforme política |
| `candidate_favorites` | Marcações de favoritos | Interno | 1 ano |
| `viewed_candidates` | Histórico de visualização | Interno | 90 dias |
| `vacancy_candidates` | Associação vaga-candidato | Confidencial | Vida da vaga + 2 anos |

#### 3.2.2 Dados de Vagas e Recrutamento
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `job_vacancies` | Título, descrição, requisitos | Interno | 5 anos |
| `recruitment_stages` | Etapas do processo | Interno | 5 anos |
| `screening_questions` | Perguntas de triagem | Interno | 5 anos |
| `candidate_stage_history` | Movimentação de candidatos | Confidencial | 5 anos |

#### 3.2.3 Dados de IA e Decisões Automatizadas
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `ai_inference_logs` | Logs de inferência IA | Interno | 2 anos |
| `automated_decision_explanations` | Explicações de decisão | Confidencial | 5 anos |
| `lia_opinions` | Pareceres da LIA | Confidencial | 5 anos |
| `lia_profile_analyses` | Análises de perfil | Confidencial | 5 anos |
| `bias_audit_reports` | Auditorias de viés | Confidencial | 7 anos |
| `bias_audit_categories` | Categorias de viés | Interno | 7 anos |
| `calibration_feedback` | Feedback de calibração | Interno | 2 anos |
| `model_evaluations` | Avaliações de modelo | Interno | 2 anos |

#### 3.2.4 Dados de Compliance e Auditoria
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `sox_audit_logs` | Logs SOX-compliant | Confidencial | 7 anos |
| `audit_retention_policies` | Políticas de retenção | Interno | Permanente |
| `compliance_controls` | Controles implementados | Interno | Permanente |
| `compliance_control_library` | Biblioteca de 218 controles (7 frameworks) | Interno | Permanente |
| `compliance_health_check_items` | 242 itens de verificação de conformidade | Interno | Permanente |
| `compliance_audits` | Registros de auditoria | Confidencial | 7 anos |
| `sox_controls` | Controles SOX específicos | Confidencial | 7 anos |
| `data_access_logs` | Logs de acesso a dados | Interno | 2 anos |

#### 3.2.5 Dados LGPD
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `data_subject_requests` | Requisições de titulares | Sensível | 5 anos |
| `consent_versions` | Versões de termos | Interno | Permanente |
| `consent_events` | Eventos de consentimento | Sensível | 5 anos |
| `consent_records` | Registros de consentimento | Sensível | 5 anos |
| `lgpd_consents` | Consentimentos LGPD | Sensível | 5 anos |
| `dpo_registry` | Registro do DPO | Interno | Permanente |
| `breach_notifications` | Notificações de incidente | Confidencial | 10 anos |

#### 3.2.6 Dados de Seguro e Riscos (BCB 498)
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `insurance_policies` | Apólices de seguro | Confidencial | 10 anos |
| `insurance_coverages` | Coberturas | Confidencial | 10 anos |
| `insurance_documents` | Documentos | Confidencial | 10 anos |
| `insurance_claims` | Sinistros | Confidencial | 10 anos |
| `risk_entries` | Registro de riscos | Confidencial | 7 anos |
| `risk_treatments` | Tratamentos de risco | Confidencial | 7 anos |

#### 3.2.7 Dados de SoD e Continuidade
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `sod_roles` | Papéis SoD | Interno | Permanente |
| `sod_conflicts` | Conflitos definidos | Interno | Permanente |
| `sod_violations` | Violações detectadas | Confidencial | 7 anos |
| `business_processes` | Processos críticos | Interno | Permanente |
| `disaster_recovery_plans` | Planos de DR | Confidencial | Permanente |
| `continuity_tests` | Testes de continuidade | Confidencial | 5 anos |

#### 3.2.8 Dados de Usuários e Acesso
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `users` | Usuários do sistema | Sensível | Vida do contrato + 2 anos |
| `client_users` | Usuários dos clientes | Sensível | Vida do contrato + 2 anos |
| `admin_roles` | Papéis administrativos | Interno | Permanente |
| `admin_user_roles` | Associação usuário-papel | Interno | Permanente |
| `admin_audit_logs` | Logs de admin | Confidencial | 7 anos |

#### 3.2.9 Dados de Comunicação
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `email_templates` | Templates de email | Interno | Permanente |
| `email_logs` | Logs de envio | Interno | 2 anos |
| `communication_history` | Histórico de comunicação | Confidencial | 5 anos |
| `notifications` | Notificações | Interno | 90 dias |

#### 3.2.10 Dados Financeiros e Billing
| Tabela | Dados | Classificação | Retenção |
|--------|-------|---------------|----------|
| `subscriptions` | Assinaturas | Confidencial | 10 anos |
| `invoices` | Faturas | Confidencial | 10 anos |
| `payment_methods` | Métodos de pagamento | Altamente Sensível | Tokenizado |
| `payment_history` | Histórico de pagamentos | Confidencial | 10 anos |
| `client_saas_metrics` | Métricas SaaS | Confidencial | 5 anos |

---

## 4. APIs REST (200+ ENDPOINTS)

### 4.1 Resumo por Módulo

| Módulo | Endpoints | Descrição |
|--------|-----------|-----------|
| activities | 3 | Atividades e urgências |
| admin | 18 | Administração geral |
| agent-monitoring | 9 | Monitoramento de agentes IA |
| ai-consumption | 10 | Consumo de IA |
| alerts | 7 | Alertas e notificações |
| analysis | 4 | Análise de candidatos |
| analytics | 10 | Predições e analytics |
| applications | 4 | Candidaturas |
| approvals | 6 | Fluxo de aprovações |
| ats | 6 | Integração ATS |
| attachments | 2 | Gestão de anexos |
| audit-logs | 6 | Logs de auditoria SOX |
| billing | 15 | Faturamento |
| calibration | 8 | Calibração de IA |
| candidate-lists | 5 | Listas de candidatos |
| candidate-search | 10 | Busca Pearch |
| candidates | 15 | Gestão de candidatos |
| chat | 5 | Chat LIA |
| communications | 8 | Comunicações |
| company | 6 | Configurações da empresa |
| company-culture | 6 | Cultura organizacional |
| consent | 9 | Gestão de consentimento |
| continuity | 12 | Continuidade de negócios |
| control-library | 8 | Biblioteca de controles |
| data-subject-requests | 10 | Portal do titular LGPD |
| health-check | 5 | Health Check de conformidade |
| email-templates | 8 | Templates de email |
| goals | 6 | Metas e objetivos |
| insurance | 19 | Seguro cibernético BCB 498 |
| integrations | 4 | Integrações externas |
| job-vacancies | 12 | Gestão de vagas |
| lia-opinions | 5 | Pareceres LIA |
| lgpd-compliance | 20 | Compliance LGPD |
| notifications | 8 | Notificações |
| observability | 18 | Observabilidade |
| orchestrator | 8 | Orquestrador de agentes |
| profiles | 6 | Análises de perfil |
| recruitment-journey | 10 | Jornada de recrutamento |
| risks | 8 | Registro de riscos |
| saas-metrics | 8 | Métricas SaaS |
| sod | 10 | Matriz SoD |
| trust-center | 10 | Trust Center |
| voice | 4 | Voz/Transcrição |
| webhooks | 5 | Webhooks |
| workforce | 15 | Workforce planning |
| wsi | 5 | Work Sample Interview |

### 4.2 APIs de Compliance Críticas

#### 4.2.1 LGPD - Portal do Titular
```
GET    /api/v1/data-subject-requests/
POST   /api/v1/data-subject-requests/
GET    /api/v1/data-subject-requests/{id}
PUT    /api/v1/data-subject-requests/{id}/assign
PUT    /api/v1/data-subject-requests/{id}/verify-identity
PUT    /api/v1/data-subject-requests/{id}/process
PUT    /api/v1/data-subject-requests/{id}/complete
PUT    /api/v1/data-subject-requests/{id}/reject
GET    /api/v1/data-subject-requests/stats
GET    /api/v1/data-subject-requests/export
```

#### 4.2.2 Gestão de Consentimento
```
GET    /api/v1/consent/versions
POST   /api/v1/consent/versions
GET    /api/v1/consent/versions/{id}
POST   /api/v1/consent/events
GET    /api/v1/consent/events
GET    /api/v1/consent/subject/{identifier}
PUT    /api/v1/consent/{id}/revoke
GET    /api/v1/consent/stats
GET    /api/v1/consent/export
```

#### 4.2.3 Seguro Cibernético (BCB 498)
```
GET    /api/v1/insurance/policies
POST   /api/v1/insurance/policies
GET    /api/v1/insurance/policies/{id}
PUT    /api/v1/insurance/policies/{id}
DELETE /api/v1/insurance/policies/{id}
POST   /api/v1/insurance/policies/{id}/coverages
GET    /api/v1/insurance/policies/{id}/coverages
POST   /api/v1/insurance/policies/{id}/documents
GET    /api/v1/insurance/claims
POST   /api/v1/insurance/claims
PUT    /api/v1/insurance/claims/{id}
GET    /api/v1/insurance/stats
GET    /api/v1/insurance/bcb-compliance
GET    /api/v1/insurance/expiring
GET    /api/v1/insurance/coverage-gaps
```

#### 4.2.4 Registro de Riscos
```
GET    /api/v1/risks
POST   /api/v1/risks
GET    /api/v1/risks/{id}
PUT    /api/v1/risks/{id}
DELETE /api/v1/risks/{id}
POST   /api/v1/risks/{id}/treatments
PUT    /api/v1/risks/treatments/{id}
GET    /api/v1/risks/stats
GET    /api/v1/risks/matrix
```

#### 4.2.5 Matriz SoD
```
GET    /api/v1/sod/roles
POST   /api/v1/sod/roles
PUT    /api/v1/sod/roles/{id}
DELETE /api/v1/sod/roles/{id}
GET    /api/v1/sod/conflicts
POST   /api/v1/sod/conflicts
POST   /api/v1/sod/violations
GET    /api/v1/sod/violations
PUT    /api/v1/sod/violations/{id}/approve
GET    /api/v1/sod/stats
```

#### 4.2.6 Continuidade de Negócios
```
GET    /api/v1/continuity/processes
POST   /api/v1/continuity/processes
PUT    /api/v1/continuity/processes/{id}
DELETE /api/v1/continuity/processes/{id}
GET    /api/v1/continuity/drp
POST   /api/v1/continuity/drp
PUT    /api/v1/continuity/drp/{id}
GET    /api/v1/continuity/tests
POST   /api/v1/continuity/tests
PUT    /api/v1/continuity/tests/{id}
GET    /api/v1/continuity/stats
GET    /api/v1/continuity/critical
```

#### 4.2.7 Compliance Health Check
```
GET    /api/v1/health-check/items                 # Lista itens com filtros (framework, status, priority)
GET    /api/v1/health-check/items/{id}            # Detalhes de item específico
PUT    /api/v1/health-check/items/{id}            # Atualiza status do item
GET    /api/v1/health-check/summary               # Resumo por framework (total, compliant, partial, etc.)
POST   /api/v1/health-check/sync-from-library     # Sincroniza itens da biblioteca de controles
```

**Distribuição de Itens por Framework:**
| Framework | Código | Total Itens | Mandatory | Optional |
|-----------|--------|-------------|-----------|----------|
| ISO 27001:2022 | `iso27001` | 96 | 73 | 23 |
| SOC 2 Type II | `soc2` | 61 | 42 | 19 |
| SOX 404 | `sox` | 27 | 22 | 5 |
| LGPD | `lgpd` | 17 | 17 | 0 |
| BCB 498/2025 | `bcb498` | 13 | 13 | 0 |
| EU AI Act | `euai` | 13 | 9 | 4 |
| NYC LL144 | `nyc144` | 11 | 8 | 3 |

#### 4.2.8 Biblioteca de Controles
```
GET    /api/v1/control-library                    # Lista controles (218 itens)
GET    /api/v1/control-library/{id}               # Detalhes do controle
POST   /api/v1/control-library                    # Cria novo controle
PUT    /api/v1/control-library/{id}               # Atualiza controle
DELETE /api/v1/control-library/{id}               # Remove controle
GET    /api/v1/control-library/by-framework/{fw}  # Controles por framework
GET    /api/v1/control-library/stats              # Estatísticas da biblioteca
POST   /api/v1/control-library/bulk-import        # Importação em lote
```

---

## 5. SISTEMA DE IA E DECISÕES AUTOMATIZADAS

### 5.1 Arquitetura Multi-Agente

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                               │
│              (Coordenador Central de Agentes)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  JOB PLANNER  │    │   SOURCING    │    │   SCREENING   │
│    AGENT      │    │    AGENT      │    │    AGENT      │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  SCHEDULING   │    │   FEEDBACK    │    │    OFFER      │
│    AGENT      │    │    AGENT      │    │    AGENT      │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  ONBOARDING   │    │  ANALYTICS    │    │   CULTURE     │
│    AGENT      │    │    AGENT      │    │    AGENT      │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 5.2 Agentes e Suas Funções

| Agente | Função | Decisões Automatizadas | Risco de Viés |
|--------|--------|------------------------|---------------|
| **Orchestrator** | Coordenação | Roteamento de tarefas | Baixo |
| **Job Planner** | Planejamento de vagas | Sugestão de requisitos | Médio |
| **Sourcing** | Busca de candidatos | Ranking de perfis | Alto |
| **Screening** | Triagem inicial | Aprovação/Rejeição | Alto |
| **Scheduling** | Agendamento | Horários de entrevista | Baixo |
| **Feedback** | Coleta de feedback | Análise de sentimento | Médio |
| **Offer** | Propostas | Sugestão de salário | Alto |
| **Onboarding** | Integração | Checklists | Baixo |
| **Analytics** | Predições | Previsões de contratação | Alto |
| **Culture** | Fit cultural | Score de compatibilidade | Alto |
| **Communication** | Comunicações | Tom e conteúdo | Médio |

### 5.3 Sistema de Scoring LIA

#### 5.3.1 Componentes do Score
| Componente | Peso | Fonte | Risco de Viés |
|------------|------|-------|---------------|
| Hard Skills | 25% | CV parsing + testes | Baixo |
| Soft Skills | 20% | Entrevista + análise | Médio |
| Experiência | 20% | CV parsing | Médio |
| Cultura | 15% | Big Five + WSI | Alto |
| Potencial | 10% | Analytics preditivo | Alto |
| Disponibilidade | 10% | Dados declarados | Baixo |

#### 5.3.2 Metodologia WSI (Work Sample Interview)
Baseada em frameworks validados:
- **Taxonomia de Bloom**: Níveis cognitivos
- **Modelo Dreyfus**: Competência profissional
- **Big Five**: Traços de personalidade
- **CBI**: Entrevista comportamental

### 5.4 Logs de Decisão Automatizada

| Campo | Descrição | Obrigatório |
|-------|-----------|-------------|
| `decision_id` | ID único da decisão | Sim |
| `agent_name` | Agente responsável | Sim |
| `decision_type` | Tipo (screening, ranking, etc) | Sim |
| `input_data` | Dados de entrada (hash) | Sim |
| `output` | Resultado da decisão | Sim |
| `confidence` | Score de confiança (0-1) | Sim |
| `reasoning` | Explicação em linguagem natural | Sim |
| `criteria_used` | Critérios utilizados | Sim |
| `criteria_ignored` | Critérios desconsiderados | Sim |
| `human_review_required` | Flag para revisão humana | Sim |
| `model_version` | Versão do modelo | Sim |
| `timestamp` | Data/hora | Sim |

### 5.5 Pontos de Intervenção Humana

| Gatilho | Ação | SLA |
|---------|------|-----|
| Confiança < 70% | Revisão obrigatória | 24h |
| Decisão de rejeição final | Aprovação gerencial | 48h |
| Score de viés elevado | Análise de compliance | 72h |
| Reclamação do candidato | Investigação DPO | 5 dias úteis |
| Auditoria de viés periódica | Revisão completa | Mensal |

---

## 6. CONTROLES DE COMPLIANCE

### 6.1 Frameworks Suportados

| Framework | Status | Controles | Cobertura |
|-----------|--------|-----------|-----------|
| LGPD | Implementado | 25 | 100% |
| SOC 2 Type II | Implementado | 45 | 95% |
| SOX 404 | Implementado | 32 | 90% |
| ISO 27001:2022 | Implementado | 55 | 85% |
| BCB 498/2025 | Implementado | 12 | 100% |
| NYC LL144 | Parcial | 8 | 70% |
| EU AI Act | Parcial | 15 | 60% |
| CA FEHA | Parcial | 5 | 50% |

### 6.2 Controles Críticos Implementados

#### 6.2.1 Controles LGPD
| ID | Controle | Evidência |
|----|----------|-----------|
| LGPD-01 | Base legal documentada | Registro em `consent_records` |
| LGPD-02 | Consentimento com hash | `consent_versions.hash` |
| LGPD-03 | Direitos do titular | `data_subject_requests` |
| LGPD-04 | Minimização de dados | Policy enforcement |
| LGPD-05 | Retenção definida | `audit_retention_policies` |
| LGPD-06 | DPO nomeado | `dpo_registry` |
| LGPD-07 | Notificação de incidente | `breach_notifications` |
| LGPD-08 | Explicação de decisão IA | `automated_decision_explanations` |
| LGPD-09 | Revisão humana | `human_review_requests` |
| LGPD-10 | Transferência internacional | Policy + contratos |

#### 6.2.2 Controles SOX
| ID | Controle | Evidência |
|----|----------|-----------|
| SOX-01 | Segregação de funções | `sod_roles`, `sod_conflicts` |
| SOX-02 | Logs imutáveis | `sox_audit_logs` (7 anos) |
| SOX-03 | Controle de acesso | RBAC + MFA |
| SOX-04 | Aprovação de transações | `approvals` workflow |
| SOX-05 | Trilha de auditoria | Todos os registros |
| SOX-06 | Backup e recuperação | DR automático |
| SOX-07 | Gestão de mudanças | Git + deploy controlado |
| SOX-08 | Monitoramento de violações | `sod_violations` |

#### 6.2.3 Controles BCB 498
| ID | Controle | Evidência |
|----|----------|-----------|
| BCB-01 | Apólice de seguro | `insurance_policies` |
| BCB-02 | Cobertura data breach | `insurance_coverages` |
| BCB-03 | Cobertura ransomware | `insurance_coverages` |
| BCB-04 | Cobertura business interruption | `insurance_coverages` |
| BCB-05 | Cobertura regulatory defense | `insurance_coverages` |
| BCB-06 | Cobertura cyber liability | `insurance_coverages` |
| BCB-07 | Cobertura forensics | `insurance_coverages` |
| BCB-08 | Cobertura notification costs | `insurance_coverages` |
| BCB-09 | Cobertura crisis management | `insurance_coverages` |
| BCB-10 | Alertas de renovação | Sistema automático |
| BCB-11 | Registro de sinistros | `insurance_claims` |
| BCB-12 | Dashboard de compliance | `/insurance/bcb-compliance` |

### 6.3 Biblioteca de Controles

A plataforma possui 177 controles pré-cadastrados em `compliance_control_library`:

| Categoria | Quantidade | Exemplo |
|-----------|------------|---------|
| Acesso e Autenticação | 28 | MFA, SSO, RBAC |
| Criptografia | 15 | Em trânsito, em repouso |
| Logging e Monitoramento | 22 | SIEM, alertas, retenção |
| Gestão de Incidentes | 18 | Resposta, notificação |
| Continuidade | 14 | BCP, DRP, testes |
| Privacidade | 25 | LGPD, GDPR |
| Governança | 20 | Políticas, procedimentos |
| Fornecedores | 12 | Due diligence, contratos |
| IA/ML | 15 | Viés, explicabilidade |
| Desenvolvimento | 8 | SDLC, code review |

---

## 7. SISTEMA DE AUDITORIA DE VIÉS

### 7.1 Categorias de Viés Monitoradas (11)

| Categoria | Atributos Protegidos | Frequência |
|-----------|---------------------|------------|
| Gênero | Masculino, Feminino, Outros | Contínuo |
| Idade | Faixas etárias | Contínuo |
| Raça/Etnia | Categorias IBGE | Contínuo |
| Deficiência | PcD, sem deficiência | Contínuo |
| Estado Civil | Todos | Contínuo |
| Orientação Sexual | Quando declarado | Contínuo |
| Identidade de Gênero | Quando declarado | Contínuo |
| Religião | Quando declarado | Contínuo |
| Origem | Regional, nacionalidade | Contínuo |
| Classe Social | Proxies socioeconômicos | Contínuo |
| Neurodiversidade | Quando declarado | Contínuo |

### 7.2 Métricas de Viés

| Métrica | Fórmula | Threshold |
|---------|---------|-----------|
| Disparate Impact | Min(rate_A/rate_B, rate_B/rate_A) | ≥ 0.8 |
| Statistical Parity | |rate_A - rate_B| | ≤ 0.1 |
| Equal Opportunity | |TPR_A - TPR_B| | ≤ 0.1 |
| Predictive Equality | |FPR_A - FPR_B| | ≤ 0.1 |
| Calibration | Score consistency across groups | ≤ 0.05 |

### 7.3 Processo de Auditoria

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Coleta    │───▶│   Análise   │───▶│  Relatório  │
│   Dados     │    │   Métricas  │    │   Mensal    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Anonimiz.  │    │  Detecção   │    │  Ações      │
│  Dados      │    │  Anomalias  │    │  Corretivas │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 7.4 Armazenamento de Auditorias

| Tabela | Campos Críticos | Retenção |
|--------|-----------------|----------|
| `bias_audit_reports` | Período, métricas, status | 7 anos |
| `bias_audit_categories` | Categoria, selection_rate, adverse_impact_ratio | 7 anos |

---

## 8. LOGS E TRILHAS DE AUDITORIA

### 8.1 Tipos de Logs

| Tipo | Tabela | Retenção | SOX |
|------|--------|----------|-----|
| **Logs de Auditoria SOX** | `sox_audit_logs` | 7 anos | Sim |
| **Logs de Admin** | `admin_audit_logs` | 7 anos | Sim |
| **Logs de Acesso a Dados** | `data_access_logs` | 2 anos | Não |
| **Logs de Inferência IA** | `ai_inference_logs` | 2 anos | Não |
| **Logs de Webhook** | `webhook_logs` | 90 dias | Não |
| **Logs de Email** | `email_logs` | 2 anos | Não |
| **Logs de Sync ATS** | `integration_sync_logs` | 90 dias | Não |

### 8.2 Categorias de Ação (SOX Audit Log)

| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| `financial` | Transações financeiras | Faturas, pagamentos |
| `configuration` | Mudanças de config | Políticas, templates |
| `access` | Controle de acesso | Login, permissões |
| `data` | Manipulação de dados | CRUD em entidades |
| `compliance` | Eventos de compliance | Consentimento, requisições |
| `security` | Eventos de segurança | Incidentes, alertas |
| `ai_decision` | Decisões de IA | Screening, ranking |

### 8.3 Políticas de Retenção

| Categoria | Período | Base Legal |
|-----------|---------|------------|
| Financeiro | 7 anos | SOX, legislação fiscal |
| Configuração | 7 anos | SOX |
| Acesso | 2 anos | ISO 27001 |
| Dados pessoais | 5 anos | LGPD |
| Decisões de IA | 5 anos | NYC LL144, EU AI Act |
| Segurança | 2 anos | ISO 27001 |
| Operacional | 90 dias | Best practices |

---

## 9. INDICADORES E MÉTRICAS

### 9.1 KPIs de Compliance

| Indicador | Fórmula | Target | Frequência |
|-----------|---------|--------|------------|
| Taxa de Cobertura de Controles | Controles OK / Total | ≥ 95% | Mensal |
| SLA de Requisições LGPD | Atendidas no prazo / Total | 100% | Contínuo |
| Taxa de Incidentes | Incidentes / Mês | Tendência ↓ | Mensal |
| Tempo Médio de Resposta | Soma tempos / Qtd | ≤ 48h | Mensal |
| Cobertura de Seguro BCB | Coberturas OK / 8 | 100% | Mensal |
| Score de Viés Médio | Média Disparate Impact | ≥ 0.8 | Mensal |
| Taxa de Revisão Humana | Revisões / Decisões | ≥ 10% | Mensal |

### 9.2 KPIs de Operação

| Indicador | Descrição | Target |
|-----------|-----------|--------|
| MRR | Monthly Recurring Revenue | Crescimento |
| ARR | Annual Recurring Revenue | Crescimento |
| Churn Rate | Taxa de cancelamento | ≤ 5% |
| NPS | Net Promoter Score | ≥ 50 |
| Uptime | Disponibilidade | ≥ 99.9% |
| MTTR | Mean Time to Recovery | ≤ 1h |

### 9.3 KPIs de IA

| Indicador | Descrição | Target |
|-----------|-----------|--------|
| Precisão de Screening | True Positives / Predictions | ≥ 85% |
| Taxa de Falsos Positivos | FP / (FP + TN) | ≤ 10% |
| Confiança Média | Média de confidence scores | ≥ 75% |
| Taxa de Intervenção Humana | Revisões manuais / Total | 10-20% |
| Tempo de Resposta IA | Latência média | ≤ 3s |

---

## 10. INTEGRAÇÕES EXTERNAS

### 10.1 Provedores de IA

| Provedor | Uso | Dados Enviados | Contrato DPA |
|----------|-----|----------------|--------------|
| Anthropic (Claude) | LIA conversacional | Prompts, contexto | Sim |
| Google (Gemini) | Transcrição, fallback | Áudio, texto | Sim |
| Deepgram | Speech-to-text | Áudio | Sim |

### 10.2 Integrações ATS

| Provedor | Tipo | Dados Sincronizados |
|----------|------|---------------------|
| Gupy | API direta | Candidatos, vagas |
| Pandapé | API direta | Candidatos, vagas |
| StackOne | Unified API | 40+ ATSs |

### 10.3 Outros Serviços

| Serviço | Uso | Dados |
|---------|-----|-------|
| Pearch AI | Busca de candidatos | Perfis públicos |
| OpenMic.ai | Voice screening | Áudio de entrevista |
| Microsoft Graph | Calendário | Agendamentos |
| SendGrid/Resend | Email | Comunicações |

---

## 11. RECOMENDAÇÕES PARA AUDITORIA

### 11.1 Evidências Disponíveis

| Área | Tipo de Evidência | Localização |
|------|-------------------|-------------|
| Controles | Configurações, logs | API + BD |
| LGPD | Requisições, consentimentos | BD + exports |
| Viés | Relatórios de auditoria | BD + dashboard |
| SOX | Logs 7 anos, SoD | BD + exports |
| Continuidade | Planos, testes | BD + documentos |
| Seguro | Apólices, coberturas | BD + documentos |

### 11.2 Processos de Coleta

1. **Exportação de Logs**: `/api/v1/audit-logs/export`
2. **Relatório de Viés**: `/api/v1/observability/bias-audits`
3. **Status de Controles**: `/api/v1/observability/compliance-controls`
4. **Requisições LGPD**: `/api/v1/data-subject-requests/export`
5. **Compliance BCB**: `/api/v1/insurance/bcb-compliance`

### 11.3 Pontos de Atenção

| Área | Risco | Mitigação |
|------|-------|-----------|
| Decisões de IA | Viés algorítmico | Auditoria mensal + revisão humana |
| Dados pessoais | Vazamento | Criptografia + access control |
| Fornecedores | Dependência | DPA + avaliação periódica |
| Continuidade | Indisponibilidade | DR + testes trimestrais |
| Compliance | Gaps | Monitoramento contínuo |

---

## 12. GAP ANALYSIS - CHECKLIST DE COMPLIANCE

Esta seção apresenta uma análise completa de gaps comparando os requisitos de mercado com a implementação atual da plataforma. Cada item está classificado como:

- ✅ **Implementado**: Funcionalidade completa e operacional
- 🟡 **Parcial**: Implementação existe mas precisa de melhorias
- ❌ **Pendente**: Não implementado ou não iniciado
- ➖ **N/A**: Não aplicável ao contexto

---

### 12.1 SOX (Sarbanes-Oxley Act) - Seção 404

#### 12.1.1 Controles Gerais de TI (ITGCs)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| SOX-ITGC-01 | Política de controle de acesso documentada | ✅ | `global_policies`, `/admin/configuracoes/politicas` | Políticas configuráveis por tenant |
| SOX-ITGC-02 | Autenticação forte (MFA) | ✅ | `security_settings.mfa_enabled` | Suporte a TOTP e SMS |
| SOX-ITGC-03 | Gestão de identidades (provisioning/deprovisioning) | ✅ | `client_users`, `admin_roles`, `admin_user_roles` | RBAC completo |
| SOX-ITGC-04 | Revisão periódica de acessos | 🟡 | `admin_audit_logs` | Logs existem, falta workflow de recertificação |
| SOX-ITGC-05 | Segregação de funções (SoD) | ✅ | `sod_roles`, `sod_conflicts`, `sod_violations` | Matriz SoD completa com detecção automática |
| SOX-ITGC-06 | Logs de auditoria imutáveis | ✅ | `sox_audit_logs` | Append-only, retenção 7 anos |
| SOX-ITGC-07 | Controle de mudanças (change management) | ✅ | Git + deploy controlado | CI/CD com aprovações |
| SOX-ITGC-08 | Backup e recuperação | ✅ | PostgreSQL Neon | Backups automáticos, PITR |
| SOX-ITGC-09 | Gestão de incidentes | ✅ | `incident_reports`, `/compliance/monitoramento/incidentes` | Workflow completo |
| SOX-ITGC-10 | Monitoramento de segurança | ✅ | `alerts`, `/compliance/monitoramento/soc-siem` | Alertas configuráveis |

#### 12.1.2 Controles de Aplicação

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| SOX-APP-01 | Validação de entrada de dados | ✅ | Pydantic schemas, frontend validation | Validação dupla (front+back) |
| SOX-APP-02 | Controles de cálculo | ✅ | Business logic no backend | Cálculos auditáveis |
| SOX-APP-03 | Integridade de transações | ✅ | SQLAlchemy transactions | ACID compliance |
| SOX-APP-04 | Trilha de auditoria de dados financeiros | ✅ | `sox_audit_logs` categoria `financial` | 7 anos retenção |
| SOX-APP-05 | Aprovações de transações | ✅ | `approvals` workflow | Workflow configurável |
| SOX-APP-06 | Reconciliação de dados | 🟡 | Parcial via `saas_metrics` | Falta automação de reconciliação |
| SOX-APP-07 | Controle de acesso a relatórios financeiros | ✅ | RBAC + permissões | Roles específicos |

#### 12.1.3 Documentação e Governança

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| SOX-DOC-01 | Documentação de processos | ✅ | Este documento + `replit.md` | Arquitetura documentada |
| SOX-DOC-02 | Matriz de riscos e controles | ✅ | `compliance_controls`, `risk_entries` | 177 controles mapeados |
| SOX-DOC-03 | Evidências de teste de controles | 🟡 | `compliance_audits` | Estrutura existe, falta operacionalizar |
| SOX-DOC-04 | Relatórios de deficiências | 🟡 | Dashboard existe | Falta workflow formal de remediação |
| SOX-DOC-05 | Certificação da administração | ❌ | - | Workflow de sign-off não implementado |

**Score SOX: 17/22 (77%) - 4 itens parciais, 1 pendente**

---

### 12.2 SOC 2 Type II

#### 12.2.1 Critérios Comuns (CC)

| Req ID | Critério | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| CC1.1 | Integridade e valores éticos | ✅ | `global_policies` tipo `ethics` | Código de conduta |
| CC1.2 | Supervisão do conselho | 🟡 | Parcial | Estrutura de governança a definir |
| CC1.3 | Estrutura organizacional | ✅ | `admin_roles`, hierarquia | Papéis definidos |
| CC1.4 | Compromisso com competência | ✅ | `/compliance/auditoria/treinamentos` | Tracking de treinamentos |
| CC1.5 | Responsabilização | ✅ | RBAC + audit logs | Responsabilidades documentadas |
| CC2.1 | Comunicação interna | ✅ | Notificações, alertas | Sistema de comunicação |
| CC2.2 | Comunicação externa | ✅ | Trust Center público | `/compliance/trust-center` |
| CC2.3 | Políticas e procedimentos | ✅ | `global_policies`, `platform_policies` | 13+ políticas default |
| CC3.1 | Avaliação de riscos | ✅ | `risk_entries`, matriz 5x5 | Registro de riscos completo |
| CC3.2 | Identificação de riscos de fraude | 🟡 | Via risk register | Falta categoria específica de fraude |
| CC3.3 | Mudanças significativas | ✅ | Change management via Git | Controle de mudanças |
| CC3.4 | Tolerância a riscos | ✅ | `risk_entries.risk_appetite` | Apetite de risco definido |
| CC4.1 | Atividades de monitoramento | ✅ | `alerts`, dashboards | Monitoramento contínuo |
| CC4.2 | Avaliação de deficiências | 🟡 | Logs e alertas | Falta processo formal |
| CC5.1 | Seleção de controles | ✅ | `compliance_control_library` | 177 controles |
| CC5.2 | Tecnologia de controles | ✅ | Automação via código | Controles automatizados |
| CC5.3 | Políticas e procedimentos | ✅ | Documentação completa | Políticas versionadas |
| CC6.1 | Controle de acesso lógico | ✅ | RBAC, JWT, MFA | Acesso controlado |
| CC6.2 | Autenticação | ✅ | JWT + MFA opcional | Auth robusto |
| CC6.3 | Autorização | ✅ | `admin_roles`, `permissions` | Permissões granulares |
| CC6.4 | Restrição de acesso físico | ➖ | Cloud-based (Replit/Neon) | Responsabilidade do provedor |
| CC6.5 | Descarte seguro | 🟡 | `audit_retention_policies` | Políticas definidas, automação parcial |
| CC6.6 | Proteção contra ameaças externas | ✅ | WAF, rate limiting | Segurança em camadas |
| CC6.7 | Proteção de transmissão | ✅ | HTTPS/TLS obrigatório | Criptografia em trânsito |
| CC6.8 | Prevenção de malware | ➖ | Cloud-based | Responsabilidade do provedor |
| CC7.1 | Detecção de eventos | ✅ | `alerts`, `incident_reports` | Detecção automática |
| CC7.2 | Monitoramento de anomalias | ✅ | Sistema de alertas | Thresholds configuráveis |
| CC7.3 | Avaliação de eventos | ✅ | Workflow de incidentes | Classificação por severidade |
| CC7.4 | Resposta a incidentes | ✅ | `incident_reports`, `breach_notifications` | Workflow completo |
| CC7.5 | Recuperação de incidentes | ✅ | `disaster_recovery_plans` | DRP documentado |
| CC8.1 | Mudanças de infraestrutura | ✅ | IaC, Git-based | Mudanças controladas |
| CC9.1 | Gestão de riscos de fornecedores | ✅ | `/compliance/riscos/fornecedores` | Due diligence |
| CC9.2 | Monitoramento de fornecedores | 🟡 | `subprocessors` lista | Falta avaliação periódica automatizada |

#### 12.2.2 Critérios de Privacidade (P)

| Req ID | Critério | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| P1.1 | Aviso de privacidade | ✅ | Trust Center, `/privacidade` | Público e acessível |
| P2.1 | Escolha e consentimento | ✅ | `consent_versions`, `consent_events` | Gestão completa |
| P3.1 | Coleta de dados pessoais | ✅ | Campos mapeados | Minimização aplicada |
| P4.1 | Uso de dados pessoais | ✅ | Finalidades documentadas | Base legal definida |
| P5.1 | Retenção e descarte | ✅ | `audit_retention_policies` | Políticas por categoria |
| P6.1 | Acesso a dados pessoais | ✅ | `data_subject_requests` tipo `access` | Art. 18 LGPD |
| P6.2 | Correção de dados | ✅ | `data_subject_requests` tipo `correction` | Art. 18 LGPD |
| P6.3 | Exclusão de dados | ✅ | `data_subject_requests` tipo `deletion` | Art. 18 LGPD |
| P7.1 | Qualidade dos dados | 🟡 | Validações existem | Falta processo de limpeza periódica |
| P8.1 | Segurança de dados pessoais | ✅ | Criptografia, access control | Proteção em camadas |

**Score SOC 2: 36/42 (86%) - 6 itens parciais, 0 pendentes**

---

### 12.3 ISO 27001:2022

#### 12.3.1 Cláusulas Organizacionais (A.5)

| Req ID | Controle | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| A.5.1 | Políticas de segurança | ✅ | `global_policies` | Políticas versionadas |
| A.5.2 | Papéis e responsabilidades | ✅ | `admin_roles` | RACI definido |
| A.5.3 | Segregação de funções | ✅ | `sod_roles`, `sod_conflicts` | SoD automatizado |
| A.5.4 | Responsabilidades da gestão | ✅ | Documentação | Papéis claros |
| A.5.5 | Contato com autoridades | ✅ | `dpo_registry`, `breach_notifications` | DPO e ANPD |
| A.5.6 | Contato com grupos especiais | 🟡 | Parcial | Falta formalização |
| A.5.7 | Inteligência de ameaças | 🟡 | Via alertas | Falta feed de threat intel |
| A.5.8 | Segurança em projetos | ✅ | SDLC seguro | Code review obrigatório |

#### 12.3.2 Controles de Pessoas (A.6)

| Req ID | Controle | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| A.6.1 | Triagem | 🟡 | Processo manual | Falta integração com background check |
| A.6.2 | Termos de contratação | ✅ | `global_policies` | NDA, confidencialidade |
| A.6.3 | Conscientização de segurança | ✅ | `/compliance/auditoria/treinamentos` | Tracking de treinamentos |
| A.6.4 | Processo disciplinar | 🟡 | Política existe | Falta workflow no sistema |
| A.6.5 | Responsabilidades pós-emprego | ✅ | Offboarding + revogação | Deprovisioning automático |
| A.6.6 | Acordos de confidencialidade | ✅ | Contratos | Templates disponíveis |
| A.6.7 | Trabalho remoto | ✅ | SaaS cloud-based | Acesso seguro |
| A.6.8 | Reporte de eventos | ✅ | `incident_reports` | Canal de reporte |

#### 12.3.3 Controles Físicos (A.7)

| Req ID | Controle | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| A.7.1 | Perímetros físicos | ➖ | Cloud-based | Provedor (Replit/Neon) |
| A.7.2 | Controles de entrada | ➖ | Cloud-based | Provedor |
| A.7.3 | Segurança de escritórios | ➖ | Remote-first | N/A |
| A.7.4 | Monitoramento físico | ➖ | Cloud-based | Provedor |
| A.7.5 | Proteção contra ameaças | ➖ | Cloud-based | Provedor |
| A.7.6 | Trabalho em áreas seguras | ➖ | Remote-first | N/A |
| A.7.7 | Mesa limpa | 🟡 | Política existe | Responsabilidade do usuário |
| A.7.8 | Localização de equipamentos | ➖ | Cloud-based | N/A |
| A.7.9 | Segurança de ativos fora das instalações | ➖ | Cloud-based | N/A |
| A.7.10 | Mídia de armazenamento | ➖ | Cloud-based | Provedor |
| A.7.11 | Utilitários de suporte | ➖ | Cloud-based | Provedor |
| A.7.12 | Segurança de cabeamento | ➖ | Cloud-based | Provedor |
| A.7.13 | Manutenção de equipamentos | ➖ | Cloud-based | Provedor |
| A.7.14 | Descarte seguro | ✅ | `audit_retention_policies` | Políticas definidas |

#### 12.3.4 Controles Tecnológicos (A.8)

| Req ID | Controle | Status | Evidência | Gap/Observação |
|--------|----------|--------|-----------|----------------|
| A.8.1 | Dispositivos de endpoint | 🟡 | Parcial | Falta MDM |
| A.8.2 | Direitos de acesso privilegiado | ✅ | `admin_roles` | RBAC com least privilege |
| A.8.3 | Restrição de acesso à informação | ✅ | Multi-tenant isolation | Isolamento por company_id |
| A.8.4 | Acesso a código-fonte | ✅ | Git + permissões | Controle de acesso |
| A.8.5 | Autenticação segura | ✅ | JWT + MFA | OAuth2 ready |
| A.8.6 | Gestão de capacidade | ✅ | Auto-scaling (Neon) | Monitoramento de recursos |
| A.8.7 | Proteção contra malware | ➖ | Cloud-based | Provedor |
| A.8.8 | Gestão de vulnerabilidades | 🟡 | Dependabot parcial | Falta scan regular |
| A.8.9 | Gestão de configuração | ✅ | IaC, Git | Config as code |
| A.8.10 | Exclusão de informações | ✅ | Data retention policies | Automação parcial |
| A.8.11 | Mascaramento de dados | 🟡 | Parcial em logs | Falta em mais áreas |
| A.8.12 | Prevenção de vazamento | 🟡 | Access control | Falta DLP dedicado |
| A.8.13 | Backup de informações | ✅ | Neon PITR | Backup contínuo |
| A.8.14 | Redundância | ✅ | Multi-region (Neon) | Alta disponibilidade |
| A.8.15 | Logging | ✅ | `sox_audit_logs`, `admin_audit_logs` | Logs completos |
| A.8.16 | Atividades de monitoramento | ✅ | `alerts`, dashboards | Monitoramento 24/7 |
| A.8.17 | Sincronização de relógios | ✅ | NTP (cloud) | Timestamps UTC |
| A.8.18 | Uso de programas utilitários | ✅ | Controle de ferramentas | Whitelist |
| A.8.19 | Instalação de software | ✅ | Controle de deploy | CI/CD |
| A.8.20 | Segurança de redes | ✅ | HTTPS, TLS | Criptografia |
| A.8.21 | Segurança de serviços de rede | ✅ | API Gateway | Rate limiting |
| A.8.22 | Segregação de redes | ✅ | Multi-tenant | Isolamento lógico |
| A.8.23 | Filtragem web | ➖ | Cloud-based | Provedor |
| A.8.24 | Uso de criptografia | ✅ | TLS 1.3, AES-256 | Em trânsito e repouso |
| A.8.25 | Ciclo de vida de desenvolvimento | ✅ | SDLC seguro | DevSecOps |
| A.8.26 | Requisitos de segurança de aplicação | ✅ | Validação, sanitização | OWASP Top 10 |
| A.8.27 | Arquitetura segura | ✅ | Defense in depth | Múltiplas camadas |
| A.8.28 | Codificação segura | ✅ | Code review | Padrões definidos |
| A.8.29 | Testes de segurança | 🟡 | Parcial | Falta pentest regular |
| A.8.30 | Desenvolvimento terceirizado | 🟡 | Contratos existem | Falta avaliação formal |
| A.8.31 | Separação de ambientes | ✅ | Dev/Prod separados | Ambientes isolados |
| A.8.32 | Gestão de mudanças | ✅ | Git + PR reviews | Change management |
| A.8.33 | Informações de teste | ✅ | Dados anonimizados | Sem produção em dev |
| A.8.34 | Proteção durante auditoria | ✅ | Logs read-only | Integridade garantida |

**Score ISO 27001: 52/72 aplicáveis (72%) - 11 parciais, 0 pendentes entre aplicáveis**

---

### 12.4 LGPD (Lei Geral de Proteção de Dados)

#### 12.4.1 Princípios (Art. 6)

| Req ID | Princípio | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| LGPD-P1 | Finalidade | ✅ | Termos documentados | Finalidades específicas |
| LGPD-P2 | Adequação | ✅ | Dados compatíveis com finalidade | Mapeamento de dados |
| LGPD-P3 | Necessidade | ✅ | Minimização aplicada | Campos essenciais apenas |
| LGPD-P4 | Livre acesso | ✅ | `/privacidade`, Portal do Titular | Acesso gratuito |
| LGPD-P5 | Qualidade dos dados | ✅ | Validações, atualização | Dados corretos |
| LGPD-P6 | Transparência | ✅ | Trust Center, políticas públicas | Informações claras |
| LGPD-P7 | Segurança | ✅ | Criptografia, access control | Medidas técnicas |
| LGPD-P8 | Prevenção | ✅ | Monitoramento, alertas | Medidas preventivas |
| LGPD-P9 | Não discriminação | ✅ | `bias_audit_reports` | Auditoria de viés |
| LGPD-P10 | Responsabilização | ✅ | Logs, evidências | Demonstração de conformidade |

#### 12.4.2 Direitos do Titular (Art. 18)

| Req ID | Direito | Status | Evidência | Gap/Observação |
|--------|---------|--------|-----------|----------------|
| LGPD-D1 | Confirmação de existência | ✅ | `data_subject_requests` tipo `access` | SLA 15 dias úteis |
| LGPD-D2 | Acesso aos dados | ✅ | `data_subject_requests` tipo `access` | Export disponível |
| LGPD-D3 | Correção de dados | ✅ | `data_subject_requests` tipo `correction` | Workflow completo |
| LGPD-D4 | Anonimização/bloqueio/eliminação | ✅ | `data_subject_requests` tipo `deletion` | Hard/soft delete |
| LGPD-D5 | Portabilidade | ✅ | `data_subject_requests` tipo `portability` | JSON/CSV export |
| LGPD-D6 | Eliminação com consentimento | ✅ | `consent_events` tipo `revoked` | Revogação tracked |
| LGPD-D7 | Informação sobre compartilhamento | ✅ | `subprocessors`, Trust Center | Lista pública |
| LGPD-D8 | Informação sobre não consentir | ✅ | Termos de uso | Consequências claras |
| LGPD-D9 | Revogação do consentimento | ✅ | `consent_events` | Revogação fácil |
| LGPD-D10 | Oposição ao tratamento | ✅ | `data_subject_requests` tipo `objection` | Workflow disponível |
| LGPD-D11 | Revisão de decisão automatizada | ✅ | `automated_decision_explanations`, `human_review_requests` | Art. 20 completo |

#### 12.4.3 Obrigações do Controlador

| Req ID | Obrigação | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| LGPD-O1 | Registro de operações (Art. 37) | ✅ | `data_access_logs` | Registro completo |
| LGPD-O2 | Relatório de impacto (RIPD) | 🟡 | Template existe | Falta automação de geração |
| LGPD-O3 | Nomeação de DPO (Art. 41) | ✅ | `dpo_registry` | Registro e publicação |
| LGPD-O4 | Notificação de incidentes (Art. 48) | ✅ | `breach_notifications` | 72h para ANPD |
| LGPD-O5 | Transferência internacional (Art. 33-36) | ✅ | DPAs com provedores | Cláusulas padrão |
| LGPD-O6 | Consentimento documentado (Art. 8) | ✅ | `consent_versions`, hash SHA256 | Prova inequívoca |
| LGPD-O7 | Base legal documentada (Art. 7) | ✅ | `consent_records.legal_basis` | 10 bases legais |

**Score LGPD: 27/28 (96%) - 1 item parcial**

---

### 12.5 BCB 498/2025 (Seguro Cibernético)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| BCB-01 | Apólice de seguro cibernético | ✅ | `insurance_policies` | CRUD completo |
| BCB-02 | Cobertura: Data Breach | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-03 | Cobertura: Ransomware | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-04 | Cobertura: Business Interruption | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-05 | Cobertura: Regulatory Defense | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-06 | Cobertura: Cyber Liability | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-07 | Cobertura: Forensics | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-08 | Cobertura: Notification Costs | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-09 | Cobertura: Crisis Management | ✅ | `insurance_coverages` | Tipo obrigatório |
| BCB-10 | Alertas de expiração (30/60/90 dias) | ✅ | `/api/v1/insurance/expiring` | Sistema automático |
| BCB-11 | Registro de sinistros | ✅ | `insurance_claims` | Tracking completo |
| BCB-12 | Dashboard de compliance | ✅ | `/api/v1/insurance/bcb-compliance` | % de conformidade |
| BCB-13 | Detecção de gaps de cobertura | ✅ | `/api/v1/insurance/coverage-gaps` | Análise automática |
| BCB-14 | Documentos de apólice | ✅ | `insurance_documents` | Upload e gestão |

**Score BCB 498: 14/14 (100%) - Totalmente implementado**

---

### 12.6 Governança de IA e Ética

#### 12.6.1 EU AI Act (Parcial - Sistema de Alto Risco)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| EUAI-01 | Classificação de risco do sistema | ✅ | Documentado como alto risco | Recrutamento = alto risco |
| EUAI-02 | Sistema de gestão de qualidade | 🟡 | Parcial | Falta certificação formal |
| EUAI-03 | Gestão de dados e governança | ✅ | Data governance implementado | Políticas definidas |
| EUAI-04 | Documentação técnica | ✅ | Este documento + APIs | Arquitetura documentada |
| EUAI-05 | Registro de eventos (logging) | ✅ | `ai_inference_logs` | Logs detalhados |
| EUAI-06 | Transparência | ✅ | `automated_decision_explanations` | Explicabilidade |
| EUAI-07 | Supervisão humana | ✅ | `human_review_requests` | Intervenção humana |
| EUAI-08 | Acurácia e robustez | ✅ | `model_evaluations`, `calibration_feedback` | Monitoramento |
| EUAI-09 | Segurança cibernética | ✅ | Múltiplas camadas | Defense in depth |
| EUAI-10 | Conformity assessment | ❌ | - | Avaliação formal pendente |
| EUAI-11 | Registro em banco de dados da UE | ❌ | - | Não operamos na UE ainda |
| EUAI-12 | Monitoramento pós-mercado | ✅ | Dashboards, alertas | Contínuo |

#### 12.6.2 NYC Local Law 144 (Bias Audit)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| NYC-01 | Auditoria de viés anual | ✅ | `bias_audit_reports` | Relatórios periódicos |
| NYC-02 | Publicação de resultados | ✅ | Trust Center | Resultados públicos |
| NYC-03 | Notificação aos candidatos | ✅ | Termos de uso | Antes do uso de AEDT |
| NYC-04 | Métricas de impacto adverso | ✅ | Disparate Impact, Statistical Parity | 5 métricas |
| NYC-05 | Categorias protegidas | ✅ | `bias_audit_categories` | 11 categorias |
| NYC-06 | Auditor independente | 🟡 | Estrutura existe | Falta contratação formal |
| NYC-07 | Resumo de dados de auditoria | ✅ | Dashboard + exports | Relatórios detalhados |
| NYC-08 | Período de retenção (4 anos) | ✅ | 7 anos configurado | Excede requisito |

#### 12.6.3 Ética e Transparência em IA

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| ETH-01 | Explicabilidade de decisões | ✅ | `automated_decision_explanations` | Linguagem natural |
| ETH-02 | Direito à revisão humana | ✅ | `human_review_requests` | Workflow completo |
| ETH-03 | Documentação de critérios | ✅ | `lia_scoring` documentado | Pesos e componentes |
| ETH-04 | Auditoria de viés contínua | ✅ | `bias_audit_reports` | 11 categorias |
| ETH-05 | Consentimento informado | ✅ | `consent_versions` | Antes do processamento |
| ETH-06 | Limitação de dados de treinamento | ✅ | Sem dados pessoais em fine-tuning | Modelos pré-treinados |
| ETH-07 | Monitoramento de drift | 🟡 | `model_evaluations` | Falta automação de detecção |
| ETH-08 | Calibração periódica | ✅ | `calibration_sessions` | Sessões de calibração |
| ETH-09 | Feedback loop | ✅ | `calibration_feedback` | Melhoria contínua |
| ETH-10 | Governança de modelos | ✅ | Versionamento de prompts | Controle de versão |

**Score Governança de IA: 25/30 (83%) - 3 parciais, 2 pendentes**

---

### 12.7 Requisitos Específicos para Bancos (BACEN/CMN)

#### 12.7.1 Resolução CMN 4.893/2021 (Política de Segurança Cibernética)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| CMN-01 | Política de segurança cibernética | ✅ | `global_policies` | Documentada |
| CMN-02 | Plano de ação e resposta | ✅ | `incident_reports`, DRP | Workflows prontos |
| CMN-03 | Contratação de serviços de processamento | ✅ | DPAs, contratos | Due diligence |
| CMN-04 | Designação de responsável | ✅ | `dpo_registry`, CISO | Funções definidas |
| CMN-05 | Relatório anual | 🟡 | Dados disponíveis | Falta template de relatório |
| CMN-06 | Comunicação de incidentes | ✅ | `breach_notifications` | 72h para BCB |

#### 12.7.2 Resolução BCB 85/2021 (Proteção de Dados)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| BCB85-01 | Política de proteção de dados | ✅ | `global_policies` tipo `privacy` | LGPD compliance |
| BCB85-02 | Gestão de consentimento | ✅ | `consent_versions`, `consent_events` | Completo |
| BCB85-03 | Direitos dos titulares | ✅ | `data_subject_requests` | Portal público |
| BCB85-04 | Transferência internacional | ✅ | Documentação de subprocessadores | DPAs |
| BCB85-05 | Registro de operações | ✅ | `data_access_logs` | Logs completos |

#### 12.7.3 Requisitos Adicionais de Homologação Bancária

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| BANK-01 | Pentest anual | 🟡 | - | Precisa contratação |
| BANK-02 | Avaliação de vulnerabilidades | 🟡 | Dependabot | Falta scan completo |
| BANK-03 | Classificação de informações | ✅ | Seção 3.1 deste doc | 5 níveis |
| BANK-04 | Criptografia em trânsito | ✅ | TLS 1.3 | Obrigatório |
| BANK-05 | Criptografia em repouso | ✅ | AES-256 (Neon) | Banco criptografado |
| BANK-06 | Gestão de acessos privilegiados | ✅ | RBAC, SoD | Controle rigoroso |
| BANK-07 | Logs de 5+ anos | ✅ | 7 anos (SOX) | Excede requisito |
| BANK-08 | SLA de disponibilidade | ✅ | 99.9% (Neon SLA) | Monitorado |
| BANK-09 | DR e continuidade | ✅ | `disaster_recovery_plans` | Multi-region |
| BANK-10 | Testes de DR periódicos | ✅ | `continuity_tests` | Registro de testes |
| BANK-11 | Avaliação de terceiros | 🟡 | `/compliance/riscos/fornecedores` | Falta score automático |
| BANK-12 | Treinamento de segurança | ✅ | `/compliance/auditoria/treinamentos` | Tracking |

**Score Bancos/BACEN: 21/23 (91%) - 4 parciais**

---

### 12.8 Continuidade de Negócios (ISO 22301)

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| BCM-01 | Análise de Impacto (BIA) | ✅ | `business_processes` | RTO/RPO definidos |
| BCM-02 | Identificação de processos críticos | ✅ | Criticality Tier 1-4 | Classificação |
| BCM-03 | Mapeamento de dependências | ✅ | `business_processes.dependencies` | Dependências tracked |
| BCM-04 | Plano de recuperação de desastres | ✅ | `disaster_recovery_plans` | Versionado |
| BCM-05 | Aprovação de planos | ✅ | `disaster_recovery_plans.status` | Workflow de aprovação |
| BCM-06 | Testes periódicos | ✅ | `continuity_tests` | 4 tipos de teste |
| BCM-07 | Registro de findings | ✅ | `continuity_tests.findings` | Tracking de melhorias |
| BCM-08 | RTO/RPO/MTPD definidos | ✅ | `business_processes` | Por processo |
| BCM-09 | Comunicação de crise | 🟡 | Templates existem | Falta automação |
| BCM-10 | Revisão pós-incidente | ✅ | `incident_reports` | RCA documentado |

**Score ISO 22301: 9/10 (90%) - 1 parcial**

---

### 12.9 Auditoria de TI

| Req ID | Requisito | Status | Evidência | Gap/Observação |
|--------|-----------|--------|-----------|----------------|
| AUDIT-01 | Trilha de auditoria completa | ✅ | `sox_audit_logs`, `admin_audit_logs` | Todas as ações |
| AUDIT-02 | Imutabilidade de logs | ✅ | Append-only design | Não alterável |
| AUDIT-03 | Timestamp confiável | ✅ | UTC, NTP sync | Sincronizado |
| AUDIT-04 | Identificação do usuário | ✅ | `user_id`, `company_id` em todos logs | Rastreável |
| AUDIT-05 | Identificação da ação | ✅ | `action`, `action_type` | Categorizado |
| AUDIT-06 | Dados antes/depois | ✅ | `old_value`, `new_value` | Diff completo |
| AUDIT-07 | IP e dispositivo | ✅ | `ip_address`, `user_agent` | Geolocalização |
| AUDIT-08 | Retenção conforme política | ✅ | `audit_retention_policies` | 7 categorias |
| AUDIT-09 | Exportação para auditores | ✅ | `/api/v1/audit-logs/export` | CSV, JSON |
| AUDIT-10 | Proteção de logs | ✅ | Access control | Acesso restrito |
| AUDIT-11 | Alertas de anomalias | ✅ | `alerts` | Detecção automática |
| AUDIT-12 | Dashboard de auditoria | ✅ | `/compliance/auditoria` | Visualização |

**Score Auditoria de TI: 12/12 (100%) - Totalmente implementado**

---

### 12.10 RESUMO EXECUTIVO - GAP ANALYSIS

#### 12.10.1 Scores por Framework

| Framework | Implementado | Parcial | Pendente | N/A | Score |
|-----------|--------------|---------|----------|-----|-------|
| **SOX 404** | 17 | 4 | 1 | 0 | 77% |
| **SOC 2 Type II** | 36 | 6 | 0 | 0 | 86% |
| **ISO 27001:2022** | 52 | 11 | 0 | 20 | 72%* |
| **LGPD** | 27 | 1 | 0 | 0 | 96% |
| **BCB 498/2025** | 14 | 0 | 0 | 0 | 100% |
| **Governança de IA** | 25 | 3 | 2 | 0 | 83% |
| **BACEN/Bancos** | 21 | 4 | 0 | 0 | 91% |
| **ISO 22301** | 9 | 1 | 0 | 0 | 90% |
| **Auditoria de TI** | 12 | 0 | 0 | 0 | 100% |
| **TOTAL** | **213** | **30** | **3** | **20** | **87%** |

*ISO 27001 score considera apenas controles aplicáveis (cloud-based)

#### 12.10.2 Itens Críticos Pendentes (❌)

| ID | Item | Framework | Prioridade | Esforço |
|----|------|-----------|------------|---------|
| SOX-DOC-05 | Workflow de sign-off da administração | SOX | Alta | Médio |
| EUAI-10 | Conformity assessment formal | EU AI Act | Média | Alto |
| EUAI-11 | Registro em banco de dados da UE | EU AI Act | Baixa | Baixo |

#### 12.10.3 Itens Parciais Prioritários (🟡)

| ID | Item | Framework | Prioridade | Esforço |
|----|------|-----------|------------|---------|
| SOX-ITGC-04 | Workflow de recertificação de acessos | SOX | Alta | Médio |
| SOX-DOC-03 | Operacionalização de testes de controles | SOX | Alta | Alto |
| A.8.8 | Scan de vulnerabilidades regular | ISO 27001 | Alta | Médio |
| A.8.29 | Pentest regular | ISO 27001 | Alta | Alto |
| BANK-01 | Pentest anual contratado | BACEN | Alta | Alto |
| NYC-06 | Contratação de auditor independente de viés | NYC LL144 | Alta | Alto |
| LGPD-O2 | Automação de geração de RIPD | LGPD | Média | Médio |
| ETH-07 | Automação de detecção de drift | IA | Média | Alto |
| CMN-05 | Template de relatório anual BACEN | BACEN | Média | Baixo |
| CC1.2 | Estrutura formal de governança | SOC 2 | Média | Médio |

#### 12.10.4 Roadmap de Remediação Sugerido

**Q1 2026 (Prioridade Alta)**
1. Implementar workflow de recertificação de acessos
2. Contratar pentest anual
3. Configurar scan de vulnerabilidades (Snyk/Dependabot Pro)
4. Contratar auditor independente de viés

**Q2 2026 (Prioridade Média-Alta)**
5. Implementar workflow de sign-off SOX
6. Operacionalizar testes de controles
7. Formalizar estrutura de governança
8. Automatizar geração de RIPD

**Q3 2026 (Prioridade Média)**
9. Implementar detecção de drift em modelos IA
10. Criar template de relatório anual BACEN
11. Avaliar conformity assessment EU AI Act

---

### 12.11 MATRIZ DE EVIDÊNCIAS PARA AUDITORIA

| Área | Tipo de Evidência | Localização | Formato | Responsável |
|------|-------------------|-------------|---------|-------------|
| Controles SOX | Configurações | `sox_audit_logs` | JSON | Compliance |
| Logs de auditoria | 7 anos | `sox_audit_logs` | DB | TI |
| Segregação de funções | Matriz SoD | `sod_roles`, `sod_conflicts` | DB | Compliance |
| LGPD - Requisições | Histórico | `data_subject_requests` | DB/Export | DPO |
| LGPD - Consentimento | Versões + Eventos | `consent_versions`, `consent_events` | DB | DPO |
| Viés IA | Relatórios mensais | `bias_audit_reports` | DB/PDF | Data Science |
| Seguro BCB 498 | Apólices | `insurance_policies` | DB/Docs | Financeiro |
| Continuidade | Planos + Testes | `disaster_recovery_plans`, `continuity_tests` | DB | TI |
| Riscos | Registro | `risk_entries`, `risk_treatments` | DB | Risk |
| Incidentes | Histórico | `incident_reports`, `breach_notifications` | DB | Security |
| Treinamentos | Registros | `/compliance/auditoria/treinamentos` | DB | RH |
| Políticas | Versões | `global_policies`, `platform_policies` | DB | Compliance |

---

### 12.12 PLANO DE IMPLEMENTAÇÃO - GAPS IDENTIFICADOS

Esta seção classifica os gaps identificados entre o que pode ser resolvido com desenvolvimento interno (funcionalidades, dashboards, coleta de dados, registros) versus o que requer contratação externa.

#### 12.12.1 Itens Resolvíveis com Desenvolvimento Interno (22 itens)

##### Workflows e Processos Automatizados

| ID | Item | O que Construir | Esforço | Prioridade |
|----|------|-----------------|---------|------------|
| SOX-ITGC-04 | Recertificação de acessos | Workflow trimestral: notificações automáticas → revisão por gestor → aprovação/revogação → registro de evidências | 3-5 dias | Alta |
| SOX-DOC-03 | Testes de controles | Dashboard para agendar testes, executar checklists, anexar evidências, gerar relatórios | 5-7 dias | Alta |
| SOX-DOC-04 | Relatórios de deficiências | Workflow: criar issue → atribuir responsável → acompanhar → resolver → validar → fechar | 3-4 dias | Alta |
| SOX-DOC-05 | Sign-off da administração | Tela para diretores assinarem digitalmente atestado trimestral/anual de eficácia dos controles | 2-3 dias | Alta |
| SOX-APP-06 | Reconciliação de dados | Job automático comparando dados financeiros entre sistemas + dashboard de divergências + alertas | 3-4 dias | Média |
| CC4.2 | Avaliação de deficiências | Processo formal integrado ao registro de riscos com workflow de escalação | 2-3 dias | Média |
| CC6.5 | Automação de descarte | Job schedulado que purga dados conforme políticas de retenção + logs de execução | 2-3 dias | Média |
| CC9.2 | Avaliação de fornecedores | Questionário de segurança + score automático + dashboard de fornecedores + alertas de renovação | 4-5 dias | Média |
| P7.1 | Limpeza de dados | Job de data quality + relatório de inconsistências + sugestões de correção | 2-3 dias | Baixa |
| A.6.4 | Processo disciplinar | Workflow: registrar incidente → investigação → comitê → decisão → ação → registro | 2-3 dias | Baixa |
| BCM-09 | Comunicação de crise | Templates pré-configurados + disparo automático para stakeholders por canal | 2-3 dias | Média |

##### Dashboards e Relatórios

| ID | Item | O que Construir | Esforço | Prioridade |
|----|------|-----------------|---------|------------|
| LGPD-O2 | Geração de RIPD | Template de Relatório de Impacto + geração automática baseada em dados da plataforma | 3-4 dias | Alta |
| CMN-05 | Relatório anual BACEN | Template de relatório + preenchimento automático com métricas da plataforma | 2-3 dias | Alta |
| CC1.2 | Estrutura de governança | Registro de comitês, membros, reuniões, decisões + dashboard de governança | 2-3 dias | Média |
| ETH-07 | Detecção de drift IA | Job comparando métricas de modelos ao longo do tempo + alertas de degradação | 4-5 dias | Média |
| EUAI-02 | Dashboard qualidade IA | Métricas de qualidade, acurácia, latência, disponibilidade do sistema de IA | 3-4 dias | Média |

##### Registros e Coleta de Dados

| ID | Item | O que Construir | Esforço | Prioridade |
|----|------|-----------------|---------|------------|
| CC3.2 | Categoria de fraude | Adicionar tipo "fraud" no registro de riscos + campos específicos | 1 dia | Baixa |
| A.5.6 | Contato com ISACs | Registro de participação em grupos de segurança (CERT.br, etc.) | 1 dia | Baixa |
| A.5.7 | Feed de threat intel | Integração com feeds públicos (CISA, CERT.br) + alertas automáticos | 2-3 dias | Média |
| A.8.11 | Mascaramento de dados | Aplicar mascaramento em exports, logs, visualizações de dados sensíveis | 3-4 dias | Média |
| A.8.30 | Avaliação de terceirização | Checklist de segurança para fornecedores de desenvolvimento + registro | 2 dias | Baixa |
| EUAI-12 | Monitoramento pós-mercado | Formalizar processo existente + documentação + métricas | 1-2 dias | Baixa |

##### Resumo de Esforço Interno

| Prioridade | Quantidade | Dias Estimados |
|------------|------------|----------------|
| Alta | 6 itens | 18-26 dias |
| Média | 11 itens | 28-38 dias |
| Baixa | 5 itens | 9-13 dias |
| **TOTAL** | **22 itens** | **55-77 dias** |

---

#### 12.12.2 Itens que Requerem Contratação Externa (8 itens)

| ID | Item | Por que não resolve com código | Ação Necessária | Custo Estimado |
|----|------|--------------------------------|-----------------|----------------|
| A.8.29 / BANK-01 | Pentest anual | Deve ser realizado por terceiro independente para validade em auditorias | Contratar empresa de pentest certificada (CEH, OSCP) | R$ 30-80k/ano |
| A.8.8 / BANK-02 | Scan de vulnerabilidades | Ferramentas enterprise oferecem cobertura mais completa | Licenciar Snyk, Qualys, ou Veracode | R$ 20-50k/ano |
| NYC-06 | Auditor de viés IA | NYC Local Law 144 exige auditor independente externo | Contratar consultor/empresa especializada em bias audit | R$ 50-100k/ano |
| EUAI-10 | Conformity assessment | EU AI Act exige avaliação por organismo notificado | Contratar certificadora quando operar na UE | R$ 100-200k (único) |
| EUAI-11 | Registro banco de dados UE | Ação administrativa junto à autoridade europeia | Registrar quando iniciar operação na União Europeia | R$ 5-10k |
| A.6.1 | Background check | Serviço externo de verificação de antecedentes | Integrar com provedor (Certifix, Vérios, etc.) | R$ 30-50/verificação |
| A.8.1 | MDM (Mobile Device Management) | Solução enterprise para gestão de dispositivos | Licenciar Jamf, Microsoft Intune, ou VMware | R$ 30-60k/ano |
| A.8.12 | DLP (Data Loss Prevention) | Ferramenta especializada em prevenção de vazamento | Licenciar Netskope, Symantec DLP, ou Microsoft Purview | R$ 40-80k/ano |

##### Resumo de Investimento Externo

| Categoria | Itens | Investimento Anual |
|-----------|-------|-------------------|
| Segurança (Pentest + Scan) | 2 | R$ 50-130k |
| Auditoria de IA | 1 | R$ 50-100k |
| Ferramentas (MDM + DLP) | 2 | R$ 70-140k |
| Compliance EU (se aplicável) | 2 | R$ 105-210k (único) |
| Background check | 1 | Variável por uso |
| **TOTAL (sem EU)** | **5** | **R$ 170-370k/ano** |
| **TOTAL (com EU)** | **7** | **R$ 275-580k (1º ano)** |

---

#### 12.12.3 Cronograma de Implementação Detalhado

##### Fase 1: Q1 2026 - Fundação SOX/BACEN (Prioridade Alta)

| Semana | Item | Tipo | Responsável |
|--------|------|------|-------------|
| 1-2 | Workflow de recertificação de acessos | Desenvolvimento | TI |
| 2-3 | Sign-off da administração | Desenvolvimento | TI |
| 3-4 | Testes de controles com evidências | Desenvolvimento | TI |
| 4-5 | Relatório anual BACEN | Desenvolvimento | TI |
| 5-6 | Geração automática de RIPD | Desenvolvimento | TI |
| Paralelo | Contratação de pentest | Contratação | Compras |
| Paralelo | Licenciamento scan de vulnerabilidades | Contratação | TI/Compras |

##### Fase 2: Q2 2026 - Governança e Processos (Prioridade Média-Alta)

| Semana | Item | Tipo | Responsável |
|--------|------|------|-------------|
| 1-2 | Relatórios de deficiências | Desenvolvimento | TI |
| 2-3 | Estrutura de governança | Desenvolvimento | TI |
| 3-4 | Avaliação de fornecedores | Desenvolvimento | TI |
| 4-5 | Automação de descarte | Desenvolvimento | TI |
| 5-6 | Comunicação de crise | Desenvolvimento | TI |
| Paralelo | Contratação auditor de viés IA | Contratação | Compliance |

##### Fase 3: Q3 2026 - IA e Refinamentos (Prioridade Média)

| Semana | Item | Tipo | Responsável |
|--------|------|------|-------------|
| 1-2 | Detecção de drift IA | Desenvolvimento | Data Science |
| 2-3 | Dashboard qualidade IA | Desenvolvimento | Data Science |
| 3-4 | Feed de threat intel | Desenvolvimento | Security |
| 4-5 | Mascaramento de dados | Desenvolvimento | TI |
| 5-6 | Reconciliação de dados | Desenvolvimento | TI |

##### Fase 4: Q4 2026 - Finalização (Prioridade Baixa)

| Semana | Item | Tipo | Responsável |
|--------|------|------|-------------|
| 1-2 | Processo disciplinar | Desenvolvimento | RH/TI |
| 2-3 | Limpeza de dados | Desenvolvimento | TI |
| 3-4 | Categoria de fraude + ISACs | Desenvolvimento | Compliance |
| 4-5 | Avaliação de terceirização | Desenvolvimento | TI |
| Paralelo | Avaliação MDM/DLP (se necessário) | Contratação | TI/Compras |

---

#### 12.12.4 Impacto nos Scores de Compliance

##### Após Implementação Completa (Desenvolvimento + Contratações)

| Framework | Score Atual | Score Projetado | Delta |
|-----------|-------------|-----------------|-------|
| **SOX 404** | 77% | 100% | +23% |
| **SOC 2 Type II** | 86% | 100% | +14% |
| **ISO 27001:2022** | 72% | 95%* | +23% |
| **LGPD** | 96% | 100% | +4% |
| **BCB 498/2025** | 100% | 100% | - |
| **Governança de IA** | 83% | 97%** | +14% |
| **BACEN/Bancos** | 91% | 100% | +9% |
| **ISO 22301** | 90% | 100% | +10% |
| **Auditoria de TI** | 100% | 100% | - |
| **TOTAL** | **87%** | **99%** | **+12%** |

*ISO 27001 limitado por controles dependentes de infraestrutura física (cloud provider)
**EU AI Act depende de decisão de operar na União Europeia

---

#### 12.12.5 Especificações Técnicas para Desenvolvimento

##### 12.12.5.1 Workflow de Recertificação de Acessos

**Tabelas necessárias:**
```
access_recertification_campaigns (id, name, start_date, end_date, status, created_by)
access_recertification_items (id, campaign_id, user_id, role_id, reviewer_id, decision, decided_at, justification)
```

**API endpoints:**
```
POST   /api/v1/access-recertification/campaigns
GET    /api/v1/access-recertification/campaigns
GET    /api/v1/access-recertification/campaigns/{id}/items
PUT    /api/v1/access-recertification/items/{id}/decide
GET    /api/v1/access-recertification/pending
GET    /api/v1/access-recertification/stats
```

**Frontend:**
- Dashboard de campanhas ativas
- Lista de acessos pendentes de revisão por gestor
- Formulário de decisão (manter/revogar) com justificativa obrigatória
- Relatório de evidências para auditoria

##### 12.12.5.2 Sign-off da Administração (SOX)

**Tabelas necessárias:**
```
sox_signoff_periods (id, period_type, start_date, end_date, status)
sox_signoff_attestations (id, period_id, signer_id, signer_role, signed_at, signature_hash, attestation_text)
```

**API endpoints:**
```
POST   /api/v1/sox-signoff/periods
GET    /api/v1/sox-signoff/periods
GET    /api/v1/sox-signoff/periods/{id}
POST   /api/v1/sox-signoff/periods/{id}/sign
GET    /api/v1/sox-signoff/pending
GET    /api/v1/sox-signoff/history
```

**Frontend:**
- Lista de períodos aguardando assinatura
- Tela de atestado com texto legal
- Assinatura digital (com senha ou MFA)
- Histórico de atestados com download de evidência

##### 12.12.5.3 Geração Automática de RIPD

**Tabelas necessárias:**
```
ripd_reports (id, company_id, generated_at, version, status, pdf_path)
ripd_data_mapping (id, report_id, data_category, legal_basis, purpose, retention, recipients)
```

**API endpoints:**
```
POST   /api/v1/ripd/generate
GET    /api/v1/ripd/reports
GET    /api/v1/ripd/reports/{id}
GET    /api/v1/ripd/reports/{id}/download
GET    /api/v1/ripd/data-mapping
```

**Dados coletados automaticamente:**
- Categorias de dados de `candidates`, `users`
- Bases legais de `consent_versions`
- Políticas de retenção de `audit_retention_policies`
- Subprocessadores de `subprocessors`
- Controles de `compliance_controls`

##### 12.12.5.4 Detecção de Drift em Modelos IA

**Tabelas necessárias:**
```
model_drift_snapshots (id, model_name, snapshot_date, metrics_json, baseline_id)
model_drift_alerts (id, snapshot_id, metric_name, expected_value, actual_value, deviation_pct, severity)
```

**API endpoints:**
```
POST   /api/v1/model-drift/snapshot
GET    /api/v1/model-drift/snapshots
GET    /api/v1/model-drift/alerts
GET    /api/v1/model-drift/trends/{model_name}
PUT    /api/v1/model-drift/baseline/{model_name}
```

**Métricas monitoradas:**
- Precisão de screening (comparação com decisões humanas)
- Distribuição de scores
- Taxa de intervenção humana
- Tempo de resposta
- Disparate impact por categoria protegida

---

#### 12.12.6 Checklist de Validação Pós-Implementação

| Item | Critério de Aceite | Validador |
|------|-------------------|-----------|
| Recertificação de acessos | Campanha executada com 100% de respostas | Compliance |
| Sign-off SOX | Atestado assinado por todos os diretores | CFO |
| Testes de controles | 100% dos controles críticos testados | Auditoria |
| RIPD | Relatório gerado e revisado pelo DPO | DPO |
| Pentest | Relatório entregue, vulnerabilidades críticas remediadas | CISO |
| Scan de vulnerabilidades | Zero vulnerabilidades críticas/altas abertas | CISO |
| Auditor de viés | Relatório anual publicado no Trust Center | Compliance |
| Drift IA | Baseline estabelecido, alertas configurados | Data Science |

---

## 13. ANEXOS

### 13.1 Glossário

| Termo | Definição |
|-------|-----------|
| BCB 498 | Resolução do Banco Central sobre seguro cibernético |
| BIA | Business Impact Analysis |
| DPO | Data Protection Officer (Encarregado LGPD) |
| DRP | Disaster Recovery Plan |
| LGPD | Lei Geral de Proteção de Dados |
| MTPD | Maximum Tolerable Period of Disruption |
| RPO | Recovery Point Objective |
| RTO | Recovery Time Objective |
| SoD | Segregation of Duties |
| SOC 2 | Service Organization Control 2 |
| SOX | Sarbanes-Oxley Act |
| WSI | Work Sample Interview |

### 12.2 Contatos

| Função | Responsabilidade |
|--------|------------------|
| DPO | Proteção de dados e LGPD |
| CISO | Segurança da informação |
| Compliance Officer | Conformidade regulatória |
| Risk Manager | Gestão de riscos |

---

**Documento gerado em:** Dezembro 2025  
**Próxima revisão:** Março 2026  
**Versão:** 1.0
