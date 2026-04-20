# STATUS — `app/domains/autonomous`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Plataforma — Time Orchestrator / Roteador Cascateado.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~2.078 (Python).
- **Conteúdo:** `agents/autonomous_react_agent.py` (Tier 6 do
  `CascadedRouter`) e `agents/autonomous_tool_registry.py` (registro de
  tools cross-domain consumido pelo agente ReAct).
- **Importadores externos:** `app/orchestrator/cascaded_router.py` (Tier 6),
  `tests/test_autonomous_react_agent.py` (≥36 referências),
  `tests/llm_eval/test_agent_reasoning_eval.py`,
  `tests/security/test_red_team_lgpd.py`,
  `tests/e2e/test_alpha1_scenario.py`,
  `tests/contract/test_agent_interface_contract.py`.
- **Testes existentes:** `tests/test_autonomous_react_agent.py` (36 casos,
  cobre fallback final do roteador). ✅
- **`@register_domain`:** ❌ Nenhum (correto — é agente especial, não
  domínio de chat com actions/tools próprias).
- **Endpoints REST diretos:** nenhum.

## Classificação
**Categoria 3 — Agente especial do roteador.** É o Tier 6 do
`CascadedRouter`: roda quando nenhum domínio específico cobre a query e
antes do fallback de clarificação. Não tem chat domain próprio porque opera
sobre o registry inteiro via `autonomous_tool_registry`.

## Plano de evolução
- Manter como agente Tier 6.
- Possível evolução: expor métricas de hit-rate (com que frequência o Tier 6
  é acionado e quais domínios ele acaba consultando) para guiar registro de
  novos domínios específicos.
- NÃO promover a `@register_domain` — isso o transformaria em concorrente
  dos domínios reais e quebraria a semântica de fallback.

## Regra anti-deleção
🛑 **NÃO DELETAR.** Deletar qualquer arquivo deste dir desativa o fallback
final do roteador antes da clarificação ao usuário. Queries cross-domain
passariam direto para "não entendi", degradando a UX do chat.

## Cobertura mínima de testes exigida
- `tests/test_autonomous_react_agent.py` deve continuar passando 100%.
- Toda nova ferramenta cross-domain registrada em
  `autonomous_tool_registry.py` precisa de teste cobrindo (a) tenant
  isolation e (b) caminho de erro quando o domínio alvo está offline.
