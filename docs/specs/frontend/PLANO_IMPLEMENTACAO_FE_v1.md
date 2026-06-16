# Plano de Implementação Frontend — WeDOTalent LIA
> **Versão:** 1.1 | **Atualizado:** 2026-03-28 | **Base:** pós-Sprint 4.10
> **Princípio:** sempre executar com múltiplos agentes em paralelo (item 10)

---

## Estado atual (em execução)

| Dimensão | Situação |
|---|---|
| Fases 0–3 | ✅ Concluídas (limpeza, tipografia, tokenização cores, badges) |
| **Fase 1 — Setup tokens** | ✅ **CONCLUÍDA** — z-index semântico (10 tokens), dimension tokens corrigidos, 29 arquivos migrados |
| **Fase 2 — Hex residual** | ✅ **CONCLUÍDA** — 6 arquivos auditados, todos isenções legítimas (print HTML, brand SVG Google/MS) |
| Fase 3 (inline styles) | ⏳ Próxima — 216 arquivos `style={{}}` · 172 arquivos `w/h-[px]` |
| Fase 4 (split) | ⏳ 7 monolitos pendentes |
| Inline styles dinâmicos | ✅ 172 — MANTER (interpolação `${}`) |
| `login-page.tsx` (raiz) | ⚠️ **Legado identificado** — versão antiga com `onLogin` prop; `pages/login-page.tsx` é a versão ativa. Remover em Fase 3 ou 8. |
| Cobertura de testes FE | ⚠️ ~3.5% (23 arquivos / 640 units) |

---

## Pergunta: split primeiro ou por último?

**Resposta: posição 4 (conforme plano).** Não começar pelo split porque:
1. Tokenizar nos monolitos primeiro → os arquivos extraídos já nascem tokenizados
2. Fazer split antes obrigaria tokenizar ~35+ arquivos menores em vez de 7
3. Os monolitos não bloqueiam nenhum passo anterior

---

## Sequência de Execução

```
1 → Setup tokens base                     ✅ CONCLUÍDA
2 → Tokenização hex/cores residual         ✅ CONCLUÍDA (todos isentos legítimos)
3 → Residual color tokens + violações inline  ← PRÓXIMA
4 → Monolith split
6 → Bridge React→Vue
7 → Design Audit "Notion/ElevenLabs"
8 → Code Review profundo
9 → Auditoria final (/feature-audit)
```

---

## Fase 1 — Setup Tokens Base

> **O que falta:** dimension tokens existem; faltam z-index semânticos e limpeza de duplicatas.

### 1.1 Z-Index Semântico (tailwind.config.ts)

**Status:** ❌ Não existe. Valores hardcoded 0–10000 espalhados em 504 componentes.

**Adicionar em `tailwind.config.ts`:**
```typescript
zIndex: {
  'base':    '0',
  'raised':  '10',
  'dropdown':'40',
  'sticky':  '50',
  'overlay': '60',
  'toast':   '100',
  'select':  '200',
  'backdrop':'9998',
  'modal':   '9999',
  'max':     '10000',
},
```

**Substituições nos componentes:**
| Valor atual | Token novo | Ocorrências estimadas |
|---|---|---|
| `z-[60]` | `z-overlay` | modais secundários |
| `z-[100]` | `z-toast` | toasts, alertas |
| `z-[200]` | `z-select` | SelectContent em modais |
| `z-[9998]` | `z-backdrop` | Dialog overlay |
| `z-[9999]` | `z-modal` | Dialog content |
| `z-[10000]` | `z-max` | Variable selector |

### 1.2 Dimension Tokens — Corrigir duplicatas (tailwind.config.ts) ✅ CONCLUÍDO

**Corrigido em Fase 1:** `height.panel-md` renomeado para `h-content-md` (300px) e `height.panel-lg` para `h-content-lg` (400px) — eliminada ambiguidade com `w-panel-md` (350px) e `w-panel-lg` (400px). `maxHeight.panel-lg` renomeado para `maxHeight.content-lg`.

```typescript
// Atual (ambíguo):
width:  { 'panel-md': '350px', 'panel-lg': '400px' }
height: { 'panel-md': '300px', 'panel-lg': '400px' }  // ← valores diferentes!

// Corrigir para naming explícito:
width: {
  'panel-sm': '300px',
  'panel-md': '350px',
  'panel-lg': '400px',
  'panel-xl': '500px',
  'sidebar-content': '200px',
}
height: {
  'chart-sm': '200px',
  'content-md': '300px',   // renomear: era panel-md (ambíguo)
  'content-lg': '400px',   // renomear: era panel-lg (ambíguo)
  'card-lg': '180px',
}
```

### 1.3 Limpar referência `theme-colors.ts` no inventário

**Status:** ✅ CONCLUÍDO — referências removidas das seções 25.2 e 28.6 do inventário.
Remover entradas e anotar como "removido em Fase 2".

**Agentes:** 1 agente (simples, ~30min)

---

## Fase 2 — Tokenização Hex/Cores Residual

> **O que falta:** 6 arquivos com hex hardcoded ainda violam o DS. Fases 2A-2F já concluídas.

### Arquivos a corrigir (6)

| Arquivo | Ação |
|---|---|
| `modals/job-insights-modal.tsx` | substituir hex → tokens `wedo-*` / `status-*` / `gray-*` |
| `pages/login-page.tsx` | substituir hex → tokens |
| `dashboard/strategic-dashboard.tsx` | substituir hex → tokens |
| `triagem-details-modal.tsx` | substituir hex → tokens |
| `login-page.tsx` (raiz) | verificar se é duplicata de `pages/login-page.tsx` — se sim, deletar |
| `clouds-background.tsx` | avaliar: se SVG puro → isentar; se CSS → substituir |

### Isentos confirmados (não tocar)
- `email-templates/email-templates-manager.tsx` — HTML inline de email
- `email-templates/report-email-templates.tsx` — HTML inline de email

**Agentes:** 1 agente, 1 dia | **Risco:** Baixo

---

## Fase 3 — Residual Color Tokens + Violações Inline

> **O que falta:** 1.889 inline styles estáticos + 172 arquivos com px arbitrários.

### 3A — Inline Styles Estáticos com `var(--)`  (957 ocorrências)

**Problema:** componentes usando `style={{ color: 'var(--eleven-text-secondary)' }}` em vez de classes Tailwind.

**Causa raiz:** sistema `--eleven-*` do command-palette não tem equivalente no tailwind.config.

**Solução em 2 passos:**
1. Mapear todas as variáveis `--eleven-*` usadas inline → criar aliases no tailwind.config ou substituir por tokens `wedo-*` equivalentes
2. Converter: `style={{ color: 'var(--eleven-text-tertiary)' }}` → `className="text-gray-400"`

**Arquivos de maior concentração:**
- `ui/command-palette.tsx` — maior usuário de `--eleven-*`
- `pages/` (41 arquivos)
- `ui-actions/` (12 arquivos)

### 3B — Inline Styles Outros Estáticos (932 ocorrências)

Converter valores estáticos para Tailwind:
- `style={{ padding: '12px' }}` → `className="p-3"`
- `style={{ marginTop: '8px' }}` → `className="mt-2"`
- `style={{ borderRadius: '8px' }}` → `className="rounded-md"`

**Exceção:** inline styles com lógica condicional (`style={{ opacity: isActive ? 1 : 0.5 }}`) → manter ou converter para `cn()`.

### 3C — Valores Arbitrários px (172 arquivos)

Usar tokens criados na Fase 1 + substituir equivalentes exatos do Tailwind:

| De | Para |
|---|---|
| `w-[80px]` | `w-20` |
| `h-[56px]` | `h-14` |
| `h-[80px]` | `h-20` |
| `w-[300px]` | `w-panel-sm` |
| `w-[350px]` | `w-panel-md` |
| `w-[400px]` | `w-panel-lg` |
| `h-[200px]` | `h-chart-sm` |
| `h-[300px]` | `h-content-md` |
| `h-[400px]` | `h-content-lg` |

**Estratégia multi-agente:** dividir por diretório — 3 agentes em paralelo:
- Agente A: `pages/`, `modals/`
- Agente B: `ui/`, `ui-actions/`, `settings/`
- Agente C: `admin/`, `search/`, restantes

**Esforço total Fase 3:** 3–4 dias | **Risco:** Médio-baixo

---

## Fase 4 — Monolith Split

> **7 arquivos pendentes.** Executar após Fases 1–3 (código já tokenizado).

### Prioridade e Sprint

| # | Arquivo | Linhas | Sprint | Agentes |
|---|---|---|---|---|
| 1 | `pages/chat-page.tsx` | 5.583 | **4.11** | 2 em paralelo |
| 2 | `pages/candidates-page.tsx` | 5.260 | **4.11** | 2 em paralelo |
| 3 | `settings/CompanyTeamHub.tsx` | 5.235 | **4.12** | 1 |
| 4 | `pages/job-kanban-page.tsx` | 4.990 | **4.12** | 1 |
| 5 | `pages/jobs-page.tsx` | 4.735 | **4.12** | 1 |
| 6 | `pages/settings-page.tsx` | 4.449 | **4.12** | 1 |
| 7 | `expandable-ai-prompt.tsx` | 4.306 | **4.12** | 1 |

### Estratégia de split (3 camadas sequenciais)

**Camada 1 — Hooks** (extrair primeiro, menor risco):
- Agrupar `useState` relacionados em hooks `use-[domínio].ts`
- Mover `useEffect`, `useCallback`, `useMemo` para o hook correspondente
- Meta: monolito perde 30–40% do volume

**Camada 2 — Componentes estáticos** (sem estado próprio):
- Extrair renders de seções autocontidas para componentes filhos
- Props tipadas explicitamente
- Meta: monolito perde mais 20–30%

**Camada 3 — Componentes com estado** (usando hooks da Camada 1):
- Extrair blocos que consomem estado via props do hook
- Meta: arquivo principal < 1.500L como orquestrador

### Sprint 4.11 — chat-page + candidates-page (detalhamento)

**`chat-page.tsx` (5.583L) — blocos identificáveis:**
- Hook `useChatPageState` — estado de mensagens, input, streaming
- Hook `useChatPageLayout` — sidebar, painel expandido, modo
- `ChatMessageList` — lista de mensagens renderizadas
- `ChatInputArea` — barra de input + upload + voz
- `ChatSidebarPanel` — painel lateral de contexto
- **Alvo:** `chat-page.tsx` < 800L como orquestrador

**`candidates-page.tsx` (5.260L) — blocos identificáveis:**
- Já extraídos em Sprint 4.9: `CandidateSearchResultsView`, `LIASearchSidebar`, `CandidateTableCellRenderer`
- Restam: hooks de paginação, estado de filtros avançados, bulk actions residuais
- **Alvo:** `candidates-page.tsx` < 600L como orquestrador

---

## Fase 6 — Bridge React→Vue

> **Auditoria de portabilidade.** Não reescreve — prepara o código para ser convertível.

### Checklist por dimensão

**Props e tipagem:**
- [ ] Todo componente tem `interface Props {}` explícito
- [ ] Nenhum `type Props = {...}` inline no componente
- [ ] Nenhum `any` em props (typescript strict)
- [ ] Callbacks nomeados `on*` (→ `@event` em Vue)

**Hooks de estado:**
- [ ] Padrão `{ state, actions }` em todos os hooks de store
- [ ] Nenhum `useContext` dentro de hook de estado (→ não traduz para Pinia)
- [ ] Nenhum `cloneElement`, `Children.map`, HOC (→ não existem em Vue)
- [ ] Nenhum `forwardRef` desnecessário

**Composição via slots:**
- [ ] `children`, `header`, `footer` como props explícitas (→ `<slot>` em Vue)
- [ ] Nenhuma renderização condicional via `React.cloneElement`

**Sidebar e layout:**
- [ ] Sidebar usa tokens `sidebar-*` do tailwind.config
- [ ] Nenhum valor hardcoded de largura de sidebar

**Ferramenta:** skill `/vue-migration-prep` em cada componente auditado.

**Agentes:** 2 em paralelo — Agente A: `components/ui/` + `components/chat/` | Agente B: `components/pages/` + `components/settings/`

---

## Fase 7 — Design Audit "Notion/ElevenLabs"

> **Validar que o DS v4.2.1 está aplicado uniformemente.**

### 7.1 Espaçamento

- [ ] Nenhum `p-[Xpx]`, `m-[Xpx]` — usar escala Tailwind (p-1=4px, p-2=8px, p-3=12px...)
- [ ] Cards usam `p-4` (16px) como padrão interno
- [ ] Gaps de grid: `gap-4` ou `gap-6` — sem valores arbitrários

### 7.2 Tipografia

- [ ] `text-xs` (11px) para labels e metadados
- [ ] `text-sm` (14px) para corpo de texto
- [ ] `text-base` (16px) para títulos de seção
- [ ] Nenhum `text-[Xpx]` — Fase 1 deve ter eliminado todos
- [ ] Pesos: `font-medium` (default), `font-semibold` (ênfase), `font-bold` (heading)

### 7.3 Hierarquia Visual

- [ ] 90% monocromático (grays) — verificar se cyan aparece fora de contexto LIA/IA
- [ ] Botões primários: `bg-gray-900 text-white` — nenhum botão azul ou colorido
- [ ] Sem `box-shadow` — bordas substituem sombras (exceto `lia-shadow-*` para LIA)
- [ ] `rounded-md` (8px) universal — sem `rounded-full` em botões

### 7.4 Dark Mode

- [ ] Todos os novos componentes têm classes `dark:` explícitas
- [ ] Nenhum componente usa `var(--eleven-*)` sem fallback dark
- [ ] Cobertura: verificar os 11 tokens `--eleven-*` usados inline

### 7.5 ElevenLabs vs LIA — Resolver Duplicação CSS

**Problema:** dois sistemas paralelos no CSS:
- `--lia-text-primary: #111827` (design-tokens.css)
- `--eleven-text-primary: #2D2D2D` (globals.css)

**Ação:** mapear todos os `--eleven-*` usados em componentes → substituir pelo equivalente `--lia-*` ou `wedo-*`. Remover `--eleven-*` de globals.css progressivamente.

**Ferramenta:** skill `/design-standardize` nos componentes afetados.

**Agentes:** 2 em paralelo — Agente A: tipografia + espaçamento | Agente B: dark mode + ElevenLabs cleanup

---

## Fase 8 — Code Review Profundo

### 8.1 Duplicações

**Candidatas identificadas:**
- `login-page.tsx` (raiz) vs `pages/login-page.tsx` — verificar se são o mesmo arquivo
- `useCompanyBenefits` + `use-company-benefits` — dois hooks com mesmo propósito
- `useTableFeatures` + `use-table-features` — dois hooks de tabela
- `dashboard-app.tsx` aparece em `components/` e em `pages/` — verificar

### 8.2 Dead Code

- `jobs2-page.tsx` (569L) — verificar se tem rotas ativas; candidato a remoção
- `mockup-shadcn-vue-page.tsx` (599L) — nome sugere arquivo de teste; verificar
- `tasks-page-mvp.tsx` (890L) — se `tasks-page.tsx` é o atual, candidato a remoção
- `settings-page-enhanced.tsx` (623L) — verificar se substituiu `settings-page.tsx`

### 8.3 Performance

- [ ] Componentes pesados sem `React.memo` (CandidateCard, KanbanColumn, ChatMessageItem)
- [ ] Listas longas sem virtualização (candidatos, vagas, kanban colunas)
- [ ] Hooks com `useEffect` sem dependências corretas (stale closures)
- [ ] Import dinâmico (`next/dynamic`) nos 5 maiores componentes

### 8.4 Type Safety

- [ ] Eliminar `any` explícito em props e retornos de hooks
- [ ] `interface` em vez de `type` para props de componentes (padrão Vue-ready)
- [ ] Remover `@ts-ignore` / `@ts-expect-error` sem justificativa documentada
- [ ] Verificar hooks sem tipo de retorno explícito

**Agentes:** 3 em paralelo — Agente A: duplicações + dead code | Agente B: performance | Agente C: type safety

---

## Fase 9 — Auditoria Final

**Ferramenta:** skill `/feature-audit` (14 dimensões).

### Dimensões auditadas

| # | Dimensão | Foco no contexto deste plano |
|---|---|---|
| D1 | Funcionalidade | Nenhuma regressão nos splits |
| D2 | Portabilidade Vue | Resultado da Fase 6 |
| D3 | Design System | Resultado da Fase 7 |
| D4 | Dark mode | 100% cobertura após Fase 7 |
| D5 | Acessibilidade | aria-label, roles, keyboard nav |
| D6 | Performance | Após Fase 8 |
| D7 | Type safety | Após Fase 8 |
| D8 | Testes | Cobertura mínima nos componentes splitados |
| D9 | LGPD / Compliance | Sem regressão |
| D10 | Internacionalização | Strings hardcoded em PT-BR |
| D11 | Responsividade | sm/md/lg breakpoints verificados |
| D12 | Segurança FE | XSS, dangerouslySetInnerHTML |
| D13 | Documentação | JSDoc nos hooks críticos |
| D14 | Integração API | Proxy routes funcionando após splits |

---

## Regras de Execução Multi-Agente (Item 10)

### Quando paralelizar

| Situação | Estratégia |
|---|---|
| Tokenização por diretório | 3 agentes: pages+modals / ui+settings / admin+search |
| Split de monolitos independentes | 2 agentes: um por arquivo (ex: chat-page + candidates-page) |
| Auditoria Bridge Vue | 2 agentes: ui+chat / pages+settings |
| Design Audit | 2 agentes: tipografia+espaçamento / dark mode+ElevenLabs |
| Code Review | 3 agentes: duplicações / performance / type safety |

### Quando NÃO paralelizar

| Situação | Motivo |
|---|---|
| Fase 1 (setup tokens) antes das demais | Dependência: fases 2–5 dependem dos tokens |
| Split de um mesmo arquivo | Um agente por arquivo — conflito de contexto |
| Fase 9 (auditoria final) | Deve ser o último passo, após todas as fases |

### Regra de isolamento

Cada agente trabalha em arquivos diferentes. Nunca dois agentes no mesmo arquivo ao mesmo tempo.

---

## Cronograma Estimado

| Sprint | Fases | Esforço | Multi-agente |
|---|---|---|---|
| **4.11** | Fase 1 + 2 + 3 (parcial) | 3–4 dias | 3 agentes na Fase 3 |
| **4.12** | Fase 3 (conclusão) + Fase 4 | 5–7 dias | 2 agentes no split |
| **4.13** | Fase 6 + 7 | 3–4 dias | 2 agentes em paralelo |
| **4.14** | Fase 8 + 9 | 2–3 dias | 3 agentes no review |
| **Total** | | **~13–18 dias úteis** | |

---

## Critérios de Conclusão por Fase

| Fase | Critério de Done |
|---|---|
| 1 | z-index tokens no tailwind.config; dimension tokens sem duplicatas; inventário atualizado |
| 2 | `grep -r "#[0-9a-fA-F]\{6\}" src/components --include="*.tsx"` retorna apenas isentos |
| 3 | Inline styles estáticos < 200 (apenas dinâmicos `${}` restam); 0 arquivos com `w/h-[px]` convertíveis |
| 4 | Nenhum componente > 2.000L; cada monolito tem hook layer + componentes filhos |
| 6 | `/vue-migration-prep` passa em 100% dos componentes auditados |
| 7 | `/design-standardize` sem violações; 0 uso de `--eleven-*` em componentes |
| 8 | 0 `any` explícito em props; dead code confirmado e removido |
| 9 | `/feature-audit` 14/14 dimensões sem críticos |
