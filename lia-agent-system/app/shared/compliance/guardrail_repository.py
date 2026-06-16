"""
GuardrailRepository — Fase 3

Acesso ao banco para leitura e gestão de guardrails de agentes.
Consultas otimizadas com índices em is_active, domain e company_id.
"""
import logging
import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail import Guardrail
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)


class GuardrailCreate(WeDoBaseModel):
    level: str = "primary"
    domain: str | None = None
    node: str | None = None
    tool: str | None = None
    rule: str
    blocking_message: str
    is_active: bool = True
    company_id: str | None = None
    updated_by: str = "system"


class GuardrailRepository:
    """Repositório para leitura e gestão de guardrails persistidos no banco."""

    @staticmethod
    async def get_active(
        db: AsyncSession,
        domain: str | None = None,
        company_id: str | None = None,
    ) -> list[Guardrail]:
        """
        Retorna guardrails ativos aplicáveis ao domínio e tenant.

        Prioridade de carregamento:
          1. Guardrails primários globais (domain=None, company_id=None)
          2. Guardrails primários do tenant (domain=None, company_id=company_id)
          3. Guardrails secundários globais do domínio (domain=domain, company_id=None)
          4. Guardrails secundários do tenant para o domínio

        Args:
            db: Sessão async do banco de dados
            domain: Nome do domínio do agente (ex: 'pipeline', 'sourcing')
            company_id: UUID do tenant atual (None = apenas globais)

        Returns:
            Lista de Guardrail ativos ordenados por nível (primary primeiro)
        """
        try:
            conditions = [Guardrail.is_active == True]  # noqa: E712

            domain_filter = or_(
                Guardrail.domain == None,   # noqa: E711  # globais
                Guardrail.domain == domain,  # específicos do domínio
            )

            company_filter = or_(
                Guardrail.company_id == None,    # noqa: E711  # globais
                Guardrail.company_id == company_id,  # do tenant
            )

            stmt = (
                select(Guardrail)
                .where(and_(*conditions, domain_filter, company_filter))
                .order_by(Guardrail.level, Guardrail.created_at)
            )

            result = await db.execute(stmt)
            guardrails = list(result.scalars().all())
            logger.debug(
                f"[GuardrailRepository] Carregados {len(guardrails)} guardrails "
                f"(domain={domain}, company_id={company_id})"
            )
            return guardrails

        except Exception as exc:
            logger.error(f"[GuardrailRepository] Erro ao carregar guardrails: {exc}")
            return []

    @staticmethod
    async def get_blocked_tools(
        db: AsyncSession,
        domain: str | None = None,
        company_id: str | None = None,
    ) -> list[str]:
        """
        Retorna lista de nomes de tools bloqueadas pelos guardrails ativos.

        Conveniência para o enhanced_agent_mixin que precisa apenas dos nomes.
        """
        guardrails = await GuardrailRepository.get_active(db, domain, company_id)
        return [g.tool for g in guardrails if g.tool is not None]

    @staticmethod
    async def upsert(db: AsyncSession, data: GuardrailCreate) -> Guardrail:
        """Cria ou atualiza um guardrail."""
        guardrail = Guardrail(
            id=uuid.uuid4(),
            level=data.level,
            domain=data.domain,
            node=data.node,
            tool=data.tool,
            rule=data.rule,
            blocking_message=data.blocking_message,
            is_active=data.is_active,
            company_id=data.company_id,
            updated_by=data.updated_by,
            updated_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(guardrail)
        await db.commit()
        await db.refresh(guardrail)
        logger.info(f"[GuardrailRepository] Guardrail criado: {guardrail.id} (domain={data.domain})")
        return guardrail

    @staticmethod
    async def toggle_active(db: AsyncSession, guardrail_id: str) -> Guardrail | None:
        """Inverte is_active do guardrail. Retorna None se não encontrado."""
        stmt = select(Guardrail).where(Guardrail.id == guardrail_id)
        result = await db.execute(stmt)
        guardrail = result.scalar_one_or_none()

        if not guardrail:
            logger.warning(f"[GuardrailRepository] Guardrail não encontrado: {guardrail_id}")
            return None

        guardrail.is_active = not guardrail.is_active
        guardrail.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(guardrail)
        logger.info(
            f"[GuardrailRepository] Guardrail {guardrail_id} → is_active={guardrail.is_active}"
        )
        return guardrail

    @staticmethod
    async def update(
        db: AsyncSession,
        guardrail_id: str,
        data: GuardrailCreate,
    ) -> Guardrail | None:
        """Atualiza campos de um guardrail existente."""
        stmt = select(Guardrail).where(Guardrail.id == guardrail_id)
        result = await db.execute(stmt)
        guardrail = result.scalar_one_or_none()

        if not guardrail:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(guardrail, field, value)
        guardrail.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(guardrail)
        return guardrail

    @staticmethod
    async def soft_delete(db: AsyncSession, guardrail_id: str) -> bool:
        """Desativa o guardrail (soft delete: is_active=False). Retorna True se encontrado."""
        stmt = select(Guardrail).where(Guardrail.id == guardrail_id)
        result = await db.execute(stmt)
        guardrail = result.scalar_one_or_none()

        if not guardrail:
            logger.warning(f"[GuardrailRepository] Guardrail não encontrado para delete: {guardrail_id}")
            return False

        guardrail.is_active = False
        guardrail.updated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[GuardrailRepository] Guardrail {guardrail_id} desativado (soft delete)")
        return True

    @staticmethod
    async def list_filtered(
        db,
        domain=None,
        company_id=None,
        is_active=None,
        level=None,
    ):
        """List guardrails with optional filters on domain, company_id, is_active, level."""
        from sqlalchemy import select as _select
        from app.models.guardrail import Guardrail

        stmt = _select(Guardrail)

        if domain is not None:
            stmt = stmt.where(Guardrail.domain == domain)
        if company_id is not None:
            stmt = stmt.where(Guardrail.company_id == company_id)
        if is_active is not None:
            stmt = stmt.where(Guardrail.is_active == is_active)
        if level is not None:
            stmt = stmt.where(Guardrail.level == level)

        stmt = stmt.order_by(Guardrail.level, Guardrail.domain, Guardrail.created_at)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def find_by_rule_domain_company(db, rule, domain=None, company_id=None):
        """Find a guardrail by exact rule + domain + company_id match. Returns None if not found."""
        from sqlalchemy import select as _select
        from app.models.guardrail import Guardrail

        stmt = _select(Guardrail).where(
            Guardrail.rule == rule,
            Guardrail.domain == domain,
            Guardrail.company_id == company_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
