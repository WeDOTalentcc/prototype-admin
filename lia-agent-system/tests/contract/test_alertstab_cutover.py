"""Contract test — AlertsTab → AlertPreferencesPanel cutover (ADR-WT-2025 Sprint D).

Garante que (a) UI legacy foi removida, (b) novo canonical UI existe,
(c) endpoint legacy /alerts/config emite Deprecation header + warning log,
(d) endpoint legacy continua funcional 1 release cycle (backward-compat),
(e) telemetry estruturada é emitida em cada chamada legacy.

Referências:
- Plan: ~/Documents/wedotalent_audit_2026-05-21/SPRINT_D_ALERTSTAB_CUTOVER.md
- ADR: ~/Documents/wedotalent_audit_2026-05-21/ADR-WT-2025-alert-canonical-table.md
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLATAFORMA_ROOT = REPO_ROOT.parent / "plataforma-lia"
FRONTEND_SRC = PLATAFORMA_ROOT / "src"


def _strip_comments_and_strings(text: str) -> str:
    """Best-effort removal of single-line comments and string literals from TS/TSX.

    Used to ensure AlertConfig string scan only catches *executable* references,
    not deprecation comments or docstring mentions.
    """
    out_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
            continue
        # Remove inline // comments
        if "//" in line and not (("://" in line) or ('"//"' in line) or ("'//'") in line):
            line = line.split("//", 1)[0]
        out_lines.append(line)
    return "\n".join(out_lines)


# ---------------------------------------------------------------------------
# Test 1 — Canonical UI exists and replaces legacy
# ---------------------------------------------------------------------------

def test_alert_preferences_panel_canonical_exists():
    """AlertPreferencesPanel.tsx deve existir como single source of truth UI."""
    panel = FRONTEND_SRC / "components" / "settings" / "AlertPreferencesPanel.tsx"
    assert panel.exists(), (
        f"Canonical UI missing at {panel.relative_to(REPO_ROOT.parent)}. "
        "Sprint D Commit 1 não aplicado."
    )
    content = panel.read_text(encoding="utf-8")
    # Sanity checks — usa hook canonical
    assert "useAlertPreferences" in content, "Deve usar hook canonical"
    # AlertConfig só permitido em comentários/docstrings (mencao explicativa)
    code_only = _strip_comments_and_strings(content)
    assert "AlertConfig" not in code_only, (
        "Não deve referenciar legacy AlertConfig em código executável"
    )


def test_alerts_tab_legacy_removed_from_communication_hub():
    """AlertsTab.tsx em communication-hub/ deve ter sido deletado no Sprint D."""
    legacy = (
        FRONTEND_SRC
        / "components"
        / "settings"
        / "communication-hub"
        / "AlertsTab.tsx"
    )
    assert not legacy.exists(), (
        f"Legacy AlertsTab.tsx ainda presente em {legacy}. "
        "Sprint D Commit 3 não aplicado (git rm)."
    )


# ---------------------------------------------------------------------------
# Test 2 — No AlertConfig writes in canonical settings panel
# ---------------------------------------------------------------------------

def test_no_alertconfig_writes_in_canonical_settings_panel():
    """AST/string scan — components/settings/ não pode escrever em AlertConfig."""
    settings_root = FRONTEND_SRC / "components" / "settings"
    if not settings_root.exists():
        pytest.skip("settings root missing in this checkout")

    offenders: list[str] = []
    for tsx in settings_root.rglob("*.tsx"):
        if "__tests__" in tsx.parts:
            continue
        try:
            text = tsx.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Pula arquivos com encoding nao-UTF8 (artefatos de tooling)
            continue
        if "AlertConfig" not in text:
            continue
        # Strip comments (// and /* */ and *) to ignore deprecation notes
        for ln_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            if "AlertConfig" in line:
                offenders.append(f"{tsx.relative_to(PLATAFORMA_ROOT)}:{ln_no}: {line.strip()[:120]}")

    assert not offenders, (
        "AlertConfig referenced em components/settings/ (deveria ser canonical):\n"
        + "\n".join(offenders)
        + "\n\nADR-WT-2025 Sprint D: usar useAlertPreferences + AlertPreferencesPanel."
    )


# ---------------------------------------------------------------------------
# Test 3 — Deprecation header on legacy endpoint
# ---------------------------------------------------------------------------

@pytest.fixture
def legacy_endpoint_source() -> str:
    """Carrega o source de app/api/v1/alerts.py — sanidade estática."""
    src = REPO_ROOT / "app" / "api" / "v1" / "alerts.py"
    return src.read_text(encoding="utf-8")


def test_legacy_config_endpoint_deprecated(legacy_endpoint_source: str):
    """PUT /alerts/config deve emitir Deprecation/Sunset/Link headers."""
    assert re.search(
        r'response\.headers\[["\']Deprecation["\']\]\s*=\s*["\']true["\']',
        legacy_endpoint_source,
    ), "Deprecation header não setado em /alerts/config"
    assert re.search(
        r'response\.headers\[["\']Sunset["\']\]',
        legacy_endpoint_source,
    ), "Sunset header não setado em /alerts/config"
    assert "successor-version" in legacy_endpoint_source and (
        "alerts/preferences" in legacy_endpoint_source
    ), "Link successor-version /alerts/preferences não setado"


def test_legacy_config_endpoint_emits_telemetry(legacy_endpoint_source: str):
    """Toda chamada a /alerts/config deve logar warning estruturado."""
    assert re.search(
        r'logger\.warning\(\s*[^)]*legacy_alert_config_(?:write|endpoint|read)',
        legacy_endpoint_source,
        flags=re.DOTALL,
    ), "Faltando logger.warning('legacy_alert_config_*') em /alerts/config"


# ---------------------------------------------------------------------------
# Test 4 — Endpoint continua funcional (backward-compat 1 release cycle)
# ---------------------------------------------------------------------------

def test_legacy_config_endpoint_still_defined(legacy_endpoint_source: str):
    """Endpoint deprecated NÃO foi removido — mantém backward-compat 3 meses."""
    assert re.search(
        r'@router\.put\(\s*["\']\/?config["\']',
        legacy_endpoint_source,
    ), "/alerts/config PUT handler removed prematurely (Sprint D+1, not D)"
    assert re.search(
        r'@router\.get\(\s*["\']\/?config["\']',
        legacy_endpoint_source,
    ), "/alerts/config GET handler removed prematurely"


# ---------------------------------------------------------------------------
# Test 5 — Hook canonical exists
# ---------------------------------------------------------------------------

def test_canonical_hook_exists_and_omits_company_id():
    """useAlertPreferences hook deve existir e NUNCA enviar company_id no body."""
    hook = FRONTEND_SRC / "hooks" / "settings" / "use-alert-preferences.ts"
    assert hook.exists(), f"Canonical hook missing: {hook}"
    content = hook.read_text(encoding="utf-8")
    assert "/alerts/preferences" in content, "Hook não chama endpoint canonical"
    # REGRA 2 Pydantic: company_id NUNCA aparece em payloads. Strip comments
    # antes de scanear.
    code_only = _strip_comments_and_strings(content)
    # Filtra TS type annotations (`company_id?:` no interface) — permitido
    # como response shape; bloqueado apenas em payload JSON.stringify.
    bad = []
    in_payload_block = False
    for ln_no, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if "JSON.stringify" in line:
            in_payload_block = True
        if in_payload_block and re.search(r'\bcompany_id\s*[:=]', line):
            bad.append(f"{hook.name}:{ln_no}: {line.strip()[:120]}")
        if in_payload_block and line.rstrip().endswith("})"):
            in_payload_block = False
    assert not bad, (
        "company_id appears in PUT/POST payload (REGRA 2 Pydantic Conventions):\n"
        + "\n".join(bad)
    )
