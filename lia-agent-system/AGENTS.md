# AGENTS.md — lia-agent-system

> Este arquivo define o harness de desenvolvimento para agentes IA.
> Leia ANTES de modificar qualquer arquivo em `app/orchestrator/`, `app/domains/`, `app/shared/providers/`.

## Regras Canônicas

### Roteamento (CascadedRouter)
- Rail A (`rail_a_hint_override.py`) sempre precede os demais tiers.
- `domain_hint="wizard"` está em `_RAIL_A_EXTRA_TARGETS` — não registrar via `@register_domain`.
- Para adicionar novo routing target fora do DomainRegistry: adicionar em `_RAIL_A_EXTRA_TARGETS` com docstring explicando por que não usa `@register_domain`.

### LLM Providers
- Todos os métodos `generate*` devem ter `@llm_transient_retry` (tenacity) + `@circuit_breaker_decorator`.
- Ordem obrigatória: `@circuit_breaker_decorator` → `@_traceable` → `@llm_transient_retry` → `async def`.
- Providers canônicos: `app/shared/providers/llm_claude.py`, `llm_openai.py`. Adicionar novo provider = replicar essa stack.

### Multi-tenancy (P0 — blocante)
- `company_id` SEMPRE do JWT/session, NUNCA do payload.
- Toda query SQLAlchemy que toque dados de empresa deve ter `.where(Model.company_id == company_id)`.
- Sensor automático: `scripts/check_tenant_guards.py`.

### Histórico de Conversa (P1-A)
- Trim obrigatório a `_MAX_HISTORY_MESSAGES = 20` antes de passar ao LLM.
- Ponto canônico: na borda de consumo (antes do `agent.process()`), não no model Pydantic.
- Ver: `app/api/v1/orchestrated_jobs_management.py:_MAX_HISTORY_MESSAGES`.

### LGPD (P0 — blocante)
- `provider_contact` em `CompanyBenefit` é PII — mascarar em logs.
- `approved_by`, `created_by` em `CompensationPolicy` são UUIDs — nunca logar em plain text.
- Campos proibidos em decisões de IA: raça, religião, gênero, etnia, estado civil, saúde.

### Wizard × Benefits/PRV (WIZARD-INT:001-005)
- Benefits filtrados por `seniority_levels` (Python-side, graceful degradation).
- `suggestions_data.benefits` inclui `id` para de-dup por id no FE.
- `suggestions_data.compensation_policy` expõe a policy default para o painel.
- `offer_service._enrich_job_snapshot_compensation()` carrega PRV antes do prefill.
- Botão "Sugerir pacote com LIA" via `onSuggestWithLIA` prop em `EditJobModalCompensation`.

## Referências

- Auditoria completa: `docs/architecture/AI_AGENT_AUDIT_REPORT.md`
- Roadmap de implementação: `docs/architecture/IMPLEMENTATION_ROADMAP.md`
- Guia de harness (regras extensas): `CLAUDE.md` (este repo)
- Plano de sessão: `~/.claude/plans/chave-do-replit-para-linked-pie.md`

## Integrações Planejadas (NOT YET WIRED)

> Estes componentes estão **implementados e testados** mas ainda não conectados ao tráfego de produção.
> Para encontrá-los: `grep -rn "TODO(RABBITMQ-INT\|WS-ADAPTER-INT)" app/`

| Componente | Arquivo | Status | O que falta para conectar |
|---|---|---|---|
| `ContextAdapter.from_ws` | `app/orchestrator/context_adapter.py` | NOT YET CALLED | Refatorar inline promotion em `agent_chat_ws.py:~954` para chamar este método |
| `ContextAdapter.from_rabbitmq` | `app/orchestrator/context_adapter.py` | NOT YET WIRED | Implementar `app/workers/rabbitmq_consumer.py` (stub existe) |
| `app/workers/rabbitmq_consumer.py` | `app/workers/rabbitmq_consumer.py` | STUB | Consumer AMQP + queue binding + integration test (ver docstring do módulo) |

### Checklist para ativar RabbitMQ em produção

- [ ] `AMQP_URL` env var configurada no Replit Secrets
- [ ] `INTERNAL_SERVICE_TOKEN` env var configurada (shared secret Rails↔Python)
- [ ] Exchange/queue criados: `exchange=lia.exchange`, `queue=lia.jobs`, `key=lia.chat`
- [ ] Rails `LiaJobsProducerService` publicando no formato do contrato (ver `rabbitmq_consumer.py` docstring)
- [ ] `app/workers/rabbitmq_consumer.py` implementado (substituir stub)
- [ ] Integration test: `tests/integration/test_rabbitmq_consumer.py`
- [ ] Smoke test manual: publicar 1 msg → verificar log `[rabbitmq_consumer] routed via ContextAdapter.from_rabbitmq`

## Idempotency Guards (G8 — LangGraph Re-execution Safety)

**Contexto:** Nós do JobCreationGraph são SYNC e podem ser re-executados pelo LangGraph (retry automático, checkpoint restore). Qualquer escrita no BD que aconteça após conclusão de um nó **deve** ser idempotente.

### Regra G8 (computacional — guide)

Toda chamada a `record_job_completion()` e funções similares de learning loop **deve** incluir um `idempotency_key` gerado como:

```python
import hashlib
from datetime import date

idempotency_key = hashlib.md5(
    f"{company_id}:{manager_email}:{job_id or session_id}:{date.today().isoformat()}".encode()
).hexdigest()
```

O serviço verifica `prefs.last_idempotency_key == idempotency_key` antes de qualquer write — se igual, retorna sem efeito colateral.

### Sensor G8 (computacional — CI guard)

Pre-commit / CI: qualquer nova chamada a `record_job_completion()` sem `idempotency_key` quebra o build:

```bash
# Sensor G8 — rodar em CI ou pre-commit
grep -rn "record_job_completion(" --include="*.py" | grep -v "idempotency_key" | grep -v "def record_job_completion" | grep -v "test_"
# Se retornar linhas → falha: adicione idempotency_key=<md5> na chamada
```

### Mensagem de erro para o LLM

> `G8 VIOLATION: record_job_completion() chamado sem idempotency_key. LangGraph pode re-executar este nó e duplicar jobs_created_count. Corrija: gere um hashlib.md5(...).hexdigest() único por (company_id, manager_email, job_id, date) e passe como idempotency_key=...`

### Arquivos canônicos

- Service: `app/domains/job_creation/services/manager_preferences_service.py` → `record_job_completion()`
- Call site: `app/domains/job_creation/services/wizard_session_service.py` (pós-handoff, L~260)
- Modelo: `libs/models/lia_models/manager_preferences.py` → campo `last_idempotency_key`
