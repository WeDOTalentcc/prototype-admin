# Handoff — Time IA — Multi-tenancy Gaps

**Data:** 2026-04-22
**Repo alvo:** `lia-agent-system` (repo do time IA, separado de `wedotalent02202026`)
**Origem:** Auditoria exaustiva feita no snapshot local em `wedotalent02202026/lia-agent-system/`

---

## Resumo

Auditoria multi-tenancy encontrou **3 itens** no código de IA/agentes que precisam atenção do time. Um é P0 (vazamento cross-tenant), os outros são P1 (refinamentos de isolation em code paths legados).

A arquitetura principal (JWT middleware, `TenantProviderRegistry` BYOK, token budget, audit logging) **está production-grade**. Os gaps são pontuais.

---

## Item 1 — 🔴 P0: `agent_monitoring_service.get_all_agents_summary()` sem escopo por company

**Arquivo:** `app/shared/governance/agent_monitoring_service.py` linhas 212-219

**Problema:**
```python
async def get_all_agents_summary(self) -> list[dict[str, Any]]:
    """Get summary for all agents."""
    summaries = []
    for agent_id in AGENT_DEFINITIONS:
        summary = await self.get_agent_summary(agent_id)
        if summary:
            summaries.append(summary)
    return summaries
```

A função consulta `AgentActivity` sem filtro de `company_id`. O endpoint `/api/v1/agent-monitoring/agents` (linhas 105-110 em `app/api/v1/agent_monitoring.py`) expõe atividades de **todos os tenants** para qualquer usuário autenticado.

**Impacto:** Qualquer cliente pode ver estatísticas de agentes de outros clientes (volumes, sucesso/falha, usage patterns).

**Fix sugerido:**

```python
# app/shared/governance/agent_monitoring_service.py
async def get_all_agents_summary(self, company_id: str) -> list[dict[str, Any]]:
    """Get summary for all agents scoped to a specific company."""
    summaries = []
    for agent_id in AGENT_DEFINITIONS:
        summary = await self.get_agent_summary(agent_id, company_id=company_id)
        if summary:
            summaries.append(summary)
    return summaries

async def get_agent_summary(self, agent_id: str, company_id: str) -> dict[str, Any] | None:
    # Adicionar filtro no query existente:
    query = select(AgentActivity).where(
        AgentActivity.agent_id == agent_id,
        AgentActivity.company_id == company_id,  # ← NOVO
    )
    ...
```

```python
# app/api/v1/agent_monitoring.py
from app.shared.tenant_guard import get_verified_company_id

@router.get("/agents")
async def get_all_agents_summary(
    company_id: str = Depends(get_verified_company_id),  # ← NOVO
    db: AsyncSession = Depends(get_db),
):
    service = AgentMonitoringService(db)
    return await service.get_all_agents_summary(company_id=company_id)
```

**Testes sugeridos:**
- Criar 2 companies A e B com agent activities distintas
- Confirmar que user de A vê só activities de A (e vice-versa)
- Tentar passar `X-Company-ID` de B no header estando logado como A → 403

---

## Item 2 — 🟡 P1: `candidate_repository` — search/find_by_email sem filtro

**Arquivo:** `app/shared/repositories/candidate_repository.py` linhas 22-56

**Contexto:** O modelo `Candidate` (em `libs/models/lia_models/candidate.py`) **tem** coluna `company_id = Column(String(255), nullable=False, index=True)`. Os métodos do repositório simplesmente ignoram.

**Problema:**
```python
async def find_by_email(self, db, email: str) -> Candidate | None:
    query = select(self.model_class).where(self.model_class.email == email)
    # ← Sem filtro company_id

async def search(self, db, query: str, filters: dict[str, Any] | None = None,
                 limit: int = 50, offset: int = 0) -> list[Candidate]:
    stmt = select(self.model_class).where(
        or_(
            self.model_class.name.ilike(search_pattern),
            self.model_class.email.ilike(search_pattern),
            ...
        )
    )
    # ← Sem filtro company_id
```

**Risco:** Se qualquer endpoint ativo chamar esses métodos sem adicionar filtro no call-site, retorna candidatos de todas as companies.

**Fix sugerido:**
```python
async def find_by_email(self, db, email: str, company_id: str | None = None) -> Candidate | None:
    query = select(self.model_class).where(self.model_class.email == email)
    if company_id:
        query = query.where(self.model_class.company_id == company_id)
    ...

async def search(self, db, query: str, filters: dict[str, Any] | None = None,
                 company_id: str | None = None, limit: int = 50, offset: int = 0) -> list[Candidate]:
    stmt = select(self.model_class).where(or_(...))
    if company_id:
        stmt = stmt.where(self.model_class.company_id == company_id)
    ...
```

**Decisão arquitetural:** Considerar tornar `company_id` parâmetro **obrigatório** (não `None`) para forçar todo call-site a ser explícito. Se algum caller tem motivo legítimo de cross-tenant (admin search), precisa passar flag explícita.

**Call sites a auditar:**
```bash
grep -rn "\.search(\|\.find_by_email(" app/ | grep candidate
```

Conferir se cada uso passa `company_id`.

---

## Item 3 — 🟡 P1: LLM Factory — 2 code paths legados sem `company_id`

**Arquivo:** `app/shared/providers/llm_factory.py` linhas 455 e 715

**Contexto:** A `LLMProviderFactory` está bem arquitetada — `TenantProviderRegistry` isola por `tenant_id`, BYOK com Fernet encryption, token budget per-tenant. Não há vazamento estrutural.

**Porém dois chamadas legadas não passam `company_id`:**

```python
# Linha 455
_claude_provider = get_provider_for_tenant().get("claude")

# Linha 715 — mesmo padrão
_claude_provider = get_provider_for_tenant().get("claude")
```

Sem `tenant_id` kwarg → `ProviderContainer` faz fallback para `self._tenant_id` (pode ser `None`) → usa env config global, ignora chave custom do tenant na DB.

**Impacto:** Se tenant configurou API key custom (BYOK), esses code paths ignoram e usam chave global. Não é vazamento, mas é comportamento inconsistente e um tenant pode receber LLM com key global quando deveria ser o custom dele.

**Fix sugerido:**
```python
# ANTES:
_claude_provider = get_provider_for_tenant().get("claude")

# DEPOIS:
from app.shared.tenant_llm_context import get_current_llm_tenant
company_id = get_current_llm_tenant()
_claude_provider = get_provider_for_tenant(tenant_id=company_id).get("claude")
```

`get_current_llm_tenant()` lê do `ContextVar` setado pelo `AuthEnforcementMiddleware` — mesmo padrão já usado em paths modernos (llm_factory.py:913).

**Comparação com o path correto:**
```python
# llm_factory.py:913 — PADRÃO CORRETO (copiar este)
company_id = get_current_llm_tenant()
provider = get_provider_for_tenant(tenant_id=company_id).get(...)
```

---

## Item 4 — 🟡 P1: Checklist de produção — LLM factory

Confirmar em staging/produção:

- [ ] **`ENCRYPTION_KEY` setada.** Sem ela, `_encrypt_provider_keys()` em `LlmConfigRepository` quebra silenciosamente — BYOK keys não são salvas corretamente
- [ ] **Audit todos os `get_provider_for_tenant()` sem `tenant_id`.** Comando: `grep -rn "get_provider_for_tenant()" app/ | grep -v "tenant_id\|company_id"`
- [ ] **Redis token budget keys incluem `tenant_id`** (não apenas `user_id`). Verificar em `app/domains/credits/services/token_budget_service.py`
- [ ] **Cache `_tenant_configs` invalida** corretamente via `clear_tenant_config_cache(company_id)` em todo handler de `update_llm_config()` (já presente em `api/v1/llm_config.py:186`)
- [ ] **Fallback behavior documentado:** quando tenant não tem key custom, sistema usa env key global — isso é intencional e OK

---

## Item 5 — Verificação cruzada sugerida

Grep patterns para auditoria interna do time IA:

```bash
# Repositórios sem filtro de tenant
grep -rn "company_id" app/shared/repositories/ | grep -v "_test"

# Calls de LLM sem tenant_id
grep -rn "get_provider_for_tenant()" app/ | grep -v "tenant_id\|company_id"

# Queries sem escopo explícito
grep -rn "select(.*)\|.query(" app/ | grep -v "company_id\|tenant_id" | head -30
```

---

## Referências no código nosso (plataforma-lia)

Padrão canônico que seguimos no frontend para referência (caso queiram alinhar com a mesma filosofia):

- `plataforma-lia/src/lib/api/session-auth.ts` — dual-auth helper (WorkOS SSO + JWT email/senha)
- `plataforma-lia/src/lib/api/backend-url.ts` — BACKEND_URL centralizado
- Commit `<novo>` — 16 rotas proxy user-facing migradas para o novo padrão

---

## Contato

Dúvidas: Paulo Moraes (tech@wedotalent.cc)
