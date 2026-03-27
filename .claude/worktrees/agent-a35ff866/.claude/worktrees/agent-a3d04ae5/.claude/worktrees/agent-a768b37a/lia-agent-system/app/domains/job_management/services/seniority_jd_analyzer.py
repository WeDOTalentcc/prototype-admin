"""
Analisador Determinístico de Senioridade em Descrições de Vagas (JD).

Este módulo extrai indicadores de senioridade a partir do texto de uma
descrição de vaga (Job Description) usando matching de keywords e patterns
regex. É 100% determinístico — NÃO usa LLM ou chamadas externas.

CATEGORIAS DE INDICADORES:
1. Anos de Experiência (regex, PT + EN)
2. Complexidade/Profundidade Técnica
3. Autonomia/Responsabilidade
4. Mentoria/Ensino
5. Requisitos de Formação

LÓGICA DE PONTUAÇÃO:
- Conta indicadores por nível de senioridade
- Anos de experiência têm peso dominante quando explícitos
- Confiança baseada na quantidade de indicadores encontrados
- Nível com mais indicadores vence

Autor: LIA Agent System
Data: 2026-02-11
Versão: 1.0
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

EXPERIENCE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\b(?:até|up\s+to)\s+[12]\s*(?:anos?|years?)\b', re.IGNORECASE), "junior"),
    (re.compile(r'\b[12]\s*[-a]\s*[12]\s*(?:anos?|years?)\b', re.IGNORECASE), "junior"),
    (re.compile(r'\b1\s+to\s+2\s+years?\b', re.IGNORECASE), "junior"),

    (re.compile(r'\b[2-4]\s*[-a]\s*[3-5]\s*(?:anos?|years?)\b', re.IGNORECASE), "pleno"),
    (re.compile(r'\b2\s+to\s+[45]\s+years?\b', re.IGNORECASE), "pleno"),
    (re.compile(r'\b3\s+to\s+5\s+years?\b', re.IGNORECASE), "pleno"),
    (re.compile(r'\b(?:mínimo|minimum|at\s+least)\s+[23]\s*(?:anos?|years?)\b', re.IGNORECASE), "pleno"),

    (re.compile(r'\b[5-7]\s*[-a]\s*[6-8]\s*(?:anos?|years?)\b', re.IGNORECASE), "senior"),
    (re.compile(r'\b5\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "senior"),
    (re.compile(r'\b5\s+to\s+[678]\s+years?\b', re.IGNORECASE), "senior"),
    (re.compile(r'\b(?:mínimo|minimum|at\s+least)\s+5\s*(?:anos?|years?)\b', re.IGNORECASE), "senior"),
    (re.compile(r'\b(?:mínimo|minimum|at\s+least)\s+[67]\s*(?:anos?|years?)\b', re.IGNORECASE), "senior"),

    (re.compile(r'\b[89]\s*[-a]\s*\d{1,2}\s*(?:anos?|years?)\b', re.IGNORECASE), "lead"),
    (re.compile(r'\b[89]\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "lead"),
    (re.compile(r'\b10\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "lead"),
    (re.compile(r'\b1[0-9]\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "executive"),
    (re.compile(r'\b(?:mínimo|minimum|at\s+least)\s+(?:[89]|1[0-9])\s*(?:anos?|years?)\b', re.IGNORECASE), "lead"),
    (re.compile(r'\b10\s+to\s+\d+\s+years?\b', re.IGNORECASE), "executive"),
    (re.compile(r'\b(?:mais\s+de|more\s+than|over)\s+10\s*(?:anos?|years?)\b', re.IGNORECASE), "executive"),
    (re.compile(r'\b15\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "executive"),
    (re.compile(r'\b20\s*\+\s*(?:anos?|years?)\b', re.IGNORECASE), "executive"),
]

GENERIC_EXPERIENCE_PATTERN = re.compile(
    r'(\d+)\s*[\-a+]\s*(\d+)?\s*(?:anos?|years?)',
    re.IGNORECASE,
)

COMPLEXITY_INDICATORS: Dict[str, List[str]] = {
    "junior": [
        "básico", "fundamental", "noções de", "conceitos básicos",
        "introdutório", "basic", "fundamentals", "noções básicas",
        "conhecimento inicial", "familiaridade com",
    ],
    "pleno": [
        "sólido conhecimento", "experiência comprovada", "proven experience",
        "intermediate", "conhecimento intermediário", "bom conhecimento",
        "experiência prática", "hands-on experience", "solid knowledge",
        "proficiency in",
    ],
    "senior": [
        "avançado", "profundo conhecimento", "arquitetura", "design patterns",
        "system design", "distributed systems", "advanced", "expert-level",
        "deep knowledge", "expertise em", "domínio avançado",
        "alto nível de conhecimento", "sistemas distribuídos",
        "microserviços", "microservices", "scalability",
    ],
    "lead": [
        "estratégico", "visão de negócio", "business strategy",
        "go-to-market", "definir roadmap", "technical roadmap",
        "visão estratégica", "strategic vision",
    ],
    "executive": [
        "p&l", "board", "conselho", "governança", "governance",
        "investor relations", "relações com investidores",
        "market strategy", "estratégia de mercado",
    ],
}

AUTONOMY_INDICATORS: Dict[str, List[str]] = {
    "junior": [
        "sob supervisão", "acompanhamento", "orientação de",
        "under supervision", "guided by", "com apoio de",
        "com orientação", "supervisionado",
    ],
    "pleno": [
        "autônomo em tarefas", "independente", "independent",
        "self-directed", "trabalhar de forma autônoma",
        "autonomia nas atividades",
    ],
    "senior": [
        "autonomia total", "tomada de decisão", "full autonomy",
        "decision-making", "ownership", "dono do projeto",
        "responsável por decisões técnicas",
    ],
    "lead": [
        "liderar equipe", "gestão de pessoas", "team management",
        "people leadership", "coordenar time", "liderança de time",
        "gerir equipe", "managing teams", "lead a team",
        "coordenar equipe", "gerenciar equipe",
    ],
    "executive": [
        "definir estratégia", "gestão de orçamento", "budget management",
        "c-level reporting", "report to ceo", "report to board",
        "reportar ao conselho", "definir diretrizes",
        "gestão de p&l", "gerenciar budget",
    ],
}

MENTORSHIP_INDICATORS: Dict[str, List[str]] = {
    "pleno": [
        "contribuir com o time", "compartilhar conhecimento",
        "share knowledge", "contribute to team",
    ],
    "senior": [
        "mentoria", "mentoring juniors", "code review",
        "mentorar", "orientar desenvolvedores", "tech talks",
        "referência técnica", "technical reference",
    ],
    "lead": [
        "desenvolver pessoas", "coaching", "talent development",
        "people development", "desenvolvimento de talentos",
        "formar profissionais", "career development",
    ],
}

EDUCATION_INDICATORS: Dict[str, List[str]] = {
    "junior": [
        "cursando", "formando", "recém-formado", "student",
        "graduating", "em formação", "estudante",
        "recém formado", "newly graduated",
    ],
    "senior": [
        "pós-graduação desejável", "mba desejável",
        "postgraduate preferred", "specialization preferred",
        "especialização desejável",
    ],
    "executive": [
        "mba", "pós-graduação obrigatória", "mba required",
        "mba obrigatório", "mestrado", "doutorado",
        "master's degree", "phd", "doctorate",
    ],
}


def _extract_experience_level(text: str) -> Tuple[Optional[str], List[str]]:
    """
    Extrai o nível de senioridade baseado em anos de experiência mencionados no texto.

    Analisa o texto usando patterns regex para identificar menções a anos de
    experiência em português e inglês. Retorna o nível inferido e as evidências
    textuais encontradas.

    Args:
        text: Texto da descrição da vaga em minúsculas.

    Returns:
        Tupla com (nível inferido ou None, lista de evidências textuais).
    """
    evidence: List[str] = []
    levels_found: List[str] = []

    for pattern, level in EXPERIENCE_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            match_obj = pattern.search(text)
            if match_obj:
                snippet = text[max(0, match_obj.start() - 20):match_obj.end() + 20].strip()
                evidence.append(f"...{snippet}...")
                levels_found.append(level)
                logger.debug("Experience pattern matched: level=%s, snippet='%s'", level, snippet)

    if not levels_found:
        generic_matches = list(GENERIC_EXPERIENCE_PATTERN.finditer(text))
        for match in generic_matches:
            years_start = int(match.group(1))
            years_end = int(match.group(2)) if match.group(2) else None
            snippet = text[max(0, match.start() - 20):match.end() + 20].strip()

            if years_end:
                avg = (years_start + years_end) / 2
            else:
                avg = years_start

            if avg <= 2:
                level = "junior"
            elif avg <= 4:
                level = "pleno"
            elif avg <= 7:
                level = "senior"
            elif avg <= 10:
                level = "lead"
            else:
                level = "executive"

            evidence.append(f"...{snippet}...")
            levels_found.append(level)
            logger.debug(
                "Generic experience pattern matched: years=%s, level=%s",
                f"{years_start}-{years_end}" if years_end else str(years_start),
                level,
            )

    if not levels_found:
        return None, []

    level_counts = Counter(levels_found)
    dominant_level = level_counts.most_common(1)[0][0]
    return dominant_level, evidence


def _find_keyword_indicators(
    text: str,
    indicators_map: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Busca indicadores de keywords no texto e retorna os encontrados por nível.

    Realiza matching case-insensitive de cada keyword contra o texto da vaga.
    Agrupa os indicadores encontrados pelo nível de senioridade correspondente.

    Args:
        text: Texto da descrição da vaga em minúsculas.
        indicators_map: Dicionário mapeando nível -> lista de keywords.

    Returns:
        Dicionário com nível -> lista de keywords encontradas no texto.
    """
    found: Dict[str, List[str]] = {}
    for level, keywords in indicators_map.items():
        matched = []
        for keyword in keywords:
            if keyword.lower() in text:
                matched.append(keyword)
        if matched:
            found[level] = matched
    return found


def _calculate_confidence(total_indicators: int) -> float:
    """
    Calcula a confiança baseada na quantidade total de indicadores encontrados.

    Usa escala fixa:
    - 1 indicador: 0.50
    - 2-3 indicadores: 0.65
    - 4-5 indicadores: 0.80
    - 6+ indicadores: 0.90

    Args:
        total_indicators: Número total de indicadores encontrados.

    Returns:
        Valor de confiança entre 0.0 e 1.0.
    """
    if total_indicators <= 0:
        return 0.0
    if total_indicators == 1:
        return 0.50
    if total_indicators <= 3:
        return 0.65
    if total_indicators <= 5:
        return 0.80
    return 0.90


def analyze_jd_for_seniority(job_description: str) -> Dict[str, Any]:
    """
    Analisa o texto de uma descrição de vaga para extrair sinais de senioridade.

    100% determinístico — usa matching de keywords e patterns regex.
    NÃO usa LLM ou chamadas externas.

    Categorias analisadas:
    1. Anos de experiência (regex patterns em PT e EN)
    2. Complexidade e profundidade técnica
    3. Autonomia e responsabilidade
    4. Mentoria e ensino
    5. Requisitos de formação/educação

    A lógica de pontuação conta indicadores por nível, com anos de experiência
    tendo peso dominante quando explicitamente mencionados. O nível com mais
    indicadores vence, e a confiança é calculada pela quantidade total.

    Args:
        job_description: Texto completo da descrição da vaga.

    Returns:
        Dicionário com as chaves:
        - level: Optional[str] - "junior" | "pleno" | "senior" | "lead" | "executive" | None
        - confidence: float - 0.0 a 1.0
        - evidence: List[str] - trechos de texto que suportam a inferência
        - indicators: Dict[str, List[str]] - indicadores encontrados por categoria
    """
    if not job_description or not job_description.strip():
        logger.warning("Empty job description provided for seniority analysis")
        return {
            "level": None,
            "confidence": 0.0,
            "evidence": [],
            "indicators": {},
        }

    text = job_description.lower()
    all_evidence: List[str] = []
    all_indicators: Dict[str, List[str]] = {}
    level_scores: Counter = Counter()

    experience_level, experience_evidence = _extract_experience_level(text)
    experience_weight = 0
    if experience_level:
        all_evidence.extend(experience_evidence)
        all_indicators["years_of_experience"] = experience_evidence
        experience_weight = 3
        level_scores[experience_level] += experience_weight
        logger.info(
            "JD experience analysis: level=%s, evidence_count=%d",
            experience_level,
            len(experience_evidence),
        )

    category_maps = [
        ("complexity", COMPLEXITY_INDICATORS),
        ("autonomy", AUTONOMY_INDICATORS),
        ("mentorship", MENTORSHIP_INDICATORS),
        ("education", EDUCATION_INDICATORS),
    ]

    for category_name, indicator_map in category_maps:
        found = _find_keyword_indicators(text, indicator_map)
        if found:
            category_keywords: List[str] = []
            for level, keywords in found.items():
                level_scores[level] += len(keywords)
                category_keywords.extend(keywords)
                for kw in keywords:
                    all_evidence.append(f"[{category_name}] {kw}")
            all_indicators[category_name] = category_keywords
            logger.debug(
                "JD category '%s': found %d indicators across %d levels",
                category_name,
                len(category_keywords),
                len(found),
            )

    total_indicators = sum(level_scores.values())

    if total_indicators == 0:
        logger.info("JD analysis: no seniority indicators found")
        return {
            "level": None,
            "confidence": 0.0,
            "evidence": [],
            "indicators": {},
        }

    resolved_level = level_scores.most_common(1)[0][0]
    raw_indicator_count = total_indicators - (experience_weight - 1 if experience_level else 0)
    confidence = _calculate_confidence(raw_indicator_count)

    logger.info(
        "JD seniority analysis result: level=%s, confidence=%.2f, "
        "total_indicators=%d, scores=%s",
        resolved_level,
        confidence,
        total_indicators,
        dict(level_scores),
    )

    return {
        "level": resolved_level,
        "confidence": confidence,
        "evidence": all_evidence,
        "indicators": all_indicators,
    }
