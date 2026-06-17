# WeDOTalent Data Flows — End-to-End Architecture
**Versão:** 2026-06-17
**Objetivo:** Mapear os 10 fluxos principais de dados da plataforma, do input do recrutador até o output final. Cada fluxo inclui diagrama ASCII, componentes envolvidos, pontos de falha e como monitorar.

---

## FLOW-01: Chat SSE — Recrutador → LIA → Resposta

### Descrição
Fluxo principal de comunicação síncrona entre o recrutador e a LIA via Server-Sent Events.

### Diagrama
```
Recrutador (browser)
    │ POST /api/v1/agent-chat/sse
    │ {message, session_id, company_id[JWT]}
    ▼
FastAPI: agent_chat_sse.py
    │ 1. auth: require_company_id (JWT) → _current_company_id ContextVar
    │ 2. FairnessGuard.check(message) → HTTP 400 se bloqueado
    │ 3. TokenBudgetService.check_budget(company_id) → budget_exhausted se excedido
    │ 4. LIA_FEDERATED_PRIMARY=true → RecruiterCopilotReActAgent
    │    LIA_FEDERATED_PRIMARY=false → MainOrchestrator → CascadedRouter
    ▼
RecruiterCopilotReActAgent (ou domain agent via CascadedRouter)
    │ 5. build_system_prompt() → lia_persona.yaml + company_context
    │    lia_agent_context_builder.build_company_agent_context()
    │    → LiaFieldConfigService.get_filtered_context(company_id)
    │    → filtra lia_field_toggles ON, append lia_instructions
    │ 6. LangGraph ReAct loop:
    │    a. LLM call (Anthropic claude-3-5-sonnet) → tool_calls or content
    │    b. StreamingCallback.on_tool_start() → SSE: tool_started
    │    c. Tool execution → SSE: tool_result
    │    d. StreamingCallback.on_llm_new_token() → SSE: token
    │    e. response_blocks drain → SSE: response_block (RRP cards)
    │ 7. HITL_GATE=on: hitl_preflight() → SSE: approval_required (se gate)
    ▼
SSE Stream (EventSource no browser)
    │ frames: token | tool_started | tool_result | response_block |
    │         reasoning_step | approval_required | budget_exhausted | error
    ▼
FE: useChatSocket (SSE consumer)
    │ case "token" → append to message buffer
    │ case "response_block" → render RRP card
    │ case "approval_required" → render HITL approval UI
    │ case "error" → surfaceError (never discard)
    ▼
Recrutador vê resposta
```

### Componentes Chave
| Componente | Arquivo | Responsabilidade |
|---|---|---|
| SSE endpoint | `app/api/v1/agent_chat_sse.py` | Entry point, auth, FairnessGuard, budget |
| Budget gate | `app/domains/token_budget/services/token_budget_service.py` | Redis key `token_budget:{company_id}:{date}` |
| Context builder | `app/shared/services/lia_agent_context_builder.py` | Monta contexto da empresa para o prompt |
| RecruiterCopilot | `app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py` | Agente federado principal |
| StreamingCallback | `app/shared/streaming/streaming_callback.py` | Tee tokens → SSE sink via ContextVar |
| MainOrchestrator | `app/orchestrators/main_orchestrator.py` | 5-phase pipeline (fallback path) |

### Pontos de Falha
- **Budget esgotado:** `TokenBudgetService` retorna `False` → SSE emite `budget_exhausted` → FE mostra aviso
- **LLM timeout:** LangGraph graph timeout → `HTTPException(504)` → FE `case "error"` surfaça
- **Tool error:** Exception em tool → `tool_handler` retorna `_TENANT_REQUIRED_RESPONSE` ou erro estruturado → nunca silencioso
- **FairnessGuard:** HTTP 400 antes do LLM — FE deve tratar 400 com `educational_message`

### Como Monitorar
```bash
# Logs SSE por session
ssh replit-wedo-0405 "grep 'session_id=<ID>' /home/runner/workspace/lia-agent-system/logs/app.log"
# Budget Redis
ssh replit-wedo-0405 "redis-cli GET token_budget:<company_id>:$(date +%Y-%m-%d)"
```

---

## FLOW-02: Criação de Vaga — Wizard Orchestrator

### Descrição
Fluxo de criação de vaga quando `LIA_WIZARD_ORCHESTRATOR=1` (caminho ativo em DEV).

### Diagrama
```
Recrutador (chat)
    │ "Criar vaga de Engenheiro de Software Senior"
    ▼
WizardOrchestrator (app/orchestrators/wizard_orchestrator.py)
    │ 18 tools: intake_job_info, suggest_salary, generate_jd, etc.
    │ Flag: LIA_WIZARD_ORCHESTRATOR=1
    ▼
FASE 1: Intake
    │ tool: intake_job_info
    │ → IntakeNode._derive_intake_suggestions()
    │   - Derive manager name from email prefix (signal real)
    │   - Derive seniority from job title pattern
    │   - NÃO inventar sem sinal → provenance declarada
    │ → JobVacancy criada com status="rascunho"
    │ → SSE: reasoning_step "Coletando informações básicas..."
    ▼
FASE 2: Enriquecimento JD
    │ tool: generate_jd
    │ → JdGenerationService.generate(vacancy_id, company_id)
    │   - FairnessGuard.check(jd_text) — bloqueia requisitos discriminatórios
    │   - LLM prompt com company context + lia_field_toggles
    │   - Grava em JobVacancy.job_description
    │ → SSE: tool_result com preview JD
    ▼
FASE 3: Faixa Salarial
    │ tool: suggest_salary
    │ → SalaryBenchmarkService.get_benchmark(title, level, dept, company_id)
    │   - match_from_bands(): procura em CompanySalaryBand (herança empresa)
    │   - Se não encontrar: chama MarketBenchmarkService
    │     - SERP_API_KEY presente → busca real → sources reais
    │     - SERP_API_KEY ausente → LLM estimate → source="estimativa_sem_busca"
    │     - NUNCA citar Glassdoor/etc para número inventado
    │ → salary_provenance: "company_salary_band" | "market_estimate" | "estimativa_sem_busca"
    ▼
FASE 4: WSI Config
    │ tool: configure_wsi
    │ → WSIService.generate_questions(vacancy_id, company_id)
    │   - Bloco de competências por função
    │   - 3-5 perguntas por bloco (Dreyfus scale)
    │   - FairnessGuard em cada pergunta
    ▼
FASE 5: Elegibilidade
    │ tool: set_eligibility_questions
    │ → EligibilityVerificationService salva em JobVacancy.eligibility_questions JSONB
    │ → Shape canônico: EligibilityQuestionItem
    │   {id, question, question_type, options, is_eliminatory, expected_answer, category, order}
    ▼
FASE 6: Aprovação / Publicação
    │ tool: submit_for_approval | publish_job
    │ → HiringPolicy.manager_approval_for_offer?
    │   - Se True: status="aguardando_aprovacao" + notifica gestor
    │   - Se False: status="publicada"
    │ → JobVacancy.status atualizado
    │ → Tombstone nodes (publish.py, review.py, calibration.py) NUNCA chamados
    │   (RAILS_API_URL ausente → RuntimeError se invocados)
```

### Estado Persisted por Fase
| Fase | Tabela | Campo | 
|---|---|---|
| Intake | job_vacancies | title, department, level, status='rascunho' |
| JD | job_vacancies | job_description |
| Salary | job_vacancies | salary_min, salary_max, salary_provenance |
| WSI | wsi_question_sets | blocks, questions |
| Elegibilidade | job_vacancies | eligibility_questions (JSONB) |
| Publicação | job_vacancies | status='publicada'/'ao_vivo' |

---

## FLOW-03: Triagem WSI — Candidato → Score

### Descrição
Fluxo completo de triagem de candidatos via WSI (Work Style Interview).

### Diagrama
```
Candidato (portal ou WhatsApp)
    │ Acessa link de triagem (token único)
    ▼
TriagemSessionService.start_session()
    │ 1. ConsentCheckerService.check_candidate_consent(purpose="ai_screening")
    │    → HTTP 403 se sem consentimento LGPD
    │ 2. EligibilityVerificationService.get_eligibility_questions_from_job(vacancy_id)
    │    → parse EligibilityQuestionItem (normaliza 4 shapes legados)
    │    → filtra is_eliminatory=True
    ▼
FASE ELEGIBILIDADE (se existir)
    │ Pergunta eliminatória → candidato responde
    │ expected_answer != resposta?
    │   → is_eliminatory=True: marca candidato como ELIMINADO
    │     + ReconsiderationService.offer_reconsideration(category)
    │       - category ∈ {work_model, location, availability, legal, default}
    │       - LGPD Art. 20: candidato pode contestar decisão automatizada
    │   → is_eliminatory=False: continua
    │ Mensagens de elegibilidade levam wsi_block=999 (sentinela)
    ▼
FASE WSI
    │ WSIService.get_questions_for_session(vacancy_id, block_idx)
    │   → WsiRepository.get_question_set(vacancy_id)
    │   → Seleciona próximo bloco não-completo
    │   → Entrega perguntas (streaming SSE ou WhatsApp)
    │ Candidato responde (texto ou voz via WSIVoicePlugin)
    │ WSIService.process_response(session_id, block, answer, company_id)
    │   → WsiAnswerRepository.save(answer)
    ▼
SCORING (após bloco completo)
    │ WSIScoreService.score_block(answers, questions, vacancy_context)
    │   → LLM prompt com BigFive blend weights (se available)
    │     BigFiveDepartmentService.get_blend_weights(company_id, department)
    │     → MIN_DEPT_SAMPLES=10 gate (ADR-LGPD-001)
    │     → Se < 10 amostras: usa weights padrão
    │   → score por competência (0.0-1.0)
    │   → wsi_effectiveness_score calculado
    ▼
LEARNING LOOP (após candidato contratado)
    │ TransitionDispatchService._hook_conclusion_hired()
    │   → WsiEffectivenessRepository.record_outcome(candidate_id, scores, hired=True)
    │   → BigFiveDepartmentService.update_profile(company_id, department, bigfive_scores)
    │     → Welford running average (sem armazenar scores individuais)
    │     → Decay factor 0.95 (recent hires mais relevantes)
    │     → sample_count++ (gate MIN_DEPT_SAMPLES para próximas vagas)
    ▼
Output
    │ CandidateScore.wsi_score
    │ CandidateScore.competency_breakdown {}
    │ Kanban column determinado por score threshold
```

### Pontos Críticos
- **Consentimento LGPD:** gate fail-closed em `start_session` — não confiar no checkbox FE
- **wsi_block=999:** sentinela que exclui respostas de elegibilidade do scoring WSI
- **MIN_DEPT_SAMPLES=10:** ADR-LGPD-001 — agregado só usado se anonimização válida
- **Voz:** CONSENT_QUESTION hardcoded ("WeDOTalent") — nunca parametrizar com ai_name

---

## FLOW-04: Elegibilidade — Parse e Gate

### Descrição
Fluxo de perguntas eliminatórias desde a configuração na vaga até a avaliação do candidato.

### Diagrama
```
Configuração (recrutador)
    │ WizardOrchestrator ou JobSetupModal
    │ Salva em JobVacancy.eligibility_questions JSONB
    │ Shapes aceitos (4 legados normalizados pelo EligibilityQuestionItem):
    │   Shape wizard: {required_answer: "yes"}
    │   Shape edição: {disqualify_on_fail, expected_answer}
    │   Shape catálogo: {eliminatory, eliminatoryAnswer}
    │   Shape extractor: {question_text, is_eliminatory}
    ▼
EligibilityVerificationService.get_eligibility_questions_from_job(vacancy_id)
    │ ÚNICO ponto de parse (produtor canônico)
    │ → EligibilityQuestionItem.model_validate() com model_validator(mode='before')
    │   normaliza → {id, question, question_type, options, is_eliminatory,
    │                expected_answer, category, order}
    ▼
TriagemSessionService (web) OU ConversationManager (WhatsApp)
    │ Ambos consomem o MESMO produtor
    │ Elegibilidade ANTES do WSI
    ▼
Avaliação da resposta
    │ resposta.lower() == expected_answer.lower()?
    │   NÃO + is_eliminatory=True → ELIMINADO
    │     │ FairnessGuard.check(reason) antes de gravar motivo
    │     │ ReconsiderationService.offer_reconsideration(category)
    │     │   → mensagem educativa com CLT Art. 373-A / LGPD Art. 20
    │   SIM ou is_eliminatory=False → CONTINUA
    ▼
Sensores
    │ tests/contract/test_eligibility_producer_contract.py (13 testes)
    │ tests/unit/test_eligibility_phase.py (7 testes)
```

---

## FLOW-05: BigFive Learning Loop

### Descrição
Como os scores BigFive de candidatos contratados atualizam os pesos de blend do departamento.

### Diagrama
```
Evento: Candidato marcado como Contratado
    │ VacancyCandidateRepository.update_status(candidate_id, "hired")
    ▼
TransitionDispatchService._hook_conclusion_hired()
    │ Trigger: status transition → "hired"
    │
    │ ─── BRANCH A: WSI Effectiveness ───
    │ WsiEffectivenessRepository.record_outcome(
    │   candidate_id, vacancy_id, wsi_scores, hired=True, company_id
    │ )
    │ → Grava em wsi_effectiveness (tabela)
    │
    │ ─── BRANCH B: BigFive Department Profile ───
    │ BigFiveDepartmentService.update_profile(
    │   company_id, department, bigfive_scores
    │ )
    │   ├── Busca perfil existente: BigFiveDepartmentProfileRepository.get(company_id, dept)
    │   │   Se não existe: cria com sample_count=0
    │   ├── Welford running average (sem armazenar scores individuais)
    │   │   new_mean = old_mean + (score - old_mean) / n
    │   │   new_M2  = old_M2  + (score - old_mean) * (score - new_mean)
    │   ├── Decay factor: blended = (old * 0.95) + (new * 0.05) para dados antigos
    │   └── sample_count++
    ▼
Gate de Leitura (ADR-LGPD-001)
    │ BigFiveDepartmentService.get_blend_weights(company_id, department)
    │   if profile.sample_count < MIN_DEPT_SAMPLES (10):
    │     return DEFAULT_WEIGHTS  # anonimização não válida
    │   else:
    │     return profile.blend_weights  # Art. 12 §1 ANPD - anonimização válida
    ▼
Uso: WSIScoreService
    │ LLM prompt inclui blend_weights para ponderar competências
    │ Empresas com mais contratações têm scoring mais personalizado
```

### Invariantes de Compliance
- **MIN_DEPT_SAMPLES=10:** gate em `bigfive_service.py:42` — sem isso o perfil não é usado
- **Erasure:** deletar candidato individual NÃO requer recompute do agregado (Art. 12 §1)
- **Sem PII:** apenas scores numéricos agregados são armazenados, nunca nome/CPF/email

---

## FLOW-06: Salary Benchmark — Herança e Fallback

### Descrição
Como a faixa salarial de uma vaga é determinada, com cadeia de fallback.

### Diagrama
```
JobVacancy sendo criada/editada
    │ salary_min, salary_max não preenchidos pelo recrutador
    ▼
CAMADA 1: Company Salary Bands (herança)
    │ SalaryBandService.match_from_bands(
    │   company_id, level, department, employment_type
    │ )
    │ → CompanySalaryBandRepository.get_bands(company_id)
    │ → match: level == band.level AND department ∈ band.departments
    │ → Se match: salary_provenance = "company_salary_band"
    │             inherited = True (read-time, sem commit)
    │             source = "Faixa herdada de Configurações"
    ▼ (se não encontrado)
CAMADA 2: Market Benchmark (SERP)
    │ MarketBenchmarkService.get_benchmark(title, level, location)
    │   ─── SE SERP_API_KEY presente ───
    │   → SerpApiClient.search("salário {title} {level} {location}")
    │   → Parse resultados → extrai faixa salarial
    │   → sources_found = ["glassdoor.com.br", "linkedin.com"] (REAIS)
    │   → salary_provenance = "market_search"
    │   → confidence = "high"
    │
    │   ─── SE SERP_API_KEY ausente ───
    │   → LLM estimate (conhecimento paramétrico)
    │   → sources_found = []  # NUNCA citar sites para número inventado
    │   → salary_provenance = "estimativa_sem_busca"
    │   → confidence = "low"
    │   → unverified = True
    │   → UI deve mostrar "Estimativa não verificada"
    ▼
Output para o recrutador
    │ {
    │   salary_min, salary_max,
    │   salary_provenance: "company_salary_band" | "market_search" | "estimativa_sem_busca",
    │   inherited: true/false,
    │   source_label: "Faixa herdada de Configurações" | "Pesquisa de mercado" | "Estimativa",
    │   unverified: false/false/true
    │ }
    │
    │ FE: useSalaryBenchmark → mostra badge "Herdado" ou "Estimativa (não verificada)"
```

### Regra de Proveniência Honesta
- Glassdoor/Robert Half/LinkedIn só aparecem como source se houve busca REAL
- LLM estimate → sempre `unverified=True` + label explícito
- Sensor: `tests/contract/test_salary_benchmark_provenance.py`

---

## FLOW-07: AI Persona Resolution — Chat System Prompt

### Descrição
Como o nome e tom da LIA são determinados para cada tenant no system prompt.

### Diagrama
```
Recrutador faz login → company_id via JWT
    ▼
build_system_prompt(company_id) chamado por qualquer agente
    ▼
LAYER 1: Base Persona (default)
    │ SystemPromptBuilder._load_persona_base()
    │ → app/prompts/shared/lia_persona.yaml
    │   - Nome padrão: "LIA"
    │   - Persona base + ethics blocks (LGPD/fairness/anti-bias)
    │   - Imutável pelo cliente
    │   - Cached (LRU, boot-time)
    ▼
LAYER 2: Tenant Override (admin WeDOTalent only)
    │ TenantPromptOverrideRepository.get(company_id, "shared/lia_persona")
    │ → Se existe: substitui Layer 1 INTEIRAMENTE
    │ → Validator: TenantPersonaValidator
    │   - YAML syntax válida
    │   - ETHICS_INVARIANTS imutáveis (LGPD/fairness blocks não podem ser removidos)
    │   - PII scan (warning)
    │ → Apenas wedotalent_admin pode criar/editar
    ▼
LAYER 3: Per-Tenant AI Persona (cliente)
    │ CompanyHiringPolicyRepository.get_ai_persona(company_id)
    │ → communication_rules.ai_persona = {name, tone}
    │   name: validado por ai_persona_validator (2-20 chars, blocklist marcas IA)
    │   tone: enum {amigavel, formal, profissional, direto, empático, motivador}
    │
    │ SystemPromptBuilder._append_ai_persona_override(base_prompt, ai_persona)
    │   → APPENDA sections ao final (nunca muta base):
    │     "## Override de Persona\nVocê se chama {name}."
    │     "## Tom Customizado\n{TONE_INSTRUCTIONS[tone]}"
    ▼
System Prompt Final
    │ = Layer1/2 + Layer3 append
    │   "Você é {name}, a IA da {company_name}. Seu tom é {tone}."
    ▼
Nota: "lia_tone" em HiringPolicy.communication_rules NÃO afeta o system prompt
    │ Esse campo controla APENAS wording de emails/WhatsApp outbound
    │ São 3 surfaces independentes — ver ADR-LGPD-002
```

### Arquivos
- `app/shared/prompts/system_prompt_builder.py` — `_append_ai_persona_override`
- `app/domains/persona/services/ai_persona_validator.py` — validação nome+tom
- `app/domains/persona/services/ai_persona_service.py` — read/update + audit

---

## FLOW-08: Talent Search (Funil de Talentos)

### Descrição
Fluxo de busca de candidatos no Funil, com múltiplos modos de query.

### Diagrama
```
Recrutador (Funil de Talentos)
    │ Input: query em linguagem natural | JD text | Boolean | Arquétipos
    ▼
POST /api/v1/candidates/search
    │ 1. FairnessGuard.check(query_text) → HTTP 400 se discriminatório
    │    → FE: banner âmbar + bolha LIA educativa
    │ 2. company_id do JWT (NUNCA do payload)
    ▼
CandidateSearchService.search(query, mode, company_id)
    │ MODE: natural_language
    │   → LLM parse: extrai skills, seniority, location, etc.
    │   → NL2Filter: converte para FilterSpec
    │
    │ MODE: similar_to_jd
    │   → JdEmbeddingService.embed(jd_text) → pgvector 768-dim
    │   → CandidateRepository.search_by_embedding(embedding, company_id, threshold=0.7)
    │   ⚠️ JD usa 768-dim, mas profiles usam 1536-dim → mismatch atual (F-06 Partial)
    │
    │ MODE: boolean
    │   → BooleanQueryParser.parse(query)
    │   → SQL WHERE clause com AND/OR/NOT
    │
    │ MODE: archetypes
    │   → ArchetypeRepository.get(archetype_id, company_id)
    │   → FairnessGuard.check(archetype.description) — checa p/ discriminação
    │   → expande para FilterSpec
    ▼
CandidateRepository.search(filter_spec, company_id, pagination)
    │ _require_company_id() — multi-tenancy fail-closed
    │ → Monta query SQL com filtros
    │ → Aplica pii_field_visibility (por papel do recrutador logado)
    │   → campos sensíveis mascarados se recrutador não tem permissão
    │ → Retorna candidatos com score básico
    ▼
IA Score (assíncrono, opcional)
    │ POST /api/v1/candidates/{id}/ai-score?vacancy_id=...
    │ → AIScoreService.compute(candidate_id, vacancy_id, company_id)
    │   → WSI scores + BigFive blend weights
    │   → score ∈ [0, 1]
    ▼
Output
    │ {
    │   candidates: [...],
    │   total: N,
    │   query_breadcrumb: [{label, color, type}],
    │   suggestions: {synonyms: [...], related_skills: [...]}
    │ }
```

### PII no Funil
- `mask_pii_outbound()`: passthrough por padrão (recrutador autenticado VÊ dados)
- `resolve_pii_field_visibility(user_id, field)`: por-campo por-papel
- CPF/email: resolve-then-strip para LLM (ADR-LGPD-002 Layer 2)

---

## FLOW-09: Offer Concierge — Proposta com HITL

### Descrição
Fluxo de geração e envio de proposta de emprego, com gate de aprovação condicional.

### Diagrama
```
Recrutador (chat ou kanban)
    │ "Enviar proposta para Maria Silva — R$ 8.000"
    ▼
OfferDomain tool: generate_offer
    │ 1. HITL gate (LIA_HITL_GATE=on): hitl_preflight("generate_offer")
    │    → approval_required emitido via SSE (se gate ativo)
    │    → Recrutador confirma → replay turno
    │ 2. OfferService.generate_offer(candidate_id, vacancy_id, salary, company_id)
    │   → Busca template de proposta (CompanyHiringPolicy.offer_template)
    │   → LLM: personaliza proposta com nome/cargo/salário/benefícios
    │   → FairnessGuard.check(offer_text) — bloqueia discriminação
    │   → Salva em Offer table com status="rascunho"
    ▼
Gate de Aprovação (HiringPolicy)
    │ OfferService.check_can_send(offer_id, company_id)
    │   → HiringPolicyRepository.get(company_id).manager_approval_for_offer
    │   → True: raise OfferRequiresApprovalError
    │     → status="aguardando_aprovacao"
    │     → NotificationService.notify_manager(manager_id, offer_id)
    │     → API retorna {requires_approval: True, ui_action: "show_approval_panel"}
    │   → False: prossegue para envio
    ▼
OfferService.mark_sent(offer_id, company_id)
    │ Defense-in-depth: verifica novamente se aprovação é necessária
    │ → CommunicationDispatcher.send_offer(offer_id, channel)
    │   → Email ou WhatsApp
    │ → AuditService.log_decision(action='offer_sent', offer_id, company_id)
    ▼
Candidato recebe proposta
    │ Portal do candidato: aceitar/recusar
    │ → TransitionDispatchService._hook_offer_accepted()
    │   → CandidateStatus → "hired"
    │   → Trigger: FLOW-05 BigFive Learning Loop
```

### Sensor
- `tests/contract/test_offer_approval_gate.py` — 5 testes pinando o gate

---

## FLOW-10: Hired Trigger Chain — Aprendizado Pós-Contratação

### Descrição
Cadeia de eventos disparada quando um candidato é marcado como contratado.

### Diagrama
```
Evento: VacancyCandidate.status → "hired"
    │ VacancyCandidateRepository.update_status(candidate_id, vacancy_id, "hired")
    ▼
TransitionDispatchService.dispatch(transition="conclusion_hired", ...)
    │ Registra no AuditLog
    ▼
Hook Chain (ordem garantida)
    │
    ├── _hook_conclusion_hired()
    │   ├── WSI Effectiveness: WsiEffectivenessRepository.record_outcome()
    │   ├── BigFive Profile: BigFiveDepartmentService.update_profile()
    │   └── JD Similar: JdSimilarService.add_to_corpus(vacancy_id)
    │       → Embeds JD (768-dim via text-embedding-3-small)
    │       → Adiciona ao índice pgvector
    │       → Próximas criações de vaga similares usam como referência
    │
    ├── _hook_notify_stakeholders()
    │   └── Notifica gestor + RH via email
    │
    └── _hook_lgpd_retention_clock()
        └── SetDataRetentionPolicy(candidate_id, hired=True)
            → Retenta dados por período conforme LGPD
            → Candidatos não-contratados: período menor

Efeitos Downstream (próximos processos seletivos)
    │ BigFive blend weights: vagas do mesmo dept usam perfil atualizado
    │ JD Similar: novas vagas similares recebem sugestões baseadas na JD que gerou contratação
    │ WSI Effectiveness: calibra threshold de aprovação por competência
```

### Importância para Reprodução
Ao adicionar novo hook de aprendizado:
1. Registrar em `TransitionDispatchService._HOOKS` dict
2. Implementar `_hook_<nome>()` com try/except que loga mas não falha a transição
3. Adicionar teste em `tests/unit/test_transition_hooks.py`
4. Documentar no FEATURE_CATALOG.md

---

*Documento gerado em 2026-06-17. Para atualizar, consulte os arquivos canônicos listados em cada seção.*
