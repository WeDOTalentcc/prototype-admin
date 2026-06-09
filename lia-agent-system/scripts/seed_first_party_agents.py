"""Seed script: insert WeDo first-party agents into custom_agents table.

Idempotent — uses INSERT ... ON CONFLICT (id) DO NOTHING.
Run via: python3 scripts/seed_first_party_agents.py

These agents are global (company_id=None, agent_type=first_party).
Their domains + allowed_tools manifests are filled in Fase B.
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert

from lia_config.database import AsyncSessionLocal
from lia_models.custom_agent import AgentType, CustomAgent, CustomAgentStatus

# Fixed UUIDs for first-party agents — deterministic, idempotent across envs
TALENT_INTEL_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
INTERVIEW_ANALYSIS_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

FIRST_PARTY_AGENTS = [
    {
        "id": TALENT_INTEL_AGENT_ID,
        "company_id": None,                         # global — no tenant
        "created_by": "wedo_system",
        "name": "TalentIntelAgent",
        "role": "Analista de Inteligência de Talentos",
        "description": (
            "Agente global WeDo para análise avançada de candidatos, ranking "
            "e recomendações de talentos. Disponível para todas as empresas."
        ),
        "system_prompt": (
            "Você é o TalentIntelAgent, um analista especializado em inteligência "
            "de talentos da plataforma WeDOTalent. Sua missão é ajudar recrutadores "
            "a identificar, avaliar e ranquear candidatos com precisão e fairness. "
            "Siga sempre as diretrizes LGPD e de equidade na avaliação de candidatos."
        ),
        "allowed_tools": [],        # filled in Fase B
        "domain": "talent",
        "icon": "🧠",
        "status": CustomAgentStatus.ACTIVE.value,
        "agent_type": AgentType.first_party.value,
        "domains": [],              # filled in Fase B
        "config": {},
        "max_steps": 10,
        "temperature": 0.3,
        "category": "screening",
    },
    {
        "id": INTERVIEW_ANALYSIS_AGENT_ID,
        "company_id": None,                         # global — no tenant
        "created_by": "wedo_system",
        "name": "InterviewAnalysisAgent",
        "role": "Analista de Entrevistas",
        "description": (
            "Agente global WeDo para análise de entrevistas, scorecard automático "
            "e síntese de feedbacks. Disponível para todas as empresas."
        ),
        "system_prompt": (
            "Você é o InterviewAnalysisAgent, especialista em análise de entrevistas "
            "da plataforma WeDOTalent. Sua missão é gerar scorecards objetivos, "
            "identificar pontos fortes e de desenvolvimento nos candidatos, e "
            "apoiar decisões de contratação com evidências concretas."
        ),
        "allowed_tools": [],        # filled in Fase B
        "domain": "talent",
        "icon": "🎯",
        "status": CustomAgentStatus.ACTIVE.value,
        "agent_type": AgentType.first_party.value,
        "domains": [],              # filled in Fase B
        "config": {},
        "max_steps": 8,
        "temperature": 0.2,
        "category": "screening",
    },
]


async def seed_first_party_agents() -> None:
    async with AsyncSessionLocal() as db:
        for agent_data in FIRST_PARTY_AGENTS:
            stmt = (
                pg_insert(CustomAgent)
                .values(**agent_data)
                .on_conflict_do_nothing(index_elements=["id"])
            )
            await db.execute(stmt)
        await db.commit()
        print(f"[seed_first_party_agents] Seeded {len(FIRST_PARTY_AGENTS)} first-party agents (idempotent).")


if __name__ == "__main__":
    asyncio.run(seed_first_party_agents())
