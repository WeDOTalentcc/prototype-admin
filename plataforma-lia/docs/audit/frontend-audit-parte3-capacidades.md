# Auditoria Frontend — Parte 3: Capacidades (Dimensões 11-15)

**Data:** 2026-03-30
**Escopo:** Frontend da Plataforma LIA (plataforma-lia/src/)
**Framework:** Next.js (App Router) + React + Tailwind CSS
**Tipo:** Diagnóstico — sem correções de código

---

## Resumo Executivo

| Dimensão | Score | Status |
|----------|-------|--------|
| 11 — Internacionalização e Localização | 0/3 | Ausente |
| 12 — SEO e Metadados | 1/3 | Mínimo |
| 13 — Compliance e Legal | 2/3 | Parcial |
| 14 — Qualidade de Produto e UX | 2/3 | Bom com lacunas |
| 15 — Testabilidade e Cobertura | 2/3 | Fundação sólida |

**Score Médio Parte 3:** 1.4/3

---

## Dimensão 11 — Internacionalização e Localização

**Score: 0/3** — i18n inexistente; todo o frontend é monolíngue pt-BR hardcoded.

### Verificações Realizadas

#### 11.1 Sistema de i18n configurado
- **Achado Crítico:** Não há react-i18next, next-intl, ou qualquer biblioteca de i18n instalada ou configurada.
- **Evidência:** Busca por `i18n`, `react-i18next`, `useTranslation`, `t(` em `plataforma-lia/src/` retorna zero matches de uso real de i18n. Os resultados encontrados são:
  - `plataforma-lia/src/lib/schemas/*.ts` — contêm `.t()` de Zod (mensagens de validação), não de i18n.
  - `plataforma-lia/src/app/layout.tsx:44` — `<html lang="pt-BR">` hardcoded.

#### 11.2 Strings hardcoded nos templates
- **Achado Crítico:** 100% das strings de UI estão hardcoded em português em todos os componentes.
- **Evidências:**
  - `plataforma-lia/src/app/page.tsx:12` — `"Carregando WeDO Talent..."` hardcoded.
  - `plataforma-lia/src/components/error-boundary.tsx:80-83` — `"Algo deu errado"`, `"Ocorreu um erro inesperado..."` hardcoded.
  - `plataforma-lia/src/app/privacidade/page.tsx:21-26` — todos os labels de REQUEST_TYPES hardcoded.
  - `plataforma-lia/src/components/ui/empty-state.tsx` — recebe `title`/`description` como props (bom padrão), mas os chamadores passam strings hardcoded.

#### 11.3 Formatação de datas/números/moeda
- **Achado Importante:** Datas são formatadas com `toLocaleDateString('pt-BR')` hardcoded (não dinâmico por locale do usuário).
- **Evidência:** `plataforma-lia/src/app/privacidade/page.tsx:475` — `new Date(trackingResult.created_at).toLocaleDateString('pt-BR')`.
- **Positivo:** Uso de `toLocaleDateString` (API Intl nativa) em vez de formatação manual. ~20+ arquivos usam `new Date()`/`toLocaleDateString`.
- **Achado:** Não há uso de `Intl.NumberFormat` para moedas. Formatação de CPF e telefone (`plataforma-lia/src/app/privacidade/page.tsx:55-68`) usa padrão brasileiro hardcoded.

#### 11.4 Pluralização
- **Verificado:** Não há sistema de pluralização. Strings condicionais usam padrões simples (ex: `item` vs `items`), sem ICU MessageFormat.

#### 11.5 Textos que quebram layout em outros idiomas
- **N/A** — Como não há suporte a outros idiomas, não é testável. O layout assume larguras de texto pt-BR.

#### 11.6 Imagens com texto embutido
- **Verificado:** Imagens em `plataforma-lia/public/` são fotos de candidatos e logos. Não foram encontradas imagens com texto embutido significativo.

#### 11.7 Timezone (UTC vs local)
- **Achado Melhoria:** Datas são criadas com `new Date()` sem tratamento explícito de timezone. O comportamento depende do timezone do browser do usuário.

#### 11.8 RTL (Right-to-Left)
- **Verificado:** Nenhum suporte a RTL. `<html lang="pt-BR">` sem atributo `dir`.

### Estimativa de custo de retrofit de i18n
- **Alto esforço:** ~200+ arquivos com strings hardcoded. Retrofit requer:
  1. Instalar react-i18next/next-intl
  2. Extrair todas as strings para arquivos de tradução
  3. Substituir strings por chaves `t('key')`
  4. Adaptar formatação de datas/números para usar locale dinâmico
  5. Estimativa: 3-5 sprints para cobertura completa

### Classificação dos Achados
- **Críticos:** Ausência total de sistema de i18n; impossível operar em outro idioma.
- **Importantes:** Locale hardcoded em formatações de data.
- **Melhorias:** Timezone implícito; sem RTL.

---

## Dimensão 12 — SEO e Metadados

**Score: 1/3** — Metadados básicos existem, mas faltam sitemap, robots.txt, Open Graph, e otimizações fundamentais.

### Verificações Realizadas

#### 12.1 SPA pura vs SSR/SSG
- **Achado Importante:** Aplicação usa Next.js App Router, porém a maioria das páginas é `"use client"` (SPA-like). O `layout.tsx:1` exporta `export const dynamic = 'force-dynamic'`, desabilitando SSG para todas as rotas.
- **Evidência:** `plataforma-lia/src/app/layout.tsx:1` — `export const dynamic = 'force-dynamic'`.
- **Impacto:** Perde benefícios de SSR/SSG para SEO. Cada página é renderizada dinamicamente.

#### 12.2 Hydration sem erros de mismatch
- **Verificado:** Layout usa `suppressHydrationWarning` em `<html>`, `<head>`, e `<body>` (`layout.tsx:44-49`). Isso oculta erros de hydration em vez de resolvê-los.
- **Achado Melhoria:** `suppressHydrationWarning` deve ser usado apenas para atributos que legitimamente diferem (ex: theme). O uso em `<head>` e `<body>` é aceitável para ThemeProvider, mas pode mascarar bugs reais.

#### 12.3 Sitemap e robots.txt
- **Achado Crítico:** Não existe `sitemap.xml`, `sitemap.ts`, `robots.txt`, ou `robots.ts` em nenhum dos locais esperados:
  - `plataforma-lia/public/sitemap.xml` — ausente
  - `plataforma-lia/public/robots.txt` — ausente
  - `plataforma-lia/src/app/sitemap.ts` — ausente
  - `plataforma-lia/src/app/robots.ts` — ausente

#### 12.4 Canonical URLs
- **Achado Importante:** Nenhuma tag `<link rel="canonical">` encontrada em qualquer página.

#### 12.5 Title/Description únicos por página
- **Achado Importante:** `layout.tsx:33-36` define metadata global:
  ```ts
  export const metadata: Metadata = {
    title: "WeDo Talent - Plataforma de Recrutamento com IA",
    description: "Plataforma de recrutamento inteligente com LIA...",
  }
  ```
- Algumas páginas internas definem `metadata` ou `generateMetadata` (encontrados em ~20 arquivos em `src/app/`), o que é positivo.
- **Achado:** Muitas páginas `"use client"` não exportam metadata (client components não podem exportar metadata no App Router).

#### 12.6 Open Graph e Twitter Cards
- **Achado Crítico:** Nenhuma tag Open Graph (`og:title`, `og:image`, etc.) ou Twitter Card encontrada em metadata exports. Busca por `og:`, `twitter:`, `openGraph` retornou zero matches em código de app.

#### 12.7 Structured Data (JSON-LD)
- **Achado Crítico:** Nenhum structured data (JSON-LD) encontrado. A página de vagas (`/vagas/[slug]`) seria candidata natural para `JobPosting` schema.

#### 12.8 URLs amigáveis e redirecionamentos
- **Verificado:** Next.js App Router gera URLs baseadas na estrutura de diretórios — URLs são amigáveis por padrão (ex: `/funil-de-talentos/candidato/[id]`).
- **Achado:** `next.config.js:5` define `trailingSlash: true` — URLs terminam com `/`, o que é consistente.
- **Achado:** Não há arquivo de redirecionamentos 301 configurado em `next.config.js`.

#### 12.9 Core Web Vitals
- **Achado Importante:** `next.config.js:63` define `Cache-Control: no-store, no-cache, must-revalidate` para TODAS as rotas (`/:path*`). Isso impede qualquer cache de assets estáticos, prejudicando LCP e performance.
- **Achado:** `images.unoptimized: true` em `next.config.js:26` desabilita a otimização de imagens do Next.js.

#### 12.10 Alt em imagens
- **Verificado:** ~25 usos de `<img>` e `<Image>` encontrados. Busca por `alt=` encontrou matches na maioria dos componentes com imagens, mas a cobertura não é 100% verificável sem renderização.

### Classificação dos Achados
- **Críticos:** Ausência de sitemap.xml, robots.txt, Open Graph, JSON-LD.
- **Importantes:** `force-dynamic` desabilita SSG; Cache-Control no-store global; imagens não otimizadas; falta canonical URLs.
- **Melhorias:** suppressHydrationWarning amplo; metadata não uniforme entre páginas.

---

## Dimensão 13 — Compliance e Legal

**Score: 2/3** — Infraestrutura LGPD sólida (portal de privacidade, consentimento, exclusão), mas faltam banner de cookies e controle de scripts de terceiros.

### Verificações Realizadas

#### 13.1 Banner de cookies com opção de rejeitar
- **Achado Crítico:** Não foi encontrado nenhum componente de banner de cookies ou consent manager no frontend. Busca por `cookie`, `Cookie`, `consent`, `banner` em componentes não retornou componente de cookie consent.
- **Evidência:** Busca em `plataforma-lia/src/` por `cookie` retornou apenas referências a dados de tracking da plataforma, não a um banner de cookies para o usuário.

#### 13.2 Consentimento verificado antes de analytics/tracking
- **Achado Importante:** Não há scripts de analytics (Google Analytics, gtag, GTM) carregados no frontend. O Sentry está configurado condicionalmente (`sentry.client.config.ts:12` — `if (SENTRY_DSN)`), mas sem verificação de consentimento.
- **Evidência:** `plataforma-lia/src/sentry.client.config.ts:10-12` — carrega Sentry se DSN estiver configurada, sem checar consentimento.

#### 13.3 Scripts de terceiros condicionais ao consentimento
- **Verificado:** O projeto não carrega scripts de terceiros de analytics/marketing. O único script de terceiro é Sentry (error monitoring), que não é condicional ao consentimento.
- **Achado Melhoria:** Quando analytics forem adicionados no futuro, precisarão de gate de consentimento.

#### 13.4 Dados pessoais em console.log
- **Verificado:** Busca por `console.(log|warn|error)` com padrões de PII (email, password, token, cpf, nome, phone) retornou **zero matches**. Console logs encontrados (~4 arquivos com `console.log`) não contêm dados pessoais.
- **Status:** Conforme.

#### 13.5 Dados pessoais em query params
- **Verificado:** URL de SSO (`auth-service.ts:95-101`) transmite `organization`, `connection`, `email` via query params. Email em query param é um risco de PII em logs de servidor/CDN.
- **Achado Melhoria:** `plataforma-lia/src/services/auth-service.ts:98` — `params.set('email', options.email)` em URL de redirect SSO.

#### 13.6 localStorage sem criptografia
- **Achado Importante:** Tokens JWT são armazenados em `localStorage` sem criptografia:
  - `plataforma-lia/src/services/auth-service.ts:77-78` — `localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)`
  - `plataforma-lia/src/services/lia-api/base.ts:9` — `localStorage.getItem('access_token')`
- **Outros dados em localStorage:** sidebar state, table configs, navigation persistence, recent items, conversation recents — nenhum contém PII diretamente.
- **Achado:** `plataforma-lia/src/contexts/ClientContext.tsx:59` — armazena dados de cliente selecionado em localStorage (pode conter nome da empresa).

#### 13.7 Limpeza de dados no logout
- **Verificado:** `auth-service.ts:82-87` — `clearTokens()` remove `ACCESS_TOKEN`, `REFRESH_TOKEN`, `AUTH_METHOD` do localStorage.
- **Achado Importante:** Logout NÃO limpa outros dados do localStorage: sidebar state, table configs, navigation persistence, recent items, conversation recents, client context. Esses dados persistem após logout.
- **Evidência:** `plataforma-lia/src/services/auth-service.ts:238-245` — `logout()` chama apenas `clearTokens()` ou `logoutSSO()`, sem limpar demais storages.

#### 13.8 Links de política de privacidade e termos de uso
- **Verificado — Conforme:** Links existem em múltiplos pontos:
  - `plataforma-lia/src/app/trust/page.tsx:522` — Link para `/privacidade`
  - `plataforma-lia/src/app/register/page.tsx:220` — "Termos de Uso" no formulário de registro
  - `plataforma-lia/src/app/aceitar-convite/page.tsx:363` — Link "Termos de Uso" com href `/privacidade`
  - `plataforma-lia/src/app/portal/data-request/[token]/page.tsx:1081-1101` — Links dinâmicos para privacy_policy_url e terms_url

#### 13.9 Exclusão de conta e exportação de dados (LGPD)
- **Verificado — Conforme:** Portal completo de privacidade implementado:
  - `plataforma-lia/src/app/privacidade/page.tsx` — Formulário LGPD Art. 18 com 5 tipos de solicitação: acesso, correção, exclusão, portabilidade, explicação de decisão automatizada.
  - `plataforma-lia/src/app/portal/data-request/[token]/page.tsx` — Portal do titular de dados.
  - `plataforma-lia/src/services/admin/data-subject-requests-service.ts` — Serviço de DSR.
  - `plataforma-lia/src/services/admin/consent-management-service.ts` — Serviço de consentimento.
  - `plataforma-lia/src/app/admin/compliance/lgpd/` — Painel administrativo LGPD (consentimentos, portal-titular, transferências).

### Classificação dos Achados
- **Críticos:** Ausência de banner de cookies/consent manager.
- **Importantes:** Tokens JWT em localStorage sem criptografia; logout não limpa todos os dados do localStorage; Sentry sem gate de consentimento.
- **Melhorias:** Email em query params de SSO; dados de cliente em localStorage.

---

## Dimensão 14 — Qualidade de Produto e UX

**Score: 2/3** — Boa infraestrutura de loading states, error handling e toasts. Faltam confirmações em ações destrutivas em alguns pontos, e edge cases de responsividade.

### Verificações Realizadas

#### 14.1 Loading states em operações assíncronas
- **Verificado — Bom:** ~30+ arquivos implementam padrões de loading state (`isLoading`, `setLoading`, `Carregando`).
- **Evidências positivas:**
  - `plataforma-lia/src/app/page.tsx:7-16` — `LoadingScreen` component com spinner e texto.
  - `plataforma-lia/src/app/privacidade/page.tsx:45-46` — `submitting` e `tracking` states para operações de formulário.
  - `plataforma-lia/src/components/ui/loading.tsx` — Componente de loading dedicado com Skeleton.
  - `plataforma-lia/src/app/page.tsx:20` — `<Suspense fallback={<LoadingScreen />}>` na raiz.

#### 14.2 Mensagens de erro claras e acionáveis
- **Verificado — Bom:**
  - `plataforma-lia/src/components/error-boundary.tsx:80-106` — ErrorBoundary global com mensagens claras em pt-BR ("Algo deu errado", "Ocorreu um erro inesperado"), botões de retry e reload.
  - `plataforma-lia/src/app/privacidade/page.tsx:91-100` — Error handling com mensagens específicas (ex: "Solicitação não encontrada. Verifique o código informado.").
  - `plataforma-lia/src/app/privacidade/page.tsx:355-360` — Exibição visual de erros com ícone e cor.

#### 14.3 Empty states
- **Verificado — Bom:**
  - `plataforma-lia/src/components/ui/empty-state.tsx` — Componente reutilizável `EmptyState` com ícone, título, descrição e ação opcional.
  - Utilizado em 8+ componentes: `LiaSplitPanel`, `LiaChatPanel`, `ClientTable`, `jobs-page`, `job-kanban-page`, `favorites-tab`, `KanbanColumn`, `CandidatesTable`.

#### 14.4 Skeleton loaders
- **Verificado — Presente:**
  - `plataforma-lia/src/components/ui/skeleton.tsx` — Componente `Skeleton` com `animate-pulse` e `motion-reduce:animate-none`.
  - Utilizado em 18+ arquivos incluindo admin pages, kanban, tables.

#### 14.5 Confirmação antes de ações destrutivas
- **Verificado — Parcial:**
  - `plataforma-lia/src/components/ui/alert-dialog.tsx` — Componente AlertDialog disponível (Radix UI).
  - Utilizado em 20+ componentes para confirmações: `reveal-credits-modal`, `ScreeningStatusModal`, `expanded-chat-modal`, `credit-confirmation-dialog`, `SourceChangeConfirmModal`, `GlobalExpansionConfirmModal`.
  - **Achado Melhoria:** Não foi possível verificar se TODAS as ações destrutivas (delete de candidato, exclusão de vaga, etc.) passam por confirmação sem renderizar a app.

#### 14.6 Validação inline
- **Verificado — Parcial:**
  - `plataforma-lia/src/app/privacidade/page.tsx:366` — `disabled` condicional baseado em campos obrigatórios (`!requestType || !name || !email || !cpf`).
  - `plataforma-lia/src/app/register/page.tsx:35-36` — Validação de aceite de termos.
  - `plataforma-lia/src/lib/schemas/*.ts` — Schemas Zod para validação em múltiplos formulários.
  - **Achado Melhoria:** Validação é bloqueante (disable do botão), mas nem sempre há feedback visual inline (mensagens de erro por campo).

#### 14.7 Deep linking e back/forward do browser
- **Achado Importante:** A aplicação é primariamente SPA com navegação interna por estado React. Muitas páginas usam App Router (deep linking via URL funciona), mas painéis internos (modais, tabs, filtros) não refletem na URL.
- **Evidência:** `plataforma-lia/src/app/page.tsx` renderiza `DashboardApp` como SPA monolítica; tabs e painéis internos usam estado React sem `useSearchParams` ou `pushState`.

#### 14.8 Timeout de sessão
- **Verificado:** Não foi encontrado mecanismo de timeout de sessão no frontend. JWT expira pelo backend, mas não há timer no frontend para alertar o usuário ou redirecionar para login.

#### 14.9 Edge cases (responsividade)
- **Verificado — Bom:** Componentes usam classes responsivas do Tailwind extensivamente (`md:grid-cols-2`, `max-w-4xl`, `mx-auto`).
- **Achado:** `plataforma-lia/src/app/privacidade/page.tsx:248` — `grid-cols-1 md:grid-cols-2` para cards de tipo de solicitação.
- **Achado Melhoria:** Não há viewport meta tag explícita no layout (Next.js inclui por padrão).

#### 14.10 Toasts/Notificações
- **Verificado — Bom:**
  - Dois sistemas de toast coexistem:
    1. `plataforma-lia/src/components/ui/toaster.tsx` + `use-toast.ts` — Radix Toast com `ToastProvider aria-live="polite"`.
    2. `plataforma-lia/src/app/layout.tsx:64` — Sonner (`<SonnerToaster position="top-right" />`).
  - **Achado Importante:** `TOAST_REMOVE_DELAY = 1000000` em `use-toast.ts:9` — delay de ~16 minutos para remoção automática. Toasts ficam visíveis por tempo excessivo ou dependem de dismiss manual.
  - **Achado Melhoria:** Dois sistemas de toast simultâneos podem causar inconsistência na UX.

#### 14.11 Acessibilidade (prefers-reduced-motion)
- **Verificado — Conforme:**
  - `plataforma-lia/src/app/globals.css:227-235` — Media query `prefers-reduced-motion: reduce` com `animation-duration: 0.01ms`, `transition-duration: 0.01ms`.
  - Componentes usam `motion-reduce:animate-none` (ex: `skeleton.tsx:9`, `error-boundary.tsx:96`, `page.tsx:11`).

### Classificação dos Achados
- **Críticos:** Nenhum.
- **Importantes:** `TOAST_REMOVE_DELAY` de ~16min efetivamente não auto-dismiss; ausência de timeout de sessão; deep linking limitado em painéis internos.
- **Melhorias:** Dois sistemas de toast; validação inline sem feedback por campo; estados internos não refletidos na URL.

---

## Dimensão 15 — Testabilidade e Cobertura

**Score: 2/3** — Boa fundação de testes com 4 camadas (unit, hooks, e2e, storybook) e CI pipeline completo (GitHub Actions com lint, type check, testes, build). Cobertura de componentes ainda baixa (~5%) e deploy não depende formalmente do CI.

### Verificações Realizadas

#### 15.1 Inventário de tipos de teste

**Testes unitários (Vitest — unit project):**
- Localização: `plataforma-lia/src/components/__tests__/`
- Arquivos: 3 arquivos de teste
  - `ml-insights-card.test.tsx` (22 assertions)
  - `lia-score-card.test.tsx` (12 assertions)
  - `fairness-warning-banner.test.tsx` (11 assertions)
- **Achado:** Testes de componentes são limitados — testam apenas exports e estrutura, sem renderização DOM completa. Nota: `@testing-library/dom@^10.4.1` está listado como dependência em `package.json:51`, então a limitação é uma escolha de design dos testes atuais, não uma restrição de ambiente.

**Testes de hooks (Vitest — hooks project, jsdom):**
- Localização: `plataforma-lia/src/hooks/__tests__/`
- Arquivos: 21 arquivos de teste
  - `use-candidate-filters.test.ts` (61 assertions)
  - `use-candidate-selection.test.ts` (65 assertions)
  - `use-candidates-list.test.ts` (51 assertions)
  - `use-float-streaming.test.ts` (34 assertions)
  - `use-ai-credits.test.ts` (41 assertions)
  - `use-ml-predictions.test.ts` (34 assertions)
  - `use-agent-streaming-reconnect.test.ts` (63 assertions)
  - `use-action-intent.test.ts` (69 assertions)
  - E 13 mais hooks testados.
- **Qualidade:** Testes usam `renderHook`/`act` de `@testing-library/react`. Testam estado inicial, transições, edge cases.
- **Setup:** `plataforma-lia/src/hooks/__tests__/setup.ts` configurado para jsdom.

**Testes de componentes adicionais:**
- `plataforma-lia/src/components/lia-float/__tests__/LiaChatPanel-p2c.test.tsx` — teste isolado de componente LIA.
- `plataforma-lia/src/components/pages/candidates/__tests__/CandidatesTable.test.tsx` — teste de tabela de candidatos.

**Testes E2E (Playwright):**
- Localização: `plataforma-lia/e2e/tests/`
- Arquivos: 13 specs em 4 áreas:
  - `auth/login.spec.ts` (5 testes — login, validação, credenciais inválidas)
  - `wizard/step1-info-basica.spec.ts` a `step7-revisao.spec.ts` (7 specs por step)
  - `wizard/complete-flow.spec.ts` (5 assertions)
  - `wizard/test_job_creation_lia.spec.ts` (16 assertions)
  - `chat/conversation-memory.spec.ts` (18 assertions)
  - `chat/tool-calling.spec.ts` (20 assertions)
  - `kanban/move-candidate.spec.ts` (14 assertions)
- **Fixtures:** `plataforma-lia/e2e/fixtures/auth.fixture.ts`, `wizard-conversation.fixture.ts`

**Testes Storybook (Vitest + Playwright browser):**
- Configurado em `vitest.config.ts:67-82` com `storybookTest` plugin.
- Usa `@vitest/browser-playwright` com chromium headless.
- **Achado:** Configuração existe mas não foi possível verificar quantas stories existem ou se os testes passam.

#### 15.2 Cobertura atual
- **Achado Importante:** Script `test:coverage` existe (`"vitest run ... --coverage"`), mas não há relatório de cobertura gerado ou threshold configurado.
- **Estimativa por amostragem:**
  - Hooks: ~21 de ~40+ hooks testados (~50% cobertura de arquivos).
  - Componentes: ~5 de ~100+ componentes testados (~5% cobertura de arquivos).
  - E2E: Cobre auth, wizard (7 steps), chat (2 cenários), kanban (1 cenário). Muitas áreas não cobertas: admin, compliance, configurações, busca, filtros.

#### 15.3 Cenários cobertos (happy path vs erros)
- **Hooks:** Testam happy path E edge cases. Exemplo em `use-candidate-filters.test.ts`: testa estado inicial, toggle, reset, hasActiveFilters.
- **E2E:** Cobrem happy path e alguns erros (ex: `login.spec.ts` testa credenciais inválidas), mas usam `.catch(() => {})` em algumas assertions — testes podem passar silenciosamente em falha.
- **Evidência:** `plataforma-lia/e2e/tests/auth/login.spec.ts:21` — `await expect(...).toBeVisible({ timeout: 5000 }).catch(() => {})` — assertion com catch vazio.

#### 15.4 Qualidade dos testes

**Comportamento vs implementação:**
- Hooks: Testam comportamento (estado, transições) — boa prática.
- Componentes: Alguns testam implementação (`typeof FairnessWarningBanner === "function"`) em vez de comportamento renderizado. `@testing-library/dom` está disponível como dependência (`package.json:51`), mas os testes atuais de componentes optam por não usá-la.

**Mocks organizados:**
- `plataforma-lia/src/hooks/__tests__/setup.ts` — setup centralizado.
- Testes usam `vi.fn()` e `vi.mock()` de forma organizada.

**Testes de acessibilidade:**
- **Achado Importante:** Nenhum teste de acessibilidade (axe-core, jest-axe) encontrado.

#### 15.5 Testabilidade do código

**Lógica extraída:**
- Hooks são bem separados (`use-candidate-filters`, `use-float-streaming`, etc.) — alta testabilidade.
- Serviços isolados (`auth-service.ts`, `lia-api/base.ts`) — testáveis com mocks.

**Dependências injetáveis:**
- Contextos React (`JWTAuthProvider`, `LiaFloatProvider`, `ClientContext`) permitem wrapping em testes.
- `plataforma-lia/src/hooks/__tests__/setup.ts` configura ambiente para hooks.

**Achado Melhoria:** Alguns componentes são monolíticos (ex: `dashboard-app.tsx`, `expanded-chat-modal.tsx`) — difíceis de testar isoladamente.

#### 15.6 Pipeline de CI
- **Verificado — Presente:** CI pipeline configurado via GitHub Actions no diretório raiz do repositório (`.github/workflows/`). 4 workflows encontrados:
  - `.github/workflows/ci.yml` — Job `Frontend — Lint & Build` (push/PR em main/develop):
    - Instala dependências (`npm ci`), lint com Biome (`npx biome check src/`), type check (`npx tsc --noEmit`), testes unitários (`npx vitest run`), build de produção (`npm run build`).
    - **Evidência:** `.github/workflows/ci.yml:88-122`
  - `.github/workflows/e2e-tests.yml` — Playwright E2E com PostgreSQL service container (push/PR em main).
  - `.github/workflows/deploy.yml` — Deploy com Docker (push em main + tags).
  - `.github/workflows/docker-build.yml` — Build de imagem Docker.
- **Achado Importante:** `next.config.js:19-24` — `eslint.ignoreDuringBuilds: true`, `typescript.ignoreBuildErrors: true` — o build do Next.js ignora erros de lint e TS, porém o CI executa lint e type check como steps separados ANTES do build, o que mitiga parcialmente este risco.
- **Achado Melhoria:** Job de acessibilidade (`.github/workflows/ci.yml:168-183`) está configurado com `continue-on-error: true` e o check real está como TODO (`echo "Axe-core accessibility check configured — run against staging URL"`).

#### 15.7 Testes bloqueiam deploy
- **Verificado — Parcial:** O CI job `frontend` executa testes unitários via Vitest antes do build. Se os testes falharem, o job falha e o PR não pode ser mergeado (dependendo da configuração de branch protection no GitHub).
- **Achado Importante:** O workflow `deploy.yml` NÃO depende (`needs`) do job de CI — o deploy é triggerado por push em `main` independentemente do resultado do CI. Isso significa que um merge direto (sem PR) poderia fazer deploy sem testes.
- **Achado:** E2E tests rodam em workflow separado (`e2e-tests.yml`) e também não bloqueiam deploy.

#### 15.8 Tempo da suite
- **Não verificável:** Suite não foi executada. Configuração sugere execução rápida (hooks unitários em node, components em jsdom).

### Classificação dos Achados
- **Críticos:** Deploy não depende de CI (workflow `deploy.yml` sem `needs: [frontend]`); sem threshold de cobertura frontend.
- **Importantes:** Cobertura de componentes muito baixa (~5%); nenhum teste de acessibilidade nos testes locais (job CI de axe-core é placeholder); assertions com `.catch(() => {})` em E2E; `ignoreBuildErrors: true` no next.config.js (mitigado por tsc no CI).
- **Melhorias:** Componentes monolíticos difíceis de testar; testes de componentes não utilizam `@testing-library/dom` (disponível mas não usado).

---

## Apêndice: Checklist de Verificações

| # | Item | Verificado | Resultado |
|---|------|-----------|-----------|
| 11.1 | Sistema i18n configurado | ✅ | Ausente |
| 11.2 | Strings hardcoded | ✅ | 100% hardcoded pt-BR |
| 11.3 | Formatação de datas/números | ✅ | Hardcoded pt-BR |
| 11.4 | Pluralização | ✅ | Ausente |
| 11.5 | Layout quebra em outros idiomas | ✅ | N/A (monolíngue) |
| 11.6 | Imagens com texto | ✅ | Conforme |
| 11.7 | Timezone | ✅ | Implícito (browser) |
| 11.8 | RTL | ✅ | Ausente |
| 12.1 | SSR/SSG vs SPA | ✅ | force-dynamic (SPA-like) |
| 12.2 | Hydration mismatch | ✅ | Suprimido |
| 12.3 | Sitemap/robots.txt | ✅ | Ausentes |
| 12.4 | Canonical URLs | ✅ | Ausentes |
| 12.5 | Title/description por página | ✅ | Parcial |
| 12.6 | Open Graph/Twitter Cards | ✅ | Ausentes |
| 12.7 | JSON-LD | ✅ | Ausente |
| 12.8 | URLs amigáveis | ✅ | Conforme |
| 12.9 | Core Web Vitals | ✅ | Prejudicado (no-cache global) |
| 12.10 | Alt em imagens | ✅ | Parcial |
| 13.1 | Banner de cookies | ✅ | Ausente |
| 13.2 | Consentimento antes de analytics | ✅ | Sentry sem gate |
| 13.3 | Scripts condicionais | ✅ | N/A (poucos scripts 3rd party) |
| 13.4 | PII em console.log | ✅ | Conforme |
| 13.5 | PII em query params | ✅ | Email em SSO redirect |
| 13.6 | localStorage sem criptografia | ✅ | JWT sem criptografia |
| 13.7 | Limpeza no logout | ✅ | Parcial (só tokens) |
| 13.8 | Links privacidade/termos | ✅ | Conforme |
| 13.9 | Exclusão/exportação dados | ✅ | Conforme (portal LGPD) |
| 14.1 | Loading states | ✅ | Bom |
| 14.2 | Mensagens de erro | ✅ | Bom |
| 14.3 | Empty states | ✅ | Bom |
| 14.4 | Skeleton loaders | ✅ | Bom |
| 14.5 | Confirmação ações destrutivas | ✅ | Parcial |
| 14.6 | Validação inline | ✅ | Parcial |
| 14.7 | Deep linking | ✅ | Limitado |
| 14.8 | Timeout de sessão | ✅ | Ausente |
| 14.9 | Responsividade | ✅ | Bom |
| 14.10 | Toasts | ✅ | 2 sistemas; delay excessivo |
| 14.11 | prefers-reduced-motion | ✅ | Conforme |
| 15.1 | Tipos de teste | ✅ | Unit + Hooks + E2E + Storybook |
| 15.2 | Cobertura | ✅ | Hooks ~50%, Components ~5% |
| 15.3 | Happy path vs erros | ✅ | Ambos (com ressalvas) |
| 15.4 | Qualidade testes | ✅ | Boa (hooks), Limitada (components) |
| 15.5 | Testabilidade código | ✅ | Boa (hooks/services) |
| 15.6 | CI pipeline | ✅ | Presente (4 workflows GitHub Actions) |
| 15.7 | Testes bloqueiam deploy | ✅ | Parcial (CI não é dependency do deploy) |
| 15.8 | Tempo da suite | ⬜ | Não verificado |
