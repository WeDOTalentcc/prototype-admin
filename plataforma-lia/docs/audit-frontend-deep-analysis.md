# Auditoria Profunda — Frontend Plataforma LIA

**Data:** 03/04/2026  
**Stack:** React 19 + Next.js 15 + Tailwind CSS + Radix UI + SWR  
**Escopo:** 1.830 arquivos | 402.950 linhas de código | 54 dependências  

---

## Sumário Executivo

| Dimensão | Score | Veredicto |
|----------|-------|-----------|
| **Segurança** | 3/10 | Crítico — credenciais hardcoded, XSS parcial, tokens em localStorage, sem middleware de auth |
| **Regras de Negócio no Frontend** | 4/10 | Alto risco — scores, thresholds, preços e lógica de permissão no client |
| **Qualidade de Código** | 4/10 | Preocupante — 1.029 @ts-ignore, 1.015 TODOs, god components, state explosion |
| **Performance** | 5/10 | Moderado — pouco code splitting, 886 inline styles, 1.830 inline handlers |
| **Escalabilidade** | 4/10 | Preocupante — sem state management global, 4.050 useState, prop drilling |
| **Dados Mock em Produção** | 3/10 | Crítico — 92 instâncias de mock data, 54 URLs fake de avatar |
| **Acessibilidade** | 4/10 | Insuficiente — 42 imagens sem alt, i18n hardcoded (5.364 strings PT-BR) |
| **Testes** | 3/10 | Crítico — apenas 50 arquivos de teste para 1.830 arquivos de código (2.7% cobertura) |

**Nota geral: 3.8/10 — Código NÃO está pronto para produção em escala.**

---

## Parte 1: Vulnerabilidades de Segurança

### 1.1 CRÍTICO — Credencial Hardcoded em Código-Fonte

**Arquivo:** `src/components/pages/login-page.tsx` (linha 72)

```tsx
if (email === "ana.silva@sodexo.com" && password === "123456") {
```

E exibido na UI (linhas 196 e 459):
```tsx
<span className="font-medium">Demo:</span> ana.silva@sodexo.com / 123456
```

**Risco:** Credencial real de demonstração exposta no bundle JavaScript. Qualquer pessoa pode inspecionar o código e obter acesso.  
**Severidade:** P0 — Crítico  
**Fix:** Remover completamente. Se necessário modo demo, usar variável de ambiente e lógica server-side.

---

### 1.2 CRÍTICO — Tokens de Autenticação em localStorage

**Arquivo:** `src/services/auth-service.ts`

```tsx
localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
```

**Risco:** localStorage é acessível via JavaScript, tornando tokens vulneráveis a XSS. Se qualquer script malicioso for injetado (via dangerouslySetInnerHTML, por exemplo), ele pode roubar tokens de todos os usuários.  
**Severidade:** P0 — Crítico  
**Fix:** Migrar para httpOnly cookies server-side. Next.js 15 suporta isso nativamente via middleware.

---

### 1.3 ALTO — Ausência Total de Middleware de Auth

**Descoberta:** Nenhum arquivo `middleware.ts` encontrado no projeto.

**Risco:** Sem middleware Next.js, não há proteção server-side de rotas. Qualquer rota é acessível diretamente pela URL, mesmo sem autenticação. A proteção atual depende apenas de checks client-side que podem ser contornados.  
**Severidade:** P0 — Crítico  
**Fix:** Implementar `middleware.ts` na raiz do app com verificação de sessão/token para rotas protegidas.

---

### 1.4 ALTO — XSS via dangerouslySetInnerHTML Sem Sanitização

**20 usos de dangerouslySetInnerHTML** encontrados. A maioria usa `sanitizeHtml()` (DOMPurify), mas **4 instâncias NÃO sanitizam:**

| Arquivo | Linha | Status |
|---------|-------|--------|
| `email-template-form-modal.tsx` | 320 | Sem sanitize |
| `email-templates-manager.tsx` | 485 | Sem sanitize |
| `report-email-templates.tsx` | 723 | Sem sanitize |
| `send-email-modal.tsx` | 283 | Sem sanitize |
| `lia-expanded-panel.tsx` | 435, 471 | Sem sanitize (userHtml, liaHtml) |

**Risco:** Se o conteúdo HTML vier do backend ou de input do usuário sem sanitização, scripts maliciosos podem ser executados no contexto do usuário autenticado, roubando tokens (que estão em localStorage).  
**Severidade:** P1 — Alto  
**Fix:** Aplicar `sanitizeHtml()` (DOMPurify) em TODOS os usos de dangerouslySetInnerHTML sem exceção.

---

### 1.5 ALTO — 174 API Routes Sem Validação de Input

**425 API routes** no proxy backend. Apenas **59% (251)** usam validação Zod.  
**174 routes (41%)** aceitam qualquer payload sem validação.

**Risco:** Injection attacks, dados malformados propagados ao backend, erros não tratados.  
**Severidade:** P1 — Alto  
**Fix:** Adicionar Zod schemas a todas as API routes que aceitam body/params.

---

### 1.6 MÉDIO — Sem Security Headers

Nenhum cabeçalho de segurança configurado:
- Sem `Content-Security-Policy`
- Sem `X-Frame-Options`
- Sem `X-Content-Type-Options`
- Sem `Strict-Transport-Security`

**Fix:** Adicionar via `next.config.js` headers ou middleware.

---

### 1.7 MÉDIO — URLs e Dados Externos Hardcoded

54 URLs de avatar fake (`randomuser.me`, `pravatar.cc`) em código de produção.

| Padrão | Ocorrências |
|--------|-------------|
| `randomuser.me/api/portraits` | ~15 |
| `pravatar.cc` | ~5 |
| `teams.microsoft.com` links fake | ~3 |
| URLs de webhook/API hardcoded | ~5 |

**Risco:** Dependência de serviços externos gratuitos que podem mudar/cair; dados fake visíveis em produção; LGPD questionável (avatares de pessoas reais).  
**Fix:** Usar avatar gerado por iniciais (já existe `CandidateAvatar` component) ou placeholders locais.

---

## Parte 2: Regras de Negócio no Frontend

### 2.1 ALTO — Lógica de Scoring/Classificação no Client

Thresholds de score e classificação de risco estão hardcoded no frontend:

```tsx
// riscos/registro/page.tsx
if (score >= 15) return { label: 'Crítico' }
if (score >= 10) return { label: 'Alto' }
if (score >= 5) return { label: 'Médio' }

// riscos/page.tsx (VALORES DIFERENTES!)
if (score >= 12) return { label: 'Crítico' }
if (score >= 8) return { label: 'Alto' }
if (score >= 4) return { label: 'Médio' }
```

**Problema duplo:**
1. Regras de negócio que deveriam estar no backend
2. **Thresholds inconsistentes** entre páginas (15 vs 12 para "Crítico")

**Risco:** Regras podem ser manipuladas via DevTools; inconsistência confunde usuários; mudança exige deploy de frontend.  
**Fix:** Mover lógica de classificação para API backend; frontend apenas renderiza.

---

### 2.2 ALTO — Preços Hardcoded no Frontend

**Arquivo:** `src/app/upgrade/UpgradeClient.tsx`

```tsx
price: "R$ 990",    // Starter
price: "R$ 2.490",  // Professional
price: "Sob consulta", // Enterprise
```

**Risco:** Qualquer alteração de preço exige deploy. Preços visíveis no source code. Sem A/B testing possível.  
**Fix:** Buscar preços de API ou CMS.

---

### 2.3 MÉDIO — Lógica de Permissão Client-Side

Verificações de `isAdmin`, `canEdit`, `hasPermission` encontradas no frontend sem enforcement server-side correspondente (sem middleware).

**Risco:** Permissões podem ser contornadas alterando estado local.  
**Fix:** Sempre validar permissões no backend; frontend apenas esconde UI.

---

## Parte 3: Qualidade de Código

### 3.1 CRÍTICO — 1.029 @ts-ignore

| Arquivo | @ts-ignore |
|---------|-----------|
| `useCandidatesPageCore.tsx` | 47 |
| `useCandidatesActions.ts` | 40 |
| `useWSIAndCalibrationHandlers.ts` | 28 |
| `CandidatesPageModals.tsx` | 26 |
| `useCandidatesQuery.ts` | 24 |
| `lia-metrics-dashboard.tsx` | 24 |
| `report-email-templates.tsx` | 23 |
| Outros (962 arquivos) | 817 |

Adicionalmente: **241 `as any`** e **33 `: any`** explícitos.

**Impacto:** TypeScript perde sua utilidade como safety net. Bugs de tipo passam silenciosamente. Refactoring se torna perigoso.  
**Fix:** Criar tipos corretos; priorizar os top 15 arquivos que concentram ~30% dos ignores.

---

### 3.2 ALTO — God Components (>500 linhas)

**30 arquivos** com mais de 500 linhas. Top ofensores:

| Arquivo | Linhas |
|---------|--------|
| `kanban/mock/candidates.ts` | 1.559 |
| `useExpandedChatModalCore.tsx` | 1.000 |
| `triagem-details-modal.tsx` | 996 |
| `JDEvaluationPanel.tsx` | 993 |
| `usePromptState.ts` | 986 |

**Impacto:** Difícil de testar, manter e revisar. Re-renders desnecessários em componentes monolíticos.  
**Fix:** Extrair sub-componentes e hooks. Limite recomendado: 300 linhas por arquivo.

---

### 3.3 ALTO — State Explosion (4.050 useState)

| Hook/Componente | useState |
|----------------|----------|
| `configuracoes/comunicacoes/page.tsx` | 56 |
| `useCandidatePageCore.tsx` | 36 |
| `useEditJob.ts` | 28 |
| `useSetupEmpresa.ts` | 25 |
| `job-status-modal.tsx` | 21 |

**Impacto:** 56 useState num único componente é ingerenciável. Causa re-renders em cascata, bugs de estado stale, e impossibilita testes unitários.  
**Fix:** Consolidar em useReducer ou migrar para state management (Zustand); agrupar estados relacionados em objetos.

---

### 3.4 ALTO — 1.015 TODOs em Código

Mais de mil TODOs indicam dívida técnica acumulada não rastreada.

**Fix:** Converter TODOs em issues Jira com severidade; remover os obsoletos.

---

### 3.5 MÉDIO — Sem Estado Global

```
useState:    4.050
useContext:     15
useReducer:     1
Zustand/Redux:  2
```

Quase zero gerenciamento de estado global. Com 4.050 useState, o estado está espalhado e duplicado por todo o app.

**Impacto:** Prop drilling, estados inconsistentes entre componentes, dados re-fetched desnecessariamente.  
**Fix:** Implementar Zustand para estado global (auth, user, preferences, active job/candidate).

---

## Parte 4: Performance

### 4.1 ALTO — Pouco Code Splitting

```
dynamic():  80
lazy():     3
```

Apenas 80 dynamic imports para 791 componentes exportados (10%). Isso significa que a maioria do código é carregada no bundle inicial.

**Impacto:** First Load JS grande; Time to Interactive alto; penalidade em Core Web Vitals.  
**Fix:** Aplicar dynamic imports em modais, painéis de admin, e features não-críticas.

---

### 4.2 ALTO — 886 Inline Styles

```
style={{...}}: 886
```

Cada inline style cria um novo objeto a cada render, causando re-renders desnecessários em componentes filhos.

**Fix:** Mover para Tailwind classes ou constantes fora do JSX.

---

### 4.3 ALTO — 1.830 Inline Arrow Functions em Handlers

```tsx
onClick={() => handleAction(id)}  // cria nova função a cada render
```

**Impacto:** Em listas com muitos itens (Kanban, tabelas de candidatos), cada re-render recria milhares de funções.  
**Fix:** Usar useCallback ou data-attributes com handler único no pai.

---

### 4.4 MÉDIO — Fetch vs SWR

```
Raw fetch(): 1.399
useSWR:         59
```

96% das chamadas de API usam fetch raw sem cache, deduplication, ou revalidação.

**Impacto:** Requisições duplicadas; sem cache de dados; sem loading states padronizados; sem retry automático.  
**Fix:** Migrar para SWR/React Query com cache policy definida. Pelo menos as rotas mais frequentes (candidatos, vagas, configurações).

---

### 4.5 BAIXO — React.memo Subutilizado

```
Componentes exportados: 791
React.memo:              83 (10%)
```

**Fix:** Aplicar memo nos componentes de lista (KanbanCard, CandidateRow, etc.) que renderizam centenas de vezes.

---

## Parte 5: Dados Mock em Produção

### 5.1 CRÍTICO — 92 Instâncias de Mock Data

Mock data está presente em **92 locais** fora de arquivos de teste, incluindo:

- `kanban/mock/candidates.ts` — 1.559 linhas de dados fake
- Constantes mock inline em hooks e componentes
- URLs fake de avatar (randomuser.me, pravatar.cc)
- Links fake do Teams (`teams.microsoft.com/l/meetup-join/19%3ameeting_demo123`)
- WhatsApp com número fake (`5511999999999`)

**Risco:** Dados mock podem aparecer em produção quando API falha; confusão entre dados reais e fake; testes ilusórios.  
**Fix:** Mover TODOS os mocks para `__mocks__/` ou `__fixtures__/`; usar feature flags para modo demo.

---

## Parte 6: Acessibilidade e i18n

### 6.1 ALTO — 42 Imagens Sem Alt Text

Apenas 4 de 46 imagens têm `alt` definido.

**Risco:** Não-compliance com WCAG 2.1; barreiras para usuários com deficiência visual; impacto em SEO.  
**Fix:** Adicionar alt text descritivo a todas as imagens.

---

### 6.2 ALTO — 5.364 Strings Hardcoded em PT-BR

Nenhum sistema de i18n implementado. Todas as strings estão diretamente no JSX.

**Impacto:** Impossível internacionalizar; difícil manter consistência de terminologia; copy changes exigem deploy.  
**Fix:** Para escalar: implementar next-intl ou react-i18next. Mínimo: extrair strings para constantes centralizadas.

---

### 6.3 MÉDIO — Acessibilidade Parcial

```
aria-label: 495
aria-*:     974
role:       321
```

Há esforço de acessibilidade (Radix UI ajuda), mas sem auditoria sistemática.  
**Fix:** Rodar Lighthouse accessibility audit; corrigir imagens e forms sem labels.

---

## Parte 7: Testes

### 7.1 CRÍTICO — Cobertura de 2.7%

```
Arquivos de teste: 50
Arquivos de código: 1.830
Cobertura: 2.7%
```

**Impacto:** Refactoring é arriscado; regressões não são detectadas; sem confiança para deploy contínuo.  
**Fix:** Estabelecer mínimo de 30% cobertura; focar em: auth flows, CRUD de candidatos/vagas, chat LIA, Kanban transitions.

---

## Parte 8: Estrutura e Escalabilidade

### 8.1 ALTO — 124 Modais

124 arquivos de modal indicam UI excessivamente fragmentada em pop-ups. Cada modal tem seu próprio estado, loading e error handling.

**Fix:** Criar sistema de modais genérico (ModalManager) com registro centralizado; reduzir modais de confirmação para uma API imperativa (`confirm()`).

---

### 8.2 ALTO — 7 Variantes de CandidatePreview

7 arquivos relacionados a preview de candidato sugerem duplicação e inconsistência.

**Fix:** Consolidar em um único `CandidatePreview` composável com sub-componentes.

---

### 8.3 MÉDIO — 8 Error Boundaries para 791 Componentes

Apenas 8 error boundaries. Se um componente deep na árvore falha, pode derrubar seções inteiras da UI.

**Fix:** Adicionar error boundaries em cada rota (page.tsx) e em componentes de alto risco (chat, kanban, modais).

---

### 8.4 MÉDIO — Código Morto

~15+ componentes possivelmente não utilizados encontrados:
- `kpi-alert-system.tsx`
- `alert-settings-modal.tsx`
- `interactive-charts.tsx`
- `advanced-interactive-charts.tsx`
- `success-prediction.tsx`
- `recruitment-ml-engine.tsx`
- E outros

**Fix:** Verificar referências e remover dead code.

---

## Resumo de Ações Prioritárias

### P0 — Bloqueadores de Produção (fazer antes de lançar)

| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 1 | Remover credencial hardcoded (`login-page.tsx`) | 1h | Segurança |
| 2 | Migrar tokens de localStorage para httpOnly cookies | 2-3d | Segurança |
| 3 | Implementar middleware.ts de auth | 1-2d | Segurança |
| 4 | Sanitizar TODOS os dangerouslySetInnerHTML | 2h | Segurança XSS |
| 5 | Remover mock data de código de produção | 2-3d | Integridade |
| 6 | Adicionar Zod validation às 174 API routes restantes | 3-5d | Segurança |

### P1 — Alta Prioridade (sprint seguinte)

| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 7 | Mover regras de negócio (scores, preços) para backend | 2-3d | Arquitetura |
| 8 | Resolver top 50 @ts-ignore (concentrados em 5 arquivos) | 3-5d | Qualidade |
| 9 | State management global (Zustand) | 3-5d | Escalabilidade |
| 10 | Code splitting (modais, admin, features pesadas) | 2-3d | Performance |
| 11 | Migrar fetch → SWR/React Query (rotas principais) | 3-5d | Performance |
| 12 | Adicionar error boundaries por rota | 1d | Resiliência |

### P2 — Média Prioridade (próximo mês)

| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 13 | Security headers (CSP, HSTS, X-Frame) | 1d | Segurança |
| 14 | Quebrar god components (>500 linhas) | 5-7d | Manutenibilidade |
| 15 | Reduzir state explosion (56 useState → useReducer) | 3d | Performance |
| 16 | Alt text em imagens | 1d | Acessibilidade |
| 17 | Testes — atingir 30% cobertura | 10-15d | Confiabilidade |
| 18 | Remover dead code | 1-2d | Bundle size |
| 19 | Converter TODOs em Jira issues | 2d | Processo |
| 20 | Preparar i18n (extrair strings) | 5-7d | Escalabilidade |

---

## Conclusão

O frontend da Plataforma LIA tem funcionalidade rica e design system consistente (tokens, Tailwind, Radix), mas **não está pronto para produção em escala** por três razões fundamentais:

1. **Segurança comprometida** — credenciais expostas, tokens vulneráveis, sem middleware de auth, XSS parcial.
2. **Dívida técnica acumulada** — 1.029 @ts-ignore, 1.015 TODOs, god components, estado fragmentado em 4.050 useState sem gerenciamento global.
3. **Ausência de testes** — 2.7% de cobertura torna qualquer refactoring arriscado.

**Estimativa total para P0:** ~2-3 semanas de trabalho focado  
**Estimativa total para P0+P1:** ~4-6 semanas  
**Estimativa total para P0+P1+P2:** ~8-12 semanas  

O caminho recomendado é resolver os P0 (segurança) imediatamente, implementar state management e testes (P1), e depois endereçar a dívida técnica gradualmente (P2).
