from pathlib import Path
"""Digital Twin Domain - RAG few-shot evaluation using SME reasoning."""
import logging
import yaml as _yaml_imp  # Fase 5
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

# LIA-I03: Shared KeywordIntentMatcher singleton
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="digital_twin")

@register_domain
class DigitalTwinDomain(ComplianceDomainPrompt):
    domain_id = "digital_twin"
    domain_name = "Digital Twins"
    description = "Clone de raciocínio de especialistas via RAG few-shot para avaliação de candidatos"
    _compliance_config = {"high_impact": True, "fairness_action_type": "screening"}

    def get_allowed_actions(self):
        from app.domains.digital_twin.actions import DIGITAL_TWIN_ACTIONS
        return DIGITAL_TWIN_ACTIONS

    async def process_intent(self, query, context):
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="list_twins")
                return IntentResult(
                    intent_id=f"digital_twin.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="list_twins")
            return IntentResult(intent_id=f"digital_twin.{match.action}", action_id=match.action, confidence=match.confidence, extracted_params={"raw_query": query}, reasoning=f"KeywordIntentMatcher matched '{match.action}'")
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            q = query.lower()
            best_action, best_conf = "list_twins", 0.3
            for kw, action in _KEYWORD_ACTION_MAP.items():
                if kw in q:
                    conf = 0.9 if len(kw) > 6 else 0.75
                    if conf > best_conf:
                        best_action, best_conf = action, conf
            return IntentResult(intent_id=f"digital_twin.{best_action}", action_id=best_action, confidence=best_conf, extracted_params={"raw_query": query}, reasoning=f"Keyword matched '{best_action}'")

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(error=f"Action '{action_id}' not found")

        if action_id == "create_twin":
            return await self._handle_create_twin(params, context)
        if action_id == "evaluate_with_twin":
            return await self._handle_evaluate_with_twin(params, context)
        if action_id == "list_twins":
            return await self._handle_list_twins(params, context)
        if action_id == "index_twin_audio":
            return await self._handle_index_twin_audio(params, context)
        if action_id == "deactivate_twin":
            return await self._handle_deactivate_twin(params, context)

        return DomainResponse.error_response(error=f"Action '{action_id}' not implemented")

    async def _handle_create_twin(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        twin_name = params.get("twin_name", "").strip()
        if not twin_name:
            return DomainResponse.clarification_response(
                question="Qual nome você quer dar ao Digital Twin?",
                options=["Twin Engenharia", "Twin Produto", "Twin Comercial"],
                domain_id=self.domain_id,
                action_id="create_twin",
            )

        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id

            sme_user_id = params.get("sme_user_id")
            specialties = params.get("specialties", [])
            if isinstance(specialties, str):
                specialties = [s.strip() for s in specialties.split(",")]

            from lia_models.digital_twin import DigitalTwin
            import uuid

            async for db in get_db():
                allowed, msg = await studio_metering_service.check_and_increment_quota(db, company_id, "digital_twin")
                if not allowed:
                    return DomainResponse.error_response(error=msg, domain_id=self.domain_id, action_id="create_twin")

                twin = DigitalTwin(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    twin_name=twin_name,
                    sme_user_id=sme_user_id,
                    specialties=specialties,
                    description=params.get("description", f"Digital Twin de {twin_name}"),
                    is_active=True,
                )
                db.add(twin)
                await db.flush()
                await db.refresh(twin)

                from app.services.twin_knowledge_indexer import twin_knowledge_indexer
                indexed = 0
                try:
                    indexed = await twin_knowledge_indexer.index_from_ats_history(
                        twin_id=str(twin.id),
                        company_id=company_id,
                        months_back=12,
                        db=db,
                    )
                except Exception as idx_err:
                    logger.warning("[DigitalTwin] ATS indexing skipped: %s", idx_err)

                await studio_metering_service.record_studio_usage(
                    db=db,
                    company_id=company_id,
                    agent_type="digital_twin",
                    operation="create_twin",
                    studio_agent_id=str(twin.id),
                    user_id=context.user_id,
                )

                await db.commit()
                break

            return DomainResponse.success_response(
                message=(
                    f"Digital Twin '{twin_name}' criado com sucesso! "
                    f"Decisões indexadas do ATS: {indexed}. "
                    f"O twin pode ser usado para avaliar candidatos com o raciocínio do especialista."
                ),
                data={
                    "twin_id": str(twin.id),
                    "twin_name": twin_name,
                    "specialties": specialties,
                    "decisions_indexed": indexed,
                    "is_active": True,
                },
                domain_id=self.domain_id,
                action_id="create_twin",
                suggestions=[
                    f"Avaliar candidato com twin {twin_name}",
                    f"Treinar twin {twin_name} com áudio",
                    "Listar meus twins",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to create digital twin: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao criar Digital Twin: {exc}",
                domain_id=self.domain_id,
                action_id="create_twin",
            )

    async def _handle_evaluate_with_twin(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        twin_id = params.get("twin_id", "").strip()
        candidate_id = params.get("candidate_id", "").strip()

        if not twin_id:
            return DomainResponse.clarification_response(
                question="Qual Digital Twin deve avaliar? Informe o twin_id.",
                domain_id=self.domain_id,
                action_id="evaluate_with_twin",
            )
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Qual candidato deve ser avaliado? Informe o candidate_id.",
                domain_id=self.domain_id,
                action_id="evaluate_with_twin",
            )

        try:
            from app.core.database import get_db
            from app.services.twin_inference_service import twin_inference_service
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            job_id = params.get("job_id")

            candidate_profile = {"candidate_id": candidate_id}
            job_context = {}

            async for db in get_db():
                try:
                    from app.domains.candidates.repositories.candidate_repository import (
                        CandidateRepository,
                    )
                    c = await CandidateRepository(db).get_by_id_str(
                        candidate_id, company_id=company_id
                    )
                    if c:
                        candidate_profile = {
                            "name": c.name, "role_name": getattr(c, "role_name", None),
                            "skills": getattr(c, "technical_skills", None) or [],
                            "experience": getattr(c, "years_of_experience", None),
                        }
                except Exception as e:
                    logger.debug("[DigitalTwin] Candidate lookup fallback: %s", e)

                from app.domains.agent_studio.repositories.digital_twin_repository import (
                    DigitalTwinRepository as _DtRepo,
                )
                twin = await _DtRepo(db).get_by_id(twin_id=twin_id, company_id=company_id)
                if not twin:
                    return DomainResponse.error_response(
                        error="Digital Twin não encontrado ou não pertence a esta empresa.",
                        domain_id=self.domain_id, action_id="evaluate_with_twin",
                    )

                if job_id:
                    try:
                        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                            JobVacancyCRUDRepository as _JvRepo,
                        )
                        import uuid as _uuid
                        j = await _JvRepo(db).get_vacancy_by_id_and_company(
                            _uuid.UUID(job_id), company_id
                        )
                        if j:
                            job_context = {"title": j.title, "description": (j.description or "")[:500]}
                    except Exception:
                        pass

                evaluation = await twin_inference_service.evaluate(
                    twin_id=twin_id,
                    candidate_profile=candidate_profile,
                    job_context=job_context,
                    company_id=company_id,
                    db=db,
                )

                twin.decision_count = (twin.decision_count or 0) + 1

                await studio_metering_service.record_studio_usage(
                    db=db,
                    company_id=company_id,
                    agent_type="digital_twin",
                    operation="evaluate_with_twin",
                    studio_agent_id=twin_id,
                    profiles_processed=1,
                    user_id=context.user_id,
                )

                await db.commit()
                break

            decision_emoji = {"approved": "✅", "rejected": "❌", "maybe": "🤔"}.get(evaluation.decision, "🤔")

            return DomainResponse.success_response(
                message=(
                    f"{decision_emoji} Avaliação do Twin '{evaluation.twin_name}':\n\n"
                    f"**Score:** {evaluation.score}/100\n"
                    f"**Decisão:** {evaluation.decision}\n"
                    f"**Confiança:** {evaluation.confidence:.0%}\n\n"
                    f"**Raciocínio:** {evaluation.reasoning}"
                ),
                data={
                    "twin_id": evaluation.twin_id,
                    "twin_name": evaluation.twin_name,
                    "score": evaluation.score,
                    "decision": evaluation.decision,
                    "reasoning": evaluation.reasoning,
                    "confidence": evaluation.confidence,
                    "examples_used": len(evaluation.supporting_examples),
                },
                domain_id=self.domain_id,
                action_id="evaluate_with_twin",
                suggestions=[
                    "Avaliar outro candidato",
                    "Ver detalhes do twin",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to evaluate with twin: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao avaliar com Digital Twin: {exc}",
                domain_id=self.domain_id,
                action_id="evaluate_with_twin",
            )

    async def _handle_list_twins(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        try:
            from app.core.database import get_db
            from app.domains.agent_studio.repositories.digital_twin_repository import (
                DigitalTwinRepository as _DtRepo,
            )

            company_id = context.tenant_id

            async for db in get_db():
                twins = await _DtRepo(db).list_by_company(
                    company_id=company_id, is_active=True, limit=20
                )
                break

            if not twins:
                return DomainResponse.success_response(
                    message="Nenhum Digital Twin encontrado. Crie um para replicar o raciocínio de um especialista.",
                    data={"twins": [], "total": 0},
                    domain_id=self.domain_id,
                    action_id="list_twins",
                    suggestions=["Criar Digital Twin"],
                )

            twin_list = [
                f"• {t.twin_name} — {t.decision_count or 0} decisões, "
                f"especialidades: {', '.join(t.specialties or ['geral'])}"
                for t in twins
            ]
            msg = f"Encontrados {len(twins)} Digital Twin(s):\n" + "\n".join(twin_list)

            return DomainResponse.success_response(
                message=msg,
                data={
                    "twins": [
                        {
                            "id": str(t.id),
                            "twin_name": t.twin_name,
                            "specialties": t.specialties or [],
                            "decision_count": t.decision_count or 0,
                            "accuracy_pct": t.accuracy_pct,
                            "is_active": t.is_active,
                        }
                        for t in twins
                    ],
                    "total": len(twins),
                },
                domain_id=self.domain_id,
                action_id="list_twins",
                suggestions=["Criar novo twin", "Avaliar candidato com twin"],
            )
        except Exception as exc:
            logger.exception("Failed to list twins: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao listar twins: {exc}",
                domain_id=self.domain_id,
                action_id="list_twins",
            )

    async def _handle_index_twin_audio(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        twin_id = params.get("twin_id", "").strip()
        if not twin_id:
            return DomainResponse.clarification_response(
                question="Qual Digital Twin deseja treinar com áudio? Informe o twin_id.",
                domain_id=self.domain_id,
                action_id="index_twin_audio",
            )

        try:
            from app.core.database import get_db
            from app.services.twin_knowledge_indexer import twin_knowledge_indexer
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id
            audio_data = params.get("audio_data")
            audio_format = params.get("audio_format", "audio/mp4")

            if not audio_data:
                return DomainResponse.clarification_response(
                    question="Envie o arquivo de áudio da entrevista com o especialista para indexação.",
                    domain_id=self.domain_id,
                    action_id="index_twin_audio",
                )

            audio_bytes = audio_data if isinstance(audio_data, bytes) else audio_data.encode("utf-8")

            async for db in get_db():
                from app.domains.agent_studio.repositories.digital_twin_repository import (
                    DigitalTwinRepository as _DtRepo,
                )
                if not await _DtRepo(db).get_by_id(twin_id=twin_id, company_id=company_id):
                    return DomainResponse.error_response(
                        error="Digital Twin não encontrado ou não pertence a esta empresa.",
                        domain_id=self.domain_id, action_id="index_twin_audio",
                    )

                result = await twin_knowledge_indexer.index_from_audio(
                    twin_id=twin_id,
                    company_id=company_id,
                    audio_bytes=audio_bytes,
                    audio_format=audio_format,
                    language="pt-BR",
                    db=db,
                )

                await studio_metering_service.record_studio_usage(
                    db=db,
                    company_id=company_id,
                    agent_type="digital_twin",
                    operation="index_twin_audio",
                    studio_agent_id=twin_id,
                    user_id=context.user_id,
                )

                await db.commit()
                break

            if result.get("status") == "error":
                return DomainResponse.error_response(
                    error=result.get("message", "Erro ao indexar áudio"),
                    domain_id=self.domain_id,
                    action_id="index_twin_audio",
                )

            return DomainResponse.success_response(
                message=(
                    f"Áudio processado com sucesso! "
                    f"Decisões extraídas e indexadas: {result.get('indexed', 0)}. "
                    f"Tamanho da transcrição: {result.get('transcript_length', 0)} caracteres."
                ),
                data=result,
                domain_id=self.domain_id,
                action_id="index_twin_audio",
                suggestions=[
                    "Avaliar candidato com twin",
                    "Enviar outro áudio",
                ],
            )
        except Exception as exc:
            logger.exception("Failed to index twin audio: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao indexar áudio: {exc}",
                domain_id=self.domain_id,
                action_id="index_twin_audio",
            )

    async def _handle_deactivate_twin(self, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        twin_id = params.get("twin_id")
        if not twin_id:
            return DomainResponse.clarification_response(
                question="Qual twin deseja desativar? Informe o twin_id.",
                domain_id=self.domain_id, action_id="deactivate_twin",
            )

        try:
            from app.core.database import get_db
            from app.services.studio_metering_service import studio_metering_service

            company_id = context.tenant_id

            async for db in get_db():
                from app.domains.agent_studio.repositories.digital_twin_repository import (
                    DigitalTwinRepository as _DtRepo,
                )
                twin = await _DtRepo(db).get_by_id(twin_id=twin_id, company_id=company_id)
                if not twin:
                    return DomainResponse.error_response(
                        error="Digital Twin não encontrado ou não pertence a esta empresa.",
                        domain_id=self.domain_id, action_id="deactivate_twin",
                    )
                twin.is_active = False
                await studio_metering_service.decrement_active_count(db, company_id, "digital_twin")
                await studio_metering_service.record_studio_usage(
                    db=db, company_id=company_id, agent_type="digital_twin",
                    operation="deactivate_twin", studio_agent_id=twin_id,
                    user_id=context.user_id,
                )
                await db.commit()
                break

            return DomainResponse.success_response(
                message=f"Digital Twin '{twin.twin_name}' desativado com sucesso. Quota liberada.",
                data={"twin_id": twin_id, "twin_name": twin.twin_name, "is_active": False},
                domain_id=self.domain_id,
                action_id="deactivate_twin",
            )
        except Exception as exc:
            logger.exception("Failed to deactivate twin: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao desativar twin: {exc}",
                domain_id=self.domain_id,
                action_id="deactivate_twin",
            )

