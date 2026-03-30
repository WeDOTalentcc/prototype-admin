# Auditoria Frontend Consolidada — 20 Dimensões

**Plataforma LIA — WeDo Talent**
**Data:** 2026-03-30
**Framework:** Next.js 15.3.2 + React 19 + Tailwind CSS 3.4.17 + shadcn/ui + Radix UI
**Codebase:** 1.540 arquivos (709 TSX + 831 TS), 398.179 linhas em `src/`

---

## Sumário Executivo Geral

| # | Dimensão | Score | Status |
|---|----------|-------|--------|
| 1 | Qualidade de Código | 1.5/3 | 🔴 Crítico |
| 2 | Arquitetura CSS | 2.0/3 | ⚠️ Importante |
| 3 | Performance de Renderização | 1.5/3 | 🔴 Crítico |
| 4 | Performance de Bundle/Assets | 0.5/3 | 🔴 Crítico |
| 5 | Design System e UI | 2.5/3 | ✅ Bom |
| 6 | Acessibilidade | 2.0/3 | ⚠️ Parcial |
| 7 | Segurança | 1.0/3 | 🔴 Crítico |
| 8 | Integração com APIs | 2.0/3 | ⚠️ Parcial |
| 9 | Routing e Navegação | 1.5/3 | 🔴 Insuficiente |
| 10 | Gestão de Formulários | 1.5/3 | ⚠️ Parcial |
| 11 | Internacionalização (i18n) | 0/3 | 🔴 Ausente |
| 12 | SEO e Metadados | 1/3 | 🔴 Mínimo |
| 13 | Compliance e Legal | 2/3 | ⚠️ Parcial |
| 14 | Qualidade de Produto e UX | 2/3 | ✅ Bom |
| 15 | Testabilidade e Cobertura | 2/3 | ✅ Bom |
| 16 | Developer Experience | 2/3 | ✅ Bom |
| 17 | Compatibilidade de Browsers | 1/3 | 🔴 Básico |
| 18 | Animações e Transições | 3/3 | ✅ Excelente |
| 19 | Scripts de Terceiros | 3/3 | ✅ Excelente |
| 20 | Observabilidade | 1/3 | 🔴 Básico |

### Scores por Parte

| Parte | Dimensões | Média |
|-------|-----------|-------|
| Parte 1 — Fundamentos | 1-5 | 1.6/3 |
| Parte 2 — Segurança e Integrações | 6-10 | 1.6/3 |
| Parte 3 — Capacidades | 11-15 | 1.4/3 |
| Parte 4 — DX e Infraestrutura | 16-20 | 2.0/3 |
| **Score Médio Global** | **1-20** | **1.65/3** |

---

## Parte 1 — Fundamentos (Dimensões 1-5)

### Dimensão 1 — Qualidade de Código (1.5/3)

**Resumo:** Muitos componentes gigantes, TypeScript relaxado, linting desabilitado no build.

**Achados Críticos:**
- **30+ componentes acima de 1.000 linhas** — top: `ats-integrations-page.tsx` (1.522), `useCandidatesPageCore.tsx` (1.509), `useChatPageCore.tsx` (1.500)
- **TypeScript relaxado** — `noImplicitAny: false`, `ignoreBuildErrors: true`, `no-explicit-any: off`
- **15 regras a11y desabilitadas** no Biome (`noAutofocus`, `useAltText`, `useKeyWithClickEvents`, etc.)

**Achados Importantes:**
- Nomenclatura inconsistente (kebab-case vs PascalCase vs camelCase entre diretórios)
- Hooks extraídos mas tão grandes quanto componentes originais (1.500+ linhas)
- 16 TODO/FIXME no código
- Tipagem de domínio insuficiente (apenas 5 arquivos em `src/types/`)

**Conformidades:**
- Gestão de estado adequada (3 contextos globais, SWR para data fetching)
- Profundidade de aninhamento conforme
- Padrão DRY razoável com 50+ componentes base e 70+ hooks

---

### Dimensão 2 — Arquitetura CSS (2.0/3)

**Resumo:** Estratégia Tailwind + design tokens clara, mas `!important` excessivo e tokens duplicados.

**Achados Críticos:**
- **139 ocorrências de `!important`** — 78 só em `onboarding-styles.css` (1 a cada 3 linhas)
- `typography.css` força fontes via `!important` em seletores amplos (`nav`, `[data-sidebar]`, etc.)

**Achados Importantes:**
- **Duplicação de dark mode** em 3 locais: `globals.css`, `dark-mode.css`, `design-tokens.css`
- **Dois sistemas de tokens CSS** coexistentes: HSL shadcn vs hex LIA com overlap semântico
- Hardcoded colors em componentes TSX (login, chat, charts)
- Estilos globais com seletores amplos demais (`*` border-color)

**Conformidades:**
- CSS split bem organizado (tokens → typography → animations → components → dark-mode)
- Tailwind Preflight + autoprefixer
- Unidades consistentes (rem/px/%)
- CSS purge configurado

---

### Dimensão 3 — Performance de Renderização (1.5/3)

**Resumo:** Ausência significativa de memoização, keys de índice disseminadas, timers/listeners sem cleanup.

**Achados Críticos:**
- **153 arquivos com `key={index}`** — causa re-renders e bugs de reconciliação
- **Ratio useMemo+useCallback / useState = 0.43** — deveria ser >1.0 para componentes grandes
- **React.memo em apenas 4 arquivos** (11 componentes total)
- **164 arquivos com timers** — cleanup não garantido 1:1

**Achados Importantes:**
- 59 arquivos com `addEventListener`, apenas 12 com `passive: true`
- Apenas 1 arquivo usa virtualização (`@tanstack/react-virtual`)
- `reactStrictMode: false`

**Conformidades:**
- Debounce/throttle em 10+ hooks de busca
- Sem operações síncronas pesadas no main thread

---

### Dimensão 4 — Performance de Bundle/Assets (0.5/3)

**Resumo:** Bundle de 49.7MB (!), cache desabilitado globalmente, imagens não otimizadas.

**Achados Críticos:**
- **`app/page.js` = 49.7MB** (60x acima do threshold de 250KB gzipped)
- **Total JS = ~72MB** — dashboard inclui TODA a lógica no chunk inicial
- **Cache-Control: no-store** em TODAS as rotas (incluindo assets estáticos) — ~63MB re-download a cada page load
- **`images: { unoptimized: true }`** — sem WebP/AVIF, sem lazy loading, sem resize
- **Zero `loading="lazy"`** em tags `<img>`

**Achados Importantes:**
- Lazy loading insuficiente: 12 de ~95 rotas usam `dynamic()`
- Duas bibliotecas de gráficos (Recharts + Chart.js): ~400KB+ combinadas
- html2canvas + jspdf + canvg adicionam ~1.5MB sem lazy loading

**Conformidades:**
- Fontes otimizadas via `next/font/google` com `font-display: swap`
- CSS purge configurado
- Tree shaking funcional (named imports)

---

### Dimensão 5 — Design System e UI (2.5/3)

**Resumo:** Design system maduro com tokens centralizados, dark mode e 50+ componentes base.

**Achados Importantes:**
- **553 valores arbitrários Tailwind** em 226 arquivos
- **875 inline styles** — `style={{...}}` em componentes
- Validação de formulários parcial (Zod + inline, sem form library integrada)

**Conformidades:**
- Sistema de tokens maduro: `design-tokens.css` (996 linhas) + `design-tokens.ts` (470 linhas)
- shadcn/ui com 50+ componentes
- Dark mode implementado e funcional
- Tipografia com escala semântica (display/heading/body/micro/nano)
- Storybook configurado com Chromatic

---

## Parte 2 — Segurança e Integrações (Dimensões 6-10)

### Dimensão 6 — Acessibilidade (2.0/3)

**Resumo:** Bons defaults do Radix UI, focus styles e motion-reduce. Lacunas em labels de formulário.

**Achados Críticos:**
- Labels de formulário **sem associação `htmlFor`/`id`** em login, register, forgot-password

**Achados Importantes:**
- Mensagens de erro não conectadas a campos via `aria-describedby` (apenas 4 ocorrências)
- Ausência de `aria-required` em campos obrigatórios
- Containers sem elementos semânticos (`<main>`, `<nav>`, `<footer>`)

**Conformidades:**
- Tab order correto, focus trap em modais (Radix)
- `:focus-visible` preservado com `focus:ring-2`
- `prefers-reduced-motion` respeitado
- `aria-live` e `aria-expanded` usados adequadamente
- Atalhos de teclado implementados

---

### Dimensão 7 — Segurança (1.0/3)

**Resumo:** CRÍTICO — XSS via dangerouslySetInnerHTML sem sanitização, tokens em localStorage, sem CSP.

**Achados Críticos:**
- **~20 usos de `dangerouslySetInnerHTML` sem NENHUMA sanitização** — chat, email, templates
- **Ausência total de CSP** (Content Security Policy)
- **Tokens JWT em localStorage** — combinado com XSS = roubo de sessão
- **11 vulnerabilidades npm** — 2 critical (Next.js RCE, jspdf 10 CVEs), 6 high

**Achados Importantes:**
- Fallback secret previsível em `session-crypto.ts`
- ~100+ usos de localStorage (dados de usuário/cliente)

**Conformidades:**
- Zero `console.log` em produção
- API keys apenas em `process.env` (server-side)
- URLs construídas com `encodeURIComponent`

---

### Dimensão 8 — Integração com APIs (2.0/3)

**Resumo:** Camada de serviços bem organizada, mas sem retry, AbortController e SWR subutilizado.

**Achados Críticos:**
- **Sem retry com backoff** — falhas de rede = erro imediato
- **AbortController em apenas ~7 arquivos** — requests continuam após unmount

**Achados Importantes:**
- **SWR subutilizado** (~5 de centenas de chamadas)
- Sem interceptors centralizados para refresh token
- Sem validação runtime de responses

**Conformidades:**
- Camada de serviços organizada (~30 arquivos em `services/`)
- Objeto unificado `liaApi` com spread de módulos
- Tratamento de status codes (401, 403, rede)
- Tipos TypeScript + Zod schemas

---

### Dimensão 9 — Routing e Navegação (1.5/3)

**Resumo:** Middleware auth funciona, mas faltam not-found, error e loading pages.

**Achados Críticos:**
- **Sem `not-found.tsx`** — 404 genérico sem branding
- **Sem `error.tsx`** — erros não capturados por rota
- **Sem `loading.tsx`** — sem loading automático durante navegação

**Achados Importantes:**
- `?next=` param do middleware não consumido pelo login
- Sem proteção de role no middleware (apenas autenticação)
- Tabs não refletidas na URL

**Conformidades:**
- Middleware auth classifica rotas (PUBLIC, PROTECTED_PAGE, PROTECTED_API)
- Layout compartilhado com providers globais
- Sidebar de navegação funcional

---

### Dimensão 10 — Gestão de Formulários (1.5/3)

**Resumo:** Zod instalado mas não integrado com forms client-side. Validação manual.

**Achados Críticos:**
- **Validação Zod não integrada com formulários client-side** — validação manual propensa a erros
- **Sem preservação de dados** ao navegar em formulários longos

**Achados Importantes:**
- **Sem máscaras de input** (CPF, telefone, CEP) — essencial para plataforma brasileira de RH
- Validação apenas em submit (sem blur/change)
- Inputs não desabilitados durante submissão em register

**Conformidades:**
- Botão disabled durante envio com loading visual
- Mensagens de erro claras em pt-BR
- Login multi-step (email → senha)

---

## Parte 3 — Capacidades (Dimensões 11-15)

### Dimensão 11 — Internacionalização (0/3)

**Resumo:** i18n inexistente. 100% das strings hardcoded em pt-BR.

**Achados Críticos:**
- Nenhuma biblioteca de i18n instalada (react-i18next, next-intl)
- 100% das strings de UI hardcoded em português
- Locale hardcoded em `toLocaleDateString('pt-BR')`
- Sem pluralização, sem RTL

**Estimativa de retrofit:** 3-5 sprints para cobertura completa (~200+ arquivos).

---

### Dimensão 12 — SEO e Metadados (1/3)

**Resumo:** Metadados básicos existem, mas faltam componentes fundamentais de SEO.

**Achados Críticos:**
- **Sem sitemap.xml** e **sem robots.txt**
- **Sem Open Graph** e **sem Twitter Cards**
- **Sem JSON-LD** (ex: `JobPosting` schema para vagas)

**Achados Importantes:**
- `force-dynamic` desabilita SSG para todas as rotas
- `Cache-Control: no-store` global prejudica Core Web Vitals
- `images.unoptimized: true`
- Sem canonical URLs

**Conformidades:**
- Metadata global definida em layout.tsx
- URLs amigáveis via App Router
- `trailingSlash: true` consistente

---

### Dimensão 13 — Compliance e Legal (2/3)

**Resumo:** Infraestrutura LGPD sólida, mas sem banner de cookies.

**Achados Críticos:**
- **Ausência de banner de cookies** / consent manager

**Achados Importantes:**
- Tokens JWT em localStorage sem criptografia
- Logout não limpa todos os dados do localStorage
- Sentry sem gate de consentimento

**Conformidades:**
- Portal LGPD completo (Art. 18: acesso, correção, exclusão, portabilidade)
- Portal do titular de dados
- Painel admin de compliance
- Links de privacidade/termos em múltiplos pontos
- Zero PII em console.log

---

### Dimensão 14 — Qualidade de Produto e UX (2/3)

**Resumo:** Boa infraestrutura de loading states, error handling e empty states.

**Achados Importantes:**
- `TOAST_REMOVE_DELAY = 1000000` (~16 min) — toasts não auto-dismiss
- Sem timeout de sessão no frontend
- Deep linking limitado em painéis internos

**Conformidades:**
- Loading states em 30+ arquivos com `LoadingScreen`, `Skeleton`, `Suspense`
- ErrorBoundary global com retry e reload
- `EmptyState` reutilizável (usado em 8+ componentes)
- Skeleton loaders em 18+ arquivos
- AlertDialog para confirmações (20+ componentes)
- `prefers-reduced-motion` respeitado
- Classes responsivas Tailwind

---

### Dimensão 15 — Testabilidade e Cobertura (2/3)

**Resumo:** Fundação de 4 camadas (unit, hooks, e2e, storybook) com CI pipeline completo.

**Achados Críticos:**
- Deploy **não depende de CI** (`deploy.yml` sem `needs: [frontend]`)
- Sem threshold de cobertura frontend

**Achados Importantes:**
- Cobertura de componentes baixa (~5%)
- Assertions com `.catch(() => {})` em E2E (falham silenciosamente)
- Sem testes de acessibilidade (axe-core placeholder)

**Conformidades:**
- 21 arquivos de teste de hooks com `renderHook`/`act`
- 13 specs E2E Playwright (auth, wizard, chat, kanban)
- CI pipeline: 4 workflows GitHub Actions (lint, type check, testes, build)
- Storybook com Chromatic integrado

---

## Parte 4 — DX e Infraestrutura (Dimensões 16-20)

### Dimensão 16 — Developer Experience (2/3)

**Resumo:** ESLint + Biome bem configurados, Storybook presente. Faltam pre-commit hooks e README.

**Achados Importantes:**
- Ausência de pre-commit hooks (Husky/lint-staged)
- `eslint.ignoreDuringBuilds: true` e `typescript.ignoreBuildErrors: true`
- README é template padrão create-next-app

**Conformidades:**
- ESLint flat config com regras customizadas do DS
- Biome formatação + organize imports
- Path aliases `@/*` funcionais
- Hot reload com HMR + `incremental: true`
- Storybook com addon-a11y
- Frameworks atualizados (Next 15, React 19, TS 5.8)

---

### Dimensão 17 — Compatibilidade de Browsers (1/3)

**Resumo:** Sem browserslist explícito, sem testes cross-browser, sem fallbacks.

**Achados Importantes:**
- Browserslist não configurado explicitamente
- Sem testes em Safari/WebKit via Playwright
- Sem `<noscript>` fallback

**Conformidades:**
- Tailwind container system com breakpoints
- `prefers-reduced-motion` verificação JS (`typeof window`)

---

### Dimensão 18 — Animações e Transições (3/3)

**Resumo:** Excelente. prefers-reduced-motion em 4 camadas, animações GPU-friendly, consistência.

**Conformidades:**
- `prefers-reduced-motion` respeitado em: globals.css, animations.css, components.css, design-tokens.css + JS utility
- `motion-reduce:animate-none` em todos os spinners/loaders
- Animações usam `transform`/`opacity` (GPU compositable)
- Durações consistentes: hover 0.15-0.25s, transitions 0.25-0.4s
- Animações Radix desabilitadas globalmente (decisão documentada)
- `will-change: auto` controlado

---

### Dimensão 19 — Scripts de Terceiros (3/3)

**Resumo:** Projeto limpo — zero scripts de terceiros no frontend.

**Conformidades:**
- Nenhum analytics, chat widget, mapa, pixel de tracking
- Nenhum CDN externo — todas dependências via npm bundle local
- Tree-shakeable por bundler

---

### Dimensão 20 — Observabilidade (1/3)

**Resumo:** Sentry preparado mas NÃO instalado. Zero console.log. Sem CWV, RUM ou correlation ID.

**Achados Críticos:**
- **`@sentry/nextjs` NÃO instalado** no package.json (config existe mas é inativa)
- `Sentry.captureException` **comentado** no ErrorBoundary

**Achados Importantes:**
- Core Web Vitals não monitorados
- Sem correlation ID entre frontend e backend
- Sem interceptor global de erros de rede

**Conformidades:**
- ErrorBoundary global funcional (UI fallback com retry)
- Zero `console.log` em produção
- Logs de auditoria de negócio existem (admin/compliance)

---

## Inventário Completo de Achados

### Achados Críticos (12)

| # | Dim | Descrição | Arquivo/Evidência |
|---|-----|-----------|-------------------|
| 1 | 1 | 30+ componentes >1.000 linhas | `ats-integrations-page.tsx` (1.522) |
| 2 | 1 | TypeScript relaxado (noImplicitAny:false, ignoreBuildErrors:true) | `tsconfig.json`, `next.config.js` |
| 3 | 3 | 153 arquivos com `key={index}` | Disseminado em `src/components` |
| 4 | 4 | Bundle principal 49.7MB (60x threshold) | `app/page.js` |
| 5 | 4 | Cache-Control no-store em TODAS as rotas | `next.config.js:56-68` |
| 6 | 7 | ~20 dangerouslySetInnerHTML sem sanitização | Chat, email, templates |
| 7 | 7 | 11 vulnerabilidades npm (2 critical, 6 high) | `npm audit` |
| 8 | 7 | Ausência total de CSP headers | `next.config.js` |
| 9 | 11 | i18n inexistente — 100% strings hardcoded pt-BR | Todo o codebase |
| 10 | 12 | Sem sitemap.xml, robots.txt, Open Graph, JSON-LD | `src/app/` |
| 11 | 20 | @sentry/nextjs não instalado — captura de erros inativa | `package.json` |
| 12 | 20 | Sentry.captureException comentado no ErrorBoundary | `error-boundary.tsx:35` |

### Achados Importantes (25)

| # | Dim | Descrição |
|---|-----|-----------|
| 1 | 1 | Nomenclatura inconsistente de arquivos |
| 2 | 2 | 139 ocorrências de `!important` (78 em onboarding) |
| 3 | 2 | Duplicação de dark mode em 3 locais |
| 4 | 2 | Dois sistemas de tokens CSS coexistentes |
| 5 | 3 | 47 addEventListener sem `passive: true` |
| 6 | 3 | Apenas 1 arquivo com virtualização |
| 7 | 4 | Lazy loading: 12 de ~95 rotas |
| 8 | 4 | Duas bibliotecas de gráficos (Recharts + Chart.js) |
| 9 | 6 | Labels sem htmlFor/id em formulários |
| 10 | 6 | aria-describedby em apenas 4 arquivos |
| 11 | 7 | Tokens JWT em localStorage (XSS-exploitable) |
| 12 | 8 | Sem retry/backoff nas chamadas API |
| 13 | 8 | AbortController em apenas ~7 arquivos |
| 14 | 8 | SWR subutilizado (~5 de centenas de chamadas) |
| 15 | 9 | Sem not-found.tsx, error.tsx, loading.tsx |
| 16 | 9 | Sem proteção de role no middleware |
| 17 | 10 | Zod não integrado com forms client-side |
| 18 | 10 | Sem máscaras de input (CPF, telefone, CEP) |
| 19 | 13 | Ausência de banner de cookies |
| 20 | 14 | Toast delay ~16 min (não auto-dismiss) |
| 21 | 15 | Deploy não depende de CI |
| 22 | 15 | Cobertura de componentes ~5% |
| 23 | 16 | Sem pre-commit hooks (Husky/lint-staged) |
| 24 | 17 | Sem testes cross-browser Safari/WebKit |
| 25 | 20 | Core Web Vitals não monitorados |

### Achados Melhorias (40+)

Incluem: `.editorconfig`, ADRs formais, duplo lock file, html2canvas substituição, browserslist, `<noscript>`, `forced-colors`, feature flags, `reportWebVitals`, correlation ID, progressShrink scaleX, CSS órfão, `.animate-slide-in` duplicada, MSW para testes, e mais.

---

## Roadmap de Correções Prioritárias

### Sprint Atual — Segurança e Resiliência (P0)

| # | Ação | Dims | Esforço |
|---|------|------|---------|
| 1 | Instalar DOMPurify e sanitizar todos os `dangerouslySetInnerHTML` | 7 | 1-2 dias |
| 2 | Executar `npm audit fix` e atualizar jspdf | 7 | 0.5 dia |
| 3 | Configurar CSP headers via next.config.js | 7 | 0.5 dia |
| 4 | Criar `not-found.tsx`, `error.tsx`, `loading.tsx` | 9 | 0.5 dia |
| 5 | Instalar @sentry/nextjs e ativar ErrorBoundary | 20 | 0.5 dia |

### Próximo Sprint — Performance e UX (P1)

| # | Ação | Dims | Esforço |
|---|------|------|---------|
| 6 | Code splitting: lazy load modais pesados e rotas | 4 | 2-3 dias |
| 7 | Remover Cache-Control no-store de assets estáticos | 4 | 0.5 dia |
| 8 | Ativar `images: { unoptimized: false }` + loading="lazy" | 4 | 1 dia |
| 9 | Migrar tokens JWT para httpOnly cookies | 7, 13 | 2 dias |
| 10 | Associar labels com htmlFor/id em formulários | 6 | 1 dia |
| 11 | Integrar Zod + React Hook Form para forms client-side | 10 | 2-3 dias |
| 12 | Consumir `?next=` param no login flow | 9 | 0.5 dia |

### Backlog — Qualidade e Manutenibilidade (P2)

| # | Ação | Dims | Esforço |
|---|------|------|---------|
| 13 | Consolidar tokens CSS (eliminar duplicação de dark mode) | 2 | 1-2 dias |
| 14 | Reduzir `!important` (começar por onboarding: 78 ocorrências) | 2 | 1 dia |
| 15 | Adotar SWR/React Query como estratégia principal de fetching | 8 | 3-5 dias |
| 16 | Implementar retry + AbortController em serviços | 8 | 2 dias |
| 17 | Adicionar máscaras de input (CPF, telefone, CEP) | 10 | 1 dia |
| 18 | Refatorar componentes >1.000 linhas (top 15) | 1 | 5-10 dias |
| 19 | Ativar `noImplicitAny: true` progressivamente | 1 | 3-5 dias |
| 20 | Substituir keys de índice por IDs únicos | 3 | 2-3 dias |
| 21 | Adicionar React.memo em componentes de lista | 3 | 1-2 dias |
| 22 | Banner de cookies / consent manager | 13 | 1-2 dias |
| 23 | Husky pre-commit hooks | 16 | 0.5 dia |
| 24 | Testes cross-browser WebKit | 17 | 1 dia |
| 25 | reportWebVitals + Core Web Vitals monitoring | 20 | 1 dia |

### Horizonte — Evolução Estratégica (P3)

| # | Ação | Dims | Esforço |
|---|------|------|---------|
| 26 | Sistema de i18n (react-i18next/next-intl) | 11 | 3-5 sprints |
| 27 | SEO: sitemap, robots.txt, Open Graph, JSON-LD | 12 | 1-2 sprints |
| 28 | Feature flags (LaunchDarkly/custom) | 20 | 1 sprint |
| 29 | Virtualização de listas longas | 3 | 1 sprint |
| 30 | Deploy dependente de CI (needs: [frontend]) | 15 | 0.5 dia |

---

## Pontos Fortes Destacados

1. **Design System maduro** (Dim 5: 2.5/3) — Tokens centralizados, dark mode, 50+ componentes
2. **Animações excelentes** (Dim 18: 3/3) — prefers-reduced-motion em 4 camadas, GPU-friendly
3. **Zero scripts de terceiros** (Dim 19: 3/3) — Bundle 100% controlado
4. **Zero console.log** — Higiene de código exemplar
5. **Infraestrutura LGPD** — Portal completo Art. 18 com 5 tipos de solicitação
6. **CI pipeline** — 4 workflows GitHub Actions cobrindo lint, type check, testes, build
7. **Hooks de dados** — 21 hooks testados com `renderHook`/`act`
8. **Camada de serviços** — ~30 arquivos organizados com tipos e schemas

---

## Relatórios Individuais (Referência)

- `docs/audit/frontend-audit-parte1-fundamentos.md` — Dims 1-5 (750 linhas)
- `docs/audit/frontend-audit-parte2-seguranca-integracoes.md` — Dims 6-10 (430 linhas)
- `plataforma-lia/docs/audit/frontend-audit-parte3-capacidades.md` — Dims 11-15 (441 linhas)
- `docs/audit/frontend-audit-parte4-dx-infra.md` — Dims 16-20 (522 linhas)

---

*Relatório consolidado gerado em 2026-03-30 — Auditoria diagnóstica de 20 dimensões.*
*Codebase analisado: 1.540 arquivos, 398.179 linhas de código TypeScript/TSX.*
