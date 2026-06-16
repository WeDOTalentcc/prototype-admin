# Design System — WeDOTalent / Plataforma LIA (DS v4.2.1)

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `plataforma-lia/src/styles/design-tokens.css`, `plataforma-lia/tailwind.config.ts`, `plataforma-lia/src/app/globals.css`, `plataforma-lia/src/components/ui/*`
> **SPEC-DRIVEN DEVELOPMENT** — tokens, componentes e regras extraídos do código real do repositório `plataforma-lia`.

---

## 1. Framework e Stack

| Item | Valor | Arquivo de referência |
|------|-------|-----------------------|
| **UI Framework** | React 18 + Next.js (App Router) | `plataforma-lia/package.json` |
| **CSS Framework** | Tailwind CSS v3 | `plataforma-lia/tailwind.config.ts` |
| **Component Primitives** | Radix UI (Dialog, Select, Tabs, Tooltip, etc.) | `plataforma-lia/src/components/ui/*.tsx` |
| **Component Library** | shadcn/ui customizado + 70 componentes `ui/` | `plataforma-lia/src/components/ui/` |
| **Icons** | Lucide React (~100+ ícones em uso) | Importações em `components/pages/*.tsx` |
| **Variant System** | class-variance-authority (CVA) | `button.tsx`, `badge.tsx`, `toast.tsx` |
| **Utility Merge** | `cn()` via `clsx` + `tailwind-merge` | `plataforma-lia/src/lib/utils.ts` |

---

## 2. Design Tokens

### 2.1 Filosofia de Cor

**Regra 90/10:** 90% monocromático (escala de cinzas) + 10% acentos estratégicos de cor.

O acento cromático é reservado exclusivamente para:
- Elementos de IA/LIA (`wedo-cyan`)
- Identidade de marca (`coral`)
- Feedback semântico (success/warning/error)

### 2.2 Paleta de Cores — Acentos Estratégicos (10%)

| Nome | Hex | Variável CSS | Uso |
|------|-----|-------------|-----|
| **Cyan (LIA/IA)** | `#60BED1` | `--wedo-cyan` | Destaque IA, botões primários IA, links IA, focus ring |
| Cyan Dark | `#4DA8BB` | `--wedo-cyan-dark` | Hover sobre cyan |
| Cyan Light | `#B8E0EA` | `--wedo-cyan-light` | Backgrounds sutis IA |
| **Coral (Marca)** | `#C74446` | `--lia-brand-primary` | Identidade LIA (uso MÍNIMO — logo, hero) |
| Coral Hover | `#B23B3D` | `--lia-brand-primary-hover` | Hover coral |
| Coral Light BG | `#FEF2F2` | `--lia-brand-primary-light` | Background sutil marca |
| **Green** | `#5DA47A` | `--wedo-green` | Candidatos, sucesso, aprovação |
| **Orange** | `#D19960` | `--wedo-orange` | Alertas, warning, atenção |
| **Purple** | `#9860D1` | `--wedo-purple` | Insights, premium, análises IA |
| **Magenta** | `#D160AB` | `--wedo-magenta` | Urgência crítica, prioridade alta |
| **Amber** | `#F59E0B` | `--wedo-amber` | Warning vibrante |
| **Coral (complementar)** | `#E16162` | `--wedo-coral` | Erros, rejeição (Tailwind alias) |

**Arquivo:** `plataforma-lia/tailwind.config.ts` — `theme.extend.colors`

### 2.3 Hierarquia de Texto (4 níveis)

| Nível | Classe CSS | Light | Dark | Uso |
|-------|-----------|-------|------|-----|
| Title | `wedo-text-title` | `#030712` (gray-950) | `#F9FAFB` | Headings principais |
| Body | `wedo-text-body` | `#1F2937` (gray-800) | `#E5E7EB` | Texto principal, labels |
| Secondary | `wedo-text-secondary` | `#4B5563` (gray-600) | `#9CA3AF` | Descrições, captions |
| Muted | `wedo-text-muted` | `#6B7280` (gray-500) | `#6B7280` | Placeholders, disabled |

**Arquivo:** `plataforma-lia/src/styles/design-tokens.css` — seção `:root` e `.dark`

### 2.4 Backgrounds

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--lia-bg-primary` | `#FFFFFF` | `#0F1113` | Fundo principal da app |
| `--lia-bg-secondary` | `#F9FAFB` | `#1A1D1F` | Cards, panels |
| `--lia-bg-tertiary` | `#F3F4F6` | `#26292B` | Hover, disabled |
| `--lia-bg-elevated` | `#FFFFFF` | `#1A1D1F` | Cards elevados (com shadow) |

**Arquivo:** `plataforma-lia/src/styles/design-tokens.css`

### 2.5 Borders

| Token | Light | Dark |
|-------|-------|------|
| `--lia-border-subtle` | `#E5E7EB` | `#2D3748` |
| `--lia-border-default` | `#D1D5DB` | `#374151` |
| `--lia-border-medium` | `#9CA3AF` | `#4B5563` |

### 2.6 Cores de Categoria (badges/ícones por módulo)

| Categoria | Hex | Variável |
|-----------|-----|---------|
| Vagas | `#60BED1` | `--lia-cat-jobs` |
| Candidatos | `#5DA47A` | `--lia-cat-candidates` |
| Entrevistas | `#E5A853` | `--lia-cat-interviews` |
| Relatórios | `#8B5CF6` | `--lia-cat-reports` |

### 2.7 Cores Pastel ElevenLabs (sépia — cards decorativos)

| Nome | Hex | Uso |
|------|-----|-----|
| Sépia Light | `#F3EBE1` | Cards decorativos |
| Sépia Mint | `#DCE4DB` | Backgrounds sutis |
| Sépia Rose | `#E3DADC` | Backgrounds sutis |
| Sépia Blue | `#DDE1E9` | Backgrounds sutis |
| Sépia Lilac | `#E5E0E2` | Backgrounds sutis |
| Sépia Ice | `#EAEAEA` | Backgrounds neutros |

---

## 3. Tipografia

### 3.1 Regra 85/10/5

| Proporção | Fonte | Tailwind Class | Uso |
|-----------|-------|---------------|-----|
| **85%** | Open Sans (300–700) | `font-brand` / `font-open-sans` | Títulos, navegação, sidebar, tabs, botões, corpo de texto |
| **10%** | Inter (300–700) | `font-data` / `font-inter` | Métricas numéricas, scores, dados tabulares |
| **5%** | JetBrains Mono | `font-mono` | Código, IDs, terminal |

**Fontes legadas (em substituição):** `font-sidebar` / `font-source-serif-4` (Source Serif 4), `font-crimson` (Crimson Text — uso decorativo mínimo).

**Google Fonts importadas:** Inter (300–700), Open Sans (300–700)

**Arquivo:** `plataforma-lia/tailwind.config.ts` — `theme.extend.fontFamily`; `plataforma-lia/src/app/globals.css` — `@import url()`

### 3.2 Escala Tipográfica

| Uso | Fonte | Peso | Tamanho | Line-Height | Cor (Light) | Cor (Dark) |
|-----|-------|------|---------|-------------|-------------|------------|
| H1 | Open Sans | 600 | 2rem (32px) | 1.2 | `#1F2937` | `#F9FAFB` |
| H2 | Open Sans | 600 | 1.5rem (24px) | 1.25 | `#1F2937` | `#F9FAFB` |
| H3 | Open Sans | 600 | 1.25rem (20px) | 1.3 | `#1F2937` | `#F9FAFB` |
| H4 | Open Sans | 600 | 1rem (16px) | 1.4 | `#1F2937` | `#F9FAFB` |
| Page Title | Open Sans | 600 | 1.75rem (28px) | 1.2 | `#1F2937` | `#F9FAFB` |
| Subtitle | Open Sans | 400 | 1rem (16px) | 1.5 | `#374151` | `#E5E7EB` |
| Body | Open Sans | 400 | 0.875rem (14px) | 1.6 | `#4B5563` | `#D1D5DB` |
| Body SM | Open Sans | 400 | 0.8125rem (13px) | 1.5 | `#4B5563` | `#D1D5DB` |
| Label | Open Sans | 500 | 0.875rem (14px) | 1.4 | `#1F2937` | `#F9FAFB` |
| Label SM | Open Sans | 500 | 0.75rem (12px) | 1.3 | `#1F2937` | `#F9FAFB` |
| Helper | Open Sans | 400 | 0.75rem (12px) | 1.4 | `#6B7280` | `#9CA3AF` |
| Caption / Eyebrow | Open Sans | 500 | 0.6875rem (11px) | 1.3 | `#6B7280` (uppercase, 0.05em) | `#9CA3AF` |
| Nav/Tabs/Menu | Open Sans | 500 | 0.6875rem (11px) | 1.125rem | — | — |
| **Componentes UI** | — | — | **11px** (`text-[11px]`) | — | — | — |

**Regra universal:** Todos os componentes de interface (buttons, inputs, badges, labels) usam `text-[11px]` como tamanho base.

**Arquivo:** `plataforma-lia/src/app/globals.css` — classes `.lia-h1` a `.lia-h4`; `plataforma-lia/src/components/ui/*.tsx`

---

## 4. Shadows

| Token | Light | Dark |
|-------|-------|------|
| `--lia-shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.02)` | `0 1px 2px 0 rgb(0 0 0 / 0.3)` |
| `--lia-shadow-default` | `0 1px 3px 0 rgb(0 0 0 / 0.05)` | `0 1px 3px 0 rgb(0 0 0 / 0.4)` |
| `--lia-shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.05)` | `0 4px 6px -1px rgb(0 0 0 / 0.5)` |
| `--lia-shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.05)` | `0 10px 15px -3px rgb(0 0 0 / 0.6)` |

**Design principle:** Sombras muito sutis em light mode (opacity 0.02–0.05), mais pronunciadas em dark mode (0.3–0.6).

**Arquivo:** `plataforma-lia/src/styles/design-tokens.css`

---

## 5. Border Radius

| Token Tailwind | Valor | Uso |
|---------------|-------|-----|
| `rounded-lg` | `var(--radius)` = 0.75rem (12px) | Cards grandes |
| `rounded-md` | `calc(var(--radius) - 2px)` ≈ 10px | Cards padrão, modais, inputs |
| `rounded-sm` | `calc(var(--radius) - 4px)` ≈ 8px | Botões, badges |
| `rounded-full` | 9999px | Avatares, pills, tabs, badges circulares |

**Arquivo:** `plataforma-lia/tailwind.config.ts` — `theme.extend.borderRadius`

---

## 6. Transições e Animações

### 6.1 Transições Base

| Propriedade | Valor |
|------------|-------|
| Duração global | 200ms |
| Timing function | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Background transition | 0.3s ease |

### 6.2 Animações Definidas

| Nome | Tipo | Uso |
|------|------|-----|
| `fadeIn` | `translateY(10px)` → 0, opacity 0→1 | Entrada de páginas |
| `slideIn` / `slideInRight` | `translateX(30px)` → 0 | Painéis laterais |
| `scaleIn` | `scale(0.95)` → 1 | Modais |
| `slideInFromRight` | `translateX(300px)` → 0 | Sidebar de candidato |
| `dotsPulse` | `scale(1)` → 1.5 | Loading dots |
| `shimmer` | background-position shift | Loading skeleton |
| `fieldHighlightFade` | yellow bg → transparent | Sincronização de campos (Wizard) |
| `fieldPulse` | box-shadow pulse | Destaque de campo |
| `loading-skeleton` | gradient sweep | Skeleton screens |

### 6.3 Micro-interações

| Classe CSS | Efeito | Uso |
|-----------|--------|-----|
| `.hover-lift` | `translateY(-2px)` + shadow | Cards interativos |
| `.hover-glow` | `box-shadow: 0 0 20px rgba(96,190,209,0.3)` | Elementos IA |
| `.hover-border` | `border-color: ai-aqua/0.5` | Inputs com foco IA |
| `.micro-bounce` | active: `scale(0.95)` | Botões |
| `.micro-scale` | hover: `scale(1.02)` | Cards clicáveis |

### 6.4 Radix UI Override

Animações nativas de entrada/saída dos Tooltips e Dropdowns Radix são desabilitadas (`animation: none !important`) para responsividade imediata. Os componentes Dialog e AlertDialog mantêm animações de overlay (fade) e content (zoom/scale) para dar feedback visual de abertura/fechamento.

**Arquivo:** `plataforma-lia/src/app/globals.css`

---

## 7. Breakpoints e Layout

### 7.1 Breakpoints

| Breakpoint | Valor | Uso |
|-----------|-------|-----|
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |
| xl | 1280px | Desktop wide |
| 2xl | 1536px | Large desktop |

### 7.2 Container Padding

| Breakpoint | Padding |
|-----------|---------|
| DEFAULT | 1rem |
| sm (640px) | 2rem |
| lg (1024px) | 4rem |
| xl (1280px) | 5rem |
| 2xl (1536px) | 6rem |

### 7.3 Layout Principal

```
Sidebar (colapsável ~240px/48px)
├── Content Area (max-w-7xl mx-auto px-4 sm:px-6 lg:px-8)
│   ├── TopBar (full width, border-bottom)
│   └── Main Content (flex-1)
└── Side Panels (overlay, slide-in)
```

**Arquivo:** `plataforma-lia/tailwind.config.ts` — `theme.container`

---

## 8. Dark Mode

### 8.1 Estratégia

- **Implementação:** Class strategy (`.dark` no `<html>`)
- **Toggle:** Componente `ThemeToggle` (`plataforma-lia/src/components/theme-toggle.tsx`) na sidebar
- **Cobertura:** Todas as variáveis CSS têm valores dark definidos em `design-tokens.css`

### 8.2 Padrão de Implementação

Todos os componentes usam classes condicionais Tailwind:
```
bg-white dark:bg-gray-800
text-gray-900 dark:text-gray-100
border-gray-200 dark:border-gray-700
```

### 8.3 Tokens Dark Override

| Categoria | Light | Dark |
|-----------|-------|------|
| Background primary | `#FFFFFF` | `#0F1113` |
| Background secondary | `#F9FAFB` | `#1A1D1F` |
| Background tertiary | `#F3F4F6` | `#26292B` |
| Text title | `#030712` | `#F9FAFB` |
| Text body | `#1F2937` | `#E5E7EB` |
| Border subtle | `#E5E7EB` | `#2D3748` |
| Border default | `#D1D5DB` | `#374151` |

**Arquivo:** `plataforma-lia/src/styles/design-tokens.css` — bloco `.dark`

---

## 9. Biblioteca de Componentes Base (shadcn/ui + Radix)

### 9.1 Button

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/button.tsx` |
| **Exports** | `Button`, `buttonVariants` |
| **Primitiva** | Radix `Slot` (via `asChild`) |
| **Texto base** | `!text-[11px]`, `font-medium` |
| **Focus** | `focus-visible:ring-2 focus-visible:ring-gray-900/20` |

| Variante | Background (Light) | Text | Hover |
|----------|-------------------|------|-------|
| `default` / `primary` | `bg-gray-900` | `text-white` | `bg-gray-800` |
| `destructive` | `bg-red-600` | `text-white` | `bg-red-700` |
| `outline` | `bg-white` border `gray-300` | `text-gray-800` | `bg-gray-50` |
| `secondary` | `bg-gray-100` | `text-gray-950` | `bg-gray-200` |
| `ghost` | transparent | `text-gray-800` | `bg-gray-100` |
| `link` | transparent | `text-gray-700` underline | underline on hover |

| Tamanho | Classes |
|---------|---------|
| `default` | `h-10 px-4 py-2` |
| `sm` | `h-9 rounded-md px-3` |
| `lg` | `h-11 rounded-md px-8` |
| `icon` | `h-10 w-10` |

### 9.2 Badge

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/badge.tsx` |
| **Exports** | `Badge`, `badgeVariants` |
| **Base** | `rounded-full`, `px-2.5 py-0.5`, `text-[11px]`, `font-medium`, border |

| Variante | Background | Text |
|----------|-----------|------|
| `default` | `bg-gray-100` | `text-gray-950` |
| `secondary` | `bg-gray-100` | `text-gray-700` |
| `destructive` | `bg-red-100` | `text-red-800` |
| `outline` | transparent (border `gray-300`) | `text-gray-800` |
| `success` | `rgba(123,194,154,0.15)` | `#5aa078` |
| `warning` | `rgba(232,168,124,0.15)` | `#c58a5e` |
| `info` | `wedo-cyan/15` | `#50a3b8` |
| `lilac` | `rgba(201,160,220,0.15)` | `#a078b0` |

### 9.3 Card

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/card.tsx` |
| **Exports** | `Card`, `CardHeader`, `CardFooter`, `CardTitle`, `CardDescription`, `CardContent` |
| **Card base** | `rounded-md`, border, `bg-card text-card-foreground` |
| **CardHeader** | `flex flex-col space-y-1.5 p-6` |
| **CardTitle** | `text-xs font-semibold leading-none tracking-tight` |
| **CardDescription** | `text-[11px] text-muted-foreground` |
| **CardContent** | `p-6 pt-0` |
| **CardFooter** | `flex items-center p-6 pt-0` |

### 9.4 Input

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/input.tsx` |
| **Dimensões** | `h-10`, `w-full`, `rounded-md`, `px-3 py-2` |
| **Texto** | `text-[11px]` |
| **Border** | `border-gray-300` (light) / `border-gray-600` (dark) |
| **Background** | `bg-white` / `bg-gray-700` (dark) |
| **Focus** | `focus:border-gray-500 focus:ring-2 focus:ring-gray-900/20` |

### 9.5 Textarea

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/textarea.tsx` |
| **Min height** | `min-h-[80px]` |
| **Texto** | `text-[11px]` |
| **Padrão** | Mesmo border/focus do Input |

### 9.6 Select

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/select.tsx` |
| **Exports** | `Select`, `SelectGroup`, `SelectValue`, `SelectTrigger`, `SelectContent`, `SelectLabel`, `SelectItem`, `SelectSeparator`, `SelectScrollUpButton`, `SelectScrollDownButton` |
| **Primitiva** | Radix Select |
| **Trigger** | `h-10`, border `gray-300`, `bg-white`, `text-sm` |
| **Content** | `z-50`, `rounded-md`, border, `bg-white` |
| **Item** | `py-1.5 pl-8 pr-2`, `text-sm`, focus: `bg-gray-100` |

### 9.7 Checkbox

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/checkbox.tsx` |
| **Primitiva** | Radix Checkbox |
| **Dimensões** | `h-4 w-4`, `rounded-sm` |
| **Checked** | `bg-gray-900 border-gray-900 text-white` (dark: `bg-gray-50`) |
| **Indicator** | `Check` icon (Lucide) `h-3 w-3` |

### 9.8 Switch

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/switch.tsx` |
| **Primitiva** | Radix Switch |
| **Track** | `h-5 w-9`, `rounded-full` |
| **Checked** | `bg-gray-900` (dark: `bg-gray-50`) |
| **Unchecked** | `bg-gray-200` (dark: `bg-gray-700`) |
| **Thumb** | `h-4 w-4`, `bg-white`, `rounded-full`, `translate-x-4` when checked |

### 9.9 Tabs

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/tabs.tsx` |
| **Primitiva** | Radix Tabs |
| **TabsList** | `h-10`, `rounded-full`, `bg-gray-100 p-1` (dark: `bg-gray-800`) |
| **TabsTrigger** | `rounded-full px-3 py-1.5`, `text-sm font-medium` |
| **Active** | `bg-white text-gray-900` (dark: `bg-gray-950 text-gray-50`) |

### 9.10 Dialog (Modal)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/dialog.tsx` |
| **Exports** | `Dialog`, `DialogPortal`, `DialogOverlay`, `DialogClose`, `DialogTrigger`, `DialogContent`, `DraggableDialogContent`, `DialogHeader`, `DialogFooter`, `DialogTitle`, `DialogDescription` |
| **Primitiva** | Radix Dialog |
| **Overlay** | `bg-black/30 backdrop-blur-[1px]`, z-index `50` |
| **Content** | `max-w-lg`, `border-gray-100`, `bg-white`, `p-6`, `rounded-md`, z-index `9999` |
| **Close** | `X` icon (Lucide), `absolute right-4 top-4`, `text-gray-500 hover:text-gray-800` |
| **Title** | `text-xs font-semibold` |
| **Description** | `text-[11px] text-gray-600` |
| **DraggableDialogContent** | Mesma aparência + drag handle (h-12, `cursor-move`) |

### 9.11 Sheet (Side Panel)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/sheet.tsx` |
| **Primitiva** | Radix Dialog (reused) |
| **Overlay** | `bg-background/80 backdrop-blur-sm` |

| Side | Positioning | Default width |
|------|------------|---------------|
| `right` (default) | `inset-y-0 right-0` | `w-3/4 sm:max-w-sm` |
| `left` | `inset-y-0 left-0` | `w-3/4 sm:max-w-sm` |
| `top` | `inset-x-0 top-0` | — |
| `bottom` | `inset-x-0 bottom-0` | — |

### 9.12 Table

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/table.tsx` |
| **Exports** | `Table`, `TableHeader`, `TableBody`, `TableFooter`, `TableHead`, `TableRow`, `TableCell`, `TableCaption` |
| **Table** | `w-full caption-bottom text-sm`, wrapped in overflow-auto div |
| **TableHead** | `h-10 px-2`, `font-medium text-muted-foreground` |
| **TableRow** | `border-b`, hover: `bg-muted/50`, selected: `bg-muted` |
| **TableCell** | `p-2 align-middle` |

### 9.13 Avatar

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/avatar.tsx` |
| **Primitiva** | Radix Avatar |
| **Avatar** | `h-10 w-10`, `rounded-full`, `overflow-hidden` |
| **Fallback** | `bg-muted`, `rounded-full`, centered content |

### 9.14 Tooltip

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/tooltip.tsx` |
| **Primitiva** | Radix Tooltip |
| **Content** | `z-50`, `rounded-md`, border, `bg-popover`, `px-3 py-1.5`, `text-sm` |

### 9.15 DropdownMenu

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/dropdown-menu.tsx` |
| **Primitiva** | Radix DropdownMenu |
| **Content** | `z-50`, `min-w-[8rem]`, `rounded-md`, border, `bg-popover p-1` (dark: `bg-gray-800`) |
| **Item** | `px-2 py-1.5`, `text-sm`, focus: `bg-accent` |

### 9.16 Progress

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/progress.tsx` |
| **Primitiva** | Radix Progress |
| **Track** | `h-2`, `rounded-full`, `bg-gray-100` (dark: `bg-gray-800`) |
| **Indicator** | `bg-gray-900` (dark: `bg-gray-100`), `transition-all 300ms` |

### 9.17 Accordion

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/accordion.tsx` |
| **Primitiva** | Radix Accordion |
| **Item** | `border-b` |
| **Trigger** | `flex flex-1 items-center justify-between py-4 font-medium`, `ChevronDown` rotates 180° |
| **Content** | `text-sm`, `pb-4 pt-0`, `animate-accordion-up/down` |

### 9.18 AlertDialog

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/alert-dialog.tsx` |
| **Primitiva** | Radix AlertDialog |
| **Overlay** | `bg-black/30 backdrop-blur-[1px]`, z-index `50` |
| **Content** | `max-w-lg`, `p-6`, `sm:rounded-md`, z-index `50` |
| **Action** | `buttonVariants()` (default style) |
| **Cancel** | `buttonVariants({ variant: "outline" })` |

### 9.19 Popover

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/popover.tsx` |
| **Primitiva** | Radix Popover |
| **Content** | `z-50`, `w-72`, `rounded-md`, `p-4`, border `gray-200` (dark: `gray-700`), bg `white` (dark: `gray-800`) |

### 9.20 Toast

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/toast.tsx` + `toaster.tsx` |
| **Primitiva** | Radix Toast |
| **Viewport** | `fixed top-0 z-[100]`, mobile: top, desktop: `sm:bottom-0 sm:right-0`, max-w `md:max-w-[420px]` |
| **Base** | `rounded-md`, border, `p-6 pr-8`, swipe gestures |
| **Hook** | `useToast()` — `plataforma-lia/src/hooks/use-toast.ts` |

| Variante | Background | Text | Border |
|----------|-----------|------|--------|
| `default` | `bg-background` | `text-foreground` | border |
| `destructive` | `bg-destructive` | `text-destructive-foreground` | `border-destructive` |
| `success` | `bg-green-50` | `text-green-900` | `border-green-200` |
| `warning` | `bg-yellow-50` | `text-yellow-900` | `border-yellow-200` |
| `info` | `bg-blue-50` | `text-blue-900` | `border-blue-200` |

### 9.21 Command (cmdk)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/command.tsx` |
| **Primitiva** | cmdk (Command Menu) |
| **Input** | `h-11`, `Search` icon, `text-sm` |
| **List** | `max-h-[300px] overflow-y-auto` |
| **Item** | `px-2 py-1.5 text-sm`, selected: `bg-accent` |

---

## 10. Componentes Especializados

### 10.1 StatusBadge (Sistema de Status por Etapa)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/status-badge.tsx` |
| **Exports** | `StatusBadge`, `ChannelBadge`, `SourceBadge`, `WarningBadge`, `DateTimeBadge`, `OriginBadge`, `AwaitingBadge` |
| **Font** | Open Sans, 9px |
| **Padding** | `px-1.5 py-0.5`, `rounded-full` |

| Variante | BG (Light) | Text | Font Weight |
|----------|-----------|------|-------------|
| `standard` | `#F9FAFB` | `#4B5563` | 500 |
| `dark` | `#111827` | `#FFFFFF` | 700 |
| `accent` | Pastel dinâmico por etapa | `#111827` | 600 |
| `outlined` | `#F9FAFB` | `#374151` | 400 (+ border) |
| `channel` | `#F3F4F6` | `#1F2937` | 400 (+ border) |
| `scheduled` | `#1F2937` | `#FFFFFF` | 600 |
| `hired` | `#111827` | `#FFFFFF` | 700 |

**Cores Pastel por Etapa (accent):**

| Etapa | Light | Dark |
|-------|-------|------|
| sourcing | `#DCE4DB` | `#3D4A3C` |
| screening | `#E3DADC` | `#4A3D40` |
| interview_* | `#DDE1E9` | `#3D414A` |
| references / offer | `#E5E0E2` | `#454043` |
| hired | `#EAEAEA` | `#3A3A3A` |
| rejected | `#F5F5F5` | `#404040` |

### 10.2 ScoreIconButton

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/score-icon-button.tsx` |
| **Layout** | `flex items-center gap-1`, `rounded-full` |
| **Score text** | `text-[11px] font-bold font-['Open_Sans'] text-gray-700` |
| **Ativo** | color `#111827` (LIA scores) / `#374151` (outros) |
| **Inativo** | color `#9CA3AF`, `opacity-25` |
| **Hover (ativo)** | `scale-105` |

### 10.3 EmptyState

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/empty-state.tsx` |
| **Layout** | `flex flex-col items-center justify-center py-12 px-6 text-center` |
| **Ícone** | `text-gray-300` (dark: `text-gray-600`), `w-10 h-10` |
| **Título** | `text-sm font-medium text-gray-700` |
| **Descrição** | `text-xs text-gray-500 max-w-xs` |
| **Ação** | `Button variant="outline" size="sm" rounded-md text-xs` |

### 10.4 Loading (4 variantes)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/loading.tsx` |
| **Exports** | `Loading`, `LoadingCard`, `LoadingList` |

| Variante | Descrição |
|----------|-----------|
| `spinner` | Circle border com `animate-spin` |
| `dots` | 3 dots com `dotsPulse` animation |
| `skeleton` | 3 linhas com `loading-skeleton` |
| `pulse` | Circle com `animate-pulse` |

| Tamanho | Dimensões |
|---------|-----------|
| `sm` | `w-4 h-4` |
| `md` | `w-6 h-6` |
| `lg` | `w-8 h-8` |

### 10.5 Skeleton

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/skeleton.tsx` |
| **Classes** | `animate-pulse rounded-md bg-gray-200` (dark: `bg-gray-700`) |

### 10.6 CandidateCard

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/candidate-card.tsx` |
| **Composição** | `Card` + `CardContent` + `Badge` + `Button` |
| **Ícones** | MapPin, Building, Mail, Linkedin, ExternalLink, Award, Calendar, ChevronDown/Up, MessageSquare, Check, AlertCircle, Clock, Send |

### 10.7 ContextPill

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/context-pill.tsx` |
| **Layout** | `inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border` |
| **Dismiss** | `X` icon, `h-5 w-5` |

### 10.8 AudioPlayer / AudioRecordButton

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/audio-player.tsx`, `audio-record-button.tsx` |
| **Player** | Play/Pause, progress bar, timestamp, volume |
| **Recorder** | Record button (pulsante), timer, stop |

---

## 11. CSS Utilitárias Customizadas

### 11.1 Cards

| Classe | Background | Shadow | Border |
|--------|-----------|--------|--------|
| `.lia-card` | `#FFFFFF` | `0 1px 3px rgba(0,0,0,0.04)` | none |
| `.lia-card-elevated` | `#FFFFFF` | `0 4px 12px rgba(0,0,0,0.06)` | none |
| `.lia-card-hover` | `#FFFFFF` | hover: `0 4px 16px rgba(0,0,0,0.08)` | none |
| `.wedo-card` | `bg-white` | `0 1px 2px rgba(0,0,0,0.02)` | `1px solid wedo-gray-200` |
| `.wedo-card-elevated` | `bg-white` | `0 2px 8px rgba(0,0,0,0.04)` | `1px solid wedo-gray-200` |

### 11.2 Botões CSS

| Classe | Background | Text | Hover |
|--------|-----------|------|-------|
| `.lia-btn-primary` | `#60BED1` (cyan) | `#FFFFFF` | `#4FA8BA` |
| `.lia-btn-secondary` | `#F3F4F6` | `#1F2937` | `#E5E7EB` |
| `.lia-btn-ghost` | transparent | `#4B5563` | `#F9FAFB` |
| `.wedo-button-primary` | `hsl(--ai-aqua)` | white | `translateY(-1px)` |
| `.wedo-button-secondary` | `bg-gray-50` | `text-gray-700` | `bg-gray-100` |

### 11.3 Badges CSS

| Classe | Background | Text |
|--------|-----------|------|
| `.lia-badge-jobs` | `rgba(96,190,209,0.12)` | `#0E7490` |
| `.lia-badge-candidates` | `rgba(93,164,122,0.12)` | `#166534` |
| `.lia-badge-interviews` | `rgba(229,168,83,0.12)` | `#92400E` |
| `.lia-badge-reports` | `rgba(139,92,246,0.12)` | `#6D28D9` |
| `.lia-badge-neutral` | `#F3F4F6` | `#4B5563` |

### 11.4 Surfaces

| Classe | Descrição |
|--------|-----------|
| `.wedo-surface` | `bg: wedo-surface`, `border: wedo-gray-200` |
| `.wedo-surface-elevated` | `.wedo-surface` + shadow |
| `.wedo-sidebar` | `.wedo-surface-elevated` + `border-right` |
| `.wedo-topbar` | `.wedo-surface` + `border-bottom` |
| `.wedo-divider` | `border-bottom: wedo-gray-200` + subtle shadow |

---

## 12. Ícones

### 12.1 Library

| Library | Uso |
|---------|-----|
| **Lucide React** | ~100+ ícones em toda a plataforma |

### 12.2 Ícones mais usados por área

| Área | Ícones |
|------|--------|
| Sidebar | LayoutDashboard, Briefcase, Users, Settings, Search, Filter, PlayCircle, PauseCircle, CheckCircle, XCircle, Target, ChevronLeft/Right, Lock, Crown, HelpCircle |
| TopBar | Bell, User, KeyRound, LogOut, Eye, EyeOff, Check, X |
| Jobs | Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Share2, Clock, BarChart3, FileText, Briefcase, Building, Target, MoreHorizontal |
| Kanban | GripVertical, ArrowUp/Down, Filter, Award, Trash2, RefreshCw, MessageSquare, Send, Phone, Mic, Paperclip, Bookmark |
| StatusBadge | Clock, CheckCircle, XCircle, Trophy, CalendarCheck, MessageCircle, BrainCircuit, FileText |
| Screening | Brain, Lightbulb, Zap, ClipboardList, ListChecks, Scale, Loader2 |
| Comunicação | MessageSquare, Mail, Phone, Send, Paperclip, MessageCircle |

### 12.3 Ícone LIA

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/lia-icon.tsx` |
| **Variações** | sm / md / lg, com/sem animação (pulsante quando ativa) |
| **Cor** | Cyan (`#60BED1`) |

---

## 13. Acessibilidade

| Item | Implementação |
|------|--------------|
| Keyboard navigation | Radix UI primitives (built-in ARIA + keyboard) |
| Focus indicators | `focus-visible:ring-2 focus-visible:ring-gray-900/20` em todos os componentes |
| Screen reader | ARIA labels via Radix + `sr-only` classes |
| Color contrast | Gray-900 sobre white (ratio ~16:1), gray-600 sobre white (~5.7:1) |
| Keyboard shortcuts | `A` = Approve, `R` = Reject, `←/→` = navigation (CandidateReviewModal) |
| AI search activation | Ctrl+K / Cmd+K (ativa busca IA em qualquer página) |

---

## 14. Design Debt Conhecido

O repositório `ats_front` (Vue/Vuetify — frontend legado) ainda usa teal genérico hardcoded nos componentes de chat, em vez dos tokens do DS v4.2.1 (`#60BED1` para cyan, `#111827` para primário). O codebase React (`plataforma-lia`) já foi totalmente unificado: todos os componentes usam `wedo-cyan` (`#60BED1`) e o token `chat-cyan` foi removido do Tailwind config.

**Referência:** `docs/JIRA_CARD_CHAT_DESIGN_FIX.md`

O mapeamento completo React → Vuetify para futura migração está em `docs/PRODUCT_DESIGN_INVENTORY.md` (Seção 18).

---

## Referências de Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `plataforma-lia/src/styles/design-tokens.css` | Tokens CSS canônicos (cores, backgrounds, borders, shadows) |
| `plataforma-lia/tailwind.config.ts` | Theme extensions (breakpoints, colors, fonts, radius) |
| `plataforma-lia/src/app/globals.css` | Font imports, animações, utility classes, overrides |
| `plataforma-lia/src/components/ui/*.tsx` | 70 componentes base shadcn/ui + Radix |
| `plataforma-lia/src/lib/utils.ts` | `cn()` utility (clsx + tailwind-merge) |
| `docs/PRODUCT_DESIGN_INVENTORY.md` | Inventário completo de 70 componentes, 35 modais, todas as telas |
| `docs/JIRA_CARD_CHAT_DESIGN_FIX.md` | Design debt — chat LIA colors fix |

---

## 2.6 Unificação de Sistemas de Tokens

O projeto mantinha dois sistemas CSS coexistentes:
- **shadcn/ui** (HSL): variáveis como , , 
- **LIA DS** (hex): variáveis como , 

**Solução adotada:** aliases em  que fazem as variáveis shadcn apontarem para os tokens LIA.
Isso garante que componentes shadcn/ui automaticamente usem o Design System LIA sem breaking changes.

**Regra:** Novos componentes devem usar variáveis  e  diretamente.
As variáveis shadcn (, etc.) são mantidas apenas para compatibilidade com a biblioteca.


---

## 2.6 Unificacao de Sistemas de Tokens

O projeto mantinha dois sistemas CSS coexistentes:
- **shadcn/ui** (HSL): variaveis como `--background`, `--foreground`, `--primary`
- **LIA DS** (hex): variaveis como `--lia-bg-primary`, `--lia-text-primary`

**Solucao adotada:** aliases em `design-tokens.css` que fazem as variaveis shadcn apontarem para os tokens LIA.
Isso garante que componentes shadcn/ui automaticamente usem o Design System LIA sem breaking changes.

**Regra:** Novos componentes devem usar variaveis `--lia-*` e `--wedo-*` diretamente.
As variaveis shadcn (`--background`, etc.) sao mantidas apenas para compatibilidade com a biblioteca.
