# API Sync vs Async — Definição Formal

**Versão:** 1.0 | **Data:** 04/março/2026

---

## Regra de Ouro

> **Operações que levam > 2 segundos ou que dependem de sistemas externos com latência variável DEVEM ser assíncronas.**

---

## Operações SÍNCRONAS (REST direto, resposta < 2s)

O endpoint executa a lógica, aguarda o resultado e retorna na mesma requisição HTTP.

### CRUD e Consultas
| Operação | Endpoint | Latência esperada |
|----------|---------|-------------------|
| Criar/editar vaga | `POST/PUT /api/v1/job-vacancies/` | < 200ms |
| Atualizar candidato | `PUT /api/v1/candidates/{id}` | < 200ms |
| Mover candidato no pipeline | `POST /api/v1/pipeline/move` | < 500ms |
| Consultar status de vaga | `GET /api/v1/job-vacancies/{id}` | < 100ms |
| Perfil de candidato | `GET /api/v1/candidates/{id}` | < 200ms |
| Estatísticas/métricas | `GET /api/v1/analytics/kpis` | < 1s |

### Classificações e Ações Rápidas
| Operação | Endpoint | Latência esperada |
|----------|---------|-------------------|
| Intent routing (chat) | `POST /api/v1/chat/message` | < 2s |
| Score rápido (single candidate) | `POST /api/v1/screening/quick-score` | < 1s |
| Toggle guardrail | `PATCH /api/v1/guardrails/{id}/toggle` | < 100ms |
| Verificar elegibilidade | `POST /api/v1/screening/eligibility` | < 500ms |

---

## Operações ASSÍNCRONAS (Celery Queue + WebSocket, > 2s)

O endpoint enfileira a tarefa via Celery, retorna `AsyncJobResponse` imediatamente,
e o cliente acompanha progresso via WebSocket ou polling.

### Padrão de Resposta Assíncrona

```json
{
  "job_id": "celery-task-uuid",
  "status": "queued",
  "estimated_duration_seconds": 45,
  "websocket_url": "/ws/jobs/celery-task-uuid",
  "created_at": "2026-03-04T14:30:00Z"
}
```

### Inventário de Operações Assíncronas

| Operação | Task Celery | Endpoint | Duração estimada |
|----------|-------------|---------|------------------|
| Triagem em lote (N candidatos) | `agents.triagem.run` | `POST /api/v1/triagem/run-batch` | 30s – 5min |
| Entrevista WSI completa | `agents.wsi_interview.start` | `POST /api/v1/interviews/wsi/start` | 30min – 2h |
| Busca Pearch AI | `agents.sourcing.search` | `POST /api/v1/sourcing/search-async` | 30s – 2min |
| Email em massa | `communication.email.send_bulk` | `POST /api/v1/communication/email/bulk` | 30s – 10min |
| Drift check (todas empresas) | `drift.run_batch` | `POST /api/v1/drift/run-batch` | 5min – 30min |

---

## Decisão: Sync vs Async?

```
Operação envolve:
  └── Sistema externo com SLA variável? (Pearch, SendGrid, WhatsApp)
  │   └── SIM → ASYNC
  └── Agente LLM com múltiplas iterações?
  │   └── SIM → ASYNC (se > 2 iter previsíveis)
  └── Processamento em lote (> 1 item)?
  │   └── SIM → ASYNC
  └── Sessão interativa de longa duração? (entrevista WSI)
  │   └── SIM → ASYNC
  └── Caso contrário → SYNC
```

---

## WebSocket de Progresso

**Endpoint:** `ws://host/ws/jobs/{job_id}`

**Mensagens emitidas:**

```json
// Início
{ "type": "status", "job_id": "...", "status": "processing", "progress": 0, "message": "Iniciando triagem..." }

// Durante execução (emitido a cada candidato processado no lote)
{ "type": "progress", "job_id": "...", "progress": 45, "message": "22/50 candidatos processados" }

// Conclusão
{ "type": "completed", "job_id": "...", "progress": 100, "result": { ... } }

// Erro
{ "type": "failed", "job_id": "...", "error": "Mensagem de erro", "retrying": true }
```

**Fallback para polling:**
`GET /api/v1/jobs/{job_id}/status` → `AsyncJobStatusResponse`

---

## Configuração Celery

```python
# app/core/celery_app.py
beat_schedule = {
    "drift-run-batch-daily": {
        "task": "drift.run_batch",
        "schedule": crontab(hour=6, minute=0),  # 06h Brasília (09h UTC)
    }
}
```

**Worker:**
```bash
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
celery -A app.core.celery_app beat --loglevel=info
```

**Inspect tasks registradas:**
```bash
celery -A app.core.celery_app inspect registered
# Esperado: drift.run_batch, agents.wsi_interview.start, agents.triagem.run,
#           agents.sourcing.search, communication.email.send_bulk
```

---

## Frontend — Tratamento de Operações Async

1. Disparar operação → receber `AsyncJobResponse` com `job_id` e `websocket_url`
2. Abrir conexão WebSocket em `websocket_url`
3. Exibir `AsyncJobProgress` component (barra de progresso + mensagem)
4. Em caso de falha de WebSocket → fallback para polling a cada 3s
5. Ao receber `type: "completed"` → fechar WebSocket, exibir resultado

Componente: `plataforma-lia/src/components/async/AsyncJobProgress.tsx`
