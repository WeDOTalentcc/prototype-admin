# AGENT BEHAVIOR SPECIFICATIONS — P39
**Data:** 2026-04-14
**Auditor:** Claude Opus 4.6 (1M context)
**Base:** 14 ReAct agents + 4 StateGraphs + 1 CustomAgentRuntime
**Contexto:** AI-first agentic platform for human capital. Recrutamento = primeiro dominio; plataforma expande para onboarding, performance, employee experience.

---

## INFRAESTRUTURA COMPARTILHADA (o que TODOS os agentes herdam)

| Componente | O que provê | Arquivo |
|-----------|-------------|---------|
| `LangGraphReActBase` | ReAct loop nativo (create_react_agent), PII strip (LIA-C04), FairnessGuard auto-check (LIA-C05), AuditCallback, TimedToolNode (15s), PostgresSaver, streaming | `libs/agents-core/langgraph_react_base.py` |
| `EnhancedAgentMixin` | Memory (working + long-term), CalibrationWeight load/cache, AutonomyEngine, LearningExtractor, post-loop learning, insight/proactive/predictive tools | `libs/agents-core/enhanced_agent_mixin.py` |
| `compliance_block.yaml` | LGPD, fairness, bias, audit — 3 variantes (decision/communication/operational) | `app/prompts/shared/` |
| `guardrails_block.yaml` | Identity, hallucination, prompt security, multi-tenancy, negation, autonomy, escalation, error handling, data safety | `app/prompts/shared/` |
| `protected_attributes.yaml` | 14 atributos protegidos com base legal, aliases, categorias | `app/config/` |

**Baseline herdado por todos os agentes:** PII strip + FairnessGuard + AuditCallback + compliance prompt + guardrails prompt + memory + learning + calibration weights.

---

## BEHAVIOR SPECS POR AGENTE

---

### 1. SourcingReActAgent — Busca de Talentos

**Identidade:** Especialista em busca ativa. Busca em banco interno (LIA) + externo (Pearch AI 190M+ perfis). Enriquecimento via Apify. Serve recrutadores que precisam encontrar candidatos.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo create_react_agent com PostgresSaver. Max 5 iteracoes. Loop real com tool calls + observations. Sem self-correction explicita mas re-planning via LLM. |
| **D2 Tool Design** | 5 | 18 tools tipadas (ToolDefinition dataclass). FC nativo. Conectam a backends reais (Pearch AI, Apify, PostgreSQL, pgvector). Stage-based tool filtering (5 stages). Error handling por tool. |
| **D3 Inteligencia** | 4 | Prompt com vocabulario de sourcing (boolean queries, shortlist, fit). Proativo (sugere refinamentos quando <5 ou >50 resultados). Score 0-100% com justificativa. Few-shot examples. |
| **D4 Self-Correction** | 3 | FairnessGuard bloqueia discriminacao. Retry via LangGraph loop. Fallback Pearch→banco local. Sem deteccao explicita de inconsistencia. |
| **D5 Context Engineering** | 4 | DOMAIN_INSTRUCTIONS + few-shot + reasoning prompt. TenantContext injetado via mixin. Memory context. Stage context. ~2K tokens de prompt. |
| **D6 Compliance** | 5 | compliance_block (decision), guardrails, FairnessGuard L3, HITL para outreach (AUD-4), audit trail (SEG-5). Consent check antes de contato. |
| **D7 Extensibilidade** | 4 | Prompt YAML separado. Tools registradas externamente. Heranca limpa. Poderia virar "SourcingAgent para Treinamentos" mudando prompt + tools. Stage-based tool filtering e reutilizavel. Acoplamento: tool wrappers referenciam models de candidato. |
| **D8 Integracao Plataforma** | 5 | LLM Factory (via base), CalibrationWeight (via mixin), TenantContext, WebSocket streaming, memory, learning, audit. Full integration. |

**SCORE TOTAL: 34/40** — PRONTO
**Recomendacao:** Polimento. O agente mais completo da plataforma. Sub-agent architecture (11 sub-agentes) e sofisticada.

---

### 2. PipelineTransitionAgent — Movimentacao no Pipeline

**Identidade:** Assistente para mover candidatos entre etapas. Extrai preferencias, valida transicoes, agenda tarefas secundarias. Serve recrutadores gerenciando pipeline.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo. Loop real com multi-tool. Action behavior (passive/active) configura tools disponiveis. |
| **D2 Tool Design** | 5 | 17+ tools. FC nativo. Backends reais (DB, calendar, Teams). check_rejection_fairness obrigatorio antes de rejeicao. Stage-based filtering. |
| **D3 Inteligencia** | 4 | Prompt v3.0 com calibracao por porte (startup/PME/corporacao). Anti-sycophancy. Proativo (sugere sub-status, detecta padroes do recrutador). Conciso (max 3 frases). |
| **D4 Self-Correction** | 4 | check_rejection_fairness ANTES de rejeitar. Valida transicao antes de executar. Fallback quando tool falha. HITL para acoes irreversiveis. |
| **D5 Context Engineering** | 4 | Prompt com candidate_name, job_title, from_stage, to_stage injetados. Memory context. Guardrails por action_behavior. |
| **D6 Compliance** | 5 | Decision-type compliance. FairnessGuard L3. HITL obrigatorio. Audit trail. check_rejection_fairness tool dedicada. |
| **D7 Extensibilidade** | 4 | Prompt YAML. Tools registradas. action_behavior pattern reutilizavel. Poderia virar "OnboardingTransitionAgent" mudando stages + tools. |
| **D8 Integracao Plataforma** | 5 | Full: LLM Factory, CalibrationWeight, TenantContext, WebSocket, memory, recruiter preferences learning. |

**SCORE TOTAL: 35/40** — PRONTO
**Recomendacao:** Pronto para producao. O mais robusto em compliance (rejection fairness check).

---

### 3. PipelineReActAgent (CV Screening) — Triagem de CVs

**Identidade:** Especialista em avaliacao de curriculos e scoring WSI. Score por rubrica, ranking, recomendacao (avancar/revisao/rejeitar). Serve recrutadores triando candidatos.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo. Max 5 iteracoes. Loop com tool calls para scoring. |
| **D2 Tool Design** | 4 | Tools via get_pipeline_tools(). FC nativo. Conecta a RubricEvaluationService real. Scoring por taxonomia Bloom/Dreyfus. |
| **D3 Inteligencia** | 4 | Vocabulario de triagem (red flags, job hopping, gaps). Score 0-100% com thresholds. Frontier zone (60-70%) → revisao humana. Bloom/Dreyfus assessment. |
| **D4 Self-Correction** | 3 | FairnessGuard pre-check. Nunca rejeita sem verificar. Frontier zone como safety net. Sem retry explicito em tool failure. |
| **D5 Context Engineering** | 4 | DOMAIN_INSTRUCTIONS + reasoning prompt. 7 blocos WSI no prompt. Stage definitions. |
| **D6 Compliance** | 5 | Decision-type compliance. FairnessGuard. Ignora atributos protegidos (nome, foto, endereco, estado civil, idade). Audit trail. |
| **D7 Extensibilidade** | 3 | Prompt YAML. Mas scoring logic acoplada a WSI methodology. Rubric framework e generico, mas Bloom/Dreyfus sao recruiting-specific. |
| **D8 Integracao Plataforma** | 4 | LLM Factory, memory, audit. CalibrationWeight agora consumido (item 12.3). |

**SCORE TOTAL: 31/40** — REFINAR
**Recomendacao:** Refinamento. Scoring methodology (WSI/Bloom/Dreyfus) e sofisticada mas acoplada ao dominio de recrutamento.

---

### 4. WizardReActAgent — Criacao de Vagas

**Identidade:** Assistente para criacao guiada de vagas. Wizard conversacional com etapas. Serve recrutadores criando vagas.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo. Stage transitions por confirmacao. Navigation logic com detection de palavras-chave. |
| **D2 Tool Design** | 5 | 9 tools. FC nativo. validate_job_requirements (FairnessGuard), salary benchmarks (DB + mercado), JD enrichment, draft health check. Stage-based tool mapping (6 stages). |
| **D3 Inteligencia** | 4 | Proativo (sugere skills, salarios, competencias). Health check proativo (identifica riscos). Salary benchmarks com dados de mercado. Few-shot + reasoning prompt. |
| **D4 Self-Correction** | 4 | validate_job_requirements bloqueia discriminacao ANTES de salvar. check_job_draft_health identifica riscos. Confirmacao antes de publicar. |
| **D5 Context Engineering** | 4 | WIZARD_DOMAIN_SPECIFIC + reasoning prompt. Stage context. Memory summary. |
| **D6 Compliance** | 5 | FairnessGuard em requirements. Linguagem inclusiva enforced. HITL para publicacao. Audit trail. |
| **D7 Extensibilidade** | 3 | Prompt YAML. Stage-based. Mas wizard logic hardcoded para vagas. Poderia virar "WizardTraining" com refactor significativo. |
| **D8 Integracao Plataforma** | 4 | LLM Factory, memory, audit. Salary benchmarks integrados. |

**SCORE TOTAL: 33/40** — PRONTO
**Recomendacao:** Pronto. Wizard pattern e reutilizavel para outros formularios guiados.

---

### 5. KanbanReActAgent — Assistente de Kanban

**Identidade:** Assistente pessoal do recrutador no kanban. Proativo, conciso, orientado a acao. Serve recrutadores no dia-a-dia.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo. Stage transitions. Confirmation word detection. Field validation antes de navegacao. |
| **D2 Tool Design** | 4 | Tools via kanban_tool_registry. FC nativo. Sub-agents (search, action, insight). |
| **D3 Inteligencia** | 4 | Prompt "personal assistant" — proativo, sugere 2-3 acoes apos cada resposta. Talent intelligence features (skills ontology, internal mobility, market intelligence). Memory persistente. |
| **D4 Self-Correction** | 3 | FairnessGuard. Field validation. Sem retry explicito. |
| **D5 Context Engineering** | 4 | KANBAN_DOMAIN_SPECIFIC + few-shot + reasoning prompt. Stage context. Memory. |
| **D6 Compliance** | 4 | FairnessGuard. Guardrails. Audit. Nao e decision agent (menor exigencia). |
| **D7 Extensibilidade** | 4 | Prompt YAML. Domain override possivel. Sub-agent pattern reutilizavel. Poderia virar "ProjectKanbanAgent" para gestao de projetos. |
| **D8 Integracao Plataforma** | 4 | LLM Factory, memory, audit, streaming. |

**SCORE TOTAL: 31/40** — REFINAR
**Recomendacao:** Refinamento. Sub-agent architecture e boa mas pode ser mais autonoma.

---

### 6. CommunicationReActAgent — Comunicacao com Candidatos

**Identidade:** Gerenciador de comunicacao multi-canal (email, WhatsApp, Teams). Serve recrutadores enviando mensagens.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 3 | LangGraph nativo. Mas comunicacao tende a ser single-shot (gerar + enviar). Menos iterativo. |
| **D2 Tool Design** | 4 | 5 tools (send_email, send_whatsapp, get_history, schedule_message, check_rate_limit). FC nativo. Backends reais (EmailService, Twilio, Teams webhook). |
| **D3 Inteligencia** | 3 | Prompt com regras de tom. Footer obrigatorio. Bulk confirmation. Mas menos proativo que outros agentes. |
| **D4 Self-Correction** | 4 | check_rate_limit ANTES de enviar. Consent LGPD verificado. Horario restrito (8h-20h). Opt-out respeitado. |
| **D5 Context Engineering** | 3 | Prompt YAML com regras claras. Mas menos context de plataforma (sem stage, sem vaga). |
| **D6 Compliance** | 5 | Communication-type compliance. Rate limit. Consent. Horario. Footer. Bulk approval. Rejection feedback requires review. Top compliance. |
| **D7 Extensibilidade** | 5 | Tools sao channel-agnostic. Prompt YAML. Poderia virar "CommunicationAgent para Onboarding" ou "Employee Experience" sem mudar nada estrutural. Padroes (rate limit, consent, scheduling) sao universais. |
| **D8 Integracao Plataforma** | 4 | LLM Factory, memory, audit, multi-channel. |

**SCORE TOTAL: 31/40** — REFINAR
**Recomendacao:** Refinamento. O mais extensivel da plataforma — padrao de comunicacao se aplica a QUALQUER dominio de RH.

---

### 7. PolicyReActAgent — Politicas de Contratacao

**Identidade:** Especialista em compliance de politicas de contratacao. Valida, edita, sugere politicas. Serve gestores de RH.

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| **D1 ReAct Loop** | 4 | LangGraph nativo. HITL integrado (solicita aprovacao). 30+ confirmation words. |
| **D2 Tool Design** | 4 | Policy tools. FC nativo. validate_policy_compliance obrigatorio. |
| **D3 Inteligencia** | 4 | Prompt com base legal (LGPD, Lei 9.029/95, CLT). Cita lei quando recruiter insiste. Escalation quando risk_score > 0.8. |
| **D4 Self-Correction** | 4 | validate_policy_compliance ANTES de salvar. Detecta discriminacao. Escalation automatica. |
| **D5 Context Engineering** | 4 | 5 config blocks. Prompt com criterios proibidos explicitos. |
| **D6 Compliance** | 5 | Decision-type compliance. Validation obrigatoria. Escalation. Base legal citada. |
| **D7 Extensibilidade** | 4 | Config blocks sao genéricos. Poderia virar "CompliancePolicyAgent" para qualquer dominio. Validation pattern reutilizavel. |
| **D8 Integracao Plataforma** | 4 | LLM Factory, memory, HITL, audit. |

**SCORE TOTAL: 33/40** — PRONTO
**Recomendacao:** Pronto. Compliance pattern e referencia para toda a plataforma.

---

### 8. AnalyticsReActAgent — Metricas e Insights

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | LangGraph nativo. Mas analytics tende a ser query→resposta. |
| D2 Tool Design | 3 | Analytics tools. Backends reais (DB queries). Menos granulares que sourcing/pipeline. |
| D3 Inteligencia | 4 | KPIs, anomalias, benchmarks setoriais. Confiabilidade quando amostra <30. |
| D4 Self-Correction | 2 | Sem retry explicito. Sem validacao de consistencia. |
| D5 Context Engineering | 3 | Prompt YAML. Menos context de plataforma. |
| D6 Compliance | 4 | LGPD (dados agregados). Guardrails. Audit. |
| D7 Extensibilidade | 5 | Analytics e 100% domain-agnostic. Mesmo pattern serve para HR analytics, finance, ops. |
| D8 Integracao Plataforma | 3 | LLM Factory, memory. Sem CalibrationWeight. |

**SCORE TOTAL: 27/40** — REFINAR

---

### 9. AutomationReActAgent — Automacoes

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | LangGraph nativo. Task decomposition. |
| D2 Tool Design | 3 | Automation tools. Task creation, SLA alerts. |
| D3 Inteligencia | 3 | Decomposicao de tarefas. Alertas proativos. |
| D4 Self-Correction | 3 | Confirmacao para acoes destrutivas. Log de execucao. |
| D5 Context Engineering | 3 | Prompt YAML. Regras de automacao. |
| D6 Compliance | 4 | Operational-type compliance. LGPD consent. |
| D7 Extensibilidade | 5 | Automacao e 100% domain-agnostic. Task/rule/alert pattern serve qualquer processo. |
| D8 Integracao Plataforma | 3 | LLM Factory, memory. |

**SCORE TOTAL: 27/40** — REFINAR

---

### 10. CompanySettingsReActAgent — Configuracao de Empresa

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | LangGraph nativo. Config collection. |
| D2 Tool Design | 4 | Company tools. FairnessGuard validation. Website extraction. |
| D3 Inteligencia | 3 | 6 config blocks. Sugestoes de completude. |
| D4 Self-Correction | 3 | FairnessGuard antes de salvar. |
| D5 Context Engineering | 4 | Few-shot + reasoning prompt. 6 blocos estruturados. |
| D6 Compliance | 4 | Ethical validation. Linguagem discriminatoria detectada. |
| D7 Extensibilidade | 4 | Config blocks pattern reutilizavel. Company setup → Department setup → Team setup. |
| D8 Integracao Plataforma | 3 | LLM Factory, memory, audit. |

**SCORE TOTAL: 28/40** — REFINAR

---

### 11. ATSIntegrationReActAgent — Integracao ATS

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | LangGraph nativo. Sync operations. |
| D2 Tool Design | 3 | ATS tools (Gupy, Pandape, Merge). |
| D3 Inteligencia | 2 | Sync bidirectional. Menos intelligence, mais middleware. |
| D4 Self-Correction | 2 | Sem retry sofisticado. |
| D5 Context Engineering | 2 | Prompt basico. |
| D6 Compliance | 3 | Operational compliance. |
| D7 Extensibilidade | 4 | Integration pattern reutilizavel. ATS → HRIS → Payroll. |
| D8 Integracao Plataforma | 3 | LLM Factory, basic. |

**SCORE TOTAL: 22/40** — REFATORAR

---

### 12. AutonomousReActAgent — Agente Cross-Domain (Tier 6)

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 5 | Max 10 steps (configuravel). Loop adaptativo. Circuit breaker (3 failures / 30s recovery). |
| D2 Tool Design | 5 | 40+ tools curadas de 6 dominios. FC nativo. Restricted tools (delete, bulk_delete). |
| D3 Inteligencia | 4 | Cross-domain reasoning. Resolve quando nenhum agente especializado consegue. |
| D4 Self-Correction | 4 | Circuit breaker. Timeout 60s. PII masking. Retry com backoff. |
| D5 Context Engineering | 3 | Sem prompt YAML dedicado. Inline. |
| D6 Compliance | 4 | Herda toda compliance da base. PII masking. FairnessGuard. |
| D7 Extensibilidade | 5 | Cross-domain by design. Adicionar novo dominio = registrar tools. |
| D8 Integracao Plataforma | 4 | LLM Factory, memory, audit, circuit breaker. |

**SCORE TOTAL: 34/40** — PRONTO

---

### 13. CustomAgentRuntime — Agent Studio

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 4 | LangGraph nativo. Max 8 steps (configuravel). |
| D2 Tool Design | 4 | 14 platform tools. Restricted tools (delete operations). Context level (full/standard/minimal). |
| D3 Inteligencia | 3 | System prompt definido pelo usuario. Intelligence depende da config. |
| D4 Self-Correction | 3 | Herda da base. Restricted tools. |
| D5 Context Engineering | 3 | Context level configuravel. System prompt user-defined. |
| D6 Compliance | 4 | Herda toda compliance. Restricted tools. |
| D7 Extensibilidade | 5 | E o PROPRIO mecanismo de extensibilidade. Novo dominio = novo custom agent. |
| D8 Integracao Plataforma | 4 | LLM Factory, memory, audit, model override, temperature config. |

**SCORE TOTAL: 30/40** — REFINAR

---

### 14. WSIInterviewGraph — Entrevista WSI

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | State machine (NAO ReAct). Deterministico. 10 stages explicitos. Correto para o caso de uso. |
| D2 Tool Design | 2 | Sem tools externas. Logic embedded nos nodes. Scoring inline. |
| D3 Inteligencia | 5 | WSI methodology completa. Bloom (6 niveis) + Dreyfus (5 niveis) + OCEAN (Big Five). 7 blocos. Evasion detection. Follow-up adaptativo. |
| D4 Self-Correction | 3 | Evasion detection. Validation node. Error stage. |
| D5 Context Engineering | 4 | Job requirements + candidate profile carregados no LOAD_CONTEXT. Question blocks tipados. |
| D6 Compliance | 4 | Audit trail por pergunta. Compliance BCB 498/SOX. |
| D7 Extensibilidade | 2 | Fortemente acoplado a WSI methodology. Bloom/Dreyfus/OCEAN sao recruiting-specific. Reescrever para outro dominio. |
| D8 Integracao Plataforma | 3 | Session store (Redis). Sem LLM Factory (usa LLM direto). |

**SCORE TOTAL: 26/40** — REFINAR

---

### 15. InterviewGraph — Agendamento de Entrevistas

| Dimensao | Score | Evidencia |
|----------|-------|-----------|
| D1 ReAct Loop | 3 | State machine. 6 nodes. Field collection loop. Max 8 iterations. |
| D2 Tool Design | 3 | Calendar service integration. DB record creation. Teams. Sem tool registry formal. |
| D3 Inteligencia | 3 | LLM extrai campos da conversa. Router decide: coletar mais ou agendar. |
| D4 Self-Correction | 3 | Validator node antes de execution. Loop de coleta. |
| D5 Context Engineering | 3 | State with conversation history. Workflow data. |
| D6 Compliance | 3 | Checkpointed. Audit. BCB 498/SOX. |
| D7 Extensibilidade | 4 | Field collection + validation + execution pattern e generico. Poderia virar "MeetingScheduler" ou "OnboardingScheduler". |
| D8 Integracao Plataforma | 3 | Calendar API (Graph). DB. |

**SCORE TOTAL: 25/40** — REFINAR

---

## RANKING (melhor → pior)

| Rank | Agente | Score | Status |
|------|--------|-------|--------|
| 1 | PipelineTransitionAgent | 35/40 | PRONTO |
| 2 | SourcingReActAgent | 34/40 | PRONTO |
| 3 | AutonomousReActAgent | 34/40 | PRONTO |
| 4 | WizardReActAgent | 33/40 | PRONTO |
| 5 | PolicyReActAgent | 33/40 | PRONTO |
| 6 | CommunicationReActAgent | 31/40 | REFINAR |
| 7 | KanbanReActAgent | 31/40 | REFINAR |
| 8 | PipelineReActAgent (CV) | 31/40 | REFINAR |
| 9 | CustomAgentRuntime | 30/40 | REFINAR |
| 10 | CompanySettingsReActAgent | 28/40 | REFINAR |
| 11 | AnalyticsReActAgent | 27/40 | REFINAR |
| 12 | AutomationReActAgent | 27/40 | REFINAR |
| 13 | WSIInterviewGraph | 26/40 | REFINAR |
| 14 | InterviewGraph | 25/40 | REFINAR |
| 15 | ATSIntegrationReActAgent | 22/40 | REFATORAR |

**Media:** 29.8/40 (75%) — acima de "REFINAR", tendendo a "BOM"

---

## MATRIX DE DIMENSOES — GAPS GLOBAIS

| Dimensao | Media | Min | Max | Gap Global |
|----------|-------|-----|-----|------------|
| D1 ReAct Loop | 3.6 | 3 | 5 | Medio |
| D2 Tool Design | 3.7 | 2 | 5 | **Alto (WSI, Interview, ATS)** |
| D3 Inteligencia | 3.5 | 2 | 5 | **Mais alto** |
| D4 Self-Correction | 3.1 | 2 | 4 | **Gap principal** |
| D5 Context Engineering | 3.3 | 2 | 4 | Medio |
| D6 Compliance | 4.1 | 3 | 5 | Baixo (forte) |
| D7 Extensibilidade | 4.0 | 2 | 5 | Baixo mas desigual |
| D8 Integracao | 3.6 | 3 | 5 | Medio |

**Dimensao mais forte:** D6 Compliance (4.1) — compliance e o diferencial da plataforma.
**Dimensao mais fraca:** D4 Self-Correction (3.1) — agentes nao detectam inconsistencias nem fazem re-planning.

---

## PLANO DE CERTIFICACAO P36

### Prioridade 1 — Nao precisa de P36 (score >= 33)
- PipelineTransitionAgent (35)
- SourcingReActAgent (34)
- AutonomousReActAgent (34)
- WizardReActAgent (33)
- PolicyReActAgent (33)

### Prioridade 2 — P36 leve (score 28-32)
- CommunicationReActAgent (31) — melhorar proatividade e context
- KanbanReActAgent (31) — melhorar self-correction
- PipelineReActAgent/CV (31) — desacoplar scoring de WSI
- CustomAgentRuntime (30) — melhorar context engineering
- CompanySettingsReActAgent (28) — melhorar intelligence

### Prioridade 3 — P36 completo (score 25-27)
- AnalyticsReActAgent (27) — precisa de mais tools e self-correction
- AutomationReActAgent (27) — precisa de mais intelligence
- WSIInterviewGraph (26) — precisa de tool registry formal
- InterviewGraph (25) — precisa de tool design formal

### Prioridade 4 — P36 pesado (score < 25)
- ATSIntegrationReActAgent (22) — precisa de redesign significativo

---

## EXTENSIBILIDADE ASSESSMENT — Pronta para novos dominios de RH?

### Resposta: SIM, com ressalvas.

**O que JA esta pronto para extensao:**
1. `LangGraphReActBase` + `EnhancedAgentMixin` — base solida que funciona para QUALQUER dominio
2. `compliance_block.yaml` com 3 variantes — extensivel para novas categorias
3. `guardrails_block.yaml` — universal (identity, hallucination, security)
4. `protected_attributes.yaml` — 14 atributos com base legal
5. `CustomAgentRuntime` — mecanismo de extensibilidade ja existe (Agent Studio)
6. Tool registry pattern — ToolDefinition dataclass e reutilizavel
7. Stage-based tool filtering — pattern reutilizavel para qualquer wizard/pipeline
8. Celery tasks — scheduling, beat, DLQ ja funcionam
9. Audit/compliance pipeline — funciona para qualquer dominio
10. `SystemPromptBuilder` com `recruiter_context` + `tenant_context` — generico

**O que FALTA para extensao limpa:**
1. **Domain YAML como SSOT** — prompts estao em YAML, mas tools e fluxo estao em Python. Ideal: novo dominio = 1 YAML (prompt + tools + flow config) + 0 Python.
2. **Tool wrappers acoplados a models** — `_wrap_search_candidates()` referencia `Candidate` model diretamente. Para novo dominio (ex: Employee), precisaria de novos wrappers.
3. **WSI methodology hardcoded** — Bloom/Dreyfus/OCEAN sao recruiting-specific. Para Performance Management, precisaria de taxonomias diferentes.
4. **Nomes de agentes hardcoded** — `@register_agent("sourcing")` e string literal. Deveria vir de config.
5. **Sem "Domain Template" pattern** — nao existe um template que gera um novo dominio a partir de config. Cada dominio e criado manualmente.

### Score de extensibilidade: 7/10
A plataforma pode expandir para novos dominios com ESFORCO MODERADO (novo prompt YAML + novos tool wrappers + novo domain.py). NAO precisa reescrever infraestrutura. Os padroes (ReAct, compliance, audit, memory, learning) sao 100% reutilizaveis.

---

## ARQUITETURA REPORT — Consistencia

### Padroes consistentes (todos os agentes):
- Heranca: `LangGraphReActBase + EnhancedAgentMixin`
- Registro: `@register_agent("domain_name")`
- Tools: `ToolDefinition` dataclass + `get_{domain}_tools()` function
- Prompts: YAML em `app/prompts/domains/` + Python system_prompt.py
- Compliance: `compliance_block.yaml` auto-injetado via `ComplianceDomainPrompt`
- Confidence: base 0.75, +0.07 se actions, -0.35 se error

### Outliers:
| Agente | Diferenca |
|--------|-----------|
| WSIInterviewGraph | StateGraph custom, sem tools registry, scoring inline |
| InterviewGraph | StateGraph custom, tools embedded, sem YAML prompt |
| PolicySetupAgent (legacy) | LLM direto, sem ReAct, sem heranca |
| AutonomousReActAgent | Max 10 steps (vs 5 padrao), circuit breaker unico |
| CustomAgentRuntime | Aceita config em runtime (nao pre-compilado) |

### Recomendacao:
Os StateGraphs (WSI, Interview) sao deliberadamente diferentes — state machines deterministicas sao corretas para workflows auditaveis. NAO devem ser migrados para ReAct. Mas devem ganhar tool registries formais para consistencia.

---

*Auditoria gerada em 2026-04-14. Base: 38 protocolos de auditoria + 58/90 items do MIGRATION_PLAN executados.*
