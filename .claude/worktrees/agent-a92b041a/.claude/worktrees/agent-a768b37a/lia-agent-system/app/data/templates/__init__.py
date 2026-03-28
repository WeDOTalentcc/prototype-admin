"""
Job Templates Library - 50 curated templates across 5 organizational areas.

This module provides market-aligned, curated job templates for Fast Track creation.
Templates are curated for the Brazilian market with current, relevant skills.

Templates include:
- Title and alternative titles (PT-BR + EN)
- Technical skills with levels and weights (current market-relevant)
- Behavioral competencies with justifications
- Responsibilities by seniority
- Realistic salary ranges for Brazilian market (BRL)
"""

from .tecnologia import get_all_tecnologia_templates
from .financas import get_all_financas_templates

# Import curated templates
try:
    from ..curated_templates_tech import TECH_TEMPLATES
    from ..curated_templates_vendas import VENDAS_TEMPLATES
    from ..curated_templates_rh import RH_TEMPLATES
    from ..curated_templates_financas import FINANCAS_TEMPLATES
    from ..curated_templates_marketing import MARKETING_TEMPLATES
    from ..curated_templates_operacoes import OPERACOES_TEMPLATES, JURIDICO_TEMPLATES, ENGENHARIA_TEMPLATES
    from ..curated_templates_customer_success import CUSTOMER_SUCCESS_TEMPLATES
    from ..curated_templates_administrativo import ADMINISTRATIVO_TEMPLATES
    from ..curated_templates_cs import CS_TEMPLATES
    from ..curated_templates_saude import SAUDE_TEMPLATES
    CURATED_AVAILABLE = True
except ImportError:
    CURATED_AVAILABLE = False
    TECH_TEMPLATES = []
    VENDAS_TEMPLATES = []
    RH_TEMPLATES = []
    FINANCAS_TEMPLATES = []
    MARKETING_TEMPLATES = []
    OPERACOES_TEMPLATES = []
    JURIDICO_TEMPLATES = []
    ENGENHARIA_TEMPLATES = []
    CUSTOMER_SUCCESS_TEMPLATES = []
    ADMINISTRATIVO_TEMPLATES = []
    CS_TEMPLATES = []
    SAUDE_TEMPLATES = []

TEMPLATE_CATEGORIES = {
    "tecnologia": {
        "display_name": "Tecnologia / TI",
        "icon": "💻",
        "color": "#3B82F6",
        "subcategories": [
            {"name": "desenvolvimento", "display_name": "Desenvolvimento de Software"},
            {"name": "dados", "display_name": "Dados e Analytics"},
            {"name": "infra", "display_name": "Infraestrutura e Cloud"},
            {"name": "infraestrutura", "display_name": "Infraestrutura e Cloud"},
            {"name": "seguranca", "display_name": "Segurança da Informação"},
            {"name": "design", "display_name": "Design e UX/UI"},
            {"name": "gestao", "display_name": "Gestão e Liderança TI"},
            {"name": "suporte", "display_name": "Suporte"},
            {"name": "arquitetura", "display_name": "Arquitetura de Software"},
            {"name": "qualidade", "display_name": "QA e Testes"},
            {"name": "produto", "display_name": "Produto e Product Management"},
        ],
    },
    "financas": {
        "display_name": "Finanças / Contabilidade / Tributário",
        "icon": "💰",
        "color": "#10B981",
        "subcategories": [
            {"name": "contabilidade", "display_name": "Contabilidade"},
            {"name": "tributario", "display_name": "Fiscal e Tributário"},
            {"name": "fiscal", "display_name": "Fiscal e Tributário"},
            {"name": "controladoria", "display_name": "Controladoria e FP&A"},
            {"name": "planejamento", "display_name": "Planejamento Financeiro"},
            {"name": "tesouraria", "display_name": "Tesouraria"},
            {"name": "auditoria", "display_name": "Auditoria"},
            {"name": "credito", "display_name": "Crédito e Risco"},
            {"name": "gestao", "display_name": "Gestão Financeira"},
        ],
    },
    "rh": {
        "display_name": "Recursos Humanos / People",
        "icon": "👥",
        "color": "#8B5CF6",
        "subcategories": [
            {"name": "recrutamento", "display_name": "Recrutamento e Seleção"},
            {"name": "generalista", "display_name": "Generalista e BP"},
            {"name": "business_partner", "display_name": "HR Business Partner"},
            {"name": "dp", "display_name": "Departamento Pessoal"},
            {"name": "administracao", "display_name": "Administração de Pessoal"},
            {"name": "remuneracao", "display_name": "Remuneração e Benefícios"},
            {"name": "td", "display_name": "Treinamento e Desenvolvimento"},
            {"name": "desenvolvimento", "display_name": "Desenvolvimento Organizacional"},
            {"name": "cultura", "display_name": "Cultura e D&I"},
            {"name": "gestao", "display_name": "Gestão de RH"},
        ],
    },
    "comercial": {
        "display_name": "Comercial / Vendas",
        "icon": "📈",
        "color": "#F59E0B",
        "subcategories": [
            {"name": "inside_sales", "display_name": "Inside Sales"},
            {"name": "field_sales", "display_name": "Field Sales / Vendas Externas"},
            {"name": "vendas_tecnicas", "display_name": "Vendas Técnicas"},
            {"name": "canais", "display_name": "Canais e Parcerias"},
            {"name": "sales_ops", "display_name": "Operações de Vendas"},
            {"name": "ecommerce", "display_name": "E-commerce"},
            {"name": "customer_success", "display_name": "Customer Success"},
            {"name": "gestao", "display_name": "Gestão Comercial"},
        ],
    },
    "marketing": {
        "display_name": "Marketing / Comunicação",
        "icon": "📣",
        "color": "#EC4899",
        "subcategories": [
            {"name": "digital", "display_name": "Marketing Digital"},
            {"name": "conteudo", "display_name": "Conteúdo e Social Media"},
            {"name": "branding", "display_name": "Branding e Comunicação"},
            {"name": "produto", "display_name": "Produto e Trade Marketing"},
            {"name": "analytics", "display_name": "Analytics e Inteligência"},
            {"name": "performance", "display_name": "Performance Marketing"},
            {"name": "growth", "display_name": "Growth Marketing"},
            {"name": "gestao", "display_name": "Gestão de Marketing"},
        ],
    },
    "operacoes": {
        "display_name": "Operações / Supply Chain / Logística",
        "icon": "📦",
        "color": "#6366F1",
        "subcategories": [
            {"name": "logistica", "display_name": "Logística"},
            {"name": "supply_chain", "display_name": "Supply Chain"},
            {"name": "compras", "display_name": "Compras / Procurement"},
            {"name": "comex", "display_name": "Comércio Exterior"},
            {"name": "qualidade", "display_name": "Qualidade"},
            {"name": "gestao", "display_name": "Gestão de Operações"},
        ],
    },
    "engenharia": {
        "display_name": "Engenharia",
        "icon": "⚙️",
        "color": "#0EA5E9",
        "subcategories": [
            {"name": "civil", "display_name": "Engenharia Civil"},
            {"name": "mecanica", "display_name": "Engenharia Mecânica"},
            {"name": "eletrica", "display_name": "Engenharia Elétrica e Eletrônica"},
            {"name": "producao", "display_name": "Engenharia de Produção"},
            {"name": "quimica", "display_name": "Engenharia Química e de Alimentos"},
            {"name": "outras", "display_name": "Outras Engenharias"},
            {"name": "seguranca_trabalho", "display_name": "Segurança do Trabalho"},
        ],
    },
    "juridico": {
        "display_name": "Jurídico / Compliance",
        "icon": "⚖️",
        "color": "#14B8A6",
        "subcategories": [
            {"name": "corporativo", "display_name": "Jurídico Corporativo"},
            {"name": "societario", "display_name": "Direito Societário"},
            {"name": "trabalhista", "display_name": "Trabalhista e Previdenciário"},
            {"name": "compliance", "display_name": "Compliance e Governança"},
            {"name": "gestao", "display_name": "Gestão Jurídica"},
            {"name": "suporte", "display_name": "Suporte Jurídico"},
        ],
    },
    "administrativo": {
        "display_name": "Administrativo / Secretariado",
        "icon": "📋",
        "color": "#78716C",
        "subcategories": [
            {"name": "geral", "display_name": "Administrativo Geral"},
            {"name": "secretariado", "display_name": "Secretariado Executivo"},
            {"name": "facilities", "display_name": "Facilities e Office"},
            {"name": "compras", "display_name": "Compras e Contratos"},
            {"name": "documentacao", "display_name": "Documentação e Arquivo"},
            {"name": "patrimonio", "display_name": "Patrimônio e Frotas"},
            {"name": "gestao", "display_name": "Gestão Administrativa"},
        ],
    },
    "customer_success": {
        "display_name": "Atendimento / Customer Success",
        "icon": "🎧",
        "color": "#22C55E",
        "subcategories": [
            {"name": "cs_management", "display_name": "Gestão de Customer Success"},
            {"name": "cs", "display_name": "Customer Success"},
            {"name": "gestao", "display_name": "Gestão de CS"},
            {"name": "operacoes", "display_name": "Operações de CS"},
            {"name": "onboarding", "display_name": "Onboarding"},
            {"name": "educacao", "display_name": "Educação de Clientes"},
            {"name": "implementation", "display_name": "Implementação e Onboarding"},
            {"name": "implementacao", "display_name": "Implementação"},
            {"name": "tam", "display_name": "Technical Account Management"},
            {"name": "experiencia", "display_name": "Experiência do Cliente"},
            {"name": "cx", "display_name": "Customer Experience"},
            {"name": "suporte", "display_name": "Suporte Técnico"},
        ],
    },
    "saude": {
        "display_name": "Saúde / Hospitalar",
        "icon": "🏥",
        "color": "#EF4444",
        "subcategories": [
            {"name": "enfermagem", "display_name": "Enfermagem"},
            {"name": "medicina", "display_name": "Medicina"},
            {"name": "terapias", "display_name": "Terapias (Fisio, Fono, Nutri, Psico)"},
            {"name": "farmacia", "display_name": "Farmácia"},
            {"name": "gestao", "display_name": "Gestão em Saúde"},
            {"name": "outras_saude", "display_name": "Outras Profissões de Saúde"},
            {"name": "gestao_hospitalar", "display_name": "Gestão Hospitalar"},
        ],
    },
    "educacao": {
        "display_name": "Educação / Treinamento",
        "icon": "🎓",
        "color": "#A855F7",
        "subcategories": [
            {"name": "docencia", "display_name": "Docência"},
            {"name": "elearning", "display_name": "E-learning"},
        ],
    },
    "qualidade": {
        "display_name": "Qualidade / Processos",
        "icon": "✅",
        "color": "#06B6D4",
        "subcategories": [
            {"name": "qualidade", "display_name": "Qualidade"},
            {"name": "processos", "display_name": "Processos e Melhoria Contínua"},
        ],
    },
}


CATEGORY_ALIASES = {
    "vendas": "comercial",
    "recursos_humanos": "rh",
}

SUBCATEGORY_ALIASES = {
    "infraestrutura": "infra",
}


def _normalize_category(category: str) -> str:
    """Normalize category to canonical name."""
    return CATEGORY_ALIASES.get(category, category)


def _normalize_subcategory(subcategory: str) -> str:
    """Normalize subcategory to canonical name."""
    return SUBCATEGORY_ALIASES.get(subcategory, subcategory)


def _expand_curated_template(template: dict) -> list:
    """
    Expand a curated template into multiple templates by seniority.
    
    Each curated template has seniorities and salary_range fields that
    need to be expanded into individual templates.
    """
    expanded = []
    seniorities = template.get("seniorities", ["junior", "pleno", "senior"])
    salary_ranges = template.get("salary_range", {})
    
    category = _normalize_category(template.get("category", ""))
    subcategory = _normalize_subcategory(template.get("subcategory", ""))
    
    for seniority in seniorities:
        salary = salary_ranges.get(seniority, {"min": 5000, "max": 15000})
        
        expanded_template = {
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
                "market": "brazil"
            }
        }
        expanded.append(expanded_template)
    
    return expanded


def get_all_curated_templates() -> list:
    """
    Get all curated templates expanded by seniority.
    
    Returns a list of template dictionaries ready for database seeding.
    """
    if not CURATED_AVAILABLE:
        return []
    
    all_templates = []
    
    # Combine all curated template sources
    curated_sources = [
        TECH_TEMPLATES,
        VENDAS_TEMPLATES,
        RH_TEMPLATES,
        FINANCAS_TEMPLATES,
        MARKETING_TEMPLATES,
        OPERACOES_TEMPLATES,
        JURIDICO_TEMPLATES,
        ENGENHARIA_TEMPLATES,
        CUSTOMER_SUCCESS_TEMPLATES,
        ADMINISTRATIVO_TEMPLATES,
        CS_TEMPLATES,
        SAUDE_TEMPLATES,
    ]
    
    for source in curated_sources:
        for template in source:
            expanded = _expand_curated_template(template)
            all_templates.extend(expanded)
    
    return all_templates


def get_all_system_templates() -> list:
    """
    Get all system templates from all areas.
    
    Priority:
    1. Curated templates (market-aligned, current skills)
    2. Legacy templates (fallback for other areas)
    
    Returns a list of template dictionaries ready for database seeding.
    """
    all_templates = []
    
    # First, add curated templates (priority)
    curated = get_all_curated_templates()
    all_templates.extend(curated)
    
    # Add legacy templates only for categories not covered by curated
    curated_categories = {t.get("category") for t in curated}
    
    legacy_templates = []
    legacy_templates.extend(get_all_tecnologia_templates())
    legacy_templates.extend(get_all_financas_templates())
    
    for template in legacy_templates:
        # Only add if category not already covered by curated templates
        if template.get("category") not in curated_categories:
            template["is_system"] = True
            template["is_active"] = True
            template["usage_count"] = 0
            template["popularity_score"] = 0.0
            template["quality_score"] = 0.8
            template["template_metadata"] = {"source": "legacy"}
            all_templates.append(template)
    
    return all_templates


def get_template_categories() -> dict:
    """Get all template categories with metadata."""
    return TEMPLATE_CATEGORIES


def get_templates_by_category(category: str) -> list:
    """Get all templates for a specific category."""
    all_templates = get_all_system_templates()
    return [t for t in all_templates if t.get("category") == category]


def get_templates_by_subcategory(category: str, subcategory: str) -> list:
    """Get all templates for a specific subcategory."""
    all_templates = get_all_system_templates()
    return [
        t for t in all_templates 
        if t.get("category") == category and t.get("subcategory") == subcategory
    ]


def search_templates(query: str) -> list:
    """
    Search templates by title or alternative titles.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching templates
    """
    all_templates = get_all_system_templates()
    query_lower = query.lower()
    
    results = []
    for template in all_templates:
        title_match = query_lower in template.get("title", "").lower()
        alt_match = any(
            query_lower in alt.lower() 
            for alt in template.get("title_alternatives", [])
        )
        if title_match or alt_match:
            results.append(template)
    
    return results


def get_template_count() -> dict:
    """Get template count by category."""
    all_templates = get_all_system_templates()
    
    counts = {}
    for template in all_templates:
        category = template.get("category", "unknown")
        counts[category] = counts.get(category, 0) + 1
    
    return counts
