"""Tests do PR-12 cleanup misc (Onda 4)."""
from __future__ import annotations

import os
import pathlib

import pytest


REPO_ROOT = pathlib.Path("/home/runner/workspace")
PLAT = REPO_ROOT / "plataforma-lia"
LIA = REPO_ROOT / "lia-agent-system"


# ─────────────────────────────────────────────────────────────────────────
# F-4.2 — smart-orchestrate proxy company_id removal
# ─────────────────────────────────────────────────────────────────────────
def test_smart_orchestrate_proxy_no_company_id():
    """F-4.2 + Fix F (2026-05-27): proxy smart-orchestrate foi DELETADO
    inteiramente (dead code violando REGRA ZERO + REGRA 4 + multi-tenancy).
    Forma mais forte do contrato original F-4.2 ("nao enviar company_id no
    payload"): se o proxy nao existe, nao ha como enviar. Backend canonical
    em wizard_smart_orchestrator.py:192 segue protegido por
    Depends(require_company_id) JWT."""
    route_ts = (
        PLAT
        / "src/app/api/backend-proxy/wizard/smart-orchestrate/route.ts"
    )
    assert not route_ts.exists(), (
        "Fix F regression: smart-orchestrate proxy foi recriado. Deveria "
        "permanecer DELETADO (dead code com violacao REGRA ZERO + REGRA 4 "
        "+ multi-tenancy). Backend endpoint canonical wizard_smart_orchestrator.py "
        "protegido por Depends(require_company_id) eh suficiente."
    )


# ─────────────────────────────────────────────────────────────────────────
# F-4.6 — wizard-store.ts deleted + legacy purge extended
# ─────────────────────────────────────────────────────────────────────────
def test_wizard_store_deleted():
    """F-4.6 part 1: wizard-store.ts removido (era dead code)."""
    store_ts = PLAT / "src/stores/wizard-store.ts"
    assert not store_ts.exists(), (
        "wizard-store.ts deveria estar deletado (zero importers de runtime)"
    )


def test_wizard_store_test_deleted():
    """F-4.6 part 2: wizard-store.test.ts removido junto."""
    test_ts = PLAT / "src/stores/__tests__/wizard-store.test.ts"
    assert not test_ts.exists(), (
        "wizard-store.test.ts deveria estar deletado (módulo não existe mais)"
    )


def test_purge_legacy_covers_wizard_store_key():
    """F-4.6 part 3: purgeLegacyWizardStorage cobre key `lia-wizard-store`."""
    api_ts = (
        PLAT
        / "src/components/unified-chat/wizard/useWizardSessionApi.ts"
    )
    content = api_ts.read_text()
    assert "lia-wizard-store" in content, (
        "purgeLegacyWizardStorage não menciona a key legacy `lia-wizard-store`."
    )
    assert "LEGACY_WIZARD_STORE_KEY" in content, (
        "constante LEGACY_WIZARD_STORE_KEY ausente — purge incompleto"
    )


def test_fairness_test_no_dangling_vi_mock():
    """F-4.6 part 4: vi.mock do wizard-store removido do fairness test."""
    fair_ts = (
        PLAT
        / "src/components/unified-chat/wizard/__tests__/"
        "useWizardFlow.fairness.test.tsx"
    )
    content = fair_ts.read_text()
    assert "vi.mock('@/stores/wizard-store'" not in content, (
        "vi.mock pendente em fairness test — módulo não existe mais"
    )


# ─────────────────────────────────────────────────────────────────────────
# F-4.10 — wizard_supervisor prompt extracted to YAML
# ─────────────────────────────────────────────────────────────────────────
def test_wizard_supervisor_yaml_exists():
    """F-4.10 part 1: YAML canonical existe."""
    yaml_path = (
        LIA / "app/prompts/job_creation/wizard_supervisor.yaml"
    )
    assert yaml_path.exists(), (
        "wizard_supervisor.yaml ausente em app/prompts/job_creation/"
    )


def test_wizard_supervisor_yaml_loads_canonical_prompt():
    """F-4.10 part 2: YAML carregável + system_prompt populado."""
    import yaml as _yaml
    yaml_path = (
        LIA / "app/prompts/job_creation/wizard_supervisor.yaml"
    )
    data = _yaml.safe_load(yaml_path.read_text())
    assert isinstance(data, dict)
    sp = data.get("system_prompt", "")
    assert isinstance(sp, str)
    # Sanity: contains supervisor-distinctive markers
    assert "SUPERVISOR" in sp
    assert "continue_current" in sp
    assert "create_new" in sp
    assert "REGRA CRÍTICA" in sp


def test_wizard_supervisor_loader_returns_yaml_content():
    """F-4.10 part 3: _load_system_prompt retorna o YAML, não fallback."""
    import sys
    sys.path.insert(0, str(LIA))
    from app.domains.job_creation.services.wizard_supervisor_classifier import (
        _load_system_prompt,
        _INLINE_SYSTEM_PROMPT_FALLBACK,
    )
    loaded = _load_system_prompt()
    assert loaded, "_load_system_prompt returned empty"
    # Sanity: muito mais longo que o fallback de emergência
    assert len(loaded) > 1000, (
        f"prompt suspeitamente curto ({len(loaded)} chars) — "
        "loader caiu no fallback?"
    )
    assert loaded != _INLINE_SYSTEM_PROMPT_FALLBACK, (
        "loader retornou fallback — YAML não foi carregado"
    )


# ─────────────────────────────────────────────────────────────────────────
# F-4.14 — Prometheus counter exists
# ─────────────────────────────────────────────────────────────────────────
def test_proactive_inject_counter_exists():
    """F-4.14: counter Prometheus canonical existe + tem labels canonical."""
    import sys
    sys.path.insert(0, str(LIA))
    from app.shared.services.proactive_context_store import (
        proactive_context_inject_counter,
    )
    if proactive_context_inject_counter is None:
        pytest.skip("prometheus_client não disponível (ambiente local)")
    # Smoke: ambos labels válidos não levantam
    proactive_context_inject_counter.labels(path="wizard", status="hit")
    proactive_context_inject_counter.labels(path="orchestrator", status="fail_open")


def test_proactive_inject_sites_use_counter():
    """F-4.14: ambos call sites incrementam o counter (grep — defensivo)."""
    wss = (LIA / "app/domains/job_creation/services/wizard_session_service.py").read_text()
    mo = (LIA / "app/orchestrator/execution/main_orchestrator.py").read_text()
    assert "proactive_context_inject_counter" in wss, (
        "wizard_session_service não importa o counter (F-4.14 regression)"
    )
    assert 'path="wizard"' in wss, "wizard site não rotula path='wizard'"
    assert "proactive_context_inject_counter" in mo, (
        "main_orchestrator não importa o counter (F-4.14 regression)"
    )
    assert 'path="orchestrator"' in mo, (
        "orchestrator site não rotula path='orchestrator'"
    )


# ─────────────────────────────────────────────────────────────────────────
# F-4.15 — env var LIA_PROACTIVE_CONTEXT_MAX_NOTES
# ─────────────────────────────────────────────────────────────────────────
def test_proactive_context_max_notes_default():
    """F-4.15 part 1: default = 8 (preserve historical behavior)."""
    import sys
    sys.path.insert(0, str(LIA))
    # Read fresh to avoid env override leaks from other tests
    if "app.shared.services.proactive_context_store" in sys.modules:
        del sys.modules["app.shared.services.proactive_context_store"]
    # Reset env var if any
    os.environ.pop("LIA_PROACTIVE_CONTEXT_MAX_NOTES", None)
    from app.shared.services.proactive_context_store import (
        PROACTIVE_CTX_MAX_NOTES,
    )
    assert PROACTIVE_CTX_MAX_NOTES == 8


def test_proactive_context_max_notes_env_override():
    """F-4.15 part 2: env var override applies on module load."""
    import sys
    if "app.shared.services.proactive_context_store" in sys.modules:
        del sys.modules["app.shared.services.proactive_context_store"]
    os.environ["LIA_PROACTIVE_CONTEXT_MAX_NOTES"] = "12"
    try:
        from app.shared.services.proactive_context_store import (
            PROACTIVE_CTX_MAX_NOTES,
        )
        assert PROACTIVE_CTX_MAX_NOTES == 12
    finally:
        os.environ.pop("LIA_PROACTIVE_CONTEXT_MAX_NOTES", None)


def test_proactive_context_inject_sites_use_constant():
    """F-4.15 part 3: ambos call sites usam PROACTIVE_CTX_MAX_NOTES."""
    wss = (LIA / "app/domains/job_creation/services/wizard_session_service.py").read_text()
    mo = (LIA / "app/orchestrator/execution/main_orchestrator.py").read_text()
    assert "limit=PROACTIVE_CTX_MAX_NOTES" in wss
    assert "limit=PROACTIVE_CTX_MAX_NOTES" in mo
    # Hardcoded `limit=8` deve ter sumido
    assert "limit=8" not in wss, "wizard_session_service ainda tem limit=8 hardcoded"
    assert "limit=8" not in mo, "main_orchestrator ainda tem limit=8 hardcoded"
