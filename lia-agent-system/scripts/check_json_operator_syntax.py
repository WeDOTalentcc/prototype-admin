#!/usr/bin/env python3
"""
Sensor: detecta operadores JSON PostgreSQL sem aspas na chave.

Padrão bugado:  ->column_name    (trata column_name como referência de coluna)
Padrão correto: ->'column_name'  (trata como string key)
                ->>'column_name' (idem, retorna text)

Varredura: arquivos .py em app/repositories/ e app/domains/*/repositories/
Honra: # JSON-OP-EXEMPT: <razão>

Exemplos de histórico:
  - context->>action_behavior              → UndefinedColumnError
  - behavioral_analysis->ocean_traits      → UndefinedColumnError
  - additional_data->>'workforce_plan'     → correto
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent.parent

# Discover repository directories
SCAN_DIRS: list[pathlib.Path] = []
static = ROOT / "app" / "repositories"
if static.exists():
    SCAN_DIRS.append(static)
domains = ROOT / "app" / "domains"
if domains.exists():
    for d in sorted(domains.rglob("repositories")):
        if d.is_dir():
            SCAN_DIRS.append(d)

# Matches bare ->identifier or ->>identifier (not preceded/followed by quotes or digits)
BARE_ARROW_RE = re.compile(
    r"->>?(?!['\"\d\s])([A-Za-z_][A-Za-z0-9_]*)"
)

# SQL execution context markers
SQL_EXEC_RE = re.compile(
    r"\btext\s*\(|\bsa\.text\s*\(|\bdb\.execute\s*\(|\bsession\.execute\s*\("
    r"|\bself\.db\.execute\s*\(",
    re.IGNORECASE,
)

# Multiline string content that contains SQL keywords
SQL_CONTENT_RE = re.compile(
    r"\b(SELECT|UPDATE|INSERT|DELETE|WHERE|FROM|JOIN|AND|OR)\b",
    re.IGNORECASE,
)


def extract_sql_string_ranges(source: str) -> list[tuple[int, int]]:
    """
    Find byte ranges of triple-quoted strings that look like SQL.
    Returns list of (start, end) byte offsets.
    """
    ranges = []
    # Match triple-quoted strings (both ''' and \"\"\")
    triple_re = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', re.MULTILINE)
    for m in triple_re.finditer(source):
        content = m.group(0)
        if SQL_CONTENT_RE.search(content):
            ranges.append((m.start(), m.end()))
    return ranges


def line_byte_offset(source: str, lineno: int) -> int:
    """Return byte offset of start of line (1-indexed)."""
    offset = 0
    for i, line in enumerate(source.splitlines(keepends=True), start=1):
        if i == lineno:
            return offset
        offset += len(line)
    return offset


violations: list[tuple[str, int, str]] = []

for scan_dir in set(SCAN_DIRS):
    if not scan_dir.exists():
        continue
    for py_file in sorted(scan_dir.rglob("*.py")):
        try:
            source = py_file.read_text(errors="replace")
        except OSError:
            continue

        sql_ranges = extract_sql_string_ranges(source)
        if not sql_ranges:
            # No SQL strings in file — skip entirely
            continue

        lines = source.splitlines()
        for lineno, line in enumerate(lines, start=1):
            # Skip exempt lines
            if "# JSON-OP-EXEMPT" in line:
                continue
            # Skip pure comment lines
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Skip docstring-only lines (not inside a SQL string)
            if not BARE_ARROW_RE.search(line):
                continue

            # Check if this line is within a SQL-bearing string
            line_offset = line_byte_offset(source, lineno)
            in_sql = any(start <= line_offset < end for (start, end) in sql_ranges)
            if not in_sql:
                continue

            # Double-check: the line must be inside an execute() call window
            # (look back up to 600 bytes for execute marker)
            window_start = max(0, line_offset - 600)
            window = source[window_start:line_offset + len(line) + 200]
            if not SQL_EXEC_RE.search(window):
                continue

            relative = py_file.relative_to(ROOT)
            violations.append((str(relative), lineno, line.rstrip()))

if violations:
    print(f"❌ JSON-OP-SENSOR: {len(violations)} violation(s) encontrada(s)")
    print()
    print("   Operadores JSON PostgreSQL sem aspas na chave causam UndefinedColumnError.")
    print("   Fix: ->coluna → ->'coluna'   ou   ->>coluna → ->>'coluna'")
    print()
    for path, lineno, text in violations:
        print(f"  {path}:{lineno}")
        print(f"    {text[:120]}")
    sys.exit(1)
else:
    print(f"✅ JSON-OP-SENSOR: 0 violations")
    sys.exit(0)
