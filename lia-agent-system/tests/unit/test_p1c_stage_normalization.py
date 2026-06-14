"""Tests P1-C: stage normalization and dedup in get_job_details tool."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_normalize_stage_en_slug():
    from app.domains.job_management.tools.query_tools import _normalize_stage
    assert _normalize_stage("screening") == "Triagem"
    assert _normalize_stage("short_list") == "Short List"
    assert _normalize_stage("interview_hr") == "Entrevista RH"
    assert _normalize_stage("hired") == "Contratado"
    assert _normalize_stage("rejected") == "Reprovado"


def test_normalize_stage_pt_aliases():
    from app.domains.job_management.tools.query_tools import _normalize_stage
    assert _normalize_stage("triagem") == "Triagem"
    assert _normalize_stage("Triagem") == "Triagem"
    assert _normalize_stage("proposta") == "Proposta"
    assert _normalize_stage("contratado") == "Contratado"
    assert _normalize_stage("reprovado") == "Reprovado"


def test_normalize_stage_null_and_unknown():
    from app.domains.job_management.tools.query_tools import _normalize_stage
    assert _normalize_stage(None) == "Indefinido"
    assert _normalize_stage("") == "Indefinido"
    assert _normalize_stage("custom_stage_xyz") == "custom_stage_xyz"


def test_stage_display_has_all_canonical_stages():
    from app.domains.job_management.tools.query_tools import _STAGE_DISPLAY
    required = ["sourcing", "screening", "short_list", "interview_hr",
                "technical_test", "offer", "hired", "rejected"]
    for slug in required:
        assert slug in _STAGE_DISPLAY, f"Missing slug: {slug}"


def test_normalize_stage_no_mixed_slugs_in_funnel():
    """Funil nao deve ter slug cru ET label PT juntos."""
    from app.domains.job_management.tools.query_tools import _normalize_stage
    slugs = ["screening", "triagem", "Triagem", "short_list", "Short List"]
    results = {_normalize_stage(s) for s in slugs}
    # All map to same canonical labels, no mixing
    assert "screening" not in results, "Raw EN slug leaked into funnel"
    assert "triagem" not in results, "Raw PT alias leaked into funnel"
