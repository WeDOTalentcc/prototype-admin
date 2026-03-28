# Plano de Implementação — Evolução da Camada de Inteligência LIA
## Análise Cruzada: Análise Estratégica × Estado Real da Plataforma

**Versão:** 1.0 — Março 2026
**Metodologia:** CLAUDE.md (Feature Impact → Aprovação → Implementação → Auditoria)
**Skills executadas:** `/feature-impact` + `/wedo-governance`
**Prerrequisito:** Aprovação do plano antes de qualquer linha de código

---

## 1. Revelação Crítica: A Plataforma é Mais Madura do Que Parecia

A análise estratégica foi elaborada a partir de gaps funcionais. A auditoria profunda do código revelou que **a plataforma tem mais infraestrutura construída do que a análise original registrou**. Isso muda fundamentalmente o esforço de cada OPP:

### Infraestrutura Existente (descoberta na auditoria)

| Componente | Arquivo | Relevância para as OPPs |
|-----------|---------|------------------------|
| `time_in_stage` calculado | `job_vacancies.py:1016-1173` + `job_vacancy_route_service.py` | OPP-1: velocity JÁ existe parcialmente |
| `CalibrationEvent` (POST_HIRE_SUCCESS/FAILURE) | `models/calibration.py` | OPP-6: quality of hire tem hook, falta coleta |
| `CalibrationSession` + `CalibrationFeedback` | `models/calibration.py` | OPP-4: sourcing calibration JÁ modelado |
| `PromptVariant` + `ABTestResult` | `models/ab_testing.py` | OPP-4: A/B testing JÁ modelado |
| `SelfSchedulingLink` + `InterviewReminder` | `models/self_scheduling.py` | OPP-9: zero-touch scheduling 70% pronto |
| `interview_transcript_analysis_service` | `api/v1/interview_analysis.py` | OPP-5: WSI de transcrições Teams PRONTO |
| `RecruiterProfile` + `RecruiterFieldPreference` | `models/recruiter_profile.py` | OPP-2: perfil do recrutador JÁ modelado |
| `ActivityFeed` | `models/activity_feed.py` | OPP-2: feed de atividades PRONTO |
| `job_analytics_prompt_service` | `api/v1/job_analytics.py` | OPP-1: analytics de vaga com NL queries |
| `workforce_planning` CRUD | `api/v1/workforce_planning.py` | OPP-8: planejamento com CRUD básico |
| `analytics_query_tools` com `time_in_stage` | `domains/analytics/tools/` | OPP-1: velocity em ferramentas do Kanban Agent |

---

## 2. Reavaliação de Maturidade por OPP

### Escala de Maturidade Real

```
NÍVEL   SIGNIFICADO
0/5     Ausente — nada existe
1/5     Conceito — modelo/schema, sem lógica
2/5     Fundação — lógica parcial, sem exposição
3/5     Funcional básico — funciona, mas incompleto
4/5     Quase pronto — falta conexão ou UI
5/5     Completo — produção-ready
```

| OPP | Nome | Maturidade Real | O que falta |
|-----|------|----------------|-------------|
| OPP-1 | Pipeline Velocity Engine | **3/5** | Histórico benchmark, diagnóstico de causa, alertas proativos |
| OPP-2 | Recruiter Intelligence | **2/5** | Response time tracking, action backlog, reliability scoring |
| OPP-3 | Early Warning Engagement | **2/5** | EWS antecipado, contact window, nurture sequences |
| OPP-4 | Sourcing Intelligence & Memory | **2/5** | Source attribution, silver medalists, A/B de outreach ativo |
| OPP-5 | Interview Intelligence | **4/5** | Interview kit personalizado, falta wiring com vaga |
| OPP-6 | Quality of Hire | **1/5** | Survey automation, cálculo de score, retroalimentação WSI |
| OPP-7 | Workforce/Market Intelligence | **1/5** | Quase tudo falta (CRUD de plano existe, sem predição) |
| OPP-8 | Hiring Plan Intelligence | **1/5** | CRUD de plano existe, sem analytics preditivo |
| OPP-9 | Zero-Touch Scheduling | **4/5** | Model pronto, falta service layer e WhatsApp trigger |
| OPP-10 | Talent Pool Lifecycle | **2/5** | Candidate lists exist, falta lifecycle stages e re-engagement |

---

## 3. Análise de Viabilidade por OPP

---

### OPP-1 — Pipeline Velocity Engine
**Maturidade real: 3/5 | Esforço restante: BAIXO | Impacto: ALTO**

**O que já existe:**
- `avg_time_in_stage` calculado em `job_vacancies.py` (linha 1044) usando `updated_at` como proxy de entrada na etapa
- `time_in_stage` disponível nas ferramentas do Kanban Agent (`analytics_query_tools.py:1265-1289`)
- `check_sla` no JobsManagement Agent — verifica vagas com SLA vencido
- `analyze_bottlenecks` no JobsManagement Agent

**O que falta:**
1. **Benchmark histórico**: o `avg_time_in_stage` é calculado por vaga, mas não há comparação com histórico da empresa ou de mercado para dizer "esta etapa está 40% mais lenta que o normal"
2. **Diagnóstico de causa**: quando há gargalo, não há drill-down para identificar "candidatos parados aguardando feedback do entrevistador X"
3. **Alerta proativo no ProactiveWorker**: não há check específico de "candidato na mesma etapa por N dias" com causa
4. **stage_entered_at**: `updated_at` é proxy impreciso — se há qualquer update na linha, o timer reinicia. Falta campo dedicado

**Gap técnico crítico:** `vacancy_candidates.updated_at` é usado como proxy de tempo na etapa, mas é impreciso porque qualquer UPDATE (adicionar nota, mudar campo) reinicia o contador. Precisamos de `stage_entered_at`.

**Viabilidade:** ALTA — os dados existem, falta precisão e lógica de comparação histórica.

**Pré-condições de implementação:**
- Migration para adicionar `stage_entered_at` a `vacancy_candidates`
- Trigger/hook para popular `stage_entered_at` quando `stage` muda
- `PipelineVelocityService` — computa benchmark histórico por empresa e por role category
- Novo check no `ProactiveAgentWorker`: `check_stage_velocity`
- Exposição via ferramenta no Kanban Agent e JobsManagement Agent

**Governance check (5 perguntas):**
1. É justo? → Sim — métrica de processo, não avalia candidato
2. É necessário? → Sim — diretamente reduz TTF
3. É transparente? → Sim — dados operacionais do recrutador
4. Conseguimos medir? → Sim — TTF delta antes/depois
5. É resiliente? → Sim — query pode falhar graciosamente com fallback

**Feature Impact (12 dimensões):**
| Dimensão | Impacto | O que fazer |
|----------|---------|-------------|
| Backend API | Médio | Novos endpoints `/pipeline-velocity/{job_id}` e `/pipeline-velocity/benchmark/{company_id}` |
| Backend Services | Alto | `PipelineVelocityService` novo |
| Banco de Dados | Alto | Migration: `stage_entered_at` em `vacancy_candidates`, índice composto |
| Agentes IA | Médio | Novo tool `get_velocity_insights` no Kanban Agent e JobsManagement |
| Automações | Médio | Novo check `check_stage_velocity` no ProactiveAgentWorker |
| Observabilidade | Baixo | Log do check e alert |
| Segurança | Baixo | `company_id` em todas as queries de benchmark |
| Frontend | Baixo | Não requer UI nova — surfaça via chat e Daily Briefing |

---

### OPP-9 — Zero-Touch Scheduling
**Maturidade real: 4/5 | Esforço restante: BAIXO-MÉDIO | Impacto: ALTO**

**Este é o OPP com maior relação esforço/impacto da lista. O model está pronto, o API de scheduling existe, Microsoft Graph está configurado.**

**O que já existe:**
- `SelfSchedulingLink` — modelo completo com token, slots, expiração, histórico de reagendamentos
- `InterviewReminder` — lembretes por canal configurável
- `RescheduleHistory` — auditoria de reagendamentos
- `api/v1/scheduling.py` — endpoints de scheduling
- `microsoft_graph.py` — integração calendar
- `WhatsApp` — integração Twilio configurada

**O que falta:**
1. **Gatilho automático após transição para "Entrevista"**: quando candidato é movido para stage de entrevista, a LIA deveria automaticamente gerar um `SelfSchedulingLink` e enviar por WhatsApp
2. **Service layer de orquestração**: conectar transição de etapa → geração de link → envio WhatsApp → criação de convite Calendar → registro de presença
3. **Handling de confirmação**: quando candidato escolhe slot, criar Interview record, enviar convite para todos, notificar recrutador
4. **Fallback manual**: se candidato não agendar em X dias, alertar recrutador

**Viabilidade:** MUITO ALTA — 70% do código existe. Falta principalmente o "glue" entre os componentes.

**Pré-condições de implementação:**
- `ZeroTouchSchedulingService` — orquestrador que conecta os modelos existentes
- Hook no `PipelineTransitionAgent` — quando `stage = interview_*`, triggerar scheduling
- Automação no `AutomationTriggerService` — "candidato em etapa de entrevista há 2 dias sem agenda" → reenviar convite
- Compatibilidade com calendários do interviewer via Microsoft Graph

**Governance check:**
1. É justo? → Sim — processo, não avaliação
2. É necessário? → Sim — elimina carga administrativa mais repetitiva do recrutador
3. É transparente? → Sim — candidato recebe link explícito para auto-agendar
4. Conseguimos medir? → Sim — taxa de auto-agendamento vs. manual
5. É resiliente? → Sim — fallback para agendamento manual se link expira

---

### OPP-5 — Interview Intelligence
**Maturidade real: 4/5 | Esforço restante: BAIXO | Impacto: ALTO**

**O que já existe:**
- `interview_transcript_analysis_service` — WSI completo de transcrições Teams
- `teams_webhook` — recebe notificação quando transcrição fica disponível
- `LiaOpinion` — armazena resultado com Bloom, Dreyfus, Big Five, score normalizado
- `CalibrationEvent` com `FeedbackType` para tracking de concordância/discordância do recrutador
- `InterviewReminder` — lembretes configuráveis

**O que falta:**
1. **Interview Kit personalizado**: LIA sabe o perfil do candidato (WSI, CV) + a vaga (competências). Falta gerar automaticamente um "kit de entrevista" para o entrevistador (perguntas personalizadas, contexto do candidato, pontos de atenção)
2. **Reliability scoring**: `CalibrationEvent` registra quando o recrutador discorda do score LIA. Falta computar "entrevistador que sempre dá scores fora da média" — os dados existem, falta o serviço de cálculo
3. **Tempo de feedback**: `InterviewReminder` existe mas só lembra do horário, não do feedback pós-entrevista

**Viabilidade:** MUITO ALTA — falta principalmente o "kit" e o cálculo de reliability usando dados já disponíveis.

**Pré-condições:**
- Tool `generate_interview_kit` no Pipeline Agent — usa perfil do candidato + competências da vaga + LLM
- `InterviewerReliabilityService` — agrega `CalibrationEvent` por usuário e detecta outliers
- Novo tipo de `InterviewReminder`: "feedback_due" (4h após entrevista)

---

### OPP-4 — Sourcing Intelligence & Memory
**Maturidade real: 2/5 | Esforço restante: MÉDIO | Impacto: ALTO**

**O que já existe:**
- `CalibrationSession` + `CalibrationFeedback` — sistema de like/dislike em buscas, aprende critérios
- `PromptVariant` + `ABTestResult` — A/B testing modelado
- `SharedSearch` — buscas salvas
- `SearchFeedback` (model existe) — feedback em resultados de busca

**O que falta:**
1. **Source attribution**: não há rastreamento de qual canal gerou cada candidato até a contratação. Precisa ligar `sourcing_channel` em `vacancy_candidates` com o resultado final
2. **Silver Medalists proativo**: candidatos que chegaram a entrevista sem ser contratados não são proativamente sugeridos para vagas similares. Os dados existem — falta a lógica de sugestão
3. **A/B testing ativo para mensagens outreach**: o modelo existe mas não há nenhum uso atual dele para testar variações de mensagens
4. **Skills Adjacency**: não existe nenhum componente de adjacência/transferabilidade de skills

**Viabilidade:** MÉDIA — calibração existe, attribution e silver medalists precisam de lógica nova, skills adjacency é componente novo.

**Decisão de escopo:** dividir em 2 partes:
- **Parte A (Onda 1):** Silver Medalists proativo — usa apenas queries em dados existentes
- **Parte B (Onda 2):** Source attribution + skills adjacency — requer novo campo + modelo de similaridade

---

### OPP-2 — Recruiter Intelligence
**Maturidade real: 2/5 | Esforço restante: MÉDIO | Impacto: ALTO**

**O que já existe:**
- `RecruiterProfile` — `total_jobs_created`, `total_corrections_made`, `avg_completion_time_seconds`
- `RecruiterFieldPreference` — padrão de correções por campo
- `ActivityFeed` — feed de atividades com actor tracking
- `communication_logs` — histórico de mensagens com timestamps

**O que falta:**
1. **Response time por recrutador**: `communication_logs` tem timestamps, mas não há cálculo de "tempo entre candidato na etapa e primeiro contato pelo recrutador"
2. **Action Backlog**: não há visão consolidada de "candidatos aguardando ação do recrutador X, ordenados por urgência"
3. **Reliability de entrevistadores**: precisa do `InterviewerReliabilityService` (dependência de OPP-5)
4. **Dashboard de gestão**: não há endpoint dedicado de métricas de produtividade do recrutador

**Viabilidade:** MÉDIA — dados existem dispersos, falta agregação e exposição.

**Pré-condições:**
- `RecruiterMetricsService` — agrega dados de `communication_logs`, `vacancy_candidates`, `interviews` por recruiter
- Novo endpoint `GET /api/v1/recruiter-metrics/{recruiter_id}`
- Nova tool no Daily Briefing: "você tem X candidatos aguardando ação"

---

### OPP-6 — Quality of Hire
**Maturidade real: 1/5 | Esforço restante: ALTO | Impacto: MUITO ALTO (longo prazo)**

**O que já existe:**
- `CalibrationEvent.feedback_type` = `POST_HIRE_SUCCESS` / `POST_HIRE_FAILURE` — o hook existe!
- `JobOutcome` model com `outcome_type`, `time_to_fill_days`
- `FeedbackType` enum contempla pós-contratação

**O que falta (quase tudo):**
1. **Coleta automática**: nada dispara um survey 30/90 dias após contratação
2. **Quality of Hire Score**: nenhum cálculo de score composto existe
3. **Retroalimentação do WSI**: nenhuma correlação WSI score × performance pós-hire
4. **Integração com HRIS**: sem dados de performance pós-hire, a LIA não pode fechar o loop

**Decisão estratégica:** OPP-6 depende de dados que só existirão 90+ dias após implementação. É o investimento com maior ROI de longo prazo, mas resultado visível mais lento.

**Abordagem recomendada:** implementar coleta agora (survey 30/90 dias) para ter dados disponíveis em 3-6 meses. Correlação WSI só em Onda 3.

**Viabilidade:** BAIXA no curto prazo (dados precisam acumular), ALTA no médio prazo.

---

### OPP-3 — Engajamento Preditivo Antecipado
**Maturidade real: 2/5 | Esforço restante: MÉDIO | Impacto: ALTO**

**O que já existe:**
- `predict_dropout_risk` — 4 fatores, funciona, mas detecta risco já materializado (10+ dias)
- `check_engagement_gaps` no ProactiveWorker — candidatos sem contato há 10+ dias
- `AutomationTriggerService` — 7 triggers configurados

**O que falta:**
1. **Thresholds por etapa**: hoje é universal "10 dias". Offer deveria ser 2 dias, Screening 5 dias
2. **Early Warning Score**: detectar declínio ANTES dos 10 dias (velocidade de resposta caindo, emails não abertos)
3. **Optimal contact window**: não há tracking de horário/dia de melhor resposta por candidato
4. **Sequências de nurture**: os triggers existem mas são simples (um evento). Falta sequência "se não respondeu → 3 dias → diferente canal"

**Viabilidade:** MÉDIA — lógica nova de EWS, thresholds por etapa são simples de adicionar.

---

### OPP-7 e OPP-8 — Market Intelligence + Hiring Plan Intelligence
**Maturidade real: 1/5 | Esforço restante: MUITO ALTO | Impacto: ALTO (longo prazo)**

**O que existe:** apenas o CRUD básico de workforce plan. Sem predição, sem inteligência de mercado.

**Decisão estratégica:** depende de:
1. Volume de dados interno suficiente (mínimo 12 meses de histórico)
2. Integração com fonte de dados externa de mercado (Pearch API signals)
3. Integração com HRIS do cliente (para dados de turnover reais)

**Recomendação:** adiar para Onda 3. Implementar coleta de dados agora para que, em 6-12 meses, haja volume suficiente para predição.

---

### OPP-10 — Talent Pool Lifecycle
**Maturidade real: 2/5 | Esforço restante: MÉDIO | Impacto: MÉDIO**

**O que existe:** `CandidateList`, candidate lists, proactive check de engagement gaps.

**O que falta:** lifecycle stages (silver_medalist → active → warm → cold), re-engagement sequences automatizadas, internal mobility (para clientes com módulo de funcionários).

**Viabilidade:** MÉDIA — silver medalists é de alta prioridade e baixo esforço. Lifecycle completo é Onda 2.

---

## 4. `/feature-impact` — Análise das 12 Dimensões para Cada Onda

### Onda 1 — Análise de Impacto

**Conjunto de features da Onda 1:**
- OPP-1: Pipeline Velocity Engine (completo)
- OPP-9: Zero-Touch Scheduling (service layer)
- OPP-5: Interview Kit + Reliability (partial)
- OPP-4A: Silver Medalists proativo
- OPP-1B: Action Backlog no Daily Briefing

| Dimensão | Impacto | Ações necessárias |
|----------|---------|------------------|
| **Frontend** | Baixo | Sem novas páginas — tudo surfaça via chat e Daily Briefing. Possível widget de "candidatos aguardando ação" no Painel |
| **Backend API** | Médio | 4-5 novos endpoints: `/pipeline-velocity/`, `/recruiter-metrics/`, `/silver-medalists/`, `/self-scheduling/trigger` |
| **Backend Services** | Alto | 4 novos serviços: `PipelineVelocityService`, `ZeroTouchSchedulingService`, `SilverMedalistService`, `InterviewKitService` |
| **Banco de Dados** | Médio | 1 migration crítica: adicionar `stage_entered_at` a `vacancy_candidates`. Índice composto `(vacancy_id, stage, stage_entered_at)` |
| **Agentes IA** | Médio | 3 novas tools: `get_velocity_insights` (Kanban+JobsMgmt), `get_silver_medalists` (Talent+Sourcing), `generate_interview_kit` (Pipeline) |
| **Comunicações** | Médio | Novo trigger WhatsApp para auto-scheduling. Novo reminder tipo "feedback_due" |
| **Integrações** | Médio | Microsoft Graph para criar eventos de calendar automaticamente (já configurado) |
| **Compliance LGPD** | Baixo | `stage_entered_at` não é PII. Silver medalists = dados já coletados com consentimento |
| **Segurança** | Médio | `company_id` em todas as queries de velocity benchmark. `SelfSchedulingLink.token` com expiração |
| **Infraestrutura** | Baixo | Celery para envio de lembretes de scheduling. Sem mudanças em Redis ou RabbitMQ |
| **Observabilidade** | Baixo | Log de velocity checks, scheduling triggers, silver medalist suggestions |
| **Testes** | Médio | Unit: velocity calculation, scheduling orchestration, silver medalist query. Integration: company_id isolation |

**Onda 1 — Pronto para implementar:** SIM, com aprovação

---

### Onda 2 — Análise de Impacto (planejamento antecipado)

**Conjunto:** OPP-2 (Recruiter Intelligence full), OPP-3 (EWS), OPP-4B (Source Attribution), OPP-10 (Pool Lifecycle)

| Dimensão | Impacto | Ações necessárias |
|----------|---------|------------------|
| **Frontend** | Médio | Dashboard de métricas do recrutador (gestor de equipe). Requer aprovação de design |
| **Backend API** | Médio | `RecruiterMetricsService`, EWS endpoint, source attribution endpoints |
| **Banco de Dados** | Médio | `sourcing_channel` em `vacancy_candidates`, `candidate_lifecycle_stage` em `candidate_list_members` |
| **Agentes IA** | Alto | EWS integrado ao ProactiveWorker, sourcing memory nas buscas |
| **Comunicações** | Alto | Nurture sequences automatizadas — requer estado de sequência por candidato |
| **Compliance** | Médio | Source tracking pode gerar dados de comportamento do candidato — verificar consentimento |

**Onda 2 — Pronto para implementar:** PARCIALMENTE — aguarda dados de Onda 1 acumulados

---

### Onda 3 — Análise de Impacto (visão de longo prazo)

**Conjunto:** OPP-6 (Quality of Hire full), OPP-7 (Market Intelligence), OPP-8 (Hiring Plan)

| Dimensão | Impacto |
|----------|---------|
| **Backend** | Muito Alto — integração HRIS, análise de correlação WSI × performance |
| **Banco de Dados** | Alto — modelo de quality of hire, tabela de performance pós-hire |
| **IA/ML** | Muito Alto — modelo de correlação, market intelligence |
| **Compliance** | Alto — dados de performance são PII sensível, requer consentimento explícito |
| **Integrações** | Alto — HRIS externo (ADP, Workday, Gupy), Pearch market signals |

**Onda 3 — Pronto para implementar:** NÃO — depende de dados acumulados de Onda 1 e 2

---

## 5. `/wedo-governance` — Verificação das 13 Crenças e 8 Inegociáveis

### Checklist por Feature (Onda 1)

| Crença | OPP-1 Velocity | OPP-9 Scheduling | OPP-5 Kit | OPP-4A Silver |
|--------|---------------|-----------------|-----------|---------------|
| 01 Humano em Primeiro Lugar | ✅ Alerta sugere, recrutador decide | ✅ Candidato confirma slot, recrutador vê | ✅ Kit orienta, entrevistador decide | ✅ LIA sugere, recrutador contata |
| 02 Justo/Não-discriminatório | ✅ Métrica de processo | ✅ Processo neutro | ⚠️ FairnessGuard no kit gerado | ✅ Baseado em score anterior |
| 03 Transparente | ✅ Dados operacionais | ✅ Candidato sabe o processo | ✅ Entrevistador vê fonte | ✅ "Candidato avaliado anteriormente" |
| 04 Seguro/Privacidade | ✅ `stage_entered_at` não é PII | ✅ Token com expiração, sem PII exposto | ✅ Dados internos | ✅ Dados com consentimento |
| 07 Resiliente | ✅ Fallback: sem velocity, sem alerta | ✅ Fallback: agendamento manual | ✅ Fallback: sem kit, entrevista normal | ✅ Fallback: não sugerir |
| 10 Inteligência vs Determinismo | ✅ Sugere, não age | ✅ Candidate escolhe slot | ✅ Kit é orientação | ✅ Sugestão, não ação automática |
| 12 Autonomia Progressiva | ✅ Recrutador ativa | ✅ Opt-in por vaga | ✅ Opcional | ✅ Sugestão proativa |

### 8 Inegociáveis — Onda 1

| Inegociável | Status |
|-------------|--------|
| 1. Nenhum candidato rankeado sem WSI explicitável | ✅ Silver medalists já têm score anterior |
| 2. Nenhuma rejeição automática | ✅ Nenhuma feature rejeita automaticamente |
| 3. FairnessGuard em screening/ranking | ✅ Interview Kit precisa de FairnessGuard Layer 1+2 na geração de perguntas |
| 4. PII masking nos logs | ✅ `stage_entered_at` é timestamp, sem PII |
| 5. Consent antes de processamento | ✅ Dados já coletados com consentimento existente |
| 6. Dados deletados quando solicitado | ✅ `stage_entered_at` incluso no scope de deleção |
| 7. Human override sempre disponível | ✅ Todas as OPPs têm fallback manual |
| 8. WCAG 2.1 AA | ✅ Surfaça via chat (sem nova UI em Onda 1) |

**Resultado governance:** APROVADO para Onda 1. OPP-5 (Interview Kit) requer validação de FairnessGuard na geração de perguntas.

---

## 6. Plano de Implementação Detalhado

### Onda 1 — "Conectar o que existe" (4-6 semanas)

**Meta:** surfaçar dados que já existem, conectar componentes isolados, alto impacto com baixo risco.

---

#### Sprint 1A — Pipeline Velocity Engine (1 semana)

**Bloqueante:** migration `stage_entered_at`

```
Sequência obrigatória:
1. Migration: ALTER TABLE vacancy_candidates ADD COLUMN stage_entered_at TIMESTAMP
2. Backfill: UPDATE vacancy_candidates SET stage_entered_at = updated_at (aproximação inicial)
3. Hook na transição de stage: sempre que stage muda → stage_entered_at = NOW()
4. PipelineVelocityService:
   - get_stage_velocity(vacancy_id) → dias em cada etapa
   - get_company_benchmark(company_id, role_category) → mediana histórica
   - get_bottleneck_analysis(vacancy_id) → etapa mais lenta vs. benchmark
5. Novo check ProactiveWorker: check_stage_velocity(company_id)
   - Detecta candidatos em etapa > 1.5x a mediana histórica
   - Identifica "possível causa" (última ação foi de qual usuário?)
6. Tool get_velocity_insights nos agentes Kanban e JobsManagement
7. Integração no Daily Briefing: "3 vagas com gargalo identificado"
```

**Dependências externas:** nenhuma
**Risco:** BAIXO — migration não-destrutiva (ADD COLUMN)
**Rollback:** desativar o check no ProactiveWorker, a migration permanece

---

#### Sprint 1B — Zero-Touch Scheduling (1 semana)

**Bloqueante:** nenhum — SelfSchedulingLink já está modelado

```
Sequência:
1. ZeroTouchSchedulingService:
   - generate_scheduling_link(candidate, vacancy, interviewer_emails, duration)
   - send_scheduling_whatsapp(candidate_id, link) → usa canal WhatsApp existente
   - on_slot_selected(token, selected_slot):
       → criar Interview record
       → criar evento Microsoft Graph para todos os participantes
       → enviar confirmação ao candidato
       → notificar recrutador (Bell + Teams)
       → criar InterviewReminder (24h antes e 1h antes)
2. Hook no PipelineTransitionAgent:
   Quando stage → interview_1 OU interview_2:
       → chamar ZeroTouchSchedulingService.generate_and_send()
3. Automação no AutomationTriggerService:
   Novo trigger: candidate_no_scheduling (2 dias sem agendar após link enviado)
       → reenviar link + alertar recrutador
4. Endpoint público: GET /scheduling/{token} (sem auth — candidato acessa)
5. Endpoint confirm: POST /scheduling/{token}/select-slot
```

**Dependências externas:** Microsoft Graph (configurado), Twilio WhatsApp (configurado)
**Risco:** MÉDIO — integração com calendário externo pode ter variações
**Rollback:** desativar o hook na transição de etapa, scheduling continua manual

---

#### Sprint 1C — Interview Kit + Reliability (1 semana)

**Bloqueante:** nenhum — interview_transcript_analysis_service já existe

```
Sequência:
1. InterviewKitService (novo):
   - generate_kit(candidate_id, vacancy_id, interview_type):
       → busca perfil WSI do candidato (LiaOpinion)
       → busca competências da vaga (screening_questions + rubric)
       → gera via LLM (Claude):
           * 5 perguntas STAR focadas nos gaps do candidato
           * 2 perguntas técnicas sobre skills ausentes
           * 1 pergunta de alinhamento cultural
           * Contexto do candidato: "Ponto de atenção: score baixo em liderança"
       → FairnessGuard Layer 1+2 nas perguntas geradas (obrigatório — Inegociável #3)

2. Tool generate_interview_kit no Pipeline Agent
   - Disponível no stage interview
   - Output: kit formatado para o entrevistador

3. InterviewerReliabilityService (novo):
   - compute_reliability(user_id, company_id):
       → agrega CalibrationEvent por usuário
       → calcula: score médio dado vs. mediana do time
       → calcula: % de discordâncias com LIA
       → flag: outlier se > 1.5 desvios padrão
   - Exposto no Daily Briefing para gestores

4. Lembrete de feedback pós-entrevista:
   - Novo InterviewReminder type: feedback_due
   - Enviado 4h após interview.end_time
   - Canal: Bell + WhatsApp
```

**Dependências:** LiaOpinion service, FairnessGuard
**Risco:** BAIXO-MÉDIO — LLM para kit pode gerar conteúdo inconsistente sem guardrail
**Mitigação:** FairnessGuard obrigatório + limite de tokens + temperatura baixa

---

#### Sprint 1D — Silver Medalists Proativo (3-4 dias)

**Bloqueante:** nenhum — dados existem

```
Sequência:
1. SilverMedalistService (novo):
   - get_silver_medalists(vacancy_id, company_id):
       → SELECT candidatos que:
           * chegaram a interview_1 ou posterior em vagas anteriores
           * não foram contratados (outcome != hired)
           * têm role_category compatível com a vaga atual
           * não estão ativos em outra vaga da empresa
           * WSI score >= threshold configurável (default: 70)
       → ordena por match de skills + WSI score
       → retorna top 5

2. Tool get_silver_medalists no Talent Agent e Sourcing Agent

3. Gatilho proativo no ProactiveWorker:
   check_silver_medalist_opportunities(company_id):
       → para cada vaga aberta há > 7 dias sem candidato strong
       → busca silver medalists
       → cria ProactiveAction: "Ana Silva foi shortlistada em vaga similar.
          Quer recontatar para a nova vaga?"

4. Integração no Daily Briefing: "X candidatos silver medalists disponíveis para vagas ativas"
```

**Dependências externas:** nenhuma
**Risco:** BAIXO — apenas queries em dados existentes

---

### Onda 2 — "Amplificar com Inteligência" (6-10 semanas após Onda 1)

**Pré-condição:** Onda 1 em produção e coletando dados há mínimo 4 semanas

#### Sprint 2A — Recruiter Intelligence Dashboard
```
- RecruiterMetricsService: agrega dados de communication_logs + vacancy_candidates + interviews
- Métricas: response_time_avg, candidates_awaiting, feedback_timeliness, pipeline_advance_rate
- Endpoint: GET /api/v1/recruiter-metrics/{recruiter_id}?period=week
- Action Backlog: GET /api/v1/recruiter-metrics/backlog (lista priorizada)
- Integração Daily Briefing: "Você tem 8 candidatos aguardando, mais antigo há 6 dias"
- UI: requer aprovação de design antes de implementar (CLAUDE.md rule)
```

#### Sprint 2B — Early Warning Score
```
- EarlyWarningService: computa risco de dropout com thresholds por etapa
  * Applied/Screening: 3 dias sem contato
  * Interview: 5 dias
  * Offer: 2 dias (CRÍTICO)
- Integração no ProactiveWorker: check_early_warning_score
- Upgrade do predict_dropout_risk: absorve EWS como fator adicional
- Sequências de nurture: AutomationTriggerService + 2 novos triggers encadeados
```

#### Sprint 2C — Source Attribution
```
- Migration: ADD COLUMN sourcing_channel VARCHAR(50) a vacancy_candidates
- Preenchimento no fluxo de candidatura: identifica origem (pearch, gupy, referral, manual)
- SourcingAttributionService: computa conversion por canal
- Tool no Sourcing Agent: get_source_roi
- Dashboard (requer aprovação de design)
```

#### Sprint 2D — Talent Pool Lifecycle
```
- Migration: ADD COLUMN lifecycle_stage VARCHAR(50) a candidate_list_members
  Valores: silver_medalist | active | warm | cold | archived
- Lógica de transição automática via Celery job diário
- Re-engagement sequences para warm/cold
- Internal mobility (se módulo funcionários ativo)
```

---

### Onda 3 — "Diferenciar com Dados Únicos" (12+ semanas após Onda 2)

**Pré-condição:** 6+ meses de dados de Onda 1+2 acumulados

#### Sprint 3A — Quality of Hire Loop
```
- Post-hire survey automation: Celery task dispara 30 e 90 dias após hired
- Survey via WhatsApp para hiring manager
- QualityOfHireScore: hiring_manager_satisfaction × performance × retention
- Retroalimentação do WSI: correlação score × quality (requer mínimo 50 contratações)
```

#### Sprint 3B — Market Intelligence (condicionado a dados suficientes)
```
- Talent Availability Index: usar volume de buscas no Pearch como proxy de disponibilidade
- Salary benchmark dinâmico: média de ofertas aceitas/recusadas na plataforma
- Competitive signals: vagas abertas em empresas similares (requer integração adicional)
```

#### Sprint 3C — Hiring Plan Intelligence Preditivo
```
- Análise de sazonalidade: padrões históricos de abertura de vagas
- Recruiting capacity model: vagas abertas × TTF médio × team size
- Previsão de headcount baseada em crescimento histórico
```

---

## 7. Ordem de Implementação — Decisão Final

### Prioridade por Impacto × Esforço × Maturidade Real

```
ORDEM   OPP   FEATURE                          SEMANAS   IMPACTO   MATURIDADE
─────────────────────────────────────────────────────────────────────────────
1       1A    stage_entered_at migration         0.5       Alto      3→4/5
2       1B    Pipeline Velocity Engine           1.0       Alto      3→5/5
3       9     Zero-Touch Scheduling              1.0       Alto      4→5/5
4       5     Interview Kit + Reliability        1.0       Alto      4→5/5
5       4A    Silver Medalists Proativo          0.5       Médio     2→3/5
─────────────────────────────────────────────────────────────────────────────
PAUSA: avaliar dados e ajustar (2-4 semanas em produção)
─────────────────────────────────────────────────────────────────────────────
6       2     Recruiter Intelligence             2.0       Alto      2→4/5
7       3     Early Warning Score               1.5       Alto      2→4/5
8       4B    Source Attribution                1.5       Médio     2→3/5
9       10    Talent Pool Lifecycle             2.0       Médio     2→4/5
─────────────────────────────────────────────────────────────────────────────
PAUSA: avaliar dados (6 meses de histórico mínimo)
─────────────────────────────────────────────────────────────────────────────
10      6     Quality of Hire Loop              3.0       Muito Alto 1→3/5
11      7     Market Intelligence               4.0       Alto      1→3/5
12      8     Hiring Plan Preditivo             4.0       Alto      1→3/5
─────────────────────────────────────────────────────────────────────────────
```

---

## 8. Métricas de Sucesso por Onda

### Onda 1
| Métrica | Meta 30 dias | Meta 90 dias |
|---------|-------------|-------------|
| % vagas com velocity tracking ativo | 100% | 100% |
| % entrevistas agendadas via zero-touch | 30% | 60% |
| % entrevistadores com kit gerado | 50% | 80% |
| Silver medalists sugeridos por mês (empresa) | 2-5 | 5-10 |
| TTF médio vs. baseline | -5% | -15% |
| Candidatos ghostados após entrevista agendada | baseline | -20% |

### Onda 2
| Métrica | Meta 30 dias | Meta 90 dias |
|---------|-------------|-------------|
| % recrutadores com action backlog visível | 80% | 95% |
| Tempo médio de resposta a candidatos | baseline | -25% |
| Candidatos em "early warning" antes de ghost | 0% → 40% | 60% |
| Source attribution trackeado | 20% vagas | 80% vagas |

### Onda 3
| Métrica | Meta 6 meses | Meta 12 meses |
|---------|-------------|--------------|
| Quality of hire score coletado | 50 hires | 150 hires |
| Correlação WSI × performance | calculável | +10% precisão WSI |
| Previsão de headcount ± 20% | validando | validado |

---

## 9. Dependências e Riscos

### Dependências Críticas

| Dependência | Necessária para | Status |
|-------------|----------------|--------|
| Microsoft Graph Calendar API | OPP-9 zero-touch | Configurado, não testado end-to-end |
| Twilio WhatsApp | OPP-9 envio de link | Configurado, habilitado por cliente |
| `stage_entered_at` migration | OPP-1 (todos os outros dependem) | Não existe ainda |
| FairnessGuard no Interview Kit | OPP-5 compliance | Deve ser integrado na geração |
| Acúmulo de dados (6+ meses) | Onda 3 completa | Começa a acumular após Onda 1 |

### Riscos Principais

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Backfill incorreto de stage_entered_at | Média | Médio | Aceitar imprecisão inicial, marcar como "estimated" |
| Microsoft Graph API rate limits em scheduling | Baixa | Alto | Circuit breaker + fallback manual |
| Interview Kit com perguntas tendenciosas | Média | Alto | FairnessGuard obrigatório + human review |
| Silver medalists com dados stale | Média | Baixo | Timestamp de última atividade no filtro |
| Dados insuficientes para Onda 3 | Alta | Alto | Começar coleta (surveys) na Onda 1 |

---

## 10. Próximo Passo

**Ação necessária antes de implementar:** aprovação deste plano.

**Sequência após aprovação:**

```
1. Aprovação do plano → sprint 1A imediato
2. Sprint 1A (migration + velocity) → 0.5 semana
3. Sprints 1B, 1C, 1D em paralelo → 1-1.5 semanas
4. Onda 1 em produção → monitorar 4 semanas
5. Review de métricas → decisão sobre Onda 2
```

**Estimativa total Onda 1:** 3-4 semanas (sprints podem ser parcialmente paralelos)

---

*Plano elaborado após auditoria profunda do código-fonte + análise estratégica comparativa. Aprovação necessária antes de qualquer implementação. Segue metodologia CLAUDE.md: Feature Impact → Aprovação → Código → Auditoria.*
