# Plano de Trabalho — Correções da Auditoria Frontend

**Baseado em:** `audit-frontend-deep-analysis.md` + Security Scans (Dependency Audit, HoundDog)  
**Data:** 03/04/2026  
**Metodologia:** Análise profunda antes de cada etapa → correção → validação  
**Nota sobre dados mock:** São dados de simulação para testes — prioridade rebaixada para P3 (melhoria futura).

---

## Visão Geral do Plano

| Etapa | Foco | Criticidade | Esforço Est. | Dependência |
|-------|------|-------------|--------------|-------------|
| **E1** | Segurança — Credenciais e XSS | P0 Crítico | 3-4h | Nenhuma |
| **E2** | Segurança — Auth (localStorage → cookies, middleware) | P0 Crítico | 2-3 dias | E1 |
| **E3** | Segurança — Validação de API Routes + Headers | P1 Alto | 3-5 dias | E1 |
| **E4** | Regras de Negócio — Remover lógica client-side | P1 Alto | 2-3 dias | Nenhuma |
| **E5** | TypeScript — Eliminar @ts-ignore e tipagem fraca | P1 Alto | 5-7 dias | Nenhuma |
| **E6** | State Management — Zustand + Refactor useState | P1 Alto | 3-5 dias | E5 (parcial) |
| **E7** | Performance — Code Splitting, SWR, Memoização | P2 Médio | 5-7 dias | E6 |
| **E8** | Design System — Padronização DS v4.2.1 | P2 Médio | 3-5 dias | Nenhuma |
| **E9** | Acessibilidade e i18n | P2 Médio | 3-5 dias | E8 |
| **E10** | Testes — Cobertura mínima 30% | P2 Médio | 10-15 dias | E5, E6 |
| **E11** | Estrutura — God Components, Dead Code, Error Boundaries | P2 Médio | 5-7 dias | E5 |
| **E12** | Dados Mock — Isolamento (simulação/testes) | P3 Baixo | 2-3 dias | Nenhuma |

**Total estimado: 45-65 dias de trabalho**

---

## ETAPA 1: Segurança — Credenciais Hardcoded e XSS

**Criticidade:** P0 — Bloqueador de produção  
**Esforço:** 3-4 horas  
**Pré-análise obrigatória:** Rodar HoundDog scan + grep manual

### 1.1 Remover credencial hardcoded

**Arquivo:** `src/components/pages/login-page.tsx`  
**Linhas:** 72, 196, 459

**O que fazer:**
1. Remover a comparação `if (email === "ana.silva@sodexo.com" && password === "123456")`
2. Remover os textos de demo visíveis na UI
3. Se modo demo for necessário, implementar via variável de ambiente `NEXT_PUBLIC_DEMO_MODE` com credencial no backend

**Validação:**
- `grep -rn "ana.silva\|123456\|sodexo" plataforma-lia/src/` retorna 0 resultados
- Login demo ainda funciona (se habilitado via env var) ou foi removido intencionalmente

---

### 1.2 Sanitizar TODOS os dangerouslySetInnerHTML

**Arquivos afetados (sem sanitize):**

| # | Arquivo | Linha |
|---|---------|-------|
| 1 | `email-templates/email-template-form-modal.tsx` | 320 |
| 2 | `email-templates/email-templates-manager.tsx` | 485 |
| 3 | `email-templates/report-email-templates.tsx` | 723 |
| 4 | `email-templates/send-email-modal.tsx` | 283 |
| 5 | `ui/lia-expanded-panel.tsx` | 435 (userHtml) |
| 6 | `ui/lia-expanded-panel.tsx` | 471 (liaHtml) |

**O que fazer:**
1. Importar `sanitizeHtml` de `@/lib/sanitize` em cada arquivo
2. Envolver cada `__html:` com `sanitizeHtml()`:
   ```tsx
   dangerouslySetInnerHTML={{ __html: sanitizeHtml(content) }}
   ```
3. Verificar que `src/lib/sanitize.ts` usa DOMPurify com configuração segura

**Validação:**
- `grep -B1 "dangerouslySetInnerHTML" plataforma-lia/src/ -rn | grep -v sanitize` retorna 0 resultados (excluindo testes)
- Templates de email renderizam corretamente após sanitização
- Chat LIA renderiza HTML sem quebrar formatação

---

### 1.3 Remover URLs fake de produção

**Foco frontend (54 ocorrências):**

| Padrão | Ação |
|--------|------|
| `randomuser.me/api/portraits` | Substituir por `CandidateAvatar` (iniciais) |
| `pravatar.cc` | Substituir por `CandidateAvatar` (iniciais) |
| `teams.microsoft.com/l/meetup-join/...demo123` | Usar dado real do backend ou mostrar placeholder |
| `wa.me/5511999999999` | Usar número real do candidato/recrutador |

**Validação:**
- `grep -rn "randomuser.me\|pravatar.cc\|demo123\|999999999" plataforma-lia/src/` retorna 0 resultados (excluindo mock files)

---

## ETAPA 2: Segurança — Autenticação (localStorage → Cookies + Middleware)

**Criticidade:** P0 — Bloqueador de produção  
**Esforço:** 2-3 dias  
**Pré-análise obrigatória:** Mapear fluxo de auth completo, todos os usos de `getAccessToken()`  
**Dependência:** E1 concluída (XSS eliminado reduz risco durante migração)

### 2.1 Migrar tokens para httpOnly cookies

**Arquivo principal:** `src/services/auth-service.ts`

**O que fazer:**
1. Criar API route `src/app/api/auth/session/route.ts` que:
   - Recebe token do login
   - Seta cookie httpOnly, Secure, SameSite=Strict
   - Retorna apenas status
2. Modificar `auth-service.ts`:
   - `setTokens()` → faz POST para `/api/auth/session` em vez de localStorage
   - `getAccessToken()` → não mais necessário no client (cookie vai automaticamente)
   - `clearTokens()` → faz DELETE para `/api/auth/session`
3. Modificar API proxy routes para ler token do cookie em vez de header Authorization

**Impacto:** Todas as requisições autenticadas precisam ser testadas

**Validação:**
- `localStorage.getItem('lia_access_token')` retorna null
- Requisições autenticadas funcionam (cookie enviado automaticamente)
- Logout limpa cookie
- XSS não consegue acessar token (httpOnly)

---

### 2.2 Implementar middleware.ts de auth

**O que criar:** `plataforma-lia/src/middleware.ts`

**O que fazer:**
1. Verificar presença do cookie de sessão
2. Rotas públicas (allowlist): `/login`, `/privacidade`, `/portal/*`, `/vagas/*`, `/shared/*`, `/api/auth/*`
3. Rotas protegidas: tudo o resto → redirecionar para `/login` se sem sessão
4. Rotas admin: `/admin/*` → verificar role admin no token

**Validação:**
- Acessar `/dashboard` sem login → redireciona para `/login`
- Acessar `/admin` sem role admin → redireciona para `/`
- Rotas públicas acessíveis sem auth

---

## ETAPA 3: Segurança — Validação de API Routes + Security Headers

**Criticidade:** P1 — Alto  
**Esforço:** 3-5 dias  
**Pré-análise obrigatória:** Listar todas as 174 routes sem validação; categorizar por risco

### 3.1 Adicionar Zod validation às 174 routes restantes

**Metodologia:**
1. Listar routes sem validação: `find src/app/api -name "route.ts" -exec grep -L "zod\|safeParse" {} \;`
2. Categorizar:
   - **Alto risco (com body/params mutáveis):** POST/PUT/DELETE routes → prioridade
   - **Baixo risco (proxy passthrough):** GET routes que apenas encaminham → pode ser batch
3. Para cada route:
   - Definir Zod schema para body/params
   - Adicionar `safeParse` com retorno 400 em caso de erro
   - Manter schemas em `src/lib/schemas/` organizado por domínio

**Validação:**
- `find src/app/api -name "route.ts" -exec grep -L "zod\|safeParse" {} \;` retorna 0

---

### 3.2 Security Headers

**Arquivo:** `next.config.js`

**O que adicionar:**
```js
async headers() {
  return [{
    source: '/(.*)',
    headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'X-XSS-Protection', value: '1; mode=block' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
      { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com" },
    ],
  }]
}
```

**Validação:**
- Inspecionar response headers no browser DevTools
- App funciona normalmente com CSP

---

## ETAPA 4: Regras de Negócio — Remover Lógica Client-Side

**Criticidade:** P1 — Alto  
**Esforço:** 2-3 dias  
**Pré-análise obrigatória:** Mapear toda lógica de scoring, preços e permissões no frontend

### 4.1 Mover scoring/classificação para backend

**Arquivos afetados:**
- `app/admin/compliance/riscos/registro/page.tsx` — thresholds 15/10/5
- `app/admin/compliance/riscos/page.tsx` — thresholds 12/8/4 (INCONSISTENTE!)
- `components/ml-analytics/success-prediction.tsx` — thresholds 85/70
- `components/modals/candidate-compare-modal.tsx` — thresholds 80/60
- `app/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx` — thresholds 80/60

**O que fazer:**
1. Criar endpoint backend `/api/v1/scoring/classify` que recebe score e retorna label + CSS class
2. Ou: retornar `classification` já calculada junto com o score na API existente
3. Frontend apenas renderiza o que o backend retorna

**Validação:**
- `grep -rn "score >= [0-9]" plataforma-lia/src/` retorna 0 (excluindo CSS/progress bars)
- Classificações são consistentes (não mais 15 vs 12 para "Crítico")

---

### 4.2 Mover preços para configuração

**Arquivo:** `src/app/upgrade/UpgradeClient.tsx`

**O que fazer:**
1. Criar endpoint `/api/v1/plans/pricing` ou usar configuração do Stripe
2. Frontend busca preços da API ao montar componente
3. Preços deixam de estar no source code

---

## ETAPA 5: TypeScript — Eliminar @ts-ignore e Tipagem Fraca

**Criticidade:** P1 — Alto  
**Esforço:** 5-7 dias  
**Pré-análise obrigatória:** Rodar skill de diagnostics para LSP errors; classificar @ts-ignore por tipo de erro

### 5.1 Resolver @ts-ignore nos top 15 arquivos (concentram ~30%)

**Arquivos prioritários (>20 ignores cada):**

| # | Arquivo | @ts-ignore | Abordagem |
|---|---------|-----------|-----------|
| 1 | `useCandidatesPageCore.tsx` | 47 | Tipar candidate data com interface unificada |
| 2 | `useCandidatesActions.ts` | 40 | Tipar actions e payloads |
| 3 | `useWSIAndCalibrationHandlers.ts` | 28 | Definir tipos WSI |
| 4 | `CandidatesPageModals.tsx` | 26 | Props tipadas nas modais |
| 5 | `useCandidatesQuery.ts` | 24 | Response types da API |
| 6 | `lia-metrics-dashboard.tsx` | 24 | Chart data types |
| 7 | `report-email-templates.tsx` | 23 | Template types |

**Metodologia por arquivo:**
1. Analisar cada `@ts-ignore` — qual erro TypeScript está escondendo?
2. Criar interface/type correto
3. Remover `@ts-ignore`
4. Verificar que compila sem erros

---

### 5.2 Eliminar `as any` e `: any`

**274 ocorrências** (241 `as any` + 33 `: any`)

**Abordagem:** Batch por domínio (candidates, jobs, kanban, chat, settings)

---

## ETAPA 6: State Management — Zustand + Refactor useState

**Criticidade:** P1 — Alto  
**Esforço:** 3-5 dias  
**Pré-análise obrigatória:** Mapear estados compartilhados entre componentes  
**Dependência:** E5 parcial (tipos definidos)

### 6.1 Implementar stores Zustand

**Stores propostos:**

| Store | Responsabilidade | useState que substitui |
|-------|-----------------|----------------------|
| `useAuthStore` | user, role, permissions | auth-related em ~15 componentes |
| `useJobStore` | activeJob, previewJob, jobList | job-related em ~20 componentes |
| `useCandidateStore` | activeCandidate, previewCandidate, filters | candidate-related em ~25 componentes |
| `useUIStore` | modals, sidebars, theme, preferences | UI state em ~30 componentes |

### 6.2 Consolidar state explosions

**Top ofensores:**

| Componente | useState | Ação |
|-----------|----------|------|
| `comunicacoes/page.tsx` | 56 | useReducer + extrair sub-componentes |
| `useCandidatePageCore.tsx` | 36 | Migrar para useCandidateStore |
| `useEditJob.ts` | 28 | useReducer com estados agrupados |
| `useSetupEmpresa.ts` | 25 | useReducer + form state |
| `job-status-modal.tsx` | 21 | Agrupar em objeto de estado |

---

## ETAPA 7: Performance — Code Splitting, SWR, Memoização

**Criticidade:** P2 — Médio  
**Esforço:** 5-7 dias  
**Pré-análise obrigatória:** Rodar Next.js bundle analyzer; medir LCP/FID/CLS

### 7.1 Code splitting com dynamic imports

**Prioridades:**
1. Modais pesados (124 modais, maioria carregada no bundle inicial)
2. Páginas admin (compliance, configurações, métricas)
3. Charts (recharts, chart.js — libs pesadas)
4. Features não-críticas (ML analytics, email templates, WSI)

**Implementação:**
```tsx
const HeavyModal = dynamic(() => import('@/components/modals/heavy-modal'), {
  loading: () => <Skeleton className="h-96" />
})
```

### 7.2 Migrar fetch → SWR nas rotas principais

**Rotas de maior impacto:**
1. Lista de candidatos (`/api/backend-proxy/candidates`)
2. Lista de vagas (`/api/backend-proxy/jobs`)
3. Configurações da empresa
4. Dados do kanban
5. Perfil do candidato

**Benefícios:** Cache automático, deduplication, revalidação, retry

### 7.3 Memoização

1. `React.memo` em componentes de lista (KanbanCard, CandidateRow, JobRow)
2. Extrair inline styles para constantes
3. Converter inline handlers frequentes para useCallback

---

## ETAPA 8: Design System — Padronização DS v4.2.1

**Criticidade:** P2 — Médio  
**Esforço:** 3-5 dias  
**Pré-análise obrigatória:** Rodar skill `design-standardize` e `feature-audit` Dimensão 3  

### 8.1 Auditar conformidade DS v4.2.1

**Checklist da skill `design-standardize`:**
1. Regra 90/10 monocromática — verificar cores de acento fora de contexto
2. Tipografia — Open Sans (85%) + Inter (10%) + JetBrains Mono (5%)
3. Tokens canônicos — `--lia-*` vs hex hardcoded
4. Dark mode — todos os componentes suportam?
5. Espaçamento — escala base 4px
6. Bordas — `rounded-md` inputs, `rounded-lg` cards, `rounded-xl` modais
7. Sombras — `shadow-sm`/`shadow-md`/`shadow-lg` sem extremos

### 8.2 Padronizar cabeçalhos (Vaga vs Candidato)

Conforme identificado na análise anterior:
- Alinhar tamanho de título (ambos `textStyles.title`)
- Badge de ID: ambos com `text-[0.625rem] leading-none`
- Gap: padronizar `gap-1.5`
- Container: ambos com `rounded-lg`

### 8.3 Resolver conflitos Tailwind

4 elementos com `text-xs text-micro` conflitante — substituir por class explícita

---

## ETAPA 9: Acessibilidade e i18n

**Criticidade:** P2 — Médio  
**Esforço:** 3-5 dias  
**Pré-análise obrigatória:** Rodar Lighthouse accessibility audit; rodar skill `feature-audit` Dimensão 3.14

### 9.1 Corrigir imagens sem alt text

**42 imagens** sem `alt` — adicionar texto descritivo

### 9.2 Acessibilidade de formulários

1. Verificar `<Label htmlFor>` em todos os inputs
2. Verificar focus rings visíveis
3. Verificar contraste WCAG AA (4.5:1)
4. Verificar aria-labels em botões de ícone

### 9.3 Preparação para i18n

**5.364 strings hardcoded em PT-BR**

**Abordagem pragmática (sem full i18n imediato):**
1. Extrair strings para constantes centralizadas por domínio:
   - `src/constants/strings/candidates.ts`
   - `src/constants/strings/jobs.ts`
   - `src/constants/strings/common.ts`
2. Isso facilita futura migração para next-intl sem reescrever componentes

---

## ETAPA 10: Testes — Cobertura Mínima 30%

**Criticidade:** P2 — Médio  
**Esforço:** 10-15 dias  
**Pré-análise obrigatória:** Mapear fluxos críticos; rodar skill `lia-testing`  
**Dependência:** E5 (tipos corretos), E6 (estado gerenciável)

### 10.1 Testes unitários (Vitest)

**Prioridade por domínio:**

| Domínio | Arquivos-chave | Cobertura-alvo |
|---------|---------------|----------------|
| Auth | auth-service.ts, middleware.ts | 90% |
| Hooks de dados | useCandidatesQuery, useJobData | 70% |
| Utilitários | sanitize.ts, badge-utils.ts, formatters | 90% |
| Stores Zustand | useAuthStore, useJobStore | 80% |
| Componentes críticos | CandidatePreview, KanbanCard, Badge | 60% |

### 10.2 Testes e2e (Playwright)

**Fluxos críticos:**
1. Login → Dashboard
2. Criar vaga → Publicar → Ver no Kanban
3. Buscar candidato → Abrir preview → Mover no Kanban
4. Chat LIA → Enviar mensagem → Receber resposta
5. Configurações → Salvar → Persistir

---

## ETAPA 11: Estrutura — God Components, Dead Code, Error Boundaries

**Criticidade:** P2 — Médio  
**Esforço:** 5-7 dias  
**Pré-análise obrigatória:** Analisar cada god component; verificar imports de dead code

### 11.1 Quebrar god components (>500 linhas)

**Top 10 para refatorar:**

| Arquivo | Linhas | Ação |
|---------|--------|------|
| `useExpandedChatModalCore.tsx` | 1000 | Extrair: useMessageHandlers, useStreamingState, useChatActions |
| `triagem-details-modal.tsx` | 996 | Extrair seções em sub-componentes |
| `JDEvaluationPanel.tsx` | 993 | Extrair: JDHeader, JDScores, JDComparison |
| `usePromptState.ts` | 986 | Separar: promptConfig, promptHistory, promptValidation |
| `comunicacoes/page.tsx` | ~960 | Extrair: MatrixView, HistoryView, TemplatesView |

### 11.2 Remover dead code

**~15 componentes possivelmente não utilizados:**
1. Verificar referências com `grep -r "NomeComponente" src/`
2. Se 0 referências → remover arquivo
3. Se referência apenas em barrel export → remover do barrel também

### 11.3 Adicionar Error Boundaries

**Onde adicionar (mínimo):**
1. Cada `page.tsx` em `src/app/` — wraps o conteúdo da página
2. Componentes de alto risco: Chat, Kanban, Modais complexas
3. Widgets de terceiros: Charts, Maps
4. Componente genérico `ErrorFallback` com botão "Tentar novamente"

---

## ETAPA 12: Dados Mock — Isolamento (Prioridade Rebaixada)

**Criticidade:** P3 — Baixo (dados de simulação para testes)  
**Esforço:** 2-3 dias

### 12.1 Isolar mock data

1. Mover `kanban/mock/candidates.ts` para `__fixtures__/`
2. Condicionar carregamento a `NEXT_PUBLIC_DEMO_MODE`
3. Nunca importar mock data em componentes de produção

### 12.2 Substituir URLs fake restantes

Se alguma URL fake foi mantida na E1 por ser de simulação, documentar explicitamente e isolar.

---

## Ordem de Execução Recomendada

```
Semana 1-2:  E1 (3-4h) → E2 (2-3d) ← SEGURANÇA CRÍTICA
Semana 2-3:  E3 (3-5d) em paralelo com E4 (2-3d) ← SEGURANÇA + NEGÓCIO
Semana 3-5:  E5 (5-7d) ← FUNDAÇÃO PARA TUDO
Semana 5-6:  E6 (3-5d) + E8 (3-5d, paralelo) ← STATE + DESIGN
Semana 6-8:  E7 (5-7d) + E9 (3-5d, parcial paralelo) ← PERFORMANCE + A11Y
Semana 8-10: E11 (5-7d) ← ESTRUTURA
Semana 10-12: E10 (10-15d, contínuo) ← TESTES
Quando possível: E12 (2-3d) ← MOCK ISOLATION
```

---

## Métricas de Sucesso

| Métrica | Atual | Meta |
|---------|-------|------|
| @ts-ignore | 1.029 | < 50 |
| `as any` + `: any` | 274 | < 20 |
| TODOs | 1.015 | < 100 |
| dangerouslySetInnerHTML sem sanitize | 6 | 0 |
| API routes sem validação | 174 (41%) | 0 (0%) |
| Cobertura de testes | 2.7% | 30% |
| Error boundaries | 8 | 40+ |
| useState explosion (>15 por componente) | 15 arquivos | 0 |
| God components (>500 linhas) | 30 | < 5 |
| Imagens sem alt | 42 | 0 |
| Credenciais hardcoded | 1 | 0 |
| Tokens em localStorage | Sim | Não (httpOnly cookies) |
| Auth middleware | Não | Sim |
| Security headers | 0 | 6 |
