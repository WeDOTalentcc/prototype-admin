#!/usr/bin/env python3
"""
Sensor canonical: cada lib em [tool.uv.sources] com workspace=true
deve ter dir correspondente em libs/.

Uso: python scripts/check_pyproject_libs_consistency.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
LIBS_DIR = ROOT / "libs"


def main() -> int:
    if not PYPROJECT.exists():
        print(f"FAIL: {PYPROJECT} nao encontrado", file=sys.stderr)
        return 2
    if not LIBS_DIR.exists():
        print(f"FAIL: {LIBS_DIR} nao encontrado", file=sys.stderr)
        return 2

    text = PYPROJECT.read_text(encoding="utf-8")
    # Encontrar bloco [tool.uv.sources]
    in_sources = False
    declared = []
    for line in text.splitlines():
        s = line.strip()
        if s == "[tool.uv.sources]":
            in_sources = True
            continue
        if in_sources and s.startswith("[") and s != "[tool.uv.sources]":
            break
        if in_sources and "=" in s and "workspace" in s and "true" in s.lower():
            # ex: lia-config = { workspace = true }
            m = re.match(r"^([a-z][a-z0-9-]+)\s*=", s)
            if m:
                declared.append(m.group(1))

    # libs/ no FS — lib name convention: lia-X => libs/X (sem prefixo)
    fs_libs = set()
    for d in LIBS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            fs_libs.add(d.name)

    missing_in_fs = []
    for lib_name in declared:
        # Convert lia-foo -> foo
        short_name = lib_name.removeprefix("lia-")
        if short_name not in fs_libs:
            missing_in_fs.append(f"{lib_name} (esperado libs/{short_name}/)")

    if missing_in_fs:
        print(
            "FAIL: pyproject [tool.uv.sources] declara libs sem dir em libs/:",
            file=sys.stderr,
        )
        for m in missing_in_fs:
            print(f"  - {m}", file=sys.stderr)
        print(
            "\nRemover das [tool.uv.sources] ou criar dirs em libs/.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {len(declared)} libs em pyproject <-> {len(fs_libs)} dirs em libs/ - consistente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
