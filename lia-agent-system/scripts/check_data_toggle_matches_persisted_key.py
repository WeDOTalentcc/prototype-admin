#!/usr/bin/env python3
"""Sensor canonical: check_data_toggle_matches_persisted_key.

Wave 4 audit 2026-05-22 — closes naming-mismatch ghost-toggle class.

Background
──────────
Multiple UI <input data-toggle="X" /> attributes were observed to NOT
match any backend Python column / Pydantic field. Symptom: UI shows a
toggle the user can flip, but no backend code reads the value because
the persistence layer uses a DIFFERENT name. Net effect: ghost setting
(user customizes something inert).

Canonical example caught by initial run (2026-05-22):
- UI: AlertsTab.tsx:226 has ``data-toggle="weekly_digest_enabled"``.
- Backend: ``digest.py:122`` reads ``prefs.get("weekly_report_enabled")``.
- Pydantic schema: ``proxy.schema.ts:54`` and the proxy route both use
  ``weekly_report_enabled``.

Result: UI toggle for "weekly digest" persisted nowhere visible to the
backend service that actually sends the digest. Classic LGPD-adjacent
trust-break (cliente acredita customizar, mas nada acontece — vide ADR
"lia_field_toggles canonical pattern" em CLAUDE.md, 2026-05-21).

Strategy
────────
1. Parse all ``.tsx`` / ``.ts`` under ``plataforma-lia/`` for
   ``data-toggle="<literal>"`` attributes (regex). Literals only —
   ``data-toggle={dynamic}`` is skipped (cannot be statically validated).
2. Collect persistence-layer name space:
   - Python: SQLAlchemy ``Column`` declarations (model field names) +
     Pydantic field annotations (assignments inside BaseModel subclasses).
   - TypeScript: Zod schema field names (``z.object({...})``).
3. For each data-toggle literal, check membership in the persistence
   name space (case-sensitive). If absent, look for fuzzy matches
   (Levenshtein distance <= 2) to suggest likely typos.

Exit codes
──────────
- 0 with success message: no mismatches.
- 0 with warn output (``--warn-only``): mismatches reported, exit 0.
- 1: mismatches found and NOT in ``--warn-only`` mode.

Escape hatch
────────────
Two ways to whitelist a legitimate UI-only data-toggle (e.g., pure
client-side UI state with no backend persistence, or UI-namespaced label
whose payload uses a different canonical name):

1. Inline comment — add ``// DATA-TOGGLE-EXEMPT: <ticket>:<reason>`` on
   the same line as ``data-toggle="X"``. Works well for plain `.ts`
   files. Inside JSX/TSX attributes the inline comment is awkward and
   often re-formatted by Prettier — prefer option 2.

2. Whitelist file — list ``<repo-rel-path>:<toggle>:<reason>`` entries
   in ``scripts/whitelists/data_toggle_exempt.txt`` (one per line,
   ``#`` comments and blank lines ignored). Path is relative to the
   workspace root. The reason field is mandatory and audit-trail.

Usage
─────
    python scripts/check_data_toggle_matches_persisted_key.py
    python scripts/check_data_toggle_matches_persisted_key.py --warn-only

Output otimizado para consumo de LLM: cada violação inclui path:linha,
toggle name, e suggestion de fix com o nome correto (se houver fuzzy
match óbvio).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent  # lia-agent-system/
# Frontend lives at sibling repo plataforma-lia/ when running from Replit
# workspace. Walk up one more for /home/runner/workspace/.
WORKSPACE_ROOT = REPO_ROOT.parent
FRONTEND_ROOT = WORKSPACE_ROOT / "plataforma-lia" / "src"
BACKEND_PY_ROOTS = [
    REPO_ROOT / "app",
    REPO_ROOT / "libs" / "models",
]

DATA_TOGGLE_RE = re.compile(r'data-toggle="([A-Za-z_][A-Za-z0-9_]*)"')
EXEMPT_MARKER_RE = re.compile(r"//\s*DATA-TOGGLE-EXEMPT\b")

WHITELIST_FILE = REPO_ROOT / "scripts" / "whitelists" / "data_toggle_exempt.txt"

# Python: SQLAlchemy Column declarations look like `name = Column(...)` and
# Pydantic fields look like `name: type = Field(...)` or `name: type`.
PY_COLUMN_RE = re.compile(
    r"^\s*([a-z_][a-z0-9_]*)\s*=\s*Column\b", re.MULTILINE
)
PY_PYDANTIC_FIELD_RE = re.compile(
    # field_name: SomeType = Field(...)  OR  field_name: SomeType
    r"^\s{4}([a-z_][a-z0-9_]*)\s*:\s*[^=\n]+\s*(?:=\s*Field|=\s*[^,\n]+)?$",
    re.MULTILINE,
)

# TypeScript Zod: `field_name: z.something()` inside z.object({...}).
TS_ZOD_FIELD_RE = re.compile(
    r"^\s*([a-z_][a-z0-9_]*)\s*:\s*z\.", re.MULTILINE
)

SKIP_DIRS = {"__pycache__", "node_modules", ".next", "dist", "build", "alembic"}


def _walk(root: Path, suffixes: set[str]):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes:
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            yield path


def collect_persistence_names() -> set[str]:
    """Aggregate field names from backend persistence layers."""
    names: set[str] = set()

    # Python — SQLAlchemy + Pydantic
    for root in BACKEND_PY_ROOTS:
        for py in _walk(root, {".py"}):
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            names.update(PY_COLUMN_RE.findall(text))
            names.update(PY_PYDANTIC_FIELD_RE.findall(text))

    # TypeScript Zod schemas in frontend src/lib/schemas + anywhere else
    if FRONTEND_ROOT.exists():
        for ts in _walk(FRONTEND_ROOT, {".ts", ".tsx"}):
            try:
                text = ts.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            names.update(TS_ZOD_FIELD_RE.findall(text))

    return names


def collect_data_toggles() -> list[tuple[Path, int, str]]:
    """Find every ``data-toggle="..."`` literal in the frontend."""
    found: list[tuple[Path, int, str]] = []
    if not FRONTEND_ROOT.exists():
        return found
    for tsx in _walk(FRONTEND_ROOT, {".tsx", ".ts"}):
        try:
            lines = tsx.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            if EXEMPT_MARKER_RE.search(line):
                continue
            for match in DATA_TOGGLE_RE.finditer(line):
                found.append((tsx, i, match.group(1)))
    return found


def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance between two short strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr[j] = min(ins, dele, sub)
        prev = curr
    return prev[-1]


def find_fuzzy_match(toggle: str, names: set[str], max_distance: int = 2) -> str | None:
    """Return best candidate (lowest Levenshtein <= max_distance), if any."""
    best: tuple[int, str] | None = None
    for candidate in names:
        d = levenshtein(toggle, candidate)
        if d == 0:
            continue
        if d <= max_distance and (best is None or d < best[0]):
            best = (d, candidate)
    return best[1] if best else None


def load_whitelist() -> set[tuple[str, str]]:
    """Load file-based whitelist entries.

    Returns a set of ``(workspace_relative_path, toggle_name)`` tuples.
    Format per line: ``<rel-path>:<toggle>:<reason>``. ``#``-prefixed
    and blank lines are ignored. The reason is parsed but currently
    unused programatically; it exists for audit-trail.
    """
    entries: set[tuple[str, str]] = set()
    if not WHITELIST_FILE.exists():
        return entries
    try:
        text = WHITELIST_FILE.read_text(encoding="utf-8")
    except OSError:
        return entries
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        rel_path = parts[0].strip()
        toggle = parts[1].strip()
        if rel_path and toggle:
            entries.add((rel_path, toggle))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print violations but exit 0 (ratchet mode).",
    )
    parser.add_argument(
        "--baseline-file",
        type=str,
        default=None,
        help=(
            "Path to a baseline file containing the max expected violation "
            "count. Sensor exits 1 only when current count exceeds baseline "
            "(ratchet-up gate)."
        ),
    )
    args = parser.parse_args()

    names = collect_persistence_names()
    toggles = collect_data_toggles()
    whitelist = load_whitelist()

    if not toggles:
        print("OK no data-toggle literals scanned (frontend tree missing?)")
        return 0

    mismatches: list[tuple[Path, int, str, str | None]] = []
    exempt_count = 0
    for path, lineno, toggle in toggles:
        if toggle in names:
            continue
        # File-based whitelist (workspace-relative path + toggle name).
        try:
            rel_str = str(path.relative_to(WORKSPACE_ROOT))
        except ValueError:
            rel_str = str(path)
        if (rel_str, toggle) in whitelist:
            exempt_count += 1
            continue
        suggestion = find_fuzzy_match(toggle, names)
        mismatches.append((path, lineno, toggle, suggestion))

    if not mismatches:
        suffix = (
            f" ({exempt_count} whitelisted as UI-only)" if exempt_count else ""
        )
        print(
            f"OK all {len(toggles)} data-toggle literals match a backend "
            f"field{suffix}"
        )
        return 0

    workspace = WORKSPACE_ROOT
    print(
        f"VIOLATIONS: {len(mismatches)} data-toggle literal(s) without matching "
        f"backend field (out of {len(toggles)} scanned)"
    )
    for path, lineno, toggle, suggestion in mismatches:
        try:
            rel = path.relative_to(workspace)
        except ValueError:
            rel = path
        print(f"  {rel}:{lineno}")
        print(f"    toggle: data-toggle=\"{toggle}\"")
        if suggestion:
            print(f"    suggested fix: rename to data-toggle=\"{suggestion}\"")
        else:
            print(
                "    no fuzzy match found — either add the backend field, "
                "or whitelist via inline // DATA-TOGGLE-EXEMPT: <ticket>:<reason> "
                "or scripts/whitelists/data_toggle_exempt.txt entry"
            )

    print()
    print("Canonical: every data-toggle attr persisted by UI MUST match a")
    print("backend column / Pydantic field / Zod schema field. Ghost toggles")
    print("break user trust (vide CLAUDE.md 'lia_field_toggles canonical pattern').")

    # Baseline-file ratchet: exit 1 only when current > baseline (new offenders).
    if args.baseline_file:
        try:
            with open(args.baseline_file) as fh:
                baseline = int(fh.read().strip().splitlines()[0])
        except FileNotFoundError:
            print(
                f"\nbaseline file not found at {args.baseline_file} — "
                "skipping ratchet gate (treat as warn-only)."
            )
            return 0
        except (ValueError, IndexError):
            print(
                f"\nbaseline file at {args.baseline_file} is not a single "
                "integer on the first line — skipping ratchet gate."
            )
            return 0
        current = len(mismatches)
        if current > baseline:
            print(
                f"\nratchet: {current} violations > baseline {baseline}. "
                f"Reduce to <= {baseline} or fix the new offender(s) above."
            )
            return 1
        print(
            f"\nratchet: {current} violations <= baseline {baseline} — OK "
            "(consider lowering baseline if you closed some)."
        )
        return 0

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
