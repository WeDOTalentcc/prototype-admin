# Theme: Background Jobs & Async Schedulers — Resilience Layer

## O que é este tema

Background Jobs é a camada de **processamento assíncrono** da LIA: tarefas longas (sourcing, triagem em lote, drift check) rodando como workers Celery fora do ciclo HTTP, além de jobs periódicos agendados via Beat. Complementado pelo `DomainTaskManager` — asyncio-based para tarefas de média duração dentro do processo FastAPI.

**3 sub-sistemas:**
1. **Celery App (`lia_config.celery_app`)** — configuração central: 4 filas com prioridade, DLQ, PII masking por worker, timezone Brasília
2. **Beat Schedule (14+ tarefas)** — jobs periódicos: drift check, LGPD cleanup, RAGAS, briefing, follow-up WSI, etc.
3. **DomainTaskManager + AsyncProcessing** — asyncio in-process para operações bulk elegíveis

**Boundary com temas irmãos:**
- **R2 Learning Loop**: `analyze_patterns()`, `export_finetuning_data()`, `ragas.evaluate_batch` rodam como Celery tasks
- **R3 Messaging**: `DomainDispatcher` enfileira mensagens que os workers Celery consomem
- **C7 Audit Trail**: `audit.apply_lifecycle_policy` roda mensalmente via Beat
- **C3 LGPD Consent**: `lgpd.run_cleanup_daily` e `conversation.ttl_cleanup` rodam diariamente

---

## Arquivos conectados (9 total)

### Camada Código (9 arquivos Python)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `celery_app.py` (canonical) | `libs/config/lia_config/celery_app.py` | Celery instance, 4 filas, LIATask base class, beat_schedule, task_routes, PII masking hook |
| `celery_app.py` (shim) | `app/core/celery_app.py` | Backward compat: `from lia_config.celery_app import celery_app` |
| `celery_tasks.py` (facade) | `app/jobs/celery_tasks.py` | Facade: `from app.jobs.tasks import *` |
| `tasks/` (10 módulos) | `app/jobs/tasks/{agents,agents_legacy,communication,compliance,feedback,followup,memory,ml,voice,_utils}.py` | Definições de tasks por domínio |
| `drift_job.py` | `app/jobs/drift_job.py` | `run_drift_check_all_companies()` — iteração de todas as empresas ativas |
| `followup_service.py` | `app/jobs/followup_service.py` | Follow-up de convites WSI não abertos |
| `scheduled_reports.py` | `app/jobs/scheduled_reports.py` | Reports programados (disabled by default — `ENABLE_SCHEDULED_REPORTS=true`) |
| `wsi_abandoned_service.py` | `app/jobs/wsi_abandoned_service.py` | Triagem WSI abandonada (candidatos que não completaram) |
| `webhook_tasks.py` | `app/jobs/webhook_tasks.py` | Webhook delivery com retry |
| `task_manager.py` | `app/shared/async_processing/task_manager.py` | DomainTaskManager singleton, asyncio in-process |
| `priority_calculator.py` | `app/shared/async_processing/priority_calculator.py` | PriorityCalculator: 1=urgente → 5=baixo |

### Integration points

- `app/jobs/drift_job.py` → `app/shared/observability/drift_alert_service.py` → evaluate_and_alert()
- `app/domains/ai/services/ragas_evaluation_service.py` → chamada diária via `ragas.evaluate_batch`
- `app/shared/learning/learning_loop_service.py` → wrapped como Celery task
- `app/shared/resilience/dlq_service.py` → `LIATask.on_failure()` persiste falhas definitivas
- `app/api/v1/agent_registry_watcher.py` → hot-reload a cada minuto via `agents.registry.check_reload`
- `app/core/agent_registry_watcher.py` → watcher de `agents_registry.yaml`

---

## Lógica IN → OUT

### 1. Celery App — configuração central

**Entry points:**
```bash
celery -A app.core.celery_app worker --loglevel=info   # Worker
celery -A app.core.celery_app beat --loglevel=info     # Beat (agendador)
```

**Broker URL resolution (prioridade):**
1. `CELERY_BROKER_URL` env var (override explícito, máxima precedência)
2. `BROKER_BACKEND` env var: `redis` → `settings.REDIS_URL` | `rabbitmq` → `settings.RABBITMQ_URL` | `pubsub` → error + fallback Redis
3. Default: `settings.REDIS_URL`

**Result backend resolution (prioridade):**
1. `CELERY_RESULT_BACKEND` env var
2. `settings.CELERY_RESULT_BACKEND`
3. `settings.REDIS_URL` (sempre Redis — RabbitMQ não é adequado para results)

**Configurações:**
```python
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "America/Sao_Paulo"
enable_utc = True
task_track_started = True
result_expires = 3600  # 1 hora
```

### 2. 4 Filas com prioridade

| Fila | Queue args | Prioridade padrão | Task routes |
|------|:----------:|:----------------:|-------------|
| `sourcing_high` | `x-max-priority: 10` | 8 | `agents.sourcing.*` |
| `evaluation_normal` | `x-max-priority: 10` | 5 | `agents.screening.*`, `agents.pipeline.*`, `agents.wsi_interview.*`, `agents.triagem.*`, `ragas.*`, `wsi.*` |
| `vagas_normal` | `x-max-priority: 10` | 4-5 | `agents.wizard.*`, `agents.kanban.*`, `agents.automation.*` |
| `onboarding_low` | `x-max-priority: 10` | 3 | `agents.policy.*`, `communication.email.*`, `followup.*`, `feedback.*`, `drift.run_batch` |
| `celery` | — | — | default (sem rota explícita) |

**Exchange:** `lia_tasks` (direct), routing key = nome da fila.

### 3. LIATask — base class para todas as tasks

```python
class LIATask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Chamado quando retries se esgotam — persiste na DLQ Redis."""
        queue = (self.request.delivery_info or {}).get("routing_key", "celery")
        await dlq_service.push_failure(
            task_name=self.name,
            queue=queue,
            args=list(args),
            kwargs=dict(kwargs),
            exc=exc,
            tb=tb_str,
            retries=self.request.retries,
            company_id=kwargs.get("company_id"),  # para auditoria multi-tenant
        )
        # DLQ push é fail-safe — falha silenciosa se dlq_service indisponível
```

**Uso:** `@celery_app.task(base=LIATask, ...)` em `app/jobs/tasks/*.py`.

### 4. PII Masking nos workers (LGPD)

```python
@signals.worker_process_init.connect
def _install_pii_masking_on_worker(**kwargs):
    """Instala PIIMaskingFilter em cada processo filho do worker Celery."""
    from app.shared.pii_masking import install_global_pii_masking
    install_global_pii_masking()
    # Fail-safe: nunca bloqueia inicialização do worker
```

**Por que existe:** O modelo prefork do Celery cria novos processos que **NÃO herdam** filtros instalados no processo pai (`app/main.py`). Esta signal garante conformidade LGPD nos logs de cada worker child.

### 5. Beat Schedule — 19 tarefas agendadas

> **Auditoria SSH 2026-04-24:** celery_app.py tem **19** entradas em `beat_schedule` (verificado via `grep -c '"task":'`). A tabela abaixo reflete o count real.

Todas as horas são em **UTC** (timezone do Beat). Horários em Brasília (UTC-3) são anotados como referência.

| Task | Cron UTC | Horário Brasília | Queue | Expires |
|------|----------|:--------:|-------|:-------:|
| `drift.run_batch` | `hour=9, min=0` (diário) | 06h | onboarding_low | 3600s |
| `golden_drift.run_check` | `hour=10, min=0` (diário) | 07h | evaluation_normal | 7200s |
| `insights.aggregate_all` | `hour=8, min=0` (diário) | 05h | evaluation_normal | 7200s |
| `fewshot.evolve` | `hour=9, min=0` (diário) | 06h | evaluation_normal | 7200s |
| `audit.apply_lifecycle_policy` | `day_of_month=1, hour=6, min=0` (mensal) | 03h | — | 3600s |
| `lgpd.run_cleanup_daily` | `hour=5, min=0` (diário) | 02h | — | 7200s |
| `conversation.ttl_cleanup` | `hour=6, min=0` (diário) | 03h | — | 7200s |
| `briefing.send_daily` | `hour=9, min=0` (diário) | 06h | — | 3600s |
| `followup.process_pending` | `minute=0` (hora a hora) | — | — | 3500s |
| `wsi.check_abandoned` | `minute=0, hour="*/4"` (a cada 4h) | — | — | 14000s |
| `feedback.process_pending_sends` | `minute=30, hour="*/2"` (a cada 2h) | — | — | 7000s |
| `ragas.evaluate_batch` | `hour=3, min=0` (diário) | 00h | — | 7200s |
| `routing.recompute_adjustments` | `hour=7, min=0` (diário) | 04h | — | 3600s |
| `data.retention.run` | `day_of_month=1, hour=2, min=0` (mensal) | 23h-30 | — | 7200s |
| `agents.registry.check_reload` | `minute="*/1"` (a cada 1 min) | — | — | — |
| `rag.rebuild_all_domains` | `hour=4, min=0` (diário) | 01h | — | 7200s |
| `digest.send_weekly` | semanal | — | — | — |
| `ml.feedback.recompute_active_jobs` | semanal | — | — | — |
| `memory.compress_old_episodes` | `hour=3, min=0` (diário) | 00h | — | — |

**Sequência diária relevante:**
- 00h Brasília: `ragas.evaluate_batch` (avaliação qualidade LIA)
- 02h Brasília: `lgpd.run_cleanup_daily` (LGPD cleanup)
- 03h Brasília: `conversation.ttl_cleanup` (TTL de conversas — LGPD Art. 18)
- 04h Brasília: `routing.recompute_adjustments` (E9 Adaptive Routing)
- 05h Brasília: `insights.aggregate_all` (GlobalInsights)
- 06h Brasília: `drift.run_batch` + `fewshot.evolve` + `briefing.send_daily`
- 07h Brasília: `golden_drift.run_check`

### 6. drift_job.py — batch drift check

```python
async def run_drift_check_all_companies(
    db: AsyncSession,
    notify_user_id: str | None = None,
) → {"checked": int, "drifted": int, "errors": int}:
    # Itera CompanyProfile.is_active == True
    # Para cada: drift_alert_service.evaluate_and_alert(db, company.id)
    # Erros individuais capturados (summary["errors"]++) — não interrompem o batch
```

Celery-ready: "pode ser wrappado em `@celery.task` em Ciclo F sem alterações."

### 7. scheduled_reports.py — feature flag obrigatório

**Segurança:** `ENABLE_SCHEDULED_REPORTS=true` env var obrigatório para enviar relatórios. Disabled por default para prevenir envios acidentais em dev/staging.

Suporta APScheduler (para testes locais) e Celery Beat (produção).

### 8. DomainTaskManager — asyncio in-process

Para operações bulk elegíveis — **não usa Celery**, processa dentro do processo FastAPI via asyncio.

```python
ASYNC_ELIGIBLE_ACTIONS = {
    "sourcing": ["bulk_search", "mass_outreach", "import_candidates"],
    "cv_screening": ["bulk_screen", "batch_evaluate", "full_pipeline_screen"],
    "communication": ["mass_email", "mass_whatsapp", "bulk_notification"],
    "analytics": ["generate_full_report", "export_large_dataset", "predictive_analysis"],
    "ats_integration": ["bulk_sync", "full_import", "full_export"],
    "automation": ["batch_stage_transition", "run_automation_rules"],
    "job_management": ["bulk_publish", "batch_update_jobs"],
    "interview_scheduling": ["batch_schedule"],
    "recruiter_assistant": ["generate_daily_briefing"],
}
```

**Singleton:**
```python
manager = DomainTaskManager.get_instance(
    max_concurrent_per_domain=3,  # default
    max_queue_size=100,            # default
)
task_id = await manager.submit_task(
    domain_id="sourcing",
    action_id="bulk_search",
    params={"skills": ["python"], "limit": 500},
    user_id="user_123",
    priority=TaskPriority.HIGH,
)
status = manager.get_task_status(task_id)
```

**reset_instance():** para cleanup em testes (`DomainTaskManager.reset_instance()`).

### 9. PriorityCalculator

```python
# Prioridade: 1=mais urgente, 5=mais baixa

_BASE_PRIORITIES = {
    "cv_screening": 2,  "sourcing": 2,
    "followup": 3,      "wsi_abandoned": 3,
    "notification": 3,
    "report": 5,        "analytics": 5,
}

def compute(task_type, metadata=None) → int:
    # Escalação para 1: sourcing com deadline_days < 7
    # Escalação para 2: cv_screening com backlog > 50
    # Demais: base priority
```

---

## Instruções para Claude Code / Cursor

### "Implementa Background Jobs no v5"

```
1. Criar libs/config/lia_config/celery_app.py (canonical)
   - LIATask base class: on_failure() → dlq_service.push_failure() + company_id
   - worker_process_init signal → install_global_pii_masking() em cada worker child
   - 4 queues: sourcing_high/evaluation_normal/vagas_normal/onboarding_low (x-max-priority: 10)
   - task_routes dict com prefixos por domínio
   - beat_schedule com 19 entries (ver tabela acima)
   - _get_celery_broker_url(): CELERY_BROKER_URL → BROKER_BACKEND → REDIS_URL
   - _get_celery_result_backend(): sempre Redis (mesmo com RabbitMQ broker)
   - timezone = "America/Sao_Paulo", enable_utc = True

2. Criar app/core/celery_app.py (shim)
   from lia_config.celery_app import celery_app  # noqa: F401

3. Criar app/jobs/tasks/ (10 módulos)
   - agents.py: tasks de agentes (execute por domain)
   - communication.py: email/whatsapp tasks
   - compliance.py: audit, lgpd, data retention tasks
   - ml.py: ragas, drift, fewshot tasks
   - followup.py: followup de convites WSI
   - feedback.py: feedback pending sends
   - memory.py: conversation TTL cleanup
   - voice.py: voice processing tasks
   - _utils.py: helpers compartilhados

4. Criar app/jobs/drift_job.py
   - run_drift_check_all_companies() Celery-ready
   - Itera CompanyProfile.is_active==True
   - Erros individuais não interrompem batch

5. Criar app/shared/async_processing/task_manager.py
   - DomainTaskManager singleton + ASYNC_ELIGIBLE_ACTIONS dict
   - max_concurrent_per_domain=3, max_queue_size=100
   - submit_task(), get_task_status(), register_handler()

6. Criar app/shared/async_processing/priority_calculator.py
   - PriorityCalculator.compute(): 1=urgente → 5=baixo
   - Escalação: sourcing deadline<7d → 1; cv_screening backlog>50 → 2

7. app/jobs/scheduled_reports.py
   - ENABLE_SCHEDULED_REPORTS=true como feature flag obrigatório
   - Desabilitado por default

8. Wiring em app/main.py lifespan:
   - celery_app importado para registrar tasks
   - DomainTaskManager.get_instance() iniciado no startup
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Background Jobs — R4
- Canonical: libs/config/lia_config/celery_app.py; shim: app/core/celery_app.py
- 4 filas: sourcing_high(8) > evaluation_normal(5) > vagas_normal(4-5) > onboarding_low(3)
- LIATask base OBRIGATÓRIA: falhas → DLQ Redis com company_id
- PII masking instalado em cada worker via worker_process_init signal
- Beat schedule: timezone America/Sao_Paulo, UTC timestamps internos
- ENABLE_SCHEDULED_REPORTS=true obrigatório para reports em produção
- DomainTaskManager: asyncio in-process para bulk ops elegíveis (9 domains × ações)
- Celery result backend: SEMPRE Redis mesmo quando broker é RabbitMQ
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|--------------|
| `beat_schedule` entries | Adicionar/remover schedules do v5 |
| `task_routes` prefixos | Ajustar nomes de task conforme arquitetura v5 |
| `ASYNC_ELIGIBLE_ACTIONS` | Expandir com actions do v5 |
| `DOMAIN_QUEUES` prioridades | Ajustar SLA por domínio |
| `result_expires=3600` | Aumentar se v5 precisa results disponíveis por mais tempo |
| `max_concurrent_per_domain=3` | Ajustar conforme capacidade do servidor v5 |
| Sequência de horários do Beat | Ajustar timezone se v5 serve outros países |
| `scheduled_reports.py` schedules | Adaptar horários de briefing |

### NÃO pode adaptar (compliance ou operacional)

| Item | Razão |
|------|-------|
| `worker_process_init` → `install_global_pii_masking()` | LGPD Art. 46 — logs de workers não podem conter PII; prefork não herda do processo pai |
| `company_id` em `LIATask.on_failure()` kwargs | Multi-tenancy — DLQ deve incluir company_id para auditoria e reprocessamento isolado |
| `lgpd.run_cleanup_daily` e `conversation.ttl_cleanup` no Beat | LGPD Art. 18 (direito ao esquecimento) — remoção automática conforme TTL configurado |
| `audit.apply_lifecycle_policy` no Beat | Requisito de auditoria EU AI Act Art. 12 — retention policy automática |
| `ragas.evaluate_batch` no Beat | Monitoramento contínuo de qualidade — remover cria blind spot de degradação silenciosa |
| `ENABLE_SCHEDULED_REPORTS=true` obrigatório | Previne envio acidental de emails em dev/staging (problema de compliance de email marketing) |
| DLQ fail-safe em `on_failure()` | Task não pode falhar por causa de falha na DLQ — resultado seria silêncio total |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `LIATask` como base class de todas as tasks — DLQ habilitado para falhas definitivas
- [ ] **(P0)** `worker_process_init` signal instala `PIIMaskingFilter` em cada worker child
- [ ] **(P0)** `lgpd.run_cleanup_daily` e `conversation.ttl_cleanup` no Beat Schedule
- [ ] **(P0)** `ENABLE_SCHEDULED_REPORTS=true` documentado em `.env.example` como opt-in
- [ ] **(P1)** 4 queues com `x-max-priority: 10` configuradas
- [ ] **(P1)** `task_routes` cobre todos os domínios de agentes
- [ ] **(P1)** Beat schedule com timezone `America/Sao_Paulo` e `enable_utc=True`
- [ ] **(P1)** `drift.run_batch` no beat schedule com `expires=3600` (não re-executa se atrasado)
- [ ] **(P1)** `ragas.evaluate_batch` diário (00h Brasília)
- [ ] **(P1)** `agents.registry.check_reload` a cada 1 minuto (hot-reload sem restart)
- [ ] **(P2)** `DomainTaskManager.reset_instance()` disponível para cleanup em testes
- [ ] **(P2)** `PriorityCalculator` com escalação para sourcing deadline<7d
- [ ] **(P2)** `result_expires=3600` documentado — results não ficam no Redis indefinidamente

---

## Gotchas e erros comuns

### 1. Worker child não tem PIIMaskingFilter sem o signal

**Problema:** `app/main.py` instala `PIIMaskingFilter` no processo FastAPI. Workers Celery (prefork) são processos separados que NÃO herdam o filtro. Logs dos workers teriam PII (emails, nomes de candidatos).

**Correto:** `worker_process_init` signal em `celery_app.py` — instala o filtro em cada processo filho na inicialização. Verificar com `grep -r "install_global_pii_masking" app/jobs/`.

### 2. RabbitMQ como result backend quebra polling de status

**Problema:** Se `CELERY_RESULT_BACKEND` apontar para RabbitMQ, resultado de tasks são consumidos (AMQP semantics) — o segundo `task.get()` não encontra o resultado. Redis mantém resultados em key-value (não destrutivo).

**Correto:** `_get_celery_result_backend()` sempre retorna Redis, mesmo quando broker é RabbitMQ.

### 3. Beat reinicia tasks com `expires` vencido silenciosamente

**Problema:** Se o Beat ficou down e o `drift.run_batch` (expires=3600) ficou 2 horas atrasado, ele NÃO executa ao voltar — `expires` faz a task ser descartada pela fila. O drift não roda.

**Comportamento esperado por design:** melhor não executar drift com 2h de atraso do que executar múltiplas vezes em sequência (flood de alertas). Monitorar Beat heartbeat separadamente.

### 4. `DomainTaskManager.get_instance()` retém estado entre testes

**Problema:** Singleton retido entre tests — se um test submete task e outro test faz `get_instance()`, herda estado do anterior.

**Correto:** Chamar `DomainTaskManager.reset_instance()` em `teardown` de cada teste que usa o manager.

### 5. `task_track_started=True` cria overhead com muitas tasks curtas

**Problema:** `task_track_started=True` grava estado STARTED no Redis para cada task. Com tasks de 50ms (ex: `agents.registry.check_reload` a cada minuto), o overhead de write pode ser significativo.

**Correto:** Para tasks de hot-reload frequentes, considerar `@celery_app.task(track_started=False)` override individual.

### 6. `BROKER_BACKEND=pubsub` usa Redis como fallback (silencioso)

**Problema:** Se `BROKER_BACKEND=pubsub` e `CELERY_BROKER_URL` não está definido, o sistema usa Redis como fallback **silenciosamente** (apenas um log de error). Workers iniciam normalmente mas não estão no backend esperado.

**Correto:** Em produção com `BROKER_BACKEND=pubsub`, `CELERY_BROKER_URL` deve ser obrigatório. Validar no startup via `validate_llm_circuit_configs()` pattern ou check customizado.

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| `test_lia_task_on_failure_pushes_dlq` | `tests/unit/test_celery_app.py` | Task falha definitivamente → DLQ recebe `{task_name, company_id, exc}` |
| `test_lia_task_dlq_failsafe` | `tests/unit/test_celery_app.py` | DLQ service down → on_failure() não levanta exception |
| `test_pii_masking_on_worker_init` | `tests/unit/test_celery_app.py` | Signal `worker_process_init` instala PIIMaskingFilter |
| `test_broker_url_resolution_redis` | `tests/unit/test_celery_app.py` | BROKER_BACKEND=redis → settings.REDIS_URL |
| `test_broker_url_resolution_explicit` | `tests/unit/test_celery_app.py` | CELERY_BROKER_URL override tem precedência |
| `test_result_backend_always_redis` | `tests/unit/test_celery_app.py` | BROKER_BACKEND=rabbitmq → result backend = Redis |
| `test_beat_schedule_lgpd_tasks_present` | `tests/unit/test_celery_app.py` | beat_schedule contém lgpd.run_cleanup_daily + conversation.ttl_cleanup |
| `test_beat_schedule_timezone` | `tests/unit/test_celery_app.py` | timezone="America/Sao_Paulo", enable_utc=True |
| `test_drift_job_all_companies` | `tests/unit/test_drift_job.py` | 3 empresas → checked=3; 1 com drift → drifted=1 |
| `test_drift_job_error_isolation` | `tests/unit/test_drift_job.py` | Erro em 1 empresa → outras continuam; errors=1 |
| `test_scheduled_reports_disabled_by_default` | `tests/unit/test_scheduled_reports.py` | Sem ENABLE_SCHEDULED_REPORTS=true → não envia |
| `test_domain_task_manager_singleton` | `tests/unit/test_task_manager.py` | get_instance() retorna mesma instância |
| `test_domain_task_manager_reset` | `tests/unit/test_task_manager.py` | reset_instance() → próximo get_instance() cria nova |
| `test_priority_calculator_escalation` | `tests/unit/test_priority_calculator.py` | sourcing + deadline_days=5 → prioridade 1 |
| `test_task_queue_max_concurrent` | `tests/unit/test_task_manager.py` | submit 5 tasks, max_concurrent=3 → 3 ativas + 2 na fila |

---

## Referências

### Código (SSoT)
- `libs/config/lia_config/celery_app.py` — Celery app canonical, LIATask, beat_schedule
- `app/core/celery_app.py` — shim de backward compat
- `app/jobs/celery_tasks.py` — facade para tasks
- `app/jobs/tasks/` (10 módulos) — definições de tasks por domínio
- `app/jobs/drift_job.py` — drift batch
- `app/jobs/scheduled_reports.py` — reports (feature-flagged)
- `app/shared/async_processing/task_manager.py` — DomainTaskManager singleton
- `app/shared/async_processing/priority_calculator.py` — PriorityCalculator

### Bundles e Guides
- Reconstruction Guide `RESILIENCE_LEARNING` Parte C — Celery + BrokerInterface overview
- Thematic Doc R2 (`R2_LEARNING_LOOP_AND_AB_TESTING.md`) — `ragas.evaluate_batch`, `analyze_patterns()` como Celery tasks
- Thematic Doc R3 (`R3_MESSAGING_AND_EVENTS.md`) — `DOMAIN_QUEUES` e filas de agentes
- Thematic Doc C7 (`C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md`) — `audit.apply_lifecycle_policy` mensal
- Thematic Doc C3 (`C3_LGPD_CONSENT_AND_DATA_SUBJECT.md`) — `lgpd.run_cleanup_daily`

### Regulatório
- **LGPD Art. 18** — direito ao esquecimento mapeado em `conversation.ttl_cleanup` + `lgpd.run_cleanup_daily`
- **EU AI Act Art. 12** — registro de operações de sistema de alto risco; `audit.apply_lifecycle_policy` implementa retention automática
