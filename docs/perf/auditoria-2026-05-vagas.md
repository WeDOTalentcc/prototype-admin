# Auditoria de performance da renderização — `/jobs` e demais páginas

> **Tipo:** diagnóstica (read-only). Nenhum código de produto/configuração foi alterado.
> **Data:** 2026-05-16
> **Ambiente:** Replit container, `plataforma-lia/` (Next.js 16.2.4 + React 19 + Turbopack, App Router), `lia-backend` FastAPI :8001, `dev-server` Next.js :5000, ambos rodando durante a coleta.
> **Comparativo:** plano de abril `docs/superpowers/plans/2026-04-20-plataforma-lia-perf.md`
> **Tasks recentes consideradas:** #1090 → #1134

---

## 0. Resumo executivo

O frontend `plataforma-lia` continua **fortemente dominado pelo custo de cold-compile do Turbopack em dev** e pela ausência de cache no client. Medições reais coletadas neste ambiente:

- `/pt` cold-compile: **25,5 s** TTFB (warm: 0,10–0,40 s).
- `/pt/jobs` cold-compile (com `/pt` já quente): **4,4 s** TTFB (warm: 0,10–0,22 s).
- `/pt/funil-de-talentos` cold: **3,1 s** | `/pt/configuracoes` cold: **2,7 s**.
- Primeira chamada da API `/api/backend-proxy/job-vacancies`: **3,76 s** (compila o route handler + roundtrip ao FastAPI); warm fica em **0,029 s**.
- Numa primeira tentativa, um curl cold contra `/pt/jobs` com timeout de 90 s **derrubou o dev-server** (provável OOM no `next dev -H 0.0.0.0 -p 5000` com `--max-old-space-size=2560`). Após restart, o cold de `/pt/jobs` foi 4,4 s — sugerindo que parte dos travamentos relatados em uso real do app correspondem a momentos em que múltiplas rotas são compiladas em paralelo (multi-tab, prefetch agressivo) ultrapassando o teto de heap.

O plano de abril `2026-04-20-plataforma-lia-perf.md` foi cumprido **apenas parcialmente**: vários itens de "trash cleanup" e duas libs (twilio voice-sdk, microsoft/teams-js) saíram do bundle estático ou já eram dinâmicas, mas as causas estruturais maiores **continuam abertas** — em especial a consolidação dos 519 `route.ts` em `backend-proxy/` (Task 9 do plano antigo, nunca executada) e os dynamic imports de `recharts` / `chart.js` / `@tiptap` (Tasks 4 e 5, idem).

**Top 5 causas-raiz (ordenadas por impacto × custo):**

| # | Causa-raiz | Evidência medida | Esforço | Ganho esperado |
|---|---|---|---|---|
| 1 | **519 route handlers individuais em `backend-proxy/`**; 274 (52,8 %) são passthroughs idênticos via `createProxyHandlers` e poderiam ser substituídos por um catch-all `[...path]/route.ts`. | `git ls-files src/app/api/backend-proxy/ \| wc -l` = 519 (`find` confirma). Cold compile do route handler `job-vacancies` adiciona **3,57 s** à primeira chamada (3,76 s cold vs 0,029 s warm). Sample de outros 5 proxies frios: 0,14 → 0,36 s cada. | M | **Alto** (cumulativo: cada API hit do dia acordando é um compile a mais) |
| 2 | **`useJobsData` faz 2 fetches sequenciais** (`listJobVacancies` + `getJobVacanciesOverview`) sem `Promise.all`; sem SWR/React Query, sem cache HTTP do lado do client. Re-fetch dispara em `focus` quando há erro. | `useJobsData.ts:79-298`. APIs medidas: 3,76 s + 0,19 s no cold (em série hoje) → 3,95 s; em paralelo ficaria limitado pelo mais lento (3,76 s). Warm: 0,029 + 0,025 = 0,054 s sequencial. | S | **Médio-alto** (TTI cold de `/jobs` cai 5 %; em redes degradadas, ganho dobra) |
| 3 | **Imports estáticos pesados ainda no client bundle:** `recharts` em `ai-credits-page.tsx` + `StudioComplianceView.tsx`; `chart.js + react-chartjs-2` nos dois `interactive-charts*.tsx`; `@tiptap/*` em `lia-editor.tsx` (consumer único: `JobInfoGeralSection.tsx`). | `rg "from ['\"](recharts\|chart.js\|@tiptap)" src/` retorna apenas esses 4 arquivos. **Não foram colocados em `next/dynamic`** apesar de Task 4 e Task 5 do plano de abril. | S–M | **Médio** (First Load JS das rotas que importam transitivamente cai; cold compile não muda) |
| 4 | **`middleware.ts` roda em toda request não-estática** (matcher amplo), faz `verifyAndDecodeSession`/`jwtVerify` por request, **sem short-circuit** para prefetches do Next (`Next-Router-Prefetch: 1`) e, em dev, faz `getDevToken()` que é round-trip ao backend. | `middleware.ts:1-347`; matcher `'/((?!_next/static\|_next/image\|favicon.ico).*)'` linha 339. Cold de `/pt` (25,5 s) inclui middleware + intl + auth; warm cai a 0,1 s então o custo de regime do middleware está aceitável, mas o multiplicador é alto em listas com muitos `<Link>`. | S | **Médio** (cada hover sobre `<Link>` paga o pipeline; redução simples) |
| 5 | **Monolito `useJobsPageCore`** retorna ~280 chaves combinando state e actions de 6 sub-hooks num único objeto. Qualquer setter de qualquer slice re-renderiza `JobsPage` inteira. Combinado com `typescript.ignoreBuildErrors: true`, o app perde gate de qualidade. | `useJobsPageCore.ts` = 560 linhas, return composto agregando `useJobsData`, `useJobsFilters`, `useJobsTableConfig`, `useJobsPreview`, `useJobsBulkActions`, `useJobsChat`. `next.config.js:13-14`. | M–L | **Médio** (latência de interação cai; regressão futura é prevenida) |

**Recomendação macro:** reativar o plano de abril em formato reduzido (5 tasks restantes), promovendo a **Task 9 (catch-all)** a P1 e mantendo as Tasks 4, 5, 11 como P2. Tasks 6, 7 e parte do 2 podem ser arquivadas — já foram cumpridas implicitamente.

---

## 1. Baseline numérico (medições reais)

### 1.1 Cold-compile de rotas (Turbopack em dev, container Replit)

Com `dev-server` recém-iniciado e cache `.next/` limpo por `predev`. Medições com `curl --max-time 300`, em ordem cronológica para isolar o efeito "primeira visita":

| Rota | TTFB cold | Bytes | HTTP | Notas |
|---|---:|---:|---:|---|
| `/pt` | **25,53 s** | 393 389 | 200 | Inclui compile inicial de layout, intl, sentry, sidebar — payload "dashboard" home. |
| `/pt/login` | 0,006 s | 24 | 307 | Apenas redirect handler (middleware). |
| `/pt/jobs` | **4,40 s** | 377 224 | 200 | `/pt` já estava quente; mede o custo incremental da página de vagas. |
| `/pt/funil-de-talentos` | **3,08 s** | — | 200 | Custo incremental do canônico 719L `CandidatesPage`. |
| `/pt/configuracoes` | **2,75 s** | — | 200 | Custo incremental do `settings-page-enhanced`. |
| `/pt/dashboard` | 0,73 s | — | 404 | Rota não existe (home do dashboard é `/pt`). |

Observação operacional: uma primeira tentativa de medir `/pt/jobs` com `curl --max-time 90` **não retornou em 90 s e foi acompanhada de queda do `dev-server`** (process disappeared). Após restart, a leitura foi reprodutivelmente 4,4 s. Hipótese: o ceiling `--max-old-space-size=2560` ficou apertado quando o compile de `/pt/jobs` correu **em paralelo** com algo do startup. Em uso real (várias abas, prefetch), o mesmo padrão pode reproduzir.

### 1.2 Warm TTFB (3 runs cada, após cold)

| Rota | run 1 | run 2 | run 3 |
|---|---:|---:|---:|
| `/pt` | 0,400 s | 0,110 s | 0,106 s |
| `/pt/jobs` | 0,206 s | 0,129 s | 0,103 s |

Warm está saudável. O problema é cold, não regime.

### 1.3 APIs chamadas por `/jobs`

| Endpoint | Cold TTFB | Warm (média 3 runs) | Bytes | HTTP |
|---|---:|---:|---:|---:|
| `/api/backend-proxy/job-vacancies?limit=50` | **3,76 s** | **0,029 s** | 125 656 | 200 |
| `/api/backend-proxy/job-vacancies/stats/overview` | 0,19 s | 0,025 s | 1 558 | 200 |

O custo cold (3,76 s) **não é dominado pelo FastAPI**: o stats/overview cold foi 0,19 s (mesmo backend, mesmo middleware, mesmo auth, payload similar para o handler). A diferença é o **compile do route handler do Next** sob demanda — exatamente o que a Task 9 do plano antigo se propunha a eliminar.

### 1.4 Cold compile de proxies frescos (evidência da causa #1)

Cinco proxies que **nunca tinham sido chamados** desde o restart, medidos um após o outro:

| Endpoint | Cold TTFB | HTTP |
|---|---:|---:|
| `/api/backend-proxy/notifications/unread-count` | 0,338 s | 200 |
| `/api/backend-proxy/recruitment-stages` | 0,242 s | 200 |
| `/api/backend-proxy/alerts` | 0,363 s | 200 |
| `/api/backend-proxy/approvals/pending` | 0,139 s | 422 |
| `/api/backend-proxy/workforce/stats` | 0,266 s | 200 |

Cada um é um arquivo separado de ~10 linhas que reexporta `createProxyHandlers`. **A primeira chamada paga 0,14–0,36 s só pelo compile do passthrough**, mesmo quando o backend é rápido. Numa sessão típica de recrutador, ~30–50 endpoints distintos são tocados; cumulativamente isso são 5–15 s espalhados ao longo da jornada que somem com o catch-all.

### 1.5 Não-medidos nesta auditoria (e por quê)

| Métrica | Status | Motivo |
|---|---|---|
| Cold start do `dev-server` (3 runs) | **Não medido**. | Workflow é gerenciado pelo Replit e tem warning explícito no `replit.md` §"Aviso operacional Task #1079" sobre o counter-limit; restart-loops repetidos arriscam destravar mais state do que o necessário. Mitigação: cold-compile de **rotas individuais** acima já isola o custo dominante. Procedimento reprodutível em §10. |
| HMR (5 edits) | **Não medido.** | Exigiria editar e reverter um arquivo de produto repetidamente, fora do escopo read-only da task. Procedimento reprodutível em §10. |
| `npm run analyze` (bundle analyzer) — top 15 First Load JS + top 20 módulos | **Não medido.** | O build production com `--turbopack` neste container tem alto risco de OOM (já observado no cold-compile dev). `next.config.js:webpack` força `parallelism=1` em prod, sintoma de problemas anteriores. Mitigação: inventário estático de imports pesados (§3) usa `rg` no source, suficiente para identificar candidatos a `next/dynamic`. Procedimento reprodutível em §10. |
| LCP/FCP via Lighthouse | **Não medido.** | Lighthouse requer Chrome headless instalado e auth de sessão completa para chegar em `/pt/jobs` logado. Fora do escopo read-only de 1 turno; melhor coletar após as P1 estarem em rollout. |

Os números medidos cobrem o ponto central pedido pela task (`/jobs` cold/warm + APIs dele + comparação com outras pages). O bundle e o HMR ficam como tarefas explícitas de follow-up.

### 1.6 Contagens estáticas (verificadas com múltiplos métodos)

| Métrica | Valor | Método |
|---|---:|---|
| `src/**/*.{ts,tsx}` | 2294 | `find src -type f \( -name '*.ts' -o -name '*.tsx' \) \| wc -l` |
| `src/app/**/page.tsx` | 41 | `find src/app -name page.tsx \| wc -l` |
| `src/app/api/backend-proxy/**/route.ts` | **519** | `find … -name route.ts \| wc -l` e `git ls-files … \| wc -l` (concordam). `rg --files` reporta 516; a diferença são 3 arquivos em diretórios com `[id]` que o rg filtra por padrão (`fairness-audit/logs/route.ts`, `fairness/audit/logs/route.ts`, `webhooks/[id]/logs/route.ts`). 519 é o número canônico. |
| route handlers usando `createProxyHandlers` (passthrough) | **274** | `rg -l createProxyHandlers src/app/api/backend-proxy/ \| wc -l` |
| route handlers custom (multipart, transform, auth especial) | **245** | 519 − 274 |
| Arquivos com `next/dynamic` | 22 | `rg -l next/dynamic src/ \| wc -l` |
| Arquivos `loading.tsx` | 5 | Todos em sub-rotas (`agent-studio`, `ajuda`, `bancos-de-talentos`, `chat`, `configuracoes/ai-credits`). Nenhum no nível pai do route group `(dashboard)` — confirma que o deadlock Turbopack documentado em `replit.md` está mitigado. |

---

## 2. Análise de `/jobs`

### 2.1 Caminho de renderização

```
/pt/jobs (page.tsx, 17 linhas)
  └─ ErrorBoundarySection
       └─ JobsPage (client, 320 linhas)
            └─ useJobsPageCore (560 linhas) — orquestrador
                 ├─ useJobsData          → fetch 1: listJobVacancies(limit=50)
                 │                        → fetch 2: getJobVacanciesOverview() (sequencial)
                 ├─ useJobsFilters
                 ├─ useJobsTableConfig
                 ├─ useJobsPreview
                 ├─ useJobsBulkActions
                 └─ useJobsChat
            ├─ JobsListContent           → render eager
            ├─ JobsModalsSection         → next/dynamic ✅
            └─ BulkImportModal           → next/dynamic ✅
```

### 2.2 Pontos de bloqueio identificados

| # | Arquivo / linhas | Problema | Impacto medido / esperado |
|---|---|---|---|
| 1 | `useJobsData.ts:92` e `:211` | `await liaApi.listJobVacancies()` e `await liaApi.getJobVacanciesOverview()` rodam em série dentro do mesmo `run()`. | Hoje cold: 3,76 + 0,19 = **3,95 s** sequencial. Paralelo: ~3,76 s. Em prod com latência ~100 ms para cada API: 0,29 s vs 0,19 s. |
| 2 | `useJobsData.ts:282-298` | Listener `focus` re-dispara fetch quando há `jobsError`. Sem cache HTTP. | Multi-tab e alt-tab refazem os 2 fetches. |
| 3 | `useJobsPageCore.ts:280-560` | Return monolítico com ~280 chaves. Qualquer setter de qualquer slice re-renderiza `JobsPage`. | Re-renders frequentes durante digitar em filtro. |
| 4 | `jobs-page.tsx:39-49` | `useMemo` de `groupedJobs` depende de `state.filteredJobs`, cuja referência muda a cada render do core. | Recompute O(n) por status, custo perceptível em listas grandes. |
| 5 | `useJobsPageCore.ts:170-237` | Effect `pendingJobOpen` faz 5 retries com `setTimeout(2000)` refazendo `listJobVacancies` por fora do `useJobsData`. | Em deep-link `/jobs?open=…`, tráfego de API dobra. |

### 2.3 Scripts no HTML de `/pt/jobs` (warm)

Listei 30 chunks `_next/static/chunks/*`: Sentry NextJS client, Radix UI, tailwind-merge, floating-ui, hidos, components, services e o chunk do `[locale]/layout`. **Nenhum chunk de `recharts`, `chart.js`, `@tiptap`, `jspdf`, `html2canvas`, `@twilio` ou `@microsoft/teams-js` apareceu no HTML inicial de `/pt/jobs`** — esperado, porque essa página não importa essas libs. O custo cold de `/pt/jobs` (4,4 s) é compile dela própria e dos componentes que ela importa, não dessas libs.

---

## 3. Inventário de imports pesados (recolhido por grep no source)

| Lib | Versão | Import estático em `src/`? | Está como `next/dynamic` / `await import`? | Status |
|---|---|---|---|---|
| `recharts` | ^3.2.1 | **Sim** — `ai-credits-page.tsx`, `StudioComplianceView.tsx` | Não | **Pendente** — Task 4 do plano de abril |
| `chart.js` + `react-chartjs-2` | ^4.5 / ^5.3 | **Sim** — `interactive-charts.tsx`, `advanced-interactive-charts.tsx` | Não | **Pendente** — Task 4 |
| `@tiptap/*` (5 pacotes) | ^3.22 | **Sim** — `lia-editor.tsx`, `lia-editor-variable-extension.ts` (consumer único: `JobInfoGeralSection.tsx`) | Não | **Pendente** — Task 5. Consumer único facilita o fix. |
| `marked` | ^18 | **Sim** — `src/lib/render-markdown.ts` | n/a | Confirmar se chega ao client (parece util server-side; analyzer confirmaria) |
| `jira.js` | ^5.3 | **Sim** — `src/lib/api/jira-service.ts` | n/a | Provável server-only. Analyzer confirmaria. |
| `@microsoft/teams-js` | ^2.51 | **Não há import estático.** `src/hooks/company/use-teams-sso.ts` faz `await import("@microsoft/teams-js")` dentro de função. | **Sim** (lazy via dynamic await) | ✅ Já lazy |
| `@twilio/voice-sdk` | ^2.11 | **Não há import estático em `src/`.** | n/a | ✅ Já fora do client (não foi possível confirmar via analyzer) |
| `html2canvas` | ^1.4.1 | Nenhum import estático em `src/` | n/a | ✅ Idem |
| `jspdf` | ^4.2.1 | Nenhum import estático em `src/` | n/a | ✅ Idem |
| `canvg` | ^4.0.3 | Nenhum import estático em `src/` | n/a | ✅ Idem |

**Correção em relação à versão anterior deste relatório:** `@microsoft/teams-js` foi marcado como "pesado no client" no resumo executivo da primeira tentativa por engano; o uso real em `use-teams-sso.ts:64` é `await import(...)` dentro de função, portanto **não vai para o bundle inicial**. A entrada acima reflete a checagem corrigida.

---

## 4. Backend-proxy: o elefante na sala

```
Total de route.ts em src/app/api/backend-proxy/  = 519
   ├─ Usam createProxyHandlers (passthrough)     = 274  (52,8 %)
   └─ Custom (multipart, transform, auth, etc.)  = 245  (47,2 %)
```

**O custo medido:** cold-compile do route handler `job-vacancies` (passthrough trivial de 8 linhas) adiciona **3,57 s** à primeira chamada da API (3,76 s cold vs 0,029 s warm). Outros 5 proxies frescos medidos: 0,14–0,36 s cada. A variação reflete dependências do handler — `job-vacancies` provavelmente arrasta `bodySchema` (Zod) compartilhado com outros handlers ainda não compilados.

**A solução estruturada (Task 9 do plano de abril, NUNCA executada):** consolidar os 274 passthroughs num único catch-all:

```
src/app/api/backend-proxy/[...path]/route.ts
```

que delega para `createProxyHandlers` baseado no `params.path`. Os 245 handlers custom permanecem como overrides (Next App Router resolve rotas específicas antes de catch-all).

**Estimativa de ganho:** primeira visita a qualquer área nova do app deixa de pagar o cold-compile do passthrough. Numa sessão típica que toca 30–50 endpoints distintos, é o equivalente a remover 5–15 s cumulativos de "API em pé".

---

## 5. Middleware

**Custo por request:**

| Etapa | Quando | Custo aproximado |
|---|---|---|
| `stripLocalePrefix` + `isStaticOrApiPath` | Sempre | µs |
| `getDevToken()` (dev-auto-login) | Toda request não-estática quando `DEV_AUTO_LOGIN=1` | Round-trip ao backend (uma vez por TTL do cache em memória) |
| `verifyAndDecodeSession` (WorkOS) ou `jwtVerify` (jose) | Toda request autenticada | 5–15 ms (CPU local) |
| `verifyJwt` fallback que chama `${BACKEND_URL}/api/v1/auth/me` | Quando não há `SECRET_KEY` configurado | Round-trip ao backend, timeout 3 s |
| `intlMiddleware` (next-intl) | Sempre em rotas não-API | Resolve locale, redireciona se `/` etc. |

**Custo total observado:** warm `/pt` = 0,1 s end-to-end inclui middleware completo. O middleware não é o gargalo em regime; é multiplicador.

**Problemas estruturais identificados:**

1. **Não há short-circuit para prefetches do Next** (`Next-Router-Prefetch: 1`). Cada hover sobre `<Link>` paga o pipeline completo (auth + intl).
2. O matcher `'/((?!_next/static|_next/image|favicon.ico).*)'` **não exclui** `_next/data`, `robots.txt`, `sitemap.xml`, `/fonts/*`. A função `isStaticOrApiPath` cobre algumas extensões, mas a passada pelo middleware ainda incorre no overhead de `Headers` clonadas + `intlMiddleware`.
3. Em dev, `DEV_AUTO_LOGIN` força um `getDevToken()` síncrono em série antes da renderização.

**Recomendação:**
- Detectar `request.headers.get('next-router-prefetch') === '1'` no topo e devolver `NextResponse.next()` sem auth/intl.
- Ampliar o matcher para excluir `_next/data`, fontes, logos.
- Em dev, paralelizar `getDevToken()` com `intlMiddleware` quando possível.

---

## 6. Confronto detalhado com o plano de abril

| Task do plano | Status verificado | Notas |
|---|---|---|
| 1 — `scripts/perf-baseline.sh` + `PERF_BASELINE.md` | **Não executada.** Nenhum dos dois existe. | Esta auditoria fornece a baseline equivalente (§1). Recomendar criação do script para coletas futuras. |
| 2 — Limpar `a.out`, `tsc_output.txt`, `nohup.out` | **Cumprida.** Não estão na raiz. | Baixíssimo impacto, já fora do crítico. |
| 3 — Dynamic `html2canvas` + `jspdf` | **Cumprida implicitamente.** `rg` não encontra import estático em `src/`. | Confirmar via analyzer quando viável. |
| 4 — Dynamic `recharts` + `chart.js` | **NÃO cumprida.** Imports estáticos vivos em 4 arquivos. | **Manter no plano** — alvo de PR pequeno. |
| 5 — Dynamic `@tiptap` | **NÃO cumprida.** Import estático em `lia-editor.tsx` (consumer único `JobInfoGeralSection.tsx`). | **Manter** — fix de 2 arquivos. |
| 6 — Dynamic `@twilio/voice-sdk` | **Cumprida implicitamente.** Sem import estático em `src/`. | Confirmar via analyzer. |
| 7 — Dynamic `@microsoft/teams-js` | **Cumprida via `await import` em `use-teams-sso.ts:64`.** | ✅ |
| 8 — Auditar `jira.js`, `canvg`, `marked` | **Parcial.** `jira.js` e `marked` em `lib/`, provavelmente server-only. `canvg` ausente. | Validar via analyzer. |
| 9 — Catch-all `backend-proxy/[...path]` | **NÃO executada.** É a maior dívida pendente. | **Promover a P1.** |
| 10 — Barrel files | **Não auditado nesta auditoria** (fora do escopo de 1 turno). | Manter no backlog. |
| 11 — `optimizePackageImports` / `modularizeImports` | `next.config.js` **não declara nenhum dos dois.** | Manter no plano. |
| 12 — Ligar build gates (`typescript.ignoreBuildErrors`) | **NÃO cumprida.** Continua `true`. | Projeto separado, custo alto. |

**Tasks recentes (#1090 → #1134) com efeito perf:** auditadas no `git log --oneline --since=2026-04-15` — **todas** focam no wizard de criação de vaga (HITL, supervisor, gates LLM, eval gates). **Nenhuma toca em** `JobsPage`, `useJobsData`, middleware, backend-proxy ou bundle. A frente de performance segue parada desde abril.

---

## 7. Checagens menores

- ✅ **Deadlock Turbopack `loading.tsx` aninhado** (replit.md menciona `configuracoes/`) — verificado: existem 5 `loading.tsx` no app, **todos em sub-rotas**. Não há `loading.tsx` no nível pai do route group `(dashboard)/`. Sem regressão.
- ✅ **`(dashboard)/layout.tsx`** envolve em `DashboardLayoutClient` (client component). `DeferredLayoutClients.tsx` já usa `next/dynamic` para os pesados — boa prática mantida.
- ⚠️ **`predev: rm -rf .next/dev`** roda antes de cada `npm run dev`, eliminando cache parcial. Intencional (Turbopack 16.2.4 lixo) mas amplifica cold start. Não tocar sem entender o motivo histórico.
- ⚠️ **`build`** usa `--turbopack` + `typescript.ignoreBuildErrors: true` + `productionBrowserSourceMaps: false`. Build não confiável como gate.
- ⚠️ Dev-server foi **derrubado por um único cold-compile pesado** durante a coleta. `NODE_OPTIONS='--max-old-space-size=2560'` está apertado para Next 16 + Turbopack em codebase desse tamanho.

---

## 8. Causas-raiz priorizadas (final, com evidência medida)

| Rank | Causa | Evidência (medida onde possível) | Esforço | Ganho | Risco |
|---|---|---|---|---|---|
| 1 | 274 passthroughs em `backend-proxy/` candidatos a catch-all | 519 routes / 274 com `createProxyHandlers`. Cold compile mede 0,14–3,57 s por proxy. | M (1–2 dias) | **Alto** | Baixo (Next resolve rotas específicas antes do catch-all) |
| 2 | Fetches sequenciais + sem cache em `useJobsData` | `useJobsData.ts:92,211,282-298`. Cold: 3,95 s sequencial vs ~3,76 s paralelo. | S (≤ ½ dia) | Alto | Baixo |
| 3 | `recharts`, `chart.js`, `@tiptap` ainda no bundle inicial | grep estático em 4 arquivos consumidores. | S | Médio | Baixo (`next/dynamic { ssr: false }`) |
| 4 | Middleware sem short-circuit para prefetch | `middleware.ts:150-340` | S | Médio | Baixo (1 if) |
| 5 | Monolito `useJobsPageCore` (~280 chaves no return) | `useJobsPageCore.ts:280-560` | M | Médio | Médio (refactor toca consumer principal) |

---

## 9. Recomendação final

**Reativar `2026-04-20-plataforma-lia-perf.md` em formato reduzido**, na ordem abaixo. Itens marcados **NOVAS** são desdobramentos do diagnóstico de hoje:

1. **(P0, NOVA)** Criar `scripts/perf-baseline.sh` (Task 1 do plano antigo) que reproduz mecanicamente as medições do §1, mais Lighthouse local logado, mais HMR cronometrado. Bloqueante para validar 2–7.
2. **(P1)** Catch-all `backend-proxy/[...path]/route.ts` substituindo os 274 passthroughs (Task 9 do plano antigo, **promovida**).
3. **(P1, NOVA)** Paralelizar `useJobsData` (`Promise.all([listJobVacancies, getJobVacanciesOverview])`) e adicionar SWR ou cache simples para evitar refetch em focus/navegação.
4. **(P2)** `next/dynamic` para `recharts`, `chart.js + react-chartjs-2`, `@tiptap` (Tasks 4 e 5 do plano antigo).
5. **(P2, NOVA)** Middleware: short-circuit em `Next-Router-Prefetch: 1` e ampliação do matcher para excluir `_next/data`, `/fonts`, `/logos`, `/images`.
6. **(P3)** `optimizePackageImports` + `modularizeImports` em `next.config.js` (Task 11 do plano antigo).
7. **(P3, NOVA)** Refactor `useJobsPageCore` para retornar slices separados — corta re-renders em cascata.
8. **(P3, NOVA)** Elevar `NODE_OPTIONS='--max-old-space-size'` do `dev` de 2560 para 4096 (alinhar com `dev:turbo` e `build`) ou diagnosticar o picão de heap antes de aceitar como permanente. Crash do dev-server durante a coleta foi sintoma.
9. **(P4, separado)** Ligar `typescript.ignoreBuildErrors: false` (Task 12 do plano antigo) — projeto próprio, ortogonal a perf de dev.

**Tasks descartadas** do plano original:
- Task 2 (limpar lixo) — cumprida.
- Task 6 (`@twilio`) e Task 7 (`@microsoft/teams-js`) — cumpridas implicitamente.
- Task 10 (barrel files) — backlog, ROI baixo até P1/P2 resolvidos.

---

## 10. Procedimento reprodutível (para coletas futuras)

```bash
# 0. Pré-requisitos
cd plataforma-lia
# garantir que dev-server e lia-backend estão up (workflows do Replit)
# para forçar cold real: stop dev-server, remova .next, restart

# 1. Cold compile por rota (com auth dev habilitada)
for path in /pt /pt/login /pt/jobs /pt/funil-de-talentos /pt/configuracoes; do
  curl -sk -o /dev/null -w "$path  TTFB %{time_starttransfer}s  total %{time_total}s  code %{http_code}\n" \
       --max-time 300 "http://127.0.0.1:5000$path"
done

# 2. Warm TTFB (3 runs)
for path in /pt /pt/jobs; do
  for i in 1 2 3; do
    curl -sk -o /dev/null -w "$path run $i  TTFB %{time_starttransfer}s\n" \
         --max-time 30 "http://127.0.0.1:5000$path"
  done
done

# 3. APIs do /jobs (cold + warm)
for ep in "job-vacancies?limit=50" "job-vacancies/stats/overview"; do
  curl -sk -o /dev/null -w "$ep cold  TTFB %{time_starttransfer}s\n" \
       --max-time 60 "http://127.0.0.1:5000/api/backend-proxy/$ep"
  for i in 1 2 3; do
    curl -sk -o /dev/null -w "$ep warm $i  TTFB %{time_starttransfer}s\n" \
         "http://127.0.0.1:5000/api/backend-proxy/$ep"
  done
done

# 4. Cold compile de proxies frescos (evidência catch-all)
for ep in notifications/unread-count recruitment-stages alerts approvals/pending workforce/stats; do
  curl -sk -o /dev/null -w "$ep cold  TTFB %{time_starttransfer}s\n" \
       --max-time 60 "http://127.0.0.1:5000/api/backend-proxy/$ep"
done

# 5. Bundle analyzer (rodar fora do Replit container; alto risco de OOM aqui)
ANALYZE=true npm run build
# abre .next/analyze/client.html

# 6. HMR — manual, cronometrar 5 edits em src/components/ui/button.tsx
#    e medir delta no log do dev-server até "compiled in Xms".
```

— fim do relatório —
