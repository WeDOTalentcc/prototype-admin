# ADR-007 — Vacancy Preview Canonical Pattern

**Status:** Accepted (2026-05-06)
**Deciders:** Paulo (founder), Phase A-F implementation
**Related:** ADR-001 Repository Pattern, CLAUDE.md > Frontend / React rules-of-hooks discipline

## Context

The "Recrutar > Visão Global > Vagas" rail surfaces 8 lifecycle stages
(`ats_importada → rascunho → enriquecida → wsi_config → aguardando_aprovacao →
publicada → ao_vivo → encerrada`). Pre-Phase A the recruiter clicked a
vacancy card and was thrown into the candidate kanban — a bad fit for
stages with zero candidates yet (everything before `aguardando_aprovacao`).
The recruiter had no contextual action surface and had to discover the
right next step by guessing.

Symptom: 192 vacancies in the rail with 133 in `Rascunho` (the screenshot
Paulo shared on 2026-05-06) and no obvious way to advance them. Backend
classifier was correct; frontend UX was the blocker.

A second symptom: BulkImportModal only accepted CSV/JSON manual upload
even though the backend had complete Gupy/Pandapé/Merge ATS clients.

## Decision

Adopt a **side-panel preview** pattern that mirrors the existing
candidate preview, with stage-aware actions that either:

1. **Deep-link** to the existing `/jobs/{id}?tab=edit&section=X` page
   (Configurações tab, ScreeningConfigManager) for pre-screening stages
   (`ats_importada / rascunho / enriquecida / wsi_config /
   aguardando_aprovacao`); OR
2. **Open inline modals** (`JobPublishModal` / `JobStatusModal`) on the
   rail itself for post-screening stages (`publicada / ao_vivo`).

The preview, the deep-link, and the wizard chat tools must reach the
**same** four conceptual actions per stage:

| Stage              | Recruiter action               | Tool / endpoint                                  |
|--------------------|--------------------------------|--------------------------------------------------|
| ats_importada      | Continuar JD                   | deep-link `?section=descricao`                   |
| rascunho           | Continuar JD                   | deep-link `?section=descricao`                   |
| enriquecida        | Continuar enriquecimento       | deep-link `?section=perguntas`                   |
| wsi_config         | Configurar WSI                 | deep-link `?section=perguntas`                   |
| aguardando_aprovacao | Ativar triagem WSI           | POST /job-readiness/.../dispatch-screening       |
| publicada          | Publicar / Despublicar         | inline `<JobPublishModal>` (+ /unpublish — Phase C) |
| ao_vivo            | Alterar status (pause/cancel/concluir) | inline `<JobStatusModal>`                |
| encerrada          | (read-only)                    | CTA disabled                                      |

## Consequences

### Positive

- Recruiter can drive a vacancy from import to dispatch without leaving
  the rail (deep-links and modals do the work).
- Wizard chat (LIA) parity — the four actions are also exposed as
  `wizard_tool_registry.py` tools (`generate_screening_questions /
  dispatch_screening / publish_vacancy / change_vacancy_status`), so the
  recruiter can drive the same flow via natural language.
- Discriminated `VacancyAction` union + `assertNeverAction` makes it a
  TypeScript error to add a new lifecycle stage in the backend without a
  frontend branch — caught by the existing
  `scripts/check-vacancy-action-coverage.ts` AST sensor in CI.

### Negative / Risk

- The preview lives next to the candidate preview in
  `pipeline-overview-page.tsx` (~2000 lines). Any refactor of that file
  needs to preserve both side panels.
- Two whitelists for `VALID_JOB_STATUSES` previously drifted (Phase C.1).
  ADR-007 mandates a single source: `app/api/v1/job_vacancies/_shared.py`.
  `tests/api/test_status_whitelist_consolidation.py` is the regression net.
- Merge ATS client gained a `list_jobs(page, size)` shim wrapping
  `get_jobs(...)` so the BulkImportModal "ATS Conectado" tab works for
  Merge users too (Phase G.1). Native pagination is offset-based for
  simplicity; large Merge instances (>500 jobs) may want cursor support
  later.

### Neutral

- The ScreeningConfigManager structure (3 sections: configuracoes /
  descricao / perguntas) is reused unchanged. `_externalActiveSection`
  was already the canonical override prop; we just started consuming it
  from the URL.
- The original `getVacancyCta` was deleted. Any future code that needs
  a label-only descriptor can compute it from `getVacancyAction(...).label`.

## Sensors

The following sensors guard this ADR:

1. `plataforma-lia/scripts/check-vacancy-action-coverage.ts` — backend
   `JOB_LIFECYCLE_ORDER` ↔ frontend `getVacancyAction` switch. Required
   in CI.
2. `lia-agent-system/scripts/check_company_id_in_routes.py` — every
   FastAPI route in `app/api/v1/` references `_require_company_id` or
   `get_user_company_id`. Warn-only initially; --strict after legacy
   cleanup.
3. `lia-agent-system/tests/wizard/test_phase_e_wizard_tools.py` — pins
   the four wizard tool schemas + STAGE_TOOLS allowlist + enum drift
   (mode, status, audience_policy).
4. `plataforma-lia/src/components/vacancy-preview/__tests__/vacancy-preview.test.tsx`
   — Rules of Hooks regression net + table-driven CTA coverage.
5. ESLint `react-hooks/rules-of-hooks` step in
   `frontend-ci.yml` (commit ae2e359b4) — global net for the broader
   modal/hook discipline.

## References

- `.planning/vacancy-pipeline-plan.md` (workspace root) — operational
  source of truth for Phase A-G.
- CLAUDE.md > Vacancy preview canonical pattern (governance).
- Phase A commits: 6a19f9234, 9274ccdf0
- Phase C commit: d220e5958
- Phase D commit: cee68ab29
- Phase E commit: 987a07a1b
- Phase F commit: f30cb9594
- Phase G commit: (this PR)
