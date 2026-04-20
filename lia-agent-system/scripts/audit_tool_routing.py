#!/usr/bin/env python3
"""
audit_tool_routing.py — Canonical tool routing CI guard (ADR-016).

Runs 4 structural checks and exits non-zero if any regression detected.
Serves as baseline for the canonical tools migration (Nível 1→3).

CHECK 1 — ACTIONABLE_INTENTS coverage
  Every action_id in ACTIONABLE_INTENTS must have a real handler function
  `_<action_id>` in one of app/orchestrator/action_handlers/*.py.

CHECK 2 — No duplicate action_ids across handler routers
  Each action_id must be routed by exactly one handler module.

CHECK 3 — V2 ToolDefinitions outside the canonical registry (ADR-016)
  `get_*_tools()` declarations in app/domains/*/agents/*_tool_registry.py are
  counted. Goal = 0 after Nível 3. Baseline ~206.

CHECK 4 — V1 REST handler paths broken
  `{DOMAIN}_TOOLS` dicts in app/domains/*/tools/__init__.py whose handler
  string paths don't resolve to an importable callable. Baseline = 44.
"""
from __future__ import annotations
import ast, importlib, os, re, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"

ANSI = {"red":"\x1b[31m","grn":"\x1b[32m","ylw":"\x1b[33m","rst":"\x1b[0m","bold":"\x1b[1m"}

exit_code = 0


def header(title: str) -> None:
    print(f"\n{ANSI['bold']}=== {title} ==={ANSI['rst']}")


def ok(msg: str) -> None:
    print(f"{ANSI['grn']}[PASS]{ANSI['rst']} {msg}")


def fail(msg: str) -> None:
    global exit_code
    exit_code = 1
    print(f"{ANSI['red']}[FAIL]{ANSI['rst']} {msg}")


def warn(msg: str) -> None:
    print(f"{ANSI['ylw']}[WARN]{ANSI['rst']} {msg}")


# ---------------------------------------------------------------------------
# CHECK 1 — ACTIONABLE_INTENTS coverage
# ---------------------------------------------------------------------------
def check_1_actionable_intents_coverage() -> None:
    header("CHECK 1 — ACTIONABLE_INTENTS → handler coverage")
    sys.path.insert(0, str(ROOT))
    try:
        from app.orchestrator.action_executor.intents_config import ACTIONABLE_INTENTS
    except Exception as e:
        fail(f"Could not import ACTIONABLE_INTENTS: {e}")
        return

    handlers_dir = APP / "orchestrator" / "action_handlers"
    handler_funcs: set[str] = set()
    for py in handlers_dir.glob("*.py"):
        if py.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("_"):
                handler_funcs.add(n.name)

    action_ids = {cfg["action_id"] for cfg in ACTIONABLE_INTENTS.values()}
    missing = sorted(a for a in action_ids if f"_{a}" not in handler_funcs)

    if missing:
        fail(f"{len(missing)} action_ids without handler function:")
        for a in missing:
            print(f"    - {a}")
    else:
        ok(f"All {len(action_ids)} distinct action_ids have a `_<action>` handler.")


# ---------------------------------------------------------------------------
# CHECK 2 — No duplicate routing across handler modules
# ---------------------------------------------------------------------------
def check_2_no_duplicate_routing() -> None:
    header("CHECK 2 — No action_id routed by multiple handler modules")
    handlers_dir = APP / "orchestrator" / "action_handlers"
    action_to_files: dict[str, list[str]] = defaultdict(list)
    pat = re.compile(r'action_id\s*==\s*[\'"]([a-z_]+)[\'"]')
    for py in handlers_dir.glob("*.py"):
        if py.name.startswith("_"):
            continue
        src = py.read_text()
        # Only look inside the exported `execute_*_action` dispatcher, not helpers
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("execute_"):
                fn_src = ast.unparse(n)
                for m in pat.finditer(fn_src):
                    action_to_files[m.group(1)].append(py.name)

    dupes = {a: fs for a, fs in action_to_files.items() if len(set(fs)) > 1}
    if dupes:
        fail(f"{len(dupes)} action_ids routed by multiple modules:")
        for a, fs in dupes.items():
            print(f"    - {a}: {sorted(set(fs))}")
    else:
        ok(f"All {len(action_to_files)} routed action_ids mapped to a single handler module.")


# ---------------------------------------------------------------------------
# CHECK 3 — V2 ToolDefinitions outside canonical registry (ADR-016)
# ---------------------------------------------------------------------------
def check_3_v2_tooldefs_outside_registry() -> None:
    header("CHECK 3 — V2 ToolDefinitions outside tool_registry (ADR-016)")
    # Count `ToolDefinition(` occurrences in agents/*_tool_registry.py files
    pattern_files = list((APP / "domains").rglob("agents/*_tool_registry.py"))
    count = 0
    per_file = []
    for f in pattern_files:
        src = f.read_text()
        n = src.count("ToolDefinition(")
        if n > 0:
            count += n
            per_file.append((f.relative_to(ROOT), n))
    if count > 0:
        warn(f"{count} ToolDefinitions across {len(per_file)} legacy registry files (target: 0 after Nível 3).")
        for rel, n in sorted(per_file, key=lambda x: -x[1])[:20]:
            print(f"    {n:4d}  {rel}")
        print(f"    baseline: see MIGRATION-LOG-TOOLS-UNIFIED.md")
    else:
        ok("No V2 ToolDefinitions outside canonical tool_registry.")


# ---------------------------------------------------------------------------
# CHECK 4 — V1 REST handler paths broken
# ---------------------------------------------------------------------------
def _resolve_handler(path: str) -> bool:
    """path like 'app.domains.foo.services.bar:do_thing' or 'app.foo.bar.do_thing'."""
    try:
        if ":" in path:
            mod, attr = path.split(":", 1)
        else:
            mod, attr = path.rsplit(".", 1)
        m = importlib.import_module(mod)
        return hasattr(m, attr)
    except Exception:
        return False


def check_4_v1_rest_handlers() -> None:
    header("CHECK 4 — V1 REST {DOMAIN}_TOOLS handler paths resolvable")
    tool_inits = list((APP / "domains").rglob("tools/__init__.py"))
    pat_handler = re.compile(r'"handler"\s*:\s*"([^"]+)"')
    total = 0
    broken = []
    for f in tool_inits:
        src = f.read_text()
        if "TOOLS" not in src:
            continue
        for m in pat_handler.finditer(src):
            total += 1
            hp = m.group(1)
            if not _resolve_handler(hp):
                broken.append((f.relative_to(ROOT), hp))
    if broken:
        fail(f"{len(broken)}/{total} V1 handler paths unresolvable:")
        for rel, hp in broken[:25]:
            print(f"    {rel}:  {hp}")
        if len(broken) > 25:
            print(f"    ... ({len(broken)-25} more)")
    else:
        ok(f"All {total} V1 handler paths resolve.")


if __name__ == "__main__":
    check_1_actionable_intents_coverage()
    check_2_no_duplicate_routing()
    check_3_v2_tooldefs_outside_registry()
    check_4_v1_rest_handlers()
    print()
    if exit_code == 0:
        print(f"{ANSI['grn']}{ANSI['bold']}ALL CHECKS PASSED{ANSI['rst']}")
    else:
        print(f"{ANSI['red']}{ANSI['bold']}AUDIT FAILED — see details above{ANSI['rst']}")
    sys.exit(exit_code)
