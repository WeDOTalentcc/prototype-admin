"""
CompanyProfileRepository — ADR-001 canonical.
Queries de perfil de empresa (company_profiles, company_culture_profiles).

Centraliza reads e writes de perfil/cultura/additional_data com
_require_company_id fail-closed em todos os métodos públicos.
"""
from typing import Optional
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CompanyProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_full_profile(self, company_id: str) -> Optional[dict]:
        """
        Retorna perfil completo da empresa (company_profiles + company_culture_profiles).
        Fail-closed em company_id.
        Migrado de _wrap_get_company_profile (ADR-001 Wave C-2 Agent D).
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
            SELECT cp.id, cp.name, cp.trading_name, cp.cnpj, cp.website,
                   cp.hr_email, cp.hr_phone, cp.address, cp.industry,
                   cp.company_size, cp.employee_count, cp.founded_year,
                   cp.linkedin_url, cp.logo_url, cp.additional_data,
                   ccp.mission, ccp.vision, ccp.values, ccp.core_competencies,
                   ccp.evp_bullets, ccp.work_model, ccp.hybrid_days_onsite,
                   ccp.employment_types, ccp.growth_opportunities,
                   ccp.team_dynamics, ccp.leadership_style, ccp.dei_initiatives,
                   ccp.sustainability, ccp.social_impact, ccp.tech_stack,
                   ccp.engineering_culture, ccp.default_languages,
                   ccp.seniority_levels, ccp.default_behavioral_competencies,
                   ccp.default_salary_ranges, ccp.locations, ccp.headquarters,
                   ccp.lia_field_toggles, ccp.lia_instructions, ccp.ai_persona
            FROM company_profiles cp
            LEFT JOIN company_culture_profiles ccp ON ccp.company_id = cp.id::text
            WHERE cp.id::text = :company_id
            LIMIT 1
            """),
            {"company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def get_culture_profile(self, company_id: str) -> Optional[dict]:
        """
        Retorna perfil de cultura da empresa.
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
            SELECT id, company_id, mission, vision, values, core_competencies,
                   evp_bullets, work_model, hybrid_days_onsite, employment_types,
                   growth_opportunities, team_dynamics, leadership_style,
                   dei_initiatives, sustainability, social_impact,
                   tech_stack, engineering_culture, default_languages,
                   seniority_levels, default_behavioral_competencies,
                   default_salary_ranges, locations, headquarters,
                   lia_field_toggles, lia_instructions, ai_persona,
                   additional_data, updated_at
            FROM company_culture_profiles
            WHERE company_id = :company_id
            LIMIT 1
            """),
            {"company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def get_workforce_plan(self, company_id: str) -> Optional[dict]:
        """
        Retorna o workforce_plan armazenado em company_culture_profiles.additional_data.
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text(
                "SELECT id, COALESCE(additional_data->'workforce_plan', null::jsonb) AS prev_plan "
                "FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"
            ),
            {"company_id": company_id},
        )
        row = result.mappings().fetchone()
        if row is None:
            return None
        raw = row.get("prev_plan")
        try:
            plan = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            plan = None
        return {"row_id": row["id"], "workforce_plan": plan}

    async def upsert_workforce_plan(
        self,
        company_id: str,
        plan_json: str,
        *,
        session=None,
    ) -> None:
        """
        Upsert do workforce_plan em company_culture_profiles.additional_data.
        Fail-closed em company_id.
        Aceita session injetada (para transação atômica com audit wrapper).
        Migrado de _import_workforce_plan_impl (ADR-001 Wave C-2 Agent D).
        """
        self._require_company_id(company_id)
        db = session or self.db
        existing = await db.execute(
            text(
                "SELECT id FROM company_culture_profiles WHERE company_id = :company_id LIMIT 1"
            ),
            {"company_id": company_id},
        )
        row = existing.mappings().fetchone()
        if row:
            await db.execute(
                text("""
                    UPDATE company_culture_profiles
                    SET additional_data = jsonb_set(
                        COALESCE(additional_data, {}::jsonb),
                        '{workforce_plan}',
                        :plan_data::jsonb
                    ),
                    updated_at = NOW()
                    WHERE company_id = :company_id
                """),
                {"plan_data": plan_json, "company_id": company_id},
            )
        else:
            await db.execute(
                text("""
                    INSERT INTO company_culture_profiles
                    (company_id, additional_data, created_at, updated_at)
                    VALUES (
                        :company_id,
                        jsonb_build_object('workforce_plan', :plan_data::jsonb),
                        NOW(), NOW()
                    )
                """),
                {"company_id": company_id, "plan_data": plan_json},
            )
