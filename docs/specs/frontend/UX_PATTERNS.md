# UX Patterns — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `plataforma-lia/src/components/ui/`, `plataforma-lia/src/components/pages/`, `plataforma-lia/src/components/modals/`, `plataforma-lia/src/hooks/`
> **SPEC-DRIVEN DEVELOPMENT** — padrões de experiência do usuário extraídos do código real da plataforma React/Next.js.

---

## 1. Navegação

### 1.1 Estrutura de Layout

```
┌────────────────────────────────────────────────────────────────┐
│ TopBar (border-bottom, bg-white, z-index alto)                │
│   Notificações (Bell) │ Avatar + DropdownMenu │ Busca Global  │
├──────────┬─────────────────────────────────────────────────────┤
│ Sidebar  │ Content Area (max-w-7xl mx-auto)                   │
│ (240px   │                                                     │
│  ou 48px │   ┌─────────────────────────────────────────────┐  │
│  colaps) │   │ Page Header (título, badges, ações)         │  │
│          │   ├─────────────────────────────────────────────┤  │
│ ─ Painel │   │ Main Content                                │  │
│ ─ Vagas  │   │                                             │  │
│ ─ Funil  │   │                                             │  │
│ ─ Config │   │                                             │  │
│          │   │                     ┌───────────────────────┤  │
│ Collapse │   │                     │ Side Panel (overlay)  │  │
│ Theme    │   │                     │ slideInFromRight      │  │
│ LIA Tips │   │                     │ ~400px                │  │
└──────────┴───┴─────────────────────┴───────────────────────┘  │
                         ┌──────────────────────────────────┐    │
                         │ Bulk Actions Bar (fixed bottom)  │    │
                         └──────────────────────────────────┘    │
```

**Arquivos:**
- Sidebar: `plataforma-lia/src/components/sidebar.tsx`
- TopBar: `plataforma-lia/src/components/top-bar.tsx`
- Admin Layout: `plataforma-lia/src/app/admin/layout.tsx`

### 1.2 Sidebar (Navegação Principal)

| Estado | Visual | Estilo |
|--------|--------|--------|
| Expanded | Full width (~240px), labels visíveis | `wedo-surface-elevated`, `border-right` |
| Collapsed | Icon-only (64px) | Tooltips nos ícones |
| Item active | Background highlight + bold text | `bg-gray-100 dark:bg-gray-800 text-gray-950 font-semibold` |
| Item hover | Background sutil | `hover:bg-gray-50` |
| Item locked | Opacity reduzida + lock icon | `Lock` icon, `opacity-60` |
| Sub-menu open | Items filhos expandidos | `ChevronDown/Up` toggle |

**Menu principal (3 itens core):**

| Ícone (Lucide) | Label | Rota |
|----------------|-------|------|
| `LayoutDashboard` | Painel de Controle | `dashboard` |
| `Briefcase` | Vagas | `vagas` |
| `Users` | Funil de Talentos | `candidatos` |

**Itens adicionais:** Search (busca global), Settings, ThemeToggle, LIATipsModal (`HelpCircle`), collapse/expand (`ChevronLeft/Right`), Premium lock (`Lock`/`Crown`).

**Font:** Open Sans, 11px (`0.6875rem`), weight 500.

### 1.3 TopBar

| Elemento | Componente | Posição |
|----------|-----------|---------|
| Notificações | `Bell` → `NotificationSystem` | Direita |
| Avatar | `Avatar` + `AvatarFallback` | Direita |
| Dropdown usuário | `DropdownMenu` (Nome, email, role, empresa) | Direita |
| Meu Perfil | `User` icon | Dropdown item |
| Alterar Senha | `KeyRound` icon → `Dialog` com 3 inputs password | Dropdown item |
| Sair | `LogOut` icon | Dropdown item |

### 1.4 Tabs (Navegação por Contexto)

| Local | Implementação | Estilo |
|-------|--------------|--------|
| Padrão shadcn/ui | `Tabs` + `TabsList` + `TabsTrigger` | `rounded-full`, `bg-gray-100 p-1`, ativo: `bg-white text-gray-900` |
| Funil de Talentos | Custom tabs com `border-b-2` | Ativa: `border-gray-950 text-gray-950`, inativa: `border-transparent text-gray-800` |
| Vaga | `TabsList` inline | Tab Gestão (com contador) + Tab Configurações |
| Candidato Full | 3 tabs (Experience, Education, Skill Map) | Dentro do `CandidateReviewModal` |

### 1.5 Busca Global com IA (Ctrl+K)

| Propriedade | Valor |
|------------|-------|
| **Atalho** | Ctrl+K / Cmd+K |
| **Função** | Ativa o copilot IA / foca no prompt de busca inteligente |
| **Hook** | `useKeyboardShortcuts` (`plataforma-lia/src/hooks/use-keyboard-shortcuts.tsx`) |
| **Ativação** | Em qualquer página — foca no campo de busca com modo IA ativo |
| **CommandPalette** | Componente `CommandPalette` (`plataforma-lia/src/components/ui/command-palette.tsx`) disponível na chat-page com cmdk |
| **Outros atalhos** | Ctrl+; (toggle prompt), Ctrl+Shift+L (LIA), Ctrl+Shift+C (candidatos), Ctrl+B (sidebar toggle) |

### 1.6 Fluxo de Navegação Principal

```
Login → Dashboard
          ↓
     Vagas (lista/tabela)
          ↓
     Vaga Específica (Kanban | Tabela)
          ↓
     Candidato (Side Panel preview | Full Modal review)
          ↓
     Ações (Avançar etapa, Rejeitar, Comunicar, Agendar)
```

---

## 2. Loading States

### 2.1 Componentes de Loading

| Componente | Arquivo | Variantes | Quando usar |
|-----------|---------|-----------|-------------|
| `Loading` | `ui/loading.tsx` | `spinner`, `dots`, `skeleton`, `pulse` | Carregamento genérico |
| `LoadingCard` | `ui/loading.tsx` | — | Placeholder de card |
| `LoadingList` | `ui/loading.tsx` | — | Placeholder de lista |
| `Skeleton` | `ui/skeleton.tsx` | — | Primitiva para layouts custom |
| `SkeletonRow` | `pages/candidates/CandidatesTable.tsx` | — | Linhas de tabela loading |
| `SearchLoadingAnimation` | `ui/search-loading-animation.tsx` | — | Busca semântica IA |

### 2.2 Regras de Uso

| Contexto | Padrão de Loading | Componente |
|----------|-------------------|-----------|
| **Páginas** | Skeleton layout (cards + barras) | `LoadingCard` × N |
| **Tabelas** | Skeleton rows com avatar circle + text bars | `SkeletonRow` (`animate-pulse`) |
| **Modais** | Skeleton dentro do DialogContent | `Skeleton` + `LoadingCard` por seção |
| **Botões (submit)** | `Loader2` icon spinning + disabled | `Loader2 animate-spin` no lugar do ícone |
| **Chat IA** | Dots pulsantes + texto de status | `dotsPulse` animation |
| **Busca semântica** | Animação customizada | `SearchLoadingAnimation` |
| **Kanban colunas** | Skeleton cards nas colunas | `LoadingCard` × N por coluna |
| **JD enrichment** | Painel com skeleton | `JDEvaluationPanel` skeleton |
| **Skills suggestion** | Brain icon + Loader | `Brain` + `Loader2` no botão |

### 2.3 Botão com Loading

Padrão universal para submits:

```tsx
<Button disabled={isSubmitting}>
  {isSubmitting ? (
    <Loader2 className="h-4 w-4 animate-spin mr-2" />
  ) : (
    <Icon className="h-4 w-4 mr-2" />
  )}
  {isSubmitting ? "Salvando..." : "Salvar"}
</Button>
```

**Arquivo:** Padrão usado em todos os modais (`modals/*.tsx`)

### 2.4 Chat Thinking States

| Estado | Visual | Texto |
|--------|--------|-------|
| Analisando | dots pulsantes | "Analisando sua pergunta..." |
| Planejando | dots pulsantes | "Planejando execução..." |
| Executando | spinner | "Executando consultas..." |
| Processando | spinner | "Processando dados..." |
| Formatando | dots pulsantes | "Formatando resposta..." |

**Arquivo:** `plataforma-lia/src/components/ui/chat-status-indicators.tsx`

---

## 3. Empty States

### 3.1 Componente Padrão

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/empty-state.tsx` |
| **Layout** | `flex flex-col items-center justify-center py-12 px-6 text-center` |
| **Ícone** | `text-gray-300` (dark: `text-gray-600`), `w-10 h-10` |
| **Título** | `text-sm font-medium text-gray-700` |
| **Descrição** | `text-xs text-gray-500 max-w-xs` |
| **Ação** | `Button variant="outline" size="sm"` (opcional) |

### 3.2 Aplicações por Tela

| Tela | Ícone | Título | Ação |
|------|-------|--------|------|
| Vagas (sem resultados) | `Briefcase` | "Nenhuma vaga encontrada" | "Criar Vaga" |
| Kanban (coluna vazia) | — | "Nenhum candidato nesta etapa" | — |
| Funil (busca vazia) | — | "Nenhum candidato encontrado" | Sugestões de query |
| Funil (estado inicial) | — | Search bar + `PromptSuggestionsDock` | — |
| Filtro (sem resultados) | — | "Nenhum resultado com estes filtros" | "Limpar filtros" |
| Tabela (sem dados) | — | Mensagem centralizada | — |

---

## 4. Error Handling

### 4.1 Error Boundary (Global)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/error-boundary.tsx` |
| **Montagem** | `plataforma-lia/src/app/layout.tsx` (root layout) |
| **Tipo** | Class-based React ErrorBoundary |
| **Fallback** | `ErrorFallbackScreen` com botões "Tentar novamente" e "Recarregar página" |
| **Dev mode** | Renderiza mensagem de erro raw |

### 4.2 Erros de API (Inline)

| Contexto | Implementação | Visual |
|----------|--------------|--------|
| Modais (submit) | Estado `error` local | `text-red-500 text-xs` inline sob o campo |
| Formulários | Validação de campo | `text-red-500 text-xs` + border `border-red-500` |
| Tabelas (fetch) | Estado `error` no hook | Toast destructive |
| Busca (falha) | Estado `error` no query hook | Toast destructive |

### 4.3 Validação de Formulários

| Tipo | Implementação | Exemplo |
|------|--------------|---------|
| **Manual/inline** | Estado `errors` local + condicionais | Login: check "@" e "." no email |
| **Required fields** | Asterisco (*) no label + validação onSubmit | `CreateJobModal`: Título, Departamento |
| **Input error state** | Border vermelha + helper text | `border-red-500` + `text-red-500 text-xs` |
| **Success feedback** | Check verde + texto | `Check` icon verde + `text-green-600` |

**Padrão de validação inline:**
```
Label (*) + Input
  └── [se erro] text-red-500 text-xs: "Campo obrigatório"
  └── [se sucesso] text-green-600 text-xs: "Alterado com sucesso" + Check icon
```

---

## 5. Feedback ao Usuário

### 5.1 Toast Notifications

| Propriedade | Valor |
|------------|-------|
| **Hook** | `useToast()` — `plataforma-lia/src/hooks/use-toast.ts` |
| **Componente** | `Toaster` — `plataforma-lia/src/components/ui/toaster.tsx` |
| **Posição** | Mobile: top, Desktop: bottom-right |
| **Max width** | `md:max-w-[420px]` |
| **Dismiss** | Swipe gesture + close button (hover) |

| Variante | Uso | Background | Border |
|----------|-----|-----------|--------|
| `default` | Ação concluída (genérico) | `bg-background` | default border |
| `destructive` | Erro, falha de operação | `bg-destructive` | `border-destructive` |
| `success` | Criação, atualização, aprovação | `bg-green-50` | `border-green-200` |
| `warning` | Ação com consequências | `bg-yellow-50` | `border-yellow-200` |
| `info` | Informação contextual | `bg-blue-50` | `border-blue-200` |

### 5.2 Proactive Alerts (IA)

| Propriedade | Valor |
|------------|-------|
| **Hook** | `use-proactive-alerts.ts` |
| **Componente** | `proactive-alert-toast` |
| **Uso** | Insights automáticos gerados pela LIA |

### 5.3 AI Disclaimer

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/ai-disclaimer.tsx` |
| **Layout** | Banner inline, `text-xs`, ícone Brain/Sparkles + texto |
| **Cor** | Cyan accent background sutil |
| **Uso** | Sempre visível quando conteúdo é gerado/assistido por IA |

### 5.4 Score Color System (5-band)

| Faixa | Cor | Classe |
|-------|-----|--------|
| ≥80 (Excelente) | Emerald/Cyan | `text-emerald-600 dark:text-emerald-400` |
| ≥60 (Bom) | Amber | `text-amber-600 dark:text-amber-400` |
| <60 (Baixo) | Red | `text-red-600 dark:text-red-400` |
| null/0 (Sem dados) | Gray | `text-gray-400 dark:text-gray-500` |

Usado em: `KanbanCard`, `CandidateReviewModal`, `RubricEvaluationModal`.

---

## 6. Modais e Overlays

### 6.1 Inventário de Modais (~35 modais)

**Localizações:**
- Principal: `plataforma-lia/src/components/modals/` (30 modais)
- Screening: `plataforma-lia/src/components/screening-config/` (4 modais)
- WSI: `plataforma-lia/src/components/wsi/` (2 modais)
- Review: `plataforma-lia/src/components/rubric-evaluation-modal.tsx`

| Categoria | Modais | Container |
|-----------|--------|-----------|
| **CRUD Vagas** | CreateJobModal, EditJobModal, JobDuplicateModal, JobPublishModal, JobUnpublishModal, JobStatusModal, CloseVacancyModal | Panel slide-in ou Dialog max-w-2xl |
| **Insights** | JobCompareModal, JobInsightsModal | Dialog large (~80% viewport) |
| **Candidatos** | AddCandidateModal, CandidateCompareModal, AddToJobModal, AddToListModal, AddCandidatesToVacancyModal, AddListToVacanciesModal | Dialog max-w-md a max-w-lg |
| **Comunicação** | UnifiedCommunicationModal, StageTransitionActionsModal, ShareSearchModal, SharedSearchDetailsModal | Dialog largo |
| **Ações em Lote** | BulkActionModal | Dialog max-w-lg max-h-[90vh] |
| **Screening** | ScreeningChannelsModal, ScreeningSchedulingModal, ScreeningSettingsModal, ScreeningStatusModal | Dialog (em `screening-config/`) |
| **WSI** | WSITextScreeningModal, WSITriagemInviteModal | Dialog (em `wsi/`) |
| **Avaliação** | LiaAnalysisModal, GeneralScoreModal, TechnicalTestModal, EnglishTestModal, ScreeningMediaModal, RubricEvaluationModal | Dialog/Overlay customizado |
| **Dados** | DataRequestModal, DataBlockingModal, InsufficientDataModal | Dialog max-w-lg |
| **Persona** | PersonaCreationModal | Dialog multi-step |
| **Alertas** | UnsavedPearchWarningModal, JobAssignRecruiterModal | Dialog simples |

### 6.2 Tamanhos de Modal

| Tamanho | Classes | Uso |
|---------|---------|-----|
| Small | `max-w-md` | Confirmações, alertas simples |
| Medium | `max-w-lg` | Formulários médios (padrão Dialog) |
| Large | `max-w-2xl` | Formulários complexos, comparação |
| Extra Large | `max-w-4xl` ou ~80% viewport | Insights, screening media |
| Full Panel | Slide-in customizado (não Dialog) | Create/Edit job, Add to job |
| Full Screen | `fixed inset-0 z-50` | CandidateReviewModal |

### 6.3 Ciclo de Vida do Modal

| Estado | Visual | Estilo |
|--------|--------|--------|
| Closed | Invisível | — |
| Opening | Overlay fade-in + content zoom-in | `bg-black/30 backdrop-blur-[1px]`, `scaleIn` |
| Open (idle) | Formulário visível | `DialogContent` |
| Submitting | Botão com loader, campos disabled | `Loader2` + `disabled:opacity-50` |
| Success | Toast + modal fecha | `Toast variant="success"` |
| Error | Inline error ou toast | `text-red-500` ou `Toast variant="destructive"` |
| Closing | Content zoom-out + overlay fade-out | Reverse animations |

### 6.4 Padrão de Footer de Modal

```
┌─────────────────────────────────────────────────────┐
│ DialogFooter (border-t bg-gray-50 gap-2)            │
│                                                      │
│              [Cancelar]  [Ação Principal]            │
│              outline      default/destructive         │
│              h-9 px-4     h-9 px-4                   │
│              text-xs      text-xs                    │
└─────────────────────────────────────────────────────┘
```

### 6.5 Modal Multi-step

| Propriedade | Implementação |
|------------|--------------|
| **Tracking** | Estado `currentStep` (`'options' | 'communication' | 'confirmation' | 'complete'`) |
| **Progress** | Step indicator visual no topo |
| **Navegação** | Botão "Voltar" (outline) + "Próximo"/"Criar" (default) |
| **Exemplo** | `PersonaCreationModal` (Step 1: Form → Step 2: Preview → Create) |

### 6.6 Confirmação de Ações Destrutivas

| Tipo | Componente | Botões |
|------|-----------|--------|
| Exclusão | `AlertDialog` | Cancel (outline) + Delete (destructive) |
| Rejeição | `BulkActionModal` | Cancel (outline) + Executar (default) |
| Status change | `JobStatusModal` | Cancel (outline) + Pausar/Reativar (default) |
| Despublicação | `JobUnpublishModal` | Cancel (outline) + Despublicar (destructive) |
| Drag & drop | `MoveConfirmationModal` | Cancel + Confirmar |

---

## 7. Formulários

### 7.1 Padrão de Campo

```
┌──────────────────────────────────────────┐
│ Label text-[11px] font-medium (*)        │
│ ┌──────────────────────────────────────┐ │
│ │ Input h-10 text-[11px] rounded-md    │ │
│ │ border-gray-300 bg-white             │ │
│ │ focus: border-gray-500 ring-2        │ │
│ │        ring-gray-900/20              │ │
│ └──────────────────────────────────────┘ │
│ [se erro] text-red-500 text-xs           │
│ [se helper] text-gray-500 text-xs        │
└──────────────────────────────────────────┘
```

### 7.2 Tipos de Controle

| Controle | Componente | Uso |
|---------|-----------|-----|
| Texto livre | `Input` | Nome, email, URLs |
| Texto longo | `Textarea` (min-h-[80px]) | Descrições, observações |
| Seleção única | `Select` (Radix) | Departamento, senioridade, motivo |
| Seleção múltipla | Lista de `Checkbox` | Filtros, campos de dados |
| Toggle | `Switch` | Configurações on/off |
| Escolha exclusiva | `RadioGroup` | Copiar candidatos (Todos/Aprovados/Nenhum) |
| Data | `Input type="date"` | Prazos |
| Número | `Input type="number"` | Quantidade de vagas |
| Senha | `Input type="password"` + `Eye/EyeOff` toggle | Alterar senha |
| Autocomplete | `PremiumAutocomplete` | Skills, cargos, empresas |
| Upload | `FileUploadButton` | CVs, documentos |

### 7.3 Padrão de Formulário em Modal

1. **Header:** `DialogTitle text-[14px] font-semibold` + `DialogDescription text-xs`
2. **Body:** Grid de campos com labels `text-[11px] font-medium text-gray-800`
3. **Validação:** Inline `text-red-500 text-xs` + border highlight
4. **Footer:** `DialogFooter border-t bg-gray-50 gap-2` com Cancel (outline) + Submit (default)
5. **Submit state:** `isSubmitting` → Loader2 no botão, campos disabled

### 7.4 Formulários Multi-tab

Usado em `AddCandidateModal`:

| Tab | Conteúdo |
|-----|----------|
| Upload CV | Drag zone + botão upload |
| Colar CV | Textarea + botão Parse |
| LinkedIn | Input URL + botão Importar |
| Manual | Inputs (Nome*, Email, Telefone, LinkedIn) |

---

## 8. Tabelas

### 8.1 Componente Base

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/table.tsx` |
| **Header** | `h-10 px-2`, `font-medium text-muted-foreground` |
| **Row** | `border-b`, hover: `bg-muted/50`, selected: `bg-muted` |
| **Cell** | `p-2 align-middle` |

### 8.2 Features de Tabela

| Feature | Implementação | Componente |
|---------|--------------|-----------|
| **Sorting** | Click no header → `ArrowUpDown`/`ArrowUp`/`ArrowDown` icons | Column headers |
| **Seleção** | `Checkbox` por row + select all no header | `Checkbox` (Radix) |
| **Colunas redimensionáveis** | Drag na borda → `cursor-col-resize` | `ResizableTableHeader` |
| **Filtros** | Panel lateral colapsível | `CandidatesFilterPanel` (1125 linhas) |
| **Paginação** | Controles de página | — |
| **Loading** | Skeleton rows | `SkeletonRow` (avatar circle + text bars) |
| **Empty** | `EmptyState` centralizado | — |
| **Side panel** | Click na row → preview lateral | `slideInFromRight` animation |

### 8.3 Skeleton Row (Loading Pattern)

```
┌────┬───────────────────────────────────────────────────┐
│ ○  │ ████████████████  ████████  ████  ██████  ████   │
│    │ animate-pulse bg-gray-200 rounded-md             │
├────┼───────────────────────────────────────────────────┤
│ ○  │ ██████████████    ██████    ████  ████████  ██   │
├────┼───────────────────────────────────────────────────┤
│ ○  │ ████████████      ████████  ████  ██████  ████   │
└────┴───────────────────────────────────────────────────┘
```

---

## 9. Kanban

### 9.1 Estrutura

| Componente | Arquivo | Função |
|-----------|---------|--------|
| `JobKanbanPage` | `pages/job-kanban-page.tsx` | Container principal |
| `KanbanColumn` | `pages/job-kanban/KanbanColumn.tsx` | Coluna por etapa |
| `KanbanCard` | `pages/job-kanban/KanbanCard.tsx` | Card de candidato |
| `MoveConfirmationModal` | `pages/job-kanban/MoveConfirmationModal.tsx` | Confirmação drag |

### 9.2 Coluna

| Elemento | Estilo |
|----------|--------|
| Container | `flex flex-col w-[300px] min-w-[300px] bg-gray-50 dark:bg-gray-900 rounded-md border` |
| Indicador de cor | `div w-3 h-3 rounded-full` (cor dinâmica por etapa) |
| Nome | `font-medium text-gray-900` |
| Contador | `Badge variant="outline" text-xs` (`border-gray-300`) |
| Botão adicionar | `Button variant="ghost" size="icon" h-7 w-7` + `Plus` |
| Botão opções | `Button variant="ghost" size="icon" h-7 w-7` + `MoreVertical` |
| Área de cards | `ScrollArea` com lista de KanbanCard |
| Empty | `EmptyState` component |

### 9.3 Card

| Elemento | Estilo |
|----------|--------|
| Container | `Card bg-white border border-gray-200 hover:border-gray-300 rounded-md cursor-pointer` |
| Drag handle | `GripVertical h-4 w-4 text-gray-400` (opacity-0 → 100 on hover) |
| Avatar | `Avatar` + `AvatarFallback` (iniciais) |
| Nome | `text-sm font-medium` |
| Score | Cor dinâmica (5-band: emerald/amber/red/gray) |
| Status | `StatusBadge` por etapa |
| Stale alert | `AlertTriangle` (>7 dias na etapa) |
| Days in stage | `Clock` icon + "Xd" |
| Messages | `MessageSquare` icon + contagem |

### 9.4 Etapas (16 colunas)

Funil, Triagem, Long List, Short List, Entrevista RH, Teste Técnico, Teste de Inglês, Entrevista Técnica, Entrevista Gestor, Entrevista Gestor 2, Entrevista Final, Referências, Proposta, Contratado, Reprovado, Proposta Recusada.

### 9.5 Interações

| Ação | Trigger | Feedback |
|------|---------|----------|
| **Drag & Drop** | Arrastar card entre colunas | Card elevado + shadow, coluna destino highlight (`border-cyan-300`) |
| **Confirmar movimento** | Drop → `MoveConfirmationModal` | Origem/destino, nome do candidato |
| **Click card** | Click → side panel | `slideInFromRight` animation, ~400px |
| **Seleção** | Checkbox no card | `UnifiedBulkActionsBar` aparece (slide-up) |
| **Toggle view** | `Grid3X3` (Kanban) / `List` (Tabela) | Mesmos dados, layout diferente |

---

## 10. Ações em Lote (Bulk Actions)

### 10.1 Componente

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx` |
| **Layout** | `fixed bottom-0`, animação slide-up |
| **Trigger** | Visível quando ≥1 candidato selecionado |
| **Elementos** | Badge contador + botões de ação + X fechar |

### 10.2 Ações Disponíveis

| Ação | Componente | Modal de Confirmação |
|------|-----------|---------------------|
| Avançar Etapa | `Button` | `BulkActionModal` → Select etapa destino |
| Rejeitar | `Button` | `BulkActionModal` → Select motivo + observações |
| Enviar Mensagem | `Button` | `UnifiedCommunicationModal` |
| Agendar Entrevista | `Button` | `InterviewSchedulingModal` |
| Solicitar Dados | `Button` | `DataRequestModal` |

### 10.3 Progress Feedback

Durante execução em lote:
1. Botão com `Loader2 animate-spin` + disabled
2. Barra de progresso (`Progress`) mostrando X de Y
3. Ao concluir: Toast success com resumo
4. Se erro parcial: Toast warning com contagem de falhas

---

## 11. Candidato — Fluxo de Visualização

### 11.1 Preview (Side Panel — Kanban)

| Propriedade | Valor |
|------------|-------|
| **Tipo** | Implementação customizada (não Sheet) |
| **Animação** | `slideInFromRight` |
| **Largura** | ~400px |
| **Tabs** | Resumo, Experiência, Formação, Habilidades, Histórico |
| **Header** | Nome, cargo, empresa, Avatar, badges de status |

**6 botões de score (ScoreIconButton):**

| ID | Label | Modal ao Click |
|----|-------|---------------|
| `geral` | Score Geral | `GeneralScoreModal` |
| `triagem` | Triagem | `WSITextScreeningModal` |
| `cv` | Análise CV | `LiaAnalysisModal` |
| `tecnico` | Teste Técnico | `TechnicalTestModal` |
| `ingles` | Teste de Inglês | `EnglishTestModal` |
| `b5` | Big Five | `BigFiveProfile` modal |

### 11.2 Review Full (CandidateReviewModal)

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/components/pages/candidate-review-modal.tsx` |
| **Container** | `fixed inset-0 z-50` overlay + panel `bg-white m-4 rounded-md` |
| **Font** | `fontFamily: 'Open Sans, sans-serif'` |
| **Keyboard** | `A` = Approve, `R` = Reject, `←/→` = navigation |

**Layout 3 colunas:**

| Coluna | Largura | Conteúdo |
|--------|---------|----------|
| Esquerda | 420px | Perfil (foto, info, tabs Experience/Education/Skill Map) |
| Central | flex-1 | Critérios de avaliação + Match reasons |
| Direita | overlay | Edição de critérios (drag reorder, add/remove, presets) |

**Footer de ação:**
- Navigation: `ChevronLeft/Right` + `Badge "X de Y"`
- Actions: `Button` Reject (border-red-200) + `Button` Approve (bg-gray-900)
- Auto-advance após ação

---

## 12. Chat LIA

### 12.1 Componentes

| Componente | Arquivo | Função |
|-----------|---------|--------|
| `LiaChatPanel` | `components/lia-float/LiaChatPanel.tsx` | Floating chat (rodapé) |
| `LiaSuperPrompt` | `components/lia-float/LiaSuperPrompt.tsx` | Chat expandido (fullscreen-like) |
| `ChatStatusIndicators` | `components/ui/chat-status-indicators.tsx` | Indicadores de estado |
| `PromptSuggestionsDock` | `components/ui/prompt-suggestions-dock.tsx` | Sugestões no rodapé |
| `PromptSuggestionsPopover` | `components/ui/prompt-suggestions-popover.tsx` | Sugestões contextual |
| `QuickActionChips` | `components/ui/quick-action-chips.tsx` | Chips de ação rápida |

### 12.2 Formatação de Mensagens

| Propriedade | Valor |
|------------|-------|
| **Arquivo** | `plataforma-lia/src/lib/chat-format.ts` |
| **Funções** | `cleanAgentResponse()`, `parseChatMarkdown()`, `escapeHtml()` |
| **Rendering** | Headings (H1-H4), bold, italic, bullet lists, numbered lists, code blocks, inline code, links, horizontal rules |
| **Sanitização** | `cleanAgentResponse()` strip JSON wrapper (`{"thought":...}`) |

### 12.3 Balões de Mensagem

| Tipo | Background | Text | Border-radius |
|------|-----------|------|---------------|
| Bot (LIA) | `bg-gray-50` | `text-gray-800` | `rounded-md`, bottom-left: 2px |
| Usuário | `bg-gray-900` | `text-white` | `rounded-md`, bottom-right: 2px |

### 12.4 Guides de Queries

| Componente | Escopo |
|-----------|--------|
| `CandidateQueriesGuide` | Busca de candidatos |
| `LiaQueriesGuide` | Análise, relatório, geral |
| `LiaSearchQueriesGuide` | Busca semântica |
| `LiaVacancyQueriesGuide` | Vagas |

---

## 13. Responsividade

### 13.1 Estratégia

**Abordagem:** Mobile-first com Tailwind responsive prefixes.

### 13.2 Padrões por Breakpoint

| Pattern | Mobile (< 640px) | Tablet (640-1024px) | Desktop (> 1024px) |
|---------|-----------------|--------------------|--------------------|
| **Headers/Ações** | `flex-col` empilhado | `flex-row` | `flex-row` |
| **Grids** | `grid-cols-1` | `sm:grid-cols-2` | `lg:grid-cols-4` |
| **Sidebar** | hidden ou collapsed | collapsed | expanded (240px) |
| **Labels de ícone** | `hidden` | `hidden sm:block` | visível |
| **Modais** | `w-full mx-4` | `max-w-lg` | `max-w-lg` ou maior |
| **Tabelas** | Scroll horizontal | Colunas reduzidas | Todas as colunas |
| **Toast** | Top (slide from top) | Bottom-right | Bottom-right |

### 13.3 Layout Constraints

| Pattern | Classes |
|---------|---------|
| Page wrapper | `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` |
| Modal mobile | `w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden` |
| Content area | flex-1 com min-width |

---

## 14. Keyboard Shortcuts

| Atalho | Ação | Contexto | Arquivo |
|--------|------|----------|---------|
| `Ctrl+K` / `Cmd+K` | Ativar busca com IA (focar prompt) | Global | `use-keyboard-shortcuts.tsx` |
| `Ctrl+;` | Toggle expandir prompt | Global | `use-keyboard-shortcuts.tsx` |
| `Ctrl+Shift+L` | Navegar para LIA | Global | `use-keyboard-shortcuts.tsx` |
| `Ctrl+Shift+C` | Navegar para candidatos | Global | `use-keyboard-shortcuts.tsx` |
| `Ctrl+B` | Toggle sidebar | Global | `sidebar.tsx` |
| `Ctrl+H` | Histórico de comandos | Prompt expandido | `expandable-ai-prompt.tsx` |
| `A` | Aprovar candidato | CandidateReviewModal | `candidate-review-modal.tsx` |
| `R` | Rejeitar candidato | CandidateReviewModal | `candidate-review-modal.tsx` |
| `←` | Candidato anterior | CandidateReviewModal | `candidate-review-modal.tsx` |
| `→` | Próximo candidato | CandidateReviewModal | `candidate-review-modal.tsx` |
| `Esc` | Fechar modal/panel | Todos os modais | Radix built-in |

---

## 15. Matriz de Estados por Tela

### 15.1 Vagas (Lista)

| Estado | Visual | Componente |
|--------|--------|-----------|
| Loading | Skeleton rows | `Skeleton` rows |
| Empty | `EmptyState` centralizado | Ícone `Briefcase`, "Nenhuma vaga encontrada" |
| Loaded | Tabela com dados | `Table` + `TableRow` |
| Filtered (sem resultados) | `EmptyState` com filtro | Mensagem de filtro |
| Error | Toast destructive | `Toast variant="destructive"` |

### 15.2 Kanban

| Estado | Visual | Componente |
|--------|--------|-----------|
| Loading | Skeleton columns | `LoadingCard` × N |
| Empty column | `EmptyState` na coluna | "Nenhum candidato nesta etapa" |
| Populated | Cards nas colunas | `KanbanCard` por candidato |
| Dragging | Card elevado + shadow | Cursor `grabbing`, border highlight |
| Drop target | Border highlight | `border-cyan-300` |
| Candidate preview | Side panel slide-in | `slideInFromRight` |
| Bulk selection | Bottom bar visível | `UnifiedBulkActionsBar` slide-up |

### 15.3 Funil de Talentos

| Estado | Visual | Componente |
|--------|--------|-----------|
| Initial | Search bar + sugestões | `CandidateSearchBar` + `PromptSuggestionsDock` |
| Searching | Animação de loading | `SearchLoadingAnimation` |
| Results | Tabela de candidatos | `CandidatesTable` |
| No results | `EmptyState` | "Nenhum candidato encontrado" + sugestões |
| CV dropping | Drop zone highlight | Border dashed cyan |
| CV parsing | Loader centralizado | `Loader2 animate-spin` |
| Filters open | Panel lateral | `CandidatesFilterPanel` slide-in |
| Bulk selection | Bottom bar | `UnifiedBulkActionsBar` |

### 15.4 Configurações da Vaga

| Estado | Visual | Componente |
|--------|--------|-----------|
| Loading | Skeleton sections | `LoadingCard` por seção |
| Loaded | Formulários preenchidos | Sections com dados |
| Editing | Campos ativos | Border focus ring |
| Saving | Spinner no botão | `Loader2 animate-spin` |
| Saved | Toast success | `Toast variant="success"` |
| Validation error | Inline red text | `text-red-500 text-xs` |
| JD enriching | Painel loading | `JDEvaluationPanel` skeleton |
| JD enriched | Painel com scores | Barras de progresso D1-D9 |
| Skills suggesting | Button loading | `Brain` icon + `Loader2` |

### 15.5 Sidebar

| Estado | Visual | Transição |
|--------|--------|-----------|
| Expanded | Full width, labels visíveis | — |
| Collapsed | Icon-only, tooltips | — |
| Active item | bg-gray-100 + border-l-2 | — |
| Hover | hover:bg-gray-50 | — |
| Locked | opacity-60 + Lock icon | — |

---

## 16. Padrões de Comunicação

### 16.1 Canais

| Canal | Ícone | Componente |
|-------|-------|-----------|
| Email | `Mail` | `UnifiedCommunicationModal` |
| WhatsApp | `MessageSquare` | `UnifiedCommunicationModal` |
| Email + WhatsApp | — | `UnifiedCommunicationModal` (opção combinada) |

### 16.2 Templates

| Propriedade | Valor |
|------------|-------|
| **Seleção** | `Select` dropdown com templates pré-definidos |
| **Variáveis** | `VariableSelector` — insere `{{variavel}}` no textarea |
| **Categorias** | Candidato, Vaga, Empresa |
| **Preview** | Sempre mostra preview antes de enviar |

### 16.3 Regra de Confirmação

Toda comunicação externa (email, WhatsApp, notificação) passa por preview obrigatório antes do envio. Alinhado com o princípio de "never send without confirmation" do MessagingDomain.

---

## Referências de Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `plataforma-lia/src/components/ui/` | 70 componentes base (loading, empty, skeleton, toast, etc.) |
| `plataforma-lia/src/components/pages/` | Telas principais (jobs, kanban, candidates, settings, tasks) |
| `plataforma-lia/src/components/modals/` | 35 modais catalogados |
| `plataforma-lia/src/components/sidebar.tsx` | Sidebar principal |
| `plataforma-lia/src/components/top-bar.tsx` | TopBar |
| `plataforma-lia/src/components/error-boundary.tsx` | Error boundary global |
| `plataforma-lia/src/hooks/use-toast.ts` | Hook do sistema de toast |
| `plataforma-lia/src/lib/chat-format.ts` | Formatação de mensagens do chat LIA |
| `docs/PRODUCT_DESIGN_INVENTORY.md` | Inventário completo (2285 linhas, 70 componentes, 35 modais) |
