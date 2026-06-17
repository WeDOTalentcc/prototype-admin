# NotImplementedError → 410 Gone — Callers de N-01 / N-02 (Task #857)

**Data:** 2026-04-26
**Hotfix:** Task #857 (Sprint 9.1 da auditoria revisão 2)
**Achados:** N-01, N-02 do `audit-criacao-vaga-2026-04-26-revisao-status.md`

## Contexto

Após a migração para o `JobCreationGraph` (Task #850), dois métodos legados
do wizard de criação de vagas continuaram registrados, mas implementavam
apenas `raise NotImplementedError(...)`. Em produção isso virava **HTTP 500**
sempre que algum caller residual tocava um deles. O caminho canônico passou
a ser:

* **WS** `/ws/agent-chat` com `domain=job_creation` (recruiter UI streaming)
* **HTTP** `GraphRunnerService.run_job_wizard()` (compat shim unária — Task #850)

Para estancar o erro sem efeito colateral arquitetural, ambos os métodos
agora retornam **HTTP 410 Gone** com payload padronizado:

```json
{
  "error": "Endpoint deprecated. Use WS /ws/agent-chat with domain=job_creation."
}
```

E emitem log estruturado **INFO** (não warning ruidoso):

```
wizard.legacy.deprecated_call
  tenant.company_id=<uuid>
  caller=<fully-qualified caller>
  path=<module:function>
```

## Inventário de callers (busca AST + grep)

Comandos executados (`rg -n "stream_job_wizard|get_wizard_step"`):

### N-01 — `GraphRunnerService.stream_job_wizard()`

| Arquivo | Linha | Tipo | Status |
|---|---|---|---|
| `lia-agent-system/app/domains/ai/services/graph_runner.py` | 371 | **Definição** | Patcheada (410). |
| `lia-agent-system/tests/unit/test_intake_extractor.py` | 538 | Teste de regressão | Atualizado para esperar `HTTPException(410)`. |

> **Nenhum caller de produção no repo.** O endpoint legado
> `lia_assistant_graph` que delegava aqui foi removido junto com o
> `JobWizardGraph` na Task #850.

### N-02 — `WizardOrchestratorService.get_wizard_step()`

| Arquivo | Linha | Tipo | Status |
|---|---|---|---|
| `lia-agent-system/app/domains/job_management/services/wizard_orchestrator_service.py` | 339 | **Definição** | Patcheada (410). |
| `lia-agent-system/app/domains/job_management/tools/__init__.py` | 147 | Registro de tool ReAct (`tool_id=get_wizard_step`) | Mantido — handler agora retorna 410, com log de uso residual. |
| `lia-agent-system/app/domains/job_management/domain.py` | 29 | Mapping `guided_wizard → get_wizard_step` | Mantido — caminho legado de capabilities; uso residual mensurado pelo log. |
| `lia-agent-system/app/domains/job_management/domain.py` | 45 | Mapping `get_wizard_step_data → get_wizard_step` | Idem. |

> **Nenhum caller HTTP direto no repo.** Os 2 mappings em `domain.py`
> apontam um alias residual de capabilities; quando algum chat/tool runner
> resolve um deles, o wrapper agora responde 410 e instrumenta o log para
> medir frequência antes da remoção definitiva.

## Plano de remoção definitiva

Remover os 2 métodos quando **0 chamadas registradas em
`wizard.legacy.deprecated_call` por 30 dias consecutivos** (consistente
com a política descrita no escopo da Task #857). Acompanhamento via
dashboard de logs estruturados.

## Rollback

`git revert <commit-da-task-857>` — alteração contida em 2 arquivos de
produção (+ 1 arquivo de teste atualizado, + 1 arquivo de teste novo, +
este doc). Sem migração de schema, sem mudança de contrato externo: o
status code passou de 500 para 410, ambos sinalizam erro ao caller —
qualquer client que tratava o 500 continua tratando o 410 (mais
explícito).

## Audit trail

Auditoria final atualizada em
`.local/audits/audit-criacao-vaga-2026-04-26-revisao-status.md` (seção
3.2): N-01 e N-02 marcados como **RESOLVIDO**. Demais achados (B-02,
A-01, A-02, A-08, A-09, A-10, M-12, N-03..N-10) permanecem como
estavam — escopo desta hotfix é estritamente N-01 + N-02.
