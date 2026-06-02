"""Job creation disambiguation (Task #1204).

Pure, deterministic module that decides — for a *fresh* recruiter message — which
of the three canonical job-creation paths the LIA should take, and whether the
message is ambiguous enough to warrant asking the recruiter to choose.

The three canonical paths:

  • ``QUICK_CREATE``      — criação rápida/simplificada. The recruiter already
    gave enough detail (or explicitly asked for "rápida"); LIA creates the job
    directly from the message instead of running the full guided wizard.
  • ``GUIDED_WIZARD``     — fluxo conversacional guiado (LangGraph wizard). Safe
    default for a bare "criar vaga" with no detail or an explicit "passo a passo".
  • ``CREATE_AND_SEARCH`` — pedido composto "criar vaga **e** buscar candidatos".
    This is owned by Plan & Execute / agentic loop, **never** by the wizard.

Design notes:

  • Classifier is **rule-based / signal-scoring** (not an LLM call) so the gating
    decision is deterministic and unit-testable, and costs nothing at runtime.
    Confidence + gap are derived from the normalized signal scores, mirroring the
    fast-router philosophy already used across the orchestrator.
  • Gating: a path is only auto-routed when its confidence clears
    ``JOB_CREATION_DISAMBIG_CONFIDENCE_THRESHOLD`` **and** the gap to the runner-up
    clears ``JOB_CREATION_DISAMBIG_GAP_THRESHOLD``. Otherwise LIA asks, presenting
    structured options ("LIA pergunta, recrutador responde").
  • The follow-up free-text reply is classified by :func:`classify_path_choice`,
    mirroring the frontend ``classifyNavConfirmation`` (T-1165) PT-BR philosophy:
    negatives win over positives, explicit path keywords win over bare confirmation.

This module performs **no I/O** and has **no side effects** — all wiring (pending
follow-up store, wizard delegation, Plan & Execute deferral) lives in
``MainOrchestrator._try_wizard_canonical``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from app.orchestrator.action_executor.utils import is_confirmation, is_rejection

__all__ = [
    "JobCreationPath",
    "JobCreationDecision",
    "is_job_creation_message",
    "score_job_creation_paths",
    "decide_job_creation",
    "classify_path_choice",
    "extract_quick_create_params",
]


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


class JobCreationPath(str, Enum):
    QUICK_CREATE = "quick_create"
    GUIDED_WIZARD = "guided_wizard"
    CREATE_AND_SEARCH = "create_and_search"


# ---------------------------------------------------------------------------
# Signal vocabularies (PT-BR canonical)
# ---------------------------------------------------------------------------

# Verbos de criação. Espelha (e amplia) ``_WIZARD_START_PATTERNS`` /
# ``JobCreationDomain.process_intent`` — mantém a mesma fonte de verdade do que
# conta como "intenção de criar vaga".
_CREATE_VERBS: tuple[str, ...] = (
    "criar", "crie", "cria", "criação", "criacao",
    "abrir", "abra", "abre",
    "cadastrar", "cadastra", "cadastre",
    "registrar", "registra",
    "montar", "monta", "monte",
    "nova vaga", "novo cargo", "nova posição", "nova posicao",
    "quero criar", "vamos criar", "preciso criar",
)

_JOB_NOUNS: tuple[str, ...] = (
    "vaga", "vagas", "posição", "posicao", "posições", "posicoes",
    "oportunidade", "requisição", "requisicao", "cargo",
)

# Sinais de contratação que implicam criação de vaga mesmo sem o substantivo.
_HIRE_SIGNALS: tuple[str, ...] = (
    "contratar", "contratação", "contratacao", "preciso contratar",
    "quero contratar", "preciso de alguém", "preciso de alguem",
)

# Caminho rápido — marcadores explícitos.
_QUICK_MARKERS: tuple[str, ...] = (
    "rápida", "rapida", "rápido", "rapido", "rapidinho",
    "simplificada", "simplificado", "simples",
    "direto", "direta", "diretamente",
    "sem wizard", "sem passo a passo", "sem etapas",
    "agora mesmo", "já cria", "ja cria", "cria logo",
)

# Caminho guiado — marcadores explícitos.
_GUIDED_MARKERS: tuple[str, ...] = (
    "passo a passo", "passo-a-passo", "guiado", "guiada",
    "wizard", "com calma", "detalhada", "detalhado", "completa", "completo",
    "me ajuda a criar", "me ajude a criar", "me guie", "me guia",
    "do zero", "não sei por onde", "nao sei por onde", "etapa por etapa",
)

# Caminho composto criar+buscar.
_SEARCH_VERBS: tuple[str, ...] = (
    "buscar", "busca", "busque", "encontrar", "encontre", "procurar",
    "procura", "procure", "achar", "ache", "sourcing", "prospectar",
    "garimpar", "garimpe", "recrutar candidatos",
)

_CANDIDATE_NOUNS: tuple[str, ...] = (
    "candidato", "candidatos", "candidata", "candidatas",
    "talento", "talentos", "profissional", "profissionais",
    "currículo", "curriculo", "currículos", "curriculos", "perfis", "perfil",
)

# Standalone sourcing markers — phrases que implicam busca ativa de candidatos
# mesmo SEM um substantivo de candidato explícito ("iniciar sourcing",
# "prospectar", "busca ativa"). Combinados a uma intenção de criar vaga, marcam
# o pedido como composto (precedência hard → Plan & Execute). Mantidos como
# frases específicas para não capturar "buscar" genérico (ex: "buscar a vaga").
_STANDALONE_SOURCING: tuple[str, ...] = (
    "sourcing", "busca ativa", "busca de candidatos", "buscar candidatos",
    "buscar talentos", "buscar perfis", "buscar profissionais",
    "prospectar", "prospecção", "prospeccao", "garimpar", "garimpo",
    "hunting", "caçar talentos", "cacar talentos", "recrutar candidatos",
    "iniciar a busca", "iniciar busca", "lançar busca", "lancar busca",
    "começar a buscar", "comecar a buscar", "fazer sourcing", "iniciar sourcing",
)

# Senioridade / modelo de trabalho — detalhes que enriquecem o quick path.
_SENIORITY: tuple[str, ...] = (
    "júnior", "junior", "pleno", "plena", "sênior", "senior",
    "estágio", "estagio", "estagiário", "estagiario", "trainee",
    "especialista", "líder", "lider", "principal", "staff",
)

_WORK_MODEL: tuple[str, ...] = (
    "remoto", "remota", "híbrido", "hibrido", "híbrida", "hibrida",
    "presencial", "home office", "home-office",
)

_SALARY_RE = re.compile(
    r"(r\$\s*\d[\d.\s]*|\d+\s*(mil|k)\b|salário|salario|faixa salarial|remuneração|remuneracao)",
    re.IGNORECASE,
)

# Título: captura o que vem depois de "vaga/posição/cargo de/para" ou
# "contratar (um/uma) ...". Best-effort; para no primeiro delimitador.
_TITLE_RE = re.compile(
    r"\b(?:vaga|posição|posicao|cargo|oportunidade)\s+(?:de|para|d[eo])\s+"
    r"(?P<a>[a-zà-ú0-9][\wà-ú\s/.+-]{2,50}?)"
    r"(?=\s+(?:em|na|no|com|que|para|remoto|remota|híbrido|hibrido|presencial|"
    r"júnior|junior|pleno|sênior|senior|estágio|estagio|trainee|e\s)|[,.;!?]|$)",
    re.IGNORECASE,
)
_TITLE_HIRE_RE = re.compile(
    r"\bcontratar\s+(?:um|uma|uns|umas|o|a)?\s*"
    r"(?P<a>[a-zà-ú0-9][\wà-ú\s/.+-]{2,50}?)"
    r"(?=\s+(?:em|na|no|com|que|para|remoto|remota|híbrido|hibrido|presencial|"
    r"júnior|junior|pleno|sênior|senior|estágio|estagio|trainee|e\s)|[,.;!?]|$)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Decision dataclass
# ---------------------------------------------------------------------------


@dataclass
class JobCreationDecision:
    """Outcome of :func:`decide_job_creation`.

    ``action`` is one of:
      • ``"none"``    — message is not a job-creation request.
      • ``"route"``   — confident enough; ``path`` tells the orchestrator where.
      • ``"clarify"`` — ambiguous; present ``clarification_question`` +
        ``clarification_options`` and store a pending follow-up.
    """

    action: str
    path: JobCreationPath | None = None
    confidence: float = 0.0
    gap: float = 0.0
    scores: dict[str, float] = field(default_factory=dict)
    clarification_question: str | None = None
    clarification_options: list[str] = field(default_factory=list)
    option_paths: list[JobCreationPath] = field(default_factory=list)
    extracted_params: dict[str, str] = field(default_factory=dict)
    missing_required: list[str] = field(default_factory=list)
    reason: str = ""


# ---------------------------------------------------------------------------
# Detection + scoring
# ---------------------------------------------------------------------------


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(n in text for n in needles)


def is_job_creation_message(message: str) -> bool:
    """True when the message expresses intent to create a job posting."""
    if not message:
        return False
    text = message.lower()
    has_create = _contains_any(text, _CREATE_VERBS)
    has_noun = _contains_any(text, _JOB_NOUNS)
    has_hire = _contains_any(text, _HIRE_SIGNALS)
    return (has_create and has_noun) or has_hire


def _has_search_intent(text: str) -> bool:
    # Composto é (verbo de busca + substantivo de candidato) OU um marcador de
    # sourcing autônomo ("iniciar sourcing", "prospectar", "busca ativa") que já
    # carrega a semântica de buscar candidatos sem precisar do substantivo. Isso
    # garante a precedência hard mesmo para "criar vaga e iniciar sourcing".
    if _contains_any(text, _STANDALONE_SOURCING):
        return True
    return _contains_any(text, _SEARCH_VERBS) and _contains_any(text, _CANDIDATE_NOUNS)


def score_job_creation_paths(message: str) -> dict[JobCreationPath, float]:
    """Return raw (un-normalized) signal scores per path.

    Both QUICK_CREATE and GUIDED_WIZARD get a base floor of ``1.0`` for any
    job-creation message because a bare "criar vaga" is genuinely viable as
    either — that floor is what makes a detail-less request resolve to *clarify*
    instead of silently picking one path.
    """
    text = message.lower()
    scores: dict[JobCreationPath, float] = {
        JobCreationPath.QUICK_CREATE: 1.0,
        JobCreationPath.GUIDED_WIZARD: 1.0,
        JobCreationPath.CREATE_AND_SEARCH: 0.0,
    }

    # ── Compound create + search (strong, owned by Plan & Execute) ──
    if _has_search_intent(text):
        scores[JobCreationPath.CREATE_AND_SEARCH] += 5.0
        if re.search(r"\be\s+(buscar|busca|encontr|procur|achar|garimp|prospect)", text):
            scores[JobCreationPath.CREATE_AND_SEARCH] += 1.0

    # ── Explicit path markers ──
    if _contains_any(text, _QUICK_MARKERS):
        scores[JobCreationPath.QUICK_CREATE] += 3.0
    if _contains_any(text, _GUIDED_MARKERS):
        scores[JobCreationPath.GUIDED_WIZARD] += 3.0

    # ── Rich-detail signals → lean quick (recruiter already gave specifics) ──
    detail_hits = 0
    if _contains_any(text, _SENIORITY):
        detail_hits += 1
    if _contains_any(text, _WORK_MODEL):
        detail_hits += 1
    if _SALARY_RE.search(text):
        detail_hits += 1
    if _TITLE_RE.search(message) or _TITLE_HIRE_RE.search(message):
        detail_hits += 1

    scores[JobCreationPath.QUICK_CREATE] += float(detail_hits)
    if detail_hits >= 2:
        scores[JobCreationPath.QUICK_CREATE] += 2.0

    return scores


def _confidence_and_gap(scores: dict[JobCreationPath, float]) -> tuple[float, float]:
    total = sum(scores.values()) or 1.0
    ordered = sorted(scores.values(), reverse=True)
    top = ordered[0]
    runner_up = ordered[1] if len(ordered) > 1 else 0.0
    confidence = top / total
    gap = (top - runner_up) / total
    return confidence, gap


# ---------------------------------------------------------------------------
# Param extraction (quick path must respect the recruiter's details)
# ---------------------------------------------------------------------------


def _clean_title(raw: str) -> str:
    title = raw.strip(" .,;:!?-/")
    # Drop trailing connective words that the regex may have grabbed.
    title = re.sub(r"\s+(de|para|com|que|e)$", "", title, flags=re.IGNORECASE).strip()
    return title


def extract_quick_create_params(message: str) -> dict[str, str]:
    """Best-effort extraction of structured params from a free-text request.

    Returns only the keys actually present. ``job_title`` is the only *required*
    field for a direct quick-create; its absence forces a guided fallback.
    """
    if not message:
        return {}
    text = message.lower()
    params: dict[str, str] = {}

    title_match = _TITLE_RE.search(message) or _TITLE_HIRE_RE.search(message)
    if title_match:
        title = _clean_title(title_match.group("a"))
        if len(title) >= 2:
            params["job_title"] = title

    for token in _SENIORITY:
        if token in text:
            params["seniority"] = token
            break

    for token in _WORK_MODEL:
        if token in text:
            params["work_model"] = token
            break

    salary_match = _SALARY_RE.search(message)
    if salary_match:
        params["salary"] = salary_match.group(0).strip()

    return params


# ---------------------------------------------------------------------------
# Top-level decision
# ---------------------------------------------------------------------------

_QUICK_LABEL = "Criação rápida — eu monto a vaga já com o que você descreveu"
_GUIDED_LABEL = "Montar passo a passo — eu te guio em cada etapa"
_SEARCH_LABEL = "Criar a vaga e já buscar candidatos"


def _thresholds() -> tuple[float, float]:
    try:
        from lia_config.config import settings

        return (
            float(getattr(settings, "JOB_CREATION_DISAMBIG_CONFIDENCE_THRESHOLD", 0.70)),
            float(getattr(settings, "JOB_CREATION_DISAMBIG_GAP_THRESHOLD", 0.15)),
        )
    except Exception:
        return (0.70, 0.15)


def decide_job_creation(
    message: str,
    *,
    plan_service_enabled: bool = False,
    confidence_threshold: float | None = None,
    gap_threshold: float | None = None,
) -> JobCreationDecision:
    """Decide the job-creation path for a fresh recruiter message.

    ``plan_service_enabled`` is recorded for telemetry/logging; the precedence
    rule (compound ``create_and_search`` is owned by Plan & Execute, never the
    wizard) is enforced by the caller regardless of the flag.
    """
    if not is_job_creation_message(message):
        return JobCreationDecision(action="none", reason="not_job_creation")

    conf_thr, gap_thr = _thresholds()
    if confidence_threshold is not None:
        conf_thr = confidence_threshold
    if gap_threshold is not None:
        gap_thr = gap_threshold

    scores = score_job_creation_paths(message)
    scores_str = {p.value: round(v, 3) for p, v in scores.items()}

    # ── Hard precedence: compound create + search ──────────────────────────
    # "criar vaga ... e buscar candidatos" is ALWAYS owned by Plan & Execute /
    # agentic, NEVER by the wizard. This is a deterministic precedence rule
    # (not a soft score) so rich job detail can never dilute the compound intent
    # below the confidence gate and accidentally fall into quick/guided/clarify.
    if _has_search_intent(message.lower()):
        return JobCreationDecision(
            action="route",
            path=JobCreationPath.CREATE_AND_SEARCH,
            confidence=1.0,
            gap=1.0,
            scores=scores_str,
            reason="compound_search_precedence",
        )
    confidence, gap = _confidence_and_gap(scores)
    top_path = max(scores, key=lambda p: scores[p])

    confident = confidence >= conf_thr and gap >= gap_thr

    if not confident:
        question = (
            "Posso seguir de algumas formas para criar essa vaga. Como você "
            "prefere? Pode me responder aqui no chat."
        )
        options = [_QUICK_LABEL, _GUIDED_LABEL]
        option_paths = [JobCreationPath.QUICK_CREATE, JobCreationPath.GUIDED_WIZARD]
        if scores[JobCreationPath.CREATE_AND_SEARCH] > 0:
            options.append(_SEARCH_LABEL)
            option_paths.append(JobCreationPath.CREATE_AND_SEARCH)
        return JobCreationDecision(
            action="clarify",
            confidence=round(confidence, 3),
            gap=round(gap, 3),
            scores=scores_str,
            clarification_question=question,
            clarification_options=options,
            option_paths=option_paths,
            extracted_params=extract_quick_create_params(message),
            reason="ambiguous_below_threshold",
        )

    # ── Confident route ──
    decision = JobCreationDecision(
        action="route",
        path=top_path,
        confidence=round(confidence, 3),
        gap=round(gap, 3),
        scores=scores_str,
        reason="confident_route",
    )

    if top_path == JobCreationPath.QUICK_CREATE:
        params = extract_quick_create_params(message)
        decision.extracted_params = params
        if not params.get("job_title"):
            # Never create an empty shell — defer to the guided wizard.
            decision.path = JobCreationPath.GUIDED_WIZARD
            decision.missing_required = ["job_title"]
            decision.reason = "quick_missing_job_title_fallback_guided"

    return decision


# ---------------------------------------------------------------------------
# Follow-up free-text classification ("LIA pergunta, recrutador responde")
# ---------------------------------------------------------------------------

# Mirrors frontend classifyNavConfirmation (T-1165): negatives take precedence,
# explicit path keywords beat a bare confirmation.

_CHOICE_QUICK: tuple[str, ...] = _QUICK_MARKERS + (
    "primeira", "primeiro", "opção 1", "opcao 1", "a 1", "número 1", "numero 1",
)
_CHOICE_GUIDED: tuple[str, ...] = _GUIDED_MARKERS + (
    "segunda", "segundo", "opção 2", "opcao 2", "a 2", "número 2", "numero 2",
    "guiar", "me ajuda", "me ajude",
)
_CHOICE_SEARCH: tuple[str, ...] = (
    "buscar candidatos", "busca candidatos", "buscar", "candidatos",
    "com busca", "e buscar", "terceira", "terceiro", "opção 3", "opcao 3",
    "número 3", "numero 3",
)

# Deferral / cancel markers (mirror frontend classifyNavConfirmation T-1165):
# "depois", "agora não", "deixa pra lá" mean "not now" → cancel the flow. These
# complement ``is_rejection`` (which covers bare negatives like "não").
_CHOICE_CANCEL: tuple[str, ...] = (
    "cancelar", "cancela", "deixa pra lá", "deixa pra la", "deixa quieto",
    "agora não", "agora nao", "depois", "mais tarde", "outra hora",
    "esquece", "esqueça", "não quero", "nao quero", "nenhuma", "nenhum",
)


def classify_path_choice(message: str) -> str | None:
    """Classify the recruiter's free-text reply to the clarification.

    Returns a :class:`JobCreationPath` value, the sentinel ``"cancel"``, or
    ``None`` when the reply is too ambiguous to resolve (caller should re-ask or
    re-run :func:`decide_job_creation` on the new message).
    """
    if not message:
        return None
    text = message.lower().strip()

    # Negatives win (precedence over positives like "pode" in "pode esperar").
    if _contains_any(text, _CHOICE_CANCEL) or is_rejection(text):
        return "cancel"

    if _contains_any(text, _CHOICE_SEARCH):
        return JobCreationPath.CREATE_AND_SEARCH.value
    if _contains_any(text, _CHOICE_QUICK):
        return JobCreationPath.QUICK_CREATE.value
    if _contains_any(text, _CHOICE_GUIDED):
        return JobCreationPath.GUIDED_WIZARD.value

    # Bare confirmation ("sim", "vamos", "pode") → recommended/default path.
    if is_confirmation(text):
        return JobCreationPath.GUIDED_WIZARD.value

    return None
