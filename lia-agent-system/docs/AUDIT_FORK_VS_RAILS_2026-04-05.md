# AUDITORIA PROFUNDA: Fork Replit vs Rails ats-api-copia
> Data: 2026-04-05 | Gerado por análise automatizada completa do código

---

## 1. ESCALA DOS DOIS SISTEMAS

| Métrica | Fork (Replit) | Rails (ats-api-copia) | Ratio |
|---------|:---:|:---:|:---:|
| Tabelas/Models | **287** | **11** | 26x |
| Endpoints | **1,727** | **29** | 60x |
| Services | **~130** | **4** | 33x |
| Domínios DDD | **12** | **0** | ∞ |
| Workers | Celery + aio-pika | 2 (Sneakers) | — |
| WebSockets | **5** | 1 (ActionCable) | 5x |

---

## 2. RAILS — INVENTÁRIO COMPLETO (11 tabelas, 29 endpoints)

### 2.1 Tabelas

| Tabela | Colunas chave | Propósito |
|--------|--------------|-----------|
| `accounts` | name, tenant, staging_tenant | Multi-tenancy root (Apartment gem) |
| `users` | email, password_digest, account_id | Auth (bcrypt + JWT 24h) |
| `roles` | name, description | RBAC definitions |
| `permissions` | name, description | Permission definitions |
| `user_roles` | user_id, role_id | Join table |
| `role_permissions` | role_id, permission_id | Join table |
| `user_permissions` | user_id, permission_id | Join table |
| `jobs` | title, description, user_id, account_id, provider, city, state, workplace_type + 10 mais | Vagas (22 colunas) |
| `candidates` | uid, name, surname, email, cpf, 30+ campos de endereço/salário/contato | Candidatos (40 colunas) |
| `applies` | candidate_id, job_id, selective_process_id, is_deleted | Candidaturas (soft-delete) |
| `selective_processes` | name, position, status (enum), job_id, sub_status (JSONB) | Pipeline stages |
| `messages` | content, entity (enum), status, reference_type/id, metadata (JSONB) | Mensagens |

### 2.2 Endpoints Rails

```
POST   /v1/sessions              → Login
GET    /v1/me                    → Current user
POST   /v1/logout                → Logout

CRUD   /v1/users/jobs            → 5 endpoints
CRUD   /v1/users/candidates      → 5 endpoints
CRUD   /v1/users/applies         → 5 endpoints
CRUD   /v1/users/selective_processes → 5 endpoints
CRUD   /v1/users/messages        → 5 endpoints
CRUD   /v1/users/users           → 4 endpoints (search, create, edit, delete)
```

### 2.3 Dependências Rails

- **Auth:** bcrypt, jwt
- **Search:** Searchkick + Elasticsearch
- **Multi-tenancy:** ros-apartment (schema-based)
- **Async:** Sidekiq + Sneakers (RabbitMQ)
- **API format:** JSONAPI::Serializer
- **Real-time:** ActionCable (Redis)

### 2.4 Gaps no Rails (observados na auditoria)

- RBAC configurado mas **NÃO enforced** nos controllers
- `apply_statuses` — migration existe mas tabela NÃO no schema.rb
- `JobImportWorker` tem `user_id=1, account_id=1` hardcoded (risco produção)
- Sem validação de recursos por permission
- JWT sem refresh token

---

## 3. FORK REPLIT — INVENTÁRIO (287 tabelas, 1727 endpoints)

### 3.1 Endpoints por grupo

| Grupo | Descrição | Endpoints | % |
|-------|-----------|:---------:|:-:|
| **A** | IA Pura (screening, chat, WSI, embeddings, agents, ML) | ~450 | 26% |
| **B** | CRUD Dados ATS (candidates, jobs, applies, pipeline) | ~400 | 23% |
| **C** | Features sem equivalente Rails (company, billing, comm, LGPD) | ~600 | 35% |
| **D** | Admin/Internal (health, monitoring, observability) | ~277 | 16% |

### 3.2 Tabelas por categoria (287 únicas)

| Categoria | Qtd | Exemplos |
|-----------|:---:|---------|
| IA/Agents/ML | ~35 | agent_working_memory, calibration_*, intelligence_insights |
| Screening/WSI | ~12 | triagem_sessions, voice_screening_calls, rubric_evaluations |
| Candidates (avançado) | ~14 | candidate_experiences, candidate_education, candidate_lists |
| Jobs (avançado) | ~13 | job_templates, job_drafts, salary_benchmarks, job_embeddings |
| Pipeline/Automation | ~15 | recruitment_stages, stage_automation_rules, planned_tasks |
| Communication | ~18 | whatsapp_conversations, teams_messages, email_templates |
| Billing/SaaS | ~10 | subscriptions, invoices, ai_consumption, client_saas_metrics |
| LGPD/Compliance | ~16 | consent_records, data_requests, audit_logs, sox_controls |
| Governance/Risk | ~20 | bias_audit_reports, risk_entries, sod_roles, insurance_policies |
| Company/Org | ~15 | company_profiles, departments, benefits, culture_values |
| Admin/Settings | ~13 | admin_roles, security_settings, notification_policies |
| Integrations | ~13 | ats_connections, webhooks, integration_providers |
| Auth/WorkOS | ~5 | workos_groups, sso_audit_logs, company_workos_config |
| Observability | ~25 | data_access_logs, breach_notifications, disaster_recovery_plans |
| Recruiter | ~7 | recruiter_profiles, personalization_settings |
| Skills/Catalog | ~7 | company_skills_catalog, behavioral_competencies_catalog |
| Policies | ~11 | business_rules, rate_limit_rules, guardrails |
| Journey/Templates | ~7 | journey_blueprints, default_templates |
| Search/Feedback | ~10 | shared_searches, search_feedbacks, candidate_searches |
| Misc | ~41 | conversations, notifications, approval_requests, etc. |

---

## 4. DECISÃO ARQUITETURAL PROPOSTA

### Princípio: O Fork é o produto. O Rails é o legado que precisa evoluir.

O Rails hoje é um CRUD básico de ATS com 11 tabelas. O Fork tem 287 tabelas com IA, compliance, comunicação, billing e 12 domínios DDD. 

A questão NÃO é "o que criar no Rails" — são 180+ tabelas. A questão é:

### **Qual é o papel de cada sistema?**

#### Opção 1: Rails = Fonte de verdade para CRUD ATS + Auth
```
Rails serve: candidates, jobs, applies, pipeline, users, auth, search (Elasticsearch)
Fork serve: TUDO o resto (IA, billing, comms, LGPD, admin, etc.)
Fork chama Rails: para CRUD de entidades ATS (via ATSAPIClient)
Rails chama Fork: via RabbitMQ events (screening.completed, etc.)
```
**Work C reduzido:** Expandir ~4 tabelas Rails (jobs, candidates) com campos faltantes. ~20 migrations.
**Pro:** Menor esforço. Fork já funciona standalone.
**Contra:** Dois bancos, dois sistemas de auth, complexidade operacional.

#### Opção 2: Migrar tudo para Rails (consolidar)
```
Rails = backend único com todas as 287+ tabelas
Fork vira apenas serviço de IA (sem DB próprio)
```
**Work C massivo:** ~200 migrations, ~150 models, ~100 controllers em Ruby.
**Pro:** Simplificação arquitetural a longo prazo.
**Contra:** Meses de trabalho. Reescrever Python→Ruby.

#### Opção 3 (RECOMENDADA): Fork = Backend principal, Rails = Bridge legado
```
Fork = backend oficial do produto (já tem 287 tabelas, 1727 endpoints)
Rails = bridge temporário que:
  - Serve auth para apps legados
  - Redireciona para Fork endpoints gradualmente
  - Eventualmente desativado
```
**Work C mínimo:** Configurar Rails como proxy/gateway para o Fork.
**Pro:** Menor esforço. Fork já é 26x maior que Rails.
**Contra:** Precisa de decisão organizacional. Rails team pode resistir.

---

## 5. GAPS DETALHADOS POR CATEGORIA

### 5.1 Entidades sobrepostas (Fork ↔ Rails)

| Entidade | Fork | Rails | Mapeamento | Status |
|----------|------|-------|------------|--------|
| Candidates | UUID, 60+ cols, PII encrypted, embeddings | bigint, 40 cols, plaintext CPF | `rails_adapter.py` completo | ✅ Adapter pronto |
| Jobs | UUID, 40+ cols, screening_questions, stages | bigint, 22 cols, básico | `rails_adapter.py` completo | ✅ Adapter pronto |
| Applies | `vacancy_candidates` / `applications` | `applies` (soft-delete) | `rails_adapter.py` básico | ✅ Adapter pronto |
| Pipeline | `recruitment_stages` (rich, automation) | `selective_processes` (5 auto) | Parcial | ⚠️ Fork muito mais completo |
| Users | WorkOS SSO, company_id, roles | bcrypt, account_id | `rails_jwt.py` | ✅ Bridge pronto |
| Messages | 3 sistemas (conv, whatsapp, teams) | 1 tabela JSONB | Sem adapter | ❌ Fork é fonte |

### 5.2 Campos que Rails precisa ganhar (se Opção 1)

**jobs → expandir:**
- department, seniority_level, employment_type
- salary_range (JSON), bonus_range (JSON)
- technical_requirements (JSON array)
- behavioral_competencies (JSON array)
- screening_questions (JSON array)
- interview_stages (JSON array)
- deadline_screening, deadline_shortlist, deadline_closing
- priority, urgency_level
- affirmative_criteria (6 campos)
- organizational_structure (JSON)

**candidates → expandir:**
- skills (ARRAY), seniority_detected
- cultural_fit (float), lia_score (float)
- is_pii_encrypted (boolean)
- Tabelas relacionadas: candidate_experiences (40+ cols), candidate_education

### 5.3 Features INTEIRAS que só o Fork tem

| Feature | Tabelas | Endpoints | Complexidade |
|---------|:-------:|:---------:|:------------:|
| Company/Org management | 15 | 69+ | Alta |
| Billing (Stripe+Iugu) | 10 | 25 | Alta |
| WhatsApp | 2 | 8 | Média |
| Teams bot | 4 | 17 | Alta |
| Email + tracking | 4 | 15+ | Média |
| LGPD compliance | 16 | 20+ | Alta |
| Interview scheduling | 7 | 10+ | Média |
| Automation engine | 6 | 30+ | Alta |
| Trust center | 4 | 13 | Média |
| Insurance/Risk (BCB 498) | 11 | 27+ | Alta |
| WorkOS SSO/SCIM | 5 | 7+ | Média |
| Skills catalog | 7 | 7 | Baixa |
| Recruiter profiles | 7 | 8 | Baixa |
| Admin panels | 13 | 17+ | Média |
| Multi-client (B2B) | 2 | 26+ | Alta |
| Governance/SOD | 8 | 10+ | Alta |
| Journey mapping | 3 | 2+ | Baixa |
| Shared searches | 4 | 7 | Baixa |

---

## 6. ESTADO ATUAL DOS WORKS

### Work A — Multi-tenancy ✅ ~95%
- MemoryResolver particionado por company_id ✅
- Auth enforcement middleware ✅
- Tenant guard (JWT-validated company_id) ✅
- Session IDs scoped (`create_session_id`) ✅ (3 pontos faltam migrar)

### Work B — Preparação Rails ✅ B0-B5, ⚠️ B6 parcial
- B1: rails_jwt.py ✅
- B2: WeDOTalentATSClient ✅
- B3-B5: Event schemas, frontend config ✅
- B6: RailsAdapter existe ✅ mas NÃO está wired nos endpoints ⚠️

### Work C — Complementar Rails ❌ 0%
- Depende de decisão arquitetural (Opção 1, 2, ou 3)
- Se Opção 1: ~20 migrations + ~5 controllers Ruby
- Se Opção 3: Rails vira proxy, mínimo de trabalho

### Work D — Go-live 🔒 Bloqueado

### Work E — Choose Your AI ✅ ~85%
- E1: LLMService wrapper + monkey-patch bootstrap ✅
- E2: API config (4 endpoints) ✅
- E3: DB table + model ✅
- E4: Frontend proxy route ✅ (tela em desenvolvimento)
- E5: Routing per-operation — data model pronto, wiring pendente ⚠️
- E6: Audit log básico, sem dashboard ⚠️

---

## 7. RECOMENDAÇÃO DE PRÓXIMOS PASSOS

1. **DECIDIR arquitetura** (Opção 1, 2, ou 3) — bloqueante para Work C
2. **Fechar gaps rápidos:**
   - A2: Migrar 3 session IDs (~15 min)
   - E5: Wire routing per-operation no LLMService (~1h)
3. **Atualizar RAILS_GAPS.md** com este documento
4. **Work C:** Implementar conforme opção escolhida
5. **B6.3:** Wire RailsAdapter nos endpoints via Depends()
