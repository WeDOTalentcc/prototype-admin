# Arquitetura Completa do Sistema LIA - Multi-Agent AI
**Data:** Novembro 2025  
**Versão:** 2.0 (Multi-Agent Architecture)

---

## 🏗️ Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER (Next.js 15.5)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │  Chat Interface│  │  Command       │  │ Context Pills  │                │
│  │  (Claude.ai UX)│  │  Palette (⌘K)  │  │ + Quick Actions│                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│         │                    │                    │                         │
│         └────────────────────┴────────────────────┘                         │
│                              │                                               │
│                              ▼                                               │
│                      REST API (FastAPI)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR LAYER (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Orchestrator Core                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │   Intent    │  │    Task     │  │   Policy    │  │   State    │ │   │
│  │  │   Router    │→ │   Planner   │→ │   Engine    │→ │  Manager   │ │   │
│  │  │ (Claude 4.5)│  │             │  │             │  │ (In-Memory)│ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                  │                                           │
│                 ┌────────────────┼────────────────┐                         │
│                 ▼                ▼                ▼                         │
└─────────────────────────────────────────────────────────────────────────────┘
                  │                │                │
                  ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (6 Specialized Agents)                      │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │ Job Intake   │  │  Sourcing    │  │  Screening   │                      │
│  │   Agent      │  │    Agent     │  │    Agent     │                      │
│  │              │  │              │  │              │                      │
│  │ • Create vaga│  │ • Local DB   │  │ • Voice call │                      │
│  │ • Update JD  │  │ • Pearch AI  │  │ • WhatsApp   │                      │
│  │ • Approvals  │  │ • Enrichment │  │ • Knockout Q │                      │
│  │              │  │ • 2-tier     │  │              │                      │
│  │ Proto-agent: │  │ Proto-agent: │  │ System:      │                      │
│  │job_creation.py│ │candidate     │  │Voice         │                      │
│  │              │  │_search.py    │  │screening     │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │ Evaluation   │  │ Scheduling   │  │Communication │                      │
│  │   Agent      │  │    Agent     │  │    Agent     │                      │
│  │              │  │              │  │              │                      │
│  │ • Tech score │  │ • MS Graph   │  │ • Email      │                      │
│  │ • Big Five   │  │ • Calendar   │  │ • WhatsApp   │                      │
│  │ • Comparative│  │ • Avail check│  │ • Follow-ups │                      │
│  │              │  │ • Reschedule │  │ • Cadences   │                      │
│  │ Status:      │  │ Proto-agent: │  │ Status:      │                      │
│  │ 🟡 Planned   │  │scheduling    │  │ 🟡 Planned   │                      │
│  │              │  │workflow      │  │              │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SHARED SERVICES LAYER                                 │
│                                                                              │
│  ┌──────────────────────────┐          ┌──────────────────────────┐         │
│  │   ATS Sync Service       │          │  Analytics Service       │         │
│  │                          │          │                          │         │
│  │  • Gupy Integration      │          │  • KPI Dashboards        │         │
│  │  • Pandapé Integration   │          │  • Predictive Insights   │         │
│  │  • Bidirectional Sync    │          │  • Reporting             │         │
│  │  • Schema Mapping        │          │  • Data Warehouse        │         │
│  │                          │          │                          │         │
│  │  Status: 🟢 Implemented  │          │  Status: 🟡 Planned      │         │
│  └──────────────────────────┘          └──────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE & CACHE LAYER                               │
│                                                                              │
│  ┌──────────────────────────┐          ┌──────────────────────────┐         │
│  │   PostgreSQL (Neon)      │          │   Redis Cache            │         │
│  │                          │          │                          │         │
│  │  • Conversations         │          │  • Search Results        │         │
│  │  • Job Vacancies         │          │  • Entity Extraction     │         │
│  │  • Candidates            │          │  • Session State         │         │
│  │  • Voice Screenings      │          │                          │         │
│  │  • Interviews            │          │  Status: 🟡 Planned      │         │
│  │  • ATS Integration Data  │          │  (Currently in-memory)   │         │
│  │                          │          │                          │         │
│  │  Status: 🟢 Implemented  │          │                          │         │
│  └──────────────────────────┘          └──────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATIONS LAYER                              │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Anthropic   │  │  Pearch AI   │  │  OpenMic.ai  │  │ Microsoft    │   │
│  │   Claude     │  │              │  │              │  │   Graph      │   │
│  │  Sonnet 4.5  │  │ Global       │  │ Voice        │  │              │   │
│  │              │  │ Candidate    │  │ Screening    │  │ Calendar API │   │
│  │ • Intent     │  │ Search       │  │ Platform     │  │              │   │
│  │ • Entity     │  │              │  │              │  │ • Schedule   │   │
│  │ • Response   │  │ • 2-tier     │  │ • Real-time  │  │ • Reschedule │   │
│  │ • Analysis   │  │ • Credits    │  │ • Post-call  │  │ • Availability│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Deepgram    │  │ Google Cloud │  │     Gupy     │  │   Pandapé    │   │
│  │              │  │     TTS      │  │     ATS      │  │     ATS      │   │
│  │ Speech-to-   │  │              │  │              │  │              │   │
│  │ Text (STT)   │  │ Voice        │  │ Brazilian    │  │ Brazilian    │   │
│  │              │  │ Synthesis    │  │ Recruiting   │  │ Recruiting   │   │
│  │              │  │              │  │ Platform     │  │ Platform     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY & MONITORING LAYER                        │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  LangSmith   │  │    Sentry    │  │  Prometheus  │  │  SonarCloud  │   │
│  │              │  │              │  │  + Grafana   │  │              │   │
│  │ LLM Traces   │  │ Error        │  │              │  │ Code Quality │   │
│  │ Agent Exec   │  │ Tracking     │  │ Metrics      │  │ Security     │   │
│  │              │  │ Session      │  │ Dashboards   │  │              │   │
│  │ Status:      │  │ Replay       │  │              │  │ Status:      │   │
│  │ 🟢 Active    │  │              │  │ Status:      │  │ 🟡 Planned   │   │
│  │              │  │ Status:      │  │ 🟡 Planned   │  │              │   │
│  │              │  │ 🟡 Planned   │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 LLM & AI Framework Stack

### Primary LLM
```
┌────────────────────────────────────────┐
│     Anthropic Claude Sonnet 4.5        │
│                                        │
│  Usage:                                │
│  ✓ Intent Classification (95%+ acc)   │
│  ✓ Entity Extraction                  │
│  ✓ Response Generation                │
│  ✓ Voice Screening Analysis           │
│  ✓ Chain-of-Thought Reasoning         │
│  ✓ Meta-Evaluation (quality scoring)  │
│                                        │
│  Frameworks:                           │
│  • LangChain (orchestration)          │
│  • LangGraph (workflow state machine) │
│  • LangSmith (observability)          │
└────────────────────────────────────────┘
```

### Fallback & Specialized Models
```
┌────────────────────────────────────────┐
│       Google Gemini Flash 2.5          │
│                                        │
│  Usage:                                │
│  ✓ Voice-to-Text Transcription        │
│  ✓ Fallback for voice screening       │
│  ✓ Cost optimization (cheaper)        │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│            GPT-4 (OpenAI)              │
│                                        │
│  Usage:                                │
│  ✓ Real-time voice conversation       │
│  ✓ OpenMic.ai integration              │
└────────────────────────────────────────┘
```

---

## 🔄 Proto-Agents → Specialized Agents (Migration Map)

### Current State (Proto-Agents)
```python
# lia-agent-system/app/agents/
├── conversation.py          # Main conversational agent (LangGraph workflow)
├── job_vacancy_nodes.py     # Job creation workflow nodes
└── interview_scheduling_nodes.py  # Interview scheduling nodes

# lia-agent-system/app/services/
├── pearch_service.py        # Candidate search (2-tier)
├── openmic_service.py       # Voice screening
├── calendar_service.py      # Microsoft Graph integration
├── gupy_service.py          # Gupy ATS sync
└── pandape_service.py       # Pandapé ATS sync
```

### Target State (Specialized Agents)
```
job_vacancy_nodes.py      →  Job Intake Agent (🟢 Absorbs workflow)
candidate_search logic    →  Sourcing Agent (🟢 2-tier search orchestration)
voice screening system    →  Screening Agent (🟢 Voice + WhatsApp)
[NEW]                     →  Evaluation Agent (🟡 Scoring + Tests)
interview_scheduling      →  Scheduling Agent (🟢 Calendar coordination)
[NEW]                     →  Communication Agent (🟡 Omnichannel)
```

**Migration Status:**
- 🟢 **Implemented:** Job Intake, Sourcing, Screening, Scheduling (proto-agents ready)
- 🟡 **Planned:** Evaluation, Communication (Q1 2026)

---

## 🎯 Intent Routing Flow

```
User Message: "Preciso criar uma vaga de Python sênior"
       │
       ▼
┌─────────────────────────┐
│   Intent Router         │
│   (Claude Sonnet 4.5)   │
│                         │
│   Classifies intent:    │
│   → create_job_vacancy  │
│   Confidence: 0.95      │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│   Entity Extraction     │
│   (Claude Sonnet 4.5)   │
│                         │
│   Extracts:             │
│   - job_title: "Python  │
│     Sênior"             │
│   - seniority: "sênior" │
│   - skills: ["Python"]  │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│    Task Planner         │
│                         │
│   Creates plan:         │
│   1. Collect job details│
│   2. Generate JD        │
│   3. Request approval   │
│   4. Publish to ATS     │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│   Policy Engine         │
│                         │
│   Validates:            │
│   ✓ User has permission │
│   ✓ Within budget       │
│   ✓ No conflicts        │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Job Intake Agent       │
│  (job_creation.py)      │
│                         │
│  Executes workflow:     │
│  → Conversational       │
│     collection of data  │
│  → Generates frames     │
│  → Stores in PostgreSQL │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│   State Manager         │
│                         │
│   Stores:               │
│   - Conversation history│
│   - Agent results       │
│   - Workflow progress   │
└─────────────────────────┘
       │
       ▼
   Response to User
```

---

## 📊 Agent Capabilities Matrix

| Agent | Primary Intent | LLM Model | Proto-Agent | External APIs | Database Tables |
|-------|---------------|-----------|-------------|---------------|-----------------|
| **Job Intake** | `create_job_vacancy` | Claude 4.5 | `job_vacancy_nodes.py` | Gupy, Pandapé | `job_vacancies` |
| **Sourcing** | `search_candidates` | Claude 4.5 | `candidate_search.py` | Pearch AI | `candidates`, `pearch_searches` |
| **Screening** | `candidate_screening` | Claude 4.5, GPT-4 | Voice screening system | OpenMic.ai, Deepgram | `voice_screening_calls`, `voice_screening_analyses` |
| **Evaluation** | `candidate_evaluation` | Claude 4.5 | 🟡 Planned | - | `candidate_evaluations` |
| **Scheduling** | `interview_scheduling` | Claude 4.5 | `interview_scheduling_nodes.py` | MS Graph | `interviews` |
| **Communication** | `communication` | Claude 4.5 | 🟡 Planned | WhatsApp, Email | `communications` |

---

## 🛠️ Technology Stack Summary

### Backend (Python)
```yaml
Framework: FastAPI 0.115+
Runtime: Python 3.11
LLM Orchestration:
  - LangChain 0.3+
  - LangGraph 0.2+
AI Models:
  - Anthropic Claude Sonnet 4.5 (primary)
  - Google Gemini Flash 2.5 (voice transcription)
  - OpenAI GPT-4 (real-time voice)
Database: PostgreSQL 16 (Neon on Replit)
Cache: Redis (planned)
Testing: pytest, pytest-asyncio
```

### Frontend (TypeScript)
```yaml
Framework: Next.js 15.5.6
Runtime: Node.js 20
UI Library: React 19
Component Library: shadcn/ui + Radix UI
Styling: Tailwind CSS v3
Charts: Chart.js
Build: Static Export (production)
```

### Observability
```yaml
LLM Tracing: LangSmith (✅ Active)
Error Tracking: Sentry (🟡 Planned)
Metrics: Prometheus + Grafana (🟡 Planned)
Code Quality: SonarCloud (🟡 Planned)
Security: Snyk + Dependabot (🟡 Planned)
Analytics: PostHog (🟡 Planned)
```

### External APIs
```yaml
AI/LLM:
  - Anthropic Claude API
  - Google Gemini API
  - OpenAI GPT API
Recruitment:
  - Pearch AI (candidate search)
  - OpenMic.ai (voice screening)
  - Gupy ATS
  - Pandapé ATS
Communication:
  - Microsoft Graph (calendar + email)
  - WhatsApp Business API (planned)
Voice:
  - Deepgram (speech-to-text)
  - Google Cloud TTS (text-to-speech)
```

---

## 💾 Data Models (PostgreSQL Schema)

```sql
-- Conversations
conversations
  ├── id (UUID)
  ├── user_id
  ├── intent
  ├── workflow_type
  ├── workflow_data (JSONB)
  └── status

-- Messages
messages
  ├── id (UUID)
  ├── conversation_id (FK)
  ├── role (user|ai)
  ├── content
  └── message_metadata (JSONB)

-- Job Vacancies
job_vacancies
  ├── id (UUID)
  ├── job_title
  ├── department
  ├── technical_requirements (JSONB)
  ├── salary_range
  ├── interview_stages (JSONB)
  └── governance_rules (JSONB)

-- Candidates
candidates
  ├── id (UUID)
  ├── name
  ├── email
  ├── phone
  ├── skills (JSONB)
  ├── experience (JSONB)
  └── source (local|pearch|gupy|pandape)

-- Voice Screening
voice_screening_calls
  ├── id (UUID)
  ├── candidate_id (FK)
  ├── job_vacancy_id (FK)
  ├── call_sid
  ├── transcript
  └── status

voice_screening_analyses
  ├── id (UUID)
  ├── screening_call_id (FK)
  ├── tech_score (0-100)
  ├── comm_score (0-100)
  ├── fit_score (0-100)
  ├── overall_score (0-100)
  └── overall_recommendation

-- Interviews
interviews
  ├── id (UUID)
  ├── candidate_id (FK)
  ├── job_vacancy_id (FK)
  ├── scheduled_time
  ├── interviewer_email
  ├── ms_graph_event_id
  └── status

-- Pearch Searches
pearch_searches
  ├── id (UUID)
  ├── user_id
  ├── query
  ├── results_count
  ├── credits_consumed
  └── created_at

-- ATS Integration
gupy_sync_logs
pandape_sync_logs
  ├── id (UUID)
  ├── entity_type (candidate|job_vacancy)
  ├── entity_id
  ├── sync_status
  └── last_synced_at
```

---

## 🔐 Security & Secrets Management

```yaml
Secret Storage: Replit Secrets (environment variables)

Required Secrets:
  # AI/LLM
  - ANTHROPIC_API_KEY
  - GOOGLE_GEMINI_API_KEY (optional)
  - OPENAI_API_KEY (for voice)
  
  # Databases
  - DATABASE_URL
  - PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
  
  # External Services
  - PEARCH_API_KEY
  - OPENMIC_API_KEY
  - AZURE_CLIENT_ID (MS Graph)
  - AZURE_CLIENT_SECRET
  - AZURE_TENANT_ID
  
  # Observability
  - LANGSMITH_API_KEY
  - LANGSMITH_WORKSPACE_ID

Authentication:
  - JWT tokens for API
  - OAuth 2.0 for MS Graph
  - API keys for external services
```

---

## 📈 Current Implementation Status

| Component | Status | Completeness |
|-----------|--------|--------------|
| **Orchestrator** | 🟢 Implemented | 90% |
| ├─ Intent Router | 🟢 Active | 95% |
| ├─ Task Planner | 🟢 Active | 85% |
| ├─ Policy Engine | 🟢 Active | 80% |
| └─ State Manager | 🟢 Active | 70% (in-memory) |
| **Job Intake Agent** | 🟢 Implemented | 95% |
| **Sourcing Agent** | 🟢 Implemented | 90% |
| **Screening Agent** | 🟢 Implemented | 85% |
| **Scheduling Agent** | 🟢 Implemented | 80% |
| **Evaluation Agent** | 🟡 Planned | 0% |
| **Communication Agent** | 🟡 Planned | 0% |
| **ATS Sync Service** | 🟢 Implemented | 75% |
| **Analytics Service** | 🟡 Planned | 0% |
| **LangSmith Observability** | 🟢 Active | 100% |
| **Redis Cache** | 🟡 Planned | 0% |
| **Sentry Error Tracking** | 🟡 Planned | 0% |
| **Prometheus Metrics** | 🟡 Planned | 0% |

**Legend:**
- 🟢 Implemented & Active
- 🟡 Planned for Q1 2026
- 🔴 Not Planned

---

## 🔄 Request Flow Example: "Buscar 5 desenvolvedores Python"

```
1. User Input (Frontend)
   ↓
2. POST /api/v1/chat (FastAPI)
   ↓
3. Orchestrator.process_message()
   ├─ Intent Router: classify_intent()
   │  └─ Claude Sonnet 4.5: "candidate_search" (confidence: 0.95)
   ├─ Entity Extraction: extract_entities()
   │  └─ Claude Sonnet 4.5: {search_query: "desenvolvedores Python", limit: 5}
   ├─ Task Planner: create_plan()
   │  └─ Plan: [search_local_db, search_pearch_if_needed, return_results]
   └─ Policy Engine: validate()
      └─ Check: Pearch credits available (10/day limit)
   ↓
4. Sourcing Agent Execution
   ├─ Search Local PostgreSQL
   │  └─ Query: SELECT * FROM candidates WHERE skills @> '["Python"]' LIMIT 5
   │  └─ Result: 2 candidates found
   ├─ Insufficient? Expand to Pearch AI
   │  └─ POST https://api.pearch.ai/search
   │  └─ Query: "Python developers with 3+ years experience"
   │  └─ Result: 8 candidates (combined total: 10)
   │  └─ Credits consumed: 1 (9 remaining today)
   └─ Return top 5 (sorted by match_score)
   ↓
5. State Manager: save_results()
   └─ PostgreSQL: INSERT INTO conversations, messages, pearch_searches
   ↓
6. Response Generation
   ├─ Claude Sonnet 4.5: generate_response()
   └─ Context: [candidates, search_metadata, next_steps]
   ↓
7. Return to Frontend
   ├─ Message content (conversational)
   ├─ contextData (side panel with candidate cards)
   └─ shouldDisplay: true
   ↓
8. Frontend Rendering
   ├─ Chat message displayed
   └─ Side panel shows 5 candidates with actions
```

**Total Latency:** ~2.5 seconds
- Intent classification: 400ms
- Entity extraction: 350ms
- Local DB search: 80ms
- Pearch AI search: 1200ms
- Response generation: 450ms
- Network overhead: ~50ms

---

## 🎓 Key Architectural Decisions

### 1. Multi-Agent vs. Super-Agent
**Decision:** Multi-Agent  
**Rationale:** Specialization, observability, extensibility (ADR-001)  
**Trade-off:** Orchestration overhead < Debugging complexity

### 2. LangGraph vs. Custom State Machine
**Decision:** LangGraph  
**Rationale:** Native LangChain integration, built-in checkpointing, proven at scale  
**Trade-off:** Learning curve acceptable for productivity gains

### 3. PostgreSQL vs. Vector DB
**Decision:** PostgreSQL with pgvector extension  
**Rationale:** Single database for all data, sufficient for 10K-100K candidates  
**Trade-off:** Will migrate to dedicated vector DB (Pinecone/Weaviate) if scale >1M

### 4. In-Memory State vs. Redis
**Decision:** In-Memory (MVP) → Redis (Production)  
**Rationale:** Simpler MVP, Redis planned for horizontal scaling  
**Trade-off:** Single-instance limitation acceptable for MVP

### 5. Anthropic Claude vs. OpenAI GPT
**Decision:** Claude Sonnet 4.5 (primary), GPT-4 (voice only)  
**Rationale:** Claude superior for Portuguese, better instruction following, lower cost  
**Trade-off:** Multi-model complexity < quality gains

---

**Próxima seção:** Como o treinamento se aplica a cada agente (criando agora...)
