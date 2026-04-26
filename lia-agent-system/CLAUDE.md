# CLAUDE.md — lia-agent-system

> Regras canônicas para agentes IA trabalhando neste repo.
> Não é doc humano — é **harness layer**: guides que reduzem P(erro) na geração de código.
> Princípio: **Agent = Model + Harness** (Hashimoto 2026). Erros recorrentes viram regras aqui.

## Não-negociáveis (multi-tenant + LGPD + fairness + secrets)

Estas regras vêm do CLAUDE.md global do usuário. **Aplicam a 100% do código.**

1. **Multi-tenant — `company_id`**: todo modelo que persiste dado de cliente DEVE ter coluna `company_id`. Toda query DEVE filtrar por `company_id`. **`company_id` vem do JWT/sessão/User-lookup, NUNCA do payload da request.** Sem exceção.
2. **LGPD**: dados sensíveis (raça, religião, gênero, etnia, estado civil, saúde) NÃO podem ser coletados nem usados em decisões de IA. Logs NÃO podem conter PII (CPF, RG, telefone, email crus) — sensor `G4: no-pii-in-logs` enforce.
3. **Fairness**: prompts que rankam/filtram candidatos DEVEM passar por `FairnessGuard`. Pattern canônico em `app/domains/communication/agents/communication_react_agent.py` (FAR-2, ACH-026).
4. **Secrets**: zero hardcoded. Tudo via env vars + Pydantic Settings.

## Anti-patterns proibidos (sensores existentes detectam)

| Anti-pattern | Por quê | Sensor |
|---|---|---|
| `getattr(model_row, "column_name", None)` | Mascara schema bug silently — fix P0-1 (auditoria 2026-04-26: `_resolve_company_id` retornava `None` pra todo Teams message) | `G6: no-getattr-on-models` (`scripts/check_no_getattr_on_models.py`) |
| Raw SQL em controllers `app/api/v1/*.py` | Mistura camada — repository é canônico | `G1: no-sql-in-controllers` |
| PII em log statements | LGPD violation | `G4: no-pii-in-logs` |
| Endpoint sem `response_model=` | Type contract quebrado | `G2: response-model-required` |
| Import de path proibido (ADR-012) | Camadas violadas | `G5: no-forbidden-imports` |
| `require_company=False` sem justificativa documentada | Bypass multi-tenant não rastreável | `F8: require-company-exemptions` |
| `try: ... except Exception: pass` | Silent failure destrói sensor — falhar alto > capturar e descartar | code review humano (TODO: linter) |

## Regras canonical-fix

- **Fix sempre no produtor, nunca no consumidor.** Se múltiplos callers passam dado errado, fix está no schema/contrato — não em cada caller.
- **Schema é fonte de verdade.** Modelo SQLAlchemy + Pydantic types > comentários > docstrings.
- **Não duplicar.** Antes de criar função/serviço novo, `grep` por nome similar. Reuso > NIH.
- **Não inventar tipos.** `String(255), nullable=True, indexed` em `User.company_id`? Replicar exato em outras colunas tenant.

## TDD obrigatório para fixes de P0/P1

Padrão: red → green → refactor. Toda fix de P0/P1 da auditoria DEVE incluir teste que falha antes da fix e passa depois. Sem teste = fix não foi feita.

**Pattern de test paths:**
- Schema check: `tests/integration/test_<feature>_<area>.py` com classe `Test<Model>Schema`
- Red team: `tests/security/test_red_team_<eixo>.py` — adicionar classe `Test<Canal>Boundary` quando expandir cobertura

## Componentes de harness deste repo

1. **Planning loop**: ReAct via `lia_agents_core` (cap iterations, condition stop)
2. **Tool layer**: `app/tools/registry.py` + `app/tools/executor.py`. Tools tipadas via `ToolDefinition`.
3. **Context management**: `app/orchestrator/registry.py` (V1/V2 — orchestrator-migration sprint III)
4. **Memory**: `app/services/conversation_memory_service.py`
5. **Sandbox**: subprocess isolation em `app/tools/executor.py`
6. **Guides**: este arquivo + módulos production-quality em `~/.claude/commands/production-quality/`
7. **Sensors**: 10 hooks em `.pre-commit-config.yaml` + suite pytest com red-team em `tests/security/`
8. **Permission gating**: `Depends(get_current_user)` + `require_company` (F8 enforce)
9. **Error handling**: 4-tier — `app/shared/errors.py` (LIAIntegrationError etc.)
10. **Observability**: OTEL `@trace_span` (orchestrator-migration sprint III.C aplicou em V1/V2)
11. **Serving layer**: FastAPI + WebSocket + RabbitMQ consumer (`MessageWorker` se aplicável)

## Auditoria pendente (referência viva)

Auditoria deep mais recente: **AUDITORIA_TEAMS_2026-04-26.md** (em `/Users/paulomoraes/Documents/Python/`).

Wave 1 (em progresso):
- ✅ **W1.1** P0-1 multi-tenant `company_id` em `TeamsConversation` — commit `f7f972882` + auto-commit `2adac0f2c`
- ⏳ **W1.2** P0-2 remover `company_id` de `TeamsWebhookPayload`
- ⏳ **W1.3** P0-3 tenant filter em `/webhook/audit-logs`
- ⏳ **W1.4** P0-4 8 testes red team Teams (PII, fairness, LGPD, prompt-injection, signature, etc.)
- ⏳ **W1.5** decorator `@require_tenant_filter` reusável

## Quando esta regra atualiza

Toda nova regra adicionada aqui DEVE:
1. Vir de erro observado (não regra preventiva genérica)
2. Ter sensor computacional correspondente (linter, teste, hook)
3. Ter mensagem de erro otimizada para LLM (não só humano)
4. Princípio Hashimoto: nunca mais aquele erro específico
