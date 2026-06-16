from pathlib import Path
"""Talent Pool Domain - Live talent banks management."""
import logging
import yaml as _yaml_imp  # Fase 5
import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="talent_pool")

@register_domain
class TalentPoolDomain(ComplianceDomainPrompt):
    domain_id = "talent_pool"
    domain_name = "Talent Pool Management"
    description = "Gestão de bancos de talentos vivos — criar, listar, adicionar candidatos, migrar para vagas"
    _compliance_config = {"high_impact": True, "fairness_action_type": "sourcing"}

    def get_allowed_actions(self):
        from app.domains.talent_pool.actions import TALENT_POOL_ACTIONS
        return TALENT_POOL_ACTIONS

    async def process_intent(self, query, context):
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="list_talent_pools")
                return IntentResult(
                    intent_id=f"talent_pool.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="list_talent_pools")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for talent_pool: %s", query[:60])
            return IntentResult(
                intent_id=f"talent_pool.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            q = query.lower()
            best_action, best_conf = "list_talent_pools", 0.3
            for kw, action in _KEYWORD_ACTION_MAP.items():
                if kw in q:
                    conf = 0.9 if len(kw) > 6 else 0.75
                    if conf > best_conf:
                        best_action, best_conf = action, conf
            return IntentResult(intent_id=f"talent_pool.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")

        handler_map = {
            "create_talent_pool": self._handle_create_pool,
            "list_talent_pools": self._handle_list_pools,
            "add_to_pool": self._handle_add_to_pool,
            "move_pool_to_job": self._handle_move_to_job,
            "get_pool_candidates": self._handle_get_candidates,
            "create_job_from_pool": self._handle_create_job_from_pool,
        }

        handler = handler_map.get(action_id)
        if not handler:
            return DomainResponse.error_response(error=f"No handler for action '{action_id}'")

        try:
            return await handler(params, context)
        except Exception as exc:
            logger.error(f"Talent pool action '{action_id}' failed: {exc}", exc_info=True)
            return DomainResponse.error_response(
                error=str(exc),
                message=f"Erro ao executar '{action.name}': {exc}",
                domain_id=self.domain_id,
                action_id=action_id,
            )

    async def _handle_create_pool(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool

        name = params.get("name")
        if not name:
            return DomainResponse.clarification_response(
                question="Qual nome você gostaria de dar ao novo banco de talentos?",
                domain_id=self.domain_id,
                action_id="create_talent_pool",
            )

        async with AsyncSessionLocal() as session:
            pool = TalentPool(
                id=uuid.uuid4(),
                company_id=context.tenant_id,
                name=name,
                description=params.get("description", ""),
                archetype_id=params.get("archetype_id"),
                status="active",
            )
            session.add(pool)
            await session.commit()
            await session.refresh(pool)
            pool_data = pool.to_dict()

        return DomainResponse.success_response(
            message=f"Banco de talentos **{name}** criado com sucesso!",
            data={"action_id": "create_talent_pool", "pool": pool_data},
            domain_id=self.domain_id,
            action_id="create_talent_pool",
        )

    async def _handle_list_pools(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool
        from sqlalchemy import select

        status_filter = params.get("status", "active")

        async with AsyncSessionLocal() as session:
            stmt = select(TalentPool).where(TalentPool.company_id == context.tenant_id)
            if status_filter:
                stmt = stmt.where(TalentPool.status == status_filter)
            stmt = stmt.order_by(TalentPool.created_at.desc())
            result = await session.execute(stmt)
            pools = [p.to_dict() for p in result.scalars().all()]

        if not pools:
            return DomainResponse.success_response(
                message="Você ainda não tem bancos de talentos. Deseja criar um?",
                data={"action_id": "list_talent_pools", "pools": [], "total": 0},
                domain_id=self.domain_id,
                action_id="list_talent_pools",
                suggestions=["Criar banco de talentos"],
            )

        pool_lines = []
        for p in pools:
            pool_lines.append(f"• **{p['name']}** — {p['candidates_count']} candidatos ({p['status']})")
        summary = "\n".join(pool_lines)

        return DomainResponse.success_response(
            message=f"Você tem **{len(pools)}** banco(s) de talentos:\n\n{summary}",
            data={"action_id": "list_talent_pools", "pools": pools, "total": len(pools)},
            domain_id=self.domain_id,
            action_id="list_talent_pools",
        )

    async def _handle_add_to_pool(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool, TalentPoolCandidate
        from sqlalchemy import select, text

        pool_id = params.get("pool_id")
        candidate_ids = params.get("candidate_ids", [])

        if not pool_id:
            return DomainResponse.clarification_response(
                question="Em qual banco de talentos você deseja adicionar os candidatos? Informe o ID ou nome do pool.",
                domain_id=self.domain_id,
                action_id="add_to_pool",
            )
        if not candidate_ids:
            return DomainResponse.clarification_response(
                question="Quais candidatos você deseja adicionar ao pool? Informe os IDs.",
                domain_id=self.domain_id,
                action_id="add_to_pool",
            )

        origin = params.get("origin", "manual")
        added = 0
        skipped = 0

        async with AsyncSessionLocal() as session:
            pool = await session.get(TalentPool, pool_id)
            if not pool or pool.company_id != context.tenant_id:
                return DomainResponse.error_response(
                    error=f"Banco de talentos '{pool_id}' não encontrado.",
                    domain_id=self.domain_id,
                    action_id="add_to_pool",
                )

            for cid in candidate_ids:
                numeric_cid = None
                resolved_uuid = None

                try:
                    candidate_uuid_obj = uuid.UUID(str(cid))
                    resolved_uuid = candidate_uuid_obj
                    ownership_check = await session.execute(text(
                        "SELECT id FROM candidates WHERE id = :cid AND company_id = :tenant"
                    ), {"cid": str(resolved_uuid), "tenant": context.tenant_id})
                    if not ownership_check.scalar_one_or_none():
                        logger.warning(f"UUID candidate '{cid}' not found or not owned by tenant")
                        skipped += 1
                        continue
                    numeric_cid = candidate_uuid_obj.int % (2**63)
                except (ValueError, AttributeError):
                    try:
                        numeric_cid = int(cid)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid candidate_id '{cid}': not integer or UUID")
                        skipped += 1
                        continue

                    int_ownership = await session.execute(text(
                        "SELECT id FROM candidate_sources WHERE source_profile_id = :sid AND candidate_id IN (SELECT id FROM candidates WHERE company_id = :tenant)"
                    ), {"sid": str(numeric_cid), "tenant": context.tenant_id})
                    if not int_ownership.first():
                        logger.warning(f"Integer candidate_id '{cid}' not found in tenant sources")
                        skipped += 1
                        continue

                if resolved_uuid:
                    existing = await session.execute(
                        select(TalentPoolCandidate).where(
                            TalentPoolCandidate.talent_pool_id == pool.id,
                            TalentPoolCandidate.candidate_uuid == resolved_uuid,
                        )
                    )
                else:
                    existing = await session.execute(
                        select(TalentPoolCandidate).where(
                            TalentPoolCandidate.talent_pool_id == pool.id,
                            TalentPoolCandidate.candidate_id == numeric_cid,
                        )
                    )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                tpc = TalentPoolCandidate(
                    id=uuid.uuid4(),
                    talent_pool_id=pool.id,
                    candidate_id=numeric_cid,
                    candidate_uuid=resolved_uuid,
                    stage="discovered",
                    origin=origin,
                )
                session.add(tpc)
                added += 1

            pool.candidates_count = (pool.candidates_count or 0) + added
            await session.commit()

        msg = f"**{added}** candidato(s) adicionado(s) ao pool **{pool.name}**."
        if skipped:
            msg += f" {skipped} já estavam no pool."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "add_to_pool", "added": added, "skipped": skipped, "pool_id": str(pool_id)},
            domain_id=self.domain_id,
            action_id="add_to_pool",
        )

    async def _handle_move_to_job(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool, TalentPoolCandidate
        from sqlalchemy import select, text
        

        pool_id = params.get("pool_id")
        job_id = params.get("job_id")
        candidate_ids = params.get("candidate_ids", [])
        target_stage = params.get("target_stage", "Novo")

        if not pool_id or not job_id:
            return DomainResponse.clarification_response(
                question="Preciso do ID do pool e da vaga destino para mover os candidatos.",
                domain_id=self.domain_id,
                action_id="move_pool_to_job",
            )

        moved = 0
        pipeline_created = 0
        now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as session:
            pool = await session.get(TalentPool, pool_id)
            if not pool or pool.company_id != context.tenant_id:
                return DomainResponse.error_response(
                    error=f"Pool '{pool_id}' não encontrado.",
                    domain_id=self.domain_id,
                    action_id="move_pool_to_job",
                )

            vacancy_uuid = None
            try:
                vacancy_uuid = uuid.UUID(str(job_id))
            except (ValueError, AttributeError):
                pass

            numeric_job_id = None
            if not vacancy_uuid:
                try:
                    numeric_job_id = int(job_id)
                except (ValueError, TypeError):
                    return DomainResponse.error_response(
                        error=f"job_id '{job_id}' inválido: não é UUID nem inteiro.",
                        domain_id=self.domain_id, action_id="move_pool_to_job",
                    )

            job_check = await session.execute(text(
                "SELECT id FROM job_vacancies WHERE id = :jid AND company_id = :tenant"
            ), {"jid": str(job_id), "tenant": context.tenant_id})
            if not job_check.scalar_one_or_none():
                return DomainResponse.error_response(
                    error=f"Vaga '{job_id}' não encontrada ou não pertence à sua empresa.",
                    domain_id=self.domain_id, action_id="move_pool_to_job",
                )

            if candidate_ids:
                pool_candidates = []
                for cid in candidate_ids:
                    try:
                        cid_uuid = uuid.UUID(str(cid))
                        result = await session.execute(
                            select(TalentPoolCandidate).where(
                                TalentPoolCandidate.talent_pool_id == pool.id,
                                TalentPoolCandidate.candidate_uuid == cid_uuid,
                            )
                        )
                    except (ValueError, AttributeError):
                        try:
                            cid_int = int(cid)
                        except (ValueError, TypeError):
                            continue
                        result = await session.execute(
                            select(TalentPoolCandidate).where(
                                TalentPoolCandidate.talent_pool_id == pool.id,
                                TalentPoolCandidate.candidate_id == cid_int,
                            )
                        )
                    tpc = result.scalar_one_or_none()
                    if tpc and not tpc.moved_to_job_uuid and not tpc.moved_to_job_id:
                        pool_candidates.append(tpc)
            else:
                result = await session.execute(
                    select(TalentPoolCandidate).where(
                        TalentPoolCandidate.talent_pool_id == pool.id,
                        TalentPoolCandidate.moved_to_job_uuid.is_(None),
                        TalentPoolCandidate.moved_to_job_id.is_(None),
                    )
                )
                pool_candidates = list(result.scalars().all())

            skipped_candidates = 0
            for tpc in pool_candidates:
                candidate_uuid = tpc.candidate_uuid
                if not candidate_uuid:
                    candidate_uuid = await self._resolve_candidate_uuid(
                        session, tpc.candidate_id, context.tenant_id
                    )

                if not candidate_uuid:
                    logger.warning(
                        f"Could not resolve candidate UUID for pool candidate_id={tpc.candidate_id}; skipping"
                    )
                    skipped_candidates += 1
                    continue

                if vacancy_uuid:
                    existing = await session.execute(text(
                        "SELECT id FROM vacancy_candidates WHERE vacancy_id = :vid AND candidate_id = :cid"
                    ), {"vid": vacancy_uuid, "cid": candidate_uuid})
                    if not existing.scalar_one_or_none():
                        await session.execute(text("""
                            INSERT INTO vacancy_candidates
                                (id, vacancy_id, candidate_id, company_id, source, origin, status, stage, added_by, notes, created_at, updated_at)
                            VALUES
                                (:id, :vid, :cid, :company_id, 'talent_pool', 'pool_transfer', 'sourced', :stage, :added_by, :notes, :now, :now)
                        """), {
                            "id": uuid.uuid4(),
                            "vid": vacancy_uuid,
                            "cid": candidate_uuid,
                            "company_id": context.tenant_id,
                            "stage": target_stage,
                            "added_by": context.user_id,
                            "notes": f"Transferido do pool '{pool.name}' (ID: {pool_id})",
                            "now": now,
                        })
                        pipeline_created += 1

                if vacancy_uuid:
                    tpc.moved_to_job_uuid = vacancy_uuid
                if numeric_job_id is not None:
                    tpc.moved_to_job_id = numeric_job_id
                tpc.moved_at = now
                tpc.moved_to_stage = target_stage
                moved += 1

            await session.commit()

        msg = f"**{moved}** candidato(s) movido(s) do pool **{pool.name}** para a vaga #{job_id} na etapa '{target_stage}'."
        if pipeline_created:
            msg += f" {pipeline_created} registro(s) de pipeline criado(s)."
        if skipped_candidates:
            msg += f" {skipped_candidates} candidato(s) não puderam ser vinculados (UUID não resolvido)."

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "move_pool_to_job", "moved": moved,
                "pipeline_records_created": pipeline_created,
                "skipped": skipped_candidates,
                "pool_id": str(pool_id), "job_id": str(job_id),
            },
            domain_id=self.domain_id,
            action_id="move_pool_to_job",
        )

    async def _resolve_candidate_uuid(self, session, pool_candidate_id: int, tenant_id: str):
        """Resolve a TalentPoolCandidate BigInteger candidate_id to a UUID from the candidates table.

        Resolution order:
        1. Try direct UUID parse (handles cases where numeric ID is actually a UUID string)
        2. Look up via candidate_sources.source_profile_id matching the numeric ID
        3. Return None if no mapping found
        """
        from sqlalchemy import text as _text
        str_id = str(pool_candidate_id)
        try:
            return uuid.UUID(str_id)
        except (ValueError, AttributeError):
            pass

        row = (await session.execute(_text(
            "SELECT cs.candidate_id FROM candidate_sources cs "
            "JOIN candidates c ON c.id = cs.candidate_id "
            "WHERE cs.source_profile_id = :sid AND c.company_id = :tenant_id LIMIT 1"
        ), {"sid": str_id, "tenant_id": tenant_id})).fetchone()
        if row:
            return row[0]

        return None

    async def _handle_get_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool, TalentPoolCandidate
        from sqlalchemy import select

        pool_id = params.get("pool_id")
        if not pool_id:
            return DomainResponse.clarification_response(
                question="De qual banco de talentos você quer ver os candidatos?",
                domain_id=self.domain_id,
                action_id="get_pool_candidates",
            )

        stage_filter = params.get("stage")
        limit = int(params.get("limit", 50))

        async with AsyncSessionLocal() as session:
            pool = await session.get(TalentPool, pool_id)
            if not pool or pool.company_id != context.tenant_id:
                return DomainResponse.error_response(
                    error=f"Pool '{pool_id}' não encontrado.",
                    domain_id=self.domain_id,
                    action_id="get_pool_candidates",
                )

            stmt = select(TalentPoolCandidate).where(
                TalentPoolCandidate.talent_pool_id == pool.id
            )
            if stage_filter:
                stmt = stmt.where(TalentPoolCandidate.stage == stage_filter)
            stmt = stmt.order_by(TalentPoolCandidate.created_at.desc()).limit(limit)

            result = await session.execute(stmt)
            candidates = [c.to_dict() for c in result.scalars().all()]

        stage_counts = {}
        for c in candidates:
            s = c.get("stage", "unknown")
            stage_counts[s] = stage_counts.get(s, 0) + 1

        stage_summary = ", ".join(f"{s}: {n}" for s, n in stage_counts.items())
        msg = f"Pool **{pool.name}** — {len(candidates)} candidato(s) encontrado(s)."
        if stage_summary:
            msg += f"\nDistribuição: {stage_summary}"

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "get_pool_candidates",
                "pool_id": str(pool_id),
                "pool_name": pool.name,
                "candidates": candidates,
                "total": len(candidates),
                "stage_counts": stage_counts,
            },
            domain_id=self.domain_id,
            action_id="get_pool_candidates",
        )

    async def _handle_create_job_from_pool(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from lia_models.talent_pool import TalentPool
        from sqlalchemy import select, text

        pool_id = params.get("pool_id")
        if not pool_id:
            return DomainResponse.clarification_response(
                question="De qual banco de talentos você quer criar uma vaga?",
                domain_id=self.domain_id,
                action_id="create_job_from_pool",
            )

        async with AsyncSessionLocal() as session:
            pool = await session.get(TalentPool, pool_id)
            if not pool or pool.company_id != context.tenant_id:
                return DomainResponse.error_response(
                    error=f"Pool '{pool_id}' não encontrado.",
                    domain_id=self.domain_id,
                    action_id="create_job_from_pool",
                )

            job_data = {
                "title": f"Vaga a partir do pool: {pool.name}",
                "archetype_id": pool.archetype_id,
                "source_pool_id": str(pool.id),
                "company_id": context.tenant_id,
                "status": "Rascunho",
            }

            import json
            pool_description = json.dumps({
                "source": "talent_pool",
                "pool_id": str(pool.id),
                "pool_name": pool.name,
                "archetype_id": pool.archetype_id,
            })

            try:
                result = await session.execute(text("""
                    INSERT INTO job_vacancies (company_id, title, description, status, created_at, updated_at)
                    VALUES (:company_id, :title, :description, :status, NOW(), NOW())
                    RETURNING id
                """), {
                    "company_id": context.tenant_id,
                    "title": job_data["title"],
                    "description": pool_description,
                    "status": "Rascunho",
                })
                row = result.fetchone()
                job_id = row[0] if row else None
                await session.commit()
            except Exception as exc:
                logger.error(f"Failed to insert job_vacancy from pool: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao criar vaga a partir do pool: {exc}",
                    domain_id=self.domain_id,
                    action_id="create_job_from_pool",
                )

        archetype_note = f" Arquétipo '{pool.archetype_id}' vinculado." if pool.archetype_id else ""
        return DomainResponse.success_response(
            message=f"Vaga **#{job_id}** criada a partir do pool **{pool.name}** com status 'Rascunho'.{archetype_note} Dados do pool foram registrados na descrição da vaga.",
            data={
                "action_id": "create_job_from_pool", "job_id": str(job_id),
                "pool_name": pool.name, "pool_id": str(pool_id),
                "archetype_id": pool.archetype_id,
            },
            domain_id=self.domain_id,
            action_id="create_job_from_pool",
        )
