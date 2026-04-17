"""
CI lint — F8 (AUDIT 2026-04).

Verifica que toda `require_company=False` em código tem comentário
`# require_company=False kept: <razão>` na linha imediatamente acima e que a
contagem total bate com o documento `docs/policies/require_company_exemptions.md`.

Exit code:
    0  -> tudo conforme política
    1  -> exceção sem comentário kept OU contagem divergente do doc
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
_APP = _ROOT / "app"
_DOC = _REPO_ROOT / "docs" / "policies" / "require_company_exemptions.md"

_FLAG = re.compile(r"require_company\s*=\s*False")
_KEPT = re.compile(r"#\s*require_company=False\s*kept\s*:", re.IGNORECASE)


def _scan() -> tuple[int, list[str]]:
    missing: list[str] = []
    total = 0
    for py in _APP.rglob("*.py"):
        try:
            lines = py.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines):
            if not _FLAG.search(line):
                continue
            # Skip the canonical default in tool_handler itself
            if py.name == "tool_handler.py":
                continue
            # Skip comment lines (the `kept:` justification itself contains
            # the literal `require_company=False`)
            if line.lstrip().startswith("#"):
                continue
            total += 1
            # Look back up to 3 lines for the `kept:` comment
            kept = False
            for back in range(1, 4):
                if idx - back < 0:
                    break
                if _KEPT.search(lines[idx - back]):
                    kept = True
                    break
            if not kept:
                missing.append(f"{py.relative_to(_REPO_ROOT)}:{idx + 1}")
    return total, missing


def _doc_count() -> int | None:
    if not _DOC.exists():
        return None
    text = _DOC.read_text(errors="ignore")
    m = re.search(r"\*\*(\d+)\s+ocorr[eê]ncias?\*\*", text)
    if m:
        return int(m.group(1))
    return None


def main() -> int:
    total, missing = _scan()
    doc_count = _doc_count()
    print(f"[F8] require_company=False em código: {total}")
    print(f"[F8] require_company=False no doc:    {doc_count}")
    if missing:
        print(
            f"[F8] FAIL — {len(missing)} ocorrência(s) sem comentário `kept:`:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        return 1
    if doc_count is None:
        print(
            "[F8] FAIL — docs/policies/require_company_exemptions.md ausente ou sem contagem.",
            file=sys.stderr,
        )
        return 1
    if total != doc_count:
        print(
            f"[F8] FAIL — divergência: código={total}, doc={doc_count}. "
            "Atualize docs/policies/require_company_exemptions.md.",
            file=sys.stderr,
        )
        return 1
    print("[F8] OK — todas as exceções estão documentadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
