# Rails Boundary — Cross-Boundary Writes to Rails-owned Tables

Rails canonical backend (`ats-api-copia/`) owns tables `candidates` and `messages`.
LIA (FastAPI) has SQLAlchemy models mirroring them for legitimate LGPD and conversation lifecycle paths.
All write paths require an inline `# ADR-001-EXEMPT: Rails-owned <Table> — <reason>` marker.

## Rails-owned tables

| Table | LIA Model | File | LIA write justification |
|-------|-----------|------|-------------------------|
| `candidates` | `Candidate` | `libs/models/lia_models/candidate.py:95` | LGPD retention + erasure |
| `messages` | `Message` | `libs/models/lia_models/conversation.py:96` | Conversation lifecycle |

## Legitimate write paths

### 1. Candidate anonymization — LGPD Art. 16
- **File**: `app/jobs/tasks/compliance.py:~364`
- **Op**: `update(Candidate).values(name=None, email=None, phone=None, cpf=None, anonymized_at=...)`
- **Trigger**: Daily Celery task `lgpd.run_cleanup_daily`
- **Guard**: `company.auto_anonymize == True` + `created_at < cutoff`

### 2. Candidate erasure — LGPD Art. 18
- **File**: `app/domains/lgpd/services/lgpd_cleanup_service.py:~199`
- **Op**: `delete(Candidate).where(id.in_(...))`
- **Trigger**: `LgpdComplianceService.cleanup()` when `scheduled_deletion_at <= now`
- **Guard**: `scheduled_deletion_at IS NOT NULL`

### 3. Message cascade delete — conversation lifecycle
- **File**: `app/domains/recruiter_assistant/services/conversation_memory.py:~501`
- **Op**: `delete(Message).where(conversation_id == uuid)`
- **Trigger**: `delete_conversation()` — removes messages before Conversation record

### 4. Message reset — user-initiated clear
- **File**: `app/domains/recruiter_assistant/services/conversation_memory.py:~540`
- **Op**: `delete(Message).where(conversation_id == uuid)`
- **Trigger**: `clear_conversation()` — clears history, preserves Conversation metadata

## Prohibited patterns

- ❌ `INSERT INTO candidates` without LGPD compliance context
- ❌ `UPDATE candidates` beyond `{name, email, phone, cpf, linkedin_url, github_url, portfolio_url, photo_url, address, anonymized_at, anonymized_by}`
- ❌ Writing to `messages` outside conversation lifecycle
- ❌ Any cross-boundary write without `# ADR-001-EXEMPT` marker

## How to add a new cross-boundary write

1. Verify the write is architecturally necessary (LGPD compliance or lifecycle management).
2. Add `# ADR-001-EXEMPT: Rails-owned <Table> — <specific reason>` on the line immediately before the SQL operation.
3. Update this document with the new path.
4. Run `python scripts/check_rails_owned_writes.py` to verify compliance.

## Related

- ADR-001: Repository Pattern
- ADR-006: No PII in logs
- ADR-030: Postgres RLS baseline
- `scripts/check_rails_owned_writes.py` — sensor
