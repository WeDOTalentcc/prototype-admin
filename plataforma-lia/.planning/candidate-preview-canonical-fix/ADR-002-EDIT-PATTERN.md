# ADR-002 — Lapis Inline por Campo com LGPD Field Policy

**Status:** APROVADO  
**Data:** 2026-05-23  
**Confirmado por:** Paulo Moraes (Opcao A, F0)  
**Milestone:** Candidato 2 Surfaces (Drawer + Page dual-mode)

---

## Contexto

Surface 2 (CandidatePage) precisa permitir edicao inline de dados de candidatos.
Dois patterns foram avaliados:

- **Opcao A:** Inline lapis por campo via `<EditableField>` + endpoint chat actions
- **Opcao B:** Modal de edicao full-form por secao

Paulo confirmou Opcao A em F0.

## Decisao

**Lapis inline por campo via `<EditableField>` com LGPD field policy.**

### Componente canonical

`src/components/candidate-profile/EditableField.tsx`
- Exibe valor + icone de lapis ao hover
- Ao clicar: input inline (text) ou select
- onSave dispara `useCandidateFieldUpdate`
- Campos LGPD-blocked: render sem lapis (readonly automatico)

### Hook canonical

`src/hooks/candidates/use-candidate-for-page.ts` expoe `updateField(fieldKey, value)`

### Endpoint canonical

`POST /api/backend-proxy/chat/actions/candidate-field-update`
- Body: `{ candidate_id, field_key, new_value }`
- `company_id` vem do JWT (NUNCA do body — ADR REGRA-6)
- Backend: `lia-agent-system/app/api/v1/candidate_field_update.py`

### LGPD Blocked Fields (readonly forcado, sem lapis)

```typescript
const LGPD_BLOCKED_FIELDS = [
  "race", "raca", "racial_origin",
  "gender", "genero",
  "marital_status", "estado_civil",
  "religion", "religiao",
  "health_data", "dados_saude",
  "ethnic_origin", "origem_etnica",
]
```

### Feature Flag

`NEXT_PUBLIC_FF_CANDIDATE_EDIT=true` — habilita modo edicao em CandidatePage.
Quando `false`: Surface 2 opera em modo read-only (identico ao Surface 1).

## Consequencias

- Edicao granular sem forms modais pesados
- LGPD enforcement no ponto de render (nao apenas no backend)
- Sensor `check_editable_fields_not_lgpd_sensitive.py` garante nenhum campo LGPD-blocked recebe lapis

## Sensors

- `check_editable_fields_not_lgpd_sensitive.py` — bloqueia campos LGPD em EditableField
- `check_company_id_from_jwt.mjs` — bloqueia company_id no body de POST/PUT

---

_Registered by execute-phase F6 — 2026-05-30_
