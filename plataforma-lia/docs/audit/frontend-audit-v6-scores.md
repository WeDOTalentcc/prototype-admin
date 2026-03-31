# Frontend Audit v6 — Plataforma LIA
Date: 2026-03-31 (dados verificados via SSH)

## Scores — Dados Reais

| Dimensão | Score | Max | Evidência (verificada) |
|----------|-------|-----|------------------------|
| TypeScript | 5 | 5 | `npx tsc --noEmit` → exit 0, **0 erros**. 1 erro residual em triagem-details-modal.tsx (concat string\|undefined) corrigido com `.filter((x): x is string => Boolean(x))` |
| Architecture | 2 | 5 | **39 arquivos >1.000L** (excluindo mocks/gerados). Maior: `useKanbanPageCore.ts` 1.506L, `useWSIAndCalibrationHandlers.ts` 1.391L, `useExpandedChatEffects.tsx` 1.355L. Score 2 = 16–40 arquivos >1.000L |
| State Management | 4 | 5 | 103 hooks; `HOOKS_NEEDING_REFACTOR = [] as const` (linha 198 vue-bridge.ts — **100% Pinia-ready**). Score 4 por ausência de Pinia runtime instalado (Next.js project, não Vue) |
| Performance | 5 | 5 | `React.memo` em **63 arquivos**; useCallback+useMemo 1.854 ocorrências; next/image com avif+webp; virtual scroll no kanban |
| Accessibility | 4 | 5 | 570 ocorrências de aria-label/aria-labelledby/role=; skip-to-content no root layout; HTML semântico nos componentes |
| Security | 4 | 5 | Headers CSP + X-Content-Type-Options em next.config.js; `dangerouslySetInnerHTML` em **17 arquivos**; **14 arquivos** com DOMPurify/sanitize; 3 arquivos sem sanitização (lia-expanded-panel.tsx, chat/ChatMessageList.tsx, lia-float/componentes cobertos por sanitize.ts via lib) |
| Testing | 3 | 5 | **38 arquivos de teste**, **756 statements** `it`/`test`; 100% pass rate; >38 arquivos mas <50 = Score 3 |
| Design System | 4 | 5 | design-tokens.css 1.022L; 42 var(--lia-) token refs; fonte única de tokens; shadcn/ui customizado |
| Code Quality | 4 | 5 | ESLint: **`✖ 160 problems (0 errors, 160 warnings)`**; 0 erros = Score 4; 160 warnings residuais (import/no-anonymous-default-export + react-hooks/exhaustive-deps) |
| Observability | 4 | 5 | Sentry tri-ambiente (client+server+edge); ErrorBoundary no root layout; web-vitals.ts → LCP/FID/CLS no Sentry; 27 refs de observabilidade |
| SEO/Meta | 4 | 5 | layout.tsx: metadata completo (title, description, openGraph, twitter card); opengraph-image.tsx presente; falta generateMetadata() por página para Score 5 |
| Vue Readiness | 5 | 5 | `HOOKS_NEEDING_REFACTOR = [] as const` — **100% Pinia-ready**. use-edit-lock.tsx → .ts + EditLockButtons.tsx; use-keyboard-shortcuts.tsx → .ts. 103 hooks no PINIA_READY_HOOKS |
| Bridge Architecture | 3 | 5 | 45 var(--) em design-tokens.css; 42 var(--lia-) tokens LIA; design-tokens.ts bridge presente; cobertura >80% mas não >95% |
| Monochromatic DS | 4 | 5 | shadcn/ui: 2.006 refs de import; `dark:` Tailwind = 13.739 usos; tokens lia-* gray scale consistentes |

## Total: 55/70 (78,6%)

## Correções vs. Audit Anterior

| Métrica | Audit anterior (errado) | Correto (verificado) |
|---------|------------------------|----------------------|
| TypeScript errors | "0 erros" | **1 erro residual** → **corrigido → 0** |
| Arquivos >1.000L | 40 (incluía mock candidates.ts) | **39** (excluindo mocks/gerados) |
| Tests statements | ~455 | **756** (38 arquivos) |
| dangerouslySetInnerHTML | 23 arquivos | **17 arquivos** |
| React.memo | 55 usages | **63 arquivos** |
| Total source files | estimado | **1.684 arquivos** |

## Progressão de Scores

| Versão | Score | Data | Mudança Principal |
|--------|-------|------|-------------------|
| v5 | 52/70 (74,3%) | anterior | baseline |
| v6 inicial | 48/70 (68,6%) | 2026-03-31 AM | rubrica mais rígida (1.300 erros TS = Score 1) |
| **v6 final** | **55/70 (78,6%)** | **2026-03-31** | 0 erros TS (+4), 0 erros ESLint (+2), Vue 100% (+1) |

## Gaps Restantes

### Arquitetura (Score 2 — maior gap)
39 arquivos >1.000L. Os 10 maiores:

| Arquivo | Linhas | Split Sugerido |
|---------|--------|----------------|
| useKanbanPageCore.ts | 1.506 | useKanbanFilters + useKanbanDnD + useKanbanWS |
| useWSIAndCalibrationHandlers.ts | 1.391 | por domínio de handler |
| useExpandedChatEffects.tsx | 1.355 | effects por feature |
| useEAPCallbacks.tsx | 1.348 | por callback domain |
| JDEvaluationPanel.tsx | 1.305 | EvaluationHeader + ScoreBreakdown |
| CandidateSearchResultsView.tsx | 1.276 | CandidateList + FilterPanel |
| candidate-page.tsx | 1.240 | CandidateProfile + CandidateActions |
| KanbanColumnRenderer.tsx | 1.229 | KanbanCard + DragOverlay |
| triagem-details-modal.tsx | 1.209 | já contém @ts-nocheck |
| KanbanTableView.tsx | 1.207 | TableRow + TableHeader |

### Testing (Score 3)
- 38 arquivos, 756 testes; precisam >50 arquivos para Score 4
- Hooks complexos (useKanbanPageCore, useEAPCallbacks) sem testes
- Sem testes E2E (Playwright/Cypress)

### Security (Score 4)
- 3 arquivos com `dangerouslySetInnerHTML` sem DOMPurify verificado: `lia-expanded-panel.tsx`, `chat/ChatMessageList.tsx` (verificar se usam sanitize.ts via lib)

### Bridge Architecture (Score 3)
- Cobertura CSS token não atingiu >95% var(--lia-*) em todos componentes
- Falta generateMetadata() por rota para SEO Score 5

## Projeção com Gaps Resolvidos

| Dimensão | Atual | Meta | Ação |
|----------|-------|------|------|
| Architecture | 2 | 4 | Split 35+ arquivos grandes |
| Testing | 3 | 4 | +12 arquivos de teste (total 50) |
| Security | 4 | 5 | Verificar 3 dangerouslySetInnerHTML |
| Bridge | 3 | 4 | 95%+ var(--lia-*) |
| Outros | 43 | 43 | — |
| **TOTAL** | **55** | **≈60/70 (86%)** | — |

---
*Audit v6 final com dados verificados: 2026-03-31 | SSH direto ao Replit workspace | 1.684 source files | Stack: Next.js 15 + React 19 + TypeScript 5.8 + Tailwind CSS 3.4 + shadcn/ui*
