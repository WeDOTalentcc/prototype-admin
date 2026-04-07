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
│  Ambiente:   Servidor próprio / VPS + Staging já existe         │
│  Deploy:     A confirmar com o time (manual ou CI/CD parcial)  │
│  Domínio:    wedotalent.cc                                      │
└──────────────────────────────────────────────────────────────────┘
```

**Limitações do stack legado:**
- Frontend Vue/Nuxt sem sistema de design padronizado
- Agente Python com LangGraph implementado, porém aquém das capacidades esperadas — cobertura de domínios e robustez limitadas em relação à nova LIA
- Deploy: status a confirmar com o time — possivelmente manual ou com CI/CD parcial
- Ambiente de staging já existe (criado pelo time) — nível de integração e automação a verificar
- Observabilidade: status a levantar com o time — logs centralizados, traces e alertas podem ou não estar configurados

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

### Visão completa — ciclo contínuo do produto

O produto opera em três ciclos simultâneos que se alimentam:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CICLO COMPLETO DO PRODUTO — DESENVOLVIMENTO → OPERAÇÃO          │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 1 — NOVAS FEATURES                            │   │
│  │                                                                        │   │
│  │  Spec / demanda                                                        │   │
│  │  (PM ou time) ──► Desenvolvimento ──► PR + Review ──► Staging         │   │
│  │                                                             │          │   │
│  │                                              QA aprova?    │          │   │
│  │                                                 Sim ────► Produção   │   │
│  │                                                 Não ────► Fix + retry│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 2 — BUGS E CORREÇÕES                          │   │
│  │                                                                        │   │
│  │  Bug encontrado ──► Triage ──► hotfix/* branch ──► Staging            │   │
│  │  (QA, time ou       (Jira)       ou fix/* branch       │              │   │
│  │   cliente)                                        QA valida?          │   │
│  │                                                        │              │   │
│  │                                              Sim ────► Produção       │   │
│  │                                              Não ────► Fix + retry   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   CICLO 3 — FEEDBACK DO CLIENTE                       │   │
│  │                                                                        │   │
│  │  Cliente reporta bug ──────────────────────► Ciclo 2 (correção)      │   │
│  │  ou faz sugestão                                                       │   │
│  │       │                                                                │   │
│  │  PM/time faz triage                                                    │   │
│  │       │                                                                │   │
│  │       ├── Bug confirmado ─────────────────► Ciclo 2                  │   │
│  │       ├── Feature aprovada ───────────────► Ciclo 1 (nova feature)   │   │
│  │       └── Fora do escopo / backlog ───────► Documentado no Jira      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ciclo 1 — Novas features: do código à produção

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUXO: NOVA FEATURE → PRODUÇÃO                        │
│                                                                          │
│  1. DESENVOLVIMENTO  (responsabilidade do time de engenharia)            │
│  ───────────────────────────────────────────────────────────            │
│                                                                          │
│   Time de engenharia (ambiente central — todos os devs)                 │
│   ┌──────────────────────────────────────────────────────────┐         │
│   │  Replit  ──── ou ────  VS Code / Cursor / qualquer IDE   │         │
│   │  (mesmo repositório GitHub, mesmas branches, mesmo fluxo)│         │
│   │  plataforma-lia/ · lia-agent-system/ · Porta 5000 + 8001 │         │
│   └──────────────────────────┬───────────────────────────────┘         │
│                               │                                          │
│   + Você (PM/produto)         │  contribui com features e protótipos    │
│     no mesmo fluxo ───────────┘  sem ser responsável pelo processo      │
│                                                                          │
│              │ git push → branch feature/*                              │
│              ▼                                                           │
│                                                                          │
│  2. PULL REQUEST                                                         │
│  ───────────────                                                         │
│                                                                          │
│   feature/* ──────────────► develop                                     │
│                                PR review pelo time                       │
│                                Testes automáticos (GitHub Actions)      │
│                                                                          │
│  3. STAGING + QA                                                         │
│  ────────────────                                                        │
│                                                                          │
│   develop branch → deploy automático → STAGING GCP                      │
│   ┌───────────────────────────────────────────────────────┐             │
│   │  staging.wedotalent.cc                                │             │
│   │  QA manual pelo time (checklist por feature)          │             │
│   │  Demo para cliente quando aplicável                  │             │
│   └───────────────────────────────────────────────────────┘             │
│              │                                                           │
│        QA aprovou?                                                       │
│        ├── Sim → PR: develop → main                                     │
│        └── Não → fix na branch → re-teste no staging                   │
│              │                                                           │
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
                  ▲               ▲
develop       ────┴───────────────┤   STAGING
                  ▲               │
feature/*     ────┘               │   branches de feature (PR → develop)
                                  │
hotfix/*      ────────────────────┘   correções urgentes (PR → main direto)
                                      depois sincroniza: main → develop
```

| Branch | Ambiente | Deploy | Banco | Uso |
|---|---|---|---|---|
| `feature/*` | Replit / local | Manual (dev) | Postgres local | Novas features e melhorias |
| `fix/*` | Replit / local | Manual (dev) | Postgres local | Correções não urgentes (P3/P4) |
| `develop` | Staging GCP | Automático (push) | Cloud SQL staging | Integração contínua |
| `hotfix/*` | Local → Produção | PR → main | Cloud SQL prod | Bugs P1/P2 em produção |
| `main` | Produção GCP | Automático (push) | Cloud SQL produção | Código em produção |

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

> **O que fazer agora vs. o que fazer no momento do deploy:**
>
> | O que fazer **agora** (desenvolvimento em curso) | O que fazer **na hora do deploy** (esta seção) |
> |---|---|
> | Continuar desenvolvendo features no Replit | Criar o Dockerfile do Next.js (Fase 1.1 abaixo) |
> | Finalizar fluxos críticos e resolução de mockups | Configurar variáveis de produção no Secret Manager |
> | Integrar e testar com Rails API localmente | Push para GitHub + ativar GitHub Actions |
> | Validar fluxos no ambiente Replit | Provisionar GCP: Cloud Run, Cloud SQL, Redis |
> | Preparar specs e documentação | Configurar domínio `wedotalent.cc` e SSL |
> | Resolver pendências de UI listadas na Seção 12 | Rodar smoke tests no staging existente |
>
> As fases abaixo são o **manual de referência para o time de infra** no momento do go-live — não são ações urgentes para o desenvolvimento atual.

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

### 7.1 Rotina de desenvolvimento — nova feature ou melhoria

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
├── 7. QA no staging
│       Time executa checklist de QA para a feature
│       ├── Passou → PR: develop → main (aprovação manual)
│       └── Reprovou → dev abre fix na mesma branch ou nova fix/*
│               └── Volta para o passo 4 → re-teste no staging
│
└── 8. Deploy produção
        Merge para main → deploy automático produção
        wedotalent.cc recebe as mudanças
        Monitorar Sentry + logs nas primeiras horas
```

### 7.2 Fluxo de bug em produção — hotfix

Quando um bug crítico é encontrado em produção, o fluxo é diferente do fluxo padrão — bypassa o `develop` para chegar rápido à produção:

```
Bug identificado em produção
│
├── 1. Criar card no Jira com prioridade (P1/P2/P3)
│       P1 = produto fora do ar ou dado corrompido
│       P2 = funcionalidade crítica quebrada
│       P3 = problema menor, sem bloqueio
│
├── 2. Criar branch diretamente de main
│       git checkout main && git pull
│       git checkout -b hotfix/nome-do-bug
│
├── 3. Corrigir localmente e testar
│       Reproduzir o bug antes de corrigir
│       Confirmar que o fix resolve sem efeitos colaterais
│
├── 4. PR: hotfix/* → main  (revisão rápida, 1 aprovador)
│       GitHub Actions roda testes automáticos
│       Code review focado no fix (não no contexto geral)
│
├── 5. Deploy automático em produção
│       Merge para main → Cloud Run produção atualizado
│       Verificar no Sentry que o erro parou de aparecer
│
└── 6. Sincronizar com develop
        git checkout develop && git merge main
        Garante que a correção não será perdida na próxima feature
```

**Classificação de prioridade de bug:**

| Prioridade | Definição | Tempo alvo de resposta |
|---|---|---|
| **P1 — Crítico** | Sistema fora do ar, dados de clientes em risco, autenticação quebrada | Fix em produção em até 4h |
| **P2 — Alto** | Funcionalidade principal quebrada (triagem, kanban, chat) mas produto funciona | Fix em produção em até 24h |
| **P3 — Médio** | Problema visual, funcionalidade secundária ou edge case raro | Fix na próxima sprint |
| **P4 — Baixo** | Melhoria cosmética, mensagem de erro imprecisa | Backlog |

### 7.3 Processo de QA — o que é testado e como

O QA não é um passo único — é um processo por tipo de mudança:

**Para novas features:**

```
Checklist de QA por feature (quem faz: QA ou dev responsável)
│
├── Fluxo principal funciona conforme spec?
├── Casos de erro tratados? (campo vazio, API offline, usuário sem permissão)
├── Funciona em diferentes tamanhos de tela? (responsividade)
├── Multi-tenant: funciona isolado entre empresas diferentes?
├── Performance: não há regressão perceptível de velocidade?
├── Testes E2E automatizados passando? (Playwright em e2e/)
└── Sem warnings críticos no console do browser / Sentry?
```

**Para hotfixes:**

```
Checklist de QA de hotfix (mais rápido — foco no bug)
│
├── O bug original foi corrigido?
├── O fix não quebrou nada ao redor? (smoke test das funcionalidades adjacentes)
└── O Sentry para de registrar o erro após o deploy?
```

**Quem faz o QA:**
- Hoje: o próprio time de desenvolvimento (dev ou PM valida no staging)
- Roadmap: QA dedicado para releases maiores

**Onde bugs e ajustes são registrados:**
- Jira (cards de bug com prioridade, reprodução e critério de aceite do fix)
- PRs do GitHub linkados ao card Jira correspondente

### 7.4 Ciclo de feedback do cliente — bugs, sugestões e novas features

Clientes em uso do produto são uma fonte contínua de melhorias. Este fluxo descreve como esse feedback é capturado, triado e transformado em trabalho real.

**Canais de entrada de feedback:**

| Canal | Tipo de feedback | Quem recebe |
|---|---|---|
| **Email / WhatsApp direto** | Bugs críticos, dúvidas urgentes | CS / PM |
| **Formulário ou canal dedicado** | Sugestões, melhorias, relatos de comportamento inesperado | PM |
| **Slack compartilhado** (quando ativo) | Dúvidas rápidas, feedback informal | CS / PM |
| **Reunião de acompanhamento** | Feedback estruturado, roadmap, prioridades | PM |
| **Sentry / logs internos** | Bugs técnicos identificados antes do cliente (proativo) | Time de engenharia |

**Fluxo de triage — o que acontece com cada feedback:**

```
Feedback entra (qualquer canal)
         │
         ▼
PM ou CS registra no Jira com contexto:
  - O que o cliente reportou (comportamento observado)
  - O que era esperado acontecer
  - Frequência / impacto (quantos clientes afetados?)
  - Evidências (prints, vídeo, logs)
         │
         ▼
Triage de classificação:
  │
  ├── É um BUG?
  │       │
  │       ├── P1/P2 (crítico/alto) ──► Hotfix imediato (Fluxo 7.2)
  │       └── P3/P4 (médio/baixo) ──► Entra no backlog da próxima sprint
  │
  ├── É uma MELHORIA ou NOVA FEATURE?
  │       │
  │       ├── Alinhada com o roadmap → PM escreve spec → Ciclo 1 (feature)
  │       └── Fora do escopo atual → Documentada no Jira (backlog)
  │
  └── É uma DÚVIDA DE USO?
          └── CS resolve com documentação / suporte direto
              Se for recorrente → virar melhoria de UX ou documentação
```

**O que faz uma feature de cliente entrar no sprint:**

Não basta um cliente pedir — o PM avalia:
1. Quantos clientes teriam benefício (impacto)
2. Alinhamento com a direção do produto
3. Esforço de implementação vs. valor entregue
4. Urgência (está bloqueando o cliente de usar o produto?)

**Fechamento do loop com o cliente:**

Quando um bug reportado pelo cliente é corrigido, ou uma feature sugerida é entregue, o cliente deve ser notificado. Isso constrói confiança e mostra que o feedback foi levado a sério. Quem fecha esse loop: CS ou PM, após o deploy em produção.

### Como o Replit se encaixa após o deploy

```
┌─────────────────────────────────────────────────────────────────┐
│               Replit — Ambiente central do time                  │
│                                                                  │
│  DESENVOLVIMENTO (responsabilidade do time de engenharia)        │
│  ├── Ambiente padrão compartilhado pelo time                    │
│  ├── Alternativa: VS Code / Cursor apontando para GitHub        │
│  ├── Todos usam as mesmas branches, PRs e CI/CD                 │
│  └── Time é dono do fluxo: feature → develop → staging → prod  │
│                                                                  │
│  PROTÓTIPO E PRODUTO (você, PM)                                 │
│  ├── Contribui com features e novas telas no Replit             │
│  ├── Valida fluxos de UX antes de passar para o time            │
│  └── Participa do mesmo fluxo de PR sem ser responsável por ele │
│                                                                  │
│  DEBUGGING (qualquer membro do time)                            │
│  ├── Reproduzir bugs de produção localmente                     │
│  ├── Testar hotfixes antes de subir para staging                │
│  └── Explorar logs e traces em tempo real                       │
└─────────────────────────────────────────────────────────────────┘
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
| **Testes E2E** | Pasta `e2e/` com 20 arquivos Playwright — auth fixture via cookie bypass (dev mode) |

#### Resultados E2E (07/04/2026 — Replit, Chromium do sistema via Nix)

| Grupo | Passaram | Falharam | Notas |
|---|---|---|---|
| **Auth** (login.spec.ts) | 6/6 | 0 | Testa UI da página de login |
| **Kanban** (move-candidate.spec.ts) | 6/7 | 1 | Falha: `data-testid="kanban-column"` não existe na página |
| **Wizard steps 1-3** | 12/13 | 1 | Falha: texto esperado diferente do renderizado |
| **Wizard steps 4-7** | — | — | Timeout no Replit (45s/teste × muitos testes) |
| **Chat** (9 arquivos) | — | — | Pesados demais para Replit (precisam CI dedicado) |

**Pendência**: Rodar suíte completa com credenciais WorkOS reais em CI (GitHub Actions) para validação de produção.

### O que precisa de atenção antes do deploy

| Área | Problema | Ação |
|---|---|---|
| **Mockups pendentes** | Existem mockups de componentes criados no Replit (worktrees agent-a92b041a, agent-af767ad0) que ainda não foram revisados, aprovados ou integrados ao produto | Revisar todos os mockups abertos, aprovar ou descartar, e integrar os aprovados ao código antes do deploy |
| **Variáveis de ambiente** | `.env.example` documentado, `.env.local` tem 2 vars (restante vem de integrações Replit) | Em prod: mover tudo para Secret Manager |
| **WorkOS configuração prod** | `WORKOS_API_KEY` e `WORKOS_CLIENT_ID` apontam para dev | Criar ambiente de prod no WorkOS e configurar redirect URIs |
| **Error Boundaries** | Parcialmente implementado (`error-boundary.tsx`) | Verificar cobertura em pages críticas |
| **Hydration** | Possíveis mismatches em páginas com dados de sessão | Testar com `next build` e revisar warnings |
| **Bundle size** | Não auditado ainda | Rodar `next build` e checar `bundle-analyzer` |
| **Cache headers** | Não configurado | Configurar `Cache-Control` para assets estáticos via Cloud CDN |
| **CSP / Headers de segurança** | Não configurado em `next.config.js` | Adicionar `Content-Security-Policy`, `X-Frame-Options` |

### Checklist de production readiness — Frontend

- [ ] Todos os mockups pendentes revisados — aprovados integrados ao código, descartados removidos
- [x] `Dockerfile` com `output: standalone` criado (`plataforma-lia/Dockerfile`)
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

**Nível de isolamento atual:** Lógico — e isso significa o seguinte:

```
ISOLAMENTO LÓGICO (o que temos):
  Banco único. Todos os clientes compartilham o mesmo servidor PostgreSQL.
  Cada linha das tabelas tem um company_id que separa os dados.

  SELECT * FROM candidates WHERE company_id = 'empresa-a'
  → empresa-A nunca vê dados da empresa-B... desde que o filtro funcione.

  Risco: um bug de query que esqueça o filtro pode, em teoria, expor dados.
  Mitigação: testes de isolamento, revisão de código, middleware de auth.

ISOLAMENTO FÍSICO (não temos — para o futuro):
  Cada cliente teria seu próprio banco de dados separado.
  Impossível vazamento por bug de query.
  Custo: muito maior. Operação: muito mais complexa.
  Quando faz sentido: clientes enterprise, contratos com exigências
  regulatórias (bancos, saúde, governo).
```

**Conclusão:** para o mercado inicial (PME e midmarket), isolamento lógico é suficiente, correto e é o padrão adotado pela maioria dos SaaS B2B. Isolamento físico fica no roadmap para contratos enterprise futuros (Fase 3 abaixo).

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

**Pré-requisito crítico antes de liberar a factory: benchmarking de modelos**

Quando um cliente usa um LLM diferente do Claude (ex: GPT-4o, Gemini, Llama), o produto precisa garantir que a qualidade se mantém. Isso exige um processo de avaliação formal antes de liberar cada modelo:

| Dimensão | O que avaliar |
|---|---|
| **Assertividade** | O agente classifica intenções corretamente? Candidatos são rankeados com qualidade similar? |
| **Formato de output** | O modelo retorna JSON estruturado de forma confiável (sem alucinações de formato)? |
| **Compatibilidade de prompts** | Nossos prompts são Claude-específicos ou LLM-agnósticos? Precisam de adaptação? |
| **Latência** | O tempo de resposta é aceitável para o produto (metas: triagem <3s, chat <2s)? |
| **Custo por operação** | Triagem de 100 CVs custa quanto em cada modelo? Comparar com Claude como baseline. |
| **Janela de contexto** | O modelo suporta a quantidade de contexto que os agentes usam (8k–32k tokens)? |
| **Estabilidade** | O modelo produz respostas consistentes entre chamadas idênticas (baixa variância)? |

Esse processo se chama *model evaluation* (ou LLM benchmarking). Deve rodar contra um dataset curado de vagas e candidatos reais (anonimizados) antes de qualquer modelo ser liberado para produção. O time de AI é responsável por esse processo.

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

## 17. Fluxo de Desenvolvimento Assistido por IA (PM + Claude Code)

> Esta seção documenta o fluxo de trabalho onde o PM desenvolve features diretamente com auxílio de IA (Replit + Claude Code), e como esse código se integra ao processo do time de engenharia.

### O modelo de trabalho

O PM tem capacidade de criar features, corrigir bugs e evoluir o produto utilizando Replit como ambiente de desenvolvimento e Claude Code como assistente técnico. Para garantir qualidade e consistência, esse fluxo usa três pilares:

1. **Specs** — documentos de especificação técnica que descrevem o comportamento esperado antes de qualquer código ser escrito
2. **Skills** — instruções padronizadas que ensinam ao assistente de IA os padrões do projeto (Design System, arquitetura, convenções de código)
3. **Revisão do time** — todo código gerado que for para `develop` passa por code review de um dev antes do merge

### Fluxo de uma feature

```
PM identifica necessidade
         │
         ▼
Escreve spec (comportamento esperado, critérios de aceite)
         │
         ▼
Claude Code gera o código guiado pelos specs + skills
         │
         ▼
PM valida no Replit (funcionalidade, visual, fluxo)
         │
         ▼
PM abre PR → branch feature/* → develop
         │
         ▼
Dev do time faz code review
  - Verifica consistência com arquitetura
  - Identifica efeitos colaterais não visíveis no contexto local
  - Valida que padrões do projeto foram seguidos
         │
         ▼
Aprovado → merge → staging → produção
```

### Por que o code review ainda é necessário?

O código gerado por IA com bons specs é de qualidade consistente — mas o assistente não tem visibilidade do contexto completo do produto (outros módulos, banco de dados em produção, edge cases de uso real). O dev do time preenche essa lacuna:

- Detecta efeitos colaterais em outras partes do sistema
- Garante que a migration de banco está correta
- Valida performance em escala
- Mantém o time ciente de tudo que entra no produto

### Biblioteca de documentação técnica (TODO)

Existe um trabalho em andamento de consolidar uma **biblioteca de documentos técnicos padrão** — seguindo práticas de mercado — para uso não apenas do PM mas de todo o time, que trabalha cada vez mais com IA no desenvolvimento.

Esta biblioteca inclui (e não se limita a):

| Tipo de documento | Propósito |
|---|---|
| **Architecture Decision Records (ADR)** | Registra decisões arquiteturais com contexto e alternativas consideradas |
| **Technical Specs** | Descreve comportamento técnico esperado antes de implementar |
| **API Contracts** | Define contratos de interface entre serviços |
| **Runbooks** | Passo a passo para operações e incidentes em produção |
| **Onboarding técnico** | Guia de entrada para novos devs no projeto |
| **Skills de IA** | Instruções para o assistente seguir os padrões do projeto |
| **Playbooks de feature** | Checklist para implementar, testar e entregar uma feature |

> **Próximo passo:** o PM irá repassar a biblioteca completa destes documentos para ser adicionada como **Anexo** a este guia, servindo de referência consolidada para o time.

---

## 18. Status de Integrações — Microsoft Office 365 e Google Workspace

### Microsoft

| Integração | Status | Detalhes |
|---|---|---|
| **Microsoft Teams** | ✅ Pronto | Bot configurado (Azure Bot Service), Adaptive Cards, webhook de screening implementado. Pendente: propagação de credenciais no Azure (401 temporário) |
| **Microsoft SSO** | ✅ Pronto | Via WorkOS — login com conta Microsoft funcional |
| **Outlook (email)** | ✅ Parcial | Microsoft Graph API cobre leitura/envio de email via Outlook — a integração depende da autorização via Graph no tenant do cliente |
| **Calendário Outlook** | ✅ Parcial | Graph API suporta agendamento via Outlook Calendar — implementação similar ao Google Calendar já existente |
| **SharePoint / OneDrive** | ❌ Não integrado | Mencionados como conceito no código mas sem integração real de API |
| **Word / Excel** | ❌ Não integrado | Não há integração com documentos Office — não é parte do roadmap atual |

### Google

| Integração | Status | Detalhes |
|---|---|---|
| **Google SSO** | ✅ Pronto | Via WorkOS — login com conta Google funcional |
| **Google Calendar** | ✅ Pronto | `google-api-python-client` instalado, agendamento de entrevistas via Google Calendar implementado |
| **Google STT/TTS** | ✅ Pronto | Triagem de voz (WSI) usa Google Speech-to-Text e Text-to-Speech |
| **Gmail** | ❌ Não integrado | Email é enviado via Resend, não via Gmail API |
| **Google Drive / Docs / Sheets** | ❌ Não integrado | Sem integração com o Google Workspace de documentos |

### O que falta para Microsoft Office / Google Workspace completo?

A integração completa com documentos (Drive, Docs, SharePoint, OneDrive) não é parte do roadmap atual. Para clientes que precisam dessas integrações, o caminho é:
1. Definir caso de uso específico (ex: "exportar relatório para Google Sheets")
2. Criar card Jira com spec
3. O time implementa a integração pontual via API correspondente (Google Sheets API, OneDrive API)

---

## 19. Status de Integração — Slack

### O que existe hoje

O código referencia Slack em múltiplos pontos do sistema:

| Área | Arquivo | Função |
|---|---|---|
| **Hub de integrações** | `app/api/v1/integrations_hub.py` | Slack listado como canal de integração disponível |
| **Journey mapping** | `app/api/v1/journey_mapping.py` | Notificações de jornada via Slack |
| **Configuração de alertas** | `app/api/backend-proxy/alerts/config/route.ts` | Slack como destino de alertas configurável |
| **Presets de empresa** | `CompanyPresetsModal.tsx` | Interface para configurar integração Slack por empresa |

### Status

```
✅ Estrutura implementada: canais de alerta e notificação via Slack previstos na arquitetura
⚠️  Credenciais: requer Slack App configurada e OAuth token por tenant (não está em produção)
⚠️  Webhook de incoming: URL de webhook por workspace Slack precisa ser configurada por cliente
❌ Não validado em produção: integração não foi homologada end-to-end
```

### Para ativar o Slack em produção por cliente

1. Cliente cria um **Slack App** no workspace deles (ou usa o app WeDO se existir)
2. Gera o **Incoming Webhook URL** para o canal desejado
3. Configura na plataforma LIA via `CompanyPresetsModal` ou API de settings
4. Testa com notificação de candidato movido no pipeline

> Slack é uma integração leve (sem SDK pesado — apenas webhook POST) e pode ser ativada rapidamente para clientes que usam Slack como ferramenta principal.

---

## 20. Onboarding e Implementação no Cliente

> Roteiro de referência para implantação da LIA em um novo cliente. Cobre desde a configuração técnica até a homologação de canais.

### Visão geral do processo

```
FASE 1: Configuração da conta
  ↓ SSO + WorkOS
  ↓ Criação da organização (tenant)
  ↓ Usuários e permissões

FASE 2: Configuração dos canais
  ↓ Botão LIA (embed no site/ATS)
  ↓ WhatsApp Business (homologação Meta)
  ↓ Microsoft Teams (bot no tenant do cliente)
  ↓ Email (domínio verificado no Resend)
  ↓ Slack (opcional — webhook por workspace)

FASE 3: Integração com ATS do cliente (se houver)
  ↓ Webhook de eventos ou API REST
  ↓ Mapeamento de stages do funil

FASE 4: Configuração da LIA
  ↓ Persona e tom de voz
  ↓ Templates de mensagens
  ↓ Políticas de triagem (hiring policies)

FASE 5: Homologação e go-live
  ↓ Teste de ponta a ponta com vaga real
  ↓ Aprovação do cliente
  ↓ Ativação em produção
```

### Checklist de implantação — novo cliente

#### Fase 1: Conta e acesso

- [ ] Organização criada no WorkOS (`organizationId` gerado)
- [ ] SSO configurado (Google, Microsoft ou SAML do cliente)
- [ ] Usuários administradores criados e acessando a plataforma
- [ ] Permissões de papéis configuradas (admin, recrutador, gestor)

#### Fase 2: Canais de comunicação

**Botão LIA (embed)**
- [ ] Script do botão gerado para o site/ATS do cliente
- [ ] URL de destino configurada (landing page de candidatos)
- [ ] Teste: candidato clica no botão → inicia fluxo de triagem
- [ ] (Opcional) Integração com ATS via iframe ou redirect com parâmetros

**WhatsApp Business — Homologação Meta**
- [ ] Cliente possui conta no **Meta Business Suite** verificada
- [ ] **WhatsApp Business Account (WABA)** criado e aprovado pela Meta
- [ ] Número de telefone dedicado registrado no WABA
- [ ] **Número de telefone verificado** na API do WhatsApp Cloud
- [ ] `WHATSAPP_ACCESS_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID` configurados
- [ ] `WHATSAPP_VERIFY_TOKEN` configurado e webhook registrado no Meta dashboard
- [ ] URL do webhook apontando para `https://wedotalent.cc/api/v1/whatsapp/webhook`
- [ ] Teste de ponta a ponta: mensagem enviada → resposta da LIA recebida
- [ ] Templates de mensagem aprovados pela Meta (para mensagens ativas — fora da janela de 24h)

> **Atenção:** A homologação do WhatsApp com a Meta pode levar de 3 a 10 dias úteis dependendo da verificação do negócio. Iniciar este processo com antecedência.

**Microsoft Teams**
- [ ] Tenant Azure do cliente identificado (`AZURE_TENANT_ID`)
- [ ] Bot da LIA registrado no Azure Bot Service do cliente (ou WeDO com permissão)
- [ ] App do Teams instalado no workspace do cliente
- [ ] Canal de triagem configurado no Teams
- [ ] Teste: candidato recebe mensagem do bot → responde → LIA processa

**Email (Resend)**
- [ ] Domínio de email do cliente verificado no Resend (registros DNS: SPF, DKIM)
- [ ] Endereço de remetente configurado (ex: `lia@empresa-cliente.com.br`)
- [ ] Teste de envio: email de triagem enviado e recebido sem ir para spam

**Slack (opcional)**
- [ ] Slack App configurada no workspace do cliente
- [ ] Webhook URL do canal de notificações configurado na plataforma
- [ ] Teste: movimentação de candidato gera notificação no Slack

#### Fase 3: Integração com ATS do cliente (se aplicável)

- [ ] ATS do cliente identificado (Greenhouse, Lever, Workday, SAP, interno, etc.)
- [ ] Método de integração definido: webhook, API REST ou exportação manual
- [ ] Mapeamento de stages: estágios do ATS → estágios da LIA
- [ ] Teste de sincronização: candidato criado na LIA aparece no ATS
- [ ] Definir quem é o sistema de registro (source of truth): LIA ou ATS?

#### Fase 4: Configuração da LIA para o cliente

- [ ] Persona da LIA definida (nome, tom de voz, idioma)
- [ ] Templates de mensagem para cada canal aprovados pelo cliente
- [ ] **Hiring policies** configuradas (critérios de triagem automática)
- [ ] Vagas padrão criadas para testes
- [ ] Limite de triagens simultâneas configurado (controle de saturação)

#### Fase 5: Homologação e go-live

- [ ] Sessão de homologação com cliente — testar fluxo completo com vaga real
- [ ] Candidato de teste passa pelo funil completo (inscrição → triagem → retorno)
- [ ] Todos os canais ativos respondem corretamente
- [ ] Cliente aprova o comportamento da LIA (tom, qualidade das respostas)
- [ ] Monitoramento ativo nas primeiras 48h (Sentry, logs)
- [ ] Contato de suporte do cliente definido para escalonamento

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
