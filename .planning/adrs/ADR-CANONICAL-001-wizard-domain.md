# ADR-CANONICAL-001 — Wizard de criação de vaga: caminho canônico único

**Data:** 2026-05-10
**Status:** Decisão registrada (rollout faseado)
**Contexto:** PLAN_FIX_wizard_memory_loss · Auditoria 2026-05-10 · Onda 4.D1

## Contexto

Auditoria 2026-05-10 (`DIAGNOSTICO_FINAL_wizard_memory_loss.md` §P0-D)
identificou **três paths paralelos** que implementam o wizard de criação
de vaga, todos invocados do mesmo endpoint WebSocket `agent_chat_ws.py`:

| Path | Domain | Quando é invocado |
|---|---|---|
| `JobCreationGraph` em `app/domains/job_creation/graph.py` | `job_creation/` | **Canônico** — `agent_chat_ws.py:1266+1341` via `graph_module.job_creation_graph.stream_invoke` |
| `WizardSessionService` em `app/domains/job_creation/services/wizard_session_service.py` | `job_creation/` | **Canônico** — wrapper de `JobCreationGraph` para o WS path principal (`agent_chat_ws.py:909-934`) |
| `JobWizardGraph` em `app/domains/job_management/agents/job_wizard_graph.py` | `job_management/` | **Legacy** — apenas em HITL resume path (`agent_chat_ws.py:558-561`) |

Adicionalmente, `app/domains/job_management/services/wizard_step_service/`
contém helpers que duplicam responsabilidades do canonical
`WizardSessionService`.

A coexistência desses paths viola "single source of truth": state escrito
num path pode não estar visível no outro, e o LLM pode receber prompts
diferentes para a mesma conversa dependendo de qual handler tratou o turno.

## Decisão

**O caminho canônico único do wizard de criação de vaga é o domain
`app/domains/job_creation/`**, com a seguinte responsabilidade:

- **`WizardSessionService`** (em `services/`) é a **entrada canônica** invocada
  pelo handler WS. Encapsula derivação de thread_id, leitura/escrita de state
  via `JobCreationGraph`, e validação de multi-tenancy.
- **`JobCreationGraph`** (em `graph.py`) é o **LangGraph state machine**
  compilado com `PostgresSaver+ConnectionPool` (canonical desde Onda 1).
- **Todos os tools, prompts e schemas** do wizard de vaga consolidam em
  `app/domains/job_creation/`.

**Path `app/domains/job_management/agents/job_wizard_graph.py` está deprecated**:
- Continua funcionando para HITL resume em `agent_chat_ws.py:558-561`
  durante o período de transição.
- Marker `# CANONICAL-EXEMPT: legacy HITL resume — migration tracked
  by ADR-CANONICAL-001` no header.
- Sensor `scripts/check_no_duplicate_wizard_domain.py` (Onda 4.D4)
  retorna 0 violations com este marker presente.

## Fases de migração

| Fase | Escopo | Status |
|---|---|---|
| **0** (Onda 4.D1, 2026-05-10) | Banner DEPRECATED + EXEMPT marker em arquivos legacy. Sensor canonical BLOCKING. ADR registrada. | Pronto |
| **1** (próximo sprint) | Migrar HITL resume em `agent_chat_ws.py:558-561` de `JobWizardGraph` para `WizardSessionService.resume_with_hitl()` (a criar). Adicionar smoke test e2e. | Planejado |
| **2** (sprint+1) | Deletar `app/domains/job_management/agents/job_wizard_graph.py` + `wizard_react_agent.py` + `wizard_tool_registry.py` + `wizard_system_prompt.py` + `stage_context.py` após confirmar 0 callers. | Planejado |
| **3** (sprint+1) | Consolidar `job_management/services/wizard_*` em `job_creation/services/` ou deletar se redundantes. | Planejado |

## Consequências

**Positivas:**
- Single source of truth para wizard de vaga.
- Elimina classe de bug "state escrito num path, lido noutro".
- Sensor canonical BLOCKING previne regressão.
- Multi-tenancy invariant (ADR-029 §3) e LGPD compliance (ADR-LGPD-002)
  aplicados em ponto único.

**Negativas / riscos:**
- HITL resume continua usando legacy path durante Fase 1 — risco de
  divergência cruzada se editado isoladamente. Mitigação: EXEMPT marker
  documenta o motivo e o sensor flagra remoção do marker.
- Fase 2 requer auditoria de callers externos (ATS, Rails) que possam
  importar `JobWizardGraph` diretamente.

## Referências

- `PLAN_FIX_wizard_memory_loss.md` (plan original, Onda 4)
- `DIAGNOSTICO_FINAL_wizard_memory_loss.md` (auditoria empírica)
- `lia-agent-system/scripts/check_no_duplicate_wizard_domain.py` (sensor)
- CLAUDE.md → "canonical-agent" pattern + REGRA 3 (branch ativa Replit)
