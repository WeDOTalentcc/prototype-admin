"""
NavigationIntentDetector — Detects which platform page a user message relates to.

Uses keyword/pattern matching (no LLM) for instant classification in the float chat.
Returns page name matching dashboard-app.tsx navigation keys.

Pages: "Vagas" | "Funil de Talentos" | "Painel de Controle" | "Configurações" | "Indicadores" | None
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NavigationIntentResult:
    page: str | None          # matches dashboard-app currentPage values
    confidence: float            # 0.0–1.0
    hint: str | None          # Suggested text: "Quer ver na página de Vagas?"
    matched_pattern: str | None = None


# Pattern groups → page mapping
# ORDENAÇÃO IMPORTANTE: padrões mais específicos devem vir antes dos genéricos.
# Em empate de score, o primeiro padrão da lista vence.
_PATTERNS: list[tuple[list[str], str, str]] = [
    # (keywords, page_name, hint_text)

    # 1. Configurações — antes de Funil para evitar ambiguidade com "triagem"
    (
        ["configurações", "configuracoes", "política", "politica",
         "políticas", "politicas", "critérios de triagem", "criterios de triagem",
         "regras de recrutamento", "ajustar política", "ajustar criterio",
         "configurar triagem", "parâmetros de seleção", "compliance recrutamento"],
        "Configurações",
        "Quer que eu abra Configurações > Políticas de Recrutamento?",
    ),

    # 2. Indicadores — ARQUIVADO: página desativada temporariamente
    # (
    #     ["indicadores", "relatório", "relatorio", "relatórios", "relatorios",
    #      "métricas", "metricas", "kpi", "time to hire", "taxa de conversão",
    #      "taxa de conversao", "funil de conversão", "performance recrutamento",
    #      "análise de vagas", "analise de vagas", "dashboard de métricas",
    #      "relatório de vagas", "relatorio de vagas", "relatório de vaga",
    #      "análise de recrutamento", "analise de recrutamento"],
    #     "Indicadores",
    #     "Quer que eu abra a página de Indicadores?",
    # ),

    # 3. Entrevista / WSI — antes do Funil geral para dar hint específico
    (
        ["entrevistar", "iniciar entrevista", "entrevista wsi", "wsi",
         "triagem por voz", "assessment", "avaliar candidato",
         "começar entrevista", "realizar entrevista", "fazer entrevista"],
        "Funil de Talentos",
        "Quer que eu abra o Funil para iniciar a entrevista WSI?",
    ),

    # 4. Vagas — criação e gestão de vagas
    (
        ["vaga", "vagas", "criar vaga", "abrir vaga", "publicar vaga",
         "job description", "jd ", "headcount", "posição aberta",
         "requisição", "aprovação de vaga"],
        "Vagas",
        "Quer que eu abra a página de Vagas?",
    ),

    # 5. Funil — candidatos e sourcing
    (
        ["candidato", "candidatos", "funil", "talento", "talentos",
         "triagem", "cv", "currículo", "screening", "sourcing",
         "banco de talentos", "perfil candidato", "score lia"],
        "Funil de Talentos",
        "Quer que eu abra o Funil de Talentos?",
    ),

    # 6. Kanban / pipeline
    (
        ["kanban", "pipeline", "etapa", "mover candidato",
         "avançar candidato", "coluna", "board"],
        "Funil de Talentos",
        "Quer que eu abra o Funil para ver o Kanban?",
    ),

    # 7. Painel de Controle
    (
        ["painel", "dashboard", "tarefas", "atividades", "pendências",
         "agenda do recrutador"],
        "Painel de Controle",
        "Quer que eu abra o Painel de Controle?",
    ),
]


class NavigationIntentDetector:
    """Keyword-based navigation intent detector."""

    def detect(self, message: str) -> NavigationIntentResult:
        text = message.lower().strip()

        best_page: str | None = None
        best_hint: str | None = None
        best_matched: str | None = None
        best_score = 0

        for keywords, page, hint in _PATTERNS:
            score = 0
            matched = None
            for kw in keywords:
                if kw in text:
                    score += 1
                    if matched is None:
                        matched = kw
            if score > best_score:
                best_score = score
                best_page = page
                best_hint = hint
                best_matched = matched

        if best_score == 0:
            return NavigationIntentResult(page=None, confidence=0.0, hint=None)

        confidence = min(0.95, 0.6 + best_score * 0.1)
        return NavigationIntentResult(
            page=best_page,
            confidence=confidence,
            hint=best_hint,
            matched_pattern=best_matched,
        )


# Singleton
_detector = NavigationIntentDetector()


def detect_navigation_intent(message: str) -> NavigationIntentResult:
    """Public API — detect navigation intent from user message."""
    return _detector.detect(message)
