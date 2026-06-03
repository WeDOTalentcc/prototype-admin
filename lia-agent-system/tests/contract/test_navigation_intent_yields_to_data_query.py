"""Sensor canonical CR-3 (2026-06-03) — NavigationIntentDetector NAO deve
deflectar queries de LEITURA/CONSULTA de dados (resumir, listar, "quais sao
minhas vagas/candidatos"). Essas queries devem ser RESPONDIDAS inline pelo
agente global federado (Opcao A), nao deflectadas com "Posso te levar para
o ambiente de vagas?".

Bug historico (transcript Paulo 2026-06-03):
  User: "resuma minhas vagas"
  -> Detector retorna page='Vagas' confidence=0.84 (deflecta)
  -> Chat oferece navegacao em vez de listar as 101 vagas reais
  User: "voce consegue listar as vagas que tenho na plataforma?"
  -> agente sem ferramenta list_jobs -> confabula "Nenhuma vaga cadastrada"

Principio canonical:
  Verbos de LEITURA de dados (resumir/listar/quais+substantivo) pedem que a
  IA CONSULTE e responda, nao que navegue. O agente global federado tem
  list_jobs/list_candidates. NavigationIntent deve retornar None (sem
  deflexao) para essas queries, deixando o agente responder.

Nao confundir com (CONTINUAM deflectando):
  - Imperativos de navegacao para VER pagina ("ver minhas vagas",
    "mostrar as vagas", "me leva pra vagas") -- BUG-18, navegacao genuina.
  - Criacao de wizard (criar/abrir/publicar vaga) -- CR-2.
  - Analytics (relatorio/funil/metrica) -- CR-1.
"""
import pytest


# Queries de LEITURA de dados -- DEVEM retornar page=None (agente responde)
DATA_QUERY_MUST_NOT_DEFLECT = [
    # Transcript Paulo 2026-06-03
    "resuma minhas vagas",
    "voce consegue listar as vagas que tenho na plataforma?",
    # Resumir
    "resumir minhas vagas",
    "resumo das vagas",
    "resumo das minhas vagas",
    "me resume as vagas",
    # Listar
    "liste minhas vagas",
    "listar as vagas",
    "listar minhas vagas",
    "liste meus candidatos",
    "listar candidatos",
    "liste as vagas ativas",
    # "quais ... vagas/candidatos"
    "quais minhas vagas",
    "quais sao as minhas vagas",
    "quais são as minhas vagas",
    "quais candidatos eu tenho",
    "quais as vagas abertas",
]


# Queries que CONTINUAM deflectando (navegacao genuina / nao-leitura)
NAV_QUERIES_MUST_STILL_DEFLECT = [
    "ver minhas vagas",
    "mostrar as vagas",
    "quero ver as vagas",
    "me leva pra vagas",
    "abra a pagina de vagas",
    "abrir pagina de vagas",
]


@pytest.mark.parametrize("query", DATA_QUERY_MUST_NOT_DEFLECT)
def test_data_query_must_not_deflect(query):
    """CR-3 fix (2026-06-03): queries de leitura/consulta de dados (resumir,
    listar, quais sao minhas vagas/candidatos) NAO podem ser deflectadas pra
    navegacao. O agente global federado deve consultar e responder inline."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is None, (
        f"Query de leitura de dados {query!r} foi deflectada pra page={result.page!r} "
        f"confidence={result.confidence}. CR-3 requer que verbos de leitura "
        f"(resumir/listar/quais+substantivo) suprimam a deflexao -- o agente "
        f"global federado tem list_jobs/list_candidates e deve responder inline."
    )


@pytest.mark.parametrize("query", NAV_QUERIES_MUST_STILL_DEFLECT)
def test_nav_queries_still_deflect_after_cr3(query):
    """Non-regression BUG-18 + CR-2: imperativos de navegacao genuina
    (ver/mostrar pagina, me leva pra) continuam deflectando. CR-3 fix NAO
    pode ser tao agressivo a ponto de engolir navegacao real -- so verbos
    de LEITURA de dados (resumir/listar/quais) vetam a deflexao."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is not None, (
        f"Query de navegacao genuina {query!r} NAO deflectou (page={result.page!r}, "
        f"confidence={result.confidence}). CR-3 fix muito agressivo -- esta "
        f"engolindo navegacao real. Refinar _DATA_READ_KEYWORDS."
    )
    assert result.confidence >= 0.5
