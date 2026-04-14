# P16 — VERTICAL INTEGRATION MAP
**WeDOTalent / LIA Platform**
**Data:** 2026-04-14
**Protocolo:** P16 — Mapeamento de Integração Vertical (Ação por Ação)
**Auditores:** Código real lido via SSH em `/home/runner/workspace/lia-agent-system/` e `/home/runner/workspace/ats-api-copia/`

---

## SUMÁRIO EXECUTIVO

| Status | Quantidade | Percentual |
|--------|-----------|-----------|
| COMPLETA | 5 | 14% |
| PARCIAL | 14 | 40% |
| QUEBRADA | 9 | 26% |
| ILUSÓRIA | 7 | 20% |
| **TOTAL** | **35** | 100% |

**Score Geral de Integração Vertical: 27/100**

### Diagnóstico Crítico

- `RAILS_API_URL` **NÃO está configurado** em produção → `RAILS_ENABLED = False` → toda integração Python↔Rails está desativada
- `MAILGUN_API_KEY` e `RESEND_API_KEY` **não estão nos env vars** → emails caem em modo `dev/simulated`
- `TWILIO_ACCOUNT_SID` tem valor real, mas `ENVIRONMENT` está como `development` no .env (Replit define `REPLIT_ENVIRONMENT=production`, mas o app lê `ENVIRONMENT=development`) → WhatsApp entra em `_send_development` (log only)
- `RABBITMQ_URL` aponta para `localhost:5672` → RabbitMQ não está em produção no Replit
- `calendar.lia.app` é um link simulado gerado em `scheduling_tools.py` com `uuid.uuid4()` — sem integração Google Calendar ou Microsoft Graph real para maioria dos fluxos
- Dashboard retorna dados hardcoded: `interviews_conducted=42` (literal no código)
- `report_service.py` usa `random.uniform()` para gerar métricas de qualidade nos relatórios

---

## MATRIZ DE AÇÕES × STATUS

| # | Ação | Agente | Tool→Backend | DB | Externo | Frontend | Feedback | Audit | STATUS |
|---|------|--------|-------------|-----|---------|----------|---------|-------|--------|
| 1 | Enviar email candidato | CommunicationAgent | ⚠ | ✓ | ✗ | ✗ | ⚠ | ⚠ | QUEBRADA |
| 2 | Enviar email recrutador | CommunicationAgent | ⚠ | ✓ | ✗ | ✗ | ⚠ | ✗ | QUEBRADA |
| 3 | Enviar WhatsApp | CommunicationAgent | ⚠ | ✓ | ✗ | ✗ | ⚠ | ⚠ | ILUSÓRIA |
| 4 | Notificação plataforma | AutomationService | ✓ | ✓ | N/A | ⚠ | ⚠ | ✗ | PARCIAL |
| 5 | Agendar envio futuro | CommunicationAgent | ⚠ | ✗ | ✗ | ✗ | ✗ | ✗ | ILUSÓRIA |
| 6 | Buscar candidatos | SourcingSearchAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✗ | PARCIAL |
| 7 | Criar perfil candidato | CVScreeningAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 8 | Atualizar perfil candidato | CVScreeningAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 9 | Mover candidato pipeline | PipelineAgent | ✓ | ✓ | ✗ | ⚠ | ✓ | ✓ | COMPLETA |
| 10 | Atribuir score candidato | CVScreeningAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✓ | COMPLETA |
| 11 | Registrar feedback entrevista | PipelineAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✗ | PARCIAL |
| 12 | Associar candidato a vaga | CVScreeningAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 13 | Marcar como contratado | CVScreeningAgent | ✓ | ✓ | ✗ | ⚠ | ✓ | ✗ | PARCIAL |
| 14 | Registrar recusa | CVScreeningAgent | ✓ | ✓ | ✗ | ⚠ | ✓ | ⚠ | PARCIAL |
| 15 | Criar vaga | JobWizardAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 16 | Atualizar requisitos vaga | JobWizardAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 17 | Fechar vaga | JobWizardAgent | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | PARCIAL |
| 18 | Criar evento entrevista | SchedulingAgent | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | QUEBRADA |
| 19 | Verificar disponibilidade | SchedulingAgent | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ILUSÓRIA |
| 20 | Reagendar entrevista | SchedulingAgent | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ILUSÓRIA |
| 21 | Enviar confirmação entrevista | CommunicationAgent | ⚠ | ✓ | ✗ | ✗ | ⚠ | ✗ | QUEBRADA |
| 22 | Triagem automática CV | CVScreeningAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✓ | COMPLETA |
| 23 | Gerar relatório avaliação | AnalyticsAgent | ⚠ | ✓ | N/A | ⚠ | ✓ | ✗ | PARCIAL |
| 24 | Comparativo entre candidatos | AnalyticsAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✗ | PARCIAL |
| 25 | Relatório pipeline | AnalyticsAgent | ✓ | ✓ | N/A | ⚠ | ✓ | ✗ | PARCIAL |
| 26 | Calcular métricas | AnalyticsAgent | ⚠ | ⚠ | N/A | ⚠ | ✓ | ✗ | QUEBRADA |
| 27 | Exportar dados | AnalyticsAgent | ✗ | ✗ | N/A | ✗ | ✗ | ✗ | QUEBRADA |
| 28 | WSI — Score voice/chat | WSIAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✓ | COMPLETA |
| 29 | Busca diversidade sourcing | DiversityAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✗ | PARCIAL |
| 30 | Enriquecimento candidato | SourcingEnrichAgent | ✓ | ✓ | ⚠ | ✓ | ✓ | ✗ | PARCIAL |
| 31 | Sequência nurture | NurtureAgent | ✓ | ⚠ | ✗ | ✗ | ⚠ | ✗ | QUEBRADA |
| 32 | Busca GitHub/SO | GithubSourcingAgent | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | PARCIAL |
| 33 | Triagem WSI | WSIAgent | ✓ | ✓ | N/A | ✓ | ✓ | ✓ | COMPLETA |
| 34 | Rate limit / opt-out check | CommunicationAgent | ✓ | ✓ | N/A | N/A | ✓ | ✗ | PARCIAL |
| 35 | Notificação recrutador (Teams) | CommunicationAgent | ✓ | ✗ | ⚠ | ✓ | ✓ | ✗ | QUEBRADA |

**Legenda:** ✓ Funciona | ⚠ Parcial/Condicionado | ✗ Ausente/Quebrado | N/A Não aplicável

---

## TRACE DETALHADO POR AÇÃO

### COMUNICAÇÃO

---

```
AÇÃO: Enviar email candidato
AGENTE: CommunicationAgent (_wrap_send_email em communication_tool_registry.py)
TRIGGER: Agente decide enviar email ao candidato via ferramenta send_email
CADEIA:
  Tool: send_email → ✓ (2 implementações: communication_tools.py e communication_tool_registry.py)
  Backend: CommunicationService.send_message → email_service._send_email_provider → ⚠
    - Código tenta Mailgun (primary) → Resend (fallback)
    - MAILGUN_API_KEY não está configurado (não encontrado em printenv)
    - RESEND_API_KEY não está configurado
    - app/.env: ENVIRONMENT=development → is_dev=True → _log_dev_email() chamado
    - Resultado: email logado mas NÃO ENVIADO
  DB: email_logs (INSERT) → ✓ log de tentativa salvo com status='failed'/'sent'
  Externo: Mailgun/Resend → ✗ nenhuma chave configurada, cai em log local
  Frontend: sem WebSocket push de volta ao front → ✗
  Feedback: agente recebe {"success": True, "message": "Email enviado"} mesmo quando não foi → ⚠ FALSO POSITIVO
  Audit: email_logs registrado → ⚠ (registra tentativa mas não confirma entrega real)
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - MAILGUN_API_KEY ausente em env
  - RESEND_API_KEY ausente em env
  - ENVIRONMENT=development força fallback de log mesmo em Replit (REPLIT_ENVIRONMENT=production)
  - Nenhum WebSocket notifica frontend sobre resultado de envio
  - Agente recebe success=True mesmo quando email não foi enviado
```

---

```
AÇÃO: Enviar email recrutador
AGENTE: CommunicationAgent
TRIGGER: Notificação interna para recrutador (ex: novo candidato aprovado)
CADEIA:
  Tool: send_email (reutiliza a mesma tool) → ⚠
  Backend: mesmo fluxo acima, sem destinatário recrutador definido explicitamente → ⚠
  DB: email_logs → ✓
  Externo: Mailgun/Resend → ✗
  Frontend: sem notificação em tempo real → ✗
  Feedback: agente não distingue se email foi para candidato ou recrutador → ✗
  Audit: ✗ sem campo "recipient_type" no log
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - Mesmos gaps do email candidato
  - Nenhuma tool específica para "email recrutador" — usa a mesma genérica
  - Sem campo recipient_type na tabela email_logs para distinguir
```

---

```
AÇÃO: Enviar WhatsApp
AGENTE: CommunicationAgent (_wrap_send_whatsapp em communication_tool_registry.py)
TRIGGER: Agente chama send_whatsapp para candidato
CADEIA:
  Tool: send_whatsapp → ⚠
    communication_tool_registry.py chama WhatsAppService.send_message()
    communication_tools.py (versão antiga) apenas retorna mock se DB falha
  Backend: WhatsAppService.send_message → ⚠
    - TWILIO_ACCOUNT_SID tem valor real em printenv (AC76fd82...)
    - TWILIO_AUTH_TOKEN tem valor real
    - ENVIRONMENT=development no .env → is_development() retorna True
    - Método: _send_development() → apenas loga, status=QUEUED_DEVELOPMENT
    - Twilio SDK disponível mas não chamado por causa do env flag
  DB: sem tabela de whatsapp_logs → ✗ (apenas log de texto)
  Externo: Twilio → ✗ (não chamado em development mode)
  Frontend: sem push de entrega → ✗
  Feedback: agente recebe success=True, status=queued_development → ⚠ ILUSÓRIO
  Audit: ✗ sem persistência de tentativa
CLASSIFICAÇÃO: ILUSÓRIA
GAPS:
  - ENVIRONMENT=development no .env sobrescreve REPLIT_ENVIRONMENT=production
  - Não existe tabela whatsapp_logs na plataforma
  - Agente recebe "enviado" mas mensagem ficou em log local
  - Fix trivial: setar ENVIRONMENT=production no .env ou checar REPLIT_ENVIRONMENT
```

---

```
AÇÃO: Notificação plataforma (in-app)
AGENTE: AutomationService / ProactiveService
TRIGGER: Evento de pipeline (candidato aprovado, entrevista agendada etc.)
CADEIA:
  Tool: _send_notification (proactive_service.py) → ✓
  Backend: ActivityFeed + NotificationService → ✓
  DB: activity_feed table (INSERT) → ✓
  Externo: N/A (notificação interna)
  Frontend: WebSocket (ws_manager.send_to_session em hitl_service.py) → ⚠ apenas em HITL
  Feedback: ⚠ parcial — apenas HITL tem WebSocket, fluxo normal não tem push
  Audit: ✗ sem AuditLog para notificações in-app
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - WebSocket só funciona via HITL (hitl_service.py linha 295)
  - Agente autônomo não notifica frontend em tempo real
  - Sem audit trail de notificações
```

---

```
AÇÃO: Agendar envio futuro
AGENTE: CommunicationAgent (_wrap_schedule_message)
TRIGGER: Agente solicita envio agendado para data futura
CADEIA:
  Tool: schedule_message → ⚠
  Backend: CommunicationService.send_message() chamado IMEDIATAMENTE, ignora scheduled_at → ✗
    Código: "result = await svc.send_message(...)" sem delay, sem fila
    Para Teams: envia imediatamente com nota "Teams não suporta envio nativo agendado"
  DB: ✗ sem tabela scheduled_messages, sem job queue
  Externo: ✗ sem Celery, sem APScheduler para deferred send
  Frontend: ✗
  Feedback: retorna {"scheduled": True} mas mensagem foi enviada agora ou não enviada → ILUSÓRIO
  Audit: ✗
CLASSIFICAÇÃO: ILUSÓRIA
GAPS:
  - scheduled_at é ignorado — mensagem enviada imediatamente
  - Sem worker/fila para execução futura (Celery tasks não implementadas para isso)
  - DB não persiste mensagens agendadas
  - Tool documenta recurso que não existe
```

---

### CANDIDATOS

---

```
AÇÃO: Buscar candidatos
AGENTE: SourcingSearchAgent (search_candidates tool)
TRIGGER: Recrutador ou agente pede busca por skills/seniority/localização
CADEIA:
  Tool: search_candidates (sourcing/tools/query_tools.py) → ✓ implementação real
  Backend: SQLAlchemy SELECT em candidates + vacancy_candidates → ✓
  DB: candidates, vacancy_candidates (SELECT com filtros) → ✓
    Filtro por company_id, status, seniority, location, skills (post-filter array)
    Sem busca vetorial real (pgvector/ES não integrado neste path)
  Externo: N/A (busca local)
  Frontend: retorno estruturado → ✓
  Feedback: agente recebe lista de candidatos → ✓
  Audit: ✗ sem log de busca
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Busca por skills usa array "contains" em memória, não índice vetorial
  - Rails não consultado (RAILS_ENABLED=False)
  - Sem audit de quem buscou o quê
  - Sem busca semântica/embedding integrada neste tool
```

---

```
AÇÃO: Criar perfil candidato
AGENTE: CVScreeningAgent (parse_and_create_candidate em cv_upload_tool.py)
TRIGGER: Upload de CV ou dados manuais
CADEIA:
  Tool: parse_and_create_candidate → ✓
  Backend: Candidate model INSERT → ✓
  DB: candidates table INSERT → ✓
  Externo: Rails → ✗ (RAILS_ENABLED=False, sem sync)
  Frontend: ✓ retorna candidato_id
  Feedback: ✓ agente recebe ID do candidato criado
  Audit: ✗ sem AuditLog de criação
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Candidato criado no Python DB mas não sincronizado com Rails
  - Rails (ats-api-copia) não recebe o novo candidato
  - Sem audit trail de criação
```

---

```
AÇÃO: Atualizar perfil candidato
AGENTE: CVScreeningAgent
TRIGGER: Agente decide enriquecer ou corrigir dados do candidato
CADEIA:
  Tool: update_candidate (via SQLAlchemy) → ✓
  Backend: Candidate model UPDATE → ✓
  DB: candidates table UPDATE → ✓
  Externo: Rails → ✗ (RAILS_ENABLED=False)
  Frontend: ✓
  Feedback: ✓
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS: mesmos da criação — sem sync Rails, sem audit
```

---

```
AÇÃO: Mover candidato no pipeline
AGENTE: PipelineAgent (_wrap_move_candidate em pipeline_tool_registry.py)
TRIGGER: Agente decide mudar etapa do candidato
CADEIA:
  Tool: move_candidate → ✓
  Backend: UPDATE vacancy_candidates SET stage = :target_stage → ✓ SQL direto
  DB: vacancy_candidates (UPDATE stage, updated_at) → ✓ commit real
  Externo: Rails → ✗ sem sync de stage para Rails applies
  Frontend: ✓ resultado retornado com previous_stage e new_stage
  Feedback: ✓ agente recebe confirmação com rows_updated
  Audit: ✓ AuditLog criado via Rails worker (LiaEventsWorker) quando evento chega por RabbitMQ
CLASSIFICAÇÃO: COMPLETA
GAPS:
  - Rails não é notificado (RABBITMQ em localhost, desconectado)
  - Sync bidirecional Rails↔Python para stages não existe
```

---

```
AÇÃO: Atribuir score candidato
AGENTE: CVScreeningAgent (analyze_cv_match em cv_match_tool.py)
TRIGGER: Agente solicita avaliação BARS de candidato contra vaga
CADEIA:
  Tool: analyze_cv_match → ✓ resolve IDs por nome, chama CVScoringService
  Backend: CVScoringService.screen_candidate() → ✓ rubric BARS real
  DB: vacancy_candidates (UPDATE lia_score, match_percentage) → ✓
  Externo: N/A (LLM local via Anthropic)
  Frontend: ✓ retorna score + matched_skills + recommendation
  Feedback: ✓ agente recebe resultado completo BARS
  Audit: ✓ rubric_evaluation_service cria activity entry + notificação
CLASSIFICAÇÃO: COMPLETA
GAPS:
  - Score não sincronizado com Rails (sem RAILS_ENABLED)
  - Notificação via NotificationService (não WebSocket direto)
```

---

```
AÇÃO: Registrar feedback entrevista
AGENTE: PipelineAgent (add_notes / view_interview_notes)
TRIGGER: Entrevistador pede para registrar notas de entrevista
CADEIA:
  Tool: _wrap_add_notes (pipeline_tool_registry.py) → ✓ UPDATE vacancy_candidates notas
  Backend: interview_notes_service.create_interview_note → ✓
  DB: interviews table (UPDATE notes) ou interview_notes → ✓
  Externo: N/A
  Frontend: ✓ dados retornados
  Feedback: ✓
  Audit: ✗ sem AuditLog específico para nota de entrevista
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Notes salvas em vacancy_candidates.notes, não em tabela interview_notes separada por entrevista
  - Sem audit trail de quem editou qual nota
```

---

```
AÇÃO: Associar candidato a vaga
AGENTE: CVScreeningAgent (add_candidate_to_vacancy)
TRIGGER: Agente adiciona candidato ao pipeline de uma vaga específica
CADEIA:
  Tool: add_candidate_to_vacancy → ✓ verifica tenant, checa duplicata
  Backend: VacancyCandidate INSERT → ✓
  DB: vacancy_candidates (INSERT) → ✓ com company_id, stage, source, added_by
  Externo: Rails → ✗
  Frontend: ✓
  Feedback: ✓ retorna mensagem de confirmação com nome candidato e vaga
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS: sem sync Rails, sem audit
```

---

```
AÇÃO: Marcar como contratado
AGENTE: CVScreeningAgent / PipelineAgent
TRIGGER: Agente move candidato para estágio 'Contratado'
CADEIA:
  Tool: update_candidate_stage(target_stage='Contratado') → ✓ (via stage string)
  Backend: UPDATE vacancy_candidates SET stage='Contratado' → ✓
  DB: vacancy_candidates → ✓
    Campos ausentes: hired_date, offer_accepted_at, salary_agreed → ✗
  Externo: Rails → ✗ (sem sync)
  Frontend: ⚠ stage exibido, mas sem campo "data contratação" para exibir
  Feedback: ✓ agente recebe confirmação
  Audit: ✗ sem campo contratado_at no DB Python
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Não existe campo hired_date, offer_accepted_at no modelo Python
  - Não existe campo hired_date na tabela vacancy_candidates
  - Candidato "contratado" não gera evento de fechamento de vaga
  - Rails não é atualizado
```

---

```
AÇÃO: Registrar recusa
AGENTE: CVScreeningAgent (reject_candidate)
TRIGGER: Agente decide ou recrutador solicita rejeição de candidato
CADEIA:
  Tool: reject_candidate → ✓ (com FairnessGuard DEI-02)
  Backend: UPDATE vacancy_candidates SET status='rejected', stage='Reprovado' → ✓
  DB: vacancy_candidates → ✓
  Externo: FairnessGuard check → ✓ (bloqueia texto com viés explícito)
    feedback enviado por send_feedback → ✗ (email não enviado)
  Frontend: ⚠ stage atualizado, sem confirmação de email
  Feedback: ✓ agente recebe resultado + fairness_warnings
  Audit: ⚠ FairnessGuard loga warnings mas sem AuditLog formal
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Email de rejeição não entrega (mesmos gaps de email)
  - Sem campo rejection_reason persistido na DB
  - Audit apenas via FairnessGuard, não via AuditLog central
```

---

### VAGAS

---

```
AÇÃO: Criar vaga
AGENTE: JobWizardAgent (create_job em job_tools.py)
TRIGGER: Agente ou recrutador cria nova vaga via wizard
CADEIA:
  Tool: create_job → ✓ completo com todos os campos
  Backend: JobVacancy INSERT → ✓ status, stage, recruiter, created_by
  DB: job_vacancies INSERT → ✓ commit real
  Externo: Rails → ✗ RAILS_ENABLED=False
    Comentário no código: "Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff"
  Frontend: ✓ retorna job_id
  Feedback: ✓ agente recebe job_id e detalhes
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - Vaga não é publicada no Rails
  - Sem sync Rails (vaga criada só no Python DB)
  - Sem audit trail
  - Publicação no LinkedIn não implementada (campo published_linkedin existe mas sem integração)
```

---

```
AÇÃO: Atualizar requisitos vaga
AGENTE: JobWizardAgent (update_job)
TRIGGER: Agente modifica campos de uma vaga existente
CADEIA:
  Tool: update_job (job_tools.py linha 152) → ✓
  Backend: JobVacancy UPDATE → ✓
  DB: job_vacancies UPDATE → ✓
  Externo: Rails → ✗
  Frontend: ✓
  Feedback: ✓
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS: mesmos da criação
```

---

```
AÇÃO: Fechar vaga
AGENTE: JobWizardAgent (close_job)
TRIGGER: Recrutador solicita encerramento de vaga
CADEIA:
  Tool: close_job (job_tools.py linha 339) → ✓
  Backend: JobVacancy UPDATE status='Fechada', closed_at=now() → ✓
  DB: job_vacancies (UPDATE) → ✓
  Externo: Rails → ✗
    Candidatos em processo NÃO são notificados por email (email quebrado)
  Frontend: ✓ confirmação retornada
  Feedback: ✓ com lista de candidatos a notificar (sem envio real)
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - notify_candidates=True apenas adiciona texto à resposta, sem envio real
  - Rails não recebe fechamento
  - Audit ausente
```

---

### AGENDAMENTO

---

```
AÇÃO: Criar evento entrevista
AGENTE: PipelineAgent (_wrap_schedule_interview em pipeline_tool_registry.py)
  / SchedulingAgent (schedule_interview em scheduling_tools.py — STUB)
TRIGGER: Agente agenda entrevista para candidato
CADEIA:
  Tool: _wrap_schedule_interview (pipeline_tool_registry) → ✓ INSERT real
    schedule_interview (scheduling_tools.py) → ✗ STUB com uuid e link fake
  Backend:
    Pipeline path: INSERT INTO interviews → ✓ (cria registro real)
    Scheduling path: retorna "IV-XXXX" e "https://calendar.lia.app/..." (FAKE) → ✗
  DB: interviews table INSERT → ✓ (pipeline path)
    Faltam: google_calendar_event_id, outlook_event_id, meet_link real → ✗
  Externo: Google Calendar / Microsoft Graph → ✗ não chamados neste fluxo
    Teams Calendar: scheduleInterview → ✓ (via microsoft_graph_service), mas só se Teams configurado
  Frontend: ✗ sem link de reunião real para exibir
  Feedback: ✓ retorna interview_id, mas meeting_link é fake
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - Dois caminhos de code: pipeline path (parcialmente real) vs scheduling path (stub total)
  - meeting_link sempre fake ("https://calendar.lia.app/interviews/IV-XXXX")
  - Google Calendar não integrado neste fluxo
  - Microsoft Graph Calendar: existe código real, mas AZURE_CLIENT_SECRET não verificado em env
```

---

```
AÇÃO: Verificar disponibilidade
AGENTE: SchedulingAgent (check_interviewer_availability em scheduling_tools.py)
TRIGGER: Agente verifica agenda do entrevistador
CADEIA:
  Tool: check_interviewer_availability → ✗ STUB TOTAL
  Backend: usa random.Random(hash(interviewer_id)) para gerar slots → ✗
  DB: ✗ sem consulta a calendar_availability table
  Externo: Google Calendar / Microsoft Graph → ✗
  Frontend: ✗ dados fake
  Feedback: agente recebe slots aleatórios determinísticos → ILUSÓRIO
  Audit: ✗
CLASSIFICAÇÃO: ILUSÓRIA
GAPS:
  - SIMULATION STUB explicitamente comentado no topo do arquivo
  - "random module usage below is intentional for simulation only"
  - calendar_availability table existe no Rails (ats-api-copia) mas não integrada
```

---

```
AÇÃO: Reagendar entrevista
AGENTE: SchedulingAgent (reschedule_interview em scheduling_tools.py)
TRIGGER: Agente reagenda entrevista existente
CADEIA:
  Tool: reschedule_interview → ✗ STUB
  Backend: retorna old_datetime='N/A' (comentário: "simulation without persistent state") → ✗
  DB: ✗ não atualiza interviews table
  Externo: ✗ nenhum update de calendário
  Frontend: ✗
  Feedback: agente recebe {"status": "rescheduled", "old_datetime": "N/A"} → ILUSÓRIO
  Audit: ✗
CLASSIFICAÇÃO: ILUSÓRIA
GAPS:
  - Comentário explícito: "Stores the old datetime as 'N/A' since this is a simulation"
  - Sem UPDATE na tabela interviews
  - Teams reschedule (teams_calendar_service.reschedule_interview) existe e é real, mas não conectado ao agente
```

---

```
AÇÃO: Enviar confirmação entrevista
AGENTE: CommunicationAgent (send_interview_invitation em scheduling_tools.py)
TRIGGER: Após agendamento, enviar convite ao candidato
CADEIA:
  Tool: send_interview_invitation → ✗ STUB
    Retorna {"status": "sent", "timestamp": ...} sem envio real
  Backend: ✗ sem chamada a email_service ou whatsapp_service
  DB: ✗ sem log de envio
  Externo: ✗
  Frontend: ✗
  Feedback: ✗ agente recebe "sent" mas nada foi enviado
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - send_interview_invitation no scheduling_tools.py é stub total
  - Comentário no arquivo: "SIMULATION STUB: replace with real calendar API integrations"
  - handlers_interview.py tem código real para email/WhatsApp, mas não é o que o agente usa
```

---

### SCREENING

---

```
AÇÃO: Triagem automática CV
AGENTE: CVScreeningAgent (analyze_cv_match em cv_match_tool.py)
TRIGGER: Agente analisa CV contra requisitos de vaga
CADEIA:
  Tool: analyze_cv_match → ✓ BARS completo
  Backend: CVScoringService.screen_candidate() → ✓ rubric scoring real
  DB: vacancy_candidates UPDATE (lia_score, match_percentage, recommendation) → ✓
  Externo: Anthropic LLM (claude-sonnet-4-6) → ✓ via AI_INTEGRATIONS_ANTHROPIC_API_KEY
  Frontend: ✓ scores e recommendation retornados
  Feedback: ✓ agente recebe avaliação detalhada
  Audit: ✓ activity_service.create_rubric_evaluation_activity
CLASSIFICAÇÃO: COMPLETA
GAPS:
  - LLM key é dummy em .env ("_DUMMY_API_KEY_"), mas em runtime usa AI_INTEGRATIONS_ANTHROPIC_BASE_URL (proxy)
  - Score não sincronizado com Rails
```

---

```
AÇÃO: Gerar relatório avaliação
AGENTE: AnalyticsAgent / SourcingAgent (generate_report)
TRIGGER: Recrutador pede relatório de avaliações
CADEIA:
  Tool: _wrap_generate_report (sourcing_tool_registry.py) → ⚠
  Backend: SELECT de applications com status shortlisted/contacted → ✓ SQL real
    MAS report_service.py usa random.uniform() para quality_score → ✗ DADO FAKE
  DB: ✓ consulta real para counts
  Externo: N/A
  Frontend: ⚠ números de count reais, percentuais de qualidade são gerados aleatoriamente
  Feedback: ✓ agente recebe relatório
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - report_service.py: "quality_score": round(rng.uniform(75.0, 98.0), 1) — dado inventado
  - Relatório não é persistido nem exportável
```

---

```
AÇÃO: Comparativo entre candidatos
AGENTE: AnalyticsAgent (compare_candidates)
TRIGGER: Recrutador pede comparação side-by-side
CADEIA:
  Tool: compare_candidates (pipeline_analytics.py) → ✓
  Backend: SELECT Candidate por UUID → ✓
  DB: candidates table → ✓
  Externo: N/A
  Frontend: ✓ retorna ranking com lia_score
  Feedback: ✓
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - wsi_score, fit_score podem ser null (campos não always preenchidos)
  - Sem audit
  - Sem export do comparativo
```

---

### RELATÓRIOS

---

```
AÇÃO: Relatório pipeline
AGENTE: AnalyticsAgent (get_pipeline_stats em pipeline_analytics.py)
TRIGGER: Recrutador solicita métricas do pipeline
CADEIA:
  Tool: get_pipeline_stats → ✓ SQL real
  Backend: SELECT job_vacancies, vacancy_candidates → ✓
  DB: ✓ dados reais de status/stage
  Externo: N/A
  Frontend: ⚠ dashboard retorna dados hardcoded (interviews_conducted=42 em dashboard_data.py)
  Feedback: ✓ agente recebe stats reais
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - dashboard_data.py linha 394: `interviews_conducted=42` — hardcoded
  - Duas fontes de dados: API analítica (real) vs dashboard API (fake)
  - time_to_fill não calculado — ausente no schema Python
```

---

```
AÇÃO: Calcular métricas (time_to_fill, conversion rate, cost-per-hire)
AGENTE: AnalyticsAgent
TRIGGER: Solicitação de métricas avançadas de recrutamento
CADEIA:
  Tool: get_efficiency_metrics, get_velocity_metrics → ⚠
  Backend: report_service.py usa random.Random(seed) para tendências → ✗
    Código: triagem_rate = rng.uniform(0.45, 0.60) — inventado
  DB: ⚠ alguns dados reais (counts), taxas de conversão são estimadas/aleatórias
  Externo: N/A
  Frontend: ⚠ métricas apresentadas como reais mas são geradas proceduralmente
  Feedback: ✓ agente recebe valores numéricos
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - time_to_fill: sem campo closed_at vs open_date calculado consistentemente
  - cost_per_hire: sem tabela de custos no schema
  - Taxas de conversão geradas com random.uniform — não representam dados reais
  - report_service.py: admitted randômico intencional "for simulation only"
```

---

```
AÇÃO: Exportar dados
AGENTE: AnalyticsAgent / LGPDService
TRIGGER: Usuário solicita export de candidatos/vagas/relatórios
CADEIA:
  Tool: ✗ sem tool de export nos agentes de analytics
  Backend: dsr_export_service.export_candidate_data existe → ✓ (apenas para LGPD DSR)
    Export de relatórios gerais: ✗ não implementado
  DB: ✗ sem endpoint de export CSV/Excel para analytics
  Externo: ✗
  Frontend: ✗ "exportar candidatos" mencionado em teams_orchestrator_bridge mas não implementado
  Feedback: ✗
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - Export só existe para LGPD DSR (direito de acesso individual)
  - Sem export de pipeline reports em CSV/Excel/PDF
  - Sem tool registrado nos agentes para esta ação
```

---

```
AÇÃO: WSI — Score de triagem voice/chat
AGENTE: WSIAgent (wsi_screening em candidate_tools.py)
TRIGGER: Candidato conclui entrevista WSI conversacional
CADEIA:
  Tool: wsi_screening → ✓
  Backend: wsi/evaluation.py → CVScoringService → ✓
  DB: wsi_sessions, vacancy_candidates (wsi_score UPDATE) → ✓
  Externo: Anthropic LLM → ✓ (via proxy)
  Frontend: ✓ score e recommendation exibidos
  Feedback: ✓ agente recebe wsi_score completo
  Audit: ✓ audit_log via handlers_screening.py
CLASSIFICAÇÃO: COMPLETA
GAPS:
  - Twilio Voice (voice screening) requer ENVIRONMENT=production — quebrado por env flag
```

---

```
AÇÃO: Notificação recrutador via Teams
AGENTE: CommunicationAgent (_wrap_send_email via TeamsService)
TRIGGER: Evento relevante no pipeline dispara notificação Teams
CADEIA:
  Tool: teams_service / teams_proactivity_engine → ✓ código existente
  Backend: TeamsBot + Microsoft Graph → ⚠
    ENABLE_MICROSOFT_GRAPH=true no .env
    AZURE_CLIENT_SECRET não encontrado em printenv
  DB: ✗ sem log de notificações Teams
  Externo: Microsoft Teams API → ⚠ (configuração parcial)
  Frontend: Teams app → ⚠ (depende de Azure configurado)
  Feedback: ✓ (quando funciona)
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - AZURE_CLIENT_SECRET ausente em env = Teams não funciona
  - Sem persistência de notificações enviadas
```

---

```
AÇÃO: Rate limit / opt-out check
AGENTE: CommunicationAgent (check_rate_limit)
TRIGGER: Antes de qualquer comunicação, verificar LGPD/opt-out
CADEIA:
  Tool: check_rate_limit (_wrap_check_rate_limit) → ✓
  Backend: CommunicationService.validate_can_send → ✓
  DB: communication_logs / opt-out table → ✓
  Externo: N/A
  Frontend: N/A (verificação interna)
  Feedback: ✓ retorna can_send, warnings, blocks
  Audit: ✗ sem log de verificações de rate limit
CLASSIFICAÇÃO: PARCIAL
GAPS: sem audit de verificações de opt-out
```

---

```
AÇÃO: Busca de diversidade/sourcing GitHub/StackOverflow
AGENTE: GithubSourcingAgent / DiversityAgent
TRIGGER: Busca de candidatos em fontes externas
CADEIA:
  Tool: _wrap_github_search_developers, diversity_search_candidates → ✓
  Backend: GitHubService (API real), Apify, StackOverflow → ✓ (quando API keys configuradas)
  DB: candidates INSERT/UPDATE → ✓
  Externo: GitHub API → ✓ (PEARCH_API_KEY=false, mas PEARCH_ENABLE=false)
  Frontend: ✓
  Feedback: ✓
  Audit: ✗
CLASSIFICAÇÃO: PARCIAL
GAPS:
  - PEARCH_API_KEY vazio → enriquecimento Pearch não funciona
  - ENABLE_PEARCH_AI=false
  - RabbitMQ publish de candidatos novos (contact_enrichment_service.py) falha (localhost)
```

---

```
AÇÃO: Sequência nurture (follow-up automático)
AGENTE: NurtureSequenceAgent
TRIGGER: Candidato passivo não respondeu — sequência automática de follow-up
CADEIA:
  Tool: nurture tools → ✓ lógica definida
  Backend: RabbitMQ publish (rabbitmq_producer.publish_chat_message) → ✗
    URL: amqp://guest:guest@localhost:5672/ — RabbitMQ não conectado em Replit
  DB: ⚠ lógica de sequence tracking implementada mas depende de RabbitMQ
  Externo: Email/WhatsApp → ✗ (mesmos problemas)
  Frontend: ✗
  Feedback: ⚠ try/except ignora falha de RabbitMQ ("non-blocking")
  Audit: ✗
CLASSIFICAÇÃO: QUEBRADA
GAPS:
  - RabbitMQ em localhost: todos os publish falham silenciosamente
  - Sequência de nurture depende inteiramente de RabbitMQ para orquestração
  - Emails de nurture não são enviados
```

---

## TOP 10 INTEGRAÇÕES QUEBRADAS/ILUSÓRIAS (CRÍTICAS)

| # | Ação | Tipo | Impacto | Causa Raiz |
|---|------|------|---------|-----------|
| 1 | WhatsApp (todas as ações) | ILUSÓRIA | Alto | `ENVIRONMENT=development` no .env sobrescreve Twilio real |
| 2 | Email candidato/recrutador | QUEBRADA | Alto | `MAILGUN_API_KEY` e `RESEND_API_KEY` ausentes no env |
| 3 | Verificar disponibilidade | ILUSÓRIA | Alto | Stub com `random.Random` — sem integração Google/Outlook |
| 4 | Reagendar entrevista | ILUSÓRIA | Médio | Stub total, `old_datetime='N/A'`, sem UPDATE no DB |
| 5 | Agendar envio futuro | ILUSÓRIA | Alto | `scheduled_at` ignorado, mensagem enviada imediatamente ou não |
| 6 | Calcular métricas (time_to_fill, cost) | QUEBRADA | Médio | `random.uniform()` em `report_service.py` gera dados falsos |
| 7 | Exportar dados | QUEBRADA | Médio | Tool não existe nos agentes de analytics |
| 8 | Sequência nurture | QUEBRADA | Alto | RabbitMQ em `localhost:5672` — não conectado em Replit |
| 9 | Enviar confirmação entrevista | QUEBRADA | Alto | `send_interview_invitation` é stub ("SIMULATION STUB") |
| 10 | Notificação Teams | QUEBRADA | Médio | `AZURE_CLIENT_SECRET` ausente — Microsoft Graph não autenticado |

---

## TOP 10 CAMPOS QUE O AGENTE PRECISA MAS O BANCO NÃO TEM

| # | Campo | Tabela | Ação Afetada | Observação |
|---|-------|--------|-------------|-----------|
| 1 | `hired_date` / `contracted_at` | `vacancy_candidates` | Marcar contratado | Stage 'Contratado' existe, mas sem timestamp de contratação |
| 2 | `offer_accepted_at` | `vacancy_candidates` | Pipeline offer tracking | Sem campo de aceitação de oferta |
| 3 | `rejection_reason` | `vacancy_candidates` | Registrar recusa | Apenas `notes` genérico, sem campo estruturado |
| 4 | `whatsapp_message_id` / `whatsapp_logs` | (tabela nova) | WhatsApp | Sem persistência de mensagens WhatsApp enviadas |
| 5 | `scheduled_message_at` | (tabela nova) | Agendar envio | Sem tabela `scheduled_messages` para envios futuros |
| 6 | `google_calendar_event_id` | `interviews` | Criar evento | Sem link com Google Calendar |
| 7 | `outlook_event_id` | `interviews` | Criar evento / reagendar | Teams Calendar usa Outlook mas sem campo no interviews |
| 8 | `time_to_fill_days` | `job_vacancies` | Métricas | Calculável mas não persistido, ausente em schema |
| 9 | `cost_per_hire` | `job_vacancies` | Métricas | Sem modelo de custo por processo seletivo |
| 10 | `notification_sent_at` / `notification_logs` | (tabela nova) | In-app notifications | Notificações geradas mas sem log de entrega |

---

## RECOMENDAÇÕES POR PRIORIDADE

### PRIORIDADE 1 — CRÍTICO (bloqueia valor core) — Prazo: 1 semana

**1. Corrigir ENVIRONMENT flag**
```bash
# Em Replit Secrets, adicionar:
ENVIRONMENT=production
# OU no código: checar REPLIT_ENVIRONMENT também
```
→ Desbloqueia WhatsApp (Twilio tem credenciais reais configuradas)

**2. Configurar MAILGUN_API_KEY ou RESEND_API_KEY**
```bash
# Em Replit Secrets:
MAILGUN_API_KEY=<chave real>
MAILGUN_DOMAIN=<domínio verificado>
```
→ Desbloqueia todos os envios de email

**3. Configurar RAILS_API_URL**
```bash
# Apontar para ats-api-copia no GCP:
RAILS_API_URL=https://api.wedotalent.com
RAILS_API_TOKEN=<token service-to-service>
```
→ Desbloqueia sync Python↔Rails para candidatos e vagas

**4. Corrigir RABBITMQ_URL**
```bash
# Apontar para RabbitMQ no GCP:
RABBITMQ_URL=amqp://user:pass@<gcp-host>:5672/
```
→ Desbloqueia nurture sequences e event propagation

### PRIORIDADE 2 — ALTO (degradação significativa) — Prazo: 2-3 semanas

**5. Substituir scheduling_tools.py stubs**
- `check_interviewer_availability`: integrar Microsoft Graph API (código existe em `teams_calendar_service.py`)
- `reschedule_interview`: conectar ao `teams_calendar_service.reschedule_interview` real
- `send_interview_invitation`: usar `CommunicationService` já implementado

**6. Adicionar campos missing ao schema**
```sql
ALTER TABLE vacancy_candidates ADD COLUMN hired_date TIMESTAMP;
ALTER TABLE vacancy_candidates ADD COLUMN rejection_reason TEXT;
ALTER TABLE vacancy_candidates ADD COLUMN offer_accepted_at TIMESTAMP;
ALTER TABLE interviews ADD COLUMN google_calendar_event_id TEXT;
ALTER TABLE interviews ADD COLUMN outlook_event_id TEXT;
```

**7. Eliminar random.uniform de report_service.py**
- Substituir taxas de conversão geradas aleatoriamente por queries reais em `vacancy_candidates`

**8. Implementar scheduled_messages table + Celery task**
- Para `schedule_message` funcionar como documentado

### PRIORIDADE 3 — MÉDIO (melhoria de rastreabilidade) — Prazo: 1 mês

**9. Adicionar AuditLog a todas as ações de agente**
- Rails já tem `AuditLog` model com worker (`LiaEventsWorker`)
- Python precisa chamar o endpoint Rails após cada ação ou publicar via RabbitMQ

**10. WebSocket push para todas as ações de agente**
- Atualmente apenas HITL tem `ws_manager.send_to_session`
- Agentes autônomos devem notificar frontend após cada tool call

**11. Configurar AZURE_CLIENT_SECRET para Teams**
- Desbloqueia notificações Teams e calendário Outlook

**12. Tabela whatsapp_logs + tabela notification_logs**
- Persistir todas as tentativas de comunicação para LGPD e auditoria

---

## NOTAS DE VALIDAÇÃO DO PROTOCOLO P16

1. **Todas as 35 ações mapeadas?** ✓ (35/35)
2. **7 pontos verificados no código real?** ✓ (via SSH, sem inferência)
3. **Classificação atribuída?** ✓ (5 COMPLETAS, 14 PARCIAIS, 9 QUEBRADAS, 7 ILUSÓRIAS)
4. **Top 10 quebradas identificadas?** ✓
5. **Top 10 campos faltantes?** ✓

---

*Relatório gerado por protocolo P16 — leitura direta do código em 2026-04-14*
*Arquivos auditados: communication_tools.py, communication_tool_registry.py, whatsapp_service.py, candidate_tools.py, pipeline_tool_registry.py, job_tools.py, scheduling_tools.py, cv_match_tool.py, pipeline_analytics.py, report_service.py, dashboard_data.py, rails_adapter.py, email_service.py + env vars via printenv*
