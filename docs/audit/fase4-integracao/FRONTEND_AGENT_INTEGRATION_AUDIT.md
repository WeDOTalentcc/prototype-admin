# FRONTEND_AGENT_INTEGRATION_AUDIT.md — Auditoria Frontend <> Agente (Experiência Unificada)
**Protocolo:** P20  
**Data:** 2026-04-14  
**Auditor:** Claude Opus 4.6  
**Repositórios auditados:**
- Frontend: `plataforma-lia/` (Next.js 15 + TypeScript, Replit)
- IA Layer: `lia-agent-system/` (Python + FastAPI, Replit)
- Backend: `ats-api-copia/` (Rails 7.1, GitHub wedocc2026/wedotalentcc, deploy GCP)
- Contexto: Frontend + IA no Replit, Backend no GCP. Integração Rails<>Python via RabbitMQ (em configuração). Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** P01 (PLATFORM_MAP)  
**Alimenta:** P21

---

## SCORE GERAL: 3.4 / 5

| Dimensão | Score | Peso |
|----------|-------|------|
| Reflexo de Ações no Frontend | 3.0/5 | 25% |
| Streaming de Respostas | 4.0/5 | 20% |
| Capabilities Match | 3.5/5 | 20% |
| Estado do Chat / Conversa | 3.5/5 | 15% |
| Formulários e Inputs | 3.0/5 | 10% |
| Visualização de Decisões | 3.5/5 | 10% |

---

## 1. REFLEXO DE ACOES DO AGENTE NO FRONTEND

### Mecanismo de Atualização

O frontend usa uma arquitetura de transporte dual:

| Protocolo | Uso | Arquivo |
|-----------|-----|---------|
| **WebSocket** (primário) | Chat real-time bidirecional | `src/hooks/chat/useChatSocket.ts` via `useAgentStreaming` |
| **SSE** (fallback) | Streaming de respostas quando WS falha | `src/app/api/lia/chat/stream/route.ts` |
| **HTTP REST** (BFF proxy) | CRUD, ações pontuais | `src/app/api/backend-proxy/**/*.ts` (~478 rotas) |
| **ActionCable WS** (Rails) | Workflow Rail updates | `src/components/workflow-rail/useWorkflowRail.ts` |
| **Polling** (fallback) | Quando ActionCable indisponível | Cada 30s via `setInterval` |

**TransportModeIndicator** (`src/components/unified-chat/TransportModeIndicator.tsx`): Mostra WS/SSE/OFF no dev mode. Invisível em produção.

### Mapa de Reflexo por Acao

| Acao do Agente | Reflete no Frontend? | Como? | Latencia | Consistente? |
|----------------|---------------------|-------|----------|-------------|
| **Resposta de chat** | SIM | WS streaming token-by-token + SSE fallback | ~100ms primeiro token | SIM |
| **Mover candidato no pipeline** | PARCIAL | BFF proxy -> API -> refetch manual | 1-3s (round-trip HTTP) | Kanban requer refresh manual em alguns cenários |
| **Enviar email** | SIM | BFF proxy -> resposta no chat | 1-2s | SIM |
| **Enviar WhatsApp** | SIM | BFF proxy -> resposta no chat | 1-2s | Depende ENVIRONMENT=production no Replit |
| **Agendar entrevista** | SIM | InterviewConfirmationCard no chat | 1-2s | SIM |
| **Atualizar score WSI** | PARCIAL | Resultado aparece no chat, mas painel de candidato precisa reload | 2-5s chat + manual | NAO |
| **Gerar relatorio** | SIM | BackgroundTaskEvent -> notificação no chat | Async, 5-30s | SIM |
| **Publicar vaga** | SIM | BFF proxy -> navegação de confirmação | 1-2s | SIM |
| **Buscar candidatos** | SIM | Resultados inline no chat + side panel | 2-10s | SIM |
| **Triagem de CV** | SIM | AsyncJobProgress com WS updates | Async, 10-60s | SIM |
| **Calibração** | PARCIAL | Sugestões no chat, mas dashboard separado | N/A | NAO |
| **HITL (Human-in-the-Loop)** | SIM | approval_required event -> UI de aprovação | Real-time | SIM |
| **Fairness warnings** | SIM | FairnessWarningBanner inline | Real-time | SIM |
| **Background tasks** | SIM | BackgroundAgentsStatus + BackgroundTaskNotification | Real-time | SIM |
| **Plan progress** | SIM | PlanProgressCard com steps | Real-time | SIM |

### Achados Criticos no Reflexo

1. **KANBAN NAO ATUALIZA EM REAL-TIME**: Quando o agente move um candidato via tool `move_candidate`, o Kanban board NAO recebe push. Requer polling (30s) ou refresh manual. O ActionCable para WorkflowChannel existe mas depende de `NEXT_PUBLIC_RAILS_WS_URL` que esta vazio.

2. **WSI SCORE DESCONECTADO**: Score calculado pelo agente aparece na resposta do chat, mas o painel lateral do candidato NAO atualiza automaticamente — precisa de navegação/refresh.

3. **CALIBRACAO ISOLADA**: CalibrationService produz sugestões que aparecem no dashboard de calibração (`/calibration`), mas o chat NAO referencia essas sugestões proativamente.

4. **RAILS NAO CONECTADO AO FRONTEND**: `NEXT_PUBLIC_RAILS_WS_URL` e `NEXT_PUBLIC_RAILS_URL` estão vazios/comentados. ActionCable do Rails NAO funciona. Workflow Rail cai para polling de 30s ou fica sem dados. **Isso sera resolvido quando a integração GCP estiver completa, mas hoje impacta toda atualização real-time que depende do Rails.**

---

## 2. STREAMING DE RESPOSTAS DO AGENTE

### Arquitetura de Streaming

```
Browser                   Next.js BFF              Python FastAPI
  |                         |                         |
  |-- WS connect ---------->| (auth ws-token)          |
  |                         |-- WS /ws/chat/{sid} --->|
  |<-- token stream --------|<-- SSE chunks ----------|
  |                         |                         |
  |-- HTTP POST (fallback)  |                         |
  |     /api/lia/chat/stream|-- POST /api/v1/chat/    |
  |<-- SSE stream ----------|<-- stream -------------->|
```

### Detalhes

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Token-by-token streaming** | SIM | Via `useAgentStreaming` hook -> WS ou SSE |
| **Protocolo primario** | WebSocket | `/ws/chat/{sessionId}` com auth token |
| **Protocolo fallback** | SSE | `POST /api/lia/chat/stream` -> `text/event-stream` |
| **Auto-detection** | SIM | Se WS falha, cai para SSE automaticamente |
| **Thinking indicator** | SIM | `isThinking` state + `thinkingSteps[]` array |
| **Tool calls durante streaming** | SIM | Plan progress steps mostram "Buscando...", "Analisando..." via `PlanProgressCard` |
| **Errors durante streaming** | SIM | `error` state exibido, SSE envia `data: {"error": ...}` |
| **Reconnect automatico** | SIM | WS reconnect com backoff, `reconnectAttempt` counter exibido |
| **PII masking** | SIM | `maskPII()` em `lia-chat-connection-types.ts` — CPF, email, telefone |

### Eventos Especiais Durante Streaming

| Evento | Handler | UI Element |
|--------|---------|------------|
| `thinking` | Mostra thinking steps | TypingIndicator + step list |
| `plan_progress` | Steps do plano de execução | PlanProgressCard |
| `approval_required` | HITL pause | Botões Aprovar/Rejeitar |
| `panel_update` | Abre side panel dinâmico | DynamicContextPanel |
| `background_task_update` | Progresso assíncrono | BackgroundAgentsStatus |
| `message` | Resposta final | Message bubble com markdown |
| `fairness_warnings` | Alerta de bias | FairnessWarningBanner |

**Veredicto: 4.0/5** — Streaming sofisticado com WS+SSE dual, thinking indicator, plan progress, HITL. Excelente UX durante processamento.

---

## 3. CAPACIDADES DO FRONTEND vs. CAPACIDADES DO AGENTE

### Features no Frontend COM suporte de agente

| Feature no Frontend | Componente | Agente/Servico Backend | Status |
|--------------------|-----------|-----------------------|--------|
| Chat conversacional | LiaChatPanel + UnifiedMessageList | MainOrchestrator -> CascadedRouter -> Domain agents | SIM |
| Job Wizard conversacional | `src/components/job-wizard/stages/*.tsx` (7 stages) | WizardReActAgent + FeedbackLearningService | SIM |
| Busca de candidatos | Smart Search Input + SearchResultsCard | SourcingReActAgent + multi_strategy_search | SIM |
| Triagem de CV | CV upload + AsyncJobProgress | CVScreeningBatchService (WSI) | SIM |
| Agendamento de entrevista | InterviewConfirmationCard | InterviewGraph (LangGraph StateGraph) | SIM |
| Email templates | EmailTemplatesManager | CommunicationReActAgent | SIM |
| WhatsApp messaging | BFF proxy /communication/send-whatsapp | CommunicationReActAgent | SIM (depende ENVIRONMENT) |
| Calibração | CalibrationStage no wizard | CalibrationService | SIM |
| Agent Studio | AgentStudioPage | AgentStudioDomain + CustomAgentRuntime | SIM |
| Voice screening | VoIPCallButton + AudioRecordButton | VoiceInterviewStateMachine | SIM |
| Feedback thumbs up/down | UnifiedMessageList -> submitThumbsFeedback | CalibrationService (implicit feedback) | SIM |
| HITL approval | Chat inline approve/reject | MainOrchestrator PendingAction | SIM |
| Background task tracking | BackgroundAgentsStatus | Celery tasks + WS events | SIM |
| Fairness warnings | FairnessWarningBanner | FairnessGuard pre-check | SIM |
| Navigation hints | NavigationHintCard | Agent response metadata.navigation_hint | SIM |
| Tasting insights | TastingInsightCard | ProactiveInsightsService | SIM |
| Weekly digest | WeeklyDigestChatMessage | AnalyticsReActAgent | SIM |

### Features no Agente SEM frontend (Capacidades Invisiveis)

| Capacidade do Agente | Arquivo | Sem Frontend? | Impacto |
|---------------------|---------|---------------|---------|
| **ML Predictions** (time-to-fill, salary) | `app/api/v1/ml_predictions.py` | SIM — API existe mas nenhuma tela consome | Alto: recrutador nunca ve predições |
| **Learning Outcomes patterns** | `app/api/v1/learning_outcomes.py` | SIM — API existe, sem dashboard | Médio: padrões de contratação invisíveis |
| **Calibration Dashboard completo** | `app/api/v1/calibration.py` | PARCIAL — endpoints existem, frontend mínimo | Alto: divergências LIA<>recrutador invisiveis |
| **Search Feedback analytics** | `app/api/v1/search_feedback.py` | SIM — coleta dados sem visualização | Baixo: dados coletados para futuro |
| **Suggestion acceptance rates** | `app/api/v1/suggestion_feedback.py` | SIM — stats endpoint sem tela | Médio: não sabe o que LIA acerta/erra |
| **Digital Twin inference** | `app/services/twin_inference_service.py` | SIM — servico existe, sem UI para configurar twin | Alto: feature premium sem interface |
| **Model Registry / A-B testing** | `app/services/ml/model_registry.py` | SIM — API de comparação sem dashboard | Baixo: admin-level |
| **Agent Quality metrics** | `app/api/v1/agent_quality.py` | SIM — endpoint existe sem dashboard | Medio: observabilidade dos agentes invisivel |

### Features no Frontend SEM agente (Botoes Decorativos)

| Feature no Frontend | Componente | O que acontece ao clicar |
|--------------------|-----------|-----------------------|
| **Comparar candidatos** | `candidates/compare/route.ts` | Chama API que retorna comparação — funciona, mas sem ML/ranking inteligente |
| **Promote to base** | `promoteCandidateToBase` | Move candidato de Pearch para base local — funciona sem IA |
| **Bulk delete** | `candidates/bulk/delete/route.ts` | CRUD puro, sem validação de agente |
| **Export candidatos** | `candidates/bulk/export/route.ts` | CRUD puro |
| **Auto-enrich** | `company/auto-enrich` | Chama API — depende de Pearch credits |

**Veredicto: 3.5/5** — Boa cobertura para features core. Gap: ~8 capacidades do backend são invisiveis ao recrutador (ML predictions, calibration analytics, digital twin). Features premium existem no backend mas não têm UI.

---

## 4. ESTADO DO CHAT / CONVERSA

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Historico persiste entre sessoes** | SIM | Via `loadChatHistory(conversationId)` -> backend API | 
| **Conversas anteriores navegaveis** | SIM | `showHistory` toggle com `recentChats[]` list |
| **Contexto da vaga carregado** | SIM | `contextPage` + `entityContext` injetados automaticamente via `resolveScopeFromPathname` |
| **Multiplas conversas simultaneas** | PARCIAL | Pode trocar conversa (SwitchTaskModal, Cmd+K), mas uma de cada vez ativa |
| **"O que o agente esta fazendo"** | SIM | ThinkingIndicator + thinkingSteps[] + PlanProgressCard + BackgroundAgentsStatus |
| **Conversation ID sync** | SIM | `conversationIdFromWs` sync do backend, persiste em `LiaChatContext` |
| **Chat modes** | SIM | `ChatMode`: sidebar (420px), fullscreen (720px), split-view |
| **Message actions** | SIM | Copy, Insert, ThumbsUp, ThumbsDown por mensagem |
| **Quick actions / chips** | SIM | `handleChipSend` para sugestões de ação contextual |
| **Command palette** | SIM | Cmd+K para trocar de tarefa/conversa |
| **Agent memory indicator** | SIM | `agent-memory-indicator.tsx` mostra se agente esta usando memória |

### Modelo de Sessao

```
LiaChatContext (React Context)
  |
  |-- chatConversationId (string | null)
  |-- chatMessages (LiaChatMessage[])
  |-- chatIsConnected (boolean)
  |-- chatIsStreaming (boolean)
  |-- chatStreamingContent (string)
  |-- chatHitlPending (HITLPending | null)
  |-- chatBackgroundTasks (BackgroundTaskEvent[])
  |-- chatFairnessWarnings (string[])
  |
  |-- sendChatMessage(content, domain?, scope?)
  |-- sendApproval(approved)
  |-- initChatConversation(firstMessage, contextType?)
  |-- loadChatHistory(conversationId)
  |-- connectChat() / disconnectChat()
```

**Veredicto: 3.5/5** — Modelo de sessão robusto com contexto automático, historico, modes, command palette. Gap: apenas uma conversa ativa por vez (sem split-chat com 2 vagas diferentes).

---

## 5. FORMULARIOS E INPUTS ESTRUTURADOS

### Job Wizard — Hibrido Chat + Formulário

O Job Wizard usa 7 stages estruturados com forms:

| Stage | Componente | Dados via | Agente envolvido |
|-------|-----------|-----------|------------------|
| Input Evaluation | `InputEvaluationStage.tsx` | Formulário | WizardReActAgent interpreta |
| Job Description | `JobDescriptionStage.tsx` | Formulário + LIA sugere | WizardReActAgent gera/ajusta |
| Competencies | `CompetenciesStage.tsx` | Side panel multi-select | WizardReActAgent sugere |
| Salary | `SalaryStage.tsx` | Formulário com benchmark | OutcomePredictor (heurístico) |
| WSI Questions | `WSIQuestionsStage.tsx` | Formulário estruturado | WSI scoring config |
| Calibration | `CalibrationStage.tsx` | Chat + aprovação manual | CalibrationService |
| Review & Publish | `ReviewPublishStage.tsx` | Resumo + confirmação | BFF -> API publish |

### Chat vs. Formulário

| Cenario | Método | Detalhes |
|---------|--------|----------|
| **Nova vaga** | Hibrido | Wizard com forms + LIA sugere valores via chat |
| **Busca de candidatos** | Chat-first | Smart Search Input parseado -> API estruturada |
| **Enviar email** | Side panel | EmailComposer como side panel (SidePanelType) |
| **Agendar entrevista** | Chat -> Card | Agente coleta dados via chat, confirma com InterviewConfirmationCard |
| **Upload CV** | File picker + chat | File attached -> LIA analisa |
| **Configurar pipeline** | Formulário puro | Settings page, sem agente |
| **Configurar LLM** | Formulário puro | Admin LLM Config page |
| **Calibração** | Chat -> Dashboard | Chat para feedback, dashboard para analytics |

### Validação

| Camada | Existe? | Detalhes |
|--------|---------|----------|
| **Frontend** | SIM | Zod/Pydantic schemas, form validation |
| **BFF Proxy** | MINIMA | Proxy passa para backend, pouca validação |
| **Backend Python** | SIM | Pydantic models em todos os endpoints |
| **Agente** | SIM | Agentes extraem dados estruturados de texto livre via LLM |
| **Consistente?** | PARCIAL | Frontend e backend validam, mas regras podem divergir (ex: max_salary no frontend vs backend) |

**Veredicto: 3.0/5** — Wizard hibrido é elegante. Gap: validação entre frontend e backend não centralizada — possível divergência de regras.

---

## 6. VISUALIZACAO DE DECISOES DO AGENTE

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **POR QUE o agente decidiu** | PARCIAL | Respostas incluem reasoning em markdown, mas não em formato estruturado |
| **Ranking mostra scores** | SIM | WSIScoreCard mostra score + breakdown (tecnico/comportamental) |
| **Ranking mostra justificativas** | PARCIAL | Chat mostra reasoning, mas lista de candidatos mostra apenas score numerico |
| **Avaliação mostra criterios** | SIM | CandidateSummaryCard com match score + skills |
| **Debug mode para power users** | PARCIAL | TransportModeIndicator (dev only), mas sem "explain this decision" button |
| **Execution plan visible** | SIM | PlanProgressCard com steps: "Buscando...", "Analisando...", "Rankeando..." |
| **ThinkingSteps visible** | SIM | Array de steps mostrado durante processing |
| **Navigation hints** | SIM | NavigationHintCard com link para pagina relevante |
| **Agent memory indicator** | SIM | Mostra quando agente usa memória de longo prazo |
| **Fairness transparency** | PARCIAL | FairnessWarningBanner mostra warnings, mas sem explicação detalhada |

### UI Actions System

O frontend tem um sistema sofisticado de UI Actions (`src/components/ui-actions/types.ts`):

**Side Panel Types (16):** compensation_benefits, technical_requirements, behavioral_competencies, languages, benefits_detailed, wsi_questions, interview_scheduling, candidate_evaluation, calibration_feedback, job_requirements, candidate_profile, search_filters, ats_field_mapping, ats_sync_status, email_composer, whatsapp_composer

**Chat Card Types (15):** candidate_summary, job_summary, compensation_summary, interview_confirmation, wsi_score, market_analysis, calibration_sample, search_results_preview, progress_tracker, stage_transition, email_preview, whatsapp_preview, dashboard_metrics, sync_status, company_benefits

**Chat Action Types (8):** confirm_proceed, select_option, quick_feedback, approve_reject, schedule_options, edit_data, send_message, export_data

**Veredicto: 3.5/5** — Sistema de UI actions rico. Gap: "explain this decision" não existe como feature explicita — reasoning está embebido no texto do chat, não em componente estruturado.

---

## INTEGRACAO RAILS <> FRONTEND (Gap Critico)

### Status Atual

| Aspecto | Status | Variavel de Ambiente |
|---------|--------|---------------------|
| **NEXT_PUBLIC_RAILS_URL** | VAZIO/COMENTADO | Frontend NAO chama Rails diretamente |
| **NEXT_PUBLIC_RAILS_WS_URL** | VAZIO | ActionCable NAO conecta |
| **BACKEND_URL** | `http://127.0.0.1:8001` | Frontend -> Python API (funciona) |
| **BFF Proxy** | Funcional | 478 rotas proxying para Python |

### Consequencias

1. **WorkflowRail**: Cai para polling de 30s ou fica sem dados (campaigns não carregam do Rails)
2. **ActionCable**: Completamente offline — nenhum push do Rails chega ao frontend
3. **Pipeline real-time**: Stage transitions no Rails NAO refletem imediatamente no frontend
4. **Notifications do Rails**: NAO chegam ao frontend via ActionCable

**Quando integração GCP estiver completa:** Configurar `NEXT_PUBLIC_RAILS_URL` e `NEXT_PUBLIC_RAILS_WS_URL` no GCP resolve toda essa categoria de gaps.

---

## RECOMENDACOES PRIORIZADAS

### P0 — Configurar NEXT_PUBLIC_RAILS_URL/WS_URL no Deploy GCP
**O que:** Quando deploy integrado, configurar variáveis para frontend acessar Rails
**Impacto:** Desbloqueia ActionCable, WorkflowRail, notifications push
**Esforço:** S (configuração, não código)

### P0 — Kanban Real-Time via WS/SSE
**O que:** Quando agente move candidato, emitir evento que Kanban consuma (via WS ou SSE channel)
**Impacto:** Kanban reflete ações do agente instantaneamente
**Esforço:** M (criar channel + consumer no frontend)

### P1 — ML Predictions Dashboard
**O que:** Criar UI para consumir /ml/predict/* (time-to-fill, salary, skill success)
**Impacto:** Recrutador ve predições. 4 endpoints ML ficam visíveis
**Esforço:** M (3-5 dias frontend)

### P1 — Calibration Analytics Dashboard
**O que:** Criar tela para /calibration/dashboard, /calibration/divergences, /calibration/weights
**Impacto:** Recrutador ve onde LIA acerta/erra e pode calibrar
**Esforço:** M (3-5 dias frontend)

### P2 — "Explain This Decision" Button
**O que:** Botão em cada WSI score / ranking que mostra reasoning estruturado do agente
**Impacto:** Transparência para o recrutador, compliance LGPD (direito a explicação)
**Esforço:** S (dados já existem no metadata, falta UI)

### P2 — WSI Score Refresh Automatico
**O que:** Quando agente calcula score, emitir evento para atualizar painel lateral do candidato
**Impacto:** Score sempre atualizado sem refresh manual
**Esforço:** S (1-2 dias)

### P2 — Digital Twin Configuration UI
**O que:** Interface para criar/configurar Digital Twins (feature premium sem frontend)
**Impacto:** Desbloqueia feature de alto valor
**Esforço:** L (5-7 dias frontend + integração)

---

## RESUMO EXECUTIVO

### O que funciona muito bem
1. **Streaming dual WS+SSE** com fallback automático — experiência de chat fluida
2. **UI Actions System** com 16 side panels, 15 chat cards, 8 action types — rico e extensível
3. **HITL completo** — approval_required pause, approve/reject inline, fairness warnings
4. **Plan progress** — recrutador ve cada step do agente em tempo real
5. **Background task tracking** — tasks assíncronas com notificação de conclusão
6. **Job Wizard hibrido** — formulários estruturados + sugestões de IA via chat

### O que precisa de atenção
1. **~8 capacidades do backend são invisiveis** (ML predictions, calibration analytics, digital twin, learning outcomes)
2. **ActionCable offline** — Rails NAO push para frontend (será resolvido com integração GCP)
3. **Kanban NAO real-time** — ações do agente não refletem instantaneamente
4. **Validação divergente** — frontend e backend validam independentemente
5. **"Explain decision" inexistente** — transparency gap para compliance

### Metafora
O frontend é como um cockpit de avião moderno — instrumentos sofisticados (streaming, plan progress, HITL, fairness) com boa visibilidade do que o piloto automático (agente) está fazendo. Mas metade dos sensores do motor (ML predictions, calibration, digital twin) não estão conectados aos mostradores do cockpit. O piloto voa bem com o que tem, mas poderia voar muito melhor se visse todos os dados.

### Score por Prioridade de Fix
| Fix | Impacto | Esforço | Score |
|-----|---------|---------|-------|
| RAILS_URL/WS_URL no GCP | Alto | S | P0 |
| Kanban real-time | Alto | M | P0 |
| ML Predictions dashboard | Alto | M | P1 |
| Calibration dashboard | Alto | M | P1 |
| Explain Decision button | Medio | S | P2 |
| WSI Score auto-refresh | Medio | S | P2 |
| Digital Twin UI | Alto | L | P2 |
