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

## Dead Code Documentado

| Método | Arquivo | Status | Razão |
|---|---|---|---|
| `ContextAdapter.from_ws` | `app/orchestrator/context_adapter.py` | DEAD CODE | WS handler faz inline promotion (linhas 954-961 de `agent_chat_ws.py`) |
| `ContextAdapter.from_rabbitmq` | `app/orchestrator/context_adapter.py` | DEAD CODE | Nenhum consumer RabbitMQ existe ainda em `lia-agent-system` |
