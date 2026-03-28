"""
Seed demo interviews for the Tasks MVP page.
Creates realistic interview entries linked to existing DEMO candidates and vacancies.
Uses BRT timezone (UTC-3) for date calculations to match the user's browser.
Can be re-run: deletes existing demo interviews first.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from app.core.database import async_session_factory
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.models.job_vacancy import JobVacancy

BRT = timezone(timedelta(hours=-3))

INTERVIEW_TYPE_LABELS = {
    "technical": "Entrevista Técnica",
    "behavioral": "Entrevista Comportamental",
    "cultural": "Fit Cultural",
    "final": "Entrevista Final",
}

PLATFORMS = [
    {"platform": "google_meet", "url_tpl": "https://meet.google.com/lia-demo-{idx:03d}"},
    {"platform": "microsoft_teams", "url_tpl": "https://teams.microsoft.com/l/meetup/lia-demo-{idx:03d}"},
    {"platform": "zoom", "url_tpl": "https://zoom.us/j/{idx}"},
]

INTERVIEWS_CONFIG = [
    {"day_offset": 0, "hour": 9, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "scheduled", "cand_idx": 0, "vac_idx": 0, "plat_idx": 0},
    {"day_offset": 0, "hour": 10, "dur": 45, "type": "behavioral", "stage": "Entrevista Comportamental", "status": "scheduled", "cand_idx": 1, "vac_idx": 1, "plat_idx": 1},
    {"day_offset": 0, "hour": 11, "dur": 45, "type": "final", "stage": "Entrevista Final", "status": "scheduled", "cand_idx": 2, "vac_idx": 2, "plat_idx": 2},
    {"day_offset": 0, "hour": 14, "dur": 30, "type": "cultural", "stage": "Fit Cultural", "status": "scheduled", "cand_idx": 3, "vac_idx": 3, "plat_idx": 0},
    {"day_offset": 0, "hour": 15, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "scheduled", "cand_idx": 4, "vac_idx": 4, "plat_idx": 1},
    {"day_offset": 0, "hour": 16, "dur": 45, "type": "final", "stage": "Entrevista Final", "status": "scheduled", "cand_idx": 5, "vac_idx": 5, "plat_idx": 2},
    {"day_offset": 0, "hour": 17, "dur": 30, "type": "cultural", "stage": "Fit Cultural", "status": "confirmed", "cand_idx": 6, "vac_idx": 6, "plat_idx": 0},

    {"day_offset": 1, "hour": 9, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "scheduled", "cand_idx": 7, "vac_idx": 7, "plat_idx": 1},
    {"day_offset": 1, "hour": 10, "dur": 45, "type": "behavioral", "stage": "Entrevista Comportamental", "status": "scheduled", "cand_idx": 8, "vac_idx": 0, "plat_idx": 2},
    {"day_offset": 1, "hour": 14, "dur": 60, "type": "final", "stage": "Entrevista Final", "status": "scheduled", "cand_idx": 9, "vac_idx": 1, "plat_idx": 0},
    {"day_offset": 1, "hour": 16, "dur": 45, "type": "cultural", "stage": "Fit Cultural", "status": "scheduled", "cand_idx": 10, "vac_idx": 2, "plat_idx": 1},

    {"day_offset": 2, "hour": 10, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "scheduled", "cand_idx": 11, "vac_idx": 3, "plat_idx": 2},
    {"day_offset": 2, "hour": 14, "dur": 45, "type": "final", "stage": "Entrevista Final", "status": "scheduled", "cand_idx": 12, "vac_idx": 4, "plat_idx": 0},

    {"day_offset": 3, "hour": 9, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "scheduled", "cand_idx": 13, "vac_idx": 5, "plat_idx": 1},
    {"day_offset": 3, "hour": 11, "dur": 30, "type": "cultural", "stage": "Fit Cultural", "status": "scheduled", "cand_idx": 14, "vac_idx": 6, "plat_idx": 2},

    {"day_offset": -1, "hour": 9, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "completed", "cand_idx": 15, "vac_idx": 7, "plat_idx": 0},
    {"day_offset": -1, "hour": 14, "dur": 45, "type": "final", "stage": "Entrevista Final", "status": "completed", "cand_idx": 16, "vac_idx": 0, "plat_idx": 1},
    {"day_offset": -1, "hour": 16, "dur": 30, "type": "cultural", "stage": "Fit Cultural", "status": "completed", "cand_idx": 17, "vac_idx": 1, "plat_idx": 2},

    {"day_offset": -2, "hour": 10, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "completed", "cand_idx": 0, "vac_idx": 2, "plat_idx": 0},
    {"day_offset": -2, "hour": 15, "dur": 45, "type": "behavioral", "stage": "Entrevista Comportamental", "status": "cancelled", "cand_idx": 1, "vac_idx": 3, "plat_idx": 1,
     "cancel_reason": "Candidato não compareceu"},

    {"day_offset": -3, "hour": 9, "dur": 60, "type": "final", "stage": "Entrevista Final", "status": "completed", "cand_idx": 2, "vac_idx": 4, "plat_idx": 2},
    {"day_offset": -3, "hour": 11, "dur": 45, "type": "technical", "stage": "Entrevista Técnica", "status": "rescheduled", "cand_idx": 3, "vac_idx": 5, "plat_idx": 0,
     "cancel_reason": "Reagendada a pedido do candidato"},
    {"day_offset": -3, "hour": 14, "dur": 30, "type": "cultural", "stage": "Fit Cultural", "status": "completed", "cand_idx": 4, "vac_idx": 6, "plat_idx": 1},

    {"day_offset": -5, "hour": 10, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "completed", "cand_idx": 5, "vac_idx": 7, "plat_idx": 2},
    {"day_offset": -5, "hour": 14, "dur": 45, "type": "final", "stage": "Entrevista Final", "status": "cancelled", "cand_idx": 6, "vac_idx": 0, "plat_idx": 0,
     "cancel_reason": "Candidato desistiu do processo"},

    {"day_offset": -7, "hour": 9, "dur": 60, "type": "technical", "stage": "Entrevista Técnica", "status": "completed", "cand_idx": 7, "vac_idx": 1, "plat_idx": 1},
    {"day_offset": -7, "hour": 15, "dur": 45, "type": "behavioral", "stage": "Entrevista Comportamental", "status": "completed", "cand_idx": 8, "vac_idx": 2, "plat_idx": 2},
]


async def seed_interviews():
    async with async_session_factory() as db:
        del_result = await db.execute(
            delete(Interview).where(Interview.created_by == "seed_script")
        )
        deleted = del_result.rowcount
        if deleted:
            print(f"🗑️  Deleted {deleted} existing seed interviews")

        candidates_result = await db.execute(
            select(Candidate).where(Candidate.name.like("[DEMO]%")).order_by(Candidate.name)
        )
        candidates = list(candidates_result.scalars().all())

        vacancies_result = await db.execute(
            select(JobVacancy).where(
                JobVacancy.title.like("[DEMO]%"),
                JobVacancy.status.in_(["active", "Ativa"])
            ).order_by(JobVacancy.title)
        )
        vacancies = list(vacancies_result.scalars().all())

        if len(candidates) < 8:
            print(f"❌ Need at least 8 DEMO candidates, found {len(candidates)}. Aborting.")
            return
        if len(vacancies) < 2:
            print(f"❌ Need at least 2 active DEMO vacancies, found {len(vacancies)}. Aborting.")
            return

        print(f"📋 Found {len(candidates)} DEMO candidates and {len(vacancies)} active DEMO vacancies")

        now_brt = datetime.now(BRT)
        today_brt = now_brt.replace(hour=0, minute=0, second=0, microsecond=0)

        interviewer_name = "Ana Recrutadora"
        interviewer_email = "ana@wedo.com"
        created_count = 0

        for idx, cfg in enumerate(INTERVIEWS_CONFIG):
            cand = candidates[cfg["cand_idx"] % len(candidates)]
            vacancy = vacancies[cfg["vac_idx"] % len(vacancies)]
            plat = PLATFORMS[cfg["plat_idx"] % len(PLATFORMS)]

            target_day = today_brt + timedelta(days=cfg["day_offset"])
            start_brt = target_day.replace(hour=cfg["hour"], minute=0, second=0, microsecond=0)
            start_naive = start_brt.replace(tzinfo=None)
            end_naive = start_naive + timedelta(minutes=cfg["dur"])

            type_label = INTERVIEW_TYPE_LABELS.get(cfg["type"], cfg["type"])
            clean_name = cand.name.replace("[DEMO] ", "")

            interview = Interview(
                id=uuid.uuid4(),
                title=f"{type_label} - {clean_name}",
                description=f"Entrevista para a vaga {vacancy.title.replace('[DEMO] ', '')}",
                interview_type=cfg["type"],
                interview_mode="video",
                candidate_id=cand.id,
                candidate_name=cand.name,
                candidate_email=cand.email or f"demo.{idx}@example.com",
                interviewer_name=interviewer_name,
                interviewer_email=interviewer_email,
                start_time=start_naive,
                end_time=end_naive,
                timezone="America/Sao_Paulo",
                duration_minutes=cfg["dur"],
                meeting_url=plat["url_tpl"].format(idx=idx + 1),
                meeting_platform=plat["platform"],
                status=cfg["status"],
                job_vacancy_id=vacancy.id,
                job_title=vacancy.title,
                application_stage=cfg["stage"],
                created_by="seed_script",
                cancelled_at=start_naive if cfg["status"] in ("cancelled", "rescheduled") else None,
                cancellation_reason=cfg.get("cancel_reason"),
            )
            db.add(interview)
            created_count += 1

            day_label = {0: "HOJE", 1: "AMANHÃ", 2: "D+2", 3: "D+3"}.get(
                cfg["day_offset"],
                f"D{cfg['day_offset']}" if cfg["day_offset"] < 0 else f"D+{cfg['day_offset']}"
            )
            print(f"  ✅ {day_label} {cfg['hour']:02d}:00 | {type_label:30s} | {clean_name:30s} | {cfg['status']:12s} | {vacancy.title.replace('[DEMO] ', '')}")

        await db.commit()
        print(f"\n🎉 Created {created_count} demo interviews!")
        print(f"   📅 Hoje: {sum(1 for c in INTERVIEWS_CONFIG if c['day_offset'] == 0)} entrevistas")
        print(f"   📅 Amanhã: {sum(1 for c in INTERVIEWS_CONFIG if c['day_offset'] == 1)} entrevistas")
        print(f"   📅 Próximos dias: {sum(1 for c in INTERVIEWS_CONFIG if c['day_offset'] > 1)} entrevistas")
        print(f"   📜 Histórico: {sum(1 for c in INTERVIEWS_CONFIG if c['day_offset'] < 0)} entrevistas")


if __name__ == "__main__":
    asyncio.run(seed_interviews())
