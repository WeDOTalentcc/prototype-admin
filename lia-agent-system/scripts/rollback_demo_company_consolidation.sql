-- Rollback for Task #969 / T-C — restores the legacy 'demo_company' slug
-- row in `companies` and re-points all string company_id/tenant_id rows
-- back to the slug. Provided for emergency recovery only; once JWTs are
-- circulating the canonical UUID, downgrading will leave the auth layer
-- out of sync with the database (see migration 080 docstring).
--
-- Usage:
--   psql "$DATABASE_URL" -f scripts/rollback_demo_company_consolidation.sql
--
-- Pre-conditions:
--   - You have a fresh DB snapshot (this script is destructive).
--   - You understand that JWTs minted with the canonical UUID will fail
--     to resolve a company until they expire/rotate.

BEGIN;

-- 1. Reinsert the legacy slug row.
INSERT INTO companies (id, name, display_name, is_active, is_demo,
                       created_at, updated_at)
SELECT 'demo_company', name, display_name, is_active, is_demo,
       CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM companies
WHERE id = '00000000-0000-4000-a000-000000000001'
ON CONFLICT (id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;

-- 2. Defer the only string-FK cycle (company_modules <-> credit_accounts).
DO $$
DECLARE
    has_fk boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class cl ON cl.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = cl.relnamespace
        WHERE n.nspname='public'
          AND cl.relname='company_modules'
          AND c.conname='fk_company_modules_credit_accounts'
    ) INTO has_fk;
    IF has_fk THEN
        EXECUTE 'ALTER TABLE company_modules ALTER CONSTRAINT '
              || 'fk_company_modules_credit_accounts DEFERRABLE';
        SET CONSTRAINTS ALL DEFERRED;
    END IF;
END $$;

-- 3. Re-point every string company_id / tenant_id column.
DO $$
DECLARE
    rec RECORD;
    sql TEXT;
BEGIN
    FOR rec IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema='public'
          AND column_name IN ('company_id','tenant_id')
          AND data_type IN ('character varying','varchar','text','character')
          AND table_name <> 'companies'
    LOOP
        sql := format(
            'UPDATE %I SET %I = %L WHERE %I = %L',
            rec.table_name, rec.column_name, 'demo_company',
            rec.column_name, '00000000-0000-4000-a000-000000000001'
        );
        EXECUTE sql;
    END LOOP;
END $$;

-- 4. Restore FK immediacy.
DO $$
DECLARE
    has_fk boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class cl ON cl.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = cl.relnamespace
        WHERE n.nspname='public'
          AND cl.relname='company_modules'
          AND c.conname='fk_company_modules_credit_accounts'
    ) INTO has_fk;
    IF has_fk THEN
        SET CONSTRAINTS ALL IMMEDIATE;
        EXECUTE 'ALTER TABLE company_modules ALTER CONSTRAINT '
              || 'fk_company_modules_credit_accounts NOT DEFERRABLE';
    END IF;
END $$;

-- 5. Restore column DEFAULT clauses pinned to the canonical UUID back
--    to the legacy 'demo_company' literal. The forward consolidation
--    script rewrites every public.* column whose default LIKE
--    '%demo_company%' to the canonical UUID; without this step new
--    inserts after rollback would still try to reference the deleted
--    UUID row and break referential integrity at boot.
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_default IS NOT NULL
          AND column_default LIKE '%00000000-0000-4000-a000-000000000001%'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I ALTER COLUMN %I SET DEFAULT %L',
            rec.table_name, rec.column_name, 'demo_company'
        );
    END LOOP;
END $$;

-- 6. Drop the canonical UUID row (now no defaults reference it).
DELETE FROM companies WHERE id = '00000000-0000-4000-a000-000000000001';

-- 7. Drop the id-format CHECK constraint installed by migration 127
--    (the legacy 'demo_company' literal would otherwise be rejected
--    by the deny-list-aware constraint).
ALTER TABLE companies DROP CONSTRAINT IF EXISTS ck_companies_id_format_canonical;

COMMIT;
