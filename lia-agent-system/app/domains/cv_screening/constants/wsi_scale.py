"""
WSI Scale Constants — fonte única da escala numérica do WSI (escala 0-10).

CONTEXTO (Task #497 PR2 — flip atômico)
========================================
A escala canônica do método WSI v3.3 (`WSI_METHODOLOGY_COMPLETE_v2`) trabalha
em **0-10 end-to-end**. Até a #497 PR1 o código vivia em **0-5** com conversões
ad-hoc `× 2` em apenas 2 endpoints (reports.py:755, evaluation.py:421) — o que
gerava drift sistemático com a spec (M04, M10, M16 do audit rev. 4) e
exigia mental gymnastics constante para devs.

A #497 PR1 consolidou ~30 magic numbers neste arquivo (zero behavior change).
A #497 PR2 (esta versão) **dobra todos os valores numéricos de escala** e
realinha 3 penalidades à spec §8.2 (M04). O engine continua intocado — toda
a aritmética usa estas constantes.

REGRA DE OURO: nenhum literal numérico de escala deve ficar inline no
``wsi_deterministic_scorer.py`` ou nos serviços satélite. Tudo lê daqui.

Histórico:
- PR1 (refator puro): consolidou constantes em 0-5 sem behavior change.
- PR2 (este flip): dobrou valores → escala 0-10 + alinhou penalidades a M04.
- PR3 (frontend): troca de divisores `/5` → `/10` em 60 telas.
- PR4 (cleanup): remoção de conversões órfãs + templates/RAG/E2E.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Range canônico da escala WSI (0-10)
# ---------------------------------------------------------------------------
# Mínimo válido — abaixo disso o engine clampa pra cima. Conceitualmente
# representa "nota mais baixa atribuível" (não há nota 0 no método WSI v3.3).
SCALE_MIN_VALID: float = 2.0
# Máximo válido — acima disso o engine clampa pra baixo. É o teto da escala.
SCALE_MAX: float = 10.0

# Dreyfus tem ladder próprio 1-5 (Novato → Especialista). É CATEGORIAL,
# não é escala WSI. Usado em normalizações de proficiência.
DREYFUS_MAX: int = 5
# Bloom tem ladder próprio 1-6 (Lembrar → Criar). Também CATEGORIAL.
BLOOM_MAX: int = 6

# ---------------------------------------------------------------------------
# Fator de normalização para componentes 0-1 → escala WSI
# ---------------------------------------------------------------------------
# STAR score e Bloom alignment são calculados em [0.0, 1.0] e precisam ser
# trazidos para a escala WSI antes de entrar na fórmula tri-componente.
# Multiplica-se por este fator. Em escala 0-10 o fator é 10.0.
NORMALIZATION_FACTOR: float = 10.0

# ---------------------------------------------------------------------------
# Cutoffs de decisão (Spec Seção 9.5 — em escala 0-10)
# ---------------------------------------------------------------------------
CUTOFF_APPROVED_AUTO: float = 7.5    # ≥ → aprovado automaticamente
CUTOFF_REVIEW_MIN: float = 6.0       # ≥ → revisão manual; < → rejeitado
CUTOFF_REJECTED_MAX: float = 6.0     # alias semântico do anterior

# Mantido como dict pois o engine expõe via ``cutoffs_applied`` no payload.
WSI_CUTOFFS: dict[str, float] = {
    "approved_auto": CUTOFF_APPROVED_AUTO,
    "review_min":    CUTOFF_REVIEW_MIN,
    "rejected_below": CUTOFF_REJECTED_MAX,
    "rejected_max": CUTOFF_REJECTED_MAX,
}

# Gate G3 — abaixo deste score técnico, candidato é rejeitado mesmo que o
# overall esteja acima do cutoff. Spec Seção 9.5 (em /10).
GATE_G3_THRESHOLD: float = 4.0

# ---------------------------------------------------------------------------
# Thresholds da classificação 6 níveis (``classify_wsi_score``) em /10
# ---------------------------------------------------------------------------
CLASSIFY_EXCEPCIONAL: float = 9.0
CLASSIFY_EXCELENTE: float   = 8.0
CLASSIFY_ALTO: float        = 7.0
CLASSIFY_MEDIO: float       = 6.0
CLASSIFY_ABAIXO_MEDIA: float = 4.5
# < CLASSIFY_ABAIXO_MEDIA → "regular"

# ---------------------------------------------------------------------------
# Autodeclaração — mapping de keywords linguísticas para nota
# ---------------------------------------------------------------------------
# Usado em ``extract_autodeclaracao_score``. As chaves continuam em 1-5
# (input do candidato é coletado em /5 — "5 de 5", "nota 4/5", etc.).
# O engine multiplica por SCALE_MAX/5.0 = 2.0 antes de usar internamente,
# convertendo automaticamente para a escala canônica /10.
AUTODECLARATION_LEVEL_KEYWORDS: dict[float, list[str]] = {
    5.0: ["expert", "especialista", "domínio completo", "mestre", "5 de 5"],
    4.0: ["avançado", "domino bem", "proficiente", "sólido", "4 de 5"],
    3.0: ["intermediário", "razoável", "competente", "3 de 5"],
    2.0: ["básico", "iniciante", "aprendendo", "2 de 5"],
    1.0: ["muito básico", "nunca usei", "não tenho experiência", "1 de 5"],
}

# ---------------------------------------------------------------------------
# Context score (``calculate_context_score``) em /10
# ---------------------------------------------------------------------------
# Score base e thresholds quantitativos para classificar a qualidade do
# contexto fornecido pelo candidato.
CONTEXT_SCORE_BASE: float = 6.0          # nota neutra default
CONTEXT_SCORE_MAX: float = 10.0
CONTEXT_SCORE_MIN: float = 2.0
CONTEXT_SCORE_HIGH: float = 10.0
CONTEXT_SCORE_HIGH_BASE: float = 8.0     # base quando há high indicators
CONTEXT_SCORE_HIGH_STEP: float = 0.4     # incremento por indicator extra
CONTEXT_SCORE_MEDIUM_HIGH: float = 7.0
CONTEXT_SCORE_MEDIUM_BASE: float = 6.0
CONTEXT_SCORE_MEDIUM_STEP: float = 0.2
# Penalidades por low_count
CONTEXT_PENALTY_LOW_HEAVY: float = 2.0   # 2+ low_count: -2.0, floor 2.0
CONTEXT_PENALTY_LOW_LIGHT: float = 1.0   # 1 low_count: -1.0, floor 3.0
CONTEXT_FLOOR_HEAVY: float = 2.0
CONTEXT_FLOOR_LIGHT: float = 3.0
# Bônus por evidência
CONTEXT_EVIDENCE_BOOST_PER: float = 0.2
CONTEXT_EVIDENCE_BOOST_MAX: float = 1.0

# ---------------------------------------------------------------------------
# Penalidades e bônus do score final (em /10, alinhadas spec §8.2 — M04)
# ---------------------------------------------------------------------------
# NOTA M04: estas 3 penalidades NÃO são puro double dos valores em /5 — elas
# foram realinhadas à spec §8.2 que sempre exigiu valores mais severos do que
# o código entregava em /5. PR2 corrige esse drift histórico:
#   - INFLATION:   /5 era -1.0 (dobrado seria -2.0); spec exige -1.5
#   - GENERIC:     /5 era -0.5 (dobrado seria -1.0); spec exige -1.0 (coincide)
#   - NO_CONTEXT:  /5 era -0.3 (dobrado seria -0.6); spec exige -2.5
PENALTY_INFLATION: float = -1.5
PENALTY_GENERIC: float = -1.0
PENALTY_NO_CONTEXT: float = -2.5
PENALTY_NO_CONTEXT_MIN_WORDS: int = 20

BONUS_HUMILITY: float = 1.0
BONUS_EXCEPTIONAL_EVIDENCE: float = 0.6
BONUS_MAX: float = 2.0

# ---------------------------------------------------------------------------
# Detecção de inflação (red flag e flag estruturada) em /10
# ---------------------------------------------------------------------------
# Inflation = autodeclaração alta + contexto fraco.
INFLATION_AUTODECLARATION_MIN: float = 9.0
INFLATION_CONTEXT_MAX: float = 6.0

# ---------------------------------------------------------------------------
# Modificadores Dreyfus baseados em context_score (em /10)
# ---------------------------------------------------------------------------
DREYFUS_PROMOTE_CONTEXT_MIN: float = 9.0  # ≥ → +1 nível
DREYFUS_DEMOTE_CONTEXT_MAX: float = 5.0   # < → -1 nível

# ---------------------------------------------------------------------------
# Thresholds para frases de justificativa (em /10)
# ---------------------------------------------------------------------------
JUSTIFICATION_CONTEXT_STRONG: float = 8.0    # ≥ → "Contexto forte"
JUSTIFICATION_CONTEXT_ADEQUATE: float = 6.0  # ≥ → "Contexto adequado"
# < → "Contexto fraco"

# ---------------------------------------------------------------------------
# Defaults de pesos técnico/comportamental (não escala — somam 1.0)
# ---------------------------------------------------------------------------
DEFAULT_TECHNICAL_WEIGHT: float = 0.625
DEFAULT_BEHAVIORAL_WEIGHT: float = 0.375

# Peso da elegibilidade quando presente (20% do total, restante em 80%)
ELIGIBILITY_WEIGHT: float = 0.20
NON_ELIGIBILITY_WEIGHT: float = 0.80
