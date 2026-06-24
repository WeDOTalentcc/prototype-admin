"""
JobCreationDomain — Domain for the conversational job creation wizard.

Integrates WSI methodology (Bloco A: F1-F6) into the Unified Chat.
The wizard flow is managed by the LangGraph JobCreationGraph;
this domain class is the entry point from the supervisor/orchestrator.

Actions are conversational stages, not CRUD operations.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple

from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.base import (
    DomainPrompt,
    DomainAction,
    DomainContext,
    DomainResponse,
    ActionType,
)
from app.domains.registry import register_domain
from app.domains.job_creation.state import (
    JobCreationState,
)
from app.domains.job_creation.graph import get_job_creation_graph

logger = logging.getLogger(__name__)


def _mask_pii(text: str) -> str:
    """Mask PII before audit logging (GOV: LGPD compliance)."""
    if not text:
        return ""
    try:
        from app.services.pii_filter import mask_pii
        return mask_pii(text[:500])
    except ImportError:
        return text[:500] if len(text) > 500 else text


@register_domain
class JobCreationDomain(ComplianceDomainPrompt):

    def __init__(self):
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = get_job_creation_graph()
        return self._graph

    domain_id: str = "job_creation"

    @property
    def domain_name(self) -> str:
        return "Criacao de Vaga (Wizard WSI)"

    @property
    def description(self) -> str:
        return (
            "Wizard conversacional para criar vagas com metodologia WSI. "
            "Guia o recrutador passo a passo: JD enrichment, Big Five, "
            "competencias, perguntas de triagem, publicacao e calibracao."
        )

    def get_allowed_actions(self) -> List[DomainAction]:
        return [
            DomainAction(
                id="start_wizard",
                name="Iniciar criacao de vaga",
                description="Inicia o wizard de criacao de vaga. Recebe descricao inicial (titulo, senioridade, departamento) e guia o recrutador pelo fluxo WSI completo",
                action_type=ActionType.ACTION,
                examples=(
                    "Criar vaga de PM senior",
                    "Quero abrir uma vaga",
                    "Nova vaga de desenvolvedor backend",
                    "Preciso contratar um designer",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="approve_jd",
                name="Aprovar JD enriquecido",
                description="Aprova ou rejeita o JD enriquecido pela IA (HITL ponto 1 - F1). Recrutador pode editar antes de aprovar",
                action_type=ActionType.ACTION,
                examples=(
                    "Aprovar JD",
                    "Fica bom",
                    "Aceito",
                    "Preciso editar o JD",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="set_salary",
                name="Definir salario e beneficios",
                description="Define faixa salarial e beneficios da vaga",
                action_type=ActionType.ACTION,
                examples=(
                    "Salario entre 15k e 20k",
                    "Beneficios: VR, VT, plano de saude",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="set_screening_mode",
                name="Escolher modo de triagem",
                description="Escolhe entre modo compacto (7 perguntas) ou completo (12 perguntas) para a triagem WSI",
                action_type=ActionType.ACTION,
                examples=(
                    "Modo compacto",
                    "Quero triagem completa",
                    "7 perguntas",
                    "12 perguntas",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="approve_questions",
                name="Aprovar perguntas de triagem",
                description="Aprova, edita ou regenera as perguntas de triagem WSI (HITL ponto 2 - F6). Recrutador revisa cada pergunta",
                action_type=ActionType.ACTION,
                examples=(
                    "Aprovar perguntas",
                    "Regenerar pergunta 3",
                    "Editar pergunta 1",
                    "Remover pergunta sobre...",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="set_eligibility",
                name="Configurar elegibilidade",
                description="Adiciona ou remove perguntas de elegibilidade sim/nao (ex: tem CNH? aceita viagem?). Requisitos eliminatorios antes da triagem WSI",
                action_type=ActionType.ACTION,
                examples=(
                    "Adicionar pergunta: tem CNH?",
                    "Disponibilidade imediata e obrigatoria",
                    "Aceita viagem?",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="configure_publish",
                name="Configurar publicacao",
                description="Define plataformas (LinkedIn/Indeed/Website), modo de sourcing (local/global/hibrido), canais de contato e opcao de auto-screening",
                action_type=ActionType.ACTION,
                examples=(
                    "Publicar no LinkedIn e Indeed",
                    "Sourcing global",
                    "Contato por WhatsApp e email",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="publish_job",
                name="Publicar vaga",
                description="Publica a vaga nas plataformas configuradas e inicia screening automatico. Requer que todas as etapas anteriores estejam completas",
                action_type=ActionType.ACTION,
                examples=(
                    "Publicar",
                    "Manda ver",
                    "Publica essa vaga",
                ),
                requires_confirmation=True,
            ),
            DomainAction(
                id="calibrate",
                name="Calibrar perfis",
                description="Apresenta candidatos para calibracao (aprovar/rejeitar com razoes). Minimo 3 perfis calibrados antes do handoff",
                action_type=ActionType.ACTION,
                examples=(
                    "Aprovar candidato",
                    "Rejeitar: falta experiencia em...",
                    "Proximo candidato",
                ),
                requires_confirmation=False,
            ),
            DomainAction(
                id="wizard_status",
                name="Status do wizard",
                description="Mostra o progresso atual do wizard de criacao de vaga",
                action_type=ActionType.QUERY,
                examples=(
                    "Em que etapa estamos?",
                    "Status do wizard",
                    "O que falta?",
                ),
            ),
            DomainAction(
                id="help",
                name="Ajuda",
                description="Explica o fluxo de criacao de vaga e a metodologia WSI",
                action_type=ActionType.QUERY,
                examples=(
                    "Como funciona?",
                    "O que e o WSI?",
                    "Ajuda",
                ),
            ),
        ]

    def get_system_prompt(self, context: DomainContext, **kwargs) -> str:

        wizard_state = context.metadata.get("wizard_state", {})
        current_stage = wizard_state.get("current_stage", "not_started")

        _domain_prompt = f"""Voce e a LIA, assistente de recrutamento da WeDOTalent.
Voce esta guiando o recrutador pelo wizard de criacao de vaga usando a metodologia WSI.

ETAPA ATUAL: {current_stage}

REGRAS WSI (absolutas, nao podem ser revertidas):
1. Gates tem precedencia sobre score
2. Perguntas hipoteticas PROIBIDAS (CBI = situacao real passada)
3. Sem perguntas de fit cultural
4. Recrutador aprova TODAS as perguntas antes de publicar
5. Falha do LLM nunca reprova candidato
6. Temperature=0.0 para avaliacao
7. JD Quality Score minimo 50 para prosseguir

FLUXO DO WIZARD:
1. Intake: recrutador descreve a vaga
2. JD Enrichment (F1): IA enriquece o JD → recrutador APROVA
3. Big Five (F2+F3): perfil extraido automaticamente
4. Salario: faixa + beneficios
5. Competencias (F4+F5): senioridade + distribuicao de perguntas + escolha de modo (compact/full)
6. Perguntas WSI (F6): IA gera perguntas → recrutador APROVA cada uma
7. Elegibilidade: perguntas sim/nao eliminatorias
8. Review: checklist final
9. Publicar: plataformas + sourcing + auto-screening
10. Calibracao: 3+ perfis aprovados/rejeitados
11. Handoff: navegar para pagina da vaga

Responda de forma conversacional, guiando o recrutador pela etapa atual.
Sempre informe qual e a proxima etapa e o que precisa ser feito."""
        return super().get_system_prompt(base_prompt=_domain_prompt)

    def process_intent(self, user_query: str, context: DomainContext) -> Dict[str, Any]:
        """Route user message to the appropriate wizard action."""
        wizard_state = context.metadata.get("wizard_state", {})
        current_stage = wizard_state.get("current_stage")

        # Stage-based routing (most common path)
        if current_stage:
            return self._route_by_stage(user_query, current_stage, context)

        # No active wizard — check if user wants to start one
        q_lower = user_query.lower()
        start_patterns = [
            "criar vaga", "nova vaga", "abrir vaga", "contratar",
            "preciso de", "quero criar", "vamos criar",
        ]
        if any(p in q_lower for p in start_patterns):
            return {
                "action_id": "start_wizard",
                "params": {"user_query": user_query},
                "confidence": 0.95,
                "source": "keyword_match",
            }

        return {
            "action_id": "help",
            "params": {"user_query": user_query},
            "confidence": 0.7,
            "source": "fallback",
        }

    def _route_by_stage(
        self, query: str, stage: str, context: DomainContext
    ) -> Dict[str, Any]:
        """Route based on current wizard stage + user message."""
        q_lower = query.lower()

        # HITL: JD approval
        if stage == "jd_enrichment":
            # T2 (Task #1085) — quando o flag LIA_WIZARD_LLM_GATES está ON,
            # toda mensagem do recrutador no stage jd_enrichment é dispatched
            # para o gate_node LLM-based, que substitui esses heurísticos.
            from app.domains.job_creation.graph import _llm_gates_enabled
            if _llm_gates_enabled():
                return {
                    "action_id": "gate_jd",
                    "params": {"user_query": query},
                    "confidence": 0.95,
                    "source": "llm_gate",
                }
            if any(w in q_lower for w in ("aprov", "aceito", "fica bom", "ok", "sim")):
                return {"action_id": "approve_jd", "params": {"approved": True, "user_query": query}, "confidence": 0.95}
            if any(w in q_lower for w in ("rejeit", "nao", "editar", "mudar")):
                return {"action_id": "approve_jd", "params": {"approved": False, "user_query": query}, "confidence": 0.9}

        # Salary
        if stage == "salary":
            return {"action_id": "set_salary", "params": {"user_query": query}, "confidence": 0.9}

        # Competency: screening mode selection
        if stage == "competency":
            # T4 (Task #1086) — quando o flag LIA_WIZARD_LLM_GATES está ON,
            # toda mensagem do recrutador no stage competency é dispatched
            # para o competency_gate_node LLM-based, que substitui esses
            # heurísticos brittle ("compact"/"compacto"/"7q"/"full"/"12q").
            from app.domains.job_creation.graph import _llm_gates_enabled
            if _llm_gates_enabled():
                return {
                    "action_id": "gate_competency",
                    "params": {"user_query": query},
                    "confidence": 0.95,
                    "source": "llm_gate",
                }
            if any(w in q_lower for w in ("compact", "compacto", "7 pergunta", "7q")):
                return {"action_id": "set_screening_mode", "params": {"mode": "compact"}, "confidence": 0.95}
            if any(w in q_lower for w in ("full", "completo", "12 pergunta", "12q")):
                return {"action_id": "set_screening_mode", "params": {"mode": "full"}, "confidence": 0.95}

        # HITL: Questions approval
        if stage == "wsi_questions":
            # T5 (Task #1087) — quando o flag LIA_WIZARD_LLM_GATES está ON,
            # toda mensagem do recrutador no stage wsi_questions é dispatched
            # para o wsi_questions_gate_node LLM-based, que substitui esses
            # heurísticos brittle ("aprov"/"regener"/"refaz").
            from app.domains.job_creation.graph import _llm_gates_enabled
            if _llm_gates_enabled():
                return {
                    "action_id": "gate_wsi_questions",
                    "params": {"user_query": query},
                    "confidence": 0.95,
                    "source": "llm_gate",
                }
            if any(w in q_lower for w in ("aprov", "aceito", "ok", "sim", "fica")):
                return {"action_id": "approve_questions", "params": {"approved": True, "user_query": query}, "confidence": 0.95}
            if any(w in q_lower for w in ("regener", "refaz", "outra")):
                return {"action_id": "approve_questions", "params": {"approved": False, "regenerate": True, "user_query": query}, "confidence": 0.9}

        # Eligibility
        if stage == "eligibility":
            return {"action_id": "set_eligibility", "params": {"user_query": query}, "confidence": 0.85}

        # Publish config
        if stage == "review" or stage == "publish":
            # T6 (Task #1088) — quando o flag LIA_WIZARD_LLM_GATES está ON,
            # toda mensagem do recrutador no stage review é dispatched para
            # o review_gate_node LLM-based, que substitui esses heurísticos
            # brittle ("public"/"manda"/"publica") e adiciona dupla
            # confirmação para publish_now + validação de target_section
            # (request_changes) e destinations.
            from app.domains.job_creation.graph import _llm_gates_enabled
            if stage == "review" and _llm_gates_enabled():
                return {
                    "action_id": "gate_review",
                    "params": {"user_query": query},
                    "confidence": 0.95,
                    "source": "llm_gate",
                }
            if any(w in q_lower for w in ("public", "manda", "publica")):
                return {"action_id": "publish_job", "params": {"user_query": query}, "confidence": 0.95}
            return {"action_id": "configure_publish", "params": {"user_query": query}, "confidence": 0.8}

        # Calibration
        if stage == "calibration":
            return {"action_id": "calibrate", "params": {"user_query": query}, "confidence": 0.85}

        # Status check
        if any(w in q_lower for w in ("status", "etapa", "falta", "progresso")):
            return {"action_id": "wizard_status", "params": {}, "confidence": 0.95}

        # Default: pass query to current stage handler
        return {
            "action_id": "wizard_status",
            "params": {"user_query": query},
            "confidence": 0.6,
            "source": "stage_fallback",
        }

    def execute_action(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: DomainContext,
    ) -> DomainResponse:
        """Execute a wizard action by invoking or resuming the LangGraph.

        wizard_state is accumulated across invocations and passed back
        to the graph on resume (same pattern as scheduling domain).
        """
        thread_id = context.session_id or str(uuid.uuid4())
        wizard_state: Dict[str, Any] = context.metadata.get("wizard_state", {})

        try:
            if action_id == "start_wizard":
                return self._start_wizard(params, context, thread_id)

            if action_id == "approve_jd":
                return self._handle_jd_approval(params, context, thread_id)

            if action_id == "gate_jd":
                return self._handle_gate_jd(params, context, thread_id)
            if action_id == "gate_competency":
                return self._handle_gate_competency(params, context, thread_id)
            if action_id == "gate_wsi_questions":
                return self._handle_gate_wsi_questions(params, context, thread_id)
            if action_id == "gate_review":
                return self._handle_gate_review(params, context, thread_id)

            if action_id == "set_salary":
                return self._handle_salary(params, context, thread_id)

            if action_id == "set_screening_mode":
                return self._handle_screening_mode(params, context, thread_id)

            if action_id == "approve_questions":
                return self._handle_question_approval(params, context, thread_id)

            if action_id == "set_eligibility":
                return self._handle_eligibility(params, context, thread_id)

            if action_id == "configure_publish":
                return self._handle_publish_config(params, context, thread_id)

            if action_id == "publish_job":
                return self._handle_publish(params, context, thread_id)

            if action_id == "calibrate":
                return self._handle_calibration(params, context, thread_id)

            if action_id == "wizard_status":
                return self._get_wizard_status(wizard_state)

            if action_id == "help":
                return self._get_help()

            return DomainResponse(
                success=False,
                message="Acao nao reconhecida no wizard de criacao de vaga",
                error=f"Unknown action: {action_id}",
            )

        except Exception as e:
            logger.error("[JobCreation] Error executing %s: %s | query=%s",
                        action_id, e, _mask_pii(params.get("user_query", "")), exc_info=True)
            return DomainResponse(
                success=False,
                message="Erro ao processar etapa do wizard. Tente novamente.",
                error=str(e),
            )

    # -------------------------------------------------------------------
    # Action handlers
    # -------------------------------------------------------------------

    def _start_wizard(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Start a new wizard session."""
        initial_state: JobCreationState = {
            "session_id": thread_id,
            "user_id": context.user_id or "",
            "workspace_id": context.workspace_id or 0,
            "auth_token": context.auth_token or "",
            "language": "pt-BR",
            "user_query": params.get("user_query", ""),
            "raw_input": params.get("user_query", ""),
            "conversation_messages": [],
            "stage_history": [],
            "jd_quality_warnings": [],
            "benefits": [],
            "wsi_questions": [],
            "eligibility_questions": [],
            "publish_platforms": [],
            "contact_channels": [],
            "calibration_candidates": [],
            "calibration_threshold": 3,
            "calibration_complete": False,
            "auto_screen_enabled": True,
            "salary_currency": "BRL",
            "company_defaults_applied": [],
            "requires_approval": False,
            "completeness": 0.0,
        }

        result = self.graph.invoke(initial_state, thread_id)
        stage_payload = result.get("ws_stage_payload", {})

        return DomainResponse(
            success=True,
            message="Wizard de criacao de vaga iniciado! Vou analisar e enriquecer a descricao da vaga.",
            data={
                "wizard_state": result,
                "ws_payload": stage_payload,
                "thread_id": thread_id,
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_jd_approval(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle recruiter's JD approval/rejection (HITL point 1)."""
        approved = params.get("approved", False)
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "jd_approved": approved,
            "user_query": params.get("user_query", ""),
        })

        if approved:
            msg = "JD aprovado! Extraindo perfil Big Five e calculando competencias..."
        else:
            msg = "Entendi, vou ajustar o JD. O que gostaria de mudar?"

        return DomainResponse(
            success=True,
            message=msg,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_gate_jd(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """T2 (Task #1085) — gate LLM-based para HITL #1 (jd_enrichment).

        Resume o graph com ``gate_resume_message=<user_query>``. O nó
        ``jd_gate_node`` classifica o intent via Haiku, muta state
        determinísticamente, e ``route_after_gate`` decide entre
        ``bigfive`` / ``intake`` / END.

        A mensagem ao recrutador vem de ``gate_clarify_message`` (preenchido
        pelo classifier) ou de fallbacks determinísticos por intent.
        """
        user_query = params.get("user_query", "")

        # Task #1094 — canônico: Command(resume=<msg>) via wrapper.
        # O gate em interrupt() recebe ``user_query`` direto como resume value.
        # Fallback para resume() legacy se o checkpoint não estiver pausado
        # (cobertura defensiva: testes/REST clients antigos sem interrupt).
        if self.graph.is_interrupted(thread_id):
            result = self.graph.resume_with_message(thread_id, user_query)
        else:
            prior = context.metadata.get("wizard_state", {})
            result = self.graph.resume(thread_id, prior, {
                "gate_resume_message": user_query,
                "user_query": user_query,
            })

        clarify = result.get("gate_clarify_message")
        intent = result.get("gate_last_intent")
        approved = result.get("jd_approved")

        if clarify:
            message = clarify
        elif approved is True:
            message = "Aprovado. Vamos para o próximo bloco do WSI (Big Five)."
        elif approved is False and intent == "provide_new_content":
            message = "Recebi a descrição nova. Vou re-enriquecer agora."
        elif approved is False:
            message = "Entendi, vou ajustar. O que mais você quer mudar?"
        else:
            message = "Posso continuar?"

        return DomainResponse(
            success=True,
            message=message,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
                "gate_intent": intent,
                "gate_confidence": result.get("gate_last_confidence"),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_gate_competency(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """T4 (Task #1086) — gate LLM-based para HITL #2 (competency).

        Resume o graph com ``gate_resume_message=<user_query>``. O nó
        ``competency_gate_node`` classifica o intent via Haiku (allowlist
        ``select_compact|select_full|ask_question|undecided``), muta state
        determinísticamente (apenas ``screening_mode`` em select_*), e
        ``route_after_competency_gate`` decide entre ``wsi_questions`` /
        ``competency`` (re-pergunta) / END.

        A mensagem ao recrutador vem de ``gate_clarify_message`` (preenchido
        pelo classifier — recomendação por seniority em ask_question /
        undecided, confirmação em select_*) ou de fallbacks determinísticos.
        """
        user_query = params.get("user_query", "")

        # Task #1094 — canônico: Command(resume=<msg>) via wrapper.
        if self.graph.is_interrupted(thread_id):
            result = self.graph.resume_with_message(thread_id, user_query)
        else:
            prior = context.metadata.get("wizard_state", {})
            result = self.graph.resume(thread_id, prior, {
                "gate_resume_message": user_query,
                "user_query": user_query,
            })

        clarify = result.get("gate_clarify_message")
        intent = result.get("gate_last_intent")
        screening_mode = result.get("screening_mode")

        if clarify:
            message = clarify
        elif intent == "select_compact" and screening_mode == "compact":
            message = "Modo Compacto (7 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        elif intent == "select_full" and screening_mode == "full":
            message = "Modo Completo (12 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        else:
            message = "Compacto (7 perguntas) ou Completo (12 perguntas)?"

        return DomainResponse(
            success=True,
            message=message,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
                "gate_intent": intent,
                "gate_confidence": result.get("gate_last_confidence"),
                "screening_mode": screening_mode,
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_gate_wsi_questions(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """T5 (Task #1087) — gate LLM-based para HITL #2 (wsi_questions).

        Resume o graph com ``gate_resume_message=<user_query>``. O nó
        ``wsi_questions_gate_node`` classifica o intent via Haiku
        (allowlist ``approve_all|regenerate_all|edit_specific_question|
        add_question|remove_question|ask_question``), muta state
        determinísticamente, e ``route_after_wsi_questions_gate`` decide
        entre ``eligibility`` / ``wsi_questions`` (regen) / END.

        A mensagem ao recrutador vem de ``gate_clarify_message``
        (preenchido pelo classifier) ou de fallbacks determinísticos
        por intent.
        """
        user_query = params.get("user_query", "")

        # Task #1094 — canônico: Command(resume=<msg>) via wrapper.
        if self.graph.is_interrupted(thread_id):
            result = self.graph.resume_with_message(thread_id, user_query)
        else:
            prior = context.metadata.get("wizard_state", {})
            result = self.graph.resume(thread_id, prior, {
                "gate_resume_message": user_query,
                "user_query": user_query,
            })

        clarify = result.get("gate_clarify_message")
        intent = result.get("gate_last_intent")
        approved = result.get("questions_approved")

        if clarify:
            message = clarify
        elif intent == "approve_all" and approved is True:
            message = (
                "Aprovado! Vou seguir para configurar as perguntas de elegibilidade."
            )
        elif intent == "regenerate_all":
            message = "Sem problema, vou regenerar o pacote inteiro agora."
        elif intent == "edit_specific_question":
            message = "Beleza, vou ajustar a pergunta indicada."
        elif intent == "add_question":
            message = "Show, vou acrescentar a pergunta nova ao pacote."
        elif intent == "remove_question":
            message = "Pergunta removida. Me confirma se posso seguir."
        else:
            message = (
                "Você quer aprovar o pacote, regenerar tudo, editar/adicionar/remover alguma pergunta?"
            )

        return DomainResponse(
            success=True,
            message=message,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
                "gate_intent": intent,
                "gate_confidence": result.get("gate_last_confidence"),
                "questions_approved": approved,
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_gate_review(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """T6 (Task #1088) — gate LLM-based para HITL #3 (review/publish).

        Resume o graph com ``gate_resume_message=<user_query>``. O nó
        ``review_gate_node`` classifica o intent via Haiku (allowlist
        ``publish_now|request_changes|ask_clarification|
        configure_destinations``), aplica DUPLA CONFIRMAÇÃO de chat
        para ``publish_now`` (state ``pending_publish_confirmation`` +
        TTL 5min), valida ``target_section`` ∈ {title, description,
        questions, salary, pipeline, destinations} e ``destinations``
        contra a allowlist canônica, muta state determinísticamente, e
        ``route_after_review_gate`` decide entre ``publish`` /
        ``jd_enrichment`` / ``salary`` / ``wsi_questions`` /
        ``eligibility`` / ``review`` / END.

        A mensagem ao recrutador vem de ``gate_clarify_message``
        (preenchido pelo gate_node — confirmação de publicação,
        confirmação de ajuste, listagem de destinos válidos, etc.) ou
        de fallbacks determinísticos por intent.
        """
        user_query = params.get("user_query", "")

        # Task #1094 — canônico: Command(resume=<msg>) via wrapper.
        if self.graph.is_interrupted(thread_id):
            result = self.graph.resume_with_message(thread_id, user_query)
        else:
            prior = context.metadata.get("wizard_state", {})
            result = self.graph.resume(thread_id, prior, {
                "gate_resume_message": user_query,
                "user_query": user_query,
            })

        clarify = result.get("gate_clarify_message")
        intent = result.get("gate_last_intent")
        confirmed_publish = result.get("policy_confirmed_publish")
        pending_publish = result.get("pending_publish_confirmation")

        if clarify:
            message = clarify
        elif intent == "publish_now" and confirmed_publish is True:
            message = "Confirmado! Publicando a vaga agora nos canais selecionados."
        elif intent == "publish_now" and pending_publish is True:
            message = "Vou publicar nos canais configurados. Confirma para mandar pro ar?"
        elif intent == "request_changes":
            message = "Beleza, vou ajustar a seção indicada."
        elif intent == "configure_destinations":
            platforms = result.get("publish_platforms") or []
            message = (
                f"Configurando publicação em: {', '.join(platforms)}." if platforms
                else "Quais canais você quer publicar?"
            )
        else:
            message = "Você quer publicar agora, ajustar alguma seção ou tirar uma dúvida?"

        return DomainResponse(
            success=True,
            message=message,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
                "gate_intent": intent,
                "gate_confidence": result.get("gate_last_confidence"),
                "policy_confirmed_publish": confirmed_publish,
                "pending_publish_confirmation": pending_publish,
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_salary(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle salary configuration."""
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "salary_min": params.get("salary_min"),
            "salary_max": params.get("salary_max"),
            "benefits": params.get("benefits", []),
            "user_query": params.get("user_query", ""),
        })

        return DomainResponse(
            success=True,
            message="Salario configurado. Agora vamos definir senioridade e modo de triagem.",
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_screening_mode(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle screening mode selection (compact/full)."""
        mode = params.get("mode", "compact")
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "screening_mode": mode,
            "user_query": params.get("user_query", ""),
        })

        mode_label = "Compacto (7 perguntas)" if mode == "compact" else "Completo (12 perguntas)"
        return DomainResponse(
            success=True,
            message=f"Modo {mode_label} selecionado. Gerando perguntas de triagem WSI...",
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_question_approval(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle recruiter's question approval/rejection (HITL point 2)."""
        approved = params.get("approved", False)
        prior = context.metadata.get("wizard_state", {})

        updates = {
            "questions_approved": approved,
            "user_query": params.get("user_query", ""),
        }

        if params.get("edited_questions"):
            updates["wsi_questions"] = params["edited_questions"]

        result = self.graph.resume(thread_id, prior, updates)

        if approved:
            msg = "Perguntas aprovadas! Vamos configurar perguntas de elegibilidade (requisitos eliminatorios)."
        else:
            msg = "Regenerando perguntas. Aguarde..."

        return DomainResponse(
            success=True,
            message=msg,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_eligibility(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle eligibility question configuration."""
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "eligibility_questions": params.get("questions", []),
            "user_query": params.get("user_query", ""),
        })

        return DomainResponse(
            success=True,
            message="Elegibilidade configurada. Revisando checklist final...",
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_publish_config(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle publish configuration."""
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "publish_platforms": params.get("platforms", []),
            "sourcing_mode": params.get("sourcing_mode"),
            "contact_channels": params.get("channels", []),
            "auto_screen_enabled": params.get("auto_screen", True),
            "user_query": params.get("user_query", ""),
        })

        return DomainResponse(
            success=True,
            message="Configuracao de publicacao atualizada.",
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_publish(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle job publishing."""
        prior = context.metadata.get("wizard_state", {})

        result = self.graph.resume(thread_id, prior, {
            "user_query": params.get("user_query", ""),
        })

        job_id = result.get("job_id")
        if job_id:
            share_link = result.get("share_link", "")
            msg = f"Vaga publicada! ID: {job_id}. Link: {share_link}. Iniciando calibracao com candidatos..."
        else:
            msg = "Publicacao pendente. Verifique se todos os campos obrigatorios estao preenchidos."

        return DomainResponse(
            success=True,
            message=msg,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _handle_calibration(
        self, params: Dict[str, Any], context: DomainContext, thread_id: str
    ) -> DomainResponse:
        """Handle calibration decisions."""
        prior = context.metadata.get("wizard_state", {})

        # Bug A/B prereq fix (2026-06-20): set current_stage="calibration" explicitly
        # BEFORE graph.resume() so _derive_wizard_stage has a non-circular signal
        # on the first calibration turn (no prior ws_stage_payload exists yet).
        # Without this, _derive_wizard_stage falls through to "handoff" because
        # it was reading ws_stage_payload.stage (circular — only set AFTER the node runs).
        # Sensor: tests/contract/test_wizard_calibration_stage.py T-a
        prior_with_stage = {**prior, "current_stage": "calibration"}

        result = self.graph.resume(thread_id, prior_with_stage, {
            "user_query": params.get("user_query", ""),
            "calibration_candidates": params.get("candidates", []),
        })

        complete = result.get("calibration_complete", False)
        if complete:
            msg = "Calibracao completa! Navegando para a pagina da vaga..."
        else:
            approved = sum(
                1 for c in result.get("calibration_candidates", [])
                if c.get("decision") == "approved"
            )
            threshold = result.get("calibration_threshold", 3)
            msg = f"Calibracao: {approved}/{threshold} perfis aprovados. Continue avaliando."

        return DomainResponse(
            success=True,
            message=msg,
            data={
                "wizard_state": result,
                "ws_payload": result.get("ws_stage_payload", {}),
            },
            metadata={"current_stage": result.get("current_stage")},
        )

    def _get_wizard_status(self, wizard_state: Dict[str, Any]) -> DomainResponse:
        """Return current wizard progress."""
        current_stage = wizard_state.get("current_stage", "not_started")
        completeness = wizard_state.get("completeness", 0.0)

        stage_labels = {
            "not_started": "Nao iniciado",
            "intake": "Coleta inicial",
            "jd_enrichment": "Enriquecimento do JD (aguardando aprovacao)",
            "bigfive": "Extracao Big Five",
            "salary": "Salario e beneficios",
            "competency": "Competencias e modo de triagem",
            "wsi_questions": "Perguntas WSI (aguardando aprovacao)",
            "eligibility": "Perguntas de elegibilidade",
            "review": "Revisao final",
            "publish": "Publicacao",
            "calibration": "Calibracao de perfis",
            "handoff": "Handoff para pagina da vaga",
            "done": "Concluido",
        }

        return DomainResponse(
            success=True,
            message=f"Etapa: {stage_labels.get(current_stage, current_stage)} | Progresso: {completeness:.0%}",
            data={
                "current_stage": current_stage,
                "completeness": completeness,
                "stage_label": stage_labels.get(current_stage, current_stage),
            },
        )

    def _get_help(self) -> DomainResponse:
        """Return help about the wizard and WSI methodology."""
        return DomainResponse(
            success=True,
            message=(
                "O wizard de criacao de vaga usa a metodologia WSI para gerar "
                "perguntas de triagem personalizadas para cada vaga.\n\n"
                "**Fluxo:**\n"
                "1. Descreva a vaga → IA enriquece o JD → voce aprova\n"
                "2. IA extrai perfil Big Five e define competencias\n"
                "3. Voce escolhe modo de triagem (compacto 7q ou completo 12q)\n"
                "4. IA gera perguntas baseadas em CBI/Bloom/Dreyfus → voce aprova\n"
                "5. Configure elegibilidade e publique\n"
                "6. Calibre com 3+ perfis de candidatos\n\n"
                "Para comecar: descreva a vaga que quer criar."
            ),
        )

    def get_suggestions(self, context: DomainContext) -> List[str]:
        wizard_state = context.metadata.get("wizard_state", {})
        stage = wizard_state.get("current_stage")

        if not stage:
            return [
                "Criar vaga de desenvolvedor backend",
                "Nova vaga de PM senior",
                "Como funciona o wizard?",
            ]

        stage_suggestions = {
            "jd_enrichment": ["Aprovar JD", "Editar descricao", "Adicionar requisitos"],
            "salary": ["Definir salario", "Adicionar beneficios"],
            "competency": ["Modo compacto (7 perguntas)", "Modo completo (12 perguntas)"],
            "wsi_questions": ["Aprovar perguntas", "Regenerar perguntas", "Editar pergunta"],
            "eligibility": ["Adicionar pergunta eliminatoria", "Prosseguir sem elegibilidade"],
            "review": ["Publicar vaga", "Revisar checklist"],
            "calibration": ["Aprovar candidato", "Rejeitar candidato", "Proximo"],
        }

        return stage_suggestions.get(stage, ["Status do wizard", "Ajuda"])

    def validate_context(self, context: DomainContext) -> Tuple[bool, Optional[str]]:
        if not context.auth_token:
            return False, "Token de autenticacao necessario para criar vagas"
        return True, None
