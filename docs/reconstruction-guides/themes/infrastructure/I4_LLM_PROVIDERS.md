# Theme I4 — LLM Providers (BYOK — Choose Your AI)

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/app/shared/providers/` no Replit

---

## O que é este tema

A camada **Choose Your AI** da LIA permite que cada tenant (empresa cliente) use seu próprio provedor de LLM com sua própria API key — BYOK (Bring Your Own Key). O sistema suporta Anthropic Claude, Google Gemini e OpenAI, com fallback automático e tiering de qualidade por task.

Componentes principais:
1. **LLMProviderABC** — contrato abstrato implementado por cada provider (`llm_provider.py`)
2. **LLMProviderFactory** — registro global de classes de provider (`llm_factory.py`)
3. **ProviderContainer** — container DI por tenant: primary + fallback chain + API keys
4. **TenantProviderRegistry** — singleton que mapeia `tenant_id → ProviderContainer`
5. **`get_provider_for_tenant()`** — entry point recomendado para todo acesso LLM
6. **LLMBootstrap** — monkey-patches todos os SDK constructors na startup para enforcement global (`llm_bootstrap.py`)
7. **Lint scripts** — `check_llm_factory_enforcement.py` + `check_llm_imports.py` bloqueiam acesso direto ao SDK

**Boundary com temas irmãos:**
- **I1 Agent Architecture** — `LangGraphReActBase._get_model()` chama `get_provider_for_tenant(company_id)` (BYOK)
- **I3 Orchestration** — `CascadedRouter` Tier 5 usa `get_provider_for_tenant()` para LLM Cascade
- **C5 Multi-tenancy** — BYOK garante que o LLM correto é usado para cada tenant
- **C7 Audit Trail** — `_audit_llm_usage()` registra provider, modelo e token usage

---

## Arquivos conectados (5 Python)

### Camada Persona (LLM vê — 0 YAMLs)

Nenhum YAML de provider. Config de provider por tenant vive na tabela `tenant_llm_configs` (DB) + env vars.

### Camada Código (5 arquivos Python)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `llm_provider.py` | `app/shared/providers/llm_provider.py` | 111 | `LLMProviderABC` (abstract) + `LLMResponse`, `LLMToolCall`, `LLMToolResponse` dataclasses |
| `llm_factory.py` | `app/shared/providers/llm_factory.py` | 729 | `LLMProviderFactory` + `ProviderContainer` + `TenantProviderRegistry` + `get_provider_for_tenant()` |
| `llm_bootstrap.py` | `app/shared/llm_bootstrap.py` | 290 | Monkey-patches SDK constructors globalmente. `install_llm_guards()` chamado na startup |
| `check_llm_factory_enforcement.py` | `scripts/check_llm_factory_enforcement.py` | — | AST lint — bloqueia instanciação direta de LLM clients fora do allowlist (LIA-LLM-1) |
| `check_llm_imports.py` | `scripts/check_llm_imports.py` | — | Regex lint — bloqueia imports diretos de SDK LLM fora de providers/ |

**Provider implementations (não incluídas no doc mas referenciadas):**
- `app/shared/providers/llm_claude.py` — Claude (Anthropic)
- `app/shared/providers/llm_gemini.py` — Gemini (Google)
- `app/shared/providers/llm_openai.py` — OpenAI / Azure

### Integration points

- **Agentes** (I1) chamam `get_provider_for_tenant(company_id)` em `_get_model()`
- **CascadedRouter Tier 5** (I3) chama `get_provider_for_tenant()` para LLM Cascade
- **AgenticLoop** (I3 Fase 1.5) chama `get_provider_for_tenant()` com tenant provider
- **AuditCallback** (C7) recebe `provider`, `model`, `token_usage` de cada call LLM
- **TenantBudget** (I3) consome `token_usage` para rastrear custo por tenant
- **llm_bootstrap.py** intercepta TODOS os SDK calls globalmente (incluindo imports diretos)

---

## Lógica IN → OUT

### LLMProviderABC — contrato por provider

```python
# app/shared/providers/llm_provider.py (111L)

@dataclass
class LLMResponse:
    text: str
    provider: str   # "claude" | "gemini" | "openai"
    model: str      # "claude-sonnet-4-6" | "gemini-2.5-pro" | "gpt-4o"
    usage: dict[str, int]  # {"input_tokens": N, "output_tokens": M}
    raw_response: Any | None

@dataclass
class LLMToolResponse:
    text: str | None
    tool_calls: list[LLMToolCall]
    is_tool_call: bool
    provider: str
    model: str

class LLMProviderABC(ABC):
    """Contrato que cada provider deve implementar."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str: ...          # "claude" | "gemini" | "openai"
    
    @property
    @abstractmethod
    def default_model(self) -> str: ...
    
    @abstractmethod
    async def generate(self, prompt, model, temperature, max_tokens, **kwargs) -> LLMResponse: ...
    
    @abstractmethod
    async def generate_with_system(self, system_prompt, user_message, model, ...) -> LLMResponse: ...
    
    @abstractmethod
    async def generate_with_tools(self, messages, tools, system_prompt, ...) -> LLMToolResponse: ...
    
    @abstractmethod
    async def generate_structured(self, messages, output_schema, ...) -> dict: ...
```

### LLMProviderFactory — registro global

```python
class LLMProviderFactory:
    _providers: dict[str, type] = {}    # nome → classe
    _instances: dict[str, LLMProviderABC] = {}  # singletons globais
    
    @classmethod
    def register(cls, provider_class: type):
        # Usa cls._provider_name ou cls.__name__ como chave
        name = getattr(provider_class, "_provider_name", provider_class.__name__)
        cls._providers[name] = provider_class
    
    @classmethod
    def get(cls, provider_name: str) -> LLMProviderABC:
        # Cria singleton se não existe; ValueError se provider não registrado
        if provider_name not in cls._instances:
            cls._instances[provider_name] = cls._providers[provider_name]()
        return cls._instances[provider_name]
    
    @classmethod
    def available_providers(cls) -> list: ...
    
    @classmethod
    def clear(cls): ...  # para testes
```

### ProviderContainer — DI por tenant

```python
class ProviderContainer:
    """Container de providers scoped a um tenant. Instances são isoladas por tenant."""
    
    def __init__(
        self,
        tenant_id: str | None,
        primary_provider: str | None,   # ex: "gemini" | "claude" | "openai"
        fallback_order: list[str] | None,  # ex: ["gemini", "claude", "openai"]
        provider_api_keys: dict[str, str] | None,  # BYOK: {"claude": "sk-ant-...", ...}
        provider_models: dict[str, str] | None,    # model override por provider
    )
    
    async def generate_with_fallback(
        self,
        messages: list[dict],
        task: str = "chat",             # "chat" | "screening" | "wsi"
        **kwargs
    ) -> LLMResponse:
        # 1. Resolve tier mínimo para a task (TASK_MINIMUM_TIER)
        # 2. Tenta primary_provider
        # 3. Em falha → itera fallback_order
        # 4. Cada tentativa chama _audit_llm_usage()
        # 5. check_request_budget_before_llm() antes de cada call
```

### TenantProviderRegistry — mapeamento tenant → container

```python
class TenantProviderRegistry:
    """Singleton que resolve tenant_id → ProviderContainer.
    
    _resolve_provider_config() busca em 5 níveis:
      1. In-memory cache (mais rápido — sem I/O)
      2. tenant_llm_configs DB table (configuração BYOK do tenant)
      3. Contextvar _current_tenant_llm_config (set pelo AuthEnforcementMiddleware)
      4. YAML global defaults (tool_permissions.yaml — fallback estático)
      5. Env vars (LLM_DEFAULT_PROVIDER, LLM_DEFAULT_MODEL — último recurso)
    """
    
    def get_container(
        self,
        tenant_id: str | None = None,
        primary_provider: str | None = None,  # override explícito
        fallback_order: list[str] | None = None,
    ) -> ProviderContainer: ...
    
    async def load_from_db(self, tenant_id: str) -> ProviderContainer | None:
        # Async: lê tenant_llm_configs table; retorna None se não existe
        
    def register_container(self, tenant_id: str, container: ProviderContainer): ...
    def remove_container(self, tenant_id: str) -> bool: ...
    def list_tenants(self) -> list[str]: ...
```

### Funções de módulo — entry points recomendados

```python
# Recomendado para uso SÍNCRONO (maioria dos casos — agentes, orchestrator):
def get_provider_for_tenant(
    tenant_id: str | None = None,
    primary_provider: str | None = None,
    fallback_order: list[str] | None = None,
) -> ProviderContainer:
    return TenantProviderRegistry.get_instance().get_container(...)

# Recomendado para uso ASSÍNCRONO (workers, background jobs):
async def get_provider_for_tenant_from_db(tenant_id: str) -> ProviderContainer:
    # Toca sempre o DB em cache miss; warm up via prime_tenant_llm_cache()
    ...

# Voice (WebSocket de voz):
def get_voice_provider_for_tenant(tenant_id: str) -> str:
    # Retorna "gemini_live" ou "openai_realtime" baseado no provider do tenant
```

### Quality tiering — BYOK quality guarantee

```python
# llm_factory.py — modelos pinned por tier
QUALITY_TIERS: dict[str, str] = {
    # Tier 1 — raciocínio complexo (WSI, Bloom, Dreyfus, screening crítico)
    "claude-sonnet-4-6": "tier1",
    "claude-opus-4-7":   "tier1",
    "gemini-2.5-pro":    "tier1",
    "gemini-2.5-flash":  "tier1",
    "gpt-4o":            "tier1",
    "gpt-4-turbo":       "tier1",
    # Tier 2 — velocidade/custo (chat, classificação simples)
    "claude-haiku-3-5":  "tier2",
    "gemini-2.0-flash":  "tier2",
    "gpt-4o-mini":       "tier2",
}

# Tasks com requisito mínimo de tier:
TASK_MINIMUM_TIER: dict[str, str] = {
    "screening": "tier1",   # triagem de candidatos — qualidade obrigatória
    "wsi":       "tier1",   # WSI evaluation — high stakes
    "chat":      "tier2",   # chat geral — tier 2 suficiente
}

# Fallback padrão do sistema:
FALLBACK_ORDER: list[str] = ["gemini", "claude", "openai"]
```

### LLMBootstrap — enforcement global na startup

```python
# app/shared/llm_bootstrap.py (290L)
# Monkey-patches SDK constructors para enforcement universal.
# Chamado UMA VEZ em app/main.py na startup.

def install_llm_guards():
    """
    Patches:
    - anthropic.Anthropic / AsyncAnthropic → inject API key + audit
    - anthropic.Anthropic.messages.create/stream → PII strip + audit
    - google.genai.Client → inject API key + audit
    - openai.OpenAI / AsyncOpenAI → inject API key + audit
    
    Todas as calls interceptadas:
    1. Obtêm tenant_id via contextvar (_current_company_id)
    2. Injetam API key do tenant (BYOK) ou env var default
    3. Stripped PII do prompt antes de enviar
    4. Registram caller file:line para audit trail
    """
    global _installed
    if _installed:
        return  # idempotente
    _installed = True
    # ... patches do SDK
```

### Enforcement de arquitetura — lint scripts

```python
# scripts/check_llm_factory_enforcement.py (LIA-LLM-1)
# AST-based — detecta instanciação direta de LLM clients
# Bloqueia: AsyncAnthropic(), ChatAnthropic(), ChatOpenAI(), genai.Client()
# ALLOWLIST (onde instanciação direta é permitida):
ALLOWLIST = {
    "app/shared/providers/llm_claude.py",
    "app/shared/providers/llm_gemini.py",
    "app/shared/providers/llm_openai.py",
    "app/domains/ai/services/llm.py",
    "app/shared/llm_bootstrap.py",
    "app/shared/tenant_llm_context.py",
    "app/api/v1/llm_config.py",        # admin test endpoint
    # ... + voice services
}
# Exit 0 = ok, Exit 1 = violações

# scripts/check_llm_imports.py
# Regex-based — detecta import direto de SDK
FORBIDDEN_PATTERNS = [
    r"from anthropic import",
    r"import anthropic\b",
    r"from google\.generativeai",
    r"import google\.generativeai",
    r"from openai import",
    r"import openai\b",
]
ALLOWED_PATHS = {
    "app/shared/providers",
    "app/shared/llm_bootstrap.py",
    "app/api/v1/llm_config.py",
    "app/api/v1/chat.py",
}
```

### Side effects

- **Audit log** (C7): `_audit_llm_usage()` registra `provider`, `model`, `token_usage` por call
- **TenantBudget** (I3): token usage incrementado no Redis por tenant/mês
- **PII stripping**: `llm_bootstrap._strip_pii()` chama `strip_pii_for_llm_prompt()` em todo prompt
- **Métricas** (I5): latência por provider + fallback count em Prometheus

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Provider primário indisponível | `generate_with_fallback()` tenta próximo da `fallback_order` automaticamente |
| API key BYOK inválida | Fallback para provider seguinte; log ERROR + alerta de billing |
| Task requer Tier 1 mas tenant só tem Tier 2 | Upgrade implícito: usa provider Tier 1 com key da plataforma |
| Budget 100% atingido | `check_request_budget_before_llm()` lança exceção antes da call LLM |
| Import direto de SDK detectado no lint | Exit code 1 no CI — PR bloqueado |

---

## Instruções para Claude Code / Cursor

### "Implementa LLM Providers (BYOK) no v5"

```
1. COPIE provider layer:
   cp app/shared/providers/llm_provider.py → <v5>/app/shared/providers/
   cp app/shared/providers/llm_factory.py  → <v5>/app/shared/providers/
   cp app/shared/providers/llm_claude.py   → <v5>/app/shared/providers/
   cp app/shared/providers/llm_gemini.py   → <v5>/app/shared/providers/
   cp app/shared/providers/llm_openai.py   → <v5>/app/shared/providers/
   cp app/shared/llm_bootstrap.py          → <v5>/app/shared/

2. INSTALE na startup (app/main.py):
   from app.shared.llm_bootstrap import install_llm_guards
   install_llm_guards()  # UMA VEZ antes de qualquer import de agente
   
3. CRIE migration para tenant_llm_configs:
   CREATE TABLE tenant_llm_configs (
     id UUID PRIMARY KEY,
     company_id VARCHAR UNIQUE NOT NULL,
     primary_provider VARCHAR NOT NULL DEFAULT 'gemini',
     fallback_order JSONB DEFAULT '["gemini","claude","openai"]',
     provider_api_keys JSONB,    -- ENCRYPTED em produção
     provider_models JSONB,
     created_at TIMESTAMP DEFAULT now(),
     updated_at TIMESTAMP DEFAULT now()
   );

4. CONFIGURE env vars defaults:
   LLM_DEFAULT_PROVIDER=gemini           # provider padrão da plataforma
   LLM_DEFAULT_MODEL=gemini-2.5-pro      # modelo padrão
   ANTHROPIC_API_KEY=sk-ant-...          # fallback Claude da plataforma
   GOOGLE_API_KEY=AIza...                 # fallback Gemini da plataforma
   OPENAI_API_KEY=sk-...                  # fallback OpenAI da plataforma

5. USE em agentes (I1):
   def _get_model(self):
       from app.shared.providers.llm_factory import get_provider_for_tenant
       container = get_provider_for_tenant(tenant_id=self._company_id)
       return container.get_primary().to_langchain()  # retorna ChatModel LangChain

6. ADICIONE lint scripts ao CI:
   python scripts/check_llm_factory_enforcement.py || exit 1
   python scripts/check_llm_imports.py || exit 1

7. VERIFIQUE:
   - pytest tests/unit/test_llm_factory.py
   - pytest tests/unit/test_provider_container.py
   - pytest tests/integration/test_byok_isolation.py
```

### "Adiciona novo provider LLM (ex: Mistral)"

```
1. CRIE implementação:
   # app/shared/providers/llm_mistral.py
   from app.shared.providers.llm_provider import LLMProviderABC, LLMResponse
   from app.shared.providers.llm_factory import LLMProviderFactory
   
   @LLMProviderFactory.register
   class MistralProvider(LLMProviderABC):
       _provider_name = "mistral"
       
       @property
       def provider_name(self) -> str:
           return "mistral"
       
       @property
       def default_model(self) -> str:
           return "mistral-large-latest"
       
       async def generate(self, prompt, model=None, ...) -> LLMResponse:
           # implementação real usando SDK mistral
           ...
       
       async def generate_with_system(self, ...): ...
       async def generate_with_tools(self, ...): ...
       async def generate_structured(self, ...): ...

2. ADICIONE ao allowlist de check_llm_factory_enforcement.py:
   ALLOWLIST.add("app/shared/providers/llm_mistral.py")

3. ADICIONE ao ALLOWED_PATHS de check_llm_imports.py (se necessário)

4. ADICIONE ao FALLBACK_ORDER se aplicável:
   FALLBACK_ORDER = ["gemini", "claude", "mistral", "openai"]

5. ADICIONE modelos ao QUALITY_TIERS:
   QUALITY_TIERS["mistral-large-latest"] = "tier1"

6. IMPORTE na startup para registro:
   import app.shared.providers.llm_mistral  # registra via @LLMProviderFactory.register
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: LLM Providers BYOK (I4)

- **Entry point:** `get_provider_for_tenant(tenant_id)` → ProviderContainer (nunca SDK direto)
- **BYOK:** API keys por tenant em `tenant_llm_configs` table (DB) — isoladas por tenant
- **Providers suportados:** gemini, claude, openai (fallback automático nessa ordem)
- **Quality tiers:** Tier 1 (sonnet/opus/gemini-pro/gpt4o), Tier 2 (haiku/flash/mini)
- **Task tiers:** screening/wsi → obrigatório Tier 1; chat → Tier 2 suficiente
- **Enforcement:** `install_llm_guards()` na startup + lint scripts no CI bloqueiam SDK direto
- **Nunca:** `from anthropic import AsyncAnthropic()` — SEMPRE via `get_provider_for_tenant()`

Consultar `themes/infrastructure/I4_LLM_PROVIDERS.md`.
```

### Setup em `.cursor/rules/llm-providers.mdc`

```
---
description: "I4 LLM Providers BYOK"
alwaysApply: false
---

Quando o usuário pedir para:
- Chamar um LLM ou fazer completion
- Adicionar suporte a novo modelo ou provider
- Configurar BYOK para um tenant

1. Leia themes/infrastructure/I4_LLM_PROVIDERS.md
2. SEMPRE use get_provider_for_tenant(tenant_id) — nunca SDK direto
3. NUNCA importe anthropic/openai/google fora de app/shared/providers/
4. Para tasks críticas (screening, wsi): task="screening" em generate_with_fallback()
5. API keys SEMPRE de tenant_llm_configs DB ou env vars — NUNCA hardcode
6. Novo provider: herdar LLMProviderABC + @LLMProviderFactory.register + ALLOWLIST
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- `FALLBACK_ORDER` (ordem de fallback entre providers)
- Modelos específicos por tier (QUALITY_TIERS pode incluir novos modelos)
- `TASK_MINIMUM_TIER` (ajustar por task conforme produto)
- Backend de storage para `tenant_llm_configs` (PostgreSQL → outro DB relacional)
- Encrypted storage de API keys (usar KMS/Vault em vez de colunas simples)
- Timeout e retry por provider

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| `get_provider_for_tenant()` como único entry point | Enforcement de BYOK + audit trail | SDK direto = sem audit, sem PII strip, sem BYOK |
| `install_llm_guards()` na startup | Captura imports diretos que escapam do factory | Sem bootstrap = bypass completo do sistema |
| Lint scripts no CI (LIA-LLM-1) | Architectural guard — previne regressão | Futuros devs criam imports diretos sem perceber |
| API keys de env vars ou DB (nunca hardcode) | Segurança básica | Keys hardcoded em código versionado |
| PII stripping via bootstrap | LGPD Art. 12 — minimização de dados em LLMs | PII enviado ao LLM mesmo sem passar pelo factory |
| Quality tier enforcement para tasks críticas | Screening/WSI com modelo Tier 2 → qualidade inaceitável | Decisões de alto risco com LLM inadequado |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `install_llm_guards()` chamado UMA VEZ na startup (app/main.py)
- [ ] **(P0)** `get_provider_for_tenant()` funcionando com provider padrão (env vars)
- [ ] **(P0)** Migration `tenant_llm_configs` table criada (I9)
- [ ] **(P0)** Provider implementations carregadas na startup (imports em main.py)
- [ ] **(P0)** API keys NUNCA hardcoded — sempre env vars ou DB
- [ ] **(P0)** Lint scripts no CI: `check_llm_factory_enforcement.py` + `check_llm_imports.py`
- [ ] **(P1)** `generate_with_fallback()` testado com provider primário simulando falha
- [ ] **(P1)** `TASK_MINIMUM_TIER` enforcement: screening → Tier 1 obrigatório
- [ ] **(P1)** `tenant_llm_configs` com BYOK keys criptografadas (não plain text)
- [ ] **(P1)** `get_provider_for_tenant_from_db()` usado em workers assíncronos
- [ ] **(P2)** `get_voice_provider_for_tenant()` configurado para tenants com voz
- [ ] **(P2)** A/B testing entre providers (R2) via `ProviderContainer` variant
- [ ] **(P2)** `LLMProviderFactory.clear()` disponível em test fixtures

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| `ValueError: Unknown LLM provider: X` | Provider não registrado no `LLMProviderFactory` | Importar o módulo do provider na startup para executar o `@register` decorator |
| Lint CI falha com `ImportError` | Provider implementação tem import direto de SDK fora de providers/ | Verificar que SDK import está em `app/shared/providers/llm_X.py` |
| API key de outro tenant usada | `get_provider_for_tenant()` sem `tenant_id` → fallback para defaults globais | Sempre passar `company_id` explicitamente |
| Task "screening" usa Tier 2 | `task="chat"` em vez de `task="screening"` | Verificar `TASK_MINIMUM_TIER` antes de chamar `generate_with_fallback()` |
| `install_llm_guards()` chamado múltiplas vezes | Imports em módulos inicializados em paralelo | Usar o guard `_installed = True` já existente (é idempotente) |
| PII não removido antes do LLM | Bootstrap não foi chamado na startup OU provider bypassa o bootstrap | Verificar que `install_llm_guards()` é a PRIMEIRA call em main.py |
| Tenant recebe resposta com API key de outro tenant | `ProviderContainer` compartilhado entre tenants | `TenantProviderRegistry` isola containers; nunca reutilizar container de outro tenant |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| Factory registration | `tests/unit/test_llm_factory.py` | `register(MyProvider)` → `get("my_provider")` retorna instância |
| ProviderContainer BYOK | `tests/unit/test_provider_container.py` | container com api_keys={"claude": "sk-test"} → `get_primary()` usa essa key |
| Fallback chain | `tests/unit/test_provider_container.py` | primary provider lança exception → fallback para próximo |
| Task tier enforcement | `tests/unit/test_provider_container.py` | `task="screening"` + Tier 2 model → upgrade para Tier 1 |
| Tenant isolation | `tests/integration/test_byok_isolation.py` | tenant A e B → containers diferentes com keys diferentes |
| Lint enforcement | `tests/unit/test_lint_scripts.py` | `check_llm_factory_enforcement.py` em codebase limpa → exit 0 |
| Bootstrap PII strip | `tests/unit/test_llm_bootstrap.py` | Prompt com CPF → PII removido antes de enviar ao LLM |
| get_provider_for_tenant | `tests/unit/test_llm_factory.py` | `get_provider_for_tenant(tenant_id="co123")` → ProviderContainer com tenant_id correto |
| DB config carregada | `tests/integration/test_tenant_provider_registry.py` | Config no DB → `get_provider_for_tenant_from_db()` retorna container com primary correto |

---

## Referências

### Bundles verbatim
- Nenhum YAML específico (tema é 100% código).

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §F (LLM Factory / Choose Your AI)
- `LLM_FACTORY_HANDOFF_v2.md` — onboarding específico do sistema BYOK

### Cross-references
- **I1 Agent Architecture** — `LangGraphReActBase._get_model()` usa `get_provider_for_tenant()`
- **I3 Orchestration** — CascadedRouter Tier 5 usa BYOK via `get_provider_for_tenant()`
- **C2 LGPD PII** — `llm_bootstrap._strip_pii()` chama `strip_pii_for_llm_prompt()` (LIA-C04)
- **C5 Multi-tenancy** — `tenant_id` no `ProviderContainer` garante isolamento de API keys
- **C7 Audit Trail** — `_audit_llm_usage()` registra provider + model + tokens em todo call
- **I3 TenantBudget** — `check_request_budget_before_llm()` consultado antes de cada call LLM

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
