"""
Security Patterns — Explicit Hardening for LIA Platform.

Comprehensive PT/EN prompt injection pattern library with 20+ documented patterns
covering: jailbreak, data exfiltration, bias elicitation, score manipulation,
privilege escalation, PII extraction, and fairness bypass.

Integrates with PromptInjectionGuard and serves as middleware for agent pipelines.

Usage:
    from app.shared.robustness.security_patterns import (
        check_input_security,
        SECURITY_PATTERNS,
        SecurityCheckResult,
    )
"""
import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ThreatCategory(StrEnum):
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    BIAS_ELICITATION = "bias_elicitation"
    SCORE_MANIPULATION = "score_manipulation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PII_EXTRACTION = "pii_extraction"
    FAIRNESS_BYPASS = "fairness_bypass"
    SYSTEM_OVERRIDE = "system_override"
    DELIMITER_INJECTION = "delimiter_injection"
    ROLE_MANIPULATION = "role_manipulation"


class RiskLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


RISK_PRIORITY: dict[str, int] = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


@dataclass
class SecurityCheckResult:
    is_blocked: bool
    risk_level: str = RiskLevel.NONE
    threat_categories: list[str] = field(default_factory=list)
    matched_pattern_names: list[str] = field(default_factory=list)
    confidence: float = 0.0
    original_input: str = ""
    block_reason: str = ""


SECURITY_PATTERNS: list[dict[str, Any]] = [
    # ── 1. JAILBREAK — Ignore previous instructions ──────────────────────────
    {
        "name": "jailbreak_ignore_instructions_en",
        "category": ThreatCategory.JAILBREAK,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
            re.compile(r"ignore\s+(all\s+)?above\s+instructions?", re.IGNORECASE),
            re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
            re.compile(r"forget\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
            re.compile(r"override\s+(previous\s+|your\s+)?instructions?", re.IGNORECASE),
        ],
    },
    # ── 2. JAILBREAK — Ignorar instruções anteriores (PT) ────────────────────
    {
        "name": "jailbreak_ignore_instructions_pt",
        "category": ThreatCategory.JAILBREAK,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"ignore?\s+tudo\s+(que\s+)?anterior", re.IGNORECASE),
            re.compile(r"desconsidere?.{0,30}instru", re.IGNORECASE | re.DOTALL),
            re.compile(r"esque.{0,5}a.{0,20}instru", re.IGNORECASE | re.DOTALL),
            re.compile(r"ignore.{0,20}instru.{0,10}anteriores?", re.IGNORECASE | re.DOTALL),
            re.compile(r"anule?\s+(as\s+)?regras?\s+anteriores?", re.IGNORECASE),
        ],
    },
    # ── 3. JAILBREAK — DAN / Developer mode ──────────────────────────────────
    {
        "name": "jailbreak_dan_developer_mode",
        "category": ThreatCategory.JAILBREAK,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"\bDAN\b", re.IGNORECASE),
            re.compile(r"do\s+anything\s+now", re.IGNORECASE),
            re.compile(r"developer\s+mode", re.IGNORECASE),
            re.compile(r"modo\s+desenvolvedor", re.IGNORECASE),
            re.compile(r"sem\s+(restr[ií][çc][õo]es|limites?|filtros?)", re.IGNORECASE),
            re.compile(r"without\s+(restrictions?|limits?|filters?)", re.IGNORECASE),
        ],
    },
    # ── 4. JAILBREAK — "From now on you are / Act as" ────────────────────────
    {
        "name": "jailbreak_act_as_override",
        "category": ThreatCategory.JAILBREAK,
        "risk": RiskLevel.HIGH,
        "confidence": 0.88,
        "patterns": [
            re.compile(r"(from\s+now\s+on|starting\s+now)\s+you\s+(are|will\s+be)", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+(a|an|the)\s+\w+\s+without", re.IGNORECASE),
            re.compile(r"act\s+as\s+(a|an)\s+\w+\s+without\s+(restriction|ethic|guideline)", re.IGNORECASE),
            re.compile(r"de\s+agora\s+em\s+diante\s+voc[êe]\s+[ée]", re.IGNORECASE),
            re.compile(r"voc[êe]\s+agora\s+[ée]\s+(um|uma)\s+\w+\s+sem", re.IGNORECASE),
        ],
    },
    # ── 5. DATA EXFILTRATION — "Show me all candidates" ─────────────────────
    {
        "name": "data_exfiltration_show_all",
        "category": ThreatCategory.DATA_EXFILTRATION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.85,
        "patterns": [
            re.compile(r"(show|list|dump|display|print)\s+all\s+(candidates?|users?|companies?|data|records?)", re.IGNORECASE),
            re.compile(r"(mostre|liste|imprima|exiba)\s+todos?\s+(os\s+)?(candidatos?|usu.{1,5}rios?|empresas?|dados?)", re.IGNORECASE | re.DOTALL),
            re.compile(r"export\s+(all|every)\s+(candidate|user|data|record)", re.IGNORECASE),
            re.compile(r"exporte?.{0,20}(candidatos?|dados?)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 6. DATA EXFILTRATION — HTTP exfil / send to URL ─────────────────────
    {
        "name": "data_exfiltration_http_send",
        "category": ThreatCategory.DATA_EXFILTRATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.92,
        "patterns": [
            re.compile(r"(send|post|fetch|curl|submit)\s+.{0,50}(https?://|ftp://|url\s*=)", re.IGNORECASE),
            re.compile(r"(envie?|mande?|poste?|submeta)\s+.{0,50}(https?://|url)", re.IGNORECASE),
            re.compile(r"make\s+a\s+(http|get|post)\s+request", re.IGNORECASE),
            re.compile(r"fa[çc]a\s+uma\s+requisi[çc][ãa]o", re.IGNORECASE),
        ],
    },
    # ── 7. DATA EXFILTRATION — base64/encoding tricks ─────────────────────────
    {
        "name": "data_exfiltration_encoding",
        "category": ThreatCategory.DATA_EXFILTRATION,
        "risk": RiskLevel.MEDIUM,
        "confidence": 0.75,
        "patterns": [
            re.compile(r"(base64|base 64)\s+(encode|decode|encod)", re.IGNORECASE),
            re.compile(r"convert\s+.{0,30}(to\s+)?(hex|hexadecimal|binary|octal)", re.IGNORECASE | re.DOTALL),
            re.compile(r"encode\s+(the\s+)?response\s+(in|as|to)", re.IGNORECASE),
            re.compile(r"codif.{0,10}(em|para)\s+(base64|hex)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 8. BIAS ELICITATION — "Prefer men / women" ──────────────────────────
    {
        "name": "bias_elicitation_gender",
        "category": ThreatCategory.BIAS_ELICITATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(prefer|consider|hire|accept)\s+(men|women|male|female|homem|mulher)\s+candidates?", re.IGNORECASE),
            re.compile(r"only\s+(consider|hire|accept|use)\s+(female|male|women|men)\s+candidates?", re.IGNORECASE),
            re.compile(r"(rank|prioritize|favor|prefer)\s+candidates?\s+(by|based\s+on)\s+(gender|sex|race|nationality)", re.IGNORECASE),
            re.compile(r"(prioritize|priorize?|favor|rank)\s+(female|male|women|men)\s+candidates?", re.IGNORECASE),
            re.compile(r"prefira?\s+(homens?|mulheres?|brancos?|negros?)\s*(candidatos?|candidatas?|para|\.)", re.IGNORECASE),
            re.compile(r"priorize?(?![\w\W]{0,40}diversidade).{0,20}(mulheres?|homens?|g.{0,3}nero|sexo)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(priorizar|dar\s+prefer.{0,5}ncia).{0,30}(g.{0,3}nero|sexo|ra.{0,3}a|cor)\b", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 9. BIAS ELICITATION — Nationality / ethnicity discrimination ─────────
    {
        "name": "bias_elicitation_ethnicity_nationality",
        "category": ThreatCategory.BIAS_ELICITATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(rank|prioritize|filter|prefer|exclude)\s+candidates?\s+(by|based\s+on)\s+(nationality|ethnicity|race|their\s+race|religion|origin|age)", re.IGNORECASE),
            re.compile(r"exclude\s+candidates?\s+based\s+on\s+(their\s+)?(race|ethnicity|nationality|religion|age|disability)", re.IGNORECASE),
            re.compile(r"filter\s+out\s+(older|younger|male|female|black|white)\s+candidates?", re.IGNORECASE),
            re.compile(r"(classificar|priorizar|filtrar|preferir|excluir)\s+candidatos?\s+(por|com\s+base\s+em)\s+(nacionalidade|etnia|ra.{0,3}a|religi)", re.IGNORECASE | re.DOTALL),
            re.compile(r"only\s+(hire|consider|accept)\s+(brazilians?|foreigners?|whites?|blacks?)", re.IGNORECASE),
            re.compile(r"(contratar|considerar|aceitar)\s+apenas\s+(brasileiros?|estrangeiros?|brancos?|negros?)", re.IGNORECASE),
        ],
    },
    # ── 10. SCORE MANIPULATION — "Set score to 10" ──────────────────────────
    {
        "name": "score_manipulation_set_value",
        "category": ThreatCategory.SCORE_MANIPULATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(set|change|force)\s+.{0,20}(score|nota|pontua.{0,5}o|rating|grade)\s+to\s+[\d.]+", re.IGNORECASE | re.DOTALL),
            re.compile(r"make\s+(the\s+)?(evaluation\s+)?(score|rating|grade)\s+[\d.]+", re.IGNORECASE),
            re.compile(r"(defina?|altere?|coloque?|mude?).{0,20}(nota|pontua.{0,5}o|score).{0,20}[\d.]+", re.IGNORECASE | re.DOTALL),
            re.compile(r"give\s+(this\s+)?candidate\s+a\s+(score|grade|nota)\s+of\s+[\d.]+", re.IGNORECASE),
            re.compile(r"d.{0,5}\s+(ao|para\s+o)\s+candidato.{0,20}(nota|score|pontua.{0,5}o)\s+[\d.]+", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 11. SCORE MANIPULATION — Override evaluation ─────────────────────────
    {
        "name": "score_manipulation_override_eval",
        "category": ThreatCategory.SCORE_MANIPULATION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.88,
        "patterns": [
            re.compile(r"(override|bypass|ignore|skip)\s+(the\s+)?(evaluation|assessment|scoring|avalia)", re.IGNORECASE),
            re.compile(r"(ignore|skip)\s+(the\s+)?WSI\s+(score|evaluation|assessment)", re.IGNORECASE),
            re.compile(r"ignore\s+(a\s+)?pontua.{0,5}o", re.IGNORECASE | re.DOTALL),
            re.compile(r"(pule?|passe?).{0,20}avalia", re.IGNORECASE | re.DOTALL),
            re.compile(r"approve?\s+(this\s+)?candidate\s+without\s+(evaluation|assessment)", re.IGNORECASE),
            re.compile(r"aprove?.{0,20}candidato.{0,20}sem\s+(avalia|teste)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 12. PRIVILEGE ESCALATION — "As admin" ────────────────────────────────
    {
        "name": "privilege_escalation_admin",
        "category": ThreatCategory.PRIVILEGE_ESCALATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"as\s+(an?\s+)?(admin|administrator|superuser|root|system)", re.IGNORECASE),
            re.compile(r"(with|using)\s+(admin|administrator)\s+(privileges?|access|rights?|permissions?)", re.IGNORECASE),
            re.compile(r"como\s+(administrador|admin|superusu.{0,5}rio|root)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(com|usando)\s+privil.{0,5}gios?\s+de\s+(administrador|admin)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(elevate|escalate)\s+(my\s+)?(privileges?|access|permissions?)", re.IGNORECASE),
            re.compile(r"(elevar|escalar)\s+(meus?\s+)?(privil.{0,5}gios?|acessos?|permiss)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 13. PRIVILEGE ESCALATION — Cross-tenant access ───────────────────────
    {
        "name": "privilege_escalation_cross_tenant",
        "category": ThreatCategory.PRIVILEGE_ESCALATION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.92,
        "patterns": [
            re.compile(r"(access|show|get|fetch)\s+.{0,30}(from|de)\s+.{0,20}(another|different|other|outr)\s+company", re.IGNORECASE | re.DOTALL),
            re.compile(r"(acess|mostr|buscar?).{0,20}(dados?|candidatos?|vagas?).{0,20}(outra|outro)\s+empresa", re.IGNORECASE | re.DOTALL),
            re.compile(r"switch\s+company\s+(to|id)", re.IGNORECASE),
            re.compile(r"change\s+company_?id\s+to", re.IGNORECASE),
            re.compile(r"usar?\s+company_?id\s+de\s+outra", re.IGNORECASE),
        ],
    },
    # ── 14. PII EXTRACTION — CPF / CNPJ ──────────────────────────────────────
    {
        "name": "pii_extraction_cpf_cnpj",
        "category": ThreatCategory.PII_EXTRACTION,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(show|list|give|reveal|exibe?|mostr|liste?).{0,30}(CPF|CNPJ)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(CPF|CNPJ)\s+(do|da|de)\s+\S+", re.IGNORECASE),
            re.compile(r"(qual|what).{0,20}(CPF|CNPJ)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(extract|obten|extraia).{0,20}(CPF|CNPJ|RG)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 15. PII EXTRACTION — Phone / email dump ───────────────────────────────
    {
        "name": "pii_extraction_phone_email",
        "category": ThreatCategory.PII_EXTRACTION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.85,
        "patterns": [
            re.compile(r"(show|list|dump|reveal)\s+all\s+(phone|email|contact)\s+(numbers?|addresses?)?", re.IGNORECASE),
            re.compile(r"(mostr(e|a)|liste?|imprima)\s+todos?\s+(os\s+)?(telefones?|e-?mails?|contatos?)", re.IGNORECASE),
            re.compile(r"(extract|obtenha)\s+(all\s+)?(phone\s+numbers?|email\s+addresses?)", re.IGNORECASE),
            re.compile(r"list\s+personal\s+(information|data|details?)\s+of\s+(all|every)", re.IGNORECASE),
        ],
    },
    # ── 16. PII EXTRACTION — Address / personal data ─────────────────────────
    {
        "name": "pii_extraction_address_personal",
        "category": ThreatCategory.PII_EXTRACTION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.82,
        "patterns": [
            re.compile(r"(reveal|show|get|fetch)\s+.{0,20}(home\s+address|personal\s+address|residential\s+address)", re.IGNORECASE),
            re.compile(r"(revelar?|mostrar?|obter?).{0,20}endere.{0,5}o\s+(residencial|pessoal|de\s+casa)", re.IGNORECASE | re.DOTALL),
            re.compile(r"(date\s+of\s+birth|birthdate|birthday)\s+of\s+(all|every|\S+)", re.IGNORECASE),
            re.compile(r"data\s+de\s+nascimento", re.IGNORECASE),
        ],
    },
    # ── 17. FAIRNESS BYPASS — Ignore fairness constraints ────────────────────
    {
        "name": "fairness_bypass_ignore",
        "category": ThreatCategory.FAIRNESS_BYPASS,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(ignore|skip|disable|bypass)\s+(fairness|bias|dei|equal\s+opportunity)", re.IGNORECASE),
            re.compile(r"(ignore|skip|pular?).{0,20}(equidade|vi.{0,3}s|bias|igualdade)", re.IGNORECASE | re.DOTALL),
            re.compile(r"desabilitar?.{0,20}(fairness|detec|vi.{0,3}s|bias)", re.IGNORECASE | re.DOTALL),
            re.compile(r"turn\s+off\s+(fairness|bias\s+detection|dei)", re.IGNORECASE),
            re.compile(r"desligar?.{0,20}(fairness|detec.{0,10}vi.{0,3}s)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 18. FAIRNESS BYPASS — Discriminatory shortlisting ────────────────────
    {
        "name": "fairness_bypass_discriminatory_filter",
        "category": ThreatCategory.FAIRNESS_BYPASS,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.95,
        "patterns": [
            re.compile(r"(filter|exclude|remove|reject)\s+candidates?\s+(by|based\s+on)\s+(age|gender|race|religion|nationality|disability)", re.IGNORECASE),
            re.compile(r"(filtrar?|excluir?|remover?|rejeitar?)\s+candidatos?\s+(por|com\s+base\s+em)\s+(idade|g[êe]nero|ra[çc]a|religi[ãa]o|nacionalidade|defici[êe]ncia)", re.IGNORECASE),
            re.compile(r"(only\s+shortlist|shortlist\s+only)\s+(young|old|male|female|white|black)", re.IGNORECASE),
            re.compile(r"(selecionar?\s+apenas|apenas\s+selecionar?)\s+(jovens?|idosos?|homens?|mulheres?|brancos?|negros?)", re.IGNORECASE),
        ],
    },
    # ── 19. SYSTEM OVERRIDE — System prompt manipulation ─────────────────────
    {
        "name": "system_override_delimiter",
        "category": ThreatCategory.SYSTEM_OVERRIDE,
        "risk": RiskLevel.CRITICAL,
        "confidence": 0.98,
        "patterns": [
            re.compile(r"```system", re.IGNORECASE),
            re.compile(r"\[SYSTEM\]", re.IGNORECASE),
            re.compile(r"<\|?(system|im_start|endoftext)\|?>", re.IGNORECASE),
            re.compile(r"###\s*SYSTEM", re.IGNORECASE),
            re.compile(r"---\s*system\s*---", re.IGNORECASE),
            re.compile(r"\|\|SYSTEM\|\|", re.IGNORECASE),
        ],
    },
    # ── 20. SYSTEM OVERRIDE — Prompt extraction ───────────────────────────────
    {
        "name": "system_override_extract_prompt",
        "category": ThreatCategory.SYSTEM_OVERRIDE,
        "risk": RiskLevel.HIGH,
        "confidence": 0.88,
        "patterns": [
            re.compile(r"(show|reveal|print|display|tell\s+me)\s+(me\s+)?(your|the)\s+system\s+prompt", re.IGNORECASE),
            re.compile(r"what\s+(is|are)\s+your\s+(system\s+)?instructions?", re.IGNORECASE),
            re.compile(r"(mostre?|revele?|exiba?)\s+(o\s+)?seu\s+prompt\s+(de\s+sistema|completo)", re.IGNORECASE),
            re.compile(r"quais?\s+s[ãa]o\s+suas?\s+instru[çc][õo]es\s+(completas?|de\s+sistema)", re.IGNORECASE),
            re.compile(r"(repeat|reproduce|output)\s+(your\s+)?(system\s+)?prompt\s+(word\s+for\s+word|verbatim)", re.IGNORECASE),
        ],
    },
    # ── 21. ROLE MANIPULATION — Pretend / finja ser ───────────────────────────
    {
        "name": "role_manipulation_pretend",
        "category": ThreatCategory.ROLE_MANIPULATION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.88,
        "patterns": [
            re.compile(r"pretend\s+(to\s+be|you\s+are).{0,60}(without|ignores?|no\s+(restriction|ethic|guideline|rule))", re.IGNORECASE | re.DOTALL),
            re.compile(r"finja\s+(ser|que).{0,30}sem\s+(restr|ética|regra)", re.IGNORECASE | re.DOTALL),
            re.compile(r"imagine\s+you\s+are\s+an?\s*(AI\s+)?(without|that\s+ignores?)\s*(restriction|rule|guideline)?", re.IGNORECASE),
            re.compile(r"imagine\s+(que\s+)?voc.{0,5}\s+(é|e)\s+uma?\s*(IA\s+)?sem\s+(restr|regra)", re.IGNORECASE | re.DOTALL),
        ],
    },
    # ── 22. DELIMITER INJECTION — Markdown / code block tricks ───────────────
    {
        "name": "delimiter_injection_markdown",
        "category": ThreatCategory.DELIMITER_INJECTION,
        "risk": RiskLevel.HIGH,
        "confidence": 0.85,
        "patterns": [
            re.compile(r"<!--\s*ignore\s+.{0,50}-->", re.IGNORECASE),
            re.compile(r"<!\s*--\s*system", re.IGNORECASE),
            re.compile(r"\{\{.*system.*\}\}", re.IGNORECASE),
            re.compile(r"\{%\s*system", re.IGNORECASE),
            re.compile(r"<prompt[^>]*>\s*ignore", re.IGNORECASE),
        ],
    },
]


def check_input_security(text: str) -> SecurityCheckResult:
    """
    Check user input against all security patterns.

    Args:
        text: Raw user input to evaluate.

    Returns:
        SecurityCheckResult with is_blocked, risk_level, categories, confidence.
    """
    if not text or not text.strip():
        return SecurityCheckResult(
            is_blocked=False,
            original_input=text or "",
        )

    matched_names: list[str] = []
    matched_categories: list[str] = []
    max_confidence = 0.0
    max_risk = RiskLevel.NONE

    for pattern_def in SECURITY_PATTERNS:
        for compiled in pattern_def["patterns"]:
            if compiled.search(text):
                name = pattern_def["name"]
                category = pattern_def["category"]
                if name not in matched_names:
                    matched_names.append(name)
                if category not in matched_categories:
                    matched_categories.append(category)
                conf = pattern_def["confidence"]
                if conf > max_confidence:
                    max_confidence = conf
                if RISK_PRIORITY.get(pattern_def["risk"], 0) > RISK_PRIORITY.get(max_risk, 0):
                    max_risk = pattern_def["risk"]
                break

    is_blocked = len(matched_names) > 0

    if is_blocked:
        block_reason = (
            f"Input blocked: threat categories={matched_categories}, "
            f"risk={max_risk}, confidence={max_confidence:.2f}"
        )
        logger.warning(
            f"[SECURITY-PATTERNS] {block_reason}, "
            f"patterns={matched_names}, "
            f"input_preview='{text[:80]}'"
        )
    else:
        block_reason = ""

    return SecurityCheckResult(
        is_blocked=is_blocked,
        risk_level=max_risk,
        threat_categories=matched_categories,
        matched_pattern_names=matched_names,
        confidence=max_confidence,
        original_input=text,
        block_reason=block_reason,
    )


def get_block_response(result: SecurityCheckResult, language: str = "pt") -> str:
    """
    Return a safe, non-revealing error message for blocked inputs.

    Args:
        result: SecurityCheckResult from check_input_security.
        language: Response language ("pt" or "en").

    Returns:
        Generic error message that does not leak internal context.
    """
    if language == "en":
        return (
            "I'm unable to process this request. "
            "Please rephrase your message and try again."
        )
    return (
        "Não consigo processar esta solicitação. "
        "Por favor, reformule sua mensagem e tente novamente."
    )


def is_safe_for_agent(text: str) -> bool:
    """
    Quick boolean check: returns True if input is safe to pass to agents.

    Args:
        text: User input.

    Returns:
        True if safe, False if blocked.
    """
    return not check_input_security(text).is_blocked
