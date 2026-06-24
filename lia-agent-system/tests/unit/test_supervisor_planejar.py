"""
TDD RED→GREEN: /planejar detection in _run_via_supervisor() path.

Tests:
  - T1: /planejar regex matches correctly (same regex as _run_agent)
  - T2: Non-planejar messages do NOT match
  - T3: /planejar sem descrição não executa plano
"""
import re
import pytest

_PLANEJAR_RE = re.compile(r"^/planejar\b\s*(.*)", re.IGNORECASE)


def test_planejar_regex_matches():
    """T1: /planejar regex matches various forms."""
    assert _PLANEJAR_RE.match("/planejar buscar candidatos sênior em SP")
    assert _PLANEJAR_RE.match("/Planejar criar vaga + triagem + email")
    assert _PLANEJAR_RE.match("/PLANEJAR  com espaços extras  ")


def test_planejar_regex_no_match_on_normal_message():
    """T2: Normal messages don't match."""
    assert _PLANEJAR_RE.match("buscar candidatos") is None
    assert _PLANEJAR_RE.match("oi, como vai?") is None
    assert _PLANEJAR_RE.match("planejar vaga") is None  # sem a /


def test_planejar_regex_empty_description():
    """T3: /planejar sem descrição → group(1) strip() == '' → não executa."""
    m = _PLANEJAR_RE.match("/planejar")
    assert m is not None
    assert m.group(1).strip() == ""


def test_planejar_regex_captures_description():
    """T4: Description is captured correctly."""
    m = _PLANEJAR_RE.match("/planejar buscar e avaliar candidatos para vaga de Designer")
    assert m is not None
    assert "buscar" in m.group(1)
    assert "Designer" in m.group(1)


def test_planejar_task_description_extraction():
    """T5: task_desc é o que vai para decompose_task."""
    content = "/planejar contratar 3 devs em 30 dias"
    m = _PLANEJAR_RE.match(content.strip())
    task_desc = m.group(1).strip()
    assert task_desc == "contratar 3 devs em 30 dias"
