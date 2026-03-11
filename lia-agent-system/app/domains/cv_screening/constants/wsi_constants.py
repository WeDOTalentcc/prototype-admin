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
    3: "Elegibilidade e Formação",           # renomeado: era "Elegibilidade WSI"
    4: "Competências Técnicas",               # alinhado com dimensão Score Card
    5: "Competências Comportamentais e Fit",  # alinhado com dimensões behavioral + contextual
    6: "Resultado e Encerramento",
}

# ---------------------------------------------------------------------------
# Formação Acadêmica — pré-qualificador (não pontuado)
# Verificação de requisitos legais e certificações obrigatórias.
# Resultado: pass/fail — não entra no cálculo do score WSI.
# Bloco: 3 (Elegibilidade e Formação)
# ---------------------------------------------------------------------------

FORMACAO_PRE_QUALIFIER_LABEL: str = "Formação Acadêmica"
FORMACAO_PRE_QUALIFIER_DESCRIPTION: str = (
    "Verificação de requisitos legais de formação (OAB, CREA, CRM, etc.) "
    "e certificações técnicas obrigatórias. Não pontuado — pass/fail."
)
