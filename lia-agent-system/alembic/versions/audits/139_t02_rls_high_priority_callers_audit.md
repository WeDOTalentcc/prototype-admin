# Migration 139_t02_rls_high_priority — callers audit

Created retroactively as part of the canonical-skill-chain sprint
(2026-05-24). Migration was merged 2026-05 (date inferred from
alembic ordering) and tightened RLS policies on 27 HIGH-priority tables
from permissive (`USING company_id IS NULL OR company_id = ...`) to
strict (`USING company_id::text = app_current_company_id()`).

The strict policies caused runtime failures in code paths that wrote
NULL company_id. The chat write path was the most visible: users saw
the LIA chat hang on "Pensando..." (commit 0a58a5bf onward).

## Tables tightened by migration 139

HIGH_TABLES_NOT_NULL + HIGH_TABLES_NULLABLE_UUID + HIGH_TABLES_NULLABLE_VARCHAR:

- (consult migration 139_t02_rls_high_priority.py for the full list)
- Notably: **conversations**, **teams_conversations**, **calibration_events**,
  **calibration_weights**, **ml_model_registry**

## Call sites for `conversations` table

INSERT call sites:

- [fixed] `app/domains/chat/repositories/chat_repository.py:create_conversation`
  → commit 0a58a5bf (V1) — `company_id` now required, raises if empty.
- [fixed] `app/domains/recruiter_assistant/services/conversation_memory.py:get_or_create_conversation`
  → commit 611883220 (V2) — `company_id` propagated through 5 callers
  (conversational, main_orchestrator x2, conversations, legacy/orchestrator).

Read paths (no INSERT but use SELECT under RLS):

- [reviewed] `app/api/v1/chat.py:send_message` (line 261, post-V5
  refactor) — uses `commit_keeping_tenant` (canonical helper) so the
  `db.refresh()` immediately after commit re-injects tenant context.
- [reviewed] all other `select(Conversation)` sites — execute under the
  tenant-aware session via `get_tenant_db` dependency.

## Call sites for `teams_conversations` table

- [RLS-EXEMPT] `app/domains/communication/repositories/teams_repository.py:save_conversation`
  → marker `# RLS-EXEMPT: TeamsConversation: RLS policy ... accepts NULL
  WT-LEGACY-RLS-EXEMPT exp:2026-11-30` (commit 611883220 +
  e33d6aee canonical format). Hardening item tracked for Teams bot
  framework propagation.

## Call sites for `calibration_events`, `calibration_weights`

- [unreviewed] — no audit performed in this retroactive doc. Tracked
  as a separate hardening item. The strict RLS policy may be filtering
  reads in calibration paths; needs runtime test against Postgres to
  confirm. Sensor `check_commit_then_read_without_tenant.py` will surface
  any related defect on first hit.

## Call sites for `ml_model_registry`

- [unreviewed] — same as above. Lower priority (ML registry is read-mostly).

## Lessons learned (Hashimoto)

The chat saga (5 commits 0a58a5bf..e33d6aee) was the cost of NOT auditing
callers at migration-merge time. If this doc had been created when
migration 139 was authored, the chat fix would have been a single commit
(handler + repo + tests + RLS-EXEMPT markers), not five.

This is now the canonical template. Any future migration that:
- tightens NOT NULL on a column,
- adds CHECK / FK constraints,
- enables/forces RLS,
- creates / tightens RLS policy

MUST create an audit doc at
`alembic/versions/audits/<revision>_callers_audit.md` listing every
INSERT/UPDATE/DELETE call site of the affected table and marking each
as `[reviewed]`, `[fixed]`, or `[RLS-EXEMPT]`.

Sensor: `scripts/check_migration_callers_audit.py` (blocking once
backlog of 18 historical migrations is cleared).
