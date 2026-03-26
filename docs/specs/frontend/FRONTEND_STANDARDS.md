# Frontend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `ats_front` (GitHub WeDOTalent, branch `develop`)
> **SPEC-DRIVEN DEVELOPMENT** — padrões reais extraídos do codebase.

---

## 1. Stack

| Tecnologia | Versão | Papel |
|-----------|--------|-------|
| **Nuxt 3** | 3.x | Framework SSR/SPA |
| **Vue 3** | 3.x | UI framework (Composition API) |
| **Vuetify 3** | 3.x | Component library (Material Design) |
| **Pinia** | 2.x | State management |
| **TypeScript** | 5.x | Tipagem (predominante) |
| **pnpm** | — | Package manager |
| **Histoire** | — | Component development / storybook |

---

## 2. Estrutura de Diretórios

```
ats_front/
├── pages/                  # Rotas Nuxt (file-based routing)
│   ├── index.vue           # Login/landing
│   ├── user/               # App principal (autenticado)
│   │   ├── dashboard/      # Dashboard
│   │   ├── candidates/     # Gestão de candidatos
│   │   ├── jobs/           # Vagas + applies
│   │   ├── lia/            # Chat LIA (IA)
│   │   ├── evaluations/    # Avaliações
│   │   ├── sourcing/       # Sourcing
│   │   ├── admin/          # Administração
│   │   │   ├── accounts/
│   │   │   ├── ai_costs/
│   │   │   ├── business/
│   │   │   ├── dashboard.vue
│   │   │   ├── job_status/
│   │   │   ├── roles/
│   │   │   ├── sectors/
│   │   │   ├── users/
│   │   │   └── whatsapp_configurations/
│   │   ├── settings/       # Configurações do usuário
│   │   └── microsoft.vue   # Auth Microsoft
│   ├── auth/               # Callback de auth
│   ├── evaluations/        # Avaliação pública (candidato)
│   ├── interviews/         # Entrevista pública
│   ├── scheduling/         # Agendamento público
│   ├── setups/             # Configuração inicial
│   └── vagas/              # Página pública de vagas
├── features/               # Feature modules (encapsulados)
│   ├── lia/                # Chat IA (46 arquivos)
│   ├── messages/           # Comunicação (88 arquivos)
│   ├── candidates/         # Candidatos (48 arquivos)
│   ├── jobs/               # Vagas (38 arquivos)
│   ├── admin/              # Admin (44 arquivos)
│   ├── applies/            # Candidaturas (23 arquivos)
│   ├── evaluations/        # Avaliações (8 arquivos)
│   ├── interview/          # Entrevistas (5 arquivos)
│   ├── prompt/             # Prompt UI (5 arquivos)
│   ├── questions/          # Perguntas (5 arquivos)
│   ├── smart-calendar/     # Calendário (4 arquivos)
│   ├── control_panel/      # Painel de controle (4 arquivos)
│   ├── selective_process/  # Processos seletivos (4 arquivos)
│   ├── activity_logs/      # Logs de atividade (7 arquivos)
│   ├── setups/             # Configurações (6 arquivos)
│   ├── benefits/           # Benefícios (5 arquivos)
│   ├── sourcing/           # (via components/sourcing)
│   ├── addresses/          # Endereços (3 arquivos)
│   ├── feedbacks/          # Feedbacks (2 arquivos)
│   ├── languages/          # Idiomas (2 arquivos)
│   ├── remunerations/      # Remunerações (2 arquivos)
│   └── skills/             # Competências (2 arquivos)
├── components/
│   ├── ui/                 # Componentes genéricos (130 arquivos)
│   ├── llm/                # Componentes LLM (8 arquivos)
│   ├── shared/             # Componentes compartilhados (3 arquivos)
│   ├── sourcing/           # Sourcing components (3 arquivos)
│   └── applies/            # Apply components (1 arquivo)
├── composables/            # Vue composables (57 arquivos)
├── stores/                 # Pinia stores (18 arquivos)
├── plugins/                # Nuxt plugins (11 arquivos)
├── layouts/                # Layouts (5: admin, blank, evaluations, setup, user)
├── config/                 # Configurações (vuetify.config.ts)
├── constants/              # Constantes
├── types/                  # TypeScript types
├── middleware/             # Route middleware
└── public/                 # Assets estáticos
```

---

## 3. Padrões de Código

### 3.1 Vue Components

- **Composition API** com `<script setup lang="ts">`
- **SFC** (Single File Components)
- Sem Options API — 100% Composition API

### 3.2 Naming Conventions

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Componentes | PascalCase | `CandidateCard.vue` |
| Composables | camelCase com `use` prefix | `useCandidateFilters.ts` |
| Stores | camelCase | `stores/lia.ts` |
| Pages | kebab-case ou param `[id]` | `pages/user/jobs/[id]/index.vue` |
| Types | PascalCase | `types/interview.ts` |
| Constants | UPPER_SNAKE | `constants/vagas.js` |

### 3.3 Feature Module Pattern

Cada feature é auto-contida em `features/`:
```
features/candidates/
├── components/       # Componentes específicos
├── composables/      # Lógica reutilizável
├── services/         # API calls
├── types/            # Tipos TypeScript
└── utils/            # Utilitários
```

### 3.4 TypeScript

- Extensão `.ts` para composables, stores, types, plugins
- Extensão `.vue` para componentes
- 1 arquivo `.js` remanescente: `composables/useActiveSection.js`
- Types em `types/` e inline nos componentes

---

## 4. Composables (57)

| Composable | Função |
|-----------|--------|
| `useCable` | WebSocket/ActionCable connection |
| `useMessageStreaming` | Streaming de mensagens do chat |
| `useDomainMessages` | Mensagens por domínio (applies, jobs, etc.) |
| `useDomainMessageChannel` | Canal de mensagem por domínio |
| `useCandidateFilters` | Filtros de candidatos |
| `useCandidateMatches` | Matching de candidatos |
| `useSimilarCandidates` | Candidatos similares |
| `useAudioRecorder` | Gravação de áudio |
| `useAudioPlayer` | Reprodução de áudio |
| `useAudioMessages` | Mensagens de áudio |
| `useVoiceRecorder` | Gravação de voz |
| `useHubVoiceCommand` | Comandos de voz do hub |
| `useInterviewSession` | Sessão de entrevista |
| `useInterviewCall` | Chamada de entrevista |
| `useInterviewAudio` | Áudio de entrevista |
| `useEvaluationSending` | Envio de avaliações |
| `useEvaluationVoiceSession` | Avaliação por voz |
| `useSourcings` | Sourcing operations |
| `useSourcedProfiles` | Perfis sourced |
| `useSourcingWebSocket` | WebSocket de sourcing |
| `useTalentSearch` | Busca de talentos |
| `useAutoSource` | Auto-source automático |
| `useSearchCredits` | Créditos de busca |
| `useCreditWebSocket` | WebSocket de créditos |
| `useSmartCalendar` | Calendário inteligente |
| `useCalendarAgenda` | Agenda do calendário |
| `useLiaDomainConfig` | Configuração de domínio LIA |
| `useLlmQuota` | Quota de LLM |
| `useLlmUsages` | Uso de LLM |
| `useExecutionTracking` | Tracking de execução |
| `useFormatter` | Formatação de dados |
| `useTextFormatting` | Formatação de texto |
| `useClipboard` | Clipboard operations |
| `useColumnResize` | Redimensionamento de colunas |
| `useConfirm` | Diálogos de confirmação |
| `useConfirmationSound` | Som de confirmação |
| `useCommunicationTemplates` | Templates de comunicação |
| `useContactEnrichment` | Enriquecimento de contatos |
| `useCurriculumParser` | Parser de currículo |
| `useCustomTheme` | Tema customizado |
| `useExpansion` | Expansion panels |
| `useHubNavigation` | Navegação do hub |
| `useArchetypes` | Arquétipos |
| `useIndustries` | Indústrias |
| `useSectors` | Setores |
| `useLanguages` | Idiomas |
| `useSkills` | Competências |
| `useScoringDisplay` | Display de scoring |
| `useSelectiveProcessTriggers` | Triggers de processo seletivo |
| `useSessionTimer` | Timer de sessão |
| `useValidators` | Validadores de formulário |
| `useAppliesImport` | Importação de candidaturas |
| `useApplyCollectionChannel` | Canal de coleção de applies |
| `useCreateJobModal` | Modal de criar vaga |
| `useJobDuplication` | Duplicação de vaga |
| `useMicrosoftAuth` | Auth Microsoft |
| `useWorkOSAuth` | Auth WorkOS |

---

## 5. Stores (Pinia — 18)

| Store | Arquivo | Função |
|-------|---------|--------|
| `user` | `stores/user.ts` | Auth, sessão, dados do usuário |
| `lia` | `stores/lia.ts` | Estado do chat LIA |
| `hub` | `stores/hub.ts` | Hub de navegação |
| `ui` | `stores/ui.ts` | Estado da UI global |
| `uiContext` | `stores/uiContext.ts` | Contexto de UI |
| `confirm` | `stores/confirm.ts` | Diálogos de confirmação |
| `dialog` | `stores/dialog.ts` | Diálogos genéricos |
| `table` | `stores/table.ts` | Estado de tabelas |
| `table_side_panels` | `stores/table_side_panels.ts` | Painéis laterais de tabela |
| `benefit` | `stores/benefit.ts` | Benefícios |
| `candidate_feedbacks` | `stores/candidate_feedbacks.ts` | Feedbacks de candidatos |
| `chatSync` | `stores/chatSync.ts` | Sincronização do chat |
| `kanbanSelection` | `stores/kanbanSelection.ts` | Seleção no kanban |
| `liaGlobalAudioTrigger` | `stores/liaGlobalAudioTrigger.ts` | Trigger global de áudio |
| `searchCredits` | `stores/searchCredits.ts` | Créditos de busca |
| `selective_processes` | `stores/selective_processes.ts` | Processos seletivos |
| `sourcingFilters` | `stores/sourcingFilters.ts` | Filtros de sourcing |
| `workspaces` | `stores/workspaces.ts` | Workspaces |

---

## 6. Plugins (11)

| Plugin | Tipo | Função |
|--------|------|--------|
| `api.ts` | universal | Configuração da API |
| `axios.ts` | universal | HTTP client |
| `vuetify.ts` | universal | Vuetify setup |
| `vue-flow.ts` | universal | Vue Flow (diagramas) |
| `auto-animate.client.ts` | client | Auto-animate |
| `toast.client.ts` | client | Notificações toast |
| `vue-tel-input.client.ts` | client | Input de telefone |
| `vue-the-mask.client.ts` | client | Máscaras de input |
| `websocket.client.ts` | client | WebSocket/ActionCable |
| `register-table-cells.ts` | universal | Células de tabela customizadas |
| `suppress-logs.client.ts` | client | Suprime logs de console |

---

## 7. Layouts

| Layout | Arquivo | Uso |
|--------|---------|-----|
| `user` | `layouts/user.vue` | App principal (autenticado) |
| `admin` | `layouts/admin.vue` | Painel admin |
| `blank` | `layouts/blank.vue` | Sem layout (login, etc.) |
| `evaluations` | `layouts/evaluations.vue` | Tela de avaliação pública |
| `setup` | `layouts/setup.vue` | Configuração inicial |

---

## 8. Rotas (34 páginas)

### Páginas Públicas (sem auth)

| Rota | Página | Função |
|------|--------|--------|
| `/` | `index.vue` | Login |
| `/vagas/[slug]/[account_slug]` | Vagas públicas | Career page |
| `/evaluations/[id]/[uid]` | Avaliação | Candidato responde perguntas |
| `/interviews/[account_uid]/[token]` | Entrevista | Entrevista ao vivo |
| `/scheduling/[account_uid]/[token]` | Agendamento | Auto-agendamento |
| `/terms` | Termos de uso | — |
| `/cookies` | Política de cookies | — |

### Páginas Autenticadas (`/user/`)

| Rota | Página | Função |
|------|--------|--------|
| `/user/dashboard` | Dashboard | Visão geral |
| `/user/candidates` | Candidatos | Lista e busca |
| `/user/candidates/[id]` | Candidato | Perfil detalhado |
| `/user/candidates/sourcings/[id]` | Sourcing | Perfis sourced |
| `/user/jobs` | Vagas | Lista de vagas |
| `/user/jobs/[id]` | Vaga | Detalhes + kanban |
| `/user/jobs/[id]/applies/[apply_id]` | Candidatura | Detalhes da apply |
| `/user/lia` | LIA Chat | Lista de chats |
| `/user/lia/[uid]` | LIA Chat | Chat específico |
| `/user/evaluations` | Avaliações | Gestão de avaliações |
| `/user/sourcing/[id]/chat` | Sourcing Chat | Chat de sourcing |
| `/user/settings` | Configurações | Settings do user |
| `/user/microsoft` | Microsoft | Auth callback |

### Páginas Admin (`/user/admin/`)

| Rota | Função |
|------|--------|
| `/user/admin/dashboard` | Dashboard admin |
| `/user/admin/accounts` | Contas |
| `/user/admin/users` | Usuários |
| `/user/admin/roles` | Permissões |
| `/user/admin/ai_costs` | Custos de IA |
| `/user/admin/business` | Negócios |
| `/user/admin/job_status` | Status de vagas |
| `/user/admin/sectors` | Setores |
| `/user/admin/whatsapp_configurations` | WhatsApp |

---

## 9. Comunicação com Backend

### 9.1 HTTP (Axios)

- Plugin `plugins/axios.ts` configura Axios globalmente
- Plugin `plugins/api.ts` configura endpoints
- Base URL configurada via `NUXT_PUBLIC_API_URL`

### 9.2 WebSocket (ActionCable)

- Plugin `plugins/websocket.client.ts`
- Composable `useCable.ts` gerencia conexão
- Canais: MessageChannel (chat), CreditChannel (créditos)

### 9.3 Chat LIA

O chat usa uma combinação:
1. HTTP POST para enviar mensagem
2. WebSocket (ActionCable) para receber respostas em streaming
3. `useDomainMessages.ts` + `useMessageStreaming.ts` para gestão

---

## 10. Regras de Código

1. **Composition API only** — nunca Options API
2. **TypeScript** — tipagem obrigatória para composables e stores
3. **Feature modules** — encapsular por feature em `features/`
4. **Vuetify components** — usar Vuetify como base (v-card, v-btn, etc.)
5. **Responsive** — suportar mobile e desktop
6. **PT-BR** — labels e textos em português brasileiro
7. **Client plugins** — marcar com `.client.ts` quando requerem DOM
8. **No console.log** — usar `suppress-logs.client.ts` em produção

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Nuxt Config | `ats_front/nuxt.config.ts` |
| Vuetify Config | `ats_front/config/vuetify.config.ts` |
| Package.json | `ats_front/package.json` |
| CLAUDE.md | `ats_front/CLAUDE.md` |
| AGENTS.md | `ats_front/AGENTS.md` |
