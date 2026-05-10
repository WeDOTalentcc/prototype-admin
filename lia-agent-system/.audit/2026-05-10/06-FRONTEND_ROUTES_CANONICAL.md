# 06 — Frontend Routes Canonical (F2-1 fix)

> **Resolve F2-1:** 4 paths reportados como 404 na Fase 2 da auditoria (smoke tests).
> Causa: docs antigas referenciavam paths que mudaram (R-013 e Fase 2 Phase 4).
> Realidade: Next.js App Router usa `(dashboard)` route group que NÃO vira segmento.

---

## Paths reportados 404 na Fase 2

| Path testado | Status | Path real canonical | Memory ref |
|---|---|---|---|
| `/pt/dashboard` | 404 | Root é `/pt/(dashboard)/...` (route group sem segmento). Pages: agent-studio, ajuda, bancos-de-talentos, biblioteca-lia, central-comunicacao, chat, configuracoes, funil-de-talentos, jobs, recrutar, tasks | — |
| `/pt/candidatos` | 404 | `/pt/teams-tab/candidatos` (subapp Teams) | — |
| `/pt/visao-do-funil` | 404 | `/pt/funil-de-talentos` | `project_funil_talentos_canonical_fix_2026-05-01` |
| `/portal/data-request` | 404 | `/pt/portal/...` (subpath verificar) | — |

---

## Páginas canonical hoje (validado SSH 2026-05-10)

### Direct (sem grupo de layout)
- Login/auth: `/pt/login`, `/pt/register`, `/pt/forgot-password`, `/pt/reset-password`
- Jobs/Vagas: `/pt/jobs`, `/pt/vagas`
- Onboarding: `/pt/access`, `/pt/accept-invitation`, `/pt/aceitar-convite`
- Standalone: `/pt/portal`, `/pt/privacidade`, `/pt/trust`
- Outros: `/pt/triagem`, `/pt/teams-tab`, `/pt/design-system`, `/pt/shared`

### Dentro do grupo `(dashboard)` (URL = `/pt/<page>` direto, sem segment)
- `/pt/agent-studio` — Agent Studio (custom agents)
- `/pt/ajuda` — Help center
- `/pt/bancos-de-talentos` — Talent Pools
- `/pt/biblioteca-lia` — LIA Library (insights/docs)
- `/pt/central-comunicacao` — Communication Center
- `/pt/chat` — Unified Chat
- `/pt/configuracoes` — Company Settings
- `/pt/funil-de-talentos` — Talent Funnel (Prompt 4 canonical)
- `/pt/jobs` — Jobs
- `/pt/recrutar` — Recruit
- `/pt/tasks` — Tasks

---

## Recomendação para docs antigas

Atualizar docs em `WeDO/...` que ainda mencionam:
- `/pt/dashboard` → linkar para `/pt/funil-de-talentos` ou `/pt/recrutar` (entry pages corretas)
- `/pt/candidatos` → `/pt/teams-tab/candidatos`
- `/pt/visao-do-funil` → `/pt/funil-de-talentos`

**Conclusão F2-1:** **NÃO é gap de feature** — é outdated docs. Frontend routes
estão corretas e canonical (validado por listing direto via SSH).
