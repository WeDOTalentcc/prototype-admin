"""
Talent Pool Tool Registry — exposes talent pool operations to the ReAct loop.

Wraps TalentPoolDomain handlers into ToolDefinition format so the
LangGraphReActBase can autonomously decide which tools to call.

Guide computacional (harness-engineering):
  - Tools carry Pydantic-style descriptions so the LLM picks the right tool.
  - Multi-tenant: company_id always sourced from context (JWT), never from payload.
  - FairnessGuard: sourcing operations tagged as fairness_action_type="sourcing".
  - High-impact actions (move_pool_to_job, create_job_from_pool) require
    confirmation=True — HITL gate applied by the ReAct base class.

ADR-001: todos os selects movidos para repositórios canonical.
  - TalentPoolRepository: list_pools, get_by_id
  - TalentPoolCandidateRepository: list_by_pool, get_by_candidate_and_pool,
    move_candidates_to_vacancy
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition, ToolOutput

from app.shared.tool_handler import tool_handler
from app.domains.talent_pool.repositories.talent_pool_repository import TalentPoolRepository
from app.domains.talent_pool.repositories.talent_pool_candidate_repository import TalentPoolCandidateRepository

logger = logging.getLogger(__name__)


# ─── Tool 1: list_talent_pools ───────────────────────────────────────────────

@tool_handler("talent_pool")
async def _wrap_list_talent_pools(**kwargs: Any) -> dict[str, Any]:
    """List all active talent pools for the current company."""
    company_id = kwargs.get("company_id", "")
    status = kwargs.get("status", "active")

    try:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            repo = TalentPoolRepository(session)
            effective_status = status if status != "all" else None
            pools = [p.to_dict() for p in await repo.list_pools(company_id, effective_status)]

        if not pools:
            return {
                "success": True,
                "message": "Nenhum banco de talentos encontrado. Deseja criar um?",
                "data": {"pools": [], "total": 0},
            }

        summary = "\n".join(
            f"• **{p['name']}** — {p.get('candidates_count', 0)} candidatos ({p['status']})"
            for p in pools
        )
        return {
            "success": True,
            "message": f"Você tem **{len(pools)}** banco(s) de talentos:\n\n{summary}",
            "data": {"pools": pools, "total": len(pools)},
        }
    except Exception as exc:
        logger.error("[list_talent_pools] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool 2: get_pool_candidates ─────────────────────────────────────────────

@tool_handler("talent_pool")
async def _wrap_get_pool_candidates(**kwargs: Any) -> dict[str, Any]:
    """List candidates in a specific talent pool, optionally filtered by stage."""
    company_id = kwargs.get("company_id", "")
    pool_id = kwargs.get("pool_id")
    stage = kwargs.get("stage")
    limit = int(kwargs.get("limit", 50))

    if not pool_id:
        return {"success": False, "error": "pool_id is required"}

    try:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            tp_repo = TalentPoolRepository(session)
            tc_repo = TalentPoolCandidateRepository(session)

            # Verify pool belongs to company (multi-tenant guard)
            pool = await tp_repo.get_by_id(pool_id, company_id)
            if not pool:
                return {"success": False, "error": "Pool not found or access denied"}

            candidates = [
                c.to_dict()
                for c in await tc_repo.list_by_pool(pool_id, company_id, stage, limit)
            ]

        return {
            "success": True,
            "message": f"**{pool.name}**: {len(candidates)} candidato(s) encontrado(s).",
            "data": {
                "pool_id": str(pool_id),
                "pool_name": pool.name,
                "candidates": candidates,
                "total": len(candidates),
            },
        }
    except Exception as exc:
        logger.error("[get_pool_candidates] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool 3: create_talent_pool ──────────────────────────────────────────────

@tool_handler("talent_pool")
async def _wrap_create_talent_pool(**kwargs: Any) -> dict[str, Any]:
    """Create a new talent pool with the given name and optional archetype."""
    company_id = kwargs.get("company_id", "")
    name = kwargs.get("name")
    description = kwargs.get("description", "")
    archetype_id = kwargs.get("archetype_id")

    if not name:
        return {"success": False, "error": "name is required to create a talent pool"}

    try:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool

        async with AsyncSessionLocal() as session:
            pool = TalentPool(
                id=uuid.uuid4(),
                company_id=company_id,
                name=name,
                description=description,
                archetype_id=archetype_id,
                status="active",
            )
            session.add(pool)
            await session.commit()
            await session.refresh(pool)
            pool_data = pool.to_dict()

        return {
            "success": True,
            "message": f"Banco de talentos **{name}** criado com sucesso! ID: `{pool_data['id']}`",
            "data": {"pool": pool_data},
        }
    except Exception as exc:
        logger.error("[create_talent_pool] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool 4: add_candidate_to_pool ───────────────────────────────────────────

@tool_handler("talent_pool")
async def _wrap_add_candidate_to_pool(**kwargs: Any) -> dict[str, Any]:
    """Add one or more candidates to a talent pool."""
    company_id = kwargs.get("company_id", "")
    pool_id = kwargs.get("pool_id")
    candidate_ids = kwargs.get("candidate_ids", [])
    origin = kwargs.get("origin", "manual")

    if not pool_id:
        return {"success": False, "error": "pool_id is required"}
    if not candidate_ids:
        return {"success": False, "error": "candidate_ids list cannot be empty"}

    try:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPoolCandidate

        async with AsyncSessionLocal() as session:
            repo = TalentPoolRepository(session)

            # Multi-tenant guard
            pool = await repo.get_by_id(pool_id, company_id)
            if not pool:
                return {"success": False, "error": "Pool not found or access denied"}

            added = 0
            for cid in candidate_ids:
                entry = TalentPoolCandidate(
                    id=uuid.uuid4(),
                    talent_pool_id=pool_id,
                    candidate_id=cid,
                    stage="discovered",
                    origin=origin,
                )
                session.add(entry)
                added += 1
            await session.commit()

        return {
            "success": True,
            "message": f"**{added}** candidato(s) adicionado(s) ao pool '{pool.name}'.",
            "data": {"pool_id": str(pool_id), "added": added, "origin": origin},
        }
    except Exception as exc:
        logger.error("[add_candidate_to_pool] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool 5: move_pool_to_job (HIGH IMPACT — confirmation required) ───────────

@tool_handler("talent_pool")
async def _wrap_move_pool_to_job(**kwargs: Any) -> dict[str, Any]:
    """
    Migrate candidates from a pool to a job vacancy (high-impact action).
    Preserves existing screening_data to avoid re-triagem.
    Requires explicit recruiter confirmation before execution.
    """
    company_id = kwargs.get("company_id", "")
    pool_id = kwargs.get("pool_id")
    job_id = kwargs.get("job_id")
    candidate_ids = kwargs.get("candidate_ids", [])
    target_stage = kwargs.get("target_stage", "triagem")

    if not pool_id or not job_id:
        return {"success": False, "error": "pool_id and job_id are both required"}
    if not candidate_ids:
        return {"success": False, "error": "candidate_ids cannot be empty"}

    try:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            tp_repo = TalentPoolRepository(session)
            tc_repo = TalentPoolCandidateRepository(session)

            # Multi-tenant guard on pool
            pool = await tp_repo.get_by_id(pool_id, company_id)
            if not pool:
                return {"success": False, "error": "Pool not found or access denied"}

            moved = await tc_repo.move_candidates_to_vacancy(
                candidate_ids=candidate_ids,
                job_id=job_id,
                company_id=company_id,
                source_pool_id=pool_id,
                target_stage=target_stage,
            )

        return {
            "success": True,
            "message": (
                f"**{moved}** candidato(s) migrado(s) do pool '{pool.name}' "
                f"para a vaga `{job_id}` (etapa: {target_stage})."
            ),
            "data": {
                "pool_id": str(pool_id),
                "job_id": str(job_id),
                "moved": moved,
                "target_stage": target_stage,
                "screening_data_preserved": True,
            },
        }
    except Exception as exc:
        logger.error("[move_pool_to_job] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool 6: create_job_from_pool (HIGH IMPACT) ───────────────────────────────

@tool_handler("talent_pool")
async def _wrap_create_job_from_pool(**kwargs: Any) -> dict[str, Any]:
    """
    Create a job vacancy based on a talent pool (inherits archetype and
    screening configuration). High-impact: requires confirmation.
    """
    company_id = kwargs.get("company_id", "")
    pool_id = kwargs.get("pool_id")

    if not pool_id:
        return {"success": False, "error": "pool_id is required"}

    try:
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            repo = TalentPoolRepository(session)
            pool = await repo.get_by_id(pool_id, company_id)
            if not pool:
                return {"success": False, "error": "Pool not found or access denied"}

        # Delegate to job_management wizard via ui_action
        return {
            "success": True,
            "message": (
                f"Preparando criacao de vaga a partir do pool **{pool.name}**. "
                f"O assistente de criacao de vagas sera aberto com o perfil pre-configurado."
            ),
            "ui_action": "wizard_step",
            "ui_action_params": {
                "wizard": "create_job",
                "step": "step_1",
                "prefill": {
                    "source": "talent_pool",
                    "pool_id": str(pool_id),
                    "archetype_id": str(pool.archetype_id) if pool.archetype_id else None,
                    "pool_name": pool.name,
                },
            },
            "data": {
                "pool_id": str(pool_id),
                "pool_name": pool.name,
                "archetype_id": str(pool.archetype_id) if pool.archetype_id else None,
            },
        }
    except Exception as exc:
        logger.error("[create_job_from_pool] Error: %s", exc)
        return {"success": False, "error": str(exc)}


# ─── Tool registry export ─────────────────────────────────────────────────────

def get_talent_pool_tools() -> list[ToolDefinition]:
    """Return all ToolDefinitions for the talent pool ReAct agent."""
    return [
        ToolDefinition(
            name="list_talent_pools",
            description=(
                "Lista todos os bancos de talentos ativos da empresa. "
                "Use quando o recrutador pedir para ver, listar ou consultar seus pools. "
                "Parametro opcional: status ('active'|'archived')."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtro de status do pool (default: 'active').",
                        "enum": ["active", "archived", "all"],
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_list_talent_pools,
        ),
        ToolDefinition(
            name="get_pool_candidates",
            description=(
                "Lista candidatos dentro de um banco de talentos especifico. "
                "Use quando o recrutador quiser ver quem esta em um pool. "
                "Parametro obrigatorio: pool_id. Opcional: stage, limit."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_id": {
                        "type": "string",
                        "description": "UUID do banco de talentos.",
                    },
                    "stage": {
                        "type": "string",
                        "description": (
                            "Filtrar por estagio: 'discovered'|'contacted'|"
                            "'screening'|'screened'|'ready'."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximo de candidatos a retornar (default: 50).",
                    },
                },
                "required": ["pool_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_get_pool_candidates,
        ),
        ToolDefinition(
            name="create_talent_pool",
            description=(
                "Cria um novo banco de talentos vivo. "
                "Use quando o recrutador quiser criar, abrir ou configurar um novo pool. "
                "Parametro obrigatorio: name."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome do banco de talentos (ex: 'Engenheiros Plenos', 'UX Designers').",
                    },
                    "description": {
                        "type": "string",
                        "description": "Descricao opcional do pool.",
                    },
                    "archetype_id": {
                        "type": "string",
                        "description": "UUID do arquetipo (perfil ideal) para o pool (opcional).",
                    },
                },
                "required": ["name"],
            },
            output_schema=ToolOutput,
            function=_wrap_create_talent_pool,
        ),
        ToolDefinition(
            name="add_candidate_to_pool",
            description=(
                "Adiciona um ou mais candidatos a um banco de talentos existente. "
                "Use quando o recrutador quiser incluir candidatos em um pool. "
                "Parametros obrigatorios: pool_id, candidate_ids (lista de UUIDs)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_id": {
                        "type": "string",
                        "description": "UUID do banco de talentos destino.",
                    },
                    "candidate_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de UUIDs dos candidatos a adicionar.",
                    },
                    "origin": {
                        "type": "string",
                        "description": "Origem dos candidatos (default: 'manual').",
                    },
                },
                "required": ["pool_id", "candidate_ids"],
            },
            output_schema=ToolOutput,
            function=_wrap_add_candidate_to_pool,
        ),
        ToolDefinition(
            name="move_pool_to_job",
            description=(
                "ACAO DE ALTO IMPACTO — migra candidatos de um pool para uma vaga. "
                "Preserva screening_data existente para evitar re-triagem. "
                "REQUER CONFIRMACAO EXPLICITA do recrutador antes de executar. "
                "Parametros obrigatorios: pool_id, job_id, candidate_ids, target_stage."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_id": {
                        "type": "string",
                        "description": "UUID do banco de talentos origem.",
                    },
                    "job_id": {
                        "type": "string",
                        "description": "UUID da vaga destino.",
                    },
                    "candidate_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de UUIDs dos candidatos a migrar.",
                    },
                    "target_stage": {
                        "type": "string",
                        "description": "Etapa destino no funil da vaga (default: 'triagem').",
                    },
                },
                "required": ["pool_id", "job_id", "candidate_ids"],
            },
            output_schema=ToolOutput,
            function=_wrap_move_pool_to_job,
        ),
        ToolDefinition(
            name="create_job_from_pool",
            description=(
                "ACAO DE ALTO IMPACTO — cria uma vaga a partir de um banco de talentos, "
                "herdando o arquetipo e configuracoes de triagem do pool. "
                "Abre o wizard de criacao de vagas pre-configurado. "
                "REQUER CONFIRMACAO EXPLICITA. Parametro obrigatorio: pool_id."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_id": {
                        "type": "string",
                        "description": "UUID do banco de talentos base para a nova vaga.",
                    },
                },
                "required": ["pool_id"],
            },
            output_schema=ToolOutput,
            function=_wrap_create_job_from_pool,
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# P1-2 (2026-06-18) — registro global
# ─────────────────────────────────────────────────────────────────────────────

def register_talent_pool_global() -> int:
    """Registra as 6 tools de talent pool no tool_registry global.

    Wraps lia_agents_core.ToolContract -> app.tools.registry.ToolDefinition,
    padrão idêntico a register_jobs_mgmt_global() (P0-1 2026-06-18).
    """
    from app.tools.registry import ToolDefinition as _G
    from app.tools.registry import tool_registry as _reg

    n = 0
    for td in get_talent_pool_tools():
        _reg.register(
            _G(
                name=td.name,
                description=td.description,
                parameters_schema=td.parameters,
                handler=td.function,
                allowed_agents=["recruiter_assistant", "orchestrator"],
            )
        )
        n += 1
    return n
