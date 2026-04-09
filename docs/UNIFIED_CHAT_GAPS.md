# Unified Chat — Gap Tracker

> Documento de tracking para garantir ZERO gaps. Atualizar status conforme implementa.

## Scorecard Atual

- REAL handlers/buttons: 18
- MOCK buttons (zero handler): 7
- PARTIAL implementations: 4
- Dead imports: 2
- Dead code: 1

---

## MOCK (7 botoes sem funcionalidade)

### M1. Copy button nas mensagens
- Arquivo: UnifiedMessageList.tsx - MessageActions
- Fix: navigator.clipboard.writeText + toast
- Status: PENDENTE

### M2. ThumbsUp button nas mensagens
- Arquivo: UnifiedMessageList.tsx - MessageActions
- Fix: POST /lia/feedback/thumbs via feedback-api.ts
- Status: PENDENTE

### M3. ThumbsDown button nas mensagens
- Fix: Mesmo que M2 com thumbs down
- Status: PENDENTE

### M4. Insert (Plus) button nas mensagens
- Fix: Copiar conteudo para o input (prefill)
- Status: PENDENTE

### M5. Renomear no menu (...)
- Arquivo: UnifiedChatHeader.tsx
- Fix: Inline input + PATCH /conversations/{id} (ENDPOINT NAO EXISTE)
- Status: PENDENTE

### M6. Mudar icone no menu (...)
- Fix: Emoji picker + localStorage
- Status: PENDENTE

### M7. Excluir no menu (...)
- Fix: Confirmacao + DELETE /conversations/{id} (endpoint EXISTE)
- Status: PENDENTE

---

## PARTIAL (4 implementacoes incompletas)

### P1. File attachment UI coleta mas NUNCA envia
- Problema: attachedFile state populado mas sendChatMessage ignora
- Fix: Enviar via FormData ou incluir no WS context
- Status: PENDENTE

### P2. Mention (@) so digita caractere sem autocomplete
- Fix: Dropdown autocomplete com vagas/candidatos ou remover opcao
- Status: PENDENTE

### P3. SlidersHorizontal (settings) botao sem onClick
- Fix: Popover com toggle scope (pagina vs global)
- Status: PENDENTE

### P4. HITL auto-confirm checkbox valor ignorado
- Fix: Passar boolean para persistir preferencia
- Status: PENDENTE

---

## FEATURES FALTANTES

### F1. Background Tasks rendering
- Componentes: BackgroundAgentsStatus + BackgroundTaskNotification
- Dados: chatBackgroundTasks, clearBackgroundTask
- Status: PENDENTE

### F2. Fairness Warnings rendering
- Componente: FairnessWarningBanner
- Dados: chatFairnessWarnings, dismissFairnessWarnings
- Status: PENDENTE

### F3. Prefill message listener
- Dispatch: InlineChatBridge envia lia:prefill-message
- Listener: NINGUEM escuta
- Status: PENDENTE

---

## DEAD CODE

### D1. ChatBubbleBase importado mas nao usado em UnifiedMessageList
### D2. SuggestionCard, ConversationMeta types nunca usados

---

## FEATURES GRANDES (sprints futuros)

- Talent Pool backend (7 REST endpoints) - CRITICO
- Agent Studio conversacional (chat-based creation)
- Calibration unification (2 modais duplicados)
- Wizard migration (96 files, 26K lines)
- Template CRUD backend
