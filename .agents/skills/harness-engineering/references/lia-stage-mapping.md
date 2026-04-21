# Mapeamento: 6-stage remediation plan + FIX 1-14 -> matriz harness

Este documento materializa o "moat proprietario" da skill `harness-engineering`: cada finding/intervencao do plano de remediacao da LIA esta classificada na matriz **guide x sensor / computacional x inferencial**, com path canonico, skill LIA responsavel e ID dos catalogos (`G-LIA-XX` / `S-LIA-XX`).

**Use este mapa quando:**
- Consolidar findings de uma nova auditoria.
- Planejar a proxima intervencao de harness e checar se o gap ja foi tratado em FIX anterior.
- Onboarding de novo agente/dev no jargao da remediacao.

---

## Tabela mestre — por FIX

| FIX  | Tema                                                  | Celula(s) da matriz                                          | Stage | Skill LIA responsavel                            | Catalogo IDs            | Artefato canonico                                                                                                               |
|------|-------------------------------------------------------|--------------------------------------------------------------|-------|--------------------------------------------------|-------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| 1    | DomainActions chegam ao LLM via routing context       | Guide computacional                                          | 1     | `ai-architecture`, `canonical-fix`               | G-LIA-01, G-LIA-02      | `app/domains/*/actions.py` + `app/orchestrator/llm_cascade.py::rebuild_routing_context()`                                        |
| 2    | Examples populados em toda DomainAction               | Guide inferencial                                            | 2     | `ai-architecture`, `lia-planning`                | G-LIA-08                | `app/domains/*/actions.py` (campo `examples`); validado por `tests/unit/test_fix2_examples_populated.py`                         |
| 3    | governance_tags + requires_hitl no executor           | Guide computacional + Guardrail + Sensor computacional       | 1+5   | `lia-compliance` PARTE 1 / PARTE 3               | G-LIA-03, S-LIA-02, S-LIA-03, S-LIA-05 | `app/tools/tool_registry_metadata.yaml` + `app/tools/registry.py`/`executor.py` + `libs/models/lia_models/hitl.py`     |
| 4    | related_tools (suggested next) no agentic_loop        | Guide inferencial                                            | 2     | `ai-architecture`                                | G-LIA-16                | YAML `related_tools` + helper em `app/orchestrator/agentic_loop.py`                                                              |
| 5    | Wizard tools enriquecidos com YAML descriptions       | Guide computacional                                          | 4     | `canonical-fix`, `feature-audit` D5              | G-LIA-05, S-LIA-13      | `app/domains/job_management/agents/wizard_tool_registry.py` + sync em `app/tools/tool_registry_loader.py`                        |
| 6    | Logging estruturado de tool calls                     | Sensor computacional                                         | 6     | `lia-testing`, `lia-compliance` PARTE 4          | S-LIA-06                | `app/shared/observability/tool_metrics.py::emit_tool_call`                                                                       |
| 7    | Cluster semantico cross-references (parte A)          | Guide inferencial                                            | 2     | `ai-architecture`, `lia-planning`                | G-LIA-06                | Descriptions de DomainActions em `job_management`, `cv_screening`, `sourcing`                                                    |
| 8    | Governance enforcement completo (FairnessGuard L1+L2+L3 + side_effects) | Sensor computacional + Sensor inferencial + Guardrail | 3 | `lia-compliance` PARTE 3, `lia-testing`           | S-LIA-01, S-LIA-04, S-LIA-16, S-LIA-22 | `app/shared/compliance/fairness_guard.py` + `libs/models/lia_models/fairness_audit.py` + `eval/eval_judge.py`            |
| 9    | Examples quality gate (<10% fallback)                 | Sensor computacional                                         | 2     | `lia-testing`                                    | S-LIA-14, S-LIA-29      | `tests/unit/test_fix9_quality.py` + `tests/test_tool_description_quality.py`                                                     |
| 10   | Wizard YAML coverage + requires_confirmation unificado | Guide computacional + Sensor computacional                  | 4     | `canonical-fix`, `feature-audit` D2/D5           | G-LIA-04, G-LIA-05, S-LIA-13 | `app/orchestrator/action_executor/intents_config.py` + `tests/unit/test_fix10_coverage_unification.py`                     |
| 11   | actions_context placement + WSI cluster (parte B)     | Guide computacional + Guide inferencial                      | 1+2   | `ai-architecture`                                | G-LIA-06, G-LIA-07      | `app/orchestrator/llm_cascade.py::_ROUTING_PROMPT` + cross-refs em `generate_wsi_questions`                                      |
| 12   | HITL envelope promovido a top-level + emit_tool_call  | Sensor computacional                                         | 5+6   | `ai-architecture`, `lia-testing`                 | S-LIA-03, S-LIA-06      | Promocao em `ChatResponse.structured_data.hitl_pending` + `tool_metrics.emit_tool_call` em `agentic_loop`                         |
| 13   | Policy consolidation                                  | Guide computacional                                          | 1+4   | `canonical-fix`, `lia-compliance` PARTE 1        | G-LIA-10, G-LIA-11      | `docs/TODO_POLICY_CONSOLIDATION.md` + `docs/RLS_CONTRACT.md` + `docs/CANONICAL_SOURCES_SPEC.md`                                  |
| 14   | Anti-agent-hijack (onboarding hint nao sobrescreve agent_type) | Sensor computacional + Guide computacional         | 1     | `canonical-fix`                                  | G-LIA-12, S-LIA-08      | `app/orchestrator/main_orchestrator.py` + regression em `tests/unit/test_fix14_no_agent_hijack.py`                               |

---

## Tabela mestre — por Stage do remediation plan

| Stage | Tema                                              | Celula predominante              | FIXes que materializam | Catalogo IDs predominantes                                              |
|-------|---------------------------------------------------|----------------------------------|------------------------|-------------------------------------------------------------------------|
| 1     | Routing & Tool Decision                           | Guide computacional + Guardrail  | 1, 3, 11, 13, 14       | G-LIA-01, G-LIA-02, G-LIA-03, G-LIA-04, G-LIA-07, G-LIA-10, G-LIA-12    |
| 2     | Few-shot & Context Injection                      | Guide inferencial                | 2, 4, 7, 9, 11         | G-LIA-06, G-LIA-08, G-LIA-13, G-LIA-14, G-LIA-15, G-LIA-16              |
| 3     | Fairness & Compliance Guards                      | Sensor computacional + inferencial + Guardrail | 8           | S-LIA-01, S-LIA-04, S-LIA-16, S-LIA-17, S-LIA-20, S-LIA-21, S-LIA-22, S-LIA-27 |
| 4     | Wizard Coverage & Resolvers                       | Guide computacional              | 5, 10, 13              | G-LIA-04, G-LIA-05, G-LIA-10, S-LIA-13                                  |
| 5     | HITL Envelope & Tool Emission                     | Sensor computacional             | 3, 12                  | S-LIA-03, S-LIA-05                                                      |
| 6     | Observability Consolidation                       | Sensor computacional + inferencial | 6, 12                | S-LIA-06, S-LIA-19, S-LIA-23, S-LIA-24, S-LIA-25, S-LIA-26, S-LIA-28    |

---

## Falhas conhecidas -> celula da matriz -> skill responsavel

Use esta tabela quando classificar **uma nova falha observada** em producao ou em audit.

| Sintoma observado                                                    | Tipo (failure-taxonomy) | Celula predominante                 | Skill LIA primaria                    | Sensor/Guide canonico               |
|----------------------------------------------------------------------|-------------------------|-------------------------------------|---------------------------------------|--------------------------------------|
| LLM ignorou DomainAction, foi para fluxo livre                       | LLM-recoverable         | Guide computacional ausente         | `ai-architecture`                     | G-LIA-01, G-LIA-02                   |
| LLM chamou tool com argumento invalido                               | LLM-recoverable         | Sensor computacional (Pydantic)     | `ai-architecture`, `lia-testing`      | S-LIA-15                             |
| Acao de alto risco executada sem confirmacao                         | User-fixable            | Guardrail (requires_hitl)           | `lia-compliance` PARTE 1              | G-LIA-03, S-LIA-03, S-LIA-05         |
| Tool emitiu texto com termo viesado                                  | Compliance violation    | Sensor computacional (L1 regex)     | `lia-compliance` PARTE 3              | S-LIA-01, S-LIA-04                   |
| Vies sutil escapou da regex L1                                       | Compliance violation    | Sensor inferencial (LLM judge)      | `lia-compliance` PARTE 3              | S-LIA-22, S-LIA-23                   |
| Disparate impact entre grupos protegidos no scoring                  | Compliance violation    | Sensor computacional (Four-Fifths)  | `lia-compliance` PARTE 3              | S-LIA-17, S-LIA-19                   |
| Endpoint nao isolou tenant -> dado vazou                             | Tenant isolation breach | Sensor computacional (CI structural) | `canonical-fix`, `lia-testing`        | S-LIA-11, G-LIA-11                   |
| Rota legacy fez shadowing da rota canonica                           | Tenant/Routing          | Sensor computacional (CI structural) | `canonical-fix`                       | S-LIA-07, G-LIA-09                   |
| Onboarding hint sequestrou agent_type em sessao multi-turno          | Unexpected/Regression   | Sensor computacional (CI structural) | `canonical-fix`                       | S-LIA-08, G-LIA-12                   |
| Wizard pediu confirmacao em momento errado (drift entre prompt e codigo) | LLM-recoverable     | Guide computacional + Sensor CI     | `canonical-fix`, `feature-audit`      | G-LIA-04, G-LIA-05, S-LIA-13         |
| Tom inadequado em feedback ao candidato                              | Compliance violation    | Sensor inferencial (tone judge)     | `lia-compliance` PARTE 3              | S-LIA-25, G-LIA-13                   |
| `@langchain.tool` voltou ao codigo (anti-pattern)                    | Unexpected              | Sensor computacional (CI guard)     | `canonical-fix`                       | S-LIA-10                             |
| Ratio de exemplos "isso"-fallback subiu acima de 10%                 | Quality regression      | Sensor computacional (CI gate)      | `lia-testing`                         | S-LIA-14, S-LIA-29                   |
| Tool chamada nao gerou audit log                                     | Compliance violation    | Sensor computacional (runtime)      | `lia-compliance` PARTE 4              | S-LIA-06                             |
| Drift de output do agente em producao                                | Unexpected              | Sensor inferencial (cron)           | `lia-compliance` PARTE 4              | S-LIA-19, S-LIA-28                   |
| Prompt injection na entrada do usuario                               | Compliance violation    | Sensor computacional (runtime)      | `lia-compliance` PARTE 3              | S-LIA-20                             |

---

## Convencoes de manutencao

- **Adicionar nova FIX**: incremente o numero, classifique na celula, registre no glossario `docs/GLOSSARIO_ACTIONS_TOOLS.md`, atualize esta tabela e os catalogos com `G-LIA-XX` ou `S-LIA-XX` correspondentes.
- **Adicionar novo sensor/guide**: aloque proximo ID livre nos catalogos (`G-LIA-17`, `S-LIA-31`...) e mapeie aqui o sintoma que ele cobre.
- **Nunca remova entrada**: se o artefato foi descontinuado, marque com `~~tachado~~` + commit/ADR que justifica para preservar trilha de aprendizado (regra Hashimoto: cada erro vira regra persistente).

## Cross-references com `failure-taxonomy.md`

- A coluna "Tipo (failure-taxonomy)" aqui e o mesmo enum de `references/failure-taxonomy.md` (Transient / LLM-recoverable / User-fixable / Unexpected / Compliance violation / Tenant isolation breach).
- Quando um novo tipo de falha for descoberto e nao couber em nenhum dos 6, abra debate em `failure-taxonomy.md` antes de adicionar coluna nova aqui.
