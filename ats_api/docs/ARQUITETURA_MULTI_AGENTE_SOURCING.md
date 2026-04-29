# Arquitetura Multi-Agente: sourced_profile_sourcing

## Descoberta Importante

Existem **dois sistemas paralelos** dentro de `sourced_profile_sourcing`:

| Sistema | Diretório | Status em Producao |
|---------|-----------|-------------------|
| **Actions** | `actions/` (14 arquivos) | ATIVO - usado pelo `domain.py` |
| **Agents** | `agents/` (10 arquivos) | NAO CONECTADO - nenhum codigo chama `MultiAgentOrchestrator` |

O `domain.py` importa **apenas** `SourcedProfileSourcingActions` (actions/) e mapeia 33 action handlers diretamente. O `MultiAgentOrchestrator` e os 6 agentes especializados existem, mas **nenhum arquivo em producao os invoca**.

---

## Como o Sistema REALMENTE Funciona (Fluxo em Producao)

```
1. Mensagem chega via RabbitMQ ou CLI
       |
2. MessageRouter.route()
       | (domain = "sourced_profile_sourcing")
       v
3. DomainOrchestrator.process_query()
       |
       +- Busca domain via DomainRegistry -> SourcedProfileSourcingDomain
       +- Monta DomainContext (sourcing_id, user_id, memory, etc.)
       +- Carrega aggregated_stats (cache TTL via StatsManager)
       |
       v
4. DomainWorkflow.process() (LangGraph 3 nodes)
       |
       +- Node 1: DomainIntentAgent
       |     +- Chama domain.process_intent(query, context)
       |         +- LLM (Gemini) analisa query -> retorna {action_id, params, confidence}
       |
       +- Node 2: DomainExecutorAgent
       |     +- Chama domain.execute_action(action_id, params, context, aggregated_stats)
       |         +- Lookup no dict action_handlers -> chama self._actions.<method>()
       |
       +- Node 3: DomainResponseBuilder
             +- Formata resposta via TemplateFormatter
       |
       v
5. DomainOrchestrator cria mensagem na API do Rails
       |
       v
6. Resposta retorna ao usuario
```

### Arquivos envolvidos nesse fluxo:

```
src/services/message_router.py          -> Rota por domain
src/domains/orchestrator.py             -> Orquestra domain + context + stats
src/domains/workflow.py                 -> LangGraph (3 nodes)
src/domains/sourced_profile_sourcing/
  domain.py                             -> process_intent() + execute_action()
  actions/__init__.py                   -> SourcedProfileSourcingActions (composicao)
  actions/base.py                       -> BaseAction + decorator require_sourcing_id
  actions/count.py                      -> CountActions
  actions/score.py                      -> ScoreActions
  actions/distribution.py               -> DistributionActions
  actions/analysis.py                   -> AnalysisActions
  actions/search.py                     -> SearchActions
  actions/details.py                    -> DetailActions
  actions/comparison.py                 -> ComparisonActions
  actions/report.py                     -> ReportActions
  actions/search_improvement.py         -> SearchImprovementActions
  actions/insights.py                   -> InsightsActions
  actions/conversational.py             -> ConversationalActions
  actions/feedback.py                   -> FeedbackActions
  prompts.py                            -> System prompt + ACTIONS_USING_AGGREGATED
  prompt_builder/                       -> Geracao dinamica de prompts
  api_client.py                         -> HTTP client para Rails API
  cache.py                              -> StatsManager (aggregated_stats com TTL)
  memory.py                             -> ConversationMemory (restaurada do Rails)
  fairness.py                           -> Guard contra filtros discriminatorios
  template_formatter.py                 -> Formatacao de DomainResponse
  config/domain_settings.py             -> Configuracoes
  dispatcher.py                         -> Consumer RabbitMQ
  tasks.py                              -> Celery tasks
```

---

## Detalhe: process_intent()

**Arquivo:** `domain.py` linhas 381-466

```
Recebe: user_query + context

1. Verifica feedback pendente (dislike)
   -> Se sim, completa o feedback com a razao do usuario

2. Monta system_prompt via SourcedProfileSourcingPrompts
   -> Inclui lista de 35 actions com descricao e exemplos
   -> Inclui aggregated_stats se disponivel

3. Envia para LLM (Gemini):
   - SystemMessage: prompt com actions disponiveis
   - HumanMessage: query do usuario

4. LLM retorna JSON:
   {
     "action_id": "top_candidates",
     "params": {"limit": 5, "skill": "python"},
     "confidence": 0.92
   }

5. Se confidence < 0.5 mas action_id valido -> bump para 0.7
6. Se needs_clarification -> retorna pergunta ao usuario
```

---

## Detalhe: execute_action()

**Arquivo:** `domain.py` linhas 468-552

```
Recebe: action_id + params + context + aggregated_stats

1. Valida action_id (esta na lista de allowed_actions?)

2. Decide se passa aggregated_stats:
   -> 26 actions usam stats (contagens, medias, distribuicoes)
   -> Demais recebem None

3. Mapeia action_id -> handler (33 handlers):
   "count_candidates"              -> self._actions.count_candidates
   "count_by_filter"               -> self._actions.count_by_filter
   "average_score"                 -> self._actions.average_score
   "top_candidates"                -> self._actions.top_candidates
   "analyze_skills"                -> self._actions.analyze_skills
   "location_distribution"         -> self._actions.location_distribution
   "compare_candidates"            -> self._actions.compare_candidates
   "summarize_search"              -> self._actions.summarize_search
   "average_experience"            -> self._actions.average_experience
   "language_distribution"         -> self._actions.language_distribution
   "education_distribution"        -> self._actions.education_distribution
   "gender_distribution"           -> self._actions.gender_distribution
   "average_salary_expectation"    -> self._actions.average_salary_expectation
   "work_model_distribution"       -> self._actions.work_model_distribution
   "diversity_analysis"            -> self._actions.diversity_analysis
   "search_candidates"             -> self._actions.search_candidates
   "filter_by_skill"               -> self._actions.filter_by_skill
   "filter_by_score"               -> self._actions.filter_by_score
   "list_candidates"               -> self._actions.list_candidates
   "list_candidates_by_index"      -> self._actions.list_candidates_by_index
   "show_candidate_details"        -> self._actions.show_candidate_details
   "generate_executive_report"     -> self._actions.generate_executive_report
   "generate_top_candidates_report"-> self._actions.generate_top_candidates_report
   "analyze_search_improvement"    -> self._actions.analyze_search_improvement
   "score_above"                   -> self._actions.score_above
   "common_strengths"              -> self._actions.common_strengths
   "skill_gaps"                    -> self._actions.skill_gaps
   "top_by_experience"             -> self._actions.top_by_experience
   "candidates_to_discard"         -> self._actions.candidates_to_discard
   "needs_screening"               -> self._actions.needs_screening
   "priority_ranking"              -> self._actions.priority_ranking
   "work_model_specific"           -> self._actions.work_model_specific
   "conversational_response"       -> self._actions.conversational_response
   "clear_filters"                 -> self._actions.clear_filters
   "candidate_feedback"            -> self._actions.candidate_feedback

4. Executa: handler(params, context, stats_to_pass)
   -> Retorna DomainResponse
```

---

## Hierarquia do Actions (sistema ativo)

```
SourcedProfileSourcingActions herda de:
+-- FeedbackActions              -> candidate_feedback
+-- ConversationalActions        -> conversational_response
+-- InsightsActions              -> common_strengths, skill_gaps, candidates_to_discard,
|                                   needs_screening, priority_ranking
+-- SearchImprovementActions     -> analyze_search_improvement
+-- ReportActions                -> generate_executive_report, generate_top_candidates_report
+-- ComparisonActions            -> compare_candidates
+-- DetailActions                -> show_candidate_details
+-- SearchActions                -> search_candidates, filter_by_skill, list_candidates, etc.
+-- CountActions                 -> count_candidates, count_by_filter
+-- ScoreActions                 -> average_score, score_above, top_candidates, filter_by_score
+-- DistributionActions          -> location, gender, language, education, salary, work_model
+-- AnalysisActions              -> analyze_skills, diversity_analysis
    |
    +-- Todas herdam de BaseAction
        +-- Prove: get_api_client(), _apply_filter(), _describe_filter()
```

Padrao de cada action:
```python
@require_sourcing_id
def nome_action(self, params, context, aggregated_stats=None) -> DomainResponse:
    # 1. Se tem aggregated_stats -> usa dados cacheados (rapido)
    # 2. Senao -> faz chamada API ao Rails
    # 3. Processa dados
    # 4. Para actions complexas (report, comparison) -> chama LLM
    # 5. Retorna DomainResponse(success, message, data, suggestions)
```

---

## O Sistema Agents/ (existe mas NAO esta conectado)

```
MultiAgentOrchestrator (agents/orchestrator.py)
+-- RouterAgent (agents/router.py)
|   Roteamento: memoria conversacional -> pattern matching -> LLM fallback
|
+-- SearchAgent (agents/search.py)
|   Busca com fairness guard, similar profiles, advanced search
|
+-- AnalyticsAgent (agents/analytics.py)
|   Estatisticas, contagens, distribuicoes
|
+-- DetailAgent (agents/detail.py)
|   Perfil detalhado com analise da IA
|
+-- ComparisonAgent (agents/comparison.py)
|   Comparacao lado a lado + LLM analysis + job matching
|
+-- ReportAgent (agents/report.py)
|   Relatorios executivos com fact-checking e chart data
|
+-- ActionAgent (agents/action.py)
    Converter, adicionar em lista, criar apply, atualizar, remover

Suporte:
+-- ExecutionPlan / AgentTask (agents/planner.py)
|   Multi-step pipelines com dependencias entre tasks
|
+-- BaseAgent (agents/base.py)
    LLM, API client, validacao, fact-checking
```

Diferencas do agents/ vs actions/:
- RouterAgent com memoria conversacional (resolve pronomes, referencias)
- Multi-step pipelines (ex: buscar candidatos -> criar apply em sequencia)
- Fairness guard em mais operacoes
- Fact-checking nas respostas do LLM
- Extracao inteligente de parametros (param_extractor + smart_extractor)
- Cada agent tem get_system_prompt() proprio

---

## Analise de Arquivos: Quem Usa Quem

### Arquivos USADOS em producao

| Arquivo | Importado Por | Funcao |
|---------|---------------|--------|
| `domain.py` | DomainRegistry (decorator) | Ponto de entrada do dominio |
| `actions/__init__.py` | domain.py | Composicao de todos os handlers |
| `actions/base.py` | Todos os actions/*.py | BaseAction + decorators |
| `actions/*.py` (12 arquivos) | actions/__init__.py | Handlers especificos |
| `api_client.py` | domain.py, orchestrator.py, actions/base.py, agents/base.py | HTTP client Rails |
| `api_operations.py` | agents/base.py, actions/feedback.py | Wrappers alto nivel API |
| `cache.py` | domain.py | StatsManager com TTL |
| `memory.py` | DomainOrchestrator (src/domains/orchestrator.py) | Memoria conversacional |
| `prompts.py` | domain.py | System prompt + set ACTIONS_USING_AGGREGATED |
| `prompt_builder/` (5 arquivos) | prompts.py | Geracao dinamica de prompts |
| `fairness.py` | actions/insights.py, agents/{comparison,search,report}.py | Anti-discriminacao |
| `template_formatter.py` | src/domains/workflow.py (linha 223) | Formata DomainResponse |
| `config/domain_settings.py` | 7+ modulos | Configuracoes |
| `dispatcher.py` | __init__.py | Consumer RabbitMQ |
| `tasks.py` | __init__.py, dispatcher.py | Celery tasks |
| `__init__.py` | src/domains/ package | Exports publicos |

### Arquivos usados APENAS pelo sistema agents/ (nao em producao)

| Arquivo | Importado Por | Obs |
|---------|---------------|-----|
| `param_extractor.py` | agents/router.py | So e chamado se agents/ for ativado |
| `smart_extractor.py` | param_extractor.py | Idem |
| `validators.py` | agents/base.py (+ testes) | Idem |
| `fact_checker.py` | agents/base.py (+ testes) | Idem |
| `agents/orchestrator.py` | agents/__init__.py | Exportado mas nunca invocado |
| `agents/router.py` | agents/orchestrator.py | Idem |
| `agents/search.py` | agents/orchestrator.py | Idem |
| `agents/analytics.py` | agents/orchestrator.py | Idem |
| `agents/detail.py` | agents/orchestrator.py | Idem |
| `agents/comparison.py` | agents/orchestrator.py | Idem |
| `agents/report.py` | agents/orchestrator.py | Idem |
| `agents/action.py` | agents/orchestrator.py | Idem |
| `agents/planner.py` | agents/orchestrator.py | Idem |
| `agents/base.py` | Todos os agents/*.py | Idem |

### Arquivo SEM NENHUM import (codigo morto)

| Arquivo | Conteudo | Imports Encontrados |
|---------|----------|---------------------|
| `models.py` | ActionType, SearchParams, CandidateParams, FilterParams, ScoreStats, CandidateCounts, AggregatedStats, ActionIntent | ZERO - nenhum arquivo importa |

**`models.py` pode ser removido com seguranca.** Grep em todo o projeto retorna zero resultados.

---

## Resumo Final

```
EM PRODUCAO:
  domain.py -> actions/ (14 arquivos) -> api_client.py -> Rails API
  Suporte: cache, memory, prompts, prompt_builder, fairness, template_formatter
  Entry points: dispatcher.py (RabbitMQ), tasks.py (Celery)

EXISTE MAS NAO CONECTADO:
  agents/ (10 arquivos) com MultiAgentOrchestrator + 6 agentes
  Suporte exclusivo: param_extractor, smart_extractor, validators, fact_checker

CODIGO MORTO (seguro remover):
  models.py -> zero imports em todo o projeto
```
