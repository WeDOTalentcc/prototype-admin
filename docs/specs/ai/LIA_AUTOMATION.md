# Sistema de Automação LIA — Especificação Unificada

**Versão:** 2.0
**Última atualização:** 2026-03-26
**Fonte:** Consolidação de 4 documentos anteriores (LIA_AUTOMATION_SYSTEM, LIA_AUTOMATION_IMPLEMENTATION_PLAN, LIA_AUTOMATION_DEVELOPMENT_GUIDE, AI_STAGE_AUTOMATION_ARCHITECTURE)
**Proprietário:** WeDOTalent Engineering

---

## 1. Visão Geral

O Sistema de Automação LIA automatiza e personaliza a comunicação com candidatos ao longo do processo de recrutamento, reduzindo o trabalho manual do recrutador enquanto melhora a experiência do candidato.

### 1.1 Princípios Fundamentais

1. **LIA Sugere, Recrutador Confirma** — sugestões inteligentes com controle final humano
2. **Personalização Baseada em Dados** — toda comunicação usa dados reais (scores, notas, pareceres)
3. **Ajuste Dinâmico** — ao alterar parâmetro (ex: sub-status), LIA reajusta o texto automaticamente
4. **Templates Centralizados** — templates base no CommunicationHub; modais fazem ajustes temporários

---

## 2. Arquitetura Multi-Agente

### 2.1 Agentes Especializados

| # | Agente | Responsabilidade | Estágios |
|---|--------|------------------|----------|
| 0 | **Orchestrator** | Roteamento, memória, delegação | Todos |
| 1 | **Job Planner** | Criar/editar vagas, requisitos | Pré-processo |
| 2 | **Sourcing** | Buscar candidatos, outreach | `sourcing` |
| 3 | **CV Screening** | Triagem curricular, ranking | `screening` |
| 4 | **Interviewer** | Entrevistas WSI (WhatsApp/Voz) | `screening`, `interview_*` |
| 5 | **WSI Evaluator** | Avaliação WSI, parecer, comparação | Todas entrevistas |
| 6 | **Scheduling** | Agendamento de entrevistas | `interview_*` |
| 7 | **Analyst & Feedback** | Comunicações, analytics | Todos |
| 8 | **ATS Integrator** | Sincronização com ATSs externos | Todos |
| 9 | **Task Planner** | Criar e gerenciar tarefas | Todos |

### 2.2 Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                        │
├─────────────────────────────────────────────────────────────────┤
│  StageTransitionModal  │  BulkActionsModal  │  QuickActionsMenu │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MOTOR DE AUTOMAÇÃO LIA                        │
├─────────────────────────────────────────────────────────────────┤
│  ContextCollector  │  MessageGenerator  │  SubStatusPredictor   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                               │
├─────────────────────────────────────────────────────────────────┤
│  CandidateContext  │  Templates  │  InterviewNotes  │  Scores   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM (Claude / Gemini)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Máquina de Estados — Recruitment Pipeline

### 3.1 Estados e Transições

```
ESTADO: sourcing
   ├─ Trigger: job_vacancy_created
   ├─ Agente: Sourcing
   ├─ Ações AI: buscar candidatos, rankear, solicitar aprovação
   ├─ Transições:
   │    ├─ [recrutador aprova] → screening
   │    ├─ [recrutador reprova] → rejected
   │    └─ [sem resposta 48h] → sourcing (follow_up_sent)
   └─ Sub-status: identified, researching, qualified_to_contact,
        contacted_*, awaiting_response, interested, not_interested,
        ready_for_screening

ESTADO: screening
   ├─ Trigger: candidate_approved_for_screening
   ├─ Agentes: CV Screening + Interviewer
   ├─ Ações AI: analisar CV, calcular LIA Score, detectar red flags,
   │    triagem conversacional, coletar WSI, rankear
   ├─ Transições:
   │    ├─ [score alto + aprovação] → long_list
   │    ├─ [score baixo] → rejected
   │    ├─ [precisa entrevistar] → interview_hr
   │    └─ [candidato desiste] → rejected
   └─ Sub-status: cv_received, cv_analyzing, cv_approved,
        screening_scheduled, screening_in_progress, screening_completed,
        screening_approved

ESTADO: long_list / short_list
   ├─ Trigger: screening_approved
   ├─ Agente: Analyst & Feedback
   ├─ Ações AI: compilar shortlist, comparativo, aprovação gestor
   ├─ Transições:
   │    ├─ [gestor aprova] → interview_manager
   │    ├─ [gestor pede mais] → sourcing
   │    └─ [gestor reprova] → rejected
   └─ Sub-status: added_to_long_list, added_to_short_list,
        presented_to_manager, awaiting_manager_evaluation,
        manager_approved, manager_rejected

ESTADO: interview_hr / interview_manager / interview_technical / interview_final
   ├─ Trigger: approved_for_interview
   ├─ Agentes: Scheduling + Interviewer + WSI Evaluator
   ├─ Ações AI: verificar disponibilidade, propor horários, enviar
   │    convites/lembretes, conduzir entrevista, transcrever, calcular
   │    WSI Score, gerar parecer
   ├─ Transições:
   │    ├─ [aprovado] → próximo estágio ou offer
   │    ├─ [reprovado] → rejected
   │    ├─ [no-show] → rejected ou follow_up
   │    └─ [reagendar] → mesmo estágio (rescheduled)
   └─ Sub-status: awaiting_schedule, scheduled, confirmed,
        in_progress, completed, no_show, awaiting_feedback,
        approved, rejected

ESTADO: offer
   ├─ Trigger: final_interview_approved
   ├─ Agente: Analyst & Feedback
   ├─ Ações AI: gerar proposta, aprovação interna, enviar, monitorar
   ├─ Transições:
   │    ├─ [aceita] → hired
   │    ├─ [recusa] → offer_declined
   │    ├─ [negocia] → offer (negotiating)
   │    └─ [sem resposta] → follow_up
   └─ Sub-status: offer_approved_internally, offer_sent,
        offer_viewed, negotiating, offer_accepted, offer_declined

ESTADO: hired (FINAL)
   ├─ Trigger: offer_accepted
   ├─ Ações: sincronizar ATS, iniciar onboarding, fechar vaga

ESTADO: rejected (FINAL)
   ├─ Trigger: various
   ├─ Ações: email feedback, salvar banco talentos, registrar motivo
```

---

## 4. Triggers, Agentes e Ações

### 4.1 Triggers do Sistema

| Trigger | Descrição | Agente |
|---------|-----------|--------|
| `candidate_applied` | Candidatura recebida | CV Screening |
| `candidate_stage_changed` | Mudança de estágio | Orchestrator |
| `screening_completed` | Triagem finalizada | WSI Evaluator |
| `interview_scheduled` | Entrevista agendada | Scheduling |
| `feedback_received` | Feedback de entrevista | Analyst |
| `offer_sent` | Proposta enviada | Analyst |
| `candidate_hired` | Candidato contratado | ATS Integrator |
| `candidate_rejected` | Candidato reprovado | Analyst |
| `no_response_48h` | Sem resposta em 48h | Sourcing/Analyst |
| `deadline_approaching` | Prazo aproximando | Task Planner |
| `lia_score_calculated` | LIA Score calculado | WSI Evaluator |
| `wsi_interview_completed` | Entrevista WSI finalizada | Interviewer |
| `manager_approval_received` | Aprovação do gestor | Analyst |
| `candidate_no_show` | Candidato faltou | Scheduling |

### 4.2 Ações Disponíveis

| Ação | Descrição | Executor |
|------|-----------|----------|
| `send_email` | Enviar email templated | Analyst |
| `send_whatsapp` | Enviar WhatsApp | Interviewer |
| `create_task` | Criar tarefa para recrutador | Task Planner |
| `notify_recruiter` | Notificação push/bell | Analyst |
| `notify_manager` | Notificação para gestor | Analyst |
| `update_candidate_status` | Atualizar status | Pipeline Stage Service |
| `log_activity` | Registrar atividade | Audit Service |
| `calculate_score` | Calcular/recalcular score | WSI Evaluator |
| `generate_parecer` | Gerar parecer AI | WSI Evaluator |
| `schedule_interview` | Agendar entrevista | Scheduling |
| `sync_to_ats` | Sincronizar com ATS | ATS Integrator |
| `add_to_talent_pool` | Banco de talentos | Sourcing |

---

## 5. Fluxo de Transição de Etapa

### 5.1 Triggers de Transição

O sistema é acionado quando:
- Candidato é arrastado no Kanban (drag & drop)
- Candidato é movido via tabela (InteractiveStageCell)
- Ação em lote é executada (bulk action)

### 5.2 Coleta de Contexto

```typescript
interface CandidateContext {
  id: string
  name: string
  email: string
  phone?: string

  current_stage: string
  target_stage: string
  days_in_process: number
  stages_completed: string[]

  wsi_score?: {
    overall: number
    technical: number
    behavioral: number
    cultural: number
  }

  interview_notes?: {
    stage: string
    interviewer: string
    rating: number
    strengths: string[]
    gaps: string[]
    recommendation: 'advance' | 'reject' | 'hold'
    notes: string
  }[]

  lia_parecer?: {
    summary: string
    strengths: string[]
    development_areas: string[]
    cultural_fit: number
    recommendation: string
  }

  job: {
    id: string
    title: string
    department: string
    seniority: string
    requirements: string[]
  }
}
```

### 5.3 Geração de Sugestões

A LIA analisa o contexto e gera:
- **Sub-status sugerido** — baseado na etapa e dados disponíveis
- **Mensagem personalizada** — usando template base + personalização
- **Canal recomendado** — email ou WhatsApp baseado em urgência/contexto

### 5.4 Ajuste Dinâmico

```
Sub-status alterado → LIA regenera mensagem → Preview atualizado
```

---

## 6. Matriz de Transições e Níveis de Automação

### 6.1 Matriz Completa

| De | Para | Automação | Comunicação | Sub-status LIA |
|----|------|-----------|-------------|----------------|
| Funil | Triagem | Auto | Convite WSI | `awaiting_screening_schedule` |
| Funil | Reprovado | Manual | Feedback | Analisa CV |
| Triagem | Long List | Semi | Aprovação (opcional) | `added_to_long_list` |
| Triagem | Short List | Semi | Aprovação | `added_to_short_list` |
| Triagem | Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Triagem | Reprovado | Manual | Feedback | Analisa triagem |
| Long List | Short List | Silencioso | Nenhuma | `added_to_short_list` |
| Long List | Reprovado | Manual | Feedback | Analisa contexto |
| Short List | Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Short List | Reprovado | Manual | Feedback | Analisa contexto |
| Entrevista* | Próxima Entrevista | Auto | Agendamento | `awaiting_*_schedule` |
| Entrevista* | Proposta | Semi | Proposta | `preparing_offer` |
| Entrevista* | Reprovado | Manual | Feedback | Analisa entrevista |
| Proposta | Contratado | Semi | Boas-vindas | `onboarding_scheduled` |
| Proposta | Recusada | Silencioso | Nenhuma | `accepted_other_offer` |
| Proposta | Reprovado | Manual | Feedback | `another_candidate_selected` |

### 6.2 Níveis de Automação

| Nível | Comportamento | Exemplo |
|-------|---------------|---------|
| 🟢 **Auto** | LIA executa após confirmação rápida | Convite triagem, agendamento |
| 🟡 **Semi** | LIA sugere, recrutador aceita/edita/pula | Aprovação, proposta |
| 🔴 **Manual** | LIA gera sugestão, recrutador deve revisar | Feedback de reprovação |
| ⚪ **Silencioso** | Move sem comunicação externa | Long List → Short List |

### 6.3 Regras de Transição por Tipo

**Automáticas (sem aprovação humana):**

| De | Para | Condição |
|----|------|----------|
| `sourcing.identified` | `sourcing.researching` | Sempre |
| `sourcing.contacted_*` | `sourcing.follow_up_sent` | Sem resposta 48h |
| `screening.cv_received` | `screening.cv_analyzing` | Sempre |
| `interview_*.scheduled` | `interview_*.confirmed` | Candidato confirma |
| `interview_*.completed` | `interview_*.awaiting_feedback` | Sempre |

**Semi-Automáticas (sugestão AI + aprovação):**

| De | Para | Aprovador |
|----|------|-----------|
| `sourcing.*` | `screening.*` | Recrutador |
| `screening.screening_completed` | `long_list.*` | Recrutador |
| `long_list.presented_to_manager` | `interview_manager.*` | Gestor |
| `interview_*.approved` | `offer.*` | Recrutador + Gestor |

**Manuais (apenas humano):**

| De | Para | Motivo |
|----|------|--------|
| Qualquer | `rejected.*` | Decisão final de reprovação |
| `offer.*` | `hired` | Aceite formal |
| Qualquer | `standby.*` | Banco de talentos |

---

## 7. Sistema de Templates

### 7.1 Categorias

| # | Categoria | Código | Gatilho | Tom |
|---|-----------|--------|---------|-----|
| 1 | Contato Inicial | `contato_inicial` | Funil → etapa ativa | Profissional, entusiasmado |
| 2 | Convite Triagem | `triagem` | Funil → Triagem | Acolhedor, explicativo |
| 3 | Follow-up | `follow_up` | Sem resposta X dias | Cordial, não invasivo |
| 4 | Aprovação/Avanço | `feedback_positivo` | Avanço de etapa | Celebratório, encorajador |
| 5 | Agendamento | `agendamento` | → Entrevista* | Profissional, prático |
| 6 | Proposta | `proposta` | → Proposta/Contratado | Celebratório, formal |
| 7 | Proposta Aceita | `proposta_aceita` | Proposta → Contratado | Muito celebratório |
| 8 | Feedback Construtivo | `feedback_construtivo` | → Reprovado | Respeitoso, construtivo |
| 9 | Vaga Fechada | `vaga_fechada` | Fechamento de vaga | Respeitoso, breve |

### 7.2 Mapeamento Ação → Template

```typescript
const ACTION_TO_TEMPLATE: Record<string, string> = {
  'triagem_wsi': 'triagem',
  'agendar_entrevista': 'agendamento',
  'enviar_proposta': 'proposta',
  'boas_vindas': 'proposta_aceita',
  'email_aprovacao': 'feedback_positivo',
  'whatsapp_aprovacao': 'feedback_positivo',
  'email_feedback': 'feedback_construtivo',
  'whatsapp_feedback': 'feedback_construtivo',
  'email_followup': 'follow_up',
  'whatsapp_followup': 'follow_up',
  'primeiro_contato': 'contato_inicial',
}
```

---

## 8. Geração de Mensagens pela LIA

### 8.1 Do's and Don'ts

**✅ DO's:**
- Usar nome do candidato (primeiro nome WhatsApp, completo email)
- Personalizar com dados específicos do candidato
- Em aprovações: destacar 1-2 pontos fortes observados
- Em rejeições: oferecer feedback construtivo específico
- Incluir próximos passos claros
- Para email: parágrafos curtos; Para WhatsApp: máximo 2-3 emojis

**❌ DON'Ts:**
- NÃO inventar dados que não existem no contexto
- NÃO expor scores numéricos ao candidato
- NÃO comparar com outros candidatos
- NÃO citar verbatim notas internas
- NÃO usar "infelizmente" no início de rejeições
- NÃO prometer futuras oportunidades que não existem
- NÃO dar feedback médico, psicológico ou pessoal

### 8.2 Regras de Canal

| Regra | Email | WhatsApp |
|-------|-------|----------|
| Max. palavras | 200 | 100 |
| Max. caracteres | 2.000 | 500 |
| Subject obrigatório | Sim | Não |
| Formatação | Sim | Não |
| Emojis | 0 | 3 |
| Formalidade | Formal | Semi-formal |

---

## 9. Sub-Status e Predição Automática

### 9.1 Lógica de Predição para Reprovação

```typescript
function predictRejectionSubStatus(context: CandidateContext): string {
  if (context.job.has_hired_candidate) return 'another_candidate_selected'
  if (wsi_score?.overall < 50) {
    if (wsi_score.technical < 40) return 'insufficient_technical_skills'
    if (wsi_score.behavioral < 40) return 'behavioral_concerns'
    if (wsi_score.cultural < 40) return 'cultural_fit'
  }
  if (current_stage === 'interview_technical' && techNotes?.gaps?.length > 2)
    return 'insufficient_technical_skills'
  if (current_stage.includes('manager')) return 'manager_decision'
  if (context.response_time_days > 7) return 'lack_of_interest'
  if (context.salary_expectation > context.job.salary_max * 1.2)
    return 'salary_expectation'
  return 'profile_not_aligned'
}
```

### 9.2 Mapeamento Sub-Status → Foco da Mensagem

| Sub-Status | Foco da Mensagem |
|------------|------------------|
| `another_candidate_selected` | Agradecer, competição forte, manter banco |
| `insufficient_technical_skills` | Agradecer, sugerir desenvolvimento técnico |
| `behavioral_concerns` | Agradecer, diplomático, focar em fit |
| `cultural_fit` | Agradecer, diferença de momento/estilo |
| `manager_decision` | Agradecer, decisão final do gestor |
| `salary_expectation` | Agradecer, incompatibilidade (sem valores) |
| `overqualified` | Agradecer muito, reconhecer qualificações |
| `underqualified` | Agradecer, encorajar desenvolvimento |
| `location_incompatibility` | Agradecer, questão logística |
| `lack_of_interest` | Tom neutro, desejar sucesso |

---

## 10. Backend API Endpoints

### 10.1 POST /api/automation/predict-substatus

```json
// Request
{
  "candidate_context": {
    "id": "cand_123",
    "current_stage": "interview_technical",
    "target_stage": "rejected",
    "wsi_score": { "overall": 65, "technical": 55, "behavioral": 75, "cultural": 70 },
    "interview_notes": [{ "stage": "interview_technical", "rating": 3, "gaps": ["cloud", "system design"] }]
  },
  "job_context": { "title": "Senior Backend Developer", "seniority": "senior" }
}

// Response
{
  "predicted_substatus": "insufficient_technical_skills",
  "confidence": 0.85,
  "reasoning": "Gaps em cloud e arquitetura, requisitos críticos para a senioridade",
  "alternatives": [{ "substatus": "profile_not_aligned", "confidence": 0.12 }]
}
```

### 10.2 POST /api/automation/generate-message

```json
// Request
{
  "candidate_context": { "..." },
  "job_context": { "..." },
  "message_type": "feedback_construtivo",
  "substatus": "insufficient_technical_skills",
  "channel": "email",
  "template_id": "default-feedback-email"
}

// Response
{
  "subject": "Retorno sobre sua candidatura - Senior Backend Developer",
  "body": "Olá João,\n\nAgradecemos muito sua participação...",
  "metadata": { "personalization_points": ["..."], "tokens_used": 450 }
}
```

### 10.3 POST /api/automation/regenerate-for-substatus

```json
// Request
{
  "original_message": "Olá João, agradecemos...",
  "new_substatus": "another_candidate_selected",
  "candidate_context": { "..." }
}

// Response
{
  "body": "Olá João,\n\nAgradecemos... decidimos avançar com outro candidato...",
  "changes_made": ["Alterado motivo", "Mantido reconhecimento de pontos fortes"]
}
```

### 10.4 POST /api/automation/execute-transition

```json
// Request
{
  "transitions": [
    { "candidate_id": "cand_123", "from_stage": "interview_technical", "to_stage": "rejected",
      "substatus": "insufficient_technical_skills", "action": "email", "message": { "subject": "...", "body": "..." } }
  ],
  "job_vacancy_id": "job_789"
}

// Response
{
  "success": true,
  "results": [{ "candidate_id": "cand_123", "stage_updated": true, "message_sent": true }],
  "alerts_triggered": [{ "type": "bell", "recipient": "recruiter@company.com" }]
}
```

---

## 11. Integração com Pipeline Stage Service

```python
from app.services.pipeline_stage_service import PipelineStageService

service = PipelineStageService()

result = await service.transition_candidate(
    vacancy_candidate_id="...",
    to_stage="long_list",
    to_sub_status="added_to_long_list",
    triggered_by="interviewer_agent",
    source_agent="interviewer",
    reason="Triagem WhatsApp concluída com score 85/100",
    context={
        "wsi_score": 85,
        "interview_duration_minutes": 12,
        "sentiment": "positive",
        "recommendation": "Excelente fit técnico"
    }
)
```

---

## 12. Frontend — Componentes e Hooks

### 12.1 SmartTransitionModal

Modal principal ao mover candidato(s) de etapa.

```typescript
interface SmartTransitionModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: CandidateForTransition[]
  fromStage: string
  toStage: string
  jobVacancy: JobVacancy
  companyId: string
  onConfirm: (result: TransitionResult) => Promise<void>
  onCancel: () => void
}
```

**Estados internos:** mode (`single | bulk`), personalizationType (`template | lia_personalized`), selectedAction, subStatusByCandidate, messagesByCandidate, isGenerating, isSubmitting, channel.

**Fluxo:**
1. Ao abrir → determinar ações disponíveis + prever sub-status
2. Exibir preview com sub-status editável
3. Ao mudar sub-status → regenerar mensagem automaticamente
4. Confirmar → executar transição

### 12.2 useTransitionContext Hook

```typescript
interface UseTransitionContextReturn {
  availableActions: TransitionAction[]
  predictedSubStatuses: Record<string, string>
  updateSubStatus: (candidateId: string, subStatus: string) => void
  messages: Record<string, GeneratedMessage>
  generateMessages: (personalized: boolean) => Promise<void>
  regenerateMessage: (candidateId: string) => Promise<void>
  updateMessage: (candidateId: string, body: string) => void
  isGenerating: boolean
  error: string | null
}
```

### 12.3 Regras de Automação por Transição

```typescript
const TRANSITION_RULES: Record<string, AutomationRule> = {
  'sourcing_to_screening': {
    defaultAction: 'triagem_wsi', autoSend: true, requireConfirmation: true,
    suggestChannel: 'email', allowSkip: false
  },
  'any_to_rejected': {
    defaultAction: 'email_feedback', autoSend: false, requireConfirmation: true,
    suggestChannel: 'email', allowSkip: true, requireReview: true
  },
  'long_list_to_short_list': {
    defaultAction: 'apenas_mover', autoSend: false, requireConfirmation: false,
    allowSkip: true, silent: true
  },
}
```

---

## 13. Ações em Lote (Bulk Actions)

### 13.1 Fluxo

1. Recrutador seleciona múltiplos candidatos
2. Escolhe ação (ex: mover para Reprovado)
3. Modal abre com lista + opção: Template padrão vs Personalizado LIA
4. Se "Personalizado": LIA gera mensagem única para cada candidato
5. Recrutador pode editar individualmente
6. Confirmação envia todas as mensagens

### 13.2 API de Geração em Lote

Endpoint: `POST /api/automation/generate-bulk`
- Processamento paralelo (batches de 5)
- Loading progressivo
- Streaming de resultados

### 13.3 Performance

- Cache de contexto de candidatos (5 min TTL)
- Batch processing (lotes de 5)
- Lazy loading de previews em bulk
- Debounce 300ms na mudança de sub-status

---

## 14. Alertas e Integrações

### 14.1 Bell (Notificações Internas)

| Evento | Destinatário | Prioridade |
|--------|--------------|------------|
| Triagem WSI concluída | Recrutador responsável | Alta |
| Candidato avançou | Próximo entrevistador | Média |
| Entrevista agendada | Entrevistador | Alta |
| Prazo expirando | Recrutador | Alta |
| Proposta aceita | Gestor + RH | Alta |

### 14.2 Microsoft Teams

| Evento | Canal/Pessoa | Formato |
|--------|--------------|---------|
| Entrevista técnica agendada | Canal time técnico | Card |
| Proposta aprovada | Canal Recrutamento | Anúncio |
| Contratação concluída | Canal geral | Celebração |
| Candidato finalista | Gestor direto (DM) | Card resumo |

---

## 15. Configurações por Empresa

```typescript
interface CompanyAutomationConfig {
  automation_levels: {
    sourcing_to_screening: 'auto' | 'semi' | 'manual'
    screening_to_interview: 'auto' | 'semi' | 'manual'
    any_to_rejected: 'auto' | 'semi' | 'manual'
  }
  channels: { email: boolean; whatsapp: boolean; teams: boolean; bell: boolean }
  communication: {
    default_channel: 'email' | 'whatsapp'
    require_review_for_rejection: boolean
    auto_send_interview_invites: boolean
  }
  custom_templates: { rejection_footer?: string; company_signature?: string }
}
```

---

## 16. Prompts de Sistema (LIA Agent Service)

### 16.1 Predição de Sub-Status

```python
SUBSTATUS_PREDICTION_PROMPT = """
Você é um especialista em recrutamento analisando contexto de candidato
para determinar o motivo mais apropriado da transição de etapa.

CANDIDATO: {candidate_name}
ETAPA: {current_stage} → {target_stage}
AVALIAÇÕES: {evaluations}
NOTAS ENTREVISTA: {interview_notes}
PARECER LIA: {lia_parecer}
VAGA: {job_title} ({seniority})
SUB-STATUS DISPONÍVEIS: {available_substatuses}

Responda em JSON:
{ "predicted_substatus": "...", "confidence": 0.0-1.0, "reasoning": "..." }
"""
```

### 16.2 Geração de Mensagem

```python
MESSAGE_GENERATION_PROMPT = """
Você é LIA, assistente de recrutamento da WeDoTalent.

CANDIDATO: {candidate_name} | {email}
VAGA: {job_title}
TRANSIÇÃO: {from_stage} → {to_stage}
MOTIVO: {substatus_display_name}
CANAL: {channel}
TEMPLATE BASE: {template_base}

REGRAS:
1. Tom profissional mas acolhedor
2. Personalizar com dados reais
3. Máximo {max_words} palavras
4. Seguir Do's and Don'ts
"""
```

### 16.3 Ajuste de Mensagem

```python
MESSAGE_ADJUSTMENT_PROMPT = """
Ajustar mensagem porque motivo da transição mudou.

MENSAGEM ORIGINAL: {original_message}
MOTIVO ANTERIOR: {old_substatus}
NOVO MOTIVO: {new_substatus}

Altere apenas trechos que mencionam o motivo. Manter estrutura e tom.
"""
```

---

## 17. Métricas e Analytics

| Métrica | Descrição |
|---------|-----------|
| Tempo médio por transição | Segundos gastos pelo recrutador |
| Taxa de aceitação LIA | % sugestões aceitas sem edição |
| Taxa de edição | % mensagens editadas antes do envio |
| NPS do candidato | Satisfação com comunicação |
| Volume mensagens/dia | Throughput do sistema |
| Erros de envio | Taxa de falhas |

**Metas com AI:**

| Métrica | Baseline | Meta |
|---------|----------|------|
| Time-to-hire | 44 dias | 11-22 dias |
| Tempo de screening | Dias | Horas |
| Eficiência recrutador | Baseline | +41% |
| Qualidade contratação | Baseline | +35% |

---

## 18. Compliance

### 18.1 LGPD / GDPR
- Decisões automatizadas devem ter explicabilidade
- Candidato pode solicitar revisão humana de qualquer decisão AI
- Logs de decisão mantidos por 5 anos

### 18.2 EU AI Act (Alto Risco)
- Recrutamento classificado como "alto risco"
- Documentação, auditoria, supervisão humana obrigatórias
- Decisões finais (rejeição, contratação) requerem aprovação humana

### 18.3 Bias Mitigation
- Monitorar disparate impact por grupo demográfico
- Auditorias trimestrais de fairness
- Treinamento diversificado dos modelos

---

## 19. Roadmap de Implementação

### Fase 1: MVP — Modal de Transição Inteligente
**Duração:** 8-12 horas | **Prioridade:** Alta

- Backend: APIs predict-substatus, generate-message, regenerate-for-substatus
- Frontend: SmartTransitionModal + useTransitionContext hook
- Integração no Kanban (handleDrop) e Tabela (InteractiveStageCell)
- Feature flags: `smart_transition_modal`, `lia_substatus_prediction`, `lia_message_personalization`, `substatus_dynamic_adjustment`

**Critérios de sucesso:**
- Todas transições passam pelo SmartTransitionModal
- Sub-status com >80% acurácia
- Mensagens geradas em <3 segundos
- Ajuste dinâmico ao mudar sub-status

### Fase 2: Ações em Lote
**Duração:** 6-8 horas | **Prioridade:** Média

- API generate-bulk com processamento paralelo
- SmartTransitionModal expandido para bulk (até 20 candidatos)
- Geração completa em <30 segundos para 20 candidatos

### Fase 3: Integrações e Analytics
**Duração:** 8-10 horas | **Prioridade:** Baixa

- Sistema de alertas (Bell + Teams)
- Central de notificações no header
- Dashboard de métricas de automação

### Fase 4: Evolução Contínua

- Aprendizado: LIA melhora baseada em edições do recrutador
- Sugestão proativa: LIA sugere ações baseada em padrões
- Automação condicional: regras customizáveis

---

## 20. Dependências Técnicas

| Camada | Tecnologia | Status |
|--------|------------|--------|
| Backend | FastAPI | Instalado |
| LLM | Anthropic Claude API | Integrado |
| Validação | Pydantic | Instalado |
| Frontend | React + TypeScript | Configurado |
| Componentes | Radix UI / shadcn/ui | Instalado |
| Data fetching | SWR | Instalado |

---

*Documento unificado em: Março 2026*
*Versão: 2.0 (consolida SYSTEM + IMPLEMENTATION_PLAN + DEVELOPMENT_GUIDE + AI_STAGE_AUTOMATION_ARCHITECTURE)*
