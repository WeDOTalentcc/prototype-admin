#!/usr/bin/env python3
"""
Sensor R1 v2 — class-based VacancyCandidate stage write detector.

Invariant: every write to stage / recruitment_stage_id / status (VC-specific
values) on VacancyCandidate instances MUST go through
pipeline_stage_service.transition_candidate().

v1: SET-stage SQL substring, bulk_update_candidate_stage literal,
    sa_update(VacancyCandidate) regex — exempt FILE-LEVEL.
v2: adds ORM attribute assignment via AST (Pattern 4/5),
    changes exempt to MATCH-LEVEL (marker on same or preceding line only).

Usage:
  python check_transition_uses_canonical_service.py
  python check_transition_uses_canonical_service.py --warn-only
  python check_transition_uses_canonical_service.py --write-baseline FILE
  python check_transition_uses_canonical_service.py --baseline FILE
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
APP_DIR = REPO_ROOT / "app"

# Files/paths exempt unconditionally (the canonical service itself + known FPs)
ALWAYS_EXEMPT_PARTS = [
    "pipeline_stage_service.py",          # canonical service — writes are authoritative
    "recruiter_metrics_repository.py",     # pre-existing legacy exempt
    "check_transition_uses_canonical_service.py",  # this file
    "wsi_interview_graph.py",             # WSI state machine (.stage = WSIInterviewStage.X)
    "__pycache__",
]

# VacancyCandidate ORM field names that constitute a stage-transition write
STAGE_FIELDS = frozenset({"stage", "recruitment_stage_id"})

# .status values specific to VacancyCandidate pipeline progression
VC_STATUS_VALUES = frozenset({
    "hired", "sourced", "in_review", "offer", "rejected", "dropout",
    "Contratado", "reprovado", "descartado", "qualified", "disqualified",
    "screening", "rejected_screening", "awaiting_screening",
})

# Markers for match-level exempt (same or preceding line)
EXEMPT_MARKERS = ("R1-EXEMPT", "ADR-001-EXEMPT")

VC_IMPORT_MARKER = "VacancyCandidate"
VC_BULK_RE = re.compile(r"(?:sa_update|update)\s*\(\s*VacancyCandidate\s*\)")


def _is_always_exempt(fpath: Path) -> bool:
    fstr = str(fpath)
    return any(part in fstr for part in ALWAYS_EXEMPT_PARTS)


def _has_vc_in_scope(content: str) -> bool:
    return VC_IMPORT_MARKER in content


def _has_match_exempt(lines: list[str], lineno: int) -> bool:
    """Match-level: marker must be on the flagged line OR the immediately preceding line."""
    idx = lineno - 1  # 0-based
    for i in (idx, idx - 1):
        if 0 <= i < len(lines) and any(m in lines[i] for m in EXEMPT_MARKERS):
            return True
    return False


class _StageWriteVisitor(ast.NodeVisitor):
    """AST visitor: collect ORM writes to stage/recruitment_stage_id/status."""

    def __init__(self, lines: list[str]) -> None:
        self.violations: list[tuple[int, str]] = []
        self._lines = lines

    def _check(self, lineno: int, attr: str, value_node: ast.expr | None) -> None:
        if attr in STAGE_FIELDS:
            # FP filter: skip enum-like attribute values (e.g. WSIInterviewStage.X)
            if isinstance(value_node, ast.Attribute):
                return
        elif attr == "status":
            # Only flag when value is a known VC status string constant
            if not (
                isinstance(value_node, ast.Constant)
                and isinstance(value_node.value, str)
                and value_node.value in VC_STATUS_VALUES
            ):
                return
        else:
            return  # not a monitored field

        if not _has_match_exempt(self._lines, lineno):
            self.violations.append((lineno, attr))

    def visit_Assign(self, node: ast.Assign) -> None:  # type: ignore[override]
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)  # simple obj.field, not obj.sub.field
            ):
                self._check(node.lineno, target.attr, node.value)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:  # type: ignore[override]
        if (
            isinstance(node.target, ast.Attribute)
            and isinstance(node.target.value, ast.Name)
        ):
            self._check(node.lineno, node.target.attr, None)
        self.generic_visit(node)


def _scan_file(fpath: Path) -> list[dict]:
    violations: list[dict] = []
    try:
        content = fpath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return violations
    lines = content.splitlines()
    rel = str(fpath.relative_to(REPO_ROOT))

    # Pattern 1 — raw SQL UPDATE on vacancy_candidates stage fields
    SQL_SET_RE = re.compile(
        r"SET\s+(?:stage|recruitment_stage_id|status)\b", re.IGNORECASE
    )
    if "vacancy_candidates" in content:
        for i, line in enumerate(lines, 1):
            if "vacancy_candidates" in line.lower() and SQL_SET_RE.search(line):
                if not _has_match_exempt(lines, i):
                    violations.append({
                        "file": rel, "line": i,
                        "pattern": "P1-raw-sql",
                        "snippet": line.strip(),
                    })

    # Pattern 2 — named bypass function
    if "bulk_update_candidate_stage" in content:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "bulk_update_candidate_stage" in line and not stripped.startswith("def "):
                if not _has_match_exempt(lines, i):
                    violations.append({
                        "file": rel, "line": i,
                        "pattern": "P2-named-bypass",
                        "snippet": stripped,
                    })

    # Pattern 3 — SQLAlchemy Core bulk update
    if VC_BULK_RE.search(content):
        for i, line in enumerate(lines, 1):
            if VC_BULK_RE.search(line):
                if not _has_match_exempt(lines, i):
                    violations.append({
                        "file": rel, "line": i,
                        "pattern": "P3-core-update",
                        "snippet": line.strip(),
                    })

    # Patterns 4/5 — AST ORM assignment (only in VC-importing files)
    if _has_vc_in_scope(content):
        try:
            tree = ast.parse(content, filename=str(fpath))
        except SyntaxError:
            return violations
        visitor = _StageWriteVisitor(lines)
        visitor.visit(tree)
        for lineno, field in visitor.violations:
            snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            violations.append({
                "file": rel, "line": lineno,
                "pattern": f"P4-orm-assign(.{field})",
                "snippet": snippet,
            })

    return violations


def _build_violation_key(v: dict) -> tuple:
    return (v["file"], v["line"], v["pattern"])


def main() -> int:
    warn_only = "--warn-only" in sys.argv
    write_baseline: Path | None = None
    baseline_path: Path | None = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--write-baseline" and i + 1 < len(args):
            write_baseline = Path(args[i + 1]); i += 2
        elif args[i] == "--baseline" and i + 1 < len(args):
            baseline_path = Path(args[i + 1]); i += 2
        else:
            i += 1

    all_files = sorted(APP_DIR.rglob("*.py"))
    scanned = 0
    all_violations: list[dict] = []
    for fpath in all_files:
        if _is_always_exempt(fpath):
            continue
        scanned += 1
        all_violations.extend(_scan_file(fpath))

    if write_baseline:
        write_baseline.parent.mkdir(parents=True, exist_ok=True)
        with open(write_baseline, "w") as f:
            json.dump(all_violations, f, indent=2)
        print(f"Baseline written: {write_baseline} ({len(all_violations)} violations)")
        return 0

    if not all_violations:
        print(f"✅ Sensor R1 v2: 0 violations ({scanned} files checked)")
        return 0

    print(f"❌ Sensor R1 v2: {len(all_violations)} violation(s) found\n")

    if baseline_path and baseline_path.exists():
        with open(baseline_path) as f:
            baseline = json.load(f)
        known_keys = {_build_violation_key(b) for b in baseline}
        new_violations = [v for v in all_violations if _build_violation_key(v) not in known_keys]

        print(f"  Known (baseline): {len(baseline)}")
        print(f"  Found total:      {len(all_violations)}")
        print(f"  NEW (unbaseline): {len(new_violations)}\n")

        for v in all_violations:
            tag = "NEW" if _build_violation_key(v) not in known_keys else "PIN"
            print(f"  {tag} [{v['file']}:{v['line']}] {v['pattern']}")
            print(f"      {v['snippet']}")
            guide = (
                "-> Use pipeline_stage_service.transition_candidate() or add\n"
                "      # R1-EXEMPT: <reason> <ticket> on the preceding line"
            )
            print(f"      {guide}")
        if new_violations:
            print(f"\n NEW {len(new_violations)} NEW violation(s) outside baseline -- fix or baseline first")
            return 0 if warn_only else 1
        print(f"\n  All {len(all_violations)} violation(s) are in baseline. No regressions.")
        return 0

    # No baseline -- print all violations
    for v in all_violations:
        print(f"  [{v['file']}:{v['line']}] {v['pattern']}")
        print(f"      {v['snippet']}")
        print(f"      -> Use pipeline_stage_service.transition_candidate() or add")
        print(f"        # R1-EXEMPT: <reason> <ticket> on the preceding line")

    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
