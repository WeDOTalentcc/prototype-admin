# DATABASE_SCHEMA_INTEGRITY_AUDIT
**Protocolo:** PX04 — Auditoria de Integridade do Banco de Dados
**Data:** 2026-04-14
**DBA Executor:** Claude Sonnet 4.6 (Protocolo PX04)
**Ambiente:** Rails 7.1 (GCP PostgreSQL) + Python/FastAPI (Replit PostgreSQL)

---

## Seção 1: Sumário Executivo

### Contagens

| Item | Valor |
|------|-------|
| Tabelas no schema.rb (produção) | **12** |
| Models Rails (arquivos .rb) | **~90** (excl. concerns/application_record) |
| Migrations Rails (total) | **85** |
| Migrations executadas (schema.rb versão) | **18** (até 20250714142059) |
| Migrations NÃO aplicadas ao schema.rb | **~67** |
| Modelos SQLAlchemy Python (__tablename__) | **13** declarativos + tabelas via raw SQL |
| Tabelas Python via raw SQL (database.py) | **~20** |
| Migrations Alembic | **76** (001→076) |
| Vector Store | **pgvector** (PostgreSQL nativo) |
| Collections pgvector | **2** (conversation_memories, knowledge_base) |

### Score de Integridade

| Banco | Score | Classificação |
|-------|-------|---------------|
| Rails PostgreSQL (schema.rb) | **32/100** | CRITICO — drift severo |
| Python PostgreSQL (Alembic) | **72/100** | MODERADO — migrations em dia mas tabelas raw SQL fora de controle |

### Top Findings Criticos

1. **DRIFT CATASTROFICO**: `schema.rb` está na versão `20250714_142059`, mas existem 67 migrations posteriores (até `20250716`). Tabelas inteiras — `apply_statuses`, expansões de `candidates`/`jobs`/`users`, `talent_pools`, `recruitment_campaigns`, `client_accounts`, LGPD, webhooks, ATS integrations — estão nos arquivos de migration mas AUSENTES do `schema.rb`.
2. **~78 models Rails sem tabela no schema.rb**: O schema.rb registra apenas 12 tabelas, mas há ~90 model files. A maioria dos models aponta para tabelas que existem apenas nas migrations não aplicadas.
3. **`candidates` sem `account_id` no schema.rb**: Migration `20250714150818` adiciona `account_id` a `candidates`, `applies` e `selective_processes` com FK — mas essa migration NÃO está refletida no schema.rb atual (versão parada em 142059 do mesmo dia, antes da 150818).
4. **`selective_processes` tem `belongs_to :account`** no model, mas `account_id` e FK não estão no schema.rb.
5. **ID type mismatch critico**: Rails usa `bigint` para PKs; Python usa `UUID`. No mapeamento `CANDIDATE_FORK_TO_RAILS`, o campo `id` mapeia diretamente mas os tipos são incompatíveis — sem conversão explícita, a sincronia vai falhar silenciosamente.
6. **`users` sem índice em `email`**: Campo crítico para autenticação não tem índice no schema.rb atual.
7. **`user_onboarding_extension.rb` é comentário, não código**: Extensões de onboarding do `User` (activation_state, onboarding_lia_enabled, etc.) existem apenas como comentário em um arquivo, nunca foram aplicadas ao `user.rb`.
8. **`apply_statuses` tabela ausente do schema.rb**: A migration `20250714150600` cria a tabela, mas o schema.rb foi gerado em `142059` do mesmo dia — a tabela não está no schema.rb. O model `ApplyStatus` referencia uma tabela inexistente no schema.

---

## Seção 2: Models Rails vs. Schema

### Tabelas presentes no schema.rb (12 tabelas)

| Tabela | Model Correspondente | Situação |
|--------|---------------------|----------|
| accounts | account.rb | OK |
| applies | apply.rb | PARCIAL — faltam campos (account_id, source, status, lia_score, fork_uuid) |
| candidates | candidate.rb | PARCIAL — faltam account_id + todos os campos Work C |
| jobs | job.rb | PARCIAL — faltam ~40 campos da migration expand_jobs |
| messages | message.rb | OK |
| permissions | permission.rb | OK |
| role_permissions | role_permission.rb | OK |
| roles | role.rb | OK |
| selective_processes | selective_process.rb | PARCIAL — faltam account_id + campos expand |
| user_permissions | user_permission.rb | OK |
| user_roles | user_role.rb | OK |
| users | user.rb | PARCIAL — faltam name, role, permissions, workos_user_id, activation_state, invitation_token, phone, onboarding_lia_override, fork_uuid |

### Models com tabela AUSENTE do schema.rb (drift de migrations)

| Model | Tabela Esperada | Migration que Cria | Severidade |
|-------|-----------------|--------------------|------------|
| apply_status.rb | apply_statuses | 20250714150600 | 🔴 CRITICO |
| talent_pool.rb | talent_pools | 20250716000002 | 🔴 CRITICO |
| talent_pool_candidate.rb | talent_pool_candidates | 20250716000002 | 🔴 CRITICO |
| client_account.rb | client_accounts | 20250715000001 | 🔴 CRITICO |
| client_user.rb | client_users | 20250715000002 | 🔴 CRITICO |
| company_profile.rb | company_profiles | 20250715000003 | 🔴 CRITICO |
| department.rb | departments | 20250715000004 | 🔴 CRITICO |
| benefit.rb | benefits | 20250715000005 | 🔴 CRITICO |
| culture_value.rb | culture_values | 20250715000006 | 🔴 CRITICO |
| ideal_profile.rb | ideal_profiles | 20250715000007 | 🔴 CRITICO |
| company_hiring_policy.rb | company_hiring_policies | 20250715000008 | 🔴 CRITICO |
| compensation_policy.rb | compensation_policies | 20250715000009 | 🔴 CRITICO |
| email_template.rb | email_templates | 20250715000010 | 🔴 CRITICO |
| email_log.rb | email_logs | 20250715000011 | 🔴 CRITICO |
| email_tracking_event.rb | email_tracking_events | 20250715000011 | 🔴 CRITICO |
| subscription.rb | subscriptions | 20250715000012 | 🔴 CRITICO |
| invoice.rb | invoices | 20250715000012 | 🔴 CRITICO |
| payment_method.rb | payment_methods | 20250715000012 | 🔴 CRITICO |
| consent_record.rb | consent_records | 20250715000013 | 🔴 CRITICO |
| consent_event.rb | consent_events | 20250715000013 | 🔴 CRITICO |
| consent_version.rb | consent_versions | 20250715000013 | 🔴 CRITICO |
| data_subject_request.rb | data_subject_requests | 20250715000013 | 🔴 CRITICO |
| company_retention_policy.rb | company_retention_policies | 20250715000013 | 🔴 CRITICO |
| audit_log.rb | audit_logs | 20250715000014 | 🔴 CRITICO |
| admin_audit_log.rb | admin_audit_logs | 20250715000014 | 🔴 CRITICO |
| audit_retention_policy.rb | audit_retention_policies | 20250715000014 | 🔴 CRITICO |
| automated_decision_explanation.rb | automated_decision_explanations | 20250715000014 | 🔴 CRITICO |
| notification.rb | notifications | 20250715000015 | 🔴 CRITICO |
| notification_policy.rb | notification_policies | 20250715000015 | 🔴 CRITICO |
| chat_notification.rb | chat_notifications | 20250715000015 | 🔴 CRITICO |
| webhook.rb | webhooks | 20250715000016 | 🔴 CRITICO |
| webhook_delivery_log.rb | webhook_delivery_logs | 20250715000016 | 🔴 CRITICO |
| webhook_registration.rb | webhook_registrations | 20250715000016 | 🔴 CRITICO |
| webhook_log.rb | webhook_logs | 20250715000016 | 🔴 CRITICO |
| interview.rb | interviews | 20250715000017 | 🔴 CRITICO |
| interview_feedback.rb | interview_feedbacks | 20250715000017 | 🔴 CRITICO |
| interview_note.rb | interview_notes | 20250715000017 | 🔴 CRITICO |
| interview_reminder.rb | interview_reminders | 20250715000017 | 🔴 CRITICO |
| reschedule_history.rb | reschedule_histories | 20250715000017 | 🔴 CRITICO |
| calendar_availability.rb | calendar_availabilities | 20250715000017 | 🔴 CRITICO |
| self_scheduling_link.rb | self_scheduling_links | 20250715000017 | 🔴 CRITICO |
| ats_connection.rb | ats_connections | 20250715000018 | 🔴 CRITICO |
| ats_candidate.rb | ats_candidates | 20250715000018 | 🔴 CRITICO |
| ats_job_mapping.rb | ats_job_mappings | 20250715000018 | 🔴 CRITICO |
| ats_sync_job.rb | ats_sync_jobs | 20250715000018 | 🔴 CRITICO |
| ats_webhook_log.rb | ats_webhook_logs | 20250715000018 | 🔴 CRITICO |
| integration_connection.rb | integration_connections | 20250715000018 | 🔴 CRITICO |
| integration_provider.rb | integration_providers | 20250715000018 | 🔴 CRITICO |
| integration_sync_log.rb | integration_sync_logs | 20250715000018 | 🔴 CRITICO |
| integration_webhook.rb | integration_webhooks | 20250715000018 | 🔴 CRITICO |
| recruitment_automation.rb | recruitment_automations | 20250715000019 | 🔴 CRITICO |
| recruitment_sla.rb | recruitment_slas | 20250715000019 | 🔴 CRITICO |
| sla_violation.rb | sla_violations | 20250715000019 | 🔴 CRITICO |
| hiring_plan.rb | hiring_plans | 20250715000020 | 🔴 CRITICO |
| planned_headcount.rb | planned_headcounts | 20250715000020 | 🔴 CRITICO |
| workforce_entry.rb | workforce_entries | 20250715000020 | 🔴 CRITICO |
| email_template.rb (template) | template_categories | 20250715000021 | 🔴 CRITICO |
| pipeline_template.rb | pipeline_templates | 20250715000021 | 🔴 CRITICO |
| job_template.rb | job_templates | 20250715000021 | 🔴 CRITICO |
| benefit_template.rb | benefit_templates | 20250715000021 | 🔴 CRITICO |
| template_usage_log.rb | template_usage_logs | 20250715000021 | 🔴 CRITICO |
| approval_request.rb | approval_requests | 20250715000022 | 🔴 CRITICO |
| pending_approval.rb | pending_approvals | 20250715000022 | 🔴 CRITICO |
| goal.rb | goals | 20250715000023 | 🔴 CRITICO |
| goal_template.rb | goal_templates | 20250715000023 | 🔴 CRITICO |
| shared_search.rb | shared_searches | 20250715000023 | 🔴 CRITICO |
| shared_search_access.rb | shared_search_accesses | 20250715000023 | 🔴 CRITICO |
| shared_search_feedback.rb | shared_search_feedbacks | 20250715000023 | 🔴 CRITICO |
| big_five_question.rb | big_five_questions | 20250715000024 | 🔴 CRITICO |
| big_five_role_profile.rb | big_five_role_profiles | 20250715000024 | 🔴 CRITICO |
| technical_question.rb | technical_questions | 20250715000024 | 🔴 CRITICO |
| technical_test_template.rb | technical_test_templates | 20250715000024 | 🔴 CRITICO |
| candidate_experience.rb | candidate_experiences | 20250715000025 | 🔴 CRITICO |
| candidate_education.rb | candidate_education | 20250715000025 | 🔴 CRITICO |
| candidate_attachment.rb | candidate_attachments | 20250715000025 | 🔴 CRITICO |
| recruitment_campaign.rb | recruitment_campaigns | 20250716000003 | 🔴 CRITICO |
| campaign_stage_event.rb | campaign_stage_events | 20250716000003 | 🔴 CRITICO |
| magic_link.rb | magic_links | (migration onboarding) | 🔴 CRITICO |
| onboarding_session.rb | onboarding_sessions | (migration onboarding) | 🔴 CRITICO |
| onboarding_message.rb | onboarding_messages | (migration onboarding) | 🔴 CRITICO |
| recruitment_email_template.rb | recruitment_email_templates | — | 🟡 ALTO |
| ai_consumption.rb | ai_consumptions | — | 🟡 ALTO |
| ai_credits_balance.rb | ai_credits_balances | — | 🟡 ALTO |
| import_job.rb | import_jobs | — | 🟡 ALTO |

### Campos críticos ausentes nas tabelas que EXISTEM no schema.rb

**Tabela `candidates` (schema.rb tem 42 campos; migrations adicionariam mais ~30):**

| Campo | Referenciado em | Status no schema.rb |
|-------|----------------|---------------------|
| account_id | model (`belongs_to :account`) + migration 20250714150818 | AUSENTE |
| seniority_level | CANDIDATE_FORK_TO_RAILS + migration 20250715000025 | AUSENTE |
| technical_skills | CANDIDATE_FORK_TO_RAILS + migration 20250715000025 | AUSENTE |
| soft_skills | CANDIDATE_FORK_TO_RAILS | AUSENTE |
| languages | CANDIDATE_FORK_TO_RAILS | AUSENTE |
| certifications | CANDIDATE_FORK_TO_RAILS | AUSENTE |
| years_of_experience | CANDIDATE_FORK_TO_RAILS | AUSENTE |
| diversity_* (10 campos) | CANDIDATE_FORK_TO_RAILS + migration | AUSENTE |
| fork_uuid | migration 20250715000025 | AUSENTE |

**Tabela `users` (schema.rb tem apenas: email, password_digest, account_id + timestamps):**

| Campo | Referenciado em | Status no schema.rb |
|-------|----------------|---------------------|
| name | onboarding_controller, sessions_controller (comentário explícito de ausência) | AUSENTE |
| role | client_users_controller | AUSENTE |
| permissions | client_users_controller | AUSENTE |
| workos_user_id | migration 20250715000027 | AUSENTE |
| avatar_url | client_users_controller | AUSENTE |
| activation_state | onboarding_controller + migration 20250716000010 | AUSENTE |
| invitation_token | migration 20250716000010 | AUSENTE |
| phone | migration 20250716000010 | AUSENTE |
| onboarding_lia_override | onboarding_controller | AUSENTE |
| first_login_at | user_onboarding_extension | AUSENTE |
| invited_by_user_id | onboarding_controller + migration | AUSENTE |
| fork_uuid | migration 20250715000027 | AUSENTE |

**Tabela `selective_processes`:**

| Campo | Status |
|-------|--------|
| account_id | AUSENTE (migration 20250714150818 adicionou, mas schema.rb versão para antes) |
| display_name, color, icon, stage_type, sla_hours, etc. | AUSENTE (migration 20250715000027) |

**Tabela `applies`:**

| Campo | Status |
|-------|--------|
| account_id | AUSENTE (migration 20250714150818) |
| source, status, lia_score, match_percentage, fork_uuid | AUSENTE (migration 20250715000027) |

---

## Seção 3: Tabelas Órfãs no Schema

Nenhuma tabela do schema.rb está sem model correspondente. Todas as 12 tabelas têm model. No entanto, o schema.rb está incompleto — o problema é o inverso: models sem tabela no schema.

---

## Seção 4: Migrations — Análise de Drift

### Resumo

| Métrica | Valor |
|---------|-------|
| Total de migrations | 85 |
| Versão atual do schema.rb | 2025_07_14_142059 |
| Última migration existente | 20250716000010 |
| Migrations aplicadas (estimado) | ~18 (primeiras 18 do arquivo, até a versão do schema) |
| Migrations NÃO aplicadas | ~67 |

### Análise de Drift

O `schema.rb` foi gerado em `20250714_142059`. As migrations seguintes foram criadas mas **nunca executadas** no banco de produção (ou foram executadas mas o `schema.rb` não foi regenerado via `rails db:schema:dump`).

**Bloco de migrations críticas não refletidas no schema.rb:**

| Versão | Migration | Impacto |
|--------|-----------|---------|
| 20250714150600 | create_applystatuses | Tabela apply_statuses ausente |
| 20250714150818 | add_account_in_others_models | account_id ausente em candidates/applies/selective_processes |
| 20250715000001 | create_client_accounts | Tabela inteira ausente |
| 20250715000002 a 000024 | 23 migrations de domínio | ~40 tabelas ausentes |
| 20250715000025 | expand_candidates_table | 30+ campos + 3 tabelas de candidato ausentes |
| 20250715000026 | expand_jobs_table | ~50 campos de jobs ausentes |
| 20250715000027 | expand_selective_processes_and_users | name, role, activation_state ausentes de users |
| 20250716000002 | create_talent_pools | talent_pools + talent_pool_candidates ausentes |
| 20250716000003 | create_recruitment_campaigns | recruitment_campaigns ausente |
| 20250716000010 | add_onboarding_to_users | phone, invitation_token, activation_state, onboarding_lia_override ausentes |

**Conclusão:** O `schema.rb` representa apenas o estado inicial do banco (~2 semanas de desenvolvimento). Todo o desenvolvimento subsequente — quase 90% do schema completo — existe apenas nas migrations. O banco de produção GCP pode ter as tabelas se as migrations foram rodadas diretamente, mas o `schema.rb` está desatualizado e é uma fonte perigosa de confusão.

**Ação imediata necessária:** `rails db:migrate && rails db:schema:dump` no ambiente de produção (GCP).

---

## Seção 5: Índices

### Índices presentes no schema.rb atual

| Tabela | Campo(s) | Índice | Tipo | Necessário? |
|--------|----------|--------|------|-------------|
| accounts | tenant | Sim | BTREE | Sim — lookup por tenant |
| accounts | staging_tenant | Sim | BTREE | Sim |
| applies | candidate_id | Sim | BTREE | Sim — FK |
| applies | job_id | Sim | BTREE | Sim — FK |
| applies | selective_process_id | Sim | BTREE | Sim — FK |
| candidates | email | Sim | BTREE | Sim — busca/login |
| candidates | linkedin | Sim | BTREE | Sim |
| candidates | uid | Sim | BTREE | Sim |
| jobs | account_id | Sim | BTREE | Sim — multi-tenant |
| jobs | provider + provider_job_id | Sim | UNIQUE | Sim |
| jobs | user_id | Sim | BTREE | Sim — FK |
| messages | account_id | Sim | BTREE | Sim |
| messages | parent_message_id | Sim | BTREE | Sim |
| messages | reference_type + reference_id | Sim | BTREE | Sim |
| permissions | name | Sim | UNIQUE | Sim |
| role_permissions | permission_id | Sim | BTREE | Sim |
| role_permissions | role_id + permission_id | Sim | UNIQUE | Sim |
| roles | name | Sim | UNIQUE | Sim |
| selective_processes | job_id | Sim | BTREE | Sim |
| selective_processes | uid | Sim | BTREE | Sim |
| user_permissions | permission_id | Sim | BTREE | Sim |
| user_permissions | user_id + permission_id | Sim | UNIQUE | Sim |
| user_roles | role_id | Sim | BTREE | Sim |
| user_roles | user_id + role_id | Sim | UNIQUE | Sim |
| users | account_id | Sim | BTREE | Sim |

### Índices AUSENTES (campos críticos sem índice)

| Tabela | Campo | Impacto | Severidade |
|--------|-------|---------|------------|
| users | email | Login sem índice = full table scan a cada autenticação | 🔴 CRITICO |
| candidates | account_id | Multi-tenant sem índice — queries lentas por tenant | 🔴 CRITICO |
| applies | account_id | Multi-tenant sem índice | 🔴 CRITICO |
| selective_processes | account_id | Multi-tenant sem índice | 🔴 CRITICO |
| messages | reference_id (isolado) | Buscas por referência parciais | 🟡 ALTO |

**Nota:** `account_id` foi adicionado a `candidates`, `applies` e `selective_processes` via migration `20250714150818` com `add_reference` (que cria índice automaticamente). Porém essa migration não está refletida no schema.rb — logo, em qualquer ambiente que usar `db:schema:load` em vez de `db:migrate`, o índice não existirá.

### Foreign Keys declaradas no schema.rb

| Tabela (origem) | Tabela (destino) | FK Constraint |
|----------------|-----------------|---------------|
| applies | candidates | Sim |
| applies | jobs | Sim |
| applies | selective_processes | Sim |
| messages | accounts | Sim |
| role_permissions | permissions | Sim |
| role_permissions | roles | Sim |
| selective_processes | jobs | Sim |
| user_permissions | permissions | Sim |
| user_permissions | users | Sim |
| user_roles | roles | Sim |
| user_roles | users | Sim |
| users | accounts | Sim |

**FK ausentes:** `jobs → users` (user_id definido como bigint mas sem `add_foreign_key`). `candidates → accounts` (account_id adicionado por migration posterior não refletida no schema).

---

## Seção 6: Integridade Referencial

### Relações mapeadas (schema.rb atual)

| Relação | FK Constraint no Schema | Cascade? | Risco de Órfão |
|---------|------------------------|----------|----------------|
| Apply → Candidate | Sim | Não (no schema) | Baixo — belongs_to hard |
| Apply → Job | Sim | Não | Baixo |
| Apply → SelectiveProcess | Sim | Não | Baixo |
| Message → Account | Sim (optional) | Não | Médio — belongs_to optional |
| SelectiveProcess → Job | Sim | Não | Baixo |
| User → Account | Sim | Não (destroy via model) | Baixo |
| Job → User | **NÃO** (bigint sem FK) | Não | **ALTO** — sem constraint |
| Candidate → Account | **NÃO** (migration não aplicada) | Não | **ALTO** |

### Soft delete

**Implementação parcial:**
- `client_accounts` e `client_users`: têm coluna `deleted_at` nas migrations e nos serializers. Porém as migrations não estão no `schema.rb`.
- `applies` e `apply_statuses`: usam `is_deleted boolean` (soft delete manual, sem paranoia gem).
- Não há gem `paranoia` ou `discard` instalada.
- Não há `deleted_at` nas tabelas principais do schema.rb atual.

### Riscos de integridade referencial

| Cenário | Risco |
|---------|-------|
| Deletar User com Jobs associados | Jobs ficam órfãos (sem FK cascade) |
| Deletar Candidate com Applies | OK — FK com restrict |
| Deletar Job com SelectiveProcesses | Propagado pelo model (dependent: :destroy) mas sem CASCADE no banco |
| Criar Apply com account_id nulo | Bloqueado pela migration 150818 (null: false) — mas migration não está no schema.rb |

---

## Seção 7: Schema Python (banco da IA)

### Tabelas declaradas via SQLAlchemy ORM

| Tabela | Arquivo | Descrição |
|--------|---------|-----------|
| users | app/auth/models.py | Usuários da plataforma — banco SEPARADO do Rails |
| workos_groups | app/auth/workos_models.py | Grupos WorkOS SSO |
| workos_group_memberships | app/auth/workos_models.py | Membros de grupos |
| workos_group_role_mappings | app/auth/workos_models.py | Mapeamento de roles WorkOS |
| sso_audit_logs | app/auth/workos_models.py | Logs de auditoria SSO |
| company_workos_config | app/auth/workos_models.py | Config WorkOS por empresa |
| personalized_feedback_records | domains/cv_screening/... | Feedback personalizado de CVs |
| pending_approvals | domains/communication/... | Aprovações pendentes |
| communication_logs | domains/communication/... | Logs de comunicação |
| candidate_opt_outs | domains/communication/... | Opt-outs de candidatos |
| candidate_quarantines | domains/communication/... | Quarentena de candidatos |
| recruiter_preferences | domains/pipeline/models/... | Preferências de recrutador |

### Tabelas criadas via raw SQL (database.py — fora do controle Alembic)

| Tabela | Propósito | Tem índice pgvector? |
|--------|-----------|---------------------|
| companies | Empresas/tenants | Não |
| audit_logs | Auditoria geral | Não |
| candidate_lists | Listas de candidatos | Não |
| candidate_list_members | Membros das listas | Não |
| lia_profile_analyses | Análises de perfil LIA | Não |
| workos_groups | Grupos (duplicado do ORM?) | Não |
| workos_group_memberships | (duplicado?) | Não |
| workos_group_role_mappings | (duplicado?) | Não |
| company_workos_config | (duplicado?) | Não |
| sso_audit_logs | (duplicado?) | Não |
| wizard_feedback | Feedback do wizard | Não |
| job_outcomes | Resultados de vagas | Não |
| interaction_feedback | Feedback de interações | Não |
| learning_patterns | Padrões de aprendizado | Não |
| **conversation_memories** | Memória de chat (RAG) | **Sim — IVFFLAT** |
| **knowledge_base** | Base de conhecimento (RAG) | **Sim — IVFFLAT** |
| background_jobs | Jobs em background | Não |
| proactive_actions | Ações proativas de LIA | Não |
| agent_long_term_memory | Memória de longo prazo | Não |
| company_hiring_policies | Políticas de contratação | Não |

### Alembic — Status das Migrations

| Métrica | Valor |
|---------|-------|
| Total de migrations Alembic | 76 (001→076) |
| Última migration | 076_consumption_observability_fields.py |
| Estado geral | Sequência contínua sem gaps visíveis |

**Problema crítico:** As tabelas criadas via raw SQL em `database.py` (setup_pgvector, setup_database functions) estão **FORA do controle do Alembic**. Isso significa que alterações nessas tabelas não são versionadas, não têm rollback, e qualquer ambiente novo precisa rodar o código Python (não as migrations) para criá-las.

---

## Seção 8: CANDIDATE_FORK_TO_RAILS — Análise de Mapeamento

### Mapeamento Campo a Campo

| Fork (Python) | Rails (schema.rb atual) | Existe no schema.rb? | Problema |
|---------------|------------------------|---------------------|----------|
| id | id | Sim | TIPO: UUID vs bigint — incompatível sem conversão |
| name | name | **NÃO** | Campo ausente no schema.rb (migration 000027) |
| email | email | Sim | OK |
| secondary_email | secondary_email | Sim | OK |
| phone | phone | **NÃO** | Campo ausente (migration 20250716000010) |
| mobile_phone | mobile_phone | Sim | OK |
| secondary_phone | secondary_phone | Sim | OK |
| linkedin_url | linkedin | Sim | Nome diferente — mapeado |
| github_url | github | Sim | Nome diferente — mapeado |
| portfolio_url | portfolio | Sim | Nome diferente — mapeado |
| avatar_url | avatar_url | Sim | OK |
| date_of_birth | date_birth | Sim | Nome diferente — mapeado |
| gender | gender | Sim | TIPO: Fork string, Rails integer enum |
| nationality | nationality | Sim | OK |
| marital_status | marital_status | Sim | TIPO: Fork string, Rails integer enum |
| cpf | cpf | Sim | Fork pode criptografar, Rails texto plano |
| current_title | role_name | Sim | Nome diferente — mapeado |
| current_company | current_company | Sim | OK |
| seniority_level | seniority_level | **NÃO** | Ausente no schema.rb (migration 000025) |
| self_introduction | self_introduction | Sim | OK |
| resume_text | curriculum_text | Sim | Nome diferente — mapeado |
| resume_url | curriculum_pdf_url | Sim | Nome diferente — mapeado |
| location_city | city | Sim | Nome diferente — mapeado |
| location_state | state | Sim | OK |
| location_country | country | Sim | OK |
| address_street | street | Sim | OK |
| address_number | number | Sim | TIPO: Fork String, Rails Integer |
| address_district | district | Sim | OK |
| address_zip | zip | Sim | OK |
| address_complement | complement | Sim | OK |
| current_salary | current_salary | Sim | OK |
| desired_salary_min | desired_salary | Sim | Nome diferente — mapeado |
| salary_expectation_clt | clt_expectation | Sim | Nome diferente — mapeado |
| salary_expectation_pj | pj_expectation | Sim | OK |
| salary_expectation_freelance | freelance_expectation | Sim | OK |
| salary_currency | currency | Sim | OK |
| is_remote | remote_work | Sim | Nome diferente — mapeado |
| willing_to_relocate | mobility | Sim | Nome diferente — mapeado |
| source | source | Sim | OK |
| technical_skills | technical_skills | **NÃO** | Ausente no schema.rb (migration 000025) |
| soft_skills | soft_skills | **NÃO** | Ausente no schema.rb |
| languages | languages | **NÃO** | Ausente no schema.rb |
| certifications | certifications | **NÃO** | Ausente no schema.rb |
| years_of_experience | years_of_experience | **NÃO** | Ausente no schema.rb |
| diversity_race_ethnicity | diversity_race_ethnicity | **NÃO** | Ausente (migration 000025) |
| diversity_disability | diversity_disability | **NÃO** | Ausente |
| diversity_disability_type | diversity_disability_type | **NÃO** | Ausente |
| diversity_lgbtqia | diversity_lgbtqia | **NÃO** | Ausente |
| diversity_refugee | diversity_refugee | **NÃO** | Ausente |
| diversity_age_50_plus | diversity_age_50_plus | **NÃO** | Ausente |
| diversity_indigenous | diversity_indigenous | **NÃO** | Ausente |
| diversity_documents | diversity_documents | **NÃO** | Ausente |
| diversity_self_declared_at | diversity_self_declared_at | **NÃO** | Ausente |
| diversity_document_deadline | diversity_document_deadline | **NÃO** | Ausente |

### Resumo de Problemas no Mapeamento

| Categoria | Contagem | Severidade |
|-----------|----------|------------|
| Campos mapeados ausentes no schema.rb Rails | 15 campos | 🔴 CRITICO |
| Tipo incompatível (UUID ↔ bigint) para ID | 1 | 🔴 CRITICO |
| Tipo incompatível (string ↔ integer enum) | 2 (gender, marital_status) | 🟡 ALTO |
| Tipo incompatível (string ↔ integer para address_number) | 1 | 🟡 ALTO |
| Nome diferente mas mapeado corretamente | 12 | 🟢 OK |
| Fork-only (sem equivalente Rails) | ~8 campos | INFO |
| Rails-only (sem equivalente Fork) | ~6 campos | INFO |

---

## Seção 9: Vector Store

### Tecnologia

**pgvector** (extensão PostgreSQL nativa) — banco Python/Replit.

Nenhum ChromaDB, Pinecone, Weaviate ou FAISS encontrado.

### Collections / Índices Configurados

| Tabela | Tipo de Índice | Dimensão | Uso |
|--------|---------------|----------|-----|
| conversation_memories | IVFFLAT (cosine) | Variável | Memória de conversas do chat LIA |
| knowledge_base | IVFFLAT (cosine) | Variável | Base de conhecimento RAG |

**Índices adicionais em conversation_memories:**
- `company_id` — isolamento por tenant
- `session_id` — sessões de chat
- `user_id` — por usuário
- `(company_id, session_id)` — composto
- `created_at` — temporal
- `embedding` — IVFFLAT vector similarity

**Índices adicionais em knowledge_base:**
- `company_id`
- `document_type`
- `parent_id`
- `(company_id, document_type)` — composto
- `created_at`
- `embedding` — IVFFLAT vector similarity

### Uso do pgvector no código

| Serviço | Uso |
|---------|-----|
| twin_inference_service.py | K-NN search em decisões do twin digital |
| twin_knowledge_indexer.py | Indexação de aprovações/rejeições com embeddings |
| vector_semantic_cache.py | Cache semântico de routing |
| rag_search.py | Busca híbrida pgvector + tsvector (BM25) |
| job_embeddings.py | Embeddings de vagas para matching |

### Sincronização com banco principal

As tabelas `conversation_memories` e `knowledge_base` são criadas via raw SQL na inicialização da aplicação Python (`setup_pgvector()`). **Não há sincronização com o banco Rails** — são tabelas exclusivas do banco Python. Isso é arquiteturalmente correto (IA ↔ Python, CRUD ↔ Rails).

---

## Seção 10: Tabela Consolidada de Findings

| ID | Severidade | Banco | Tabela/Model | Descrição | Impacto | Ação Recomendada |
|----|------------|-------|--------------|-----------|---------|------------------|
| F01 | 🔴 CRITICO | Rails | schema.rb | Drift de 67 migrations — schema.rb v20250714 vs migrations até 20250716 | Schema.rb inutilizável para db:schema:load; produção pode estar inconsistente | `rails db:migrate && rails db:schema:dump` imediato |
| F02 | 🔴 CRITICO | Rails | candidates | account_id ausente no schema.rb (migration 20250714150818 não refletida) | candidates sem FK para accounts no schema — multi-tenancy quebrada | Parte do F01 |
| F03 | 🔴 CRITICO | Rails | users | Colunas name, role, activation_state, phone, invitation_token, onboarding_lia_override ausentes do schema.rb | Login e onboarding quebrados em ambiente db:schema:load | Parte do F01 |
| F04 | 🔴 CRITICO | Rails | apply_statuses | Tabela inteira ausente do schema.rb; model ApplyStatus ativo no código | ApplyStatus.create! falha com "table not found" em novo ambiente | Parte do F01 |
| F05 | 🔴 CRITICO | Rails | ~70 models | Models para client_accounts, interviews, webhooks, lgpd, etc. sem tabela no schema.rb | Todo o domínio de negócio novo inacessível em ambiente reconstruído | Parte do F01 |
| F06 | 🔴 CRITICO | Ambos | id (candidates) | UUID (Python/Fork) mapeado diretamente para bigint (Rails) sem conversão | Dados corrompidos ou erros na sincronia Fork→Rails | Implementar conversão explícita no rails_adapter.py |
| F07 | 🔴 CRITICO | Rails | users | Email sem índice na tabela users | Full table scan a cada login — impacto grave em escala | `add_index :users, :email, unique: true` |
| F08 | 🔴 CRITICO | Rails | candidates | 15 campos do CANDIDATE_FORK_TO_RAILS ausentes do schema.rb | Sincronia Fork→Rails perde dados silenciosamente | Parte do F01 (migrations) |
| F09 | 🟡 ALTO | Rails | jobs | ~50 campos expandidos (status, seniority_level, salary_range, etc.) ausentes do schema.rb | Funcionalidades de vaga avançada indisponíveis em ambiente reconstruído | Parte do F01 |
| F10 | 🟡 ALTO | Rails | gender/marital_status | Fork usa string, Rails usa integer enum | Conversão incorreta corromperia o valor salvo | Validar conversão no rails_adapter.py |
| F11 | 🟡 ALTO | Rails | user.rb | Código de onboarding_lia_enabled?, activation_state, etc. em arquivo de comentários, nunca aplicado ao modelo real | Onboarding controller chama métodos inexistentes no User | Aplicar extensões do user_onboarding_extension.rb ao user.rb real |
| F12 | 🟡 ALTO | Python | database.py | ~20 tabelas criadas via raw SQL fora do controle do Alembic | Sem versionamento, rollback impossível, inconsistência entre ambientes | Migrar criação das tabelas para migrations Alembic |
| F13 | 🟡 ALTO | Rails | client_accounts | Coluna deleted_at nos serializers e migration mas sem gem paranoia/discard | Soft delete manual sem garantias; possível retorno de registros deletados | Implementar discard gem ou validar lógica manual |
| F14 | 🟡 ALTO | Rails | jobs | FK user_id definido como bigint mas sem add_foreign_key no schema | Jobs órfãos possíveis se user deletado sem cascade | Adicionar FK constraint |
| F15 | 🟢 INFO | Python | workos_models.py | Definições duplicadas — tabelas definidas tanto no ORM quanto via raw SQL em database.py | Possível conflito de schema em ambiente novo | Consolidar em Alembic |
| F16 | 🟢 INFO | Ambos | address_number | Fork: String, Rails: Integer | Endereços com letras ("12A") perdidos na conversão | Normalizar tipo ou tratar no adapter |
| F17 | 🟢 INFO | Rails | talent_pool.rb | Usa counter_cache, created_by_user, ideal_profile mas tabela não está no schema.rb | Dependências em cascata se migrations forem aplicadas parcialmente | Parte do F01 |

---

## Validação Final do Protocolo PX04

| Item | Status | Observação |
|------|--------|------------|
| 1. Todos os models Rails verificados contra schema.rb | COMPLETO | 90 models vs 12 tabelas no schema.rb |
| 2. Campos referenciados em controllers/workers ausentes no schema | COMPLETO | F03, F04, F08 identificados |
| 3. Migrations analisadas (total, versão, drift) | COMPLETO | 85 total, 67 não refletidas no schema.rb |
| 4. Índices mapeados (account_id, email, FKs) | COMPLETO | email ausente (F07), account_id ausente em candidates/applies |
| 5. Schema Python / Alembic verificado | COMPLETO | 76 migrations, 20 tabelas via raw SQL fora do controle |
| 6. CANDIDATE_FORK_TO_RAILS mapeamento analisado | COMPLETO | 15 campos ausentes no Rails, 3 incompatibilidades de tipo |
| 7. Vector store identificado | COMPLETO | pgvector, 2 collections indexadas |

---

## Recomendações Prioritárias

### Prioridade 1 — Imediato (esta semana)
1. **Executar `rails db:migrate && rails db:schema:dump`** no ambiente GCP para sincronizar schema.rb com o banco real.
2. **Adicionar índice em `users.email`** — crítico para autenticação.
3. **Aplicar extensões de `user_onboarding_extension.rb`** ao `user.rb` real — onboarding controller vai falhar.

### Prioridade 2 — Curto prazo (próximos 14 dias)
4. Implementar conversão UUID→bigint no `rails_adapter.py` para o campo `id`.
5. Validar/implementar conversão de tipo para `gender` e `marital_status` (string↔integer).
6. Adicionar FK constraint para `jobs.user_id`.
7. Migrar tabelas raw SQL do `database.py` para migrations Alembic.

### Prioridade 3 — Médio prazo
8. Implementar `discard` gem para soft delete consistente.
9. Adicionar `add_foreign_key :applies, :accounts` e `add_foreign_key :candidates, :accounts` quando schema.rb for sincronizado.
10. Consolidar tabelas WorkOS duplicadas (ORM vs raw SQL).
