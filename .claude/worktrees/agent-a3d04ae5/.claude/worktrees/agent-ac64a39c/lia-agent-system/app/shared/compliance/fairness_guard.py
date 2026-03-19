"""
FairnessGuard - Middleware that blocks discriminatory filters.

Intercepts queries before domain processing and checks for bias indicators.
When a discriminatory pattern is detected, returns an educational message
instead of proceeding with the query.

Part of the 3-pillar compliance architecture (LGPD, SOX, EU AI Act).
"""
import hashlib
import re
import logging
import unicodedata
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

try:
    from app.observability.metrics import fairness_blocks_total
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False


def _normalize_text(text: str) -> str:
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')


IMPLICIT_BIAS_TERMS: Dict[str, str] = {
    # Chaves sem acentuação — _normalize_text() normaliza antes da busca
    "boa aparencia": "O termo 'boa aparência' pode configurar discriminação estética (Lei 12.984/14). Use critérios objetivos de apresentação profissional.",
    "bairros nobres": "Filtrar por 'bairros nobres' pode configurar discriminação socioeconômica. Considere critérios de disponibilidade ou mobilidade.",
    "regiao nobre": "Filtrar por 'região nobre' pode configurar discriminação socioeconômica. Considere critérios de disponibilidade ou mobilidade.",
    "universidades de primeira linha": "Filtrar por 'universidades de primeira linha' pode configurar elitismo acadêmico. Avalie competências e resultados.",
    "faculdade de ponta": "Filtrar por 'faculdade de ponta' pode configurar elitismo acadêmico. Avalie competências e resultados.",
    "escola particular": "Filtrar por 'escola particular' pode configurar discriminação socioeconômica. Avalie formação e competências.",
    "clube social": "Referência a 'clube social' pode configurar discriminação socioeconômica ou de classe.",
    "perfil adequado": "O termo 'perfil adequado' é vago e pode mascarar vieses inconscientes. Especifique competências objetivas.",
    "apresentacao pessoal": "O termo 'apresentação pessoal' pode configurar discriminação estética. Use critérios objetivos.",
    "morar proximo": "Filtrar por 'morar próximo' pode configurar discriminação socioeconômica. Considere disponibilidade ou trabalho remoto.",
    "boa familia": "O termo 'boa família' pode configurar discriminação socioeconômica ou de origem. Use critérios profissionais.",
}


@dataclass
class FairnessCheckResult:
    is_blocked: bool
    blocked_terms: List[str] = field(default_factory=list)
    category: Optional[str] = None
    educational_message: Optional[str] = None
    original_query: str = ""
    confidence: float = 0.0
    soft_warnings: List[str] = field(default_factory=list)

    @property
    def is_biased(self) -> bool:
        """Alias semântico para is_blocked (Layer 1 = viés explícito)."""
        return self.is_blocked


DISCRIMINATORY_CATEGORIES = {
    "genero": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(homens?|mulheres?|masculino|feminino)\b",
            r"\b(sexo|gênero|genero)\s*(\w+\s+)*(masculino|feminino|macho|fêmea|femea)\b",
            r"\bexcluir?\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\bpreferência\s+por\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\bpreferencia\s+por\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\b(gender|male|female)\s+only\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por gênero. "
            "A legislação trabalhista brasileira (Art. 5º, CLT) e a LGPD proíbem "
            "discriminação por gênero em processos seletivos. "
            "Posso ajudar você a definir critérios baseados em competências e experiência?"
        ),
    },
    "raca_etnia": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(brancos?|negros?|pardos?|indígenas?|indigenas?|amarelos?)\b",
            r"\b(raça|raca|cor|etnia)\s*(\w+\s+)*(branca|negra|parda)\b",
            r"\bexcluir?\s+(\w+\s+)*(brancos?|negros?|pardos?)\b",
            r"\b(race|ethnicity|white|black)\s+only\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por raça ou etnia. "
            "A Constituição Federal (Art. 5º) e a Lei 7.716/89 proíbem "
            "discriminação racial em qualquer contexto, incluindo processos seletivos. "
            "Posso ajudar você a buscar candidatos por habilidades e experiência?"
        ),
    },
    "idade": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(jovens?|velhos?|idosos?)\b",
            r"\b(muito|demais|bastante|bem)?\s*(velh[oa]s?|idosos?|jovens?)\s*(demais|para)?\b",
            r"\b(idade|anos?)\s*(máxim[oa]|mínim[oa]|maxim[oa]|minim[oa])\s*[:\s]*\d+\b",
            r"\bexcluir?\s+maiores?\s+de\s+\d+\b",
            r"\bexcluir?\s+menores?\s+de\s+\d+\b",
            r"\b(máximo|mínimo|maximo|minimo)\s+\d+\s+anos\b(?!\s+de\s+(experiên|experienc|atua|mercado|pr[aá]tica|trabalho|carreira|vivên|vivenc|profissional|experi))",
            r"\bidade\s+entre\s+\d+\s+e\s+\d+\b",
            r"\bde\s+\d+\s+(a|até|ate)\s+\d+\s+anos\b",
            r"\b(age|old|young)\s+only\b",
            r"\b(velho|velha|idoso|idosa)\s+(para|pra|demais)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por idade. "
            "O Estatuto do Idoso (Lei 10.741/03) e a CLT proíbem discriminação etária "
            "em processos seletivos. Posso ajudar a definir requisitos de senioridade "
            "baseados em experiência profissional?"
        ),
    },
    "religiao": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(cristãos?|cristaos?|muçulmanos?|muculmanos?|judeus?|budistas?|ateus?)\b",
            r"\b(religião|religiao)\s*(\w+\s+)*(cristã|crista|católica|catolica|evangélica|evangelica|muçulmana|muculmana|judaica)\b",
            r"\bexcluir?\s+(\w+\s+)*(cristãos?|cristaos?|muçulmanos?|muculmanos?|judeus?|ateus?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por religião. "
            "A Constituição Federal garante liberdade religiosa (Art. 5º, VI) "
            "e proíbe discriminação por credo. "
            "Posso ajudar a definir critérios baseados em disponibilidade e competências?"
        ),
    },
    "orientacao_sexual": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(heterossexuais?|homossexuais?|gays?|lésbicas?|lesbicas?|bi)\b",
            r"\b(orientação|orientacao)\s+sexual\b",
            r"\bexcluir?\s+(\w+\s+)*(gays?|lésbicas?|lesbicas?|heterossexuais?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por orientação sexual. "
            "O STF reconhece a criminalização da homofobia (ADO 26) e qualquer "
            "discriminação por orientação sexual é vedada. "
            "Posso ajudar a buscar candidatos com base em qualificações profissionais?"
        ),
    },
    "estado_civil": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(solteiros?|casados?|divorciados?|viúvos?|viuvos?)\b",
            r"\bestado\s+civil\b",
            r"\bexcluir?\s+(\w+\s+)*(solteiros?|casados?|divorciados?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por estado civil. "
            "A CLT proíbe discriminação por estado civil em processos seletivos. "
            "Posso ajudar a definir critérios baseados em experiência e competências?"
        ),
    },
    "deficiencia": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(deficientes?|pcd|pne)\b",
            r"\bexcluir?\s+(\w+\s+)*(deficientes?|pcd|cadeirantes?)\b",
            r"\bsem\s+defici[eê]ncia\b",
            r"\bsem\s+deficiencia\b",
        ],
        "message": (
            "A LIA não pode excluir candidatos com deficiência. "
            "A Lei 8.213/91 (Lei de Cotas) e o Estatuto da Pessoa com Deficiência "
            "(Lei 13.146/15) protegem os direitos de PCDs. "
            "Posso ajudar a buscar candidatos com as competências necessárias?"
        ),
    },
    "maternidade_paternidade": {
        "terms": [
            r"\bengravidar\b",
            r"\bgravidez\b",
            r"\b(tem|ter|possui|possuir|ter)\s+filhos?\b",
            r"\bsem\s+filhos?\b",
            r"\bplano\s+(de\s+)?ter\s+filhos?\b",
            r"\bplanej(a|and[oa])\s+(ter|engravidar)\b",
            r"\bfilhos?\s+(previsto|planejado|futuro)\b",
        ],
        "message": (
            "A LIA não pode questionar candidatos sobre planos de maternidade/paternidade "
            "ou existência de filhos. A CLT (Art. 373-A) e a Lei 9.029/95 proíbem "
            "discriminação por gestação ou maternidade em processos seletivos. "
            "Posso ajudar a definir critérios baseados em disponibilidade e competências?"
        ),
    },
    "nacionalidade": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(brasileiros?|estrangeiros?)\b",
            r"\bexcluir?\s+(\w+\s+)*(estrangeiros?|imigrantes?)\b",
            r"\bnacionalidade\s*(brasileira|estrangeira)\b",
        ],
        "message": (
            "A LIA não pode discriminar por nacionalidade em processos seletivos. "
            "A Constituição Federal garante igualdade entre brasileiros e estrangeiros "
            "residentes (Art. 5º). Posso ajudar com critérios de proficiência linguística "
            "ou experiência regional?"
        ),
    },
}

_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {}


def _ensure_compiled() -> None:
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        for category, config in DISCRIMINATORY_CATEGORIES.items():
            _COMPILED_PATTERNS[category] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in config["terms"]
            ]
        logger.info(f"FairnessGuard compiled patterns for {len(_COMPILED_PATTERNS)} categories")


class FairnessGuard:
    def __init__(self):
        _ensure_compiled()

    def check(self, query: str) -> FairnessCheckResult:
        if not query or not query.strip():
            return FairnessCheckResult(is_blocked=False, original_query=query)

        query_lower = query.lower().strip()
        query_normalized = _normalize_text(query_lower)
        blocked_terms = []
        detected_category = None
        max_confidence = 0.0

        for category, patterns in _COMPILED_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(query_lower)
                if not match:
                    match = pattern.search(query_normalized)
                if match:
                    blocked_terms.append(match.group())
                    if not detected_category:
                        detected_category = category
                    confidence = min(0.95, 0.7 + len(match.group()) * 0.02)
                    max_confidence = max(max_confidence, confidence)

        soft_warnings = self.check_implicit_bias(query)

        if blocked_terms and detected_category:
            educational_message = DISCRIMINATORY_CATEGORIES[detected_category]["message"]
            logger.warning(
                f"FairnessGuard BLOCKED query: category={detected_category}, "
                f"terms={blocked_terms}, query='{query[:60]}...'"
            )
            if _METRICS_AVAILABLE:
                fairness_blocks_total.labels(category=detected_category).inc()
            return FairnessCheckResult(
                is_blocked=True,
                blocked_terms=blocked_terms,
                category=detected_category,
                educational_message=educational_message,
                original_query=query,
                confidence=max_confidence,
                soft_warnings=soft_warnings,
            )

        return FairnessCheckResult(
            is_blocked=False,
            original_query=query,
            soft_warnings=soft_warnings,
        )

    def check_explicit_bias(self, text: str) -> "FairnessCheckResult":
        """Alias semântico para check() — verifica Camada 1 (padrões explícitos de viés)."""
        return self.check(text)

    def check_implicit_bias(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        text_lower = text.lower().strip()
        text_normalized = _normalize_text(text_lower)
        warnings = []

        for term, warning_message in IMPLICIT_BIAS_TERMS.items():
            term_lower = term.lower()
            term_normalized = _normalize_text(term_lower)
            if term_lower in text_lower or term_normalized in text_normalized:
                if warning_message not in warnings:
                    warnings.append(warning_message)

        if warnings:
            # LGPD: logar apenas contagem e tamanho — nunca fragmentos do texto
            # (pode conter dados do candidato gerados pelo LLM)
            logger.info(
                "FairnessGuard implicit bias detected: %d warnings for text_len=%d",
                len(warnings), len(text),
            )

        return warnings

    async def check_semantic(self, text: str, context: str = "") -> FairnessCheckResult:
        result = self.check(text)

        try:
            from app.services.llm_service import LLMService
            llm_service = LLMService()

            semantic_prompt = (
                "Analise o seguinte texto de política de contratação e identifique "
                "possíveis vieses discriminatórios implícitos ou explícitos. "
                "Responda APENAS com uma lista de alertas, um por linha. "
                "Se não houver vieses, responda 'NENHUM_VIES_DETECTADO'.\n\n"
                f"Texto: {text}\n"
            )
            if context:
                semantic_prompt += f"Contexto: {context}\n"

            response = await llm_service.generate(semantic_prompt)

            if response and "NENHUM_VIES_DETECTADO" not in response:
                semantic_warnings = [
                    line.strip() for line in response.strip().split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                result.soft_warnings.extend(semantic_warnings)

        except (ImportError, Exception) as e:
            logger.debug(f"Semantic analysis unavailable: {e}")

        return result

    def get_categories(self) -> List[str]:
        return list(DISCRIMINATORY_CATEGORIES.keys())

    async def log_check(
        self,
        result: "FairnessCheckResult",
        db: "AsyncSession",
        context: str = "unknown",
        company_id: Optional[str] = None,
        recruiter_id: Optional[str] = None,
        job_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> None:
        """
        Persist a FairnessGuard check result to the audit log (EU AI Act compliance).

        Only logs checks that blocked the query OR generated soft warnings.
        Clean checks are not persisted to avoid flooding the table.

        Args:
            result: The FairnessCheckResult from check().
            db: Async SQLAlchemy session.
            context: Where the check occurred (pipeline | wizard | sourcing | search).
            company_id: Company that made the request.
            recruiter_id: Recruiter user ID.
            job_id: Related job vacancy ID.
            candidate_id: Related candidate ID.
        """
        if not result.is_blocked and not result.soft_warnings:
            return

        try:
            from app.models.fairness_audit import FairnessAuditLog

            query_hash = hashlib.sha256(result.original_query.encode("utf-8")).hexdigest()

            import uuid as _uuid
            record = FairnessAuditLog(
                company_id=_uuid.UUID(company_id) if company_id else None,
                recruiter_id=_uuid.UUID(recruiter_id) if recruiter_id else None,
                job_id=_uuid.UUID(job_id) if job_id else None,
                candidate_id=_uuid.UUID(candidate_id) if candidate_id else None,
                query_hash=query_hash,
                category=result.category,
                blocked_terms=result.blocked_terms or [],
                confidence=result.confidence,
                is_blocked=result.is_blocked,
                context=context,
            )
            db.add(record)
            await db.flush()
            logger.debug(
                f"FairnessGuard audit logged: is_blocked={result.is_blocked} "
                f"category={result.category} context={context}"
            )
        except Exception as e:
            logger.error(f"FairnessGuard audit log failed (non-blocking): {e}")
