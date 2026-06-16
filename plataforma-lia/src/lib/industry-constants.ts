export type IndustryCategory =
  | "technology"
  | "finance"
  | "consulting"
  | "ecommerce_retail"
  | "education"
  | "healthcare"
  | "marketing_agency"
  | "startup_ecosystem"
  | "legal"
  | "energy"
  | "manufacturing"
  | "real_estate"
  | "telecommunications"
  | "media"
  | "other"

export interface Industry {
  key: string
  labelPt: string
  labelEn: string
  category: IndustryCategory
  synonyms: string[]
}

export const INDUSTRY_CATEGORIES: Record<IndustryCategory, { labelPt: string; labelEn: string }> = {
  technology: { labelPt: "Tecnologia", labelEn: "Technology" },
  finance: { labelPt: "Finanças", labelEn: "Finance" },
  consulting: { labelPt: "Consultoria", labelEn: "Consulting" },
  ecommerce_retail: { labelPt: "E-commerce e Varejo", labelEn: "E-commerce & Retail" },
  education: { labelPt: "Educação", labelEn: "Education" },
  healthcare: { labelPt: "Saúde", labelEn: "Healthcare" },
  marketing_agency: { labelPt: "Marketing e Agências", labelEn: "Marketing & Agency" },
  startup_ecosystem: { labelPt: "Ecossistema Startup", labelEn: "Startup Ecosystem" },
  legal: { labelPt: "Jurídico", labelEn: "Legal" },
  energy: { labelPt: "Energia", labelEn: "Energy" },
  manufacturing: { labelPt: "Manufatura", labelEn: "Manufacturing" },
  real_estate: { labelPt: "Imobiliário", labelEn: "Real Estate" },
  telecommunications: { labelPt: "Telecomunicações", labelEn: "Telecommunications" },
  media: { labelPt: "Mídia", labelEn: "Media" },
  other: { labelPt: "Outros", labelEn: "Other" },
}

export const INDUSTRIES: Industry[] = [
  // Technology
  {
    key: "Information Technology",
    labelPt: "Tecnologia da Informação",
    labelEn: "Information Technology",
    category: "technology",
    synonyms: ["TI", "IT", "Tech", "Tecnologia", "Information Technology and Services"],
  },
  {
    key: "Computer Software",
    labelPt: "Software",
    labelEn: "Computer Software",
    category: "technology",
    synonyms: ["Software", "Desenvolvimento de Software", "Software Development", "SaaS"],
  },
  {
    key: "Internet",
    labelPt: "Internet",
    labelEn: "Internet",
    category: "technology",
    synonyms: ["Internet", "Web", "Online", "Digital"],
  },
  {
    key: "Computer & Network Security",
    labelPt: "Segurança da Informação",
    labelEn: "Computer & Network Security",
    category: "technology",
    synonyms: ["Cibersegurança", "Cybersecurity", "InfoSec", "Segurança Cibernética"],
  },
  {
    key: "Cloud Computing",
    labelPt: "Computação em Nuvem",
    labelEn: "Cloud Computing",
    category: "technology",
    synonyms: ["Cloud", "Nuvem", "AWS", "Azure", "GCP", "IaaS", "PaaS"],
  },
  {
    key: "Artificial Intelligence",
    labelPt: "Inteligência Artificial",
    labelEn: "Artificial Intelligence",
    category: "technology",
    synonyms: ["IA", "AI", "Machine Learning", "ML", "Deep Learning", "Aprendizado de Máquina"],
  },
  {
    key: "Computer Games",
    labelPt: "Jogos Digitais",
    labelEn: "Computer Games",
    category: "technology",
    synonyms: ["Games", "Jogos", "Gaming", "Video Games"],
  },
  {
    key: "Semiconductors",
    labelPt: "Semicondutores",
    labelEn: "Semiconductors",
    category: "technology",
    synonyms: ["Chips", "Hardware", "Microprocessadores"],
  },
  {
    key: "Data Analytics",
    labelPt: "Análise de Dados",
    labelEn: "Data Analytics",
    category: "technology",
    synonyms: ["Big Data", "Data Science", "Ciência de Dados", "Analytics", "BI", "Business Intelligence"],
  },

  // Finance
  {
    key: "Banking",
    labelPt: "Bancos",
    labelEn: "Banking",
    category: "finance",
    synonyms: ["Banco", "Bancos", "Banco Digital", "Digital Banking", "Neobank", "Neobanco"],
  },
  {
    key: "Financial Services",
    labelPt: "Serviços Financeiros",
    labelEn: "Financial Services",
    category: "finance",
    synonyms: ["Financeiro", "Finanças", "Finance", "Serviços Financeiros"],
  },
  {
    key: "Fintech",
    labelPt: "Fintech",
    labelEn: "Fintech",
    category: "finance",
    synonyms: ["Fintech", "Financial Technology", "Tecnologia Financeira"],
  },
  {
    key: "Investment Banking",
    labelPt: "Banco de Investimento",
    labelEn: "Investment Banking",
    category: "finance",
    synonyms: ["Investment Bank", "IB", "M&A", "Fusões e Aquisições"],
  },
  {
    key: "Investment Management",
    labelPt: "Gestão de Investimentos",
    labelEn: "Investment Management",
    category: "finance",
    synonyms: ["Asset Management", "Gestão de Ativos", "Investimentos", "Investments"],
  },
  {
    key: "Capital Markets",
    labelPt: "Mercado de Capitais",
    labelEn: "Capital Markets",
    category: "finance",
    synonyms: ["Mercado Financeiro", "Stock Market", "Bolsa de Valores"],
  },
  {
    key: "Insurance",
    labelPt: "Seguros",
    labelEn: "Insurance",
    category: "finance",
    synonyms: ["Seguro", "Insurtech", "Insurance Tech"],
  },
  {
    key: "Payments",
    labelPt: "Pagamentos",
    labelEn: "Payments",
    category: "finance",
    synonyms: ["Pagamentos", "Payment Processing", "Meios de Pagamento", "Payment Gateway"],
  },
  {
    key: "Cryptocurrency",
    labelPt: "Criptomoedas",
    labelEn: "Cryptocurrency",
    category: "finance",
    synonyms: ["Crypto", "Blockchain", "Web3", "DeFi", "Bitcoin", "Ethereum"],
  },

  // Consulting
  {
    key: "Management Consulting",
    labelPt: "Consultoria de Gestão",
    labelEn: "Management Consulting",
    category: "consulting",
    synonyms: ["Consultoria", "Consulting", "Strategy Consulting", "Consultoria Estratégica"],
  },
  {
    key: "Professional Training & Coaching",
    labelPt: "Treinamento e Coaching",
    labelEn: "Professional Training & Coaching",
    category: "consulting",
    synonyms: ["Coaching", "Treinamento", "Training", "Desenvolvimento Profissional"],
  },
  {
    key: "Human Resources",
    labelPt: "Recursos Humanos",
    labelEn: "Human Resources",
    category: "consulting",
    synonyms: ["RH", "HR", "People", "Gestão de Pessoas", "Talent Acquisition"],
  },
  {
    key: "Staffing and Recruiting",
    labelPt: "Recrutamento e Seleção",
    labelEn: "Staffing and Recruiting",
    category: "consulting",
    synonyms: ["Recrutamento", "Recruiting", "Headhunting", "R&S", "Talent Acquisition"],
  },
  {
    key: "Outsourcing/Offshoring",
    labelPt: "Terceirização",
    labelEn: "Outsourcing/Offshoring",
    category: "consulting",
    synonyms: ["Outsourcing", "BPO", "Body Shop"],
  },

  // E-commerce & Retail
  {
    key: "E-commerce",
    labelPt: "E-commerce",
    labelEn: "E-commerce",
    category: "ecommerce_retail",
    synonyms: ["Ecommerce", "Comércio Eletrônico", "Online Retail", "Loja Virtual", "Marketplace"],
  },
  {
    key: "Retail",
    labelPt: "Varejo",
    labelEn: "Retail",
    category: "ecommerce_retail",
    synonyms: ["Varejo", "Loja", "Comércio", "Commerce"],
  },
  {
    key: "Consumer Goods",
    labelPt: "Bens de Consumo",
    labelEn: "Consumer Goods",
    category: "ecommerce_retail",
    synonyms: ["FMCG", "CPG", "Fast Moving Consumer Goods", "Produtos de Consumo"],
  },
  {
    key: "Luxury Goods & Jewelry",
    labelPt: "Luxo e Joias",
    labelEn: "Luxury Goods & Jewelry",
    category: "ecommerce_retail",
    synonyms: ["Luxo", "Luxury", "Premium"],
  },
  {
    key: "Apparel & Fashion",
    labelPt: "Moda e Vestuário",
    labelEn: "Apparel & Fashion",
    category: "ecommerce_retail",
    synonyms: ["Moda", "Fashion", "Vestuário", "Roupas", "Apparel"],
  },
  {
    key: "Food & Beverages",
    labelPt: "Alimentos e Bebidas",
    labelEn: "Food & Beverages",
    category: "ecommerce_retail",
    synonyms: ["Alimentos", "Bebidas", "Food", "F&B", "CPG Food"],
  },
  {
    key: "Supermarkets",
    labelPt: "Supermercados",
    labelEn: "Supermarkets",
    category: "ecommerce_retail",
    synonyms: ["Supermercado", "Grocery", "Mercearia"],
  },
  {
    key: "Logistics and Supply Chain",
    labelPt: "Logística",
    labelEn: "Logistics and Supply Chain",
    category: "ecommerce_retail",
    synonyms: ["Logística", "Supply Chain", "Cadeia de Suprimentos", "Fulfillment", "Last Mile"],
  },

  // Education
  {
    key: "E-Learning",
    labelPt: "E-Learning",
    labelEn: "E-Learning",
    category: "education",
    synonyms: ["EdTech", "Edtech", "Education Technology", "EAD", "Ensino a Distância", "Online Learning"],
  },
  {
    key: "Higher Education",
    labelPt: "Ensino Superior",
    labelEn: "Higher Education",
    category: "education",
    synonyms: ["Universidade", "University", "Faculdade", "Academia"],
  },
  {
    key: "Education Management",
    labelPt: "Gestão Educacional",
    labelEn: "Education Management",
    category: "education",
    synonyms: ["Educação", "Education", "Ensino", "Escola"],
  },
  {
    key: "Primary/Secondary Education",
    labelPt: "Educação Básica",
    labelEn: "Primary/Secondary Education",
    category: "education",
    synonyms: ["Ensino Fundamental", "Ensino Médio", "K-12", "Escola"],
  },
  {
    key: "Research",
    labelPt: "Pesquisa",
    labelEn: "Research",
    category: "education",
    synonyms: ["Pesquisa", "R&D", "P&D", "Research & Development"],
  },

  // Healthcare
  {
    key: "Hospital & Health Care",
    labelPt: "Hospitais e Saúde",
    labelEn: "Hospital & Health Care",
    category: "healthcare",
    synonyms: ["Hospital", "Saúde", "Healthcare", "Health", "Clínica", "Clinic"],
  },
  {
    key: "Health Tech",
    labelPt: "Healthtech",
    labelEn: "Health Tech",
    category: "healthcare",
    synonyms: ["Healthtech", "Health Technology", "Digital Health", "Saúde Digital", "Telemedicina", "Telemedicine"],
  },
  {
    key: "Pharmaceuticals",
    labelPt: "Farmacêutico",
    labelEn: "Pharmaceuticals",
    category: "healthcare",
    synonyms: ["Pharma", "Farmácia", "Medicamentos", "Drugs"],
  },
  {
    key: "Medical Devices",
    labelPt: "Dispositivos Médicos",
    labelEn: "Medical Devices",
    category: "healthcare",
    synonyms: ["Medical Equipment", "Equipamentos Médicos", "MedTech"],
  },
  {
    key: "Biotechnology",
    labelPt: "Biotecnologia",
    labelEn: "Biotechnology",
    category: "healthcare",
    synonyms: ["Biotech", "Life Sciences", "Ciências da Vida"],
  },
  {
    key: "Mental Health Care",
    labelPt: "Saúde Mental",
    labelEn: "Mental Health Care",
    category: "healthcare",
    synonyms: ["Saúde Mental", "Psicologia", "Psychology", "Therapy", "Terapia"],
  },
  {
    key: "Health/Wellness/Fitness",
    labelPt: "Bem-estar e Fitness",
    labelEn: "Health/Wellness/Fitness",
    category: "healthcare",
    synonyms: ["Wellness", "Fitness", "Bem-estar", "Academia", "Gym"],
  },

  // Marketing & Agency
  {
    key: "Marketing and Advertising",
    labelPt: "Marketing e Publicidade",
    labelEn: "Marketing and Advertising",
    category: "marketing_agency",
    synonyms: ["Marketing", "Publicidade", "Advertising", "Ads", "Propaganda"],
  },
  {
    key: "Digital Marketing",
    labelPt: "Marketing Digital",
    labelEn: "Digital Marketing",
    category: "marketing_agency",
    synonyms: ["Marketing Digital", "Performance Marketing", "Growth", "Growth Marketing"],
  },
  {
    key: "Agência Digital",
    labelPt: "Agência Digital",
    labelEn: "Digital Agency",
    category: "marketing_agency",
    synonyms: ["Digital Agency", "Agência", "Agency", "Creative Agency", "Agência Criativa"],
  },
  {
    key: "Public Relations",
    labelPt: "Relações Públicas",
    labelEn: "Public Relations",
    category: "marketing_agency",
    synonyms: ["PR", "RP", "Comunicação", "Communications"],
  },
  {
    key: "Design",
    labelPt: "Design",
    labelEn: "Design",
    category: "marketing_agency",
    synonyms: ["Design", "UX", "UI", "Product Design", "Graphic Design", "Design Gráfico"],
  },
  {
    key: "Market Research",
    labelPt: "Pesquisa de Mercado",
    labelEn: "Market Research",
    category: "marketing_agency",
    synonyms: ["Pesquisa", "Research", "Consumer Insights", "Analytics"],
  },

  // Startup Ecosystem
  {
    key: "Venture Capital & Private Equity",
    labelPt: "Venture Capital e Private Equity",
    labelEn: "Venture Capital & Private Equity",
    category: "startup_ecosystem",
    synonyms: ["VC", "PE", "Venture Capital", "Private Equity", "Capital de Risco", "Investidor"],
  },
  {
    key: "Startup",
    labelPt: "Startup",
    labelEn: "Startup",
    category: "startup_ecosystem",
    synonyms: ["Startup", "Start-up", "Startups", "Scaleup", "Scale-up"],
  },
  {
    key: "Accelerator",
    labelPt: "Aceleradora",
    labelEn: "Accelerator",
    category: "startup_ecosystem",
    synonyms: ["Aceleradora", "Incubadora", "Incubator", "Accelerator Program"],
  },

  // Legal
  {
    key: "Law Practice",
    labelPt: "Advocacia",
    labelEn: "Law Practice",
    category: "legal",
    synonyms: ["Advocacia", "Law Firm", "Escritório de Advocacia", "Jurídico", "Legal"],
  },
  {
    key: "Legal Services",
    labelPt: "Serviços Jurídicos",
    labelEn: "Legal Services",
    category: "legal",
    synonyms: ["Legal", "Jurídico", "Law", "Direito"],
  },
  {
    key: "Legal Tech",
    labelPt: "Legaltech",
    labelEn: "Legal Tech",
    category: "legal",
    synonyms: ["Legaltech", "Lawtech", "Legal Technology"],
  },

  // Energy
  {
    key: "Oil & Energy",
    labelPt: "Petróleo e Energia",
    labelEn: "Oil & Energy",
    category: "energy",
    synonyms: ["Petróleo", "Oil", "Gas", "Gás", "Energy", "Energia", "O&G"],
  },
  {
    key: "Renewables & Environment",
    labelPt: "Energia Renovável",
    labelEn: "Renewables & Environment",
    category: "energy",
    synonyms: ["Renovável", "Clean Energy", "Energia Limpa", "Solar", "Eólica", "Wind", "Sustainability", "ESG"],
  },
  {
    key: "Utilities",
    labelPt: "Utilidades",
    labelEn: "Utilities",
    category: "energy",
    synonyms: ["Energia Elétrica", "Electric", "Water", "Água", "Saneamento"],
  },

  // Manufacturing
  {
    key: "Automotive",
    labelPt: "Automotivo",
    labelEn: "Automotive",
    category: "manufacturing",
    synonyms: ["Automotivo", "Carros", "Cars", "Auto", "Veículos", "Vehicles"],
  },
  {
    key: "Industrial Automation",
    labelPt: "Automação Industrial",
    labelEn: "Industrial Automation",
    category: "manufacturing",
    synonyms: ["Automação", "Automation", "Indústria 4.0", "Industry 4.0", "Robotics", "Robótica"],
  },
  {
    key: "Mechanical or Industrial Engineering",
    labelPt: "Engenharia Industrial",
    labelEn: "Mechanical or Industrial Engineering",
    category: "manufacturing",
    synonyms: ["Engenharia", "Engineering", "Manufatura", "Manufacturing"],
  },
  {
    key: "Construction",
    labelPt: "Construção",
    labelEn: "Construction",
    category: "manufacturing",
    synonyms: ["Construção Civil", "Construtora", "Civil Construction", "Building"],
  },

  // Real Estate
  {
    key: "Real Estate",
    labelPt: "Imobiliário",
    labelEn: "Real Estate",
    category: "real_estate",
    synonyms: ["Imobiliário", "Imóveis", "Property", "Proptech", "Real Estate Tech"],
  },
  {
    key: "Commercial Real Estate",
    labelPt: "Imóveis Comerciais",
    labelEn: "Commercial Real Estate",
    category: "real_estate",
    synonyms: ["CRE", "Commercial Property", "Escritórios", "Office Space"],
  },

  // Telecommunications
  {
    key: "Telecommunications",
    labelPt: "Telecomunicações",
    labelEn: "Telecommunications",
    category: "telecommunications",
    synonyms: ["Telecom", "Telco", "Telefonia", "Mobile", "Móvel"],
  },
  {
    key: "Wireless",
    labelPt: "Wireless",
    labelEn: "Wireless",
    category: "telecommunications",
    synonyms: ["Wireless", "5G", "Connectivity", "Conectividade"],
  },

  // Media & Entertainment
  {
    key: "Media Production",
    labelPt: "Produção de Mídia",
    labelEn: "Media Production",
    category: "media",
    synonyms: ["Mídia", "Media", "Produção", "Production", "Content"],
  },
  {
    key: "Entertainment",
    labelPt: "Entretenimento",
    labelEn: "Entertainment",
    category: "media",
    synonyms: ["Entretenimento", "Shows", "Events", "Eventos"],
  },
  {
    key: "Online Media",
    labelPt: "Mídia Online",
    labelEn: "Online Media",
    category: "media",
    synonyms: ["Digital Media", "Streaming", "OTT", "Conteúdo Digital"],
  },
  {
    key: "Publishing",
    labelPt: "Editoras",
    labelEn: "Publishing",
    category: "media",
    synonyms: ["Editora", "Editorial", "Livros", "Books"],
  },

  // Other
  {
    key: "Non-Profit Organization Management",
    labelPt: "Organizações sem Fins Lucrativos",
    labelEn: "Non-Profit Organization Management",
    category: "other",
    synonyms: ["ONG", "NGO", "Non-Profit", "Terceiro Setor", "Social Impact", "Impacto Social"],
  },
  {
    key: "Government Administration",
    labelPt: "Administração Pública",
    labelEn: "Government Administration",
    category: "other",
    synonyms: ["Governo", "Government", "Public Sector", "Setor Público", "Govtech"],
  },
  {
    key: "Hospitality",
    labelPt: "Hotelaria",
    labelEn: "Hospitality",
    category: "other",
    synonyms: ["Hotel", "Hotelaria", "Turismo", "Tourism", "Travel"],
  },
  {
    key: "Leisure/Travel/Tourism",
    labelPt: "Turismo e Viagens",
    labelEn: "Leisure/Travel/Tourism",
    category: "other",
    synonyms: ["Viagens", "Travel", "Tourism", "Turismo", "OTA"],
  },
  {
    key: "Restaurants",
    labelPt: "Restaurantes",
    labelEn: "Restaurants",
    category: "other",
    synonyms: ["Restaurante", "Food Service", "Gastronomia", "Foodtech"],
  },
  {
    key: "Agriculture",
    labelPt: "Agronegócio",
    labelEn: "Agriculture",
    category: "other",
    synonyms: ["Agro", "Agronegócio", "Farming", "Agtech", "Agricultura"],
  },
  {
    key: "Transportation",
    labelPt: "Transporte",
    labelEn: "Transportation",
    category: "other",
    synonyms: ["Transporte", "Transport", "Mobilidade", "Mobility", "Ride-sharing"],
  },
]

const synonymMap: Map<string, Set<string>> = new Map()

function buildSynonymMap(): void {
  if (synonymMap.size > 0) return

  for (const industry of INDUSTRIES) {
    const allTerms = new Set<string>()
    allTerms.add(industry.key.toLowerCase())
    allTerms.add(industry.labelPt.toLowerCase())
    allTerms.add(industry.labelEn.toLowerCase())
    for (const syn of industry.synonyms) {
      allTerms.add(syn.toLowerCase())
    }

    for (const term of allTerms) {
      if (!synonymMap.has(term)) {
        synonymMap.set(term, new Set())
      }
      for (const otherTerm of allTerms) {
        synonymMap.get(term)!.add(otherTerm)
      }
    }
  }
}

export function normalizeIndustry(term: string): string[] {
  buildSynonymMap()
  const normalized = term.toLowerCase().trim()
  const equivalents = synonymMap.get(normalized)
  if (equivalents) {
    return Array.from(equivalents)
  }
  return [normalized]
}

export function getIndustryByKey(key: string): Industry | undefined {
  return INDUSTRIES.find(
    (i) =>
      i.key.toLowerCase() === key.toLowerCase() ||
      i.labelPt.toLowerCase() === key.toLowerCase() ||
      i.labelEn.toLowerCase() === key.toLowerCase()
  )
}

export function getCanonicalKey(term: string): string | null {
  const termLower = term.toLowerCase().trim()
  for (const industry of INDUSTRIES) {
    if (
      industry.key.toLowerCase() === termLower ||
      industry.labelPt.toLowerCase() === termLower ||
      industry.labelEn.toLowerCase() === termLower ||
      industry.synonyms.some((s) => s.toLowerCase() === termLower)
    ) {
      return industry.key
    }
  }
  return null
}

export function getAllEquivalentTerms(term: string): string[] {
  buildSynonymMap()
  const normalized = term.toLowerCase().trim()
  const equivalents = synonymMap.get(normalized)
  if (!equivalents) {
    return [term]
  }
  const allTerms: string[] = []
  for (const industry of INDUSTRIES) {
    const industryTermsLower = new Set([
      industry.key.toLowerCase(),
      industry.labelPt.toLowerCase(),
      industry.labelEn.toLowerCase(),
      ...industry.synonyms.map((s) => s.toLowerCase()),
    ])
    if (industryTermsLower.has(normalized)) {
      allTerms.push(industry.key)
      allTerms.push(industry.labelPt)
      allTerms.push(industry.labelEn)
      allTerms.push(...industry.synonyms)
    }
  }
  return [...new Set(allTerms)]
}

export function matchIndustry(searchTerm: string, industries: string[]): boolean {
  const searchEquivalents = normalizeIndustry(searchTerm)
  return industries.some((ind) => {
    const indLower = ind.toLowerCase()
    return searchEquivalents.includes(indLower)
  })
}

export function searchIndustries(query: string): Industry[] {
  if (!query.trim()) {
    return INDUSTRIES
  }
  const queryLower = query.toLowerCase().trim()
  return INDUSTRIES.filter((industry) => {
    return (
      industry.key.toLowerCase().includes(queryLower) ||
      industry.labelPt.toLowerCase().includes(queryLower) ||
      industry.labelEn.toLowerCase().includes(queryLower) ||
      industry.synonyms.some((s) => s.toLowerCase().includes(queryLower))
    )
  })
}

export function getIndustriesByCategory(category: IndustryCategory): Industry[] {
  return INDUSTRIES.filter((i) => i.category === category)
}

export function getPopularIndustries(): Industry[] {
  const popularKeys = [
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
  return INDUSTRIES.filter((i) => popularKeys.includes(i.key))
}

export const POPULAR_INDUSTRIES_LIST = INDUSTRIES.map((i) => i.key)
