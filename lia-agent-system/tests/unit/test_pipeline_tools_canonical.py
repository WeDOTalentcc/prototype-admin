"""TDD tests for UC-P2-10: pipeline_tools canonical deduplication.

Verifies that:
1. The canonical pipeline_tools is in app.domains.pipeline.tools
2. The recruiter_assistant pipeline_tools has a clear docstring explaining
   the distinction and pointing to the canonical module
3. Both modules are importable without conflict
"""


def test_pipeline_tools_canonical_is_pipeline_domain():
    """Canonical pipeline_tools is in the pipeline domain (langchain @tool based)."""
    from app.domains.pipeline.tools import pipeline_tools

    assert "pipeline/tools/pipeline_tools.py" in pipeline_tools.__file__, (
        f"Expected pipeline/tools/pipeline_tools.py, got: {pipeline_tools.__file__}"
    )


def test_pipeline_tools_canonical_has_langchain_tools():
    """Canonical pipeline_tools exposes langchain @tool decorated functions."""
    from app.domains.pipeline.tools.pipeline_tools import (
        move_candidate_to_stage,
        get_pipeline_overview,
        reject_candidate,
        extend_offer,
        get_candidate_pipeline_history,
        bulk_advance_candidates,
    )
    # All must be langchain StructuredTool or similar (have .name attribute)
    for fn in (
        move_candidate_to_stage,
        get_pipeline_overview,
        reject_candidate,
        extend_offer,
        get_candidate_pipeline_history,
        bulk_advance_candidates,
    ):
        assert hasattr(fn, "name"), f"{fn} is not a langchain tool"


def test_recruiter_assistant_pipeline_tools_importable():
    """recruiter_assistant pipeline_tools must remain importable (no breakage)."""
    from app.domains.recruiter_assistant.tools.pipeline_tools import (  # noqa: F401
        register_pipeline_tools,
        create_pipeline_stage,
    )
    assert callable(register_pipeline_tools)
    assert callable(create_pipeline_stage)


def test_recruiter_assistant_pipeline_tools_has_uc_p2_10_docstring():
    """recruiter_assistant/pipeline_tools must have UC-P2-10 docstring noting canonical split."""
    from app.domains.recruiter_assistant.tools import pipeline_tools as ra_pt

    doc = ra_pt.__doc__ or ""
    assert "UC-P2-10" in doc, (
        "recruiter_assistant/pipeline_tools docstring must reference UC-P2-10"
    )
    assert "pipeline.tools.pipeline_tools" in doc, (
        "Must point to canonical pipeline.tools.pipeline_tools"
    )


def test_recruiter_assistant_no_duplicate_functions():
    """recruiter_assistant pipeline_tools must not duplicate langchain tool functions."""
    import importlib
    ra_pt = importlib.import_module("app.domains.recruiter_assistant.tools.pipeline_tools")
    canonical_pt = importlib.import_module("app.domains.pipeline.tools.pipeline_tools")

    # Functions that should ONLY live in canonical, not duplicated in ra
    canonical_only = {"move_candidate_to_stage", "reject_candidate", "extend_offer",
                      "get_pipeline_overview", "bulk_advance_candidates"}
    ra_attrs = set(dir(ra_pt))
    overlap = canonical_only & ra_attrs
    assert not overlap, (
        f"recruiter_assistant pipeline_tools duplicates canonical functions: {overlap}"
    )
