# Inventário Completo de Design — Plataforma LIA (WeDOTalent)

> Documento de referência para revisão de design. Snapshot dos elementos visuais da área operacional.

| Meta | Valor |
|------|-------|
| Última validação | Abril 2026 |
| Metodologia | Extração automatizada de arquivos-fonte (`components/ui/`, `components/modals/`, `components/pages/`, `design-tokens.css`, `tailwind.config.ts`) + revisão manual + auditoria de diretório completa |
| Componentes UI base (`ui/`) | 68 arquivos `.tsx` (stories removidos) |
| Modais (`modals/`) | 34 arquivos principais + sub-diretórios (edit-job, edit-job-sections, new-candidate, job-compare, job-insights, job-status) |
| Modais dispersos (fora de `modals/`) | ~20 (batch-approval, big-five, candidate-decision-flow, column-configuration, cv-upload, disc-assessment, expanded-chat, global-search, job-report, lia-tips, quick-actions-modals, quick-view, reveal-credits, save-command, task-modal, triagem-details, alert-settings, etc.) |
| Componentes root (`components/*.tsx`) | 71 arquivos `.tsx` diretamente em `components/` |
| Componentes especializados (fora de `ui/`) | 53 subdiretórios em `components/` |
| Hooks (`hooks/`) | 102 hook files root + subdiretórios (admin/, settings/, __tests__/) |
| Lib/Utils (`lib/`) | 28 arquivos + subdiretórios (api/, schemas/, sidebar/, transforms/, utils/) |
| Pages root (`pages/*.tsx`) | 25 arquivos de página |
| Pages sub-componentes | 8 subdiretórios: candidates/ (81), job-kanban/ (56), jobs/ (30), chat-page/ (18), dashboards-page/ (12), indicators/ (10), ats-integrations/ (5), tasks/ (2) |
| Settings | 40 arquivos root + 5 subdiretórios (benefits/, communication-hub/, company/, goals/, recruitment/) |
| Telas operacionais | Dashboard/Tasks, Vagas (lista + kanban + configurações), Funil de Talentos, Candidato Full (review + preview + page), Chat LIA, Settings, Sidebar, TopBar, Admin Panel |
| Telas adicionais | Dashboards (12 sub-dashboards), Indicadores, Executive/Real-Time/Big Five Dashboards, LIA Library, Templates, Integrations/ATS, AI Credits, Workflow Automation, Job Templates, Work Model Analytics, Onboarding, Login |
| Gaps conhecidos | Detalhamento interno de: Onboarding wizard steps, Real-Time Dashboard widgets, Work Model Analytics charts |
| Unificações T001-T007 (Abril 2026) | `format-utils.ts` centralizado; `useTagInputState` compartilhado; `SearchPresetsModal<T>` genérico; `MetricCard` com `variant="compact"` + `CompactDelta` export; CandidateIdentity sub-components extraídos |

**Manutenção:** Ao adicionar novo componente UI, modal, ou tela, atualizar a seção correspondente deste documento com: arquivo, export, layout, campos/props, estados e tokens.

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

### 2.33 Toast (Sonner)
- **Biblioteca:** `sonner` (npm package)
- **Configuração:** `<SonnerToaster position="top-right" richColors />` em `layout.tsx`
- **Import:** `import { toast } from "sonner"`
- **Sistema anterior (Radix) removido:** `toast.tsx`, `toaster.tsx`, `use-toast.ts` deletados

| Método | Cor (richColors) | Uso |
|--------|-----------------|-----|
| `toast.success(title, opts)` | Verde | Confirmações de ações |
| `toast.error(title, opts)` | Vermelho | Erros e falhas |
| `toast.warning(title, opts)` | Amarelo | Avisos não-críticos |
| `toast.info(title, opts)` | Azul | Informações gerais |

- **Options:** `{ description?: string, duration?: number, action?: { label, onClick } }`
- **Posição:** `top-right` (consistente em toda a plataforma)
- **Auto-dismiss:** 4s padrão para success/info

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

#### CandidateQueriesGuide (`candidate-queries-guide.tsx`)
- **Export:** `CandidateQueriesGuide`
- **Função:** Popover com exemplos de queries para busca de candidatos
- **Container:** `Popover` + `PopoverContent` + `ScrollArea`
- **Ícones:** Lightbulb, Search, Users, BarChart3, TrendingUp, Target, Brain, Globe, Filter, MessageSquare, X, Star, UserCheck, Zap, RefreshCw, Eye, Send, Clock, Database
- **Layout:** Lista categorizada de exemplos de queries
- **States:** closed (trigger visível), open (popover com lista)

#### LiaQueriesGuide (`lia-queries-guide.tsx`)
- **Export:** `LiaQueriesGuide`
- **Função:** Popover com exemplos de queries para a LIA (assistente IA)
- **Container:** `Popover` + `PopoverContent` + `ScrollArea`
- **Ícones:** Lightbulb, Search, Users, BarChart3, Calendar, TrendingUp, Target, FileText, Briefcase, Building, Clock, AlertCircle, CheckCircle, Star, Filter, MessageSquare, Globe, Zap, X, Brain
- **Layout:** Lista categorizada de queries por tipo (análise, relatório, etc.)
- **States:** closed, open (lista de queries)

#### LiaSearchQueriesGuide (`lia-search-queries-guide.tsx`)
- **Export:** `LiaSearchQueriesGuide`
- **Função:** Popover com exemplos de queries de busca semântica
- **Container:** `Popover` + `PopoverContent` + `ScrollArea`
- **Ícones:** Lightbulb, Search, Users, BarChart3, TrendingUp, Target, FileText, MapPin, Clock, Globe, Star, Filter, Briefcase, GraduationCap, DollarSign, Building, UserCheck, Accessibility, X, Brain, Zap
- **Layout:** Lista de exemplos de busca com categorias (localização, salário, skills, etc.)
- **States:** closed, open (lista de queries)

#### LiaVacancyQueriesGuide (`lia-vacancy-queries-guide.tsx`)
- **Export:** `LiaVacancyQueriesGuide`
- **Função:** Popover com exemplos de queries relacionadas a vagas
- **Container:** `Popover` + `PopoverContent` + `ScrollArea`
- **Ícones:** Lightbulb, Search, Users, BarChart3, TrendingUp, Target, Clock, Brain, X, Filter, AlertCircle
- **Layout:** Lista de exemplos de queries para vagas
- **States:** closed, open (lista de queries)

#### AIDisclaimer (`ai-disclaimer.tsx`)
- **Export:** `AIDisclaimer`
- **Função:** Aviso de que o conteúdo foi gerado/assistido por IA
- **Layout:** Banner inline, `text-xs`, ícone Brain/Sparkles + texto
- **Cor:** Cyan accent background sutil
- **States:** visible (sempre quando conteúdo IA presente)

#### CookieConsent (`cookie-consent.tsx`)
- **Export:** `CookieConsent`
- **Função:** Banner de consentimento de cookies (LGPD/GDPR)
- **States:** visible (primeiro acesso), hidden (após aceitar/recusar)

#### MaskedInput (`masked-input.tsx`)
- **Export:** `MaskedInput`
- **Função:** Input com máscara para CPF, telefone, CEP, etc.
- **Elementos:** Input com formatação automática baseada em padrão

#### ThinkingDots (`thinking-dots.tsx`)
- **Export:** `ThinkingDots`
- **Função:** Animação de "pensando" (3 dots pulsantes)
- **States:** animating (visível enquanto LIA processa)

#### LiaPromptHeader (`lia-prompt-header.tsx`)
- **Export:** `LiaPromptHeader`
- **Função:** Header contextual para prompts da LIA
- **Elementos:** Ícone LIA + título + contexto

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

## 5. PAINEL DE CONTROLE (Dashboard / Tasks)

- **Arquivo principal:** `plataforma-lia/src/components/pages/tasks-page-mvp.tsx`
- **Componente:** `TasksPageMVP`
- **Descrição:** Tarefas e atividades pendentes do recrutador
- **Arquivo alternativo:** `plataforma-lia/src/components/pages/tasks-page.tsx` (`TasksPage`)

### Sub-componentes de Tasks
| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ActiveAlertsCard` | `pages/tasks/ActiveAlertsCard.tsx` | Card de alertas ativos |
| `TaskCard` | `pages/tasks/TaskCard.tsx` | Card individual de tarefa |
| `DailyBriefingCard` | `daily-briefing-card.tsx` | Card de briefing diário |
| `TasksSection` | `tasks-section.tsx` | Seção de tarefas agrupadas |
| `EventsSection` | `events-section.tsx` | Seção de eventos/agenda |
| `TaskModal` | `task-modal.tsx` | Modal de detalhes/edição de tarefa |

### Dashboard Estratégico
| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `StrategicDashboard` | `dashboard/strategic-dashboard.tsx` | Dashboard estratégico |
| `PredictiveAnalyticsTab` | `dashboard/predictive-analytics-tab.tsx` | Tab de analytics preditivos |
| `DashboardApp` | `dashboard-app.tsx` | Container do dashboard |

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

#### Kanban Sub-componentes (`kanban/components/`)

| Componente | Descrição |
|-----------|-----------|
| `KanbanBoard` | Board principal (em `kanban/components/`) |
| `CandidateBadges` | Badges do candidato no kanban |
| `CandidateCard` | Card do candidato (kanban) |
| `CandidateTableRow` | Row do candidato (visão tabela) |
| `ColumnContextMenu` | Menu de contexto da coluna |
| `OverrideApproveButton` | Botão de override/aprovação |
| `SaturationBadge` | Badge de saturação |
| `TransitionChatPanel` | Painel de chat de transição |
| `UniversalTransitionModal` | Modal universal de transição entre etapas |

#### Kanban Hooks (`kanban/hooks/`)

| Hook | Descrição |
|------|-----------|
| `useDragDrop` | Hook de drag & drop |
| `useCandidateSelection` | Hook de seleção de candidatos |
| `useColumnConfig` | Hook de configuração de colunas |
| `useFiltersPersistence` | Hook de persistência de filtros |
| `useKanbanFilters` | Hook de filtros do kanban |
| `useUniversalTransition` | Hook de transição universal |

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
- **Sub-diretório:** `plataforma-lia/src/components/wsi/jd-evaluation/`
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

#### WSIScorecard (`wsi/wsi-scorecard.tsx`)
- **Função:** Scorecard visual dos resultados WSI

#### WSIVoiceScreeningStatus (`wsi/wsi-voice-screening-status.tsx`)
- **Função:** Status de triagem por voz WSI

### 10.34B Screening Config Sub-componentes (`screening-config/`)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ScreeningConfigManager` | `screening-config/ScreeningConfigManager.tsx` | Manager principal de configuração |
| `ScreeningScriptTab` | `screening-config/ScreeningScriptTab.tsx` | Tab de script de triagem |
| `CompanyBankQuestions` | `screening-config/CompanyBankQuestions.tsx` | Banco de perguntas da empresa |
| `CompanyDefaultQuestions` | `screening-config/CompanyDefaultQuestions.tsx` | Perguntas default da empresa |
| `CustomQuestions` | `screening-config/CustomQuestions.tsx` | Perguntas customizadas |
| `SCMQuestionDetail` | `screening-config/SCMQuestionDetail.tsx` | Detalhe de pergunta |
| `SCMScreeningTypes` | `screening-config/SCMScreeningTypes.ts` | Tipos de screening |
| `SCMSectionConfiguracoes` | `screening-config/SCMSectionConfiguracoes.tsx` | Seção de configurações |
| `SCMSectionContent` | `screening-config/SCMSectionContent.tsx` | Seção de conteúdo |
| `SCMSectionPerguntasEdit` | `screening-config/SCMSectionPerguntasEdit.tsx` | Edição de perguntas |
| `SCMWSIStepDetails` | `screening-config/SCMWSIStepDetails.tsx` | Detalhes de step WSI |
| `ScreeningChannelsModal` | `screening-config/ScreeningChannelsModal.tsx` | Modal de canais |
| `ScreeningSchedulingModal` | `screening-config/ScreeningSchedulingModal.tsx` | Modal de agendamento |
| `ScreeningSettingsModal` | `screening-config/ScreeningSettingsModal.tsx` | Modal de configurações |
| `ScreeningStatusModal` | `screening-config/ScreeningStatusModal.tsx` | Modal de status |

### 10.34C Screening Notifications (`screening/`)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ScreeningNotificationCard` | `screening/screening-notification-card.tsx` | Card de notificação de triagem |

### 10.34D WSI Sub-componentes (`wsi/`)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `QuestionAdjustmentChat` | `wsi/QuestionAdjustmentChat.tsx` | Chat de ajuste de perguntas |
| `QuestionDiffView` | `wsi/QuestionDiffView.tsx` | Diff view de perguntas |
| `AdjustmentCounter` | `wsi/AdjustmentCounter.tsx` | Contador de ajustes |
| `JDEvaluationPanel` | `wsi/JDEvaluationPanel.tsx` | Painel de avaliação JD |
| `WSIScorecard` | `wsi/wsi-scorecard.tsx` | Scorecard visual WSI |
| `WSITextScreeningModal` | `wsi/wsi-text-screening-modal.tsx` | Modal triagem por texto |
| `WSITriagemInviteModal` | `wsi/wsi-triagem-invite-modal.tsx` | Modal convite triagem |
| `WSIVoiceScreeningStatus` | `wsi/wsi-voice-screening-status.tsx` | Status triagem por voz |
| `jd-evaluation/` | `wsi/jd-evaluation/` | Sub-diretório de avaliação JD |

### 10.35 RubricEvaluationModal
- **Arquivo:** `plataforma-lia/src/components/rubric-evaluation-modal.tsx`
- **Export:** `RubricEvaluationModal` (named + default)
- **Container:** Overlay customizado (`fixed inset-0 z-50 bg-black/30 backdrop-blur-[1px]`)
- **Panel:** `max-w-3xl max-h-[90vh] bg-white rounded-md shadow-xl`
- **Header:** Nome do candidato + job title + score badge + fechar (X)
- **Score badge:** Dynamic colors — ≥85 'Excelente' cyan, ≥70 'Bom' cyan, ≥50 'Moderado' amber, ≥30 'Fraco' coral, <30 'Inadequado' coral
- **Decision badge:** `APROVAR_TRIAGEM` (CheckCircle cyan), `MANTER_ESPERA` (Clock amber), `NAO_PROSSEGUIR` (XCircle coral)

| Seção | Componentes | Dados |
|-------|-----------|-------|
| Tabs de navegação | `overview` / `details` botões | 2 seções alternáveis |
| Score Hero | Número grande + `Badge` label | Score geral + classificação |
| Requirements Grid | Cards com ícone + badge | Por requisito: nome, prioridade, nível, evidência |
| Rubric Levels | `Check` / `AlertTriangle` / `X` ícones | Excede, Atende, Parcial, Ausente |
| Priority Badges | `Badge` inline | Essencial (coral bg), Importante (amber bg), Desejável (gray bg) |
| Red Flags | Cards com status | ok (gray), warning (amber), critical (coral) |
| Why Candidate | Lista numerada | Evidências positivas |
| Parecer LIA | Accordion sections | Contexto fit, pontos fortes, riscos, recomendação |
| Audit Metrics | Collapsible section | Total requirements, essential/important/desirable met, confidence, data completeness |

- **Rubric style logic:**
  - `exceeds`: bg `rgba(96,190,209,0.08)`, ícone Check gray-700
  - `meets`: bg `rgba(96,190,209,0.04)`, ícone Check gray-700
  - `partial`: bg `rgba(245,158,11,0.08)`, ícone AlertTriangle amber
  - `missing`: bg `rgba(225,97,98,0.08)`, ícone X wedo-coral
- **Footer:** `Button outline` (Rejeitar, ThumbsDown) + `Button default` (Aprovar, ThumbsUp)
- **Loading states:** `isApproving` / `isRejecting` com `Loader2 animate-spin`
- **Props:** `isOpen`, `onClose`, `evaluation: RubricEvaluationData`, `candidateId`, `candidateName`, `jobId`, `onApprove`, `onReject`
- **States:** closed, open (overview tab), details tab, audit expanded, approving (loader), rejecting (loader), approved (toast success), rejected (toast)

---

## 11. TELA FULL DO CANDIDATO (CandidateReviewModal)

- **Arquivo:** `plataforma-lia/src/components/pages/candidate-review-modal.tsx`
- **Export:** `CandidateReviewModal` (named + default)
- **Container:** `fixed inset-0 z-50` overlay (`bg-black/50`) + panel `bg-white m-4 rounded-md`
- **Font:** `fontFamily: 'Open Sans, sans-serif'`
- **Keyboard shortcuts:** `A` = Approve, `R` = Reject, `ArrowLeft/Right` = navigation

### 11.1 Header
- **Layout:** `flex items-center justify-between px-6 py-4 border-b`
- **Back button:** `ChevronLeft w-5 h-5` + "Review Profiles" `text-sm font-medium`
- **Job title:** `text-sm text-gray-600`

### 11.2 Layout 3 Colunas
- **Coluna Esquerda (420px):** Perfil do candidato
- **Coluna Central (flex-1):** Critérios de avaliação + Match reasons
- **Coluna Direita (hidden/visible):** Edição de critérios (overlay)

### 11.3 Coluna Esquerda — Perfil

| Elemento | Componente | Estilo |
|----------|-----------|--------|
| Nome | `h2 text-xl font-semibold text-gray-950` | Open Sans |
| LinkedIn | `Linkedin w-5 h-5 text-[#0077B5]` | Link externo |
| Localização | `MapPin w-4 h-4` + texto `text-sm text-gray-600` | — |
| Cargo atual | `Briefcase w-4 h-4` + "Title at Company" `text-sm text-gray-800` | Company logo se disponível |
| Educação | `GraduationCap w-4 h-4` + texto `text-sm text-gray-600` | — |
| Full Profile btn | `Button variant="outline" size="sm" text-xs` | `ExternalLink w-3 h-3` |

#### Tabs de Perfil (3 tabs)
| Tab | Dados |
|-----|-------|
| Experience | Highlights (grid 3-col bg-gray-50), Experience stats (grid 3-col), Timeline de experiências |
| Education | Lista de formações (institution, degree, period) |
| Skill Map | Skills + Languages em `Badge variant="outline" text-xs` |

#### Experience Highlights (grid)
- **Card:** `p-3 bg-gray-50 rounded-md border border-gray-100`
- **Título:** `text-xs font-semibold text-gray-950`
- **Descrição:** `text-[11px] text-gray-600 line-clamp-2`

#### Experience Stats (grid 3-col)
- **Label:** `text-[11px] text-gray-600 uppercase tracking-wide`
- **Value:** `text-sm font-semibold text-gray-950`
- **Campos:** Average Tenure, Current Tenure, Total Experience

#### Experience Timeline
- **Card:** `pl-6 relative` com `absolute left-0 top-2 w-2 h-2 rounded-full bg-gray-300`
- **Company:** `img w-5 h-5 rounded` ou `Building2 w-4 h-4`
- **Title:** `text-sm font-medium text-gray-950`
- **Period:** `text-[11px] text-gray-600`
- **Skills:** `Badge variant="outline" text-[10px]`
- **Promotion:** `Badge text-[10px] bg-amber-50 text-amber-700 border-amber-200` com `Star w-3 h-3`

### 11.4 Coluna Central — Avaliação

| Elemento | Componente | Detalhes |
|----------|-----------|---------|
| Criteria counter | `text-sm font-medium` | "Your Criteria (X)" |
| Edit button | `Button variant="ghost" size="sm"` + `Edit2 w-4 h-4` | Abre panel de edição |
| Criteria list | `Badge` por critério | Pinned (`Star fill w-3`) e normais |
| Match reasons | `Card bg-white border-gray-200` | Por critério: explanation + score bar |
| Score bar (match) | `div h-1.5 rounded-full bg-gray-100` | Fill: green se isGoodMatch, red senão |
| Good match indicator | `CheckCircle2 w-4 h-4 text-green-600` | — |
| Bad match indicator | `XIcon w-4 h-4 text-red-500` | — |

### 11.5 Footer de Ação
- **Layout:** `border-t border-gray-200 bg-white px-6 py-4`
- **Navigation:** `ChevronLeft`/`ChevronRight` arrows + `Badge variant="outline" text-xs` (X de Y)
- **Action buttons:** `Button` (Reject, XIcon, border-red-200 hover:bg-red-50) + `Button` (Approve, Check, bg-gray-900)
- **States:** navigating (prev/next), approving (action + auto-advance), rejecting (action + auto-advance)

### 11.6 Panel de Edição de Critérios (overlay)
- **Trigger:** Edit button na coluna central
- **Layout:** `fixed inset-0 z-50 bg-black/50` + panel `bg-white rounded-md`
- **Elementos:**
  - Lista de critérios com `GripVertical` drag handle
  - `Input` para adicionar novo critério
  - `Button` (Save, `Save w-4 h-4 bg-gray-900`)
  - `Button` (Cancel, `X w-4 h-4`)
  - Presets: `DEFAULT_PRESETS` (Tech Senior, Product Manager, Design Lead)
- **Ações por critério:** Pin (`Star`), Delete (`Trash2`)
- **States:** editing, reordering (drag), saving

---

## 12. CONFIGURAÇÕES (Settings)

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
| ApproverSection | `settings/ApproverSection.tsx` | Seção de aprovadores |
| DepartmentsTab | `settings/DepartmentsTab.tsx` | Tab de departamentos |
| TechStackTab | `settings/TechStackTab.tsx` | Tab de tech stack |
| SettingsApiKeysTab | `settings/settings-api-keys-tab.tsx` | Tab de API keys |
| SettingsBillingTab | `settings/settings-billing-tab.tsx` | Tab de billing |
| SettingsCompanyTabs | `settings/settings-company-tabs.tsx` | Tabs de empresa |
| SettingsGeneralTab | `settings/settings-general-tab.tsx` | Tab geral |
| SettingsIntegrationsTab | `settings/settings-integrations-tab.tsx` | Tab de integrações |
| SettingsJourneyTab | `settings/settings-journey-tab.tsx` | Tab de jornada |
| SettingsNotificationsTab | `settings/settings-notifications-tab.tsx` | Tab de notificações |
| SettingsRecruitmentTabs | `settings/settings-recruitment-tabs.tsx` | Tabs de recrutamento |
| SettingsSecurityTab | `settings/settings-security-tab.tsx` | Tab de segurança |
| CommunicationHub | `settings/CommunicationHub.tsx` | Hub de comunicação unificado |
| GoalsManagement (hook) | `settings/use-goals-management.ts` | Hook de gestão de metas |
| GoalsPlanningConstants | `settings/goalsPlanningConstants.ts` | Constantes de planejamento de metas |
| CompanyTeamHubTypes | `settings/companyTeamHub.types.ts` | Tipos do hub de equipe |
| EligibilityQuestionsBank | `settings/eligibility-questions-bank.ts` | Banco de perguntas de elegibilidade |
| RecruitmentJourneyTypes | `settings/recruitment-journey.types.ts` | Tipos da jornada de recrutamento |

### Sub-diretórios de Settings

| Diretório | Descrição |
|-----------|-----------|
| `settings/benefits/` | Componentes de benefícios |
| `settings/communication-hub/` | Sub-componentes do hub de comunicação |
| `settings/company/` | Sub-componentes de dados da empresa |
| `settings/goals/` | Sub-componentes de gestão de metas |
| `settings/recruitment/` | Sub-componentes de recrutamento |

---

## 13. COMPONENTES TRANSVERSAIS

### 13.1 Chat LIA
- **Arquivo:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Componente:** `ChatPage`
- **CSS:** `plataforma-lia/src/components/pages/chat-page.css`
- **Indicadores:** `ChatStatusIndicators` (pensando, executando, concluído)
- **Sugestões:** `PromptSuggestionsDock`, `PromptSuggestionsPopover`
- **Ações rápidas:** `QuickActionChips`

### 13.2 Busca Global
- **Componente:** `CommandPalette` (`components/ui/command-palette.tsx`)
- **Atalho:** Ctrl+K / Cmd+K
- **Primitiva:** cmdk
- **Também:** `LiaSearchQueriesGuide`, `LiaVacancyQueriesGuide`, `CandidateQueriesGuide`

### 13.3 Sistema de Notificações
- **Componente:** `NotificationSystem` (`components/notification-system.tsx`)
- **Ícone trigger:** `Bell` (Lucide) na TopBar
- **Toast:** Sonner (`toast.success/error/warning/info` — `position="top-right"`, `richColors`)

### 13.4 AI Disclaimer
- **Componente:** `AIDisclaimer` (`components/ui/ai-disclaimer.tsx`)
- **Uso:** Aviso em conteúdos gerados por IA

### 13.5 Theme Toggle
- **Componente:** `ThemeToggle` (`components/theme-toggle.tsx`)
- **Posição:** Na sidebar, rodapé
- **Ação:** Alterna entre light/dark mode (class strategy)

### 13.6 Error Boundary
- **Componente:** `ErrorBoundary` (`components/error-boundary.tsx`)
- **Função:** Captura erros React e exibe fallback amigável

### 13.7 Page Transition
- **Componente:** `PageTransition` (`components/page-transition.tsx`)
- **Função:** Animação de transição entre páginas

### 13.8 Presentation Mode
- **Componente:** `PresentationMode` (`components/presentation-mode.tsx`)
- **Função:** Modo de apresentação com interface simplificada

### 13.9 WeDO Logo
- **Componente:** `WedoLogo` (`components/wedo-logo.tsx`)
- **Função:** Logo SVG da WeDOTalent

### 13.10 Auth Context
- **Componente:** `AuthContext` (`components/auth-context.tsx`)
- **Função:** Contexto React de autenticação (WorkOS)

### 13.11 Theme Provider
- **Componente:** `ThemeProvider` (`components/theme-provider.tsx`)
- **Função:** Provider do tema (light/dark mode)

---

## 13A. SISTEMA DE BUSCA (Search)

- **Diretório:** `plataforma-lia/src/components/search/`
- **Barrel:** `search/index.ts`

### Componentes Principais

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `SmartSearchInput` | `smart-search-input.tsx` | Input principal de busca semântica com modos |
| `AdvancedSearch` | `advanced-search.tsx` | Interface de busca avançada |
| `AdvancedFiltersModal` | `advanced-filters-modal.tsx` | Modal de filtros avançados (1125+ linhas) |
| `SearchPresetsModal` | `SearchPresetsModal.tsx` | Modal genérico de presets reutilizável (T004 — 433 linhas) |
| `CompanyPresetsModal` | `CompanyPresetsModal.tsx` | Presets de empresas (wrapper de SearchPresetsModal) |
| `LocationPresetsModal` | `LocationPresetsModal.tsx` | Presets de localização (wrapper de SearchPresetsModal) |
| `UniversityPresetsModal` | `UniversityPresetsModal.tsx` | Presets de universidades (wrapper de SearchPresetsModal) |
| `SearchQualityPanel` | `SearchQualityPanel.tsx` | Painel de qualidade da busca |
| `SearchFeedbackButtons` | `SearchFeedbackButtons.tsx` | Botões like/dislike por resultado |
| `SearchSourceSelector` | `SearchSourceSelector.tsx` | Seletor de fonte (interno/externo) |
| `CreditConfirmationDialog` | `credit-confirmation-dialog.tsx` | Diálogo de confirmação de créditos |
| `CreditCostDisplay` | `credit-cost-display.tsx` | Exibição de custo em créditos |
| `QualificationBadge` | `QualificationBadge.tsx` | Badge de qualificação do candidato |
| `FilterAutocomplete` | `filter-autocomplete.tsx` | Autocomplete para filtros |
| `SearchPreviewCard` | `search-preview-card.tsx` | Card de preview do resultado |
| `SearchResultsCard` | `search-results-card.tsx` | Card de resultado de busca |

### Filter Sections (`search/filter-sections/`)

| Componente | Descrição |
|-----------|-----------|
| `FilterChipsBar` | Barra de chips de filtros ativos |
| `FilterSectionEmpresa` | Filtros de empresa |
| `FilterSectionFormacao` | Filtros de formação |
| `FilterSectionGeral` | Filtros gerais |
| `FilterSectionHabilidades` | Filtros de habilidades |
| `FilterSectionIdiomas` | Filtros de idiomas |
| `FilterSectionOpcoes` | Filtros de opções |
| `FilterSectionOrigem` | Filtros de origem |
| `FilterSectionPerfil` | Filtros de perfil |
| `ModalFooterActions` | Botões de ação do modal de filtros |

### Filter Inputs (inputs especializados de filtro)

| Componente | Descrição |
|-----------|-----------|
| `CompanyFilterInput` | Input de filtro por empresa |
| `CompanyHQLocationsInput` | Input de localização da sede |
| `CompanyTagsInput` | Input de tags de empresa |
| `DegreeRequirementsInput` | Input de requisitos de grau |
| `ExcludedCompaniesInput` | Input de empresas excluídas |
| `ExcludedUniversitiesInput` | Input de universidades excluídas |
| `ExpertiseAreasInput` | Input de áreas de expertise |
| `FieldsOfStudyInput` | Input de campos de estudo |
| `FundingStagesInput` | Input de estágios de funding |
| `GraduationYearInput` | Input de ano de graduação |
| `IndustryFilterInput` / `IndustrySingleSelect` | Filtros de indústria |
| `LanguageFilterInput` | Input de filtro de idioma |
| `LocationFilterInput` | Input de filtro de localização |
| `RadiusDropdown` | Dropdown de raio geográfico |
| `SimilarProfilesInput` | Input de perfis similares |
| `SkillsFilterInput` | Input de filtro de skills |
| `TimezoneDropdown` | Dropdown de timezone |
| `UniversitiesFilterInput` / `UniversityLocationsInput` | Filtros de universidades |

### SSI Modes (`search/ssi-modes/`)

| Componente | Descrição |
|-----------|-----------|
| `SSIModeBoolean` | Modo de busca booleana |
| `SSIModeJobDescription` | Modo de busca por JD |
| `SSIModeNatural` | Modo de busca em linguagem natural |
| `SSIModeContent` | `SSIModeContent.tsx` — Container de conteúdo SSI |
| `SSIJDMode` | `SSIJDMode.tsx` — Modo JD integrado |
| `SSISimilarMode` | `SSISimilarMode.tsx` — Modo de perfis similares |

### Job Filters (`search/job-filters/`)

| Componente | Descrição |
|-----------|-----------|
| `JobLevelsAndRolesSection` | Filtro de níveis e roles |
| `JobTitlesSection` | Filtro de títulos |
| `PastTitlesSection` | Filtro de títulos anteriores |
| `TenureSection` | Filtro de tenure |

### Archetypes

| Componente | Descrição |
|-----------|-----------|
| `ArchetypesList` | Lista de arquétipos de busca |
| `SearchModeArchetypes` | Modo de busca por arquétipo |
| `EditArchetypeModal` | Modal de edição de arquétipo |
| `SaveArchetypeModal` | `save-archetype-modal.tsx` — Salvar novo arquétipo |

### Search Hooks (`search/hooks/`)

| Hook | Descrição |
|------|-----------|
| `useSmartSearchCore` | Core da busca inteligente |
| `useSmartSearchCallbacks` | Callbacks da busca |
| `useSmartSearchArchetypes` | Gestão de arquétipos |
| `useSmartSearchSimilar` | Busca de perfis similares |
| `useAdvancedFiltersCore` | Core de filtros avançados |

---

## 13B. AGENT CONTROL CENTER

- **Diretório:** `plataforma-lia/src/components/agent-control-center/`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `AgentControlCenter` | `index.tsx` | Painel principal de controle de agentes IA — usa `MetricCard variant="compact"` + `CompactDelta` (T006) |
| `Sparkline` | `sparkline.tsx` | Gráfico sparkline para métricas inline |
| `AgentDetailPanel` | `agent-detail-panel.tsx` | Painel de detalhes do agente selecionado |

---

## 13C. EXPANDED CHAT / JOB WIZARD

- **Diretório:** `plataforma-lia/src/components/expanded-chat/`
- **Modal wrapper:** `plataforma-lia/src/components/expanded-chat-modal.tsx`
- **Descrição:** Sistema wizard conversacional para criação de vagas com LIA

### Componentes (`expanded-chat/components/`)

| Componente | Descrição |
|-----------|-----------|
| `ChatMessageList` | Lista de mensagens do wizard |
| `ExpandedChatInput` | Input do chat expandido |
| `WizardHeader` | Header do wizard |
| `WizardSidebar` | Sidebar de navegação de etapas |
| `WizardRightPanel` | Painel direito com preview |
| `WSIQualityBar` | Barra de qualidade WSI |
| `ToolConfirmationMessage` | Mensagem de confirmação de tool call |
| `ToolExecutionFeedback` | Feedback visual de execução de tool |

### Stages (`expanded-chat/stages/`)

| Stage | Descrição |
|-------|-----------|
| `CompetenciesStage` | Configuração de competências |
| `EnrichedJDStage` | JD enriquecida pela LIA |
| `InputEvaluationStage` | Avaliação de inputs |
| `ReviewPublishStage` | Revisão e publicação |
| `SalaryStage` | Configuração salarial |
| `SearchCalibrationStage` | Calibração de busca |
| `WSIQuestionsStage` | Configuração de perguntas WSI |

### Modals (`expanded-chat/modals/`)

| Modal | Descrição |
|-------|-----------|
| `AddBenefitModal` | Adicionar benefício |
| `AddCompetencyModal` | Adicionar competência |
| `AddSkillModal` | Adicionar skill |
| `AddTechnicalSkillModal` | Adicionar skill técnica |
| `CalibrationProfileModal` | Modal de perfil de calibração |
| `ClearDraftConfirmModal` | Confirmar limpeza de rascunho |
| `EditCriteriaModal` | Editar critérios |
| `SkipCompetenciesWarningModal` | Aviso ao pular competências |

### Hooks Principais (`expanded-chat/hooks/` — 40+ hooks)
- `useExpandedChatModalCore`, `useWizardFlow`, `useWizardOrchestrator`, `useWizardNavigation`, `useWizardState`, `useSendMessageHandlers`, `useToolCalling`, `useConversationMemory`, `useCriteriaDetection`, `useWSIState`, `useWSIQuestionHandlers`, `useCalibrationState`, `useFastTrackState`, `useContextSwitching`, `useFieldHighlight`, `useWizardPublishHandlers`, etc.

---

## 13D. JOB WIZARD (Alternativo)

- **Diretório:** `plataforma-lia/src/components/job-wizard/`
- **Descrição:** Wizard simplificado de criação de vaga (alternativa ao Expanded Chat)

| Componente | Descrição |
|-----------|-----------|
| `WizardContainer` | Container principal do wizard |
| `WizardContext` | Context React do wizard |
| `FastTrackReviewPanel` | Painel de revisão fast-track |
| `FastTrackSuggestions` | Sugestões fast-track da LIA |
| `VacancySummaryCard` | Card de resumo da vaga |

### Stages (`job-wizard/stages/`)
- Etapas do wizard com formulários guiados

---

## 13E. LIA FLOAT SYSTEM

- **Diretório:** `plataforma-lia/src/components/lia-float/`
- **Descrição:** Sistema de chat flutuante da LIA (acessível globalmente)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `LiaChatButton` | `LiaChatButton.tsx` | Botão flutuante para abrir chat LIA |
| `LiaChatPanel` | `LiaChatPanel.tsx` | Painel de chat flutuante |
| `LiaSplitPanel` | `LiaSplitPanel.tsx` | Painel dividido (chat + preview) |
| `LiaSuperPrompt` | `LiaSuperPrompt.tsx` | Super prompt com ações rápidas |
| `HITLConfirmCard` | `HITLConfirmCard.tsx` | Card de confirmação Human-in-the-Loop |
| `LiaFloatConditional` | `LiaFloatConditional.tsx` | Renderização condicional do float |

---

## 13F. TRIAGEM (Candidato-Facing)

- **Diretório:** `plataforma-lia/src/components/triagem/`
- **Descrição:** Componentes do fluxo de triagem visto pelo candidato

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ChatContainer` | `ChatContainer.tsx` | Container principal do chat de triagem |
| `MessageBubble` | `MessageBubble.tsx` | Bolha de mensagem |
| `InputBar` | `InputBar.tsx` | Barra de input do candidato |
| `WelcomeCard` | `WelcomeCard.tsx` | Card de boas-vindas |
| `CompletionCard` | `CompletionCard.tsx` | Card de conclusão |
| `ConfirmationCard` | `ConfirmationCard.tsx` | Card de confirmação |
| `ProgressBar` | `ProgressBar.tsx` | Barra de progresso |
| `TypingIndicator` | `TypingIndicator.tsx` | Indicador de digitação |
| `LikertScaleCard` | `LikertScaleCard.tsx` | Card de escala Likert |
| `MultipleChoiceCard` | `MultipleChoiceCard.tsx` | Card de múltipla escolha |

---

## 13G. TRIAGEM DETAILS (Recrutador)

- **Diretório:** `plataforma-lia/src/components/triagem-details/`
- **Modal wrapper:** `plataforma-lia/src/components/triagem-details-modal.tsx`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `TriagemComparativoTab` | `triagem-comparativo-tab.tsx` | Tab comparativa de triagens |
| `TriagemScoresPanel` | `triagem-scores-panel.tsx` | Painel de scores da triagem |
| `TriagemSummaryBar` | `triagem-summary-bar.tsx` | Barra de resumo da triagem |

---

## 13H. CALIBRATION

- **Diretório:** `plataforma-lia/src/components/calibration/`
- **Card avulso:** `plataforma-lia/src/components/calibration-card.tsx`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `CalibrationDashboard` | `calibration-dashboard.tsx` | Dashboard de calibração de busca |
| `CalibrationIndex` | `index.tsx` | Componente principal de calibração |
| `LiaFeedbackWidget` | `lia-feedback-widget.tsx` | Widget de feedback para calibração da LIA |
| `CalibrationCard` | `calibration-card.tsx` (root) | Card de calibração |

---

## 13I. ADMIN PANEL

- **Diretório:** `plataforma-lia/src/components/admin/`
- **Barrel:** `admin/index.ts`

### Dashboard Admin (`admin/dashboard/`)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `MetricCard` | `MetricCard.tsx` | Card de métrica canônico — `variant="default"\|"compact"`, exporta `CompactDelta`, `ACCENT_BG_MAP` (T006) |
| `ActivityFeed` | `ActivityFeed.tsx` | Feed de atividades do admin |
| `PeriodFilter` | `PeriodFilter.tsx` | Filtro de período |
| `QuickActions` | `QuickActions.tsx` | Ações rápidas do admin |
| `ServiceConsumption` | `ServiceConsumption.tsx` | Consumo de serviços |

### AI Consumption (`admin/ai-consumption/`)

| Componente | Descrição |
|-----------|-----------|
| `AgentBreakdown` | Breakdown por agente |
| `ConsumptionChart` | Gráfico de consumo |
| `ConsumptionGrid` | Grid de consumo |
| `ConsumptionSummaryCard` | Card de resumo de consumo |

### Clients (`admin/clients/`)

| Componente | Descrição |
|-----------|-----------|
| `ClientCard` | Card de cliente |
| `ClientFilters` | Filtros de clientes |
| `ClientTable` | Tabela de clientes |
| `CreateClientDialog` | Diálogo de criação de cliente |

### Outros Admin

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `AdminTemplateHub` | `AdminTemplateHub.tsx` | Hub de templates admin |
| `Breadcrumbs` | `Breadcrumbs.tsx` | Breadcrumbs de navegação admin |
| `ClientSelector` | `ClientSelector.tsx` | Seletor de cliente ativo |
| `WorkOSAdminPortal` | `workos-admin-portal.tsx` | Portal admin WorkOS |
| `WorkOSLinkCard` | `workos-link-card.tsx` | Card de link WorkOS |

---

## 13J. CANDIDATE PROFILE / PREVIEW / PAGE

### Candidate Profile (`components/candidate-profile/`)

| Componente | Descrição |
|-----------|-----------|
| `CandidateAvatar` | Avatar com fallback e status (T002) |
| `CandidateContactActions` | Botões de contato (email, phone, linkedin) (T002) |
| `CandidateScoreBadge` | Badge de score com cor dinâmica (T002) |
| `CandidateSkillsList` | Lista de skills com badges (T002) |
| `ProfileEducationSection` | Seção de educação do perfil |
| `ProfileExperienceSection` | Seção de experiência do perfil |

### Candidate Preview (`components/candidate-preview/`)

| Componente | Descrição |
|-----------|-----------|
| `CandidatePreviewProfileTab` | Tab de perfil no preview |
| `CandidateActivitiesTab` | Tab de atividades |
| `CandidateFilesTab` | Tab de arquivos |
| `CandidateOpinionsTab` | Tab de opiniões |
| `FilePreviewModal` | Modal de preview de arquivo |
| `LiaChatModal` | Modal de chat com LIA |
| `OpinionCard` | Card de opinião |
| `useCandidateFiles` | Hook de arquivos |
| `useCandidatePreviewCore` | Hook core do preview |

### Candidate Page (`components/candidate-page/`)

| Componente | Descrição |
|-----------|-----------|
| `CandidatePageHeader` | Header da página do candidato |
| `CandidatePageProfileTab` | Tab de perfil |
| `CandidatePageActivitiesTab` | Tab de atividades |
| `CandidatePageFilesTab` | Tab de arquivos |
| `CandidatePageOpinionsTab` | Tab de opiniões |
| `useCandidatePageCore` | Hook core da página |

---

## 13K. CHAT SYSTEM

- **Diretório:** `plataforma-lia/src/components/chat/`
- **Barrel:** `chat/index.ts`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ChatMessageList` | `ChatMessageList.tsx` | Lista de mensagens |
| `ChatInputBar` | `chat-input-bar.tsx` | Barra de input com ações |
| `MessageBubble` | `message-bubble.tsx` | Bolha de mensagem |
| `MessageFeedback` | `message-feedback.tsx` | Feedback (like/dislike) por mensagem |
| `ChatContextPanel` | `ChatContextPanel.tsx` + `Part1/Part2/Part3` | Painel de contexto (3 partes) |
| `ActionResultCard` | `action-result-card.tsx` | Card de resultado de ação |
| `AgentMemoryIndicator` | `agent-memory-indicator.tsx` | Indicador de memória do agente |
| `DetectedFieldsCard` | `detected-fields-card.tsx` | Card de campos detectados |
| `EmptyFieldNotificationMessage` | `empty-field-notification-message.tsx` | Notificação de campo vazio |
| `ParecerLIACard` | `parecer-lia-card.tsx` | Card de parecer da LIA |
| `ResumeAnalysisResult` | `resume-analysis-result.tsx` | Resultado de análise de CV |
| `MultimodalUpload` | `multimodal-upload.tsx` | Upload multimodal (arquivo + áudio) |
| `TypingIndicator` | `typing-indicator.tsx` | Indicador de digitação |
| `VoiceChatButton` | `voice-chat-button.tsx` | Botão de chat por voz |

---

## 13L. CHARTS

- **Diretório:** `plataforma-lia/src/components/charts/`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `AdvancedInteractiveCharts` | `advanced-interactive-charts.tsx` | Gráficos interativos avançados |
| `ChartComponents` | `chart-components.tsx` | Componentes base de gráficos (MetricCard removido — T006) |
| `InteractiveCharts` | `interactive-charts.tsx` | Gráficos interativos |

---

## 13M. TABLES SYSTEM

- **Diretório:** `plataforma-lia/src/components/tables/`
- **Barrel:** `tables/index.ts`

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `UnifiedCandidateTable` | `unified-candidate-table.tsx` | Tabela unificada de candidatos |
| `CandidateTableRow` | `candidate-table-row.tsx` | Row de candidato |
| `CellRenderers` | `cell-renderers.tsx` | Renderizadores de célula |
| `ColumnDefinitions` | `column-definitions.ts` | Definições de colunas |

---

## 13N. AUTONOMOUS AGENTS

- **Diretório:** `plataforma-lia/src/components/autonomous/`

| Componente | Descrição |
|-----------|-----------|
| `JobsDashboard` | Dashboard de vagas do agente autônomo |
| `CreateJobModal` | Modal de criação de vaga autônoma |
| `ProactiveActions` | Ações proativas do agente |
| `ProactiveActionsBell` | Bell de notificação de ações proativas |

---

## 13O. MODAIS DISPERSOS (fora de `modals/`)

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `BatchApprovalModal` | `batch-approval-modal.tsx` | Aprovação em lote |
| `BigFiveModal` | `big-five-modal.tsx` | Modal de perfil Big Five |
| `CandidateDecisionFlowModal` | `candidate-decision-flow-modal.tsx` | Fluxo de decisão sobre candidato |
| `CandidateModal` | `candidate-modal.tsx` | Modal genérico de candidato |
| `ColumnConfigurationModal` | `column-configuration-modal.tsx` | Configuração de colunas de tabela |
| `DiscAssessmentModal` | `disc-assessment-modal.tsx` | Modal de avaliação DISC |
| `ExpandedChatModal` | `expanded-chat-modal.tsx` | Modal wrapper do expanded chat |
| `GlobalSearchModal` | `global-search-modal.tsx` | Modal de busca global |
| `JobReportModal` | `job-report-modal.tsx` | Modal de relatório da vaga |
| `LiaTipsModal` | `lia-tips-modal.tsx` | Modal de dicas da LIA |
| `QuickActionsModals` | `quick-actions-modals.tsx` | Modais de ações rápidas |
| `QuickViewModal` | `quick-view-modal.tsx` | Modal de quick view |
| `RevealCreditsModal` | `reveal-credits-modal.tsx` | Modal de reveal de créditos |
| `SaveCommandModal` | `save-command-modal.tsx` | Modal de salvar comando |
| `TriagemDetailsModal` | `triagem-details-modal.tsx` | Modal de detalhes da triagem |
| `CVUploadModal` | `cv/cv-upload-modal.tsx` | Modal de upload de CV |
| `AdvancedFiltersModal` | `search/advanced-filters-modal.tsx` | Modal de filtros avançados |
| `AlertSettingsModal` | `alerts/alert-settings-modal.tsx` | Modal de configuração de alertas |

---

## 13P. COMPONENTES LIA ESPECIALIZADOS

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `LiaExpandedPrompt` | `lia-expanded-prompt.tsx` | Prompt expandido da LIA |
| `LiaMetricsChart` | `lia-metrics-chart.tsx` | Gráfico de métricas da LIA |
| `LiaMetricsDashboard` | `lia-metrics-dashboard.tsx` | Dashboard de métricas |
| `LiaPerformanceIndicators` | `lia-performance-indicators.tsx` | Indicadores de performance |
| `LiaProcessingCard` | `lia-processing-card.tsx` | Card de processamento |
| `LiaScoreCard` | `lia-score-card.tsx` | Card de score LIA |
| `LiaSuggestionCards` | `lia-suggestion-cards.tsx` | Cards de sugestões |
| `LiaScreeningDialogue` | `lia-screening-dialogue.tsx` | Diálogo de triagem |
| `LiaScreeningGuide` | `lia-screening-guide.tsx` | Guia de triagem |
| `ScreeningFeedbackSection` | `lia-screening/ScreeningFeedbackSection.tsx` | Seção de feedback de triagem |

---

## 13Q. COMPONENTES DIVERSOS

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| `ActivityFeed` | `activity-feed.tsx` | Feed de atividades |
| `AISearchToggle` | `ai-search-toggle.tsx` | Toggle de busca por IA |
| `AsyncJobProgress` | `async/AsyncJobProgress.tsx` | Progresso de job assíncrono |
| `BulkActionsBar` | `bulk-actions-bar.tsx` | Barra de ações em lote |
| `CandidateComparison` | `candidate-comparison.tsx` | Comparação de candidatos |
| `ClientOnly` | `client-only.tsx` | Wrapper para renderização client-side |
| `CloudsBackground` | `clouds-background.tsx` | Background decorativo |
| `CompanyScreeningSettings` | `company-screening-settings.tsx` | Settings de screening da empresa |
| `ContextualActionsBanner` | `contextual-actions-banner.tsx` | Banner de ações contextuais |
| `CVPreview` | `cv/cv-preview.tsx` | Preview de CV |
| `ExperienceHighlightCard` | `experience-highlight-card.tsx` | Card de destaque de experiência |
| `ExportTools` | `export-tools.tsx` | Ferramentas de exportação |
| `FairnessWarningBanner` | `fairness-warning-banner.tsx` | Banner de aviso de fairness/bias |
| `IntelligenceNotifications` | `intelligence-notifications.tsx` | Notificações inteligentes |
| `JobActionsBar` | `job-actions-bar.tsx` | Barra de ações da vaga |
| `MLRecruitmentEngine` | `ml/recruitment-ml-engine.tsx` | Engine de ML para recrutamento |
| `SuccessPrediction` | `ml-analytics/success-prediction.tsx` | Predição de sucesso |
| `ModuleUpsell` | `module-access/module-upsell.tsx` | Upsell de módulos premium |
| `ProactiveInsightCard` | `proactive-insight-card.tsx` | Card de insight proativo |
| `ProactiveChatMessage` | `automation/ProactiveChatMessage.tsx` | Mensagem proativa no chat |
| `PromptContextViewer` | `PromptContextViewer.tsx` | Viewer de contexto do prompt |
| `PromptSuggestionsPanel` | `PromptSuggestionsPanel.tsx` | Painel de sugestões de prompts |
| `ReactThinkingStream` | `react-thinking-stream.tsx` | Stream de pensamento |
| `RegionalAnalysis` | `regional-analysis.tsx` | Análise regional |
| `ReportScheduler` | `report-scheduler/report-scheduler.tsx` | Agendador de relatórios |
| `AdvancedReportExporter` | `reports/advanced-report-exporter.tsx` | Exportador avançado de relatórios |
| `RubricEvaluationCard` | `rubric-evaluation-card.tsx` | Card de avaliação por rubrica |
| `ScoreBreakdownBadge` | `score/ScoreBreakdownBadge.tsx` | Badge de breakdown de score |
| `TemplateSuggestionToast` | `template-suggestion-toast.tsx` | Toast de sugestão de template |
| `TestStatusIndicators` | `test-status-indicators.tsx` | Indicadores de status de teste |
| `TimelineSection` | `timeline-section.tsx` | Seção de timeline |
| `UserCommandsSection` | `user-commands-section.tsx` | Seção de comandos do usuário |
| `WarRoom` | `war-room.tsx` | Sala de guerra (monitoramento) |
| `WorkModelCharts` | `work-model-charts.tsx` | Gráficos de modelo de trabalho |
| `CandidatePage` | `candidate-page.tsx` | Página completa do candidato (wrapper) |
| `CandidatePreview` | `candidate-preview.tsx` | Preview lateral do candidato |
| `ExpandableAIPrompt` | `expandable-ai-prompt.tsx` | Prompt expansível IA (wrapper root) |
| `InterviewsSection` | `interviews-section.tsx` | Seção de entrevistas |
| `MLInsightsCard` | `ml-insights-card.tsx` | Card de insights de Machine Learning |

---

## 13R. EXPANDABLE AI PROMPT (`components/expandable-ai-prompt/`)

- **Diretório:** `plataforma-lia/src/components/expandable-ai-prompt/`
- **Arquivos:** 8 root + 7 em `tabs/`

| Arquivo | Descrição |
|---------|-----------|
| `EAPModals.tsx` | Modais do prompt expansível |
| `EAPTabContent.tsx` | Conteúdo de tabs do prompt |
| `useArchetypeHandlers.ts` | Handlers de arquétipos |
| `useEAPCallbacks.tsx` | Callbacks do EAP |
| `useEAPCallbacksTypes.ts` | Types dos callbacks |
| `useEAPEffects.tsx` | Effects do EAP |
| `useExpandableAIPromptCore.tsx` | Core hook do prompt expansível |

**Sub-diretório `tabs/`:**

| Arquivo | Descrição |
|---------|-----------|
| `EAPTabArquetipos.tsx` | Tab de arquétipos |
| `EAPTabBoolean.tsx` | Tab de busca booleana |
| `EAPTabFiltros.tsx` | Tab de filtros |
| `EAPTabJobDescription.tsx` | Tab de job description |
| `EAPTabNatural.tsx` | Tab de busca em linguagem natural |
| `EAPTabSimilar.tsx` | Tab de perfis similares |
| `index.ts` | Re-exports |

---

## 13S. EMAIL TEMPLATES

- **Diretório:** `plataforma-lia/src/components/email-templates/`

| Componente | Descrição |
|-----------|-----------|
| `EmailTemplatesManager` | Gerenciador de templates de email |
| `EmailTemplateFormModal` | Modal de formulário de template |
| `SendEmailModal` | Modal de envio de email |
| `ReportEmailTemplates` | Templates de email de relatório |

---

## 13T. COMMUNICATION

- **Diretório:** `plataforma-lia/src/components/communication/`
- **Componente:** `MessageComposer` (`message-composer.tsx`) — Compositor de mensagens unificado

---

## 13U. INTERVIEW NOTES

- **Diretório:** `plataforma-lia/src/components/interview-notes/`

| Componente | Descrição |
|-----------|-----------|
| `InterviewNoteCard` | Card de nota de entrevista |
| `CreateAdhocNoteModal` | Modal para criar nota ad-hoc |
| `NextStepModal` | Modal de próximo passo |
| `ScheduledInterviewActivityCard` | Card de atividade de entrevista agendada |
| `ScoreCardWSI` | Scorecard WSI |
| `TeamsAnalysisPanel` | Painel de análise de times |

---

## 13V. JOB CREATION (Wizard Inputs)

- **Diretório:** `plataforma-lia/src/components/job-creation/`

| Componente | Descrição |
|-----------|-----------|
| `CompensationAnalysisPanel` | Painel de análise de remuneração |
| `CompensationChatMessage` | Mensagem de chat de remuneração |
| `CompetenciesChatMessage` | Mensagem de chat de competências |
| `ConfidenceIndicator` | Indicador de confiança |
| `FieldOriginBadge` | Badge de origem do campo |
| `FinalReviewPanel` | Painel de revisão final |
| `ScreeningQuestionsPanel` | Painel de perguntas de triagem |
| `VacancyFullSummary` | Resumo completo da vaga |
| `VacancySearchResults` | Resultados de busca de vagas |

---

## 13W. JOB DESCRIPTION

- **Diretório:** `plataforma-lia/src/components/job-description/`

| Componente | Descrição |
|-----------|-----------|
| `JobDescriptionFinal` | Descrição final da vaga |
| `JobDescriptionPreview` | Preview da descrição |

---

## 13X. BENEFITS

- **Diretório:** `plataforma-lia/src/components/benefits/`

| Componente | Descrição |
|-----------|-----------|
| `BenefitBadgeList` | Lista de badges de benefícios |
| `BenefitDetailsSheet` | Sheet de detalhes do benefício |

---

## 13Y. AI COMPONENTS

- **Diretório:** `plataforma-lia/src/components/ai/`

| Componente | Descrição |
|-----------|-----------|
| `AgentExplainabilityPanel` | Painel de explicabilidade do agente |
| `AISuggestionBadge` | Badge de sugestão da IA |

---

## 13Z. QUICK ACTIONS

- **Diretório:** `plataforma-lia/src/components/quick-actions/`

| Componente | Descrição |
|-----------|-----------|
| `BatchActionModal` | Modal de ação em lote |
| `ContactModal` | Modal de contato |
| `QuickViewModal` | Modal de quick view |
| `ScheduleModal` | Modal de agendamento |

---

## 13AA. UI ACTIONS / SIDE PANELS

- **Diretório:** `plataforma-lia/src/components/ui-actions/`

| Componente | Descrição |
|-----------|-----------|
| `SidePanelContainer` | Container de side panel |
| `CompanyBenefitsSummaryCard` | Card de resumo de benefícios da empresa |
| + `cards/` e `panels/` | Sub-diretórios com cards e panels adicionais |

---

## 13AB. TALENT FUNNEL TABS

- **Diretório:** `plataforma-lia/src/components/talent-funnel-tabs/`

| Componente | Descrição |
|-----------|-----------|
| `FavoritesTab` | Tab de favoritos |
| `HistoryTab` | Tab de histórico |
| `ListsTab` | Tab de listas |
| `SavedSearchesTab` | Tab de buscas salvas |

---

## 13AC. ALERTS

- **Diretório:** `plataforma-lia/src/components/alerts/`

| Componente | Descrição |
|-----------|-----------|
| `AlertSettingsModal` | Modal de configuração de alertas |
| `KPIAlertSystem` | Sistema de alertas KPI |

---

## 13AD. ONBOARDING

- **Diretório:** `plataforma-lia/src/components/onboarding/`

| Componente | Descrição |
|-----------|-----------|
| `FirstAccessManager` | Gerenciador de primeiro acesso |
| `OnboardingController` | Controlador do onboarding |
| `OnboardingReplayButton` | Botão para replay do onboarding |

---

## 14. PÁGINAS ADICIONAIS

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
| Chat LIA | `pages/chat-page.tsx` + `pages/chat-page/` | `ChatPage` |
| Tasks MVP | `pages/tasks-page-mvp.tsx` | `TasksPageMVP` |
| Tasks | `pages/tasks-page.tsx` | `TasksPage` |

### 14.1 Sub-dashboards (`pages/dashboards-page/`)

| Componente | Descrição |
|-----------|-----------|
| `AgentActivityDashboard` | Dashboard de atividade de agentes |
| `AnaliseCompetenciasPlaceholder` | Placeholder de análise de competências |
| `BigFiveAnalyticsDashboard` | Dashboard de analytics Big Five |
| `DiversidadeInclusaoDashboard` | Dashboard de diversidade e inclusão |
| `FunilPerformancePlaceholder` | Placeholder de performance do funil |
| `IndicadoresEstrategicosPlaceholder` | Placeholder de indicadores estratégicos |
| `ModelosTrabalhoPlaceholder` | Placeholder de modelos de trabalho |
| `NPSDashboard` | Dashboard de NPS |
| `PeopleAnalyticsPlaceholder` | Placeholder de People Analytics |
| `PrevisoesIAPlaceholder` | Placeholder de previsões IA |
| `VoiceScreeningDashboard` | Dashboard de voice screening |
| `WarRoomOperacionalPlaceholder` | Placeholder de war room operacional |

### 14.2 Indicadores (`pages/indicators/`) — 10 arquivos

| Arquivo | Descrição |
|---------|-----------|
| `indicators.constants.ts` | Constantes de indicadores |
| `indicators.types.ts` | Tipos de indicadores |
| `useIndicatorsPage.ts` | Hook principal da página |

**Sub-diretório `tabs/`:**

| Arquivo | Descrição |
|---------|-----------|
| `AgentControlTab.tsx` | Tab de controle de agentes |
| `AlertsTab.tsx` | Tab de alertas |
| `PredictionsTab.tsx` | Tab de predições |
| `RecruitersTab.tsx` | Tab de recrutadores |
| `StrategicTab.tsx` | Tab estratégica |
| `WorkModelsTab.tsx` | Tab de modelos de trabalho |

### 14.3 ATS Integrations (`pages/ats-integrations/`) — 5 arquivos

| Arquivo | Descrição |
|---------|-----------|
| `ats-integrations.constants.ts` | Constantes de integrações ATS |
| `ats-integrations.types.ts` | Tipos de integrações ATS |
| `index.ts` | Re-exports |
| `SystemConfigurationModal.tsx` | Modal de configuração do sistema ATS |
| `useAtsIntegrations.ts` | Hook de gestão de integrações |

### 14.4 Jobs Page Sub-componentes (`pages/jobs/`) — 30 arquivos

**Root (12 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `ColumnConfigPanel.tsx` | Painel de configuração de colunas |
| `index.ts` | Re-exports |
| `InlineChatPanel.tsx` | Painel de chat inline |
| `JobPreviewPanel.tsx` | Painel de preview da vaga |
| `JobsCompactTableView.tsx` | Visão compacta da tabela |
| `JobsDashboardView.tsx` | Visão dashboard das vagas |
| `JobsHeader.tsx` | Header da página de vagas |
| `JobsModalsSection.tsx` | Seção de modais de vagas |
| `JobsTable.tsx` | Tabela de vagas |
| `TableFiltersPanel.tsx` | Painel de filtros da tabela |
| `types.ts` | Tipos da página de vagas |
| `WSITutorialModal.tsx` | Modal de tutorial WSI |

**Sub-diretório `hooks/` (10 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `useJobsBulkActions.ts` | Ações em lote de vagas |
| `useJobsChat.ts` | Chat inline de vagas |
| `useJobsData.ts` | Dados de vagas |
| `useJobSelection.ts` | Seleção de vagas |
| `useJobsFilters.ts` | Filtros de vagas |
| `useJobsPageCore.ts` | Core hook da página |
| `useJobsPreview.ts` | Preview de vagas |
| `useJobsQuery.ts` | Queries de vagas |
| `useJobsTableColumns.ts` | Colunas da tabela |
| `useJobsTableConfig.ts` | Configuração da tabela |

### 14.5 Kanban Page Sub-componentes (`pages/job-kanban/`) — 56 arquivos

**Root (27 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `AddColumnPopover.tsx` | Popover para adicionar coluna |
| `index.ts` | Re-exports |
| `KanbanCandidatePreviewPanel.tsx` | Preview lateral do candidato |
| `KanbanCard.tsx` | Card do candidato no kanban |
| `KanbanCardActions.tsx` | Ações no card |
| `KanbanCardInterviewButtons.tsx` | Botões de entrevista |
| `KanbanCardScores.tsx` | Scores no card |
| `KanbanCardStatusBadges.tsx` | Badges de status |
| `KanbanColumn.tsx` | Coluna do kanban |
| `KanbanColumnConfigPanel.tsx` | Configuração de colunas |
| `KanbanColumnRenderer.tsx` | Renderizador de coluna |
| `KanbanFiltersPanel.tsx` | Painel de filtros |
| `KanbanJobHeader.tsx` | Header da vaga |
| `KanbanLIASidebar.tsx` | Sidebar LIA |
| `KanbanPageModals.tsx` | Container de modais |
| `KanbanTableCellRenderer.tsx` | Renderizador de célula |
| `KanbanTableFiltersPanel.tsx` | Filtros da visão tabela |
| `KanbanTablePagination.tsx` | Paginação da tabela |
| `KanbanTableView.tsx` | Visão tabela do kanban |
| `KanbanToolbar.tsx` | Toolbar com filtros e ações |
| `LIAQuestionsPanel.tsx` | Painel de perguntas LIA |
| `LIASuggestionsPanel.tsx` | Painel de sugestões LIA |
| `MoveConfirmationModal.tsx` | Modal de confirmação de movimentação |
| `TestHistoryModal.tsx` | Modal de histórico de testes |
| `TestLibraryModal.tsx` | Modal de biblioteca de testes |
| `TestPreviewModal.tsx` | Modal de preview de teste |
| `types.ts` | Tipos do kanban |

**Sub-diretório `hooks/` (19 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `useKanbanBulkActions.ts` | Ações em lote |
| `useKanbanCandidateDecisions.ts` | Decisões de candidatos |
| `useKanbanCandidateHandlers.ts` | Handlers de candidatos |
| `useKanbanCandidateLoader.ts` | Loader de candidatos |
| `useKanbanColumnConfig.ts` | Configuração de colunas |
| `useKanbanDragDrop.ts` | Drag and drop |
| `useKanbanFilters.ts` | Filtros do kanban |
| `useKanbanFilters.test.ts` | Testes de filtros |
| `useKanbanJobEditing.ts` | Edição de vaga |
| `useKanbanLIAHandlers.ts` | Handlers LIA |
| `useKanbanLIASuggestions.ts` | Sugestões LIA |
| `useKanbanNavigation.ts` | Navegação do kanban |
| `useKanbanPageCore.ts` | Core hook da página |
| `useKanbanPublishing.ts` | Publicação de vaga |
| `useKanbanState.ts` | Estado do kanban |
| `useKanbanTableView.ts` | Visão tabela |
| `useKanbanTransitionHandlers.ts` | Handlers de transição |
| `useKanbanTransitions.ts` | Transições de etapa |
| `useKanbanUIModals.ts` | Modais de UI |

**Sub-diretório `sections/` (3 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `index.ts` | Re-exports |
| `KanbanEmptyState.tsx` | Estado vazio do kanban |
| `KanbanLoadingState.tsx` | Estado de loading |

**Sub-diretório `utils/` (3 arquivos + __tests__):**

| Arquivo | Descrição |
|---------|-----------|
| `kanbanHelpers.ts` | Helpers do kanban |
| `kanbanStageUtils.ts` | Utilitários de stages |

### 14.6 Candidates Page Sub-componentes (`pages/candidates/`) — 81 arquivos

**Root (37 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `ActiveFiltersBadge.tsx` | Badge de filtros ativos |
| `CandidatePreviewPanel.tsx` | Painel de preview |
| `CandidatePreviewSidePanel.tsx` | Side panel de preview |
| `CandidateSearchBar.tsx` | Barra de busca de candidatos |
| `CandidateSearchResultsView.tsx` | View de resultados de busca |
| `CandidateSearchResultsView.types.ts` | Tipos da view de resultados |
| `CandidatesFilterPanel.tsx` | Painel de filtros |
| `CandidatesHeader.tsx` | Header da página |
| `CandidatesLoadMoreFooter.tsx` | Footer de "carregar mais" |
| `CandidatesPageHeader.tsx` | Header da página (alternativo) |
| `CandidatesPageModals.tsx` | Container de modais |
| `CandidatesPageModals.types.ts` | Tipos dos modais |
| `CandidatesTableArea.tsx` | Área da tabela |
| `CandidatesTable.tsx` | Tabela de candidatos |
| `CandidateTableCellRenderer.tsx` | Renderizador de célula |
| `CandidateTabs.tsx` | Tabs de candidatos |
| `ColumnConfigSidebar.tsx` | Sidebar de configuração de colunas |
| `CompactLIAPrompt.tsx` | Prompt LIA compacto |
| `ContactFilterConfirmModal.tsx` | Modal de confirmação de filtro de contato |
| `CreditConfirmationModal.tsx` | Modal de confirmação de créditos |
| `CrossTabFilterBanner.tsx` | Banner de filtro cross-tab |
| `DeleteArchetypeModal.tsx` | Modal de exclusão de arquétipo |
| `EditQueryModal.tsx` | Modal de edição de query |
| `GlobalExpansionConfirmModal.tsx` | Modal de expansão global |
| `index.ts` | Re-exports |
| `LIASearchSidebar.tsx` | Sidebar de busca LIA |
| `PreviewSuggestionModal.tsx` | Modal de preview de sugestão |
| `SaveAsArchetypeModal.tsx` | Modal de salvar como arquétipo |
| `SearchControlsBar.tsx` | Barra de controles de busca |
| `SearchResultsHeader.tsx` | Header de resultados de busca |
| `SourceChangeConfirmModal.tsx` | Modal de mudança de fonte |
| `types.ts` | Tipos gerais |
| `useCandidatesExecuteSearch.ts` | Hook de execução de busca |
| `ViewingListBanner.tsx` | Banner de "visualizando lista" |

**Sub-diretório `cells/` (4 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `ContactCells.tsx` | Células de contato |
| `PearchCells.tsx` | Células de Pearch |
| `ScoreCells.tsx` | Células de score |
| `SourceCell.tsx` | Célula de fonte |

**Sub-diretório `filters/` (4 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `CheckableItem.tsx` | Item selecionável |
| `TagInput.tsx` | Input de tags |
| `TriStateButtons.tsx` | Botões tri-state |
| `types.ts` | Tipos de filtros |

**Sub-diretório `hooks/` (18 + 5 em candidates-core):**

| Arquivo | Descrição |
|---------|-----------|
| `liaMessageUtils.ts` | Utilitários de mensagens LIA |
| `useCandidatesActions.ts` | Ações de candidatos |
| `useCandidatesArchetypes.ts` | Arquétipos de candidatos |
| `useCandidatesColumnConfig.ts` | Configuração de colunas |
| `useCandidatesCVHandlers.ts` | Handlers de CV |
| `useCandidatesExecuteSearch.ts` | Execução de busca |
| `useCandidatesFilterSort.ts` | Filtros e ordenação |
| `useCandidatesInteractions.ts` | Interações com candidatos |
| `useCandidatesLIAHandlers.ts` | Handlers LIA |
| `useCandidatesNavigation.ts` | Navegação |
| `useCandidatesPageCore.tsx` | Core hook da página |
| `useCandidatesQuery.ts` | Queries de candidatos |
| `useCandidatesSearch.ts` | Busca de candidatos |
| `useCandidatesSelection.ts` | Seleção de candidatos |
| `useCandidatesTableConfig.ts` | Configuração da tabela |
| `useCandidatesUIState.ts` | Estado de UI |
| `useRevealContact.tsx` | Reveal de contato |
| `candidates-core/` | `useCandidatesData.ts`, `useCandidatesFilters.ts`, types, constants, index |

**Sub-diretório `lia-sidebar/` (9 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `index.ts` | Re-exports |
| `LIASearchSidebarChat.tsx` | Chat da sidebar LIA |
| `LIASearchSidebarInput.tsx` | Input da sidebar LIA |
| `lia-sidebar-types.ts` | Tipos da sidebar |
| `mapCandidates.ts` | Mapeamento de candidatos |
| `TabBoolean.tsx` | Tab de busca booleana |
| `TabFiltros.tsx` | Tab de filtros |
| `TabJobDescription.tsx` | Tab de job description |
| `TabSimilar.tsx` | Tab de perfis similares |

**Sub-diretório `__tests__/` (2 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `CandidatesPageHeader.test.tsx` | Testes do header |
| `CandidatesTable.test.tsx` | Testes da tabela |

### 14.7 Chat Page Sub-componentes (`pages/chat-page/`) — 18 arquivos

**Root (4 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `constants.ts` | Constantes da página de chat |
| `types.ts` | Tipos da página de chat |
| `useChatPageCore.tsx` | Core hook da página |
| `useChatPageHandlers.tsx` | Handlers da página |

**Sub-diretório `chat-core/` (5 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `chat-core.constants.ts` | Constantes do core de chat |
| `chat-core.types.ts` | Tipos do core |
| `index.ts` | Re-exports |
| `useChatMessages.ts` | Hook de mensagens |
| `useChatSession.ts` | Hook de sessão de chat |

**Sub-diretório `constants/` (7 arquivos):**

| Arquivo | Descrição |
|---------|-----------|
| `conversations.test.ts` | Testes de conversas |
| `empty-conversations.ts` | Conversas vazias (defaults) |
| `index.ts` | Re-exports |
| `modern-conversations-part2.ts` | Conversas modernas parte 2 |
| `modern-conversations.ts` | Conversas modernas |
| `prompts.ts` | Prompts de chat |
| `ui.ts` | Constantes de UI |

### 14.8 Tasks Page Sub-componentes (`pages/tasks/`) — 2 arquivos

| Arquivo | Descrição |
|---------|-----------|
| `ActiveAlertsCard.tsx` | Card de alertas ativos |
| `TaskCard.tsx` | Card de tarefa |

---

### 14.9 Hooks Completos (`hooks/`) — 102 arquivos root

| Grupo | Arquivo | Descrição |
|-------|---------|-----------|
| **Candidatos** | `use-candidate-compare.ts` | Comparação de candidatos |
| | `use-candidate-data-requests.ts` | Solicitação de dados |
| | `use-candidate-filters.ts` | Filtros de candidatos |
| | `use-candidate-selection.ts` | Seleção de candidato |
| | `use-candidates-list.ts` | Lista de candidatos |
| | `use-candidates-list-mapped.ts` | Lista mapeada |
| | `use-candidates-search-state.ts` | Estado de busca |
| | `useCandidateSuggestions.ts` | Sugestões de candidatos |
| | `use-candidates-view-state.ts` | Estado da view |
| | `use-similar-profiles.ts` | Perfis similares |
| | `use-short-list.ts` | Short list |
| **Chat/LIA** | `use-chat-file-handling.ts` | Upload de arquivos no chat |
| | `useChatLayout.ts` | Layout do chat |
| | `use-chat-page-state.ts` | Estado da página de chat |
| | `use-chat-search.ts` | Busca no chat |
| | `use-float-conversation.ts` | Conversa flutuante LIA |
| | `use-float-streaming.ts` | Streaming flutuante |
| | `use-lia-suggestions.ts` | Sugestões LIA |
| | `use-interpret-context.ts` | Interpretação de contexto |
| | `use-action-intent.ts` | Intenção de ação |
| | `use-agent-streaming.ts` | Streaming de agente |
| | `useAgentMemory.ts` | Memória do agente |
| **Empresa** | `use-company-culture.ts` | Cultura da empresa |
| | `use-company-defaults.ts` | Defaults da empresa |
| | `use-company-eligibility-questions.ts` | Perguntas de elegibilidade |
| | `use-company-lia-instructions.ts` | Instruções LIA da empresa |
| | `use-company-managers.ts` | Gestores da empresa |
| | `use-company-pipeline.ts` | Pipeline da empresa |
| | `useCompanyBenefits.ts` | Benefícios da empresa |
| | `useCompanySkillsCatalog.ts` | Catálogo de skills |
| | `use-company-tech-stack.ts` | Tech stack |
| | `use-current-company.ts` | Empresa atual |
| | `use-current-scope.ts` | Escopo atual |
| | `use-clients.ts` | Clientes |
| **Vagas** | `use-job-analytics.ts` | Analytics de vagas |
| | `useJobColumnConfig.ts` | Config de colunas de vagas |
| | `use-job-draft.ts` | Rascunho de vaga |
| | `useJobFiltersPersistence.ts` | Persistência de filtros |
| | `use-job-report.ts` | Relatório de vaga |
| | `use-job-wizard-backend.ts` | Backend do wizard |
| | `use-wizard-auto-save.ts` | Auto-save do wizard |
| | `use-wizard-suggestions.ts` | Sugestões do wizard |
| **Recrutamento** | `use-recruitment-stages.ts` | Etapas de recrutamento |
| | `use-pipeline-inheritance.ts` | Herança de pipeline |
| | `use-hiring-policies.ts` | Políticas de contratação |
| | `use-screening-questions.ts` | Perguntas de screening |
| | `useScreeningConfig.ts` | Configuração de screening |
| | `use-override-approve.ts` | Override de aprovação |
| | `use-sub-status-panel.ts` | Painel de sub-status |
| | `use-transition-context.ts` | Contexto de transição |
| **Busca/ML** | `use-search-autocomplete.ts` | Autocomplete de busca |
| | `use-search-entities.ts` | Entidades de busca |
| | `useSearchFlow.ts` | Fluxo de busca |
| | `use-search-source.ts` | Fonte de busca |
| | `useSemanticSearch.ts` | Busca semântica |
| | `use-ml-predictions.ts` | Predições ML |
| | `use-archetypes.ts` | Arquétipos |
| **IA/Créditos** | `use-ai-consumption.ts` | Consumo de IA |
| | `use-ai-credits.ts` | Créditos de IA |
| | `useCreditEstimator.ts` | Estimador de créditos |
| | `useFastTrack.ts` | Fast track |
| | `use-bias-audit-report.ts` | Relatório de auditoria de bias |
| **UI/Navegação** | `use-bulk-selection.ts` | Seleção em lote |
| | `use-keyboard-shortcuts.ts` | Atalhos de teclado |
| | `use-navigation-intent.ts` | Intenção de navegação |
| | `use-navigation-persistence.ts` | Persistência de navegação |
| | `use-recent-items.ts` | Itens recentes |
| | ~~`use-toast.ts`~~ | ~~Removido — usar `import { toast } from "sonner"` direto~~ |
| | `useTableFeatures.ts` | Features da tabela |
| | `useUIActions.ts` | Ações de UI |
| | `useUnifiedSearch.ts` | Busca unificada |
| | `useUnsavedChanges.ts` | Alterações não salvas |
| | `useHideViewedCandidates.ts` | Ocultar candidatos vistos |
| **Dados/Métricas** | `use-daily-briefing.ts` | Briefing diário |
| | `use-data-request-config.ts` | Config de solicitação de dados |
| | `use-data-request-modals.ts` | Modais de solicitação |
| | `use-saas-metrics.ts` | Métricas SaaS |
| | `use-score-breakdown.ts` | Breakdown de score |
| | `use-talent-funnel.ts` | Funil de talentos |
| | `use-workforce-planning.ts` | Planejamento de workforce |
| | `use-workos-metrics.ts` | Métricas WorkOS |
| | `use-job-analytics.ts` | Analytics de vagas |
| **Comunicação** | `use-communication-templates.ts` | Templates de comunicação |
| | `use-template-suggestions.ts` | Sugestões de templates |
| | `use-triagem-chat.ts` | Chat de triagem |
| | `use-return-events.ts` | Eventos de retorno |
| **Settings/Config** | `useSettingsForm.ts` | Formulário de settings |
| | `useSettingsNavigation.ts` | Navegação de settings |
| | `use-scim-config.ts` | Configuração SCIM |
| | `useGlobalSearchSettings.ts` | Settings de busca global |
| | `use-edit-lock.tsx` | Lock de edição |
| | `use-empty-field-notifications.ts` | Notificações de campo vazio |
| **Sessão/Auth** | `useSessionRefresh.ts` | Refresh de sessão |
| | `useSessionTimeout.ts` | Timeout de sessão |
| | `use-wsi-async.ts` | WSI assíncrono |
| **Alerts/Insights** | `use-proactive-alerts.ts` | Alertas proativos |
| | `use-proactive-insights.ts` | Insights proativos |
| | `use-notifications.ts` | Notificações |
| **Prompt/Estado** | `usePromptState.ts` | Estado do prompt |
| | `useDynamicSuggestions.ts` | Sugestões dinâmicas |
| | `promptStateCriteriaUtils.ts` | Utilitários de critérios |
| | `useTagInputState.ts` | Estado de tag input (T003) |
| **Extras** | `index.ts` | Re-exports |

**Sub-diretórios de hooks:**
- `hooks/admin/` — hooks administrativos
- `hooks/settings/` — hooks de settings
- `hooks/__tests__/` — testes de hooks

---

## 15. CLASSES CSS UTILITÁRIAS CUSTOMIZADAS

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

## 16. RESUMO DE ÍCONES POR ÁREA

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

## 17. MATRIZ DE ESTADOS POR TELA

### 17.1 Vagas (Lista)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Loading | Skeleton rows (animate-pulse) | `Skeleton` rows |
| Empty (sem vagas) | `EmptyState` centralizado | Ícone `Briefcase`, "Nenhuma vaga encontrada" |
| Loaded | Tabela com dados | `Table` + `TableRow` por vaga |
| Filtered (sem resultados) | `EmptyState` com filtro ativo | Mensagem de filtro |
| Error (API fail) | Toast error | `toast.error("...")` (Sonner) |

### 17.2 Kanban (Gestão da Vaga)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Loading | Skeleton columns | `LoadingCard` x N |
| Empty column | `EmptyState` na coluna | "Nenhum candidato nesta etapa" |
| Populated | Cards nas colunas | `KanbanCard` por candidato |
| Dragging | Card elevado + shadow | Cursor `grabbing`, border highlight |
| Drop target | Border highlight na coluna | `border-cyan-300` (destino válido) |
| Candidate preview | Side panel slide-in | `slideInFromRight` animation |
| Bulk selection | Bottom bar visible | `UnifiedBulkActionsBar` slide-up |
| Error | Toast error | `toast.error("...")` (Sonner) |

### 17.3 Funil de Talentos
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

### 17.4 Configurações da Vaga
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

### 17.5 Modais (padrão geral)
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Closed | Invisível | — |
| Opening | Overlay fade-in + content zoom-in | `bg-black/30 backdrop-blur-[1px]`, `scaleIn` |
| Open (idle) | Formulário visível | `DialogContent` |
| Submitting | Botão com loader, campos disabled | `Loader2` no botão, `disabled:opacity-50` |
| Success | Toast + modal fecha | `Toast variant="success"` |
| Error | Inline error ou toast | `text-red-500` ou `Toast variant="destructive"` |
| Closing | Content zoom-out + overlay fade-out | Reverse animations |

### 17.6 Sidebar
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Expanded | Full width (~240px) | Labels visíveis |
| Collapsed | Icon-only (~48px) | Tooltips nos ícones |
| Item active | Background highlight + left border | `bg-gray-100` + `border-l-2 border-gray-900` |
| Item hover | Background subtle | `hover:bg-gray-50` |
| Item locked | Opacity + lock icon | `Lock` icon, `opacity-60` |
| Sub-menu open | Expandido com items filhos | `ChevronDown/Up` toggle |

### 17.7 TopBar
| Estado | Visual | Componente/Estilo |
|--------|--------|-------------------|
| Default | Avatar + Bell | — |
| Notifications open | Panel dropdown | `NotificationSystem` |
| Has notifications | Badge counter vermelho | — |
| User menu open | `DropdownMenu` | Lista de ações |
| Password modal open | `Dialog` | 3 inputs + validação |

---

## 18. MAPEAMENTO REACT → VUETIFY 3 (Correspondência por Componente)

> Referência para conversão futura. Stack alvo: **Vue 3 + Vuetify 3 + Nuxt 3 + Pinia**.
> Skill de preparação: `.agents/skills/vue-migration-prep/SKILL.md`
> Plano de migração: `plataforma-lia/docs/design-system/VUETIFY-MIGRATION-PLAN.md`

### 18.1 Componentes Base — shadcn/ui → Vuetify 3

| # | Componente React (shadcn) | Arquivo Atual | Vuetify 3 Equivalente | Notas de Conversão |
|---|--------------------------|---------------|----------------------|-------------------|
| 1 | `Button` | `ui/button.tsx` | `<v-btn>` | `variant="default"` → `color="grey-darken-4" variant="flat"`. `variant="outline"` → `variant="outlined"`. `variant="ghost"` → `variant="text"`. `variant="destructive"` → `color="error"`. `size="sm"` → `size="small"`. `size="icon"` → `icon` prop. |
| 2 | `Badge` | `ui/badge.tsx` | `<v-chip>` | `variant="default"` → `size="small" color="grey-darken-4"`. `variant="outline"` → `variant="outlined"`. `variant="secondary"` → `color="grey-lighten-3"`. |
| 3 | `Card` / `CardHeader` / `CardContent` / `CardFooter` | `ui/card.tsx` | `<v-card>` / `<v-card-title>` / `<v-card-text>` / `<v-card-actions>` | `variant="outlined"` no Vuetify. `rounded="md"`. |
| 4 | `Input` | `ui/input.tsx` | `<v-text-field>` | `variant="outlined"` + `density="compact"`. `text-[11px]` → custom CSS `font-size: 11px`. |
| 5 | `Textarea` | `ui/textarea.tsx` | `<v-textarea>` | `variant="outlined"` + `density="compact"`. `rows` prop direto. |
| 6 | `Select` / `SelectTrigger` / `SelectContent` / `SelectItem` | `ui/select.tsx` | `<v-select>` | `variant="outlined"` + `density="compact"`. `:items` array. `item-title` + `item-value`. |
| 7 | `Checkbox` | `ui/checkbox.tsx` | `<v-checkbox>` | `color="grey-darken-4"`. `density="compact"`. |
| 8 | `Switch` | `ui/switch.tsx` | `<v-switch>` | `color="grey-darken-4"`. `density="compact"`. |
| 9 | `Tabs` / `TabsList` / `TabsTrigger` / `TabsContent` | `ui/tabs.tsx` | `<v-tabs>` + `<v-tab>` + `<v-tabs-window>` + `<v-tabs-window-item>` | `color="grey-darken-4"`. `slider-color="grey-darken-4"`. |
| 10 | `Dialog` / `DialogContent` / `DialogHeader` / `DialogTitle` / `DialogFooter` | `ui/dialog.tsx` | `<v-dialog>` + `<v-card>` (dentro) | `max-width` como prop. `<v-card-title>` = header. `<v-card-actions>` = footer. `persistent` para modais blocking. |
| 11 | `Sheet` / `SheetContent` / `SheetHeader` | `ui/sheet.tsx` | `<v-navigation-drawer>` `temporary` | `location="right"` para side panel. `width="400"`. |
| 12 | `Table` / `TableHeader` / `TableRow` / `TableCell` | `ui/table.tsx` | `<v-data-table>` | `:headers` + `:items`. Slots personalizados via `#item.campo`. Sorting/pagination built-in. |
| 13 | `Avatar` / `AvatarFallback` | `ui/avatar.tsx` | `<v-avatar>` | `size="40"`. Fallback via slot default com iniciais. `color="grey-lighten-3"`. |
| 14 | `Tooltip` / `TooltipTrigger` / `TooltipContent` | `ui/tooltip.tsx` | `<v-tooltip>` | `location="top"`. Trigger via `activator` slot. |
| 15 | `DropdownMenu` / `DropdownMenuTrigger` / `DropdownMenuContent` / `DropdownMenuItem` | `ui/dropdown-menu.tsx` | `<v-menu>` + `<v-list>` + `<v-list-item>` | Trigger via `activator` slot. `<v-list-item-title>` para texto. `<v-divider>` para separadores. |
| 16 | `Progress` | `ui/progress.tsx` | `<v-progress-linear>` | `color="grey-darken-4"`. `:model-value` para %. `height="8"`. |
| 17 | `Skeleton` | `ui/skeleton.tsx` | `<v-skeleton-loader>` | `type="text"`, `type="avatar"`, `type="card"`, etc. |
| 18 | `Accordion` / `AccordionItem` / `AccordionTrigger` / `AccordionContent` | `ui/accordion.tsx` | `<v-expansion-panels>` + `<v-expansion-panel>` | `variant="accordion"`. `<v-expansion-panel-title>` + `<v-expansion-panel-text>`. |
| 19 | `AlertDialog` / `AlertDialogAction` / `AlertDialogCancel` | `ui/alert-dialog.tsx` | `<v-dialog>` + `<v-card>` (confirmação) | `max-width="500"`. `persistent`. Botões em `<v-card-actions>`. |
| 20 | `Collapsible` / `CollapsibleTrigger` / `CollapsibleContent` | `ui/collapsible.tsx` | `<v-expand-transition>` + `v-show` | Sem equivalente direto — usar transition + toggle manual. |
| 21 | `Label` | `ui/label.tsx` | Vuetify labels integrados nos inputs | `<v-text-field label="...">`. Para labels avulsos: `<label class="text-caption">`. |
| 22 | `Popover` / `PopoverTrigger` / `PopoverContent` | `ui/popover.tsx` | `<v-menu>` | `location="bottom"`. `close-on-content-click="false"`. Content via default slot. |
| 23 | `RadioGroup` / `RadioGroupItem` | `ui/radio-group.tsx` | `<v-radio-group>` + `<v-radio>` | `color="grey-darken-4"`. `density="compact"`. |
| 24 | `ScrollArea` | `ui/scroll-area.tsx` | CSS nativo ou `<v-virtual-scroll>` | Vuetify não tem ScrollArea equivalente — usar `overflow-y: auto` com estilização customizada do scrollbar. |
| 25 | `Separator` | `ui/separator.tsx` | `<v-divider>` | Horizontal por padrão. `vertical` prop. `class="my-2"`. |
| 26 | `Slider` | `ui/slider.tsx` | `<v-slider>` | `color="grey-darken-4"`. `thumb-size="20"`. `track-size="4"`. |
| 27 | `Toast` / `Toaster` | `ui/toast.tsx` + `ui/toaster.tsx` | `<v-snackbar>` | `location="bottom right"`. `color` por variant: default → nenhum, destructive → `"error"`, success → `"success"`, warning → `"warning"`, info → `"info"`. |
| 28 | `Command` / `CommandDialog` / `CommandInput` | `ui/command.tsx` | `<v-dialog>` + `<v-text-field>` + `<v-list>` customizado | Sem equivalente direto — implementar command palette com dialog + search + list filtrada. |
| 29 | `CommandPalette` | `ui/command-palette.tsx` | `<v-dialog>` + busca + `<v-list>` | Componente customizado necessário. Atalho Ctrl+K mantido via `@keydown`. |

### 18.2 Componentes Especializados — Conversão

| # | Componente React | Vuetify 3 Equivalente | Complexidade | Notas |
|---|-----------------|----------------------|-------------|-------|
| 1 | `StatusBadge` | `<v-chip>` customizado | Média | 8 variants com cores pastéis — definir como componente Vue com prop `variant`. Cores via CSS variables. |
| 2 | `ScoreIconButton` | `<v-btn icon>` customizado | Média | 6 ícones SVG customizados. Manter como componente Vue com prop `scoreType`. |
| 3 | `CandidateCard` | `<v-card>` customizado | Alta | Avatar + badges + scores. Compor com `<v-avatar>`, `<v-chip>`, `<v-btn>`. |
| 4 | `EmptyState` | Componente customizado | Baixa | Sem equivalente Vuetify. `<v-card variant="flat">` + ícone + texto. |
| 5 | `AudioPlayer` | Componente customizado | Alta | Sem equivalente Vuetify. Manter implementação HTML5 Audio. |
| 6 | `BigFiveProfile` | Componente customizado | Alta | Radar chart — manter lib de charts (Chart.js ou similar). |
| 7 | `DateRangePicker` | `<v-date-picker>` com range | Média | Vuetify 3 Labs tem `VDateRangePicker` (experimental). |
| 8 | `FileUploadButton` | `<v-file-input>` | Baixa | `variant="outlined"`. `prepend-icon="mdi-upload"`. |
| 9 | `PipelineStagesCarousel` | `<v-slide-group>` | Média | `show-arrows`. Items como `<v-slide-group-item>`. |
| 10 | `PremiumAutocomplete` | `<v-autocomplete>` | Baixa | `variant="outlined"`. `auto-select-first`. |
| 11 | `BulkSelectionBar` / `UnifiedBulkActionsBar` | `<v-bottom-sheet>` ou `<v-snackbar>` fixo | Média | Barra flutuante no rodapé — usar `<v-bottom-navigation>` temporária ou `position: fixed`. |
| 12 | `InterviewSchedulingModal` | `<v-dialog>` + `<v-date-picker>` + `<v-select>` | Alta | Combinar vários componentes Vuetify dentro do dialog. |
| 13 | `LiaExpandedPanel` | `<v-navigation-drawer>` `temporary` `location="right"` | Média | Side panel da LIA. Width customizado. |
| 14 | `PromptSuggestionsDock` | Componente customizado | Média | Chips/botões fixos — `<v-chip-group>` ou botões customizados. |
| 15 | `VariableSelector` | `<v-menu>` + `<v-list>` agrupada | Média | Usar `<v-list-subheader>` para categorias. |
| 16 | `SearchLoadingAnimation` | Componente customizado | Baixa | Animação CSS pura — transferir diretamente. |
| 17 | `ResizableTableHeader` | `<v-data-table>` com resize | Alta | Vuetify v-data-table não suporta resize nativo. Implementar com directive customizada. |
| 18 | `RubricEvaluationModal` | `<v-dialog>` complexo | Alta | Multi-seção com tabs, cards, badges. Compor com `<v-tabs>`, `<v-card>`, `<v-chip>`, `<v-expansion-panels>`. |
| 19 | `CandidateReviewModal` | `<v-dialog fullscreen>` ou page | Alta | 3 colunas. Usar `<v-row>` + `<v-col>`. Tabs com `<v-tabs>`. Keyboard nav mantida via composable. |

### 18.3 Tokens de Design — CSS Variables → Vuetify Theme

| Token CSS LIA | Classe Tailwind | Vuetify Theme Key | Valor |
|--------------|----------------|-------------------|-------|
| `--wedo-cyan` | `text-wedo-cyan` | `colors.wedo-cyan` | `#60BED1` |
| `--wedo-cyan-dark` | `text-wedo-cyan-dark` | `colors.wedo-cyan-dark` | `#4DA8BB` |
| `--wedo-coral` | `text-wedo-coral` | `colors.error` (override) | `#C74446` |
| `--wedo-green` | `text-wedo-green` | `colors.success` (override) | `#5DA47A` |
| `--wedo-orange` | `text-wedo-orange` | `colors.warning` (override) | `#D19960` |
| gray-50 | `bg-gray-50` | `colors.grey-lighten-5` | `#F9FAFB` |
| gray-100 | `bg-gray-100` | `colors.grey-lighten-4` | `#F3F4F6` |
| gray-200 | `border-gray-200` | `colors.grey-lighten-3` | `#E5E7EB` |
| gray-400 | `text-gray-400` | `colors.grey-lighten-1` | `#9CA3AF` |
| gray-500 | `text-gray-500` | `colors.grey` | `#6B7280` |
| gray-600 | `text-gray-600` | `colors.grey-darken-1` | `#4B5563` |
| gray-700 | `text-gray-700` | `colors.grey-darken-2` | `#374151` |
| gray-800 | `text-gray-800` | `colors.grey-darken-3` | `#1F2937` |
| gray-900 | `bg-gray-900` | `colors.grey-darken-4` | `#111827` |
| gray-950 | `text-gray-950` | custom | `#030712` |

### 18.4 Tipografia — Tailwind → Vuetify

| Tailwind Class | Vuetify Class | Font | Uso |
|---------------|--------------|------|-----|
| `text-[11px]` | custom CSS `font-size: 11px` | Open Sans | Padrão LIA (labels, botões, badges) |
| `text-xs` (12px) | `text-caption` | Open Sans | Small text, disclaimers |
| `text-sm` (14px) | `text-body-2` | Open Sans | Texto corpo padrão |
| `text-base` (16px) | `text-body-1` | Open Sans | Texto corpo grande |
| `text-lg` (18px) | `text-subtitle-1` | Open Sans | Subtítulos |
| `text-xl` (20px) | `text-h6` | Open Sans | Títulos de seção |
| `text-2xl` (24px) | `text-h5` | Open Sans | Títulos de página |
| `font-medium` (500) | `font-weight-medium` | — | Labels, botões |
| `font-semibold` (600) | `font-weight-bold` | — | Títulos (Vuetify usa bold≈600) |
| `font-mono` | custom CSS `font-family: 'JetBrains Mono'` | JetBrains Mono | Código, IDs (5% da UI) |
| Inter para métricas | custom CSS `font-family: 'Inter'` | Inter | Dados numéricos, scores (10% da UI) |

### 18.5 Layout — Tailwind → Vuetify

| Tailwind | Vuetify | Exemplo |
|----------|---------|---------|
| `flex items-center gap-2` | `d-flex align-center ga-2` | Layout inline |
| `flex flex-col gap-4` | `d-flex flex-column ga-4` | Layout vertical |
| `grid grid-cols-3 gap-4` | `<v-row><v-col cols="4">` × 3 | Grid de 3 colunas |
| `grid grid-cols-12` | `<v-row><v-col :cols="n">` | Grid responsivo |
| `p-4` | `pa-4` | Padding all |
| `px-6 py-4` | `px-6 py-4` | Padding eixos (idêntico) |
| `mt-2 mb-4` | `mt-2 mb-4` | Margin (idêntico) |
| `rounded-md` | `rounded="md"` | Border radius |
| `shadow-sm` | `elevation="1"` | Sombra |
| `shadow-md` | `elevation="3"` | Sombra média |
| `border border-gray-200` | `border-sm` + custom color | Borda |
| `overflow-y-auto` | `class="overflow-y-auto"` | Scroll (idêntico) |
| `animate-pulse` | `<v-skeleton-loader>` | Skeleton loading |
| `animate-spin` | `<v-progress-circular indeterminate size="20">` | Spinner |

### 18.6 Transições CSS → Vuetify Transitions

| Animação CSS LIA | Vuetify Transition | Uso |
|-----------------|-------------------|-----|
| `fadeIn 150ms` | `<v-fade-transition>` | Overlay, entrada de modais |
| `slideInFromBottom 200ms` | `<v-slide-y-transition>` | Modais, menus |
| `slideInFromRight 300ms` | `<v-slide-x-reverse-transition>` | Side panels, sheets |
| `scaleIn 150ms` | `<v-scale-transition>` | FABs, tooltips, botões |
| `expandFromTop 200ms` | `<v-expand-transition>` | Acordeões, collapsibles |
| Custom `backdrop-blur` | Vuetify overlay padrão | Modais usam Vuetify overlay built-in |

### 18.7 Modais — Conversão por Tipo

| Tipo de Modal | Componentes React | Vuetify 3 Pattern |
|--------------|------------------|------------------|
| Formulário simples | `Dialog` + `Input` + `Button` | `<v-dialog max-width="600"><v-card><v-card-title>` + `<v-card-text>` com `<v-text-field>` + `<v-card-actions>` com `<v-btn>` |
| Formulário complexo | `Dialog` + multi-step | `<v-dialog>` + `<v-stepper>` ou `<v-tabs>` internos |
| Confirmação | `AlertDialog` | `<v-dialog max-width="400" persistent>` + texto + 2 botões |
| Side panel | `Sheet` | `<v-navigation-drawer temporary location="right" width="400">` |
| Full-screen | Custom overlay | `<v-dialog fullscreen>` ou `<v-dialog max-width="95vw">` |
| Comparação | `Dialog` wide | `<v-dialog max-width="1200">` + `<v-data-table>` ou grid |

### 18.8 Ícones — Lucide → Material Design Icons

| Lucide (React) | MDI (Vuetify) | Uso |
|---------------|--------------|-----|
| `Briefcase` | `mdi-briefcase` | Vagas |
| `Users` | `mdi-account-group` | Candidatos |
| `Settings` | `mdi-cog` | Configurações |
| `Search` | `mdi-magnify` | Busca |
| `Filter` | `mdi-filter` | Filtros |
| `Plus` | `mdi-plus` | Adicionar |
| `X` | `mdi-close` | Fechar |
| `ChevronDown` | `mdi-chevron-down` | Dropdown |
| `ChevronLeft/Right` | `mdi-chevron-left` / `mdi-chevron-right` | Navegação |
| `Check` | `mdi-check` | Confirmação |
| `AlertTriangle` | `mdi-alert` | Alerta |
| `Bell` | `mdi-bell` | Notificações |
| `Star` | `mdi-star` | Favorito |
| `Eye` | `mdi-eye` | Visualizar |
| `Edit2` / `Pencil` | `mdi-pencil` | Editar |
| `Trash2` | `mdi-delete` | Excluir |
| `Mail` | `mdi-email` | Email |
| `Phone` | `mdi-phone` | Telefone |
| `MapPin` | `mdi-map-marker` | Localização |
| `Brain` | `mdi-brain` | LIA / IA |
| `Clock` | `mdi-clock` | Tempo |
| `Linkedin` | `mdi-linkedin` | LinkedIn |
| `GraduationCap` | `mdi-school` | Educação |
| `Building` / `Building2` | `mdi-office-building` | Empresa |
| `Loader2` (spinning) | `<v-progress-circular indeterminate>` | Loading |
| `GripVertical` | `mdi-drag-vertical` | Drag handle |
| `MoreVertical` | `mdi-dots-vertical` | Menu opções |
| `ExternalLink` | `mdi-open-in-new` | Link externo |
| `Crown` | `mdi-crown` | Premium |
| `MessageSquare` | `mdi-message` | Chat/Mensagens |
| `Send` | `mdi-send` | Enviar |

### 18.9 Recomendações de Conversão por Prioridade

| Prioridade | Módulo | Componentes | Complexidade |
|-----------|--------|-------------|-------------|
| 1 (Piloto) | Configurações (Settings) | Formulários, Tabs, Inputs, Selects | Baixa-Média |
| 2 | Pipeline/Kanban | KanbanColumn, KanbanCard, DnD, Side preview | Alta |
| 3 | Vagas (Lista + Formulários) | Table, Modais CRUD, Badges | Média |
| 4 | Funil de Talentos | Search, Filters (1125 linhas), Table, Bulk actions | Alta |
| 5 | CandidateReviewModal | 3-col layout, Tabs, Criteria, Keyboard nav | Alta |
| 6 | Dashboard | Cards KPI, Charts | Média |
| 7 | Modais de Comunicação | Templates, Rich text, Multi-canal | Média-Alta |
| 8 | RubricEvaluationModal | Tabs, Score logic, Rubric grid, Audit section | Alta |

---

## 19. ARQUIVOS DE REFERÊNCIA

### 19.1 Código-Fonte (React/Tailwind)

| Categoria | Path | Arquivos | Descrição |
|-----------|------|----------|-----------|
| Design tokens | `plataforma-lia/src/styles/design-tokens.css` | 1 | CSS custom properties (cores, sombras, radius, transições) |
| CSS global | `plataforma-lia/src/app/globals.css` | 1 | Imports, resets, classes utilitárias `.wedo-*` |
| Tailwind config | `plataforma-lia/tailwind.config.ts` | 1 | Theme extensions, custom colors, animations |
| Componentes UI | `plataforma-lia/src/components/ui/*.tsx` | 68 | Biblioteca base (shadcn + customizados) |
| Stories (Storybook) | `plataforma-lia/src/components/ui/*.stories.tsx` | 0 | Removidos (badge, button, card, dialog, input, select existiam anteriormente) |
| Modais (central) | `plataforma-lia/src/components/modals/*.tsx` | 34 | Modais centrais + sub-diretórios |
| Modais (dispersos) | Vários diretórios | ~20 | Modais em components root, search, cv, alerts, quick-actions, etc. |
| Components root | `plataforma-lia/src/components/*.tsx` | 71 | Componentes raiz diretamente em components/ |
| Páginas | `plataforma-lia/src/components/pages/*.tsx` | 25 | Telas principais |
| Kanban | `plataforma-lia/src/components/pages/job-kanban/` | 56 | Kanban completo com toolbar, filtros, modais, sidebar LIA, hooks, sections, utils |
| Candidatos | `plataforma-lia/src/components/pages/candidates/` | 81 | Header, Tabs, SearchBar, FilterPanel, Table, modais, sidebars, hooks, cells, lia-sidebar |
| Jobs | `plataforma-lia/src/components/pages/jobs/` | 30 | Header, Table, Preview, Filters, Dashboard view, hooks |
| Chat Page | `plataforma-lia/src/components/pages/chat-page/` | 18 | Core hooks, constants, chat session management |
| Dashboards | `plataforma-lia/src/components/pages/dashboards-page/` | 12 | Sub-dashboards especializados |
| Indicadores | `plataforma-lia/src/components/pages/indicators/` | 10 | Tabs de indicadores + constants/types |
| ATS Integrations | `plataforma-lia/src/components/pages/ats-integrations/` | 5 | Modal de configuração + hook + constants |
| Tasks | `plataforma-lia/src/components/pages/tasks/` | 2 | ActiveAlertsCard + TaskCard |
| Settings | `plataforma-lia/src/components/settings/` | 40 | Tabs de configuração + 5 sub-diretórios |
| Screening Config | `plataforma-lia/src/components/screening-config/` | 12+ | Manager, modais, hooks, JD evaluation |
| WSI | `plataforma-lia/src/components/wsi/` | 4 | Triagem WSI + scorecard + voice status |
| Search System | `plataforma-lia/src/components/search/` | 50+ | SmartSearch, filtros, presets, modes, hooks |
| Expanded Chat | `plataforma-lia/src/components/expanded-chat/` | 60+ | Wizard conversacional completo |
| LIA Float | `plataforma-lia/src/components/lia-float/` | 6 | Sistema de chat flutuante |
| Agent Control Center | `plataforma-lia/src/components/agent-control-center/` | 3 | Controle de agentes IA |
| Admin Panel | `plataforma-lia/src/components/admin/` | 15+ | Dashboard admin, clients, AI consumption |
| Candidate Profile | `plataforma-lia/src/components/candidate-profile/` | 6 | Sub-componentes do perfil (T002) |
| Candidate Preview | `plataforma-lia/src/components/candidate-preview/` | 10+ | Tabs de preview lateral |
| Candidate Page | `plataforma-lia/src/components/candidate-page/` | 6 | Página full do candidato |
| Chat System | `plataforma-lia/src/components/chat/` | 15+ | Mensagens, input, contexto, cards |
| Triagem | `plataforma-lia/src/components/triagem/` | 10 | UI de triagem candidato-facing |
| Triagem Details | `plataforma-lia/src/components/triagem-details/` | 4 | Detalhes de triagem recrutador-facing |
| Calibration | `plataforma-lia/src/components/calibration/` | 3 | Dashboard e feedback de calibração |
| Job Wizard | `plataforma-lia/src/components/job-wizard/` | 8+ | Wizard alternativo + stages |
| Job Creation | `plataforma-lia/src/components/job-creation/` | 9 | Componentes de criação de vaga |
| Rubric Evaluation | `plataforma-lia/src/components/rubric-evaluation-modal.tsx` | 1 | Modal de avaliação por rubrica |
| Expandable AI Prompt | `plataforma-lia/src/components/expandable-ai-prompt/` | 15 | Prompt expansível IA com tabs, hooks, modais |
| Hooks | `plataforma-lia/src/hooks/*.ts` | 102 | Hooks de estado, dados, UI, integração + subdiretórios admin/settings/__tests__ |
| Lib/Utils | `plataforma-lia/src/lib/` | 28 | `utils.ts` (cn), `format-utils.ts` (T001), `fetch-client.ts`, `masks.ts`, `sanitize.ts`, `safe-data.ts`, `template-variables.ts`, `workos.ts`, `vue-bridge.ts`, etc. + subdiretórios api/schemas/sidebar/transforms/utils |
| Shared Hooks (T001-T003) | `plataforma-lia/src/hooks/useTagInputState.ts` | 1 | Hook compartilhado de tag input (T003) |
| Format Utils (T001) | `plataforma-lia/src/lib/format-utils.ts` | 1 | `formatRelativeTime` + `formatFileSize` centralizados |

### 19.2 Documentação de Design System

| Documento | Path | Conteúdo |
|-----------|------|----------|
| Design System v4 | `plataforma-lia/docs/design-system/00-design-system-v4.md` | Tokens, regras, Vuetify mapping |
| Design System LIA | `plataforma-lia/docs/design-system/LIA-DESIGN-SYSTEM.md` | Identidade visual da LIA |
| Vuetify Migration Plan | `plataforma-lia/docs/design-system/VUETIFY-MIGRATION-PLAN.md` | Fases 0-3, auditoria de cores, workflow Figma→Vue |
| Modal Standards | `plataforma-lia/docs/design-system/modal-design-standards.md` | Padrões de modais |
| DS v3 Pendências | `plataforma-lia/docs/design-system/design-system-v3-pendencias.md` | Pendências da v3 |

### 19.3 Skills de Migração Vue

| Skill | Path | Uso |
|-------|------|-----|
| Vue Migration Prep | `.agents/skills/vue-migration-prep/SKILL.md` | Princípios, mapeamento React→Vue, prompts de conversão, diagnóstico de portabilidade |
| Design Standardize | `.agents/skills/design-standardize/SKILL.md` | Padronização visual conforme DS v4.2.1 |

### 19.4 Vuetify Theme Config (template para projeto Vue)

```typescript
import { createVuetify } from 'vuetify'

const liaTheme = {
  dark: false,
  colors: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    'surface-variant': '#F9FAFB',
    primary: '#111827',
    secondary: '#6B7280',
    error: '#C74446',
    warning: '#D19960',
    success: '#5DA47A',
    info: '#60BED1',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
    'on-error': '#FFFFFF',
    'on-warning': '#FFFFFF',
    'on-success': '#FFFFFF',
    'on-info': '#FFFFFF',
    'wedo-cyan': '#60BED1',
    'wedo-cyan-dark': '#4DA8BB',
    'wedo-coral': '#C74446',
    'wedo-green': '#5DA47A',
    'wedo-orange': '#D19960',
  },
  variables: {
    'border-color': '#E5E7EB',
    'border-opacity': 1,
    'high-emphasis-opacity': 0.95,
    'medium-emphasis-opacity': 0.70,
    'disabled-opacity': 0.50,
    'theme-overlay-multiplier': 1,
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'liaTheme',
    themes: { liaTheme },
  },
  defaults: {
    VBtn: { rounded: 'md', elevation: 0 },
    VCard: { rounded: 'md', elevation: 0, variant: 'outlined' },
    VTextField: { variant: 'outlined', density: 'compact' },
    VTextarea: { variant: 'outlined', density: 'compact' },
    VSelect: { variant: 'outlined', density: 'compact' },
    VCheckbox: { color: 'grey-darken-4', density: 'compact' },
    VSwitch: { color: 'grey-darken-4', density: 'compact' },
    VRadio: { color: 'grey-darken-4' },
    VChip: { size: 'small' },
    VDataTable: { density: 'compact' },
    VDialog: { maxWidth: 600 },
    VTabs: { color: 'grey-darken-4' },
  },
})
```
