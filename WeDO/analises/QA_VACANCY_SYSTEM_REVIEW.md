# QA Review - Sistema de Vagas LIA Plataforma
**Data:** 2026-01-20  
**Versão:** 1.0  
**Status:** Revisão Completa

---

## 1. FLUXO COMPLETO DE VIDA DE UMA VAGA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CICLO DE VIDA DA VAGA                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CRIAÇÃO    │───▶│   APROVAÇÃO  │───▶│  PUBLICAÇÃO  │───▶│    ATIVA     │
│  (Rascunho)  │    │  (Pendente)  │    │  (LinkedIn,  │    │ (Recebendo   │
│              │    │              │    │   Indeed)    │    │ candidatos)  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
 ┌───────────┐      ┌───────────┐       ┌───────────┐       ┌───────────┐
 │ LIA Chat  │      │ Manager   │       │ Job Board │       │ Sourcing  │
 │ Wizard    │      │ Approval  │       │ Publish   │       │ Agent     │
 └───────────┘      └───────────┘       └───────────┘       └───────────┘
                                                                   │
       ┌───────────────────────────────────────────────────────────┘
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PAUSADA    │◀──▶│  CONCLUÍDA   │    │  ARQUIVADA   │    │  CANCELADA   │
│              │    │  (Contratou) │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 2. FLUXO DO CANDIDATO NO PIPELINE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DO CANDIDATO NA VAGA                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ENTRADA DO CANDIDATO (3 Canais)
  ═══════════════════════════════
  
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  LinkedIn   │   │   Indeed    │   │  WhatsApp   │
  │  Apply      │   │   Apply     │   │  Channel    │
  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
         │                 │                 │
         │                 │                 ▼
         │                 │          ┌─────────────┐
         │                 │          │ LGPD        │
         │                 │          │ Consent     │
         │                 │          └──────┬──────┘
         │                 │                 │
         │                 │                 ▼
         │                 │          ┌─────────────┐
         │                 │          │ CV Upload   │
         │                 │          │ + Parse     │
         │                 │          └──────┬──────┘
         │                 │                 │
         │                 │                 ▼
         │                 │          ┌─────────────┐
         │                 │          │ Screening   │
         │                 │          │ Questions   │
         │                 │          └──────┬──────┘
         │                 │                 │
         └────────────────┴────────────────┘
                           │
                           ▼
                 ┌─────────────────┐
                 │ VacancyCandidate│  ◀── Dispara: CANDIDATE_APPLIED
                 │ stage=screening │
                 │ source=channel  │
                 └────────┬────────┘
                          │
  ════════════════════════▼════════════════════════════════════════════════════
                    PIPELINE AUTOMATIZADO
  ════════════════════════════════════════════════════════════════════════════
  
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │  TRIAGEM    │───▶│ ENTREVISTA  │───▶│ ENTREVISTA  │───▶│ PROPOSTA    │
  │ (Screening) │    │    RH       │    │  TÉCNICA    │    │  (Offer)    │
  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
   ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
   │ Ag.3: CV  │     │ Ag.4:     │     │ Ag.5: WSI │     │ Ag.7:     │
   │ Screening │     │ Interviewer│    │ Evaluator │     │ Analyst   │
   └───────────┘     └───────────┘     └───────────┘     └───────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
   ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
   │ CV Score  │     │ Scheduling│     │ WSI Score │     │ Feedback  │
   │ + Rubric  │     │ Agent     │     │ + Parecer │     │ + Report  │
   └───────────┘     └───────────┘     └───────────┘     └───────────┘
                                                               │
                                                               ▼
                                                        ┌─────────────┐
                                                        │ CONTRATADO  │
                                                        │  (Hired)    │
                                                        └─────────────┘
```

---

## 3. AUTOMAÇÕES E TRIGGERS

### 3.1 Tipos de Trigger (TriggerType)

| Trigger | Descrição | Handler Sugerido |
|---------|-----------|------------------|
| `CANDIDATE_APPLIED` | Candidato se candidatou | `start_screening` |
| `SCREENING_COMPLETED` | Triagem concluída | `move_to_interview` |
| `INTERVIEW_SCHEDULED` | Entrevista agendada | `send_confirmation` |
| `INTERVIEW_COMPLETED` | Entrevista realizada | `generate_parecer` |
| `CANDIDATE_INACTIVE` | Candidato inativo | `send_followup` |
| `CANDIDATE_NO_SHOW` | No-show em entrevista | `reschedule_or_reject` |
| `OFFER_SENT` | Proposta enviada | `monitor_response` |
| `CANDIDATE_HIRED` | Contratação efetivada | `sync_ats_onboarding` |
| `CANDIDATE_REJECTED` | Candidato reprovado | `send_feedback_talent_pool` |
| `STAGE_CHANGED` | Mudança de etapa | `notify_stakeholders` |
| `NO_RESPONSE_48H` | Sem resposta 48h | `send_reminder` |
| `FEEDBACK_RECEIVED` | Feedback recebido | `process_feedback` |
| `DEADLINE_APPROACHING` | Prazo se aproximando | `alert_recruiter` |
| `ATS_SYNC` | Sincronização ATS | `sync_status` |

### 3.2 Status de Vaga

| Status | Descrição | Transições Permitidas |
|--------|-----------|----------------------|
| `Rascunho` | Em criação | Aprovação, Cancelada |
| `Pendente Aprovação` | Aguardando gestor | Aprovada, Rejeitada |
| `Aprovada` | Pronta para publicar | Ativa, Rascunho |
| `Ativa` | Recebendo candidatos | Pausada, Concluída |
| `Pausada` | Temporariamente parada | Ativa, Cancelada |
| `Concluída` | Posição preenchida | Arquivada |
| `Cancelada` | Vaga cancelada | Arquivada |
| `Arquivada` | Histórico | - |

### 3.3 Etapas do Pipeline (Configuráveis por Empresa)

| Etapa Default | Ordem | Tipo | SLA (horas) |
|---------------|-------|------|-------------|
| Sourcing | 1 | active | 72 |
| Screening | 2 | active | 48 |
| Entrevista RH | 3 | active | 72 |
| Entrevista Técnica | 4 | active | 72 |
| Entrevista Gestor | 5 | active | 72 |
| Proposta | 6 | active | 48 |
| Contratado | 7 | final | - |
| Reprovado | 8 | rejection | - |

---

## 4. AGENTES ENVOLVIDOS

| Agente | Responsabilidade na Vaga |
|--------|-------------------------|
| **Ag.1: Job Planner** | Criação, atualização, fechamento de vagas |
| **Ag.2: Sourcing** | Busca proativa de candidatos, boolean queries |
| **Ag.3: CV Screening** | Triagem curricular, scoring inicial |
| **Ag.4: Interviewer** | Condução de entrevistas WSI |
| **Ag.5: WSI Evaluator** | Cálculo de WSI Score, parecer |
| **Ag.6: Scheduling** | Agendamento de entrevistas |
| **Ag.7: Analyst & Feedback** | KPIs, feedback, comunicação |
| **Ag.8: ATS Integrator** | Sincronização com ATS externos |

---

## 5. CAMPOS DA VAGA - ANÁLISE COMPLETA

### 5.1 Informações Básicas
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `title` | String(255) | ✅ Sim | ✅ |
| `department` | String(100) | Não | ✅ |
| `location` | String(255) | Não | ✅ |
| `work_model` | Enum | Não | ✅ |
| `employment_type` | Enum | Não | ✅ |
| `seniority_level` | Enum | Não | ✅ |

### 5.2 Descrição e Requisitos
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `description` | Text | Não | ✅ |
| `requirements` | Array[String] | Não | ✅ |
| `technical_requirements` | JSON | Não | ✅ |
| `behavioral_competencies` | JSON | Não | ✅ |
| `languages` | JSON | Não | ✅ |

### 5.3 Remuneração
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `salary` | String | Não | ✅ |
| `salary_range` | JSON | Não | ✅ |
| `benefits` | Array[String] | Não | ✅ |

### 5.4 Pessoas e Aprovação
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `manager` | String | Não | ✅ |
| `manager_email` | String | Não | ✅ |
| `recruiter` | String | Não | ✅ |
| `recruiter_email` | String | Não | ✅ |
| `created_by` | String | Não | ✅ |
| `approval_status` | Enum | Não | ✅ |
| `approved_by` | String | Não | ✅ |

### 5.5 Publicação e Visibilidade
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `visibility` | Enum | Não | ✅ |
| `is_confidential` | Boolean | Não | ✅ |
| `access_list` | Array[String] | Não | ✅ |
| `masked_company_name` | String | Não | ✅ |
| `public_slug` | String | Não | ✅ |
| `published_linkedin` | Boolean | Não | ✅ |
| `published_indeed` | Boolean | Não | ✅ |
| `published_website` | Boolean | Não | ✅ |

### 5.6 Processo Seletivo
| Campo | Tipo | Obrigatório | Implementado |
|-------|------|-------------|--------------|
| `interview_stages` | JSON | Não | ✅ |
| `screening_questions` | JSON | Não | ✅ |
| `governance_rules` | JSON | Não | ✅ |
| `timeline` | JSON | Não | ✅ |
| `screening_config` | JSON | Não | ✅ |

---

## 6. CANAIS DE NOTIFICAÇÃO

| Canal | Implementado | Uso |
|-------|--------------|-----|
| Chat LIA | ✅ | Mensagens inline no chat |
| Bell (In-App) | ✅ | Notificações no sino |
| Email | ✅ | Comunicações formais |
| WhatsApp | ✅ | Candidatos e recrutadores |
| Teams | ✅ | Integração empresarial |
| Push | ✅ | Browser notifications |

---

## 7. TEMPLATES DE PIPELINE PADRÃO

| Template | Etapas | SLA Total | Uso |
|----------|--------|-----------|-----|
| Tech Standard | 6 etapas | 21 dias | Vagas técnicas |
| Fast Track | 4 etapas | 7 dias | Vagas urgentes |
| Executive | 6 etapas | 35 dias | C-Level |
| Estágio | 4 etapas | 14 dias | Programa trainee |
| Operacional | 4 etapas | 10 dias | Operações |

---

## 8. INTEGRAÇÕES

### 8.1 Job Boards
| Plataforma | Status | Método |
|------------|--------|--------|
| LinkedIn | Mock Mode | OAuth API (requer aprovação) |
| Indeed | ✅ Produção | XML Feed |
| Website | ✅ | Página pública |

### 8.2 ATS
| ATS | Status | Método |
|-----|--------|--------|
| Gupy | ✅ Implementado | API REST |
| Pandapé | ✅ Implementado | API REST |
| StackOne | ✅ Implementado | Unified API |
| Merge | ✅ Implementado | Unified API |

### 8.3 Comunicação
| Serviço | Status | Uso |
|---------|--------|-----|
| SendGrid | ✅ | Email |
| Resend | ✅ | Email alternativo |
| Meta Cloud API | ✅ | WhatsApp direto |
| Twilio | ✅ | WhatsApp (fallback) |
| Microsoft Graph | ✅ | Teams + Calendar |

---

## 9. ANÁLISE DE GAPS E PENDÊNCIAS

### 9.1 ✅ TODAS PENDÊNCIAS IMPLEMENTADAS (2026-01-20)

| Item | Descrição | Prioridade | Status |
|------|-----------|------------|--------|
| 1 | **Validação de campos obrigatórios no wizard** | Média | ✅ Implementado |
| 2 | **Templates de email para cada etapa** | Média | ✅ 10 templates criados |
| 3 | **Webhook de atualização de status para ATS** | Alta | ✅ Com HMAC + retry |
| 4 | **Relatório de funil por vaga exportável (PDF/Excel)** | Baixa | ✅ Implementado |
| 5 | **Histórico de alterações da vaga (audit log detalhado)** | Média | ✅ Field-level tracking |
| 6 | **Bulk actions para múltiplas vagas** | Baixa | ✅ 5 endpoints criados |

### 9.2 ✅ FUNCIONALIDADES COMPLETAS

| Funcionalidade | Status | Observações |
|----------------|--------|-------------|
| CRUD de Vagas | ✅ | Create, Read, Update, Delete (soft) |
| Duplicação de Vaga | ✅ | POST /job-vacancies/{id}/duplicate |
| Arquivamento | ✅ | DELETE (soft delete → Arquivada) |
| Publicação LinkedIn/Indeed | ✅ | LinkedIn mock, Indeed XML |
| Link público + view counter | ✅ | Com slug SEO-friendly |
| Templates de pipeline | ✅ | 5 templates padrão |
| Benefícios da empresa | ✅ | 25 benefícios BR |
| Perguntas de triagem | ✅ | 8 perguntas padrão |
| Sourcing Agent | ✅ | 12 ações implementadas |
| Analytics de vaga | ✅ | Funil, tempo, fonte |
| Automação de stages | ✅ | 14 triggers implementados |
| WhatsApp channel | ✅ | Com LGPD + pipeline integration |
| Multi-tenancy | ✅ | company_id em todas as queries |

---

## 10. RECOMENDAÇÕES DE IMPLEMENTAÇÃO

### 10.1 Alta Prioridade

1. **Webhook de Status para ATS**
   - Disparar webhook quando status muda
   - Payload: job_id, old_status, new_status, timestamp
   - Retry com backoff exponencial

### 10.2 Média Prioridade

2. **Templates de Email por Etapa**
   - Criar templates default para cada transição
   - Permitir customização por empresa
   - Variáveis: {{candidate_name}}, {{job_title}}, {{next_step}}

3. **Audit Log de Vaga (Detalhado)**
   - Registrar todas as alterações de campos
   - Campos: field_changed, old_value, new_value, changed_by, timestamp
   - Endpoint: GET /job-vacancies/{id}/history

### 10.3 Baixa Prioridade

4. **Bulk Actions**
   - Pausar múltiplas vagas
   - Arquivar múltiplas vagas
   - Alterar recrutador de múltiplas vagas

5. **Export de Relatório**
   - PDF com funil e métricas
   - Excel com dados detalhados
   - Agendamento periódico

---

## 11. FLUXO DE APROVAÇÃO DE VAGA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE APROVAÇÃO                                   │
└─────────────────────────────────────────────────────────────────────────────┘

   Recrutador                    Gestor                      Sistema
   ──────────                    ──────                      ───────
       │                           │                            │
       │   Cria vaga (Rascunho)    │                            │
       ├──────────────────────────▶│                            │
       │                           │                            │
       │   Solicita aprovação      │                            │
       ├──────────────────────────▶│                            │
       │                           │                            │
       │                           │   Notificação Bell+Email   │
       │                           │◀───────────────────────────┤
       │                           │                            │
       │                           │   Revisa dados da vaga     │
       │                           ├───────────────────────────▶│
       │                           │                            │
       │                     ┌─────┴─────┐                      │
       │                     │ Aprovado? │                      │
       │                     └─────┬─────┘                      │
       │                           │                            │
       │             ┌─────────────┼─────────────┐              │
       │             ▼             │             ▼              │
       │      ┌──────────┐         │      ┌──────────┐          │
       │      │   SIM    │         │      │   NÃO    │          │
       │      └────┬─────┘         │      └────┬─────┘          │
       │           │               │           │                │
       │           ▼               │           ▼                │
       │    Status: Aprovada       │    Status: Rejeitada       │
       │    + Notificação          │    + Motivo + Notificação  │
       │           │               │           │                │
       │           ▼               │           ▼                │
       │    Pode publicar          │    Voltar para Rascunho    │
       │                           │                            │
```

---

## 12. ESTRUTURA DE DADOS JSON

### 12.1 technical_requirements
```json
[
  {
    "category": "Linguagens de Programação",
    "technology": "Python",
    "level": "Avançado",
    "required": true,
    "years_experience": 3
  }
]
```

### 12.2 salary_range
```json
{
  "min": 12000,
  "max": 18000,
  "currency": "BRL",
  "frequency": "monthly",
  "bonus": {
    "type": "PLR",
    "target": 3,
    "frequency": "yearly"
  }
}
```

### 12.3 interview_stages
```json
[
  {
    "stageName": "Entrevista RH",
    "stageOrder": 1,
    "interviewers": ["Ana Silva", "João Costa"],
    "format": "Comportamental",
    "duration": 45,
    "schedulingWindow": "Terças e Quintas à tarde",
    "hasScript": true
  }
]
```

### 12.4 governance_rules
```json
{
  "autoScheduleInterviews": true,
  "autoSendNegativeFeedback": true,
  "autoAdvanceApproved": false,
  "requireManagerApproval": true,
  "minInterviewers": 2,
  "maxDaysInStage": 7
}
```

### 12.5 screening_config
```json
{
  "channels": {
    "whatsapp": true,
    "voice": true,
    "video": false
  },
  "settings": {
    "maxQuestions": 10,
    "timeoutMinutes": 30
  },
  "metrics": {
    "minScore": 60,
    "autoReject": true
  },
  "scheduling": {
    "availableSlots": ["09:00-12:00", "14:00-18:00"],
    "timezone": "America/Sao_Paulo"
  }
}
```

---

## 13. CHECKLIST FINAL DE QA

### Funcionalidades Core
- [x] Criar vaga via wizard
- [x] Criar vaga via chat LIA
- [x] Editar vaga existente
- [x] Publicar em job boards
- [x] Gerar link público
- [x] Configurar etapas do processo
- [x] Definir perguntas de triagem
- [x] Adicionar benefícios
- [x] Solicitar aprovação
- [x] Duplicar vaga existente
- [x] Arquivar vaga (soft delete)
- [x] Visualizar analytics

### Automações
- [x] Trigger CANDIDATE_APPLIED
- [x] Trigger SCREENING_COMPLETED
- [x] Trigger INTERVIEW_SCHEDULED
- [x] Trigger STAGE_CHANGED
- [x] Sugestões de IA para aprovação
- [x] Notificações multi-canal

### Integrações
- [x] Sincronização ATS
- [x] Indeed XML Feed
- [x] LinkedIn (mock)
- [x] WhatsApp candidatos
- [x] Email templates

### Multi-tenancy
- [x] company_id em todas queries
- [x] Isolamento de dados
- [x] Validação de acesso

---

## 14. PRÓXIMOS PASSOS RECOMENDADOS

1. **Implementar endpoint de duplicação** - Prioridade alta para produtividade
2. **Revisar templates de email** - Garantir cobertura de todos os cenários
3. **Testar fluxo WhatsApp end-to-end** - Validar LGPD + pipeline
4. **Configurar webhooks de status** - Para clientes com ATS próprio
5. **Adicionar export de relatórios** - PDF e Excel para gestores

---

*Documento gerado automaticamente pelo sistema de QA da Plataforma LIA*
