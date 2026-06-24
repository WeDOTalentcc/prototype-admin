---
name: design-standardize
description: Padronização visual de componentes React+Tailwind conforme Design System LIA v4.2.1. Use ao criar telas, componentes, modais, botões ou qualquer elemento novo de UI. Começa com PASSO 0 (Intenção Estética) para novas telas, depois aplica regra 90/10, tipografia (Open Sans 85% + Inter 10% + JetBrains Mono 5%), tokens canônicos, dark mode e validação automática por grep.
---

# Design Standardize — Padronização Visual DS v4.2.1

Aplica o Design System LIA v4.2.1 em componentes React+Tailwind novos ou existentes.

> **Referência completa:** `plataforma-lia/docs/design-system/00-design-system-v4.md` (4.181 linhas)
> **Tokens TS:** `plataforma-lia/src/lib/design-tokens.ts`
> **Tokens CSS:** `plataforma-lia/src/styles/design-tokens.css`

## Quando ativar

- Quando o usuário disser "padroniza", "aplica DS", "adequa ao design system", "deixa com a cara da LIA" ou "aplica DS no botão X"
- Ao criar componente, tela, modal, drawer ou botão novo no `plataforma-lia` (React+Tailwind)
- Ao receber feedback como "não está com a cara certa", "tá feio", "fora do padrão" ou "destoa"
- Ao introduzir cor, tipografia, espaçamento ou border-radius novos em componente existente
- Como parte do fluxo de auditoria (D3 UI/DS no `feature-audit`)
- Antes de capturar screenshot para conversão Figma ou para apresentação a cliente
- Quando o usuário pedir dark mode (ou toggle dark/light) em tela existente
- Ao migrar hex literais (`#000`, `bg-blue-500`) para tokens canônicos do DS

## Quando NÃO ativar

- Componente Vue/Vuetify no `recruiter_agent_v5` -> usar `vue-vuetify-standardize`
- Decidir intenção estética de tela nova de entrada/branding -> usar `frontend-design` antes
- Escolher padrão de composição de componente (factory, render props, compound) -> usar `design-patterns`
- Mudança de copy/texto sem alteração visual


## Filosofia

> "90% monocromático, 10% acento WeDo. Botões são pretos. Cyan é da LIA."

---

## PASSO 0: Intenção Estética (obrigatório para novas telas — opcional para refatorações)

> Inspirado na análise da skill `frontend-design` (Anthropic), adaptado aos limites do DS LIA v4.2.1.
> Para **refatorações de componentes existentes**, pule direto para o PASSO 1.

Antes de qualquer código ou inventário de violações, responda às 5 perguntas abaixo. Elas evitam que a tela fique tecnicamente correta mas esteticamente vazia.

### Pergunta 1 — Problema e usuário
O que esta tela resolve? Quem a usa e com que frequência?

| Perfil | Implicação estética |
|--------|---------------------|
| Recruiter voltando todo dia | Clareza imediata, sem surpresas — previsibilidade é feature |
| Candidato em primeira visita | Primeira impressão conta — atmosfera e impacto visual permitidos |
| Admin configurando o sistema | Densidade funcional — foco em dados, não em emoção |

### Pergunta 2 — Sentimento alvo
O que o usuário deve **sentir** ao ver esta tela? Escolha um:

- `confiança` — a plataforma está no controle, dados confiáveis (ex: dashboard de candidatos)
- `boas-vindas` — acolhedor, a IA trabalha por você antes de você entrar (ex: login)
- `foco` — sem distração, clareza total para decidir (ex: modal de transição de candidato)
- `descoberta` — explorar o que a IA revelou (ex: perfil do candidato com WSI)

Para telas de branding/entrada, considerar também o **tom estético** (ver `frontend-design` para o espectro completo: refinado/luxo, editorial, orgânico, soft/pastel, industrial, brutalmente minimal).

### Pergunta 3 — Memorabilidade dentro do DS
O que torna este componente **inesquecível** dentro dos limites do DS? Responda dentro das possibilidades permitidas:

- Uma palavra em `text-wedo-cyan` no lugar certo
- Um background atmosférico (ver padrões permitidos abaixo)
- Uma tipografia de impacto (`text-5xl font-light`) na headline
- Uma composição espacial assimétrica (dois painéis, card flutuante)
- A ausência proposital de elementos — espaço negativo generoso

### Pergunta 4 — Tipo de contexto
**Escolha um** antes de decidir o nível de liberdade criativa:

```
TELA DE ENTRADA / BRANDING (login, onboarding, landing, welcome)
→ Liberdade para composição atmosférica, tipografia de impacto,
  backgrounds em camadas, glassmorphism no card principal.
→ Ainda dentro do DS — mas com os padrões atmosféricos desta seção.

INTERFACE INTERNA DA PLATAFORMA (Kanban, tabelas, modais, settings)
→ Padronização estrita. Previsibilidade é feature, não bug.
→ O usuário não deve se perguntar onde está o candidato.
→ Pule direto para o PASSO 1.
```

### Pergunta 5 — Composição espacial
Qual padrão de layout se aplica? Escolha e documente antes de codificar:

| Padrão | Exemplo | Característica |
|--------|---------|----------------|
| Card centralizado full-screen | Welcome page | CloudsBackground + card flutuante centralizado |
| Dois painéis assimétricos | Login (atual) | Branding à esquerda, ação à direita |
| Lista / tabela | Candidatos | Densidade funcional, Inter para dados |
| Sidebar + main area | Settings | Navegação lateral, conteúdo principal |
| Full-screen sem divisão | 404, Maintenance | Impacto visual único, sem estrutura de layout |

---

## Padrões Atmosféricos Válidos para Telas de Entrada LIA

> Estes padrões são **APROVADOS** apenas em telas de entrada/branding.
> São **PROIBIDOS** em interfaces internas da plataforma (Kanban, tabelas, modais).

### Background em Camadas (CloudsBackground-style)
```tsx
// Gradiente de fundo (sky azul → branco)
background: "linear-gradient(180deg, #7CBAD8 0%, #8EC5DE 20%, ... #ffffff 100%)"

// Elementos SVG animados — Framer Motion
// 3 camadas: back (opacity 0.30, blur 3px) | mid (0.60, 2px) | front (0.88, 1px)
// pointer-events-none aria-hidden="true"

// Fade suave na base
<div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white/50 to-transparent" />
```
Referência: `plataforma-lia/src/components/clouds-background.tsx`

### Glassmorphism no Card Principal
```tsx
// Permitido em telas de entrada — NUNCA em cards internos da plataforma
className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-2xl shadow-2xl"
//                     ↑ rounded-2xl aqui (telas de entrada) vs rounded-md (interface interna)
```

### Tipografia de Impacto (Headline)
```tsx
// Permitido apenas em headline principal de telas de branding
<h1 className="text-5xl text-gray-950 font-light leading-tight font-['Open_Sans',sans-serif]">
  Entre. A <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> já está
  trabalhando por você.
</h1>
```
> "LIA" em Source Serif 4 bold é **exceção de branding intencional** — não corrigir quando o validator apontar `TYPOGRAPHY_SOURCE_SERIF_WRONG_CONTEXT`.

### Acento Semântico Único
```tsx
// Uma palavra em cyan na sequência de suporte — dentro da regra 90/10
<p className="text-base text-gray-500 font-light">
  Sourcing global · Triagem inteligente · Agendamentos automáticos<br />
  Recrutamento <span className="text-wedo-cyan">simples</span>
</p>
```

### Layout Dois Painéis Assimétricos
```tsx
// Painel esquerdo: branding (hidden em mobile)
<div className="hidden lg:flex lg:w-1/2 relative flex-col z-10">
// Painel direito: ação (100% em mobile)
<div className="w-full lg:w-1/2 flex flex-col relative z-10">
```

### Regra de Ouro — Interface Interna vs Tela de Entrada

| Atributo | Interface interna | Tela de entrada |
|----------|-------------------|-----------------|
| Border radius card | `rounded-xl` | `rounded-2xl` |
| Sombra | `shadow-sm` | `shadow-2xl` |
| Gradientes em card | **PROIBIDO** | Permitido no background |
| Glassmorphism | **PROIBIDO** | `bg-white/90 backdrop-blur-md` |
| Headline tipografia | `text-sm` / `text-base` | `text-5xl font-light` |
| Background animado | **PROIBIDO** | CloudsBackground permitido |

> Qualquer técnica desta seção de Padrões Atmosféricos aplicada em interface interna é uma **violação grave do DS v4.2.1**.

---

## PASSO 1: Inventário Rápido

```bash
ls -la plataforma-lia/src/components/[pasta-do-feature]/
grep -rn "bg-blue-\|bg-cyan-\|bg-green-5\|bg-purple-\|font-serif" [ARQUIVOS] --include="*.tsx"
```

Registrar: arquivos tocados, quantidade de botões/inputs/cards/badges, violações encontradas.

---

## PASSO 2: Aplicar por Tipo de Componente

### 2.1 BOTÕES

| Variante | Classes Tailwind (com dark mode) |
|----------|----------------------------------|
| **Primary** | `bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200` |
| **Secondary** | `bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-700` |
| **Ghost** | `bg-transparent text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800` |
| **Destructive** | `bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus:ring-red-600/20` |
| **Disabled** | `bg-gray-300 text-gray-500 cursor-not-allowed` |

**Tamanhos:** Small `px-3 py-1.5 text-xs` (32px) | Default `px-4 py-2 text-sm` (40px) | Large `px-5 py-2.5 text-sm` (48px)

**Base:** `font-medium rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-gray-900/20 font-['Open_Sans']`

**Regras:** Primary PRETO (`bg-gray-900`). Cyan NUNCA em botões. Focus ring grayscale.

**Helper:** `getButtonClasses('primary', 'default')`

---

### 2.2 INPUTS & FORMS

**Input:** `w-full px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 bg-white border border-gray-300 rounded transition-all duration-150 hover:border-gray-400 focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 focus:outline-none disabled:bg-gray-50 disabled:text-gray-500 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600`

**Erro:** `border-red-500 focus:ring-red-500/20 bg-red-50 dark:bg-red-900/10`

**Labels:** `text-[11px] font-semibold text-gray-800 dark:text-gray-200 font-['Open_Sans']`

**Hint:** `text-xs text-gray-600 dark:text-gray-400` | **Erro msg:** `text-xs text-red-600 dark:text-red-400`

**Regras:** Todo input com `<label htmlFor>` + `id`. Spacing `space-y-1.5`. Checkbox/Radio `accent-gray-900`.

**Select:** `cursor-pointer` | **Textarea:** `resize-none`

**Helper:** `getInputClasses(hasError)`

---

### 2.3 CARDS & CONTAINERS

**Card:** `bg-white border border-gray-200 rounded-xl shadow-sm dark:bg-gray-800 dark:border-gray-700`

**Card interativo:** + `transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer`

**Card glassmorphism:** `bg-white/70 backdrop-blur-lg border border-gray-200/50 rounded-xl shadow-sm dark:bg-gray-800/70`

**Estrutura:** Header `px-6 py-4 border-b border-gray-200` | Body `p-6` | Footer `px-6 py-4 bg-gray-50 border-t border-gray-200`

**Regras:** Cards `rounded-xl` (12px). Shadow máximo `shadow-md`. NUNCA `shadow-xl`, bordas grossas ou gradientes.

**Helper:** `getCardClasses('default')`

---

### 2.4 TABELAS

**Container:** `bg-white rounded-md border border-gray-200 overflow-hidden dark:bg-gray-800 dark:border-gray-700`

**Header:** `bg-gray-50 border-b border-gray-200 dark:bg-[#1A1D1F]`

**Header cell:** `px-6 py-3 text-left text-[11px] font-semibold text-gray-800 font-['Inter'] uppercase`

**Body cell:** `px-6 py-4 text-sm text-gray-900 dark:text-gray-100`

**Row hover:** `hover:bg-gray-50 dark:hover:bg-[#26292B]`

**Números:** `font-['Inter']` com `font-variant-numeric: tabular-nums` ou `style={{ fontFeatureSettings: "'tnum' 1" }}`

**Dividers:** `divide-y divide-gray-200 dark:divide-gray-700`

---

### 2.5 MODAIS

**Overlay:** `fixed inset-0 bg-gray-900/50 dark:bg-gray-950/70 z-50`

**Container:** `bg-white rounded-xl shadow-xl dark:bg-gray-800`

| Tamanho | Classe | Uso |
|---------|--------|-----|
| Small | `max-w-sm` | Confirmações |
| Default | `max-w-md` | Formulários simples |
| Large | `max-w-lg` | Formulários complexos |
| XLarge | `max-w-2xl` | Conteúdo extenso |
| Full | `max-w-4xl` | Tabelas, comparações |

**Header:** `px-6 py-4 border-b border-gray-200` | **Body:** `px-6 py-4` | **Footer:** `px-6 py-4 bg-gray-50 border-t flex justify-end gap-2`

**Acessibilidade:** `role="dialog" aria-modal="true" aria-labelledby="modal-title"` | Fechar: `aria-label="Fechar"`

---

### 2.6 BADGES & STATUS

| Tipo | Background | Text | Border |
|------|------------|------|--------|
| **Success** | `bg-green-50` | `text-green-700` | `border-green-200` |
| **Warning** | `bg-amber-50` | `text-amber-700` | `border-amber-200` |
| **Error** | `bg-red-50` | `text-red-700` | `border-red-200` |
| **Info** | `bg-blue-50` | `text-blue-700` | `border-blue-200` |
| **Neutral** | `bg-gray-100` | `text-gray-700` | `border-gray-200` |
| **LIA (cyan)** | `bg-[#60BED1]/10` | `text-[#60BED1]` | `border-[#60BED1]/20` |

**Dark mode:** `dark:bg-{color}-900/20 dark:text-{color}-400 dark:border-{color}-800`

**Base:** `inline-flex items-center px-2 py-1 rounded-full text-[10px] font-medium border`

**Regra:** Sempre usar ícone + cor + texto (acessibilidade para daltonismo).

**Helper:** `getBadgeClasses('success')` / `getBadgeClasses('lia')`

---

### 2.7 NAVEGAÇÃO & SIDEBAR

**Sidebar expandida:** `w-64 h-screen bg-white border-r border-gray-200 p-4 dark:bg-[#0F1113] dark:border-gray-800`

**Sidebar colapsada:** `w-16 h-screen bg-white border-r border-gray-200 p-2 dark:bg-[#0F1113] dark:border-gray-800` — apenas ícones visíveis (sem texto), tooltips no hover para cada item.

> **Regra `w-16` = 64px:** Quando a sidebar está colapsada, usa `w-16` (64px). O conteúdo principal deve usar `ml-16` (ou transição suave com `transition-all duration-300`). Nunca colapsar abaixo de 64px — ícones de 20px + padding precisam de espaço mínimo.

**Item ativo:** `flex items-center gap-3 px-3 py-2 bg-gray-100 rounded-md text-sm font-semibold text-gray-900 font-['Open_Sans'] dark:bg-gray-800 dark:text-gray-100`

**Item inativo:** `flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 rounded-md text-sm font-medium font-['Open_Sans'] dark:text-gray-400 dark:hover:bg-gray-800`

**Brain icon:** `text-[#60BED1]` (cyan permitido)

**Tabs pill:** (Open Sans) — Formato preferencial
- Ativa: `px-3 py-1.5 text-sm font-semibold text-white bg-gray-900 rounded-full dark:bg-gray-50 dark:text-gray-900`
- Inativa: `px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-full dark:text-gray-400 dark:hover:bg-gray-800`

**Tabs underline:** (Open Sans) — Alternativa para contextos horizontais
- Ativa: `text-sm font-semibold text-gray-900 border-b-2 border-gray-900 dark:text-gray-100 dark:border-gray-100`
- Inativa: `text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent dark:text-gray-400`

**Breadcrumbs:** Link `text-gray-600 hover:text-gray-900` | Atual `text-gray-900 font-semibold` | Sep `ChevronRight w-4 h-4 text-gray-400`

---

### 2.8 PROGRESS INDICATORS

**Barra:** `w-full bg-gray-200 rounded-full h-2 overflow-hidden dark:bg-gray-700`

**Fill:** `bg-gray-900 h-2 rounded-full transition-all duration-300 dark:bg-gray-100`

**Circular (spinner):** `animate-spin text-gray-900 dark:text-gray-100`

**Skeleton:** `animate-pulse bg-gray-200 rounded dark:bg-gray-700`

---

### 2.9 AVATARS

**Iniciais:** `w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-sm font-semibold dark:bg-gray-700 dark:text-gray-300`

**Imagem:** `w-10 h-10 rounded-full object-cover`

**Tamanhos:** XS `w-6 h-6` | SM `w-8 h-8` | MD `w-10 h-10` | LG `w-12 h-12` | XL `w-16 h-16`

---

### 2.10 PAGINATION

**Ativa:** `px-3 py-1 text-sm bg-gray-900 text-white rounded dark:bg-gray-100 dark:text-gray-900`

**Inativa:** `px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded dark:text-gray-300 dark:hover:bg-gray-800`

**Nav arrows:** `p-2 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50`

---

### 2.11 SWITCHES & TOGGLES

**Inativo:** `relative w-11 h-6 bg-gray-200 rounded-full transition-colors focus:ring-2 focus:ring-gray-900/20`

**Ativo:** `relative w-11 h-6 bg-gray-900 rounded-full transition-colors`

**Knob:** `absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform` | Inativo: `left-1` | Ativo: `left-6`

---

### 2.12 DROPDOWNS & MENUS

**Container:** `bg-white border border-gray-200 rounded-md shadow-lg py-1 z-50 dark:bg-gray-800 dark:border-gray-700`

**Item:** `block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700`

**Item destructive:** `text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20`

**Divider:** `border-t border-gray-200 my-1 dark:border-gray-700`

---

### 2.13 TOOLTIPS, TOASTS, ACCORDIONS

**Tooltip:** `bg-gray-900 text-white text-xs rounded px-3 py-1.5 dark:bg-gray-100 dark:text-gray-900` + `opacity-0 group-hover:opacity-100 transition-opacity duration-150`

**Toast:** `bg-white border rounded-md shadow-lg p-4 dark:bg-gray-800` + borda por tipo

**Accordion:** `border border-gray-200 rounded-md divide-y divide-gray-200 dark:border-gray-700`
- Header: `px-4 py-3 text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-50`
- Body: `px-4 py-3 text-sm text-gray-600`

---

### 2.14 CHECKBOXES & RADIOS

**Checkbox:** `accent-gray-900 w-4 h-4 rounded-sm border-gray-300 focus:ring-2 focus:ring-gray-900/20`

**Radio:** `accent-gray-900 w-4 h-4 border-gray-300 focus:ring-2 focus:ring-gray-900/20`

**Label (ao lado):** `text-sm text-gray-900 ml-2 cursor-pointer dark:text-gray-100`

**Group:** `space-y-2` | **Hint:** `text-xs text-gray-500 ml-6`

---

### 2.15 TABS

**Container pill:** `inline-flex items-center rounded-full bg-gray-100 p-1 dark:bg-gray-800`

**Ativa (pill):** `px-3 py-1.5 text-sm font-semibold rounded-full bg-white text-gray-900 shadow-sm dark:bg-gray-950 dark:text-gray-50`

**Inativa (pill):** `px-3 py-1.5 text-sm text-gray-600 rounded-full hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700`

**Container underline (alternativa):** `border-b border-gray-200 dark:border-gray-700`

**Ativa (underline):** `px-4 py-2 text-sm font-semibold text-gray-900 border-b-2 border-gray-900 dark:text-gray-100 dark:border-gray-100`

**Inativa (underline):** `px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border-b-2 border-transparent dark:text-gray-400`

---

### 2.16 SKELETON LOADERS

**Base:** `animate-pulse bg-gray-200 rounded dark:bg-gray-700`

**Linha texto:** `h-4 bg-gray-200 rounded w-full`

**Título:** `h-6 bg-gray-200 rounded w-1/3`

**Círculo (avatar):** `w-10 h-10 bg-gray-200 rounded-full`

**Card skeleton:** `bg-white rounded-md border border-gray-200 p-6 space-y-4`

---

### 2.17 DIVIDERS

**Horizontal:** `border-t border-gray-200 dark:border-gray-700`

**Com texto:** `flex items-center gap-4` + `<span className="text-xs text-gray-500">OU</span>` + bordas flex-1

---

### 2.18 FILE UPLOAD

**Dropzone:** `border-2 border-dashed border-gray-300 rounded-md p-8 text-center hover:border-gray-400 transition-colors dark:border-gray-600`

**Ícone:** `w-12 h-12 text-gray-400 mx-auto mb-3`

**Texto:** `text-sm text-gray-600` | **Link:** `text-sm font-semibold text-gray-900 hover:text-gray-700`

---

### 2.19 SLIDERS

**Track:** `w-full h-2 bg-gray-200 rounded-full dark:bg-gray-700`

**Fill:** `h-2 bg-gray-900 rounded-full dark:bg-gray-100`

**Thumb:** `w-4 h-4 bg-white border-2 border-gray-900 rounded-full shadow-sm cursor-pointer`

---

### 2.20 COMPONENTES NÃO DETALHADOS

Os seguintes componentes existem no DS v4.2.1 mas são usados com menor frequência. Consulte a referência completa (`00-design-system-v4.md`) para especificações:

- **Date Pickers:** Seção 2.20
- **Sort Dropdown:** Seção 2.27
- **Load More Button:** Seção 2.28
- **Qualification Badge:** Seção 2.29
- **Feedback Buttons:** Seção 2.26

---

### 2.21 EMPTY STATES & ERROR PAGES

**Empty state:** `py-16 text-center`
- Ícone: `w-16 h-16 text-gray-400 mx-auto mb-4`
- Título: `text-base font-semibold text-gray-900 mb-1`
- Descrição: `text-sm text-gray-600 mb-4`
- CTA: Botão primary padrão

**404:** `min-h-screen flex items-center justify-center`
- Número: `text-6xl font-bold text-gray-900`
- Subtítulo: `text-2xl font-semibold text-gray-900`

---

## REFERÊNCIA RÁPIDA: Tokens

### Tipografia (3 Fontes — DS v4.2.1 Oficial)

| Fonte | Proporção | Uso | Classe |
|-------|-----------|-----|--------|
| **Open Sans** | 85% | UI geral: headers, labels, botões, body, cards, sidebar, navigation, chat | `font-['Open_Sans']` ou `font-brand` |
| **Inter** | 10% | Dados numéricos: métricas, KPIs, números em tabelas, dashboards | `font-['Inter']` ou `font-data` |
| **JetBrains Mono** | 5% | Código, queries booleanas, dados técnicos, IDs | `font-mono` |

> **NOTA v4.2.1:** Sistema expandido de 2 para 3 fontes. Source Serif 4 removido na v4.2.1. JetBrains Mono adicionado na v4.2.1 para código e queries técnicas.

**Hierarquia Open Sans:**

| Elemento | Tamanho | Peso | Cor |
|----------|---------|------|-----|
| H1 | 24px | 600 | gray-900 |
| H2 | 18px | 600 | gray-900 |
| H3 (card title) | 14px | 600 | gray-900 |
| Body | 13px | 400 | gray-800 |
| Body SM | 12px | 400 | gray-700 |
| Label | 11px | 500 | gray-800 |
| Caption | 10px | 400 | gray-600 |
| Button | 11px | 500 | — |

> **⚠️ font-weight v4.2.1:** `font-medium` (500) é dominante — botões, labels, sidebar items, texto interativo. `font-semibold` (600) apenas para títulos e cabeçalhos.

> **`text-xs` = 11px (não 12px):** A classe `text-xs` está sobrescrita em `plataforma-lia/tailwind.config.ts` para `0.6875rem` (11px, lineHeight 1.4) em vez do padrão Tailwind de 12px. Use `text-xs` para labels de nav, badges e captions. Se precisar de 12px exato, use `text-[12px]`. Nunca assuma que `text-xs` é 12px neste projeto.

**Hierarquia Inter:**

| Elemento | Tamanho | Peso | Uso |
|----------|---------|------|-----|
| KPI Large | 32px | 700 | Números dashboard |
| KPI Medium | 24px | 700 | Valores cards |
| KPI Small | 18px | 600 | Valores inline |
| Metric | 14px | 500 | Dados tabela |
| Metric SM | 12px | 500 | Dados secundários |

### Cores (90% Monocromático)

| Token | Hex | Tailwind | Uso |
|-------|-----|----------|-----|
| bg-primary | #FFFFFF | `bg-white` | Fundo principal |
| bg-secondary | #F9FAFB | `bg-gray-50` | Cards, sidebars |
| bg-tertiary | #F3F4F6 | `bg-gray-100` | Hover, disabled |
| text-primary | #111827 | `text-gray-900` | Títulos |
| text-body | #1F2937 | `text-gray-800` | Texto principal |
| text-secondary | #4B5563 | `text-gray-600` | Descrições |
| text-muted | #6B7280 | `text-gray-500` | Placeholders |
| text-disabled | #9CA3AF | `text-gray-400` | Desabilitado |
| border-subtle | #E5E7EB | `border-gray-200` | Bordas padrão |
| border-default | #D1D5DB | `border-gray-300` | Bordas destaque |

### Cores WeDo (10% Acento)

| Token Tailwind | Hex | Uso EXCLUSIVO |
|----------------|-----|---------------|
| `text-wedo-cyan` / `bg-wedo-cyan` | #60BED1 | Brain icon LIA, badges LIA, sparkles, acento IA |
| `text-wedo-green` / `bg-wedo-green` | #5DA47A | Candidatos aprovados, sucesso |
| `text-wedo-orange` / `bg-wedo-orange` | #D19960 | Tempo, urgência, itens sensíveis a prazo |
| `text-wedo-purple` / `bg-wedo-purple` | #9860D1 | Insights, recomendações IA |
| `text-wedo-magenta` / `bg-wedo-magenta` | #D160AB | Crítico, prioridade alta |
| `text-wedo-coral` / `bg-wedo-coral` | #E16162 | Alertas de risco, rejeição |
| `text-wedo-cyan-dark` | #4DA8BB | Hover do cyan (não usar diretamente em novo código) |
| `text-wedo-green-light` | #7BC29A | Verde claro de suporte (usar com moderação) |

> **Tokens Tailwind canônicos** (definidos em `plataforma-lia/tailwind.config.ts`): usar sempre a classe Tailwind em vez de hex literal. Ex: `text-wedo-cyan` em vez de `text-[#60BED1]`. Hex literal só é aceitável quando o token ainda não existe no config.

> **`wedo-coral` (#E16162) ≠ `wedo-orange` (#D19960):** coral é para alertas/rejeição; orange é para urgência/tempo.

### Grid System (12 colunas)

```
<div className="grid grid-cols-12 gap-6">
  <div className="col-span-12 md:col-span-6 lg:col-span-4">...</div>
</div>
```

| Contexto | Gap | Classe |
|----------|-----|--------|
| Tight | 8px | `gap-2` |
| Default | 16px | `gap-4` |
| Comfortable | 24px | `gap-6` |
| Spacious | 32px | `gap-8` |

### Breakpoints

| Nome | Min Width | Classe |
|------|-----------|--------|
| xs | < 640px | (default) |
| sm | 640px | `sm:` |
| md | 768px | `md:` |
| lg | 1024px | `lg:` |
| xl | 1280px | `xl:` |
| 2xl | 1536px | `2xl:` |

### Border Radius (Fundação DS — fonte-da-verdade = código)

| Classe | Uso |
|--------|-----|
| `rounded-sm` | Elementos inline: `<code>`, `<kbd>`, skeletons |
| `rounded-md` | **Ação/controle:** botões, inputs, selects, textareas, dropdowns, callouts |
| `rounded-xl` (12px) | **Containers:** cards, modais, dialogs |
| `rounded-2xl` | Interfaces imersivas: chat expandido, login |
| `rounded-full` | Chips, badges, pills, avatars, skills |

> **REGRA (Fundação DS):** cards/modais = `rounded-xl`; botões/inputs/selects = `rounded-md`; chips/badges/pílulas = `rounded-full`. **NUNCA** sobrescrever o raio em `<Button>` (as variantes `sm`/`lg` já resolvem `rounded-md`). `rounded-sm`/`rounded-lg` em botões/inputs são PROIBIDOS. Espelha `tailwind.config.ts` (borderRadius) e a seção *Design System — Fundação* do `replit.md`.

### Componentes Canônicos (Fundação DS)

Antes de montar UI à mão (com cores cruas e raios ad-hoc), use o componente canônico em `plataforma-lia/src/components/ui/`. Eles já carregam raio, tokens e acessibilidade corretos:

| Necessidade | Componente | Notas |
|---|---|---|
| Campo de formulário (label + controle + hint + erro) | `FormField` (`ui/form-field.tsx`) | Envolve `Input`/`Textarea`/`Select`; injeta `htmlFor`/`id`/`aria-invalid`/`aria-describedby`. Controle já é `rounded-md`. |
| Pílula de status | `StatusPill` (`ui/status-pill.tsx`) | `rounded-full` + tokens `status-*` (`success`/`error`/`warning`/`info`/`neutral`). Use `withDot` ou `icon` (daltonismo: ícone+cor+texto). |
| Bloco de alerta/aviso | `Callout` (`ui/callout.tsx`) | `rounded-md` + tokens `status-*`/`wedo-cyan` com ícone semântico. Substitui blocos `bg-amber-50`/`bg-blue-50`/`bg-red-50`. |
| KPI/número | `Metric` (`ui/metric.tsx`) ou `textStyles.kpi*`/`textStyles.metric*` | Fonte de dados **Inter** (`font-data`) + `tabular-nums`. NUNCA `font-sans` em números. |

> **Anti-padrão a corrigir:** chips/callouts/badges com cores cruas do Tailwind (`bg-emerald-50 text-emerald-700`, `bg-amber-100`, `bg-blue-50`, `bg-red-200`…) → trocar por `StatusPill`/`Callout` (tokens `status-*`). KPIs em `font-sans` → trocar por `<Metric />`/`textStyles.metric*`.

### Sombras

| Classe | Interface interna | Tela de entrada | Uso |
|--------|:-----------------:|:---------------:|-----|
| `shadow-sm` | ✅ Padrão obrigatório | ✅ Permitido | Cards de interface interna (Kanban, tabelas, settings) |
| `shadow-md` | ⚠️ Somente dropdowns | ✅ Permitido | Dropdown menus, popovers, elementos flutuantes |
| `shadow-lg` | ⚠️ Somente modais | ✅ Permitido | Modais, dialogs — ficam acima do plano de conteúdo |
| `shadow-xl` | ❌ PROIBIDO | ✅ Permitido | Reservado para telas de entrada/branding |
| `shadow-2xl` | ❌ PROIBIDO | ✅ Permitido | Glassmorphism, telas imersivas |

> **Regra principal:** Em interfaces internas (Kanban, tabelas, modais de formulário, settings), o único nível de sombra padrão para cards é `shadow-sm`. O produto usa `shadow-sm` extensamente — ele é o esperado. `shadow-md` e `shadow-lg` são aceitos apenas como exceção contextual (dropdowns e modais overlay). `shadow-xl` e `shadow-2xl` são proibidos em qualquer interface interna.
>
> **Exceção modais:** `shadow-xl` em `bg-white rounded-md shadow-xl` para o container do modal é comum no codebase mas deve ser migrado para `shadow-lg` em refatorações futuras.

### Motion

| Tipo | Duração | Classe | Uso |
|------|---------|--------|-----|
| Instant | 50ms | `duration-50` | Feedback imediato |
| Fast | 100ms | `duration-100` | Hovers |
| Normal | 150ms | `duration-150` | Padrão |
| Slow | 200ms | `duration-200` | Modais |
| Slower | 300ms | `duration-300` | Sidebars, drawers |

### Dark Mode (Tokens)

| Token | Light | Dark |
|-------|-------|------|
| bg-primary | #FFFFFF | #0F1113 |
| bg-secondary | #F9FAFB | #1A1D1F |
| bg-tertiary | #F3F4F6 | #26292B |
| text-primary | #111827 | #F9FAFB |
| text-body | #1F2937 | #E5E7EB |
| border-subtle | #E5E7EB | #374151 |

Sombras em dark: aumentar opacidade (0.3/0.4/0.5).

### Acessibilidade (WCAG AA)

| Combinação | Contraste | Status |
|------------|-----------|--------|
| gray-900 / white | 16.73:1 | AAA |
| gray-800 / white | 13.36:1 | AAA |
| gray-600 / white | 7.92:1 | AAA |
| gray-500 / white | 5.89:1 | AA Large |
| green-700 / green-50 | 7.2:1 | AAA |

**ARIA obrigatórios:** `aria-label` em botões ícone, `role="dialog"` em modais, `aria-required` em inputs obrigatórios, `aria-live="polite"` em mensagens dinâmicas, `sr-only` para texto acessível.

**Keyboard:** Tab navega, Enter ativa, Esc fecha modais/dropdowns, Arrow keys em listas.

**Daltonismo:** Sempre ícone + cor + texto em badges de status.

**Reduced motion:** `@media (prefers-reduced-motion: reduce)` deve desabilitar animações.

### Cores Deprecadas (Eliminar)

| Cor Atual | Substituir Por | Tailwind |
|-----------|---------------|----------|
| #FAFAFA | #F9FAFB | gray-50 |
| #E8E8E8 | #E5E7EB | gray-200 |
| #666666 | #6B7280 | gray-500 |
| #999999 | #9CA3AF | gray-400 |
| #2D2D2D | #1F2937 | gray-800 |

---

## PASSO 3: Validação

```bash
# 1. Cyan em botões (PROIBIDO):
grep -rn "bg-cyan\|bg-\[#60BED1\]\|bg-blue-" [ARQUIVOS] --include="*.tsx" | grep -i "button\|btn"

# 2. rounded incorreto em botões (deve ser rounded-md):
grep -rn "rounded-sm\|rounded-lg\|rounded-xl" [ARQUIVOS] --include="*.tsx" | grep -i "button\|btn\|input"

# 3. Sombras excessivas:
grep -rn "shadow-2xl" [ARQUIVOS] --include="*.tsx"

# 4. Bordas grossas:
grep -rn "border-2\|border-4" [ARQUIVOS] --include="*.tsx"

# 5. Dark mode ausente:
grep -L "dark:" [ARQUIVOS] --include="*.tsx"

# 6. Hex hardcoded:
grep -rn "#[0-9A-Fa-f]\{6\}" [ARQUIVOS] --include="*.tsx" | grep -v "60BED1\|5DA47A\|D19960\|9860D1\|D160AB\|F59E0B\|design-tokens"

# 7. Labels em inputs:
grep -B2 "<input\|<Input\|<textarea\|<select" [ARQUIVOS] --include="*.tsx" | grep -c "htmlFor\|label"

# 8. Acessibilidade em modais:
grep -n "role=\"dialog\"\|aria-modal\|aria-label" [ARQUIVOS] --include="*.tsx"

# 9. Font consistency (deve ter Open Sans ou Inter):
grep -rn "font-sans\b" [ARQUIVOS] --include="*.tsx" | grep -v "Open_Sans\|Inter"

# 10. Deprecated colors:
grep -rn "#FAFAFA\|#E8E8E8\|#666666\|#999999\|#2D2D2D\|#E4EBEF" [ARQUIVOS] --include="*.tsx"

# 11. tabular-nums em dados numéricos:
grep -rn "font-\['Inter'\]" [ARQUIVOS] --include="*.tsx" | grep -v "tnum\|tabular"
```

### Screenshot-Ready Checklist

Antes de capturar tela para conversão Figma:

- [ ] Todos os componentes visíveis seguem DS v4.2.1
- [ ] Nenhuma cor fora do padrão (sem azuis, roxos ou cyans em botões)
- [ ] Grid consistente (12 colunas com gaps padronizados)
- [ ] Tipografia correta (Open Sans UI, Inter dados)
- [ ] Dark mode completo
- [ ] Estados visíveis (hover, active, disabled, error, loading, empty)
- [ ] Spacing consistente (base 4px)
- [ ] Nenhum componente com scroll cortado ou overflow

### Checklist Final por Componente

- [ ] Botões: primary preto, cyan apenas em ícones LIA
- [ ] Inputs: labels com htmlFor, focus ring grayscale
- [ ] Cards: rounded-xl, shadow-sm, sem gradientes
- [ ] Tabelas: Inter para números, tabular-nums, header uppercase
- [ ] Badges: rounded-full (pill), ícone+cor+texto
- [ ] Tipografia: Open Sans 85% (UI geral), Inter 10% (dados numéricos), JetBrains Mono 5% (código)
- [ ] Espaçamento: base 4px, grid 12-col
- [ ] Dark mode: variantes dark: em todos elementos
- [ ] Acessibilidade: ARIA labels, focus rings, contraste AA, keyboard nav
- [ ] Tokens: usar helpers quando disponível

---

## Formato de Relatório

```
## Padronização DS v4.2.1 — [Nome]

### Arquivos Modificados
- src/components/X.tsx: Y botões, Z inputs, W cards

### Conformidade
- Botões: ✅ 100% (3 primary, 2 secondary)
- Inputs: ✅ 100% (5 inputs com labels)
- Cards: ✅ rounded-md aplicado
- Tabelas: ✅ Inter + tabular-nums
- Tipografia: ✅ Open Sans UI, Inter dados
- Dark mode: ✅ 100%
- Acessibilidade: ⚠️ 2 botões sem aria-label

### Violações Corrigidas
- bg-blue-500 → bg-gray-900 (3 botões)
- rounded-xl → rounded-md (2 cards)
- font-serif → font-brand (1 header)

### Pendências
- [ ] aria-label em botão de fechar modal
```

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/design-standardize` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/design-standardize.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/design-standardize/SKILL.md` |

**Quando ativar:**
- Ao criar ou refatorar qualquer componente de UI, tela, modal ou botão
- Quando o usuário pedir "padronizar" ou "adequar ao design system"
- Antes de capturar screenshots para conversão Figma
- Como parte do fluxo de auditoria (`/feature-audit` — D3 UI/DS)
