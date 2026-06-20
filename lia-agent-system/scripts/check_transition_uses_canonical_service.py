#!/usr/bin/env python3
"""
Sensor R1 — Canonical transition service enforcement.

Checks that every Python file that touches VacancyCandidate.stage (writes)
imports and uses PipelineStageService.transition_candidate, not raw SQL or
repository bulk updates.

Honors # ADR-001-EXEMPT marker in the same file.

Exit 1 if violations found (blocking).
"""
import sys
import re as _re
from pathlib import Path

VIOLATIONS = []

# Files unconditionally exempt (the canonical service itself, scripts, tests)
ALWAYS_EXEMPT = [
    'pipeline_stage_service.py',
    'recruiter_metrics_repository.py',
    'check_transition_uses_canonical_service.py',
    '__pycache__',
]

def _is_always_exempt(fpath: Path) -> bool:
    fstr = str(fpath)
    return any(e in fstr for e in ALWAYS_EXEMPT)

root = Path(__file__).parent.parent
service_files = list(root.glob('app/**/*.py'))

_VC_BULK = _re.compile(r'sa_update\s*\(\s*VacancyCandidate\s*\)')

for fpath in service_files:
    if _is_always_exempt(fpath):
        continue
    try:
        content = fpath.read_text(errors='replace')
    except Exception:
        continue

    has_exempt = 'ADR-001-EXEMPT' in content or 'R1-EXEMPT' in content

    fp = str(fpath.relative_to(root))

    # Pattern 1 — raw SQL UPDATE on vacancy_candidates.stage bypasses canonical service
    if ('SET stage' in content and 'vacancy_candidates' in content and not has_exempt):
        VIOLATIONS.append(
            f"  [{fp}] raw SQL stage write — add ADR-001-EXEMPT or migrate to pipeline_stage_service"
        )

    # Pattern 2 — bulk_update_candidate_stage repository bypass
    if 'bulk_update_candidate_stage' in content and not has_exempt:
        VIOLATIONS.append(
            f"  [{fp}] bulk_update_candidate_stage bypass — add ADR-001-EXEMPT or migrate to pipeline_stage_service"
        )

    # Pattern 3 — SQLAlchemy Core bulk update on VacancyCandidate bypasses canonical service
    if _VC_BULK.search(content) and not has_exempt:
        VIOLATIONS.append(
            f"  [{fp}] sa_update(VacancyCandidate) detected — raw Core update bypasses "
            f"pipeline_stage_service.transition_candidate() (P-SSOT). "
            f"Use canonical service or add # R1-EXEMPT: <reason>"
        )

if VIOLATIONS:
    print("❌ Sensor R1: canonical transition bypass detected:")
    for v in VIOLATIONS:
        print(v)
    print()
    print("→ Fix: use pipeline_stage_service.transition_candidate() instead of direct SQL/repo writes")
    print("→ If intentional legacy: add '# ADR-001-EXEMPT: <reason>' comment to the file")
    sys.exit(1)
else:
    print(f"✅ Sensor R1: all stage writes use canonical service or have ADR-001-EXEMPT ({len(service_files)} files checked)")
    sys.exit(0)
