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

Moved from app/agents/policy_setup_agent.py (I3c cleanup).
"""
import json
import logging
from typing import Any

from app.domains.policy.agents.stage_context import (
    BLOCK_NAMES,
    PolicySetupSession,
    get_or_create_session,
)
from app.domains.policy.agents.system_prompt import EXTRACTION_PROMPT, REPLY_PROMPT
from app.domains.ai.services.llm import LLMService

logger = logging.getLogger(__name__)


class PolicySetupAgent:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if not self._llm:
            self._llm = LLMService()
        return self._llm

    async def process_message(
        self,
        message: str,
        company_id: str,
        session_id: str,
        current_policy: dict[str, Any],
    ) -> dict[str, Any]:
        session = get_or_create_session(company_id, session_id, current_policy)

        if session.completed:
            return self._completed_response(session)

        if message.strip().lower() in ["", "iniciar", "comecar", "start", "oi", "ola", "vamos"]:
            return self._welcome_response(session)

        if session.waiting_for_block_confirmation:
            return await self._handle_block_transition(message, session)

        return await self._process_answer(message, session)

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
        self, message: str, session: PolicySetupSession
    ) -> dict[str, Any]:
        q = session.get_current_question()
        if not q:
            return self._completed_response(session)

        extracted = await self._extract_value(message, q)
        update_data = self._build_update(q, extracted)
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

        try:
            from app.shared.compliance.audit_service import audit_service
            await audit_service.log_decision(
                company_id=str(session.company_id),
                agent_name="policy_setup_agent",
                decision_type="policy_update",
                action=f"field_updated:{q.get('field', 'unknown')}",
                decision="completed" if session.completed else "in_progress",
                reasoning=[f"Q{q['id']}: {q['question'][:80]}"],
                criteria_used=[q.get("field", "")],
            )
        except Exception as _audit_exc:
            logger.debug("[PolicySetupAgent] AuditService skipped: %s", _audit_exc)

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

    async def _extract_value(self, message: str, question: dict[str, Any]) -> Any:
        try:
            prompt = EXTRACTION_PROMPT.format(
                question=question["question"],
                field=question["field"],
                type_hint=question["type"],
                answer=message,
                default=json.dumps(question["default"]),
            )

            response = type("R", (), {"content": await self.llm.safe_invoke(prompt, provider="claude")})()

            content = response.content if hasattr(response, 'content') else str(response)
            content = content.strip()

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
            response = type("R", (), {"content": await self.llm.safe_invoke(prompt, provider="claude")})()
            return response.content if hasattr(response, 'content') else str(response)
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
            response = type("R", (), {"content": await self.llm.safe_invoke(prompt, provider="claude")})()
            return response.content if hasattr(response, 'content') else str(response)
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
