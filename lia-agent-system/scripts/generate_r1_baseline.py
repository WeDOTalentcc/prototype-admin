#!/usr/bin/env python3
"""T-07: Gera scripts/r1_baseline.json com snapshot atual das R1 violations.

Sensor `check_pydantic_conventions.py --ratchet R1` compara contra esse baseline.
PR que aumenta count → exit 1 (BLOCKING). PR que diminui → manual update.

Uso:
    python scripts/generate_r1_baseline.py
"""
import json
import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    sensor = repo_root / "scripts" / "check_pydantic_conventions.py"

    result = subprocess.run(
        ["python3", str(sensor), "app/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Parse R1 violations: lines starting "❌ R1 violation: ClassName em path:line"
    r1_pattern = re.compile(
        r"❌ R1 violation: (\w+) em (app/[^:]+):(\d+)"
    )
    violations = []
    for line in output.splitlines():
        m = r1_pattern.search(line)
        if m:
            class_name, file_path, line_no = m.groups()
            violations.append({
                "class": class_name,
                "file": file_path,
                "line": int(line_no),
            })

    # Aggregate by module (first 2-3 path components)
    by_module = defaultdict(int)
    by_class = {}
    for v in violations:
        # Module = first 3 components of path
        parts = v["file"].split("/")
        module = "/".join(parts[:3]) if len(parts) > 3 else "/".join(parts[:2])
        by_module[module] += 1
        by_class[v["class"]] = f"{v['file']}:{v['line']}"

    # Get git commit hash
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        commit = "unknown"

    baseline = {
        "version": 1,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "captured_commit": commit,
        "rule": "R1",
        "policy": "no-new-violations",
        "exempt_marker": "R1-EXEMPT",
        "total_count": len(violations),
        "by_module": dict(sorted(by_module.items(), key=lambda x: -x[1])),
        "by_class": dict(sorted(by_class.items())),
    }

    output_path = repo_root / "scripts" / "r1_baseline.json"
    output_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Baseline gerado: {output_path}")
    print(f"Total R1 violations: {len(violations)}")
    print(f"Modules: {len(by_module)}")
    print(f"Commit: {commit[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
