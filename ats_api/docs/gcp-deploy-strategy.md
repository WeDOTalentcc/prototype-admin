# Estrategia de Deploy - GCP (Google Cloud Platform)

## Stack do Projeto

| Componente | Tecnologia |
|---|---|
| API | Rails 7.1 / Ruby 3.4.4 |
| Workers | Sidekiq 7 (15 concurrency, 10+ filas) |
| Consumers | Sneakers (RabbitMQ) |
| Banco | PostgreSQL 15 + pgvector |
| Search | Elasticsearch 7.17+ |
| Cache/Queue | Redis 7 |
| Mensageria | RabbitMQ |
| Upload | ActiveStorage |
| Multi-tenancy | ros-apartment (schema-based) |

---

## Arquitetura Recomendada

```
                    ┌──────────────┐
                    │ Cloud Load   │
                    │  Balancer    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Cloud Run   │
                    │  (API Rails) │
                    │  min: 2      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
   │ Cloud SQL   │ │ Memorystore │ │ GCS Bucket   │
   │ PostgreSQL  │ │ (Redis)     │ │ (Uploads)    │
   │ + pgvector  │ └─────────────┘ └──────────────┘
   └─────────────┘        │
                           │
                    ┌──────▼───────┐
                    │   GKE        │
                    │ Autopilot    │
                    │ ┌──────────┐ │
                    │ │ Sidekiq  │ │
                    │ │ Workers  │ │
                    │ ├──────────┤ │
                    │ │ Sneakers │ │
                    │ │ Consumer │ │
                    │ ├──────────┤ │
                    │ │ Elastic  │ │
                    │ │ search   │ │
                    │ └──────────┘ │
                    └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ CloudAMQP    │
                    │ (RabbitMQ)   │
                    └──────────────┘
```

---

## Componente por Componente

### 1. API Rails → Cloud Run

**Por que Cloud Run e nao GKE para a API:**
- Scale-to-zero quando nao tem trafego (economia)
- Autoscaling automatico baseado em requests
- Zero gerenciamento de infra (sem nodes, sem patches)
- Deploy com um `gcloud run deploy`
- Suporte nativo a containers (ja temos Dockerfile multi-stage)

**Configuracao recomendada:**
```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ats-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "2"
        autoscaling.knative.dev/maxScale: "20"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/vpc-access-connector: "projects/PROJECT/locations/REGION/connectors/ats-connector"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: REGION-docker.pkg.dev/PROJECT/ats-repo/ats-api:latest
          ports:
            - containerPort: 3000
          resources:
            limits:
              cpu: "2"
              memory: "1Gi"
          env:
            - name: RAILS_ENV
              value: production
```

**Pontos importantes:**
- `minScale: 2` para evitar cold starts (multi-tenancy + JWT decode precisam de warmup)
- `cpu-throttling: false` para manter CPU alocada fora de requests (background threads do ActionCable)
- VPC Connector para acessar Cloud SQL e Memorystore via rede privada

---

### 2. Sidekiq Workers → GKE Autopilot

**Por que GKE e nao Cloud Run para Sidekiq:**
- Sidekiq e um processo long-running, nao request-driven
- Precisa de conexao persistente com Redis
- Cloud Run cobra por request/tempo - Sidekiq fica 100% ativo, seria mais caro
- GKE Autopilot elimina gerenciamento de nodes mas mantem controle de pods

**Deployment recomendado:**
```yaml
# k8s/sidekiq-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sidekiq
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sidekiq
  template:
    spec:
      containers:
        - name: sidekiq
          image: REGION-docker.pkg.dev/PROJECT/ats-repo/ats-api:latest
          command: ["bundle", "exec", "sidekiq", "-C", "config/sidekiq.yml"]
          resources:
            requests:
              cpu: "1"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "2Gi"
          envFrom:
            - secretRef:
                name: ats-env-secrets
```

**Scaling por fila:**
Dado que o projeto tem filas com prioridades muito diferentes (`critical`, `ai_analysis`, `embeddings`, `low`), considerar deployments separados:

```yaml
# sidekiq-critical.yaml  → replicas: 2, queues: critical,email_delivery
# sidekiq-ai.yaml        → replicas: 1, queues: ai_analysis,embeddings,sourcing_search
# sidekiq-default.yaml   → replicas: 1, queues: default,mailers,active_storage,low,ats_sync
```

Isso permite escalar filas de AI independentemente das filas criticas.

---

### 3. Sneakers (RabbitMQ Consumer) → GKE Autopilot

Mesmo cluster GKE, deployment separado:
```yaml
command: ["bundle", "exec", "rake", "sneakers:run"]
```

**RabbitMQ em si:** usar **CloudAMQP** (managed RabbitMQ) ao inves de self-host. Rodar RabbitMQ no GKE e possivel mas adiciona complexidade operacional desnecessaria (clustering, persistencia, monitoring).

---

### 4. PostgreSQL 15 + pgvector → Cloud SQL

**Por que Cloud SQL:**
- Backups automaticos, point-in-time recovery
- High availability com failover automatico
- Suporte nativo a pgvector (extensao disponivel no Cloud SQL)
- Maintenance windows configuraveis
- Read replicas se necessario

**Configuracao recomendada:**
```
Tier:           db-custom-4-16384 (4 vCPU, 16GB RAM)
Storage:        SSD, 100GB (auto-increase habilitado)
Availability:   Regional (HA com failover)
Backup:         Diario, retencao 30 dias
Extensions:     pgvector, uuid-ossp
Flags:
  - max_connections: 200
  - shared_buffers: 4GB
  - work_mem: 64MB
```

**Conexao:** usar Cloud SQL Auth Proxy (sidecar no GKE, built-in no Cloud Run) para conexao segura sem expor IP publico.

---

### 5. Redis → Memorystore for Redis

**Por que Memorystore:**
- Fully managed, HA com failover automatico
- Latencia sub-millisecond na mesma VPC
- Sem overhead de gerenciar Redis (patches, memory management)

**Configuracao recomendada:**
```
Tier:       Standard (HA com replica)
Size:       5GB (Sidekiq + ActionCable + sessions)
Version:    7.x
Network:    Mesma VPC do Cloud Run e GKE
```

**Nota:** Memorystore so aceita conexoes via VPC privada - por isso o VPC Connector no Cloud Run e essencial.

---

### 6. Elasticsearch → Elastic Cloud on GCP

**Por que Elastic Cloud e nao self-host no GKE:**
- Elasticsearch e notoriamente dificil de operar (memory tuning, shard management, upgrades)
- Elastic Cloud roda nativamente no GCP (mesma regiao, baixa latencia)
- Snapshots, monitoring, upgrades sem downtime incluidos
- O projeto usa searchkick com indices por tenant - Elastic Cloud escala melhor para esse pattern

**Alternativa mais barata:** rodar no GKE com o ECK Operator (Elastic Cloud on Kubernetes). Mais trabalho operacional, mas sem custo de licenca Elastic Cloud.

**Configuracao recomendada (Elastic Cloud):**
```
Deployment:     GCP, mesma regiao
Version:        8.x
Data nodes:     2x 8GB RAM
Kibana:         Habilitado (monitoring)
```

---

### 7. Uploads (ActiveStorage) → Google Cloud Storage (GCS)

**Configuracao no Rails:**
```yaml
# config/storage.yml
google:
  service: GCS
  project: ats-production
  credentials: <%= Rails.application.credentials.dig(:gcs, :credentials).to_json %>
  bucket: ats-uploads-production

# config/environments/production.rb
config.active_storage.service = :google
```

**Bucket config:**
```
Location:       Mesma regiao
Storage class:  Standard (acesso frequente)
Lifecycle:      Mover para Nearline apos 90 dias (se aplicavel)
Access:         Uniform (IAM-based)
CORS:           Configurado para dominio do frontend
```

Adicionar gem `google-cloud-storage` ao Gemfile.

---

## Rede e Seguranca

### VPC Setup
```
VPC: ats-vpc
├── Subnet: ats-private (10.0.0.0/20) → Cloud SQL, Memorystore
├── Subnet: ats-gke (10.0.16.0/20) → GKE Autopilot pods
├── VPC Connector: ats-connector → Cloud Run ↔ recursos privados
└── Private Service Access → Cloud SQL
```

### Secret Management → Secret Manager
Todas as env vars sensiveis (API keys, DB passwords, JWT secrets) no **Google Secret Manager**:
```bash
gcloud secrets create POSTGRES_PASSWORD --data-file=- <<< "senha"
gcloud secrets create OPENAI_API_KEY --data-file=- <<< "sk-..."
gcloud secrets create RAILS_MASTER_KEY --data-file=- <<< "abc123"
```

Cloud Run e GKE referenciam secrets via IAM, sem .env files em producao.

---

## CI/CD Pipeline → Cloud Build + Artifact Registry

### Pipeline
```
Push to main
    │
    ▼
GitHub Actions (existente)
    │ scan_ruby (Brakeman)
    │ lint (RuboCop)
    │
    ▼
Cloud Build Trigger
    │
    ├─► Build Docker image
    ├─► Push to Artifact Registry
    ├─► Run db:migrate (Cloud Build step)
    ├─► Deploy Cloud Run (API)
    └─► Update GKE deployments (Sidekiq, Sneakers)
```

### cloudbuild.yaml
```yaml
steps:
  # Build
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${_IMAGE}:${SHORT_SHA}', '--build-arg', 'APP_ENV=production', '.']

  # Push
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_IMAGE}:${SHORT_SHA}']

  # Migrate
  - name: '${_IMAGE}:${SHORT_SHA}'
    args: ['bundle', 'exec', 'rails', 'db:migrate']
    env:
      - 'RAILS_ENV=production'
    secretEnv: ['DATABASE_URL', 'RAILS_MASTER_KEY']

  # Deploy API
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'ats-api', '--image', '${_IMAGE}:${SHORT_SHA}', '--region', '${_REGION}']

  # Deploy Sidekiq
  - name: 'gcr.io/cloud-builders/kubectl'
    args: ['set', 'image', 'deployment/sidekiq', 'sidekiq=${_IMAGE}:${SHORT_SHA}']
    env: ['CLOUDSDK_COMPUTE_REGION=${_REGION}', 'CLOUDSDK_CONTAINER_CLUSTER=ats-cluster']

substitutions:
  _IMAGE: '${_REGION}-docker.pkg.dev/${PROJECT_ID}/ats-repo/ats-api'
  _REGION: 'southamerica-east1'
```

---

## Estimativa de Custo Mensal (Baseline)

| Servico | Config | Estimativa/mes |
|---|---|---|
| Cloud Run (API) | 2 instances min, 2 vCPU, 1GB | ~$80-150 |
| GKE Autopilot | 3-4 pods (Sidekiq + Sneakers) | ~$150-250 |
| Cloud SQL (PostgreSQL) | 4 vCPU, 16GB, HA | ~$350-450 |
| Memorystore (Redis) | 5GB Standard | ~$150-200 |
| Elastic Cloud | 2x 8GB nodes | ~$200-350 |
| CloudAMQP (RabbitMQ) | Tiger plan | ~$20-80 |
| GCS (Storage) | Standard, ~50GB | ~$1-5 |
| Cloud Build | Build minutes | ~$10-30 |
| Secret Manager | Secrets + access | ~$1-5 |
| VPC / Networking | Connector, egress | ~$20-50 |
| **Total estimado** | | **~$1.000-1.500/mes** |

*Valores para regiao `southamerica-east1` (Sao Paulo). Precos variam com uso real.*

---

## Alternativa de Menor Custo: Tudo no GKE

Se o custo for prioridade maxima, rodar **tudo** no GKE Autopilot:

| Componente | Approach |
|---|---|
| API Rails | Deployment + Service + Ingress |
| Sidekiq | Deployment (sem service) |
| Sneakers | Deployment (sem service) |
| Redis | StatefulSet ou Memorystore (recomendo manter managed) |
| PostgreSQL | Cloud SQL (recomendo manter managed - DB nao vale o risco) |
| Elasticsearch | ECK Operator no GKE |
| RabbitMQ | RabbitMQ Operator no GKE |

Isso reduz custo de Elastic Cloud e CloudAMQP mas aumenta complexidade operacional.

**Estimativa:** ~$700-1.000/mes

---

## Recomendacao Final

| Decisao | Escolha | Motivo |
|---|---|---|
| API | Cloud Run | Serverless, autoscaling, zero ops |
| Workers | GKE Autopilot | Long-running, cost-effective |
| PostgreSQL | Cloud SQL | Nunca self-host banco em producao |
| Redis | Memorystore | Managed, HA, sub-ms latency |
| Elasticsearch | Elastic Cloud (ideal) ou ECK no GKE (budget) | Complexidade operacional vs custo |
| RabbitMQ | CloudAMQP | Barato, managed, sem dor de cabeca |
| Uploads | GCS | Nativo para ActiveStorage, barato |
| Secrets | Secret Manager | Seguro, auditavel, integrado |
| CI/CD | Cloud Build + GitHub Actions | Aproveita CI existente |
| Regiao | southamerica-east1 | Latencia para usuarios BR |

A combinacao Cloud Run (API) + GKE Autopilot (workers) e o melhor balance entre custo, operacao e flexibilidade para esse stack.
