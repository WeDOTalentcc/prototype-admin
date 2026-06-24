"""#3 follow-up: a tool agentic search_candidates referencia colunas que EXISTEM
no model Candidate. Bug: usava Candidate.location (inexistente; é location_city)
-> AttributeError ao filtrar por localização -> erro 29ms. E getattr(c,'skills')
em vez de technical_skills. Sensor: colunas do tool batem com o model.
"""
from pathlib import Path

from app.models.candidate import Candidate

_TOOL = (
    Path(__file__).resolve().parents[2]
    / "app" / "domains" / "sourcing" / "tools" / "query_tools.py"
)


def test_candidate_model_has_columns_the_tool_filters_on():
    for col in ["location_city", "seniority_level", "status", "technical_skills",
                "languages", "lia_score"]:
        assert hasattr(Candidate, col), f"Candidate sem coluna '{col}' usada por search_candidates"


def test_candidate_has_no_bare_location_column():
    # Pin do bug: a tabela candidates usa location_city, NÃO location.
    assert not hasattr(Candidate, "location"), (
        "Candidate ganhou coluna 'location'? Confirme se search_candidates deve usá-la."
    )


def test_search_candidates_tool_uses_location_city_not_bare_location():
    src = _TOOL.read_text(encoding="utf-8")
    assert "Candidate.location_city" in src, (
        "search_candidates deve filtrar por Candidate.location_city (coluna real)."
    )
    assert "Candidate.location." not in src, (
        "search_candidates referencia Candidate.location (inexistente) → AttributeError. "
        "Fix: usar Candidate.location_city."
    )


def test_search_candidates_skills_postfilter_uses_technical_skills():
    src = _TOOL.read_text(encoding="utf-8")
    assert "getattr(c, 'skills'" not in src and 'getattr(c, "skills"' not in src, (
        "post-filter de skills usa getattr(c,'skills') mas a coluna é technical_skills "
        "→ filtro sempre vazio. Fix: getattr(c,'technical_skills')."
    )
