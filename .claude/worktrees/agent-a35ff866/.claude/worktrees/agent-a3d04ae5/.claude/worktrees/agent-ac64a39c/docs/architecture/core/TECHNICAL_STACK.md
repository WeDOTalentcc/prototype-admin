# 📘 Plataforma LIA - Documentação Técnica Completa
**Versão:** 2.0 | **Data:** Novembro 2025 | **Time:** WedoTalent Engineering

---

## 📋 **Índice**
1. [Visão Geral](#visão-geral)
2. [Integrações Externas](#integrações-externas)
3. [Stack Tecnológica](#stack-tecnológica)
4. [Infraestrutura](#infraestrutura)
5. [Arquitetura Multi-Agent](#arquitetura-multi-agent)
6. [Frameworks e Bibliotecas](#frameworks-e-bibliotecas)
7. [Análise de Migração Frontend](#análise-de-migração-frontend)

---

## 🎯 **Visão Geral**

**Plataforma LIA** (Learning Intelligence Assistant) é um sistema de recrutamento e seleção alimentado por IA que automatiza workflows end-to-end incluindo:
- Criação conversacional de vagas
- Busca inteligente de candidatos (2-tier: BD interno → Pearch AI global)
- Screening por voz (OpenMic.ai + Google Cloud TTS/STT)
- Agendamento de entrevistas (Microsoft Graph Calendar)
- Integrações ATS (Gupy + Pandapé)
- Dashboards KPI e analytics preditivos

**Arquitetura:** Dual-repository decoupled
- **Frontend:** `plataforma-lia/` (Next.js 15 + React + shadcn/ui)
- **Backend:** `lia-agent-system/` (FastAPI + Python + LangGraph)

---

## 🔌 **Integrações Externas**

### **1. Provedores de LLM (3)**
| Serviço | Versão | Uso Principal | Status |
|---------|--------|---------------|--------|
| **Anthropic Claude** | Sonnet 4.5 | LIA conversational agent, intent classification, entity extraction, job creation | ✅ Produção |
| **OpenAI GPT-4** | GPT-4 Turbo | Voice screening conversação em tempo real | ✅ Produção |
| **Google Gemini** | Flash 2.5 | Fallback para voice-to-text + conversação | ✅ Produção |

**Chaves necessárias:**
```bash
ANTHROPIC_API_KEY=sk-ant-***
OPENAI_API_KEY=sk-***
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_CLOUD_PROJECT=project-id
```

---

### **2. Candidate Search & Enrichment (1)**
| Serviço | Cobertura | Custo | Uso |
|---------|-----------|-------|-----|
| **Pearch AI** | 190M+ perfis globais | Créditos (2-5 por busca) | Tier 2 search quando BD interno insuficiente |

**API:**
```bash
PEARCH_API_KEY=***
PEARCH_API_URL=https://api.pearch.ai
```

**Políticas de uso:**
- Max 10 buscas/dia (configurável via Policy Engine)
- Max 5 créditos por busca (soft limit)
- Prioriza sempre BD PostgreSQL local primeiro

---

### **3. Voice Screening Stack (3 serviços)**
| Serviço | Função | Tecnologia |
|---------|--------|-----------|
| **OpenMic.ai** | Orquestração de calls + webhooks | Plataforma de voice AI |
| **Deepgram** | Speech-to-Text (STT) | Nova-2 model |
| **Google Cloud TTS** | Text-to-Speech | WaveNet voices |

**Workflow:**
1. OpenMic.ai inicia call → webhooks para backend LIA
2. Real-time: GPT-4 conversa com candidato
3. Post-call: Claude Sonnet 4.5 analisa transcrição completa
4. Resultados salvos em PostgreSQL (`voice_screening_calls` + `voice_screening_analyses`)

**Chaves:**
```bash
OPENMIC_API_KEY=***
OPENMIC_WEBHOOK_SECRET=***  # Signature verification
```

---

### **4. Microsoft Graph Integration (2 serviços)**
| Serviço | Função | OAuth Flow |
|---------|--------|-----------|
| **Microsoft Graph API** | Calendar CRUD, availability checks | Client credentials (daemon app) |
| **Microsoft Teams Bot** | Bot Framework para Teams integration | 🟡 Planejado |

**Azure AD App:**
```bash
AZURE_TENANT_ID=***
AZURE_CLIENT_ID=***
AZURE_CLIENT_SECRET=***
MICROSOFT_APP_ID=***          # Teams bot (futuro)
MICROSOFT_APP_PASSWORD=***     # Teams bot (futuro)
```

**Permissões necessárias (Graph API):**
- `Calendars.ReadWrite`
- `User.Read`

---

### **5. ATS Integrations (2 plataformas brasileiras)**
| ATS | API | Status | Funcionalidade |
|-----|-----|--------|---------------|
| **Gupy** | REST API | ✅ Schema pronto | Sync bidirecional de candidatos + vagas |
| **Pandapé** | REST API | ✅ Schema pronto | Sync bidirecional de candidatos + vagas |

**Tabelas DB:**
- `ats_connections` - Credenciais por cliente
- `ats_sync_jobs` - Histórico de syncs
- `ats_candidates` - Mapping externo → interno
- `ats_webhook_logs` - Eventos recebidos

---

### **6. Communication Channels (1)**
| Serviço | Uso | Status |
|---------|-----|--------|
| **Twilio WhatsApp** | Outreach cadences, knockout questions | 🟡 Implementado (feature flag) |

```bash
TWILIO_ACCOUNT_SID=***
TWILIO_AUTH_TOKEN=***
TWILIO_WHATSAPP_NUMBER=+14155238886
```

---

### **7. Observability & Monitoring (6 ferramentas)**
| Ferramenta | Propósito | Status |
|-----------|----------|--------|
| **LangSmith** | LLM/agent trace debugging, latency tracking | ✅ Configurado |
| **Prometheus** | Custom metrics (throughput, errors) | 🟡 Planejado |
| **Grafana** | Dashboards de métricas | 🟡 Planejado |
| **Sentry** | Error tracking (frontend + backend) | 🟡 Planejado |
| **SonarCloud** | Code quality gates | 🟡 Planejado |
| **Snyk** | Dependency vulnerability scanning | 🟡 Planejado |

**LangSmith config:**
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_***
LANGCHAIN_PROJECT=lia-agent-system
LANGSMITH_WORKSPACE_ID=***  # Para org-scoped keys
```

---

## 🛠️ **Stack Tecnológica**

### **Frontend (`plataforma-lia/`)**

#### **Core Framework**
```json
{
  "next": "15.3.2",           // React meta-framework
  "react": "18.3.1",          // UI library
  "typescript": "5.8.3",      // Type safety
  "tailwindcss": "3.4.17"     // Utility-first CSS
}
```

**Features habilitadas:**
- ✅ App Router (Next.js 13+)
- ✅ Server Components (RSC)
- ✅ Static export (`output: 'export'`)
- ✅ Image optimization disabled (static export)

---

#### **UI Component Library**
**shadcn/ui** (copy-paste components, não npm package)
- Baseado em **Radix UI primitives** (acessibilidade WAI-ARIA)
- Componentes copiados para `src/components/ui/`
- Customizável via Tailwind + CVA (Class Variance Authority)

**Componentes principais:**
```typescript
// Radix UI dependencies
"@radix-ui/react-avatar": "1.1.10",
"@radix-ui/react-dialog": "1.1.15",
"@radix-ui/react-dropdown-menu": "2.1.16",
"@radix-ui/react-select": "2.2.6",
"@radix-ui/react-tabs": "1.1.13",
"@radix-ui/react-toast": "1.2.15",
"@radix-ui/react-tooltip": "1.2.8"
```

---

#### **Charting Libraries**
```json
{
  "chart.js": "4.5.0",                    // Canvas-based charts
  "react-chartjs-2": "5.3.0",             // React wrapper
  "recharts": "3.2.1",                    // Declarative charts (SVG)
  "chartjs-adapter-date-fns": "3.0.0"     // Time-series support
}
```

**Uso:**
- Chart.js → Line/bar charts em dashboards KPI
- Recharts → Tooltips customizados, composições complexas

---

#### **Animation & Motion**
```json
{
  "framer-motion": "12.23.22"  // Declarative animations (ChatGPT-like transitions)
}
```

---

#### **Export & PDF Generation**
```json
{
  "html2canvas": "1.4.1",  // Screenshot de DOM → canvas
  "jspdf": "3.0.3"         // PDF generation client-side
}
```

**Uso:** Exportar dashboards KPI, relatórios de candidatos

---

#### **Utilities**
```json
{
  "clsx": "2.1.1",                          // Conditional classNames
  "tailwind-merge": "3.3.0",                // Merge Tailwind classes
  "class-variance-authority": "0.7.1",      // Type-safe variants (shadcn/ui)
  "date-fns": "4.1.0",                      // Date manipulation
  "lucide-react": "0.475.0",                // Icon library (24k+ icons)
  "next-themes": "0.4.6"                    // Dark mode system
}
```

---

### **Backend (`lia-agent-system/`)**

#### **Core Framework**
```python
fastapi==0.115.5          # Async web framework (ASGI)
uvicorn[standard]==0.32.1 # ASGI server (production-ready)
python-multipart==0.0.19  # Form/file uploads
websockets==13.1          # Real-time WebSocket support
```

**Versão Python:** 3.11 (Type hints avançados, performance)

---

#### **Database Stack**
```python
# ORM & Migrations
sqlalchemy==2.0.36        # Async ORM
alembic==1.14.0           # Schema migrations
psycopg2-binary==2.9.10   # PostgreSQL adapter (sync)
asyncpg==0.30.0           # PostgreSQL adapter (async)

# Vector Search
pgvector==0.3.6           # PostgreSQL extension (embeddings)
```

**Database:** PostgreSQL 15+ (Replit-managed Neon instance)

---

#### **LangChain & LangGraph Stack**
```python
# Framework
langchain==0.3.9                # LLM orchestration
langgraph==0.2.53               # State machines para agents
langsmith==0.2.5                # Tracing & debugging

# LLM Providers
langchain-anthropic==0.3.22     # Claude integration
langchain-openai==0.2.9         # OpenAI integration
langchain-google-vertexai==2.0.8 # Gemini integration
```

**Capabilities:**
- ✅ Conversational state management (TypedDict)
- ✅ Conditional routing (intent classification)
- ✅ Multi-step workflows (job creation, interview scheduling)
- ✅ Memory/context summarization

---

#### **Async & Queue**
```python
celery==5.4.0       # Distributed task queue (heavy jobs)
redis==5.2.0        # Message broker + cache
aio-pika==9.5.3     # RabbitMQ client (async)
```

**Uso:**
- Celery → ATS syncs, bulk email sends
- Redis → Session cache, rate limiting
- RabbitMQ → Event-driven architecture (webhooks)

---

#### **Data Validation**
```python
pydantic==2.10.3           # Runtime validation + serialization
pydantic-settings==2.6.1   # .env config management
```

**Pydantic Schemas:**
- `JobVacancyState` - Job creation workflow
- `InterviewSchedulingState` - Interview scheduling
- `CandidateSearchRequest` - Search filters
- `VoiceScreeningAnalysis` - Call analysis results

---

#### **HTTP Clients**
```python
httpx==0.28.1      # Async HTTP (Pearch, OpenMic, etc.)
aiohttp==3.11.10   # Alternative async client (Graph API)
```

---

#### **Microsoft Integration**
```python
msal==1.31.0                   # Microsoft Authentication Library
msgraph-sdk==1.12.0            # Graph API SDK
botbuilder-core==4.17.0        # Bot Framework (Teams)
botbuilder-schema==4.17.0      # Bot schemas
pyjwt[crypto]==2.10.1          # JWT handling
cryptography==44.0.0           # Encryption utilities
```

---

#### **Communication**
```python
twilio==9.4.0  # WhatsApp API
```

---

#### **Utilities**
```python
python-dotenv==1.0.1           # .env file loading
python-jose[cryptography]==3.3.0 # JWT encoding/decoding
passlib[bcrypt]==1.7.4         # Password hashing
python-dateutil==2.9.0         # Date parsing
email-validator==2.2.0         # Email validation
```

---

#### **Monitoring**
```python
prometheus-client==0.21.0  # Metrics export (/metrics endpoint)
```

---

## 🏗️ **Infraestrutura**

### **Hosting & Deployment**
| Componente | Tecnologia | URL | Status |
|-----------|-----------|-----|--------|
| **Dev Environment** | Replit | `.replit.dev` | ✅ Ativo |
| **Frontend** | Next.js (port 5000) | `http://0.0.0.0:5000` | ✅ Running |
| **Backend API** | FastAPI (port 8000) | `http://0.0.0.0:8000` | ✅ Running |
| **Database** | PostgreSQL (Neon) | Managed by Replit | ✅ Ativo |

---

### **Database Schema (27 tabelas)**

#### **Core Tables**
```sql
-- Conversações LIA
conversations              -- Chat sessions
messages                   -- Message history
conversation_summaries     -- Context summaries

-- Candidatos
candidates                 -- Candidate profiles
candidate_searches         -- Search history + filters
credits_usage              -- Pearch AI usage tracking

-- Vagas
job_vacancies             -- Job postings
job_vacancy_interview_stages -- Interview flow config
job_vacancy_templates     -- Reusable templates

-- Entrevistas
interviews                -- Scheduled interviews
interview_feedbacks       -- Post-interview notes
calendar_availability     -- Interviewer slots

-- Voice Screening
voice_screening_calls     -- OpenMic call metadata
voice_screening_analyses  -- Claude análise completa

-- Activity Feed
activity_feed             -- Timeline de eventos

-- ATS Integration
ats_connections           -- Credentials por cliente
ats_sync_jobs             -- Sync logs
ats_candidates            -- External ID mapping
ats_webhook_logs          -- Webhook events
ats_job_mappings          -- Vaga interna ↔ externa

-- Microsoft Teams (futuro)
teams_conversations
teams_messages
teams_notifications
```

**Indexes:**
- ✅ Foreign keys (candidate_id, job_id, etc.)
- ✅ Search fields (email, phone, skills - GIN/trigram)
- ✅ Temporal queries (created_at, updated_at)

**Vector Search:**
- ✅ `pgvector` extension instalada
- 🟡 Embeddings planejados (semantic search de JDs)

---

### **Workflows (2 ativos)**
```yaml
dev-server:
  command: "cd plataforma-lia && npm run dev"
  port: 5000
  output_type: webview

lia-backend:
  command: "cd lia-agent-system && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
  port: 8000
  output_type: console
```

---

### **Environment Variables (23)**
```bash
# Application
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://***

# LLMs
ANTHROPIC_API_KEY=***
OPENAI_API_KEY=***
GOOGLE_APPLICATION_CREDENTIALS=***

# External APIs
PEARCH_API_KEY=***
OPENMIC_API_KEY=***
AZURE_TENANT_ID=***
AZURE_CLIENT_ID=***
AZURE_CLIENT_SECRET=***

# Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=***
LANGSMITH_WORKSPACE_ID=***

# Security
SECRET_KEY=***
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5000"]
```

---

## 🤖 **Arquitetura Multi-Agent**

### **Design Decision: Multi-Agent > Super-Agent**

**Rationale (ADR-001):**
- ✅ **Specialization:** Cada agent domina 1 domínio (Job Intake, Sourcing, Screening, etc.)
- ✅ **Observability:** Traces isolados por agent (LangSmith)
- ✅ **Extensibility:** Adicionar novos agents sem refactoring monolith
- ❌ **Trade-off:** Overhead de orquestração < Debugging complexity monolítico

---

### **Orchestrator (Central Coordinator)**

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │Intent Router │  │Task Planner  │  │State Mgr  │  │
│  │(Claude 4.5)  │  │(Multi-step)  │  │(Postgres) │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
│  ┌──────────────┐                                    │
│  │Policy Engine │  (Credit limits, approvals)        │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Job Intake│   │Sourcing │   │Screening│
└─────────┘   └─────────┘   └─────────┘
    ▼               ▼               ▼
┌─────────┐   ┌──────────┐  ┌──────────┐
│Evaluation│  │Scheduling│  │Comms     │
└─────────┘   └──────────┘  └──────────┘
```

---

### **Orchestrator Components (4)**

#### **1. Intent Router**
**Modelo:** Claude Sonnet 4.5  
**Função:** Classificar intent do usuário (95%+ confiança)  
**Outputs:** `job_intake`, `candidate_search`, `interview_scheduling`, `communication`, etc.

**Exemplo:**
```python
"Criar vaga de Python sênior remoto" 
→ Intent: job_intake (confidence: 0.98)
→ Delegate to: Job Intake Agent
```

---

#### **2. Task Planner**
**Função:** Decompor requests complexos em multi-step plans

**Exemplo:**
```python
"Encontrar 5 candidatos React e agendar entrevistas"
→ Plan:
  1. [Sourcing Agent] Search candidates (React, limit=5)
  2. [Evaluation Agent] Score top 5 by technical fit
  3. [Screening Agent] Send WhatsApp knockout questions
  4. [Scheduling Agent] Schedule interviews com aprovados
```

---

#### **3. Policy Engine**
**Função:** Enforce business rules

**Policies:**
```python
{
  "max_pearch_searches_per_day": 10,
  "max_voice_screenings_per_day": 20,
  "bulk_email_approval_threshold": 10,  # >10 emails = require approval
  "prefer_local_database": true
}
```

---

#### **4. State Manager**
**Storage:** PostgreSQL (`conversations` + `messages`)  
**MVP:** In-memory dict  
**Production:** Redis (distributed cache)

**Tracked State:**
- Conversation history (last 10 messages)
- Agent execution results
- Workflow metadata (current_step, collected_fields)

---

### **6 Specialized Agents**

#### **1️⃣ Job Intake Agent**
**Intent:** `job_intake`  
**Responsibilities:**
- Conversational job creation (10+ fields via LangGraph)
- JD structuring (Pydantic schemas)
- Approval workflows
- Template management

**Proto-agent:** `job_creation.py` (10 nodes)  
**Status:** ✅ Produção

**Workflow Nodes:**
```python
[state_loader] → [router] → [basics_collector] 
  → [remuneration_collector] → [technical_matrix_collector] 
  → [interview_flow_collector] → [screening_collector] 
  → [validator] → [frame_generator] → [response_planner]
```

---

#### **2️⃣ Sourcing Agent**
**Intent:** `candidate_search`  
**Responsibilities:**
- 2-tier search (PostgreSQL → Pearch AI)
- Profile enrichment
- Dossier generation (skills, experience, cultura fit)

**Proto-agent:** `candidate_search.py`  
**Status:** ✅ Produção

**Search Strategy:**
1. **Local DB** (PostgreSQL full-text search)
   - Filtros: skills, location, seniority, company experience
   - Se ≥ 5 resultados → retorna local
2. **Pearch AI** (se insuficiente)
   - Pergunta confirmação ao usuário (custo)
   - Track credits (`credits_usage` table)

---

#### **3️⃣ Screening Agent**
**Intent:** `candidate_screening`  
**Responsibilities:**
- Voice screening (OpenMic.ai + GPT-4 real-time + Claude post-analysis)
- WhatsApp knockout questions
- Automated triagem

**Status:** ✅ Produção (voice screening completo)

**Voice Screening Flow:**
```
OpenMic call initiated
  ↓
GPT-4 conversa em tempo real (30min)
  ↓
Deepgram STT → transcript JSON
  ↓
Claude Sonnet 4.5 análise profunda
  ↓
Results → PostgreSQL (voice_screening_analyses)
  ↓
Dashboard disponível no frontend
```

---

#### **4️⃣ Evaluation Agent**
**Intent:** `candidate_evaluation`  
**Responsibilities:**
- Technical/behavioral scoring
- Big Five personality tests
- Comparative analysis (rank candidatos)

**Status:** 🟡 Planejado

---

#### **5️⃣ Scheduling Agent**
**Intent:** `interview_scheduling`  
**Responsibilities:**
- Microsoft Graph Calendar integration
- Availability checks
- Reschedule/cancel logic

**Proto-agent:** `scheduling` workflow (6 nodes)  
**Status:** ✅ Produção

**Features:**
- Natural language ("agendar entrevista com João para quinta às 14h")
- AI-generated email templates
- Integration com candidate cards

---

#### **6️⃣ Communication Agent**
**Intent:** `communication`  
**Responsibilities:**
- Omnichannel cadences (WhatsApp, email)
- Follow-ups automáticos
- Notification system

**Status:** 🟡 Planejado

---

### **Shared Services (2)**

#### **ATS Sync Service**
**Platforms:** Gupy + Pandapé  
**Direction:** Bidirectional  
**Sync Strategy:** Webhooks (real-time) + Cron (daily full sync)

**Schema:**
- `ats_connections` - OAuth credentials
- `ats_sync_jobs` - Last sync timestamps
- `ats_candidates` - External ↔ Internal ID mapping

---

#### **Analytics Service**
**Dashboards:** 7 strategic categories (Indicadores section)  
**Technologies:** Chart.js + Recharts  
**Metrics:**
- Pipeline health (conversion rates)
- Time-to-hire
- Source effectiveness
- Candidate quality scores

---

## 📚 **Frameworks e Bibliotecas**

### **Frontend (Total: 21 dependencies)**
```
Core Framework:
- next 15.3.2
- react 18.3.1
- typescript 5.8.3

UI Components:
- @radix-ui/* (8 packages)
- lucide-react 0.475.0 (icons)
- framer-motion 12.23.22

Styling:
- tailwindcss 3.4.17
- tailwind-merge 3.3.0
- clsx 2.1.1

Charts:
- chart.js 4.5.0
- react-chartjs-2 5.3.0
- recharts 3.2.1

Utilities:
- date-fns 4.1.0
- html2canvas 1.4.1
- jspdf 3.0.3
```

---

### **Backend (Total: 29 dependencies)**
```
Web Framework:
- fastapi 0.115.5
- uvicorn[standard] 0.32.1

Database:
- sqlalchemy 2.0.36
- alembic 1.14.0
- asyncpg 0.30.0
- pgvector 0.3.6

LangChain Stack:
- langchain 0.3.9
- langgraph 0.2.53
- langchain-anthropic 0.3.22
- langchain-openai 0.2.9
- langchain-google-vertexai 2.0.8
- langsmith 0.2.5

Queue & Cache:
- celery 5.4.0
- redis 5.2.0
- aio-pika 9.5.3

Microsoft:
- msal 1.31.0
- msgraph-sdk 1.12.0
- botbuilder-core 4.17.0

Utilities:
- pydantic 2.10.3
- httpx 0.28.1
- python-jose[cryptography] 3.3.0
- twilio 9.4.0
- prometheus-client 0.21.0
```

---

## 🔄 **Análise de Migração Frontend**

### **Cenário 1: Migração Completa para Vue.js + Nuxt**

#### **Stack Proposta:**
```
Framework: Nuxt 3/4 (Vue 3 Composition API)
UI: shadcn-vue (port oficial do shadcn/ui)
Styling: Tailwind CSS v3/v4
Charts: ECharts ou Chart.js (compatível)
TypeScript: Mantido
```

---

#### **✅ Vantagens:**
1. **Bundle Size:** Nuxt 3 produz bundles ~30% menores que Next.js (Nitro engine)
2. **DX (Developer Experience):**
   - Sintaxe Vue 3 mais limpa (SFCs vs JSX)
   - Auto-imports de composables/components
   - Menor boilerplate
3. **SSR Performance:** Nitro engine (~2ms cold start em Cloudflare Workers)
4. **Ecosystem:** shadcn-vue é port 1:1 (mesma DX, componentes idênticos)
5. **Convention-over-Configuration:** Nuxt é mais opinionado (menos decisões)

---

#### **❌ Desvantagens:**
1. **Esforço de Migração:**
   - ~**50-60% do código precisa ser reescrito**
   - Conversão de 30+ componentes React → Vue SFCs
   - Hooks → Composables (useEffect → watchEffect, useState → ref)
   - Routing Next.js → Nuxt (similar mas não idêntico)
2. **Time de Learning Curve:**
   - Se time só conhece React: **2-4 semanas** de ramp-up
   - Vue 3 Composition API é diferente de Options API
3. **Ecosystem React:**
   - Perda de React-specific libraries (ex: react-hook-form, React Three Fiber)
   - shadcn-vue tem menos community plugins que shadcn/ui React
4. **Custo-Benefício:**
   - Para projeto com 6-12 meses de vida: **não vale a pena**
   - ROI positivo apenas em projetos long-term (2+ anos)

---

#### **Esforço Estimado (Migração Completa):**
| Fase | Tarefa | Effort | Duração |
|------|--------|--------|---------|
| 1 | Setup Nuxt + shadcn-vue | Baixo | 2 dias |
| 2 | Migrar utilities (TypeScript puro) | Baixo | 3 dias |
| 3 | Converter 30+ componentes React → Vue | **Alto** | 3 semanas |
| 4 | Hooks → Composables | Médio | 1.5 semanas |
| 5 | Routing (pages/) | Médio | 1 semana |
| 6 | State (Zustand → Pinia) | Médio | 1 semana |
| 7 | API routes Next.js → Nuxt server | Baixo | 3 dias |
| 8 | shadcn/ui → shadcn-vue swap | Médio | 1 semana |
| **TOTAL** | | | **~8-10 semanas** (1 dev) |

---

### **Cenário 2: Preservar Next.js + React**

#### **✅ Vantagens:**
1. **Zero Migration Cost:** Time continua produtivo 100%
2. **Ecosystem Maduro:**
   - shadcn/ui tem mais components/plugins que shadcn-vue
   - Milhares de tutoriais, StackOverflow threads
3. **Vercel Optimization:** Next.js é otimizado para Vercel (deploy 1-click)
4. **Team Expertise:** Se time já domina React, productivity máxima
5. **React Server Components:**
   - Next.js 13+ RSC são bleeding-edge (Nuxt ainda catching up)
   - Melhor SEO out-of-the-box

---

#### **❌ Desvantagens:**
1. **Bundle Size:** ~30% maior que Nuxt (mas aceitável para maioria dos casos)
2. **Boilerplate:** React requer mais código que Vue (ex: event handlers, state)
3. **Vendor Lock-in:** Next.js + Vercel são acoplados (migrar para outro host = effort)

---

### **Cenário 3: Ruby on Rails Backend + Vue.js Nuxt Frontend**

#### **Arquitetura Proposta:**
```
Backend:  Ruby on Rails 8 API mode (port 3000/8080)
Frontend: Nuxt 3 (port 3001)
Auth:     Devise-JWT (tokens em headers)
Deploy:   Heroku/Railway (2 apps separados)
```

---

#### **✅ Vantagens:**
1. **Separation of Concerns:** Frontend/backend completamente decoupled
2. **Independent Scaling:** Scale Rails API ≠ Scale Nuxt (Heroku dynos separados)
3. **Ruby Ecosystem:** ActiveRecord, Devise, Sidekiq (mature)
4. **Nuxt SSR:** Frontend pode fazer SSR mesmo com Rails API backend

---

#### **❌ Desvantagens:**
1. **Esforço Duplicado:**
   - Migrar Next.js → Nuxt (frontend)
   - Migrar FastAPI → Rails (backend)
   - **Esforço total: 4-6 meses** (team de 2-3 devs)
2. **Loss of LangGraph:**
   - Rails não tem equivalente nativo de LangGraph
   - Precisaria reescrever workflows de agents em Ruby (Langchain.rb existe mas é menos maduro)
3. **Python ML Ecosystem:**
   - Python tem melhor suporte para LLMs (OpenAI SDK, LangChain, etc.)
   - Ruby ML ecosystem é menor

---

### **Cenário 4: Preservar FastAPI (Backend) + Migrar para Nuxt (Frontend)**

#### **Arquitetura Híbrida:**
```
Backend:  FastAPI + Python + LangGraph (mantido)
Frontend: Nuxt 3 (migrado de Next.js)
```

---

#### **✅ Vantagens:**
1. **Preserva LangGraph:** Multi-agent architecture permanece intacta
2. **Python ML Stack:** Mantém OpenAI SDK, LangChain, LangSmith
3. **Frontend Modernization:** Ganha benefícios de Nuxt sem reescrever backend

---

#### **❌ Desvantagens:**
1. **Ainda Requer Migração Frontend:** 8-10 semanas de esforço (cenário 1)
2. **Dual Skillset:** Time precisa dominar Python + Vue (vs Python + React atual)

---

### **🎯 Recomendação Final**

#### **Cenário Recomendado: Preservar Next.js + FastAPI**

**Rationale:**
1. ✅ **Zero migration cost** (time 100% produtivo em features)
2. ✅ **Stack madura:** Next.js 15 + FastAPI + LangGraph são production-ready
3. ✅ **Ecosystem:** React + Python LLM stack têm melhor suporte que Vue + Python
4. ✅ **ROI:** Migração só faz sentido se:
   - Projeto for long-term (2+ anos)
   - Time já domina Vue (ramp-up = 0)
   - Bundle size é critical bottleneck (atualmente não é)

---

#### **Alternativa (Se Migração for Mandatória):**

**Cenário 4 (FastAPI + Nuxt)** é o melhor compromisso:
- ✅ Preserva multi-agent architecture (LangGraph)
- ✅ Moderniza frontend (Nuxt)
- ❌ Mas ainda requer 8-10 semanas de migração

**Pré-requisitos:**
- Time disponível para 2 meses de migration
- Budget para parar features nesse período
- Vue expertise no time (ou budget para training)

---

## 📊 **Comparação Rápida**

| Critério | Next.js + FastAPI (Atual) | Nuxt + FastAPI | Rails + Nuxt |
|----------|---------------------------|----------------|--------------|
| **Migration Effort** | 0 semanas | 8-10 semanas | 16-24 semanas |
| **Bundle Size** | Baseline | -30% | -30% |
| **LLM Ecosystem** | ✅ Python (melhor) | ✅ Python | ❌ Ruby (menor) |
| **Team Learning Curve** | 0 | 2-4 semanas (Vue) | 6-8 semanas (Ruby+Vue) |
| **Long-term Maintenance** | Alta | Média | Média |
| **Vendor Lock-in** | Vercel (Next.js) | Neutro | Neutro |
| **Production Readiness** | ✅ Agora | 🟡 Q1 2026 | 🔴 Q2-Q3 2026 |

---

## 📁 **Estrutura de Diretórios**

### **Frontend (`plataforma-lia/`)**
```
plataforma-lia/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── api/                  # API routes (backend proxy)
│   │   ├── chat/                 # LIA chat page
│   │   ├── jobs/[id]/            # Job detail pages
│   │   └── admin/                # Admin dashboard
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components
│   │   ├── alerts/               # KPI alert system
│   │   └── charts/               # Chart.js wrappers
│   └── lib/
│       └── utils.ts              # Shared utilities
├── public/
│   └── images/                   # Static assets
├── package.json
├── tailwind.config.ts
└── next.config.js
```

---

### **Backend (`lia-agent-system/`)**
```
lia-agent-system/
├── app/
│   ├── agents/                   # LangGraph workflows
│   │   ├── conversation.py       # Main agent (1249 linhas)
│   │   ├── job_vacancy_nodes.py  # Job creation nodes
│   │   └── interview_scheduling_nodes.py
│   ├── orchestrator/             # Multi-agent orchestrator
│   │   ├── orchestrator.py
│   │   ├── intent_router.py
│   │   ├── task_planner.py
│   │   └── policy_engine.py
│   ├── api/                      # FastAPI routes
│   │   └── v1/
│   │       ├── chat.py
│   │       ├── candidates.py
│   │       ├── jobs.py
│   │       └── calendar.py
│   ├── services/                 # Business logic
│   │   ├── llm.py                # LLM clients (Claude, GPT, Gemini)
│   │   ├── pearch_service.py
│   │   ├── openmic_service.py
│   │   └── graph_client.py       # Microsoft Graph
│   ├── models/                   # SQLAlchemy models (27 tables)
│   ├── schemas/                  # Pydantic schemas
│   └── core/
│       ├── config.py             # Environment config
│       └── database.py           # DB connection
├── docs/
│   ├── agents/                   # Agent contracts
│   └── adr/                      # Architecture decision records
├── requirements.txt
└── main.py                       # App entrypoint
```

---

## 🚀 **Deployment**

### **Development**
```bash
# Terminal 1: Frontend
cd plataforma-lia
npm run dev  # http://localhost:5000

# Terminal 2: Backend
cd lia-agent-system
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### **Production (Replit)**
```yaml
Workflows:
  dev-server:    # Frontend (Next.js)
    port: 5000
    output: webview

  lia-backend:   # Backend (FastAPI)
    port: 8000
    output: console

Database: PostgreSQL (Neon-managed)
Secrets: 23 environment variables (Replit Secrets)
```

---

## 📖 **Referências**

### **Documentação Oficial**
- Next.js: https://nextjs.org/docs
- Nuxt: https://nuxt.com/docs
- FastAPI: https://fastapi.tiangolo.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- shadcn/ui: https://ui.shadcn.com
- shadcn-vue: https://www.shadcn-vue.com

### **Integrações**
- Pearch AI: https://pearch.ai/docs
- OpenMic.ai: https://openmic.ai/docs
- Microsoft Graph: https://learn.microsoft.com/graph
- LangSmith: https://docs.smith.langchain.com

### **ADRs (Architecture Decision Records)**
- `/docs/adr/ADR-001-multi-agent-architecture.md`
- `/docs/adr/ADR-002-observability-stack.md`

---

**Última Atualização:** Novembro 24, 2025  
**Versão:** 2.0  
**Autor:** WedoTalent Engineering Team
