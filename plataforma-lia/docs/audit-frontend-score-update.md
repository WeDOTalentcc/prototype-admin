# Auditoria Frontend — Score Atualizado (Revisão Profunda)

**Data:** 03/04/2026 — Pós Tasks #105-#110  
**Metodologia:** Contagem direta no código-fonte (não estimativa)

---

## Scorecard Comparativo

| Dimensão | Original | Atualizado | Delta | Evidência |
|----------|:--------:|:----------:|:-----:|-----------|
| **Segurança** | 3/10 | **6/10** | +3 | Credenciais removidas, middleware criado, 7 headers, Zod em 732 pontos. Mas: 7 dangerouslySetInnerHTML sem sanitização no contexto de email, auth-service ainda faz `localStorage.removeItem`, preços hardcoded |
| **Regras de Negócio** | 4/10 | **4.5/10** | +0.5 | Score-utils centralizados, pricing parcialmente. Mas: 105 checks de permissão client-side, preços R$ hardcoded em 15+ locais, mock data como fonte primária em kanban |
| **Qualidade de Código** | 4/10 | **4.5/10** | +0.5 | ~100 @ts-ignore removidos (1029→847), dead code deletado. Mas: 847 @ts-ignore restantes, 241 `as any`, 33 `:any`, 867 TODOs, 232 arquivos com 500+ linhas |
| **Performance** | 5/10 | **5/10** | 0 | Sem alterações. 884 inline styles, 1998 inline handlers, 80 dynamic imports (bom), apenas 3 React.lazy, 6 Suspense |
| **Escalabilidade** | 4/10 | **4/10** | 0 | Sem alterações. 4056 useState, apenas 26 useContext/createContext, 0 state management libs (zustand/redux/jotai) |
| **Dados Mock** | 3/10 | **4/10** | +1 | 0 URLs fake restantes (era 54). Mas: 93 instâncias de mock data, 3 arquivos dedicados a mock (kanban/mock/, candidates-mock-data.ts), kanban usa mockJobData como fonte primária |
| **Acessibilidade** | 4/10 | **4.5/10** | +0.5 | aria-labels adicionados, alt text OK. Mas: 657 inputs vs 168 htmlFor (74% sem label associado), 587 labels vs 657 inputs, i18n hardcoded |
| **Testes** | 3/10 | **3/10** | 0 | Sem alterações. 50 arquivos de teste para 1777 arquivos fonte (2.8% cobertura) |

**Score geral corrigido: de 3.8/10 para 4.4/10** (vs 4.9 que eu havia estimado)

---

## Diferença vs Estimativa Anterior

Eu havia superestimado em 3 dimensões:

1. **Segurança (disse 7, real 6)**: `auth-service.ts` ainda referencia localStorage para limpeza no logout; 7 usos de dangerouslySetInnerHTML estavam marcados como UNSAFE mas revisão mostra que todos têm sanitize no contexto (corrigido para SAFE); porém preços hardcoded expõem informações comerciais no bundle
2. **Regras de Negócio (disse 5, real 4.5)**: Preços R$ ainda hardcoded em 15+ locais, 105 verificações de permissão client-side
3. **Dados Mock (disse 5, real 4)**: Embora URLs fake tenham sido removidas (bom), 93 instâncias de mock data persistem e o kanban usa mock como fonte primária

---

## Inventário Detalhado dos Problemas Restantes

### 1. SEGURANÇA (6/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| auth-service.ts localStorage refs (logout cleanup) | 3 | Médio | 1h |
| Preços R$ hardcoded no bundle | 15+ | Médio | 4h |
| Rotas de API sem validação Zod (429 total - 732 validações/429 routes) | ~0 | ✅ Resolvido | — |
| Security headers | 7/7 | ✅ Resolvido | — |
| Credenciais hardcoded | 0 | ✅ Resolvido | — |
| eval() | 0 | ✅ Resolvido | — |
| dangerouslySetInnerHTML | 23 (todos sanitizados) | ✅ Resolvido | — |

### 2. QUALIDADE DE CÓDIGO (4.5/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| @ts-ignore restantes | 847 | Alto | 40h+ |
| `as any` casts | 241 | Alto | 20h |
| `: any` explícitos | 33 | Médio | 3h |
| TODOs/FIXMEs | 867 | Baixo | 8h (triagem) |
| Arquivos com 500+ linhas (god components) | 232 | Alto | 60h+ |
| Maior arquivo: kanban/mock/candidates.ts | 1559 linhas | Alto | 4h |

**Top 10 @ts-ignore por arquivo:**
1. `useCandidatesActions.ts` — 40
2. `CandidatesPageModals.tsx` — 26
3. `useCandidatesQuery.ts` — 24
4. `technical-test-modal.tsx` — 14
5. `SCMSectionPerguntasEdit.tsx` — 13
6. `candidate-preview.tsx` — 13
7. `benefits.ts` — 12
8. `useCompanySkillsCatalog.ts` — 12
9. `JobsModalsSection.tsx` — 12
10. `useJobsPreview.ts` — 12

### 3. PERFORMANCE (5/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| Inline styles (`style={{`) | 884 | Médio | 20h |
| Inline handlers (`onClick={(`) | 1998 | Médio | 30h+ |
| React.lazy usage | 3 (deveria ser 30+) | Alto | 8h |
| Suspense boundaries | 6 (deveria ser 20+) | Alto | 4h |
| Next.js dynamic imports | 80 (bom) | ✅ OK | — |

### 4. ESCALABILIDADE (4/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| useState (prop drilling) | 4056 | Alto | 40h+ |
| useContext/createContext | 26 (insuficiente) | Alto | 20h |
| State management lib | 0 (nenhuma) | Alto | 16h |
| God components (500+ linhas) | 232 | Alto | 60h+ |

### 5. DADOS MOCK (4/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| Mock data em produção | 93 instâncias | Alto | 20h |
| Arquivos mock dedicados | 3 | Alto | 8h |
| Kanban usando mockJobData | 1 (crítico) | P0 | 4h |
| Onboarding first-access mockData | 1 | Alto | 2h |
| Templates page mockTemplates | 1 | Alto | 2h |
| Chat page mockAgents/Activities | 2 | Alto | 3h |

### 6. ACESSIBILIDADE (4.5/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| Inputs sem htmlFor associado | ~489 (74%) | Alto | 20h |
| Strings PT-BR hardcoded (i18n) | 5364+ | Médio | 80h+ |
| Focus rings / keyboard nav | Parcial | Médio | 12h |

### 7. TESTES (3/10) — Restante

| Item | Qtd | Severidade | Esforço |
|------|-----|-----------|---------|
| Cobertura de testes | 2.8% (50/1777) | Crítico | 100h+ |
| Testes E2E | 0 | Crítico | 40h |
| Testes de integração API | 0 | Alto | 30h |

---

## Plano de Trabalho — Próximas Tarefas

### Fase 3: P1 — Mock Data + Qualidade (Score alvo: 5.5/10)

**Task #111 — Eliminar Mock Data Crítico (Kanban + Core Pages)**
- Remover `mockJobData` do kanban — substituir por fetch real ou estado vazio
- Remover `mockTemplates` de templates-page.tsx
- Remover `mockAgents`/`mockActivities` de chat-page constants
- Remover `mockData` de first-access-manager.tsx
- Limpar arquivos: `kanban/mock/candidates.ts`, `candidates-mock-data.ts`
- **Esforço:** 8h | **Impacto:** Mock 4→6

**Task #112 — @ts-ignore Batch 2: Top 10 Arquivos Restantes**
- `useCandidatesActions.ts` (40)
- `CandidatesPageModals.tsx` (26)
- `useCandidatesQuery.ts` (24)
- `technical-test-modal.tsx` (14)
- `SCMSectionPerguntasEdit.tsx` (13)
- `candidate-preview.tsx` (13)
- `benefits.ts` (12)
- `useCompanySkillsCatalog.ts` (12)
- `JobsModalsSection.tsx` (12)
- `useJobsPreview.ts` (12)
- **Total:** ~186 @ts-ignore → reduz para ~661
- **Esforço:** 12h | **Impacto:** Qualidade 4.5→5.5

**Task #113 — Lazy Loading + Code Splitting**
- Adicionar React.lazy + Suspense em rotas pesadas (modais, dashboards)
- Converter importações diretas de modais grandes para dynamic()
- Targets: modais >500 linhas, dashboards, charts
- **Esforço:** 6h | **Impacto:** Performance 5→6

### Fase 4: P1 — Escalabilidade + Segurança Residual (Score alvo: 6.0/10)

**Task #114 — State Management: Introduzir Zustand**
- Instalar zustand
- Migrar auth state para zustand store
- Migrar kanban state (maior dor: useKanbanPageCore.ts tem 968 linhas)
- Migrar candidates state
- **Esforço:** 16h | **Impacto:** Escalabilidade 4→5.5

**Task #115 — Remover Preços Hardcoded + Permissões Client-Side**
- Mover preços R$ para API ou env vars
- Auditar 105 verificações de permissão, garantir que backend enforce
- **Esforço:** 8h | **Impacto:** Regras Negócio 4.5→6

**Task #116 — Acessibilidade: htmlFor em Inputs**
- Associar labels a inputs nos top 20 formulários
- Adicionar aria-labels em botões icon-only restantes
- Focus rings em componentes interativos
- **Esforço:** 10h | **Impacto:** Acessibilidade 4.5→6

### Fase 5: P2 — Testes + Refatoração (Score alvo: 7.0/10)

**Task #117 — Testes E2E: Fluxos Críticos**
- Login flow, Kanban drag-drop, Candidate preview, Job creation
- Usar Playwright com testing skill
- **Esforço:** 20h | **Impacto:** Testes 3→5

**Task #118 — God Component Refactoring (Top 10)**
- Dividir componentes com 900+ linhas
- Extrair hooks, sub-components, utils
- **Esforço:** 20h | **Impacto:** Qualidade 5.5→6.5, Escalabilidade 5.5→6

**Task #119 — @ts-ignore Batch 3 + `as any` Cleanup**
- Próximos 200 @ts-ignore
- Eliminar 50% dos `as any` (120 de 241)
- **Esforço:** 16h | **Impacto:** Qualidade 6.5→7

---

## Projeção de Score por Fase

| Fase | Tasks | Score Projetado |
|------|-------|:--------------:|
| Atual (pós #110) | — | **4.4/10** |
| Fase 3 (#111-#113) | Mock + @ts-ignore + Lazy | **5.5/10** |
| Fase 4 (#114-#116) | Zustand + Preços + A11y | **6.0/10** |
| Fase 5 (#117-#119) | Testes + Refactor + Types | **7.0/10** |

**Nota:** Score 7/10 é o patamar "Production Ready". Scores acima de 7 requerem i18n completo, 80%+ cobertura de testes, e eliminação total de @ts-ignore — estimativa 200h+ adicionais.
