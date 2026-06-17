"""Sprint 3.4 sensor (2026-05-26) — MainOrchestrator inject de proactive
context notes no _phase15_system_prompt antes de agentic_loop.run.

Validates static source:
  1. ProactiveContextStore import + call canonical (list_recent)
  2. company_id + user_id passados (multi-tenancy)
  3. Injection bloco contém "Contexto recente das configurações"
  4. Reforça Anti-pattern #1 (NUNCA enumere features) no inject context
  5. clear_consumed após inject (evita re-injeção)
  6. Fail-open try/except em volta de todo o bloco
"""
from pathlib import Path


ORCH = Path("app/orchestrator/execution/main_orchestrator.py")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_imports_proactive_context_store():
    """Sprint 3.4: main_orchestrator deve importar ProactiveContextStore."""
    src = _read(ORCH)
    assert "from app.shared.services.proactive_context_store import" in src, (
        "Sprint 3.4 missing canonical import of ProactiveContextStore. "
        "G9 wire requires inject de notes recentes no system_prompt."
    )
    assert "ProactiveContextStore" in src


def test_calls_list_recent_with_company_user():
    """list_recent canonical signature requires company_id + user_id."""
    src = _read(ORCH)
    assert "ProactiveContextStore.list_recent(" in src
    # Find the block — check kwargs presence
    idx = src.find("ProactiveContextStore.list_recent(")
    window = src[idx:idx + 600]
    assert "company_id=" in window, "list_recent must pass company_id (multi-tenancy)"
    assert "user_id=" in window, "list_recent must pass user_id (per-user store)"
    assert "limit=" in window, "list_recent must bound results"


def test_injects_canonical_context_block_header():
    """Injection block deve ter header reconhecível pelo LLM como
    'Contexto recente das configurações'."""
    src = _read(ORCH)
    assert "Contexto recente das configurações" in src, (
        "Sprint 3.4 missing canonical header for injected context block. "
        "LLM precisa de marker claro pra entender o bloco como background."
    )


def test_reinforces_anti_pattern_1_no_bullet_list():
    """Bloco injected deve reforçar lia_persona Anti-pattern #1 inline
    (NUNCA enumere features) pra evitar LIA gerar capability spam ao
    reagir ao contexto."""
    src = _read(ORCH)
    # Inject block region
    idx = src.find("Contexto recente das configurações")
    assert idx >= 0
    window = src[idx:idx + 800]
    assert "NUNCA enumere features" in window or "Anti-pattern" in window, (
        "Sprint 3.4 inject block deve reforçar lia_persona Anti-pattern #1 "
        "(NUNCA enumere features). Sem reforço inline, LLM pode reagir ao "
        "contexto via capability list spam (CR-4 regression)."
    )


def test_calls_clear_consumed_after_inject():
    """Após inject, deve chamar clear_consumed pra evitar re-injeção
    do mesmo context no próximo turn (LLM já viu)."""
    src = _read(ORCH)
    assert "ProactiveContextStore.clear_consumed(" in src, (
        "Sprint 3.4 deve chamar clear_consumed após injetar notes. "
        "Sem isso, mesmo context é re-injetado a cada turn — ruído."
    )


def test_fail_open_try_except():
    """Todo o bloco de inject deve estar wrapped em try/except fail-open
    pra não quebrar chat se Redis down ou store falha."""
    src = _read(ORCH)
    idx = src.find("ProactiveContextStore.list_recent(")
    # Look backwards for try: within reasonable distance
    prefix = src[max(0, idx - 600):idx]
    assert "try:" in prefix, (
        "Sprint 3.4 inject block must be wrapped in try/except fail-open. "
        "Redis down ou store exception NÃO pode quebrar agentic_loop.run."
    )
    # And after the inject, the except clause should exist
    suffix = src[idx:idx + 3000]
    assert "except Exception" in suffix, "fail-open except clause missing"


def test_inject_happens_before_agentic_loop_run():
    """Order critical: inject ANTES de agentic_loop.run (system_prompt
    já com context). Sensor que detecta regressão de ordem."""
    src = _read(ORCH)
    list_recent_idx = src.find("ProactiveContextStore.list_recent(")
    # Find the SPECIFIC agentic_loop.run call after the inject
    agentic_run_idx = src.find("_agentic_result = await agentic_loop.run(", list_recent_idx)
    assert agentic_run_idx > list_recent_idx, (
        "Sprint 3.4: inject deve acontecer ANTES de agentic_loop.run "
        "(system_prompt já enriquecido). Inverter a ordem = LLM NÃO "
        "vê os notes injetados."
    )
