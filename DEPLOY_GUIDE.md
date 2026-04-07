# LIA Platform — Guia de Deploy e Fluxo de Desenvolvimento

> **Documento de referência para o time de engenharia.**
> Cobre a jornada completa: do ambiente de desenvolvimento no Replit até a produção no GCP Cloud Run, passando pelo ambiente de staging.

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Estado Atual (ANTES)](#2-estado-atual-antes)
3. [Estado Alvo (DEPOIS)](#3-estado-alvo-depois)
4. [Fluxo de Desenvolvimento ao Cliente](#4-fluxo-de-desenvolvimento-ao-cliente)
5. [Ambientes](#5-ambientes)
6. [Passo a Passo de Deploy](#6-passo-a-passo-de-deploy)
7. [Fluxo de Trabalho do Time](#7-fluxo-de-trabalho-do-time)
8. [Variáveis de Ambiente](#8-variáveis-de-ambiente)
9. [Checklist Pré-Go-Live](#9-checklist-pré-go-live)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Visão Geral da Arquitetura

A Plataforma LIA é composta por três serviços independentes que se comunicam:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLATAFORMA LIA                           │
│                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐                   │
│   │  plataforma-lia  │    │ lia-agent-system │                  │
│   │  (Next.js 15)   │◄──►│ (FastAPI/Python) │                  │
│   │  React/Tailwind  │    │  Claude/Gemini   │                  │
│   │  Porta: 5000    │    │  Porta: 8001     │                  │
│   └────────┬────────┘    └────────┬─────────┘                  │
│            │                      │                             │
│            └──────────┬───────────┘                             │
│                       ▼                                         │
│            ┌─────────────────────┐                             │
│            │    ats-api-copia    │                             │
│            │   (Rails 7 / REST)  │                             │
│            │   PostgreSQL (DB)   │                             │
│            └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

| Serviço | Repositório | Tecnologia | Responsabilidade |
|---|---|---|---|
| Frontend | `ats-front-copia` | Next.js 15 + React + Tailwind | Interface do usuário, pages, componentes |
| AI Agent | `lia-agent-system` | FastAPI + Python + LangGraph | Agentes IA, orquestração, integrações |
| Rails API | `ats-api-copia` | Rails 7 + PostgreSQL | Core de dados, autenticação, business logic |

---

## 2. Estado Atual (ANTES)

### Infraestrutura em Produção Hoje

```
┌──────────────────────────────────────────────────────────────────┐
│                     STACK LEGADA (ANTES)                         │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────┐    │
│  │    wedo-nuxt-copia   │    │   recruiter-agent-v5-copia   │   │
│  │  (Vue 3 / Nuxt)     │◄──►│  (Python / Gemini / Langchain│   │
│  │  Frontend Legado    │    │   Agente Legado)             │   │
│  └──────────┬──────────┘    └──────────────┬───────────────┘   │
│             │                               │                    │
│             └───────────────┬───────────────┘                   │
│                             ▼                                    │
│                ┌────────────────────────┐                       │
│                │     ats-api-copia      │                       │
│                │  (Rails 7 + PostgreSQL) │                       │
│                │  ← permanece inalterado │                       │
│                └────────────────────────┘                       │
│                                                                  │
│  Ambiente:   Servidor próprio / VPS                             │
│  Deploy:     Manual (sem CI/CD)                                 │
│  Domínio:    wedotalent.cc                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Limitações do stack legado:**
- Frontend Vue/Nuxt sem sistema de design padronizado
- Agente Python básico sem LangGraph / sem memória contextual
- Deploy manual sem pipeline de CI/CD
- Sem ambiente de staging separado
- Sem observabilidade centralizada (logs, traces, alertas)

---

## 3. Estado Alvo (DEPOIS)

### Infraestrutura LIA no GCP

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        STACK LIA — GCP (DEPOIS)                          │
│                                                                          │
│   Domínio: wedotalent.cc          SSL: Google-managed Certificate        │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Cloud Load Balancer                           │   │
│   │              (SSL termination + path-based routing)              │   │
│   └──────────────┬───────────────────────────┬───────────────────────┘  │
│                  │ /                          │ /api/agent/*             │
│                  ▼                            ▼                          │
│   ┌──────────────────────────┐  ┌──────────────────────────────────┐   │
│   │   Cloud Run: lia-frontend │  │   Cloud Run: lia-agent           │   │
│   │   (Next.js 15 / Docker)   │  │   (FastAPI / Docker)             │   │
│   │   Min 1 instance          │  │   Min 1 instance                 │   │
│   │   Max 10 instances        │  │   Max 5 instances                │   │
│   │   2 vCPU / 2 GB RAM       │  │   4 vCPU / 4 GB RAM             │   │
│   └─────────────┬─────────────┘  └───────────────┬──────────────────┘  │
│                 │                                 │                      │
│                 └─────────────┬───────────────────┘                     │
│                               ▼                                          │
│              ┌────────────────────────────────┐                         │
│              │      Cloud SQL (PostgreSQL 16)   │                        │
│              │      Instância compartilhada     │                        │
│              │      Rails DB + LIA DB           │                        │
│              └────────────────────────────────┘                         │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐     │
│   │ Cloud Storage │  │ Cloud Redis  │  │    Secret Manager        │     │
│   │  (CVs/Docs)  │  │  (Cache/Job) │  │  (API Keys / Env Vars)   │     │
│   └──────────────┘  └──────────────┘  └──────────────────────────┘     │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐                                   │
│   │ Cloud Logging │  │   Sentry     │                                   │
│   │  (Observ.)   │  │   (Erros)    │                                   │
│   └──────────────┘  └──────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Ganhos com a nova arquitetura:**
- Auto-scaling: Cloud Run sobe instâncias automaticamente sob carga
- Zero downtime deploy: Cloud Run faz blue/green deployment nativo
- Banco compartilhado: Rails e FastAPI leem o mesmo PostgreSQL (Cloud SQL)
- CI/CD automático: push na `main` → staging; tag `v*.*.*` → produção
- Observabilidade: logs centralizados no Cloud Logging + erros no Sentry
- Segredos gerenciados: Secret Manager (sem `.env` em produção)

---

## 4. Fluxo de Desenvolvimento ao Cliente

### Visão completa — do código à produção

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUXO: DESENVOLVIMENTO → PRODUÇÃO                     │
│                                                                          │
│                                                                          │
│  1. DESENVOLVIMENTO                                                      │
│  ─────────────────                                                       │
│                                                                          │
│   Replit (ambiente central)   ←→   VS Code / Cursor (time)             │
│   ┌──────────────────────┐         ┌──────────────────────┐            │
│   │  plataforma-lia/     │         │  Clone do repo       │            │
│   │  lia-agent-system/   │         │  git clone <repo>    │            │
│   │  Porta 5000 + 8001   │         │  npm run dev         │            │
│   └──────────┬───────────┘         └──────────────────────┘            │
│              │                                                           │
│              │ git push → branch feature/*                              │
│              ▼                                                           │
│                                                                          │
│  2. PULL REQUEST                                                         │
│  ───────────────                                                         │
│                                                                          │
│   feature/* ──────────────► develop                                     │
│                                PR review                                 │
│                                Testes automáticos (GitHub Actions)      │
│                                                                          │
│                                                                          │
│  3. STAGING                                                              │
│  ──────────                                                              │
│                                                                          │
│   develop branch → deploy automático → STAGING GCP                      │
│   ┌───────────────────────────────────────────────────────┐             │
│   │  staging.wedotalent.cc                                │             │
│   │  Cloud Run (staging) ← banco de dados staging         │             │
│   │  Testes manuais pelo time + demos para cliente        │             │
│   └───────────────────────────────────────────────────────┘             │
│              │                                                           │
│              │  Aprovação do time / QA                                   │
│              ▼                                                           │
│                                                                          │
│  4. PRODUÇÃO                                                             │
│  ─────────────                                                           │
│                                                                          │
│   develop → main  (merge manual com aprovação)                           │
│   main branch → deploy automático → PRODUÇÃO GCP                        │
│   ┌───────────────────────────────────────────────────────┐             │
│   │  wedotalent.cc                                        │             │
│   │  Cloud Run (prod) ← banco de dados produção          │             │
│   │  Clientes finais acessam aqui                        │             │
│   └───────────────────────────────────────────────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Estratégia de branches

```
main          ──────────────────────────────────►  PRODUÇÃO
                       ▲
develop       ──────────────────────────────────►  STAGING
                  ▲          ▲
feature/*     ────┘    ──────┘   branches de feature (PR → develop)
```

| Branch | Ambiente | Deploy | Banco |
|---|---|---|---|
| `feature/*` | Replit / local | Manual (dev) | SQLite / Postgres local |
| `develop` | Staging GCP | Automático (push) | Cloud SQL staging |
| `main` | Produção GCP | Automático (push) | Cloud SQL produção |

---

## 5. Ambientes

### Comparação dos três ambientes

| | **Desenvolvimento** | **Staging** | **Produção** |
|---|---|---|---|
| **URL Frontend** | `localhost:5000` | `staging.wedotalent.cc` | `wedotalent.cc` |
| **URL Backend** | `localhost:8001` | `api-staging.wedotalent.cc` | `api.wedotalent.cc` |
| **Banco** | PostgreSQL local (Replit) | Cloud SQL - instância staging | Cloud SQL - instância prod |
| **AI Models** | Claude + Gemini (keys do Replit) | Mesmas keys (Secret Manager) | Mesmas keys (Secret Manager) |
| **Deploy** | Automático no Replit | GitHub Actions → Cloud Run | GitHub Actions → Cloud Run |
| **Logs** | Console Replit | Cloud Logging | Cloud Logging + Sentry |
| **Branch** | feature/* | develop | main |

### Conectar Replit ao Staging

Para testar features do Replit contra o banco de staging (sem subir código):

```bash
# No Replit, mudar temporariamente as variáveis de ambiente:
DATABASE_URL=<staging-cloud-sql-url>
NEXT_PUBLIC_BACKEND_URL=https://api-staging.wedotalent.cc

# Reiniciar os serviços localmente
```

> **Atenção:** Nunca apontar o Replit para o banco de **produção** durante desenvolvimento.

---

## 6. Passo a Passo de Deploy

### Fase 1 — Preparação do código (Replit)

#### 1.1 Dockerfile do Next.js

Criar `plataforma-lia/Dockerfile`:

```dockerfile
FROM node:22-alpine AS base

FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json bun.lock* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]
```

Adicionar em `plataforma-lia/next.config.js`:
```js
output: 'standalone'  // necessário para Docker otimizado
```

#### 1.2 Arquivo de variáveis de referência

Criar `plataforma-lia/.env.production.example`:

```bash
# Frontend (Next.js)
NEXT_PUBLIC_BACKEND_URL=https://api.wedotalent.cc
NEXT_PUBLIC_APP_URL=https://wedotalent.cc

# Auth (Microsoft/Azure AD)
MICROSOFT_APP_ID=246eb1e7-a437-4cb2-a231-0325b567be5f
MICROSOFT_APP_PASSWORD=<secret>
AZURE_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6

# Analytics (opcional)
NEXT_PUBLIC_SENTRY_DSN=<sentry-dsn>
```

Criar `lia-agent-system/.env.production.example`:

```bash
# Database (Cloud SQL compartilhado com Rails)
DATABASE_URL=postgresql://lia_user:<password>@<cloud-sql-ip>/lia_db

# AI Models
ANTHROPIC_API_KEY=<secret>
GEMINI_API_KEY=<secret>

# Microsoft Teams Bot
MICROSOFT_APP_ID=246eb1e7-a437-4cb2-a231-0325b567be5f
MICROSOFT_APP_PASSWORD=<secret>
AZURE_TENANT_ID=bd25f438-71ab-4f63-a88f-abc8da37a1f6

# Cache
REDIS_URL=redis://<cloud-redis-ip>:6379

# Rails API (para chamadas entre serviços, se necessário)
RAILS_API_URL=https://api.wedotalent.cc
RAILS_API_KEY=<secret>

# Observability
SENTRY_DSN=<sentry-dsn>
```

#### 1.3 Configuração do banco compartilhado

No `lia-agent-system/app/core/config.py`, garantir que o `DATABASE_URL` venha de variável de ambiente (já existe):

```python
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://lia_user:lia_password@localhost/lia_db")
```

Para staging/produção, apenas apontar a variável para o Cloud SQL do Rails.

---

### Fase 2 — GitHub (repositórios)

#### 2.1 Push do frontend para `ats-front-copia`

```bash
cd plataforma-lia/
git init
git remote add origin https://github.com/wedocc2026/ats-front-copia.git
git add .
git commit -m "feat: initial LIA platform frontend"
git push -u origin main
```

#### 2.2 Push do agent para repositório próprio

```bash
cd lia-agent-system/
git init
git remote add origin https://github.com/wedocc2026/lia-agent-system.git
git add .
git commit -m "feat: initial LIA agent system"
git push -u origin main
```

#### 2.3 GitHub Actions — CI/CD Frontend

Criar `.github/workflows/deploy.yml` em `ats-front-copia`:

```yaml
name: Deploy LIA Frontend

on:
  push:
    branches: [develop, main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build and Push Docker Image
        run: |
          gcloud builds submit \
            --tag gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }}

      - name: Deploy to Cloud Run (Staging)
        if: github.ref == 'refs/heads/develop'
        run: |
          gcloud run deploy lia-frontend-staging \
            --image gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }} \
            --region us-central1

      - name: Deploy to Cloud Run (Production)
        if: github.ref == 'refs/heads/main'
        run: |
          gcloud run deploy lia-frontend \
            --image gcr.io/${{ env.GCP_PROJECT }}/lia-frontend:${{ github.sha }} \
            --region us-central1
```

#### 2.4 GitHub Actions — CI/CD Agent

Mesma estrutura, para o repositório `lia-agent-system`, apontando para o serviço Cloud Run `lia-agent-staging` / `lia-agent`.

---

### Fase 3 — GCP (time de infra)

> O Terraform já existe em `lia-agent-system/terraform/gcp/`. Use-o como base.

#### 3.1 Cloud SQL

```bash
# Criar instância
gcloud sql instances create lia-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-standard-2 \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=100GB

# Criar banco para o LIA Agent
gcloud sql databases create lia_db --instance=lia-postgres

# Criar banco para Rails (se migrar do servidor atual)
gcloud sql databases create ats_production --instance=lia-postgres

# Rodar migrations
# Rails:
RAILS_ENV=production DATABASE_URL=<cloud-sql-url> rails db:migrate
# FastAPI (Alembic):
DATABASE_URL=<cloud-sql-url> alembic upgrade head
```

#### 3.2 Secret Manager

```bash
# Criar todos os segredos
echo -n "sk-ant-..." | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
echo -n "AIza..."    | gcloud secrets create GEMINI_API_KEY    --data-file=-
echo -n "..."        | gcloud secrets create MS_APP_PASSWORD   --data-file=-
# ... demais segredos
```

#### 3.3 Cloud Run — Frontend

```bash
gcloud run deploy lia-frontend \
  --image gcr.io/<project>/lia-frontend:latest \
  --region us-central1 \
  --platform managed \
  --min-instances 1 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --port 3000 \
  --set-secrets MICROSOFT_APP_ID=MICROSOFT_APP_ID:latest \
  --set-env-vars NEXT_PUBLIC_BACKEND_URL=https://api.wedotalent.cc
```

#### 3.4 Cloud Run — AI Agent

```bash
gcloud run deploy lia-agent \
  --image gcr.io/<project>/lia-agent:latest \
  --region us-central1 \
  --platform managed \
  --min-instances 1 \
  --max-instances 5 \
  --memory 4Gi \
  --cpu 4 \
  --port 8001 \
  --set-secrets ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --set-secrets DATABASE_URL=DATABASE_URL:latest
```

#### 3.5 Load Balancer + Domínio

```bash
# Criar IP estático
gcloud compute addresses create lia-lb-ip --global

# Criar Cloud Armor policy (segurança)
gcloud compute security-policies create lia-security-policy \
  --description="LIA Platform WAF"

# Configurar domínio via DNS:
# wedotalent.cc       A    <IP estático>
# *.wedotalent.cc     A    <IP estático>
```

#### 3.6 Cloud Storage (uploads)

```bash
gcloud storage buckets create gs://lia-uploads-prod \
  --location=us-central1 \
  --uniform-bucket-level-access

# Lifecycle: mover CVs com +1 ano para Nearline
gcloud storage buckets update gs://lia-uploads-prod \
  --lifecycle-file=lifecycle-config.json
```

---

### Fase 4 — Staging (ambiente de testes)

O staging segue a **mesma infraestrutura**, com instâncias menores e banco separado:

```bash
# Cloud SQL staging
gcloud sql databases create lia_db_staging --instance=lia-postgres

# Cloud Run staging — frontend
gcloud run deploy lia-frontend-staging \
  --image gcr.io/<project>/lia-frontend:develop-latest \
  --region us-central1 \
  --min-instances 0 \   # pode escalar para zero (economiza custo)
  --max-instances 3 \
  --set-env-vars NEXT_PUBLIC_BACKEND_URL=https://api-staging.wedotalent.cc

# Cloud Run staging — agent
gcloud run deploy lia-agent-staging \
  --image gcr.io/<project>/lia-agent:develop-latest \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 2
```

**DNS para staging:**

```
staging.wedotalent.cc       → Cloud Run: lia-frontend-staging
api-staging.wedotalent.cc   → Cloud Run: lia-agent-staging
```

---

## 7. Fluxo de Trabalho do Time

### Rotina diária de desenvolvimento

```
Dev (Replit ou VS Code/Cursor)
│
├── 1. Puxa a branch develop atualizada
│       git checkout develop && git pull
│
├── 2. Cria branch de feature
│       git checkout -b feature/nome-da-feature
│
├── 3. Desenvolve e testa localmente
│       npm run dev (frontend, porta 5000)
│       uvicorn app.main:app (backend, porta 8001)
│
├── 4. Commit + Push
│       git add . && git commit -m "feat: descrição"
│       git push origin feature/nome-da-feature
│
├── 5. Abre Pull Request → develop
│       GitHub PR: feature/* → develop
│       GitHub Actions roda testes automáticos
│       Code review do time
│
├── 6. Merge → staging automático
│       Aprovado e mergeado → deploy automático no staging
│       staging.wedotalent.cc recebe as mudanças
│
├── 7. Validação no staging
│       QA manual / demos para cliente
│       Se aprovado → PR: develop → main
│
└── 8. Deploy produção
        Merge para main → deploy automático produção
        wedotalent.cc recebe as mudanças
```

### Como o Replit se encaixa após o deploy

```
┌─────────────────────────────────────────────────────────┐
│                   Replit — Papéis pós-deploy            │
│                                                         │
│  PROTOTIPAGEM (PM / Design)                             │
│  ├── Criar novas telas e componentes                   │
│  ├── Testar fluxos de UX rapidamente                   │
│  └── Validar com cliente antes de implementar          │
│                                                         │
│  DESENVOLVIMENTO REAL (Engenharia)                      │
│  ├── Replit como ambiente de dev compartilhado         │
│  ├── VS Code / Cursor via SSH ou clone do repo         │
│  └── Todos apontam para o mesmo repositório GitHub     │
│                                                         │
│  DEBUGGING (Qualquer membro do time)                   │
│  ├── Reproduzir bugs de produção localmente            │
│  ├── Testar hotfixes antes de subir para staging       │
│  └── Explorar logs e traces em tempo real              │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Variáveis de Ambiente

### Referência completa por serviço

#### Frontend — `plataforma-lia`

| Variável | Dev (Replit) | Staging | Produção |
|---|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8001` | `https://api-staging.wedotalent.cc` | `https://api.wedotalent.cc` |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:5000` | `https://staging.wedotalent.cc` | `https://wedotalent.cc` |
| `MICROSOFT_APP_ID` | `246eb1e7-...` | `246eb1e7-...` | `246eb1e7-...` |
| `MICROSOFT_APP_PASSWORD` | via Replit Secrets | Secret Manager | Secret Manager |
| `AZURE_TENANT_ID` | `bd25f438-...` | `bd25f438-...` | `bd25f438-...` |

#### Backend — `lia-agent-system`

| Variável | Dev (Replit) | Staging | Produção |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://localhost/lia_db` | Cloud SQL staging | Cloud SQL prod |
| `ANTHROPIC_API_KEY` | via Replit Secrets | Secret Manager | Secret Manager |
| `GEMINI_API_KEY` | via Replit Secrets | Secret Manager | Secret Manager |
| `REDIS_URL` | `redis://localhost:6379` | Cloud Redis staging | Cloud Redis prod |
| `MICROSOFT_APP_ID` | `246eb1e7-...` | `246eb1e7-...` | `246eb1e7-...` |
| `MICROSOFT_APP_PASSWORD` | via Replit Secrets | Secret Manager | Secret Manager |
| `AZURE_TENANT_ID` | `bd25f438-...` | `bd25f438-...` | `bd25f438-...` |
| `RAILS_API_URL` | `http://localhost:3000` | `https://api-staging.wedotalent.cc` | `https://api.wedotalent.cc` |
| `SENTRY_DSN` | (opcional) | obrigatório | obrigatório |

---

## 9. Checklist Pré-Go-Live

### Código (Replit / time dev)

- [ ] Dockerfile do `plataforma-lia` criado e testado com `docker build`
- [ ] `next.config.js` com `output: 'standalone'`
- [ ] `.env.production.example` completo e documentado
- [ ] `lia-agent-system` aponta para `DATABASE_URL` via variável de ambiente
- [ ] GitHub Actions configurado nos dois repositórios
- [ ] Testes E2E passando no staging
- [ ] Sentry configurado e recebendo eventos de teste
- [ ] Bot Teams funcionando com Tenant ID correto (`bd25f438-...`)

### Infraestrutura (time infra)

- [ ] Cloud SQL provisionado e com backup automático configurado
- [ ] Migrations rodadas (Rails + Alembic)
- [ ] Secret Manager populado com todas as variáveis
- [ ] Cloud Run (frontend + agent) deployado em staging
- [ ] Cloud Run (frontend + agent) deployado em produção
- [ ] Load Balancer configurado com SSL
- [ ] DNS apontando: `wedotalent.cc` + `staging.wedotalent.cc` + APIs
- [ ] Cloud Storage criado para uploads de arquivos
- [ ] Cloud Armor (WAF) ativo
- [ ] Alertas de Cloud Monitoring configurados (CPU, latência, erros 5xx)

### Validação funcional (time completo)

- [ ] Login / Autenticação funcionando em produção
- [ ] Criação e listagem de vagas
- [ ] Upload e parsing de CVs
- [ ] Chat com LIA (agente Claude)
- [ ] Bot do Teams respondendo
- [ ] Funil de candidatos (kanban)
- [ ] Geração de relatórios
- [ ] Envio de notificações

---

## 10. Troubleshooting

### Backend não sobe (ImportError)

Causa comum: função privada (`_calculate_confidence`) não exportada por `import *`.

```bash
# Verificar qual módulo está falhando
cd lia-agent-system
python3 -c "from app.main import app"

# Solução: exportar explicitamente a função privada no shim
# Editar app/shared/services/<service>.py e adicionar:
from app.domains.<domain>.services.<service> import _nome_da_funcao  # noqa: F401
```

### Bot Teams retorna 401

Verificar propagação do App Registration no Azure:
```
App ID: 246eb1e7-a437-4cb2-a231-0325b567be5f
Tenant: bd25f438-71ab-4f63-a88f-abc8da37a1f6
```
A propagação pode levar até 24h após mudança de Tenant ID. Não requer alteração de código.

### Cloud Run com cold start alto

Definir `--min-instances 1` para evitar que a instância escale para zero:
```bash
gcloud run services update lia-frontend \
  --min-instances 1 \
  --region us-central1
```

### Banco de dados — conexão recusada no Cloud Run

Cloud Run precisa do Cloud SQL Auth Proxy. Verificar:
```bash
gcloud run services update lia-agent \
  --add-cloudsql-instances <project>:us-central1:lia-postgres \
  --region us-central1
```

---

## Repositórios e Contatos

| Repositório | URL | Responsável |
|---|---|---|
| Frontend LIA | `github.com/wedocc2026/ats-front-copia` | Time Front |
| AI Agent LIA | `github.com/wedocc2026/lia-agent-system` | Time Back / AI |
| Rails API | `github.com/wedocc2026/ats-api-copia` | Time Back |
| Terraform GCP | `lia-agent-system/terraform/gcp/` | Time Infra |

---

*Última atualização: Abril 2026*
*Domínio: wedotalent.cc · Região GCP: us-central1 · Stack: Next.js 15 + FastAPI + Rails 7*
