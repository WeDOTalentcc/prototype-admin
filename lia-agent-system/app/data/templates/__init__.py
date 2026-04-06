"""
app/data/templates/__init__.py — Job Templates Library.

Data is loaded from app/data/fixtures/*.json via app/data/loader.py.
Public API (get_all_system_templates, get_template_categories, search_templates)
is unchanged from the previous Python-dict implementation.
"""
from app.data.loader import (
    get_administrativo_templates as _get_admin,
)
from app.data.loader import (
    get_category_aliases,
    get_subcategory_aliases,
    get_template_categories,
)
from app.data.loader import (
    get_cs_templates as _get_cs2,
)
from app.data.loader import (
    get_customer_success_templates as _get_cs,
)
from app.data.loader import (
    get_engenharia_templates as _get_engenharia,
)
from app.data.loader import (
    get_financas_templates as _get_financas,
)
from app.data.loader import (
    get_juridico_templates as _get_juridico,
)
from app.data.loader import (
    get_marketing_templates as _get_marketing,
)
from app.data.loader import (
    get_operacoes_templates as _get_operacoes,
)
from app.data.loader import (
    get_rh_templates as _get_rh,
)
from app.data.loader import (
    get_saude_templates as _get_saude,
)
from app.data.loader import (
    get_tech_templates as _get_tech,
)
from app.data.loader import (
    get_vendas_templates as _get_vendas,
)
from app.data.templates.financas import get_all_financas_templates
from app.data.templates.tecnologia import get_all_tecnologia_templates

# Re-export for backward compat (used in app/data/templates/__init__ imports)
TECH_TEMPLATES = None          # lazy via _get_tech()
CURATED_AVAILABLE = True


def _normalize_category(category: str) -> str:
    aliases = get_category_aliases()
    return aliases.get(category, category)


def _normalize_subcategory(subcategory: str) -> str:
    aliases = get_subcategory_aliases()
    return aliases.get(subcategory, subcategory)


def _expand_curated_template(template: dict) -> list:
    """Expand a curated template into multiple templates by seniority."""
    expanded = []
    seniorities = template.get("seniorities", ["junior", "pleno", "senior"])
    salary_ranges = template.get("salary_range", {})

    category = _normalize_category(template.get("category", ""))
    subcategory = _normalize_subcategory(template.get("subcategory", ""))

    for seniority in seniorities:
        salary = salary_ranges.get(seniority, {"min": 5000, "max": 15000})
        expanded.append({
            "category": category,
            "subcategory": subcategory,
            "title": template.get("title"),
            "title_normalized": template.get("title", "").lower().strip(),
            "title_alternatives": template.get("title_alternatives", []),
            "seniority": seniority,
            "default_description": template.get("default_description", ""),
            "default_responsibilities": template.get("default_responsibilities", []),
            "default_requirements": template.get("default_requirements", ""),
            "default_nice_to_have": template.get("default_nice_to_have", ""),
            "default_education": template.get("default_education", []),
            "default_certifications": template.get("default_certifications", []),
            "default_languages": template.get("default_languages", []),
            "default_skills": template.get("default_skills", []),
            "default_behavioral": template.get("default_behavioral", []),
            "salary_range_min": salary.get("min"),
            "salary_range_max": salary.get("max"),
            "salary_currency": "BRL",
            "work_model": template.get("work_model", "hybrid"),
            "employment_type": template.get("employment_type", "clt"),
            "is_system": True,
            "is_active": True,
            "usage_count": 0,
            "popularity_score": 0.0,
            "quality_score": 0.9,
            "template_metadata": {
                "source": "curated",
                "curated_version": "2024.02",
                "market": "brazil",
            },
        })
    return expanded


def get_all_curated_templates() -> list:
    """Get all curated templates expanded by seniority."""
    all_templates = []
    curated_sources = [
        _get_tech(), _get_vendas(), _get_rh(), _get_financas(),
        _get_marketing(), _get_operacoes(), _get_juridico(),
        _get_engenharia(), _get_cs(), _get_admin(), _get_cs2(), _get_saude(),
    ]
    for source in curated_sources:
        for template in source:
            all_templates.extend(_expand_curated_template(template))
    return all_templates


def get_all_system_templates() -> list:
    """Get all system templates (curated first, legacy fallback)."""
    all_templates = []
    curated = get_all_curated_templates()
    all_templates.extend(curated)

    curated_categories = {t.get("category") for t in curated}
    for template in [*get_all_tecnologia_templates(), *get_all_financas_templates()]:
        if template.get("category") not in curated_categories:
            template.update({
                "is_system": True,
                "is_active": True,
                "usage_count": 0,
                "popularity_score": 0.0,
                "quality_score": 0.8,
                "template_metadata": {"source": "legacy"},
            })
            all_templates.append(template)

    return all_templates


def get_templates_by_category(category: str) -> list:
    return [t for t in get_all_system_templates() if t.get("category") == category]


def get_templates_by_subcategory(category: str, subcategory: str) -> list:
    return [
        t for t in get_all_system_templates()
        if t.get("category") == category and t.get("subcategory") == subcategory
    ]


def search_templates(query: str) -> list:
    query_lower = query.lower()
    return [
        t for t in get_all_system_templates()
        if query_lower in t.get("title", "").lower()
        or any(query_lower in alt.lower() for alt in t.get("title_alternatives", []))
    ]


def get_template_count() -> dict:
    counts: dict = {}
    for t in get_all_system_templates():
        cat = t.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts
