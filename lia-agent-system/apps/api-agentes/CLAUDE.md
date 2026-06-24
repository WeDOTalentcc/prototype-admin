# CLAUDE.md — api-agentes

Micro-app de Agent Studio, chat SSE, LLM config e governança da LIA.
Domínio: Agent Studio, chat SSE, AI config, LLM config, digital twins, HITL, guardrails, custom agents.
Porta padrão: `8003`.

## Regra Auth — OBRIGATÓRIA em todos os novos endpoints

TODO endpoint **novo** neste sub-app DEVE usar `get_auth_context_dependency`:

```python
from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

@router.get("/endpoint")
async def meu_endpoint(auth: AuthContext = Depends(get_auth_context_dependency())):
    company_id = auth.company_id
```

**PROIBIDO** em novos endpoints:
- `from app.auth.dependencies import get_current_active_user`
- `from app.auth.dependencies import get_current_user`
- `from app.auth.dependencies import get_current_user_or_demo`

**Endpoints legados existentes são PERM-EXEMPT** — NÃO reescrever em massa.
Somente novos endpoints devem usar `get_auth_context_dependency()`.

### Por que AuthContext?

`AuthContext` unifica `user`, `company_id`, `auth_source` e `roles` num único objeto:

```python
auth.user                   # User model (retrocompat)
auth.company_id             # tenant UUID string (multi-tenancy canonical)
auth.auth_source            # AuthSource.LOCAL / RAILS(deprecated) / WORKOS
auth.roles                  # list[str]
auth.is_wedotalent_admin    # bool — property
auth.is_admin               # bool — property
auth.has_role("recruiter")  # bool — method
```

## Domínio

Rotas deste sub-app: Agent Studio, chat SSE, LLM config, digital twins, HITL, guardrails.
Destino de extração para G10: será consumidor de `ats-llm` quando disponível.

### Módulos incluídos

| Arquivo | Router(s) | Tags |
|---|---|---|
| `agent_chat_sse.py` | `router` | chat-sse |
| `agent_deployments.py` | `router`, `target_router` | agent_deployments |
| `agent_memory.py` | `router` | agent_memory |
| `agent_monitoring.py` | `router` | agent_monitoring |
| `agent_quality.py` | `router` | agent_quality |
| `agent_quality_dashboard.py` | `router` | agent_quality_dashboard |
| `agent_studio_channels.py` | `router` | agent_studio_channels |
| `agent_studio_quality.py` | `router` | agent_studio_quality |
| `agent_studio_triagem_invite.py` | `router` | agent_studio_triagem_invite |
| `agent_studio_voice.py` | `router` | agent_studio_voice |
| `agent_studio_whatsapp.py` | `router` | agent_studio_whatsapp |
| `agent_template_catalog.py` | `router` | agent_template_catalog |
| `agent_templates.py` | `router` | agent_templates |
| `agent_approvals.py` | `agent_router`, `approvals_router` | agent_approvals |
| `agent_explainability.py` | `router` | agent_explainability |
| `ai_config.py` | `router` | ai_config |
| `ai_consumption.py` | `router` | ai_consumption |
| `ai_performance.py` | `router` | ai_performance |
| `ai_transparency.py` | `router` | ai_transparency |
| `custom_agents.py` | `router`, `marketplace_router`, `admin_marketplace_router` | custom_agents / marketplace |
| `digital_twins.py` | `router` | digital_twins |
| `llm_config.py` | `router` | llm_config |
| `internal_llm.py` | `router` | internal_llm |
| `hitl.py` | `router` | hitl |
| `guardrails.py` | `router` | guardrails |

## MONOLITH-IMPORT markers em main.py

Os imports marcados com `# MONOLITH-IMPORT:` são dependências do monolito que ainda não têm
equivalente em libs/ extraídas. Ao migrar este sub-app para standalone:

1. `app.core.sentry` → extrair para `lia-config` ou `lia-utils`
2. `app.core.config` → migrar para `lia-config` (parcialmente disponível)
3. `app.core.database` → migrar para `lia-config` (get_db disponível, falta init_db)
4. `app.core.logging_config` → extrair para `lia-utils`
5. `app.shared.pii_masking` → extrair para `lia-utils`
6. `app.config.langsmith` → extrair para `lia-config`
7. `app.middleware.rate_limiter` → extrair para `lia-utils`
8. `app.middleware.request_id` → extrair para `lia-utils`
9. `app.core.logging_middleware` → extrair para `lia-utils`

## Arquivos de referência

- `app/shared/auth/auth_provider.py` — implementação do `AuthContext` + `get_auth_context_dependency`
- `app/auth/dependencies.py` — auth legada (somente leitura — não adicionar dependências)
- `apps/api-vagas/main.py` — sub-app de referência com mesmo padrão de middleware
