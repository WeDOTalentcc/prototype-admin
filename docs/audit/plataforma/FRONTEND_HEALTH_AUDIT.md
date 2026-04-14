# FRONTEND_HEALTH_AUDIT.md — Auditoria de Saude do Frontend
**Protocolo:** PX05  
**Data:** 2026-04-14  
**Auditor:** Claude Opus 4.6  
**Repositorio auditado:** `plataforma-lia/` (Next.js 15 + TypeScript, Replit)
- Backend IA: `lia-agent-system/` (FastAPI, Replit, porta 8001)
- Backend CRUD: `ats-api-copia/` (Rails 7.1, GitHub wedocc2026/wedotalentcc, deploy GCP)
- Contexto: Frontend + IA no Replit, Backend Rails no GCP. Integracao Rails<>Python via RabbitMQ (em configuracao). Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** P01 (PLATFORM_MAP), P20 (FRONTEND_AGENT_INTEGRATION_AUDIT)  
**Alimenta:** P32

---

## SCORE GERAL: 3.6 / 5

| Dimensao | Score | Peso |
|----------|-------|------|
| API Proxy e Conexoes | 3.5/5 | 25% |
| Chamadas Mortas | 3.0/5 | 25% |
| Estado e Stores | 4.0/5 | 20% |
| Error Handling | 4.0/5 | 15% |
| Componentes Mortos | 3.5/5 | 15% |

---

## 1. API PROXY E CONEXOES

### Arquitetura de Proxy

O frontend usa um BFF (Backend For Frontend) pattern com Next.js App Router:

```
Browser -> Next.js Server (port 5000)
             |
             |-- /api/backend-proxy/**  -> createProxyHandlers() -> BACKEND_URL (FastAPI :8001)
             |-- /api/lia/**            -> direct fetch -> BACKEND_URL (FastAPI :8001)
             |-- /api/v1/**             -> next.config rewrites -> BACKEND_URL (FastAPI :8001)
             |-- /ws/**                 -> next.config rewrites -> BACKEND_URL (FastAPI :8001)
             |-- /api/auth/**           -> auth handlers (WorkOS SSO + JWT)
```

### Proxy Configuration

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **BACKEND_URL** | OK | `http://127.0.0.1:8001` (server-side only, NAO exposto ao browser) |
| **RAILS_BACKEND_URL** | VAZIO | `""` — rotas Rails caem no fallback FastAPI |
| **NEXT_PUBLIC_WS_URL** | OK no .env.example | `ws://127.0.0.1:8001` |
| **NEXT_PUBLIC_RAILS_WS_URL** | NAO CONFIGURADO | ActionCable offline |
| **NEXT_PUBLIC_APP_URL** | OK | `http://localhost:5000` |
| **Padronizacao** | OK | Historico de 4 nomes (NEXT_PUBLIC_BACKEND_URL, LIA_BACKEND_URL, etc.) foi corrigido para um unico BACKEND_URL (07/04/2026, 423 arquivos) |

### Rewrites (next.config.js)

| Source | Destination | Status |
|--------|-------------|--------|
| `/api/v1/:path*` | `BACKEND_URL/api/v1/:path*` | OK — bypass do BFF para chamadas diretas |
| `/api/backend-proxy/wizard/:path*` | `BACKEND_URL/api/v1/wizard/:path*` | OK |
| `/api/lia/chat/stream` | `BACKEND_URL/api/v1/chat/stream` | OK — SSE streaming |
| `/ws/:path*` | `BACKEND_URL/ws/:path*` | OK — WebSocket proxy |

### createProxyHandlers() — BFF Pattern Central

- **Arquivo:** `src/lib/api/proxy-handler.ts`
- **478 rotas BFF** geradas por este pattern
- **BackendTarget:** Suporta `"fastapi"` (default) e `"rails"` — quando `RAILS_BACKEND_URL` esta vazio, TUDO vai para FastAPI
- **Auth:** `getAuthHeaders()` extrai token de 3 fontes (Authorization header > lia_access_token cookie > WorkOS session)
- **Timeout:** `AbortSignal.timeout(15000)` — 15s timeout por request
- **Error handling:** Retorna `{ error, details }` com status code do backend
- **Envelope unwrap:** Auto-detecta `{ok: true, data: ...}` e extrai `.data`

### CORS

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Same-origin** | OK | BFF roda no mesmo dominio — sem CORS issues para /api/backend-proxy |
| **WS connections** | OK | Rewrite para /ws/* — same-origin |
| **CSP connect-src** | OK | `'self' https://*.sentry.io wss: ws:` — permite WS |
| **Rails direto** | N/A | Frontend NAO chama Rails diretamente (tudo via BFF -> FastAPI) |

### WebSocket/SSE

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **WS URL** | OK | Rewrite `/ws/:path*` -> BACKEND_URL |
| **WS Auth** | OK | Token obtido via `/api/auth/ws-token` antes de conectar |
| **WS Reconnect** | OK | Auto-reconnect com backoff via `useChatTransport` |
| **SSE Fallback** | OK | Se WS falha, cai para SSE automaticamente |
| **ActionCable (Rails)** | OFFLINE | `NEXT_PUBLIC_RAILS_WS_URL` vazio — WorkflowRail sem push |

### ACHADOS CRITICOS — Proxy

1. **RAILS_BACKEND_URL vazio**: `proxy-handler.ts` tem suporte para rotear para Rails, mas `RAILS_BACKEND_URL=""` faz TODAS as rotas irem para FastAPI. Rotas marcadas como `backendTarget: "rails"` silenciosamente caem no FastAPI. **Sera resolvido quando integrado no GCP.**

2. **Onboarding proxy aponta para Rails inexistente**: `src/app/api/backend-proxy/onboarding/[...path]/route.ts` usa `RAILS_URL = process.env.RAILS_BACKEND_URL || "http://localhost:3000"`. Se `RAILS_BACKEND_URL` NAO esta configurado, aponta para `localhost:3000` que NAO existe no Replit. **Chamadas de onboarding falham silenciosamente.**

3. **Magic link aponta para Rails**: `src/app/api/auth/magic-link/route.ts` usa `RAILS_URL = process.env.RAILS_BACKEND_URL || "http://localhost:3000"`. Mesmo problema — fallback para localhost:3000 inexistente.

---

## 2. CHAMADAS MORTAS

### Rotas BFF que Apontam para Backend Inexistente

| Rota Frontend | Backend Target | Problema |
|---------------|---------------|----------|
| `/api/backend-proxy/onboarding/**` | Rails (localhost:3000) | RAILS_BACKEND_URL vazio, cai em localhost:3000 inexistente |
| `/api/auth/magic-link` | Rails (localhost:3000) | Mesmo problema |
| `/api/backend-proxy/recruitment-campaigns` | FastAPI | WorkflowRail chama esta rota — precisa verificar se endpoint existe no FastAPI |

### Rotas BFF OK (478 rotas -> FastAPI)

A grande maioria das 478 rotas BFF aponta para FastAPI via `BACKEND_URL` e funciona corretamente. O pattern `createProxyHandlers` garante consistencia.

### Endpoints no Backend SEM Frontend Correspondente

(Documentado em P20 — 8 capacidades invisiveis: ML predictions, calibration dashboard, digital twin config, search feedback analytics, suggestion acceptance rates, learning outcomes patterns, model registry, agent quality metrics)

### Paginas do Frontend

| Pagina | Rota | Backend Necessario | Status |
|--------|------|-------------------|--------|
| Home/Dashboard | `/[locale]` | FastAPI dashboard data | OK |
| Chat | `/[locale]/chat` | FastAPI WS/SSE | OK |
| Jobs | `/[locale]/jobs` | FastAPI CRUD | OK |
| Job Detail | `/[locale]/jobs/[id]` | FastAPI CRUD + Kanban | OK |
| Funil Talentos | `/[locale]/funil-de-talentos` | FastAPI talent pool | OK |
| Candidato Detail | `/[locale]/funil-de-talentos/candidato/[id]` | FastAPI candidate | OK |
| Bancos de Talentos | `/[locale]/bancos-de-talentos` | FastAPI pools | OK |
| Agent Studio | `/[locale]/agent-studio` | FastAPI studio | OK |
| Configuracoes | `/[locale]/configuracoes` | FastAPI settings | OK |
| AI Credits | `/[locale]/configuracoes/ai-credits` | FastAPI credits | OK |
| Tasks | `/[locale]/tasks` | FastAPI tasks | OK |
| Trust Center | `/[locale]/trust` | FastAPI compliance | OK |
| Privacidade | `/[locale]/privacidade` | FastAPI LGPD | OK |
| Triagem | `/[locale]/triagem/[token]` | FastAPI screening | OK |
| Portal LGPD | `/[locale]/portal/data-request/[token]` | FastAPI data subject | OK |
| Design System | `/[locale]/design-system` | Nenhum (reference page) | OK |
| Upgrade | `/[locale]/upgrade` | FastAPI plans | OK |
| Shared Search | `/[locale]/shared/[token]` | FastAPI shared | OK |
| Ajuda | `/[locale]/ajuda` | Static content | OK |
| Teams Tab (3 pages) | `/[locale]/teams-tab/**` | FastAPI + Teams SSO | OK |
| Login/Register/SSO | 5 paginas | FastAPI auth + WorkOS | OK |
| Funil (legacy) | `/[locale]/funil` | FastAPI | LEGACY — duplicado de funil-de-talentos |
| Vagas public | `/[locale]/vagas/[slug]` | FastAPI public job page | OK |
| Accept Invitation | 2 paginas (pt/en) | FastAPI invite | OK |

**32 paginas ativas**, nenhuma orfan (sem backend). 1 pagina legacy duplicada (`/funil`).

---

## 3. ESTADO E STORES

### Padrao: Zustand

| Store | Arquivo | Consumers | Sync com Backend |
|-------|---------|-----------|------------------|
| **auth-store** | `src/stores/auth-store.ts` | Global — todos os componentes | Login/logout -> API, refresh token automatico |
| **kanban-store** | `src/stores/kanban-store.ts` | KanbanPage, drag-drop hooks | Local state — NAO sincroniza automaticamente com backend |
| **wizard-store** | `src/stores/wizard-store.ts` | Job wizard flow | Local state durante wizard, salva ao publicar |
| **candidates-store** | `src/stores/candidates-store.ts` | Search, list, detail pages | Fetch on mount, NAO real-time |
| **chat-state-store** | `src/stores/chat-state-store.ts` | Chat page alternate state | Local state |
| **agent-studio-store** | `src/stores/agent-studio-store.ts` | Agent Studio page | Fetch on mount |
| **job-filters-store** | `src/stores/job-filters-store.ts` | Jobs list page | Local filter state |
| **job-ui-store** | `src/stores/job-ui-store.ts` | Jobs UI state | Local |
| **navigation-store** | `src/stores/navigation-store.ts` | Sidebar/nav state | Local |
| **onboarding-store** | `src/stores/onboarding-store.ts` | Onboarding flow | Local |
| **recent-items-store** | `src/stores/recent-items-store.ts` | Recent items menu | Local |
| **table-features-store** | `src/stores/table-features-store.ts` | Table config | Local |
| **talent-funnel-store** | `src/stores/talent-funnel-store.ts` | Talent funnel page | Fetch on mount |
| **template-store** | `src/stores/template-store.ts` | Template management | Fetch on mount |
| **triagem-store** | `src/stores/triagem-store.ts` | Screening page | Fetch on mount |
| **ui-preferences-store** | `src/stores/ui-preferences-store.ts` | Theme, layout prefs | LocalStorage persistence |

**16 stores** + **3 React Contexts** (auth, lia-float, teams-sso).

### Notificacao de Mudancas (Backend -> Frontend)

| Mecanismo | Usado Para | Status |
|-----------|-----------|--------|
| **WebSocket** | Chat streaming, HITL, plan progress, background tasks | OK |
| **SSE** | Chat fallback | OK |
| **ActionCable** | Workflow Rail campaign updates | OFFLINE (RAILS_WS_URL vazio) |
| **Polling 30s** | Workflow Rail fallback | Ativo quando ActionCable falha |
| **Manual refresh** | Kanban, candidate detail, job detail | Necessario apos acoes do agente |
| **SWR/useSWR** | Hooks de dados (testados mas uso limitado) | Parcial |
| **Store reset on auth** | `registerStoreReset()` limpa tudo no logout | OK |

### ACHADO: Dados Stale

| Cenario | Stale? | Detalhes |
|---------|--------|----------|
| Agente move candidato -> Kanban | SIM | Kanban NAO recebe push, precisa reload |
| Agente calcula WSI -> Candidate detail | SIM | Score no chat OK, painel lateral stale |
| Agente envia email -> Communication history | PARCIAL | Chat confirma, historico pode demorar |
| Agente publica vaga -> Jobs list | PARCIAL | Depende de refetch |
| Chat resposta -> Chat UI | NAO | Real-time via WS/SSE |
| Background task completa -> UI | NAO | Real-time via WS event |

---

## 4. ERROR HANDLING NO FRONTEND

### Error Boundaries

| Boundary | Arquivo | Escopo |
|----------|---------|--------|
| **Global Error** | `src/app/error.tsx` | Toda a aplicacao — captura erros nao tratados |
| **ErrorBoundarySection** | `src/components/ui/error-boundary-section.tsx` | Secao de pagina — isola falhas |
| **WizardErrorBoundary** | `src/components/unified-chat/wizard/WizardErrorBoundary.tsx` | Wizard do chat |
| **Generic ErrorBoundary** | `src/components/error-boundary.tsx` | Componente wrapper generico |

### Sentry Integration

- **Global error.tsx:** Captura erros e envia para Sentry automaticamente
- **Error digest:** Mostra codigo de rastreamento ao usuario
- **Retry button:** "Tentar novamente" em todos os error boundaries

### API Error Handling

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Proxy errors** | OK | `createProxyHandlers` retorna `{ error, details }` com status HTTP |
| **401 -> Token refresh** | OK | `proxyFetchWithRetry` tenta refresh automatico no 401, retry com novo token |
| **Loading states** | OK | `isLoading` / `isCreating` / `isStreaming` em todos os hooks relevantes |
| **404/500 ao usuario** | OK | Error boundaries capturam e mostram UI amigavel |
| **WS error -> SSE fallback** | OK | `useChatTransport` faz fallback automatico |
| **WS reconnect** | OK | Auto-reconnect com backoff exponencial |
| **Timeout** | OK | 15s timeout em proxy requests via `AbortSignal.timeout(15000)` |
| **Tela branca** | RARO | Error boundaries previnem — pior caso mostra "Algo deu errado" |

### ACHADO: Onboarding Falha Silenciosa

`/api/backend-proxy/onboarding/[...path]/route.ts` chama `RAILS_URL` (localhost:3000). Se Rails NAO esta rodando (cenario atual no Replit), a chamada falha com timeout/connection refused. O erro retornado ao frontend e um generico 500, mas o usuario pode ver loading infinito se o componente nao trata timeout adequadamente.

---

## 5. COMPONENTES MORTOS

### Analise de Imports Nao Usados

| Tipo | Encontrados | Detalhes |
|------|-------------|----------|
| **Paginas orfas** | 1 | `/[locale]/funil` — duplicado legacy de `/[locale]/funil-de-talentos` |
| **Design System page** | 0 impacto | Reference page, nao e orfan, mas nao e acessivel em producao |
| **Stores sem consumers** | 0 confirmados | Todos os 16 stores tem pelo menos 1 consumer |
| **Contexts** | 0 orfaos | 3 contexts todos usados |

### Services Layer

| Service | Arquivo | Usado? |
|---------|---------|--------|
| `agentMemoryService.ts` | Agent memory queries | SIM |
| `agent-monitoring.ts` | Agent health dashboard | SIM |
| `ai-consumption.ts` | Token usage tracking | SIM |
| `auth-service.ts` | Login/SSO/JWT | SIM |
| `duplicate-detection-service.ts` | Candidate dedup | SIM |
| `integrations-service.ts` | Third-party integrations | SIM |
| `lia-api/` (10 modules) | Chat, candidates, jobs, email, bulk, feedback, etc. | SIM |

### Assets e Dependencias

| Aspecto | Status |
|---------|--------|
| **Bundle analyzer** | Configurado (`ANALYZE=true`) |
| **Tree-shaking** | Otimizado para lucide-react (1500 icones), radix-ui, recharts |
| **Image optimization** | Next.js Image com AVIF/WebP, remote patterns configurados |
| **Cache headers** | Corretos — static assets 1yr immutable, API no-cache |

---

## SEGURANCA DO FRONTEND

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **CSP** | OK | default-src self, script-src unsafe-inline/eval (necessario para Next.js) |
| **X-Frame-Options** | OK em prod | DENY em production |
| **HSTS** | OK em prod | max-age=63072000, includeSubDomains, preload |
| **X-Content-Type-Options** | OK | nosniff |
| **Referrer-Policy** | OK | strict-origin-when-cross-origin |
| **Permissions-Policy** | OK | camera=(), microphone=(self), geolocation=() |
| **X-XSS-Protection** | OK | 1; mode=block |
| **BACKEND_URL NAO exposto** | OK | Server-side only, sem NEXT_PUBLIC_ prefix |
| **PII masking no chat** | OK | maskPII() para CPF, email, telefone |
| **Token em cookie httpOnly** | OK | lia_access_token com httpOnly, secure em prod, sameSite lax |
| **Session crypto** | OK | WorkOS session com verifyAndDecodeSession() |

### ACHADO: CSP unsafe-eval

`script-src 'self' 'unsafe-inline' 'unsafe-eval'` — necessario para Next.js runtime, mas `unsafe-eval` abre risco de XSS se houver injecao. Considerar `nonce`-based CSP quando Next.js suportar melhor.

---

## RECOMENDACOES PRIORIZADAS

### P0 — Fix Onboarding Proxy Fallback
**O que:** `onboarding/[...path]/route.ts` faz fallback para `localhost:3000`. Adicionar check: se `RAILS_BACKEND_URL` vazio, retornar 503 com mensagem clara em vez de tentar conectar localhost inexistente.
**Impacto:** Previne loading infinito e erros silenciosos
**Esforco:** S (30 min)

### P0 — Fix Magic Link Proxy
**O que:** Mesmo problema em `auth/magic-link/route.ts` — fallback para localhost:3000
**Impacto:** Magic link login nao funciona sem Rails
**Esforco:** S (30 min)

### P1 — Configurar RAILS_BACKEND_URL no Deploy GCP
**O que:** Quando integrado, setar `RAILS_BACKEND_URL` e `NEXT_PUBLIC_RAILS_WS_URL`
**Impacto:** Desbloqueia onboarding proxy, magic link, ActionCable, WorkflowRail
**Esforco:** S (configuracao)

### P1 — Eliminar Dados Stale no Kanban
**O que:** Quando agente executa `move_candidate`, emitir evento WS que Kanban escuta para update otimista
**Impacto:** Kanban reflete acoes do agente instantaneamente
**Esforco:** M (criar event channel + consumer)

### P2 — Remover Pagina Legacy /funil
**O que:** `/[locale]/funil` e duplicado de `/[locale]/funil-de-talentos`. Adicionar redirect permanente.
**Impacto:** Menos confusao, URLs limpas
**Esforco:** S (1 redirect)

### P2 — CSP com Nonce
**O que:** Substituir `unsafe-eval` por nonce-based CSP
**Impacto:** Maior seguranca contra XSS
**Esforco:** M (depende de suporte Next.js)

### P2 — SWR Global para Data Fetching
**O que:** Padronizar data fetching com SWR em vez de fetch-on-mount em stores
**Impacto:** Cache automatico, revalidacao, melhor UX de loading
**Esforco:** L (migracao gradual)

---

## RESUMO EXECUTIVO

### O que funciona muito bem
1. **BFF pattern consistente** — 478 rotas via `createProxyHandlers()` com auth, timeout, envelope unwrap
2. **Auth chain robusta** — 3 fontes de token (header > cookie > WorkOS session), refresh automatico no 401
3. **Error boundaries em 4 niveis** — global, section, wizard, generic + Sentry integration
4. **Seguranca HTTP headers** — CSP, HSTS, X-Frame-Options, PII masking, httpOnly cookies
5. **WS/SSE dual transport** — auto-fallback, reconnect com backoff
6. **Store pattern limpo** — 16 Zustand stores, reset on logout, devtools habilitado
7. **Padronizacao concluida** — historico de 4 nomes de URL corrigido para 1 unico BACKEND_URL

### O que precisa de atencao
1. **2 rotas apontam para Rails inexistente** — onboarding e magic-link fallback para localhost:3000
2. **ActionCable offline** — RAILS_WS_URL vazio, WorkflowRail sem push (resolve com GCP)
3. **Dados stale apos acoes do agente** — Kanban, candidate detail, job detail precisam refresh manual
4. **1 pagina legacy duplicada** — /funil (redirect para /funil-de-talentos)
5. **CSP com unsafe-eval** — risco baixo mas nao ideal

### Metafora
O frontend e uma casa bem construida — fundacao solida (BFF pattern, auth, error handling), encanamento funcionando (WS/SSE), alarme instalado (CSP, HSTS). Mas 2 torneiras estao conectadas a um cano que ainda nao chega na rua (Rails routes -> localhost:3000), e quando o jardineiro (agente) mexe no jardim, voce precisa abrir a janela para ver a mudanca (dados stale, sem push).

### Score Final: 3.6/5
Frontend saudavel com gaps pontuais e previssiveis (integracoes Rails pendentes do deploy GCP).
