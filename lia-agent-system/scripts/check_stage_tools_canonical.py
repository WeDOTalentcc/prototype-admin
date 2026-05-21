#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect tool_registry files
sem STAGE_TOOLS allowlist canonical.

Catches the class of gaps found in 2026-05-20 audit P1.6 / Tema C:
21 tools de Settings (company_tool_registry 8 + policy_tool_registry 13) sem
STAGE_TOOLS dict, deixando agente conversacional com TODAS as tools
disponíveis em qualquer contexto. Os outros domains (sourcing, wizard, kanban,
pipeline, talent) já têm o pattern canonical.

Canonical pattern (CLAUDE.md vacancy preview Phase E):
    STAGE_TOOLS: dict[str, list[str]] = {
        "stage_name": ["tool1", "tool2", ...],
        ...
    }

    def get_<domain>_tools_for_stage(stage: str) -> list[ToolDefinition]:
        all_tools = get_<domain>_tools()
        tool_names = STAGE_TOOLS.get(stage)
        if tool_names is None:
            return all_tools  # fallback canonical
        tool_map = {t.name: t for t in all_tools}
        return [tool_map[name] for name in tool_names if name in tool_map]

Scope: any file matching `**/agents/*_tool_registry.py` em app/domains/.

Run modes:
  blocking (default): exit 1 if any file falta STAGE_TOOLS
  --warn-only: exit 0, only lists hits (use durante migração)

Exit codes:
  0 = all tool_registry files have STAGE_TOOLS, or warn-only mode
  1 = some files missing STAGE_TOOLS + blocking mode
  2 = usage error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _has_stage_tools_export(path: Path) -> bool:
    """Detect canonical stage filtering — either:
    - STAGE_TOOLS dict in this file, OR
    - STAGE_DEFINITIONS dict in adjacent `*_stage_context.py` file
      (canonical pattern usado em communication, analytics, ats_integration)
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if ("STAGE_TOOLS:" in source) or ("STAGE_TOOLS =" in source):
        return True

    # Look for adjacent *_stage_context.py
    domain_dir = path.parent
    base = path.stem  # e.g. ats_integration_tool_registry
    domain_prefix = base.replace("_tool_registry", "")
    candidates = list(domain_dir.glob(f"{domain_prefix}_stage_context.py"))
    if not candidates:
        # Fallback: any *_stage_context.py in same dir
        candidates = list(domain_dir.glob("*_stage_context.py"))
    for sc_path in candidates:
        try:
            sc_source = sc_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if (
            ("STAGE_DEFINITIONS" in sc_source)
            or ("STAGE_TOOLS" in sc_source)
            or ("STAGE_CAPABILITIES" in sc_source)
        ):
            return True

    return False


def _has_tool_definitions(path: Path) -> bool:
    """Heuristic: file declares at least 2 ToolDefinition(name="...")."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return source.count('name="') >= 2 or source.count("name='") >= 2


def find_tool_registry_files(root: Path) -> list[Path]:
    """Glob for `**/agents/*_tool_registry.py` under root."""
    return [
        p
        for p in root.rglob("*_tool_registry.py")
        if "/agents/" in str(p) and "__pycache__" not in str(p)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect tool_registry files sem STAGE_TOOLS canonical."
    )
    parser.add_argument(
        "--root",
        default="app/domains",
        help="Root dir to scan (default: app/domains).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even if violations exist. Use during migration.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Error: --root {root} does not exist", file=sys.stderr)
        return 2

    files = find_tool_registry_files(root)
    if not files:
        print(f"⚠ No *_tool_registry.py files found under {root}")
        return 0

    missing: list[Path] = []
    for path in files:
        if not _has_tool_definitions(path):
            continue
        if not _has_stage_tools_export(path):
            missing.append(path)

    if not missing:
        print(
            f"✅ All {len(files)} tool_registry files have STAGE_TOOLS canonical "
            f"(CLAUDE.md vacancy preview Phase E pattern)."
        )
        return 0

    print(
        f"⚠️  {len(missing)} tool_registry file(s) without STAGE_TOOLS canonical "
        f"(CLAUDE.md vacancy preview Phase E pattern):\n"
    )
    for p in missing:
        print(f"── {p}")
    print(
        f"\nHow to fix each hit:\n"
        f"  1. Add a STAGE_TOOLS: dict[str, list[str]] = {{...}} at module level\n"
        f"     mapping each canonical stage → list of tool names allowed.\n"
        f"  2. Add a get_<domain>_tools_for_stage(stage: str) function\n"
        f"     that filters tools by STAGE_TOOLS.get(stage), with fallback to\n"
        f"     all tools when stage unknown (preserves backward compat).\n"
        f"  3. Reference: see app/domains/sourcing/agents/sourcing_tool_registry.py\n"
        f"     for canonical pattern.\n"
    )
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
