"""
Módulo de Dados: Perfis de Calibração para Inferência Contextual de Senioridade (WSI).

Este arquivo contém APENAS estruturas de dados (dicionários) utilizadas pelo sistema
de inferência contextual de senioridade do WSI (WeDoTalent Skill Index). Não contém
lógica de negócio.

Perfis inclusos:
- AREA_MATURITY_PROFILES: 13 perfis de área com configurações de senioridade
- DEFAULT_PROFILE: Perfil padrão para fallback
- GEOGRAPHIC_ADJUSTMENTS: Ajustes por localização geográfica
- TECHNOLOGY_AGE_PROFILES: Perfis de idade/maduridade tecnológica
- SALARY_REFERENCE_RANGES_BRL: Ranges de referência salarial (mercado BR)

Todos os dados são hardcoded e versionados no repositório, não são configuráveis
por clientes.

Última atualização: 2026-02-11
Versão: 1.0
"""

# ============================================================================
# 1. AREA_MATURITY_PROFILES
# ============================================================================
"""
Perfis de maturidade por área profissional.

Cada perfil contém:
- maturity: "emergent" | "growing" | "mature" | "traditional"
- keywords: Lista de palavras-chave para matching (português + inglês)
- seniority_years: Dicionário com (min_years, max_years) por nível WSI
- bloom_offset: Deslocamento a aplicar aos níveis base de Bloom
- dreyfus_offset: Deslocamento a aplicar aos níveis base de Dreyfus

Níveis WSI: "junior" | "pleno" | "senior" | "lead" | "executive"
"""

AREA_MATURITY_PROFILES = {
    # ========================================================================
    # ÁREA 1: IA GENERATIVA
    # ========================================================================
    # Maturity: EMERGENT
    # Justificativa: Tecnologia muito nova (mainstream desde 2022-2023).
    # Ofertas de mercado ainda em expansão. Profissionais em curva de
    # aprendizado acelerado. Calibração conservadora para não sobre-estimar.
    # ========================================================================
    "ai_generative": {
        "maturity": "emergent",
        "keywords": [
            # Português
            "ia generativa",
            "inteligência artificial generativa",
            "genai",
            "prompt engineering",
            "engenharia de prompts",
            "langchain",
            "llamaindex",
            "rag",
            "retrieval augmented generation",
            "vector database",
            "banco de dados vetorial",
            "gpt",
            "claude",
            "gemini",
            "stable diffusion",
            "difusão estável",
            "fine-tuning",
            "llm",
            "large language model",
            "modelo de linguagem grande",
            # Inglês
            "generative ai",
            "prompt engineering",
            "langchain",
            "llamaindex",
            "retrieval augmented generation",
            "vector database",
            "fine-tuning",
            "llm",
            "large language model",
        ],
        "seniority_years": {
            "junior": (0, 1),
            "pleno": (1, 2),
            "senior": (2, 4),
            "lead": (3, 5),
            "executive": (4, 7),
        },
        "bloom_offset": -1,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 2: CIÊNCIA DE DADOS
    # ========================================================================
    # Maturity: GROWING
    # Justificativa: Tecnologia com ~7-10 anos de maturidade. Mercado em
    # crescimento ativo. Profissionais com perfil misto (estatísticos +
    # engenheiros). Calibração moderada.
    # ========================================================================
    "data_science": {
        "maturity": "growing",
        "keywords": [
            # Português
            "ciência de dados",
            "data science",
            "machine learning",
            "aprendizado de máquina",
            "ml",
            "deep learning",
            "aprendizado profundo",
            "neural networks",
            "redes neurais",
            "nlp",
            "processamento de linguagem natural",
            "computer vision",
            "visão computacional",
            "data engineer",
            "engenheiro de dados",
            "analytics",
            "analítica",
            "big data",
            "spark",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            # Inglês
            "data science",
            "machine learning",
            "deep learning",
            "nlp",
            "computer vision",
            "data engineer",
            "analytics",
            "big data",
            "spark",
            "tensorflow",
            "pytorch",
            "scikit-learn",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 4),
            "senior": (3, 6),
            "lead": (5, 8),
            "executive": (7, 12),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 3: CLOUD & DEVOPS
    # ========================================================================
    # Maturity: GROWING
    # Justificativa: Consolidação de padrões cloud (AWS/Azure/GCP ~8-10 anos),
    # mas DevOps/SRE ainda em expansão. Mercado aquecido. Profissionais
    # especializados em demanda.
    # ========================================================================
    "cloud_devops": {
        "maturity": "growing",
        "keywords": [
            # Português
            "devops",
            "site reliability engineer",
            "sre",
            "cloud",
            "nuvem",
            "kubernetes",
            "k8s",
            "docker",
            "containerização",
            "terraform",
            "infraestrutura como código",
            "infrastructure as code",
            "iac",
            "aws",
            "amazon web services",
            "azure",
            "microsoft azure",
            "gcp",
            "google cloud",
            "google cloud platform",
            "ci/cd",
            "integração contínua",
            "deployment",
            "implantação",
            # Inglês
            "devops",
            "site reliability engineer",
            "sre",
            "cloud",
            "kubernetes",
            "docker",
            "terraform",
            "infrastructure as code",
            "aws",
            "azure",
            "gcp",
            "ci/cd",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 4),
            "senior": (4, 7),
            "lead": (6, 10),
            "executive": (8, 15),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 4: ENGENHARIA DE SOFTWARE
    # ========================================================================
    # Maturity: MATURE
    # Justificativa: Disciplina consolidada com 30+ anos. Padrões bem definidos.
    # Mercado estável. Profissionais em todos os níveis disponíveis.
    # Calibração padrão.
    # ========================================================================
    "software_engineering": {
        "maturity": "mature",
        "keywords": [
            # Português
            "desenvolvedor",
            "desenvolvedor de software",
            "desenvolvedor web",
            "desenvolvedor mobile",
            "dev",
            "engineer",
            "engenheiro de software",
            "engenheiro",
            "fullstack",
            "full-stack",
            "frontend",
            "frontend engineer",
            "engenheiro frontend",
            "backend",
            "backend engineer",
            "engenheiro backend",
            "java",
            "python",
            "javascript",
            "typescript",
            "react",
            "angular",
            "vue",
            "node",
            "nodejs",
            "express",
            "django",
            "fastapi",
            "spring",
            "go",
            "rust",
            "c#",
            "csharp",
            "dotnet",
            ".net",
            # Inglês
            "developer",
            "software engineer",
            "fullstack",
            "frontend",
            "backend",
            "java",
            "python",
            "javascript",
            "typescript",
            "react",
            "angular",
            "vue",
            "node",
            "go",
            "rust",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (5, 8),
            "lead": (7, 12),
            "executive": (10, 20),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 5: DESIGN (PRODUTO)
    # ========================================================================
    # Maturity: MATURE
    # Justificativa: UX/UI consolidados há 15+ anos. Disciplina reconhecida.
    # Profissionais especializados em mercado. Calibração padrão.
    # ========================================================================
    "product_design": {
        "maturity": "mature",
        "keywords": [
            # Português
            "ux",
            "user experience",
            "experiência do usuário",
            "ui",
            "user interface",
            "interface do usuário",
            "product design",
            "design de produto",
            "designer",
            "designer ux",
            "designer ui",
            "ux designer",
            "ui designer",
            "figma",
            "sketch",
            "user research",
            "pesquisa de usuário",
            "usabilidade",
            "prototipação",
            "wireframe",
            "mockup",
            "design system",
            # Inglês
            "ux",
            "user experience",
            "ui",
            "user interface",
            "product design",
            "designer",
            "figma",
            "user research",
            "usability",
            "prototype",
            "wireframe",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (4, 7),
            "lead": (6, 10),
            "executive": (8, 15),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 6: PRODUCT MANAGEMENT
    # ========================================================================
    # Maturity: MATURE
    # Justificativa: Disciplina consolidada há 10+ anos (surge ~2005). Padrões
    # e metodologias bem estabelecidas. Profissionais em demanda.
    # ========================================================================
    "product_management": {
        "maturity": "mature",
        "keywords": [
            # Português
            "product manager",
            "gerente de produto",
            "pm",
            "product owner",
            "po",
            "gestão de produto",
            "product management",
            "gerenciamento de produto",
            "roadmap",
            "backlog",
            "sprint",
            "agile",
            "ágil",
            "scrum",
            "kanban",
            "ota",
            "opm",
            "opportunity sizing",
            # Inglês
            "product manager",
            "product owner",
            "product management",
            "pm",
            "po",
            "roadmap",
            "backlog",
            "agile",
            "scrum",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (5, 8),
            "lead": (7, 12),
            "executive": (10, 18),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 7: FINANÇAS & CONTABILIDADE
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Profissão milenar. Regulamentação forte. Certificações
    # obrigatórias. Progressão lenta (acúmulo de experiência critical).
    # bloom_offset=+1 (requer mais cognição), dreyfus_offset=0
    # ========================================================================
    "finance_accounting": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "financeiro",
            "finance",
            "contabilidade",
            "contábil",
            "accounting",
            "controller",
            "fiscal",
            "diretor financeiro",
            "cfo",
            "chief financial officer",
            "tributário",
            "auditoria",
            "auditor",
            "tesouraria",
            "tesouro",
            "planejamento financeiro",
            "ifrs",
            "gaap",
            "sarbanes-oxley",
            "sox",
            # Inglês
            "finance",
            "accounting",
            "controller",
            "financial",
            "cfo",
            "chief financial officer",
            "audit",
            "auditor",
            "treasury",
            "ifrs",
            "gaap",
        ],
        "seniority_years": {
            "junior": (0, 3),
            "pleno": (3, 6),
            "senior": (6, 10),
            "lead": (8, 15),
            "executive": (12, 25),
        },
        "bloom_offset": 1,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 8: JURÍDICO & COMPLIANCE
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Profissão regulada (OAB no Brasil). Certificações
    # mandatórias. Progressão muito lenta. Requer expertise profunda e
    # contextual. bloom_offset=+1, dreyfus_offset=+1 (especialização crítica)
    # ========================================================================
    "legal": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "advogado",
            "avocado",
            "jurídico",
            "legal",
            "direito",
            "attorney",
            "lawyer",
            "compliance",
            "conformidade",
            "regulatório",
            "regulatory",
            "contencioso",
            "litigação",
            "litigation",
            "trabalhista",
            "labor law",
            "societário",
            "corporate law",
            "direito civil",
            "direito penal",
            "direito tributário",
            "tax law",
            # Inglês
            "legal",
            "lawyer",
            "attorney",
            "compliance",
            "regulatory",
            "litigation",
            "corporate",
        ],
        "seniority_years": {
            "junior": (0, 3),
            "pleno": (3, 7),
            "senior": (7, 12),
            "lead": (10, 18),
            "executive": (15, 30),
        },
        "bloom_offset": 1,
        "dreyfus_offset": 1,
    },

    # ========================================================================
    # ÁREA 9: ENGENHARIA CIVIL
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Profissão centenária. Regulação CREA/MEC. Acúmulo de
    # experiência crítico. Progressão lenta (acima de 10 anos). bloom_offset=+1,
    # dreyfus_offset=+1 (expertise contextual)
    # ========================================================================
    "engineering_civil": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "engenheiro civil",
            "civil engineer",
            "engenharia civil",
            "civil engineering",
            "construção",
            "construction",
            "obras",
            "obra",
            "estrutural",
            "structural",
            "geotécnico",
            "geotechnical",
            "fundações",
            "foundations",
            "project management",
            "gerenciamento de projetos",
            "orçamento",
            "budgeting",
            "planejamento",
            "planning",
            # Inglês
            "civil engineer",
            "civil engineering",
            "construction",
            "structural",
            "geotechnical",
            "project management",
        ],
        "seniority_years": {
            "junior": (0, 3),
            "pleno": (3, 7),
            "senior": (7, 12),
            "lead": (10, 18),
            "executive": (15, 25),
        },
        "bloom_offset": 1,
        "dreyfus_offset": 1,
    },

    # ========================================================================
    # ÁREA 10: MEDICINA & SAÚDE
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Profissão regulada (CRM/COREN). Formação longa (6+ anos).
    # Certificações mandatórias. Especialização crítica. Progressão acumulativa.
    # bloom_offset=+1, dreyfus_offset=+1 (expertise e certificação obrigatórias)
    # ========================================================================
    "medicine_health": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "médico",
            "physician",
            "doctor",
            "enfermeiro",
            "nurse",
            "saúde",
            "health",
            "healthcare",
            "assistência à saúde",
            "farmacêutico",
            "pharmacist",
            "biomédico",
            "biomedical",
            "fisioterapeuta",
            "physiotherapist",
            "hospitalar",
            "hospital",
            "clínico",
            "clinical",
            "cirurgião",
            "surgeon",
            "pediatra",
            "cardiologista",
            "psiquiatra",
            # Inglês
            "physician",
            "doctor",
            "nurse",
            "health",
            "healthcare",
            "pharmacist",
            "biomedical",
            "physiotherapist",
            "hospital",
            "clinical",
            "surgeon",
        ],
        "seniority_years": {
            "junior": (0, 3),
            "pleno": (3, 7),
            "senior": (8, 15),
            "lead": (12, 20),
            "executive": (15, 30),
        },
        "bloom_offset": 1,
        "dreyfus_offset": 1,
    },

    # ========================================================================
    # ÁREA 11: RECURSOS HUMANOS
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Disciplina consolidada há 50+ anos. Regulações trabalhistas
    # complexas. Profissionais em demanda. Progressão moderada a acumulativa.
    # bloom_offset=0, dreyfus_offset=0
    # ========================================================================
    "human_resources": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "rh",
            "hr",
            "human resources",
            "recursos humanos",
            "pessoas",
            "people",
            "talent",
            "talento",
            "recrutamento",
            "recruitment",
            "seleção",
            "selection",
            "onboarding",
            "development",
            "desenvolvimento",
            "training",
            "treinamento",
            "gente e gestão",
            "dp",
            "departamento pessoal",
            "folha",
            "payroll",
            "gestão de pessoas",
            "compensation",
            "benefits",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (5, 9),
            "lead": (7, 14),
            "executive": (10, 20),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 12: VENDAS & COMERCIAL
    # ========================================================================
    # Maturity: TRADITIONAL
    # Justificativa: Função perene em qualquer organização. Consolidada há
    # décadas. Progressão variável (baseada em resultados). Profissionais
    # em demanda. bloom_offset=0, dreyfus_offset=0
    # ========================================================================
    "sales_commercial": {
        "maturity": "traditional",
        "keywords": [
            # Português
            "vendas",
            "sales",
            "comercial",
            "commercial",
            "vendedor",
            "salesperson",
            "account",
            "account manager",
            "gerente de contas",
            "business development",
            "desenvolvimento de negócios",
            "bd",
            "bdr",
            "business development representative",
            "sdr",
            "sales development representative",
            "closer",
            "fechador",
            "key account",
            "conta-chave",
            "retail",
            "varejo",
            # Inglês
            "sales",
            "salesperson",
            "account",
            "account manager",
            "business development",
            "bdr",
            "sdr",
            "closer",
            "key account",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (5, 8),
            "lead": (7, 12),
            "executive": (10, 20),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },

    # ========================================================================
    # ÁREA 13: MARKETING
    # ========================================================================
    # Maturity: MATURE
    # Justificativa: Disciplina consolidada há 50+ anos. Digital marketing
    # evoluiu 15+ anos. Profissionais especializados em demanda. Progressão
    # acumulativa. bloom_offset=0, dreyfus_offset=0
    # ========================================================================
    "marketing": {
        "maturity": "mature",
        "keywords": [
            # Português
            "marketing",
            "growth",
            "growth marketing",
            "performance",
            "performance marketing",
            "branding",
            "marca",
            "conteúdo",
            "content",
            "content marketing",
            "inbound",
            "inbound marketing",
            "outbound",
            "outbound marketing",
            "crm",
            "customer relationship management",
            "automação",
            "marketing automation",
            "estratégia",
            "strategy",
            "analítica",
            "analytics",
            "seo",
            "sem",
            # Inglês
            "marketing",
            "growth",
            "performance",
            "branding",
            "content",
            "inbound",
            "outbound",
            "crm",
            "automation",
            "strategy",
            "analytics",
            "seo",
        ],
        "seniority_years": {
            "junior": (0, 2),
            "pleno": (2, 5),
            "senior": (4, 8),
            "lead": (6, 12),
            "executive": (10, 18),
        },
        "bloom_offset": 0,
        "dreyfus_offset": 0,
    },
}

# ============================================================================
# 2. DEFAULT_PROFILE
# ============================================================================
"""
Perfil padrão para fallback quando nenhuma área é identificada.

Utilizado como valor default quando:
- Nenhum keyword match é encontrado
- Perfil de área não está definido
- Candidato não tem informações de área/departamento

Equivalente ao mapeamento fixo original do WSI.
"""

DEFAULT_PROFILE = {
    "maturity": "mature",
    "keywords": [],
    "seniority_years": {
        "junior": (0, 2),
        "pleno": (2, 5),
        "senior": (5, 8),
        "lead": (7, 12),
        "executive": (10, 18),
    },
    "bloom_offset": 0,
    "dreyfus_offset": 0,
}

# ============================================================================
# 3. GEOGRAPHIC_ADJUSTMENTS (REMOVED — Bias Compliance B2)
# ============================================================================
# Geographic-based career progression multipliers were removed to prevent
# discrimination by country of origin (Lei 9.029/1995, CF Art. 5°).
# All candidates are now evaluated with a universal multiplier of 1.0
# regardless of geographic location.

GEOGRAPHIC_ADJUSTMENTS = {}

# ============================================================================
# 4. TECHNOLOGY_AGE_PROFILES
# ============================================================================
"""
Perfis de maturidade/idade tecnológica.

Diferentes tecnologias têm ciclos de vida distintos. Tecnologias mais novas
tendem a ter profissionais menos maduros (pois há menos tempo de experiência
acumulada disponível).

Ajustes:
- very_new: Restringe alcance máximo de senioridade (ninguém pode ter 20 anos
  de experiência em tecnologia de 2 anos). Reduz teto Bloom.
- new: Restrição moderada.
- established: Sem restrição.
- legacy: Sem restrição (acúmulo de décadas possível).

Aplicação: Limita bloom_level máximo e years máximo para dado nível de
senioridade, quando candidato usa tecnologia deste grupo.
"""

TECHNOLOGY_AGE_PROFILES = {
    "very_new": {
        "description": "< 3 anos em mainstream (ex: GPT-4, Claude 2023+)",
        "skills": [
            "langchain",
            "llamaindex",
            "openai api",
            "prompt engineering",
            "rag",
            "retrieval augmented generation",
            "vector database",
            "pinecone",
            "weaviate",
        ],
        "max_senior_years": 4,
        "bloom_ceiling": 5,
    },
    "new": {
        "description": "3-7 anos em mainstream (ex: Kubernetes 2016+, Next.js 2020+)",
        "skills": [
            "kubernetes",
            "k8s",
            "terraform",
            "next.js",
            "nextjs",
            "svelte",
            "deno",
            "flutter",
            "graphql",
            "rust",
            "tailwind",
            "tailwind css",
        ],
        "max_senior_years": 6,
        "bloom_ceiling": 6,
    },
    "established": {
        "description": "7-15 anos em mainstream (ex: React 2013+, Docker 2013+)",
        "skills": [
            "react",
            "angular",
            "vue",
            "docker",
            "typescript",
            "python",
            "apache spark",
            "spark",
            "kafka",
            "aws",
            "amazon web services",
            "azure",
            "microsoft azure",
        ],
        "max_senior_years": 10,
        "bloom_ceiling": 6,
    },
    "legacy": {
        "description": "15+ anos em mainstream (ex: Java 1995+, PHP 1995+, Oracle 1977+)",
        "skills": [
            "java",
            "c#",
            "csharp",
            ".net",
            "dotnet",
            "sql server",
            "sqlserver",
            "oracle",
            "cobol",
            "sap",
            "mainframe",
            "delphi",
            "php",
        ],
        "max_senior_years": 15,
        "bloom_ceiling": 6,
    },
}

# ============================================================================
# 5. SALARY_REFERENCE_RANGES_BRL
# ============================================================================
"""
Ranges de referência salarial no mercado brasileiro (BRL).

Utilizados para validação de sinais: se candidato declara senior e tem
experiência senior (5-8 anos), mas salário é junior, há inconsistência
(red flag).

Valores em BRL mensais (salário bruto), baseados em:
- Pesquisas de mercado 2024-2025
- Dados de plataformas como Glassdoor, Payscale, LinkedIn
- Ajustado por custo de vida SP/Rio

Aplicação: ValidationService usa para detectar inconsistências entre
senioridade inferida, experiência e salário declarado.

Obs: Ranges são aproximados. Variações regionais e por setor são esperadas.
"""

SALARY_REFERENCE_RANGES_BRL = {
    "junior": (3000, 8000),
    "pleno": (7000, 15000),
    "senior": (12000, 30000),
    "lead": (18000, 40000),
    "executive": (25000, 80000),
}
