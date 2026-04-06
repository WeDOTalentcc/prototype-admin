
"""
Industry constants and normalization for bilingual (English/Portuguese) support.
Mirrors the frontend industry-constants.ts for consistency.
"""
from dataclasses import dataclass, field


@dataclass
class Industry:
    key: str
    label_pt: str
    label_en: str
    category: str
    synonyms: list[str] = field(default_factory=list)


INDUSTRY_CATEGORIES: dict[str, dict[str, str]] = {
    "technology": {"label_pt": "Tecnologia", "label_en": "Technology"},
    "finance": {"label_pt": "Finanças", "label_en": "Finance"},
    "consulting": {"label_pt": "Consultoria", "label_en": "Consulting"},
    "ecommerce_retail": {"label_pt": "E-commerce e Varejo", "label_en": "E-commerce & Retail"},
    "education": {"label_pt": "Educação", "label_en": "Education"},
    "healthcare": {"label_pt": "Saúde", "label_en": "Healthcare"},
    "marketing_agency": {"label_pt": "Marketing e Agências", "label_en": "Marketing & Agency"},
    "startup_ecosystem": {"label_pt": "Ecossistema Startup", "label_en": "Startup Ecosystem"},
    "legal": {"label_pt": "Jurídico", "label_en": "Legal"},
    "energy": {"label_pt": "Energia", "label_en": "Energy"},
    "manufacturing": {"label_pt": "Manufatura", "label_en": "Manufacturing"},
    "real_estate": {"label_pt": "Imobiliário", "label_en": "Real Estate"},
    "telecommunications": {"label_pt": "Telecomunicações", "label_en": "Telecommunications"},
    "media": {"label_pt": "Mídia", "label_en": "Media"},
    "other": {"label_pt": "Outros", "label_en": "Other"},
}


INDUSTRIES: list[Industry] = [
    # Technology
    Industry(
        key="Information Technology",
        label_pt="Tecnologia da Informação",
        label_en="Information Technology",
        category="technology",
        synonyms=["TI", "IT", "Tech", "Tecnologia", "Information Technology and Services"],
    ),
    Industry(
        key="Computer Software",
        label_pt="Software",
        label_en="Computer Software",
        category="technology",
        synonyms=["Software", "Desenvolvimento de Software", "Software Development", "SaaS"],
    ),
    Industry(
        key="Internet",
        label_pt="Internet",
        label_en="Internet",
        category="technology",
        synonyms=["Internet", "Web", "Online", "Digital"],
    ),
    Industry(
        key="Computer & Network Security",
        label_pt="Segurança da Informação",
        label_en="Computer & Network Security",
        category="technology",
        synonyms=["Cibersegurança", "Cybersecurity", "InfoSec", "Segurança Cibernética"],
    ),
    Industry(
        key="Cloud Computing",
        label_pt="Computação em Nuvem",
        label_en="Cloud Computing",
        category="technology",
        synonyms=["Cloud", "Nuvem", "AWS", "Azure", "GCP", "IaaS", "PaaS"],
    ),
    Industry(
        key="Artificial Intelligence",
        label_pt="Inteligência Artificial",
        label_en="Artificial Intelligence",
        category="technology",
        synonyms=["IA", "AI", "Machine Learning", "ML", "Deep Learning", "Aprendizado de Máquina"],
    ),
    Industry(
        key="Computer Games",
        label_pt="Jogos Digitais",
        label_en="Computer Games",
        category="technology",
        synonyms=["Games", "Jogos", "Gaming", "Video Games"],
    ),
    Industry(
        key="Semiconductors",
        label_pt="Semicondutores",
        label_en="Semiconductors",
        category="technology",
        synonyms=["Chips", "Hardware", "Microprocessadores"],
    ),
    Industry(
        key="Data Analytics",
        label_pt="Análise de Dados",
        label_en="Data Analytics",
        category="technology",
        synonyms=["Big Data", "Data Science", "Ciência de Dados", "Analytics", "BI", "Business Intelligence"],
    ),

    # Finance
    Industry(
        key="Banking",
        label_pt="Bancos",
        label_en="Banking",
        category="finance",
        synonyms=["Banco", "Bancos", "Banco Digital", "Digital Banking", "Neobank", "Neobanco"],
    ),
    Industry(
        key="Financial Services",
        label_pt="Serviços Financeiros",
        label_en="Financial Services",
        category="finance",
        synonyms=["Financeiro", "Finanças", "Finance", "Serviços Financeiros"],
    ),
    Industry(
        key="Fintech",
        label_pt="Fintech",
        label_en="Fintech",
        category="finance",
        synonyms=["Fintech", "Financial Technology", "Tecnologia Financeira"],
    ),
    Industry(
        key="Investment Banking",
        label_pt="Banco de Investimento",
        label_en="Investment Banking",
        category="finance",
        synonyms=["Investment Bank", "IB", "M&A", "Fusões e Aquisições"],
    ),
    Industry(
        key="Investment Management",
        label_pt="Gestão de Investimentos",
        label_en="Investment Management",
        category="finance",
        synonyms=["Asset Management", "Gestão de Ativos", "Investimentos", "Investments"],
    ),
    Industry(
        key="Capital Markets",
        label_pt="Mercado de Capitais",
        label_en="Capital Markets",
        category="finance",
        synonyms=["Mercado Financeiro", "Stock Market", "Bolsa de Valores"],
    ),
    Industry(
        key="Insurance",
        label_pt="Seguros",
        label_en="Insurance",
        category="finance",
        synonyms=["Seguro", "Insurtech", "Insurance Tech"],
    ),
    Industry(
        key="Payments",
        label_pt="Pagamentos",
        label_en="Payments",
        category="finance",
        synonyms=["Pagamentos", "Payment Processing", "Meios de Pagamento", "Payment Gateway"],
    ),
    Industry(
        key="Cryptocurrency",
        label_pt="Criptomoedas",
        label_en="Cryptocurrency",
        category="finance",
        synonyms=["Crypto", "Blockchain", "Web3", "DeFi", "Bitcoin", "Ethereum"],
    ),

    # Consulting
    Industry(
        key="Management Consulting",
        label_pt="Consultoria de Gestão",
        label_en="Management Consulting",
        category="consulting",
        synonyms=["Consultoria", "Consulting", "Strategy Consulting", "Consultoria Estratégica"],
    ),
    Industry(
        key="Professional Training & Coaching",
        label_pt="Treinamento e Coaching",
        label_en="Professional Training & Coaching",
        category="consulting",
        synonyms=["Coaching", "Treinamento", "Training", "Desenvolvimento Profissional"],
    ),
    Industry(
        key="Human Resources",
        label_pt="Recursos Humanos",
        label_en="Human Resources",
        category="consulting",
        synonyms=["RH", "HR", "People", "Gestão de Pessoas", "Talent Acquisition"],
    ),
    Industry(
        key="Staffing and Recruiting",
        label_pt="Recrutamento e Seleção",
        label_en="Staffing and Recruiting",
        category="consulting",
        synonyms=["Recrutamento", "Recruiting", "Headhunting", "R&S", "Talent Acquisition"],
    ),
    Industry(
        key="Outsourcing/Offshoring",
        label_pt="Terceirização",
        label_en="Outsourcing/Offshoring",
        category="consulting",
        synonyms=["Outsourcing", "BPO", "Body Shop"],
    ),

    # E-commerce & Retail
    Industry(
        key="E-commerce",
        label_pt="E-commerce",
        label_en="E-commerce",
        category="ecommerce_retail",
        synonyms=["Ecommerce", "Comércio Eletrônico", "Online Retail", "Loja Virtual", "Marketplace"],
    ),
    Industry(
        key="Retail",
        label_pt="Varejo",
        label_en="Retail",
        category="ecommerce_retail",
        synonyms=["Varejo", "Loja", "Comércio", "Commerce"],
    ),
    Industry(
        key="Consumer Goods",
        label_pt="Bens de Consumo",
        label_en="Consumer Goods",
        category="ecommerce_retail",
        synonyms=["FMCG", "CPG", "Fast Moving Consumer Goods", "Produtos de Consumo"],
    ),
    Industry(
        key="Luxury Goods & Jewelry",
        label_pt="Luxo e Joias",
        label_en="Luxury Goods & Jewelry",
        category="ecommerce_retail",
        synonyms=["Luxo", "Luxury", "Premium"],
    ),
    Industry(
        key="Apparel & Fashion",
        label_pt="Moda e Vestuário",
        label_en="Apparel & Fashion",
        category="ecommerce_retail",
        synonyms=["Moda", "Fashion", "Vestuário", "Roupas", "Apparel"],
    ),
    Industry(
        key="Food & Beverages",
        label_pt="Alimentos e Bebidas",
        label_en="Food & Beverages",
        category="ecommerce_retail",
        synonyms=["Alimentos", "Bebidas", "Food", "F&B", "CPG Food"],
    ),
    Industry(
        key="Supermarkets",
        label_pt="Supermercados",
        label_en="Supermarkets",
        category="ecommerce_retail",
        synonyms=["Supermercado", "Grocery", "Mercearia"],
    ),
    Industry(
        key="Logistics and Supply Chain",
        label_pt="Logística",
        label_en="Logistics and Supply Chain",
        category="ecommerce_retail",
        synonyms=["Logística", "Supply Chain", "Cadeia de Suprimentos", "Fulfillment", "Last Mile"],
    ),

    # Education
    Industry(
        key="E-Learning",
        label_pt="E-Learning",
        label_en="E-Learning",
        category="education",
        synonyms=["EdTech", "Edtech", "Education Technology", "EAD", "Ensino a Distância", "Online Learning"],
    ),
    Industry(
        key="Higher Education",
        label_pt="Ensino Superior",
        label_en="Higher Education",
        category="education",
        synonyms=["Universidade", "University", "Faculdade", "Academia"],
    ),
    Industry(
        key="Education Management",
        label_pt="Gestão Educacional",
        label_en="Education Management",
        category="education",
        synonyms=["Educação", "Education", "Ensino", "Escola"],
    ),
    Industry(
        key="Primary/Secondary Education",
        label_pt="Educação Básica",
        label_en="Primary/Secondary Education",
        category="education",
        synonyms=["Ensino Fundamental", "Ensino Médio", "K-12", "Escola"],
    ),
    Industry(
        key="Research",
        label_pt="Pesquisa",
        label_en="Research",
        category="education",
        synonyms=["Pesquisa", "R&D", "P&D", "Research & Development"],
    ),

    # Healthcare
    Industry(
        key="Hospital & Health Care",
        label_pt="Hospitais e Saúde",
        label_en="Hospital & Health Care",
        category="healthcare",
        synonyms=["Hospital", "Saúde", "Healthcare", "Health", "Clínica", "Clinic"],
    ),
    Industry(
        key="Health Tech",
        label_pt="Healthtech",
        label_en="Health Tech",
        category="healthcare",
        synonyms=["Healthtech", "Health Technology", "Digital Health", "Saúde Digital", "Telemedicina", "Telemedicine"],
    ),
    Industry(
        key="Pharmaceuticals",
        label_pt="Farmacêutico",
        label_en="Pharmaceuticals",
        category="healthcare",
        synonyms=["Pharma", "Farmácia", "Medicamentos", "Drugs"],
    ),
    Industry(
        key="Medical Devices",
        label_pt="Dispositivos Médicos",
        label_en="Medical Devices",
        category="healthcare",
        synonyms=["Medical Equipment", "Equipamentos Médicos", "MedTech"],
    ),
    Industry(
        key="Biotechnology",
        label_pt="Biotecnologia",
        label_en="Biotechnology",
        category="healthcare",
        synonyms=["Biotech", "Life Sciences", "Ciências da Vida"],
    ),
    Industry(
        key="Mental Health Care",
        label_pt="Saúde Mental",
        label_en="Mental Health Care",
        category="healthcare",
        synonyms=["Saúde Mental", "Psicologia", "Psychology", "Therapy", "Terapia"],
    ),
    Industry(
        key="Health/Wellness/Fitness",
        label_pt="Bem-estar e Fitness",
        label_en="Health/Wellness/Fitness",
        category="healthcare",
        synonyms=["Wellness", "Fitness", "Bem-estar", "Academia", "Gym"],
    ),

    # Marketing & Agency
    Industry(
        key="Marketing and Advertising",
        label_pt="Marketing e Publicidade",
        label_en="Marketing and Advertising",
        category="marketing_agency",
        synonyms=["Marketing", "Publicidade", "Advertising", "Ads", "Propaganda"],
    ),
    Industry(
        key="Digital Marketing",
        label_pt="Marketing Digital",
        label_en="Digital Marketing",
        category="marketing_agency",
        synonyms=["Marketing Digital", "Performance Marketing", "Growth", "Growth Marketing"],
    ),
    Industry(
        key="Agência Digital",
        label_pt="Agência Digital",
        label_en="Digital Agency",
        category="marketing_agency",
        synonyms=["Digital Agency", "Agência", "Agency", "Creative Agency", "Agência Criativa"],
    ),
    Industry(
        key="Public Relations",
        label_pt="Relações Públicas",
        label_en="Public Relations",
        category="marketing_agency",
        synonyms=["PR", "RP", "Comunicação", "Communications"],
    ),
    Industry(
        key="Design",
        label_pt="Design",
        label_en="Design",
        category="marketing_agency",
        synonyms=["Design", "UX", "UI", "Product Design", "Graphic Design", "Design Gráfico"],
    ),
    Industry(
        key="Market Research",
        label_pt="Pesquisa de Mercado",
        label_en="Market Research",
        category="marketing_agency",
        synonyms=["Pesquisa", "Research", "Consumer Insights", "Analytics"],
    ),

    # Startup Ecosystem
    Industry(
        key="Venture Capital & Private Equity",
        label_pt="Venture Capital e Private Equity",
        label_en="Venture Capital & Private Equity",
        category="startup_ecosystem",
        synonyms=["VC", "PE", "Venture Capital", "Private Equity", "Capital de Risco", "Investidor"],
    ),
    Industry(
        key="Startup",
        label_pt="Startup",
        label_en="Startup",
        category="startup_ecosystem",
        synonyms=["Startup", "Start-up", "Startups", "Scaleup", "Scale-up"],
    ),
    Industry(
        key="Accelerator",
        label_pt="Aceleradora",
        label_en="Accelerator",
        category="startup_ecosystem",
        synonyms=["Aceleradora", "Incubadora", "Incubator", "Accelerator Program"],
    ),

    # Legal
    Industry(
        key="Law Practice",
        label_pt="Advocacia",
        label_en="Law Practice",
        category="legal",
        synonyms=["Advocacia", "Law Firm", "Escritório de Advocacia", "Jurídico", "Legal"],
    ),
    Industry(
        key="Legal Services",
        label_pt="Serviços Jurídicos",
        label_en="Legal Services",
        category="legal",
        synonyms=["Legal", "Jurídico", "Law", "Direito"],
    ),
    Industry(
        key="Legal Tech",
        label_pt="Legaltech",
        label_en="Legal Tech",
        category="legal",
        synonyms=["Legaltech", "Lawtech", "Legal Technology"],
    ),

    # Energy
    Industry(
        key="Oil & Energy",
        label_pt="Petróleo e Energia",
        label_en="Oil & Energy",
        category="energy",
        synonyms=["Petróleo", "Oil", "Gas", "Gás", "Energy", "Energia", "O&G"],
    ),
    Industry(
        key="Renewables & Environment",
        label_pt="Energia Renovável",
        label_en="Renewables & Environment",
        category="energy",
        synonyms=["Renovável", "Clean Energy", "Energia Limpa", "Solar", "Eólica", "Wind", "Sustainability", "ESG"],
    ),
    Industry(
        key="Utilities",
        label_pt="Utilidades",
        label_en="Utilities",
        category="energy",
        synonyms=["Energia Elétrica", "Electric", "Water", "Água", "Saneamento"],
    ),

    # Manufacturing
    Industry(
        key="Automotive",
        label_pt="Automotivo",
        label_en="Automotive",
        category="manufacturing",
        synonyms=["Automotivo", "Carros", "Cars", "Auto", "Veículos", "Vehicles"],
    ),
    Industry(
        key="Industrial Automation",
        label_pt="Automação Industrial",
        label_en="Industrial Automation",
        category="manufacturing",
        synonyms=["Automação", "Automation", "Indústria 4.0", "Industry 4.0", "Robotics", "Robótica"],
    ),
    Industry(
        key="Mechanical or Industrial Engineering",
        label_pt="Engenharia Industrial",
        label_en="Mechanical or Industrial Engineering",
        category="manufacturing",
        synonyms=["Engenharia", "Engineering", "Manufatura", "Manufacturing"],
    ),
    Industry(
        key="Construction",
        label_pt="Construção",
        label_en="Construction",
        category="manufacturing",
        synonyms=["Construção Civil", "Construtora", "Civil Construction", "Building"],
    ),

    # Real Estate
    Industry(
        key="Real Estate",
        label_pt="Imobiliário",
        label_en="Real Estate",
        category="real_estate",
        synonyms=["Imobiliário", "Imóveis", "Property", "Proptech", "Real Estate Tech"],
    ),
    Industry(
        key="Commercial Real Estate",
        label_pt="Imóveis Comerciais",
        label_en="Commercial Real Estate",
        category="real_estate",
        synonyms=["CRE", "Commercial Property", "Escritórios", "Office Space"],
    ),

    # Telecommunications
    Industry(
        key="Telecommunications",
        label_pt="Telecomunicações",
        label_en="Telecommunications",
        category="telecommunications",
        synonyms=["Telecom", "Telco", "Telefonia", "Mobile", "Móvel"],
    ),
    Industry(
        key="Wireless",
        label_pt="Wireless",
        label_en="Wireless",
        category="telecommunications",
        synonyms=["Wireless", "5G", "Connectivity", "Conectividade"],
    ),

    # Media & Entertainment
    Industry(
        key="Media Production",
        label_pt="Produção de Mídia",
        label_en="Media Production",
        category="media",
        synonyms=["Mídia", "Media", "Produção", "Production", "Content"],
    ),
    Industry(
        key="Entertainment",
        label_pt="Entretenimento",
        label_en="Entertainment",
        category="media",
        synonyms=["Entretenimento", "Shows", "Events", "Eventos"],
    ),
    Industry(
        key="Online Media",
        label_pt="Mídia Online",
        label_en="Online Media",
        category="media",
        synonyms=["Digital Media", "Streaming", "OTT", "Conteúdo Digital"],
    ),
    Industry(
        key="Publishing",
        label_pt="Editoras",
        label_en="Publishing",
        category="media",
        synonyms=["Editora", "Editorial", "Livros", "Books"],
    ),

    # Other
    Industry(
        key="Non-Profit Organization Management",
        label_pt="Organizações sem Fins Lucrativos",
        label_en="Non-Profit Organization Management",
        category="other",
        synonyms=["ONG", "NGO", "Non-Profit", "Terceiro Setor", "Social Impact", "Impacto Social"],
    ),
    Industry(
        key="Government Administration",
        label_pt="Administração Pública",
        label_en="Government Administration",
        category="other",
        synonyms=["Governo", "Government", "Public Sector", "Setor Público", "Govtech"],
    ),
    Industry(
        key="Hospitality",
        label_pt="Hotelaria",
        label_en="Hospitality",
        category="other",
        synonyms=["Hotel", "Hotelaria", "Turismo", "Tourism", "Travel"],
    ),
    Industry(
        key="Leisure/Travel/Tourism",
        label_pt="Turismo e Viagens",
        label_en="Leisure/Travel/Tourism",
        category="other",
        synonyms=["Viagens", "Travel", "Tourism", "Turismo", "OTA"],
    ),
    Industry(
        key="Restaurants",
        label_pt="Restaurantes",
        label_en="Restaurants",
        category="other",
        synonyms=["Restaurante", "Food Service", "Gastronomia", "Foodtech"],
    ),
    Industry(
        key="Agriculture",
        label_pt="Agronegócio",
        label_en="Agriculture",
        category="other",
        synonyms=["Agro", "Agronegócio", "Farming", "Agtech", "Agricultura"],
    ),
    Industry(
        key="Transportation",
        label_pt="Transporte",
        label_en="Transportation",
        category="other",
        synonyms=["Transporte", "Transport", "Mobilidade", "Mobility", "Ride-sharing"],
    ),
]


_synonym_map: dict[str, set[str]] = {}


def _build_synonym_map() -> None:
    """Build the synonym map for fast lookups."""
    global _synonym_map
    if _synonym_map:
        return
    
    for industry in INDUSTRIES:
        all_terms: set[str] = set()
        all_terms.add(industry.key.lower())
        all_terms.add(industry.label_pt.lower())
        all_terms.add(industry.label_en.lower())
        for syn in industry.synonyms:
            all_terms.add(syn.lower())
        
        for term in all_terms:
            if term not in _synonym_map:
                _synonym_map[term] = set()
            for other_term in all_terms:
                _synonym_map[term].add(other_term)


def normalize_industry(term: str) -> list[str]:
    """
    Returns all equivalent industry terms for the given term.
    This allows bidirectional matching - "Banking" returns ["banking", "banco", "banco digital", ...]
    
    Args:
        term: The industry term to normalize
        
    Returns:
        List of all equivalent terms (lowercase)
    """
    _build_synonym_map()
    normalized = term.lower().strip()
    equivalents = _synonym_map.get(normalized)
    if equivalents:
        return list(equivalents)
    return [normalized]


def get_canonical_key(term: str) -> str | None:
    """
    Get the canonical (English LinkedIn standard) key for a term.
    
    Args:
        term: Any industry term (English, Portuguese, or synonym)
        
    Returns:
        The canonical key or None if not found
    """
    term_lower = term.lower().strip()
    for industry in INDUSTRIES:
        if (
            industry.key.lower() == term_lower or
            industry.label_pt.lower() == term_lower or
            industry.label_en.lower() == term_lower or
            any(s.lower() == term_lower for s in industry.synonyms)
        ):
            return industry.key
    return None


def get_all_equivalent_terms(term: str) -> list[str]:
    """
    Get all equivalent terms including original casing from the industry definitions.
    
    Args:
        term: The industry term to look up
        
    Returns:
        List of all equivalent terms with original casing
    """
    _build_synonym_map()
    normalized = term.lower().strip()
    
    all_terms: list[str] = []
    for industry in INDUSTRIES:
        industry_terms_lower = {
            industry.key.lower(),
            industry.label_pt.lower(),
            industry.label_en.lower(),
            *[s.lower() for s in industry.synonyms]
        }
        if normalized in industry_terms_lower:
            all_terms.append(industry.key)
            all_terms.append(industry.label_pt)
            all_terms.append(industry.label_en)
            all_terms.extend(industry.synonyms)
    
    return list(set(all_terms)) if all_terms else [term]


def match_industry(search_term: str, industries: list[str]) -> bool:
    """
    Check if any industry in the list matches the search term (including synonyms).
    
    Args:
        search_term: The term to search for
        industries: List of industries to check against
        
    Returns:
        True if any industry matches the search term
    """
    search_equivalents = set(normalize_industry(search_term))
    return any(ind.lower() in search_equivalents for ind in industries)


def search_industries(query: str) -> list[Industry]:
    """
    Search for industries matching the query in any language.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching Industry objects
    """
    if not query.strip():
        return list(INDUSTRIES)
    
    query_lower = query.lower().strip()
    return [
        industry for industry in INDUSTRIES
        if (
            query_lower in industry.key.lower() or
            query_lower in industry.label_pt.lower() or
            query_lower in industry.label_en.lower() or
            any(query_lower in s.lower() for s in industry.synonyms)
        )
    ]


def expand_industries_for_search(industries: list[str]) -> list[str]:
    """
    Expand a list of industries to include all equivalent terms.
    This is useful for search queries where we want to match any synonym.
    
    Args:
        industries: List of industry terms
        
    Returns:
        Expanded list with all equivalent terms (lowercase, deduplicated)
    """
    expanded: set[str] = set()
    for industry in industries:
        equivalents = normalize_industry(industry)
        expanded.update(equivalents)
    return list(expanded)


def get_industry_by_key(key: str) -> Industry | None:
    """
    Get an Industry object by its key.
    
    Args:
        key: The industry key
        
    Returns:
        Industry object or None if not found
    """
    key_lower = key.lower()
    for industry in INDUSTRIES:
        if (
            industry.key.lower() == key_lower or
            industry.label_pt.lower() == key_lower or
            industry.label_en.lower() == key_lower
        ):
            return industry
    return None


def get_industries_by_category(category: str) -> list[Industry]:
    """
    Get all industries in a category.
    
    Args:
        category: The category key
        
    Returns:
        List of Industry objects in that category
    """
    return [i for i in INDUSTRIES if i.category == category]


def get_popular_industries() -> list[Industry]:
    """Get a curated list of popular industries."""
    popular_keys = [
        "Information Technology",
        "Computer Software",
        "Banking",
        "Financial Services",
        "Fintech",
        "E-commerce",
        "Management Consulting",
        "Hospital & Health Care",
        "Marketing and Advertising",
        "Venture Capital & Private Equity",
        "Education Management",
        "Human Resources",
        "Retail",
        "Startup",
        "Logistics and Supply Chain",
    ]
    return [i for i in INDUSTRIES if i.key in popular_keys]
