"""Sprint 4 sensor (2026-05-26) — WizardSessionService.process_message
injeta proactive context notes em state['tenant_context_snippet'] após
_build_state e ANTES de hiring_policy_summary block.

Espelha sensor de Sprint 3.4 (main_orchestrator inject) mas para o
wizard path. Sem isso, editar Settings durante wizard ativo NÃO chega
ao LLM do wizard.
"""
from pathlib import Path


SVC = Path("app/domains/job_creation/services/wizard_session_service.py")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_imports_proactive_context_store_inline():
    """Sprint 4: inject must import ProactiveContextStore inline (lazy)
    para evitar import cycle no module load."""
    src = _read(SVC)
    assert "from app.shared.services.proactive_context_store import" in src, (
        "Sprint 4 missing ProactiveContextStore import. Wizard path "
        "needs it for parity com Sprint 3.4 (main_orchestrator)."
    )
    assert "ProactiveContextStore" in src


def test_calls_list_recent_with_company_user_in_wizard_path():
    """list_recent canonical signature: company_id + user_id."""
    src = _read(SVC)
    # Find the inject block by header
    idx = src.find("Sprint 4")
    assert idx >= 0, "Sprint 4 marker missing"
    # Window around the inject block
    window = src[idx:idx + 4000]
    assert "ProactiveContextStore.list_recent(" in window, (
        "Sprint 4 must call list_recent in wizard process_message"
    )
    assert "company_id=" in window
    assert "user_id=" in window
    assert "limit=" in window


def test_enriches_tenant_context_snippet_not_replaces():
    """Sprint 4: notes devem ENRIQUECER tenant_context_snippet existente,
    não substituir. Senão sobrescreve contexto canonical do tenant."""
    src = _read(SVC)
    # Pattern: existing_snippet + pc_block (append, não overwrite)
    assert "_existing_snippet = state.get(\"tenant_context_snippet\")" in src, (
        "Sprint 4 must READ existing tenant_context_snippet first"
    )
    assert "_existing_snippet + _pc_block" in src or '_existing_snippet+_pc_block' in src, (
        "Sprint 4 must APPEND (não overwrite). Pattern: existing + pc_block."
    )


def test_reinforces_anti_pattern_1_in_wizard_context():
    """Bloco injected deve reforçar Anti-pattern #1 inline (mesmo padrão
    Sprint 3.4 — consistência cross-paths)."""
    src = _read(SVC)
    idx = src.find("Contexto recente das configurações")
    assert idx >= 0, "canonical header missing"
    window = src[idx:idx + 1500]
    assert "NUNCA enumere features" in window or "Anti-pattern" in window, (
        "Sprint 4 inject deve reforçar lia_persona Anti-pattern #1 "
        "(consistência com Sprint 3.4 main_orchestrator inject)."
    )


def test_clears_consumed_after_inject():
    """Após inject deve clear_consumed para evitar re-injeção a cada
    turn do wizard. Mesma semântica do Sprint 3.4.

    Window bumped 4000 → 6000 em PR-15 (2026-05-26): PR-12/F-4.14
    adicionou telemetry counter (Prometheus labels) entre o inject e o
    clear_consumed, empurrando o clear_consumed para além de 4000 chars.
    Sensor reativa após o bump."""
    src = _read(SVC)
    idx = src.find("Sprint 4")
    window = src[idx:idx + 6000]
    assert "ProactiveContextStore.clear_consumed(" in window, (
        "Sprint 4 missing clear_consumed após inject"
    )


def test_fail_open_in_wizard_inject():
    """Bloco inject wrapped em try/except — fail-open canonical.
    Redis down ou exception NÃO pode quebrar wizard."""
    src = _read(SVC)
    idx = src.find("ProactiveContextStore.list_recent(")
    # Find specifically the wizard call site (NOT the orchestrator one)
    # Multiple occurrences expected — but in wizard_session_service.py
    # apenas 1 deve existir.
    occurrences = src.count("ProactiveContextStore.list_recent(")
    assert occurrences >= 1, "list_recent call site missing in wizard"
    # Look backwards for try: within reasonable distance from FIRST occurrence
    prefix = src[max(0, idx - 600):idx]
    assert "try:" in prefix, (
        "Sprint 4 inject must be wrapped in try/except fail-open. "
        "Redis exception NÃO pode quebrar WizardSessionService.process_message."
    )


def test_inject_happens_after_build_state_before_hiring_policy():
    """Order critical: inject DEPOIS de _build_state (state já montado)
    mas ANTES de hiring_policy_summary block (pra fluxo natural de
    enriquecimento). Sprint 4 segue mesma ordem cronológica do pattern
    manager_preferences/hiring_policy."""
    src = _read(SVC)
    build_state_idx = src.find("state = cls._build_state(")
    sprint4_idx = src.find("Sprint 4")
    hiring_policy_idx = src.find("Hiring policy summary injection")
    assert build_state_idx < sprint4_idx < hiring_policy_idx, (
        f"Ordem errada: _build_state={build_state_idx} sprint4={sprint4_idx} "
        f"hiring_policy={hiring_policy_idx}. Sprint 4 inject deve ser AFTER "
        f"_build_state E BEFORE hiring_policy_summary."
    )
