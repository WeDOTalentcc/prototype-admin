# Theme C8 — Policy Engine & Governance

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

Camada de **governança runtime** que avalia políticas dinâmicas do cliente e gating de features:
1. **Policy Engine** — avalia políticas sincronizadas do Rails (stage SLAs, processos seletivos, regras de escalação)
2. **Precondition Checker** — verifica pré-condições antes de executar ações (candidato tem permissão? vaga está aberta?)
3. **Feature Flag Service** — habilita/desabilita features por tenant (A/B testing, rollout gradual)
4. **Module Gating** — bloqueia uso de módulos baseado em billing/permissões (trial, pro, enterprise)

**Boundary com temas irmãos:**
- **HiringPolicyAgent** (em `domains/hiring_policy`) é um **agente LLM** que configura políticas; C8 é o **runtime** que avalia
- **C5 Multi-tenancy** — isolamento; C8 é policy por tenant
- **C7 Audit Trail** — C8 produz eventos que C7 audita
- **R4 Background Jobs** — policy_sync_service roda em cron

---

## Arquivos conectados (8 Python)

### Camada Persona (LLM vê — 0 YAMLs)

Nenhum YAML específico — tema 100% código. Policies são dados estruturados lidos de DB sincronizados do Rails.

### Camada Código (Python — 8 arquivos)

**Core Policy (5 arquivos):**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|------------------|
| `policy_engine.py` | `app/orchestrator/policy_engine.py` | 345 | **Núcleo.** `PolicyEngine` class — avaliação de policies em runtime + `_get_db_connection()` |
| `policy_engine_service.py` | `app/shared/services/policy_engine_service.py` | 2 | Thin re-export para manter import path (back-compat) |
| `policy_middleware.py` | `app/shared/policy_middleware.py` | 111 | FastAPI middleware: `get_policy_from_request()`, `get_policy_for_company()`, `resolve_policy_value()` — injeta policy no request context |
| `policy_helper.py` | `app/shared/policy_helper.py` | 120 | Utilities: `get_company_policy()`, cache invalidation, `get_policy_rule()` |
| `policy_sync_service.py` | `app/shared/policy_sync_service.py` | 167 | Sync periódico de policies do Rails: `sync_policy_to_models()`, `_sync_stage_slas()`, `_sync_feature_flags()` |

**Precondition + Governance (3 arquivos):**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|------------------|
| `precondition_checker.py` | `app/orchestrator/precondition_checker.py` | 385 | `PreConditionChecker` + `ProactiveHint` — verifica pré-condições antes de ações + sugestões proativas |
| `feature_flag_service.py` | `app/shared/governance/feature_flag_service.py` | 340 | `FeatureFlagService` singleton + `get_feature_flag_service()` |
| `module_gating.py` | `app/shared/module_gating.py` | 289 | `check_tool_module_access()`, `require_module()`, `build_degraded_response()`, `build_beta_response()` |

### Integration points

- **Middleware chain:** policy_middleware corre APÓS auth_enforcement → popula `request.state.policy`
- **Agents** consultam policy via `policy_helper.get_company_policy(company_id)` antes de decisões operacionais
- **Rails integration:** Rails app (ats-api-copia) é SSoT das policies; LIA sincroniza via `policy_sync_service` (R4 cron)
- **FeatureFlagService:** usado em cascaded_router (I3) e custom_agent_runtime (AS1) para gating
- **Audit (C7):** policy changes + feature flag toggles geram audit log

---

## Lógica IN → OUT

### Policy Engine — avaliação runtime

**Input:**
```python
policy_dict: dict        # policy carregada do DB (sincronizada do Rails)
context: dict            # company_id, vacancy_id, stage, recruiter_action
```

**Processing:**
```
1. PolicyEngine recebe policy_dict + context
2. Avalia regras declarativas (YAML-like estrutura):
   - stage_slas: {screening: "5 dias", interview: "3 dias", offer: "2 dias"}
   - processo_seletivo: {etapas: [...], obrigatorias: [...]}
   - autonomia_lia: "baixa" | "media" | "alta"
   - comunicacao: {tom: "formal" | "informal", canais: ["whatsapp", "email"]}
3. Retorna decision dict:
   - is_allowed: bool
   - reason: str (para log/UI)
   - suggested_action: str | None
```

**Cache:** `policy_helper.get_company_policy` usa cache (invalidation via `invalidate_policy_cache(company_id)` quando Rails envia webhook de update).

### Policy Sync — cron do Rails

**Input:** Rails API endpoint `/api/v1/policies/{company_id}` retorna JSON.

**Processing** (`policy_sync_service.sync_policy_to_models`):
```
1. Fetch current policy do Rails
2. Diff com versão local
3. _sync_stage_slas: atualiza stage_slas table
4. _sync_feature_flags: atualiza feature_flags table
5. invalidate_policy_cache(company_id)
6. Emit event policy.updated (R3 UnifiedEventPublisher)
```

**Schedule:** via Celery beat (R4) a cada 15 minutos + webhook-triggered imediato.

### Precondition Checker — antes de ação

**Input:**
```python
ctx: ProactiveHintContext  # company_id, vacancy_id, candidate_id, action_intent
```

**Processing** (`PreConditionChecker`):
```
1. Cache check (_cache_key baseado em ctx)
2. Avalia precondições específicas da action:
   - Para "move_to_interview": vaga está aberta? candidato passou na triagem?
   - Para "reject": candidato já foi rejeitado? (idempotência)
   - Para "send_offer": candidato aprovou etapas anteriores?
3. Retorna list[ProactiveHint] — se falhar, hints explicam por quê + sugerem remediation
```

**Proactive hint:**
```python
@dataclass
class ProactiveHint:
    severity: str       # "blocker" | "warning" | "info"
    message: str        # mensagem em PT-BR para o recrutador
    action: str | None  # ação sugerida ou None
```

### Feature Flag — gating dinâmico

**Input:** `flag_name: str, company_id: str, user_id: str | None`

**Processing** (`FeatureFlagService.is_enabled`):
```
1. Cache check
2. Query feature_flags table: (company_id, flag_name) → enabled | disabled | rollout_pct
3. Se rollout_pct: hash(user_id + flag_name) < pct → enabled
4. Audit log para flags críticas (ex.: FAIRNESS_LAYER3_ENABLED)
```

### Module Gating — billing/permissions

**Use case:** tenant com plano "trial" tenta usar feature "bulk_email" (só enterprise).

**Processing** (`check_tool_module_access`):
```
1. Lookup company plan
2. Lookup module's required_plan
3. Se incompatível → build_degraded_response() com upgrade CTA
4. Se beta → build_beta_response() com preview warning
```

**Decorator:** `@require_module("bulk_email")` em tools.

### Side effects

- **Audit log (C7)**: policy changes + flag toggles + module gate denials
- **Metrics:** `policy_evaluations_total{company_id}`, `feature_flag_hits_total`, `module_gate_denials_total`
- **Events (R3):** `policy.updated`, `feature_flag.toggled`

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Policy inválida do Rails (schema mismatch) | Fallback para defaults + alert ops |
| Cache miss massivo (policy DB down) | Degraded mode: default policies + alert |
| Feature flag malformada | Log + default disabled |
| Module gate negado em massa (bug) | Alert product team |

---

## Instruções para Claude Code / Cursor

### "Implementa Policy Engine & Governance no v5"

```
1. COPIE 8 arquivos Python

2. CRIE migrations para tabelas:
   - company_policies (company_id, policy_json, version, updated_at)
   - stage_slas (company_id, stage, sla_hours)
   - feature_flags (company_id, flag_name, enabled, rollout_pct)
   - module_plans (module_name, required_plan)

3. INTEGRE policy_middleware no app.add_middleware:
   # ORDEM: AuthEnforcement → TenantGuard → PolicyMiddleware → ...
   app.add_middleware(PolicyMiddleware)

4. SINCRONIZE com Rails:
   # Celery beat (R4)
   CELERY_BEAT_SCHEDULE = {
       'policy-sync-every-15min': {
           'task': 'app.shared.policy_sync_service.sync_all_policies',
           'schedule': 900,  # 15 min
       }
   }
   # + webhook receiver em app/api/v1/webhooks/policy_updated.py

5. INTEGRE precondition_checker em orchestrator:
   # Antes de executar ação (pipeline_move, send_offer, etc.):
   hints = await precondition_checker.check(ctx)
   blockers = [h for h in hints if h.severity == "blocker"]
   if blockers:
       return {"action": "blocked", "hints": blockers}

6. FEATURE FLAGS em uso:
   from app.shared.governance.feature_flag_service import get_feature_flag_service
   ff = get_feature_flag_service()
   if await ff.is_enabled("fairness_l3", company_id):
       # ... L3 enabled path

7. MODULE GATING em tools:
   @tool_handler("domain", require_company=True)
   @require_module("bulk_actions")  # ← gating
   async def bulk_reject(...): ...

8. VERIFIQUE:
   - pytest tests/unit/test_policy_engine.py
   - pytest tests/unit/test_precondition_checker.py
   - pytest tests/unit/test_feature_flag_service.py
   - Smoke: webhook Rails → policy invalidated → reload → new policy ativo
```

### "Adiciona governance a uma feature nova"

```
Se feature usa policy (ex.: stage SLA):
  → Ler policy via get_policy_from_request(request)
  → Usar get_policy_rule(policy, block="stage_slas", key="interview") para extract valor
  → Comportamento adapta ao tenant

Se feature é opt-in / experimental:
  → Criar feature_flag name em feature_flags table
  → Check via FeatureFlagService.is_enabled()
  → Default disabled; rollout via rollout_pct

Se feature requer plano específico:
  → Adicionar module em module_plans table
  → Decorator @require_module("<name>") no tool handler

Se feature exige precondições:
  → Adicionar check em PreConditionChecker
  → Criar ProactiveHint com message + severity
  → Compor com blockers existentes
```

### Setup em CLAUDE.md

```markdown
## Compliance: Policy Engine & Governance (C8)

- **Policies** sincronizadas do Rails via cron 15min + webhook
- **PolicyMiddleware** popula `request.state.policy` após Auth
- **Precondition check** antes de ações críticas (move, reject, offer)
- **Feature flags** via `FeatureFlagService` — opt-in rollout gradual
- **Module gating** via `@require_module(...)` em tools — billing-aware

Consultar `themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md`.
```

### Setup em `.cursor/rules/policy-governance.mdc`

```
---
description: "C8 Policy Engine & Governance"
alwaysApply: false
---

Quando o usuário pedir para:
- Adicionar regra de negócio configurável por tenant
- Criar feature experimental
- Gatear feature por plano de billing

1. Leia themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md
2. Policies via get_company_policy + get_policy_rule (cache)
3. Feature flags via FeatureFlagService
4. Module gating via @require_module decorator
5. Preconditions via PreConditionChecker antes de ações críticas
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nome e schema de tabelas de policies
- Backend de cache (Redis, Memcached)
- Intervalo de sync (15min é sugestão; pode ser 5min ou 30min)
- Formato de ProactiveHint (pode virar Pydantic)
- Nomes de features/flags (específicos do produto)
- Estrutura de planos (trial/pro/enterprise ou custom)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| Policy sync automatic | Policies são SSoT no Rails, LIA precisa sincronizar | LIA com policies desatualizadas = decisões erradas |
| Cache invalidation on Rails webhook | Updates precisam propagar <30s | Janela de inconsistência |
| PolicyMiddleware DEPOIS de Auth | Policy depende de company_id do JWT | Policy errada aplicada |
| Precondition check ANTES de ação irreversível | Evita estados inválidos | Ação executada e depois descoberta inválida |
| Feature flag audit log | Compliance sobre quem ativou o quê | Impossível reconstruir histórico |
| Module gating bilateral (frontend + backend) | UX consistency + security | Bypass via API direto |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `PolicyEngine` class + `get_company_policy()` funcional
- [ ] **(P0)** PolicyMiddleware registrado na ordem correta
- [ ] **(P0)** `policy_sync_service.sync_policy_to_models` rodando em cron
- [ ] **(P0)** Webhook endpoint `/webhooks/policy_updated` ativo
- [ ] **(P0)** `PreConditionChecker` integrado em decisões críticas
- [ ] **(P0)** `FeatureFlagService.is_enabled()` testado
- [ ] **(P1)** `@require_module` decorator funcional em tools
- [ ] **(P1)** Degraded response quando plano não suficiente
- [ ] **(P1)** Beta response para features em rollout
- [ ] **(P1)** Cache invalidation testada (webhook → invalidate → reload)
- [ ] **(P2)** Audit de policy changes
- [ ] **(P2)** Dashboard de feature adoption por tenant

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| Policy não atualiza após mudança no Rails | Webhook não configurado OU sync falhou | Monitorar `policy_sync_errors_total` metric |
| Feature flag sempre false | Default disabled + nunca ativado | Admin UI para toggle explícito |
| Module gating bypass via API direto | Frontend não enforça + backend esqueceu | @require_module em todas as tools afetadas |
| PolicyMiddleware ordem errada (antes de Auth) | Registro no order errado em main.py | Testes de integração com ordem de middleware |
| Precondition check causa latência | Cache miss em massa | Pre-warming + TTL curto (5-15s) |
| Flag rollout_pct não distribuído uniformemente | Hash sem user_id | Sempre incluir user_id no hash |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| PolicyEngine evaluates | `tests/unit/test_policy_engine.py` | policy_dict + context → decision correto |
| Policy cache | `tests/unit/test_policy_helper.py` | get → hit cache | invalidate → re-fetch |
| Policy sync | `tests/integration/test_policy_sync.py` | Mock Rails → sync → DB atualizado |
| PreCondition blockers | `tests/unit/test_precondition_checker.py` | vaga fechada + ação "move" → blocker |
| FeatureFlag is_enabled | `tests/unit/test_feature_flag_service.py` | Rollout 50% + user hash → distribui ~50% |
| Module gating denied | `tests/unit/test_module_gating.py` | Plano trial + module enterprise → degraded response |
| Policy webhook | `tests/integration/test_policy_webhook.py` | POST webhook → invalidate_cache chamado |
| Middleware order | `tests/integration/test_middleware_order.py` | Policy após Auth → company_id disponível |

---

## Referências

### Bundles verbatim
- Nenhum YAML específico (tema é código).

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §E (integração com CascadedRouter)

### Cross-references
- **C1 Fairness** — hiring_policy LLM agent + C8 policy runtime são complementares
- **C5 Multi-tenancy** — policies por company_id
- **C7 Audit Trail** — policy changes/flag toggles geram audit
- **I3 Orchestration** — PolicyMiddleware parte do request lifecycle
- **R3 Messaging** — policy.updated events via UnifiedEventPublisher
- **R4 Background Jobs** — policy_sync_service em Celery beat

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
