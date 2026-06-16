"""
Contract sensor — `app/api/v1/lia_feedback.py` must register all 6 canonical
endpoints in the FastAPI app.

WHY THIS SENSOR EXISTS
======================
Audit Recovery 2026-05-23 descobriu que o commit `02361f41c` ("docs cherry-pick"
em 2026-05-01) reverteu SILENCIOSAMENTE o trabalho Task #570 (commit
`0120f8d7e` em 2026-04-19) que implementava os 6 endpoints canonical de feedback.
O arquivo `lia_feedback.py` passou de 403 LOC implementados para 3 LOC (router
vazio) sem nenhum aviso. Feedback ficou ghost feature por 22 dias até a auditoria
descobrir.

Esse sensor previne a regressão automática:
- Importa o `feedback_router` em runtime
- Conta routes registradas
- Falha (= bloqueia CI) se algum dos 6 paths canonical sumir

Pattern: sensor BLOCKING (não warn-only) — Recovery canonical é trabalho one-way,
qualquer remoção futura precisa ser explicitamente aprovada via update do sensor.

Se algum endpoint precisar mesmo ser removido no futuro (deprecation legítima
documentada em ADR), atualizar `_EXPECTED_PATHS` aqui — vai forçar revisor a
ver o que está sendo removido.
"""
from __future__ import annotations

from app.api.v1 import lia_feedback


_EXPECTED_PATHS: set[str] = {
    "/feedback/thumbs",
    "/feedback/rating",
    "/feedback/correction",
    "/feedback/regenerate",
    "/feedback/metrics",
    "/feedback/by-conversation/{session_id}",
    # Task #1299 — implicit feedback signal (correction_delta / abandonment).
    "/feedback/implicit",
}
"""
Canonical paths registered by `feedback_router`.

Path final na OpenAPI runtime: `/api/v1/lia/feedback/*` (após include_router
em `lia_assistant/__init__.py` adicionar `/lia` e `app/api/routes.py:492`
adicionar `/api/v1`).
"""


def test_feedback_router_is_not_empty():
    """
    Direct check: feedback_router must have routes.

    Specific regression guard against the 02361f41c incident — back then the
    router file was reduced to 3 lines (just `APIRouter(tags=...)` decl), so
    `feedback_router.routes` was an empty list. This test fails immediately
    if that state ever recurs.
    """
    assert len(lia_feedback.feedback_router.routes) > 0, (
        "feedback_router has zero routes registered. "
        "This is the exact regression that 02361f41c silently introduced in "
        "2026-05-01. Restore via `git show 0120f8d7e:lia-agent-system/"
        "app/api/v1/lia_feedback.py` and re-apply Boy Scout upgrades from "
        "Recovery #1 audit sheet."
    )


def test_feedback_router_registers_all_canonical_paths():
    """
    All 6 canonical paths must be present in the router's route table.

    If a future PR removes one of the 6 endpoints, this fails. To legitimately
    deprecate one, update _EXPECTED_PATHS + ADR + remove the frontend caller
    (services/lia-api/feedback-api.ts) in the same change.
    """
    registered_paths = {
        route.path for route in lia_feedback.feedback_router.routes  # type: ignore[attr-defined]
    }
    missing = _EXPECTED_PATHS - registered_paths
    assert not missing, (
        f"feedback_router missing canonical paths: {sorted(missing)}\n"
        f"Registered: {sorted(registered_paths)}\n"
        f"Expected: {sorted(_EXPECTED_PATHS)}"
    )


def test_feedback_router_uses_short_prefix():
    """
    Prefix canonical é `/feedback` (NÃO `/lia/feedback`) porque o parent
    `lia_assistant.router` já adiciona `/lia`. Path final correto em runtime:
    `/api/v1/lia/feedback/*`.

    Task #570 original tinha prefix `/lia/feedback` que provavelmente gerava
    duplicação `/api/v1/lia/lia/feedback/*` em runtime; corrigido no recovery.
    """
    assert lia_feedback.feedback_router.prefix == "/feedback", (
        f"Router prefix is '{lia_feedback.feedback_router.prefix}', expected '/feedback'. "
        "Path final esperado: /api/v1/lia/feedback/* (composto por /api/v1 + /lia + /feedback). "
        "Se mudar prefix aqui, validar que paths na OpenAPI runtime permanecem corretos."
    )


def test_audit_service_wired_into_module():
    """
    Boy Scout upgrade #3 (canonical): cada submit_* / regenerate deve registrar
    via AuditService.log_decision (trail SOX-equivalent).

    Esse sensor garante que o singleton `_audit_service` permanece importável
    e tem o método esperado. Se algum refactor futuro remover, falha.
    """
    assert hasattr(lia_feedback, "_audit_service"), (
        "Module `_audit_service` singleton ausente. Recovery canonical exige "
        "AuditService.log_decision em ações de feedback (CLAUDE.md 'AuditService "
        "em ações sensíveis')."
    )
    assert hasattr(lia_feedback._audit_service, "log_decision"), (
        "_audit_service não tem log_decision method. Algo está errado com AuditService import."
    )


def test_schemas_inherit_wedobasemodel():
    """
    Boy Scout upgrade #2 (canonical): request body schemas devem herdar
    WeDoBaseModel (`extra='forbid'`) — rejeita payload com fields fantasma
    (R1 from CLAUDE.md Pydantic conventions).
    """
    from app.shared.types import WeDoBaseModel

    request_schemas = [
        lia_feedback.ThumbsRequest,
        lia_feedback.RatingRequest,
        lia_feedback.CorrectionRequest,
        lia_feedback.RegenerateRequest,
        lia_feedback.MessageContextPayload,
    ]
    for schema in request_schemas:
        assert issubclass(schema, WeDoBaseModel), (
            f"{schema.__name__} não herda WeDoBaseModel. "
            "Request body schemas DEVEM herdar WeDoBaseModel (extra='forbid') — "
            "regra canonical R1 do CLAUDE.md. Trocar `BaseModel` → `WeDoBaseModel` "
            "no import e na definição da class."
        )
