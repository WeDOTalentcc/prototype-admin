"""Candidate Self-Service domain — read-only status portal for candidates."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml as _yaml_imp

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain
from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher

logger = logging.getLogger(__name__)

_capabilities_yaml_path = Path(__file__).parent / "config" / "capabilities.yaml"
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get("intent_keywords", {})
    if _capabilities_yaml_path.exists()
    else {}
)

_matcher = KeywordIntentMatcher.from_keyword_map(
    _KEYWORD_ACTION_MAP, domain_id="candidate_self_service"
)

CANDIDATE_SELF_SERVICE_ACTIONS = [
    DomainAction(
        action_id="get_status",
        name="Consultar Status da Candidatura",
        description="Retorna etapa atual, data de entrada e próximos passos",
        required_params=["candidate_id", "vacancy_id"],
        tags=["status", "pipeline"],
    ),
    DomainAction(
        action_id="get_interview_info",
        name="Consultar Entrevista Agendada",
        description="Retorna data, horário e formato da entrevista agendada (se houver)",
        required_params=["candidate_id", "vacancy_id"],
        tags=["interview", "scheduling"],
    ),
    DomainAction(
        action_id="get_feedback",
        name="Consultar Feedback da Triagem",
        description="Retorna feedback estruturado WSI se disponibilizado pela empresa",
        required_params=["candidate_id", "vacancy_id"],
        tags=["feedback", "wsi"],
    ),
    DomainAction(
        action_id="get_lgpd_info",
        name="Solicitar Explicação LGPD",
        description="Informa sobre direito de explicação (LGPD Art. 20) e canal de contato",
        required_params=["candidate_id"],
        tags=["lgpd", "compliance"],
    ),
]


@register_domain
class CandidateSelfServiceDomain(ComplianceDomainPrompt):
    """Domínio read-only de autoatendimento do candidato."""

    _compliance_config = {"high_impact": True, "fairness_action_type": "candidate_response"}

    domain_id = "candidate_self_service"
    domain_name = "Candidate Self-Service"
    description = "Portal de autoatendimento: candidato consulta status do próprio processo seletivo"

    def get_allowed_actions(self) -> list[DomainAction]:
        return CANDIDATE_SELF_SERVICE_ACTIONS

    def get_system_prompt(self) -> str:
        return (
            "Assistente de autoatendimento para candidatos da WeDOTalent. "
            "Responda apenas sobre o processo seletivo do candidato autenticado, "
            "com empatia e clareza. Nunca revele scores internos ou dados de terceiros."
        )

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="get_status")
                return IntentResult(
                    intent_id=f"candidate_self_service.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[CSS] Info query → action='{match.action}'",
                )
            except Exception:
                pass

        try:
            match = _matcher.match(query, default_action="get_status")
            return IntentResult(
                intent_id=f"candidate_self_service.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"[CSS] KeywordIntentMatcher → action='{match.action}'",
            )
        except Exception as e:
            logger.debug("[CSS] Matcher failed, fallback: %s", e)
            return IntentResult(
                intent_id="candidate_self_service.get_status",
                action_id="get_status",
                confidence=0.5,
                extracted_params={"raw_query": query},
                reasoning="[CSS] Fallback default → get_status",
            )

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio candidate_self_service."
            )
        logger.info("[CSS] action=%s candidate_id=%s", action_id, params.get("candidate_id"))

        handler_map = {
            "get_status": self._handle_get_status,
            "get_interview_info": self._handle_get_interview_info,
            "get_feedback": self._handle_get_feedback,
            "get_lgpd_info": self._handle_get_lgpd_info,
        }
        handler = handler_map.get(action_id)
        if handler:
            return await handler(params, context)

        return DomainResponse.error_response(
            error=f"Ação '{action_id}' não implementada.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    @staticmethod
    def _require_authenticated(context: DomainContext, action_id: str) -> DomainResponse | None:
        """Bloqueia execução sem identidade autenticada (defesa contra IDOR)."""
        if not context.user_id or not context.tenant_id:
            return DomainResponse.error_response(
                error="Acesso negado: identidade do candidato não autenticada.",
                domain_id="candidate_self_service",
                action_id=action_id,
            )
        return None

    async def _handle_get_status(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        if (denied := self._require_authenticated(context, "get_status")):
            return denied
        vacancy_id = params.get("vacancy_id")
        if not vacancy_id:
            return DomainResponse.clarification_response(
                question="Para qual vaga você quer consultar seu status?",
                domain_id=self.domain_id,
                action_id="get_status",
            )
        # Identidade do candidato vem do contexto autenticado (NUNCA dos params)
        # e os predicados SQL aplicam escopo por tenant para evitar IDOR.
        try:
            from app.core.database import get_db
            from sqlalchemy import text
            data: dict[str, Any] = {}
            async for db in get_db():
                result = await db.execute(
                    text(
                        "SELECT ca.current_stage, ca.applied_at, ca.last_updated_at "
                        "FROM candidate_applications ca "
                        "JOIN candidates c ON c.id = ca.candidate_id "
                        "WHERE c.user_id = :uid AND ca.company_id = :cid "
                        "  AND ca.vacancy_id = :vid LIMIT 1"
                    ),
                    {"uid": context.user_id, "cid": context.tenant_id, "vid": vacancy_id},
                )
                row = result.fetchone() if result else None
                data = dict(row._mapping) if row else {}
                break
            if not data:
                return DomainResponse.success_response(
                    message="Não encontramos sua candidatura ativa para essa vaga.",
                    data={"vacancy_id": vacancy_id},
                    domain_id=self.domain_id,
                    action_id="get_status",
                )
            return DomainResponse.success_response(
                message=f"Sua candidatura está na etapa: **{data.get('current_stage', 'em análise')}**",
                data=data,
                domain_id=self.domain_id,
                action_id="get_status",
            )
        except Exception as exc:
            logger.warning("[CSS] get_status failed: %s", exc)
            return DomainResponse.error_response(
                error="Não foi possível consultar seu status agora. Tente novamente em instantes.",
                domain_id=self.domain_id,
                action_id="get_status",
            )

    async def _handle_get_interview_info(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        if (denied := self._require_authenticated(context, "get_interview_info")):
            return denied
        vacancy_id = params.get("vacancy_id")
        if not vacancy_id:
            return DomainResponse.clarification_response(
                question="De qual vaga você quer ver os detalhes da entrevista?",
                domain_id=self.domain_id,
                action_id="get_interview_info",
            )
        try:
            from app.core.database import get_db
            from sqlalchemy import text
            row_data: dict[str, Any] = {}
            async for db in get_db():
                result = await db.execute(
                    text(
                        "SELECT i.scheduled_at, i.format, i.location, i.meeting_url "
                        "FROM interviews i "
                        "JOIN candidates c ON c.id = i.candidate_id "
                        "WHERE c.user_id = :uid AND i.company_id = :cid "
                        "  AND i.vacancy_id = :vid "
                        "ORDER BY i.scheduled_at DESC LIMIT 1"
                    ),
                    {"uid": context.user_id, "cid": context.tenant_id, "vid": vacancy_id},
                )
                row = result.fetchone() if result else None
                row_data = dict(row._mapping) if row else {}
                break
            if not row_data:
                return DomainResponse.success_response(
                    message="Você ainda não tem entrevista agendada para essa vaga.",
                    data={},
                    domain_id=self.domain_id,
                    action_id="get_interview_info",
                )
            return DomainResponse.success_response(
                message=f"Sua entrevista está agendada para {row_data.get('scheduled_at')}.",
                data=row_data,
                domain_id=self.domain_id,
                action_id="get_interview_info",
            )
        except Exception as exc:
            logger.warning("[CSS] get_interview_info failed: %s", exc)
            return DomainResponse.error_response(
                error="Não foi possível consultar sua entrevista agora.",
                domain_id=self.domain_id,
                action_id="get_interview_info",
            )

    async def _handle_get_feedback(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        if (denied := self._require_authenticated(context, "get_feedback")):
            return denied
        vacancy_id = params.get("vacancy_id")
        if not vacancy_id:
            return DomainResponse.clarification_response(
                question="De qual vaga você quer ver o feedback?",
                domain_id=self.domain_id,
                action_id="get_feedback",
            )
        try:
            from app.core.database import get_db
            from sqlalchemy import text
            feedback: dict[str, Any] = {}
            async for db in get_db():
                result = await db.execute(
                    text(
                        "SELECT cf.feedback_text, cf.shared_at "
                        "FROM candidate_feedback cf "
                        "JOIN candidates c ON c.id = cf.candidate_id "
                        "WHERE c.user_id = :uid AND cf.company_id = :cid "
                        "  AND cf.vacancy_id = :vid "
                        "  AND cf.shared_with_candidate = true "
                        "ORDER BY cf.shared_at DESC LIMIT 1"
                    ),
                    {"uid": context.user_id, "cid": context.tenant_id, "vid": vacancy_id},
                )
                row = result.fetchone() if result else None
                feedback = dict(row._mapping) if row else {}
                break
            if not feedback:
                return DomainResponse.success_response(
                    message="A empresa ainda não compartilhou feedback público para essa vaga.",
                    data={},
                    domain_id=self.domain_id,
                    action_id="get_feedback",
                )
            return DomainResponse.success_response(
                message=feedback.get("feedback_text", "Feedback disponível."),
                data=feedback,
                domain_id=self.domain_id,
                action_id="get_feedback",
            )
        except Exception as exc:
            logger.warning("[CSS] get_feedback failed: %s", exc)
            return DomainResponse.error_response(
                error="Não foi possível consultar feedback agora.",
                domain_id=self.domain_id,
                action_id="get_feedback",
            )

    async def _handle_get_lgpd_info(
        self, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        return DomainResponse.success_response(
            message=(
                "Sob a LGPD (Art. 20), você tem direito a uma explicação sobre decisões "
                "automatizadas que afetem sua candidatura. Para solicitar revisão humana ou "
                "exportar/excluir seus dados, envie um e-mail para dpo@wedotalent.com."
            ),
            data={
                "rights": ["explicação", "revisão humana", "exportação", "exclusão"],
                "contact": "dpo@wedotalent.com",
            },
            domain_id=self.domain_id,
            action_id="get_lgpd_info",
        )
