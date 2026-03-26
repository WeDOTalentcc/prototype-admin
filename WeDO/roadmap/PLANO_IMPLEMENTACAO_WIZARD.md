# Plano de Implementação COMPLETO: Smart Wizard Inteligente da LIA

**Data:** 01 de Fevereiro de 2026  
**Versão:** 4.0 (ATUALIZADO)  
**Arquivo Alvo:** `plataforma-lia/src/components/expanded-chat-modal.tsx`

---

## Objetivo Principal

Transformar o wizard de criação de vagas em uma experiência verdadeiramente inteligente onde:
- **10ª vaga criada é 80% mais rápida que a 1ª** (reutilização de catálogo)
- **LIA interpreta comandos em linguagem natural** ("mude salário para 15k")
- **Qualidade WSI garantida** por Quality Gates antes de gerar perguntas
- **Chat e painel sincronizados** bidirecionalmente
- **Orquestrador unificado** para wizard, análises e ações

---

## IMPORTANTE: Serviços Existentes - NÃO REIMPLEMENTAR

Antes de implementar qualquer funcionalidade, verificar se já existe. Os seguintes serviços **JÁ ESTÃO IMPLEMENTADOS**:

| Serviço | Arquivo | Linhas | Funcionalidade | Usar Em |
|---------|---------|--------|----------------|---------|
| **Pearch AI** | `pearch_service.py` | 1043 | Busca global de candidatos via API v2 | Fase de busca |
| **Market Benchmark** | `market_benchmark_service.py` | 703 | Benchmark de salários via web search | Fase de salário |
| **Intelligence Layer** | `intelligence_layer_service.py` | ~500 | Pattern Detection, Confidence Adjuster | Quality Gates |
| **Recruiter Personalization** | `recruiter_personalization_service.py` | ~400 | Preferências por recrutador | Smart Start |
| **Skills Catalog** | `skills_catalog_service.py` | ~300 | Catálogo de skills por área | Competências |
| **Confidence Policy** | `confidence_policy_service.py` | ~200 | Cálculo determinístico de confiança | Quality Gates |
| **Conversation Memory** | `conversation_memory.py` | ~400 | Persistência de conversas | Memória |
| **Tool Registry** | `tool_registry.py` | ~600 | 23 tools registradas | Tool Calling |

### Hooks Frontend Existentes (NOVO!)

| Hook | Arquivo | Linhas | Funcionalidade | Status |
|------|---------|--------|----------------|--------|
| **useWizardNavigation** | `hooks/useWizardNavigation.ts` | 258 | Navegação via chat, validação de stages | ✅ Integrado |
| **useWSIQualityGates** | `hooks/useWSIQualityGates.ts` | 170 | Quality score, bloqueio <70%, barra visual | ✅ Integrado |
| **useChatSync** | `hooks/useChatSync.ts` | 336 | Rastreio de mudanças, sincronização bidirecional | ✅ Integrado |
| **useWizardOrchestrator** | `hooks/useWizardOrchestrator.ts` | 254 | Orquestrador unificado, mapeamento de campos | ✅ Integrado |
| **useWizardState** | `hooks/useWizardState.ts` | ~200 | Estado centralizado do wizard | ✅ Integrado |

### Componentes Frontend Existentes

| Componente | Arquivo | Funcionalidade |
|------------|---------|----------------|
| `ConfidenceIndicator` | `job-creation/confidence-indicator.tsx` | Mostra nível de confiança visual |
| `FieldOriginBadge` | `job-creation/field-origin-badge.tsx` | Mostra origem (inferido, default, benchmark) |
| `FinalReviewPanel` | `job-creation/final-review-panel.tsx` | Painel de revisão final |
| `ScreeningQuestionsPanel` | `job-creation/ScreeningQuestionsPanel.tsx` | Painel de perguntas WSI |
| `WSIQualityBar` | `expanded-chat/components/WSIQualityBar.tsx` | Barra visual de qualidade |

---

## Resumo das Fases (STATUS ATUALIZADO)

| # | Fase | Descrição | Estimativa | Status | Dependências |
|---|------|-----------|------------|--------|--------------|
| **1** | Smart Start + Catálogo | Integração com dados cadastrados | 4-5 dias | ✅ CONCLUÍDA | - |
| **2** | Navegação + Comandos | Comandos de edição via chat | 6-8 dias | ✅ CONCLUÍDA | Fase 1 |
| **3** | Quality Gates para WSI | Validação de qualidade de dados | 4-5 dias | ✅ CONCLUÍDA | Fase 2 |
| **4** | Sincronização Chat ↔ Painel | Bidirecional em tempo real | 5-6 dias | ✅ CONCLUÍDA | Fases 2, 3 |
| **5** | Orquestrador Unificado | Endpoint único de roteamento | 6-8 dias | ✅ CONCLUÍDA | Fase 2 |
| **6** | Tool Calling | Integrar 23 tools no wizard | 5-6 dias | ✅ CONCLUÍDA | Fase 5 |
| **7** | Memória Conversacional | Contexto persistente | 5-6 dias | ✅ CONCLUÍDA | Fase 5 |
| **8** | Fast Track | Reutilização de vagas anteriores | 8-10 dias | ✅ CONCLUÍDA | - |
| **9** | UX e Qualidade | Testes, acessibilidade, polish | 8-10 dias | ✅ CONCLUÍDA | Todas |

---

## FASE 1: Smart Start + Integração com Catálogo ✅ CONCLUÍDA

### Itens Implementados

| # | Tarefa | Descrição | Status |
|---|--------|-----------|--------|
| 1.1 | Verificar catálogo no início | LIA consulta políticas/competências ao abrir wizard | ✅ |
| 1.2 | Mensagem inicial dinâmica | Adaptar saudação baseado na maturidade dos dados | ✅ |
| 1.3 | Pré-preencher painel lateral | Mostrar dados do catálogo como sugestões editáveis | ✅ |
| 1.4 | Reduzir campos obrigatórios | Empresas com catálogo: apenas cargo + departamento | ✅ |
| 1.5 | Endpoint catalog-status | Retorna score de maturidade (0-100) | ✅ |
| 1.6 | Endpoint smart-wizard-greeting | Saudação personalizada por nível | ✅ |

---

## FASE 2: Navegação Flexível + Comandos de Edição ✅ CONCLUÍDA

### Objetivo
Permitir que o recrutador navegue livremente e faça edições via chat, eliminando o fluxo rígido de etapas.

### Implementação

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 2.1 | Navegação via chat | "Volte para salário", "Pule para revisão" | ✅ | `useWizardNavigation.ts:56` |
| 2.2 | Interpretador de comandos de edição | "Mude senioridade para Sênior", "Adicione Python" | ✅ | `expanded-chat-modal.tsx:6141-6312` |
| 2.3 | LLM decide se pode pular etapas | Verificar se dados suficientes para avançar | ✅ | `useWizardNavigation.ts:57` |
| 2.4 | Feedback loop de ajustes | Usuário pede → LLM interpreta → Atualiza → Confirma | ✅ | `expanded-chat-modal.tsx:6195-6312` |

### Detalhes da Implementação

**Hook `useWizardNavigation`** (258 linhas):
- `handleChatNavigation(targetStage)` - Navega via chat com validação
- `canNavigateToStage(stage)` - Verifica se pode navegar (dados suficientes)
- `getStageValidation(stage)` - Valida campos obrigatórios
- `isStageAccessible(stage)` - Verifica acessibilidade

**Comandos de Edição** (linha 6141-6312):
- Parsing de comandos de navegação ("volte para", "pule para")
- Parsing de comandos de edição ("mude X para Y", "adicione X")
- Handler para salário: `parseSalaryValue()` - "15k", "R$ 15.000"
- Handler para skills: adicionar/remover competências

**Comandos Suportados:**
| Padrão | Campo Afetado | Exemplo |
|--------|---------------|---------|
| "mude X para Y" | Qualquer campo | "mude senioridade para sênior" |
| "adicione X" | Skills, benefícios | "adicione Python nas skills" |
| "remova X" | Skills, benefícios | "remova vale combustível" |
| "volte para X" | Navegação | "volte para salário" |
| "pule para X" | Navegação | "pule para revisão" |

---

## FASE 3: Quality Gates para WSI ✅ CONCLUÍDA

### Objetivo
Garantir que o recrutador forneça dados suficientes para gerar perguntas de triagem WSI de alta qualidade.

### Implementação

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 3.1 | Definir requisitos mínimos WSI | 5 skills técnicas, 3 comportamentais, responsabilidades | ✅ | `useWSIQualityGates.ts:37-48` |
| 3.2 | Barra de qualidade visual | Mostrar 0-100% de completude no painel | ✅ | `WSIQualityBar.tsx` + linha 7523 |
| 3.3 | Bloquear avanço se < 70% | LIA pede mais dados antes de gerar perguntas | ✅ | `expanded-chat-modal.tsx:3762-3781` |
| 3.4 | Follow-up inteligente | LIA faz perguntas específicas para campos faltantes | ✅ | Via orchestrator |
| 3.5 | Preview de qualidade WSI | Mostrar estimativa da qualidade das perguntas | ✅ | `WSIQualityBar` com score color |

### Detalhes da Implementação

**Hook `useWSIQualityGates`** (170 linhas):

```typescript
const QUALITY_THRESHOLDS = {
  TECHNICAL_SKILLS_MIN: 5,     // Peso: 8 × 5 = 40 pontos
  BEHAVIORAL_MIN: 3,           // Peso: 10 × 3 = 30 pontos
  RESPONSIBILITIES_MIN: 3,     // Peso: 5 × 3 = 15 pontos
  SENIORITY_WEIGHT: 5,         // 5 pontos
  WORK_MODEL_WEIGHT: 5,        // 5 pontos
  DESCRIPTION_MIN_CHARS: 200,  // 5 pontos
}
// Total máximo: 100 pontos
// Mínimo para avançar: 70 pontos
```

**Retorno do hook:**
- `score: number` - Score 0-100
- `fields: WSIQualityField[]` - Status de cada campo
- `canAdvance: boolean` - true se score >= 70
- `scoreColor: 'green' | 'yellow' | 'red'`
- `summaryText: string` - "Adicione mais 2 skills técnicas"

**Componente `WSIQualityBar`:**
- Visível nas stages 'competencies' e 'wsi-questions'
- Barra de progresso colorida (verde/amarelo/vermelho)
- Lista de campos com status (✓ / ⚠)

---

## FASE 4: Sincronização Chat ↔ Painel ✅ CONCLUÍDA

### Objetivo
Criar uma experiência bidirecional onde edições no painel refletem no chat e vice-versa.

### Implementação

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 4.1 | Chat atualiza painel em tempo real | Digitou salário → painel reflete | ✅ | Via orchestrator |
| 4.2 | Painel atualiza chat | Editou campo → LIA confirma no chat | ✅ | `useChatSync.ts` |
| 4.3 | Indicadores visuais de origem | "Sugerido pela LIA" vs "Definido por você" | ✅ | `FieldOriginBadge` |
| 4.4 | Animações de sincronização | Feedback visual quando dados sincronizam | ⚠️ Parcial | CSS transitions |

### Detalhes da Implementação

**Hook `useChatSync`** (336 linhas):

```typescript
interface FieldChange {
  field: string
  oldValue: any
  newValue: any
  source: 'panel' | 'chat' | 'orchestrator'
  timestamp: Date
  displayLabel?: string
}
```

**Funções principais:**
- `trackFieldChange(change)` - Registra mudança de campo
- `generateChangeSummary()` - Resume mudanças para mensagem
- `generateLLMContext()` - Contexto para LLM (histórico de edições)
- `getGroupedChanges()` - Agrupa mudanças próximas

**Labels de campos:**
- cargo, area, gestor, localidade, modeloTrabalho
- minSalary, maxSalary, bonus
- technicalSkill, behavioralCompetency, wsiQuestion

---

## FASE 5: Orquestrador Unificado ✅ 95% CONCLUÍDA

### Objetivo
Criar um único ponto de entrada que roteia mensagens para wizard, análises ou ações conforme a intenção detectada.

### Implementação

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 5.1 | Criar endpoint único | Roteia para wizard, análise, ações, etc. | ✅ | Backend + `orchestrateWizardMessage()` |
| 5.2 | Detecção de intenção robusta | "Criar vaga" vs "Analisar candidato" vs "Executar ação" | ✅ | Backend LLM |
| 5.3 | Chat livre usa mesmo orquestrador | Super Chat não depende do wizard | ✅ | `lia-api.ts` + `/api/backend-proxy/orchestrator/process` |
| 5.4 | Context switching | Mudar de contexto sem perder estado | ✅ MVP | `useContextSwitching.ts` (312 linhas) |

### Hook useContextSwitching (MVP)

**Funcionalidades implementadas:**
- Três contextos: 'general', 'wizard', 'fast_track'
- Detecção automática de intenção via padrões regex
- Persistência de snapshots no localStorage (24h)
- Sincronização bidirecional com wizardMode
- Restauração de estado do wizard (stage, campos, competências)
- Scroll automático no chat geral

**Limitações conhecidas (refinamentos futuros):**
- Transições fast_track podem não persistir wizard state se não salvas explicitamente
- Histórico de mensagens não é incluído no snapshot (gerenciado externamente)
- Alguns side effects podem ser pulados para evitar loops infinitos

### Detalhes da Implementação

**Hook `useWizardOrchestrator`** (254 linhas):

```typescript
interface OrchestratorResult {
  action: WizardOrchestratorAction  // 'navigate' | 'update_field' | 'ask_question' | etc.
  response: string
  fieldUpdates?: OrchestratorFieldUpdates
  targetStage?: WizardStage
  confidence: number
  reasoning?: string
  suggestions?: Array<{ field: string; value: any; reason: string }>
}
```

**Mapeamento Backend → Frontend:**
- `salary_min` → `salaryInfo.minSalary`
- `technical_skills` → `technicalSkills`
- `seniority_level` → `detectedCriteria.senioridadeIdiomas`
- (36 campos mapeados)

### 5.3 Integração Super Chat ✅ CONCLUÍDA

| # | Tarefa | Descrição | Status |
|---|--------|-----------|--------|
| 5.3.1 | orchestratorProcess no modo general | Chat fora do wizard usa `/orchestrator/process` | ✅ |
| 5.3.2 | Integração useConversationMemory | initConversation, addMessage, getContext | ✅ |
| 5.3.3 | Context injection | conversation_context passado ao orquestrador | ✅ |

### 5.4 Context Switching ✅ CONCLUÍDA

| # | Tarefa | Descrição | Status |
|---|--------|-----------|--------|
| 5.4.1 | onGeneralRestore callback | Restaura conversationId e mensagens | ✅ |
| 5.4.2 | Snapshot persistence | localStorage com expiração 24h | ✅ |
| 5.4.3 | Sync bidirecional | syncContext com skipCallbacks para evitar loops | ✅ |

---

## FASE 6: Integração com Tool Calling ✅ CONCLUÍDA

### Objetivo
Permitir que comandos no wizard executem as 59 tools existentes do sistema.

### Itens Implementados

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 6.1 | Backend: Endpoint de execução | POST `/orchestrator/execute-tool` | ✅ | `orchestrator_routes.py` |
| 6.2 | Backend: Mapeamento intents → tools | Regex patterns para PT-BR | ✅ | `wizard_orchestrator_service.py` |
| 6.3 | Frontend: Hook useToolCalling | Gerencia lifecycle de tools | ✅ | `hooks/useToolCalling.ts` |
| 6.4 | Frontend: Componentes de UI | ToolConfirmationMessage, ToolExecutionFeedback | ✅ | `components/` |
| 6.5 | Integração no modal | Tool calling no expanded-chat-modal | ✅ | `expanded-chat-modal.tsx` |

### Intent-to-Tool Mappings

| Intent (PT-BR) | Tool | Confirmação |
|----------------|------|-------------|
| "publica a vaga" | publish_job | ✅ Sim |
| "pause a vaga" | pause_job | ✅ Sim |
| "encerra a vaga" | close_job | ✅ Sim |
| "salva como rascunho" | update_job | ❌ Não |
| "valida os campos" | validate_job_fields | ❌ Não |

### Fluxo de Execução
1. Usuário digita comando em linguagem natural
2. Backend detecta intent via regex patterns
3. Orquestrador retorna `suggested_tool_call`
4. Frontend exibe `ToolConfirmationMessage` se requires_confirmation
5. Usuário confirma → Hook executa via API
6. Frontend exibe `ToolExecutionFeedback` com resultado

---

## FASE 7: Memória Conversacional ✅ CONCLUÍDA

### Objetivo
Manter contexto entre sessões e usar histórico para sugestões.

### Itens Implementados

| # | Tarefa | Descrição | Status | Localização |
|---|--------|-----------|--------|-------------|
| 7.1 | Backend: Endpoints REST | CRUD de conversas + mensagens | ✅ | `api/v1/conversations.py` |
| 7.2 | Backend: Injeção de contexto | Max 4000 tokens (~16000 chars) | ✅ | `wizard_orchestrator_service.py` |
| 7.3 | Frontend: Hook useConversationMemory | Persistência localStorage | ✅ | `hooks/useConversationMemory.ts` |
| 7.4 | Frontend: Integração no wizard | Auto-save de mensagens | ✅ | `expanded-chat-modal.tsx` |
| 7.5 | Migração de banco | Colunas session_id, context_type, etc. | ✅ | PostgreSQL |
| 7.6 | Proxies Next.js | 6 rotas de conversations | ✅ | `app/api/backend-proxy/conversations/` |

### Funcionalidades
- **Auto-summary**: Gera resumo a cada 10 mensagens via LLM
- **Context injection**: Injetado no system prompt do orquestrador
- **Persistência**: localStorage por contexto (key: `lia_conversation_${type}_${id}`)
- **Cross-session**: Recupera conversa ativa ao reabrir wizard

### Formato de Contexto Injetado
```
## Contexto da Conversa
Resumo: {summary ou "Início da conversa"}
Últimas mensagens:
- [user]: {mensagem}
- [assistant]: {resposta}

## Preferências do Usuário
{preferences se disponível}
```

**Serviço backend:** `conversation_memory.py` (~853 linhas)

---

## FASE 8: Fast Track ✅ CONCLUÍDA

### Objetivo
Reutilizar vagas anteriores para acelerar criação (80% de economia de tempo).

### Itens Implementados

| # | Tarefa | Descrição | Status |
|---|--------|-----------|--------|
| 8.1 | Detecção de similaridade | Busca semântica por título (>70% match) | ✅ |
| 8.2 | Sugestões conversacionais | LIA mostra opções no chat | ✅ |
| 8.3 | Cópia completa | Copia todos os campos da vaga anterior | ✅ |
| 8.4 | Campos sensíveis | Pergunta gestor, localização, afirmativa | ✅ |
| 8.5 | Regeneração WSI | Detecta mudanças e oferece regenerar | ✅ |
| 8.6 | Analytics | 4 eventos de tracking | ✅ |
| 8.7 | Learning Loop | Success weights por outcome | ✅ |

**Documento detalhado:** `plano_implementacao_wizard.md` (PLANO_FAST_TRACK_WIZARD.md)

---

## FASE 9: UX e Qualidade ✅ CONCLUÍDA

### Objetivo
Testes E2E, acessibilidade WCAG, e polish visual para produção.

### 9.1 Testes E2E - Tool Calling ✅

**Arquivo:** `plataforma-lia/e2e/tests/chat/tool-calling.spec.ts`

| Teste | Descrição |
|-------|-----------|
| Confirmação de ação crítica | Verifica ToolConfirmationMessage ao solicitar publicação |
| Cancelamento de execução | Valida fluxo de cancelamento via botão |
| Execução sem confirmação | Tools não críticas executam diretamente |
| Estado de execução | Indicador "executing" durante processamento |
| Confirmação via texto | Aceita "sim" no chat como confirmação |

### 9.2 Testes E2E - Conversation Memory ✅

**Arquivo:** `plataforma-lia/e2e/tests/chat/conversation-memory.spec.ts`

| Teste | Descrição |
|-------|-----------|
| Persistência entre recarregamentos | Mensagens visíveis após reload |
| Geração de resumo | Summary após 10+ mensagens |
| Restauração de contexto | Context restore ao reabrir wizard |
| Histórico visível | Mensagens anteriores no chat |
| Continuidade contextual | LIA lembra conversa anterior |

### 9.3 Acessibilidade WCAG ✅

| Elemento | Implementação |
|----------|---------------|
| Aria-labels | Botões fullscreen, input, enviar, confirmar/cancelar |
| Keyboard navigation | Enter enviar, ESC fechar, Tab navegação |
| Focus management | Auto-focus input, aria-modal="true" |
| Screen readers | role="dialog", aria-live="polite", role="status" |
| sr-only hints | Descrições ocultas para navegação |

### 9.4 Polish Visual ✅

| Feature | Implementação |
|---------|---------------|
| Typing indicator | "LIA está digitando..." com animação dots bounce |
| Transitions | animate-in fade-in-0, slide-in-from-bottom, duration-300 |
| Backdrop click | Fecha modal ao clicar fora (modo não-inline) |
| Focus ring | Visível em elementos focáveis |

---

## Resumo de Pendências

### Prioridade Alta
**Todas as fases core estão concluídas!** 🎉

### Prioridade Média

| Fase | Item | Descrição | Estimativa |
|------|------|-----------|------------|
| 8 | Templates | Expandir de 172 para 480+ templates | 15-20 dias |

### Prioridade Baixa

| Fase | Item | Descrição | Estimativa |
|------|------|-----------|------------|
| 4 | 4.4 | Animações de sincronização completas | 2h |
| - | Testes | Executar Playwright em CI | 1 dia |

---

## Arquivos Principais

### Backend (lia-agent-system)
| Arquivo | Descrição |
|---------|-----------|
| `app/services/job_embedding_service.py` | Embeddings e busca semântica |
| `app/api/v1/job_embeddings.py` | Endpoints Fast Track |
| `app/api/v1/wsi_questions.py` | Regeneração WSI |
| `app/services/wizard_orchestrator_service.py` | Orquestrador unificado |
| `app/services/tool_registry.py` | 23 tools registradas |

### Frontend (plataforma-lia)
| Arquivo | Descrição | Linhas |
|---------|-----------|--------|
| `src/components/expanded-chat-modal.tsx` | Modal do wizard | ~9800 |
| `src/components/expanded-chat/hooks/useWizardNavigation.ts` | Navegação via chat | 258 |
| `src/components/expanded-chat/hooks/useWSIQualityGates.ts` | Quality gates | 170 |
| `src/components/expanded-chat/hooks/useChatSync.ts` | Sincronização | 336 |
| `src/components/expanded-chat/hooks/useWizardOrchestrator.ts` | Orquestrador | 254 |
| `src/components/expanded-chat/hooks/useToolCalling.ts` | Tool calling lifecycle | ~250 |
| `src/components/expanded-chat/hooks/useConversationMemory.ts` | Memória conversacional | ~300 |
| `src/components/expanded-chat/components/tool-confirmation-message.tsx` | UI confirmação de tool | ~150 |
| `src/components/expanded-chat/components/tool-execution-feedback.tsx` | UI resultado de tool | ~120 |
| `src/hooks/useFastTrack.ts` | Fast Track | ~400 |
| `src/services/lia-api.ts` | Funções de API | ~4500 |

---

## Histórico de Versões

| Data | Versão | Atualização |
|------|--------|-------------|
| 2026-02-01 | 1.0 | Criação do plano inicial |
| 2026-02-01 | 2.0 | Fase 1 concluída (Smart Start) |
| 2026-02-01 | 3.0 | Fast Track concluído (Fase 8) |
| 2026-02-01 | 4.0 | Atualização completa: Fases 2-4 descobertas como concluídas; status real de hooks e componentes; pendências priorizadas |
| 2026-02-01 | 5.0 | Fases 6 e 7 concluídas: Tool Calling e Memória Conversacional |
| 2026-02-01 | **6.0** | **TODAS AS FASES CORE CONCLUÍDAS:** Fase 5 completa (Super Chat + Context Switching), Fase 9 completa (Testes E2E, WCAG, Polish). Smart Wizard 100% funcional! |
