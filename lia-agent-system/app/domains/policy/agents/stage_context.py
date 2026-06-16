"""
Stage context for PolicySetupAgent — questions, blocks, and session state.

Moved from app/agents/policy_setup_agent.py (I3c cleanup).
"""
from datetime import datetime
from typing import Any

QUESTIONS = [
    {
        "id": 1,
        "block": "pipeline_rules",
        "block_name": "Pipeline e Processo",
        "block_index": 0,
        "field": "min_interviews_before_offer",
        "question": "Quantas entrevistas minimas voces fazem antes de enviar uma proposta ao candidato?",
        "type": "integer",
        "default": 2,
        "hint": "Exemplo: 2 entrevistas (RH + gestor)",
    },
    {
        "id": 2,
        "block": "pipeline_rules",
        "block_name": "Pipeline e Processo",
        "block_index": 0,
        "field": "manager_approval_for_offer",
        "question": "A proposta salarial precisa de aprovacao do gestor da area antes de ser enviada?",
        "type": "boolean",
        "default": True,
        "hint": "Sim ou nao",
    },
    {
        "id": 3,
        "block": "pipeline_rules",
        "block_name": "Pipeline e Processo",
        "block_index": 0,
        "field": "max_days_in_stage",
        "question": "Qual o tempo maximo (em dias) que um candidato pode ficar em cada etapa sem acao antes de gerar um alerta? Por exemplo: triagem 5 dias, entrevista 10 dias.",
        "type": "stage_days",
        "default": {},
        "hint": "Pode definir por etapa ou um padrao geral",
    },
    {
        "id": 4,
        "block": "pipeline_rules",
        "block_name": "Pipeline e Processo",
        "block_index": 0,
        "field": "pipeline_templates",
        "question": "Voces tem tipos diferentes de vagas com processos diferentes? Por exemplo, vagas operacionais com menos etapas e vagas tecnicas com mais etapas.",
        "type": "templates",
        "default": [],
        "hint": "Se sim, quais tipos e quais etapas cada um tem?",
        "target_block": "pipeline_templates",
    },
    {
        "id": 5,
        "block": "scheduling_rules",
        "block_name": "Agendamento",
        "block_index": 1,
        "field": "allowed_days",
        "question": "Quais dias da semana sao permitidos para entrevistas?",
        "type": "days",
        "default": ["mon", "tue", "wed", "thu", "fri"],
        "hint": "Exemplo: segunda a sexta, ou terca a quinta",
    },
    {
        "id": 6,
        "block": "scheduling_rules",
        "block_name": "Agendamento",
        "block_index": 1,
        "field": "allowed_hours",
        "question": "Qual o horario permitido para entrevistas? Por exemplo, das 9h as 18h.",
        "type": "hours",
        "default": {"start": "09:00", "end": "18:00"},
        "hint": "Formato: inicio e fim",
    },
    {
        "id": 7,
        "block": "scheduling_rules",
        "block_name": "Agendamento",
        "block_index": 1,
        "field": "default_duration_minutes",
        "question": "Qual a duracao padrao de uma entrevista em minutos?",
        "type": "integer",
        "default": 60,
        "hint": "Exemplo: 45 minutos, 1 hora",
    },
    {
        "id": 8,
        "block": "scheduling_rules",
        "block_name": "Agendamento",
        "block_index": 1,
        "field": "self_scheduling_enabled",
        "question": "Candidatos podem escolher o horario da entrevista sozinhos (auto-agendamento)?",
        "type": "boolean",
        "default": False,
        "hint": "Sim ou nao",
    },
    {
        "id": 9,
        "block": "communication_rules",
        "block_name": "Comunicacao",
        "block_index": 2,
        "field": "auto_rejection_feedback",
        "question": "Candidatos reprovados devem receber feedback automatico?",
        "type": "boolean",
        "default": False,
        "hint": "Sim ou nao",
    },
    {
        "id": 10,
        "block": "communication_rules",
        "block_name": "Comunicacao",
        "block_index": 2,
        "field": "rejection_feedback_deadline_hours",
        "question": "Em quanto tempo apos a reprovacao o feedback deve ser enviado? (em horas)",
        "type": "integer",
        "default": 48,
        "hint": "Exemplo: 24 horas, 48 horas",
    },
    {
        "id": 11,
        "block": "communication_rules",
        "block_name": "Comunicacao",
        "block_index": 2,
        "field": "preferred_channel",
        "question": "Qual o canal preferido para falar com candidatos: WhatsApp, email ou ambos?",
        "type": "channel",
        "default": "whatsapp",
        "hint": "whatsapp, email ou both",
    },
    {
        "id": 12,
        "block": "communication_rules",
        "block_name": "Comunicacao",
        "block_index": 2,
        "field": "lia_tone",
        "question": "Qual o tom que eu (LIA) devo usar nas comunicacoes? Profissional, amigavel ou mais formal?",
        "type": "tone",
        "default": "professional",
        "hint": "professional, friendly ou formal",
    },
    {
        "id": 13,
        "block": "screening_rules",
        "block_name": "Triagem",
        "block_index": 3,
        "field": "salary_expectation_filter",
        "question": "Voces filtram candidatos por pretensao salarial? Se sim, com qual tolerancia percentual?",
        "type": "salary_filter",
        "default": False,
        "hint": "Exemplo: sim, com 15% de tolerancia",
    },
    {
        "id": 14,
        "block": "screening_rules",
        "block_name": "Triagem",
        "block_index": 3,
        "field": "experience_policy",
        "question": "A experiencia minima exigida e definida por vaga ou existe um padrao geral para a empresa?",
        "type": "experience",
        "default": "per_job",
        "hint": "por vaga ou padrao geral",
    },
    {
        "id": 15,
        "block": "screening_rules",
        "block_name": "Triagem",
        "block_index": 3,
        "field": "default_screening_questions",
        "question": "Existem perguntas de triagem padrao que valem para todas as vagas da empresa?",
        "type": "questions_list",
        "default": [],
        "hint": "Se sim, quais perguntas?",
    },
    {
        "id": 16,
        "block": "automation_rules",
        "block_name": "Autonomia da LIA",
        "block_index": 4,
        "field": "auto_screening",
        "question": "Eu (LIA) posso triar candidatos automaticamente ou voce prefere que eu aguarde sua confirmacao?",
        "type": "boolean",
        "default": False,
        "hint": "Sim (automatico) ou nao (aguarda confirmacao)",
    },
    {
        "id": 17,
        "block": "automation_rules",
        "block_name": "Autonomia da LIA",
        "block_index": 4,
        "field": "auto_scheduling",
        "question": "Eu posso agendar entrevistas automaticamente com base nas regras que definimos?",
        "type": "boolean",
        "default": False,
        "hint": "Sim ou nao",
    },
    {
        "id": 18,
        "block": "automation_rules",
        "block_name": "Autonomia da LIA",
        "block_index": 4,
        "field": "auto_stage_advance",
        "question": "Eu posso mover candidatos de etapa automaticamente quando os criterios sao atendidos?",
        "type": "boolean",
        "default": False,
        "hint": "Sim ou nao",
    },
    {
        "id": 19,
        "block": "automation_rules",
        "block_name": "Autonomia da LIA",
        "block_index": 4,
        "field": "autonomy_level",
        "question": "De forma geral, qual nivel de autonomia quer me dar? Baixo (sempre confirmo com voce), Medio (confirmo acoes de alto impacto) ou Alto (ajo e notifico depois)?",
        "type": "autonomy",
        "default": "low",
        "hint": "low, medium ou high",
    },
]

BLOCK_NAMES = [
    "Pipeline e Processo",
    "Agendamento",
    "Comunicacao",
    "Triagem",
    "Autonomia da LIA",
]

BLOCK_FIELD_MAP = {
    "pipeline_rules": "Pipeline e Processo",
    "scheduling_rules": "Agendamento",
    "communication_rules": "Comunicacao",
    "screening_rules": "Triagem",
    "automation_rules": "Autonomia da LIA",
}


class PolicySetupSession:
    """Tracks the state of a policy setup conversation."""

    def __init__(self, company_id: str, current_policy: dict[str, Any]):
        self.company_id = company_id
        self.current_question_index = 0
        self.answered_questions: dict[int, Any] = {}
        self.current_policy = current_policy
        self.started_at = datetime.utcnow()
        self.waiting_for_block_confirmation = False
        self.completed = False

    def get_current_question(self) -> dict[str, Any] | None:
        if self.current_question_index >= len(QUESTIONS):
            return None
        return QUESTIONS[self.current_question_index]

    def get_current_block_name(self) -> str:
        q = self.get_current_question()
        if q:
            return q["block_name"]
        return ""

    def advance_to_next_question(self):
        self.current_question_index += 1
        if self.current_question_index >= len(QUESTIONS):
            self.completed = True

    def is_block_transition(self) -> bool:
        if self.current_question_index >= len(QUESTIONS) - 1:
            return False
        current = QUESTIONS[self.current_question_index]
        next_q = QUESTIONS[self.current_question_index + 1]
        return current["block_index"] != next_q["block_index"]

    def get_block_summary(self) -> str:
        current_q = self.get_current_question()
        if not current_q:
            return ""
        block = current_q["block"]
        items = []
        for q in QUESTIONS:
            if q["block"] == block and q["id"] in self.answered_questions:
                val = self.answered_questions[q["id"]]
                items.append(f"- {q['field']}: {val}")
        return "\n".join(items) if items else "Nenhuma configuracao neste bloco"


_sessions: dict[str, PolicySetupSession] = {}


def get_or_create_session(
    company_id: str,
    session_id: str,
    current_policy: dict[str, Any]
) -> PolicySetupSession:
    key = f"{company_id}:{session_id}"
    if key not in _sessions:
        session = PolicySetupSession(company_id, current_policy)
        _determine_start_position(session, current_policy)
        _sessions[key] = session
    return _sessions[key]


def _determine_start_position(session: PolicySetupSession, policy: dict[str, Any]):
    """Skip questions that already have non-default answers."""
    pass
