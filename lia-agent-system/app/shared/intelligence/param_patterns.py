from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any


class ParamType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    DATE = "date"
    DATE_RANGE = "date_range"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    LIST = "list"
    BOOLEAN = "boolean"
    ENUM = "enum"


@dataclass
class ParamPattern:
    name: str
    patterns: list[str]
    param_type: ParamType
    transform_fn: Callable | None = None
    group_index: int = 1


@dataclass
class ExtractionResult:
    name: str
    value: Any
    raw_match: str
    confidence: float
    source: str = "regex"


def _transform_salary(match):
    raw = match.group(0)
    groups = match.groups()
    if len(groups) >= 2 and groups[1] and groups[1].lower() in ("mil", "k"):
        num = float(groups[0].replace(".", "").replace(",", "."))
        return num * 1000
    value_str = groups[0] if groups else raw
    value_str = value_str.replace(".", "").replace(",", ".")
    try:
        return float(value_str)
    except ValueError:
        return value_str


def _transform_quantity(match):
    groups = match.groups()
    for g in groups:
        if g and g.isdigit():
            return int(g)
    return match.group(0)


def _transform_score(match):
    groups = match.groups()
    for g in groups:
        if g and g.isdigit():
            return int(g)
    return match.group(0)


def _transform_seniority(match):
    raw = match.group(0).lower().strip().rstrip(".")
    mapping = {
        "estagiário": "intern", "estagiária": "intern", "estágio": "intern", "intern": "intern",
        "júnior": "junior", "junior": "junior", "jr": "junior", "jr.": "junior",
        "pleno": "mid", "mid": "mid", "middle": "mid",
        "sênior": "senior", "senior": "senior", "sr": "senior", "sr.": "senior",
        "staff": "staff", "principal": "staff", "lead": "staff",
        "gerente": "management", "manager": "management", "diretor": "management",
        "director": "management", "c-level": "management", "cto": "management",
        "ceo": "management", "cfo": "management",
    }
    return mapping.get(raw, raw)


def _transform_work_model(match):
    raw = match.group(0).lower().strip()
    if raw in ("remoto", "remote") or "home" in raw:
        return "remote"
    if raw in ("presencial", "in loco") or "site" in raw:
        return "onsite"
    if raw in ("híbrido", "hybrid"):
        return "hybrid"
    return raw


def _transform_boolean(match):
    groups = match.groups()
    prefix = groups[0].lower() if groups else ""
    flag = groups[1].lower() if len(groups) > 1 else ""
    if prefix in ("com", "incluir", "inclui"):
        return {flag: True}
    return {flag: False}


SALARY_PATTERNS = ParamPattern(
    name="salary",
    patterns=[
        r"R\$\s*([\d.,]+)",
        r"(\d[\d.]*)\s*(mil|k)\b",
        r"salário\s+(?:de\s+)?R?\$?\s*([\d.,]+)\s*(?:a|até|[-–])\s*R?\$?\s*([\d.,]+)",
        r"faixa\s+(?:salarial\s+)?(?:de\s+)?R?\$?\s*([\d.,]+)",
    ],
    param_type=ParamType.CURRENCY,
    transform_fn=_transform_salary,
    group_index=1,
)

QUANTITY_PATTERNS = ParamPattern(
    name="quantity",
    patterns=[
        r"\b(?:top|melhores?)\s+(\d+)\b",
        r"\b(\d+)\s+(?:candidatos?|vagas?|resultados?)\b",
        r"\blimite?\s+(?:de\s+)?(\d+)\b",
    ],
    param_type=ParamType.INTEGER,
    transform_fn=_transform_quantity,
    group_index=1,
)

SCORE_PATTERNS = ParamPattern(
    name="score",
    patterns=[
        r"\bscore\s+(?:acima\s+de|maior\s+que|>=?|>)\s*(\d+)\b",
        r"\bscore\s+(?:abaixo\s+de|menor\s+que|<=?|<)\s*(\d+)\b",
        r"\b(\d+)\s*%?\s*(?:de\s+)?aderência\b",
    ],
    param_type=ParamType.INTEGER,
    transform_fn=_transform_score,
    group_index=1,
)

SENIORITY_PATTERNS = ParamPattern(
    name="seniority",
    patterns=[
        r"\b(estagiári[oa]|estágio|intern)\b",
        r"\b(júnior|junior|jr\.?)\b",
        r"\b(pleno|mid|middle)\b",
        r"\b(sênior|senior|sr\.?)\b",
        r"\b(staff|principal|lead)\b",
        r"\b(gerente|manager|diretor|director|c-level|cto|ceo|cfo)\b",
    ],
    param_type=ParamType.ENUM,
    transform_fn=_transform_seniority,
    group_index=1,
)

WORK_MODEL_PATTERNS = ParamPattern(
    name="work_model",
    patterns=[
        r"\b(remoto|remote|home\s*office)\b",
        r"\b(presencial|on-?site|in\s*loco)\b",
        r"\b(híbrido|hybrid)\b",
    ],
    param_type=ParamType.ENUM,
    transform_fn=_transform_work_model,
    group_index=1,
)

LOCATION_PATTERNS = ParamPattern(
    name="location",
    patterns=[
        r"\bem\s+(São\s+Paulo|Rio\s+de\s+Janeiro|Belo\s+Horizonte|Curitiba|Porto\s+Alegre|Brasília|Salvador|Recife|Fortaleza|Campinas|Florianópolis)\b",
        r"\bem\s+(\w[\w\s]*?)\s*(?:[-/]|$)",
    ],
    param_type=ParamType.STRING,
    group_index=1,
)

DATE_PATTERNS = ParamPattern(
    name="date",
    patterns=[
        r"\b(hoje|ontem|amanhã)\b",
        r"\b(esta|essa|última|próxima)\s+(semana|mês|quinzena)\b",
        r"\b(?:desde|a\s+partir\s+de)\s+(\w+(?:\s+de\s+\d{4})?)\b",
        r"\b(\d{1,2})\s*(?:de\s+)?(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b",
        r"\b(?:últimos?|nos\s+últimos?)\s+(\d+)\s+(dias?|semanas?|meses?)\b",
    ],
    param_type=ParamType.DATE,
    group_index=1,
)

SKILL_PATTERNS = ParamPattern(
    name="skills",
    patterns=[
        r"\b(python|java|javascript|typescript|react|angular|vue|node\.?js|ruby|go|golang|rust|c\+\+|c#|\.net|php|swift|kotlin|scala|sql|nosql|mongodb|postgresql|mysql|redis|docker|kubernetes|aws|azure|gcp|terraform|ci/?cd|git|agile|scrum|devops|machine\s*learning|deep\s*learning|data\s*science|ai|ml|nlp)\b",
    ],
    param_type=ParamType.LIST,
    group_index=1,
)

BOOLEAN_PATTERNS = ParamPattern(
    name="boolean_flags",
    patterns=[
        r"\b(com|sem)\s+(experiência|formação|certificação|pcd|deficiência)\b",
        r"\b(incluir?|excluir?)\s+(inativos?|arquivados?|rejeitados?)\b",
    ],
    param_type=ParamType.BOOLEAN,
    transform_fn=_transform_boolean,
    group_index=1,
)

DOMAIN_PARAM_PATTERNS: dict[str, list[ParamPattern]] = {
    "sourcing": [QUANTITY_PATTERNS, SKILL_PATTERNS, SENIORITY_PATTERNS, LOCATION_PATTERNS, WORK_MODEL_PATTERNS, SCORE_PATTERNS],
    "job_management": [SALARY_PATTERNS, SENIORITY_PATTERNS, WORK_MODEL_PATTERNS, LOCATION_PATTERNS, SKILL_PATTERNS],
    "cv_screening": [SCORE_PATTERNS, SENIORITY_PATTERNS, SKILL_PATTERNS, QUANTITY_PATTERNS],
    "analytics": [DATE_PATTERNS, QUANTITY_PATTERNS],
    "interview_scheduling": [DATE_PATTERNS],
    "communication": [],
    "ats_integration": [],
    "automation": [DATE_PATTERNS],
    "recruiter_assistant": [DATE_PATTERNS, QUANTITY_PATTERNS],
}

UNIVERSAL_PATTERNS: list[ParamPattern] = [
    SALARY_PATTERNS, QUANTITY_PATTERNS, SCORE_PATTERNS, SENIORITY_PATTERNS,
    WORK_MODEL_PATTERNS, LOCATION_PATTERNS, DATE_PATTERNS, SKILL_PATTERNS, BOOLEAN_PATTERNS,
]


def get_patterns_for_domain(domain_id: str) -> list[ParamPattern]:
    domain_patterns = DOMAIN_PARAM_PATTERNS.get(domain_id, [])
    seen_names = set()
    result = []
    for p in domain_patterns:
        if p.name not in seen_names:
            seen_names.add(p.name)
            result.append(p)
    for p in UNIVERSAL_PATTERNS:
        if p.name not in seen_names:
            seen_names.add(p.name)
            result.append(p)
    return result
