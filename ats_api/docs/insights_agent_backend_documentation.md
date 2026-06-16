# Documentação Completa do Backend — Agente de Insights

> Documento de referência para construção do Agente de Insights (Python/LangGraph) que consome a API REST do ATS.

---

## Sumário

1. [Modelo de Dados — Entidades e Relacionamentos](#seção-1-modelo-de-dados--entidades-e-relacionamentos)
2. [API REST — Endpoints Disponíveis](#seção-2-api-rest--endpoints-disponíveis)
3. [Métricas e KPIs Calculáveis](#seção-3-métricas-e-kpis-calculáveis)
4. [Alertas e Triggers para Proatividade](#seção-4-alertas-e-triggers-para-proatividade)
5. [Briefing Matinal — Estrutura Completa](#seção-5-briefing-matinal--estrutura-completa)
6. [Report sob Demanda — Templates](#seção-6-report-sob-demanda--templates)
7. [Fluxo de Dados para o Agente Insights](#seção-7-fluxo-de-dados-para-o-agente-insights)
8. [Considerações Técnicas](#seção-8-considerações-técnicas)

---

## Seção 1: Modelo de Dados — Entidades e Relacionamentos

### 1.1 Domínio: Vagas (Jobs)

#### `jobs`
**Propósito:** Vaga de emprego publicada pela empresa. Entidade central do sistema.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Título da vaga |
| `description` | text | Descrição completa da vaga |
| `is_active` | boolean | Vaga ativa ou pausada |
| `is_archived` | boolean | Vaga arquivada |
| `is_deleted` | boolean | Soft-delete |
| `is_urgent` | boolean | Flag de urgência |
| `seniority` | integer | Nível (0=Estagiário..7=C-Level) |
| `employment_type` | integer | CLT, PJ, Freelance, etc. |
| `workplace_type` | string | Presencial, Remoto, Híbrido |
| `priority` | integer | Prioridade (0=Baixa..3=Crítica) |
| `urgency_level` | integer | Urgência (0..5) |
| `published_date` | datetime | Data de publicação |
| `application_deadline` | datetime | Prazo para candidaturas |
| `screening_deadline` | date | Prazo para triagem |
| `shortlist_deadline` | date | Prazo para shortlist |
| `closing_deadline` | date | Prazo para fechamento |
| `city/state/country` | strings | Localização |
| `is_screening_active` | boolean | Triagem automática ativa |
| `has_automatic_interview` | boolean | Entrevista AI automática |
| `minimum_screening_score` | float | Score mínimo para triagem |
| `interview_minimum_score` | float | Score mínimo para entrevista |
| `reason_for_pause` | string | Motivo da pausa |
| `auto_source_metadata` | jsonb | Config do sourcing automático |

**Relacionamentos:**
- `belongs_to :user` (recrutador responsável)
- `belongs_to :account`
- `belongs_to :company` (empresa cliente, quando B2B)
- `belongs_to :job_status` (status customizado)
- `belongs_to :department`
- `belongs_to :team`
- `belongs_to :hiring_manager` (gestor da vaga)
- `belongs_to :workflow_template` (template de pipeline)
- `has_many :selective_processes` (etapas do pipeline)
- `has_many :applies` (candidaturas)
- `has_many :evaluations` (testes/avaliações)
- `has_many :interview_sessions` (entrevistas AI)
- `has_many :skill_relationships → skills`
- `has_many :benefit_relationships → benefits`
- `has_many :remuneration_relationships → remunerations`
- `has_many :language_relationships → languages`
- `has_one :analytics_snapshot` (cache de métricas)

**Constantes importantes:**
```
SENIORITY: [Intern, Junior, Mid-Level, Senior, Specialist, Lead, Manager, C-Level]
EMPLOYMENT_TYPES: [CLT, PJ, Freelance, Temporary, Internship, Apprentice]
WORKPLACE_TYPES: [on_site, remote, hybrid]
PRIORITY: [low, medium, high, critical]
URGENCY_LEVEL: [0..5]
```

**Campos derivados úteis para métricas:**
- `closing_deadline - published_date` = Janela planejada da vaga
- `created_at` vs `closing_deadline` = Aderência ao prazo
- `applies.count` = Volume de atração

---

#### `selective_processes`
**Propósito:** Etapas do pipeline de seleção (Kanban). Cada vaga tem várias etapas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome da etapa (ex: "Triagem", "Entrevista Técnica") |
| `position` | integer | Ordem no pipeline |
| `status` | enum | Tipo da etapa |
| `sub_status` | jsonb | Sub-statuses configuráveis |
| `color` | string | Cor visual |
| `duration` | integer | Duração estimada (dias) |
| `approved_process_id` | integer | Próxima etapa (aprovação) |
| `rejected_process_id` | integer | Etapa de rejeição |

**Enum `status`:**
| Valor | Significado |
|-------|-------------|
| `0` - web_submission | Inscrição recebida |
| `1` - screening | Triagem |
| `2` - interview | Entrevista |
| `3` - rejected | Rejeitado |
| `4` - hired | Contratado |

**Sub-statuses de Interview:** `invite_sent`, `accepted`, `confirmed`, `in_progress`, `completed`
**Sub-statuses de Rejected:** `overqualified`, `underqualified`, `salary_mismatch`, `location_mismatch`, `no_show`, `withdrew`, `other`, etc. (20 opções)

**Relacionamentos:**
- `belongs_to :job`
- `has_many :applies`

---

#### `job_statuses`
**Propósito:** Status customizáveis das vagas (diferente do status do processo seletivo).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome do status |
| `color` | string | Cor hex |
| `is_main` | boolean | Status padrão do sistema |

**Status padrão:** Em Aberto, Em Andamento, Concluída, Cancelada, Pausada, Em Aprovação, Rascunho, Urgente, Reaberta, Expirada, Congelada, Pipeline Review.

---

#### `job_analytics_snapshots`
**Propósito:** Cache de métricas pré-calculadas por vaga.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `snapshot_data` | jsonb | JSON com métricas completas (funil, velocidade, qualidade, etc.) |
| `computed_at` | datetime | Quando foi calculado |
| `version` | integer | Versão do schema |

---

### 1.2 Domínio: Candidatos e Candidaturas

#### `candidates`
**Propósito:** Perfil do candidato no ATS.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `uid` | string | ID público único |
| `name` | string | Nome completo |
| `email` | string | E-mail principal |
| `mobile_phone` | string | Celular |
| `linkedin` | string | URL do LinkedIn |
| `current_company` | string | Empresa atual |
| `role_name` | string | Cargo atual |
| `position_level` | string | Nível |
| `curriculum_text` | text | Texto do currículo (parseado) |
| `source` | string | Origem (linkedin, website, referral, etc.) |
| `clt_expectation` | float | Pretensão CLT |
| `pj_expectation` | float | Pretensão PJ |
| `current_salary` | float | Salário atual |
| `remote_work` | boolean | Aceita remoto |
| `city/state/country` | strings | Localização |
| `gender` | integer | Gênero (0=Não informado..6) |
| `favorite_user_ids` | array[int] | IDs dos recrutadores que favoritaram |

**Relacionamentos:**
- `belongs_to :account`
- `has_many :applies`
- `has_many :jobs, through: :applies`
- `has_many :evaluation_candidates`
- `has_many :educations`
- `has_many :experiences`
- `has_many :skill_relationships → skills`
- `has_many :interview_sessions`

---

#### `applies`
**Propósito:** Candidatura — a junção entre candidato e vaga numa etapa do pipeline.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `candidate_id` | FK | Candidato |
| `job_id` | FK | Vaga |
| `selective_process_id` | FK | Etapa atual do pipeline |
| `evaluation_candidate_status` | enum | Status da avaliação |
| `selective_process_status` | string | Alias do status da etapa |
| `cv_match` | float | Score de match com a vaga (0-100) |
| `total_score` | float | Score total combinado |
| `sub_status` | string | Sub-status (ex: no_show, withdrew) |
| `reason_for_reject` | text | Motivo da rejeição |
| `reason_code` | string | Código do motivo |
| `reason_category` | string | Categoria do motivo |
| `alerts` | jsonb | Alertas ativos |
| `is_deleted` | boolean | Soft-delete |
| `pin_user_ids` | array[int] | Recrutadores que fixaram |

**Enum `evaluation_candidate_status`:**
| Valor | Significado |
|-------|-------------|
| `0` - pending | Avaliação não enviada |
| `1` - sent | Avaliação enviada ao candidato |
| `2` - answered | Candidato respondeu a avaliação |

**Relacionamentos:**
- `belongs_to :candidate`
- `belongs_to :job`
- `belongs_to :selective_process`
- `has_many :meeting_relationships`
- `has_many :candidate_feedbacks`

**Campos derivados:**
- `created_at` = Data da candidatura
- `selective_process.status` = Em qual fase está
- Mudança de `selective_process_id` = Movimentação no pipeline (registrada em `apply_statuses`)

---

#### `apply_statuses`
**Propósito:** Histórico de movimentações do candidato no pipeline. Cada mudança de etapa gera um registro.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `apply_id` | FK | Candidatura |
| `selective_process_id` | FK | Etapa para onde moveu |
| `status_id` | integer | ID do status |
| `status_name` | string | Nome do status |
| `comment` | text | Comentário do recrutador |
| `user_id` | FK | Quem moveu |
| `created_at` | datetime | Quando moveu |

**Crucial para métricas de tempo:** Distância entre `apply_statuses.created_at` consecutivos = tempo em cada etapa.

---

### 1.3 Domínio: Entrevistas e Agendamento

#### `meetings`
**Propósito:** Reunião/entrevista agendada (Teams, Meet, Zoom, presencial).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `subject` | string | Assunto |
| `provider` | string | Plataforma (microsoft_teams, google_meet, zoom, presential) |
| `start_time` | datetime | Início |
| `end_time` | datetime | Fim |
| `join_url` | text | Link da reunião online |
| `sub_status` | string | Status da reunião |
| `location` | string | Local (presencial) |
| `job_id` | FK | Vaga relacionada |
| `apply_id` | FK | Candidatura relacionada |

**Sub-statuses:** `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show`

**Relacionamentos:**
- `belongs_to :organizer` (User)
- `belongs_to :job` (opcional)
- `belongs_to :apply` (opcional)
- `has_many :meeting_relationships`

---

#### `calendar_events`
**Propósito:** Evento de calendário sincronizado com Microsoft/Google Calendar.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `provider` | string | microsoft, google |
| `external_id` | string | ID no provider externo |
| `title` | string | Título |
| `event_type` | string | Tipo do evento |
| `start_time/end_time` | datetime | Horários |
| `is_all_day` | boolean | Dia inteiro |
| `is_cancelled` | boolean | Cancelado |
| `sub_status` | string | Status do evento |
| `job_id/apply_id` | FK | Contexto de recrutamento |

**Event types:** `generic`, `interview`, `document_delivery`, `feedback`, `onboarding`
**Sub-statuses:** `invite_sent`, `scheduled`, `confirmed`, `completed`, `no_show`, `rescheduled`, `cancelled`

**Relacionamentos:**
- `belongs_to :organizer` (User)
- `belongs_to :meeting` (opcional)
- `has_many :attendees` (CalendarEventAttendee)

---

#### `scheduling_links`
**Propósito:** Link de agendamento enviado ao candidato (self-scheduling).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `token` | string | Token único do link |
| `status` | string | active, booked, expired, cancelled |
| `interview_type` | string | technical, behavioral, cultural_fit, etc. |
| `platform` | string | teams, google_meet, zoom |
| `duration_minutes` | integer | Duração |
| `booked_at` | datetime | Quando candidato agendou |
| `expires_at` | datetime | Expiração do link |

**Relacionamentos:**
- `belongs_to :created_by` (User)
- `belongs_to :apply`, `:candidate`, `:job` (opcional)
- `has_many :scheduling_slots`

---

#### `scheduling_settings`
**Propósito:** Configurações de disponibilidade do recrutador.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timezone` | string | Fuso (padrão: America/Sao_Paulo) |
| `work_hours_start/end` | time | Horário de trabalho |
| `default_duration_minutes` | integer | Duração padrão (60 min) |
| `buffer_minutes` | integer | Buffer entre reuniões (15 min) |
| `lookahead_days` | integer | Dias à frente para disponibilidade (14) |

---

#### `interview_sessions`
**Propósito:** Sessão de entrevista conduzida por IA (chatbot/voz).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `token` | string | Token único de acesso |
| `status` | string | pending, active, completed, scored, expired, cancelled |
| `interview_type` | string | voice, video |
| `duration_minutes` | integer | Duração planejada |
| `questions_snapshot` | jsonb | Perguntas congeladas |
| `transcript` | jsonb | Transcrição completa |
| `report` | jsonb | Relatório de avaliação |
| `score` | float | Score final |
| `recommendation` | string | Recomendação |
| `started_at/completed_at` | datetime | Timestamps |

**Status flow:** `pending → active → completed → scored`

**Relacionamentos:**
- `belongs_to :evaluation`
- `belongs_to :evaluation_candidate`
- `belongs_to :candidate`
- `belongs_to :job`
- `belongs_to :apply`

---

### 1.4 Domínio: Avaliações

#### `evaluations`
**Propósito:** Teste/avaliação configurada para uma vaga.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome da avaliação |
| `is_chatbot` | boolean | Avaliação via chatbot |
| `ai_enabled` | boolean | IA para correção |
| `time` | integer | Tempo em minutos (padrão: 90) |
| `is_screening` | boolean | É triagem automática |
| `is_trigger` | boolean | Dispara automaticamente |
| `chatbot_channel` | enum | 0=internal, 1=whatsapp |
| `notification_type` | enum | 0=per_candidate, 1=daily, 2=weekly |
| `approved_selective_process_id` | FK | Etapa para onde aprovados vão |
| `rejected_selective_process_id` | FK | Etapa para onde reprovados vão |

**Relacionamentos:**
- `belongs_to :job`
- `belongs_to :selective_process` (em qual etapa do pipeline está configurada)
- `has_many :evaluation_candidates`
- `has_many :questions`
- `has_many :interview_sessions`

---

#### `evaluation_candidates`
**Propósito:** Envio de uma avaliação para um candidato específico.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `uid` | string | Token público |
| `completed` | boolean | Candidato finalizou |
| `score` | float | Score WSI calculado |
| `ai_feedback` | jsonb | Feedback da IA |
| `evaluation_summary` | text | Resumo da avaliação |
| `wsi_classification` | string | Classificação WSI |
| `wsi_level` | string | Nível WSI |
| `wsi_summary` | text | Resumo WSI |
| `is_screening` | boolean | É triagem |
| `session_status` | string | active, timeout, closed |
| `timeout_count` | integer | Quantas vezes deu timeout |

**Ciclo de vida:** Criado → Enviado ao candidato → Candidato responde → `completed = true` → AI Feedback calculado → Score WSI gerado

**Relacionamentos:**
- `belongs_to :evaluation`
- `belongs_to :candidate`
- `belongs_to :apply` (opcional)
- `belongs_to :job` (opcional)
- `has_many :answers`

---

#### `questions`
**Propósito:** Pergunta de uma avaliação.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Texto da pergunta |
| `response_type` | integer | Tipo (texto, múltipla escolha, etc.) |
| `position` | integer | Ordem |
| `choices` | json | Opções (para múltipla escolha) |
| `expected_response` | text | Resposta esperada |
| `competence_type` | string | Competência avaliada |
| `bloom_level` | string | Nível Bloom |
| `dreyfus_target` | integer | Nível Dreyfus alvo |
| `ocean_trait` | string | Traço Big Five |
| `framework_weights` | jsonb | Pesos dos frameworks |

---

#### `answers`
**Propósito:** Resposta de um candidato a uma pergunta.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Texto da resposta |
| `description` | text | Descrição detalhada |
| `time_taken` | integer | Tempo gasto (segundos) |
| `final_skill_score` | decimal(4,2) | Score (0.00–5.00) |
| `analysis_data` | jsonb | Análise detalhada (Bloom, Dreyfus, BigFive, CBI) |
| `comments_response` | text | Feedback da IA |

**Relacionamentos:**
- `belongs_to :question`
- `belongs_to :evaluation`
- `belongs_to :candidate`
- `belongs_to :job`
- `belongs_to :apply`
- `has_one_attached :audio_file`

---

#### `issues`
**Propósito:** Problemas/ocorrências durante avaliações.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | text | Descrição do problema |
| `type` | enum | 0=nao_informado, 1=screening |
| `status` | enum | 0=pending, 1=received, 2=answered |

---

### 1.5 Domínio: Sourcing

#### `sourcings`
**Propósito:** Busca de candidatos (local, global, LinkedIn, híbrido).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `uid` | string | ID único |
| `provider` | string | pearch, linkedin, local, global, hybrid |
| `query` | string | Texto da busca |
| `parameters` | jsonb | Parâmetros do filtro |
| `status` | string | done, processing, failed |
| `results_count` | integer | Total de resultados |
| `credits_used` | integer | Créditos gastos |
| `credits_remaining` | integer | Créditos restantes |
| `local_results_count` | integer | Resultados do banco local |
| `global_results_count` | integer | Resultados do Pearch |
| `aggregated_stats` | jsonb | Estatísticas agregadas |

**Relacionamentos:**
- `belongs_to :user`
- `belongs_to :account`
- `has_many :sourced_profile_sourcings`
- `has_many :sourced_profiles`

---

#### `sourced_profiles`
**Propósito:** Perfil encontrado via sourcing (antes de virar candidato).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome |
| `email/phone` | string | Contato |
| `title` | string | Título profissional |
| `current_company` | string | Empresa atual |
| `total_experience_years` | integer | Anos de experiência |
| `status` | string | new, viewed, interested, contacted, rejected, hired |
| `rating` | integer | Avaliação (1-5) |
| `candidate_id` | FK | Candidato (após importação) |
| `skills_data` | jsonb | Skills |
| `experiences_data` | jsonb | Experiências |
| `educations_data` | jsonb | Formação |

**Status flow:** `new → viewed → interested → contacted → (hired | rejected)`

**Relacionamentos:**
- `belongs_to :account`
- `belongs_to :candidate` (quando importado)
- `has_many :sourced_profile_sourcings`
- `has_many :sourcings, through: :sourced_profile_sourcings`

---

#### `sourced_profile_sourcings`
**Propósito:** Junção entre perfil e busca, com score e análise.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `score` | float | Score de aderência |
| `analysis` | jsonb | Análise da IA |
| `ai_metadata` | jsonb | Metadados da análise |
| `search_source` | string | Fonte (local/global) |
| `similarity_score` | float | Score de similaridade |

---

#### `candidate_feedbacks`
**Propósito:** Like/dislike de recrutador em perfis (para refinamento de busca).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `feedback_type` | string | "like" ou "dislike" |
| `reason` | text | Motivo |
| `search_query_snapshot` | jsonb | Query no momento do feedback |
| `candidate_score_snapshot` | jsonb | Score no momento |

---

### 1.6 Domínio: Empresa e Configuração

#### `accounts`
**Propósito:** Tenant (empresa cliente). Cada account é um schema isolado no PostgreSQL.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome da empresa |
| `tenant` | string | Nome do schema PostgreSQL |
| `uid` | string | ID público (usado em URLs de API pública) |
| `pearch_credits` | integer | Créditos de sourcing disponíveis |
| `pearch_total_consumed` | integer | Total de créditos consumidos |
| `sourcing_config` | jsonb | Configurações de sourcing |

---

#### `users`
**Propósito:** Recrutador/usuário da plataforma.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome |
| `email` | string | E-mail |
| `is_admin` | boolean | Administrador |
| `is_manager` | boolean | Gestor |
| `role_name` | string | Cargo |
| `status` | integer | 0=Inativo, 1=Ativo, 2=Pendente |
| `lia_user` | boolean | Usuário bot (Lia) |
| `ms_access_token` | text | Token Microsoft (calendário) |

**Relacionamentos:**
- `belongs_to :account`
- `belongs_to :department`
- `has_many :jobs`
- `has_many :roles, through: :user_roles`
- `has_one :scheduling_setting`
- `has_many :scheduling_links`
- `has_many :workspaces`

---

#### `departments`
**Propósito:** Departamento (hierárquico — árvore).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome |
| `level` | integer | Nível na hierarquia |
| `parent_department_id` | FK | Departamento pai |
| `manager_id` | FK | Gestor |
| `headcount` | integer | Headcount planejado |
| `cost_center` | string | Centro de custo |

---

#### `teams`
**Propósito:** Time dentro de um departamento.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome |
| `department_id` | FK | Departamento |
| `team_lead_id` | FK | Líder |
| `member_count` | integer | Número de membros |

---

#### `businesses`
**Propósito:** Dados da empresa (perfil institucional).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome fantasia |
| `corporate_name` | string | Razão social |
| `cnpj` | string | CNPJ |
| `industry` | string | Setor |
| `size` | string | Porte |
| `work_model` | string | Modelo de trabalho |
| `culture_values/soft_skills` | jsonb | Cultura e valores |
| `openness..stability` | integers | Big Five organizacional |

---

### 1.7 Domínio: Comunicação

#### `messages`
**Propósito:** Mensagens do chat AI (workspace/conversação).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `content` | text | Conteúdo |
| `entity` | integer | 0=system, 1=user, 2=candidate |
| `status` | integer | 0=not_answered, 1=answered |
| `content_format` | string | plain_text, conversation, thoughts, audio |
| `reference_type/id` | polymorphic | Contexto (User, Candidate, etc.) |
| `workspace_id` | FK | Workspace |
| `domain` | string | Domínio do workspace |

---

#### `dispatches` / `dispatch_messages`
**Propósito:** Envio de e-mails/mensagens em massa.

| Campo (dispatch) | Tipo | Descrição |
|-------|------|-----------|
| `channel_type` | string | email, whatsapp |
| `status` | enum | 0=pending..3=failed |
| `subject/body` | string/text | Conteúdo |
| `target_type` | string | ids, all, filter |

| Campo (dispatch_message) | Tipo | Descrição |
|-------|------|-----------|
| `status` | enum | 0=pending..5=opened |
| `sent_at` | datetime | Quando enviou |

---

#### `workspaces`
**Propósito:** Espaço de conversa AI por contexto (vaga, candidato, etc.).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `domain` | string | Contexto (jobs, candidates, general) |
| `domain_reference_id` | integer | ID do recurso |
| `last_message_date` | datetime | Última mensagem |

---

### 1.8 Domínio: Analytics e Custos

#### `llm_usages`
**Propósito:** Tracking de uso de LLMs (Gemini, etc.).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `model` | string | Modelo usado |
| `operation` | string | Operação (search, evaluation, chat, etc.) |
| `input_tokens/output_tokens/total_tokens` | integer | Tokens consumidos |
| `cost_usd` | decimal | Custo em USD |
| `latency_ms` | decimal | Latência |
| `success` | boolean | Sucesso |
| `context` | jsonb | Contexto (service name, etc.) |

---

#### `llm_quotas` / `llm_quota_usages`
**Propósito:** Limites e consumo mensal de LLM por conta.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `plan` | string | Plano |
| `monthly_cost_limit_usd` | decimal | Limite mensal |
| `monthly_request_limit` | integer | Limite de requests |
| `enabled` | boolean | Quota ativa |
| `hard_limit` | boolean | Bloqueia ao atingir |

---

#### `activity_logs`
**Propósito:** Log de ações dos usuários (auditoria e timeline).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `action` | string | Ação executada |
| `reference_type/id` | polymorphic | Recurso afetado |
| `changeset` | jsonb | O que mudou (before/after) |
| `user_id` | FK | Quem fez |
| `category` | string | Categoria |

---

#### `pearch_credit_transactions`
**Propósito:** Histórico de uso de créditos de sourcing.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `transaction_type` | string | Tipo |
| `amount` | integer | Quantidade |
| `balance_before/after` | integer | Saldo |
| `reason` | text | Motivo |

---

### 1.9 Fluxo de Dados Principal

```
Recrutador abre VAGA (Job)
    │
    ├── Configura PIPELINE (SelectiveProcesses: Triagem → Entrevista → Oferta → Contratado)
    ├── Configura AVALIAÇÃO (Evaluation + Questions)
    ├── Faz SOURCING (Sourcing → SourcedProfiles → importa como Candidate)
    │
    ▼
CANDIDATO se inscreve ou é importado
    │
    ▼
APPLY criado (status: web_submission)
    │
    ├── Recrutador tria → move para "Screening"
    │   └── Se is_screening_active → EvaluationCandidate criado automaticamente
    │       └── Candidato responde (Answers) → Score calculado → AI Feedback
    │
    ├── Aprovado na triagem → move para "Interview"
    │   └── Meeting/CalendarEvent criado (entrevista agendada)
    │   └── Ou InterviewSession criado (entrevista AI)
    │
    ├── Entrevista concluída → move para etapa seguinte
    │   └── Cada movimentação gera ApplyStatus (histórico)
    │
    ├── Oferta aceita → move para "Hired"
    │   └── Vaga pode ser fechada
    │
    └── Rejeitado em qualquer etapa → move para "Rejected"
        └── reason_code + reason_category registrados
```

---

## Seção 2: API REST — Endpoints Disponíveis

### 2.0 Informações Gerais

**Base URL:** `https://{host}/v1/users/` (endpoints autenticados)

**Autenticação:**
```
Authorization: Bearer {jwt_token}
```

**Multi-tenancy:** O tenant é determinado automaticamente pelo JWT token. O token contém `user_id` ou `account_id`, e o backend faz `Apartment::Tenant.switch!` para o schema correto.

**Formato de resposta padrão (JSON:API):**
```json
{
  "data": [
    {
      "id": "123",
      "type": "apply",
      "attributes": { ... }
    }
  ],
  "meta": {
    "total": 250,
    "where": { "is_deleted": false },
    "search": "*"
  }
}
```

**Paginação (padrão para todos os endpoints de listagem):**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `page` | int | 1 | Número da página |
| `per_page` | int | 30 | Itens por página (max 30) |

**Filtros (shared via Elasticsearch):**

| Param | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `search` | string | Busca full-text | `"desenvolvedor ruby"` |
| `where` | JSON | Filtros estruturados | `{"job_id": 5, "is_deleted": false}` |
| `filter` | JSON | Filtros adicionais (merge com where) | `{"status": "active"}` |
| `order` | JSON | Ordenação | `{"created_at": "desc"}` |
| `compact` | string | Campos específicos (CSV) | `"id,name,email"` |
| `includes` | string | Associações para incluir (CSV) | `"skills,languages"` |

**Operadores de filtro (dentro de `where`):**
```json
{
  "field_name": "exact_value",
  "field_name": { "like": "%partial%" },
  "field_name": { "gte": "2026-01-01", "lte": "2026-03-01" },
  "field_name": { "in": ["value1", "value2"] },
  "_or": [{ "field1": "a" }, { "field2": "b" }]
}
```

---

### 2.1 Vagas (Jobs)

#### GET /v1/users/jobs

**Propósito:** Listar vagas com filtros. Endpoint mais importante para overview.

**Filtros úteis para Insights:**
```json
{
  "where": {
    "is_active": true,
    "is_archived": false,
    "is_deleted": false,
    "job_status_id": 1,
    "department_id": 5,
    "user_id": 10,
    "created_at": { "gte": "2026-03-01" }
  }
}
```

**Response (campos principais do serializer):**
```json
{
  "id": "123",
  "type": "job",
  "attributes": {
    "title": "Desenvolvedor Full Stack",
    "description": "...",
    "is_active": true,
    "is_archived": false,
    "is_urgent": true,
    "seniority": 3,
    "seniority_text": "Senior",
    "employment_type": 0,
    "employment_type_text": "CLT",
    "workplace_type": "remote",
    "workplace_type_text": "Remoto",
    "priority": 2,
    "priority_text": "Alta",
    "urgency_level": 4,
    "urgency_level_text": "Muito Urgente",
    "city": "São Paulo",
    "state": "SP",
    "published_date": "2026-02-15T00:00:00Z",
    "application_deadline": "2026-04-01T00:00:00Z",
    "closing_deadline": "2026-04-15",
    "applies_count": 45,
    "applies_by_status_count": {
      "web_submission": 20,
      "screening": 10,
      "interview": 8,
      "rejected": 5,
      "hired": 2
    },
    "in_process": 38,
    "job_status": "Em Andamento",
    "job_status_color": "#4CAF50",
    "department_name": "Engenharia",
    "hiring_manager_name": "João Silva",
    "user_name": "Maria Recruiter",
    "salary_from": 8000,
    "salary_to": 15000,
    "salary_currency": "BRL",
    "completeness_percentage": 85,
    "is_ready_for_publication": true,
    "created_at": "2026-02-10T10:00:00Z"
  }
}
```

---

#### GET /v1/users/jobs/:id

**Propósito:** Detalhes completos de uma vaga específica.

**Response:** Mesmo formato, mas com associações incluídas: `selective_processes`, `skills`, `languages`, `benefits`, `remunerations`, `behavioral_skills`.

---

#### GET /v1/users/jobs/:id/analytics

**Propósito:** Analytics completas de uma vaga. **Endpoint mais rico para insights per-job.**

**Query params:**
| Param | Tipo | Descrição |
|-------|------|-----------|
| `force_refresh` | boolean | Forçar recálculo (ignora cache de 10min) |

**Response:**
```json
{
  "overview": {
    "total_applies": 45,
    "active_applies": 38,
    "days_since_published": 20,
    "days_since_created": 25,
    "days_until_deadline": 25,
    "is_deadline_expired": false,
    "is_active": true,
    "is_archived": false
  },
  "funnel": {
    "stages": [
      {
        "name": "Inscrição",
        "position": 0,
        "status": 0,
        "color": "#2196F3",
        "current_count": 20,
        "total_entered": 45,
        "total_exited": 25,
        "conversion_rate": 0.556,
        "avg_time_in_stage_hours": 48.5,
        "median_time_in_stage_hours": 36.0,
        "min_time_in_stage_hours": 2.0,
        "max_time_in_stage_hours": 168.0
      }
    ],
    "overall_conversion_rate": 0.044,
    "bottleneck_stage": "Entrevista Técnica",
    "avg_total_pipeline_days": 15.3
  },
  "velocity": {
    "avg_time_to_first_action_hours": 12.5,
    "avg_time_to_screening_hours": 24.0,
    "avg_time_to_interview_hours": 72.0,
    "applies_per_day": 2.25,
    "applies_trend": [
      { "week": "2026-02-10", "count": 15 },
      { "week": "2026-02-17", "count": 12 }
    ]
  },
  "quality": {
    "avg_cv_match": 72.5,
    "avg_total_score": 65.0,
    "score_distribution": {
      "0-20": 5, "21-40": 8, "41-60": 12, "61-80": 15, "81-100": 5
    },
    "evaluation_stats": {
      "total": 30,
      "avg_score": 3.2,
      "completed": 25,
      "pending": 5,
      "screening_stats": { "pass_rate": 0.7 }
    },
    "status_breakdown": {
      "web_submission": 20,
      "screening": 10,
      "interview": 8,
      "rejected": 5,
      "hired": 2
    }
  },
  "sources": {
    "by_source": [
      { "source": "linkedin", "count": 20, "percentage": 44.4 },
      { "source": "website", "count": 15, "percentage": 33.3 },
      { "source": "referral", "count": 10, "percentage": 22.2 }
    ]
  },
  "engagement": {
    "total_dispatches": 35,
    "total_messages": 120,
    "avg_messages_per_candidate": 2.7,
    "candidates_with_feedback": 15,
    "feedback_breakdown": { "like": 12, "dislike": 3 }
  },
  "scheduling": {
    "total_interviews_scheduled": 12,
    "interviews_completed": 8,
    "interviews_cancelled": 1,
    "interviews_pending": 3,
    "no_show_count": 1,
    "sub_status_breakdown": {
      "invite_sent": 1,
      "confirmed": 2,
      "completed": 8,
      "no_show": 1
    }
  },
  "team_activity": {
    "actions_by_user": [
      {
        "user_id": 10,
        "user_name": "Maria",
        "applies_moved": 25,
        "evaluations_done": 15,
        "last_action_at": "2026-03-06T14:30:00Z"
      }
    ]
  },
  "computed_at": "2026-03-07T10:00:00Z"
}
```

---

#### GET /v1/users/jobs/stats

**Propósito:** Métricas gerais de vagas da conta (dashboard).

**Query params:**
| Param | Tipo | Descrição |
|-------|------|-----------|
| `start_date` | date | Início do período |
| `end_date` | date | Fim do período |

**Response:**
```json
{
  "by_status": [{ "status": "Em Andamento", "color": "#4CAF50", "count": 15 }],
  "open_vs_closed": { "open": 20, "closed": 8, "total": 28 },
  "avg_days_to_close": 32.5,
  "created_per_week": [{ "week": "2026-02-24", "count": 3 }],
  "by_department": [{ "department": "Engenharia", "count": 8 }],
  "by_priority": [{ "priority": "high", "count": 5 }],
  "by_urgency": [{ "urgency": "4", "count": 3 }],
  "top_hiring_managers": [{ "user_id": 10, "name": "João", "count": 5 }],
  "top_recruiters_by_speed": [{ "user_id": 5, "name": "Maria", "jobs_closed": 3, "avg_days_to_close": 25 }],
  "totals": { "total": 50, "active": 20, "archived": 22, "created_in_period": 8 },
  "stale_jobs": [{ "job_id": 15, "title": "Dev Backend", "last_activity_at": "2026-01-15", "days_inactive": 51 }],
  "jobs_ranking": {
    "most_applies": [{ "job_id": 10, "title": "...", "count": 120 }],
    "longest_open": [{ "job_id": 8, "title": "...", "days": 90 }],
    "fastest_closed": [{ "job_id": 20, "title": "...", "days": 12 }]
  },
  "period": { "start_date": "2026-02-05", "end_date": "2026-03-07" }
}
```

---

#### GET /v1/users/jobs/alerts

**Propósito:** Alertas ativos sobre vagas.

**Response:**
```json
{
  "deadline_expired": [{ "job_id": 5, "title": "...", "closing_deadline": "2026-02-28", "urgency_level": 3 }],
  "deadline_soon": [{ "job_id": 12, "title": "...", "closing_deadline": "2026-03-10", "days_remaining": 3 }],
  "urgent_without_finalists": [{ "job_id": 7, "title": "...", "urgency_level": 5 }],
  "stale": [{ "job_id": 15, "title": "...", "last_activity_at": "2026-01-20", "days_inactive": 46 }],
  "no_applies": [{ "job_id": 22, "title": "...", "days_open": 14 }],
  "summary": { "total_alerts": 8 }
}
```

---

#### GET /v1/users/jobs/:id/kanban

**Propósito:** Dados do Kanban (pipeline visual) de uma vaga.

**Params:** `selective_process_id` (opcional), `term` (busca), `page`

**Response:** Array de colunas, cada uma com applies paginados.

---

#### GET /v1/users/jobs/:id/activity_log

**Propósito:** Timeline de atividades de uma vaga.

---

#### GET /v1/users/jobs/:id/evaluations

**Propósito:** Avaliações configuradas para uma vaga.

---

#### POST /v1/users/jobs/:id/change_status

**Propósito:** Mudar status da vaga.

**Body:** `{ "job_status_id": 5 }`

---

### 2.2 Candidaturas (Applies)

#### GET /v1/users/applies

**Propósito:** Listar candidaturas com filtros. Endpoint principal para funil.

**Filtros úteis:**
```json
{
  "where": {
    "job_id": 123,
    "selective_process_id": 456,
    "evaluation_candidate_status": 0,
    "is_deleted": false,
    "created_at": { "gte": "2026-03-01" }
  }
}
```

**Response (campos principais):**
```json
{
  "id": "789",
  "type": "apply",
  "attributes": {
    "candidate_id": 100,
    "job_id": 123,
    "name": "João Silva",
    "email": "joao@email.com",
    "selective_process_id": 456,
    "selective_process_name": "Entrevista Técnica",
    "selective_process_status": "interview",
    "evaluation_candidate_status": "answered",
    "cv_match": 85.5,
    "total_score": 72.0,
    "sub_status": null,
    "reason_for_reject": null,
    "source": "linkedin",
    "created_at": "2026-02-20T15:30:00Z",
    "evaluation_candidate_scores": { "eval_1": 4.2 },
    "evaluation_candidate_summaries": { "eval_1": "Candidato forte em..." },
    "meetings": [{ "id": 1, "start_time": "...", "sub_status": "confirmed" }]
  }
}
```

---

#### PUT /v1/users/applies/:id

**Propósito:** Atualizar candidatura (mover no pipeline, rejeitar, etc.).

**Body:** `{ "selective_process_id": 789, "sub_status": "no_show", "reason_for_reject": "..." }`

---

### 2.3 Candidatos (Candidates)

#### GET /v1/users/candidates

**Propósito:** Listar candidatos com filtros.

**Filtros úteis:**
```json
{
  "where": {
    "source": "linkedin",
    "city": "São Paulo",
    "is_deleted": false,
    "created_at": { "gte": "2026-03-01" }
  }
}
```

**Response (campos principais):**
```json
{
  "id": "100",
  "type": "candidate",
  "attributes": {
    "uid": "cand_abc123",
    "name": "João Silva",
    "email": "joao@email.com",
    "mobile_phone": "+5511999999999",
    "linkedin": "https://linkedin.com/in/joaosilva",
    "current_company": "Tech Corp",
    "role_name": "Senior Developer",
    "position_level": "Senior",
    "source": "linkedin",
    "city": "São Paulo",
    "state": "SP",
    "clt_expectation": 15000.0,
    "remote_work": true,
    "created_at": "2026-02-20T10:00:00Z",
    "applies": [
      { "job_id": 123, "job_title": "Full Stack Dev", "selective_process_id": 456 }
    ]
  }
}
```

---

### 2.4 Avaliações (Evaluations)

#### GET /v1/users/evaluations/evaluations

**Propósito:** Listar avaliações configuradas.

---

#### GET /v1/users/evaluations/evaluations/:id/dashboard_stats

**Propósito:** Estatísticas de uma avaliação específica.

**Response:** Métricas de conclusão, scores médios, distribuição, pendentes.

---

#### GET /v1/users/evaluation_candidates

**Propósito:** Listar envios de avaliação (quem respondeu, quem está pendente).

**Filtros úteis:**
```json
{
  "where": {
    "completed": true,
    "evaluation_id": 5,
    "job_id": 123,
    "created_at": { "gte": "2026-03-01" }
  }
}
```

**Response (campos principais):**
```json
{
  "id": "50",
  "type": "evaluation_candidate",
  "attributes": {
    "candidate_name": "João Silva",
    "candidate_email": "joao@email.com",
    "evaluation_name": "Teste Técnico Ruby",
    "completed": true,
    "score": 4.2,
    "wsi_classification": "strong_fit",
    "wsi_level": "advanced",
    "wsi_summary": "Candidato demonstra domínio avançado...",
    "ai_feedback": { "summary": "...", "strengths": [...], "weaknesses": [...] },
    "evaluation_summary": "Score médio de 4.2/5...",
    "is_screening": false
  }
}
```

---

### 2.5 Entrevistas e Agenda

#### GET /v1/users/calendar_events

**Propósito:** Listar eventos do calendário.

**Filtros úteis:**
```json
{
  "where": {
    "event_type": "interview",
    "is_cancelled": false,
    "start_time": { "gte": "2026-03-07T00:00:00Z", "lte": "2026-03-07T23:59:59Z" }
  }
}
```

---

#### GET /v1/users/calendar_events/daily_agenda

**Propósito:** Agenda diária formatada.

**Params:**
| Param | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `from` | datetime | Início do período | `"2026-03-07T00:00:00"` |
| `to` | datetime | Fim do período | `"2026-03-07T23:59:59"` |
| `timezone` | string | Fuso horário | `"America/Sao_Paulo"` |
| `event_type` | string | Filtrar por tipo | `"interview"` |
| `organizer_id` | integer | Filtrar por organizador | `10` |

---

#### GET /v1/users/meetings

**Propósito:** Listar reuniões/entrevistas agendadas.

**Filtros úteis:**
```json
{
  "where": {
    "sub_status": "confirmed",
    "start_time": { "gte": "2026-03-07" }
  }
}
```

---

#### GET /v1/users/interview_sessions

**Propósito:** Listar entrevistas AI.

**Params:**
| Param | Tipo | Descrição |
|-------|------|-----------|
| `job_id` | integer | Filtrar por vaga |
| `status` | string | Filtrar por status |
| `candidate_id` | integer | Filtrar por candidato |

**Response:**
```json
{
  "id": "30",
  "type": "interview_session",
  "attributes": {
    "token": "abc123",
    "status": "completed",
    "interview_type": "voice",
    "score": 4.1,
    "recommendation": "strong_hire",
    "candidate_name": "João Silva",
    "job_title": "Dev Full Stack",
    "started_at": "2026-03-05T14:00:00Z",
    "completed_at": "2026-03-05T14:25:00Z",
    "questions_count": 8,
    "report": { "summary": "...", "strengths": [...] },
    "transcript": [...]
  }
}
```

---

#### GET /v1/users/scheduling/availability

**Propósito:** Obter slots livres de um recrutador.

---

#### GET /v1/users/scheduling/settings

**Propósito:** Configurações de disponibilidade.

---

### 2.6 Sourcing

#### GET /v1/users/sourcings

**Propósito:** Listar buscas de sourcing realizadas.

---

#### GET /v1/users/sourcings/:id/stats

**Propósito:** Estatísticas de um sourcing específico.

**Response:** `sourcing_stats`, `score_distribution`, `roi_metrics`.

---

#### GET /v1/users/sourcings/history

**Propósito:** Histórico de sourcing por data.

**Params:** `page`, `per_page` (default 30).

---

#### GET /v1/users/sourcings/credits

**Propósito:** Consumo de créditos de sourcing.

**Params:** `start_date`, `end_date`.

---

#### GET /v1/users/sourcings/transactions

**Propósito:** Transações de créditos.

**Response:** `{ current_balance, total_consumed, transactions: [...] }`

---

### 2.7 Comunicação

#### GET /v1/users/messages

**Propósito:** Listar mensagens do chat AI (scoped ao usuário logado).

---

### 2.8 Atividades e Logs

#### GET /v1/users/activity_logs

**Propósito:** Log de ações (auditoria e timeline).

**Filtros úteis:**
```json
{
  "where": {
    "reference_type": "Apply",
    "reference_id": 789,
    "category": "pipeline_change"
  }
}
```

**Response:**
```json
{
  "id": "500",
  "type": "activity_log",
  "attributes": {
    "action": "update",
    "reference_type": "Apply",
    "reference_id": 789,
    "changeset": {
      "selective_process_id": [456, 789],
      "selective_process_status": ["screening", "interview"]
    },
    "category": "pipeline_change",
    "user_name": "Maria Recruiter",
    "created_at": "2026-03-06T14:30:00Z"
  }
}
```

---

### 2.9 LLM / Custos

#### GET /v1/users/llm_usages/stats

**Propósito:** Estatísticas de uso de LLM (custo, tokens, latência).

**Response:**
```json
{
  "today": { "total_cost": 0.15, "total_requests": 45, "total_tokens": 25000 },
  "this_week": { "total_cost": 0.85, "total_requests": 230, "total_tokens": 150000 },
  "this_month": { "total_cost": 2.50, "total_requests": 800, "total_tokens": 500000 },
  "last_30_days": { "total_cost": 3.20, "total_requests": 1000, "total_tokens": 650000 }
}
```

---

#### GET /v1/users/llm_usages/by_operation

**Propósito:** Breakdown de custo por operação (search, evaluation, chat, etc.).

---

#### GET /v1/users/llm_usages/daily_trend

**Propósito:** Tendência diária de uso.

**Params:** `days` (1-90, default 30).

---

### 2.10 Aggregações (Genérico)

#### GET /v1/users/aggregators/:entity

**Propósito:** Retorna agregações do Elasticsearch para qualquer entidade. Muito útil para dashboards.

**Params:**
| Param | Tipo | Descrição |
|-------|------|-----------|
| `entity` | string (path) | applies, candidates, jobs, etc. |
| `where` | JSON | Filtros |
| `aggs` | JSON | Agregações customizadas |

**Response:**
```json
{
  "entity": "applies",
  "aggregators": {
    "selective_process_status": {
      "buckets": [
        { "key": "screening", "doc_count": 150 },
        { "key": "interview", "doc_count": 45 },
        { "key": "hired", "doc_count": 12 }
      ]
    },
    "source": {
      "buckets": [
        { "key": "linkedin", "doc_count": 200 },
        { "key": "website", "doc_count": 100 }
      ]
    }
  }
}
```

---

### 2.11 Listas (Lists)

#### GET /v1/users/lists

**Propósito:** Listas customizadas de candidatos/vagas (shortlists).

---

### 2.12 Departamentos e Times

#### GET /v1/users/departments

**Propósito:** Listar departamentos.

---

#### GET /v1/users/departments/tree

**Propósito:** Árvore hierárquica de departamentos.

---

#### GET /v1/users/teams

**Propósito:** Listar times.

---

### 2.13 Empresas (Businesses)

#### GET /v1/users/businesses

**Propósito:** Dados da empresa/perfil institucional.

---

## Seção 3: Métricas e KPIs Calculáveis

### 3.1 Métricas de Funil

#### Candidatos por Fase do Pipeline

**Fórmula:** Contagem de applies por `selective_process_status`
**Dados:** `GET /v1/users/aggregators/applies` com agg por `selective_process_status` **OU** campo `applies_by_status_count` do `GET /v1/users/jobs/:id`
**Granularidade:** Por vaga, por recrutador, global
**Benchmark BR:** Funil saudável — 100 inscritos → 20 triados → 8 entrevistados → 3 finalistas → 1 contratado
**Pergunta:** "quantos candidatos tem em cada etapa da vaga X?", "como tá o funil?"

---

#### Taxa de Conversão entre Fases

**Fórmula:** `candidatos_que_avançaram / candidatos_que_entraram × 100` por etapa
**Dados:** `GET /v1/users/jobs/:id/analytics` → `funnel.stages[].conversion_rate`
**Granularidade:** Por vaga, por etapa
**Benchmark BR:** Triagem→Entrevista: 20-30% | Entrevista→Oferta: 30-50% | Oferta→Contratação: 70-90%
**Pergunta:** "qual a taxa de conversão da vaga de dev?", "onde tá o gargalo?"

---

#### Taxa de Rejeição por Fase

**Fórmula:** `rejeitados_na_fase / total_que_entrou_na_fase × 100`
**Dados:** `GET /v1/users/applies` filtrando por `sub_status` (reason codes) + `selective_process_status: "rejected"`
**Granularidade:** Por vaga, por motivo de rejeição
**Benchmark BR:** Taxa de rejeição > 80% na triagem é normal; > 50% em entrevista indica problema no filtro
**Pergunta:** "por que tão rejeitando tantos?", "quais os motivos de rejeição?"

---

#### Candidatos Novos por Período

**Fórmula:** Contagem de applies com `created_at` no período
**Dados:** `GET /v1/users/applies?where={"created_at":{"gte":"2026-03-01"}}`
**Granularidade:** Dia, semana, mês; por vaga ou global
**Benchmark BR:** Varia muito por senioridade. Junior: 50-200/semana, Senior: 5-20/semana
**Pergunta:** "quantos candidatos entraram essa semana?", "tá vindo gente pra vaga X?"

---

#### Candidatos sem Movimentação (Aging)

**Fórmula:** Applies com `updated_at` ou último `apply_status.created_at` > X dias
**Dados:** `GET /v1/users/jobs/alerts` → `stale` **OU** `GET /v1/users/applies` com filtro de data
**Granularidade:** Por vaga
**Benchmark BR:** > 5 dias sem movimentação em triagem é lento; > 3 dias em entrevista é alarmante
**Pergunta:** "tem candidato parado?", "quem tá esperando retorno?"

---

### 3.2 Métricas de Tempo

#### Time-to-Fill

**Fórmula:** `data_contratação - data_abertura_vaga` (em dias)
**Dados:** `GET /v1/users/jobs/stats` → `avg_days_to_close` **OU** Jobs com status "Contratado" — diff entre `created_at` e activity log de `status → hired`
**Granularidade:** Por vaga, média geral, por departamento
**Benchmark BR:** CLT Júnior: 20-30 dias | Pleno: 30-45 dias | Sênior: 45-75 dias | Liderança: 60-120 dias
**Pergunta:** "quanto tempo tá levando pra fechar vaga?", "qual o time-to-fill médio?"

---

#### Time-to-Hire

**Fórmula:** `data_contratação - data_primera_candidatura_do_contratado` (em dias)
**Dados:** Para o apply com `selective_process.status == hired`: `apply.created_at` vs `apply_status.created_at` (hired)
**Granularidade:** Por vaga, por candidato contratado
**Benchmark BR:** 15-40 dias é ideal
**Pergunta:** "quanto tempo levou do candidato aplicar até ser contratado?"

---

#### Tempo Médio em Cada Fase

**Fórmula:** Média de `(apply_status[N+1].created_at - apply_status[N].created_at)` por etapa
**Dados:** `GET /v1/users/jobs/:id/analytics` → `funnel.stages[].avg_time_in_stage_hours`
**Granularidade:** Por vaga, por etapa
**Benchmark BR:** Triagem: 24-48h | Entrevista: 3-7 dias | Oferta: 2-5 dias
**Pergunta:** "onde tá demorando mais?", "quanto tempo os candidatos ficam em cada etapa?"

---

#### Tempo de Resposta do Recrutador

**Fórmula:** Diferença entre `apply.created_at` e primeiro `apply_status.created_at` (primeira ação)
**Dados:** `GET /v1/users/jobs/:id/analytics` → `velocity.avg_time_to_first_action_hours`
**Granularidade:** Por recrutador, por vaga
**Benchmark BR:** < 24h = Excelente | 24-48h = Bom | 48-72h = Regular | > 72h = Ruim
**Pergunta:** "quanto tempo levo pra responder os candidatos?"

---

#### Vagas Abertas há Mais de X Dias

**Fórmula:** `hoje - job.published_date` para vagas ativas
**Dados:** `GET /v1/users/jobs/stats` → `jobs_ranking.longest_open` **OU** `GET /v1/users/jobs/alerts` → `stale`
**Granularidade:** Ranking
**Benchmark BR:** > 60 dias sem fechar é preocupante
**Pergunta:** "quais vagas estão abertas há mais tempo?"

---

### 3.3 Métricas de Volume

#### Vagas Abertas/Fechadas/Pausadas

**Fórmula:** Contagem por status
**Dados:** `GET /v1/users/jobs/stats` → `by_status`, `open_vs_closed`, `totals`
**Granularidade:** Por período, por departamento, por recrutador
**Pergunta:** "quantas vagas tenho abertas?", "quantas fechei esse mês?"

---

#### Candidaturas por Vaga

**Fórmula:** `count(applies)` por job
**Dados:** `GET /v1/users/jobs` → `applies_count`
**Granularidade:** Por vaga, ranking
**Benchmark BR:** < 10 candidatos em 1 semana = Baixa atração | > 100 = Alta
**Pergunta:** "qual vaga tem mais candidatos?", "tá vindo gente?"

---

#### Entrevistas Agendadas/Realizadas/Canceladas

**Fórmula:** Contagem de meetings/calendar_events por `sub_status`
**Dados:** `GET /v1/users/jobs/:id/analytics` → `scheduling` **OU** `GET /v1/users/meetings`
**Granularidade:** Por período, por vaga
**Pergunta:** "quantas entrevistas tenho essa semana?", "quantas foram canceladas?"

---

#### Avaliações Enviadas/Respondidas/Pendentes

**Fórmula:** Contagem de evaluation_candidates por `completed` (true/false)
**Dados:** `GET /v1/users/evaluation_candidates?where={"completed":true}`
**Granularidade:** Por avaliação, por vaga
**Pergunta:** "quantos candidatos responderam o teste?", "quantos faltam?"

---

### 3.4 Métricas de Qualidade

#### Score Médio dos Candidatos

**Fórmula:** `AVG(evaluation_candidates.score)` ou `AVG(applies.cv_match)`
**Dados:** `GET /v1/users/jobs/:id/analytics` → `quality.avg_cv_match`, `quality.evaluation_stats.avg_score`
**Granularidade:** Por vaga, por avaliação
**Benchmark BR:** Score WSI > 3.5/5.0 = Strong fit | 2.5-3.5 = Moderate | < 2.5 = Weak
**Pergunta:** "qual a qualidade dos candidatos da vaga X?"

---

#### Taxa de Desistência (Dropout)

**Fórmula:** `applies com sub_status == 'withdrew' / total_applies × 100`
**Dados:** `GET /v1/users/applies?where={"sub_status":"withdrew"}`
**Granularidade:** Por vaga, por etapa
**Benchmark BR:** < 5% = Normal | 5-15% = Atenção | > 15% = Problema (salário, experiência, timing)
**Pergunta:** "tem muito candidato desistindo?"

---

#### Taxa de No-Show

**Fórmula:** `meetings com sub_status == 'no_show' / total_meetings × 100`
**Dados:** `GET /v1/users/jobs/:id/analytics` → `scheduling.no_show_count`
**Granularidade:** Por vaga, por período
**Benchmark BR:** < 10% = Normal | 10-20% = Alto | > 20% = Crítico
**Pergunta:** "tá tendo muito no-show?"

---

#### Qualidade do Sourcing

**Fórmula:** `sourced_profiles com status 'hired' ou importados que avançaram / total_sourced × 100`
**Dados:** `GET /v1/users/sourcings/:id/stats` → `roi_metrics`
**Granularidade:** Por busca, por período
**Pergunta:** "o sourcing tá valendo a pena?", "quanto dos perfis encontrados avançaram?"

---

### 3.5 Métricas de Produtividade

#### Candidatos Triados por Dia/Semana

**Fórmula:** Contagem de `apply_statuses` com mudança de `web_submission → screening` por período
**Dados:** `GET /v1/users/activity_logs?where={"reference_type":"Apply","category":"pipeline_change"}` por usuário/período
**Granularidade:** Por recrutador, por período
**Benchmark BR:** 20-40 triagens/dia é produtivo
**Pergunta:** "quantos candidatos triei hoje?", "como tá minha produtividade?"

---

#### Vagas Gerenciadas Simultaneamente

**Fórmula:** Contagem de jobs ativos por `user_id`
**Dados:** `GET /v1/users/jobs?where={"is_active":true,"user_id":10}`
**Granularidade:** Por recrutador
**Benchmark BR:** 5-15 vagas simultâneas é normal para recrutador R&S
**Pergunta:** "quantas vagas cada recrutador tá gerenciando?"

---

### 3.6 Métricas de Custo

#### Custo de LLM por Vaga

**Fórmula:** `SUM(llm_usages.cost_usd) WHERE context.job_id = X`
**Dados:** `GET /v1/users/llm_usages?where={"context.job_id":123}`
**Granularidade:** Por vaga, por operação, por mês
**Pergunta:** "quanto tô gastando de IA nessa vaga?"

---

#### Custo de Sourcing

**Fórmula:** `SUM(sourcings.credits_used)` por período
**Dados:** `GET /v1/users/sourcings/credits`
**Granularidade:** Por período, por busca
**Pergunta:** "quantos créditos usei esse mês?", "quanto custa um sourcing?"

---

## Seção 4: Alertas e Triggers para Proatividade

### 4.1 Candidato Esperando Retorno

**Condição:** Apply sem `apply_status` novo há > 48h (triagem) ou > 72h (entrevista)
**Dados:** `GET /v1/users/applies` com filtro de `updated_at` antigo + status != rejected/hired
**Severidade:** 🟡 Atenção (48h) → 🔴 Urgente (72h+)
**Mensagem:** "⚠️ {candidato_name} está na etapa '{etapa}' da vaga '{vaga}' há {N} dias sem movimentação. Deseja avançar ou dar retorno?"
**Frequência:** A cada 12h

---

### 4.2 Vaga sem Movimentação

**Condição:** Job ativo sem nenhum `apply_status` criado em 7+ dias
**Dados:** `GET /v1/users/jobs/alerts` → `stale`
**Severidade:** 🟡 Atenção (7 dias) → 🔴 Urgente (14+ dias)
**Mensagem:** "🔴 A vaga '{título}' está sem movimentação há {N} dias. Considere revisar o pipeline ou fazer sourcing."
**Frequência:** 1x/dia (manhã)

---

### 4.3 Entrevista nas Próximas 24h

**Condição:** CalendarEvent/Meeting com `start_time` nas próximas 24h, `event_type == 'interview'`
**Dados:** `GET /v1/users/calendar_events/daily_agenda?from=now&to=+24h&event_type=interview`
**Severidade:** 🟢 Informativo
**Mensagem:** "📅 Entrevista amanhã: {candidato_name} para {vaga_title} às {hora}. Link: {join_url}"
**Frequência:** 1x/dia (manhã) + 1h antes

---

### 4.4 No-Show em Entrevista

**Condição:** Meeting com `sub_status == 'no_show'` criado nas últimas 24h
**Dados:** `GET /v1/users/meetings?where={"sub_status":"no_show","updated_at":{"gte":"24h_ago"}}`
**Severidade:** 🟡 Atenção
**Mensagem:** "😕 {candidato_name} não compareceu à entrevista para '{vaga}'. Deseja reagendar ou rejeitar?"
**Frequência:** A cada 2h durante horário comercial

---

### 4.5 Avaliação Respondida Aguardando Análise

**Condição:** EvaluationCandidate com `completed == true` nas últimas 24h
**Dados:** `GET /v1/users/evaluation_candidates?where={"completed":true,"updated_at":{"gte":"24h_ago"}}`
**Severidade:** 🟢 Informativo (se tem AI feedback) → 🟡 Atenção (se não tem)
**Mensagem:** "✅ {candidato_name} completou o teste '{avaliação}' para '{vaga}'. Score: {score}/5.0 ({wsi_classification}). {resumo_ai}"
**Frequência:** A cada 4h

---

### 4.6 Candidato Desistiu

**Condição:** Apply movido para `sub_status == 'withdrew'` nas últimas 24h
**Dados:** `GET /v1/users/applies?where={"sub_status":"withdrew","updated_at":{"gte":"24h_ago"}}`
**Severidade:** 🟡 Atenção
**Mensagem:** "⛔ {candidato_name} desistiu do processo para '{vaga}' na etapa '{etapa}'. Motivo: {reason}"
**Frequência:** A cada 6h

---

### 4.7 Vaga com Prazo Vencido

**Condição:** Job com `closing_deadline < today` e status ativo
**Dados:** `GET /v1/users/jobs/alerts` → `deadline_expired`
**Severidade:** 🔴 Urgente
**Mensagem:** "🚨 A vaga '{título}' passou do prazo de fechamento ({deadline}). Já se passaram {N} dias. Precisa fechar ou estender?"
**Frequência:** 1x/dia

---

### 4.8 Vaga com Prazo Próximo

**Condição:** Job com `closing_deadline` nos próximos 7 dias
**Dados:** `GET /v1/users/jobs/alerts` → `deadline_soon`
**Severidade:** 🟡 Atenção
**Mensagem:** "⏰ A vaga '{título}' vence em {N} dias ({deadline}). Status atual: {X} candidatos em processo."
**Frequência:** 1x/dia

---

### 4.9 Pico de Candidaturas

**Condição:** Vaga recebeu > 2x a média diária de candidaturas nas últimas 24h
**Dados:** `GET /v1/users/jobs/:id/analytics` → `velocity.applies_per_day` e `velocity.applies_trend`
**Severidade:** 🟢 Informativo
**Mensagem:** "📈 A vaga '{título}' recebeu {N} candidaturas hoje (média é {M}/dia). Pode ser hora de triar!"
**Frequência:** 1x/dia (final do dia)

---

### 4.10 Candidato Strong-Fit

**Condição:** EvaluationCandidate com `wsi_classification == 'strong_fit'` ou `score >= 4.0` completado nas últimas 24h
**Dados:** `GET /v1/users/evaluation_candidates?where={"completed":true,"score":{"gte":4.0}}`
**Severidade:** 🔴 Urgente (ação rápida para não perder)
**Mensagem:** "🌟 Candidato forte detectado! {candidato_name} marcou {score}/5.0 no teste de '{vaga}'. Classificação: {wsi_classification}. Recomendo avançar rapidamente."
**Frequência:** A cada 2h

---

### 4.11 Vaga sem Candidatas

**Condição:** Job ativo com 0 applies após 7+ dias publicado
**Dados:** `GET /v1/users/jobs/alerts` → `no_applies`
**Severidade:** 🟡 Atenção (7 dias) → 🔴 Urgente (14+ dias)
**Mensagem:** "🔍 A vaga '{título}' está publicada há {N} dias e não recebeu nenhum candidato. Sugestões: revisar título, ampliar divulgação, ou considerar sourcing ativo."
**Frequência:** 1x/dia

---

### 4.12 Vaga Urgente sem Finalistas

**Condição:** Job com `is_urgent == true` ou `urgency_level >= 4` sem applies em etapas avançadas (interview+)
**Dados:** `GET /v1/users/jobs/alerts` → `urgent_without_finalists`
**Severidade:** 🔴 Urgente
**Mensagem:** "🚨 Vaga urgente '{título}' ainda não tem candidatos na etapa de entrevista. Nível de urgência: {urgency}. Ação imediata recomendada."
**Frequência:** 1x/dia

---

## Seção 5: Briefing Matinal — Estrutura Completa

### Sequência de Chamadas API

```
1. GET /v1/users/jobs/stats?start_date=yesterday → overview geral
2. GET /v1/users/jobs/alerts → alertas ativos
3. GET /v1/users/applies?where={"created_at":{"gte":"yesterday"}}&per_page=30 → novos candidatos
4. GET /v1/users/calendar_events/daily_agenda?from=today_start&to=today_end → agenda
5. GET /v1/users/evaluation_candidates?where={"completed":true,"updated_at":{"gte":"yesterday"}} → avaliações
6. GET /v1/users/activity_logs?where={"created_at":{"gte":"yesterday"}}&per_page=50 → movimentações
7. GET /v1/users/meetings?where={"sub_status":"no_show","updated_at":{"gte":"yesterday"}} → no-shows
```

### Estrutura do Briefing

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☀️ BOM DIA, {NOME}!
Sexta, 7 de Março de 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMO DE ONTEM
• {N} novos candidatos recebidos
• {N} movimentações no pipeline  
• {N} entrevistas realizadas
• {N} avaliações completadas
• {N} vagas ativas | {N} pendências

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 PENDÊNCIAS URGENTES ({total})

🔴 {N} candidatos esperando retorno há +48h
   → {candidato1} - {vaga} (3 dias)
   → {candidato2} - {vaga} (2 dias)

🔴 {N} vagas com prazo vencido
   → {vaga_title} (venceu há 5 dias)

🟡 {N} vagas sem movimentação há +7 dias
   → {vaga_title} (12 dias parado)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 AGENDA DE HOJE

09:00 - Entrevista com João Silva
        → Vaga: Dev Full Stack Senior
        → Link: {join_url}

14:30 - Entrevista com Maria Oliveira
        → Vaga: Product Manager
        → Link: {join_url}

16:00 - Feedback com gerente (vaga QA)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 NOVOS CANDIDATOS
(top 5 por score/relevância)

🌟 Ana Costa - Dev Full Stack (cv_match: 92%)
   Origem: LinkedIn | Empresa: Nubank
   
⭐ Pedro Santos - Dev Backend (cv_match: 85%)
   Origem: Website | Empresa: iFood

📝 +{N} outros candidatos novos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ AVALIAÇÕES COMPLETADAS

🧠 Carlos Mendes finalizou teste "Ruby Technical"
   → Score: 4.3/5 | WSI: Strong Fit
   → IA: "Forte em design patterns, melhoria sugerida em testes"

🧠 Julia Lima finalizou teste "React Assessment"
   → Score: 2.8/5 | WSI: Moderate Fit  
   → IA: "Conhecimento básico, falta experiência com hooks avançados"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 AÇÕES SUGERIDAS (por prioridade)

1. 🔴 Responder {candidato} que está há 4 dias na triagem
2. 🟡 Revisar avaliação de Carlos Mendes (strong fit!)
3. 🟡 Preparar-se para entrevista das 09:00
4. 🟢 Publicar vaga "{título}" que está completa (85%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Regras de Formatação

- **Máximo:** 15 items por seção (priorizar por urgência/relevância)
- **Omitir seções vazias:** Se não há pendências, não mostrar
- **Ordenação:** Urgente → Atenção → Informativo
- **Candidatos novos:** Mostrar top 5 por `cv_match` ou `total_score`
- **Texto clean:** Funcionar em WhatsApp, Teams e web (sem HTML)

---

## Seção 6: Report sob Demanda — Templates

### 6.1 Status de Vaga (para Gestor)

**Trigger:** "me dá um resumo da vaga X", "gera um relatório pra mandar pro gestor"

**Dados:**
```
GET /v1/users/jobs/:id → detalhes da vaga
GET /v1/users/jobs/:id/analytics → métricas completas
GET /v1/users/applies?where={"job_id":ID,"selective_process_status":"interview"} → finalistas
```

**Formato:** Texto no chat + opção de gerar PDF

**Template:**
```
📋 STATUS DA VAGA: {título}
Atualizado em: {data}
━━━━━━━━━━━━━━━━━━━━━━━━

📊 OVERVIEW
• Status: {status}
• Dias aberta: {N}
• Prazo: {deadline} ({N} dias restantes)
• Recrutador: {nome}

📈 FUNIL
• Inscritos: {N}
• Triagem: {N} (conversão: {X}%)
• Entrevista: {N} (conversão: {X}%)
• Oferta: {N}
• Contratados: {N}
• Gargalo: {etapa_bottleneck}

⏱️ VELOCIDADE
• Tempo médio até 1ª ação: {N}h
• Candidaturas/dia: {N}
• Tempo médio no pipeline: {N} dias

🎯 QUALIDADE
• Match médio: {N}%
• Score médio: {N}/5
• Taxa de triagem: {N}% aprovados
• No-shows: {N}

👥 FINALISTAS ({N})
1. {nome} - Score: {score} | Etapa: {etapa}
2. {nome} - Score: {score} | Etapa: {etapa}
3. {nome} - Score: {score} | Etapa: {etapa}

📌 PRÓXIMOS PASSOS SUGERIDOS
• {sugestão baseada nos dados}
```

---

### 6.2 Comparação entre Candidatos Finalistas

**Trigger:** "compara os finalistas da vaga X", "quem é melhor: João ou Maria?"

**Dados:**
```
GET /v1/users/applies?where={"job_id":ID,"selective_process_status":"interview"}
GET /v1/users/evaluation_candidates?where={"job_id":ID,"completed":true}
```

**Template:**
```
⚖️ COMPARAÇÃO DE FINALISTAS
Vaga: {título}
━━━━━━━━━━━━━━━━━━━━━━━━

                    {Cand. 1}    {Cand. 2}    {Cand. 3}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score Avaliação     4.3/5        3.8/5        4.1/5
CV Match            92%          78%          85%
WSI                 Strong       Moderate     Strong
Exp. (anos)         8            5            6
Empresa Atual       Nubank       iFood        Itaú
Pretensão CLT       R$18k        R$14k        R$16k
Aceita remoto?      Sim          Não          Sim
Pontos fortes       {resumo}     {resumo}     {resumo}
Pontos fracos       {resumo}     {resumo}     {resumo}

💡 RECOMENDAÇÃO
Baseado nos dados, {candidato_X} apresenta melhor fit geral 
considerando {critérios}.
```

---

### 6.3 Performance do Recrutador

**Trigger:** "como tá minha performance?", "relatório da minha produtividade"

**Dados:**
```
GET /v1/users/jobs/stats?start_date=30d_ago
GET /v1/users/jobs?where={"user_id":current,"is_active":true}
GET /v1/users/activity_logs?where={"user_id":current} (contagem)
```

**Template:**
```
📊 PERFORMANCE - {nome_recrutador}
Período: {start} a {end}
━━━━━━━━━━━━━━━━━━━━━━━━

📋 VAGAS
• Ativas: {N}
• Fechadas no período: {N}
• Média de dias p/ fechar: {N}
• Vagas com prazo vencido: {N}

👤 CANDIDATOS
• Triados: {N}
• Entrevistados: {N}
• Contratados: {N}
• Avg tempo de resposta: {N}h

📈 CONVERSÃO
• Triagem → Entrevista: {X}%
• Entrevista → Oferta: {X}%
• Oferta → Contratação: {X}%

🤖 USO DE IA
• Custo LLM: ${X}
• Créditos sourcing usados: {N}
• Avaliações AI disparadas: {N}
```

---

### 6.4 Resumo Semanal

**Trigger:** "resumo da semana", "como foi essa semana?"

**Dados:**
```
GET /v1/users/jobs/stats?start_date=7d_ago
GET /v1/users/jobs/alerts
GET /v1/users/applies?where={"created_at":{"gte":"7d_ago"}}&per_page=1 (só pra total)
GET /v1/users/evaluation_candidates?where={"completed":true,"updated_at":{"gte":"7d_ago"}}
```

**Template:**
```
📊 RESUMO SEMANAL
{data_início} a {data_fim}
━━━━━━━━━━━━━━━━━━━━━━━━

✅ CONQUISTAS DA SEMANA
• {N} vagas abertas, {N} fechadas
• {N} candidatos novos recebidos
• {N} entrevistas realizadas
• {N} contratações efetuadas

📈 MÉTRICAS VS SEMANA ANTERIOR
• Candidatos: {N} ({+X}% vs semana anterior)
• Entrevistas: {N} ({-X}%)
• Time-to-hire médio: {N} dias ({trend})

⚠️ PONTOS DE ATENÇÃO
• {N} candidatos esperando retorno
• {N} vagas sem movimentação
• {N} avaliações pendentes de análise

🎯 META PRÓXIMA SEMANA
• Triar {N} candidatos pendentes
• Fechar vaga "{título}"
• Enviar feedback para {N} rejeitados
```

---

### 6.5 Pipeline com Gargalos

**Trigger:** "identifica os gargalos", "onde tá travando?"

**Dados:**
```
Para cada vaga ativa:
  GET /v1/users/jobs/:id/analytics → funnel + velocity
```

**Template:**
```
🔍 ANÁLISE DE GARGALOS
━━━━━━━━━━━━━━━━━━━━━━━━

🔴 GARGALOS IDENTIFICADOS (por severidade)

1. Vaga "{título}" - Etapa: Entrevista Técnica
   → {N} candidatos há +5 dias nessa etapa
   → Tempo médio: {N}h (benchmark: 72h)
   → Causa provável: falta de agenda dos entrevistadores
   → Sugestão: agendar entrevistas em bloco

2. Vaga "{título}" - Etapa: Triagem
   → {N} candidatos aguardando triagem
   → Tempo médio: {N}h (benchmark: 48h)
   → Causa provável: volume alto + triagem manual
   → Sugestão: ativar triagem AI automática

📊 FLUXO GERAL (todas as vagas)
Inscrição ──{X}%──→ Triagem ──{X}%──→ Entrevista ──{X}%──→ Oferta ──{X}%──→ Contratação
                      ⬆️ LENTO                    ⬆️ GARGALO
```

---

## Seção 7: Fluxo de Dados para o Agente Insights

### 7.1 Cenário: Briefing Matinal ("me atualiza")

```
Recrutador: "me atualiza" / "bom dia" / "como tá?"
    │
    ▼
Agente Insights (paralelo):
    ├── GET /v1/users/jobs/stats?start_date=yesterday
    │   → Resumo de vagas: abertas, fechadas, criadas
    │
    ├── GET /v1/users/jobs/alerts
    │   → Alertas: prazo vencido, vagas paradas, urgentes
    │
    ├── GET /v1/users/applies?where={"created_at":{"gte":"yesterday"}}&order={"cv_match":"desc"}&per_page=10
    │   → Candidatos novos (top 10 por score)
    │
    ├── GET /v1/users/calendar_events/daily_agenda?from=today_start&to=today_end&event_type=interview
    │   → Entrevistas do dia
    │
    ├── GET /v1/users/evaluation_candidates?where={"completed":true,"updated_at":{"gte":"yesterday"}}&per_page=10
    │   → Avaliações completadas
    │
    └── GET /v1/users/meetings?where={"sub_status":"no_show","updated_at":{"gte":"2d_ago"}}
        → No-shows recentes
    │
    ▼
Agrega → Prioriza → Formata briefing
    │
    ▼
Envia ao recrutador (WhatsApp/Teams/Web)
```

### 7.2 Cenário: Status de Vaga ("como tá a vaga de dev?")

```
Recrutador: "como tá a vaga de dev senior?"
    │
    ▼
Agente Insights:
    │
    ├── STEP 1: Identificar a vaga
    │   GET /v1/users/jobs?search=dev senior&per_page=5
    │   → Mapeia título → ID (pode perguntar se ambíguo)
    │
    ├── STEP 2: Buscar analytics
    │   GET /v1/users/jobs/{id}/analytics
    │   → Funil, velocidade, qualidade, scheduling
    │
    ├── STEP 3: Buscar finalistas
    │   GET /v1/users/applies?where={"job_id":{id},"selective_process_status":{"in":["interview","hired"]}}&order={"total_score":"desc"}&per_page=5
    │   → Top candidatos avançados
    │
    └── STEP 4: Buscar avaliações
        GET /v1/users/evaluation_candidates?where={"job_id":{id},"completed":true}&order={"score":"desc"}&per_page=5
        → Resultados de avaliações
    │
    ▼
Formata report com overview, funil, finalistas, sugestões
```

### 7.3 Cenário: Métrica Específica ("quantos candidatos entraram essa semana?")

```
Recrutador: "quantos candidatos entraram essa semana?"
    │
    ▼
Agente Insights:
    │
    ├── GET /v1/users/aggregators/applies
    │   body: { "where": {"created_at":{"gte":"this_week_start"},"is_deleted":false} }
    │   → total count no meta
    │
    └── GET /v1/users/aggregators/applies
        body: { "where": {"created_at":{"gte":"this_week_start"}}, "aggs": {"job_id":{}} }
        → Breakdown por vaga
    │
    ▼
"📊 Essa semana entraram {N} candidatos:
 • Vaga 'Dev Full Stack': {N}
 • Vaga 'Product Manager': {N}
 • Vaga 'QA Sênior': {N}
 (+{N} outras vagas)"
```

### 7.4 Cenário: Alerta Proativo (background polling)

```
Cron Job (a cada 2h):
    │
    ├── GET /v1/users/jobs/alerts → verifica alertas
    │
    ├── GET /v1/users/evaluation_candidates?where={"completed":true,"score":{"gte":4.0},"updated_at":{"gte":"2h_ago"}}
    │   → Strong-fits recentes
    │
    ├── GET /v1/users/applies?where={"sub_status":"withdrew","updated_at":{"gte":"2h_ago"}}
    │   → Desistências recentes
    │
    └── GET /v1/users/meetings?where={"sub_status":"no_show","updated_at":{"gte":"2h_ago"}}
        → No-shows recentes
    │
    ▼
Para cada alerta novo (não enviado antes):
    └── Envia notificação no canal ativo do recrutador
```

### 7.5 Cenário: Report PDF ("gera relatório pro gestor")

```
Recrutador: "gera um relatório da vaga de dev pra mandar pro gestor"
    │
    ▼
Agente Insights:
    │
    ├── Identifica vaga (mesmo flow 7.2 step 1)
    ├── Coleta dados (analytics + applies + evaluations)
    ├── Gera texto formatado (template 6.1)
    │
    ├── Se canal = Web/Teams:
    │   └── Gera PDF via serviço de renderização
    │       → Retorna link pro download
    │
    └── Se canal = WhatsApp:
        └── Envia resumo em texto
            → "📋 Resumo enviado! Para PDF completo, acesse: {link}"
```

---

## Seção 8: Considerações Técnicas

### 8.1 Autenticação

**Método recomendado para o agente: Service Token via OAuth**

```python
import httpx

async def get_service_token(client_id: str, client_secret: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/oauth/token",
            json={
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        data = response.json()
        return data["access_token"]  # JWT válido por 5 minutos
```

**Método alternativo: Agent Token Exchange (quando tem contexto de usuário)**

```python
async def exchange_agent_token(one_time_token: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/agent_tokens/exchange",
            json={"one_time_token": one_time_token}
        )
        data = response.json()
        return data["access_token"]  # JWT com user_id + account_id
```

**Headers para todas as requests:**
```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

**Token refresh:** O service token expira em 5 minutos. O agente deve:
1. Cachear o token localmente
2. Renovar 30s antes da expiração
3. Tratar 401 com retry automático + novo token

---

### 8.2 Multi-tenancy

O tenant é determinado automaticamente pelo JWT:
- **Service token** (`POST /v1/oauth/token`): O `client_id` pertence a um `ApiClient` que está vinculado a um `account_id`. O backend faz `Apartment::Tenant.switch!` para o schema correto.
- **Agent token** (`POST /v1/agent_tokens/exchange`): O OTT contém `user_id` e o backend resolve o `account` via `user.account`.

**O agente NÃO precisa** enviar tenant/account_id nos headers — é implícito no token.

**Regra crítica:** Cada token acessa SOMENTE dados do seu tenant. Impossível acessar dados de outro tenant, mesmo com SQL injection.

---

### 8.3 Paginação

**Tipo:** Page-based (não cursor-based).

```python
async def fetch_all_pages(endpoint: str, where: dict, max_pages: int = 10):
    all_data = []
    page = 1
    while page <= max_pages:
        response = await client.get(
            endpoint,
            params={"page": page, "per_page": 30, "where": json.dumps(where)}
        )
        data = response.json()
        all_data.extend(data.get("data", []))
        total = data.get("meta", {}).get("total", 0)
        if page * 30 >= total:
            break
        page += 1
    return all_data
```

**Limites:**
- `per_page` máximo: 30
- Para listagens grandes, usar filtros para reduzir scope (por job_id, por data, etc.)
- Endpoints de stats/analytics já retornam dados agregados (não requerem paginação)

---

### 8.4 Rate Limiting

⚠️ **DADO NÃO ENCONTRADO:** Não foi identificado rate limiting explícito nos controllers/middleware, exceto:
- Endpoint de login: 5 tentativas / 60 segundos
- Recomendação: limitar o agente a ~10 requests/segundo por segurança

---

### 8.5 Cache

**Recomendações de cache no lado do agente:**

| Dado | TTL | Motivo |
|------|-----|--------|
| Jobs list (active) | 5 min | Vagas não mudam com frequência |
| Job analytics | 10 min | Backend já cacheia por 10 min |
| Job alerts | 15 min | Alertas são checados periodicamente |
| Job stats | 30 min | Dados agregados, atualização lenta |
| Applies list | 2 min | Podem ter movimentações frequentes |
| Calendar events (today) | 5 min | Agenda do dia é relativamente fixa |
| LLM usage stats | 1 hora | Dados de custo mudam lentamente |
| Department/Team lists | 1 hora | Raramente mudam |
| Evaluation candidates | 5 min | Respostas podem chegar |

---

### 8.6 Dados Sensíveis (LGPD)

**Campos que requerem PII masking nos logs:**
- `candidate.email`, `candidate.mobile_phone`, `candidate.cpf`
- `candidate.date_birth`
- `candidate.current_salary`, `candidate.clt_expectation`, `candidate.pj_expectation`
- `user.email`, `user.password_digest`
- Todo conteúdo de `messages.content`
- `ms_access_token`, `ms_refresh_token`

**Recomendações:**
- Nunca logar respostas completas do endpoint de candidatos
- Usar masking: `joao****@email.com`, `***.***.***-12`
- Em relatórios, nunca incluir CPF ou salário sem consentimento
- Respeitar `confidential_user_ids` — candidatos confidenciais só são visíveis para usuários autorizados

---

### 8.7 Limites e Timeouts

| Aspecto | Limite |
|---------|--------|
| Max items por request | 30 (via Elasticsearch per_page) |
| Max items Kanban per column | 10 (PER_PAGE_KANBAN) |
| Service token TTL | 300 segundos (5 min) |
| Agent token OTT | 10 min (one-time-use) |
| Analytics cache | 10 min |
| Elasticsearch timeout | ~30 segundos (padrão) |
| File upload max | 25 MB (audio) |
| LLM daily_trend max | 90 dias |
| LLM recent max | 200 registros |

**Timeouts recomendados para httpx:**
```python
timeout = httpx.Timeout(
    connect=5.0,      # conexão
    read=30.0,        # leitura (analytics pode demorar)
    write=10.0,       # escrita
    pool=5.0           # espera no pool
)
```

---

### 8.8 Elasticsearch vs ActiveRecord

A maioria dos endpoints de listagem usa **Elasticsearch (Searchkick)**, não queries SQL diretas. Isso significa:
- **Vantagem:** Busca full-text, aggregações, filtros avançados, performance
- **Desvantagem:** Dados podem ter ~1-2 segundos de atraso (async reindex)
- **Exceção:** `interview_sessions#index` usa ActiveRecord direto

Para o agente, isso é transparente — a API abstrai o backend de busca.

---

### 8.9 Fluxo de Autenticação Completo

```
┌─────────────────────────┐
│   Frontend/WhatsApp/    │
│   Teams (canal)         │
│                         │
│  1. User se autentica   │══════► POST /v1/sessions
│                         │         → { token: JWT }
│  2. Inicia conversa     │
│     com agente          │
│                         │
│  3. Frontend gera OTT   │══════► (JWT com role: one_time_token, TTL: 10min)
│     para o agente       │
└────────────┬────────────┘
             │
             │ OTT enviado ao agente Python
             ▼
┌─────────────────────────┐
│   Agente Insights       │
│   (Python/LangGraph)    │
│                         │
│  4. Exchange OTT        │══════► POST /v1/agent_tokens/exchange
│                         │         → { access_token: service_JWT, user_id }
│                         │
│  5. Usa service token   │══════► GET /v1/users/jobs/stats
│     para API calls      │         (Authorization: Bearer {service_JWT})
│                         │
│  6. Token expira (5min) │══════► POST /v1/oauth/token (renova)
│                         │
└─────────────────────────┘
```

**Para polling de alertas (background, sem contexto de usuário):**
```
Agente Background Worker
│
├── POST /v1/oauth/token (client_id + client_secret do account)
│   → service_token (sem user_id, mas com account_id)
│
├── GET /v1/users/jobs/alerts → alertas
├── GET /v1/users/evaluation_candidates → avaliações
│
└── Envia notificações via webhook/push
```

---

### 8.10 Endpoints Faltantes (Sugestões)

⚠️ Para o Agente de Insights funcionar com eficiência máxima, os seguintes endpoints seriam úteis mas **NÃO EXISTEM** atualmente:

| Endpoint Sugerido | Propósito | Prioridade |
|---|---|---|
| `GET /v1/users/applies/stats` | Aggregação de applies global (sem precisar vaga) | 🔴 Alta |
| `GET /v1/users/applies/aging` | Candidatos sem movimentação há X dias | 🔴 Alta |
| `GET /v1/users/applies/timeline/:apply_id` | Histórico completo de uma candidatura | 🟡 Média |
| `GET /v1/users/candidates/stats` | Stats de candidatos (novos/período, por source) | 🟡 Média |
| `GET /v1/users/evaluation_candidates/stats` | Stats globais de avaliações | 🟡 Média |
| `GET /v1/users/meetings/stats` | Stats de reuniões (agendadas, no-shows, canceladas) | 🟡 Média |
| `GET /v1/users/dashboard` | Endpoint unificado pra briefing (reduz N calls para 1) | 🟢 Baixa |
| `GET /v1/users/me/productivity` | Métricas de produtividade do recrutador logado | 🟢 Baixa |

Enquanto esses endpoints não existem, o agente pode calcular as métricas combinando os endpoints existentes (com mais chamadas, mas igualmente preciso).
