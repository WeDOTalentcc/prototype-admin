# Auditoria Frontend — Parte 2: Segurança e Integrações (Dimensões 6-10)

**Plataforma:** LIA by WeDoTalent  
**Data:** 2026-03-30  
**Escopo:** Frontend (Next.js 15 + React 19 + Radix UI + Tailwind CSS)  
**Stack relevante:** TypeScript, SWR, Zod v4, Radix UI, Sonner, Lucide React

---

## Resumo Executivo

| Dimensão | Score | Status |
|----------|-------|--------|
| 6 — Acessibilidade | **2.0 / 3** | ⚠️ Parcial |
| 7 — Segurança | **1.0 / 3** | 🔴 Crítico |
| 8 — Integração com APIs | **2.0 / 3** | ⚠️ Parcial |
| 9 — Routing e Navegação | **1.5 / 3** | 🔴 Insuficiente |
| 10 — Gestão de Formulários | **1.5 / 3** | ⚠️ Parcial |
| **Média Geral** | **1.6 / 3** | ⚠️ Requer atenção |

---

## Dimensão 6 — Acessibilidade (Score: 2.0/3)

### Semântica HTML

| Item | Status | Evidência |
|------|--------|-----------|
| `<html lang="pt-BR">` | ✅ Conforme | `plataforma-lia/src/app/layout.tsx:44` |
| Hierarquia de headings | ⚠️ Parcial | `login/page.tsx:97` usa `<h1>`, depois `<h2>` na L161 — correto. Porém em `register/page.tsx:96-97` o branding lateral usa `<h1>` e o formulário `<h2>`, o que é adequado. Não foram encontrados saltos de nível (ex: h1→h3). |
| Elementos semânticos vs div/span | ⚠️ Parcial | Formulários usam `<form>`, `<label>`, `<input>` corretamente. Porém muitos containers usam `<div>` genéricos onde `<main>`, `<nav>`, `<section>`, `<header>`, `<footer>` seriam mais adequados. Ex: `login/page.tsx:65` poderia ser `<main>`. |
| Tabelas com thead/th | ✅ Conforme | `components/ui/table.tsx` usa `TableHeader`, `TableHead` (mapeando para `<thead>`, `<th>`). |

### Interação por Teclado

| Item | Status | Evidência |
|------|--------|-----------|
| Tab order | ✅ Conforme | Formulários seguem ordem natural de DOM. Radix UI (Dialog, Dropdown, Select) gerencia focus trap automaticamente. |
| Focus trap em modais | ✅ Conforme | `components/ui/dialog.tsx` usa `@radix-ui/react-dialog` que implementa focus trap nativo. Botão close tem `sr-only` label (L51). |
| `:focus-visible` preservado | ✅ Conforme | `components/ui/button.tsx:8` inclui `focus-visible:outline-none` com `focus:ring-2`. `components/ui/input.tsx:12` tem `focus:ring-2 focus:ring-gray-900/20`. Estilos de foco consistentes. |
| `motion-reduce` | ✅ Conforme | Animations respeitam `motion-reduce:transition-none` e `motion-reduce:animate-none`. Ex: `login/page.tsx:59,115,187,234`. |
| Atalhos de teclado | ✅ Conforme | `hooks/use-keyboard-shortcuts.tsx` existe e é utilizado. Componentes como `onKeyDown` são usados em ~70+ arquivos. |

### ARIA

| Item | Status | Evidência |
|------|--------|-----------|
| `aria-label` em elementos sem texto | ✅ Conforme | Loading states: `login/page.tsx:58` `aria-label="Carregando..."`. Ícones decorativos: `login/page.tsx:305` SVG Microsoft com `aria-hidden="true"`. |
| `aria-hidden` em ícones decorativos | ⚠️ Parcial | SVG do Microsoft tem `aria-hidden="true"` (L305). Porém Lucide icons (Mail, Lock, Eye, etc.) não possuem `aria-hidden="true"` sistematicamente — Lucide já omite de assistive tech por padrão via SVG sem `role="img"`, mas a prática explícita seria melhor. |
| `aria-expanded/selected/checked` | ✅ Conforme | Gerenciado automaticamente pelos componentes Radix UI (Accordion, Tabs, Dialog, Select, Checkbox, Switch). |
| `aria-live` | ✅ Conforme | Usado em loading states e contadores dinâmicos. Ex: `shared/[token]/page.tsx:432` `aria-live="polite" aria-atomic="true"`. Login loading: `login/page.tsx:58`. |
| `alt` em imagens | ✅ Conforme | `login/page.tsx:74` `alt="WeDo Talent"`. Verificado em múltiplos componentes — imagens possuem alt descritivo. |

### Formulários e A11y

| Item | Status | Evidência |
|------|--------|-----------|
| Label associado via `for/id` | 🔴 Ausente | `login/page.tsx:178-192`: `<label>` existe mas sem `htmlFor`. O `<input>` correspondente não tem `id`. Mesmo padrão em `register/page.tsx:136-146`, `forgot-password/page.tsx:82-92`. Nenhum formulário principal usa associação explícita `htmlFor`/`id`. |
| Erros via `aria-describedby` | 🔴 Insuficiente | Apenas 4 ocorrências em todo o codebase: `expanded-chat-modal.tsx:83`, `tool-confirmation-message.tsx:101`, `ExpandedChatInput.tsx:133`, `job-insights-modal.tsx:730`. Formulários de login/register/forgot-password NÃO associam mensagens de erro aos campos via `aria-describedby`. |
| `aria-required` | 🔴 Ausente | Nenhuma ocorrência de `aria-required` encontrada. Inputs usam atributo HTML `required`, que é parcialmente acessível, mas `aria-required` seria mais robusto para screen readers. |
| `role="alert"` em erros | ⚠️ Parcial | Erros em formulários são exibidos visualmente mas sem `role="alert"` para anúncio imediato por screen readers. Ex: `login/page.tsx:167-172`, `register/page.tsx:230-234`. |

### Contraste

| Item | Status | Evidência |
|------|--------|-----------|
| Texto normal (4.5:1) | ⚠️ Não auditável automaticamente | Classes como `lia-text-400`, `lia-text-500`, `lia-text-600` usam tokens customizados. Sem auditoria de contraste automatizada configurada. O Storybook possui `@storybook/addon-a11y` instalado (`package.json:80`), o que é positivo. |
| Botões e elementos UI (3:1) | ✅ Provável conforme | Botões primários usam `bg-gray-900 text-white` (alto contraste). Botões outline/ghost mantêm bom contraste visual. |

### Achados Dimensão 6

**Críticos:**
- Labels de formulário sem associação `htmlFor`/`id` em login, register e forgot-password — impacta navegação por screen reader

**Importantes:**
- Mensagens de erro não conectadas a campos via `aria-describedby` — screen readers não anunciam erros contextualmente
- Ausência de `aria-required` em campos obrigatórios
- Ausência de `role="alert"` em mensagens de erro de formulários
- Containers principais sem elementos semânticos (`<main>`, `<nav>`, `<footer>`)

**Melhorias:**
- Adicionar `aria-hidden="true"` explicitamente em ícones Lucide decorativos
- Configurar auditoria de contraste automatizada (axe-core ou Lighthouse CI)
- Adicionar skip-to-content link no layout principal
- Considerar addon-a11y do Storybook para testes de acessibilidade automatizados

---

## Dimensão 7 — Segurança (Score: 1.0/3)

### XSS e Sanitização

| Item | Status | Evidência |
|------|--------|-----------|
| `dangerouslySetInnerHTML` | 🔴 CRÍTICO | **~20 ocorrências** sem nenhuma biblioteca de sanitização (DOMPurify, sanitize-html). Zero matches para `DOMPurify`, `sanitize`, `purify` no codebase. |
| Arquivos afetados | 🔴 | `wsi-triagem-invite-modal.tsx:649,660,692`, `lia-expanded-panel.tsx:452,488`, `interview-scheduling-modal.tsx:195`, `MessageBubble.tsx:83`, `ChatMessageList.tsx:83,135,407`, `LiaSuperPrompt.tsx:539,574,603`, `LiaChatPanel.tsx:534`, `TransitionChatPanel.tsx:167`, `send-email-modal.tsx:280`, `report-email-templates.tsx:700`, `email-templates-manager.tsx:484`, `email-template-form-modal.tsx:317`, `unified-communication-modal.tsx:860,871`, `message-bubble.tsx:31` |
| Conteúdo renderizado | 🔴 | Mensagens de chat (user + LIA), previews de email, templates de comunicação — todos renderizam HTML não sanitizado. Potencial XSS via input do usuário no chat ou templates. |
| URLs com parâmetros | ⚠️ Parcial | `login/page.tsx:301` usa `encodeURIComponent(email)` para email no SSO redirect — correto. `middleware.ts:84` usa `new URL('/login', request.url)` — seguro por ser construção server-side. |

### Armazenamento de Tokens e Dados Sensíveis

| Item | Status | Evidência |
|------|--------|-----------|
| Tokens em localStorage | 🔴 IMPORTANTE | `auth-service.ts:57,62` armazena `access_token` e `refresh_token` em `localStorage`. Vulnerável a XSS — se o atacante explorar `dangerouslySetInnerHTML`, pode ler tokens. httpOnly cookies seriam mais seguros. |
| localStorage extensivo | ⚠️ Preocupante | ~100+ usos de `localStorage` no codebase para: preferências UI, dados de onboarding, configurações de tabela, templates, dados de usuário (`lia_user_data`), comandos salvos, etc. |
| sessionStorage | ✅ Uso limitado | Usado para dados transitórios: `lia-create-template`, `lia-execute-template`. Adequado para este tipo de dado. |
| Dados pessoais em storage | ⚠️ Atenção | `onboarding-controller.tsx:113` salva `lia_user_data` (demo user) em localStorage. `ClientContext.tsx:59` salva dados de cliente em localStorage. Avaliar se há PII. |

### Console.log em Produção

| Item | Status | Evidência |
|------|--------|-----------|
| `console.log/debug/info` | ✅ Conforme | **Zero ocorrências** de `console.log`, `console.debug` ou `console.info` no código fonte. Excelente higiene. |
| `console.warn/error` | ✅ Conforme | Apenas 4 arquivos com `console.warn/error` — uso adequado para debugging legítimo. |

### Secrets e API Keys

| Item | Status | Evidência |
|------|--------|-----------|
| API keys hardcoded | ✅ Conforme | Todas as API keys lidas de `process.env`: `WORKOS_API_KEY` (`lib/workos.ts:8-9`), `AI_INTEGRATIONS_ANTHROPIC_API_KEY` (rotas API), `WORKOS_WEBHOOK_SECRET`. Nenhuma key hardcoded no bundle client-side. |
| Fallback secret | ⚠️ Atenção | `lib/session-crypto.ts:3` usa `'fallback-dev-secret'` como fallback quando env vars não estão definidas. Em produção, se as vars não estiverem setadas, o secret será previsível. |
| API keys no bundle | ✅ Conforme | Keys do Anthropic/WorkOS são usadas apenas em `app/api/` (server-side routes), não expostas ao cliente. |

### Vulnerabilidades e Headers

| Item | Status | Evidência |
|------|--------|-----------|
| npm audit | 🔴 11 vulnerabilidades | **2 critical, 6 high, 3 moderate**. Pacotes críticos: `next` (RCE via React flight protocol, Server Actions source exposure, DoS), `jspdf` (Path Traversal, PDF Injection, XSS, DoS — 10 CVEs). High: `flatted` (DoS + Prototype Pollution), `minimatch` (ReDoS), `rollup` (Path Traversal), `storybook` (env var exposure, WebSocket hijacking), `undici` (HTTP smuggling, memory exhaustion, CRLF injection), `picomatch` (Method Injection, ReDoS). Moderate: `ajv` (ReDoS), `brace-expansion` (DoS), `dompurify` (mutation-XSS — irônico pois DOMPurify não é utilizado no código). Fix disponível via `npm audit fix` (non-breaking) e `npm audit fix --force` (breaking para jspdf). |
| CSP (Content Security Policy) | 🔴 Ausente | Nenhum header CSP configurado em `next.config.*` ou `middleware.ts`. Crítico dado o uso extensivo de `dangerouslySetInnerHTML`. |
| SRI (Subresource Integrity) | 🔴 Ausente | Sem configuração de SRI para scripts externos. |
| HTTPS | ✅ Implícito | Next.js em produção via Replit/Vercel opera em HTTPS por padrão. |

### Achados Dimensão 7

**Críticos:**
- **~20 usos de `dangerouslySetInnerHTML` sem NENHUMA sanitização** — risco direto de XSS stored/reflected via mensagens de chat, templates de email, previews de comunicação
- **Ausência total de CSP** — sem segunda camada de defesa contra XSS
- **Tokens JWT em localStorage** — combinado com XSS via dangerouslySetInnerHTML, permite roubo completo de sessão
- **11 vulnerabilidades npm (2 critical, 6 high)** — `next` com RCE via React flight protocol; `jspdf` com 10 CVEs incluindo Path Traversal e PDF Injection com execução de JavaScript arbitrário

**Importantes:**
- Fallback secret previsível em `session-crypto.ts` — pode comprometer integridade de sessões se env vars não configuradas em produção
- Dados de usuário/cliente armazenados em localStorage sem necessidade clara
- `undici` com HTTP smuggling e memory exhaustion; `flatted` com Prototype Pollution

**Melhorias:**
- Instalar e configurar DOMPurify em todos os pontos de `dangerouslySetInnerHTML`
- Migrar tokens para httpOnly cookies (ou pelo menos o refresh token)
- Configurar CSP headers via `next.config.js` (headers) ou middleware
- Remover fallback secret e falhar explicitamente se env var ausente
- Executar `npm audit fix` imediatamente para corrigir vulnerabilidades non-breaking
- Atualizar `jspdf` para v4.2.1+ (breaking change, requer teste)
- Integrar `npm audit` em pipeline CI

---

## Dimensão 8 — Integração com APIs (Score: 2.0/3)

### Camada de Serviços

| Item | Status | Evidência |
|------|--------|-----------|
| Pasta `services/` separada | ✅ Conforme | Estrutura organizada: `services/lia-api/` (11 módulos), `services/admin/` (12 módulos), `services/auth-service.ts`, mais 5 serviços auxiliares. Total: ~30 arquivos de serviço. |
| Módulos temáticos | ✅ Conforme | `candidates-api.ts`, `jobs-api.ts`, `chat-api.ts`, `wsi-api.ts`, `email-api.ts`, `bulk-api.ts`, `notifications-api.ts`, `voice-api.ts`, `feedback-api.ts`, `autonomous-api.ts`, `misc-api.ts`. |
| Objeto unificado `liaApi` | ✅ Conforme | `services/lia-api/index.ts:29-41` exporta objeto consolidado com spread de todos os módulos. |

### Cliente HTTP

| Item | Status | Evidência |
|------|--------|-----------|
| Centralização de headers | ✅ Conforme | `services/lia-api/base.ts:12-18` fornece `getAuthHeaders()` centralizado. `services/admin/api-client.ts:33-51` tem `buildHeaders()` separado com suporte a `X-Company-ID`, `X-User-ID`, `X-User-Role`. |
| Admin API Client | ✅ Conforme | `services/admin/api-client.ts` implementa client completo com métodos `get`, `post`, `patch`, `put`, `delete` e error handling tipado (`ApiClientError`). |
| Interceptors (auth, refresh, error) | ⚠️ Parcial | Sem interceptors no sentido clássico (sem Axios). `auth-service.ts:220-227` implementa refresh automático no `getMe()` em caso de 401 — abordagem ad-hoc, não centralizada. `admin/api-client.ts:53-86` trata 401/403 centralizadamente — melhor. |
| BACKEND_URL centralizado | ✅ Conforme | `base.ts:3` e `admin/api-client.ts:1` usam `/api/backend-proxy` como constante. |

### Resiliência

| Item | Status | Evidência |
|------|--------|-----------|
| Retry com backoff | 🔴 Ausente | Nenhum mecanismo de retry encontrado em nenhum serviço. Falhas de rede resultam em erro imediato. |
| Cancelamento no unmount (AbortController) | 🔴 Insuficiente | Apenas ~7 arquivos usam `AbortController`/`signal` — concentrados em hooks de busca (`useSemanticSearch.ts`, `UniversitiesFilterInput.tsx`). A grande maioria das chamadas API não cancela ao desmontar componente. |
| Race conditions | ⚠️ Risco | Sem debounce centralizado nas chamadas API. Hooks de busca com AbortController mitigam parcialmente, mas a maioria das chamadas não tem proteção. |
| Timeout configurado | ⚠️ Mínimo | Apenas `candidates-api.ts:23` passa `timeout: 60` como query param para o backend. Nenhum timeout no fetch client-side (fetch API não tem timeout nativo sem AbortController). |

### Contratos e Tipagem

| Item | Status | Evidência |
|------|--------|-----------|
| Tipos TypeScript | ✅ Conforme | `services/lia-api/types/` contém 14 arquivos de tipos: `candidate.types.ts`, `job.types.ts`, `chat.types.ts`, `pipeline.types.ts`, `wsi.types.ts`, `email.types.ts`, etc. Contratos manuais bem organizados. |
| Validação Zod | ✅ Conforme | `lib/schemas/` contém 6 schemas Zod: `candidate.schema.ts`, `job.schema.ts`, `ai.schema.ts`, `search.schema.ts`, `webhook.schema.ts`, `common.schema.ts`. Usados para validação de requests na camada API. |
| Validação de resposta | ⚠️ Parcial | Respostas tipadas via TypeScript (type assertion `response.json() as T`), mas sem validação runtime de response shape. |

### Tratamento de Status Codes

| Item | Status | Evidência |
|------|--------|-----------|
| 401 (Unauthorized) | ✅ Conforme | `admin/api-client.ts:54-62` trata 401 com `ApiClientError`. `auth-service.ts:220` tenta refresh. `middleware.ts:71-76` retorna JSON 401 para APIs protegidas. |
| 403 (Forbidden) | ✅ Conforme | `admin/api-client.ts:64-72` trata 403 com flag `isForbidden`. |
| Erros genéricos | ✅ Conforme | `admin/api-client.ts:74-86` trata outros erros extraindo `message`/`detail`. |
| Network errors | ✅ Conforme | `admin/api-client.ts:88-101` encapsula erros de rede com `isNetworkError: true`. |
| Payment required | ✅ Conforme | `base.ts:1` importa `checkPaymentRequired` — tratamento de 402. |

### Cache e Otimização

| Item | Status | Evidência |
|------|--------|-----------|
| SWR | ⚠️ Mínimo | SWR está instalado (`package.json:71`) mas `useSWR` usado em apenas ~5 arquivos (`admin/sso/page.tsx`, `useSemanticSearch.ts`, `useCandidateSuggestions.ts`, `use-candidate-data-requests.ts`, `use-workos-metrics.ts`). A maioria das chamadas usa `useEffect` + `useState` + `fetch` diretamente. |
| Invalidação de cache | ⚠️ Parcial | `mutate()` usado em ~5 arquivos — apenas onde SWR é utilizado. |
| Optimistic updates | 🔴 Ausente | Nenhuma evidência de optimistic updates no codebase. |
| Debounce | ⚠️ Limitado | Não encontrado debounce centralizado para chamadas API. |

### Ambiente e Mocking

| Item | Status | Evidência |
|------|--------|-----------|
| MSW (Mock Service Worker) | 🔴 Ausente | Sem MSW configurado. Testes existentes usam mocking manual. |
| Variáveis de ambiente | ✅ Conforme | API keys via `process.env`, URLs centralizadas em constantes. Correto. |

### Achados Dimensão 8

**Críticos:**
- Ausência de retry com backoff — falhas de rede resultam em erro imediato sem tentativa de recuperação
- Uso quase inexistente de AbortController — requests podem continuar após unmount, causando memory leaks e state updates em componentes desmontados

**Importantes:**
- SWR subutilizado (~5 de centenas de chamadas) — perda de benefícios de cache, dedup, revalidação
- Sem interceptors centralizados para refresh token — cada serviço trata auth failures de forma ad-hoc
- Sem validação runtime de responses (apenas type assertion)

**Melhorias:**
- Adotar SWR ou React Query como estratégia principal de data fetching
- Implementar wrapper fetch com retry, timeout via AbortController, e interceptors
- Configurar MSW para testes e2e e desenvolvimento
- Adicionar debounce em inputs de busca que disparam chamadas API

---

## Dimensão 9 — Routing e Navegação (Score: 1.5/3)

### Guards de Rota

| Item | Status | Evidência |
|------|--------|-----------|
| Middleware de autenticação | ✅ Conforme | `middleware.ts` classifica rotas em PUBLIC, PROTECTED_PAGE e PROTECTED_API. Verifica `wos-session` cookie ou `Authorization` header. |
| Redirecionamento pós-login | ✅ Conforme | `middleware.ts:83-84` salva `pathname` em `?next=` param. `login/page.tsx:42` redireciona para `/login/welcome` após login (não usa o `next` param diretamente — ver abaixo). |
| Return URL após login | ⚠️ Parcial | `middleware.ts` seta `?next=pathname`, mas `login/page.tsx:42` redireciona sempre para `/login/welcome`, ignorando o `next` param. O redirecionamento para a URL original pode ocorrer na welcome page. |
| Proteção por role | 🔴 Ausente | `middleware.ts` verifica apenas autenticação (token presente), não roles. Rotas `/admin/*` não verificam se o usuário é admin no middleware — a verificação ocorre apenas client-side ou no backend. |

### Lazy Loading e Performance

| Item | Status | Evidência |
|------|--------|-----------|
| Rotas lazy-loaded | ⚠️ Implícito | Next.js App Router faz code splitting automático por rota. Porém, `next/dynamic` é usado em apenas ~3 componentes, indicando que componentes pesados dentro de páginas não são lazy-loaded. |
| `Suspense` boundaries | ⚠️ Mínimo | Apenas ~3 usos de `Suspense` no codebase — sem boundaries em nível de layout/page. |
| `loading.tsx` | 🔴 Ausente | Nenhum arquivo `loading.tsx` encontrado em `src/app/`. Sem loading states automáticos do Next.js durante navegação. |
| `error.tsx` | 🔴 Ausente | Nenhum arquivo `error.tsx` encontrado em `src/app/`. Erros de renderização não são capturados por error boundaries do Next.js (há `ErrorBoundary` genérico em `layout.tsx:60`, mas não error boundaries por rota). |

### Página 404

| Item | Status | Evidência |
|------|--------|-----------|
| `not-found.tsx` | 🔴 Ausente | Nenhum arquivo `not-found.tsx` encontrado em `src/app/`. Rotas inválidas mostram o 404 padrão do Next.js sem branding. |
| Tratamento de chunk load failure | 🔴 Ausente | Sem `handleChunkLoadError` ou fallback para `ChunkLoadError` — se um chunk falhar ao carregar (deploy novo), o usuário vê um erro genérico. |

### Scroll e Estado na URL

| Item | Status | Evidência |
|------|--------|-----------|
| Scroll restoration | ⚠️ Padrão | Next.js App Router tem scroll restoration básica. Sem customização. |
| Filtros/paginação na URL | ⚠️ Parcial | `useSearchParams` usado em ~7 arquivos, `usePathname` em ~31 arquivos. Alguns filtros são gerenciados via URL, mas a maioria fica em state local (ex: tabelas de candidatos, kanban). |
| Tabs na URL | 🔴 Ausente | Tabs gerenciadas via state local, não refletidas na URL. Ao recarregar página, tab volta ao default. |

### Layouts e Navegação

| Item | Status | Evidência |
|------|--------|-----------|
| Layout compartilhado | ✅ Conforme | `src/app/layout.tsx` fornece providers globais (Theme, Auth, LiaFloat, ErrorBoundary, Toasters). Admin tem layout próprio (`admin/layout.tsx`). |
| Breadcrumbs | ⚠️ Existente | `components/admin/Breadcrumbs.tsx` existe para área admin. Sem breadcrumbs na área principal da plataforma. |
| Sidebar/navegação | ✅ Conforme | `components/sidebar.tsx` fornece navegação principal com links para todas as seções. |
| Comportamento por perfil | ⚠️ Parcial | `useJWTAuth()` fornece `user.role`, mas a maioria das verificações de permissão ocorre no backend. Frontend mostra/oculta elementos com base em role, mas sem sistema centralizado de permissões. |

### Achados Dimensão 9

**Críticos:**
- Ausência de `not-found.tsx` — rotas inválidas mostram 404 genérico sem branding
- Ausência de `error.tsx` — erros de renderização não são capturados por error boundaries específicas por rota
- Ausência de `loading.tsx` — sem indicadores de loading automáticos durante navegação

**Importantes:**
- `?next=` param do middleware não é consumido pelo login page — return URL potencialmente ignorada
- Sem proteção de role no middleware — admin pode ser acessado por qualquer usuário autenticado até o backend responder 403
- Sem tratamento de chunk load failure — deploys podem quebrar sessões ativas

**Melhorias:**
- Criar `not-found.tsx`, `error.tsx` e `loading.tsx` pelo menos no root de `src/app/`
- Consumir `?next=` param no login flow para redirecionar ao destino original
- Persistir filtros, paginação e tabs na URL via searchParams
- Adicionar breadcrumbs na área principal (não apenas admin)
- Implementar retry automático em chunk load errors

---

## Dimensão 10 — Gestão de Formulários (Score: 1.5/3)

### Validação

| Item | Status | Evidência |
|------|--------|-----------|
| Biblioteca de validação (Zod) | ✅ Instalada | `package.json:74` Zod v4 instalado. Schemas em `lib/schemas/`: `candidate.schema.ts`, `job.schema.ts`, `ai.schema.ts`, `search.schema.ts`, `webhook.schema.ts`, `common.schema.ts`. |
| Uso de Zod em formulários | ⚠️ Parcial | Zod usado primariamente para **validação de API requests** (server-side, em rotas `app/api/`). Formulários client-side fazem validação **manual**: `login/page.tsx:29-31` (`if (!email.includes("@"))`), `register/page.tsx:25-37` (checks manuais de senha, terms). |
| Estratégia de validação (blur/change/submit) | ⚠️ Apenas submit | Validação ocorre apenas em `onSubmit`. Sem validação em blur ou change. Ex: `register/page.tsx:21` valida tudo no `handleRegister`. |
| Mensagens de erro acionáveis | ✅ Conforme | Mensagens claras em pt-BR: "As senhas não coincidem", "A senha deve ter pelo menos 8 caracteres", "Insira um email válido". |

### UX de Submissão

| Item | Status | Evidência |
|------|--------|-----------|
| Botão disabled durante envio | ✅ Conforme | `login/page.tsx:274` `disabled={isSubmitting}`. `register/page.tsx:238` `disabled={isLoading}`. `forgot-password/page.tsx:103` `disabled={isLoading}`. |
| Loading visual | ✅ Conforme | Spinner (Loader2) + texto descritivo: "Entrando..." (`login/page.tsx:278`), "Criando conta..." (`register/page.tsx:243`), "Enviando..." (`forgot-password/page.tsx:108`). |
| Inputs disabled durante envio | ⚠️ Parcial | `login/page.tsx:238` desabilita campo de senha durante submissão. Mas campo de email na etapa 1 não é desabilitado. `register/page.tsx` não desabilita inputs durante loading. |
| Preservação de dados ao navegar | 🔴 Ausente | Sem mecanismo de preservação de dados. Navegar para outra página e voltar perde todo o input. Sem `sessionStorage` ou `useRef` para draft. |
| Confirmação antes de descartar | ⚠️ Parcial | `components/modals/unsaved-pearch-warning-modal.tsx` existe para pesquisas. Formulários de criação/edição de vaga não verificam alterações não salvas antes de fechar. |

### Máscaras e Inputs Especializados

| Item | Status | Evidência |
|------|--------|-----------|
| Máscara de CPF | 🔴 Ausente | Sem biblioteca de masking (react-input-mask, react-number-format). Nenhum input com máscara de CPF encontrado. |
| Máscara de telefone | 🔴 Ausente | Sem máscara de telefone. |
| Máscara de CEP | 🔴 Ausente | Sem máscara de CEP. |
| Upload com preview | ⚠️ Parcial | `components/cv/cv-upload-modal.tsx` existe para upload de CV. `components/chat/multimodal-upload.tsx` para uploads no chat. Sem preview visual antes do envio na maioria dos fluxos. |
| Campos de data | ⚠️ Básico | `date-fns` instalado para formatação. Sem date picker dedicado — inputs usam `type="date"` nativo. |
| Autocomplete | ✅ Conforme | `components/search/filter-autocomplete.tsx` fornece autocomplete para filtros de busca. `cmdk` (Command Menu) usado para paleta de comandos. |

### Multi-step e Formulários Grandes

| Item | Status | Evidência |
|------|--------|-----------|
| Login multi-step | ✅ Conforme | `login/page.tsx:18` implementa fluxo de 2 etapas (email → senha) com transição suave e botão "Alterar" para voltar. |
| Wizard/multi-step forms | ⚠️ Não encontrado | Diretório `components/wizard/` não contém arquivos. `components/job-wizard/` existe mas não está na lista de relevância. |
| Formulários grandes | ⚠️ Parcial | Criação de vaga (`create-job-modal.tsx`, `edit-job-modal.tsx`) são formulários complexos com múltiplos campos. Sem indicador de progresso ou divisão em seções colapsáveis com validação parcial. |

### Achados Dimensão 10

**Críticos:**
- Validação Zod não integrada com formulários client-side — validação manual propensa a erros e inconsistente
- Sem preservação de dados em formulários longos ao navegar — risco de perda de trabalho do usuário

**Importantes:**
- Ausência total de máscaras de input (CPF, telefone, CEP) — essencial para plataforma brasileira de RH
- Validação apenas em submit — sem feedback em tempo real (blur/change)
- Inputs não são desabilitados durante submissão em register

**Melhorias:**
- Integrar Zod com React Hook Form ou similar para validação client-side consistente
- Implementar validação em blur para campos críticos (email, senha)
- Adicionar máscaras para CPF, telefone e CEP
- Implementar `beforeunload` listener para formulários com alterações não salvas
- Usar `react-hook-form` com `zodResolver` para eliminar validação manual
- Adicionar date picker dedicado (ex: react-day-picker)

---

## Recomendações Prioritárias (Cross-dimensão)

### Prioridade 1 (Crítica — Sprint Atual)
1. **Executar `npm audit fix` e atualizar `jspdf`** — 11 vulnerabilidades (2 critical, 6 high), incluindo RCE em Next.js e Path Traversal em jspdf
2. **Instalar DOMPurify e sanitizar todos os usos de `dangerouslySetInnerHTML`** — risco XSS direto
3. **Configurar CSP headers** via `next.config.js` — segunda camada de defesa
4. **Criar `not-found.tsx`, `error.tsx`, `loading.tsx`** em `src/app/` — resiliência básica de navegação

### Prioridade 2 (Importante — Próximo Sprint)
5. **Migrar tokens para httpOnly cookies** (ao menos o refresh token)
6. **Associar labels com `htmlFor`/`id`** em todos os formulários
7. **Integrar Zod com React Hook Form** para validação client-side consistente
8. **Consumir `?next=` param no login** para redirect pós-autenticação

### Prioridade 3 (Melhorias — Backlog)
9. Adotar SWR/React Query como estratégia principal de fetching
10. Implementar retry com backoff e AbortController em serviços
11. Adicionar máscaras de input (CPF, telefone, CEP)
12. Persistir filtros/tabs na URL
13. Configurar MSW para mocking em testes
14. Integrar `npm audit` em pipeline CI

---

## Apêndice: Reprodutibilidade

### npm audit (executado em 2026-03-30)

```
$ cd plataforma-lia && npm audit

11 vulnerabilities (3 moderate, 6 high, 2 critical)

Critical:
  next 9.5.0–15.5.13 — RCE via React flight protocol, Server Actions source exposure, DoS (7 CVEs)
  jspdf ≤4.2.0 — Path Traversal, PDF Injection, XSS, DoS (10 CVEs)

High:
  flatted ≤3.4.1 — DoS + Prototype Pollution (2 CVEs)
  minimatch ≤3.1.3 — ReDoS (3 CVEs)
  picomatch ≤2.3.1 — Method Injection + ReDoS (2 CVEs)
  rollup 4.0.0–4.58.0 — Path Traversal (1 CVE)
  storybook 10.0.0-beta.0–10.2.9 — env var exposure + WebSocket hijacking (2 CVEs)
  undici 7.0.0–7.23.0 — HTTP smuggling, memory exhaustion, CRLF injection (6 CVEs)

Moderate:
  ajv <6.14.0 — ReDoS (1 CVE)
  brace-expansion <1.1.13 — DoS (1 CVE)
  dompurify ≤3.3.1 — mutation-XSS (2 CVEs, pacote não utilizado no código fonte)
```

### Comandos de busca utilizados

- `dangerouslySetInnerHTML`: grep no diretório `plataforma-lia/src` — ~20 matches em 15 arquivos
- `DOMPurify|sanitize|purify`: grep — 0 matches
- `console.log|debug|info`: grep — 0 matches (excluindo testes)
- `localStorage|sessionStorage`: grep — ~100+ matches
- `aria-describedby`: grep — 4 matches
- `aria-live|role="alert"`: grep — ~20 matches
- `not-found.tsx`, `loading.tsx`, `error.tsx`: glob em `src/app/` — 0 matches cada
- `useSWR|mutate`: grep — ~5 arquivos
- `AbortController|signal|abort`: grep — ~7 arquivos

---

*Relatório gerado como parte da Auditoria Frontend da Plataforma LIA — Parte 2*
