# GCP Migration Guide — Redis → Cloud Pub/Sub / Cloud Tasks

**Status:** Planejado (sprint de infra dedicada)  
**Autor:** Task #67 — Infraestrutura Broker Abstraction  
**Última atualização:** 2026-04-07

---

## Contexto

O Celery usa Redis como broker de mensageria (fila de tasks). Para migrar para GCP,
o destino natural é **Cloud Tasks** (Celery tasks assíncronas) ou **Cloud Pub/Sub**
(eventos de plataforma, publish/subscribe).

A camada de abstração `BrokerInterface` (`app/shared/messaging/broker_interface.py`)
foi criada especificamente para que essa migração seja uma mudança de configuração,
não uma reescrita.

---

## Arquitetura Atual (On-Prem)

```
  LIA App ──► RedisBroker (BROKER_BACKEND=redis)
                  │
                  ├── Celery Worker (sourcing_high / evaluation_normal / vagas_normal / onboarding_low)
                  ├── Rate Limiter (redis)
                  ├── DLQ Service (redis)
                  └── Token Budget (redis)

  LIA Chat ──► RabbitMQBroker (aio-pika, exchange=lia_agent_chat)
                  │
                  └── WebSocket Gateway → Agent Workers
```

---

## Passo a Passo de Migração GCP

### Fase 1 — Preparação (sem downtime)

1. **Instalar google-cloud-pubsub**
   ```bash
   pip install google-cloud-pubsub google-cloud-tasks
   ```

2. **Implementar `PubSubBroker` real** em `app/shared/messaging/broker_interface.py`:
   ```python
   class PubSubBroker(BrokerInterface):
       async def publish(self, topic: str, message: dict) -> str:
           from google.cloud import pubsub_v1
           publisher = pubsub_v1.PublisherClient()
           topic_path = publisher.topic_path(self._project_id, topic)
           data = json.dumps(message).encode("utf-8")
           future = publisher.publish(topic_path, data)
           return future.result()  # message_id

       async def consume(self, topic: str) -> dict | None:
           # Usar Pub/Sub pull ou push subscription
           ...

       async def health_check(self) -> dict:
           from google.cloud import pubsub_v1
           client = pubsub_v1.PublisherClient()
           topics = list(client.list_topics(project=f"projects/{self._project_id}"))
           return {"status": "healthy", "backend": "pubsub", "project": self._project_id}
   ```

3. **Criar tópicos no GCP**:
   ```bash
   gcloud pubsub topics create sourcing_high
   gcloud pubsub topics create evaluation_normal
   gcloud pubsub topics create vagas_normal
   gcloud pubsub topics create onboarding_low
   gcloud pubsub subscriptions create sourcing_high-sub --topic=sourcing_high
   ```

### Fase 2 — Configuração (sem downtime)

4. **Setar variáveis de ambiente**:
   ```env
   BROKER_BACKEND=pubsub
   GOOGLE_CLOUD_PROJECT=meu-projeto-gcp
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

5. **Para Celery scheduler** (separado do BROKER_BACKEND):
   ```env
   CELERY_BROKER_URL=redis://redis-gcp:6379/0   # Manter Redis para Celery inicialmente
   # OU migrar para Cloud Tasks:
   CELERY_BROKER_URL=gcpubsub://projects/meu-projeto/topics/celery
   ```
   Nota: Celery tem suporte nativo a GCP Pub/Sub via `celery-gcp-backend`.

### Fase 3 — Validação

6. **Checklist de validação**:
   - [ ] `GET /health` → `components.broker.status == "healthy"` com `backend: "pubsub"`
   - [ ] `GET /health` → `components.broker.project_id` = projeto correto
   - [ ] Tasks Celery fluindo pelas 4 filas (sourcing_high, evaluation_normal, vagas_normal, onboarding_low)
   - [ ] Chat WebSocket funcionando (RabbitMQ ou migrar também para Pub/Sub)
   - [ ] DLQ funcionando (pode manter Redis ou migrar para Cloud Firestore)
   - [ ] Token Budget funcionando (pode manter Redis ou migrar para Cloud Memorystore)
   - [ ] `pytest -m "not very_hard"` sem erros
   - [ ] Latência P99 < 2s para tasks de evaluation_normal

7. **Rollback**:
   ```env
   BROKER_BACKEND=redis   # Uma linha de config → rollback instantâneo
   ```

---

## Estimativa de Custo (GCP Cloud Pub/Sub)

| Componente | Volume estimado | Custo/mês (USD) |
|------------|----------------|-----------------|
| Pub/Sub messages (tasks) | ~500k/mês | ~$0.04 |
| Pub/Sub throughput | ~1 GB/mês | ~$0.06 |
| Cloud Tasks (se usado) | ~100k/mês | ~$0.01 |
| Cloud Memorystore (Redis) | 1 GB tier | ~$35 |
| **Total estimado** | | **~$35-50/mês** |

> Nota: Cloud Memorystore (Redis gerenciado) é recomendado para manter
> compatibilidade com DLQ, Rate Limiter e Token Budget sem reescrita.

---

## Variáveis de Ambiente — Referência Completa

| Variável | Valor padrão | Descrição |
|----------|-------------|-----------|
| `BROKER_BACKEND` | `redis` | Backend da BrokerInterface (`redis`/`rabbitmq`/`pubsub`) |
| `REDIS_URL` | `redis://localhost:6379/0` | URL Redis (usado pelo Celery, cache, DLQ) |
| `CELERY_BROKER_URL` | _(usa REDIS_URL)_ | Override do broker Celery |
| `CELERY_RESULT_BACKEND` | _(usa REDIS_URL)_ | Override do result backend Celery |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | URL RabbitMQ (chat de agentes) |
| `GOOGLE_CLOUD_PROJECT` | _(não configurado)_ | Projeto GCP (obrigatório para pubsub) |
| `GOOGLE_APPLICATION_CREDENTIALS` | _(não configurado)_ | Service account JSON path |

---

## Arquivos Relevantes

- `app/shared/messaging/broker_interface.py` — BrokerInterface, RedisBroker, RabbitMQBroker, PubSubBroker stub
- `libs/config/lia_config/celery_app.py` — Celery app com `_get_celery_broker_url()` via factory
- `libs/config/lia_config/config.py` — `BROKER_BACKEND` em MessagingSettings
- `app/api/v1/system_health.py` — `/health` inclui `broker` health check
- `app/shared/messaging/rabbitmq_producer.py` — Producer RabbitMQ (chat)

---

## Ordem de Migração Recomendada

1. Cloud Pub/Sub para eventos de plataforma (platform_events.py)
2. Cloud Pub/Sub para broker da aplicação (BrokerInterface)
3. Cloud Memorystore (Redis gerenciado) para DLQ/Rate Limiter/Token Budget
4. Cloud Tasks para Celery scheduler (CELERY_BROKER_URL)
5. RabbitMQ → Cloud Pub/Sub para chat de agentes (RabbitMQBroker → PubSubBroker)

---

*Documento criado em: Task #67 — Infraestrutura Broker Abstraction & Test Health*
