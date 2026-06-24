"""TDD tests for UC-P2-10: pipeline_tools canonical deduplication.

Verifies that the live recruiter_assistant pipeline_tools module is importable.
Note: app.domains.pipeline.tools.pipeline_tools was deleted (Path F dead code
cleanup) — tests referencing that module have been removed.
"""


def test_recruiter_assistant_pipeline_tools_importable():
    """recruiter_assistant pipeline_tools must remain importable (no breakage)."""
    from app.domains.recruiter_assistant.tools.pipeline_tools import (  # noqa: F401
        register_pipeline_tools,
        create_pipeline_stage,
    )
    assert callable(register_pipeline_tools)
    assert callable(create_pipeline_stage)
