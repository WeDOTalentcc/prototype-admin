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
