# UX Patterns — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `ats_front` (GitHub WeDOTalent, branch `develop`)
> **SPEC-DRIVEN DEVELOPMENT** — padrões de experiência do usuário extraídos do código real.

---

## 1. Padrão de Navegação

### 1.1 Hub Navigation

- Navegação lateral via `useHubNavigation.ts`
- Store `hub.ts` gerencia estado do hub
- Layout `user.vue` como shell principal

### 1.2 Estrutura de Páginas

```
Layout (user.vue)
├── Sidebar (navegação principal)
│   ├── Dashboard
│   ├── Vagas (jobs)
│   ├── Candidatos (candidates)
│   ├── LIA (chat IA)
│   ├── Avaliações
│   ├── Sourcing
│   └── Admin (se permissão)
├── Content Area
│   ├── Header (breadcrumb, ações)
│   └── Main Content
└── Side Panels (table_side_panels)
```

### 1.3 Fluxo de Navegação Principal

```
Dashboard → Vagas → Vaga Específica → Kanban de Candidaturas
                                          ↓
                                    Detalhes do Candidato
                                          ↓
                                    Ações (mover etapa, feedback, etc.)
```

---

## 2. Chat LIA (IA Conversacional)

### 2.1 Arquitetura de Chat

```
features/lia/
├── components/
│   ├── LiaChat.vue           # Container principal
│   ├── LiaChatMessages.vue   # Lista de mensagens
│   ├── LiaChatInput.vue      # Input de texto
│   ├── BotMessage.vue        # Mensagem da IA
│   ├── UserMessage.vue       # Mensagem do usuário
│   └── ...
├── composables/
│   └── (via composables globais)
└── services/
    └── (via stores/lia.ts)
```

### 2.2 Fluxo de Mensagem

```
Usuário digita → LiaChatInput
    │
    ▼
Store lia.ts → envio HTTP
    │
    ▼
Streaming via WebSocket (ActionCable)
    │
    ▼
useMessageStreaming → atualiza BotMessage em tempo real
    │
    ▼
BotMessage renderiza resposta final
```

### 2.3 Domínios no Chat

O chat LIA suporta múltiplos domínios via `useLiaDomainConfig.ts`:

| Domínio | Contexto | Ações |
|---------|----------|-------|
| `applies` | Dentro de uma vaga | Busca, pipeline, ranking |
| `jobs` | Gestão geral | CRUD, analytics |
| `insights` | Cross-domain | Briefings, métricas |
| `messaging` | Comunicação | Emails, feedbacks |
| `autonomous` | Universal | ~73 tools |

### 2.4 Thinking Messages

Durante processamento, o chat mostra status via `useExecutionTracking.ts`:

```
🔍 Analisando sua pergunta...
📋 Planejando execução...
⚡ Executando consultas...
📊 Processando dados...
✍️ Formatando resposta...
```

---

## 3. Kanban de Candidaturas

### 3.1 Componentes

- `features/applies/` — 23 arquivos
- `stores/kanbanSelection.ts` — seleção no kanban
- `stores/selective_processes.ts` — etapas do processo

### 3.2 Etapas Default

| Posição | Etapa | Status |
|---------|-------|--------|
| 0 | Inscrição Web | `web_submission` |
| 1 | Triagem | `screening` |
| 2 | Entrevista | `interview` |
| 3 | Rejeitados | `rejected` |
| 4 | Contratados | `hired` |

### 3.3 Interações

- **Drag & Drop**: Mover candidato entre etapas
- **Bulk actions**: Selecionar múltiplos e mover
- **Click**: Ver detalhes do candidato
- **Filtros**: Busca e filtros dentro do kanban

---

## 4. Tabelas

### 4.1 Componentes de Tabela

- `components/ui/` — 130 componentes genéricos
- `stores/table.ts` — estado da tabela
- `stores/table_side_panels.ts` — painéis laterais
- `composables/useColumnResize.ts` — redimensionamento

### 4.2 Features

- Colunas redimensionáveis
- Busca e filtros
- Paginação
- Side panel com detalhes
- Células customizadas via `plugins/register-table-cells.ts`
- Export de dados

---

## 5. Avaliação de Candidatos

### 5.1 Fluxo do Recrutador

```
Configurar Avaliação
    │
    ▼
Definir Perguntas (features/questions/)
    │
    ▼
Enviar para Candidato (useEvaluationSending)
    │
    ▼
Acompanhar Respostas (features/evaluations/)
    │
    ▼
Visualizar Score/Rubrica
```

### 5.2 Fluxo do Candidato

```
Recebe link → pages/evaluations/[id]/[uid].vue
    │
    ▼
Responde perguntas (chat ou texto)
    │ (pode usar voz: useEvaluationVoiceSession)
    ▼
Respostas avaliadas automaticamente (AI)
    │
    ▼
Score calculado (rubrica 4 critérios)
```

### 5.3 Entrevista por Voz

- `composables/useInterviewSession.ts` — sessão
- `composables/useInterviewCall.ts` — chamada
- `composables/useInterviewAudio.ts` — áudio
- `pages/interviews/[account_uid]/[token].vue` — página pública

---

## 6. Sourcing

### 6.1 Fluxo

```
Recruiter configura sourcing
    │
    ▼
Auto-source (useAutoSource) ou manual
    │
    ▼
Perfis sourced (useSourcedProfiles)
    │
    ▼
WebSocket updates (useSourcingWebSocket)
    │
    ▼
Converter para candidato (ação)
```

### 6.2 Créditos

- `composables/useSearchCredits.ts` — gestão
- `composables/useCreditWebSocket.ts` — real-time updates
- `stores/searchCredits.ts` — estado global

---

## 7. Comunicação (Messaging)

### 7.1 Estrutura

```
features/messages/ — 88 arquivos (maior feature module)
├── components/
│   ├── MessageList.vue
│   ├── MessageComposer.vue
│   ├── TemplateSelector.vue
│   └── ...
├── composables/
├── services/
└── types/
```

### 7.2 Templates

- `composables/useCommunicationTemplates.ts` — templates reutilizáveis
- Templates para: feedback positivo, negativo, convite, follow-up

### 7.3 Regra de Preview

O sistema sempre mostra preview antes de enviar — alinhado com o `MessagingDomain` que nunca envia sem confirmação.

---

## 8. Componentes Compartilhados

### 8.1 components/ui/ (130 arquivos)

Componentes genéricos reutilizáveis:
- Botões, cards, modais, dialogs
- Formulários, inputs, selects
- Loading states, empty states
- Data displays (tabelas, listas, grids)
- Charts e visualizações

### 8.2 components/llm/ (8 arquivos)

Componentes específicos para interação com LLM:
- Quota display
- Usage tracking
- AI cost indicators

---

## 9. Padrões de UX

### 9.1 Confirmação antes de Ação

Todas as ações destrutivas ou em lote requerem confirmação:
- `composables/useConfirm.ts`
- `stores/confirm.ts`
- `composables/useConfirmationSound.ts` — feedback sonoro

### 9.2 Toast Notifications

- `plugins/toast.client.ts`
- Sucesso: verde
- Erro: vermelho
- Warning: amarelo

### 9.3 Loading States

- Auto-animate via `plugins/auto-animate.client.ts`
- Skeleton loaders para tabelas e listas
- Thinking messages para chat IA

### 9.4 Responsive

- Layout adapta para mobile
- Sidebar colapsável
- Tabelas com scroll horizontal

### 9.5 Auth Flow

```
Login (/) → POST /v1/sessions → JWT → stores/user.ts
    │
    ▼
Microsoft Auth (optional)
    │ useMicrosoftAuth.ts
    │ middleware/microsoft-auth.ts
    ▼
WorkOS Auth (optional)
    │ useWorkOSAuth.ts
    ▼
Dashboard (/user/dashboard)
```

---

## 10. Real-time Updates

| Feature | Mecanismo | Composable |
|---------|-----------|-----------|
| Chat LIA | ActionCable | `useCable`, `useMessageStreaming` |
| Sourcing progress | WebSocket | `useSourcingWebSocket` |
| Search credits | WebSocket | `useCreditWebSocket` |
| Apply collection | WebSocket | `useApplyCollectionChannel` |
| Domain messages | Channel | `useDomainMessageChannel` |

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| LIA Chat | `ats_front/features/lia/` |
| Messages | `ats_front/features/messages/` |
| Candidates | `ats_front/features/candidates/` |
| Jobs | `ats_front/features/jobs/` |
| Applies | `ats_front/features/applies/` |
| UI Components | `ats_front/components/ui/` |
| Composables | `ats_front/composables/` |
| Stores | `ats_front/stores/` |
