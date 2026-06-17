"""
Route service facade for company management.
Encapsulates business logic from API routes (app/api/v1/company.py) for portability.
Placed in shared services since company spans multiple domains.
"""
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.services.benefits_service import (
    BENEFIT_CATEGORIES,
    resolve_benefit_category,
)
from app.domains.company.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.domains.company.repositories.culture_profile_repository import (
    CultureProfileRepository,
)
from app.domains.company.repositories.culture_value_repository import (
    CultureValueRepository,
)
from app.domains.company.repositories.department_repository import DepartmentRepository

logger = logging.getLogger(__name__)


class CompanyRouteService:
    """Encapsulates business logic from company API routes."""

    async def submit_onboarding(
        self,
        db: AsyncSession,
        company_name: str,
        trade_name: str | None = None,
        cnpj: str | None = None,
        address: str | None = None,
        sector: str | None = None,
        employee_count: int | None = None,
        website: str | None = None,
        linkedin_url: str | None = None,
        logo_url: str | None = None,
        responsible_name: str | None = None,
        responsible_email: str | None = None,
        responsible_phone: str | None = None,
        responsible_position: str | None = None,
        preferred_contact_time: str | None = None,
        hiring_volume: str | None = None,
        job_types: list[str] | None = None,
        current_ats: str | None = None,
        main_challenges: list[str] | None = None,
        main_priority: str | None = None,
        platform_expectations: str | None = None,
        communication_channels: list[str] | None = None,
        allow_lia_contact: bool | None = None,
        additional_notes: str | None = None,
        work_model: str | None = None,
        company_id: str | None = None,
        culture_profile_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process onboarding wizard submission.

        Extracted from POST /onboarding (lines 147-297).
        Creates or updates company profile and optionally creates/updates culture profile.

        Returns:
            Dict with keys: success, message, company_id, company_name
        """
        from lia_models.company import CompanyCultureProfile, CompanyProfile

        company_repo = CompanyProfileRepository(db)
        culture_repo = CultureProfileRepository(db)

        profile = None

        if company_id:
            try:
                company_uuid = UUID(company_id)
                profile = await company_repo.get_by_id(company_uuid)
            except ValueError:
                logger.warning(f"Invalid company_id format: {company_id}")

        if not profile:
            profile = await company_repo.get_default()

        onboarding_metadata = {
            "hiring_volume": hiring_volume,
            "job_types": job_types,
            "current_ats": current_ats,
            "main_challenges": main_challenges,
            "main_priority": main_priority,
            "platform_expectations": platform_expectations,
            "communication_channels": communication_channels,
            "allow_lia_contact": allow_lia_contact,
            "additional_notes": additional_notes,
            "responsible_name": responsible_name,
            "responsible_email": responsible_email,
            "responsible_phone": responsible_phone,
            "responsible_position": responsible_position,
            "preferred_contact_time": preferred_contact_time,
            "work_model": work_model,
            "onboarding_completed_at": datetime.utcnow().isoformat(),
        }

        if profile:
            profile.name = company_name
            profile.trading_name = trade_name
            profile.cnpj = cnpj
            profile.address = address
            profile.industry = sector
            profile.company_size = employee_count
            profile.website = website
            profile.linkedin_url = linkedin_url
            profile.logo_url = logo_url
            profile.hr_email = responsible_email
            profile.hr_phone = responsible_phone
            profile.updated_at = datetime.utcnow()
            if profile.additional_data:
                profile.additional_data.update(onboarding_metadata)
            else:
                profile.additional_data = onboarding_metadata
        else:
            profile = CompanyProfile(
                name=company_name,
                trading_name=trade_name,
                cnpj=cnpj,
                address=address,
                industry=sector,
                company_size=employee_count,
                website=website,
                linkedin_url=linkedin_url,
                logo_url=logo_url,
                hr_email=responsible_email,
                hr_phone=responsible_phone,
                is_default=True,
                additional_data=onboarding_metadata,
            )
            db.add(profile)

        await db.commit()
        await db.refresh(profile)

        if culture_profile_data:
            culture_profile = await culture_repo.get_for_company(profile.id)

            cp = culture_profile_data
            if culture_profile:
                culture_profile.mission = cp.get("mission")
                culture_profile.vision = cp.get("vision")
                culture_profile.values = cp.get("values", [])
                culture_profile.evp_bullets = cp.get("evp_bullets", [])
                culture_profile.openness_score = cp.get("openness_score", 50)
                culture_profile.conscientiousness_score = cp.get("conscientiousness_score", 50)
                culture_profile.extraversion_score = cp.get("extraversion_score", 50)
                culture_profile.agreeableness_score = cp.get("agreeableness_score", 50)
                culture_profile.stability_score = cp.get("stability_score", 50)
                culture_profile.source = "onboarding"
                culture_profile.website_url = website
                culture_profile.updated_at = datetime.utcnow()
            else:
                culture_profile = CompanyCultureProfile(
                    company_id=profile.id,
                    mission=cp.get("mission"),
                    vision=cp.get("vision"),
                    values=cp.get("values", []),
                    evp_bullets=cp.get("evp_bullets", []),
                    openness_score=cp.get("openness_score", 50),
                    conscientiousness_score=cp.get("conscientiousness_score", 50),
                    extraversion_score=cp.get("extraversion_score", 50),
                    agreeableness_score=cp.get("agreeableness_score", 50),
                    stability_score=cp.get("stability_score", 50),
                    source="onboarding",
                    website_url=website,
                )
                db.add(culture_profile)

            await db.commit()

        return {
            "success": True,
            "message": "Onboarding data received successfully",
            "company_id": str(profile.id),
            "company_name": profile.name,
        }

    async def enrich_company_profile(
        self,
        linkedin_url: str | None = None,
        glassdoor_company_name: str | None = None,
    ) -> dict[str, Any]:
        """Enrich company profile with LinkedIn and Glassdoor data.

        Extracted from POST /enrich (lines 300-376).
        NOTE: Delegates to apify_service for actual scraping.

        Returns:
            Dict with keys: success, linkedin_data, glassdoor_data,
            enriched_culture, errors
        """
        from app.domains.sourcing.services.apify_service import apify_service

        errors: list[str] = []
        linkedin_data: dict[str, Any] = {}
        glassdoor_data: dict[str, Any] = {}
        enriched_culture: dict[str, Any] = {}

        if not linkedin_url and not glassdoor_company_name:
            return {
                "success": False,
                "error": "At least one of linkedin_url or glassdoor_company_name must be provided",
            }

        if linkedin_url:
            linkedin_data = await apify_service.scrape_linkedin_company(linkedin_url)
            if not linkedin_data:
                errors.append("Failed to fetch LinkedIn data or no data found")

        if glassdoor_company_name:
            glassdoor_data = await apify_service.scrape_glassdoor_company(glassdoor_company_name)
            if not glassdoor_data:
                errors.append("Failed to fetch Glassdoor data or no data found")

        if linkedin_data.get("description"):
            enriched_culture["company_description"] = linkedin_data["description"]
        if linkedin_data.get("tagline"):
            enriched_culture["tagline"] = linkedin_data["tagline"]
        if linkedin_data.get("specialties"):
            enriched_culture["specialties"] = linkedin_data["specialties"]
        if glassdoor_data.get("mission"):
            enriched_culture["mission"] = glassdoor_data["mission"]
        if glassdoor_data.get("overview"):
            enriched_culture["vision"] = glassdoor_data["overview"]
        if glassdoor_data.get("employee_pros"):
            enriched_culture["culture_highlights"] = glassdoor_data["employee_pros"]
        if glassdoor_data.get("culture_rating"):
            enriched_culture["culture_rating"] = glassdoor_data["culture_rating"]
        if glassdoor_data.get("overall_rating"):
            enriched_culture["overall_rating"] = glassdoor_data["overall_rating"]
        if glassdoor_data.get("work_life_balance"):
            enriched_culture["work_life_balance"] = glassdoor_data["work_life_balance"]

        return {
            "success": bool(linkedin_data or glassdoor_data),
            "linkedin_data": linkedin_data,
            "glassdoor_data": glassdoor_data,
            "enriched_culture": enriched_culture,
            "errors": errors,
        }

    async def generate_evp(
        self, db: AsyncSession, profile_id: UUID
    ) -> dict[str, Any]:
        """Generate EVP (Employee Value Proposition) analysis using LLM.

        Extracted from POST /profile/{profile_id}/generate-evp (lines 752-894).
        NOTE: Delegates to llm_service for LLM generation.

        Returns:
            Dict with keys: success, evp_analysis (or error)
        """
        from app.domains.ai.services.llm import llm_service

        company_repo = CompanyProfileRepository(db)
        profile = await company_repo.get_by_id(profile_id)

        if not profile:
            return {"success": False, "error": "Company profile not found"}

        additional_data = profile.additional_data or {}

        company_info = {
            "name": profile.name,
            "description": profile.description or additional_data.get("company_description", ""),
            "tagline": additional_data.get("tagline", ""),
            "mission": additional_data.get("mission", ""),
            "vision": additional_data.get("vision", ""),
            "values": additional_data.get("values", ""),
            "culture_highlights": additional_data.get("culture_highlights", []),
            "industry": profile.industry or "",
            "company_size": profile.company_size or "",
            "specialties": additional_data.get("specialties", []),
            "work_life_balance": additional_data.get("work_life_balance", ""),
            "culture_rating": additional_data.get("culture_rating", ""),
            "overall_rating": additional_data.get("overall_rating", ""),
        }

        sources: list[str] = []
        if company_info.get("description") or company_info.get("tagline"):
            sources.append("linkedin")
        if company_info.get("mission") or company_info.get("culture_highlights"):
            sources.append("glassdoor")

        specialties_str = ', '.join(company_info['specialties']) if isinstance(company_info['specialties'], list) else company_info['specialties']
        culture_str = ', '.join(company_info['culture_highlights']) if isinstance(company_info['culture_highlights'], list) else company_info['culture_highlights']

        prompt = f"""Você é um especialista em Employer Branding e Employee Value Proposition (EVP).
Analise os dados da empresa abaixo e gere uma análise de EVP estruturada em português brasileiro.

DADOS DA EMPRESA:
- Nome: {company_info['name']}
- Descrição: {company_info['description']}
- Tagline: {company_info['tagline']}
- Missão: {company_info['mission']}
- Visão: {company_info['vision']}
- Valores: {company_info['values']}
- Setor: {company_info['industry']}
- Porte: {company_info['company_size']}
- Especialidades: {specialties_str}
- Destaques culturais: {culture_str}
- Rating de cultura: {company_info['culture_rating']}
- Rating geral: {company_info['overall_rating']}
- Work-life balance: {company_info['work_life_balance']}

GERE UMA ANÁLISE EVP NO FORMATO JSON EXATO ABAIXO:
{{
  "statement": "Uma frase de 1-2 sentenças que resume a proposta de valor única da empresa para seus colaboradores",
  "pillars": [
    {{
      "name": "Nome do Pilar 1 (ex: Crescimento, Inovação, Impacto)",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }},
    {{
      "name": "Nome do Pilar 2",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }},
    {{
      "name": "Nome do Pilar 3",
      "description": "Descrição detalhada do pilar",
      "evidence": "Evidência concreta baseada nos dados da empresa"
    }}
  ],
  "tone_guidance": ["adjetivo1", "adjetivo2", "adjetivo3", "adjetivo4", "adjetivo5"],
  "candidate_promise": "Uma frase clara sobre o que a empresa promete ao candidato que se juntar à equipe"
}}

REGRAS:
1. Baseie-se APENAS nos dados fornecidos
2. Os pilares devem refletir os diferenciais reais da empresa
3. O tone_guidance deve ter 5 adjetivos que guiem a comunicação com candidatos
4. Use linguagem profissional mas acessível
5. Responda APENAS com o JSON, sem texto adicional"""

        evp_response = await llm_service.generate(prompt, provider="gemini")

        try:
            evp_response = evp_response.strip()
            if evp_response.startswith("```json"):
                evp_response = evp_response[7:]
            if evp_response.startswith("```"):
                evp_response = evp_response[3:]
            if evp_response.endswith("```"):
                evp_response = evp_response[:-3]
            evp_response = evp_response.strip()

            evp_data = json.loads(evp_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse EVP response: {e}")
            return {"success": False, "error": f"Falha ao processar resposta da IA: {str(e)}"}

        evp_analysis = {
            "statement": evp_data.get("statement", ""),
            "pillars": evp_data.get("pillars", []),
            "tone_guidance": evp_data.get("tone_guidance", []),
            "candidate_promise": evp_data.get("candidate_promise", ""),
            "generated_at": datetime.utcnow().isoformat(),
            "sources": sources,
        }

        updated_additional_data = {**(profile.additional_data or {}), "evp_analysis": evp_analysis}
        profile.additional_data = updated_additional_data
        profile.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(profile)

        return {"success": True, "evp_analysis": evp_analysis}

    async def get_company_with_relations(
        self, db: AsyncSession, profile_id: UUID
    ) -> dict[str, Any] | None:
        """Get company profile with all related data.

        Extracted from GET /profile/{profile_id}/full (lines 694-743).
        Loads departments, benefits, and culture values.

        Returns:
            Dict with profile data plus departments, benefits, culture_values lists,
            or None if not found.
        """
        company_repo = CompanyProfileRepository(db)
        dept_repo = DepartmentRepository(db)
        benefit_repo = BenefitRepository(db)
        culture_value_repo = CultureValueRepository(db)

        profile = await company_repo.get_by_id(profile_id)

        if not profile:
            return None

        departments = await dept_repo.list_active_for_company(profile_id)
        benefits = await benefit_repo.list_active_for_company(profile_id)
        culture_values = await culture_value_repo.list_active_for_company(profile_id)

        def _serialize(obj: Any) -> dict[str, Any]:
            result_dict = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.name, None)
                if isinstance(val, datetime):
                    val = val.isoformat()
                elif isinstance(val, UUID):
                    val = str(val)
                result_dict[col.name] = val
            return result_dict

        return {
            "profile": _serialize(profile),
            "departments": [_serialize(d) for d in departments],
            "benefits": [_serialize(b) for b in benefits],
            "culture_values": [_serialize(c) for c in culture_values],
        }

    async def list_departments(
        self,
        db: AsyncSession,
        company_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """List departments with member counts.

        Extracted from GET /departments (lines 897-931).

        Returns:
            List of department dicts with headcount field added.
        """
        dept_repo = DepartmentRepository(db)

        departments = await dept_repo.list_filtered(
            company_id=company_id,
            include_inactive=include_inactive,
        )

        dept_dicts: list[dict[str, Any]] = []
        for dept in departments:
            member_count = await dept_repo.count_members(dept.id)

            dept_dict = {
                "id": str(dept.id),
                "company_id": str(dept.company_id) if dept.company_id else None,
                "name": dept.name,
                "description": getattr(dept, "description", None),
                "order": dept.order,
                "is_active": dept.is_active,
                "headcount": member_count,
            }
            dept_dicts.append(dept_dict)

        return dept_dicts

    async def create_department(
        self,
        db: AsyncSession,
        company_id: str | None,
        department_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new department.

        Extracted from POST /departments (lines 934-976).
        Resolves company_id to actual profile if needed.

        Returns:
            Dict with department data including id.
        """
        company_repo = CompanyProfileRepository(db)
        dept_repo = DepartmentRepository(db)

        resolved_company_id = None
        if company_id:
            try:
                resolved_company_id = UUID(company_id)
            except ValueError:
                pass

        if not resolved_company_id:
            profile = await company_repo.get_latest_default()
            if not profile:
                profile = await company_repo.get_latest_active()
            if profile:
                resolved_company_id = profile.id

        department = await dept_repo.create(
            {"company_id": resolved_company_id, **department_data}
        )

        return {
            "id": str(department.id),
            "company_id": str(department.company_id) if department.company_id else None,
            "name": department.name,
            "is_active": department.is_active,
        }

    async def update_department(
        self,
        db: AsyncSession,
        department_id: UUID,
        update_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update a department.

        Extracted from PUT /departments/{department_id} (lines 979-1010).

        Returns:
            Updated department dict or None if not found.
        """
        dept_repo = DepartmentRepository(db)
        department = await dept_repo.get_by_id(department_id)

        if not department:
            return None

        for field, value in update_data.items():
            setattr(department, field, value)
        department.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(department)

        return {
            "id": str(department.id),
            "company_id": str(department.company_id) if department.company_id else None,
            "name": department.name,
            "is_active": department.is_active,
        }

    async def delete_department(
        self, db: AsyncSession, department_id: UUID
    ) -> dict[str, Any] | None:
        """Soft delete a department.

        Extracted from DELETE /departments/{department_id} (lines 1013-1039).

        Returns:
            Dict with success/message or None if not found.
        """
        dept_repo = DepartmentRepository(db)
        department = await dept_repo.get_by_id(department_id)

        if not department:
            return None

        department.is_active = False
        department.updated_at = datetime.utcnow()
        await db.commit()

        return {"success": True, "message": "Department deleted"}

    async def auto_enrich_company(
        self, db: AsyncSession, profile_id: UUID
    ) -> dict[str, Any]:
        """Automatically enrich company profile after onboarding.

        Extracted from POST /auto-enrich/{profile_id} (lines 387-601).
        NOTE: Delegates to apify_service for scraping and llm_service for inference.
        Heavy inline logic for LinkedIn/Glassdoor data parsing and LLM-based field inference.

        Returns:
            Dict with keys: success, fields_updated, apify_data, inferred_data, errors
        """
        from app.domains.sourcing.services.apify_service import apify_service
        from app.domains.ai.services.llm import llm_service

        company_repo = CompanyProfileRepository(db)
        culture_repo = CultureProfileRepository(db)

        errors: list[str] = []
        fields_updated: list[str] = []
        apify_data: dict[str, Any] = {}
        inferred_data: dict[str, Any] = {}

        profile = await company_repo.get_by_id(profile_id)
        if not profile:
            return {"success": False, "error": "Company profile not found"}

        culture_profile = await culture_repo.get_for_company(profile_id)

        linkedin_data: dict[str, Any] = {}
        glassdoor_data: dict[str, Any] = {}

        linkedin_url = profile.linkedin_url or (profile.additional_data or {}).get("linkedin_url")
        if linkedin_url:
            try:
                linkedin_data = await apify_service.scrape_linkedin_company(linkedin_url)
                apify_data["linkedin"] = linkedin_data
            except Exception as e:
                errors.append(f"LinkedIn enrichment failed: {str(e)}")

        if profile.name:
            try:
                glassdoor_data = await apify_service.scrape_glassdoor_company(profile.name)
                apify_data["glassdoor"] = glassdoor_data
            except Exception as e:
                errors.append(f"Glassdoor enrichment failed: {str(e)}")

        if linkedin_data:
            if linkedin_data.get("headquarters") and not profile.headquarters_city:
                hq = linkedin_data["headquarters"]
                if isinstance(hq, dict):
                    profile.headquarters_city = hq.get("city", "")
                    profile.headquarters_state = hq.get("state", "")
                    profile.headquarters_country = hq.get("country", "Brasil")
                elif isinstance(hq, str):
                    parts = hq.split(",")
                    if len(parts) >= 2:
                        profile.headquarters_city = parts[0].strip()
                        profile.headquarters_state = parts[1].strip()
                fields_updated.append("headquarters")

            if linkedin_data.get("founded") and not profile.founded_year:
                try:
                    profile.founded_year = int(linkedin_data["founded"])
                    fields_updated.append("founded_year")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("company_size") and not profile.employee_count:
                size_str = linkedin_data["company_size"]
                try:
                    if "-" in str(size_str):
                        nums = str(size_str).replace(",", "").replace("+", "").split("-")
                        profile.employee_count = int(nums[1]) if len(nums) > 1 else int(nums[0])
                    else:
                        profile.employee_count = int(str(size_str).replace(",", "").replace("+", ""))
                    fields_updated.append("employee_count")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("description"):
                if not profile.description:
                    profile.description = linkedin_data["description"]
                    fields_updated.append("description")
                if culture_profile and not culture_profile.culture_description:
                    culture_profile.culture_description = linkedin_data["description"]

        company_context = {
            "name": profile.name,
            "industry": profile.industry,
            "description": profile.description or linkedin_data.get("description", ""),
            "size": profile.company_size,
            "glassdoor_pros": glassdoor_data.get("employee_pros", []),
            "glassdoor_cons": glassdoor_data.get("employee_cons", []),
            "work_life_balance": glassdoor_data.get("work_life_balance", ""),
            "culture_rating": glassdoor_data.get("culture_rating", ""),
            "mission": culture_profile.mission if culture_profile else "",
            "vision": culture_profile.vision if culture_profile else "",
            "values": culture_profile.values if culture_profile else [],
        }

        if company_context.get("description") or company_context.get("mission"):
            pros_str = ', '.join(company_context['glassdoor_pros'][:3]) if company_context['glassdoor_pros'] else 'N/A'
            cons_str = ', '.join(company_context['glassdoor_cons'][:2]) if company_context['glassdoor_cons'] else 'N/A'
            values_str = ', '.join(company_context['values']) if company_context['values'] else 'N/A'
            desc_str = company_context['description'][:500] if company_context['description'] else 'N/A'

            inference_prompt = f"""Você é um especialista em cultura organizacional e employer branding.
Analise os dados da empresa abaixo e infira campos faltantes de forma consistente.

DADOS DISPONÍVEIS:
- Nome: {company_context['name']}
- Setor: {company_context['industry']}
- Descrição: {desc_str}
- Porte: {company_context['size']}
- Missão: {company_context['mission']}
- Visão: {company_context['vision']}
- Valores: {values_str}
- Avaliação cultura (Glassdoor): {company_context['culture_rating']}
- Work-life balance: {company_context['work_life_balance']}
- Pontos positivos (funcionários): {pros_str}
- Pontos negativos (funcionários): {cons_str}

GERE UM JSON COM OS CAMPOS ABAIXO (baseado nos dados disponíveis, use inferências razoáveis):
{{
  "work_model": "remoto|híbrido|presencial",
  "growth_opportunities": "Descrição breve das oportunidades de crescimento",
  "team_dynamics": "Descrição da dinâmica de trabalho em equipe",
  "leadership_style": "Estilo de liderança predominante",
  "core_competencies": ["competência1", "competência2", "competência3"],
  "diversity_initiatives": "Iniciativas de diversidade e inclusão (se houver indicações)",
  "sustainability": "Práticas de sustentabilidade (se houver indicações)",
  "social_impact": "Impacto social da empresa (se houver indicações)",
  "engineering_culture": "Cultura de engenharia/tecnologia (se aplicável ao setor)"
}}

REGRAS:
1. Use APENAS informações que podem ser inferidas dos dados
2. Se não houver base para inferir, use "Não especificado"
3. Para core_competencies, liste 3-5 competências comportamentais típicas do setor
4. Responda APENAS com o JSON, sem texto adicional"""

            try:
                llm_response = await llm_service.generate(inference_prompt, provider="gemini")
                llm_response = llm_response.strip()
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.startswith("```"):
                    llm_response = llm_response[3:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                llm_response = llm_response.strip()

                inferred = json.loads(llm_response)
                inferred_data = inferred

                additional = profile.additional_data or {}
                inferred_fields = [
                    "work_model", "growth_opportunities", "team_dynamics",
                    "leadership_style", "diversity_initiatives", "sustainability",
                    "social_impact", "engineering_culture",
                ]
                for field in inferred_fields:
                    if inferred.get(field) and inferred[field] != "Não especificado":
                        additional[field] = inferred[field]
                        fields_updated.append(field)

                profile.additional_data = additional

                if culture_profile and inferred.get("core_competencies"):
                    if not culture_profile.core_competencies or len(culture_profile.core_competencies) == 0:
                        culture_profile.core_competencies = inferred["core_competencies"]
                        fields_updated.append("core_competencies")

            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse LLM response: {str(e)}")
            except Exception as e:
                errors.append(f"LLM inference failed: {str(e)}")

        profile.updated_at = datetime.utcnow()
        if culture_profile:
            culture_profile.updated_at = datetime.utcnow()

        await db.commit()

        return {
            "success": len(fields_updated) > 0,
            "fields_updated": fields_updated,
            "apify_data": apify_data,
            "inferred_data": inferred_data,
            "errors": errors,
        }

    async def get_benefits_summary(
        self,
        db: AsyncSession,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a summary of company benefits for AI agents.

        Extracted from GET /benefits/summary (lines 1508-1600+).
        Includes formatted text ready for use in prompts.

        Returns:
            Dict with keys: total_count, active_count, highlighted_count,
            categories, formatted_text, benefits
        """
        import uuid as uuid_mod

        benefit_repo = BenefitRepository(db)

        scoped_company_id = uuid_mod.UUID(company_id) if company_id else None
        all_benefits = await benefit_repo.list_optional_company(scoped_company_id)

        active_benefits = [b for b in all_benefits if b.is_active]
        highlighted_benefits = [b for b in active_benefits if b.is_highlighted]

        # Canonical labels from benefits_service SSOT (v2, 14 categories)

        categories: dict[str, Any] = {}
        for benefit in active_benefits:
            cat = benefit.category or "other"
            if cat not in categories:
                categories[cat] = {
                    "name": BENEFIT_CATEGORIES.get(resolve_benefit_category(cat), cat),
                    "count": 0,
                    "benefits": [],
                }
            categories[cat]["count"] += 1
            categories[cat]["benefits"].append({
                "name": benefit.name,
                "description": benefit.description,
                "value_type": benefit.value_type,
                "value": benefit.value,
                "is_highlighted": benefit.is_highlighted,
            })

        formatted_lines = []
        for cat_key, cat_data in categories.items():
            formatted_lines.append(f"\n{cat_data['name']}:")
            for b in cat_data["benefits"]:
                highlight = " ⭐" if b.get("is_highlighted") else ""
                formatted_lines.append(f"  - {b['name']}{highlight}: {b.get('description', '')}")

        formatted_text = "\n".join(formatted_lines)

        benefits_list = [
            {
                "name": b.name,
                "description": b.description,
                "category": b.category,
                "is_highlighted": b.is_highlighted,
                "is_active": b.is_active,
            }
            for b in active_benefits
        ]

        return {
            "total_count": len(all_benefits),
            "active_count": len(active_benefits),
            "highlighted_count": len(highlighted_benefits),
            "categories": categories,
            "formatted_text": formatted_text,
            "benefits": benefits_list,
        }


company_route_service = CompanyRouteService()
