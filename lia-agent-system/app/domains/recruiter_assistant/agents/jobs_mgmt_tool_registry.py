"""
Jobs Management Tool Registry - Exposes job portfolio tools to the ReAct loop.

Wraps job management operations into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call for portfolio management.

ADR-001 W1-004-B Commit 3: all SQL inline blocks migrated to
JobVacancyCRUDRepository. No AsyncSessionLocal() calls remain here.
"""
import logging
import uuid
from typing import Any

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.core.database import AsyncSessionLocal
from app.domains.hiring_policy.agents.policy_tool_registry import INDUSTRY_BENCHMARKS
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


@tool_handler("jobs_mgmt")
async def _wrap_get_recruitment_benchmarks(**kwargs: Any) -> dict[str, Any]:
    company_id = kwargs.get("company_id", "")
    period_days = kwargs.get("period_days", 90)
    logger.info(
        f"[jobs_mgmt_tools] get_recruitment_benchmarks called: "
        f"company={company_id} period={period_days}d"
    )

    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            benchmarks = await repo.get_recruitment_benchmarks(
                company_id=company_id,
                period_days=period_days,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] SQL error in get_recruitment_benchmarks: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar os benchmarks agora. Tente novamente em instantes.",
        }

    ttf = benchmarks.get("avg_ttf_days", 0.0)
    fill_rate = benchmarks.get("fill_rate", 0.0)
    active_jobs = benchmarks.get("active_jobs", 0)
    total_jobs = benchmarks.get("total_jobs", 0)
    filled_jobs = benchmarks.get("filled_jobs", 0)

    market_benchmarks = INDUSTRY_BENCHMARKS.get("technology", {})
    market_ttf = market_benchmarks.get("avg_time_to_fill_days", 35)
    market_sources = [s["name"] for s in market_benchmarks.get("sources", [])]
    if not market_sources:
        market_sources = [
            "Robert Half - Guia Salarial 2024",
            "Gupy - Pesquisa de Recrutamento 2024",
            "LinkedIn Talent Solutions - Global Talent Trends",
            "ABRH - Pesquisa de Indicadores de RH",
            "GPTW - Melhores Empresas para Trabalhar",
        ]

    if ttf > 0 and market_ttf > 0:
        ratio = ttf / market_ttf
        if ratio <= 0.8:
            comparison = "above_market"
        elif ratio <= 1.2:
            comparison = "at_market"
        else:
            comparison = "below_market"
    else:
        comparison = "no_data"

    return {
        "success": True,
        "data": {
            "company_id": company_id,
            "period_days": period_days,
            "ttf": ttf,
            "fill_rate": fill_rate,
            "active_jobs": active_jobs,
            "total_jobs": total_jobs,
            "filled_jobs": filled_jobs,
            "market_avg_ttf": market_ttf,
            "comparison_with_market": comparison,
        },
        "sources": market_sources + ["Dados internos da empresa (historico de vagas)"],
        "message": (
            f"Benchmarks de recrutamento carregados para empresa "
            f"{company_id or 'N/A'} ({period_days} dias)."
        ),
    }


def _format_location(loc) -> str | None:
    """Formata location para string legivel — trata objeto JSON e string."""
    if not loc:
        return None
    if isinstance(loc, str):
        # Tenta parsear JSON serializado como string
        try:
            import json as _json
            parsed = _json.loads(loc)
            if isinstance(parsed, dict):
                loc = parsed
            else:
                return loc.strip() or None
        except Exception:
            return loc.strip() or None
    if isinstance(loc, dict):
        parts = [loc.get("city"), loc.get("state"), loc.get("country")]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None
    return str(loc) or None


def _normalize_job_for_card(j: dict) -> dict:
    """Normaliza job dict para o shape JobSummary esperado pelo FE (JobListCard)."""
    return {
        "id": str(j.get("id") or j.get("job_id") or ""),
        "title": j.get("title") or j.get("job_title") or "",
        "department": j.get("department") or j.get("department_name") or None,
        "location": _format_location(j.get("location")),
        "status": j.get("status") or j.get("job_status") or None,
        "candidateCount": j.get("candidate_count") or j.get("candidates_count") or None,
        "daysOpen": j.get("days_open") or None,
        "priority": j.get("priority") or None,
    }


def _format_list_jobs_result(jobs_list: list, *, total: int = 0) -> dict:
    """P2.5-BE: formata resultado de list_jobs com response_blocks list_jobs_result.

    Produtor UNICO (canonical-fix) — adicionar response_blocks de tipo list_jobs_result
    para que o FE renderize JobListCard. Dados originais (status_filter, etc.) continuam
    em data para consumo pelo LLM.

    Seguindo precedente de _format_search_candidates_result (P2.4).
    """
    _total = total or len(jobs_list)
    response_blocks = (
        [
            {
                "type": "list_jobs_result",
                "data": {
                    "jobs": [_normalize_job_for_card(j) for j in jobs_list[:20]],
                    "total_count": _total,
                },
            }
        ]
        if jobs_list
        else None
    )
    return {
        "success": True,
        "data": {
            "total_jobs": _total,
            "jobs": jobs_list,
            "response_blocks": response_blocks,
        },
        "message": f"{_total} vagas encontradas.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_list_jobs(**kwargs: Any) -> dict[str, Any]:
    raw_status = kwargs.get("status", "ativa")
    department = kwargs.get("department", "all")
    company_id = kwargs.get("company_id", "")
    limit = min(int(kwargs.get("limit", 20)), 50)
    query: str | None = kwargs.get("query") or kwargs.get("title_query") or None
    status_map = {
        "active": "Ativa", "ativa": "Ativa",
        "paused": "Pausada", "pausada": "Pausada",
        "closed": "Concluída", "concluida": "Concluída", "concluída": "Concluída",
        "draft": "Rascunho", "rascunho": "Rascunho",
        "cancelled": "Cancelada", "cancelada": "Cancelada",
        "archived": "Arquivada", "arquivada": "Arquivada",
        "all": "all",
    }
    status = status_map.get(raw_status.lower(), raw_status) if raw_status else "all"
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] list_jobs called: status={status} department={department} query={query!r}")

    jobs: list[dict] = []
    total = 0
    status_breakdown: dict[str, int] = {}
    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            result = await repo.list_jobs_with_candidate_count(
                company_id=company_id,
                status=status,
                department=department,
                limit=limit,
                title_query=query,
            )
            jobs = result["jobs"]
            total = result["total"]
            try:
                status_breakdown = await repo.count_by_status(company_id)
            except Exception:
                status_breakdown = {}
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] list_jobs DB error: {e}")

    _bd = ", ".join(
        f"{k}: {v}" for k, v in sorted(status_breakdown.items(), key=lambda x: -x[1])
    )
    _blocks, _hint = [], ""
    if jobs:
        try:
            from app.shared.rrp_ranking_builder import build_table_block, RRP_TABLE_HINT
            _hint = RRP_TABLE_HINT
            _blocks = build_table_block(
                title="Vagas",
                entity_type="job",
                source_tool="list_jobs",
                total_count=total,
                columns=[
                    ("title", "Vaga", "text"),
                    ("department", "Departamento", "text"),
                    ("location", "Local", "text"),
                    ("candidate_count", "Candidatos", "number"),
                    ("days_open", "Dias aberta", "number"),
                    ("priority", "Prioridade", "badge"),
                ],
                rows=[
                    {
                        "entity_id": str(j.get("id")),
                        "cells": {
                            "title": j.get("title"),
                            "department": j.get("department"),
                            "location": _format_location(j.get("location")),
                            "candidate_count": j.get("candidate_count"),
                            "days_open": j.get("days_open"),
                            "priority": j.get("priority"),
                        },
                    }
                    for j in jobs
                ],
            )
        except Exception as _e:
            logger.warning(f"[jobs_mgmt_tools] list_jobs RRP table skipped: {_e}")
    _msg = (
        f"{total} vagas no total -- por status: {_bd}." if _bd
        else f"{total} vagas encontradas (status={status}, departamento={department})."
    )
    # FIX (2026-06-14): list_jobs_result foi removido — duplicava o display
    # pois o build_table_block (kind-based) já renderiza os dados na tabela RRP.
    # Ter os dois causava: tabela enriquecida + card simples para o mesmo dado,
    # e se list_jobs era chamado 2× no mesmo turno = 2 tabelas + 2 cards.
    _all_blocks = _blocks  # apenas RRP kind-based

    if _all_blocks:
        _data = {
            "status_filter": status,
            "department_filter": department,
            "total_jobs": total,
            "status_breakdown": status_breakdown,
            "rendered_as_card": True,
            "narrative": f"{total} vagas (filtro status={status}).",
            "response_blocks": _all_blocks,
            "render_hint": (
                "CARD VISUAL JÁ ENVIADO. Escreva APENAS 1-2 frases narrativas resumindo o total e destaques. "
                "NUNCA repita dados em tabela markdown. "
                "Os IDs em jobs_index estão disponíveis para follow-up."
            ),
            "jobs_index": [
                {
                    "id": str(j.get("id", "")),
                    "title": j.get("title", ""),
                    "status": j.get("status", ""),
                    "department": j.get("department", ""),
                }
                for j in jobs[:20]
            ],
        }
    else:
        _data = {
            "status_filter": status,
            "department_filter": department,
            "total_jobs": total,
            "status_breakdown": status_breakdown,
            "jobs": jobs,
        }
    return {"success": True, "data": _data, "message": _msg}


@tool_handler("jobs_mgmt")
async def _wrap_view_job_details(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")  # P0.A canonical: tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] view_job_details called for job={job_id}")

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCrudRepository(db)
        data = await repo.get_job_details_with_days_open(
            job_id=job_id,
            company_id=company_id,
        )

    if not data:
        return {"success": False, "data": {}, "message": f"Vaga {job_id} nao encontrada."}

    return {
        "success": True,
        "data": data,
        "message": (
            f"Detalhes da vaga '{data['title']}' carregados. "
            f"{data['candidates_total']} candidatos."
        ),
    }


@tool_handler("jobs_mgmt")
async def _wrap_get_portfolio_metrics(**kwargs: Any) -> dict[str, Any]:
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] get_portfolio_metrics called: period={period}")

    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            metrics = await repo.get_portfolio_metrics(
                company_id=company_id,
                period_days=period_days,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] get_portfolio_metrics DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar as métricas do portfolio agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": {**metrics, "period": period},
        "message": (
            f"Metricas do portfolio ({period}): "
            f"{metrics.get('total_active', 0)} ativas, "
            f"fill rate {metrics.get('fill_rate', 0)}%."
        ),
    }


@tool_handler("jobs_mgmt")
async def _wrap_compare_jobs(**kwargs: Any) -> dict[str, Any]:
    job_ids = kwargs.get("job_ids", [])
    company_id = kwargs.get("company_id", "")  # P0.A canonical: batch tenant gate
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] compare_jobs called: jobs={job_ids}")

    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            comparison = await repo.compare_jobs_by_ids(
                job_ids=job_ids,
                company_id=company_id,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] compare_jobs DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui comparar as vagas agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": {
            "job_ids": job_ids,
            "comparison_count": len(comparison),
            "comparison": comparison,
        },
        "message": f"Comparacao de {len(comparison)} vagas concluida.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_check_sla(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] check_sla called: job={job_id or 'all'}")

    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            sla = await repo.get_sla_status(
                company_id=company_id,
                job_id=job_id,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] check_sla DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui consultar o status de SLA agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": {
            "job_id": job_id or "all",
            "sla_status": sla["overall_status"],
            "overdue": len(sla["overdue_jobs"]),
            "at_risk": len(sla["at_risk_jobs"]),
            "compliant": sla["compliant_count"],
            "overdue_jobs": sla["overdue_jobs"],
            "at_risk_jobs": sla["at_risk_jobs"],
        },
        "message": (
            f"SLA: {len(sla['overdue_jobs'])} vencidas, "
            f"{len(sla['at_risk_jobs'])} em risco, "
            f"{sla['compliant_count']} ok."
        ),
    }


@tool_handler("jobs_mgmt")
async def _wrap_analyze_bottlenecks(**kwargs: Any) -> dict[str, Any]:
    department = kwargs.get("department", "all")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] analyze_bottlenecks called: department={department}")

    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            bottlenecks = await repo.get_bottleneck_analysis(
                company_id=company_id,
                department=department,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] analyze_bottlenecks DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui analisar os gargalos agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": {
            "department": department,
            "bottlenecks": bottlenecks,
            "total_identified": len(bottlenecks),
            "analysis_complete": True,
        },
        "message": f"{len(bottlenecks)} gargalos identificados no departamento '{department}'.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_pause_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] pause_job called: job={job_id} reason={reason}")

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCrudRepository(db)
        found = await repo.update_status(
            job_id=job_id,
            company_id=company_id,
            new_status="Pausada",
        )
        if not found:
            return {
                "success": False,
                "data": {},
                "message": f"Vaga {job_id} nao encontrada ou sem permissao.",
            }
        await db.commit()

    return {
        "success": True,
        "data": {"job_id": job_id, "new_status": "Pausada", "reason": reason},
        "message": f"Vaga {job_id} pausada com sucesso.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_reopen_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] reopen_job called: job={job_id}")

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCrudRepository(db)
        found = await repo.update_status(
            job_id=job_id,
            company_id=company_id,
            new_status="Ativa",
        )
        if not found:
            return {
                "success": False,
                "data": {},
                "message": f"Vaga {job_id} nao encontrada ou sem permissao.",
            }
        await db.commit()

    return {
        "success": True,
        "data": {"job_id": job_id, "new_status": "Ativa"},
        "message": f"Vaga {job_id} reaberta com sucesso.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_close_job(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    reason = kwargs.get("reason", "")
    company_id = kwargs.get("company_id", "")
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] close_job called: job={job_id} reason={reason}")

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCrudRepository(db)
        found = await repo.update_status(
            job_id=job_id,
            company_id=company_id,
            new_status="Concluída",
        )
        if not found:
            return {
                "success": False,
                "data": {},
                "message": f"Vaga {job_id} nao encontrada ou sem permissao.",
            }
        await db.commit()

    return {
        "success": True,
        "data": {"job_id": job_id, "new_status": "Concluída", "reason": reason},
        "message": f"Vaga {job_id} fechada com sucesso.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_update_priority(**kwargs: Any) -> dict[str, Any]:
    job_id = kwargs.get("job_id", "")
    priority = kwargs.get("priority", "média")
    company_id = kwargs.get("company_id", "")
    priority_map = {
        "high": "alta", "medium": "média", "low": "baixa",
        "alta": "alta", "média": "média", "baixa": "baixa",
    }
    priority_pt = priority_map.get(priority.lower(), priority)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] update_priority called: job={job_id} priority={priority_pt}")

    async with AsyncSessionLocal() as db:
        repo = JobVacancyCrudRepository(db)
        result = await repo.update_priority(
            job_id=job_id,
            company_id=company_id,
            priority=priority_pt,
        )
        if result is None:
            return {
                "success": False,
                "data": {},
                "message": f"Vaga {job_id} nao encontrada.",
            }
        await db.commit()

    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "previous_priority": result["previous_priority"],
            "new_priority": priority_pt,
        },
        "message": f"Prioridade da vaga {job_id} atualizada para '{priority_pt}'.",
    }


@tool_handler("jobs_mgmt")
async def _wrap_generate_report(**kwargs: Any) -> dict[str, Any]:
    report_type = kwargs.get("report_type", "summary")
    period = kwargs.get("period", "month")
    company_id = kwargs.get("company_id", "")
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"[jobs_mgmt_tools] generate_report called: type={report_type} period={period}")

    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    try:
        async with AsyncSessionLocal() as db:
            repo = JobVacancyCrudRepository(db)
            summary = await repo.get_report_summary(
                company_id=company_id,
                period_days=period_days,
            )
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.warning(f"[jobs_mgmt_tools] generate_report DB error: {e}")
        return {
            "success": False,
            "message": "Não consegui gerar o relatório agora. Tente novamente em instantes.",
        }

    return {
        "success": True,
        "data": {
            "report_type": report_type,
            "period": period,
            "report_id": report_id,
            "generated": True,
            "summary": summary,
        },
        "message": (
            f"Relatorio '{report_type}' gerado (id: {report_id}). "
            f"{summary.get('total_jobs', 0)} vagas no periodo."
        ),
    }


@tool_handler("jobs_mgmt")
async def _wrap_validate_job_action_fairness(**kwargs: Any) -> dict[str, Any]:
    action_description = kwargs.get("action_description", "")
    action_type = kwargs.get("action_type", "general")
    logger.info(
        f"[jobs_mgmt_tools] validate_job_action_fairness called: "
        f"type={action_type} desc='{action_description[:60]}...'"
    )

    if not action_description.strip():
        return {
            "success": False,
            "message": "Descricao da acao vazia. Informe o texto a validar.",
        }

    try:
        result = _fairness_guard.check(action_description)
        implicit_warnings = _fairness_guard.check_implicit_bias(action_description)

        if result.is_blocked:
            return {
                "success": True,
                "data": {
                    "is_compliant": False,
                    "blocked": True,
                    "category": result.category,
                    "blocked_terms": result.blocked_terms,
                    "educational_message": result.educational_message,
                    "soft_warnings": implicit_warnings,
                },
                "message": f"Acao BLOQUEADA por vies discriminatorio: {result.educational_message}",
            }

        semantic_warnings = []
        try:
            semantic_result = await _fairness_guard.check_semantic(
                action_description, context=f"job_action_{action_type}"
            )
            if semantic_result.is_blocked:
                return {
                    "success": True,
                    "data": {
                        "is_compliant": False,
                        "blocked": True,
                        "category": semantic_result.category,
                        "blocked_terms": semantic_result.blocked_terms,
                        "educational_message": semantic_result.educational_message,
                        "soft_warnings": implicit_warnings + (semantic_result.soft_warnings or []),
                    },
                    "message": (
                        f"Acao BLOQUEADA por vies semantico: "
                        f"{semantic_result.educational_message}"
                    ),
                }
            semantic_warnings = semantic_result.soft_warnings or []
        except Exception as sem_err:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.debug(f"[jobs_mgmt_tools] semantic check skipped: {sem_err}")

        all_warnings = implicit_warnings + [
            w for w in semantic_warnings if w not in implicit_warnings
        ]

        return {
            "success": True,
            "data": {
                "is_compliant": True,
                "blocked": False,
                "soft_warnings": all_warnings,
            },
            "message": "Acao validada. Nenhum vies discriminatorio detectado."
            + (f" {len(all_warnings)} alertas de vies implicito." if all_warnings else ""),
        }
    except Exception as e:
        # P0 LGPD (audit 2026-05-20 — sensor check_no_silent_llm_fallback):
        # REGRA 4 CLAUDE.md — fail-CLOSED em fairness check. Anteriormente
        # retornava success=True + is_compliant=True mesmo no erro, mascarando
        # falha e potencialmente liberando acao com vies. Agora retorna
        # success=False + needs_manual_review=True; agente deve parar e pedir
        # review humano.
        logger.exception(
            "[jobs_mgmt_tools] validate_job_action_fairness FAILED -- failing CLOSED"
        )
        return {
            "success": False,
            "data": {
                "is_compliant": False,
                "blocked": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "soft_warnings": [],
            },
            "error": f"Fairness check failed: {str(e)}",
            "message": (
                "Nao foi possivel validar a acao por vies. "
                "Por seguranca (fail-closed LGPD), revise manualmente antes de prosseguir."
            ),
        }


@tool_handler("jobs_mgmt")
async def _wrap_get_pipeline_prediction_jobs_mgmt(**kwargs: Any) -> dict[str, Any]:
    """Return closure probability prediction for company overview or individual vacancy."""
    from app.shared.services.pipeline_prediction_service import pipeline_prediction_service

    vacancy_id = kwargs.get("vacancy_id", "")
    company_id = kwargs.get("company_id", "")

    if vacancy_id:
        result = await pipeline_prediction_service.get_vacancy_prediction(
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
        prob = result.get("closure_probability", 0)
        est = result.get("estimated_days_to_close")
        days_str = f" em ~{est} dias" if est else ""
        interpretation = (
            f"Probabilidade de fechamento: {prob}%{days_str}. "
            f"Confiança: {result.get('confidence_level', 'medium')}."
        )
    else:
        result = await pipeline_prediction_service.get_company_overview(
            company_id=company_id,
        )
        summary = result.get("summary", {})
        vacancies = result.get("vacancies", [])
        at_risk = [v for v in vacancies if v["closure_probability"] < 30]
        near = [v for v in vacancies if v["closure_probability"] >= 80]
        interpretation = (
            f"{summary.get('total_active_vacancies', 0)} vagas ativas. "
            f"{len(at_risk)} em risco de não fechar: "
            + (
                ", ".join(
                    f"'{v['vacancy_title']}' ({v['closure_probability']}%)"
                    for v in at_risk[:3]
                )
                or "nenhuma"
            )
            + f". {len(near)} prestes a fechar: "
            + (
                ", ".join(
                    f"'{v['vacancy_title']}' ({v['closure_probability']}%)"
                    for v in near[:3]
                )
                or "nenhuma"
            )
            + "."
        )
    result["success"] = True
    result["interpretation"] = interpretation
    return result


TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="validate_job_action_fairness",
        description="Valida acoes de gestao de vagas contra vies discriminatorio usando FairnessGuard. Use ao fechar, pausar ou modificar vagas com justificativas do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "action_description": {"type": "string", "description": "Texto descrevendo a acao ou justificativa a validar"},
                "action_type": {"type": "string", "description": "Tipo da acao: close, pause, reopen, priority_change"},
            },
            "required": ["action_description"],
        },
        output_schema=ToolOutput,
        function=_wrap_validate_job_action_fairness,
    ),
    ToolDefinition(
        name="get_recruitment_benchmarks",
        description="Obtem benchmarks reais de recrutamento via SQL: time-to-fill, fill rate, vagas por status, comparacao com mercado por setor. Fontes citaveis incluidas.",
        parameters={
            "type": "object",
            "properties": {
                "period_days": {"type": "integer", "description": "Periodo em dias para analise (padrao: 90)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_recruitment_benchmarks,
    ),
    ToolDefinition(
        name="list_jobs",
        description=(
            "Lista vagas com status, metricas e informacoes resumidas do portfolio. "
            "Use o parametro 'query' para buscar por nome/titulo (substring case-insensitive). "
            "Exemplo: query='Diretor Juridico' retorna vagas cujo titulo contem essa expressao. "
            "Sem query retorna as 50 vagas mais recentes/prioritarias. "
            "Os IDs retornados em jobs_index podem ser usados diretamente em view_job_details(job_id=...) para detalhes de uma vaga especifica."
        ),
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": (
                        "Filtro de status da vaga. PADRAO: ativa (vagas abertas/ativas). "
                        "Valores aceitos: ativa, pausada, concluida, rascunho, cancelada, arquivada, all. "
                        "Use all SOMENTE quando o usuario pedir explicitamente TODAS as vagas independente de status."
                    ),
                },
                "department": {"type": "string", "description": "Filtro por departamento (padrao: all)"},
                "query": {
                    "type": "string",
                    "description": "Busca por titulo da vaga (substring, case-insensitive). Use quando o usuario mencionar o nome de uma vaga especifica.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero maximo de vagas a retornar (padrao: 20, max: 50)",
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_list_jobs,
    ),
    ToolDefinition(
        name="view_job_details",
        description="Visualiza informacoes detalhadas de uma vaga especifica, incluindo pipeline, candidatos e metricas.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga — use os IDs do jobs_index retornado pelo list_jobs"},
            },
            "required": ["job_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_view_job_details,
    ),
    ToolDefinition(
        name="get_portfolio_metrics",
        description="Obtem metricas agregadas do portfolio de vagas como taxa de preenchimento, tempo medio e distribuicao.",
        parameters={
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_portfolio_metrics,
    ),
    ToolDefinition(
        name="compare_jobs",
        description="Compara multiplas vagas lado a lado em dimensoes como pipeline, velocidade e qualidade.",
        parameters={
            "type": "object",
            "properties": {
                "job_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs das vagas para comparar"},
            },
            "required": ["job_ids"],
        },
        output_schema=ToolOutput,
        function=_wrap_compare_jobs,
    ),
    ToolDefinition(
        name="check_sla",
        description="Verifica compliance de SLA das vagas, identificando vagas em risco ou com prazo vencido.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga (vazio para verificar todas)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_check_sla,
    ),
    ToolDefinition(
        name="analyze_bottlenecks",
        description="Identifica gargalos no pipeline de recrutamento entre todas as vagas, por departamento ou geral.",
        parameters={
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Departamento para analisar (vazio para todos)"},
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_analyze_bottlenecks,
    ),
    ToolDefinition(
        side_effects=["write"],
        name="pause_job",
        description="Pausa uma vaga ativa. Requer motivo e confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "reason": {"type": "string", "description": "Motivo para pausar a vaga"},
            },
            "required": ["job_id", "reason"],
        },
        output_schema=ToolOutput,
        function=_wrap_pause_job,
    ),
    ToolDefinition(
        side_effects=["write"],
        name="reopen_job",
        description="Reabre uma vaga pausada ou fechada, reativando o pipeline de recrutamento.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
            },
            "required": ["job_id"],
        },
        output_schema=ToolOutput,
        function=_wrap_reopen_job,
    ),
    ToolDefinition(
        side_effects=["write"],
        requires_human_review=True,
        name="close_job",
        description="Fecha uma vaga definitivamente. Requer motivo e confirmacao do recrutador.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "reason": {"type": "string", "description": "Motivo para fechar a vaga"},
            },
            "required": ["job_id", "reason"],
        },
        output_schema=ToolOutput,
        function=_wrap_close_job,
    ),
    ToolDefinition(
        side_effects=["write"],
        name="update_priority",
        description="Atualiza o nivel de prioridade de uma vaga (alta, media, baixa).",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID da vaga"},
                "priority": {"type": "string", "description": "Nova prioridade: high, medium, low"},
            },
            "required": ["job_id", "priority"],
        },
        output_schema=ToolOutput,
        function=_wrap_update_priority,
    ),
    ToolDefinition(
        name="generate_report",
        description="Gera um relatorio do portfolio de vagas com metricas, analises e recomendacoes.",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "Tipo: summary, detailed, sla"},
                "period": {"type": "string", "description": "Periodo: week, month, quarter"},
            },
            "required": ["report_type"],
        },
        output_schema=ToolOutput,
        function=_wrap_generate_report,
    ),
    ToolDefinition(
        affects_candidate_decision=True,
        lgpd_legal_basis="LEGITIMATE_INTEREST",
        name="get_pipeline_prediction",
        description=(
            "Retorna previsão de fechamento de vagas ativas: probabilidade (0–100%), "
            "prazo estimado, confiança da previsão, fatores positivos e de risco. "
            "Sem vacancy_id retorna visão geral de todas as vagas da empresa ordenadas por risco. "
            "Use para responder: 'qual a chance de fechar essas vagas?', 'quais vagas vão fechar logo?', "
            "'quais vagas estão em risco?', 'previsão de fechamento do pipeline', "
            "'probabilidade de fechar esse mês'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vacancy_id": {
                    "type": "string",
                    "description": "ID da vaga (opcional — sem este campo retorna visão geral da empresa).",
                },
            },
            "required": [],
        },
        output_schema=ToolOutput,
        function=_wrap_get_pipeline_prediction_jobs_mgmt,
    ),
]

_TOOL_MAP: dict[str, ToolDefinition] = {t.name: t for t in TOOL_DEFINITIONS}

STAGE_TOOLS: dict[str, list[str]] = {
    "overview": ["list_jobs", "view_job_details", "get_portfolio_metrics", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
    "analysis": ["compare_jobs", "check_sla", "analyze_bottlenecks", "view_job_details", "get_portfolio_metrics", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
    "action": ["pause_job", "reopen_job", "close_job", "update_priority", "generate_report", "get_recruitment_benchmarks", "validate_job_action_fairness", "get_pipeline_prediction"],
}


def get_jobs_mgmt_tools(stage: str = "") -> list[ToolDefinition]:
    """Return jobs management tools, optionally filtered by stage.

    Args:
        stage: Current stage identifier. If empty, returns all tools.

    Returns:
        List of ToolDefinition instances available for the given stage.
    """
    if not stage:
        return list(TOOL_DEFINITIONS)

    tool_names = STAGE_TOOLS.get(stage, list(_TOOL_MAP.keys()))
    tools = [_TOOL_MAP[name] for name in tool_names if name in _TOOL_MAP]
    return tools


# ─────────────────────────────────────────────────────────────────────────────
# Opção C — registro global com namespace de domínio (2026-06-18)
# ─────────────────────────────────────────────────────────────────────────────

def register_jobs_mgmt_global() -> int:
    """Registra as tools de gestão de vagas no tool_registry global.

    Tools com nomes conflitantes recebem prefixo 'jm_' (Opção C —
    namespace de domínio). Tools únicas mantêm o nome original.
    Segue o padrão de register_ui_tools_global() (ui_tool_registry.py).
    Chamada por app/tools/__init__.py:initialize_tools().

    Renames:
        pause_job             → jm_pause_job
        close_job             → jm_close_job
        generate_report       → jm_generate_report
        get_pipeline_prediction → jm_pipeline_prediction
    """
    from app.tools.registry import ToolDefinition as _G
    from app.tools.registry import tool_registry as _reg

    _RENAMES: dict[str, str] = {
        "pause_job": "jm_pause_job",
        "close_job": "jm_close_job",
        "generate_report": "jm_generate_report",
        "get_pipeline_prediction": "jm_pipeline_prediction",
    }

    n = 0
    for td in TOOL_DEFINITIONS:
        _reg.register(
            _G(
                name=_RENAMES.get(td.name, td.name),
                description=td.description,
                parameters_schema=td.parameters,
                handler=td.function,
                allowed_agents=["recruiter_assistant", "orchestrator"],
            )
        )
        n += 1
    return n
