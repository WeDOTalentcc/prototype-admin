"""Manus F1 — prompt do wizard reflete as capabilities de painel."""
from app.domains.job_creation.orchestrator import wizard_orchestrator


def _prompt() -> str:
    return wizard_orchestrator._SYSTEM_PROMPT_BASE


def test_prompt_menciona_tools_de_painel():
    p = _prompt()
    assert "open_panel" in p
    assert "close_panel" in p


def test_prompt_nao_proibe_mais_controle_do_painel():
    assert "NÃO controla o painel lateral" not in _prompt()


def test_prompt_mantem_anti_alucinacao_de_painel():
    assert "sem ter chamado a TOOL correspondente" in _prompt()


def test_publish_oferece_3_opcoes():
    import inspect
    from app.domains.job_creation.orchestrator import wizard_service_tools
    src = inspect.getsource(wizard_service_tools._handle_publish_job)
    assert "navigate_to_jobs" in src
    assert "close_panel" in src
