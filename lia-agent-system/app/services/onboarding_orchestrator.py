"""
OnboardingOrchestrator — FSM that controls the recruiter onboarding flow.

States: PENDING → WELCOME → WHATSAPP_INTRO → WHATSAPP_LEARN → AWAITING_LOGIN
        → FIRST_LOGIN → PLATFORM_TOUR → ACTION_CHOICE → JOB_CREATION → COMPLETE

Follows VoiceInterviewStateMachine pattern (FSM + session dataclass + async handlers).
Integrates with: Twilio WhatsApp, Rails API, LLM (Claude), existing job_creation domain.

Apply to: lia-agent-system/app/services/onboarding_orchestrator.py
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class OnboardingPhase(Enum):
    PENDING = "pending"
    WELCOME = "welcome"
    WHATSAPP_INTRO = "whatsapp_intro"
    WHATSAPP_LEARN = "whatsapp_learn"
    AWAITING_LOGIN = "awaiting_login"
    FIRST_LOGIN = "first_login"
    PLATFORM_TOUR = "platform_tour"
    ACTION_CHOICE = "action_choice"
    JOB_CREATION = "job_creation"
    COMPLETE = "complete"
    SETTINGS_EXTRACTION = "settings_extraction"  # P2-2 Sprint A.5


# Valid transitions
TRANSITIONS = {
    OnboardingPhase.PENDING: [OnboardingPhase.WELCOME],
    OnboardingPhase.WELCOME: [OnboardingPhase.WHATSAPP_INTRO, OnboardingPhase.AWAITING_LOGIN],
    OnboardingPhase.WHATSAPP_INTRO: [OnboardingPhase.WHATSAPP_LEARN, OnboardingPhase.AWAITING_LOGIN],
    OnboardingPhase.WHATSAPP_LEARN: [OnboardingPhase.AWAITING_LOGIN],
    OnboardingPhase.AWAITING_LOGIN: [OnboardingPhase.FIRST_LOGIN],
    OnboardingPhase.FIRST_LOGIN: [OnboardingPhase.PLATFORM_TOUR],
    OnboardingPhase.PLATFORM_TOUR: [OnboardingPhase.ACTION_CHOICE],
    OnboardingPhase.ACTION_CHOICE: [OnboardingPhase.JOB_CREATION, OnboardingPhase.SETTINGS_EXTRACTION, OnboardingPhase.COMPLETE],
    OnboardingPhase.JOB_CREATION: [OnboardingPhase.COMPLETE],
    OnboardingPhase.SETTINGS_EXTRACTION: [OnboardingPhase.ACTION_CHOICE, OnboardingPhase.COMPLETE],
    OnboardingPhase.COMPLETE: [],
}


@dataclass
class OnboardingSession:
    session_id: str
    user_id: int
    account_id: int
    user_name: str
    user_email: str
    user_phone: Optional[str] = None

    phase: OnboardingPhase = OnboardingPhase.PENDING
    channel: str = "web"  # whatsapp, email, web

    # WhatsApp context
    whatsapp_conversation_id: Optional[str] = None
    whatsapp_messages: list[dict] = field(default_factory=list)

    # Data collected from WhatsApp Flow
    onboarding_data: dict = field(default_factory=dict)

    # Tour progress
    tour_steps_completed: list[str] = field(default_factory=list)
    tour_current_step: Optional[str] = None

    # Magic link
    magic_link_url: Optional[str] = None

    # Metadata
    onboarding_lia_enabled: bool = True
    invited_by: Optional[str] = None
    created_at: Optional[datetime] = None

    # P2-2 Sprint A.5: settings extraction state (opcional).
    # Quando phase=SETTINGS_EXTRACTION, este campo guarda snapshot JSON
    # do SettingsExtractionStatus do settings_phase module.
    settings_extraction_status_json: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        return self.phase == OnboardingPhase.COMPLETE

    @property
    def progress(self) -> float:
        """Progress 0.0 to 1.0 based on phase."""
        phase_progress = {
            OnboardingPhase.PENDING: 0.0,
            OnboardingPhase.WELCOME: 0.05,
            OnboardingPhase.WHATSAPP_INTRO: 0.15,
            OnboardingPhase.WHATSAPP_LEARN: 0.25,
            OnboardingPhase.AWAITING_LOGIN: 0.30,
            OnboardingPhase.FIRST_LOGIN: 0.35,
            OnboardingPhase.PLATFORM_TOUR: 0.60,
            OnboardingPhase.ACTION_CHOICE: 0.80,
            OnboardingPhase.JOB_CREATION: 0.90,
            OnboardingPhase.COMPLETE: 1.0,
        }
        return phase_progress.get(self.phase, 0.0)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "user_name": self.user_name,
            "phase": self.phase.value,
            "channel": self.channel,
            "progress": self.progress,
            "onboarding_data": self.onboarding_data,
            "tour_steps_completed": self.tour_steps_completed,
            "is_complete": self.is_complete,
            "settings_extraction_status_json": self.settings_extraction_status_json,
        }

    @classmethod
    def from_invite_event(cls, event: dict) -> "OnboardingSession":
        """Create from RabbitMQ user_invited event."""
        payload = event.get("payload", event)
        return cls(
            session_id=str(uuid.uuid4()),
            user_id=payload["user_id"],
            account_id=payload["account_id"],
            user_name=payload.get("name", ""),
            user_email=payload.get("email", ""),
            user_phone=payload.get("phone"),
            magic_link_url=payload.get("magic_link_url"),
            onboarding_lia_enabled=payload.get("onboarding_lia_enabled", True),
            invited_by=payload.get("invited_by"),
            created_at=datetime.utcnow(),
        )


class OnboardingOrchestrator:
    """
    Controls the onboarding flow for a new recruiter.

    Each call to handle_message() or handle_event():
    1. Validates current state
    2. Processes input based on phase
    3. Transitions to next phase if ready
    4. Returns response for the appropriate channel (WhatsApp, email, or web)
    """

    def __init__(self, db=None, llm=None, whatsapp_client=None, rails_client=None):
        self.db = db
        self.llm = llm
        self.whatsapp_client = whatsapp_client
        self.rails_client = rails_client

    # === Entry point: start onboarding ===

    async def start(self, session: OnboardingSession) -> dict:
        """Start onboarding: dispatch welcome via WhatsApp + Email."""
        if not session.onboarding_lia_enabled:
            self._safe_transition(session, OnboardingPhase.AWAITING_LOGIN)
            await self._persist(session)
            return {"action": "skip_lia", "message": "LIA onboarding disabled for this user"}

        self._safe_transition(session, OnboardingPhase.WELCOME)

        responses = []

        # Send WhatsApp welcome (if phone available)
        if session.user_phone and self.whatsapp_client:
            try:
                wa_result = await self.whatsapp_client.send_template(
                    phone=session.user_phone,
                    template_name="lia_welcome_recruiter",
                    variables=[session.user_name, session.invited_by or "Sua empresa"],
                )
                session.whatsapp_conversation_id = wa_result.get("conversation_sid")
                session.channel = "whatsapp"
                responses.append({"channel": "whatsapp", "status": "sent"})
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"[Onboarding] WhatsApp welcome sent to {session.user_phone}")
            except Exception as e:
                logger.warning(f"[Onboarding] WhatsApp send failed: {e}")

        # Email is sent by Rails (already triggered in OnboardingController#invite)
        responses.append({"channel": "email", "status": "sent_by_rails"})

        await self._persist(session)

        # Audit: log onboarding start
        await self._audit("onboarding_start", session, f"Welcome dispatched via {', '.join(r['channel'] for r in responses)}")

        return {
            "action": "welcome_dispatched",
            "session": session.to_dict(),
            "responses": responses,
        }

    # === WhatsApp message handler ===

    async def handle_whatsapp_message(
        self, session: OnboardingSession, message: str
    ) -> dict:
        """Process inbound WhatsApp message and return response."""

        # Store message
        session.whatsapp_messages.append({
            "direction": "inbound",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        if session.phase in (OnboardingPhase.WELCOME, OnboardingPhase.PENDING):
            return await self._handle_whatsapp_intro_start(session, message)

        elif session.phase == OnboardingPhase.WHATSAPP_INTRO:
            return await self._handle_whatsapp_intro(session, message)

        elif session.phase == OnboardingPhase.WHATSAPP_LEARN:
            # Flow data comes via webhook, not message
            return await self._handle_awaiting_flow(session, message)

        elif session.phase == OnboardingPhase.AWAITING_LOGIN:
            return self._build_wa_response(
                session,
                f"Estou te esperando na plataforma, {session.user_name}! "
                f"Clique no link que enviei para acessar sem senha.",
            )

        # Default: any phase
        return self._build_wa_response(
            session,
            f"Oi {session.user_name}! Acesse a plataforma para continuar: {session.magic_link_url}",
        )

    # === WhatsApp Flow handler ===

    async def handle_whatsapp_flow_complete(
        self, session: OnboardingSession, flow_data: dict
    ) -> dict:
        """Process WhatsApp Flow completion data."""
        session.onboarding_data = {
            **session.onboarding_data,
            **flow_data,
        }
        self._safe_transition(session, OnboardingPhase.AWAITING_LOGIN)
        session.channel = "whatsapp"

        # Generate personalized response based on flow data
        focus = flow_data.get("hiring_focus", "recrutamento")
        pain = flow_data.get("biggest_pain", "triagem")

        response_text = (
            f"Perfeito, {session.user_name}! Agora eu sei que voce foca em {focus} "
            f"e sua maior dor e {pain}. Com isso eu vou:\n\n"
            f"• Priorizar avaliacoes para esse perfil\n"
            f"• Calibrar perguntas de triagem adequadas\n"
            f"• Sugerir candidatos com match mais preciso\n\n"
            f"Vamos para a plataforma? Sem precisar criar senha:"
        )

        await self._persist(session)
        await self._audit("whatsapp_flow_complete", session, f"Focus: {focus}, Pain: {pain}")

        return {
            "action": "flow_complete",
            "response_text": response_text,
            "cta_url": session.magic_link_url,
            "session": session.to_dict(),
        }

    # === Web event handler ===

    async def handle_web_event(
        self, session: OnboardingSession, event_type: str, data: dict = None
    ) -> dict:
        """Process web events (first_login, tour_step, action_choice, etc.)"""

        # P2-2 Sprint A.7: explicit trigger to enter SETTINGS_EXTRACTION phase.
        # Frontend dispatcha "start_settings_extraction" quando o banner do
        # onboarding chat e acionado (Sprint B.1). NAO usa _safe_transition
        # porque SETTINGS_EXTRACTION nao tem path canonical no FSM TRANSITIONS
        # (eh um side-flow opt-in, nao um proximo passo do flow principal).
        if event_type == "start_settings_extraction":
            session.phase = OnboardingPhase.SETTINGS_EXTRACTION
            return await self.handle_settings_extraction_message(session, "")

        # P2-2 Sprint A.7: route user messages quando session ja esta dentro
        # do settings extraction flow. Aceita "message" ou "text" no payload.
        if session.phase == OnboardingPhase.SETTINGS_EXTRACTION:
            payload = data or {}
            message = payload.get("message") or payload.get("text") or ""
            return await self.handle_settings_extraction_message(session, message)

        if event_type == "magic_link_used":
            return await self._handle_first_login(session)

        elif event_type == "tour_step_completed":
            step_id = (data or {}).get("step_id", "")
            if step_id and step_id not in session.tour_steps_completed:
                session.tour_steps_completed.append(step_id)
            await self._persist(session)
            return {"action": "step_recorded", "session": session.to_dict()}

        elif event_type == "tour_complete":
            self._safe_transition(session, OnboardingPhase.ACTION_CHOICE)
            await self._persist(session)
            return await self._handle_action_choice(session)

        elif event_type == "action_selected":
            action = (data or {}).get("action", "explore")
            return await self._handle_action_selected(session, action)

        elif event_type == "onboarding_complete":
            self._safe_transition(session, OnboardingPhase.COMPLETE)
            await self._persist(session)
            return {"action": "onboarding_complete", "session": session.to_dict()}

        return {"action": "unknown_event", "event_type": event_type}

    # === Internal handlers ===

    async def _handle_whatsapp_intro_start(
        self, session: OnboardingSession, message: str
    ) -> dict:
        """User responded to welcome template — start LIA introduction."""
        self._safe_transition(session, OnboardingPhase.WHATSAPP_INTRO)

        response_text = (
            f"Que bom, {session.user_name}! Deixa eu me apresentar direito.\n\n"
            f"Eu sou uma assistente pessoal de recrutamento — mas diferente de um chatbot comum:\n\n"
            f"✦ Eu APRENDO com voce — quanto mais trabalhamos juntos, melhor eu fico\n"
            f"✦ Eu garanto recrutamento IGUALITARIO — verifico bias e linguagem inclusiva\n"
            f"✦ Voce sempre tem a palavra final — eu sugiro, voce decide\n\n"
            f"E voce pode falar comigo por texto ou AUDIO 🎤"
        )

        # Store outbound message
        session.whatsapp_messages.append({
            "direction": "outbound",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
        })

        await self._persist(session)

        return {
            "action": "intro_sent",
            "response_text": response_text,
            "buttons": [
                {"id": "want_more", "title": "Quero saber mais!"},
                {"id": "go_platform", "title": "Ver na plataforma"},
                {"id": "go_direct", "title": "Vamos direto"},
            ],
            "session": session.to_dict(),
        }

    async def _handle_whatsapp_intro(
        self, session: OnboardingSession, message: str
    ) -> dict:
        """Handle follow-up messages during WhatsApp intro phase."""
        msg_lower = message.lower().strip()

        # User wants more info
        if any(kw in msg_lower for kw in ["mais", "saber", "want", "quero", "sim"]):
            response_text = (
                "Posso te ajudar em todo o processo de recrutamento:\n\n"
                "📝 Criar vagas com JD enriquecido automaticamente\n"
                "🎯 Gerar perguntas de triagem calibradas por competencia\n"
                "🔍 Buscar candidatos com sourcing inteligente\n"
                "📞 Triar por ligacao, chat ou WhatsApp\n"
                "📊 Emitir pareceres detalhados\n"
                "📅 Agendar entrevistas\n"
                "💬 Conversar via Teams com gestores\n"
                "📈 Enviar reports semanais\n\n"
                "Agora, pra eu te ajudar melhor, preciso entender como voce trabalha. "
                "Posso te fazer 4 perguntas rapidas? Leva menos de 1 minuto."
            )

            session.whatsapp_messages.append({
                "direction": "outbound",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self._persist(session)

            return {
                "action": "capabilities_sent",
                "response_text": response_text,
                "trigger_flow": True,  # Signal to send WhatsApp Flow next
                "session": session.to_dict(),
            }

        # User wants to go to platform directly
        elif any(kw in msg_lower for kw in ["plataforma", "direto", "ponto", "link", "acessar"]):
            self._safe_transition(session, OnboardingPhase.AWAITING_LOGIN)
            await self._persist(session)

            return {
                "action": "skip_to_login",
                "response_text": (
                    "Claro! Clique abaixo para acessar — sem precisar criar senha:"
                ),
                "cta_url": session.magic_link_url,
                "session": session.to_dict(),
            }

        # Default: try to understand with LLM
        else:
            return await self._handle_free_conversation(session, message)

    async def _handle_awaiting_flow(
        self, session: OnboardingSession, message: str
    ) -> dict:
        """User sends message while we're waiting for Flow completion."""
        return self._build_wa_response(
            session,
            "Estou aguardando suas respostas no formulario. "
            "Se preferir, pode acessar a plataforma direto pelo link que enviei!",
        )

    async def _handle_first_login(self, session: OnboardingSession) -> dict:
        """User just logged in via magic link."""
        self._safe_transition(session, OnboardingPhase.FIRST_LOGIN)
        session.channel = "web"

        # Build welcome message that references WhatsApp context
        has_wa_data = bool(session.onboarding_data)
        focus = session.onboarding_data.get("hiring_focus", "")
        pain = session.onboarding_data.get("biggest_pain", "")

        if has_wa_data:
            welcome = (
                f"Oi {session.user_name}! Que bom te ver por aqui! 🎉\n\n"
                f"Ja nos falamos no WhatsApp e preparei tudo com base no que voce me contou. "
                f"Voce foca em {focus} e sua maior dor e {pain}.\n\n"
                f"Vou te mostrar como a plataforma funciona — leva menos de 3 minutos."
            )
        else:
            welcome = (
                f"Oi {session.user_name}! Sou a LIA, sua assistente de recrutamento. 🎉\n\n"
                f"Vou te mostrar como a plataforma funciona e como posso te ajudar no dia-a-dia. "
                f"Leva menos de 3 minutos."
            )

        self._safe_transition(session, OnboardingPhase.PLATFORM_TOUR)
        await self._persist(session)

        return {
            "action": "first_login_welcome",
            "welcome_message": welcome,
            "whatsapp_context": session.whatsapp_messages,  # For context injection
            "onboarding_data": session.onboarding_data,
            "session": session.to_dict(),
        }

    async def _handle_action_choice(self, session: OnboardingSession) -> dict:
        """Present action choices after tour."""
        return {
            "action": "present_choices",
            "message": (
                "Agora que voce conhece a plataforma, vamos colocar a mao na massa!\n\n"
                "Voce ja tem alguma vaga aberta que quer trabalhar?"
            ),
            "choices": [
                {"id": "create_job", "label": "Criar uma vaga nova", "icon": "sparkles"},
                {"id": "import_ats", "label": "Tenho vagas no meu ATS", "icon": "clipboard"},
                {"id": "existing_jobs", "label": "Ver vagas existentes", "icon": "folder"},
                {"id": "explore", "label": "So quero explorar por agora", "icon": "eye"},
            ],
            "session": session.to_dict(),
        }

    async def _handle_action_selected(
        self, session: OnboardingSession, action: str
    ) -> dict:
        """Handle user's action choice."""
        if action == "create_job":
            self._safe_transition(session, OnboardingPhase.JOB_CREATION)
            await self._persist(session)
            return await self._delegate_job_creation(session)

        elif action == "import_ats":
            self._safe_transition(session, OnboardingPhase.JOB_CREATION)
            await self._persist(session)
            return {
                "action": "import_ats",
                "message": "Qual ATS voce usa? Posso importar suas vagas abertas para completar o JD e criar perguntas de triagem.",
                "session": session.to_dict(),
            }

        elif action == "existing_jobs":
            self._safe_transition(session, OnboardingPhase.JOB_CREATION)
            await self._persist(session)
            return {
                "action": "list_jobs",
                "message": "Vou listar suas vagas. Escolha uma para completar com JD enriquecido e perguntas WSI.",
                "session": session.to_dict(),
            }

        else:  # explore
            self._safe_transition(session, OnboardingPhase.COMPLETE)
            await self._persist(session)
            await self._sync_rails_state(session)
            return {
                "action": "explore",
                "message": "Fique a vontade! Estou aqui quando precisar. Pode me chamar a qualquer momento pelo chat, por texto ou por audio 🎤",
                "session": session.to_dict(),
            }

    async def _handle_free_conversation(
        self, session: OnboardingSession, message: str
    ) -> dict:
        """Use LLM to handle unexpected messages during WhatsApp intro."""
        # Use SystemPromptBuilder for persona-consistent responses
        from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
        _onboarding_system = SystemPromptBuilder.build(
            agent_type="recruiter_assistant",
            user_name=session.user_name or "",
            extra_instructions="Você está no fluxo de onboarding. Seja acolhedora e guie o recrutador passo a passo.",
        )
        if not self.llm:
            return self._build_wa_response(
                session,
                "Desculpe, nao entendi. Quer que eu te explique o que posso fazer? Responda SIM ou acesse o link para ir direto para a plataforma.",
            )

        try:
            # PII masking: don't send real name/email to LLM
            masked_name = f"Recrutador_{session.user_id}"
            masked_message = message  # User messages are their own input, OK to send

            prompt = (
                f"Voce e a LIA, assistente de IA de recrutamento da WeDOTalent. "
                f"Esta fazendo onboarding de um novo recrutador via WhatsApp. "
                f"Ele disse: '{masked_message}'. "
                f"Responda de forma amigavel e breve (max 3 frases). "
                f"Se possivel, direcione para fazer o onboarding ou acessar a plataforma. "
                f"Responda em portugues do Brasil."
            )
            response = await self.llm.ainvoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)

            # FairnessGuard: check LLM output for bias
            try:
                from app.shared.compliance.fairness_guard import FairnessGuard
                guard = FairnessGuard()
                check_result = guard.check({"response": text})
                if check_result.get("is_blocked"):
                    logger.warning(f"[Onboarding] FairnessGuard blocked response: {check_result}")
                    text = "Me desculpe, vou reformular. Quer saber mais sobre a plataforma ou prefere acessar direto?"
                elif check_result.get("soft_warnings"):
                    logger.info(f"[Onboarding] FairnessGuard warnings: {check_result['soft_warnings']}")
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"[Onboarding] FairnessGuard check failed: {e}")

            session.whatsapp_messages.append({
                "direction": "outbound",
                "content": text,
                "timestamp": datetime.utcnow().isoformat(),
            })
            await self._persist(session)

            return {
                "action": "llm_response",
                "response_text": text,
                "session": session.to_dict(),
            }
        except Exception as e:
            logger.warning(f"[Onboarding] LLM call failed: {e}")
            return self._build_wa_response(session, "Me desculpe, tive um problema. Tente novamente ou acesse o link para ir para a plataforma.")

    # === Helpers ===

    async def handle_settings_extraction_message(
        self,
        session: OnboardingSession,
        message: str,
    ) -> dict:
        """P2-2 Sprint A.5 — handler do flow conversacional de settings.

        Delega ao onboarding_settings_runner que orquestra:
        loader (next question) -> extractor (LLM) -> runner (persist via tool).

        Returns dict canonical:
            {
                "phase": str,
                "message": str,
                "is_complete": bool,
                "progress_percent": int,
            }
        """
        from app.services.onboarding_settings_runner import (
            start as runner_start,
            process_message as runner_process,
            RunnerResponse,
        )
        from app.services.onboarding_settings_phase import (
            SettingsExtractionStatus,
            SettingsExtractionState,
        )
        import json as _json

        # company_id derivado de account_id (tenant pass-through canonical do orchestrator).
        company_id = str(session.account_id)
        user_id_str = str(session.user_id) if session.user_id is not None else None

        # Restore status do session.settings_extraction_status_json (ou novo).
        status = None
        if session.settings_extraction_status_json:
            try:
                raw = _json.loads(session.settings_extraction_status_json)
                status = SettingsExtractionStatus(
                    state=SettingsExtractionState(raw.get("state", "intro")),
                    current_block_id=raw.get("current_block_id"),
                    answered_fields=raw.get("answered_fields", {}),
                    pending_extraction=raw.get("pending_extraction", {}),
                    skipped_fields=set(raw.get("skipped_fields", [])),
                    last_asked_field=raw.get("last_asked_field"),
                )
            except Exception as e:
                logger.warning(
                    "settings_extraction_status_json invalid for session %s: %s - re-iniciando",
                    session.session_id, e,
                )
                status = None

        # Primeira chamada (sem status) -> start.
        # Apos start, status fica em state=INTRO ate primeira user response.
        # runner_process trata transicao INTRO -> ASKING via handle_user_response.
        # Bug fix Sprint A.8: NAO re-rodar runner_start quando status restored=INTRO
        # — isso causava loop infinito INTRO. (Flagged pelo E2E agent.)
        if status is None:
            response: RunnerResponse = await runner_start(company_id=company_id)
        else:
            response = await runner_process(
                status=status,
                user_message=message,
                company_id=company_id,
                user_id=user_id_str,
            )

        # Persiste novo status como JSON em session.
        # Bug fix Sprint A.8: incluir last_asked_field pra preservar
        # contexto de re-ask/skip entre requests. (Flagged pelo E2E agent.)
        session.settings_extraction_status_json = _json.dumps({
            "state": response.status.state.value,
            "current_block_id": response.status.current_block_id,
            "answered_fields": response.status.answered_fields,
            "pending_extraction": response.status.pending_extraction,
            "skipped_fields": list(response.status.skipped_fields),
            "last_asked_field": response.status.last_asked_field,
        })

        await self._audit(
            "settings_extraction_step",
            session,
            f"progress={response.progress_percent}% state={response.status.state.value}",
        )

        await self._persist(session)

        return {
            "phase": OnboardingPhase.SETTINGS_EXTRACTION.value,
            "message": response.user_message,
            "is_complete": response.is_complete,
            "progress_percent": response.progress_percent,
        }

    async def _audit(self, action: str, session: OnboardingSession, details: str = "") -> None:
        """Non-blocking audit log."""
        try:
            from app.shared.compliance.audit_service import AuditService
            audit = AuditService()
            await audit.log_output(
                company_id=session.account_id,
                session_id=session.session_id,
                agent_used="onboarding",
                input_text=f"Phase: {session.phase.value}",
                output_text=details[:500],
                action_executed=action,
                candidate_id=None,
                job_vacancy_id=None,
                fairness_flags=[],
            )
        except Exception:
            pass  # Non-blocking

    def _build_wa_response(self, session: OnboardingSession, text: str) -> dict:
        session.whatsapp_messages.append({
            "direction": "outbound",
            "content": text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {
            "action": "wa_message",
            "response_text": text,
            "session": session.to_dict(),
        }

    def _validate_transition(self, current: OnboardingPhase, target: OnboardingPhase) -> bool:
        return target in TRANSITIONS.get(current, [])

    def _safe_transition(self, session: OnboardingSession, target: OnboardingPhase) -> None:
        """Transition with validation. Logs warning on invalid but allows (non-blocking)."""
        if not self._validate_transition(session.phase, target):
            logger.warning(
                f"[Onboarding] Invalid transition {session.phase.value} → {target.value} "
                f"for user {session.user_id}. Allowed: {[t.value for t in TRANSITIONS.get(session.phase, [])]}"
            )
        session.phase = target

    async def _sync_rails_state(self, session: OnboardingSession) -> None:
        """Sync onboarding state back to Rails (canonical source)."""
        if not self.rails_client:
            # Fallback: try direct HTTP call
            try:
                import httpx
                import os
                rails_url = os.getenv("RAILS_BACKEND_URL")
                if not rails_url:
                    logger.debug("[Onboarding] RAILS_BACKEND_URL not set -- skipping Rails sync (rails-elimination)")
                    return
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Update onboarding session phase
                    internal_token = os.getenv("INTERNAL_API_TOKEN")
                    if not internal_token:
                        logger.warning("[Onboarding] INTERNAL_API_TOKEN not set -- skipping Rails sync")
                        return
                    headers = {"Authorization": f"Bearer {internal_token}", "Content-Type": "application/json", "X-Internal": "true"}

                    await client.patch(
                        f"{rails_url}/v1/onboarding/progress",
                        json={"phase": session.phase.value},
                        headers=headers,
                    )
                    # If complete, update user activation_state
                    if session.is_complete:
                        await client.patch(
                            f"{rails_url}/v1/users/edit/{session.user_id}",
                            json={"activation_state": "active", "onboarding_completed_at": datetime.utcnow().isoformat()},
                            headers=headers,
                        )
            except Exception as e:
                logger.warning(f"[Onboarding] Rails sync failed (non-blocking): {e}")

    async def _delegate_job_creation(self, session: OnboardingSession, message: str = "") -> dict:
        """Delegate to existing job_creation domain for wizard flow."""
        try:
            # Send message to chat context that triggers job_creation
            # The supervisor will route "Criar vaga" to job_creation domain
            return {
                "action": "start_wizard",
                "delegate_to": "job_creation",
                "message": message or "Descreva a vaga que quer criar. Pode ser simples — 'Dev Python Senior' — que eu cuido do resto.",
                "chat_command": "Criar nova vaga",  # This triggers supervisor routing
                "session": session.to_dict(),
            }
        except Exception as e:
            logger.warning(f"[Onboarding] Job creation delegation failed: {e}")
            return {
                "action": "delegation_failed",
                "message": "Me desculpe, tive um problema ao iniciar a criacao da vaga. Tente digitar 'Criar nova vaga' no chat.",
                "session": session.to_dict(),
            }

    async def _persist(self, session: OnboardingSession) -> None:
        """Persist session state to database."""
        if not self.db:
            return
        try:
            await self.db.execute(
                """
                INSERT INTO onboarding_agent_state (id, user_id, account_id, phase, channel, session_data, whatsapp_context, onboarding_metadata, settings_extraction_status_json)
                VALUES (:id, :user_id, :account_id, :phase, :channel, :session_data, :whatsapp_context, :metadata, :settings_json)
                ON CONFLICT (user_id) DO UPDATE SET
                    phase = :phase,
                    channel = :channel,
                    session_data = :session_data,
                    whatsapp_context = :whatsapp_context,
                    onboarding_metadata = :metadata,
                    settings_extraction_status_json = :settings_json,
                    updated_at = NOW()
                """,
                {
                    "id": session.session_id,
                    "user_id": session.user_id,
                    "account_id": session.account_id,
                    "phase": session.phase.value,
                    "channel": session.channel,
                    "session_data": json.dumps(session.to_dict()),
                    "whatsapp_context": json.dumps(session.whatsapp_messages),
                    "metadata": json.dumps(session.onboarding_data),
                    "settings_json": session.settings_extraction_status_json,
                },
            )
        except Exception as e:
            logger.warning(f"[Onboarding] Persist failed (non-blocking): {e}")
