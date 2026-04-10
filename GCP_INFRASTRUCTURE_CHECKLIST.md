# GCP Infrastructure Checklist — Guia de Provisionamento

> **Plataforma LIA** — Guia executável para o time de infraestrutura.
> Última atualização: Abril 2026
>
> **Domínio:** `wedotalent.cc`
> **Região padrão:** `us-east1` (substitua `$REGION` se diferente)

---

## Pré-requisitos

- [ ] Conta GCP com billing ativo
- [ ] `gcloud` CLI instalado (v450+) e autenticado (`gcloud auth login`)
- [ ] Domínio `wedotalent.cc` registrado com acesso ao painel DNS
- [ ] Chaves de API prontas: Anthropic, WorkOS, Twilio, Mailgun, Sentry

---

## Fase 1 — Projeto e APIs

### 1.1 Criar/selecionar projeto

```bash
export PROJECT_ID="wedotalent-prod"
export REGION="us-east1"
export ZONE="${REGION}-b"

gcloud projects create $PROJECT_ID --name="WeDOTalent Production" 2>/dev/null || true
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

- [ ] Projeto criado e billing vinculado

### 1.2 Habilitar APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  speech.googleapis.com \
  texttospeech.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  vpcaccess.googleapis.com
# Artifact Registry substitui Container Registry (gcr.io) — é o padrão moderno do GCP.
# Cloud Armor usa a Compute API (compute.googleapis.com) — não precisa de API separada.
```

- [ ] Todas as APIs habilitadas

### 1.3 Service Account para CI/CD

```bash
gcloud iam service-accounts create lia-deployer \
  --display-name="LIA CI/CD Deployer"

SA_EMAIL="lia-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

for ROLE in \
  roles/run.admin \
  roles/artifactregistry.writer \
  roles/iam.serviceAccountUser \
  roles/secretmanager.secretAccessor \
  roles/cloudsql.client \
  roles/storage.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --quiet
done

gcloud iam service-accounts keys create lia-deployer-key.json \
  --iam-account="${SA_EMAIL}"

echo "⚠️  Salve lia-deployer-key.json como GCP_SA_KEY no GitHub Secrets (ambos os repos)"
```

- [ ] Service account criada com roles corretas
- [ ] JSON key gerada e armazenada no GitHub Secrets

### 1.4 Artifact Registry

```bash
gcloud artifacts repositories create lia \
  --repository-format=docker \
  --location=$REGION \
  --description="LIA Platform Docker images"
```

- [ ] Repositório Docker `lia` criado

---

## Fase 2 — Rede (VPC Connector)

Cloud Run precisa de um VPC Connector para acessar Memorystore (Redis) e Cloud SQL via IP privado.

```bash
gcloud compute networks vpc-access connectors create lia-connector \
  --region=$REGION \
  --range="10.8.0.0/28" \
  --min-instances=2 \
  --max-instances=10
```

- [ ] VPC Connector `lia-connector` criado

---

## Fase 3 — Banco de Dados (Cloud SQL)

### 3.1 Criar instância PostgreSQL

```bash
gcloud sql instances create lia-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-custom-2-8192 \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=50GB \
  --storage-auto-increase \
  --availability-type=regional \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04 \
  --database-flags=max_connections=200,log_min_duration_statement=1000 \
  --root-password="$(openssl rand -base64 32)"
```

### 3.2 Criar bancos e usuário

```bash
gcloud sql databases create lia_db --instance=lia-postgres

gcloud sql users create lia_user \
  --instance=lia-postgres \
  --password="$(openssl rand -base64 32)"

echo "⚠️  Anote a senha do lia_user — será usada no DATABASE_URL"
```

### 3.3 Obter connection name

```bash
gcloud sql instances describe lia-postgres --format='value(connectionName)'
```

A string será algo como `wedotalent-prod:us-east1:lia-postgres`. Use para construir a DATABASE_URL:

```
postgresql+asyncpg://lia_user:PASSWORD@/lia_db?host=/cloudsql/wedotalent-prod:us-east1:lia-postgres
```

- [ ] Cloud SQL criado e rodando
- [ ] Banco `lia_db` criado
- [ ] Usuário `lia_user` criado com senha forte
- [ ] CONNECTION_NAME anotado

---

## Fase 4 — Redis (Memorystore)

```bash
gcloud redis instances create lia-redis \
  --region=$REGION \
  --tier=standard \
  --size=2 \
  --redis-version=redis_7_2 \
  --transit-encryption-mode=DISABLED \
  --auth-enabled \
  --display-name="LIA Redis"
```

Obter IP e AUTH string:

```bash
REDIS_HOST=$(gcloud redis instances describe lia-redis \
  --region=$REGION --format='value(host)')
REDIS_AUTH=$(gcloud redis instances describe lia-redis \
  --region=$REGION --format='value(authString)')
echo "REDIS_URL=redis://:${REDIS_AUTH}@${REDIS_HOST}:6379/0"
```

- [ ] Memorystore criado
- [ ] REDIS_URL construído e anotado

---

## Fase 5 — Secret Manager

### 5.1 Secrets obrigatórios

Cada secret abaixo deve ser criado no Secret Manager. A coluna "Origem" indica onde obter o valor.

| Secret Name | Descrição | Origem | Obrigatório |
|---|---|---|---|
| `DATABASE_URL` | Connection string PostgreSQL | Fase 3.3 acima | Sim |
| `REDIS_URL` | URL do Redis com auth | Fase 4 acima | Sim |
| `SECRET_KEY` | JWT signing key (64 bytes hex) | `openssl rand -hex 64` | Sim |
| `ANTHROPIC_API_KEY` | Claude API key | console.anthropic.com | Sim |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | platform.openai.com | Não |
| `SENTRY_DSN` | DSN do Sentry backend | sentry.io → Settings → DSN | Sim |
| `WORKOS_API_KEY` | WorkOS API key | dashboard.workos.com | Sim (SSO) |
| `WORKOS_CLIENT_ID` | WorkOS Client ID | dashboard.workos.com | Sim (SSO) |
| `WORKOS_WEBHOOK_SECRET` | WorkOS webhook secret | dashboard.workos.com | Não |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | console.twilio.com | Sim (voz) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | console.twilio.com | Sim (voz) |
| `MAILGUN_API_KEY` | Mailgun API key | app.mailgun.com → API Keys | Sim (email) |
| `RESEND_API_KEY` | Resend API key (fallback email) | resend.com/api-keys | Não |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | portal.azure.com → Entra ID | Não (calendar) |
| `AZURE_CLIENT_ID` | Azure App Client ID | portal.azure.com → App Registration | Não (calendar) |
| `AZURE_CLIENT_SECRET` | Azure App Secret | portal.azure.com → Certificates & Secrets | Não (calendar) |
| `STRIPE_SECRET_KEY` | Stripe secret key | dashboard.stripe.com/apikeys | Não (billing) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | dashboard.stripe.com/webhooks | Não (billing) |
| `LANGCHAIN_API_KEY` | LangSmith API key | smith.langchain.com | Não (tracing) |
| `ADMIN_API_KEY` | Admin endpoint auth key | `openssl rand -hex 32` | Não |

### 5.2 Criar secrets em batch

```bash
echo -n "$(openssl rand -hex 64)" | \
  gcloud secrets create SECRET_KEY --data-file=- --replication-policy=automatic

echo -n "postgresql+asyncpg://lia_user:PASSWORD@/lia_db?host=/cloudsql/${CONNECTION_NAME}" | \
  gcloud secrets create DATABASE_URL --data-file=- --replication-policy=automatic

echo -n "redis://:${REDIS_AUTH}@${REDIS_HOST}:6379/0" | \
  gcloud secrets create REDIS_URL --data-file=- --replication-policy=automatic

echo -n "sk-ant-..." | \
  gcloud secrets create ANTHROPIC_API_KEY --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create SENTRY_DSN --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create WORKOS_API_KEY --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create WORKOS_CLIENT_ID --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create TWILIO_ACCOUNT_SID --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create TWILIO_AUTH_TOKEN --data-file=- --replication-policy=automatic

echo -n "..." | \
  gcloud secrets create MAILGUN_API_KEY --data-file=- --replication-policy=automatic
```

### 5.3 Conceder acesso ao Cloud Run

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CR_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in DATABASE_URL REDIS_URL SECRET_KEY ANTHROPIC_API_KEY SENTRY_DSN \
  WORKOS_API_KEY WORKOS_CLIENT_ID TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN MAILGUN_API_KEY; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${CR_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet
done
```

- [ ] Todos os secrets obrigatórios criados
- [ ] Cloud Run service account tem acesso de leitura

---

## Fase 6 — Cloud Storage

### 6.1 Buckets

```bash
gcloud storage buckets create gs://lia-uploads-prod \
  --location=$REGION \
  --uniform-bucket-level-access \
  --public-access-prevention

gcloud storage buckets create gs://lia-audit-logs \
  --location=$REGION \
  --uniform-bucket-level-access \
  --public-access-prevention
```

### 6.2 Lifecycle (mover para Nearline após 365 dias)

```bash
cat > /tmp/lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 365}
    }
  ]
}
EOF

gcloud storage buckets update gs://lia-uploads-prod --lifecycle-file=/tmp/lifecycle.json
gcloud storage buckets update gs://lia-audit-logs --lifecycle-file=/tmp/lifecycle.json
```

- [ ] Buckets criados com lifecycle

---

## Fase 7 — Cloud Run (Deploy dos serviços)

> Os deploys serão feitos automaticamente pelo CI/CD (GitHub Actions).
> Os comandos abaixo servem para o **primeiro deploy manual** ou troubleshooting.

### 7.1 Frontend (`lia-frontend`)

```bash
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-frontend:latest"

gcloud run deploy lia-frontend \
  --project $PROJECT_ID \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --port 3000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars "NODE_ENV=production,BACKEND_URL=https://lia-api-HASH.a.run.app" \
  --allow-unauthenticated \
  --vpc-connector lia-connector
```

### 7.2 Backend API (`lia-api`)

```bash
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-api:latest"

gcloud run deploy lia-api \
  --project $PROJECT_ID \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --port 8000 \
  --memory 1Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 20 \
  --timeout 120 \
  --set-env-vars "APP_ENV=production,DEBUG=false,LOG_LEVEL=WARNING,APP_BASE_URL=https://wedotalent.cc" \
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,SECRET_KEY=SECRET_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,SENTRY_DSN=SENTRY_DSN:latest,TWILIO_ACCOUNT_SID=TWILIO_ACCOUNT_SID:latest,TWILIO_AUTH_TOKEN=TWILIO_AUTH_TOKEN:latest,MAILGUN_API_KEY=MAILGUN_API_KEY:latest,WORKOS_API_KEY=WORKOS_API_KEY:latest,WORKOS_CLIENT_ID=WORKOS_CLIENT_ID:latest" \
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:lia-postgres" \
  --vpc-connector lia-connector \
  --allow-unauthenticated
```

### 7.3 Celery Worker (`lia-worker`)

```bash
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-worker:latest"

gcloud run deploy lia-worker \
  --project $PROJECT_ID \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --no-cpu-throttling \
  --memory 1Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 5 \
  --timeout 900 \
  --set-env-vars "APP_ENV=production,CELERY_CONCURRENCY=2" \
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest" \
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:lia-postgres" \
  --vpc-connector lia-connector \
  --no-allow-unauthenticated
```

> O worker usa `scripts/worker_health.py` como entrypoint — inclui um HTTP health server
> na porta `$PORT` e inicia o Celery em paralelo. O `--no-cpu-throttling` garante
> processamento contínuo de filas, e `--min-instances=1` mantém o worker sempre ativo.

- [ ] Frontend deploy OK
- [ ] API deploy OK
- [ ] Worker deploy OK

---

## Fase 8 — Load Balancer, SSL e DNS

### 8.1 IP estático global

```bash
gcloud compute addresses create lia-lb-ip --global
LB_IP=$(gcloud compute addresses describe lia-lb-ip --global --format='value(address)')
echo "IP do Load Balancer: $LB_IP"
```

### 8.2 Managed SSL Certificates

```bash
gcloud compute ssl-certificates create lia-cert-prod \
  --domains="wedotalent.cc,www.wedotalent.cc,api.wedotalent.cc"

gcloud compute ssl-certificates create lia-cert-staging \
  --domains="staging.wedotalent.cc,api-staging.wedotalent.cc"
```

### 8.3 Serverless NEGs (Network Endpoint Groups)

```bash
gcloud compute network-endpoint-groups create lia-frontend-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=lia-frontend

gcloud compute network-endpoint-groups create lia-api-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=lia-api

gcloud compute network-endpoint-groups create lia-frontend-staging-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=lia-frontend-staging

gcloud compute network-endpoint-groups create lia-api-staging-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=lia-api-staging
```

### 8.4 Backend Services

```bash
gcloud compute backend-services create lia-frontend-bs \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend lia-frontend-bs \
  --global \
  --network-endpoint-group=lia-frontend-neg \
  --network-endpoint-group-region=$REGION

gcloud compute backend-services create lia-api-bs \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend lia-api-bs \
  --global \
  --network-endpoint-group=lia-api-neg \
  --network-endpoint-group-region=$REGION
```

### 8.4.1 Backend Services — Staging

```bash
gcloud compute backend-services create lia-frontend-staging-bs \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend lia-frontend-staging-bs \
  --global \
  --network-endpoint-group=lia-frontend-staging-neg \
  --network-endpoint-group-region=$REGION

gcloud compute backend-services create lia-api-staging-bs \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend lia-api-staging-bs \
  --global \
  --network-endpoint-group=lia-api-staging-neg \
  --network-endpoint-group-region=$REGION
```

### 8.5 URL Map (roteamento por domínio)

```bash
gcloud compute url-maps create lia-lb \
  --default-service=lia-frontend-bs

gcloud compute url-maps add-host-rule lia-lb \
  --hosts="api.wedotalent.cc" \
  --path-matcher-name="api-matcher"
gcloud compute url-maps add-path-matcher lia-lb \
  --path-matcher-name="api-matcher" \
  --default-service=lia-api-bs

gcloud compute url-maps add-host-rule lia-lb \
  --hosts="staging.wedotalent.cc" \
  --path-matcher-name="staging-frontend-matcher"
gcloud compute url-maps add-path-matcher lia-lb \
  --path-matcher-name="staging-frontend-matcher" \
  --default-service=lia-frontend-staging-bs

gcloud compute url-maps add-host-rule lia-lb \
  --hosts="api-staging.wedotalent.cc" \
  --path-matcher-name="staging-api-matcher"
gcloud compute url-maps add-path-matcher lia-lb \
  --path-matcher-name="staging-api-matcher" \
  --default-service=lia-api-staging-bs
```

### 8.6 HTTPS Proxy e Forwarding Rules

```bash
gcloud compute target-https-proxies create lia-https-proxy \
  --url-map=lia-lb \
  --ssl-certificates=lia-cert-prod,lia-cert-staging

gcloud compute forwarding-rules create lia-https-rule \
  --global \
  --target-https-proxy=lia-https-proxy \
  --ports=443 \
  --address=lia-lb-ip
```

### 8.6.1 HTTP → HTTPS Redirect

```bash
gcloud compute url-maps import lia-http-redirect-map \
  --source=/dev/stdin <<'EOF'
kind: compute#urlMap
name: lia-http-redirect-map
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
EOF

gcloud compute target-http-proxies create lia-http-proxy \
  --url-map=lia-http-redirect-map

gcloud compute forwarding-rules create lia-http-redirect \
  --global \
  --target-http-proxy=lia-http-proxy \
  --ports=80 \
  --address=lia-lb-ip
```

### 8.7 Cloud Armor (WAF)

```bash
gcloud compute security-policies create lia-waf \
  --description="LIA Platform WAF"

gcloud compute security-policies rules create 1000 \
  --security-policy=lia-waf \
  --action=deny-403 \
  --expression="evaluatePreconfiguredWaf('sqli-v33-stable')"

gcloud compute security-policies rules create 1001 \
  --security-policy=lia-waf \
  --action=deny-403 \
  --expression="evaluatePreconfiguredWaf('xss-v33-stable')"

gcloud compute security-policies rules create 2000 \
  --security-policy=lia-waf \
  --action=throttle \
  --expression="true" \
  --rate-limit-threshold-count=300 \
  --rate-limit-threshold-interval-sec=60 \
  --conform-action=allow \
  --exceed-action=deny-429

gcloud compute backend-services update lia-api-bs \
  --global \
  --security-policy=lia-waf
```

### 8.8 DNS Records

Configure no painel DNS do registrador de `wedotalent.cc`:

| Record | Type | Value | TTL |
|---|---|---|---|
| `wedotalent.cc` | A | `$LB_IP` | 300 |
| `www.wedotalent.cc` | CNAME | `wedotalent.cc` | 300 |
| `api.wedotalent.cc` | A | `$LB_IP` | 300 |
| `staging.wedotalent.cc` | A | `$LB_IP` | 300 |
| `api-staging.wedotalent.cc` | A | `$LB_IP` | 300 |

- [ ] IP estático alocado
- [ ] Certificados SSL criados (provisioning pode levar até 24h)
- [ ] NEGs criados para cada Cloud Run service
- [ ] Load Balancer configurado com URL Map
- [ ] Cloud Armor WAF ativo na API
- [ ] DNS records configurados
- [ ] SSL certificates em status ACTIVE

---

## Fase 9 — Staging (ambiente paralelo)

### 9.1 Banco staging

```bash
gcloud sql databases create lia_db_staging --instance=lia-postgres
```

### 9.2 Secrets staging (prefixados)

```bash
echo -n "$(openssl rand -hex 64)" | \
  gcloud secrets create SECRET_KEY_STAGING --data-file=- --replication-policy=automatic

echo -n "postgresql+asyncpg://lia_user:PASSWORD@/lia_db_staging?host=/cloudsql/${CONNECTION_NAME}" | \
  gcloud secrets create DATABASE_URL_STAGING --data-file=- --replication-policy=automatic
```

### 9.3 Cloud Run — Staging Services (primeiro deploy manual)

```bash
IMAGE_FE="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-frontend:latest"
IMAGE_API="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-api:latest"
IMAGE_WORKER="${REGION}-docker.pkg.dev/${PROJECT_ID}/lia/lia-worker:latest"

gcloud run deploy lia-frontend-staging \
  --project $PROJECT_ID \
  --image $IMAGE_FE \
  --region $REGION \
  --platform managed \
  --port 3000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "NODE_ENV=production,BACKEND_URL=https://lia-api-staging-HASH.a.run.app" \
  --allow-unauthenticated \
  --vpc-connector lia-connector

gcloud run deploy lia-api-staging \
  --project $PROJECT_ID \
  --image $IMAGE_API \
  --region $REGION \
  --platform managed \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 120 \
  --set-env-vars "APP_ENV=staging,DEBUG=false,LOG_LEVEL=INFO,APP_BASE_URL=https://staging.wedotalent.cc" \
  --set-secrets "DATABASE_URL=DATABASE_URL_STAGING:latest,REDIS_URL=REDIS_URL:latest,SECRET_KEY=SECRET_KEY_STAGING:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest" \
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:lia-postgres" \
  --vpc-connector lia-connector \
  --allow-unauthenticated

gcloud run deploy lia-worker-staging \
  --project $PROJECT_ID \
  --image $IMAGE_WORKER \
  --region $REGION \
  --platform managed \
  --no-cpu-throttling \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 900 \
  --set-env-vars "APP_ENV=staging,CELERY_CONCURRENCY=1" \
  --set-secrets "DATABASE_URL=DATABASE_URL_STAGING:latest,REDIS_URL=REDIS_URL:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest" \
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:lia-postgres" \
  --vpc-connector lia-connector \
  --no-allow-unauthenticated
```

> Após o primeiro deploy manual, o CI/CD (push para `develop`) atualiza automaticamente.
> Staging usa `--min-instances 0` para escalar a zero quando inativo (~$0 quando sem tráfego).

- [ ] Banco staging criado
- [ ] Secrets staging criados
- [ ] Serviços staging deployados

---

## Fase 10 — Validação pós-provisionamento

### 10.1 Verificar APIs habilitadas

```bash
gcloud services list --enabled --filter="NAME:(run OR sqladmin OR redis OR secretmanager OR artifactregistry)" \
  --format="table(NAME,STATE)"
```

### 10.2 Testar Cloud SQL

```bash
gcloud sql connect lia-postgres --database=lia_db --user=lia_user
# No prompt SQL:
# SELECT version();
# \dt
```

### 10.3 Testar Redis

```bash
REDIS_HOST=$(gcloud redis instances describe lia-redis --region=$REGION --format='value(host)')
REDIS_AUTH=$(gcloud redis instances describe lia-redis --region=$REGION --format='value(authString)')
echo "Teste manual: redis-cli -h $REDIS_HOST -a $REDIS_AUTH ping"
```

### 10.4 Health checks dos serviços

```bash
API_URL=$(gcloud run services describe lia-api \
  --region=$REGION --format='value(status.url)')

echo "=== Health Check ==="
curl -sf "${API_URL}/api/v1/health" | python3 -m json.tool

echo "=== Readiness ==="
curl -sf "${API_URL}/api/v1/health/ready" | python3 -m json.tool

echo "=== Liveness ==="
curl -sf "${API_URL}/api/v1/health/live" | python3 -m json.tool

FRONTEND_URL=$(gcloud run services describe lia-frontend \
  --region=$REGION --format='value(status.url)')

echo "=== Frontend ==="
curl -sf -o /dev/null -w "HTTP %{http_code}" "${FRONTEND_URL}/"
```

### 10.5 Testar conectividade Cloud Run → Cloud SQL

```bash
gcloud run services logs read lia-api \
  --region=$REGION --limit=20 \
  --format="table(timestamp,textPayload)"

API_URL=$(gcloud run services describe lia-api \
  --region=$REGION --format='value(status.url)')
curl -sf "${API_URL}/api/v1/health/ready" | python3 -m json.tool
```

> O endpoint `/api/v1/health/ready` verifica conexão com banco e Redis.
> Se retornar `"database": "ok"`, a conectividade Cloud Run → Cloud SQL está funcionando.

### 10.5.1 Testar conectividade Cloud Run → Redis (Memorystore)

```bash
curl -sf "${API_URL}/api/v1/health/ready" | python3 -c "
import sys, json
data = json.load(sys.stdin)
redis_ok = data.get('redis', data.get('cache', 'unknown'))
print(f'Redis status: {redis_ok}')
if redis_ok != 'ok':
    print('⚠️  Redis connectivity issue — check VPC connector and REDIS_URL')
    sys.exit(1)
print('✅ Cloud Run → Memorystore connectivity OK')
"
```

> Se o health/ready não incluir status do Redis, verificar manualmente nos logs:
> ```bash
> gcloud run services logs read lia-api --region=$REGION --limit=50 | grep -i redis
> ```

### 10.6 Testar DNS

```bash
for DOMAIN in wedotalent.cc www.wedotalent.cc api.wedotalent.cc; do
  echo "${DOMAIN}: $(dig +short $DOMAIN A)"
done
```

### 10.7 Testar SSL

```bash
for DOMAIN in wedotalent.cc api.wedotalent.cc; do
  echo | openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} 2>/dev/null | \
    openssl x509 -noout -dates -subject
done
```

### 10.8 Testar Worker (Celery)

O worker usa `--no-allow-unauthenticated`, então o curl precisa de identity token:

```bash
WORKER_URL=$(gcloud run services describe lia-worker \
  --region=$REGION --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token)
curl -sf -H "Authorization: Bearer ${TOKEN}" "${WORKER_URL}/health" | python3 -m json.tool
```

- [ ] APIs habilitadas confirmadas
- [ ] Cloud SQL conecta (gcloud sql connect)
- [ ] Redis responde PONG (redis-cli)
- [ ] Health endpoints da API retornam 200
- [ ] Frontend retorna 200
- [ ] Cloud Run → Cloud SQL connectivity OK (/api/v1/health/ready → database: ok)
- [ ] Cloud Run → Memorystore connectivity OK (/api/v1/health/ready → redis: ok)
- [ ] DNS resolve para IP do LB (todos os 5 records)
- [ ] SSL válido e ACTIVE (wedotalent.cc + api.wedotalent.cc)
- [ ] Worker health OK (/health → status: ok)

---

## Estimativa de Custo Mensal

> Valores estimados para produção (us-east1, abril 2026).
> Baseados em pricing público do GCP. Podem variar com uso real.

| Componente | Spec | Custo/mês (USD) |
|---|---|---|
| **Cloud SQL** (PostgreSQL 16) | db-custom-2-8192, 50GB SSD, HA regional | ~$130–170 |
| **Memorystore** (Redis 7.2) | Standard tier, 2GB | ~$80–100 |
| **Cloud Run — lia-frontend** | 1 vCPU, 512Mi, min=1, max=10 | ~$30–60 |
| **Cloud Run — lia-api** | 2 vCPU, 1Gi, min=1, max=20 | ~$60–120 |
| **Cloud Run — lia-worker** | 2 vCPU, 1Gi, min=1, max=5, always-on | ~$80–120 |
| **Cloud Storage** | 2 buckets, ~10GB estimado | ~$1–5 |
| **Artifact Registry** | ~5GB de imagens Docker | ~$1–3 |
| **Load Balancer** (HTTPS) | Forwarding rules + data processing | ~$20–30 |
| **Cloud Armor** (WAF) | 1 policy + 3 rules | ~$5–10 |
| **SSL Certificates** (managed) | 2 certificates | Gratuito |
| **Secret Manager** | ~20 secrets, low access volume | ~$1 |
| **VPC Connector** | Serverless VPC Access | ~$7–10 |
| **Networking** (egress) | ~100GB/mês estimado | ~$10–15 |
| | | |
| **TOTAL ESTIMADO** | | **~$425–640/mês** |

### Notas de otimização

- **Staging**: reduzir `min-instances=0` em todos os serviços → ~$0 quando inativo
- **Cloud SQL**: começar com `db-f1-micro` em staging (~$8/mês)
- **Memorystore**: começar com Basic tier 1GB em staging (~$35/mês)
- **Committed Use Discounts**: 1 year CUD em Cloud SQL = ~40% desconto
- **Worker**: se volume de tasks for baixo, considerar `min-instances=0` e aceitar cold start

---

## Resumo de Serviços Cloud Run

| Serviço | Porta | Auth | CPU Throttling | min/max | Uso |
|---|---|---|---|---|---|
| `lia-frontend` | 3000 | Público | Sim (padrão) | 1/10 | Next.js SSR |
| `lia-api` | 8000 | Público* | Sim (padrão) | 1/20 | FastAPI + Gunicorn |
| `lia-worker` | 8080** | Privado | **Desabilitado** | 1/5 | Celery worker |

\* API é pública porque recebe webhooks (Twilio, Teams). Autenticação JWT é feita no app.
\** Worker usa health wrapper HTTP (`scripts/worker_health.py`) para Cloud Run readiness.

---

## Arquivos de referência no projeto

| Arquivo | Conteúdo |
|---|---|
| `DEPLOY_GUIDE.md` | Guia geral de deploy (histórico + arquitetura) |
| `GITHUB_SECRETS_SETUP.md` | Secrets para CI/CD no GitHub |
| `plataforma-lia/.github/workflows/deploy.yml` | CI/CD frontend |
| `lia-agent-system/.github/workflows/deploy.yml` | CI/CD backend |
| `lia-agent-system/.env.production.example` | Todas as env vars do backend |
| `lia-agent-system/Dockerfile.prod` | Dockerfile API (Gunicorn) |
| `lia-agent-system/Dockerfile.worker` | Dockerfile Worker (Celery + health) |
| `lia-agent-system/scripts/worker_health.py` | Health wrapper para Cloud Run |
| `lia-agent-system/terraform/gcp/` | Terraform base (VM, não Cloud Run — referência histórica) |
