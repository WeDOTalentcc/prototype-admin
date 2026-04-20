# STATUS — `app/domains/pipeline`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Pipeline / Kanban.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~4.358 (Python) em `domain.py`, `agents/`, `tools/`,
  `repositories/`, `models/`, `config/capabilities.yaml`.
- **`@register_domain`:** ✅ **SIM** — `domain.py` registra a classe
  `PipelineTransitionDomain` com `domain_id = "pipeline_transition"`. Por
  isso o auditor antigo achava que o dir `pipeline/` era "não-registrado":
  ele comparava nomes de dir contra IDs de domain literalmente, sem
  inspecionar `__module__` da classe registrada. Isto foi corrigido nesta
  task — `scripts/audit_chat_capabilities.py` agora deriva os dirs
  registrados a partir do `__module__` das classes em `_DOMAIN_REGISTRY`.
- **Agentes registrados (alias):** `kanban_search`, `kanban_insight`,
  `kanban_action`, `pipeline_context`, `pipeline_decision`,
  `pipeline_action`.
- **Importadores externos:** `app/orchestrator/cascaded_router.py`,
  `tests/integration/test_pipeline_transition_flow.py`,
  `tests/test_domains/test_pipeline_transition_agent.py` (≥12 referências),
  `tests/unit/test_pipeline_tool_registry_cov.py` (≥14 referências),
  `tests/unit/test_z1_pipeline_decomposition.py` (≥15 referências),
  `app/domains/cv_screening/agents/pipeline_react_agent.py`,
  `app/api/v1/pipeline*` (5 endpoints).
- **Testes existentes:** ✅ `test_pipeline_transition_agent.py`,
  `test_pipeline_tool_registry_cov.py`, `test_z1_pipeline_decomposition.py`,
  `test_pipeline_transition_flow.py`.

## Classificação
**Categoria 2 — Já registrado no chat (auditor corrigido).** É o
`pipeline_transition` domain do relatório, com 5 actions intent-routed.

## Plano de evolução
- Manter registro como `pipeline_transition`. Não renomear o dir para
  `pipeline_transition` (quebraria todos os imports atuais sem ganho real).
- Próximo passo natural: aumentar cobertura de `execute_action` (já tem
  testes de agente; falta teste do pipeline action→tool→handler).
- Considerar adicionar tools explícitas (hoje 0 tools, 5 actions) para
  permitir chamadas via `_ACTION_TOOL_MAP` — opcional.

## Regra anti-deleção
🛑 **NÃO DELETAR.** Este dir é o `pipeline_transition` chat domain ATIVO,
ponto de entrada para 6 agent-types do roteador (kanban_*, pipeline_*).
Deleção quebra movimentação de candidatos no Kanban.

## Cobertura mínima de testes exigida
- `tests/test_domains/test_pipeline_transition_agent.py` deve passar 100%.
- Nova action exige: (a) registro em `get_allowed_actions`, (b) handler com
  `@tool_handler` ou tenant check manual, (c) teste cobrindo caminho feliz.
