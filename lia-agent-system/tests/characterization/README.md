# Characterization Tests — Orchestrator V1 Migration

## Propósito

Estes testes capturam o **comportamento atual de produção** do `Orchestrator` V1 (`app/orchestrator/orchestrator.py`, marcado `LIA-D06: DEPRECATED`).

Durante a migração V1 → V2 (Sprints II-V do plano `ORCHESTRATOR_MIGRATION_MASTER_PLAN.md`), estes testes funcionam como **rede de segurança**: se algum FALHAR, é sinal de regressão — investigar antes de avançar.

## Princípio harness-engineering

`[sensor]` antes de `[guide]` — adicionar testes (feedback) antes de mexer em lógica de orquestração (feedforward). Sem essa rede, qualquer Sprint subsequente é cego.

## Como rodar

```bash
# Apenas characterization tests (rápido):
cd lia-agent-system
pytest tests/characterization/ -v

# Como parte da suite completa:
pytest -v
```

## Cobertura esperada (Sprint I — em construção)

- `test_v1_smoke.py` — Sanidade: V1 instanciável, métodos públicos existem, retornos têm shape esperado
- `test_v1_process_request.py` — 8 fixtures (TODO Sprint I)
- `test_v1_process_request_with_memory.py` — 4 fixtures (TODO)
- `test_v1_execute_plan.py` — 4 fixtures (TODO)
- `test_v1_handle_directly.py` — 6 fixtures LIA-A04 (TODO)
- `test_v1_cv_screening_rubric.py` — 4 fixtures (TODO)
- `test_v1_analytics.py` — 3 fixtures (TODO)
- `test_v1_metrics_cache.py` — 4 fixtures (TODO)
- `test_v1_tool_permissions.py` — 4 fixtures (TODO)
- `test_v1_scope_prompts.py` — 3 fixtures (TODO)
- `test_v1_available_tools.py` — 2 fixtures (TODO)

**Total alvo Sprint I**: 52+ characterization tests

## Por que usar `Orchestrator` V1 deprecated?

Sim, o V1 está marcado `DeprecationWarning`. Os testes silenciam o warning via `pytest.ini` (`filterwarnings = ignore::DeprecationWarning`). Estes tests existem **explicitamente** para preservar comportamento V1 durante a migração — é o ponto desta camada.

Após Sprint V (delete V1), estes testes serão **convertidos** para test V2 ou **removidos** se o comportamento já estiver coberto por `test_main_orchestrator.py`.

## Quando atualizar este arquivo

- Ao adicionar novo characterization test, atualizar a lista acima
- Ao final de cada Sprint, atualizar status (DONE/TODO)
- Após Sprint V, este README é deletado junto com V1

---

**Criado**: 2026-04-26 — Sprint I Tarefa C  
**Owner**: orchestrator migration team  
**Doc mestre**: `Documents/Python/ORCHESTRATOR_MIGRATION_MASTER_PLAN.md`
