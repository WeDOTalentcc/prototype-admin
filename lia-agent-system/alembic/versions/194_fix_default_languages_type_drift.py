"""fix(schema-drift): company_culture_profiles.default_languages jsonb -> varchar[]

Bug: SQLAlchemy ORM declares default_languages = Column(ARRAY(String)) but the
live Postgres column was created as jsonb (acknowledged in migration 130, lines
104-105). Any cold-start INSERT (tenant with no culture profile yet) fails with:
  asyncpg.exceptions.DatatypeMismatchError: column "default_languages" is of type
  jsonb but expression is of type character varying[]

This blocked every first-save attempt in Configuracoes -> Minha Empresa -> Cultura
& EVP for tenants with empty profiles (all fields showing "Nao definido").

Root cause: migration 130 set server_default correctly but skipped the column type.
This migration aligns the DB with the ORM (source of truth = code).

Approach: add temp column -> UPDATE correlated subquery (Postgres allows this,
unlike subquery in ALTER COLUMN ... USING) -> drop old -> rename.

Data formats found in production (verified 2026-05-25):
  - jsonb string arrays: ["Portugues", "Ingles"]                      -> preserved
  - jsonb object arrays: [{"code": "pt-BR", "label": "Portugues"}]    -> extracts label/code
"""
from alembic import op
from sqlalchemy import text

revision = "194"
down_revision = "193"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add temp column with correct type
    conn.execute(text("""
        ALTER TABLE company_culture_profiles
        ADD COLUMN default_languages_new character varying[] NOT NULL DEFAULT '{}'
    """))

    # 2. Populate via correlated UPDATE (subquery in SET is allowed; USING is not)
    #    Handles both pure-string jsonb arrays and legacy object arrays.
    #    array_agg of empty array returns NULL -> coalesce to '{}'
    conn.execute(text("""
        UPDATE company_culture_profiles
        SET default_languages_new = COALESCE(
            (
                SELECT array_agg(
                    CASE
                        WHEN jsonb_typeof(e) = 'string' THEN e#>>'{}'
                        ELSE COALESCE(e->>'label', e->>'code', e#>>'{}')
                    END
                )
                FROM jsonb_array_elements(default_languages) AS e
            ),
            '{}'::character varying[]
        )
    """))

    # 3. Drop old jsonb column, rename temp to canonical name
    conn.execute(text(
        "ALTER TABLE company_culture_profiles DROP COLUMN default_languages"
    ))
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "RENAME COLUMN default_languages_new TO default_languages"
    ))

    # 4. Restore DEFAULT (was set on temp column, explicit set on final name)
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "ALTER COLUMN default_languages SET DEFAULT '{}'"
    ))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(text("""
        ALTER TABLE company_culture_profiles
        ADD COLUMN default_languages_old jsonb NOT NULL DEFAULT '[]'::jsonb
    """))
    conn.execute(text("""
        UPDATE company_culture_profiles
        SET default_languages_old = to_jsonb(default_languages)
    """))
    conn.execute(text(
        "ALTER TABLE company_culture_profiles DROP COLUMN default_languages"
    ))
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "RENAME COLUMN default_languages_old TO default_languages"
    ))
    conn.execute(text(
        "ALTER TABLE company_culture_profiles "
        "ALTER COLUMN default_languages SET DEFAULT '[]'::jsonb"
    ))
