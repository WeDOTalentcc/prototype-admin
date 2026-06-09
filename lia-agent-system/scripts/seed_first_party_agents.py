"""Seed script: insert WeDo first-party agents into custom_agents table.

Idempotent — uses INSERT ... ON CONFLICT (id) DO UPDATE SET to refresh
domains and allowed_tools when re-run. This ensures Fase B manifest data
is always applied even if the row already exists from a previous seed.

Run via: python3 scripts/seed_first_party_agents.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert

from lia_config.database import AsyncSessionLocal
from lia_models.custom_agent import AgentType, CustomAgent, CustomAgentStatus

# Fixed UUIDs for first-party agents — deterministic, idempotent across envs
TALENT_INTEL_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
INTERVIEW_ANALYSIS_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
VOICE_SCREENING_CHANNEL_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")

# ── Fase B: Canonical tool lists ────────────────────────────────────────────
# TalentIntelAgent exposes all 15 tools from app/domains/talent_intelligence/
# tools/registry.py (verified 2026-06-09 against actual registrations).
_TALENT_INTEL_TOOLS: list[str] = [
    # Skill analysis
    "infer_related_skills",
    "get_skill_adjacencies",
    "analyze_skill_gaps",
    "map_candidate_skills_to_ontology",
    # Workforce & market intelligence
    "get_market_intelligence",
    "forecast_hiring_needs",
    "match_internal_candidates",
    # Candidate nurture & engagement
    "create_nurture_sequence",
    "get_engagement_metrics",
    "suggest_reengagement",
    # Interview intelligence (shared with InterviewAnalysisAgent)
    "analyze_interview_recording",
    "detect_interview_bias",
    "compare_interview_performance",
    "generate_candidate_feedback",
    "generate_interview_opinion",
]

# InterviewAnalysisAgent exposes only the 5 interview_intelligence tools,
# sourced from app/domains/interview_intelligence/services/:
#   bias_detector_service, comparative_analysis_service,
#   feedback_generator_service, interview_wsi_service, strategic_opinion_service
_INTERVIEW_ANALYSIS_TOOLS: list[str] = [
    "analyze_interview_recording",    # interview_wsi_service
    "detect_interview_bias",          # bias_detector_service
    "compare_interview_performance",  # comparative_analysis_service
    "generate_candidate_feedback",    # feedback_generator_service
    "generate_interview_opinion",     # strategic_opinion_service
]

FIRST_PARTY_AGENTS = [
    {
        "id": TALENT_INTEL_AGENT_ID,
        "company_id": None,                         # global — no tenant
        "created_by": "wedo_system",
        "name": "TalentIntelAgent",
        "role": "Analista de Inteligencia de Talentos",
        "description": (
            "Agente global WeDo para analise avancada de candidatos, ranking "
            "e recomendacoes de talentos. Disponivel para todas as empresas."
        ),
        "system_prompt": (
            "Voce e o TalentIntelAgent, um analista especializado em inteligencia "
            "de talentos da plataforma WeDOTalent. Sua missao e ajudar recrutadores "
            "a identificar, avaliar e ranquear candidatos com precisao e fairness. "
            "Siga sempre as diretrizes LGPD e de equidade na avaliacao de candidatos."
        ),
        "allowed_tools": _TALENT_INTEL_TOOLS,
        "domain": "talent",
        "icon": "\U0001f9e0",
        "status": CustomAgentStatus.ACTIVE.value,
        "agent_type": AgentType.first_party.value,
        "domains": [
            "talent_analysis",
            "skill_gap",
            "market_intelligence",
            "workforce_planning",
            "candidate_nurture",
        ],
        "config": {},
        "max_steps": 10,
        "temperature": 0.3,
        "category": "screening",
        "is_marketplace_published": True,
    },
    {
        "id": INTERVIEW_ANALYSIS_AGENT_ID,
        "company_id": None,                         # global — no tenant
        "created_by": "wedo_system",
        "name": "InterviewAnalysisAgent",
        "role": "Analista de Entrevistas",
        "description": (
            "Agente global WeDo para analise de entrevistas, scorecard automatico "
            "e sintese de feedbacks. Disponivel para todas as empresas."
        ),
        "system_prompt": (
            "Voce e o InterviewAnalysisAgent, especialista em analise de entrevistas "
            "da plataforma WeDOTalent. Sua missao e gerar scorecards objetivos, "
            "identificar pontos fortes e de desenvolvimento nos candidatos, e "
            "apoiar decisoes de contratacao com evidencias concretas."
        ),
        "allowed_tools": _INTERVIEW_ANALYSIS_TOOLS,
        "domain": "talent",
        "icon": "\U0001f3af",
        "status": CustomAgentStatus.ACTIVE.value,
        "agent_type": AgentType.first_party.value,
        "domains": [
            "interview_analysis",
            "bias_detection",
            "interview_feedback",
        ],
        "config": {},
        "max_steps": 8,
        "temperature": 0.2,
        "category": "screening",
        "is_marketplace_published": True,
    },
    {
        "id": VOICE_SCREENING_CHANNEL_ID,
        "name": "VoiceScreeningChannel",
        "company_id": None,
        "agent_type": AgentType.first_party.value,
        "category": "voice_channel",
        "voice_enabled": True,
        "status": "active",
        "domains": [],
        "allowed_tools": [],
        "description": "Canal de triagem por voz (Twilio -> Gemini STT -> LLM -> TTS). Manifesto de configuracao por tenant - sem routing de chat.",
        "system_prompt": "",
        "max_steps": 1,  # minimum to avoid recursion crash if ever instantiated
        "temperature": 0.0,
    },
]


async def seed_first_party_agents() -> None:
    async with AsyncSessionLocal() as db:
        for agent_data in FIRST_PARTY_AGENTS:
            stmt = (
                pg_insert(CustomAgent)
                .values(**agent_data)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "domains": agent_data["domains"],
                        "allowed_tools": agent_data["allowed_tools"],
                        "description": agent_data["description"],
                        "is_marketplace_published": agent_data.get("is_marketplace_published", False),
                    },
                )
            )
            await db.execute(stmt)
        await db.commit()
        print(
            f"[seed_first_party_agents] Seeded {len(FIRST_PARTY_AGENTS)} first-party agents "
            f"(upsert — domains+allowed_tools always refreshed)."
        )


if __name__ == "__main__":
    asyncio.run(seed_first_party_agents())
