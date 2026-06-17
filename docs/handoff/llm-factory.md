# LLM Factory — Handoff de Engenharia para o Time Rails + IA

> **Audiência**: time de back-end Rails que vai re-implementar a camada de IA da plataforma LIA, e o time front-end que vai conectar ao novo back-end.
> **Objetivo**: descrever, sem necessidade de abrir código, *como* a camada `LLMProviderFactory` foi desenhada hoje em `lia-agent-system` (FastAPI/Python), *o que* ela resolve, *quem* a consome dentro do produto, *onde* estão os gaps, e *o que* deve ou não ser portado/repetido no novo back-end.
> **Idioma**: português técnico. Termos de mercado mantidos em inglês quando idiomáticos (factory, fallback, tier, BYOK).
> **Não-escopo**: corrigir gaps, implementar OpenRouter, refatorar `LLMService` legado, alterar UI de Configurações.

---

## 0. Sumário

1. [Visão geral e arquitetura](#1-visão-geral-e-arquitetura)
2. [Anatomia da factory](#2-anatomia-da-factory)
3. [Configuração do cliente — menu Configurações → LLMs](#3-configuração-do-cliente--menu-configurações--llms)
4. [Resolução por tenant em runtime](#4-resolução-por-tenant-em-runtime)
5. [Roteamento e cascata de modelos](#5-roteamento-e-cascata-de-modelos)
6. [Mapa exaustivo de consumidores](#6-mapa-exaustivo-de-consumidores)
7. [Particularidades por caso de uso](#7-particularidades-por-caso-de-uso)
8. [Prontidão para múltiplas LLMs](#8-prontidão-para-múltiplas-llms)
9. [Análise de eficiência por LLM](#9-análise-de-eficiência-por-llm)
10. [Auditoria de gaps e falhas](#10-auditoria-de-gaps-e-falhas)
11. [OpenRouter para testes — sim, não, condicional?](#11-openrouter-para-testes)
12. [Padrões de mercado e melhores práticas](#12-padrões-de-mercado-e-melhores-práticas)
13. [Apêndices](#13-apêndices)

---

## 1. Visão geral e arquitetura

### 1.1 O problema que a factory resolve

A LIA é multi-tenant e oferece um modelo "**Choose Your AI / BYOK**" (Bring Your Own Key): cada cliente pode usar a própria conta da OpenAI, Anthropic ou Google em vez de consumir a chave do sistema. A factory existe para que **a lógica de negócio jamais saiba qual provider está atendendo a request**: ela apenas pede "um provider para esse tenant", e a factory devolve um `LLMProviderABC` configurado com a chave certa, modelo certo e cadeia de fallback certa.

Os requisitos endereçados:

| Requisito | Como a factory resolve |
|---|---|
| **Multi-tenant + BYOK** | `TenantProviderRegistry` mantém um `ProviderContainer` por `company_id`, cada um com suas próprias chaves criptografadas (Fernet) |
| **Fallback entre provedores** | `ProviderContainer.generate_with_fallback()` percorre `[primary, ...fallback_order]` na ordem; para cada provider tenta primeiro a chave do tenant, depois a chave do sistema |
| **Circuit breaker por provider** | Cada provider concreto é decorado com `@circuit_breaker_decorator(<NOME>_CIRCUIT)` — se um provider explode, o breaker abre e o fallback assume |
| **Auditoria + LGPD** | Todas as chamadas passam por `strip_pii_for_llm_prompt` (E6) e `audit_service.log_decision` (E7) antes do provider ser invocado |
| **Token budget por tenant** | `check_request_budget_before_llm` é chamado *antes* do primeiro provider, evitando estouro silencioso |
| **Cascata de custo** | `LLMCascadeRouter` (Flash → Pro/Sonnet → Opus) e `CascadedRouter` (8 tiers, do cache em memória ao agente ReAct autônomo) |

### 1.2 Glossário

| Termo | Significado neste documento |
|---|---|
| **Provider** | Implementação concreta de um SDK de LLM (Gemini / Claude / OpenAI). Classe que herda de `LLMProviderABC`. |
| **`LLMProviderFactory`** | Registro **global** de classes de provider. Mantém `_providers` (classes) e `_instances` (singletons). |
| **`ProviderContainer`** | Container DI **por tenant**. Sabe qual é o primary provider, a fallback chain, e quais chaves de API usar. |
| **`TenantProviderRegistry`** | Singleton `tenant_id → ProviderContainer`. Cacheia containers para que cada tenant tenha o seu, isolado dos demais. |
| **BYOK** | *Bring Your Own Key*. Cliente cadastra a própria chave em `Configurações → LLMs`. |
| **Tier** | Camada da cascata de custo. `fast` (Flash/Haiku/Mini), `mid` (Pro/Sonnet/4o), `powerful` (Opus/Pro/4-turbo). |
| **Cascade Router** | `LLMCascadeRouter` (custo) + `CascadedRouter` (intent). Dois roteadores diferentes que coexistem. |
| **Tenant** | Equivalente a *empresa cliente*, identificado por `company_id`. |

### 1.3 Diagrama ponta a ponta

```mermaid
flowchart TD
    subgraph Request
      A[HTTP/WS Request] --> B[AuthEnforcementMiddleware]
      B --> |seta _current_company_id| C[Endpoint / Orchestrator]
    end

    subgraph "Resolução por tenant"
      C --> D[get_provider_for_tenant_from_db tenant_id]
      D --> E[TenantProviderRegistry singleton]
      E --> |miss| F[load_from_db]
      F --> G[(tenant_llm_configs)<br/>Fernet-encrypted keys]
      G --> H[ProviderContainer<br/>tenant_id, primary, fallback, api_keys]
      E --> |hit| H
    end

    subgraph "Guardrails pré-LLM"
      H --> I[check_request_budget_before_llm<br/>token ceiling por plano]
      I --> J[strip_pii_for_llm_prompt<br/>LGPD Art. 12]
      J --> K[audit_service.log_decision<br/>E7]
    end

    subgraph "Fallback chain"
      K --> L{Provider 1<br/>tenant key}
      L --> |OK| Z[LLMResponse.text]
      L --> |fail| M{Provider 1<br/>system key}
      M --> |OK| Z
      M --> |CircuitBreakerError ou fail| N{Provider 2<br/>tenant key → system key}
      N --> |OK| Z
      N --> |fail| O{Provider 3<br/>tenant key → system key}
      O --> |OK| Z
      O --> |fail| P[LIALLMError<br/>LLM_ALL_PROVIDERS_FAILED]
    end

    subgraph "Provider concreto"
      L --> Q[GeminiLLMProvider<br/>circuit: GEMINI_CIRCUIT]
      Q --> R[google.genai.Client]
      L --> S[ClaudeLLMProvider<br/>circuit: ANTHROPIC_CIRCUIT]
      S --> T[anthropic.Anthropic]
      L --> U[OpenAILLMProvider<br/>circuit: OPENAI_CIRCUIT]
      U --> V[openai.OpenAI]
    end
```

**Como ler**: a request entra; o middleware de autenticação injeta `company_id` num `contextvar`; o consumidor pede um container para esse tenant; a factory carrega config criptografada do banco (ou usa cache em memória); aplica orçamento + PII + auditoria; e só então tenta o provider primário, com fallback automático para chave do sistema e para os providers seguintes.

---

## 2. Anatomia da factory

Arquivos: `lia-agent-system/app/shared/providers/`.

### 2.1 `LLMProviderABC` — o contrato

`app/shared/providers/llm_provider.py` (linhas 45–112).

Toda implementação de provider deve expor:

| Método | Uso |
|---|---|
| `provider_name` (property) | `"gemini" \| "claude" \| "openai"` |
| `default_model` (property) | Modelo default por provider — **hardcoded** hoje (gap, ver §10) |
| `generate(prompt, model, temperature, max_tokens, **kwargs) → LLMResponse` | Texto livre |
| `generate_with_system(system_prompt, user_message, ...)` | System + user |
| `generate_with_tools(messages, tools, system_prompt, max_tokens) → LLMToolResponse` | Function calling / tool use |
| `generate_structured(messages, output_schema, system_prompt, max_tokens) → dict` | JSON estruturado por schema |

Tipos de retorno padronizados (`LLMResponse`, `LLMToolCall`, `LLMToolResponse`) tornam a chamada idempotente entre providers — quem consome a factory recebe sempre o mesmo dataclass.

> **Padrão de mercado**: equivalente ao que LiteLLM chama de "unified completion API". A LIA tem a abstração, mas com escopo menor (4 métodos vs ~20 do LiteLLM).

### 2.2 `LLMProviderFactory` — registro global de classes

`llm_factory.py` linhas 26–68.

- `_providers: dict[str, type]` — classes registradas via `@LLMProviderFactory.register` (decorador aplicado em cada `*LLMProvider`).
- `_instances: dict[str, LLMProviderABC]` — singletons "globais" (sem chave de tenant), usados quando ninguém passa `api_key`.
- `available_providers()` — listagem (útil para o endpoint `/admin/llm-config/providers`).
- `clear()` — só usado em testes.

> Esta classe **não deve ser usada diretamente** pela lógica de negócio em código novo — ela é uma fábrica de classes, não de instâncias com a chave certa do tenant. O ponto de entrada correto é `get_provider_for_tenant()` ou `get_provider_for_tenant_from_db()`.

### 2.3 `ProviderContainer` — DI por tenant

`llm_factory.py` linhas 75–266.

**Ciclo de vida**:
1. Construído com `tenant_id`, `primary_provider`, `fallback_order`, `provider_api_keys`.
2. `get(name)` faz lazy-instantiation: se houver chave do tenant, instancia `<Provider>(api_key=tenant_key)`; senão instancia `<Provider>()` (que cai na chave do sistema via env var).
3. `get_primary()` retorna o provider preferido.
4. `generate_with_fallback(prompt, system, **kwargs)` é o método crítico:

```python
# pseudo-código resumindo linhas 167–259
check_request_budget_before_llm(...)            # token ceiling Fase 3
for provider_name in [primary, *fallback_order]:
    try:
        return await provider(tenant_key).generate(...)
    except CircuitBreakerError: continue
    except Exception:
        if tenant_key:
            try: return await provider(system_key).generate(...)
            except: continue
raise LIALLMError(LLM_ALL_PROVIDERS_FAILED)
```

**Pontos sutis**:
- A primeira coisa que acontece é o **check de orçamento por request** — chamadas que estourariam o teto de tokens por chamada do plano são rejeitadas *antes* de qualquer provider ser tocado.
- A cadeia tenta **chave-do-tenant antes da chave-do-sistema** dentro do mesmo provider; só passa para o próximo provider depois de esgotar as duas.
- Erros são acumulados em `errors[]` e expostos no `LIALLMError.details` para diagnóstico.

### 2.4 `TenantProviderRegistry` — cache de containers

`llm_factory.py` linhas 273–533.

- Singleton (`get_instance()`).
- `get_container(tenant_id)`: retorna o container cacheado para aquele tenant; se não existir, resolve config (DB → YAML → env) e cria.
- `_resolve_provider_config()` (linhas 349–397): ordem de precedência é **explícita por código**:
  1. Overrides explícitos passados pelo caller
  2. Cache em memória de `tenant_llm_context._tenant_configs`
  3. Best-effort `asyncio.run(get_tenant_llm_config(...))` — só funciona se NÃO estivermos dentro de event loop
  4. YAML global (`tool_permissions.yaml` → `cfg.llm_provider`)
  5. Env var `LLM_DEFAULT_PROVIDER` ou hardcoded `"gemini"`
- `load_from_db(tenant_id)` (linhas 458–495): caminho async preferido; carrega do banco, descriptografa chaves, cria container com `provider_api_keys` setado.

> ⚠️ **Cache sem TTL** — `_containers` cresce indefinidamente; em produção com milhares de tenants vira memory leak (gap §10).

### 2.5 Providers concretos

| Arquivo | Default model | Particularidades |
|---|---|---|
| `llm_gemini.py` | `gemini-2.5-flash` | Usa `google.genai` SDK; `circuit_breaker_decorator(GEMINI_CIRCUIT)`; retry em resposta vazia (`tenacity`); aceita `AI_INTEGRATIONS_GEMINI_BASE_URL` (proxy do Replit). |
| `llm_claude.py` | `claude-sonnet-4-6` | Anthropic SDK síncrono envolvido em método `async`; integração LangSmith via `@_traceable`; métricas Prometheus (atualmente desabilitadas — `_METRICS_AVAILABLE = False`). |
| `llm_openai.py` | `gpt-4o` | OpenAI SDK síncrono; sem retry, sem trace LangSmith — implementação mais enxuta dos três. |

Há também o `embedding_factory.py` (espelho da `LLMProviderFactory` para embeddings — `gemini` default, `openai` fallback; ver §6 e §7).

### 2.6 Pontos de entrada recomendados

```python
# Sync (ex.: dentro de view FastAPI sem async context)
from app.shared.providers.llm_factory import get_provider_for_tenant
container = get_provider_for_tenant("acme")
text = await container.generate_with_fallback(prompt)

# Async (preferido — sempre que houver event loop)
from app.shared.providers.llm_factory import get_provider_for_tenant_from_db
container = await get_provider_for_tenant_from_db("acme")
text = await container.generate_with_fallback(prompt, system="Você é a LIA")
```

> **Recomendação para o time Rails**: replicar essa dupla `(sync, async)` é prático, mas o código Rails é tipicamente sync por convenção. Em Rails recomenda-se um `LlmFactory.for(company_id)` único, com cache thread-safe (`Concurrent::Map`), e fazer as chamadas HTTP via `Faraday` com `connection: persistent` para reaproveitar TLS.

---

## 3. Configuração do cliente — menu Configurações → LLMs

### 3.1 Fluxo end-to-end

```
Front-end (plataforma-lia)                  Back-end (lia-agent-system)
──────────────────────────                  ──────────────────────────
IntegrationsHub.tsx                         POST/GET/PUT /api/backend-proxy/llm-config
   └─ ApiKeyConfigForm.tsx       ───────►   /admin/llm-config       (llm_config.py)
        (campos: provider,                       │
         api_key, model,                         ▼
         routing.chat,                       LlmConfigRepository  (encrypt_value via Fernet)
         fallback_order)                         │
                                                 ▼
                                            tenant_llm_configs (PostgreSQL)
                                            campos: primary_provider,
                                                    fallback_order JSONB,
                                                    providers JSONB (api_keys cifradas),
                                                    routing JSONB,
                                                    is_active, created_by

                                            clear_tenant_config_cache(company_id)
                                            ↑
                                            invalida cache em tenant_llm_context._tenant_configs
```

### 3.2 Endpoints

`app/api/v1/llm_config.py`:

| Método | Path | Função |
|---|---|---|
| `GET` | `/admin/llm-config` (linhas 78–129) | Retorna config corrente. **API keys são mascaradas** (`abcd1234...wxyz`). Se não houver row, devolve defaults `gemini` + fallback `[gemini, claude, openai]`. |
| `PUT` | `/admin/llm-config` (linhas 132–239) | Upsert com **merge semântica**: chaves contendo `...` (formato mascarado) são tratadas como "preserve a existente". Grava audit log. Invalida cache. |
| `POST` | `/admin/llm-config/test` (linhas 242–300) | Teste de conectividade. ⚠️ **Bypassa a factory** — instancia `genai.Client/AsyncAnthropic/AsyncOpenAI` diretamente (gap §10). |
| `GET` | `/admin/llm-config/providers` (linhas 303–331) | Catálogo estático: lista de provedores + modelos suportados. **Hardcoded** — atualizar é trabalho manual. |

### 3.3 Persistência e criptografia

`app/domains/ai/repositories/llm_config_repository.py` + tabela `tenant_llm_configs` (`libs/models/lia_models/tenant_llm_config.py`):

- `_encrypt_provider_keys` (linhas 17–26): cifra cada `api_key` com Fernet (chave em env var) **se** ela ainda não estiver cifrada (heurística: prefixo `gAAAAA`).
- `_decrypt_provider_keys` (linhas 29–36): descriptografa só na leitura interna; nunca expõe ao cliente sem mascaramento.
- `_Snapshot` (linhas 39–43): repositório retorna **snapshot detached** para impedir o ORM de fazer flush dos campos descriptografados de volta ao banco (evita corrupção).
- `_merge_providers` (linhas 81–92): trata `_remove: true` para remoção explícita.

### 3.4 Como a chave do cliente passa a ser usada em runtime

1. PUT `/admin/llm-config` chama `clear_tenant_config_cache(company_id)`.
2. Próxima request entra no middleware → `_current_company_id.set(company_id)`.
3. Endpoint chama `get_provider_for_tenant_from_db(tenant_id)`.
4. `TenantProviderRegistry.load_from_db()` → `LlmConfigRepository.get_by_company_id()` → snapshot descriptografado → `ProviderContainer(provider_api_keys=...)`.
5. Container popula seu próprio `_api_keys` e instancia providers passando `api_key=tenant_key` no construtor.
6. Próxima vez que esse tenant aparecer, o container está cacheado.

---

## 4. Resolução por tenant em runtime

Arquivo central: `app/shared/tenant_llm_context.py`.

### 4.1 Como o `company_id` chega à factory

```
Cliente HTTP/WS
   ↓ Authorization: Bearer <jwt>
AuthEnforcementMiddleware (app/middleware/auth_enforcement.py)
   ↓ extrai claims, valida tenant
   ↓ _current_company_id.set(company_id)   ←  contextvar (não thread-local)
Handler / Orchestrator / Tool / Agent
   ↓ get_current_llm_tenant() → "acme"
get_provider_for_tenant_from_db("acme")
```

A propagação usa `contextvars.ContextVar`, que funciona **transparentemente em corrotinas** (cada task asyncio recebe sua cópia). É o mecanismo correto para FastAPI; em Rails o equivalente seria `RequestStore` ou `CurrentAttributes`.

### 4.2 Cache em memória (`_tenant_configs`)

`tenant_llm_context.py` linha 33: `_tenant_configs: dict = {}`.

- Populado por `get_tenant_llm_config(company_id)` (linhas 36–77) — DB read + decrypt.
- Invalidado por `clear_tenant_config_cache(company_id)` quando o cliente atualiza a config.
- Pré-aquecido por `prime_tenant_llm_cache(company_id)` (linhas 160–177), chamado pelo middleware para evitar cache miss síncrono.

⚠️ **Sem TTL, sem LRU, sem limite de tamanho**. É um `dict` puro — é correto enquanto o número de tenants ativos for pequeno. Em escala (>10k tenants) precisa virar `cachetools.TTLCache(maxsize=2000, ttl=300)` no mínimo.

### 4.3 Precedência efetiva

| Camada | Lookup | O que acontece se vazio |
|---|---|---|
| 1. Override explícito do caller | argumento `primary_provider=` em `get_container` | passa para 2 |
| 2. Cache em memória `_tenant_configs` | dict in-process | passa para 3 |
| 3. DB `tenant_llm_configs` (assíncrono) | `LlmConfigRepository.get_by_company_id` | passa para 4 |
| 4. YAML global `tool_permissions.yaml` | `tool_permissions_loader.get_permissions(None)` | passa para 5 |
| 5. Env var `LLM_DEFAULT_PROVIDER` | `os.environ.get(...)` | hardcoded `"gemini"` |

### 4.4 O que acontece quando NÃO há contexto de tenant

Se `get_current_llm_tenant()` devolve `""` (request sem auth, job de Celery sem context, teste isolado), a factory cai direto para a etapa 4/5 e usa **a chave do sistema**. A consequência é silenciosa: a chamada funciona, mas é faturada na conta da Replit/plataforma, não na do cliente. Esse é um dos gaps críticos (§10).

> **Recomendação**: o time Rails deve falhar fechado (`raise NoTenantContextError`) em vez de cair em chave-do-sistema silenciosamente; e tornar a chave-do-sistema explícita por feature flag (`ALLOW_SYSTEM_KEY_FALLBACK=true`).

---

## 5. Roteamento e cascata de modelos

Há **dois roteadores diferentes que coexistem** e que muita gente confunde:

### 5.1 `LLMCascadeRouter` — cascata de custo (modelo a modelo)

Arquivo: `app/orchestrator/llm_cascade.py`.

Implementa a escada **Flash → Sonnet → Opus** (apesar do nome sugerir Gemini puro, hoje mistura provedores):

| Tier | Setting de modelo | Threshold de aceitação | Exemplo default |
|---|---|---|---|
| 3a. fast | `LLM_FAST_MODEL` | ≥ `LLM_CASCADE_FAST_THRESHOLD` (0.80) | `gemini-2.5-flash` |
| 3b. mid | `LLM_PRIMARY_MODEL` | ≥ `LLM_CASCADE_MID_THRESHOLD` (0.70) | `claude-sonnet-4-6` |
| 3c. powerful | `LLM_POWERFUL_MODEL` | aceita o que vier | `claude-opus-4` |

Detalhes (linhas 79–202):
- O provider é **derivado do nome do modelo** via `_provider_for_model()`: prefixo `gemini-` → gemini; `gpt-` ou `openai-` → openai; resto → claude.
- O usuário/tenant pode passar `preferred_model=` que é tentado **antes** da cascata, com fail-safe para a cascata padrão.
- Cada chamada acumula tokens e custo USD em `cost_accumulator`, registrado no `tenant_budget`.

### 5.2 `CascadedRouter` — roteamento por intent (8 tiers)

Arquivo: `app/orchestrator/cascaded_router.py`.

Decide **qual domínio** atende a request, do mais barato ao mais caro:

```
Tier 0: MemoryResolver           — pronomes / referências de contexto
Tier 1: LRU in-process           — hash MD5
Tier 2: Redis hash               — distribuído, exato
Tier 3: VectorSemanticCache      — pgvector cosine ≥ 0.85
Tier 4: FastRouter               — regex/keywords
Tier 5: LLMCascadeRouter         — Flash → Sonnet → Opus
Tier 6: AutonomousReActAgent     — agente cross-domain (feature flag)
Tier 7: clarification_needed     — pergunta para o usuário
```

A integração com a factory acontece **só no Tier 5**: o router chama `llm_service.generate(provider=..., model=...)`, que por sua vez (se houver `_tenant_container` setado) delega ao `ProviderContainer`. Nos demais tiers a factory não é tocada.

### 5.3 Override por tenant via campo `routing`

A tabela `tenant_llm_configs.routing` aceita JSON do tipo:

```json
{
  "chat": "gemini",
  "embedding": "openai",
  "screening": "claude",
  "voice": "gemini",
  "fallback": "openai"
}
```

**Hoje, esse campo é lido em apenas dois lugares**:
- `langgraph_react_base._get_model` (linha 407): usa `routing.screening` para decidir o provider dos agentes ReAct.
- `embedding_factory._get_tenant_provider` (linhas 220–245): usa para selecionar Gemini com chave do tenant.

Ou seja: o cliente cadastra o campo, mas o produto **ignora** parcialmente. WSI, jd_enrichment, semantic_search e o orchestrator principal não consultam `routing.*` — usam `primary_provider` ou hardcode.

> **Recomendação para o Rails**: tratar `routing` como contrato de primeiro nível. Cada caso de uso (chat, screening, embedding, voice) deve passar uma `purpose` para a factory, e a factory consulta `routing[purpose]` antes de cair em `primary_provider`.

---

## 6. Mapa exaustivo de consumidores

Lista dos pontos do produto que tocam LLM. Para cada um: arquivo, se passa pela factory, parâmetros e particularidades.

| # | Consumidor | Arquivo + linhas-chave | Caminho LLM | Parâmetros | Observações |
|---|---|---|---|---|---|
| 1 | Chat / Orquestrador | `app/orchestrator/main_orchestrator.py` (45–46) | `get_provider_for_tenant()` + `LLMService` legado | herda do tier (Sonnet) | Caminho **híbrido** — usa factory para alguns paths e `llm_service.claude` (LangChain) para outros. |
| 2 | WSI F2/F3/F6 — geração de perguntas | `app/domains/job_creation/services/wsi_question_generator.py` (196–218) | Helper `create_tracked_llm` (não a factory direta) | `temp=0.1` (BigFive), `0.7` (técnicas), `0.75` (comportamentais), `max_tokens=4000` | Cada bloco tem seu próprio LLM; passa por audit/PII via callback. |
| 3 | WSI Compact / talent pools | `app/services/wsi_compact_pipeline.py` (112–142) | **`get_llm(tier="fast")`** — função inexistente! | n/a | 🔴 **Bug crítico** (gap §10): o módulo importa `get_llm` de `llm_factory` que não existe — código quebra em runtime na primeira chamada. |
| 4 | WSI F11 / CBI / parecer | `app/api/v1/wsi/reports.py` (263, 337–349) | `get_provider_for_tenant().generate_with_fallback()` | system + user prompt longos | ✅ Caminho correto pela factory. |
| 5 | JD Enrichment F1 | `app/domains/job_creation/services/jd_enrichment.py` (266–289) | LLM via Claude (LangChain) com `temp=0.3, max_tokens=4000, top_p=0.95` | "Single LLM call replaces 4 regex extractors" | Não passa pela factory — usa `ChatAnthropic` diretamente. |
| 6 | Semantic search / expansão | `app/shared/intelligence/semantic_search_service.py` (340–349) | `get_provider_for_tenant().generate_with_fallback(formatted_prompt)` | Gemini Flash visado (P95 < 300ms) | ✅ Factory; cacheia em Redis. |
| 7 | Embeddings (vetoriais) | `app/shared/providers/embedding_factory.py` | Factory paralela à de LLM, mas **separada** | Gemini default, OpenAI fallback | Lê chave do tenant em `_tenant_configs[company_id].providers.gemini.api_key`. |
| 8 | Funil — Pipeline Feedback | `app/domains/pipeline/agents/pipeline_feedback_tool.py` (60–80) | `llm_service` (legado) com `ChatPromptTemplate` | system + user prompts via LangChain | Não usa factory — depende do `LLMService.claude` global. |
| 9 | Funil — Pipeline Transition Agent | `app/domains/pipeline/agents/pipeline_transition_agent.py` | LangGraph ReAct via `langgraph_react_base` | `LLM_AGENT_TEMPERATURE` | Cai em `_get_model` (gap principal). |
| 10 | LangGraph ReAct base (todos os agentes) | `libs/agents-core/lia_agents_core/langgraph_react_base.py` (340–456) | **Bypass total da factory** — cria `ChatAnthropic/ChatOpenAI/ChatGoogleGenerativeAI` direto | `LLM_AGENT_TEMPERATURE`, `streaming=True` | 🟠 Gap §10. |
| 11 | Voice (Gemini Live / OpenAI Realtime) | `app/shared/providers/llm_factory.py` (591–646) | `get_voice_provider_for_tenant()` decide com base no `primary_provider` | n/a | Gemini → `GeminiLiveVoiceProvider`; OpenAI → `OpenAIRealtimeVoiceProvider`; Claude/outro → `CompositeVoiceProvider` (STT Gemini + LLM tenant + TTS Gemini). |

Notação: ✅ correto · 🟠 gap conhecido · 🔴 bug.

---

## 7. Particularidades por caso de uso

### 7.1 WSI (Work Sample Interview)

**Por que é especial**: WSI tem regras absolutas (apenas CBI, sem perguntas hipotéticas, sem fit cultural, gates G1–G6). Erros do LLM aqui geram contestação trabalhista — não dá para "tentar de novo com outro modelo" sem pensar.

**Como está hoje**:
- F1 (jd_enrichment): `temp=0.3` para enriquecer JD — privilegia consistência. Claude Sonnet, não passa pela factory.
- F2 (BigFive extraction): `temp=0.1` — quase determinístico.
- F3 (trait ranking): **fórmula determinística** em Python (`TRAIT_FORMULA_WEIGHTS = {llm: 0.4, prior: 0.35, seniority_boost: 0.25}`); nem chama LLM.
- F6 (geração de perguntas): `temp=0.7` técnicas, `temp=0.75` comportamentais — variabilidade controlada.
- F11 (parecer/CBI): chama `generate_with_fallback`, prompts grandes (>2k tokens).
- Compact (talent pool): tier `fast` (Flash), 3–5 perguntas.

**O que muda se o cliente trocar de provider**:
- Determinismo (`temp=0.1`) é respeitado por todos os SDKs, mas **a estabilidade entre runs varia**: GPT-4o é o mais estável, Gemini Flash o mais errático.
- Geração de perguntas com Gemini Flash às vezes ignora "REGRAS ABSOLUTAS" do prompt (omitir hipotéticas) — Claude Sonnet/Opus respeitam melhor.
- F11 (parecer longo, JSON estruturado): Claude Sonnet > GPT-4o > Gemini Pro nesse benchmark interno.

**Cuidados para o Rails**:
- Manter **PromptRegistry versionado** com hash; nunca alterar prompts WSI sem rodar regression suite (gold dataset).
- Validar saída com schema Pydantic/dry-run *antes* de persistir.
- Para clientes que escolherem Gemini Flash, considerar uma flag "WSI-grade output" que força fallback para Sonnet só nesse caminho.

### 7.2 Embeddings

**Por que é especial**: vetores ficam armazenados em `pgvector`; mudar de provider invalida a base inteira (dimensões e distribuição mudam).

**Como está hoje**:
- Default: `gemini-embedding-001` (3072 dims) ou compatível.
- Fallback: `text-embedding-3-small` (OpenAI, 1536 dims).
- Order: `EMBEDDING_FALLBACK_ORDER = ["gemini", "openai"]`.
- Suporte BYOK: só Gemini hoje (`embedding_factory._get_tenant_provider`).

**Restrição crítica não documentada hoje**:
> ⚠️ Se o cliente trocar de Gemini para OpenAI **depois** de já ter indexado candidatos, **toda a base vetorial vira lixo** (similarity scores incomparáveis). O produto não tem migração de embeddings.

**Cuidados para o Rails**:
- Tornar `embedding_provider` **imutável** após primeiro uso (com migração explícita exigindo reindexação completa).
- Versionar vetores: gravar `provider`, `model`, `dim` em cada row — para detectar mistura.
- Não fazer fallback silencioso entre Gemini e OpenAI em runtime: se Gemini cai e OpenAI assume, os vetores gerados não são compatíveis com o índice — *deve falhar fechado*.

### 7.3 Funil de talentos

**Por que é especial**: feedback ao candidato vai por e-mail/WhatsApp e tem implicação LGPD Art. 20 (revisão por humano).

**Como está hoje**:
- `pipeline_feedback_tool.py`: usa `llm_service.claude` (LangChain Anthropic) com prompts diferenciados por gate (Gate 1 construtivo / Gate 2 conclusivo).
- `pipeline_transition_agent.py`: agente ReAct via `langgraph_react_base._get_model` (cai no bypass §10).
- Guardrails: FairnessGuard no output, FactChecker, link para revisão humana hard-coded em `HUMAN_REVIEW_LINK`.

**O que muda se o cliente trocar de provider**:
- Tom do feedback varia bastante entre Gemini (mais frio/formal) e Claude (mais empático/longo).
- GPT-4o às vezes inventa "próximos passos" que não existem na config — guardrail de FactChecker é essencial.

**Cuidados para o Rails**:
- Replicar FairnessGuard como serviço próprio antes de qualquer e-mail sair.
- Nunca expor score numérico no texto de feedback (regra de produto, não de IA).
- Logar (audit) qual modelo gerou cada feedback — necessário para responder DSR (LGPD Art. 18).

---

## 8. Prontidão para múltiplas LLMs

### 8.1 O que está pronto hoje

| Provider | Modelos suportados (hardcoded em `llm_config.py`) | Tool calling | Embeddings |
|---|---|---|---|
| Google Gemini | `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash` | ✅ via `FunctionDeclaration` | ✅ |
| Anthropic Claude | `claude-sonnet-4-6`, `claude-haiku-3-5` | ✅ via `tool_use` | ❌ |
| OpenAI | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` | ✅ via `function calling` | ✅ |

### 8.2 Como adicionar um novo provider

Passo a passo, atual:

1. Criar `app/shared/providers/llm_xxx.py` herdando `LLMProviderABC`.
2. Implementar os 4 métodos abstratos + `provider_name` + `default_model`.
3. Adicionar decorator `@circuit_breaker_decorator(XXX_CIRCUIT)` em cada chamada de SDK.
4. No `app/main.py` (ou wherever o registry é populado): `LLMProviderFactory.register(XxxLLMProvider)`.
5. Atualizar `FALLBACK_ORDER` em `llm_factory.py` se o novo provider deve participar do fallback.
6. Atualizar a lista hardcoded em `llm_config.py:303-331` para aparecer no front-end.
7. Atualizar `ProviderConfig` schema em `llm_config.py:32` se houver campos novos.
8. Atualizar `_provider_for_model()` em `llm_cascade.py:204` se o novo provider tem prefixo de modelo distinto.

### 8.3 O que NÃO está pronto

- **OpenRouter, Mistral, Groq, AWS Bedrock, Azure OpenAI, Ollama, vLLM** — nenhum suporte. Adicionar requer ~150–300 linhas por provider.
- **Streaming uniforme**: o ABC não tem `stream()` — endpoints SSE acessam `AsyncAnthropic` diretamente via `get_anthropic_streaming_client_for_tenant`.
- **Anthropic prompt caching**: não usado (perda de ~50% de custo em prompts repetitivos como WSI).
- **Multimodal genérico**: só Gemini tem caminho dedicado (`generate_native_gemini`); Claude vision e GPT-4o vision não têm wrapper.
- **Tool use compatível entre providers**: cada provider tem schema próprio (`FunctionDeclaration` vs `tool_use` vs `function`); o ABC tenta unificar mas há perdas (ex.: parallel tool calls do Claude Sonnet 4.6 não são expostas).

---

## 9. Análise de eficiência por LLM

A pergunta "o cliente que escolhe um provider 'fraco' degrada a qualidade?" tem resposta **sim, mas depende da tarefa**. Matriz qualitativa abaixo.

### 9.1 Matriz por caso de uso da LIA

Escala: ⭐⭐⭐⭐⭐ excelente · ⭐⭐⭐ médio · ⭐ ruim. Notas baseadas em LMSys Chatbot Arena (Mar/2026), MTEB Leaderboard (Hugging Face), Berkeley Function-Calling Leaderboard (BFCL v3) e nossa observação interna.

| Caso de uso | Gemini 2.5 Flash | Gemini 2.5 Pro | Claude Sonnet 4.6 | Claude Haiku 3.5 | GPT-4o | GPT-4o-mini |
|---|---|---|---|---|---|---|
| **Roteamento de intent** (cascade router) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Geração de pergunta WSI (CBI)** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Parecer/CBI longo (F11)** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Chat agentic (ReAct + tools)** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Busca semântica / expansão** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Embeddings (MTEB)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | n/a | n/a | ⭐⭐⭐⭐⭐ | n/a |
| **Custo (1M tokens output)** | $0.30 | $10 | $15 | $4 | $10 | $0.60 |
| **Latência P50** | 0.6s | 1.8s | 1.4s | 0.8s | 1.2s | 0.7s |

### 9.2 Recomendação por tarefa

| Tarefa | Recomendação primária | Por quê |
|---|---|---|
| Routing/intent | Gemini Flash | Custo + latência; precisão "good enough" |
| WSI F2 BigFive | Claude Sonnet | Determinismo, segue regras absolutas |
| WSI F6 perguntas | Claude Sonnet | Estilo CBI, evita hipotéticas |
| WSI F11 parecer | Claude Sonnet/Opus | Coerência em texto longo, citação de evidências |
| JD enrichment F1 | Claude Sonnet ou GPT-4o | Formatação estruturada robusta |
| Chat agentic | Claude Sonnet 4.6 | Líder em tool use (BFCL v3) |
| Busca semântica | Gemini Flash | Latência crítica (P95 < 300ms) |
| Embeddings | Gemini `gemini-embedding-001` | Top-3 MTEB; integrado |
| Voice realtime | Gemini Live / OpenAI Realtime | Único caminho nativo multimodal |

### 9.3 Referências públicas

1. **LMSys Chatbot Arena Leaderboard** — https://chat.lmsys.org/?leaderboard (rankings ELO de modelos em tarefas conversacionais).
2. **MTEB — Massive Text Embedding Benchmark** — https://huggingface.co/spaces/mteb/leaderboard (tabela definitiva de embeddings).
3. **Berkeley Function-Calling Leaderboard (BFCL v3)** — https://gorilla.cs.berkeley.edu/leaderboard.html (tool use rigoroso).
4. **Anthropic — "Claude 4 system card"** — relatórios oficiais de tool use, instruction following, refusal rates.
5. **Google DeepMind — "Gemini 2.5 technical report"** — métricas internas de latência e qualidade (multimodal).
6. **OpenAI Cookbook — Structured Outputs** — recomendação oficial sobre `response_format` para JSON.
7. **Anthropic Prompt Caching docs** — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching (50% economia em prompts repetitivos).

---

## 10. Auditoria de gaps e falhas

| # | Gap | Arquivo + linhas | Severidade | Recomendação |
|---|---|---|---|---|
| G1 | **Bypass da factory em LangGraph ReAct** — agentes instanciam `ChatAnthropic/ChatOpenAI/ChatGoogleGenerativeAI` diretamente, sem fallback nem circuit breaker | `libs/agents-core/lia_agents_core/langgraph_react_base.py:340–456` | 🔴 Alta | Mover construção do model para um wrapper que use `get_provider_for_tenant_from_db` e exponha interface compatível com LangChain (ex.: `LangChainAdapter(container)`). |
| G2 | **Bypass no endpoint de teste** — `POST /admin/llm-config/test` instancia clients diretos | `app/api/v1/llm_config.py:254–280` | 🟠 Média | Refatorar para usar `LLMProviderFactory.get(provider_name)` com `api_key` injetado. Hoje o teste pode passar e o uso real falhar (e vice-versa). |
| G3 | **`LLMService.generate` sem fallback robusto** — só tenta o `_tenant_container` e cai em `LLMService.claude` global em caso de erro | `app/domains/ai/services/llm.py:309–407` | 🟠 Média | Substituir todo `LLMService.generate` por `container.generate_with_fallback`; deprecar a classe legada gradualmente. |
| G4 | **Modelos default hardcoded** nos providers | `llm_gemini.py:23`, `llm_claude.py:29`, `llm_openai.py:15` | 🟡 Baixa | Mover para `settings` ou para `tenant_llm_configs.providers[*].model`; permitir update sem deploy. |
| G5 | **Cache `_tenant_configs` sem TTL/limite** | `app/shared/tenant_llm_context.py:33` | 🟠 Média | Substituir por `cachetools.TTLCache(maxsize=2000, ttl=300)` ou Redis. Risco de memory leak em produção com >1k tenants ativos. |
| G6 | **Cache `TenantProviderRegistry._containers` idem** — sem TTL, e *ignora* `primary_provider`/`fallback_order` em chamadas subsequentes (documentado no docstring, mas surpresa para devs novos) | `llm_factory.py:289, 297–347` | 🟠 Média | Mesma solução que G5; expor `force_refresh=True` nos call-sites que precisam. |
| G7 | **Duplicação `tenant_llm_context` ↔ `ProviderContainer`** — ambas as estruturas mantêm config por tenant; `_tenant_configs` é dict pelado, `_containers` é dict de containers | `tenant_llm_context.py:33` + `llm_factory.py:289` | 🟡 Baixa | Unificar: container deveria ler config do mesmo objeto que `tenant_llm_context.get_tenant_llm_config` retorna, sem cache paralelo. |
| G8 | **Ausência de OpenRouter/Mistral/Groq/Bedrock/Azure** | n/a (estrutural) | 🟡 Baixa (P2 do produto) | Ver §11 (OpenRouter recomendado para *teste*; Bedrock/Azure quando entrarmos em clientes regulados). |
| G9 | **Fallback silencioso para chave-do-sistema** quando `company_id` não está setado | `llm_factory.py:101, 144–149` | 🔴 Alta (LGPD/billing) | Falhar fechado por padrão; permitir chave-do-sistema só com feature flag explícita (`ALLOW_SYSTEM_KEY_FALLBACK`). Hoje tenant sem key gera custo na conta da plataforma sem notificação. |
| G10 | **`get_llm(tier="fast")` chamado mas inexistente** em `wsi_compact_pipeline.py:112–113` — quebra em runtime | `app/services/wsi_compact_pipeline.py:112` | 🔴 Alta | Bug. Trocar por `container = await get_provider_for_tenant_from_db(company_id); text = await container.generate_with_fallback(prompt)`. |
| G11 | **Embedding fallback Gemini ↔ OpenAI silencioso** invalida o índice pgvector | `embedding_factory.py:96–144` | 🔴 Alta | Falhar fechado quando provider primário falhar e o índice já contém vetores do primário. Considerar marcar o vetor com `provider`/`model` na row. |
| G12 | **Métricas Prometheus desabilitadas** (`_METRICS_AVAILABLE = False` em `llm_claude.py:22`) — perdemos observabilidade de latência por provider | `llm_claude.py:22` | 🟡 Baixa | Re-habilitar após auditar dependências; considerar OpenTelemetry uniforme em vez de Prometheus puro. |
| G13 | **Catálogo de modelos hardcoded** em `/admin/llm-config/providers` | `app/api/v1/llm_config.py:303–331` | 🟡 Baixa | Mover para tabela `llm_models_catalog` ou para um YAML versionado, atualizável sem deploy. |
| G14 | **`generate_with_tools` ignora `routing` por purpose** — quem chama escolhe o provider; routing.tools nunca é consultado | `llm.py:409–444` | 🟡 Baixa | Adicionar parâmetro `purpose=` e consultar `routing[purpose]`. |
| G15 | **`LLMCascadeRouter` deriva provider do nome do modelo** — frágil para nomes não-padronizados (e.g. modelos OpenRouter) | `llm_cascade.py:204–217` | 🟡 Baixa | Tornar provider explícito no input em vez de inferir de string. |

---

## 11. OpenRouter para testes

### 11.1 O que é

[OpenRouter.ai](https://openrouter.ai) é um **proxy unificado** sobre 100+ modelos de LLM (OpenAI, Anthropic, Google, Mistral, Llama, DeepSeek, Qwen, etc.). Uma única chave + uma única API (`POST /api/v1/chat/completions`, compatível com schema OpenAI) dá acesso a todos. Faturamento agregado, com markup pequeno (~5%) sobre o custo do provider.

### 11.2 Vantagens (no contexto LIA)

- **Comparação rápida**: trocar Gemini por GPT-4o por Llama-3 sem mexer em `LLMProviderFactory`.
- **Acesso a modelos não suportados**: Mistral Large, DeepSeek-Coder, Qwen 72B sem implementar SDK próprio.
- **Fallback agregado**: o próprio OpenRouter tem fallback entre data-centers do mesmo modelo.
- **Custo predizível por tenant** durante experimentação (não precisa configurar 4 contas separadas).

### 11.3 Desvantagens

- **Privacidade/LGPD**: requests passam por servidor de terceiro nos EUA. Para clientes em regime LGPD estrito ou para dados de candidatos, **isso é um problema contratual** — DPAs precisam ser revistos.
- **Latência extra**: +50–150ms por chamada (proxy hop adicional, geralmente em IAD ou SFO).
- **Markup**: ~5% sobre o preço do provider; nada catastrófico, mas em escala (>10M req/mês) faz diferença.
- **Disponibilidade**: introduzimos um SPOF — se OpenRouter cai, todos os tenants que usam OpenRouter caem juntos.
- **Falta de prompt caching nativo do Anthropic**: o cache do Claude não funciona via OpenRouter (perdemos ~50% de economia em WSI).

### 11.4 Esforço para plugar na factory

Estimado: **~1.5 a 2 dias** (1 engenheiro Sr).

1. Criar `app/shared/providers/llm_openrouter.py` (~200 linhas) implementando `LLMProviderABC` com `httpx.AsyncClient` apontando para `https://openrouter.ai/api/v1`.
2. Registrar via `LLMProviderFactory.register(OpenRouterLLMProvider)` em `app/main.py`.
3. Adicionar `"openrouter"` em `FALLBACK_ORDER` ou em `ProviderContainer.fallback_order` por tenant.
4. Atualizar `llm_config.py:303–331` para incluir `openrouter` no catálogo, com lista de modelos populares.
5. Atualizar `_provider_for_model()` em `llm_cascade.py` se quisermos usar nomes prefixados (ex.: `openrouter/anthropic/claude-3.5-sonnet`).
6. Adicionar feature flag `LLM_OPENROUTER_ENABLED=true` no env.
7. Pelo menos 4 testes: happy path, retry, circuit breaker, schema de tool use.

### 11.5 Recomendação final

> **Sim, condicional**: usar OpenRouter exclusivamente em **ambientes de staging/teste e A/B internos**, **nunca em produção com dados de candidatos reais**.

Critérios para uso:

- ✅ **OK**: comparar qualidade de novos modelos (Mistral, Llama, DeepSeek) antes de implementar SDK próprio.
- ✅ **OK**: testes de carga / chaos com modelos baratos sem encher conta de produção.
- ✅ **OK**: A/B test de prompt em modelos diferentes para o time de IA.
- ❌ **NÃO**: tráfego de produção contendo PII de candidatos (LGPD).
- ❌ **NÃO**: substituir Anthropic direct (perdemos prompt caching).
- ❌ **NÃO**: caminho crítico (chat principal, WSI F11).

Para clientes Enterprise em regime LGPD, manter providers diretos (Gemini/Claude/OpenAI) com BYOK.

---

## 12. Padrões de mercado e melhores práticas

| Padrão | LIA hoje | Mercado | Status |
|---|---|---|---|
| **Unified completion API** | `LLMProviderABC` com 4 métodos | LiteLLM (proxy unificado), Vercel AI SDK | ✅ Alinhado, escopo menor |
| **Circuit breaker por provider** | `circuit_breaker_decorator` em cada SDK call | Hystrix, resilience4j | ✅ Alinhado |
| **Token budget per-request** | `check_request_budget_before_llm` | Portkey, Helicone | ✅ Alinhado (raro!) |
| **Audit logging** | `audit_service.log_decision` por chamada | Helicone, Langfuse | ✅ Funcional, formato custom (não OTel) |
| **PII masking pré-LLM** | `strip_pii_for_llm_prompt` em todos os entry-points | Microsoft Presidio, regex DLP | ✅ Alinhado |
| **Prompt caching** | ❌ não usado | Anthropic native (50% off em prompts repetidos), OpenAI implicit | 🟠 Atrás — implementar para WSI |
| **Semantic cache** | `VectorSemanticCache` (pgvector) | GPTCache, Redis VL | ✅ Alinhado |
| **Cascada de custo (router)** | `LLMCascadeRouter` Flash→Sonnet→Opus | LangChain RouterChain, RouteLLM (Lepton) | ✅ Alinhado |
| **Per-tenant BYOK** | `tenant_llm_configs` + `ProviderContainer` | Portkey, OpenRouter (consumer-side) | ✅ Alinhado |
| **Streaming uniforme** | ❌ ABC não tem `stream()` | LangChain `astream`, OpenAI SSE, Anthropic stream | 🟠 Atrás |
| **Function calling unificado** | parcial (3 SDKs com schemas diferentes) | LiteLLM `tools`, Vercel `streamObject` | 🟠 Atrás (cobertura básica) |
| **Multimodal genérico** | só Gemini tem caminho dedicado | OpenAI Responses API, Anthropic Vision, Gemini multimodal nativo | 🔴 Atrás |
| **Observabilidade (traces/metrics)** | LangSmith opcional + logs estruturados | Langfuse, Phoenix Arize, OTel | 🟠 Híbrido — falta padrão único |

### 12.1 Principais recomendações para o time Rails

1. **Não implementar `LLMService` legado**. Já nasce gambiarra. Use só `ProviderContainer`-equivalente.
2. **Tornar `routing[purpose]` contrato de primeiro nível** desde o dia 1.
3. **Adotar OTel** (`semconv/gen-ai`) para traces — formato padrão da indústria, melhor que custom logs.
4. **Implementar Anthropic prompt caching** desde o início para WSI — economia direta de 30–50% em F2/F6/F11.
5. **Falhar fechado** quando não houver `company_id` setado, em vez de cair em chave-do-sistema.
6. **Versionar prompts** com hash + golden dataset; rodar regression a cada PR que mexe em prompt.
7. **Considerar LiteLLM como base** se a equipe Rails tem proficiência Python — pode ser exposto via gRPC ou rodado como sidecar; reduz código novo significativamente.

---

## 13. Apêndices

### 13.1 Tabela de arquivos relevantes

| Arquivo | Responsabilidade |
|---|---|
| `app/shared/providers/llm_provider.py` | ABC + dataclasses (`LLMResponse`, `LLMToolCall`, `LLMToolResponse`) |
| `app/shared/providers/llm_factory.py` | `LLMProviderFactory`, `ProviderContainer`, `TenantProviderRegistry`, helpers |
| `app/shared/providers/llm_gemini.py` | Provider Gemini (google.genai) |
| `app/shared/providers/llm_claude.py` | Provider Claude (anthropic SDK) |
| `app/shared/providers/llm_openai.py` | Provider OpenAI (openai SDK) |
| `app/shared/providers/embedding_factory.py` | Factory paralela para embeddings |
| `app/shared/tenant_llm_context.py` | contextvar `_current_company_id` + cache `_tenant_configs` + helpers para Gemini/Claude por tenant |
| `app/domains/ai/services/llm.py` | `LLMService` legado — em deprecação |
| `app/domains/ai/repositories/llm_config_repository.py` | CRUD com Fernet encrypt/decrypt |
| `app/api/v1/llm_config.py` | Endpoints `/admin/llm-config` (GET/PUT/test/providers) |
| `app/orchestrator/llm_cascade.py` | `LLMCascadeRouter` (Flash→Sonnet→Opus) |
| `app/orchestrator/cascaded_router.py` | `CascadedRouter` 8-tier (memory→redis→vector→fast→LLM→ReAct→clarification) |
| `app/orchestrator/main_orchestrator.py` | Entry point unificado para chat/agentes |
| `app/domains/job_creation/services/wsi_question_generator.py` | WSI F2/F3/F6 (BigFive + ranking + perguntas) |
| `app/services/wsi_compact_pipeline.py` | WSI Compact para talent pools (3–5 perguntas) |
| `app/api/v1/wsi/reports.py` | F11 (parecer) e CBI |
| `app/domains/job_creation/services/jd_enrichment.py` | F1 (enriquecimento de JD) |
| `app/shared/intelligence/semantic_search_service.py` | Busca semântica + expansão de termos |
| `app/domains/pipeline/agents/pipeline_feedback_tool.py` | Geração de feedback ao candidato (Gate 1/2) |
| `app/domains/pipeline/agents/pipeline_transition_agent.py` | Agente de transição de pipeline |
| `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base de todos os agentes ReAct (com bypass §G1) |
| `libs/models/lia_models/tenant_llm_config.py` | Schema SQLAlchemy de `tenant_llm_configs` |
| `plataforma-lia/src/components/settings/IntegrationsHub.tsx` | UI Configurações → Integrações |
| `plataforma-lia/src/components/settings/integrations/ApiKeyConfigForm.tsx` | Form BYOK |

### 13.2 Exemplo de payload `/admin/llm-config`

**GET response (chaves mascaradas)**:
```json
{
  "company_id": "acme-corp-uuid",
  "primary_provider": "claude",
  "fallback_order": ["claude", "gemini", "openai"],
  "providers": {
    "claude": {
      "api_key": "sk-ant-a...x4Y9",
      "model": "claude-sonnet-4-6",
      "is_active": true
    },
    "gemini": {
      "api_key": "AIza1234...wxyz",
      "model": "gemini-2.5-flash",
      "is_active": true
    }
  },
  "routing": {
    "chat": "claude",
    "embedding": "gemini",
    "screening": "claude",
    "voice": "gemini",
    "fallback": "openai"
  },
  "is_active": true
}
```

**PUT request (atualizar primary + adicionar OpenAI)**:
```json
{
  "primary_provider": "claude",
  "fallback_order": ["claude", "openai", "gemini"],
  "providers": {
    "openai": {
      "provider": "openai",
      "api_key": "sk-proj-realkey-here",
      "model": "gpt-4o",
      "is_active": true
    },
    "claude": {
      "provider": "claude",
      "api_key": "sk-ant-a...x4Y9",
      "model": "claude-sonnet-4-6",
      "is_active": true
    }
  },
  "routing": {
    "chat": "claude",
    "embedding": "gemini",
    "screening": "claude",
    "voice": "gemini",
    "fallback": "openai"
  }
}
```

> Note o `...` no `claude.api_key` — o backend preserva a chave existente nesse caso (merge semântico, `llm_config.py:160–168`).

### 13.3 Schema da tabela `tenant_llm_configs`

```sql
CREATE TABLE tenant_llm_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id VARCHAR(255) NOT NULL UNIQUE,
  primary_provider VARCHAR(50) DEFAULT 'gemini',
  fallback_order JSONB DEFAULT '["gemini","claude","openai"]',
  providers JSONB DEFAULT '{}',  -- api_keys cifradas com Fernet
  routing JSONB DEFAULT '{}',
  config JSONB DEFAULT '{}',     -- futuro: settings avançadas
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  created_by VARCHAR(255)
);
CREATE INDEX idx_tenant_llm_configs_company ON tenant_llm_configs(company_id);
```

### 13.4 Checklist para o time Rails replicar a factory

- [ ] Definir `LlmProviderInterface` (Ruby module com `generate`, `generate_with_system`, `generate_with_tools`, `generate_structured`).
- [ ] Implementar 3 providers: `GeminiProvider`, `ClaudeProvider`, `OpenaiProvider` (com Faraday + circuit breaker via `Stoplight` ou similar).
- [ ] Schema `TenantLlmConfig` com colunas equivalentes; usar `attr_encrypted` ou `lockbox` para `providers` (campos JSONB com `api_key`).
- [ ] Service `LlmFactory.for(company_id)` retornando container thread-safe (`Concurrent::Map`).
- [ ] `LlmFactory.for(company_id).generate_with_fallback(prompt:, system:, purpose:)` — sempre receber `purpose` (chat / screening / wsi / embedding / feedback) e consultar `routing[purpose]`.
- [ ] Middleware Rails que popula `Current.company_id` (equivalente ao `contextvar` do FastAPI).
- [ ] Endpoint `GET/PUT /admin/llm_config` espelhando schema atual.
- [ ] Endpoint `POST /admin/llm_config/test` que **use a factory**, não SDK direto (não repetir gap §G2).
- [ ] Pré-LLM: PII masking + token budget check + audit log (3 concerns separadas, encadeadas).
- [ ] Falhar fechado quando `Current.company_id` for `nil` (gap §G9).
- [ ] Cache `TTLCache(maxsize: 2000, ttl: 5.minutes)` para `tenant_configs` — não usar `Hash` puro (gap §G5).
- [ ] Suporte a streaming via `Enumerator::Lazy` ou Rack Hijack para SSE.
- [ ] OTel/Langfuse para traces; emitir spans `gen_ai.completion` com `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.*`.
- [ ] Versionamento de prompts com hash + golden dataset rodado em CI.
- [ ] Anthropic prompt caching habilitado para WSI prompts (system + few-shots cacheados).

### 13.5 Referências bibliográficas

1. LMSys — *Chatbot Arena Leaderboard* — https://chat.lmsys.org/?leaderboard
2. Hugging Face — *MTEB Leaderboard* — https://huggingface.co/spaces/mteb/leaderboard
3. UC Berkeley — *Berkeley Function-Calling Leaderboard v3* — https://gorilla.cs.berkeley.edu/leaderboard.html
4. Anthropic — *Prompt caching docs* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
5. OpenAI — *Function calling guide* — https://platform.openai.com/docs/guides/function-calling
6. Google DeepMind — *Gemini 2.5 technical report* (2026) — https://deepmind.google/technologies/gemini/
7. LiteLLM — *Unified API for LLMs* — https://github.com/BerriAI/litellm
8. OpenRouter — *Docs and pricing* — https://openrouter.ai/docs
9. OpenTelemetry — *GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
10. Langfuse — *LLM observability* — https://langfuse.com/docs

---

**Fim do documento.** Dúvidas de arquitetura: alinhe com o tech-lead da LIA antes de divergir do contrato `LLMProviderABC` na re-implementação Rails — ele é o ponto de costura que mantém WSI, embeddings, voice e chat compatíveis entre back-ends.
