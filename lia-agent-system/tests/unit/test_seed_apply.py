"""Unit tests for apply_seed_to_state (Task A5a) - pure mapping, no IO."""
from app.domains.job_creation.helpers.seed_apply import apply_seed_to_state
from app.domains.job_creation.schemas import (
    FieldProvenance,
    JobCreationSeed,
    SourceDescriptor,
)


def _seed(**over):
    base = dict(
        title="Dev Backend Senior",
        seniority="senior",
        work_model="hybrid",
        department="Engenharia",
        salary_min=12000,
        salary_max=16000,
        description="Constroi APIs.",
        requirements="Python, 5 anos.",
        responsibilities=["Desenhar APIs", "Mentorar"],
        skills=["Python", "FastAPI"],
        nice_to_have="Kafka.",
        provenance={
            "title": FieldProvenance(
                source_type="template", source_id="t1", source_name="Tpl X"
            ),
            "salary_min": FieldProvenance(
                source_type="template",
                source_id="t1",
                source_name="Tpl X",
                needs_review=True,
            ),
        },
        source=SourceDescriptor(type="template", id="t1", name="Tpl X"),
    )
    base.update(over)
    return JobCreationSeed(**base)


def test_maps_flat_fields():
    state: dict = {}
    apply_seed_to_state(state, _seed())
    assert state["parsed_title"] == "Dev Backend Senior"
    assert state["parsed_seniority"] == "senior"
    assert state["parsed_model"] == "hybrid"
    assert state["parsed_department"] == "Engenharia"
    assert state["salary_min"] == 12000
    assert state["salary_max"] == 16000


def test_user_value_wins_over_seed():
    state = {"parsed_title": "Título do recrutador"}
    apply_seed_to_state(state, _seed())
    assert state["parsed_title"] == "Título do recrutador"  # not overwritten


def test_provenance_recorded():
    state: dict = {}
    apply_seed_to_state(state, _seed())
    assert state["seed_provenance"]["parsed_title"]["source_type"] == "template"
    assert state["seed_provenance"]["salary_min"]["needs_review"] is True
    assert state["seed_source"]["type"] == "template"


def test_jd_raw_composed_from_rich_fields():
    state: dict = {}
    apply_seed_to_state(state, _seed())
    jd = state["jd_raw"]
    assert "Constroi APIs." in jd
    assert "Responsabilidades:" in jd
    assert "Desenhar APIs" in jd
    assert "Python, 5 anos." in jd
    assert "FastAPI" in jd


def test_jd_raw_not_overwritten_if_present():
    state = {"jd_raw": "JD que o recrutador colou"}
    apply_seed_to_state(state, _seed())
    assert state["jd_raw"] == "JD que o recrutador colou"


def test_always_fresh_fields_untouched():
    state: dict = {}
    apply_seed_to_state(state, _seed())
    # seed never carries manager/headcount/etc -> state must not gain them
    for f in ("parsed_manager_name", "parsed_manager_email"):
        assert not state.get(f)


def test_empty_seed_is_noop_safe():
    state: dict = {}
    apply_seed_to_state(state, JobCreationSeed(source=SourceDescriptor(type="template", id="t", name="X")))
    # no flat fields set, but seed_source recorded
    assert state["seed_source"]["id"] == "t"
    assert "parsed_title" not in state


def test_rich_fields_mapped_to_state():
    """PR-B2a: competencias + elegibilidade do seed caem nas chaves de state
    que competency_node (_has_confirmed) e eligibility_node ja reusam."""
    seed = _seed(
        technical_competencies=[{"skill": "Python", "contexto": "Avancado"}],
        behavioral_competencies=[
            {"competencia": "Lideranca", "contexto": "", "trait_big_five": ""}
        ],
        eligibility_questions=[
            {"id": "1", "question": "Tem CNH?", "is_eliminatory": True}
        ],
    )
    state: dict = {}
    apply_seed_to_state(state, seed)
    assert state["confirmed_technical_competencies"] == [
        {"skill": "Python", "contexto": "Avancado"}
    ]
    assert state["confirmed_behavioral_competencies"][0]["competencia"] == "Lideranca"
    assert state["eligibility_questions"][0]["question"] == "Tem CNH?"


def test_rich_fields_user_value_wins():
    seed = _seed(eligibility_questions=[{"id": "1", "question": "do seed"}])
    state = {"eligibility_questions": [{"id": "x", "question": "do recrutador"}]}
    apply_seed_to_state(state, seed)
    assert state["eligibility_questions"][0]["question"] == "do recrutador"


def test_wsi_questions_parked_not_live_key():
    """PR-B2b: WSI da origem vai p/ estacionamento (seed_wsi_questions), NAO
    p/ a chave live wsi_questions — senao o node pegaria sem perguntar."""
    seed = _seed(wsi_questions=[{"id": "1", "question": "Q da origem"}])
    state: dict = {}
    apply_seed_to_state(state, seed)
    assert state["seed_wsi_questions"][0]["question"] == "Q da origem"
    assert "wsi_questions" not in state


def test_jd_enriched_mapped_to_live_key():
    """PR-B2 item 3: jd_enriched do seed -> state['jd_enriched'] (chave live);
    o jd_enrichment_node tem reuse-guard e apresenta no HITL #1."""
    seed = _seed(jd_enriched={"titulo_padronizado": "X", "about_role": "y"})
    state: dict = {}
    apply_seed_to_state(state, seed)
    assert state["jd_enriched"]["titulo_padronizado"] == "X"


def test_jd_enriched_user_value_wins():
    seed = _seed(jd_enriched={"titulo_padronizado": "do seed"})
    state = {"jd_enriched": {"titulo_padronizado": "do recrutador"}}
    apply_seed_to_state(state, seed)
    assert state["jd_enriched"]["titulo_padronizado"] == "do recrutador"
