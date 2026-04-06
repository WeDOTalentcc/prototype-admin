"""
Biblioteca de Taxonomia para Recrutamento - LIA Platform
Baseada em CBO (Classificação Brasileira de Ocupações), ESCO e padrões de mercado.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum


class TaxonomyCategory(StrEnum):
    JOB_TITLE = "job_title"
    SKILL_TECHNICAL = "skill_technical"
    SKILL_SOFT = "skill_soft"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    INDUSTRY = "industry"
    SENIORITY = "seniority"
    WORK_MODEL = "work_model"


@dataclass
class TaxonomyEntry:
    canonical: str
    synonyms: list[str]
    category: TaxonomyCategory
    subcategory: str = ""
    cbo_code: str = ""


JOB_TITLES_TAXONOMY: dict[str, list[str]] = {
    "tecnologia": [
        "Desenvolvedor", "Developer", "Programador", "Software Engineer", "Engenheiro de Software",
        "Desenvolvedor Backend", "Backend Developer", "Desenvolvedor Back-end",
        "Desenvolvedor Frontend", "Frontend Developer", "Desenvolvedor Front-end",
        "Desenvolvedor Full Stack", "Full Stack Developer", "Desenvolvedor Fullstack",
        "Desenvolvedor Web", "Web Developer",
        "Desenvolvedor Mobile", "Mobile Developer", "Desenvolvedor de Apps",
        "iOS Developer", "Desenvolvedor iOS", "Swift Developer",
        "Android Developer", "Desenvolvedor Android", "Kotlin Developer",
        "React Developer", "Desenvolvedor React", "React Native Developer",
        "Vue Developer", "Desenvolvedor Vue", "Vue.js Developer",
        "Angular Developer", "Desenvolvedor Angular",
        "Node.js Developer", "Desenvolvedor Node", "Node Developer",
        "Python Developer", "Desenvolvedor Python",
        "Java Developer", "Desenvolvedor Java",
        "C# Developer", "Desenvolvedor C#", ".NET Developer", "Desenvolvedor .NET",
        "Go Developer", "Desenvolvedor Go", "Golang Developer",
        "Rust Developer", "Desenvolvedor Rust",
        "PHP Developer", "Desenvolvedor PHP", "Laravel Developer",
        "Ruby Developer", "Desenvolvedor Ruby", "Rails Developer",
    ],
    "dados_ia": [
        "Data Scientist", "Cientista de Dados",
        "Data Analyst", "Analista de Dados",
        "Data Engineer", "Engenheiro de Dados",
        "Machine Learning Engineer", "ML Engineer", "Engenheiro de ML",
        "AI Engineer", "Engenheiro de IA", "Inteligência Artificial",
        "Deep Learning Engineer", "Engenheiro de Deep Learning",
        "NLP Engineer", "Engenheiro de NLP",
        "Computer Vision Engineer", "Engenheiro de Visão Computacional",
        "MLOps Engineer", "Engenheiro MLOps",
        "BI Analyst", "Analista de BI", "Business Intelligence Analyst",
        "Analytics Engineer", "Engenheiro de Analytics",
        "Data Architect", "Arquiteto de Dados",
    ],
    "infraestrutura": [
        "DevOps Engineer", "Engenheiro DevOps",
        "SRE", "Site Reliability Engineer", "Engenheiro de Confiabilidade",
        "Platform Engineer", "Engenheiro de Plataforma",
        "Cloud Engineer", "Engenheiro de Cloud", "Engenheiro de Nuvem",
        "AWS Engineer", "Azure Engineer", "GCP Engineer",
        "Infrastructure Engineer", "Engenheiro de Infraestrutura",
        "Kubernetes Engineer", "K8s Engineer",
        "System Administrator", "Administrador de Sistemas", "SysAdmin",
        "Network Engineer", "Engenheiro de Redes", "Administrador de Redes",
        "Database Administrator", "DBA", "Administrador de Banco de Dados",
    ],
    "seguranca": [
        "Security Engineer", "Engenheiro de Segurança",
        "Cybersecurity Analyst", "Analista de Cibersegurança",
        "AppSec Engineer", "Application Security Engineer",
        "Penetration Tester", "Pentester", "Ethical Hacker",
        "Security Analyst", "Analista de Segurança da Informação",
        "SOC Analyst", "Analista SOC",
        "CISO", "Chief Information Security Officer",
        "Security Architect", "Arquiteto de Segurança",
    ],
    "gestao_ti": [
        "Tech Lead", "Líder Técnico", "Lead Developer", "Technical Lead",
        "Engineering Manager", "Gerente de Engenharia",
        "CTO", "Chief Technology Officer", "Diretor de Tecnologia",
        "VP of Engineering", "VP Engineering",
        "Head of Engineering", "Head de Engenharia",
        "Software Architect", "Arquiteto de Software",
        "Solutions Architect", "Arquiteto de Soluções",
        "Cloud Architect", "Arquiteto de Cloud",
        "Enterprise Architect", "Arquiteto Corporativo",
    ],
    "produto_design": [
        "Product Manager", "PM", "Gerente de Produto",
        "Product Owner", "PO",
        "Product Designer", "Designer de Produto",
        "UX Designer", "User Experience Designer",
        "UI Designer", "User Interface Designer",
        "UX/UI Designer", "Designer UX/UI",
        "UX Researcher", "Pesquisador de UX",
        "Design Lead", "Líder de Design",
        "Head of Design", "Head de Design",
        "Interaction Designer", "Designer de Interação",
        "Visual Designer", "Designer Visual",
        "Motion Designer", "Designer de Motion",
    ],
    "qualidade": [
        "QA Engineer", "Quality Assurance Engineer", "Engenheiro de QA",
        "QA Analyst", "Analista de QA", "Analista de Qualidade",
        "Test Engineer", "Engenheiro de Testes",
        "SDET", "Software Development Engineer in Test",
        "Automation Engineer", "Engenheiro de Automação de Testes",
        "QA Lead", "Líder de QA",
        "Test Analyst", "Analista de Testes",
        "Performance Engineer", "Engenheiro de Performance",
    ],
    "agile": [
        "Scrum Master",
        "Agile Coach", "Coach Ágil",
        "Agilista",
        "Agile Project Manager", "Gerente de Projetos Ágil",
        "Release Manager",
        "Delivery Manager", "Gerente de Delivery",
    ],
    "sap_erp": [
        "Desenvolvedor SAP", "SAP Developer",
        "Desenvolvedor ABAP", "ABAP Developer", "SAP ABAP Developer",
        "Consultor SAP", "SAP Consultant",
        "Consultor SAP MM", "SAP MM Consultant",
        "Consultor SAP SD", "SAP SD Consultant",
        "Consultor SAP FI", "SAP FI Consultant",
        "Consultor SAP CO", "SAP CO Consultant",
        "Consultor SAP FI/CO", "SAP FICO Consultant",
        "Consultor SAP PP", "SAP PP Consultant",
        "Consultor SAP HR", "SAP HR Consultant", "SAP HCM Consultant",
        "Consultor SAP BW", "SAP BW Consultant",
        "SAP Basis", "SAP Basis Administrator",
        "SAP HANA Developer", "Desenvolvedor SAP HANA",
        "Analista SAP", "SAP Analyst",
        "Analista Funcional SAP", "SAP Functional Analyst",
        "Desenvolvedor TOTVS", "TOTVS Developer",
        "Consultor TOTVS", "TOTVS Consultant",
        "Consultor Protheus", "Protheus Developer",
        "Consultor ERP", "ERP Consultant",
        "Oracle ERP Consultant", "Consultor Oracle ERP",
        "Salesforce Developer", "Desenvolvedor Salesforce",
        "Salesforce Administrator", "Administrador Salesforce",
        "Salesforce Consultant", "Consultor Salesforce",
    ],
    "suporte": [
        "Analista de Suporte", "Support Analyst",
        "Analista de Suporte Técnico", "Technical Support Analyst",
        "Analista de Help Desk", "Help Desk Analyst",
        "Analista de Service Desk", "Service Desk Analyst",
        "IT Support Specialist", "Especialista de Suporte TI",
        "Support Engineer", "Engenheiro de Suporte",
        "Customer Success Engineer", "Engenheiro de Customer Success",
    ],
    "negocios": [
        "Business Analyst", "Analista de Negócios",
        "Analista de Processos", "Process Analyst",
        "Analista de Requisitos", "Requirements Analyst",
        "Consultor de Negócios", "Business Consultant",
        "Analista de Sistemas", "Systems Analyst",
        "Consultor de TI", "IT Consultant",
    ],
    "marketing_vendas": [
        "Growth Hacker", "Growth Marketing",
        "Marketing Manager", "Gerente de Marketing",
        "Digital Marketing Manager", "Gerente de Marketing Digital",
        "Performance Marketing", "Marketing de Performance",
        "SEO Specialist", "Especialista SEO",
        "SEM Specialist", "Especialista SEM",
        "Content Marketing", "Marketing de Conteúdo",
        "Social Media Manager", "Gerente de Redes Sociais",
        "Sales Development Representative", "SDR",
        "Account Executive", "Executivo de Contas",
        "Customer Success Manager", "CSM", "Gerente de Customer Success",
        "Pre-Sales Engineer", "Engenheiro de Pré-Vendas",
        "Sales Engineer", "Engenheiro de Vendas",
    ],
    "rh_administrativo": [
        "Analista de RH", "HR Analyst", "Analista de Recursos Humanos",
        "Business Partner", "HR Business Partner", "HRBP",
        "Recrutador", "Recruiter", "Tech Recruiter",
        "Talent Acquisition", "Aquisição de Talentos",
        "Analista de DHO", "Analista de Desenvolvimento Humano",
        "Analista de T&D", "Training Analyst",
        "Analista Financeiro", "Financial Analyst",
        "Analista Contábil", "Accountant",
        "Controller",
        "Analista Administrativo", "Administrative Analyst",
    ],
    "executivo": [
        "CEO", "Chief Executive Officer", "Diretor Executivo",
        "COO", "Chief Operating Officer", "Diretor de Operações",
        "CFO", "Chief Financial Officer", "Diretor Financeiro",
        "CMO", "Chief Marketing Officer", "Diretor de Marketing",
        "CPO", "Chief Product Officer", "Diretor de Produto",
        "CHRO", "Chief Human Resources Officer", "Diretor de RH",
        "VP", "Vice President", "Vice-Presidente",
        "Diretor", "Director",
        "Gerente", "Manager",
        "Coordenador", "Coordinator",
        "Supervisor", "Supervisor",
    ],
}

TECHNICAL_SKILLS_TAXONOMY: dict[str, list[str]] = {
    "linguagens_programacao": [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
        "Go", "Golang", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala",
        "R", "MATLAB", "Julia", "Perl", "Lua", "Elixir", "Erlang",
        "Objective-C", "Dart", "Groovy", "Clojure", "F#", "Haskell",
        "ABAP", "Cobol", "Fortran", "Assembly", "VBA", "VB.NET",
        "Shell Script", "Bash", "PowerShell", "SQL", "PL/SQL", "T-SQL",
    ],
    "frontend": [
        "React", "React.js", "ReactJS",
        "Vue", "Vue.js", "VueJS", "Vue 3",
        "Angular", "AngularJS", "Angular 2+",
        "Next.js", "NextJS", "Nuxt.js", "NuxtJS",
        "Svelte", "SvelteKit",
        "HTML", "HTML5", "CSS", "CSS3",
        "Tailwind", "Tailwind CSS", "TailwindCSS",
        "Bootstrap", "Material UI", "MUI", "Chakra UI",
        "SASS", "SCSS", "Less", "Styled Components",
        "Redux", "MobX", "Zustand", "Recoil",
        "Webpack", "Vite", "Rollup", "Parcel", "esbuild",
        "Jest", "Testing Library", "Cypress", "Playwright",
        "Storybook", "Figma", "Sketch", "Adobe XD",
    ],
    "backend": [
        "Node.js", "NodeJS", "Express", "Express.js", "Fastify", "NestJS",
        "Django", "Flask", "FastAPI", "Pyramid",
        "Spring", "Spring Boot", "Spring MVC",
        ".NET", ".NET Core", "ASP.NET", "Entity Framework",
        "Ruby on Rails", "Rails", "Sinatra",
        "Laravel", "Symfony", "CodeIgniter",
        "Go", "Gin", "Echo", "Fiber",
        "Rust", "Actix", "Rocket",
        "GraphQL", "Apollo", "REST", "RESTful", "gRPC", "WebSocket",
        "Microservices", "Microsserviços", "API Gateway",
        "RabbitMQ", "Kafka", "Redis", "Celery",
    ],
    "mobile": [
        "React Native",
        "Flutter", "Dart",
        "Swift", "SwiftUI", "UIKit",
        "Kotlin", "Android", "Android SDK",
        "iOS", "Xcode",
        "Ionic", "Cordova", "Capacitor",
        "Xamarin", "MAUI",
        "PWA", "Progressive Web Apps",
    ],
    "banco_dados": [
        "PostgreSQL", "Postgres",
        "MySQL", "MariaDB",
        "SQL Server", "MSSQL",
        "Oracle", "Oracle Database", "PL/SQL",
        "MongoDB", "NoSQL",
        "Redis", "Memcached",
        "Elasticsearch", "OpenSearch",
        "Cassandra", "DynamoDB",
        "Neo4j", "Graph Database",
        "SQLite", "H2",
        "Firebase", "Firestore",
        "Supabase",
        "Prisma", "Sequelize", "TypeORM", "SQLAlchemy",
    ],
    "cloud_devops": [
        "AWS", "Amazon Web Services",
        "Azure", "Microsoft Azure",
        "GCP", "Google Cloud Platform", "Google Cloud",
        "Docker", "Containers", "Containerização",
        "Kubernetes", "K8s", "EKS", "AKS", "GKE",
        "Terraform", "IaC", "Infrastructure as Code",
        "Ansible", "Puppet", "Chef",
        "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI",
        "CI/CD", "Continuous Integration", "Continuous Deployment",
        "Helm", "ArgoCD", "Flux",
        "Prometheus", "Grafana", "Datadog", "New Relic",
        "ELK Stack", "Logstash", "Kibana",
        "Linux", "Ubuntu", "CentOS", "Debian", "RHEL",
        "Nginx", "Apache", "HAProxy",
        "Serverless", "Lambda", "Cloud Functions",
    ],
    "dados_ml": [
        "Pandas", "NumPy", "SciPy",
        "Scikit-learn", "sklearn",
        "TensorFlow", "Keras",
        "PyTorch",
        "Hugging Face", "Transformers",
        "OpenAI", "GPT", "LLM", "Large Language Models",
        "LangChain", "LlamaIndex",
        "Spark", "PySpark", "Apache Spark",
        "Hadoop", "Hive", "Presto",
        "Airflow", "Apache Airflow", "Prefect", "Dagster",
        "dbt", "Data Build Tool",
        "Snowflake", "BigQuery", "Redshift", "Databricks",
        "MLflow", "Kubeflow", "SageMaker",
        "Power BI", "Tableau", "Looker", "Metabase",
        "Excel", "Google Sheets",
    ],
    "sap_erp": [
        "SAP", "SAP ERP", "SAP ECC",
        "SAP ABAP", "ABAP", "ABAP OO",
        "SAP S/4HANA", "S4HANA", "SAP HANA",
        "SAP Fiori", "SAP UI5",
        "SAP MM", "Materials Management",
        "SAP SD", "Sales and Distribution",
        "SAP FI", "Financial Accounting",
        "SAP CO", "Controlling",
        "SAP FICO", "SAP FI/CO",
        "SAP PP", "Production Planning",
        "SAP HR", "SAP HCM", "Human Capital Management",
        "SAP BW", "Business Warehouse",
        "SAP Basis",
        "SAP PI", "SAP PO", "Process Integration",
        "SAP CRM", "SAP SRM",
        "SAP SuccessFactors",
        "SAP Ariba",
        "TOTVS", "Protheus", "TOTVS RM", "Datasul",
        "Oracle ERP", "Oracle Cloud",
        "Salesforce", "Salesforce CRM", "Apex", "SOQL",
        "Microsoft Dynamics", "Dynamics 365", "NAV", "AX",
        "NetSuite", "Workday",
    ],
    "seguranca": [
        "OWASP", "Segurança de Aplicações",
        "Pentest", "Penetration Testing",
        "Vulnerability Assessment",
        "SIEM", "SOC",
        "Firewall", "WAF",
        "IDS", "IPS",
        "Cryptography", "Criptografia",
        "SSL", "TLS", "HTTPS",
        "OAuth", "OAuth2", "JWT", "SAML",
        "LDAP", "Active Directory",
        "IAM", "Identity Management",
        "Zero Trust",
        "GDPR", "LGPD", "Compliance",
    ],
    "metodologias": [
        "Scrum", "Kanban", "Agile", "Ágil",
        "SAFe", "Scaled Agile",
        "Lean", "Lean Startup",
        "DevOps", "DevSecOps",
        "TDD", "Test Driven Development",
        "BDD", "Behavior Driven Development",
        "DDD", "Domain Driven Design",
        "Clean Code", "Código Limpo",
        "Clean Architecture", "Arquitetura Limpa",
        "SOLID", "Design Patterns", "Padrões de Projeto",
        "Microservices", "Monolith",
        "Event Sourcing", "CQRS",
        "GitFlow", "Git", "GitHub", "GitLab", "Bitbucket",
    ],
}

SOFT_SKILLS_TAXONOMY: list[str] = [
    "Comunicação", "Communication",
    "Comunicação verbal", "Verbal Communication",
    "Comunicação escrita", "Written Communication",
    "Trabalho em equipe", "Teamwork", "Team Player",
    "Colaboração", "Collaboration",
    "Liderança", "Leadership",
    "Gestão de pessoas", "People Management",
    "Gestão de tempo", "Time Management",
    "Organização", "Organization",
    "Proatividade", "Proactivity", "Iniciativa", "Initiative",
    "Resolução de problemas", "Problem Solving",
    "Pensamento crítico", "Critical Thinking",
    "Pensamento analítico", "Analytical Thinking",
    "Criatividade", "Creativity",
    "Inovação", "Innovation",
    "Adaptabilidade", "Adaptability", "Flexibilidade", "Flexibility",
    "Resiliência", "Resilience",
    "Inteligência emocional", "Emotional Intelligence",
    "Empatia", "Empathy",
    "Negociação", "Negotiation",
    "Persuasão", "Persuasion",
    "Apresentação", "Presentation Skills",
    "Feedback", "Dar e receber feedback",
    "Mentoria", "Mentoring", "Coaching",
    "Tomada de decisão", "Decision Making",
    "Gestão de conflitos", "Conflict Resolution",
    "Orientação a resultados", "Results Oriented",
    "Foco no cliente", "Customer Focus",
    "Autonomia", "Self-Management",
    "Aprendizado contínuo", "Continuous Learning",
    "Atenção aos detalhes", "Attention to Detail",
    "Multitarefa", "Multitasking",
    "Trabalho sob pressão", "Work Under Pressure",
]

LANGUAGES_TAXONOMY: dict[str, dict] = {
    "inglês": {"canonical": "Inglês", "synonyms": ["English", "Ingles"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "espanhol": {"canonical": "Espanhol", "synonyms": ["Spanish", "Español", "Castelhano"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "português": {"canonical": "Português", "synonyms": ["Portuguese", "Portugues"], "levels": ["Nativo", "Fluente"]},
    "francês": {"canonical": "Francês", "synonyms": ["French", "Français", "Frances"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "alemão": {"canonical": "Alemão", "synonyms": ["German", "Deutsch", "Alemao"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "italiano": {"canonical": "Italiano", "synonyms": ["Italian", "Italiana"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "mandarim": {"canonical": "Mandarim", "synonyms": ["Chinese", "Mandarin", "Chinês"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "japonês": {"canonical": "Japonês", "synonyms": ["Japanese", "Japones"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "coreano": {"canonical": "Coreano", "synonyms": ["Korean", "Coreana"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "russo": {"canonical": "Russo", "synonyms": ["Russian"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "árabe": {"canonical": "Árabe", "synonyms": ["Arabic", "Arabe"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "hebraico": {"canonical": "Hebraico", "synonyms": ["Hebrew"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "holandês": {"canonical": "Holandês", "synonyms": ["Dutch", "Holandes", "Neerlandês"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "polonês": {"canonical": "Polonês", "synonyms": ["Polish", "Polones"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "sueco": {"canonical": "Sueco", "synonyms": ["Swedish", "Svenska"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]},
    "libras": {"canonical": "Libras", "synonyms": ["LIBRAS", "Língua Brasileira de Sinais"], "levels": ["Básico", "Intermediário", "Avançado", "Fluente"]},
}

CERTIFICATIONS_TAXONOMY: dict[str, list[str]] = {
    "cloud_aws": [
        "AWS Certified Cloud Practitioner",
        "AWS Certified Solutions Architect Associate",
        "AWS Certified Solutions Architect Professional",
        "AWS Certified Developer Associate",
        "AWS Certified SysOps Administrator",
        "AWS Certified DevOps Engineer Professional",
        "AWS Certified Data Analytics",
        "AWS Certified Machine Learning",
        "AWS Certified Security Specialty",
    ],
    "cloud_azure": [
        "Azure Fundamentals (AZ-900)",
        "Azure Administrator (AZ-104)",
        "Azure Developer (AZ-204)",
        "Azure Solutions Architect (AZ-305)",
        "Azure DevOps Engineer (AZ-400)",
        "Azure Data Engineer (DP-203)",
        "Azure Data Scientist (DP-100)",
        "Azure Security Engineer (AZ-500)",
    ],
    "cloud_gcp": [
        "Google Cloud Digital Leader",
        "Google Cloud Associate Cloud Engineer",
        "Google Cloud Professional Cloud Architect",
        "Google Cloud Professional Data Engineer",
        "Google Cloud Professional Machine Learning Engineer",
        "Google Cloud Professional Cloud DevOps Engineer",
    ],
    "devops": [
        "Kubernetes Administrator (CKA)",
        "Kubernetes Application Developer (CKAD)",
        "Kubernetes Security Specialist (CKS)",
        "Docker Certified Associate",
        "Terraform Associate",
        "HashiCorp Vault Associate",
        "GitLab Certified Associate",
    ],
    "agile": [
        "Certified Scrum Master (CSM)",
        "Professional Scrum Master (PSM I, PSM II, PSM III)",
        "Certified Scrum Product Owner (CSPO)",
        "Professional Scrum Product Owner (PSPO)",
        "SAFe Agilist (SA)",
        "SAFe Practitioner (SP)",
        "SAFe Scrum Master (SSM)",
        "PMI-ACP",
        "ICAgile Certified Professional (ICP)",
        "Kanban Management Professional (KMP)",
    ],
    "gestao_projetos": [
        "PMP (Project Management Professional)",
        "CAPM (Certified Associate in Project Management)",
        "PRINCE2 Foundation",
        "PRINCE2 Practitioner",
        "ITIL Foundation",
        "ITIL Managing Professional",
        "COBIT Foundation",
    ],
    "seguranca": [
        "CISSP (Certified Information Systems Security Professional)",
        "CISM (Certified Information Security Manager)",
        "CEH (Certified Ethical Hacker)",
        "CompTIA Security+",
        "CompTIA CySA+",
        "CompTIA PenTest+",
        "OSCP (Offensive Security Certified Professional)",
        "CCSP (Certified Cloud Security Professional)",
    ],
    "dados": [
        "Google Data Analytics Certificate",
        "IBM Data Science Professional Certificate",
        "Microsoft Certified: Data Analyst Associate",
        "Databricks Certified Data Engineer",
        "Snowflake SnowPro Core",
        "dbt Certified Analytics Engineer",
    ],
    "sap": [
        "SAP Certified Application Associate",
        "SAP Certified Development Associate",
        "SAP Certified Technology Associate",
        "SAP S/4HANA Certification",
        "SAP ABAP Certification",
        "SAP Fiori Certification",
    ],
    "salesforce": [
        "Salesforce Administrator",
        "Salesforce Platform Developer I",
        "Salesforce Platform Developer II",
        "Salesforce Sales Cloud Consultant",
        "Salesforce Service Cloud Consultant",
        "Salesforce Marketing Cloud Email Specialist",
    ],
    "outras": [
        "Oracle Certified Professional",
        "Microsoft Certified: Azure Administrator",
        "Cisco CCNA",
        "Cisco CCNP",
        "Red Hat Certified System Administrator (RHCSA)",
        "Red Hat Certified Engineer (RHCE)",
        "Linux Foundation Certified System Administrator (LFCS)",
    ],
}

INDUSTRIES_TAXONOMY: list[str] = [
    "Fintech", "Serviços Financeiros", "Banco", "Banco Digital", "Seguros", "Insurtech",
    "E-commerce", "Varejo", "Retail", "Marketplace",
    "Healthtech", "Saúde", "Healthcare", "Farmacêutico", "Biotech",
    "Edtech", "Educação", "Education",
    "Agritech", "Agronegócio", "Agricultura",
    "Proptech", "Imobiliário", "Real Estate",
    "Legaltech", "Jurídico", "Legal",
    "Martech", "Marketing", "Publicidade", "Advertising",
    "HRtech", "Recursos Humanos", "RH",
    "Logtech", "Logística", "Supply Chain", "Transporte",
    "Foodtech", "Alimentação", "Restaurantes", "Delivery",
    "Traveltech", "Turismo", "Viagens", "Hotelaria",
    "Gamedev", "Games", "Jogos", "Entretenimento",
    "Mídia", "Media", "Streaming", "Conteúdo",
    "SaaS", "Software as a Service",
    "B2B", "B2C", "B2B2C", "D2C",
    "Startup", "Scale-up", "Unicórnio",
    "Consultoria", "Consulting",
    "Telecomunicações", "Telecom",
    "Energia", "Energy", "Oil & Gas", "Renewables",
    "Automotivo", "Automotive", "Mobilidade",
    "Manufatura", "Manufacturing", "Indústria",
    "Construção", "Construction", "Engenharia Civil",
    "Governo", "Government", "Setor Público",
    "ONG", "Non-profit", "Terceiro Setor",
]

SENIORITY_LEVELS: dict[str, dict] = {
    "estagiario": {
        "canonical": "Estagiário",
        "synonyms": ["Estágio", "Intern", "Internship", "Trainee"],
        "years": "0",
    },
    "junior": {
        "canonical": "Júnior",
        "synonyms": ["Junior", "Jr", "Jr.", "Nível 1", "Level 1", "Entry Level", "Iniciante"],
        "years": "0-2",
    },
    "pleno": {
        "canonical": "Pleno",
        "synonyms": ["Mid", "Mid-Level", "Nível 2", "Level 2", "Intermediário"],
        "years": "3-5",
    },
    "senior": {
        "canonical": "Sênior",
        "synonyms": ["Senior", "Sr", "Sr.", "Nível 3", "Level 3", "Experiente"],
        "years": "6-9",
    },
    "especialista": {
        "canonical": "Especialista",
        "synonyms": ["Specialist", "Expert", "Staff", "Staff Engineer", "Principal"],
        "years": "8+",
    },
    "lead": {
        "canonical": "Lead",
        "synonyms": ["Tech Lead", "Líder Técnico", "Team Lead", "Líder de Equipe"],
        "years": "5+",
    },
    "manager": {
        "canonical": "Gerente",
        "synonyms": ["Manager", "Engineering Manager", "Gestor"],
        "years": "7+",
    },
    "director": {
        "canonical": "Diretor",
        "synonyms": ["Director", "Head", "VP", "Vice President"],
        "years": "10+",
    },
    "c_level": {
        "canonical": "C-Level",
        "synonyms": ["CTO", "CIO", "CPO", "CEO", "Chief", "Executive"],
        "years": "12+",
    },
}

WORK_MODELS: dict[str, list[str]] = {
    "remoto": ["Remoto", "Remote", "100% Remoto", "Full Remote", "Trabalho Remoto", "Home Office"],
    "hibrido": ["Híbrido", "Hybrid", "Flexível", "Flexible", "Parcialmente Remoto"],
    "presencial": ["Presencial", "On-site", "Escritório", "Office", "In-person"],
}

LOCATIONS_BRAZIL: dict[str, list[str]] = {
    "sao_paulo": ["São Paulo", "SP", "São Paulo - Capital", "Grande São Paulo", "ABCD", "Campinas", "Santos", "Sorocaba", "Ribeirão Preto", "São José dos Campos"],
    "rio_de_janeiro": ["Rio de Janeiro", "RJ", "Rio de Janeiro - Capital", "Niterói", "Grande Rio"],
    "minas_gerais": ["Minas Gerais", "MG", "Belo Horizonte", "BH", "Uberlândia", "Contagem"],
    "parana": ["Paraná", "PR", "Curitiba", "Londrina", "Maringá"],
    "rio_grande_sul": ["Rio Grande do Sul", "RS", "Porto Alegre", "POA", "Caxias do Sul"],
    "santa_catarina": ["Santa Catarina", "SC", "Florianópolis", "Joinville", "Blumenau", "Itajaí"],
    "bahia": ["Bahia", "BA", "Salvador", "Feira de Santana"],
    "pernambuco": ["Pernambuco", "PE", "Recife", "Porto Digital"],
    "ceara": ["Ceará", "CE", "Fortaleza"],
    "distrito_federal": ["Distrito Federal", "DF", "Brasília", "BSB"],
    "goias": ["Goiás", "GO", "Goiânia"],
    "espirito_santo": ["Espírito Santo", "ES", "Vitória"],
    "para": ["Pará", "PA", "Belém"],
    "amazonas": ["Amazonas", "AM", "Manaus"],
    "outros": ["Brasil", "Nacional", "Todo Brasil", "LATAM", "América Latina", "Global", "Internacional", "Remoto Brasil"],
}


class TaxonomyService:
    """Service for taxonomy lookups and matching."""
    
    _instance = None
    _all_job_titles: set[str] = set()
    _all_skills: set[str] = set()
    _all_locations: set[str] = set()
    _synonym_map: dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        for category, titles in JOB_TITLES_TAXONOMY.items():
            for title in titles:
                self._all_job_titles.add(title.lower())
                self._synonym_map[title.lower()] = title
        
        for category, skills in TECHNICAL_SKILLS_TAXONOMY.items():
            for skill in skills:
                self._all_skills.add(skill.lower())
                self._synonym_map[skill.lower()] = skill
        
        for skill in SOFT_SKILLS_TAXONOMY:
            self._all_skills.add(skill.lower())
            self._synonym_map[skill.lower()] = skill
        
        for region, cities in LOCATIONS_BRAZIL.items():
            for city in cities:
                self._all_locations.add(city.lower())
                self._synonym_map[city.lower()] = city
    
    def find_job_title(self, text: str) -> str | None:
        """Find matching job title from taxonomy."""
        text_lower = text.lower().strip()
        if text_lower in self._all_job_titles:
            return self._synonym_map.get(text_lower, text)
        
        for title in self._all_job_titles:
            if title in text_lower or text_lower in title:
                return self._synonym_map.get(title, title)
        return None
    
    def find_skill(self, text: str) -> str | None:
        """Find matching skill from taxonomy."""
        text_lower = text.lower().strip()
        if text_lower in self._all_skills:
            return self._synonym_map.get(text_lower, text)
        
        for skill in self._all_skills:
            if skill == text_lower or text_lower == skill:
                return self._synonym_map.get(skill, skill)
        return None
    
    def find_location(self, text: str) -> str | None:
        """Find matching location from taxonomy."""
        text_lower = text.lower().strip()
        if text_lower in self._all_locations:
            return self._synonym_map.get(text_lower, text)
        
        for location in self._all_locations:
            if location in text_lower or text_lower in location:
                return self._synonym_map.get(location, location)
        return None
    
    def get_all_job_titles(self) -> list[str]:
        """Get all job titles from taxonomy."""
        result = []
        for category, titles in JOB_TITLES_TAXONOMY.items():
            result.extend(titles)
        return result
    
    def get_all_skills(self) -> list[str]:
        """Get all skills from taxonomy."""
        result = []
        for category, skills in TECHNICAL_SKILLS_TAXONOMY.items():
            result.extend(skills)
        result.extend(SOFT_SKILLS_TAXONOMY)
        return result
    
    def get_skills_by_category(self, category: str) -> list[str]:
        """Get skills by category."""
        return TECHNICAL_SKILLS_TAXONOMY.get(category, [])
    
    def get_job_titles_by_category(self, category: str) -> list[str]:
        """Get job titles by category."""
        return JOB_TITLES_TAXONOMY.get(category, [])
    
    def get_certifications_by_category(self, category: str) -> list[str]:
        """Get certifications by category."""
        return CERTIFICATIONS_TAXONOMY.get(category, [])
    
    def get_all_certifications(self) -> list[str]:
        """Get all certifications."""
        result = []
        for category, certs in CERTIFICATIONS_TAXONOMY.items():
            result.extend(certs)
        return result
    
    def search_taxonomy(self, query: str, limit: int = 10) -> dict[str, list[str]]:
        """Search across all taxonomy categories."""
        query_lower = query.lower().strip()
        results = {
            "job_titles": [],
            "skills": [],
            "locations": [],
            "certifications": [],
        }
        
        for title in self._all_job_titles:
            if query_lower in title:
                canonical = self._synonym_map.get(title, title)
                if canonical not in results["job_titles"]:
                    results["job_titles"].append(canonical)
        
        for skill in self._all_skills:
            if query_lower in skill:
                canonical = self._synonym_map.get(skill, skill)
                if canonical not in results["skills"]:
                    results["skills"].append(canonical)
        
        for location in self._all_locations:
            if query_lower in location:
                canonical = self._synonym_map.get(location, location)
                if canonical not in results["locations"]:
                    results["locations"].append(canonical)
        
        for category, certs in CERTIFICATIONS_TAXONOMY.items():
            for cert in certs:
                if query_lower in cert.lower():
                    if cert not in results["certifications"]:
                        results["certifications"].append(cert)
        
        for key in results:
            results[key] = results[key][:limit]
        
        return results


taxonomy_service = TaxonomyService()
