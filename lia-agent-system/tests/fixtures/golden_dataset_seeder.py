"""
Golden Dataset para Bias Audit Baseline — 100 candidatos sintéticos.
Balanceados por: gênero, faixa etária, PCD, região.
Usado para estabelecer baseline da Four-Fifths Rule antes do go-live.

Uso:
    python -m tests.fixtures.golden_dataset_seeder --company-id <uuid>
"""
from __future__ import annotations
import asyncio
import logging
import random
import uuid
from datetime import date, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Distribuição balanceada ──────────────────────────────────────────────────
# 50 candidatos por gênero (M/F)
# 25 por faixa etária (<30 / 30-40 / 40-50 / 50+)
# 10% PCD (10 candidatos)
# Regiões: SE(40) / NE(25) / S(20) / N(10) / CO(5)

GENDERS = ["M"] * 50 + ["F"] * 50
AGE_GROUPS = ["<30"] * 25 + ["30-40"] * 25 + ["40-50"] * 25 + ["50+"] * 25
REGIONS = ["SE"] * 40 + ["NE"] * 25 + ["S"] * 20 + ["N"] * 10 + ["CO"] * 5
PCD_FLAGS = [True] * 10 + [False] * 90

FIRST_NAMES_M = ["Carlos", "João", "Pedro", "Lucas", "Rafael", "Marcos", "Bruno", "Diego", "Felipe", "André",
                  "Gabriel", "Eduardo", "Ricardo", "Fernando", "Thiago", "Rodrigo", "Leonardo", "Gustavo", "Alexandre", "Matheus"]
FIRST_NAMES_F = ["Ana", "Maria", "Paula", "Fernanda", "Camila", "Juliana", "Amanda", "Beatriz", "Larissa", "Leticia",
                  "Patricia", "Aline", "Renata", "Daniela", "Mariana", "Carolina", "Vanessa", "Claudia", "Simone", "Tatiana"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Costa", "Ferreira", "Rodrigues", "Almeida", "Nascimento",
               "Araújo", "Gomes", "Martins", "Pereira", "Carvalho", "Ribeiro", "Freitas", "Barbosa", "Correia", "Mendes"]

SKILLS_POOL = ["Python", "JavaScript", "SQL", "Excel", "PowerBI", "Gestão de Equipes", "Atendimento ao Cliente",
                "Logística", "Vendas", "Marketing Digital", "Análise de Dados", "Comunicação", "Liderança"]

CITY_BY_REGION = {
    "SE": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Campinas"],
    "NE": ["Salvador", "Fortaleza", "Recife", "Natal"],
    "S": ["Porto Alegre", "Curitiba", "Florianópolis"],
    "N": ["Manaus", "Belém"],
    "CO": ["Brasília", "Goiânia"],
}


def _generate_candidate(idx: int) -> Dict[str, Any]:
    """Gera um candidato sintético com dados balanceados."""
    random.seed(idx)
    gender = GENDERS[idx]
    age_group = AGE_GROUPS[idx]
    region = REGIONS[idx]
    pcd = PCD_FLAGS[idx]

    first_name = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
    last_name = random.choice(LAST_NAMES)
    city = random.choice(CITY_BY_REGION[region])

    age_ranges = {"<30": (22, 29), "30-40": (30, 40), "40-50": (41, 50), "50+": (51, 62)}
    age_min, age_max = age_ranges[age_group]
    birth_year = date.today().year - random.randint(age_min, age_max)
    birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))

    # Score uniforme (não discriminatório) — distribuição normal centrada em 70
    lia_score = max(40, min(98, int(random.gauss(70, 12))))
    experience_years = max(0, random.randint(0, 25))

    return {
        "id": str(uuid.uuid4()),
        "name": f"{first_name} {last_name}",
        "email": f"candidato{idx:03d}@golden-dataset.test",
        "gender": gender,
        "birth_date": birth_date.isoformat(),
        "age_group": age_group,
        "region": region,
        "city": city,
        "disability": pcd,
        "lia_score": lia_score,
        "experience_years": experience_years,
        "skills": random.sample(SKILLS_POOL, k=random.randint(3, 7)),
        "is_golden_dataset": True,
    }


def generate_golden_dataset() -> List[Dict[str, Any]]:
    """Gera os 100 candidatos do golden dataset."""
    candidates = []
    indices = list(range(100))
    random.shuffle(indices)
    for i, idx in enumerate(indices):
        c = _generate_candidate(idx)
        candidates.append(c)
    return candidates


async def seed_bias_audit_baseline(company_id: str, job_id: str) -> None:
    """Persiste o baseline de bias audit para um par company/job."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.shared.services.bias_audit_service import BiasAuditService

        candidates = generate_golden_dataset()
        logger.info("[GoldenDataset] Gerando baseline com %d candidatos para company=%s", len(candidates), company_id)

        async with AsyncSessionLocal() as db:
            svc = BiasAuditService()
            snapshot = await svc.run_audit(
                job_id=job_id,
                company_id=company_id,
                db=db,
                candidates_override=candidates,
            )
            if snapshot:
                await svc.save_snapshot(snapshot, db)
                logger.info("[GoldenDataset] Baseline salvo: snapshot_id=%s", getattr(snapshot, "id", "N/A"))
    except Exception as exc:
        logger.error("[GoldenDataset] Erro ao seed baseline: %s", exc)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed bias audit golden dataset baseline")
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--job-id", default="golden-baseline-job")
    args = parser.parse_args()
    asyncio.run(seed_bias_audit_baseline(args.company_id, args.job_id))
