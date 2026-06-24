"""Sensor: todos os schemas de pipeline tools devem estar definidos antes do register.
Bug original: RENAME/REORDER/DELETE_PIPELINE_STAGE_SCHEMA ausentes causavam NameError no boot.
"""
import pytest

def test_pipeline_schemas_all_defined():
    from app.domains.recruiter_assistant.tools.pipeline_tools import (
        CREATE_PIPELINE_STAGE_SCHEMA,
        RENAME_PIPELINE_STAGE_SCHEMA,
        REORDER_PIPELINE_STAGES_SCHEMA,
        DELETE_PIPELINE_STAGE_SCHEMA,
    )
    for name, schema in [
        ("CREATE", CREATE_PIPELINE_STAGE_SCHEMA),
        ("RENAME", RENAME_PIPELINE_STAGE_SCHEMA),
        ("REORDER", REORDER_PIPELINE_STAGES_SCHEMA),
        ("DELETE", DELETE_PIPELINE_STAGE_SCHEMA),
    ]:
        assert isinstance(schema, dict), f"{name} schema deve ser dict"
        assert "required" in schema, f"{name} schema deve ter 'required'"
        assert "company_id" in schema["required"], f"{name} schema deve ter company_id em required"


def test_register_pipeline_tools_no_name_error():
    """register_pipeline_tools() deve completar sem NameError."""
    from unittest.mock import MagicMock, patch
    mock_registry = MagicMock()
    with patch("app.domains.recruiter_assistant.tools.pipeline_tools.tool_registry", mock_registry):
        from app.domains.recruiter_assistant.tools.pipeline_tools import register_pipeline_tools
        register_pipeline_tools()
    assert mock_registry.register.call_count == 4, "Deve registrar exatamente 4 pipeline tools"
