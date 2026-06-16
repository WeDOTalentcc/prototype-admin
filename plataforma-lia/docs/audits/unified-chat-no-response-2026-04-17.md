# Unified Chat: auditoria de causa-raiz "LIA não responde"

- **Data:** 2026-04-17
- **Tarefa:** #374
- **Branch / commit:** task agent isolated
- **Ambiente:** dev local (`dev-server` Next.js 15 + `lia-backend` FastAPI), Replit container
- **Status do bug:** **CONFIRMADO** em 2026-04-17 03:24:08 UTC

---

## 1. Reprodução

### Cenário (mesmo do screenshot do usuário)

1. Subir `dev-server` (Next.js, porta 5000) e `lia-backend` (FastAPI, porta 8001).
2. Abrir o app via `https://$REPLIT_DEV_DOMAIN/` (browser limpo, sem cookies).
3. Navegar até a página de uma vaga (ou `/chat`, ou qualquer rota interna), abrir o chat unificado.
4. Digitar `oi` e pressionar Enter.

### Resultado observado

- Bolha do usuário com `oi` aparece à direita.
- Indicador "LIA pensando" pisca por 1–2 s.
- Nenhuma bolha de assistente aparece.
- Nenhum erro visível na UI.
- Nenhuma toast/banner.
- Indicador some silenciosamente — chat fica "morto".

### Resultado esperado

- Resposta da LIA (texto) deveria aparecer em até ~10 s.
- Em caso de erro, uma mensagem clara ("Erro ao conectar…", "Backend indisponível…", etc.) deveria aparecer.

### Reprodução por curl (sem cookies, simula browser limpo)

```bash
$ curl -sS -i "https://$REPLIT_DEV_DOMAIN/api/auth/ws-token"
HTTP/2 503
content-type: application/json
{"token":null,"code":"dev_auto_login_failed",
 "reason":"Backend /api/v1/auth/login did not return a token for the demo user",
 "authMode":"dev-auto-login"}

$ curl -sS -i -X POST "https://$REPLIT_DEV_DOMAIN/api/backend-proxy/chat/message" \
    -H "Content-Type: application/json" \
    --data '{"message":"oi","domain":"","session_id":"audit-374",
            "conversation_id":null,"context":{"page_type":"job_detail"}}'
HTTP/2 401
{"error":"Authentication required"}

$ curl -sS -i -X POST http://127.0.0.1:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    --data '{"email":"demo@wedotalent.com","password":"demo123"}'
HTTP/1.1 401 Unauthorized
{"error":true,"status_code":401,"message":"Invalid email or password",...}
```

### Evidência nos logs

`/tmp/logs/dev-server_*.log`:

```
GET /api/auth/ws-token 503 in 3165ms
GET /api/auth/ws-token 503 in 451ms
GET /api/auth/ws-token 503 in 393ms
GET /api/auth/ws-token 503 in 398ms
```

`/tmp/logs/lia-backend_*.log` (audit_logs do backend para cada tentativa do
`dev-auto-login`):

```
agent_name='auth_module' action='auth_failed' decision='rejected'
reasoning=["Authentication failed: invalid credentials",
           "Method: password", "Source IP: *.*.*.1"]
```

→ A flood de `GET /api/auth/ws-token` (citada na Task #374, item 4 / H4) é
**sintoma**, não causa — `useChatSocket` faz 3 tentativas com backoff e cada
nova montagem de `<UnifiedChat>` (sidebar / floating / fullscreen /
DashboardChatPanel) repete a sequência.

---

## 2. Mapa de fluxo da mensagem (REST, ramo efetivo neste bug)

| Etapa | Arquivo : linhas | Comportamento observado |
| --- | --- | --- |
| 1. Input → submit | `src/components/unified-chat/UnifiedChatInput.tsx:63-68` | Enter chama `onSend` |
| 2. `handleSend` | `src/components/unified-chat/UnifiedChat.tsx:138-160` | Chama `sendChatMessage(text)` do contexto |
| 3. Contexto LIA | `src/contexts/lia-float-context.tsx` (`useLiaChatContext`) | Encaminha para `useLiaChatConnection` |
| 4. Facade | `src/hooks/chat/use-lia-chat-connection.ts:34-95` | Compõe `useChatSocket` + `useChatMessages` |
| 5. Decisão de transporte | `src/hooks/chat/useChatMessages.ts:140-162` | `isConnected=false`, `transportMode="disconnected"` → cai no REST |
| 6. WS-token (paralelo) | `src/hooks/chat/useChatSocket.ts:86-120` | `GET /api/auth/ws-token` retorna **503** (3 tentativas). `wsAuthToken` permanece `undefined` |
| 7. WS handshake | `src/hooks/chat/useChatTransport.ts:98-244` | `buildWsUrl()` sem `?token=` → backend `agent_chat_ws` fecha o socket → `wsFailedPermanentlyRef=true` após `maxReconnectAttempts=3`, `transportMode="disconnected"` (BUG-AUDIT #277) |
| 8. POST proxy | `src/app/api/backend-proxy/chat/message/route.ts:9-58` | **Nunca executa** — middleware corta antes |
| 9. Middleware Next | `src/middleware.ts:162-191` | `DEV_AUTO_LOGIN=true` → `getDevToken()` → `null`. Sem cookie. Sem `workos_session`. Cai em `denyAccess` → `NextResponse.json({error:'Authentication required'}, 401)` |
| 10. Resposta no front | `src/hooks/chat/useChatMessages.ts:177-227` | `data = {error: "Authentication required"}`. **Todos os `if`** (`needs_clarification`, `pending_action.awaiting_confirmation`, `data.content`) são falsos. `onCompleteRef.current?.(...)` **nunca é chamado** |
| 11. `finally` | `src/hooks/chat/useChatMessages.ts:230-234` | `setIsThinking(false)` desliga o spinner — mas **nenhuma mensagem** foi adicionada ao array |

**Resultado líquido:** o usuário vê sua bolha, o spinner some em ~1 s, e nada
mais acontece. Sem erro, sem toast, sem fallback.

---

## 3. Hipóteses (todas auditadas)

| # | Hipótese | Status | Evidência |
| --- | --- | --- | --- |
| **H1** | `useChatSocket` declara `isConnected=true` enquanto `wsRef` está null/CLOSED → `wsSend` retorna silencioso e a mensagem some, deixando spinner preso. | **Parcial / latente** | Existe risco real: `useChatTransport.sendMessage` (linhas 254-261) só checa `wsRef.current.readyState`, sem fallback para REST nem desligar `setIsThinking`. Mas, nesta repro, `isConnected=false` desde o início (WS nunca abre), então o caminho REST é o tomado. **Defeito real, mas não é a causa-raiz deste sintoma específico.** |
| **H2** | Backend devolve `data.content`/`data.message.content`/`data.message.text` vazios; proxy entrega `content=""` e o `if (data.content)` falha. | **Descartada para esta repro** | O proxy NÃO chega a executar (middleware bloqueia em 401). Quando executa (sessão válida), `route.ts:36-40` extrai corretamente `data.message.content` (shape real do `ChatResponse` em `lia-agent-system/app/schemas/chat.py:17-27`). |
| **H3** | Em erro do backend (502/timeout) o proxy mascara como `200 { content: "Erro ao processar mensagem...", error: "backend_error" }`; usuário não vê esse texto. | **Descartada para esta repro** | Esse caminho RENDERIZARIA "Erro ao processar mensagem. Tente novamente." (porque `data.content` ficaria truthy). Como nada aparece, o proxy não está rodando — middleware antecipou o 401. |
| **H4** | Flood de `/api/auth/ws-token` indica re-mount agressivo de `useChatSocket` perdendo callbacks. | **Confirmada como sintoma, não causa** | `dev-server.log` mostra ≥ 4 chamadas ws-token em 5 s. Causa: `UnifiedChatConditional` (sidebar overlay) + `DashboardChatPanel` (inline) + provider raiz montam instâncias de `useChatSocket`/`useChatMessages` independentes. Não perde callbacks neste sintoma porque ninguém chega a entregar resposta. |
| **H5** | Efeito reconectador `if (wsAuthToken && isConnected) { disconnect(); setTimeout(connect, 50) }` cria janela onde mensagens vão a socket fechado. | **Descartada para esta repro** | O efeito só dispara quando `wsAuthToken` existe E `isConnected=true`. Aqui `wsAuthToken` nunca é setado (todos os GET `/api/auth/ws-token` retornam 503). **Defeito latente real**, mas só ativa quando WS funciona. |
| **H6** | Backend `chat.py:178` cai em `pre_compliance` 422 ("fairness_blocked") silenciosamente para "oi". | **Descartada** | (a) `pre_compliance` não é alcançado — middleware Next bloqueia antes. (b) Mesmo se fosse, o proxy `route.ts:27-31` converteria 422 em 200 com `content: "Erro ao processar mensagem..."`, então o usuário VERIA algo. |
| **H7** | Orquestrador retorna `response=""` e backend lança 502; mensagem 502 não é entregue. | **Descartada** | Mesmo motivo de H6: orquestrador nunca é alcançado. Quando é (sessão válida), `chat.py:249-260` faz `raise HTTPException(502, "LIA não conseguiu gerar resposta...")` e o proxy mascara em `content` truthy → renderiza. |
| **H8** | Persistência da conversa quebra após o primeiro turno (`MainOrchestrator._setup_conversation_memory`). | **Descartada para esta repro** | Não chegamos no primeiro turno real — auth falha antes. (Pode ser problema separado em sessões válidas; fora de escopo aqui.) |
| **H9** | WebSocket rejeita o token devolvido por `/api/auth/ws-token` (auth dev-auto-login vs JWT real) → socket fecha, front não recebe `message`. | **Confirmada como contribuinte** | `getDevToken()` retorna `null` (backend `/api/v1/auth/login` devolve 401 para `demo@wedotalent.com / demo123` — **demo seed quebrado / senha rotacionada**). Sem token, `buildWsUrl` (`useChatTransport.ts:98-102`) **não anexa `?token=`**; o handshake `WS /api/v1/ws/chat/{session_id}` é fechado pelo backend (vide `agent_chat_ws.py`, parsing de token na query string). Reconexão exponencial estoura `maxReconnectAttempts=3` → `wsFailedPermanentlyRef=true`. |
| **H10** | `onCompleteRef.current` aponta para callback de instância já desmontada → resposta entregue a listener "morto". | **Descartada para esta repro** | Nenhuma resposta chega; não há nada para o callback receber. (Risco real existe pelo H4, mas não é a causa observável.) |
| **H11 (novo)** | Proxy REST → middleware Next denyAccess 401 → resposta `{error:"Authentication required"}` sem campo `content` → `useChatMessages` não bate em nenhum `if` → silent drop. | **CONFIRMADA — causa-raiz do sintoma na UI** | Curl reproduz: middleware retorna 401 com payload sem `content`. Em `useChatMessages.ts:177-234`, `data.content` é `undefined`, `data.needs_clarification` é `undefined`, `data.message_metadata` é `undefined`. **Nada** dispara `onCompleteRef`. `catch` não dispara (HTTP é "ok" do ponto de vista do `fetch` — só `await res.json()` precisa ter sucesso, e tem). `finally` desliga `setIsThinking`. |
| **H12 (novo)** | `dev-auto-login` está hard-coded para `demo@wedotalent.com / demo123` mas o backend não tem esse usuário/senha sincronizado (audit_logs registram `auth_failed` sistemático). | **CONFIRMADA — causa-raiz ambiental** | `src/lib/auth/dev-auto-login.ts:18-19` define defaults; `lia-backend` rejeita: `audit_logs.reasoning=["Authentication failed: invalid credentials","Method: password",...]`. Sem variável de ambiente `DEV_AUTO_LOGIN_EMAIL/PASSWORD` correta nem demo seed atualizado, todo o fluxo dev-only quebra. |

---

## 4. Causa-raiz e por que os fixes anteriores não pegaram

### Causa-raiz (composta — duas camadas)

**Camada 1 — ambiental (H12):** `DEV_AUTO_LOGIN_EMAIL/PASSWORD` no `dev-server`
e o usuário demo no banco do `lia-backend` ficaram dessincronizados (rotação de
senha, restore de DB, ou `.env.local` ausente). Resultado: `getDevToken()` →
`null` permanentemente; `ws-token` → 503; nenhum cookie de auth é setado.

**Camada 2 — silent drop no front (H11):** quando o middleware Next retorna
401 (`{error:"Authentication required"}`), o `useChatMessages.sendMessage` no
ramo REST não tem nenhum branch para "resposta sem `content`". Ele:

1. Roda `await res.json()` com sucesso (não cai no `catch`).
2. Avalia 4 `if` — todos falsos (`conversation_id`, `pending_action`,
   `needs_clarification`, `content`).
3. Cai no `finally`, desliga `setIsThinking`, **retorna sem nunca chamar
   `onCompleteRef`**.

Isso tornaria o sintoma silencioso para QUALQUER resposta proxy/backend que
não case com o shape esperado — não apenas 401.

### Por que os fixes anteriores não pegaram

| Fix anterior | Cobertura | Por que não pega este caso |
| --- | --- | --- |
| **BUG-13** ("LIA digitando" acende em REST/SSE) | Liga `setIsThinking(true)` antes do `fetch` e desliga no `finally`. | Só trata o **indicador**. Não garante que uma resposta seja renderizada quando o JSON do servidor não tem `content`. |
| **BUG-AUDIT #277** (não declarar `isConnected=true` em SSE fantasma; emitir `error` em fechamento silencioso do SSE) | Limpa `isThinking` quando WS/SSE quebram. Libera REST como fallback. | Cobre **transporte WS/SSE**. O REST em si continua sem fallback de "resposta vazia". E não cobre `getDevToken=null` permanente. |
| **Task #298** (ws-token retry com backoff; `Cache-Control: no-store`; cookies seguros) | Evita cache de 401/503 e adiciona retry de 3 tentativas. | Não corrige o motivo do 503 (demo seed). 3 retries só amplificam o flood de logs e não geram token. |

---

## 5. Plano de correção recomendado

Cada item é independente e curto o suficiente para virar uma tarefa única.

### F1 — Front-end: REST nunca pode falhar silenciosamente
**Arquivo:** `plataforma-lia/src/hooks/chat/useChatMessages.ts:164-234`
**O que fazer:** depois de `await res.json()`, se `data.content` for falsy E
nenhum outro branch (`needs_clarification`, `pending_action`) disparou, chamar
`onCompleteRef.current?.(...)` com:
- `"Erro de autenticação. Faça login novamente."` quando `res.status === 401`.
- `"Erro do servidor (HTTP {status}). Tente novamente."` quando `!res.ok`.
- `"Resposta inesperada do servidor."` quando `res.ok` mas sem `content`.
Adicionar log estruturado (`console.error`) com `{status, body}` para
diagnóstico futuro.
**Por quê:** elimina H11 — qualquer cenário de "JSON sem content" passa a
mostrar mensagem ao usuário em vez de desaparecer.

### F2 — Front-end: `wsSend` precisa fallback REST
**Arquivo:** `plataforma-lia/src/hooks/chat/useChatTransport.ts:254-261` e
`plataforma-lia/src/hooks/chat/useChatMessages.ts:154-157`.
**O que fazer:** se `wsRef.current.readyState !== OPEN` no momento do envio,
**não** retornar silencioso. Devolver um sinal (boolean ou throw) para que
`useChatMessages` caia no caminho REST/SSE em vez de manter spinner preso.
**Por quê:** cobre H1 (e H5 implicitamente). Mesmo com WS funcionando,
janelas de reconexão continuam dando "spinner eterno" se a mensagem cair
fora do `OPEN`.

### F3 — Dev env: `dev-auto-login` falha precisa ser reportada e remediável
**Arquivos:**
- `plataforma-lia/src/lib/auth/dev-auto-login.ts:17-37` — logar com
  `console.error` o `status`/`body` do `/api/v1/auth/login` quando `!res.ok`,
  com prefixo `[dev-auto-login] DEMO USER LOGIN FAILED — check
  DEV_AUTO_LOGIN_EMAIL/PASSWORD or backend seed`.
- `plataforma-lia/src/middleware.ts:162-191` — quando `DEV_AUTO_LOGIN=true` e
  `getDevToken()` retorna `null` para uma rota `/api/`, devolver `503` com
  `{error:"dev_auto_login_failed"}` em vez de `401` "Authentication
  required" — assim o front consegue distinguir "não autenticado" de
  "ambiente dev quebrado".
- Documentar (`replit.md`) as variáveis `DEV_AUTO_LOGIN_EMAIL` e
  `DEV_AUTO_LOGIN_PASSWORD` e o seed de demo esperado no backend.

**Por quê:** sem isso, todo dev novo que clonar o repo bate exatamente neste
bug. Resolve H12.

(Opcional / fora do escopo desta tarefa de auditoria: F4 — consolidar provider
único de `useLiaChatConnection` no nível do layout para eliminar o flood do H4
e o risco do H10. Já existe a tarefa "Unify how recent conversations are
saved…", então não duplicar.)

---

## 6. Guard-rail

- **Teste Playwright:** `plataforma-lia/e2e/tests/chat/unified-chat-no-response.spec.ts`
  - Abre `/chat`, intercepta `POST /api/backend-proxy/chat/message` para
    devolver `401 {error:"Authentication required"}` (mesmo shape do
    middleware Next), envia "oi", e **falha** se nenhuma bolha de assistente
    aparecer em até 8 s.
  - Hoje o teste falha (reproduz o bug).
  - Quando F1 for aplicado, o teste passa.
- Anexa console + network log à evidência (`testInfo.attach`) para auditoria
  futura.

---

## 7. Apêndice — sumário de evidências em arquivo

- `dev-server` log: `/tmp/logs/dev-server_20260417_032531_555.log`
  → 4× `GET /api/auth/ws-token 503` em < 5s.
- `lia-backend` log: `/tmp/logs/lia-backend_20260417_032531_584.log`
  → audit_logs `auth_failed` para o usuário demo a cada tentativa do
  middleware Next.
- Repros curl: seção 1.
