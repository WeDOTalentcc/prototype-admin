"""
UI Actions - Mapeamento entre Ações dos Agentes e Componentes de UI.

Este módulo define o sistema de UI Actions que conecta as ações dos agentes
com os componentes visuais que devem ser exibidos ao usuário.

TIPOS DE COMPONENTES:
1. SIDE_PANEL - Painel lateral direito (40% da tela) para formulários estruturados
2. CHAT_CARD - Card inline no chat com informações resumidas
3. CHAT_ACTION - Botões de ação rápida no chat
4. MODAL - Modal centralizado para confirmações/alertas
5. EXPANDABLE_PROMPT - Prompt expandido com abas (em telas de busca)
6. NOTIFICATION - Notificação toast/bell

FLUXO DE INTERAÇÃO:
1. Agente identifica necessidade de coletar/exibir dados estruturados
2. Agente envia mensagem no chat explicando o que vai acontecer
3. Agente dispara UI Action com tipo apropriado
4. Frontend renderiza o componente
5. Usuário interage com o componente
6. Dados retornam para o agente via callback
7. Agente confirma no chat e continua o fluxo

Static data (catalogs, schemas, templates) is loaded from
app/data/ui_actions_data.json to keep this module focused on logic.
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import os
import pathlib


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UIComponentType(str, Enum):
    """Tipos de componentes de UI que podem ser disparados pelos agentes."""
    SIDE_PANEL = "side_panel"
    CHAT_CARD = "chat_card"
    CHAT_ACTION = "chat_action"
    MODAL = "modal"
    EXPANDABLE_PROMPT = "expandable_prompt"
    NOTIFICATION = "notification"
    INLINE_FORM = "inline_form"


class SidePanelType(str, Enum):
    """Tipos de painéis laterais disponíveis."""
    COMPENSATION_BENEFITS = "compensation_benefits"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    BEHAVIORAL_COMPETENCIES = "behavioral_competencies"
    LANGUAGES = "languages"
    BENEFITS_DETAILED = "benefits_detailed"
    WSI_QUESTIONS = "wsi_questions"
    INTERVIEW_SCHEDULING = "interview_scheduling"
    CANDIDATE_EVALUATION = "candidate_evaluation"
    CALIBRATION_FEEDBACK = "calibration_feedback"
    JOB_REQUIREMENTS = "job_requirements"
    CANDIDATE_PROFILE = "candidate_profile"
    SEARCH_FILTERS = "search_filters"
    ATS_FIELD_MAPPING = "ats_field_mapping"
    ATS_SYNC_STATUS = "ats_sync_status"
    EMAIL_COMPOSER = "email_composer"
    WHATSAPP_COMPOSER = "whatsapp_composer"


class ChatCardType(str, Enum):
    """Tipos de cards inline no chat."""
    CANDIDATE_SUMMARY = "candidate_summary"
    JOB_SUMMARY = "job_summary"
    COMPENSATION_SUMMARY = "compensation_summary"
    INTERVIEW_CONFIRMATION = "interview_confirmation"
    WSI_SCORE = "wsi_score"
    MARKET_ANALYSIS = "market_analysis"
    CALIBRATION_SAMPLE = "calibration_sample"
    SEARCH_RESULTS_PREVIEW = "search_results_preview"
    PROGRESS_TRACKER = "progress_tracker"
    STAGE_TRANSITION = "stage_transition"
    EMAIL_PREVIEW = "email_preview"
    WHATSAPP_PREVIEW = "whatsapp_preview"
    DASHBOARD_METRICS = "dashboard_metrics"
    SYNC_STATUS = "sync_status"


class ChatActionType(str, Enum):
    """Tipos de ações rápidas no chat."""
    CONFIRM_PROCEED = "confirm_proceed"
    SELECT_OPTION = "select_option"
    QUICK_FEEDBACK = "quick_feedback"
    APPROVE_REJECT = "approve_reject"
    SCHEDULE_OPTIONS = "schedule_options"
    EDIT_DATA = "edit_data"
    SEND_MESSAGE = "send_message"
    EXPORT_DATA = "export_data"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class UIAction:
    """
    Representa uma ação de UI disparada por um agente.
    
    Esta é a estrutura base que o agente envia para o frontend
    quando precisa exibir um componente específico.
    """
    action_id: str
    component_type: UIComponentType
    component_subtype: str
    title: str
    description: Optional[str] = None
    
    data: Dict[str, Any] = field(default_factory=dict)
    
    schema: Optional[Dict[str, Any]] = None
    
    callback_action: Optional[str] = None
    
    source_agent: Optional[str] = None
    conversation_id: Optional[str] = None
    
    priority: int = 0
    auto_open: bool = True
    dismissible: bool = True
    
    expires_at: Optional[datetime] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "component_type": self.component_type.value,
            "component_subtype": self.component_subtype,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "schema": self.schema,
            "callback_action": self.callback_action,
            "source_agent": self.source_agent,
            "conversation_id": self.conversation_id,
            "priority": self.priority,
            "auto_open": self.auto_open,
            "dismissible": self.dismissible,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Load static data from JSON
# ---------------------------------------------------------------------------

def _load_ui_actions_data() -> Dict[str, Any]:
    """Load static data from the JSON file generated by extract_ui_data.py."""
    # Try several candidate paths so it works regardless of cwd
    _this_dir = pathlib.Path(__file__).resolve().parent          # lia_models/
    _project_root = _this_dir.parent.parent.parent               # lia-agent-system/
    candidates = [
        _project_root / "app" / "data" / "ui_actions_data.json",
        pathlib.Path("/home/runner/workspace/lia-agent-system/app/data/ui_actions_data.json"),
    ]
    for p in candidates:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(
        f"ui_actions_data.json not found. Searched: {[str(c) for c in candidates]}"
    )


_DATA = _load_ui_actions_data()

CURRENCY_CONFIG: Dict[str, Any] = _DATA["CURRENCY_CONFIG"]
BENEFITS_CATALOG: List[Dict[str, Any]] = _DATA["BENEFITS_CATALOG"]
TECHNOLOGY_SUGGESTIONS: Dict[str, List[Dict[str, Any]]] = _DATA["TECHNOLOGY_SUGGESTIONS"]
COMPETENCY_DESCRIPTIONS: Dict[str, Dict[str, Any]] = _DATA["COMPETENCY_DESCRIPTIONS"]
LANGUAGES_CATALOG: List[Dict[str, Any]] = _DATA["LANGUAGES_CATALOG"]
LANGUAGE_LEVELS: List[Dict[str, Any]] = _DATA["LANGUAGE_LEVELS"]
WSI_QUESTION_TEMPLATES: Dict[str, Dict[str, Any]] = _DATA["WSI_QUESTION_TEMPLATES"]
CALENDAR_INTEGRATION_CONFIG: Dict[str, Any] = _DATA["CALENDAR_INTEGRATION_CONFIG"]
AGENT_UI_MAPPINGS: Dict[str, Dict[str, Any]] = _DATA["AGENT_UI_MAPPINGS"]
WORKFLOW_STEP_UI_MAPPINGS: Dict[str, Any] = _DATA["WORKFLOW_STEP_UI_MAPPINGS"]
SIDE_PANEL_SCHEMAS: Dict[str, Dict[str, Any]] = _DATA["SIDE_PANEL_SCHEMAS"]
CHAT_CARD_SCHEMAS: Dict[str, Dict[str, Any]] = _DATA["CHAT_CARD_SCHEMAS"]

# Free the loader reference
del _DATA


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_ui_action_for_trigger(agent: str, trigger: str) -> Optional[Dict[str, Any]]:
    """
    Retorna a definição de UI Action para um trigger específico de um agente.
    
    Args:
        agent: Nome do agente (ex: "job_planner")
        trigger: Nome do trigger (ex: "collect_compensation")
        
    Returns:
        Dict com a configuração da UI Action ou None
    """
    agent_config = AGENT_UI_MAPPINGS.get(agent)
    if not agent_config:
        return None
    
    for action in agent_config.get("ui_actions", []):
        if action.get("trigger") == trigger:
            return action
    
    return None


def get_side_panel_schema(panel_type: str) -> Optional[Dict[str, Any]]:
    """
    Retorna o schema de um painel lateral.
    
    Args:
        panel_type: Tipo do painel (ex: "compensation_benefits")
        
    Returns:
        Dict com o schema do painel ou None
    """
    return SIDE_PANEL_SCHEMAS.get(panel_type)


def get_chat_card_schema(card_type: str) -> Optional[Dict[str, Any]]:
    """
    Retorna o schema de um chat card.
    
    Args:
        card_type: Tipo do card (ex: "candidate_summary")
        
    Returns:
        Dict com o schema do card ou None
    """
    return CHAT_CARD_SCHEMAS.get(card_type)


def get_workflow_step_ui(step: str) -> Optional[Dict[str, Any]]:
    """
    Retorna a configuração de UI para um step específico do workflow.
    
    Args:
        step: ID do step (ex: "step_05_compensation")
        
    Returns:
        Dict com a configuração ou None
    """
    return WORKFLOW_STEP_UI_MAPPINGS.get(step)


async def build_ui_action(
    agent: str,
    trigger: str,
    context: Dict[str, Any],
    conversation_id: Optional[str] = None,
) -> Optional[UIAction]:
    """
    Constrói UIAction com dados do contexto para envio ao frontend.
    
    Esta função é usada pelos agentes para criar UI Actions de forma consistente,
    preenchendo automaticamente campos do schema com dados existentes.
    
    Args:
        agent: Nome do agente disparando a ação
        trigger: Trigger que identifica a ação
        context: Dados do contexto (job vacancy, candidate, etc.)
        conversation_id: ID da conversa atual
        
    Returns:
        UIAction configurada ou None se não encontrar a definição
    """
    action_def = get_ui_action_for_trigger(agent, trigger)
    if not action_def:
        return None
    
    action_id = f"{agent}_{trigger}_{uuid.uuid4().hex[:8]}"
    
    component_type_str = action_def["component_type"]
    component_subtype = action_def["component_subtype"]
    
    # component_type comes from JSON as a string now
    if isinstance(component_type_str, str):
        component_type = UIComponentType(component_type_str)
    else:
        component_type = component_type_str
    
    if isinstance(component_subtype, Enum):
        component_subtype = component_subtype.value
    
    schema = None
    if component_type == UIComponentType.SIDE_PANEL:
        schema = get_side_panel_schema(component_subtype)
    elif component_type == UIComponentType.CHAT_CARD:
        schema = get_chat_card_schema(component_subtype)
    
    data = _extract_relevant_data(context, action_def.get("fields", []))
    
    return UIAction(
        action_id=action_id,
        component_type=component_type,
        component_subtype=component_subtype,
        title=action_def.get("title", ""),
        description=action_def.get("description"),
        data=data,
        schema=schema,
        callback_action=f"handle_{trigger}_response",
        source_agent=agent,
        conversation_id=conversation_id,
        priority=action_def.get("priority", 0),
        auto_open=action_def.get("auto_open", True),
        dismissible=action_def.get("dismissible", True),
    )


async def emit_ui_action(
    action: UIAction,
    conversation_id: str,
    websocket_manager: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Emite UIAction para o frontend via WebSocket/SSE.
    
    Esta função é responsável por enviar a UI Action para o cliente,
    registrando a ação para tracking e garantindo entrega.
    
    Args:
        action: UIAction a ser emitida
        conversation_id: ID da conversa
        websocket_manager: Gerenciador de WebSocket (opcional)
        
    Returns:
        Dict com status da emissão e action_id
    """
    action.conversation_id = conversation_id
    
    payload = {
        "type": "ui_action",
        "action": action.to_dict(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if websocket_manager:
        try:
            await websocket_manager.send_to_conversation(conversation_id, payload)
            return {
                "success": True,
                "action_id": action.action_id,
                "delivery_method": "websocket",
            }
        except Exception as e:
            return {
                "success": False,
                "action_id": action.action_id,
                "error": str(e),
                "fallback_payload": payload,
            }
    
    return {
        "success": True,
        "action_id": action.action_id,
        "delivery_method": "poll",
        "payload": payload,
    }


def get_panel_with_data(
    panel_type: str,
    existing_data: Dict[str, Any],
    prefill_defaults: bool = True,
) -> Dict[str, Any]:
    """
    Retorna schema do painel com dados pré-preenchidos.
    
    Esta função é usada quando queremos abrir um painel lateral com
    dados já existentes (ex: edição de uma vaga).
    
    Args:
        panel_type: Tipo do painel (ex: "compensation_benefits")
        existing_data: Dados existentes para pré-preenchimento
        prefill_defaults: Se deve preencher valores padrão
        
    Returns:
        Dict com o schema do painel e dados preenchidos
    """
    schema = get_side_panel_schema(panel_type)
    if not schema:
        return {"error": f"Panel type '{panel_type}' not found"}
    
    schema_with_data = json.loads(json.dumps(schema))
    
    for section in schema_with_data.get("sections", []):
        for field in section.get("fields", []):
            field_name = field.get("name")
            
            if field_name in existing_data:
                field["value"] = existing_data[field_name]
            elif prefill_defaults and "default" in field:
                field["value"] = field["default"]
            
            if field.get("type") == "benefits_selector" and "benefits" in existing_data:
                field["selected_values"] = existing_data["benefits"]
            
            if field.get("type") in ["tech_table", "language_table"] and field_name in existing_data:
                field["rows"] = existing_data[field_name]
    
    return {
        "schema": schema_with_data,
        "prefilled_data": existing_data,
        "panel_type": panel_type,
    }


def get_card_with_data(
    card_type: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Retorna schema do chat card com dados preenchidos.
    
    Args:
        card_type: Tipo do card (ex: "candidate_summary")
        data: Dados para preencher o card
        
    Returns:
        Dict com o schema do card e dados
    """
    schema = get_chat_card_schema(card_type)
    if not schema:
        return {"error": f"Card type '{card_type}' not found"}
    
    return {
        "schema": schema,
        "data": data,
        "card_type": card_type,
    }


def _extract_relevant_data(
    context: Dict[str, Any],
    field_definitions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Extrai dados relevantes do contexto baseado nas definições de campos.
    
    Args:
        context: Contexto completo
        field_definitions: Lista de definições de campos
        
    Returns:
        Dict com dados relevantes extraídos
    """
    extracted = {}
    
    for field_def in field_definitions:
        field_name = field_def.get("name")
        if field_name and field_name in context:
            extracted[field_name] = context[field_name]
    
    common_fields = ["job_id", "candidate_id", "vacancy_title", "candidate_name"]
    for f in common_fields:
        if f in context and f not in extracted:
            extracted[f] = context[f]
    
    return extracted


def validate_panel_data(
    panel_type: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Valida dados submetidos de um painel lateral.
    
    Args:
        panel_type: Tipo do painel
        data: Dados submetidos
        
    Returns:
        Dict com resultado da validação (valid, errors)
    """
    schema = get_side_panel_schema(panel_type)
    if not schema:
        return {"valid": False, "errors": [f"Unknown panel type: {panel_type}"]}
    
    errors = []
    
    for section in schema.get("sections", []):
        for field in section.get("fields", []):
            field_name = field.get("name")
            is_required = field.get("required", False)
            
            if is_required and (field_name not in data or not data[field_name]):
                errors.append({
                    "field": field_name,
                    "error": f"Campo obrigatório: {field.get('label', field_name)}",
                })
            
            if field_name in data and field.get("validation"):
                validation = field["validation"]
                value = data[field_name]
                
                if "min_value" in validation and value < validation["min_value"]:
                    errors.append({
                        "field": field_name,
                        "error": f"Valor mínimo: {validation['min_value']}",
                    })
                
                if "max_value" in validation and value > validation["max_value"]:
                    errors.append({
                        "field": field_name,
                        "error": f"Valor máximo: {validation['max_value']}",
                    })
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def get_wsi_templates_for_area(area: str) -> List[Dict[str, Any]]:
    """
    Retorna templates de perguntas WSI para uma área específica.
    
    Args:
        area: Área de atuação (tech, sales, marketing, etc.)
        
    Returns:
        Lista de templates de perguntas
    """
    area_config = WSI_QUESTION_TEMPLATES.get(area)
    if not area_config:
        return []
    
    return area_config.get("templates", [])


def get_benefits_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retorna benefícios agrupados por categoria.
    
    Returns:
        Dict com categorias como chaves e lista de benefícios como valores
    """
    grouped = {}
    for benefit in BENEFITS_CATALOG:
        category = benefit.get("category", "outros")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(benefit)
    
    return grouped


def get_technology_suggestions_for_category(category: str) -> List[Dict[str, Any]]:
    """
    Retorna sugestões de tecnologias para uma categoria.
    
    Args:
        category: Categoria (languages, frameworks, databases, etc.)
        
    Returns:
        Lista de sugestões ordenadas por popularidade
    """
    suggestions = TECHNOLOGY_SUGGESTIONS.get(category, [])
    return sorted(suggestions, key=lambda x: x.get("popularity", 0), reverse=True)


def format_compensation_summary(data: Dict[str, Any]) -> str:
    """
    Formata um resumo de remuneração para exibição no chat.
    
    Args:
        data: Dados de remuneração do painel
        
    Returns:
        String formatada para exibição
    """
    currency = data.get("salary_currency", "R$")
    salary_min = data.get("salary_min", 0)
    salary_max = data.get("salary_max", 0)
    
    summary = f"""💰 **REMUNERAÇÃO E BENEFÍCIOS**

**SALÁRIO BASE (CLT)**
• Faixa: {currency} {salary_min:,.2f} - {currency} {salary_max:,.2f}
"""
    
    if data.get("has_bonus"):
        bonus_min = data.get("bonus_min", 0)
        bonus_max = data.get("bonus_max", 0)
        bonus_type = data.get("bonus_type", "Anual")
        summary += f"""
**BÔNUS {bonus_type.upper()}**
• Faixa: {currency} {bonus_min:,.2f} - {currency} {bonus_max:,.2f}
"""
        if data.get("bonus_criteria"):
            summary += f"• Critérios: {data['bonus_criteria']}\n"
    
    if data.get("benefits"):
        summary += "\n**BENEFÍCIOS**\n"
        for benefit in data["benefits"]:
            if isinstance(benefit, dict):
                label = benefit.get("label", benefit.get("value", ""))
                value = benefit.get("amount")
                if value:
                    summary += f"• {label} ({value})\n"
                else:
                    summary += f"• {label}\n"
            else:
                benefit_info = next(
                    (b for b in BENEFITS_CATALOG if b["value"] == benefit),
                    None
                )
                if benefit_info:
                    summary += f"• {benefit_info['label']}\n"
                else:
                    summary += f"• {benefit}\n"
    
    if data.get("observations"):
        summary += f"\n**OBSERVAÇÕES**\n• {data['observations']}\n"
    
    return summary
