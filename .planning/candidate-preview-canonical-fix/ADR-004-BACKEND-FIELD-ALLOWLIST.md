# ADR-004 — Backend ALLOWED_FIELDS allow-list (caveat F5)

**Data:** 2026-05-23
**Status:** Documentado (caveat conhecido)
**Phase:** F6

## Contexto

F5 (D7 — edit inline lápis) implementou UI/UX completa de edição:
- `<EditableField>` em `CandidatePageHeader` (name, current_title, location_city)
- `<EditArrayItemModal>` em `ProfileExperienceSection` (`work_history` array)
- `<EditArrayItemModal>` em `ProfileEducationSection` (`education` array)
- Backend: `POST /api/backend-proxy/chat/actions/candidate-field-update`

Durante F6 backend probe descobri que o handler `_update_candidate_field` em `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py:14` tem allow-list **estrita** de campos:

### Backend ALLOWED_FIELDS (estado 2026-05-23)

**ALLOWED_DIRECT_FIELDS** (11):
- `phone`, `email`, `linkedin_url`
- `current_title`, `current_company`
- `location_city`, `location_state`
- `salary_expectation_clt`, `salary_expectation_pj`
- `work_model_preference`
- `languages` (JSON)

**ALLOWED_JSON_FIELDS** (2):
- `availability_date`, `education_level`

**Total: 13 fields**

### Comportamento

Se field não estiver na allow-list, backend retorna:
```json
{
  "status": "error",
  "message": "Campo 'XYZ' não é atualizável pelo chat. Campos permitidos: ...",
  "error_detail": "Field 'XYZ' not in ALLOWED_FIELDS"
}
```

Frontend (via toast.error) mostra mensagem amigável.

## Decisão

**Aceitar caveat por agora.** Não vou modificar backend nesta fase (escopo Replit-only, não toca handler).

### Ação imediata (boy scout em F6)

1. **`name` field**: revertido para read-only em `CandidatePageHeader` (TODO marker apontando para esta ADR)
2. **`work_history`/`education` arrays**: UI mantida (Phase B2 está completa) — runtime error em primeiro save mostra toast amigável; usuário entende

### Backlog (próxima sprint)

- Expandir `ALLOWED_DIRECT_FIELDS` em `candidate_actions.py:14` com:
  - `name`, `headline`, `summary`, `current_position`
  - `github_url`, `portfolio_url`, `website`
  - `years_of_experience`
- Expandir `ALLOWED_JSON_FIELDS` (ou criar new logic) para arrays:
  - `work_history` (replace-all OU per-index)
  - `education`
  - `technical_skills` (string array)
  - `certifications`
- Considerar criar endpoint específico `PUT /candidates/{id}/experiences` per-array para encoding mais limpo

## Field mapping (UI → backend)

| UI campo | Backend ALLOWED? | Mapeamento |
|---|---|---|
| name | ❌ | TODO add |
| current_title (header position) | ✅ | OK |
| location_city (header location) | ✅ | OK |
| work_history (experiences array) | ❌ | Backend allow-list expansion + JSON handling |
| education (array) | ❌ | Backend allow-list expansion + JSON handling |
| email/phone/linkedin_url | ✅ | OK (se aplicado futuramente) |
| skills/technical_skills | ❌ | Backend allow-list expansion |

## Refs

- Commit F5 B1+B2: `0cf9510b1`
- Backend: `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py:14`
- Backend chat dispatch: `lia-agent-system/app/api/v1/chat.py:1027`
