# ADR-021 — `JobCreationGraph` (Wizard de Criação de Vaga)

| Campo | Valor |
|---|---|
| Status | **Accepted** |
| Data | 2026-04-27 |
| Autores | Plataforma LIA — orchestrator team |
| Substitui | — |
| Substituído por | — |
| Referências | ADR-019 (orchestrator consolidation), ADR-017 (WSI screening data model), `app/domains/job_creation/graph.py`, Auditoria Rev 4 §N-13 |

## Contexto

A criação de vaga é o fluxo **mais auditado** da plataforma (HRS — high-risk system sob EU AI Act §6.2 + Anexo III §4). Até a Rev 3 da auditoria, o fluxo vivia espalhado entre `wizard_step_service` (handlers stateless) e `wizard.py` (5 endpoints REST). A Rev 4 confirmou a consolidação canônica em **`JobCreationGraph`** (LangGraph `StateGraph`) — porém **sem ADR específico**. SOC2/ISO 27001 e o auditor externo de EU AI Act exigem documento canônico cobrindo:

1. Os 11 nós, suas responsabilidades e contratos de I/O.
2. As transições condicionais e seus invariantes.
3. Os pontos de Human-in-the-Loop (HITL) e como o consentimento é registrado.
4. A persistência (`PostgresSaver`/`MemorySaver`) e as garantias de retomada.
5. O modo fail-closed (qualquer falha de policy/fairness aborta sem publicar).
6. O handoff para serviços downstream (`RubricDispatchService`).

Este ADR resolve o achado **N-13** da Auditoria Rev 4 e serve como artefato canônico para auditores.

## Decisão

`JobCreationGraph` é o **único orchestrator** do wizard de criação de vaga. Todo entry-point (REST `/api/v1/job-creation/*`, WebSocket `domain="wizard"`, retomada HITL) **deve** rotear pelo grafo. Endpoints legados em `wizard.py` retornam **`HTTP 410 Gone`** (ver Auditoria Rev 4 §N-03).

> **Nota de terminologia (Rev 4):** o domínio do código é `job_creation` (módulo `app/domains/job_creation/`), mas o domínio exposto na superfície WS/UI é `wizard` (preserva compatibilidade com clientes existentes). As duas formas referem-se ao **mesmo grafo**. O mapeamento canônico é:
>
> | Camada | Termo |
> |---|---|
> | Código (módulo, classes, spans) | `job_creation` (`JobCreationGraph`, `wizard.*` apenas em nomes históricos de span) |
> | API REST | `/api/v1/job-creation/*` |
> | WebSocket `domain` | `"wizard"` |
> | Frontend (`useAgentMemory`) | `"wizard"` |
>
> Renomear o canal WS para `"job_creation"` é tarefa futura (requer bump de `LIA_WS_PROTOCOL_VERSION` para `2.0` e migração coordenada de clientes via PM-03 handshake).

### Escopo do streaming de tokens (PM-02, Rev 4)

A wire-up de `astream_events("v2")` via `JobCreationGraph.stream_invoke()` está implementada e ativada **apenas no caminho de retomada HITL** (`agent_chat_ws._resume_wizard_canonical_streaming`), atrás da feature flag `LIA_WS_TOKEN_STREAMING` (default OFF). Justificativa:

1. O caminho de retomada é o **único site** em `agent_chat_ws.py` que invoca `JobCreationGraph` diretamente — chamadas pelo grafo durante a primeira mensagem do usuário ocorrem via `graph_runner.py:248` (Celery / orquestração) e `crew_examples.py:186` (exemplos), fora do laço de mensagens WS.
2. Estender streaming para o caminho da primeira mensagem requer roteamento explícito de `domain="wizard"` no laço de mensagens WS (atualmente roteado para o registry genérico de agentes), o que extrapola o escopo do achado PM-02 e está coberto pelo follow-up de **token streaming end-to-end**.
3. A flag default OFF garante zero impacto em produção até validação A/B controlada.

### Diagrama (alto nível)

```
                            ┌──────────────┐
                            │   intake     │  parse + extrai entidades
                            └──────┬───────┘
                                   ▼
                            ┌──────────────┐
                            │ jd_enrichment│  enriquece JD (LLM)  ← HITL #1
                            └──────┬───────┘
              ┌────────────┬───────┼────────────┐
              ▼            ▼       ▼            ▼
        (intake)     (bigfive)   (end)
                          │
                          ▼
                    ┌──────────┐                      ┌──────────────┐
                    │ bigfive  │ ── salary ─────────► │   salary     │
                    └────┬─────┘                      └──────┬───────┘
                         │                                   │
                         └─────────► competency ◄────────────┘
                                          │
                                          ▼
                                  ┌──────────────┐
                                  │wsi_questions │  perguntas de triagem ← HITL #2
                                  └──────┬───────┘
                                         ▼
                                  ┌──────────────┐
                                  │ eligibility  │  policy gate (fail-closed)
                                  └──────┬───────┘
                                         ▼
                                  ┌──────────────┐
                                  │   review     │  readiness check
                                  └──────┬───────┘
                                         ▼
                                  ┌──────────────┐
                                  │   publish    │  cria Job no banco
                                  └──────┬───────┘
                                         ▼
                                  ┌──────────────┐
                                  │ calibration  │  rubric calibration
                                  └──────┬───────┘
                                         ▼
                                  ┌──────────────┐
                                  │   handoff    │  → RubricDispatchService
                                  └──────┬───────┘
                                         ▼
                                       END
```

## Os 11 nós

Todos os nós são **funções puras** (`fn(state) -> state_delta`) decoradas com `@wizard_traced_node("wizard.<stage>")` (ver `app/shared/observability/span_validation.py`) — emitem span OTLP **e** histograma `wizard_node_latency_seconds` (N-14, Rev 4).

| # | Node | Responsabilidade | I/O Crítico | HITL | Fail-mode |
|---|---|---|---|---|---|
| 1 | `intake_node` | Parse da fala do recrutador, extração de entidades (cargo, senioridade, modalidade), classificação de intent. | In: `last_message`. Out: `intake_payload`, `current_stage="intake"`. | — | Reentrar no `intake` se intent não classificável. |
| 2 | `jd_enrichment_node` | Enriquecimento de JD via LLM com base em `intake_payload` e contexto da empresa (catálogos, departamentos, benefícios). | In: `intake_payload`, `company_context`. Out: `jd_enriched`, `ws_stage_payload`. | **Sim** — recrutador aprova/edita o JD enriquecido antes do próximo nó. | Volta para `intake` se rejeitado. Aborta se LLM falha 3x. |
| 3 | `bigfive_node` | Sugestão de perfil Big Five baseado em catálogos históricos da empresa + tabela de benchmarks de cargo. | In: `intake_payload`, `historical_patterns`. Out: `bigfive_profile`. | — | Default conservador se não houver histórico. |
| 4 | `salary_node` | Sugestão de faixa salarial; pode ser pulado por `route_after_bigfive` se a empresa já fixou política. | In: `intake_payload`, `salary_patterns`. Out: `salary_band`. | — | Pula para `competency` se policy obriga `pre-set`. |
| 5 | `competency_node` | Mapeamento de competências técnicas / comportamentais. Pode pular para `wsi_questions` ou ir direto para `END` quando screening_mode = none. | In: `intake_payload`, `bigfive_profile`. Out: `competencies`. | — | `END` se screening desativado. |
| 6 | `wsi_questions_node` | Geração de perguntas de triagem WSI (ver ADR-017). | In: `competencies`, `bigfive_profile`. Out: `wsi_questions`, `ws_stage_payload`. | **Sim** — recrutador aprova/edita as perguntas. | Reentrar no próprio nó se rejeitado; `END` se cancelado. |
| 7 | `eligibility_node` | Policy gate canônico (`PolicyEngineService` + `FairnessGuard` 3 camadas). **Fail-closed.** | In: payload completo. Out: `policy_decision` (`approve`/`reject`/`hold`). | — | **Aborta** se viola critério protegido (LGPD/EU AI Act). |
| 8 | `review_node` | Readiness check final: campos obrigatórios, score de calibração, contagem de skills. | In: payload completo. Out: `readiness_score`. | — | Volta para `competency` se score < 0.7. |
| 9 | `publish_node` | Persiste a vaga (`Job` table) com flag `status="published"`. Idempotente por `idempotency_key`. | In: payload completo. Out: `job_id`. | — | Aborta o grafo se DB falhar (não chega no calibration). |
| 10 | `calibration_node` | Calibração de rubrica para pipeline (peso/score por critério). | In: `job_id`, `competencies`, `wsi_questions`. Out: `rubric_id`. | — | `END` se calibração não for necessária (ex.: vaga interna). |
| 11 | `handoff_node` | Despacha rubrica para `RubricDispatchService` (sourcing/screening downstream). | In: `rubric_id`. Out: evento OTLP `wizard.handoff.completed`. | — | Best-effort. Falha não invalida o publish. |

## Persistência e retomada

- **Checkpointer**: `PostgresSaver` em produção (`DATABASE_URL`), `MemorySaver` em test. Configurado via `app/core/checkpointer_factory.py`.
- **Thread ID**: `wizard:{company_id}:{user_id}:{conversation_id}` — garante isolamento multi-tenant e reentrancy idempotente.
- **Garantia de retomada (A-06, Rev 4)**: cliente WS desconecta a qualquer momento → reconexão com mesmo `thread_id` retoma do último checkpoint persistido. Validado por `tests/integration/test_ws_reconnect_resume_wizard.py` (8 cenários).

## HITL — pontos de aprovação humana

Há **dois** pontos de HITL no grafo:

1. **Após `jd_enrichment_node`** — recrutador aprova/edita o JD enriquecido pelo LLM.
2. **Após `wsi_questions_node`** — recrutador aprova/edita as perguntas de triagem WSI.

Ambos passam por `HITLService.request_approval()` (registra `pending_approval` em DB), suspendem o grafo (`hitl_approved=False`) e só prosseguem após `_resume_wizard_canonical()` ser chamado com a aprovação. **A decisão humana é registrada** em `audit_service.log_decision()` com critérios protegidos vazios (sanitização LGPD).

## Fail-closed — invariantes de produção

- `eligibility_node` **aborta** o grafo se `PolicyEngineService` ou `FairnessGuard` retornarem `reject`. Nenhum job é publicado.
- `publish_node` é idempotente (`idempotency_key = sha256(thread_id + payload_hash)`) — retomada nunca cria duplicata.
- Todo span de nó carrega `tenant.company_id`, `user.id`, `conversation.id`, `orchestrator.version`, `wizard.stage` (N-07/N-08, ADR-019). Atributos LGPD-protegidos são banidos em runtime (`FORBIDDEN_SPAN_ATTR_PATTERNS`).
- Histograma OTLP `wizard_node_latency_seconds{node=...}` permite alertar regressão por nó (N-14, Rev 4).

## Handoff: `calibration_node` → `RubricDispatchService`

`handoff_node` é o **ponto canônico** de entrega para downstream:

```python
RubricDispatchService.dispatch(
    rubric_id=state["rubric_id"],
    job_id=state["job_id"],
    company_id=state["tenant"]["company_id"],
    requested_by=state["user"]["id"],
)
```

`RubricDispatchService` registra a rubrica em `rubric_registry` e emite eventos `rubric.created` para sourcing/screening reagirem (`SourcingPlannerAgent`, `PipelineReActAgent`).

## Versionamento e migração

- **Versão atual**: `orchestrator.version=2` (V2 = JobCreationGraph). V1 (handoff via `wizard_step_service`) foi descontinuado em #850 e os handlers legados foram removidos em #871 (Rev 4 §N-04).
- **Feature flag** `LIA_V2_USE_PLAN_SERVICE` governa a substituição do `PlanOrchestrationService` (V1) pelo grafo. Default `false`. Plano de remoção: `# REMOVE: 2026-07-01` (ver Rev 4 §N-10).
- **Contrato de payload** entre wizard e UI: `app/contracts/wizard_contract.py` (Pydantic v2) — gera `wizard-contract.ts` no frontend (Rev 4 §N-12).

## Consequências

### Positivas

- Auditor externo SOC2/EU AI Act tem documento canônico do fluxo HRS.
- Single-source-of-truth para nós, transições e invariantes.
- HITL e fail-closed documentados explicitamente (requisito EU AI Act §14).
- Histograma por nó permite alertar regressão sem agregação cega.

### Negativas / trade-offs

- ADR precisa ser atualizado a cada novo nó. Mitigado por test CI (`tests/ci/test_wizard_span_attributes.py`) que falha se a lista de nós divergir.
- Crescimento do grafo aumenta superfície de teste — mitigado por `tests/integration/test_job_creation_graph_e2e.py` cobrindo o happy-path completo.

## Status de implementação (Rev 4)

- ✅ 11 nós ativos em `app/domains/job_creation/graph.py`
- ✅ Decorator `@wizard_traced_node` aplicado em todos (CI gate `test_wizard_span_attributes.py`)
- ✅ HITL #1 + HITL #2 funcionais com retomada via checkpointer
- ✅ Histograma `wizard_node_latency_seconds` emitido (N-14)
- ✅ Contrato Pydantic+TS (N-12)
- ✅ Reconnect WS test (A-06)
- ✅ Endpoints legados retornam 410 (N-03)

## Apêndice — referências de código

| Arquivo | Linhas relevantes |
|---|---|
| `app/domains/job_creation/graph.py` | `class JobCreationGraph` L1610; `create_job_creation_graph()` L1493; nodes L1496–1506; edges L1509–1598 |
| `app/domains/job_creation/state.py` | `JobCreationState` (TypedDict) |
| `app/shared/observability/span_validation.py` | `wizard_traced_node` L233; `_attrs_from_state` |
| `app/api/v1/agent_chat_ws.py` | `_resume_wizard_canonical()` L378 |
| `app/contracts/wizard_contract.py` | `WizardStagePayload`, `BigFiveProfile`, `TraitRanking` |
| `tests/integration/test_ws_reconnect_resume_wizard.py` | 8 cenários de reconnect/resume |
| `tests/ci/test_wizard_span_attributes.py` | CI gate de instrumentação |
