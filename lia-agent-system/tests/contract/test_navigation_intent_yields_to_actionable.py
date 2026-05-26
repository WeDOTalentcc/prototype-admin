"""Sensor canonical CR-1 (2026-05-26) — NavigationIntentDetector NÃO deve
deflectar queries que são intent acionável de tool (analytics, relatório,
KPI, métricas, funil-de-query, etc.). Esse sensor pina o fix proposto em
~/Documents/wedotalent_audit_2026-05-26/AUDIT_CHAT_E_WIZARD_2026-05-26.md
§3 CR-1.

Bug histórico (transcript Paulo 2026-05-26):
  User: "faca analise de funil e velocidade de gargalo das vagas ativas"
  → Detector retorna page='Vagas' confidence=0.84 (deflecta "Posso te
     levar pro ambiente de vagas")
  → Tool real `get_vacancy_funnel` / `get_velocity_metrics` /
     `get_bottleneck_analysis` NUNCA é invocada
  → User vê loop de deflexão de navegação em vez de receber relatório

Princípio canonical:
  Quando user usa palavras-chave de AÇÃO/ANALYTICS (análise, funil,
  relatório, velocidade, gargalo, métricas, KPI, taxa, conversão,
  quantos, quantas, status, etc.), o NavigationIntentDetector deve
  RETORNAR None (sem deflexão) mesmo se patterns de página
  (vagas/funil/configurações) também batem. Tool real tem precedência
  sobre sugestão de navegação.

Não confundir com:
  - Imperativos de navegação clara ("me leva pra vagas") — esses CONTINUAM
    deflectando (mantém BUG-18 fix).
  - Navegação genuína ("abra a página de vagas") — continua deflectando.
"""
import pytest


# Queries do transcript real Paulo + variações canonical de analytics
# que DEVEM RETORNAR page=None (sem deflexão — tool deve rodar)
ANALYTICS_QUERIES_MUST_NOT_DEFLECT = [
    # Transcript Paulo 2026-05-26
    "faca analsie de funil e velocidade de gargalo das vagas ativas",
    "faça análise de funil e velocidade de gargalo das vagas ativas",
    "consegue gerar um relatorio de uma vaga ativa?",
    "consegue gerar um relatório de uma vaga ativa?",
    # "mas ha vagas ativas na plataforma" — statement conversacional, fora do escopo CR-1
    # Analytics canonical
    "como está o funil da vaga Python?",
    "como esta o funil da vaga Python",
    "qual a taxa de conversão da vaga X?",
    "qual a taxa de conversao",
    "quantos candidatos estão na etapa de entrevista?",
    "quantos candidatos temos no funil?",
    "quantas vagas ativas temos?",
    "qual a velocidade de fechamento das vagas?",
    "gere relatório de KPI",
    "mostre as métricas de velocidade",
    "vagas sem candidatos?",
    "análise de gargalo do pipeline",
    "qual o status do pipeline da vaga Python?",
    "compare a velocidade de duas vagas",
    "tendência de candidaturas nas últimas 4 semanas",
]

# Queries que CONTINUAM deflectando (navegação genuína, sem keywords de analytics)
NAV_QUERIES_MUST_DEFLECT = [
    "me leva pra vagas",
    "abra a página de vagas",
    "abrir página de vagas",
    "vamos pra configurações",
    "quero ver o funil de talentos",
    "vamos para o painel de controle",
    "abra a página de configurações",
    "me mostra a página de candidatos",
]


@pytest.mark.parametrize("query", ANALYTICS_QUERIES_MUST_NOT_DEFLECT)
def test_analytics_queries_must_not_deflect(query):
    """CR-1 fix (2026-05-26): queries com keywords de analytics/relatório
    NÃO podem ser interpretadas como navegação. Tool real (get_vacancy_funnel,
    get_velocity_metrics, get_bottleneck_analysis, get_pipeline_stats) tem
    precedência sobre sugestão de navegação."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is None, (
        f"Query analytics {query!r} foi deflectada pra page={result.page!r} "
        f"confidence={result.confidence}. CR-1 fix requer que keywords de "
        f"análise/funil/relatório/velocidade/gargalo/métrica/KPI/conversão/"
        f"quantos suprimam a deflexão de navegação — tool real deve rodar."
    )
    assert result.confidence == 0.0 or result.page is None


@pytest.mark.parametrize("query", NAV_QUERIES_MUST_DEFLECT)
def test_nav_queries_still_deflect(query):
    """Não-regressão BUG-18 fix: imperativos de navegação genuína continuam
    deflectando normalmente. CR-1 fix NÃO pode quebrar BUG-18."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is not None, (
        f"Query de navegação genuína {query!r} NÃO deflectou (page={result.page!r}, "
        f"confidence={result.confidence}). CR-1 fix muito agressivo — está "
        f"engolindo navegação real. Refinar anti-pattern."
    )
    assert result.confidence >= 0.5
