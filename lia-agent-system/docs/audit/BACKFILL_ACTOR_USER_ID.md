# Backfill `audit_logs.actor_user_id` (Task #419)

## Why

Migration `084_add_actor_user_id_to_audit_logs` promoted `actor_user_id`
to a structured column on `audit_logs`. Rows written **after** that
migration populate the column directly. Rows written **before** it still
carry the user id only inside the free-text `reasoning` JSON array, in
the form `"actor_user_id=user-42"`.

Until those legacy rows are migrated, the admin endpoint
`GET /admin/audit/decisions?actor_user_id=...` (and
`AuditService.get_decisions_by_user`) will silently miss historical
entries — both filter on the structured column.

Migration `087_backfill_actor_user_id_audit_logs` walks the legacy rows,
extracts the id from `reasoning`, and writes it into the column.

## How to run in production

The backfill is just a regular Alembic step, so it goes through the same
path as any other schema change:

```bash
cd lia-agent-system
alembic upgrade head
```

Single-step variant (only this revision, e.g. running it in isolation
for verification):

```bash
cd lia-agent-system
alembic upgrade 087_backfill_actor_user_id_audit_logs
```

Expected log line on first run (omitted when there is nothing to do):

```
[087] audit_logs.actor_user_id: backfilled <N> rows from reasoning[]
```

## Idempotency

Re-running the backfill is safe. The `UPDATE` is gated by
`actor_user_id IS NULL`, so rows that already have a value (either from
the original caller or from a previous run of this migration) are
skipped. Running `alembic upgrade head` repeatedly is a no-op once the
backlog is drained.

## Spot-check after running

```sql
-- Should be 0 once the backfill has completed.
-- The CASE wrapper mirrors the migration: it makes the lateral
-- expansion safe even when reasoning is NULL or not a JSON array.
SELECT COUNT(*)
FROM audit_logs
WHERE actor_user_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements_text(
          CASE
              WHEN reasoning IS NOT NULL
               AND jsonb_typeof(reasoning::jsonb) = 'array'
              THEN reasoning::jsonb
              ELSE '[]'::jsonb
          END
      ) AS elem
      WHERE elem LIKE 'actor_user_id=%'
  );
```

Any non-zero count there represents rows whose `reasoning` carries an
ill-formed token (empty value after the `=`); they are intentionally
left alone.

## Rollback

`alembic downgrade 086_add_job_readiness_columns` clears
`actor_user_id` only on rows whose `reasoning` still contains an
`actor_user_id=` token (i.e. rows that received their value from this
backfill). Rows that the caller persisted as a structured value from the
beginning are preserved.
