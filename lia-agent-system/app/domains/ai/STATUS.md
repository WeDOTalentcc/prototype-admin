# STATUS — `app/domains/ai`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Plataforma — Time Core LLM / Infraestrutura de Inteligência.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~9.002 (Python) em 22 services + repositórios.
- **Conteúdo:** infraestrutura LLM canônica — `llm.py`, `intent_classifier.py`,
  `enhanced_intent_classifier.py`, `rag_service.py`, `rag_pipeline_service.py`,
  `hybrid_search_service.py`, `embedding_cache_service.py`,
  `response_cache_service.py`, `tool_executor_service.py`,
  `agent_quality_evaluator.py`, `prompt_version_registry.py`,
  `structured_output.py`, `multimodal_service.py`,
  `ragas_evaluation_service.py`, `knowledge_base_service.py`, etc.
- **Importadores externos identificados (>25):** `app/main.py`,
  `app/orchestrator/main_orchestrator.py`, `cascaded_router.py`,
  `agentic_loop.py`, `llm_cascade.py`, `app/api/v1/chat.py`,
  `app/api/v1/lia_assistant/*`, `app/api/wsi_endpoints.py`,
  `app/api/v1/llm_config.py`, `app/api/v1/ai_consumption.py`,
  `app/api/v1/system_health.py`, `app/api/v1/rag_search.py`,
  `app/domains/cv_screening/services/*`,
  `app/domains/job_management/services/*`,
  `app/domains/sourcing/services/*`,
  `app/domains/analytics/services/*`,
  `app/domains/recruitment/*`, `app/shared/services/*` (re-exports),
  `libs/agents-core/lia_agents_core/nodes.py`, e múltiplos testes.
- **Testes existentes:** `tests/test_ai_consumption_outbox.py` (cobertura
  parcial — só billing/outbox). Cobertura LLM core vem indireta via testes
  de domínios consumidores (cv_screening, sourcing, etc.).
- **`@register_domain`:** ❌ Nenhum (correto — é infra, não domínio de chat).
- **Endpoints REST diretos:** nenhum próprio; é dependência transversal.

## Classificação
**Categoria 1 — Infra LLM Core.** NÃO é domínio de chat candidato. É a
biblioteca interna que fornece LLM, RAG, cache, classificadores de intent e
executor de tools para todos os 18 domínios registrados.

## Plano de evolução
- Manter como pacote-biblioteca. Não promover a `@register_domain`.
- Próximas tarefas previsíveis (já listadas em outros backlogs):
  P0-2 (warning quando agent-type retorna desconhecido) toca `intent_classifier`;
  P1-5 (validação de schema de params) toca `tool_executor_service`.
- Considerar mover para `app/shared/ai/` em refactor futuro para deixar a
  intenção arquitetural óbvia. Não fazer agora — quebraria >25 importadores.

## Regra anti-deleção
🛑 **NÃO DELETAR / NÃO MOVER sem RFC.** Deletar qualquer arquivo deste dir
quebra todos os 18 domínios registrados. O caminho `app.domains.ai.*` é
endereço público estável da infra LLM.

## Cobertura mínima de testes exigida
- Cada novo service em `app/domains/ai/` deve ter teste unitário cobrindo
  pelo menos o caminho feliz e um modo de falha (timeout, resposta inválida
  do LLM, cache miss).
- Mudanças em `llm.py`, `tool_executor_service.py` ou
  `intent_classifier.py` exigem rodar `tests/llm_eval/` localmente antes de
  merge.
