# Auditoria Frontend — Relatório Final Consolidado

**Projeto:** Plataforma LIA (WeDo Talent)  
**Data:** 2026-03-30  
**Escopo:** Frontend (plataforma-lia/)  
**Método:** Auditoria estática — inspeção de código fonte, configurações e dependências  
**Relatórios base:** Parte 1 (dims 1-5), Parte 2 (dims 6-10), Parte 3 (dims 11-15), Parte 4 (dims 16-20)  
**Dimensões auditadas:** 20 de 20  
**Codebase:** 1.540 arquivos (709 TSX + 831 TS), 398.179 linhas em `src/`

---

## Contexto do Projeto

| Aspecto | Detalhe |
|---------|---------|
| **Stack Frontend** | Next.js 15.3.2 (App Router), React 19, Tailwind CSS 3.4.17, TypeScript 5.8.3 |
| **UI Library** | Radix UI (shadcn/ui), Lucide React (ícones), Sonner (toasts) |
| **Data Fetching** | SWR (instalado, subutilizado), fetch nativo, serviços customizados |
| **Validação** | Zod v4 (server-side), validação manual (client-side) |
| **Backend** | FastAPI consumido via `/api/backend-proxy` (proxy Next.js) |
| **Volume** | ~91 rotas, ~437 componentes, ~97 hooks, 30+ componentes >1.000 linhas |
| **Testes** | Vitest (unit/hooks), Playwright (E2E), Storybook (visual) |
| **CI/CD** | GitHub Actions (4 workflows: CI, E2E, Deploy, Docker) |
| **Design System** | Tokens CSS customizados (LIA DS), ESLint rules para enforcement |
| **Browsers alvo** | Não explicitamente configurado (defaults do Next.js) |
| **Idioma** | Monolíngue pt-BR (sem i18n) |

---

## Tabela de Scores — 20 Dimensões

| # | Dimensão | Score | Status | Relatório |
|---|----------|-------|--------|-----------|
| 1 | Qualidade de Código | **1.5 / 3** | 🔴 Crítico | Parte 1 |
| 2 | Arquitetura CSS | **2.0 / 3** | ⚠️ Parcial | Parte 1 |
| 3 | Performance de Renderização | **1.5 / 3** | 🔴 Crítico | Parte 1 |
| 4 | Performance de Bundle/Assets | **0.5 / 3** | 🔴 Crítico | Parte 1 |
| 5 | Design System e UI | **2.5 / 3** | ✅ Bom | Parte 1 |
| 6 | Acessibilidade | **2.0 / 3** | ⚠️ Parcial | Parte 2 |
| 7 | Segurança | **1.0 / 3** | 🔴 Crítico | Parte 2 |
| 8 | Integração com APIs | **2.0 / 3** | ⚠️ Parcial | Parte 2 |
| 9 | Routing e Navegação | **1.5 / 3** | 🔴 Insuficiente | Parte 2 |
| 10 | Gestão de Formulários | **1.5 / 3** | ⚠️ Parcial | Parte 2 |
| 11 | Internacionalização e Localização | **0.0 / 3** | 🔴 Ausente | Parte 3 |
| 12 | SEO e Metadados | **1.0 / 3** | 🔴 Mínimo | Parte 3 |
| 13 | Compliance e Legal | **2.0 / 3** | ⚠️ Parcial | Parte 3 |
| 14 | Qualidade de Produto e UX | **2.0 / 3** | ✅ Bom com lacunas | Parte 3 |
| 15 | Testabilidade e Cobertura | **2.0 / 3** | ✅ Fundação sólida | Parte 3 |
| 16 | Developer Experience | **2.0 / 3** | ✅ Bom | Parte 4 |
| 17 | Compatibilidade de Browsers | **1.0 / 3** | 🔴 Básico | Parte 4 |
| 18 | Animações e Transições | **3.0 / 3** | ✅ Excelente | Parte 4 |
| 19 | Scripts de Terceiros | **3.0 / 3** | ✅ Excelente | Parte 4 |
| 20 | Observabilidade | **1.0 / 3** | 🔴 Básico | Parte 4 |

### Score Consolidado

| Métrica | Valor |
|---------|-------|
| **Score Total (20 dimensões)** | **33.0 / 60** |
| **Média por dimensão** | **1.65 / 3** |
| **Percentual** | **55.0%** |

### Referência de Leitura (escala /60)

| Faixa | Classificação | Status do Projeto |
|-------|---------------|-------------------|
| 0-20 | 🔴 Crítico | Riscos graves, parar e corrigir |
| 21-35 | ⚠️ Frágil | Funciona mas com riscos significativos |
| 36-48 | ✅ Sólido | Boa base, melhorias incrementais |
| 49-60 | 🏆 Maduro | Excelência, manutenção contínua |

**Classificação: ⚠️ Frágil (33.0/60)** — O projeto funciona e tem fundações sólidas em várias áreas (animações, design system, scripts de terceiros, UX), mas possui riscos significativos em segurança, performance de bundle, observabilidade e gaps estruturais (i18n, SEO, browser compat).

---

## Destaques Positivos

Antes de abordar os problemas, vale reconhecer os pontos fortes identificados:

| Área | Destaque |
|------|----------|
| Design System (5) | Design tokens centralizados em CSS (996 linhas) e TypeScript (470+ linhas) com 20+ variantes de texto, 7 de card, 7 de botão, 12 de badge. shadcn/ui com 50+ componentes base. Mapeamento Vuetify preparado para migração futura. |
| Animações (18) | Implementação exemplar de `prefers-reduced-motion` em 4 camadas (CSS global + componentes + JS utility). Todas as animações respeitam acessibilidade. |
| Scripts de terceiros (19) | Zero scripts externos no frontend — sem analytics, chat widgets, CDNs. Bundle limpo e controlado. |
| Console.log | Zero ocorrências de `console.log/debug/info` em produção — excelente higiene de código. |
| Serviços API (8) | Camada `services/` bem organizada com ~30 arquivos temáticos e objeto unificado `liaApi`. |
| LGPD/Compliance (13) | Portal completo de privacidade com 5 tipos de solicitação LGPD Art. 18, portal do titular e painel admin. |
| UX (14) | Loading states, empty states, skeleton loaders e error boundary implementados de forma consistente. |
| Testes de hooks (15) | 21 hooks testados com `renderHook`/`act`, cobrindo happy path e edge cases. |
| CI Pipeline (15) | 4 workflows GitHub Actions cobrindo lint, type check, testes, E2E e deploy. |
| Design System | ESLint rules customizadas previnem uso de tokens deprecated. Regras de linting do DS funcionam (0 violações). |

---

## Matriz de Prioridade Consolidada

### 🚨 Bloqueadores (Correção imediata — risco de segurança ou falha em produção)

| ID | Dim | Achado | Impacto | Ref |
|----|-----|--------|---------|-----|
| BLQ-01 | 4 | Bundle principal `app/page.js` com 49.7MB — total JS ~72MB; rota principal inclui toda a aplicação no chunk inicial | First Contentful Paint e Time to Interactive catastróficos; ~60x acima do threshold de 250KB gzipped | Parte 1 §4.1 |
| BLQ-02 | 4 | `Cache-Control: no-store, no-cache` aplicado a TODAS as rotas incluindo assets estáticos | Cada navegação recarrega ~63MB de JS; destrutivo para performance percebida | Parte 1 §4.4 |
| BLQ-03 | 7 | ~20 usos de `dangerouslySetInnerHTML` sem sanitização (DOMPurify ausente) | XSS stored/reflected via mensagens de chat, templates de email, previews de comunicação | Parte 2 §7 |
| BLQ-04 | 7 | Ausência total de CSP (Content Security Policy) | Sem segunda camada de defesa contra XSS; agrava BLQ-03 | Parte 2 §7 |
| BLQ-05 | 7 | Tokens JWT em localStorage | Combinado com XSS (BLQ-03), permite roubo completo de sessão | Parte 2 §7 |
| BLQ-06 | 7 | 11 vulnerabilidades npm (2 critical, 6 high) — Next.js RCE, jspdf 10 CVEs | Exploits conhecidos com CVEs públicos | Parte 2 §7 |
| BLQ-07 | 20 | `@sentry/nextjs` referenciado mas NÃO instalado — captura de erros inativa | Erros em produção são invisíveis; sem telemetria de falhas | Parte 4 §20 |
| BLQ-08 | 15 | Deploy (`deploy.yml`) não depende do CI — merge direto faz deploy sem testes | Código não testado pode ir para produção | Parte 3 §15 |

### 🔶 Alta Prioridade (Próximo sprint — impacto significativo na qualidade)

| ID | Dim | Achado | Impacto | Ref |
|----|-----|--------|---------|-----|
| ALT-01 | 1 | 30+ componentes com >1.000 linhas (top: `ats-integrations-page` 1.522 linhas) | Múltiplas responsabilidades misturadas; manutenção e testabilidade comprometidas | Parte 1 §1.1 |
| ALT-02 | 1 | TypeScript relaxado: `noImplicitAny: false`, `no-explicit-any: off`, `no-unused-vars: off` | Sem guardrails de tipo; bugs de runtime passam despercebidos em 398k linhas | Parte 1 §1.2 |
| ALT-03 | 3 | 153 arquivos com `key={index}` ou `key={i}` em listas | Re-renders desnecessários e bugs de reconciliação em kanban, tabelas, formulários dinâmicos | Parte 1 §3.1 |
| ALT-04 | 3 | Apenas 4 arquivos usam `React.memo` vs 4.192 useState; ratio memo/state de 0.43 | Componentes >1.000 linhas re-renderizam sub-árvores inteiras a cada mudança de estado | Parte 1 §3.2 |
| ALT-05 | 4 | `images: { unoptimized: true }` + `@next/next/no-img-element: off` | Todas as imagens servidas no formato/tamanho original, sem lazy loading | Parte 1 §4.3 |
| ALT-06 | 6 | Labels de formulário sem `htmlFor`/`id` em login, register, forgot-password | Screen readers não conseguem associar labels a campos | Parte 2 §6 |
| ALT-07 | 6 | Mensagens de erro sem `aria-describedby`, sem `aria-required`, sem `role="alert"` | Screen readers não anunciam erros contextualmente | Parte 2 §6 |
| ALT-08 | 8 | Ausência de retry com backoff em chamadas API | Falhas de rede = erro imediato sem recuperação | Parte 2 §8 |
| ALT-09 | 8 | AbortController usado em apenas ~7 de centenas de chamadas | Memory leaks e state updates em componentes desmontados | Parte 2 §8 |
| ALT-10 | 9 | Ausência de `not-found.tsx`, `error.tsx`, `loading.tsx` | Rotas inválidas mostram 404 genérico; sem error boundaries por rota; sem loading automático | Parte 2 §9 |
| ALT-11 | 9 | Sem proteção de role no middleware | Qualquer usuário autenticado acessa /admin até backend responder 403 | Parte 2 §9 |
| ALT-12 | 10 | Zod não integrado com formulários client-side; validação manual | Validação inconsistente, propensa a erros | Parte 2 §10 |
| ALT-13 | 10 | Sem preservação de dados em formulários ao navegar | Perda de trabalho do usuário em formulários longos | Parte 2 §10 |
| ALT-14 | 12 | Ausência de sitemap.xml, robots.txt, Open Graph, JSON-LD | SEO completamente inoperante | Parte 3 §12 |
| ALT-15 | 13 | Ausência de banner de cookies/consent manager | Não-conformidade LGPD para tracking futuro | Parte 3 §13 |
| ALT-16 | 13 | Logout não limpa todos os dados do localStorage | Dados de sessão anterior persistem após logout | Parte 3 §13 |
| ALT-17 | 15 | Cobertura de componentes ~5%; sem threshold de cobertura | Regressões em componentes não são detectadas por testes | Parte 3 §15 |
| ALT-18 | 16 | `eslint.ignoreDuringBuilds: true` e `typescript.ignoreBuildErrors: true` | Erros de lint e TS silenciados no build (mitigado parcialmente pelo CI) | Parte 4 §16 |
| ALT-19 | 20 | Core Web Vitals não monitorados; sem RUM | Zero visibilidade de performance real dos usuários | Parte 4 §20 |

### 📋 Backlog Técnico (Trimestre 1 — dívida técnica)

| ID | Dim | Achado | Ref |
|----|-----|--------|-----|
| BCK-01 | 1 | 15 regras de a11y desabilitadas em biome.json + `@next/next/no-img-element: off` | Parte 1 §1.3 |
| BCK-02 | 1 | Nomenclatura inconsistente de arquivos (kebab vs camelCase vs PascalCase) | Parte 1 §1.4 |
| BCK-03 | 2 | 139 usos de `!important` (78 em `onboarding-styles.css` — 1 a cada 3 linhas) | Parte 1 §2.1 |
| BCK-04 | 2 | Duplicação de tokens dark mode em 3 locais (globals.css, dark-mode.css, design-tokens.css) | Parte 1 §2.2 |
| BCK-05 | 2 | Dois sistemas de tokens CSS coexistentes (HSL shadcn + hex LIA) com overlap semântico | Parte 1 §2.3 |
| BCK-06 | 3 | 164 arquivos com setTimeout/setInterval; cleanup não garantido 1:1 | Parte 1 §3.3 |
| BCK-07 | 3 | 47 arquivos com addEventListener sem `passive: true` (de 59 totais) | Parte 1 §3.4 |
| BCK-08 | 3 | Apenas 1 arquivo usa virtualização; listas de candidatos/vagas renderizadas in-DOM | Parte 1 §3.5 |
| BCK-09 | 4 | Duas bibliotecas de gráficos (Recharts + Chart.js); html2canvas+jspdf+canvg sem dynamic() | Parte 1 §4.5 |
| BCK-10 | 5 | 553 valores arbitrários Tailwind em 226 arquivos; 875 inline styles em 211 arquivos | Parte 1 §5.1-5.2 |
| BCK-11 | 6 | Containers sem elementos semânticos (`<main>`, `<nav>`, `<footer>`) | Parte 2 §6 |
| BCK-12 | 7 | Fallback secret previsível em `session-crypto.ts` | Parte 2 §7 |
| BCK-13 | 7 | ~100+ usos de localStorage; dados de usuário/cliente sem necessidade clara | Parte 2 §7 |
| BCK-14 | 8 | SWR subutilizado (~5 de centenas de chamadas); sem interceptors centralizados | Parte 2 §8 |
| BCK-15 | 8 | Sem validação runtime de responses (apenas type assertion) | Parte 2 §8 |
| BCK-16 | 9 | `?next=` param do middleware não consumido pelo login page | Parte 2 §9 |
| BCK-17 | 9 | Filtros, paginação e tabs não persistidos na URL | Parte 2 §9 |
| BCK-18 | 9 | Sem tratamento de chunk load failure em deploys | Parte 2 §9 |
| BCK-19 | 10 | Ausência de máscaras de input (CPF, telefone, CEP) | Parte 2 §10 |
| BCK-20 | 10 | Validação apenas em submit; sem feedback em blur/change | Parte 2 §10 |
| BCK-21 | 12 | `force-dynamic` em layout.tsx desabilita SSG para todas as rotas | Parte 3 §12 |
| BCK-22 | 13 | Sentry carrega sem verificar consentimento do usuário | Parte 3 §13 |
| BCK-23 | 13 | Email em query params de SSO redirect (risco PII) | Parte 3 §13 |
| BCK-24 | 14 | `TOAST_REMOVE_DELAY = 1000000` (~16 min) — toasts não auto-dismiss | Parte 3 §14 |
| BCK-25 | 14 | Dois sistemas de toast simultâneos (Radix Toast + Sonner) | Parte 3 §14 |
| BCK-26 | 14 | Deep linking limitado em painéis internos (modais, tabs, filtros) | Parte 3 §14 |
| BCK-27 | 14 | Sem timeout de sessão no frontend | Parte 3 §14 |
| BCK-28 | 15 | Assertions com `.catch(() => {})` em E2E — testes passam silenciosamente em falha | Parte 3 §15 |
| BCK-29 | 15 | Nenhum teste de acessibilidade (axe-core, jest-axe); job CI de a11y é placeholder | Parte 3 §15 |
| BCK-30 | 16 | Ausência de pre-commit hooks (Husky/lint-staged) | Parte 4 §16 |
| BCK-31 | 16 | README é template padrão create-next-app sem informações do projeto | Parte 4 §16 |
| BCK-32 | 17 | Browserslist não explicitamente configurado | Parte 4 §17 |
| BCK-33 | 17 | Sem testes cross-browser em Safari/WebKit | Parte 4 §17 |
| BCK-34 | 20 | Sem correlation ID (x-request-id) entre frontend e backend | Parte 4 §20 |
| BCK-35 | 20 | Sem feature flags | Parte 4 §20 |

### 👁️ Observação Futura (90 dias — melhorias de maturidade)

| ID | Dim | Achado | Ref |
|----|-----|--------|-----|
| OBS-01 | 1 | Remover diretórios `_archived/` e dead code comentado | Parte 1 §1.5 |
| OBS-02 | 2 | Eliminar CSS morto em `components.css` (classes .bg-ai-aqua, .text-electric-red etc.) | Parte 1 §2.8 |
| OBS-03 | 2 | Adicionar estilos de impressão `@media print` para relatórios e fichas | Parte 1 §2.12 |
| OBS-04 | 3 | Habilitar `reactStrictMode: true` em `next.config.js` | Parte 1 §3.7 |
| OBS-05 | 4 | Lazy-load bibliotecas pesadas (html2canvas, jspdf, canvg) com `dynamic()` | Parte 1 §4.2 |
| OBS-06 | 5 | Migrar cores hardcoded hex em classes `.lia-*` para `var()` | Parte 1 §5.3 |
| OBS-07 | 5 | Habilitar `enableSystem={true}` no ThemeProvider para detectar preferência do OS | Parte 1 §5.5 |
| OBS-08 | 6 | Adicionar `aria-hidden="true"` explícito em ícones Lucide decorativos | Parte 2 §6 |
| OBS-09 | 6 | Configurar auditoria de contraste (axe-core, Lighthouse CI) | Parte 2 §6 |
| OBS-10 | 6 | Adicionar skip-to-content link no layout | Parte 2 §6 |
| OBS-11 | 8 | Configurar MSW para mocking em testes e desenvolvimento | Parte 2 §8 |
| OBS-12 | 8 | Implementar debounce centralizado em inputs de busca | Parte 2 §8 |
| OBS-13 | 9 | Adicionar breadcrumbs na área principal (não apenas admin) | Parte 2 §9 |
| OBS-14 | 10 | Adicionar date picker dedicado (substituir `type="date"` nativo) | Parte 2 §10 |
| OBS-15 | 10 | Implementar `beforeunload` listener para formulários com alterações não salvas | Parte 2 §10 |
| OBS-16 | 11 | Sistema de i18n — alto esforço (~3-5 sprints para retrofit completo) | Parte 3 §11 |
| OBS-17 | 12 | Metadata não uniforme entre páginas; `suppressHydrationWarning` amplo | Parte 3 §12 |
| OBS-18 | 15 | Testes de componentes não utilizam `@testing-library/dom` (disponível mas não usado) | Parte 3 §15 |
| OBS-19 | 15 | Componentes monolíticos difíceis de testar (`dashboard-app.tsx`, `expanded-chat-modal.tsx`) | Parte 3 §15 |
| OBS-20 | 16 | Criar `.editorconfig` para consistência entre editores | Parte 4 §16 |
| OBS-21 | 16 | Criar ADRs formais em `docs/adr/` | Parte 4 §16 |
| OBS-22 | 16 | Resolver duplo lock file (package-lock.json + bun.lock) | Parte 4 §16 |
| OBS-23 | 16 | Avaliar substituição de `html2canvas` por alternativa mais mantida | Parte 4 §16 |
| OBS-24 | 17 | Implementar `@media (forced-colors: active)` para alto contraste | Parte 4 §17 |
| OBS-25 | 17 | Adicionar `<noscript>` tag com fallback | Parte 4 §17 |
| OBS-26 | 17 | Detectar conexão lenta via `navigator.connection` | Parte 4 §17 |
| OBS-27 | 18 | `progressShrink` anima `width` — usar `transform: scaleX()` | Parte 4 §18 |
| OBS-28 | 18 | Blocos CSS órfãos em `animations.css` | Parte 4 §18 |
| OBS-29 | 18 | `.animate-slide-in` definida 2x com animações diferentes | Parte 4 §18 |
| OBS-30 | 19 | Planejar carregamento condicional para futuro analytics e SRI para CDNs | Parte 4 §19 |
| OBS-31 | 20 | Implementar `reportWebVitals`, `Sentry.setUser()`, source maps upload | Parte 4 §20 |

---

## Roadmap de Remediação

### Semana 1-2: Bloqueadores (BLQ-01 a BLQ-08)

| Ação | Dependência | Esforço | Responsável sugerido |
|------|-------------|---------|---------------------|
| Implementar code splitting agressivo com `dynamic()` para modais e componentes pesados; reduzir `app/page.js` de 49.7MB | Nenhuma | 3-5 dias | Frontend Sr |
| Remover `Cache-Control: no-store` de assets estáticos (JS, CSS, fontes, imagens); manter apenas para rotas API | Nenhuma | 0.5 dia | Frontend |
| Instalar DOMPurify e sanitizar todos os 20 usos de `dangerouslySetInnerHTML` | Nenhuma | 2-3 dias | Frontend Sr |
| Executar `npm audit fix` para vulnerabilidades non-breaking | Nenhuma | 0.5 dia | DevOps/Frontend |
| Atualizar `jspdf` para v4.2.1+ (breaking change — requer teste) | Após npm audit fix | 1 dia | Frontend |
| Configurar CSP headers via `next.config.js` ou middleware | Após DOMPurify (para definir allowed sources) | 1 dia | Frontend Sr |
| Instalar `@sentry/nextjs`, descomentar `captureException` no ErrorBoundary | Nenhuma | 0.5 dia | Frontend |
| Adicionar `needs: [frontend]` no `deploy.yml` do GitHub Actions | Nenhuma | 0.5 dia | DevOps |
| Migrar tokens para httpOnly cookies (ao menos refresh token) | Requer coordenação com backend | 2-3 dias | Full-stack |

### Mês 1: Alta Prioridade (ALT-01 a ALT-19)

| Ação | Dependência | Esforço |
|------|-------------|---------|
| Refatorar os 15 maiores componentes (>1.000 linhas) em sub-componentes | Nenhuma | 2-3 semanas |
| Habilitar `noImplicitAny: true` e `no-explicit-any: warn` incrementalmente | Nenhuma | 1 semana |
| Substituir `key={index}` por keys estáveis nos 153 arquivos afetados | Nenhuma | 3-5 dias |
| Adicionar `React.memo` em componentes de lista (kanban cards, candidate rows) | Após refatoração de componentes | 2 dias |
| Habilitar otimização de imagens: remover `images: { unoptimized: true }` | Nenhuma | 1 dia |
| Associar labels com `htmlFor`/`id` em login, register, forgot-password | Nenhuma | 1 dia |
| Adicionar `aria-describedby`, `aria-required`, `role="alert"` em formulários | Após labels | 1 dia |
| Criar `not-found.tsx`, `error.tsx`, `loading.tsx` em `src/app/` | Nenhuma | 1 dia |
| Adicionar verificação de role no middleware para rotas `/admin/*` | Nenhuma | 1 dia |
| Integrar Zod com React Hook Form (`zodResolver`) para validação client-side | Nenhuma | 3-5 dias |
| Implementar retry com backoff exponencial no fetch wrapper | Nenhuma | 2 dias |
| Adicionar AbortController em hooks de data fetching | Após retry wrapper | 2 dias |
| Criar sitemap.ts, robots.ts, adicionar Open Graph e canonical URLs | Nenhuma | 2 dias |
| Implementar banner de cookies/consent manager | Nenhuma | 2-3 dias |
| Limpar todos os dados de localStorage no logout | Nenhuma | 0.5 dia |
| Definir threshold de cobertura de testes e expandir testes de componentes | Nenhuma | 3-5 dias |
| Remover `ignoreBuildErrors` e corrigir erros de lint/TS pendentes | Nenhuma | 3-5 dias |
| Implementar `reportWebVitals` do Next.js | Após Sentry instalado (BLQ-07) | 1 dia |

### Trimestre 1: Dívida Técnica (BCK-01 a BCK-35)

| Fase | Ações agrupadas | Esforço estimado |
|------|-----------------|------------------|
| **CSS cleanup** | Reduzir 139 `!important`, eliminar duplicação de dark mode, consolidar 2 sistemas de tokens | 1-2 semanas |
| **Performance de render** | Cleanup timers/listeners, adicionar `passive: true`, implementar virtualização em listas longas | 1 semana |
| **Bundle optimization** | Consolidar chart libs (Recharts OU Chart.js), lazy-load html2canvas/jspdf/canvg | 1 semana |
| **Code quality** | Padronizar naming (kebab-case), reativar regras a11y no biome, remover dead code | 1 semana |
| **Resiliência de rede** | Retry wrapper, AbortController universal, debounce, timeout via AbortController | 1 semana |
| **Qualidade de formulários** | Máscaras (CPF, tel, CEP), validação blur/change, preservação de draft, `beforeunload` | 1 semana |
| **Routing** | Consumir `?next=` param, persistir filtros/tabs na URL, chunk load error handling | 1 semana |
| **Observabilidade** | Correlation ID, feature flags, source maps, `Sentry.setUser()` | 1 semana |
| **UX polish** | Unificar toasts (escolher Sonner), ajustar `TOAST_REMOVE_DELAY`, timeout de sessão | 3 dias |
| **DX** | Pre-commit hooks, README customizado, browserslist, `.editorconfig` | 3 dias |
| **Data fetching** | Migrar de `useEffect`+`fetch` para SWR/React Query | 2-3 semanas |

### Contínuo: Cultura e Processo

| Prática | Frequência |
|---------|-----------|
| `npm audit` no pipeline CI | A cada PR |
| Testes de acessibilidade (axe-core) no CI | A cada PR |
| Visual regression testing via Chromatic/Storybook | A cada PR |
| Code review checklist incluindo a11y, security, performance | Contínuo |
| Threshold de cobertura mínima (ex: 40% statements) | Enforcement no CI |
| Testes cross-browser (Safari/WebKit) no Playwright | Release mensal |
| Monitoramento de Core Web Vitals via Sentry/RUM | Contínuo |
| Revisão trimestral de dependências (`npm outdated`, `npm audit`) | Trimestral |
| ADRs para decisões arquiteturais significativas | Por decisão |

---

## Notas de Contexto

Decisões técnicas e restrições que explicam achados sem necessariamente serem problemas:

| Contexto | Explicação | Impacto na auditoria |
|----------|------------|---------------------|
| **Monolíngue pt-BR** | A plataforma é voltada ao mercado brasileiro. i18n (dim 11, score 0) reflete uma decisão de negócio, não uma falha técnica. Retrofit de i18n deve ser guiado por expansão internacional real, não por completude técnica. | Score 0 é factual, mas a prioridade de remediação é baixa (OBS-09). |
| **`force-dynamic` em layout.tsx** | Necessário para autenticação server-side e dados dinâmicos por usuário. Desabilitar SSG é consequência do modelo auth-first. | SEO impactado, mas a maioria das rotas é protegida e não deveria ser indexada. |
| **Animações Radix desabilitadas** | Decisão documentada em `globals.css` e `design-tokens.css` para consistência visual do Design System LIA. Reduz jank e é positivo para acessibilidade. | Não é defeito — é design intencional bem documentado. |
| **Sem scripts de terceiros** | O projeto não usa analytics, chat widgets ou tracking. Score 3/3 em dim 19 reflete um frontend limpo, mas analytics serão necessários eventualmente. | Positivo hoje; preparar infrastructure para futuro (consent gate, async loading). |
| **`eslint.ignoreDuringBuilds`** | Comentário no código indica "Sprint 8: pre-existing lint/TS errors — to be fixed in Sprint 9". O CI executa lint/tsc como steps separados antes do build, mitigando parcialmente o risco. | Dívida técnica reconhecida pela equipe; CI mitiga parcialmente. |
| **Dois lock files** | `package-lock.json` + `bun.lock` coexistem. Pode indicar migração em andamento de npm para bun, ou uso alternado. | Risco de inconsistência entre ambientes; resolver escolhendo um. |
| **SWR instalado mas subutilizado** | ~5 de centenas de chamadas usam SWR. A maioria usa `useEffect`+`useState`+`fetch`. Pode ser adoção incremental em progresso. | Perda de benefícios de cache/dedup/revalidação na maioria dos data fetches. |
| **Sentry preparado mas não instalado** | Config file existe (`sentry.client.config.ts`) com DSN via env var, replays, traces. O pacote `@sentry/nextjs` simplesmente não está nas dependências. Pode ser remoção intencional por custo ou problema de compatibilidade com Next.js 15/React 19. | Resolução simples: `npm install @sentry/nextjs` e descomentar captura. Verificar compatibilidade primeiro. |
| **Portal LGPD completo** | A plataforma tem infraestrutura robusta de compliance: portal de privacidade, DSR, consentimento, painel admin LGPD. Isso mitiga significativamente o risco de compliance mesmo com o banner de cookies ausente. | O banner é necessário para completude, mas a base de compliance é sólida. |

---

## Referências aos Relatórios Parciais

| Relatório | Dimensões | Localização |
|-----------|-----------|-------------|
| Parte 1 — Fundamentos | 1-5 | `docs/audit/frontend-audit-parte1-fundamentos.md` |
| Parte 2 — Segurança e Integrações | 6-10 | `docs/audit/frontend-audit-parte2-seguranca-integracoes.md` |
| Parte 3 — Capacidades | 11-15 | `plataforma-lia/docs/audit/frontend-audit-parte3-capacidades.md` |
| Parte 4 — DX e Infraestrutura | 16-20 | `docs/audit/frontend-audit-parte4-dx-infra.md` |

---

## Sumário Quantitativo

| Severidade | Quantidade | Distribuição por dimensão |
|------------|-----------|--------------------------|
| Bloqueadores | 8 | Bundle (1), Cache (1), Segurança (4), Observabilidade (1), CI/CD (1) |
| Alta Prioridade | 19 | Code Quality (2), Rendering (2), Bundle/Imagens (1), Acessibilidade (2), APIs (2), Routing (2), Formulários (2), SEO (1), Compliance (2), Testabilidade (1), DX (1), Observabilidade (1) |
| Backlog Técnico | 35 | Distribuídos em 16 dimensões |
| Observação Futura | 31 | Distribuídos em 14 dimensões |
| **Total de achados** | **93** | — |

### Dimensões mais críticas (menor score)

1. **Internacionalização (0/3)** — ausência total, mas baixa prioridade se mercado é apenas Brasil
2. **Bundle Size (0.5/3)** — chunk de 49.7MB, sem code splitting, imagens não otimizadas
3. **Segurança (1/3)** — XSS + JWT em localStorage + npm vulns = risco real e imediato
4. **SEO (1/3)** — sem sitemap, robots, OG, JSON-LD, cache headers inadequados
5. **Compatibilidade de Browsers (1/3)** — sem browserslist, sem testes cross-browser
6. **Observabilidade (1/3)** — Sentry não instalado, sem CWV, sem RUM
7. **Code Quality (1.5/3)** — componentes monolíticos, TypeScript sem guardrails
8. **Rendering Perf (1.5/3)** — key={index} em 153 arquivos, memo quase inexistente

### Dimensões mais fortes (maior score)

1. **Animações e Transições (3/3)** — implementação exemplar de a11y e performance
2. **Scripts de Terceiros (3/3)** — frontend limpo, sem dependências externas
3. **Developer Experience (2/3)** — ESLint + Biome + Storybook + CI bem configurados
4. **Qualidade de Produto e UX (2/3)** — loading states, empty states, error boundary sólidos
5. **Compliance e Legal (2/3)** — portal LGPD completo e robusto

---

*Relatório consolidado gerado em 2026-03-30 — Auditoria diagnóstica, sem correções de código aplicadas.*
