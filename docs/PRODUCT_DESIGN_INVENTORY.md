# Inventário Completo de Design — Plataforma LIA (WeDOTalent)

> Documento de referência para revisão de design. Cobre 100% dos elementos visuais da área operacional.
> Última atualização: Março 2026

---

## 1. DESIGN TOKENS GLOBAIS

### 1.1 Tipografia

| Uso | Fonte | Peso | Tamanho | Line-Height | Cor (Light) | Cor (Dark) |
|-----|-------|------|---------|-------------|-------------|------------|
| H1 | Open Sans | 600 | 2rem (32px) | 1.2 | #1F2937 | #F9FAFB |
| H2 | Open Sans | 600 | 1.5rem (24px) | 1.25 | #1F2937 | #F9FAFB |
| H3 | Open Sans | 600 | 1.25rem (20px) | 1.3 | #1F2937 | #F9FAFB |
| H4 | Open Sans | 600 | 1rem (16px) | 1.4 | #1F2937 | #F9FAFB |
| Page Title | Open Sans | 600 | 1.75rem (28px) | 1.2 | #1F2937 | #F9FAFB |
| Subtitle | Open Sans | 400 | 1rem (16px) | 1.5 | #374151 | #E5E7EB |
| Subtitle SM | Open Sans | 400 | 0.875rem (14px) | 1.5 | #374151 | #E5E7EB |
| Body | Open Sans | 400 | 0.875rem (14px) | 1.6 | #4B5563 | #D1D5DB |
| Body SM | Open Sans | 400 | 0.8125rem (13px) | 1.5 | #4B5563 | #D1D5DB |
| Label | Open Sans | 500 | 0.875rem (14px) | 1.4 | #1F2937 | #F9FAFB |
| Label SM | Open Sans | 500 | 0.75rem (12px) | 1.3 | #1F2937 | #F9FAFB |
| Helper | Open Sans | 400 | 0.75rem (12px) | 1.4 | #6B7280 | #9CA3AF |
| Caption | Open Sans | 500 | 0.6875rem (11px) | 1.3 | #6B7280 (uppercase, 0.05em) | #9CA3AF |
| Eyebrow | Open Sans | 500 | 0.6875rem (11px) | — | #6B7280 (uppercase, 0.05em) | #9CA3AF |
| Nav/Tabs/Menu | Open Sans | 500 | 0.6875rem (11px) | 1.125rem (18px) | — | — |
| Componentes UI (buttons, inputs, badges) | — | — | 11px (`text-[11px]`) | — | — | — |

**Família de fontes (Tailwind config):**
- `font-brand` / `font-open-sans`: Open Sans (títulos, navegação, sidebar, tabs, botões)
- `font-data` / `font-inter`: Inter (métricas numéricas, dados)
- `font-crimson`: Crimson Text (serif, uso decorativo mínimo)
- `font-sidebar` / `font-source-serif-4`: Source Serif 4 (legado, sendo substituído por Open Sans)

**Regra 85/10/5:** Open Sans 85% | Inter 10% (dados/métricas) | JetBrains Mono 5% (código/terminal)

**Google Fonts importadas:** Inter (300-700), Open Sans (300-700)

### 1.2 Paleta de Cores

#### Hierarquia de Texto (4 níveis)
| Nível | Classe CSS | Light | Dark | Uso |
|-------|-----------|-------|------|-----|
| Title | `wedo-text-title` | #030712 (gray-950) | #F9FAFB | Headings principais |
| Body | `wedo-text-body` | #1F2937 (gray-800) | #E5E7EB | Texto principal, labels |
| Secondary | `wedo-text-secondary` | #4B5563 (gray-600) | #9CA3AF | Descrições, captions |
| Muted | `wedo-text-muted` | #6B7280 (gray-500) | #6B7280 | Placeholders, disabled |

#### Backgrounds
| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--lia-bg-primary` | #FFFFFF | #0F1113 | Fundo principal |
| `--lia-bg-secondary` | #F9FAFB | #1A1D1F | Cards, panels |
| `--lia-bg-tertiary` | #F3F4F6 | #26292B | Hover, disabled |
| `--lia-bg-elevated` | #FFFFFF | #1A1D1F | Cards elevados (com shadow) |

#### Borders
| Token | Light | Dark |
|-------|-------|------|
| `--lia-border-subtle` | #E5E7EB | #2D3748 |
| `--lia-border-default` | #D1D5DB | #374151 |
| `--lia-border-medium` | #9CA3AF | #4B5563 |

#### Acentos Estratégicos (10% da interface)
| Nome | Hex | Variável CSS | Uso |
|------|-----|-------------|-----|
| **Cyan (LIA/IA)** | #60BED1 | `--wedo-cyan` | Destaque IA, botões primários, links, focus ring |
| Cyan Dark | #4DA8BB | `--wedo-cyan-dark` | Hover cyan |
| Cyan Light | #B8E0EA | `--wedo-cyan-light` | Backgrounds sutis |
| **Coral (Marca)** | #C74446 | `--lia-brand-primary` | Identidade LIA (uso MÍNIMO) |
| Coral Hover | #B23B3D | `--lia-brand-primary-hover` | Hover coral |
| Coral Light BG | #FEF2F2 | `--lia-brand-primary-light` | Background sutil |
| **Green** | #5DA47A | `--wedo-green` | Candidatos, sucesso, aprovação |
| **Orange** | #D19960 | `--wedo-orange` | Alertas, warning, atenção |
| **Purple** | #9860D1 | `--wedo-purple` | Insights, premium, análises IA |
| **Magenta** | #D160AB | `--wedo-magenta` | Urgência crítica, prioridade alta |
| **Amber** | #F59E0B | `--wedo-amber` | Warning vibrante |

#### Cores de Categoria (para badges/ícones)
| Categoria | Hex | Variável |
|-----------|-----|---------|
| Vagas | #60BED1 | `--lia-cat-jobs` |
| Candidatos | #5DA47A | `--lia-cat-candidates` |
| Entrevistas | #E5A853 | `--lia-cat-interviews` |
| Relatórios | #8B5CF6 | `--lia-cat-reports` |

#### Cores Pastel ElevenLabs (sépia)
| Nome | Hex | Uso |
|------|-----|-----|
| Sépia Light | #F3EBE1 | Cards decorativos |
| Sépia Mint | #DCE4DB | Backgrounds sutis |
| Sépia Rose | #E3DADC | Backgrounds sutis |
| Sépia Blue | #DDE1E9 | Backgrounds sutis |
| Sépia Lilac | #E5E0E2 | Backgrounds sutis |
| Sépia Ice | #EAEAEA | Backgrounds neutros |

### 1.3 Shadows
| Token | Light | Dark |
|-------|-------|------|
| `--lia-shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.02)` | `0 1px 2px 0 rgb(0 0 0 / 0.3)` |
| `--lia-shadow-default` | `0 1px 3px 0 rgb(0 0 0 / 0.05)` | `0 1px 3px 0 rgb(0 0 0 / 0.4)` |
| `--lia-shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.05)` | `0 4px 6px -1px rgb(0 0 0 / 0.5)` |
| `--lia-shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.05)` | `0 10px 15px -3px rgb(0 0 0 / 0.6)` |

### 1.4 Border Radius
| Token Tailwind | Valor |
|---------------|-------|
| `rounded-lg` | `var(--radius)` = 0.75rem (12px) |
| `rounded-md` | `calc(var(--radius) - 2px)` ≈ 10px |
| `rounded-sm` | `calc(var(--radius) - 4px)` ≈ 8px |

### 1.5 Transições
| Propriedade | Valor |
|------------|-------|
| Duração global | 200ms |
| Timing | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Background transition | 0.3s ease |

### 1.6 Container / Layout
| Breakpoint | Padding |
|-----------|---------|
| DEFAULT | 1rem |
| sm (640px) | 2rem |
| md (768px) | — |
| lg (1024px) | 4rem |
| xl (1280px) | 5rem |
| 2xl (1536px) | 6rem |

### 1.7 Animações Definidas
| Nome | Tipo | Uso |
|------|------|-----|
| `fadeIn` | translateY(10px) → 0 | Entrada de páginas |
| `slideIn` / `slideInRight` | translateX(30px) → 0 | Painéis laterais |
| `scaleIn` | scale(0.95) → 1 | Modais |
| `slideInFromRight` | translateX(300px) → 0 | Sidebar de candidato |
| `dotsPulse` | scale(1) → 1.5 | Loading dots |
| `shimmer` | background-position | Loading skeleton |
| `fieldHighlightFade` | yellow bg → transparent | Sincronização de campos |
| `fieldPulse` | box-shadow pulse | Destaque de campo |
| `loading-skeleton` | gradient sweep | Skeleton screens |

**Arquivo de referência:** `plataforma-lia/src/styles/design-tokens.css`, `plataforma-lia/src/app/globals.css`, `plataforma-lia/tailwind.config.ts`

---

## 2. BIBLIOTECA DE COMPONENTES BASE (`components/ui/`)

### 2.1 Button
- **Arquivo:** `plataforma-lia/src/components/ui/button.tsx`
- **Exports:** `Button`, `buttonVariants`
- **Primitiva:** Radix `Slot` (via `asChild`)
- **Texto base:** `!text-[11px]`, `font-medium`

| Variante | Background (Light) | Text (Light) | Background (Dark) | Hover |
|----------|-------------------|-------------|-------------------|-------|
| `default` / `primary` | `bg-gray-900` | `text-white` | `bg-gray-50` / `text-gray-900` | `bg-gray-800` |
| `destructive` | `bg-red-600` | `text-white` | `bg-red-600` | `bg-red-700` |
| `outline` | `bg-white` border `gray-300` | `text-gray-800` | `bg-gray-800` border `gray-600` | `bg-gray-50` |
| `secondary` | `bg-gray-100` | `text-gray-950` | `bg-gray-700` / `text-gray-50` | `bg-gray-200` |
| `ghost` | transparent | `text-gray-800` | `text-gray-200` | `bg-gray-100` |
| `link` | transparent | `text-gray-700` underline | `text-gray-300` | underline on hover |

| Tamanho | Classes |
|---------|---------|
| `default` | `h-10 px-4 py-2` |
| `sm` | `h-9 rounded-md px-3` |
| `lg` | `h-11 rounded-md px-8` |
| `icon` | `h-10 w-10` |

**Focus:** `focus-visible:ring-2 focus-visible:ring-gray-900/20`

### 2.2 Badge
- **Arquivo:** `plataforma-lia/src/components/ui/badge.tsx`
- **Exports:** `Badge`, `badgeVariants`
- **Base:** `rounded-full`, `px-2.5 py-0.5`, `text-[11px]`, `font-medium`, border

| Variante | Background | Text | Border |
|----------|-----------|------|--------|
| `default` | `bg-gray-100` | `text-gray-950` | transparent |
| `secondary` | `bg-gray-100` | `text-gray-700` | transparent |
| `destructive` | `bg-red-100` | `text-red-800` | transparent |
| `outline` | transparent | `text-gray-800` | `border-gray-300` |
| `success` | `rgba(123,194,154,0.15)` | `#5aa078` | transparent |
| `warning` | `rgba(232,168,124,0.15)` | `#c58a5e` | transparent |
| `info` | `wedo-cyan/15` | `#50a3b8` | transparent |
| `danger` | `rgba(232,168,124,0.15)` | `#c58a5e` | transparent |
| `lilac` | `rgba(201,160,220,0.15)` | `#a078b0` | transparent |

### 2.3 Card
- **Arquivo:** `plataforma-lia/src/components/ui/card.tsx`
- **Exports:** `Card`, `CardHeader`, `CardFooter`, `CardTitle`, `CardDescription`, `CardContent`
- **Card base:** `rounded-md`, border, `bg-card text-card-foreground`
- **CardHeader:** `flex flex-col space-y-1.5 p-6`
- **CardTitle:** `text-xs font-semibold leading-none tracking-tight`
- **CardDescription:** `text-[11px] text-muted-foreground`
- **CardContent:** `p-6 pt-0`
- **CardFooter:** `flex items-center p-6 pt-0`

### 2.4 Input
- **Arquivo:** `plataforma-lia/src/components/ui/input.tsx`
- **Export:** `Input`
- **Dimensões:** `h-10`, `w-full`, `rounded-md`, `px-3 py-2`
- **Texto:** `text-[11px]`
- **Border:** `border-gray-300` (light) / `border-gray-600` (dark)
- **Background:** `bg-white` / `bg-gray-700` (dark)
- **Placeholder:** `text-gray-600` / `text-gray-400` (dark)
- **Focus:** `focus:border-gray-500 focus:ring-2 focus:ring-gray-900/20`

### 2.5 Textarea
- **Arquivo:** `plataforma-lia/src/components/ui/textarea.tsx`
- **Export:** `Textarea`
- **Min height:** `min-h-[80px]`
- **Texto:** `text-[11px]`
- **Mesmo padrão de border/focus do Input**

### 2.6 Select
- **Arquivo:** `plataforma-lia/src/components/ui/select.tsx`
- **Exports:** `Select`, `SelectGroup`, `SelectValue`, `SelectTrigger`, `SelectContent`, `SelectLabel`, `SelectItem`, `SelectSeparator`, `SelectScrollUpButton`, `SelectScrollDownButton`
- **Primitiva:** Radix Select
- **Trigger:** `h-10`, border `gray-300`, `bg-white`, `text-sm`
- **Ícones:** `ChevronDown` (trigger), `ChevronUp` (scroll), `Check` (selected indicator)
- **Content:** `z-50`, `rounded-md`, border, `bg-white`
- **Item:** `py-1.5 pl-8 pr-2`, `text-sm`, focus: `bg-gray-100`

### 2.7 Checkbox
- **Arquivo:** `plataforma-lia/src/components/ui/checkbox.tsx`
- **Export:** `Checkbox`
- **Primitiva:** Radix Checkbox
- **Dimensões:** `h-4 w-4`, `rounded-sm`
- **Border:** `border-gray-300`
- **Checked:** `bg-gray-900 border-gray-900 text-white` (dark: `bg-gray-50`)
- **Indicator:** `Check` icon (Lucide) `h-3 w-3`

### 2.8 Switch
- **Arquivo:** `plataforma-lia/src/components/ui/switch.tsx`
- **Export:** `Switch`
- **Primitiva:** Radix Switch
- **Track:** `h-5 w-9`, `rounded-full`
- **Checked:** `bg-gray-900` (dark: `bg-gray-50`)
- **Unchecked:** `bg-gray-200` (dark: `bg-gray-700`)
- **Thumb:** `h-4 w-4`, `bg-white`, `rounded-full`, `translate-x-4` when checked

### 2.9 Tabs
- **Arquivo:** `plataforma-lia/src/components/ui/tabs.tsx`
- **Exports:** `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- **Primitiva:** Radix Tabs
- **TabsList:** `h-10`, `rounded-full`, `bg-gray-100 p-1` (dark: `bg-gray-800`)
- **TabsTrigger:** `rounded-full px-3 py-1.5`, `text-sm font-medium`
  - Active: `bg-white text-gray-900` (dark: `bg-gray-950 text-gray-50`)
- **TabsContent:** `mt-2`

### 2.10 Dialog (Modal)
- **Arquivo:** `plataforma-lia/src/components/ui/dialog.tsx`
- **Exports:** `Dialog`, `DialogPortal`, `DialogOverlay`, `DialogClose`, `DialogTrigger`, `DialogContent`, `DraggableDialogContent`, `DialogHeader`, `DialogFooter`, `DialogTitle`, `DialogDescription`
- **Primitiva:** Radix Dialog
- **Overlay:** `bg-black/30 backdrop-blur-[1px]`, z-index `50`
- **Content:** `max-w-lg`, `border-gray-100`, `bg-white`, `p-6`, `rounded-md`, z-index `9999`
- **Close button:** `X` icon (Lucide), `absolute right-4 top-4`, `text-gray-500 hover:text-gray-800`
- **DialogTitle:** `text-xs font-semibold`
- **DialogDescription:** `text-[11px] text-gray-600`
- **DraggableDialogContent:** Mesma aparência + drag handle (h-12 invisível no topo, `cursor-move`)

### 2.11 Sheet (Side Panel)
- **Arquivo:** `plataforma-lia/src/components/ui/sheet.tsx`
- **Exports:** `Sheet`, `SheetPortal`, `SheetOverlay`, `SheetTrigger`, `SheetClose`, `SheetContent`, `SheetHeader`, `SheetFooter`, `SheetTitle`, `SheetDescription`
- **Primitiva:** Radix Dialog (reused)
- **Overlay:** `bg-background/80 backdrop-blur-sm`
- **Side variants:**

| Side | Positioning | Animation |
|------|------------|-----------|
| `top` | `inset-x-0 top-0` | slide from top |
| `bottom` | `inset-x-0 bottom-0` | slide from bottom |
| `left` | `inset-y-0 left-0 w-3/4 sm:max-w-sm` | slide from left |
| `right` (default) | `inset-y-0 right-0 w-3/4 sm:max-w-sm` | slide from right |

- **Close:** `X` icon, `absolute right-4 top-4`
- **Title:** `text-lg font-semibold`

### 2.12 Table
- **Arquivo:** `plataforma-lia/src/components/ui/table.tsx`
- **Exports:** `Table`, `TableHeader`, `TableBody`, `TableFooter`, `TableHead`, `TableRow`, `TableCell`, `TableCaption`
- **Table:** `w-full caption-bottom text-sm`, wrapped in overflow-auto div
- **TableHead:** `h-10 px-2`, `font-medium text-muted-foreground`
- **TableRow:** `border-b`, hover: `bg-muted/50`, selected: `bg-muted`
- **TableCell:** `p-2 align-middle`

### 2.13 Avatar
- **Arquivo:** `plataforma-lia/src/components/ui/avatar.tsx`
- **Exports:** `Avatar`, `AvatarImage`, `AvatarFallback`
- **Primitiva:** Radix Avatar
- **Avatar:** `h-10 w-10`, `rounded-full`, `overflow-hidden`
- **Fallback:** `bg-muted`, `rounded-full`, centered content

### 2.14 Tooltip
- **Arquivo:** `plataforma-lia/src/components/ui/tooltip.tsx`
- **Exports:** `Tooltip`, `TooltipTrigger`, `TooltipContent`, `TooltipProvider`
- **Primitiva:** Radix Tooltip
- **Content:** `z-50`, `rounded-md`, border, `bg-popover`, `px-3 py-1.5`, `text-sm`

### 2.15 DropdownMenu
- **Arquivo:** `plataforma-lia/src/components/ui/dropdown-menu.tsx`
- **Exports:** `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuCheckboxItem`, `DropdownMenuRadioItem`, `DropdownMenuLabel`, `DropdownMenuSeparator`, `DropdownMenuShortcut`, `DropdownMenuGroup`, `DropdownMenuPortal`, `DropdownMenuSub`, `DropdownMenuSubContent`, `DropdownMenuSubTrigger`, `DropdownMenuRadioGroup`
- **Primitiva:** Radix DropdownMenu
- **Content:** `z-50`, `min-w-[8rem]`, `rounded-md`, border, `bg-popover p-1` (dark: `bg-gray-800`)
- **Item:** `px-2 py-1.5`, `text-sm`, focus: `bg-accent`
- **Ícones internos:** `Check` (checkbox indicator), `ChevronRight` (sub trigger), `Circle` (radio indicator)

### 2.16 Progress
- **Arquivo:** `plataforma-lia/src/components/ui/progress.tsx`
- **Export:** `Progress`
- **Primitiva:** Radix Progress
- **Track:** `h-2`, `rounded-full`, `bg-gray-100` (dark: `bg-gray-800`)
- **Indicator:** `bg-gray-900` (dark: `bg-gray-100`), `transition-all 300ms`

### 2.17 Skeleton
- **Arquivo:** `plataforma-lia/src/components/ui/skeleton.tsx`
- **Export:** `Skeleton`
- **Classes:** `animate-pulse rounded-md bg-gray-200` (dark: `bg-gray-700`)

### 2.18 EmptyState
- **Arquivo:** `plataforma-lia/src/components/ui/empty-state.tsx`
- **Export:** `EmptyState`
- **Layout:** `flex flex-col items-center justify-center py-12 px-6 text-center`
- **Ícone:** `text-gray-300` (dark: `text-gray-600`), `w-10 h-10`
- **Título:** `text-sm font-medium text-gray-700`
- **Descrição:** `text-xs text-gray-500 max-w-xs`
- **Ação:** `Button variant="outline" size="sm" rounded-md text-xs`

### 2.19 Loading
- **Arquivo:** `plataforma-lia/src/components/ui/loading.tsx`
- **Exports:** `Loading`, `LoadingCard`, `LoadingList`

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

### 2.20 StatusBadge (Sistema de Status Customizado)
- **Arquivo:** `plataforma-lia/src/components/ui/status-badge.tsx`
- **Exports:** `StatusBadge`, `ChannelBadge`, `SourceBadge`, `WarningBadge`, `DateTimeBadge`, `OriginBadge`, `AwaitingBadge`
- **Font:** Open Sans, 9px
- **Ícone:** 8px (`w-2 h-2`)
- **Padding:** `px-1.5 py-0.5`
- **Border-radius:** `rounded-full`

| Variante | BG (Light) | Text | Icon Color | Font Weight |
|----------|-----------|------|-----------|-------------|
| `standard` | #F9FAFB | #4B5563 | #6B7280 | 500 |
| `dark` | #111827 | #FFFFFF | #FFFFFF | 700 |
| `accent` | Pastel por etapa (dinâmico) | #111827 | #111827 | 600 |
| `outlined` | #F9FAFB | #374151 | #374151 | 400 (+ border #E5E7EB) |
| `channel` | #F3F4F6 | #1F2937 | #1F2937 | 400 (+ border #D1D5DB) |
| `scheduled` | #1F2937 | #FFFFFF | #22D3EE | 600 |
| `hired` | #111827 | #FFFFFF | #10B981 (green) | 700 |
| `rejected` | #F9FAFB | #4B5563 | #6B7280 | 500 (+ border) |

**Cores Pastel por Etapa (accent variant):**
| Etapa | Cor Light | Cor Dark |
|-------|----------|---------|
| sourcing | #DCE4DB | #3D4A3C |
| screening | #E3DADC | #4A3D40 |
| interview_* | #DDE1E9 | #3D414A |
| references / offer | #E5E0E2 | #454043 |
| hired | #EAEAEA | #3A3A3A |
| rejected | #F5F5F5 | #404040 |

**Ícones automáticos por variante:** Clock (accent/waiting), Trophy (hired), XCircle (rejected), CalendarCheck (scheduled), CheckCircle (completed), MessageCircle (in_progress), BrainCircuit (screening), FileText (default)

**Sub-componentes:**
- `ChannelBadge`: Canais (WhatsApp→MessageSquare, Email→Mail, Phone→Phone, LinkedIn→Linkedin, Teams→Video, Presencial→Building)
- `SourceBadge`: Origens (LinkedIn, Indeed, Google Jobs, Website, Referral, Headhunting, Interno, Banco LIA, Manual)
- `WarningBadge`: `bg-gray-100`, `AlertCircle` icon, text `text-[9px] font-semibold`
- `DateTimeBadge`: `Calendar` icon, formato DD/MM HH:MM
- `OriginBadge`: Web (blue), WhatsApp (green), Busca (gray), ATS (purple)
- `AwaitingBadge`: `bg-amber-50`, `Clock` icon, `text-amber-700`

### 2.21 ScoreIconButton
- **Arquivo:** `plataforma-lia/src/components/ui/score-icon-button.tsx`
- **Export:** `ScoreIconButton`
- **Layout:** `flex items-center gap-1`, `rounded-full`
- **Ícone:** `w-3.5 h-3.5`
- **Score text:** `text-[11px] font-bold font-['Open_Sans'] text-gray-700`
- **Ativo:** color `#111827` (LIA scores) / `#374151` (outros)
- **Inativo:** color `#9CA3AF`, `opacity-25`
- **Hover (ativo):** `scale-105`
- **Envolto em:** `TooltipProvider > Tooltip`

### 2.22 CandidateCard
- **Arquivo:** `plataforma-lia/src/components/ui/candidate-card.tsx`
- **Export:** `CandidateCard`
- **Usa:** `Card`, `CardContent`, `Badge`, `Button`
- **Ícones:** MapPin, Building, Mail, Linkedin, ExternalLink, Award, Calendar, ChevronDown, ChevronUp, MessageSquare, Check, AlertCircle, Clock, Send

### 2.23 ContextPill
- **Arquivo:** `plataforma-lia/src/components/ui/context-pill.tsx`
- **Export:** `ContextPill`
- **Layout:** `inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border`
- **BG:** `var(--eleven-bg-card)`
- **Border:** `var(--eleven-border)`
- **Ícone default:** MapPin `w-3.5 h-3.5`
- **Dismiss:** `X` icon, `h-5 w-5`

### 2.24 Accordion
- **Arquivo:** `plataforma-lia/src/components/ui/accordion.tsx`
- **Exports:** `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`
- **Primitiva:** Radix Accordion
- **AccordionItem:** `border-b`
- **AccordionTrigger:** `flex flex-1 items-center justify-between py-4 font-medium`, hover: `underline`
  - Ícone: `ChevronDown` `h-4 w-4`, rotaciona 180° quando `data-state=open`
  - Transição: `transition-transform duration-200`
- **AccordionContent:** `text-sm`, padding `pb-4 pt-0`
  - Animações: `animate-accordion-up` (fechar), `animate-accordion-down` (abrir)
- **States:** open (rotação ícone + conteúdo visível), closed (ícone normal + conteúdo oculto)

### 2.25 AlertDialog
- **Arquivo:** `plataforma-lia/src/components/ui/alert-dialog.tsx`
- **Exports:** `AlertDialog`, `AlertDialogPortal`, `AlertDialogOverlay`, `AlertDialogTrigger`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogFooter`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogAction`, `AlertDialogCancel`
- **Primitiva:** Radix AlertDialog
- **Overlay:** `bg-black/30 backdrop-blur-[1px]`, z-index `50`, fade in/out
- **Content:** `max-w-lg`, `p-6`, `gap-4`, `sm:rounded-md`, z-index `50`, zoom in/out
- **Header:** `flex flex-col space-y-2 text-center sm:text-left`
- **Footer:** `flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2`
- **Title:** `text-lg font-semibold`
- **Description:** `text-sm text-muted-foreground`
- **Action button:** Usa `buttonVariants()` (default/primary style)
- **Cancel button:** Usa `buttonVariants({ variant: "outline" })`, `mt-2 sm:mt-0`
- **States:** open (overlay + content visível), closed (fade out + zoom out)

### 2.26 Collapsible
- **Arquivo:** `plataforma-lia/src/components/ui/collapsible.tsx`
- **Exports:** `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent`
- **Primitiva:** Radix Collapsible (sem customizações de estilo — re-export direto)
- **States:** open (conteúdo visível), closed (conteúdo oculto)

### 2.27 Label
- **Arquivo:** `plataforma-lia/src/components/ui/label.tsx`
- **Export:** `Label`
- **Primitiva:** Radix Label
- **Classe base (CVA):** `text-[11px] font-medium leading-none`
- **Disabled:** `peer-disabled:cursor-not-allowed peer-disabled:opacity-70`

### 2.28 Popover
- **Arquivo:** `plataforma-lia/src/components/ui/popover.tsx`
- **Exports:** `Popover`, `PopoverTrigger`, `PopoverContent`
- **Primitiva:** Radix Popover
- **Content:** `z-50`, `w-72`, `rounded-md`, `p-4`
  - Border: `border-gray-200` (dark: `border-gray-700`)
  - BG: `bg-white` (dark: `bg-gray-800`)
  - Text: `text-gray-950` (dark: `text-gray-50`)
  - Align default: `center`, sideOffset: `4`
- **Animações:** fade in/out + zoom in/out + slide por direção (top/bottom/left/right)
- **States:** open (animado para dentro), closed (animado para fora)

### 2.29 RadioGroup
- **Arquivo:** `plataforma-lia/src/components/ui/radio-group.tsx`
- **Exports:** `RadioGroup`, `RadioGroupItem`
- **Primitiva:** Radix RadioGroup
- **RadioGroup:** `grid gap-2`
- **RadioGroupItem:** `h-4 w-4`, `rounded-full`, `border border-gray-300`
  - Checked: `border-gray-900` (dark: `border-gray-50`)
  - Indicator: `Circle` icon (Lucide) `h-2.5 w-2.5`, `fill-gray-900` (dark: `fill-gray-50`)
  - Focus: `ring-2 ring-gray-900/20`, `ring-offset-2`
  - Disabled: `cursor-not-allowed opacity-50`
- **States:** checked (filled circle + dark border), unchecked (empty + gray border), disabled (opacity 50%)

### 2.30 ScrollArea
- **Arquivo:** `plataforma-lia/src/components/ui/scroll-area.tsx`
- **Exports:** `ScrollArea`, `ScrollBar`
- **Primitiva:** Radix ScrollArea
- **Root:** `relative overflow-hidden`
- **Viewport:** `h-full w-full rounded-[inherit]`
- **ScrollBar (vertical):** `h-full w-2.5 border-l border-l-transparent p-[1px]`
- **ScrollBar (horizontal):** `h-2.5 flex-col border-t border-t-transparent p-[1px]`
- **Thumb:** `rounded-full bg-gray-200 hover:bg-gray-300`

### 2.31 Separator
- **Arquivo:** `plataforma-lia/src/components/ui/separator.tsx`
- **Export:** `Separator`
- **Primitiva:** Radix Separator
- **Cor:** `bg-gray-200`
- **Horizontal:** `h-[1px] w-full`
- **Vertical:** `h-full w-[1px]`
- **Props:** `orientation` (horizontal|vertical), `decorative` (boolean)

### 2.32 Slider
- **Arquivo:** `plataforma-lia/src/components/ui/slider.tsx`
- **Export:** `Slider`
- **Primitiva:** Radix Slider
- **Track:** `h-2`, `rounded-full`, `bg-gray-100` (dark: `bg-gray-800`)
- **Range:** `bg-gray-900` (dark: `bg-gray-100`)
- **Thumb:** `h-5 w-5`, `rounded-full`, `border-2 border-gray-900`, `bg-white`
  - Dark: `border-gray-100`, `bg-gray-950`
  - Cursor: `cursor-grab`, active: `cursor-grabbing`
  - Focus: `ring-2 ring-gray-400 ring-offset-2`
  - Disabled: `pointer-events-none opacity-50`

### 2.33 Toast
- **Arquivo:** `plataforma-lia/src/components/ui/toast.tsx`
- **Exports:** `ToastProvider`, `ToastViewport`, `Toast`, `ToastTitle`, `ToastDescription`, `ToastClose`, `ToastAction`
- **Primitiva:** Radix Toast
- **Viewport:** `fixed top-0 z-[100]`, mobile: top, desktop: `sm:bottom-0 sm:right-0`, max-w: `md:max-w-[420px]`
- **Toast base:** `rounded-md`, border, `p-6 pr-8`, swipe gestures

| Variante | Background | Text | Border |
|----------|-----------|------|--------|
| `default` | `bg-background` | `text-foreground` | border |
| `destructive` | `bg-destructive` | `text-destructive-foreground` | `border-destructive` |
| `success` | `bg-green-50` | `text-green-900` | `border-green-200` |
| `warning` | `bg-yellow-50` | `text-yellow-900` | `border-yellow-200` |
| `info` | `bg-blue-50` | `text-blue-900` | `border-blue-200` |

- **ToastTitle:** `text-sm font-semibold`
- **ToastDescription:** `text-sm opacity-90`
- **ToastClose:** `X` icon `h-4 w-4`, `absolute right-2 top-2`, `opacity-0` → `group-hover:opacity-100`
- **ToastAction:** `h-8 rounded-md px-3 text-sm font-medium`
- **Animações:** slide-in-from-top (mobile), slide-in-from-bottom (desktop), fade-out-80 on close, swipe-to-dismiss
- **States:** open (slide in + fade in), closed (fade out + slide right), swiping (translate-x follows finger)

### 2.34 Toaster
- **Arquivo:** `plataforma-lia/src/components/ui/toaster.tsx`
- **Export:** `Toaster`
- **Usa:** `useToast()` hook, renderiza lista de `Toast` components
- **Layout:** `ToastProvider` → map toasts → `Toast` + `ToastTitle` + `ToastDescription` + action + `ToastClose` → `ToastViewport`
- **Posição global:** Montado no root layout da aplicação

### 2.35 Command (cmdk)
- **Arquivo:** `plataforma-lia/src/components/ui/command.tsx`
- **Exports:** `Command`, `CommandDialog`, `CommandInput`, `CommandList`, `CommandEmpty`, `CommandGroup`, `CommandItem`, `CommandShortcut`, `CommandSeparator`
- **Primitiva:** cmdk (Command Menu)
- **Command:** `flex flex-col overflow-hidden rounded-md bg-popover text-popover-foreground`
- **CommandInput:** `h-11`, `Search` icon (Lucide) `mr-2 h-4 w-4`, `text-sm`, `placeholder:text-muted-foreground`
- **CommandList:** `max-h-[300px] overflow-y-auto overflow-x-hidden`
- **CommandEmpty:** `py-6 text-center text-sm`
- **CommandGroup:** heading `px-2 py-1.5 text-xs font-medium text-muted-foreground`
- **CommandItem:** `px-2 py-1.5 text-sm`, selected: `bg-accent text-accent-foreground`
- **CommandSeparator:** `h-px bg-border`
- **CommandShortcut:** `ml-auto text-xs tracking-widest text-muted-foreground`
- **CommandDialog:** Wrapper using `Dialog` + `DialogContent` (sem close button, `p-0`, shadow-lg)
- **States:** empty (CommandEmpty shown), populated (CommandList), item selected (bg-accent)

### 2.36 Componentes UI Especializados (inventário individual)

#### AudioPlayer (`audio-player.tsx`)
- **Export:** `AudioPlayer`
- **Função:** Player de áudio para ouvir triagens de candidatos
- **Elementos:** Play/Pause button, progress bar, timestamp, volume control
- **States:** idle, playing, paused, loading, error

#### AudioRecordButton (`audio-record-button.tsx`)
- **Export:** `AudioRecordButton`
- **Função:** Gravação de áudio para feedback/notas do recrutador
- **Elementos:** Record button (pulsante quando gravando), timer, stop button
- **States:** idle, recording (pulsante), stopped, processing

#### BigFiveProfile (`big-five-profile.tsx`)
- **Export:** `BigFiveProfile`
- **Função:** Gráfico radar de personalidade Big Five (OCEAN)
- **Dimensões:** Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- **Elementos:** Canvas/SVG radar, labels, scores numéricos
- **States:** data loaded (radar visível), no data (placeholder)

#### BulkSelectionBar (`bulk-selection-bar.tsx`)
- **Export:** `BulkSelectionBar`
- **Função:** Barra flutuante inferior para ações em lote sobre candidatos selecionados
- **Layout:** `fixed bottom-0`, full width, z-index alto
- **Elementos:** Contador de selecionados, botões de ação (Avançar, Rejeitar, Comunicar), botão deselecionar
- **States:** hidden (0 selecionados), visible (≥1 selecionado)

#### ChatStatusIndicators (`chat-status-indicators.tsx`)
- **Export:** `ChatStatusIndicators`
- **Função:** Indicadores visuais do estado do chat da LIA
- **Variantes:** "pensando" (dots pulsantes), "executando" (spinner), "concluído" (check)
- **States:** idle, thinking, executing, completed, error

#### CommandPalette (`command-palette.tsx`)
- **Export:** `CommandPalette`
- **Função:** Paleta de comandos global (atalho Ctrl+K / Cmd+K)
- **Primitiva:** `Command` (cmdk) + `Dialog`
- **Seções:** Navegação, Vagas recentes, Candidatos recentes, Ações
- **States:** closed, open (overlay + input focused), searching (results filtering)

#### DataRequestIndicator (`data-request-indicator.tsx`)
- **Export:** `DataRequestIndicator`
- **Função:** Ícone/badge indicando que dados foram solicitados ao candidato
- **Elementos:** Ícone de status + badge com contador
- **States:** nenhuma solicitação, pendente, parcialmente respondido, completo

#### DateRangePicker (`date-range-picker.tsx`)
- **Export:** `DateRangePicker`
- **Função:** Seletor de intervalo de datas para filtros e relatórios
- **Elementos:** 2 inputs de data, calendário dropdown, presets (Última semana, Último mês, etc.)
- **States:** empty, start date selected, range selected

#### FileUploadButton (`file-upload-button.tsx`)
- **Export:** `FileUploadButton`
- **Função:** Upload de CVs e documentos
- **Elementos:** Button com ícone Upload, drag area, progress indicator
- **States:** idle, dragging over, uploading (progress), completed, error

#### InterviewRating (`interview-rating.tsx`)
- **Export:** `InterviewRating`
- **Função:** Componente de avaliação de entrevista com escala
- **Elementos:** Stars/Score input, textarea para feedback, competências avaliadas
- **States:** empty (não avaliado), partial, completed

#### InterviewSchedulingModal (`interview-scheduling-modal.tsx`)
- **Export:** `InterviewSchedulingModal`
- **Função:** Modal para agendar entrevistas com candidatos
- **Campos:** DatePicker, TimePicker, Select (tipo de entrevista), Select (entrevistadores), Textarea (notas)
- **Botões:** `Button outline` (Cancelar), `Button default` (Agendar)
- **States:** empty form, valid (botão ativo), submitting, success, error

#### LiaExpandedPanel (`lia-expanded-panel.tsx`)
- **Export:** `LiaExpandedPanel`
- **Função:** Painel expandido para interações com a LIA (chat/análise)
- **Layout:** Side panel fullheight, header + content scrollable + input area
- **States:** collapsed, expanded, loading, error

#### LiaIcon (`lia-icon.tsx`)
- **Export:** `LIAIcon`
- **Função:** Ícone customizado da assistente LIA
- **Variações:** Tamanhos (sm/md/lg), com/sem animação (pulsante quando ativa)
- **Cor:** Cyan (#60BED1)

#### PipelineReport (`pipeline-report.tsx`)
- **Export:** `PipelineReport`
- **Função:** Relatório visual do pipeline de recrutamento
- **Elementos:** Funil visual, barras de progresso por etapa, métricas de conversão, timeline
- **States:** loading (skeleton), loaded, empty (sem dados)

#### PipelineStagesCarousel (`pipeline-stages-carousel.tsx`)
- **Export:** `PipelineStagesCarousel`
- **Função:** Carrossel horizontal de etapas do pipeline
- **Elementos:** Cards de etapa lado a lado, setas de navegação, indicador de posição
- **States:** scrollable (setas visíveis), fit-in-view (setas ocultas)

#### PremiumAutocomplete (`premium-autocomplete.tsx`)
- **Export:** `PremiumAutocomplete`
- **Função:** Campo de autocomplete com sugestões de skills/cargos/empresas
- **Elementos:** Input + Popover dropdown com sugestões filtradas, badges de seleção
- **States:** idle, focused (dropdown open), loading suggestions, no results

#### PromptSuggestionsDock (`prompt-suggestions-dock.tsx`)
- **Export:** `PromptSuggestionsDock`
- **Função:** Dock fixo na base com sugestões de prompts para o chat LIA
- **Layout:** Horizontal scroll de chips/cards
- **States:** visible (com sugestões), hidden (após seleção ou chat ativo)

#### PromptSuggestionsPopover (`prompt-suggestions-popover.tsx`)
- **Export:** `PromptSuggestionsPopover`
- **Função:** Popover de sugestões de prompt contextual
- **Layout:** Popover ancorado ao input do chat
- **States:** open (com sugestões), closed

#### QuickActionChips (`quick-action-chips.tsx`)
- **Export:** `QuickActionChips`
- **Função:** Chips de ação rápida para o chat LIA
- **Layout:** Flex wrap de chips clicáveis
- **Elementos:** Badge-like chips com ícones + labels
- **States:** idle, hovered, clicked (ripple/scale feedback)

#### ResizableTableHeader (`resizable-table-header.tsx`)
- **Export:** `ResizableTableHeader`
- **Função:** Cabeçalho de tabela com colunas redimensionáveis
- **Interação:** Drag na borda da coluna para redimensionar
- **States:** idle, resizing (cursor col-resize, highlight na borda)

#### SearchLoadingAnimation (`search-loading-animation.tsx`)
- **Export:** `SearchLoadingAnimation`
- **Função:** Animação de loading durante busca de candidatos
- **Tipo:** Animação customizada (dots + text pulsante)
- **States:** animating (visível durante busca)

#### SetupAlertBadge (`setup-alert-badge.tsx`)
- **Export:** `SetupAlertBadge`
- **Função:** Badge de alerta indicando setup incompleto da vaga
- **Cor:** Amber/warning
- **States:** visible (setup pendente), hidden (setup completo)

#### UnifiedBulkActionsBar (`unified-bulk-actions-bar.tsx`)
- **Export:** `UnifiedBulkActionsBar`
- **Função:** Barra unificada de ações em lote (evolução do BulkSelectionBar)
- **Layout:** `fixed bottom-0`, animação slide-up
- **Ações:** Avançar Etapa, Rejeitar, Enviar Mensagem, Agendar Entrevista, Solicitar Dados
- **Elementos:** Contador (`Badge`), botões de ação (`Button`), X para fechar
- **States:** hidden, visible (slide up), action executing (spinner)

#### VariableSelector (`variable-selector.tsx`)
- **Export:** `VariableSelector`
- **Função:** Seletor de variáveis de template para emails/mensagens
- **Elementos:** Dropdown com categorias (Candidato, Vaga, Empresa), variáveis clicáveis
- **Inserção:** Click insere `{{variavel}}` no textarea
- **States:** closed, open (lista de variáveis)

#### AIDisclaimer (`ai-disclaimer.tsx`)
- **Export:** `AIDisclaimer`
- **Função:** Aviso de que o conteúdo foi gerado/assistido por IA
- **Layout:** Banner inline, `text-xs`, ícone Brain/Sparkles + texto
- **Cor:** Cyan accent background sutil
- **States:** visible (sempre quando conteúdo IA presente)

---

## 3. SIDEBAR (Navegação Principal)

- **Arquivo:** `plataforma-lia/src/components/sidebar.tsx`
- **Componente:** `Sidebar`
- **Layout:** Coluna vertical fixa à esquerda, colapsável
- **Background:** `wedo-surface-elevated`, `border-right: 1px solid wedo-gray-200`
- **Logo:** `Image` (Next.js) no topo
- **Itens do menu:** Font Open Sans, 11px (`0.6875rem`), weight 500

### Menu Principal (3 itens core)
| Ícone (Lucide) | Label | Page ID |
|----------------|-------|---------|
| `LayoutDashboard` | Painel de Controle | `dashboard` |
| `Briefcase` | Vagas | `vagas` |
| `Users` | Funil de Talentos | `candidatos` |

### Filtros de Vagas (sub-menu contextual quando em Vagas)
| Ícone | Label | Valor |
|-------|-------|-------|
| `Filter` | Todas | `todas` |
| `PlayCircle` | Ativas | `ativas` |
| `PauseCircle` | Paralisadas | `paralisadas` |
| `CheckCircle` | Concluídas | `concluidas` |
| `XCircle` | Canceladas | `canceladas` |
| `Target` | Por Estágio | `por-estagio` |

### Itens Adicionais
- **Ícone de busca:** `Search` (abre busca global)
- **Itens recentes:** Lista com ícones por tipo
- **Configurações:** `Settings` icon no rodapé
- **Theme Toggle:** Componente `ThemeToggle`
- **LIA Tips:** Componente `LIATipsModal` (`HelpCircle` icon)
- **Collapse/Expand:** `ChevronLeft` / `ChevronRight`
- **Premium lock:** `Lock` / `Crown` icons para módulos premium

---

## 4. TOPBAR

- **Arquivo:** `plataforma-lia/src/components/top-bar.tsx`
- **Componente:** `TopBar`
- **Layout:** Barra horizontal fixa no topo
- **Background:** `wedo-surface`, `border-bottom: 1px solid wedo-gray-200`

### Elementos
| Elemento | Componente/Ícone | Posição | Detalhes |
|----------|-----------------|---------|---------|
| Notificações | `Bell` (Lucide) → `NotificationSystem` | Direita | Ícone com badge contador |
| Avatar do Usuário | `Avatar` + `AvatarFallback` | Direita | Foto + iniciais fallback |
| Dropdown do Usuário | `DropdownMenu` | Direita | Nome, email, role, empresa |
| Item: Meu Perfil | `User` icon | Dropdown | Navega para perfil |
| Item: Alterar Senha | `KeyRound` icon | Dropdown | Abre `Dialog` de senha |
| Item: Sair | `LogOut` icon | Dropdown | Logout |

### Modal de Alterar Senha
- **Tipo:** `Dialog` + `DialogContent`
- **Campos:** 3x `Input type="password"` (Senha Atual, Nova Senha, Confirmar)
- **Toggle visibilidade:** `Eye` / `EyeOff` icons
- **Validação:** inline error `text-red-500 text-xs`
- **Sucesso:** `Check` icon verde + `text-green-600`
- **Botões:** `Button variant="outline"` (Cancelar) + `Button default` (Alterar)

---

## 5. PAINEL DE CONTROLE (Dashboard)

- **Arquivo:** `plataforma-lia/src/components/pages/tasks-page-mvp.tsx`
- **Componente:** `TasksPageMVP`
- **Descrição:** Tarefas e atividades pendentes do recrutador

---

## 6. VAGAS (Lista)

- **Arquivo:** `plataforma-lia/src/components/pages/jobs-page.tsx`
- **Componente:** `JobsPage`
- **Layout:** Tabela de vagas com header, filtros e ações

### Ícones Lucide Usados (100+)
Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Edit2, Share2, Clock, Layout, Layers3, Layers, ChevronDown, ChevronUp, ChevronLeft, BarChart3, TrendingUp, TrendingDown, FileText, ExternalLink, Briefcase, Building, Building2, Target, CheckCircle, CheckCircle2, XCircle, Linkedin, Globe, Shield, Hash, UserCheck, Heart, MoreHorizontal, Grid3X3, List, Maximize2, Minimize2, Star, Brain, Expand, Copy, MessageSquare, MoreVertical, Settings, Settings2, X, ChevronsLeftRight, Bell, Pin, Github, Mail, Lock, LockOpen, MessageCircle, AlertCircle, AlertTriangle, ShieldAlert, Lightbulb, ChevronRight, Home, Zap, ClipboardList, ListChecks, CalendarCheck, ThumbsUp, Phone, Send, Bookmark, Paperclip, Mic, GripVertical, ArrowUp, ArrowDown, ArrowUpDown, Filter, Award, Trash2, RefreshCw, ArrowRight, ArrowLeft, HelpCircle, Timer, GraduationCap, BookOpen, Scale, Loader2, History, Languages, UserCircle, CalendarDays, Link, Save, Check, RotateCcw, CalendarClock, Info, Archive, Gauge

### Tabela de Vagas
| Coluna | Tipo | Componente |
|--------|------|-----------|
| Título da vaga | Texto + link | — |
| Status | Badge | `Badge` variant (Ativa/Paralisada/etc) |
| Candidatos | Contador | — |
| Prazo | Data | `Calendar` icon + texto |
| Departamento | Texto | — |
| Localização | Texto | `MapPin` icon |
| Ações | Botões | `MoreHorizontal` dropdown |

### Botão Criar Vaga
- `Button` default + `Plus` icon
- Abre `CreateJobModal`

---

## 7. PÁGINA DA VAGA (Kanban)

- **Arquivo:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Componente:** `JobKanbanPage`

### Header da Vaga
| Elemento | Tipo | Detalhes |
|----------|------|---------|
| Título | `text-lg font-semibold` | Nome da vaga |
| Badge Senioridade | `Badge` | Júnior/Pleno/Sênior |
| Badge Modelo | `Badge` | CLT/PJ/Temporário |
| Badge Regime | `Badge` | Presencial/Híbrido/Remoto |
| Badge Departamento | `Badge` | Área/setor |
| Badge Localização | `Badge` + `MapPin` icon | Cidade/Estado |
| Badge Salário | `Badge` + `DollarSign` icon | Faixa salarial |
| Botão Configurar Etapas | `Button outline` + `Settings` icon | — |
| Botão Relatório | `Button outline` + `BarChart3` icon | — |
| Botão Compartilhar | `Button outline` + `Share2` icon | — |

### Tabs Principais
| Tab | Label | Conteúdo |
|-----|-------|---------|
| Tab 1 | Gestão da Vaga (com contador) | Kanban ou Tabela de candidatos |
| Tab 2 | Configurações | ScreeningConfigManager |

### Modo Kanban — Sub-componentes

#### KanbanColumn (`pages/job-kanban/KanbanColumn.tsx`)
- **Export:** `KanbanColumn`
- **Arquivo:** `plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx`
- **Layout:** `flex flex-col w-[300px] min-w-[300px] bg-gray-50 dark:bg-gray-900 rounded-md border`
- **Header:** `flex items-center justify-between p-3 border-b`
  - Indicador de cor: `div w-3 h-3 rounded-full` (cor dinâmica por etapa)
  - Nome: `font-medium text-gray-900`
  - Contador: `Badge variant="outline" text-xs` (`border-gray-300`)
  - Botão adicionar: `Button variant="ghost" size="icon" h-7 w-7` + `Plus h-4 w-4`
  - Botão opções: `Button variant="ghost" size="icon" h-7 w-7` + `MoreVertical h-4 w-4`
- **Área de cards:** `ScrollArea` com lista de `KanbanCard`
- **Empty state:** `EmptyState` component
- **Colunas (16 etapas):** Funil, Triagem, Long List, Short List, Entrevista RH, Teste Técnico, Teste de Inglês, Entrevista Técnica, Entrevista Gestor, Entrevista Gestor 2, Entrevista Final, Referências, Proposta, Contratado, Reprovado, Proposta Recusada
- **States:** empty (EmptyState shown), populated (cards), receiving drag (highlight border)

#### KanbanCard (`pages/job-kanban/KanbanCard.tsx`)
- **Export:** `KanbanCard`
- **Arquivo:** `plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`
- **Layout:** `Card bg-white border border-gray-200 hover:border-gray-300 rounded-md cursor-pointer`
- **Padding:** `CardContent p-3`
- **Elementos:**
  - Drag handle: `GripVertical h-4 w-4 text-gray-400` (opacity-0 → opacity-100 on group-hover)
  - Avatar: `Avatar` + `AvatarFallback` (iniciais uppercase, 2 chars)
  - Nome: `text-sm font-medium` (via design tokens)
  - Score: Cor dinâmica — ≥80 emerald-600, ≥60 amber-600, <60 red-600
  - Badges de status: `StatusBadge` por etapa
  - Ícone star: `Star h-4 w-4` (favorito)
  - Ícone alert: `AlertTriangle` (stale >7 days)
  - Score LIA: `TrendingUp` ícone + valor numérico
  - Days in stage: `Clock` ícone + "Xd"
  - Mensagens: `MessageSquare` ícone + contagem
- **Scores color logic:**
  - ≥80: `text-emerald-600 dark:text-emerald-400` (high)
  - ≥60: `text-amber-600 dark:text-amber-400` (medium)
  - <60: `text-red-600 dark:text-red-400` (low)
  - null/0: `text-gray-400 dark:text-gray-500`
- **States:** normal, hovered (border-gray-300), dragging, stale (>7 days highlight)
- **Tooltips:** Via `TooltipProvider > Tooltip`

#### MoveConfirmationModal (`pages/job-kanban/MoveConfirmationModal.tsx`)
- **Função:** Confirmação ao mover candidato entre etapas via drag & drop
- **Dados:** Nome do candidato, etapa de origem, etapa de destino
- **Botões:** Cancelar + Confirmar
- **States:** open (confirmação), confirming, confirmed

### Modo Tabela
- Mesmos dados em formato tabular com `Table` + `TableHeader` + `TableRow`
- Toggle: `Grid3X3` icon (Kanban) / `List` icon (Tabela)
- Colunas: Checkbox seleção, Nome + Avatar, Cargo, Score, Etapa, Dias na Etapa, Ações

### Preview do Candidato (Sidebar)
- **Tipo:** Side panel (não Sheet — implementação customizada com `slideInFromRight` animation)
- **Largura:** ~400px
- **Tabs:** Resumo, Experiência, Formação, Habilidades, Histórico
- **Header:** Nome, cargo, empresa, `Avatar`, badges de status
- **Ícones de score (ScoreIconButton — 6 botões):**

| ID | Ícone | Label | Cor Ativa | Modal ao Click |
|----|-------|-------|----------|---------------|
| `geral` | Custom | Score Geral | #111827 | `GeneralScoreModal` |
| `triagem` | Custom | Triagem | #111827 | `WSITextScreeningModal` |
| `cv` | Custom | Análise CV | #111827 | `LiaAnalysisModal` |
| `tecnico` | Custom | Teste Técnico | #374151 | `TechnicalTestModal` |
| `ingles` | Custom | Teste de Inglês | #374151 | `EnglishTestModal` |
| `b5` | Custom | Big Five | #374151 | `BigFiveProfile` modal |

- **Botão "Ver perfil completo":** Abre view full do candidato
- **Botões de ação:** `Button` (Avançar Etapa), `Button destructive` (Rejeitar), `Button outline` (Comunicar)
- **States:** loading (skeleton), loaded (dados do candidato), empty (nenhum selecionado), error

### Ações em Lote
- `BulkSelectionBar` / `UnifiedBulkActionsBar`: Barra flutuante fixa no rodapé
- **Trigger:** Aparece quando ≥1 candidato selecionado (checkbox)
- **Ações disponíveis:** Avançar Etapa, Rejeitar, Enviar Mensagem, Agendar Entrevista, Solicitar Dados
- **Elementos:** Badge contador + Button por ação + X fechar
- **States:** hidden (0 selecionados), visible (≥1 com slide-up), action executing

---

## 8. CONFIGURAÇÕES DA VAGA

- **Arquivo:** `plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx`
- **Componente:** `ScreeningConfigManager`
- **Sub-arquivo:** `plataforma-lia/src/components/jobs/JobEditTab.tsx` (`JobEditTab`)

### Sidebar de Navegação (Seções)
| Seção | Descrição |
|-------|-----------|
| Processo Seletivo | Etapas do recrutamento |
| Remuneração | Salário, bônus, benefícios |
| Configurações do Roteiro | Formato e duração da triagem |
| Descricão do Cargo | Informações da vaga para a LIA |
| Perguntas WSI | Configuração de perguntas da entrevista |
| Critérios de Elegibilidade | Filtros de elegibilidade |
| Ações Afirmativas | Critérios de diversidade |
| Confidencialidade | Configurações de privacidade |

### Seção "Descrição do Cargo"
| Elemento | Tipo | Detalhes |
|----------|------|---------|
| Descrição/Sumário | `Textarea` | Campo livre |
| Responsabilidades | Lista editável | Items com `X` para remover, `Plus` para adicionar |
| Competências Técnicas | Lista + botão "Sugerir com IA" | `Brain` icon no botão |
| Competências Comportamentais | Lista + botão "Sugerir com IA" | `Brain` icon no botão |
| Botão "Gerar Descrição" | `Button` primary | Chama endpoint de IA |

### Painel JD Enriquecida (JDEvaluationPanel)
- **Arquivo:** `plataforma-lia/src/components/wsi/JDEvaluationPanel.tsx`
- **Componente:** `JDEvaluationPanel`
- **Título:** "DESCRIÇÃO ENRIQUECIDA (LIA)"
- **Dimensões avaliadas:** D1-D9 com scores individuais
- **Indicadores:** Barras de progresso + scores numéricos
- **Botão:** "Salvar Versão Definitiva"
- **Status:** Badges de qualidade (Excelente ≥90, Bom 70-89, Adequado 50-69, etc.)

---

## 9. FUNIL DE TALENTOS

- **Arquivo:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Componente:** `CandidatesPage`

### Sub-componentes Extraídos

#### CandidatesHeader (`pages/candidates/CandidatesHeader.tsx`)
- **Export:** `CandidatesHeader`
- **Layout:** `flex items-center justify-between border-b px-6 py-4 bg-white dark:bg-gray-900`
- **Elementos:**
  - Ícone: `Users h-5 w-5 text-gray-600`
  - Título: `text-lg font-semibold text-gray-900`
  - Contador total: `Badge variant="outline" border-gray-300` ("X candidatos")
  - Contador selecionados: `Badge bg-gray-100 text-gray-700 border border-gray-200` ("X selecionados") — visível quando selectedCount > 0
  - Botão Filtros: `Button variant="ghost" size="sm"` + `Filter h-4 w-4` — toggle ativo/inativo
  - Botão Adicionar: `Button size="sm" bg-gray-900 hover:bg-gray-800 text-white` + `Plus h-4 w-4`
- **States:** no selection (counter hidden), with selection (counter visible + bulk bar)

#### CandidateTabs (`pages/candidates/CandidateTabs.tsx`)
- **Export:** `CandidateTabs`
- **Layout:** `border-b border-gray-200`, `nav -mb-px flex items-center space-x-6`
- **Tab ativa:** `border-gray-950 text-gray-950 border-b-2`
- **Tab inativa:** `border-transparent text-gray-800 hover:text-gray-950 hover:border-gray-300`
- **Badge "Em Breve":** `rounded-full text-[11px] font-medium` — `bg rgba(96,190,209,0.15) color #0369A1`

| Tab ID | Label | Disponível |
|--------|-------|-----------|
| search | Busca | Sim |
| favorites | Favoritos | Sim |
| lists | Listas | Sim |
| saved-searches | Buscas Salvas | Sim |
| history | Histórico | Sim |
| coming-soon-tab | (futuras) | Em Breve |

#### CandidateSearchBar (`pages/candidates/CandidateSearchBar.tsx`)
- **Export:** `CandidateSearchBar`
- **Lazy-loaded:** `SmartSearchInput`, `SearchLoadingAnimation`
- **Ícones:** `Brain`, `FileUp`, `Loader2`
- **Layout:** Zona de busca inteligente com drag-and-drop de CV
- **Elementos:**
  - `SmartSearchInput`: Input principal de busca semântica
  - Indicador de filtros ativos: Badge com contagem
  - Source switcher: Troca entre fonte interna/externa
  - Opções Pearch: `requireEmails`, `requirePhoneNumbers`
  - CV drop zone: Área de drag-and-drop para upload de CV
- **States:** idle (campo vazio), searching (loading animation), cv-dropping (highlight zone), cv-parsing (loader)

#### CandidatesFilterPanel (`pages/candidates/CandidatesFilterPanel.tsx`)
- **Export:** `CandidatesFilterPanel`
- **Arquivo:** 1125 linhas — painel lateral completo
- **Layout:** Painel lateral collapsível
- **Componentes usados:** `Badge`, `Input`, `Switch`, `RadioGroup`, `RadioGroupItem`
- **Ícones:** X, ArrowUpDown, Zap, Star, Briefcase, MapPin, DollarSign, Crown, Bookmark, CheckCircle, Calendar, FileText, Code, Check, Brain, Github, Globe, Building, Layers

| Categoria de Filtro | Tipo de Controle | Campos |
|-------------------|-----------------|--------|
| Status | `Checkbox` lista | Ativo, Passivo, etc. |
| Tags | `Badge` clicável | Tags customizadas |
| Senioridade | `Checkbox` lista | Júnior, Pleno, Sênior, Especialista |
| Modelo de Trabalho | `Checkbox` lista | Presencial, Híbrido, Remoto |
| Tipo de Contrato | `Checkbox` lista | CLT, PJ, Freelancer, Estágio |
| Experiência | `Input` range | min/max anos |
| Score | `Input` range | min/max score |
| Salário | `Input` range | min/max |
| Localização | `Checkbox` lista | Cidades/Estados |
| Remoto Only | `Switch` | Toggle |
| Contato | `Switch` x3 | hasEmail, hasPhone, hasLinkedin |
| Fontes | `Checkbox` lista | LinkedIn, Indeed, etc. |
| Cargos | `Checkbox` lista | Cargos filtrados |
| Skills | `Checkbox` lista | Skills filtradas |
| Empresas | `Checkbox` lista | Empresas anteriores |
| Indústrias | `Checkbox` lista | Setores |
| Universidades | `Checkbox` lista | Instituições |
| Graus | `Checkbox` lista | Graduação, Mestrado, etc. |
| Idiomas | `Checkbox` lista | Inglês, Espanhol, etc. |
| Especiais | `Switch` x5 | isOpenToWork, isDecisionMaker, isTopUniversities, isStartup, hasGithub |

- **States:** collapsed (hidden), expanded (visible), filters active (badge count), cleared

#### CandidatesTable (`pages/candidates/CandidatesTable.tsx`)
- **Export:** `CandidatesTable`
- **Componentes usados:** `Avatar`, `Badge`, `Button`, `Checkbox`, `Tooltip`
- **Ícones:** Eye, Mail, Phone, Linkedin, Star, MapPin, Building, Briefcase, ArrowUpDown, ArrowUp, ArrowDown, Clock

| Coluna | Componente | Sorting | Detalhes |
|--------|-----------|---------|---------|
| Seleção | `Checkbox` | — | Select all / individual |
| Candidato | `Avatar` + nome + cargo | Sim (ArrowUpDown) | `AvatarFallback` com iniciais |
| Empresa | Texto | Sim | `Building` icon |
| Localização | Texto | Sim | `MapPin` icon |
| Score | Badge numérico | Sim | Cor por faixa (5-band) |
| Última atividade | Texto relativo | Sim | "Agora", "Xmin", "Xh", "Xd", "Xsem" |
| Ações | Botões | — | `Eye` (ver), `Mail` (email), `Phone` (telefone) |

- **Feedback de busca:** `SearchFeedbackButtons` por candidato (like/dislike)
- **Loading state:** `SkeletonRow` com `animate-pulse` — avatar circle, text bars
- **Empty state:** Mensagem centralizada
- **Date formatting:** Relative ("Agora", "5min atrás", "2h atrás", "3d atrás", "1sem atrás")

#### SearchResultsHeader (`pages/candidates/SearchResultsHeader.tsx`)
- **Export:** `SearchResultsHeader`
- **Função:** Header contextual exibido acima dos resultados de busca
- **Elementos:** Contagem de resultados, query executada, tempo de busca, botões de ação

---

## 10. MODAIS (detalhamento campo a campo)

### 10.1 CreateJobModal
- **Arquivo:** `plataforma-lia/src/components/modals/create-job-modal.tsx`
- **Componente:** `CreateJobModal`
- **Container:** Não usa `Dialog` — implementação customizada com overlay + panel fixo
- **Max-width:** Full-screen lado direito (slide-in)

| Campo | Componente | Placeholder/Opções | Obrigatório |
|-------|-----------|-------------------|-------------|
| Título da Vaga | `Input` | "Ex: Engenheiro de Software Senior" | Sim |
| Departamento | `Select` | Opções dinâmicas | Sim |
| Localização | `Input` | — | Não |
| Modelo de Trabalho | `Select` | Presencial/Híbrido/Remoto | Sim |
| Tipo de Contrato | `Select` | CLT/PJ/Freelancer/Estágio | Sim |
| Senioridade | `Select` | Júnior/Pleno/Sênior/Especialista | Sim |
| Gestor | `Input` | "Nome do gestor" | Não |
| Email do Gestor | `Input` | "gestor@empresa.com" | Não |

- **Validação:** Inline, `text-red-500 text-xs`
- **Botões:** Cancelar (`X` button top-right) + Criar Vaga (`Button default`)
- **States:** empty form, validação inline (erros), submitting (loading), success (fecha + toast)

### 10.2 EditJobModal
- **Arquivo:** `plataforma-lia/src/components/modals/edit-job-modal.tsx`
- **Componente:** `EditJobModal`
- **Container:** Panel slide-in (similar ao CreateJobModal)

| Campo | Componente | Placeholder/Opções | Obrigatório |
|-------|-----------|-------------------|-------------|
| Título da Vaga | `Input` | "Ex: Desenvolvedor Full Stack" | Sim |
| Departamento | `Select` ou `Input` | "Selecione" ou "Ex: Tecnologia" | Sim |
| Localização | `Input` | "Ex: São Paulo, SP" | Não |
| Modelo de Trabalho | `Select` | Presencial/Híbrido/Remoto | Sim |
| Tipo de Contrato | `Select` | CLT/PJ/Temporário/Estágio | Sim |
| Senioridade | `Select` | Júnior/Pleno/Sênior/Especialista | Sim |
| Recrutador | `Input` | "Nome do recrutador" | Não |

- **Labels:** `text-[11px] font-medium text-gray-800`
- **SelectTrigger:** custom style via `selectTriggerStyle`
- **Botão salvar:** `Button default` no rodapé
- **States:** loaded (pré-preenchido), dirty (campos alterados), saving, saved

### 10.3 JobDuplicateModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-duplicate-modal.tsx`
- **Componente:** `JobDuplicateModal`
- **Container:** `Dialog` + `DialogContent max-w-2xl`
- **Header:** `DialogTitle text-[14px] font-semibold`, `DialogHeader border-b`

| Campo | Componente | Placeholder/Opções |
|-------|-----------|-------------------|
| Copiar Candidatos | `RadioGroup` | Todos / Apenas aprovados / Nenhum |
| Nome da nova vaga | `Input` | "Nome da nova vaga" |
| Recrutador Responsável | `Select` | Lista de recrutadores |
| Prazo Inicial | `Input type="date"` | — |
| Prazo Final | `Input type="date"` | — |
| Número de Vagas | `Input type="number"` | — |

- **Labels:** `text-[11px] text-gray-800`
- **Footer:** `DialogFooter border-t gap-2`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Duplicar)
- **States:** form loaded, submitting, success

### 10.4 JobPublishModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-publish-modal.tsx`
- **Componente:** `JobPublishModal`
- **Container:** `Dialog` + `DialogContent max-w-2xl`
- **Header:** `DialogTitle text-[14px] font-semibold`, border-b

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Agendamento | `RadioGroup` | Publicar agora / Agendar (com `Input type="date"` + `Input type="time"`) |
| Congelar vaga | `Checkbox` + `Label text-[11px]` | Se marcado, mostra motivo (`Input`) + data prevista (`Input`) |
| Notificar candidatos | `Checkbox` + `Label text-[11px]` | — |
| Aviso WSI | `Checkbox` + `Label text-[10px] text-amber-900` | Confirmação de triagem configurada |
| Busca automática interna | `Checkbox` + `Label text-[11px]` | — |
| Busca automática global | `Checkbox` + `Label text-[11px]` | Com `Crown` icon (premium) |

- **Footer:** `DialogFooter border-t gap-2`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Publicar / Agendar)
- **States:** form initial, scheduling mode, freeze mode, submitting, published

### 10.5 JobUnpublishModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-unpublish-modal.tsx`
- **Componente:** `JobUnpublishModal`
- **Container:** `Dialog` + `DialogContent`
- **Layout:** Confirmação simples com texto explicativo
- **Botões:** `Button outline` (Cancelar) + `Button destructive` (Despublicar)
- **States:** open, confirming, success

### 10.6 JobStatusModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-status-modal.tsx`
- **Componente:** `JobStatusModal`
- **Container:** `Dialog` + `DialogContent`

| Campo (Pausar) | Componente | Descrição |
|-------|-----------|-----------|
| Motivo | `Select text-[11px]` | "Selecione um motivo..." |
| Observações | `Textarea text-[11px]` | "Digite o motivo para pausar..." |
| Cancelar triagens | `Checkbox` + `Label text-[11px]` | — |
| Cancelar entrevistas | `Checkbox` + `Label text-[11px]` | — |
| Cancelar testes | `Checkbox` + `Label text-[11px]` | — |
| Notificar recrutadores | `Checkbox` + `Label text-[11px]` | Com sub-opção de canal (botões Email/WhatsApp) |
| Notificar candidatos | `Checkbox` + `Label text-[11px]` | — |

| Campo (Reativar) | Componente | Descrição |
|-------|-----------|-----------|
| Retomar triagem | `Checkbox` + `Label text-[11px]` | — |
| Republicar | `Checkbox` + `Label text-[11px]` | — |
| Atualizar prazos | `Checkbox` + `Label text-[11px]` | — |

- **Badges:** `Badge variant="outline" text-[10px] bg-white border-red-200 text-red-700` (candidatos impactados)
- **Botões:** `Button outline` (Cancelar) + `Button default` (Pausar/Reativar)
- **States:** pause mode, activate mode, submitting, success

### 10.7 CloseVacancyModal
- **Arquivo:** `plataforma-lia/src/components/modals/close-vacancy-modal.tsx`
- **Componente:** `CloseVacancyModal`
- **Container:** `Dialog` + `DialogContent max-w-lg rounded-md`
- **Header:** `DialogTitle text-[14px] font-semibold`, `DialogDescription text-xs`

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Candidato contratado | `Badge success` | Indicação visual |
| Template de comunicação | `Select` | "Selecione um template..." |
| Candidatos reprovados (lista) | `Checkbox` por candidato | Seleção para notificação |
| Template de rejeição | `Select` | "Selecione um template..." |

- **Footer:** `DialogFooter border-t bg-gray-50`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Encerrar Vaga)
- **States:** loaded (com dados dos candidatos), notifying, closed

### 10.8 JobCompareModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-compare-modal.tsx`
- **Componente:** `JobCompareModal`
- **Container:** `Dialog` + `DialogContent` (large, ~80% viewport)
- **Header:** `DialogTitle text-[14px] font-semibold`

- **Layout:** Grid de comparação lado a lado (2 ou mais vagas)
- **Dados comparados:** Título, Status, Departamento, Localização, Salário, Senioridade, Candidatos, Pipeline, Métricas WSI
- **Interações:** `Checkbox` para selecionar vagas, `Button outline` para exportar
- **Footer:** `DialogFooter border-t`
- **Botões:** `Button outline` (Fechar)
- **States:** loading, loaded (tabela comparativa), empty (sem vagas selecionadas)

### 10.9 JobInsightsModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-insights-modal.tsx`
- **Componente:** `JobInsightsModal`
- **Container:** `Dialog` + `DialogContent` (large, scrollable)
- **Header:** `DialogTitle text-[14px] font-semibold`

- **Dados exibidos:** WSI Scores (F1-F11), Conversion rates por etapa, Stage bottlenecks, Demographics, Behavioral competencies, LIA metrics, Insight categories
- **Elementos visuais:** Progress bars, Score badges (5-band), Charts, KPI cards
- **Footer:** `DialogFooter border-t`
- **Botões:** `Button outline` (Fechar) + `Button default` (Exportar)
- **States:** loading (skeleton cards), loaded (métricas visíveis), no data

### 10.10 JobAssignRecruiterModal
- **Arquivo:** `plataforma-lia/src/components/modals/job-assign-recruiter-modal.tsx`
- **Componente:** `JobAssignRecruiterModal`
- **Container:** `Dialog` + `DialogContent`
- **Campos:** Lista de recrutadores (`Select` ou lista clicável), busca (`Input`)
- **Botões:** `Button outline` (Cancelar) + `Button default` (Atribuir)
- **States:** loaded, searching, selected, submitting

### 10.11 AddCandidateModal
- **Arquivo:** `plataforma-lia/src/components/modals/add-candidate-modal.tsx`
- **Componente:** `AddCandidateModal`
- **Container:** `Dialog` + `DialogContent max-w-4xl max-h-[85vh] overflow-hidden flex flex-col`

| Campo | Componente | Placeholder | Obrigatório |
|-------|-----------|-------------|-------------|
| Nome Completo | `Input` | "João Silva" | Sim (*) |
| E-mail | `Input` | "joao.silva@email.com" | Sim (*) |
| Telefone | `Input` | "(11) 99999-9999" | Sim (*) |
| Localização | `Input` | "São Paulo, SP" | Não |
| Modelo de Trabalho | `Select` | Presencial/Híbrido/Remoto | Não |
| Tipo de Contrato | `Select` | CLT/PJ/Freelancer/Estágio | Não |
| Sobre o Candidato | `Textarea` | "Breve descrição..." | Não |
| Cargo Desejado | `Input` | — | Sim (*) |

- **Labels:** `Label htmlFor="..."` padrão
- **Validação:** Inline em cada campo
- **Botões:** `Button outline` (Cancelar) + `Button default` (Adicionar)
- **States:** empty form, filling, validation errors, submitting, success

### 10.12 NewCandidateUnifiedModal
- **Arquivo:** `plataforma-lia/src/components/modals/new-candidate-unified-modal.tsx`
- **Componente:** `NewCandidateUnifiedModal`
- **Container:** `Dialog` + `DialogContent` (large)
- **Tabs de entrada:** `cv` | `linkedin` | `manual`

| Tab CV | Componente | Descrição |
|--------|-----------|-----------|
| Colar CV | `Textarea` | "Cole aqui o conteúdo do currículo..." |
| Parse CV | `Button` | Extrai dados automaticamente |

| Tab LinkedIn | Componente | Descrição |
|--------|-----------|-----------|
| URL do LinkedIn | `Input text-xs` | "https://linkedin.com/in/nome-do-usuario" |
| Importar | `Button` | Busca perfil |

| Tab Manual | Componente | Descrição |
|--------|-----------|-----------|
| Nome Completo | `Input text-xs` | "João Silva" (*) |
| E-mail | `Input text-xs` | "joao.silva@email.com" |
| Telefone | `Input text-xs` | "(11) 99999-9999" |
| LinkedIn | `Input text-xs` | "linkedin.com/in/joao-silva" |

- **Botões footer:** `Button outline` (Cancelar) + `Button default` (Adicionar)
- **States:** tab selection, form filling, cv parsing (loading), parsed (preview), submitting, success

### 10.13 CandidateCompareModal
- **Arquivo:** `plataforma-lia/src/components/modals/candidate-compare-modal.tsx`
- **Componente:** `CandidateCompareModal`
- **Container:** `Dialog` + `DialogContent max-w-2xl`
- **Header:** `DialogTitle text-sm font-semibold` com ícone
- **Layout:** Grid de comparação lado a lado (2 candidatos)
- **Dados:** Nome, Cargo, Empresa, Skills, Scores (LIA, CV, Triagem, Técnico, Inglês, B5)
- **States:** loading, loaded, empty (sem candidatos para comparar)

### 10.14 AddToJobModal
- **Arquivo:** `plataforma-lia/src/components/modals/add-to-job-modal.tsx`
- **Componente:** `AddToJobModal`
- **Container:** Panel customizado (slide-in, não Dialog)

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Buscar vaga | `Input` | "Buscar vaga..." |
| Lista de vagas | Lista clicável | Com `Label` por vaga |
| Etapa inicial | `Select text-[11px]` | "Selecione a etapa" (lista de stages) |
| Iniciar triagem | `Checkbox` + `Label` | — |
| Notificar recrutador | `Checkbox` + `Label` | — |

- **Botões:** `Button outline` (Cancelar) + `Button default` (Vincular)
- **States:** searching, vaga selected, stage selected, submitting

### 10.15 AddToListModal
- **Arquivo:** `plataforma-lia/src/components/modals/add-to-list-modal.tsx`
- **Componente:** `AddToListModal`
- **Container:** `Dialog` + `DialogContent max-w-md`
- **Header:** `DialogTitle` com ícone, `DialogDescription`

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Selecionar lista | `Label` + lista de `Checkbox` | Listas existentes |
| Criar nova lista | `Button` + `Input` | "Ex: Candidatos Finalistas" |
| Nome da lista (nova) | `Input text-[11px]` | placeholder |

- **Footer:** `DialogFooter border-t bg-gray-50`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Adicionar)
- **States:** loaded (listas existentes), creating new list, submitting

### 10.16 AddCandidatesToVacancyModal
- **Arquivo:** `plataforma-lia/src/components/modals/add-candidates-to-vacancy-modal.tsx`
- **Componente:** `AddCandidatesToVacancyModal`
- **Container:** Panel customizado

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Buscar vagas | `Input` | "Buscar vagas por título, departamento ou local..." |
| Filtro rápido | `Button` | Ativas/Todas |
| Lista de vagas | Lista selecionável | Listbox com role="listbox" |

- **Botões:** `Button outline` (Cancelar) + `Button default` (Vincular X candidatos)
- **States:** searching, results shown, vaga selected, submitting

### 10.17 AddListToVacanciesModal
- **Arquivo:** `plataforma-lia/src/components/modals/add-list-to-vacancies-modal.tsx`
- **Componente:** `AddListToVacanciesModal`
- **Container:** `Dialog` + `DialogContent max-w-lg`
- **Header:** `DialogTitle text-lg`, `DialogDescription text-[11px]`

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Buscar vagas | `Input` | "Buscar vagas por título, departamento ou local..." |
| Lista de vagas | `Checkbox` por vaga | Multi-seleção |

- **Footer:** `DialogFooter border-t bg-gray-50`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Vincular)
- **States:** loaded, searching, selected, submitting

### 10.18 CreateJobWithCandidatesModal
- **Arquivo:** `plataforma-lia/src/components/modals/create-job-with-candidates-modal.tsx`
- **Componente:** `CreateJobWithCandidatesModal`
- **Container:** Panel customizado (dark theme: `bg-gray-800`)

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Etapa inicial | `Select bg-gray-800 border-gray-700 text-[11px]` | Lista de stages |
| Iniciar triagem | `Checkbox` + `Label` | — |

- **Labels:** `text-[11px] font-medium text-gray-300`
- **Botões:** `Button outline` (Cancelar) + `Button default` (Criar Vaga)
- **States:** form filling, submitting, success

### 10.19 LiaAnalysisModal
- **Arquivo:** `plataforma-lia/src/components/modals/lia-analysis-modal.tsx`
- **Componente:** `LiaAnalysisModal`
- **Container:** Dialog/Panel largo
- **Dados:** Análise detalhada da LIA (scores, recomendações, insights)
- **Botões:** `Button outline` (Fechar) + `Button default` (Exportar) + `Button` (Recalcular)
- **States:** loading (skeleton), loaded (análise completa), error, recalculating

### 10.20 GeneralScoreModal
- **Arquivo:** `plataforma-lia/src/components/modals/general-score-modal.tsx`
- **Componente:** `GeneralScoreModal`
- **Container:** Dialog
- **Dados:** Score geral do candidato, breakdown por dimensão, radar chart
- **Botões:** `Button` (Fechar)
- **States:** loading, loaded (scores visíveis), no data

### 10.21 InsufficientDataModal
- **Arquivo:** `plataforma-lia/src/components/modals/insufficient-data-modal.tsx`
- **Componente:** `InsufficientDataModal`
- **Container:** Dialog
- **Layout:** Ícone de alerta + mensagem + ações sugeridas
- **Botões:** `Button outline` (Fechar) + `Button default` (Solicitar Dados)
- **States:** open (alerta visível)

### 10.22 UnifiedCommunicationModal
- **Arquivo:** `plataforma-lia/src/components/modals/unified-communication-modal.tsx`
- **Componente:** `UnifiedCommunicationModal`
- **Container:** Dialog largo

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Canal | 3 botões aria-label | "Enviar por Email" / "WhatsApp" / "Email e WhatsApp" |
| Template | `Select` | Seleção de template de mensagem |
| Assunto (email) | `Input` | — |
| Corpo da mensagem | `Textarea` | Editor com variáveis |
| Agendar envio | `Switch` | Toggle |
| Configurações avançadas | `Switch` | Expandir opções |

- **Badges:** `Badge variant="outline"` (status dos candidatos)
- **Botões:** `Button outline` (Cancelar) + `Button default` (Enviar)
- **States:** channel selected, template loaded, editing, scheduling, sending, sent

### 10.23 StageTransitionActionsModal
- **Arquivo:** `plataforma-lia/src/components/modals/stage-transition-actions-modal.tsx`
- **Componente:** `StageTransitionActionsModal`
- **Container:** Dialog

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Badges do candidato | `Badge` (múltiplos) | Stage atual, pipeline badges |
| Template de mensagem | `Select text-xs` | "Selecionar template..." |
| Assunto (email) | `Input` | "Assunto do email" |
| Mensagem | `Textarea` | "Escreva sua mensagem..." |

- **Botões:** `Button outline` (Cancelar) + `Button default` (Confirmar Transição)
- **States:** loaded (info do candidato), template selected, editing message, confirming, success

### 10.24 BulkActionModal
- **Arquivo:** `plataforma-lia/src/components/modals/bulk-action-modal.tsx`
- **Componente:** `BulkActionModal`
- **Container:** `Dialog` + `DialogContent max-w-lg max-h-[90vh] overflow-y-auto`
- **Header:** `DialogTitle text-[14px] font-semibold`, `DialogDescription text-xs`

| Campo (Avançar) | Componente | Descrição |
|-------|-----------|-----------|
| Ação selecionada | `Label text-[11px]` + `Badge secondary` | Contador de candidatos |
| Etapa de Destino | `Select` + `SelectTrigger` | "Selecione a etapa" |

| Campo (Rejeitar) | Componente | Descrição |
|-------|-----------|-----------|
| Motivo | `Select` | "Selecione o motivo" |
| Observações | `Textarea` | "Adicione observações sobre a reprovação..." |

- **Footer:** `DialogFooter border-t bg-gray-50`
- **Botões:** `Button outline h-9 px-4 text-xs` (Cancelar) + `Button h-9 px-4 text-xs bg-gray-900` (Executar)
- **Progress:** Barra de progresso durante execução
- **States:** action selection, configuring, executing (progress bar), completed (summary), error

### 10.25 DataRequestModal
- **Arquivo:** `plataforma-lia/src/components/modals/data-request-modal.tsx`
- **Componente:** `DataRequestModal`
- **Container:** `Dialog` + `DialogContent max-w-lg max-h-[90vh] overflow-y-auto rounded-md`
- **Header:** `DialogTitle text-[14px] font-semibold`, `DialogDescription text-xs`

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Template | `Select h-9` | "Selecione um template" |
| Campos a solicitar | Lista de `Checkbox` | Multi-seleção de campos de dados |
| Adicionar campo | `Button` | Adicionar campo customizado |
| Canal de envio | `Select h-9` | Email / WhatsApp / Ambos |
| Prazo de expiração | `Select h-9` | 3/5/7/14/30 dias |
| Mensagem personalizada | `Input/Textarea` | (opcional) |

- **Labels:** `text-[11px] font-medium text-gray-800 dark:text-gray-200`
- **Footer:** `DialogFooter border-t bg-gray-50`
- **Botões:** `Button outline h-9 px-4 text-xs` (Cancelar) + `Button h-9 px-4 text-xs` (Enviar Solicitação)
- **States:** form filling, template loaded (auto-preenche campos), submitting, sent

### 10.26 DataBlockingModal
- **Arquivo:** `plataforma-lia/src/components/modals/data-blocking-modal.tsx`
- **Componente:** `DataBlockingModal`
- **Container:** `Dialog` + `DialogContent`
- **Layout:** Lista de campos pendentes que bloqueiam o avanço do candidato
- **Elementos:** Lista de `PendingField` com ícones de status
- **Botões:** `Button outline` (Fechar) + `Button default` (Solicitar Dados Faltantes)
- **States:** loaded (campos pendentes listados), requesting

### 10.27 TechnicalTestModal
- **Arquivo:** `plataforma-lia/src/components/modals/technical-test-modal.tsx`
- **Componente:** `TechnicalTestModal`
- **Container:** Dialog
- **Dados:** Resultado do teste técnico (score, respostas, análise LIA)
- **Botões:** `Button` (Fechar)
- **States:** loading, loaded (resultado visível), no test taken

### 10.28 EnglishTestModal
- **Arquivo:** `plataforma-lia/src/components/modals/english-test-modal.tsx`
- **Componente:** `EnglishTestModal`
- **Container:** Dialog
- **Dados:** Resultado do teste de inglês (score, nível CEFR, análise)
- **Botões:** `Button` (Fechar)
- **States:** loading, loaded, no test taken

### 10.29 ScreeningMediaModal
- **Arquivo:** `plataforma-lia/src/components/modals/screening-media-modal.tsx`
- **Componente:** `ScreeningMediaModal`
- **Container:** Dialog
- **Dados:** Mídia da triagem (áudio/texto da entrevista)
- **Elementos:** `AudioPlayer` (se áudio), texto da conversa (se texto)
- **States:** loading, audio loaded, text loaded, error

### 10.30 ShareSearchModal
- **Arquivo:** `plataforma-lia/src/components/modals/share-search-modal.tsx`
- **Componente:** `ShareSearchModal`
- **Container:** `Dialog` + `DialogContent`
- **Header:** `DialogTitle`, `DialogDescription`

| Campo | Componente | Descrição |
|-------|-----------|-----------|
| Canal de envio | `Label` + seletor | Email/WhatsApp/Link |
| Email do gestor | `Input` | "Email do gestor" |
| Telefone | `Input` | "Telefone (opcional)" |
| Adicionar destinatário | `Button` | — |
| Template | `Select` | Seleção de template |

- **Botões:** `Button outline` (Cancelar) + `Button default` (Compartilhar)
- **States:** filling, recipients added, sending, sent

### 10.31 SharedSearchDetailsModal
- **Arquivo:** `plataforma-lia/src/components/modals/shared-search-details-modal.tsx`
- **Componente:** `SharedSearchDetailsModal`
- **Container:** `Dialog` + `DialogContent` (dark theme)
- **Header:** `DialogTitle text-base font-semibold text-white`
- **Layout:** Detalhes da busca compartilhada + lista de candidatos
- **Elementos:** `Checkbox` (seleção de candidatos), `Button` (ações)
- **States:** loaded, selecting candidates, actioning

### 10.32 UnsavedSearchWarningModal
- **Arquivo:** `plataforma-lia/src/components/modals/unsaved-pearch-warning-modal.tsx`
- **Componente:** `UnsavedPearchWarningModal`
- **Container:** Dialog simples
- **Layout:** Alerta de busca não salva com candidatos não adicionados
- **Dados:** Lista de `UnsavedCandidate` com contagem
- **Botões:** `Button outline` (Descartar) + `Button default` (Salvar e Sair)
- **States:** open (alerta visível)

### 10.33 PersonaCreationModal
- **Arquivo:** `plataforma-lia/src/components/modals/persona-creation-modal.tsx`
- **Componente:** `PersonaCreationModal`
- **Container:** Dialog multi-step
- **Multi-step wizard:** `step` state variable

| Campo (Step 1) | Componente | Descrição |
|-------|-----------|-----------|
| Título da Persona | `Input` | "Ex: Desenvolvedor Frontend Sênior" |
| Descrição | `Textarea` | "Descreva o perfil ideal..." |
| Skills obrigatórias | `Input` + `Badge` lista | Adicionar/remover skills |
| Skills preferenciais | `Input` + `Badge outline` lista | Adicionar/remover |
| Experiência mínima | `Input` | Anos |
| Salário mínimo | `Input` | Valor |
| Salário máximo | `Input` | Valor |
| Localização | `Input` | — |

| Elemento (Step 2 - Preview) | Componente | Descrição |
|-------|-----------|-----------|
| Skills badge | `Badge bg-gray-50 text-wedo-cyan-dark` | Lista visual |
| Score match | `Badge bg-green-100 text-green-700` | Indicador |

- **Botões:** `Button variant="outline"` (Voltar/Cancelar) + `Button` (Próximo/Criar)
- **States:** step 1 (form), step 2 (preview), creating, created

### 10.34 Modais de Screening/WSI

#### ScreeningChannelsModal (`screening-config/ScreeningChannelsModal.tsx`)
- **Função:** Configurar canais de triagem (WhatsApp, Email, Telefone, Presencial)
- **Campos:** `Switch` por canal, configurações específicas por canal
- **States:** loaded (toggles), saving

#### ScreeningSchedulingModal (`screening-config/ScreeningSchedulingModal.tsx`)
- **Função:** Configurar agendamento de triagem
- **Campos:** Janelas de horário, dias da semana, duração, timezone
- **States:** loaded, editing, saving

#### ScreeningSettingsModal (`screening-config/ScreeningSettingsModal.tsx`)
- **Função:** Configurações gerais da triagem WSI
- **Campos:** Modo (Compact/Full), temperatura, idioma, timeout
- **States:** loaded, editing, saving

#### ScreeningStatusModal (`screening-config/ScreeningStatusModal.tsx`)
- **Função:** Visualizar status das triagens em andamento
- **Dados:** Lista de candidatos com status (Agendada/Em andamento/Concluída/Cancelada)
- **States:** loading, loaded (lista), empty

#### WSITextScreeningModal (`wsi/wsi-text-screening-modal.tsx`)
- **Função:** Modal de triagem por texto com perguntas WSI
- **Dados:** Transcrição da conversa, scores por dimensão
- **States:** loading, loaded (transcrição), no screening

#### WSITriagemInviteModal (`wsi/wsi-triagem-invite-modal.tsx`)
- **Função:** Convite para triagem WSI
- **Campos:** Canal (email/WhatsApp), mensagem personalizada, agendamento
- **Botões:** `Button outline` (Cancelar) + `Button default` (Enviar Convite)
- **States:** configuring, sending, sent

---

## 11. CONFIGURAÇÕES (Settings)

- **Arquivo:** `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`
- **Componente:** `SettingsPageEnhanced`

### Seções de Configuração

| Seção | Componente de Conteúdo | Ícones |
|-------|----------------------|--------|
| Empresa | `CompanyDataSection` → `CompanyDataCard`, `CompanyTeamHub` | Building, Users |
| Recrutamento | `RecruitmentHub` → `RecruitmentJourneyConfig`, `HiringPoliciesHub` | Briefcase, Target |
| Comunicação | `CommunicationHub` | MessageSquare, Mail |
| Planejamento | `GoalsPlanningHub` → `goals-management.tsx` | Calendar, Target |
| Busca Global | `GlobalSearchHub` | Search, Globe |
| Painel de Indicadores | `progress-dashboard.tsx` | BarChart3, Gauge |

### Componentes de Settings

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| ApprovalsHub | `settings/ApprovalsHub.tsx` | Gestão de aprovações |
| BenefitsTab | `settings/BenefitsTab.tsx` | Tabela de benefícios |
| BigFiveRadar | `settings/BigFiveRadar.tsx` | Gráfico radar Big Five |
| CompanyDataCard | `settings/CompanyDataCard.tsx` | Card de dados da empresa |
| CompanyDataSection | `settings/CompanyDataSection.tsx` | Seção completa dados empresa |
| CompanyTeamHub | `settings/CompanyTeamHub.tsx` | Gestão de equipe |
| CultureAnalyzer | `settings/CultureAnalyzer.tsx` | Análise de cultura |
| CultureProfilePreview | `settings/CultureProfilePreview.tsx` | Preview do perfil cultural |
| DataRequestTab | `settings/DataRequestTab.tsx` | Configuração de solicitação de dados |
| GlobalSearchHub | `settings/GlobalSearchHub.tsx` | Configurações de busca |
| GoalsPlanningHub | `settings/GoalsPlanningHub.tsx` | Planejamento de metas |
| HiringPoliciesHub | `settings/HiringPoliciesHub.tsx` | Políticas de contratação |
| LiaFieldToggle | `settings/LiaFieldToggle.tsx` | Toggle de campos LIA (Switch) |
| LiaInstructionPopover | `settings/LiaInstructionPopover.tsx` | Popover de instrução LIA |
| RecruitmentHub | `settings/RecruitmentHub.tsx` | Hub de recrutamento |
| RecruitmentJourneyConfig | `settings/RecruitmentJourneyConfig.tsx` | Configuração de jornada |
| SmartImportZone | `settings/SmartImportZone.tsx` | Zona de importação inteligente |
| StageCard | `settings/StageCard.tsx` | Card de etapa do pipeline |
| UserManagement | `settings/user-management.tsx` | Gestão de usuários |
| ValidationSystem | `settings/validation-system.tsx` | Sistema de validações |

---

## 12. COMPONENTES TRANSVERSAIS

### 12.1 Chat LIA
- **Arquivo:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Componente:** `ChatPage`
- **CSS:** `plataforma-lia/src/components/pages/chat-page.css`
- **Indicadores:** `ChatStatusIndicators` (pensando, executando, concluído)
- **Sugestões:** `PromptSuggestionsDock`, `PromptSuggestionsPopover`
- **Ações rápidas:** `QuickActionChips`

### 12.2 Busca Global
- **Componente:** `CommandPalette` (`components/ui/command-palette.tsx`)
- **Atalho:** Ctrl+K / Cmd+K
- **Primitiva:** cmdk
- **Também:** `LiaSearchQueriesGuide`, `LiaVacancyQueriesGuide`, `CandidateQueriesGuide`

### 12.3 Sistema de Notificações
- **Componente:** `NotificationSystem` (`components/notification-system.tsx`)
- **Ícone trigger:** `Bell` (Lucide) na TopBar
- **Toast:** Componente `Toaster` + `Toast` (Radix)

### 12.4 AI Disclaimer
- **Componente:** `AIDisclaimer` (`components/ui/ai-disclaimer.tsx`)
- **Uso:** Aviso em conteúdos gerados por IA

### 12.5 Theme Toggle
- **Componente:** `ThemeToggle` (`components/theme-toggle.tsx`)
- **Posição:** Na sidebar, rodapé
- **Ação:** Alterna entre light/dark mode (class strategy)

---

## 13. PÁGINAS ADICIONAIS

| Página | Arquivo | Componente |
|--------|---------|-----------|
| Dashboards | `pages/dashboards-page.tsx` | `DashboardsPage` |
| Indicadores | `pages/indicators-page.tsx` | `IndicatorsPage` |
| Executive Dashboard | `pages/executive-dashboard-page.tsx` | `ExecutiveDashboardPage` |
| Real-time Dashboard | `pages/real-time-dashboard-page.tsx` | `RealTimeDashboardPage` |
| Big Five Dashboard | `pages/big-five-dashboard-page.tsx` | `BigFiveDashboardPage` |
| LIA Library | `pages/lia-library-page.tsx` | `LiaLibraryPage` |
| Templates | `pages/templates-page.tsx` | `TemplatesPage` |
| Integrações | `pages/integrations-page.tsx` | `IntegrationsPage` |
| ATS Integrations | `pages/ats-integrations-page.tsx` | `ATSIntegrationsPage` |
| AI Credits | `pages/ai-credits-page.tsx` | `AICreditsPage` |
| Workflow Automation | `pages/workflow-automation-page.tsx` | `WorkflowAutomationPage` |
| Job Templates | `pages/job-templates-page.tsx` | `JobTemplatesPage` |
| Work Model Analytics | `pages/work-model-analytics-page.tsx` | `WorkModelAnalyticsPage` |
| Onboarding | `pages/onboarding-page.tsx` | `OnboardingPage` |
| Onboarding Premium | `pages/onboarding-premium-page.tsx` | `OnboardingPremiumPage` |
| Login | `pages/login-page.tsx` | `LoginPage` |

---

## 14. CLASSES CSS UTILITÁRIAS CUSTOMIZADAS

### Cards
| Classe | Background | Shadow | Border |
|--------|-----------|--------|--------|
| `.lia-card` | #FFFFFF | `0 1px 3px rgba(0,0,0,0.04)` | none |
| `.lia-card-elevated` | #FFFFFF | `0 4px 12px rgba(0,0,0,0.06)` | none |
| `.lia-card-hover` | #FFFFFF | hover: `0 4px 16px rgba(0,0,0,0.08)` | none |
| `.wedo-card` | `bg-white` | `0 1px 2px rgba(0,0,0,0.02)` | `1px solid wedo-gray-200` |
| `.wedo-card-elevated` | `bg-white` | `0 2px 8px rgba(0,0,0,0.04)` | `1px solid wedo-gray-200` |

### Botões CSS
| Classe | Background | Text | Hover |
|--------|-----------|------|-------|
| `.lia-btn-primary` | #60BED1 (cyan) | #FFFFFF | #4FA8BA |
| `.lia-btn-secondary` | #F3F4F6 | #1F2937 | #E5E7EB |
| `.lia-btn-ghost` | transparent | #4B5563 | #F9FAFB |
| `.wedo-button-primary` | `hsl(--ai-aqua)` | white | translateY(-1px) |
| `.wedo-button-secondary` | `bg-gray-50` | `text-gray-700` | `bg-gray-100` |
| `.wedo-button-ghost` | transparent | `text-gray-600` | `bg-gray-50` |

### Badges CSS
| Classe | Background | Text |
|--------|-----------|------|
| `.lia-badge` | — | 12px, weight 500, `rounded-[6px]` |
| `.lia-badge-jobs` | `rgba(96,190,209,0.12)` | #0E7490 |
| `.lia-badge-candidates` | `rgba(93,164,122,0.12)` | #166534 |
| `.lia-badge-interviews` | `rgba(229,168,83,0.12)` | #92400E |
| `.lia-badge-reports` | `rgba(139,92,246,0.12)` | #6D28D9 |
| `.lia-badge-neutral` | #F3F4F6 | #4B5563 |

### Inputs CSS
| Classe | Background | Border | Focus |
|--------|-----------|--------|-------|
| `.lia-input` | #F9FAFB | `1px solid #E5E7EB` | border: #60BED1, shadow: `0 0 0 3px rgba(96,190,209,0.1)` |

### Hover Effects
| Classe | Efeito |
|--------|--------|
| `.hover-lift` | `translateY(-2px)` + shadow |
| `.hover-glow` | `box-shadow: 0 0 20px rgba(96,190,209,0.3)` |
| `.hover-border` | `border-color: ai-aqua/0.5` |
| `.micro-bounce` | active: `scale(0.95)` |
| `.micro-scale` | hover: `scale(1.02)` |

### Surfaces
| Classe | Descrição |
|--------|-----------|
| `.wedo-surface` | `bg: wedo-surface`, `border: wedo-gray-200` |
| `.wedo-surface-elevated` | `.wedo-surface` + shadow |
| `.wedo-sidebar` | `.wedo-surface-elevated` + `border-right` |
| `.wedo-topbar` | `.wedo-surface` + `border-bottom` |
| `.wedo-divider` | `border-bottom: wedo-gray-200` + subtle shadow |

---

## 15. RESUMO DE ÍCONES POR ÁREA

| Área | Ícones Lucide mais usados |
|------|--------------------------|
| Sidebar | LayoutDashboard, Briefcase, Users, Settings, Search, Filter, PlayCircle, PauseCircle, CheckCircle, XCircle, Target, ChevronLeft/Right, Lock, Crown, HelpCircle |
| TopBar | Bell, User, KeyRound, LogOut, Eye, EyeOff, Check, X |
| Jobs Page | Search, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Share2, Clock, BarChart3, FileText, Briefcase, Building, Target, CheckCircle, XCircle, MoreHorizontal, Star, Brain, Settings |
| Kanban | GripVertical, ArrowUp/Down, Filter, Award, Trash2, RefreshCw, MessageSquare, Send, Phone, Mic, Paperclip, Bookmark |
| StatusBadge | Clock, CheckCircle, XCircle, Trophy, CalendarCheck, MessageCircle, BrainCircuit, FileText, Star, AlertCircle, Users, User, Linkedin, Globe, Mail, Phone, Video, Building, Briefcase, Search, Target |
| Screening | Brain, Lightbulb, Zap, ClipboardList, ListChecks, Scale, Loader2 |
| Comunicação | MessageSquare, Mail, Phone, Send, Paperclip, MessageCircle |

---

## 16. MATRIZ DE ESTADOS POR TELA

### 16.1 Vagas (Lista)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Loading | Skeleton rows (animate-pulse) | `Skeleton` rows |
| Empty (sem vagas) | `EmptyState` centralizado | Ícone `Briefcase`, "Nenhuma vaga encontrada" |
| Loaded | Tabela com dados | `Table` + `TableRow` por vaga |
| Filtered (sem resultados) | `EmptyState` com filtro ativo | Mensagem de filtro |
| Error (API fail) | Toast destructive | `Toast variant="destructive"` |

### 16.2 Kanban (Gestão da Vaga)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Loading | Skeleton columns | `LoadingCard` x N |
| Empty column | `EmptyState` na coluna | "Nenhum candidato nesta etapa" |
| Populated | Cards nas colunas | `KanbanCard` por candidato |
| Dragging | Card elevado + shadow | Cursor `grabbing`, border highlight |
| Drop target | Border highlight na coluna | `border-cyan-300` (destino válido) |
| Candidate preview | Side panel slide-in | `slideInFromRight` animation |
| Bulk selection | Bottom bar visible | `UnifiedBulkActionsBar` slide-up |
| Error | Toast | `Toast variant="destructive"` |

### 16.3 Funil de Talentos
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Initial (busca vazia) | Search bar + sugestões | `CandidateSearchBar` + `PromptSuggestionsDock` |
| Searching | Animação de loading | `SearchLoadingAnimation` |
| Results loaded | Tabela de candidatos | `CandidatesTable` com resultados |
| No results | `EmptyState` | "Nenhum candidato encontrado" + sugestões |
| CV dropping | Drop zone highlight | Border dashed cyan |
| CV parsing | Loader centralizado | `Loader2 animate-spin` |
| Filters open | Panel lateral visível | `CandidatesFilterPanel` slide-in |
| Bulk selection | Bottom bar visible | `UnifiedBulkActionsBar` |
| Error (search) | Toast | `Toast variant="destructive"` |

### 16.4 Configurações da Vaga
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Loading | Skeleton sections | `LoadingCard` por seção |
| Loaded | Formulários preenchidos | Sections com dados |
| Editing | Campos ativos | Border focus ring |
| Saving | Spinner no botão | `Loader2 animate-spin` |
| Saved | Toast success | `Toast variant="success"` |
| Validation error | Inline red text | `text-red-500 text-xs` |
| JD enriching | Painel loading | `JDEvaluationPanel` com skeleton |
| JD enriched | Painel com scores | Barras de progresso D1-D9 |
| Skills suggesting | Button loading | `Brain` icon + `Loader2` |

### 16.5 Modais (padrão geral)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Closed | Invisível | — |
| Opening | Overlay fade-in + content zoom-in | `bg-black/30 backdrop-blur-[1px]`, `scaleIn` |
| Open (idle) | Formulário visível | `DialogContent` |
| Submitting | Botão com loader, campos disabled | `Loader2` no botão, `disabled:opacity-50` |
| Success | Toast + modal fecha | `Toast variant="success"` |
| Error | Inline error ou toast | `text-red-500` ou `Toast variant="destructive"` |
| Closing | Content zoom-out + overlay fade-out | Reverse animations |

### 16.6 Sidebar
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Expanded | Full width (~240px) | Labels visíveis |
| Collapsed | Icon-only (~48px) | Tooltips nos ícones |
| Item active | Background highlight + left border | `bg-gray-100` + `border-l-2 border-gray-900` |
| Item hover | Background subtle | `hover:bg-gray-50` |
| Item locked | Opacity + lock icon | `Lock` icon, `opacity-60` |
| Sub-menu open | Expandido com items filhos | `ChevronDown/Up` toggle |

### 16.7 TopBar
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Default | Avatar + Bell | — |
| Notifications open | Panel dropdown | `NotificationSystem` |
| Has notifications | Badge counter vermelho | — |
| User menu open | `DropdownMenu` | Lista de ações |
| Password modal open | `Dialog` | 3 inputs + validação |

---

**Arquivos-chave de referência:**
- Design tokens: `plataforma-lia/src/styles/design-tokens.css`
- CSS global: `plataforma-lia/src/app/globals.css`
- Tailwind config: `plataforma-lia/tailwind.config.ts`
- Componentes UI: `plataforma-lia/src/components/ui/*.tsx`
- Páginas: `plataforma-lia/src/components/pages/*.tsx`
- Modais: `plataforma-lia/src/components/modals/*.tsx`
- Settings: `plataforma-lia/src/components/settings/*.tsx`
- Screening: `plataforma-lia/src/components/screening-config/*.tsx`
- WSI: `plataforma-lia/src/components/wsi/*.tsx`
- Kanban sub-componentes: `plataforma-lia/src/components/pages/job-kanban/*.tsx`
- Candidatos sub-componentes: `plataforma-lia/src/components/pages/candidates/*.tsx`
