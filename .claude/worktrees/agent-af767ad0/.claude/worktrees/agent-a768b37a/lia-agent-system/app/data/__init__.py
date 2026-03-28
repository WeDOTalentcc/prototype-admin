# Curated job templates for Brazilian market
from .curated_templates_tech import TECH_TEMPLATES
from .curated_templates_vendas import VENDAS_TEMPLATES
from .curated_templates_rh import RH_TEMPLATES
from .curated_templates_financas import FINANCAS_TEMPLATES
from .curated_templates_marketing import MARKETING_TEMPLATES

# Combined list of all curated templates
ALL_CURATED_TEMPLATES = (
    TECH_TEMPLATES +
    VENDAS_TEMPLATES +
    RH_TEMPLATES +
    FINANCAS_TEMPLATES +
    MARKETING_TEMPLATES
)

def get_all_templates():
    """Return all curated templates."""
    return ALL_CURATED_TEMPLATES

def get_templates_by_category(category: str):
    """Return templates filtered by category."""
    return [t for t in ALL_CURATED_TEMPLATES if t.get("category") == category]

def get_template_count():
    """Return total count of curated templates."""
    return len(ALL_CURATED_TEMPLATES)
