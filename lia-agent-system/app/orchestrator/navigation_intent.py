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
         ("posição aberta", 0.7), ("requisição", 0.5), ("aprovação de vaga", 1.0),
         ("vagas", 0.3), ("vaga", 0.3)],
        "Vagas",
        "Quer que eu abra a página de Vagas?",
    ),

    # 4. Funil — candidatos e sourcing (action phrases weighted high, generic words low)
    (
        [("buscar candidato", 1.0), ("buscar candidatos", 1.0), ("procurar candidato", 1.0),
         ("sourcing", 0.7), ("banco de talentos", 1.0), ("perfil candidato", 0.7),
         ("score lia", 0.7), ("screening", 0.5), ("triagem", 0.4),
         ("funil", 0.4), ("candidato", 0.2), ("candidatos", 0.2),
         ("talento", 0.2), ("talentos", 0.2), ("cv", 0.3), ("currículo", 0.3)],
        "Funil de Talentos",
        "Quer que eu abra o Funil de Talentos?",
    ),

    # 5. Kanban / pipeline
    (
        [("kanban", 0.7), ("pipeline", 0.5), ("mover candidato", 1.0),
         ("avançar candidato", 1.0), ("mover para etapa", 1.0), ("board", 0.5)],
        "Funil de Talentos",
        "Quer que eu abra o Funil para ver o Kanban?",
    ),

    # 6. Painel de Controle
    (
        [("painel de controle", 1.0), ("dashboard", 0.7), ("tarefas pendentes", 1.0),
         ("atividades", 0.4), ("pendências", 0.5), ("agenda do recrutador", 1.0)],
        "Painel de Controle",
        "Quer que eu abra o Painel de Controle?",
    ),
]

_HAS_STRONG_PHRASE_THRESHOLD = 0.7
_FINAL_CONFIDENCE_MIN = 0.50


class NavigationIntentDetector:
    """Keyword-based navigation intent detector with interrogative dampening."""

    def detect(self, message: str) -> NavigationIntentResult:
        text = message.lower().strip()

        is_question = bool(
            _INTERROGATIVE_PREFIXES.search(text) or _INTERROGATIVE_SUFFIXES.search(text)
        )

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

        if is_question:
            confidence *= 0.45

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
