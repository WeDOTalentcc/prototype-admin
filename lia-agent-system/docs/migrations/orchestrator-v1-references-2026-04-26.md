# Orchestrator V1 References — Canonical Inventory
## Sprint I — Tarefa A.3: Reconciliação grep × AST

**Date**: 2026-04-26
**Branch**: `feat/orch-migration-sprint-I`
**Sources**:
- `grep-v1-references-2026-04-26.md` — grep textual (incompleto)
- `ast-v1-references-2026-04-26.md` — AST parsing canônico (este é a fonte da verdade)

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Arquivos Python escaneados | 2.559 |
| Arquivos com referência ao V1 | 14 |
| Imports estáticos do V1 | 6 |
| Imports dinâmicos (`importlib.import_module`, `__import__`) | 0 |
| Method calls (`.process_request`, etc.) | 44 |
| Falsos positivos do grep eliminados pelo AST | ~27 (71 grep − 44 AST = 27 strings em comentários/docstrings) |

**Conclusão**: AST parsing eliminou ~38% de ruído do grep. Lista canônica abaixo.

---

## 1. Importers Estáticos (6 ocorrências, 6 arquivos)

### Produção (3 arquivos):
| Arquivo:linha | Tipo | Decisão Sprint |
|--------------|------|----------------|
| `app/orchestrator/__init__.py:4` | `from .orchestrator import Orchestrator` (re-export) | V — remover no delete |
| `app/orchestrator/registry.py:14` | `from app.orchestrator.orchestrator import Orchestrator` (typing) | V — atualizar tipo |
| `app/api/orchestrator_routes.py:16` | `from app.orchestrator import Orchestrator` (via parent) | IV — substituir |

### Testes (3 arquivos):
| Arquivo:linha | Tipo | Decisão Sprint |
|--------------|------|----------------|
| `tests/integration/test_orchestrator_consolidation.py:246` | direct import | I — manter (characterization) |
| `tests/test_autonomous_react_agent.py:1259, 1326` | direct imports | I — auditar/atualizar |
| `tests/unit/test_anti_sycophancy_prompts.py:43` | `from ... import _LIA_SYSTEM_PROMPT` | Não toca V1 class — apenas constante |

---

## 2. Factory Calls (V1, não V2) — análise dos grep results

| Arquivo:linha | Padrão | Categoria |
|--------------|--------|-----------|
| `app/api/orchestrator_routes.py:97, 123, 161, 173` | `def get_orchestrator()`, `Depends(get_orchestrator)` | Produção V1 — Sprint IV |
| `app/api/v1/lia_assistant/insights.py:382, 387, 400` | `from ... import get_orchestrator; orchestrator.process_request(...)` | Produção V1 — Sprint IV |
| `app/orchestrator/main_orchestrator.py:1529, 1530` | V2 importa get_orchestrator (V1) — circular dep | Sprint III |
| `app/api/v1/onboarding.py:_get_orchestrator` | Factory específica do Onboarding (NÃO V1) | Não toca |
| `app/api/v1/whatsapp_webhook.py:_get_orchestrator` | Factory específica do WhatsApp (NÃO V1) | Não toca |
| `app/domains/communication/services/teams_orchestrator_bridge.py:71, 89` | usa `get_orchestrator_instance()` do registry | Sprint IV |
| `app/orchestrator/registry.py:22` | `def get_orchestrator_instance()` — pertence ao registry | Sprint V — atualizar |
| `app/domains/job_management/prompts/job_wizard.py:322` | `def get_orchestrator_prompt(...)` | **FALSO POSITIVO** — não relacionado |
| `app/prompts/__init__.py:35, 58` | re-export `get_orchestrator_prompt` | **FALSO POSITIVO** |

---

## 3. Method Calls (44 ocorrências canônicas)

### Produção (5 callers):
| Arquivo:linha | Método | Risco |
|--------------|--------|-------|
| `app/api/orchestrator_routes.py:136` | `.process_request` | 🔴 ALTO (endpoint público) |
| `app/api/v1/chat.py:139` | `.process_request` | 🟡 MÉDIO (legacy fallback) |
| `app/api/v1/lia_assistant/insights.py:400` | `.process_request` | 🟡 MÉDIO (Phase 3 fallback) |
| `app/domains/communication/services/teams_orchestrator_bridge.py:92` | `.process_request` | 🟡 MÉDIO (Teams integration) |
| `app/orchestrator/main_orchestrator.py:1247` | `.process_request` | 🔴 V2 → V1 delegation |

### V1 internal calls (4 ocorrências dentro do próprio orchestrator.py):
| Arquivo:linha | Método |
|--------------|--------|
| `app/orchestrator/orchestrator.py:270, 304` | `._handle_directly` |
| `app/orchestrator/orchestrator.py:347` | `.process_request` (em `process_request_with_memory`) |
| `app/orchestrator/orchestrator.py:434` | `._handle_cv_screening_with_rubric` |

### Testes (35 ocorrências em 8 arquivos):
- `tests/integration/test_orchestrator_consolidation.py` — 2 ocorrências
- `tests/test_agent_regression.py` — 7 ocorrências
- `tests/test_autonomous_react_agent.py` — 1 ocorrência
- `tests/unit/test_main_orchestrator.py` — 16 ocorrências
- `tests/unit/test_main_orchestrator_extended.py` — 7 ocorrências
- `tests/unit/test_sprint_i_foundations.py` — 1 ocorrência (NÃO É NOSSO Sprint I — outro projeto, mesma sigla)

---

## 4. Achado Crítico Novo

**`teams_orchestrator_bridge.py`** (Microsoft Teams integration) usa V1 via `get_orchestrator_instance()` — esse caller NÃO estava no plano original e precisa ser adicionado ao Sprint IV.

**Atualização ao MASTER_PLAN.md necessária**: incluir Teams bridge na lista de "callers diretos do V1" — passa de 3 para 4 callers.

---

## 5. Importação Dinâmica

AST parser confirmou: **zero `importlib.import_module("app.orchestrator.orchestrator")` ou `__import__()` na codebase**. Ao contrário do FE (Sprint A cleanup canônico que teve dynamic imports), aqui a árvore Python é estática — grep cobriria suficientemente se filtrasse comments/docstrings.

---

## 6. Próximos Passos

- Sprint I — continuar com Tarefa B (baseline metrics) e Tarefa C (characterization tests)
- Atualizar `ORCHESTRATOR_MIGRATION_MASTER_PLAN.md` Anexo G com:
  - 4 callers (não 3) — adicionar Teams bridge
  - 14 arquivos com referência V1 (não estimado anteriormente)
- Atualizar `MIGRATION_REGRESSION_BASELINE.md` com a lista canônica acima
