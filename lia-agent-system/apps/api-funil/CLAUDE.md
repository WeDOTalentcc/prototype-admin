# CLAUDE.md — api-funil

Micro-app de pipeline e funil de candidatos da LIA.
Domínio: Pipeline, Candidates, Applications, Sourcing, Kanban.
Porta padrão: `8002`.

## Regra Auth — OBRIGATÓRIA em todos os novos endpoints

Todo endpoint **novo** neste sub-app DEVE usar `get_auth_context_dependency`:

```python
from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

@router.get("/meu-endpoint")
async def meu_endpoint(
    auth: AuthContext = Depends(get_auth_context_dependency()),
):
    user = auth.user
    company_id = auth.company_id
```

**PROIBIDO em novos endpoints:**
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

### Sensor ativo

`scripts/check_auth_provider_adoption.py --subapp funil` — detecta novos
endpoints que usam auth legada.

**Baseline 2026-06-13: 89 violations** (todos endpoints legados — PERM-EXEMPT).

### Arquivos de referência

- `app/shared/auth/auth_provider.py` — implementação do `AuthContext` + `get_auth_context_dependency`
- `app/auth/dependencies.py` — auth legada (somente leitura — não adicionar dependências)
