"""
AdminRepository -- session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/admin.py.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertRule
from app.models.task import TaskTemplate
from app.shared.services.seed_service import clear_demo_data, seed_demo_data

logger = logging.getLogger(__name__)


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_task_template_by_name(self, name: str):
        result = await self.db.execute(
            select(TaskTemplate).where(TaskTemplate.name == name)
        )
        return result.scalar_one_or_none()

    async def create_task_template(self, template_data: dict):
        template = TaskTemplate(**template_data)
        self.db.add(template)
        return template

    async def flush(self) -> None:
        await self.db.flush()

    async def get_alert_rule_by_name(self, name: str):
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.name == name)
        )
        return result.scalar_one_or_none()

    async def create_alert_rule(self, rule_data: dict):
        rule = AlertRule(**rule_data)
        self.db.add(rule)
        return rule

    async def seed_task_templates(self, templates: list) -> dict:
        results = {"created": 0, "skipped": 0, "details": []}
        for template_data in templates:
            existing = await self.get_task_template_by_name(template_data["name"])
            if existing:
                logger.info("TaskTemplate %r already exists, skipping", template_data["name"])
                results["skipped"] += 1
                results["details"].append({
                    "name": template_data["name"],
                    "status": "skipped",
                    "reason": "already_exists",
                })
            else:
                await self.create_task_template(template_data)
                logger.info("Created TaskTemplate: %r", template_data["name"])
                results["created"] += 1
                results["details"].append({
                    "name": template_data["name"],
                    "status": "created",
                })
        await self.flush()
        return results

    async def seed_alert_rules(self, rules: list) -> dict:
        results = {"created": 0, "skipped": 0, "details": []}
        for rule_data in rules:
            existing = await self.get_alert_rule_by_name(rule_data["name"])
            if existing:
                logger.info("AlertRule %r already exists, skipping", rule_data["name"])
                results["skipped"] += 1
                results["details"].append({
                    "name": rule_data["name"],
                    "status": "skipped",
                    "reason": "already_exists",
                })
            else:
                await self.create_alert_rule(rule_data)
                logger.info("Created AlertRule: %r", rule_data["name"])
                results["created"] += 1
                results["details"].append({
                    "name": rule_data["name"],
                    "status": "created",
                })
        await self.flush()
        return results

    async def seed_demo(self) -> dict:
        return await seed_demo_data(self.db)

    async def clear_demo(self) -> dict:
        return await clear_demo_data(self.db)
