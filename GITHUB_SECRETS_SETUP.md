# GitHub Secrets — Configuração para CI/CD

Este documento lista todos os secrets que devem ser configurados nos repositórios
GitHub para que os workflows de CI/CD funcionem corretamente.

## Repositórios

| Repositório | URL | Descrição |
|---|---|---|
| `wedocc2026/plataforma-lia` | github.com/wedocc2026/plataforma-lia | Frontend Next.js |
| `wedocc2026/lia-agent-system` | github.com/wedocc2026/lia-agent-system | Backend FastAPI |

## Secrets Compartilhados (ambos os repos)

| Secret | Descrição | Exemplo |
|---|---|---|
| `GCP_SA_KEY` | JSON da service account GCP com permissões de deploy | `{"type":"service_account",...}` |
| `GCP_PROJECT` | ID do projeto GCP | `wedotalent-prod` |
| `GCP_REGION` | Região GCP (opcional, default: us-east1) | `us-east1` |

### Permissões da Service Account (GCP_SA_KEY)

A service account precisa dos seguintes papéis IAM:
- `roles/run.admin` — Deploy Cloud Run services
- `roles/artifactregistry.writer` — Push Docker images
- `roles/iam.serviceAccountUser` — Act as service account

## Secrets do Frontend (`plataforma-lia`)

| Secret | Descrição | Exemplo |
|---|---|---|
| `APP_BASE_URL` | URL pública da aplicação | `https://wedotalent.cc` |
| `BACKEND_INTERNAL_URL` | URL interna do backend (Cloud Run service-to-service) | `https://lia-api-HASH-ue.a.run.app` |
| `SENTRY_DSN_FRONTEND` | DSN do Sentry para o frontend | `https://xxx@o123.ingest.sentry.io/456` |
| `WS_URL` | URL do WebSocket | `wss://wedotalent.cc` |
| `WHATSAPP_NUMBER` | Número WhatsApp para contato | `+551150289337` |

## Secrets do Backend (`lia-agent-system`)

Os secrets sensíveis do backend são injetados via **GCP Secret Manager** (não via GitHub Secrets).
O workflow de deploy referencia os secrets pelo nome no Secret Manager:

| Secret Manager Name | Descrição | Obrigatório |
|---|---|---|
| `DATABASE_URL` | Connection string PostgreSQL (Cloud SQL) | Sim |
| `REDIS_URL` | URL do Redis (Memorystore) com senha | Sim |
| `SECRET_KEY` | JWT signing key | Sim |
| `ANTHROPIC_API_KEY` | API key do Claude | Sim |
| `OPENAI_API_KEY` | API key do OpenAI (fallback) | Não |
| `SENTRY_DSN` | DSN do Sentry para o backend | Sim |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Se Twilio ativo |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Se Twilio ativo |
| `MAILGUN_API_KEY` | API key do Mailgun | Se email ativo |
| `WORKOS_API_KEY` | WorkOS API key (SSO) | Se SSO ativo |
| `WORKOS_CLIENT_ID` | WorkOS Client ID (SSO) | Se SSO ativo |

### Secrets usados apenas no CI (GitHub Secrets do backend)

| Secret | Descrição |
|---|---|
| `ANTHROPIC_API_KEY` | Usado nos testes do CI |
| `OPENAI_API_KEY` | Usado nos testes DeepEval |
| `LANGSMITH_API_KEY` | Usado na verificação LangSmith |

## Fluxo de Branches

```
feature/* ──→ develop (staging) ──→ main (produção)
                  │                       │
                  ▼                       ▼
          Cloud Run staging       Cloud Run produção
          lia-api-staging         lia-api
          lia-frontend-staging    lia-frontend
          lia-worker-staging      lia-worker
```

### Regras de proteção recomendadas

**Branch `main`:**
- Require pull request reviews (1 reviewer)
- Require status checks: CI (test suite), Security Scan
- No force push
- No deletion

**Branch `develop`:**
- Require status checks: CI (test suite)
- Allow merge without review (para staging rápido)

## Artifact Registry

Criar o repositório Docker no Artifact Registry antes do primeiro deploy:

```bash
gcloud artifacts repositories create lia \
  --repository-format=docker \
  --location=us-east1 \
  --description="LIA Platform Docker images"
```

## Política de Security Scans

Os scans de segurança (npm audit, bandit, pip-audit) são configurados como
**non-blocking** (`continue-on-error: true`) para não impedir deploys
durante a fase inicial. Após estabilização:

1. Remover `continue-on-error` dos steps de security scan
2. Mudar `needs: security` para bloquear o deploy se o scan falhar
3. Configurar alertas Dependabot nos repositórios GitHub

## API pública vs autenticada

- `lia-frontend`: `--allow-unauthenticated` (necessário — serve o app web)
- `lia-api`: `--allow-unauthenticated` (necessário — recebe webhooks Twilio/Teams
  e requisições autenticadas via JWT do frontend)
- `lia-worker`: Cloud Run Service com `--no-cpu-throttling --min-instances=1`
  (Celery worker contínuo com HTTP health wrapper em `scripts/worker_health.py`)

## Primeiros passos

1. Configurar todos os secrets listados acima nos repositórios GitHub
2. Criar o Artifact Registry repository (`lia`)
3. Criar os secrets no GCP Secret Manager
4. Push para `develop` → deploy automático para staging
5. Validar staging
6. Merge `develop` → `main` → deploy automático para produção
