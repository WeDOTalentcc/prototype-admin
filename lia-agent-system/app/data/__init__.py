"""
app/data/__init__.py — Job template data access.

All data is loaded from app/data/fixtures/*.json via loader.py.
Public API is unchanged from the previous Python-dict implementation.
"""
from app.data.loader import (
    get_customer_success_templates,
    get_financas_templates,
    get_marketing_templates,
    get_rh_templates,
    get_tech_templates,
    get_vendas_templates,
)


def get_all_templates() -> list:
    """Return all curated templates combined."""
    return (
        get_tech_templates()
        + get_vendas_templates()
        + get_rh_templates()
        + get_financas_templates()
        + get_marketing_templates()
        + get_customer_success_templates()
    )


# Keep backward-compat name
ALL_CURATED_TEMPLATES = None  # lazy — use get_all_templates() instead


def get_templates_by_category(category: str) -> list:
    """Return templates filtered by category."""
    return [t for t in get_all_templates() if t.get("category") == category]


def get_template_count() -> int:
    """Return total count of curated templates."""
    return len(get_all_templates())
