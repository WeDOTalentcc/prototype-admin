"""
Policy Tool Registry - Exposes policy configuration tools to the ReAct loop.

Wraps hiring policy operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for policy management.
Tools connect to PostgreSQL for real data operations and integrate with
FairnessGuard for compliance validation.
"""
import json
import logging
import re
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_SAFE_COL_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_VALID_POLICY_BLOCKS = frozenset([
    "pipeline_rules", "scheduling_rules", "communication_rules",
    "screening_rules", "automation_rules",
])

_fairness_guard = FairnessGuard()


@tool_handler("hiring_policy")
async def _wrap_get_current_policy(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    # ADR-001 W1-004-C MIGRATE 1: uses HiringPolicyRepository.get_by_company
    # instead of inline text() SQL. Fail-closed via repo multi-tenancy.
    async with AsyncSessionLocal() as db:
        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if not policy:
            return {
                "success": True,
                "data": {
                    "exists": False,
                    "pipeline_rules": {},
                    "scheduling_rules": {},
                    "communication_rules": {},
                    "screening_rules": {},
                    "automation_rules": {},
                    "pipeline_templates": [],
                    "setup_progress": 0,
                },
                "message": "Nenhuma politica configurada ainda. Vamos comecar do zero.",
            }

        def _parse(val, is_list=False):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return val
            if val is not None:
                return val
            return [] if is_list else {}

        data = {
            "pipeline_rules": _parse(policy.pipeline_rules),
            "scheduling_rules": _parse(policy.scheduling_rules),
            "communication_rules": _parse(policy.communication_rules),
            "screening_rules": _parse(policy.screening_rules),
            "automation_rules": _parse(policy.automation_rules),
            "pipeline_templates": _parse(policy.pipeline_templates, is_list=True),
            "learned_patterns": _parse(getattr(policy, "learned_patterns", None)),
            "exists": True,
            "setup_progress": policy.setup_progress or 0,
            "autonomy_level": getattr(policy, "autonomy_level", None) or "low",
        }

        return {
            "success": True,
            "data": data,
            "message": "Politicas atuais carregadas com sucesso.",
        }


@tool_handler("hiring_policy")
async def _wrap_save_policy_field(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    block = kwargs.get("block", "")
    field = kwargs.get("field", "")
    value = kwargs.get("value")

    if block not in _VALID_POLICY_BLOCKS:
        return {
            "success": False,
            "data": {},
            "message": f"Bloco '{block}' nao e valido. Blocos validos: {sorted(_VALID_POLICY_BLOCKS)}",
        }

    if not _SAFE_COL_RE.match(block):
        return {"success": False, "data": {}, "message": f"Bloco '{block}' contém caracteres inválidos."}

    # ADR-001-EXEMPT: _VALID_POLICY_BLOCKS frozenset + _SAFE_COL_RE regex enforce
    # double sanitization on block name — dynamic field update with equivalent
    # security to typed repo method. Block name is validated against allowlist
    # AND regex before interpolation. Not abstractable without losing clarity.
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text(f"SELECT id, {block} FROM company_hiring_policies WHERE company_id = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        row = existing.mappings().first()

        if row:
            current_block = row[block]
            if isinstance(current_block, str):
                try:
                    current_block = json.loads(current_block)
                except (json.JSONDecodeError, TypeError):
                    current_block = {}
            elif current_block is None:
                current_block = {}

            current_block[field] = value
            block_json = json.dumps(current_block, ensure_ascii=False)

            await session.execute(
                text(f"""
                    UPDATE company_hiring_policies
                    SET {block} = :block_data::jsonb, updated_at = NOW()
                    WHERE company_id = :company_id
                """),
                {"block_data": block_json, "company_id": company_id},
            )
        else:
            block_data = {field: value}
            block_json = json.dumps(block_data, ensure_ascii=False)
            await session.execute(
                text(f"""
                    INSERT INTO company_hiring_policies (company_id, {block}, created_at, updated_at)
                    VALUES (:company_id, :block_data::jsonb, NOW(), NOW())
                """),
                {"company_id": company_id, "block_data": block_json},
            )

        await session.commit()

        return {
            "success": True,
            "data": {
                "block": block,
                "field": field,
                "value": value,
                "saved": True,
            },
            "message": f"Politica salva: {block}.{field} = {value}",
        }


@tool_handler("hiring_policy")
async def _wrap_get_policy_summary(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    # ADR-001 W1-004-C MIGRATE 2: reuses HiringPolicyRepository.get_by_company
    # instead of inline text() SQL — same repo as _wrap_get_current_policy.
    async with AsyncSessionLocal() as db:
        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if not policy:
            return {
                "success": True,
                "data": {"configured": False, "summary": "Nenhuma politica configurada."},
                "message": "Nenhuma politica foi definida para esta empresa.",
            }

        def _parse_block(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return val or {}

        summary_parts = []
        blocks = {
            "pipeline_rules": "Pipeline e Processo",
            "scheduling_rules": "Agendamento",
            "communication_rules": "Comunicacao",
            "screening_rules": "Triagem",
            "automation_rules": "Autonomia da LIA",
        }

        configured_count = 0
        for block_key, block_name in blocks.items():
            block_data = _parse_block(getattr(policy, block_key, None))

            if block_data:
                configured_count += 1
                fields = []
                for k, v in block_data.items():
                    if v not in (None, "", [], {}):
                        fields.append(f"  - {k}: {v}")
                if fields:
                    summary_parts.append(f"**{block_name}**:")
                    summary_parts.extend(fields)
                else:
                    summary_parts.append(f"**{block_name}**: (vazio)")
            else:
                summary_parts.append(f"**{block_name}**: Nao configurado")

        return {
            "success": True,
            "data": {
                "configured": True,
                "blocks_configured": configured_count,
                "total_blocks": len(blocks),
                "setup_progress": policy.setup_progress or 0,
                "autonomy_level": getattr(policy, "autonomy_level", None) or "low",
                "summary": "\n".join(summary_parts),
            },
            "message": f"Resumo das politicas: {configured_count}/{len(blocks)} blocos configurados.",
        }


@tool_handler("hiring_policy", require_company=False)  # kept: pure text/policy validation, no tenant data
async def _wrap_validate_policy_compliance(**kwargs: Any) -> dict[str, Any]:
    policy_text = kwargs.get("policy_text", "")
    field_name = kwargs.get("field_name", "")
    deep_check = kwargs.get("deep_check", False)

    if not policy_text:
        return {
            "success": True,
            "data": {"is_compliant": True, "issues": [], "soft_warnings": []},
            "message": "Nenhum texto para validar.",
        }

    check_result = _fairness_guard.check(policy_text)

    if check_result.is_blocked:
        return {
            "success": True,
            "data": {
                "is_compliant": False,
                "category": check_result.category,
                "blocked_terms": check_result.blocked_terms,
                "educational_message": check_result.educational_message,
                "confidence": check_result.confidence,
                "soft_warnings": check_result.soft_warnings,
            },
            "message": f"COMPLIANCE VIOLATION: {check_result.educational_message}",
        }

    implicit_warnings = _fairness_guard.check_implicit_bias(policy_text)
    all_warnings = list(set(check_result.soft_warnings + implicit_warnings))

    semantic_analysis = None
    if deep_check and all_warnings:
        try:
            semantic_result = await _fairness_guard.check_semantic(policy_text, context=field_name)
            if semantic_result.soft_warnings:
                all_warnings = list(set(all_warnings + semantic_result.soft_warnings))
            semantic_analysis = {
                "performed": True,
                "additional_warnings": semantic_result.soft_warnings,
            }
        except Exception as sem_err:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"[policy_tools] Semantic check failed: {sem_err}")
            semantic_analysis = {"performed": False, "error": str(sem_err)}

    return {
        "success": True,
        "data": {
            "is_compliant": True,
            "soft_warnings": all_warnings,
            "issues": [],
            "semantic_analysis": semantic_analysis,
        },
        "message": "Politica aprovada pelo FairnessGuard." + (
            f" Alertas: {'; '.join(all_warnings)}" if all_warnings else ""
        ),
    }


@tool_handler("hiring_policy")
async def _wrap_get_company_context(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    # ADR-001-EXEMPT: cross-domain context aggregation (job_vacancies + vacancy_candidates +
    # company_profiles) for AI prompt building — ContextAggregatorService is the canonical
    # alternative; inline SQL preserved until ContextAggregatorService migration is complete.
    async with AsyncSessionLocal() as session:
        jobs = await session.execute(
            text("""
                SELECT
                    COUNT(*) AS total_jobs,
                    COUNT(*) FILTER (WHERE status = 'active') AS active_jobs,
                    COUNT(*) FILTER (WHERE status = 'closed') AS closed_jobs
                FROM job_vacancies
                WHERE company_id = :company_id
            """),
            {"company_id": company_id},
        )
        jobs_row = jobs.mappings().first()

        candidates = await session.execute(
            text("""
                SELECT
                    COUNT(DISTINCT vc.candidate_id) AS total_candidates,
                    AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)::int AS avg_days_in_pipeline
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE jv.company_id = :company_id
            """),
            {"company_id": company_id},
        )
        cand_row = candidates.mappings().first()

        company = await session.execute(
            text("""
                SELECT name, industry, company_size, employee_count
                FROM company_profiles
                WHERE id::text = :company_id OR id::text LIKE :company_id_like
                LIMIT 1
            """),
            {"company_id": company_id, "company_id_like": f"%{company_id[:8]}%"},
        )
        comp_row = company.mappings().first()

        # NOTE (audit 2026-05-21, ratchet 2->0): este dict é retornado
        # ao LLM como resultado de tool call — NÃO é injetado direto no
        # system prompt. O LLM já viu o system prompt filtrado via
        # build_company_agent_context() upstream. Por isso este arquivo
        # está em ALLOWLIST_PREFIXES no lint canonical
        # (scripts/check_agent_respects_lia_toggles.py).
        return {
            "success": True,
            "data": {
                "company_name": comp_row["name"] if comp_row else "N/A",
                "industry": comp_row["industry"] if comp_row else "N/A",
                "company_size": comp_row["company_size"] if comp_row else "N/A",
                "employee_count": comp_row["employee_count"] if comp_row else 0,
                "total_jobs": jobs_row["total_jobs"] if jobs_row else 0,
                "active_jobs": jobs_row["active_jobs"] if jobs_row else 0,
                "total_candidates": cand_row["total_candidates"] if cand_row else 0,
                "avg_days_in_pipeline": cand_row["avg_days_in_pipeline"] if cand_row else 0,
            },
            "message": "Contexto da empresa carregado.",
        }


INDUSTRY_BENCHMARKS = {
    "technology": {
        "avg_interviews": 3,
        "avg_days_per_stage": {"triagem": 5, "avaliacao": 7, "entrevista": 10, "proposta": 5},
        "avg_time_to_fill_days": 35,
        "common_autonomy_level": "medium",
        "self_scheduling_adoption": "65%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 48,
        "preferred_channel": "email",
        "sources": [
            {"name": "Gupy - Pesquisa de Recrutamento Tech Brasil", "url": "https://www.gupy.io/blog/pesquisas", "year": 2024, "type": "report"},
            {"name": "LinkedIn Talent Solutions - Global Talent Trends", "url": "https://business.linkedin.com/talent-solutions/resources", "year": 2024, "type": "survey"},
            {"name": "Robert Half - Guia Salarial", "url": "https://www.roberthalf.com.br/guia-salarial", "year": 2024, "type": "report"},
        ],
        "last_updated": "2024-Q4",
    },
    "finance": {
        "avg_interviews": 4,
        "avg_days_per_stage": {"triagem": 3, "avaliacao": 5, "entrevista": 14, "proposta": 7},
        "avg_time_to_fill_days": 42,
        "common_autonomy_level": "low",
        "self_scheduling_adoption": "30%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 72,
        "preferred_channel": "email",
        "sources": [
            {"name": "Robert Half - Guia Salarial", "url": "https://www.roberthalf.com.br/guia-salarial", "year": 2024, "type": "report"},
            {"name": "ABRH - Pesquisa de Praticas de RH", "url": "https://www.abrh.org.br/pesquisas", "year": 2024, "type": "survey"},
            {"name": "Glassdoor Economic Research", "url": "https://www.glassdoor.com.br/research", "year": 2024, "type": "index"},
        ],
        "last_updated": "2024-Q4",
    },
    "retail": {
        "avg_interviews": 2,
        "avg_days_per_stage": {"triagem": 3, "avaliacao": 5, "entrevista": 7, "proposta": 3},
        "avg_time_to_fill_days": 21,
        "common_autonomy_level": "high",
        "self_scheduling_adoption": "40%",
        "auto_rejection_feedback": False,
        "feedback_deadline_hours": 24,
        "preferred_channel": "whatsapp",
        "sources": [
            {"name": "ABRH - Pesquisa de Praticas de RH", "url": "https://www.abrh.org.br/pesquisas", "year": 2024, "type": "survey"},
            {"name": "GPTW - Melhores Empresas para Trabalhar", "url": "https://gptw.com.br/ranking", "year": 2024, "type": "ranking"},
        ],
        "last_updated": "2024-Q4",
    },
    "healthcare": {
        "avg_interviews": 3,
        "avg_days_per_stage": {"triagem": 5, "avaliacao": 7, "entrevista": 12, "proposta": 7},
        "avg_time_to_fill_days": 45,
        "common_autonomy_level": "low",
        "self_scheduling_adoption": "25%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 72,
        "preferred_channel": "email",
        "sources": [
            {"name": "ABRH - Pesquisa de Praticas de RH", "url": "https://www.abrh.org.br/pesquisas", "year": 2024, "type": "survey"},
            {"name": "Robert Half - Guia Salarial", "url": "https://www.roberthalf.com.br/guia-salarial", "year": 2024, "type": "report"},
        ],
        "last_updated": "2024-Q4",
    },
    "legal": {
        "avg_interviews": 4,
        "avg_days_per_stage": {"triagem": 5, "avaliacao": 7, "entrevista": 14, "proposta": 10},
        "avg_time_to_fill_days": 50,
        "common_autonomy_level": "low",
        "self_scheduling_adoption": "20%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 72,
        "preferred_channel": "email",
        "sources": [
            {"name": "Robert Half - Guia Salarial", "url": "https://www.roberthalf.com.br/guia-salarial", "year": 2024, "type": "report"},
            {"name": "Glassdoor Economic Research", "url": "https://www.glassdoor.com.br/research", "year": 2024, "type": "index"},
        ],
        "last_updated": "2024-Q4",
    },
    "education": {
        "avg_interviews": 3,
        "avg_days_per_stage": {"triagem": 7, "avaliacao": 10, "entrevista": 14, "proposta": 7},
        "avg_time_to_fill_days": 45,
        "common_autonomy_level": "low",
        "self_scheduling_adoption": "30%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 48,
        "preferred_channel": "email",
        "sources": [
            {"name": "ABRH - Pesquisa de Praticas de RH", "url": "https://www.abrh.org.br/pesquisas", "year": 2024, "type": "survey"},
            {"name": "GPTW - Melhores Empresas para Trabalhar", "url": "https://gptw.com.br/ranking", "year": 2024, "type": "ranking"},
        ],
        "last_updated": "2024-Q4",
    },
    "manufacturing": {
        "avg_interviews": 2,
        "avg_days_per_stage": {"triagem": 3, "avaliacao": 5, "entrevista": 7, "proposta": 5},
        "avg_time_to_fill_days": 28,
        "common_autonomy_level": "medium",
        "self_scheduling_adoption": "35%",
        "auto_rejection_feedback": False,
        "feedback_deadline_hours": 48,
        "preferred_channel": "whatsapp",
        "sources": [
            {"name": "ABRH - Pesquisa de Praticas de RH", "url": "https://www.abrh.org.br/pesquisas", "year": 2024, "type": "survey"},
            {"name": "LinkedIn Talent Solutions - Global Talent Trends", "url": "https://business.linkedin.com/talent-solutions/resources", "year": 2024, "type": "survey"},
        ],
        "last_updated": "2024-Q4",
    },
    "services": {
        "avg_interviews": 2,
        "avg_days_per_stage": {"triagem": 3, "avaliacao": 5, "entrevista": 7, "proposta": 5},
        "avg_time_to_fill_days": 25,
        "common_autonomy_level": "medium",
        "self_scheduling_adoption": "45%",
        "auto_rejection_feedback": True,
        "feedback_deadline_hours": 48,
        "preferred_channel": "whatsapp",
        "sources": [
            {"name": "GPTW - Melhores Empresas para Trabalhar", "url": "https://gptw.com.br/ranking", "year": 2024, "type": "ranking"},
            {"name": "Glassdoor Economic Research", "url": "https://www.glassdoor.com.br/research", "year": 2024, "type": "index"},
        ],
        "last_updated": "2024-Q4",
    },
}


@tool_handler("hiring_policy", require_company=False)  # kept: static INDUSTRY_BENCHMARKS dict lookup, no tenant data
async def _wrap_get_industry_benchmarks(**kwargs: Any) -> dict[str, Any]:
    industry = kwargs.get("industry", "technology")

    industry_lower = industry.lower() if industry else "technology"
    data = INDUSTRY_BENCHMARKS.get(industry_lower, INDUSTRY_BENCHMARKS["technology"])
    available_sectors = list(INDUSTRY_BENCHMARKS.keys())

    return {
        "success": True,
        "data": {
            "industry": industry_lower,
            "benchmarks": data,
            "available_sectors": available_sectors,
        },
        "message": f"Benchmarks do setor '{industry_lower}' carregados com {len(data.get('sources', []))} fontes verificaveis.",
    }


@tool_handler("hiring_policy", require_company=False)  # kept: cross-tenant platform aggregation (by design)
async def _wrap_get_platform_benchmarks(**kwargs: Any) -> dict[str, Any]:
    industry = kwargs.get("industry", "")
    # ADR-001-EXEMPT: cross-tenant platform analytics (AVG/COUNT by industry + INTERVAL) —
    # GROUP BY aggregation, not abstractable to simple repo method without over-engineering.
    async with AsyncSessionLocal() as session:
        time_query = await session.execute(
            text("""
                SELECT
                    AVG(EXTRACT(EPOCH FROM (jv.updated_at - jv.created_at)) / 86400)::int AS avg_time_to_fill,
                    COUNT(*) AS total_jobs,
                    COUNT(*) FILTER (WHERE jv.status = 'closed') AS filled_jobs
                FROM job_vacancies jv
                LEFT JOIN company_profiles cp ON jv.company_id = cp.id::text
                WHERE (:industry = '' OR LOWER(cp.industry) = LOWER(:industry))
                AND jv.created_at > NOW() - INTERVAL '180 days'
            """),
            {"industry": industry},
        )
        time_row = time_query.mappings().first()

        stage_query = await session.execute(
            text("""
                SELECT
                    vc.stage,
                    COUNT(*) AS candidates_count,
                    AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)::int AS avg_days
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                LEFT JOIN company_profiles cp ON jv.company_id = cp.id::text
                WHERE (:industry = '' OR LOWER(cp.industry) = LOWER(:industry))
                AND vc.created_at > NOW() - INTERVAL '180 days'
                GROUP BY vc.stage
                ORDER BY candidates_count DESC
            """),
            {"industry": industry},
        )
        stage_rows = stage_query.mappings().all()

        total_jobs = time_row["total_jobs"] if time_row else 0

        if total_jobs < 5:
            return {
                "success": True,
                "data": {
                    "has_data": False,
                    "industry": industry or "todos",
                    "total_jobs_analyzed": total_jobs,
                },
                "message": f"Dados insuficientes na plataforma para o setor '{industry or 'todos'}' (apenas {total_jobs} vagas). Use benchmarks de mercado como referencia.",
            }

        stage_data = {}
        for row in stage_rows:
            stage_data[row["stage"]] = {
                "candidates": row["candidates_count"],
                "avg_days": row["avg_days"] or 0,
            }

        fill_rate = (time_row["filled_jobs"] / total_jobs * 100) if total_jobs > 0 else 0

        return {
            "success": True,
            "data": {
                "has_data": True,
                "industry": industry or "todos",
                "total_jobs_analyzed": total_jobs,
                "avg_time_to_fill_days": time_row["avg_time_to_fill"] or 0,
                "fill_rate_percent": round(fill_rate, 1),
                "stages": stage_data,
                "period": "ultimos 180 dias",
                "note": "Dados calculados a partir de processos reais na plataforma.",
            },
            "message": f"Benchmarks reais da plataforma para '{industry or 'todos'}': {total_jobs} vagas analisadas.",
        }


@tool_handler("hiring_policy", require_company=False)  # kept: pure dict lookup of impact templates, no tenant data
async def _wrap_explain_policy_impact(**kwargs: Any) -> dict[str, Any]:
    block = kwargs.get("block", "")
    field = kwargs.get("field", "")
    value = kwargs.get("value")

    impacts = {
        "automation_rules.autonomy_level": {
            "low": "Com autonomia BAIXA, a LIA vai pedir sua confirmacao para praticamente todas as acoes: triar candidatos, agendar entrevistas, mover entre etapas. Voce tem controle total mas o processo e mais lento.",
            "medium": "Com autonomia MEDIA, a LIA pode triar candidatos e agendar entrevistas sozinha, mas pedira confirmacao para acoes de alto impacto como rejeicoes em massa, propostas e contratacoes. Equilibrio entre controle e agilidade.",
            "high": "Com autonomia ALTA, a LIA age e notifica depois. Tria, agenda, move etapas e envia comunicacoes automaticamente. Voce so e consultada para decisoes irreversiveis como contratacao final e exclusao de vagas. Maximo de agilidade.",
        },
        "automation_rules.auto_screening": {
            True: "A LIA vai triar candidatos automaticamente com base nos criterios da vaga, movendo aprovados e reprovados sem aguardar sua confirmacao.",
            False: "A LIA vai analisar os candidatos e apresentar sua recomendacao, mas aguarda sua confirmacao antes de aprovar ou reprovar.",
        },
        "automation_rules.auto_scheduling": {
            True: "A LIA vai agendar entrevistas automaticamente com base nas regras de dias/horarios/duracao configuradas, enviando convites diretamente aos candidatos.",
            False: "A LIA vai sugerir horarios para entrevista mas aguarda sua confirmacao antes de enviar convites.",
        },
        "communication_rules.auto_rejection_feedback": {
            True: "Candidatos reprovados receberao feedback automatico e construtivo, melhorando a experiencia do candidato e a marca empregadora.",
            False: "Candidatos reprovados NAO receberao feedback automatico. Voce precisara decidir manualmente quando e como comunicar reprovacoes.",
        },
        "screening_rules.salary_expectation_filter": {
            True: "Candidatos com pretensao salarial acima da tolerancia definida serao filtrados automaticamente na triagem.",
            False: "A pretensao salarial nao sera usada como filtro eliminatorio, apenas como informacao adicional.",
        },
    }

    key = f"{block}.{field}"
    impact_map = impacts.get(key, {})
    impact_text = impact_map.get(value, impact_map.get(str(value), ""))

    if not impact_text:
        impact_text = f"A configuracao {block}.{field} = {value} sera aplicada em todos os processos seletivos da empresa."

    return {
        "success": True,
        "data": {
            "block": block,
            "field": field,
            "value": value,
            "impact": impact_text,
        },
        "message": impact_text,
    }


@tool_handler("hiring_policy")
async def _wrap_get_setup_progress(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    # ADR-001-EXEMPT: setup progress computation reads all 5 JSONB blocks + counts
    # non-empty fields per block — computed aggregation over policy JSONB structure,
    # not a simple repo lookup. Uses same approach as _wrap_get_current_policy pattern
    # but computes field-level counts inline. Acceptable deviation per audit review.
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT pipeline_rules, scheduling_rules, communication_rules,
                       screening_rules, automation_rules, setup_progress
                FROM company_hiring_policies
                WHERE company_id = :company_id
                LIMIT 1
            """),
            {"company_id": company_id},
        )
        row = result.mappings().first()

        if not row:
            return {
                "success": True,
                "data": {
                    "overall_progress": 0,
                    "blocks": {
                        "pipeline_rules": {"configured": False, "fields_set": 0, "total_fields": 4},
                        "scheduling_rules": {"configured": False, "fields_set": 0, "total_fields": 4},
                        "communication_rules": {"configured": False, "fields_set": 0, "total_fields": 4},
                        "screening_rules": {"configured": False, "fields_set": 0, "total_fields": 4},
                        "automation_rules": {"configured": False, "fields_set": 0, "total_fields": 4},
                    },
                    "pending_blocks": ["Pipeline e Processo", "Agendamento", "Comunicacao", "Triagem", "Autonomia da LIA"],
                },
                "message": "Nenhuma politica configurada. Todos os blocos estao pendentes.",
            }

        block_names = {
            "pipeline_rules": "Pipeline e Processo",
            "scheduling_rules": "Agendamento",
            "communication_rules": "Comunicacao",
            "screening_rules": "Triagem",
            "automation_rules": "Autonomia da LIA",
        }
        field_counts = {
            "pipeline_rules": 4,
            "scheduling_rules": 4,
            "communication_rules": 4,
            "screening_rules": 4,
            "automation_rules": 4,
        }

        blocks_info = {}
        pending = []
        total_fields = 0
        filled_fields = 0

        for block_key, block_name in block_names.items():
            block_data = row[block_key]
            if isinstance(block_data, str):
                try:
                    block_data = json.loads(block_data)
                except (json.JSONDecodeError, TypeError):
                    block_data = {}
            elif block_data is None:
                block_data = {}

            expected = field_counts.get(block_key, 4)
            fields_set = sum(1 for v in block_data.values() if v not in (None, "", [], {}))
            total_fields += expected
            filled_fields += min(fields_set, expected)

            configured = fields_set > 0
            blocks_info[block_key] = {
                "configured": configured,
                "fields_set": fields_set,
                "total_fields": expected,
                "block_name": block_name,
            }
            if not configured:
                pending.append(block_name)

        overall = int(filled_fields / total_fields * 100) if total_fields > 0 else 0

        return {
            "success": True,
            "data": {
                "overall_progress": overall,
                "blocks": blocks_info,
                "pending_blocks": pending,
                "completed_blocks": [
                    info["block_name"] for info in blocks_info.values() if info["configured"]
                ],
            },
            "message": f"Progresso: {overall}%. Pendentes: {', '.join(pending) if pending else 'nenhum'}.",
        }


@tool_handler("hiring_policy")
async def _wrap_detect_policy_impact_anomalies(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    # ADR-001-EXEMPT: anomaly detection combines policy config + stagnation + abandonment
    # analytics (GROUP BY vc.stage + INTERVAL/EXTRACT window functions) — cross-table
    # aggregation not abstractable to simple repo method without over-engineering.
    async with AsyncSessionLocal() as session:
        policy_result = await session.execute(
            text("""
                SELECT pipeline_rules, automation_rules, updated_at
                FROM company_hiring_policies
                WHERE company_id = :company_id
                LIMIT 1
            """),
            {"company_id": company_id},
        )
        policy_row = policy_result.mappings().first()
        if not policy_row:
            return {
                "success": True,
                "data": {"anomalies": [], "has_policy": False},
                "message": "Nenhuma politica configurada para analise de impacto.",
            }

        pipeline_rules = policy_row["pipeline_rules"]
        if isinstance(pipeline_rules, str):
            try:
                pipeline_rules = json.loads(pipeline_rules)
            except (json.JSONDecodeError, TypeError):
                pipeline_rules = {}
        elif pipeline_rules is None:
            pipeline_rules = {}

        max_days = pipeline_rules.get("max_days_in_stage", {})

        stagnated = await session.execute(
            text("""
                SELECT vc.stage, COUNT(*) AS stuck_count,
                       AVG(EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400)::int AS avg_days_stuck
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE jv.company_id = :company_id
                AND jv.status = 'active'
                AND vc.status NOT IN ('hired', 'rejected', 'withdrawn')
                AND EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400 > 7
                GROUP BY vc.stage
                ORDER BY stuck_count DESC
            """),
            {"company_id": company_id},
        )
        stagnated_rows = stagnated.mappings().all()

        abandonment = await session.execute(
            text("""
                SELECT vc.stage,
                       COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE vc.status = 'withdrawn') AS withdrawn
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE jv.company_id = :company_id
                AND vc.created_at > NOW() - INTERVAL '90 days'
                GROUP BY vc.stage
                HAVING COUNT(*) > 3
            """),
            {"company_id": company_id},
        )
        abandon_rows = abandonment.mappings().all()

        anomalies = []

        for row in stagnated_rows:
            stage = row["stage"] or "desconhecida"
            count = row["stuck_count"]
            avg_days = row["avg_days_stuck"] or 0
            stage_limit = max_days.get(stage, 7)

            if avg_days > stage_limit:
                severity = "critical" if avg_days > stage_limit * 2 else "warning"
                anomalies.append({
                    "type": "stagnation",
                    "severity": severity,
                    "stage": stage,
                    "stuck_count": count,
                    "avg_days_stuck": avg_days,
                    "sla_limit": stage_limit,
                    "recommendation": f"{count} candidatos estagnados na etapa '{stage}' ha {avg_days} dias (SLA: {stage_limit} dias). Considere revisar o SLA ou criar alertas automaticos.",
                })

        for row in abandon_rows:
            stage = row["stage"] or "desconhecida"
            total = row["total"]
            withdrawn = row["withdrawn"]
            rate = (withdrawn / total * 100) if total > 0 else 0
            if rate > 30:
                severity = "critical" if rate > 50 else "warning"
                anomalies.append({
                    "type": "high_abandonment",
                    "severity": severity,
                    "stage": stage,
                    "abandonment_rate": round(rate, 1),
                    "total_candidates": total,
                    "withdrawn": withdrawn,
                    "recommendation": f"Taxa de desistencia de {rate:.0f}% na etapa '{stage}'. Candidatos podem estar perdendo interesse. Considere reduzir o tempo nesta etapa ou melhorar a comunicacao.",
                })

        if not anomalies:
            anomalies.append({
                "type": "all_clear",
                "severity": "info",
                "recommendation": "Nenhuma anomalia detectada. As politicas estao operando dentro dos parametros esperados.",
            })

        return {
            "success": True,
            "data": {
                "anomalies": anomalies,
                "has_policy": True,
                "analysis_period": "ultimos 90 dias",
            },
            "message": f"Analise de impacto concluida: {len(anomalies)} observacoes encontradas.",
        }


@tool_handler("hiring_policy")
async def _wrap_get_policy_effectiveness_report(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    period_days = kwargs.get("period_days", 30)
    # ADR-001-EXEMPT: analytics aggregation (hiring_metrics COUNT/AVG + funnel GROUP BY stage
    # + INTERVAL dynamic period) — window functions, not abstractable to simple repo method.
    async with AsyncSessionLocal() as session:
        hiring_metrics = await session.execute(
            text("""
                SELECT
                    COUNT(*) AS total_jobs,
                    COUNT(*) FILTER (WHERE status = 'closed') AS filled_jobs,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400)::int AS avg_time_to_fill
                FROM job_vacancies
                WHERE company_id = :company_id
                AND created_at > NOW() - INTERVAL :period
            """),
            {"company_id": company_id, "period": f"{period_days} days"},
        )
        metrics_row = hiring_metrics.mappings().first()

        funnel = await session.execute(
            text("""
                SELECT
                    vc.stage,
                    COUNT(*) AS candidates,
                    COUNT(*) FILTER (WHERE vc.status = 'rejected') AS rejected,
                    COUNT(*) FILTER (WHERE vc.status = 'hired') AS hired,
                    AVG(EXTRACT(EPOCH FROM (vc.updated_at - vc.created_at)) / 86400)::int AS avg_days
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE jv.company_id = :company_id
                AND vc.created_at > NOW() - INTERVAL :period
                GROUP BY vc.stage
                ORDER BY candidates DESC
            """),
            {"company_id": company_id, "period": f"{period_days} days"},
        )
        funnel_rows = funnel.mappings().all()

        total_jobs = metrics_row["total_jobs"] if metrics_row else 0
        filled_jobs = metrics_row["filled_jobs"] if metrics_row else 0
        avg_ttf = metrics_row["avg_time_to_fill"] if metrics_row else 0
        fill_rate = (filled_jobs / total_jobs * 100) if total_jobs > 0 else 0

        funnel_data = {}
        for row in funnel_rows:
            funnel_data[row["stage"] or "unknown"] = {
                "candidates": row["candidates"],
                "rejected": row["rejected"],
                "hired": row["hired"],
                "avg_days_in_stage": row["avg_days"] or 0,
            }

        insights = []
        if avg_ttf and avg_ttf > 40:
            insights.append("Tempo medio de contratacao acima de 40 dias. Considere otimizar etapas com maior tempo de permanencia.")
        if fill_rate < 50 and total_jobs > 3:
            insights.append(f"Taxa de preenchimento de {fill_rate:.0f}% esta abaixo do ideal. Revise criterios de triagem ou amplie o funil de candidatos.")
        for stage, data in funnel_data.items():
            if data["candidates"] > 5 and data["avg_days_in_stage"] > 10:
                insights.append(f"Etapa '{stage}' tem tempo medio de {data['avg_days_in_stage']} dias. Considere ajustar o SLA.")

        if not insights:
            insights.append("Metricas dentro dos parametros esperados para o periodo analisado.")

        return {
            "success": True,
            "data": {
                "period_days": period_days,
                "total_jobs": total_jobs,
                "filled_jobs": filled_jobs,
                "fill_rate_percent": round(fill_rate, 1),
                "avg_time_to_fill_days": avg_ttf or 0,
                "funnel": funnel_data,
                "insights": insights,
            },
            "message": f"Relatorio de efetividade: {total_jobs} vagas, {fill_rate:.0f}% preenchidas, TTF medio: {avg_ttf or 'N/A'} dias.",
        }


@tool_handler("hiring_policy")
async def _wrap_save_policy_block(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    block = kwargs.get("block", "")
    data = kwargs.get("data", {})

    if block not in _VALID_POLICY_BLOCKS:
        return {
            "success": False,
            "data": {},
            "message": f"Bloco '{block}' nao e valido. Blocos validos: {sorted(_VALID_POLICY_BLOCKS)}",
        }

    if not _SAFE_COL_RE.match(block):
        return {"success": False, "data": {}, "message": f"Bloco '{block}' contém caracteres inválidos."}

    if not data or not isinstance(data, dict):
        return {
            "success": False,
            "data": {},
            "message": "Dados do bloco estao vazios ou invalidos.",
        }

    compliance_warnings = []
    if block == "screening_rules":
        for field_name, field_value in data.items():
            if isinstance(field_value, str):
                check = _fairness_guard.check(field_value)
                if check.is_blocked:
                    return {
                        "success": False,
                        "data": {"blocked_field": field_name, "category": check.category},
                        "message": f"Campo '{field_name}' bloqueado por compliance: {check.educational_message}",
                    }
                implicit = _fairness_guard.check_implicit_bias(field_value)
                compliance_warnings.extend(implicit)

    # ADR-001-EXEMPT: _VALID_POLICY_BLOCKS frozenset + _SAFE_COL_RE regex enforce
    # double sanitization on block name — dynamic block bulk-update with equivalent
    # security to typed repo method. FairnessGuard pre-validates screening_rules.
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text(f"SELECT id, {block} FROM company_hiring_policies WHERE company_id = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        row = existing.mappings().first()

        if row:
            current_block = row[block]
            if isinstance(current_block, str):
                try:
                    current_block = json.loads(current_block)
                except (json.JSONDecodeError, TypeError):
                    current_block = {}
            elif current_block is None:
                current_block = {}

            current_block.update(data)
            block_json = json.dumps(current_block, ensure_ascii=False)

            await session.execute(
                text(f"""
                    UPDATE company_hiring_policies
                    SET {block} = :block_data::jsonb, updated_at = NOW()
                    WHERE company_id = :company_id
                """),
                {"block_data": block_json, "company_id": company_id},
            )
        else:
            block_json = json.dumps(data, ensure_ascii=False)
            await session.execute(
                text(f"""
                    INSERT INTO company_hiring_policies (company_id, {block}, created_at, updated_at)
                    VALUES (:company_id, :block_data::jsonb, NOW(), NOW())
                """),
                {"company_id": company_id, "block_data": block_json},
            )

        await session.commit()

        return {
            "success": True,
            "data": {
                "block": block,
                "fields_saved": list(data.keys()),
                "field_count": len(data),
                "compliance_warnings": compliance_warnings,
            },
            "message": f"Bloco '{block}' salvo com {len(data)} campos: {', '.join(data.keys())}.",
        }


@tool_handler("hiring_policy")
async def _wrap_apply_industry_defaults(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    industry = kwargs.get("industry", "technology")

    industry_lower = industry.lower() if industry else "technology"
    benchmarks = INDUSTRY_BENCHMARKS.get(industry_lower, INDUSTRY_BENCHMARKS["technology"])

    defaults = {
        "pipeline_rules": {
            "min_interviews_before_offer": benchmarks["avg_interviews"],
            "manager_approval_for_offer": benchmarks["common_autonomy_level"] != "high",
            "max_days_in_stage": benchmarks["avg_days_per_stage"],
        },
        "scheduling_rules": {
            "allowed_days": ["mon", "tue", "wed", "thu", "fri"],
            "allowed_hours": {"start": "09:00", "end": "18:00"},
            "default_duration_minutes": 60,
            "self_scheduling_enabled": benchmarks["self_scheduling_adoption"].replace("%", "") > "40",
        },
        "communication_rules": {
            "auto_rejection_feedback": benchmarks["auto_rejection_feedback"],
            "rejection_feedback_deadline_hours": benchmarks["feedback_deadline_hours"],
            "preferred_channel": benchmarks["preferred_channel"],
            "lia_tone": "professional",
        },
        "screening_rules": {
            "salary_expectation_filter": False,
            "salary_tolerance_percent": 15,
            "experience_policy": "per_job",
        },
        "automation_rules": {
            "auto_screening": benchmarks["common_autonomy_level"] in ("medium", "high"),
            "auto_scheduling": benchmarks["common_autonomy_level"] == "high",
            "auto_stage_advance": benchmarks["common_autonomy_level"] == "high",
            "autonomy_level": benchmarks["common_autonomy_level"],
        },
    }

    # ADR-001-EXEMPT: multi-block dynamic UPDATE/INSERT from industry defaults dict —
    # iterates over 5 blocks with dynamic column names; not abstractable to simple repo
    # method without losing the dynamic-defaults pattern clarity.
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text("SELECT id FROM company_hiring_policies WHERE company_id = :company_id LIMIT 1"),
            {"company_id": company_id},
        )
        row = existing.mappings().first()

        if row:
            for block_name, block_data in defaults.items():
                block_json = json.dumps(block_data, ensure_ascii=False)
                await session.execute(
                    text(f"""
                        UPDATE company_hiring_policies
                        SET {block_name} = :block_data::jsonb, updated_at = NOW()
                        WHERE company_id = :company_id
                    """),
                    {"block_data": block_json, "company_id": company_id},
                )
        else:
            all_json = {k: json.dumps(v, ensure_ascii=False) for k, v in defaults.items()}
            await session.execute(
                text("""
                    INSERT INTO company_hiring_policies
                        (company_id, pipeline_rules, scheduling_rules, communication_rules,
                         screening_rules, automation_rules, created_at, updated_at)
                    VALUES
                        (:company_id, :pipeline_rules::jsonb, :scheduling_rules::jsonb,
                         :communication_rules::jsonb, :screening_rules::jsonb,
                         :automation_rules::jsonb, NOW(), NOW())
                """),
                {"company_id": company_id, **all_json},
            )

        await session.commit()

        applied_summary = []
        for block_name, block_data in defaults.items():
            fields = ", ".join(f"{k}={v}" for k, v in block_data.items())
            applied_summary.append(f"**{block_name}**: {fields}")

        return {
            "success": True,
            "data": {
                "industry": industry_lower,
                "blocks_applied": list(defaults.keys()),
                "defaults": defaults,
                "sources": benchmarks.get("sources", []),
            },
            "message": f"Defaults do setor '{industry_lower}' aplicados com sucesso em {len(defaults)} blocos. Fonte: {benchmarks.get('last_updated', 'N/A')}.",
        }


def get_policy_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="get_current_policy",
            description="Carrega todas as politicas de contratacao atuais da empresa do banco de dados.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_current_policy,
        ),
        ToolDefinition(
            side_effects=["write"],
            affects_candidate_decision=True,
            lgpd_legal_basis="LEGITIMATE_INTEREST",
            name="save_policy_field",
            description="Salva um campo especifico de politica no banco de dados. Use apos validar compliance.",
            parameters={
                "type": "object",
                "properties": {
                    "block": {"type": "string", "description": "Nome do bloco (pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules)"},
                    "field": {"type": "string", "description": "Nome do campo dentro do bloco"},
                    "value": {"description": "Valor a ser salvo (tipo varia por campo)"},
                },
                "required": ["block", "field", "value"],
            },
            output_schema=ToolOutput,
            function=_wrap_save_policy_field,
        ),
        ToolDefinition(
            name="get_policy_summary",
            description="Retorna um resumo formatado de todas as politicas configuradas da empresa.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_policy_summary,
        ),
        ToolDefinition(
            affects_candidate_decision=True,
            lgpd_legal_basis="LEGITIMATE_INTEREST",
            name="validate_policy_compliance",
            description="Verifica se uma politica proposta viola criterios eticos ou legais usando FairnessGuard. Detecta vies explicito (bloqueio) e implicito (alerta). DEVE ser chamada antes de salvar qualquer criterio de triagem ou filtro.",
            parameters={
                "type": "object",
                "properties": {
                    "policy_text": {"type": "string", "description": "Texto da politica a ser validada"},
                    "field_name": {"type": "string", "description": "Nome do campo sendo configurado"},
                    "deep_check": {"type": "boolean", "description": "Se True, usa analise semantica via LLM para detectar vies sutil. Padrao: False."},
                },
                "required": ["policy_text"],
            },
            output_schema=ToolOutput,
            function=_wrap_validate_policy_compliance,
        ),
        ToolDefinition(
            name="get_company_context",
            description="Busca dados reais da empresa (volume de vagas, candidatos, tempos medios) para embasar sugestoes inteligentes.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_company_context,
        ),
        ToolDefinition(
            name="get_industry_benchmarks",
            description="Retorna benchmarks do setor para comparacao (SLAs tipicos, taxas, praticas comuns).",
            parameters={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Setor da empresa (technology, finance, retail, etc.)"},
                },
                "required": ["industry"],
            },
            output_schema=ToolOutput,
            function=_wrap_get_industry_benchmarks,
        ),
        ToolDefinition(
            name="explain_policy_impact",
            description="Explica o impacto de uma configuracao especifica nos agentes e processos da plataforma.",
            parameters={
                "type": "object",
                "properties": {
                    "block": {"type": "string", "description": "Nome do bloco da politica"},
                    "field": {"type": "string", "description": "Nome do campo"},
                    "value": {"description": "Valor configurado"},
                },
                "required": ["block", "field", "value"],
            },
            affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST",
            output_schema=ToolOutput,
            function=_wrap_explain_policy_impact,
        ),
        ToolDefinition(
            name="get_setup_progress",
            description="Retorna o progresso da configuracao de politicas: quais blocos estao configurados, quais faltam, percentual geral.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_setup_progress,
        ),
        ToolDefinition(
            name="get_platform_benchmarks",
            description="Calcula benchmarks REAIS a partir dos dados da propria plataforma (tempo medio por etapa, taxa de conversao) para empresas do mesmo setor.",
            parameters={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Setor para filtrar (technology, finance, retail, etc.). Vazio para todos os setores."},
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_platform_benchmarks,
        ),
        ToolDefinition(
            name="detect_policy_impact_anomalies",
            description="Detecta anomalias causadas pelas politicas atuais: candidatos estagnados, taxas de abandono altas, SLAs violados. Use proativamente ao iniciar sessao.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            affects_candidate_decision=True, lgpd_legal_basis="LEGITIMATE_INTEREST",
            output_schema=ToolOutput,
            function=_wrap_detect_policy_impact_anomalies,
        ),
        ToolDefinition(
            name="get_policy_effectiveness_report",
            description="Gera relatorio de efetividade das politicas: tempo medio de contratacao, taxa de preenchimento, funil de conversao, insights e recomendacoes.",
            parameters={
                "type": "object",
                "properties": {
                    "period_days": {"type": "integer", "description": "Periodo em dias para analise (padrao: 30)"},
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_get_policy_effectiveness_report,
        ),
        ToolDefinition(
            side_effects=["write"],
            affects_candidate_decision=True,
            lgpd_legal_basis="LEGITIMATE_INTEREST",
            name="save_policy_block",
            description="Salva um bloco inteiro de politica de uma vez (todos os campos do bloco). Mais eficiente que save_policy_field para multiplos campos.",
            parameters={
                "type": "object",
                "properties": {
                    "block": {"type": "string", "description": "Nome do bloco (pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules)"},
                    "data": {"type": "object", "description": "Dicionario com todos os campos e valores do bloco"},
                },
                "required": ["block", "data"],
            },
            output_schema=ToolOutput,
            function=_wrap_save_policy_block,
        ),
        ToolDefinition(
            side_effects=["write"],
            requires_human_review=True,
            affects_candidate_decision=True,
            lgpd_legal_basis="LEGITIMATE_INTEREST",
            name="apply_industry_defaults",
            description="Aplica configuracoes padrao do setor em TODOS os blocos de uma vez. Ideal para 'configure tudo no padrao do mercado'.",
            parameters={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Setor da empresa (technology, finance, retail, healthcare, legal, education, manufacturing, services)"},
                },
                "required": ["industry"],
            },
            output_schema=ToolOutput,
            function=_wrap_apply_industry_defaults,
        ),
    ]


# ─── STAGE_TOOLS canonical allowlist ──────────────────────────────────────────
# Audit 2026-05-20 P1.6 / Tema C — canonical pattern CLAUDE.md (vacancy
# preview Phase E). Maps Hiring Policy stage → tools relevantes pro agente.
# Stages refletem fluxo natural de configuração de política: overview → edit
# → validate → benchmark → deploy. Fallback canonical: stage não declarado
# retorna TODAS as tools (backward compat).

STAGE_TOOLS: dict[str, list[str]] = {
    "policy-overview": [
        "get_current_policy",
        "get_policy_summary",
        "get_setup_progress",
        "get_company_context",
        "get_industry_benchmarks",
        "get_platform_benchmarks",
    ],
    "policy-edit": [
        "get_current_policy",
        "save_policy_field",
        "save_policy_block",
        "validate_policy_compliance",
        "get_setup_progress",
    ],
    "policy-validate": [
        "validate_policy_compliance",
        "detect_policy_impact_anomalies",
        "explain_policy_impact",
        "get_policy_effectiveness_report",
    ],
    "policy-benchmark": [
        "get_industry_benchmarks",
        "get_platform_benchmarks",
        "get_company_context",
        "explain_policy_impact",
    ],
    "policy-deploy": [
        "apply_industry_defaults",
        "save_policy_block",
        "validate_policy_compliance",
        "get_current_policy",
    ],
}


def get_hiring_policy_tools_for_stage(stage: str) -> list[ToolDefinition]:
    """
    Return Hiring Policy tools filtered by stage canonical.

    Stage names refletem o fluxo natural de policy setup:
      policy-overview, policy-edit, policy-validate, policy-benchmark,
      policy-deploy

    Fallback canonical: stage not in STAGE_TOOLS returns ALL tools
    (preserva backward compat de chamadas conversacionais sem stage).
    """
    all_tools = get_policy_tools()
    tool_names = STAGE_TOOLS.get(stage)
    if tool_names is None:
        return all_tools
    tool_map = {t.name: t for t in all_tools}
    return [tool_map[name] for name in tool_names if name in tool_map]
