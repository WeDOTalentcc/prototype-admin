"""
Archetype Builder Service - Build search archetypes from search specifications.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from lia_models.archetype import SearchArchetype

logger = logging.getLogger(__name__)


def extract_tags_from_search_spec(search_spec: dict[str, Any]) -> list[str]:
    """
    Extract human-readable tags from a search specification.
    
    Extracts tags from:
    - skills, required_skills, preferred_skills → tags
    - job_title → tag
    - industry, industries → tags
    - location, location_city, location_state → tags
    - seniority → tag
    - work_model → tag
    
    Args:
        search_spec: The search specification dictionary
        
    Returns:
        List of extracted tags (deduplicated, lowercase)
    """
    tags = set()
    
    skill_fields = ['skills', 'required_skills', 'preferred_skills', 'technical_skills', 'soft_skills']
    for field in skill_fields:
        value = search_spec.get(field)
        if isinstance(value, list):
            for skill in value:
                if isinstance(skill, str) and skill.strip():
                    tags.add(skill.strip())
        elif isinstance(value, str) and value.strip():
            tags.add(value.strip())
    
    job_title = search_spec.get('job_title') or search_spec.get('title') or search_spec.get('position')
    if isinstance(job_title, str) and job_title.strip():
        tags.add(job_title.strip())
    elif isinstance(job_title, list):
        for title in job_title:
            if isinstance(title, str) and title.strip():
                tags.add(title.strip())
    
    for field in ['industry', 'industries', 'sector', 'sectors']:
        value = search_spec.get(field)
        if isinstance(value, list):
            for ind in value:
                if isinstance(ind, str) and ind.strip():
                    tags.add(ind.strip())
        elif isinstance(value, str) and value.strip():
            tags.add(value.strip())
    
    location_fields = ['location', 'location_city', 'location_state', 'city', 'state', 'region']
    for field in location_fields:
        value = search_spec.get(field)
        if isinstance(value, str) and value.strip():
            tags.add(value.strip())
        elif isinstance(value, list):
            for loc in value:
                if isinstance(loc, str) and loc.strip():
                    tags.add(loc.strip())
    
    seniority = search_spec.get('seniority') or search_spec.get('seniority_level') or search_spec.get('experience_level')
    if isinstance(seniority, str) and seniority.strip():
        tags.add(seniority.strip())
    elif isinstance(seniority, list):
        for sen in seniority:
            if isinstance(sen, str) and sen.strip():
                tags.add(sen.strip())
    
    work_model = search_spec.get('work_model') or search_spec.get('work_type') or search_spec.get('remote')
    if isinstance(work_model, str) and work_model.strip():
        tags.add(work_model.strip())
    elif isinstance(work_model, bool):
        if work_model:
            tags.add("remoto")
    
    certifications = search_spec.get('certifications')
    if isinstance(certifications, list):
        for cert in certifications:
            if isinstance(cert, str) and cert.strip():
                tags.add(cert.strip())
    
    languages = search_spec.get('languages')
    if isinstance(languages, list):
        for lang in languages:
            if isinstance(lang, str) and lang.strip():
                tags.add(lang.strip())
    elif isinstance(languages, dict):
        for lang in languages.keys():
            if isinstance(lang, str) and lang.strip():
                tags.add(lang.strip())
    
    tags_list = sorted([tag for tag in tags if len(tag) > 1])
    
    return tags_list


def _generate_archetype_id(name: str) -> str:
    """
    Generate a slug-based ID from the archetype name.
    
    Args:
        name: The archetype name
        
    Returns:
        A URL-friendly ID string
    """
    slug = name.lower().strip()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    if len(slug) > 40:
        slug = slug[:40].rstrip('-')
    
    short_uuid = str(uuid.uuid4())[:8]
    return f"{slug}-{short_uuid}"


def _extract_query_from_search_spec(search_spec: dict[str, Any]) -> str:
    """
    Build a natural language query from the search specification.
    
    Args:
        search_spec: The search specification dictionary
        
    Returns:
        A natural language query string
    """
    parts = []
    
    job_title = search_spec.get('job_title') or search_spec.get('title') or search_spec.get('position')
    if isinstance(job_title, str) and job_title.strip():
        parts.append(job_title.strip())
    elif isinstance(job_title, list) and job_title:
        parts.append(job_title[0].strip())
    
    seniority = search_spec.get('seniority') or search_spec.get('seniority_level')
    if isinstance(seniority, str) and seniority.strip():
        parts.append(f"nível {seniority.strip()}")
    
    skills = []
    for field in ['skills', 'required_skills', 'technical_skills']:
        value = search_spec.get(field)
        if isinstance(value, list):
            skills.extend([s for s in value if isinstance(s, str) and s.strip()])
        elif isinstance(value, str) and value.strip():
            skills.append(value.strip())
    
    if skills:
        skills_display = skills[:5]
        parts.append(f"com experiência em {', '.join(skills_display)}")
    
    industry = search_spec.get('industry') or search_spec.get('industries')
    if isinstance(industry, str) and industry.strip():
        parts.append(f"na área de {industry.strip()}")
    elif isinstance(industry, list) and industry:
        parts.append(f"na área de {industry[0].strip()}")
    
    location = search_spec.get('location') or search_spec.get('location_city')
    if isinstance(location, str) and location.strip():
        parts.append(f"em {location.strip()}")
    
    if not parts:
        return "Busca de candidatos"
    
    return " ".join(parts)


def _extract_filters_from_search_spec(search_spec: dict[str, Any]) -> dict[str, Any]:
    """
    Extract structured filters from the search specification.
    
    Args:
        search_spec: The search specification dictionary
        
    Returns:
        A dictionary of filters suitable for the archetype
    """
    filters = {}
    
    seniority = search_spec.get('seniority') or search_spec.get('seniority_level')
    if seniority:
        filters['seniority'] = seniority
    
    skills = []
    for field in ['skills', 'required_skills', 'technical_skills', 'preferred_skills']:
        value = search_spec.get(field)
        if isinstance(value, list):
            skills.extend([s for s in value if isinstance(s, str)])
        elif isinstance(value, str):
            skills.append(value)
    if skills:
        filters['skills'] = list(set(skills))
    
    exp_min = search_spec.get('experience_years_min') or search_spec.get('min_experience')
    if exp_min:
        filters['experience_years_min'] = exp_min
    
    exp_max = search_spec.get('experience_years_max') or search_spec.get('max_experience')
    if exp_max:
        filters['experience_years_max'] = exp_max
    
    work_model = search_spec.get('work_model') or search_spec.get('work_type')
    if work_model:
        filters['work_model'] = work_model
    
    for field in ['location', 'location_city', 'location_state', 'city', 'state']:
        value = search_spec.get(field)
        if value:
            filters[field] = value
    
    languages = search_spec.get('languages')
    if languages:
        filters['languages'] = languages
    
    certifications = search_spec.get('certifications')
    if certifications:
        filters['certifications'] = certifications
    
    return filters


def build_archetype_from_search(
    search_spec: dict[str, Any],
    name: str,
    description: str | None,
    emoji: str | None,
    company_id: str,
    user_id: str
) -> SearchArchetype:
    """
    Build a complete SearchArchetype from a search specification.
    
    Args:
        search_spec: The search specification dictionary
        name: Name for the archetype
        description: Optional description
        emoji: Optional emoji icon (defaults to 🎯)
        company_id: The company ID for multi-tenancy
        user_id: The user who created this archetype
        
    Returns:
        A SearchArchetype instance (not yet persisted)
    """
    tags = extract_tags_from_search_spec(search_spec)
    
    archetype_id = _generate_archetype_id(name)
    
    query = search_spec.get('query') or search_spec.get('natural_query') or _extract_query_from_search_spec(search_spec)
    
    filters = _extract_filters_from_search_spec(search_spec)
    
    industry = search_spec.get('industry')
    if isinstance(industry, list) and industry:
        industry = industry[0]
    elif not isinstance(industry, str):
        industry = None
    
    seniority = search_spec.get('seniority') or search_spec.get('seniority_level')
    if isinstance(seniority, list) and seniority:
        seniority = seniority[0]
    elif not isinstance(seniority, str):
        seniority = None
    
    archetype = SearchArchetype(
        id=archetype_id,
        name=name,
        description=description or f"Arquétipo criado a partir de busca: {name}",
        emoji=emoji or "🎯",
        query=query,
        filters=filters,
        tags=tags,
        industry=industry,
        seniority=seniority,
        is_default=False,
        is_active=True,
        usage_count=0,
        company_id=company_id,
        created_by=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Built archetype '{name}' with {len(tags)} tags for company {company_id}")
    
    return archetype
