# Agent Specs — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` (GitHub WeDOTalent)
> **SPEC-DRIVEN DEVELOPMENT** — um bloco por agente/domínio com contratos completos.

---

## 1. Pipeline Agents (Workflow Graph)

Estes agentes formam o pipeline sequencial do `WorkflowOrchestrator` em `src/workflow/graph.py`.

### 1.1 IntentAnalyzerAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/intent_analyzer.py` |
| **Objetivo** | Analisar a query do recrutador e extrair intent estruturado |
| **Input** | `QueryState.question` (string em português) |
| **Output** | `QueryState.intent` com: entities, main_action, filters, aggregations, fields_needed, restricted_fields |
| **LLM** | Gemini (via settings) — temperature 0.0 |
| **Tools** | RAGService para consultar documentação de APIs |
| **Limites** | Não executa ações, apenas classifica. Pode retornar erro se query incompreensível |

**Actions identificáveis:**
- `list` — listar registros
- `count` — contar registros
- `filter` — filtrar por critérios
- `aggregate` — calcular métricas (avg, sum, etc.)
- `analyze` — análise complexa (correlações, padrões)
- `create_applies` — inscrever candidatos em vaga (ação composta)
- `multi_step` — múltiplas ações encadeadas

### 1.2 APIPlannerAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/api_planner.py` |
| **Objetivo** | Criar plano de execução sequencial usando APIs disponíveis |
| **Input** | `QueryState.intent` + documentação RAG |
| **Output** | `QueryState.api_plan` — lista de `PlanStep` |
| **LLM** | Gemini — temperature 0.0 |
| **Tools** | RAGService |
| **Limites** | Cada step deve ter: step, api, params, save_as, description. Máximo ~10 steps |

**Estrutura de um PlanStep:**
```
{
  "step": 1,
  "api": "candidates_search",
  "params": {"where": {"city": "São Paulo"}},
  "save_as": "candidates_data",
  "description": "Buscar candidatos em SP",
  "execute_if": null,
  "fallback_step": null,
  "requires_confirmation": false
}
```

### 1.3 APIExecutorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/api_executor.py` |
| **Objetivo** | Executar chamadas REST ao ATS API seguindo o plano |
| **Input** | `QueryState.api_plan` |
| **Output** | `QueryState.api_results` — dict com resultados por save_as |
| **LLM** | Não usa LLM |
| **Tools** | `ATSAPIClient` — REST client para ats_api |
| **Limites** | Respeita `requires_confirmation`, suporta `VariableSubstitutor` para interpolação entre steps |

### 1.4 PlanValidatorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/plan_validator.py` |
| **Objetivo** | Validar resultados da execução — decidir se precisa replanejar |
| **Input** | `QueryState.api_results` |
| **Output** | Decision: continue, replan, ou abort |
| **LLM** | Gemini — temperature 0.0 |
| **Limites** | Máximo 1 re-planejamento (evitar loops infinitos) |

### 1.5 DataProcessorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/data_processor.py` |
| **Objetivo** | Processar e formatar dados brutos das APIs |
| **Input** | `QueryState.api_results` |
| **Output** | `QueryState.processed_data` — dados formatados com summary |
| **LLM** | Não usa LLM (processamento determinístico) |
| **Limites** | Lida com paginação, deduplicação, agregação numérica |

### 1.6 AnswerFormatterAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/answer_formatter.py` |
| **Objetivo** | Formatar resposta final usando taxonomia de 11 tipos |
| **Input** | `QueryState.processed_data` + `QueryState.question` |
| **Output** | `QueryState.final_answer` — string formatada em português |
| **LLM** | Gemini — temperature 0.0 |
| **Limites** | Nunca cola JSON bruto, usa nomes concretos, português brasileiro |

---

## 2. Domain Agents

Cada domínio é uma especialização de `DomainPrompt` que opera dentro de um contexto específico.

### 2.1 AppliesDomain — Gestão de Candidaturas

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/applies/domain.py` |
| **Domain ID** | `applies` |
| **Objetivo** | Gestão completa de candidaturas: busca, pipeline/kanban, ranking, comparação, analytics, ações em lote |
| **Contexto** | Opera dentro de uma vaga (`job_id`) |
| **LLM** | `create_tracked_llm(temperature=0.0, service_name="AppliesDomain")` |
| **API Client** | `AppliesAPIClient` |
| **Memória** | `AppliesConversationMemory` |
| **Cache** | `AppliesCacheManager` com tier para ações que precisam |

**Ações (DomainAction):**

| Action ID | Tipo | Descrição | Exemplos |
|-----------|------|-----------|----------|
| `search_applies` | QUERY | Buscar candidaturas com filtros | "Candidatos dessa vaga", "Buscar Maria" |
| `show_apply_details` | QUERY | Detalhes de um candidato específico | "Detalhes do candidato X" |
| `pipeline_status` | QUERY | Status do pipeline/kanban | "Pipeline da vaga" |
| `move_apply` | ACTION | Mover candidato entre etapas | "Mover João para Entrevista" |
| `compare_candidates` | ANALYZE | Comparar candidatos | "Compare Maria e João" |
| `bulk_move` | ACTION | Mover múltiplos candidatos | "Mover todos aprovados" |
| `ranking` | ANALYZE | Ranking por score/critério | "Top 5 candidatos" |
| `analytics` | AGGREGATE | Analytics da vaga | "Funil de conversão" |
| `scoring` | ANALYZE | Score de candidatos | "Score do candidato X" |

**Prompt Builder:** `AppliesDynamicPromptBuilder` — gera prompts dinâmicos com até 8 ações e 2 exemplos por ação.

### 2.2 JobsDomain — Gestão de Vagas

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/jobs/domain.py` |
| **Domain ID** | `jobs` |
| **Objetivo** | CRUD de vagas, analytics, pipeline health, sourcing automático, feedback |
| **LLM** | `create_tracked_llm(temperature=0.0, service_name="JobsDomain")` |
| **API Client** | `JobsAPIClient` |
| **Cache** | `TieredContextManager` com Tier1 (leve) e Tier2 (completo) |
| **Fairness** | `JobFairnessGuard` — bloqueia filtros discriminatórios |

**Ações:**

| Action ID | Tipo | Descrição |
|-----------|------|-----------|
| `search_jobs` | QUERY | Buscar vagas |
| `show_job_details` | QUERY | Detalhes de uma vaga |
| `create_job` | ACTION | Criar nova vaga |
| `update_job` | ACTION | Atualizar vaga |
| `pipeline_status` | QUERY | Status do pipeline |
| `pipeline_health` | ANALYZE | Saúde do pipeline |
| `job_analytics` | AGGREGATE | Analytics da vaga |
| `summarize_job` | ANALYZE | Relatório/resumo |
| `alerts` | QUERY | Alertas e gargalos |
| `account_stats` | AGGREGATE | Estatísticas da conta |
| `export_job` | ACTION | Exportar dados |
| `auto_source` | ACTION | Sourcing automático |
| `send_reject_feedback` | ACTION | Feedback de rejeição |

**Pattern Matching:** `_CONTEXT_ACTION_PATTERNS` — regex para resolver ação rapidamente sem LLM quando possível (ex: "pipeline" → `pipeline_status`).

### 2.3 InsightsDomain — Analytics e Briefings

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/insights/domain.py` |
| **Domain ID** | `insights` |
| **Objetivo** | Análises cross-domain: briefings executivos, métricas, KPIs, gargalos, comparações, tendências |
| **LLM** | `create_tracked_llm(temperature=0.0, service_name="InsightsDomain")` |
| **API Client** | `InsightsAPIClient` |

**Ações:**

| Action ID | Tipo | Descrição |
|-----------|------|-----------|
| `daily_briefing` | ANALYZE | Briefing diário executivo |
| `job_status_report` | ANALYZE | Report de vaga específica |
| `metrics_query` | AGGREGATE | Métricas e KPIs |
| `pipeline_bottleneck` | ANALYZE | Gargalos no pipeline |
| `candidate_comparison` | ANALYZE | Comparação de candidatos |
| `weekly_summary` | ANALYZE | Resumo semanal |
| `trend_analysis` | ANALYZE | Análise de tendências |
| `performance` | AGGREGATE | Performance de recrutamento |
| `alerts` | QUERY | Alertas proativos |

**Formato de resposta estruturada:** Resumo Executivo → Dados → Análise → Riscos → Recomendações.

### 2.4 MessagingDomain — Comunicação com Candidatos

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/messaging/domain.py` |
| **Domain ID** | `messaging` |
| **Objetivo** | Envio de emails, feedbacks, convites, follow-ups para candidatos |
| **LLM** | `create_tracked_llm(temperature=0.0, service_name="MessagingDomain")` |
| **API Client** | `MessagingAPIClient` |
| **Regra crítica** | NUNCA envia sem confirmação explícita do recrutador — sempre preview primeiro |

**Ações:**

| Action ID | Tipo | Descrição |
|-----------|------|-----------|
| `send_feedback_positive` | ACTION | Feedback positivo/aprovação |
| `send_feedback_negative` | ACTION | Feedback negativo/rejeição |
| `send_invite` | ACTION | Convite para entrevista |
| `send_followup` | ACTION | Follow-up |
| `send_custom` | ACTION | Mensagem customizada |
| `check_history` | QUERY | Histórico de comunicações |
| `bulk_send` | ACTION | Envio em lote |

### 2.5 AutonomousDomain — Agente Universal ReAct

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/autonomous/domain.py` |
| **Domain ID** | `autonomous` |
| **Objetivo** | Agente universal com acesso a TODAS as APIs (~73 tools). Resolve queries complexas ou cross-domain |
| **LLM** | Gemini — temperature controlada |
| **Prompt** | `AUTONOMOUS_SYSTEM_PROMPT` — 28KB de instruções detalhadas |
| **Agent** | `UniversalReActAgent` — loop ReAct com tools |

**Capacidades:**
- Acesso a ~73 ferramentas cobrindo toda a API do ATS
- Playbooks YAML para operações compostas
- Resolução de contexto UI (`viewing_entities`)
- Memória de conversa
- Compressão de contexto para conversas longas

**Playbooks disponíveis:**

| Playbook | Arquivo YAML |
|----------|-------------|
| Diagnóstico de Vaga | `diagnostico_vaga.yaml` |
| Panorama de Vagas | `panorama_vagas.yaml` |
| Sourcing Completo | `sourcing_completo.yaml` |
| Triagem de Vaga | `triagem_vaga.yaml` |
| Review Semanal | `weekly_review.yaml` |

### 2.6 EvaluationDomain — Avaliação de Candidatos

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/evaluation/domain.py` |
| **Domain ID** | `evaluation` |
| **Objetivo** | Processar e avaliar respostas de candidatos em entrevistas via chat |
| **LLM** | `create_tracked_llm(temperature=0.2, service_name="EvaluationNode")` — nota: temperature 0.2 |
| **Graph** | LangGraph próprio: classify → evaluate → decide_flow → craft_message |

**Rubrica de avaliação:**

| Critério | Peso |
|----------|------|
| Relevância | 30% |
| Profundidade | 30% |
| Clareza | 20% |
| Exemplos | 20% |

**Classificação de input:**

| Intent | Descrição |
|--------|-----------|
| `answer` | Candidato respondeu à pergunta |
| `question` | Candidato fez uma pergunta |
| `off_topic` | Fora do contexto |
| `unclear` | Confuso ou muito curto |
| `not_interested` | Desinteresse explícito |

**Segurança:** Proteção contra prompt injection via `safe_process_input()`.

---

## 3. Workers (Celery)

| Worker | Arquivo | Queue | Função |
|--------|---------|-------|--------|
| `celery_worker.py` | `celery_worker.py` | default | Processa queries de domínio via RabbitMQ |
| `evaluation_worker.py` | `evaluation_worker.py` | evaluation | Processa avaliações de candidatos |

---

## 4. Mapa de Dependências entre Domínios

```
                    ┌──────────────┐
                    │  autonomous  │  ← acessa todos os outros
                    │  (universal) │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  applies   │   │   jobs    │   │ insights  │
    │ (por vaga) │   │ (CRUD+)  │   │ (cross)   │
    └────────────┘   └──────────┘   └───────────┘
          │                │
    ┌─────▼─────┐   ┌─────▼─────┐
    │ messaging │   │evaluation │
    │ (emails)  │   │(entrevista)│
    └───────────┘   └───────────┘
```

---

## Referências

| Componente | Arquivo |
|-----------|---------|
| Domain Registry | `src/domains/registry.py` |
| Base Domain | `src/domains/base.py` |
| Applies Domain | `src/domains/applies/domain.py` |
| Jobs Domain | `src/domains/jobs/domain.py` |
| Insights Domain | `src/domains/insights/domain.py` |
| Messaging Domain | `src/domains/messaging/domain.py` |
| Autonomous Domain | `src/domains/autonomous/domain.py` |
| Evaluation Domain | `src/domains/evaluation/domain.py` |
| Autonomous Prompt | `src/domains/autonomous/prompts.py` |
| Evaluation Graph | `src/domains/evaluation/graph.py` |
