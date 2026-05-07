"""
Skills Ontology Tools — Exposes the SkillsOntologyEngine as callable tools
for LLM agents.

Tools:
- infer_related_skills: Given a set of skills, find related skills via graph traversal
- get_skill_adjacencies: Get adjacent skills for a single skill with weights
- analyze_skill_gaps: Compare candidate skills vs job requirements with adjacency awareness
- map_candidate_skills_to_ontology: Map raw skill strings to canonical ontology nodes
"""
import logging
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("talent_intelligence", require_company=False, module="talent_intelligence_pro")  # kept: pure ontology lookup, no tenant data
async def infer_related_skills(
    skills: list[str] | None = None,
    depth: int = 2,
    limit: int = 15,
    **kwargs,
) -> dict[str, Any]:
    """Infer related skills from a set of input skills using the ontology graph
    with optional embedding-based re-ranking when embeddings are available."""
    from app.domains.talent_intelligence.services.skills_ontology_engine import skills_ontology

    if not skills:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetro 'skills' é obrigatório (lista de skills).",
        }

    await skills_ontology._load_embeddings()

    related = skills_ontology.infer_related_skills(
        skills=skills, depth=min(depth, 3), limit=min(limit, 30)
    )

    scoring_mode = "graph_only"
    if skills_ontology._embeddings:
        scoring_mode = "hybrid"
        for item in related:
            best_sim = 0.0
            for input_skill in skills:
                sim = skills_ontology.get_embedding_similarity(input_skill, item["skill"])
                if sim is not None and sim > best_sim:
                    best_sim = sim
            item["embedding_similarity"] = round(best_sim, 3)
            graph_score = item["relevance_score"]
            item["hybrid_score"] = round(0.6 * graph_score + 0.4 * best_sim, 3)
        related.sort(key=lambda x: x.get("hybrid_score", x["relevance_score"]), reverse=True)

    return {
        "success": True,
        "data": {
            "input_skills": skills,
            "related_skills": related,
            "total_found": len(related),
            "depth": depth,
            "scoring_mode": scoring_mode,
        },
        "message": f"Encontradas {len(related)} skills relacionadas a partir de {len(skills)} skill(s) de entrada (modo: {scoring_mode}).",
    }


@tool_handler("talent_intelligence", require_company=False, module="talent_intelligence_pro")  # kept: pure ontology lookup, no tenant data
async def get_skill_adjacencies(
    skill: str = "",
    min_weight: float = 0.0,
    **kwargs,
) -> dict[str, Any]:
    """Get adjacent skills for a given skill with proximity weights,
    enriched with embedding cosine similarity when available."""
    from app.domains.talent_intelligence.services.skills_ontology_engine import skills_ontology

    if not skill:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetro 'skill' é obrigatório.",
        }

    await skills_ontology._load_embeddings()

    info = skills_ontology.get_skill_info(skill)
    adjacencies = skills_ontology.get_adjacencies(skill, min_weight=min_weight)

    scoring_mode = "graph_only"
    if skills_ontology._embeddings:
        scoring_mode = "hybrid"
        for adj in adjacencies:
            sim = skills_ontology.get_embedding_similarity(skill, adj["skill"])
            adj["embedding_similarity"] = round(sim, 3) if sim is not None else None
            graph_w = adj["weight"]
            adj["hybrid_proximity"] = round(0.6 * graph_w + 0.4 * (sim or 0), 3)

    return {
        "success": True,
        "data": {
            "skill": skill,
            "skill_info": info,
            "adjacencies": adjacencies,
            "total_adjacent": len(adjacencies),
            "scoring_mode": scoring_mode,
        },
        "message": (
            f"Skill '{skill}' tem {len(adjacencies)} adjacências no grafo (modo: {scoring_mode})."
            if info
            else f"Skill '{skill}' não encontrada na ontologia."
        ),
    }


@tool_handler("talent_intelligence", module="talent_intelligence_pro")
async def analyze_skill_gaps(
    candidate_skills: list[str] | None = None,
    required_skills: list[str] | None = None,
    candidate_id: str | None = None,
    job_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Analyze skill gaps between candidate and job requirements using ontology adjacencies."""
    from app.domains.talent_intelligence.services.skills_ontology_engine import skills_ontology

    company_id = kwargs.get("company_id", "")
    c_skills = candidate_skills or []
    r_skills = required_skills or []

    if candidate_id and not c_skills:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                row = await session.execute(
                    text("SELECT technical_skills FROM candidates WHERE id = :cid AND company_id = :company_id"),
                    {"cid": candidate_id, "company_id": company_id},
                )
                data = row.mappings().first()
                c_skills = list(data.get("technical_skills") or []) if data else []
        except Exception as e:
            logger.warning(f"Could not load candidate skills: {e}")

    if job_id and not r_skills:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                row = await session.execute(
                    text("SELECT technical_requirements FROM job_vacancies WHERE id = :jid AND company_id = :company_id"),
                    {"jid": job_id, "company_id": company_id},
                )
                data = row.mappings().first()
                reqs = data.get("technical_requirements") or [] if data else []
                if isinstance(reqs, list):
                    r_skills = [
                        r.get("technology", "") for r in reqs if isinstance(r, dict) and r.get("technology")
                    ]
        except Exception as e:
            logger.warning(f"Could not load job requirements: {e}")

    if not c_skills or not r_skills:
        return {
            "success": False,
            "data": {},
            "message": "Necessário fornecer candidate_skills e required_skills (ou candidate_id/job_id).",
        }

    await skills_ontology._load_embeddings()
    analysis = skills_ontology.analyze_skill_gaps(c_skills, r_skills)

    scoring_mode = "graph_only"
    if skills_ontology._embeddings and analysis.get("adjacency_matches"):
        scoring_mode = "hybrid"
        for am in analysis["adjacency_matches"]:
            sim = skills_ontology.get_embedding_similarity(
                am["missing_skill"], am["related_candidate_skill"]
            )
            am["embedding_similarity"] = round(sim, 3) if sim is not None else None
            am["hybrid_proximity"] = round(
                0.6 * am["proximity"] + 0.4 * (sim or 0), 3
            )

    analysis["scoring_mode"] = scoring_mode

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            "job_id": job_id,
            **analysis,
        },
        "message": (
            f"Gap analysis: {analysis['match_percentage']}% match direto, "
            f"{analysis['effective_match_percentage']}% match efetivo (com adjacências). "
            f"Severidade: {analysis['gap_severity']}. Modo: {scoring_mode}."
        ),
    }


@tool_handler("talent_intelligence", module="talent_intelligence_pro")
async def map_candidate_skills_to_ontology(
    skills: list[str] | None = None,
    candidate_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Map raw skill strings to canonical ontology nodes with domain classification."""
    from app.domains.talent_intelligence.services.skills_ontology_engine import skills_ontology

    company_id = kwargs.get("company_id", "")
    raw_skills = skills or []

    if candidate_id and not raw_skills:
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                row = await session.execute(
                    text("SELECT technical_skills, soft_skills FROM candidates WHERE id = :cid AND company_id = :company_id"),
                    {"cid": candidate_id, "company_id": company_id},
                )
                data = row.mappings().first()
                if data:
                    raw_skills = list(data.get("technical_skills") or []) + list(
                        data.get("soft_skills") or []
                    )
        except Exception as e:
            logger.warning(f"Could not load candidate skills: {e}")

    if not raw_skills:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetro 'skills' ou 'candidate_id' é obrigatório.",
        }

    mapping = skills_ontology.map_skills_to_ontology(raw_skills)

    return {
        "success": True,
        "data": {
            "candidate_id": candidate_id,
            **mapping,
        },
        "message": (
            f"Mapeamento: {mapping['mapped_count']}/{mapping['total_skills']} skills "
            f"reconhecidas na ontologia ({mapping['coverage_percentage']}% cobertura)."
        ),
    }
