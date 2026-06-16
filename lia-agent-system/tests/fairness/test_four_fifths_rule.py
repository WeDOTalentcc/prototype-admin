"""
Four-Fifths Rule (Regra dos 4/5) — Bias Audit Baseline

Testa que a taxa de seleção (score >= 60) é equitativa entre grupos demográficos.
Critério: adverse_impact_ratio >= 0.80 para todas as dimensões protegidas.

Referências:
- dei-fairness §4 (Bias Audit Dashboard — adverse_impact_ratio)
- screening-compliance §5 (Four-Fifths Rule)
- EEOC Uniform Guidelines on Employee Selection Procedures (29 CFR §1607)

Golden dataset: tests/fixtures/golden_dataset.py
  60 candidatos sintéticos com distribuição equilibrada por grupo demográfico.
  Scores determinísticos (independentes de dados demográficos — pré-condição do teste).
"""
import pytest
from itertools import combinations
from typing import List, Tuple

from tests.fixtures.golden_dataset import (
    GOLDEN_DATASET,
    APPROVAL_THRESHOLD,
    GROUPS,
    get_group,
    selection_rate,
    adverse_impact_ratio,
)

FOUR_FIFTHS_MIN_RATIO = 0.80  # critério EEOC / dei-fairness §4


# ---------------------------------------------------------------------------
# Estrutura do dataset
# ---------------------------------------------------------------------------

class TestGoldenDatasetIntegrity:
    """Valida que o golden dataset está bem formado antes dos testes de fairness."""

    def test_total_count(self):
        """Dataset deve ter exatamente 60 candidatos."""
        assert len(GOLDEN_DATASET) == 60

    def test_all_ids_unique(self):
        """Todos os IDs devem ser únicos."""
        ids = [c["id"] for c in GOLDEN_DATASET]
        assert len(ids) == len(set(ids))

    def test_all_required_fields_present(self):
        """Todos os campos obrigatórios devem estar presentes em cada candidato."""
        required = {"id", "name", "gender", "age_group", "disability", "region", "tech_level", "score", "approved"}
        for c in GOLDEN_DATASET:
            assert required.issubset(c.keys()), f"Candidato {c['id']} com campos faltando: {required - c.keys()}"

    def test_approved_matches_threshold(self):
        """Campo 'approved' deve ser consistente com score >= APPROVAL_THRESHOLD."""
        for c in GOLDEN_DATASET:
            expected = c["score"] >= APPROVAL_THRESHOLD
            assert c["approved"] == expected, (
                f"Candidato {c['id']}: score={c['score']} mas approved={c['approved']} (esperado {expected})"
            )

    def test_demographic_values_valid(self):
        """Todos os valores demográficos devem estar nos grupos esperados."""
        for c in GOLDEN_DATASET:
            for dim, valid_values in GROUPS.items():
                assert c[dim] in valid_values, (
                    f"Candidato {c['id']}: {dim}={c[dim]!r} não é um valor válido {valid_values}"
                )

    def test_scores_in_range(self):
        """Todos os scores devem estar no intervalo [0, 99]."""
        for c in GOLDEN_DATASET:
            assert 0 <= c["score"] <= 99, f"Candidato {c['id']}: score={c['score']} fora do range"

    def test_score_tiers_distribution(self):
        """Dataset deve conter os 3 tiers de performance (alta, média, baixa)."""
        high = [c for c in GOLDEN_DATASET if c["score"] >= 75]
        mid = [c for c in GOLDEN_DATASET if 45 <= c["score"] < 75]
        low = [c for c in GOLDEN_DATASET if c["score"] < 45]
        assert len(high) == 20, f"Esperado 20 candidatos alta performance, got {len(high)}"
        assert len(mid) == 20, f"Esperado 20 candidatos média performance, got {len(mid)}"
        assert len(low) == 20, f"Esperado 20 candidatos baixa performance, got {len(low)}"


# ---------------------------------------------------------------------------
# Four-Fifths Rule — Dimensão: Gênero
# ---------------------------------------------------------------------------

class TestFourFifthsRuleGender:
    """
    Regra dos 4/5 por gênero.
    Taxa de aprovação de qualquer subgrupo de gênero não pode ser < 80%
    da taxa do grupo de maior aprovação.
    """

    def test_gender_groups_present(self):
        """Todos os grupos de gênero devem ter pelo menos 1 candidato no dataset."""
        for g in GROUPS["gender"]:
            group = get_group("gender", g)
            assert len(group) > 0, f"Grupo de gênero '{g}' não tem candidatos no dataset"

    def test_adverse_impact_ratio_masculino_feminino(self):
        """Ratio masculino vs feminino >= 0.80."""
        g_m = get_group("gender", "masculino")
        g_f = get_group("gender", "feminino")
        ratio = adverse_impact_ratio(g_m, g_f)
        assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
            f"Adverse impact ratio masculino/feminino = {ratio:.3f} < {FOUR_FIFTHS_MIN_RATIO} "
            f"(masculino: {selection_rate(g_m):.2%}, feminino: {selection_rate(g_f):.2%})"
        )

    def test_adverse_impact_ratio_all_gender_pairs(self):
        """Para todo par de grupos de gênero, o adverse_impact_ratio deve ser >= 0.80."""
        gender_groups = ["masculino", "feminino", "nao_binario"]
        for g1, g2 in combinations(gender_groups, 2):
            grp1 = get_group("gender", g1)
            grp2 = get_group("gender", g2)
            ratio = adverse_impact_ratio(grp1, grp2)
            assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
                f"Adverse impact ratio {g1}/{g2} = {ratio:.3f} < {FOUR_FIFTHS_MIN_RATIO} "
                f"({g1}: {selection_rate(grp1):.2%}, {g2}: {selection_rate(grp2):.2%})"
            )


# ---------------------------------------------------------------------------
# Four-Fifths Rule — Dimensão: Faixa Etária
# ---------------------------------------------------------------------------

class TestFourFifthsRuleAgeGroup:
    """
    Regra dos 4/5 por faixa etária.
    Proteção contra discriminação etária (Estatuto do Idoso, Lei 10.741/03).
    """

    def test_age_groups_present(self):
        for g in GROUPS["age_group"]:
            group = get_group("age_group", g)
            assert len(group) > 0

    def test_adverse_impact_ratio_all_age_pairs(self):
        """Para todo par de faixas etárias, adverse_impact_ratio >= 0.80."""
        for g1, g2 in combinations(GROUPS["age_group"], 2):
            grp1 = get_group("age_group", g1)
            grp2 = get_group("age_group", g2)
            ratio = adverse_impact_ratio(grp1, grp2)
            assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
                f"Adverse impact ratio {g1}/{g2} = {ratio:.3f} < {FOUR_FIFTHS_MIN_RATIO} "
                f"({g1}: {selection_rate(grp1):.2%}, {g2}: {selection_rate(grp2):.2%})"
            )

    def test_older_workers_not_disadvantaged(self):
        """
        Candidatos 50+ devem ter adverse_impact_ratio >= 0.80 em relação a 25-35.
        Verificação específica contra discriminação de idosos.
        """
        young = get_group("age_group", "25-35")
        senior = get_group("age_group", "50+")
        ratio = adverse_impact_ratio(young, senior)
        assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
            f"Candidatos 50+ disadvantaged: ratio={ratio:.3f} "
            f"(25-35: {selection_rate(young):.2%}, 50+: {selection_rate(senior):.2%})"
        )


# ---------------------------------------------------------------------------
# Four-Fifths Rule — Dimensão: PCD
# ---------------------------------------------------------------------------

class TestFourFifthsRuleDisability:
    """
    Regra dos 4/5 por deficiência (PCD).
    Proteção: Lei 8.213/91 (cotas), Lei 13.146/15 (Estatuto da Pessoa com Deficiência).
    """

    def test_disability_groups_present(self):
        for g in GROUPS["disability"]:
            group = get_group("disability", g)
            assert len(group) > 0

    def test_adverse_impact_ratio_pcd(self):
        """Candidatos com PCD não devem ter taxa de aprovação < 80% vs sem PCD."""
        com_pcd = get_group("disability", "com_pcd")
        sem_pcd = get_group("disability", "sem_pcd")
        ratio = adverse_impact_ratio(com_pcd, sem_pcd)
        assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
            f"Adverse impact ratio PCD = {ratio:.3f} < {FOUR_FIFTHS_MIN_RATIO} "
            f"(com_pcd: {selection_rate(com_pcd):.2%}, sem_pcd: {selection_rate(sem_pcd):.2%})"
        )


# ---------------------------------------------------------------------------
# Four-Fifths Rule — Dimensão: Região
# ---------------------------------------------------------------------------

class TestFourFifthsRuleRegion:
    """
    Regra dos 4/5 por região.
    Verificação contra discriminação socioeconômica por localização.
    """

    def test_region_groups_present(self):
        for g in GROUPS["region"]:
            group = get_group("region", g)
            assert len(group) > 0

    def test_adverse_impact_ratio_all_region_pairs(self):
        """Para todo par de regiões, adverse_impact_ratio >= 0.80."""
        for g1, g2 in combinations(GROUPS["region"], 2):
            grp1 = get_group("region", g1)
            grp2 = get_group("region", g2)
            ratio = adverse_impact_ratio(grp1, grp2)
            assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
                f"Adverse impact ratio {g1}/{g2} = {ratio:.3f} < {FOUR_FIFTHS_MIN_RATIO} "
                f"({g1}: {selection_rate(grp1):.2%}, {g2}: {selection_rate(grp2):.2%})"
            )

    def test_interior_not_disadvantaged_vs_sp(self):
        """
        Candidatos do interior não devem ser disadvantaged vs São Paulo.
        Verificação específica contra discriminação por região.
        """
        sp = get_group("region", "sp")
        interior = get_group("region", "interior")
        ratio = adverse_impact_ratio(sp, interior)
        assert ratio >= FOUR_FIFTHS_MIN_RATIO, (
            f"Interior disadvantaged: ratio={ratio:.3f} "
            f"(sp: {selection_rate(sp):.2%}, interior: {selection_rate(interior):.2%})"
        )


# ---------------------------------------------------------------------------
# Relatório de distribuição (informativo — não falha)
# ---------------------------------------------------------------------------

class TestBiasAuditReport:
    """
    Gera relatório de taxas de aprovação por dimensão demográfica.
    Não falha — apenas produz saída informativa para o bias audit dashboard.
    """

    def test_print_approval_rates_by_dimension(self, capsys):
        """Imprime as taxas de aprovação por grupo para auditoria."""
        total = len(GOLDEN_DATASET)
        approved_total = sum(1 for c in GOLDEN_DATASET if c["approved"])
        lines = [
            f"\n=== Bias Audit Report — Golden Dataset ({total} candidatos) ===",
            f"Threshold: score >= {APPROVAL_THRESHOLD}",
            f"Taxa global de aprovação: {approved_total}/{total} = {approved_total/total:.1%}",
            "",
        ]
        for dim, values in GROUPS.items():
            lines.append(f"[{dim.upper()}]")
            rates = {}
            for val in values:
                group = get_group(dim, val)
                rate = selection_rate(group)
                rates[val] = rate
                lines.append(f"  {val:20s}: {sum(c['approved'] for c in group):2d}/{len(group):2d} = {rate:.1%}")
            # calcular pior ratio
            all_pairs = list(combinations(values, 2))
            if all_pairs:
                min_ratio = min(
                    adverse_impact_ratio(get_group(dim, a), get_group(dim, b))
                    for a, b in all_pairs
                )
                status = "✅" if min_ratio >= FOUR_FIFTHS_MIN_RATIO else "❌"
                lines.append(f"  min adverse_impact_ratio: {min_ratio:.3f} {status}")
            lines.append("")

        print("\n".join(lines))
        # Não falha — relatório informativo
        assert True
