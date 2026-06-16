# ComplianceReporter — Specification

Generated: 2026-05-02
Implemented in: UC-P1-12
File: `app/domains/compliance/services/compliance_reporter.py`
API endpoint: `app/api/v1/compliance_report.py`

---

## Purpose

`ComplianceReporter` aggregates five compliance dimensions for a given company and date range
into a single report payload. Used by compliance officers, internal audits, and the Trust Center.

---

## What It Aggregates

| Dimension | Source | Description |
|-----------|--------|-------------|
| `bias_summary` | Rails adapter (`RailsAdapter.get_bias_audit_snapshot_history`) | Last 5 bias audit snapshots for the company |
| `fairness_summary` | `SOXAuditLog` (Postgres) | Count of fairness-related audit events in the period |
| `audit_log_count` | `SOXAuditLog` (Postgres) | Total audit log entries for the company |
| `consent_summary` | `ConsentVersion` (Postgres) | Total consent versions on record |
| `retention_status` | `Candidate` table (Postgres) | Count of candidates with overdue scheduled deletion |

---

## API Endpoint

```
GET /api/v1/compliance/report
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_id` | string (UUID) | Yes | Company to generate report for |
| `from_date` | date (YYYY-MM-DD) | Yes | Report period start |
| `to_date` | date (YYYY-MM-DD) | Yes | Report period end |

### Authentication

Requires admin role (`require_admin` dependency). JWT must have `role: admin`.

### Example Request

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://api.wedotalent.cc/api/v1/compliance/report?company_id=abc-123&from_date=2026-04-01&to_date=2026-04-30"
```

---

## Output Format

```json
{
  "status": "ok",
  "data": {
    "company_id": "abc-123",
    "period": { "from": "2026-04-01", "to": "2026-04-30" },
    "generated_at": "2026-05-02T10:00:00",
    "bias_summary": {
      "snapshots": [ ... ],
      "source": "rails_adapter"
    },
    "fairness_summary": {
      "fairness_events": 12,
      "source": "sox_audit_log"
    },
    "audit_log_count": 1042,
    "consent_summary": {
      "consent_versions": 3,
      "source": "consent_version_table"
    },
    "retention_status": {
      "pending_deletion": 0,
      "source": "candidate_table"
    }
  },
  "meta": { "company_id": "abc-123" }
}
```

---

## How to Run

### Via API
See example request above.

### Programmatically (in a background task or script)

```python
from app.domains.compliance.services.compliance_reporter import ComplianceReporter
from datetime import date

async def run_report(db, company_id: str):
    reporter = ComplianceReporter(db=db)
    return await reporter.generate_report(
        company_id=company_id,
        from_date=date(2026, 4, 1),
        to_date=date(2026, 4, 30),
    )
```

---

## Error Handling

Each dimension is wrapped in a try/except. If a data source is unavailable, the dimension
returns `{"source": "unavailable", "error": "..."}` — the overall report still returns 200.
This allows partial reports during partial outages.

---

## Frequency Recommendation

| Use Case | Recommended Frequency |
|----------|----------------------|
| LGPD quarterly audit | Monthly, last day of month |
| Compliance dashboard refresh | Daily (can be cached 24h) |
| Incident investigation | On-demand |
| EU AI Act FRIA evidence | Before each major model update |

---

## Known Limitations

1. `consent_summary` does not filter by company — returns global `ConsentVersion` count (fix in backlog).
2. `fairness_summary` counts SOXAuditLog entries with `action ILIKE '%fairness%'` — low precision.
3. `bias_summary` is limited to last 5 snapshots regardless of date range (Rails adapter constraint).
