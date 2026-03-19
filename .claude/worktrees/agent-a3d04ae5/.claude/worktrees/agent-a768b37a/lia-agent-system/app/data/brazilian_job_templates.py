"""
Brazilian Job Templates - Curated templates for the Brazilian market.

These templates are pre-configured with:
- Technical skills common in Brazil
- Behavioral competencies aligned with Brazilian work culture
- Market-aligned salary ranges (BRL)
- WSI questions in Portuguese
- Common benefits packages

Categories:
- Technology (Dev, Data, DevOps)
- Product (PM, Designer)
- Marketing (Growth, Content)
- HR/People (RH, DP)
- Sales/Commercial (Vendas, CS)
"""
from typing import List, Dict, Any
from uuid import uuid4


BRAZILIAN_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": str(uuid4()),
        "title": "Desenvolvedor(a) Full Stack",
        "department": "Tecnologia",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Buscamos um(a) Desenvolvedor(a) Full Stack para atuar no desenvolvimento de soluções web modernas.

Responsabilidades:
- Desenvolver e manter aplicações web usando React e Node.js
- Colaborar com times de produto e design
- Participar de code reviews e garantir qualidade do código
- Implementar testes automatizados
- Contribuir com arquitetura de soluções

Diferenciais:
- Experiência com metodologias ágeis
- Conhecimento em cloud (AWS/GCP)
- Experiência com microsserviços""",
        "technical_skills": [
            "JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL",
            "Git", "REST APIs", "Docker"
        ],
        "behavioral_competencies": [
            {"name": "Trabalho em Equipe", "weight": 4},
            {"name": "Resolução de Problemas", "weight": 5},
            {"name": "Comunicação", "weight": 3},
            {"name": "Proatividade", "weight": 4}
        ],
        "salary_min": 8000,
        "salary_max": 14000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 40/dia", "enabled": True},
            {"id": "2", "name": "Vale Transporte", "enabled": True},
            {"id": "3", "name": "Plano de Saúde", "enabled": True},
            {"id": "4", "name": "Plano Odontológico", "enabled": True},
            {"id": "5", "name": "Gympass", "enabled": True},
            {"id": "6", "name": "Home Office", "value": "3x por semana", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-tech-react",
                "question": "Descreva um projeto complexo em React que você desenvolveu. Quais desafios enfrentou e como resolveu?",
                "type": "open",
                "required": True,
                "competency_validated": "React"
            },
            {
                "id": "wsi-tech-nodejs",
                "question": "Como você estrutura uma API REST em Node.js? Fale sobre padrões e boas práticas que utiliza.",
                "type": "open",
                "required": True,
                "competency_validated": "Node.js"
            },
            {
                "id": "wsi-behav-teamwork",
                "question": "Conte sobre uma situação de conflito técnico com um colega. Como lidou?",
                "type": "open",
                "required": True,
                "competency_validated": "Trabalho em Equipe"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 21
    },
    {
        "id": str(uuid4()),
        "title": "Desenvolvedor(a) Backend Senior",
        "department": "Tecnologia",
        "seniority": "Sênior",
        "location": "Remoto",
        "work_model": "Remoto",
        "employment_type": "CLT",
        "description": """Estamos em busca de um(a) Desenvolvedor(a) Backend Sênior para liderar iniciativas técnicas.

Responsabilidades:
- Arquitetar e desenvolver sistemas backend escaláveis
- Mentoring de desenvolvedores júnior e pleno
- Definir padrões técnicos e boas práticas
- Otimizar performance e segurança
- Participar de decisões arquiteturais

Requisitos:
- 5+ anos de experiência com backend
- Experiência com sistemas de alta disponibilidade
- Conhecimento em arquitetura de microsserviços""",
        "technical_skills": [
            "Python", "Java", "PostgreSQL", "Redis", "Docker", "Kubernetes",
            "AWS", "Microsserviços", "CI/CD", "Mensageria"
        ],
        "behavioral_competencies": [
            {"name": "Liderança Técnica", "weight": 5},
            {"name": "Mentoria", "weight": 4},
            {"name": "Pensamento Estratégico", "weight": 4},
            {"name": "Comunicação", "weight": 4}
        ],
        "salary_min": 15000,
        "salary_max": 25000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 50/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde Premium", "enabled": True},
            {"id": "3", "name": "PLR", "value": "2 salários", "enabled": True},
            {"id": "4", "name": "Equipamento Home Office", "enabled": True},
            {"id": "5", "name": "Auxílio Educação", "value": "R$ 500/mês", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-tech-arch",
                "question": "Descreva a arquitetura de um sistema de alta disponibilidade que você projetou. Quais decisões tomou e por quê?",
                "type": "open",
                "required": True,
                "competency_validated": "Arquitetura"
            },
            {
                "id": "wsi-tech-scaling",
                "question": "Como você abordaria a migração de um monolito para microsserviços? Quais critérios usaria?",
                "type": "open",
                "required": True,
                "competency_validated": "Microsserviços"
            },
            {
                "id": "wsi-behav-leadership",
                "question": "Conte sobre uma situação onde precisou convencer a equipe a adotar uma nova tecnologia ou padrão.",
                "type": "open",
                "required": True,
                "competency_validated": "Liderança Técnica"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 35
    },
    {
        "id": str(uuid4()),
        "title": "Product Manager",
        "department": "Produto",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Buscamos um(a) Product Manager para liderar a estratégia e execução de produtos digitais.

Responsabilidades:
- Definir visão e roadmap do produto
- Trabalhar com squads de desenvolvimento
- Priorizar backlog baseado em dados e negócio
- Conduzir discovery e validação de hipóteses
- Acompanhar métricas de sucesso do produto

Requisitos:
- 3+ anos de experiência como PM
- Experiência com produtos digitais B2B ou B2C
- Conhecimento em metodologias ágeis""",
        "technical_skills": [
            "Product Discovery", "Roadmapping", "SQL Básico", "Analytics",
            "Jira", "Figma", "A/B Testing", "OKRs"
        ],
        "behavioral_competencies": [
            {"name": "Visão Estratégica", "weight": 5},
            {"name": "Comunicação", "weight": 5},
            {"name": "Influência sem Autoridade", "weight": 4},
            {"name": "Orientação a Dados", "weight": 4}
        ],
        "salary_min": 12000,
        "salary_max": 20000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 45/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Stock Options", "enabled": True},
            {"id": "4", "name": "Home Office", "value": "2x por semana", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-pm-discovery",
                "question": "Descreva um processo de discovery que você conduziu. Como validou as hipóteses?",
                "type": "open",
                "required": True,
                "competency_validated": "Product Discovery"
            },
            {
                "id": "wsi-pm-priority",
                "question": "Como você prioriza features quando há demandas conflitantes de stakeholders?",
                "type": "open",
                "required": True,
                "competency_validated": "Priorização"
            },
            {
                "id": "wsi-behav-influence",
                "question": "Conte sobre uma vez que precisou convencer stakeholders a mudar de direção em um projeto.",
                "type": "open",
                "required": True,
                "competency_validated": "Influência sem Autoridade"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 28
    },
    {
        "id": str(uuid4()),
        "title": "UX/UI Designer",
        "department": "Design",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Procuramos um(a) UX/UI Designer para criar experiências digitais excepcionais.

Responsabilidades:
- Conduzir pesquisas com usuários
- Criar wireframes, protótipos e designs de alta fidelidade
- Colaborar com PMs e desenvolvedores
- Manter e evoluir design system
- Realizar testes de usabilidade

Requisitos:
- 3+ anos de experiência em UX/UI
- Portfólio com casos de estudo
- Domínio de Figma""",
        "technical_skills": [
            "Figma", "Design System", "Prototipagem", "Pesquisa com Usuários",
            "Usabilidade", "Design Responsivo", "Acessibilidade"
        ],
        "behavioral_competencies": [
            {"name": "Empatia", "weight": 5},
            {"name": "Atenção a Detalhes", "weight": 4},
            {"name": "Colaboração", "weight": 4},
            {"name": "Criatividade", "weight": 4}
        ],
        "salary_min": 8000,
        "salary_max": 15000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 40/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Auxílio Home Office", "value": "R$ 200/mês", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-ux-research",
                "question": "Descreva um projeto onde a pesquisa com usuários mudou significativamente a direção do design.",
                "type": "open",
                "required": True,
                "competency_validated": "Pesquisa com Usuários"
            },
            {
                "id": "wsi-ux-ds",
                "question": "Como você aborda a criação ou evolução de um Design System?",
                "type": "open",
                "required": True,
                "competency_validated": "Design System"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 25
    },
    {
        "id": str(uuid4()),
        "title": "Analista de Marketing Digital",
        "department": "Marketing",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Buscamos um(a) Analista de Marketing Digital para impulsionar nossa presença online.

Responsabilidades:
- Planejar e executar campanhas de mídia paga
- Gerenciar redes sociais e conteúdo
- Analisar métricas e otimizar ROI
- Implementar estratégias de SEO
- Trabalhar com automação de marketing

Requisitos:
- 3+ anos de experiência em marketing digital
- Conhecimento em Google Ads e Meta Ads
- Experiência com ferramentas de analytics""",
        "technical_skills": [
            "Google Ads", "Meta Ads", "Google Analytics", "SEO",
            "RD Station", "HubSpot", "Copywriting", "Excel Avançado"
        ],
        "behavioral_competencies": [
            {"name": "Criatividade", "weight": 4},
            {"name": "Orientação a Resultados", "weight": 5},
            {"name": "Organização", "weight": 4},
            {"name": "Adaptabilidade", "weight": 3}
        ],
        "salary_min": 5000,
        "salary_max": 9000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 35/dia", "enabled": True},
            {"id": "2", "name": "Vale Transporte", "enabled": True},
            {"id": "3", "name": "Plano de Saúde", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-mkt-campaign",
                "question": "Descreva uma campanha de mídia paga que você planejou. Quais métricas acompanhou e quais resultados obteve?",
                "type": "open",
                "required": True,
                "competency_validated": "Google Ads"
            },
            {
                "id": "wsi-mkt-roi",
                "question": "Como você calcula e otimiza o ROI de campanhas de marketing?",
                "type": "open",
                "required": True,
                "competency_validated": "Analytics"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 18
    },
    {
        "id": str(uuid4()),
        "title": "Analista de RH / People Analytics",
        "department": "Recursos Humanos",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Procuramos um(a) Analista de RH com foco em People Analytics.

Responsabilidades:
- Coletar e analisar dados de pessoas
- Criar dashboards e relatórios de RH
- Apoiar decisões estratégicas com dados
- Monitorar indicadores de turnover, engajamento e performance
- Colaborar com áreas de negócio

Requisitos:
- 3+ anos de experiência em RH
- Conhecimento em análise de dados
- Excel avançado e Power BI""",
        "technical_skills": [
            "People Analytics", "Power BI", "Excel Avançado", "HRIS",
            "Indicadores de RH", "SQL Básico", "Estatística"
        ],
        "behavioral_competencies": [
            {"name": "Pensamento Analítico", "weight": 5},
            {"name": "Atenção a Detalhes", "weight": 4},
            {"name": "Comunicação", "weight": 4},
            {"name": "Ética", "weight": 5}
        ],
        "salary_min": 6000,
        "salary_max": 10000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 35/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Auxílio Educação", "value": "R$ 300/mês", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-hr-analytics",
                "question": "Descreva um projeto de People Analytics que você conduziu. Quais insights gerou e que ações foram tomadas?",
                "type": "open",
                "required": True,
                "competency_validated": "People Analytics"
            },
            {
                "id": "wsi-hr-indicators",
                "question": "Quais indicadores de RH você considera essenciais e por quê?",
                "type": "open",
                "required": True,
                "competency_validated": "Indicadores de RH"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 22
    },
    {
        "id": str(uuid4()),
        "title": "Executivo(a) de Vendas B2B",
        "department": "Comercial",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Presencial",
        "employment_type": "CLT",
        "description": """Buscamos um(a) Executivo(a) de Vendas B2B para expandir nossa base de clientes.

Responsabilidades:
- Prospectar e qualificar leads
- Conduzir reuniões de vendas consultivas
- Negociar contratos e fechar deals
- Gerenciar pipeline no CRM
- Atingir metas mensais e trimestrais

Requisitos:
- 3+ anos de experiência em vendas B2B
- Experiência com vendas consultivas
- Conhecimento em CRM (Salesforce/HubSpot)""",
        "technical_skills": [
            "Vendas Consultivas", "CRM Salesforce", "Negociação",
            "Pipeline Management", "Cold Calling", "Social Selling"
        ],
        "behavioral_competencies": [
            {"name": "Resiliência", "weight": 5},
            {"name": "Persuasão", "weight": 5},
            {"name": "Orientação a Resultados", "weight": 5},
            {"name": "Escuta Ativa", "weight": 4}
        ],
        "salary_min": 5000,
        "salary_max": 8000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 35/dia", "enabled": True},
            {"id": "2", "name": "Vale Transporte", "enabled": True},
            {"id": "3", "name": "Comissão", "value": "até 3x salário", "enabled": True},
            {"id": "4", "name": "Plano de Saúde", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-sales-deal",
                "question": "Descreva seu maior deal fechado. Qual foi a estratégia e como você superou objeções?",
                "type": "open",
                "required": True,
                "competency_validated": "Vendas Consultivas"
            },
            {
                "id": "wsi-sales-pipeline",
                "question": "Como você organiza e prioriza seu pipeline de vendas?",
                "type": "open",
                "required": True,
                "competency_validated": "Pipeline Management"
            },
            {
                "id": "wsi-behav-resilience",
                "question": "Conte sobre um momento de muita pressão por metas. Como lidou?",
                "type": "open",
                "required": True,
                "competency_validated": "Resiliência"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 15
    },
    {
        "id": str(uuid4()),
        "title": "Customer Success Manager",
        "department": "Customer Success",
        "seniority": "Pleno",
        "location": "Remoto",
        "work_model": "Remoto",
        "employment_type": "CLT",
        "description": """Procuramos um(a) Customer Success Manager para garantir o sucesso de nossos clientes.

Responsabilidades:
- Gerenciar carteira de clientes
- Conduzir onboarding e QBRs
- Identificar oportunidades de upsell/cross-sell
- Monitorar health score e prevenir churn
- Ser voz do cliente internamente

Requisitos:
- 3+ anos de experiência em CS ou áreas relacionadas
- Experiência com SaaS B2B
- Conhecimento em métricas de sucesso""",
        "technical_skills": [
            "Customer Success", "Health Score", "Onboarding",
            "Gainsight", "HubSpot", "Churn Prevention", "QBR"
        ],
        "behavioral_competencies": [
            {"name": "Empatia", "weight": 5},
            {"name": "Comunicação", "weight": 5},
            {"name": "Orientação ao Cliente", "weight": 5},
            {"name": "Proatividade", "weight": 4}
        ],
        "salary_min": 7000,
        "salary_max": 12000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 40/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Bônus por Retenção", "enabled": True},
            {"id": "4", "name": "Equipamento Home Office", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-cs-churn",
                "question": "Descreva uma situação de risco de churn que você identificou e reverteu. O que fez?",
                "type": "open",
                "required": True,
                "competency_validated": "Churn Prevention"
            },
            {
                "id": "wsi-cs-onboarding",
                "question": "Como você estrutura um onboarding eficiente para novos clientes?",
                "type": "open",
                "required": True,
                "competency_validated": "Onboarding"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 20
    },
    {
        "id": str(uuid4()),
        "title": "Cientista de Dados",
        "department": "Dados",
        "seniority": "Pleno",
        "location": "São Paulo, SP",
        "work_model": "Híbrido",
        "employment_type": "CLT",
        "description": """Buscamos um(a) Cientista de Dados para extrair insights e construir modelos preditivos.

Responsabilidades:
- Desenvolver modelos de machine learning
- Analisar grandes volumes de dados
- Criar visualizações e dashboards
- Colaborar com áreas de negócio
- Implementar pipelines de dados

Requisitos:
- 3+ anos de experiência em Data Science
- Python avançado (pandas, scikit-learn)
- Experiência com SQL e cloud""",
        "technical_skills": [
            "Python", "Machine Learning", "SQL", "Pandas",
            "Scikit-learn", "TensorFlow", "Power BI", "AWS/GCP"
        ],
        "behavioral_competencies": [
            {"name": "Pensamento Analítico", "weight": 5},
            {"name": "Curiosidade", "weight": 4},
            {"name": "Comunicação de Dados", "weight": 4},
            {"name": "Resolução de Problemas", "weight": 5}
        ],
        "salary_min": 10000,
        "salary_max": 18000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 45/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Auxílio Educação", "value": "R$ 500/mês", "enabled": True},
            {"id": "4", "name": "Home Office", "value": "3x por semana", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-ds-model",
                "question": "Descreva um modelo de ML que você desenvolveu e colocou em produção. Quais métricas usou para avaliar?",
                "type": "open",
                "required": True,
                "competency_validated": "Machine Learning"
            },
            {
                "id": "wsi-ds-impact",
                "question": "Conte sobre um insight de dados que gerou impacto significativo no negócio.",
                "type": "open",
                "required": True,
                "competency_validated": "Comunicação de Dados"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 30
    },
    {
        "id": str(uuid4()),
        "title": "DevOps Engineer",
        "department": "Infraestrutura",
        "seniority": "Pleno",
        "location": "Remoto",
        "work_model": "Remoto",
        "employment_type": "CLT",
        "description": """Procuramos um(a) DevOps Engineer para automatizar e otimizar nossa infraestrutura.

Responsabilidades:
- Implementar e manter pipelines CI/CD
- Gerenciar infraestrutura cloud (AWS/GCP)
- Automatizar processos com IaC (Terraform)
- Monitorar e otimizar performance
- Garantir segurança da infraestrutura

Requisitos:
- 3+ anos de experiência em DevOps/SRE
- Experiência com containers e Kubernetes
- Conhecimento em scripting (Bash/Python)""",
        "technical_skills": [
            "AWS", "Docker", "Kubernetes", "Terraform",
            "CI/CD", "Linux", "Monitoring", "Python/Bash"
        ],
        "behavioral_competencies": [
            {"name": "Atenção a Detalhes", "weight": 5},
            {"name": "Resolução de Problemas", "weight": 5},
            {"name": "Documentação", "weight": 3},
            {"name": "Trabalho sob Pressão", "weight": 4}
        ],
        "salary_min": 10000,
        "salary_max": 18000,
        "benefits": [
            {"id": "1", "name": "Vale Refeição", "value": "R$ 45/dia", "enabled": True},
            {"id": "2", "name": "Plano de Saúde", "enabled": True},
            {"id": "3", "name": "Equipamento Home Office", "enabled": True},
            {"id": "4", "name": "Certificações AWS", "enabled": True}
        ],
        "wsi_questions": [
            {
                "id": "wsi-devops-cicd",
                "question": "Descreva um pipeline CI/CD que você implementou. Quais ferramentas usou e como lidou com rollbacks?",
                "type": "open",
                "required": True,
                "competency_validated": "CI/CD"
            },
            {
                "id": "wsi-devops-incident",
                "question": "Conte sobre um incidente crítico em produção que você resolveu. Qual foi o processo?",
                "type": "open",
                "required": True,
                "competency_validated": "Resolução de Problemas"
            }
        ],
        "is_template": True,
        "outcome_status": "filled",
        "time_to_fill_days": 28
    }
]


def get_templates_by_department(department: str) -> List[Dict[str, Any]]:
    """Get templates filtered by department."""
    return [t for t in BRAZILIAN_TEMPLATES if t["department"].lower() == department.lower()]


def get_templates_by_seniority(seniority: str) -> List[Dict[str, Any]]:
    """Get templates filtered by seniority."""
    return [t for t in BRAZILIAN_TEMPLATES if t["seniority"].lower() == seniority.lower()]


def get_all_templates() -> List[Dict[str, Any]]:
    """Get all available templates."""
    return BRAZILIAN_TEMPLATES
