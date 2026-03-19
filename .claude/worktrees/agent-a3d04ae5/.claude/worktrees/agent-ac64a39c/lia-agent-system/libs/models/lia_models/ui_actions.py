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
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


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


CURRENCY_CONFIG = {
    "default_currency": "BRL",
    "supported_currencies": [
        {"code": "BRL", "symbol": "R$", "name": "Real Brasileiro", "locale": "pt-BR"},
        {"code": "USD", "symbol": "$", "name": "Dólar Americano", "locale": "en-US"},
        {"code": "EUR", "symbol": "€", "name": "Euro", "locale": "de-DE"},
    ],
    "format_options": {
        "minimumFractionDigits": 2,
        "maximumFractionDigits": 2,
    },
    "validation": {
        "min_value": 0,
        "max_value": 10000000,
        "step": 100,
    }
}

BENEFITS_CATALOG = [
    {"value": "vale_refeicao", "label": "Vale Refeição", "has_value": True, "default_value": 30, "unit": "dia", "category": "alimentacao"},
    {"value": "vale_alimentacao", "label": "Vale Alimentação", "has_value": True, "default_value": 600, "unit": "mês", "category": "alimentacao"},
    {"value": "vale_transporte", "label": "Vale Transporte", "has_value": False, "category": "mobilidade"},
    {"value": "auxilio_combustivel", "label": "Auxílio Combustível", "has_value": True, "default_value": 400, "unit": "mês", "category": "mobilidade"},
    {"value": "plano_saude", "label": "Plano de Saúde", "has_value": True, "default_value": None, "unit": "mês", "category": "saude", "providers": ["Unimed", "Bradesco Saúde", "SulAmérica", "Amil", "NotreDame Intermédica", "Porto Seguro"]},
    {"value": "plano_saude_dependentes", "label": "Plano de Saúde (Dependentes)", "has_value": False, "category": "saude"},
    {"value": "plano_odonto", "label": "Plano Odontológico", "has_value": False, "category": "saude"},
    {"value": "plano_odonto_dependentes", "label": "Plano Odontológico (Dependentes)", "has_value": False, "category": "saude"},
    {"value": "seguro_vida", "label": "Seguro de Vida", "has_value": True, "default_value": 24, "unit": "salários", "category": "seguranca"},
    {"value": "previdencia_privada", "label": "Previdência Privada", "has_value": True, "default_value": 100, "unit": "% match", "category": "seguranca"},
    {"value": "gympass", "label": "Gympass/TotalPass", "has_value": True, "default_value": None, "unit": "plano", "category": "bem_estar", "plans": ["Basic", "Gold", "Platinum", "Diamond"]},
    {"value": "auxilio_academia", "label": "Auxílio Academia", "has_value": True, "default_value": 150, "unit": "mês", "category": "bem_estar"},
    {"value": "auxilio_saude_mental", "label": "Auxílio Saúde Mental", "has_value": True, "default_value": 200, "unit": "mês", "category": "bem_estar"},
    {"value": "stock_options", "label": "Stock Options / RSUs", "has_value": True, "default_value": None, "unit": "vesting", "category": "incentivos"},
    {"value": "ppr_plr", "label": "PPR/PLR", "has_value": True, "default_value": None, "unit": "salários/ano", "category": "incentivos"},
    {"value": "auxilio_home_office", "label": "Auxílio Home Office", "has_value": True, "default_value": 200, "unit": "mês", "category": "trabalho"},
    {"value": "notebook_empresa", "label": "Notebook da Empresa", "has_value": False, "category": "trabalho"},
    {"value": "celular_corporativo", "label": "Celular Corporativo", "has_value": False, "category": "trabalho"},
    {"value": "auxilio_educacao", "label": "Auxílio Educação", "has_value": True, "default_value": 1500, "unit": "mês", "category": "desenvolvimento"},
    {"value": "auxilio_idiomas", "label": "Auxílio Idiomas", "has_value": True, "default_value": 300, "unit": "mês", "category": "desenvolvimento"},
    {"value": "auxilio_certificacoes", "label": "Auxílio Certificações", "has_value": True, "default_value": 5000, "unit": "ano", "category": "desenvolvimento"},
    {"value": "day_off_aniversario", "label": "Day Off de Aniversário", "has_value": False, "category": "folgas"},
    {"value": "short_friday", "label": "Short Friday", "has_value": False, "category": "folgas"},
    {"value": "ferias_extra", "label": "Férias Extras", "has_value": True, "default_value": 5, "unit": "dias/ano", "category": "folgas"},
    {"value": "licenca_maternidade_estendida", "label": "Licença Maternidade Estendida", "has_value": True, "default_value": 6, "unit": "meses", "category": "familia"},
    {"value": "licenca_paternidade_estendida", "label": "Licença Paternidade Estendida", "has_value": True, "default_value": 20, "unit": "dias", "category": "familia"},
    {"value": "auxilio_creche", "label": "Auxílio Creche", "has_value": True, "default_value": 800, "unit": "mês", "category": "familia"},
    {"value": "auxilio_pet", "label": "Auxílio Pet", "has_value": True, "default_value": 100, "unit": "mês", "category": "outros"},
    {"value": "desconto_produtos", "label": "Desconto em Produtos/Serviços", "has_value": True, "default_value": None, "unit": "%", "category": "outros"},
]

TECHNOLOGY_SUGGESTIONS = {
    "languages": [
        {"name": "JavaScript", "category": "frontend", "popularity": 95},
        {"name": "TypeScript", "category": "frontend", "popularity": 90},
        {"name": "Python", "category": "backend", "popularity": 92},
        {"name": "Java", "category": "backend", "popularity": 85},
        {"name": "C#", "category": "backend", "popularity": 78},
        {"name": "Go", "category": "backend", "popularity": 70},
        {"name": "Rust", "category": "systems", "popularity": 65},
        {"name": "Kotlin", "category": "mobile", "popularity": 72},
        {"name": "Swift", "category": "mobile", "popularity": 68},
        {"name": "PHP", "category": "backend", "popularity": 60},
        {"name": "Ruby", "category": "backend", "popularity": 55},
        {"name": "Scala", "category": "backend", "popularity": 45},
        {"name": "Elixir", "category": "backend", "popularity": 40},
        {"name": "Dart", "category": "mobile", "popularity": 50},
        {"name": "C++", "category": "systems", "popularity": 65},
        {"name": "C", "category": "systems", "popularity": 55},
        {"name": "SQL", "category": "data", "popularity": 90},
        {"name": "R", "category": "data", "popularity": 50},
    ],
    "frameworks": [
        {"name": "React", "category": "frontend", "language": "JavaScript/TypeScript", "popularity": 95},
        {"name": "Next.js", "category": "fullstack", "language": "JavaScript/TypeScript", "popularity": 88},
        {"name": "Vue.js", "category": "frontend", "language": "JavaScript/TypeScript", "popularity": 75},
        {"name": "Angular", "category": "frontend", "language": "TypeScript", "popularity": 70},
        {"name": "Node.js", "category": "backend", "language": "JavaScript/TypeScript", "popularity": 90},
        {"name": "Express.js", "category": "backend", "language": "JavaScript/TypeScript", "popularity": 85},
        {"name": "NestJS", "category": "backend", "language": "TypeScript", "popularity": 70},
        {"name": "Django", "category": "backend", "language": "Python", "popularity": 82},
        {"name": "FastAPI", "category": "backend", "language": "Python", "popularity": 78},
        {"name": "Flask", "category": "backend", "language": "Python", "popularity": 72},
        {"name": "Spring Boot", "category": "backend", "language": "Java", "popularity": 80},
        {"name": ".NET Core", "category": "backend", "language": "C#", "popularity": 75},
        {"name": "Ruby on Rails", "category": "backend", "language": "Ruby", "popularity": 55},
        {"name": "Laravel", "category": "backend", "language": "PHP", "popularity": 60},
        {"name": "React Native", "category": "mobile", "language": "JavaScript/TypeScript", "popularity": 78},
        {"name": "Flutter", "category": "mobile", "language": "Dart", "popularity": 72},
        {"name": "SwiftUI", "category": "mobile", "language": "Swift", "popularity": 65},
        {"name": "Jetpack Compose", "category": "mobile", "language": "Kotlin", "popularity": 60},
        {"name": "TailwindCSS", "category": "frontend", "language": "CSS", "popularity": 85},
        {"name": "Bootstrap", "category": "frontend", "language": "CSS", "popularity": 70},
    ],
    "databases": [
        {"name": "PostgreSQL", "category": "relational", "popularity": 90},
        {"name": "MySQL", "category": "relational", "popularity": 85},
        {"name": "SQL Server", "category": "relational", "popularity": 75},
        {"name": "Oracle", "category": "relational", "popularity": 60},
        {"name": "MongoDB", "category": "nosql", "popularity": 82},
        {"name": "Redis", "category": "cache", "popularity": 88},
        {"name": "Elasticsearch", "category": "search", "popularity": 75},
        {"name": "DynamoDB", "category": "nosql", "popularity": 65},
        {"name": "Cassandra", "category": "nosql", "popularity": 50},
        {"name": "Neo4j", "category": "graph", "popularity": 45},
        {"name": "InfluxDB", "category": "timeseries", "popularity": 40},
        {"name": "ClickHouse", "category": "analytics", "popularity": 55},
        {"name": "Supabase", "category": "baas", "popularity": 60},
        {"name": "Firebase", "category": "baas", "popularity": 72},
    ],
    "cloud_devops": [
        {"name": "AWS", "category": "cloud", "popularity": 90},
        {"name": "Azure", "category": "cloud", "popularity": 78},
        {"name": "GCP", "category": "cloud", "popularity": 72},
        {"name": "Docker", "category": "containers", "popularity": 92},
        {"name": "Kubernetes", "category": "orchestration", "popularity": 85},
        {"name": "Terraform", "category": "iac", "popularity": 80},
        {"name": "Ansible", "category": "iac", "popularity": 65},
        {"name": "Jenkins", "category": "ci_cd", "popularity": 70},
        {"name": "GitHub Actions", "category": "ci_cd", "popularity": 82},
        {"name": "GitLab CI", "category": "ci_cd", "popularity": 72},
        {"name": "CircleCI", "category": "ci_cd", "popularity": 55},
        {"name": "ArgoCD", "category": "gitops", "popularity": 60},
        {"name": "Prometheus", "category": "monitoring", "popularity": 78},
        {"name": "Grafana", "category": "monitoring", "popularity": 80},
        {"name": "Datadog", "category": "monitoring", "popularity": 72},
        {"name": "New Relic", "category": "monitoring", "popularity": 65},
        {"name": "Nginx", "category": "web_server", "popularity": 85},
        {"name": "Apache Kafka", "category": "messaging", "popularity": 75},
        {"name": "RabbitMQ", "category": "messaging", "popularity": 68},
    ],
    "tools": [
        {"name": "Git", "category": "version_control", "popularity": 98},
        {"name": "GitHub", "category": "platform", "popularity": 95},
        {"name": "GitLab", "category": "platform", "popularity": 75},
        {"name": "Bitbucket", "category": "platform", "popularity": 60},
        {"name": "Jira", "category": "project_management", "popularity": 82},
        {"name": "Confluence", "category": "documentation", "popularity": 70},
        {"name": "Notion", "category": "documentation", "popularity": 75},
        {"name": "Slack", "category": "communication", "popularity": 88},
        {"name": "VS Code", "category": "ide", "popularity": 90},
        {"name": "IntelliJ IDEA", "category": "ide", "popularity": 72},
        {"name": "Postman", "category": "api_testing", "popularity": 85},
        {"name": "Insomnia", "category": "api_testing", "popularity": 55},
        {"name": "Figma", "category": "design", "popularity": 88},
        {"name": "Storybook", "category": "ui_components", "popularity": 72},
    ],
}

COMPETENCY_DESCRIPTIONS = {
    "communication": {
        "label": "Comunicação",
        "description": "Capacidade de transmitir ideias de forma clara e eficaz, tanto verbalmente quanto por escrito. Inclui escuta ativa e adaptação da mensagem ao público.",
        "behaviors": [
            "Expressa ideias de forma clara e concisa",
            "Pratica escuta ativa",
            "Adapta a comunicação ao público",
            "Dá e recebe feedback construtivo",
        ],
        "interview_questions": [
            "Descreva uma situação em que você precisou explicar algo complexo para alguém sem conhecimento técnico.",
            "Como você lida com conflitos de comunicação em equipe?",
        ],
    },
    "teamwork": {
        "label": "Trabalho em Equipe",
        "description": "Habilidade de colaborar efetivamente com outros, contribuindo para objetivos compartilhados e apoiando colegas.",
        "behaviors": [
            "Contribui ativamente para o grupo",
            "Oferece ajuda proativamente",
            "Respeita opiniões diferentes",
            "Compartilha conhecimento",
        ],
        "interview_questions": [
            "Conte sobre um projeto em que você trabalhou em equipe. Qual foi seu papel?",
            "Como você lida quando discorda de uma decisão do time?",
        ],
    },
    "leadership": {
        "label": "Liderança",
        "description": "Capacidade de inspirar, motivar e guiar outros em direção a objetivos comuns. Inclui tomada de decisão e responsabilidade.",
        "behaviors": [
            "Inspira e motiva outros",
            "Assume responsabilidade por decisões",
            "Desenvolve pessoas",
            "Define direção clara",
        ],
        "interview_questions": [
            "Descreva uma situação em que você liderou uma iniciativa ou projeto.",
            "Como você desenvolve membros do seu time?",
        ],
    },
    "problem_solving": {
        "label": "Resolução de Problemas",
        "description": "Habilidade de identificar, analisar e resolver problemas de forma eficaz e criativa.",
        "behaviors": [
            "Identifica a causa raiz dos problemas",
            "Propõe soluções criativas",
            "Avalia alternativas sistematicamente",
            "Implementa soluções eficazes",
        ],
        "interview_questions": [
            "Conte sobre um problema complexo que você resolveu. Como abordou?",
            "Descreva uma situação em que uma solução inicial não funcionou. O que fez?",
        ],
    },
    "adaptability": {
        "label": "Adaptabilidade",
        "description": "Flexibilidade para se ajustar a mudanças, novos ambientes e situações inesperadas.",
        "behaviors": [
            "Aceita mudanças positivamente",
            "Aprende rapidamente com novos contextos",
            "Mantém produtividade sob pressão",
            "Ajusta abordagem quando necessário",
        ],
        "interview_questions": [
            "Conte sobre uma mudança significativa no trabalho. Como se adaptou?",
            "Como você lida com prioridades que mudam frequentemente?",
        ],
    },
    "creativity": {
        "label": "Criatividade",
        "description": "Capacidade de gerar ideias originais e encontrar abordagens inovadoras para desafios.",
        "behaviors": [
            "Propõe ideias inovadoras",
            "Questiona o status quo construtivamente",
            "Conecta conceitos de formas novas",
            "Experimenta abordagens diferentes",
        ],
        "interview_questions": [
            "Descreva uma ideia inovadora que você implementou.",
            "Como você estimula a criatividade no seu trabalho diário?",
        ],
    },
    "time_management": {
        "label": "Gestão de Tempo",
        "description": "Habilidade de organizar e priorizar tarefas para maximizar produtividade e cumprir prazos.",
        "behaviors": [
            "Prioriza tarefas eficazmente",
            "Cumpre prazos consistentemente",
            "Evita procrastinação",
            "Equilibra múltiplas demandas",
        ],
        "interview_questions": [
            "Como você organiza seu dia de trabalho?",
            "Conte sobre uma situação em que teve que gerenciar múltiplos prazos apertados.",
        ],
    },
    "critical_thinking": {
        "label": "Pensamento Crítico",
        "description": "Capacidade de analisar informações objetivamente e fazer julgamentos fundamentados.",
        "behaviors": [
            "Questiona suposições",
            "Avalia evidências objetivamente",
            "Identifica vieses e falácias",
            "Toma decisões baseadas em dados",
        ],
        "interview_questions": [
            "Descreva uma decisão importante que você tomou. Como avaliou as opções?",
            "Como você valida informações antes de agir?",
        ],
    },
    "emotional_intelligence": {
        "label": "Inteligência Emocional",
        "description": "Capacidade de reconhecer, entender e gerenciar emoções próprias e dos outros.",
        "behaviors": [
            "Reconhece e gerencia próprias emoções",
            "Demonstra empatia",
            "Navega situações sociais com habilidade",
            "Constrói relacionamentos positivos",
        ],
        "interview_questions": [
            "Conte sobre uma situação difícil emocionalmente no trabalho. Como lidou?",
            "Como você percebe quando um colega está passando por dificuldades?",
        ],
    },
    "autonomy": {
        "label": "Autonomia",
        "description": "Capacidade de trabalhar independentemente, tomando iniciativa e sendo responsável pelos resultados.",
        "behaviors": [
            "Toma iniciativa sem esperar instruções",
            "Assume responsabilidade por resultados",
            "Busca soluções independentemente",
            "Pede ajuda quando necessário",
        ],
        "interview_questions": [
            "Conte sobre um projeto que você conduziu do início ao fim sem supervisão direta.",
            "Como você decide quando pedir ajuda versus resolver algo sozinho?",
        ],
    },
    "analytical_thinking": {
        "label": "Pensamento Analítico",
        "description": "Habilidade de decompor problemas complexos em partes menores e analisá-los sistematicamente.",
        "behaviors": [
            "Decompõe problemas em partes menores",
            "Identifica padrões e tendências",
            "Usa dados para fundamentar análises",
            "Documenta raciocínio de forma clara",
        ],
        "interview_questions": [
            "Descreva como você abordaria a análise de um problema complexo de negócio.",
            "Conte sobre uma análise de dados que você conduziu e os insights gerados.",
        ],
    },
    "customer_focus": {
        "label": "Foco no Cliente",
        "description": "Compromisso em entender e atender às necessidades dos clientes (internos ou externos).",
        "behaviors": [
            "Prioriza necessidades do cliente",
            "Busca feedback ativamente",
            "Antecipa necessidades futuras",
            "Resolve problemas rapidamente",
        ],
        "interview_questions": [
            "Conte sobre uma situação em que você foi além para atender um cliente.",
            "Como você lida com clientes insatisfeitos?",
        ],
    },
    "results_orientation": {
        "label": "Orientação para Resultados",
        "description": "Foco em atingir metas e entregar resultados de alta qualidade.",
        "behaviors": [
            "Define metas claras e mensuráveis",
            "Persiste diante de obstáculos",
            "Monitora progresso regularmente",
            "Celebra conquistas e aprende com falhas",
        ],
        "interview_questions": [
            "Qual foi sua maior conquista profissional? Como alcançou?",
            "Conte sobre uma meta desafiadora que você atingiu.",
        ],
    },
    "strategic_thinking": {
        "label": "Pensamento Estratégico",
        "description": "Capacidade de ver o quadro geral e alinhar ações com objetivos de longo prazo.",
        "behaviors": [
            "Considera impacto de longo prazo",
            "Alinha ações com objetivos maiores",
            "Antecipa tendências e mudanças",
            "Balanceia curto e longo prazo",
        ],
        "interview_questions": [
            "Descreva uma decisão estratégica que você influenciou.",
            "Como você equilibra demandas urgentes com objetivos de longo prazo?",
        ],
    },
}

LANGUAGES_CATALOG = [
    {"code": "pt-BR", "name": "Português (Brasil)", "native_name": "Português", "flag": "🇧🇷"},
    {"code": "en-US", "name": "Inglês (EUA)", "native_name": "English", "flag": "🇺🇸"},
    {"code": "en-GB", "name": "Inglês (UK)", "native_name": "English", "flag": "🇬🇧"},
    {"code": "es", "name": "Espanhol", "native_name": "Español", "flag": "🇪🇸"},
    {"code": "es-MX", "name": "Espanhol (México)", "native_name": "Español", "flag": "🇲🇽"},
    {"code": "fr", "name": "Francês", "native_name": "Français", "flag": "🇫🇷"},
    {"code": "de", "name": "Alemão", "native_name": "Deutsch", "flag": "🇩🇪"},
    {"code": "it", "name": "Italiano", "native_name": "Italiano", "flag": "🇮🇹"},
    {"code": "zh-CN", "name": "Chinês (Mandarim)", "native_name": "中文", "flag": "🇨🇳"},
    {"code": "ja", "name": "Japonês", "native_name": "日本語", "flag": "🇯🇵"},
    {"code": "ko", "name": "Coreano", "native_name": "한국어", "flag": "🇰🇷"},
    {"code": "ru", "name": "Russo", "native_name": "Русский", "flag": "🇷🇺"},
    {"code": "ar", "name": "Árabe", "native_name": "العربية", "flag": "🇸🇦"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "flag": "🇮🇳"},
    {"code": "nl", "name": "Holandês", "native_name": "Nederlands", "flag": "🇳🇱"},
    {"code": "pl", "name": "Polonês", "native_name": "Polski", "flag": "🇵🇱"},
    {"code": "tr", "name": "Turco", "native_name": "Türkçe", "flag": "🇹🇷"},
    {"code": "sv", "name": "Sueco", "native_name": "Svenska", "flag": "🇸🇪"},
    {"code": "he", "name": "Hebraico", "native_name": "עברית", "flag": "🇮🇱"},
    {"code": "pt-PT", "name": "Português (Portugal)", "native_name": "Português", "flag": "🇵🇹"},
]

LANGUAGE_LEVELS = [
    {"value": "basic", "label": "Básico", "cefr": "A1-A2", "description": "Comunicação básica, vocabulário limitado"},
    {"value": "intermediate", "label": "Intermediário", "cefr": "B1-B2", "description": "Conversação fluente em contextos familiares"},
    {"value": "advanced", "label": "Avançado", "cefr": "C1", "description": "Comunicação eficaz em contextos profissionais complexos"},
    {"value": "fluent", "label": "Fluente", "cefr": "C2", "description": "Domínio quase nativo, nuances e expressões idiomáticas"},
    {"value": "native", "label": "Nativo", "cefr": "-", "description": "Língua materna"},
]

WSI_QUESTION_TEMPLATES = {
    "tech": {
        "area": "Tecnologia",
        "templates": [
            {
                "question": "Descreva como você abordaria a refatoração de um sistema legado crítico para a empresa. Quais critérios usaria para priorizar o que refatorar primeiro?",
                "bloom_level": "Analisar",
                "dreyfus_level": "Proficiente",
                "competency": "Pensamento Analítico",
                "time_estimate": "10-15 min",
            },
            {
                "question": "Você recebeu um relatório de bug crítico em produção às 22h. Descreva passo a passo como você investigaria e resolveria o problema.",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Resolução de Problemas",
                "time_estimate": "10 min",
            },
            {
                "question": "Projete a arquitetura de um sistema de notificações em tempo real para 1 milhão de usuários simultâneos. Quais tecnologias e padrões você utilizaria?",
                "bloom_level": "Criar",
                "dreyfus_level": "Expert",
                "competency": "Pensamento Estratégico",
                "time_estimate": "15-20 min",
            },
            {
                "question": "Como você garantiria a qualidade do código em um time de 10 desenvolvedores? Descreva processos, ferramentas e métricas.",
                "bloom_level": "Avaliar",
                "dreyfus_level": "Proficiente",
                "competency": "Liderança",
                "time_estimate": "10 min",
            },
        ],
    },
    "sales": {
        "area": "Vendas",
        "templates": [
            {
                "question": "Um cliente estratégico está considerando um concorrente. Descreva sua estratégia para reconquistar esse cliente.",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Orientação para Resultados",
                "time_estimate": "10 min",
            },
            {
                "question": "Como você estruturaria uma apresentação de vendas para um CFO focado em ROI? Inclua as principais métricas que destacaria.",
                "bloom_level": "Criar",
                "dreyfus_level": "Proficiente",
                "competency": "Comunicação",
                "time_estimate": "10-15 min",
            },
            {
                "question": "Descreva como você gerenciaria um pipeline de 50 oportunidades em diferentes estágios. Quais critérios usaria para priorização?",
                "bloom_level": "Analisar",
                "dreyfus_level": "Competente",
                "competency": "Gestão de Tempo",
                "time_estimate": "10 min",
            },
        ],
    },
    "marketing": {
        "area": "Marketing",
        "templates": [
            {
                "question": "Projete uma campanha de lançamento de produto B2B com orçamento limitado de R$50.000. Inclua canais, métricas e cronograma.",
                "bloom_level": "Criar",
                "dreyfus_level": "Proficiente",
                "competency": "Criatividade",
                "time_estimate": "15 min",
            },
            {
                "question": "Analise os resultados de uma campanha fictícia: CTR 2%, conversão 1.5%, CAC R$150. Quais otimizações você sugeriria?",
                "bloom_level": "Avaliar",
                "dreyfus_level": "Competente",
                "competency": "Pensamento Analítico",
                "time_estimate": "10 min",
            },
        ],
    },
    "hr": {
        "area": "Recursos Humanos",
        "templates": [
            {
                "question": "Um colaborador de alta performance apresentou queda de produtividade nos últimos 3 meses. Como você abordaria essa situação?",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Inteligência Emocional",
                "time_estimate": "10 min",
            },
            {
                "question": "Desenhe um programa de desenvolvimento de liderança para média gerência. Inclua formato, duração e métricas de sucesso.",
                "bloom_level": "Criar",
                "dreyfus_level": "Proficiente",
                "competency": "Liderança",
                "time_estimate": "15 min",
            },
            {
                "question": "Como você conduziria um processo de demissão em massa (10% do quadro) minimizando impacto na cultura?",
                "bloom_level": "Analisar",
                "dreyfus_level": "Proficiente",
                "competency": "Pensamento Estratégico",
                "time_estimate": "10-15 min",
            },
        ],
    },
    "finance": {
        "area": "Finanças",
        "templates": [
            {
                "question": "A empresa precisa reduzir 20% dos custos operacionais. Como você estruturaria a análise e priorizaria as áreas de corte?",
                "bloom_level": "Analisar",
                "dreyfus_level": "Proficiente",
                "competency": "Pensamento Analítico",
                "time_estimate": "15 min",
            },
            {
                "question": "Avalie um projeto de investimento com VPL positivo mas TIR abaixo do WACC. Você aprovaria? Justifique.",
                "bloom_level": "Avaliar",
                "dreyfus_level": "Competente",
                "competency": "Pensamento Crítico",
                "time_estimate": "10 min",
            },
        ],
    },
    "operations": {
        "area": "Operações",
        "templates": [
            {
                "question": "Descreva como você implementaria uma metodologia ágil em uma equipe que nunca trabalhou dessa forma.",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Liderança",
                "time_estimate": "10 min",
            },
            {
                "question": "Um fornecedor estratégico anunciou aumento de 40% nos preços. Quais alternativas você exploraria?",
                "bloom_level": "Analisar",
                "dreyfus_level": "Proficiente",
                "competency": "Resolução de Problemas",
                "time_estimate": "10-15 min",
            },
        ],
    },
    "leadership": {
        "area": "Liderança Geral",
        "templates": [
            {
                "question": "Você assumiu um time desmotivado após a saída do gestor anterior. Quais seriam suas primeiras ações nos 90 dias?",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Liderança",
                "time_estimate": "15 min",
            },
            {
                "question": "Dois membros seniores do seu time têm um conflito que está afetando a equipe. Como você mediaria?",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Competente",
                "competency": "Inteligência Emocional",
                "time_estimate": "10 min",
            },
            {
                "question": "Descreva como você daria feedback negativo a um colaborador que é sensível a críticas.",
                "bloom_level": "Aplicar",
                "dreyfus_level": "Iniciante Avançado",
                "competency": "Comunicação",
                "time_estimate": "8 min",
            },
        ],
    },
}

CALENDAR_INTEGRATION_CONFIG = {
    "providers": [
        {"id": "google", "name": "Google Calendar", "icon": "📅", "oauth_required": True},
        {"id": "outlook", "name": "Microsoft Outlook", "icon": "📆", "oauth_required": True},
        {"id": "apple", "name": "Apple Calendar", "icon": "🗓️", "oauth_required": True},
        {"id": "manual", "name": "Inserção Manual", "icon": "✏️", "oauth_required": False},
    ],
    "slot_durations": [
        {"value": 30, "label": "30 minutos"},
        {"value": 45, "label": "45 minutos"},
        {"value": 60, "label": "1 hora"},
        {"value": 90, "label": "1h30"},
        {"value": 120, "label": "2 horas"},
    ],
    "meeting_types": [
        {"value": "presencial", "label": "Presencial", "icon": "🏢", "requires_location": True},
        {"value": "teams", "label": "Microsoft Teams", "icon": "💬", "auto_link": True},
        {"value": "meet", "label": "Google Meet", "icon": "🎥", "auto_link": True},
        {"value": "zoom", "label": "Zoom", "icon": "📹", "auto_link": True},
        {"value": "phone", "label": "Telefone", "icon": "📞", "requires_phone": True},
    ],
    "buffer_options": [
        {"value": 0, "label": "Sem intervalo"},
        {"value": 5, "label": "5 minutos"},
        {"value": 10, "label": "10 minutos"},
        {"value": 15, "label": "15 minutos"},
        {"value": 30, "label": "30 minutos"},
    ],
    "working_hours": {
        "default_start": "09:00",
        "default_end": "18:00",
        "lunch_start": "12:00",
        "lunch_end": "13:00",
    },
    "reminder_options": [
        {"value": 15, "label": "15 minutos antes"},
        {"value": 30, "label": "30 minutos antes"},
        {"value": 60, "label": "1 hora antes"},
        {"value": 1440, "label": "1 dia antes"},
    ],
}


AGENT_UI_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "job_planner": {
        "description": "Agente de Planejamento de Vaga - coleta requisitos da vaga",
        "ui_actions": [
            {
                "trigger": "collect_compensation",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.COMPENSATION_BENEFITS,
                "title": "Remuneração e Benefícios",
                "chat_intro": "Agora vamos para a remuneração. Vou abrir um painel lateral com todos os campos relacionados.",
                "chat_confirm": "Recebi! Deixa eu confirmar o que você preencheu:",
                "fields": [
                    {"name": "salary_min", "label": "Salário Mínimo", "type": "currency", "required": True},
                    {"name": "salary_max", "label": "Salário Máximo", "type": "currency", "required": True},
                    {"name": "bonus_min", "label": "Bônus Mínimo", "type": "currency"},
                    {"name": "bonus_max", "label": "Bônus Máximo", "type": "currency"},
                    {"name": "bonus_criteria", "label": "Critérios do Bônus", "type": "text"},
                    {"name": "benefits", "label": "Benefícios", "type": "checkbox_list"},
                    {"name": "observations", "label": "Observações", "type": "textarea"},
                ],
            },
            {
                "trigger": "collect_technical_requirements",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.TECHNICAL_REQUIREMENTS,
                "title": "Requisitos Técnicos",
                "chat_intro": "Vamos definir os requisitos técnicos. Abrindo o painel de tecnologias...",
                "fields": [
                    {"name": "languages", "label": "Linguagens de Programação", "type": "tech_table"},
                    {"name": "frameworks", "label": "Frameworks e Bibliotecas", "type": "tech_table"},
                    {"name": "databases", "label": "Bancos de Dados", "type": "tech_table"},
                    {"name": "cloud", "label": "Cloud e DevOps", "type": "tech_table"},
                    {"name": "tools", "label": "Ferramentas", "type": "tech_table"},
                ],
            },
            {
                "trigger": "collect_behavioral_competencies",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.BEHAVIORAL_COMPETENCIES,
                "title": "Competências Comportamentais",
                "chat_intro": "Agora as competências comportamentais. Essas são importantes para o fit cultural!",
                "fields": [
                    {"name": "competencies", "label": "Competências", "type": "competency_slider"},
                ],
            },
            {
                "trigger": "collect_languages",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.LANGUAGES,
                "title": "Idiomas",
                "chat_intro": "Vamos aos idiomas necessários para a posição.",
                "fields": [
                    {"name": "languages", "label": "Idiomas", "type": "language_table"},
                ],
            },
            {
                "trigger": "collect_wsi_questions",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.WSI_QUESTIONS,
                "title": "Perguntas WSI",
                "chat_intro": "Vamos definir as perguntas de Work Sample Interview (WSI).",
                "fields": [
                    {"name": "questions", "label": "Perguntas", "type": "wsi_question_list"},
                ],
            },
            {
                "trigger": "show_job_summary",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.JOB_SUMMARY,
                "title": "Resumo da Vaga",
            },
        ],
    },
    
    "sourcing": {
        "description": "Agente de Sourcing - busca e engajamento de candidatos",
        "ui_actions": [
            {
                "trigger": "show_search_results",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.SEARCH_RESULTS_PREVIEW,
                "title": "Resultados da Busca",
            },
            {
                "trigger": "show_candidate_preview",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.CANDIDATE_SUMMARY,
                "title": "Perfil do Candidato",
            },
            {
                "trigger": "request_calibration",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.CALIBRATION_FEEDBACK,
                "title": "Calibração de Busca",
                "chat_intro": "Preciso da sua ajuda para calibrar a busca. Vou mostrar alguns perfis de amostra.",
            },
            {
                "trigger": "confirm_add_candidates",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.CONFIRM_PROCEED,
                "title": "Confirmar Adição",
            },
        ],
    },
    
    "cv_screening": {
        "description": "Agente de Triagem de CV - análise e scoring de currículos",
        "ui_actions": [
            {
                "trigger": "show_cv_analysis",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.CANDIDATE_PROFILE,
                "title": "Análise do CV",
            },
            {
                "trigger": "show_wsi_score",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.WSI_SCORE,
                "title": "Score WSI",
            },
            {
                "trigger": "request_evaluation",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.CANDIDATE_EVALUATION,
                "title": "Avaliação do Candidato",
                "chat_intro": "Preciso que você avalie este candidato. Abrindo o painel de avaliação...",
            },
        ],
    },
    
    "interviewer": {
        "description": "Agente Entrevistador - conduz entrevistas WSI",
        "ui_actions": [
            {
                "trigger": "show_interview_guide",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.WSI_QUESTIONS,
                "title": "Roteiro da Entrevista",
            },
            {
                "trigger": "record_response",
                "component_type": UIComponentType.INLINE_FORM,
                "component_subtype": "interview_response",
                "title": "Registrar Resposta",
            },
        ],
    },
    
    "wsi_evaluator": {
        "description": "Agente Avaliador WSI - avalia respostas e gera parecer",
        "ui_actions": [
            {
                "trigger": "show_evaluation_result",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.WSI_SCORE,
                "title": "Resultado da Avaliação",
            },
            {
                "trigger": "request_parecer_review",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.CANDIDATE_EVALUATION,
                "title": "Revisar Parecer",
                "chat_intro": "Gerei um parecer para este candidato. Você pode revisar antes de salvar.",
            },
        ],
    },
    
    "scheduling": {
        "description": "Agente de Agendamento - gerencia agenda de entrevistas",
        "ui_actions": [
            {
                "trigger": "show_available_slots",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.INTERVIEW_SCHEDULING,
                "title": "Agendar Entrevista",
                "chat_intro": "Vou abrir o painel de agendamento para você selecionar o melhor horário.",
            },
            {
                "trigger": "confirm_scheduling",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.INTERVIEW_CONFIRMATION,
                "title": "Entrevista Agendada",
            },
            {
                "trigger": "request_reschedule",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.SCHEDULE_OPTIONS,
                "title": "Reagendar",
            },
        ],
    },
    
    "analyst_feedback": {
        "description": "Agente de Analytics e Feedback - métricas e feedback",
        "ui_actions": [
            {
                "trigger": "show_market_analysis",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.MARKET_ANALYSIS,
                "title": "Análise de Mercado",
            },
            {
                "trigger": "show_pipeline_progress",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.PROGRESS_TRACKER,
                "title": "Progresso do Pipeline",
            },
            {
                "trigger": "request_rejection_reason",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.SELECT_OPTION,
                "title": "Motivo da Reprovação",
            },
        ],
    },
    
    "recruiter_assistant": {
        "description": "Agente Assistente do Recrutador - proativo e contextual",
        "ui_actions": [
            {
                "trigger": "show_daily_briefing",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.PROGRESS_TRACKER,
                "title": "Briefing Diário",
            },
            {
                "trigger": "suggest_action",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.CONFIRM_PROCEED,
                "title": "Sugestão de Ação",
            },
            {
                "trigger": "show_notification",
                "component_type": UIComponentType.NOTIFICATION,
                "component_subtype": "proactive_alert",
                "title": "Alerta Proativo",
            },
        ],
    },
    
    "ats_integrator": {
        "description": "Agente de Integração ATS - sincronização com ATSs externos",
        "ui_actions": [
            {
                "trigger": "show_sync_status",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.SYNC_STATUS,
                "title": "Status da Sincronização",
                "chat_intro": "Aqui está o status atual da sincronização com o ATS.",
            },
            {
                "trigger": "request_field_mapping",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.ATS_FIELD_MAPPING,
                "title": "Mapeamento de Campos",
                "chat_intro": "Vou abrir o painel de mapeamento para você configurar a correspondência de campos.",
            },
            {
                "trigger": "show_sync_errors",
                "component_type": UIComponentType.MODAL,
                "component_subtype": "sync_errors",
                "title": "Erros de Sincronização",
            },
            {
                "trigger": "confirm_sync",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.CONFIRM_PROCEED,
                "title": "Confirmar Sincronização",
            },
        ],
    },
    
    "communication": {
        "description": "Agente de Comunicação - emails, WhatsApp e mensagens",
        "ui_actions": [
            {
                "trigger": "show_email_preview",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.EMAIL_PREVIEW,
                "title": "Preview do Email",
                "chat_intro": "Preparei um rascunho do email. Confira abaixo:",
            },
            {
                "trigger": "compose_email",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.EMAIL_COMPOSER,
                "title": "Compor Email",
                "chat_intro": "Abrindo o editor de email para você personalizar a mensagem.",
            },
            {
                "trigger": "show_whatsapp_preview",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.WHATSAPP_PREVIEW,
                "title": "Preview WhatsApp",
                "chat_intro": "Preparei a mensagem de WhatsApp. Confira:",
            },
            {
                "trigger": "compose_whatsapp",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.WHATSAPP_COMPOSER,
                "title": "Compor WhatsApp",
                "chat_intro": "Abrindo o compositor de mensagem WhatsApp.",
            },
            {
                "trigger": "send_message",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.SEND_MESSAGE,
                "title": "Enviar Mensagem",
            },
            {
                "trigger": "select_template",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.SELECT_OPTION,
                "title": "Selecionar Template",
            },
        ],
    },
    
    "analytics": {
        "description": "Agente de Analytics - dashboards e métricas",
        "ui_actions": [
            {
                "trigger": "show_dashboard_preview",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.DASHBOARD_METRICS,
                "title": "Métricas do Dashboard",
                "chat_intro": "Aqui estão as principais métricas do período:",
            },
            {
                "trigger": "show_metrics_card",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.DASHBOARD_METRICS,
                "title": "Resumo de Métricas",
            },
            {
                "trigger": "show_funnel_analysis",
                "component_type": UIComponentType.CHAT_CARD,
                "component_subtype": ChatCardType.PROGRESS_TRACKER,
                "title": "Análise do Funil",
            },
            {
                "trigger": "export_report",
                "component_type": UIComponentType.CHAT_ACTION,
                "component_subtype": ChatActionType.EXPORT_DATA,
                "title": "Exportar Relatório",
            },
            {
                "trigger": "compare_periods",
                "component_type": UIComponentType.SIDE_PANEL,
                "component_subtype": SidePanelType.SEARCH_FILTERS,
                "title": "Comparar Períodos",
                "chat_intro": "Selecione os períodos que deseja comparar.",
            },
        ],
    },
}


WORKFLOW_STEP_UI_MAPPINGS: Dict[str, List[Dict[str, Any]]] = {
    "step_01_greeting": {
        "agent": "recruiter_assistant",
        "ui_actions": ["show_daily_briefing"],
        "description": "Saudação inicial com briefing do dia",
    },
    
    "step_02_job_title": {
        "agent": "job_planner",
        "ui_actions": [],
        "description": "Coleta do título da vaga (apenas chat)",
    },
    
    "step_03_job_type": {
        "agent": "job_planner",
        "ui_actions": [],
        "description": "Define se é criação ou atualização (chat com opções)",
    },
    
    "step_04_basic_info": {
        "agent": "job_planner",
        "ui_actions": [],
        "description": "Área, senioridade, modelo de trabalho (chat sequencial)",
    },
    
    "step_05_compensation": {
        "agent": "job_planner",
        "ui_actions": ["collect_compensation"],
        "description": "Abre painel lateral de Remuneração e Benefícios",
    },
    
    "step_06_technical_requirements": {
        "agent": "job_planner",
        "ui_actions": ["collect_technical_requirements"],
        "description": "Abre painel lateral de Requisitos Técnicos",
    },
    
    "step_07_behavioral_competencies": {
        "agent": "job_planner",
        "ui_actions": ["collect_behavioral_competencies"],
        "description": "Abre painel lateral de Competências Comportamentais",
    },
    
    "step_08_languages": {
        "agent": "job_planner",
        "ui_actions": ["collect_languages"],
        "description": "Abre painel lateral de Idiomas",
    },
    
    "step_09_wsi_questions": {
        "agent": "job_planner",
        "ui_actions": ["collect_wsi_questions"],
        "description": "Abre painel lateral de Perguntas WSI",
    },
    
    "step_10_job_summary": {
        "agent": "job_planner",
        "ui_actions": ["show_job_summary"],
        "description": "Exibe card resumo da vaga no chat para confirmação",
    },
    
    "step_11_calibration": {
        "agent": "sourcing",
        "ui_actions": ["request_calibration"],
        "description": "Abre painel de calibração com candidatos amostra",
    },
    
    "step_12_sourcing_start": {
        "agent": "sourcing",
        "ui_actions": ["show_search_results"],
        "description": "Inicia busca e exibe preview de resultados",
    },
    
    "step_13_candidate_review": {
        "agent": "cv_screening",
        "ui_actions": ["show_cv_analysis", "show_wsi_score"],
        "description": "Análise de CV com score WSI no chat",
    },
    
    "step_14_interview_scheduling": {
        "agent": "scheduling",
        "ui_actions": ["show_available_slots"],
        "description": "Abre painel de agendamento de entrevistas",
    },
    
    "step_15_interview_conduct": {
        "agent": "interviewer",
        "ui_actions": ["show_interview_guide"],
        "description": "Exibe roteiro WSI durante a entrevista",
    },
    
    "step_16_evaluation": {
        "agent": "wsi_evaluator",
        "ui_actions": ["show_evaluation_result", "request_parecer_review"],
        "description": "Avaliação WSI e parecer final",
    },
    
    "step_17_decision": {
        "agent": "analyst_feedback",
        "ui_actions": ["show_pipeline_progress"],
        "description": "Decisão final com análise de pipeline",
    },
}


SIDE_PANEL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    SidePanelType.COMPENSATION_BENEFITS.value: {
        "title": "Remuneração e Benefícios",
        "icon": "💰",
        "currency_config": CURRENCY_CONFIG,
        "sections": [
            {
                "title": "SALÁRIO BASE (CLT)",
                "fields": [
                    {
                        "name": "salary_currency",
                        "label": "Moeda",
                        "type": "currency_select",
                        "options": CURRENCY_CONFIG["supported_currencies"],
                        "default": "BRL",
                    },
                    {
                        "name": "salary_min",
                        "label": "R$ De:",
                        "type": "currency",
                        "required": True,
                        "validation": CURRENCY_CONFIG["validation"],
                        "placeholder": "12.000,00",
                    },
                    {
                        "name": "salary_max",
                        "label": "R$ Até:",
                        "type": "currency",
                        "required": True,
                        "validation": CURRENCY_CONFIG["validation"],
                        "placeholder": "18.000,00",
                    },
                    {
                        "name": "salary_negotiable",
                        "label": "Negociável",
                        "type": "checkbox",
                        "default": False,
                    },
                ],
            },
            {
                "title": "BÔNUS E VARIÁVEL",
                "collapsible": True,
                "default_collapsed": False,
                "fields": [
                    {
                        "name": "has_bonus",
                        "label": "Possui Bônus/Variável",
                        "type": "toggle",
                        "default": False,
                    },
                    {
                        "name": "bonus_type",
                        "label": "Tipo de Bônus",
                        "type": "select",
                        "options": ["Anual", "Semestral", "Trimestral", "Mensal", "Por Projeto"],
                        "depends_on": {"has_bonus": True},
                    },
                    {
                        "name": "bonus_min",
                        "label": "R$ De:",
                        "type": "currency",
                        "validation": CURRENCY_CONFIG["validation"],
                        "depends_on": {"has_bonus": True},
                    },
                    {
                        "name": "bonus_max",
                        "label": "R$ Até:",
                        "type": "currency",
                        "validation": CURRENCY_CONFIG["validation"],
                        "depends_on": {"has_bonus": True},
                    },
                    {
                        "name": "bonus_target",
                        "label": "Target (%)",
                        "type": "percentage",
                        "placeholder": "Ex: 15% do salário anual",
                        "depends_on": {"has_bonus": True},
                    },
                    {
                        "name": "bonus_criteria",
                        "label": "Critérios do Bônus",
                        "type": "text",
                        "placeholder": "Desempenho individual e metas da empresa",
                        "depends_on": {"has_bonus": True},
                    },
                ],
            },
            {
                "title": "BENEFÍCIOS",
                "description": "Selecione os benefícios oferecidos e informe valores quando aplicável",
                "fields": [
                    {
                        "name": "benefits",
                        "type": "benefits_selector",
                        "required": True,
                        "catalog": BENEFITS_CATALOG,
                        "grouped_by": "category",
                        "category_labels": {
                            "alimentacao": "🍽️ Alimentação",
                            "mobilidade": "🚗 Mobilidade",
                            "saude": "🏥 Saúde",
                            "seguranca": "🛡️ Segurança",
                            "bem_estar": "💪 Bem-estar",
                            "incentivos": "💎 Incentivos",
                            "trabalho": "💻 Trabalho",
                            "desenvolvimento": "📚 Desenvolvimento",
                            "folgas": "🏖️ Folgas",
                            "familia": "👨‍👩‍👧 Família",
                            "outros": "📦 Outros",
                        },
                        "allow_custom": True,
                        "custom_label": "+ Adicionar benefício customizado",
                    },
                ],
            },
            {
                "title": "OBSERVAÇÕES ADICIONAIS",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "observations",
                        "label": "Observações",
                        "type": "textarea",
                        "placeholder": "Possibilidade de revisão salarial semestral, outros detalhes...",
                        "max_length": 500,
                    },
                ],
            },
        ],
        "submit_button": "Concluído",
        "summary_template": """
💰 **REMUNERAÇÃO E BENEFÍCIOS**

**SALÁRIO BASE (CLT)**
• Faixa: {salary_currency} {salary_min} - {salary_max}
{salary_negotiable_text}

{bonus_section}

**BENEFÍCIOS**
{benefits_list}

{observations_section}
""",
    },
    
    SidePanelType.TECHNICAL_REQUIREMENTS.value: {
        "title": "Requisitos Técnicos",
        "icon": "💻",
        "technology_suggestions": TECHNOLOGY_SUGGESTIONS,
        "sections": [
            {
                "title": "LINGUAGENS DE PROGRAMAÇÃO",
                "fields": [
                    {
                        "name": "languages",
                        "type": "tech_table",
                        "columns": ["Tecnologia", "Nível", "Obrigatória?"],
                        "level_options": ["Básico", "Intermediário", "Avançado", "Expert"],
                        "suggestions": TECHNOLOGY_SUGGESTIONS["languages"],
                        "autocomplete": True,
                        "min_items": 1,
                        "max_items": 10,
                    },
                ],
            },
            {
                "title": "FRAMEWORKS E BIBLIOTECAS",
                "fields": [
                    {
                        "name": "frameworks",
                        "type": "tech_table",
                        "columns": ["Tecnologia", "Nível", "Obrigatória?"],
                        "level_options": ["Básico", "Intermediário", "Avançado", "Expert"],
                        "suggestions": TECHNOLOGY_SUGGESTIONS["frameworks"],
                        "autocomplete": True,
                        "filter_by_language": True,
                    },
                ],
            },
            {
                "title": "BANCOS DE DADOS",
                "fields": [
                    {
                        "name": "databases",
                        "type": "tech_table",
                        "columns": ["Tecnologia", "Nível", "Obrigatória?"],
                        "level_options": ["Básico", "Intermediário", "Avançado", "Expert"],
                        "suggestions": TECHNOLOGY_SUGGESTIONS["databases"],
                        "autocomplete": True,
                    },
                ],
            },
            {
                "title": "CLOUD E DEVOPS",
                "fields": [
                    {
                        "name": "cloud_devops",
                        "type": "tech_table",
                        "columns": ["Tecnologia", "Nível", "Obrigatória?"],
                        "level_options": ["Básico", "Intermediário", "Avançado", "Expert"],
                        "suggestions": TECHNOLOGY_SUGGESTIONS["cloud_devops"],
                        "autocomplete": True,
                    },
                ],
            },
            {
                "title": "FERRAMENTAS",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "tools",
                        "type": "tech_table",
                        "columns": ["Ferramenta", "Nível", "Obrigatória?"],
                        "level_options": ["Básico", "Intermediário", "Avançado", "Expert"],
                        "suggestions": TECHNOLOGY_SUGGESTIONS["tools"],
                        "autocomplete": True,
                    },
                ],
            },
            {
                "title": "CERTIFICAÇÕES DESEJÁVEIS",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "certifications",
                        "type": "tag_input",
                        "placeholder": "AWS Solutions Architect, Kubernetes CKA, etc.",
                        "suggestions": [
                            "AWS Solutions Architect",
                            "AWS Developer Associate",
                            "Azure Administrator",
                            "GCP Professional Cloud Architect",
                            "Kubernetes CKA",
                            "Kubernetes CKAD",
                            "Docker DCA",
                            "Terraform Associate",
                            "Scrum Master (PSM)",
                            "Product Owner (PSPO)",
                            "PMP",
                            "ITIL Foundation",
                        ],
                    },
                ],
            },
        ],
        "submit_button": "Concluído",
    },
    
    SidePanelType.BEHAVIORAL_COMPETENCIES.value: {
        "title": "Competências Comportamentais",
        "icon": "🧠",
        "competency_descriptions": COMPETENCY_DESCRIPTIONS,
        "sections": [
            {
                "title": "COMPETÊNCIAS",
                "description": "Ajuste o nível de importância de cada competência (1-5). Clique no ícone de info para ver detalhes.",
                "fields": [
                    {
                        "name": "competencies",
                        "type": "competency_slider",
                        "items": [
                            {
                                "name": key,
                                "label": value["label"],
                                "description": value["description"],
                                "behaviors": value["behaviors"],
                                "interview_questions": value["interview_questions"],
                            }
                            for key, value in COMPETENCY_DESCRIPTIONS.items()
                        ],
                        "scale": {
                            "min": 1,
                            "max": 5,
                            "labels": ["Baixo", "Médio-Baixo", "Médio", "Médio-Alto", "Alto"],
                            "colors": ["#94a3b8", "#60a5fa", "#34d399", "#fbbf24", "#f87171"],
                        },
                        "show_description_tooltip": True,
                        "allow_not_applicable": True,
                    },
                ],
            },
            {
                "title": "COMPETÊNCIAS CRÍTICAS",
                "description": "Selecione até 3 competências que são absolutamente essenciais para o sucesso na função",
                "fields": [
                    {
                        "name": "critical_competencies",
                        "type": "multi_select",
                        "max_selections": 3,
                        "options": [
                            {"value": key, "label": value["label"]}
                            for key, value in COMPETENCY_DESCRIPTIONS.items()
                        ],
                    },
                ],
            },
            {
                "title": "CULTURA E FIT",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "culture_notes",
                        "label": "Notas sobre Cultura",
                        "type": "textarea",
                        "placeholder": "Aspectos importantes da cultura da equipe/empresa que devem ser considerados...",
                    },
                ],
            },
        ],
        "submit_button": "Concluído",
    },
    
    SidePanelType.LANGUAGES.value: {
        "title": "Idiomas",
        "icon": "🌍",
        "languages_catalog": LANGUAGES_CATALOG,
        "levels_catalog": LANGUAGE_LEVELS,
        "sections": [
            {
                "title": "IDIOMAS NECESSÁRIOS",
                "description": "Adicione os idiomas requeridos para a posição e defina o nível mínimo necessário",
                "fields": [
                    {
                        "name": "languages",
                        "type": "language_table",
                        "columns": ["Idioma", "Nível Mínimo", "Obrigatório?", "Uso Principal"],
                        "language_options": LANGUAGES_CATALOG,
                        "level_options": LANGUAGE_LEVELS,
                        "usage_options": [
                            "Comunicação com clientes",
                            "Documentação técnica",
                            "Reuniões internas",
                            "Apresentações",
                            "Viagens internacionais",
                            "Suporte a usuários",
                        ],
                        "default_languages": [
                            {"code": "pt-BR", "level": "native", "required": True},
                        ],
                        "show_cefr": True,
                    },
                ],
            },
            {
                "title": "IDIOMAS DESEJÁVEIS (DIFERENCIAL)",
                "collapsible": True,
                "default_collapsed": False,
                "fields": [
                    {
                        "name": "nice_to_have_languages",
                        "type": "language_table",
                        "columns": ["Idioma", "Nível Mínimo"],
                        "language_options": LANGUAGES_CATALOG,
                        "level_options": LANGUAGE_LEVELS,
                        "is_required_column": False,
                    },
                ],
            },
            {
                "title": "OBSERVAÇÕES",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "language_notes",
                        "label": "Notas adicionais",
                        "type": "textarea",
                        "placeholder": "Ex: Inglês para reuniões semanais com time global, Espanhol para expansão LATAM...",
                    },
                ],
            },
        ],
        "submit_button": "Concluído",
    },
    
    SidePanelType.WSI_QUESTIONS.value: {
        "title": "Perguntas WSI",
        "icon": "📝",
        "question_templates": WSI_QUESTION_TEMPLATES,
        "sections": [
            {
                "title": "TEMPLATES POR ÁREA",
                "description": "Selecione templates prontos ou crie perguntas personalizadas",
                "fields": [
                    {
                        "name": "template_area",
                        "label": "Área de Atuação",
                        "type": "select",
                        "options": [
                            {"value": key, "label": value["area"]}
                            for key, value in WSI_QUESTION_TEMPLATES.items()
                        ],
                        "placeholder": "Selecione para ver templates",
                        "on_change": "load_templates",
                    },
                    {
                        "name": "suggested_templates",
                        "type": "template_selector",
                        "templates_source": "template_area",
                        "multi_select": True,
                        "show_preview": True,
                    },
                ],
            },
            {
                "title": "PERGUNTAS DE WORK SAMPLE INTERVIEW",
                "description": "Defina as perguntas que simulam situações reais do trabalho (recomendado: 3-5 perguntas)",
                "fields": [
                    {
                        "name": "questions",
                        "type": "wsi_question_list",
                        "min_items": 1,
                        "max_items": 8,
                        "recommended_items": 5,
                        "item_fields": [
                            {
                                "name": "question",
                                "label": "Pergunta",
                                "type": "textarea",
                                "required": True,
                                "placeholder": "Descreva uma situação real de trabalho...",
                                "max_length": 1000,
                            },
                            {
                                "name": "context",
                                "label": "Contexto (opcional)",
                                "type": "textarea",
                                "placeholder": "Informações adicionais para o candidato...",
                                "max_length": 500,
                                "collapsible": True,
                            },
                            {
                                "name": "bloom_level",
                                "label": "Nível Bloom",
                                "type": "select",
                                "options": ["Lembrar", "Entender", "Aplicar", "Analisar", "Avaliar", "Criar"],
                                "tooltip": "Nível cognitivo esperado na resposta",
                                "default": "Aplicar",
                            },
                            {
                                "name": "dreyfus_level",
                                "label": "Nível Dreyfus",
                                "type": "select",
                                "options": ["Novato", "Iniciante Avançado", "Competente", "Proficiente", "Expert"],
                                "tooltip": "Nível de expertise esperado",
                                "default": "Competente",
                            },
                            {
                                "name": "competency",
                                "label": "Competência Avaliada",
                                "type": "competency_select",
                                "options": list(COMPETENCY_DESCRIPTIONS.keys()),
                                "multi_select": True,
                                "max_selections": 3,
                            },
                            {
                                "name": "time_estimate",
                                "label": "Tempo Estimado",
                                "type": "select",
                                "options": ["5 min", "8 min", "10 min", "15 min", "20 min"],
                                "default": "10 min",
                            },
                            {
                                "name": "expected_answer",
                                "label": "Resposta Esperada (opcional)",
                                "type": "textarea",
                                "placeholder": "Pontos-chave que uma boa resposta deve abordar...",
                                "collapsible": True,
                            },
                            {
                                "name": "scoring_rubric",
                                "label": "Rubrica de Avaliação",
                                "type": "scoring_rubric",
                                "levels": [
                                    {"score": 1, "label": "Insuficiente", "description": ""},
                                    {"score": 2, "label": "Abaixo do Esperado", "description": ""},
                                    {"score": 3, "label": "Atende", "description": ""},
                                    {"score": 4, "label": "Acima do Esperado", "description": ""},
                                    {"score": 5, "label": "Excepcional", "description": ""},
                                ],
                                "collapsible": True,
                            },
                        ],
                        "reorderable": True,
                        "duplicate_action": True,
                    },
                ],
            },
            {
                "title": "CONFIGURAÇÕES DA ENTREVISTA",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "total_duration",
                        "label": "Duração Total Estimada",
                        "type": "duration_display",
                        "calculated_from": "questions.time_estimate",
                    },
                    {
                        "name": "interview_format",
                        "label": "Formato",
                        "type": "select",
                        "options": ["Presencial", "Vídeo (síncrono)", "Vídeo (assíncrono)", "Misto"],
                        "default": "Vídeo (síncrono)",
                    },
                    {
                        "name": "evaluation_type",
                        "label": "Tipo de Avaliação",
                        "type": "select",
                        "options": ["Individual", "Painel (múltiplos avaliadores)", "Dupla"],
                        "default": "Individual",
                    },
                ],
            },
        ],
        "submit_button": "Concluído",
    },
    
    SidePanelType.INTERVIEW_SCHEDULING.value: {
        "title": "Agendar Entrevista",
        "icon": "📅",
        "calendar_config": CALENDAR_INTEGRATION_CONFIG,
        "sections": [
            {
                "title": "INTEGRAÇÃO COM CALENDÁRIO",
                "description": "Conecte seu calendário para ver disponibilidade automaticamente",
                "fields": [
                    {
                        "name": "calendar_provider",
                        "type": "calendar_provider_select",
                        "options": CALENDAR_INTEGRATION_CONFIG["providers"],
                        "show_sync_button": True,
                    },
                    {
                        "name": "sync_availability",
                        "type": "availability_grid",
                        "depends_on": {"calendar_provider": ["google", "outlook"]},
                        "show_conflicts": True,
                    },
                ],
            },
            {
                "title": "SELECIONE O HORÁRIO",
                "fields": [
                    {
                        "name": "date",
                        "label": "Data",
                        "type": "date_picker",
                        "required": True,
                        "min_date": "today",
                        "max_date": "+60 days",
                        "exclude_weekends": True,
                        "show_availability": True,
                    },
                    {
                        "name": "time",
                        "label": "Horário",
                        "type": "time_slots",
                        "required": True,
                        "slot_interval": 30,
                        "working_hours": CALENDAR_INTEGRATION_CONFIG["working_hours"],
                        "show_availability_indicator": True,
                    },
                    {
                        "name": "duration",
                        "label": "Duração",
                        "type": "select",
                        "options": CALENDAR_INTEGRATION_CONFIG["slot_durations"],
                        "default": 60,
                        "required": True,
                    },
                    {
                        "name": "buffer_after",
                        "label": "Intervalo após entrevista",
                        "type": "select",
                        "options": CALENDAR_INTEGRATION_CONFIG["buffer_options"],
                        "default": 15,
                    },
                ],
            },
            {
                "title": "TIPO DE ENTREVISTA",
                "fields": [
                    {
                        "name": "meeting_type",
                        "label": "Formato",
                        "type": "meeting_type_select",
                        "options": CALENDAR_INTEGRATION_CONFIG["meeting_types"],
                        "default": "teams",
                        "required": True,
                    },
                    {
                        "name": "location",
                        "label": "Endereço",
                        "type": "address",
                        "depends_on": {"meeting_type": "presencial"},
                        "required_when_visible": True,
                    },
                    {
                        "name": "meeting_link",
                        "label": "Link da Reunião",
                        "type": "url",
                        "depends_on": {"meeting_type": ["teams", "meet", "zoom"]},
                        "auto_generate": True,
                        "editable": True,
                    },
                    {
                        "name": "phone_number",
                        "label": "Telefone",
                        "type": "phone",
                        "depends_on": {"meeting_type": "phone"},
                        "required_when_visible": True,
                    },
                ],
            },
            {
                "title": "PARTICIPANTES",
                "fields": [
                    {
                        "name": "interviewers",
                        "label": "Entrevistadores",
                        "type": "user_multi_select",
                        "required": True,
                        "min_selections": 1,
                        "show_availability": True,
                        "source": "team_members",
                    },
                    {
                        "name": "optional_attendees",
                        "label": "Participantes Opcionais",
                        "type": "user_multi_select",
                        "source": "team_members",
                    },
                ],
            },
            {
                "title": "LEMBRETES",
                "collapsible": True,
                "default_collapsed": False,
                "fields": [
                    {
                        "name": "candidate_reminder",
                        "label": "Lembrete para Candidato",
                        "type": "multi_select",
                        "options": CALENDAR_INTEGRATION_CONFIG["reminder_options"],
                        "default": [60, 1440],
                    },
                    {
                        "name": "interviewer_reminder",
                        "label": "Lembrete para Entrevistadores",
                        "type": "multi_select",
                        "options": CALENDAR_INTEGRATION_CONFIG["reminder_options"],
                        "default": [15, 60],
                    },
                ],
            },
            {
                "title": "OBSERVAÇÕES",
                "collapsible": True,
                "default_collapsed": True,
                "fields": [
                    {
                        "name": "notes_for_candidate",
                        "label": "Instruções para o Candidato",
                        "type": "textarea",
                        "placeholder": "Informações importantes para o candidato (documentos, preparação, etc.)",
                        "max_length": 500,
                    },
                    {
                        "name": "internal_notes",
                        "label": "Notas Internas",
                        "type": "textarea",
                        "placeholder": "Notas para a equipe de entrevistadores",
                        "max_length": 500,
                    },
                ],
            },
        ],
        "submit_button": "Agendar",
        "cancel_button": "Cancelar",
        "actions": [
            {"type": "primary", "label": "Agendar", "action": "schedule"},
            {"type": "secondary", "label": "Sugerir Horários", "action": "suggest_slots"},
        ],
    },
    
    SidePanelType.CALIBRATION_FEEDBACK.value: {
        "title": "Calibração de Busca",
        "icon": "🎯",
        "sections": [
            {
                "title": "AMOSTRA DE CANDIDATOS",
                "description": "Avalie estes perfis para calibrar a busca. Seu feedback ajuda a refinar os resultados.",
                "fields": [
                    {
                        "name": "samples",
                        "type": "calibration_cards",
                        "actions": [
                            {"value": "approve", "label": "✓ Aprovar", "color": "green"},
                            {"value": "reject", "label": "✗ Reprovar", "color": "red"},
                            {"value": "maybe", "label": "? Talvez", "color": "yellow"},
                        ],
                        "require_feedback_on_reject": True,
                        "show_match_score": True,
                        "show_key_highlights": True,
                    },
                ],
            },
            {
                "title": "AJUSTE DE CRITÉRIOS",
                "description": "Baseado no seu feedback, sugiro os seguintes ajustes:",
                "fields": [
                    {
                        "name": "suggested_adjustments",
                        "type": "adjustment_suggestions",
                        "editable": True,
                    },
                ],
            },
            {
                "title": "FEEDBACK GERAL",
                "fields": [
                    {
                        "name": "missing_criteria",
                        "label": "O que está faltando nos perfis?",
                        "type": "textarea",
                        "placeholder": "Descreva critérios que não estão sendo considerados...",
                    },
                    {
                        "name": "too_strict_criteria",
                        "label": "Quais critérios estão muito restritivos?",
                        "type": "textarea",
                        "placeholder": "Critérios que podem ser flexibilizados...",
                    },
                ],
            },
        ],
        "submit_button": "Concluir Calibração",
    },
    
    SidePanelType.ATS_FIELD_MAPPING.value: {
        "title": "Mapeamento de Campos ATS",
        "icon": "🔗",
        "sections": [
            {
                "title": "CAMPOS DO CANDIDATO",
                "description": "Mapeie os campos do sistema externo para os campos internos",
                "fields": [
                    {
                        "name": "candidate_mapping",
                        "type": "field_mapping_table",
                        "source_fields": ["Nome", "Email", "Telefone", "LinkedIn", "CV", "Cidade", "Estado"],
                        "target_fields": ["full_name", "email", "phone", "linkedin_url", "cv_url", "city", "state"],
                        "show_preview": True,
                    },
                ],
            },
            {
                "title": "CAMPOS DA VAGA",
                "fields": [
                    {
                        "name": "job_mapping",
                        "type": "field_mapping_table",
                        "source_fields": ["Título", "Departamento", "Salário", "Localização", "Status"],
                        "target_fields": ["title", "department", "salary_range", "location", "status"],
                    },
                ],
            },
            {
                "title": "ESTÁGIOS DO PIPELINE",
                "fields": [
                    {
                        "name": "stage_mapping",
                        "type": "stage_mapping",
                        "source_stages": [],
                        "target_stages": ["Aplicado", "Triagem", "Entrevista", "Proposta", "Contratado", "Recusado"],
                    },
                ],
            },
        ],
        "submit_button": "Salvar Mapeamento",
    },
    
    SidePanelType.EMAIL_COMPOSER.value: {
        "title": "Compor Email",
        "icon": "📧",
        "sections": [
            {
                "title": "DESTINATÁRIOS",
                "fields": [
                    {"name": "to", "label": "Para", "type": "email_multi_input", "required": True},
                    {"name": "cc", "label": "Cc", "type": "email_multi_input"},
                    {"name": "bcc", "label": "Cco", "type": "email_multi_input"},
                ],
            },
            {
                "title": "MENSAGEM",
                "fields": [
                    {"name": "subject", "label": "Assunto", "type": "text", "required": True},
                    {"name": "body", "label": "Corpo do Email", "type": "rich_text", "required": True},
                ],
            },
            {
                "title": "TEMPLATE",
                "collapsible": True,
                "fields": [
                    {"name": "template_id", "label": "Usar Template", "type": "template_select"},
                ],
            },
            {
                "title": "AGENDAMENTO",
                "collapsible": True,
                "fields": [
                    {"name": "send_later", "label": "Agendar Envio", "type": "toggle"},
                    {"name": "send_at", "label": "Data e Hora", "type": "datetime", "depends_on": {"send_later": True}},
                ],
            },
        ],
        "submit_button": "Enviar",
        "secondary_button": {"label": "Salvar Rascunho", "action": "save_draft"},
    },
    
    SidePanelType.WHATSAPP_COMPOSER.value: {
        "title": "Compor WhatsApp",
        "icon": "💬",
        "sections": [
            {
                "title": "DESTINATÁRIO",
                "fields": [
                    {"name": "phone", "label": "Telefone", "type": "phone", "required": True},
                    {"name": "candidate_name", "label": "Nome do Candidato", "type": "text", "readonly": True},
                ],
            },
            {
                "title": "MENSAGEM",
                "fields": [
                    {
                        "name": "message",
                        "label": "Mensagem",
                        "type": "textarea",
                        "required": True,
                        "max_length": 4096,
                        "show_char_count": True,
                        "variables": ["{{nome}}", "{{vaga}}", "{{empresa}}", "{{data}}"],
                    },
                ],
            },
            {
                "title": "TEMPLATE",
                "fields": [
                    {"name": "template_id", "label": "Usar Template", "type": "whatsapp_template_select"},
                ],
            },
        ],
        "submit_button": "Enviar",
    },
}


CHAT_CARD_SCHEMAS: Dict[str, Dict[str, Any]] = {
    ChatCardType.CANDIDATE_SUMMARY.value: {
        "title": "Perfil do Candidato",
        "icon": "👤",
        "layout": "horizontal",
        "fields": [
            {
                "name": "avatar",
                "type": "avatar",
                "size": "large",
                "fallback": "initials",
            },
            {
                "name": "header",
                "type": "header_group",
                "fields": [
                    {"name": "name", "type": "text", "style": "title"},
                    {"name": "current_role", "type": "text", "style": "subtitle"},
                    {"name": "current_company", "type": "text", "style": "muted"},
                ],
            },
            {
                "name": "quick_info",
                "type": "info_grid",
                "columns": 2,
                "fields": [
                    {"name": "location", "label": "📍 Localização", "type": "text"},
                    {"name": "experience_years", "label": "💼 Experiência", "type": "text", "suffix": "anos"},
                    {"name": "salary_expectation", "label": "💰 Pretensão", "type": "currency"},
                    {"name": "availability", "label": "🗓️ Disponibilidade", "type": "text"},
                ],
            },
            {
                "name": "match_score",
                "type": "score_badge",
                "color_scale": {"0-50": "red", "51-70": "yellow", "71-85": "green", "86-100": "blue"},
                "show_label": True,
            },
            {
                "name": "key_skills",
                "type": "tag_list",
                "max_visible": 5,
                "expandable": True,
            },
            {
                "name": "highlights",
                "type": "bullet_list",
                "icon": "✓",
                "max_visible": 3,
            },
            {
                "name": "concerns",
                "type": "bullet_list",
                "icon": "⚠️",
                "style": "warning",
                "collapsible": True,
            },
        ],
        "actions": [
            {"label": "Ver Perfil Completo", "action": "view_profile", "style": "link"},
            {"label": "Adicionar ao Pipeline", "action": "add_to_pipeline", "style": "primary"},
            {"label": "Rejeitar", "action": "reject", "style": "secondary"},
        ],
    },
    
    ChatCardType.JOB_SUMMARY.value: {
        "title": "Resumo da Vaga",
        "icon": "💼",
        "layout": "vertical",
        "fields": [
            {
                "name": "header",
                "type": "header_group",
                "fields": [
                    {"name": "title", "type": "text", "style": "title"},
                    {"name": "department", "type": "badge", "style": "info"},
                    {"name": "seniority", "type": "badge", "style": "default"},
                ],
            },
            {
                "name": "basic_info",
                "type": "info_grid",
                "columns": 2,
                "fields": [
                    {"name": "work_model", "label": "🏢 Modelo", "type": "text"},
                    {"name": "location", "label": "📍 Local", "type": "text"},
                    {"name": "salary_range", "label": "💰 Faixa Salarial", "type": "currency_range"},
                    {"name": "urgency", "label": "⏰ Urgência", "type": "badge"},
                ],
            },
            {
                "name": "requirements_summary",
                "type": "section",
                "title": "Requisitos Principais",
                "fields": [
                    {
                        "name": "required_skills",
                        "type": "skill_list",
                        "show_level": True,
                        "filter": "required",
                        "max_visible": 6,
                    },
                ],
            },
            {
                "name": "benefits_preview",
                "type": "icon_list",
                "title": "Benefícios",
                "max_visible": 6,
                "expandable": True,
            },
            {
                "name": "competencies_chart",
                "type": "radar_chart",
                "title": "Competências Comportamentais",
                "collapsible": True,
            },
            {
                "name": "wsi_questions_count",
                "type": "info_badge",
                "label": "Perguntas WSI",
                "icon": "📝",
            },
        ],
        "actions": [
            {"label": "Editar Vaga", "action": "edit_job", "style": "secondary"},
            {"label": "Publicar", "action": "publish", "style": "primary"},
            {"label": "Iniciar Sourcing", "action": "start_sourcing", "style": "primary"},
        ],
        "footer": {
            "type": "status_bar",
            "fields": [
                {"name": "created_at", "label": "Criada em", "type": "date"},
                {"name": "status", "type": "status_badge"},
            ],
        },
    },
    
    ChatCardType.WSI_SCORE.value: {
        "title": "Score WSI",
        "icon": "🎯",
        "layout": "vertical",
        "fields": [
            {
                "name": "overall_score",
                "type": "score_display",
                "size": "large",
                "max_score": 100,
                "color_scale": {
                    "0-40": {"color": "red", "label": "Baixo"},
                    "41-60": {"color": "yellow", "label": "Médio"},
                    "61-80": {"color": "green", "label": "Bom"},
                    "81-100": {"color": "blue", "label": "Excelente"},
                },
                "show_trend": True,
            },
            {
                "name": "dimension_scores",
                "type": "breakdown_bars",
                "title": "Breakdown por Dimensão",
                "dimensions": [
                    {"key": "technical", "label": "Técnico", "weight": 0.4},
                    {"key": "behavioral", "label": "Comportamental", "weight": 0.3},
                    {"key": "cultural_fit", "label": "Fit Cultural", "weight": 0.2},
                    {"key": "potential", "label": "Potencial", "weight": 0.1},
                ],
                "show_weights": True,
            },
            {
                "name": "competency_scores",
                "type": "competency_heatmap",
                "title": "Scores por Competência",
                "collapsible": True,
                "default_collapsed": False,
            },
            {
                "name": "strengths",
                "type": "highlight_list",
                "title": "🌟 Pontos Fortes",
                "icon": "✓",
                "style": "positive",
                "max_visible": 3,
            },
            {
                "name": "development_areas",
                "type": "highlight_list",
                "title": "📈 Áreas de Desenvolvimento",
                "icon": "→",
                "style": "neutral",
                "max_visible": 3,
            },
            {
                "name": "risks",
                "type": "highlight_list",
                "title": "⚠️ Riscos Identificados",
                "icon": "!",
                "style": "warning",
                "collapsible": True,
            },
            {
                "name": "recommendation",
                "type": "recommendation_badge",
                "options": [
                    {"value": "strong_hire", "label": "Forte Recomendação", "color": "green", "icon": "🎯"},
                    {"value": "hire", "label": "Recomendado", "color": "blue", "icon": "✓"},
                    {"value": "maybe", "label": "Considerar", "color": "yellow", "icon": "?"},
                    {"value": "no_hire", "label": "Não Recomendado", "color": "red", "icon": "✗"},
                ],
            },
            {
                "name": "parecer",
                "type": "expandable_text",
                "title": "Parecer Detalhado",
                "max_preview_length": 200,
            },
        ],
        "actions": [
            {"label": "Ver Detalhes Completos", "action": "view_full_report", "style": "link"},
            {"label": "Aprovar", "action": "approve", "style": "primary"},
            {"label": "Rejeitar", "action": "reject", "style": "danger"},
            {"label": "Agendar Entrevista", "action": "schedule_interview", "style": "secondary"},
        ],
    },
    
    ChatCardType.EMAIL_PREVIEW.value: {
        "title": "Preview do Email",
        "icon": "📧",
        "layout": "vertical",
        "fields": [
            {
                "name": "header",
                "type": "email_header",
                "fields": [
                    {"name": "to", "label": "Para", "type": "email_list"},
                    {"name": "subject", "label": "Assunto", "type": "text", "style": "bold"},
                ],
            },
            {
                "name": "body",
                "type": "email_body",
                "format": "html",
                "max_height": 300,
                "scrollable": True,
            },
        ],
        "actions": [
            {"label": "Editar", "action": "edit_email", "style": "secondary"},
            {"label": "Enviar", "action": "send_email", "style": "primary"},
        ],
    },
    
    ChatCardType.WHATSAPP_PREVIEW.value: {
        "title": "Preview WhatsApp",
        "icon": "💬",
        "layout": "vertical",
        "style": "whatsapp_bubble",
        "fields": [
            {
                "name": "recipient",
                "type": "recipient_info",
                "fields": [
                    {"name": "name", "type": "text"},
                    {"name": "phone", "type": "phone"},
                ],
            },
            {
                "name": "message",
                "type": "whatsapp_message",
                "show_timestamp": True,
            },
        ],
        "actions": [
            {"label": "Editar", "action": "edit_message", "style": "secondary"},
            {"label": "Enviar", "action": "send_whatsapp", "style": "primary", "icon": "💬"},
        ],
    },
    
    ChatCardType.DASHBOARD_METRICS.value: {
        "title": "Métricas",
        "icon": "📊",
        "layout": "grid",
        "columns": 2,
        "fields": [
            {
                "name": "metrics",
                "type": "metric_cards",
                "items": [
                    {"key": "total_candidates", "label": "Candidatos", "icon": "👥", "format": "number"},
                    {"key": "interviews_scheduled", "label": "Entrevistas", "icon": "📅", "format": "number"},
                    {"key": "avg_time_to_hire", "label": "Tempo Médio", "icon": "⏱️", "format": "days"},
                    {"key": "conversion_rate", "label": "Conversão", "icon": "📈", "format": "percentage"},
                ],
                "show_trend": True,
                "compare_period": "previous_month",
            },
        ],
        "actions": [
            {"label": "Ver Dashboard Completo", "action": "open_dashboard", "style": "link"},
            {"label": "Exportar", "action": "export_metrics", "style": "secondary"},
        ],
    },
    
    ChatCardType.SYNC_STATUS.value: {
        "title": "Status de Sincronização",
        "icon": "🔄",
        "layout": "vertical",
        "fields": [
            {
                "name": "status",
                "type": "sync_status_indicator",
                "states": [
                    {"value": "synced", "label": "Sincronizado", "color": "green", "icon": "✓"},
                    {"value": "syncing", "label": "Sincronizando...", "color": "blue", "icon": "🔄"},
                    {"value": "error", "label": "Erro", "color": "red", "icon": "✗"},
                    {"value": "pending", "label": "Pendente", "color": "yellow", "icon": "⏳"},
                ],
            },
            {
                "name": "details",
                "type": "sync_details",
                "fields": [
                    {"name": "last_sync", "label": "Última Sincronização", "type": "datetime"},
                    {"name": "records_synced", "label": "Registros Sincronizados", "type": "number"},
                    {"name": "errors_count", "label": "Erros", "type": "number", "style": "warning_if_nonzero"},
                ],
            },
            {
                "name": "error_list",
                "type": "error_list",
                "collapsible": True,
                "visible_if": {"errors_count": ">0"},
            },
        ],
        "actions": [
            {"label": "Sincronizar Agora", "action": "sync_now", "style": "primary"},
            {"label": "Ver Logs", "action": "view_logs", "style": "link"},
        ],
    },
    
    ChatCardType.INTERVIEW_CONFIRMATION.value: {
        "title": "Entrevista Agendada",
        "icon": "✅",
        "layout": "vertical",
        "style": "success",
        "fields": [
            {
                "name": "confirmation_header",
                "type": "confirmation_banner",
                "message": "Entrevista agendada com sucesso!",
                "icon": "✅",
            },
            {
                "name": "details",
                "type": "info_grid",
                "columns": 2,
                "fields": [
                    {"name": "candidate_name", "label": "👤 Candidato", "type": "text"},
                    {"name": "job_title", "label": "💼 Vaga", "type": "text"},
                    {"name": "date", "label": "📅 Data", "type": "date"},
                    {"name": "time", "label": "🕐 Horário", "type": "time"},
                    {"name": "duration", "label": "⏱️ Duração", "type": "text"},
                    {"name": "type", "label": "📍 Tipo", "type": "text"},
                ],
            },
            {
                "name": "interviewers",
                "type": "user_list",
                "title": "Entrevistadores",
                "show_avatar": True,
            },
            {
                "name": "meeting_link",
                "type": "link_button",
                "visible_if": {"type": ["teams", "meet", "zoom"]},
            },
        ],
        "actions": [
            {"label": "Adicionar ao Calendário", "action": "add_to_calendar", "style": "secondary"},
            {"label": "Reagendar", "action": "reschedule", "style": "link"},
            {"label": "Cancelar", "action": "cancel", "style": "danger_link"},
        ],
    },
    
    ChatCardType.MARKET_ANALYSIS.value: {
        "title": "Análise de Mercado",
        "icon": "📈",
        "layout": "vertical",
        "fields": [
            {
                "name": "salary_comparison",
                "type": "salary_range_chart",
                "title": "Comparativo Salarial",
                "show_percentiles": [25, 50, 75, 90],
                "highlight_position": True,
            },
            {
                "name": "market_insights",
                "type": "insight_list",
                "title": "Insights de Mercado",
                "items": [
                    {"key": "supply_demand", "icon": "📊"},
                    {"key": "salary_trend", "icon": "📈"},
                    {"key": "competition", "icon": "🏢"},
                ],
            },
            {
                "name": "recommendations",
                "type": "recommendation_list",
                "title": "Recomendações",
            },
        ],
        "actions": [
            {"label": "Ver Relatório Completo", "action": "view_full_report", "style": "link"},
        ],
    },
    
    ChatCardType.PROGRESS_TRACKER.value: {
        "title": "Progresso do Pipeline",
        "icon": "📊",
        "layout": "vertical",
        "fields": [
            {
                "name": "pipeline_stages",
                "type": "pipeline_funnel",
                "stages": [
                    {"key": "applied", "label": "Aplicados", "color": "#6366f1"},
                    {"key": "screening", "label": "Triagem", "color": "#8b5cf6"},
                    {"key": "interview", "label": "Entrevista", "color": "#a855f7"},
                    {"key": "offer", "label": "Proposta", "color": "#d946ef"},
                    {"key": "hired", "label": "Contratado", "color": "#22c55e"},
                ],
                "show_conversion_rates": True,
            },
            {
                "name": "key_metrics",
                "type": "metric_row",
                "metrics": [
                    {"key": "total", "label": "Total"},
                    {"key": "this_week", "label": "Esta Semana"},
                    {"key": "avg_days", "label": "Dias Médio"},
                ],
            },
        ],
        "actions": [
            {"label": "Ver Pipeline Completo", "action": "view_pipeline", "style": "link"},
        ],
    },
}


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
    
    component_type = action_def["component_type"]
    component_subtype = action_def["component_subtype"]
    
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
    for field in common_fields:
        if field in context and field not in extracted:
            extracted[field] = context[field]
    
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
