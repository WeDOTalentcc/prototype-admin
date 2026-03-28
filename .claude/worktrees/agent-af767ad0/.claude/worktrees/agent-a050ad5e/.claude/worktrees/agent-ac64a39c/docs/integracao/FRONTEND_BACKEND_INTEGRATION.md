# Frontend-Backend Integration - LIA Platform

## ✅ Status: IMPLEMENTED (24/11/2025)

Integração completa entre Frontend Next.js (porta 5000) e Backend FastAPI (porta 8000) para chat conversacional com LIA Agent.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│              Frontend Next.js (Port 5000)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Chat Page (chat-page.tsx)                             │    │
│  │  - User input                                          │    │
│  │  - Message display                                     │    │
│  │  - Thinking indicators                                 │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  LIA API Client (lia-api.ts)                           │    │
│  │  - sendMessage()                                       │    │
│  │  - searchCandidates()                                  │    │
│  │  - healthCheck()                                       │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Next.js API Proxy (/api/lia/[...path]/route.ts)      │    │
│  │  - Proxies requests to localhost:8000                  │    │
│  │  - Handles CORS                                        │    │
│  └─────────────────────┬──────────────────────────────────┘    │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTP (internal)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend FastAPI (Port 8000)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Chat API (/api/v1/chat)                               │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  LIA Conversational Agent (conversation.py)            │    │
│  │  - Intent classification                               │    │
│  │  - Entity extraction                                   │    │
│  │  - Workflow execution                                  │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Pearch AI Service (pearch_service.py)                 │    │
│  │  - Candidate search (190M+ profiles)                   │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Arquivos Implementados

### Frontend (plataforma-lia/)

#### 1. **API Client Service** (`src/services/lia-api.ts`)
Service layer para comunicação com backend FastAPI.

**Métodos:**
- `healthCheck()` - Verifica status do backend
- `sendMessage(data)` - Envia mensagem para LIA agent
- `getConversations(userId)` - Lista conversas do usuário
- `getConversationHistory(conversationId)` - Histórico de uma conversa
- `searchCandidates(request)` - Busca candidatos via Pearch AI
- `searchCandidatesByJobDescription(jd)` - Busca por job description
- `checkPearchHealth()` - Verifica status Pearch AI

**Uso:**
```typescript
import { liaApi } from '@/services/lia-api'

// Enviar mensagem
const response = await liaApi.sendMessage({
  message: "Preciso de desenvolvedores Python",
  user_id: "user-123"
})

// Buscar candidatos
const candidates = await liaApi.searchCandidates({
  query: "Senior Python engineer in SF",
  limit: 10
})
```

#### 2. **API Proxy** (`src/app/api/lia/[...path]/route.ts`)
Next.js API Route que proxia requisições para o backend (porta 8000).

**Por que é necessário?**
- Replit expõe apenas a porta 5000 publicamente
- Backend (porta 8000) só é acessível internamente
- Proxy resolve CORS e permite comunicação client-side ↔ backend

**Funcionamento:**
```
Frontend → /api/lia/api/v1/chat → Proxy → http://localhost:8000/api/v1/chat
```

#### 3. **Chat Page Integration** (`src/components/pages/chat-page.tsx`)
Página de chat integrada com backend real.

**Mudanças principais:**
- ✅ Import `liaApi` service
- ✅ `handleSendMessage()` agora é async e chama API real
- ✅ Thinking indicator enquanto aguarda resposta
- ✅ Exibe metadata (intent, entities, workflow_data)
- ✅ Auto-detecta resultados Pearch AI e exibe no painel lateral
- ✅ Error handling robusto

**Fluxo:**
1. Usuário digita mensagem
2. Mensagem enviada via `liaApi.sendMessage()`
3. Thinking indicator exibido
4. Backend processa (LIA Agent + Pearch AI se necessário)
5. Resposta exibida no chat
6. Se houver candidatos, painel lateral abre automaticamente

---

## 🔧 Configuração

### Variáveis de Ambiente

**Backend (.env ou Replit Secrets):**
```bash
ANTHROPIC_API_KEY=sk-ant-...       # Claude API (LIA brain)
PEARCH_API_KEY=pk_...              # Pearch AI (candidate search)
DATABASE_URL=postgresql://...      # PostgreSQL (Replit managed)
```

**Frontend (Next.js - não requer env vars públicas):**
- Proxy usa `http://localhost:8000` internamente
- Nenhuma env var pública necessária

---

## 🚀 Como Testar

### 1. Health Check Backend
```bash
curl http://localhost:8000/health
```

**Esperado:**
```json
{
  "status": "healthy",
  "app": "lia-agent-system",
  "environment": "development"
}
```

### 2. Health Check via Proxy
```bash
curl http://localhost:5000/api/lia/health
```

### 3. Teste Chat Direto (Backend)
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá LIA!", "user_id": "test-user"}'
```

### 4. Teste Chat via Proxy (Frontend)
```bash
curl -X POST http://localhost:5000/api/lia/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Preciso de desenvolvedores Python", "user_id": "demo-user"}'
```

### 5. Teste Frontend Visual
1. Abrir: `http://localhost:5000/chat`
2. Digitar: "Preciso de desenvolvedores Python sênior em São Paulo"
3. Aguardar resposta (LIA detecta intent `search_candidates`)
4. Candidatos aparecerão no painel lateral automaticamente

---

## 📊 Response Format

### Chat Response
```typescript
{
  response: string                    // Resposta conversacional da LIA
  conversation_id: string             // ID da conversa
  metadata: {
    intent?: string                   // create_job, search_candidates, etc
    entities?: {                      // Entidades extraídas
      job_title?: string
      seniority?: string
      skills?: string[]
      location?: string
    }
    confidence?: number               // Confiança da classificação
    workflow_data?: {
      search_results?: {              // Se busca de candidatos
        query: string
        total_found: number
        candidates: CandidateProfile[]
      }
    }
  }
}
```

### Candidate Search Response
```typescript
{
  query: string
  total_results: number
  candidates: [
    {
      id: string | null
      name: string | null
      headline: string                // "Senior Python Engineer @ Company"
      current_title: string
      current_company: string
      location: string
      contact: {
        email?: string
        linkedin_url?: string
      }
      skills: string[]
      summary: string
      match_score: number | null
    }
  ]
  search_time_seconds: number
}
```

---

## 🎯 Funcionalidades Integradas

### ✅ Chat Conversacional
- Envio/recebimento de mensagens em tempo real
- Thinking indicators (processando IA)
- Histórico de conversas persistido
- Metadata display (intent, entities)

### ✅ Busca de Candidatos (Pearch AI)
- Detecção automática de intenção de busca
- Query natural ("desenvolvedores Python sênior SP")
- Integração com painel lateral (auto-abre com resultados)
- Exibição de candidatos com headline, location, skills

### ✅ Error Handling
- Timeout handling
- Backend offline fallback
- Mensagens de erro amigáveis
- Retry logic (futuro)

---

## 🔍 Debug & Troubleshooting

### Frontend não conecta ao backend
**Sintoma:** Erro "Failed to connect to LIA backend"

**Soluções:**
1. Verificar se backend está rodando: `curl http://localhost:8000/health`
2. Reiniciar workflow backend: `lia-backend`
3. Checar logs: `/tmp/logs/lia-backend_*.log`

### Proxy retorna 500
**Sintoma:** `POST /api/lia/api/v1/chat` retorna 500

**Soluções:**
1. Verificar logs Next.js: `/tmp/logs/dev-server_*.log`
2. Confirmar BACKEND_URL no proxy route.ts
3. Testar backend diretamente (sem proxy)

### Candidates não aparecem no painel
**Sintoma:** LIA responde mas painel lateral não abre

**Causas:**
- Backend não retornou `metadata.workflow_data.search_results`
- Intent não foi detectado como `search_candidates`
- Erro no parsing de candidates

**Debug:**
```typescript
console.log('Chat response:', response)
console.log('Metadata:', response.metadata)
console.log('Workflow data:', response.metadata?.workflow_data)
```

---

## 📝 Próximos Passos

### Melhorias Planejadas

1. **WebSockets / Server-Sent Events**
   - Stream de respostas em tempo real
   - Progress indicators dinâmicos
   - Typing indicators

2. **Conversation Persistence**
   - Salvar conversas no banco (PostgreSQL)
   - Lista de conversas anteriores
   - Retomar conversas

3. **Rich Messages**
   - Cards interativos
   - Botões de ação (agendar, ver mais)
   - File uploads (CVs, JDs)

4. **Authentication**
   - User authentication real
   - Multi-tenant support
   - Permissões por role

5. **Analytics**
   - Track user interactions
   - LIA performance metrics
   - A/B testing intents

---

## 🎨 UI Features

### Thinking Indicators
- ⏳ "Processando sua solicitação com IA..."
- 🔍 Animated loading state
- Substituído por resposta real quando completa

### Context Panel
- Auto-abre quando candidates são encontrados
- Exibe query, total found, top candidates
- Headline, location, skills, match score
- Scroll infinito (futuro)

### Message Types
- `text` - Mensagem normal
- `thinking` - Processando IA
- `action` - Com botões de ação
- `structured` - Dados estruturados
- `system` - Mensagens de sistema
- `error` - Mensagens de erro

---

## 🔐 Security

### API Proxy Security
- ✅ Requests limitados a métodos permitidos (GET, POST, PUT, DELETE, PATCH)
- ✅ Headers sanitizados
- ✅ Error messages não vazam stack traces
- ⚠️ TODO: Rate limiting
- ⚠️ TODO: Authentication/authorization

### Secret Management
- ✅ API keys em Replit Secrets (encrypted at rest)
- ✅ Não expostas no frontend
- ✅ Proxy não loga secrets
- ✅ HTTPS em produção (Replit deploy)

---

## 📚 Referências

- [Next.js API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Pearch AI Integration](./lia-agent-system/PEARCH_INTEGRATION.md)
- [LIA Backend Status](./lia-agent-system/README.md)

---

**Última atualização:** 24/11/2025  
**Status:** ✅ Funcional (frontend ↔ backend)  
**Testado:** Chat conversacional + Pearch AI integration  
**Pendente:** WebSockets, authentication, conversation history UI
