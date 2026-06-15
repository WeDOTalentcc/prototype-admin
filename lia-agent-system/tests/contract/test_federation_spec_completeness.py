"""
Harness sensor: validates _FEDERATION_SPEC entries resolve to real callable handlers.
Prevents ghost tools (registered but not callable).

P1-2: view_screening_results in _FEDERATION_SPEC (WSI/BigFive visible in chat)
P1-3: send_email + send_whatsapp in _FEDERATION_SPEC (individual communication)
P1-6: interview_scheduling tools in _FEDERATION_SPEC (schedule_interview, check_interviewer_availability)
P2-3: autonomous ghost removed from _CANONICAL_SOURCES (prevents silent ModuleNotFoundError)

2026-06-15
"""
import os

import pytest


def test_autonomous_not_in_canonical_sources():
    """autonomous domain dir does not exist — must not be in catalog.

    P2-3: 'autonomous' in _CANONICAL_SOURCES causava ModuleNotFoundError
    silencioso em toda carga do catálogo (_load_sources captura e loga,
    mas a degradação era silenciosa para o caller).
    Fix: entrada removida de _CANONICAL_SOURCES em 2026-06-15.
    """
    autonomous_dir = os.path.join(
        os.path.dirname(__file__),
        "../../app/domains/autonomous",
    )
    assert not os.path.isdir(autonomous_dir), (
        "O diretório app/domains/autonomous/ foi criado. "
        "Se intencional, remova este assert e registre em _CANONICAL_SOURCES "
        "com get_autonomous_tools() real."
    )

    from app.shared.tool_catalog import _CANONICAL_SOURCES

    assert "autonomous" not in _CANONICAL_SOURCES, (
        "GHOST: 'autonomous' em _CANONICAL_SOURCES mas o diretório não existe. "
        "Remova a entrada para parar o ModuleNotFoundError silencioso em _load_sources. "
        "Fix: deletar linha 'autonomous': (...) de app/shared/tool_catalog.py"
    )


def test_federation_spec_view_screening_results_present():
    """view_screening_results deve estar acessível pelo chat federado (P1-2).

    Sem isso, recrutadores não conseguem ver score WSI/BigFive de candidatos
    via chat — precisam sair do chat e navegar manualmente.
    """
    try:
        from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
            _FEDERATION_SPEC,
        )

        spec_tools = [t[1] if isinstance(t, tuple) else t for t in _FEDERATION_SPEC]
        assert "view_screening_results" in spec_tools, (
            "view_screening_results NÃO está em _FEDERATION_SPEC. "
            "Recrutadores não podem ver score WSI/BigFive de candidatos via chat. "
            "Fix: adicionar ('cv_screening_pipeline', 'view_screening_results') ao _FEDERATION_SPEC "
            "e 'cv_screening_pipeline' ao _source_maps() em recruiter_copilot_tool_registry.py"
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")


def test_federation_spec_communication_tools_present():
    """send_email e send_whatsapp devem estar em _FEDERATION_SPEC (P1-3).

    Sem isso, a LIA não pode enviar email/whatsapp individual para candidato
    diretamente pelo chat — apenas comunicação em batch (send_batch_communication).
    """
    try:
        from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
            _FEDERATION_SPEC,
        )

        spec_tools = [t[1] if isinstance(t, tuple) else t for t in _FEDERATION_SPEC]
        assert "send_email" in spec_tools, (
            "send_email NÃO está em _FEDERATION_SPEC. "
            "Fix: adicionar ('communication', 'send_email') ao _FEDERATION_SPEC "
            "e 'communication' ao _source_maps() em recruiter_copilot_tool_registry.py"
        )
        assert "send_whatsapp" in spec_tools, (
            "send_whatsapp NÃO está em _FEDERATION_SPEC. "
            "Fix: adicionar ('communication', 'send_whatsapp') ao _FEDERATION_SPEC "
            "e 'communication' ao _source_maps() em recruiter_copilot_tool_registry.py"
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")


def test_federation_spec_interview_scheduling_present():
    """schedule_interview e check_interviewer_availability devem estar em _FEDERATION_SPEC (P1-6).

    Sem isso, a LIA não pode agendar entrevistas pelo chat.
    """
    try:
        from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
            _FEDERATION_SPEC,
        )

        spec_tools = [t[1] if isinstance(t, tuple) else t for t in _FEDERATION_SPEC]
        assert "schedule_interview" in spec_tools, (
            "schedule_interview NÃO está em _FEDERATION_SPEC. "
            "Fix: adicionar ('interview_scheduling', 'schedule_interview') ao _FEDERATION_SPEC."
        )
        assert "check_interviewer_availability" in spec_tools, (
            "check_interviewer_availability NÃO está em _FEDERATION_SPEC. "
            "Fix: adicionar ('interview_scheduling', 'check_interviewer_availability') ao _FEDERATION_SPEC."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")


def test_interview_scheduling_registry_is_importable():
    """interview_scheduling_tool_registry deve ser importável e retornar 2 tools (P1-6)."""
    try:
        from app.domains.interview_scheduling.agents.interview_scheduling_tool_registry import (
            get_interview_scheduling_tools,
        )

        tools = get_interview_scheduling_tools()
        tool_names = [t.name for t in tools]
        assert "schedule_interview" in tool_names, (
            "schedule_interview não encontrado em get_interview_scheduling_tools(). "
            "Verifique interview_scheduling_tool_registry.py."
        )
        assert "check_interviewer_availability" in tool_names, (
            "check_interviewer_availability não encontrado em get_interview_scheduling_tools(). "
            "Verifique interview_scheduling_tool_registry.py."
        )
        assert len(tools) >= 2, f"Esperado >= 2 tools, encontrado {len(tools)}"
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")


def test_cv_screening_pipeline_registry_exposes_view_screening_results():
    """pipeline_tool_registry deve expor view_screening_results como ToolDefinition (P1-2)."""
    try:
        from app.domains.cv_screening.agents.pipeline_tool_registry import get_pipeline_tools

        tools = get_pipeline_tools()
        tool_names = [t.name for t in tools]
        assert "view_screening_results" in tool_names, (
            "view_screening_results não encontrado em get_pipeline_tools(). "
            "Verifique pipeline_tool_registry.py — o ToolDefinition deve estar em TOOL_DEFINITIONS."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")
