"""
Golden Queries para avaliação RAGAS dos fluxos críticos da LIA.
Cada query tem: query, expected_tools, expected_output_keywords, domain.

Domínios cobertos:
  - sourcing: busca e abordagem de candidatos
  - screening: triagem curricular e avaliação
  - job_management: criação e gestão de vagas
  - pipeline: movimentação e transições no pipeline
  - wsi_scoring: avaliação WSI (entrevista estruturada)
  - salary_benchmark: benchmarks salariais
  - candidate_search: busca genérica de candidatos
"""

GOLDEN_QUERIES = {
    "sourcing": [
        {
            "query": "Buscar desenvolvedores Python sênior com experiência em AWS em São Paulo",
            "expected_tools": ["search_candidates"],
            "expected_output_keywords": ["python", "AWS", "São Paulo", "candidato", "score"],
        },
        {
            "query": "Gerar boolean string para buscar gestores de projetos ágeis no LinkedIn",
            "expected_tools": [],
            "expected_output_keywords": ["AND", "OR", "boolean", "LinkedIn", "gestão"],
        },
        {
            "query": "Buscar engenheiros de dados com Spark e Airflow disponíveis para remoto",
            "expected_tools": ["search_candidates"],
            "expected_output_keywords": ["spark", "airflow", "remoto", "candidato", "dados"],
        },
        {
            "query": "Gerar mensagem de abordagem personalizada para candidato sênior em fintech",
            "expected_tools": [],
            "expected_output_keywords": ["mensagem", "personalizada", "fintech", "candidato"],
        },
    ],
    "screening": [
        {
            "query": "Avaliar CV do candidato para vaga de Desenvolvedor Python Sênior",
            "expected_tools": ["analyze_cv", "score_candidate"],
            "expected_output_keywords": ["score", "python", "experiência", "avaliação"],
        },
        {
            "query": "Triagem em lote dos 10 candidatos inscritos na vaga de Product Manager",
            "expected_tools": ["batch_screen", "rank_candidates"],
            "expected_output_keywords": ["ranking", "score", "lote", "candidatos"],
        },
        {
            "query": "Analisar gap de emprego de 2 anos no currículo do candidato",
            "expected_tools": ["analyze_cv"],
            "expected_output_keywords": ["gap", "contexto", "não penalizar", "evidência"],
        },
        {
            "query": "Comparar perfil do candidato com requisitos mínimos da vaga",
            "expected_tools": ["match_profile", "get_job_requirements"],
            "expected_output_keywords": ["requisitos", "match", "compatibilidade", "score"],
        },
    ],
    "job_management": [
        {
            "query": "Criar vaga de Analista de Dados Pleno para o time de inteligência",
            "expected_tools": ["create_job", "suggest_jd"],
            "expected_output_keywords": ["título", "Analista de Dados", "departamento", "vaga"],
        },
        {
            "query": "Qual o salário de mercado para Engenheiro de ML Sênior em SP?",
            "expected_tools": ["get_market_benchmarks", "search_salary_benchmark"],
            "expected_output_keywords": ["salário", "mercado", "benchmark", "SP"],
        },
        {
            "query": "Sugerir responsabilidades e benefícios para vaga de DevOps Lead",
            "expected_tools": ["suggest_jd", "enrich_job"],
            "expected_output_keywords": ["responsabilidades", "benefícios", "DevOps", "sugestões"],
        },
        {
            "query": "Publicar vaga de UX Designer em todos os job boards integrados",
            "expected_tools": ["publish_job"],
            "expected_output_keywords": ["publicar", "job board", "UX", "vaga"],
        },
    ],
    "pipeline": [
        {
            "query": "Mover candidato João Silva para etapa de Entrevista Técnica",
            "expected_tools": ["transition_candidate", "get_pipeline_stage"],
            "expected_output_keywords": ["mover", "Entrevista Técnica", "candidato", "confirmar"],
        },
        {
            "query": "Analise os gargalos no pipeline da vaga de Product Manager",
            "expected_tools": ["get_bottleneck_analysis", "get_job_velocity"],
            "expected_output_keywords": ["gargalo", "estágio", "dias", "candidatos"],
        },
        {
            "query": "Avançar todos os candidatos aprovados na triagem para Entrevista com RH",
            "expected_tools": ["batch_transition", "get_approved_candidates"],
            "expected_output_keywords": ["lote", "candidatos", "Entrevista", "avançar"],
        },
        {
            "query": "Gerar relatório de velocidade do pipeline nos últimos 30 dias",
            "expected_tools": ["get_job_velocity", "get_pipeline_metrics"],
            "expected_output_keywords": ["velocidade", "dias", "pipeline", "estágio", "relatório"],
        },
    ],
    "wsi_scoring": [
        {
            "query": "Avalie a resposta do candidato sobre liderança em equipes",
            "expected_tools": ["score_wsi_response"],
            "expected_output_keywords": ["score", "bloom", "dreyfus", "avaliação"],
        },
    ],
    "candidate_search": [
        {
            "query": "Encontre desenvolvedores React com 3+ anos disponíveis em SP",
            "expected_tools": ["search_candidates"],
            "expected_output_keywords": ["react", "desenvolvedor", "São Paulo", "experiência"],
        },
    ],
}

DOMAIN_MAPPING = {
    "sourcing": "sourcing",
    "screening": "screening",
    "job_management": "job_management",
    "pipeline": "pipeline",
    "wsi_scoring": "screening",
    "candidate_search": "sourcing",
}

REQUIRED_DOMAINS = {"sourcing", "screening", "job_management", "pipeline"}
MIN_QUERIES_PER_DOMAIN = 3
