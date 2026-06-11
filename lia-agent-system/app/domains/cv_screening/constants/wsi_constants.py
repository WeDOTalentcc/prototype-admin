"""
WSI canonical constants — single source of truth.

Toda referência a nomes de dimensões e blocos WSI deve importar daqui.
Isso garante consistência entre pipeline, agente, frontend e relatórios.

Referência: Guia WeDOTalent v3.4 — Score Card WSI e Roteiro de Entrevista.
"""

# ---------------------------------------------------------------------------
# Dimensões de avaliação (Score Card WSI — 4 dimensões pontuadas)
# Usado em: avaliador_wsi_agent, interview_notes, candidate_report_service
# ---------------------------------------------------------------------------

WSI_DIMENSION_LABELS: dict[str, str] = {
    "technical":    "Competências Técnicas",
    "behavioral":   "Competências Comportamentais",
    "gap_analysis": "Experiência Profissional",
    "contextual":   "Fit Cultural e Alinhamento",
}

# Pesos padrão do Score Card completo (entrevista + screening)
# Nota: avaliador_wsi_agent usa pesos simplificados para análise de CV
# apenas (sem dados de entrevista): technical=0.70, behavioral=0.30.
# Esses pesos simplificados permanecem no agente com comentário explicativo.
WSI_DIMENSION_WEIGHTS_DEFAULT: dict[str, float] = {
    "technical":    0.50,
    "behavioral":   0.20,
    "gap_analysis": 0.15,
    "contextual":   0.15,
}

# ---------------------------------------------------------------------------
# Blocos estruturais do roteiro (conversa com candidato — 7 blocos, 0-6)
# Usado em: wsi_screening_pipeline, jobsPageConstants (FE)
# ---------------------------------------------------------------------------

WSI_BLOCK_NAMES: dict[int, str] = {
    0: "Abordagem Inicial",
    1: "Apresentação da Oportunidade",
    2: "Perguntas Padrão da Empresa",
    3: "Competências Técnicas",
    4: "Competências Comportamentais e Fit",
    5: "Resultado e Encerramento",
}

# ---------------------------------------------------------------------------
# F5 — Distribuição adaptativa de perguntas técnicas vs. comportamentais
# por senioridade e modo (compact=7 / full=12).
# Fonte canônica: importar aqui em vez de definir localmente em cada módulo.
# Referência: Guia WeDOTalent v3.4 — Metodologia WSI F5.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Taxonomia Bloom — labels simples para uso em perguntas e relatórios
# Canonical labels em PT-BR. Módulos que precisam de estrutura rica (com
# indicadores ou descriptions) mantêm suas próprias dicts estendidas,
# mas DEVEM usar esses labels como fonte dos nomes.
# ---------------------------------------------------------------------------
BLOOM_LEVEL_LABELS: dict[int, str] = {
    1: "Recordar",
    2: "Compreender",
    3: "Aplicar",
    4: "Analisar",
    5: "Avaliar",
    6: "Criar",
}

# ---------------------------------------------------------------------------
# Dreyfus Model — labels simples para uso em perguntas e relatórios
# ---------------------------------------------------------------------------
DREYFUS_STAGE_LABELS: dict[int, str] = {
    1: "Iniciante",
    2: "Básico",
    3: "Intermediário",
    4: "Avançado",
    5: "Especialista",
}

# ---------------------------------------------------------------------------
# Seniority → Dreyfus/Bloom mappings (base, uncalibrated)
# Usado em: wsi_service, wsi_screening_pipeline,
#           seniority_context_calibrator (como base antes de ajustes),
#           wsi_endpoints
# ---------------------------------------------------------------------------
SENIORITY_TO_DREYFUS: dict[str, int] = {
    "junior": 2,
    "pleno": 3,
    "senior": 4,
    "lead": 5,
    "executive": 5,
}

SENIORITY_TO_BLOOM: dict[str, list[int]] = {
    "junior": [1, 2, 3],
    "pleno": [3, 4],
    "senior": [4, 5],
    "lead": [5, 6],
    "executive": [5, 6],
}

# ---------------------------------------------------------------------------
# F5 — Distribuição adaptativa de perguntas técnicas vs. comportamentais
# ---------------------------------------------------------------------------
SENIORITY_DISTRIBUTIONS: dict[str, dict[str, dict[str, int]]] = {
    "compact": {
        "estagiario": {"technical": 5, "behavioral": 2, "total": 7},
        "junior":     {"technical": 5, "behavioral": 2, "total": 7},
        "pleno":      {"technical": 5, "behavioral": 2, "total": 7},
        "senior":     {"technical": 4, "behavioral": 3, "total": 7},
        "lead":       {"technical": 3, "behavioral": 4, "total": 7},
        "principal":  {"technical": 4, "behavioral": 3, "total": 7},
        "staff":      {"technical": 4, "behavioral": 3, "total": 7},
        "diretor":    {"technical": 3, "behavioral": 4, "total": 7},
        "executive":  {"technical": 2, "behavioral": 5, "total": 7},
    },
    "full": {
        "estagiario": {"technical": 9, "behavioral": 3, "total": 12},
        "junior":     {"technical": 9, "behavioral": 3, "total": 12},
        "pleno":      {"technical": 8, "behavioral": 4, "total": 12},
        "senior":     {"technical": 7, "behavioral": 5, "total": 12},
        "lead":       {"technical": 7, "behavioral": 5, "total": 12},
        "principal":  {"technical": 7, "behavioral": 5, "total": 12},
        "staff":      {"technical": 7, "behavioral": 5, "total": 12},
        "diretor":    {"technical": 7, "behavioral": 5, "total": 12},
        "executive":  {"technical": 7, "behavioral": 5, "total": 12},
    },
}
