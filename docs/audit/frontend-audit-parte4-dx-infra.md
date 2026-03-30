# Auditoria Frontend — Parte 4: DX e Infraestrutura (Dimensões 16-20)

**Projeto:** Plataforma LIA (WeDo Talent)  
**Data:** 2026-03-30  
**Commit base:** `995a4fe1`  
**Framework:** Next.js 15.3.2 + React 19 + Tailwind CSS 3.4.17  
**Escopo:** Dimensões 16 (Developer Experience), 17 (Compatibilidade de Browsers), 18 (Animações/Transições), 19 (Scripts de Terceiros), 20 (Observabilidade)  
**Método:** Auditoria estática — inspeção de código fonte, configurações e dependências. Sem execução de build, runtime testing ou verificação em browser real. Afirmações sobre comportamento em runtime (ex: tempo de onboarding, performance em 3G) são inferências baseadas na análise estática e devem ser validadas separadamente.

---

## Resumo Executivo

| Dimensão | Score | Classificação |
|----------|-------|---------------|
| 16 — Developer Experience | 2/3 | Bom |
| 17 — Compatibilidade de Browsers | 1/3 | Básico |
| 18 — Animações e Transições | 3/3 | Excelente |
| 19 — Scripts de Terceiros | 3/3 | Excelente |
| 20 — Observabilidade | 1/3 | Básico |
| **Média Geral** | **2.0/3** | **Bom** |

---

## Dimensão 16 — Developer Experience (Score: 2/3)

### Justificativa do Score
Ferramental de linting e formatação bem configurado (ESLint + Biome), path aliases funcionais, Storybook presente, testes unitários e E2E configurados. Porém, faltam pre-commit hooks, .editorconfig, Prettier standalone, README customizado e ADRs.

### Verificações Realizadas

#### 16.1 Linting e Formatação

**ESLint com regras customizadas — ✅ CONFORME**
- Arquivo: `plataforma-lia/eslint.config.mjs` (linhas 1-55)
- Configuração flat config com `next/core-web-vitals` e `next/typescript`
- Regras customizadas do WeDo DS via `no-restricted-syntax` (linhas 33-51): previnem `transition-all`, `rounded-2xl`, tokens `wedo-apoio-*` deprecated
- Plugin Storybook integrado (`eslint-plugin-storybook`, linha 2)
- Evidência: 0 ocorrências de `transition-all` em arquivos .tsx — regra está funcionando

**Biome configurado — ✅ CONFORME**
- Arquivo: `plataforma-lia/biome.json` (linhas 1-54)
- Formatter habilitado com indent por espaço (linha 14-16)
- Linter com regras recommended (linha 23)
- Organize imports habilitado (linha 19)
- Escopo correto: `src/**/*.ts`, `src/**/*.tsx` (linha 11)
- Regras a11y desabilitadas deliberadamente (linhas 31-46) — decisão documentada

**Prettier integrado — ⚠️ AUSENTE**
- Nenhum arquivo `.prettierrc*` encontrado no projeto
- Formatação delegada ao Biome (`npm run format` usa `bunx biome format --write`, package.json linha 10)
- Não é um problema real pois Biome substitui Prettier, mas pode confundir devs que esperam Prettier

#### 16.2 Pre-commit Hooks e EditorConfig

**Husky / pre-commit hooks — ❌ AUSENTE**
- Diretório `.husky` não existe
- Nenhuma configuração de lint-staged encontrada
- Risco: código não lintado pode ser commitado

**EditorConfig — ❌ AUSENTE**
- Arquivo `.editorconfig` não encontrado
- Risco: inconsistência de tabs/espaços entre editores de diferentes devs

#### 16.3 Path Aliases

**Path aliases (@/) — ✅ CONFORME**
- Arquivo: `plataforma-lia/tsconfig.json` (linhas 27-31)
- Alias `@/*` mapeado para `./src/*`
- Uso consistente em todo o projeto (ex: `import { cn } from '@/lib/utils'`)

#### 16.4 Hot Reload e Build

**Hot reload — ✅ CONFORME**
- `next dev` com HMR padrão do Next.js 15 (package.json linha 6)
- `incremental: true` no tsconfig (linha 21) para builds incrementais

**Tempo de build — ⚠️ NÃO VERIFICÁVEL EM AUDITORIA ESTÁTICA**
- Build command: `next build` (package.json linha 7)
- `eslint.ignoreDuringBuilds: true` e `typescript.ignoreBuildErrors: true` em next.config.js (linhas 19-24) — acelera build mas oculta erros
- Comentário "Sprint 8: pre-existing lint/TS errors - to be fixed in Sprint 9" indica dívida técnica

#### 16.5 Documentação e Onboarding

**README — ⚠️ INSUFICIENTE**
- Arquivo: `plataforma-lia/README.md` (linhas 1-37)
- Template padrão do `create-next-app` sem customização
- Não descreve: arquitetura do projeto, variáveis de ambiente necessárias, dependências externas (backend), design system, convenções de código
- Onboarding em <30min para novo dev: improvável sem README customizado

**ADRs (Architecture Decision Records) — ❌ AUSENTE em `plataforma-lia/`**
- Diretório `plataforma-lia/docs/adr/` não existe (nota: existe `docs/adr/` no monorepo raiz, mas não dentro do pacote frontend)
- Decisões arquiteturais documentadas inline em comentários CSS (ex: `globals.css` linhas 17-30, `design-tokens.css`) — melhor que nada, mas não é formato ADR

**Storybook — ✅ CONFORME**
- Configuração presente em `.storybook/` (main.ts, preview.ts, vitest.setup.ts)
- Scripts configurados: `storybook`, `build-storybook`, `chromatic` (package.json linhas 11-13)
- Addon a11y instalado (`@storybook/addon-a11y`, package.json linha 80)
- Chromatic integrado para visual testing

#### 16.6 Lock File e Dependências

**Lock file commitado — ✅ CONFORME**
- `package-lock.json` presente com lockfileVersion 3 (15022 linhas)
- `bun.lock` também presente (duplo lock file — potencial confusão)

**Versões de frameworks — ✅ CONFORME**
- Next.js ^15.3.2 (atual)
- React ^19.0.0 (atual)
- TypeScript ^5.8.3 (atual)
- Tailwind CSS ^3.4.17 (atual, v4 disponível mas migração não trivial)

**Dependências abandonadas — ⚠️ VERIFICAÇÃO PARCIAL**
- `html2canvas` v1.4.1 — projeto com manutenção reduzida, última release significativa há tempo
- `same-runtime` v0.0.1 — versão extremamente baixa, propósito específico (JSX runtime)
- Duplo lock file (`package-lock.json` + `bun.lock`) pode causar inconsistências

### Achados

**Críticos:**
- Nenhum

**Importantes:**
- [DX-IMP-01] Ausência de pre-commit hooks (Husky/lint-staged) — código não lintado pode chegar ao repositório
- [DX-IMP-02] `eslint.ignoreDuringBuilds: true` e `typescript.ignoreBuildErrors: true` em `next.config.js` (linhas 19-24) — erros silenciados no build
- [DX-IMP-03] README é template padrão create-next-app sem informações do projeto (`plataforma-lia/README.md`)

**Melhorias:**
- [DX-MEL-01] Criar `.editorconfig` para consistência entre editores
- [DX-MEL-02] Criar ADRs formais em `docs/adr/` para decisões já documentadas inline
- [DX-MEL-03] Resolver duplo lock file (package-lock.json + bun.lock) — escolher um package manager
- [DX-MEL-04] Avaliar substituição de `html2canvas` por alternativa mais mantida (ex: `html-to-image`)

---

## Dimensão 17 — Compatibilidade de Browsers (Score: 1/3)

### Justificativa do Score
Não há configuração explícita de browserslist, polyfills seletivos, ou testes cross-browser. O projeto depende das configurações padrão do Next.js e autoprefixer. Não há evidência de testes em Safari, fallback para browsers antigos, ou verificação de APIs com suporte condicional.

### Verificações Realizadas

#### 17.1 Browserslist

**Browserslist configurado — ⚠️ IMPLÍCITO**
- Nenhum campo `browserslist` em `package.json` ou arquivo `.browserslistrc`
- O projeto usa `autoprefixer` (devDependency, package.json linha 93) que depende do browserslist padrão
- Next.js aplica seus próprios defaults de browserslist internamente
- Recomendação: explicitar para controle e documentação

#### 17.2 Polyfills

**Polyfills carregados seletivamente — ⚠️ NÃO CONFIGURADO**
- Nenhum polyfill explícito encontrado
- `tsconfig.json` target ES2017 (linha 3) — compatível com browsers modernos
- Next.js 15 inclui polyfills automáticos para `fetch`, `URL`, `Object.assign` etc.
- Sem polyfills para APIs mais recentes (ex: `ResizeObserver`, `IntersectionObserver`) que são usadas por Radix UI

#### 17.3 Testes Cross-Browser

**Testes em Safari — ❌ NÃO EVIDENCIADO**
- Playwright instalado como devDependency (`package.json` linha 101), mas sem configuração de projetos multi-browser (Safari/WebKit) identificada no escopo `plataforma-lia/`
- Scripts E2E disponíveis (`test:e2e`, `test:e2e:wizard`, `test:e2e:kanban`) sem indicação de execução em WebKit

**Fallback gracioso para browsers antigos — ❌ NÃO EVIDENCIADO**
- Nenhum mecanismo de detecção de browser ou fallback gracioso
- `<noscript>` tag não presente em `layout.tsx`

#### 17.4 Layout e Responsividade

**Overflow horizontal em mobile — ✅ PARCIALMENTE CONFORME**
- `overflow-hidden` usado em `clouds-background.tsx` (linha 149)
- Container system configurado em `tailwind.config.ts` (linhas 217-233) com breakpoints padrão

**Layout com zoom 150%/200% — ⚠️ NÃO VERIFICADO**
- Sem testes automatizados de zoom
- Uso de `rem` e utilities do Tailwind favorece escalabilidade, mas não há garantia

#### 17.5 Conexão e Performance

**Comportamento em conexão lenta (3G) — ❌ NÃO EVIDENCIADO**
- Nenhum mecanismo de detecção de conexão lenta
- Sem loading states condicionais baseados em `navigator.connection`

**SSR com JS desabilitado — ⚠️ PARCIAL**
- Next.js provê SSR por padrão, mas `force-dynamic` em `layout.tsx` (linha 1) indica renderização server-side
- Componentes `'use client'` não funcionarão sem JS
- Sem `<noscript>` fallback

#### 17.6 Acessibilidade de Browser

**Modo alto contraste — ⚠️ NÃO VERIFICADO**
- Sem media query `@media (forced-colors: active)` ou `prefers-contrast: high`
- Design system tem tokens de cor bem definidos, mas sem adaptação para alto contraste

**APIs de browser com verificação de suporte — ⚠️ PARCIAL**
- `prefersReducedMotion()` em `motion.ts` (linha 6) verifica `typeof window` antes de acessar `matchMedia`
- Sem verificação similar para outras APIs (ex: `navigator.clipboard`, `IntersectionObserver`)

### Achados

**Críticos:**
- Nenhum

**Importantes:**
- [BR-IMP-01] Ausência de browserslist explícito — browsers alvo não documentados
- [BR-IMP-02] Sem testes cross-browser em Safari/WebKit via Playwright
- [BR-IMP-03] Sem `<noscript>` fallback em `layout.tsx`

**Melhorias:**
- [BR-MEL-01] Adicionar campo `browserslist` em `package.json` com targets explícitos
- [BR-MEL-02] Configurar Playwright para testes em WebKit (Safari)
- [BR-MEL-03] Adicionar `<noscript>` tag com mensagem de fallback
- [BR-MEL-04] Implementar media query `@media (forced-colors: active)` para modo alto contraste
- [BR-MEL-05] Adicionar detecção de conexão lenta via `navigator.connection` API

---

## Dimensão 18 — Animações e Transições (Score: 3/3)

### Justificativa do Score
Excelente implementação. `prefers-reduced-motion` respeitado em 4 locais (CSS global + componentes + JS utility). Animações usam `transform`/`opacity` (propriedades compositable). Durações consistentes. `motion-reduce:animate-none` aplicado em todos os spinners e loaders. `will-change` controlado. Animações Radix desabilitadas globalmente com documentação clara.

### Verificações Realizadas

#### 18.1 prefers-reduced-motion

**prefers-reduced-motion respeitado — ✅ EXCELENTE**
- `globals.css` (linhas 227-235): regra global `@media (prefers-reduced-motion: reduce)` que zera `animation-duration` e `transition-duration`
- `animations.css` (linhas 356-365): segunda camada de proteção com `scroll-behavior: auto`
- `components.css` (linhas 521-528): terceira camada
- `design-tokens.css` (linhas 983-995): proteção específica para field animations
- `motion.ts` (linhas 1-17): utility JavaScript `prefersReducedMotion()` e `getAnimationDuration()` para animações JS
- Todos os `animate-spin` e `animate-pulse` no projeto usam `motion-reduce:animate-none` (verificado em 30+ ocorrências)
- Exemplo: `loading.tsx` linha 35: `animate-spin motion-reduce:animate-none`
- Exemplo: `skeleton.tsx` linha 9: `animate-pulse motion-reduce:animate-none`

#### 18.2 Propriedades Animadas

**transform/opacity vs width/height — ✅ CONFORME**
- Keyframes em `animations.css` usam predominantemente `transform` (translate, scale, rotate) e `opacity`
- Única exceção: `progressShrink` (linhas 154-161) anima `width` — aceitável para barra de progresso (raramente renderizada)
- `tailwind.config.ts` keyframes (linhas 192-208): `fade-in-up`, `scale-in-delayed`, `slide-in-up` — todos usam `transform` + `opacity`

**Animações CSS vs JavaScript — ✅ CONFORME**
- Animações são predominantemente CSS (keyframes + Tailwind classes)
- `clouds-background.tsx` usa CSS keyframes inline (linhas 151-172) em vez de framer-motion — decisão documentada como "OPT-027"
- Sem dependência de framer-motion para animações (grepping por `framer-motion` mostra referências textuais em strings/comments, não imports de animação)

#### 18.3 Duração e Easing Consistentes

**Durações com design system — ✅ CONFORME**
- Transições de hover: `0.15s`-`0.25s` com `cubic-bezier(0.4, 0, 0.2, 1)` (animations.css linhas 215-228)
- Page transitions: `0.25s`-`0.4s` com `ease-out` (page-transition.tsx linhas 14, 23, 36)
- Loaders: `0.8s`-`2s` (animações contínuas como shimmer, pulse, spin)
- Easing consistente: `ease-out` para entradas, `ease-in-out` para loops

#### 18.4 Animações de Entrada/Saída

**Page transitions — ✅ CONFORME**
- `page-transition.tsx`: 3 variantes (PageTransition=slideInUp, SlidePageTransition=slideInRight, FadePageTransition=fadeIn)
- Animações desabilitadas globalmente para Radix UI (tooltips, dropdowns, popovers) — decisão documentada em `globals.css` linhas 17-30 e `design-tokens.css` linhas 902-944
- Fade/slide/scale classes desabilitadas via `globals.css` linhas 246-251

#### 18.5 Animações Contínuas

**Loaders e skeleton — ✅ CONFORME**
- `loading.tsx`: 4 variantes (spinner, dots, skeleton, pulse) com `motion-reduce:animate-none`
- `skeleton.tsx`: `animate-pulse motion-reduce:animate-none` (linha 9)
- Shimmer animation: `2s infinite linear` (animations.css linhas 15-19)
- Loading-skeleton: `1.5s infinite` com gradient (animations.css linhas 180-187, 260-271)

#### 18.6 will-change

**Uso criterioso de will-change — ✅ CONFORME**
- `will-change: auto !important` aplicado nos seletores Radix desabilitados (`design-tokens.css` linhas 909, 919, 930) — reset correto
- Nenhum uso indiscriminado de `will-change` encontrado no projeto
- Clouds background usa `animationName` CSS sem `will-change` manual

### Achados

**Críticos:**
- Nenhum

**Importantes:**
- Nenhum

**Melhorias:**
- [AN-MEL-01] Animação `progressShrink` (animations.css linhas 154-161) anima `width` — considerar usar `transform: scaleX()` para performance GPU
- [AN-MEL-02] `animations.css` contém blocos CSS órfãos (linhas 76-88, 172-178, 273) — `to {}` blocks sem `@keyframes` pai (possível corrupção de arquivo)
- [AN-MEL-03] Classe `.animate-slide-in` definida duas vezes (animations.css linhas 194-196 e 202-204) com animações diferentes — segunda definição sobrescreve a primeira

---

## Dimensão 19 — Scripts de Terceiros (Score: 3/3)

### Justificativa do Score
Projeto limpo — sem scripts de terceiros carregados no frontend (zero analytics, chat widgets, mapas, pixels de tracking). Todas as dependências são npm packages instalados e bundled pelo webpack/turbopack. Sem CDN externas. Isso elimina riscos de performance, privacidade e segurança associados a scripts terceiros.

### Verificações Realizadas

#### 19.1 Inventário de Scripts de Terceiros

**Analytics (GA, GTM, etc.) — ✅ NENHUM ENCONTRADO**
- Nenhum `gtag`, `google.analytics`, `dataLayer` encontrado no código fonte
- Nenhum pixel de tracking (Facebook, LinkedIn, etc.)

**Chat widgets — ✅ NENHUM ENCONTRADO**
- Nenhum Intercom, Drift, Crisp, Tawk.to encontrado

**Mapas — ✅ NENHUM ENCONTRADO**
- Nenhum Google Maps, Mapbox, Leaflet encontrado

**Pagamento — ✅ NENHUM ENCONTRADO**
- Nenhum Stripe.js, PayPal SDK encontrado no frontend

#### 19.2 CDN e Scripts Externos

**Scripts via CDN — ✅ NENHUM ENCONTRADO**
- Nenhuma referência a `unpkg`, `jsdelivr`, `cloudflare.com/ajax` encontrada
- Todas as dependências servidas via bundle local

**SRI (Subresource Integrity) — N/A**
- Não aplicável — nenhum script externo carregado via CDN

#### 19.3 Impacto no Bundle

**Dependências de terceiros no bundle — ✅ CONFORME**
- Todas as dependências são npm packages (Radix UI, Chart.js, Recharts, dnd-kit, etc.)
- Carregadas via import estático, tree-shakeable pelo bundler Next.js
- Nenhum script carregado via `<script>` tag dinâmica

#### 19.4 Consentimento de Cookies

**Carregamento condicional ao consentimento — N/A**
- Sem scripts de tracking, não há necessidade de banner de cookies para scripts terceiros
- LGPD compliance tratada em módulos internos (`admin/compliance/lgpd/consentimentos/`)

### Achados

**Críticos:**
- Nenhum

**Importantes:**
- Nenhum

**Melhorias:**
- [TP-MEL-01] Quando analytics forem adicionados no futuro, implementar carregamento condicional ao consentimento do usuário e usar `async`/`defer`
- [TP-MEL-02] Se CDNs forem usadas no futuro, implementar SRI (Subresource Integrity) em todas as tags `<script>` e `<link>`

---

## Dimensão 20 — Observabilidade (Score: 1/3)

### Justificativa do Score
Infraestrutura de Sentry preparada (config file existe) mas pacote `@sentry/nextjs` **não está instalado** nas dependências do `package.json`. ErrorBoundary existe mas com captura Sentry comentada. Zero `console.log` em produção (excelente). Porém: sem Core Web Vitals monitorados, sem RUM, sem correlation ID, sem feature flags, sem alertas de degradação.

### Verificações Realizadas

#### 20.1 Captura de Erros Frontend

**Sentry configurado — ⚠️ PREPARADO MAS NÃO INSTALADO**
- Arquivo: `plataforma-lia/src/sentry.client.config.ts` (linhas 1-23)
- Configuração completa: DSN via env var, traces sample rate configurável, replays habilitados
- **Porém:** `@sentry/nextjs` NÃO está listado em `package.json` (nem dependencies nem devDependencies)
- Comentário em `error-boundary.tsx` linha 33-35: "Sentry capture disabled — package not installed"
- ErrorBoundary global existe e funciona (`error-boundary.tsx`), mas sem envio para Sentry

**ErrorBoundary — ✅ CONFORME**
- Arquivo: `plataforma-lia/src/components/error-boundary.tsx` (linhas 1-111)
- Envolve toda a aplicação em `layout.tsx` (linha 60)
- `getDerivedStateFromError` + `componentDidCatch` implementados
- Fallback UI com botão "Tentar novamente" e "Recarregar página"
- Exibe stack trace apenas em development (linha 86)

**Erros de rede capturados — ❌ NÃO EVIDENCIADO**
- Sem interceptor global de fetch/axios para captura de erros de rede
- Sem retry logic centralizada ou circuit breaker no frontend
- SWR (instalado) tem error handling por hook, mas sem agregação central

**console.log em produção — ✅ EXCELENTE**
- Zero ocorrências de `console.log`, `console.debug`, `console.info`, `console.warn` em `src/**/*.{ts,tsx}`
- Código totalmente limpo de logs de debug

#### 20.2 Source Maps

**Source maps disponíveis sem expor ao público — ⚠️ NÃO CONFIGURADO**
- Nenhuma configuração de source maps encontrada em `next.config.js`
- Next.js gera source maps por padrão em dev, mas em produção depende de configuração explícita
- Sem upload de source maps para Sentry (pacote não instalado)
- Nenhuma configuração em `netlify.toml` para restringir acesso a `.map` files

#### 20.3 Core Web Vitals e RUM

**Core Web Vitals monitorados — ❌ AUSENTE**
- Nenhum `reportWebVitals`, `web-vitals` package, ou integração de CWV encontrada
- Next.js 15 provê métricas via `reportWebVitals` mas não está implementado
- Referências a "CWV" encontradas apenas em dados demo (`demo-activities.ts`)

**RUM (Real User Monitoring) — ❌ AUSENTE**
- Nenhum serviço de RUM configurado (sem Datadog RUM, New Relic Browser, Sentry Performance)

**Alertas de degradação — ❌ AUSENTE**
- Sem mecanismo de alerta para degradação de performance ou disponibilidade

#### 20.4 Contexto e Rastreabilidade

**Correlation ID — ❌ AUSENTE**
- Nenhum `correlationId`, `x-request-id`, ou `requestId` encontrado no frontend
- Sem propagação de trace ID entre frontend e backend

**Contexto de usuário/sessão nos erros — ⚠️ PARCIAL**
- Sentry config não define `Sentry.setUser()` ou `Sentry.setContext()` (pois não está ativo)
- Auth context existe (`auth-context.tsx`) mas não propaga dados para observabilidade

**Feature flags — ❌ AUSENTE**
- Nenhum sistema de feature flags (LaunchDarkly, Unleash, Flagsmith, custom) encontrado
- Referências a "feature flag" em `demo-activities.ts` são dados demo, não implementação real

**Logs de auditoria — ✅ PARCIAL**
- Módulo `admin/configuracoes/auditoria/` existe (auditoria de ações do sistema)
- `audit-logs-service.ts` existe para comunicação com backend
- Porém, isso é auditoria de negócio, não observabilidade técnica

### Achados

**Críticos:**
- [OB-CRI-01] `@sentry/nextjs` referenciado em `sentry.client.config.ts` mas NÃO instalado no `package.json` — captura de erros em produção está completamente inativa
- [OB-CRI-02] Sentry.captureException comentado em `error-boundary.tsx` (linha 35) — erros de render não são reportados

**Importantes:**
- [OB-IMP-01] Core Web Vitals não monitorados — sem visibilidade de performance real dos usuários
- [OB-IMP-02] Sem correlation ID entre frontend e backend — debug de problemas cross-stack é manual
- [OB-IMP-03] Sem interceptor global de erros de rede (fetch/SWR) para agregação central

**Melhorias:**
- [OB-MEL-01] Instalar `@sentry/nextjs` e descomentar integração no ErrorBoundary
- [OB-MEL-02] Implementar `reportWebVitals` do Next.js e enviar métricas para backend/analytics
- [OB-MEL-03] Adicionar `Sentry.setUser()` após login para contextualizar erros
- [OB-MEL-04] Implementar feature flags (mesmo que simples, baseado em env vars)
- [OB-MEL-05] Configurar source maps upload para Sentry em pipeline de deploy
- [OB-MEL-06] Adicionar header `x-request-id` nas chamadas API do frontend

---

## Sumário de Achados por Severidade

### Críticos (2)
| ID | Dimensão | Descrição | Arquivo |
|----|----------|-----------|---------|
| OB-CRI-01 | 20 | @sentry/nextjs não instalado — captura de erros inativa | package.json |
| OB-CRI-02 | 20 | Sentry.captureException comentado no ErrorBoundary | error-boundary.tsx:35 |

### Importantes (6)
| ID | Dimensão | Descrição | Arquivo |
|----|----------|-----------|---------|
| DX-IMP-01 | 16 | Ausência de pre-commit hooks (Husky/lint-staged) | — |
| DX-IMP-02 | 16 | ESLint e TS errors ignorados no build | next.config.js:19-24 |
| DX-IMP-03 | 16 | README é template padrão sem info do projeto | README.md |
| BR-IMP-01 | 17 | Browserslist não explicitamente configurado | package.json |
| BR-IMP-02 | 17 | Sem testes cross-browser Safari/WebKit | — |
| BR-IMP-03 | 17 | Sem `<noscript>` fallback | layout.tsx |

### Melhorias (20)
| ID | Dimensão | Descrição |
|----|----------|-----------|
| DX-MEL-01 | 16 | Criar .editorconfig |
| DX-MEL-02 | 16 | Criar ADRs formais em `plataforma-lia/docs/adr/` (nota: existe `docs/adr/` no monorepo raiz, mas não dentro de `plataforma-lia/`) |
| DX-MEL-03 | 16 | Resolver duplo lock file (npm vs bun) |
| DX-MEL-04 | 16 | Avaliar substituição de html2canvas |
| BR-MEL-01 | 17 | Adicionar browserslist explícito |
| BR-MEL-02 | 17 | Configurar Playwright para WebKit (atualmente apenas Chromium configurado) |
| BR-MEL-03 | 17 | Adicionar `<noscript>` tag |
| BR-MEL-04 | 17 | Implementar `@media (forced-colors: active)` |
| BR-MEL-05 | 17 | Detectar conexão lenta via navigator.connection |
| AN-MEL-01 | 18 | progressShrink: usar scaleX() em vez de width |
| AN-MEL-02 | 18 | Blocos CSS órfãos em animations.css |
| AN-MEL-03 | 18 | .animate-slide-in definida 2x com valores diferentes |
| TP-MEL-01 | 19 | Planejar carregamento condicional para futuro analytics |
| TP-MEL-02 | 19 | Planejar SRI para futuras CDNs |
| OB-MEL-01 | 20 | Instalar @sentry/nextjs e ativar integração |
| OB-MEL-02 | 20 | Implementar reportWebVitals |
| OB-MEL-03 | 20 | Adicionar Sentry.setUser() após login |
| OB-MEL-04 | 20 | Implementar feature flags |
| OB-MEL-05 | 20 | Configurar source maps upload para Sentry |
| OB-MEL-06 | 20 | Adicionar x-request-id nas chamadas API |

---

## Notas de Validação

Comandos e critérios utilizados nas verificações:

| Verificação | Método |
|-------------|--------|
| ESLint/Biome config | Leitura direta de `eslint.config.mjs`, `biome.json` |
| Pre-commit hooks | glob por `.husky/**/*` — diretório inexistente |
| .editorconfig | glob por `.editorconfig` — arquivo inexistente |
| Prettier | glob por `.prettierrc*` — nenhum arquivo encontrado |
| Path aliases | Leitura de `tsconfig.json` paths |
| Storybook | glob por `.storybook/**/*` — 3 arquivos encontrados |
| ADRs | glob por `docs/adr/**/*` dentro de `plataforma-lia/` — inexistente |
| Lock files | Verificação de `package-lock.json` e `bun.lock` |
| Browserslist | grep por `browserslist` — encontrado apenas em lock files |
| prefers-reduced-motion | grep recursivo em `plataforma-lia/src` — 5 locais |
| console.log em produção | grep por `console\.(log\|debug\|info\|warn)` em `src/**/*.{ts,tsx}` — 0 matches |
| will-change | grep em `plataforma-lia/src` — 3 ocorrências (todas `auto !important`) |
| transition-all em .tsx | grep em `src/**/*.tsx` — 0 matches (CSS-only em components.css) |
| Sentry instalado | grep por `@sentry/nextjs` em `package.json` — não encontrado |
| Scripts de terceiros | grep por gtag, analytics, dataLayer, fbq, hotjar etc. — 0 matches relevantes |
| CDN externas | grep por `cdn.`, `unpkg`, `jsdelivr` — 0 matches |
| SRI | grep por `integrity=` em `src/` — 0 matches |
| Core Web Vitals | grep por `web-vitals`, `reportWebVitals` — não implementado |
| Feature flags | grep por `feature.?flag`, `LaunchDarkly`, `unleash` — apenas dados demo |
| Correlation ID | grep por `correlation.?id`, `x-request-id` — 0 matches no frontend |

Escopo: todas as verificações limitadas ao diretório `plataforma-lia/` (pacote frontend). Backend e monorepo raiz fora de escopo.

---

*Relatório gerado em 2026-03-30 — Auditoria diagnóstica, sem correções de código aplicadas.*
