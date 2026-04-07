"""
Sector Benchmark Service — Anti-sycophancy (Crença #11)

Fornece benchmarks setoriais por área e senioridade para enriquecer o prompt de avaliação
do LLM, evitando que o modelo inflacione scores por viés de complacência (sycophancy).

O benchmark é injetado no prompt antes da chamada LLM, ancorando a avaliação em
referências objetivas de mercado (Dreyfus + Bloom + WSI Calibration Service).

Referência:
- wedo-governance Crença #11 (Anti-sycophancy)
- screening-compliance §1.3 (Calibração por Senioridade — 4 etapas)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tabela interna de benchmarks
#
# Estrutura: area → seniority → BenchmarkProfile
# Fonte: screening-compliance §1.3 + dados históricos WeDOTalent
#
# score_range: (min_esperado, max_típico) para candidatos qualificados
# approval_rate: % histórica de aprovação neste segmento
# score_p50: score mediano — referência para calibração
# score_p75: score para candidato acima da média
# key_signals: sinais obrigatórios para o nível (mencionados no prompt)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BenchmarkProfile:
    area: str
    seniority: str
    score_p50: float       # mediana histórica
    score_p75: float       # 75º percentil
    min_expected: float    # mínimo esperado para aprovação
    approval_rate: float   # taxa de aprovação histórica no segmento
    key_signals: tuple[str, ...]  # sinais que o LLM deve verificar
    calibration_note: str  # instrução de anti-sycophancy para o LLM


_BENCHMARKS: dict[tuple[str, str], BenchmarkProfile] = {
    # -----------------------------------------------------------------------
    # Software Engineering
    # -----------------------------------------------------------------------
    ("software_engineering", "junior"): BenchmarkProfile(
        area="software_engineering", seniority="junior",
        score_p50=38.0, score_p75=52.0, min_expected=30.0,
        approval_rate=0.35,
        key_signals=("código funcional em projetos reais", "versionamento Git", "testes unitários básicos"),
        calibration_note=(
            "Júniores tipicamente atingem 30-52 pontos. Score > 65 para júnior requer "
            "evidência explícita e quantificada. Não inflar por potencial — avaliar APENAS evidência presente."
        ),
    ),
    ("software_engineering", "pleno"): BenchmarkProfile(
        area="software_engineering", seniority="pleno",
        score_p50=58.0, score_p75=72.0, min_expected=50.0,
        approval_rate=0.52,
        key_signals=("features end-to-end", "code review", "SQL + API REST", "ciclo completo de deploy"),
        calibration_note=(
            "Plenos tipicamente atingem 50-72 pontos. Score > 80 para pleno requer "
            "entrega técnica mensurável documentada. Distinguir pleno de sênior pelo escopo de autonomia."
        ),
    ),
    ("software_engineering", "senior"): BenchmarkProfile(
        area="software_engineering", seniority="senior",
        score_p50=72.0, score_p75=85.0, min_expected=65.0,
        approval_rate=0.45,
        key_signals=("decisões arquiteturais", "mentoria", "liderança técnica", "impacto mensurável"),
        calibration_note=(
            "Sêniores tipicamente atingem 65-85 pontos. Score > 90 exige impacto técnico "
            "excepcional documentado. Mentoria e liderança técnica são diferenciais — verificar evidência explícita."
        ),
    ),
    ("software_engineering", "staff"): BenchmarkProfile(
        area="software_engineering", seniority="staff",
        score_p50=82.0, score_p75=92.0, min_expected=75.0,
        approval_rate=0.30,
        key_signals=("arquitetura de sistemas", "contribuição open-source", "definição de padrões de engenharia"),
        calibration_note=(
            "Staff/Principal tipicamente atingem 75-92 pontos. Avaliar visibilidade técnica externa "
            "(talks, artigos, OSS) e impacto cross-team. Pool muito reduzido — critérios rigorosos."
        ),
    ),

    # -----------------------------------------------------------------------
    # Data Science
    # -----------------------------------------------------------------------
    ("data_science", "junior"): BenchmarkProfile(
        area="data_science", seniority="junior",
        score_p50=35.0, score_p75=50.0, min_expected=28.0,
        approval_rate=0.32,
        key_signals=("Python/R básico", "análise exploratória", "Pandas/NumPy", "projetos acadêmicos"),
        calibration_note=(
            "Júniores de data science: 28-50 pts. Kaggle/projetos acadêmicos são evidência válida "
            "mas pesa menos que experiência real. Não equiparar portfolio acadêmico a produção."
        ),
    ),
    ("data_science", "pleno"): BenchmarkProfile(
        area="data_science", seniority="pleno",
        score_p50=56.0, score_p75=70.0, min_expected=48.0,
        approval_rate=0.48,
        key_signals=("ML em produção", "comunicação de resultados", "SQL avançado", "feature engineering"),
        calibration_note=(
            "Plenos de data science: 48-70 pts. Exigir modelos em produção (não só notebooks). "
            "Comunicação de resultados para stakeholders não-técnicos é critério diferenciador."
        ),
    ),
    ("data_science", "senior"): BenchmarkProfile(
        area="data_science", seniority="senior",
        score_p50=70.0, score_p75=84.0, min_expected=62.0,
        approval_rate=0.40,
        key_signals=("MLOps", "estratégia de dados", "mentoria", "impacto de negócio mensurável"),
        calibration_note=(
            "Sêniores de data science: 62-84 pts. Verificar impacto de negócio direto (receita, redução de custo). "
            "MLOps e ciclo completo de produção são obrigatórios."
        ),
    ),

    # -----------------------------------------------------------------------
    # Legal
    # -----------------------------------------------------------------------
    ("legal", "junior"): BenchmarkProfile(
        area="legal", seniority="junior",
        score_p50=40.0, score_p75=55.0, min_expected=35.0,
        approval_rate=0.38,
        key_signals=("OAB ativa", "pesquisa jurídica", "elaboração de peças básicas"),
        calibration_note=(
            "Advogados júniores: 35-55 pts. OAB ativa é requisito, não diferencial. "
            "Avaliar qualidade técnica de peças e pesquisa, não apenas presença do título."
        ),
    ),
    ("legal", "pleno"): BenchmarkProfile(
        area="legal", seniority="pleno",
        score_p50=60.0, score_p75=74.0, min_expected=52.0,
        approval_rate=0.50,
        key_signals=("contencioso próprio", "contratos complexos", "área de especialização definida"),
        calibration_note=(
            "Advogados plenos: 52-74 pts. Verificar especialização real (trabalhista, tributário, M&A). "
            "Presença em audiências ou negociações — evidência explícita de complexidade."
        ),
    ),
    ("legal", "senior"): BenchmarkProfile(
        area="legal", seniority="senior",
        score_p50=73.0, score_p75=87.0, min_expected=65.0,
        approval_rate=0.42,
        key_signals=("liderança de equipe jurídica", "estratégia legal", "relacionamento com clientes chave"),
        calibration_note=(
            "Advogados sêniores/sócios: 65-87 pts. Verificar carteira de clientes ou liderança "
            "de casos estratégicos. Reconhecimento externo (Chambers, Legal 500) é sinal forte."
        ),
    ),

    # -----------------------------------------------------------------------
    # Product Management
    # -----------------------------------------------------------------------
    ("product_management", "junior"): BenchmarkProfile(
        area="product_management", seniority="junior",
        score_p50=36.0, score_p75=50.0, min_expected=28.0,
        approval_rate=0.30,
        key_signals=("discovery básico", "user stories", "colaboração com dev/design"),
        calibration_note=(
            "PMs júniores: 28-50 pts. Verificar entendimento real de ciclo de produto. "
            "Papéis de Product Owner ≠ Product Manager — analisar escopo de decisão real."
        ),
    ),
    ("product_management", "pleno"): BenchmarkProfile(
        area="product_management", seniority="pleno",
        score_p50=57.0, score_p75=71.0, min_expected=50.0,
        approval_rate=0.46,
        key_signals=("roadmap", "métricas de produto (DAU/MAU/NPS)", "priorização estratégica"),
        calibration_note=(
            "PMs plenos: 50-71 pts. Exigir métricas de impacto próprio (NPS, conversão, retenção). "
            "Roadmap ≠ backlog. Verificar evidência de decisões de priorização com tradeoffs documentados."
        ),
    ),
    ("product_management", "senior"): BenchmarkProfile(
        area="product_management", seniority="senior",
        score_p50=71.0, score_p75=85.0, min_expected=63.0,
        approval_rate=0.38,
        key_signals=("visão de produto", "alinhamento de stakeholders C-level", "produto 0→1 ou escala"),
        calibration_note=(
            "PMs sêniores: 63-85 pts. Verificar ownership de produto completo (P&L, estratégia). "
            "Lançamentos de 0→1 ou crescimento de escala são critérios diferenciadores."
        ),
    ),
}

# Mapeamento de aliases comuns para área canônica
_AREA_ALIASES: dict[str, str] = {
    "software": "software_engineering",
    "engenharia_de_software": "software_engineering",
    "engineering": "software_engineering",
    "dev": "software_engineering",
    "desenvolvimento": "software_engineering",
    "tech": "software_engineering",
    "data": "data_science",
    "ml": "data_science",
    "machine_learning": "data_science",
    "analytics": "data_science",
    "direito": "legal",
    "juridico": "legal",
    "advocacia": "legal",
    "produto": "product_management",
    "pm": "product_management",
    "product": "product_management",
}

_SENIORITY_ALIASES: dict[str, str] = {
    "estagio": "junior",
    "estagiario": "junior",
    "trainee": "junior",
    "jr": "junior",
    "júnior": "junior",
    "mid": "pleno",
    "mid-level": "pleno",
    "sr": "senior",
    "sênior": "senior",
    "seniority": "senior",
    "principal": "staff",
    "staff_engineer": "staff",
    "lead": "staff",
}


def _normalize_area(raw: str) -> str | None:
    if not raw:
        return None
    key = raw.lower().strip().replace(" ", "_").replace("-", "_")
    return _AREA_ALIASES.get(key, key if key in {b.area for b in _BENCHMARKS.values()} else None)


def _normalize_seniority(raw: str) -> str | None:
    if not raw:
        return None
    key = raw.lower().strip().replace(" ", "_").replace("-", "_")
    return _SENIORITY_ALIASES.get(key, key if key in {"junior", "pleno", "senior", "staff"} else None)


class SectorBenchmarkService:
    """
    Retorna contexto de benchmark setorial para enriquecer prompts de avaliação.

    Uso em rubric_evaluation_service.py:
        ctx = sector_benchmark_service.get_benchmark_context(area="software_engineering", seniority="senior")
        if ctx:
            prompt += f"\\n\\n## Benchmark Setorial (anti-sycophancy)\\n{ctx}"
    """

    def get_benchmark_context(self, area: str = "", seniority: str = "") -> str:
        """
        Retorna string de contexto de benchmark para injeção no prompt LLM.

        Retorna string vazia se não houver benchmark para a combinação area+seniority.
        Nunca lança exceção — falha silenciosa (não bloqueia avaliação).
        """
        try:
            norm_area = _normalize_area(area)
            norm_seniority = _normalize_seniority(seniority)

            if not norm_area or not norm_seniority:
                return ""

            profile = _BENCHMARKS.get((norm_area, norm_seniority))
            if not profile:
                return ""

            return (
                f"Área: {norm_area} | Senioridade: {norm_seniority}\n"
                f"Score mediano (P50) histórico: {profile.score_p50:.0f} pts\n"
                f"Score 75º percentil (P75): {profile.score_p75:.0f} pts\n"
                f"Score mínimo esperado para aprovação: {profile.min_expected:.0f} pts\n"
                f"Taxa histórica de aprovação neste segmento: {profile.approval_rate:.0%}\n"
                f"Sinais obrigatórios para o nível: {', '.join(profile.key_signals)}\n"
                f"INSTRUÇÃO DE CALIBRAÇÃO: {profile.calibration_note}\n"
                f"IMPORTANTE: Calibre seu score contra este benchmark. "
                f"Score acima do P75 ({profile.score_p75:.0f}) exige justificativa explícita e excepcional."
            )
        except Exception as exc:
            logger.debug("SectorBenchmarkService.get_benchmark_context falhou: %s", exc)
            return ""

    def get_profile(self, area: str, seniority: str) -> BenchmarkProfile | None:
        """Retorna o BenchmarkProfile para testes e auditoria."""
        norm_area = _normalize_area(area)
        norm_seniority = _normalize_seniority(seniority)
        if not norm_area or not norm_seniority:
            return None
        return _BENCHMARKS.get((norm_area, norm_seniority))

    def list_supported(self) -> list:
        """Lista todas as combinações area+seniority suportadas."""
        return list(_BENCHMARKS.keys())


# Instância de módulo — singleton leve (stateless, sem DB)
sector_benchmark_service = SectorBenchmarkService()
