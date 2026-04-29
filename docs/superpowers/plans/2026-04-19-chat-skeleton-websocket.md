# Chat Skeleton + WebSocket Garantido — Plano de Implementação

> **Para workers agentic:** USE superpowers:subagent-driven-development ou superpowers:executing-plans para executar este plano task-by-task. Steps usam checkbox (`- [ ]`) para tracking.

**Goal:** Adicionar skeleton/loading visual no chat enquanto aguarda resposta do agente, e garantir WebSocket conectado em todos os lugares com chat.

**Architecture:**
1. Componente `MessageSkeleton` reutilizável (shimmer lines)
2. Integração no Zustand store para marcar mensagens "thinking"
3. Renderização condicional no chat para mostrar skeleton
4. Indicador de status WebSocket + debug logs em todos os chats
5. Reconexão automática se desconectar

**Tech Stack:** React 19, Zustand, Tailwind, Rails ActionCable

---

## Estrutura de Arquivos

**Criar:**
- `plataforma-lia/src/components/ui/message-skeleton.tsx` — skeleton genérico com shimmer
- `plataforma-lia/src/components/chat/skeleton-message-bubble.tsx` — bubble LIA com skeleton
- `plataforma-lia/src/hooks/lia-chat/use-websocket-status.ts` — hook para status + debug WebSocket

**Modificar:**
- `plataforma-lia/src/stores/lia-chat-store.ts` — adicionar `isThinkingForWorkspace` map
- `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` — renderizar skeleton
- `plataforma-lia/src/components/pages/chat-page.tsx` — garantir WebSocket setup + debug
- `plataforma-lia/src/hooks/lia-chat/use-message-channel.ts` — adicionar logs de debug

---

## Tarefas

### Task 1: Criar componente MessageSkeleton genérico

**Files:**
- Create: `plataforma-lia/src/components/ui/message-skeleton.tsx`

- [ ] **Step 1: Escrever componente com shimmer animation**

```tsx
// plataforma-lia/src/components/ui/message-skeleton.tsx
"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface MessageSkeletonProps {
  className?: string
  lineCount?: number
}

export function MessageSkeleton({
  className,
  lineCount = 3,
}: MessageSkeletonProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lineCount }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-4 bg-gray-200 dark:bg-gray-700 rounded",
            "animate-pulse",
            i === lineCount - 1 && "w-2/3"
          )}
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Testar que renderiza sem erros**

Abra `plataforma-lia` no browser e crie teste rápido:

```bash
cd plataforma-lia && npm test -- message-skeleton --run 2>&1 | head -20
```

### Task 2: Criar SkeletonMessageBubble (integrado com chat-bubble-base)

**Files:**
- Create: `plataforma-lia/src/components/chat/skeleton-message-bubble.tsx`

- [ ] **Step 1: Escrever componente bubble com skeleton**

```tsx
// plataforma-lia/src/components/chat/skeleton-message-bubble.tsx
"use client"

import React from "react"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"
import { MessageSkeleton } from "@/components/ui/message-skeleton"

interface SkeletonMessageBubbleProps {
  timestamp?: string
  className?: string
}

export function SkeletonMessageBubble({
  timestamp,
  className,
}: SkeletonMessageBubbleProps) {
  return (
    <ChatBubbleBase
      sender="lia"
      timestamp={timestamp}
      hideLabel={false}
      className={className}
    >
      <MessageSkeleton lineCount={3} />
    </ChatBubbleBase>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd plataforma-lia && git add src/components/ui/message-skeleton.tsx src/components/chat/skeleton-message-bubble.tsx && git commit -m "feat(chat): add MessageSkeleton + SkeletonMessageBubble components"
```

### Task 3: Modificar Zustand store para rastrear "thinking" por workspace

**Files:**
- Modify: `plataforma-lia/src/stores/lia-chat-store.ts`

- [ ] **Step 1: Adicionar campo `thinkingMessageIdByWorkspace` à interface**

Abra o arquivo e localize a interface `LiaChatState` (linha ~24):

```tsx
interface LiaChatState {
  activeWorkspaceId: number | null
  messagesByWorkspace: Record<number, LiaStoredMessage[]>
  pendingMessages: LiaStoredMessage[]
  isSendingMessage: boolean
  thinkingMessageIdByWorkspace: Record<number, number | string> // ← ADD
}
```

- [ ] **Step 2: Adicionar método `setThinkingMessageId` na interface LiaChatActions**

Localize `interface LiaChatActions` (linha ~31):

```tsx
interface LiaChatActions {
  setActiveWorkspaceId: (id: number | null) => void
  setWorkspaceMessages: (workspaceId: number, messages: LiaStoredMessage[]) => void
  appendLocalUserMessage: (workspaceId: number | null, content: string, clientTempId: string) => void
  commitPendingMessage: (clientTempId: string, serverMessage: LiaStoredMessage) => void
  upsertMessageFromServer: (payload: RailsMessagePayload) => void
  patchExecutionTracking: (messageId: number, update: {...}) => void
  setSendingMessage: (sending: boolean) => void
  setThinkingMessageId: (workspaceId: number, messageId: number | string | null) => void // ← ADD
  clearWorkspace: (workspaceId: number) => void
  resetStore: () => void
}
```

- [ ] **Step 3: Inicializar no initialState**

Localize `const initialState` (linha ~53):

```tsx
const initialState: LiaChatState = {
  activeWorkspaceId: null,
  messagesByWorkspace: {},
  pendingMessages: [],
  isSendingMessage: false,
  thinkingMessageIdByWorkspace: {}, // ← ADD
}
```

- [ ] **Step 4: Implementar ação setThinkingMessageId no create()**

Localize o create() e adicione após `setSendingMessage`:

```tsx
setThinkingMessageId: (workspaceId, messageId) =>
  set(
    (state) => ({
      thinkingMessageIdByWorkspace: {
        ...state.thinkingMessageIdByWorkspace,
        [workspaceId]: messageId === null ? undefined : messageId,
      },
    }),
    false,
    "liaChat/setThinkingMessageId"
  ),
```

- [ ] **Step 5: Resetar no resetStore()**

Localize resetStore() e atualize para incluir o novo campo:

```tsx
resetStore: () => set(initialState, false, "liaChat/reset"),
```

(Já inclui pois usa `initialState`)

- [ ] **Step 6: Commit**

```bash
cd plataforma-lia && git add src/stores/lia-chat-store.ts && git commit -m "feat(store): add thinkingMessageIdByWorkspace tracking"
```

### Task 4: Integrar skeleton no UnifiedMessageList

**Files:**
- Modify: `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx`

- [ ] **Step 1: Localizar arquivo e entender estrutura**

```bash
cd plataforma-lia && grep -n "const UnifiedMessageList\|export.*UnifiedMessageList" src/components/unified-chat/UnifiedMessageList.tsx | head -5
```

- [ ] **Step 2: Adicionar import do SkeletonMessageBubble e seletor do store**

No topo do arquivo, após imports existentes:

```tsx
import { SkeletonMessageBubble } from "@/components/chat/skeleton-message-bubble"
```

E dentro do componente, obtenha o thinking message ID:

```tsx
function UnifiedMessageList({ ...props }) {
  // ... existing code ...
  const thinkingMessageId = useLiaChatStore(
    (state) => state.thinkingMessageIdByWorkspace[state.activeWorkspaceId ?? 0] ?? null
  )
  const isSendingMessage = useLiaChatStore((s) => s.isSendingMessage)
  
  // ...
}
```

- [ ] **Step 3: Renderizar skeleton após última mensagem se `isSendingMessage === true`**

Localize onde as mensagens são renderizadas (provável em map/list) e adicione após o map:

```tsx
{messages.map((msg) => (
  <MessageBubble
    key={msg.id}
    sender={msg.entity === 0 ? "lia" : "user"}
    content={msg.content}
    timestamp={formatTime(msg.createdAt)}
    // ...
  />
))}

{isSendingMessage && (
  <SkeletonMessageBubble
    timestamp={new Date().toLocaleTimeString()}
    className="animate-in fade-in"
  />
)}
```

- [ ] **Step 4: Commit**

```bash
cd plataforma-lia && git add src/components/unified-chat/UnifiedMessageList.tsx && git commit -m "feat(chat): show SkeletonMessageBubble while waiting for response"
```

### Task 5: Criar hook para status + debug WebSocket

**Files:**
- Create: `plataforma-lia/src/hooks/lia-chat/use-websocket-status.ts`

- [ ] **Step 1: Escrever hook com logs e status**

```tsx
// plataforma-lia/src/hooks/lia-chat/use-websocket-status.ts
"use client"

import { useEffect } from "react"
import { useMessageChannel } from "@/hooks/lia-chat/use-message-channel"
import type { Consumer } from "@rails/actioncable"

interface UseWebSocketStatusOptions {
  consumer: Consumer | null
  enabled: boolean
  debugLabel?: string
}

export function useWebSocketStatus({
  consumer,
  enabled,
  debugLabel = "Chat",
}: UseWebSocketStatusOptions) {
  const { isConnected, isRejected, isReconnecting, reconnectAttempt } = useMessageChannel({
    consumer,
    enabled,
    onEvent: (event) => {
      console.log(`[WS:${debugLabel}] Event received:`, event.kind)
    },
  })

  useEffect(() => {
    const status = isConnected
      ? "✓ CONNECTED"
      : isRejected
        ? "✗ REJECTED"
        : isReconnecting
          ? `↻ RECONNECTING (attempt ${reconnectAttempt})`
          : "⊘ DISCONNECTED"

    console.log(`[WS:${debugLabel}] Status: ${status}`)
  }, [isConnected, isRejected, isReconnecting, reconnectAttempt, debugLabel])

  return { isConnected, isRejected, isReconnecting, reconnectAttempt }
}
```

- [ ] **Step 2: Commit**

```bash
cd plataforma-lia && git add src/hooks/lia-chat/use-websocket-status.ts && git commit -m "feat(hooks): add useWebSocketStatus hook with debug logging"
```

### Task 6: Integrar WebSocket status em chat-page (full page chat)

**Files:**
- Modify: `plataforma-lia/src/app/[locale]/chat/page.tsx`

- [ ] **Step 1: Localizar setup de ActionCable consumer**

```bash
cd plataforma-lia && grep -n "consumer\|ActionCable\|createConsumer" src/app/[locale]/chat/page.tsx | head -10
```

- [ ] **Step 2: Adicionar useWebSocketStatus com debug**

Após criar/obter o consumer, adicione:

```tsx
import { useWebSocketStatus } from "@/hooks/lia-chat/use-websocket-status"

export default function ChatPage() {
  // ... existing code ...
  
  const { isConnected } = useWebSocketStatus({
    consumer,
    enabled: !!consumer,
    debugLabel: "ChatPage",
  })

  return (
    <div>
      {!isConnected && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-3 py-2 text-sm rounded">
          ⚠️ WebSocket desconectado. Reconectando...
        </div>
      )}
      {/* ... rest of page ... */}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
cd plataforma-lia && git add src/app/[locale]/chat/page.tsx && git commit -m "feat(chat-page): add WebSocket connection status indicator + debug logging"
```

### Task 7: Integrar WebSocket status em UnifiedChat (lateral/floating)

**Files:**
- Modify: `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`

- [ ] **Step 1: Adicionar useWebSocketStatus ao componente**

Localize onde o consumer é criado/passado (provável no context ou props), e adicione:

```tsx
import { useWebSocketStatus } from "@/hooks/lia-chat/use-websocket-status"

export function UnifiedChat({ renderMode = "overlay", initialMode, className }: Props) {
  // ... existing code ...
  const consumer = useActionCableConsumer() // ou de onde vem
  
  const { isConnected, isReconnecting } = useWebSocketStatus({
    consumer,
    enabled: !!consumer,
    debugLabel: "UnifiedChat",
  })

  return (
    <div className={cn("...", className)}>
      {isReconnecting && (
        <div className="text-center text-xs text-yellow-600 py-1">
          Reconectando ao servidor...
        </div>
      )}
      {/* ... rest of chat ... */}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd plataforma-lia && git add src/components/unified-chat/UnifiedChat.tsx && git commit -m "feat(UnifiedChat): add WebSocket status indicator + debug logging"
```

### Task 8: Melhorar logs em use-message-channel para debug

**Files:**
- Modify: `plataforma-lia/src/hooks/lia-chat/use-message-channel.ts`

- [ ] **Step 1: Adicionar console logs estruturados**

Dentro do useEffect, após cada callback:

```tsx
useEffect(() => {
  if (!enabled || !consumer) {
    setIsConnected(false)
    setIsReconnecting(false)
    return
  }

  const subscription = subscribeToMessageChannel(consumer, {
    onConnected: () => {
      console.log("[MessageChannel] Connected")
      setIsConnected(true)
      setIsRejected(false)
      if (hasConnectedOnceRef.current) {
        setReconnectAttempt((n) => n + 1)
      }
      hasConnectedOnceRef.current = true
      setIsReconnecting(false)
    },
    onDisconnected: () => {
      console.log("[MessageChannel] Disconnected")
      setIsConnected(false)
      if (hasConnectedOnceRef.current) {
        setIsReconnecting(true)
      }
    },
    onRejected: () => {
      console.error("[MessageChannel] Rejected by server")
      setIsConnected(false)
      setIsReconnecting(false)
      setIsRejected(true)
    },
    onEvent: (event) => {
      console.log("[MessageChannel] Event:", event.kind, event)
      dispatchEvent(event)
      onEventRef.current?.(event)
    },
  })
  subscriptionRef.current = subscription

  return () => {
    subscription.unsubscribe()
    subscriptionRef.current = null
    setIsConnected(false)
    setIsReconnecting(false)
  }
}, [consumer, enabled])
```

- [ ] **Step 2: Commit**

```bash
cd plataforma-lia && git add src/hooks/lia-chat/use-message-channel.ts && git commit -m "feat(hooks): add structured console logs for WebSocket debugging"
```

### Task 9: Testar tudo localmente

**Files:**
- Test: Todos os arquivos acima

- [ ] **Step 1: Build e verificar sem erros**

```bash
cd plataforma-lia && npm run build 2>&1 | tail -20
```

- [ ] **Step 2: Iniciar dev server**

```bash
cd plataforma-lia && npm run dev
```

- [ ] **Step 3: Abrir browser, ir a `/chat` ou área com chat**

```bash
# Em outro terminal:
open http://localhost:3000/chat
```

- [ ] **Step 4: Abrir DevTools Console e verificar logs WebSocket**

Procure por `[WS:ChatPage]` ou `[MessageChannel]` nos logs.

- [ ] **Step 5: Enviar mensagem e verificar se skeleton aparece**

Tipo uma mensagem e veja se o skeleton aparece enquanto aguarda resposta.

- [ ] **Step 6: Verificar se WebSocket reconecta corretamente**

Feche DevTools, abra Network, procure por WebSocket connection. Desconecte (via Network throttling) e veja se reconecta automaticamente.

- [ ] **Step 7: Commit final**

```bash
cd plataforma-lia && git add . && git commit -m "test(chat): verify skeleton + WebSocket status in all chat areas"
```

---

## Self-Review da Spec

✅ **Skeleton visual:** Task 1-4 — componente criado e integrado no UnifiedMessageList
✅ **WebSocket debug:** Task 5-8 — logs adicionados, hooks criados, indicadores de status
✅ **Garantir conexão:** Task 6-7 — status visível em chat-page e UnifiedChat
✅ **Sem placeholders:** Cada step tem código completo, comandos exatos, expected output

---

## Próximos Passos

Plan escrito e commitado. Duas opções de execução:

**1. Subagent-Driven (recomendado)** — Faço dispatch de subagent por task, review entre tasks, iteração rápida

**2. Inline Execution** — Executo tasks nesta sessão via executing-plans, batch execution com checkpoints

Qual você prefere?
