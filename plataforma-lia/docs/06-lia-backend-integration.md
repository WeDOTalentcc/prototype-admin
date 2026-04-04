# Backend LIA Agent System - Integração

## 📋 Overview

O **LIA Agent System** é o backend Python/FastAPI que alimenta a inteligência artificial da plataforma WedoTalent. Ele fornece a LIA (Learning Intelligence Assistant) com capacidades conversacionais avançadas e automação de workflows.

---

## 🏗️ Arquitetura Dual

A plataforma WedoTalent agora opera em **arquitetura dual**:

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 15.5.6)                               │
│  plataforma-lia/                                         │
│  • UI/UX completo                                        │
│  • Design system                                         │
│  • Páginas e componentes                                │
│  • Dashboards e visualizações                            │
└──────────────────────────────────────────────────────────┘
               ↕ WebSocket/REST API
┌──────────────────────────────────────────────────────────┐
│  BACKEND (Python FastAPI)                                │
│  lia-agent-system/                                       │
│  • LangGraph state machines                              │
│  • LangChain orchestration                               │
│  • Claude/OpenAI/Gemini integration                      │
│  • PostgreSQL + pgvector                                 │
│  • Celery + RabbitMQ                                     │
└──────────────────────────────────────────────────────────┘
               ↕ External APIs
┌──────────────────────────────────────────────────────────┐
│  INTEGRATIONS LAYER                                      │
│  • Pearch AI (candidate search)                          │
│  • Merge.dev (ATS sync)                                  │
│  • Synthflow (voice screening)                           │
│  • Microsoft Graph (Teams + Outlook)                     │
│  • Twilio (WhatsApp + SMS)                               │
└──────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Repositórios

### Frontend (Existente)
```
plataforma-lia/
├── src/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   └── services/         # NEW: lia-chat.ts (API client)
├── docs/                 # Documentação técnica
└── package.json
```

### Backend (Novo)
```
lia-agent-system/
├── app/
│   ├── agents/          # LangGraph state machines
│   ├── api/             # FastAPI endpoints
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   └── integrations/    # External APIs
├── docker-compose.yml   # PostgreSQL, Redis, RabbitMQ
└── requirements.txt
```

---

## 🚀 Como Funciona

### 1. Usuário Interage com Frontend

```typescript
// plataforma-lia/src/services/lia-chat.ts
await liaChatService.sendMessage("Preciso criar uma vaga de Python")
```

### 2. Frontend Conecta ao Backend via WebSocket

```
ws://localhost:8000/api/v1/chat/ws/user-123
```

### 3. Backend Processa com LangGraph

```python
# lia-agent-system/app/agents/conversation.py
conversation_graph.ainvoke(state)
```

### 4. LIA Responde via Claude

```python
# lia-agent-system/app/services/llm.py
llm_service.claude.ainvoke(messages)
```

### 5. Response Volta ao Frontend em Tempo Real

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // { type: 'message', content: 'Entendi! Vaga de Python...', ... }
}
```

---

## 🔗 Como Integrar

### Passo 1: Iniciar Backend

```bash
cd lia-agent-system

# Configure .env com suas API keys
cp .env.example .env
nano .env

# Inicie serviços
docker-compose up -d postgres redis rabbitmq

# Inicie API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Passo 2: Instalar Cliente no Frontend

```bash
cd plataforma-lia
npm install socket.io-client
```

### Passo 3: Usar Serviço de Chat

Veja documentação completa em:
- `lia-agent-system/FRONTEND_INTEGRATION.md`
- `lia-agent-system/QUICKSTART.md`

---

## 📊 Features Disponíveis (MVP)

### ✅ Implementado
- [x] Chat conversacional com Claude
- [x] WebSocket real-time
- [x] REST API fallback
- [x] Intent classification
- [x] Entity extraction
- [x] Conversation persistence (PostgreSQL)
- [x] Message history

### 🔄 Em Desenvolvimento
- [ ] Job creation workflow (13 stages)
- [x] Merge.dev integration
- [ ] Microsoft Teams bot
- [ ] Pearch AI candidate search
- [ ] WhatsApp screening
- [ ] Voice screening (Synthflow)

---

## 🔑 Configuração de API Keys

### Claude (OBRIGATÓRIO)
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### OpenAI (Fallback)
```bash
OPENAI_API_KEY=sk-xxxxx
```

### Google Gemini (Futuro)
```bash
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### LangSmith (Observability)
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-xxxxx
LANGCHAIN_PROJECT=lia-agent-system
```

---

## 🐛 Troubleshooting

### Backend não inicia
✅ Verifique se Docker está rodando: `docker ps`
✅ Verifique logs: `docker-compose logs -f`
✅ Verifique API key no `.env`

### Frontend não conecta
✅ Verifique se backend está rodando: `curl http://localhost:8000/health`
✅ Verifique CORS no backend (`plataforma-lia` deve estar em `CORS_ORIGINS`)
✅ Verifique URL no frontend (`.env.local`)

### LIA não responde
✅ Verifique logs do backend: `docker-compose logs -f api`
✅ Verifique Claude API key: `ANTHROPIC_API_KEY`
✅ Verifique LangSmith traces: https://smith.langchain.com/

---

## 📚 Documentação Completa

Veja repositório `lia-agent-system/`:
- `README.md` - Visão geral completa
- `QUICKSTART.md` - Guia de início rápido
- `FRONTEND_INTEGRATION.md` - Como integrar frontend
- `docs/06-plano-lia-agent-system-opcao-b.md` - Plano completo 5 meses

---

## 🎯 Roadmap de Integração

### Fase 1: Chat Básico (✅ CONCLUÍDO)
- Backend FastAPI funcionando
- LangGraph conversation agent
- WebSocket real-time
- Frontend integrado

### Fase 2: Job Creation (Próxima)
- Workflow de 13 stages
- Merge.dev integration
- Microsoft Teams notifications
- Approval system

### Fase 3: Candidate Search
- Pearch AI integration
- RAG with pgvector
- ML ranking

### Fase 4: Screening
- WhatsApp automation
- Voice screening
- Automated scoring

### Fase 5: Scheduling
- Outlook Calendar
- Auto-scheduling
- Reminders

---

**Última atualização**: Novembro 2025
**Status**: ✅ MVP Chat funcionando
