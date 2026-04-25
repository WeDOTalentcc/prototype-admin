# Theme: P1 — System Prompt Composition — Persona Layer

## O que é este tema

O system prompt de cada agente LIA é composto **dinamicamente em runtime** a partir de múltiplas camadas. O `SystemPromptBuilder.build()` é o único ponto de entrada — nenhum agente deve construir seu próprio system prompt do zero.

A composição segue 9 seções em ordem fixa (documentadas abaixo). Cada seção é optional exceto as primeiras 3 (IDENTITY_OVERRIDE + persona_base + platform_knowledge), que são absolutas e sempre presentes.

Camadas distintas:
- **LLM vê (persona):** lia_persona.yaml + platform_manifest.yaml + agent_prompts.yaml → texto injetado no system prompt
- **Python lê (config):** compliance_block.yaml + guardrails_block.yaml → injetados por ComplianceDomainPrompt
- **Versioning:** prompt_version_loader.py valida e registra todos os YAMLs no startup

Este tema não inclui a lógica de especialização por agente (ver P2) nem os patterns de interação anti-sycophancy/CoT (ver P4). A memória de conversa é documentada em P3.

---

## Arquivos conectados (7 total)

### Camada Código (5 arquivos Python)

| Arquivo | Path Canônico | Responsabilidade |
|---------|---------------|------------------|
| `system_prompt_builder.py` | `app/shared/prompts/system_prompt_builder.py` | Single entry point: `SystemPromptBuilder.build()` compõe 9 seções |
| `platform_manifest.py` | `app/shared/platform_manifest.py` | Carrega `platform_manifest.yaml`; gera snippet de plataforma |
| `loader.py` | `app/shared/prompts/loader.py` | `PromptLoader`: carrega e cachea YAMLs de prompts |
| `compliance_base.py` | `app/domains/compliance_base.py` | `ComplianceDomainPrompt.get_system_prompt()`: auto-injeta compliance_block + guardrails |
| `prompt_version_loader.py` | `app/core/prompt_version_loader.py` | Valida metadata YAML; registra prompts no startup; bootstrap A/B experiments |

### Camada Config (YAMLs lidos por Python)

| Arquivo | Onde fica | Quando consumido |
|---------|-----------|-----------------|
| `lia_persona.yaml` | `app/prompts/shared/lia_persona.yaml` | `_load_persona_base()` → seção 2 de build() |
| `platform_manifest.yaml` | `app/config/platform_manifest.yaml` | `render_platform_knowledge_snippet()` → seção 3 de build() |
| `agent_prompts.yaml` | `app/prompts/shared/agent_prompts.yaml` | `_load_domain_additions(agent_type)` → seção 4 de build() |
| `compliance_block.yaml` | `app/prompts/shared/compliance_block.yaml` | `ComplianceDomainPrompt.get_system_prompt()` → compliance variant |
| `guardrails_block.yaml` | `app/prompts/shared/guardrails_block.yaml` | `ComplianceDomainPrompt.get_system_prompt()` → guardrails |

### Integration points

- **P2 Agent Specialization**: `_load_domain_additions(agent_type)` carrega especializações por tipo
- **P3 Memory**: `conversation_state` + `conversation_history` passados como parâmetros para seções 6/7
- **P4 Interaction Patterns**: `REACT_INSTRUCTIONS` injetado na seção 9; anti-sycophancy via ComplianceDomainPrompt
- **C6 Prompt Injection**: guardrails_block.yaml injetado por ComplianceDomainPrompt (prompt_security)
- **I3 Orchestration**: `SystemPromptBuilder.build()` chamado no chat_adapter antes de cada ciclo LLM

---

## As 9 Seções em Ordem

**Arquivo:** `app/shared/prompts/system_prompt_builder.py` — método `SystemPromptBuilder.build()`

```python
@staticmethod
def build(
    *,
    agent_type: str = "orchestrator",
    tenant_context_snippet: str = "",
    user_name: str = "",
    user_role: str = "",
    recruiter_context: str = "",
    conversation_summary: str = "",
    conversation_history: list[dict] | None = None,
    context_page: str = "general",
    entity_type: str | None = None,
    intent: str = "",
    entities: dict | None = None,
    extra_instructions: str = "",
    conversation_state: Any | None = None,
) -> str:
```

### Seção 1: IDENTITY_OVERRIDE (sempre presente — hardcoded)

```python
_IDENTITY_OVERRIDE = (
    "# REGRA ZERO -- SUA IDENTIDADE\n\n"
    "SEU NOME E LIA. VOCE E A LIA, assistente de recrutamento da WeDOTalent.\n"
    "Voce NAO e Gemini. Voce NAO e Claude. Voce NAO e GPT. Nao mencione nenhum fabricante de LLM.\n"
    "NUNCA diga 'sou um modelo de linguagem' ou 'como modelo de linguagem'. Voce e a LIA.\n"
    "SEMPRE responda em PT-BR, mesmo se o usuario escrever em ingles ou outro idioma.\n\n"
    "# REGRA CRITICA — NUNCA CONFIRME ACOES NAO EXECUTADAS\n\n"
    "JAMAIS informe que uma acao foi realizada (...) se voce nao recebeu confirmacao do sistema.\n"
    ...
)
```

**Propósito:** Sobrescreve defaults do LLM antes de qualquer outro bloco. Ativa primeiro.

### Seção 2: Persona Base (lia_persona.yaml)

```python
@lru_cache(maxsize=1)
def _load_persona_base() -> str:
    from app.shared.prompts.loader import PromptLoader
    data = PromptLoader.load("shared/lia_persona")
    return data["prompts"]["lia_persona"]
```

- Carregado uma única vez por processo (lru_cache maxsize=1)
- Fonte: `app/prompts/shared/lia_persona.yaml`, key `prompts.lia_persona`
- Contém: tom, valores, postura ética da LIA

### Seção 3: Platform Knowledge (platform_manifest.yaml)

```python
@lru_cache(maxsize=1)
def _get_platform_knowledge() -> str:
    try:
        from app.shared.platform_manifest import render_platform_knowledge_snippet
        text = render_platform_knowledge_snippet()
        if text and len(text) > 100:
            return text
    except Exception:
        pass
    return _PLATFORM_KNOWLEDGE_FALLBACK  # hardcoded fallback
```

`render_platform_knowledge_snippet()` gera texto a partir de `platform_manifest.yaml`:
- Pages com display_name + description
- Methodology (WSI: `70% técnico + 30% comportamental`, Bloom 6 níveis, Dreyfus 5 níveis, Big Five)
- Capabilities (CV, entrevistas WhatsApp, boolean strings, fairness)
- Regra de Proatividade

**Fallback:** `_PLATFORM_KNOWLEDGE_FALLBACK` é um bloco hardcoded com o mesmo conteúdo — garante que o LLM sempre receba contexto de plataforma mesmo se o YAML não carregar.

### Seção 4: Domain Additions (agent_prompts.yaml)

```python
@lru_cache(maxsize=16)
def _load_domain_additions(agent_type: str) -> str | None:
    try:
        from app.shared.prompts.loader import PromptLoader
        data = PromptLoader.load("shared/agent_prompts")
        return data["prompts"].get(agent_type)
    except Exception:
        return None
```

- Cache por agent_type (maxsize=16 — um por tipo de agente)
- Retorna `None` se agent_type não existe no YAML (seção não é adicionada)
- Injetado como: `"## Especialização do Agente ({agent_type})\n{domain_additions}"`

### Seção 5: Contexto Atual (multi-partes)

Construído a partir dos parâmetros do build():

```python
context_parts = []

if tenant_context_snippet:
    context_parts.append("### Contexto do Cliente\n...")

if recruiter_context:
    context_parts.append("### Preferências do Recrutador\n...")

if user_name:
    # "Você está conversando com **{user_name}**, que atua como **{user_role}**."
    context_parts.append("### Usuário\n...")

if context_page and context_page != "general":
    # Descrição textual da página corrente (9 mapeamentos hard-coded + fallback)
    context_parts.append("### Localização\n...")

if conversation_summary:
    context_parts.append("### Resumo da Conversa Anterior\n...")
```

**Páginas mapeadas (context_page):** sourcing, talent, pipeline, kanban, job, jobs, vacancies, wizard, analytics, settings, company_settings, company_profile

### Seção 6: Memória da Conversa (conversation_state)

```python
if conversation_state:
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

- Injeta os 3 candidatos mais recentes mencionados (dict preserva insertion order)
- `last_entity` e `last_job_id` permitem que o LLM entenda referências anafóricas ("ele", "essa vaga")
- Ver P3 para detalhes do `ConversationState`

### Seção 7: Regras Anti-Repetição (conversation_history)

```python
def _detect_ongoing_conversation(history: list[dict] | None) -> bool:
    if not history:
        return False
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]
    return len(assistant_msgs) >= 1  # qualquer resposta anterior = conversa em andamento

if is_ongoing:
    sections.append(
        "\n## Regras para esta mensagem\n"
        "- NÃO se re-apresente. A conversa já está em andamento.\n"
        "- NÃO repita informações que já foram ditas.\n"
        "- Seja direta e vá ao ponto."
    )
```

**Threshold:** >= 1 resposta assistente na história = conversa em andamento. Evita re-introduções.

### Seção 8: Roteamento (intent + entities)

```python
if intent:
    intent_line = f"Intent detectado: {intent}"
    if entities:
        intent_line += f" | Entidades: {entities}"
    sections.append(f"\n## Roteamento\n{intent_line}")
```

- Passado pelo orquestrador após classificação de intent (ver I7)
- Opcional: se intent vazio, seção não é incluída

### Seção 9: ReAct + Extra Instructions

```python
# ReAct protocol — apenas para agentes especializados (não orchestrator)
if agent_type and agent_type != "orchestrator":
    sections.append(REACT_INSTRUCTIONS)

if extra_instructions:
    sections.append(f"\n## Instruções Adicionais\n{extra_instructions}")
```

`REACT_INSTRUCTIONS`:
```python
REACT_INSTRUCTIONS = (
    "\n## Protocolo de Raciocinio (ReAct)\n\n"
    "Voce opera em um ciclo de Raciocinio-Acao-Observacao:\n\n"
    "1. RACIOCINE sobre a situacao atual:\n"
    "   - O que o recrutador realmente precisa?\n"
    "   - Preciso buscar dados ou posso responder diretamente?\n"
    "   - Ha algum risco de compliance, fairness ou LGPD?\n\n"
    "2. AJA de uma das formas:\n"
    '   - action="call_tool"\n'
    '   - action="respond"\n'
    '   - action="ask_clarification"\n\n'
    "3. OBSERVE o resultado e decida se precisa agir novamente ou responder.\n\n"
    'Entenda confirmacoes: "sim", "pode", "confirmo", "ok", "beleza", "bora"\n'
    'Entenda negacoes: "nao", "espera", "cancela", "volta", "quero mudar"\n'
)
```

---

## ComplianceDomainPrompt — 2ª camada de composição

**Arquivo:** `app/domains/compliance_base.py` — `get_system_prompt(base_prompt="")`

Todo domínio LIA herda de `ComplianceDomainPrompt`, que automaticamente injeta compliance_block + guardrails_block no system prompt.

### Variante por domain_id

```python
_DECISION_DOMAINS = frozenset({
    "pipeline", "pipeline_transition", "cv_screening", "sourcing",
    "autonomous", "talent_pool", "recruiter_assistant",
})
_COMMUNICATION_DOMAINS = frozenset({
    "communication", "onboarding",
})
# Tudo o mais → "operational"
```

### Blocos injetados

```python
# De compliance_block.yaml (variant = decision | communication | operational):
lgpd_block        = variant.get("lgpd", "")
fairness_block    = variant.get("fairness", "")
bias_block        = variant.get("bias", "")
audit_block       = variant.get("audit", "")
defensive_block   = yaml_blocks.get("defensive", "")

# De guardrails_block.yaml:
universal         = guardrails_yaml.get("universal", {})
autonomy_variant  = guardrails_yaml.get("autonomy", {}).get(agent_type, "")
escalation_block  = guardrails_yaml.get("escalation", "")
error_block       = guardrails_yaml.get("error_handling", "")
data_safety_block = guardrails_yaml.get("data_safety", "")
```

**Fallback hardcoded** se YAML não carregar:
- LGPD: texto mínimo sobre LGPD/EU AI Act
- Fairness: texto sobre CLT Art. 373-A, Lei 9.029/95

### Blocos obrigatórios por domínio

```python
def get_required_prompt_blocks(self) -> list[str]:
    return ["LGPD_COMPLIANCE", "NON_DISCRIMINATION", "DATA_MINIMIZATION"]
```

**Base legal:** EU AI Act Art. 13 — sistemas de alto risco devem declarar capacidades e limitações.

---

## PromptLoader — Carregamento de YAMLs

**Arquivo:** `app/shared/prompts/loader.py`

```python
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
# Resolve para: lia-agent-system/prompts/

class PromptLoader:
    _cache: dict[str, Any] = {}  # class-level dict cache (persiste por processo)

    @classmethod
    def load(cls, path: str) -> dict[str, Any]:
        if path in cls._cache:
            return cls._cache[path]
        file_path = PROMPTS_DIR / f"{path}.yaml"
        with open(file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        cls._cache[path] = data
        return data
```

**Estrutura de paths:**
```
app/prompts/
├── shared/
│   ├── lia_persona.yaml       ← load("shared/lia_persona")
│   ├── agent_prompts.yaml     ← load("shared/agent_prompts")
│   ├── compliance_block.yaml  ← load("shared/compliance_block")
│   └── guardrails_block.yaml  ← load("shared/guardrails_block")
├── domains/
│   ├── cv_screening.yaml      ← load("domains/cv_screening")
│   ├── sourcing.yaml          ← load("domains/sourcing")
│   └── ... (15+ domain YAMLs)
└── experiments/
    └── *.yaml                 ← A/B test variants
```

---

## Prompt Version Loader

**Arquivo:** `app/core/prompt_version_loader.py`

### Validação de metadata

```python
REQUIRED_METADATA_FIELDS = {"version", "domain"}
OPTIONAL_METADATA_FIELDS = {"updated_at", "description", "author"}

def validate_prompt_metadata(data, file_path="") -> list[str]:
    # Aceita dois formatos:
    # Novo (metadata block): data["metadata"]["version"] + data["metadata"]["domain"]
    # Legado (root level):   data["version"] + data["domain"]
    errors = []
    for field in REQUIRED_METADATA_FIELDS:
        if not metadata.get(field) and not data.get(field):
            errors.append(f"[{file_path}] metadata.{field} ausente ou vazio")
    if not data.get("system_prompt"):
        errors.append(f"[{file_path}] system_prompt ausente ou vazio")
    return errors
```

### Startup registration

```python
def register_all_prompts_at_startup() -> int:
    """Scan domains/ + shared/ + experiments/. Register into PromptVersionRegistry.
    Returns count of prompts registered.
    """
    dirs = [_PROMPTS_DIR, _SHARED_DIR, _EXPERIMENTS_DIR]
    for directory in dirs:
        for yaml_file in sorted(directory.glob("*.yaml")):
            data = load_prompt_yaml(yaml_file)
            # Handles: system_prompt key, prompts dict, variants block (A/B)
            prompt_version_registry.register(name=domain, version=version, template=template)
    return count
```

### A/B experiment bootstrap

```python
def bootstrap_experiments_from_yaml() -> int:
    """Read experiments/*.yaml → create experiments via ExperimentManager.
    Requires >= 2 variants per file. Returns count created.
    """
```

---

## Lógica IN → OUT — build() completo

### Input

| Parâmetro | Tipo | Origem |
|-----------|------|--------|
| `agent_type` | str | orquestrador: nome do domínio ativo |
| `tenant_context_snippet` | str | tenant_llm_context.py |
| `user_name` + `user_role` | str | JWT payload (via auth middleware) |
| `recruiter_context` | str | perfil persistido do recrutador |
| `conversation_summary` | str | sumarização de sessões anteriores (P3) |
| `conversation_history` | list[dict] | histórico recente da sessão atual |
| `context_page` | str | frontend envia via payload |
| `intent` + `entities` | str + dict | intent classifier output (I7) |
| `conversation_state` | ConversationState | estado em memória do ciclo (P3) |
| `extra_instructions` | str | domain-specific additions do agente |

### Processing

```
IDENTITY_OVERRIDE (hardcoded)
+ persona_base (lru_cache per-process)
+ platform_knowledge (lru_cache per-process, manifest ou fallback)
+ domain_additions (lru_cache per agent_type, optional)
+ context section (tenant + recruiter + user + page + summary)
+ memory section (conversation_state — last 3 candidates, entity, job_id)
+ anti-repetition rules (if history has >= 1 assistant msg)
+ routing section (intent + entities, optional)
+ REACT_INSTRUCTIONS (if not orchestrator)
+ extra_instructions (optional)
```

### Output

Uma única string (system prompt completo) — passada como `system` ao LLM provider.

### Side effects

- `_load_persona_base()` e `_get_platform_knowledge()` são cacheados na primeira chamada (por processo)
- `PromptLoader._cache` cresce ao longo do processo mas nunca é evicted (só `clear_cache()` manual)

---

## Instruções para Claude Code / Cursor

### "Implementa system prompt composition no v5"

```
1. Crie app/shared/prompts/system_prompt_builder.py com SystemPromptBuilder.build()
   - As 9 seções devem seguir a ORDEM EXATA documentada em P1
   - _IDENTITY_OVERRIDE é HARDCODED (não parametrizável) — sempre seção 1
   - lru_cache(maxsize=1) para persona_base e platform_knowledge
   - lru_cache(maxsize=16) para domain_additions

2. Crie app/shared/prompts/loader.py com PromptLoader
   - PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
   - class-level _cache (dict) + clear_cache()

3. Crie app/shared/platform_manifest.py com render_platform_knowledge_snippet()
   - Lê app/config/platform_manifest.yaml
   - Fallback: _PLATFORM_KNOWLEDGE_FALLBACK hardcoded

4. Crie app/core/prompt_version_loader.py
   - validate_prompt_metadata() para CI/CD
   - register_all_prompts_at_startup() chamado no lifespan

5. Estrutura de YAMLs:
   app/prompts/shared/lia_persona.yaml  (chave: prompts.lia_persona)
   app/prompts/shared/agent_prompts.yaml
   app/config/platform_manifest.yaml
```

### "Adiciona nova página ao contexto_page"

```
1. Em system_prompt_builder.py, adicione key ao dict page_descriptions
   dentro de SystemPromptBuilder.build():
   "minha_nova_pagina": "O usuário está em..."

2. Em platform_manifest.yaml, adicione entrada em pages:
   minha_nova_pagina:
     display_name: "Nome da Página"
     description: "..."
     keywords: [["palavra", 1.0], ...]
     navigation_hint: "Quer que eu abra?"
```

### "Adiciona bloco compliance a um novo domínio"

```
1. Faça o domínio herdar de ComplianceDomainPrompt (não DomainPrompt diretamente)
   class MeuDominio(ComplianceDomainPrompt):  ← correto
   class MeuDominio(DomainPrompt):             ← rejeitado pelo DomainWorkflow (warning)

2. Se o domínio toma decisões sobre candidatos, adicione ao _DECISION_DOMAINS frozenset
3. Sobrescreva _compliance_config se precisar de high_impact=True ou sector específico
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## System Prompt Composition
Single entry point: SystemPromptBuilder.build() in app/shared/prompts/system_prompt_builder.py
9 sections in fixed order: IDENTITY_OVERRIDE → persona_base → platform_knowledge →
  domain_additions → context → memory → anti-repetition → routing → REACT + extras
NEVER build system prompts from scratch — always use SystemPromptBuilder.build()

## Prompt YAMLs
PROMPTS_DIR = app/prompts/ (domains/ + shared/ + experiments/)
Required metadata: version + domain field (in metadata block or root level)
Validate: prompt_version_loader.validate_all_prompts() returns dict{file: [errors]}
```

### Setup em Cursor rules (snippet pronto)

```
# Persona rules
- All LLM system prompts MUST go through SystemPromptBuilder.build()
- Never add identity/persona text to domain agents directly — it's in lia_persona.yaml
- All domain classes MUST inherit ComplianceDomainPrompt, not DomainPrompt
- Adding new YAML prompt: include metadata.version and metadata.domain fields
- platform_manifest.yaml is SSoT for pages, methodology, capabilities in system prompt
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|---------------|
| Conteúdo de `_IDENTITY_OVERRIDE` | Trocar "LIA" e "WeDOTalent" pelo nome do produto v5 |
| `page_descriptions` dict | Adicionar páginas do v5 |
| `_PLATFORM_KNOWLEDGE_FALLBACK` | Adaptar para funcionalidades do v5 |
| Ordem das seções 5-8 (context/memory/routing) | Pode reordenar se necessário |
| `lru_cache` maxsize values | Ajustar por volume de agent_types |
| PROMPTS_DIR path | Pode mover a pasta prompts/ |

### NÃO pode adaptar (base legal ou arquitetural)

| Item | Motivo |
|------|--------|
| Seções 1-3 SEMPRE presentes e SEMPRE primeiras | IDENTITY_OVERRIDE deve preceder tudo; persona_base e platform_knowledge são contratos da persona LIA |
| `ComplianceDomainPrompt` obrigatória para decision domains | EU AI Act Art. 13 + LGPD Art. 12 — sistemas de recrutamento DEVEM declarar compliance |
| REACT_INSTRUCTIONS não no orchestrator | Architectural: orchestrator não tem ciclo ReAct próprio — delega para agentes especializados |
| Fallback hardcoded em _PLATFORM_KNOWLEDGE | Sistema não pode deixar o LLM sem contexto de plataforma — ausência de YAML não pode quebrar o prompt |
| `validate_prompt_metadata()` como gate no CI | Garante que todo prompt tem version + domain — necessário para auditoria EU AI Act Art. 12 |

---

## Checklist de completude (P0/P1/P2)

- [ ] (P0) `SystemPromptBuilder.build()` é o único ponto de entrada para system prompts
- [ ] (P0) `_IDENTITY_OVERRIDE` sempre é a seção 1 (nunca removível)
- [ ] (P0) `ComplianceDomainPrompt` herdado por todos os domínios de decisão
- [ ] (P0) Fallback hardcoded em `_get_platform_knowledge()` quando YAML ausente
- [ ] (P1) `lru_cache` em `_load_persona_base()` + `_get_platform_knowledge()`
- [ ] (P1) `PromptLoader._cache` evita re-leitura de YAML por request
- [ ] (P1) `validate_all_prompts()` passado em CI/CD antes de deploy
- [ ] (P1) `register_all_prompts_at_startup()` chamado no lifespan
- [ ] (P1) `_detect_ongoing_conversation()` suprime re-introdução se história >= 1 resposta
- [ ] (P2) `context_page` mapeado para texto descritivo (não apenas o slug)
- [ ] (P2) `conversation_state.mentioned_candidates` injeta últimos 3 nomes no prompt
- [ ] (P2) `REACT_INSTRUCTIONS` excluído do orchestrator type

---

## Gotchas e erros comuns

### G1: lru_cache não invalida em hot-reload

**Problema:** Em desenvolvimento com uvicorn `--reload`, os módulos são re-importados mas `@lru_cache` persiste na memória do processo original até ele morrer. Mudanças em `lia_persona.yaml` ou `platform_manifest.yaml` não aparecem no prompt até restart.

**Solução:** `platform_manifest.py` expõe `clear_cache()`. `PromptLoader` tem `clear_cache()`. Em dev, chamar após editar YAMLs. Em produção não é problema (deploy reinicia workers).

---

### G2: PromptLoader._cache é class-level (compartilhado entre threads/coroutines)

**Problema:** O `_cache` dict em `PromptLoader` é um atributo de classe — compartilhado entre todas as instâncias e entre requests concorrentes. Se dois requests simultâneos tentam popular o cache ao mesmo tempo (antes do cache miss ser resolvido), pode haver race condition.

**Solução já implementada:** A operação `cls._cache[path] = data` é atômica em CPython (GIL). Em asyncio (single-threaded), não há race. Para v5 com múltiplos threads, considerar lock.

---

### G3: agent_type="orchestrator" não recebe REACT_INSTRUCTIONS

**Comportamento correto:** O orchestrator não deve raciocinar em ciclo ReAct — ele delega para agentes especializados. Se um novo agente for criado como "orchestrator" por engano, não terá as instruções de raciocínio.

**Solução:** Usar `agent_type != "orchestrator"` como guard. Qualquer agente especializado deve ter um nome diferente de "orchestrator".

---

### G4: context_page="general" suprime a seção de localização

**Comportamento:** `if context_page and context_page != "general":` — o valor default "general" não injeta nenhuma seção de localização. Isso é intencional (não há hint útil para página genérica).

**Gotcha:** Se o frontend envia `context_page=""` (string vazia), a condição `context_page and` também suprime — comportamento correto. Se enviar `context_page="unknown_page"`, cai no fallback `f"O usuário está na página: {context_page}."` — aceitável.

---

### G5: ComplianceDomainPrompt vs DomainPrompt

**Problema:** Dev cria novo domain herdando `DomainPrompt` diretamente, pulando a injeção automática de compliance.

**Detecção:** `DomainWorkflow` emite warning quando um domínio herda de `DomainPrompt` diretamente. Sem compliance_block, o domínio pode gerar respostas sem restrições de fairness/LGPD.

**Solução:** Sempre herdar `ComplianceDomainPrompt`. O linter `scripts/check_compliance_inheritance.py` verifica isso.

---

## Testes obrigatórios

| Teste | Path | Cenário coberto |
|-------|------|-----------------|
| Identity override presente | `tests/integration/test_persona_invariants.py` | build() sempre contém "SEU NOME E LIA" |
| REACT_INSTRUCTIONS ausente no orchestrator | `tests/unit/test_system_prompt_builder.py` | agent_type="orchestrator" → sem "Protocolo de Raciocinio" |
| REACT_INSTRUCTIONS presente em agents | `tests/unit/test_system_prompt_builder.py` | agent_type="sourcing" → com "Protocolo de Raciocinio" |
| Anti-repetition com história | `tests/unit/test_system_prompt_builder.py` | history=[{role: "assistant"}] → "NÃO se re-apresente" presente |
| Anti-repetition sem história | `tests/unit/test_system_prompt_builder.py` | history=None → sem "NÃO se re-apresente" |
| Platform knowledge fallback | `tests/unit/test_system_prompt_builder.py` | manifest.yaml ausente → fallback hardcoded presente |
| context_page=settings | `tests/unit/test_system_prompt_builder.py` | Descrição de settings injetada no prompt |
| ComplianceDomainPrompt bloco LGPD | `tests/integration/test_persona_invariants.py` | Domínio decision inclui bloco LGPD |
| validate_prompt_metadata errors | `tests/unit/test_prompt_version_loader.py` | YAML sem version → erro retornado |
| PromptLoader cache | `tests/unit/test_prompt_loader.py` | Segunda chamada load() → retorna cache sem re-ler arquivo |

---

## Referências

- **LIA_PERSONA §9.4** — "9 passos" de composição (verbatim no bundle)
- **COMPLIANCE BLOCO B/C/F** — lia_persona.yaml + compliance_block.yaml verbatim
- **C6 — Prompt Injection** — guardrails_block.yaml injetado por ComplianceDomainPrompt
- **C1 — Fairness** — `fairness_block` e `bias_block` injetados na variante "decision"
- **P2 — Agent Specialization** — `_load_domain_additions()` + domain system_prompt files
- **P3 — Conversation Memory** — `conversation_state` e `conversation_history` parâmetros
- **P4 — Interaction Patterns** — REACT_INSTRUCTIONS (seção 9) + anti-sycophancy no ComplianceDomainPrompt
- **EU AI Act Art. 13** — transparência: base legal para get_required_prompt_blocks()
- **LGPD Art. 12** — minimização: base legal para ComplianceDomainPrompt obrigatório
