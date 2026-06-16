"""
WSI Deterministic Scorer - Cálculos 100% determinísticos para scores WSI.

IMPORTANTE: Este serviço NÃO usa LLM para cálculos de score.
Os scores são calculados com fórmulas fixas e reproduzíveis.

O LLM pode ser usado APENAS para:
- Extração de informações estruturadas do texto
- Classificação de evidências

O CÁLCULO FINAL é sempre determinístico.
"""
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

BLOOM_LEVELS = {
    1: {"name": "Recordar", "description": "Recordar fatos e conceitos básicos", 
        "indicators": ["lembro", "sei", "conheço", "aprendi", "estudei", "vi", "ouvi"]},
    2: {"name": "Compreender", "description": "Explicar ideias ou conceitos", 
        "indicators": ["entendo", "explico", "compreendo", "descrevo", "interpreto", "resumo"]},
    3: {"name": "Aplicar", "description": "Usar conhecimento na prática", 
        "indicators": ["aplico", "uso", "implemento", "desenvolvo", "construo", "projeto", "faço"]},
    4: {"name": "Analisar", "description": "Fazer conexões entre ideias", 
        "indicators": ["analiso", "comparo", "diferencio", "diagnostico", "investigo", "otimizo"]},
    5: {"name": "Avaliar", "description": "Justificar decisões", 
        "indicators": ["avalio", "julgo", "recomendo", "decido", "valido", "defendo", "escolhi"]},
    6: {"name": "Criar", "description": "Produzir trabalho original", 
        "indicators": ["crio", "arquiteto", "projeto", "inovo", "lidero", "fundei", "desenvolvi do zero"]}
}

DREYFUS_LEVELS = {
    1: {"name": "Iniciante",    "description": "Segue regras rígidas",           "years_range": (0, 1)},
    2: {"name": "Básico",       "description": "Reconhece aspectos situacionais", "years_range": (1, 2)},
    3: {"name": "Intermediário","description": "Planeja e prioriza",              "years_range": (2, 3)},
    4: {"name": "Avançado",     "description": "Visão holística",                 "years_range": (3, 5)},
    5: {"name": "Especialista", "description": "Intuição transcende análise",     "years_range": (5, 99)}
}

from app.domains.cv_screening.constants.wsi_constants import (
    BLOOM_LEVEL_LABELS as BLOOM_RECRUITER_LABELS,
)
from app.domains.cv_screening.constants.wsi_constants import (
    DREYFUS_STAGE_LABELS as DREYFUS_RECRUITER_LABELS,
)

BIG_FIVE_RECRUITER_LABELS = {
    "openness":          "Abertura a mudanças",
    "conscientiousness": "Organização e disciplina",
    "extraversion":      "Sociabilidade",
    "agreeableness":     "Cooperação",
    "stability":         "Estabilidade emocional",
}

SENIORITY_WEIGHTS = {
    "estagiario": {"technical": 0.6875, "behavioral": 0.3125},
    "junior":     {"technical": 0.625,  "behavioral": 0.375},
    "pleno":      {"technical": 0.6875, "behavioral": 0.3125},
    "senior":     {"technical": 0.5625, "behavioral": 0.4375},
    "lead":       {"technical": 0.4375, "behavioral": 0.5625},
    "principal":  {"technical": 0.50,   "behavioral": 0.50},
    "diretor":    {"technical": 0.3125, "behavioral": 0.6875},
    "vp_clevel":  {"technical": 0.25,   "behavioral": 0.75},
    "executive":  {"technical": 0.3125, "behavioral": 0.6875},
    "staff":      {"technical": 0.5625, "behavioral": 0.4375},
}

# Spec F8 — fórmula tri-componente por tipo de pergunta (v2)
WSI_FORMULA_WEIGHTS_TECHNICAL = {
    "autodeclaracao":    0.35,
    "evidencias_tecnicas": 0.40,
    "bloom_alinhamento": 0.25,
}

WSI_FORMULA_WEIGHTS_BEHAVIORAL = {
    "star_estrutura":    0.35,
    "sinais_trait":      0.40,
    "bloom_alinhamento": 0.25,
}

# Mantido para retrocompatibilidade — não usar em código novo
WSI_FORMULA_WEIGHTS = {
    "autodeclaracao": 0.60,
    "contexto": 0.40,
}

# Pesos S/T/A/R conforme spec F8 (A tem maior peso por ser a ação concreta)
STAR_COMPONENT_WEIGHTS = {"S": 0.20, "T": 0.20, "A": 0.40, "R": 0.20}

STAR_INDICATORS = {
    "S": ["estava trabalhando", "naquela época", "no contexto", "situação era", "momento era",
          "quando eu", "enquanto eu", "naquele projeto", "naquele período", "no cenário"],
    "T": ["minha tarefa", "meu objetivo", "deveria", "precisava", "responsabilidade era",
          "fui designado", "me pediram", "o desafio era", "precisávamos", "o requisito"],
    "A": ["então fiz", "decidi", "implementei", "executei", "apliquei", "criei", "desenvolvi",
          "propus", "sugeri", "atuei", "conduzi", "liderei", "corrigi", "resolvi", "refatorei"],
    "R": ["resultado", "conseguimos", "atingimos", "reduzimos", "aumentamos", "melhoramos",
          "entregamos", "economizamos", "impacto foi", "ficou", "passou a", "hoje está"],
}

WSI_CUTOFFS = {
    "approved_auto": 3.75,
    "review_min":    3.00,
    "rejected_below": 3.00,
    "rejected_max": 3.00,
}

GATE_G3_THRESHOLD = 2.0

CONTEXT_INDICATORS = {
    "high_quality": [
        "milhões", "milhares", "percentual", "%", "reduzimos", "aumentamos",
        "métricas", "kpi", "produção", "escala", "enterprise", "liderança",
        "arquitetura", "decisão", "impacto", "resultado", "otimização"
    ],
    "medium_quality": [
        "projeto", "equipe", "implementei", "desenvolvi", "trabalhei",
        "cliente", "api", "sistema", "banco de dados", "deploy"
    ],
    "low_quality": [
        "curso", "tutorial", "estudando", "aprendendo", "básico",
        "iniciante", "teoria", "acadêmico"
    ]
}

PENALTY_TRIGGERS = {
    "inflation": {
        "keywords": ["expert", "especialista", "domino completamente", "5 de 5", "nível máximo"],
        "penalty": -1.0
    },
    "generic": {
        "keywords": ["trabalhei com isso", "tenho experiência", "já fiz", "sei fazer"],
        "penalty": -0.5
    },
    "no_context": {
        "min_words": 20,
        "penalty": -0.3
    }
}

BONUS_TRIGGERS = {
    "humility": {
        "keywords": ["ainda estou aprendendo", "preciso melhorar", "3 de 5", "intermediário"],
        "bonus": 0.5
    },
    "exceptional_evidence": {
        "keywords": ["open source", "contribuí", "palestrei", "publiquei", "patente", "prêmio"],
        "bonus": 0.3
    }
}


@dataclass
class DeterministicWSIResult:
    """Resultado do cálculo determinístico WSI."""
    autodeclaracao_score: float
    context_score: float
    bloom_level: int
    bloom_name: str
    dreyfus_level: int
    dreyfus_name: str
    evidences: list[str]
    red_flags: list[str]
    penalty: float
    bonus: float
    final_score: float
    formula_applied: str
    justification: str
    # v2 — fórmula tri-componente (spec F8)
    formula_version: str = "v2"
    star_components: dict[str, bool] | None = None   # S/T/A/R presentes
    star_score: float = 0.0                             # score ponderado STAR
    bloom_alignment: float = 1.0                        # alinhamento bloom demonstrado vs esperado
    flags_structured: dict[str, bool] | None = None  # is_inflation/is_generic/is_short


def extract_autodeclaracao_score(text: str) -> float | None:
    """
    Extrai score de autodeclaração do texto.
    
    Patterns detectados:
    - "4 de 5", "4/5", "nota 4"
    - "intermediário", "avançado", "básico"
    - "domino bem", "tenho facilidade"
    """
    text_lower = text.lower()
    
    patterns = [
        (r"(\d)[/\s]?de[/\s]?5", lambda m: float(m.group(1))),
        (r"nota\s*(\d)", lambda m: float(m.group(1))),
        (r"(\d)/5", lambda m: float(m.group(1))),
        (r"nível\s*(\d)", lambda m: float(m.group(1))),
    ]
    
    for pattern, extractor in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return extractor(match)
    
    level_keywords = {
        5.0: ["expert", "especialista", "domínio completo", "mestre", "5 de 5"],
        4.0: ["avançado", "domino bem", "proficiente", "sólido", "4 de 5"],
        3.0: ["intermediário", "razoável", "competente", "3 de 5"],
        2.0: ["básico", "iniciante", "aprendendo", "2 de 5"],
        1.0: ["muito básico", "nunca usei", "não tenho experiência", "1 de 5"]
    }
    
    for score, keywords in level_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return score
    
    return None


def calculate_context_score(text: str, evidences: list[str] | None = None) -> float:
    """
    Calcula score de contexto baseado em indicadores determinísticos.
    
    Returns: Score de 1.0 a 5.0
    """
    text_lower = text.lower()
    score = 3.0
    
    high_count = sum(1 for ind in CONTEXT_INDICATORS["high_quality"] if ind in text_lower)
    medium_count = sum(1 for ind in CONTEXT_INDICATORS["medium_quality"] if ind in text_lower)
    low_count = sum(1 for ind in CONTEXT_INDICATORS["low_quality"] if ind in text_lower)
    
    if high_count >= 3:
        score = 5.0
    elif high_count >= 1:
        score = 4.0 + (high_count * 0.2)
    elif medium_count >= 3:
        score = 3.5
    elif medium_count >= 1:
        score = 3.0 + (medium_count * 0.1)
    
    if low_count >= 2:
        score = max(1.0, score - 1.0)
    elif low_count >= 1:
        score = max(1.5, score - 0.5)
    
    if evidences:
        evidence_boost = min(0.5, len(evidences) * 0.1)
        score += evidence_boost
    
    return min(5.0, max(1.0, round(score, 2)))


def calculate_bloom_level(text: str) -> tuple[int, str]:
    """
    Classifica nível Bloom baseado em indicadores de texto.
    
    Returns: (level, name)
    """
    text_lower = text.lower()
    detected_level = 1
    
    for level in range(6, 0, -1):
        level_data = BLOOM_LEVELS[level]
        for indicator in level_data["indicators"]:
            if indicator in text_lower:
                detected_level = max(detected_level, level)
                break
    
    return detected_level, BLOOM_LEVELS[detected_level]["name"]


def calculate_dreyfus_level(
    years_experience: float,
    context_score: float,
    years_reference: dict[str, tuple[float, float]] | None = None,
) -> tuple[int, str]:
    """
    Classifica nível Dreyfus baseado em anos de experiência e qualidade do contexto.
    
    Args:
        years_experience: Anos de experiência do candidato
        context_score: Score de contexto (1-5)
        years_reference: Ranges contextuais do calibrador (ex: {"junior": (0,2), "pleno": (2,4), ...}).
                         Se None, usa DREYFUS_LEVELS estáticos.
    
    Returns: (level, name)
    """
    base_level = 1

    if years_reference:
        seniority_to_dreyfus_map = {
            "junior": 2,
            "pleno": 3,
            "senior": 4,
            "specialist": 5,
            "lead": 5,
            "executive": 5,
            "trainee": 1,
            "intern": 1,
        }
        for seniority_key, (min_y, max_y) in years_reference.items():
            if min_y <= years_experience < max_y:
                base_level = seniority_to_dreyfus_map.get(seniority_key, 3)
                break
        else:
            max_key = max(years_reference.keys(), key=lambda k: years_reference[k][1])
            if years_experience >= years_reference[max_key][1]:
                base_level = seniority_to_dreyfus_map.get(max_key, 5)
    else:
        for level, data in DREYFUS_LEVELS.items():
            min_years, max_years = data["years_range"]
            if min_years <= years_experience < max_years:
                base_level = level
                break
    
    if context_score >= 4.5:
        base_level = min(5, base_level + 1)
    elif context_score < 2.5:
        base_level = max(1, base_level - 1)
    
    return base_level, DREYFUS_LEVELS[base_level]["name"]


def extract_years_experience(text: str) -> float:
    """
    Extrai anos de experiência do texto.
    
    Returns: Anos de experiência (default 2.0 se não encontrado)
    """
    text_lower = text.lower()
    
    patterns = [
        (r"(\d+)\s*anos?\s*(?:de\s*)?(?:experiência|exp)", lambda m: float(m.group(1))),
        (r"há\s*(\d+)\s*anos?", lambda m: float(m.group(1))),
        (r"(\d+)\s*anos?\s*(?:trabalhando|desenvolvendo)", lambda m: float(m.group(1))),
        (r"experiência\s*(?:de\s*)?(\d+)\s*anos?", lambda m: float(m.group(1))),
    ]
    
    for pattern, extractor in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return min(20.0, extractor(match))
    
    return 2.0


def detect_red_flags(
    text: str,
    autodeclaracao: float | None,
    context_score: float,
    *,
    layer2=None,
) -> list[str]:
    """
    Detecta red flags na resposta.

    Args:
        layer2: Layer2Signals optional. When provided and layer2.semantic_inflation
                is True, emits the semantic flag (M06) and suppresses the lexical
                inflation heuristic to avoid double-flagging.

    Returns: Lista de red flags detectados
    """
    red_flags = []
    text_lower = text.lower()

    # M06 — Layer2 semantic inflation takes priority over lexical heuristic.
    if layer2 is not None:
        if getattr(layer2, "semantic_inflation", False):
            red_flags.append("Inflação semântica detectada (Layer 2)")
            # Do NOT fall through to lexical inflation check.
        else:
            # Layer2 says no inflation — still apply lexical if thresholds met
            from app.domains.cv_screening.constants.wsi_scale import (
                INFLATION_AUTODECLARATION_MIN, INFLATION_CONTEXT_MAX,
            )
            if (
                autodeclaracao is not None
                and autodeclaracao >= INFLATION_AUTODECLARATION_MIN
                and context_score < INFLATION_CONTEXT_MAX
            ):
                red_flags.append("Inflação de score: autodeclaração alta, contexto fraco")
    else:
        from app.domains.cv_screening.constants.wsi_scale import INFLATION_AUTODECLARATION_MIN, INFLATION_CONTEXT_MAX
        if autodeclaracao is not None and autodeclaracao >= INFLATION_AUTODECLARATION_MIN and context_score < INFLATION_CONTEXT_MAX:
            red_flags.append("Inflação de score: autodeclaração alta, contexto fraco")
    
    if len(text.split()) < PENALTY_TRIGGERS["no_context"]["min_words"]:
        red_flags.append("Resposta muito curta, falta contexto")
    
    generic_count = sum(1 for kw in PENALTY_TRIGGERS["generic"]["keywords"] if kw in text_lower)
    if generic_count >= 2 and len(text.split()) < 50:
        red_flags.append("Resposta genérica sem detalhes específicos")
    
    return red_flags


def calculate_penalty(text: str, autodeclaracao: float | None, context_score: float, *, layer2=None, expects_first_person: bool = False) -> float:
    """
    Calcula penalidade determinística.
    
    Returns: Valor negativo da penalidade
    """
    penalty = 0.0
    text_lower = text.lower()
    
    if autodeclaracao and autodeclaracao >= 4.5 and context_score < 3.0:
        penalty += PENALTY_TRIGGERS["inflation"]["penalty"]
    
    generic_count = sum(1 for kw in PENALTY_TRIGGERS["generic"]["keywords"] if kw in text_lower)
    if generic_count >= 2:
        penalty += PENALTY_TRIGGERS["generic"]["penalty"]
    
    if len(text.split()) < PENALTY_TRIGGERS["no_context"]["min_words"]:
        penalty += PENALTY_TRIGGERS["no_context"]["penalty"]
    
    # M04+M06 — Camada 2 signals (semantic + structural penalties)
    if layer2 is not None:
        from app.domains.cv_screening.constants.wsi_scale import (
            PENALTY_PARAPHRASE, PENALTY_LANGUAGE_MISMATCH, PENALTY_MISSING_R_OUTCOME,
            PENALTY_NO_FIRST_PERSON, PENALTY_WORD_BAND_VERY_SHORT, PENALTY_WORD_BAND_SHORT,
        )
        # Paraphrase — repeats question without adding content
        if getattr(layer2, "is_paraphrase", False):
            penalty += PENALTY_PARAPHRASE

        # Language mismatch
        if not getattr(layer2, "language_consistency", True):
            penalty += PENALTY_LANGUAGE_MISMATCH

        # Missing R-outcome (STAR without result)
        if not getattr(layer2, "has_R_outcome", True):
            penalty += PENALTY_MISSING_R_OUTCOME

        # No first-person — only penalizes in behavioral context
        if not getattr(layer2, "is_first_person", True) and expects_first_person:
            penalty += PENALTY_NO_FIRST_PERSON

        # Word band penalties (avoid double-charging with lexical no_context gate)
        word_band = getattr(layer2, "word_count_band", "50-150") or "50-150"
        word_count = len(text.split())
        lexical_no_context_gate = PENALTY_TRIGGERS["no_context"]["min_words"]  # typically 20
        if word_band == "<30":
            # Only add band penalty if lexical no_context hasn't already fired
            if word_count >= lexical_no_context_gate:
                penalty += PENALTY_WORD_BAND_VERY_SHORT
        elif word_band == "30-50":
            penalty += PENALTY_WORD_BAND_SHORT

        # M06 — semantic inflation (already handled lexically above; add here if layer2 signals it)
        if getattr(layer2, "semantic_inflation", False):
            # Inflation already handled by lexical heuristic unless layer2 is explicitly set
            pass  # semantic inflation captured by detect_red_flags, not double-charged here

    return round(penalty, 2)


def calculate_bonus(
    text: str,
    *,
    layer2=None,
    dreyfus_expected: int | None = None,
    trait_signals_expected: int | None = None,
    is_behavioral: bool = False,
    bloom_expected: int | None = None,
) -> float:
    """
    Calcula bônus determinístico.

    M05 — Layer2 spec adjustments:
      - has_quantification → BONUS_QUANTIFICATION
      - dreyfus_demonstrated > dreyfus_expected → BONUS_DREYFUS_EXCEEDS
      - dreyfus_demonstrated < dreyfus_expected-1 → PENALTY_DREYFUS_BELOW
      - is_behavioral + trait_signals_count==0 → PENALTY_NO_TRAIT_SIGNALS
      - bloom_demonstrated > bloom_expected → BONUS_BLOOM_EXCEEDS
      - trait_signals_count > trait_signals_expected → BONUS_TRAIT_SIGNALS_EXCEED

    Returns: Float (positive bonus minus spec-driven penalties)
    """
    bonus = 0.0
    text_lower = text.lower()

    humility_count = sum(1 for kw in BONUS_TRIGGERS["humility"]["keywords"] if kw in text_lower)
    if humility_count >= 1:
        bonus += BONUS_TRIGGERS["humility"]["bonus"]

    exceptional_count = sum(1 for kw in BONUS_TRIGGERS["exceptional_evidence"]["keywords"] if kw in text_lower)
    if exceptional_count >= 1:
        bonus += BONUS_TRIGGERS["exceptional_evidence"]["bonus"]

    # M05 — Camada 2 spec adjustments
    if layer2 is not None:
        from app.domains.cv_screening.constants.wsi_scale import (
            BONUS_QUANTIFICATION, BONUS_DREYFUS_EXCEEDS, BONUS_BLOOM_EXCEEDS,
            BONUS_TRAIT_SIGNALS_EXCEED, PENALTY_DREYFUS_BELOW, PENALTY_NO_TRAIT_SIGNALS,
        )
        # Quantification bonus
        if getattr(layer2, "has_quantification", False):
            bonus += BONUS_QUANTIFICATION

        # Dreyfus level adjustments (spec §F8.3-M05)
        dreyfus_demo = getattr(layer2, "dreyfus_demonstrated", None)
        if dreyfus_demo is not None and dreyfus_expected is not None:
            if dreyfus_demo > dreyfus_expected:
                bonus += BONUS_DREYFUS_EXCEEDS
            elif dreyfus_demo < dreyfus_expected - 1:
                bonus += PENALTY_DREYFUS_BELOW  # negative value

        # Bloom exceeds expected
        bloom_demo = getattr(layer2, "bloom_demonstrated", None)
        if bloom_demo is not None and bloom_expected is not None:
            if bloom_demo > bloom_expected:
                bonus += BONUS_BLOOM_EXCEEDS

        # Trait signals
        trait_count = getattr(layer2, "trait_signals_count", 0)
        if is_behavioral and trait_count == 0:
            bonus += PENALTY_NO_TRAIT_SIGNALS  # negative value
        if trait_signals_expected is not None and trait_count > trait_signals_expected:
            bonus += BONUS_TRAIT_SIGNALS_EXCEED

    from app.domains.cv_screening.constants.wsi_scale import BONUS_MAX
    return round(min(BONUS_MAX, bonus), 2)


def extract_evidences(text: str) -> list[str]:
    """
    Extrai evidências do texto de forma determinística.
    
    Returns: Lista de evidências encontradas
    """
    evidences = []
    text_lower = text.lower()
    
    tech_patterns = [
        r"(?:python|java|javascript|typescript|react|angular|vue|node|fastapi|django|flask)",
        r"(?:postgresql|mysql|mongodb|redis|elasticsearch)",
        r"(?:aws|azure|gcp|docker|kubernetes|k8s)",
        r"(?:api|rest|graphql|microserviços|microsserviços)"
    ]
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        evidences.extend(set(matches))
    
    metric_patterns = [
        r"(\d+%\s*(?:de\s*)?(?:redução|aumento|melhoria|cobertura|coverage))",
        r"(reduz\w*\s*(?:de\s*)?\d+\s*(?:ms|s|segundos))",
        r"(atend\w*\s*\d+\s*(?:mil|milhões|usuários|clientes|requisições))",
    ]
    
    for pattern in metric_patterns:
        matches = re.findall(pattern, text_lower)
        evidences.extend(matches)
    
    return list(set(evidences))[:10]


def calculate_star_score(text: str) -> tuple[dict[str, bool], float]:
    """
    Detecta componentes STAR na resposta e calcula score ponderado.
    Spec F8 — pesos: S=0.20, T=0.20, A=0.40, R=0.20

    Returns:
        (components_dict, weighted_score_0_to_1)
    """
    text_lower = text.lower()
    components: dict[str, bool] = {}
    for component, indicators in STAR_INDICATORS.items():
        components[component] = any(ind in text_lower for ind in indicators)

    score = sum(
        STAR_COMPONENT_WEIGHTS[c] for c, present in components.items() if present
    )
    return components, round(score, 3)


def calculate_bloom_alignment(bloom_demonstrated: int, bloom_expected: int) -> float:
    """
    Calcula alinhamento entre nível Bloom demonstrado e esperado (0.0–1.0).
    Spec F8 — componente bloom_alinhamento.

    alignment = 1.0 - |demonstrated - expected| / max_distance
    max_distance = 5 (range 1–6)
    """
    max_distance = 5
    alignment = 1.0 - abs(bloom_demonstrated - bloom_expected) / max_distance
    return round(max(0.0, alignment), 3)


def calculate_wsi_deterministic(
    response_text: str,
    competency_name: str = "",
    question_framework: str = "CBI",
    autodeclaracao_override: float | None = None,
    contexto_override: float | None = None,
    years_experience: float | None = None,
    years_reference: dict[str, tuple[float, float]] | None = None,
    question_type: str = "technical",   # "technical" | "behavioral"
    bloom_expected: int = 3,            # nível Bloom esperado pela pergunta
    layer2_signals=None,                # Optional[Layer2Signals] — M04/M05/M06
    dreyfus_expected: int | None = None,          # nível Dreyfus esperado
    trait_signals_expected: int | None = None,    # qtd traits esperados
) -> DeterministicWSIResult:
    """
    Calcula WSI de forma 100% determinística — Spec F8 fórmula v2.

    Fórmula técnica:   0.35×autodeclaracao + 0.40×evidencias_tecnicas + 0.25×bloom_alinhamento
    Fórmula comportamental: 0.35×star_estrutura + 0.40×sinais_trait   + 0.25×bloom_alinhamento
    Penalidades e bônus aplicados ao resultado final.

    Args:
        response_text:           Texto da resposta do candidato
        competency_name:         Nome da competência avaliada
        question_framework:      Framework usado (CBI, Dreyfus, BigFive, etc.)
        autodeclaracao_override: Override do score de autodeclaração
        contexto_override:       Override do score de contexto
        years_experience:        Anos de experiência para cálculo Dreyfus
        years_reference:         Ranges de senioridade para calibração Dreyfus
        question_type:           "technical" usa evidências; "behavioral" usa STAR
        bloom_expected:          Nível Bloom esperado pela pergunta (1–6)

    Returns:
        DeterministicWSIResult com todos os componentes do cálculo
    """
    if autodeclaracao_override is not None:
        autodeclaracao = autodeclaracao_override
    else:
        autodeclaracao = extract_autodeclaracao_score(response_text)

    evidences = extract_evidences(response_text)

    if contexto_override is not None:
        context_score = contexto_override
    else:
        context_score = calculate_context_score(response_text, evidences)

    if autodeclaracao is None:
        autodeclaracao = context_score

    bloom_level, bloom_name = calculate_bloom_level(response_text)
    bloom_align = calculate_bloom_alignment(bloom_level, bloom_expected)

    years = years_experience if years_experience is not None else extract_years_experience(response_text)
    dreyfus_level, dreyfus_name = calculate_dreyfus_level(years, context_score, years_reference=years_reference)

    red_flags = detect_red_flags(response_text, autodeclaracao, context_score, layer2=layer2_signals)

    # Flags estruturadas para G6 (spec F10)
    is_prompt_injection = (
        layer2_signals is not None
        and getattr(layer2_signals, "prompt_injection_detected", False)
    )
    is_semantic_inflation = (
        layer2_signals is not None
        and getattr(layer2_signals, "semantic_inflation", False)
    )
    flags_structured: dict[str, bool] = {
        "is_inflation": autodeclaracao >= 4.5 and context_score < 3.0,
        "is_generic": sum(1 for kw in PENALTY_TRIGGERS["generic"]["keywords"]
                         if kw in response_text.lower()) >= 2,
        "is_short": len(response_text.split()) < PENALTY_TRIGGERS["no_context"]["min_words"],
    }
    if is_prompt_injection:
        flags_structured["is_prompt_injection"] = True
    if is_semantic_inflation:
        flags_structured["is_semantic_inflation"] = True

    # M04 — prompt injection override: final_score = PROMPT_INJECTION_OVERRIDE_SCORE
    if is_prompt_injection:
        from app.domains.cv_screening.constants.wsi_scale import PROMPT_INJECTION_OVERRIDE_SCORE
        return DeterministicWSIResult(
            autodeclaracao_score=autodeclaracao,
            context_score=context_score,
            bloom_level=0,
            bloom_name="N/A",
            dreyfus_level=0,
            dreyfus_name="N/A",
            evidences=[],
            red_flags=["prompt-injection detectado (Layer 2)"],
            penalty=0.0,
            bonus=0.0,
            final_score=PROMPT_INJECTION_OVERRIDE_SCORE,
            formula_applied="prompt_injection_override",
            justification="Resposta bloqueada: injeção de prompt detectada.",
            formula_version="v2",
            star_components={},
            star_score=0.0,
            bloom_alignment=0.0,
            flags_structured=flags_structured,
        )

    # Dreyfus branch — fórmula canônica: 0.60×autodeclaracao + 0.40×context_score
    # Não aplica STAR nem Bloom (autodeclaração é naturalmente concisa)
    if question_framework.lower() == "dreyfus":
        dreyfus_raw = 0.60 * autodeclaracao + 0.40 * context_score
        dreyfus_penalty = -0.5 if (autodeclaracao >= 4.5 and context_score < 3.0) else 0.0
        final_dreyfus = max(1.0, min(5.0, dreyfus_raw + dreyfus_penalty))
        final_dreyfus = round(final_dreyfus, 2)
        dreyfus_formula = (
            f"dreyfus: 0.60×auto{autodeclaracao:.1f} + 0.40×ctx{context_score:.1f}"
        )
        if dreyfus_penalty:
            dreyfus_formula += f" + penalty({dreyfus_penalty}) [inflation]"
        dreyfus_formula += f" = {final_dreyfus:.2f}"
        return DeterministicWSIResult(
            autodeclaracao_score=autodeclaracao,
            context_score=context_score,
            bloom_level=bloom_level,
            bloom_name=bloom_name,
            dreyfus_level=dreyfus_level,
            dreyfus_name=dreyfus_name,
            evidences=evidences,
            red_flags=red_flags,
            penalty=dreyfus_penalty,
            bonus=0.0,
            final_score=final_dreyfus,
            formula_applied=dreyfus_formula,
            justification=f"Dreyfus autodeclaração: {dreyfus_name}. Contexto: {context_score:.1f}/5.",
            formula_version="v2-dreyfus",
            star_components={},
            star_score=0.0,
            bloom_alignment=bloom_align,
            flags_structured=flags_structured,
        )

        is_behavioral = question_type == "behavioral"
    penalty = calculate_penalty(
        response_text, autodeclaracao, context_score,
        layer2=layer2_signals,
        expects_first_person=is_behavioral,
    )
    bonus = calculate_bonus(
        response_text,
        layer2=layer2_signals,
        dreyfus_expected=dreyfus_expected,
        trait_signals_expected=trait_signals_expected,
        is_behavioral=is_behavioral,
        bloom_expected=bloom_expected,
    )

    # Fórmula v2 — tri-componente por tipo (Spec F8)
    if question_type == "behavioral":
        star_components, star_score = calculate_star_score(response_text)
        # sinais_trait ≈ context_score (qualidade do contexto comportamental)
        weights = WSI_FORMULA_WEIGHTS_BEHAVIORAL
        raw_score = (
            weights["star_estrutura"]    * (star_score * 5.0) +  # normaliza 0–1 → 0–5
            weights["sinais_trait"]      * context_score +
            weights["bloom_alinhamento"] * (bloom_align * 5.0)   # normaliza 0–1 → 0–5
        )
        formula_desc = (
            f"behavioral: ({weights['star_estrutura']}×STAR{star_score:.2f}×5) + "
            f"({weights['sinais_trait']}×ctx{context_score:.1f}) + "
            f"({weights['bloom_alinhamento']}×bloom{bloom_align:.2f}×5)"
        )
    else:
        star_components, star_score = {}, 0.0
        # evidencias_tecnicas ≈ context_score (qualidade técnica das evidências)
        weights = WSI_FORMULA_WEIGHTS_TECHNICAL
        raw_score = (
            weights["autodeclaracao"]      * autodeclaracao +
            weights["evidencias_tecnicas"] * context_score +
            weights["bloom_alinhamento"]   * (bloom_align * 5.0)
        )
        formula_desc = (
            f"technical: ({weights['autodeclaracao']}×auto{autodeclaracao:.1f}) + "
            f"({weights['evidencias_tecnicas']}×ctx{context_score:.1f}) + "
            f"({weights['bloom_alinhamento']}×bloom{bloom_align:.2f}×5)"
        )

    final_score = max(1.0, min(5.0, raw_score + penalty + bonus))
    final_score = round(final_score, 2)
    formula = f"{formula_desc} + penalty({penalty}) + bonus({bonus}) = {final_score:.2f}"

    justification_parts = []
    if context_score >= 4.0:
        justification_parts.append(f"Contexto forte ({context_score:.1f}/5)")
    elif context_score >= 3.0:
        justification_parts.append(f"Contexto adequado ({context_score:.1f}/5)")
    else:
        justification_parts.append(f"Contexto fraco ({context_score:.1f}/5)")

    justification_parts.append(f"Bloom: {bloom_name} (esperado L{bloom_expected})")
    justification_parts.append(f"Dreyfus: {dreyfus_name}")

    if red_flags:
        justification_parts.append(f"Alertas: {len(red_flags)}")
    if evidences:
        justification_parts.append(f"Evidências: {len(evidences)}")

    justification = ". ".join(justification_parts)

    return DeterministicWSIResult(
        autodeclaracao_score=autodeclaracao,
        context_score=context_score,
        bloom_level=bloom_level,
        bloom_name=bloom_name,
        dreyfus_level=dreyfus_level,
        dreyfus_name=dreyfus_name,
        evidences=evidences,
        red_flags=red_flags,
        penalty=penalty,
        bonus=bonus,
        final_score=final_score,
        formula_applied=formula,
        justification=justification,
        formula_version="v2",
        star_components=star_components,
        star_score=star_score,
        bloom_alignment=bloom_align,
        flags_structured=flags_structured,
    )


def get_seniority_weights(seniority: str | None) -> dict[str, float]:
    """
    Retorna os pesos técnico/comportamental para o nível de senioridade.
    Spec Seção 9.2 — tabela SENIORITY_WEIGHTS.
    
    Args:
        seniority: Nível de senioridade (estagiario, junior, pleno, senior,
                   lead, principal, diretor, vp_clevel)
    Returns:
        Dict com 'technical' e 'behavioral' (somam 1.0)
    """
    if not seniority:
        return {"technical": 0.625, "behavioral": 0.375}
    key = seniority.lower().strip()
    return SENIORITY_WEIGHTS.get(key, {"technical": 0.625, "behavioral": 0.375})


def classify_wsi_score(score: float) -> str:
    """
    Classifica o score WSI final nos 6 níveis canônicos.
    Spec Seção 9.5 — escala /5 (= /10 ÷ 2).

    /5 thresholds derived from /10 spec:
        Excepcional   ≥ 9.0/10 → ≥ 4.5/5
        Excelente     ≥ 8.0/10 → ≥ 4.0/5
        Alto          ≥ 7.0/10 → ≥ 3.5/5
        Médio         ≥ 6.0/10 → ≥ 3.0/5
        Abaixo da média ≥ 4.5/10 → ≥ 2.25/5
        Regular/Baixo < 4.5/10 → < 2.25/5
    """
    if score >= 4.5:
        return "excepcional"
    if score >= 4.0:
        return "excelente"
    if score >= 3.5:
        return "alto"
    if score >= 3.0:
        return "medio"
    if score >= 2.25:
        return "abaixo_da_media"
    return "regular"


def get_classification_display(classification: str) -> dict[str, str]:
    """Retorna label PT-BR e cor para a classificação WSI."""
    config = {
        "excepcional":      {"label": "Excepcional",      "color": "emerald-700"},
        "excelente":        {"label": "Excelente",         "color": "green-600"},
        "alto":             {"label": "Alto",               "color": "blue-600"},
        "medio":            {"label": "Médio",              "color": "amber-600"},
        "abaixo_da_media":  {"label": "Abaixo da média",   "color": "orange-600"},
        "regular":          {"label": "Regular / Baixo",   "color": "red-600"},
    }
    return config.get(classification, config["medio"])


def get_wsi_decision(overall_score: float, technical_avg: float | None = None) -> dict[str, Any]:
    """
    Aplica WSI_CUTOFFS e Gate G3 a um score para retornar decisão.

    Spec Seção 9.5 — Cutoffs /5:
        approved_auto ≥ 3.75 (= 7.5/10)
        review_min    ≥ 3.00 (= 6.0/10)
        rejected_max  < 3.00 (= 6.0/10)
        Gate G3: tech_avg < 2.0 → rejected

    Returns:
        Dict com decision, interpretation, classification, classification_label
    """
    classification = classify_wsi_score(overall_score)
    class_display = get_classification_display(classification)

    if overall_score >= WSI_CUTOFFS["approved_auto"]:
        decision = "approved"
        interpretation = "Candidato aprovado automaticamente"
    elif overall_score >= WSI_CUTOFFS["review_min"]:
        decision = "needs_review"
        interpretation = "Candidato requer revisão manual"
    else:
        decision = "rejected"
        interpretation = "Candidato abaixo do corte mínimo"

    gate_g3_triggered = False
    if technical_avg is not None and technical_avg < GATE_G3_THRESHOLD:
        gate_g3_triggered = True
        decision = "rejected"
        interpretation = "Gate G3: score técnico insuficiente"

    return {
        "decision": decision,
        "interpretation": interpretation,
        "classification": classification,
        "classification_label": class_display["label"],
        "gate_g3_triggered": gate_g3_triggered,
        "cutoffs_applied": WSI_CUTOFFS,
    }


def calculate_final_wsi_score(
    technical_scores: list[tuple[str, float, float]],
    behavioral_scores: list[tuple[str, float, float]],
    seniority: str | None = None,
    technical_weight: float | None = None,
    behavioral_weight: float | None = None,
    eligibility_score: float | None = None,
) -> dict[str, Any]:
    """
    Calcula score WSI final ponderado com SENIORITY_WEIGHTS da Spec Seção 9.2.

    Args:
        technical_scores:   Lista de (competency_name, score, weight)
        behavioral_scores:  Lista de (competency_name, score, weight)
        seniority:          Nível de senioridade da vaga (lookup em SENIORITY_WEIGHTS)
        technical_weight:   Override explícito (ignorado se seniority for fornecido)
        behavioral_weight:  Override explícito (ignorado se seniority for fornecido)
        eligibility_score:  Score de elegibilidade 0–5 (quando presente, 20% do total)

    Returns:
        Dict com score final, classificação 6 níveis, decisão, breakdown
    """
    def weighted_avg(scores: list[tuple[str, float, float]]) -> float:
        if not scores:
            return 0.0
        total_weight = sum(w for _, _, w in scores)
        if total_weight == 0:
            return sum(s for _, s, _ in scores) / len(scores)
        return sum(s * w for _, s, w in scores) / total_weight

    weights = get_seniority_weights(seniority) if seniority else None
    if weights:
        t_weight = weights["technical"]
        b_weight = weights["behavioral"]
    elif technical_weight is not None and behavioral_weight is not None:
        t_weight = technical_weight
        b_weight = behavioral_weight
    else:
        t_weight = 0.625
        b_weight = 0.375

    tech_avg  = weighted_avg(technical_scores)
    behav_avg = weighted_avg(behavioral_scores)

    if eligibility_score is not None:
        t_weight  = t_weight  * 0.80
        b_weight  = b_weight  * 0.80
        e_weight  = 0.20
        final_score = (t_weight * tech_avg) + (b_weight * behav_avg) + (e_weight * eligibility_score)
    else:
        e_weight = 0.0
        final_score = (t_weight * tech_avg) + (b_weight * behav_avg)

    final_score = round(max(1.0, min(5.0, final_score)), 2)

    if final_score >= WSI_CUTOFFS["approved_auto"]:
        decision = "approved"
        interpretation = "Candidato aprovado automaticamente"
    elif final_score >= WSI_CUTOFFS["review_min"]:
        decision = "needs_review"
        interpretation = "Candidato requer revisão manual"
    else:
        decision = "rejected"
        interpretation = "Candidato abaixo do corte mínimo"

    classification = classify_wsi_score(final_score)
    class_display  = get_classification_display(classification)

    gate_g3_triggered = tech_avg < GATE_G3_THRESHOLD
    if gate_g3_triggered:
        decision = "rejected"
        interpretation = "Gate G3: score técnico insuficiente"

    return {
        "final_score": final_score,
        "classification": classification,
        "classification_label": class_display["label"],
        "decision": decision,
        "interpretation": interpretation,
        "gate_g3_triggered": gate_g3_triggered,
        "breakdown": {
            "technical_average":  round(tech_avg, 2),
            "behavioral_average": round(behav_avg, 2),
            "technical_weight":   round(t_weight, 4),
            "behavioral_weight":  round(b_weight, 4),
            "eligibility_weight": round(e_weight, 4),
            "eligibility_score":  eligibility_score,
            "seniority_used":     seniority,
        },
        "formula": (
            f"WSI = ({t_weight:.4f} × {tech_avg:.2f})"
            f" + ({b_weight:.4f} × {behav_avg:.2f})"
            + (f" + ({e_weight:.2f} × {eligibility_score:.2f})" if eligibility_score else "")
            + f" = {final_score:.2f}"
        ),
        "cutoffs_applied": WSI_CUTOFFS,
    }


wsi_deterministic_scorer = None

def get_wsi_scorer():
    """Retorna instância do scorer determinístico."""
    return {
        "calculate_wsi": calculate_wsi_deterministic,
        "calculate_final_score": calculate_final_wsi_score,
        "classify_score": classify_wsi_score,
        "get_classification_display": get_classification_display,
        "get_wsi_decision": get_wsi_decision,
        "get_seniority_weights": get_seniority_weights,
        "extract_autodeclaracao": extract_autodeclaracao_score,
        "calculate_context": calculate_context_score,
        "calculate_bloom": calculate_bloom_level,
        "calculate_dreyfus": calculate_dreyfus_level,
        "extract_evidences": extract_evidences,
        "detect_red_flags": detect_red_flags,
        "dreyfus_recruiter_labels": DREYFUS_RECRUITER_LABELS,
        "bloom_recruiter_labels": BLOOM_RECRUITER_LABELS,
        "big_five_recruiter_labels": BIG_FIVE_RECRUITER_LABELS,
        "seniority_weights": SENIORITY_WEIGHTS,
        "wsi_cutoffs": WSI_CUTOFFS,
        "gate_g3_threshold": GATE_G3_THRESHOLD,
    }
