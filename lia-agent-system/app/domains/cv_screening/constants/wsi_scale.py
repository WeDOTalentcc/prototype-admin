"""
WSI Scale Constants — fonte única da escala numérica do WSI.

CONTEXTO (Task #497 PR1)
========================
Antes da #497 essas constantes estavam espalhadas como magic numbers em
``wsi_deterministic_scorer.py`` (clamps ``min(5.0, max(1.0, ...))`` em 4
lugares, cutoffs ``3.75``/``3.0``, gate ``2.0``, normalizações ``× 5.0``,
etc.). A consolidação numa única fonte permite a migração futura de escala
0-5 → 0-10 (PR2) trocando apenas os valores neste arquivo, sem tocar no
engine.

REGRA DE OURO: nenhum literal numérico de escala deve ficar inline no
``wsi_deterministic_scorer.py`` ou nos serviços satélite. Tudo lê daqui.

Para PR1 os valores são exatamente os que estavam hardcoded antes (escala
1.0–5.0). PR2 dobra esses valores e a engine passa a operar 0–10 sem
nenhuma outra alteração.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Range canônico da escala WSI
# ---------------------------------------------------------------------------
# Mínimo válido — abaixo disso o engine clampa pra cima. Conceitualmente
# representa "nota mais baixa atribuível" (não há nota 0 no método WSI v3.3).
SCALE_MIN_VALID: float = 1.0
# Máximo válido — acima disso o engine clampa pra baixo. É o teto da escala.
SCALE_MAX: float = 5.0

# ---------------------------------------------------------------------------
# Fator de normalização para componentes 0-1 → escala WSI
# ---------------------------------------------------------------------------
# STAR score e Bloom alignment são calculados em [0.0, 1.0] e precisam ser
# trazidos para a escala WSI antes de entrar na fórmula tri-componente.
# Multiplica-se por este fator. Em escala 0-5 o fator é 5.0; em 0-10 vira 10.0.
NORMALIZATION_FACTOR: float = 5.0

# ---------------------------------------------------------------------------
# Cutoffs de decisão (Spec Seção 9.5)
# ---------------------------------------------------------------------------
CUTOFF_APPROVED_AUTO: float = 3.75   # ≥ → aprovado automaticamente
CUTOFF_REVIEW_MIN: float = 3.0       # ≥ → revisão manual; < → rejeitado
CUTOFF_REJECTED_MAX: float = 3.0     # alias semântico do anterior

# Mantido como dict pois o engine expõe via ``cutoffs_applied`` no payload.
WSI_CUTOFFS: dict[str, float] = {
    "approved_auto": CUTOFF_APPROVED_AUTO,
    "review_min":    CUTOFF_REVIEW_MIN,
    "rejected_below": CUTOFF_REJECTED_MAX,
    "rejected_max": CUTOFF_REJECTED_MAX,
}

# Gate G3 — abaixo deste score técnico, candidato é rejeitado mesmo que o
# overall esteja acima do cutoff. Spec Seção 9.5.
GATE_G3_THRESHOLD: float = 2.0

# ---------------------------------------------------------------------------
# Thresholds da classificação 6 níveis (``classify_wsi_score``)
# ---------------------------------------------------------------------------
CLASSIFY_EXCEPCIONAL: float = 4.5
CLASSIFY_EXCELENTE: float   = 4.0
CLASSIFY_ALTO: float        = 3.5
CLASSIFY_MEDIO: float       = 3.0
CLASSIFY_ABAIXO_MEDIA: float = 2.25
# < CLASSIFY_ABAIXO_MEDIA → "regular"

# ---------------------------------------------------------------------------
# Autodeclaração — mapping de keywords linguísticas para nota
# ---------------------------------------------------------------------------
# Usado em ``extract_autodeclaracao_score``. Reflete diretamente as âncoras
# da escala (5 = expert, 1 = nunca usei).
AUTODECLARATION_LEVEL_KEYWORDS: dict[float, list[str]] = {
    5.0: ["expert", "especialista", "domínio completo", "mestre", "5 de 5"],
    4.0: ["avançado", "domino bem", "proficiente", "sólido", "4 de 5"],
    3.0: ["intermediário", "razoável", "competente", "3 de 5"],
    2.0: ["básico", "iniciante", "aprendendo", "2 de 5"],
    1.0: ["muito básico", "nunca usei", "não tenho experiência", "1 de 5"],
}

# ---------------------------------------------------------------------------
# Context score (``calculate_context_score``)
# ---------------------------------------------------------------------------
# Score base e thresholds quantitativos para classificar a qualidade do
# contexto fornecido pelo candidato.
CONTEXT_SCORE_BASE: float = 3.0          # nota neutra default
CONTEXT_SCORE_MAX: float = 5.0
CONTEXT_SCORE_MIN: float = 1.0
CONTEXT_SCORE_HIGH: float = 5.0
CONTEXT_SCORE_HIGH_BASE: float = 4.0     # base quando há high indicators
CONTEXT_SCORE_HIGH_STEP: float = 0.2     # incremento por indicator extra
CONTEXT_SCORE_MEDIUM_HIGH: float = 3.5
CONTEXT_SCORE_MEDIUM_BASE: float = 3.0
CONTEXT_SCORE_MEDIUM_STEP: float = 0.1
# Penalidades por low_count
CONTEXT_PENALTY_LOW_HEAVY: float = 1.0   # 2+ low_count: -1.0, floor 1.0
CONTEXT_PENALTY_LOW_LIGHT: float = 0.5   # 1 low_count: -0.5, floor 1.5
CONTEXT_FLOOR_HEAVY: float = 1.0
CONTEXT_FLOOR_LIGHT: float = 1.5
# Bônus por evidência
CONTEXT_EVIDENCE_BOOST_PER: float = 0.1
CONTEXT_EVIDENCE_BOOST_MAX: float = 0.5

# ---------------------------------------------------------------------------
# Penalidades e bônus do score final
# ---------------------------------------------------------------------------
PENALTY_INFLATION: float = -1.0
PENALTY_GENERIC: float = -0.5
PENALTY_NO_CONTEXT: float = -0.3
PENALTY_NO_CONTEXT_MIN_WORDS: int = 20

BONUS_HUMILITY: float = 0.5
BONUS_EXCEPTIONAL_EVIDENCE: float = 0.3
BONUS_MAX: float = 1.0

# ---------------------------------------------------------------------------
# Detecção de inflação (red flag e flag estruturada)
# ---------------------------------------------------------------------------
# Inflation = autodeclaração alta + contexto fraco.
INFLATION_AUTODECLARATION_MIN: float = 4.5
INFLATION_CONTEXT_MAX: float = 3.0

# ---------------------------------------------------------------------------
# Modificadores Dreyfus baseados em context_score
# ---------------------------------------------------------------------------
DREYFUS_PROMOTE_CONTEXT_MIN: float = 4.5  # ≥ → +1 nível
DREYFUS_DEMOTE_CONTEXT_MAX: float = 2.5   # < → -1 nível

# ---------------------------------------------------------------------------
# Thresholds para frases de justificativa
# ---------------------------------------------------------------------------
JUSTIFICATION_CONTEXT_STRONG: float = 4.0   # ≥ → "Contexto forte"
JUSTIFICATION_CONTEXT_ADEQUATE: float = 3.0  # ≥ → "Contexto adequado"
# < → "Contexto fraco"

# ---------------------------------------------------------------------------
# Defaults de pesos técnico/comportamental quando não há senioridade definida
# ---------------------------------------------------------------------------
DEFAULT_TECHNICAL_WEIGHT: float = 0.625
DEFAULT_BEHAVIORAL_WEIGHT: float = 0.375

# Peso da elegibilidade quando presente (20% do total, restante em 80%)
ELIGIBILITY_WEIGHT: float = 0.20
NON_ELIGIBILITY_WEIGHT: float = 0.80
