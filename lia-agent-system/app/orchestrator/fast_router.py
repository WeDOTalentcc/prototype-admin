"""
Fast Router - Keyword and regex-based domain routing.

Resolves ~80% of user queries without LLM calls using pattern matching.
Part of the CascadedRouter pipeline: memory → fast → LLM fallback.
"""
import re
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FastRouteResult:
    domain_id: str
    confidence: float
    matched_pattern: str
    matched_text: str


DOMAIN_PATTERNS: Dict[str, List[str]] = {
    "job_management": [
        r"criar?\s+\w*\s*vaga",
        r"nova\s+vaga",
        r"editar?\s+\w*\s*vaga",
        r"atualizar?\s+\w*\s*vaga",
        r"gerar?\s+jd",
        r"job\s+description",
        r"descri[çc][ãa]o\s+d[aeo]\s+vaga",
        r"wizard",
        r"requisitos\s+d[aeo]",
        r"clonar?\s+\w*\s*vaga",
        r"fechar?\s+\w*\s*vaga",
        r"publicar?\s+\w*\s*vaga",
        r"pausar?\s+\w*\s*vaga",
        r"template\s+d[aeo]\s+vaga",
        r"\bvaga\b",
        r"compet[eê]ncias",
        r"sal[áa]rio",
        r"benef[ií]cios",
        r"enrichment",
    ],
    "sourcing": [
        r"buscar?\s+\w*\s*candidato",
        r"pesquisar?\s+\w*\s*candidato",
        r"encontrar?\s+\w*\s*candidato",
        r"pearch",
        r"boolean\s+search",
        r"busca\s+booleana",
        r"string\s+booleana",
        r"talent\s+pool",
        r"sourcing",
        r"atrair?\s+\w*\s*candidato",
        r"ranking\s+d[eo]",
        r"top\s+\d+\s+candidato",
        r"filtrar?\s+\w*\s*candidato",
    ],
    "cv_screening": [
        r"triagem",
        r"analisar?\s+\w*\s*cv",
        r"analisar?\s+\w*\s*curr[ií]culo",
        r"red\s*flags?",
        r"screening",
        r"parsear?\s+cv",
        r"extrair?\s+dados?\s+d[eo]?\s*cv",
        r"avaliar?\s+\w*\s*curr[ií]culo",
        r"pontua[çc][ãa]o\s+d[eo]\s+cv",
    ],
    "wsi_assessment": [
        r"score\s+wsi",
        r"avaliar?\s+\w*\s*candidato",
        r"avalia[çc][ãa]o\s+wsi",
        r"\bwsi\b",
        r"\bbloom\b",
        r"\bdreyfus\b",
        r"big\s*five",
        r"compet[eê]ncia\s+comportamental",
        r"eligibilidade",
        r"calibra[çc][ãa]o",
        r"senioridade",
        r"perguntas?\s+wsi",
        r"question[áa]rio",
    ],
    "interviewing": [
        r"entrevistar?",
        r"entrevista\b",
        r"transcrever?\s+\w*\s*entrevista",
        r"openmic",
        r"voice\s+interview",
        r"gravar?\s+\w*\s*entrevista",
        r"iniciar?\s+\w*\s*entrevista",
    ],
    "scheduling": [
        r"agendar?\s+\w*\s*entrevista",
        r"reagendar?\s+\w*\s*entrevista",
        r"cancelar?\s+\w*\s*entrevista",
        r"hor[áa]rio\s+dispon[ií]vel",
        r"marcar?\s+\w*\s*entrevista",
        r"agendar?\s+\w*\s*reuni[ãa]o",
        r"calend[áa]rio",
        r"disponibilidade\s+de\s+hor[áa]rio",
        r"agendar?\b",
        r"reagendar?\b",
    ],
    "communication": [
        r"enviar?\s+\w*\s*email",
        r"enviar?\s+\w*\s*whatsapp",
        r"enviar?\s+\w*\s*mensagem",
        r"template\s+d[aeo]\s+email",
        r"notifica[çc][ãa]o",
        r"comunicar?\s+\w*\s*candidato",
        r"feedback\s+para?\s+\w*\s*candidato",
        r"\bteams\b",
    ],
    # Z1-01: Kanban subagents
    "kanban_search": [
        r"\bver\s+\w*\s*candidato",          # \b evita casar dentro de "mover"
        r"\blistar?\s+\w*\s*candidato",
        r"\bmostrar?\s+\w*\s*candidato",
        r"quem\s+est[áa]\s+em",
        r"candidatos?\s+na\s+etapa",
        r"resumo\s+d[eo]\s+pipeline",
        r"m[ée]tricas?\s+da\s+etapa",
        r"benchmarks?\s+d[eo]\s+pipeline",
        r"velocidade\s+d[eo]\s+pipeline",
        r"pipeline_velocity",
        r"\bkanban\b",
        r"etapa\s+d[eo]",
        r"funil\s+de\s+recrutamento",       # mais específico que "funil" simples
    ],
    "kanban_insight": [
        r"gargalo[s]?\s+d[eo]\s+pipeline",  # plural+específico
        r"gargalo[s]?\b",                    # singular e plural
        r"bottleneck[s]?",
        r"previs[ãa]o\s+de\s+fechamento",   # específico — evita falso positivo "to do"
        r"previs[ãa]o\s+d[eo]\s+pipeline",
        r"candidatos?\s+em\s+risco",
        r"\bat.?risk\b",
        r"aging\s+d[eo]\s+candidato",
        r"tempo\s+na\s+etapa",
        r"analisar?\s+etapa",
        r"comparar?\s+etapas?",
        r"sugerir?\s+movimenta[çc][ãa]o",
        r"jornada\s+d[eo]\s+candidato",
        r"pipeline.?prediction",
        r"an[áa]lise\s+d[eo]\s+funil",
        r"identify.?bottleneck",
    ],
    "kanban_action": [
        r"mover?\s+\w*\s*candidato",
        r"mover?\s+em\s+lote",
        r"aprovar?\s+\w*\s*candidato",
        r"rejeitar?\s+\w*\s*candidato",
        r"reprovar?\s+\w*\s*candidato",
        r"triagem\s+em\s+lote",
        r"triagem\s+batch",
        r"comunicac[ao][ãa]o\s+em\s+massa",
        r"mensagem\s+em\s+massa",
        r"relat[óo]rio\s+d[eo]\s+pipeline",
        r"prata\s+da\s+casa",
        r"silver\s+medalist",
        r"backlog\s+d[eo]\s+recrutador",
        r"benchmark\s+d[eo]\s+recrutador",
        r"compara[çc][ãa]o\s+d[eo]\s+candidato",
    ],
    # Z1-02: Pipeline subagents
    "pipeline_context": [
        r"perfil\s+d[eo]\s+candidato",
        r"scores?\s+wsi",
        r"resultado\s+da\s+triagem",
        r"sal[áa]rio\s+d[eo]\s+candidato",
        r"disponibilidade\s+d[eo]\s+candidato",
        r"contexto\s+da\s+vaga",
        r"sub.?status\s+dispon",
        r"get_candidate_profile",
        r"get_candidate_wsi",
    ],
    "pipeline_decision": [
        r"validar?\s+transi[çc][ãa]o",
        r"sub.?status\s+suger",
        r"prefer[eê]ncias?\s+d[eo]\s+recrutador",
        r"coletar?\s+dados?\s+d[eo]\s+candidato",
        r"agendar?\s+tarefa\s+secund[áa]ria",
        r"validate.?transition",
        r"suggest.?sub.?status",
        r"recruiter.?preference",
    ],
    "pipeline_action": [
        r"atualizar?\s+\w*\s*candidato",
        r"personalizar?\s+comunica[çc][ãa]o",
        r"cancelar?\s+\w*\s*entrevista",
        r"reagendar?\s+\w*\s*entrevista",
        r"detalhes?\s+da\s+entrevista",
        r"update.?candidate.?field",
        r"personalize.?communication",
        r"reschedule.?interview",
        r"cancel.?interview",
    ],
    "analytics": [
        r"gerar?\s+relat[óo]rio",
        r"relat[óo]rio\b",
        r"dashboard",
        r"kpi",
        r"m[ée]trica",
        r"estat[ií]stica",
        r"an[áa]lise\s+d[aeo]",
        r"exportar?\s+\w*\s*candidato",
        r"exportar?\s+\w*\s*dados",
        r"report",
    ],
    "ats_integration": [
        r"sync\s+ats",
        r"sincronizar?\s+\w*\s*ats",
        r"\bgupy\b",
        r"pandap[eé]",
        r"merge\s+ats",
        r"importar?\s+d[eo]\s+ats",
        r"integra[çc][ãa]o\s+ats",
    ],
    "recruiter_assistant": [
        r"briefing",
        r"meu\s+dia",
        r"resumo\s+d[eo]\s+dia",
        r"sugest[ãõ]es?\s+proativa",
        r"assist[eê]ncia",
        r"\bajuda\b",
    ],
    "task_planning": [
        r"tarefa",
        r"planejar?\s+tarefa",
        r"delegar?\s+tarefa",
        r"criar?\s+tarefa",
        r"to[\s-]?do",
        r"lista\s+de?\s+tarefas",
        r"pr[óo]ximos?\s+passos?",
    ],
}

_DOMAIN_ID_NORMALIZE: Dict[str, str] = {
    "wsi_assessment": "cv_screening",
    "interviewing": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "task_planning": "automation",
    # Z1: subagentes kanban/pipeline passam sem normalização
}


def normalize_domain_id(domain_id: str) -> str:
    """Normalize legacy/pattern domain IDs to canonical domain IDs."""
    return _DOMAIN_ID_NORMALIZE.get(domain_id, domain_id)


_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {}


def _ensure_compiled() -> None:
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        for domain_id, patterns in DOMAIN_PATTERNS.items():
            _COMPILED_PATTERNS[domain_id] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns
            ]
        logger.info(f"FastRouter compiled {sum(len(v) for v in _COMPILED_PATTERNS.values())} patterns for {len(_COMPILED_PATTERNS)} domains")


class FastRouter:
    def __init__(self):
        _ensure_compiled()

    def match(self, message: str) -> Optional[FastRouteResult]:
        message_lower = message.lower().strip()
        if not message_lower:
            return None

        all_matches: List[FastRouteResult] = []

        for domain_id, patterns in _COMPILED_PATTERNS.items():
            best_for_domain: Optional[FastRouteResult] = None
            best_specificity = 0
            for pattern in patterns:
                m = pattern.search(message_lower)
                if m:
                    specificity = len(m.group())
                    if specificity > best_specificity:
                        best_specificity = specificity
                        best_for_domain = FastRouteResult(
                            domain_id=normalize_domain_id(domain_id),
                            confidence=min(0.95, 0.7 + specificity * 0.02),
                            matched_pattern=pattern.pattern,
                            matched_text=m.group(),
                        )
            if best_for_domain:
                all_matches.append(best_for_domain)

        if not all_matches:
            return None

        all_matches.sort(key=lambda r: r.confidence, reverse=True)
        best_match = all_matches[0]

        if len(all_matches) >= 2:
            confidence_gap = best_match.confidence - all_matches[1].confidence
            if confidence_gap < 0.1:
                ambiguous_domains = [m.domain_id for m in all_matches[:3]]
                logger.warning(
                    f"FastRouter ambiguity detected for '{message[:60]}...': "
                    f"domains={ambiguous_domains}, gap={confidence_gap:.2f}. "
                    f"Applying penalty."
                )
                best_match.confidence = max(0.3, best_match.confidence - 0.15)

        logger.debug(
            f"FastRouter matched '{message[:50]}...' → {best_match.domain_id} "
            f"(conf={best_match.confidence:.2f}, candidates={len(all_matches)})"
        )
        return best_match

    def match_all(self, message: str) -> List[FastRouteResult]:
        message_lower = message.lower().strip()
        if not message_lower:
            return []

        results = []
        for domain_id, patterns in _COMPILED_PATTERNS.items():
            for pattern in patterns:
                m = pattern.search(message_lower)
                if m:
                    results.append(FastRouteResult(
                        domain_id=normalize_domain_id(domain_id),
                        confidence=min(0.95, 0.7 + len(m.group()) * 0.02),
                        matched_pattern=pattern.pattern,
                        matched_text=m.group(),
                    ))
                    break
        return sorted(results, key=lambda r: r.confidence, reverse=True)

    def get_patterns_for_domain(self, domain_id: str) -> List[str]:
        return DOMAIN_PATTERNS.get(domain_id, [])

    def get_all_domains(self) -> List[str]:
        return list(DOMAIN_PATTERNS.keys())
