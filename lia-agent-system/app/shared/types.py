"""
Canonical shared types — WeDoTalent lia-agent-system.

Registrado 2026-05-20 pós-audit E2E (vide ~/Documents/wedotalent_audit_2026-05-20/).

Esta camada elimina copy-paste recorrente de:
  - Path param regex (UUID OR bigint legacy Rails) — antes duplicada em 24 sites
  - Pydantic BaseModel default config — antes implícito 'extra=ignore' aceitava
    fields fantasma silenciosamente

Princípio canonical: single source of truth (CLAUDE.md canonical-standards).
Imports absolutos: `from app.shared.types import JobIdParam, WeDoBaseModel`.

NÃO importar de _shared.py dos sub-packages (job_vacancies/_shared, etc.) —
shared types vivem aqui, no nível de app/shared/, acima dos domains.
"""
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────────────────────────────────────
# Path param canonical pattern
# ─────────────────────────────────────────────────────────────────────────────
#
# Why this pattern: aceita UUID v4 (36 chars com hyphens) OR bigint legacy Rails
# (apenas dígitos). Rejeita strings arbitrárias como "lifecycle-overview" pra
# proteger contra router-include order bug que faria FastAPI cair em handler
# errado (Task #455 + #952).
#
# CRÍTICO: type aqui é `str`, NÃO `UUID`. Pydantic 2.10+ não aceita constraint
# `pattern=` em type UUID (audit F2.B1 — 24 endpoints quebrados). Type alias
# elimina a chance de devs recolocarem `: UUID = Path(...)` por engano.
UUID_OR_BIGINT_PATTERN = r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"

JobIdParam = Annotated[
    str,
    Path(
        ...,
        pattern=UUID_OR_BIGINT_PATTERN,
        description="Job vacancy ID — UUID v4 (`f57df2bf-5f74-...`) OU bigint legacy Rails string",
    ),
]
"""
Uso canonical em FastAPI handlers:

    @router.get("/job-vacancies/{job_id}")
    async def get_vacancy(
        job_id: JobIdParam,
        repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    ):
        # job_id chega validado (UUID ou bigint). Parse para UUID dentro do handler
        # quando for query local em DB; passar como str para integrações Rails.
        ...
"""

CandidateIdParam = Annotated[
    str,
    Path(
        ...,
        pattern=UUID_OR_BIGINT_PATTERN,
        description="Candidate ID — UUID v4 OR bigint legacy Rails string",
    ),
]

CompanyIdParam = Annotated[
    str,
    Path(
        ...,
        pattern=r"^[0-9a-fA-F-]{36}$",  # company_id sempre UUID, nunca bigint
        description="Company ID — UUID v4",
    ),
]

AgentIdParam = Annotated[
    str,
    Path(
        ...,
        pattern=UUID_OR_BIGINT_PATTERN,
        description="Agent ID — UUID v4 (custom_agent.id canonical) OR bigint legacy",
    ),
]
"""
Uso canonical em FastAPI handlers de Agent Studio (custom_agents endpoints):

    @router.get("/custom-agents/{agent_id}/timeline")
    async def get_timeline(agent_id: AgentIdParam, ...):
        ...

Aceita UUID (custom_agent.id) OU bigint legacy. Sprint 7B-3b transitional shim:
durante migration, agent_id pode ser CustomAgent.id OU legacy_sourcing_agent_id —
ambos UUIDs, pattern unificado. Sprint 7B-3b Part 3 removerá OR shim.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic base canonical pattern
# ─────────────────────────────────────────────────────────────────────────────
#
# Why: Pydantic default é `extra='ignore'` — aceita fields fantasma do payload
# silenciosamente. Audit F1.O2: POST /job-vacancies aceitou `city`, `state`,
# `country`, `industry` (4 fields fantasma) sem warning. Frontend pode mandar
# JSON errado e ninguém percebe.
#
# CLAUDE.md canonical-standards "Single Source of Truth" + harness-engineering
# Regra 1 (Pydantic conventions).
class WeDoBaseModel(BaseModel):
    """
    Base canonical para TODO request body schema da WeDoTalent.

    Forbid extra fields by default — força declaração explícita de quem precisa
    relax (raríssimos casos: schemas de webhook externo onde shape varia).
    Para opt-out localizado, override em subclass com motivação documentada:

        class WebhookPayload(WeDoBaseModel):
            model_config = ConfigDict(extra='allow')  # Reason: external partner schema drift

    Response schemas (JobVacancyResponse, CandidateResponse) NÃO precisam herdar
    — eles são serializados a partir de SQLAlchemy ORM via `from_attributes=True`,
    e extra fields no retorno são features (e.g., joined relationships).
    """
    model_config = ConfigDict(
        extra="forbid",
        # T-canonical-2026-05-20: validação estrita de assignment depois do __init__
        # impede atribuições silenciosas em runtime (defesa em profundidade).
        validate_assignment=True,
    )
