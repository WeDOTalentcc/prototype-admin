# Ownership: `triagem_sessions`, `triagem_messages`, `voice_screening_*`

## Source of truth

These tables are **owned by the Python lia-agent-system** (FastAPI), not by the
Rails ATS API. The live schema in `heliumdb` is generated from the SQLAlchemy
models below and should be treated as the canonical definition:

| Tabela | Modelo SQLAlchemy |
|---|---|
| `triagem_sessions` | `lia-agent-system/libs/models/lia_models/triagem.py` → `TriagemSession` |
| `triagem_messages` | `lia-agent-system/libs/models/lia_models/triagem.py` → `TriagemMessage` |
| `voice_screening_calls` | `lia-agent-system/libs/models/lia_models/voice_screening.py` → `VoiceScreeningCall` |
| `voice_screening_analyses` | `lia-agent-system/libs/models/lia_models/voice_screening.py` (related models) |

The auto-generated reference docs `docs/DATABASE_SCHEMA.md` and
`docs/DATABASE_SCHEMA_ACTIVE.md` are produced from these Python models and match
the live database.

## How Rails should interact

The Rails app (`ats-api-copia`) **must not** create, alter or drop these
tables. There used to be a divergent migration
`ats-api-copia/db/migrate/20250716000045_create_triagem_and_voice.rb` that
defined a completely different schema (e.g. `current_question_idx`,
`total_questions`, `progress`, `final_score`); that file has been removed
because it was never reflected in `db/schema.rb` and never matched the live
database. The bug investigated in task #426 (recruiter modal reading from
`wsi_*` instead of those non-existent fields) was a direct consequence of that
divergence.

If Rails ever needs to read triagem data, it should query the Python-owned
tables read-only using the column names defined in the SQLAlchemy models (e.g.
`token`, `current_block`, `total_blocks`, `wsi_final_score`,
`recommendation`, `voice_mode`, `expires_at`, `metadata_json`). All writes go
through the Python API.

## Schema changes

Any change to the columns/indexes of these tables must be done as an Alembic
migration under `lia-agent-system/alembic/versions/` and reflected in the
SQLAlchemy model. Do not add a Rails migration for the same table.
