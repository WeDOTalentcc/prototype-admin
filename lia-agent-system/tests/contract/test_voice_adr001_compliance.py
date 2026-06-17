"""
F-13 sensor (audit 2026-05-22 AUDIT_VOICE_SCREENING_ORCHESTRATOR.md):

ADR-001 Repository Pattern: services MUST NOT contain raw SQL inline.
Voice orchestrator was violating in 6 sites — db.execute(_text(...)) or
db.execute(text(...)) — all should be moved to repository methods.

These tests assert structural absence of SQL inline patterns in voice
orchestrator + presence of the canonical repository methods that
replaced them.
"""
from __future__ import annotations

import re
from pathlib import Path


VOICE_ORCH = Path(__file__).resolve().parents[2] / (
    "app/domains/voice/services/voice_screening_orchestrator.py"
)
WSI_REPO = Path(__file__).resolve().parents[2] / (
    "app/domains/voice/repositories/wsi_repository.py"
)
TENANT_REPO = Path(__file__).resolve().parents[2] / (
    "app/domains/company/repositories/tenant_repository.py"
)


# Patterns matching raw SQL inline (mirror of scripts/check_no_sql_inline_in_services.py
# extended to catch the `_text` alias the voice orch was using).
_RAW_SQL_PATTERNS = (
    re.compile(r"\bdb\.execute\s*\(\s*_text\s*\("),
    re.compile(r"\bdb\.execute\s*\(\s*text\s*\("),
    re.compile(r"\bdb\.execute\s*\(\s*sa\.text\s*\("),
    re.compile(r"\bdb\.execute\s*\(\s*sqlalchemy\.text\s*\("),
    re.compile(r"\bdb\.execute\s*\(\s*\"\"\""),
    re.compile(r"\bdb\.execute\s*\(\s*'''"),
)


def _count_sql_inline_in(file_path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, line)] for each raw-SQL inline in voice orchestrator.

    Honors `# ADR-001-EXEMPT: <reason>` marker on the same or previous line.

    Catches both single-line (`db.execute(text(...`) and multi-line
    (`await db.execute(\n  text(...`) patterns, plus pre-built `text(...)`
    objects assigned and passed (`query = text(...); db.execute(query)`).
    """
    if not file_path.exists():
        return []
    src = file_path.read_text()
    hits: list[tuple[int, str]] = []
    lines = src.splitlines()
    # multi-line `await db.execute(` + next non-empty line begins with text(/_text(
    for i, line in enumerate(lines, 1):
        # single-line pattern check
        for p in _RAW_SQL_PATTERNS:
            if p.search(line):
                window = "\n".join(lines[max(0, i - 4): i])
                if "ADR-001-EXEMPT" in window:
                    continue
                hits.append((i, line.strip()[:120]))
                break
        # multi-line: `await db.execute(` then next non-comment, non-empty line
        # starts with `text(` / `_text(` / `query` (where query was assigned text())
        if re.search(r"db\.execute\s*\(\s*$", line):
            # look ahead 1-3 lines
            for j in range(i, min(i + 4, len(lines))):
                nxt = lines[j].strip()
                if not nxt or nxt.startswith("#"):
                    continue
                if re.match(r"^(?:_text|text|sa\.text|sqlalchemy\.text|query)\s*[(,]", nxt) or \
                   re.match(r"^(?:_text|text)\s*\(\s*\"\"\"", nxt) or \
                   nxt.startswith("query,") or nxt.startswith("query "):
                    window = "\n".join(lines[max(0, i - 4): i])
                    if "ADR-001-EXEMPT" in window:
                        break
                    hits.append((i, line.strip()[:120]))
                    break
                break
        # `query = _text(...)` assignment pattern
        if re.search(r"\bquery\s*=\s*_text\s*\(", line) or re.search(r"\bquery\s*=\s*text\s*\(", line):
            window = "\n".join(lines[max(0, i - 4): i])
            if "ADR-001-EXEMPT" not in window:
                hits.append((i, line.strip()[:120]))
    return hits


def test_voice_orchestrator_has_zero_sql_inline():
    """F-13: voice orchestrator MUST NOT contain raw SQL inline (ADR-001).

    Pre-fix: 6 violations at lines ~420, 460, 499, 554, 2113, 2269, 2459.
    Post-fix: all moved to WsiRepository / TenantRepository / JobVacancyCrudRepository.
    """
    hits = _count_sql_inline_in(VOICE_ORCH)
    assert not hits, (
        f"voice orchestrator has {len(hits)} ADR-001 violations:\n"
        + "\n".join(f"  line {ln}: {txt}" for ln, txt in hits[:10])
    )


def test_wsi_repository_has_voice_session_state_methods():
    """F-13: persist/load voice_session_state moved to WsiRepository."""
    src = WSI_REPO.read_text()
    assert "async def update_voice_session_state" in src, (
        "WsiRepository must expose update_voice_session_state method"
    )
    assert "async def get_voice_session_state" in src, (
        "WsiRepository must expose get_voice_session_state method"
    )


def test_wsi_repository_has_load_question_texts():
    """F-13: load WSI question texts moved to WsiRepository."""
    src = WSI_REPO.read_text()
    assert "async def list_question_texts_for_session" in src, (
        "WsiRepository must expose list_question_texts_for_session method"
    )


def test_tenant_repository_has_pricing_tier_lookup():
    """F-13: pricing_tier lookup moved to TenantRepository (or canonical)."""
    src = TENANT_REPO.read_text()
    assert "async def get_pricing_tier" in src, (
        "TenantRepository must expose get_pricing_tier method"
    )


def test_voice_orchestrator_imports_canonical_repos():
    """F-13: voice orchestrator must import WsiRepository + JobVacancyCrudRepository."""
    src = VOICE_ORCH.read_text()
    # WsiRepository should be referenced somewhere in service
    assert "WsiRepository" in src, (
        "voice orchestrator must reference WsiRepository for canonical writes"
    )
    # Job vacancy fetch should use repo path
    assert "JobVacancyCrudRepository" in src or "get_vacancy_by_id_and_company" in src, (
        "voice orchestrator must use JobVacancyCrudRepository.get_vacancy_by_id_and_company"
    )
