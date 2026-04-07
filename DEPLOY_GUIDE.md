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

## 11. Mapa Completo de Integrações

> Análise extraída diretamente do código-fonte (`requirements.txt`, `package.json`, serviços e rotas). Cada integração tem status, função e o que é necessário para o deploy.

### 11.1 Modelos de Linguagem (LLMs)

| Integração | Status no código | Função | Chave necessária | GCP |
|---|---|---|---|---|
| **Claude (Anthropic)** | ✅ Core — em produção | Triagem de CVs, agente principal, análise de candidatos, WSI | `ANTHROPIC_API_KEY` | Secret Manager |
| **Gemini (Google AI)** | ✅ Core — em produção | Voz conversacional, chat LIA, busca semântica, insights | `GEMINI_API_KEY` | Secret Manager |
| **OpenAI** | ⚠️ Opcional | Fine-tuning export, busca por JD, triagem backup | `OPENAI_API_KEY` | Secret Manager (se ativo) |
| **LangSmith** | ⚠️ Opcional | Tracing de LLM calls, observabilidade de agentes | `LANGSMITH_API_KEY` | Secret Manager (se ativo) |

**LangGraph** (framework dos agentes) roda localmente — não é uma integração externa, é parte do código.

---

### 11.2 Voz e Transcrição (Google + Twilio)

```
Fluxo de triagem por voz:
Candidato → Twilio Voice (ligação) → Google Cloud Speech-to-Text (STT)
        → LIA Agent (Gemini / Claude análise) → resposta em áudio (TTS)
        → grava resultado no banco → notifica recrutador
```

| Integração | Arquivo principal | Função | Configuração GCP |
|---|---|---|---|
| **Google Cloud Speech-to-Text** | `app/api/v1/gemini_voice.py` | Transcrição das triagens por voz em tempo real | Habilitar API no projeto GCP |
| **Google Cloud Text-to-Speech** | `app/api/v1/voice.py` | LIA fala com o candidato durante triagem | Habilitar API no projeto GCP |
| **Twilio Voice** | `app/api/v1/twilio_voice.py` | Ligações reais (inbound/outbound), gravação | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| **Twilio WhatsApp** | `app/domains/communication/services/whatsapp_twilio_service.py` | WhatsApp via Twilio (alternativa ao Meta API) | mesmas credenciais Twilio |

> **Ação GCP:** Habilitar as APIs `speech.googleapis.com` e `texttospeech.googleapis.com` no projeto GCP. A autenticação usa o Service Account do Cloud Run — sem API key adicional.

---

### 11.3 Comunicação e Notificações

| Canal | Integração | Arquivo principal | Status | Configuração |
|---|---|---|---|---|
| **Email transacional** | Resend | `app/api/v1/email.py` | ✅ Ativo | `RESEND_API_KEY` |
| **WhatsApp (Meta)** | WhatsApp Business API | `app/domains/communication/services/whatsapp_meta_service.py` | ⚠️ Config pendente | `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` |
| **Microsoft Teams** | Bot Framework + Graph API | `app/domains/communication/services/teams_service.py` | ✅ Ativo (dev mode) | `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `AZURE_TENANT_ID` |
| **Teams SSO** | MSAL + Microsoft Graph | `app/domains/communication/services/teams_sso_service.py` | ✅ Ativo | mesmas credenciais MS |
| **Teams Recordings** | Microsoft Graph | `app/domains/communication/services/teams_recording_service.py` | ✅ Ativo | `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |

---

### 11.4 Agendamento e Calendário

| Integração | Arquivo | Função | Configuração |
|---|---|---|---|
| **Google Calendar** | `app/domains/interview_scheduling/services/calendar_service.py` | Criar/gerenciar entrevistas no Google Calendar | `GOOGLE_CALENDAR_CREDENTIALS` (service account JSON) |
| **Microsoft Calendar** | `app/domains/integrations_hub/services/microsoft_graph_service.py` | Agendamento via Outlook / Teams | mesmas credenciais Microsoft Graph |
| **APScheduler** | `app/jobs/scheduled_reports.py` | Jobs internos (relatórios agendados, alertas proativos) | sem config externa |
| **Celery** | `app/core/celery_app.py` | Tasks assíncronas longas (triagem em batch, exportações) | `CELERY_BROKER_URL` (RabbitMQ) |

---

### 11.5 Infraestrutura de Filas e Cache

```
Arquitetura de filas da LIA:
                                    ┌─────────────┐
FastAPI request ──► Celery task ──► │  RabbitMQ   │ ──► Celery worker processa
                                    └─────────────┘
                                          │
                              ┌───────────▼──────────┐
                              │         Redis         │
                              │  - Cache de sessões   │
                              │  - Token budgets      │
                              │  - HITL TTL store     │
                              │  - Celery result back │
                              └───────────────────────┘
```

| Serviço | Uso no código | Deploy no GCP |
|---|---|---|
| **Redis** | Cache, token budget, HITL store, Celery results | Cloud Memorystore (Redis) |
| **RabbitMQ (aio-pika)** | Message broker para Celery, jd_search, agent_chat_ws | Cloud Run sidecar ou VM dedicada |
| **Celery** | Workers assíncronos para triagem em batch, drift detection | Cloud Run (worker) separado |

> **Nota:** RabbitMQ é o único serviço que não tem managed service direto no GCP. Opções: (1) VM e2-small dedicada, (2) substituir por Cloud Pub/Sub (maior esforço de migração), (3) CloudAMQP (serviço gerenciado externo).

---

### 11.6 CRM e Sourcing Externo

| Integração | Arquivo | Função | Status | Config |
|---|---|---|---|---|
| **HubSpot** | `app/domains/company/services/hubspot_service.py` | Sync de empresas e contatos com CRM | ⚠️ Config pendente | `HUBSPOT_ACCESS_TOKEN` |
| **PEARCH** | `app/domains/sourcing/services/pearch_service.py` | Busca externa de candidatos (banco proprietário) | ⚠️ Config pendente | `PEARCH_API_KEY` |
| **GitHub** | `app/domains/sourcing/services/github_service.py` | Sourcing de devs via GitHub API | ✅ Ativo | `GITHUB_TOKEN` (injetado pelo Replit) |

---

### 11.7 Autenticação e Multi-tenant (WorkOS)

```
Fluxo de autenticação na LIA:

Usuário acessa wedotalent.cc
         │
         ▼
┌─────────────────────────┐
│   WorkOS SSO            │  ← Gerencia organizações (multi-tenant)
│   - Google SSO          │     Cada empresa = 1 organização WorkOS
│   - Microsoft SSO       │     session cookie: workos_session
│   - SAML Enterprise     │
└──────────┬──────────────┘
           │ workosProfile.organizationId
           ▼
┌─────────────────────────┐
│   Next.js Backend Proxy │  ← /api/backend-proxy/* lê workos_session
│   getWorkOSSession()    │     injeta organizationId em todas as requests
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   FastAPI / Rails API   │  ← filtra dados pelo organizationId (tenant)
└─────────────────────────┘
```

| Componente | Arquivo | Notas |
|---|---|---|
| **WorkOS SDK** | `plataforma-lia/src/lib/workos-session.ts` | Gerencia sessão multi-tenant |
| **Organização** | todos os `/api/backend-proxy/*.ts` | injeta `organizationId` nas chamadas |
| **SSO Providers** | WorkOS dashboard | Google, Microsoft, SAML configurados por empresa |

> **Para o deploy:** Configurar `WORKOS_API_KEY` e `WORKOS_CLIENT_ID` no Secret Manager. Registrar o domínio `wedotalent.cc` como redirect URI no WorkOS dashboard.

---

### 11.8 Observabilidade

| Ferramenta | Camada | Arquivo | Config |
|---|---|---|---|
| **Sentry** | Frontend + Backend | `sentry.client.config.ts`, `sentry-sdk[fastapi]` | `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN` |
| **Cloud Logging** | Backend | automático no Cloud Run | sem config adicional |
| **LangSmith** | Agentes LLM | `app/config/langsmith.py` | `LANGSMITH_API_KEY` (opcional) |
| **APM Cloud Monitoring** | GCP | via dashboards GCP | alertas configurados manualmente |

---

### 11.9 Plano de Ação para Integrações — O que falta plugar

| Prioridade | Integração | Status atual | Ação necessária |
|---|---|---|---|
| 🔴 Crítico | WorkOS | Código pronto, sem credenciais prod | Criar conta WorkOS Prod, configurar domínio, adicionar secrets |
| 🔴 Crítico | Claude (Anthropic) | Funciona no Replit | Mover chave para Secret Manager GCP |
| 🔴 Crítico | Gemini (Google AI) | Funciona no Replit | Habilitar Vertex AI no projeto GCP + Secret Manager |
| 🔴 Crítico | PostgreSQL (Cloud SQL) | Banco local no Replit | Provisionar Cloud SQL, rodar migrations |
| 🔴 Crítico | Redis (Memorystore) | redis local no Replit | Provisionar Cloud Memorystore |
| 🟡 Importante | Google Voice/STT | Código pronto | Habilitar APIs `speech.googleapis.com`, `texttospeech.googleapis.com` |
| 🟡 Importante | Twilio Voice + WhatsApp | Config pendente no Replit | Adicionar `TWILIO_*` ao Secret Manager |
| 🟡 Importante | Microsoft Teams Bot | Funciona (dev mode) | Registrar webhook URL de produção no Azure Bot Service |
| 🟡 Importante | Resend (email) | Código pronto | `RESEND_API_KEY` no Secret Manager |
| 🟡 Importante | RabbitMQ | Código pronto | Provisionar CloudAMQP ou VM e2-small |
| 🟡 Importante | Sentry | Código pronto | Criar projeto Sentry, adicionar DSN |
| 🟢 Desejável | HubSpot | Código pronto, config pendente | `HUBSPOT_ACCESS_TOKEN` quando necessário |
| 🟢 Desejável | PEARCH | Código pronto, config pendente | `PEARCH_API_KEY` (contato com PEARCH) |
| 🟢 Desejável | LangSmith | Código pronto | `LANGSMITH_API_KEY` quando quiser observabilidade de agentes |
| 🟢 Desejável | OpenAI | Fallback implementado | `OPENAI_API_KEY` se quiser usar GPT como fallback |

---

## 12. Avaliação — Frontend (Next.js / React / Tailwind)

> Status atual do `plataforma-lia/` para production readiness.

### O que está sólido

| Área | Situação |
|---|---|
| **Arquitetura** | Next.js 15 App Router, Server Components, Server Actions — padrão moderno |
| **Design System** | Tailwind + shadcn/ui, componentes padronizados com variantes CVA |
| **Tipagem** | TypeScript strict mode ativo, tipos bem definidos |
| **Auth** | WorkOS SSO integrado, `workos_session` cookie, middleware de proteção de rotas |
| **Proxy de API** | `/api/backend-proxy/*` centraliza todas as chamadas ao backend (boa separação) |
| **Observabilidade** | Sentry integrado no frontend |
| **Teams** | `@microsoft/teams-js` integrado, rotas de tab e auth criadas |
| **WebSockets** | Chat em tempo real via WS implementado |
| **Testes E2E** | Pasta `e2e/` com Playwright configurado |

### O que precisa de atenção antes do deploy

| Área | Problema | Ação |
|---|---|---|
| **Dockerfile** | Não existe ainda | Criar com `output: standalone` (Fase 1.1 deste guia) |
| **Variáveis de ambiente** | Mistura de hardcoded e `.env.local` | Auditar e mover tudo para Secret Manager |
| **WorkOS configuração prod** | `WORKOS_API_KEY` e `WORKOS_CLIENT_ID` apontam para dev | Criar ambiente de prod no WorkOS e configurar redirect URIs |
| **Error Boundaries** | Parcialmente implementado (`error-boundary.tsx`) | Verificar cobertura em pages críticas |
| **Hydration** | Possíveis mismatches em páginas com dados de sessão | Testar com `next build` e revisar warnings |
| **Bundle size** | Não auditado ainda | Rodar `next build` e checar `bundle-analyzer` |
| **Cache headers** | Não configurado | Configurar `Cache-Control` para assets estáticos via Cloud CDN |
| **CSP / Headers de segurança** | Não configurado em `next.config.js` | Adicionar `Content-Security-Policy`, `X-Frame-Options` |

### Checklist de production readiness — Frontend

- [ ] `Dockerfile` com `output: standalone` criado e testado
- [ ] `next build` passa sem erros e sem warnings críticos
- [ ] `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` de produção configurados
- [ ] Redirect URIs do WorkOS registrados para `wedotalent.cc`
- [ ] Sentry DSN de produção configurado (`NEXT_PUBLIC_SENTRY_DSN`)
- [ ] Todas as variáveis `NEXT_PUBLIC_*` auditadas (sem secrets expostos no cliente)
- [ ] Headers de segurança adicionados no `next.config.js`
- [ ] Error boundary verificado em pages críticas (funil, chat, vagas)
- [ ] Teste E2E passando (login → criar vaga → chat LIA → mover candidato)
- [ ] Teams Tab URL atualizada para domínio de produção

---

## 13. Avaliação — Camada de IA (Python / FastAPI / LangGraph)

> Status atual do `lia-agent-system/` para production readiness.

### Arquitetura de agentes

```
Requisição do usuário
        │
        ▼
┌───────────────────┐
│  FastAPI Router   │  ← 70+ endpoints organizados por domínio
│  (Port 8001)      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Intent Classifier │  ← Claude classifica a intenção da mensagem
│  (fast_router.py) │     antes de invocar o agente correto
└────────┬──────────┘
         │
    ┌────┴────────────────────────────┐
    │           DOMÍNIOS (40+)        │
    │                                 │
    │  ┌─────────────┐ ┌──────────┐  │
    │  │ CV Screening│ │ Sourcing │  │
    │  │  (LangGraph)│ │ (Graph)  │  │
    │  └─────────────┘ └──────────┘  │
    │  ┌─────────────┐ ┌──────────┐  │
    │  │Job Management│ │Analytics │  │
    │  └─────────────┘ └──────────┘  │
    │  ┌─────────────────────────┐   │
    │  │ Communication (Teams/WA)│   │
    │  └─────────────────────────┘   │
    └─────────────────────────────────┘
         │
         ▼
┌───────────────────┐
│  PostgreSQL       │  ← 69 ferramentas registradas
│  + pgvector       │     (candidate_tools, job_tools, analytics...)
│  Redis + RabbitMQ │
└───────────────────┘
```

### O que está sólido

| Área | Situação |
|---|---|
| **LangGraph** | Grafos de agentes implementados por domínio (cv_screening, sourcing, interview_scheduling) |
| **Tool Registry** | 69 ferramentas registradas e organizadas por domínio |
| **Policy Engine** | Controle de acesso e regras de negócio centralizadas |
| **Circuit Breakers** | Resiliência implementada para chamadas LLM e serviços externos |
| **PII Masking** | LGPD: mascaramento de dados pessoais no logger ativo |
| **HITL** | Human-in-the-loop implementado (aprovações antes de ações críticas) |
| **Alembic** | Migrations versionadas para o banco |
| **Dockerfile** | `Dockerfile` e `Dockerfile.prod` já existem |
| **Sentry** | `sentry-sdk[fastapi]` integrado |
| **WSI** | Voice Screening Interface implementado (triagem por voz) |

### O que precisa de atenção antes do deploy

| Área | Problema | Ação |
|---|---|---|
| **Shims de compatibilidade** | Funções privadas não exportadas pelos shims (import *) | ✅ Corrigido para os que encontramos — rodar `python3 -c "from app.main import app"` para validar todos |
| **GOOGLE_APPLICATION_CREDENTIALS** | Speech/TTS precisam de service account | Configurar Workload Identity no Cloud Run |
| **RabbitMQ** | Sem serviço gerenciado no GCP | Provisionar (ver Seção 11.5) |
| **Banco compartilhado** | `DATABASE_URL` precisa apontar para Cloud SQL com Rails | Configurar variável de ambiente (não requer mudança de código) |
| **Redis prod** | Sem autenticação configurada no código | Adicionar `REDIS_URL` com senha para Memorystore |
| **Celery workers** | Não configurado para Cloud Run | Adicionar segundo serviço Cloud Run para workers Celery |
| **LANGSMITH** | Opcional mas recomendado para debug em prod | Adicionar `LANGSMITH_API_KEY` |
| **Secrets hardcoded** | Verificar se há chaves hardcoded em algum arquivo | Auditar com `grep -r "sk-ant\|AIza\|ghp_" app/` |

### Checklist de production readiness — IA

- [ ] `python3 -c "from app.main import app"` passa sem erros
- [ ] `alembic upgrade head` roda clean no banco de produção
- [ ] Todas as variáveis LLM (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) no Secret Manager
- [ ] Service Account com permissão para Speech API e TTS configurado
- [ ] RabbitMQ provisionado e `CELERY_BROKER_URL` configurado
- [ ] `REDIS_URL` apontando para Cloud Memorystore (com senha)
- [ ] Celery worker rodando como serviço separado no Cloud Run
- [ ] Circuit breakers validados para cada LLM (Claude, Gemini, OpenAI)
- [ ] Sentry DSN backend configurado (`SENTRY_DSN`)
- [ ] Teams webhook URL atualizada para URL de produção do Cloud Run

---

## 14. Avaliação — Rails API e Banco de Dados

> `ats-api-copia` — o core de dados que permanece inalterado.

### O que o Rails API provê

| Recurso | Endpoint | Notas |
|---|---|---|
| Autenticação | `POST /v1/sessions` | Cria sessão (token JWT ou cookie) |
| Perfil | `GET /v1/me` | Dados do usuário logado |
| Candidatos | `GET/POST /v1/users/candidates` | CRUD de candidatos |
| Vagas | `GET/POST /v1/users/jobs` | CRUD de vagas |
| Aplicações | `GET /v1/users/applies` | Candidatos × Vagas |
| Processos seletivos | `GET /v1/users/selective_processes` | Funil por vaga |
| Mensagens | `GET/POST /v1/users/messages` | Histórico de comunicação |

### Estratégia de integração LIA ↔ Rails

```
OPÇÃO A (atual — mais simples):
  lia-agent-system ──REST──► ats-api-copia (Rails)
  Simples, mantém fronteira clara entre serviços.
  Latência adicional de ~5-20ms por request.

OPÇÃO B (banco compartilhado — mais performático):
  lia-agent-system ──SQL──► PostgreSQL (mesma instância que o Rails)
  Zero latência de rede interna.
  Requer acesso read/write direto às tabelas Rails.
  Risco: quebrar integridade se escrita não seguir convenções Rails.
```

**Recomendação:** usar Opção A para o MVP de produção (REST). A Opção B pode ser adotada progressivamente para queries de leitura pesada (analytics, busca de candidatos).

### Checklist de production readiness — Rails + Banco

- [ ] Cloud SQL provisionado (PostgreSQL 16)
- [ ] Banco Rails migrado para Cloud SQL (`rails db:migrate`)
- [ ] Banco LIA criado na mesma instância (`lia_db`)
- [ ] Migrations Alembic do FastAPI rodadas (`alembic upgrade head`)
- [ ] Backups automáticos habilitados no Cloud SQL (retenção 7 dias)
- [ ] Point-in-time recovery habilitado
- [ ] IP do Cloud Run autorizado a conectar no Cloud SQL
- [ ] Connection pooling configurado (pgBouncer ou Cloud SQL Proxy)
- [ ] URL do Rails API configurada em `RAILS_API_URL` no Secret Manager

---

## 15. Arquitetura Multi-tenant e LLM Factory

> O conceito central do produto: cada empresa usa a LIA com seu próprio contexto, dados e — futuramente — seu próprio modelo de linguagem.

### 15.1 Como o multi-tenant funciona hoje

```
┌─────────────────────────────────────────────────────────────┐
│                ISOLAMENTO POR TENANT (HOJE)                  │
│                                                              │
│  Empresa A (Tenant A)          Empresa B (Tenant B)         │
│  organizationId: org_aaa       organizationId: org_bbb       │
│                                                              │
│  WorkOS SSO → workos_session   WorkOS SSO → workos_session   │
│       │                               │                      │
│       ▼                               ▼                      │
│  /api/backend-proxy            /api/backend-proxy            │
│  (injeta org_aaa em todas      (injeta org_bbb em todas      │
│   as chamadas ao backend)       as chamadas ao backend)      │
│       │                               │                      │
│       ▼                               ▼                      │
│  FastAPI filtra por            FastAPI filtra por            │
│  company_id = org_aaa          company_id = org_bbb          │
│       │                               │                      │
│  MESMO banco PostgreSQL ──────────────┘                      │
│  Dados isolados por company_id                              │
└─────────────────────────────────────────────────────────────┘
```

**Nível de isolamento atual:** Lógico (por `company_id`/`organization_id` em todas as tabelas). Não é isolamento físico (banco separado por cliente). Para o mercado inicial, isso é suficiente e seguro.

---

### 15.2 LLM Factory — O conceito

O produto prevê que cada empresa-cliente possa plugar seu próprio modelo de linguagem:

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM FACTORY                                │
│                                                                 │
│  empresa-a → ANTHROPIC_API_KEY = sk-ant-xxx  → Claude          │
│  empresa-b → usa LIA SaaS (chave WeDO)       → Claude/Gemini   │
│  empresa-c → OPENAI_API_KEY = sk-openai-xxx  → GPT-4o          │
│  empresa-d → GEMINI_API_KEY = AIza-xxx       → Gemini Pro      │
│                                                                 │
│  Resolvido por:                                                 │
│  app/orchestrator/fast_router.py — seleciona o LLM             │
│  app/shared/resilience/circuit_breaker.py — fallback automático │
└─────────────────────────────────────────────────────────────────┘
```

**Status no código:** O `fast_router.py` e o `circuit_breaker.py` já implementam fallback entre modelos. A factory per-tenant (onde cada empresa usa sua própria chave) está no roadmap mas **não está completamente implementada** — hoje o sistema usa chaves globais (da WeDO).

**Para implementar LLM Factory completa:**
1. Adicionar tabela `company_llm_configs` (chave criptografada por company_id)
2. Modificar o `fast_router.py` para carregar a chave do tenant antes de invocar o LLM
3. Usar KMS do GCP para criptografar as chaves armazenadas no banco

---

### 15.3 WorkOS — Multi-tenant em produção

```
Plano WorkOS necessário para produção:
  - Tier: Enterprise (suporta múltiplas organizações, SAML, SCIM)
  - Configurações por ambiente: Dev, Staging, Production (3 ambientes)
  - SSO providers por organização: Google, Microsoft, SAML genérico

Configurações obrigatórias no WorkOS dashboard:
  - Redirect URIs:
      https://wedotalent.cc/api/auth/workos/callback
      https://staging.wedotalent.cc/api/auth/workos/callback
      http://localhost:5000/api/auth/workos/callback (dev)
  - Allowed origins:
      https://wedotalent.cc
      https://staging.wedotalent.cc
```

---

### 15.4 Evolução da arquitetura — Roadmap de multi-tenancy

| Fase | Descrição | Complexidade |
|---|---|---|
| **Fase 1 (atual)** | Isolamento lógico por `company_id`, chaves LLM globais | ✅ Implementado |
| **Fase 2** | LLM Factory: cada empresa usa sua própria chave | Média (2-3 sprints) |
| **Fase 3** | Banco isolado por cliente (schema separado) | Alta (mídia enterprises) |
| **Fase 4** | Modelo fine-tuned por cliente (dados próprios) | Alta (roadmap longo) |

---

## 16. Checklist Final — Go-Live

> Lista consolidada de todos os itens deste documento. Use como board de acompanhamento antes do go-live.

### Código (Replit + time dev)

**Frontend:**
- [ ] Dockerfile Next.js criado com `output: standalone`
- [ ] `next build` sem erros
- [ ] WorkOS prod configurado (API key + redirect URIs)
- [ ] Headers de segurança em `next.config.js`
- [ ] Sentry DSN frontend
- [ ] Teams Tab URL atualizada para prod
- [ ] Teste E2E completo passando

**AI Agent:**
- [ ] `python3 -c "from app.main import app"` sem erros
- [ ] Migrations Alembic clean
- [ ] Todos os secrets movidos para Secret Manager
- [ ] Celery worker configurado como serviço separado
- [ ] Service Account para Google Speech/TTS
- [ ] Teams webhook URL atualizada para URL prod Cloud Run

### Infraestrutura (time infra)

**GCP:**
- [ ] Projeto GCP criado com billing ativo
- [ ] APIs habilitadas: Cloud Run, Cloud SQL, Cloud Memorystore, Speech, TTS, Secret Manager, Container Registry
- [ ] Cloud SQL PostgreSQL 16 provisionado
- [ ] Cloud Memorystore (Redis) provisionado
- [ ] RabbitMQ provisionado (CloudAMQP ou VM)
- [ ] Secret Manager populado (todos os secrets)
- [ ] Cloud Run: `lia-frontend` deployado
- [ ] Cloud Run: `lia-agent` deployado
- [ ] Cloud Run: `celery-worker` deployado (serviço adicional)
- [ ] Load Balancer configurado com SSL
- [ ] DNS: `wedotalent.cc` + `staging.wedotalent.cc` + APIs

**Staging:**
- [ ] Cloud Run staging deployado (frontend + agent)
- [ ] Banco staging separado do banco de produção
- [ ] GitHub Actions: develop → staging automático
- [ ] GitHub Actions: main → prod automático

### Integrações (time produto + infra)

- [ ] WorkOS: ambiente de produção criado e configurado
- [ ] Anthropic: `ANTHROPIC_API_KEY` no Secret Manager prod
- [ ] Google AI: `GEMINI_API_KEY` no Secret Manager prod
- [ ] Google Speech/TTS: APIs habilitadas no projeto GCP
- [ ] Twilio: credenciais prod no Secret Manager
- [ ] Microsoft Teams: webhook URL de prod registrado no Azure
- [ ] Resend: `RESEND_API_KEY` no Secret Manager
- [ ] Sentry: projetos criados (frontend + backend), DSNs configurados
- [ ] WhatsApp Meta: (se pronto) credenciais de prod

### Validação funcional (time completo)

- [ ] Login Google SSO (via WorkOS)
- [ ] Login Microsoft SSO (via WorkOS)
- [ ] Criação de vaga
- [ ] Upload de CV + triagem por Claude
- [ ] Triagem por voz (Twilio + Google STT)
- [ ] Chat com LIA no funil
- [ ] Bot Teams respondendo em prod
- [ ] Mover candidato no kanban
- [ ] Geração de relatório
- [ ] Notificação por email (Resend)
- [ ] Notificação por WhatsApp (se ativo)
- [ ] LGPD: solicitação de exclusão de dados (endpoint admin)
- [ ] Multi-tenant: criar 2 empresas separadas, confirmar isolamento de dados

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
*Integrações mapeadas: Claude, Gemini, OpenAI, WorkOS, Twilio Voice, Google STT/TTS, Teams, WhatsApp, Resend, HubSpot, PEARCH, Redis, RabbitMQ, Celery, Sentry, LangSmith*
