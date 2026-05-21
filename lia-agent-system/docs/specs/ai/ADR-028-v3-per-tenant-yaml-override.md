# ADR-028-v3: Per-tenant YAML override + hot-reload (T-13)

**Status:** Aprovado 2026-05-20 (T-13 Fase 1 — loader infra)
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-13)
**Relaciona:** ADR-028 (YAML metadata.version), ADR-019 (services consolidation),
T-05 (YAML metadata enforcement)

## Contexto

WeDOTalent Fortune 500 prospects pediram persona LIA customizada por tenant SEM
deploy (ex: empresa financeira quer tom formal, empresa varejo quer informal).

Pré-T-13: persona/prompts são compostos via `SystemPromptBuilder.build()` que
chama `PromptLoader.load(path)` retornando SEMPRE o YAML canonical
`app/prompts/{path}.yaml`. Customização cross-tenant exige PR + deploy.

Pós-T-13: `PromptLoader.load(path, tenant_id=...)` tenta primeiro
`app/prompts/tenants/{tenant_id}/{path}.yaml` e fallback pra canonical.

## Decisão

### 1. Estrutura canonical de diretório

```
app/prompts/
├── shared/                  # canonical persona base
│   ├── lia_persona.yaml
│   ├── compliance_block.yaml
│   └── defensive.yaml
├── domains/                 # canonical domain prompts
│   ├── sourcing.yaml
│   ├── communication.yaml
│   └── ...
└── tenants/                 # ⭐ NEW — per-tenant overrides
    ├── .gitkeep             # marker (tenants commit separadamente)
    ├── acme-corp/
    │   ├── shared/
    │   │   └── lia_persona.yaml  # override completo
    │   └── domains/
    │       └── communication.yaml  # tone formal financeiro
    └── retail-store-xyz/
        └── domains/
            └── sourcing.yaml      # tone informal varejo
```

### 2. API canonical `PromptLoader`

```python
from app.shared.prompts.loader import PromptLoader

# Canonical (backward-compatible)
prompt = PromptLoader.load("domains/sourcing")

# Per-tenant override
prompt = PromptLoader.load("domains/sourcing", tenant_id="acme-corp")
# → tenta tenants/acme-corp/domains/sourcing.yaml primeiro
# → fallback pra domains/sourcing.yaml canonical

# Hot-reload (admin UI / cron)
PromptLoader.invalidate_cache(path="domains/sourcing", tenant_id="acme-corp")
PromptLoader.invalidate_cache()  # full cache flush
```

### 3. Cache canonical

Cache key: `tuple[path: str, tenant_id: str | None]`
- Canonical entries: `(path, None)`
- Tenant entries: `(path, tenant_id)`
- Sem cross-tenant pollution (tenants veem APENAS seu override + canonical fallback)

### 4. Schema canonical override

Tenant override DEVE ter:
```yaml
metadata:
  version: "1.0"
  tenant_id: "acme-corp"
  source: "manual"  # ou "auto-generated"
  inherits: "domains/sourcing.yaml"  # canonical parent
  created_at: "2026-05-20T00:00:00Z"

# Resto: schema canonical compatible (mesmas top-level keys do canonical)
persona: |
  ... (override completo OU parcial via inherits)
```

### 5. Sensor canonical

`scripts/check_tenant_yaml_override.py`:

| Regra | Descrição |
|---|---|
| R1 | tenant override file em estrutura `tenants/{id}/{path}.yaml` |
| R2 | metadata.version presente (mesma regra ADR-028) |
| R3 | NÃO PII raw (CPF/email/phone) no override — LGPD cross-tenant exfiltration risk |
| R4 | (WARN) schema top-level keys compatible com canonical parent |

Modo INICIAL: WARN-ONLY (admin UI ainda não existe).
Promover BLOCKING após T-13 Fase 2 (UI live + tenant override workflow).

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-13 Fase 1 (este)** | 4 | Loader extension + tenants/ dir + sensor warn-only + ADR |
| T-13 Fase 2 | 5+ | Admin UI CRUD `/api/v1/admin/prompts/tenant-override` |
| T-13 Fase 3 | 6+ | Webhook hot-reload trigger (admin save → invalidate_cache) |
| T-13 Fase 4 | 7+ | UI consultora WeDO publica override pre-aprovados pre-tenant |

## Consequências

**Positivas:**
- Cliente Fortune 500 customiza persona sem deploy
- Hot-reload (admin save → cache invalidate → próximo request usa override)
- Backward compat 100% (tenant_id é parâmetro opcional)
- Fail-soft: tenant override missing → cai pra canonical (default behavior)
- Cache key isolation = zero cross-tenant pollution
- Sensor R3 previne LGPD exfiltration cross-tenant

**Negativas:**
- Aumenta superfície de teste (cada domain × cada tenant override)
- Risco drift entre canonical e overrides (sensor R4 alerta mas não bloqueia v1)
- Manutenção (quando canonical muda, overrides podem ficar obsoletos)

**Mitigação drift:**
- Sensor R4 alerta schema drift periodicamente
- ADR-028-v4 (futuro): version pinning explícito (override aponta `inherits.version`)

## Referências

- PLANO_ACAO_REPLIT_V3 T-13
- ADR-028 (YAML metadata.version canonical)
- ADR-019-v2 (services consolidation)
- T-05 (YAML enforcement)
- `app/shared/prompts/loader.py` (canonical loader)
- `scripts/check_tenant_yaml_override.py` (sensor canonical)
