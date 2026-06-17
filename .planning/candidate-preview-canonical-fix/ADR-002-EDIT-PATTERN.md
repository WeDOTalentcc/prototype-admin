# ADR-002 — Edit pattern: inline pencil (D7) + LGPD policy

**Data:** 2026-05-23
**Status:** Approved (Paulo D7)
**Phase:** F5

## Contexto

Paulo definiu que page completa (mode=page) deve permitir edição inline tipo LinkedIn (lápis por campo). Drawer (mode=modal) permanece read-only por design (contexto de decisão de pipeline, não edição).

## Decisão

### Pattern UX

- **Pencil icon ao lado do campo** quando hover/focus + `editable=true`
- Click pencil → input inline → **Enter** salva / **Esc** cancela
- Optimistic update + rollback em erro
- Toast de sucesso/erro

### Arquitetura

- `<EditableField>` componente reusável (single field)
- `<EditArrayItemModal>` modal generic (array items)
- `useCandidateFieldUpdate(id)` hook canonical (single field)
- `useCandidateArrayUpdate<T>(id, field, current)` hook canonical (array replace-all)
- `<CandidateEditProvider>` context — Surface 2 mode=page provê `editable=true` + `updateField`; Surface 1 default `editable=false`

### Backend

Toda edição via `POST /api/backend-proxy/chat/actions/candidate-field-update` (FastAPI lia-agent-system). Multi-tenant via JWT cookie (proxy resolve).

### LGPD policy

**14+ fields BLOQUEADOS** em runtime + sensor build-time:

```
race, racial_origin, gender, marital_status, religion,
health_data, ethnic_origin, political_opinion,
sexual_orientation, union_membership, date_of_birth,
cpf, rg, passport, id, candidate_id, company_id,
account_id, created_at, updated_at, created_by
```

Defesa em profundidade:
- **Runtime**: `useCandidateFieldUpdate` refusa antes de fazer fetch
- **Build-time**: `scripts/check_editable_fields_not_lgpd_sensitive.py` scan AST
- **CI**: sensor em `frontend-ci.yml` blocking mode

## Alternativas rejeitadas

- **Modal de "editar tudo"** — pouco granular, sem feedback per-field
- **Edição via chat LIA** — endpoint existe mas UX assume contexto conversacional, não direct manipulation

## Consequências

- ✅ Granularidade boa (per-field para top-level; per-item para arrays)
- ✅ Multi-tenant garantido via JWT (não payload)
- ✅ LGPD: defense-in-depth runtime + build-time
- ⚠️ Backend tem allow-list de 13 fields (ver ADR-004). Alguns campos editáveis na UI vão falhar runtime até backend expandir

## Refs

- Commits F5: `77686ef05` (Phase A), `9b7c0352a` (B0.5), `0cf9510b1` (B1+B2)
- PLAN.md V3 seção F5
