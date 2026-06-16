#!/usr/bin/env python3
"""
Sensor: check_lia_entity_annotations.py
Audits which candidate-name-rendering surfaces have data-lia-entity-id/type/label
and which don't. Anti-ghost for seleção contextual Fase 3.

Exit 0 (warn-only). Add --blocking for CI gate.
"""

import os
import re
import sys
import argparse
from pathlib import Path

ROOT = Path('/home/runner/workspace/plataforma-lia/src')

# Surfaces that render candidate names directly — expected to have annotation
EXPECTED_ANNOTATED = [
    'components/pages/job-kanban/KanbanColumnRenderer.tsx',      # kanban card h4
    'components/pages/candidates/CandidateTableCellRenderer.tsx', # bank table span
]

# Surfaces that render candidate names but annotation is deferred (lower priority)
DEFERRED = [
    'components/pages/candidates/CandidatePreviewPanel.tsx',
    'app/[locale]/recrutar/',
    'app/[locale]/bancos/',
]

ANNOTATION_PATTERN = re.compile(r'data-lia-entity-type\s*=\s*["\']candidate["\']')
CANDIDATE_NAME_PATTERN = re.compile(r'candidate\.name|candidateName|candidate\?\.name')

def check_file(rel_path: str) -> tuple[bool, str]:
    """Returns (has_annotation, reason)"""
    full = ROOT / rel_path
    if not full.exists():
        return False, 'FILE_NOT_FOUND'
    content = full.read_text()
    if ANNOTATION_PATTERN.search(content):
        return True, 'OK'
    if CANDIDATE_NAME_PATTERN.search(content):
        return False, 'MISSING_ANNOTATION'
    return True, 'NO_CANDIDATE_NAME'  # no annotation needed

def scan_unannotated() -> list[str]:
    """Find .tsx files that render candidate names without annotation."""
    results = []
    for path in ROOT.rglob('*.tsx'):
        if any(skip in str(path) for skip in ('__tests__', 'node_modules', '.next', 'triagem', 'shared')):
            continue
        content = path.read_text(errors='replace')
        if CANDIDATE_NAME_PATTERN.search(content) and not ANNOTATION_PATTERN.search(content):
            rel = str(path.relative_to(ROOT))
            # Filter noise: only files that likely render visual candidate names
            if any(kw in rel for kw in ('Candidate', 'candidate', 'Kanban', 'kanban', 'Talent', 'talent', 'Profile', 'profile')):
                results.append(rel)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blocking', action='store_true')
    args = parser.parse_args()

    print('=== Sensor: data-lia-entity annotation coverage ===\n')
    violations = 0

    print('[REQUIRED — must be annotated]')
    for rel in EXPECTED_ANNOTATED:
        ok, reason = check_file(rel)
        status = '✅' if ok else '❌'
        print(f'  {status} {rel} ({reason})')
        if not ok:
            violations += 1
            print(f'     → Fix: add data-lia-entity-type="candidate" data-lia-entity-id={{candidate.id}} data-lia-entity-label={{candidate.name}} to the name element')

    print('\n[UNANNOTATED surfaces (candidate name present, no annotation)]')
    unannotated = scan_unannotated()
    deferred = [u for u in unannotated if any(d in u for d in ['PreviewPanel', 'ProfilePage', 'bancos', 'recrutar', 'TalentPool'])]
    new_gaps = [u for u in unannotated if u not in deferred]

    for u in deferred:
        print(f'  ⏳ {u} (deferred — Phase 3 follow-up)')

    for u in new_gaps:
        print(f'  ⚠️  {u} (unannotated — consider adding)')

    print(f'\nSummary: {violations} required violations | {len(deferred)} deferred | {len(new_gaps)} optional gaps')

    if args.blocking and violations > 0:
        print(f'\n❌ BLOCKING: {violations} required annotation(s) missing')
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
