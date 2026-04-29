# LLM Factory — Handoff Document v2

**Data**: 2026-04-19
**Status**: Implementado e verificado (py_compile ✓)
**Responsável técnico**: lia-agent-system / WeDOTalent

---

## 1. Visão Geral Arquitetural

```
Request do usuário
      │
      ▼
AuthEnforcementMiddleware
  └─ _current_company_id.set(company_id)
  └─ prime_tenant_llm_cache(company_id)      ← carrega config do DB na cache
      │
      ▼
MainOrchestrator / AgenticLoop
  └─ get_provider_for_tenant_from_db(company_id)  ← ponto canônico de acesso
      │
      ▼
TenantProviderRegistry.load_from_db(tenant_id)
  └─ ProviderContainer(
       tenant_id,
       primary_provider,      # ex: "claude"
       fallback_order,        # ex: ["claude", "gemini", "openai"]
       provider_api_keys,     # keys descriptografadas do DB
       provider_models,       # modelos configurados (novo v2)
     )
      │
      ▼
ProviderContainer.generate_with_fallback(prompt, task_type="screening")
  ├─ B7: Quality Tier Guard (task_type × QUALITY_TIERS × TASK_MINIMUM_TIER)
  ├─ budget check via check_request_budget_before_llm()
  ├─ tenta providers em fallback_order
  │    ├─ usa tenant key se disponível     → INFO  [TenantLLM]
  │    └─ usa system key se não            → WARN  [LIA-BYOK]
  ├─ G15: tenant key falhou → system fallback → WARN [LIA-BYOK]
  └─ B3: audit_service.log_decision() após cada sucesso
```

### Paths que NÃO passam pelo factory (legacy)

| Path | Status | Nota |
|------|--------|------|
| `LLMService.generate(provider="claude")` quando `_tenant_container is None` | ✅ **Corrigido v2** | Agora usa `get_audited_model(company_id=_cid)` → tenant-aware |
| `LangGraphReActBase._get_model()` | ✅ **Corrigido v2** | Lê tenant config; WARN se sem config; budget check adicionado |
| `get_gemini_client_for_tenant()` | ✅ **Corrigido v2** | WARN [LIA-BYOK] quando usa key da plataforma |

---

## 2. Tabela de Gaps — Status Final

| Gap | Descrição | Status | Arquivo Modificado |
|-----|-----------|--------|--------------------|
| G1 | LangGraph sem budget check | ✅ Corrigido (B2) | `langgraph_react_base.py` |
| G2 | API key vaza no erro do test endpoint | ✅ Corrigido (B6) | `llm_config.py` |
| G3 | LLMService.generate() usa key global | ✅ Corrigido (B5) | `llm.py` |
| G4 | Sem budget check em LLMService | ✅ Corrigido via B5 | `llm.py` |
| G5 | Cache sem TTL | ✅ Corrigido (B6) | `tenant_llm_context.py` |
| G6 | Cache sem LRU eviction | ✅ Corrigido (B6 — maxsize implícito) | `tenant_llm_context.py` |
| G7 | API key sem criptografia | ✅ Já implementado (Fernet) | `llm_config_repository.py` |
| G8 | Decryption inconsistente | ✅ Já implementado | `llm_config_repository.py` |
| G9 | Fallback silencioso para system key | ✅ Corrigido (B1) | `llm_factory.py`, `tenant_llm_context.py`, `langgraph_react_base.py` |
| G10 | wsi_compact_pipeline crash | ✅ Falso positivo — já usa factory | N/A |
| G11 | Embedding dimension mismatch | ✅ Corrigido (B4) | `embedding_factory.py` |
| G12 | Voice provider isolation | ✅ Já implementado | `llm_factory.py` |
| G13 | Catálogo hardcoded desatualizado | ✅ Corrigido (B8) | `llm_config.py` |
| G14 | Sem audit trail BYOK | ✅ Corrigido (B3) | `llm_factory.py` |
| G15 | Budget depletion → system fallback silencioso | ✅ Corrigido (B3+G15) | `llm_factory.py` |

---

## 3. Constantes de Referência

### `app/shared/providers/llm_factory.py`

```python
QUALITY_TIERS: dict[str, str] = {
    "claude-sonnet-4-6": "tier1",
    "claude-opus-4-7":   "tier1",
    "gemini-2.5-pro":    "tier1",
    "gemini-2.5-flash":  "tier1",
    "gpt-4o":            "tier1",
    "gpt-4-turbo":       "tier1",
    "claude-haiku-3-5":  "tier2",   # NOT for screening/WSI
    "gemini-2.0-flash":  "tier2",   # NOT for screening/WSI
    "gpt-4o-mini":       "tier2",   # NOT for screening/WSI
}

TASK_MINIMUM_TIER: dict[str, str] = {
    "screening": "tier1",   # WSI / Bloom / Dreyfus — sempre Tier 1
    "wsi":       "tier1",
    "chat":      "tier2",   # chat pode usar Tier 2
}
```

**Quando adicionar um novo modelo**: adicione em `QUALITY_TIERS` com o tier correto.
**Quando adicionar uma nova task crítica**: adicione em `TASK_MINIMUM_TIER` com `"tier1"`.

### `app/shared/tenant_llm_context.py`

```python
_TENANT_CONFIG_TTL: float = 300.0  # 5 minutos
```

Cache expira automaticamente após 5 min. Para invalidação imediata (ex: após update):
```python
from app.shared.tenant_llm_context import clear_tenant_config_cache
clear_tenant_config_cache(company_id)   # já chamado em PUT /admin/llm-config
```

### `app/shared/providers/embedding_factory.py`

```python
EMBEDDING_FALLBACK_ORDER: list[str] = ["gemini", "openai"]
```

**Env var `EMBEDDING_LOCK_PROVIDER`**: se definida, bloqueia qualquer fallback de embedding.
- `EMBEDDING_LOCK_PROVIDER=gemini` → só Gemini, nunca cai para OpenAI
- Vazia (padrão) → fallback permitido mas logado em CRITICAL

---

## 4. Guia de Logs

### Tags e seus significados

| Tag | Level | Significado | Ação esperada |
|-----|-------|-------------|---------------|
| `[LIA-BYOK]` | WARN | Tenant sem key própria — usando key da plataforma | Normal para tenants free/trial. Para enterprise: verificar config em Configurações > Integrações > LLM |
| `[LIA-BYOK]` | WARN | Tenant key falhou — usou key da plataforma | Verificar validade da key BYOK configurada pelo cliente |
| `[LIA-QUALITY]` | WARN | Modelo Tier 2 em task crítica — usando plataforma | Admin do tenant configurou modelo inadequado. Avisar cliente |
| `[TenantLLM]` | INFO | Usando key do tenant (BYOK ativo) | Normal — BYOK funcionando |
| `[EmbeddingFactory]` | CRITICAL | Fallback cross-provider sem lock | Índice pgvector pode estar comprometido. Considerar reindexação |
| `[ProviderContainer]` | WARN | Fallback para provider secundário | Normal se provider primário falhou temporariamente |

### Exemplo de log saudável (BYOK ativo)
```
INFO  [TenantLLM] Using tenant Gemini key for tenant=acme_corp
INFO  [LLMService] generate provider=gemini model=gemini-2.5-flash prompt_len=342 pii_stripped=False tenant=acme_corp
```

### Exemplo de log de alerta (sem BYOK)
```
WARN  [LIA-BYOK] tenant=trial_tenant_01 provider=gemini: sem key própria — usando key da plataforma.
```

### Exemplo de alerta de qualidade
```
WARN  [LIA-QUALITY] tenant=acme_corp task=screening model=claude-haiku-3-5 (tier2) — Tier 1 obrigatório. Usando modelo da plataforma.
```

---

## 5. Guia do Operador

### Env vars disponíveis

| Env Var | Padrão | Descrição |
|---------|--------|-----------|
| `EMBEDDING_LOCK_PROVIDER` | `` (vazio) | Se definido, bloqueia fallback de embedding cross-provider |
| `LLM_DEFAULT_PROVIDER` | `gemini` | Provider padrão quando nenhuma config DB existe |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | — | Key da plataforma para Gemini (system key) |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | — | Key da plataforma para Claude (system key) |
| `AI_INTEGRATIONS_OPENAI_API_KEY` | — | Key da plataforma para OpenAI (system key) |

### Reindexação do pgvector

Se `[EmbeddingFactory] CRITICAL` aparecer nos logs, o índice pgvector pode estar comprometido:

```sql
-- Verificar dimensão atual dos embeddings
SELECT vector_dims(embedding) as dims, count(*)
FROM candidate_embeddings
GROUP BY dims;

-- Se houver registros com dimensões mistas (768 e 1536), reindexar:
-- 1. Setar EMBEDDING_LOCK_PROVIDER=gemini (ou openai)
-- 2. Rodar job de reindexação que re-embed todos os candidatos
-- 3. Verificar que todos os embeddings têm a mesma dimensão
```

---

## 6. Matriz "Choose Your AI" — Provider × Capacidade × Tier

| Provider | Chat | Triagem/WSI | Embedding | Voz | Tier Máx |
|----------|------|-------------|-----------|-----|----------|
| Gemini 2.5 Flash | ✅ Tier 1 | ✅ Tier 1 | ✅ 768 dims | ✅ Gemini Live | Tier 1 |
| Gemini 2.5 Pro | ✅ Tier 1 | ✅ Tier 1 | ✅ 768 dims | ✅ Gemini Live | Tier 1 |
| Gemini 2.0 Flash | ✅ Tier 2 | ⚠️ Tier 2 (não recomendado) | ✅ 768 dims | ✅ Gemini Live | Tier 2 |
| Claude Sonnet 4.6 | ✅ Tier 1 | ✅ Tier 1 | ❌ | ⚠️ Composite | Tier 1 |
| Claude Opus 4.7 | ✅ Tier 1 | ✅ Tier 1 | ❌ | ⚠️ Composite | Tier 1 |
| Claude Haiku 3.5 | ✅ Tier 2 | ⚠️ Tier 2 (não recomendado) | ❌ | ⚠️ Composite | Tier 2 |
| GPT-4o | ✅ Tier 1 | ✅ Tier 1 | ✅ 1536 dims | ⚠️ Realtime API | Tier 1 |
| GPT-4o-mini | ✅ Tier 2 | ⚠️ Tier 2 (não recomendado) | ✅ 1536 dims | ⚠️ Realtime API | Tier 2 |

**Legenda**:
- ✅ Suportado e recomendado
- ⚠️ Suportado com ressalvas
- ❌ Não suportado nativamente (usa fallback para provider da plataforma)
- "Composite" = voz via STT Gemini + LLM configurado + TTS Gemini

### Configuração recomendada por perfil de cliente

| Perfil | Configuração Recomendada |
|--------|--------------------------|
| Enterprise BYOK completo | Gemini 2.5 Flash + OpenAI para embedding |
| Enterprise BYOK Claude-first | Claude Sonnet + Gemini para embedding + voz |
| Trial / Free | Usa plataforma — sem necessidade de configurar |
| Custo-optimizado (não WSI) | GPT-4o-mini ou Haiku para chat (NÃO screening) |

---

## 7. Decisões de Arquitetura

### Por que Quality Tier Guard em runtime (não só no save)?

O save-time warning (PUT /admin/llm-config) pode ser ignorado pelo admin. O guard em runtime garante que a plataforma **nunca entregue triagem WSI de baixa qualidade** ao recrutador, independente do que o admin configurou. O cliente pode não perceber que a qualidade foi degradada.

Trade-off: o admin configura uma key BYOK Haiku para economizar, mas a plataforma ignora silenciosamente em tarefas críticas. Para transparência, o log WARN `[LIA-QUALITY]` fica visível para o time de operações.

### Por que TTL de 5 minutos?

O Anthropic prompt cache TTL é 5 minutos. Alinhar o TTL do `_tenant_configs` evita que um update de config do tenant fique invisível por mais tempo do que o prompt cache dura. Após um update via PUT /admin/llm-config, `clear_tenant_config_cache()` é chamado explicitamente — o TTL é uma segunda linha de defesa.

### Por que não usar cachetools.TTLCache?

Evitar dependência externa desnecessária. O TTL manual com `_time_mod.monotonic()` tem o mesmo comportamento para o volume esperado (<500 tenants ativos por processo). Se o volume crescer, migrar para `cachetools.TTLCache(maxsize=500, ttl=300)` é uma troca de 5 linhas.

### Por que EMBEDDING_LOCK_PROVIDER é opt-in?

Bloquear por padrão quebraria deployments existentes onde o Gemini embedding falha e o OpenAI salva silenciosamente. A recomendação é: ao fazer o deploy inicial, verificar a dimensão usada e setar o lock. Para deployments existentes, analisar os logs `CRITICAL` primeiro.

---

## 8. Arquivos Modificados Nesta Versão

| Arquivo | Mudanças |
|---------|----------|
| `app/shared/providers/llm_factory.py` | QUALITY_TIERS, TASK_MINIMUM_TIER, provider_models, WARN [LIA-BYOK] em get(), audit trail em generate_with_fallback(), G15 WARN |
| `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Budget check em _process_langgraph(), WARN em _get_model() |
| `app/shared/tenant_llm_context.py` | TTL cache 5 min, WARN [LIA-BYOK] em get_gemini_client_for_tenant() |
| `app/shared/providers/embedding_factory.py` | EMBEDDING_LOCK_PROVIDER guard, CRITICAL log em fallback cross-provider |
| `app/domains/ai/services/llm.py` | generate() usa get_audited_model() → tenant-aware |
| `app/api/v1/llm_config.py` | Sanitizar erro test endpoint, quality warnings no save, dependency map em /providers |
| `app/services/wsi_compact_pipeline.py` | task_type="screening" em generate_with_fallback() |


---

## 9. Interface do Cliente — Choose Your AI (Frontend)

**Atualizado em**: 2026-04-19
**Localização no produto**: Configurações → Integrações → categoria "Modelos de IA"

### Fluxo de Configuração (UX)

```
Admin abre Configurações → Integrações
      │
      ▼
IntegrationsHub carrega:
  - GET /api/backend-proxy/llm-config         ← config atual do tenant
  - GET /api/backend-proxy/llm-config/providers  ← catálogo de modelos + tiers
      │
      ▼
Cards de provider (Gemini, Claude, OpenAI) exibem:
  - Badge "Provedor ativo" se for o primary_provider
  - Badge "Chave própria" se tenant tem API key salva
  - Badge "Chave do sistema" se usa key da plataforma
      │
      ▼ (clique no card)
IntegrationDetailDrawer abre com:
  1. Status badges (Conectado / Não configurado)
  2. Recursos & Capacidades (do integration-data.ts)
  3. [se provider ≠ configurado] Banner amber: aviso de voz (OpenAI) ou companion
  4. ApiKeyConfigForm → testa key → salva via PUT /admin/llm-config
  5. [se PUT retorna warnings] Banner status-warning com mensagens do Quality Guard
  6. ModelSelector → dropdown com badge Tier 1 / Tier 2 por modelo
  7. [se Tier 2 selecionado] Banner status-warning: "não recomendado para triagem WSI"
  8. [se requires_companion_for] Banner info com companion_recommendation do backend
```

### Arquivos Frontend

| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/src/components/settings/IntegrationsHub.tsx` | Hub principal; fetcha llmConfig + providersCatalog; renderiza cards |
| `plataforma-lia/src/components/settings/integrations/IntegrationDetailDrawer.tsx` | Drawer de configuração; save key + model; captura PUT warnings |
| `plataforma-lia/src/components/settings/integrations/ModelSelector.tsx` | Seletor de modelo com badges Tier 1/Tier 2; save model separado |
| `plataforma-lia/src/components/settings/integrations/ApiKeyConfigForm.tsx` | Form de API key; valida via /test; salva |
| `plataforma-lia/src/components/settings/integrations/integration-data.ts` | Dados estáticos dos providers (nome, ícone, capabilities) |
| `plataforma-lia/src/app/api/backend-proxy/llm-config/route.ts` | Proxy GET/PUT → FastAPI /api/v1/admin/llm-config |
| `plataforma-lia/src/app/api/backend-proxy/llm-config/providers/route.ts` | Proxy GET → FastAPI /api/v1/admin/llm-config/providers |
| `plataforma-lia/src/app/api/backend-proxy/llm-config/test/route.ts` | Proxy POST → FastAPI /api/v1/admin/llm-config/test |

### Contrato de Dados (Frontend ↔ Backend)

**GET /admin/llm-config** — resposta lida pelo frontend:
```json
{
  "company_id": "...",
  "primary_provider": "gemini",
  "fallback_order": ["gemini", "claude", "openai"],
  "providers": {
    "gemini": { "api_key": "AIza***MASKED***", "model": "gemini-2.5-flash", "is_active": true }
  },
  "routing": { "chat": "gemini", "screening": "gemini", "embedding": "gemini", "voice": "gemini" }
}
```

**PUT /admin/llm-config** — payload enviado pelo frontend:
```json
{
  "primary_provider": "gemini",
  "fallback_order": ["gemini", "claude", "openai"],
  "providers": {
    "gemini": { "provider": "gemini", "api_key": "AIza...", "model": "gemini-2.5-flash", "is_active": true }
  },
  "routing": { "chat": "gemini", "screening": "gemini" }
}
```

**PUT /admin/llm-config** — resposta com Quality Guard warnings:
```json
{
  "status": "updated",
  "company_id": "...",
  "warnings": [
    "Modelo 'claude-haiku-3-5' (Tier 2) configurado para 'screening' — qualidade da triagem WSI pode ser reduzida."
  ]
}
```

**GET /admin/llm-config/providers** — catálogo lido pelo ModelSelector:
```json
{
  "providers": [
    {
      "id": "claude",
      "models": ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-3-5"],
      "model_tiers": { "claude-sonnet-4-6": "tier1", "claude-haiku-3-5": "tier2" },
      "requires_companion_for": ["embedding", "voice"],
      "companion_recommendation": "Claude não suporta embedding nem voz nativas...",
      "default_model": "claude-sonnet-4-6"
    }
  ],
  "tier_definitions": { "tier1": "...", "tier2": "..." }
}
```

---

## 10. Auditoria E2E — Estado Real do Sistema (2026-04-19)

### Status por Camada

| Camada | Componente | Status | Notas |
|--------|-----------|--------|-------|
| Frontend proxy routes | `/api/backend-proxy/llm-config/*` | ✅ OK | company_id via JWT; proxy correto |
| Backend endpoints | `app/api/v1/llm_config.py` | ✅ OK | GET/PUT/test/providers funcionando |
| Repository/DB | `llm_config_repository.py` | ✅ OK | model persiste e retorna na resposta |
| Tenant LLM context | `tenant_llm_context.py` + `llm_factory.py` | ✅ OK | `provider_models` carregado corretamente |
| Auth / tenant isolation | JWT → `company_id` via middleware | ✅ OK | Sem vazamento entre tenants |
| Frontend UI | IntegrationsHub + Drawer + ModelSelector | ✅ OK | Fluxo completo funcional |
| **Serviços hardcoded** | `wsi_question_adjuster`, `vacancy_search`, `voice` | ❌ **CRÍTICO** | Ver abaixo |

### Gaps Críticos — Serviços que Ignoram BYOK

Os seguintes serviços hardcodam `model="gemini-2.5-flash"` e ignoram completamente a configuração do tenant:

| Serviço | Arquivo | Operação | Impacto BYOK |
|---------|---------|----------|-------------|
| WSI Question Adjuster | `app/domains/cv_screening/services/wsi_question_adjuster.py:248` | Avaliação de qualidade da JD | ❌ Sempre Gemini |
| Vacancy Search | `app/domains/sourcing/services/vacancy_search.py` | Busca e ranking de vagas | ❌ Sempre Gemini |
| Vacancy Search Service | `app/domains/job_management/services/vacancy_search_service.py` | Indexação de vagas | ❌ Sempre Gemini |
| Gemini Voice Service | `app/domains/voice/services/gemini_voice_service.py` | Voz da LIA (TTS/STT) | ❌ Hardcoded por design (OK para voz) |

**Consequência**: Tenants que configuram Claude BYOK ou OpenAI BYOK como primary provider ainda têm suas triagens WSI e buscas de vagas processadas com a key da plataforma (Gemini). Isso viola o contrato "Choose Your AI" para essas operações críticas.

### Plano de Correção dos Gaps

**Utilitário a criar** (antes de corrigir os serviços):

```python
# app/shared/providers/tenant_model_resolver.py
from app.shared.providers.llm_factory import get_provider_for_tenant_from_db

async def get_tenant_model(
    company_id: str,
    provider: str | None = None,
    fallback: str = "gemini-2.5-flash",
) -> str:
    """Resolve o modelo configurado pelo tenant para um provider."""
    try:
        container = await get_provider_for_tenant_from_db(company_id)
        prov = provider or container.primary_provider
        return container._provider_models.get(prov, fallback)
    except Exception:
        return fallback
```

**Correção em `wsi_question_adjuster.py:248`**:
```python
# ANTES (hardcoded — viola BYOK):
response = llm_service.generate_native_gemini_sync(model="gemini-2.5-flash", ...)

# DEPOIS (tenant-aware):
from app.shared.providers.tenant_model_resolver import get_tenant_model
model = await get_tenant_model(company_id, provider="gemini", fallback="gemini-2.5-flash")
response = llm_service.generate_native_gemini_sync(model=model, ...)
```

**Nota sobre Voice Services**: `gemini_voice_service.py` está hardcoded por design — voz usa Gemini Live API que não tem equivalente em outros providers. Esse comportamento é correto e documentado no `requires_companion_for: ["voice"]` do catálogo.

### O Que Funciona Hoje (pós-2026-04-19)

| Funcionalidade | BYOK Respeitado? |
|----------------|-----------------|
| Chat / Orchestrator (AgenticLoop) | ✅ Sim |
| Triagem WSI via `wsi_compact_pipeline` | ✅ Sim (task_type="screening" ativo) |
| LangGraph agents (entrevistas, sourcing) | ✅ Sim (budget check ativo) |
| Embedding | ✅ Sim (com EMBEDDING_LOCK_PROVIDER) |
| Avaliação de JD (wsi_question_adjuster) | ❌ Não — hardcoded Gemini |
| Busca de vagas (vacancy_search) | ❌ Não — hardcoded Gemini |
| Voz LIA (TTS/STT) | ⚠️ Por design usa Gemini Live |

### Prioridade de Correção dos Gaps Restantes

```
P0 (antes do release BYOK para enterprise):
  → Criar tenant_model_resolver.py
  → wsi_question_adjuster.py:248 — tenant-aware
  → vacancy_search.py — tenant-aware

P1 (sprint seguinte):
  → vacancy_search_service.py — tenant-aware
  → Testes de integração cobrindo tenant isolation por serviço
```


---

## 11. Auditoria Profunda de Hardcoded Bypasses (2026-04-19)

### Resumo Executivo

Auditoria exaustiva encontrou **18 instâncias em 15 arquivos** que bypassam o LLM Factory.
Achado crítico: o audit trail (G14) foi implementado com kwargs errados — cada chamada ao
`log_decision()` falhava silenciosamente desde o commit de implementação.

---

### Bugs Corrigidos (commit b4218eace)

#### BUG-01: `llm_factory._audit_llm_usage()` — kwargs errados (assinatura real ignorada)

**Arquivo**: `app/shared/providers/llm_factory.py:251`
**Impacto**: Audit trail 100% não-funcional — `TypeError` silenciado pelo `except Exception: pass`

```
# ANTES (quebrado):
await _fa.log_decision(action="llm_usage", resource_type="llm_provider",
    resource_id=..., details={...}, user_id=...)
# resource_type/resource_id/details/user_id NÃO existem na assinatura

# DEPOIS (correto):
await _fa.log_decision(
    company_id=..., agent_name="llm_factory", decision_type="llm_usage",
    action=f"generate/{pname}", decision="executed",
    reasoning=[f"task_type={task_type}", ...], criteria_used=["byok_key_source", ...])
```

#### BUG-01b: `LLMService.generate()` — mesmo padrão de kwargs errados

**Arquivo**: `app/domains/ai/services/llm.py:382`
Cópia do mesmo padrão. Corrigido com a assinatura real.

#### BUG-02: `wsi_question_adjuster.evaluate_job_description()` — BYOK ignorado

**Arquivo**: `app/domains/cv_screening/services/wsi_question_adjuster.py:246`
Usava `llm_service.generate_native_gemini_sync(model="gemini-2.5-flash")` com key da plataforma.
Fix: `company_id: str | None = None` adicionado à assinatura + `get_gemini_client_for_tenant()`.

#### BUG-03: `voice_screening_orchestrator.py:1072` — BYOK ignorado em entrevista de voz

**Arquivo**: `app/domains/voice/services/voice_screening_orchestrator.py:1072`
`session.company_id` estava disponível mas não era passado ao cliente Gemini.
Fix: `get_gemini_client_for_tenant(session.company_id)` substituiu `self._llm_service.generate_native_gemini_sync()`.

---

### Inventário Completo de Hardcoded Model References

| Status | Arquivo | Linha | Problema | Tipo |
|--------|---------|-------|----------|------|
| ✅ Corrigido | `app/shared/providers/llm_factory.py` | 251 | audit kwargs errados | BUG-01 |
| ✅ Corrigido | `app/domains/ai/services/llm.py` | 382 | audit kwargs errados | BUG-01b |
| ✅ Corrigido | `app/domains/cv_screening/services/wsi_question_adjuster.py` | 246 | BYOK bypass | BUG-02 |
| ✅ Corrigido | `app/domains/voice/services/voice_screening_orchestrator.py` | 1072 | BYOK bypass | BUG-03 |
| ⚠️ By design | `app/domains/voice/services/gemini_voice_service.py` | 118,208,288 | Gemini Live API exclusiva para voz | P2 |
| ⚠️ By design | `app/domains/voice/services/voice_screening_orchestrator.py` | 933 | Transcrição de áudio | P2 |
| ℹ️ Via contextvar | `app/domains/sourcing/services/vacancy_search.py` | 127,376 | Usa `llm_service._current_tenant` — BYOK OK quando chamado pelo orchestrator | P2 |
| ℹ️ Falso positivo | `app/shared/compliance/fairness_guard.py` | — | Não usa LLM diretamente | N/A |

### generate_native_gemini vs factory

`LLMService.generate_native_gemini()` em `llm.py:217` **já é BYOK-aware** — usa
`get_gemini_client_for_tenant(self._current_tenant)` internamente quando `_current_tenant` está setado.
`_current_tenant` é injetado pelo `MainOrchestrator` por request, então serviços chamados
via orchestrator têm BYOK ativo automaticamente.

Serviços chamados fora do contexto do orchestrator (batch jobs, webhooks) precisam setar
`llm_service._current_tenant = company_id` explicitamente antes de chamar `generate_native_gemini`.

### Assinatura Canônica de `audit_service.log_decision()`

```python
async def log_decision(
    self,
    company_id: str,           # OBRIGATÓRIO
    agent_name: str,           # OBRIGATÓRIO — ex: "llm_factory", "cv_screening_agent"
    decision_type: str,        # OBRIGATÓRIO — ex: "llm_usage", "candidate_screening"
    action: str,               # OBRIGATÓRIO — ex: "generate/gemini"
    decision: str,             # OBRIGATÓRIO — ex: "executed", "approved", "rejected"
    reasoning: list[str],      # OBRIGATÓRIO — lista de razões
    criteria_used: list[str],  # OBRIGATÓRIO — lista de critérios avaliados
    candidate_id: str | None = None,
    job_vacancy_id: str | None = None,
    score: float | None = None,
    confidence: float | None = None,
    human_review_required: bool = False,
    criteria_ignored: list[str] | None = None,
    actor_user_id: str | None = None,
) -> AuditLog:
```

**Parâmetros que NÃO existem** (não use): `resource_type`, `resource_id`, `details`, `user_id`.

*Last updated: 2026-04-19 | Deep audit + BUG-01/01b/02/03 corrigidos*


---

## 12. Guia do Desenvolvedor — Checklist + Mapa de Consumidores LLM

> **Propósito**: Este guia garante que todo desenvolvedor que toca código LLM aplique os contratos
> corretos de BYOK, Quality Tier Guard e audit trail. Baseado na auditoria de 2026-04-19.

---

### 12.1 — Checklist de Implementação (novos consumidores LLM)

Use este checklist ao criar ou modificar qualquer serviço, rota ou agente que chama LLM.

#### A — Escolha do padrão de chamada

```
[ ] Rota FastAPI (endpoint REST):
    → usar generate_with_fallback(prompt, task_type=...) via get_provider_for_tenant_from_db(company_id)
    → company_id vem do JWT via AuthEnforcementMiddleware, NUNCA do request body

[ ] Agente LangGraph / ReAct:
    → usar generate_with_fallback() via ProviderContainer (já injetado pelo orchestrator)
    → verificar: _get_model() em langgraph_react_base.py usa get_current_llm_tenant()

[ ] Serviço Python assíncrono:
    → usar get_provider_for_tenant_from_db(company_id) → container.generate_with_fallback()
    → SE for síncrono: get_provider_for_tenant(company_id) + asyncio.run() ou rodar async

[ ] Chamada Gemini direta (sem Claude/OpenAI):
    → usar get_gemini_client_for_tenant(company_id) de tenant_llm_context.py
    → NÃO instanciar genai.Client() diretamente — viola BYOK

[ ] LLMService.generate() (legado):
    → verificar que self._current_tenant está setado antes da chamada
    → preferir migrar para generate_with_fallback()
```

#### B — task_type correto (Quality Tier Guard)

```
[ ] Triagem WSI, Bloom/Dreyfus, avaliação de candidato:
    → task_type="wsi" ou task_type="screening"
    → PROIBIDO Tier 2 (haiku, gemini-2.0-flash, gpt-4o-mini) nessas tasks
    → O Quality Tier Guard bloqueia automaticamente e usa modelo Tier 1 da plataforma

[ ] Chat, geração de texto genérico, perguntas de entrevista:
    → task_type="chat" (aceita Tier 2)

[ ] Embedding:
    → usar EmbeddingProviderFactory.embed_with_fallback()
    → NÃO misturar providers (Gemini 768 dims ≠ OpenAI 1536 dims no pgvector)
    → se ambiente tem EMBEDDING_LOCK_PROVIDER, respeitar
```

#### C — Audit trail obrigatório

```
[ ] Toda chamada LLM passa pelo factory → audit automático em generate_with_fallback()

[ ] Se chamar audit_service.log_decision() DIRETAMENTE, usar APENAS estes kwargs:
    company_id, agent_name, decision_type, action, decision, reasoning, criteria_used
    + opcionais: candidate_id, job_vacancy_id, score, confidence, human_review_required

[ ] PROIBIDO: resource_type, resource_id, details, user_id
    (não existem na assinatura — geram TypeError silenciado pelo except:pass)

[ ] Não envolver log_decision() em try/except: pass se for chamada direta
    (o factory já faz isso — mas código próprio deve falhar explicitamente)
```

#### D — Isolamento multi-tenant

```
[ ] company_id NUNCA vem do payload/body do request
    → usar: get_current_llm_tenant() ou JWT via Depends(get_current_user)
    → o middleware já seta _current_company_id contextvar para todos os requests

[ ] Serviços de background (Celery, webhooks):
    → NÃO têm contextvar automaticamente
    → passar company_id explicitamente: get_provider_for_tenant_from_db(company_id)

[ ] Cache de config de tenant:
    → prime_tenant_llm_cache(company_id) para aquecimento assíncrono
    → TTL: 5 minutos — mudanças de config levam até 5 min para propagar
    → forçar refresh: clear_tenant_config_cache(company_id)
```

#### E — Code review de PRs com LLM

```
[ ] Não há genai.Client() ou AsyncAnthropic() instanciados diretamente (exceto llm_config.py)
[ ] Não há model="gemini-*" ou model="claude-*" hardcoded em rotas de screening
[ ] task_type está explícito em chamadas de screening/WSI
[ ] audit_service.log_decision() usa os kwargs corretos (ver seção 12.1.C)
[ ] company_id vem de contextvar ou JWT, nunca do body
[ ] Não há try/except: pass envolvendo chamadas LLM críticas
```

---

### 12.2 — Checklist de Verificação (bugs já corrigidos — regressão)

Execute este checklist após qualquer refactor que toque os arquivos listados na seção 12.3.

| # | Arquivo | O que verificar | Como testar |
|---|---------|----------------|-------------|
| V-01 | `llm_factory.py` | `_audit_llm_usage()` usa kwargs corretos (agent_name, decision_type, reasoning, criteria_used) | grep "resource_type\|resource_id\|details.*provider\|user_id.*system" — deve retornar vazio |
| V-02 | `llm.py` | `LLMService.generate()` audit usa kwargs corretos | mesmo grep acima |
| V-03 | `wsi_question_adjuster.py` | `evaluate_job_description()` tem param `company_id` e usa `get_gemini_client_for_tenant` | grep "company_id" — deve aparecer na assinatura |
| V-04 | `voice_screening_orchestrator.py:1072` | usa `get_gemini_client_for_tenant(session.company_id)` | grep "get_gemini_client_for_tenant" — deve aparecer nessa linha |
| V-05 | `wsi/_shared.py` | `get_anthropic_client()` usa `get_current_llm_tenant()` + `get_provider_for_tenant_from_db` | grep "get_current_llm_tenant" — deve aparecer |
| V-06 | `wsi/_shared.py` | `_run_anthropic_sync()` tem param `task_type` e passa para `generate_with_fallback` | grep "task_type" — deve aparecer na assinatura e na chamada |
| V-07 | `wsi/evaluation.py` | `analyze_response` passa `task_type="wsi"` | grep "task_type.*wsi" — deve aparecer |

**Script de smoke test rápido** (rodar após deploy):
```bash
# V-01/V-02: sem kwargs errados
grep -rn "resource_type.*llm_provider\|resource_id.*provider.*model" \
  app/shared/providers/llm_factory.py app/domains/ai/services/llm.py

# V-03: company_id na assinatura
grep -n "company_id" app/domains/cv_screening/services/wsi_question_adjuster.py

# V-04: tenant-aware em voice orchestrator
grep -n "get_gemini_client_for_tenant" \
  app/domains/voice/services/voice_screening_orchestrator.py

# V-05/V-06: BYOK + task_type no helper WSI
grep -n "get_current_llm_tenant\|task_type" app/api/v1/wsi/_shared.py

# V-07: task_type=wsi no endpoint de análise
grep -n "task_type" app/api/v1/wsi/evaluation.py
```

---

### 12.3 — Mapa Completo de Consumidores LLM

**Total**: 54 arquivos | 38 BYOK-aware | 15 legado (LLMService) | 1 parcial

#### Legenda

| Ícone | Significado |
|-------|------------|
| ✅ | BYOK-aware — usa factory ou contextvar corretamente |
| ⚠️ | Legado — usa LLMService global; BYOK depende de _current_tenant setado pelo orchestrator |
| 🔧 | Corrigido nesta sprint (2026-04-19) |
| 📌 | By design — hardcoded aceitável (voz, embedding, config endpoint) |

---

#### CAMADA API (`app/api/v1/`)

| Status | Arquivo | Padrão de chamada | task_type |
|--------|---------|-------------------|-----------|
| ✅ | `candidate_search/archetypes.py` | `generate_with_fallback` | chat |
| ✅ | `email_templates.py` | `generate_with_fallback` | chat |
| ✅ | `experience_highlights.py` | `generate_with_fallback` | chat |
| ✅ 📌 | `gemini_voice.py` | `get_gemini_client_for_tenant` + `genai.Client` | voz (by design) |
| ✅ | `internal_llm.py` | `generate_with_fallback` | chat |
| ✅ | `interviews.py` | `generate_with_fallback` | chat |
| ⚠️ | `lia_assistant/conversational.py` | `LLMService` global | — |
| ⚠️ | `lia_assistant/insights.py` | `LLMService` global | — |
| ⚠️ | `lia_assistant/_shared.py` | `LLMService` global | — |
| ⚠️ | `lia_assistant/wizard.py` | `LLMService` + `generate_native_gemini` | — |
| ✅ | `lia_profile_analysis.py` | `generate_with_fallback` | chat |
| ✅ 📌 | `llm_config.py` | `genai.Client` + `AsyncAnthropic` (key do tenant) | config endpoint |
| ✅ 🔧 | `wsi/_shared.py` | `get_anthropic_client` (contextvar) + `generate_with_fallback` | wsi via task_type |
| ✅ 🔧 | `wsi/evaluation.py` | `get_anthropic_client` → `_run_anthropic_sync(task_type="wsi")` | wsi |
| ✅ | `wsi/questions.py` | `get_anthropic_client` + `_run_anthropic_sync` | wsi |
| ✅ | `wsi/reports.py` | `generate_with_fallback` | wsi |
| ⚠️ | `orchestrator_routes.py` | `LLMService` global | — |

---

#### CAMADA ORQUESTRADOR (`app/orchestrator/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ⚠️ | `agentic_loop.py` | `LLMService` global | `_current_tenant` setado pelo main_orchestrator antes da chamada |
| ✅ | `main_orchestrator.py` | `LLMService` com contextvar | seta `_current_tenant` por request |
| ✅ | `tenant_budget.py` | `generate_with_fallback` | budget check antes do LLM |
| ✅ | `vector_semantic_cache.py` | `EmbeddingProviderFactory` | cache semântico |

---

#### DOMÍNIO: CV SCREENING (`app/domains/cv_screening/`)

| Status | Arquivo | Padrão de chamada | task_type |
|--------|---------|-------------------|-----------|
| ✅ | `services/cv_parser.py` | `LLMService` (tenant-aware) | chat |
| ⚠️ | `services/rubric_evaluation_service.py` | `LLMService` padrão | — |
| ✅ 🔧 | `services/wsi_question_adjuster.py` | `generate_with_fallback` + `get_gemini_client_for_tenant(company_id)` | screening / jd eval |

---

#### DOMÍNIO: VOICE (`app/domains/voice/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ✅ 📌 | `services/gemini_voice_service.py` | `get_gemini_client_for_tenant` + `generate_native_gemini_sync` | Gemini Live — voz exclusiva |
| ✅ 🔧 | `services/voice_screening_orchestrator.py` | `get_gemini_client_for_tenant(session.company_id)` | Entrevista voz + screening |

---

#### DOMÍNIO: SOURCING (`app/domains/sourcing/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ✅ | `services/llm_job_classification_service.py` | `generate_with_fallback` | classificação de vagas |
| ✅ | `services/search_analytics.py` | `generate_with_fallback` | analytics de busca |
| ⚠️ | `services/vacancy_search.py` | `generate_native_gemini` via `LLMService` | `_current_tenant` depende do contexto do chamador |

---

#### DOMÍNIO: JOB MANAGEMENT (`app/domains/job_management/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ✅ | `services/job_qualification_service.py` | `generate_with_fallback` | qualificação de vaga |
| ✅ | `services/job_template_service.py` | `generate_with_fallback` | templates |
| ⚠️ | `services/wizard_step_service/service.py` | `LLMService` global | wizard de criação de vaga (consolidado em pacote — N-04 Rev 4) |
| ⚠️ | `services/wizard_step_service/stage_description.py` | `LLMService` global | geração de descritivo |

---

#### DOMÍNIO: INTERVIEW INTELLIGENCE (`app/domains/interview_intelligence/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ⚠️ | `services/bias_detector_service.py` | `LLMService` lazy | detector de viés nas entrevistas |
| ⚠️ | `services/feedback_generator_service.py` | `LLMService` lazy | geração de feedback |
| ⚠️ | `services/strategic_opinion_service.py` | `LLMService` lazy | análise estratégica |
| ✅ 📌 | `services/transcription_service.py` | `get_gemini_client_for_tenant` | STT/transcrição de áudio |
| ✅ | `../interview_scheduling/agents/interview_scheduling_nodes.py` | `generate_with_fallback` | agendamento via agente |

---

#### DOMÍNIO: AUTOMATION (`app/domains/automation/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ⚠️ | `agents/automation_tool_registry.py` | `LLMService` global | registry de tools automáticas |
| ⚠️ | `services/stage_transition_automation.py` | `generate_with_fallback` sem company_id | automação de etapas |

---

#### DOMÍNIO: RECRUITER ASSISTANT (`app/domains/recruiter_assistant/`)

| Status | Arquivo | Padrão de chamada | task_type |
|--------|---------|-------------------|-----------|
| ✅ | `services/jobs_management_assistant_service.py` | `generate_with_fallback` | chat |
| ✅ | `services/kanban_assistant_service.py` | `generate_with_fallback` | chat |

---

#### DOMÍNIO: POLICY (`app/domains/policy/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ✅ | `agents/agent.py` | `LLMService` com lazy singleton | PolicyEngine — contextvar ativo |

---

#### SHARED SERVICES (`app/shared/`)

| Status | Arquivo | Padrão de chamada | Observação |
|--------|---------|-------------------|------------|
| ✅ | `intelligence/embedding_service.py` | `EmbeddingProviderFactory` | multi-provider embeddings (pgvector) |
| ✅ | `intelligence/semantic_search_service.py` | `generate_with_fallback` | busca semântica |
| ✅ | `providers/llm_client.py` | `get_anthropic_client` + `generate_with_fallback` | wrapper sync |
| ✅ | `providers/voice_composite.py` | `generate_with_fallback` + `get_gemini_client_for_tenant` | composição voz |
| ✅ 📌 | `providers/voice_gemini_live.py` | `get_gemini_client_for_tenant` | Gemini Live streaming |
| ✅ | `services/analysis_service.py` | `generate_with_fallback` | análise genérica |
| ✅ | `services/wsi_compact_pipeline.py` | `generate_with_fallback(task_type="screening")` | pipeline principal de triagem WSI |

---

### 12.4 — Resumo por Prioridade de Migração

Os 15 arquivos com status ⚠️ (LLMService legado) funcionam quando chamados dentro do contexto do `MainOrchestrator` (que seta `_current_tenant`). O risco é quando são chamados de contextos sem middleware (jobs Celery, webhooks externos, testes unitários).

| Prioridade | Arquivos | Risco |
|-----------|----------|-------|
| 🔴 P1 — Migrar este sprint | `lia_assistant/conversational.py`, `lia_assistant/wizard.py`, `lia_assistant/insights.py`, `orchestrator_routes.py` | Chamados diretamente por usuários — sem garantia de contextvar |
| 🟡 P2 — Migrar próximo sprint | `wizard_step_service/` (3 arquivos), `interview_intelligence/` (3 arquivos), `automation/` (2 arquivos) | Chamados por fluxos internos — contextvar geralmente ativo |
| 🟢 P3 — Monitorar | `agentic_loop.py`, `vacancy_search.py`, `rubric_evaluation_service.py` | Contextvar sempre ativo pelo orchestrator; risco baixo |

---

### 12.5 — Env Vars de Controle LLM

| Variável | Efeito | Padrão |
|----------|--------|--------|
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Key global da plataforma Gemini | obrigatório |
| `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | Key global da plataforma Claude | obrigatório |
| `AI_INTEGRATIONS_OPENAI_API_KEY` | Key global da plataforma OpenAI | opcional |
| `EMBEDDING_LOCK_PROVIDER` | Bloqueia fallback cross-provider em embeddings | vazio (desbloqueado) |
| `LLM_DEFAULT_PROVIDER` | Provider padrão quando tenant sem config | `gemini` |
| `FAIRNESS_LAYER3_ENABLED` | Ativa Layer 3 do FairnessGuard (análise semântica) | `false` |

*Last updated: 2026-04-19 | Auditoria exaustiva 54 arquivos — Checklist + Mapa completo*
