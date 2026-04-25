# Theme I5 — Observability & Agent Quality

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/app/api/v1/observability.py` + `app/shared/observability/` no Replit

---

## O que é este tema

A camada de **observabilidade** da LIA cobre três sub-sistemas complementares:

1. **Execution Logs** — rastreia cada invocação de agente: domain, tools chamadas, duração, confiança, reasoning chain → tabela `agent_execution_records` (`ExecutionLogStore`)
2. **Agent Quality Dashboard** — endpoint que agrega dados de audit_logs + calibration_events + fairness_audit_log para o frontend `Agent Control` tab
3. **Model Drift Detection** — monitora 4 gatilhos de drift (score, aprovação, custo, latência) comparando janela de 7 dias vs. baseline; alerta via `drift_alert_service`; roda como Celery job (`drift_job.py`)
4. **Compliance Observability API** — endpoints REST para AI inference logs, data access logs, consent records, incident reports, model evaluations, compliance controls, bias audits
5. **Sentry** — integração com PII scrubbing antes de enviar exceções (before_send hook)

**Boundary com temas irmãos:**
- **I1 Agent Architecture** — `ExecutionLogStore` é alimentado pelo `AuditCallback` (que captura invocações do LangGraph)
- **C1 Fairness** — `fairness_audit_log` alimenta o Agent Quality Dashboard; BiasAuditService alimenta fairness reports
- **C7 Audit Trail** — audit_service.py persiste os logs que observability API consulta
- **R4 Background Jobs** — `drift_job.py` é um Celery worker (Celery-ready)

---

## Arquivos conectados (11 Python)

### Camada Código (11 arquivos Python)

**Execution logging:**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `execution_log_store.py` | `libs/agents-core/lia_agents_core/execution_log_store.py` | 204 | `AgentExecutionRecord` SQLAlchemy model + `ExecutionLogStore.save()` |
| `observability.py (lib)` | `libs/agents-core/lia_agents_core/observability.py` | — | `ReActObserver` — observer pattern para eventos do ReAct loop |

**Quality dashboard:**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `agent_quality_dashboard.py` | `app/api/v1/agent_quality_dashboard.py` | 234 | `/analytics/agent-quality-dashboard` — agrega audit + calibration + fairness |
| `fairness_reports.py` | `app/api/v1/fairness_reports.py` | 374 | Endpoints de relatórios de fairness por período e domínio |

**Drift detection:**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|-----------------|
| `model_drift_service.py` | `app/shared/observability/model_drift_service.py` | 4 triggers de drift: score, aprovação, custo, latência P95 |
| `drift_alert_service.py` | `app/shared/observability/drift_alert_service.py` | `DriftAlertService.evaluate_and_alert()` — avalia + notifica |
| `drift_job.py` | `app/jobs/drift_job.py` | `run_drift_check_all_companies()` — Celery-ready |
| `golden_drift_monitor.py` | `app/services/golden_drift_monitor.py` | `BaselineManager` — golden scenarios baseline para drift qualitativo |

**Compliance observability API:**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `observability.py (api)` | `app/api/v1/observability.py` | — | 15+ endpoints REST: AI inference logs, data access logs, consent, incidents, model evaluations, compliance controls, bias audits |
| `observability_repository.py` | `app/domains/observability/repositories/observability_repository.py` | — | `ObservabilityRepository` — queries aos modelos de observabilidade |
| `sentry.py` | `app/core/sentry.py` | 124 | `init_sentry()` + `_before_send()` PII scrubbing (email, CPF, phone) |

### Integration points

- **AuditCallback** (C7) alimenta `ExecutionLogStore` via `save()` após cada invocação LangGraph
- **FairnessGuard** (C1) gera entradas em `fairness_audit_log` que Agent Quality Dashboard consulta
- **BiasAuditService** (C1) gera `bias_audit_reports` que fairness_reports endpoint expõe
- **Celery beat** (R4) chama `run_drift_check_all_companies()` periodicamente
- **AdminUI** consome `/analytics/agent-quality-dashboard` (Agent Control tab)
- **Sentry SDK** inicializado em `main.py` via `init_sentry()` com before_send PII hook

---

## Lógica IN → OUT

### AgentExecutionRecord — execution log per invocation

```python
# libs/agents-core/lia_agents_core/execution_log_store.py
class AgentExecutionRecord(Base):
    __tablename__ = "agent_execution_records"
    
    id                 = UUID (PK)
    session_id         = String(255), indexed
    company_id         = String(255), indexed  ← multi-tenancy
    user_id            = String(255)
    domain             = String(100)           # "pipeline", "sourcing", etc.
    agent_class        = String(255)           # "PipelineTransitionAgent"
    user_message       = Text (nullable)
    agent_response     = Text (nullable)
    total_duration_ms  = Float
    total_iterations   = Integer
    tools_called       = JSON                  # lista de tool names
    tools_succeeded    = Integer
    tools_failed       = Integer
    final_confidence   = Float                 # 0.0-1.0 (compute_confidence)
    reasoning_chain    = JSON                  # iterations list
    stage_before       = String(100) (nullable)
    stage_after        = String(100) (nullable)
    stage_transitioned = Boolean
    model_provider     = String(100) default="claude"
    created_at         = DateTime
    metadata_          = JSON (nullable)

class ExecutionLogStore:
    async def save(self, log_data: dict, company_id: str, user_id: str) -> AgentExecutionRecord:
        # Cria e persiste o record via AsyncSessionLocal
```

### Model Drift Detection — 4 triggers

```python
# app/shared/observability/model_drift_service.py
# Compara janela recente (7 dias) vs baseline (7 dias anteriores)

# Thresholds (screening-compliance §7):
SCORE_DRIFT_THRESHOLD    = 0.5    # variação absoluta no score médio WSI
APPROVAL_DRIFT_THRESHOLD = 0.10   # variação percentual na taxa de aprovação (10 p.p.)
COST_DRIFT_THRESHOLD     = 0.20   # variação relativa no custo (20%)
LATENCY_DRIFT_THRESHOLD  = 0.50   # variação relativa no P95 de latência (50%)
WINDOW_DAYS              = 7

@dataclass
class DriftTrigger:
    name: str             # "score_drift" | "approval_drift" | "cost_drift" | "latency_drift"
    baseline_value: float
    recent_value: float
    delta: float
    threshold: float
    triggered: bool
    description: str

# Sources de dados:
#   score/approval: lia_models.ai_consumption.AiConsumption + lia_models.observability.AIInferenceLog
#   latency:        lia_models.observability.AIInferenceLog
#   cost:           lia_models.ai_consumption.AiConsumption
```

### Drift Job — Celery-ready

```python
# app/jobs/drift_job.py
async def run_drift_check_all_companies(
    db: AsyncSession,
    notify_user_id: str | None = None,
) -> dict:
    """
    Itera todas as empresas ativas (CompanyProfile table).
    Chama drift_alert_service.evaluate_and_alert() para cada uma.
    Retorna: {checked: N, drifted: M, errors: K}
    
    Celery-ready: pode ser wrappado em @celery.task sem alterações.
    """
```

### Agent Quality Dashboard — aggregated view

```python
# app/api/v1/agent_quality_dashboard.py
GET /analytics/agent-quality-dashboard?period=7d  # 7d | 30d | 90d

# Agrega 4 fontes:
# 1. audit_logs (AuditService) — decisions, errors, confidence stats
# 2. calibration_events (CalibrationEvent) — divergences, weights
# 3. fairness_audit_log (FairnessGuard) — warnings, blocks count
# 4. Drift status (quantitative + qualitative):
async def _get_drift_status(company_id: str, db: AsyncSession) -> dict:
    # Quantitative: ModelDriftService.evaluate() → 4 DriftTriggers com alert_level
    # Qualitative:  BaselineManager.load() → golden scenario pass_rate por agente
    # Overall: worst-of-both (critical > warning > stable > unknown)
    return {
        "quantitative": {"alert_level": "stable|warning|critical", "triggers": [...]},
        "qualitative":  {"has_baseline": bool, "agents": {"pipeline": 0.95, ...}},
        "overall": "stable|warning|critical|unknown"
    }
```

### Compliance Observability API — 15+ endpoints

```python
# app/api/v1/observability.py
# Usa ObservabilityRepository para queries multi-tenant (sempre filtra por company_id)

# AI Inference Logs (EU AI Act Art. 12):
GET  /observability/ai-inference-logs?company_id=...
GET  /observability/ai-inference-logs/{log_id}
GET  /observability/ai-inference-stats

# Data Access Logs (LGPD Art. 37):
GET  /observability/data-access-logs
GET  /observability/data-access-stats

# Consent Records (LGPD Arts. 7-9):
GET  /observability/consent-records
POST /observability/consent-records
POST /observability/consent-records/{id}/revoke

# Incident Reports (SOC2/ISO27001):
GET  /observability/incident-reports
POST /observability/incident-reports
PUT  /observability/incident-reports/{id}
POST /observability/incident-reports/{id}/resolve

# Model Evaluations (AI Ethics):
GET  /observability/model-evaluations
GET  /observability/model-evaluations/{id}
GET  /observability/model-evaluations/summary

# Compliance Controls (ISO27001/SOC2):
GET  /observability/compliance-controls
PUT  /observability/compliance-controls/{id}
GET  /observability/compliance-summary

# Bias Audits (LGPD/EU AI Act):
POST /observability/bias-audits
POST /observability/bias-audits/{id}/publish
GET  /observability/bias-audits
GET  /observability/bias-audits/{id}
GET  /observability/bias-audits/summary
GET  /observability/dashboard           ← ObservabilityDashboardResponse
```

### Sentry — PII scrubbing

```python
# app/core/sentry.py
# PII patterns removidos antes de enviar ao Sentry:
_PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    (re.compile(r'\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}\b'), '[PHONE]'),
]

def init_sentry():
    # SENTRY_DSN vazio → log INFO + retorna False (sem exceção)
    # SDK não instalado → log WARNING + retorna False
    # Passa before_send=_before_send para scrubbing automático

def _before_send(event: dict, hint: dict) -> dict | None:
    # Scrub exception messages + breadcrumbs
    # Nunca descarta o evento — apenas sanitiza
```

### Side effects

- `ExecutionLogStore.save()` persiste em `agent_execution_records` table → I9
- `DriftAlertService.evaluate_and_alert()` pode disparar notificações via email/Teams (R3)
- `init_sentry()` configura Sentry SDK globalmente na startup

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Drift `alert_level = "critical"` | `DriftAlertService` notifica ops + alerta no dashboard |
| SENTRY_DSN ausente | `init_sentry()` retorna False silenciosamente (fail-open) |
| `ObservabilityRepository` query falha | Endpoint retorna 503 com `{"detail": "service unavailable"}` |
| `run_drift_check_all_companies` parcialmente falha | Continua outras empresas; retorna `{errors: N}` no dict |
| Golden baseline ausente | `_get_drift_status` retorna `{"has_baseline": False}` (não crash) |

---

## Instruções para Claude Code / Cursor

### "Implementa Observability no v5"

```
1. COPIE os arquivos de execution logging:
   cp libs/agents-core/lia_agents_core/execution_log_store.py → <v5>/libs/agents-core/...
   cp libs/agents-core/lia_agents_core/observability.py      → <v5>/libs/agents-core/...

2. CRIE migration para agent_execution_records:
   CREATE TABLE agent_execution_records (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     session_id VARCHAR(255) NOT NULL,
     company_id VARCHAR(255) NOT NULL,
     user_id VARCHAR(255) NOT NULL,
     domain VARCHAR(100) NOT NULL,
     agent_class VARCHAR(255) NOT NULL,
     user_message TEXT,
     agent_response TEXT,
     total_duration_ms FLOAT DEFAULT 0,
     total_iterations INT DEFAULT 0,
     tools_called JSONB DEFAULT '[]',
     tools_succeeded INT DEFAULT 0,
     tools_failed INT DEFAULT 0,
     final_confidence FLOAT DEFAULT 0,
     reasoning_chain JSONB DEFAULT '[]',
     stage_before VARCHAR(100),
     stage_after VARCHAR(100),
     stage_transitioned BOOL DEFAULT false,
     model_provider VARCHAR(100) DEFAULT 'claude',
     created_at TIMESTAMPTZ DEFAULT now(),
     metadata JSONB
   );
   CREATE INDEX ON agent_execution_records (company_id);
   CREATE INDEX ON agent_execution_records (session_id);

3. COPIE drift detection:
   cp app/shared/observability/model_drift_service.py
   cp app/shared/observability/drift_alert_service.py
   cp app/jobs/drift_job.py

4. CONFIGURE Celery beat (R4):
   CELERY_BEAT_SCHEDULE = {
       'drift-check-daily': {
           'task': 'app.jobs.drift_job.run_drift_check_all_companies',
           'schedule': crontab(hour=6, minute=0),  # 06:00 diário
       }
   }

5. INICIALIZE Sentry na startup (app/main.py):
   from app.core.sentry import init_sentry
   init_sentry()  # SENTRY_DSN env var controla ativação

6. CONFIGURE SENTRY_DSN no .env:
   SENTRY_DSN=https://xxx@sentry.io/yyy  # vazio = desativado

7. EXPONHA endpoints de observability:
   from app.api.v1 import observability, agent_quality_dashboard, fairness_reports
   app.include_router(observability.router)
   app.include_router(agent_quality_dashboard.router)
   app.include_router(fairness_reports.router)

8. VERIFIQUE:
   - pytest tests/unit/test_execution_log_store.py
   - pytest tests/unit/test_model_drift_service.py
   - pytest tests/integration/test_observability_api.py
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: Observability & Agent Quality (I5)

- **Execution logs:** `ExecutionLogStore.save()` — persiste invocações em `agent_execution_records`
- **Quality dashboard:** `/analytics/agent-quality-dashboard` — agrega audit + calibration + fairness
- **Drift detection:** 4 triggers (score±0.5, aprovação±10pp, custo±20%, latência P95±50%) — janela 7d
- **Drift job:** `run_drift_check_all_companies()` — Celery-ready, roda diário
- **Compliance API:** 15+ endpoints em `/observability/` — AI logs, consent, incidents, bias audits
- **Sentry:** `init_sentry()` na startup com PII scrubbing (email, CPF, phone) no before_send

Consultar `themes/infrastructure/I5_OBSERVABILITY.md`.
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Thresholds de drift (0.5/0.10/0.20/0.50 são sugestões; ajustar por produto)
- `WINDOW_DAYS` (7 é default; pode ser 14 ou 30)
- Destino de alertas de drift (email/Teams/Slack via `drift_alert_service`)
- Sentry DSN (vazio = desativado para dev)
- Campos adicionais em `AgentExecutionRecord.metadata_`
- Frequência do drift job (diário é mínimo; pode ser mais frequente)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| `company_id` em `AgentExecutionRecord` | Multi-tenancy — queries sempre filtradas por tenant | Cross-tenant data leak em análises de qualidade |
| PII scrubbing antes do Sentry | LGPD — exceções podem conter dados de candidatos | CPF/email de candidato enviado ao Sentry (terceiro) |
| `agent_execution_records` table | Base de dados para dashboard + debugging | Sem tabela = sem Agent Quality Dashboard |
| ObservabilityRepository filtra por `company_id` | Multi-tenancy em todos os endpoints de compliance | Empresa A vê logs de empresa B |
| AI inference logs (EU AI Act Art. 12) | Obrigatório por regulação para sistemas IA de alto risco | Não-conformidade com EU AI Act |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** Migration `agent_execution_records` criada e aplicada
- [ ] **(P0)** `ExecutionLogStore.save()` chamado pelo AuditCallback (C7) após cada invocação
- [ ] **(P0)** `init_sentry()` chamado na startup com `SENTRY_DSN` em env var
- [ ] **(P0)** PII scrubbing ativo no Sentry `before_send` (email, CPF, phone)
- [ ] **(P0)** AI inference logs endpoint `/observability/ai-inference-logs` ativo (EU AI Act Art. 12)
- [ ] **(P1)** `ModelDriftService` com 4 triggers configurados + thresholds calibrados
- [ ] **(P1)** `run_drift_check_all_companies()` em Celery beat (mínimo diário)
- [ ] **(P1)** `/analytics/agent-quality-dashboard` agregando as 4 fontes corretamente
- [ ] **(P1)** Bias audit endpoints ativos em `/observability/bias-audits/`
- [ ] **(P2)** Golden scenario baseline configurado para drift qualitativo
- [ ] **(P2)** `DriftAlertService` notificando ops via canal configurado (email/Slack/Teams)
- [ ] **(P2)** Compliance controls (`/observability/compliance-controls`) com ISO27001/SOC2 items

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| Dashboard vazio para tenant novo | `agent_execution_records` sem dados para o período | Normal para tenants novos; verificar que AuditCallback está salvando |
| Drift "critical" mesmo com sistema saudável | Threshold muito baixo para o produto | Calibrar `SCORE_DRIFT_THRESHOLD` e `APPROVAL_DRIFT_THRESHOLD` para o baseline real |
| Sentry recebe exceções com PII | `init_sentry()` não chamado na startup | Verificar linha no main.py; SENTRY_DSN deve estar setado |
| `ObservabilityRepository` lança 503 | DB connection timeout em queries complexas | Adicionar índices em `company_id` + `created_at` nos modelos de observabilidade |
| Drift job falha silenciosamente | `errors` no return dict não monitorado | Configurar alerta quando `errors > 0` no retorno do job |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| ExecutionLogStore.save() | `tests/unit/test_execution_log_store.py` | `save(log_data, company_id)` → record em DB com campos corretos |
| Drift detection triggers | `tests/unit/test_model_drift_service.py` | Score baseline 80 → recent 79 (delta 0.4 < 0.5) → não triggerado |
| Drift detection triggered | `tests/unit/test_model_drift_service.py` | Score baseline 80 → recent 74 (delta 0.6 > 0.5) → `triggered=True` |
| Drift job multi-company | `tests/unit/test_drift_job.py` | 3 empresas → `{checked: 3, drifted: 1, errors: 0}` |
| Sentry PII scrub | `tests/unit/test_sentry.py` | Exceção com CPF → `_before_send()` retorna evento com `[CPF]` |
| Quality dashboard endpoint | `tests/integration/test_agent_quality_dashboard.py` | GET com period=7d → response com drift_status + fairness_stats |
| AI inference logs multi-tenant | `tests/integration/test_observability_api.py` | Tenant A não vê logs de Tenant B |
| init_sentry sem DSN | `tests/unit/test_sentry.py` | `SENTRY_DSN=""` → `init_sentry()` retorna False sem exceção |

---

## Referências

### Bundles verbatim
- Nenhum YAML específico (tema é 100% código).

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §G (Observability)

### Cross-references
- **I1 Agent Architecture** — `AuditCallback` alimenta `ExecutionLogStore` + `ReActObserver`
- **C1 Fairness** — `fairness_audit_log` + `BiasAuditService` alimentam fairness_reports
- **C7 Audit Trail** — `audit_logs` table é consultada pelo Agent Quality Dashboard
- **I9 Data Layer** — Migration de `agent_execution_records` + índices
- **R3 Messaging** — `DriftAlertService` envia notificações via `UnifiedEventPublisher`
- **R4 Background Jobs** — `drift_job.py` roda como Celery worker

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
