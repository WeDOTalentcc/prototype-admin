# Design System — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `ats_front/config/vuetify.config.ts` + componentes + análise visual
> **SPEC-DRIVEN DEVELOPMENT** — tokens, componentes e regras de design extraídos do código.

---

## 1. Framework

| Item | Valor |
|------|-------|
| **Framework CSS** | Vuetify 3 (Material Design 3) |
| **Customização** | `config/vuetify.config.ts` |
| **Component Library** | Vuetify + componentes custom em `components/ui/` (130 arquivos) |
| **Icons** | Material Design Icons (MDI) |
| **Tipografia** | Vuetify default (Roboto) + customizações |

---

## 2. Cores

### 2.1 Cores da Marca

| Token | Hex | Uso |
|-------|-----|-----|
| Primary | `#60BED1` | Cor principal — botões, links, highlights |
| Secondary | TBD (via vuetify.config.ts) | Cor secundária |
| Accent | `#00B8B8` | Cor de acento (usada em chat — ver issue #CHAT-001) |

### 2.2 Cores Semânticas

| Token | Uso |
|-------|-----|
| `success` | Verde — ações concluídas |
| `error` | Vermelho — erros, rejeição |
| `warning` | Amarelo — alertas |
| `info` | Azul — informações |

### 2.3 Issue Conhecida: Chat Colors

O chat LIA (`BotMessage.vue`, `UserMessage.vue`) usa `#00B8B8` hardcoded em vez do token `primary` (`#60BED1`). Documentado em `docs/JIRA_CARD_CHAT_DESIGN_FIX.md`.

---

## 3. Componentes

### 3.1 Componentes UI Base (130 arquivos)

Localização: `components/ui/`

Categorias identificadas:
- **Layout**: cards, containers, grids, panels
- **Navigation**: tabs, breadcrumbs, menus
- **Data Display**: tables, lists, stats, badges
- **Forms**: inputs, selects, date pickers, file uploads
- **Feedback**: alerts, toasts, loaders, skeletons
- **Overlays**: modals, dialogs, drawers, side panels
- **Chat**: message bubbles, input bar, typing indicators

### 3.2 Componentes LLM (8 arquivos)

Localização: `components/llm/`

- Quota display (uso de LLM)
- Cost indicators
- Usage tracking widgets

### 3.3 Componentes por Feature

Cada `features/` module tem seus próprios componentes encapsulados:

| Feature | Componentes |
|---------|-------------|
| `features/lia/` | Chat container, messages, input, bot/user messages |
| `features/messages/` | Message list, composer, templates |
| `features/candidates/` | Candidate card, profile, filters |
| `features/jobs/` | Job card, kanban, analytics |
| `features/applies/` | Apply card, pipeline view |
| `features/admin/` | Admin panels, config forms |

---

## 4. Tipografia

### 4.1 Config Atual

Vuetify 3 default: Roboto + Material Design typography scale.

### 4.2 Issues Identificadas

| Issue | Local | Atual | Esperado |
|-------|-------|-------|----------|
| Font-size chat messages | BotMessage.vue | 13.5px | Design System standard |
| Font-size user messages | UserMessage.vue | 13.5px | Design System standard |

---

## 5. Spacing

Segue a grade de spacing do Vuetify (4px base):

| Token | Valor |
|-------|-------|
| `pa-1` / `ma-1` | 4px |
| `pa-2` / `ma-2` | 8px |
| `pa-3` / `ma-3` | 12px |
| `pa-4` / `ma-4` | 16px |
| `pa-5` / `ma-5` | 20px |
| `pa-6` / `ma-6` | 24px |

---

## 6. Breakpoints

Vuetify 3 default breakpoints:

| Breakpoint | Valor | Alvo |
|-----------|-------|------|
| `xs` | < 600px | Mobile |
| `sm` | 600-960px | Tablet portrait |
| `md` | 960-1264px | Tablet landscape |
| `lg` | 1264-1904px | Desktop |
| `xl` | > 1904px | Large desktop |

---

## 7. Elevação e Sombras

Segue o sistema de elevação do Material Design via Vuetify:

| Classe | Uso |
|--------|-----|
| `elevation-0` | Sem sombra (flat) |
| `elevation-1` | Cards base |
| `elevation-2` | Cards hover |
| `elevation-4` | Modais e drawers |
| `elevation-8` | Popups e menus |

---

## 8. Ícones

| Library | Prefixo | Uso |
|---------|---------|-----|
| Material Design Icons | `mdi-` | Principal |

Exemplos de ícones usados:
- `mdi-magnify` — busca
- `mdi-plus` — adicionar
- `mdi-delete` — deletar
- `mdi-pencil` — editar
- `mdi-account` — candidato
- `mdi-briefcase` — vaga
- `mdi-robot` — LIA/IA
- `mdi-send` — enviar mensagem

---

## 9. Tema (Dark/Light)

- Vuetify 3 suporta dark/light mode
- `composables/useCustomTheme.ts` gerencia tema
- Theme tokens definidos em `config/vuetify.config.ts`

---

## 10. Padrões de Componentes

### 10.1 Cards

```vue
<v-card variant="outlined" rounded="lg">
  <v-card-title>Título</v-card-title>
  <v-card-text>Conteúdo</v-card-text>
  <v-card-actions>
    <v-btn>Ação</v-btn>
  </v-card-actions>
</v-card>
```

### 10.2 Tabelas

```vue
<DataTable
  :items="items"
  :columns="columns"
  :loading="loading"
  @row-click="onRowClick"
/>
```

Custom cells via `plugins/register-table-cells.ts`.

### 10.3 Formulários

```vue
<v-form ref="form" v-model="valid">
  <v-text-field
    v-model="name"
    :rules="[rules.required]"
    label="Nome"
  />
</v-form>
```

Validadores em `composables/useValidators.ts`.

### 10.4 Diálogos

```vue
<v-dialog v-model="dialog" max-width="500">
  <v-card>
    <v-card-title>Confirmar</v-card-title>
    <v-card-actions>
      <v-btn @click="confirm">Sim</v-btn>
      <v-btn @click="cancel">Não</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

Gestão via `stores/dialog.ts` + `composables/useConfirm.ts`.

---

## 11. Animações

| Tipo | Implementação |
|------|--------------|
| Page transitions | Nuxt built-in |
| List animations | `auto-animate` plugin |
| Loading states | Vuetify progress/skeleton |
| Chat typing | Custom CSS animation |

---

## 12. Acessibilidade

| Item | Status |
|------|--------|
| Keyboard navigation | Via Vuetify (built-in) |
| Screen reader | Via Vuetify ARIA |
| Color contrast | Needs audit |
| Focus indicators | Via Vuetify |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Vuetify Config | `ats_front/config/vuetify.config.ts` |
| UI Components | `ats_front/components/ui/` |
| LLM Components | `ats_front/components/llm/` |
| Custom Theme | `ats_front/composables/useCustomTheme.ts` |
| Chat Design Issue | `docs/JIRA_CARD_CHAT_DESIGN_FIX.md` |
