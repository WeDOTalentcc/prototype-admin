# Workflow de Congelamento de Vaga

## Visão Geral

O congelamento de vaga é um fluxo crítico que pausa temporariamente um processo seletivo. Este documento define como cada agente deve atuar quando receber o evento `JOB_FREEZE_REQUESTED`.

---

## Evento Trigger

```python
class JobFreezeEvent:
    event_type: str = "JOB_FREEZE_REQUESTED"
    job_id: str                          # UUID da vaga
    job_title: str                       # Título da vaga
    job_code: str                        # Código da vaga (ex: WDT-123)
    company_id: str                      # UUID da empresa
    recruiter_id: str                    # UUID do recrutador
    freeze_reason: str                   # Código do motivo
    freeze_reason_label: str             # Label do motivo (para exibição)
    unfreeze_date: Optional[datetime]    # Data prevista de descongelamento
    notify_candidates: bool              # Se deve notificar candidatos
    requested_at: datetime               # Timestamp da solicitação
```

### Motivos de Congelamento (freeze_reason)

| Código | Label | Descrição |
|--------|-------|-----------|
| `budget_review` | Revisão orçamentária | Orçamento da vaga em análise |
| `headcount_freeze` | Congelamento de headcount | Empresa pausou contratações |
| `restructuring` | Reestruturação da área | Área passando por mudanças |
| `position_redefinition` | Redefinição do perfil | Requisitos da vaga em revisão |
| `internal_transfer` | Possível transferência interna | Avaliando candidato interno |
| `vacation_period` | Período de férias do gestor | Gestor ausente temporariamente |
| `other` | Outro motivo | Motivo não listado |

---

## Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                         │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  1. Recebe JOB_FREEZE_REQUESTED                                              │
│  2. Valida pré-requisitos (candidatos em Proposta?)                          │
│  3. SE bloqueado → Emite JOB_FREEZE_BLOCKED                                  │
│  4. SE ok → Atualiza status da vaga para "Paralisada"                        │
│  5. Dispara agentes em PARALELO                                              │
│                                                                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐               │
│  │  SCHEDULING  │  SCREENING   │   SOURCING   │  EVALUATION  │               │
│  │    AGENT     │    AGENT     │    AGENT     │    AGENT     │               │
│  └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘               │
│         │              │              │              │                       │
│         ▼              ▼              ▼              ▼                       │
│  Cancela          Pausa          Pausa          Cancela                      │
│  entrevistas      triagem        sourcing       testes                       │
│                                                                              │
│  6. Aguarda conclusão (timeout: 30s)                                         │
│  7. Consolida resultados                                                     │
│  8. Dispara COMMUNICATION AGENT                                              │
│  9. Agenda lembrete de descongelamento                                       │
│  10. Emite JOB_FREEZE_COMPLETED                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Responsabilidades por Agente

### 1. ORCHESTRATOR (orchestrator.py)

**Arquivo:** `lia-agent-system/app/orchestrator/orchestrator.py`

**Handler:** `handle_job_freeze_request(event: JobFreezeEvent)`

```python
async def handle_job_freeze_request(self, event: JobFreezeEvent) -> JobFreezeResult:
    """
    Orquestra o fluxo completo de congelamento de vaga.
    
    Passos:
    1. Validar pré-requisitos (nenhum candidato em Proposta)
    2. Atualizar status da vaga para "Paralisada"
    3. Gravar freeze_reason e unfreeze_date na vaga
    4. Disparar agentes em paralelo
    5. Aguardar resultados
    6. Consolidar e enviar para Communication Agent
    7. Agendar notificação proativa para unfreeze_date
    8. Registrar auditoria
    
    Returns:
        JobFreezeResult com status e detalhes das ações
    """
    pass
```

**Validação de Bloqueio:**
```python
async def validate_freeze_prerequisites(self, job_id: str) -> FreezeValidation:
    """
    Verifica se a vaga pode ser congelada.
    
    Regras:
    - BLOQUEIA se houver candidatos em etapa "Proposta"
    - PERMITE em qualquer outra etapa
    
    Returns:
        FreezeValidation(
            can_freeze: bool,
            blocking_reason: Optional[str],
            candidates_in_proposal: List[CandidateInfo]
        )
    """
    candidates_in_proposal = await self.db.get_candidates_by_stage(
        job_id=job_id, 
        stage="Proposta"
    )
    
    if candidates_in_proposal:
        return FreezeValidation(
            can_freeze=False,
            blocking_reason="Existem candidatos em etapa de Proposta",
            candidates_in_proposal=candidates_in_proposal
        )
    
    return FreezeValidation(can_freeze=True)
```

**Eventos Emitidos:**

| Evento | Quando | Payload |
|--------|--------|---------|
| `JOB_FREEZE_STARTED` | Início do processo | job_id, timestamp |
| `JOB_FREEZE_BLOCKED` | Há candidatos em Proposta | job_id, candidates_count, candidates |
| `JOB_FREEZE_COMPLETED` | Sucesso | job_id, summary |
| `JOB_FREEZE_FAILED` | Erro em algum agente | job_id, error, partial_results |

---

### 2. SCHEDULING AGENT (scheduling_agent.py)

**Arquivo:** `lia-agent-system/app/agents/specialized/scheduling_agent.py`

**Handler:** `handle_job_freeze(job_id: str) -> SchedulingFreezeResult`

**Responsabilidades:**

1. **Buscar entrevistas agendadas**
   - Query: `interviews WHERE job_id = ? AND scheduled_date >= NOW() AND status = 'scheduled'`

2. **Cancelar eventos no calendário**
   - Integração: Microsoft Graph API
   - Endpoint: `DELETE /me/events/{event_id}`
   - Autenticação: Azure AD OAuth

3. **Atualizar status das entrevistas**
   - Novo status: `cancelled_job_frozen`
   - Gravar: `cancelled_at`, `cancellation_reason`

4. **Retornar lista de afetados**

```python
async def handle_job_freeze(self, job_id: str) -> SchedulingFreezeResult:
    """
    Cancela todas as entrevistas futuras da vaga congelada.
    
    Integrações:
    - Microsoft Graph API (DELETE /me/events/{event_id})
    - Secrets: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
    
    Returns:
        SchedulingFreezeResult(
            cancelled_interviews: List[CancelledInterview],
            total_cancelled: int,
            calendar_events_deleted: int,
            errors: List[str]
        )
    """
    interviews = await self.db.get_scheduled_interviews(
        job_id=job_id,
        min_date=datetime.now(),
        status="scheduled"
    )
    
    results = []
    for interview in interviews:
        try:
            # Cancelar no Microsoft Graph
            await self.graph_client.delete_event(interview.calendar_event_id)
            
            # Atualizar no banco
            await self.db.update_interview_status(
                interview_id=interview.id,
                status="cancelled_job_frozen",
                cancellation_reason="Vaga congelada"
            )
            
            results.append(CancelledInterview(
                candidate_id=interview.candidate_id,
                candidate_name=interview.candidate_name,
                candidate_email=interview.candidate_email,
                interview_date=interview.scheduled_date,
                interview_type=interview.interview_type
            ))
        except Exception as e:
            self.logger.error(f"Erro ao cancelar entrevista {interview.id}: {e}")
    
    return SchedulingFreezeResult(
        cancelled_interviews=results,
        total_cancelled=len(results),
        calendar_events_deleted=len(results)
    )
```

---

### 3. SCREENING AGENT (screening_agent.py)

**Arquivo:** `lia-agent-system/app/agents/specialized/screening_agent.py`

**Handler:** `handle_job_freeze(job_id: str) -> ScreeningFreezeResult`

**Responsabilidades:**

1. **Pausar triagens automáticas**
   - Atualizar: `vacancy.auto_screening_enabled = False`

2. **Pausar respostas LIA WhatsApp**
   - Adicionar job_id à lista `frozen_jobs` no Redis
   - LIA verificará esta lista antes de responder sobre a vaga

3. **Cancelar follow-ups pendentes**
   - Remover jobs agendados do Celery/scheduler
   - Query: `scheduled_tasks WHERE job_id = ? AND task_type = 'followup'`

4. **Retornar candidatos em triagem**

```python
async def handle_job_freeze(self, job_id: str) -> ScreeningFreezeResult:
    """
    Pausa triagens automáticas e configura LIA para responder sobre vaga congelada.
    
    Quando vaga está na lista frozen_jobs:
    - LIA NÃO faz perguntas de triagem
    - LIA NÃO agenda entrevistas
    - LIA RESPONDE: "O processo seletivo está temporariamente pausado..."
    
    Returns:
        ScreeningFreezeResult(
            paused_screenings: int,
            paused_followups: int,
            candidates_in_screening: List[CandidateScreeningInfo]
        )
    """
    # 1. Pausar auto-screening da vaga
    await self.db.update_vacancy(
        job_id=job_id,
        auto_screening_enabled=False
    )
    
    # 2. Adicionar à lista de vagas congeladas (Redis)
    await self.redis.sadd("frozen_jobs", job_id)
    
    # 3. Cancelar follow-ups agendados
    cancelled_followups = await self.scheduler.cancel_tasks(
        job_id=job_id,
        task_type="followup"
    )
    
    # 4. Listar candidatos em triagem
    candidates = await self.db.get_candidates_in_screening(job_id)
    
    return ScreeningFreezeResult(
        paused_screenings=len(candidates),
        paused_followups=cancelled_followups,
        candidates_in_screening=candidates
    )
```

**Comportamento LIA WhatsApp (Vaga Congelada):**

```python
async def should_respond_about_job(self, job_id: str) -> bool:
    """Verifica se LIA pode responder normalmente sobre a vaga."""
    return not await self.redis.sismember("frozen_jobs", job_id)

async def get_frozen_job_response(self, job_title: str) -> str:
    """Resposta padrão para vagas congeladas."""
    return f"""Olá! O processo seletivo para a vaga {job_title} está 
temporariamente pausado. Você será notificado(a) assim que houver 
novidades. Obrigado pela compreensão!"""
```

---

### 4. SOURCING AGENT (sourcing_agent.py)

**Arquivo:** `lia-agent-system/app/agents/specialized/sourcing_agent.py`

**Handler:** `handle_job_freeze(job_id: str) -> SourcingFreezeResult`

**Responsabilidades:**

1. **Pausar buscas automáticas**
   - Atualizar: `vacancy.auto_sourcing_enabled = False`

2. **Cancelar jobs de busca agendados**
   - Remover do scheduler: `sourcing_search_{job_id}`

3. **Desativar alertas de novos candidatos**
   - Pausar notificações proativas sobre candidatos encontrados

```python
async def handle_job_freeze(self, job_id: str) -> SourcingFreezeResult:
    """
    Pausa buscas automáticas de candidatos para a vaga.
    
    Returns:
        SourcingFreezeResult(
            sourcing_jobs_cancelled: int,
            alerts_paused: int,
            last_search_date: Optional[datetime]
        )
    """
    # 1. Pausar auto-sourcing
    vacancy = await self.db.update_vacancy(
        job_id=job_id,
        auto_sourcing_enabled=False
    )
    
    # 2. Cancelar jobs de busca
    cancelled = await self.scheduler.cancel_tasks(
        job_id=job_id,
        task_type="sourcing_search"
    )
    
    # 3. Desativar alertas
    await self.db.pause_sourcing_alerts(job_id)
    
    return SourcingFreezeResult(
        sourcing_jobs_cancelled=cancelled,
        alerts_paused=1 if vacancy.sourcing_alert_enabled else 0,
        last_search_date=vacancy.last_sourcing_search_at
    )
```

---

### 5. EVALUATION AGENT (avaliador_wsi_agent.py)

**Arquivo:** `lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py`

**Handler:** `handle_job_freeze(job_id: str) -> EvaluationFreezeResult`

**Responsabilidades:**

1. **Buscar testes pendentes**
   - Query: `test_invites WHERE job_id = ? AND status = 'pending'`

2. **Cancelar convites de teste**
   - Atualizar status: `cancelled_job_frozen`

3. **Invalidar links de acesso**
   - Marcar tokens como expirados

```python
async def handle_job_freeze(self, job_id: str) -> EvaluationFreezeResult:
    """
    Cancela todos os convites de testes pendentes da vaga.
    
    Tipos de testes afetados:
    - Testes técnicos (coding challenges)
    - Testes de inglês
    - Testes comportamentais (Big Five)
    - Assessments customizados
    
    Returns:
        EvaluationFreezeResult(
            cancelled_tests: List[CancelledTest],
            total_cancelled: int
        )
    """
    pending_tests = await self.db.get_pending_test_invites(job_id)
    
    results = []
    for test in pending_tests:
        await self.db.update_test_invite(
            invite_id=test.id,
            status="cancelled_job_frozen",
            cancelled_at=datetime.now()
        )
        
        # Invalidar token de acesso
        await self.db.expire_test_token(test.access_token)
        
        results.append(CancelledTest(
            candidate_id=test.candidate_id,
            candidate_name=test.candidate_name,
            test_type=test.test_type,
            test_name=test.test_name,
            invite_date=test.created_at
        ))
    
    return EvaluationFreezeResult(
        cancelled_tests=results,
        total_cancelled=len(results)
    )
```

---

### 6. COMMUNICATION AGENT (communication_agent.py)

**Arquivo:** `lia-agent-system/app/agents/specialized/communication_agent.py`

**Handler:** `handle_job_freeze_notifications(event: JobFreezeEvent, results: ConsolidatedFreezeResults)`

**Responsabilidades:**

1. **Notificar candidatos afetados**
   - Canal: Email + WhatsApp (se disponível)
   - Template: `vaga_congelada_candidato`

2. **Notificar sobre cancelamento de entrevista**
   - Canal: Email
   - Template: `entrevista_cancelada_vaga_congelada`

3. **Notificar sobre cancelamento de teste**
   - Canal: Email
   - Template: `teste_cancelado_vaga_congelada`

4. **Enviar email resumo para recrutador**
   - Template: `resumo_congelamento_vaga`

```python
async def handle_job_freeze_notifications(
    self, 
    event: JobFreezeEvent, 
    results: ConsolidatedFreezeResults
) -> NotificationResult:
    """
    Envia todas as notificações relacionadas ao congelamento.
    
    Ordem de envio:
    1. Candidatos com entrevistas canceladas
    2. Candidatos com testes cancelados
    3. Demais candidatos da vaga (se notify_candidates=True)
    4. Email resumo para recrutador
    
    Returns:
        NotificationResult(
            candidates_notified_email: int,
            candidates_notified_whatsapp: int,
            recruiter_email_sent: bool
        )
    """
    notified_email = 0
    notified_whatsapp = 0
    
    # 1. Notificar candidatos com entrevistas canceladas
    for interview in results.scheduling.cancelled_interviews:
        await self.send_email(
            to=interview.candidate_email,
            template="entrevista_cancelada_vaga_congelada",
            variables={
                "candidato_nome": interview.candidate_name,
                "vaga_titulo": event.job_title,
                "data_entrevista": interview.interview_date.strftime("%d/%m/%Y às %H:%M"),
                "tipo_entrevista": interview.interview_type,
                "motivo": event.freeze_reason_label
            }
        )
        notified_email += 1
    
    # 2. Notificar candidatos com testes cancelados
    for test in results.evaluation.cancelled_tests:
        await self.send_email(
            to=test.candidate_email,
            template="teste_cancelado_vaga_congelada",
            variables={
                "candidato_nome": test.candidate_name,
                "vaga_titulo": event.job_title,
                "tipo_teste": test.test_name
            }
        )
        notified_email += 1
    
    # 3. Notificar demais candidatos (se solicitado)
    if event.notify_candidates:
        other_candidates = await self.get_remaining_candidates(
            job_id=event.job_id,
            exclude_ids=[i.candidate_id for i in results.scheduling.cancelled_interviews] +
                        [t.candidate_id for t in results.evaluation.cancelled_tests]
        )
        
        for candidate in other_candidates:
            await self.send_email(
                to=candidate.email,
                template="vaga_congelada_candidato",
                variables={
                    "candidato_nome": candidate.name,
                    "vaga_titulo": event.job_title,
                    "motivo_congelamento": event.freeze_reason_label,
                    "data_previsao": event.unfreeze_date.strftime("%d/%m/%Y") if event.unfreeze_date else "A definir"
                }
            )
            notified_email += 1
            
            # WhatsApp se disponível
            if candidate.whatsapp:
                await self.send_whatsapp(
                    to=candidate.whatsapp,
                    template="vaga_congelada_candidato_whatsapp",
                    variables={...}
                )
                notified_whatsapp += 1
    
    # 4. Email resumo para recrutador
    await self.send_recruiter_summary_email(event, results)
    
    return NotificationResult(
        candidates_notified_email=notified_email,
        candidates_notified_whatsapp=notified_whatsapp,
        recruiter_email_sent=True
    )
```

**Template: Email Resumo para Recrutador**

```python
RECRUITER_SUMMARY_TEMPLATE = """
Assunto: Resumo do Congelamento - {vaga_titulo} ({vaga_codigo})

Olá {recrutador_nome},

A vaga {vaga_titulo} foi congelada com sucesso. Segue resumo das ações automatizadas:

📋 DETALHES DO CONGELAMENTO
──────────────────────────
Motivo: {motivo_congelamento}
Previsão de descongelamento: {data_previsao}
Congelado em: {data_congelamento}

📅 ENTREVISTAS CANCELADAS: {total_entrevistas}
{lista_entrevistas}

📝 TESTES CANCELADOS: {total_testes}
{lista_testes}

🔔 CANDIDATOS NOTIFICADOS: {total_notificados}
  - Via Email: {notificados_email}
  - Via WhatsApp: {notificados_whatsapp}

⏸️ PROCESSOS PAUSADOS:
  - Triagens automáticas: {triagens_pausadas}
  - Follow-ups agendados: {followups_pausados}
  - Buscas de sourcing: Pausadas

💡 PRÓXIMOS PASSOS:
  1. LIA irá notificá-lo em {data_previsao} sobre o descongelamento
  2. Para descongelar antes, acesse Vagas > {vaga_titulo} > Alterar Status
  3. Candidatos em etapa de proposta não foram afetados

Dúvidas? Fale com a LIA!

Atenciosamente,
Sistema LIA
"""
```

---

## Regras de Negócio

| Código | Regra | Validação |
|--------|-------|-----------|
| RN-001 | Candidatos em etapa de Proposta bloqueiam congelamento | Orchestrator |
| RN-002 | Congelamento deve ter motivo obrigatório | Frontend + Orchestrator |
| RN-003 | Data de previsão é opcional mas recomendada | Frontend (warning) |
| RN-004 | LIA notifica recrutador na data de previsão | Scheduler |
| RN-005 | Candidatos em outras etapas permanecem no pipeline | Todos |
| RN-006 | Status da vaga muda para "Paralisada" | Orchestrator |
| RN-007 | Vaga pode ser despublicada sem congelar | Frontend |
| RN-008 | Congelamento cancela entrevistas/testes FUTUROS apenas | Scheduling/Evaluation |
| RN-009 | Histórico de congelamentos é mantido na auditoria | Orchestrator |
| RN-010 | Recrutador recebe email resumo após conclusão | Communication |

---

## Estados do Fluxo

```python
class JobFreezeStatus(Enum):
    REQUESTED = "requested"      # Recrutador solicitou
    VALIDATING = "validating"    # Verificando pré-requisitos
    BLOCKED = "blocked"          # Há candidatos em proposta
    EXECUTING = "executing"      # Agentes processando
    FAILED = "failed"            # Erro em algum agente
    COMPLETED = "completed"      # Sucesso
```

---

## Agendamento de Descongelamento

Se `unfreeze_date` foi informada, o Orchestrator agenda uma notificação proativa:

```python
async def schedule_unfreeze_reminder(self, event: JobFreezeEvent):
    """Agenda lembrete para o recrutador no dia do descongelamento previsto."""
    if not event.unfreeze_date:
        return
    
    await self.notifications.schedule(
        user_id=event.recruiter_id,
        notification_type="proactive_reminder",
        title="Lembrete: Vaga pronta para descongelar",
        message=f"A vaga {event.job_title} estava prevista para descongelar hoje. Deseja reativar o processo?",
        action_url=f"/vagas/{event.job_id}/descongelar",
        action_label="Descongelar Vaga",
        scheduled_for=event.unfreeze_date,
        channels=["bell", "email"],
        extra_data={
            "job_id": event.job_id,
            "freeze_reason": event.freeze_reason
        }
    )
```

---

## Auditoria

Todas as ações são registradas no log de auditoria:

```python
audit_log.record(
    entity_type="job_vacancy",
    entity_id=job_id,
    action="freeze",
    actor_id=recruiter_id,
    details={
        "freeze_reason": freeze_reason,
        "unfreeze_date": unfreeze_date,
        "cancelled_interviews": len(results.scheduling.cancelled_interviews),
        "cancelled_tests": len(results.evaluation.cancelled_tests),
        "candidates_notified": results.communication.total_notified,
        "timestamp": datetime.now().isoformat()
    }
)
```

---

## Testes Recomendados

```python
class TestJobFreezeWorkflow:
    
    async def test_freeze_blocked_when_candidate_in_proposal(self):
        """Deve bloquear congelamento se houver candidato em Proposta."""
        pass
    
    async def test_interviews_cancelled_on_freeze(self):
        """Deve cancelar todas as entrevistas futuras."""
        pass
    
    async def test_tests_cancelled_on_freeze(self):
        """Deve cancelar todos os convites de teste pendentes."""
        pass
    
    async def test_lia_responds_frozen_message_on_whatsapp(self):
        """LIA deve responder mensagem de vaga congelada no WhatsApp."""
        pass
    
    async def test_recruiter_receives_summary_email(self):
        """Recrutador deve receber email com resumo das ações."""
        pass
    
    async def test_unfreeze_reminder_scheduled(self):
        """Deve agendar lembrete para data de descongelamento."""
        pass
```

---

## Diagrama de Sequência

```
Recrutador      Frontend       Orchestrator    Agents           DB/Redis
    │              │               │              │                 │
    │──Congelar───>│               │              │                 │
    │              │──Validate────>│              │                 │
    │              │               │──Query──────────────────────────>│
    │              │               │<─Candidates in Proposal─────────│
    │              │               │              │                 │
    │              │               │ IF blocked:  │                 │
    │              │<──Error───────│              │                 │
    │<──Show Modal─│               │              │                 │
    │              │               │              │                 │
    │              │               │ IF ok:       │                 │
    │              │               │──Update Status─────────────────>│
    │              │               │──Dispatch────>│                 │
    │              │               │              │──Cancel Events──>│
    │              │               │              │──Pause Screening>│
    │              │               │              │──Cancel Tests───>│
    │              │               │<─Results─────│                 │
    │              │               │──Notify──────>│                 │
    │              │               │              │──Send Emails────>│
    │              │<─Success──────│              │                 │
    │<─Toast───────│               │              │                 │
```
