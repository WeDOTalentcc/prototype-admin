# Theme: P3 — Conversation Memory / Context State — Persona Layer

## O que é este tema

A memória conversacional do LIA é dividida em **4 camadas** por durabilidade e escopo:

| Camada | Duração | Escopo | Armazenamento |
|--------|---------|--------|---------------|
| `ConversationState` | Sessão (30min TTL) | Per-session | In-memory LRU |
| `MemoryResolver` | Sessão (até clear) | Per-session/orchestrator | In-memory dict |
| `WorkingMemory` | Cross-restart | Per-session + domain | PostgreSQL |
| `LongTermMemory` | Permanente (expires_at) | Per-company + domain | PostgreSQL |

A escolha de camada depende do que precisa sobreviver:
- **ConversationState**: candidatos mostrados, filtros ativos, última entidade — volátil, não persiste entre restarts
- **MemoryResolver**: action_history + intent_history — para o orchestrator rastrear o que fez na sessão
- **WorkingMemory**: campos coletados, plano atual, ações pendentes — para agentes wizard/pipeline que têm múltiplos turnos
- **LongTermMemory**: padrões aprendidos, preferências de recrutador, outcomes — cresce com o uso

Este tema não inclui a memória conversacional do banco de dados `conversation_messages` (ver I9), nem o RAG sobre histórico (ver I11).

---

## Arquivos conectados (7 total)

### Camada Código (7 arquivos Python)

| Arquivo | Path Canônico | Responsabilidade |
|---------|---------------|------------------|
| `conversation_state.py` | `app/shared/memory/conversation_state.py` | ConversationState dataclass + ConversationStateStore LRU |
| `memory_resolver.py` | `app/shared/memory_resolver.py` | MemoryResolver: action/intent history + entity cache |
| `working_memory.py` | `libs/agents-core/lia_agents_core/working_memory.py` | WorkingMemoryService: PostgreSQL-backed agent state |
| `long_term_memory.py` | `libs/agents-core/lia_agents_core/long_term_memory.py` | LongTermMemoryService: company-scoped persistent memory |
| `checkpointer.py` | `libs/agents-core/lia_agents_core/checkpointer.py` | LangGraph checkpointer customizado — persiste estado do grafo entre invocações |
| `memory_integration.py` | `libs/agents-core/lia_agents_core/memory_integration.py` | Integração Working+LongTerm memory com o ReAct loop — injeta memória nos nós LangGraph |
| `system_prompt_builder.py` | `app/shared/prompts/system_prompt_builder.py` | Consome ConversationState → seções 6+7 do system prompt |

### Integration points

- **P1 System Prompt Composition**: `conversation_state` + `conversation_history` são parâmetros de `SystemPromptBuilder.build()` → injetados nas seções 6 e 7
- **I3 Orchestration**: `MemoryResolver.add_action()` chamado após cada tool call no orchestrator; `ConversationStateStore.get/set()` no state_manager
- **I9 Data Layer**: `AgentWorkingMemory` e `AgentLongTermMemory` são SQLAlchemy models em `libs/models/` com `company_id` para RLS
- **C5 Multi-tenancy**: `MemoryResolver._sessions` particionado por `company_id`; `WorkingMemory.get_or_create()` filtra por `company_id`

---

## Camada 1: ConversationState (in-memory, hot path)

**Arquivo:** `app/shared/memory/conversation_state.py`

### Dataclass fields

```python
@dataclass
class ConversationState:
    # Multi-tenancy — sempre presente
    company_id: str | None = None

    # Candidates tracking
    last_candidates_shown: list[int] = field(default_factory=list)   # max 20
    last_candidate_detailed: int | None = None
    detailed_history: list[int] = field(default_factory=list)        # max 10
    shortlist: list[int] = field(default_factory=list)               # max 50
    mentioned_candidates: dict[str, int] = field(default_factory=dict)  # name → id

    # Context
    active_filters: dict[str, Any] = field(default_factory=dict)
    last_search_term: str | None = None
    last_action: str | None = None
    last_job_id: int | None = None
    last_domain_id: str | None = None
    last_results_count: int | None = None

    # Phase 2 — MemoryResolver expansion
    last_entity: dict[str, Any] | None = None   # {type, id, name} — pronome resolution
    pagination_cursor: int = 0                   # offset para "mostra mais"
```

**Limits:**
```python
MAX_CANDIDATES_SHOWN = 20    # last_candidates_shown truncado
MAX_DETAILED_HISTORY = 10    # detailed_history FIFO
MAX_SHORTLIST = 50           # shortlist cap
```

### update_after_action() — auto-update a partir de tool response

```python
def update_after_action(self, action_id: str, domain_id: str, response_data: Any) -> None:
    """Atualiza o estado automaticamente com base na resposta da ação.
    
    Detecta automaticamente: candidates list, candidate detail, job_id, 
    filters, search_term.
    """
    self.last_action = action_id
    self.last_domain_id = domain_id
    
    # Extrai candidate IDs de candidates ou candidate_ids
    candidates = response_data.get("candidates") or response_data.get("candidate_ids")
    if isinstance(candidates, list):
        for c in candidates:
            if isinstance(c, dict) and "id" in c:
                candidate_ids.append(c["id"])
                if c.get("name"):
                    self.update_mentioned(c["name"], c["id"])  # name → id
        self.update_candidates_shown(candidate_ids)
    
    # Atualiza last_entity para resolução de pronomes
    candidate = response_data.get("candidate") or response_data.get("candidate_detail")
    if isinstance(candidate, dict) and "id" in candidate:
        self.update_candidate_detailed(candidate["id"])
        self.update_last_entity("candidate", candidate["id"], name)
    
    # Outros campos: job_id, filters, search_term
```

### Pronome resolution via last_entity

```python
def update_last_entity(self, entity_type: str, entity_id: Any, name: str = "") -> None:
    """Registra a última entidade mencionada para resolução de pronomes."""
    self.last_entity = {"type": entity_type, "id": entity_id, "name": name}
```

O `last_entity` é injetado no system prompt (P1, seção 6) para que o LLM possa resolver referências como "ele", "esse candidato", "essa vaga" sem fazer tool calls extras.

### Paginação

```python
def advance_pagination(self, page_size: int = 10) -> int:
    """Avança cursor. Retorna novo offset."""
    self.pagination_cursor += page_size
    return self.pagination_cursor

def reset_pagination(self) -> None:
    """Reset em nova busca."""
    self.pagination_cursor = 0
```

### clear() — preserva company_id

```python
def clear(self) -> None:
    _company_id = self.company_id   # Preserva tenant context
    # ... reset all fields ...
    self.company_id = _company_id   # Restaura tenant context
```

### ConversationStateStore — LRU com TTL

```python
_DEFAULT_TTL_SECONDS = 1800   # env: CONVERSATION_STATE_TTL_SECONDS
_DEFAULT_MAX_SIZE = 1000      # env: CONVERSATION_STATE_MAX_SIZE

class ConversationStateStore:
    def __init__(self):
        self._entries: OrderedDict[str, tuple[ConversationState, float]] = OrderedDict()
        self._op_count: int = 0
        self._cleanup_interval: int = 100   # purge expired a cada 100 ops
    
    def get(self, conversation_id: str) -> ConversationState | None:
        # Move to end on hit (LRU)
        # Returns None if expired (evicts entry)
    
    def set(self, conversation_id: str, state: ConversationState) -> None:
        # Move to end + evict oldest if over max_size
    
    def _purge_expired(self) -> None:
        # Lazy cleanup — só roda a cada 100 ops
```

**Eviction policy:** TTL-based + LRU capacity. Quando > max_size, remove o mais antigo (OrderedDict FIFO). Lazy cleanup a cada 100 operações.

**Singleton:** `conversation_state_store = ConversationStateStore()`

---

## Camada 2: MemoryResolver (in-memory, orchestrator)

**Arquivo:** `app/shared/memory_resolver.py`

### ActionRecord

```python
@dataclass
class ActionRecord:
    domain: str
    action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
```

### MemoryResolver — 4 estruturas internas

```python
class MemoryResolver:
    def __init__(self, session_id: str, user_id: str = "", company_id: str = ""):
        self._action_history: list[ActionRecord] = []   # max 20 (FIFO)
        self._intent_history: list[str] = []             # max 10 (FIFO)
        self._entity_cache: dict[str, Any] = {}          # {type → {id, metadata, cached_at}}
        self._user_preferences: dict[str, Any] = {}      # persistem na sessão
        self.company_id = company_id  # multi-tenancy tag
```

**Limits:**
```python
_MAX_ACTION_HISTORY = 20
_MAX_INTENT_HISTORY = 10
```

### API pública

```python
# Action history
add_action(domain, action, metadata, success) → ActionRecord
get_recent_actions(limit=5) → list[dict]
get_actions_for_domain(domain, limit=5) → list[dict]
get_last_action() → dict | None

# Intent history
add_intent(intent) → None
get_intent_history(limit=5) → list[str]
get_last_intent() → str | None

# Entity cache
set_entity(entity_type, entity_id, metadata) → None
get_entity(entity_type) → dict | None
get_entity_id(entity_type) → str | None

# Preferences
set_preference(key, value) → None
get_preference(key, default=None) → Any

# Context snapshot
get_context() → dict[str, Any]  # full snapshot: actions + intents + entities + prefs

# LGPD Art. 15 — right to erasure
clear() → None
```

### Storage — particionado por company_id

```python
# Module-level, in-memory
_sessions: dict[str, dict[str, MemoryResolver]] = {}
# Estrutura: {company_id: {session_id: MemoryResolver}}

def get_or_create_resolver(session_id, user_id="", company_id="") -> MemoryResolver:
    """Cria ou reutiliza resolver, particionado por company_id."""
    if company_id not in _sessions:
        _sessions[company_id] = {}
    if session_id not in _sessions[company_id]:
        _sessions[company_id][session_id] = MemoryResolver(...)
    return _sessions[company_id][session_id]

def clear_session(session_id, company_id="") -> bool:
    """Remove memória da sessão — LGPD Art. 15."""
```

**Nota:** `_sessions` não tem TTL próprio — é in-memory per-process. Reinício do worker limpa tudo. Para persistência entre restarts, usar WorkingMemory.

---

## Camada 3: WorkingMemory (PostgreSQL, per-session + domain)

**Arquivo:** `libs/agents-core/lia_agents_core/working_memory.py`

### AgentWorkingMemory SQLAlchemy model

```python
class AgentWorkingMemory(Base):
    __tablename__ = "agent_working_memory"
    
    # Identificação
    id = Column(UUID, primary_key=True)
    session_id = Column(String(255), index=True)
    domain = Column(String(100))        # "wizard", "pipeline", "cv_screening"
    company_id = Column(String(255))    # Multi-tenancy
    user_id = Column(String(255))
    
    # State JSON fields
    collected_fields: dict       # Campos coletados até agora (wizard: titulo, salario, etc.)
    current_plan: list           # Plano de ações a executar
    pending_actions: list        # Ações aguardando confirmação do usuário
    adjustment_history: list     # Histórico de ajustes/correções
    parecer_data: dict           # Dados de parecer do candidato
    accepted_suggestions: list   # Sugestões aceitas pelo recrutador
    rejected_suggestions: list   # Sugestões recusadas pelo recrutador
    agent_notes: str | None      # Notas livres do agente
    iteration_count: int         # Quantos turnos de raciocínio já ocorreram
    last_intent: str | None      # Último intent classificado
    last_confidence: float | None # Confiança do último intent
```

### WorkingMemoryService.get_or_create()

```python
async def get_or_create(
    self,
    session_id: str,
    domain: str,
    company_id: str,   # Multi-tenancy: isolamento por tenant
    user_id: str,
) -> AgentWorkingMemory:
    """Busca ou cria working memory para a sessão + domínio.
    
    Query: WHERE session_id=? AND domain=? AND company_id=?
    """
```

**Uso típico:** Agente wizard usa `collected_fields` para acumular campos da vaga entre turnos. Após criar a vaga, `pending_actions` é esvaziado, `current_plan` zerado.

---

## Camada 4: LongTermMemory (PostgreSQL, per-company + domain)

**Arquivo:** `libs/agents-core/lia_agents_core/long_term_memory.py`

### AgentLongTermMemory model

```python
class AgentLongTermMemory(Base):
    __tablename__ = "agent_long_term_memory"
    
    company_id = Column(String(255), index=True)   # Multi-tenancy
    domain = Column(String(100))
    memory_type = Column(String(50))               # pattern|preference|learning|outcome
    memory_key = Column(String(255))
    memory_value = Column(JSON)
    context_tags = Column(JSON)                    # list[str] para busca
    usage_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=1.0)  # cresce com uso (max 1.0)
    source_session_id = Column(String(255))
    expires_at = Column(DateTime, nullable=True)   # TTL opcional
```

### 4 memory_types válidos

```python
VALID_MEMORY_TYPES = {"pattern", "preference", "learning", "outcome"}
# pattern:    padrão identificado no recrutamento da empresa
# preference: preferência explícita do recrutador
# learning:   algo aprendido de iterações anteriores
# outcome:    resultado de uma decisão de recrutamento
```

### Upsert com relevance_score

```python
async def store(self, company_id, domain, memory_type, key, value, tags, session_id):
    # Tenta encontrar key existente para company_id + domain
    if existing:
        existing.memory_value = value
        existing.relevance_score = min(existing.relevance_score + 0.1, 1.0)  # incrementa
        # ...
    else:
        # Cria novo registro
```

**Relevance decay:** Não implementado em código — `relevance_score` só cresce (cap 1.0). Para decay por tempo, usar `expires_at`.

---

## Fluxo completo de memória por turno

```
[User Message]
    │
    ▼
[1] Orchestrator recebe o message
    │   MemoryResolver.add_intent(detected_intent)
    │   state = ConversationStateStore.get(conversation_id)
    ▼
[2] SystemPromptBuilder.build(conversation_state=state, conversation_history=msgs)
    │   → Seção 6: injeta last_entity + mentioned_candidates + last_job_id
    │   → Seção 7: _detect_ongoing_conversation() → regras anti-repetição
    ▼
[3] LLM gera resposta / tool calls
    ▼
[4] Tool call executada (ex: search_candidates)
    │   MemoryResolver.add_action(domain="sourcing", action="search_candidates", metadata={...})
    ▼
[5] Action response processada
    │   state.update_after_action(action_id, domain_id, response_data)
    │   ConversationStateStore.set(conversation_id, state)
    ▼
[6] Para agentes com WorkingMemory (wizard, cv_screening):
    │   wm = WorkingMemoryService.get_or_create(session_id, domain, company_id, user_id)
    │   wm.collected_fields.update({...})
    │   wm.iteration_count += 1
    ▼
[User Response Sent]
```

---

## Como o system prompt consome o estado

O `SystemPromptBuilder.build()` recebe `conversation_state: ConversationState` e injeta (seção 6):

```python
mem_lines = []
if conversation_state.last_entity:
    e = conversation_state.last_entity
    mem_lines.append(f"- Última entidade: {e['type']} **{e['name']}** (ID: {e['id']})")
if conversation_state.mentioned_candidates:
    recent = list(conversation_state.mentioned_candidates.items())[-3:]
    names = ", ".join(f"{n} (ID: {cid})" for n, cid in recent)
    mem_lines.append(f"- Candidatos mencionados: {names}")
if conversation_state.last_job_id:
    mem_lines.append(f"- Última vaga: ID {conversation_state.last_job_id}")
```

Injeta apenas os últimos 3 candidatos `mentioned_candidates` (dict preserva insertion order) para evitar contexto excessivo.

---

## Instruções para Claude Code / Cursor

### "Implementa conversation memory no v5"

```
1. Crie app/shared/memory/conversation_state.py
   - ConversationState dataclass com company_id obrigatório
   - ConversationStateStore com OrderedDict LRU + TTL
   - TTL default: 1800s (env: CONVERSATION_STATE_TTL_SECONDS)
   - Max size: 1000 (env: CONVERSATION_STATE_MAX_SIZE)
   - clear() DEVE preservar company_id

2. Crie app/shared/memory_resolver.py
   - MemoryResolver com action_history (max 20) + intent_history (max 10)
   - _sessions particionado por company_id (não global flat dict)
   - clear() com log LGPD Art. 15

3. Crie migration para agent_working_memory e agent_long_term_memory
   - Ambas DEVEM ter company_id NOT NULL + index
   - long_term_memory precisa de expires_at para TTL

4. Em SystemPromptBuilder.build():
   - Passe conversation_state como parâmetro
   - Injete last_entity + mentioned_candidates[-3:] + last_job_id
```

### "Adiciona campo ao ConversationState"

```
1. Adicione field em ConversationState dataclass
2. Atualize to_dict() + from_dict() para serialização
3. Atualize update_after_action() se o novo campo deve ser auto-populado
4. Atualize clear() para resetar o campo (exceto se for invariante de tenant)
5. Atualize SystemPromptBuilder.build() se o campo deve ser injetado no prompt
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Conversation Memory (4 layers)
1. ConversationState (in-memory LRU, TTL=1800s) → candidatos, filtros, última entidade
2. MemoryResolver (in-memory, por sessão) → action history + intent history
3. WorkingMemory (PostgreSQL, per session+domain) → collected_fields, pending_actions
4. LongTermMemory (PostgreSQL, per company+domain) → patterns, preferences, outcomes

ConversationState.clear() PRESERVA company_id — nunca perde o tenant context
_sessions in MemoryResolver é particionado por company_id (não flat dict)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|---------------|
| TTL da ConversationStateStore (1800s) | Ajustar via CONVERSATION_STATE_TTL_SECONDS |
| Max size (1000 sessions) | Ajustar via CONVERSATION_STATE_MAX_SIZE |
| MAX_CANDIDATES_SHOWN (20) | Ajustar para UI do v5 |
| MAX_SHORTLIST (50) | Ajustar para contexto do v5 |
| LongTermMemory memory_types | Adicionar novos tipos se necessário |
| relevance_score increment (0.1) | Ajustar por volume de dados |

### NÃO pode adaptar (base legal ou arquitetural)

| Item | Motivo |
|------|--------|
| `company_id` em todos os stores e models | Multi-tenancy: RLS enforcement (I9). Sem isso, memória vaza entre tenants |
| `ConversationState.clear()` preserva company_id | Limpar estado não deve perder o contexto de tenant |
| `MemoryResolver.clear()` com log LGPD Art. 15 | Direito ao esquecimento: auditável |
| `_sessions` particionado por company_id | Cross-tenant contamination se usar flat dict |
| `AgentWorkingMemory` filtrado por company_id no get_or_create | Sem isso, sessão de tenant A pode ler state de tenant B |
| `LongTermMemory.VALID_MEMORY_TYPES` validado | Evita tipos arbitrários que podem conter dados sensíveis sem categorização |

---

## Checklist de completude (P0/P1/P2)

### ConversationState

- [ ] (P0) `company_id` presente e não resetado em `clear()`
- [ ] (P0) `update_after_action()` atualiza automaticamente menioned_candidates e last_entity
- [ ] (P1) LRU eviction quando > max_size
- [ ] (P1) TTL-based eviction em `get()`
- [ ] (P1) Lazy cleanup a cada 100 ops (não a cada request)
- [ ] (P2) `pagination_cursor` resetado em nova busca

### MemoryResolver

- [ ] (P0) `_sessions` particionado por `company_id` (não flat `{session_id: resolver}`)
- [ ] (P0) `clear()` loga como LGPD Art. 15
- [ ] (P1) action_history FIFO (max 20)
- [ ] (P1) intent_history FIFO (max 10)
- [ ] (P2) `get_context()` snapshot completo para orchestrator

### WorkingMemory

- [ ] (P0) `get_or_create()` filtra por company_id (multi-tenancy)
- [ ] (P1) `collected_fields` JSON permite schema aberto por domínio
- [ ] (P2) `iteration_count` para detectar loops de raciocínio

### LongTermMemory

- [ ] (P0) `company_id` NOT NULL + index na tabela
- [ ] (P1) `memory_type` validado contra VALID_MEMORY_TYPES
- [ ] (P1) Upsert: se key existe, incrementa relevance_score (não duplica)
- [ ] (P2) `expires_at` suportado para TTL-based expiration

---

## Gotchas e erros comuns

### G1: ConversationState vazando entre sessões

**Problema:** Dev usa um `ConversationState` singleton global em vez de buscar do store por `conversation_id`. Múltiplos usuários ou sessões compartilham o mesmo estado.

**Solução:** Sempre `state = conversation_state_store.get(conversation_id)` antes de usar. Nunca criar `ConversationState()` inline nos handlers.

---

### G2: MemoryResolver._sessions não particionado por company_id

**Problema:** Dev cria `_sessions: dict[str, MemoryResolver]` flat. Se dois tenants têm a mesma session_id (UUID collision improvável mas possível), um leria o resolver do outro.

**Solução:** Sempre `_sessions[company_id][session_id]`. O código correto já faz isso — não simplificar.

---

### G3: WorkingMemory.get_or_create sem company_id

**Problema:** Chamada como `get_or_create(session_id, domain, company_id="")`. Company_id vazio faz o filtro SQL match qualquer registro com `company_id=""`, potencialmente retornando state de outro tenant.

**Solução:** Sempre passar `company_id` do JWT. Se não disponível, falhar explicitamente em vez de usar string vazia.

---

### G4: ConversationState.mentioned_candidates cresce indefinidamente

**Problema:** `mentioned_candidates` é um `dict[str, int]` sem limite. Em sessões longas, acumula todos os candidatos mencionados.

**Mitigação:** O `SystemPromptBuilder` injeta apenas os **últimos 3** (`list(...items())[-3:]`). O dict pode crescer mas o impacto no prompt é controlado.

**Para v5:** Considerar adicionar `MAX_MENTIONED_CANDIDATES = 100` com eviction FIFO.

---

### G5: WorkingMemory não limpo após conclusão do agente

**Problema:** Agente wizard conclui a criação de vaga mas `collected_fields` permanece no banco. Próxima sessão do mesmo usuário/domain pode carregar campos da vaga anterior.

**Solução:** Após conclusão, o agente deve chamar `update` para zerar `collected_fields`, `pending_actions`, `current_plan`. Ou criar nova entry com `session_id` diferente.

---

## Testes obrigatórios

| Teste | Path | Cenário coberto |
|-------|------|-----------------|
| ConversationState clear preserva company_id | `tests/unit/test_conversation_state.py` | Após clear(), company_id = mesmo valor |
| LRU eviction | `tests/unit/test_conversation_state_store.py` | max_size=2, terceira entry evita oldest |
| TTL expiration | `tests/unit/test_conversation_state_store.py` | State após TTL → None |
| update_after_action candidatos | `tests/unit/test_conversation_state.py` | Response com candidates → mentioned_candidates populado |
| update_after_action last_entity | `tests/unit/test_conversation_state.py` | Candidate detail → last_entity = {type, id, name} |
| MemoryResolver company_id partitioning | `tests/unit/test_memory_resolver.py` | Dois tenants, mesmo session_id → resolvers diferentes |
| MemoryResolver action FIFO | `tests/unit/test_memory_resolver.py` | 21 actions → history tem 20 mais recentes |
| MemoryResolver clear LGPD | `tests/unit/test_memory_resolver.py` | clear() → action_history vazia |
| WorkingMemory multi-tenant | `tests/integration/test_working_memory.py` | company_id A não lê working memory de B |
| LongTermMemory upsert relevance | `tests/integration/test_long_term_memory.py` | Segunda store com mesma key → relevance_score += 0.1 |
| LongTermMemory invalid memory_type | `tests/unit/test_long_term_memory.py` | memory_type="invalid" → ValueError |

---

## Referências

- **P1 — System Prompt Composition** — `conversation_state` + `conversation_history` são parâmetros de `SystemPromptBuilder.build()`; seções 6 e 7
- **I3 — Orchestration** — `MemoryResolver.add_action()` chamado após cada tool call; `ConversationStateStore` usado pelo state_manager
- **I9 — Data Layer** — `AgentWorkingMemory` + `AgentLongTermMemory` SQLAlchemy models; `company_id` para RLS
- **C5 — Multi-tenancy** — `company_id` presente em todas as camadas de memória
- **LGPD Art. 15** — direito de exclusão de dados: base legal para `MemoryResolver.clear()` com log
- **LIA_PERSONA §9.4 passo 5** — "contexto de conversa" (verbatim no bundle)
