"""
NavigationIntentDetector — Detects which platform page a user message relates to.

Uses keyword/pattern matching (no LLM) for instant classification in the float chat.
Returns page name matching dashboard-app.tsx navigation keys.

Pages: "Vagas" | "Funil de Talentos" | "Painel de Controle" | "Configurações" | "Indicadores" | None

Calibration rules:
- Interrogative phrases (perguntas) reduce confidence — user is asking, not commanding.
- Single generic keyword matches (e.g. just "candidato") are not enough to navigate.
- Multi-word action phrases get higher weight than single generic words.
- Confidence threshold on frontend is 0.75 — only strong signals navigate.
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NavigationIntentResult:
    page: str | None
    confidence: float
    hint: str | None
    matched_pattern: str | None = None


_INTERROGATIVE_PREFIXES = re.compile(
    r"^(você|voce|vc|tu|a lia|a plataforma|o sistema|é possível|e possivel|"
    r"como|será que|sera que|dá para|da para|tem como|posso|consegue|"
    r"existe|há|ha |qual|quais|o que|quando|onde|por que|porque)\b",
    re.IGNORECASE,
)

_INTERROGATIVE_SUFFIXES = re.compile(
    r"\?\s*$",
)

# BUG-18 fix: frases que começam com intenção direta de navegação NÃO devem
# ser tratadas como perguntas, mesmo se terminam com "?". "Me leva pra vagas?"
# é comando educado, não dúvida. Sem esta lista, a confidence era multiplicada
# por 0.45 e caía abaixo do threshold, bloqueando a sugestão de navegação.
_NAV_IMPERATIVE_PREFIXES = re.compile(
    r"^(me\s+(leva|leve|levando|mostra|mostre)|"
    r"abrir?|abra|abre|"
    r"ir\s+para|va\s+para|vai\s+para|vamos\s+para|"
    r"quero\s+(ver|ir|abrir|acessar)|"
    r"mostra|mostre|"
    r"levar?\s+(para|pro|pra)|"
    r"navega[rl]?\s+(para|pro|pra))\b",
    re.IGNORECASE,
)

# CR-1 fix (2026-05-26) — actionable analytics intent veto.
#
# Keywords abaixo indicam que user está pedindo AÇÃO de analytics
# (gerar relatório, análise de funil, métrica, KPI, taxa, velocidade,
# gargalo, comparação, tendência, status). Para essas queries há tool
# real registrada em ``app/orchestrator/action_handlers/analytics_actions.py``
# (gerar_relatorio_kpi, analisar_funil, vagas_sem_candidatos, etc.) que
# deve rodar — NÃO devemos deflectar pra "Posso te levar pro ambiente de
# X". ActionExecutor tem precedência.
#
# Bug histórico: transcript Paulo 2026-05-26 mostrou query
# "faca analise de funil e velocidade de gargalo das vagas ativas"
# sendo deflectada pra page='Vagas' confidence=0.84, em vez de invocar
# get_vacancy_funnel/get_velocity_metrics/get_bottleneck_analysis.
#
# Sensor: tests/contract/test_navigation_intent_yields_to_actionable.py
_ACTIONABLE_ANALYTICS_KEYWORDS = re.compile(
    r"\b("
    # Análise/análise SEGUIDO de contexto analytics (não candidato/CV/currículo
    # — esses são nav legítima pra Funil de Talentos). v2 refined 2026-05-26.
    r"an[áa]li[sc]es?\s+(de|do|da)\s+(funil|gargalo|pipeline|kpi|m[ée]trica|relat[óo]rio|velocidade|status|tend[êe]ncia|convers[ãa]o|performance)|"
    r"an[áa]li[sc]ar\s+(o\s+|a\s+)?(funil|gargalo|pipeline|kpi|m[ée]trica|relat[óo]rio|velocidade|status|tend[êe]ncia|convers[ãa]o|performance)|"
    # Relatório (sempre tool)
    r"relat[óo]rios?|"
    # Velocidade / gargalo (analytics terms)
    r"velocidade|gargalos?|"
    # Métricas / KPI
    r"m[ée]tricas?|kpis?|"
    # Taxa / conversão
    r"taxa\s+de|convers[ãa]o|"
    # Quantitativo (perguntas "quantos X?")
    r"quantos|quantas|quanto|quanta|"
    # Comparação / tendência
    r"compare|comparar|comparativ[oa]|compara[çc][ãa]o|"
    r"tend[êe]ncia|"
    # Status / como está
    r"status\s+(do|da|de)|"
    r"como\s+est[áa]|"
    # Funil-de-query (taxa/status/velocidade de funil)
    r"qual\s+(a|o)\s+(taxa|velocidade|status|funil|convers[ãa]o)|"
    # Vagas sem candidatos (vacancies_without_candidates tool)
    r"sem\s+candidatos"
    r")\b",
    re.IGNORECASE,
)


# CR-2 fix (2026-05-27) -- wizard creation intent veto.
#
# Quando user pede pra CRIAR/INICIAR um wizard (criar vaga, abrir vaga,
# publicar vaga, nova vaga, vamos criar, etc), NAO deflectar pra navegacao.
# O wizard conversacional eh a UX correta -- oferecer "Posso te levar pra
# pagina de Vagas?" em vez de iniciar wizard interrompe o flow e forca
# user a confirmar 2x. Wizard tem precedencia sobre sugestao de navegacao.
#
# Bug historico: teste Paulo 2026-05-27 -- query "vamos criar uma nova
# vaga agora" -> NavigationIntent retornou page="Vagas" -> frontend ofereceu
# "Posso te levar para o ambiente de vagas?" em vez de iniciar wizard.
#
# Sensor: tests/contract/test_navigation_intent_yields_to_wizard.py
_WIZARD_CREATION_KEYWORDS = re.compile(
    r"\b("
    # Verbo de criacao + (qualificador opcional) + vaga/posicao/requisicao.
    # Cobre: "criar vaga", "criar uma vaga", "criar uma nova vaga",
    # "abrir uma nova posicao", "publicar nova vaga", "iniciar wizard de vaga", etc.
    r"(criar|abrir|publicar|iniciar|come[cç]ar|comecar)"
    r"\s+(uma\s+|um\s+)?"
    r"(nova\s+|novo\s+)?"
    r"(vaga|vagas|posi[cç][aã]o|posi[cç][oõ]es|requisi[cç][aã]o|requisi[cç][oõ]es|wizard)"
    r")",
    re.IGNORECASE,
)

_PATTERNS: list[tuple[list[tuple[str, float]], str, str]] = [
    # ([(keyword, weight), ...], page_name, hint_text)
    # weight: 1.0 = strong action phrase, 0.3 = generic/ambiguous word

    # 1. Configurações
    (
        [("configurações", 1.0), ("configuracoes", 1.0), ("política", 0.5), ("politica", 0.5),
         ("políticas", 0.5), ("politicas", 0.5), ("critérios de triagem", 1.0), ("criterios de triagem", 1.0),
         ("regras de recrutamento", 1.0), ("ajustar política", 1.0), ("ajustar criterio", 1.0),
         ("configurar triagem", 1.0), ("parâmetros de seleção", 1.0), ("compliance recrutamento", 1.0)],
        "Configurações",
        "Quer que eu abra Configurações > Políticas de Recrutamento?",
    ),

    # 2. Entrevista / WSI
    (
        [("iniciar entrevista", 1.0), ("entrevista wsi", 1.0), ("wsi", 0.5),
         ("triagem por voz", 1.0), ("assessment", 0.5), ("avaliar candidato", 0.7),
         ("começar entrevista", 1.0), ("realizar entrevista", 1.0), ("fazer entrevista", 1.0)],
        "Funil de Talentos",
        "Quer que eu abra o Funil para iniciar a entrevista WSI?",
    ),

    # 3. Vagas — criação e gestão
    (
        [("criar vaga", 1.0), ("abrir vaga", 1.0), ("publicar vaga", 1.0),
         ("nova vaga", 1.0), ("job description", 0.7), ("headcount", 0.7),
         ("posição aberta", 0.7), ("requisição", 1.0), ("aprovação de vaga", 1.0),
         ("vagas", 0.7), ("vaga", 1.0)],
        "Vagas",
        "Quer que eu abra a página de Vagas?",
    ),

    # 4. Funil — candidatos e sourcing (action phrases weighted high, generic words low)
    (
        [("buscar candidato", 1.0), ("buscar candidatos", 1.0), ("procurar candidato", 1.0),
         ("sourcing", 0.7), ("banco de talentos", 1.0), ("perfil candidato", 0.7),
         ("score lia", 0.7), ("screening", 0.5), ("triagem", 0.4),
         ("funil", 1.0), ("candidato", 1.0), ("candidatos", 1.0),
         ("talento", 0.2), ("talentos", 0.2), ("cv", 1.0), ("currículo", 0.7)],
        "Funil de Talentos",
        "Quer que eu abra o Funil de Talentos?",
    ),

    # 5. Kanban / pipeline
    (
        [("kanban", 0.7), ("pipeline", 0.5), ("mover candidato", 1.0),
         ("avançar candidato", 1.0), ("mover para etapa", 1.0), ("board", 1.0)],
        "Funil de Talentos",
        "Quer que eu abra o Funil para ver o Kanban?",
    ),

    # 6. Painel de Controle
    (
        [("painel de controle", 1.0), ("dashboard", 0.7), ("tarefas pendentes", 1.0),
         ("atividades", 0.4), ("pendências", 1.0), ("agenda do recrutador", 1.0)],
        "Painel de Controle",
        "Quer que eu abra o Painel de Controle?",
    ),
]

_HAS_STRONG_PHRASE_THRESHOLD = 0.7
_FINAL_CONFIDENCE_MIN = 0.50


class NavigationIntentDetector:
    """Keyword-based navigation intent detector with interrogative dampening."""

    def detect(self, message: str) -> NavigationIntentResult:
        logger.debug("[LIA-I06] NavigationIntentDetector still uses internal patterns. Migration to KeywordIntentMatcher pending.")
        text = message.lower().strip()

        # CR-1 fix (2026-05-26) — actionable analytics veto. Quando user
        # pede análise/relatório/métrica/KPI/funil-query, tool real do
        # ActionExecutor tem precedência. NÃO sugerir navegação.
        if _ACTIONABLE_ANALYTICS_KEYWORDS.search(text):
            logger.debug(
                "[NavigationIntent] CR-1 veto: actionable analytics keyword "
                "detected in %r — yielding to ActionExecutor (no deflection)",
                text[:80],
            )
            return NavigationIntentResult(
                page=None, confidence=0.0, hint=None,
                matched_pattern="cr1_actionable_intent_veto",
            )

        # CR-2 fix (2026-05-27) -- wizard creation veto. Quando user pede
        # pra criar/iniciar wizard (criar vaga, nova vaga, publicar vaga,
        # iniciar wizard, etc), o wizard conversacional tem precedencia
        # sobre sugestao de navegacao. NAO deflectar pra pagina de Vagas.
        if _WIZARD_CREATION_KEYWORDS.search(text):
            logger.info(
                "[NavigationIntent] CR-2 veto: wizard creation keyword "
                "detected in %r -- yielding to JobCreationWizard (no deflection)",
                text[:80],
            )
            return NavigationIntentResult(
                page=None, confidence=0.0, hint=None,
                matched_pattern="cr2_wizard_creation_veto",
            )

        # BUG-18: imperativos de navegação ("me leva pra vagas", "abra a página X",
        # "quero ver minhas vagas") NÃO são perguntas, mesmo com "?". Eles devem
        # manter confidence alta e disparar a sugestão de navegação.
        is_nav_imperative = bool(_NAV_IMPERATIVE_PREFIXES.search(text))
        is_question = bool(
            _INTERROGATIVE_PREFIXES.search(text) or _INTERROGATIVE_SUFFIXES.search(text)
        ) and not is_nav_imperative

        best_page: str | None = None
        best_hint: str | None = None
        best_matched: str | None = None
        best_score: float = 0.0
        best_has_strong = False

        for keywords, page, hint in _PATTERNS:
            score: float = 0.0
            matched: str | None = None
            has_strong = False
            for kw, weight in keywords:
                if kw in text:
                    score += weight
                    if weight >= _HAS_STRONG_PHRASE_THRESHOLD:
                        has_strong = True
                    if matched is None or weight > 0.5:
                        matched = kw
            if score > best_score:
                best_score = score
                best_page = page
                best_hint = hint
                best_matched = matched
                best_has_strong = has_strong

        if not best_has_strong and best_score < 0.6:
            return NavigationIntentResult(page=None, confidence=0.0, hint=None)

        confidence = min(0.95, 0.5 + best_score * 0.2)

        # BUG-18: imperativos de navegação ADICIONAM confiança em vez de remover.
        # "me leva pra vagas" é intenção clara, merece prioridade sobre pergunta genérica.
        if is_nav_imperative:
            confidence = min(0.95, confidence + 0.15)
        elif is_question:
            # Reduz confiança de perguntas genéricas ("qual é a página de vagas?"),
            # mas não tanto a ponto de bloquear — antes era 0.45 (muito agressivo).
            confidence *= 0.75

        return NavigationIntentResult(
            page=best_page if confidence >= _FINAL_CONFIDENCE_MIN else None,
            confidence=round(confidence, 3),
            hint=best_hint if confidence >= _FINAL_CONFIDENCE_MIN else None,
            matched_pattern=best_matched,
        )


_detector = NavigationIntentDetector()


def detect_navigation_intent(message: str) -> NavigationIntentResult:
    """Public API — detect navigation intent from user message."""
    return _detector.detect(message)
