"""PR-B2b: _wsi_source_decision pure helper — decide a fonte das perguntas WSI.

Sensor do harness: garante que clone reaproveita (reuse_seed) apenas na 1a
entrada e que 'gerar novas' (wsi_regenerate_pending) vence o seed. Sem LLM/graph.
"""
from app.domains.job_creation.nodes.wsi_questions import _wsi_source_decision


def test_generate_is_default():
    assert _wsi_source_decision({})[0] == "generate"


def test_reuse_seed_on_first_entry():
    src, data = _wsi_source_decision({"seed_wsi_questions": [{"question": "Q1"}]})
    assert src == "reuse_seed"
    assert data == [{"question": "Q1"}]


def test_resume_when_already_approved():
    src, _ = _wsi_source_decision(
        {"questions_approved": True, "wsi_questions": [{"question": "Q"}]}
    )
    assert src == "resume"


def test_force_regen_beats_seed():
    src, _ = _wsi_source_decision(
        {"wsi_regenerate_pending": True, "seed_wsi_questions": [{"question": "Q"}]}
    )
    assert src == "generate"


def test_seed_not_reoffered_once_questions_exist():
    # Apos a 1a entrada (wsi_questions setado), o seed NAO e reoferecido.
    src, _ = _wsi_source_decision(
        {"seed_wsi_questions": [{"q": 1}], "wsi_questions": [{"question": "gen"}]}
    )
    assert src == "generate"
