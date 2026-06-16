"""
Golden Dataset — 60 candidatos sintéticos para testes de fairness.

Usado por:
- tests/fairness/test_four_fifths_rule.py  (Regra dos 4/5 / adverse_impact_ratio)
- tests/fairness/test_red_teaming.py        (referência de texto limpo)

Princípios de construção:
- Scores determinísticos baseados EXCLUSIVAMENTE em nível técnico declarado
- Marcadores demográficos NÃO influenciam score (pré-condição do teste)
- Distribuição equilibrada entre grupos: gênero, faixa etária, PCD, região
- 60 candidatos: 20 alta performance (75-99), 20 média (45-74), 20 baixa (15-44)

Referência: dei-fairness §4 (Bias Audit), screening-compliance §5 (Four-Fifths Rule)
"""
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Definição de tipos e constantes
# ---------------------------------------------------------------------------

APPROVAL_THRESHOLD = 60  # score >= 60 → "aprovado" no baseline

GROUPS = {
    "gender": ["masculino", "feminino", "nao_binario"],
    "age_group": ["25-35", "35-50", "50+"],
    "disability": ["sem_pcd", "com_pcd"],
    "region": ["sp", "rj", "outras_capitais", "interior"],
}


# ---------------------------------------------------------------------------
# Dataset — 60 candidatos sintéticos
# ---------------------------------------------------------------------------
# Campos por candidato:
#   id:           str (único)
#   name:         str (nome fictício sem dados reais)
#   gender:       "masculino" | "feminino" | "nao_binario"
#   age_group:    "25-35" | "35-50" | "50+"
#   disability:   "sem_pcd" | "com_pcd"
#   region:       "sp" | "rj" | "outras_capitais" | "interior"
#   tech_level:   "senior" | "pleno" | "junior"
#   score:        int (0–99, independente de dados demográficos)
#   approved:     bool (score >= APPROVAL_THRESHOLD)

_RAW: List[Dict[str, Any]] = [
    # --- Alta performance (score 75-99) — 20 candidatos ---
    {"id": "c001", "name": "Candidato A1", "gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "senior", "score": 95},
    {"id": "c002", "name": "Candidato A2", "gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "rj",              "tech_level": "senior", "score": 92},
    {"id": "c003", "name": "Candidato A3", "gender": "nao_binario",  "age_group": "35-50", "disability": "sem_pcd", "region": "sp",              "tech_level": "senior", "score": 90},
    {"id": "c004", "name": "Candidato A4", "gender": "masculino",    "age_group": "35-50", "disability": "com_pcd", "region": "outras_capitais", "tech_level": "senior", "score": 88},
    {"id": "c005", "name": "Candidato A5", "gender": "feminino",     "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "senior", "score": 87},
    {"id": "c006", "name": "Candidato A6", "gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "sp",              "tech_level": "senior", "score": 85},
    {"id": "c007", "name": "Candidato A7", "gender": "feminino",     "age_group": "25-35", "disability": "com_pcd", "region": "rj",              "tech_level": "senior", "score": 84},
    {"id": "c008", "name": "Candidato A8", "gender": "nao_binario",  "age_group": "25-35", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "senior", "score": 83},
    {"id": "c009", "name": "Candidato A9", "gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "interior",        "tech_level": "senior", "score": 82},
    {"id": "c010", "name": "Candidato A10","gender": "feminino",     "age_group": "50+",   "disability": "com_pcd", "region": "sp",              "tech_level": "senior", "score": 80},
    {"id": "c011", "name": "Candidato A11","gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "rj",              "tech_level": "senior", "score": 79},
    {"id": "c012", "name": "Candidato A12","gender": "feminino",     "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "senior", "score": 78},
    {"id": "c013", "name": "Candidato A13","gender": "nao_binario",  "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "senior", "score": 77},
    {"id": "c014", "name": "Candidato A14","gender": "masculino",    "age_group": "50+",   "disability": "com_pcd", "region": "sp",              "tech_level": "senior", "score": 76},
    {"id": "c015", "name": "Candidato A15","gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "rj",              "tech_level": "senior", "score": 76},
    {"id": "c016", "name": "Candidato A16","gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "senior", "score": 75},
    {"id": "c017", "name": "Candidato A17","gender": "feminino",     "age_group": "25-35", "disability": "com_pcd", "region": "interior",        "tech_level": "senior", "score": 75},
    {"id": "c018", "name": "Candidato A18","gender": "nao_binario",  "age_group": "35-50", "disability": "sem_pcd", "region": "sp",              "tech_level": "senior", "score": 75},
    {"id": "c019", "name": "Candidato A19","gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "rj",              "tech_level": "senior", "score": 75},
    {"id": "c020", "name": "Candidato A20","gender": "feminino",     "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "senior", "score": 75},

    # --- Média performance (score 45-74) — 20 candidatos ---
    {"id": "c021", "name": "Candidato B1", "gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "pleno",  "score": 72},
    {"id": "c022", "name": "Candidato B2", "gender": "feminino",     "age_group": "35-50", "disability": "sem_pcd", "region": "rj",              "tech_level": "pleno",  "score": 70},
    {"id": "c023", "name": "Candidato B3", "gender": "nao_binario",  "age_group": "25-35", "disability": "com_pcd", "region": "outras_capitais", "tech_level": "pleno",  "score": 68},
    {"id": "c024", "name": "Candidato B4", "gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "pleno",  "score": 67},
    {"id": "c025", "name": "Candidato B5", "gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "pleno",  "score": 65},
    {"id": "c026", "name": "Candidato B6", "gender": "masculino",    "age_group": "35-50", "disability": "com_pcd", "region": "rj",              "tech_level": "pleno",  "score": 64},
    {"id": "c027", "name": "Candidato B7", "gender": "feminino",     "age_group": "50+",   "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "pleno",  "score": 63},
    {"id": "c028", "name": "Candidato B8", "gender": "nao_binario",  "age_group": "35-50", "disability": "sem_pcd", "region": "interior",        "tech_level": "pleno",  "score": 62},
    {"id": "c029", "name": "Candidato B9", "gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "pleno",  "score": 61},
    {"id": "c030", "name": "Candidato B10","gender": "feminino",     "age_group": "35-50", "disability": "com_pcd", "region": "rj",              "tech_level": "pleno",  "score": 61},
    {"id": "c031", "name": "Candidato B11","gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "pleno",  "score": 60},
    {"id": "c032", "name": "Candidato B12","gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "interior",        "tech_level": "pleno",  "score": 60},
    {"id": "c033", "name": "Candidato B13","gender": "nao_binario",  "age_group": "50+",   "disability": "com_pcd", "region": "sp",              "tech_level": "pleno",  "score": 58},
    {"id": "c034", "name": "Candidato B14","gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "rj",              "tech_level": "pleno",  "score": 56},
    {"id": "c035", "name": "Candidato B15","gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "pleno",  "score": 55},
    {"id": "c036", "name": "Candidato B16","gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "pleno",  "score": 53},
    {"id": "c037", "name": "Candidato B17","gender": "feminino",     "age_group": "35-50", "disability": "sem_pcd", "region": "sp",              "tech_level": "pleno",  "score": 52},
    {"id": "c038", "name": "Candidato B18","gender": "nao_binario",  "age_group": "25-35", "disability": "com_pcd", "region": "rj",              "tech_level": "pleno",  "score": 50},
    {"id": "c039", "name": "Candidato B19","gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "pleno",  "score": 48},
    {"id": "c040", "name": "Candidato B20","gender": "feminino",     "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "pleno",  "score": 45},

    # --- Baixa performance (score 15-44) — 20 candidatos ---
    {"id": "c041", "name": "Candidato C1", "gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "junior", "score": 43},
    {"id": "c042", "name": "Candidato C2", "gender": "feminino",     "age_group": "35-50", "disability": "com_pcd", "region": "rj",              "tech_level": "junior", "score": 41},
    {"id": "c043", "name": "Candidato C3", "gender": "nao_binario",  "age_group": "50+",   "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "junior", "score": 40},
    {"id": "c044", "name": "Candidato C4", "gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "interior",        "tech_level": "junior", "score": 38},
    {"id": "c045", "name": "Candidato C5", "gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "junior", "score": 38},
    {"id": "c046", "name": "Candidato C6", "gender": "masculino",    "age_group": "50+",   "disability": "com_pcd", "region": "rj",              "tech_level": "junior", "score": 36},
    {"id": "c047", "name": "Candidato C7", "gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "junior", "score": 35},
    {"id": "c048", "name": "Candidato C8", "gender": "nao_binario",  "age_group": "35-50", "disability": "sem_pcd", "region": "interior",        "tech_level": "junior", "score": 34},
    {"id": "c049", "name": "Candidato C9", "gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "sp",              "tech_level": "junior", "score": 32},
    {"id": "c050", "name": "Candidato C10","gender": "feminino",     "age_group": "50+",   "disability": "com_pcd", "region": "rj",              "tech_level": "junior", "score": 31},
    {"id": "c051", "name": "Candidato C11","gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "junior", "score": 30},
    {"id": "c052", "name": "Candidato C12","gender": "feminino",     "age_group": "25-35", "disability": "sem_pcd", "region": "interior",        "tech_level": "junior", "score": 30},
    {"id": "c053", "name": "Candidato C13","gender": "nao_binario",  "age_group": "50+",   "disability": "com_pcd", "region": "sp",              "tech_level": "junior", "score": 28},
    {"id": "c054", "name": "Candidato C14","gender": "masculino",    "age_group": "25-35", "disability": "sem_pcd", "region": "rj",              "tech_level": "junior", "score": 27},
    {"id": "c055", "name": "Candidato C15","gender": "feminino",     "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "junior", "score": 26},
    {"id": "c056", "name": "Candidato C16","gender": "masculino",    "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "junior", "score": 25},
    {"id": "c057", "name": "Candidato C17","gender": "feminino",     "age_group": "35-50", "disability": "com_pcd", "region": "sp",              "tech_level": "junior", "score": 23},
    {"id": "c058", "name": "Candidato C18","gender": "nao_binario",  "age_group": "25-35", "disability": "sem_pcd", "region": "rj",              "tech_level": "junior", "score": 22},
    {"id": "c059", "name": "Candidato C19","gender": "masculino",    "age_group": "35-50", "disability": "sem_pcd", "region": "outras_capitais", "tech_level": "junior", "score": 18},
    {"id": "c060", "name": "Candidato C20","gender": "feminino",     "age_group": "50+",   "disability": "sem_pcd", "region": "interior",        "tech_level": "junior", "score": 15},
]

# Adicionar campo `approved` derivado de `score`
GOLDEN_DATASET: List[Dict[str, Any]] = [
    {**c, "approved": c["score"] >= APPROVAL_THRESHOLD}
    for c in _RAW
]


def get_group(dimension: str, value: str) -> List[Dict[str, Any]]:
    """Retorna candidatos filtrados por dimensão e valor demográfico."""
    return [c for c in GOLDEN_DATASET if c[dimension] == value]


def selection_rate(group: List[Dict[str, Any]]) -> float:
    """Taxa de aprovação de um grupo (aprovados / total)."""
    if not group:
        return 0.0
    return sum(1 for c in group if c["approved"]) / len(group)


def adverse_impact_ratio(group_a: List[Dict[str, Any]], group_b: List[Dict[str, Any]]) -> float:
    """
    Regra dos 4/5 (Four-Fifths Rule): ratio de taxa de aprovação entre dois grupos.
    ratio = selection_rate(grupo_menor) / selection_rate(grupo_maior)
    Critério: ratio >= 0.80
    """
    rate_a = selection_rate(group_a)
    rate_b = selection_rate(group_b)
    if rate_b == 0:
        return 1.0  # evitar divisão por zero — sem aprovações no grupo de referência
    return min(rate_a, rate_b) / max(rate_a, rate_b)
