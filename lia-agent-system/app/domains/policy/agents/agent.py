"""
PolicySetupAgent — Conducts the 19-question onboarding flow for CompanyHiringPolicy.

Blocks:
1. Pipeline e Processo (Q1-Q4)
2. Agendamento (Q5-Q8)
3. Comunicacao (Q9-Q12)
4. Triagem (Q13-Q15)
5. Autonomia da LIA (Q16-Q19)

The agent uses Claude to:
- Ask questions in natural Portuguese
- Parse natural language responses ("terça a quinta" -> ["tue","wed","thu"])
- Save extracted data to CompanyHiringPolicy via API
- Manage block transitions and progress

Compliance gates (Audit A2 — task #316):
- LangGraphReActBase + EnhancedAgentMixin inheritance for shared infrastructure.
- FairnessGuard pre-check on every user message AND post-check on extracted
  policy values (a hiring-policy field that says "prefer male candidates" is
  exactly what the guard must block).
- audit_service.log_decision on each policy mutation with policy_diff
  (company_id, actor_user_id, old_value, new_value).
- tenant_llm_context: company_id is set on the per-request contextvar so
  LLM calls resolve the tenant's provider/key.
- pii_masking.strip_pii_for_llm_prompt is applied to free-text user messages
  before they are forwarded to the LLM (LGPD Art. 12 — minimização).
- SystemPromptBuilder.build composes the policy-domain system prompt header.
"""
import json
import logging
from typing import Any

from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase

from app.domains.policy.agents.stage_context import (
    BLOCK_NAMES,
    PolicySetupSession,
    get_or_create_session,
)
from app.domains.policy.agents.system_prompt import EXTRACTION_PROMPT, REPLY_PROMPT
from app.domains.ai.services.llm import LLMService
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.pii_masking import strip_pii_for_llm_prompt
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
from app.shared.tenant_llm_context import get_current_llm_tenant

logger = logging.getLogger(__name__)


class _FairnessGuardError:
    """Synthetic FairnessGuard result used when the guard itself raises.

    Used by ``PolicySetupAgent._fairness_check`` to fail closed: any runtime
    error from the guard is converted into a block so a discriminatory policy
    cannot be persisted while the guard is degraded.
    """

    is_blocked = True
    category = "guard_error"
    blocked_terms: list[str] = []
    soft_warnings: list[str] = []

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.educational_message = (
            "Não foi possível validar esta política contra os critérios de "
            "equidade no momento. Por segurança, a alteração foi bloqueada. "
            "Tente novamente em instantes."
        )


class PolicySetupAgent(LangGraphReActBase, EnhancedAgentMixin):
    """Sequential 19-question hiring-policy onboarding agent.

    Inherits from LangGraphReActBase to gain shared compliance plumbing
    (PII sanitization, FairnessGuard hook, SystemPromptBuilder, audit
    callback) but exposes the legacy ``process_message`` interface used by
    the chat orchestrator. The ReAct loop itself is not exercised because
    the flow is a deterministic questionnaire, not a tool-using graph.
    """

    DOMAIN_INSTRUCTIONS = (
        "Você conduz a configuração das políticas de contratação da empresa "
        "via questionário linear. Toda saída precisa respeitar critérios de "
        "equidade — políticas que privilegiem ou excluam candidatos por "
        "atributos protegidos são bloqueadas pelo FairnessGuard."
    )

    # PII sanitization is handled explicitly in _safe_invoke_llm (we do not
    # use the inherited LangGraph message pipeline).
    _enable_pii_strip = True

    def __init__(self) -> None:
        try:
            super().__init__()
        except Exception as exc:  # pragma: no cover — fail-safe for tests w/o checkpointer
            logger.debug("[PolicySetupAgent] base init skipped: %s", exc)
            self._checkpointer = None
            self._compiled = None
        try:
            self._setup_enhanced(domain="policy")
        except Exception as exc:  # pragma: no cover
            logger.debug("[PolicySetupAgent] enhanced setup skipped: %s", exc)
        self._llm: LLMService | None = None
        self._fairness_guard = FairnessGuard()

    # ------------------------------------------------------------------
    # LangGraphReActBase abstract requirements (stubs — not exercised).
    # ------------------------------------------------------------------
    @property
    def domain_name(self) -> str:
        return "policy_setup"

    @property
    def available_tools(self) -> list[str]:
        return []

    def _get_tools(self) -> list:
        return []

    def _build_graph(self) -> Any:  # pragma: no cover — graph not used
        return None

    @property
    def llm(self) -> LLMService:
        if not self._llm:
            self._llm = LLMService()
        return self._llm

    # ------------------------------------------------------------------
    # Public entrypoint (legacy interface used by chat orchestrator).
    # ------------------------------------------------------------------
    async def process_message(
        self,
        message: str,
        company_id: str,
        session_id: str,
        current_policy: dict[str, Any],
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        # ── tenant_llm_context: ensure LLM calls resolve the tenant ─────
        token = self._set_tenant_context(company_id)
        try:
            # ── FairnessGuard pre-check on raw user input ──────────────
            blocked = self._fairness_check(message)
            if blocked is not None:
                await self._audit_block(company_id, actor_user_id, message, blocked)
                return self._compliance_blocked_response(blocked, company_id)

            session = get_or_create_session(company_id, session_id, current_policy)

            if session.completed:
                return self._completed_response(session)

            if message.strip().lower() in ["", "iniciar", "comecar", "start", "oi", "ola", "vamos"]:
                return self._welcome_response(session)

            if session.waiting_for_block_confirmation:
                return await self._handle_block_transition(message, session)

            return await self._process_answer(message, session, actor_user_id)
        finally:
            self._reset_tenant_context(token)

    # LangGraph-native entrypoint — thin adapter onto process_message so any
    # generic dispatch (router, tests, future orchestrator) keeps working.
    async def process(self, input):  # type: ignore[override]
        if not isinstance(input, dict):
            raise TypeError(
                "PolicySetupAgent.process expects a dict with keys "
                "{message, company_id, session_id, current_policy}."
            )
        return await self.process_message(
            message=input.get("message") or input.get("user_message") or "",
            company_id=str(input.get("company_id") or ""),
            session_id=str(input.get("session_id") or input.get("conversation_id") or ""),
            current_policy=input.get("current_policy") or {},
            actor_user_id=input.get("actor_user_id") or input.get("user_id"),
        )

    # ------------------------------------------------------------------
    # Compliance helpers
    # ------------------------------------------------------------------
    def _set_tenant_context(self, company_id: str):
        try:
            from app.middleware.auth_enforcement import _current_company_id
            if get_current_llm_tenant() != company_id and company_id:
                return _current_company_id.set(company_id)
        except Exception as exc:
            logger.debug("[PolicySetupAgent] tenant_llm_context set skipped: %s", exc)
        return None

    def _reset_tenant_context(self, token) -> None:
        if token is None:
            return
        try:
            from app.middleware.auth_enforcement import _current_company_id
            _current_company_id.reset(token)
        except Exception as exc:
            logger.debug("[PolicySetupAgent] tenant_llm_context reset skipped: %s", exc)

    def _fairness_check(self, text: str):
        """Return a FairnessCheckResult-like object if blocked, else None.

        Fail-closed: if FairnessGuard itself raises, we return a synthetic
        block instead of allowing the policy mutation through. Hiring-policy
        authoring is too high-risk to silently pass on guard errors.
        """
        if not text:
            return None
        try:
            result = self._fairness_guard.check(text)
        except Exception as exc:
            logger.error(
                "[PolicySetupAgent] FairnessGuard raised — failing closed: %s", exc
            )
            return _FairnessGuardError(str(exc))
        if result and getattr(result, "is_blocked", False):
            return result
        return None

    def _compliance_blocked_response(self, fg_result, company_id: str) -> dict[str, Any]:
        msg = (
            getattr(fg_result, "educational_message", None)
            or "Sua solicitação contém critérios que podem gerar viés. "
               "Reformule usando competências e experiência objetivas."
        )
        return {
            "reply": msg,
            "current_block": None,
            "current_question": 0,
            "total_questions": 19,
            "setup_progress": 0,
            "updated_fields": {},
            "block_completed": False,
            "all_completed": False,
            "compliance_blocked": True,
            "fairness_category": getattr(fg_result, "category", None),
        }

    async def _audit_block(
        self,
        company_id: str,
        actor_user_id: str | None,
        message: str,
        fg_result,
    ) -> None:
        try:
            from app.shared.compliance.audit_service import audit_service
            await audit_service.log_decision(
                company_id=str(company_id),
                agent_name="policy_setup_agent",
                decision_type="policy_update",
                action="fairness_block",
                decision="blocked",
                reasoning=[
                    f"FairnessGuard blocked policy input (category={getattr(fg_result, 'category', '?')})",
                ],
                criteria_used=[getattr(fg_result, "category", "fairness")],
                human_review_required=True,
                actor_user_id=actor_user_id,
            )
        except Exception as exc:  # pragma: no cover
            logger.debug("[PolicySetupAgent] block audit skipped: %s", exc)

    async def _audit_policy_change(
        self,
        company_id: str,
        actor_user_id: str | None,
        question: dict[str, Any],
        old_value: Any,
        new_value: Any,
        completed: bool,
    ) -> None:
        try:
            from app.shared.compliance.audit_service import audit_service
            policy_diff = {
                "field": question.get("field", "unknown"),
                "block": question.get("block_name", ""),
                "question_id": question.get("id"),
                "old_value": old_value,
                "new_value": new_value,
            }
            await audit_service.log_decision(
                company_id=str(company_id),
                agent_name="policy_setup_agent",
                decision_type="policy_update",
                action=f"policy_field_updated:{question.get('field', 'unknown')}",
                decision="completed" if completed else "in_progress",
                reasoning=[
                    f"Q{question.get('id')}: {(question.get('question') or '')[:80]}",
                    f"policy_diff={json.dumps(policy_diff, ensure_ascii=False, default=str)}",
                ],
                criteria_used=[question.get("field", "")],
                actor_user_id=actor_user_id,
            )
        except Exception as exc:  # pragma: no cover
            logger.debug("[PolicySetupAgent] AuditService skipped: %s", exc)

    def _build_system_header(self, session: PolicySetupSession) -> str:
        try:
            return SystemPromptBuilder.build(
                agent_type=self.domain_name,
                company_id=str(session.company_id) if getattr(session, "company_id", None) else "",
                tenant_context_snippet=f"company_id={session.company_id}",
                user_role="hiring_manager",
                context_page="policy_setup",
                intent="configure_hiring_policy",
            )
        except Exception as exc:
            logger.debug("[PolicySetupAgent] SystemPromptBuilder skipped: %s", exc)
            return ""

    async def _safe_invoke_llm(self, prompt: str, session: PolicySetupSession | None = None) -> str:
        """LLM invocation that PII-masks the prompt and prepends the system header."""
        sanitized = strip_pii_for_llm_prompt(prompt) if self._enable_pii_strip else prompt
        if session is not None:
            header = self._build_system_header(session)
            if header:
                sanitized = f"{header}\n\n{self.DOMAIN_INSTRUCTIONS}\n\n---\n\n{sanitized}"
        return await self.llm.safe_invoke(sanitized, provider="claude")

    # ------------------------------------------------------------------
    # Original flow logic (unchanged behaviour, instrumented for compliance).
    # ------------------------------------------------------------------
    def _welcome_response(self, session: PolicySetupSession) -> dict[str, Any]:
        q = session.get_current_question()
        if not q:
            return self._completed_response(session)

        reply = (
            f"Ola! Vou te ajudar a configurar as politicas de contratacao da sua empresa. "
            f"Sao 19 perguntas divididas em 5 blocos. Voce pode pular qualquer pergunta "
            f"e voltar depois.\n\n"
            f"Vamos comecar pelo bloco **{q['block_name']}**.\n\n"
            f"{q['question']}"
        )

        return {
            "reply": reply,
            "current_block": q["block_name"],
            "current_question": q["id"],
            "total_questions": 19,
            "setup_progress": self._calc_progress(session),
            "updated_fields": {},
            "block_completed": False,
            "all_completed": False,
        }

    async def _process_answer(
        self,
        message: str,
        session: PolicySetupSession,
        actor_user_id: str | None = None,
    ) -> dict[str, Any]:
        q = session.get_current_question()
        if not q:
            return self._completed_response(session)

        extracted = await self._extract_value(message, q, session)

        # ── FairnessGuard post-check on extracted policy value ─────────
        # A user could bypass the input check by phrasing the bias as a
        # legitimate-looking policy value (e.g. free-text "perfil ideal").
        # We re-check the JSON-serialised extracted value here.
        try:
            extracted_text = json.dumps(extracted, ensure_ascii=False, default=str)
        except Exception:
            extracted_text = str(extracted)
        post_block = self._fairness_check(extracted_text)
        if post_block is not None:
            await self._audit_block(
                str(session.company_id),
                actor_user_id,
                f"extracted:{extracted_text}",
                post_block,
            )
            return self._compliance_blocked_response(post_block, str(session.company_id))

        update_data = self._build_update(q, extracted)
        old_snapshot: dict[str, Any] = {}
        for block_key in update_data.keys():
            existing = session.current_policy.get(block_key)
            if isinstance(existing, dict):
                old_snapshot[block_key] = dict(existing)
            elif isinstance(existing, list):
                old_snapshot[block_key] = list(existing)
            else:
                old_snapshot[block_key] = existing
        session.answered_questions[q["id"]] = extracted

        for block_key, block_data in update_data.items():
            if block_key in session.current_policy:
                if isinstance(session.current_policy[block_key], dict) and isinstance(block_data, dict):
                    session.current_policy[block_key].update(block_data)
                else:
                    session.current_policy[block_key] = block_data
            else:
                session.current_policy[block_key] = block_data

        is_block_end = session.is_block_transition()

        if is_block_end:
            session.waiting_for_block_confirmation = True
            reply = await self._generate_block_end_reply(message, q, extracted, session)
        else:
            session.advance_to_next_question()
            next_q = session.get_current_question()
            if next_q:
                reply = await self._generate_reply(message, q, extracted, next_q, session)
            else:
                session.completed = True
                reply = await self._generate_completion_reply(message, q, extracted, session)

        await self._audit_policy_change(
            company_id=str(session.company_id),
            actor_user_id=actor_user_id,
            question=q,
            old_value=old_snapshot,
            new_value=update_data,
            completed=session.completed,
        )

        return {
            "reply": reply,
            "current_block": q["block_name"],
            "current_question": q["id"],
            "total_questions": 19,
            "setup_progress": self._calc_progress(session),
            "updated_fields": update_data,
            "block_completed": is_block_end,
            "all_completed": session.completed,
            "answered_field": q.get("field"),
        }

    async def _handle_block_transition(
        self, message: str, session: PolicySetupSession
    ) -> dict[str, Any]:
        is_continue = self._is_confirmation(message)
        session.waiting_for_block_confirmation = False

        if is_continue:
            session.advance_to_next_question()
            q = session.get_current_question()
            if not q:
                session.completed = True
                return self._completed_response(session)

            reply = (
                f"Otimo! Vamos para o bloco **{q['block_name']}**.\n\n"
                f"{q['question']}"
            )
            return {
                "reply": reply,
                "current_block": q["block_name"],
                "current_question": q["id"],
                "total_questions": 19,
                "setup_progress": self._calc_progress(session),
                "updated_fields": {},
                "block_completed": False,
                "all_completed": False,
            }
        else:
            return {
                "reply": (
                    "Sem problema! As configuracoes que fizemos ja foram salvas. "
                    "Voce pode voltar quando quiser para continuar de onde parou."
                ),
                "current_block": session.get_current_block_name(),
                "current_question": session.current_question_index + 1,
                "total_questions": 19,
                "setup_progress": self._calc_progress(session),
                "updated_fields": {},
                "block_completed": False,
                "all_completed": False,
            }

    def _is_confirmation(self, message: str) -> bool:
        msg = message.strip().lower()
        positive = [
            "sim", "pode", "vamos", "avancar", "proxima", "ok", "confirmo",
            "esta bom", "perfeito", "claro", "com certeza", "bora",
            "continua", "continuar", "proximo", "yes", "s", "siga",
            "va em frente", "manda", "seguir", "prosseguir",
        ]
        return any(p in msg for p in positive)

    async def _extract_value(
        self,
        message: str,
        question: dict[str, Any],
        session: PolicySetupSession | None = None,
    ) -> Any:
        try:
            prompt = EXTRACTION_PROMPT.format(
                question=question["question"],
                field=question["field"],
                type_hint=question["type"],
                answer=message,
                default=json.dumps(question["default"]),
            )
            content = await self._safe_invoke_llm(prompt, session=session)
            content = (content or "").strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            parsed = json.loads(content)
            return parsed.get("value", question["default"])
        except Exception as e:
            logger.warning(f"LLM extraction failed for Q{question['id']}: {e}")
            return self._fallback_extract(message, question)

    def _fallback_extract(self, message: str, question: dict[str, Any]) -> Any:
        msg = message.strip().lower()
        q_type = question["type"]

        if q_type == "boolean":
            if any(w in msg for w in ["sim", "pode", "claro", "yes", "s"]):
                return True
            if any(w in msg for w in ["nao", "no", "n", "prefiro nao"]):
                return False
            return question["default"]

        if q_type == "integer":
            import re
            numbers = re.findall(r'\d+', msg)
            if numbers:
                return int(numbers[0])
            if "uma hora" in msg or "1 hora" in msg:
                return 60
            return question["default"]

        if q_type == "channel":
            if "ambos" in msg or "both" in msg or "dois" in msg:
                return "both"
            if "whatsapp" in msg or "whats" in msg or "zap" in msg:
                return "whatsapp"
            if "email" in msg or "e-mail" in msg:
                return "email"
            return question["default"]

        if q_type == "tone":
            if "amigavel" in msg or "amigável" in msg or "friendly" in msg:
                return "friendly"
            if "formal" in msg:
                return "formal"
            return "professional"

        if q_type == "autonomy":
            if "alto" in msg or "high" in msg:
                return "high"
            if "medio" in msg or "médio" in msg or "medium" in msg:
                return "medium"
            return "low"

        return question["default"]

    def _build_update(self, question: dict[str, Any], value: Any) -> dict[str, Any]:
        target_block = question.get("target_block", question["block"])

        if question["type"] == "salary_filter" and isinstance(value, dict):
            return {
                "screening_rules": {
                    "salary_expectation_filter": value.get("salary_expectation_filter", False),
                    "salary_tolerance_percent": value.get("salary_tolerance_percent", 15),
                }
            }

        if target_block == "pipeline_templates":
            return {"pipeline_templates": value if isinstance(value, list) else []}

        return {target_block: {question["field"]: value}}

    async def _generate_reply(
        self,
        user_message: str,
        current_q: dict[str, Any],
        extracted_value: Any,
        next_q: dict[str, Any],
        session: PolicySetupSession,
    ) -> str:
        try:
            prompt = REPLY_PROMPT.format(
                block_name=current_q["block_name"],
                block_index=current_q["block_index"] + 1,
                question_number=current_q["id"],
                field=current_q["field"],
                extracted_value=json.dumps(extracted_value, ensure_ascii=False),
                user_message=user_message,
                transition_context="",
                next_question=next_q["question"],
            )
            return await self._safe_invoke_llm(prompt, session=session)
        except Exception as e:
            logger.warning(f"LLM reply generation failed: {e}")
            return f"Entendido! Proxima pergunta: {next_q['question']}"

    async def _generate_block_end_reply(
        self,
        user_message: str,
        current_q: dict[str, Any],
        extracted_value: Any,
        session: PolicySetupSession,
    ) -> str:
        summary = session.get_block_summary()
        next_block_index = current_q["block_index"] + 1
        next_block_name = BLOCK_NAMES[next_block_index] if next_block_index < len(BLOCK_NAMES) else ""

        try:
            prompt = REPLY_PROMPT.format(
                block_name=current_q["block_name"],
                block_index=current_q["block_index"] + 1,
                question_number=current_q["id"],
                field=current_q["field"],
                extracted_value=json.dumps(extracted_value, ensure_ascii=False),
                user_message=user_message,
                transition_context=f"FINAL DO BLOCO. Resumo do que foi salvo:\n{summary}\n\nProximo bloco: {next_block_name}. Pergunte se quer continuar.",
                next_question="",
            )
            return await self._safe_invoke_llm(prompt, session=session)
        except Exception as e:
            logger.warning(f"LLM block end reply failed: {e}")
            return (
                f"Salvei as configuracoes de {current_q['block_name']}.\n\n"
                f"Quer continuar para o bloco {next_block_name}?"
            )

    async def _generate_completion_reply(
        self,
        user_message: str,
        current_q: dict[str, Any],
        extracted_value: Any,
        session: PolicySetupSession,
    ) -> str:
        return (
            "Pronto! Todas as 19 perguntas foram respondidas. "
            "As politicas de contratacao da sua empresa estao configuradas. "
            "Voce pode editar qualquer configuracao a qualquer momento pelo painel ao lado, "
            "ou pedir para mim diretamente no chat."
        )

    def _completed_response(self, session: PolicySetupSession) -> dict[str, Any]:
        return {
            "reply": (
                "As politicas de contratacao ja estao configuradas! "
                "Se precisar ajustar algo, e so me dizer ou editar pelo painel ao lado."
            ),
            "current_block": None,
            "current_question": 19,
            "total_questions": 19,
            "setup_progress": 100,
            "updated_fields": {},
            "block_completed": False,
            "all_completed": True,
        }

    def _calc_progress(self, session: PolicySetupSession) -> int:
        if not session.answered_questions:
            return 0
        return min(int((len(session.answered_questions) / 19) * 100), 100)


policy_setup_agent = PolicySetupAgent()
