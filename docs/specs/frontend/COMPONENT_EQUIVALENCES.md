# Equivalências shadcn/ui → Vuetify 3 — Plataforma LIA

> Referência técnica para migração de componentes React+shadcn/ui para Vue 3+Vuetify 3.
> Gerado a partir do inventário real do projeto (65+ componentes em `plataforma-lia/src/components/ui/`).

---

## Índice

1. [Inventário de Componentes](#1-inventário-de-componentes)
2. [Mapeamento por Categoria](#2-mapeamento-por-categoria)
   - [2.1 Forms & Inputs](#21-forms--inputs)
   - [2.2 Feedback & Overlay](#22-feedback--overlay)
   - [2.3 Data Display](#23-data-display)
   - [2.4 Navigation](#24-navigation)
   - [2.5 Layout & Structure](#25-layout--structure)
3. [Componentes Custom LIA (sem equivalente direto)](#3-componentes-custom-lia-sem-equivalente-direto)
4. [Mapeamento Detalhado de Props](#4-mapeamento-detalhado-de-props)
5. [Padrões de Composição: children → slots](#5-padrões-de-composição-children--slots)
6. [Convenções Enforçadas](#6-convenções-enforçadas)

---

## 1. Inventário de Componentes

### Top 25 shadcn/ui (padrão) — por frequência de uso

| # | Componente shadcn/ui | Radix Primitive | Vuetify 3 Equivalente | Complexidade |
|---|---------------------|-----------------|----------------------|-------------|
| 1 | **Button** | `@radix-ui/react-slot` | `<v-btn>` | Baixa |
| 2 | **Badge** | — (div simples) | `<v-chip>` | Baixa |
| 3 | **Card** (+ Header/Title/Description/Content/Footer) | — (div simples) | `<v-card>` (+ subcomponentes) | Baixa |
| 4 | **Input** | — (input nativo) | `<v-text-field>` | Baixa |
| 5 | **Dialog** (+ Header/Footer/Title/Description) | `@radix-ui/react-dialog` | `<v-dialog>` | Média |
| 6 | **Select** (+ Trigger/Content/Item/Group) | `@radix-ui/react-select` | `<v-select>` | Média |
| 7 | **Avatar** (+ Image/Fallback) | `@radix-ui/react-avatar` | `<v-avatar>` | Baixa |
| 8 | **Tabs** (+ List/Trigger/Content) | `@radix-ui/react-tabs` | `<v-tabs>` + `<v-tab>` + `<v-tabs-window>` | Média |
| 9 | **Table** (+ Header/Body/Row/Head/Cell/Footer/Caption) | — (HTML nativo) | `<v-data-table>` ou `<v-table>` | Média |
| 10 | **Switch** | `@radix-ui/react-switch` | `<v-switch>` | Baixa |
| 11 | **Checkbox** | `@radix-ui/react-checkbox` | `<v-checkbox>` | Baixa |
| 12 | **DropdownMenu** (+ Trigger/Content/Item/Sub/etc.) | `@radix-ui/react-dropdown-menu` | `<v-menu>` + `<v-list>` | Média |
| 13 | **Tooltip** (+ Provider/Trigger/Content) | `@radix-ui/react-tooltip` | `<v-tooltip>` | Baixa |
| 14 | **Popover** (+ Trigger/Content) | `@radix-ui/react-popover` | `<v-menu>` | Média |
| 15 | **Progress** | `@radix-ui/react-progress` | `<v-progress-linear>` | Baixa |
| 16 | **Skeleton** | — (div simples) | `<v-skeleton-loader>` | Baixa |
| 17 | **Sheet** (+ Trigger/Content/Header/Footer/Title) | `@radix-ui/react-dialog` | `<v-navigation-drawer temporary>` | Média |
| 18 | **Accordion** (+ Item/Trigger/Content) | `@radix-ui/react-accordion` | `<v-expansion-panels>` + `<v-expansion-panel>` | Baixa |
| 19 | **AlertDialog** (+ Trigger/Content/Header/Action/Cancel) | `@radix-ui/react-alert-dialog` | `<v-dialog>` com `persistent` | Média |
| 20 | **Slider** | `@radix-ui/react-slider` | `<v-slider>` | Baixa |
| 21 | **Label** | `@radix-ui/react-label` | Prop `label` do input Vuetify | Baixa |
| 22 | **Textarea** | — (textarea nativo) | `<v-textarea>` | Baixa |
| 23 | **RadioGroup** (+ Item) | `@radix-ui/react-radio-group` | `<v-radio-group>` + `<v-radio>` | Baixa |
| 24 | **ScrollArea** (+ ScrollBar) | `@radix-ui/react-scroll-area` | CSS `overflow-auto` (nativo) | Baixa |
| 25 | **Separator** | `@radix-ui/react-separator` | `<v-divider>` | Baixa |

### Componentes Adicionais (standard shadcn/ui)

| Componente | Vuetify 3 | Notas |
|-----------|-----------|-------|
| **Toast** (+ Provider/Viewport/Action/Close/Title/Description) | `<v-snackbar>` | 5 variants: default, destructive, success, warning, info |
| **Toaster** | `<v-snackbar>` global via composable | Gerenciado por `useToast()` → `useSnackbar()` |
| **Collapsible** (+ Trigger/Content) | `<v-expansion-panels>` ou `v-show` | Re-export simples do Radix |
| **Command** (+ Dialog/Input/List/Empty/Group/Item) | Custom (`<v-combobox>` parcial) | Baseado em `cmdk`; sem equivalente 1:1 |

### Componentes Custom LIA (13 componentes proprietários)

| Componente | Linhas | Equivalente Vuetify | Estratégia |
|-----------|--------|-------------------|-----------|
| **lia-icon** | 63 | Custom component | Recriar como `LiaIcon.vue` |
| **empty-state** | 57 | Custom component | Recriar; pode usar `<v-empty-state>` (Vuetify Labs) |
| **context-pill** | 55 | `<v-chip>` customizado | Adaptar com slot e ícone |
| **quick-action-chips** | 92 | `<v-chip-group>` | Adaptar layout |
| **audio-record-button** | 200 | Custom component | Recriar; lógica MediaRecorder API permanece |
| **file-upload-button** | 217 | `<v-file-input>` parcial | Recriar com lógica de upload customizada |
| **loading** | 130 | `<v-progress-circular>` + `<v-overlay>` | Compor com componentes Vuetify |
| **status-badge** | 602 | `<v-chip>` customizado | Componente mais complexo; recriar com mapeamento de status |
| **command-palette** | 258 | Custom component | Sem equivalente direto; recriar |
| **prompt-suggestions-dock** | 371 | Custom component | Específico LIA; recriar |
| **search-loading-animation** | 95 | `<v-progress-linear>` + CSS | Recriar animação |
| **data-request-indicator** | 260 | Custom component | Específico LIA; recriar |
| **setup-alert-badge** | 210 | `<v-alert>` + `<v-badge>` | Compor com Vuetify primitivos |

### Componentes Custom LIA (domínio/feature — não em `/ui/`)

| Componente | Vuetify | Notas |
|-----------|---------|-------|
| **ai-disclaimer** | Custom | Disclaimer LIA; texto + ícone |
| **audio-player** | Custom | Player HTML5 customizado |
| **big-five-profile** | Custom | Gráfico radar; manter lib de chart |
| **bulk-selection-bar** | `<v-toolbar>` | Barra de ações em massa |
| **candidate-card** | `<v-card>` customizado | Composição Vuetify |
| **date-range-picker** | `<v-date-picker>` + custom | Vuetify date picker + range logic |
| **interview-rating** | Custom | Rating com estrelas/critérios |
| **interview-scheduling-modal** | `<v-dialog>` | Modal com form Vuetify |
| **lia-expanded-panel** | `<v-expansion-panel>` | Painel LIA |
| **pipeline-report** | Custom | Relatório com charts |
| **pipeline-stages-carousel** | `<v-slide-group>` | Carousel de stages |
| **premium-autocomplete** | `<v-autocomplete>` | Mapeia bem |
| **resizable-table-header** | `<v-data-table>` com resize | Custom header |
| **score-icon-button** | `<v-btn icon>` | Botão com score |
| **unified-bulk-actions-bar** | `<v-toolbar>` | Barra unificada |
| **variable-selector** | `<v-select>` customizado | Seletor de variáveis |

---

## 2. Mapeamento por Categoria

### 2.1 Forms & Inputs

#### Button

| shadcn/ui (React) | Vuetify 3 (Vue) | Notas |
|---|---|---|
| `<Button>` | `<v-btn>` | — |
| `variant="default"` / `"primary"` | `color="grey-darken-4" variant="flat"` | Paleta LIA monocromática |
| `variant="destructive"` | `color="error" variant="flat"` | — |
| `variant="outline"` | `variant="outlined"` | — |
| `variant="secondary"` | `color="grey-lighten-4" variant="flat"` | — |
| `variant="ghost"` | `variant="text"` | — |
| `variant="link"` | `variant="text"` + `:ripple="false"` | Adicionar underline via class |
| `size="default"` (h-10) | `size="default"` | — |
| `size="sm"` (h-9) | `size="small"` | — |
| `size="lg"` (h-11) | `size="large"` | — |
| `size="icon"` (h-10 w-10) | `icon` prop | `<v-btn icon>` |
| `asChild` (Slot) | Não existe | Usar `<component :is="tag">` ou scoped slot |
| `disabled` | `disabled` | Idêntico |

```vue
<!-- React -->
<Button variant="destructive" size="sm">Excluir</Button>

<!-- Vue/Vuetify -->
<v-btn color="error" variant="flat" size="small">Excluir</v-btn>
```

#### Input

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Input type="text" />` | `<v-text-field variant="outlined" />` | — |
| `<Input type="password" />` | `<v-text-field type="password" variant="outlined" />` | — |
| `placeholder` | `placeholder` ou `label` | Vuetify suporta ambos |
| `disabled` | `disabled` | — |
| `className` | `class` | — |
| `onChange` | `@update:model-value` ou `v-model` | Two-way binding nativo |

```vue
<!-- React -->
<Input placeholder="Buscar..." value={search} onChange={(e) => setSearch(e.target.value)} />

<!-- Vue/Vuetify -->
<v-text-field v-model="search" placeholder="Buscar..." variant="outlined" density="compact" />
```

#### Textarea

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Textarea />` | `<v-textarea variant="outlined" />` | — |
| `rows` | `rows` | Idêntico |
| `placeholder` | `placeholder` | — |

#### Select

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Select>` | `<v-select>` | Componente único vs composição |
| `<SelectTrigger>` + `<SelectValue>` | `label` + `placeholder` props | Integrado no `<v-select>` |
| `<SelectContent>` | Automático | Dropdown interno do Vuetify |
| `<SelectItem value="x">` | `:items="[{title, value}]"` | Array de items vs filhos |
| `<SelectGroup>` + `<SelectLabel>` | `item-props` com headers | — |
| `onValueChange` | `@update:model-value` | — |

```vue
<!-- React -->
<Select onValueChange={setStatus}>
  <SelectTrigger><SelectValue placeholder="Status" /></SelectTrigger>
  <SelectContent>
    <SelectItem value="active">Ativo</SelectItem>
    <SelectItem value="inactive">Inativo</SelectItem>
  </SelectContent>
</Select>

<!-- Vue/Vuetify -->
<v-select
  v-model="status"
  :items="[{title: 'Ativo', value: 'active'}, {title: 'Inativo', value: 'inactive'}]"
  label="Status"
  variant="outlined"
/>
```

#### Checkbox

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Checkbox checked={x} onCheckedChange={fn} />` | `<v-checkbox v-model="x" />` | v-model nativo |
| `disabled` | `disabled` | — |
| `id` + `<Label htmlFor>` | `label` prop | Integrado |

#### Switch

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Switch checked={x} onCheckedChange={fn} />` | `<v-switch v-model="x" color="grey-darken-4" />` | — |
| `disabled` | `disabled` | — |

#### RadioGroup

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<RadioGroup value={x} onValueChange={fn}>` | `<v-radio-group v-model="x">` | — |
| `<RadioGroupItem value="a" />` | `<v-radio value="a" label="..." />` | Label integrado |

#### Slider

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Slider value={[x]} onValueChange={fn} max={100} step={1} />` | `<v-slider v-model="x" :max="100" :step="1" />` | Array → valor único |
| `min`, `max`, `step` | `min`, `max`, `step` | Idêntico |

#### Label

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Label htmlFor="x">Texto</Label>` | Prop `label` do input | Vuetify integra label no campo |
| Label separado | `<label>` HTML nativo | Quando necessário |

### 2.2 Feedback & Overlay

#### Dialog

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Dialog open={x} onOpenChange={fn}>` | `<v-dialog v-model="x">` | — |
| `<DialogTrigger asChild>` | `activator` slot | `<template v-slot:activator="{ props }">` |
| `<DialogContent>` | Conteúdo direto dentro de `<v-dialog>` | `<v-card>` como wrapper |
| `<DialogHeader>` | `<v-card-title>` | — |
| `<DialogTitle>` | `<v-card-title>` | — |
| `<DialogDescription>` | `<v-card-subtitle>` ou `<v-card-text>` | — |
| `<DialogFooter>` | `<v-card-actions>` | — |
| `<DialogClose>` | `@click="dialog = false"` | Manual close |
| `<DraggableDialogContent>` | Custom; sem equivalente | Recriar com `v-dialog` + drag logic |

```vue
<!-- React -->
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild><Button>Abrir</Button></DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Título</DialogTitle>
      <DialogDescription>Descrição</DialogDescription>
    </DialogHeader>
    <div>Conteúdo</div>
    <DialogFooter><Button onClick={() => setOpen(false)}>OK</Button></DialogFooter>
  </DialogContent>
</Dialog>

<!-- Vue/Vuetify -->
<v-dialog v-model="open" max-width="500">
  <template v-slot:activator="{ props }">
    <v-btn v-bind="props">Abrir</v-btn>
  </template>
  <v-card>
    <v-card-title>Título</v-card-title>
    <v-card-subtitle>Descrição</v-card-subtitle>
    <v-card-text>Conteúdo</v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn @click="open = false">OK</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

#### AlertDialog

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<AlertDialog>` | `<v-dialog persistent>` | `persistent` impede fechar ao clicar fora |
| `<AlertDialogAction>` | `<v-btn>` com action handler | — |
| `<AlertDialogCancel>` | `<v-btn variant="outlined">` | — |
| `<AlertDialogTitle>` | `<v-card-title>` | — |
| `<AlertDialogDescription>` | `<v-card-text>` | — |

#### Sheet

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Sheet>` | `<v-navigation-drawer temporary>` | — |
| `side="right"` (default) | `location="right"` | — |
| `side="left"` | `location="left"` | — |
| `side="top"` | `location="top"` | — |
| `side="bottom"` | `location="bottom"` | — |
| `<SheetContent>` | Conteúdo direto | — |
| `<SheetHeader>` | `<div>` ou `<v-card-title>` | — |
| `<SheetTitle>` | Texto ou `<v-card-title>` | — |
| `<SheetClose>` | `@click="drawer = false"` | — |

```vue
<!-- React -->
<Sheet>
  <SheetTrigger asChild><Button>Menu</Button></SheetTrigger>
  <SheetContent side="right">
    <SheetHeader><SheetTitle>Configurações</SheetTitle></SheetHeader>
    <div>Conteúdo</div>
  </SheetContent>
</Sheet>

<!-- Vue/Vuetify -->
<v-navigation-drawer v-model="drawer" temporary location="right">
  <v-card-title>Configurações</v-card-title>
  <v-card-text>Conteúdo</v-card-text>
</v-navigation-drawer>
<v-btn @click="drawer = true">Menu</v-btn>
```

#### Toast

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `useToast()` + `toast({ title, description })` | `useSnackbar()` ou Vuetify global | — |
| `variant="default"` | `color="surface"` | — |
| `variant="destructive"` | `color="error"` | — |
| `variant="success"` | `color="success"` | — |
| `variant="warning"` | `color="warning"` | — |
| `variant="info"` | `color="info"` | — |
| `<ToastAction>` | Snackbar `action` slot | — |

#### Tooltip

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<TooltipProvider>` | Não necessário | Global em Vuetify |
| `<Tooltip>` + `<TooltipTrigger>` + `<TooltipContent>` | `<v-tooltip>` | Componente único |
| `sideOffset` | `offset` | — |
| `side="top"` | `location="top"` | — |

```vue
<!-- React -->
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild><Button>?</Button></TooltipTrigger>
    <TooltipContent>Ajuda</TooltipContent>
  </Tooltip>
</TooltipProvider>

<!-- Vue/Vuetify -->
<v-tooltip text="Ajuda">
  <template v-slot:activator="{ props }">
    <v-btn v-bind="props" icon="mdi-help" />
  </template>
</v-tooltip>
```

#### Popover

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Popover>` + `<PopoverTrigger>` + `<PopoverContent>` | `<v-menu>` | — |
| `align="center"` | Automático | — |
| `sideOffset` | `offset` | — |

#### Progress

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Progress value={65} />` | `<v-progress-linear :model-value="65" />` | — |
| `max` | `max` | — |
| Cores via className | `color` prop | `color="grey-darken-4"` |

#### Skeleton

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Skeleton className="h-4 w-[200px]" />` | `<v-skeleton-loader type="text" />` | — |
| Formas via className | `type` prop | `text`, `heading`, `image`, `card`, `avatar`, etc. |

### 2.3 Data Display

#### Card

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Card>` | `<v-card variant="outlined" rounded="md">` | — |
| `<CardHeader>` | `<v-card-item>` | — |
| `<CardTitle>` | `<v-card-title>` | — |
| `<CardDescription>` | `<v-card-subtitle>` | — |
| `<CardContent>` | `<v-card-text>` | — |
| `<CardFooter>` | `<v-card-actions>` | — |

```vue
<!-- React -->
<Card>
  <CardHeader>
    <CardTitle>Candidatos</CardTitle>
    <CardDescription>Total: 42</CardDescription>
  </CardHeader>
  <CardContent><p>Conteúdo</p></CardContent>
  <CardFooter><Button>Ver Mais</Button></CardFooter>
</Card>

<!-- Vue/Vuetify -->
<v-card variant="outlined" rounded="md">
  <v-card-item>
    <v-card-title>Candidatos</v-card-title>
    <v-card-subtitle>Total: 42</v-card-subtitle>
  </v-card-item>
  <v-card-text><p>Conteúdo</p></v-card-text>
  <v-card-actions><v-btn>Ver Mais</v-btn></v-card-actions>
</v-card>
```

#### Badge

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Badge>` | `<v-chip size="small">` | — |
| `variant="default"` | `color="grey-lighten-4"` | — |
| `variant="secondary"` | `color="grey-lighten-3"` | — |
| `variant="destructive"` | `color="error" variant="tonal"` | — |
| `variant="outline"` | `variant="outlined"` | — |
| `variant="success"` | `color="success" variant="tonal"` | — |
| `variant="warning"` | `color="warning" variant="tonal"` | — |
| `variant="info"` | `color="info" variant="tonal"` | — |
| `variant="danger"` | `color="error" variant="tonal"` | Alias de destructive |
| `variant="lilac"` | `color="purple" variant="tonal"` | Cor custom WeDO |

```vue
<!-- React -->
<Badge variant="success">Ativo</Badge>

<!-- Vue/Vuetify -->
<v-chip size="small" color="success" variant="tonal">Ativo</v-chip>
```

#### Table

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Table>` | `<v-data-table>` (com features) ou `<v-table>` (simples) | — |
| `<TableHeader>` + `<TableHead>` | `:headers` prop | Array de objetos `{ title, key, sortable }` |
| `<TableBody>` + `<TableRow>` + `<TableCell>` | `:items` prop | Array de dados |
| Custom cell render | `#item.column` slot | Scoped slot por coluna |
| `<TableCaption>` | Não existe | `<template #bottom>` ou texto |
| `<TableFooter>` | `<template #bottom>` | — |
| Sorting manual | `:sort-by` prop | Integrado |
| Pagination manual | Integrada | `items-per-page`, `page` |

```vue
<!-- React (manual) -->
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Nome</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {candidates.map(c => (
      <TableRow key={c.id}>
        <TableCell>{c.name}</TableCell>
        <TableCell><Badge variant="success">{c.status}</Badge></TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>

<!-- Vue/Vuetify (declarativo) -->
<v-data-table :headers="headers" :items="candidates">
  <template #item.status="{ item }">
    <v-chip size="small" color="success" variant="tonal">{{ item.status }}</v-chip>
  </template>
</v-data-table>
```

#### Avatar

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Avatar>` + `<AvatarImage>` + `<AvatarFallback>` | `<v-avatar>` | Componente único |
| `src` em AvatarImage | `image` prop | — |
| Texto em AvatarFallback | Conteúdo slot | `<v-avatar>JD</v-avatar>` |
| `className="h-10 w-10"` | `size="40"` | Numérico em px |

```vue
<!-- React -->
<Avatar>
  <AvatarImage src={user.avatar} />
  <AvatarFallback>{user.initials}</AvatarFallback>
</Avatar>

<!-- Vue/Vuetify -->
<v-avatar :image="user.avatar" size="40">
  <template v-if="!user.avatar">{{ user.initials }}</template>
</v-avatar>
```

### 2.4 Navigation

#### Tabs

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Tabs defaultValue="tab1">` | `<v-tabs v-model="tab">` | Controlled |
| `<TabsList>` | Contido em `<v-tabs>` | — |
| `<TabsTrigger value="tab1">` | `<v-tab value="tab1">` | — |
| `<TabsContent value="tab1">` | `<v-tabs-window-item value="tab1">` | Dentro de `<v-tabs-window>` |

```vue
<!-- React -->
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Visão Geral</TabsTrigger>
    <TabsTrigger value="details">Detalhes</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">Conteúdo overview</TabsContent>
  <TabsContent value="details">Conteúdo details</TabsContent>
</Tabs>

<!-- Vue/Vuetify -->
<v-tabs v-model="tab">
  <v-tab value="overview">Visão Geral</v-tab>
  <v-tab value="details">Detalhes</v-tab>
</v-tabs>
<v-tabs-window v-model="tab">
  <v-tabs-window-item value="overview">Conteúdo overview</v-tabs-window-item>
  <v-tabs-window-item value="details">Conteúdo details</v-tabs-window-item>
</v-tabs-window>
```

#### DropdownMenu

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<DropdownMenu>` | `<v-menu>` | — |
| `<DropdownMenuTrigger>` | `activator` slot | — |
| `<DropdownMenuContent>` | `<v-list>` dentro do menu | — |
| `<DropdownMenuItem>` | `<v-list-item>` | — |
| `<DropdownMenuCheckboxItem>` | `<v-list-item>` com `<v-checkbox>` prepend | — |
| `<DropdownMenuRadioItem>` | `<v-list-item>` com `<v-radio>` prepend | — |
| `<DropdownMenuSeparator>` | `<v-divider>` | — |
| `<DropdownMenuLabel>` | `<v-list-subheader>` | — |
| `<DropdownMenuShortcut>` | `<template #append>` no list-item | — |
| `<DropdownMenuSub>` + `<DropdownMenuSubTrigger>` | `<v-list-group>` | Submenu |
| `inset` prop | `class="pl-8"` | Sem prop nativa |

```vue
<!-- React -->
<DropdownMenu>
  <DropdownMenuTrigger asChild><Button variant="ghost">⋮</Button></DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Ações</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem onClick={handleEdit}>Editar</DropdownMenuItem>
    <DropdownMenuItem onClick={handleDelete}>Excluir</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>

<!-- Vue/Vuetify -->
<v-menu>
  <template v-slot:activator="{ props }">
    <v-btn v-bind="props" variant="text" icon="mdi-dots-vertical" />
  </template>
  <v-list>
    <v-list-subheader>Ações</v-list-subheader>
    <v-divider />
    <v-list-item @click="handleEdit" title="Editar" />
    <v-list-item @click="handleDelete" title="Excluir" />
  </v-list>
</v-menu>
```

#### Accordion

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Accordion type="single" collapsible>` | `<v-expansion-panels>` | — |
| `<Accordion type="multiple">` | `<v-expansion-panels multiple>` | — |
| `<AccordionItem value="x">` | `<v-expansion-panel value="x">` | — |
| `<AccordionTrigger>` | `<v-expansion-panel-title>` | — |
| `<AccordionContent>` | `<v-expansion-panel-text>` | — |

### 2.5 Layout & Structure

#### ScrollArea

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<ScrollArea className="h-[300px]">` | `<div style="height: 300px; overflow-y: auto">` | CSS nativo |
| `<ScrollBar orientation="horizontal">` | `overflow-x: auto` | — |
| Custom scrollbar styling | CSS `::-webkit-scrollbar` | — |

#### Separator

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Separator />` | `<v-divider />` | — |
| `orientation="vertical"` | `vertical` prop | `<v-divider vertical />` |
| `decorative` | Não existe | — |

#### Collapsible

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Collapsible open={x}>` | `v-show="x"` ou `<v-expand-transition>` | — |
| `<CollapsibleTrigger>` | `@click="x = !x"` | Manual |
| `<CollapsibleContent>` | Conteúdo com `v-show` | — |

#### Command (cmdk)

| shadcn/ui | Vuetify 3 | Notas |
|---|---|---|
| `<Command>` | Custom component | Sem equivalente 1:1 em Vuetify |
| `<CommandInput>` | `<v-text-field>` com search | Parte de composição custom |
| `<CommandList>` | `<v-list>` com filtering | — |
| `<CommandItem>` | `<v-list-item>` | — |
| `<CommandGroup>` | `<v-list-group>` ou subheader | — |
| `<CommandEmpty>` | `v-if` condicional | — |
| `<CommandDialog>` | `<v-dialog>` + custom | Compor command palette |

---

## 3. Componentes Custom LIA (sem equivalente direto)

### 3.1 lia-icon (63 linhas)

**O que faz:** Renderiza o ícone brain/LIA com animação e variantes de cor.

**Estratégia Vue:** Recriar como `LiaIcon.vue` com `defineProps<{ size, animated, color }>`.

**Composição Vuetify:** Nenhuma; componente puro SVG/CSS.

### 3.2 empty-state (57 linhas)

**O que faz:** Estado vazio com ícone, título, descrição e action opcional.

**Estratégia Vue:** Vuetify Labs tem `<v-empty-state>` (experimental). Alternativa: recriar com `<v-card>` + layout.

**Props a manter:** `icon`, `title`, `description`, `action` (slot).

### 3.3 context-pill (55 linhas)

**O que faz:** Pill/chip que mostra contexto ativo (job, candidato, etc.) com ícone e close.

**Estratégia Vue:** `<v-chip closable>` com customização.

```vue
<v-chip closable size="small" color="grey-lighten-3" @click:close="onRemove">
  <template #prepend><v-icon :icon="icon" size="x-small" /></template>
  {{ label }}
</v-chip>
```

### 3.4 quick-action-chips (92 linhas)

**O que faz:** Grid de chips de ação rápida para o chat LIA.

**Estratégia Vue:** `<v-chip-group>` com `<v-chip>` items.

### 3.5 audio-record-button (200 linhas)

**O que faz:** Botão que grava áudio via MediaRecorder API com visual feedback.

**Estratégia Vue:** Recriar; lógica em composable `useAudioRecorder()`, template com `<v-btn>` + progress.

### 3.6 file-upload-button (217 linhas)

**O que faz:** Botão de upload com drag & drop, preview e validação de tipo/tamanho.

**Estratégia Vue:** `<v-file-input>` para casos simples. Para drag & drop customizado: recriar com composable `useFileUpload()`.

### 3.7 loading (130 linhas)

**O que faz:** Componente de loading com variantes (fullscreen, inline, skeleton).

**Estratégia Vue:** Compor `<v-overlay>` + `<v-progress-circular>` para fullscreen, `<v-skeleton-loader>` para inline.

### 3.8 status-badge (602 linhas — mais complexo)

**O que faz:** Badge de status com 50+ mapeamentos de cor/ícone para diferentes estados de candidatos, vagas, etc.

**Estratégia Vue:** Recriar como `StatusBadge.vue` com composable `useStatusMapping()` para mapeamentos. Base visual: `<v-chip>` com `:color` e `:prepend-icon` dinâmicos.

**Complexidade:** Alta. Mapeamentos de status devem ser extraídos para arquivo separado `statusMappings.ts` (portabilidade 100%).

### 3.9 command-palette (258 linhas)

**O que faz:** Paleta de comandos (Ctrl+K) com busca fuzzy, grupos e atalhos.

**Estratégia Vue:** Sem equivalente Vuetify. Recriar com `<v-dialog>` + `<v-text-field>` + `<v-list>` + lógica de busca em composable.

### 3.10 prompt-suggestions-dock (371 linhas)

**O que faz:** Dock de sugestões de prompts para o chat LIA, com categorias e animações.

**Estratégia Vue:** Componente específico LIA. Recriar com `<v-card>` + `<v-chip-group>` + transitions.

### 3.11 search-loading-animation (95 linhas)

**O que faz:** Animação de loading estilo "searching" com dots/waves.

**Estratégia Vue:** CSS animation puro. Recriar template + `<style scoped>`.

### 3.12 data-request-indicator (260 linhas)

**O que faz:** Indicador de que LIA está solicitando dados do backend.

**Estratégia Vue:** Recriar com `<v-progress-linear>` + status text.

### 3.13 setup-alert-badge (210 linhas)

**O que faz:** Badge/alert para itens de setup pendentes.

**Estratégia Vue:** `<v-alert type="warning">` + `<v-badge>` para contagem.

---

## 4. Mapeamento Detalhado de Props

### Padrão de Variantes (CVA → Vuetify props)

O projeto usa `class-variance-authority` (CVA) para variantes. Em Vuetify, variantes são props nativas:

| Conceito CVA (React) | Vuetify 3 (Vue) |
|---|---|
| `variants.variant` → classes CSS condicionais | `variant` prop (`flat`, `outlined`, `text`, `tonal`, `elevated`, `plain`) |
| `variants.size` → classes de tamanho | `size` prop (`x-small`, `small`, `default`, `large`, `x-large`) |
| `defaultVariants` | Props com valor default (`variant="flat"`) |
| `cn()` para merge classes | `:class="[]"` array syntax |

### Mapeamento de Cores LIA

| Token LIA (Tailwind) | Vuetify 3 color | Uso |
|---|---|---|
| `bg-gray-900` / `text-white` | `color="grey-darken-4"` | Primary/Default |
| `bg-status-error` | `color="error"` | Destructive/Danger |
| `bg-gray-100` | `color="grey-lighten-4"` | Secondary |
| `bg-wedo-green/15` | `color="success"` + `variant="tonal"` | Success badge |
| `bg-wedo-orange/15` | `color="warning"` + `variant="tonal"` | Warning badge |
| `bg-wedo-cyan/15` | `color="info"` + `variant="tonal"` | Info badge |
| `bg-wedo-purple/15` | `color="purple"` + `variant="tonal"` | Lilac badge |
| `border-gray-300` | — | Outline (Vuetify handles) |
| `text-gray-600` | `text-grey-darken-1` | Muted text |

### Mapeamento de Tamanhos

| shadcn/ui (Tailwind) | Vuetify 3 | Contexto |
|---|---|---|
| `h-9` (36px) | `size="small"` | Button sm |
| `h-10` (40px) | `size="default"` | Button default, Input |
| `h-11` (44px) | `size="large"` | Button lg |
| `h-5 w-9` | `size="default"` | Switch |
| `h-4 w-4` | `size="small"` | Checkbox, Radio |
| `h-2` | Default | Progress, Slider track |

---

## 5. Padrões de Composição: children → slots

### Composição Multi-componente → Componente Único

Muitos componentes shadcn/ui são composições de múltiplos sub-componentes que em Vuetify se tornam um componente único com props/slots:

| Padrão shadcn/ui (React) | Padrão Vuetify 3 (Vue) |
|---|---|
| `<Dialog>` + `<DialogTrigger>` + `<DialogContent>` + ... | `<v-dialog>` com `activator` slot |
| `<Select>` + `<SelectTrigger>` + `<SelectContent>` + `<SelectItem>` | `<v-select :items="...">` |
| `<Tooltip>` + `<TooltipTrigger>` + `<TooltipContent>` | `<v-tooltip text="...">` + `activator` slot |
| `<Avatar>` + `<AvatarImage>` + `<AvatarFallback>` | `<v-avatar :image="..." />` |
| `<Accordion>` + `<AccordionItem>` + `<AccordionTrigger>` + `<AccordionContent>` | `<v-expansion-panels>` + `<v-expansion-panel>` (title + text) |

### Padrão Activator (Vuetify)

Muitos componentes Vuetify usam o padrão `activator` slot para o trigger element:

```vue
<v-menu>
  <template v-slot:activator="{ props }">
    <v-btn v-bind="props">Trigger</v-btn>
  </template>
  <!-- conteúdo do menu -->
</v-menu>
```

Equivale ao padrão `<XxxTrigger asChild>` do shadcn/ui.

### children → default slot

```tsx
// React
<Card>{content}</Card>

// Vue
<v-card>{{ content }}</v-card>
```

### Named render props → Named slots

```tsx
// React
<Card header={<h2>Title</h2>} footer={<Button>OK</Button>}>
  {content}
</Card>

// Vue
<v-card>
  <template #title>Title</template>
  <template #text>{{ content }}</template>
  <template #actions><v-btn>OK</v-btn></template>
</v-card>
```

---

## 6. Convenções Enforçadas

### 6.1 Naming de Componentes

| React (atual) | Vue (futuro) | Regra |
|---|---|---|
| `button.tsx` | `VBtn` (Vuetify nativo) | Usar componente Vuetify |
| `status-badge.tsx` | `StatusBadge.vue` | PascalCase para custom |
| `lia-icon.tsx` | `LiaIcon.vue` | PascalCase |
| `use-candidate-filter.ts` | `useCandidateFilter.ts` | camelCase (composable) |

### 6.2 Props Interface

```tsx
// React (manter este padrão para facilitar conversão)
interface StatusBadgeProps {
  status: CandidateStatus
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  onStatusChange?: (status: CandidateStatus) => void
}
```

```vue
<!-- Vue (resultado da conversão) -->
<script setup lang="ts">
interface Props {
  status: CandidateStatus
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showIcon: true,
})
const emit = defineEmits<{
  statusChange: [status: CandidateStatus]
}>()
</script>
```

### 6.3 Event Naming

| React callback | Vue emit | Regra |
|---|---|---|
| `onSelect` | `@select` | Drop "on" prefix |
| `onStatusChange` | `@status-change` | camelCase → kebab-case |
| `onOpenChange` | `@update:model-value` | Para v-model bindings |
| `onClick` | `@click` | Native event |

### 6.4 Composição: Slot Pattern Ready

Ao criar componentes React, preferir o padrão que mapeia para slots Vue:

```tsx
// PREFERIR (slot-ready)
interface CardProps {
  children: React.ReactNode       // → <slot />
  header?: React.ReactNode        // → <slot name="header">
  footer?: React.ReactNode        // → <slot name="footer">
  actions?: React.ReactNode       // → <slot name="actions">
}

// EVITAR (difícil mapear para slots)
interface CardProps {
  renderHeader?: (data: CardData) => React.ReactNode  // render prop complexa
}
```

### 6.5 State Management: Pinia-Ready

| Padrão React (atual) | Padrão Vue (futuro) | Regra |
|---|---|---|
| `useContext(AuthCtx)` | `useAuthStore()` | Pinia store |
| `useState + useCallback` | `ref() + function` | Composable |
| `useMemo` | `computed()` | Auto-tracking |
| Prop drilling | `provide/inject` ou Pinia | — |

### 6.6 Checklist de Portabilidade por Componente

Antes de considerar um componente "migration-ready":

- [ ] Props tipadas com `interface` (não `type` inline)
- [ ] Callbacks nomeados `on*` (onSelect, onChange, etc.)
- [ ] Composição via children/named props (não render props)
- [ ] Lógica complexa extraída para hook `use-*.ts`
- [ ] Sem `React.Children.map`, `cloneElement`, ou `useImperativeHandle`
- [ ] Sem CSS-in-JS (styled-components/emotion)
- [ ] Classes via `cn()` ou ternary simples
- [ ] Sem prop drilling profundo (máx 2 níveis)
