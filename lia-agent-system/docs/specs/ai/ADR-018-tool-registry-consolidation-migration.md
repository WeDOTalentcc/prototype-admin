# ADR-018: Plano de consolidação operacional do tool registry (Task #382)

**Status:** Accepted
**Data:** 2026-04-20
**Relacionado:** ADR-015 (S7.1–S7.3), ADR-016 (S7.4 — superfície canônica), ADR-017 (WSI), Task #350 (não-execução), Task #351 (ADR-016), Task #353/Task #354 (S7.5), Task #382 (este ADR)

---

## Contexto

ADR-016 já fixou o **alvo arquitetural**: `@tool_handler` é a superfície de autoria, `app/tools/registry.py` é o roteador de execução, `tool_permissions.yaml` cuida só de governança de escopo (com config de LLM por tenant migrada para `tenant_llm_configs`). O guard S7.5 (Task #354, `scripts/check_tool_authoring_surface.py`) já bloqueia novos `tool_registry.register(` fora do entry-point canônico.

O que ADR-016 deixou em aberto, e que motivou a Task #382, é o **plano operacional** de como sair do estado atual sem quebrar nada:

1. O `ALLOW_LIST` de S7.5 ainda tem **11 arquivos** grandfathered chamando `tool_registry.register(...)` à mão (cv_screening/cv_upload, cv_screening/candidate, communication, job_management ×3, recruiter_assistant/pipeline, sourcing/query, talent_intelligence/registry, analytics_query_tools/registry, shared/tools/export). A Task #350 propôs apagá-los; a verificação mostrou que estão vivos. Apagar quebra o orchestrator/`ActionExecutor`.
2. Existem **30+ módulos `*_tool_registry.py`** em `app/domains/*/agents/` que já usam `@tool_handler` mas devolvem `ToolDefinition` do `lia_agents_core.react_loop` para serem consumidos pelo ReAct loop do agente, **sem passar pelo `tool_registry` global**. Esses arquivos coexistem com os 11 do ALLOW_LIST e a confusão "qual é o registry?" é a fonte de várias propostas erradas (incluindo a Task #350).
3. `initialize_tools()` em `app/tools/__init__.py` chama 14 `register_*_tools()` à mão. Não há autodiscovery.
4. `scope_config.py` deriva 9 constantes de módulo (`FUNNEL_QUERY_TOOLS`, etc.) lendo a YAML em **import-time**. Qualquer mudança na YAML após import é invisível para esses globals — o que torna invalidate_cache() falsamente confiável.
5. `_load_from_permissions` em `llm_factory.py` foi renomeado para `_resolve_provider_config` e a config-por-tenant migrou para `tenant_llm_configs`, mas a YAML ainda aceita `tenants:` com `llm_provider`/`llm_fallback_order` (apenas avisa via warning). Existe data residual a remover.

A Task #382 trata isso como **migração arquitetural multi-arquivo, não delete**. Este ADR define a sequência exata, o critério de "feito", e os testes de fitness que provam que a migração concluiu — testes que **não devem rodar antes** da migração porque o estado intermediário ainda é o atual.

## Decisão

Manter integralmente o alvo do ADR-016. Este ADR adiciona apenas o **plano de execução** e o **gate de aceitação**.

### Princípio orientador da sequência

> Cada passo precisa deixar o sistema **bootável e atendendo requests** sem perder nenhuma tool. A migração é por arquivo, não por classe/função, e cada arquivo migrado atualiza simultaneamente: (a) o conteúdo do arquivo, (b) `initialize_tools()`, (c) o ALLOW_LIST de S7.5.

### Forma canônica pós-migração de cada arquivo do ALLOW_LIST

Para um módulo legado `app/domains/<dom>/tools/<x>.py` (ou `app/shared/tools/<x>.py`) que hoje chama `tool_registry.register(ToolDefinition(...))`:

1. Cada handler vira uma função decorada com `@tool_handler(domain=<dom>, require_company=True[, module=...])`. Funções já autoradas assim ficam como estão.
2. O arquivo passa a expor `get_<x>_tools() -> list[ToolDefinition]` que devolve uma lista de `app.tools.registry.ToolDefinition` montada a partir dessas funções (o ToolDefinition mantém apenas `name`, `description`, `parameters_schema`, `handler`, `allowed_agents` — **não** é responsável por tenant check, isso já está dentro de `@tool_handler`).
3. O arquivo deixa de importar `tool_registry`. Não chama mais `register(...)` em nenhum lugar.
4. `app/tools/__init__.py:initialize_tools()` ganha:
   ```python
   for _td in get_<x>_tools():
       tool_registry.register(_td)
   ```
   Esse é o único lugar em todo o código fora de `app/tools/registry.py` autorizado a chamar `tool_registry.register`.
5. A entrada correspondente em `scripts/check_tool_authoring_surface.py:ALLOW_LIST` é **removida** no mesmo commit.

O padrão já está aplicado em `app/domains/cv_screening/tools/cv_match_tool.py` (Task #417). Os 11 arquivos restantes seguem o mesmo molde.

### Sequência (10 etapas, cada uma é uma task futura)

| # | Escopo | Deps | Risco | Notas |
|---|---|---|---|---|
| **M1** | Extrair `get_export_tools()` em `app/shared/tools/export_tools.py`; remover do ALLOW_LIST. | — | Baixo (poucas tools, sem state). | Use-se de "smoke test" do molde. |
| **M2** | `app/domains/sourcing/tools/query_tools.py` → `get_sourcing_query_tools()`. | M1 | Baixo. | |
| **M3** | `app/domains/communication/tools/communication_tools.py` → `get_communication_tools()`. | M1 | Médio (tools com side-effect: send_email, send_whatsapp, send_bulk_email — preservar HITL via `restricted_tools`). | |
| **M4** | `app/domains/recruiter_assistant/tools/pipeline_tools.py` → `get_pipeline_tools()`. | M1 | Médio (update_candidate_stage, bulk_update_candidates_stage têm HITL). | |
| **M5** | `app/domains/cv_screening/tools/candidate_tools.py` → `get_candidate_tools()`. | M1 | Médio. | |
| **M6** | `app/domains/cv_screening/tools/cv_upload_tool.py` → `get_cv_upload_tools()`. | M1 | Baixo. | |
| **M7** | `app/domains/job_management/tools/job_tools.py` + `job_wizard_tools.py` + `query_tools.py` → 3 `get_*_tools()` independentes. | M1 | Médio (3 arquivos, mais alto throughput de chat). | Migrar em commits separados. |
| **M8** | `app/domains/talent_intelligence/tools/registry.py` → `get_talent_intelligence_tools()`. Renomear o arquivo para `tools_registry.py` para liberar o nome `registry` da confusão. | M1 | Baixo. | |
| **M9** | `app/domains/analytics/tools/analytics_query_tools/registry.py` → idem. Mesma renomeação. | M1 | Baixo. | |
| **M10** | Após M1-M9: `ALLOW_LIST` em `scripts/check_tool_authoring_surface.py` está vazio. **Remover o `ALLOW_LIST` do guard inteiro** e adicionar gate explícito "ALLOW_LIST must be empty". | M1-M9 | Nenhum (apenas remoção de tech debt). | Marca o ponto de não-retorno. |

Após M10, M11–M13 são polimento independente (não bloqueiam a consolidação principal):

| # | Escopo | Deps | Risco |
|---|---|---|---|
| **M11** | Em `scope_config.py`: remover os 9 globals derivados em import-time (`FUNNEL_QUERY_TOOLS`, etc.) e os 5 itens em `SCOPE_TOOL_MAPPING` que dependem deles. Substituir cada uso interno por chamada direta a `get_tools_for_scope(scope, type, tenant_id=tid)`. Manter `SCOPE_DESCRIPTIONS` e `SCOPE_INTENT_MAPPING` (são metadata estável, não data). | — | Médio (alguns testes podem importar os globals — auditar antes). |
| **M12** | Limpar `tool_permissions.yaml`: remover do bloco `tenants:` quaisquer chaves `llm_provider` / `llm_fallback_order` (já são silenciosamente ignoradas pelo loader desde Task #353). Validar que a tabela `tenant_llm_configs` cobre 100% dos tenants que tinham essas chaves (script one-shot de migração + diff). | — | Baixo (nada lê isso em runtime). |
| **M13** | Atualizar `lia-agent-system/README.md` (seção "Adicionando uma tool nova") com o passo-a-passo do molde acima e um link para este ADR + ADR-016. Cobre o item 6 do plano original do ADR-016. | M10 | Nenhum. |

### Itens explicitamente fora deste plano

- **Substituir `ToolRegistry` por `dict[str, ToolDefinition]`.** ADR-016 já decidiu não fazer; reafirmado.
- **Mexer no `ActionExecutor` / `agentic_loop` / orchestrator.** Eles consultam `tool_registry.get_tool(name)`; isso continua válido. A migração é puramente da camada de autoria.
- **Tocar nos 30+ `*_tool_registry.py` de `app/domains/*/agents/`.** Esses já estão na forma canônica (`@tool_handler` + `ToolDefinition` do `lia_agents_core`); nenhum chama `tool_registry.register`. Eles servem o ReAct loop diretamente, não passam pelo executor central — e isso é por design (são tools internas a um agente específico, não tools do chat global). Quem precisar promover uma delas para o `tool_registry` global o faz **adicionando** um `get_*_tools()` agregado em `initialize_tools()`, sem mexer no arquivo de origem.
- **Migrar para um sistema de autodiscovery (entry points / decorator-side-effect).** Ganho marginal vs. risco de boot silencioso (uma tool não-importada simplesmente não existe). `initialize_tools()` explícito ganha um `len(tool_registry.list_tools())` previsível.

## Acceptance criteria

A consolidação está concluída quando **todas** as condições abaixo são verdadeiras simultaneamente:

1. **A1 — ALLOW_LIST vazio:** `scripts/check_tool_authoring_surface.py` reporta `len(ALLOW_LIST) == 0` e o guard ainda passa em CI.
2. **A2 — Single-source de autoria:** `git grep -nE '\btool_registry\.register\s*\(' app/` devolve **exatamente uma linha**, em `app/tools/__init__.py` (loop `for _td in get_*_tools(): tool_registry.register(_td)`).
3. **A3 — Inventário preservado:** o número de tools registradas após `initialize_tools()` é `>=` o número pré-migração. Snapshot dos nomes em `tests/fixtures/tool_registry_snapshot.txt` cobre o pré e pós migração; o teste falha se nomes desaparecem.
4. **A4 — `scope_config` sem globals em import-time:** `python -c "import app.tools.scope_config as s; assert not hasattr(s, 'FUNNEL_QUERY_TOOLS')"` passa (M11).
5. **A5 — YAML sem config-por-tenant LLM:** o teste lê `tool_permissions.yaml` e assegura que nenhuma chave sob `tenants:` contém `llm_provider` ou `llm_fallback_order` (M12).
6. **A6 — `_resolve_provider_config` sem fallback YAML para per-tenant:** mock que injeta `tenants: {acme: {llm_provider: foo}}` no YAML não muda o provider efetivo de `acme` (M12 confirma fim do path).
7. **A7 — README atualizado:** README.md tem uma seção "Adicionando uma tool nova" com link para ADR-016 e ADR-018 (M13).
8. **A8 — Boot estável:** `pytest tests/test_tool_registry_boot.py` (novo, ver §Canary fitness tests) verifica que `initialize_tools()` executa sem warnings de "Tool 'X' already registered, overwriting".

## Canary fitness tests (criar **junto com** M10)

Estes testes são parte do gate, não da migração. Eles **devem falhar hoje** se rodarem isoladamente — porque o estado atual ainda tem ALLOW_LIST não-vazio. Por isso são marcados `@pytest.mark.consolidation` e excluídos do `pytest` default até M10.

### `tests/consolidation/test_authoring_surface_clean.py`

```python
import pytest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.consolidation
def test_allow_list_is_empty():
    """A1 — guard S7.5 has no grandfathered files left."""
    from scripts.check_tool_authoring_surface import ALLOW_LIST
    assert ALLOW_LIST == set(), (
        f"ALLOW_LIST still has {len(ALLOW_LIST)} entries: {sorted(ALLOW_LIST)}. "
        "Each remaining entry must be migrated to get_<x>_tools() + "
        "initialize_tools() aggregation per ADR-018 §M1-M9."
    )

@pytest.mark.consolidation
def test_single_register_call_site():
    """A2 — only initialize_tools() may call tool_registry.register(...)."""
    pattern = re.compile(r"\btool_registry\.register\s*\(")
    offenders: list[str] = []
    for py in (ROOT / "app").rglob("*.py"):
        rel = str(py.relative_to(ROOT))
        if rel in {"app/tools/__init__.py", "app/tools/registry.py"}:
            continue
        if any(p in py.parts for p in ("__pycache__", "tests")):
            continue
        if pattern.search(py.read_text(encoding="utf-8")):
            offenders.append(rel)
    assert offenders == [], (
        f"Found tool_registry.register(...) outside the canonical entry "
        f"point in: {offenders}"
    )
```

### `tests/consolidation/test_tool_inventory_snapshot.py`

```python
import pytest
from pathlib import Path

SNAPSHOT = Path(__file__).parent / "fixtures" / "tool_registry_snapshot.txt"

@pytest.mark.consolidation
def test_no_tool_disappeared_in_consolidation():
    """A3 — the consolidation must not drop any tool name."""
    from app.tools import initialize_tools, tool_registry
    initialize_tools()
    current = set(tool_registry.list_tools())
    expected = {l.strip() for l in SNAPSHOT.read_text().splitlines() if l.strip()}
    missing = expected - current
    assert not missing, f"Tools dropped during consolidation: {sorted(missing)}"
```

`tests/consolidation/fixtures/tool_registry_snapshot.txt` é gerado **antes** de iniciar M1 (rodar o sistema atual e dumpar `tool_registry.list_tools()`). Esse arquivo é o congelamento de inventário que prova que nenhum tool sumiu.

### `tests/consolidation/test_scope_config_no_import_globals.py`

```python
import pytest

@pytest.mark.consolidation
def test_scope_config_has_no_import_time_globals():
    """A4 — scope_config does not freeze YAML at import time anymore."""
    import app.tools.scope_config as s
    forbidden = (
        "FUNNEL_QUERY_TOOLS", "FUNNEL_ACTION_TOOLS",
        "VACANCY_QUERY_TOOLS", "VACANCY_ACTION_TOOLS",
        "IN_JOB_QUERY_TOOLS", "IN_JOB_ACTION_TOOLS",
        "GLOBAL_TOOLS",
        "UNIVERSAL_QUERY_TOOLS", "UNIVERSAL_ACTION_TOOLS",
    )
    leaked = [name for name in forbidden if hasattr(s, name)]
    assert leaked == [], (
        f"scope_config still exposes import-time YAML snapshots: {leaked}. "
        "Use get_tools_for_scope(scope, type, tenant_id=...) instead."
    )
```

### `tests/consolidation/test_yaml_no_per_tenant_llm_config.py`

```python
import pytest, yaml
from pathlib import Path

YAML = Path(__file__).resolve().parents[2] / "app" / "tools" / "tool_permissions.yaml"

@pytest.mark.consolidation
def test_no_per_tenant_llm_provider_in_yaml():
    """A5 — per-tenant LLM config lives in tenant_llm_configs, not YAML."""
    raw = yaml.safe_load(YAML.read_text(encoding="utf-8")) or {}
    tenants = raw.get("tenants", {}) or {}
    offenders = {
        tid: [k for k in cfg.keys() if k in {"llm_provider", "llm_fallback_order"}]
        for tid, cfg in tenants.items()
        if any(k in cfg for k in ("llm_provider", "llm_fallback_order"))
    }
    assert not offenders, (
        f"Tenants still carry LLM config in YAML: {offenders}. "
        "Migrate to tenant_llm_configs (see Task #353)."
    )
```

### `tests/consolidation/test_boot_stable.py`

```python
import logging, pytest

@pytest.mark.consolidation
def test_initialize_tools_no_overwrite_warnings(caplog):
    """A8 — no tool name is registered twice."""
    from app.tools import initialize_tools, tool_registry
    tool_registry.clear()
    with caplog.at_level(logging.WARNING, logger="ToolRegistry"):
        initialize_tools()
    overwrites = [r for r in caplog.records if "already registered" in r.getMessage()]
    assert overwrites == [], (
        f"Duplicate tool registrations: "
        f"{[r.getMessage() for r in overwrites]}"
    )
```

### Wiring

- Marcador `consolidation` é registrado em `pyproject.toml` ou `pytest.ini`. Default run **exclui** `-m consolidation`.
- CI ganha um job opcional `consolidation-gate` que roda `pytest -m consolidation`. Vira required check no PR de M10.

## Não-decisões (deixadas em aberto)

- **Mover `app/tools/scope_config.py` para `app/tools/permissions/`** para refletir que vira só uma camada fina sobre o loader. Provável, mas não escopo desta migração.
- **Substituir o snapshot `.txt` por um asdict()/JSON estruturado.** Provavelmente sim quando houver +1 caso de teste de inventário; hoje overkill.
- **Carregar tools dos `*_tool_registry.py` de domínios também no `tool_registry` global por autodiscovery.** Esse é um plano separado ("unificar registry de chat global e ReAct dos agentes") que merece seu próprio ADR — não é o que esta task pediu, e ADR-016 explicitamente preferiu manter as duas superfícies separadas enquanto agentes ReAct têm tool sets curados.
- **Schema validation (jsonschema/pydantic) para `tool_permissions.yaml`.** Recomendado em ADR-016, segue em aberto.
