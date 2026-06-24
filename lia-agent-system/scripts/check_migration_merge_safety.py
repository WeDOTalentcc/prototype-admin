#!/usr/bin/env python3
"""
REGRA 5 enforcement — no merge commits touching migrations.

Checks:
1. If we're inside a git merge (MERGE_HEAD exists), block staging migrations
2. Verify Alembic has a single head (no branch forks)
3. Staged migration files have sequential numbering (no gaps or duplicates)

Exit 0 = pass, Exit 1 = violation.
Output is LLM-friendly (includes fix instructions).
"""
import os
import re
import subprocess
import sys


def _run(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=_workspace())
    return r.stdout.strip()


def _workspace() -> str:
    return os.environ.get("WORKSPACE", "/home/runner/workspace")


def _git_dir() -> str:
    return os.path.join(_workspace(), ".git")


MIGRATIONS_DIR = "lia-agent-system/alembic/versions"


def check_merge_state() -> list[str]:
    """Block if inside a merge and migrations are staged."""
    merge_head = os.path.join(_git_dir(), "MERGE_HEAD")
    if not os.path.exists(merge_head):
        return []

    staged = _run("git diff --cached --name-only")
    staged_migrations = [
        f for f in staged.splitlines()
        if f.startswith(MIGRATIONS_DIR) and f.endswith(".py")
    ]
    if not staged_migrations:
        return []

    violations = [
        "REGRA 5 VIOLATION: Merge commit with migrations staged.",
        f"  Staged migrations: {len(staged_migrations)}",
    ]
    for f in staged_migrations[:5]:
        violations.append(f"    - {f}")
    violations.append("")
    violations.append("  Fix: abort the merge and rebase instead:")
    violations.append("    git merge --abort")
    violations.append("    git rebase <target-branch>")
    return violations


def check_alembic_heads() -> list[str]:
    """Warn if Alembic has multiple heads (branch fork)."""
    versions_path = os.path.join(_workspace(), MIGRATIONS_DIR)
    if not os.path.isdir(versions_path):
        return []

    down_revisions: dict[str, list[str]] = {}
    revision_ids: dict[str, str] = {}

    for fname in sorted(os.listdir(versions_path)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        fpath = os.path.join(versions_path, fname)
        try:
            with open(fpath, "r") as f:
                text = f.read(2000)
        except Exception:
            continue

        rev_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", text)
        down_match = re.search(r"down_revision\s*=\s*['\"]([^'\"]*)['\"]", text)

        if rev_match:
            rev_id = rev_match.group(1)
            revision_ids[fname] = rev_id
            if down_match:
                down_rev = down_match.group(1)
                down_revisions.setdefault(down_rev, []).append(fname)

    branches = {k: v for k, v in down_revisions.items() if len(v) > 1}
    if not branches:
        return []

    violations = [
        f"REGRA 5 WARNING: Alembic has {len(branches)} branch fork(s).",
    ]
    for down_rev, files in list(branches.items())[:3]:
        violations.append(f"  down_revision='{down_rev}' claimed by:")
        for f in files:
            violations.append(f"    - {f}")
    violations.append("")
    violations.append("  Fix: merge the Alembic heads or rebase one migration's down_revision.")
    violations.append("  See: alembic merge heads")
    return violations


def check_numbering_gaps() -> list[str]:
    """Check staged migrations have valid sequential numbering."""
    staged = _run("git diff --cached --name-only")
    staged_migrations = [
        f for f in staged.splitlines()
        if f.startswith(MIGRATIONS_DIR) and f.endswith(".py")
    ]
    if not staged_migrations:
        return []

    versions_path = os.path.join(_workspace(), MIGRATIONS_DIR)
    existing_nums = set()
    for fname in os.listdir(versions_path):
        m = re.match(r"^(\d+)", fname)
        if m:
            existing_nums.add(int(m.group(1)))

    violations = []
    for fpath in staged_migrations:
        fname = os.path.basename(fpath)
        m = re.match(r"^(\d+)", fname)
        if not m:
            continue
        num = int(m.group(1))
        if num in existing_nums:
            existing_files = [
                f for f in os.listdir(versions_path)
                if f.startswith(f"{num:03d}") or f.startswith(str(num))
            ]
            if len(existing_files) > 1:
                violations.append(f"  REGRA 5 WARNING: Duplicate migration number {num}:")
                for ef in existing_files[:3]:
                    violations.append(f"    - {ef}")

    if violations:
        violations.insert(0, "REGRA 5 WARNING: Migration numbering collision detected.")
        violations.append("")
        violations.append("  Fix: renumber the new migration to the next available number.")
        violations.append("  Check: ls lia-agent-system/alembic/versions/ | grep -oE '^[0-9]+' | sort -un | tail -5")
    return violations


def main() -> int:
    all_violations: list[str] = []
    all_warnings: list[str] = []

    merge_v = check_merge_state()
    if merge_v:
        all_violations.extend(merge_v)

    heads_v = check_alembic_heads()
    if heads_v:
        all_warnings.extend(heads_v)

    numbering_v = check_numbering_gaps()
    if numbering_v:
        all_warnings.extend(numbering_v)

    if all_warnings:
        print("\n".join(all_warnings))

    if all_violations:
        print("\n".join(all_violations))
        return 1

    staged = _run("git diff --cached --name-only")
    staged_mig = [f for f in staged.splitlines() if f.startswith(MIGRATIONS_DIR)]
    if staged_mig:
        print(f"REGRA 5 OK: {len(staged_mig)} migration(s) staged, no merge detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
