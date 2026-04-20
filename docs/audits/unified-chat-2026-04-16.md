# Auditoria — LIA Unified Chat (frontend + transporte + backend)

- **Task**: #292 — Audit + root-cause do chat unificado (`/chat`, float, sidebar)
- **Data**: 2026-04-16
- **Autor**: Task agent (somente auditoria, sem correções de código)
- **Escopo**: `UnifiedChat` (sidebar / floating / fullscreen), stack de conexão
  (`useLiaChatConnection` → `useChatSocket` → `useChatTransport` → `useAgentStreaming`),
  transporte WS/SSE/REST, slash commands, `DynamicContextPanel`, indicador
  "LIA digitando".
- **Fora de escopo**: wizard de criação de vagas, HITL aprovações, tool-calling
  detalhado, performance de LLM.

---

## 1. Metodologia

1. **Leitura estática** do stack do chat e do transporte (frontend + backend),
   mapeando fluxo de dados WS → handler → `setIsThinking` /
   `onCompleteRef` / `setHitlPending`.
2. **Playwright e2e** dedicado:
   `plataforma-lia/e2e/tests/chat/unified-chat-audit.spec.ts` (8 testes,
   `desktop-chrome`). Para permitir handshake WS real, a suíte não usa a
   fixture `authenticatedPage` (que injeta JWT fake rejeitado pelo backend) —
   confia no `dev-auto-login` disparado por `/api/auth/ws-token`
   (`plataforma-lia/src/lib/auth/dev-auto-login.ts:17`).
3. **Inspeção de logs** de `dev-server` (Next) e `lia-backend` (FastAPI)
   durante a execução dos testes.
4. **Screenshots** salvos em `plataforma-lia/e2e/screenshots/unified-chat-*.png`.

Os 8 testes passaram, mas intencionalmente usam `expect.soft` +
`test.info().annotations` para registrar desvios como achados em vez de
quebrar a suíte — este é um audit, não um portão.

### Arquivos-chave auditados

| Camada   | Arquivo                                                                              |
| -------- | ------------------------------------------------------------------------------------ |
| Página   | `plataforma-lia/src/app/[locale]/chat/page.tsx` (renderiza `ChatPageFullscreen`)     |
| UI raiz  | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`                         |
| Slash    | `plataforma-lia/src/components/unified-chat/wizard/useWizardIntegration.ts`          |
| Hook API | `plataforma-lia/src/hooks/chat/useChatSocket.ts`                                     |
| Hook tx  | `plataforma-lia/src/hooks/chat/useChatTransport.ts`                                  |
| Hook msg | `plataforma-lia/src/hooks/chat/useChatMessages.ts`                                   |
| Auth WS  | `plataforma-lia/src/app/api/auth/ws-token/route.ts`                                  |
| WS       | `lia-agent-system/app/api/v1/agent_chat_ws.py`                                       |
| SSE      | `lia-agent-system/app/api/v1/agent_chat_sse.py`                                      |

---

## 2. Resultados dos cenários do task spec

| ID          | Cenário                                       | Status | Achado principal                                          |
| ----------- | --------------------------------------------- | ------ | --------------------------------------------------------- |
| TC-UC-001   | Abrir `/chat`                                 | ✅     | Renderiza com `data-chat-mode=fullscreen`.                |
| TC-UC-002   | Transporte conecta via `/api/auth/ws-token`   | ⚠️     | `ws-token` responde 200; **nenhum upgrade WS detectado**. |
| TC-UC-003   | Indicador "LIA digitando"                     | ⚠️     | Não capturado por seletor de texto — ver F-UI-01.         |
| TC-UC-004   | Slash command `/criar vaga`, `/ajuda`, etc.   | ✅     | Input limpo localmente, não vai ao backend.               |
| TC-UC-005   | Slash `/job` e `/talent` (pedidos pelo task)  | ❌     | **Não existem** no código — ver F-CMD-02/03.              |
| TC-UC-006   | Fallback WS → SSE/REST                        | ✅     | `POST /api/backend-proxy/chat/message` fecha o fluxo.     |
| TC-UC-007   | Mode switching (fullscreen/sidebar/floating)  | ⚠️     | Toggle existe, mas sem `aria-label`/`title` padronizado.  |
| TC-UC-008   | `/chat` deve abrir em `fullscreen`            | ✅     | Confirmado pelo `data-chat-mode`.                         |

Evidência quantitativa das requisições durante a suíte
(`/tmp/logs/dev-server_*.log`):

- `GET /api/auth/ws-token 200` — **sempre** precedido pelo carregamento de
  `/chat`.
- `POST /api/backend-proxy/chat/message 200` — `~12` ocorrências,
  representando o fluxo REST que efetivamente entregou cada resposta.
- **Zero** upgrades `101 Switching Protocols` em `/ws/chat/*` nos logs
  coletados; zero eventos `websocket` capturados pelo Playwright.

---

## 3. Matriz de severidade

| ID            | Severidade | Área            | Título                                                                  |
| ------------- | ---------- | --------------- | ----------------------------------------------------------------------- |
| F-WS-01       | **Alto**   | Transporte      | WebSocket nunca é promovido em dev — todo o chat usa REST               |
| F-CMD-02      | **Alto**   | Slash commands  | `/job` inexistente — divergência task spec × código                     |
| F-CMD-03      | **Alto**   | Slash commands  | `/talent` inexistente — idem                                            |
| F-UI-01       | Médio      | UX              | Indicador "LIA digitando" sem rótulo acessível estável                  |
| F-UI-02       | Médio      | UX/a11y         | Botões de troca de modo sem `aria-label`/`title`                        |
| F-AUTH-01     | Médio      | Auth            | `e2e-test-token` do fixture é rejeitado pelo backend                    |
| F-HEALTH-01   | Médio      | Observabilidade | WS "silent fallback" não é reportado em telemetria                      |
| F-SSE-01      | Médio      | SSE             | `Last-Event-ID` é enviado mas replay não existe no servidor             |
| F-CHAT-01     | Baixo      | UX              | Fairness warnings são silenciosamente resetados a cada nova resposta    |
| F-CHAT-02     | Baixo      | UX              | `setFairnessWarnings` exposto mas nunca consumido na UI auditada        |
| F-HITL-01     | Baixo      | HITL            | `sendRaw` no caminho SSE chama `/api/v1/chat/action` direto, sem proxy  |

Critérios:

- **Crítico**: quebra funcionalidade para usuário final.
- **Alto**: perda significativa de recursos (realtime, comandos prometidos).
- **Médio**: UX/observabilidade/a11y degradada mas fluxo funciona.
- **Baixo**: débito menor, confusão ou código morto.

---

## 4. Achados detalhados (root-cause)

### F-WS-01 — WebSocket nunca completa handshake em dev (Alto)

**Sintoma**: em toda a suíte, `POST /api/backend-proxy/chat/message` é a
rota efetiva usada para enviar mensagens. Nenhum evento `websocket` é
disparado no contexto Playwright, e nenhum `101 Switching Protocols`
aparece nos logs do Next.

**Cadeia**:

1. `useChatSocket.ts:86-120` resolve o token via `/api/auth/ws-token`
   (com retry/backoff 0/1.5/3s). **OK.**
2. `useChatTransport.ts:98-102` monta a URL:
   `ws://${window.location.host}/ws/chat/{sessionId}?token=...`.
   Como o usuário acessa o app via `localhost:5000` (Next),
   a URL é `ws://localhost:5000/ws/chat/...` — **o Next.js não faz
   proxy/upgrade de WebSocket por default**. O backend (FastAPI) só
   atende WS em `127.0.0.1:8001`.
3. `ws.onclose` dispara com `evt.code` fora de 1000/1001 → retry até
   `maxReconnectAttempts=3`, cada um repetindo o mesmo destino inútil.
4. Após 3 falhas, `useChatTransport.ts:225-232` **corretamente** marca
   `wsFailedPermanentlyRef=true` e deixa `transportMode="disconnected"` para
   liberar o branch REST em `useChatMessages.ts:164-177` (comentário
   BUG-AUDIT #277 documenta essa escolha).
5. `setIsThinking(true)` é feito localmente em `useChatMessages.ts:145` (fix
   BUG-13), então o usuário percebe alguma responsividade, mas toda a
   vantagem de streaming (tokens incrementais) está perdida.

**Root-cause**: ausência de configuração de rewrite/proxy WS no Next.js
(`next.config.js`). O frontend assume que WS e HTTP compartilham host, o
que é verdadeiro em produção (ingress cuida do upgrade) mas **não** em
dev (`npm run dev` com `cd plataforma-lia`).

**Recomendação** (não implementar aqui):
- Adicionar `NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8001` no `.env` de dev, ou
  configurar `rewrites/customServer` com suporte a `upgrade` no Next.
- Emitir um log de transporte estruturado
  (`console.info('[chat-transport] mode=REST reason=ws_failed')`) em
  `useChatTransport.ts:225` para facilitar diagnóstico em campo.

---

### F-CMD-02 / F-CMD-03 — `/job` e `/talent` não existem (Alto) — RESOLVIDO (task #300)

**Resolução** (2026-04-20): a tabela canônica passou a viver em
`plataforma-lia/src/components/unified-chat/slash-commands.ts`. Os comandos
oficiais continuam em português (`/criar vaga`, `/buscar`, `/pipeline`,
`/relatorio`, `/feedback @…`, `/agendar @…`, `/ajuda`) e os identificadores
do task spec #292 (`/job`, `/talent`) foram registrados como aliases —
mapeiam para `/criar vaga` e `/buscar`, respectivamente. Tanto o
interceptor (`useWizardIntegration.handleSlashCommand`) quanto o dropdown
(`useSlashCommands`) consomem a constante. O texto de `/ajuda` em
`messages/{pt-BR,en}.json` agora lista os mesmos comandos.



**Sintoma**: digitar `/job` ou `/talent` e apertar Enter envia o texto
para o backend como mensagem normal, em vez de abrir o wizard de vaga /
de busca de talentos.

**Root-cause**: `useWizardIntegration.handleSlashCommand`
(`plataforma-lia/src/components/unified-chat/wizard/useWizardIntegration.ts:121-181`)
só cobre: `/criar vaga`, `/nova vaga`, `/ajuda`, `/pipeline`, `/relatorio`,
`/buscar @…`, `/pipeline @…`, `/relatorio @…`, `/feedback @…`,
`/agendar @…`. Não há `/job` nem `/talent`. O task spec #292 cita esses
comandos como contrato esperado.

**Duas hipóteses mutuamente exclusivas**:

- A implementação nunca cumpriu o contrato original (gap de produto).
- O task spec usa nomes "conceituais" que deveriam mapear para
  `/criar vaga` e `/buscar @…` (gap de documentação).

**Recomendação**:
- Decidir (PM) qual direção seguir e alinhar entre README do módulo
  `unified-chat`, o help in-app (comando `/ajuda`) e o task spec.
- Independente da decisão: **centralizar** a tabela de comandos num
  único `SLASH_COMMANDS` tipado (record) para evitar desvio futuro.

---

### F-UI-01 — Indicador "LIA digitando" sem rótulo estável (Médio)

**Sintoma**: o teste TC-UC-003 tentou localizar o indicador via
`text=/LIA (pensando|digitando|processando)|thinking/i` e não o
encontrou em 5s. Contudo, o fluxo REST retorna em ~800ms, então o
indicador pode aparecer e sumir antes do seletor resolver.

**Cadeia**:

- `UnifiedMessageList` recebe `isThinking` / `thinkingSteps` (ver
  `UnifiedChat.tsx:282-287`).
- O componente concreto que renderiza o indicador não foi inspecionado
  neste audit — a ausência de `data-testid="lia-thinking"` ou
  `role="status"` estável o torna difícil de localizar deterministicamente.

**Recomendação**:
- Adicionar `data-testid="lia-thinking-indicator"` e
  `role="status" aria-live="polite"` no componente de indicador para
  ganhar (a) testabilidade e (b) acessibilidade.

---

### F-UI-02 — Toggle de modo sem rotulagem acessível (Médio)

**Sintoma**: `page.locator('button[aria-label*="modo"|"mode"|...]').count()`
retorna 0 em `/chat`. O `UnifiedChatHeader` emite `handleModeChange` (ver
`UnifiedChat.tsx:187-208`) mas os botões que disparam não têm rótulo
acessível padronizado.

**Recomendação**:
- Adicionar `aria-label` explícito:
  `"Modo sidebar"`, `"Modo flutuante"`, `"Modo tela cheia"`, `"Minimizar chat"`.

---

### F-AUTH-01 — Fixture de auth e2e é incompatível com o backend (Médio)

**Sintoma**: `plataforma-lia/e2e/fixtures/auth.fixture.ts:19-32` injeta
`lia_access_token=e2e-test-token`. Ao chamar `/api/auth/ws-token`, o Next
devolve esse token como-if-fosse-JWT. O backend tenta `pyjwt.decode(...)`
em `agent_chat_ws.py:405` e `agent_chat_sse.py:70`, falha, e retorna
`user_id="anonymous"` — a conexão WS é rejeitada com
`code=1008` (`agent_chat_ws.py:415-419`) e o SSE retorna 401
(`agent_chat_sse.py:185-186`).

**Consequência**: qualquer teste e2e pré-existente que toque o stream do
chat está testando apenas o caminho REST/proxy. O branch WS/SSE está
sem cobertura real.

**Recomendação**:
- Reescrever `authenticatedPage` para bypassar o fixture cookie e
  forçar `dev-auto-login` (como este audit fez), ou
- Adicionar um endpoint `POST /api/v1/auth/e2e-token` gated por env
  `LIA_E2E_MODE=1` que emite JWT real para demo user.

---

### F-HEALTH-01 — "Silent fallback" sem telemetria (Médio)

**Sintoma**: quando o WS falha permanentemente
(`useChatTransport.ts:219-233`), o frontend apenas segue como se nada
tivesse ocorrido — nem um `console.warn` é emitido, apenas a troca
silenciosa de `transportMode`. O backend também não vê a falha.

**Recomendação**:
- Emitir evento estruturado (`console.info`) e um beacon
  `/api/client-metrics/transport-fallback` para SRE monitorar taxa de
  fallback em produção.

---

### F-SSE-01 — `Last-Event-ID` sem replay no servidor (Médio)

`useChatTransport.ts:326-339` envia o header `Last-Event-ID` e mantém
`lastEventIdRef`. O backend (`agent_chat_sse.py:167-171`) apenas aceita
o header mas **não** faz replay — o docstring admite. Se uma conexão SSE
cair no meio, o cliente hoje re-envia a mensagem original, o que gera
cobrança de tokens em duplicata.

**Recomendação**:
- Implementar event-store in-memory (Redis) por `session_id` com TTL
  de 5 min e replay a partir do `Last-Event-ID`.
- Alternativamente, remover o header do cliente para evitar implicar um
  contrato que não é honrado.

---

### F-CHAT-01 / F-CHAT-02 — Fairness warnings (Baixo)

`useChatSocket.ts:244-248` define:

```
if (event.fairness_warnings && (…).length > 0) {
  setFairnessWarnings(event.fairness_warnings as string[])
} else {
  setFairnessWarnings([])   // ← reset a cada mensagem
}
```

- F-CHAT-01: como `setFairnessWarnings([])` é chamado em TODO evento
  `message`, um warning só é visível enquanto nenhuma nova mensagem chega.
  Se o stream da LIA emitir múltiplos `message` em rápida sequência
  (multi-turn), o warning pisca e some.
- F-CHAT-02: o valor `fairnessWarnings` é exposto em
  `useLiaChatContext`, mas `UnifiedChat.tsx` não consome. A feature está
  implementada do lado do modelo mas invisível na UI auditada.

**Recomendação**:
- Acumular warnings em uma fila com dismissal manual, ou
- Se a feature está parked, remover do state até virar contrato formal.

---

### F-HITL-01 — `sendRaw` SSE ignora proxy (Baixo)

`useChatTransport.ts:264-276` no caminho SSE chama
`fetch('${API_BASE_URL}/api/v1/chat/action', …)` — isso bypassa
`/api/backend-proxy/*` e expõe a URL do backend se
`NEXT_PUBLIC_API_URL` estiver configurada para ambiente remoto.
Em dev com mesmo host funciona, mas viola a convenção usada em todo o
resto do código ("front nunca fala direto com FastAPI").

**Recomendação**:
- Criar `POST /api/backend-proxy/chat/action` encaminhando ao backend
  e usar essa rota em `sendRaw` SSE.

---

## 5. Observações gerais positivas

- `useChatTransport.ts:219-233` tem comentário explicando a decisão de
  declarar `disconnected` em vez de fingir "SSE fantasma" — boa
  engenharia defensiva (BUG-AUDIT #277).
- `useChatMessages.ts:142-145` e `:231-234` acendem/apagam `isThinking`
  no caminho REST — fix BUG-13 está presente e testado.
- `useChatTransport.ts:302-390` garante `setIsThinking=false` mesmo
  quando o stream SSE fecha sem evento terminal (fix BUG-AUDIT #277 H7).
- Backend `agent_chat_sse.py:347-354` usa keepalive de 30s — previne
  timeout de proxies.

---

## 6. Recomendações priorizadas (próximos passos, não executadas aqui)

1. **[Alto] Corrigir WS em dev**: configurar proxy de upgrade no Next ou
   apontar `NEXT_PUBLIC_WS_URL` diretamente para o backend.
2. **[Alto] Decidir contrato de slash commands**: implementar `/job` e
   `/talent` ou atualizar o task spec #292 para refletir os comandos
   existentes.
3. **[Médio] Rotular UI** (`aria-label`, `data-testid`) para thinking
   indicator e botões de modo — aumenta testabilidade e a11y.
4. **[Médio] Reescrever fixture `authenticatedPage`** para usar JWT real
   via dev-auto-login; só assim os ramos WS/SSE ganham cobertura e2e.
5. **[Médio] Adicionar telemetria de fallback** — beacon ao degradar
   para REST.
6. **[Médio] Revisar contrato SSE `Last-Event-ID`** — implementar
   replay ou remover o header do cliente.
7. **[Baixo] Limpar fairness warnings** (acumular ou remover) e rotear
   `chat/action` via backend-proxy para uniformizar.

---

## 7. Entregáveis deste audit

- Spec Playwright: `plataforma-lia/e2e/tests/chat/unified-chat-audit.spec.ts`
  (8 cenários, `desktop-chrome`).
- Screenshots: `plataforma-lia/e2e/screenshots/unified-chat-*.png`.
- Este relatório: `docs/audits/unified-chat-2026-04-16.md`.
- Sem mudanças de código no app — somente a spec de auditoria e este MD.
