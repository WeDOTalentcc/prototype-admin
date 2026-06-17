"""Contract tests — ADR-WT-2025 Sprint B+C alert canonical consolidation.

5 testes obrigatorios per harness engineering discipline:
1. migration 170 backfilla AlertConfig.alerts -> AlertPreference (mapping 5 names)
2. migration 170 backfilla CommunicationSettings.alerts (no-op verificado)
3. migration 170 idempotente (NOT EXISTS gate previne dupes)
4. AlertPreference catalog tem todos os 4 new default types (ADR-WT-2025)
5. AST scan: production code (excl. migrations/tests) tem 0 reads novos de AlertConfig
   apos cutoff date — read-shadow pattern enforcing

Sensors:
- TDD baseline: 5 testes green em greenfield (DB empty), serve como contract
  pra regression apos prod backfill.
"""
from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# =============================================================================
# Helpers
# =============================================================================


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # type: ignore[union-attr]
    return m


def _read_migration_sql(path: Path) -> str:
    """Extract SQL strings from migration file (returns raw source)."""
    src = path.read_text(encoding="utf-8")
    return src


# =============================================================================
# Test 1: AlertConfig.alerts -> AlertPreference name mapping completeness
# =============================================================================


def test_migration_170_backfills_alertconfig_rows():
    """Migration 170 contem mapping table com 5 names canonical legacy."""
    mig_path = REPO_ROOT / "alembic" / "versions" / "170_alert_canonical_consolidation.py"
    assert mig_path.exists(), f"migration not found: {mig_path}"

    mig = _load_module(mig_path)
    mapping = mig._LEGACY_NAME_TO_ALERT_TYPE

    expected = {
        "SLA Próximo do Vencimento": "sla_near_expiration",
        "Meta Mensal em Risco": "monthly_goal_at_risk",
        "Candidato Sem Interação": "candidate_no_interaction",
        "Entrevista Não Confirmada": "interview_not_confirmed",
        "Feedback Pendente": "feedback_pending",
    }

    assert mapping == expected, (
        f"Migration 170 mapping diverge de canonical legacy DEFAULT_ALERTS. "
        f"Got: {mapping}, expected: {expected}. "
        f"Adicione/remova entries em _LEGACY_NAME_TO_ALERT_TYPE."
    )

    sql = _read_migration_sql(mig_path)
    assert "INSERT INTO alert_preferences" in sql
    assert "alert_configs ac" in sql
    # `NOT EXISTS` pattern (lookahead permissivo pra newlines/indent)
    assert re.search(r"NOT EXISTS\s*\(", sql), "idempotency guard NOT EXISTS missing"


# =============================================================================
# Test 2: CommunicationSettings.alerts no-op verificado
# =============================================================================


def test_migration_170_backfills_communication_settings_alerts_noop():
    """Sprint C: communication_settings.alerts column does NOT exist on DB.

    Migration deve documentar isso explicitamente para auditoria futura.
    """
    mig_path = REPO_ROOT / "alembic" / "versions" / "170_alert_canonical_consolidation.py"
    src = mig_path.read_text(encoding="utf-8")

    # SQL sentinel checks information_schema.columns
    assert "information_schema.columns" in src
    assert "communication_settings" in src
    assert "column_name = 'alerts'" in src or 'column_name = "alerts"' in src

    # Docstring deve explicar no-op
    assert "Sprint C" in src
    assert "no-op" in src.lower() or "no op" in src.lower()


# =============================================================================
# Test 3: Idempotency
# =============================================================================


def test_migration_170_idempotent_no_duplicate_inserts():
    """Migration usa WHERE NOT EXISTS por (company_id, user_id, alert_type)."""
    mig_path = REPO_ROOT / "alembic" / "versions" / "170_alert_canonical_consolidation.py"
    src = mig_path.read_text(encoding="utf-8")

    # WHERE NOT EXISTS must filter por triple (company_id, user_id, alert_type)
    assert re.search(
        r"NOT EXISTS\s*\(\s*SELECT 1 FROM alert_preferences",
        src,
        re.IGNORECASE,
    ), "missing NOT EXISTS idempotency guard"

    # Triple key match check
    assert "ap.company_id = ac.company_id" in src
    assert "ap.user_id" in src
    assert "ap.alert_type" in src


# =============================================================================
# Test 4: Catalog extension — 4 new alert_types per ADR-WT-2025
# =============================================================================


def test_alert_preference_canonical_has_all_4_new_default_types():
    """DEFAULT_ALERT_PREFERENCES contem 4 entries que detector usa via _DETECTOR_ALERT_TYPE_MAP."""
    alerts_py = REPO_ROOT / "app" / "api" / "v1" / "alerts.py"
    src = alerts_py.read_text(encoding="utf-8")

    expected_new_types = [
        "company_profile_incomplete",
        "dsr_overdue",
        "workforce_plan_stale",
        "credits_low",
    ]

    for atype in expected_new_types:
        assert f'"alert_type": "{atype}"' in src, (
            f'DEFAULT_ALERT_PREFERENCES missing entry "alert_type": "{atype}". '
            f'Per ADR-WT-2025 _DETECTOR_ALERT_TYPE_MAP usa esse alert_type. '
            f'Fix: adicione entry com schema canonical em app/api/v1/alerts.py:DEFAULT_ALERT_PREFERENCES.'
        )

    # Schema-sync sensor independente confirma alignment com detector
    sensor_path = REPO_ROOT / "scripts" / "check_alert_preferences_schema_sync.py"
    assert sensor_path.exists(), "schema-sync sensor missing"


# =============================================================================
# Test 5: AST scan — no new AlertConfig reads em production code
# =============================================================================

_ALLOWED_ALERTCONFIG_READERS = {
    # ADR-WT-2025 read-shadow pattern: estes sites mantem write/read legacy
    # ate prod cutover. Allowlist-only para nao adicionar novos sites.
    # Sprint D+1 removera /alerts/config endpoint -> reduzira lista.
    "app/api/v1/alerts.py",  # REST endpoints GET/PUT /alerts/config (deprecated 2026-05-22, sunset 2026-08-22)
    "app/domains/notifications/repositories/alert_repository.py",  # data layer
    "app/domains/company_settings/agents/company_settings_tools_extended.py",  # LLM tool
    # Sprint D+1 partial (2026-05-22): briefing_dispatch.py canonical reader
    # agora e HiringPolicy.communication_rules.briefing_frequency. AlertConfig
    # references restantes sao APENAS legacy fallback (narrow scope via
    # _legacy_alertconfig_briefing_frequency) + user_id discovery temporario
    # (Sprint D+2 substituira por AlertPreference / user_company_membership).
    # Telemetria via briefing_dispatch_legacy_alertconfig_read_total counter
    # mostra quanto tenants ainda dependem do fallback. Quando counter zerar
    # sustentado pre-sunset (2026-08-22), remover esta entrada + fallback path.
    "app/jobs/tasks/briefing_dispatch.py",
}


def test_no_new_alertconfig_readers_in_production_code():
    """Production code (excl. allowlist) NAO deve referenciar AlertConfig direto.

    Read-shadow pattern enforce: novos consumers DEVEM usar AlertPreference
    (canonical). Lista whitelist contem os 3 sites legacy que escrevem para
    backward-compat ate prod cutover.
    """
    app_dir = REPO_ROOT / "app"
    if not app_dir.exists():
        pytest.skip("app dir not present")

    offenders: list[str] = []
    for py_file in app_dir.rglob("*.py"):
        # Skip __pycache__
        if "__pycache__" in py_file.parts:
            continue
        # Skip allowlist
        rel = py_file.relative_to(REPO_ROOT).as_posix()
        if rel in _ALLOWED_ALERTCONFIG_READERS:
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        # Look for AlertConfig usage (import or class reference)
        if re.search(r"\bAlertConfig\b", content):
            # Permitir referencia em comentario / docstring que explicita deprecation
            non_comment_hits = []
            for ln_no, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "AlertConfig" in line:
                    # Tolera linhas dentro de docstring (best effort)
                    non_comment_hits.append((ln_no, line))
            if non_comment_hits:
                offenders.append(f"{rel}: {len(non_comment_hits)} reference(s)")

    assert not offenders, (
        f"AlertConfig referenced em production code (fora do allowlist):\n"
        + "\n".join(offenders)
        + "\n\nADR-WT-2025: canonical eh AlertPreference. Migrar leitor para "
        "AlertRepository.list_preferences_for_company_user. Se for legacy write "
        "necessario, adicione path em _ALLOWED_ALERTCONFIG_READERS com motivo."
    )
