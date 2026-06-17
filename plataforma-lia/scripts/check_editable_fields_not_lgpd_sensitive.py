#!/usr/bin/env python3
"""
check_editable_fields_not_lgpd_sensitive.py

Sensor canonical (F5 / ADR LGPD-001): bloqueia uso de <EditableField>
ou onSave callbacks referenciando fields LGPD-sensíveis.

Detecção (heurística):
- <EditableField ... label="race"> / label="gender"/...
- useCandidateFieldUpdate().updateField("race", ...) ou similar
- Strings literais que parecem field name LGPD em proximidade de
  EditableField ou updateField call

Modo: warn-only por default. Use --blocking para CI gate.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

LGPD_BLOCKED = {
    "race", "raca", "racial_origin",
    "gender", "genero",
    "marital_status", "estado_civil",
    "religion", "religiao",
    "health_data", "dados_saude",
    "ethnic_origin", "origem_etnica",
    "political_opinion", "opiniao_politica",
    "sexual_orientation", "orientacao_sexual",
    "union_membership", "filiacao_sindical",
    "date_of_birth", "data_nascimento",
    "cpf", "rg", "passport",
    "id", "candidate_id", "company_id", "account_id",
    "created_at", "updated_at", "created_by",
}

# Pattern: updateField("FIELD_NAME", ...) or .updateField('FIELD_NAME'
PATTERN_UPDATE = re.compile(r'updateField\(\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']')
# Pattern: <EditableField name="FIELD" / label="FIELD"
PATTERN_FIELD_PROP = re.compile(r'<EditableField\s+[^>]*?(?:name|label)\s*=\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']')


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (lineno, field_name, snippet)."""
    out: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return out
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        for pat in (PATTERN_UPDATE, PATTERN_FIELD_PROP):
            for m in pat.finditer(line):
                field_name = m.group(1).lower()
                if field_name in LGPD_BLOCKED:
                    out.append((lineno, field_name, line.strip()))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations.")
    args = parser.parse_args()

    files: list[Path] = []
    for p in SRC.rglob("*.tsx"):
        files.append(p)
    for p in SRC.rglob("*.ts"):
        files.append(p)

    total = 0
    print("check_editable_fields_not_lgpd_sensitive.py")
    print(f"Scanning {len(files)} files for LGPD field edits...\n")

    for path in sorted(set(files)):
        if "__tests__" in path.parts or "node_modules" in path.parts or ".next" in path.parts:
            continue
        # Allow LGPD_BLOCKED_FIELDS Set declarations in the hook file itself
        if path.name == "use-candidate-field-update.ts":
            continue
        if path.name == "check_editable_fields_not_lgpd_sensitive.py":
            continue
        vios = scan_file(path)
        for lineno, field, snippet in vios:
            total += 1
            rel = path.relative_to(ROOT)
            print(f"  [{rel}:{lineno}] LGPD-blocked field '{field}'")
            print(f"    {snippet}")
            print(f"    → Fix: remova edição deste campo. LGPD não permite editar dados sensíveis ({field}).")
            print()

    if total == 0:
        print("✅ 0 violations — nenhum campo LGPD-sensível editável via UI.")
        return 0

    print(f"\nTotal: {total} violation(s).")
    if args.blocking:
        print("Modo: BLOCKING (exit 1)")
        return 1
    print("Modo: WARN-ONLY (exit 0). Use --blocking pra falhar CI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
