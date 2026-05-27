"""Sensor canonical CR-2 (2026-05-27) — NavigationIntentDetector NAO deve
deflectar queries que sao intent de INICIAR WIZARD (criar vaga, nova vaga,
abrir vaga, publicar vaga). Esse sensor pina o fix proposto em
~/Documents/wedotalent_audit_2026-05-26/WIZARD_DEEP_DIVE_2026-05-27_POST_PR18.md.

Bug historico (teste Paulo 2026-05-27):
  User: "vamos criar uma nova vaga agora"
  -> Detector retorna page='Vagas' confidence=0.84 (deflecta "Posso te
     levar para o ambiente de vagas")
  -> Wizard NUNCA inicia, frontend renderiza navegacao em vez de wizard
  -> User responde "sim" ou "agora nao" e perde o flow

Principio canonical:
  Quando user usa palavras-chave de CRIACAO/INICIO de wizard (criar vaga,
  abrir vaga, publicar vaga, nova vaga, iniciar wizard, vamos criar, etc),
  o NavigationIntentDetector deve RETORNAR None (sem deflexao) mesmo se
  patterns de pagina (vagas) tambem batem. Wizard conversacional tem
  precedencia sobre sugestao de navegacao.

Nao confundir com:
  - Imperativos de navegacao para VER pagina ("me leva pra vagas",
    "abra a pagina de vagas", "ver minhas vagas") -- esses CONTINUAM
    deflectando (mantem BUG-18 fix).
  - Analytics queries -- ja cobertos por CR-1.
"""
import pytest


# Queries que pedem CRIAR vaga via wizard -- DEVEM retornar page=None
WIZARD_CREATION_QUERIES_MUST_NOT_DEFLECT = [
    # Transcript Paulo 2026-05-27
    "vamos criar uma nova vaga agora",
    "vamos criar uma nova vaga",
    "vamos criar vaga",
    # Verbos de criacao diretos
    "criar uma nova vaga",
    "criar nova vaga",
    "criar vaga",
    "criar uma vaga",
    "abrir uma nova vaga",
    "abrir nova vaga",
    "abrir vaga",
    "publicar uma vaga",
    "publicar vaga",
    "publicar nova vaga",
    # Acentos e ortografia variada
    "criar posicao",
    "criar posição",
    "abrir requisicao",
    "abrir requisição",
    # Sujeito implicito (quero/preciso/vou)
    "quero criar uma nova vaga",
    "quero criar vaga",
    "preciso criar uma vaga",
    "vou criar uma vaga nova",
    # Iniciar wizard literal
    "iniciar wizard de vaga",
    "iniciar uma nova vaga",
    "comecar uma nova vaga",
    "começar uma nova vaga",
]


# Queries que CONTINUAM deflectando (navegacao genuina, NAO criacao)
# Non-regression BUG-18 + nao quebrar nav legitima pra ver vagas existentes
NAV_QUERIES_MUST_STILL_DEFLECT = [
    "me leva pra vagas",
    "abra a pagina de vagas",
    "abrir pagina de vagas",
    "abrir a pagina de vagas",
    "ver minhas vagas",
    "mostrar as vagas",
    "vamos para a pagina de vagas",
    "quero ver as vagas",
    "vamos para vagas",
    "vamos pra vagas",
]


@pytest.mark.parametrize("query", WIZARD_CREATION_QUERIES_MUST_NOT_DEFLECT)
def test_wizard_creation_queries_must_not_deflect(query):
    """CR-2 fix (2026-05-27): queries com intent de criar vaga/wizard NAO
    podem ser interpretadas como navegacao. O wizard conversacional eh a UX
    correta -- ofertar 'Posso te levar pra pagina de Vagas?' interrompe o
    flow e forca user a confirmar 2x antes de chegar ao wizard."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is None, (
        f"Query de criacao de wizard {query!r} foi deflectada pra page={result.page!r} "
        f"confidence={result.confidence}. CR-2 fix requer que verbos de criacao "
        f"(criar/abrir/publicar/iniciar/comecar) seguidos de vaga/posicao/requisicao "
        f"suprimam a deflexao de navegacao -- wizard tem precedencia."
    )


@pytest.mark.parametrize("query", NAV_QUERIES_MUST_STILL_DEFLECT)
def test_nav_queries_still_deflect_after_cr2(query):
    """Non-regression BUG-18 + CR-1: imperativos de navegacao genuina (ver
    pagina, listar vagas existentes) continuam deflectando normalmente.
    CR-2 fix NAO pode ser tao agressivo a ponto de bloquear navegacao legitima."""
    from app.orchestrator.context.navigation_intent import detect_navigation_intent
    result = detect_navigation_intent(query)
    assert result.page is not None, (
        f"Query de navegacao genuina {query!r} NAO deflectou (page={result.page!r}, "
        f"confidence={result.confidence}). CR-2 fix muito agressivo -- esta "
        f"engolindo navegacao real. Refinar anti-pattern em _WIZARD_CREATION_KEYWORDS."
    )
    assert result.confidence >= 0.5
