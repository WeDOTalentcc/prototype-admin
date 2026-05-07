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
    agent_aliases = ("candidate_status", "candidate_portal")

    def get_allowed_actions(self) -> list[DomainAction]:
        return CANDIDATE_SELF_SERVICE_ACTIONS

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

    # NOTE: Os handlers abaixo delegam para os endpoints canônicos do Rails
    # (`/v1/candidate-portal/*`) — a mesma fonte usada pelas tools do
    # `CandidateSelfServiceAgent`. Não escrevemos SQL aqui porque a triagem,
    # entrevistas e feedback ficam no monólito Rails (e seus modelos não estão
    # mapeados no Postgres da LIA com o schema fictício antes assumido).
    # Identidade do candidato vem do contexto autenticado (NUNCA dos params)
    # para evitar IDOR.
    #
    # Sanitização: a resposta crua do Rails pode trazer campos internos
    # (scores brutos, notas de avaliadores, IDs de avaliação). Filtramos com
    # allowlists explícitas antes de devolver para o canal de chat — nunca
    # retornamos o payload bruto.
    _STATUS_ALLOWED_FIELDS = {
        "vacancy_id", "vacancy_title", "stage", "stage_name", "current_stage",
        "applied_at", "last_updated_at", "next_step", "next_step_at",
        "expected_response_at",
    }
    _INTERVIEW_ALLOWED_FIELDS = {
        "vacancy_id", "vacancy_title", "scheduled_at", "start_time", "end_time",
        "format", "modality", "location", "meeting_url", "interviewer_name",
        "duration_minutes", "instructions",
    }
    _FEEDBACK_ALLOWED_FIELDS = {
        "vacancy_id", "vacancy_title", "feedback_text", "summary", "shared_at",
        "stage", "outcome", "next_steps",
    }

    @staticmethod
    def _filter_fields(payload: Any, allowed: set[str]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        return {k: v for k, v in payload.items() if k in allowed}
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
        try:
            from app.shared.rails_client import rails_get
            data = await rails_get(
                "/v1/candidate-portal/status",
                params={
                    "candidate_id": context.user_id,
                    "vacancy_id": vacancy_id,
                    "company_id": context.tenant_id,
                },
            )
            if not data:
                return DomainResponse.success_response(
                    message="Não encontramos sua candidatura ativa para essa vaga.",
                    data={"vacancy_id": vacancy_id},
                    domain_id=self.domain_id,
                    action_id="get_status",
                )
            stage = (
                data.get("stage_name")
                or data.get("current_stage")
                or data.get("stage")
                or "em análise"
            )
            safe = self._filter_fields(data, self._STATUS_ALLOWED_FIELDS)
            return DomainResponse.success_response(
                message=f"Sua candidatura está na etapa: **{stage}**",
                data=safe,
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
            from app.shared.rails_client import rails_get
            data = await rails_get(
                "/v1/candidate-portal/interview",
                params={
                    "candidate_id": context.user_id,
                    "vacancy_id": vacancy_id,
                    "company_id": context.tenant_id,
                },
            )
            if not data:
                return DomainResponse.success_response(
                    message="Você ainda não tem entrevista agendada para essa vaga.",
                    data={},
                    domain_id=self.domain_id,
                    action_id="get_interview_info",
                )
            scheduled = (
                data.get("scheduled_at")
                or data.get("start_time")
                or "data a confirmar"
            )
            safe = self._filter_fields(data, self._INTERVIEW_ALLOWED_FIELDS)
            return DomainResponse.success_response(
                message=f"Sua entrevista está agendada para {scheduled}.",
                data=safe,
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
            from app.shared.rails_client import rails_get
            # Política da empresa precisa habilitar feedback público — checamos antes
            policy = await rails_get(
                "/v1/candidate-portal/policy",
                params={"company_id": context.tenant_id},
            )
            if policy and not policy.get("show_feedback", False):
                return DomainResponse.success_response(
                    message=(
                        "A empresa optou por não disponibilizar feedback detalhado "
                        "neste processo seletivo."
                    ),
                    data={"feedback_available": False},
                    domain_id=self.domain_id,
                    action_id="get_feedback",
                )
            feedback = await rails_get(
                "/v1/candidate-portal/wsi-feedback",
                params={
                    "candidate_id": context.user_id,
                    "vacancy_id": vacancy_id,
                    "company_id": context.tenant_id,
                },
            )
            if not feedback:
                return DomainResponse.success_response(
                    message="A empresa ainda não compartilhou feedback público para essa vaga.",
                    data={},
                    domain_id=self.domain_id,
                    action_id="get_feedback",
                )
            text = (
                feedback.get("feedback_text")
                or feedback.get("summary")
                or "Feedback disponível — confira os detalhes abaixo."
            )
            safe = self._filter_fields(feedback, self._FEEDBACK_ALLOWED_FIELDS)
            return DomainResponse.success_response(
                message=text,
                data=safe,
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
