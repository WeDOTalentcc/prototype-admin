# Mapeamento de Integração: Funcionalidades × Agentes AI

Este documento mapeia todas as funcionalidades existentes na plataforma LIA que precisam ser conectadas aos agentes AI para automação completa do processo de recrutamento.

## Arquitetura Multi-Agente (9 Agentes)

| # | Agente | Arquivo | Responsabilidade Principal |
|---|--------|---------|---------------------------|
| 0 | **Orchestrator** | `agent_registry.py` | Roteia tarefas entre agentes |
| 1 | **Job Planner** | `job_intake_agent.py` | Cria vagas, define requisitos |
| 2 | **Sourcing** | `sourcing_agent.py` | Busca candidatos, ranking inicial |
| 3 | **CV Screening** | `triagem_curricular_agent.py` | Triagem curricular, red flags |
| 4 | **Interviewer** | `entrevistador_agent.py` | Entrevistas WSI (WhatsApp/Voz) |
| 5 | **WSI Evaluator** | `avaliador_wsi_agent.py` | Calcula score, gera parecer |
| 6 | **Scheduling** | `scheduling_agent.py` | Agenda entrevistas |
| 7 | **Analyst & Feedback** | `analista_feedback_agent.py` | Comunicações, notificações |
| 8 | **ATS Integrator** | `integrador_ats_agent.py` | Sincroniza com Gupy, Pandapé |
| 9 | **Task Planner** | `task_planner_agent.py` | Planejamento de tarefas |
| 10 | **Recruiter Assistant** | `recruiter_assistant_agent.py` | Assistente pessoal |

---

## 1. CRIAÇÃO DE VAGAS

### 1.1 Job Creation Wizard
**Componente:** `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx`

**Status Atual:** ✅ Parcialmente integrado
- Usa `liaApi` para chat conversacional
- Extrai critérios da descrição da vaga
- Busca candidatos locais/globais para calibração

**Agente Responsável:** `Job Planner (Ag.1)`

**Integrações Necessárias:**
| Ação | Endpoint/Service | Status |
|------|------------------|--------|
| Extrair requisitos da JD | `/api/v1/jobs/extract` | ✅ Existe |
| Gerar perguntas WSI | `wsi_question_generator.py` | ✅ Existe |
| Buscar candidatos calibração | `pearch_service.py` | ✅ Existe |
| Criar vaga no backend | `/api/v1/jobs` POST | ✅ Existe |
| **Notificar Sourcing Agent** | `automation_service.py` | ❌ Faltando |
| **Disparar busca automática** | `sourcing_agent.py` | ❌ Faltando |

**Ação Requerida:**
```
Wizard finaliza criação → Trigger "job_created" → 
  → Orchestrator notifica Sourcing Agent
  → Sourcing inicia busca automática (opcional, configurável)
  → Recrutador recebe notificação com candidatos sugeridos
```

### 1.2 Edit Job Modal
**Componente:** `plataforma-lia/src/components/modals/edit-job-modal.tsx`

**Status Atual:** ⚠️ Não integrado com agentes

**Integrações Necessárias:**
| Ação | Agente | Status |
|------|--------|--------|
| Atualizar requisitos → recalcular aderência | CV Screening | ❌ Faltando |
| Mudança significativa → re-ranquear candidatos | WSI Evaluator | ❌ Faltando |
| Notificar candidatos de mudanças | Analyst & Feedback | ❌ Faltando |

---

## 2. BUSCA E SOURCING

### 2.1 Smart Search Input
**Componente:** `plataforma-lia/src/components/search/smart-search-input.tsx`

**Status Atual:** ✅ Parcialmente integrado
- Busca semântica via `semantic_search_service.py`
- Busca global via `pearch_service.py`

**Agente Responsável:** `Sourcing (Ag.2)`

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Boolean string generation | ✅ Existe |
| Enriquecimento de perfil | ✅ Existe (Pearch) |
| **Sugestão proativa de candidatos** | ❌ Faltando |
| **Outreach automático WhatsApp** | ⚠️ Existe parcialmente |

### 2.2 Candidate Search Results
**Componente:** `plataforma-lia/src/components/search/search-results-card.tsx`

**Integrações Necessárias:**
| Ação | Agente | Status |
|------|--------|--------|
| Adicionar à vaga → trigger triagem | CV Screening | ❌ Faltando |
| Iniciar contato automático | Analyst & Feedback | ❌ Faltando |

---

## 3. TRIAGEM E SCREENING

### 3.1 Screening Questions Panel
**Componente:** `plataforma-lia/src/components/job-creation/ScreeningQuestionsPanel.tsx`

**Status Atual:** ✅ Integrado
- Perguntas geradas pelo Job Planner
- Configuração de eliminatórias

**Agente Responsável:** `CV Screening (Ag.3)`

### 3.2 WSI Triagem Invite Modal
**Componente:** `plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx`

**Status Atual:** ⚠️ Parcialmente integrado

**Agente Responsável:** `Interviewer (Ag.4)`

**Integrações Necessárias:**
| Ação | Service | Status |
|------|---------|--------|
| Enviar convite WhatsApp | `whatsapp_service.py` | ✅ Existe |
| Enviar convite Email | `email_service.py` | ✅ Existe |
| **Iniciar triagem automática** | `wsi_voice_orchestrator.py` | ⚠️ Manual |
| **Processar respostas** | `entrevistador_agent.py` | ⚠️ Manual |
| **Calcular score após conclusão** | `avaliador_wsi_agent.py` | ⚠️ Manual |

**Ação Requerida:**
```
Candidato conclui triagem WSI → Trigger "screening_completed" →
  → WSI Evaluator calcula score automaticamente
  → Gera parecer
  → Sugere próximo estágio (com confidence score)
  → Recrutador aprova/ajusta
```

---

## 4. COMUNICAÇÕES

### 4.1 Unified Communication Modal
**Componente:** `plataforma-lia/src/components/modals/unified-communication-modal.tsx`

**Status Atual:** ✅ Parcialmente integrado
- Suporta: email, whatsapp, triagem, agendamento, feedback
- Usa templates do backend
- Multi-tenancy via `companyId`

**Agente Responsável:** `Analyst & Feedback (Ag.7)`

**Integrações Necessárias:**
| Ação | Service | Status |
|------|---------|--------|
| Enviar email | `email_service.py` | ✅ Existe |
| Enviar WhatsApp | `whatsapp_service.py` | ✅ Existe |
| **Registrar atividade** | `activity_service.py` | ⚠️ Parcial |
| **Sugerir template baseado no contexto** | `automation_service.py` | ❌ Faltando |
| **Follow-up automático** | `proactive_service.py` | ❌ Faltando |

### 4.2 Stage Transition Actions Modal
**Componente:** `plataforma-lia/src/components/modals/stage-transition-actions-modal.tsx`

**Status Atual:** ✅ Recém integrado
- Abre após seleção de estágio
- Sugere ações baseadas na transição
- Busca templates do backend

**Agente Responsável:** `Analyst & Feedback (Ag.7)` + `Orchestrator`

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Sugestões AI via `/stage-suggestions` | ✅ Existe |
| Disparar comunicação | ⚠️ Parcial (UI pronta, backend precisa wiring) |
| Iniciar triagem WSI | ⚠️ Parcial |
| Agendar entrevista | ⚠️ Parcial |

---

## 5. AGENDAMENTO

### 5.1 Interview Scheduling Modal/Panel
**Componentes:**
- `plataforma-lia/src/components/ui/interview-scheduling-modal.tsx`
- `plataforma-lia/src/components/ui-actions/panels/InterviewSchedulingPanel.tsx`

**Status Atual:** ⚠️ Parcialmente integrado

**Agente Responsável:** `Scheduling (Ag.6)`

**Services Backend:**
- `scheduling_service.py` - lógica de agendamento
- `calendar_service.py` - integração com calendários

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Verificar disponibilidade | ✅ Existe |
| Criar evento no calendário | ✅ Existe (Microsoft Graph) |
| **Enviar convite automático** | ⚠️ Manual |
| **Lembretes automáticos** | ❌ Faltando |
| **Detectar no-show** | ❌ Faltando |
| **Reagendar automaticamente** | ❌ Faltando |

---

## 6. AVALIAÇÃO E SCORING

### 6.1 LIA Analysis Modal
**Componente:** `plataforma-lia/src/components/modals/lia-analysis-modal.tsx`

**Status Atual:** ✅ Integrado
- Mostra análise do candidato
- Score LIA e componentes

**Agente Responsável:** `WSI Evaluator (Ag.5)`

**Services Backend:**
- `lia_score_service.py`
- `wsi_service.py`
- `rubric_evaluation_service.py`

### 6.2 General Score Modal
**Componente:** `plataforma-lia/src/components/modals/general-score-modal.tsx`

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Calcular score | ✅ Existe |
| **Sugerir estágio baseado no score** | ❌ Faltando |
| **Explicar decisão (Explainability)** | ✅ Existe (`explainability_service.py`) |

---

## 7. CONFIGURAÇÕES E ONBOARDING

### 7.1 Onboarding Wizard
**Componente:** `plataforma-lia/src/components/settings/onboarding-wizard.tsx`

**Status Atual:** ⚠️ Não integrado com agentes

**Integrações Necessárias:**
| Ação | Agente | Status |
|------|--------|--------|
| Analisar cultura da empresa | Culture Analyzer | ⚠️ Existe service, não agente |
| Configurar templates padrão | Analyst & Feedback | ❌ Faltando |
| Setup inicial de automações | Orchestrator | ❌ Faltando |

### 7.2 Recruitment Journey Config
**Componente:** `plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx`

**Status Atual:** ✅ UI existe

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Definir estágios do pipeline | ✅ Existe |
| **Configurar automações por estágio** | ❌ Faltando |
| **Vincular agentes a cada estágio** | ❌ Faltando |

### 7.3 Communication Hub
**Componente:** `plataforma-lia/src/components/settings/CommunicationHub.tsx`

**Status Atual:** ✅ UI existe

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Templates de comunicação | ✅ Existe |
| **Automações de follow-up** | ❌ Faltando |
| **Triggers por tempo** | ❌ Faltando |

---

## 8. INTEGRAÇÕES ATS

### 8.1 ATS Integrations Page
**Componente:** `plataforma-lia/src/components/pages/ats-integrations-page.tsx`

**Status Atual:** ✅ Parcialmente integrado

**Agente Responsável:** `ATS Integrator (Ag.8)`

**Services Backend:**
- `ats_sync_service.py`
- `ats_clients/gupy.py`
- `ats_clients/pandape.py`
- `ats_clients/stackone.py`

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Sincronizar vagas | ✅ Existe |
| Sincronizar candidatos | ✅ Existe |
| **Sincronizar mudanças de estágio automaticamente** | ⚠️ Parcial |
| **Receber webhooks do ATS** | ✅ Existe |

---

## 9. PIPELINE E KANBAN

### 9.1 Job Kanban Page
**Componente:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`

**Status Atual:** ✅ Recém integrado
- InteractiveStageCell com StageTransitionActionsModal
- InteractiveSubStatusCell

**Integrações Necessárias:**
| Ação | Status |
|------|--------|
| Transição de estágio | ✅ Existe |
| Sugestões de ação | ✅ Existe (recém integrado) |
| **Automação baseada em regras** | ❌ Faltando |
| **Indicadores visuais de IA** | ⚠️ Parcial |

---

## 10. MAPA DE TRIGGERS E AÇÕES

### Triggers Existentes (Implementados)
| Trigger | Evento | Handler | Status |
|---------|--------|---------|--------|
| `candidate_stage_changed` | Mudança de estágio | `pipeline_stage_service.py` | ✅ |
| `lia_score_calculated` | Score calculado | `lia_score_service.py` | ✅ |

### Triggers Necessários (A Implementar)
| Trigger | Evento | Agente Responsável | Prioridade |
|---------|--------|-------------------|------------|
| `job_created` | Nova vaga criada | Sourcing | Alta |
| `job_updated` | Vaga editada | CV Screening | Média |
| `screening_completed` | Triagem WSI concluída | WSI Evaluator | Alta |
| `interview_scheduled` | Entrevista agendada | Scheduling | Alta |
| `interview_completed` | Entrevista concluída | WSI Evaluator | Alta |
| `candidate_no_show` | Candidato não compareceu | Scheduling | Média |
| `offer_sent` | Proposta enviada | Analyst & Feedback | Média |
| `offer_accepted` | Proposta aceita | ATS Integrator | Alta |
| `offer_declined` | Proposta recusada | Analyst & Feedback | Média |
| `candidate_inactive` | 7+ dias sem ação | Proactive Service | Baixa |

---

## 11. PRIORIZAÇÃO DE IMPLEMENTAÇÃO

### Fase 1: Fundação (Semana 1-2)
1. ✅ Stage Transition Actions Modal integrado
2. ⏳ Implementar endpoint de disparo de comunicações
3. ⏳ Wiring completo: stage change → communication dispatch
4. ⏳ Trigger `job_created` → notificar Sourcing

### Fase 2: Automação Core (Semana 3-4)
5. Trigger `screening_completed` → WSI Evaluator auto-score
6. Trigger `interview_scheduled` → envio automático de convites
7. Trigger `interview_completed` → geração de parecer
8. Painel de aprovação de sugestões AI

### Fase 3: Proatividade (Semana 5-6)
9. Trigger `candidate_inactive` → follow-up automático
10. Trigger `candidate_no_show` → reagendar/reprovar
11. Dashboard de métricas AI (acurácia das sugestões)

### Fase 4: Inteligência Avançada (Semana 7-8)
12. Sugestão proativa de candidatos (Sourcing)
13. Auto-triagem baseada em score
14. Previsão de aceite de proposta

---

## 12. ARQUITETURA DE INTEGRAÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
├─────────────────────────────────────────────────────────────┤
│  Job Wizard ─────────────────────────────────────────────┐  │
│  Search ─────────────────────────────────────────────────┤  │
│  Kanban/Pipeline ────────────────────────────────────────┤  │
│  Communication Modal ────────────────────────────────────┤  │
│  Settings ───────────────────────────────────────────────┤  │
└──────────────────────────────────────────────────────────│──┘
                                                           │
                                                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  /api/v1/jobs                                               │
│  /api/v1/candidates                                         │
│  /api/v1/pipeline/stages                                    │
│  /api/v1/automation/stage-suggestions ◄── company_id        │
│  /api/v1/communication/send                                 │
│  /api/v1/scheduling                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  pipeline_stage_service.py ──► automation_service.py        │
│  communication_dispatcher.py                                 │
│  scheduling_service.py                                       │
│  wsi_service.py                                              │
│  ats_sync_service.py                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LAYER (LangGraph)                   │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator ──┬──► Job Planner                            │
│                 ├──► Sourcing                                │
│                 ├──► CV Screening                            │
│                 ├──► Interviewer                             │
│                 ├──► WSI Evaluator                           │
│                 ├──► Scheduling                              │
│                 ├──► Analyst & Feedback                      │
│                 ├──► ATS Integrator                          │
│                 └──► Task Planner                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 13. PRÓXIMOS PASSOS IMEDIATOS

1. **Implementar `communication_dispatcher` integration**
   - Conectar StageTransitionActionsModal → backend → email/whatsapp

2. **Criar endpoint `/api/v1/automation/execute-action`**
   - Recebe: action_type, candidate_id, job_id, template_id, channel
   - Executa: dispara comunicação via service apropriado

3. **Implementar trigger `job_created`**
   - Job Wizard → trigger → Sourcing Agent → busca inicial

4. **Implementar trigger `screening_completed`**
   - WSI concluída → WSI Evaluator → score + parecer → sugestão de estágio

---

*Última atualização: 2026-01-19*
*Versão: 1.0*
