# STATUS — `app/domains/policy`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Policy Engine / Compliance.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~2.486 (Python) em `agents/`, `services/`,
  `repositories/`.
- **Conteúdo:**
  - `agents/agent.py`, `tool_registry.py`, `system_prompt.py`,
    `stage_context.py` — agente de policy reasoning.
  - `services/policy_engine_service.py` — engine de avaliação de regras.
  - `repositories/policy_repository.py`, `global_policy_repository.py`.
- **Importadores externos:** `app/shared/services/policy_engine_service.py`
  (re-export), `app/agents/policy_setup_agent.py`,
  `app/api/v1/policy_engine.py` (17 endpoints), `app/api/v1/policies.py`,
  `app/api/v1/global_policies.py`, `tests/test_hiring_policy_e2e.py`
  (≥4 referências), `tests/test_domains/test_policy_setup_agent_compliance.py`.
- **Testes existentes:** ✅ `test_policy_react_agent.py`,
  `test_policy_setup_agent_compliance.py`, `test_policy_engine_alpha1.py`,
  `test_policy_automation_contracts.py`.
- **`@register_domain`:** ❌ não registrado. Mas existe um chat domain
  separado `hiring_policy` (em `app/domains/hiring_policy/`) que cobre o
  caso de uso de configuração via chat. Este `policy/` é o engine + agente
  de execução, distinto do wizard de configuração.

## Classificação
**Categoria 4 — Feature REST candidata a chat domain (com nuance).** Já tem
agente, services e endpoints REST. Promoção a `@register_domain` exige
desambiguar a fronteira com o `hiring_policy` chat domain existente
(provavelmente: `hiring_policy` = configurar; `policy` = aplicar/avaliar).

## Plano de evolução
1. Documentar a separação `hiring_policy` vs `policy` em `replit.md` ou em
   `docs/MAPA_CAMADA_INTELIGENCIA.md`.
2. Decidir: (a) consolidar em `hiring_policy` adicionando actions de
   avaliação, OU (b) criar `policy_engine` chat domain registrado.
3. Manter testes existentes como gate antes de qualquer refactor.

## Regra anti-deleção
🛑 **NÃO DELETAR.** Endpoints `policy_engine.py`, `policies.py`,
`global_policies.py` dependem deste dir. Agente é referenciado por
`app/agents/policy_setup_agent.py`.

## Cobertura mínima de testes exigida
- Manter passes em todos os 4 testes listados acima.
- Toda mudança em `policy_engine_service.py` exige teste cobrindo pelo
  menos um cenário de regra que aprova e um que bloqueia.
