"""
Golden Queries para avaliação RAGAS dos 5 fluxos críticos da LIA.
Cada query tem: input, expected_tools, expected_output_keywords.
"""

GOLDEN_QUERIES = {
    "wsi_scoring": [
        {
            "query": "Avalie a resposta do candidato sobre liderança em equipes",
            "expected_tools": ["score_wsi_response"],
            "expected_output_keywords": ["score", "bloom", "dreyfus", "avaliação"],
        },
    ],
    "cv_matching": [
        {
            "query": "Quais candidatos têm perfil para a vaga de Engenheiro Python?",
            "expected_tools": ["search_candidates", "get_candidate_details"],
            "expected_output_keywords": ["python", "candidato", "experiência", "score"],
        },
    ],
    "salary_benchmark": [
        {
            "query": "Qual o salário de mercado para Analista de Dados Sênior em São Paulo?",
            "expected_tools": ["get_market_benchmarks", "search_salary_benchmark"],
            "expected_output_keywords": ["salário", "mercado", "benchmark", "SP"],
        },
    ],
    "pipeline_analysis": [
        {
            "query": "Analise os gargalos no pipeline da vaga de Product Manager",
            "expected_tools": ["get_bottleneck_analysis", "get_job_velocity"],
            "expected_output_keywords": ["gargalo", "estágio", "dias", "candidatos"],
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
