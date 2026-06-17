"""LGPD Art. 9 invariant — Onda 1 B5.2 declarative.

Pin que ExecutionReasoningResponse.data_fields_NOT_accessed inclui SEMPRE
os 5 tokens canonical mesmo se alguém comentar/reordenar a constante.
"""
from __future__ import annotations


def test_lgpd_canonical_five_tokens_in_endpoint_response_constant():
    """Defense in depth — testa contract direto da constante."""
    from app.api.v1 import agent_monitoring

    canonical = {"cpf", "raca", "religiao", "genero", "estado_civil"}
    assert canonical.issubset(set(agent_monitoring._LGPD_NEVER_ACCESSED_FIELDS))


def test_lgpd_canonical_five_tokens_in_builder_constant():
    """Defense in depth — builder's FORBIDDEN_LGPD_FIELDS é canonical."""
    from app.domains.agent_studio.reasoning_trace_builder import FORBIDDEN_LGPD_FIELDS

    canonical = {"cpf", "raca", "religiao", "genero", "estado_civil"}
    assert canonical.issubset(FORBIDDEN_LGPD_FIELDS)


def test_response_model_includes_data_fields_NOT_accessed_field():
    """ExecutionReasoningResponse contrato — campo declarativo presente."""
    from app.api.v1.agent_monitoring import ExecutionReasoningResponse

    fields = ExecutionReasoningResponse.model_fields
    assert "data_fields_NOT_accessed" in fields
    assert "data_fields_accessed_summary" in fields


def test_response_model_field_type_is_list_str():
    """Sanity: campo tipado como list[str] (não Optional, não None default)."""
    from typing import get_args, get_origin

    from app.api.v1.agent_monitoring import ExecutionReasoningResponse

    f = ExecutionReasoningResponse.model_fields["data_fields_NOT_accessed"]
    ann = f.annotation
    # Pydantic 2: f.annotation pode ser list[str] direto
    assert get_origin(ann) is list
    assert str in get_args(ann)
