# Plano de Implementação: Ciclo Fechado de Execução da LIA

**Data:** 21/02/2026  
**Versão:** 1.0  
**Objetivo:** Transformar a LIA de uma assistente que sugere ações (ciclo aberto) para uma que executa ações reais (ciclo fechado), como ChatGPT, Manus AI e Claude.

---

## 1. Diagnóstico da Arquitetura Atual

### 1.1 Como funciona ChatGPT / Manus AI / Claude (Ciclo Fechado)

```
Usuário escreve → LLM entende → LLM chama ferramenta (tool) →
Ferramenta executa ação real → Resultado volta para LLM →
LLM responde com o resultado
```

O ponto-chave: **a IA decide E executa**. Quando você pede "busque informações sobre X", ela chama uma tool de busca, recebe o resultado, e te mostra. Manus AI executa código, navega sites, cria arquivos — tudo no mesmo ciclo.

### 1.2 Como funciona a LIA hoje (Ciclo Aberto)

```
Usuário escreve → LLM classifica intent → Backend retorna ui_action →
Frontend ABRE UM MODAL → Usuário preenche manualmente →
Usuário clica botão → Aí sim executa
```

**Problema fundamental:** A LIA entende o que o usuário quer, mas ao invés de executar, abre uma janela para o usuário executar manualmente.

### 1.3 O que temos vs o que falta

| Camada | Status | Detalhe |
|--------|--------|---------|
| Classificação de intent (LLM) | ✅ Funciona | IntentRouter com Claude classifica corretamente |
| Roteamento para domínios | ✅ Funciona | CascadedRouter: memory → FastRouter → IntentRouter |
| Domínios especializados | ✅ Existe | 9 domínios com `execute_action()` implementado |
| ToolRegistry + ToolExecutor | ✅ Existe | Validação, timeout, segurança, tenant isolation |
| Tools reais (send_email, move_candidate) | ✅ Código existe | Mas muitos retornam mock quando DB falha |
| `generate_with_tools()` (tool calling nativo) | ✅ Existe | Claude + Gemini suportados, mas NÃO conectado ao fluxo |
| **Banco de dados provisionado** | ❌ FALTA | PostgreSQL não ativo — operações DB falham |
| **Modelo Claude com nome correto** | ❌ ERRADO | Usa `claude-sonnet-4-5` (não existe), correto: `claude-sonnet-4-6` |
| **API keys de email** | ❌ FALTA | Mailgun/Resend sem API keys nos secrets |
| **Conexão LLM → Tool Execution** | ❌ FALTA | Orquestrador não conecta intent a execução real |
| **Ciclo fechado (execute → retorne resultado)** | ❌ FALTA | Endpoint retorna ui_action ao invés de executar |
| **Conversa multi-turno com clarificação** | ❌ FALTA | Não pede parâmetros faltantes antes de executar |
| **Confirmação antes de ação destrutiva** | ❌ FALTA | Não pede "confirma?" antes de mover/enviar |

---

## 2. Arquitetura Alvo (Ciclo Fechado)

### 2.1 Fluxo Principal

```
Usuário: "Mover João para Entrevista"
    ↓
IntentRouter (Claude) classifica:
    intent: "mover_candidato"
    entities: { candidate_name: "João", target_stage: "Entrevista" }
    confidence: 0.95
    ↓
ActionExecutorService verifica:
    - Intent é acionável? SIM (está no ACTIONABLE_INTENTS)
    - Tem todos os parâmetros? candidate_name ✅, target_stage ✅
    - Resolve candidate_name → candidate_id via DB/contexto
    - Ação requer confirmação? SIM (risco médio)
    ↓
LIA responde: "Vou mover João Silva para a etapa Entrevista. Confirma?"
    ↓
Usuário: "sim"
    ↓
PendingActionState detecta confirmação:
    - Executa move_candidate via PipelineDomain.execute_action()
    - Resultado real do banco de dados
    ↓
LIA responde: "✅ João Silva foi movido para Entrevista com sucesso."
Frontend: Atualiza kanban automaticamente (sem reload)
```

### 2.2 Fluxo com Parâmetros Faltantes (Multi-turno)

```
Usuário: "Enviar email para a Maria"
    ↓
ActionExecutorService verifica:
    - Intent: "enviar_email" → acionável
    - candidate_name: "Maria" ✅
    - subject: ❌ FALTA
    - body: ❌ FALTA
    ↓
Salva PendingActionState:
    { action: "send_email", collected: { candidate_name: "Maria" }, missing: ["subject", "body"] }
    ↓
LIA responde: "Claro! Qual o assunto do email para a Maria?"
    ↓
Usuário: "Convite para entrevista"
    ↓
PendingAction atualiza: subject = "Convite para entrevista"
LIA: "E qual mensagem você quer enviar?"
    ↓
Usuário: "Parabéns, você foi selecionada para entrevista técnica dia 25/02"
    ↓
PendingAction completa: body preenchido
ActionExecutor: Todos parâmetros presentes → pedir confirmação
    ↓
LIA: "Vou enviar o email para Maria Santos (maria@email.com):
  Assunto: Convite para entrevista
  Mensagem: Parabéns, você foi selecionada...
  Confirma o envio?"
    ↓
Usuário: "sim"
    ↓
CommunicationDomain.execute_action("send_email", params) → Provider real (Mailgun/Resend)
    ↓
LIA: "✅ Email enviado para Maria Santos com sucesso!"
```

### 2.3 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                       │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Chat UI  │  │ActionResult  │  │ Kanban (auto-update)  │ │
│  │          │  │   Card       │  │                       │ │
│  └────┬─────┘  └──────────────┘  └───────────────────────┘ │
│       │                                                     │
└───────┼─────────────────────────────────────────────────────┘
        │ POST /api/v1/orchestrator/job-chat
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ENDPOINT (FastAPI)                        │
│                                                             │
│  orchestrated_job_chat.py                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │ 1. Check PendingActionState (multi-turno)    │           │
│  │ 2. Se não pendente → Orchestrator.process()  │           │
│  │ 3. ActionExecutorService.try_execute()       │           │
│  │ 4. Retorna resultado ou pergunta             │           │
│  └──────────────────────────────────────────────┘           │
│                                                             │
└───────┼─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                              │
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐ │
│  │ Cascaded    │──▶│ Intent       │──▶│ Domain           │ │
│  │ Router      │   │ Router (LLM) │   │ Workflow         │ │
│  │ (fast→LLM)  │   │              │   │ (analyze→exec)   │ │
│  └─────────────┘   └──────────────┘   └──────────────────┘ │
│                                                             │
└───────┼─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│               ACTION EXECUTOR SERVICE (NOVO)                │
│                                                             │
│  ┌──────────────────────────────────────────────┐           │
│  │ ACTIONABLE_INTENTS = {                       │           │
│  │   "mover_candidato": {                       │           │
│  │     domain: "pipeline",                      │           │
│  │     action: "move_candidate",                │           │
│  │     required: ["candidate_id","target_stage"],│          │
│  │     risk: "medium",                          │           │
│  │     confirm: True                            │           │
│  │   },                                         │           │
│  │   "enviar_email": { ... },                   │           │
│  │   "agendar_entrevista": { ... },             │           │
│  │ }                                            │           │
│  │                                              │           │
│  │ try_execute(intent, entities, context):       │           │
│  │   1. É acionável?                            │           │
│  │   2. Tem todos parâmetros?                   │           │
│  │   3. Se falta → retorna pergunta             │           │
│  │   4. Se requer confirmação → retorna resumo  │           │
│  │   5. Se tudo ok → executa via Domain         │           │
│  └──────────────────────────────────────────────┘           │
│                                                             │
└───────┼─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOMAINS (Execução Real)                  │
│                                                             │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────────┐ │
│  │ Pipeline │  │Communication  │  │ Scheduling           │ │
│  │ Domain   │  │ Domain        │  │ Domain               │ │
│  │          │  │               │  │                      │ │
│  │move_cand │  │ send_email    │  │ schedule_interview   │ │
│  │predict_  │  │ send_whatsapp │  │ reschedule           │ │
│  │substatus │  │ send_feedback │  │ cancel               │ │
│  └────┬─────┘  └──────┬────────┘  └──────────┬───────────┘ │
│       │               │                      │             │
└───────┼───────────────┼──────────────────────┼─────────────┘
        │               │                      │
        ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    INFRAESTRUTURA                           │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │PostgreSQL│  │Mailgun/     │  │ Calendar API         │  │
│  │ (Neon)   │  │Resend        │  │ (futuro)             │  │
│  │          │  │              │  │                      │  │
│  │Candidates│  │Email sending │  │ Scheduling           │  │
│  │Jobs      │  │Templates     │  │                      │  │
│  │Pipeline  │  │Tracking      │  │                      │  │
│  └──────────┘  └──────────────┘  └──────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Fases de Implementação

### FASE 0 — Infraestrutura (Pré-requisito)

Sem esta fase, NADA funciona. É a fundação.

#### F0.1 — Provisionar Banco PostgreSQL
- **O que:** Ativar banco PostgreSQL no Replit e rodar migrações
- **Por que:** Todas as operações reais (buscar candidato, mover, registrar email) precisam de banco
- **Como:** Usar ferramenta de criação de banco do Replit, verificar tabelas existentes
- **Critério de sucesso:** `SELECT * FROM candidates LIMIT 1` funciona

#### F0.2 — Corrigir Nome do Modelo Claude
- **O que:** Substituir `claude-sonnet-4-5` por `claude-sonnet-4-6` em todos os arquivos
- **Por que:** `claude-sonnet-4-5` não existe nas integrações Replit — causa erro silencioso
- **Arquivos afetados:**
  - `app/services/llm.py` (linhas 85, 98, 240)
  - `app/domains/recruiter_assistant/services/kanban_assistant_service.py`
  - Qualquer outro arquivo que referencie o modelo
- **Critério de sucesso:** Chamada à API Claude retorna resposta válida

#### F0.3 — Configurar API Keys de Email
- **O que:** Adicionar API key do Mailgun ou Resend nos secrets
- **Por que:** Sem API key, o envio de email é simulado (mock)
- **Decisão:** Mailgun (mais popular) ou Resend (mais moderno, melhor DX)
- **Critério de sucesso:** Email de teste enviado e recebido

#### F0.4 — Validar Conexão LLM
- **O que:** Testar que LLMService conecta ao Claude e retorna respostas
- **Como:** Endpoint de health check ou teste manual via API
- **Critério de sucesso:** `POST /api/v1/orchestrator/health` retorna `{ "llm": "ok", "model": "claude-sonnet-4-6" }`

---

### FASE 1 — Ciclo Fechado Básico (Move Candidate funciona via chat)

Esta fase é o MVP: um comando via chat executa uma ação real.

#### F1.1 — Criar ActionExecutorService

**Arquivo:** `app/orchestrator/action_executor.py`

```python
ACTIONABLE_INTENTS = {
    "mover_candidato": {
        "domain_id": "pipeline",
        "action_id": "move_candidate",
        "required_params": ["candidate_id", "target_stage"],
        "optional_params": ["reason", "sub_status"],
        "risk_level": "medium",  # low, medium, high
        "requires_confirmation": True,
        "clarification_prompts": {
            "candidate_id": "Qual candidato você quer mover?",
            "target_stage": "Para qual etapa?"
        }
    },
    "enviar_email": {
        "domain_id": "communication",
        "action_id": "send_email",
        "required_params": ["candidate_id", "subject", "body"],
        "optional_params": ["template_id", "cc"],
        "risk_level": "high",
        "requires_confirmation": True,
        "clarification_prompts": {
            "candidate_id": "Para qual candidato?",
            "subject": "Qual o assunto do email?",
            "body": "Qual a mensagem que quer enviar?"
        }
    },
    "agendar_entrevista": {
        "domain_id": "interview_scheduling",
        "action_id": "schedule_interview",
        "required_params": ["candidate_id", "datetime", "interviewer"],
        "risk_level": "medium",
        "requires_confirmation": True,
        ...
    },
    "disparar_triagem": {
        "domain_id": "cv_screening",
        "action_id": "start_screening",
        "required_params": ["candidate_ids"],
        "risk_level": "low",
        "requires_confirmation": False,
        ...
    },
    "analisar_perfil": {
        "domain_id": "cv_screening",
        "action_id": "analyze_profile",
        "required_params": ["candidate_id"],
        "risk_level": "low",
        "requires_confirmation": False,
        ...
    },
    "aprovar_candidato": {
        "domain_id": "pipeline",
        "action_id": "approve_candidate",
        "required_params": ["candidate_id"],
        "optional_params": ["target_stage", "reason"],
        "risk_level": "medium",
        "requires_confirmation": True,
        ...
    }
}
```

**Método principal:**
```python
async def try_execute(intent, entities, context, candidates_data) -> ActionResult:
    """
    Returns:
        ActionResult with one of:
        - status="executed" + result (ação executada com sucesso)
        - status="needs_params" + question (falta parâmetros, pergunta ao usuário)
        - status="needs_confirmation" + summary (pede confirmação)
        - status="not_actionable" (intent não é acionável, tratar normalmente)
        - status="error" + error_message
    """
```

#### F1.2 — Integrar no Endpoint

**Arquivo:** `app/api/v1/orchestrated_job_chat.py`

Lógica no endpoint:
```
1. Verificar se existe PendingActionState (Fase 2)
2. Se não → chamar Orchestrator.process_request()
3. Com o intent retornado → ActionExecutorService.try_execute()
4. Se executed → retornar resultado real + action_executed=True
5. Se needs_params → retornar pergunta + salvar PendingState
6. Se needs_confirmation → retornar resumo + salvar PendingState
7. Se not_actionable → retornar resposta normal (como hoje)
```

#### F1.3 — Campos Novos na Resposta API

Adicionar ao `OrchestratedJobChatResponse`:
```python
action_executed: bool = False          # Ação foi executada de verdade?
action_result: Optional[Dict] = None   # Resultado da execução
action_type: Optional[str] = None      # Tipo da ação executada
needs_confirmation: bool = False       # Aguardando confirmação?
needs_params: bool = False             # Aguardando parâmetros?
pending_action_id: Optional[str] = None # ID da ação pendente (para multi-turno)
```

---

### FASE 2 — Clarificação Multi-turno

Quando a LIA não tem todas as informações, ela pergunta antes de agir.

#### F2.1 — PendingActionState

**Arquivo:** `app/orchestrator/pending_action.py`

```python
@dataclass
class PendingActionState:
    action_id: str                    # "send_email"
    intent: str                       # "enviar_email"
    domain_id: str                    # "communication"
    collected_params: Dict[str, Any]  # {"candidate_id": "123"}
    missing_params: List[str]         # ["subject", "body"]
    conversation_id: str
    created_at: datetime
    expires_at: datetime              # auto-expire em 5 min
    
    @property
    def is_complete(self) -> bool:
        return len(self.missing_params) == 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def next_question(self) -> str:
        """Retorna pergunta para o próximo parâmetro faltante."""
        ...
```

**Storage:** In-memory dict com conversation_id como chave (suficiente para MVP).

#### F2.2 — Fluxo de Clarificação

No endpoint, ANTES de chamar o orquestrador:
```python
# 1. Verificar se existe ação pendente
pending = pending_action_store.get(conversation_id)

if pending and not pending.is_expired:
    # 2. Tentar extrair parâmetro da mensagem do usuário
    extracted = extract_param_from_message(message, pending.missing_params[0])
    
    if extracted:
        pending.collected_params[pending.missing_params[0]] = extracted
        pending.missing_params.pop(0)
    
    # 3. Se completo → executar ou pedir confirmação
    if pending.is_complete:
        if pending.requires_confirmation:
            return confirmation_response(pending)
        else:
            result = await executor.execute(pending)
            return executed_response(result)
    
    # 4. Se ainda falta → perguntar próximo
    return clarification_response(pending.next_question())
```

#### F2.3 — Extração Inteligente de Parâmetros

Usar Claude para extrair parâmetros de texto livre:
```python
async def extract_param_from_message(message: str, param_name: str, context: dict) -> Optional[str]:
    """
    Usa LLM para extrair parâmetro específico da mensagem.
    
    Exemplo:
        message = "Convite para entrevista técnica"
        param_name = "subject"
        → retorna "Convite para entrevista técnica"
    """
```

---

### FASE 3 — Confirmação Antes de Executar

Ações com risco médio/alto pedem confirmação explícita.

#### F3.1 — Classificação de Risco

| Ação | Risco | Confirmação |
|------|-------|-------------|
| analisar_perfil | Baixo | Não |
| disparar_triagem | Baixo | Não |
| mover_candidato | Médio | Sim |
| aprovar_candidato | Médio | Sim |
| agendar_entrevista | Médio | Sim |
| enviar_email | Alto | Sim |
| reprovar_candidato | Alto | Sim |

#### F3.2 — Detecção de Confirmação

```python
CONFIRMATION_PATTERNS = [
    "sim", "pode", "confirmo", "confirma", "ok", "vamos",
    "pode sim", "manda", "envia", "faz isso", "tá bom",
    "perfeito", "isso mesmo", "correto", "exato", "avança",
    "prossiga", "pode mandar", "manda ver", "vai lá",
    "yes", "go", "confirm", "approved"
]

REJECTION_PATTERNS = [
    "não", "cancela", "para", "espera", "mudei de ideia",
    "deixa", "esquece", "cancelar", "no", "cancel", "stop"
]
```

Verificação no início do endpoint:
```python
if pending and pending.awaiting_confirmation:
    if is_confirmation(message):
        result = await executor.execute(pending)
        return executed_response(result)
    elif is_rejection(message):
        pending_store.remove(conversation_id)
        return {"message": "Ok, ação cancelada.", "action_executed": False}
```

---

### FASE 4 — Frontend (Exibir Resultado no Chat)

#### F4.1 — ActionResultCard

Componente React para exibir no chat quando uma ação foi executada:

```tsx
// Tipos de resultado:
// ✅ Sucesso: "João Silva foi movido para Entrevista"
// ❌ Erro: "Não foi possível enviar o email (candidato sem email cadastrado)"
// ⏳ Pendente: "Aguardando confirmação..."
// ❓ Clarificação: "Para qual etapa quer mover?"

interface ActionResultMessage {
  type: 'action_result'
  action_type: 'move_candidate' | 'send_email' | 'schedule_interview' | ...
  status: 'success' | 'error' | 'pending_confirmation' | 'needs_params'
  title: string
  details: Record<string, any>
}
```

#### F4.2 — Auto-update do Kanban

Quando `action_executed: true` e `action_type: "move_candidate"`:
```typescript
// Após receber resposta com action_executed
if (response.action_executed && response.action_type === 'move_candidate') {
  // Atualizar estado local do kanban
  const { candidate_id, from_stage, to_stage } = response.action_result
  moveCandidateInState(candidate_id, from_stage, to_stage)
  // Opcionalmente: refetch completo para sincronizar
  await refetchCandidates()
}
```

#### F4.3 — Fallback para Modais

Se a execução automática falhar:
```typescript
if (response.action_executed === false && response.action_type) {
  // Oferecer fallback manual
  addChatMessage({
    type: 'assistant',
    content: `Não consegui executar automaticamente. Quer tentar manualmente?`,
    actions: [
      { label: 'Abrir modal', action: () => handleLiaUiAction(response.action_type, response.ui_action_params) }
    ]
  })
}
```

---

### FASE 5 — Ações Reais (Providers Conectados)

#### F5.1 — Email Real

Fluxo completo:
1. `send_email` tool recebe `candidate_id`, `subject`, `body`
2. Busca candidato no banco → pega email
3. Chama provider (Mailgun/Resend) com email real
4. Registra envio no banco (histórico de comunicação)
5. Retorna resultado para LIA mostrar no chat

**Arquivos:**
- `app/domains/communication/tools/communication_tools.py` — já tem `send_email()`
- `app/domains/communication/services/email_service.py` — já tem providers
- `app/services/email_providers/mailgun_provider.py` — implementação Mailgun

#### F5.2 — Agendamento Real

Para MVP: criar registro no banco com data/hora proposta.
Para versão completa: integrar com Google Calendar / Microsoft Graph.

#### F5.3 — Move Candidate Real

Já existe em `app/domains/pipeline/domain.py`:
```python
async def _handle_move_candidate(parameters, context):
    # Atualizar stage_id do candidato no banco
    # Registrar histórico de movimentação
    # Retornar resultado
```

Precisa: banco provisionado + tabelas criadas.

---

## 4. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Banco não ter dados para testar | Alta | Alto | Criar seeds com dados de teste |
| Claude API rate limit | Média | Médio | Cache de respostas + Gemini como fallback |
| Email ir para spam | Média | Alto | Configurar SPF/DKIM no domínio |
| Ação executada por engano | Baixa | Alto | Confirmação obrigatória para risco médio/alto |
| Multi-turno perder contexto | Média | Médio | PendingActionState com timeout de 5 min |
| Frontend dessincronizado | Média | Médio | Refetch após ação + otimistic update |

---

## 5. Métricas de Sucesso

Após implementação completa, validar:

1. **"Mover João para Entrevista"** → candidato realmente muda de coluna no kanban ✅
2. **"Enviar email para Maria"** → LIA pergunta assunto → mensagem → confirma → email real enviado ✅
3. **"Disparar triagem"** → screening iniciado sem precisar abrir modal ✅
4. **"Agendar entrevista com Pedro"** → LIA pergunta data/hora → confirma → agendado ✅
5. **Texto livre sem keywords específicas** → LLM entende e executa corretamente ✅
6. **"Cancelar"** no meio de um fluxo → ação cancelada, estado limpo ✅

---

## 6. Ordem de Execução

```
FASE 0 (Infraestrutura)     ← SEM ISSO NADA FUNCIONA
  ├── F0.1 Banco PostgreSQL
  ├── F0.2 Modelo Claude correto
  ├── F0.3 API keys email
  └── F0.4 Validar conexão LLM

FASE 1 (Ciclo Fechado MVP)  ← PRIMEIRO RESULTADO VISÍVEL
  ├── F1.1 ActionExecutorService
  ├── F1.2 Integrar no endpoint
  └── F1.3 Campos na resposta API

FASE 2 (Multi-turno)        ← CONVERSAÇÃO INTELIGENTE
  ├── F2.1 PendingActionState
  ├── F2.2 Fluxo clarificação
  └── F2.3 Extração de parâmetros

FASE 3 (Confirmação)        ← SEGURANÇA
  ├── F3.1 Classificação de risco
  └── F3.2 Detecção de confirmação/rejeição

FASE 4 (Frontend)           ← EXPERIÊNCIA DO USUÁRIO
  ├── F4.1 ActionResultCard
  ├── F4.2 Auto-update kanban
  └── F4.3 Fallback modais

FASE 5 (Ações Reais)        ← PRODUÇÃO
  ├── F5.1 Email real (Mailgun/Resend)
  ├── F5.2 Agendamento real
  └── F5.3 Move candidate real (DB)
```

---

## 7. Arquivos Principais Afetados

### Backend (lia-agent-system)
| Arquivo | Ação |
|---------|------|
| `app/orchestrator/action_executor.py` | **NOVO** — Serviço central de execução |
| `app/orchestrator/pending_action.py` | **NOVO** — Estado de ação pendente |
| `app/api/v1/orchestrated_job_chat.py` | **MODIFICAR** — Integrar ActionExecutor |
| `app/orchestrator/intent_router.py` | **MODIFICAR** — Adicionar intents acionáveis |
| `app/services/llm.py` | **MODIFICAR** — Corrigir modelo Claude |
| `app/domains/pipeline/domain.py` | **MODIFICAR** — Conectar ao banco real |
| `app/domains/communication/domain.py` | **MODIFICAR** — Conectar ao provider real |
| `app/domains/communication/tools/communication_tools.py` | **MODIFICAR** — Envio real |

### Frontend (plataforma-lia)
| Arquivo | Ação |
|---------|------|
| `src/components/pages/job-kanban-page.tsx` | **MODIFICAR** — Tratar action_executed |
| `src/components/chat/ActionResultCard.tsx` | **NOVO** — Card de resultado de ação |
| `src/lib/api/kanban-assistant.ts` | **MODIFICAR** — Novos campos na resposta |

---

## 8. Observações Importantes

### O que já funciona e NÃO precisa ser refeito:
- IntentRouter com Claude classifica intents corretamente
- CascadedRouter (fast → LLM) funciona
- DomainWorkflow (analyze → execute → format) está implementado
- ToolExecutor com validação, timeout e tenant isolation
- Tools de comunicação, pipeline, scheduling existem
- Frontend kanban com modais já funciona como fallback

### O que precisa de atenção especial:
- **Banco de dados**: Sem ele, tudo é mock. É o bloqueio #1.
- **Modelo Claude correto**: Erro sutil que pode causar falhas intermitentes.
- **Dados de teste**: Precisamos de candidatos, vagas e pipeline com dados reais para testar.
- **Rate limits**: Claude tem limites por minuto — implementar cache e retry.

### Filosofia conversacional:
Manter o princípio do Job Wizard: **chat é a interface principal**, painéis são suporte visual. As ações executadas via chat devem ser refletidas imediatamente nos painéis/kanban sem necessidade de reload.
