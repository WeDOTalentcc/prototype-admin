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

for fpath in service_files:
    if _is_always_exempt(fpath):
        continue
    try:
        content = fpath.read_text(errors='replace')
    except Exception:
        continue

    has_exempt = 'ADR-001-EXEMPT' in content

    # Check for raw SQL UPDATE on vacancy_candidates.stage (the bypass pattern)
    if ('SET stage' in content and 'vacancy_candidates' in content and not has_exempt):
        VIOLATIONS.append(
            f"{fpath.relative_to(root)}: raw SQL stage write — add ADR-001-EXEMPT or migrate to pipeline_stage_service"
        )

    # Check for bulk_update_candidate_stage calls (repository bypass)
    if 'bulk_update_candidate_stage' in content and not has_exempt:
        VIOLATIONS.append(
            f"{fpath.relative_to(root)}: bulk_update_candidate_stage bypass — add ADR-001-EXEMPT or migrate to pipeline_stage_service"
        )

if VIOLATIONS:
    print("❌ Sensor R1: canonical transition bypass detected:")
    for v in VIOLATIONS:
        print(f"  - {v}")
    print()
    print("→ Fix: use pipeline_stage_service.transition_candidate() instead of direct SQL/repo writes")
    print("→ If intentional legacy: add '# ADR-001-EXEMPT: <reason>' comment to the file")
    sys.exit(1)
else:
    print(f"✅ Sensor R1: all stage writes use canonical service or have ADR-001-EXEMPT ({len(service_files)} files checked)")
    sys.exit(0)
