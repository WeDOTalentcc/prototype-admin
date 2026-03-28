# 🔗 Frontend Integration Guide

Como conectar o frontend Next.js (`plataforma-lia/`) ao backend LIA Agent System.

---

## 📋 Overview

O frontend Next.js existente precisa se conectar ao backend Python/FastAPI via:
- **REST API** para operações síncronas
- **WebSocket** para chat em tempo real

---

## 🚀 Quick Setup

### 1. Instalar Cliente WebSocket no Frontend

```bash
cd plataforma-lia
npm install socket.io-client
```

### 2. Criar Serviço de Chat

Crie `plataforma-lia/src/services/lia-chat.ts`:

```typescript
// src/services/lia-chat.ts
interface Message {
  id: string;
  role: 'human' | 'ai';
  content: string;
  created_at: string;
  metadata?: {
    intent?: string;
    confidence?: number;
  };
}

interface Conversation {
  id: string;
  title?: string;
  status: string;
  created_at: string;
}

class LIAChatService {
  private ws: WebSocket | null = null;
  private apiUrl: string;
  private wsUrl: string;
  
  constructor() {
    // Use variáveis de ambiente ou configure aqui
    this.apiUrl = process.env.NEXT_PUBLIC_LIA_API_URL || 'http://localhost:8000/api/v1';
    this.wsUrl = process.env.NEXT_PUBLIC_LIA_WS_URL || 'ws://localhost:8000/api/v1';
  }
  
  // =============================================
  // REST API METHODS
  // =============================================
  
  async sendMessage(content: string, conversationId?: string): Promise<{
    message: Message;
    conversation: Conversation;
  }> {
    const response = await fetch(`${this.apiUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        conversation_id: conversationId
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  }
  
  async getConversations(userId: string = 'demo-user'): Promise<{
    conversations: Conversation[];
    total: number;
  }> {
    const response = await fetch(
      `${this.apiUrl}/chat/conversations?user_id=${userId}`
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    
    return response.json();
  }
  
  // =============================================
  // WEBSOCKET METHODS
  // =============================================
  
  connectWebSocket(
    userId: string,
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): void {
    this.ws = new WebSocket(`${this.wsUrl}/chat/ws/${userId}`);
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket connected to LIA');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      if (onError) onError(error);
    };
    
    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
    };
  }
  
  sendWebSocketMessage(content: string, conversationId?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }
    
    this.ws.send(JSON.stringify({
      type: 'message',
      content,
      conversation_id: conversationId
    }));
  }
  
  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const liaChatService = new LIAChatService();
export type { Message, Conversation };
```

### 3. Atualizar Componente de Chat

Atualize o componente de chat existente em `plataforma-lia/src/components/pages/chat-page.tsx`:

```typescript
'use client';

import { useState, useEffect, useRef } from 'react';
import { liaChatService, type Message } from '@/services/lia-chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Brain } from 'lucide-react';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Connect WebSocket on mount
  useEffect(() => {
    const userId = 'demo-user'; // TODO: Get from auth
    
    liaChatService.connectWebSocket(
      userId,
      (data) => {
        // Receive message from LIA
        if (data.type === 'message') {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'ai',
            content: data.content,
            created_at: new Date().toISOString(),
            metadata: data.metadata
          }]);
          
          if (data.conversation_id && !conversationId) {
            setConversationId(data.conversation_id);
          }
          
          setIsLoading(false);
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      }
    );
    
    setIsConnected(true);
    
    // Cleanup on unmount
    return () => {
      liaChatService.disconnectWebSocket();
    };
  }, []);
  
  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'human',
      content: input,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      if (isConnected) {
        // Use WebSocket
        liaChatService.sendWebSocketMessage(input, conversationId || undefined);
      } else {
        // Fallback to REST API
        const response = await liaChatService.sendMessage(input, conversationId || undefined);
        
        setMessages(prev => [...prev, response.message]);
        setConversationId(response.conversation.id);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
  };
  
  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b bg-white dark:bg-gray-950">
        <Brain className="w-6 h-6 text-wedo-cyan" />
        <div>
          <h1 className="text-lg font-semibold">LIA Assistant</h1>
          <p className="text-xs text-gray-500">
            {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
          </p>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'human' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                message.role === 'human'
                  ? 'bg-wedo-cyan text-white'
                  : 'bg-white dark:bg-gray-800 border'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              {message.metadata?.intent && (
                <p className="text-xs mt-1 opacity-70">
                  Intent: {message.metadata.intent} ({Math.round((message.metadata.confidence || 0) * 100)}%)
                </p>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border rounded-lg px-4 py-2">
              <p className="text-sm text-gray-500">LIA está digitando...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="p-4 border-t bg-white dark:bg-gray-950">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Digite sua mensagem..."
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={!input.trim() || isLoading}>
            Enviar
          </Button>
        </div>
      </div>
    </div>
  );
}
```

### 4. Configurar Variáveis de Ambiente

Crie `plataforma-lia/.env.local`:

```bash
# Backend URLs
NEXT_PUBLIC_LIA_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_LIA_WS_URL=ws://localhost:8000/api/v1
```

### 5. Atualizar CORS no Backend

Já está configurado! Veja `lia-agent-system/app/main.py`:

```python
# CORS permite localhost:5000 e localhost:3000
CORS_ORIGINS=["http://localhost:5000","http://localhost:3000"]
```

---

## 🧪 Testar Integração

### 1. Iniciar Backend

```bash
cd lia-agent-system
docker-compose up -d postgres redis rabbitmq
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Iniciar Frontend

```bash
cd plataforma-lia
npm run dev
```

### 3. Acessar Chat

Navegue para: http://localhost:5000/chat

---

## 📊 Fluxo de Dados

```
Frontend (Next.js)
    ↓ WebSocket
Backend (FastAPI)
    ↓ LangGraph
LIA Agent (Claude)
    ↓ Response
Backend (FastAPI)
    ↓ WebSocket
Frontend (Next.js)
    ↓ UI Update
```

---

## 🔧 Troubleshooting

### WebSocket não conecta
- ✅ Verifique se o backend está rodando: `curl http://localhost:8000/health`
- ✅ Verifique CORS: Certifique-se de que `http://localhost:5000` está em `CORS_ORIGINS`
- ✅ Verifique o console do navegador para erros

### Mensagens não aparecem
- ✅ Abra Network tab do DevTools
- ✅ Veja se há erros na aba "WS" (WebSocket)
- ✅ Verifique logs do backend: `docker-compose logs -f api`

### API muito lenta
- ✅ Claude pode demorar 2-5 segundos (normal)
- ✅ Adicione loading state na UI
- ✅ Considere usar streaming (feature futura)

---

## 🚀 Próximos Passos

1. **Autenticação**: Integrar com sistema de auth existente
2. **Persistência**: Salvar conversas no localStorage
3. **Streaming**: Implementar streaming de respostas (character-by-character)
4. **Notificações**: Integrar com sistema de notificações existente
5. **Mobile**: Otimizar para mobile

---

**Pronto! Frontend e Backend integrados! 🎉**
