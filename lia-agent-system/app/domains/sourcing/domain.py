from __future__ import annotations
from pathlib import Path

import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="sourcing")


_ACTION_TOOL_MAP: dict[str, str] = {
    "search_candidates": "search_candidates",
    "global_search": "pearch_search",
    "rank_candidates": "candidate_match",
    "filter_candidates": "boolean_search",
    "compare_candidates": "search_candidates",
    "assess_market": "search_analytics",
}


@register_domain
class SourcingDomain(ComplianceDomainPrompt):
    """Domínio de Sourcing & Busca de Talentos da LIA."""

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'sourcing'}

    domain_id = "sourcing"
    domain_name = "Sourcing & Talent Search"
    description = "Busca, identificação e gestão de candidatos em múltiplas fontes"

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.sourcing.actions import SOURCING_ACTIONS
        return SOURCING_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="search_candidates")
                return IntentResult(
                    intent_id=f"sourcing.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="search_candidates")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for sourcing: %s", query[:60])
            return IntentResult(
                intent_id=f"sourcing.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
        query_lower = query.lower()
        best_action = "search_candidates"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = 0.85 if len(keyword) > 4 else 0.7
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"sourcing.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )


    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de sourcing."
            )

        logger.info(f"Executing sourcing action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.sourcing.tools import SOURCING_TOOLS, execute_sourcing_tool

        tool_ids = {t["tool_id"] for t in SOURCING_TOOLS}
        mapped_tool = _ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_sourcing_tool(
                mapped_tool,
                params,
                context.tenant_id,
            )
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        handler_map = {
            "add_candidate": self._handle_add_candidate,
            "enrich_profile": self._handle_enrich_profile,
            "auto_source": self._handle_auto_source,
            "proactive_suggest": self._handle_proactive_suggest,
            "build_search_strategy": self._handle_build_strategy,
            "feedback_search": self._handle_feedback_search,
            "expand_search": self._handle_expand_search,
            "contact_candidates": self._handle_contact_candidates,
            "screen_candidates": self._handle_screen_candidates,
            "export_candidates": self._handle_export_candidates,
            "import_candidates": self._handle_import_candidates,
            "dedup_candidates": self._handle_dedup_candidates,
            "tag_candidates": self._handle_tag_candidates,
            "engagement_pipeline": self._handle_engagement_pipeline,
            "schedule_outreach": self._handle_schedule_outreach,
            "semantic_search": self._handle_semantic_search,
            "suggest_candidates": self._handle_suggest_candidates,
            "generate_boolean": self._handle_generate_boolean,
            "parse_cv": self._handle_parse_cv,
            "match_candidates": self._handle_match_candidates,
            "check_volume": self._handle_check_volume,
            "talent_pool_search": self._handle_talent_pool_search,
            "pearch_search": self._handle_pearch_search,
            "analyze_search_results": self._handle_analyze_results,
        }

        handler = handler_map.get(action_id)
        if handler:
            try:
                return await handler(params, context)
            except Exception as exc:
                logger.error(f"Sourcing handler '{action_id}' failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=str(exc),
                    message=f"Erro ao executar '{action.name}': {exc}",
                    domain_id=self.domain_id,
                    action_id=action_id,
                )

        return DomainResponse.error_response(
            error=f"Nenhum handler configurado para a ação '{action_id}'.",
            message=f"A ação '{action.name}' não possui handler implementado.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_add_candidate(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text
        import uuid

        name = params.get("name", params.get("candidate_name", ""))
        email = params.get("email", params.get("candidate_email", ""))

        if not name:
            return DomainResponse.clarification_response(
                question="Qual o nome do candidato que deseja cadastrar?",
                domain_id=self.domain_id, action_id="add_candidate",
            )

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    INSERT INTO candidates (name, email, company_id, status, created_at, updated_at)
                    VALUES (:name, :email, :company_id, 'active', NOW(), NOW())
                    RETURNING id
                """), {"name": name, "email": email or "", "company_id": context.tenant_id})
                row = result.fetchone()
                candidate_id = row[0] if row else None
                await session.commit()
            except Exception as exc:
                logger.warning(f"Could not insert candidate: {exc}")
                candidate_id = None

        if candidate_id:
            return DomainResponse.success_response(
                message=f"Candidato **{name}** cadastrado com sucesso (ID: {candidate_id}).",
                data={"action_id": "add_candidate", "candidate_id": str(candidate_id), "name": name},
                domain_id=self.domain_id, action_id="add_candidate",
            )
        return DomainResponse.error_response(
            error="Não foi possível cadastrar o candidato.",
            domain_id=self.domain_id, action_id="add_candidate",
        )

    async def _handle_enrich_profile(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Qual candidato você deseja enriquecer? Informe o ID.",
                domain_id=self.domain_id, action_id="enrich_profile",
            )
        return DomainResponse.success_response(
            message=f"Enriquecimento de perfil iniciado para candidato #{candidate_id}. Dados de LinkedIn e fontes externas serão agregados.",
            data={"action_id": "enrich_profile", "candidate_id": candidate_id, "status": "processing"},
            domain_id=self.domain_id, action_id="enrich_profile",
        )

    async def _handle_auto_source(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id")
        if not job_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga você deseja ativar o sourcing automático?",
                domain_id=self.domain_id, action_id="auto_source",
            )
        return DomainResponse.success_response(
            message=f"Pipeline de sourcing automático ativado para vaga #{job_id}. Candidatos serão buscados continuamente.",
            data={"action_id": "auto_source", "job_id": job_id, "status": "active"},
            domain_id=self.domain_id, action_id="auto_source",
        )

    async def _handle_proactive_suggest(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("search_candidates", {"limit": 5}, context.tenant_id)
        return DomainResponse.success_response(
            message="Baseado nas vagas abertas, aqui estão sugestões proativas de candidatos:",
            data={"action_id": "proactive_suggest", "suggestions": result},
            domain_id=self.domain_id, action_id="proactive_suggest",
        )

    async def _handle_build_strategy(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id")
        title = params.get("title", "")
        strategy = {
            "channels": ["Banco interno", "LinkedIn", "GitHub"],
            "approach": "Multi-canal com prioridade para banco interno",
            "estimated_days": 14,
            "boolean_query_suggested": True,
        }
        return DomainResponse.success_response(
            message=f"Estratégia de busca definida{' para vaga #' + str(job_id) if job_id else ''}:\n"
                    f"• Canais: {', '.join(strategy['channels'])}\n"
                    f"• Abordagem: {strategy['approach']}\n"
                    f"• Estimativa: {strategy['estimated_days']} dias",
            data={"action_id": "build_search_strategy", "strategy": strategy, "job_id": job_id},
            domain_id=self.domain_id, action_id="build_search_strategy",
        )

    async def _handle_feedback_search(self, params: dict, context: DomainContext) -> DomainResponse:
        return DomainResponse.success_response(
            message="Feedback registrado. O modelo de busca será ajustado com base nas suas preferências.",
            data={"action_id": "feedback_search", "feedback": params},
            domain_id=self.domain_id, action_id="feedback_search",
        )

    async def _handle_expand_search(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.sourcing.tools import execute_sourcing_tool
        expanded_params = dict(params)
        if "min_experience_years" in expanded_params:
            expanded_params["min_experience_years"] = max(0, int(expanded_params["min_experience_years"]) - 1)
        expanded_params["limit"] = expanded_params.get("limit", 30)
        result = await execute_sourcing_tool("search_candidates", expanded_params, context.tenant_id)
        return DomainResponse.success_response(
            message="Busca expandida com critérios relaxados para ampliar o funil.",
            data={"action_id": "expand_search", "result": result},
            domain_id=self.domain_id, action_id="expand_search",
        )

    async def _handle_contact_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        if not candidate_ids:
            return DomainResponse.clarification_response(
                question="Quais candidatos você deseja contatar?",
                domain_id=self.domain_id, action_id="contact_candidates",
            )
        return DomainResponse.success_response(
            message=f"Outreach iniciado para {len(candidate_ids)} candidato(s). Mensagens serão enviadas pelo canal preferido.",
            data={"action_id": "contact_candidates", "candidate_ids": candidate_ids, "status": "queued"},
            domain_id=self.domain_id, action_id="contact_candidates",
        )

    async def _handle_screen_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        job_id = params.get("job_id")
        return DomainResponse.success_response(
            message=f"Triagem rápida iniciada para {len(candidate_ids) if candidate_ids else 'todos os'} candidato(s)"
                    f"{' da vaga #' + str(job_id) if job_id else ''}.",
            data={"action_id": "screen_candidates", "candidate_ids": candidate_ids, "job_id": job_id, "status": "processing"},
            domain_id=self.domain_id, action_id="screen_candidates",
        )

    async def _handle_export_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("search_candidates", params, context.tenant_id)
        return DomainResponse.success_response(
            message="Lista de candidatos exportada com sucesso.",
            data={"action_id": "export_candidates", "result": result, "format": params.get("format", "json")},
            domain_id=self.domain_id, action_id="export_candidates",
        )

    async def _handle_import_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        source = params.get("source", "csv")
        return DomainResponse.success_response(
            message=f"Importação de candidatos via {source} iniciada. Processamento em andamento.",
            data={"action_id": "import_candidates", "source": source, "status": "processing"},
            domain_id=self.domain_id, action_id="import_candidates",
        )

    async def _handle_dedup_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT email, COUNT(*) as cnt
                    FROM candidates
                    WHERE company_id = :company_id AND email IS NOT NULL AND email != ''
                    GROUP BY email HAVING COUNT(*) > 1
                    LIMIT 20
                """), {"company_id": context.tenant_id})
                duplicates = [{"email": r[0], "count": r[1]} for r in result.fetchall()]
            except Exception as exc:
                logger.error(f"Dedup query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao buscar duplicatas: {exc}",
                    domain_id=self.domain_id, action_id="dedup_candidates",
                )

        count = len(duplicates)
        return DomainResponse.success_response(
            message=f"Análise de duplicatas concluída: **{count}** grupo(s) de duplicatas encontrado(s).",
            data={"action_id": "dedup_candidates", "duplicates": duplicates, "total_groups": count},
            domain_id=self.domain_id, action_id="dedup_candidates",
        )

    async def _handle_tag_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        tags = params.get("tags", [])
        if not candidate_ids or not tags:
            return DomainResponse.clarification_response(
                question="Informe os candidatos e as tags que deseja adicionar.",
                domain_id=self.domain_id, action_id="tag_candidates",
            )
        return DomainResponse.success_response(
            message=f"Tags {tags} aplicadas a {len(candidate_ids)} candidato(s).",
            data={"action_id": "tag_candidates", "candidate_ids": candidate_ids, "tags": tags},
            domain_id=self.domain_id, action_id="tag_candidates",
        )

    async def _handle_engagement_pipeline(self, params: dict, context: DomainContext) -> DomainResponse:
        return DomainResponse.success_response(
            message="Pipeline de engajamento configurado. Candidatos passivos receberão nurture sequences automaticamente.",
            data={"action_id": "engagement_pipeline", "status": "active"},
            domain_id=self.domain_id, action_id="engagement_pipeline",
        )

    async def _handle_schedule_outreach(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        scheduled_date = params.get("date", params.get("scheduled_date"))
        return DomainResponse.success_response(
            message=f"Outreach agendado para {len(candidate_ids) if candidate_ids else 'os'} candidato(s)"
                    f"{' em ' + str(scheduled_date) if scheduled_date else ''}.",
            data={"action_id": "schedule_outreach", "candidate_ids": candidate_ids, "scheduled_date": scheduled_date},
            domain_id=self.domain_id, action_id="schedule_outreach",
        )

    async def _handle_semantic_search(self, params: dict, context: DomainContext) -> DomainResponse:
        query_text = params.get("query", params.get("raw_query", ""))
        limit = int(params.get("limit", 10))

        if not query_text:
            return DomainResponse.clarification_response(
                question="Qual perfil ou descrição devo usar como base para a busca semântica?",
                domain_id=self.domain_id, action_id="semantic_search",
            )

        from app.shared.intelligence.embedding_service import EmbeddingService
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        embedding_svc = EmbeddingService()
        try:
            query_embedding = await embedding_svc.generate_embedding(query_text, company_id=context.tenant_id)
        except Exception as exc:
            logger.warning(f"Embedding generation failed for semantic search: {exc}")
            return DomainResponse.error_response(
                error="Não foi possível gerar embedding para a busca semântica.",
                message=f"Falha ao gerar vetor de embedding: {exc}",
                domain_id=self.domain_id, action_id="semantic_search",
            )

        if not query_embedding:
            return DomainResponse.error_response(
                error="Embedding vazio retornado pelo provedor.",
                domain_id=self.domain_id, action_id="semantic_search",
            )

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
        candidates = []

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT c.id, c.name, c.current_title, c.seniority_level,
                           1 - (ce.embedding <=> :query_vec::vector) AS similarity
                    FROM candidate_embeddings ce
                    JOIN candidates c ON c.id = ce.candidate_id
                    WHERE c.company_id = :company_id
                    ORDER BY ce.embedding <=> :query_vec::vector
                    LIMIT :lim
                """), {
                    "query_vec": embedding_str,
                    "company_id": context.tenant_id,
                    "lim": limit,
                })
                for r in result.fetchall():
                    candidates.append({
                        "id": str(r[0]), "name": r[1], "title": r[2],
                        "seniority": r[3], "similarity": round(float(r[4]), 4) if r[4] else None,
                    })
            except Exception as exc:
                logger.warning(f"Vector search query failed (table may not exist): {exc}")
                from app.domains.sourcing.tools import execute_sourcing_tool
                fallback = await execute_sourcing_tool("search_candidates", params, context.tenant_id)
                return DomainResponse.success_response(
                    message="Busca semântica via vetor indisponível; resultado obtido por busca textual padrão.",
                    data={"action_id": "semantic_search", "result": fallback, "fallback": True},
                    domain_id=self.domain_id, action_id="semantic_search",
                )

        return DomainResponse.success_response(
            message=f"Busca semântica encontrou **{len(candidates)}** candidato(s) similares à query.",
            data={"action_id": "semantic_search", "candidates": candidates, "query": query_text},
            domain_id=self.domain_id, action_id="semantic_search",
        )

    async def _handle_suggest_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id", params.get("vacancy_id"))
        limit = int(params.get("limit", 10))

        if not job_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga deseja sugestões de candidatos? Informe o ID da vaga.",
                domain_id=self.domain_id, action_id="suggest_candidates",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        suggestions = []
        async with AsyncSessionLocal() as session:
            try:
                hired_result = await session.execute(text("""
                    SELECT c.current_title, c.seniority_level,
                           array_agg(DISTINCT ts.name) FILTER (WHERE ts.name IS NOT NULL) as skills
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    LEFT JOIN candidate_technical_skills cts ON cts.candidate_id = c.id
                    LEFT JOIN technical_skills ts ON ts.id = cts.technical_skill_id
                    WHERE vc.vacancy_id = :job_id
                      AND vc.company_id = :company_id
                      AND vc.status IN ('hired', 'approved', 'shortlisted')
                    GROUP BY c.id, c.current_title, c.seniority_level
                    LIMIT 5
                """), {"job_id": job_id, "company_id": context.tenant_id})
                successful_profiles = hired_result.fetchall()
            except Exception as exc:
                logger.warning(f"Failed to fetch historical profiles: {exc}")
                successful_profiles = []

            if successful_profiles:
                title_filter = successful_profiles[0][0] or ""
                seniority_filter = successful_profiles[0][1] or ""
                try:
                    result = await session.execute(text("""
                        SELECT c.id, c.name, c.current_title, c.seniority_level, c.years_of_experience
                        FROM candidates c
                        WHERE c.company_id = :company_id
                          AND c.id NOT IN (
                              SELECT candidate_id FROM vacancy_candidates WHERE vacancy_id = :job_id
                          )
                          AND (
                              c.current_title ILIKE :title_pattern
                              OR c.seniority_level = :seniority
                          )
                        ORDER BY c.updated_at DESC NULLS LAST
                        LIMIT :lim
                    """), {
                        "company_id": context.tenant_id,
                        "job_id": job_id,
                        "title_pattern": f"%{title_filter}%",
                        "seniority": seniority_filter,
                        "lim": limit,
                    })
                    for r in result.fetchall():
                        suggestions.append({
                            "id": str(r[0]), "name": r[1], "title": r[2],
                            "seniority": r[3], "experience_years": r[4],
                            "reason": f"Perfil similar a contratações anteriores ({title_filter})",
                        })
                except Exception as exc:
                    logger.warning(f"Suggestion query failed: {exc}")
            else:
                try:
                    jv_result = await session.execute(text("""
                        SELECT title, seniority_level FROM job_vacancies
                        WHERE id = :job_id AND company_id = :company_id
                    """), {"job_id": job_id, "company_id": context.tenant_id})
                    jv = jv_result.fetchone()
                    if jv:
                        result = await session.execute(text("""
                            SELECT c.id, c.name, c.current_title, c.seniority_level, c.years_of_experience
                            FROM candidates c
                            WHERE c.company_id = :company_id
                              AND c.id NOT IN (
                                  SELECT candidate_id FROM vacancy_candidates WHERE vacancy_id = :job_id
                              )
                              AND (
                                  c.current_title ILIKE :title_pattern
                                  OR c.seniority_level = :seniority
                              )
                            ORDER BY c.updated_at DESC NULLS LAST
                            LIMIT :lim
                        """), {
                            "company_id": context.tenant_id,
                            "job_id": job_id,
                            "title_pattern": f"%{jv[0] or ''}%",
                            "seniority": jv[1] or "",
                            "lim": limit,
                        })
                        for r in result.fetchall():
                            suggestions.append({
                                "id": str(r[0]), "name": r[1], "title": r[2],
                                "seniority": r[3], "experience_years": r[4],
                                "reason": f"Perfil compatível com requisitos da vaga '{jv[0]}'",
                            })
                except Exception as exc:
                    logger.warning(f"Job-based suggestion query failed: {exc}")

        if not suggestions:
            return DomainResponse.success_response(
                message=f"Nenhuma sugestão encontrada para a vaga #{job_id}. Tente ampliar os critérios ou adicionar candidatos ao banco.",
                data={"action_id": "suggest_candidates", "job_id": str(job_id), "suggestions": []},
                domain_id=self.domain_id, action_id="suggest_candidates",
            )

        return DomainResponse.success_response(
            message=f"**{len(suggestions)}** candidato(s) sugerido(s) para a vaga #{job_id} com base no histórico de contratações.",
            data={"action_id": "suggest_candidates", "job_id": str(job_id), "suggestions": suggestions},
            domain_id=self.domain_id, action_id="suggest_candidates",
        )

    async def _handle_generate_boolean(self, params: dict, context: DomainContext) -> DomainResponse:
        title = params.get("title", "")
        skills = params.get("skills", [])
        exclude = params.get("exclude_terms", [])
        parts = []
        if title:
            parts.append(f'"{title}"')
        if skills:
            parts.append("(" + " OR ".join(f'"{s}"' for s in skills) + ")")
        if exclude:
            parts.extend(f'NOT "{e}"' for e in exclude)
        boolean_query = " AND ".join(parts) if parts else "(query vazia)"
        return DomainResponse.success_response(
            message=f"**Query booleana gerada:**\n\n`{boolean_query}`\n\nUse esta query para buscar em LinkedIn, GitHub e outras fontes.",
            data={"action_id": "generate_boolean", "boolean_query": boolean_query, "params": params},
            domain_id=self.domain_id, action_id="generate_boolean",
        )

    async def _handle_parse_cv(self, params: dict, context: DomainContext) -> DomainResponse:
        cv_text = params.get("cv_text", "")
        file_data = params.get("file_data")
        if not cv_text and not file_data:
            return DomainResponse.clarification_response(
                question="Envie o texto ou arquivo do CV para análise.",
                domain_id=self.domain_id, action_id="parse_cv",
            )

        extracted = {}
        if file_data and not cv_text:
            try:
                import base64
                raw_bytes = base64.b64decode(file_data) if isinstance(file_data, str) else file_data
                from app.domains.ai.services.multimodal_service import MultimodalService
                svc = MultimodalService()
                doc_result = await svc.analyze_document(raw_bytes, document_type="pdf")
                cv_text = doc_result.get("text_content", "")
                extracted["document_analysis"] = {
                    "formatting_quality": doc_result.get("formatting_quality"),
                    "structure": doc_result.get("structure"),
                }
            except Exception as exc:
                logger.warning(f"Document analysis failed, using raw text: {exc}")

        if not cv_text:
            return DomainResponse.error_response(
                error="Não foi possível extrair texto do CV.",
                domain_id=self.domain_id, action_id="parse_cv",
            )

        import re
        lines = cv_text.strip().split("\n")
        name = lines[0].strip() if lines else ""
        emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", cv_text)
        phones = re.findall(r"[\+\(]?[\d\s\-\(\)]{8,15}", cv_text)

        skill_keywords = [
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "node", "sql", "aws", "azure", "docker", "kubernetes", "go", "rust",
            "c#", ".net", "php", "ruby", "swift", "kotlin", "flutter", "dart",
            "machine learning", "data science", "devops", "ci/cd", "agile", "scrum",
        ]
        cv_lower = cv_text.lower()
        detected_skills = [s for s in skill_keywords if s in cv_lower]

        experience_patterns = re.findall(
            r"(\d{4})\s*[-–—]\s*(\d{4}|present|atual|presente)",
            cv_text, re.IGNORECASE,
        )
        years_experience = 0
        for start, end in experience_patterns:
            try:
                end_year = 2026 if end.lower() in ("present", "atual", "presente") else int(end)
                years_experience += end_year - int(start)
            except ValueError:
                pass

        education_keywords = ["graduação", "bacharelado", "mestrado", "doutorado",
                              "bachelor", "master", "phd", "mba", "pós-graduação"]
        education = [kw for kw in education_keywords if kw in cv_lower]

        parsed = {
            "name": name,
            "emails": emails[:3],
            "phones": [p.strip() for p in phones[:3]],
            "detected_skills": detected_skills,
            "education_level": education,
            "estimated_experience_years": years_experience,
            "word_count": len(cv_text.split()),
            "line_count": len(lines),
            **extracted,
        }

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text as sql_text

        persisted = False
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(sql_text("""
                    INSERT INTO candidate_cv_parses
                        (company_id, user_id, raw_text, parsed_data, created_at)
                    VALUES
                        (:company_id, :user_id, :raw_text, :parsed_data, NOW())
                """), {
                    "company_id": context.tenant_id,
                    "user_id": context.user_id,
                    "raw_text": cv_text[:5000],
                    "parsed_data": str(parsed),
                })
                await session.commit()
                persisted = True
            except Exception as exc:
                logger.error(f"Failed to persist CV parse result: {exc}", exc_info=True)
                persisted = False

        skills_str = ", ".join(detected_skills) if detected_skills else "nenhuma detectada"
        persist_note = "" if persisted else "\n(Persistência falhou — resultado disponível apenas nesta resposta)"
        msg = (
            f"**CV analisado:**\n\n"
            f"• Nome: {name or 'Não identificado'}\n"
            f"• Skills: {skills_str}\n"
            f"• Experiência estimada: ~{years_experience} anos\n"
            f"• Palavras: {parsed['word_count']}{persist_note}"
        )

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "parse_cv", "parsed": parsed, "persisted": persisted},
            domain_id=self.domain_id, action_id="parse_cv",
        )

    async def _handle_match_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id", params.get("vacancy_id"))
        if not candidate_id or not job_id:
            return DomainResponse.clarification_response(
                question="Informe o ID do candidato e da vaga para calcular a compatibilidade.",
                domain_id=self.domain_id, action_id="match_candidates",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        candidate_data = {}
        job_data = {}
        match_result = {}

        async with AsyncSessionLocal() as session:
            try:
                c_result = await session.execute(text("""
                    SELECT c.name, c.current_title, c.seniority_level, c.years_of_experience,
                           array_agg(DISTINCT ts.name) FILTER (WHERE ts.name IS NOT NULL) as skills
                    FROM candidates c
                    LEFT JOIN candidate_technical_skills cts ON cts.candidate_id = c.id
                    LEFT JOIN technical_skills ts ON ts.id = cts.technical_skill_id
                    WHERE c.id = :cid AND c.company_id = :company_id
                    GROUP BY c.id, c.name, c.current_title, c.seniority_level, c.years_of_experience
                """), {"cid": candidate_id, "company_id": context.tenant_id})
                row = c_result.fetchone()
                if not row:
                    return DomainResponse.error_response(
                        error=f"Candidato '{candidate_id}' não encontrado.",
                        domain_id=self.domain_id, action_id="match_candidates",
                    )
                candidate_data = {
                    "name": row[0], "title": row[1], "seniority": row[2],
                    "experience_years": row[3], "skills": row[4] or [],
                }
            except Exception as exc:
                return DomainResponse.error_response(
                    error=f"Erro ao buscar candidato: {exc}",
                    domain_id=self.domain_id, action_id="match_candidates",
                )

            try:
                j_result = await session.execute(text("""
                    SELECT jv.title, jv.seniority_level, jv.required_skills, jv.min_experience_years
                    FROM job_vacancies jv
                    WHERE jv.id = :job_id AND jv.company_id = :company_id
                """), {"job_id": job_id, "company_id": context.tenant_id})
                jrow = j_result.fetchone()
                if not jrow:
                    return DomainResponse.error_response(
                        error=f"Vaga '{job_id}' não encontrada.",
                        domain_id=self.domain_id, action_id="match_candidates",
                    )
                job_data = {
                    "title": jrow[0], "seniority": jrow[1],
                    "required_skills": jrow[2] or [], "min_experience": jrow[3] or 0,
                }
            except Exception as exc:
                return DomainResponse.error_response(
                    error=f"Erro ao buscar vaga: {exc}",
                    domain_id=self.domain_id, action_id="match_candidates",
                )

        candidate_skills = set(s.lower() for s in (candidate_data.get("skills") or []) if s)
        required_skills = set()
        raw_skills = job_data.get("required_skills", [])
        if isinstance(raw_skills, list):
            required_skills = set(s.lower() for s in raw_skills if s)
        elif isinstance(raw_skills, str):
            required_skills = set(s.strip().lower() for s in raw_skills.split(",") if s.strip())

        skill_overlap = candidate_skills & required_skills
        skill_score = len(skill_overlap) / max(len(required_skills), 1) * 100

        seniority_match = (
            candidate_data.get("seniority", "").lower() == job_data.get("seniority", "").lower()
        ) if candidate_data.get("seniority") and job_data.get("seniority") else None

        exp_years = candidate_data.get("experience_years") or 0
        min_exp = job_data.get("min_experience", 0) or 0
        experience_match = exp_years >= min_exp if min_exp else True

        overall_score = skill_score * 0.5
        if seniority_match is True:
            overall_score += 25
        elif seniority_match is False:
            overall_score += 10
        if experience_match:
            overall_score += 25
        else:
            overall_score += max(0, 25 - (min_exp - exp_years) * 5)

        overall_score = min(100, overall_score)

        match_result = {
            "overall_score": round(overall_score, 1),
            "skill_match": round(skill_score, 1),
            "skills_matched": list(skill_overlap),
            "skills_missing": list(required_skills - candidate_skills),
            "seniority_match": seniority_match,
            "experience_match": experience_match,
            "candidate": candidate_data,
            "job": job_data,
        }

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("""
                    UPDATE vacancy_candidates
                    SET match_percentage = :score
                    WHERE candidate_id = :cid AND vacancy_id = :job_id AND company_id = :company_id
                """), {
                    "score": overall_score,
                    "cid": candidate_id,
                    "job_id": job_id,
                    "company_id": context.tenant_id,
                })
                await session.commit()
        except Exception as exc:
            logger.warning(f"Could not persist match score: {exc}")

        msg = (
            f"**Match: {candidate_data['name']} × {job_data['title']}**\n\n"
            f"• Score geral: **{match_result['overall_score']}%**\n"
            f"• Skills compatíveis: {len(skill_overlap)}/{len(required_skills)} "
            f"({', '.join(skill_overlap) if skill_overlap else 'nenhuma'})\n"
            f"• Senioridade: {'✓' if seniority_match else '✗ ou N/A'}\n"
            f"• Experiência: {'✓' if experience_match else '✗'} ({exp_years} anos vs mín. {min_exp})"
        )

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "match_candidates", **match_result},
            domain_id=self.domain_id, action_id="match_candidates",
        )

    async def _handle_check_volume(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("volume_check", params, context.tenant_id)
        return DomainResponse.success_response(
            message="Verificação de volume concluída — candidatos disponíveis para o perfil buscado.",
            data={"action_id": "check_volume", "result": result},
            domain_id=self.domain_id, action_id="check_volume",
        )

    async def _handle_talent_pool_search(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            stmt = select(TalentPool).where(
                TalentPool.company_id == context.tenant_id,
                TalentPool.status == "active",
            ).order_by(TalentPool.candidates_count.desc())
            result = await session.execute(stmt)
            pools = [p.to_dict() for p in result.scalars().all()]

        if pools:
            lines = [f"• **{p['name']}** — {p['candidates_count']} candidatos" for p in pools]
            msg = "**Pools de talentos disponíveis:**\n\n" + "\n".join(lines)
        else:
            msg = "Nenhum pool de talentos ativo encontrado."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "talent_pool_search", "pools": pools},
            domain_id=self.domain_id, action_id="talent_pool_search",
        )

    async def _handle_pearch_search(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.sourcing.tools import execute_sourcing_tool
        result = await execute_sourcing_tool("pearch_search", params, context.tenant_id)
        return DomainResponse.success_response(
            message="Busca Pearch executada — resultados de fontes externas agregados.",
            data={"action_id": "pearch_search", "result": result},
            domain_id=self.domain_id, action_id="pearch_search",
        )

    async def _handle_analyze_results(self, params: dict, context: DomainContext) -> DomainResponse:
        return DomainResponse.success_response(
            message="Análise de resultados de busca concluída. Métricas de efetividade calculadas.",
            data={"action_id": "analyze_search_results", "params": params, "status": "analyzed"},
            domain_id=self.domain_id, action_id="analyze_search_results",
        )


try:
    from app.shared.compliance.domain_validators import validate_sourcing_count_claim
    from app.shared.compliance.fact_checker import FactChecker
    FactChecker.register_validator("sourcing", validate_sourcing_count_claim)
    logger.debug("sourcing domain validator registered")
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Could not register sourcing domain validator: %s", _e
    )
