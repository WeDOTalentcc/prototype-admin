# Plano de Evolução da Plataforma LIA — Automação Progressiva

**Versão:** 1.0  
**Data:** 21/02/2026  
**Status:** Planejamento  
**Base:** Diagnóstico arquitetural v6.2 + análise de gaps + benchmarks de mercado

---

## Visão Geral

Este plano detalha **4 fases** para evoluir a LIA de uma assistente reativa (espera comandos) para uma recrutadora inteligente proativa (monitora, aprende, sugere, age). Cada fase constrói sobre a anterior e entrega valor independente.

**Gantt do Roadmap:** [Roadmap Evolução LIA - 4 Fases](https://www.figma.com/online-whiteboard/create-diagram/6c5d6a5e-6e1c-4566-a202-c6dcd512db62?utm_source=other&utm_content=edit_in_figjam)

**Diagramas complementares:**
- [Layout Políticas de Contratação](https://www.figma.com/online-whiteboard/create-diagram/804303f5-3a26-417b-8465-731a8dbd4a50?utm_source=other&utm_content=edit_in_figjam)
- [Fluxo 19 Perguntas](https://www.figma.com/online-whiteboard/create-diagram/b9190356-1ea6-4902-ad00-adf832672f81?utm_source=other&utm_content=edit_in_figjam)
- [Arquitetura 5 Níveis](https://www.figma.com/online-whiteboard/create-diagram/b8f7d8b3-2dd5-4222-9de1-1ac20537b0e2?utm_source=other&utm_content=edit_in_figjam)

---

## Diagnóstico: O que temos vs. O que falta

| Capacidade | Estado Atual | Estado Ideal | Gap |
|---|---|---|---|
| Entender comandos do recrutador | Funciona (Cascaded Router, 205 actions) | Funciona | Pequeno |
| Executar ações simples | Funciona (109 tools, tool calling) | Funciona | Nenhum |
| Scoring e triagem WSI | Funciona (7 blocos, calibração cruzada) | Funciona | Nenhum |
| Memória conversacional | Funciona (ConversationMemory, ReferenceResolver) | Funciona | Nenhum |
| Transições de pipeline | Funciona parcialmente (modal + LLM sub-status) | Funciona | Pequeno |
| **Políticas por empresa** | **Não existe** | CompanyHiringPolicy governa tudo | **Grande** |
| **Execução multi-step** | **Frágil** (cada tool call isolada) | Action Planner robusto com retry | **Médio** |
| **Proatividade** | **Stubs inativos** (ProactiveAlert, AutonomousAgent) | Monitor contínuo + sugestões | **Grande** |
| **Predição acionável** | **Calcula mas não usa** (OutcomePredictor) | Predição → sugestão → ação | **Grande** |
| **Aprendizado contínuo** | **Registra mas não calibra** (FeedbackLoop) | Feedback → recalibração | **Médio** |
| **Contexto cross-domain** | **Fragmentado** (cada domínio isolado) | Agregador unificado | **Médio** |
| **Raciocínio estratégico** | **Inexistente** | Plano de trabalho por vaga | **Grande** |

---

## FASE 1: Fundação — CompanyHiringPolicy + Settings Page

> **Objetivo:** A empresa pode configurar suas políticas de contratação via conversa com a LIA na tela de Configurações. Os dados ficam salvos e acessíveis a toda a plataforma.

### 1.1 Entregáveis

#### Backend (lia-agent-system)

| # | Entregável | Tipo | Detalhes |
|---|---|---|---|
| 1.1 | Modelo `CompanyHiringPolicy` | NOVO | SQLAlchemy model com 5 campos JSON + `pipeline_templates` + `learned_patterns`. Migration Alembic. |
| 1.2 | API CRUD `/api/v1/company-hiring-policy` | NOVO | Endpoints: `GET` (por company_id), `PUT` (upsert), `PATCH` (update parcial por bloco), `GET /progress` (retorna setup_progress). Auth via tenant_id. |
| 1.3 | Helper `get_company_policy(company_id)` | NOVO | Função utilitária em `app/shared/policy_helper.py`. Retorna policy da empresa ou defaults (null). Cache em Redis (TTL 5min). |
| 1.4 | Schema Pydantic `CompanyHiringPolicySchema` | NOVO | Validação de entrada/saída para API. Includes `PipelineRulesSchema`, `SchedulingRulesSchema`, etc. |
| 1.5 | Endpoint de chat `/api/v1/policy-chat` | NOVO | Endpoint WebSocket ou SSE para chat no contexto de configuração de policies. Reutiliza infraestrutura de chat existente (ConversationMemory) com novo contexto `"policy_setup"`. |
| 1.6 | Policy Setup Agent | NOVO | Agente LangGraph específico para conduzir o onboarding de 19 perguntas. Usa intent classification para entender respostas naturais. Persiste resultados via API de update parcial. |

#### Frontend (plataforma-lia)

| # | Entregável | Tipo | Detalhes |
|---|---|---|---|
| 1.7 | Tab "Políticas de Contratação" em Configurações | NOVO | Nova tab na página de configurações. Reutiliza layout do Wizard de Vagas (chat à esquerda ~40%, painel à direita ~60%). |
| 1.8 | Componente `PolicyChat` | ADAPTAR | Reutiliza componente de chat existente (`ChatThread`, `ChatInput`, `ChatBubble`) com novo provider de contexto `PolicyChatProvider`. |
| 1.9 | Componente `PolicyCardsPanel` | NOVO | Painel com 5 cards colapsáveis (Pipeline, Agendamento, Comunicação, Triagem, Autonomia). Cada card mostra valores configurados (✓) ou pendentes (—). Barra de progresso no topo. |
| 1.10 | Componente `PolicyCardEdit` | NOVO | Modo de edição inline para cada card. Campos editáveis diretamente sem precisar conversar com a LIA. Salva via `PATCH /api/v1/company-hiring-policy`. |
| 1.11 | Real-time update | ADAPTAR | WebSocket/polling que atualiza os cards quando a LIA processa uma resposta. Animação fade-in nos valores novos. |

#### Roteiro de 19 Perguntas (implementado no Policy Setup Agent)

**Bloco 1: Pipeline e Processo (4 perguntas)**

| # | Pergunta | Campo | Default | Componente existente |
|---|---|---|---|---|
| Q1 | "Quantas entrevistas mínimas antes de proposta?" | `pipeline_rules.min_interviews_before_offer` | 2 | `RecruitmentStage` (regra de negócio) |
| Q2 | "Proposta precisa de aprovação do gestor?" | `pipeline_rules.manager_approval_for_offer` | true | `batch-approval-modal.tsx` |
| Q3 | "Tempo máximo por etapa sem ação?" | `pipeline_rules.max_days_in_stage` | null | `RecruitmentStage.sla_hours` |
| Q4 | "Tipos de vagas com processos diferentes?" | `pipeline_templates` | 1 template | `RecruitmentStage` per-company |

**Bloco 2: Agendamento (4 perguntas)**

| # | Pergunta | Campo | Default | Componente existente |
|---|---|---|---|---|
| Q5 | "Dias permitidos para entrevistas?" | `scheduling_rules.allowed_days` | Seg-Sex | `scheduling_service.py` |
| Q6 | "Horário permitido?" | `scheduling_rules.allowed_hours` | 09:00-18:00 | `scheduling_service.py` |
| Q7 | "Duração padrão de entrevista?" | `scheduling_rules.default_duration_minutes` | 60 | `scheduling_service.py` |
| Q8 | "Candidatos podem auto-agendar?" | `scheduling_rules.self_scheduling_enabled` | false | `ScreeningSchedulingModal.tsx` |

**Bloco 3: Comunicação (4 perguntas)**

| # | Pergunta | Campo | Default | Componente existente |
|---|---|---|---|---|
| Q9 | "Feedback automático para reprovados?" | `communication_rules.auto_rejection_feedback` | false | `CommunicationDispatcher` |
| Q10 | "Prazo para feedback?" | `communication_rules.rejection_feedback_deadline_hours` | 48h | Conceito SLA |
| Q11 | "Canal preferido: WhatsApp, email, ambos?" | `communication_rules.preferred_channel` | "whatsapp" | `whatsapp_service.py`, `email_service.py` |
| Q12 | "Tom da LIA: profissional, amigável, formal?" | `communication_rules.lia_tone` | "professional" | System prompts |

**Bloco 4: Triagem (3 perguntas)**

| # | Pergunta | Campo | Default | Componente existente |
|---|---|---|---|---|
| Q13 | "Filtram por pretensão salarial? Tolerância?" | `screening_rules.salary_expectation_filter` + `salary_tolerance_percent` | false | Campo de pretensão salarial na vaga |
| Q14 | "Experiência mínima por vaga ou geral?" | `screening_rules.experience_policy` | "per_job" | Campo de experiência |
| Q15 | "Perguntas padrão para todas as vagas?" | `screening_rules.default_screening_questions` | [] | `CompanyBankQuestions` |

**Bloco 5: Autonomia da LIA (4 perguntas)**

| # | Pergunta | Campo | Default | Componente existente |
|---|---|---|---|---|
| Q16 | "Triagem automática ou aguarda confirmação?" | `automation_rules.auto_screening` | false | `StageAutomationEngine` |
| Q17 | "Agendamento automático?" | `automation_rules.auto_scheduling` | false | `scheduling_service.py` |
| Q18 | "Mover etapa automaticamente?" | `automation_rules.auto_stage_advance` | false | `auto_advance_rules` |
| Q19 | "Nível geral: Baixo/Médio/Alto?" | `automation_rules.autonomy_level` | "low" | Feature flags |

### 1.2 Dependências

- Migration PostgreSQL (modelo novo)
- Reutilização de componentes de chat do Wizard de Vagas
- ConversationMemory já existente (novo contexto `"policy_setup"`)

### 1.3 Esforço Estimado

| Componente | Esforço | Risco |
|---|---|---|
| Backend (modelo + API + agent) | Médio | Baixo (padrões conhecidos) |
| Frontend (tab + chat + painel) | Médio | Baixo (reutiliza wizard) |
| Roteiro 19 perguntas | Médio | Médio (intent classification para respostas naturais) |
| **Total Fase 1** | **~4-5 semanas** | |

### 1.4 Critérios de Sucesso

- [ ] Recrutador acessa Configurações → Políticas de Contratação
- [ ] LIA conduz conversa de 19 perguntas em 5 blocos
- [ ] Dados preenchem os cards em tempo real
- [ ] Recrutador pode editar cards diretamente
- [ ] Recrutador pode parar e voltar depois (progresso salvo)
- [ ] API retorna `get_company_policy(company_id)` com dados ou defaults
- [ ] Testes E2E: criação completa, edição parcial, respostas naturais

---

## FASE 2: Integração — Agentes Consultam Policies

> **Objetivo:** Todos os serviços que tomam decisões passam a consultar `CompanyHiringPolicy` antes de agir. A LIA deixa de ser genérica e passa a respeitar as regras da empresa.

### 2.1 Entregáveis

| # | Entregável | Tipo | Detalhes | Componente afetado |
|---|---|---|---|---|
| 2.1 | `PolicyMiddleware` | NOVO | Middleware que injeta `company_policy` no contexto de cada request. Todos os serviços recebem a policy automaticamente. | `app/shared/policy_middleware.py` |
| 2.2 | Scheduling respeita `scheduling_rules` | ADAPTAR | `scheduling_service.py` consulta `allowed_days`, `allowed_hours`, `default_duration_minutes` antes de sugerir horários. Se null, usa defaults. | `scheduling_service.py`, `calendar_service.py` |
| 2.3 | Communication respeita `communication_rules` | ADAPTAR | `CommunicationDispatcher` consulta `preferred_channel` como fallback quando recrutador não especifica. `lia_tone` injetado no system prompt. | `communication_dispatcher.py`, prompts |
| 2.4 | Screening respeita `screening_rules` | ADAPTAR | Triagem automática consulta `salary_expectation_filter` + `salary_tolerance_percent`. `default_screening_questions` adicionadas automaticamente a novas vagas. | `screening_service.py`, criação de vaga |
| 2.5 | `PolicySyncService` | NOVO | Sincroniza `max_days_in_stage` (dias) → `RecruitmentStage.sla_hours` (horas × 24). Roda quando policy é salva. | `app/shared/policy_sync_service.py` |
| 2.6 | Feature flags mapeiam `automation_rules` | ADAPTAR | `auto_screening` → `ENABLE_AUTO_SCREENING_{company_id}`, etc. `autonomy_level` faz override conforme mapeamento da seção 3.22.6 do audit. | `feature_flag_service.py` |
| 2.7 | Pipeline templates conectam `RecruitmentStage` | ADAPTAR | Quando recrutador cria vaga e escolhe template "Operacional", as stages são pré-configuradas conforme `pipeline_templates`. | Wizard de vagas, `RecruitmentStage` |
| 2.8 | Validação de proposta respeita `pipeline_rules` | NOVO | `UniversalTransitionModal` verifica `min_interviews_before_offer` e `manager_approval_for_offer` ao mover candidato para Proposta. | `UniversalTransitionModal.tsx` |

### 2.2 Padrão de Integração

```
Antes (sem policy):
  scheduling_service.suggest_slots() → usa defaults fixos

Depois (com policy):
  policy = await get_company_policy(company_id)
  scheduling_service.suggest_slots(
    allowed_days=policy.scheduling_rules.get("allowed_days", DEFAULT_DAYS),
    allowed_hours=policy.scheduling_rules.get("allowed_hours", DEFAULT_HOURS),
    duration=policy.scheduling_rules.get("default_duration_minutes", 60)
  )
```

### 2.3 Esforço Estimado

| Componente | Esforço | Risco |
|---|---|---|
| PolicyMiddleware | Pequeno | Baixo |
| Adaptação de 4 serviços (scheduling, communication, screening, pipeline) | Médio | Médio (testes de regressão necessários) |
| PolicySyncService | Pequeno | Baixo |
| Feature flags mapping | Pequeno | Baixo |
| Validação de proposta | Pequeno | Baixo |
| **Total Fase 2** | **~3-4 semanas** | |

### 2.4 Critérios de Sucesso

- [ ] Ao criar vaga, se empresa tem template "Técnica", stages são pré-configuradas
- [ ] Scheduling sugere horários respeitando `allowed_days` e `allowed_hours` da empresa
- [ ] LIA usa tom configurado (`lia_tone`) em comunicações
- [ ] Canal preferido é usado como fallback
- [ ] `max_days_in_stage` sincronizado com `sla_hours`
- [ ] Modal de proposta bloqueia se `min_interviews_before_offer` não atendido
- [ ] Feature flags refletem `automation_rules`
- [ ] Testes: empresa sem policy funciona normalmente (defaults), empresa com policy respeita configurações

---

## FASE 3: Proatividade — Monitor Contínuo + Action Planner

> **Objetivo:** A LIA passa a monitorar o pipeline proativamente e consegue executar sequências de ações robustas com retry. Deixa de ser uma assistente passiva.

### 3.1 Entregáveis

| # | Entregável | Tipo | Detalhes |
|---|---|---|---|
| 3.1 | `PipelineMonitor` | NOVO | Job agendado (APScheduler) que roda a cada 30min e analisa o estado do pipeline de cada empresa. Gera eventos para candidatos parados, deadlines se aproximando, scores altos sem ação. Consulta `CompanyHiringPolicy` para saber os SLAs. |
| 3.2 | Ativar `ProactiveAlertService` | ADAPTAR | Hoje é stub. Conectar com eventos do `PipelineMonitor`. Cada alerta vira uma sugestão proativa na interface do recrutador (chat ou notificação). |
| 3.3 | `ActionPlanner` | NOVO | Orquestrador de ações multi-step com retry e rollback. Quando LIA recebe "agende entrevista com os 3 finalistas", o planner: (1) identifica candidatos, (2) verifica disponibilidade de cada um, (3) cria eventos, (4) envia convites, (5) move etapas. Se step 3 falha para um candidato, tenta alternativa sem parar o fluxo inteiro. |
| 3.4 | `PredictionActionBridge` | NOVO | Ponte entre `OutcomePredictor`/`PredictiveAnalytics` e sugestões acionáveis. Quando predição indica alta probabilidade de sucesso → sugere avanço. Quando indica risco de desistência → sugere ação preventiva. |
| 3.5 | Sugestões proativas no chat | ADAPTAR | Mensagens da LIA no chat principal (não só no contexto de policies): "Olha, o João está há 6 dias em Triagem e o SLA é 5 dias. Quer que eu mova ele para entrevista?" |
| 3.6 | Notificações inteligentes | ADAPTAR | `IntelligenceNotifications` recebe eventos do `PipelineMonitor` e gera notificações contextualizadas (não genéricas). |

### 3.2 Tipos de Eventos do PipelineMonitor

| Evento | Condição | Ação sugerida |
|---|---|---|
| `CANDIDATE_STAGNANT` | Candidato na mesma etapa > `max_days_in_stage` | "João está há X dias em [etapa]. Quer avançar?" |
| `HIGH_SCORE_NO_ACTION` | Score WSI > 80 e sem ação há 48h | "Maria tem score 88 e está parada. Sugerir entrevista?" |
| `DEADLINE_APPROACHING` | Vaga com deadline em < 5 dias e poucos candidatos | "Vaga [X] fecha em 4 dias, só 2 candidatos na entrevista" |
| `INTERVIEW_COMPLETED_NO_FEEDBACK` | Entrevista realizada há 48h sem feedback | "A entrevista do Pedro foi há 2 dias. Quer registrar feedback?" |
| `REJECTION_PENDING_FEEDBACK` | Candidato reprovado e `auto_rejection_feedback=false` e > deadline_hours | "5 candidatos reprovados sem feedback. Enviar em lote?" |
| `FUNNEL_WEAK` | < 3 candidatos em etapas avançadas | "Funil fraco para [vaga]. Sugerir ampliar sourcing?" |

### 3.3 ActionPlanner — Estrutura

```
ExecutionPlan {
  id: uuid
  steps: [
    { action: "find_candidates", params: {...}, status: "completed" },
    { action: "check_availability", params: {...}, status: "completed" },
    { action: "create_event", params: {...}, status: "failed", retry_count: 1 },
    { action: "send_invite", params: {...}, status: "pending" },
    { action: "move_stage", params: {...}, status: "pending" }
  ]
  retry_policy: { max_retries: 2, backoff: "exponential" }
  rollback_steps: [...]  // desfaz ações anteriores se plano é cancelado
  created_at, completed_at, error_log
}
```

### 3.4 Esforço Estimado

| Componente | Esforço | Risco |
|---|---|---|
| PipelineMonitor | Médio | Médio (performance com muitas empresas) |
| Ativar ProactiveAlertService | Pequeno | Baixo (já existe, só conectar) |
| ActionPlanner | Grande | Alto (orquestração multi-step é complexa) |
| PredictionActionBridge | Médio | Médio (calibrar thresholds) |
| Sugestões no chat + notificações | Pequeno | Baixo |
| **Total Fase 3** | **~5-6 semanas** | |

### 3.5 Critérios de Sucesso

- [ ] PipelineMonitor roda a cada 30min e gera eventos para candidatos parados
- [ ] LIA envia sugestão proativa no chat quando candidato excede SLA
- [ ] "Agende entrevista com os 3 finalistas" funciona como sequência robusta
- [ ] Se um step falha, planner tenta alternativa sem parar todo o fluxo
- [ ] Predições com score > 0.8 geram sugestões acionáveis automaticamente
- [ ] Recrutador pode aceitar/rejeitar sugestão proativa com um clique ou resposta no chat
- [ ] Performance: monitor roda em < 30s para empresa com 100 candidatos ativos

---

## FASE 4: Aprendizado — Feedback Loop Ativo + Contexto Cross-Domain

> **Objetivo:** A LIA aprende com as decisões do recrutador e calibra seu comportamento. Dados de todos os domínios alimentam decisões mais inteligentes. A LIA evolui de assistente para consultora.

### 4.1 Entregáveis

| # | Entregável | Tipo | Detalhes |
|---|---|---|---|
| 4.1 | Ativar `FeedbackLoopService` (recalibração) | ADAPTAR | Hoje registra feedback mas não recalibra. Novo: quando recrutador rejeita sugestão da LIA → reduz peso do padrão (-0.1). Quando aceita → reforça (+0.05). Quando altera → aprende variação. |
| 4.2 | `CrossDomainContextAggregator` | NOVO | Versão expandida do `CandidateContextAggregator` que funciona cross-domain. Quando LIA está no chat de uma vaga, ela "vê" que candidato X tem score WSI alto na triagem, respondeu assessment, tem entrevista agendada — mesmo que esses dados venham de domínios diferentes. |
| 4.3 | `learned_patterns` preenchido automaticamente | NOVO | A LIA observa padrões e salva em `learned_patterns`: "recrutadores desta empresa preferem entrevistas à tarde" (confidence: 0.85), "vagas de TI demoram em média 18 dias" (confidence: 0.92). |
| 4.4 | Motor de confiança calibrado | NOVO | Decisões da LIA usam peso triplo: regras explícitas (1.0) + padrões aprendidos (0.7) + defaults (0.3). Confiança calculada determina se LIA age, sugere, ou só informa (conforme `autonomy_level`). |
| 4.5 | Consultoria estratégica | NOVO | LIA analisa métricas da empresa vs. benchmarks: "Seu tempo médio em triagem é 40% acima do benchmark. Possível gargalo no feedback dos gestores." "Baseado em vagas similares, candidatos com certificação X são 3x mais retidos." |
| 4.6 | Dashboard de automação por empresa | NOVO | Tela simples mostrando: quantas ações a LIA executou, quantas sugestões aceitas/rejeitadas, padrões aprendidos, confiança atual, nível de autonomia ativo. |

### 4.2 Arquitetura do Motor de Decisão

```
┌─────────────────────────────────────────────────────┐
│              MOTOR DE DECISÃO DA LIA                 │
│                                                       │
│  Entrada: Evento do PipelineMonitor                  │
│           + Contexto cross-domain                    │
│           + CompanyHiringPolicy                      │
│                                                       │
│  Cálculo de confiança:                               │
│  ├─ Regra explícita encontrada? → peso 1.0           │
│  ├─ Padrão aprendido relevante? → peso 0.7           │
│  └─ Usar default genérico → peso 0.3                 │
│                                                       │
│  Decisão (baseada em autonomy_level):                │
│  ├─ confiança ≥ 0.9 + "high" → EXECUTA + notifica   │
│  ├─ confiança ≥ 0.7 + "medium" → SUGERE + confirma  │
│  └─ confiança < 0.7 OU "low" → INFORMA apenas       │
│                                                       │
│  Feedback loop:                                       │
│  ├─ Aceita → reforça padrão (+0.05 confiança)       │
│  ├─ Rejeita → reduz peso (-0.10 confiança)          │
│  └─ Altera → aprende variação nova                   │
└─────────────────────────────────────────────────────┘
```

### 4.3 Exemplos de learned_patterns

```json
[
  {
    "pattern": "recruiter_prefers_afternoon_interviews",
    "confidence": 0.85,
    "source": "observation",
    "data": { "preferred_hours": "14:00-17:00" },
    "observation_count": 12,
    "last_observed": "2026-04-15"
  },
  {
    "pattern": "tech_jobs_avg_duration",
    "confidence": 0.92,
    "source": "analytics",
    "data": { "avg_days": 18, "std_dev": 4.2 },
    "observation_count": 45,
    "last_observed": "2026-04-20"
  },
  {
    "pattern": "recruiter_overrides_lia_substatus",
    "confidence": 0.78,
    "source": "feedback",
    "data": { "lia_suggested": "sem_experiencia", "recruiter_chose": "perfil_incompleto", "count": 8 },
    "observation_count": 8,
    "last_observed": "2026-04-18"
  }
]
```

### 4.4 Esforço Estimado

| Componente | Esforço | Risco |
|---|---|---|
| FeedbackLoop ativo + recalibração | Médio | Médio (calibrar pesos sem overfitting) |
| CrossDomainContextAggregator | Médio | Médio (performance com muitos dados) |
| learned_patterns automático | Médio | Médio (definir o que observar) |
| Motor de confiança | Grande | Alto (lógica complexa) |
| Consultoria estratégica | Médio | Baixo (analytics já existem) |
| Dashboard de automação | Pequeno | Baixo |
| **Total Fase 4** | **~6-8 semanas** | |

### 4.5 Critérios de Sucesso

- [ ] Quando recrutador rejeita sugestão 3x, LIA ajusta comportamento
- [ ] `learned_patterns` tem pelo menos 5 padrões por empresa após 30 dias de uso
- [ ] LIA no chat de uma vaga "sabe" o score WSI do candidato mesmo sem perguntar
- [ ] Dashboard mostra taxa de aceitação de sugestões > 60%
- [ ] Consultoria estratégica gera pelo menos 1 insight por semana por empresa
- [ ] Motor de confiança reduz taxa de sugestões rejeitadas em 30% vs. sem aprendizado

---

## Resumo Consolidado

| Fase | Objetivo | Esforço | Impacto | Dependência |
|---|---|---|---|---|
| **Fase 1** | Políticas da empresa configuráveis via LIA | ~4-5 semanas | Base para tudo | Nenhuma |
| **Fase 2** | Agentes respeitam policies | ~3-4 semanas | LIA personalizada | Fase 1 |
| **Fase 3** | Proatividade + execução robusta | ~5-6 semanas | LIA proativa | Fases 1-2 |
| **Fase 4** | Aprendizado + consultoria | ~6-8 semanas | LIA inteligente | Fases 1-3 |
| **Total** | | **~18-23 semanas** | | |

### O que já existe e será REUTILIZADO

| Componente existente | Fase que reutiliza | Como |
|---|---|---|
| Chat components (Wizard de Vagas) | Fase 1 | Layout e componentes do chat para Settings |
| `RecruitmentStage` (company-scoped) | Fase 2 | `PolicySyncService` sincroniza SLAs |
| `StageAutomationEngine` (16 triggers) | Fase 2, 3 | Conectar com policies + monitor |
| `CommunicationDispatcher` | Fase 2 | Consultar `preferred_channel` e `lia_tone` |
| Feature Flags | Fase 2 | Mapear `automation_rules` |
| `ProactiveAlertService` (stub) | Fase 3 | Ativar com eventos do PipelineMonitor |
| `AutomationScheduler` (APScheduler) | Fase 3 | Base para PipelineMonitor |
| `OutcomePredictor` + `PredictiveAnalytics` | Fase 3 | PredictionActionBridge |
| `FeedbackLoopService` + `LearningPattern` | Fase 4 | Ativar recalibração |
| `CandidateContextAggregator` | Fase 4 | Expandir para cross-domain |
| `ConversationMemory` | Fase 1, 4 | Novo contexto + contexto cruzado |

### O que será NOVO

| Componente novo | Fase | Função |
|---|---|---|
| `CompanyHiringPolicy` (modelo + API) | Fase 1 | Armazena políticas por empresa |
| `PolicySetupAgent` | Fase 1 | Conduz onboarding conversacional |
| `PolicyCardsPanel` (frontend) | Fase 1 | Painel visual de políticas |
| `PolicyMiddleware` | Fase 2 | Injeta policy no contexto |
| `PolicySyncService` | Fase 2 | Sincroniza policy → models existentes |
| `PipelineMonitor` | Fase 3 | Monitoramento contínuo do pipeline |
| `ActionPlanner` | Fase 3 | Execução multi-step robusta |
| `PredictionActionBridge` | Fase 3 | Predição → sugestão acionável |
| `CrossDomainContextAggregator` | Fase 4 | Contexto unificado |
| Motor de confiança | Fase 4 | Decisão com peso calibrado |
| Dashboard de automação | Fase 4 | Visibilidade do aprendizado |

---

## Métricas de Sucesso do Projeto

| Métrica | Baseline (hoje) | Meta Fase 1-2 | Meta Fase 3-4 |
|---|---|---|---|
| Empresas com policies configuradas | 0% | 50% das ativas | 80% das ativas |
| Sugestões proativas por semana/empresa | 0 | N/A | 10+ |
| Taxa de aceitação de sugestões | N/A | N/A | > 60% |
| Tempo médio de candidato em etapa | Sem monitoramento | Visível (SLA) | Redução 20% |
| Ações multi-step completadas com sucesso | N/A | N/A | > 85% |
| Padrões aprendidos por empresa (30 dias) | 0 | N/A | 5+ |

---

*Documento de planejamento v1.0 — 21/02/2026. Baseado no diagnóstico arquitetural v6.2, análise de gaps da plataforma, e benchmarks de mercado (Ashby, Lever, Greenhouse, Paradox).*
