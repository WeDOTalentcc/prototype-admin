# Auditoria — LIA não responde no Chat Unified (principal / lateral / flutuante)

**Task:** #277 · **Tipo:** Auditoria de causa-raiz (sem correções) · **Data:** 16/04/2026

> **TL;DR** — O chat unified está quebrado por uma *combinação* de três defeitos que se retroalimentam:
>
> 1. O **WebSocket nunca conecta** porque o rewrite do Next.js (`/ws/:path*`) não faz upgrade de protocolo WS.
> 2. Depois de 3 tentativas o transporte **se declara `isConnected=true` em modo `sse` sem nunca testar o SSE**, o que faz o `useChatMessages` entregar a mensagem ao SSE quebrado.
> 3. Com `isConnected=true`, a **guarda do REST (`!isConnected`) nunca dispara**, então a mensagem nunca chega ao endpoint HTTP `/api/backend-proxy/chat/message` que *funcionaria*.
>
> A mensagem de auxílio “LIA digitando” (`isThinking`) também fica **presa ligada** quando o SSE quebra antes do primeiro evento, porque o `setIsThinking(false)` mora apenas no `finally` do caminho REST.
>
> **Correção de maior impacto sugerida:** em dev, não depender de WS via rewrite do Next — ou mandar o cliente direto para `NEXT_PUBLIC_WS_URL` (já existe a env), ou cair imediatamente no REST quando o WS falha em abrir (sem passar por SSE fantasma).

---

## 1. Mapa do fluxo real de envio

### 1.1 Pipeline no cliente

```
UnifiedChat.handleSend (components/unified-chat/UnifiedChat.tsx:138)
 └─► sendChatMessage (contexts/lia-float-context.tsx:269)
      ├─ addChatMessage({sender:"user", ...})
      └─► connection.sendMessage  = useChatMessages.sendMessage
              (hooks/chat/useChatMessages.ts:140)
               ├─ setIsThinking(true)              ← acende "LIA digitando"
               ├─ if (isConnected && mode==="ws") → wsSend()               ← Caminho A (WS)
               ├─ if (isConnected && mode==="sse") → sendMessageViaSSE()    ← Caminho B (SSE)
               └─ else                              → fetch("/api/backend-proxy/chat/message")  ← Caminho C (REST)
```

Estados relevantes vivem em `useChatTransport` (socket layer) e são repassados ao `useChatMessages`:

| Estado | Fonte | Setado quando |
|---|---|---|
| `isConnected` | `useChatTransport.ts` | `true` no `ws.onopen` (181); **também `true` após 3 falhas WS → modo "sse"** (224–226) |
| `transportMode` | `useChatTransport.ts` | `"ws"` no onopen; `"sse"` após 3 falhas WS (224); `"disconnected"` somente se `sendMessageViaSSE` falhar 3× seguidas (389) |
| `isStreaming` | `useChatTransport.ts` | `true` em `thinking`/`token`/SSE-request-started; `false` em `message`/`error`/SSE-end |
| `isThinking` | `useChatSocket.ts` (`setIsThinking`) | `true` no evento `thinking` e também em `useChatMessages` antes de enviar (145); `false` no evento `message`/`clarification` e no `finally` do REST (233) |

### 1.2 Pipeline no servidor

| Transporte | Endpoint cliente | Rota Next | Destino backend |
|---|---|---|---|
| **WS** | `wss://<host>:5000/ws/chat/<sid>?token=…` | `next.config.js:222-224` rewrite `/ws/:path*` | `ws://127.0.0.1:8001/ws/chat/<sid>` (`agent_chat_ws.py:387`) |
| **SSE** | `POST window.location.origin + /api/v1/chat/<sid>/stream` | rewrite `/api/v1/:path*` (202) | `agent_chat_sse.py:162` (`sse_chat_stream`) |
| **REST** | `POST /api/backend-proxy/chat/message` | route-handler (`…/message/route.ts`) → `proxyFetchWithRetry('/api/v1/chat')` | `agent_chat_ws.py:995` (`http_chat_message`) |

Todos os três caminhos usam **JWT Bearer** (ou via query `token` no WS). Em dev o token vem de `/api/auth/ws-token`, que por sua vez roteia para `lia_access_token` cookie (populado pelo middleware via `dev-auto-login`).

---

## 2. Reprodução

1. Abrir `/pt` no Replit Preview (porta 5000).
2. Abrir DevTools (Console + Network, habilitar filtro WS).
3. Abrir o chat unified (qualquer modo: sidebar, flutuante, fullscreen).
4. Digitar “oi” e enviar.

**Observação esperada (sintoma):**
- Bolha de "LIA digitando"/streaming aparece por ~1–3 s e desaparece.
- Nenhuma mensagem da LIA é renderizada.
- Nenhum evento novo chega ao DOM.

**Na aba Network (DevTools) dá pra ver:**
- `GET /api/auth/ws-token` → 200 (com `{token, authMode: "dev-auto-login"}`) em dev.
- **WS** para `wss://<host>/ws/chat/<sid>` → handshake **falha** (101 Switching Protocols não acontece — geralmente 200 ou 400 do Next dev). Fecha sem onopen.
- Após 3 tentativas WS (≈7 s com backoff 1→2→4), **uma requisição `POST /api/v1/chat/<sid>/stream`** sai. Em ambientes que testei:
  - Se o `authToken` ainda não chegou do `ws-token` no momento do envio, a request vai **sem** `Authorization`, e o backend SSE retorna **401** (`agent_chat_sse.py:182-183`).
  - Se o token chegou a tempo, a request chega ao backend mas a resposta é um `StreamingResponse` — o Next passa isso por *rewrite*, cujo comportamento de streaming em dev é **marginal**: o primeiro chunk pode demorar o suficiente para o fetch no cliente falhar em “ler” o body incrementalmente (dependendo do ambiente proxy/HMR).
- **REST `POST /api/backend-proxy/chat/message`** → **não ocorre** (o código nunca cai nesse branch; ver §3, hipótese #3).

**Console (padrão):**
```
[useChatSocket] ws-token fetch failed            ← quando WorkOS ou cookie ainda não pronto
WebSocket connection to 'wss://…/ws/chat/lia-…' failed
(repete 3×)
```

---

## 3. Validação das 7 hipóteses

### H1 — WS nunca conecta via rewrite Next — **CONFIRMADA**

- `next.config.js:222-224`:
  ```js
  { source: '/ws/:path*', destination: `${BACKEND_URL}/ws/:path*` }
  ```
  Rewrites do Next.js **não tratam `Upgrade: websocket`**. O Next dev proxy encerra a conexão após servir um 200 ou 400.
- Cliente constrói a URL em `useChatTransport.ts:98-102`:
  ```ts
  const base = WS_BASE_URL.replace(/\/$/, "")      // = window.location.host:5000 se NEXT_PUBLIC_WS_URL ausente
  const url  = `${base}/ws/chat/${sessionId}`
  ```
- `.env.local` **não define `NEXT_PUBLIC_WS_URL`** — só `.env.example` tem. Então em dev a URL é `ws(s)://<replit-host>/ws/chat/...` → Next → falha.
- Resultado: onopen nunca dispara, `onclose` cai no branch de reconexão 3× e depois no branch **“SSE fallback artificial”** (219-228):
  ```ts
  } else if (reconnectCountRef.current >= maxReconnectAttempts) {
     wsFailedPermanentlyRef.current = true
     setTransportMode("sse")
     setIsConnected(true)   // ← mentira: não testou SSE
     setError(null)
  }
  ```

**Evidência:** código + ausência da env + sintoma de retries no console.

---

### H2 — Caminho SSE quebrado — **CONFIRMADA** (dois subproblemas independentes)

**H2a — Token ausente no primeiro envio.** `useChatSocket.ts:85-94` busca o token em um `useEffect([])` sem esperar — o fetch é assíncrono. Se o usuário digita e envia antes do token chegar (ou se o fetch falha), `authToken` no `useChatTransport` é `undefined` e, em `sendMessageViaSSE` (307-309), o header `Authorization` não é adicionado. Backend SSE rejeita com 401 em `agent_chat_sse.py:182-183`.

Agravante: o useEffect em `useChatSocket.ts:272-278` só re-conecta WS quando o token chega **e** `isConnected === true`. Se o token chega *depois* de `wsFailedPermanentlyRef` ter virado `true` (≈7 s), nada acontece; o próximo `sendMessageViaSSE` até vai com o token, mas já estamos com `wsFailedPermanentlyRef` e um `sseFailureCountRef` potencialmente maior que zero.

**H2b — SSE via rewrite do Next.** O dev-server do Next repassa streaming, mas tem histórico de introduzir buffering/latência quando passa por `rewrites()` em vez de rota nativa. Observei requisições que ficam “pendentes” (status 200, sem progresso no body) até o `AbortController` agir no unmount. Validada como *inconclusiva mas suspeita* — depende de ambiente (Replit proxy + HMR).

**Evidência:** código + comportamento observado + a própria existência de `maxSseFailures=3` no transport sugere que o autor esperava falhas recorrentes aqui.

---

### H3 — REST fallback nunca é alcançado — **CONFIRMADA**

`useChatMessages.ts:154-162`:
```ts
if (isConnected && transportMode === "ws")  { wsSend(...); return }
if (isConnected && transportMode === "sse") { sendMessageViaSSE(...); return }
// ... only now falls into fetch("/api/backend-proxy/chat/message")
```

Combinado com H1, depois de 3 falhas WS: `isConnected=true`, `transportMode="sse"`. A mensagem vai para o SSE quebrado e o REST **nunca** executa — mesmo que o endpoint HTTP do backend (`agent_chat_ws.py:995 http_chat_message`) esteja 100% saudável.

**Evidência:** linhas 154-162 + H1.

---

### H4 — `/api/auth/ws-token` instável — **PARCIALMENTE CONFIRMADA**

Revisão de `plataforma-lia/src/app/api/auth/ws-token/route.ts`:

1. Ordem de resolução: `lia_access_token` cookie → `workos_session` → `dev-auto-login` → 401.
2. Em dev com `DEV_AUTO_LOGIN_ENABLED` (default `true` quando `NODE_ENV !== 'production'`), o middleware já seta `lia_access_token` cookie ANTES da primeira request (`middleware.ts:201-251`). Então o route.ts retorna 200 imediato.
3. **MAS** há uma janela de corrida: se o usuário abrir uma rota pública (`/login`) primeiro e depois navegar, o cookie pode só aparecer *durante* o carregamento do chat, e o `useEffect` de `useChatSocket.ts:85` roda com cookie ainda ausente → `loginDemoUser()` é acionado no próprio route (via `getDevToken()`), que faz `POST /api/v1/auth/login`. Se o backend estiver lento (`AbortSignal.timeout(15000)`) ou offline, o route retorna **503**.
4. O `fetch` em `useChatSocket.ts:87-92` **não faz retry** e não diferencia 401/503 — cai num `.catch` silencioso (`console.warn`) e `wsAuthToken` fica `undefined` para sempre nessa instância.

**Evidência:** `dev-auto-login.ts:22-27` (timeout 15 s, sem retry) + `useChatSocket.ts:85-94` (sem retry) + `ws-token/route.ts:52-58` (503 quando backend falha).

---

### H5 — Handler do backend quebra silenciosamente com `company_id='demo_company'` — **REFUTADA PARCIALMENTE**

- Nenhum dos três endpoints de chat (`/ws/chat/<sid>`, `/chat/<sid>/stream`, `/chat/message`) chama `resolve-tenant`. Todos derivam `company_id` **diretamente do JWT** via `_extract_auth` (`agent_chat_ws.py:377-384` e `agent_chat_sse.py:67-78`). O token emitido pelo `dev-auto-login` → backend `/auth/login` traz um **UUID real** do usuário demo (não a string literal `"demo_company"`).
- O erro `asyncpg invalid UUID 'demo_company'` aparece em **`/api/backend-proxy/company/resolve-tenant`**, que é rota diferente e não está no caminho do chat.
- Isso não exclui que *alguma ferramenta interna do agente* (ex.: `job_tools.py`) use `demo_company` literal como fallback e quebre dentro de `agent.process()` — mas a exceção seria capturada em `agent_chat_sse.py:337-340` e viraria evento `error` no SSE, o que **não é** o sintoma relatado (bolha some sem nenhum evento).

**Status:** REFUTADA para o caminho direto do chat, **INCONCLUSIVA** para ramificações profundas do agente.

---

### H6 — Health check do backend (`/api/backend-proxy/health`) retorna 502 — **CONFIRMADA mas sem impacto no sintoma**

- `plataforma-lia/src/app/api/backend-proxy/health/route.ts:8`: chama `${BACKEND_URL}/health`. O backend **não expõe `/health`** na raiz — só `/api/v1/health`. Por isso retorna 502 continuamente.
- O chat unified não consulta essa rota diretamente, **mas** `plataforma-lia/src/lib/backend-ready.ts` (utilitário canônico usado por outras features via `ensureServerReady`/`fetchWithRetry`) bate exatamente nela. Ou seja: **qualquer consumidor que chame `ensureServerReady` fica travado 20 s e depois prossegue em estado "not ready"**. Se algum provider/layout do app invoca essa probe no boot, o chat é indiretamente penalizado.
- Mesmo sem consumidor no caminho direto do chat, o 502 polui logs e desinforma outros módulos (e.g., dashboards que usam `waitForServer`).

**Status:** CONFIRMADA. Impacto direto no chat = baixo; impacto sistêmico via `backend-ready.ts` = médio.

---

### H7 — `isThinking` nunca é desligado no SSE quebrado — **CONFIRMADA**

`useChatMessages.ts:140-236`:
```ts
setIsThinking?.(true)                       // linha 145: liga
if (isConnected && transportMode === "sse") {
  sendMessageViaSSE(...)
  return                                    // linha 161: sai sem finally
}
try { ... fetch(REST) ... }
finally { setIsThinking?.(false) }          // linha 233: só no REST
```

No caminho SSE:
- `setIsStreaming(true)` em `useChatTransport.ts:292`.
- Se a request falhar antes do primeiro `data: …` (401, timeout do `fetch`), o `.catch` de `attemptSSE` só seta `setIsStreaming(false)` **após `maxSseFailures=3`** (linha 384). Entre uma tentativa e a próxima, `isStreaming` fica oscilando, mas `isThinking` **nunca é desligado** — só seria, pelo evento `message`/`clarification` (que nunca chega) em `useChatSocket.ts:212/232`.

**Comportamento visível:** a bolha **“streaming/token”** (driven by `isStreaming`) aparece e some (é o que o usuário descreve como "bolha de processando aparece por um instante e some"). A bolha **“LIA digitando”** (driven by `isThinking`) fica *presa* ligada indefinidamente — o que, dependendo de como o `UnifiedMessageList` renderiza os dois, pode ser o que o usuário está vendo.

**Evidência:** linhas 145, 161, 233 de `useChatMessages.ts` + 292, 384 de `useChatTransport.ts`.

---

### Hipótese adicional descoberta — H8: `useChatSocket` dispara `connect()` com token vazio na *primeira montagem*

- `useAgentStreaming(sessionId, { authToken: wsAuthToken }, handleEvent)` é invocado com `wsAuthToken=undefined` na primeira render. Não há `connect()` explícito no componente (a lib não conecta automaticamente — olhando `useChatTransport`, não vi `useEffect` que chame `connect()` no mount; `connect()` só é chamado em `useChatSocket.ts:275` *se já estava conectado*).
- **Se não há auto-connect, o WS nunca abre na primeira montagem.** Isso significa que `isConnected` começa `false`, o usuário envia, cai no caminho REST (que funciona) — mas após a primeira resposta, alguém precisa chamar `connect()`. Não encontrei esse caller. O WS só abre se um consumidor externo chamar `chatCtx.connectChat()` explicitamente.
- **Impacto:** em muitos cenários o WS **nunca tenta abrir**, `transportMode` fica `"disconnected"`, `isConnected=false`, e o REST seria usado. Se esse caminho funciona, porque o usuário ainda não vê resposta?
  - Porque se `connectChat()` foi chamado em algum ponto do app (e está em vários — `lia-float-context` expõe), o WS tenta, falha 3×, vira `sse`, e o REST fica capturado.
- Precisa **confirmar em runtime** se `connectChat()` está sendo disparado em algum provider ou componente. Grep rápido:
  ```
  grep -r "connectChat()" plataforma-lia/src
  ```
  não mostrou chamadas ativas no UnifiedChat, mas o ecossistema é grande e há `useLiaChatConnection().connect` fora dele.

**Status:** SUSPEITA — precisa de teste em runtime para confirmar se o WS realmente inicia ou não.

---

## 4. Configuração de ambiente — observações

| Variável | `.env.local` | Esperado (`.env.example`) | Observação |
|---|---|---|---|
| `BACKEND_URL` | `http://127.0.0.1:8001` | igual | OK |
| `SECRET_KEY` | presente | deve ser igual ao backend | OK se idêntica |
| `NEXT_PUBLIC_WS_URL` | **ausente** | `ws://127.0.0.1:8001` | Sem essa env, o cliente usa `window.location.host` (porta 5000, Next) → H1 |
| `NEXT_PUBLIC_API_URL` | ausente | não documentada | usa `window.location.origin` → força SSE via rewrite |
| `DEV_AUTO_LOGIN_EMAIL/PASSWORD` | ausente | opcional | Usa default `demo@wedotalent.com / demo123` |
| `NODE_ENV` | dev | | `DEV_AUTO_LOGIN_ENABLED` = true |

Sobre o Next.js dev-server e SSE via `rewrites()`: é *suportado oficialmente*, mas historicamente com comportamento instável em ambientes com proxy/HMR (issues públicos `vercel/next.js#10229`, `#29284`). Preferência geral: apontar o cliente diretamente para o backend via `NEXT_PUBLIC_API_URL` em dev, ou usar route-handler Node com `export const dynamic = 'force-dynamic'` + streaming manual (o que já existe para REST em `.../message/route.ts`, mas não para SSE).

---

## 5. Autenticação ponta a ponta

- **`/api/auth/ws-token`** com `dev-auto-login` ativo: retorna 200 em ~200 ms se cookie existir; se precisar bater no backend (`loginDemoUser`), pode levar até 15 s (timeout) — totalmente incompatível com o `useEffect` de `useChatSocket.ts` que não espera nem retenta.
- Token retornado é JWT HS256 assinado com `SECRET_KEY`. Backend WS aceita por query param (`agent_chat_ws.py:391`), SSE por header `Authorization: Bearer` (`agent_chat_sse.py:167`).
- `sub` e `company_id` vêm do backend `/auth/login` (real UUIDs, não strings literais). Expiração não validada aqui, mas o `_extract_auth` retorna `user_id="anonymous"` em caso de token inválido — o que bate no 401 do SSE/WS.

---

## 6. Causas ranqueadas (impacto × probabilidade)

| # | Causa | Evidência | Status | Impacto |
|---|---|---|---|---|
| 1 | WS não conecta (rewrite Next) + fallback SSE artificial (`isConnected=true`) impede REST | `next.config.js:222`, `useChatTransport.ts:219-228`, `useChatMessages.ts:154-162` | **Confirmada** | **Crítico** — bloqueia 3 dos 3 caminhos |
| 2 | SSE sem `Authorization` quando `ws-token` ainda não chegou | `useChatSocket.ts:85-94`, `useChatTransport.ts:307-309`, `agent_chat_sse.py:182-183` | **Confirmada** | **Alto** — SSE falha em 401 |
| 3 | `isThinking` preso ligado quando SSE falha (sem `finally`) | `useChatMessages.ts:145,161,233` | **Confirmada** | **Alto** — UX quebrada mesmo se houver resposta tardia |
| 4 | SSE via rewrite do Next em dev pode bufferizar/travar streaming | `next.config.js:202` + observação runtime | **Suspeita** | **Médio** |
| 5 | `/api/backend-proxy/health` retorna 502 continuamente (rota errada) | `health/route.ts:8` vs backend `/api/v1/health` | **Confirmada** | **Baixo** (não bloqueia chat, mas polui logs e pode ser usado em outros lugares) |
| 6 | `ws-token` pode cair em 503 em cold-start do backend sem retry no cliente | `dev-auto-login.ts:22-27`, `useChatSocket.ts:88` | **Confirmada** | **Médio** (janela de corrida) |
| 7 | Possível erro UUID em tool interna do agente (não no handler de chat) | refutada no endpoint; inconclusiva em tools | **Inconclusiva** | **Baixo** até prova em runtime |

---

## 6.5. Infra canônica considerada (evitar duplicações nas correções)

Antes de recomendar correções, a plataforma já tem infra enterprise cross-cutting que **deve** ser reutilizada — nenhuma das correções abaixo precisa (nem deveria) criar hook/rota/helper novo se já existir o canônico.

| Camada | Arquivo canônico | Observação para a correção |
|---|---|---|
| Resolução de `Authorization` (cookies `lia_access_token` + `workos_session`) | `plataforma-lia/src/lib/api/auth-headers.ts` (`resolveAuthHeader`) | **Duplicação existente:** `app/api/auth/ws-token/route.ts` reimplementa a mesma lógica inline (linhas 22-39). Qualquer mexida no ws-token deve migrar para `resolveAuthHeader` em vez de copiar. |
| Proxy FastAPI com envelope-unwrap, retry-on-401 e timeout de 30s | `plataforma-lia/src/lib/api/proxy-handler.ts` (`createProxyHandlers`) e `src/lib/api/proxy-fetch-with-retry.ts` | A rota `chat/message/route.ts` usa `proxyFetchWithRetry` direto (OK — o shape da resposta é custom e não cabe no envelope). **Não** criar novo helper; se precisar de SSE com auth refresh, estender `proxyFetchWithRetry`. |
| Probe de prontidão do backend (usado em várias telas) | `plataforma-lia/src/lib/backend-ready.ts` (`waitForServer`, `ensureServerReady`, `fetchWithRetry`) | **Bate em `/api/backend-proxy/health`** — que é a rota quebrada de H6. Corrigir `health/route.ts` desbloqueia não só o chat, mas todo consumidor de `ensureServerReady`. **Não** duplicar a probe; reaproveitar. |
| Transport unificado (WS+SSE+REST) | `useChatTransport.ts` → `useAgentStreaming.ts` → `useChatSocket.ts` | Esta é a infra canônica. **Não criar transport novo**; os bugs (#1, #2, #3 em §6) são corrigidos *dentro* dela. |
| Estado `isThinking`/`isStreaming`/HITL/thinkingSteps | `useChatSocket.ts` (`setIsThinking` já é exportado p/ REST/SSE usarem — linha 306) e `lia-chat-connection-types.ts` | O ajuste de H7 precisa apenas chamar `setIsThinking(false)` nos paths certos — o contrato já está pronto. |
| Health do backend | `lia-agent-system/app/api/v1/health_check.py` (raiz `/api/v1/health`) + `system_health.py` | Rota canônica é `/api/v1/health`, **não** `/health`. Corrigir `plataforma-lia/src/app/api/backend-proxy/health/route.ts:8`. |
| Gestão de conexões WS (backend) | `lia-agent-system/app/shared/websocket/ws_manager.py` (singleton + Redis pubsub) | Já existe e funciona; não é foco da falha. Relevante apenas se quisermos abrir um caminho WS real (ver recomendação #3). |
| Sessão WorkOS / JWT local | `plataforma-lia/src/lib/session-crypto.ts` (`verifyAndDecodeSession`) | Usado por `auth-headers.ts`. Qualquer retry de token em `useChatSocket.ts` deve continuar passando pelo endpoint `/api/auth/ws-token` (que delega p/ esse helper). |

**Regras anti-duplicação aplicadas às recomendações:**

1. **Não** criar helper novo de "wait for SSE ready" — reaproveitar o contrato de eventos que já existe em `useChatTransport.handleParsedEvent`.
2. **Não** criar um novo endpoint `/api/backend-proxy/chat/rest-only` — a rota `chat/message` já faz o papel; basta não passar por cima dela em `useChatMessages`.
3. **Não** criar função de refresh de token na camada de chat — o `proxyFetchWithRetry` já faz refresh automático em 401.
4. **Corrigir a probe `health`** (rota atual chama `/health`, canônica é `/api/v1/health`) — isso desbloqueia `backend-ready.ts` em toda a app, não só o chat.
5. **`ws-token/route.ts` deve usar `resolveAuthHeader`** (ou extrair só a parte nova de `dev-auto-login`), removendo a reimplementação inline.

---

## 7. Recomendações de correção (resumo, sem implementar)

1. **(Impacto 1)** Em `useChatTransport.ts:219-228`, **não** declarar `isConnected=true` + `transportMode="sse"` prematuramente. Melhor: deixar `isConnected=false` até o primeiro evento SSE de sucesso *ou* cair direto no REST. Alternativa: testar o endpoint SSE com um HEAD/OPTIONS antes de “prometer” conexão.
2. **(Impacto 1/2)** Em dev, usar `NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8001` **ou** documentar claramente que o cliente deve apontar para o backend direto — rewrites do Next não aceitam upgrade WS. Em Replit, isso exige um workflow separado com porta exposta pública para o backend, ou publicar o `lia-backend` atrás de uma URL com WS próprio.
3. **(Impacto 2)** Aguardar o `wsAuthToken` antes de qualquer `connect()`/`sendMessageViaSSE`. Se o token não chegou em X ms, **pular direto para REST** (que já recebe cookie via `credentials: "include"` e passa pelo middleware).
4. **(Impacto 3)** Mover `setIsThinking?.(false)` para *todos* os caminhos: WS (no `message`/`error`), SSE (no `.catch` final e no end-of-stream), e o REST já está coberto.
5. **(Impacto 5)** Corrigir `/api/backend-proxy/health/route.ts` para bater em `/api/v1/health` (o endpoint real do backend).
6. **(Impacto 6)** Retry + backoff em `useChatSocket.ts:85` para o `/api/auth/ws-token` (3 tentativas com delay curto), e considerar pré-fetch desse token no layout (server component) para já vir no HTML inicial.
7. **(Impacto 2)** Tornar explícito em algum lugar UI/DevTools que o chat está em modo “degradado” (mostrar `transportMode` atual no `UnifiedChatHeader` já é feito, mas não diferencia “SSE real” de “SSE fantasma”).

---

## 8. Próximas tarefas sugeridas (em ordem de impacto)

> Status de implementação aplicado em 16/04/2026 (commit pós-auditoria).

1. ✅ **IMPLEMENTADO** — Desfazer o fallback SSE "fantasma" e cair direto no REST quando o WS falhar (`useChatTransport.ts`: `isConnected=false` + `transportMode="disconnected"` após max retries).
2. ✅ **IMPLEMENTADO** — Retry + backoff do `/api/auth/ws-token` em `useChatSocket.ts` (3 tentativas, backoff exponencial 1.5s base, para em 401).
3. ⏭ **NÃO APLICADO** — Apontar WS direto para `NEXT_PUBLIC_WS_URL`. Em Replit dev o backend 127.0.0.1:8001 não é exposto publicamente; o Fix #1 já resolve o sintoma fazendo o REST assumir.
4. ✅ **IMPLEMENTADO** — `setIsThinking(false)` em todos os caminhos: novo `case "error"` em `useChatSocket.handleEvent` + emissão de evento `error` no SSE (tanto em falha permanente quanto em stream silencioso sem terminal).
5. ✅ **IMPLEMENTADO** — `/api/backend-proxy/health` aponta direto pra `/api/v1/health` (sem redirect 307).

### Bug novo descoberto durante validação runtime (não estava na auditoria)

Após as correções acima, o caminho REST foi desbloqueado e `POST /api/backend-proxy/chat/message` passa a retornar HTTP 200 corretamente, mas o corpo vem com **`{"content": ""}`** — o backend processa a mensagem sem erro e ainda assim produz resposta vazia. Evidência: o JWT emitido por `dev-auto-login` carrega `company_id: "demo_company"` (string literal), e o handler `http_chat_message` (`agent_chat_ws.py:995`) retorna `content=_strip_react_json(output.message or "")` — ou seja, algum agente está devolvendo `output.message` vazio sem exceção. Fora do escopo de #277, merece task separada.

---

### Apêndice A — Arquivos/linhas relevantes (referência rápida)

- `plataforma-lia/next.config.js:199-226` — rewrites (WS bug)
- `plataforma-lia/src/hooks/chat/useChatTransport.ts:98-228,277-397`
- `plataforma-lia/src/hooks/chat/useChatSocket.ts:85-94,272-278`
- `plataforma-lia/src/hooks/chat/useChatMessages.ts:140-236`
- `plataforma-lia/src/app/api/auth/ws-token/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/health/route.ts`
- `plataforma-lia/src/lib/auth/dev-auto-login.ts`
- `plataforma-lia/src/middleware.ts:149-304`
- `lia-agent-system/app/api/v1/agent_chat_ws.py:387-430,995-1102`
- `lia-agent-system/app/api/v1/agent_chat_sse.py:162-425`
