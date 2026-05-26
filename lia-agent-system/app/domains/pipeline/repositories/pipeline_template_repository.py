"""
PipelineTemplate Repository — data access layer for pipeline templates.

Multi-tenancy fail-closed canonical (Sprint Pipeline Templates 2026-05-26):
todo método público invoca  antes de query. Caller que
esquecer de passar company_id explode rápido em vez de abrir cross-tenant.

Refs:
- ADR-001 Repository Pattern (CLAUDE.md)
- Memory project_chat_tool_dispatch_canonical_fix_2026-05-24 (defense-in-depth)
- Plan ~/.claude/plans/precisamos-fazer-uma-analise-polished-quill.md
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_template import DEFAULT_PIPELINE_TEMPLATES, PipelineTemplate

logger = logging.getLogger(__name__)


def _require_company_id(company_id: str | None) -> str:
    """Fail-closed multi-tenancy gate. Raises ValueError if empty/None.

    Defense-in-depth: endpoints já filtram via current_user.company_id, mas
    callers internos (tools LLM, jobs, services novos) podem esquecer.
    Esse gate impede cross-tenant silencioso.
    """
    if not company_id:
        raise ValueError(
            "company_id is required for PipelineTemplateRepository operations "
            "(multi-tenancy fail-closed canonical)"
        )
    return company_id


class PipelineTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        is_active: bool | None = True,
        is_archived: bool | None = False,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[PipelineTemplate], int]:
        """Return (items, total) with optional filters.

        Default behavior excludes archived templates (is_archived=False).
        Pass is_archived=None to include both.
        """
        _require_company_id(company_id)
        query = select(PipelineTemplate).where(PipelineTemplate.company_id == company_id)
        if is_active is not None:
            query = query.where(PipelineTemplate.is_active == is_active)
        if is_archived is not None:
            query = query.where(PipelineTemplate.is_archived == is_archived)
        if search:
            p = f"%{search}%"
            query = query.where(
                or_(
                    PipelineTemplate.name.ilike(p),
                    PipelineTemplate.description.ilike(p),
                )
            )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0
        query = (
            query
            .order_by(
                PipelineTemplate.is_default.desc(),
                PipelineTemplate.usage_count.desc(),
                PipelineTemplate.name,
            )
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, template_id: uuid.UUID, company_id: str) -> PipelineTemplate | None:
        _require_company_id(company_id)
        result = await self.db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.id == template_id,
                PipelineTemplate.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def clear_default(self, company_id: str, exclude_id: uuid.UUID | None = None) -> None:
        """Un-set is_default on all templates for the company (optionally excluding one)."""
        _require_company_id(company_id)
        q = select(PipelineTemplate).where(
            PipelineTemplate.company_id == company_id,
            PipelineTemplate.is_default.is_(True),
        )
        if exclude_id:
            q = q.where(PipelineTemplate.id != exclude_id)
        result = await self.db.execute(q)
        for t in result.scalars():
            t.is_default = False

    async def create(self, company_id: str, data: dict, created_by: str) -> PipelineTemplate:
        _require_company_id(company_id)
        template = PipelineTemplate(
            id=uuid.uuid4(),
            company_id=company_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            usage_count=0,
            is_active=True,
            is_archived=False,
            **data,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def update(self, template: PipelineTemplate, data: dict, updated_by: str | None = None) -> PipelineTemplate:
        for key, value in data.items():
            setattr(template, key, value)
        if updated_by is not None:
            template.updated_by = updated_by
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        return template

    async def soft_delete(self, template: PipelineTemplate) -> None:
        """Legacy soft-delete: sets is_active=False. Use  for the canonical hide-from-selector behavior."""
        template.is_active = False
        template.updated_at = datetime.utcnow()
        await self.db.flush()

    async def archive(self, template: PipelineTemplate, updated_by: str | None = None) -> None:
        """Canonical archive — set is_archived=True. Mantém in analytics but hides from apply selectors."""
        template.is_archived = True
        if updated_by is not None:
            template.updated_by = updated_by
        template.updated_at = datetime.utcnow()
        await self.db.flush()

    async def clone(
        self, original: PipelineTemplate, new_name: str, created_by: str
    ) -> PipelineTemplate:
        _require_company_id(original.company_id)
        cloned = PipelineTemplate(
            id=uuid.uuid4(),
            company_id=original.company_id,
            name=new_name,
            description=original.description,
            stages=original.stages.copy() if original.stages else [],
            is_default=False,
            is_active=True,
            is_archived=False,
            usage_count=0,
            department_hint=list(original.department_hint or []) or None,
            seniority_hint=list(original.seniority_hint or []) or None,
            job_family_hint=list(original.job_family_hint or []) or None,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(cloned)
        await self.db.flush()
        return cloned

    async def count_active(self, company_id: str) -> int:
        _require_company_id(company_id)
        result = await self.db.execute(
            select(func.count()).select_from(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.is_active.is_(True),
            )
        )
        return result.scalar() or 0

    async def get_by_name(self, company_id: str, name: str) -> PipelineTemplate | None:
        _require_company_id(company_id)
        result = await self.db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def seed_defaults(self, company_id: str, created_by: str) -> int:
        _require_company_id(company_id)
        seeded = 0
        for tdata in DEFAULT_PIPELINE_TEMPLATES:
            if await self.get_by_name(company_id, tdata["name"]):
                continue
            t = PipelineTemplate(
                id=uuid.uuid4(),
                company_id=company_id,
                name=tdata["name"],
                description=tdata["description"],
                stages=tdata["stages"],
                is_default=tdata["is_default"],
                is_active=True,
                is_archived=False,
                usage_count=0,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(t)
            seeded += 1
        await self.db.flush()
        return seeded

    async def increment_usage(self, template: PipelineTemplate) -> PipelineTemplate:
        template.usage_count = (template.usage_count or 0) + 1
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        return template

    async def list_for_suggestion(
        self,
        company_id: str,
        *,
        department: str | None = None,
        seniority: str | None = None,
        job_family: str | None = None,
    ) -> list[tuple[PipelineTemplate, float]]:
        """Return scored list of active, non-archived templates for auto-suggest.

        Scoring (transparent, tunável):
          - department match: 0.50 weight
          - seniority match: 0.25 weight
          - job_family match: 0.25 weight
        Match = input value (case-insensitive) presente em template.<X>_hint list.

        Fallback: se nenhum template tem hints configuradas e existe um is_default,
        retorna esse default com score 0.5 (sinal de fallback explícito).

        Resultado ordenado por score desc. Caller faz threshold (sugiro >= 0.4) e top-N.
        """
        _require_company_id(company_id)
        query = (
            select(PipelineTemplate)
            .where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.is_active.is_(True),
                PipelineTemplate.is_archived.is_(False),
            )
        )
        result = await self.db.execute(query)
        templates = list(result.scalars().all())

        def _norm(v: str | None) -> str | None:
            return v.strip().lower() if v else None

        dept = _norm(department)
        sen = _norm(seniority)
        fam = _norm(job_family)

        def _hit(hint_list, needle: str | None) -> bool:
            if not needle or not hint_list:
                return False
            return any(_norm(h) == needle for h in hint_list)

        scored: list[tuple[PipelineTemplate, float]] = []
        any_hints_configured = False
        for t in templates:
            has_hints = bool(t.department_hint or t.seniority_hint or t.job_family_hint)
            if has_hints:
                any_hints_configured = True
            score = 0.0
            if _hit(t.department_hint, dept):
                score += 0.50
            if _hit(t.seniority_hint, sen):
                score += 0.25
            if _hit(t.job_family_hint, fam):
                score += 0.25
            scored.append((t, score))

        # Fallback: nenhum template tem hints + existe default → sugere default com 0.5
        if not any_hints_configured:
            default = next((t for t in templates if t.is_default), None)
            if default:
                scored = [(default, 0.5)] + [(t, 0.0) for t in templates if t.id != default.id]

        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored
