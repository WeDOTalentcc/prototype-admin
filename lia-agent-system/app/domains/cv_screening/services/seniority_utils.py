"""
Seniority Normalization Utils - Single Source of Truth for WSI System.

Este módulo centraliza toda a lógica de normalização de níveis de senioridade
para o sistema WSI (Work Suitability Index). Define a taxonomia oficial de 5 níveis
e fornece funções de normalização, inferência e comparação numérica.

TAXONOMIA OFICIAL WSI:
- junior: Profissionais em início de carreira com até 2 anos de experiência
- pleno: Profissionais com experiência intermediária (2-7 anos)
- senior: Profissionais sênior com expertise consolidada (7+ anos)
- lead: Líderes técnicos e especialistas em papéis de liderança
- executive: Executivos, gerentes e profissionais em nível C-suite

Este módulo é o PONTO ÚNICO DE VERDADE para toda a plataforma.
Qualquer normalização de senioridade deve usar funções deste módulo.

Autor: LIA Agent System
Data: 2026-02-11
Versão: 1.0
"""

import logging


logger = logging.getLogger(__name__)

WSI_SENIORITY_LEVELS = ["junior", "pleno", "senior", "lead", "executive"]

SENIORITY_NORMALIZATION_MAP: dict[str, str] = {
    "júnior": "junior",
    "junior": "junior",
    "jr": "junior",
    "jr.": "junior",
    "entry": "junior",
    "entry level": "junior",
    "entry-level": "junior",
    "trainee": "junior",
    "estagiário": "junior",
    "estágiário": "junior",
    "intern": "junior",
    "internship": "junior",
    "graduate": "junior",
    "apprentice": "junior",
    
    "pleno": "pleno",
    "mid": "pleno",
    "mid-level": "pleno",
    "midlevel": "pleno",
    "intermediário": "pleno",
    "intermedio": "pleno",
    "middle": "pleno",
    
    "sênior": "senior",
    "senior": "senior",
    "sr": "senior",
    "sr.": "senior",
    "especialista": "senior",
    "expert": "senior",
    "staff": "senior",
    
    "tech lead": "lead",
    "techlead": "lead",
    "tech-lead": "lead",
    "líder": "lead",
    "líder técnico": "lead",
    "lider tecnico": "lead",
    "principal": "lead",
    "principal engineer": "lead",
    "staff engineer": "lead",
    "coordenador": "lead",
    "coordinator": "lead",
    "team lead": "lead",
    "teamlead": "lead",
    "chapter lead": "lead",
    "squad lead": "lead",
    
    "c-level": "executive",
    "c-suite": "executive",
    "executive": "executive",
    "diretor": "executive",
    "director": "executive",
    "vp": "executive",
    "vice president": "executive",
    "vice-president": "executive",
    "president": "executive",
    "head": "executive",
    "head of": "executive",
    "ceo": "executive",
    "cto": "executive",
    "cfo": "executive",
    "coo": "executive",
    "cio": "executive",
    "cfoo": "executive",
    "chro": "executive",
    "gerente": "executive",
    "manager": "executive",
    "gerente sênior": "executive",
    "senior manager": "executive",
    "superintendente": "executive",
    "diretor executivo": "executive",
    "executive director": "executive",
}

SENIORITY_NUMERIC_MAPPING: dict[str, int] = {
    "junior": 1,
    "pleno": 2,
    "senior": 3,
    "lead": 4,
    "executive": 5,
}


def normalize_seniority(raw: str | None) -> str:
    """
    Normaliza uma string de senioridade para um dos 5 níveis oficiais WSI.
    
    Função principal para normalização de senioridade em toda a plataforma.
    Aceita variações em português, inglês, abreviações e inicia normalização.
    
    Args:
        raw: String bruta com a senioridade (ex: "Júnior", "SR", "Tech Lead")
        
    Returns:
        String com um dos 5 níveis oficiais: "junior", "pleno", "senior", "lead", "executive"
        Retorna "pleno" como fallback se nenhuma correspondência for encontrada.
        
    Exemplo:
        >>> normalize_seniority("Júnior")
        "junior"
        
        >>> normalize_seniority("SR")
        "senior"
        
        >>> normalize_seniority("Tech Lead")
        "lead"
        
        >>> normalize_seniority("Algo aleatório")
        "pleno"  # fallback
    """
    if not raw:
        logger.warning("Empty or None seniority value received, defaulting to 'pleno'")
        return "pleno"
    
    raw_lower = raw.strip().lower()
    
    if raw_lower in SENIORITY_NORMALIZATION_MAP:
        normalized = SENIORITY_NORMALIZATION_MAP[raw_lower]
        logger.debug(f"Normalized seniority: '{raw}' -> '{normalized}'")
        return normalized
    
    for key, value in SENIORITY_NORMALIZATION_MAP.items():
        if key in raw_lower:
            logger.debug(f"Partial match for seniority: '{raw}' -> '{value}'")
            return value
    
    logger.warning(f"Unknown seniority value: '{raw}', defaulting to 'pleno'")
    return "pleno"


def get_seniority_numeric(seniority: str | None) -> int:
    """
    Retorna o valor numérico de um nível de senioridade para comparação e ordenação.
    
    Converte a senioridade normalizada em um número para operações de comparação,
    ordenação e cálculos numéricos (1=junior, 5=executive).
    
    Args:
        seniority: Nível de senioridade normalizado (ex: "junior", "senior")
        
    Returns:
        Inteiro de 1 a 5 representando o nível:
        - 1: junior
        - 2: pleno
        - 3: senior
        - 4: lead
        - 5: executive
        
    Exemplo:
        >>> get_seniority_numeric("junior")
        1
        
        >>> get_seniority_numeric("senior")
        3
        
        >>> get_seniority_numeric("executive")
        5
    """
    if not seniority:
        logger.warning("Empty seniority value for numeric conversion, defaulting to 2")
        return 2
    
    seniority_norm = seniority.strip().lower()
    numeric = SENIORITY_NUMERIC_MAPPING.get(seniority_norm)
    
    if numeric is None:
        logger.warning(f"Unknown seniority for numeric conversion: '{seniority}', defaulting to 2")
        return 2
    
    return numeric


def infer_seniority_from_title(title: str | None) -> str | None:
    """
    Infere o nível de senioridade a partir de um título de cargo.
    
    Analisa o texto do título de cargo para detectar palavras-chave que indicam
    o nível de senioridade. Usa matching de keywords em português e inglês.
    
    Args:
        title: Título do cargo (ex: "Senior Software Engineer", "Diretor de TI")
        
    Returns:
        String com nível de senioridade inferido ("junior", "pleno", "senior", "lead", "executive")
        ou None se não conseguir inferir
        
    Exemplo:
        >>> infer_seniority_from_title("Senior Software Engineer")
        "senior"
        
        >>> infer_seniority_from_title("Junior Developer")
        "junior"
        
        >>> infer_seniority_from_title("Tech Lead da Equipe")
        "lead"
        
        >>> infer_seniority_from_title("Diretor Executivo")
        "executive"
        
        >>> infer_seniority_from_title("Engenheiro")
        None  # Sem indicativo claro
    """
    if not title:
        logger.debug("Empty title provided for seniority inference")
        return None
    
    title_lower = title.strip().lower()
    
    junior_keywords = [
        "júnior", "junior", "jr", "jr.", "entry", "entry level", "entry-level",
        "trainee", "estagiário", "estágiário", "intern", "internship", "graduate",
        "apprentice", "iniciante", "iniciador"
    ]
    
    pleno_keywords = [
        "pleno", "mid", "mid-level", "midlevel", "intermediário", "intermedio",
        "middle", "especialista técnico", "técnico sênior", "tecnico senior"
    ]
    
    senior_keywords = [
        "sênior", "senior", "sr", "sr.", "especialista", "expert", "staff engineer",
        "staff", "principal", "experienced", "experiente"
    ]
    
    lead_keywords = [
        "tech lead", "techlead", "tech-lead", "líder", "líder técnico",
        "lider tecnico", "principal engineer", "staff engineer", "coordenador",
        "coordinator", "team lead", "teamlead", "chapter lead", "squad lead"
    ]
    
    executive_keywords = [
        "c-level", "c-suite", "executive", "diretor", "director", "vp",
        "vice president", "vice-president", "president", "head of", "head",
        "ceo", "cto", "cfo", "coo", "cio", "cfoo", "chro",
        "gerente", "manager", "superintendente", "diretora", "diretora executiva"
    ]
    
    for keyword in executive_keywords:
        if keyword in title_lower and len(keyword) > 3:
            logger.debug(f"Inferred 'executive' from title: {title}")
            return "executive"
    
    for keyword in lead_keywords:
        if keyword in title_lower:
            logger.debug(f"Inferred 'lead' from title: {title}")
            return "lead"
    
    for keyword in senior_keywords:
        if keyword in title_lower:
            logger.debug(f"Inferred 'senior' from title: {title}")
            return "senior"
    
    for keyword in pleno_keywords:
        if keyword in title_lower:
            logger.debug(f"Inferred 'pleno' from title: {title}")
            return "pleno"
    
    for keyword in junior_keywords:
        if keyword in title_lower:
            logger.debug(f"Inferred 'junior' from title: {title}")
            return "junior"
    
    for keyword in executive_keywords:
        if keyword in title_lower:
            logger.debug(f"Inferred 'executive' from title: {title}")
            return "executive"
    
    logger.debug(f"Could not infer seniority from title: {title}")
    return None


def is_valid_seniority_level(seniority: str | None) -> bool:
    """
    Verifica se uma senioridade é um nível válido da taxonomia WSI.
    
    Args:
        seniority: String de senioridade a validar
        
    Returns:
        True se é um dos 5 níveis oficiais, False caso contrário
        
    Exemplo:
        >>> is_valid_seniority_level("junior")
        True
        
        >>> is_valid_seniority_level("master")
        False
    """
    if not seniority:
        return False
    
    return seniority.strip().lower() in WSI_SENIORITY_LEVELS


def compare_seniority(seniority1: str, seniority2: str) -> int:
    """
    Compara dois níveis de senioridade.
    
    Args:
        seniority1: Primeiro nível de senioridade
        seniority2: Segundo nível de senioridade
        
    Returns:
        -1 se seniority1 < seniority2
        0 se seniority1 == seniority2
        1 se seniority1 > seniority2
        
    Exemplo:
        >>> compare_seniority("junior", "senior")
        -1
        
        >>> compare_seniority("executive", "junior")
        1
        
        >>> compare_seniority("pleno", "pleno")
        0
    """
    num1 = get_seniority_numeric(seniority1)
    num2 = get_seniority_numeric(seniority2)
    
    if num1 < num2:
        return -1
    elif num1 > num2:
        return 1
    else:
        return 0


def normalize_and_validate(raw: str | None) -> str | None:
    """
    Normaliza uma senioridade e retorna None se não conseguir normalizar.
    
    Diferente de normalize_seniority que retorna "pleno" como fallback,
    esta função retorna None se a normalização não tiver sucesso.
    
    Útil para validações estritas onde nível desconhecido é inaceitável.
    
    Args:
        raw: String bruta de senioridade
        
    Returns:
        String com nível normalizado ou None
        
    Exemplo:
        >>> normalize_and_validate("Senior")
        "senior"
        
        >>> normalize_and_validate("xyz")
        None
    """
    if not raw:
        return None
    
    raw_lower = raw.strip().lower()
    
    if raw_lower in SENIORITY_NORMALIZATION_MAP:
        return SENIORITY_NORMALIZATION_MAP[raw_lower]
    
    for key, value in SENIORITY_NORMALIZATION_MAP.items():
        if key in raw_lower:
            return value
    
    return None
