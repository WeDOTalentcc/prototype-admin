# Handoff — Time Rails — Multi-tenancy Status

**Data:** 2026-04-22
**Repo alvo:** `ats-api-copia`

---

## Status: ✅ Nenhuma ação bloqueadora

Auditoria multi-tenancy realizada em 2026-04-22 não identificou gaps críticos no backend Rails.

---

## O que foi verificado

### Models com `company_id` validation

Modelos já seguem o padrão correto:

```ruby
# app/models/department.rb
class Department < ApplicationRecord
  validates :company_id, :name, presence: true
  belongs_to :company_profile, foreign_key: :company_id
end

# app/models/client_user.rb
class ClientUser < ApplicationRecord
  validates :company_id, presence: true
end
```

Isso é o **padrão de referência** que o time de IA (Python/FastAPI) também deveria seguir.

---

## Recomendação opcional (não bloqueadora)

### `MultiTenant` concern

Considerar criar um concern para garantir filtragem automática por `company_id` em todas as queries:

```ruby
# app/models/concerns/multi_tenant.rb
module MultiTenant
  extend ActiveSupport::Concern

  included do
    validates :company_id, presence: true

    scope :for_company, ->(company_id) { where(company_id: company_id) }

    # Opcional: default_scope para forçar filtragem
    # CUIDADO: default_scope pode causar surpresas; considerar query objects em vez disso
  end
end

# Uso:
class Department < ApplicationRecord
  include MultiTenant
  ...
end
```

Benefícios:
- DRY — elimina duplicação de `validates :company_id`
- Escopo `for_company` reutilizável em controllers
- Marcação explícita de quais models são tenant-scoped

---

## Handoff da sessão completa

Para contexto amplo da auditoria (frontend + IA), ver [HANDOFF_SESSION_MULTI_TENANCY.md](./HANDOFF_SESSION_MULTI_TENANCY.md).

Resumo:
- ✅ Frontend (plataforma-lia) — 26 pontos corrigidos (10 hooks/components + 16 proxy routes)
- ⚠️ Time IA (lia-agent-system) — 3 itens documentados em [HANDOFF_AI_TEAM_MULTI_TENANCY.md](./HANDOFF_AI_TEAM_MULTI_TENANCY.md)
- ✅ Rails (ats-api-copia) — nenhum item bloqueador

---

## Contato

Dúvidas: Paulo Moraes (tech@wedotalent.cc)
