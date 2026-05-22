"""
Intent Schemas - Define entity requirements for each intent per agent.

This module provides structured schemas for intent detection and routing,
enabling dynamic confidence scoring based on entity presence and quality.
"""
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

from app.shared.agents.agent_types import AgentType


class EntityImportance(StrEnum):
    """Importance level of an entity for intent handling."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class EntityType(StrEnum):
    """Types of entities that can be extracted."""
    JOB_ID = "job_id"
    JOB_TITLE = "job_title"
    CANDIDATE_ID = "candidate_id"
    CANDIDATE_NAME = "candidate_name"
    CANDIDATE_EMAIL = "candidate_email"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SKILLS = "skills"
    EXPERIENCE_YEARS = "experience_years"
    LOCATION = "location"
    SALARY_RANGE = "salary_range"
    INTERVIEW_ID = "interview_id"
    STAGE_NAME = "stage_name"
    SCORE = "score"
    MESSAGE = "message"
    FILE = "file"
    BOOLEAN = "boolean"
    TEXT = "text"
    NUMBER = "number"
    LIST = "list"


@dataclass
class EntityRequirement:
    """Defines an entity requirement for an intent."""
    entity_type: EntityType
    importance: EntityImportance = EntityImportance.OPTIONAL
    description: str = ""
    default_value: Any = None
    validation_pattern: str | None = None
    
    def is_satisfied(self, entities: dict[str, Any]) -> bool:
        """Check if this requirement is satisfied by the entities."""
        entity_key = self.entity_type.value
        if self.importance == EntityImportance.REQUIRED:
            return entity_key in entities and entities[entity_key] is not None
        return True
    
    def get_confidence_contribution(self, entities: dict[str, Any]) -> float:
        """Get confidence contribution based on entity presence."""
        entity_key = self.entity_type.value
        has_entity = entity_key in entities and entities[entity_key] is not None
        
        if self.importance == EntityImportance.REQUIRED:
            return 0.4 if has_entity else 0.0
        elif self.importance == EntityImportance.RECOMMENDED:
            return 0.2 if has_entity else 0.05
        else:
            return 0.1 if has_entity else 0.05


@dataclass
class IntentSchema:
    """Schema defining an intent and its entity requirements."""
    intent: str
    agent_type: AgentType
    description: str
    entity_requirements: list[EntityRequirement] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    fallback_intents: list[str] = field(default_factory=list)
    requires_context: list[str] = field(default_factory=list)
    min_confidence: float = 0.5
    
    def calculate_confidence(
        self, 
        entities: dict[str, Any], 
        context: dict[str, Any],
        message: str = ""
    ) -> float:
        """Calculate confidence score for handling this intent."""
        base_confidence = 0.3
        
        for req in self.entity_requirements:
            base_confidence += req.get_confidence_contribution(entities)
        
        keyword_matches = sum(1 for kw in self.keywords if kw.lower() in message.lower())
        if keyword_matches > 0:
            base_confidence += min(0.2, keyword_matches * 0.05)
        
        context_satisfied = all(
            ctx_key in context and context[ctx_key] is not None 
            for ctx_key in self.requires_context
        )
        if self.requires_context and context_satisfied:
            base_confidence += 0.1
        elif self.requires_context and not context_satisfied:
            base_confidence -= 0.1
        
        return min(0.95, max(0.0, base_confidence))
    
    def get_missing_entities(self, entities: dict[str, Any]) -> list[EntityRequirement]:
        """Get list of missing required/recommended entities."""
        missing = []
        for req in self.entity_requirements:
            if req.importance in [EntityImportance.REQUIRED, EntityImportance.RECOMMENDED]:
                if not req.is_satisfied(entities):
                    missing.append(req)
        return missing
    
    def is_valid(self, entities: dict[str, Any]) -> bool:
        """Check if all required entities are present."""
        return all(
            req.is_satisfied(entities) 
            for req in self.entity_requirements 
            if req.importance == EntityImportance.REQUIRED
        )


JOB_PLANNER_INTENTS = [
    IntentSchema(
        intent="create_job_vacancy",
        agent_type=AgentType.JOB_PLANNER,
        description="Criar uma nova vaga de emprego",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_TITLE, EntityImportance.RECOMMENDED, "Título da vaga"),
            EntityRequirement(EntityType.SKILLS, EntityImportance.OPTIONAL, "Competências técnicas"),
            EntityRequirement(EntityType.LOCATION, EntityImportance.OPTIONAL, "Localização"),
            EntityRequirement(EntityType.SALARY_RANGE, EntityImportance.OPTIONAL, "Faixa salarial"),
        ],
        keywords=["criar vaga", "nova vaga", "abrir vaga", "criar posição", "nova posição", "create job"],
        fallback_intents=["general_question"],
    ),
    IntentSchema(
        intent="extract_job_description",
        agent_type=AgentType.JOB_PLANNER,
        description="Extrair informações de uma descrição de vaga",
        entity_requirements=[
            EntityRequirement(EntityType.TEXT, EntityImportance.REQUIRED, "Texto da JD"),
        ],
        keywords=["extrair", "analisar jd", "parse jd", "ler descrição"],
    ),
    IntentSchema(
        intent="generate_wsi_questions",
        agent_type=AgentType.JOB_PLANNER,
        description="Gerar perguntas WSI para uma vaga",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
        ],
        keywords=["perguntas wsi", "gerar perguntas", "criar triagem", "wsi questions"],
        requires_context=["current_job_id"],
    ),
]

SOURCING_INTENTS = [
    IntentSchema(
        intent="search_candidates",
        agent_type=AgentType.SOURCING,
        description="Buscar candidatos no banco de talentos",
        entity_requirements=[
            EntityRequirement(EntityType.SKILLS, EntityImportance.RECOMMENDED, "Skills para buscar"),
            EntityRequirement(EntityType.EXPERIENCE_YEARS, EntityImportance.OPTIONAL, "Anos de experiência"),
            EntityRequirement(EntityType.LOCATION, EntityImportance.OPTIONAL, "Localização"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.OPTIONAL, "ID da vaga para matching"),
        ],
        keywords=["buscar", "procurar", "encontrar candidatos", "search", "sourcing", "hunting"],
    ),
    IntentSchema(
        intent="generate_boolean_string",
        agent_type=AgentType.SOURCING,
        description="Gerar string booleana para busca",
        entity_requirements=[
            EntityRequirement(EntityType.SKILLS, EntityImportance.REQUIRED, "Skills para busca"),
        ],
        keywords=["boolean", "string booleana", "busca avançada"],
    ),
    IntentSchema(
        intent="pearch_search",
        agent_type=AgentType.SOURCING,
        description="Buscar candidatos no Pearch AI (banco externo)",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.RECOMMENDED, "ID da vaga"),
            EntityRequirement(EntityType.SKILLS, EntityImportance.RECOMMENDED, "Skills para buscar"),
        ],
        keywords=["pearch", "banco externo", "busca global", "candidatos externos"],
    ),
]

CV_SCREENING_INTENTS = [
    IntentSchema(
        intent="parse_cv",
        agent_type=AgentType.CV_SCREENING,
        description="Analisar e extrair dados de um currículo",
        entity_requirements=[
            EntityRequirement(EntityType.FILE, EntityImportance.REQUIRED, "Arquivo do CV"),
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.OPTIONAL, "ID do candidato"),
        ],
        keywords=["analisar cv", "parse cv", "ler currículo", "extrair cv"],
    ),
    IntentSchema(
        intent="screen_candidate",
        agent_type=AgentType.CV_SCREENING,
        description="Fazer triagem inicial de um candidato",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
        ],
        keywords=["triagem", "triar", "avaliar cv", "screening"],
        requires_context=["current_job_id"],
    ),
    IntentSchema(
        intent="rank_candidates",
        agent_type=AgentType.CV_SCREENING,
        description="Rankear candidatos por adequação à vaga",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
            EntityRequirement(EntityType.LIST, EntityImportance.OPTIONAL, "Lista de candidatos"),
        ],
        keywords=["rankear", "ordenar", "classificar", "ranking", "top candidatos"],
    ),
]

INTERVIEWER_INTENTS = [
    IntentSchema(
        intent="start_wsi_interview",
        agent_type=AgentType.INTERVIEWER,
        description="Iniciar entrevista WSI com candidato",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
        ],
        keywords=["iniciar entrevista", "entrevistar", "start interview", "wsi interview"],
    ),
    IntentSchema(
        intent="voice_screening",
        agent_type=AgentType.INTERVIEWER,
        description="Triagem por voz (Twilio Voice / Gemini STT)",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
        ],
        keywords=["voz", "voice", "áudio", "ligar", "chamada"],
    ),
    IntentSchema(
        intent="transcribe_audio",
        agent_type=AgentType.INTERVIEWER,
        description="Transcrever áudio de entrevista",
        entity_requirements=[
            EntityRequirement(EntityType.FILE, EntityImportance.REQUIRED, "Arquivo de áudio"),
            EntityRequirement(EntityType.INTERVIEW_ID, EntityImportance.OPTIONAL, "ID da entrevista"),
        ],
        keywords=["transcrever", "transcription", "áudio para texto"],
    ),
]

WSI_EVALUATOR_INTENTS = [
    IntentSchema(
        intent="calculate_wsi_score",
        agent_type=AgentType.WSI_EVALUATOR,
        description="Calcular score WSI determinístico",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
        ],
        keywords=["calcular wsi", "score wsi", "avaliar wsi", "pontuação"],
    ),
    IntentSchema(
        intent="generate_parecer",
        agent_type=AgentType.WSI_EVALUATOR,
        description="Gerar parecer técnico do candidato",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.REQUIRED, "ID da vaga"),
        ],
        keywords=["parecer", "laudo", "avaliação", "relatório candidato"],
    ),
    IntentSchema(
        intent="compare_candidates",
        agent_type=AgentType.WSI_EVALUATOR,
        description="Comparar candidatos usando WSI",
        entity_requirements=[
            EntityRequirement(EntityType.LIST, EntityImportance.REQUIRED, "Lista de candidate_ids"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.RECOMMENDED, "ID da vaga"),
        ],
        keywords=["comparar", "compare", "versus", "qual melhor"],
    ),
]

SCHEDULING_INTENTS = [
    IntentSchema(
        intent="schedule_interview",
        agent_type=AgentType.SCHEDULING,
        description="Agendar entrevista com candidato",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.DATETIME, EntityImportance.RECOMMENDED, "Data e hora"),
            EntityRequirement(EntityType.JOB_ID, EntityImportance.OPTIONAL, "ID da vaga"),
        ],
        keywords=["agendar", "marcar", "schedule", "entrevista"],
    ),
    IntentSchema(
        intent="check_availability",
        agent_type=AgentType.SCHEDULING,
        description="Verificar disponibilidade para agendamento",
        entity_requirements=[
            EntityRequirement(EntityType.DATE, EntityImportance.OPTIONAL, "Data para verificar"),
        ],
        keywords=["disponibilidade", "horários", "agenda", "availability"],
    ),
    IntentSchema(
        intent="reschedule_interview",
        agent_type=AgentType.SCHEDULING,
        description="Reagendar entrevista existente",
        entity_requirements=[
            EntityRequirement(EntityType.INTERVIEW_ID, EntityImportance.REQUIRED, "ID da entrevista"),
            EntityRequirement(EntityType.DATETIME, EntityImportance.RECOMMENDED, "Nova data e hora"),
        ],
        keywords=["reagendar", "remarcar", "alterar data", "reschedule"],
    ),
]

ANALYST_FEEDBACK_INTENTS = [
    IntentSchema(
        intent="generate_kpi_report",
        agent_type=AgentType.ANALYST_FEEDBACK,
        description="Gerar relatório de KPIs de recrutamento",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.OPTIONAL, "ID da vaga (ou geral)"),
            EntityRequirement(EntityType.DATE, EntityImportance.OPTIONAL, "Período do relatório"),
        ],
        keywords=["kpi", "relatório", "métricas", "report", "dashboard"],
    ),
    IntentSchema(
        intent="analyze_funnel",
        agent_type=AgentType.ANALYST_FEEDBACK,
        description="Analisar funil de recrutamento",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.RECOMMENDED, "ID da vaga"),
        ],
        keywords=["funil", "funnel", "conversão", "etapas"],
    ),
    IntentSchema(
        intent="send_feedback",
        agent_type=AgentType.ANALYST_FEEDBACK,
        description="Enviar feedback para candidato",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.MESSAGE, EntityImportance.OPTIONAL, "Mensagem de feedback"),
        ],
        keywords=["feedback", "retorno", "resposta candidato"],
    ),
]

ATS_INTEGRATOR_INTENTS = [
    IntentSchema(
        intent="sync_candidate",
        agent_type=AgentType.ATS_INTEGRATOR,
        description="Sincronizar candidato com ATS externo",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
        ],
        keywords=["sincronizar", "sync", "ats", "gupy", "pandape"],
    ),
    IntentSchema(
        intent="import_candidates",
        agent_type=AgentType.ATS_INTEGRATOR,
        description="Importar candidatos do ATS",
        entity_requirements=[
            EntityRequirement(EntityType.JOB_ID, EntityImportance.OPTIONAL, "ID da vaga"),
        ],
        keywords=["importar", "import", "trazer candidatos"],
    ),
    IntentSchema(
        intent="update_ats_status",
        agent_type=AgentType.ATS_INTEGRATOR,
        description="Atualizar status do candidato no ATS",
        entity_requirements=[
            EntityRequirement(EntityType.CANDIDATE_ID, EntityImportance.REQUIRED, "ID do candidato"),
            EntityRequirement(EntityType.STAGE_NAME, EntityImportance.REQUIRED, "Novo status/etapa"),
        ],
        keywords=["atualizar ats", "mudar status ats", "update ats"],
    ),
]

TASK_PLANNER_INTENTS = [
    IntentSchema(
        intent="plan_task",
        agent_type=AgentType.TASK_PLANNER,
        description="Planejar e decompor uma tarefa complexa",
        entity_requirements=[
            EntityRequirement(EntityType.TEXT, EntityImportance.REQUIRED, "Descrição da tarefa"),
        ],
        keywords=["planejar", "decompor", "dividir tarefa", "plan"],
    ),
    IntentSchema(
        intent="check_pending_tasks",
        agent_type=AgentType.TASK_PLANNER,
        description="Verificar tarefas pendentes",
        entity_requirements=[],
        keywords=["tarefas pendentes", "o que falta", "pending", "backlog"],
    ),
]

RECRUITER_ASSISTANT_INTENTS = [
    IntentSchema(
        intent="daily_briefing",
        agent_type=AgentType.RECRUITER_ASSISTANT,
        description="Resumo diário de atividades",
        entity_requirements=[],
        keywords=["bom dia", "resumo", "briefing", "como está", "novidades"],
    ),
    IntentSchema(
        intent="general_question",
        agent_type=AgentType.RECRUITER_ASSISTANT,
        description="Pergunta geral ou chitchat",
        entity_requirements=[
            EntityRequirement(EntityType.TEXT, EntityImportance.OPTIONAL, "Pergunta"),
        ],
        keywords=["ajuda", "help", "como", "o que é", "explica"],
    ),
    IntentSchema(
        intent="chitchat",
        agent_type=AgentType.RECRUITER_ASSISTANT,
        description="Conversa casual",
        entity_requirements=[],
        keywords=["oi", "olá", "tudo bem", "obrigado", "valeu"],
    ),
]

ALL_INTENT_SCHEMAS: dict[AgentType, list[IntentSchema]] = {
    AgentType.JOB_PLANNER: JOB_PLANNER_INTENTS,
    AgentType.SOURCING: SOURCING_INTENTS,
    AgentType.CV_SCREENING: CV_SCREENING_INTENTS,
    AgentType.INTERVIEWER: INTERVIEWER_INTENTS,
    AgentType.WSI_EVALUATOR: WSI_EVALUATOR_INTENTS,
    AgentType.SCHEDULING: SCHEDULING_INTENTS,
    AgentType.ANALYST_FEEDBACK: ANALYST_FEEDBACK_INTENTS,
    AgentType.ATS_INTEGRATOR: ATS_INTEGRATOR_INTENTS,
    AgentType.TASK_PLANNER: TASK_PLANNER_INTENTS,
    AgentType.RECRUITER_ASSISTANT: RECRUITER_ASSISTANT_INTENTS,
}


def get_agent_intents(agent_type: AgentType) -> list[IntentSchema]:
    """Get all intent schemas for a specific agent."""
    return ALL_INTENT_SCHEMAS.get(agent_type, [])


def get_intent_schema(intent: str) -> IntentSchema | None:
    """Get the schema for a specific intent."""
    for schemas in ALL_INTENT_SCHEMAS.values():
        for schema in schemas:
            if schema.intent == intent:
                return schema
    return None


def find_best_matching_intent(
    message: str,
    entities: dict[str, Any],
    context: dict[str, Any]
) -> IntentSchema | None:
    """Find the best matching intent schema for a message."""
    best_schema = None
    best_confidence = 0.0
    
    for schemas in ALL_INTENT_SCHEMAS.values():
        for schema in schemas:
            confidence = schema.calculate_confidence(entities, context, message)
            if confidence > best_confidence:
                best_confidence = confidence
                best_schema = schema
    
    return best_schema if best_confidence >= 0.5 else None
