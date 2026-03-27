"""
Golden dataset para Bias Audit baseline.

Dados sintéticos balanceados para validar que o algoritmo Four-Fifths Rule
não viola métricas de adverse impact nas 4 dimensões protegidas:
  - gender (gênero)
  - age_group (faixa etária)
  - disability (PCD)
  - region (região)

Todos os dados são SINTÉTICOS — não representam candidatos reais.
Gerados para teste, sem PII real.
"""
from typing import List, Dict, Any


def get_balanced_baseline_candidates(job_id: str = "baseline-job-001") -> List[Dict[str, Any]]:
    """
    Retorna 200 candidatos sintéticos balanceados demograficamente.

    Distribuição intencional:
      - 100 homens, 100 mulheres (50/50)
      - 50 por faixa: 18-30, 31-40, 41-50, 51+
      - 20 PCD, 180 não-PCD (10% alinhado com IBGE)
      - 50 por região: Sul, Sudeste, Nordeste, Centro-Norte

    Aprovação intencionalmente equilibrada para Four-Fifths ≥ 0.80:
      - Overall approval rate ~60%
      - Por gênero: ≥ 0.80 ratio
      - Por idade: ≥ 0.80 ratio
      - Por PCD: ≥ 0.80 ratio
      - Por região: ≥ 0.80 ratio
    """
    # Estratégia: aprovação = (idx % 10) < 6  →  exatamente 60% para qualquer grupo
    # cujo tamanho seja múltiplo de 10.
    #
    # Prova: LCM(4,10)=20 → em 20 posições espaçadas de 4, cada valor %10 aparece exatamente
    # uma vez por ciclo de LCM(4,10)/4 = 5 → 3 em 5 satisfazem %10<6 → 60%.
    #
    # Distribuição: gender(100+100), age_group(50×4), region(50×4), disability(180+20)
    # Todos múltiplos de 10 → aprovação exata 60% por grupo → AIR=1.0 ≥ 0.80 ✅

    genders = ["male"] * 100 + ["female"] * 100
    # age_group cíclico: idx % 4 → 50 por grupo (LCM(4,10)=20 garante 60% uniforme)
    age_group_map = {0: "18-30", 1: "31-40", 2: "41-50", 3: "51+"}
    # region em blocos contíguos de 50 (todos múltiplos de 10 → 60% exato)
    regions_list = ["sul"] * 50 + ["sudeste"] * 50 + ["nordeste"] * 50 + ["centro_norte"] * 50
    # disability: 0-179=non-PCD (180), 180-199=PCD (20) — ambos múltiplos de 10
    disabilities = [False] * 180 + [True] * 20

    candidates = []
    for idx in range(200):
        approved = (idx % 10) < 6  # exatamente 60% em qualquer subgrupo múltiplo de 10

        candidates.append({
            "id": f"synthetic-{idx:04d}",
            "job_id": job_id,
            "gender": genders[idx],
            "age_group": age_group_map[idx % 4],
            "disability": disabilities[idx],
            "region": regions_list[idx],
            "approved": approved,
            "lia_score": 70 if approved else 45,
            "synthetic": True,  # Marcador: dado sintético
        })

    return candidates


def assert_four_fifths_rule(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida Four-Fifths Rule (80% Rule) no dataset.

    Adverse Impact Ratio = menor taxa de aprovação / maior taxa de aprovação
    Threshold: AIR >= 0.80 para conformidade.

    Returns:
        Dict com resultado por dimensão + passed (bool)
    """
    results = {}
    all_pass = True

    for dimension in ["gender", "age_group", "region"]:
        groups: Dict[str, Dict[str, int]] = {}
        for c in candidates:
            key = c.get(dimension, "unknown")
            if key not in groups:
                groups[key] = {"total": 0, "approved": 0}
            groups[key]["total"] += 1
            if c.get("approved"):
                groups[key]["approved"] += 1

        rates = {k: v["approved"] / v["total"] if v["total"] > 0 else 0
                 for k, v in groups.items()}
        max_rate = max(rates.values()) if rates else 1

        dim_results = {}
        for group, rate in rates.items():
            air = rate / max_rate if max_rate > 0 else 1.0
            passed = air >= 0.80
            if not passed:
                all_pass = False
            dim_results[group] = {"rate": round(rate, 3), "air": round(air, 3), "passed": passed}

        results[dimension] = dim_results

    # PCD check
    pcd_groups = {"pcd": {"total": 0, "approved": 0}, "non_pcd": {"total": 0, "approved": 0}}
    for c in candidates:
        key = "pcd" if c.get("disability") else "non_pcd"
        pcd_groups[key]["total"] += 1
        if c.get("approved"):
            pcd_groups[key]["approved"] += 1

    pcd_rates = {k: v["approved"] / v["total"] if v["total"] > 0 else 0 for k, v in pcd_groups.items()}
    max_pcd_rate = max(pcd_rates.values()) if pcd_rates else 1
    pcd_dim = {}
    for group, rate in pcd_rates.items():
        air = rate / max_pcd_rate if max_pcd_rate > 0 else 1.0
        passed = air >= 0.80
        if not passed:
            all_pass = False
        pcd_dim[group] = {"rate": round(rate, 3), "air": round(air, 3), "passed": passed}
    results["disability"] = pcd_dim

    return {"dimensions": results, "all_passed": all_pass}
