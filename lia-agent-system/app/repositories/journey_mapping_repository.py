"""JourneyMappingRepository - manages JourneyBlueprint, JourneyStep, JourneyIntegration CRUD."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journey_mapping import JourneyBlueprint, JourneyIntegration, JourneyStep

logger = logging.getLogger(__name__)


class JourneyMappingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Blueprint methods ---

    async def get_company_blueprint(self, company_id: UUID) -> JourneyBlueprint | None:
        """Get the most recent blueprint for a company with steps and integrations loaded."""
        result = await self.db.execute(
            select(JourneyBlueprint)
            .options(
                selectinload(JourneyBlueprint.steps),
                selectinload(JourneyBlueprint.integrations)
            )
            .where(JourneyBlueprint.company_id == company_id)
            .order_by(JourneyBlueprint.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_blueprint(
        self,
        blueprint_id: UUID,
        company_id: UUID | None = None,
    ) -> JourneyBlueprint | None:
        """Get a blueprint by ID without relationships.

        Sprint B.1 tail (2026-05-22): company_id agora opcional pra defense-in-depth.
        Quando passado, filtra tambem por tenant (recomendado). Quando None,
        endpoint deve fazer o gate (api/v1/journey_mapping.py).
        """
        # TENANT-EXEMPT: caller (api/v1/journey_mapping.py) eh tenant-gated via require_company_id e re-verifica blueprint.company_id antes de operar; defense-in-depth opcional via company_id param desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(JourneyBlueprint).where(
                    JourneyBlueprint.id == blueprint_id,
                    JourneyBlueprint.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat path — caller validates blueprint.company_id post-fetch
            result = await self.db.execute(
                select(JourneyBlueprint).where(JourneyBlueprint.id == blueprint_id)
            )
        return result.scalar_one_or_none()

    async def get_blueprint_with_relations(
        self,
        blueprint_id: UUID,
        company_id: UUID | None = None,
    ) -> JourneyBlueprint | None:
        """Get a blueprint by ID with steps and integrations loaded.

        Sprint B.1 tail (2026-05-22): company_id agora opcional pra defense-in-depth.
        """
        # TENANT-EXEMPT: caller (api/v1/journey_mapping.py) eh tenant-gated via require_company_id; defense-in-depth opcional via company_id param desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(JourneyBlueprint)
                .options(
                    selectinload(JourneyBlueprint.steps),
                    selectinload(JourneyBlueprint.integrations)
                )
                .where(
                    JourneyBlueprint.id == blueprint_id,
                    JourneyBlueprint.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat path — caller validates blueprint.company_id post-fetch
            result = await self.db.execute(
                select(JourneyBlueprint)
                .options(
                    selectinload(JourneyBlueprint.steps),
                    selectinload(JourneyBlueprint.integrations)
                )
                .where(JourneyBlueprint.id == blueprint_id)
            )
        return result.scalar_one_or_none()

    async def create_blueprint(self, **kwargs) -> JourneyBlueprint:
        """Create a new blueprint and return it with relationships loaded."""
        blueprint = JourneyBlueprint(**kwargs)
        self.db.add(blueprint)
        await self.db.flush()
        return blueprint

    async def create_blueprint_with_commit(self, **kwargs) -> JourneyBlueprint:
        """Create a blueprint, commit, and reload with relationships.

        TENANT-EXEMPT: blueprint.id eh PK recem-criada pelo proprio INSERT acima;
        kwargs sao injetados via caller (que ja eh tenant-gated). Defense-in-depth
        opcional via add filter de company_id (skipped: same-session round-trip).
        """
        blueprint = JourneyBlueprint(**kwargs)
        self.db.add(blueprint)
        await self.db.commit()
        await self.db.refresh(blueprint)
        # TENANT-EXEMPT: blueprint.id retornado por INSERT do caller tenant-gated; reload das relationships eh same-session
        result = await self.db.execute(
            select(JourneyBlueprint)
            .options(
                selectinload(JourneyBlueprint.steps),
                selectinload(JourneyBlueprint.integrations)
            )
            .where(JourneyBlueprint.id == blueprint.id)
        )
        return result.scalar_one()

    async def update_blueprint(self, blueprint: JourneyBlueprint, update_data: dict) -> JourneyBlueprint:
        """Apply update_data dict to blueprint, set updated_at, commit and refresh."""
        for field, value in update_data.items():
            setattr(blueprint, field, value)
        blueprint.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(blueprint)
        return blueprint

    async def save_wizard_step(
        self,
        blueprint: JourneyBlueprint,
        step_number: int,
        data: dict,
    ) -> JourneyBlueprint:
        """Merge wizard step data into blueprint and persist."""
        current_wizard_data = blueprint.wizard_data or {}
        current_wizard_data[f"step_{step_number}"] = data
        blueprint.wizard_data = current_wizard_data

        if step_number > blueprint.wizard_step:
            blueprint.wizard_step = step_number

        if data.get("completed", False):
            blueprint.wizard_completed = True
            blueprint.status = "completed"
        else:
            blueprint.status = "in_progress"

        blueprint.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(blueprint)
        return blueprint

    async def update_blueprint_ai(
        self,
        blueprint: JourneyBlueprint,
        ai_recommendations: list,
        ai_summary: str,
    ) -> None:
        """Persist AI recommendations and summary on the blueprint."""
        blueprint.ai_recommendations = ai_recommendations
        blueprint.ai_summary = ai_summary
        blueprint.updated_at = datetime.utcnow()
        await self.db.commit()

    async def complete_wizard(
        self,
        blueprint_kwargs: dict,
        steps_data: list[dict],
        integrations_data: list[dict],
    ) -> JourneyBlueprint:
        """
        Atomically create blueprint + steps + integrations from wizard submission.
        Returns the blueprint reloaded with all relationships.
        """
        blueprint = JourneyBlueprint(**blueprint_kwargs)
        self.db.add(blueprint)
        await self.db.flush()

        for step_kwargs in steps_data:
            step = JourneyStep(**step_kwargs, blueprint_id=blueprint.id)
            self.db.add(step)

        for integration_kwargs in integrations_data:
            integration = JourneyIntegration(**integration_kwargs, blueprint_id=blueprint.id)
            self.db.add(integration)

        await self.db.commit()

        # TENANT-EXEMPT: blueprint.id retornado por INSERT acima (same-session); blueprint_kwargs vem do caller tenant-gated
        result = await self.db.execute(
            select(JourneyBlueprint)
            .options(
                selectinload(JourneyBlueprint.steps),
                selectinload(JourneyBlueprint.integrations)
            )
            .where(JourneyBlueprint.id == blueprint.id)
        )
        return result.scalar_one()

    # --- Step methods ---

    async def list_steps(self, blueprint_id: UUID) -> list[JourneyStep]:
        """List all steps for a blueprint ordered by .order."""
        result = await self.db.execute(
            select(JourneyStep)
            .where(JourneyStep.blueprint_id == blueprint_id)
            .order_by(JourneyStep.order)
        )
        return list(result.scalars().all())

    async def get_step(self, step_id: UUID) -> JourneyStep | None:
        """Get a step by ID."""
        result = await self.db.execute(
            select(JourneyStep).where(JourneyStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def create_step(self, **kwargs) -> JourneyStep:
        """Create a step, commit, and refresh."""
        step = JourneyStep(**kwargs)
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def update_step(self, step: JourneyStep, update_data: dict) -> JourneyStep:
        """Apply update_data to step, set updated_at, commit and refresh."""
        for field, value in update_data.items():
            setattr(step, field, value)
        step.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def delete_step(self, step: JourneyStep) -> None:
        """Delete a step and commit."""
        await self.db.delete(step)
        await self.db.commit()

    # --- Integration methods ---

    async def list_integrations(self, blueprint_id: UUID) -> list[JourneyIntegration]:
        """List all integrations for a blueprint ordered by integration_type."""
        result = await self.db.execute(
            select(JourneyIntegration)
            .where(JourneyIntegration.blueprint_id == blueprint_id)
            .order_by(JourneyIntegration.integration_type)
        )
        return list(result.scalars().all())

    async def get_integration(self, integration_id: UUID) -> JourneyIntegration | None:
        """Get an integration by ID."""
        result = await self.db.execute(
            select(JourneyIntegration).where(JourneyIntegration.id == integration_id)
        )
        return result.scalar_one_or_none()

    async def create_integration(self, **kwargs) -> JourneyIntegration:
        """Create an integration, commit, and refresh."""
        integration = JourneyIntegration(**kwargs)
        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def update_integration(self, integration: JourneyIntegration, update_data: dict) -> JourneyIntegration:
        """Apply update_data to integration, set updated_at, commit and refresh."""
        for field, value in update_data.items():
            setattr(integration, field, value)
        integration.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(integration)
        return integration
