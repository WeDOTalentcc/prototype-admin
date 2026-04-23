# Plano de Deploy GCP — WeDO Talent (Rails + Recruiter Agent)

Documento consolidado com a estrategia de deploy para producao no Google Cloud Platform.
Considera o cenario atual (0 clientes, 2 alpha entrando) com budget de ate ~$2.500-3.000/mes.
Foco: confiabilidade profissional, custo proporcional ao uso, e caminho de evolucao claro.

---

## Principio Arquitetural

**Compute descartavel, dados protegidos.**

Todo estado (dados, filas, cache, indices) fica em servicos managed. A VM roda apenas processos
stateless de compute (Sidekiq, Sneakers, Celery). Se a VM morrer, nada se perde — MIG recria em
2-3 min, processos sobem, reconectam nos servicos managed e continuam de onde pararam.

Os Cloud Runs continuam servindo requests HTTP normalmente durante o recovery da VM. O que para
sao so os jobs assincronos (que por definicao o usuario nao esta esperando na tela).

---

## Situacao Atual

| Componente | Onde esta hoje |
|---|---|
| Rails API (2 instancias) | Cloud Run |
| Frontend Nuxt | Cloud Run |
| Sidekiq (Rails workers) | VM fixa |
| Sneakers (RabbitMQ consumer) | VM fixa |
| Elasticsearch | VM fixa |
| Redis | VM fixa |
| RabbitMQ | VM fixa |
| PostgreSQL | Cloud SQL |
| Agent (Celery workers) | VM fixa |
| Interview AI (FastAPI + WS) | Ainda nao existe em prod |
| Evaluation API (Flask) | Ainda nao existe em prod |

**Problema:** Se a VM morrer, Sidekiq + ES + Redis + RabbitMQ + Agent workers = tudo para. Dados do ES podem se perder. Sem autohealing, sem redundancia. Recovery manual.

---

## Arquitetura Proposta — Fase 1 (0-2 clientes alpha)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GCP — southamerica-east1                              │
│                                                                         │
│  ┌─────────────────── Cloud Run (HTTP/Serverless) ──────────────────┐  │
│  │                                                                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────────┐  │  │
│  │  │ Rails    │ │ Rails    │ │ Interview AI │ │ Evaluation API │  │  │
│  │  │ API 1    │ │ API 2    │ │ (FastAPI+WS) │ │ (Flask)        │  │  │
│  │  │ min: 1   │ │ min: 0   │ │ min: 0       │ │ min: 0         │  │  │
│  │  └──────────┘ └──────────┘ └──────────────┘ └────────────────┘  │  │
│  │  ┌──────────┐                                                    │  │
│  │  │ Nuxt     │  ← LB automatico em cada Cloud Run                │  │
│  │  │ Front    │                                                    │  │
│  │  └──────────┘                                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│         ┌────────────────────┼─────────────────────┐                   │
│         │                    │                     │                   │
│  ┌──────▼───────┐    ┌──────▼───────┐     ┌───────▼──────┐           │
│  │ Cloud SQL    │    │ Memorystore  │     │ Elastic      │           │
│  │ PostgreSQL   │    │ Redis 7      │     │ Cloud        │           │
│  │ db-custom    │    │ Standard 2GB │     │ 1x 4GB node  │           │
│  │ 2vCPU/4GB    │    │ (HA)         │     │ (GCP SP)     │           │
│  │ + pgvector   │    │              │     │              │           │
│  └──────────────┘    └──────┬───────┘     └──────────────┘           │
│                              │                                          │
│                    ┌─────────▼──────────────────────┐                  │
│                    │ VM MIG Autohealing (e2-std-2)   │                  │
│                    │ ┌──────────────────────────────┐│                  │
│                    │ │ Sidekiq 15t  (← Redis)       ││                  │
│                    │ │ Sneakers     (← RabbitMQ)    ││                  │
│                    │ │ Celery 4w    (← RabbitMQ)    ││                  │
│                    │ └──────────────────────────────┘│                  │
│                    │   100% stateless — zero dados   │                  │
│                    └─────────────────────────────────┘                  │
│                              │                                          │
│                    ┌─────────▼──────────┐                              │
│                    │ CloudAMQP          │                              │
│                    │ RabbitMQ managed   │                              │
│                    │ Lemming/Lemur      │                              │
│                    └────────────────────┘                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  GCS Bucket (uploads) │ Secret Manager │ Cloud Logging           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Decisao por decisao — Pros e Contras

### 1. Rails API → Cloud Run (manter como esta)

| Pros | Contras |
|---|---|
| Ja esta funcionando | Cold start se min-instances = 0 (~3-5s) |
| LB automatico embutido | CPU throttling fora de requests (ActionCable) |
| Scale-to-zero quando ninguem usa | VPC Connector necessario pra rede privada |
| Deploy simples (`gcloud run deploy`) | |
| Paga so quando tem request | |

**Decisao:** Manter. Funciona, custo baixo, sem motivo pra mudar.

**Config recomendada para alpha:**
```bash
# API principal — min 1 pra evitar cold start total
gcloud run deploy ats-api \
  --min-instances 1 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi \
  --cpu-throttling \
  --set-env-vars="RAILS_ENV=production"
```

> **Nota sobre min-instances:** Com 0 clientes, `min: 0` economiza. Quando os alphas entrarem, subir pra `min: 1` pra evitar cold start no primeiro request do dia (~$25-40/mes a mais).

---

### 2. Interview AI (FastAPI + WebSocket) → Cloud Run (novo)

| Pros | Contras |
|---|---|
| WebSocket nativo no Cloud Run | Timeout max de 60min por conexao |
| Scale-to-zero (ninguem entrevistando = $0) | Se tiver muitas entrevistas simultaneas, custo sobe rapido |
| Isolado do Rails (crash nao afeta API) | Precisa de 2GB RAM (audio streaming) |
| Deploy independente | |

**Decisao:** Cloud Run. Entrevistas sao esporadicas — scale-to-zero e perfeito aqui. Ninguem entrevistando = custo zero.

```bash
gcloud run deploy interview-ai \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 900 \
  --concurrency 10
```

---

### 3. Evaluation API (Flask) → Cloud Run (novo)

| Pros | Contras |
|---|---|
| Stateless (recebe request, publica no RabbitMQ, retorna) | Nenhum significativo |
| Scale-to-zero | |
| 512MB RAM suficiente | |
| Custo quase zero com pouco trafego | |

**Decisao:** Cloud Run. Caso mais simples possivel.

```bash
gcloud run deploy evaluation-api \
  --min-instances 0 \
  --max-instances 3 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 60
```

---

### 4. Redis → Memorystore Standard HA (TIRAR da VM)

| Pros | Contras |
|---|---|
| Se VM crashar, Redis sobrevive | ~$70-90/mes (Standard 2GB HA) |
| Sidekiq, ActionCable, Celery continuam funcionando | Precisa de VPC Connector no Cloud Run |
| Managed com failover automatico | |
| Replica HA — se master morrer, failover em segundos | |
| Sub-millisecond latency na mesma VPC | |

**Decisao:** **TIRAR da VM — Standard 2GB com HA.** Redis e o single point of failure mais critico. Se morrer:
- Sidekiq para de processar jobs
- ActionCable desconecta todos os users
- Celery workers perdem result backend
- Sessions perdem-se

Redis e critico demais pra clientes alpha. Com Standard HA, tem failover automatico — se o master cair, replica assume em segundos. Sao ~$35/mes a mais que Basic, mas se Redis cair com empresa grande usando, e vergonha instantanea.

```bash
gcloud redis instances create ats-redis \
  --size=2 \
  --region=southamerica-east1 \
  --redis-version=redis_7_0 \
  --network=default \
  --tier=standard
```

---

### 5. Elasticsearch → Elastic Cloud (TIRAR da VM)

| Elastic Cloud managed | Manter na VM |
|---|---|
| ~$95-150/mes (1 no 4GB, GCP Sao Paulo) | $0 extra (ja paga a VM) |
| Zero operacao (upgrades, snapshots automaticos) | Persistent disk protege dados mas nao garante |
| Escala pelo dashboard sem downtime | Se perder dados, reindex resolve (10-15 min) |
| Shard management automatico conforme tenants crescem | Downtime de 2-3 min se VM crashar |
| **VM fica stateless = descartavel** | **ES consome 4-8GB de heap, rouba recursos dos workers** |

**Decisao:** **TIRAR da VM → Elastic Cloud.** Por dois motivos:

1. **VM vira descartavel.** Com ES fora, a VM nao tem nenhum dado. Se morrer, zero perda. MIG recria, processos sobem, conectam nos servicos managed e continuam. Recovery perfeito.

2. **Recursos.** Elasticsearch consome 4-8GB de heap. Tirando ele, a VM pode ser **menor** (e2-standard-2: 2 vCPU, 8GB por ~$60-70/mes em vez de e2-standard-4: 4 vCPU, 16GB por ~$120/mes). Sobra mais recurso pro Sidekiq (15 threads + filas pesadas de AI), Sneakers e Celery workers.

O custo extra de ~$95-150/mes do Elastic Cloud e parcialmente compensado pela VM menor (~$50-60 de economia). Delta real: ~$40-90/mes a mais — que compra zero operacao de ES, snapshots automaticos, e upgrades sem downtime.

**Config recomendada (Elastic Cloud):**
```
Provider:       GCP
Regiao:         southamerica-east1 (Sao Paulo)
Version:        8.x
Data nodes:     1x 4GB RAM (suficiente pra 2 tenants)
Kibana:         Habilitado (monitoring)
Snapshots:      Automaticos (incluso)
```

**Atencao:** 1 no sem replica = se o no cair, busca para ate Elastic Cloud recriar (minutos). Mas ES nao e fonte de verdade — PostgreSQL e. Se necessario, `rake searchkick:reindex:all` reconstroi tudo. Pra alpha, aceitavel. Quando tiver SLA com cliente, adicionar segundo no (~$95/mes a mais).

---

### 6. RabbitMQ → CloudAMQP (TIRAR da VM)

| Pros | Contras |
|---|---|
| Plano Lemming: $5/mes (managed) | Latencia um pouco maior (externo ao GCP) |
| Tiger: $0 (free, 1M msgs/mes) | Free tier tem limite de conexoes |
| Se VM crashar, mensagens nao se perdem | |
| Dashboard de monitoring incluso | |
| Nao precisa gerenciar Erlang/RabbitMQ | |

**Decisao:** **CloudAMQP Lemming ($5/mes).** RabbitMQ e chato de operar (Erlang, clustering, memory alarms). Tiger (free) funciona pra testar mas tem limite de 20 conexoes — com Sidekiq + Sneakers + Celery, pode estourar. Lemming tem 100 conexoes e 10M msgs/mes.

**Risco do free tier:** Tiger tem max 20 conexoes simultaneas. Sidekiq com 15 threads = 15 conexoes. Sneakers = mais algumas. Celery workers = mais. Facil estourar. Lemming ($5) resolve.

---

### 7. VM (Workers) → MIG Autohealing (MELHORAR a VM)

| Pros | Contras |
|---|---|
| Custo identico a VM atual ($0 extra) | Nao e HA (1 VM so, downtime de 2-3 min no recreate) |
| Autohealing: se crashar, GCP recria sozinho | Startup script precisa ser robusto |
| Instance Template: receita reproduzivel | Todos os workers na mesma VM ainda |
| Health check customizavel | |

**Decisao:** Converter a VM fixa em **MIG com autohealing**. Custo zero extra, mas ganha:
1. **Recreacao automatica** se a VM morrer (2-3 min)
2. **Instance Template** reproduzivel (nao e mais "aquela VM que alguem configurou na mao")
3. **Health check** que detecta problemas antes de voce acordar

**O que roda na VM (somente compute, zero dados):**
- Sidekiq (Rails background jobs) — conecta no Redis (Memorystore)
- Sneakers (RabbitMQ consumer) — conecta no RabbitMQ (CloudAMQP)
- Celery Workers (Agent — sourcing + evaluation) — conecta no RabbitMQ + Redis

**O que NAO roda mais na VM:**
- ~~Elasticsearch~~ → Elastic Cloud
- ~~Redis~~ → Memorystore
- ~~RabbitMQ~~ → CloudAMQP

**VM menor:** Sem ES (4-8GB heap), pode usar **e2-standard-2** (2 vCPU, 8GB) por ~$60-70/mes em vez de e2-standard-4 (~$120/mes). 8GB e mais que suficiente pra Sidekiq 15 threads + Sneakers + Celery 4 workers. Se apertar, monitoring de CPU/memoria mostra nas primeiras semanas — upgrade pra e2-standard-4 por ~$60 a mais.

**Startup script da VM:**
```bash
#!/bin/bash
# VM stateless — todos os servicos conectam em managed services externos

# Sobe Sidekiq (conecta no Redis via REDIS_URL e PostgreSQL via DATABASE_URL)
cd /app/ats_api && bundle exec sidekiq -C config/sidekiq.yml &

# Sobe Sneakers (conecta no RabbitMQ via RABBITMQ_URL)
cd /app/ats_api && bundle exec rake sneakers:run &

# Sobe Celery Workers (conecta no RabbitMQ via CELERY_BROKER_URL + Redis via REDIS_URL)
cd /app/recruiter_agent && celery -A src.celery_app worker \
  --queues=sourcing_high,evaluation_normal \
  --concurrency=4 &

# Health check server (porta 8080 pra MIG health check)
while true; do
  echo -e "HTTP/1.1 200 OK\r\n" | nc -l -p 8080 -q 1
done &
```

**Health check:**
```bash
# Script em /health.sh — chamado pelo MIG health check
#!/bin/bash
pgrep -f sidekiq || exit 1
pgrep -f sneakers || exit 1
pgrep -f celery || exit 1
exit 0
```

**Por que o recovery e perfeito:** Quando a VM morre e o MIG recria:
1. Startup script sobe Sidekiq, Sneakers e Celery
2. Sidekiq reconecta no Redis (Memorystore) e pega jobs que estavam na fila
3. Sneakers reconecta no RabbitMQ (CloudAMQP) e consome mensagens pendentes
4. Celery reconecta no RabbitMQ e processa tasks acumuladas
5. Zero dados perdidos, zero intervencao manual

---

### 8. PostgreSQL → Cloud SQL db-custom-2-4096 (upgrade)

| Pros | Contras |
|---|---|
| Ja esta funcionando | ~$50-60/mes a mais que db-g1-small |
| Backup automatico | Custo sobe se precisar de HA |
| Point-in-time recovery | |
| pgvector suportado | |
| 2 vCPU + 4GB = folga pra multi-tenant + pgvector | |

**Decisao:** **Upgrade pra db-custom-2-4096.** Clientes alpha sao empresas grandes — volume de candidatos razoavel, Apartment cria schemas pesados por tenant, pgvector pra embeddings puxa memoria. db-g1-small (shared core, 1.7GB) vai apertar e gargalo no banco e o tipo de problema mais dificil de debugar sob pressao.

A diferenca e ~$50-60/mes e evita o cenario de ter que fazer upgrade de emergencia no meio de um demo com cliente.

```bash
# Verificar tier atual
gcloud sql instances describe ats-db --format='value(settings.tier)'

# Upgrade
gcloud sql instances patch ats-db --tier=db-custom-2-4096
```

---

### 9. Uploads → GCS Bucket (manter/configurar)

Custo irrelevante (~$1-5/mes). Sem decisao a tomar, so configurar ActiveStorage pra usar GCS.

---

### 10. Secrets → Secret Manager

Custo irrelevante (~$1/mes). Usar em vez de .env files em producao. Mais seguro, auditavel.

---

## Estimativa de Custo — Fase 1

| Servico | Config | USD/mes |
|---|---|---|
| Cloud Run — Rails API | min 1, 2 vCPU, 1GB | ~$50-80 |
| Cloud Run — Rails API 2 | min 0 (scale) | ~$10-20 |
| Cloud Run — Nuxt Front | min 0, 1 vCPU, 512MB | ~$10-20 |
| Cloud Run — Interview AI | min 0, 2 vCPU, 2GB | ~$10-50 (uso esporadico) |
| Cloud Run — Evaluation API | min 0, 1 vCPU, 512MB | ~$5-10 |
| Cloud SQL — PostgreSQL | db-custom-2-4096 (2 vCPU, 4GB) | ~$80-100 |
| Memorystore — Redis | Standard 2GB (HA com replica) | ~$70-90 |
| Elastic Cloud | 1x 4GB node (GCP Sao Paulo) | ~$95-150 |
| CloudAMQP — RabbitMQ | Lemming ($5) ou Little Lemur | ~$5-20 |
| VM (MIG) — Workers ONLY | e2-standard-2 (2 vCPU, 8GB) | ~$60-70 |
| GCS — Uploads | Standard ~10GB | ~$1 |
| Secret Manager | ~10 secrets | ~$1 |
| VPC Connector | Cloud Run ↔ Memorystore/SQL | ~$7 |
| Networking/Egress | | ~$10-20 |
| **TOTAL** | | **~$420-650/mes** |

**Comparativo:**

| Estrategia | Custo/mes | Resiliencia | Operacao | VM stateless? |
|---|---|---|---|---|
| VM fixa com tudo (hoje) | ~$180 | Baixa (SPOF total, perda de dados) | Alta (tudo manual) | Nao |
| Plano anterior (ES na VM) | ~$300 | Media (autohealing, mas ES na VM) | Media | Nao |
| **Fase 1 proposta (tudo managed)** | **~$500** | **Alta (zero perda de dados, autohealing)** | **Baixa** | **Sim** |
| Full GKE + tudo managed | ~$1.200+ | Muito alta | Muito baixa | Sim |

**O que os ~$300/mes extras compram (vs VM com tudo):**
- **VM descartavel:** se morrer, zero perda de dados, recovery automatico em 2-3 min
- **Redis HA:** failover automatico em segundos, Sidekiq/ActionCable nunca caem por Redis
- **ES managed:** zero operacao, snapshots automaticos, upgrades sem downtime
- **VM menor:** sem ES, e2-standard-2 ($60) em vez de e2-standard-4 ($120)
- **Banco robusto:** db-custom-2-4096 aguenta multi-tenant + pgvector sem apertar

Com budget de $2.500-3.000/mes, ~$500 deixa margem enorme pra escalar quando os clientes comecarem a usar de verdade (mais entrevistas, mais sourcing, mais candidatos indexados).

---

## O que NAO vale a pena agora

| Servico | Custo | Por que nao agora |
|---|---|---|
| GKE Autopilot | $70-100/mes so de management fee | Overkill pra 2 clientes. VM com MIG resolve |
| Elastic Cloud 2o no (replica) | +$95/mes | 1 no suficiente pra alpha. ES nao e fonte de verdade |
| Cloud SQL HA (failover automatico) | +$80-100/mes | Single instance com backup diario resolve por agora |
| Cloud Armor (WAF) | $5-200/mes | Cloud Run ja tem DDoS basico. So quando tiver clientes enterprise |
| Multi-region | 2x custo total | Zero necessidade agora |
| Load Balancer externo | $18+/mes | Cloud Run ja embute LB |

---

## Caminho de Evolucao — Fases

### Fase 1: Alpha (0-5 clientes) ← VOCE ESTA AQUI
- Cloud Run pra tudo que e HTTP
- VM MIG stateless (Sidekiq + Sneakers + Celery)
- Memorystore Standard 2GB (Redis HA)
- Elastic Cloud 1x 4GB (GCP Sao Paulo)
- CloudAMQP Lemming/Lemur (RabbitMQ)
- Cloud SQL db-custom-2-4096
- **~$500/mes**

### Fase 2: Crescimento (5-20 clientes)
- Elastic Cloud: adicionar 2o no (replica HA) ~+$95/mes
- Cloud SQL HA (failover automatico) ~+$80/mes
- VM e2-standard-4 se workers estiverem lotados ~+$60/mes
- CloudAMQP Little Lemur ($20) se conexoes aumentarem
- **~$700-900/mes**

### Fase 3: Escala (20-100 clientes)
- Migrar workers pra GKE Autopilot (scaling independente por fila)
- Elastic Cloud com mais nodes conforme tenants crescem
- Cloud SQL read replica se necessario
- Cloud Armor (WAF) se clientes enterprise exigirem
- **~$1.200-2.000/mes**

### Fase 4: Enterprise (100+ clientes)
- Multi-region (SA + US)
- Dedicated Cloud SQL
- SLA 99.9%+
- **~$3.000+/mes**

---

## Riscos e Mitigacoes — Fase 1

| Risco | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|
| VM crashar | Baixa | **Baixo** (workers param 2-3 min, zero dados perdidos) | MIG autohealing recria, processos reconectam nos managed services |
| ES no cair (Elastic Cloud) | Baixa | Medio (busca para, reindex se necessario) | Elastic Cloud recria automaticamente. ES nao e fonte de verdade |
| Redis cair | Muito baixa | Alto | Memorystore Standard com failover automatico |
| Cloud SQL cair | Muito baixa | Critico | Backup diario + point-in-time recovery |
| RabbitMQ cair | Muito baixa (managed) | Alto | CloudAMQP com monitoring e retries |
| Cold start Cloud Run | Media | Baixo (3-5s no primeiro request) | min-instances 1 na API principal |
| Custo estourar | Baixa | Medio | Alertas de billing no GCP ($500, $700, $1000) |

---

## Checklist de Implementacao

### Infra (fazer antes dos alphas entrarem)

- [ ] Criar Memorystore Redis Standard 2GB HA (southamerica-east1)
- [ ] Criar VPC Connector (Cloud Run ↔ Memorystore/Cloud SQL)
- [ ] Configurar Cloud Run API pra usar Memorystore (REDIS_URL)
- [ ] Criar conta Elastic Cloud (1x 4GB, GCP southamerica-east1)
- [ ] Migrar ELASTICSEARCH_URL nos Cloud Runs e VM pra Elastic Cloud
- [ ] Rodar reindex completo no Elastic Cloud (`rake searchkick:reindex:all`)
- [ ] Criar conta CloudAMQP (Lemming $5 ou Little Lemur $20)
- [ ] Migrar RabbitMQ da VM pro CloudAMQP
- [ ] Upgrade Cloud SQL pra db-custom-2-4096
- [ ] Criar Instance Template da VM e2-standard-2 (startup script SEM ES/Redis/RabbitMQ)
- [ ] Criar MIG com autohealing (health check no Sidekiq + Sneakers + Celery)
- [ ] Remover ES, Redis e RabbitMQ da VM
- [ ] Testar: matar a VM e ver se MIG recria e processos reconectam

### Novos Cloud Runs

- [ ] Deploy Interview AI no Cloud Run (min 0)
- [ ] Deploy Evaluation API no Cloud Run (min 0)
- [ ] Configurar DNS/routing pra novos endpoints

### Seguranca

- [ ] Migrar todas as env vars sensiveis pro Secret Manager
- [ ] Configurar IAM: service accounts com principio de menor privilegio
- [ ] Cloud Run: remover `--allow-unauthenticated` onde nao for publico
- [ ] Configurar alertas de billing ($500, $700, $1000)

### Monitoring

- [ ] Cloud Monitoring: alerta de CPU da VM > 80% por 5 min
- [ ] Cloud Monitoring: alerta de memoria VM > 85%
- [ ] Cloud Monitoring: alerta de erro 5xx nos Cloud Runs
- [ ] Health check do MIG respondendo corretamente
- [ ] Elastic Cloud: verificar dashboard de health e snapshots

### Backup

- [ ] Cloud SQL: backup diario habilitado, retencao 7 dias
- [ ] Elastic Cloud: snapshots automaticos (ja incluso, verificar)
- [ ] Testar restore do Cloud SQL backup

---

## Decisao Final — Resumo

| Componente | Onde | Managed? | Custo |
|---|---|---|---|
| Rails API (x2) | Cloud Run | Sim | ~$60-100 |
| Nuxt Frontend | Cloud Run | Sim | ~$10-20 |
| Interview AI | Cloud Run | Sim | ~$10-50 |
| Evaluation API | Cloud Run | Sim | ~$5-10 |
| PostgreSQL | Cloud SQL (db-custom-2-4096) | Sim | ~$80-100 |
| Redis | Memorystore Standard 2GB HA | Sim | ~$70-90 |
| Elasticsearch | Elastic Cloud (1x 4GB) | Sim | ~$95-150 |
| RabbitMQ | CloudAMQP | Sim | ~$5-20 |
| Sidekiq | VM | Compute only | (incluso na VM) |
| Sneakers | VM | Compute only | (incluso na VM) |
| Celery Workers | VM | Compute only | (incluso na VM) |
| **VM total** | **MIG e2-standard-2 (stateless)** | **Autohealing** | **~$60-70** |
| Infra (GCS, Secrets, VPC, egress) | GCP | Sim | ~$20-30 |
| **TOTAL** | | | **~$420-650** |

---

## Por que esse plano e solido

**Separacao correta: compute descartavel, dados protegidos.**

Todo estado esta em servico managed:
- Dados → Cloud SQL (backup automatico, point-in-time recovery)
- Cache/filas → Memorystore Redis (HA com failover)
- Indices de busca → Elastic Cloud (snapshots automaticos)
- Mensageria → CloudAMQP (persistencia de mensagens)

A VM roda apenas processos stateless que reconectam automaticamente. Se morrer:
1. MIG recria em 2-3 min
2. Sidekiq reconecta no Redis e pega jobs pendentes
3. Sneakers reconecta no RabbitMQ e consome mensagens
4. Celery reconecta e processa tasks acumuladas
5. Cloud Runs continuam servindo HTTP durante todo o processo
6. **Zero perda de dados. Zero intervencao manual.**

Com budget de $2.500-3.000/mes, gastar ~$500 na Fase 1 deixa margem enorme pra escalar quando os clientes comecarem a usar de verdade. E nao vai fazer passar vergonha — tudo que pode cair tem failover ou recovery automatico.
