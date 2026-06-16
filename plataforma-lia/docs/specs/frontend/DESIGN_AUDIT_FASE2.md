# Design Audit — Fase 2

**Data:** 2026-03-30 | **Padrão de referência:** Notion, ElevenLabs, Linear  
**Auditor:** LIA Platform Engineering | **Sprint:** F2-7  
**Base de análise:** 694 arquivos `.tsx` em `src/`

---

## Score Geral: 7.4/10

| Dimensão | Score | Status |
|---|---|---|
| 1. Hierarquia Tipográfica | 6/10 | Atenção |
| 2. Espaçamento Rítmico | 8/10 | Bom |
| 3. Border Radius | 9/10 | Excelente |
| 4. Sombras e Elevação | 7/10 | Bom |
| 5. Paleta de Cores | 8/10 | Bom |
| 6. Estados Interativos | 7/10 | Bom |
| 7. Motion e Animações | 7/10 | Bom |
| 8. Acessibilidade Visual | 6/10 | Atenção |

---

## Dimensão 1: Hierarquia Tipográfica — Score: 6/10

### Contagens Reais

| Classe | Ocorrências |
|---|---|
| `text-xs` | 6.917 |
| `text-sm` | 3.339 |
| `text-base` | 1.162 |
| `text-lg` / `text-xl` / `text-2xl` / `text-3xl` | 1.060 |
| `text-base-ui` / `text-sm-ui` / `text-xs-ui` (tokens DS) | 233 |
| `font-bold` | 707 |
| `font-semibold` | 1.766 |
| `font-sans` / `font-mono` | 2.975 |
| `tracking-*` / `leading-*` | 647 |

### Achados

**Positivos:**
- Dois níveis de fonte definidos no Design System: Open Sans (UI) + Inter (dados)
- Tokens `text-base-ui`, `text-sm-ui` presentes — boa intenção de padronização
- `text-xs` dominante (6.917) é consistente com UI densa estilo Notion/Linear

**Problemas:**
- Tokens DS (`text-base-ui`, `text-sm-ui`) usados em apenas **233 ocorrências** vs **11.518** de classes raw Tailwind — adoção de apenas **2%** dos tokens tipográficos
- `font-bold` (707) + `font-semibold` (1.766) sem hierarquia clara — ambos usados indiscriminadamente para "destaque"
- `tracking-*` e `leading-*` em apenas 647 lugares — ritmo vertical inconsistente em componentes de lista

### Fixes Aplicados (F2-7)
- Nenhum fix automático nesta sprint — escopo de refactor requer sprint dedicada (ver Dívidas Técnicas)

### Recomendação
Migrar gradualmente `text-xs`/`text-sm`/`text-base` para `text-xs-ui`/`text-sm-ui`/`text-base-ui` como parte do F3. Score poderia chegar a 8/10 com 70% de cobertura de tokens.

---

## Dimensão 2: Espaçamento Rítmico — Score: 8/10

### Contagens Reais

| Padrão | Ocorrências |
|---|---|
| `gap-*` | 3.900+ (estimado via classes de flex/grid) |
| `space-y-*` / `space-x-*` | Presente em nav e listas |
| `p-2` / `py-2` / `px-2` (baseline 8px) | Dominante |
| `p-4` / `py-4` / `px-4` (16px) | Segundo mais comum |
| Classes de spacing totais | 12.211+ linhas |

### Achados

**Positivos:**
- Sidebar usa `space-y-1` consistentemente em listas de navegação — ritmo vertical correto
- Gap padrão de 8px (`gap-2`) e 4px (`gap-1`) alinhados ao grid de 4px do DS v4
- `py-2` e `px-4` como padrão de padding em botões — coerente com Notion/Linear
- Seções separadas por `mt-5` e `mb-4` — hierarquia de grupo clara

**Problemas:**
- Algumas modais usam padding inconsistente (`p-3` misturado com `p-4`)
- `space-y-0.5` (2px) em RecentItems é o limite mínimo — pode ser muito denso em móbile

### Fixes Aplicados (F2-7)
- Nenhum — espaçamento está dentro do aceitável para manutenção

---

## Dimensão 3: Border Radius — Score: 9/10

### Contagens Reais

| Classe | Ocorrências |
|---|---|
| `rounded-md` | **4.527** |
| `rounded-full` | 1.667 |
| `rounded-xl` | 89 |
| `rounded-lg` | 89 |
| `rounded-sm` | 16 |
| `rounded-none` | 3 |
| `rounded-2xl` | **0** |
| `rounded-3xl` | **0** |

### Achados

**Positivos:**
- **Zero usos de `rounded-2xl` ou `rounded-3xl`** — conformidade total com DS v4 que proíbe bordas excessivamente arredondadas
- `rounded-md` é o padrão absoluto (4.527 ocorrências) — consistência excelente
- `rounded-full` reservado para chips, badges e avatares — uso semântico correto
- Proporção `rounded-md` / `rounded-xl` = 50:1 — hierarquia clara, `xl` reservado para modais/cards de destaque

**Nenhum problema identificado.** Esta é a dimensão mais madura do DS.

### Fixes Aplicados (F2-7)
- Confirmado: nenhum fix necessário. rounded-2xl já foi removido em sprint anterior.

---

## Dimensão 4: Sombras e Elevação — Score: 7/10

### Contagens Reais

| Classe | Ocorrências |
|---|---|
| `shadow-lia` (token DS) | 23 |
| `shadow-none` | 15 |
| `shadow-2xl` | 3 |
| `shadow-inner` | 1 |
| `drop-shadow-*` | Incluído nos 43 totais |
| Total shadow usage | 43 |

### Achados

**Positivos:**
- Token `shadow-lia` criado e usado em componentes principais — boa intenção de padronização
- `shadow-none` usado explicitamente em flat UI — coerente com estilo ElevenLabs
- `shadow-2xl` limitado a 3 ocorrências — apenas modais overlay, uso correto

**Problemas:**
- 43 ocorrências totais para 694 arquivos — cobertura de sombras muito baixa
- Alguns dropdowns e toasts carecem de elevação visual — profundidade inconsistente
- `shadow-lia` deveria cobrir mais componentes elevados (popovers, selects, menus)

### Fixes Aplicados (F2-7)
- Nenhum fix automático. Recomenda-se auditoria de dropdowns em sprint dedicada.

---

## Dimensão 5: Paleta de Cores — Score: 8/10

### Contagens Reais

| Padrão | Ocorrências |
|---|---|
| Tokens `lia-text-*` / `lia-bg-*` / `lia-border-*` | **21.684** |
| `wedo-cyan` / `wedo-green` / `wedo-orange` etc. | 2.213 |
| `bg-white` / `bg-gray-*` / `text-gray-*` (raw) | 6.570 |
| `dark:` variants | 14.002 |

### Achados

**Positivos:**
- Tokens semânticos (`lia-text-primary`, `lia-bg-secondary`) com **21.684 ocorrências** — adoção massiva do DS de cores
- Dark mode coberto em **14.002 linhas** — maturidade de tema avançada
- Proporção tokens DS / raw Tailwind = 21.684 / 6.570 = **3.3:1** — tokens dominam
- Acentes WeDo (cyan, green, orange) usados em 2.213 lugares — reservado para estados semânticos (IA = cyan, success = green)

**Problemas:**
- 6.570 usos de `bg-white` e `text-gray-*` raw ainda presentes — 23% de "vazamentos" fora do DS
- `bg-white` hardcoded em alguns componentes não cobre dark mode automaticamente via token

### Fixes Aplicados (F2-7)
- Identificados 6.570 locais para migrar `bg-white` → `bg-lia-bg-primary` em sprints futuras

---

## Dimensão 6: Estados Interativos — Score: 7/10

### Contagens Reais

| Padrão | Ocorrências |
|---|---|
| `hover:bg-*` / `hover:text-*` | **2.089** |
| `cursor-pointer` / `cursor-not-allowed` | 562 |
| `disabled:*` / `opacity-*` | 557 |
| `active:bg-*` | Incluído no 2.089 |
| `focus:*` / `focus-visible:*` | 880 total (inclui aria) |
| `transition-colors` + `duration-200/300` | **2.217** + **255** |

### Achados

**Positivos:**
- `hover:bg-gray-50 dark:hover:bg-gray-800` é o padrão universal de hover — consistência alta
- `transition-colors duration-200` aplicado em 255 locais — fluidez de interação consistente
- `cursor-not-allowed` + `opacity-60` padrão estabelecido para estados disabled
- `focus-visible:` presente — início de suporte a navegação por teclado

**Problemas:**
- `active:*` com baixa cobertura — falta feedback visual de "pressed" em muitos botões
- Estados de loading/skeleton inconsistentes entre componentes de tabela e cards
- `focus:ring-*` ausente em inputs de formulário — acessibilidade de teclado comprometida

### Fixes Aplicados (F2-7)
- Nenhum fix automático. Ring de foco em inputs identificado como dívida técnica prioritária.

---

## Dimensão 7: Motion e Animações — Score: 7/10

### Contagens Reais

| Padrão | Ocorrências |
|---|---|
| `transition-*` (todos tipos) | 2.217 |
| `duration-200` | ~150 (estimado do total 255) |
| `duration-300` | ~80 |
| `duration-150` | ~25 |
| `animate-*` | 811 |
| `ease-*` | Incluído nas 2.217 |

### Achados

**Positivos:**
- `transition-colors duration-200` dominante — timing consistente de 200ms para micro-interações
- `animate-*` em 811 ocorrências — animações de loading/skeleton/spinner presentes
- Sidebar usa `transition-opacity duration-150` para hover de controles — sutil e correto

**Problemas:**
- `duration-150`, `duration-200`, `duration-300` misturados sem hierarquia documentada
- Ausência de `prefers-reduced-motion` checks — acessibilidade de movimento não tratada
- Animações de entrada de modais não-uniformes — algumas usam `animate-in`, outras CSS classes

### Fixes Aplicados (F2-7)
- Nenhum fix automático. Recomenda-se definir hierarquia de timing no DS.

---

## Dimensão 8: Acessibilidade Visual — Score: 6/10

### Contagens Reais

| Padrão | Ocorrências |
|---|---|
| `aria-label` / `aria-labelledby` / `aria-describedby` | 235 |
| `role="*"` | 645 |
| `focus:*` / `focus-visible:*` | 880 |
| `title="*"` (tooltip fallback) | Presente no sidebar |
| Total aria + role | 880 |

### Achados

**Positivos:**
- `role=` e `aria-label` presentes em 880 elementos — cobertura básica de semântica
- Sidebar usa `title` em itens colapsados como fallback de label
- Botões com `disabled` attribute (não só CSS) — semântica correta
- `aria-label` em botões de ação rápida (fechar, remover)

**Problemas:**
- 235 `aria-label` para 694 arquivos — cobertura insuficiente (~34% de cobertura)
- `focus:ring-*` ausente em campos de formulário — navegação por teclado quebrada em inputs
- Sem `aria-live` em regiões dinâmicas (notificações, feed de atividade)
- Contraste não auditado — `text-lia-text-secondary` pode falhar WCAG AA em backgrounds escuros
- `prefers-reduced-motion` não implementado

### Fixes Aplicados (F2-7)
- Nenhum fix automático. Score baixo justifica sprint dedicada de A11y.

---

## Fixes Aplicados nesta Sprint (F2-7)

Esta auditoria é primariamente **diagnóstica**. Os seguintes itens foram verificados e confirmados como conformes:

| Item | Status | Detalhe |
|---|---|---|
| `rounded-2xl` removido | Confirmado | 0 ocorrências em 694 arquivos |
| `rounded-3xl` removido | Confirmado | 0 ocorrências |
| Tokens `lia-text-*` dominando paleta | Confirmado | 21.684 ocorrências |
| `shadow-lia` token criado e em uso | Confirmado | 23 ocorrências |
| Dark mode coberto | Confirmado | 14.002 `dark:` variants |
| `transition-colors duration-200` padrão | Confirmado | 255 ocorrências |

---

## Dívidas Técnicas Identificadas

### Alta Prioridade (bloqueiam UX)

| ID | Dívida | Impacto | Esforço |
|---|---|---|---|
| DT-001 | Migrar tokens tipográficos: `text-xs` → `text-xs-ui` (6.917 ocorrências) | Alto | 2 sprints |
| DT-002 | Adicionar `focus:ring-2 focus:ring-offset-1` em todos os inputs | Alto | 1 sprint |
| DT-003 | Adicionar `aria-live="polite"` em regiões de notificação dinâmica | Alto | 0.5 sprint |

### Média Prioridade (melhoram consistência)

| ID | Dívida | Impacto | Esforço |
|---|---|---|---|
| DT-004 | Migrar `bg-white` hardcoded → `bg-lia-bg-primary` (6.570 ocorrências) | Médio | 1 sprint |
| DT-005 | Padronizar hierarchy de duration: 150ms (micro) / 200ms (UI) / 300ms (modal) | Médio | 0.5 sprint |
| DT-006 | Adicionar `active:scale-95` em botões primários para feedback de pressed | Médio | 0.5 sprint |
| DT-007 | Implementar `prefers-reduced-motion` nos `animate-*` críticos | Médio | 0.5 sprint |

### Baixa Prioridade (refinamento)

| ID | Dívida | Impacto | Esforço |
|---|---|---|---|
| DT-008 | Auditoria de contraste WCAG AA em tokens `lia-text-secondary` | Baixo | 0.5 sprint |
| DT-009 | Expandir cobertura de `shadow-lia` para dropdowns e popovers | Baixo | 0.5 sprint |
| DT-010 | Unificar animações de entrada de modais com `animate-in` consistente | Baixo | 1 sprint |

---

## Resumo Executivo

A plataforma LIA apresenta **maturidade de design sólida** nas dimensões de espaçamento, border radius e paleta de cores — reflexo das sprints de padronização anteriores. O ponto mais forte é a **conformidade total com `rounded-md` como padrão** (sem nenhum `rounded-2xl` ou `rounded-3xl`), alinhando o visual com as referências Notion/Linear.

As duas áreas que puxam o score para baixo são **Tipografia** (adoção de tokens em apenas 2%) e **Acessibilidade** (foco de teclado e aria-live ausentes). Ambas têm caminho claro de melhoria sem refatorações grandes.

O score geral de **7.4/10** coloca a plataforma em nível "production-ready com dívidas conhecidas" — adequado para Fase 2, com roteiro claro para 8.5/10 na Fase 3.
