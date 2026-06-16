"""
WizardState - Redis-backed persistence for job creation wizard.

Stores collected fields between conversation turns so LIA never asks
for information already provided. TTL: 2 hours.

Redis client: app.core.redis_client.get_redis (shared singleton, decode_responses=True)
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_WIZARD_TTL = 7200  # 2 hours
_KEY_PREFIX = "wizard:"


@dataclass
class WizardState:
    conversation_id: str = ""
    company_id: str = ""
    recruiter_id: str = ""
    draft_id: str | None = None
    # Collected fields
    title: str | None = None
    department: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    seniority: str | None = None
    work_model: str | None = None
    skills: list[str] = field(default_factory=list)
    description: str | None = None
    # Flow control
    step: str = "init"  # init | collecting | reviewing | saved | published
    confirmed_fields: list[str] = field(default_factory=list)

    def collected_summary(self) -> str:
        """Returns a human-readable summary of what has been collected."""
        lines = []
        if self.title:
            lines.append(f"- Titulo: {self.title}")
        if self.department:
            lines.append(f"- Departamento: {self.department}")
        if self.location:
            lines.append(f"- Localizacao: {self.location}")
        if self.seniority:
            lines.append(f"- Nivel: {self.seniority}")
        if self.work_model:
            lines.append(f"- Modelo: {self.work_model}")
        if self.salary_min or self.salary_max:
            lines.append(f"- Salario: R$ {self.salary_min or '?'} - R$ {self.salary_max or '?'}")
        if self.skills:
            lines.append(f"- Skills: {', '.join(self.skills[:5])}")
        return "\n".join(lines) if lines else "Nenhum campo coletado ainda."

    def pending_fields(self) -> list[str]:
        """Returns list of fields still needed."""
        pending = []
        if not self.title:
            pending.append("titulo da vaga")
        if not self.department:
            pending.append("departamento")
        if not self.location:
            pending.append("localizacao")
        if not self.seniority:
            pending.append("nivel de senioridade")
        if not self.work_model:
            pending.append("modelo de trabalho")
        return pending

    def to_prompt_snippet(self) -> str:
        """Returns a snippet to inject into the system prompt."""
        summary = self.collected_summary()
        pending = self.pending_fields()
        snippet = f"## Estado do Wizard de Vaga\n{summary}"
        if pending:
            snippet += f"\n\nAinda precisa: {', '.join(pending)}"
        else:
            snippet += "\n\nTodos os campos essenciais coletados."
        snippet += "\n\nIMPORTANTE: NAO pergunte por campos ja coletados acima."
        return snippet


def _redis_key(conversation_id: str) -> str:
    return f"{_KEY_PREFIX}{conversation_id}"


async def get_wizard_state(conversation_id: str) -> WizardState | None:
    """Load WizardState from Redis. Returns None if not found or on error (fail-safe)."""
    if not conversation_id:
        return None
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        raw = await redis.get(_redis_key(conversation_id))
        if raw:
            data = json.loads(raw)
            valid_fields = WizardState.__dataclass_fields__
            s = WizardState(**{k: v for k, v in data.items() if k in valid_fields})
            logger.debug("[WizardState] loaded for conversation=%s step=%s", conversation_id, s.step)
            return s
    except Exception as exc:
        logger.debug("[WizardState] get failed (fail-safe): %s", exc)
    return None


async def set_wizard_state(conversation_id: str, state: WizardState) -> None:
    """Persist WizardState to Redis with TTL. Fails silently."""
    if not conversation_id:
        return
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        await redis.set(_redis_key(conversation_id), json.dumps(asdict(state)), ex=_WIZARD_TTL)
        logger.debug("[WizardState] saved for conversation=%s step=%s", conversation_id, state.step)
    except Exception as exc:
        logger.debug("[WizardState] set failed (fail-safe): %s", exc)


async def clear_wizard_state(conversation_id: str) -> None:
    """Delete WizardState from Redis. Fails silently."""
    if not conversation_id:
        return
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        await redis.delete(_redis_key(conversation_id))
        logger.debug("[WizardState] cleared for conversation=%s", conversation_id)
    except Exception as exc:
        logger.debug("[WizardState] clear failed (fail-safe): %s", exc)


def update_wizard_state_from_draft(state: WizardState, draft_data: dict[str, Any]) -> WizardState:
    """Merge fields from a save_job_draft result into the WizardState.

    Call this after a successful save_job_draft tool call so the state
    stays in sync with what was actually persisted.

    Args:
        state: Current WizardState to update in-place.
        draft_data: dict returned by the save_job_draft tool (the data sub-key
                    or the raw response dict accepted).

    Returns:
        The same state object (mutated) for convenience.
    """
    payload = draft_data.get("data", draft_data)
    field_map: dict[str, str] = {
        "title": "title",
        "department": "department",
        "location": "location",
        "seniority": "seniority",
        "work_model": "work_model",
        "salary_min": "salary_min",
        "salary_max": "salary_max",
        "skills": "skills",
        "description": "description",
        "draft_id": "draft_id",
        "id": "draft_id",
    }
    for src_key, dst_attr in field_map.items():
        val = payload.get(src_key)
        if val is not None:
            setattr(state, dst_attr, val)
    return state
