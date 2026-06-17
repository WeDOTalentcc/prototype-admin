# Campos que Rails precisa ganhar (Fase 2)

> Gerado automaticamente pela análise fork vs Rails.
> Estes campos existem no fork mas NÃO no Rails.
> Precisam ser adicionados ao ats_api quando autorizado.

## jobs (Rails) ← job_vacancies (Fork)

| Campo Fork | Tipo | Descrição |
|-----------|------|-----------|
| department | String(100) | Departamento da vaga |
| seniority_level | String(50) | Júnior/Pleno/Sênior/Especialista |
| employment_type | String(50) | CLT/PJ/Temporary |
| salary_range | JSON | {min, max, currency} |
| bonus_range | JSON | {min, max, currency} |
| technical_requirements | JSON array | [{category, technology, level, required}] |
| behavioral_competencies | JSON array | [{competency, weight}] |
| languages | JSON array | [{language, level, required}] |
| screening_questions | JSON array | [{id, question, type, weight}] |
| interview_stages | JSON array | [{stageName, interviewers, format, duration}] |
| organizational_structure | JSON | {directManager, teamSize, teamComposition} |
| deadline_screening | DateTime | Prazo de triagem |
| deadline_shortlist | DateTime | Data da shortlist |
| deadline_closing | DateTime | Prazo final |
| priority | String(20) | alta/média/baixa |
| urgency_level | Integer | 1-5 |
| affirmative_criteria_primary | String(50) | gender/race/disability/age/lgbtqia |
| affirmative_criteria_secondary | String(50) | Segundo critério |
| affirmative_description | Text | Descrição livre |
| is_affirmative | Boolean | Vaga afirmativa |

## candidates (Rails) ← candidates (Fork)

| Campo Fork | Tipo | Descrição |
|-----------|------|-----------|
| candidate_experiences | Tabela separada | 40+ campos por experiência |
| candidate_education | Tabela separada | Instituição, grau, campo de estudo |
| embeddings | Vector(768) | pgvector para busca semântica |
| skills | ARRAY(String) | Skills extraídas por IA |
| seniority_detected | String | Senioridade detectada por IA |
| cultural_fit | Float | Score de cultural fit |
| lia_score | Float | Score geral da LIA |
| is_pii_encrypted | Boolean | PII criptografado via Fernet |

## Novos módulos (não existem no Rails)

| Módulo | Tabelas Fork | Descrição |
|--------|-------------|-----------|
| Goals Planning | goals, planned_headcounts, hiring_plans | Planejamento de metas por depto |
| Hiring Policies | company_hiring_policies | Regras de automação de triagem |
| WSI | wsi_sessions, triagem_sessions | Work Sample Interview |
| LGPD Retention | company_retention_policies | Política de retenção por empresa |
| Billing | subscriptions, invoices, payment_methods | Stripe + Iugu/Vindi |
| Agent Studio | agent_templates | Prompts customizáveis por empresa |
| Intelligence | intelligence_insights, pattern_cache | Aprendizado por empresa |
| Communication | whatsapp_conversations, teams_conversations | Multi-canal |
| Voice | voice_screening_calls, voice_screening_analyses | Triagem por voz |
