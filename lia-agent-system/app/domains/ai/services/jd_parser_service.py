"""
JDParserService — Job Description extraction and requirements structuring.

Extracted from JobIntakeAgent._handle_extract_jd (Sprint 5).
Callers should use this service directly instead of going through the deprecated agent.
"""
import json
import logging
import re
from typing import Any

from app.domains.job_management.services.jd_template_cache_service import jd_template_cache_service
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.shared.robustness.input_validation import detect_language

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Prompt templates (canonical copies; agent still has its own)         #
# ------------------------------------------------------------------ #

_JD_PROMPT_PT = """Você é um especialista em análise de descrições de vagas (Job Descriptions).
Analise a descrição da vaga abaixo e extraia TODOS os requisitos de forma estruturada.

## Descrição da Vaga:
{job_description}

## Instruções:
Extraia os requisitos nas seguintes categorias:
1. Requisitos Técnicos, 2. Experiência, 3. Formação, 4. Soft Skills, 5. Outros

Para cada requisito classifique: ESSENTIAL | IMPORTANT | NICE_TO_HAVE

Responda APENAS com JSON válido no formato:
{{"job_title":"...","requirements":[{{"requirement":"...","category":"technical|experience|education|soft_skill|other","priority":"essential|important|nice_to_have","description":"..."}}],"is_affirmative":false,"affirmative_criteria_primary":null}}"""

_JD_PROMPT_EN = """You are an expert in analyzing job descriptions.
Extract ALL requirements in a structured format from the job description below.

## Job Description:
{job_description}

Respond ONLY with valid JSON:
{{"job_title":"...","requirements":[{{"requirement":"...","category":"technical|experience|education|soft_skill|other","priority":"essential|important|nice_to_have","description":"..."}}],"is_affirmative":false,"affirmative_criteria_primary":null}}"""

_PRIORITY_MAP = {
    "essential": RequirementPriorityEnum.ESSENTIAL,
    "important": RequirementPriorityEnum.IMPORTANT,
    "nice_to_have": RequirementPriorityEnum.NICE_TO_HAVE,
}


class JDParserService:
    """Parses Job Descriptions and structures them as JobRequirements."""

    async def extract_requirements(
        self,
        jd_text: str,
        company_id: str = None,
    ) -> dict[str, Any]:
        """
        Extract structured requirements from raw JD text.

        Uses Gemini (primary) → Claude (fallback).
        Returns raw dict with keys: job_title, requirements, is_affirmative, etc.
        Raises RuntimeError if extraction fails.
        """
        from app.domains.ai.services.llm import llm_service

        cached = await jd_template_cache_service.get_cached_extraction(
            jd_text, company_id
        )
        if cached:
            logger.info(f"JD extraction cache hit for company {company_id}")
            return {k: v for k, v in cached.items() if not k.startswith("_cache")}

        detected_language = detect_language(jd_text)
        prompt_template = _JD_PROMPT_PT if detected_language != "en" else _JD_PROMPT_EN
        prompt = prompt_template.format(job_description=jd_text)

        try:
            response_text = await llm_service.generate(prompt)
        except Exception as exc:
            logger.warning(f"Default LLM failed for JD extraction, falling back to Claude: {exc}")
            response_text = await llm_service.generate(prompt, provider="claude")

        match = re.search(r"\{[\s\S]*\}", response_text)
        if not match:
            raise RuntimeError("Could not parse JSON from LLM response")

        extracted_data: dict[str, Any] = json.loads(match.group())

        await jd_template_cache_service.cache_extraction(
            jd_text, company_id, extracted_data
        )
        logger.info(f"JD extraction cached for company {company_id}")
        return extracted_data

    def to_requirement_creates(
        self, extracted_data: dict[str, Any]
    ) -> list[JobRequirementCreate]:
        """Convert raw extraction dict into typed JobRequirementCreate objects."""
        result = []
        for req in extracted_data.get("requirements", []):
            priority = _PRIORITY_MAP.get(
                req.get("priority", "important"), RequirementPriorityEnum.IMPORTANT
            )
            result.append(
                JobRequirementCreate(
                    requirement=req.get("requirement", ""),
                    description=req.get("description"),
                    priority=priority,
                    category=req.get("category"),
                )
            )
        return result


jd_parser_service = JDParserService()
