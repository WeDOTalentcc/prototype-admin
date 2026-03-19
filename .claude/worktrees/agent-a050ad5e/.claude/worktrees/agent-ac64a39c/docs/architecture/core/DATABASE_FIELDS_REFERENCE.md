# DATABASE FIELDS REFERENCE

> **Mapeamento completo de campos do banco de dados da plataforma LIA**  
> **Versão:** 1.0 | **Data:** 22 Janeiro 2026  
> **Objetivo:** Referência técnica para o time de desenvolvimento replicar no stack de produção  
> **Arquivos fonte:** `lia-agent-system/app/models/*.py`

---

## ÍNDICE

1. [Vagas (Job Vacancy)](#1-vagas-job-vacancy)
2. [Candidatos (Candidate)](#2-candidatos-candidate)
3. [Relacionamento Vaga-Candidato](#3-relacionamento-vaga-candidato)
4. [Pipeline e Estágios](#4-pipeline-e-estágios)
5. [Triagem por Voz (WSI)](#5-triagem-por-voz-wsi)
6. [Pareceres LIA](#6-pareceres-lia)
7. [Calibração e Feedback](#7-calibração-e-feedback)
8. [Solicitação de Dados](#8-solicitação-de-dados)
9. [Comunicação](#9-comunicação)
10. [Configurações Admin](#10-configurações-admin)

---

## 1. VAGAS (Job Vacancy)

### Tabela: `job_vacancies`

> **Arquivo:** `lia-agent-system/app/models/job_vacancy.py`

#### Identificação e Multi-tenancy

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `company_id` | String(255) | Sim | ID da empresa (multi-tenancy) |
| `job_id` | String(50) | Não | Código interno (ex: WDT-2025-001) |

#### Informações Básicas

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `title` | String(255) | Sim | Título da vaga |
| `department` | String(100) | Não | Departamento |
| `location` | String(255) | Não | Localização |
| `work_model` | String(50) | Não | presencial, híbrido, remoto |
| `employment_type` | String(50) | Não | CLT, PJ, Temporary |
| `seniority_level` | String(50) | Não | Júnior, Pleno, Sênior, Especialista |

#### Descrição e Requisitos

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `description` | Text | Não | Descrição completa da vaga |
| `requirements` | Array[String] | Não | Requisitos básicos (legacy) |
| `technical_requirements` | JSON | Não | `[{category, technology, level, required}]` |
| `languages` | JSON | Não | `[{language, level, required}]` |
| `behavioral_competencies` | JSON | Não | `[{competency, weight}]` |

#### Remuneração

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `salary` | String(100) | Não | Faixa salarial (legacy) |
| `salary_range` | JSON | Não | `{min, max, currency, bonus}` |
| `benefits` | Array[String] | Não | Lista de benefícios |

#### Status e Workflow

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `status` | String(50) | Sim | Ativa, Rascunho, Pausada, Concluída |
| `stage` | String(50) | Sim | Planejamento, Aprovação, Publicada |
| `priority` | String(20) | Sim | alta, média, baixa |
| `urgency_level` | Integer | Sim | 1-5 |

#### Datas

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `open_date` | DateTime | Não | Data de abertura |
| `deadline` | DateTime | Não | Prazo geral |
| `deadline_screening` | DateTime | Não | Prazo de triagem |
| `deadline_shortlist` | DateTime | Não | Data da shortlist |
| `deadline_closing` | DateTime | Não | Prazo final |

#### Pessoas

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `manager` | String(255) | Não | Nome do gestor |
| `manager_email` | String(255) | Não | Email do gestor |
| `recruiter` | String(255) | Não | Nome do recrutador |
| `recruiter_email` | String(255) | Não | Email do recrutador |
| `created_by` | String(255) | Não | Usuário que criou |

#### Estrutura Organizacional

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `organizational_structure` | JSON | Não | `{directManager, teamSize, teamComposition}` |
| `interview_stages` | JSON | Não | `[{stageName, interviewers, format, duration}]` |
| `screening_questions` | JSON | Não | `[{id, question, type, weight}]` |

#### Publicação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `published_linkedin` | Boolean | Não | Publicado no LinkedIn |
| `published_website` | Boolean | Não | Publicado no site |
| `published_indeed` | Boolean | Não | Publicado no Indeed |
| `linkedin_post_id` | String(255) | Não | ID do post no LinkedIn |
| `indeed_job_id` | String(255) | Não | ID da vaga no Indeed |
| `public_slug` | String(100) | Não | Slug URL-friendly para página pública |

#### Confidencialidade

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `visibility` | String(50) | Sim | public, internal, confidential, hidden |
| `is_confidential` | Boolean | Não | (Legacy) Vaga confidencial |
| `is_affirmative` | Boolean | Não | Vaga afirmativa |
| `access_list` | Array[String] | Não | Lista de usuários com acesso |
| `masked_company_name` | String(255) | Não | Nome mascarado para publicação |
| `confidentiality_config` | JSON | Não | Configuração de confidencialidade |

#### Orçamento

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `budget` | Float | Não | Orçamento da vaga |
| `budget_used` | Float | Não | Orçamento utilizado |

#### Aprovação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `approval_status` | String(50) | Sim | pendente, aprovada, rejeitada |
| `approval_requested_at` | DateTime | Não | Data da solicitação |
| `approval_requested_by` | String(255) | Não | Solicitante |
| `approved_by` | String(255) | Não | Aprovador |
| `approved_at` | DateTime | Não | Data de aprovação |
| `rejection_reason` | Text | Não | Motivo de rejeição |

#### Tags e Segmentação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `tags` | Array[String] | Não | Tags da vaga |
| `target_audience` | String(500) | Não | Público-alvo |
| `target_sector` | String(255) | Não | Setor alvo (Fintechs, Bancos) |
| `target_segment` | String(255) | Não | Segmento (Meios de Pagamento) |

#### Métricas e Analytics

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `nps` | Integer | Não | NPS da vaga |
| `funnel_data` | JSON | Não | `{total, screening, interview, ...}` |
| `lia_metrics` | JSON | Não | `{pipeline_lia, triagens_agendadas, ...}` |
| `view_count` | Integer | Não | Visualizações da página pública |

#### Configurações LIA

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `governance_rules` | JSON | Não | Regras de autonomia da LIA |
| `screening_config` | JSON | Não | `{channels, settings, metrics, scheduling}` |
| `eligibility_questions` | JSON | Não | Perguntas eliminatórias |
| `timeline` | JSON | Não | Cronograma calculado |
| `next_actions` | Array[String] | Não | Próximas ações |

#### Timestamps

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `created_at` | DateTime | Sim | Data de criação |
| `updated_at` | DateTime | Sim | Última atualização |
| `published_at` | DateTime | Não | Data de publicação |
| `closed_at` | DateTime | Não | Data de fechamento |

---

### Tabela: `job_vacancy_interview_stages`

> **Arquivo:** `lia-agent-system/app/models/job_vacancy.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `job_vacancy_id` | UUID (FK) | Sim | Referência à vaga |
| `stage_name` | String(100) | Sim | Nome do estágio |
| `stage_order` | Integer | Sim | Ordem no processo |
| `interviewers` | Array[String] | Não | Entrevistadores |
| `format` | String(100) | Não | Comportamental, Técnica, Cultural |
| `duration` | Integer | Não | Duração em minutos |
| `scheduling_window` | String(255) | Não | Janela de agendamento |
| `has_script` | Boolean | Não | Tem roteiro |
| `script_url` | String(500) | Não | URL do roteiro |

---

## 2. CANDIDATOS (Candidate)

### Tabela: `candidates`

> **Arquivo:** `lia-agent-system/app/models/candidate.py`

#### Identificação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `name` | String(255) | Sim | Nome completo |
| `email` | String(255) | Não | Email principal |
| `secondary_email` | String(255) | Não | Email secundário |
| `phone` | String(50) | Não | Telefone |
| `mobile_phone` | String(50) | Não | Celular |
| `secondary_phone` | String(50) | Não | Telefone secundário |

#### Perfil Online

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `linkedin_url` | String(500) | Não | URL LinkedIn |
| `github_url` | String(500) | Não | URL GitHub |
| `portfolio_url` | String(500) | Não | URL Portfólio |
| `avatar_url` | String(500) | Não | URL da foto |

#### Dados Pessoais

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `date_of_birth` | Date | Não | Data de nascimento |
| `gender` | String(50) | Não | Gênero |
| `nationality` | String(100) | Não | Nacionalidade |
| `marital_status` | String(50) | Não | Estado civil |
| `cpf` | String(14) | Não | CPF |

#### Perfil Profissional

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `current_title` | String(255) | Não | Cargo atual |
| `current_company` | String(255) | Não | Empresa atual |
| `seniority_level` | String(50) | Não | Nível de senioridade |
| `years_of_experience` | Integer | Não | Anos de experiência |
| `self_introduction` | Text | Não | Auto-apresentação |

#### Skills e Competências

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `technical_skills` | Array[String] | Não | Skills técnicas |
| `soft_skills` | Array[String] | Não | Soft skills |
| `languages` | JSON | Não | Idiomas e níveis |
| `certifications` | Array[String] | Não | Certificações |
| `interests` | Array[String] | Não | Interesses |

#### Localização

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `location_city` | String(100) | Não | Cidade |
| `location_state` | String(100) | Não | Estado |
| `location_country` | String(100) | Não | País |
| `address_street` | String(255) | Não | Rua |
| `address_number` | String(20) | Não | Número |
| `address_district` | String(100) | Não | Bairro |
| `address_zip` | String(20) | Não | CEP |
| `timezone` | String(50) | Não | Fuso horário |

#### Preferências de Trabalho

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `is_remote` | Boolean | Não | Aceita remoto |
| `willing_to_relocate` | Boolean | Não | Aceita mudança |
| `mobility` | Boolean | Não | Disponível para viagens |
| `work_model_preference` | String(50) | Não | Preferência de modelo |
| `contract_type_preference` | String(50) | Não | Preferência de contrato |

#### Salário

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `current_salary` | Float | Não | Salário atual |
| `salary_currency` | String(10) | Não | Moeda |
| `desired_salary_min` | Float | Não | Pretensão mínima |
| `desired_salary_max` | Float | Não | Pretensão máxima |
| `salary_expectation_clt` | Float | Não | Expectativa CLT |
| `salary_expectation_pj` | Float | Não | Expectativa PJ |

#### Currículo

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `resume_url` | String(500) | Não | URL do CV |
| `resume_text` | Text | Não | Texto extraído do CV |
| `cover_letter` | Text | Não | Carta de apresentação |

#### Fonte e Integração

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `source` | String(50) | Sim | Origem (ats, manual, pearch) |
| `ats_source_name` | String(100) | Não | Nome do ATS |
| `ats_candidate_id` | String(255) | Não | ID no ATS |
| `pearch_profile_id` | String(255) | Não | ID no Pearch |

#### Dados Pearch (Busca Global)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `is_open_to_work` | Boolean | Não | Aberto a oportunidades |
| `is_decision_maker` | Boolean | Não | Tomador de decisão |
| `headline` | String(500) | Não | Headline LinkedIn |
| `expertise` | Array[String] | Não | Áreas de expertise |
| `linkedin_followers_count` | Integer | Não | Seguidores LinkedIn |
| `pearch_insights` | JSON | Não | Insights do Pearch |
| `best_personal_email` | String(255) | Não | Melhor email pessoal |
| `best_business_email` | String(255) | Não | Melhor email corporativo |

#### Insights LIA

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `lia_score` | Float | Não | Score geral LIA |
| `lia_insights` | JSON | Não | Insights gerados pela LIA |
| `skills_match_percentage` | Float | Não | % de match de skills |

#### Status

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `status` | String(50) | Sim | new, active, inactive |
| `is_active` | Boolean | Sim | Ativo no sistema |
| `is_blacklisted` | Boolean | Não | Na blacklist |
| `blacklist_reason` | Text | Não | Motivo da blacklist |

#### Comunicação

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `preferred_contact_method` | String(50) | Não | Método preferido |
| `best_time_to_contact` | String(100) | Não | Melhor horário |
| `communication_consent` | Boolean | Não | Consentimento |

#### Timestamps

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `created_at` | DateTime | Sim | Data de criação |
| `updated_at` | DateTime | Sim | Última atualização |
| `last_contacted_at` | DateTime | Não | Último contato |
| `last_activity_at` | DateTime | Não | Última atividade |

---

### Tabela: `candidate_experiences`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `candidate_id` | UUID (FK) | Sim | Referência ao candidato |
| `company_name` | String(255) | Sim | Nome da empresa |
| `title` | String(255) | Não | Cargo |
| `start_date` | String(50) | Não | Data início |
| `end_date` | String(50) | Não | Data fim |
| `duration_years` | Float | Não | Duração em anos |
| `is_current` | Boolean | Não | Emprego atual |
| `description` | Text | Não | Descrição |
| `industries` | Array[String] | Não | Indústrias |
| `technologies` | Array[String] | Não | Tecnologias |
| `is_startup` | Boolean | Não | É startup |
| `funding_stage` | String(50) | Não | Estágio de funding |

---

### Tabela: `candidate_education`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `candidate_id` | UUID (FK) | Sim | Referência ao candidato |
| `institution` | String(255) | Sim | Instituição |
| `degree` | String(100) | Não | Grau (Bacharelado, MBA) |
| `field_of_study` | String(255) | Não | Área de estudo |
| `start_date` | String(50) | Não | Data início |
| `end_date` | String(50) | Não | Data fim |
| `is_completed` | Boolean | Não | Concluído |
| `institution_tier` | String(50) | Não | Tier da instituição |

---

## 3. RELACIONAMENTO VAGA-CANDIDATO

### Tabela: `vacancy_candidates`

> **Arquivo:** `lia-agent-system/app/models/candidate.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `vacancy_id` | UUID (FK) | Sim | Referência à vaga |
| `candidate_id` | UUID (FK) | Sim | Referência ao candidato |
| `company_id` | String(255) | Sim | ID da empresa |
| `source` | String(50) | Sim | Origem (local, pearch) |
| `lia_score` | Float | Não | Score LIA para esta vaga |
| `match_percentage` | Float | Não | % de match |
| `status` | String(50) | Sim | sourced, screening, interview... |
| `stage` | String(50) | Sim | Estágio atual no pipeline |
| `added_by` | String(255) | Não | Quem adicionou |
| `notes` | Text | Não | Observações |
| `additional_data` | JSON | Não | Dados extras |

**Constraint:** `UNIQUE(vacancy_id, candidate_id)`

---

### Tabela: `candidate_favorites`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `candidate_id` | String(255) | Sim | ID do candidato |
| `user_id` | String(255) | Sim | ID do usuário |
| `company_id` | String(255) | Sim | ID da empresa |
| `note` | Text | Não | Nota |
| `is_pinned` | Boolean | Não | Fixado |

---

### Tabela: `viewed_candidates`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `candidate_id` | String(255) | Sim | ID do candidato |
| `user_id` | String(255) | Sim | ID do usuário |
| `viewed_at` | DateTime | Sim | Data da visualização |
| `source` | String(50) | Não | Origem |

---

## 4. PIPELINE E ESTÁGIOS

### Tabela: `recruitment_stages`

> **Arquivo:** `lia-agent-system/app/models/recruitment_stages.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `company_id` | String(255) | Sim | ID da empresa |
| `name` | String(100) | Sim | Nome técnico |
| `display_name` | String(100) | Sim | Nome de exibição |
| `description` | Text | Não | Descrição |
| `stage_order` | Integer | Sim | Ordem no pipeline |
| `color` | String(20) | Não | Cor (hex) |
| `icon` | String(50) | Não | Ícone |
| `stage_type` | String(50) | Sim | active, final, rejection |
| `is_initial` | Boolean | Não | É estágio inicial |
| `is_final` | Boolean | Não | É estágio final |
| `is_rejection` | Boolean | Não | É reprovação |
| `is_hired` | Boolean | Não | É contratação |
| `allowed_transitions` | JSON | Não | Transições permitidas |
| `auto_advance_rules` | JSON | Não | Regras de avanço automático |
| `sla_hours` | Integer | Não | SLA em horas |
| `is_active` | Boolean | Sim | Ativo |
| `is_system` | Boolean | Não | Estágio do sistema |

---

## 5. TRIAGEM POR VOZ (WSI)

### Tabela: `voice_screening_calls`

> **Arquivo:** `lia-agent-system/app/models/voice_screening.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `call_id` | String(255) | Sim | ID OpenMic.ai |
| `agent_id` | String(255) | Não | ID do agente |
| `call_type` | String(50) | Sim | outbound, inbound |
| `call_status` | String(50) | Sim | completed, failed, in_progress |
| `from_number` | String(50) | Não | Número origem |
| `to_number` | String(50) | Não | Número destino |
| `start_timestamp` | DateTime | Não | Início da chamada |
| `end_timestamp` | DateTime | Não | Fim da chamada |
| `duration_seconds` | Integer | Não | Duração em segundos |
| `candidate_name` | String(255) | Sim | Nome do candidato |
| `candidate_id` | String(255) | Não | ID do candidato |
| `job_title` | String(500) | Sim | Título da vaga |
| `transcript` | Text | Não | Transcrição completa |
| `transcript_object` | JSON | Não | Transcrição estruturada |
| `processing_status` | String(50) | Sim | pending, analyzing, completed |
| `is_analyzed` | Boolean | Não | Foi analisado |

---

### Tabela: `voice_screening_analyses`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `screening_call_id` | UUID (FK) | Sim | Referência à chamada |
| `analysis_model` | String(100) | Não | Modelo usado (claude, gemini) |
| `tech_skills_mentioned` | JSON | Não | Skills mencionadas |
| `tech_skills_matched` | JSON | Não | Skills que batem |
| `tech_skills_missing` | JSON | Não | Skills faltantes |
| `tech_score` | Integer | Não | Score técnico (0-100) |
| `comm_clarity` | String(20) | Não | Clareza (baixa/média/alta) |
| `comm_confidence` | String(20) | Não | Confiança |
| `comm_score` | Integer | Não | Score comunicação (0-100) |
| `fit_motivation` | Text | Não | Motivação |
| `fit_red_flags` | JSON | Não | Red flags |
| `fit_green_flags` | JSON | Não | Green flags |
| `fit_score` | Integer | Não | Score fit (0-100) |

---

## 6. PARECERES LIA

### Tabela: `lia_opinions`

> **Arquivo:** `lia-agent-system/app/models/lia_opinion.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `candidate_id` | UUID (FK) | Sim | Referência ao candidato |
| `job_vacancy_id` | UUID (FK) | Não | Referência à vaga (se WSI) |
| `opinion_type` | String(50) | Sim | general, wsi |
| `source` | String(50) | Sim | cv_analysis, voice_screening, etc |
| `score` | Float | Não | Score geral (0-100) |
| `wsi_score` | Float | Não | Score WSI (0-100) |
| `recommendation` | String(50) | Não | approved, pending_review, not_approved |
| `summary` | Text | Não | Resumo do parecer |
| `archetype` | String(100) | Não | Arquétipo identificado |
| `score_breakdown` | JSON | Não | Detalhamento do score |
| `technical_analysis` | JSON | Não | Análise técnica |
| `behavioral_analysis` | JSON | Não | Análise comportamental |
| `cultural_fit` | JSON | Não | Fit cultural |
| `strengths` | JSON | Não | Pontos fortes |
| `concerns` | JSON | Não | Preocupações |
| `gaps` | JSON | Não | Gaps identificados |
| `matched_skills` | JSON | Não | Skills que batem |
| `missing_skills` | JSON | Não | Skills faltantes |
| `next_steps` | Text | Não | Próximos passos |
| `recruiter_notes` | Text | Não | Notas do recrutador |
| `recruiter_override` | String(50) | Não | Override do recrutador |
| `recruiter_override_reason` | Text | Não | Motivo do override |
| `is_current` | Boolean | Sim | Versão atual |
| `version` | Integer | Sim | Número da versão |

---

## 7. CALIBRAÇÃO E FEEDBACK

### Tabela: `calibration_feedback`

> **Arquivo:** `lia-agent-system/app/models/calibration.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | String | Sim | Chave primária |
| `vacancy_id` | String | Não | ID da vaga |
| `search_session_id` | String | Não | ID da sessão de busca |
| `candidate_id` | String | Sim | ID do candidato |
| `user_id` | String | Sim | ID do usuário |
| `feedback` | String | Sim | like, dislike, neutral |
| `reason` | String | Não | Motivo do feedback |
| `candidate_snapshot` | JSON | Não | Snapshot do candidato |

---

### Tabela: `calibration_sessions`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | String | Sim | Chave primária |
| `vacancy_id` | String | Não | ID da vaga |
| `user_id` | String | Sim | ID do usuário |
| `search_criteria` | JSON | Não | Critérios de busca |
| `status` | String | Sim | awaiting_feedback, learning, confirmed, completed |
| `total_shown` | Integer | Sim | Total de candidatos mostrados |
| `likes_count` | Integer | Sim | Total de likes |
| `dislikes_count` | Integer | Sim | Total de dislikes |
| `learned_criteria` | JSON | Não | Critérios aprendidos |
| `min_feedbacks_required` | Integer | Sim | Mínimo de feedbacks (default: 5) |
| `sourcing_blocked` | Boolean | Sim | Sourcing bloqueado |
| `confirmation_message` | Text | Não | Mensagem de confirmação |

---

## 8. SOLICITAÇÃO DE DADOS

### Tabela: `data_request_templates`

> **Arquivo:** `lia-agent-system/app/models/data_request.py`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Chave primária |
| `company_id` | UUID | Sim | ID da empresa |
| `name` | String(255) | Sim | Nome do template |
| `description` | Text | Não | Descrição |
| `trigger_stage` | String(100) | Não | Estágio que dispara |
| `trigger_type` | Enum | Sim | manual, automatic, stage_entry, stage_exit |
| `is_blocking` | Boolean | Não | Bloqueia avanço |
| `expiration_days` | Integer | Sim | Dias para expirar (default: 7) |
| `fields` | JSON | Não | Campos do template |
| `is_active` | Boolean | Sim | Ativo |
| `is_default` | Boolean | Não | Template padrão |

---

### Tipos de Campos Disponíveis

| Tipo | Descrição |
|------|-----------|
| `text` | Texto simples |
| `cpf` | CPF com validação |
| `cnpj` | CNPJ com validação |
| `email` | Email com validação |
| `phone` | Telefone |
| `date` | Data |
| `number` | Número |
| `currency` | Valor monetário |
| `file` | Upload de arquivo |
| `photo` | Upload de foto |
| `address` | Endereço completo |
| `select` | Seleção única |
| `multi_select` | Seleção múltipla |
| `textarea` | Texto longo |

---

## 9. COMUNICAÇÃO

### Tabelas Principais

| Tabela | Descrição |
|--------|-----------|
| `communication_history` | Histórico de comunicações |
| `email_templates` | Templates de email |
| `recruitment_email_templates` | Templates de recrutamento |
| `whatsapp_conversations` | Conversas WhatsApp |
| `message_queue` | Fila de mensagens |

---

## 10. CONFIGURAÇÕES ADMIN

### Tabelas Principais

| Tabela | Descrição |
|--------|-----------|
| `admin_settings` | Configurações gerais |
| `companies` | Dados das empresas |
| `company_benefits` | Benefícios padrão |
| `company_culture` | Cultura organizacional |
| `screening_questions` | Perguntas de triagem padrão |
| `pipeline_templates` | Templates de pipeline |
| `global_policies` | Políticas globais |
| `rubrics` | Rubricas BARS |

---

## DIAGRAMA DE RELACIONAMENTOS

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   companies     │────<│  job_vacancies   │>────│ vacancy_        │
└─────────────────┘     └──────────────────┘     │ candidates      │
                               │                  └────────┬────────┘
                               │                           │
                        ┌──────┴──────┐                    │
                        │             │                    │
               ┌────────▼────────┐    │           ┌────────▼────────┐
               │ interview_      │    │           │   candidates    │
               │ stages          │    │           └────────┬────────┘
               └─────────────────┘    │                    │
                                      │            ┌───────┴───────┐
                              ┌───────▼───────┐    │               │
                              │ recruitment_  │    │  ┌────────────▼────────┐
                              │ stages        │    │  │ candidate_          │
                              └───────────────┘    │  │ experiences         │
                                                   │  └─────────────────────┘
                              ┌────────────────────┘
                              │
                     ┌────────▼────────┐     ┌─────────────────────┐
                     │ voice_screening │────>│ voice_screening_    │
                     │ _calls          │     │ analyses            │
                     └────────┬────────┘     └─────────────────────┘
                              │
                     ┌────────▼────────┐
                     │  lia_opinions   │
                     └─────────────────┘
                              │
                     ┌────────▼────────┐
                     │ calibration_    │
                     │ feedback        │
                     └─────────────────┘
```

---

## CHANGELOG

| Data | Versão | Alteração |
|------|--------|-----------|
| 22/01/2026 | 1.0 | Criação inicial com mapeamento de 65 tabelas |
