"""Contract sensor — proveniência honesta do benchmark salarial.

Auditoria fluxo de criação de vagas (2026-06-03). Dois defeitos P0 confirmados
em MarketBenchmarkService (app/domains/analytics/services/market_benchmark_service.py):

  (1) Sem SERP_API_KEY (sem busca web real), o serviço ainda anexava domínios
      reais (glassdoor.com.br / linkedin.com) a um número 100% inventado pelo
      LLM — proveniência fabricada. A LIA narrava "fonte: mercado".
  (2) Senioridade "Diretoria" não casava com a chave "diretor" do dict default
      → caía no fallback de analista (6000, 12000). R$6-12k para uma Diretoria.

Estes sensores pinam o invariante: SEM busca real → SEM fonte real + estimativa
explícita; e faixa de diretoria NUNCA pode ser de analista.

Se este teste falhar:
  → Fonte real (glassdoor/linkedin/...) só pode aparecer em `sources` quando
    is_estimate=False (houve busca SerpAPI de fato). Estimativa do LLM deve usar
    source='estimativa_llm_sem_busca', confidence='low', is_estimate=True.
  → A faixa default por senioridade deve respeitar a ordem (diretoria > sênior).
    Verifique o mapeamento de aliases em _get_default_salary_estimate.
"""
from unittest.mock import patch

from app.domains.analytics.services.market_benchmark_service import (
    MarketBenchmarkService,
)

_REAL_DOMAINS = (
    "glassdoor", "linkedin", "catho", "indeed", "robert", "vagas.com", "gupy",
)


def test_director_default_range_is_not_analyst_range():
    svc = MarketBenchmarkService()
    for label in ("Diretoria", "Diretor", "diretor(a)", "director", "C-Level"):
        data = svc._get_default_salary_estimate("Diretor de Pesquisa Clínica", label)["data"]
        assert data["min"] >= 20000, (
            f"senioridade '{label}': min R${data['min']} caiu em faixa de analista"
        )

    senior = svc._get_default_salary_estimate("Analista", "Sênior")["data"]
    director = svc._get_default_salary_estimate("Analista", "Diretoria")["data"]
    assert director["min"] > senior["max"], (
        "faixa de diretoria deve estar inteiramente acima da de sênior"
    )


def test_unknown_seniority_is_not_silent_analyst_range():
    svc = MarketBenchmarkService()
    data = svc._get_default_salary_estimate("Cargo Exótico", "NívelInexistente")["data"]
    # Senioridade desconhecida não pode virar faixa de analista anchorada como fato.
    assert data["confidence"] in ("low", "none")
    assert data.get("sources_found", []) == []


async def test_no_real_search_no_real_source_attribution():
    svc = MarketBenchmarkService()
    svc._serp_api_key = ""  # garante ausência de busca real

    async def fake_search(query):
        return {"success": True, "results": [], "query": query, "llm_fallback": True}

    async def fake_parse(search_results, role, seniority=None, location=None):
        # LLM alucina domínios reais + confiança média (comportamento observado).
        return {
            "success": True,
            "data": {
                "min": 8000, "max": 15000, "median": 11500,
                "sources_found": ["glassdoor.com.br", "linkedin.com"],
                "confidence": "medium", "trend": "estável", "notes": "x",
            },
            "llm_fallback": True,
        }

    with patch.object(svc, "_do_web_search", fake_search), \
         patch.object(svc, "_parse_salary_from_results", fake_parse):
        result = await svc.search_salary_benchmark(
            role="Diretor de Pesquisa Clínica", seniority="Diretoria",
        )

    assert result["is_estimate"] is True, "sem busca real, is_estimate deve ser True"
    assert result["confidence"] == "low", "estimativa sem busca → confiança baixa"
    joined = " ".join(result.get("sources", [])).lower()
    for dom in _REAL_DOMAINS:
        assert dom not in joined, (
            f"proveniência fabricada vazou em sources={result.get('sources')}"
        )
