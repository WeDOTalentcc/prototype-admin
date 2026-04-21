# Catalogo de Sensors (feedback)

Sensors capturam erros depois do ato e devolvem sinal acionavel para o agente (e para o humano). Sem sensors, o agente repete o mesmo erro indefinidamente.

> **Como usar este catalogo:** as duas primeiras secoes sao **canonicas para a Plataforma LIA** — sensores reais ja em producao com path, gatilho e tipo. As duas ultimas secoes ("Generico") ficam como referencia metodologica.

---

## Sensors computacionais — instancias canonicas LIA

| ID interno | Sensor                                                                  | Onde vive                                                                                           | Trigger                       | Origem               |
|------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------|----------------------|
| S-LIA-01   | FairnessGuard L1 (regex de termos viesados)                             | `lia-agent-system/app/shared/compliance/fairness_guard.py`                                          | runtime, antes de retornar    | FIX 8                |
| S-LIA-02   | Tool executor enforcement de governance_tags                            | `lia-agent-system/app/tools/registry.py` + `executor.py`                                            | runtime, pre-tool-call        | FIX 3, FIX 8         |
| S-LIA-03   | HITL envelope estruturado (`hitl_pending`)                              | `lia-agent-system/libs/models/lia_models/hitl.py` + promocao em ChatResponse (FIX 12 G8)            | runtime, pos-tool-call        | FIX 3, FIX 12        |
| S-LIA-04   | Audit trail de fairness                                                 | `lia-agent-system/libs/models/lia_models/fairness_audit.py`                                         | runtime, em todo bloqueio L1/L2 | FIX 8 (L3)         |
| S-LIA-05   | Audit trail HITL (SOX/BCB)                                              | `lia-agent-system/libs/models/lia_models/hitl.py` (`HITLAuditTrail`)                                | runtime, em toda confirmacao  | FIX 3                |
| S-LIA-06   | `emit_tool_call()` — log estruturado de tool execution                  | `lia-agent-system/app/shared/observability/tool_metrics.py`                                         | runtime, pos-tool-call        | FIX 6, FIX 12 (G9)   |
| S-LIA-07   | Teste estrutural anti-shadowing de rotas dual-ID                        | `lia-agent-system/tests/api/test_dual_id_route_shadowing.py`                                        | CI                            | Migracao Rails->LIA  |
| S-LIA-08   | Teste estrutural anti-agent-hijack                                      | `lia-agent-system/tests/unit/test_fix14_no_agent_hijack.py`                                         | CI                            | FIX 14               |
| S-LIA-09   | Teste estrutural de prompt parity (registry vs prompt)                  | `lia-agent-system/tests/test_prompt_tool_parity.py`                                                 | CI                            | FIX 1-12             |
| S-LIA-10   | Guard contra `@langchain.tool` decorator (proibido)                     | `lia-agent-system/tests/test_no_langchain_tool_decorator_guard.py`                                  | CI                            | Canonical path       |
| S-LIA-11   | Tenant isolation tests (multi-tenant + handlers)                        | `tests/integration/test_multi_tenant_isolation.py`, `test_candidates_tenant_isolation.py`, `test_job_readiness_tenant_isolation.py` + `docs/audits/tenant_isolation_handlers_2026-04-20.md` | CI | Tenant isolation     |
| S-LIA-12   | Smoke de chat capabilities + audit CI                                   | `lia-agent-system/tests/test_chat_capabilities_audit_ci.py` + `tests/test_chat_capabilities_smoke.py` | CI                          | FIX 1-12             |
| S-LIA-13   | Wizard YAML coverage check                                              | `lia-agent-system/tests/unit/test_fix10_coverage_unification.py`                                    | CI                            | FIX 5, FIX 10        |
| S-LIA-14   | Examples quality gate (<10% fallback "isso")                            | `lia-agent-system/tests/unit/test_fix9_quality.py`                                                  | CI                            | FIX 9                |
| S-LIA-15   | Pydantic validator em tool args (LLM-recoverable)                       | declarado em cada tool schema, executado por `app/tools/executor.py`                                | runtime, pre-tool-call        | FIX 3, FIX 8         |
| S-LIA-16   | E2E audit trail de fairness block                                       | `lia-agent-system/tests/integration/test_audit_trail_fairness_block_e2e.py`                         | CI                            | FIX 8                |
| S-LIA-17   | Disparate impact (Four-Fifths Rule) sobre WSI                           | `lia-agent-system/tests/test_disparate_impact_wsi.py`                                               | CI / batch                    | DEI/Fairness         |
| S-LIA-18   | Idempotency check em endpoints dual-ID                                  | `lia-agent-system/tests/test_idempotency_dual_id.py`                                                | CI                            | Canonical path       |
| S-LIA-19   | Drift detection + bias audit pipeline                                   | `lia-agent-system/tests/integration/test_drift_and_bias_audit.py` + `app/shared/compliance/bias_audit_service.py` | CI / cron        | Stage 6              |
| S-LIA-20   | Prompt injection guard                                                  | `lia-agent-system/app/shared/compliance/prompt_injection_guard.py`                                  | runtime, pre-LLM              | Stage 3              |
| S-LIA-21   | Scoring safeguards (limites em score numerico)                          | `lia-agent-system/app/shared/compliance/scoring_safeguards.py`                                      | runtime, pos-scoring          | Stage 3              |

## Sensors inferenciais — instancias canonicas LIA

| ID interno | Sensor                                                                | Onde vive                                                                                  | Trigger                | Origem        |
|------------|-----------------------------------------------------------------------|--------------------------------------------------------------------------------------------|------------------------|---------------|
| S-LIA-22   | FairnessGuard L2 (LLM-as-judge para vies sutil)                       | `lia-agent-system/app/shared/compliance/fairness_guard.py` (camada 2) + `eval/eval_judge.py` | runtime / batch        | FIX 8         |
| S-LIA-23   | WSI Layer 2 LLM extraction/judging                                    | `lia-agent-system/app/prompts/domains/wsi_layer2_extraction.yaml` + `eval/eval_judge.py`   | batch                  | Stage 2       |
| S-LIA-24   | Eval com golden dataset (DeepEval / Ragas)                            | `lia-agent-system/tests/deepeval/`, `tests/ragas/`, `tests/golden/`, `tests/golden_dataset.py` | CI/eval offline    | Stage 6       |
| S-LIA-25   | Tone filter (avalia tom em respostas a candidato)                     | `lia-agent-system/tests/test_tone_filter.py`                                               | CI/eval                | Stage 6       |
| S-LIA-26   | LLM eval suite                                                        | `lia-agent-system/tests/llm_eval/`                                                         | CI/eval                | Stage 6       |
| S-LIA-27   | Fact checker semantico                                                | `lia-agent-system/app/shared/compliance/fact_checker.py` + `tests/test_fact_checker.py`    | runtime/eval           | Stage 3       |
| S-LIA-28   | Drift alert (detecta mudanca de distribuicao no output do agente)     | `lia-agent-system/app/shared/observability/drift_alert_service.py`                         | cron                   | Stage 6       |
| S-LIA-29   | Tool description quality check                                        | `lia-agent-system/tests/test_tool_description_quality.py`                                  | CI                     | FIX 9         |
| S-LIA-30   | Code review subagente (architect)                                     | invocado via skill `code_review`                                                           | on-demand pre-merge    | Generico      |

---

## Generico — sensors computacionais (referencia metodologica)

| Categoria                  | Exemplo concreto                                                          | Onde vive                                              |
|----------------------------|---------------------------------------------------------------------------|--------------------------------------------------------|
| Linter customizado         | Regra ESLint/Ruff que proibe `import from app.legacy`                     | `tools/lint/`, `pyproject.toml`                        |
| Teste unitario             | `test_tenant_isolation_for_screening_endpoint`                            | `tests/unit/`                                          |
| Teste de integracao        | `test_pearch_client_retries_on_503`                                       | `tests/integration/`                                   |
| Teste estrutural           | `test_no_endpoint_skips_tenant_guard` (varre arvore de rotas)             | `tests/structural/`                                    |
| Schema validator           | Pydantic falhando em payload invalido / JSON Schema em tool args          | proprio handler / proprio executor de tool             |
| Pre-commit hook            | `bandit`, `detect-secrets`, `mypy --strict` em arquivos staged            | `.pre-commit-config.yaml`                              |
| CI guard                   | GitHub Action que falha se `DEFAULT_ACCOUNT_ID` voltar ao codigo          | `.github/workflows/anti-patterns.yml`                  |
| Regex bias check           | FairnessGuard L1: lista de termos proibidos por dimensao DEI              | `app/guards/fairness/regex_rules.py`                   |
| Eval golden dataset (computacional) | Compara output exato com expected em casos canonicos             | `evals/golden/`                                        |
| HITL envelope estruturado  | Schema que sinaliza ao frontend que a acao precisa de confirmacao humana  | `app/schemas/hitl.py`                                  |
| Audit trail estruturado    | Log JSON com tenant, user, tool, args, result, timestamp                  | `app/observability/audit.py`                           |

## Generico — sensors inferenciais (referencia metodologica)

| Categoria                  | Exemplo concreto                                                          | Onde vive                                              |
|----------------------------|---------------------------------------------------------------------------|--------------------------------------------------------|
| LLM-as-judge em PR         | Claude revisa diff e flagga quebra de convencao do `CLAUDE.md`            | `.github/workflows/llm-review.yml`                     |
| AI code review             | Subagente architect (skill `code_review`) avalia design                   | invocado por orchestrator                              |
| Semantic diff              | LLM compara duas versoes do system prompt e descreve mudanca de comportamento | `evals/semantic_diff.py`                            |
| Eval com golden dataset (inferencial) | LLM-as-judge avalia se resposta cumpre rubrica em casos abertos | `evals/inferential/`                                  |
| FairnessGuard L2 (LLM-as-judge) | LLM avalia se a saida tem vies sutil que escapou do regex            | `app/guards/fairness/llm_judge.py`                     |
| Tone / empathy check       | LLM avalia tom da resposta a candidato em casos sensiveis                 | `evals/tone/`                                          |

---

## Anatomia de um sensor bem feito

Todo sensor de qualidade tem 4 partes:

1. **Trigger claro** — quando dispara (em PR, em pre-commit, em runtime, em batch).
2. **Sinal binario** — passou ou falhou (nao "score 0.73" sem threshold).
3. **Mensagem de erro otimizada para LLM** — texto contem instrucao de correcao embutida (positive prompt injection).
4. **Caminho de bypass auditavel** — quando o time precisa ignorar conscientemente, o bypass fica registrado (commit message, PR comment, `# noqa: HARNESS-XYZ — motivo`).

### Exemplo de mensagem otimizada (BOM)

```
ERROR HARNESS-RTI-002: endpoint POST /candidates/screening (linha 42 de
app/routes/candidates.py) nao usa o decorator @require_tenant.

CORRECAO: importe `from app.guards.tenant import require_tenant` e adicione
@require_tenant logo abaixo de @router.post(...).

REFERENCIA: CLAUDE.md, secao "Multi-tenancy", regra MT-3.

Esta regra existe porque endpoint sem tenant guard vaza dados entre
empresas. Ja causou incidente em 2026-Q1 (ver postmortem #87).
```

### Exemplo de mensagem fraca (RUIM)

```
ERROR: missing tenant guard
```

A diferenca: a primeira realimenta o agente com o que fazer; a segunda exige que o agente adivinhe ou que um humano explique.

## Heuristica de escolha

1. Pode ser expresso como **regex / lista / schema / assercao deterministica**? -> **sensor computacional**.
2. Exige **julgamento semantico** (tom, fairness sutil, design quality)? -> **sensor inferencial**.
3. **Sempre** prefira computacional para o mesmo problema. Inferencial e fallback caro, nao primeira linha.

## Sinais de sensor ausente

- Bug entrou em producao e foi descoberto pelo cliente -> sensor ausente em CI/runtime.
- Regressao em comportamento que ja funcionou antes -> falta sensor estrutural ou eval (ver S-LIA-08, S-LIA-09).
- Mesma classe de erro aparece em multiplos PRs -> falta sensor computacional para essa classe.
