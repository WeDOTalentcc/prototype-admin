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

### 2.24 Demais Componentes UI (primitivas Radix)

| Componente | Arquivo | Primitiva | Exports |
|-----------|---------|-----------|---------|
| Accordion | `accordion.tsx` | Radix Accordion | `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent` |
| AlertDialog | `alert-dialog.tsx` | Radix AlertDialog | `AlertDialog`, `AlertDialogAction`, `AlertDialogCancel`, etc. |
| Collapsible | `collapsible.tsx` | Radix Collapsible | `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent` |
| Command | `command.tsx` | cmdk | `Command`, `CommandInput`, `CommandList`, `CommandItem`, etc. |
| Label | `label.tsx` | Radix Label | `Label` |
| Popover | `popover.tsx` | Radix Popover | `Popover`, `PopoverTrigger`, `PopoverContent` |
| RadioGroup | `radio-group.tsx` | Radix RadioGroup | `RadioGroup`, `RadioGroupItem` |
| ScrollArea | `scroll-area.tsx` | Radix ScrollArea | `ScrollArea`, `ScrollBar` |
| Separator | `separator.tsx` | Radix Separator | `Separator` |
| Slider | `slider.tsx` | Radix Slider | `Slider` |
| Toast | `toast.tsx` | Radix Toast | `Toast`, `ToastAction`, `ToastClose`, `ToastTitle`, etc. |
| Toaster | `toaster.tsx` | — | `Toaster` |

### 2.25 Componentes UI Especializados

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| AudioPlayer | `audio-player.tsx` | Player de áudio para triagens |
| AudioRecordButton | `audio-record-button.tsx` | Botão de gravação de áudio |
| BigFiveProfile | `big-five-profile.tsx` | Gráfico radar Big Five |
| BulkSelectionBar | `bulk-selection-bar.tsx` | Barra flutuante para ações em lote |
| ChatStatusIndicators | `chat-status-indicators.tsx` | Indicadores "pensando", "executando" |
| CommandPalette | `command-palette.tsx` | Paleta de comandos global (Ctrl+K) |
| DataRequestIndicator | `data-request-indicator.tsx` | Indicador de dados pendentes |
| DateRangePicker | `date-range-picker.tsx` | Seletor de intervalo de datas |
| FileUploadButton | `file-upload-button.tsx` | Upload de arquivos |
| InterviewRating | `interview-rating.tsx` | Avaliação de entrevista |
| InterviewSchedulingModal | `interview-scheduling-modal.tsx` | Modal de agendamento |
| LiaExpandedPanel | `lia-expanded-panel.tsx` | Painel expandido da LIA |
| LiaIcon | `lia-icon.tsx` | Ícone customizado da LIA |
| PipelineReport | `pipeline-report.tsx` | Relatório visual do pipeline |
| PipelineStagesCarousel | `pipeline-stages-carousel.tsx` | Carrossel de etapas |
| PremiumAutocomplete | `premium-autocomplete.tsx` | Autocomplete premium |
| PromptSuggestionsDock | `prompt-suggestions-dock.tsx` | Dock de sugestões de prompt |
| PromptSuggestionsPopover | `prompt-suggestions-popover.tsx` | Popover de sugestões |
| QuickActionChips | `quick-action-chips.tsx` | Chips de ação rápida |
| ResizableTableHeader | `resizable-table-header.tsx` | Cabeçalho redimensionável |
| SearchLoadingAnimation | `search-loading-animation.tsx` | Animação de busca |
| SetupAlertBadge | `setup-alert-badge.tsx` | Badge de alerta de setup |
| UnifiedBulkActionsBar | `unified-bulk-actions-bar.tsx` | Barra de ações em lote unificada |
| VariableSelector | `variable-selector.tsx` | Seletor de variáveis de template |
| AIDisclaimer | `ai-disclaimer.tsx` | Aviso de conteúdo IA |

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

### Modo Kanban
- **Colunas (Pipeline - 16 etapas):** Funil, Triagem, Long List, Short List, Entrevista RH, Teste Técnico, Teste de Inglês, Entrevista Técnica, Entrevista Gestor, Entrevista Gestor 2, Entrevista Final, Referências, Proposta, Contratado, Reprovado, Proposta Recusada
- **Card de Candidato:** Avatar, nome, cargo atual, badges de status (StatusBadge), ícones de score (ScoreIconButton)
- **Drag & Drop:** Cards arrastáveis entre colunas

### Modo Tabela
- Mesmos dados em formato tabular
- Toggle: `Grid3X3` (Kanban) / `List` (Tabela)

### Preview do Candidato (Sidebar)
- **Tipo:** Side panel (não Sheet — implementação customizada)
- **Tabs:** Resumo, Experiência, Formação, Habilidades, Histórico
- **Ícones de score (ScoreIconButton):**
  - Geral (overall score)
  - Triagem (screening score)
  - CV (rubrica de CV)
  - Técnico (teste técnico)
  - Inglês (teste de inglês)
  - B5 (Big Five personality)
- **Botão "Ver perfil completo":** Abre tela full do candidato
- **Botões de ação:** Avançar, Rejeitar, Comunicar

### Ações em Lote
- `BulkSelectionBar` / `UnifiedBulkActionsBar`: Barra flutuante no rodapé
- Ações: Rejeitar, Avançar Etapa, Enviar Mensagem

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

### Tabs de Busca (6 tipos)
| Tab | Descrição |
|-----|-----------|
| Busca Semântica | Busca por texto natural |
| Busca Booleana | Operadores AND/OR/NOT |
| Busca por Localização | Filtro geográfico |
| Busca por Habilidades | Filtro por skills |
| Busca por Experiência | Filtro por anos/tipo |
| Busca Combinada | Múltiplos filtros simultâneos |

### Campo de Busca
- **Ícone:** `Search` (Lucide)
- **Input:** Texto livre
- **Badges de filtro rápido:** Chips clicáveis para filtros comuns

### Cards de Resultado
- `CandidateCard` component
- Avatar + nome + cargo + empresa + localização
- Badges de habilidades
- Score de match

### Abas auxiliares
| Tab | Descrição |
|-----|-----------|
| Favoritos | `Star` / `Bookmark` icon |
| Listas | Listas salvas de candidatos |
| Buscas Salvas | Queries salvas |
| Histórico | Buscas recentes |

---

## 10. MODAIS

### 10.1 Modais de Vagas

| Modal | Arquivo | Campos/Elementos Principais |
|-------|---------|---------------------------|
| `CreateJobModal` | `modals/create-job-modal.tsx` | Título, departamento, senioridade, modelo, regime, localização, salário, descrição — `Input`, `Select`, `Textarea`, `Button` |
| `EditJobModal` | `modals/edit-job-modal.tsx` | Mesmos campos em modo edição |
| `JobDuplicateModal` | `modals/job-duplicate-modal.tsx` | Confirmação + opções de duplicação |
| `JobInsightsModal` | `modals/job-insights-modal.tsx` | Dashboard de métricas da vaga — gráficos, KPIs |
| `JobPublishModal` | `modals/job-publish-modal.tsx` | Configurações de publicação em job boards |
| `JobUnpublishModal` | `modals/job-unpublish-modal.tsx` | Confirmação de remoção |
| `JobStatusModal` | `modals/job-status-modal.tsx` | Mudança de status (Ativa/Paralisada/etc) |
| `CloseVacancyModal` | `modals/close-vacancy-modal.tsx` | Motivo do encerramento |
| `JobCompareModal` | `modals/job-compare-modal.tsx` | Comparação lado a lado |
| `JobAssignRecruiterModal` | `modals/job-assign-recruiter-modal.tsx` | Seleção de recrutador |

### 10.2 Modais de Candidatos

| Modal | Arquivo | Campos/Elementos Principais |
|-------|---------|---------------------------|
| `AddCandidateModal` | `modals/add-candidate-modal.tsx` | Nome, email, telefone, LinkedIn, CV upload |
| `NewCandidateUnifiedModal` | `modals/new-candidate-unified-modal.tsx` | Fluxo unificado de adição |
| `CandidateCompareModal` | `modals/candidate-compare-modal.tsx` | Comparação lado a lado de candidatos |
| `AddToJobModal` | `modals/add-to-job-modal.tsx` | Seleção de vaga para vincular candidato |
| `AddToListModal` | `modals/add-to-list-modal.tsx` | Adicionar a lista de candidatos |
| `AddCandidatesToVacancyModal` | `modals/add-candidates-to-vacancy-modal.tsx` | Multi-seleção de candidatos |
| `AddListToVacanciesModal` | `modals/add-list-to-vacancies-modal.tsx` | Vincular lista a vagas |
| `CreateJobWithCandidatesModal` | `modals/create-job-with-candidates-modal.tsx` | Criar vaga já com candidatos |

### 10.3 Modais de Avaliação/IA

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `LiaAnalysisModal` | `modals/lia-analysis-modal.tsx` | Análise detalhada da LIA |
| `GeneralScoreModal` | `modals/general-score-modal.tsx` | Score geral do candidato |
| `InsufficientDataModal` | `modals/insufficient-data-modal.tsx` | Alerta de dados insuficientes |

### 10.4 Modais de Comunicação

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `UnifiedCommunicationModal` | `modals/unified-communication-modal.tsx` | Email + WhatsApp unificado |
| `StageTransitionActionsModal` | `modals/stage-transition-actions-modal.tsx` | Ações ao mover candidato |
| `BulkActionModal` | `modals/bulk-action-modal.tsx` | Ações em lote |

### 10.5 Modais de Dados e Testes

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `DataRequestModal` | `modals/data-request-modal.tsx` | Solicitar dados do candidato |
| `DataBlockingModal` | `modals/data-blocking-modal.tsx` | Bloquear avanço por dados pendentes |
| `TechnicalTestModal` | `modals/technical-test-modal.tsx` | Configuração de teste técnico |
| `EnglishTestModal` | `modals/english-test-modal.tsx` | Configuração de teste de inglês |
| `ScreeningMediaModal` | `modals/screening-media-modal.tsx` | Mídia de triagem |

### 10.6 Modais de Busca/Compartilhamento

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `ShareSearchModal` | `modals/share-search-modal.tsx` | Compartilhar busca |
| `SharedSearchDetailsModal` | `modals/shared-search-details-modal.tsx` | Detalhes de busca compartilhada |
| `UnsavedSearchWarningModal` | `modals/unsaved-pearch-warning-modal.tsx` | Alerta de busca não salva |

### 10.7 Modais de Persona/Screening

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `PersonaCreationModal` | `modals/persona-creation-modal.tsx` | Criação de persona candidato |
| `ScreeningChannelsModal` | `screening-config/ScreeningChannelsModal.tsx` | Configuração de canais |
| `ScreeningSchedulingModal` | `screening-config/ScreeningSchedulingModal.tsx` | Agendamento de triagem |
| `ScreeningSettingsModal` | `screening-config/ScreeningSettingsModal.tsx` | Configurações de triagem |
| `ScreeningStatusModal` | `screening-config/ScreeningStatusModal.tsx` | Status da triagem |

### 10.8 Modais WSI

| Modal | Arquivo | Descrição |
|-------|---------|-----------|
| `WSITextScreeningModal` | `wsi/wsi-text-screening-modal.tsx` | Triagem por texto WSI |
| `WSITriagemInviteModal` | `wsi/wsi-triagem-invite-modal.tsx` | Convite para triagem WSI |

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
