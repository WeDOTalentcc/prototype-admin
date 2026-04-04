# LIA Agent System

**AI-powered recruitment agent** built with FastAPI, LangGraph, and Claude.

## 🎯 Overview

LIA (Learning Intelligence Assistant) is an autonomous conversational AI agent that automates the complete recruitment workflow from job creation through interview scheduling.

### Key Features

- 🤖 **Conversational AI**: Natural language interface powered by Claude Sonnet 4.5
- 🔄 **LangGraph State Machines**: Complex workflow orchestration
- 💬 **WebSocket Support**: Real-time chat interface
- 🗄️ **PostgreSQL + pgvector**: Persistent storage with vector search
- 📊 **LangSmith Integration**: Complete observability and tracing
- 🔌 **Multiple Integrations**: Pearch AI, Merge.dev, Synthflow, Microsoft Graph, Twilio

## 🏗️ Architecture

```
lia-agent-system/
├── app/
│   ├── agents/          # LangGraph state machines
│   │   └── conversation.py
│   ├── api/             # FastAPI endpoints
│   │   └── v1/
│   │       └── chat.py
│   ├── core/            # Core configuration
│   │   ├── config.py
│   │   └── database.py
│   ├── models/          # SQLAlchemy models
│   │   └── conversation.py
│   ├── schemas/         # Pydantic schemas
│   │   └── chat.py
│   ├── services/        # Business logic
│   │   └── llm.py
│   └── main.py          # FastAPI app
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Claude API key (Anthropic)
- PostgreSQL (via Docker)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repo-url>
cd lia-agent-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# REQUIRED:
ANTHROPIC_API_KEY=your_claude_api_key_here
DATABASE_URL=postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db

# OPTIONAL (for full features):
OPENAI_API_KEY=your_openai_key
LANGCHAIN_API_KEY=your_langsmith_key
PEARCH_API_KEY=your_pearch_key
```

### 3. Start Services

```bash
# Start PostgreSQL, Redis, RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Wait for services to be healthy
docker-compose ps

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## 💬 Using the Chat API

### REST API

```bash
# Send message (creates new conversation)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Preciso contratar um desenvolvedor Python sênior"
  }'

# Continue conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Remoto, de preferência em São Paulo",
    "conversation_id": "uuid-from-previous-response"
  }'

# List conversations
curl http://localhost:8000/api/v1/chat/conversations?user_id=demo-user
```

### WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/demo-user');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  content: 'Oi LIA, preciso de ajuda para criar uma vaga'
}));

// Receive response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('LIA:', data.content);
};
```

## 🔧 Development

### Run with Docker

```bash
# Start all services (including API)
docker-compose up

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📊 Observability

### LangSmith Tracing

Set up LangSmith for complete LLM call tracing:

```bash
# In .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=lia-agent-system
```

View traces at: https://smith.langchain.com/

### Logs

```bash
# View API logs
docker-compose logs -f api

# View all logs
docker-compose logs -f
```

## 🔌 Integrations

### Available Integrations

| Integration | Status | Purpose |
|------------|--------|---------|
| Claude (Anthropic) | ✅ Active | Primary LLM |
| OpenAI | ⏳ Optional | Fallback LLM |
| Google Gemini | ⏳ Optional | Alternative LLM |
| Pearch AI | ⏳ Pending | Candidate search (190M+ profiles) |
| Merge.dev | ✅ Active | Universal ATS connector (Greenhouse, Lever, etc) |
| Synthflow | ⏳ Pending | Voice screening |
| Twilio | ⏳ Pending | WhatsApp + SMS |
| Microsoft Graph | ⏳ Pending | Teams + Outlook |

### Adding API Keys

Edit `.env` and set the corresponding `*_API_KEY` variables. Enable features by setting `ENABLE_*` flags to `true`.

## 📝 API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.115+
- **AI Orchestration**: LangChain 0.3+ & LangGraph 0.2+
- **LLM**: Claude Sonnet 4.5 (Anthropic)
- **Database**: PostgreSQL 15+ with pgvector
- **Cache**: Redis 7
- **Queue**: RabbitMQ 3 + Celery
- **Observability**: LangSmith

## 🚦 Roadmap

### ✅ Phase 1: Foundation (Current)
- [x] FastAPI setup
- [x] LangGraph conversation agent
- [x] WebSocket support
- [x] Database models
- [x] Claude integration

### 🔄 Phase 2: Job Creation (Next)
- [ ] Job creation workflow (13 stages)
- [x] Merge.dev ATS integration
- [ ] Microsoft Teams notifications
- [ ] Approval system

### 📅 Phase 3: Candidate Search
- [ ] Pearch AI integration
- [ ] RAG with pgvector
- [ ] ML ranking system

### 📅 Phase 4: Screening
- [ ] WhatsApp screening (Twilio)
- [ ] Voice screening (Synthflow)
- [ ] Automated scoring

### 📅 Phase 5: Scheduling
- [ ] Outlook Calendar integration
- [ ] Auto-scheduling logic
- [ ] Interview reminders

## 🤝 Contributing

This is a private project. For questions or suggestions, contact the development team.

## 📄 License

Proprietary - WedoTalent © 2025
