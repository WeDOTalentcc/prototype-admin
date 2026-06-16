"""
Fast Router - Keyword and regex-based domain routing.

Resolves ~80% of user queries without LLM calls using pattern matching.
Part of the CascadedRouter pipeline: memory → fast → LLM fallback.
"""
import logging
import math
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LIA-I05: Build a shadow KeywordIntentMatcher from DOMAIN_PATTERNS
# for telemetry.  Runs alongside the regex to surface migration signals.
# ---------------------------------------------------------------------------
_DOMAIN_MATCHER = None


def _get_domain_matcher():
    global _DOMAIN_MATCHER
    if _DOMAIN_MATCHER is not None:
        return _DOMAIN_MATCHER
    try:
        from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
        import re as _re
        keywords_map: dict[str, str] = {}
        for domain_id, patterns in DOMAIN_PATTERNS.items():
            for pattern_str in patterns:
                # Convert regex to literal keyword (best-effort)
                literal = _re.sub(r"[\^\$\(\)\[\]\?\*\+\\\|\{\}]", "", pattern_str).strip()
                literal = _re.sub(r"\\b", "", literal)
                literal = _re.sub(r"\s\+", " ", literal)
                literal = _re.sub(r"\s+", " ", literal)
                if literal and len(literal) > 2:
                    keywords_map[literal.lower()] = domain_id
        _DOMAIN_MATCHER = KeywordIntentMatcher.from_keyword_map(
            keywords_map, domain_id="fast_router"
        )
        return _DOMAIN_MATCHER
    except Exception:
        # T-04 Tipo B: matcher build failure must be visible — routing
        # falls back to slower tiers (cascaded router), which is correct
        # behavior, but operators need to know the keyword map is broken.
        logger.warning(
            "[fast_router] _build_domain_matcher failed, returning None (fallback to slower tiers)",
            exc_info=True,
        )
        return None


@dataclass
class FastRouteResult:
    domain_id: str
    confidence: float
    matched_pattern: str
    matched_text: str


_HARDCODED_DOMAIN_PATTERNS: dict[str, list[str]] = {
    "wizard": [
        r"\bwizard\b",
        r"job\s+creation\s+wizard",
        # Frente 1 (unificacao wizard 2026-05-29) — intencao de CRIACAO de vaga.
        # Espelhado em app/orchestrator/config/domain_routing.yaml (YAML primario).
        r"criar.*\bvaga\b",
        # Neg lookahead exclui quando ha codigo de vaga (v0003, v0014 etc)
        r"abrir.*\bvaga\b(?!.*\b[vV]\d{3})",
        r"cadastr\w*.*\bvaga\b",
        r"registrar.*\bvaga\b",
        r"\bnova\s+vaga\b",
        r"\bnova\s+oportunidade\b",
        r"(criar|abrir).*posi[çc][ãa]o",
        r"(preciso|quero|vou|gostaria)\b.{0,15}contratar",
    ],
    "job_management": [
        r"editar?\s+\w*\s*vaga",
        r"atualizar?\s+\w*\s*vaga",
        r"gerar?\s+jd",
        r"job\s+description",
        r"descri[çc][ãa]o\s+d[aeo]\s+vaga",
        r"requisitos\s+d[aeo]",
        r"clonar?\s+\w*\s*vaga",
        r"fechar?\s+\w*\s*vaga",
        r"publicar?\s+\w*\s*vaga",
        r"pausar?\s+\w*\s*vaga",
        r"template\s+d[aeo]\s+vaga",
        r"\bvagas?\b",
        r"filtr\w*\s+\w*\s*vagas?",
        r"\bvagas?\b.*\bativ\w*|\bativ\w*.*\bvagas?\b",
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
    # Z2-02: subagentes Sourcing
    "sourcing_planner": [
        r"crit[eé]rios\s+de\s+busca",
        r"definir?\s+\w*\s*crit[eé]rios",
        r"par[aâ]metros\s+de\s+busca",
        r"configurar?\s+\w*\s*busca",
        r"sugerir?\s+\w*\s*skills?",
        r"sugest[aã]o\s+de\s+skills?",
    ],
    "sourcing_search": [
        r"busca\s+de\s+talentos",
        r"talent\s+search",
        r"ver\s+perfil\s+d[eo]\s+candidato",
        r"exibir?\s+\w*\s*candidatos?",
        r"listar?\s+candidatos?\s+encontrados?",
    ],
    "sourcing_enrich": [
        r"analisar?\s+\w*\s*perfil",
        r"comparar?\s+\w*\s*candidatos?",
        r"score\s+d[eo]\s+candidato",
        r"\bshortlist\b",
        r"adicionar?\s+\w*\s*shortlist",
        r"ranking\s+d[eo]\s+candidatos?",
        r"avaliar?\s+\w*\s*perfil",
    ],
    "sourcing_engagement": [
        r"abordagem\s+d[eo]\s+candidato",
        r"enviar?\s+\w*\s*abordagem",
        r"mensagem\s+de\s+abordagem",
        r"contatar?\s+\w*\s*candidato",
        r"rastrear?\s+\w*\s*resposta",
        r"\boutreach\b",
        r"gerar?\s+\w*\s*mensagem\s+d[eo]\s+contato",
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
        r"voice\s+screening",
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
        r"atualiza\s+o?\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|sal[aá]rio|modelo\s+de\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)",
        r"atualizar?\s+campo",
        r"muda\s+o?\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|sal[aá]rio|modelo\s+de\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)",
        r"troca\s+o?\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|sal[aá]rio|modelo\s+de\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)",
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
        r"resumo\s+di[aá]rio",
        r"sum[aá]rio\s+d[eo]\s+dia",
        r"minha\s+agenda",
        r"agenda\s+de\s+hoje",
        r"agenda\s+de\s+amanhã",
        r"agenda\s+dessa?\s+semana",
        r"compromissos?\s+de\s+hoje",
        r"compromissos?\s+de\s+amanhã",
        r"entrevistas?\s+de\s+hoje",
        r"entrevistas?\s+de\s+amanhã",
        r"o\s+que\s+tenho\s+hoje",
        r"o\s+que\s+tenho\s+amanhã",
        r"o\s+que\s+preciso\s+fazer\s+hoje",
        r"tarefas?\s+de\s+hoje",
        r"tarefas?\s+pendentes?",
        r"sugest[ãõ]es?\s+proativa",
        r"assist[eê]ncia",
        r"\bajuda\b",
        r"como\s+funciona",
        r"o\s+que\s+[eé]\s+o?\s+m[oó]dulo",
        r"explica\s+o\s+m[oó]dulo",
        r"para\s+que\s+serve",
        r"como\s+us[ao]",
        r"me\s+explica",
        r"o\s+que\s+[eé]\s+[ao]?\s*\blia\b",
        r"help\b",
    ],
    "task_planning": [
        r"tarefa",
        r"planejar?\s+tarefa",
        r"delegar?\s+tarefa",
        r"criar?\s+tarefa",
        r"to[\s-]?do",
        r"lista\s+de?\s+tarefas",
        r"pr[óo]ximos?\s+passos?",
        r"lembrete",
        r"me\s+lembra",
        r"me\s+avisa",
        r"cria\s+um\s+lembrete",
        r"criar?\s+lembrete",
        r"anot[ao]",
        r"criar?\s+nota",
        r"salva\s+uma?\s+nota",
        r"nota\s+sobre",
    ],
    "interview_scheduling": [
        r"criar?\s+compromisso",
        r"novo\s+compromisso",
        r"agendar?\s+reuni[aã]o",
        r"agendar?\s+call",
        r"agendar?\s+alinhamento",
        r"criar?\s+evento",
        r"compromisso\s+no\s+calend[aá]rio",
        r"reuni[aã]o\s+no\s+calend[aá]rio",
    ],

    # --- Phase 6 domains ---
    "talent_pool": [
        r"talent\s+pool", r"pool\s+de\s+talentos?", r"banco\s+de\s+talentos?",
        r"banco\s+vivo", r"bancos?\s+vivos?", r"criar\s+\w*\s*pool",
        r"mover\s+\w*\s*pool\s+\w*\s*vaga", r"candidatos?\s+do\s+pool",
    ],
    "agent_studio": [
        r"agent\s+studio", r"studio\s+de\s+agentes?", r"criar\s+\w*\s*agente",
        r"novo\s+agente", r"ativar\s+\w*\s*agente", r"calibra[rç]",
        r"recalibra[rç]", r"busca\s+inteligente", r"multi.?estrat[eé]gia",
        r"4\s+estrat[eé]gias?", r"templates?\s+setor",
    ],
    "digital_twin": [
        r"digital\s+twin", r"g[eê]meo\s+digital", r"twin\s+\w*\s*especialista",
        r"avaliar?\s+com\s+twin", r"segunda\s+opini[aã]o",
        r"clon[ae]r?\s+\w*\s*racioc[ií]nio", r"criar\s+\w*\s*twin",
    ],
    "recruitment_campaign": [
        r"campanha\s+\w*\s*recrutamento", r"criar\s+\w*\s*campanha",
        r"nova\s+campanha", r"fluxo\s+completo", r"avan[cç]ar\s+\w*\s*campanha",
        r"progresso\s+\w*\s*campanha", r"workflow\s+rail",
    ],

    # A2 (PR5 / Task #1005) — fallback para a tag estruturada do chat
    # lateral de Configurações. Espelha a entrada `company_settings` no
    # YAML (`domain_routing.yaml`); usado se YAML estiver indisponível
    # (LIA_DISABLE_YAML_ROUTING=1 ou arquivo ausente).
    "company_settings": [
        r"\[action:prefill_section\]\[target_section:[a-z_]+\]",
    ],

}


# LIA-I06 (Wave 3 / Fase 5): Load DOMAIN_PATTERNS from YAML with hardcoded fallback.
# Config path: app/orchestrator/config/domain_routing.yaml
# If YAML is missing/malformed, falls back to _HARDCODED_DOMAIN_PATTERNS above.
# This is config-as-data: edit YAML + restart worker, no code deploy needed.
def _load_domain_patterns() -> dict[str, list[str]]:
    import os as _os
    import yaml as _yaml
    import pathlib as _pathlib

    # Resolve YAML path relative to this file (works in any deployment layout).
    # __file__ = app/orchestrator/routing/fast_router.py
    # .parent = app/orchestrator/routing/ ; .parent.parent = app/orchestrator/
    # YAML canonical vive em app/orchestrator/config/domain_routing.yaml.
    # FIX 2026-05-29 (audit unificacao wizard): o path anterior apontava para
    # routing/config/ (INEXISTENTE), fazendo TODO o domain_routing.yaml cair no
    # fallback hardcoded silenciosamente (logger.warning "YAML not found"). 3 dominios
    # degradados: company_settings(+18p), job_management(+10p listagem), wizard(+1p).
    # Sensor: tests/unit/orchestrator/test_domain_routing_yaml_loads.py
    _yaml_path = _pathlib.Path(__file__).parent.parent / "config" / "domain_routing.yaml"

    if _os.environ.get("LIA_DISABLE_YAML_ROUTING", "").lower() in ("1", "true", "yes"):  # R-044: verified-active — disables YAML domain routing, falls back to hardcoded DOMAIN_PATTERNS
        # W3-022 (2026-05-23): canary warning — fallback ativo sinaliza candidato
        # pra deleção quando YAML domain_routing.yaml estiver estável em prod.
        # Em prod, este path é EXCEPCIONAL (rollback emergencial); em dev/test
        # é warn-only.
        _env = _os.environ.get("APP_ENV", "development")
        if _env in ("production", "prod", "staging"):
            logger.warning(
                "[W3-022 CANARY] LIA_DISABLE_YAML_ROUTING=1 em %s · "
                "YAML routing bypassed, hardcoded fallback ativo. "
                "Investigar OR fechar W3-022 cleanup.",
                _env,
            )
        else:
            logger.info("[LIA-I06] LIA_DISABLE_YAML_ROUTING set — using hardcoded DOMAIN_PATTERNS")
        return _HARDCODED_DOMAIN_PATTERNS

    try:
        with open(_yaml_path, "r", encoding="utf-8") as f:
            data = _yaml.safe_load(f)
        loaded = data.get("domains", {})
        if not loaded or not isinstance(loaded, dict):
            logger.warning("[LIA-I06] YAML %s has empty/invalid 'domains' — using hardcoded", _yaml_path)
            return _HARDCODED_DOMAIN_PATTERNS

        # Validate each value is a list of strings
        validated: dict[str, list[str]] = {}
        for domain_id, patterns in loaded.items():
            if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
                logger.warning("[LIA-I06] Skipping malformed domain '%s' in YAML", domain_id)
                continue
            validated[str(domain_id)] = list(patterns)

        if not validated:
            logger.warning("[LIA-I06] No valid domain in YAML — using hardcoded")
            return _HARDCODED_DOMAIN_PATTERNS

        logger.info(
            "[LIA-I06] Loaded %d domains (%d total patterns) from %s",
            len(validated), sum(len(p) for p in validated.values()), _yaml_path,
        )
        return validated
    except FileNotFoundError:
        logger.warning("[LIA-I06] YAML %s not found — using hardcoded DOMAIN_PATTERNS", _yaml_path)
        return _HARDCODED_DOMAIN_PATTERNS
    except Exception as exc:
        logger.error("[LIA-I06] YAML load failed: %s — using hardcoded DOMAIN_PATTERNS", exc)
        return _HARDCODED_DOMAIN_PATTERNS


DOMAIN_PATTERNS: dict[str, list[str]] = _load_domain_patterns()

_DOMAIN_ID_NORMALIZE: dict[str, str] = {
    "wsi_assessment": "cv_screening",
    "interviewing": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "task_planning": "automation",
    # Z1: subagentes kanban/pipeline passam sem normalização
}


def normalize_domain_id(domain_id: str) -> str:
    """Normalize legacy/pattern domain IDs to canonical domain IDs."""
    return _DOMAIN_ID_NORMALIZE.get(domain_id, domain_id)


_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {}


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

    # ------------------------------------------------------------------
    # P06: Deduplication helper
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_matches(
        matches: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """Deduplicate ambiguous domain matches by confidence bucket.

        Groups matches into 0.05-width confidence buckets.  Within the
        highest-confidence bucket, keeps only the single match whose
        ``matched_pattern`` string is longest (most specific).  All matches
        from lower buckets are preserved unchanged.

        Args:
            matches: List of ``(domain_id, confidence)`` tuples, where
                     ``domain_id`` may carry the matched_pattern appended
                     as ``"domain|pattern"`` for tiebreaking.  If no pipe
                     separator is present the domain_id itself is used as
                     the tiebreaker string.

        Returns:
            Deduplicated list sorted by confidence descending.

        Note:
            Callers should pass tuples enriched with pattern info using the
            ``"domain|pattern"`` convention so that specificity tiebreaking
            works correctly.  The returned tuples always expose only the
            ``domain_id`` part (before the pipe).
        """
        if not matches:
            return []

        # Bucket floor: round confidence DOWN to nearest 0.05
        def _bucket(conf: float) -> float:
            return math.floor(conf / 0.05) * 0.05

        # Find the top bucket value
        top_bucket = _bucket(max(conf for _, conf in matches))

        top_group: list[tuple[str, float]] = []
        rest: list[tuple[str, float]] = []

        for domain_with_pattern, conf in matches:
            if _bucket(conf) == top_bucket:
                top_group.append((domain_with_pattern, conf))
            else:
                rest.append((domain_with_pattern, conf))

        # Within the top bucket keep only the most specific (longest pattern)
        if len(top_group) > 1:
            def _pattern_len(item: tuple[str, float]) -> int:
                key = item[0]
                if "|" in key:
                    return len(key.split("|", 1)[1])
                return len(key)

            top_group = [max(top_group, key=_pattern_len)]

        # Strip the "|pattern" suffix before returning
        def _strip_pattern(item: tuple[str, float]) -> tuple[str, float]:
            domain, conf = item
            return (domain.split("|", 1)[0], conf)

        deduped = [_strip_pattern(t) for t in top_group] + [
            _strip_pattern(t) for t in rest
        ]
        deduped.sort(key=lambda t: t[1], reverse=True)
        return deduped

    # ------------------------------------------------------------------
    # Core matching
    # ------------------------------------------------------------------

    def match(self, message: str) -> FastRouteResult | None:
        message_lower = message.lower().strip()
        if not message_lower:
            return None

        all_matches: list[FastRouteResult] = []

        for domain_id, patterns in _COMPILED_PATTERNS.items():
            best_for_domain: FastRouteResult | None = None
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

        # PR5 / A2 (Task #1005) — structured-tag hard priority.
        # Mensagens do chat lateral começam com `[ACTION:<verb>][target_*:<key>]`.
        # Esses tokens são intent-signals determinísticos do frontend (não
        # texto livre do usuário). Bypass da penalidade de ambiguidade
        # E early return: se o melhor match veio de um pattern de tag
        # estruturada, devolve direto sem deixar o "vaga"/"campanha"
        # citado no resto da frase competir.
        if best_match.matched_text.startswith("[action:"):
            logger.debug(
                "FastRouter structured-tag short-circuit: '%s' → %s (conf=%.2f)",
                message[:50], best_match.domain_id, best_match.confidence,
            )
            return best_match

        # Frente 1 (unificacao wizard 2026-05-29) — wizard creation short-circuit.
        # Intencao de CRIACAO de vaga e deterministica (mesma filosofia do Tier 2.5
        # Wizard Guard no cascaded_router). Os patterns do dominio `wizard` sao TODOS
        # gatilhos especificos de criacao (sem generico tipo \bvaga\b), entao quando
        # wizard e o top match ele DEVE vencer. Sem isto, frases curtas como "nova vaga"
        # (match 9 chars -> conf 0.88) perdiam para o `\bvaga\b` de job_management
        # (0.78) por causa da penalidade de ambiguidade (gap 0.10) que rebaixava o
        # vencedor a 0.73 e o _deduplicate_matches (re-sort por conf) o flipava.
        if best_match.domain_id == "wizard":
            logger.debug(
                "FastRouter wizard-creation short-circuit: '%s' → wizard (conf=%.2f)",
                message[:50], best_match.confidence,
            )
            return best_match

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

        # P06: deduplication — resolve ties by most-specific pattern string
        raw_tuples: list[tuple[str, float]] = [
            (f"{r.domain_id}|{r.matched_pattern}", r.confidence)
            for r in all_matches
        ]
        before_count = len(raw_tuples)
        deduped_tuples = self._deduplicate_matches(raw_tuples)
        after_count = len(deduped_tuples)

        logger.debug(
            "[FastRouter] dedup: %d -> %d matches for '%s'",
            before_count,
            after_count,
            message[:50],
        )

        # Re-resolve best_match from deduped result (domain_id is first element)
        if deduped_tuples:
            top_domain_id, top_conf = deduped_tuples[0]
            # Find the original FastRouteResult for the winning domain
            for r in all_matches:
                if r.domain_id == top_domain_id:
                    best_match = r
                    # Preserve the (possibly penalised) confidence from above
                    # but ensure the deduplication winner's confidence is used
                    # only if it differs meaningfully (dedup doesn't change conf)
                    break

        # LIA-I05: Shadow comparison with KeywordIntentMatcher (fail-open)
        try:
            domain_matcher = _get_domain_matcher()
            if domain_matcher is not None:
                shadow = domain_matcher.match(message)
                if shadow.confidence > 0.5 and shadow.action != best_match.domain_id:
                    logger.debug(
                        "[LIA-I05] Domain routing disagreement: fast_router=%s, matcher=%s (conf=%.2f), query=%r",
                        best_match.domain_id, shadow.action, shadow.confidence, message[:60],
                    )
        except Exception as e:
            logger.debug("[LIA-I05] Shadow match failed: %s", e)

        logger.debug(
            f"FastRouter matched '{message[:50]}...' → {best_match.domain_id} "
            f"(conf={best_match.confidence:.2f}, candidates={len(all_matches)})"
        )
        return best_match

    def match_all(self, message: str) -> list[FastRouteResult]:
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

    def get_patterns_for_domain(self, domain_id: str) -> list[str]:
        return DOMAIN_PATTERNS.get(domain_id, [])

    def get_all_domains(self) -> list[str]:
        return list(DOMAIN_PATTERNS.keys())
