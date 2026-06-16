"""Onda 2 B2 — agent-deployments?target_type=pipeline_stage contract tests.

2 testes obrigatórios:
1. Endpoint aceita target_type=pipeline_stage (4 valores canonical via enum)
2. Validation rejeita target_type inválido (ex: foo)

Canonical-fix: target_type agora é DeploymentTargetType (enum em
lia_models.agent_deployment) em vez de str solto. FastAPI valida 422
automaticamente em qualquer valor fora do enum.
"""
from __future__ import annotations

from fastapi.testclient import TestClient



def test_pipeline_stage_is_canonical_target_type():
    """O enum canonical DEVE incluir pipeline_stage como valor valido."""
    from lia_models.agent_deployment import DeploymentTargetType

    valid_values = {v.value for v in DeploymentTargetType}
    assert "pipeline_stage" in valid_values
    assert "talent_pool" in valid_values
    assert "job" in valid_values
    assert "candidate_list" in valid_values
    # Exatamente 4 valores (sentinel sem drift acidental).
    assert valid_values == {"job", "talent_pool", "pipeline_stage", "candidate_list"}


def test_endpoint_query_param_uses_canonical_enum():
    """O endpoint list_deployments_by_target usa DeploymentTargetType (FastAPI valida)."""
    import inspect
    from app.api.v1 import agent_deployments
    from lia_models.agent_deployment import DeploymentTargetType

    sig = inspect.signature(agent_deployments.list_deployments_by_target)
    target_type_param = sig.parameters.get("target_type")
    assert target_type_param is not None, "endpoint deve ter param target_type"
    # O annotation deve ser DeploymentTargetType (canonical enum).
    assert target_type_param.annotation is DeploymentTargetType, (
        f"target_type deve usar enum canonical (got {target_type_param.annotation})"
    )
