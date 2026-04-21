# Catalogo de Sensors (feedback)

Sensors capturam erros depois do ato e devolvem sinal acionavel para o agente (e para o humano). Sem sensors, o agente repete o mesmo erro indefinidamente.

## Computacionais (deterministicos, baratos)

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

## Inferenciais (semanticos, caros)

| Categoria                  | Exemplo concreto                                                          | Onde vive                                              |
|----------------------------|---------------------------------------------------------------------------|--------------------------------------------------------|
| LLM-as-judge em PR         | Claude revisa diff e flagga quebra de convencao do `CLAUDE.md`            | `.github/workflows/llm-review.yml`                     |
| AI code review             | Subagente architect (skill `code_review`) avalia design                   | invocado por orchestrator                              |
| Semantic diff              | LLM compara duas versoes do system prompt e descreve mudanca de comportamento | `evals/semantic_diff.py`                            |
| Eval com golden dataset (inferencial) | LLM-as-judge avalia se resposta cumpre rubrica em casos abertos | `evals/inferential/`                                  |
| FairnessGuard L2 (LLM-as-judge) | LLM avalia se a saida tem viés sutil que escapou do regex            | `app/guards/fairness/llm_judge.py`                     |
| Tone / empathy check       | LLM avalia tom da resposta a candidato em casos sensiveis                 | `evals/tone/`                                          |

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

1. Pode ser expresso como **regex / lista / schema / asserção determinística**? → **sensor computacional**.
2. Exige **julgamento semantico** (tom, fairness sutil, design quality)? → **sensor inferencial**.
3. **Sempre** prefira computacional para o mesmo problema. Inferencial e fallback caro, nao primeira linha.

## Sinais de sensor ausente

- Bug entrou em producao e foi descoberto pelo cliente → sensor ausente em CI/runtime.
- Regressao em comportamento que ja funcionou antes → falta sensor estrutural ou eval.
- Mesma classe de erro aparece em multiplos PRs → falta sensor computacional para essa classe.
