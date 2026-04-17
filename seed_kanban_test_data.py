"""
Seed Kanban Test Data
=====================
Popula candidatos em todas as etapas do kanban para as vagas:
  - Product Manager (V0037)
  - Tech Lead — Backend (V0039)

Distribui candidatos reais (já no BD) por todas as colunas:
  sourcing → screening → long_list → short_list →
  interview_hr → interview_technical → interview_manager →
  offer → hired | rejected

Cada candidato recebe scores realistas: lia_score, triagem, CV, técnico,
inglês, Big Five — para testar os modais de score no kanban.

Uso:
    cd lia-agent-system
    python3 ../seed_kanban_test_data.py --seed      # Insere dados
    python3 ../seed_kanban_test_data.py --clean     # Remove dados de teste
    python3 ../seed_kanban_test_data.py --reset     # Limpa + Insere
"""
import asyncio
import argparse
import json
import sys
import os
import uuid
from datetime import datetime, timedelta
from random import uniform, choice, randint, sample

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lia-agent-system"))

from lia_config.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

# ─── Constants ────────────────────────────────────────────────────────────────

COMPANY_ID = "00000000-0000-4000-a000-000000000001"
NOW = datetime.utcnow()

# Jobs to seed
TARGET_JOBS = {
    "Product Manager": "406731ad-388f-5ea5-a0b6-bdb6dadf186e",
    "Tech Lead — Backend": "e603b68b-febd-50e8-84e7-7568a28fede1",
}

# Stages (name → DB id for this company)
STAGE_MAP = {
    "sourcing":            "b85770d1-ef84-5622-aa76-7dddd432677f",
    "screening":           "08feb99a-588d-5e88-8b9f-47b191af6c13",
    "long_list":           "2d79e3a8-7ec9-549f-a1be-4b494079e31c",
    "short_list":          "a3bab07e-47cb-5dd4-8960-46e465339d21",
    "interview_hr":        "079249c8-a2fd-545c-8a1d-0ec483365839",
    "technical_test":      "859cc76b-fd3c-5b36-bddb-4351fa7d7ec7",
    "interview_technical": "585f497b-4a03-5715-9f45-19b11e050b00",
    "interview_manager":   "7036e4be-35e5-5080-8a2a-ef6c61b77816",
    "offer":               "5afe8376-a375-5034-a498-6457c809446e",
    "hired":               "e3054b9d-ad6c-5886-9e2b-ec2050ff295a",
    "rejected":            "0856af6e-1b2f-562b-b747-885787ccca83",
}

# How many candidates per stage per job
STAGE_DISTRIBUTION = {
    "sourcing":            5,
    "screening":           4,
    "long_list":           3,
    "short_list":          3,
    "interview_hr":        3,
    "technical_test":      2,
    "interview_technical": 2,
    "interview_manager":   2,
    "offer":               2,
    "hired":               2,
    "rejected":            2,
}

TOTAL_PER_JOB = sum(STAGE_DISTRIBUTION.values())  # 30

# Status mapping (vacancy_candidates.status) — valid values only
STAGE_TO_STATUS = {
    "sourcing":            "sourced",
    "screening":           "screening",
    "long_list":           "shortlisted",
    "short_list":          "shortlisted",
    "interview_hr":        "interview",
    "technical_test":      "interview",
    "interview_technical": "interview",
    "interview_manager":   "interview",
    "offer":               "offer",
    "hired":               "hired",
    "rejected":            "not_selected",
}

INTERVIEW_PLATFORMS = [
    {"platform": "microsoft_teams", "url": "https://teams.microsoft.com/l/meetup/lia-seed-001"},
    {"platform": "google_meet",     "url": "https://meet.google.com/lia-seed-002"},
    {"platform": "zoom",            "url": "https://zoom.us/j/99988877766"},
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _past(days_min: int, days_max: int) -> datetime:
    return NOW - timedelta(days=randint(days_min, days_max))


def _future(hours_min: int = 24, hours_max: int = 168) -> datetime:
    return NOW + timedelta(hours=randint(hours_min, hours_max))


def _score(lo: float, hi: float) -> float:
    return round(uniform(lo, hi), 1)


def _big_five() -> dict:
    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    return {t: _score(40, 95) for t in traits}


def _wsi_result() -> dict:
    """Simulated WSI screening result stored in additional_data."""
    return {
        "wsi_completed": True,
        "wsi_score": _score(55, 98),
        "wsi_answers": [
            {"question": "Descreva sua experiência com gestão de produto", "answer": "Trabalhei por 4 anos liderando roadmap em startup SaaS.", "score": _score(60, 95)},
            {"question": "Como você prioriza backlog?", "answer": "Uso framework RICE combinado com inputs de stakeholders.", "score": _score(65, 95)},
            {"question": "Experiência com OKRs?", "answer": "Implementei OKRs em duas empresas. Defino metas trimestrais alinhadas à estratégia.", "score": _score(70, 98)},
        ],
        "wsi_completed_at": (NOW - timedelta(days=randint(1, 10))).isoformat(),
        "wsi_recommendation": choice(["Aprovado", "Aprovado com ressalvas", "Em avaliação"]),
    }


def _build_additional_data(stage: str, lia_score: float) -> dict:
    """Build additional_data JSON with scores for kanban modals."""
    data: dict = {
        "source_detail": choice(["LinkedIn", "Indicação", "Portal de vagas", "Banco de talentos"]),
        "days_in_stage": randint(1, 14),
    }

    # Scores used by KanbanCardScores.tsx
    data["skillsMatch"]  = _score(50, 98)   # fitScore / CV Rubric
    data["fitScore"]     = data["skillsMatch"]

    # General score factors (used by calculateNotaLiaGeral)
    data["generalScore"] = lia_score

    # WSI / Triagem score (candidate.liaScore ?? candidate.score)
    if stage not in ("sourcing",):
        data["triagemScore"] = _score(55, 98)
        data["wsi"] = _wsi_result() if randint(0, 1) else None
    else:
        data["triagemScore"] = None
        data["wsi"] = None

    # Technical test
    if stage in ("technical_test", "interview_technical", "interview_manager", "offer", "hired"):
        data["technicalTestScore"] = _score(60, 98)
        data["technicalTestName"]  = choice(["Teste SQL Avançado", "Desafio React", "Case de Produto", "Teste Python"])
    else:
        data["technicalTestScore"] = None

    # English test
    if stage in ("interview_manager", "offer", "hired") or (stage == "interview_technical" and randint(0, 1)):
        data["englishTestScore"] = _score(65, 98)
        data["englishLevel"]     = choice(["Intermediário", "Avançado", "Fluente"])
    else:
        data["englishTestScore"] = None

    # Big Five
    if stage in ("offer", "hired", "interview_manager") or (stage == "short_list" and randint(0, 1)):
        data["bigFive"]       = _big_five()
        data["bigFiveScores"] = data["bigFive"]
    else:
        data["bigFive"]       = None
        data["bigFiveScores"] = None

    # Interview data (for Entrevista columns)
    if stage in ("interview_hr", "interview_technical", "interview_manager"):
        has_schedule = randint(0, 1)
        if has_schedule:
            plat = choice(INTERVIEW_PLATFORMS)
            interview_dt = _future(4, 96)
            data["agendada"]      = interview_dt.isoformat()
            data["interviewDate"] = interview_dt.strftime("%d/%m/%Y %H:%M")
            data["teamsLink"]     = plat["url"]
            data["platform"]      = plat["platform"]
        else:
            data["agendada"] = None

    # LIA opinion
    data["lia_opinion"] = choice([
        "Candidato com forte alinhamento cultural e experiência relevante.",
        "Perfil técnico sólido. Recomendo avançar para próxima etapa.",
        "Bom fit com os requisitos. Salário dentro da faixa.",
        "Experiência acima da média. Risco de over-qualification.",
        "Candidato promissor. Recomendo triagem complementar.",
    ])

    # Sub-status
    data["sub_status"] = choice([
        "Em análise", "Aguardando retorno", "Documentação enviada",
        "Proposta aceita", "Em negociação", None,
    ])

    return data


# ─── Seed ─────────────────────────────────────────────────────────────────────

async def seed_kanban_data():
    print("=" * 60)
    print("🌱  Seed Kanban Test Data")
    print("=" * 60)

    async with engine.connect() as conn:
        # 1. Fetch candidate pool
        result = await conn.execute(text(
            "SELECT id, name, current_title FROM candidates "
            "ORDER BY RANDOM() LIMIT :n"
        ), {"n": TOTAL_PER_JOB * len(TARGET_JOBS) + 20})
        all_candidates = result.fetchall()

        if len(all_candidates) < TOTAL_PER_JOB:
            print(f"⚠️  Apenas {len(all_candidates)} candidatos no BD. Precisamos de {TOTAL_PER_JOB}.")
            return

        print(f"✓ Pool de candidatos disponível: {len(all_candidates)}")

        cand_pool = list(all_candidates)
        cand_idx = 0

        for job_title, job_id in TARGET_JOBS.items():
            print(f"\n→ Populando: {job_title} ({job_id})")

            for stage, count in STAGE_DISTRIBUTION.items():
                inserted = 0
                for _ in range(count):
                    if cand_idx >= len(cand_pool):
                        print("  ⚠️  Sem mais candidatos no pool!")
                        break

                    cand = cand_pool[cand_idx]
                    cand_idx += 1

                    lia_score   = _score(30, 98)
                    match_pct   = _score(40, 98)
                    add_data    = _build_additional_data(stage, lia_score)
                    entered_at  = _past(1, 21)

                    try:
                        await conn.execute(text("""
                            INSERT INTO vacancy_candidates
                                (id, vacancy_id, candidate_id, company_id,
                                 source, origin, lia_score, match_percentage,
                                 status, stage, previous_status,
                                 additional_data, stage_entered_at,
                                 created_at, updated_at)
                            VALUES
                                (:id, :vac_id, :cand_id, :company_id,
                                 :source, :origin, :lia_score, :match_pct,
                                 :status, :stage, :prev_status,
                                 CAST(:add_data AS jsonb), :entered_at,
                                 :now, :now)
                            ON CONFLICT (vacancy_id, candidate_id) DO NOTHING
                        """), {
                            "id":          str(uuid.uuid4()),
                            "vac_id":      job_id,
                            "cand_id":     str(cand[0]),
                            "company_id":  COMPANY_ID,
                            "source":      "seed",
                            "origin":      choice(["web", "manual", "import"]),
                            "lia_score":   lia_score,
                            "match_pct":   match_pct,
                            "status":      STAGE_TO_STATUS[stage],
                            "stage":       stage,
                            "prev_status": None,
                            "add_data":    json.dumps(add_data),
                            "entered_at":  entered_at,
                            "now":         NOW,
                        })
                        inserted += 1
                    except Exception as e:
                        print(f"    ⚠️  Erro ao inserir {cand[1]} em {stage}: {e}")

                print(f"  ✓ {stage}: {inserted}/{count} candidatos inseridos")

            await conn.commit()
            print(f"✓ {job_title}: commit OK")

    print("\n✅  Seed completo!")
    print(f"   Acesse: /vagas → Product Manager ou Tech Lead — Backend")


async def clean_seed_data():
    print("🧹  Limpando seed data...")
    async with engine.connect() as conn:
        for job_title, job_id in TARGET_JOBS.items():
            result = await conn.execute(text(
                "DELETE FROM vacancy_candidates WHERE vacancy_id = :jid AND source = 'seed' RETURNING id"
            ), {"jid": job_id})
            deleted = len(result.fetchall())
            print(f"  ✓ {job_title}: {deleted} registros removidos")
        await conn.commit()
    print("✅  Limpeza concluída!")


async def main():
    parser = argparse.ArgumentParser(description="Seed kanban test data")
    parser.add_argument("--seed",  action="store_true", help="Insert test data")
    parser.add_argument("--clean", action="store_true", help="Remove test data")
    parser.add_argument("--reset", action="store_true", help="Clean + Seed")
    args = parser.parse_args()

    if args.reset:
        await clean_seed_data()
        await seed_kanban_data()
    elif args.clean:
        await clean_seed_data()
    elif args.seed:
        await seed_kanban_data()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
