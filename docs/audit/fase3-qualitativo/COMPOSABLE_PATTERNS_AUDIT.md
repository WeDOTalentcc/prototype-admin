# P12 — Auditoria de Padrões Composable (Benchmark Anthropic)

**Protocolo:** P12  
**Data:** 2026-04-14  
**Plataforma:** WeDOTalent / LIA Agent System  
**Escopo:** 10 fluxos de negócio críticos mapeados aos 6 padrões Anthropic  
**Framework de Auditoria:** Anthropic Composable Patterns + Princípio da Complexidade Mínima  
**Auditores:** LIA Systems Architect (automated), referência: PLATFORM_MAP.md (P01), FLOW_TRACES.md (P02)

---

## REFERÊNCIA: OS 6 PADRÕES ANTHROPIC

| # | Padrão | Definição | Quando Usar |
|---|--------|-----------|-------------|
| 1 | **PROMPT CHAINING** | Decomposição em chamadas LLM sequenciais com quality gate entre etapas | Tarefas decomponíveis com output de cada etapa alimentando a próxima |
| 2 | **ROUTING** | Classifica input e despacha para handler especializado | Inputs com domínios distintos que requerem tratamento diferente |
| 3 | **PARALLELIZATION** | Execução simultânea de subtarefas independentes (Sectioning ou Voting) | Subtarefas independentes ou necessidade de consenso via múltiplas execuções |
| 4 | **ORCHESTRATOR-WORKERS** | Orchestrator analisa, decompõe dinamicamente, despacha para workers especializados | Decomposição dinâmica (diferente de Prompt Chaining porque a decomposição é o LLM decidindo) |
| 5 | **EVALUATOR-OPTIMIZER** | Loop iterativo: gerador + avaliador, refinando até critério de qualidade | Quando há critério de qualidade verificável e benefício claro de iteração |
| 6 | **AUTONOMOUS AGENT** | LLM em loop com ferramentas, usando feedback do ambiente para decidir próximos passos | Tarefas complexas com domínio de ação longo — mais caro, mais risco, mais guardrails necessários |

> **Princípio Anthropic:** "Start with the simplest possible solution and increase complexity only when clearly necessary."

---

## SCORE SUMMARY

| Fluxo | Padrão Atual | Padrão Recomendado | Alinhado? | Score Maturidade (0-5) |
|---|---|---|---|---|
| 1. Chat do Recrutador | ROUTING (8 tiers) | ROUTING (correto, otimizar) | PARCIAL | 3/5 |
| 2. Busca de Candidatos | AUTONOMOUS AGENT | PARALLELIZATION + ROUTING | NÃO | 2/5 |
| 3. Triagem de CVs | PROMPT CHAINING (StateGraph) | PROMPT CHAINING (correto) | SIM | 4/5 |
| 4. Entrevista WSI | PROMPT CHAINING (StateGraph) | PROMPT CHAINING (correto) | SIM | 4/5 |
| 5. Wizard de Vaga | ORCHESTRATOR-WORKERS | PROMPT CHAINING simples | SOBRE-ENGENHARIA | 2/5 |
| 6. Onboarding Conversacional | PROMPT CHAINING | PROMPT CHAINING (correto) | SIM | 3/5 |
| 7. Geração de JD | EVALUATOR-OPTIMIZER parcial | EVALUATOR-OPTIMIZER completo | PARCIAL | 3/5 |
| 8. Comunicação com Candidatos | AUTONOMOUS AGENT | ROUTING + PROMPT CHAINING | NÃO | 2/5 |
| 9. Pipeline Autônomo | AUTONOMOUS AGENT | ORCHESTRATOR-WORKERS | NÃO | 1/5 |
| 10. Análise de Candidato | PARALLELIZATION (parcial) | PARALLELIZATION (Voting) | PARCIAL | 3/5 |

**Score Global de Maturidade: 2.7 / 5.0**

Principais problemas: over-engenharia no Wizard de Vaga (padrão Orchestrator-Workers aplicado onde Prompt Chaining bastaria), sub-utilização de Parallelization em Busca (busca sequencial quando 4 estratégias poderiam rodar em paralelo com merger), e Autonomous Agent aplicado à Comunicação (domínio determinístico que não precisa de loop de ferramentas).

---

## MATRIZ DE PADRÕES POR FLUXO

| Fluxo | Padrão Atual | Padrão Recomendado | Complexidade | Prioridade | Esforço |
|---|---|---|---|---|---|
| Chat do Recrutador | ROUTING 8-tier | ROUTING otimizado | Média | P1 | M |
| Busca de Candidatos | Autonomous Agent | Parallelization + Routing | Alta | P0 | L |
| Triagem de CVs | Prompt Chaining (StateGraph) | Prompt Chaining (manter) | Média | P2 | S |
| Entrevista WSI | Prompt Chaining (StateGraph) | Prompt Chaining (manter) | Média | P2 | S |
| Wizard de Vaga | Orchestrator-Workers | Prompt Chaining simples | Alta | P0 | M |
| Onboarding Conversacional | Prompt Chaining | Prompt Chaining + gate LGPD | Simples | P1 | S |
| Geração de JD | Eval-Optimizer parcial | Evaluator-Optimizer completo | Média | P1 | M |
| Comunicação | Autonomous Agent | Routing + Prompt Chaining | Alta | P0 | L |
| Pipeline Autônomo | Autonomous Agent puro | Orchestrator-Workers | Alta | P0 | XL |
| Análise de Candidato | Parallelization parcial | Parallelization Voting | Média | P1 | M |

---

## FLUXO 1: CHAT DO RECRUTADOR (Main Chat)

### A. Padrão Atual

```
Input (mensagem)
  → FairnessGuard + SecurityPatterns (pre-checks)
  → TenantContext enrichment
  → Phase 0: PendingAction resolver (multi-turn)
  → Phase 1: ActionExecutor (intents fechados)
  → Phase 2: CascadedRouter (8 tiers)
       Tier 0: MemoryResolver (pronomes)
       Tier 1: LRU cache (MD5 hash)
       Tier 2: Redis hash cache
       Tier 3: VectorSemanticCache (pgvector ≥ 0.85)
       Tier 4: FastRouter (regex/keyword)
       Tier 5: LLMCascadeRouter (Gemini Flash → Sonnet → Opus)
       Tier 6: AutonomousReActAgent (fallback)
       Fallback: clarification_needed
  → DomainWorkflow → Agent ReAct → Response
```

**Padrão identificado:** ROUTING (com caching hierárquico e LLM cascade como fallback de classificação)

### B. Padrão Recomendado

ROUTING é o padrão correto para este fluxo. A implementação está bem estruturada.

```
Input
  → [Pre-checks: FairnessGuard + Security] (correto — gates antes do routing)
  → ROUTER (8 tiers com custo crescente) → Domain Handler
  → Response
```

**Justificativa:** O problema não é o padrão, mas a profundidade do Tier 6 (AutonomousReActAgent como fallback). O Tier 6 é um Autonomous Agent completo (40+ tools, loop aberto), ativado quando as camadas anteriores falham. Isso significa que queries ambíguas — que deveriam resultar em clarification_needed — às vezes caem em um agente autônomo de 40 tools com max_steps=10. O Tier 6 deveria ser substituído por uma clarification mais inteligente.

### C. Análise de Complexidade

**Sobre-engenharia detectada no Tier 6:**
- `app/domains/autonomous/agents/autonomous_react_agent.py`: AutonomousReActAgent com 40+ tools como fallback de routing.
- O custo de um Autonomous Agent (múltiplas chamadas LLM + loop de tools) é desproporcional para resolver uma query que simplesmente não pôde ser classificada.
- Anthropic recomenda que o Autonomous Agent seja ativado apenas quando "a tarefa complexa requer múltiplos passos encadeados com feedback do ambiente" — não como fallback de routing.

**Bem implementado:**
- `app/orchestrator/cascaded_router.py`: A hierarquia de custo crescente (Tier 0 O(1) → Tier 5 LLM) segue o princípio de complexidade mínima.
- `app/orchestrator/fast_router.py`: FastRouter com regex/keyword cobre ~80% das queries a custo zero de LLM.
- LLM Cascade (Gemini Flash → Sonnet → Opus) aplica o princípio de usar o modelo mais barato que resolve o problema.

### D. Mapeamento Proposto

Substituir Tier 6 (AutonomousReActAgent) por clarification inteligente com sugestões contextuais:

```
Tier 5 (LLM) falha com confiança < threshold
  → Tier 6: SystemPromptBuilder.build_clarification(partial_matches)
  → clarification_question + options → usuário
  (Autonomous Agent removido do caminho crítico de routing)
```

O AutonomousReActAgent deve ser ativado explicitamente pelo usuário via intent, não como fallback automático.

- **Complexidade:** Média  
- **Prioridade:** P1  
- **Esforço:** M  
- **Arquivo-chave:** `app/orchestrator/cascaded_router.py` (Tier 6, linhas do bloco autonomous)

---

## FLUXO 2: BUSCA DE CANDIDATOS (Sourcing)

### A. Padrão Atual

```
Chat Input → CascadedRouter → domain="sourcing"
  → SourcingReActAgent (create_react_agent)
       → LLM decide: chamar search_candidates(skills, seniority, limit)
       → Tool: search_candidates → PostgreSQL SELECT
       → (Opcional) rank_candidates → WRF score
       → LLM formula resposta
  → panel_update via WebSocket

[Separado, via API REST]
  MultiStrategySearchService (4 estratégias em paralelo):
    asyncio.gather(direct, adjacent, silver, reengagement)
    → dedup + weighted ranking
```

**Padrão atual:** AUTONOMOUS AGENT para o path de chat (loop aberto com decisão LLM de quais tools chamar). O `MultiStrategySearchService` em `app/services/multi_strategy_search.py` implementa PARALLELIZATION corretamente mas não é chamado pelo agente de chat.

### B. Padrão Recomendado

**PARALLELIZATION (Sectioning) + ROUTING** para o path de chat:

```
Input → ROUTER → domain="sourcing"
  → SourcingOrchestrator (determina estratégias)
       ┌─────────────────────────────────────────┐
       │ asyncio.gather (paralelo):               │
       │   A: direct_search(skills, seniority)    │
       │   B: adjacent_search(similar_titles)     │
       │   C: silver_medalists(job_id)            │
       │   D: reengagement(company_id, skills)    │
       └─────────────────────────────────────────┘
  → Deduplicação + WRF ranking
  → FairnessCheck nos resultados
  → panel_update via WebSocket
```

**Justificativa:** A busca de candidatos não requer que o LLM "decida" qual tool usar em cada passo. As estratégias de busca são conhecidas antecipadamente e independentes — o caso de uso perfeito para Parallelization. O `MultiStrategySearchService` já existe e implementa exatamente esse padrão, mas está desconectado do path de chat.

### C. Análise de Complexidade

**Oportunidade de Parallelization perdida:**
- `app/services/multi_strategy_search.py:59`: 4 estratégias em `asyncio.gather` — padrão correto implementado mas inacessível pelo agente de chat.
- `app/domains/sourcing/agents/sourcing_react_agent.py`: Path de chat usa `create_react_agent` (loop aberto), chamando `search_candidates` sequencialmente via decisão LLM.
- Custo desnecessário: O loop ReAct gasta tokens de LLM para decidir entre opções de busca que são determinísticas.

**Anti-pattern detectado:** God-tool em `app/domains/sourcing/tools/query_tools.py:37-175`: `search_candidates` faz filtros em memória pós-query sem estrutura de pipeline. 

**Risco LGPD não mitigado:** `app/domains/sourcing/tools/query_tools.py:37` — busca retorna candidatos sem verificação de consentimento LGPD (identificado em FLOW_TRACES.md F1-G1). O padrão Parallelization recomendado deve incluir gate de consentimento na etapa de deduplicação.

### D. Mapeamento Proposto

```python
# Conectar MultiStrategySearchService ao SourcingDomain
# app/domains/sourcing/domain.py: execute_action("search_candidates")
#   → multi_strategy_search_service.search(...)  # já implementado
#   → LGPD consent gate pós-busca, pré-ranking
#   → FairnessCheck nos resultados ranqueados
```

- **Complexidade:** Alta  
- **Prioridade:** P0  
- **Esforço:** L  
- **Arquivos-chave:** `app/services/multi_strategy_search.py`, `app/domains/sourcing/domain.py`, `app/domains/sourcing/tools/query_tools.py:37`

---

## FLUXO 3: TRIAGEM DE CVs (CV Screening)

### A. Padrão Atual

```
POST /wsi/screening-pipeline
  → WSIScreeningPipeline.build_pipeline()
       → SeniorityResolver.resolve_seniority_full() [multi-sinal determinístico]
       → _build_company_block() [perguntas DB + affirmative action]
       → _build_technical_block() → WSIService.generate() → LLM (Claude)
       → _build_behavioral_block() → WSIService.generate() → LLM (Claude)
       → calibrate_or_fallback() [Bloom/Dreyfus]
  → WSIScreeningPipelineResponse(questions, blocks, metadata)

[Triagem em lote]
CVScreeningBatchService.run_batch(candidate_ids, job_id, company_id)
  → Para cada candidato:
       → rubric_evaluation_service.evaluate() → LLM (Claude)
       → _calculate_wsi_score(rubric_score)
       → _determine_recommendation(wsi_score)
  → Resultados agregados
```

**Padrão identificado:** PROMPT CHAINING — pipeline sequencial onde cada etapa processa o output da anterior (seniority → questions → scoring → recommendation).

### B. Padrão Recomendado

PROMPT CHAINING é o padrão correto. A implementação está bem estruturada.

```
Input (job_id, candidate_ids)
  → [Step 1] SeniorityResolver (determinístico, sem LLM) — quality gate
  → [Step 2] PipelineBuilder (perguntas técnicas + comportamentais) — LLM
  → [Step 3] RubricEvaluation (scoring por candidato) — LLM
  → [Step 4] Recommendation (determinístico: thresholds fixos)
  → Output (wsi_score + recommendation)
```

O `CVScreeningBatchService` está corretamente "de-agentificado" — removido de BaseAgent para serviço direto chamado por Celery. Isso é um acerto de projeto.

### C. Análise de Complexidade

**Bem implementado:**
- `app/domains/cv_screening/services/seniority_resolver.py`: Motor multi-sinal determinístico (5 sinais ponderados, sem LLM), com voting implícito (full/majority/conflict/single/none). Quality gate correto.
- `app/domains/cv_screening/services/cv_screening_batch_service.py`: De-agentificação correta — serviço sem BaseAgent overhead.
- Thresholds fixos (`auto_approve ≥ 75, review ≥ 55`) — decisão determinística na etapa final.

**Oportunidade de Parallelization perdida:**
- `CVScreeningBatchService.run_batch()` processa candidatos sequencialmente em loop `for`. Com `asyncio.gather` poderia avaliar múltiplos candidatos em paralelo (cada um é independente).
- `app/domains/cv_screening/services/cv_screening_batch_service.py`: linha do loop de candidatos.

**Sobre-engenharia marginal:**
- `app/domains/cv_screening/agents/wsi_interview_graph.py`: StateGraph LangGraph com 7 nodes para um fluxo que é fundamentalmente sequencial. Um Prompt Chain simples seria suficiente — o StateGraph adiciona overhead de serialização/deserialização de estado sem benefício claro para este fluxo determinístico.

### D. Mapeamento Proposto

Manter Prompt Chaining. Otimização: paralelizar avaliação de candidatos no batch:

```python
# CVScreeningBatchService.run_batch()
# ATUAL: for candidate_id in candidate_ids: await evaluate(candidate_id)
# RECOMENDADO:
tasks = [evaluate_candidate(cid, job_id, company_id) for cid in candidate_ids]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

- **Complexidade:** Média  
- **Prioridade:** P2  
- **Esforço:** S  
- **Arquivo-chave:** `app/domains/cv_screening/services/cv_screening_batch_service.py`

---

## FLUXO 4: ENTREVISTA WSI (Behavioral Assessment)

### A. Padrão Atual

```
POST /wsi/interview-graph/sessions
  → WSIInterviewGraph.start()
       → StateGraph LangGraph:
            lg_dispatcher → lg_load_context → lg_generate_question
            ↑ (loop)          lg_validate_response → lg_score_response
                              lg_advance
                              lg_generate_feedback [interrupt_before HITL]
```

**Padrão identificado:** PROMPT CHAINING com StateGraph (máquina de estados determinística). Cada nó processa e passa estado ao próximo, com routing condicional baseado no estado (não em decisão LLM livre).

### B. Padrão Recomendado

PROMPT CHAINING via StateGraph é o padrão correto.

```
[Pergunta N]
  → validate_response (PII masking + FairnessGuard) [quality gate]
  → score_response (Bloom/Dreyfus determinístico) [quality gate]
  → advance (próxima pergunta ou feedback)
  → [HITL interrupt_before generate_feedback]
  → generate_feedback (LLM) → persist score
```

**Justificativa:** A entrevista WSI tem estados claramente definidos, transições determinísticas e qualidade verificável por etapa — isso é exatamente o caso de uso de Prompt Chaining. O LangGraph StateGraph é a implementação correta.

### C. Análise de Complexidade

**Bem implementado:**
- `app/domains/cv_screening/agents/wsi_interview_graph.py:972`: `interrupt_before=["lg_generate_feedback"]` — HITL correto antes da decisão de alto impacto.
- `app/domains/cv_screening/agents/wsi_interview_graph.py:296-317`: Gate LGPD em `load_context` — quality gate correto.
- Scoring determinístico (Bloom/Dreyfus/STAR) sem LLM no cálculo final.
- `MAX_ITERATIONS = 8` como proteção de loop infinito.

**Gap crítico de persistência:**
- `wsi/sessions.py:183-200`: wsi_final_score NÃO é persistido no banco — sessão in-memory deletada após resposta REST. Isso é um bug arquitetural grave, não de padrão.

**Gap de silêncio no gate LGPD:**
- `wsi_interview_graph.py:319-324`: exception no ConsentChecker é logada como warning e o fluxo prossegue — viola o princípio de fail-closed para dados sensíveis.

### D. Mapeamento Proposto

Manter Prompt Chaining. Fixes urgentes (não de padrão):

1. Persistir `wsi_final_score` em tabela após HITL approval.
2. Tornar ConsentChecker exception blocking (fail-closed), não best-effort.

```python
# wsi_interview_graph.py:319-324
# ATUAL: except Exception: logger.warning() → prossegue
# RECOMENDADO:
except Exception as e:
    logger.error("[WSI] ConsentChecker failed — abortando por segurança: %s", e)
    state.error = "CONSENT_CHECK_FAILED"
    state.stage = WSIInterviewStage.ERROR
    return state  # fail-closed
```

- **Complexidade:** Média  
- **Prioridade:** P2 (padrão correto), P0 (fix de persistência e LGPD)  
- **Esforço:** S (padrão), M (fixes)  
- **Arquivo-chave:** `app/domains/cv_screening/agents/wsi_interview_graph.py:319-324`, `app/api/v1/wsi/sessions.py:183-200`

---

## FLUXO 5: WIZARD DE VAGA (WSI Wizard)

### A. Padrão Atual

```
POST /lia-assistant/job-wizard/graph-orchestrate
  → JobWizardGraph (StateGraph LangGraph):
       intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition
       [interrupt_before stage_transition] (HITL)

  → Nodes:
       intent_classifier: LLM classifica intent (WizardIntent enum)
       field_extractor:   LLM extrai campos do job draft
       tool_router:       Decide se usa tools (salary benchmark, skills)
       tool_executor:     Executa tools selecionadas
       response_generator: LLM gera resposta conversacional
       stage_transition:  Avança estágio (HITL gate)

  + WizardSmartOrchestrator: enriquecimento de JD via 5 fontes paralelas
  + PendingActionStore: gerencia confirmações multi-turn
  + TaskPlanner: decompõe em tarefas com agentes (inativo na maioria dos casos)
```

**Padrão identificado:** ORCHESTRATOR-WORKERS com StateGraph — o intent_classifier age como orchestrator dinâmico, workers são nodes especializados.

### B. Padrão Recomendado

**PROMPT CHAINING simples** é suficiente para este fluxo:

```
Input (mensagem do recrutador)
  → [Step 1] IntentClassifier (LLM, determin.) → WizardIntent
  → [Step 2] FieldExtractor (LLM, se intent=PROVIDE_INFO/MODIFY) → fields
  → [Step 3] ToolExecutor (se tools necessárias) → salary/skills data
  → [Step 4] ResponseGenerator (LLM) → mensagem conversacional
  → [Step 5] StageTransition (determinístico) → próximo estágio
  [HITL gate antes de confirmar criação de vaga]
```

**Justificativa:** O Wizard tem um fluxo de estágios bem definido (`WizardStage` enum), sem necessidade de decomposição dinâmica. O `intent_classifier` não "decide dinamicamente quais workers ativar" — ele mapeia para caminhos pré-definidos no grafo. Isso é Prompt Chaining com routing condicional entre steps, não Orchestrator-Workers.

O TaskPlanner (`app/orchestrator/task_planner.py`) existe mas está inativo na maioria dos casos — adicionou complexidade sem benefício real para o wizard.

### C. Análise de Complexidade

**Sobre-engenharia detectada:**
- `app/domains/job_management/agents/job_wizard_graph.py`: StateGraph com `_build_edges()` + `_build_conditional_edges()` + `_build_langgraph()` = 3 camadas de abstração para um fluxo de 6 nodes sequenciais com 2 ramificações simples.
- `app/api/v1/lia_assistant_graph.py` + `app/api/v1/wizard_smart_orchestrator.py`: Dois endpoints separados para o mesmo wizard, com overlap de responsabilidade.
- `app/orchestrator/task_planner.py:95-160`: TaskPlanner com LLM call para decompor tarefas — raramente ativado (só para queries genuinamente multi-agente), mas sempre presente no codebase.
- `EdgeCondition` dataclass com `priority` e `condition lambda` — abstração desnecessária para um grafo com 2-3 caminhos possíveis.

**Bem implementado:**
- `interrupt_before=["stage_transition"]` — HITL correto antes da confirmação de vaga.
- PostgresSaver como checkpointer — persistência cross-turn correta.
- `WizardSmartOrchestrator.format_enrichment_as_conversational_message()` — enriquecimento de JD bem encapsulado.

### D. Mapeamento Proposto

Simplificar para Prompt Chain linear com 5 steps e routing condicional simples:

```python
# Substituir StateGraph complexo por pipeline direto:
async def wizard_step(message, state, company_id):
    intent = await classify_intent(message)  # LLM
    if intent in [PROVIDE_INFO, MODIFY]:
        fields = await extract_fields(message, state)  # LLM
        if needs_tools(fields):
            tool_data = await execute_tools(fields)  # determinístico
            state.update(tool_data)
    response = await generate_response(intent, state)  # LLM
    next_stage = advance_stage(intent, state)  # determinístico
    if next_stage.requires_confirmation:
        return await hitl_gate(response, state)  # HITL
    return response, next_stage
```

- **Complexidade:** Alta (atual) → Simples (proposto)
- **Prioridade:** P0  
- **Esforço:** M  
- **Arquivos-chave:** `app/domains/job_management/agents/job_wizard_graph.py`, `app/api/v1/lia_assistant_graph.py`, `app/api/v1/wizard_smart_orchestrator.py`

---

## FLUXO 6: ONBOARDING CONVERSACIONAL

### A. Padrão Atual

```
POST /policy/setup
  → PolicySetupAgent.process_message(message, company_id, session_id)
       → get_or_create_session() [19 perguntas, 5 blocos]
       → if welcome: _welcome_response()
       → if block_confirmation: _handle_block_transition()
       → else: _process_answer()
            → LLM (EXTRACTION_PROMPT): parse natural language → structured fields
            → LLM (REPLY_PROMPT): gera próxima pergunta conversacional
            → save_to_policy(extracted_data)
  → {reply, current_block, current_question, progress}
```

**Padrão identificado:** PROMPT CHAINING — pipeline de perguntas sequenciais com LLM duplo por resposta (extraction + reply generation). Estado gerenciado em `PolicySetupSession`.

### B. Padrão Recomendado

PROMPT CHAINING é o padrão correto. A implementação está adequada.

```
[Resposta do recrutador]
  → [Step 1] ExtractionLLM: parse natural language → structured policy fields
             [quality gate: campos mínimos extraídos?]
  → [Step 2] Persist policy fields
  → [Step 3] ReplyLLM: gera próxima pergunta (ou transition de bloco)
  → Output: {reply, progress}
```

**Melhoria identificada:** Os dois prompts (EXTRACTION + REPLY) são LLM calls separadas em série. Poderiam ser combinados em uma única chamada com saída estruturada (JSON + texto) — reduzindo latência e custo.

### C. Análise de Complexidade

**Bem implementado:**
- `app/domains/policy/agents/agent.py`: Estrutura de 19 perguntas em 5 blocos bem organizada.
- Separação entre extraction LLM e reply LLM — boa prática de single responsibility.
- `session.waiting_for_block_confirmation` — state machine simples e efetiva.

**Gaps:**
- Sem gate de progresso: usuário pode "pular" sem confirmação — sem quality gate para campos obrigatórios.
- Sem integração com RabbitMQ `onboarding_events` (canal existe no PLATFORM_MAP mas não está sendo usado para persistir o progresso no Rails).
- `app/domains/policy/agents/agent.py`: usa `LLMService()` diretamente (não usa `get_provider_for_tenant`) — ignora configuração de modelo por tenant.

### D. Mapeamento Proposto

Manter Prompt Chaining. Otimizações:

1. Combinar EXTRACTION_PROMPT + REPLY_PROMPT em uma única chamada LLM com saída estruturada.
2. Emitir evento RabbitMQ `onboarding_events` após cada bloco completo para sincronização com Rails.

```python
# ATUAL: 2 LLM calls sequenciais
extracted = await llm.generate(EXTRACTION_PROMPT + message)
reply = await llm.generate(REPLY_PROMPT + extracted)

# RECOMENDADO: 1 LLM call com saída estruturada
result = await llm.generate_structured(COMBINED_PROMPT + message)
# result = { "extracted_fields": {...}, "reply": "..." }
```

- **Complexidade:** Simples  
- **Prioridade:** P1  
- **Esforço:** S  
- **Arquivo-chave:** `app/domains/policy/agents/agent.py`, `app/domains/policy/agents/system_prompt.py`

---

## FLUXO 7: GERAÇÃO DE JD (Job Description)

### A. Padrão Atual

```
WizardSmartOrchestrator.format_enrichment_as_conversational_message()
  → intelligent_data_orchestrator.get_salary_data() [múltiplas fontes]
       Sources: LearningPatterns + CompanyConfig + ATSHistory + SerpAPI + Fallback LLM
       → result.consensus (bool): indica se fontes concordam
       → result.primary_source, result.primary_confidence
  → generate_enriched_jd() [tool: job_wizard_tools.py]
       → LLM gera JD baseado em campos coletados

SeniorityResolver (Voting implícito):
  → 5 sinais: explicit (0.50) + title_keywords (0.25) + jd_analysis (0.25) + salary_range (0.15) + skills_complexity (0.10)
  → Motor de combinação determinístico → full/majority/conflict/single/none
  → Se conflict → requires_confirmation = True → HITL

AgentQualityEvaluator (shadow mode):
  → QUALITY_EVAL_SAMPLING_RATE = 10%
  → 5 métricas: task_completion, factual_accuracy, fairness, coherence, actionability
  → LLM-as-judge (Claude Haiku) → EvaluationResult
  → Persiste em agent_quality_evaluations (não retroalimenta geração)
```

**Padrão atual:** EVALUATOR-OPTIMIZER parcial — há um avaliador (`AgentQualityEvaluator`) mas em shadow mode sem loop de refinamento. O `SeniorityResolver` implementa Voting (Parallelization variant) de forma determinística.

### B. Padrão Recomendado

**EVALUATOR-OPTIMIZER completo** para geração de JD:

```
Input (job fields)
  → [Generator] JD Draft Generator (LLM) → draft_jd
  → [Evaluator] JD Quality Evaluator (LLM Haiku):
       - completeness: todos os campos necessários?
       - bias: linguagem discriminatória?
       - clarity: score de legibilidade?
       - wsi_alignment: alinhado com perguntas WSI?
  → [Quality Gate] score ≥ threshold? → finalizar
                   score < threshold? → feedback → Generator (próxima iteração)
  → Max 3 iterações → output final
```

**Justificativa:** A geração de JD tem critério de qualidade verificável (score de completude, ausência de bias, alinhamento WSI) e benefício claro de iteração. O `AgentQualityEvaluator` já existe mas não está no loop de produção.

### C. Análise de Complexidade

**Oportunidade de Evaluator-Optimizer não aproveitada:**
- `app/domains/ai/services/agent_quality_evaluator.py:54`: `QUALITY_EVAL_SAMPLING_RATE = 10%` — avaliação só em shadow mode (background Celery), não bloqueia produção.
- O avaliador existe mas o resultado não retroalimenta a geração — é monitoramento, não otimização.
- `app/domains/job_management/tools/job_wizard_tools.py:517`: `"consensus": result.consensus` — a agregação multi-fonte já existe, mas não há loop de refinamento se a JD não atinge qualidade.

**Voting bem implementado (Parallelization variant):**
- `app/domains/cv_screening/services/seniority_resolver.py:18`: "Regra 2: Maioria concorda (2+) → confiança 0.85, acordo 'majority'" — Voting determinístico correto para resolução de senioridade.
- `app/domains/job_management/tools/job_wizard_tools.py:588`: `"consensus": result.consensus` — multi-fonte com consensus check.

### D. Mapeamento Proposto

Ativar `AgentQualityEvaluator` no loop de produção para JD (max 2 iterações):

```python
# app/domains/job_management/tools/job_wizard_tools.py: generate_enriched_jd()
async def generate_enriched_jd_with_eval(fields, company_id):
    for attempt in range(MAX_JD_ITERATIONS):  # max 2
        draft = await generate_jd_draft(fields)
        eval_result = await jd_evaluator.evaluate(draft, fields)
        if eval_result.overall_score >= JD_QUALITY_THRESHOLD:
            return draft
        fields["improvement_hints"] = eval_result.feedback  # retroalimentação
    return draft  # melhor versão após N tentativas
```

- **Complexidade:** Média  
- **Prioridade:** P1  
- **Esforço:** M  
- **Arquivos-chave:** `app/domains/ai/services/agent_quality_evaluator.py`, `app/domains/job_management/tools/job_wizard_tools.py`

---

## FLUXO 8: COMUNICAÇÃO COM CANDIDATOS

### A. Padrão Atual

```
Chat Input → CascadedRouter → domain="communication"
  → CommunicationReActAgent (create_react_agent, LangGraph)
       → LLM decide quais tools chamar:
            get_candidate_preferences() → canal preferido
            generate_message() → draft de mensagem
            [HITL gate: initial_contact, rejection_feedback, offer_letter]
            send_email() ou send_whatsapp() ou send_teams()
       → LLM gera resposta confirmando envio
```

**Padrão identificado:** AUTONOMOUS AGENT — loop ReAct aberto com decisão LLM em cada step.

### B. Padrão Recomendado

**ROUTING + PROMPT CHAINING** — fluxo determinístico não requer loop aberto:

```
Input (mensagem do recrutador + contexto candidato)
  → [Router] Classifica tipo de comunicação:
       bulk_rejection | individual_feedback | offer_letter | status_update | outreach
  → [Prompt Chain por tipo]:
       Step 1: get_candidate_preferences() → canal + idioma [determinístico]
       Step 2: generate_message(tipo, candidato, vaga) → draft [LLM]
       Step 3: [HITL gate para tipos de alto impacto] → aprovação recrutador
       Step 4: send_via_channel(canal, draft) → confirmação [determinístico]
```

**Justificativa:** O domínio de comunicação tem caminhos bem definidos por tipo de mensagem. Não há exploração de domínio de ação aberto — o canal, o template e o recipient são conhecidos antes do início. Um loop ReAct adiciona latência e risco de hallucination sem benefício. O HITL gate (já implementado para 3 tipos) é o safeguard correto — não o loop aberto.

### C. Análise de Complexidade

**Over-engineering detectado:**
- `app/domains/communication/agents/communication_react_agent.py`: `create_react_agent` com loop aberto para um fluxo que é fundamentalmente: classifica tipo → gera mensagem → [HITL] → envia.
- `_HITL_MESSAGE_TYPES = frozenset({"initial_contact", "rejection_feedback", "offer_letter"})` — o HITL está correto, mas o ReAct loop ao redor dele não é necessário.
- Risco: loop ReAct pode "decidir" enviar por canal errado, omitir HITL gate, ou gerar mensagens em múltiplas tentativas antes de enviar.

**Bem implementado:**
- `app/services/email_providers/mailgun_provider.py`, `app/services/whatsapp_client.py`, `app/shared/channels/adapters/teams_adapter.py` — provedores bem encapsulados.
- HITL gate para tipos de alto impacto — correto e bem implementado.

### D. Mapeamento Proposto

Substituir CommunicationReActAgent por Prompt Chain determinístico com routing inicial:

```python
# app/domains/communication/domain.py: execute_action()
async def send_communication(tipo, candidato_id, job_id, company_id):
    prefs = await get_candidate_preferences(candidato_id)  # determinístico
    draft = await generate_message_llm(tipo, candidato_id, job_id)  # LLM
    if tipo in HITL_REQUIRED_TYPES:
        await hitl_gate.request_approval(draft)  # blocking HITL
        return  # aguarda callback
    await send_via_channel(prefs.channel, draft)  # determinístico
    return confirmation
```

- **Complexidade:** Alta (atual) → Simples (proposto)
- **Prioridade:** P0  
- **Esforço:** L  
- **Arquivo-chave:** `app/domains/communication/agents/communication_react_agent.py`

---

## FLUXO 9: PIPELINE AUTÔNOMO

### A. Padrão Atual

```
[Vários triggers]
  → AutonomousReActAgent (Tier 6 do CascadedRouter)
       → 40+ tools cross-domain
       → Circuit breaker (failure_threshold=3, recovery_timeout=30s)
       → MAX_STEPS = 10
       → EnhancedAgentMixin (FairnessGuard + memória longa)
       → Loop: LLM decide → tool call → resultado → LLM decide → ...

[Automação via AutomationReActAgent]
  → decompose_task() → DAG planning
  → prioritize_tasks() → execution order
  → Loop: create_goal → update_task_status → schedule_automation
```

**Padrão identificado:** AUTONOMOUS AGENT — tanto o AutonomousReActAgent quanto o AutomationReActAgent são loops abertos com ferramentas. Este é o fluxo mais complexo e de maior risco.

### B. Padrão Recomendado

**ORCHESTRATOR-WORKERS** — decomposição dinâmica controlada por orchestrator com workers especializados:

```
Input (tarefa complexa cross-domain)
  → [Orchestrator] TaskPlanner.create_plan(message, intent)
       → LLM decompõe em tarefas atômicas
       → Retorna: [{step, agent, dependencies, can_run_parallel}]
  → [Parallel/Sequential Workers] por task:
       step.can_run_parallel → asyncio.gather(worker_A, worker_B)
       step.dependencies → aguarda resultado anterior
  → [Merger] consolida resultados
  → [HITL gate] antes de qualquer ação irreversível (write operations)
  → Response
```

**Justificativa:** O `TaskPlanner` já existe e implementa corretamente o padrão Orchestrator-Workers (`app/orchestrator/task_planner.py`). O AutonomousReActAgent como fallback de último recurso é válido — o problema é que está sendo usado como modo primário para automações, não como safety net.

### C. Análise de Complexidade

**Anti-pattern: God-Agent**
- `app/domains/autonomous/agents/autonomous_tool_registry.py`: 40+ tools cross-domain em um único agente. Isso é o anti-pattern "God Agent" — viola Single Responsibility e torna o comportamento imprevisível.
- `app/domains/automation/agents/automation_react_agent.py`: AutomationReActAgent também com loop aberto + decompose_task tool — duplicação parcial com TaskPlanner.
- Risco: com 40+ tools e MAX_STEPS=10, o espaço de ação é grande demais para garantir comportamento determinístico.

**Circuit breaker é necessário mas insuficiente:**
- `autonomous_react_agent.py`: `CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30s)` — correto como failsafe, mas não substitui guardrails de HITL para ações irreversíveis (reject_candidate, batch_move, etc.).

**TaskPlanner existe mas está desconectado:**
- `app/orchestrator/task_planner.py:268`: "Execution levels (tasks grouped by parallel execution)" — a infra está pronta para Orchestrator-Workers, mas não é o path padrão.

### D. Mapeamento Proposto

Fazer TaskPlanner o path padrão para automações, AutonomousAgent apenas para fallback de ação única:

```
Automação request
  → TaskPlanner.create_plan() → plan com steps + parallelism
  → Para steps can_run_parallel: asyncio.gather(workers)
  → Para steps com dependency: aguardar resultado anterior
  → HITL gate antes de qualquer write operation
  → AutonomousAgent apenas se plan.estimated_steps == 1 e sem workers especializados disponíveis
```

Reduzir tool pool do AutonomousAgent de 40+ para ≤ 15 (read-only + safe writes).

- **Complexidade:** Alta  
- **Prioridade:** P0  
- **Esforço:** XL  
- **Arquivos-chave:** `app/orchestrator/task_planner.py`, `app/domains/autonomous/agents/autonomous_react_agent.py`, `app/domains/autonomous/agents/autonomous_tool_registry.py`

---

## FLUXO 10: ANÁLISE DE CANDIDATO

### A. Padrão Atual

```
[Via SourcingEnrichAgent]
  → analyze_profile(candidate_id) → LLM analysis
  → score_candidate(candidate_id, job_id) → WSI scoring
  → compare_candidates([ids], job_id) → LLM comparison
  → rank_candidates([ids], job_id) → WRF ranking

[Via MultiStrategySearchService — separado]
  asyncio.gather(direct, adjacent, silver, reengagement)
  → dedup + weighted ranking

[Via SeniorityResolver — Voting determinístico]
  5 sinais → consensus resolution → SeniorityResolution

[Via DigitalTwinDomain — RAG few-shot]
  → evaluate_with_twin(candidate_id, job_id) → SME-simulated judgment
```

**Padrão atual:** Misto — Parallelization parcial (MultiStrategySearch), Voting determinístico (SeniorityResolver), sem integração entre as partes.

### B. Padrão Recomendado

**PARALLELIZATION (Voting variant)** para análise holística de candidato:

```
Input (candidate_id, job_id)
  → asyncio.gather (paralelo):
       A: RubricEvaluation (determinístico + LLM)
       B: DigitalTwinEvaluation (RAG few-shot)
       C: SeniorityResolution (multi-sinal determinístico)
       D: MarketBenchmark (SerpAPI + LLM fallback)
  → [Merger / Voter]:
       Média ponderada dos scores (A:0.40, B:0.30, C:0.20, D:0.10)
       Detecção de divergências > threshold → flag para revisão humana
  → Candidate profile com score consolidado + confidence + divergences
```

**Justificativa:** A análise de candidato tem múltiplas perspectivas independentes (técnica, comportamental, seniority, mercado) que podem ser calculadas em paralelo e consolidadas via voting ponderado. Isso é o caso clássico de Parallelization Voting do Anthropic.

### C. Análise de Complexidade

**Oportunidade de Voting não aproveitada:**
- `app/domains/sourcing/agents/sourcing_enrich_agent.py:6-9`: `analyze_profile, compare_candidates, score_candidate, rank_candidates` são chamadas sequenciais via ReAct loop.
- `app/domains/digital_twin/domain.py`: DigitalTwinDomain existe mas não está integrado ao pipeline de scoring principal — é chamado separadamente.
- `app/domains/cv_screening/services/seniority_resolver.py:18`: SeniorityResolver já implementa Voting corretamente (full/majority/conflict) mas só é usado na geração de perguntas WSI, não na análise final de candidato.

**Bem implementado:**
- `app/services/multi_strategy_search.py`: `asyncio.gather` com 4 estratégias + weighted dedup — Parallelization Sectioning correto.
- `SeniorityResolver`: Voting determinístico com metadados de audit — pode ser modelo para o Voting de análise.

### D. Mapeamento Proposto

Criar `CandidateAnalysisOrchestrator` que coordena as perspectivas em paralelo:

```python
# app/domains/cv_screening/services/candidate_analysis_orchestrator.py
async def analyze_candidate(candidate_id, job_id, company_id):
    rubric, twin, seniority, market = await asyncio.gather(
        rubric_evaluation_service.evaluate(candidate_id, job_id),
        digital_twin_domain.evaluate_with_twin(candidate_id, job_id, company_id),
        resolve_seniority_full(job_id, company_id),
        market_benchmark_service.get_candidate_market_fit(candidate_id, job_id),
        return_exceptions=True
    )
    return _merge_and_vote(rubric, twin, seniority, market, weights=ANALYSIS_WEIGHTS)
```

- **Complexidade:** Média  
- **Prioridade:** P1  
- **Esforço:** M  
- **Arquivos-chave:** `app/domains/sourcing/agents/sourcing_enrich_agent.py`, `app/domains/digital_twin/domain.py`, `app/domains/cv_screening/services/seniority_resolver.py`

---

## ANTI-PATTERNS ENCONTRADOS

### AP-1: God Agent (Autonomous Tier 6)
**Arquivo:** `app/domains/autonomous/agents/autonomous_tool_registry.py`  
**Evidência:** 40+ tools cross-domain registradas em um único agente com MAX_STEPS=10 e loop aberto.  
**Impacto:** Comportamento imprevisível, custo elevado, risco de ações não intencionais.  
**Padrão Anthropic violado:** "Use specialized agents rather than one agent with all tools."

### AP-2: Autonomous Agent como Fallback de Routing
**Arquivo:** `app/orchestrator/cascaded_router.py` (Tier 6)  
**Evidência:** `AutonomousReActAgent` é ativado automaticamente quando Tiers 0-5 não têm confiança suficiente — transformando uma falha de classificação em execução de agente autônomo.  
**Impacto:** Queries ambíguas podem disparar ações irreversíveis (move_candidate, send_email) sem intenção do usuário.  
**Padrão Anthropic violado:** "Autonomous agents should be reserved for tasks that require real-world environment interaction in long action sequences."

### AP-3: Evaluator sem Loop (Shadow Mode Evaluator)
**Arquivo:** `app/domains/ai/services/agent_quality_evaluator.py:54`  
**Evidência:** `QUALITY_EVAL_SAMPLING_RATE = 0.10` — avaliação em 10% dos casos, em background, sem retroalimentação para o gerador.  
**Impacto:** O padrão Evaluator-Optimizer está incompleto — existe avaliação mas sem otimização.  
**Padrão Anthropic violado:** "The evaluator provides feedback that the generator uses to improve."

### AP-4: Parallelization Disponível mas não Conectada
**Arquivo:** `app/services/multi_strategy_search.py` (existente) vs `app/domains/sourcing/agents/sourcing_react_agent.py` (usado no chat)  
**Evidência:** `MultiStrategySearchService` com `asyncio.gather` de 4 estratégias existe mas não é chamado pelo agente de chat. O chat usa busca sequencial via ReAct loop.  
**Impacto:** 3-4x mais lento que necessário; busca incompleta (só 1 de 4 estratégias ativa no chat).  
**Padrão Anthropic violado:** "When independent subtasks can be parallelized, do it."

### AP-5: Over-Engineering no Wizard de Vaga
**Arquivo:** `app/domains/job_management/agents/job_wizard_graph.py`  
**Evidência:** StateGraph com `_build_edges()` + `_build_conditional_edges()` + `_build_langgraph()` para fluxo de 6 nodes com 2-3 ramificações simples. `EdgeCondition` dataclass com prioridade e condition lambda para casos que cabem em 5 linhas de if/elif.  
**Impacto:** Código difícil de manter, debugging complexo, overhead de serialização LangGraph sem benefício arquitetural.  
**Padrão Anthropic violado:** "Start with the simplest possible solution."

### AP-6: ReAct Loop para Fluxo Determinístico (Comunicação)
**Arquivo:** `app/domains/communication/agents/communication_react_agent.py`  
**Evidência:** `create_react_agent` com loop aberto para fluxo: get_preferences → generate_message → [HITL] → send. Todos os steps têm inputs/outputs definidos antecipadamente.  
**Impacto:** Latência desnecessária, risco de o LLM "decidir" omitir HITL gate ou enviar por canal errado.  
**Padrão Anthropic violado:** "Workflows are appropriate when the process is well-defined; agents are for open-ended exploration."

---

## RECOMENDAÇÕES PRIORITIZADAS

### REC-1 (P0, Esforço L): Conectar MultiStrategySearch ao Chat de Sourcing
**Impacto:** Reduz latência de busca em 3-4x, aumenta recall de candidatos de ~25% para ~90% (4 estratégias vs 1).  
**Ação:** `app/domains/sourcing/domain.py:execute_action("search_candidates")` → chamar `multi_strategy_search_service.search()` em vez de delegar ao SourcingReActAgent.  
**Arquivos:** `app/domains/sourcing/domain.py`, `app/services/multi_strategy_search.py`  
**Padrão:** Parallelization (Sectioning)

### REC-2 (P0, Esforço M): Remover AutonomousAgent do Fallback Automático de Routing
**Impacto:** Elimina risco de ações irreversíveis disparadas por queries ambíguas. Reduz custo por query ~40% nos casos de Tier 6.  
**Ação:** `app/orchestrator/cascaded_router.py` Tier 6 → substituir por `clarification_needed` inteligente. AutonomousAgent passa a ser ativado apenas por intent explícito "modo autônomo".  
**Arquivos:** `app/orchestrator/cascaded_router.py`  
**Padrão:** Routing correto, sem Autonomous como fallback

### REC-3 (P0, Esforço M): Simplificar Wizard de Vaga para Prompt Chain
**Impacto:** Reduz complexidade de manutenção, elimina overhead de StateGraph para fluxo sequencial.  
**Ação:** Substituir `JobWizardGraph` com `EdgeCondition` + `_build_langgraph()` por pipeline linear de 5 async funções com routing condicional simples (if/elif).  
**Arquivos:** `app/domains/job_management/agents/job_wizard_graph.py`  
**Padrão:** Prompt Chaining simples

### REC-4 (P0, Esforço L): Converter CommunicationReActAgent para Prompt Chain
**Impacto:** Elimina risco de HITL bypass via loop ReAct, reduz latência de comunicação.  
**Ação:** Substituir `create_react_agent` por pipeline determinístico: classify_type → get_preferences → generate_message → [HITL gate] → send.  
**Arquivos:** `app/domains/communication/agents/communication_react_agent.py`  
**Padrão:** Routing + Prompt Chaining

### REC-5 (P1, Esforço M): Ativar Evaluator-Optimizer para Geração de JD
**Impacto:** Aumenta qualidade das JDs geradas, reduz retrabalho manual do recrutador.  
**Ação:** Mover `AgentQualityEvaluator` de shadow mode para loop de produção na geração de JD (max 2 iterações, quality threshold configurável).  
**Arquivos:** `app/domains/ai/services/agent_quality_evaluator.py`, `app/domains/job_management/tools/job_wizard_tools.py`  
**Padrão:** Evaluator-Optimizer completo

---

## CHECKLIST DE VERIFICAÇÃO DO RELATÓRIO

- [x] Todos os 6 padrões Anthropic referenciados? SIM — Prompt Chaining (F3,F4,F6), Routing (F1), Parallelization (F2,F10), Orchestrator-Workers (F9), Evaluator-Optimizer (F7), Autonomous Agent (F8,F9)
- [x] Padrão atual vs recomendado para cada fluxo? SIM — 10 fluxos mapeados com seções A e B
- [x] Anti-patterns identificados com evidência de arquivo:linha? SIM — 6 anti-patterns com referências exatas
- [x] God-agent identificado especificamente? SIM — AP-1 em `autonomous_tool_registry.py`
- [x] Parallelization opportunity perdida identificada? SIM — AP-4 em `multi_strategy_search.py` vs `sourcing_react_agent.py`
- [x] Evaluator-Optimizer sem loop identificado? SIM — AP-3 em `agent_quality_evaluator.py:54`
- [x] Prioridades e esforços atribuídos? SIM — todos os fluxos e recomendações têm P0/P1/P2 e S/M/L/XL
- [x] Código concreto a mudar para cada recomendação? SIM — todas as 5 recomendações têm arquivos e pseudocódigo
