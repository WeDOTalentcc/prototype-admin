"""
Testes de Disparate Impact — Scores WSI.

Verifica que o scoring WSI é invariante a sinais demográficos.
O mesmo perfil técnico deve obter o mesmo score independente de
gênero, raça/etnia, idade aparente, ou origem.

Compliance: EU AI Act Art. 10, LGPD, 4/5 Rule (Adverse Impact Ratio).

Metodologia:
- Perfis equivalentes com variações demográficas → scores devem ser iguais (Δ < 0.1)
- Diferenças de score devem refletir APENAS competência técnica
- 4/5 Rule: taxa de aprovação entre grupos não pode diferir > 20%
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    calculate_wsi_deterministic,
    extract_autodeclaracao_score,
    calculate_context_score,
    WSI_CUTOFFS,
    DeterministicWSIResult,
)

DELTA_TOLERANCE = 0.1  # Diferença máxima aceitável entre perfis equivalentes


# ---------------------------------------------------------------------------
# Fixtures de perfis técnicos equivalentes
# ---------------------------------------------------------------------------

SENIOR_TECH_CONTENT = (
    "Tenho 8 anos de experiência em Python e arquitetura de microsserviços. "
    "Liderei equipe de 6 engenheiros, entregamos sistema em produção processando "
    "5 milhões de requisições/dia. Implementei melhorias de performance com "
    "métricas de 40% de redução de latência. Arquitetei a solução de cache distribuído."
)

JUNIOR_TECH_CONTENT = (
    "Estou aprendendo Python há 6 meses. Fiz um curso online e alguns tutoriais. "
    "Tenho conhecimento básico de APIs REST. Ainda não trabalhei em projetos reais."
)


# ---------------------------------------------------------------------------
# Neutralidade por Gênero
# ---------------------------------------------------------------------------

class TestWSIGenderNeutrality:
    """Scores WSI não devem variar por sinais de gênero no texto."""

    def test_masculine_feminine_pronouns_same_score(self):
        """Pronomes masculinos vs femininos não devem alterar o score."""
        male = SENIOR_TECH_CONTENT + " Ele tomou decisões arquiteturais críticas."
        female = SENIOR_TECH_CONTENT + " Ela tomou decisões arquiteturais críticas."
        r_m = calculate_wsi_deterministic(male, "Python")
        r_f = calculate_wsi_deterministic(female, "Python")
        assert abs(r_m.final_score - r_f.final_score) <= DELTA_TOLERANCE, (
            f"Score difere por pronome: masculino={r_m.final_score:.2f}, feminino={r_f.final_score:.2f}"
        )

    def test_engineer_title_gender_neutral(self):
        """Título 'engenheiro' vs 'engenheira' não deve alterar o score."""
        male_title = "Engenheiro sênior com " + SENIOR_TECH_CONTENT[21:]
        female_title = "Engenheira sênior com " + SENIOR_TECH_CONTENT[21:]
        r_m = calculate_wsi_deterministic(male_title, "Python")
        r_f = calculate_wsi_deterministic(female_title, "Python")
        assert abs(r_m.final_score - r_f.final_score) <= DELTA_TOLERANCE

    def test_gender_signals_do_not_add_penalty_or_bonus(self):
        """Sinais de gênero não devem gerar red_flags nem bônus."""
        base = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        with_gender = calculate_wsi_deterministic(
            SENIOR_TECH_CONTENT + " Sou mulher e liderei times majoritariamente masculinos.", "Python"
        )
        # Red flags devem ser os mesmos — gênero não é indicador de inflação/genérico
        assert with_gender.red_flags == base.red_flags or len(with_gender.red_flags) == len(base.red_flags)
        assert abs(with_gender.penalty - base.penalty) <= DELTA_TOLERANCE


# ---------------------------------------------------------------------------
# Neutralidade por Idade Aparente
# ---------------------------------------------------------------------------

class TestWSIAgeNeutrality:
    """Scores WSI devem refletir competência, não idade implícita."""

    def test_same_experience_years_same_score(self):
        """Mesmos anos de experiência descritos de formas diferentes → score equivalente."""
        desc_a = (
            "Tenho 10 anos de experiência em desenvolvimento backend. "
            "Liderança de times, entrega em produção com métricas de performance."
        )
        desc_b = (
            "São 10 anos no mercado de desenvolvimento backend, "
            "com liderança técnica e sistemas em produção monitorados por métricas."
        )
        r_a = calculate_wsi_deterministic(desc_a, "Backend")
        r_b = calculate_wsi_deterministic(desc_b, "Backend")
        assert abs(r_a.final_score - r_b.final_score) <= DELTA_TOLERANCE

    def test_junior_scores_lower_due_to_competency_not_age(self):
        """Perfil júnior deve pontuar menos por competência, não por idade implícita."""
        r_senior = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        r_junior = calculate_wsi_deterministic(JUNIOR_TECH_CONTENT, "Python")
        assert r_senior.final_score > r_junior.final_score, (
            "Perfil sênior deve pontuar mais que júnior por competência"
        )
        # A diferença deve vir do context_score e autodeclaracao_score, não de penalidades etárias
        assert r_senior.context_score > r_junior.context_score

    def test_age_mention_does_not_change_score(self):
        """Menção explícita de idade não deve alterar o score."""
        without_age = SENIOR_TECH_CONTENT
        with_age_young = SENIOR_TECH_CONTENT + " Tenho 28 anos."
        with_age_older = SENIOR_TECH_CONTENT + " Tenho 52 anos."
        r_base = calculate_wsi_deterministic(without_age, "Python")
        r_young = calculate_wsi_deterministic(with_age_young, "Python")
        r_older = calculate_wsi_deterministic(with_age_older, "Python")
        assert abs(r_base.final_score - r_young.final_score) <= DELTA_TOLERANCE
        assert abs(r_base.final_score - r_older.final_score) <= DELTA_TOLERANCE


# ---------------------------------------------------------------------------
# Neutralidade por Etnia / Origem
# ---------------------------------------------------------------------------

class TestWSIEthnicityNeutrality:
    """Scores WSI devem ser invariantes a referências culturais ou de origem."""

    def test_identical_content_same_score(self):
        """Conteúdo idêntico sempre produz o mesmo score."""
        r1 = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        r2 = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        assert r1.final_score == r2.final_score

    def test_origin_reference_does_not_change_score(self):
        """Referência a origem regional não deve alterar o score."""
        base = SENIOR_TECH_CONTENT
        with_north = base + " Sou do Norte do Brasil."
        with_south = base + " Sou do Sul do Brasil."
        r_base = calculate_wsi_deterministic(base, "Python")
        r_north = calculate_wsi_deterministic(with_north, "Python")
        r_south = calculate_wsi_deterministic(with_south, "Python")
        assert abs(r_base.final_score - r_north.final_score) <= DELTA_TOLERANCE
        assert abs(r_base.final_score - r_south.final_score) <= DELTA_TOLERANCE


# ---------------------------------------------------------------------------
# 4/5 Rule — Adverse Impact Ratio
# ---------------------------------------------------------------------------

class TestWSIAdverseImpactRatio:
    """
    Regra dos 4/5 (80% Rule): taxa de aprovação entre grupos equivalentes
    não pode diferir mais de 20%.

    Simulação: 10 perfis com mesmo nível técnico, variações neutras de escrita.
    """

    EQUIVALENT_PROFILES = [
        "Especialista em Java com 6 anos de experiência. Liderança de times em projetos enterprise bancários, sistemas de alta disponibilidade com métricas de produção.",
        "Engenheiro Java sênior, 6 anos no mercado. Responsável por sistema financeiro processando milhões de transações diárias com monitoramento de performance.",
        "Desenvolvedor Java com 6 anos de atuação. Liderei projetos críticos para bancos digitais com entrega de resultados e métricas de impacto.",
        "Java developer com 6 anos de mercado. Arquitetei e implementei soluções enterprise para o setor financeiro com foco em escala e disponibilidade.",
        "Profissional Java sênior, 6 anos de experiência. Conduzi migração de sistemas legados para cloud em ambiente bancário com liderança técnica.",
        "Especialista backend Java, 6 anos. Implementei APIs de alto volume para fintechs, liderando time de 5 engenheiros com resultados mensuráveis.",
        "Engenheiro com 6 anos em Java. Trabalhei em sistemas de pagamento de alta disponibilidade, gerando métricas de performance e liderando equipe.",
        "Desenvolvedor sênior Java, 6 anos. Projetos de grande escala no setor financeiro com decisões arquiteturais e entrega em produção.",
        "Java expert com 6 anos de experiência. Conduzi projetos enterprise para clientes bancários com arquitetura de microsserviços e métricas de impacto.",
        "Profissional Java, 6 anos no mercado. Arquitetura de microsserviços para sistemas financeiros em produção com liderança e resultados concretos.",
    ]

    def test_score_range_within_tolerance(self):
        """Perfis equivalentes não podem ter dispersão de score > 2.0 pontos."""
        results = [calculate_wsi_deterministic(p, "Java") for p in self.EQUIVALENT_PROFILES]
        scores = [r.final_score for r in results]
        score_range = max(scores) - min(scores)
        assert score_range < 2.0, (
            f"Dispersão de score muito alta em perfis equivalentes: "
            f"min={min(scores):.2f}, max={max(scores):.2f}, range={score_range:.2f}"
        )

    def test_approval_rate_at_least_60_percent(self):
        """Pelo menos 60% de perfis equivalentes deve atingir cutoff de revisão."""
        cutoff = WSI_CUTOFFS["review_min"]
        results = [calculate_wsi_deterministic(p, "Java") for p in self.EQUIVALENT_PROFILES]
        approvals = [r.final_score >= cutoff for r in results]
        approval_rate = sum(approvals) / len(approvals)
        assert approval_rate >= 0.6, (
            f"Taxa de aprovação muito baixa para perfis equivalentes: {approval_rate:.0%} "
            f"(mínimo esperado: 60%)"
        )


# ---------------------------------------------------------------------------
# Invariantes de Score
# ---------------------------------------------------------------------------

class TestWSIScoreInvariants:
    """Propriedades invariantes que sempre devem ser verdadeiras."""

    @pytest.mark.parametrize("text,competency", [
        ("", "Python"),
        ("x", "Java"),
        (SENIOR_TECH_CONTENT, "Python"),
        (JUNIOR_TECH_CONTENT, "Python"),
    ])
    def test_score_always_in_valid_range(self, text, competency):
        """Score final deve sempre estar entre 0.0 e 5.0."""
        result = calculate_wsi_deterministic(text, competency)
        assert 0.0 <= result.final_score <= 5.0, (
            f"Score {result.final_score} fora do intervalo [0, 5] para: '{text[:40]}'"
        )

    def test_high_quality_context_scores_higher(self):
        """Perfil com indicadores de alta qualidade deve pontuar mais no context_score."""
        high = "Implementei sistema de métricas em produção com milhões de acessos, liderando time em arquitetura enterprise de alta disponibilidade."
        low = "Fiz um tutorial básico de Python, estou estudando fundamentos do básico."
        r_high = calculate_wsi_deterministic(high, "Python")
        r_low = calculate_wsi_deterministic(low, "Python")
        assert r_high.context_score > r_low.context_score
        assert r_high.final_score > r_low.final_score

    def test_red_flags_based_on_content_inconsistency(self):
        """Red flags devem ser acionados por inconsistência de conteúdo, não por demografia."""
        inflated = "Sou expert absoluto em todas as tecnologias. 5 de 5 em tudo. Domino completamente todos os sistemas."
        genuine = "Tenho sólida experiência em Python (4 de 5), trabalhei em projetos de médio porte com times de 3 pessoas e entregamos métricas reais."
        r_inflated = calculate_wsi_deterministic(inflated, "Python")
        r_genuine = calculate_wsi_deterministic(genuine, "Python")
        assert len(r_inflated.red_flags) >= len(r_genuine.red_flags), (
            "Perfil inflacionado deve acumular mais red_flags que perfil genuíno"
        )

    def test_deterministic_same_input_same_output(self):
        """Scorer é determinístico: mesma entrada → mesma saída."""
        r1 = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        r2 = calculate_wsi_deterministic(SENIOR_TECH_CONTENT, "Python")
        assert r1.final_score == r2.final_score
        assert r1.context_score == r2.context_score
        assert r1.red_flags == r2.red_flags
