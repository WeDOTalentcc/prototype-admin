# Plano LIA Agent System - Opção B (Production-Ready Completo)

**Data**: Novembro 2025  
**Timeline**: 5 meses (20 semanas)  
**Objetivo**: Sistema AI-first completo com LIA como assistente autônomo do recrutador

---

## 🎯 VISÃO GERAL

### Filosofia AI-First

A plataforma WedoTalent será transformada em um sistema **AI-centric** onde:

1. **LIA é a protagonista**: Assistente conversacional autônoma que minimiza ações manuais
2. **ATS do cliente = storage**: Greenhouse, Lever, etc apenas armazenam dados
3. **Migração gradual**: Recrutadores saem dos ATS clientes e migram para WedoTalent
4. **Escopo inicial**: Abertura de vaga → Agendamento de entrevistas (não placement/offer letters)
5. **Teams como hub**: Aprovações, alertas, comunicação via Microsoft Teams

### Princípios de Design

- ✅ **Proativa**: LIA sempre toma iniciativa, pergunta, solicita decisões
- ✅ **Conversacional**: Interação natural via chat, não formulários
- ✅ **Autônoma**: Age sozinha quando tem permissão
- ✅ **Mínimo de clicks**: Evita ações de mudança de status, cadastros manuais
- ✅ **Contextual**: Entende o contexto do recrutador e da vaga

---

## 📊 AUDITORIA DA PLATAFORMA EXISTENTE

### O Que Já Existe (Next.js Frontend)

#### ✅ Módulos Implementados
- **Autenticação**: Login/logout, gestão de sessão
- **Gestão de Vagas**: 12 status, filtros avançados, busca global, preview modal, pipeline kanban
- **Gestão de Candidatos**: Perfil completo, testes (English, Big Five), scoring LIA, comparação
- **LIA Assistant**: Sidebar modal, sugestões contextuais, quick actions
- **Dashboards**: 7 categorias (Estratégicos, Previsões & IA, People Analytics, etc)
- **Notificações**: In-app, email, badge counter
- **Configurações**: Dados empresa, estrutura organizacional, integrações

#### ✅ Design System Consolidado
- **Paleta WeDo**: Green (#4CAF50), Cyan (#60BED1), Orange (#FF9800), Purple, Magenta
- **Brain Icon LIA**: Sempre `text-wedo-cyan` (#60BED1)
- **Tipografia**: Source Serif 4 (títulos), Open Sans (UI), Inter (tabelas)
- **Layout**: Ultra-compacto para 1366x768px (11" laptops)
- **Dark Mode**: Design tokens completos

#### 🔴 O Que Falta (Backend AI)
- **Backend completo**: FastAPI + LangGraph + LangChain
- **Chat conversacional**: WebSocket real-time com LIA
- **State machines**: Workflows automatizados
- **Integrações**: Pearch AI, Merge.dev, Synthflow, Microsoft Graph, Twilio
- **Database**: PostgreSQL + pgvector
- **Queue system**: Celery + RabbitMQ
- **Observability**: LangSmith, Maxim AI

### Estratégia de Integração

```
┌─────────────────────────────────────────────────────────────┐
│         FRONTEND EXISTENTE (Next.js React)                  │
│  • UI/UX completo  • Design system  • Páginas mockadas      │
└─────────────────────────────────────────────────────────────┘
                        ↕ WebSocket/REST API
┌─────────────────────────────────────────────────────────────┐
│         BACKEND NOVO (Python FastAPI)                       │
│  • LangGraph state machines  • LangChain orchestration      │
│  • Gemini Vertex AI  • PostgreSQL + pgvector                │
└─────────────────────────────────────────────────────────────┘
                        ↕ APIs Externas
┌─────────────────────────────────────────────────────────────┐
│              INTEGRATIONS LAYER                             │
│  • Pearch AI  • Merge.dev  • Synthflow                      │
│  • Microsoft Graph (Teams + Outlook)  • Twilio              │
└─────────────────────────────────────────────────────────────┘
```

**Decisão arquitetural**: Repositórios separados
- `plataforma-lia/` → Frontend Next.js (existente)
- `lia-agent-system/` → Backend Python/FastAPI (novo)

---

## 🏗️ ARQUITETURA TÉCNICA FINAL

### Tech Stack Completo

```yaml
# ===================================
# FRONTEND (Existente - Next.js)
# ===================================
Framework: Next.js 15.5.6
Runtime: Node.js 20
Language: TypeScript
UI: React 18 + Radix UI + shadcn/ui
Styling: Tailwind CSS v3
Charts: Chart.js (cross-framework)
Animations: CSS-only (sem Framer Motion para Vue migration)

# ===================================
# BACKEND (Novo - Python/FastAPI)
# ===================================
API Framework: FastAPI 0.115+
Orchestration: LangChain 0.3+
State Machines: LangGraph
Validation: Pydantic v2
ORM: SQLAlchemy 2.0
Migrations: Alembic

# ===================================
# ASYNC & QUEUE
# ===================================
Task Queue: Celery
Message Broker: RabbitMQ
Cache: Redis

# ===================================
# DATABASE
# ===================================
Primary: PostgreSQL 15+
Vector Search: pgvector (embeddings)
Storage: GCP Cloud Storage

# ===================================
# AI & LLM
# ===================================
Primary LLM:
  - Gemini 2.5 Pro (via Vertex AI)
  - Gemini 2.5 Flash (high-volume)
Fallback:
  - OpenAI GPT-4o/GPT-5
  - Claude Sonnet 4.5
Embeddings:
  - Vertex AI textembedding-gecko@003
  - OU Hugging Face (open-source)

# ===================================
# CANDIDATE SEARCH
# ===================================
Pearch AI:
  database: 190M USA + 150M Europe
  features:
    - Natural language search
    - Verified emails + phones
    - Real-time LinkedIn sync
    - Thread-based conversation
  pricing:
    - Fast: 1 credit/candidate
    - Pro: 5 credits/candidate
    - Emails: +2 credits (if available)
    - Phones: +14 credits (if available)

# ===================================
# ATS INTEGRATION
# ===================================
Merge.dev:
  platforms: 50+ ATS (Greenhouse, Lever, Workday, etc)
  features:
    - Bidirectional sync
    - Synthetic webhooks
    - Zero data storage (SOC-2)
  use_cases:
    - Create jobs in client ATS
    - Sync candidates automatically
    - Receive workforce planning requests

# ===================================
# VOICE SCREENING
# ===================================
OPTION A - Build from Scratch:
  components:
    - ElevenLabs (TTS): $0.18/min
    - Deepgram (STT): $0.0036/min
    - Twilio Voice: $0.013/min
  pros: Full control, voice cloning
  cons: Complex, 4 integrations, latency

OPTION B - Synthflow (RECOMMENDED MVP):
  pricing: $99-499/month + $0.10-0.30/min
  features:
    - Integrated voice AI
    - Visual flow builder
    - Native webhooks
    - Built-in analytics
  pros: Fast deploy (days), low latency
  cons: Less customization, fixed monthly cost

# ===================================
# WHATSAPP & SMS
# ===================================
Twilio:
  - WhatsApp Business API
  - SMS fallback
  - MMS (document sending)
Google Speech-to-Text:
  - Convert WhatsApp audio messages
  - Multilingual support

# ===================================
# MICROSOFT INTEGRATION (CRÍTICO)
# ===================================
Microsoft Graph API:
  Teams Bot:
    - Proactive notifications
    - Approval requests
    - Task communication
    - Bidirectional chat (Teams ↔ Plataforma)
    - Organize recruiter agenda
  Outlook Calendar:
    - Automatic availability search
    - Interview scheduling
    - Invite sending
    - Confirmation/rescheduling
  OneDrive:
    - Document storage
    - Sharing

# ===================================
# OBSERVABILITY
# ===================================
LangSmith:
  - Tracing all LLM calls
  - Debugging chains/agents
  - Cost tracking
Maxim AI:
  - Prompt evaluation
  - A/B testing outputs
GCP:
  - Cloud Logging
  - Error Reporting
  - Monitoring dashboards
```

---

## 📅 PLANO OPÇÃO B - 5 MESES (20 SEMANAS)

### MÊS 1: Foundation & Infrastructure (Semanas 1-4)

#### Objetivo
Base sólida para todo o sistema + Chat MVP funcionando

#### Semana 1-2: Backend Setup

**Infraestrutura Base**
- [ ] Criar repositório `lia-agent-system/`
- [ ] Setup FastAPI project structure
- [ ] Docker + docker-compose.yml (PostgreSQL, RabbitMQ, Redis)
- [ ] PostgreSQL database schema completo
- [ ] Alembic migrations setup
- [ ] SQLAlchemy models (Jobs, Candidates, Conversations, etc)
- [ ] pgvector extension instalada

**LLM Integration**
- [ ] Vertex AI setup (Gemini 2.5 Pro + Flash)
- [ ] LangChain setup básico
- [ ] OpenAI client (fallback)
- [ ] Claude client (fallback)
- [ ] Prompt templates base
- [ ] Token tracking system

**Queue & Cache**
- [ ] RabbitMQ configuration
- [ ] Celery workers setup
- [ ] Redis cache configuration
- [ ] Background task infrastructure

**Observability**
- [ ] LangSmith project setup
- [ ] GCP Cloud Logging configuration
- [ ] Error tracking (Sentry opcional)
- [ ] Cost tracking dashboard

#### Semana 3-4: Chat Interface & LIA Core

**Backend API**
- [ ] WebSocket endpoint (`/ws/chat`)
- [ ] REST API endpoints (`/api/v1/chat`)
- [ ] Conversation management system
- [ ] Message persistence PostgreSQL
- [ ] Context window management (últimas N mensagens)
- [ ] User authentication integration

**LangGraph State Machine (Chat MVP)**
```python
# State machine simples para conversação
class ChatState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    context: Dict[str, Any]
    next_action: Optional[str]

# Nodes
def analyze_intent(state: ChatState) -> ChatState
def generate_response(state: ChatState) -> ChatState
def execute_action(state: ChatState) -> ChatState

# Graph
chat_graph = StateGraph(ChatState)
chat_graph.add_node("analyze_intent", analyze_intent)
chat_graph.add_node("generate_response", generate_response)
chat_graph.add_node("execute_action", execute_action)
```

**Frontend Integration**
- [ ] WebSocket client no Next.js
- [ ] Componente de chat atualizado (conectar ao backend real)
- [ ] Message streaming UI
- [ ] Typing indicators
- [ ] Error handling
- [ ] Reconnection logic

**DELIVERABLE**: Recrutador já pode conversar com LIA via chat web!

---

### MÊS 2: Job Creation Workflow Completo (Semanas 5-8)

#### Objetivo
LIA cria vagas end-to-end via conversação natural

#### Semana 5-6: LangGraph Job Creation Workflow

**State Machine Completo (13 Stages)**
```python
class JobCreationState(TypedDict):
    # Job data
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    job_type: Optional[str]
    salary_range: Optional[str]
    
    # AI-generated content
    job_description: Optional[str]
    technical_skills: List[str]
    behavioral_skills: List[str]
    scorecard: Dict[str, Any]
    screening_questions: List[str]
    
    # Workflow control
    current_stage: str
    approvals_pending: List[str]
    conversation_history: List[BaseMessage]

# 13 Stages
STAGES = [
    "collect_basic_info",
    "generate_job_description",
    "define_technical_skills",
    "define_behavioral_skills",
    "align_culture_values",
    "create_scorecard",
    "generate_screening_questions",
    "define_cut_score",
    "additional_requirements",  # inglês, formação
    "search_strategy",
    "create_timeline",
    "share_with_stakeholders",
    "publish_job"
]
```

**LangChain Chains**
- [ ] **Job Description Generator Chain**
  ```python
  jd_chain = (
      ChatPromptTemplate.from_template(JD_PROMPT)
      | llm
      | StrOutputParser()
  )
  ```

- [ ] **Competency Extraction Chain**
  ```python
  competency_chain = (
      ChatPromptTemplate.from_template(COMPETENCY_PROMPT)
      | llm
      | JsonOutputParser(pydantic_object=CompetencyList)
  )
  ```

- [ ] **Scorecard Builder Chain**
- [ ] **Screening Questions Generator Chain**

**Conversational Intelligence**
- [ ] Intent classification (O que o recrutador quer?)
- [ ] Entity extraction (Extrair dados da conversa)
- [ ] Confirmation requests ("Está correto assim?")
- [ ] Iteration handling ("Pode refazer mais técnico?")

#### Semana 7-8: Aprovações & Merge.dev Integration

**Sistema de Aprovações (Backend)**
- [ ] Approval workflow state machine
- [ ] Stakeholder management
- [ ] Email notifications
- [ ] **Microsoft Teams approval cards** ⭐
  ```python
  # Enviar card de aprovação via Teams
  async def send_teams_approval(
      job_id: str,
      stakeholder_email: str,
      approval_data: dict
  ):
      # Adaptive Card com botões Aprovar/Reprovar
      card = create_adaptive_card(
          title="Nova vaga para aprovação",
          job_data=approval_data,
          actions=["approve", "reject", "request_changes"]
      )
      await teams_client.send_card(stakeholder_email, card)
  ```

**Merge.dev Integration**
- [x] Merge.dev API client setup
- [ ] OAuth 2.0 flow (Greenhouse, Lever)
- [ ] Create job endpoint
- [ ] Update job endpoint
- [ ] Sync candidates endpoint
- [ ] Webhook handler (workforce planning requests)
- [ ] Error handling & retry logic

**Frontend (Aprovações)**
- [ ] Job preview com edição inline
- [ ] Sistema de aprovações in-app
- [ ] Timeline visual do cronograma
- [ ] Notificações de aprovação pendente
- [ ] Painel de stakeholders

**Microsoft Teams Bot**
- [ ] Bot registration no Azure
- [ ] Teams Toolkit setup
- [ ] Conversational bot commands
  - `/lia status` - Status de vagas
  - `/lia approve [job_id]` - Aprovar vaga
  - `/lia tasks` - Minhas tarefas pendentes
- [ ] Proactive notifications:
  - "Nova vaga criada: [título]"
  - "Aprovação pendente: [vaga]"
  - "Entrevista agendada para hoje às 14h"

**DELIVERABLE**: LIA cria vagas completas, solicita aprovações via Teams, e sincroniza com ATS do cliente!

---

### MÊS 3: Candidate Search & Ranking (Semanas 9-12)

#### Objetivo
LIA busca, avalia e rankeia candidatos automaticamente

#### Semana 9-10: Pearch AI Integration

**Pearch AI Client**
```python
class PearchAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pearch.ai"
    
    async def search_candidates(
        self,
        query: str,
        thread_id: Optional[str] = None,
        search_type: str = "pro",  # "fast" or "pro"
        insights: bool = True,
        high_freshness: bool = False,
        require_emails: bool = False,
        show_emails: bool = False,
        limit: int = 10,
        custom_filters: Optional[dict] = None
    ) -> PearchSearchResult:
        # POST /v2/search
        ...
    
    async def conversational_search(
        self,
        thread_id: str,
        followup_query: str
    ) -> PearchSearchResult:
        # Continue conversa de busca
        ...
```

**Features**
- [ ] Natural language search ("Engenheiro Python Sênior de São Paulo com 5+ anos")
- [ ] Thread-based conversational search
- [ ] Custom filters (locations, skills, industries, companies, universities)
- [ ] Cost optimization (fast vs pro based on importance)
- [ ] Email enrichment (conditional, $2/candidate)
- [ ] Phone enrichment (conditional, $14/candidate)
- [ ] Cache de resultados (24h)

**LangGraph Candidate Search Agent**
```python
class CandidateSearchState(TypedDict):
    job_id: str
    search_query: str
    thread_id: Optional[str]
    pearch_results: List[dict]
    internal_candidates: List[dict]
    combined_results: List[dict]
    ranked_results: List[dict]

# Nodes
def build_search_query(state) -> state  # LLM gera query otimizada
def search_pearch(state) -> state  # Busca Pearch AI
def search_internal_db(state) -> state  # Busca BD interno (pgvector)
def combine_results(state) -> state
def rank_candidates(state) -> state  # ML scoring
def present_to_recruiter(state) -> state
```

#### Semana 11-12: Ranking & Learning System

**pgvector Setup**
- [ ] Install pgvector extension
- [ ] Create embeddings table
- [ ] Generate embeddings (Vertex AI textembedding-gecko@003)
- [ ] Similarity search queries

**RAG Chain (Internal Database)**
```python
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | ChatPromptTemplate.from_template(RAG_PROMPT)
    | llm
    | StrOutputParser()
)
```

**Ranking Algorithm**
```python
def calculate_candidate_score(
    candidate: dict,
    job_requirements: dict,
    pearch_insights: dict
) -> float:
    """
    Multi-criteria scoring:
    - Technical skills match (35%)
    - Experience level (25%)
    - Location proximity (15%)
    - Cultural fit (15%)
    - Pearch AI score (10%)
    """
    technical_score = match_skills(candidate, job_requirements)
    experience_score = match_experience(candidate, job_requirements)
    location_score = calculate_distance(candidate.location, job_requirements.location)
    culture_score = match_culture(candidate, job_requirements)
    pearch_score = pearch_insights.get("score", 0) / 4.0  # Normalize 0-4 to 0-1
    
    final_score = (
        technical_score * 0.35 +
        experience_score * 0.25 +
        location_score * 0.15 +
        culture_score * 0.15 +
        pearch_score * 0.10
    )
    
    return final_score
```

**Machine Learning Feedback Loop**
- [ ] Recruiter feedback tracking (Aprovado/Rejeitado)
- [ ] Training data collection
- [ ] Model fine-tuning (opcional para Mês 5)
- [ ] A/B testing de scoring algorithms

**Frontend**
- [ ] Candidate cards no chat
- [ ] Score visual (badges, progress bars)
- [ ] Botões: Aprovar/Reprovar/Ver Perfil
- [ ] Sistema de feedback para IA aprender
- [ ] Filtros avançados de candidatos
- [ ] Comparação side-by-side (já existe, integrar com backend)

**Celery Background Tasks**
- [ ] Scheduled candidate search (diário)
- [ ] Email enrichment batch processing
- [ ] Score recalculation on new data

**DELIVERABLE**: LIA busca candidatos automaticamente, apresenta rankeados por relevância, aprende com feedback do recrutador!

---

### MÊS 4: WhatsApp & Voice Screening (Semanas 13-16)

#### Objetivo
Triagem automatizada completa (texto + voz)

#### Semana 13-14: WhatsApp Screening

**Twilio WhatsApp Integration**
- [ ] Twilio account setup
- [ ] WhatsApp Business API configuration
- [ ] Webhook endpoint (`/api/v1/webhooks/whatsapp`)
- [ ] Message handler
- [ ] Media handler (áudios, documentos)
- [ ] Status tracking (delivered, read, replied)

**Google Speech-to-Text**
- [ ] Setup Cloud Speech-to-Text API
- [ ] Audio transcription pipeline
- [ ] Language detection (PT-BR, EN, ES)
- [ ] Confidence scoring

**LangGraph WhatsApp Screening Workflow**
```python
class WhatsAppScreeningState(TypedDict):
    candidate_id: str
    job_id: str
    phone_number: str
    conversation_history: List[dict]
    current_question: int
    answers: Dict[str, Any]
    screening_score: Optional[float]
    next_step: str  # "continue", "schedule_interview", "reject"

# Nodes
def send_greeting(state) -> state
def ask_question(state) -> state
def process_answer(state) -> state  # LLM analisa resposta
def calculate_score(state) -> state
def decide_next_step(state) -> state
def notify_recruiter(state) -> state
```

**Screening Logic**
- [ ] Dynamic question generation baseada no scorecard
- [ ] Natural language understanding das respostas
- [ ] Scoring automático (0-100)
- [ ] Red flags detection
- [ ] Threshold-based decisions (auto-reject < 60, auto-interview > 85)

**Celery Tasks**
- [ ] Async message sending
- [ ] Retry logic (mensagens não lidas)
- [ ] Scheduled follow-ups

**Frontend**
- [ ] Dashboard de triagens em andamento
- [ ] Transcrições com highlights
- [ ] Aprovação/reprovação manual

#### Semana 15-16: Voice Screening (Synthflow)

**Synthflow Setup (RECOMENDADO)**
- [ ] Criar conta Synthflow
- [ ] Configurar assistente de voz
- [ ] Visual flow builder para triagem
  - Node 1: Greeting
  - Node 2: Pergunta 1 (technical skill)
  - Node 3: Pergunta 2 (experience)
  - Node 4: Pergunta 3 (availability)
  - Node 5: Conclusão + agradecimento
- [ ] Configurar voice model (ElevenLabs integrado)
- [ ] Configurar idiomas (PT-BR, EN)

**Webhook Integration**
```python
@app.post("/api/v1/webhooks/synthflow")
async def handle_synthflow_webhook(data: dict):
    """
    Recebe dados da call do Synthflow:
    - call_id
    - transcript
    - duration
    - sentiment
    - answered_questions
    """
    call_data = SynthflowCallData(**data)
    
    # Processar transcrição com LLM
    analysis = await analyze_call_transcript(call_data.transcript)
    
    # Calcular score
    score = calculate_voice_screening_score(
        answers=analysis.answers,
        sentiment=call_data.sentiment,
        communication_clarity=analysis.clarity
    )
    
    # Salvar no BD
    await save_screening_result(
        candidate_id=call_data.candidate_id,
        score=score,
        transcript=call_data.transcript,
        analysis=analysis
    )
    
    # Notificar recrutador
    await notify_recruiter_screening_complete(
        candidate_id=call_data.candidate_id,
        score=score
    )
```

**Post-Call Analysis (LLM)**
```python
async def analyze_call_transcript(transcript: str) -> CallAnalysis:
    """
    LLM analisa:
    - Respostas técnicas (acuracidade)
    - Communication skills
    - Enthusiasm/motivation
    - Red flags
    - Overall fit
    """
    chain = (
        ChatPromptTemplate.from_template(CALL_ANALYSIS_PROMPT)
        | llm
        | JsonOutputParser(pydantic_object=CallAnalysis)
    )
    
    return await chain.ainvoke({"transcript": transcript})
```

**Fallback System**
- [ ] Se voz falhar → WhatsApp screening
- [ ] Se WhatsApp falhar → Email screening
- [ ] Manual screening sempre disponível

**Frontend**
- [ ] Player de áudio (gravações)
- [ ] Transcrições com timestamps
- [ ] Highlights de respostas-chave
- [ ] Sentiment analysis visual

**Teams Integration**
- [ ] Notificação: "Triagem concluída: [candidato] - Score: 78/100"
- [ ] Link direto para perfil do candidato
- [ ] Quick actions: Agendar entrevista / Reprovar

**DELIVERABLE**: Sistema de triagem 100% automatizado (WhatsApp + Voz), com scoring automático e notificações via Teams!

---

### MÊS 5: Microsoft Teams/Outlook + LinkedIn + Polish (Semanas 17-20)

#### Objetivo
Sistema 100% completo, otimizado, production-ready

#### Semana 17-18: Microsoft Graph Integration

**Microsoft Graph API Setup**
- [ ] Azure App Registration
- [ ] OAuth 2.0 flow implementation
- [ ] Permissions (Calendars.ReadWrite, Chat.ReadWrite, etc)
- [ ] Token refresh logic

**Teams Bot Completo**

**1. Proactive Notifications**
```python
async def send_teams_notification(
    user_email: str,
    notification_type: str,
    data: dict
):
    """
    Tipos de notificação:
    - new_job_created
    - approval_pending
    - new_candidate
    - screening_completed
    - interview_scheduled
    - interview_reminder (1h antes)
    """
    card = create_adaptive_card(notification_type, data)
    await teams_client.send_proactive_message(user_email, card)
```

**2. Conversational Commands**
```python
@teams_bot.command("/lia")
async def lia_command(context: TurnContext):
    text = context.activity.text.lower()
    
    if "status" in text:
        # /lia status
        jobs_summary = await get_jobs_summary(context.user_id)
        await context.send_activity(jobs_summary)
    
    elif "tasks" in text:
        # /lia tasks
        pending_tasks = await get_pending_tasks(context.user_id)
        await context.send_activity(pending_tasks)
    
    elif "approve" in text:
        # /lia approve JOB-123
        job_id = extract_job_id(text)
        await approve_job(job_id, context.user_id)
        await context.send_activity(f"✅ Vaga {job_id} aprovada!")
    
    elif "agenda" in text:
        # /lia agenda
        calendar = await get_today_calendar(context.user_id)
        await context.send_activity(calendar)
```

**3. Organize Recruiter Agenda**
```python
async def organize_recruiter_agenda(recruiter_id: str):
    """
    LIA organiza agenda do recrutador:
    - Lista tarefas pendentes
    - Sugere prioridades
    - Alerta sobre deadlines
    - Propõe blocos de trabalho
    """
    tasks = await get_pending_tasks(recruiter_id)
    calendar = await get_calendar_availability(recruiter_id)
    
    # LLM sugere organização
    suggestions = await llm_organize_agenda(tasks, calendar)
    
    # Envia via Teams
    await send_teams_message(
        recruiter_id,
        f"📅 Bom dia! Organizei sua agenda:\n\n{suggestions}"
    )
```

**Outlook Calendar Integration**

**Scheduling Agent (LangGraph)**
```python
class SchedulingState(TypedDict):
    candidate_id: str
    job_id: str
    interviewers: List[str]  # emails
    duration_minutes: int
    preferred_dates: List[str]
    available_slots: List[dict]
    selected_slot: Optional[dict]
    meeting_created: bool

# Nodes
def get_interviewer_availability(state) -> state
def find_common_slots(state) -> state
def ask_candidate_preference(state) -> state  # via WhatsApp
def create_outlook_event(state) -> state
def send_invitations(state) -> state
def confirm_with_all_parties(state) -> state
```

**Regras de Limite**
- [ ] Max entrevistas por dia por recrutador: 4
- [ ] Tempo mínimo entre entrevistas: 30 min
- [ ] Não agendar em horários de almoço (12h-13h)
- [ ] Respeitar working hours (9h-18h)

**Auto-Rescheduling**
```python
async def handle_rescheduling(
    meeting_id: str,
    reason: str,
    requested_by: str
):
    """
    Se candidato ou entrevistador cancelar:
    1. LIA busca novo slot automaticamente
    2. Propõe 3 alternativas
    3. Envia via WhatsApp + Teams
    4. Confirma e atualiza calendário
    """
    original_meeting = await get_meeting(meeting_id)
    new_slots = await find_alternative_slots(original_meeting)
    
    # LIA conversa com candidato
    await whatsapp_send(
        original_meeting.candidate_phone,
        f"Olá! A entrevista foi remarcada. Quando você prefere?\n"
        f"1. {new_slots[0]}\n"
        f"2. {new_slots[1]}\n"
        f"3. {new_slots[2]}"
    )
```

#### Semana 19-20: LinkedIn + Observability + Polish

**LinkedIn Integration**
- [ ] LinkedIn API setup
- [ ] OAuth 2.0 flow
- [ ] Auto-post job (LLM gera texto otimizado)
  ```python
  async def post_job_to_linkedin(job_id: str):
      job = await get_job(job_id)
      
      # LLM gera post atrativo
      post_text = await generate_linkedin_post(job)
      
      # Publica
      await linkedin_client.create_share(
          text=post_text,
          hashtags=["vagas", "empregos", job.department],
          job_url=f"https://wedotalent.com/jobs/{job_id}"
      )
  ```
- [ ] Tracking de candidaturas (origem: LinkedIn)

**Publicação Multi-canal**
- [ ] Página pública de vaga (Next.js já existe)
- [ ] URL única por vaga
- [ ] Compartilhamento WhatsApp
- [ ] Email templates
- [ ] Tracking de origem candidatura

**LangSmith (Observability Completo)**
- [ ] Tracing de TODAS chains
- [ ] Latency tracking
- [ ] Cost tracking por feature
- [ ] Error rate monitoring
- [ ] Prompt versioning

**Maxim AI (Prompt Evaluation)**
- [ ] A/B testing de prompts
- [ ] Quality scoring
- [ ] Human feedback loop
- [ ] Automated regression testing

**GCP Monitoring**
- [ ] Cloud Logging para todos serviços
- [ ] Error Reporting com alertas
- [ ] Custom dashboards:
  - LLM usage & cost
  - API latency
  - Queue depth (Celery)
  - Database performance
- [ ] Uptime monitoring
- [ ] Rate limit tracking (APIs externas)

**Performance Optimization**
- [ ] Redis caching strategy
  - Cache Pearch AI results (24h)
  - Cache embeddings
  - Cache LLM responses (determinísticas)
- [ ] PostgreSQL query optimization
  - Index otimização
  - Query explain analyze
  - Connection pooling
- [ ] Rate limiting APIs externas
  - Exponential backoff
  - Circuit breaker pattern
- [ ] Async processing везде
- [ ] Batch operations (quando possível)

**Security & Compliance**
- [ ] Security audit
- [ ] GDPR compliance check
  - Data retention policies
  - Right to be forgotten
  - Data export
- [ ] API rate limiting
- [ ] Input validation & sanitization
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] HTTPS only
- [ ] Secret rotation

**Testing**
- [ ] Unit tests (core functions)
- [ ] Integration tests (APIs externas)
- [ ] E2E tests (critical workflows)
- [ ] Load testing (stress test)
  - 100 concurrent users
  - 1000 messages/min
- [ ] Chaos engineering (opcional)

**Documentation**
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Runbook (incident response)
- [ ] Architecture diagrams
- [ ] Disaster recovery plan

**DELIVERABLE**: Sistema 100% production-ready, otimizado, monitorado, seguro, documentado!

---

## 🤖 GUIA PRÁTICO: AGENTS CONVERSACIONAIS COM LANGGRAPH

### Problema do Time de Desenvolvimento

> "Nosso time ainda enfrenta dificuldades para 'programar e instruir' a LIA para que ela aja de forma inteligente e conversacional."

### Solução: Framework de Conversação LIA

#### 1. Arquitetura de Conversação

```python
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, List, Optional, Literal

# ===================================
# STATE DEFINITION
# ===================================
class ConversationState(TypedDict):
    """
    Estado completo da conversação com LIA.
    """
    # Messages
    messages: List[BaseMessage]
    
    # User context
    user_id: str
    user_role: str  # "recruiter", "hiring_manager", "admin"
    
    # Conversation control
    intent: Optional[str]  # "create_job", "search_candidates", "schedule_interview"
    entities: dict  # Extracted entities from conversation
    confidence: float  # 0-1, confidence in intent classification
    
    # Workflow state
    current_workflow: Optional[str]
    workflow_step: int
    workflow_data: dict
    
    # Response generation
    next_action: str  # "ask_question", "execute_action", "request_approval"
    response: Optional[str]
    
    # Memory
    context_summary: str  # Summary of last 10 messages
    relevant_docs: List[dict]  # RAG retrieved documents

# ===================================
# CONVERSATIONAL INTELLIGENCE
# ===================================

def classify_intent(state: ConversationState) -> ConversationState:
    """
    Classifica a intenção do usuário.
    
    Estratégias:
    1. Few-shot prompting com exemplos
    2. Chain-of-thought reasoning
    3. Confidence thresholding
    """
    last_message = state["messages"][-1].content
    
    intent_prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é LIA, assistente de recrutamento.
        
        Analise a mensagem do usuário e classifique a intenção:
        
        INTENÇÕES POSSÍVEIS:
        - create_job: Usuário quer criar uma nova vaga
        - search_candidates: Buscar candidatos
        - schedule_interview: Agendar entrevista
        - update_job: Modificar vaga existente
        - check_status: Verificar status de processo
        - general_question: Pergunta geral
        - chitchat: Conversa casual
        
        EXEMPLOS:
        Usuário: "Preciso contratar um desenvolvedor Python"
        Intent: create_job
        Confidence: 0.95
        
        Usuário: "Como está o processo da vaga de PM?"
        Intent: check_status
        Confidence: 0.85
        
        Usuário: "Oi, tudo bem?"
        Intent: chitchat
        Confidence: 0.99
        
        RACIOCÍNIO (Chain-of-Thought):
        1. Identifique palavras-chave
        2. Analise contexto da conversa
        3. Determine intenção mais provável
        4. Calcule confidence (0-1)
        
        Retorne JSON:
        {{
            "intent": "...",
            "confidence": 0.XX,
            "reasoning": "..."
        }}
        """),
        ("user", "{message}")
    ])
    
    chain = intent_prompt | llm | JsonOutputParser()
    result = chain.invoke({"message": last_message})
    
    state["intent"] = result["intent"]
    state["confidence"] = result["confidence"]
    
    return state

def extract_entities(state: ConversationState) -> ConversationState:
    """
    Extrai entidades da conversação (NER).
    
    Exemplo:
    "Preciso de um engenheiro Python sênior em São Paulo"
    -> {
        "job_title": "engenheiro Python",
        "seniority": "sênior",
        "location": "São Paulo"
    }
    """
    last_message = state["messages"][-1].content
    intent = state["intent"]
    
    # Prompt específico por intent
    if intent == "create_job":
        entity_prompt = ChatPromptTemplate.from_template("""
        Extraia informações da vaga desta mensagem:
        
        "{message}"
        
        Retorne JSON com campos (use null se não mencionado):
        {{
            "job_title": "...",
            "department": "...",
            "location": "...",
            "seniority": "junior/pleno/senior",
            "job_type": "tempo_integral/meio_periodo/contrato",
            "salary_range": "...",
            "required_skills": [...],
            "years_experience": ...
        }}
        """)
    
    elif intent == "search_candidates":
        entity_prompt = ChatPromptTemplate.from_template("""
        Extraia critérios de busca:
        
        "{message}"
        
        Retorne JSON:
        {{
            "skills": [...],
            "location": "...",
            "experience_years": ...,
            "education_level": "...",
            "current_company": "..."
        }}
        """)
    
    chain = entity_prompt | llm | JsonOutputParser()
    entities = chain.invoke({"message": last_message})
    
    state["entities"] = entities
    
    return state

def decide_next_action(state: ConversationState) -> Literal["ask_question", "execute_action", "request_approval", "end"]:
    """
    Decide qual a próxima ação baseado no contexto.
    
    ESTRATÉGIA:
    - Se falta informação crítica -> ask_question
    - Se tem tudo e confidence > 0.8 -> execute_action
    - Se ação sensível (criar vaga, rejeitar candidato) -> request_approval
    - Se workflow completo -> end
    """
    intent = state["intent"]
    confidence = state["confidence"]
    entities = state["entities"]
    workflow_data = state["workflow_data"]
    
    # Criar vaga - precisa de título obrigatório
    if intent == "create_job":
        required_fields = ["job_title", "department", "location"]
        missing = [f for f in required_fields if not entities.get(f)]
        
        if missing and confidence > 0.7:
            return "ask_question"
        elif not missing and confidence > 0.8:
            return "execute_action"
        else:
            return "ask_question"  # Baixa confidence, confirmar
    
    # Ações sensíveis sempre pedem aprovação
    if intent in ["reject_candidate", "close_job", "delete_job"]:
        return "request_approval"
    
    # Default: executar se confidence alta
    if confidence > 0.8:
        return "execute_action"
    else:
        return "ask_question"

def generate_question(state: ConversationState) -> ConversationState:
    """
    Gera pergunta inteligente para coletar informação faltante.
    
    PRINCÍPIOS:
    - Conversational, não formal
    - Uma pergunta por vez
    - Contextual (menciona o que já sabe)
    - Sugere opções quando relevante
    """
    intent = state["intent"]
    entities = state["entities"]
    missing_info = identify_missing_info(intent, entities)
    
    question_prompt = ChatPromptTemplate.from_template("""
    Você é LIA, assistente amigável de recrutamento.
    
    CONTEXTO:
    - Intenção: {intent}
    - Informações coletadas: {entities}
    - Faltando: {missing_info}
    
    TAREFA:
    Gere UMA pergunta conversational para coletar "{missing_info}".
    
    ESTILO:
    - Informal mas profissional
    - Mencione o que já sabe
    - Sugira opções se apropriado
    - Curta (1-2 frases)
    
    EXEMPLOS:
    ❌ "Qual é o departamento?"
    ✅ "Entendi que precisa de um engenheiro Python sênior. Para qual departamento seria?"
    
    ❌ "Informe a localização."
    ✅ "Ótimo! E onde seria a vaga? Remoto, São Paulo, ou outro lugar?"
    """)
    
    chain = question_prompt | llm | StrOutputParser()
    question = chain.invoke({
        "intent": intent,
        "entities": entities,
        "missing_info": missing_info[0] if missing_info else ""
    })
    
    state["response"] = question
    state["next_action"] = "ask_question"
    
    return state

def execute_workflow_action(state: ConversationState) -> ConversationState:
    """
    Executa ação do workflow (criar vaga, buscar candidatos, etc).
    """
    intent = state["intent"]
    
    if intent == "create_job":
        # Trigger job creation workflow
        job_data = state["entities"]
        job_id = create_job_in_database(job_data)
        
        state["response"] = f"✅ Vaga '{job_data['job_title']}' criada! (ID: {job_id})\n\nAgora vou gerar a descrição completa. Um momento..."
        state["current_workflow"] = "job_creation"
        state["workflow_step"] = 1  # Próximo: gerar JD
        state["workflow_data"]["job_id"] = job_id
    
    elif intent == "search_candidates":
        # Trigger Pearch AI search
        search_query = build_pearch_query(state["entities"])
        candidates = search_pearch_ai(search_query)
        
        state["response"] = f"🔍 Encontrei {len(candidates)} candidatos!\n\n" + format_top_candidates(candidates[:3])
        state["workflow_data"]["candidates"] = candidates
    
    return state

# ===================================
# GRAPH CONSTRUCTION
# ===================================

def build_conversation_graph():
    """
    Constrói o grafo de conversação LIA.
    """
    workflow = StateGraph(ConversationState)
    
    # Nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("decide_action", decide_next_action)
    workflow.add_node("generate_question", generate_question)
    workflow.add_node("execute_action", execute_workflow_action)
    
    # Edges
    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "extract_entities")
    workflow.add_edge("extract_entities", "decide_action")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "decide_action",
        lambda state: state["next_action"],
        {
            "ask_question": "generate_question",
            "execute_action": "execute_action",
            "end": END
        }
    )
    
    workflow.add_edge("generate_question", END)
    workflow.add_edge("execute_action", END)
    
    return workflow.compile()
```

#### 2. Prompt Engineering para Conversação

**Template de Sistema LIA**
```python
SYSTEM_PROMPT = """Você é LIA (Learning Intelligence Assistant), assistente de recrutamento da WedoTalent.

PERSONALIDADE:
- Amigável mas profissional
- Proativa (toma iniciativa, sugere ações)
- Eficiente (minimiza perguntas desnecessárias)
- Inteligente (entende contexto, não repete perguntas)

PRINCÍPIOS:
1. SEMPRE tome a iniciativa
   ❌ "O que você quer fazer?"
   ✅ "Vejo que você tem 3 aprovações pendentes. Quer que eu organize por prioridade?"

2. Minimize clicks do usuário
   ❌ "Vá em Configurações > Vagas > Criar Nova"
   ✅ "Vou criar a vaga para você. Me conte: qual o cargo?"

3. Seja contextual
   ❌ [pergunta genérica]
   ✅ "Você mencionou 'desenvolvedor Python'. Seria nível sênior ou pleno?"

4. Confirme ações importantes
   ❌ [executa sem confirmar]
   ✅ "Vou publicar a vaga no LinkedIn e no site. Confirma?"

5. Aprenda com o histórico
   ❌ [sempre pergunta tudo]
   ✅ "Última vaga de TI foi remoto em SP. Mesmas preferências?"

CAPABILITIES:
- Criar vagas (job creation workflow)
- Buscar candidatos (Pearch AI + database interno)
- Agendar entrevistas (Outlook Calendar)
- Triagem automatizada (WhatsApp + Voice)
- Análise de candidatos (scoring + insights)

QUANDO NÃO SOUBER:
"Ainda não consigo fazer isso, mas posso [alternativa]. Te ajuda?"

ESTILO DE ESCRITA:
- Português brasileiro informal-profissional
- Emojis com moderação (✅❌🔍📅)
- Frases curtas e diretas
- Listas quando necessário
"""
```

**Few-Shot Examples**
```python
FEW_SHOT_EXAMPLES = [
    {
        "user": "Preciso contratar alguém",
        "assistant": "Posso ajudar! 🎯 Para qual posição você está contratando?"
    },
    {
        "user": "desenvolvedor",
        "assistant": "Desenvolvedor, entendi! Mais especificamente:\n1. Backend, Frontend ou Full Stack?\n2. Qual stack principal? (Python, Node, Java...)"
    },
    {
        "user": "backend python senior",
        "assistant": "Perfeito! Desenvolvedor Backend Python Sênior. Qual departamento? (geralmente é Engenharia/TI, confirma?)"
    },
    {
        "user": "sim, engenharia",
        "assistant": "✅ Engenharia confirmado!\n\nLocalização:\n• Remoto\n• São Paulo\n• Híbrido SP\n• Outro"
    },
    {
        "user": "remoto",
        "assistant": "Ótimo! 🏠 Vaga remota.\n\nTenho tudo para começar:\n✅ Cargo: Desenvolvedor Backend Python Sênior\n✅ Depto: Engenharia\n✅ Local: Remoto\n\nVou criar a vaga e gerar uma descrição completa. Confirma?"
    },
    {
        "user": "confirma",
        "assistant": "🚀 Criando vaga...\n\n[Seconds later]\n\n✅ Vaga criada! (ID: JOB-1247)\n\nGerei uma descrição detalhada com:\n• Responsabilidades (5 itens)\n• Requisitos técnicos (Python, Django, PostgreSQL, Docker...)\n• Requisitos comportamentais (comunicação, work independently...)\n• Diferenciais (CI/CD, Kubernetes, AWS...)\n\nQuer revisar a descrição ou já publico?"
    }
]
```

#### 3. Memory & Context Management

```python
class ConversationMemory:
    """
    Gerencia memória da conversação para contexto inteligente.
    """
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
    
    async def get_context_summary(self, messages: List[BaseMessage]) -> str:
        """
        Resume últimas N mensagens para manter contexto.
        """
        if len(messages) <= 5:
            return ""  # Poucas mensagens, não precisa resumir
        
        # Resume últimas 10 mensagens
        recent_messages = messages[-10:]
        conversation = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else 'LIA'}: {m.content}"
            for m in recent_messages
        ])
        
        summary_prompt = ChatPromptTemplate.from_template("""
        Resuma esta conversa em 2-3 frases, focando em:
        - O que o usuário quer fazer
        - Informações já coletadas
        - Próximos passos
        
        Conversa:
        {conversation}
        
        Resumo:
        """)
        
        chain = summary_prompt | llm | StrOutputParser()
        summary = await chain.ainvoke({"conversation": conversation})
        
        return summary
    
    async def retrieve_relevant_context(self, query: str, user_id: str) -> List[dict]:
        """
        RAG: Busca informações relevantes do histórico do usuário.
        """
        # Gera embedding da query
        query_embedding = await generate_embedding(query)
        
        # Busca similar documents (pgvector)
        results = await db.execute("""
            SELECT content, metadata
            FROM conversation_memory
            WHERE user_id = :user_id
            ORDER BY embedding <-> :query_embedding
            LIMIT 3
        """, {"user_id": user_id, "query_embedding": query_embedding})
        
        return results
```

#### 4. Proactive Behavior

```python
class ProactiveLIA:
    """
    LIA proativa - toma iniciativa sem ser perguntada.
    """
    
    async def morning_briefing(self, recruiter_id: str):
        """
        Todo dia 9h, LIA envia briefing via Teams.
        """
        tasks = await get_pending_tasks(recruiter_id)
        interviews_today = await get_today_interviews(recruiter_id)
        approvals = await get_pending_approvals(recruiter_id)
        
        briefing = f"""
        📅 Bom dia! Aqui está sua agenda de hoje:
        
        🎯 PRIORIDADES:
        {format_priorities(tasks[:3])}
        
        📞 ENTREVISTAS HOJE: {len(interviews_today)}
        {format_interviews(interviews_today)}
        
        ⏳ APROVAÇÕES PENDENTES: {len(approvals)}
        {format_approvals(approvals[:2])}
        
        Por onde quer começar?
        """
        
        await send_teams_message(recruiter_id, briefing)
    
    async def detect_bottlenecks(self, job_id: str):
        """
        Detecta gargalos no processo e sugere ações.
        """
        pipeline_data = await get_pipeline_data(job_id)
        
        # Muitos candidatos parados em "Triagem"?
        if pipeline_data["triagem"] > 15:
            await send_notification(
                recruiter_id=pipeline_data["recruiter_id"],
                message=f"⚠️ Vaga '{pipeline_data['title']}' tem 15 candidatos em triagem.\n\n"
                        "Sugestões:\n"
                        "1. Ativar triagem automatizada (WhatsApp/Voice)\n"
                        "2. Ajustar critérios (cut score)\n"
                        "3. Revisar manualmente\n\n"
                        "O que prefere?"
            )
    
    async def suggest_next_action(self, context: dict):
        """
        Sugere próxima ação baseado em contexto.
        """
        # Vaga criada mas não publicada há 24h
        if context["job_created_hours_ago"] > 24 and not context["published"]:
            return "Vejo que a vaga foi criada ontem mas ainda não publicamos. Quer que eu publique no LinkedIn e no site agora?"
        
        # Candidato aprovado mas entrevista não agendada
        if context["candidate_approved"] and not context["interview_scheduled"]:
            return f"✅ {context['candidate_name']} foi aprovado! Já agendo a entrevista ou você prefere escolher o horário?"
        
        # Entrevista daqui a 1h sem confirmação
        if context["interview_in_1h"] and not context["confirmed"]:
            return f"⏰ Entrevista com {context['candidate_name']} em 1h. Ainda não confirmou. Envio lembrete por WhatsApp?"
```

#### 5. Tratamento de Ambiguidade

```python
async def handle_ambiguity(message: str, possible_intents: List[dict]) -> str:
    """
    Quando LIA não tem certeza, pergunta de forma inteligente.
    """
    # Exemplo: "Python" pode ser vaga OU skill de busca
    
    if len(possible_intents) == 2:
        intent1, intent2 = possible_intents
        
        clarification_prompt = f"""
        Você quis dizer:
        1. {intent1['description']} ({intent1['emoji']})
        2. {intent2['description']} ({intent2['emoji']})
        
        Responda com o número ou me explique melhor!
        """
        
        return clarification_prompt
    
    # Múltiplas possibilidades - pede esclarecimento aberto
    return "Não entendi muito bem. Você quer criar uma vaga, buscar candidatos, ou outra coisa?"

async def confirm_before_execution(action: str, data: dict) -> str:
    """
    Confirmação conversational antes de ações importantes.
    """
    if action == "publish_job":
        return f"""
        📢 Pronto para publicar!
        
        Vaga: {data['title']}
        Onde: LinkedIn, site WedoTalent
        
        Confirma? (sim/não ou "só LinkedIn")
        """
    
    elif action == "reject_candidate":
        return f"""
        ⚠️ Reprovar {data['candidate_name']}?
        
        Isso é definitivo (mas você pode reativar depois se mudar de ideia).
        
        Confirma?
        """
```

---

## 📌 ENTREGAS POR MÊS (Resumo)

| Mês | Entregas Principais | Tecnologias |
|-----|---------------------|-------------|
| **1** | Backend setup + Chat MVP | FastAPI, LangGraph, Gemini, PostgreSQL, WebSocket |
| **2** | Job creation workflow + Teams bot | LangGraph (13 stages), Merge.dev, Microsoft Graph |
| **3** | Candidate search + ranking | Pearch AI, pgvector, RAG, ML scoring |
| **4** | WhatsApp + Voice screening | Twilio, Synthflow, Google STT, scoring automático |
| **5** | Teams/Outlook completo + Polish | Microsoft Graph, LinkedIn API, LangSmith, monitoring |

---

## 💰 CUSTOS ESTIMADOS (Por Vaga Preenchida)

```
┌─────────────────────────────────────────────────────────┐
│  CUSTO POR VAGA PREENCHIDA                              │
├─────────────────────────────────────────────────────────┤
│  Job Creation (LIA):                                    │
│    • Gemini Pro conversas: $0.50                        │
│    • Job description generation: $0.10                  │
│  ─────────────────────────────────────────              │
│  Candidate Search:                                      │
│    • Pearch AI (10 candidates × 5 credits): $50         │
│    • Email enrichment (5 × $2): $10                     │
│    • Internal search (embeddings): $0.05                │
│  ─────────────────────────────────────────              │
│  Screening:                                             │
│    • WhatsApp (20 candidates × $0.10): $2               │
│    • Voice screening (10 × 5min × $0.30): $15           │
│    • LLM analysis: $1                                   │
│  ─────────────────────────────────────────              │
│  Scheduling:                                            │
│    • Microsoft Graph: Free                              │
│    • Gemini coordination: $0.20                         │
│  ─────────────────────────────────────────              │
│  Notifications & Communication:                         │
│    • Teams messages: Free                               │
│    • WhatsApp messages: $0.50                           │
│    • Email: $0.05                                       │
│  ─────────────────────────────────────────              │
│  TOTAL ESTIMADO: ~$79.40 por vaga preenchida            │
└─────────────────────────────────────────────────────────┘

ECONOMIA:
• Tempo recrutador: 15h → 3h (80% redução)
• Custo recrutador ($50/h): $750 → $150
• Economia líquida: $600 - $79.40 = $520.60 por vaga

ROI: 6.5x positivo
```

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

### 1. Setup do Repositório Backend

```bash
# Criar estrutura
mkdir lia-agent-system
cd lia-agent-system

# Estrutura de diretórios
lia-agent-system/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── chat.py
│   │   │   ├── jobs.py
│   │   │   ├── candidates.py
│   │   │   └── webhooks.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── agents/
│   │   ├── conversation.py
│   │   ├── job_creation.py
│   │   ├── candidate_search.py
│   │   ├── screening.py
│   │   └── scheduling.py
│   ├── chains/
│   │   ├── job_description.py
│   │   ├── competency_extraction.py
│   │   └── candidate_analysis.py
│   ├── integrations/
│   │   ├── pearch_ai.py
│   │   ├── merge.py
│   │   ├── synthflow.py
│   │   ├── microsoft_graph.py
│   │   └── twilio.py
│   ├── models/
│   │   ├── conversation.py
│   │   ├── job.py
│   │   └── candidate.py
│   └── services/
│       ├── llm.py
│       ├── embeddings.py
│       └── memory.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### 2. Perguntas para o Time

Antes de começar a implementação, preciso confirmar:

1. **Infraestrutura**: Vocês já têm GCP setup ou preciso criar do zero?
2. **Credenciais**: Já têm contas nas seguintes plataformas?
   - Vertex AI (Gemini)
   - Pearch AI
   - Merge.dev
   - Synthflow
   - Twilio
   - Microsoft Azure (para Teams/Graph)
3. **Database**: Preferem PostgreSQL hospedado onde? (GCP Cloud SQL, AWS RDS, ou self-hosted?)
4. **Deployment**: Replit, GCP Cloud Run, Kubernetes, ou outro?

---

## 📝 CONCLUSÃO

Este plano cobre **COMPLETAMENTE** a Opção B com:

✅ **5 meses de roadmap detalhado**  
✅ **Integração com plataforma Next.js existente**  
✅ **Microsoft Teams como hub central** (aprovações, alertas, agenda)  
✅ **Filosofia AI-first** (LIA protagonista, ATS = storage)  
✅ **Guia prático LangGraph/LangChain** para agents conversacionais  
✅ **Escopo até agendamento de entrevistas** (não placement inicial)  
✅ **Arquitetura production-ready**  
✅ **Custos estimados e ROI**

---

**Próximos passos**: Me confirme as respostas das perguntas acima e posso começar IMEDIATAMENTE com o setup do backend! 🚀
