"""
Organization Catalog Service - Comprehensive Brazilian Organizational Catalog.

Provides a complete catalog of areas, roles, seniority levels, and competencies
typical of Brazilian medium and large companies.

Features:
- 20 organizational areas/departments
- 12 seniority levels with descriptions
- 10-15 roles per area
- 30-50 technical skills per area
- 50 universal behavioral competencies
- Area detection from text
- Role-to-skills mapping
- Fuzzy search capabilities
"""
import logging
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Area:
    """Organizational area/department definition."""
    id: str
    nome: str
    descricao: str
    palavras_chave: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeniorityLevel:
    """Seniority level definition."""
    id: str
    nome: str
    descricao: str
    ordem: int
    anos_experiencia_min: int
    anos_experiencia_max: int | None
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Role:
    """Job role/position definition."""
    id: str
    nome: str
    area_id: str
    niveis_aplicaveis: list[str]
    descricao: str
    competencias_tecnicas: list[str]
    competencias_comportamentais: list[str]
    variantes_nome: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalSkill:
    """Technical skill/competency definition."""
    id: str
    nome: str
    areas: list[str]
    nivel_minimo: str
    descricao: str
    categoria: str
    palavras_chave: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BehavioralSkill:
    """Behavioral competency definition."""
    id: str
    nome: str
    descricao: str
    categoria: str
    subcategorias: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# AREAS CATALOG (20 areas)
# =============================================================================

AREAS_CATALOG: dict[str, Area] = {
    "tecnologia": Area(
        id="tecnologia",
        nome="Tecnologia da Informação",
        descricao="Área responsável por desenvolvimento de software, infraestrutura de TI, segurança da informação e suporte técnico",
        palavras_chave=["ti", "tecnologia", "dev", "developer", "desenvolvedor", "programador", "software", "sistemas", "tech", "it", "desenvolvimento", "engenharia de software", "devops", "sre", "dados", "data", "cloud", "infraestrutura", "suporte", "helpdesk"]
    ),
    "financeiro": Area(
        id="financeiro",
        nome="Financeiro",
        descricao="Área responsável por gestão financeira, FP&A, tesouraria, controladoria e análise de investimentos",
        palavras_chave=["financeiro", "finanças", "finance", "fp&a", "fpa", "tesouraria", "treasury", "controladoria", "controller", "financas", "analista financeiro", "financial analyst", "planejamento financeiro"]
    ),
    "contabil": Area(
        id="contabil",
        nome="Contabilidade",
        descricao="Área responsável por escrituração contábil, fechamento, demonstrações financeiras e conformidade contábil",
        palavras_chave=["contábil", "contabilidade", "contador", "accounting", "accountant", "contabil", "escrituração", "fechamento contábil", "demonstrações financeiras", "balanço", "dre", "ifrs", "cpc"]
    ),
    "fiscal": Area(
        id="fiscal",
        nome="Fiscal/Tributário",
        descricao="Área responsável por apuração de impostos, obrigações acessórias, planejamento tributário e compliance fiscal",
        palavras_chave=["fiscal", "tributário", "tax", "impostos", "tributos", "tributario", "sped", "nfe", "icms", "pis", "cofins", "irpj", "csll", "iss", "obrigações acessórias", "planejamento tributário"]
    ),
    "rh": Area(
        id="rh",
        nome="Recursos Humanos",
        descricao="Área responsável por recrutamento, desenvolvimento organizacional, gestão de talentos e cultura organizacional",
        palavras_chave=["rh", "recursos humanos", "hr", "human resources", "gente", "pessoas", "talent", "talentos", "recrutamento", "r&s", "treinamento", "t&d", "desenvolvimento", "cargos e salários", "remuneração", "clima", "cultura", "engajamento"]
    ),
    "dp": Area(
        id="dp",
        nome="Departamento Pessoal",
        descricao="Área responsável por folha de pagamento, admissões, demissões, benefícios e obrigações trabalhistas",
        palavras_chave=["dp", "departamento pessoal", "folha", "payroll", "admissão", "demissão", "benefícios", "esocial", "e-social", "clt", "fgts", "inss", "férias", "rescisão", "ponto", "jornada"]
    ),
    "comercial": Area(
        id="comercial",
        nome="Comercial/Vendas",
        descricao="Área responsável por vendas, gestão de clientes, negociação e desenvolvimento de negócios",
        palavras_chave=["comercial", "vendas", "sales", "vendedor", "executivo de vendas", "account executive", "ae", "sdr", "bdr", "hunter", "farmer", "key account", "kam", "inside sales", "outside sales", "representante comercial"]
    ),
    "marketing": Area(
        id="marketing",
        nome="Marketing",
        descricao="Área responsável por estratégia de marca, marketing digital, comunicação e geração de demanda",
        palavras_chave=["marketing", "mkt", "branding", "marca", "digital", "growth", "performance", "conteúdo", "content", "social media", "mídia", "comunicação", "endomarketing", "trade marketing", "product marketing"]
    ),
    "operacoes": Area(
        id="operacoes",
        nome="Operações",
        descricao="Área responsável por gestão operacional, processos, eficiência e melhoria contínua",
        palavras_chave=["operações", "operations", "ops", "processos", "process", "eficiência", "melhoria contínua", "lean", "six sigma", "bpm", "gestão operacional"]
    ),
    "logistica": Area(
        id="logistica",
        nome="Logística/Supply Chain",
        descricao="Área responsável por gestão de cadeia de suprimentos, distribuição, armazenagem e transporte",
        palavras_chave=["logística", "logistics", "supply chain", "cadeia de suprimentos", "distribuição", "armazém", "warehouse", "wms", "transporte", "frete", "expedição", "recebimento", "estoque", "inventory", "s&op", "demand planning"]
    ),
    "compras": Area(
        id="compras",
        nome="Compras/Procurement",
        descricao="Área responsável por aquisição de materiais e serviços, gestão de fornecedores e negociação de contratos",
        palavras_chave=["compras", "procurement", "purchasing", "sourcing", "strategic sourcing", "fornecedores", "suppliers", "vendor management", "negociação", "cotação", "licitação"]
    ),
    "juridico": Area(
        id="juridico",
        nome="Jurídico",
        descricao="Área responsável por assessoria jurídica, contratos, contencioso e compliance legal",
        palavras_chave=["jurídico", "legal", "advogado", "lawyer", "direito", "contratos", "contencioso", "societário", "trabalhista", "tributário", "compliance", "lgpd", "regulatório", "m&a"]
    ),
    "compliance": Area(
        id="compliance",
        nome="Compliance/GRC",
        descricao="Área responsável por conformidade regulatória, gestão de riscos, controles internos e governança corporativa",
        palavras_chave=["compliance", "conformidade", "grc", "riscos", "risk", "controles internos", "auditoria", "audit", "sox", "governança", "governance", "anticorrupção", "due diligence", "kyc", "aml", "pld"]
    ),
    "administrativo": Area(
        id="administrativo",
        nome="Administrativo",
        descricao="Área responsável por serviços administrativos gerais, secretariado e apoio operacional",
        palavras_chave=["administrativo", "admin", "administrative", "secretaria", "secretariado", "recepção", "office", "escritório", "apoio administrativo", "assistente administrativo", "auxiliar administrativo"]
    ),
    "qualidade": Area(
        id="qualidade",
        nome="Qualidade",
        descricao="Área responsável por gestão da qualidade, garantia da qualidade, controle de qualidade e certificações",
        palavras_chave=["qualidade", "quality", "qa", "qc", "controle de qualidade", "garantia da qualidade", "iso", "sgi", "auditoria de qualidade", "inspeção", "metrologia", "calibração"]
    ),
    "engenharia": Area(
        id="engenharia",
        nome="Engenharia",
        descricao="Área responsável por projetos de engenharia, desenvolvimento de produtos e processos industriais",
        palavras_chave=["engenharia", "engineering", "engenheiro", "engineer", "projeto", "design", "cad", "mecânica", "elétrica", "civil", "automação", "manutenção", "pcm", "facilities engineering"]
    ),
    "producao": Area(
        id="producao",
        nome="Produção/Manufatura",
        descricao="Área responsável por gestão da produção, planejamento de produção e operações fabris",
        palavras_chave=["produção", "production", "manufatura", "manufacturing", "fábrica", "factory", "pcp", "planejamento de produção", "supervisor de produção", "operador", "linha de produção", "chão de fábrica"]
    ),
    "pd": Area(
        id="pd",
        nome="P&D/Inovação",
        descricao="Área responsável por pesquisa e desenvolvimento, inovação e novos produtos",
        palavras_chave=["p&d", "pd", "pesquisa", "research", "r&d", "desenvolvimento", "inovação", "innovation", "novos produtos", "npd", "laboratório", "lab", "cientista", "researcher"]
    ),
    "atendimento": Area(
        id="atendimento",
        nome="Atendimento ao Cliente/Customer Success",
        descricao="Área responsável por atendimento ao cliente, suporte, customer success e experiência do cliente",
        palavras_chave=["atendimento", "customer service", "suporte", "support", "customer success", "cs", "cx", "experiência do cliente", "sac", "call center", "contact center", "help desk", "service desk", "relacionamento"]
    ),
    "facilities": Area(
        id="facilities",
        nome="Facilities/Infraestrutura Predial",
        descricao="Área responsável por gestão de instalações, manutenção predial, segurança patrimonial e serviços gerais",
        palavras_chave=["facilities", "infraestrutura", "predial", "manutenção predial", "segurança patrimonial", "serviços gerais", "limpeza", "conservação", "portaria", "vigilância", "building management"]
    ),
}


# =============================================================================
# SENIORITY LEVELS (12 levels)
# =============================================================================

SENIORITY_LEVELS: dict[str, SeniorityLevel] = {
    "estagiario": SeniorityLevel(
        id="estagiario",
        nome="Estagiário",
        descricao="Estudante em formação, realizando estágio para desenvolvimento prático na área de atuação",
        ordem=1,
        anos_experiencia_min=0,
        anos_experiencia_max=0
    ),
    "trainee": SeniorityLevel(
        id="trainee",
        nome="Trainee",
        descricao="Recém-formado em programa estruturado de desenvolvimento acelerado de carreira",
        ordem=2,
        anos_experiencia_min=0,
        anos_experiencia_max=2
    ),
    "junior_i": SeniorityLevel(
        id="junior_i",
        nome="Júnior I",
        descricao="Profissional em início de carreira, executando atividades com supervisão direta",
        ordem=3,
        anos_experiencia_min=0,
        anos_experiencia_max=2
    ),
    "junior_ii": SeniorityLevel(
        id="junior_ii",
        nome="Júnior II",
        descricao="Profissional com conhecimento básico consolidado, executando atividades com supervisão moderada",
        ordem=4,
        anos_experiencia_min=1,
        anos_experiencia_max=3
    ),
    "pleno_i": SeniorityLevel(
        id="pleno_i",
        nome="Pleno I",
        descricao="Profissional com autonomia para executar atividades de média complexidade",
        ordem=5,
        anos_experiencia_min=2,
        anos_experiencia_max=4
    ),
    "pleno_ii": SeniorityLevel(
        id="pleno_ii",
        nome="Pleno II",
        descricao="Profissional experiente com autonomia para atividades complexas e mentoria de juniores",
        ordem=6,
        anos_experiencia_min=3,
        anos_experiencia_max=5
    ),
    "senior_i": SeniorityLevel(
        id="senior_i",
        nome="Sênior I",
        descricao="Profissional referência técnica, liderando projetos e orientando equipes",
        ordem=7,
        anos_experiencia_min=5,
        anos_experiencia_max=8
    ),
    "senior_ii": SeniorityLevel(
        id="senior_ii",
        nome="Sênior II",
        descricao="Especialista com visão estratégica, influenciando decisões técnicas e de negócio",
        ordem=8,
        anos_experiencia_min=7,
        anos_experiencia_max=10
    ),
    "especialista": SeniorityLevel(
        id="especialista",
        nome="Especialista",
        descricao="Expert reconhecido na área, referência técnica para toda a organização",
        ordem=9,
        anos_experiencia_min=8,
        anos_experiencia_max=None
    ),
    "coordenador": SeniorityLevel(
        id="coordenador",
        nome="Coordenador",
        descricao="Líder de equipe operacional, responsável por execução e desenvolvimento do time",
        ordem=10,
        anos_experiencia_min=5,
        anos_experiencia_max=None
    ),
    "gerente": SeniorityLevel(
        id="gerente",
        nome="Gerente",
        descricao="Gestor de área ou departamento, responsável por estratégia, orçamento e resultados",
        ordem=11,
        anos_experiencia_min=8,
        anos_experiencia_max=None
    ),
    "diretor": SeniorityLevel(
        id="diretor",
        nome="Diretor",
        descricao="Executivo responsável por diretoria ou unidade de negócio, reportando à alta gestão",
        ordem=12,
        anos_experiencia_min=12,
        anos_experiencia_max=None
    ),
    "vp": SeniorityLevel(
        id="vp",
        nome="VP/Vice-Presidente",
        descricao="Executivo sênior responsável por múltiplas áreas ou regiões, membro do comitê executivo",
        ordem=13,
        anos_experiencia_min=15,
        anos_experiencia_max=None
    ),
    "c_level": SeniorityLevel(
        id="c_level",
        nome="C-Level",
        descricao="Executivo do C-Suite (CEO, CFO, CTO, etc.), responsável pela estratégia global da empresa",
        ordem=14,
        anos_experiencia_min=15,
        anos_experiencia_max=None
    ),
}


# =============================================================================
# BEHAVIORAL COMPETENCIES (50 competencies)
# =============================================================================

BEHAVIORAL_SKILLS: dict[str, BehavioralSkill] = {
    "lideranca": BehavioralSkill(
        id="lideranca",
        nome="Liderança",
        descricao="Capacidade de inspirar, motivar e guiar pessoas para alcançar objetivos comuns",
        categoria="gestao",
        subcategorias=["Liderança Situacional", "Liderança Transformacional", "Liderança Servidora"]
    ),
    "comunicacao": BehavioralSkill(
        id="comunicacao",
        nome="Comunicação",
        descricao="Habilidade de transmitir informações de forma clara, assertiva e adaptada ao público",
        categoria="interpessoal",
        subcategorias=["Comunicação Verbal", "Comunicação Escrita", "Escuta Ativa"]
    ),
    "trabalho_equipe": BehavioralSkill(
        id="trabalho_equipe",
        nome="Trabalho em Equipe",
        descricao="Capacidade de colaborar efetivamente com outros para alcançar objetivos compartilhados",
        categoria="interpessoal",
        subcategorias=["Colaboração", "Cooperação", "Espírito de Equipe"]
    ),
    "resolucao_problemas": BehavioralSkill(
        id="resolucao_problemas",
        nome="Resolução de Problemas",
        descricao="Habilidade de identificar, analisar e solucionar problemas de forma eficaz",
        categoria="analitica",
        subcategorias=["Análise de Causa Raiz", "Problem Solving", "Troubleshooting"]
    ),
    "pensamento_critico": BehavioralSkill(
        id="pensamento_critico",
        nome="Pensamento Crítico",
        descricao="Capacidade de avaliar informações objetivamente e fazer julgamentos fundamentados",
        categoria="analitica",
        subcategorias=["Análise Crítica", "Questionamento", "Ceticismo Saudável"]
    ),
    "adaptabilidade": BehavioralSkill(
        id="adaptabilidade",
        nome="Adaptabilidade",
        descricao="Flexibilidade para se ajustar a mudanças e novos desafios de forma positiva",
        categoria="pessoal",
        subcategorias=["Flexibilidade", "Gestão de Mudanças", "Agilidade"]
    ),
    "proatividade": BehavioralSkill(
        id="proatividade",
        nome="Proatividade",
        descricao="Iniciativa para antecipar necessidades e agir antes de ser solicitado",
        categoria="pessoal",
        subcategorias=["Iniciativa", "Antecipação", "Autonomia"]
    ),
    "organizacao": BehavioralSkill(
        id="organizacao",
        nome="Organização",
        descricao="Capacidade de estruturar tarefas, informações e processos de forma eficiente",
        categoria="pessoal",
        subcategorias=["Planejamento", "Estruturação", "Metodologia"]
    ),
    "gestao_tempo": BehavioralSkill(
        id="gestao_tempo",
        nome="Gestão de Tempo",
        descricao="Habilidade de priorizar e gerenciar atividades para maximizar produtividade",
        categoria="pessoal",
        subcategorias=["Priorização", "Produtividade", "Cumprimento de Prazos"]
    ),
    "negociacao": BehavioralSkill(
        id="negociacao",
        nome="Negociação",
        descricao="Capacidade de conduzir negociações buscando acordos mutuamente benéficos",
        categoria="interpessoal",
        subcategorias=["Barganha", "Mediação", "Win-Win"]
    ),
    "influencia": BehavioralSkill(
        id="influencia",
        nome="Influência",
        descricao="Habilidade de persuadir e inspirar outros sem autoridade formal",
        categoria="interpessoal",
        subcategorias=["Persuasão", "Convencimento", "Advocacy"]
    ),
    "empatia": BehavioralSkill(
        id="empatia",
        nome="Empatia",
        descricao="Capacidade de compreender e se colocar no lugar do outro",
        categoria="interpessoal",
        subcategorias=["Compreensão", "Sensibilidade", "Conexão Emocional"]
    ),
    "resiliencia": BehavioralSkill(
        id="resiliencia",
        nome="Resiliência",
        descricao="Capacidade de superar adversidades e manter desempenho sob pressão",
        categoria="pessoal",
        subcategorias=["Persistência", "Recuperação", "Tolerância ao Estresse"]
    ),
    "foco_resultados": BehavioralSkill(
        id="foco_resultados",
        nome="Foco em Resultados",
        descricao="Orientação para entrega de resultados concretos e mensuráveis",
        categoria="execucao",
        subcategorias=["Orientação para Metas", "Entrega", "Performance"]
    ),
    "orientacao_cliente": BehavioralSkill(
        id="orientacao_cliente",
        nome="Orientação ao Cliente",
        descricao="Compromisso em entender e atender às necessidades dos clientes internos e externos",
        categoria="interpessoal",
        subcategorias=["Foco no Cliente", "Atendimento", "Experiência do Cliente"]
    ),
    "criatividade": BehavioralSkill(
        id="criatividade",
        nome="Criatividade",
        descricao="Capacidade de gerar ideias originais e encontrar soluções inovadoras",
        categoria="analitica",
        subcategorias=["Ideação", "Pensamento Lateral", "Originalidade"]
    ),
    "inovacao": BehavioralSkill(
        id="inovacao",
        nome="Inovação",
        descricao="Habilidade de implementar novas ideias que geram valor para o negócio",
        categoria="analitica",
        subcategorias=["Implementação de Ideias", "Melhoria Contínua", "Disrupção"]
    ),
    "tomada_decisao": BehavioralSkill(
        id="tomada_decisao",
        nome="Tomada de Decisão",
        descricao="Capacidade de tomar decisões tempestivas e fundamentadas",
        categoria="gestao",
        subcategorias=["Decisividade", "Julgamento", "Assertividade"]
    ),
    "gestao_conflitos": BehavioralSkill(
        id="gestao_conflitos",
        nome="Gestão de Conflitos",
        descricao="Habilidade de identificar, mediar e resolver conflitos de forma construtiva",
        categoria="interpessoal",
        subcategorias=["Mediação", "Resolução", "Harmonização"]
    ),
    "mentoria": BehavioralSkill(
        id="mentoria",
        nome="Mentoria/Coaching",
        descricao="Capacidade de desenvolver e orientar pessoas em seu crescimento profissional",
        categoria="gestao",
        subcategorias=["Coaching", "Desenvolvimento de Pessoas", "Feedback"]
    ),
    "visao_estrategica": BehavioralSkill(
        id="visao_estrategica",
        nome="Visão Estratégica",
        descricao="Capacidade de pensar no longo prazo e alinhar ações aos objetivos organizacionais",
        categoria="gestao",
        subcategorias=["Pensamento Estratégico", "Visão de Futuro", "Planejamento Estratégico"]
    ),
    "ownership": BehavioralSkill(
        id="ownership",
        nome="Ownership/Senso de Dono",
        descricao="Atitude de responsabilidade total pelos resultados como se fosse o dono do negócio",
        categoria="execucao",
        subcategorias=["Responsabilidade", "Accountability", "Comprometimento"]
    ),
    "pensamento_analitico": BehavioralSkill(
        id="pensamento_analitico",
        nome="Pensamento Analítico",
        descricao="Capacidade de decompor problemas complexos e analisar dados sistematicamente",
        categoria="analitica",
        subcategorias=["Análise de Dados", "Raciocínio Lógico", "Decomposição"]
    ),
    "atencao_detalhes": BehavioralSkill(
        id="atencao_detalhes",
        nome="Atenção aos Detalhes",
        descricao="Cuidado minucioso para garantir precisão e qualidade nas entregas",
        categoria="execucao",
        subcategorias=["Precisão", "Meticulosidade", "Rigor"]
    ),
    "aprendizado_continuo": BehavioralSkill(
        id="aprendizado_continuo",
        nome="Aprendizado Contínuo",
        descricao="Disposição para buscar constantemente novos conhecimentos e habilidades",
        categoria="pessoal",
        subcategorias=["Curiosidade", "Autodesenvolvimento", "Growth Mindset"]
    ),
    "etica": BehavioralSkill(
        id="etica",
        nome="Ética e Integridade",
        descricao="Conduta pautada por princípios éticos, honestidade e transparência",
        categoria="pessoal",
        subcategorias=["Honestidade", "Transparência", "Integridade"]
    ),
    "autogestao": BehavioralSkill(
        id="autogestao",
        nome="Autogestão",
        descricao="Capacidade de gerenciar próprias emoções, tempo e desenvolvimento sem supervisão constante",
        categoria="pessoal",
        subcategorias=["Autonomia", "Autodisciplina", "Autorregulação"]
    ),
    "relacionamento_interpessoal": BehavioralSkill(
        id="relacionamento_interpessoal",
        nome="Relacionamento Interpessoal",
        descricao="Habilidade de construir e manter relacionamentos profissionais positivos",
        categoria="interpessoal",
        subcategorias=["Networking", "Rapport", "Conexão"]
    ),
    "inteligencia_emocional": BehavioralSkill(
        id="inteligencia_emocional",
        nome="Inteligência Emocional",
        descricao="Capacidade de reconhecer e gerenciar próprias emoções e as dos outros",
        categoria="interpessoal",
        subcategorias=["Autoconsciência", "Empatia", "Regulação Emocional"]
    ),
    "orientacao_dados": BehavioralSkill(
        id="orientacao_dados",
        nome="Orientação a Dados",
        descricao="Tendência a basear decisões em dados e evidências objetivas",
        categoria="analitica",
        subcategorias=["Data-Driven", "Evidências", "Métricas"]
    ),
    "senso_urgencia": BehavioralSkill(
        id="senso_urgencia",
        nome="Senso de Urgência",
        descricao="Capacidade de agir com rapidez e eficiência quando necessário",
        categoria="execucao",
        subcategorias=["Agilidade", "Rapidez", "Prontidão"]
    ),
    "delegacao": BehavioralSkill(
        id="delegacao",
        nome="Delegação",
        descricao="Habilidade de distribuir responsabilidades de forma eficaz desenvolvendo a equipe",
        categoria="gestao",
        subcategorias=["Distribuição de Tarefas", "Empowerment", "Confiança"]
    ),
    "gestao_stakeholders": BehavioralSkill(
        id="gestao_stakeholders",
        nome="Gestão de Stakeholders",
        descricao="Capacidade de identificar, priorizar e gerenciar expectativas de partes interessadas",
        categoria="gestao",
        subcategorias=["Mapeamento", "Engajamento", "Alinhamento"]
    ),
    "apresentacao": BehavioralSkill(
        id="apresentacao",
        nome="Apresentação/Oratória",
        descricao="Habilidade de apresentar ideias de forma clara e envolvente para diferentes públicos",
        categoria="interpessoal",
        subcategorias=["Oratória", "Storytelling", "Public Speaking"]
    ),
    "gestao_projetos_soft": BehavioralSkill(
        id="gestao_projetos_soft",
        nome="Gestão de Projetos (Soft)",
        descricao="Capacidade de planejar, executar e entregar projetos de forma organizada",
        categoria="execucao",
        subcategorias=["Planejamento", "Execução", "Monitoramento"]
    ),
    "pensamento_sistemico": BehavioralSkill(
        id="pensamento_sistemico",
        nome="Pensamento Sistêmico",
        descricao="Capacidade de ver o todo e entender como as partes se conectam",
        categoria="analitica",
        subcategorias=["Visão Holística", "Interconexões", "Big Picture"]
    ),
    "tolerancia_ambiguidade": BehavioralSkill(
        id="tolerancia_ambiguidade",
        nome="Tolerância à Ambiguidade",
        descricao="Conforto para operar em cenários incertos sem informações completas",
        categoria="pessoal",
        subcategorias=["Incerteza", "Complexidade", "VUCA"]
    ),
    "consciencia_cultural": BehavioralSkill(
        id="consciencia_cultural",
        nome="Consciência Cultural",
        descricao="Sensibilidade para trabalhar com pessoas de diferentes culturas e backgrounds",
        categoria="interpessoal",
        subcategorias=["Diversidade", "Inclusão", "Multiculturalismo"]
    ),
    "networking": BehavioralSkill(
        id="networking",
        nome="Networking",
        descricao="Habilidade de construir e manter uma rede de contatos profissionais",
        categoria="interpessoal",
        subcategorias=["Conexões", "Relacionamentos", "Rede de Contatos"]
    ),
    "planejamento": BehavioralSkill(
        id="planejamento",
        nome="Planejamento",
        descricao="Capacidade de definir objetivos, estratégias e ações para alcançar metas",
        categoria="gestao",
        subcategorias=["Estratégia", "Roadmap", "Metas"]
    ),
    "persistencia": BehavioralSkill(
        id="persistencia",
        nome="Persistência",
        descricao="Determinação para continuar buscando objetivos apesar de obstáculos",
        categoria="pessoal",
        subcategorias=["Determinação", "Tenacidade", "Perseverança"]
    ),
    "humildade": BehavioralSkill(
        id="humildade",
        nome="Humildade",
        descricao="Reconhecimento de próprias limitações e abertura para aprender com outros",
        categoria="pessoal",
        subcategorias=["Abertura", "Receptividade", "Autorreflexão"]
    ),
    "confidencialidade": BehavioralSkill(
        id="confidencialidade",
        nome="Confidencialidade",
        descricao="Compromisso com a proteção de informações sensíveis e sigilosas",
        categoria="pessoal",
        subcategorias=["Sigilo", "Discrição", "Proteção de Dados"]
    ),
    "orientacao_qualidade": BehavioralSkill(
        id="orientacao_qualidade",
        nome="Orientação para Qualidade",
        descricao="Comprometimento com altos padrões de qualidade em todas as entregas",
        categoria="execucao",
        subcategorias=["Excelência", "Padrões", "Melhoria"]
    ),
    "gestao_stress": BehavioralSkill(
        id="gestao_stress",
        nome="Gestão de Estresse",
        descricao="Capacidade de manter desempenho e equilíbrio em situações de alta pressão",
        categoria="pessoal",
        subcategorias=["Equilíbrio", "Calma", "Controle"]
    ),
    "curiosidade": BehavioralSkill(
        id="curiosidade",
        nome="Curiosidade",
        descricao="Interesse genuíno em explorar, questionar e descobrir novas possibilidades",
        categoria="analitica",
        subcategorias=["Exploração", "Investigação", "Descoberta"]
    ),
    "agilidade_aprendizado": BehavioralSkill(
        id="agilidade_aprendizado",
        nome="Agilidade de Aprendizado",
        descricao="Capacidade de aprender rapidamente em situações novas e desconhecidas",
        categoria="pessoal",
        subcategorias=["Learning Agility", "Adaptação Rápida", "Absorção"]
    ),
    "coragem": BehavioralSkill(
        id="coragem",
        nome="Coragem",
        descricao="Disposição para tomar riscos calculados e defender posições",
        categoria="pessoal",
        subcategorias=["Ousadia", "Desafio", "Confronto Construtivo"]
    ),
    "foco": BehavioralSkill(
        id="foco",
        nome="Foco",
        descricao="Capacidade de manter atenção e energia nas prioridades mais importantes",
        categoria="execucao",
        subcategorias=["Concentração", "Priorização", "Disciplina"]
    ),
    "visao_cliente": BehavioralSkill(
        id="visao_cliente",
        nome="Visão de Cliente",
        descricao="Capacidade de entender profundamente as necessidades e dores dos clientes",
        categoria="interpessoal",
        subcategorias=["Customer Centric", "Empatia com Cliente", "Jornada do Cliente"]
    ),
}


# =============================================================================
# TECHNICAL SKILLS BY AREA
# =============================================================================

TECHNICAL_SKILLS: dict[str, TechnicalSkill] = {}

# ----- TECNOLOGIA (50+ skills) -----
_tech_skills = [
    ("python", "Python", ["tecnologia"], "intermediario", "Linguagem de programação versátil para backend, dados e automação", "programacao", ["programming", "backend", "scripts"]),
    ("java", "Java", ["tecnologia"], "intermediario", "Linguagem de programação orientada a objetos para aplicações enterprise", "programacao", ["programming", "backend", "spring"]),
    ("javascript", "JavaScript", ["tecnologia"], "intermediario", "Linguagem de programação para web frontend e backend", "programacao", ["programming", "frontend", "node"]),
    ("typescript", "TypeScript", ["tecnologia"], "intermediario", "Superset tipado de JavaScript para aplicações robustas", "programacao", ["programming", "frontend", "node"]),
    ("csharp", "C#/.NET", ["tecnologia"], "intermediario", "Linguagem e framework da Microsoft para aplicações enterprise", "programacao", ["programming", "backend", "dotnet"]),
    ("go", "Go/Golang", ["tecnologia"], "avancado", "Linguagem de programação para sistemas de alta performance", "programacao", ["programming", "backend", "cloud"]),
    ("rust", "Rust", ["tecnologia"], "avancado", "Linguagem de programação para sistemas de baixo nível com segurança", "programacao", ["programming", "systems"]),
    ("react", "React", ["tecnologia"], "intermediario", "Biblioteca JavaScript para construção de interfaces de usuário", "frontend", ["frontend", "ui", "spa"]),
    ("angular", "Angular", ["tecnologia"], "intermediario", "Framework TypeScript para aplicações web enterprise", "frontend", ["frontend", "ui", "spa"]),
    ("vuejs", "Vue.js", ["tecnologia"], "intermediario", "Framework JavaScript progressivo para interfaces de usuário", "frontend", ["frontend", "ui", "spa"]),
    ("nextjs", "Next.js", ["tecnologia"], "intermediario", "Framework React para aplicações web com SSR", "frontend", ["frontend", "react", "fullstack"]),
    ("nodejs", "Node.js", ["tecnologia"], "intermediario", "Runtime JavaScript para backend e ferramentas", "backend", ["backend", "javascript", "api"]),
    ("sql", "SQL", ["tecnologia", "financeiro", "contabil"], "basico", "Linguagem para consulta e manipulação de bancos de dados", "dados", ["database", "query", "relacional"]),
    ("postgresql", "PostgreSQL", ["tecnologia"], "intermediario", "Sistema de banco de dados relacional avançado open source", "dados", ["database", "relacional", "sql"]),
    ("mysql", "MySQL", ["tecnologia"], "intermediario", "Sistema de banco de dados relacional popular", "dados", ["database", "relacional", "sql"]),
    ("mongodb", "MongoDB", ["tecnologia"], "intermediario", "Banco de dados NoSQL orientado a documentos", "dados", ["database", "nosql", "documentos"]),
    ("redis", "Redis", ["tecnologia"], "intermediario", "Banco de dados em memória para cache e mensageria", "dados", ["cache", "nosql", "memoria"]),
    ("elasticsearch", "Elasticsearch", ["tecnologia"], "avancado", "Motor de busca e análise distribuído", "dados", ["search", "analytics", "logs"]),
    ("docker", "Docker", ["tecnologia"], "intermediario", "Plataforma de containerização de aplicações", "devops", ["containers", "devops", "deploy"]),
    ("kubernetes", "Kubernetes", ["tecnologia"], "avancado", "Orquestrador de containers para deploy e scaling", "devops", ["containers", "orchestration", "cloud"]),
    ("aws", "AWS", ["tecnologia"], "intermediario", "Plataforma de cloud computing da Amazon", "cloud", ["cloud", "infraestrutura", "saas"]),
    ("azure", "Microsoft Azure", ["tecnologia"], "intermediario", "Plataforma de cloud computing da Microsoft", "cloud", ["cloud", "infraestrutura", "microsoft"]),
    ("gcp", "Google Cloud Platform", ["tecnologia"], "intermediario", "Plataforma de cloud computing do Google", "cloud", ["cloud", "infraestrutura", "google"]),
    ("terraform", "Terraform", ["tecnologia"], "avancado", "Ferramenta de infraestrutura como código", "devops", ["iac", "infrastructure", "automation"]),
    ("cicd", "CI/CD", ["tecnologia"], "intermediario", "Práticas de integração e deploy contínuos", "devops", ["automation", "pipeline", "deploy"]),
    ("git", "Git", ["tecnologia"], "basico", "Sistema de controle de versão distribuído", "ferramentas", ["versioning", "source control"]),
    ("linux", "Linux", ["tecnologia"], "intermediario", "Sistema operacional open source para servidores", "infraestrutura", ["os", "servers", "admin"]),
    ("apis_rest", "APIs REST", ["tecnologia"], "intermediario", "Design e desenvolvimento de APIs RESTful", "backend", ["api", "web services", "http"]),
    ("graphql", "GraphQL", ["tecnologia"], "intermediario", "Linguagem de query para APIs", "backend", ["api", "query", "facebook"]),
    ("microservicos", "Microsserviços", ["tecnologia"], "avancado", "Arquitetura de sistemas distribuídos", "arquitetura", ["architecture", "distributed", "services"]),
    ("machine_learning", "Machine Learning", ["tecnologia"], "avancado", "Algoritmos de aprendizado de máquina", "ia", ["ai", "ml", "data science"]),
    ("deep_learning", "Deep Learning", ["tecnologia"], "avancado", "Redes neurais profundas para IA avançada", "ia", ["ai", "neural networks", "ml"]),
    ("nlp", "NLP/Processamento de Linguagem Natural", ["tecnologia"], "avancado", "Processamento e análise de texto por IA", "ia", ["ai", "text", "language"]),
    ("llm", "LLMs/Modelos de Linguagem", ["tecnologia"], "avancado", "Modelos de linguagem de grande escala como GPT", "ia", ["ai", "gpt", "generative"]),
    ("tensorflow", "TensorFlow", ["tecnologia"], "avancado", "Framework de machine learning do Google", "ia", ["ml", "deep learning", "google"]),
    ("pytorch", "PyTorch", ["tecnologia"], "avancado", "Framework de machine learning do Facebook", "ia", ["ml", "deep learning", "facebook"]),
    ("spark", "Apache Spark", ["tecnologia"], "avancado", "Framework de processamento de big data", "dados", ["big data", "processing", "analytics"]),
    ("airflow", "Apache Airflow", ["tecnologia"], "avancado", "Orquestrador de workflows de dados", "dados", ["etl", "orchestration", "pipeline"]),
    ("kafka", "Apache Kafka", ["tecnologia"], "avancado", "Plataforma de streaming de eventos distribuída", "dados", ["streaming", "messaging", "events"]),
    ("dbt", "dbt", ["tecnologia"], "intermediario", "Ferramenta de transformação de dados em SQL", "dados", ["etl", "transformation", "analytics"]),
    ("power_bi", "Power BI", ["tecnologia", "financeiro"], "intermediario", "Ferramenta de business intelligence da Microsoft", "bi", ["analytics", "dashboards", "reporting"]),
    ("tableau", "Tableau", ["tecnologia", "financeiro"], "intermediario", "Plataforma de visualização de dados", "bi", ["analytics", "visualization", "dashboards"]),
    ("scrum", "Scrum", ["tecnologia"], "basico", "Framework ágil para gestão de projetos de software", "metodologia", ["agile", "project management"]),
    ("kanban", "Kanban", ["tecnologia"], "basico", "Metodologia ágil de gestão visual de trabalho", "metodologia", ["agile", "workflow", "lean"]),
    ("seguranca_informacao", "Segurança da Informação", ["tecnologia"], "avancado", "Práticas e tecnologias de proteção de dados e sistemas", "seguranca", ["security", "infosec", "cybersecurity"]),
    ("pentest", "Pentest/Ethical Hacking", ["tecnologia"], "avancado", "Testes de invasão e análise de vulnerabilidades", "seguranca", ["security", "hacking", "vulnerabilities"]),
    ("mobile_ios", "Desenvolvimento iOS", ["tecnologia"], "intermediario", "Desenvolvimento de aplicativos para iOS/iPhone", "mobile", ["swift", "apple", "mobile"]),
    ("mobile_android", "Desenvolvimento Android", ["tecnologia"], "intermediario", "Desenvolvimento de aplicativos para Android", "mobile", ["kotlin", "java", "mobile"]),
    ("react_native", "React Native", ["tecnologia"], "intermediario", "Framework para desenvolvimento mobile cross-platform", "mobile", ["mobile", "cross-platform", "javascript"]),
    ("flutter", "Flutter", ["tecnologia"], "intermediario", "Framework Google para desenvolvimento mobile cross-platform", "mobile", ["mobile", "cross-platform", "dart"]),
    ("ux_ui", "UX/UI Design", ["tecnologia", "marketing"], "intermediario", "Design de experiência e interface do usuário", "design", ["design", "user experience", "interface"]),
    ("figma", "Figma", ["tecnologia", "marketing"], "basico", "Ferramenta de design de interfaces colaborativa", "design", ["design", "prototyping", "ui"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _tech_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- FINANCEIRO (40+ skills) -----
_fin_skills = [
    ("fpa", "FP&A (Financial Planning & Analysis)", ["financeiro"], "intermediario", "Planejamento financeiro, orçamento e análise de variância", "planejamento", ["budget", "forecast", "variance"]),
    ("orcamento", "Orçamento/Budget", ["financeiro"], "basico", "Elaboração e gestão de orçamentos empresariais", "planejamento", ["budget", "planning"]),
    ("forecast", "Forecast", ["financeiro"], "intermediario", "Projeções financeiras e revisões de estimativas", "planejamento", ["projection", "estimation"]),
    ("variance_analysis", "Análise de Variância", ["financeiro"], "intermediario", "Análise de desvios entre real e orçado", "analise", ["variance", "deviation"]),
    ("modelagem_financeira", "Modelagem Financeira", ["financeiro"], "avancado", "Construção de modelos financeiros em Excel/Python", "analise", ["financial modeling", "dcf"]),
    ("valuation", "Valuation", ["financeiro"], "avancado", "Avaliação de empresas e ativos", "analise", ["dcf", "multiples", "valuation"]),
    ("tesouraria", "Tesouraria", ["financeiro"], "intermediario", "Gestão de caixa, liquidez e fluxo de caixa", "tesouraria", ["cash management", "liquidity"]),
    ("fluxo_caixa", "Fluxo de Caixa", ["financeiro"], "basico", "Gestão e projeção de entradas e saídas de caixa", "tesouraria", ["cash flow", "dfc"]),
    ("cambio", "Operações de Câmbio", ["financeiro"], "avancado", "Operações de câmbio e hedge cambial", "tesouraria", ["fx", "forex", "hedge"]),
    ("derivativos", "Derivativos", ["financeiro"], "avancado", "Operações com derivativos para hedge e especulação", "tesouraria", ["hedge", "options", "futures"]),
    ("credito", "Análise de Crédito", ["financeiro"], "intermediario", "Avaliação de risco de crédito de clientes e fornecedores", "credito", ["credit analysis", "risk"]),
    ("cobranca", "Gestão de Cobrança", ["financeiro"], "basico", "Processos de cobrança e recuperação de crédito", "credito", ["collection", "receivables"]),
    ("contas_pagar", "Contas a Pagar", ["financeiro"], "basico", "Gestão de obrigações e pagamentos a fornecedores", "operacional", ["accounts payable", "ap"]),
    ("contas_receber", "Contas a Receber", ["financeiro"], "basico", "Gestão de recebíveis e faturamento", "operacional", ["accounts receivable", "ar"]),
    ("controladoria", "Controladoria", ["financeiro"], "avancado", "Controle de gestão e reporting gerencial", "controladoria", ["controlling", "management accounting"]),
    ("relatorios_gerenciais", "Relatórios Gerenciais", ["financeiro"], "intermediario", "Elaboração de reports para tomada de decisão", "controladoria", ["reporting", "dashboards"]),
    ("kpis_financeiros", "KPIs Financeiros", ["financeiro"], "intermediario", "Definição e acompanhamento de indicadores financeiros", "controladoria", ["indicators", "metrics"]),
    ("excel_avancado_fin", "Excel Avançado (Financeiro)", ["financeiro"], "intermediario", "Fórmulas avançadas, macros e análise de dados", "ferramentas", ["spreadsheet", "macros", "analysis"]),
    ("sap_fi", "SAP FI", ["financeiro", "contabil"], "intermediario", "Módulo financeiro do SAP ERP", "sistemas", ["erp", "sap"]),
    ("oracle_financials", "Oracle Financials", ["financeiro"], "intermediario", "Suite financeira da Oracle", "sistemas", ["erp", "oracle"]),
    ("totvs_protheus", "TOTVS Protheus", ["financeiro", "contabil"], "intermediario", "ERP brasileiro para gestão financeira", "sistemas", ["erp", "totvs"]),
    ("ma", "M&A (Fusões e Aquisições)", ["financeiro", "juridico"], "avancado", "Processos de fusões, aquisições e due diligence", "corporate_finance", ["mergers", "acquisitions", "due diligence"]),
    ("due_diligence_fin", "Due Diligence Financeira", ["financeiro"], "avancado", "Análise financeira detalhada em processos de M&A", "corporate_finance", ["m&a", "analysis"]),
    ("restructuring", "Reestruturação Financeira", ["financeiro"], "avancado", "Processos de reestruturação e turnaround", "corporate_finance", ["turnaround", "restructuring"]),
    ("investimentos", "Gestão de Investimentos", ["financeiro"], "avancado", "Análise e gestão de carteira de investimentos", "investimentos", ["portfolio", "assets"]),
    ("renda_fixa", "Renda Fixa", ["financeiro"], "intermediario", "Análise e operação de títulos de renda fixa", "investimentos", ["bonds", "fixed income"]),
    ("renda_variavel", "Renda Variável", ["financeiro"], "intermediario", "Análise e operação de ações e derivativos", "investimentos", ["stocks", "equities"]),
    ("analise_investimentos", "Análise de Investimentos", ["financeiro"], "intermediario", "Avaliação de projetos e retorno de investimentos", "analise", ["roi", "payback", "tir"]),
    ("viabilidade_economica", "Viabilidade Econômica", ["financeiro"], "intermediario", "Estudos de viabilidade de projetos", "analise", ["feasibility", "business case"]),
    ("custo_capital", "Custo de Capital", ["financeiro"], "avancado", "Cálculo de WACC e custo de oportunidade", "analise", ["wacc", "cost of capital"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _fin_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- CONTÁBIL (35+ skills) -----
_contabil_skills = [
    ("contabilidade_geral", "Contabilidade Geral", ["contabil"], "basico", "Princípios e práticas de escrituração contábil", "contabilidade", ["accounting", "bookkeeping"]),
    ("fechamento_contabil", "Fechamento Contábil", ["contabil"], "intermediario", "Processos de fechamento mensal e anual", "contabilidade", ["closing", "monthly close"]),
    ("conciliacao_contabil", "Conciliação Contábil", ["contabil"], "basico", "Conciliação de contas e saldos contábeis", "contabilidade", ["reconciliation"]),
    ("lancamentos_contabeis", "Lançamentos Contábeis", ["contabil"], "basico", "Registro de transações no sistema contábil", "contabilidade", ["journal entries", "bookkeeping"]),
    ("balanco_patrimonial", "Balanço Patrimonial", ["contabil"], "intermediario", "Elaboração e análise do balanço", "demonstracoes", ["balance sheet"]),
    ("dre", "DRE (Demonstração de Resultados)", ["contabil"], "intermediario", "Elaboração e análise da DRE", "demonstracoes", ["income statement", "p&l"]),
    ("dfc", "DFC (Demonstração de Fluxo de Caixa)", ["contabil"], "intermediario", "Elaboração da demonstração de fluxo de caixa", "demonstracoes", ["cash flow statement"]),
    ("dmpl", "DMPL", ["contabil"], "intermediario", "Demonstração de mutações do patrimônio líquido", "demonstracoes", ["equity statement"]),
    ("notas_explicativas", "Notas Explicativas", ["contabil"], "avancado", "Elaboração de notas explicativas às demonstrações", "demonstracoes", ["footnotes", "disclosures"]),
    ("ifrs", "IFRS", ["contabil"], "avancado", "Normas internacionais de contabilidade", "normas", ["international standards"]),
    ("cpc", "CPC (Comitê de Pronunciamentos Contábeis)", ["contabil"], "avancado", "Pronunciamentos contábeis brasileiros", "normas", ["brazilian standards"]),
    ("cpc_06", "CPC 06 - Arrendamentos", ["contabil"], "avancado", "Contabilização de arrendamentos (IFRS 16)", "normas", ["leasing", "ifrs 16"]),
    ("cpc_47", "CPC 47 - Receitas", ["contabil"], "avancado", "Reconhecimento de receitas (IFRS 15)", "normas", ["revenue", "ifrs 15"]),
    ("cpc_48", "CPC 48 - Instrumentos Financeiros", ["contabil"], "avancado", "Contabilização de instrumentos financeiros", "normas", ["financial instruments", "ifrs 9"]),
    ("ativo_imobilizado", "Ativo Imobilizado", ["contabil"], "intermediario", "Controle e contabilização de ativos fixos", "patrimonial", ["fixed assets", "ppe"]),
    ("depreciacao", "Depreciação", ["contabil"], "basico", "Cálculo e registro de depreciação de ativos", "patrimonial", ["depreciation"]),
    ("intangivel", "Ativo Intangível", ["contabil"], "intermediario", "Contabilização de ativos intangíveis", "patrimonial", ["intangible assets"]),
    ("estoques", "Contabilização de Estoques", ["contabil"], "intermediario", "Controle e valoração de estoques", "patrimonial", ["inventory"]),
    ("provisoes", "Provisões e Contingências", ["contabil"], "avancado", "Registro de provisões para contingências", "patrimonial", ["provisions", "contingencies"]),
    ("consolidacao", "Consolidação de Balanços", ["contabil"], "avancado", "Consolidação de demonstrações de grupos empresariais", "avancado", ["consolidation"]),
    ("contabilidade_custos", "Contabilidade de Custos", ["contabil"], "intermediario", "Apuração e análise de custos", "custos", ["cost accounting"]),
    ("custeio_absorcao", "Custeio por Absorção", ["contabil"], "intermediario", "Método de custeio absorção", "custos", ["absorption costing"]),
    ("custeio_variavel", "Custeio Variável", ["contabil"], "intermediario", "Método de custeio variável/direto", "custos", ["variable costing"]),
    ("abc_custos", "Custeio ABC", ["contabil"], "avancado", "Custeio baseado em atividades", "custos", ["activity based costing"]),
    ("auditoria_externa", "Auditoria Externa", ["contabil", "compliance"], "avancado", "Atendimento a auditorias independentes", "auditoria", ["external audit"]),
    ("sped_contabil", "SPED Contábil/ECD", ["contabil"], "intermediario", "Escrituração Contábil Digital", "obrigacoes", ["digital bookkeeping"]),
    ("ecf", "ECF (Escrituração Contábil Fiscal)", ["contabil", "fiscal"], "intermediario", "Obrigação acessória de IR", "obrigacoes", ["tax bookkeeping"]),
    ("contabilidade_societaria", "Contabilidade Societária", ["contabil"], "intermediario", "Aspectos contábeis de operações societárias", "societario", ["corporate accounting"]),
    ("relatorio_administracao", "Relatório da Administração", ["contabil"], "avancado", "Elaboração de relatório anual da administração", "reporting", ["management report"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _contabil_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- FISCAL/TRIBUTÁRIO (40+ skills) -----
_fiscal_skills = [
    ("icms", "ICMS", ["fiscal"], "intermediario", "Imposto sobre circulação de mercadorias e serviços", "impostos_indiretos", ["state tax", "vat"]),
    ("ipi", "IPI", ["fiscal"], "intermediario", "Imposto sobre produtos industrializados", "impostos_indiretos", ["federal tax"]),
    ("pis_cofins", "PIS/COFINS", ["fiscal"], "intermediario", "Contribuições sociais sobre faturamento", "impostos_indiretos", ["contributions"]),
    ("iss", "ISS", ["fiscal"], "intermediario", "Imposto sobre serviços municipal", "impostos_indiretos", ["municipal tax"]),
    ("icms_st", "ICMS-ST (Substituição Tributária)", ["fiscal"], "avancado", "Regime de substituição tributária do ICMS", "impostos_indiretos", ["tax substitution"]),
    ("difal", "DIFAL", ["fiscal"], "intermediario", "Diferencial de alíquota do ICMS", "impostos_indiretos", ["differential rate"]),
    ("irpj", "IRPJ", ["fiscal"], "intermediario", "Imposto de renda pessoa jurídica", "impostos_diretos", ["corporate income tax"]),
    ("csll", "CSLL", ["fiscal"], "intermediario", "Contribuição social sobre o lucro", "impostos_diretos", ["social contribution"]),
    ("lucro_real", "Lucro Real", ["fiscal"], "avancado", "Regime tributário lucro real", "regimes", ["taxable income"]),
    ("lucro_presumido", "Lucro Presumido", ["fiscal"], "intermediario", "Regime tributário lucro presumido", "regimes", ["presumed income"]),
    ("simples_nacional", "Simples Nacional", ["fiscal"], "intermediario", "Regime tributário simplificado", "regimes", ["simplified tax"]),
    ("sped_fiscal", "SPED Fiscal/EFD", ["fiscal"], "intermediario", "Escrituração Fiscal Digital ICMS/IPI", "obrigacoes", ["digital tax"]),
    ("efd_contribuicoes", "EFD Contribuições", ["fiscal"], "intermediario", "Escrituração de PIS/COFINS", "obrigacoes", ["contributions"]),
    ("nfe", "NF-e", ["fiscal"], "basico", "Nota Fiscal Eletrônica", "documentos", ["electronic invoice"]),
    ("nfs_e", "NFS-e", ["fiscal"], "basico", "Nota Fiscal de Serviços Eletrônica", "documentos", ["service invoice"]),
    ("ct_e", "CT-e", ["fiscal"], "intermediario", "Conhecimento de Transporte Eletrônico", "documentos", ["transport document"]),
    ("reinf", "EFD-Reinf", ["fiscal", "dp"], "intermediario", "Escrituração de retenções e informações fiscais", "obrigacoes", ["withholding"]),
    ("dctf", "DCTF", ["fiscal"], "intermediario", "Declaração de débitos e créditos tributários", "obrigacoes", ["tax declaration"]),
    ("dirf", "DIRF", ["fiscal", "dp"], "intermediario", "Declaração do imposto retido na fonte", "obrigacoes", ["withholding declaration"]),
    ("perdcomp", "PER/DCOMP", ["fiscal"], "intermediario", "Pedido de restituição/compensação", "obrigacoes", ["tax refund"]),
    ("planejamento_tributario", "Planejamento Tributário", ["fiscal"], "avancado", "Estratégias legais de economia tributária", "estrategico", ["tax planning"]),
    ("elisao_fiscal", "Elisão Fiscal", ["fiscal"], "avancado", "Práticas legais de redução de carga tributária", "estrategico", ["tax avoidance"]),
    ("transfer_pricing", "Transfer Pricing", ["fiscal"], "avancado", "Preços de transferência em operações internacionais", "internacional", ["intercompany pricing"]),
    ("tributacao_internacional", "Tributação Internacional", ["fiscal"], "avancado", "Aspectos tributários de operações internacionais", "internacional", ["international tax"]),
    ("tratados_bitributacao", "Tratados de Bitributação", ["fiscal"], "avancado", "Aplicação de tratados para evitar dupla tributação", "internacional", ["tax treaties"]),
    ("retencoes_fonte", "Retenções na Fonte", ["fiscal"], "intermediario", "IR, PIS, COFINS, CSLL retidos na fonte", "retencoes", ["withholding"]),
    ("inss_retido", "INSS Retido", ["fiscal", "dp"], "intermediario", "Retenção de INSS sobre serviços", "retencoes", ["social security"]),
    ("iss_retido", "ISS Retido", ["fiscal"], "intermediario", "Retenção de ISS sobre serviços", "retencoes", ["municipal tax"]),
    ("contencioso_tributario", "Contencioso Tributário", ["fiscal", "juridico"], "avancado", "Processos administrativos e judiciais tributários", "contencioso", ["tax litigation"]),
    ("parcelamentos_fiscais", "Parcelamentos Fiscais", ["fiscal"], "intermediario", "Adesão a programas de parcelamento", "contencioso", ["installment"]),
    ("certidoes_negativas", "Certidões Negativas", ["fiscal"], "basico", "Obtenção e gestão de certidões de regularidade", "compliance", ["tax certificates"]),
    ("bloco_k", "Bloco K", ["fiscal"], "avancado", "Controle da produção e estoque no SPED", "obrigacoes", ["production control"]),
    ("ncm", "NCM (Classificação Fiscal)", ["fiscal", "compras"], "intermediario", "Classificação fiscal de mercadorias", "classificacao", ["tariff code"]),
    ("cest", "CEST", ["fiscal"], "intermediario", "Código especificador da substituição tributária", "classificacao", ["substitution code"]),
    ("beneficios_fiscais", "Benefícios Fiscais", ["fiscal"], "avancado", "Identificação e aplicação de incentivos fiscais", "estrategico", ["tax incentives"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _fiscal_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- RH (35+ skills) -----
_rh_skills = [
    ("recrutamento_selecao", "Recrutamento e Seleção", ["rh"], "basico", "Processos de atração e seleção de talentos", "rs", ["recruitment", "hiring"]),
    ("entrevista_competencias", "Entrevista por Competências", ["rh"], "intermediario", "Técnica de entrevista estruturada por competências", "rs", ["behavioral interview"]),
    ("hunting", "Hunting/Executive Search", ["rh"], "avancado", "Busca ativa de talentos para posições estratégicas", "rs", ["headhunting"]),
    ("employer_branding", "Employer Branding", ["rh", "marketing"], "intermediario", "Gestão da marca empregadora", "rs", ["employer brand"]),
    ("ats", "ATS (Applicant Tracking System)", ["rh"], "basico", "Sistemas de gestão de recrutamento", "sistemas", ["recruitment software"]),
    ("linkedin_recruiter", "LinkedIn Recruiter", ["rh"], "intermediario", "Ferramenta de recrutamento do LinkedIn", "ferramentas", ["sourcing"]),
    ("assessment", "Assessment/Avaliação", ["rh"], "intermediario", "Aplicação e análise de assessments", "avaliacao", ["evaluation"]),
    ("td", "Treinamento e Desenvolvimento", ["rh"], "intermediario", "Programas de capacitação e desenvolvimento", "td", ["training", "learning"]),
    ("lms", "LMS (Learning Management System)", ["rh"], "intermediario", "Plataformas de gestão de aprendizagem", "sistemas", ["e-learning"]),
    ("pdi", "PDI (Plano de Desenvolvimento Individual)", ["rh"], "intermediario", "Elaboração e acompanhamento de PDIs", "td", ["development plan"]),
    ("lnt", "LNT (Levantamento de Necessidades)", ["rh"], "intermediario", "Identificação de gaps de treinamento", "td", ["training needs"]),
    ("avaliacao_desempenho", "Avaliação de Desempenho", ["rh"], "intermediario", "Processos de avaliação de performance", "performance", ["performance review"]),
    ("feedback_360", "Feedback 360°", ["rh"], "intermediario", "Avaliação multi-fonte de competências", "performance", ["multi-rater feedback"]),
    ("okr", "OKR", ["rh", "operacoes"], "intermediario", "Objectives and Key Results", "performance", ["goals"]),
    ("cargos_salarios", "Cargos e Salários", ["rh"], "intermediario", "Estruturação de planos de cargos e remuneração", "remuneracao", ["job grading", "compensation"]),
    ("pesquisa_salarial", "Pesquisa Salarial", ["rh"], "intermediario", "Análise de mercado e benchmarking salarial", "remuneracao", ["salary survey"]),
    ("remuneracao_variavel", "Remuneração Variável", ["rh"], "avancado", "Programas de bônus e incentivos", "remuneracao", ["bonus", "incentives"]),
    ("stock_options", "Stock Options/ILP", ["rh"], "avancado", "Programas de incentivos de longo prazo", "remuneracao", ["equity", "ilp"]),
    ("pesquisa_clima", "Pesquisa de Clima", ["rh"], "intermediario", "Avaliação de clima organizacional", "clima", ["engagement survey"]),
    ("enps", "eNPS", ["rh"], "basico", "Employee Net Promoter Score", "clima", ["employee satisfaction"]),
    ("cultura_organizacional", "Cultura Organizacional", ["rh"], "intermediario", "Gestão e desenvolvimento de cultura", "cultura", ["organizational culture"]),
    ("people_analytics", "People Analytics", ["rh"], "avancado", "Análise de dados de pessoas para decisões de RH", "analytics", ["hr analytics"]),
    ("turnover", "Gestão de Turnover", ["rh"], "intermediario", "Análise e ações de retenção", "analytics", ["attrition"]),
    ("onboarding", "Onboarding", ["rh"], "basico", "Programas de integração de novos colaboradores", "integracao", ["induction"]),
    ("offboarding", "Offboarding", ["rh"], "basico", "Processos de desligamento estruturado", "integracao", ["exit"]),
    ("business_partner", "BP de RH", ["rh"], "avancado", "Atuação como parceiro estratégico do negócio", "estrategico", ["hrbp"]),
    ("consultoria_interna", "Consultoria Interna de RH", ["rh"], "intermediario", "Suporte consultivo às áreas de negócio", "estrategico", ["internal consulting"]),
    ("sucessao", "Planejamento de Sucessão", ["rh"], "avancado", "Identificação e desenvolvimento de sucessores", "estrategico", ["succession planning"]),
    ("diversidade_inclusao", "Diversidade e Inclusão", ["rh"], "intermediario", "Programas de D&I", "dei", ["d&i"]),
    ("programas_jovens", "Programas de Jovens Talentos", ["rh"], "intermediario", "Estágio, trainee e jovem aprendiz", "programas", ["early career"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _rh_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- DEPARTAMENTO PESSOAL (35+ skills) -----
_dp_skills = [
    ("folha_pagamento", "Folha de Pagamento", ["dp"], "intermediario", "Processamento completo de folha de pagamento", "folha", ["payroll"]),
    ("encargos_sociais", "Encargos Sociais", ["dp"], "intermediario", "Cálculo de INSS, FGTS e contribuições", "folha", ["payroll taxes"]),
    ("irrf_salario", "IRRF sobre Salários", ["dp"], "intermediario", "Cálculo e retenção de IR na folha", "folha", ["income tax"]),
    ("admissao", "Processos de Admissão", ["dp"], "basico", "Documentação e registro de novos colaboradores", "movimentacoes", ["hiring"]),
    ("demissao", "Processos de Demissão", ["dp"], "intermediario", "Rescisões e homologações", "movimentacoes", ["termination"]),
    ("rescisao", "Cálculo Rescisório", ["dp"], "intermediario", "Cálculo de verbas rescisórias", "movimentacoes", ["severance"]),
    ("ferias", "Gestão de Férias", ["dp"], "basico", "Programação e cálculo de férias", "movimentacoes", ["vacation"]),
    ("decimo_terceiro", "13º Salário", ["dp"], "basico", "Cálculo e pagamento do 13º salário", "folha", ["christmas bonus"]),
    ("beneficios_dp", "Gestão de Benefícios", ["dp"], "intermediario", "Administração de VR, VA, VT, plano de saúde", "beneficios", ["benefits administration"]),
    ("vale_transporte", "Vale Transporte", ["dp"], "basico", "Gestão e desconto de vale transporte", "beneficios", ["transportation"]),
    ("plano_saude", "Plano de Saúde", ["dp"], "intermediario", "Gestão de plano de saúde corporativo", "beneficios", ["health insurance"]),
    ("esocial", "e-Social", ["dp"], "intermediario", "Escrituração digital das obrigações trabalhistas", "obrigacoes", ["digital labor"]),
    ("dctfweb", "DCTFWeb", ["dp"], "intermediario", "Declaração de débitos e créditos tributários federais", "obrigacoes", ["tax declaration"]),
    ("clt", "Legislação Trabalhista/CLT", ["dp", "juridico"], "intermediario", "Conhecimento da CLT e legislação trabalhista", "legislacao", ["labor law"]),
    ("reforma_trabalhista", "Reforma Trabalhista", ["dp", "juridico"], "intermediario", "Alterações da reforma trabalhista de 2017", "legislacao", ["labor reform"]),
    ("ponto_eletronico", "Gestão de Ponto", ["dp"], "basico", "Controle de jornada e ponto eletrônico", "jornada", ["time tracking"]),
    ("banco_horas", "Banco de Horas", ["dp"], "intermediario", "Gestão de banco de horas", "jornada", ["time bank"]),
    ("horas_extras", "Horas Extras", ["dp"], "basico", "Cálculo e controle de horas extras", "jornada", ["overtime"]),
    ("afastamentos", "Gestão de Afastamentos", ["dp"], "intermediario", "Controle de afastamentos e atestados", "saude", ["leave management"]),
    ("caged", "CAGED (histórico)", ["dp"], "basico", "Cadastro geral de empregados e desempregados", "obrigacoes", ["employment registry"]),
    ("rais", "RAIS", ["dp"], "basico", "Relação anual de informações sociais", "obrigacoes", ["annual report"]),
    ("fgts_digital", "FGTS Digital", ["dp"], "intermediario", "Novo sistema de recolhimento do FGTS", "obrigacoes", ["digital fgts"]),
    ("seguro_desemprego", "Seguro Desemprego", ["dp"], "basico", "Processos relacionados ao seguro desemprego", "movimentacoes", ["unemployment"]),
    ("pensao_alimenticia", "Pensão Alimentícia", ["dp"], "basico", "Gestão de descontos de pensão", "folha", ["alimony"]),
    ("emprestimo_consignado", "Empréstimo Consignado", ["dp"], "basico", "Gestão de consignações em folha", "folha", ["payroll loan"]),
    ("trabalho_temporario", "Trabalho Temporário", ["dp"], "intermediario", "Gestão de contratos temporários", "contratos", ["temp work"]),
    ("terceirizacao_dp", "Terceirização", ["dp"], "intermediario", "Gestão de terceiros e responsabilidade solidária", "contratos", ["outsourcing"]),
    ("saude_seguranca", "Saúde e Segurança do Trabalho", ["dp", "qualidade"], "intermediario", "NRs, PPRA, PCMSO", "sst", ["occupational safety"]),
    ("cipa", "CIPA", ["dp", "qualidade"], "basico", "Comissão interna de prevenção de acidentes", "sst", ["safety committee"]),
    ("cat", "CAT (Comunicação de Acidente)", ["dp"], "basico", "Registro de acidentes de trabalho", "sst", ["accident report"]),
    ("sistemas_dp", "Sistemas de DP (ADP, Senior, etc)", ["dp"], "intermediario", "Operação de sistemas de gestão de pessoal", "sistemas", ["hr systems"]),
    ("relatorios_dp", "Relatórios Trabalhistas", ["dp"], "intermediario", "Elaboração de relatórios e indicadores de DP", "analytics", ["reports"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _dp_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- COMERCIAL/VENDAS (35+ skills) -----
_comercial_skills = [
    ("vendas_consultivas", "Vendas Consultivas", ["comercial"], "intermediario", "Metodologia de venda focada em solução de problemas", "metodologia", ["solution selling"]),
    ("spin_selling", "SPIN Selling", ["comercial"], "intermediario", "Técnica de vendas baseada em perguntas estratégicas", "metodologia", ["sales technique"]),
    ("challenger_sale", "Challenger Sale", ["comercial"], "avancado", "Metodologia de venda desafiadora", "metodologia", ["sales methodology"]),
    ("meddic", "MEDDIC/MEDDPICC", ["comercial"], "avancado", "Metodologia de qualificação de vendas enterprise", "metodologia", ["qualification"]),
    ("negociacao_comercial", "Negociação Comercial", ["comercial"], "intermediario", "Técnicas de negociação e fechamento", "habilidades", ["negotiation"]),
    ("prospeccao", "Prospecção", ["comercial"], "basico", "Busca ativa de novos clientes potenciais", "processo", ["prospecting"]),
    ("cold_calling", "Cold Calling", ["comercial"], "basico", "Ligações ativas para prospecção", "processo", ["outbound"]),
    ("social_selling", "Social Selling", ["comercial"], "intermediario", "Vendas através de redes sociais", "digital", ["linkedin sales"]),
    ("gestao_pipeline", "Gestão de Pipeline", ["comercial"], "intermediario", "Gerenciamento do funil de vendas", "processo", ["pipeline management"]),
    ("forecast_vendas", "Forecast de Vendas", ["comercial"], "intermediario", "Projeção e previsão de vendas", "analise", ["sales forecast"]),
    ("crm_comercial", "CRM", ["comercial"], "basico", "Sistemas de gestão de relacionamento com cliente", "sistemas", ["customer relationship"]),
    ("salesforce", "Salesforce", ["comercial"], "intermediario", "Plataforma líder de CRM", "sistemas", ["crm"]),
    ("hubspot", "HubSpot", ["comercial", "marketing"], "intermediario", "Plataforma de CRM e inbound", "sistemas", ["crm", "inbound"]),
    ("pipedrive", "Pipedrive", ["comercial"], "basico", "CRM focado em pipeline", "sistemas", ["crm"]),
    ("account_management", "Account Management", ["comercial"], "intermediario", "Gestão de carteira de clientes", "gestao", ["client management"]),
    ("key_account", "Key Account Management", ["comercial"], "avancado", "Gestão de contas estratégicas", "gestao", ["kam"]),
    ("customer_success", "Customer Success", ["comercial", "atendimento"], "intermediario", "Sucesso e retenção de clientes", "pos_venda", ["cs"]),
    ("upselling", "Upselling/Cross-selling", ["comercial"], "intermediario", "Técnicas de venda adicional", "pos_venda", ["expansion"]),
    ("churn", "Gestão de Churn", ["comercial"], "intermediario", "Análise e redução de cancelamentos", "pos_venda", ["retention"]),
    ("vendas_b2b", "Vendas B2B", ["comercial"], "intermediario", "Vendas para empresas", "mercado", ["business to business"]),
    ("vendas_b2c", "Vendas B2C", ["comercial"], "intermediario", "Vendas para consumidor final", "mercado", ["business to consumer"]),
    ("vendas_saas", "Vendas SaaS", ["comercial"], "avancado", "Vendas de software como serviço", "mercado", ["software sales"]),
    ("vendas_enterprise", "Vendas Enterprise", ["comercial"], "avancado", "Vendas para grandes empresas", "mercado", ["enterprise sales"]),
    ("proposta_comercial", "Proposta Comercial", ["comercial"], "basico", "Elaboração de propostas e apresentações", "documentos", ["proposal"]),
    ("rfp", "RFP/RFI/RFQ", ["comercial", "compras"], "intermediario", "Processos de concorrência e licitação", "processo", ["bidding"]),
    ("precificacao", "Precificação", ["comercial"], "intermediario", "Estratégias de pricing", "estrategia", ["pricing"]),
    ("territorio", "Gestão de Território", ["comercial"], "intermediario", "Gestão de região/carteira de vendas", "gestao", ["territory"]),
    ("trade_show", "Feiras e Eventos", ["comercial", "marketing"], "intermediario", "Participação em eventos comerciais", "marketing", ["events"]),
    ("apresentacao_vendas", "Apresentação de Vendas", ["comercial"], "basico", "Técnicas de apresentação e pitch", "habilidades", ["pitch"]),
    ("demonstracao_produto", "Demonstração de Produto", ["comercial"], "intermediario", "Realização de demos e POCs", "processo", ["demo"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _comercial_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- MARKETING (40+ skills) -----
_marketing_skills = [
    ("marketing_digital", "Marketing Digital", ["marketing"], "intermediario", "Estratégias e táticas de marketing online", "digital", ["digital marketing"]),
    ("seo", "SEO", ["marketing"], "intermediario", "Otimização para mecanismos de busca", "digital", ["search engine optimization"]),
    ("sem", "SEM/PPC", ["marketing"], "intermediario", "Marketing de busca paga", "digital", ["paid search"]),
    ("google_ads", "Google Ads", ["marketing"], "intermediario", "Plataforma de anúncios do Google", "midia_paga", ["adwords"]),
    ("meta_ads", "Meta Ads (Facebook/Instagram)", ["marketing"], "intermediario", "Anúncios em redes sociais Meta", "midia_paga", ["facebook ads"]),
    ("linkedin_ads", "LinkedIn Ads", ["marketing"], "intermediario", "Anúncios no LinkedIn", "midia_paga", ["b2b ads"]),
    ("programatica", "Mídia Programática", ["marketing"], "avancado", "Compra automatizada de mídia", "midia_paga", ["programmatic"]),
    ("analytics_mkt", "Google Analytics/GA4", ["marketing"], "intermediario", "Análise de dados de marketing digital", "analytics", ["web analytics"]),
    ("growth_hacking", "Growth Hacking", ["marketing"], "avancado", "Estratégias de crescimento acelerado", "growth", ["growth"]),
    ("inbound_marketing", "Inbound Marketing", ["marketing"], "intermediario", "Marketing de atração e conteúdo", "estrategia", ["content marketing"]),
    ("automacao_marketing", "Automação de Marketing", ["marketing"], "intermediario", "Ferramentas de marketing automation", "ferramentas", ["marketing automation"]),
    ("email_marketing", "Email Marketing", ["marketing"], "basico", "Campanhas de email e newsletters", "canais", ["email campaigns"]),
    ("social_media", "Social Media Marketing", ["marketing"], "basico", "Gestão de redes sociais", "canais", ["social networks"]),
    ("community_management", "Community Management", ["marketing"], "intermediario", "Gestão de comunidades online", "canais", ["community"]),
    ("content_marketing", "Marketing de Conteúdo", ["marketing"], "intermediario", "Estratégia e produção de conteúdo", "conteudo", ["content strategy"]),
    ("copywriting", "Copywriting", ["marketing"], "intermediario", "Redação persuasiva para marketing", "conteudo", ["copy"]),
    ("storytelling", "Storytelling", ["marketing"], "intermediario", "Narrativa para engajamento", "conteudo", ["narrative"]),
    ("branding", "Branding", ["marketing"], "avancado", "Gestão e construção de marca", "marca", ["brand management"]),
    ("posicionamento", "Posicionamento de Marca", ["marketing"], "avancado", "Estratégia de posicionamento", "marca", ["positioning"]),
    ("identidade_visual", "Identidade Visual", ["marketing"], "intermediario", "Gestão de identidade de marca", "marca", ["visual identity"]),
    ("product_marketing", "Product Marketing", ["marketing"], "avancado", "Marketing de produto", "produto", ["pmm"]),
    ("go_to_market", "Go-to-Market", ["marketing"], "avancado", "Estratégias de lançamento de produto", "produto", ["gtm"]),
    ("competitive_intel", "Inteligência Competitiva", ["marketing"], "avancado", "Análise de concorrência", "estrategia", ["competitive analysis"]),
    ("pesquisa_mercado", "Pesquisa de Mercado", ["marketing"], "intermediario", "Estudos e análises de mercado", "pesquisa", ["market research"]),
    ("crm_marketing", "CRM Marketing", ["marketing"], "intermediario", "Gestão de relacionamento via CRM", "ferramentas", ["customer marketing"]),
    ("performance_marketing", "Performance Marketing", ["marketing"], "intermediario", "Marketing orientado a resultados", "performance", ["roi marketing"]),
    ("roi_marketing", "ROI de Marketing", ["marketing"], "intermediario", "Análise de retorno de investimento", "analytics", ["marketing roi"]),
    ("atribuicao", "Modelos de Atribuição", ["marketing"], "avancado", "Atribuição de conversões multicanal", "analytics", ["attribution"]),
    ("ab_testing", "A/B Testing", ["marketing", "tecnologia"], "intermediario", "Testes e experimentação", "analytics", ["experimentation"]),
    ("endomarketing", "Endomarketing", ["marketing", "rh"], "intermediario", "Marketing interno para colaboradores", "interno", ["internal marketing"]),
    ("trade_marketing", "Trade Marketing", ["marketing"], "intermediario", "Marketing para canais de venda", "canais", ["channel marketing"]),
    ("eventos_mkt", "Marketing de Eventos", ["marketing"], "intermediario", "Planejamento e execução de eventos", "canais", ["event marketing"]),
    ("pr_relacoes_publicas", "Relações Públicas/PR", ["marketing"], "intermediario", "Comunicação corporativa e imprensa", "comunicacao", ["public relations"]),
    ("assessoria_imprensa", "Assessoria de Imprensa", ["marketing"], "intermediario", "Relacionamento com mídia", "comunicacao", ["press"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _marketing_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- JURÍDICO (35+ skills) -----
_juridico_skills = [
    ("contratos", "Direito Contratual", ["juridico"], "intermediario", "Elaboração e análise de contratos", "contratos", ["contracts"]),
    ("revisao_contratos", "Revisão de Contratos", ["juridico"], "basico", "Análise e parecer sobre contratos", "contratos", ["contract review"]),
    ("negociacao_juridica", "Negociação de Contratos", ["juridico"], "intermediario", "Negociação de termos contratuais", "contratos", ["negotiation"]),
    ("direito_societario", "Direito Societário", ["juridico"], "avancado", "Operações societárias e governança", "societario", ["corporate law"]),
    ("ma_juridico", "M&A (Jurídico)", ["juridico"], "avancado", "Fusões e aquisições do ponto de vista jurídico", "societario", ["mergers"]),
    ("due_diligence_juridica", "Due Diligence Legal", ["juridico"], "avancado", "Auditoria legal em transações", "societario", ["legal audit"]),
    ("governanca_corporativa", "Governança Corporativa", ["juridico", "compliance"], "avancado", "Estruturas e práticas de governança", "societario", ["governance"]),
    ("direito_trabalhista", "Direito Trabalhista", ["juridico", "dp"], "intermediario", "Legislação e processos trabalhistas", "trabalhista", ["labor law"]),
    ("contencioso_trabalhista", "Contencioso Trabalhista", ["juridico"], "intermediario", "Processos judiciais trabalhistas", "trabalhista", ["labor litigation"]),
    ("consultivo_trabalhista", "Consultivo Trabalhista", ["juridico"], "intermediario", "Consultoria preventiva em questões trabalhistas", "trabalhista", ["labor consulting"]),
    ("direito_tributario_jur", "Direito Tributário", ["juridico", "fiscal"], "avancado", "Questões jurídicas tributárias", "tributario", ["tax law"]),
    ("contencioso_tributario_jur", "Contencioso Tributário (Jurídico)", ["juridico"], "avancado", "Processos tributários", "tributario", ["tax litigation"]),
    ("direito_civil", "Direito Civil", ["juridico"], "intermediario", "Questões civis e obrigações", "civil", ["civil law"]),
    ("direito_consumidor", "Direito do Consumidor", ["juridico"], "intermediario", "CDC e relações de consumo", "civil", ["consumer law"]),
    ("direito_imobiliario", "Direito Imobiliário", ["juridico"], "intermediario", "Questões imobiliárias e locação", "imobiliario", ["real estate law"]),
    ("propriedade_intelectual", "Propriedade Intelectual", ["juridico"], "avancado", "Marcas, patentes e direitos autorais", "pi", ["intellectual property"]),
    ("lgpd_juridico", "LGPD/Proteção de Dados", ["juridico", "compliance"], "intermediario", "Lei Geral de Proteção de Dados", "dados", ["data protection"]),
    ("direito_digital", "Direito Digital", ["juridico"], "intermediario", "Questões jurídicas de tecnologia", "digital", ["tech law"]),
    ("direito_regulatorio", "Direito Regulatório", ["juridico", "compliance"], "avancado", "Regulação de setores específicos", "regulatorio", ["regulatory law"]),
    ("direito_concorrencial", "Direito Concorrencial", ["juridico"], "avancado", "Antitruste e defesa da concorrência", "concorrencia", ["antitrust"]),
    ("direito_internacional", "Direito Internacional", ["juridico"], "avancado", "Questões jurídicas internacionais", "internacional", ["international law"]),
    ("comercio_exterior_jur", "Comércio Exterior (Jurídico)", ["juridico", "logistica"], "avancado", "Questões legais de importação/exportação", "internacional", ["trade law"]),
    ("contencioso_civel", "Contencioso Cível", ["juridico"], "intermediario", "Processos judiciais cíveis", "contencioso", ["civil litigation"]),
    ("contencioso_estrategico", "Contencioso Estratégico", ["juridico"], "avancado", "Gestão de grandes causas", "contencioso", ["strategic litigation"]),
    ("arbitragem", "Arbitragem", ["juridico"], "avancado", "Resolução de disputas por arbitragem", "resolucao", ["arbitration"]),
    ("mediacao", "Mediação", ["juridico"], "intermediario", "Resolução alternativa de conflitos", "resolucao", ["mediation"]),
    ("compliance_juridico", "Compliance (Jurídico)", ["juridico", "compliance"], "intermediario", "Conformidade legal e regulatória", "compliance", ["legal compliance"]),
    ("anticorrupcao", "Lei Anticorrupção", ["juridico", "compliance"], "avancado", "Lei 12.846 e programas de integridade", "compliance", ["anti-bribery"]),
    ("investigacoes", "Investigações Internas", ["juridico", "compliance"], "avancado", "Condução de investigações corporativas", "compliance", ["investigations"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _juridico_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- COMPLIANCE/GRC (30+ skills) -----
_compliance_skills = [
    ("programa_compliance", "Programa de Compliance", ["compliance"], "avancado", "Estruturação e gestão de programa de compliance", "estrutura", ["compliance program"]),
    ("matriz_riscos", "Matriz de Riscos", ["compliance"], "intermediario", "Identificação e avaliação de riscos", "riscos", ["risk matrix"]),
    ("gestao_riscos", "Gestão de Riscos", ["compliance", "financeiro"], "avancado", "Identificação, avaliação e mitigação de riscos", "riscos", ["risk management"]),
    ("erm", "ERM (Enterprise Risk Management)", ["compliance"], "avancado", "Gestão integrada de riscos corporativos", "riscos", ["enterprise risk"]),
    ("controles_internos", "Controles Internos", ["compliance", "contabil"], "intermediario", "Desenho e avaliação de controles", "controles", ["internal controls"]),
    ("sox_compliance", "SOX Compliance", ["compliance"], "avancado", "Conformidade com Sarbanes-Oxley", "controles", ["sarbanes-oxley"]),
    ("coso", "Framework COSO", ["compliance"], "avancado", "Modelo de controles internos", "framework", ["coso framework"]),
    ("auditoria_interna", "Auditoria Interna", ["compliance"], "avancado", "Realização de auditorias internas", "auditoria", ["internal audit"]),
    ("auditoria_processos", "Auditoria de Processos", ["compliance"], "intermediario", "Revisão de eficácia de processos", "auditoria", ["process audit"]),
    ("kyc", "KYC (Know Your Customer)", ["compliance"], "intermediario", "Identificação e verificação de clientes", "prevencao", ["customer verification"]),
    ("pld", "PLD/AML (Prevenção à Lavagem)", ["compliance"], "avancado", "Prevenção à lavagem de dinheiro", "prevencao", ["anti-money laundering"]),
    ("due_diligence_compliance", "Due Diligence de Terceiros", ["compliance"], "intermediario", "Avaliação de fornecedores e parceiros", "terceiros", ["third party"]),
    ("codigo_conduta", "Código de Conduta", ["compliance"], "intermediario", "Elaboração e disseminação de código de ética", "etica", ["code of conduct"]),
    ("canal_etica", "Canal de Ética/Denúncias", ["compliance"], "intermediario", "Gestão de canal de denúncias", "etica", ["hotline"]),
    ("investigacoes_compliance", "Investigações de Compliance", ["compliance"], "avancado", "Condução de investigações internas", "etica", ["investigations"]),
    ("treinamento_compliance", "Treinamentos de Compliance", ["compliance"], "basico", "Programa de conscientização", "educacao", ["training"]),
    ("politicas_corporativas", "Políticas Corporativas", ["compliance"], "intermediario", "Elaboração e gestão de políticas", "documentacao", ["corporate policies"]),
    ("regulatorio_compliance", "Regulatório", ["compliance"], "avancado", "Conformidade com regulações setoriais", "regulatorio", ["regulatory"]),
    ("bacen", "Regulação BACEN", ["compliance", "financeiro"], "avancado", "Normas do Banco Central", "regulatorio", ["central bank"]),
    ("cvm", "Regulação CVM", ["compliance", "financeiro"], "avancado", "Normas da Comissão de Valores Mobiliários", "regulatorio", ["securities"]),
    ("susep", "Regulação SUSEP", ["compliance"], "avancado", "Normas de seguros e previdência", "regulatorio", ["insurance"]),
    ("anp", "Regulação ANP", ["compliance"], "avancado", "Normas do setor de petróleo e gás", "regulatorio", ["oil and gas"]),
    ("anvisa", "Regulação ANVISA", ["compliance", "qualidade"], "avancado", "Normas sanitárias", "regulatorio", ["health"]),
    ("iso_27001", "ISO 27001", ["compliance", "tecnologia"], "avancado", "Gestão de segurança da informação", "certificacoes", ["information security"]),
    ("iso_9001", "ISO 9001", ["compliance", "qualidade"], "intermediario", "Gestão da qualidade", "certificacoes", ["quality"]),
    ("iso_37001", "ISO 37001", ["compliance"], "avancado", "Sistema de gestão antissuborno", "certificacoes", ["anti-bribery"]),
    ("reporting_compliance", "Reporting de Compliance", ["compliance"], "intermediario", "Relatórios e indicadores de compliance", "gestao", ["reporting"]),
    ("monitoramento_compliance", "Monitoramento de Compliance", ["compliance"], "intermediario", "Monitoramento contínuo de riscos e controles", "gestao", ["monitoring"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _compliance_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- OPERAÇÕES (25+ skills) -----
_operacoes_skills = [
    ("gestao_processos", "Gestão de Processos", ["operacoes"], "intermediario", "Mapeamento e melhoria de processos", "processos", ["bpm"]),
    ("bpm", "BPM (Business Process Management)", ["operacoes"], "avancado", "Metodologia de gestão de processos", "processos", ["process management"]),
    ("lean", "Lean Manufacturing/Office", ["operacoes", "producao"], "intermediario", "Metodologia lean para eficiência", "melhoria", ["lean"]),
    ("six_sigma", "Six Sigma", ["operacoes", "qualidade"], "avancado", "Metodologia de melhoria de qualidade", "melhoria", ["dmaic"]),
    ("lean_six_sigma", "Lean Six Sigma", ["operacoes"], "avancado", "Combinação de Lean e Six Sigma", "melhoria", ["lss"]),
    ("kaizen", "Kaizen", ["operacoes", "producao"], "intermediario", "Melhoria contínua incremental", "melhoria", ["continuous improvement"]),
    ("5s", "5S", ["operacoes", "producao"], "basico", "Metodologia de organização do ambiente", "melhoria", ["workplace organization"]),
    ("pdca", "PDCA", ["operacoes"], "basico", "Ciclo de melhoria contínua", "melhoria", ["plan do check act"]),
    ("kpis_operacionais", "KPIs Operacionais", ["operacoes"], "intermediario", "Definição e gestão de indicadores", "gestao", ["metrics"]),
    ("dashboard_ops", "Dashboards Operacionais", ["operacoes"], "intermediario", "Visualização de performance operacional", "gestao", ["visualization"]),
    ("project_management", "Gestão de Projetos", ["operacoes"], "intermediario", "Planejamento e execução de projetos", "projetos", ["pmo"]),
    ("pmo", "PMO (Project Management Office)", ["operacoes"], "avancado", "Escritório de gestão de projetos", "projetos", ["project office"]),
    ("pmp", "Metodologia PMP", ["operacoes"], "avancado", "Certificação e práticas PMI", "projetos", ["pmi"]),
    ("agile_ops", "Metodologias Ágeis", ["operacoes", "tecnologia"], "intermediario", "Scrum, Kanban aplicados a operações", "metodologias", ["agile"]),
    ("change_management", "Gestão de Mudanças", ["operacoes", "rh"], "avancado", "Metodologias de change management", "transformacao", ["prosci"]),
    ("automacao_processos", "Automação de Processos", ["operacoes"], "intermediario", "RPA e automação operacional", "automacao", ["rpa"]),
    ("erp", "Sistemas ERP", ["operacoes"], "intermediario", "Sistemas integrados de gestão", "sistemas", ["enterprise resource planning"]),
    ("sap_geral", "SAP (Geral)", ["operacoes"], "intermediario", "Sistema SAP ERP", "sistemas", ["sap"]),
    ("oracle_erp", "Oracle ERP", ["operacoes"], "intermediario", "Suite ERP Oracle", "sistemas", ["oracle"]),
    ("totvs_geral", "TOTVS (Geral)", ["operacoes"], "intermediario", "ERP TOTVS", "sistemas", ["totvs"]),
    ("capacity_planning", "Planejamento de Capacidade", ["operacoes"], "avancado", "Planejamento de recursos e capacidade", "planejamento", ["capacity"]),
    ("sla", "Gestão de SLAs", ["operacoes"], "intermediario", "Acordos de nível de serviço", "servico", ["service level"]),
    ("outsourcing", "Gestão de Outsourcing", ["operacoes"], "intermediario", "Gestão de serviços terceirizados", "terceiros", ["bpo"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _operacoes_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- LOGÍSTICA/SUPPLY CHAIN (30+ skills) -----
_logistica_skills = [
    ("supply_chain_management", "Supply Chain Management", ["logistica"], "avancado", "Gestão integrada da cadeia de suprimentos", "estrategia", ["scm"]),
    ("sop", "S&OP (Sales & Operations Planning)", ["logistica"], "avancado", "Planejamento integrado de vendas e operações", "planejamento", ["planning"]),
    ("demand_planning", "Demand Planning", ["logistica"], "intermediario", "Planejamento e previsão de demanda", "planejamento", ["forecast"]),
    ("mrp", "MRP (Material Requirements Planning)", ["logistica", "producao"], "intermediario", "Planejamento de necessidades de materiais", "planejamento", ["materials"]),
    ("gestao_estoques", "Gestão de Estoques", ["logistica"], "intermediario", "Controle e otimização de inventário", "estoque", ["inventory management"]),
    ("inventario", "Inventário", ["logistica"], "basico", "Contagem e controle físico de estoque", "estoque", ["stock count"]),
    ("armazenagem", "Armazenagem", ["logistica"], "intermediario", "Gestão de operações de armazém", "armazem", ["warehousing"]),
    ("wms", "WMS (Warehouse Management System)", ["logistica"], "intermediario", "Sistemas de gestão de armazém", "sistemas", ["warehouse system"]),
    ("picking_packing", "Picking e Packing", ["logistica"], "basico", "Processos de separação e embalagem", "armazem", ["order fulfillment"]),
    ("cross_docking", "Cross Docking", ["logistica"], "intermediario", "Operação de transbordo direto", "armazem", ["distribution"]),
    ("transporte", "Gestão de Transporte", ["logistica"], "intermediario", "Planejamento e operação de transportes", "transporte", ["transportation"]),
    ("tms", "TMS (Transportation Management System)", ["logistica"], "intermediario", "Sistemas de gestão de transporte", "sistemas", ["transport system"]),
    ("roteirizacao", "Roteirização", ["logistica"], "intermediario", "Planejamento de rotas de entrega", "transporte", ["routing"]),
    ("frete", "Gestão de Frete", ["logistica"], "intermediario", "Negociação e controle de fretes", "transporte", ["freight"]),
    ("last_mile", "Last Mile Delivery", ["logistica"], "intermediario", "Logística de última milha", "transporte", ["delivery"]),
    ("comercio_exterior", "Comércio Exterior", ["logistica"], "avancado", "Operações de importação e exportação", "comex", ["foreign trade"]),
    ("importacao", "Importação", ["logistica"], "intermediario", "Processos de importação", "comex", ["import"]),
    ("exportacao", "Exportação", ["logistica"], "intermediario", "Processos de exportação", "comex", ["export"]),
    ("despacho_aduaneiro", "Despacho Aduaneiro", ["logistica"], "intermediario", "Processos de liberação aduaneira", "comex", ["customs clearance"]),
    ("incoterms", "Incoterms", ["logistica", "compras"], "intermediario", "Termos internacionais de comércio", "comex", ["trade terms"]),
    ("gestao_fornecedores", "Gestão de Fornecedores", ["logistica", "compras"], "intermediario", "Relacionamento e performance de fornecedores", "fornecedores", ["supplier management"]),
    ("logistica_reversa", "Logística Reversa", ["logistica"], "intermediario", "Processos de devolução e descarte", "sustentabilidade", ["reverse logistics"]),
    ("sustentabilidade_scm", "Sustentabilidade na Cadeia", ["logistica"], "avancado", "Práticas sustentáveis em supply chain", "sustentabilidade", ["green logistics"]),
    ("indicadores_logistica", "KPIs de Logística", ["logistica"], "intermediario", "Indicadores de desempenho logístico", "gestao", ["logistics kpis"]),
    ("otif", "OTIF", ["logistica"], "basico", "On Time In Full - indicador de entrega", "gestao", ["on time in full"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _logistica_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- COMPRAS/PROCUREMENT (25+ skills) -----
_compras_skills = [
    ("strategic_sourcing", "Strategic Sourcing", ["compras"], "avancado", "Sourcing estratégico de fornecedores", "estrategia", ["sourcing"]),
    ("category_management", "Category Management", ["compras"], "avancado", "Gestão por categoria de compras", "estrategia", ["categories"]),
    ("negociacao_compras", "Negociação com Fornecedores", ["compras"], "intermediario", "Técnicas de negociação em compras", "negociacao", ["supplier negotiation"]),
    ("tcl", "TCO (Total Cost of Ownership)", ["compras"], "avancado", "Análise de custo total de propriedade", "analise", ["total cost"]),
    ("vendor_management", "Vendor Management", ["compras"], "intermediario", "Gestão de relacionamento com fornecedores", "gestao", ["supplier relationship"]),
    ("homologacao", "Homologação de Fornecedores", ["compras"], "intermediario", "Qualificação e aprovação de fornecedores", "qualificacao", ["vendor qualification"]),
    ("avaliacao_fornecedores", "Avaliação de Fornecedores", ["compras"], "intermediario", "Métricas e performance de fornecedores", "qualificacao", ["vendor assessment"]),
    ("contratos_compras", "Gestão de Contratos", ["compras"], "intermediario", "Elaboração e gestão de contratos de compras", "contratos", ["contract management"]),
    ("licitacoes", "Licitações", ["compras"], "intermediario", "Processos de licitação pública", "processo", ["bidding"]),
    ("cotacao", "Processo de Cotação", ["compras"], "basico", "Solicitação e análise de cotações", "processo", ["quotation"]),
    ("requisicao_compras", "Requisição de Compras", ["compras"], "basico", "Processo de requisição e aprovação", "processo", ["purchase requisition"]),
    ("pedido_compra", "Pedido de Compra", ["compras"], "basico", "Emissão e gestão de pedidos", "processo", ["purchase order"]),
    ("compras_indiretas", "Compras Indiretas", ["compras"], "intermediario", "Compras não ligadas à produção", "categorias", ["indirect procurement"]),
    ("compras_diretas", "Compras Diretas", ["compras"], "intermediario", "Compras de matéria-prima e produção", "categorias", ["direct procurement"]),
    ("compras_servicos", "Compras de Serviços", ["compras"], "intermediario", "Contratação de serviços", "categorias", ["service procurement"]),
    ("capex", "Compras CAPEX", ["compras"], "avancado", "Compras de investimento", "categorias", ["capital expenditure"]),
    ("e_procurement", "e-Procurement", ["compras"], "intermediario", "Sistemas eletrônicos de compras", "sistemas", ["electronic procurement"]),
    ("ariba", "SAP Ariba", ["compras"], "intermediario", "Plataforma de compras SAP", "sistemas", ["sap ariba"]),
    ("coupa", "Coupa", ["compras"], "intermediario", "Plataforma de spend management", "sistemas", ["spend management"]),
    ("saving", "Saving/Redução de Custos", ["compras"], "intermediario", "Identificação de oportunidades de economia", "resultados", ["cost reduction"]),
    ("spend_analysis", "Spend Analysis", ["compras"], "intermediario", "Análise de gastos corporativos", "analise", ["spending"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _compras_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- QUALIDADE (25+ skills) -----
_qualidade_skills = [
    ("gestao_qualidade", "Gestão da Qualidade", ["qualidade"], "intermediario", "Sistema de gestão da qualidade", "gestao", ["quality management"]),
    ("iso_9001_impl", "Implementação ISO 9001", ["qualidade"], "avancado", "Implementação de sistema de gestão da qualidade", "certificacao", ["quality system"]),
    ("auditoria_qualidade", "Auditoria de Qualidade", ["qualidade"], "intermediario", "Condução de auditorias internas e externas", "auditoria", ["quality audit"]),
    ("auditor_lider", "Auditor Líder", ["qualidade"], "avancado", "Liderança de auditorias de certificação", "auditoria", ["lead auditor"]),
    ("controle_qualidade", "Controle de Qualidade", ["qualidade"], "intermediario", "Inspeção e controle de produtos/processos", "operacional", ["quality control"]),
    ("cep", "CEP (Controle Estatístico de Processo)", ["qualidade", "producao"], "avancado", "Controle estatístico de processos", "estatistica", ["spc"]),
    ("msa", "MSA (Análise de Sistema de Medição)", ["qualidade"], "avancado", "Análise de sistemas de medição", "estatistica", ["measurement"]),
    ("fmea", "FMEA", ["qualidade", "engenharia"], "avancado", "Análise de modos de falha e efeitos", "metodologia", ["failure mode"]),
    ("masp", "MASP", ["qualidade"], "intermediario", "Método de análise e solução de problemas", "metodologia", ["problem solving"]),
    ("a3", "A3 Problem Solving", ["qualidade"], "intermediario", "Metodologia A3 de resolução de problemas", "metodologia", ["toyota"]),
    ("fishbone", "Diagrama de Ishikawa", ["qualidade"], "basico", "Análise de causa e efeito", "ferramentas", ["fishbone"]),
    ("pareto", "Análise de Pareto", ["qualidade"], "basico", "Priorização de problemas", "ferramentas", ["80/20"]),
    ("capabilidade", "Análise de Capabilidade", ["qualidade"], "avancado", "Cp, Cpk e análise de processo", "estatistica", ["capability"]),
    ("nao_conformidade", "Gestão de Não Conformidades", ["qualidade"], "intermediario", "Tratamento de desvios e não conformidades", "gestao", ["nc"]),
    ("acoes_corretivas", "Ações Corretivas/Preventivas", ["qualidade"], "intermediario", "CAPA - Corrective and Preventive Actions", "gestao", ["capa"]),
    ("bpf", "BPF (Boas Práticas de Fabricação)", ["qualidade"], "intermediario", "Normas de boas práticas para produção", "regulatorio", ["gmp"]),
    ("haccp", "HACCP", ["qualidade"], "avancado", "Análise de perigos e pontos críticos de controle", "regulatorio", ["food safety"]),
    ("ppap", "PPAP", ["qualidade", "engenharia"], "avancado", "Processo de aprovação de peças de produção", "automotivo", ["production part"]),
    ("apqp", "APQP", ["qualidade", "engenharia"], "avancado", "Planejamento avançado da qualidade do produto", "automotivo", ["advanced quality"]),
    ("metrologia", "Metrologia", ["qualidade"], "intermediario", "Ciência das medições", "medicao", ["measurement"]),
    ("calibracao", "Calibração", ["qualidade"], "intermediario", "Calibração de instrumentos de medição", "medicao", ["calibration"]),
    ("indicadores_qualidade", "Indicadores de Qualidade", ["qualidade"], "intermediario", "KPIs de qualidade (PPM, DPU, etc)", "gestao", ["quality kpis"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _qualidade_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- ENGENHARIA (30+ skills) -----
_engenharia_skills = [
    ("engenharia_mecanica", "Engenharia Mecânica", ["engenharia"], "intermediario", "Projeto e análise de sistemas mecânicos", "mecanica", ["mechanical"]),
    ("engenharia_eletrica", "Engenharia Elétrica", ["engenharia"], "intermediario", "Projetos elétricos e eletrônicos", "eletrica", ["electrical"]),
    ("engenharia_civil", "Engenharia Civil", ["engenharia"], "intermediario", "Projetos de construção civil", "civil", ["civil engineering"]),
    ("engenharia_quimica", "Engenharia Química", ["engenharia"], "intermediario", "Processos químicos e industriais", "quimica", ["chemical"]),
    ("engenharia_producao", "Engenharia de Produção", ["engenharia", "producao"], "intermediario", "Otimização de sistemas produtivos", "producao", ["industrial engineering"]),
    ("automacao_industrial", "Automação Industrial", ["engenharia", "producao"], "avancado", "Sistemas automatizados de produção", "automacao", ["industrial automation"]),
    ("plc", "PLC (Controlador Lógico Programável)", ["engenharia"], "intermediario", "Programação de CLPs", "automacao", ["programmable logic"]),
    ("scada", "SCADA", ["engenharia"], "intermediario", "Sistemas de supervisão e controle", "automacao", ["supervisory control"]),
    ("cad", "CAD (Desenho Assistido por Computador)", ["engenharia"], "intermediario", "Ferramentas de desenho técnico", "projeto", ["computer aided design"]),
    ("autocad", "AutoCAD", ["engenharia"], "intermediario", "Software de desenho técnico 2D/3D", "projeto", ["autodesk"]),
    ("solidworks", "SolidWorks", ["engenharia"], "intermediario", "Software de modelagem 3D", "projeto", ["3d modeling"]),
    ("catia", "CATIA", ["engenharia"], "avancado", "Software de projeto para indústria aeronáutica/automotiva", "projeto", ["dassault"]),
    ("ansys", "ANSYS", ["engenharia"], "avancado", "Software de simulação e análise de elementos finitos", "simulacao", ["fem"]),
    ("manutenção_industrial", "Manutenção Industrial", ["engenharia", "producao"], "intermediario", "Gestão de manutenção de equipamentos", "manutencao", ["maintenance"]),
    ("pcm", "PCM (Planejamento e Controle de Manutenção)", ["engenharia"], "intermediario", "Planejamento de manutenção", "manutencao", ["maintenance planning"]),
    ("tpm", "TPM (Manutenção Produtiva Total)", ["engenharia", "producao"], "avancado", "Metodologia de manutenção autônoma", "manutencao", ["total productive"]),
    ("rcm", "RCM (Manutenção Centrada em Confiabilidade)", ["engenharia"], "avancado", "Metodologia de confiabilidade", "manutencao", ["reliability"]),
    ("projeto_produto", "Projeto de Produto", ["engenharia", "pd"], "intermediario", "Desenvolvimento de novos produtos", "desenvolvimento", ["product design"]),
    ("prototipagem", "Prototipagem", ["engenharia", "pd"], "intermediario", "Criação de protótipos", "desenvolvimento", ["prototyping"]),
    ("cronograma_obra", "Cronograma de Obras", ["engenharia"], "intermediario", "Planejamento de obras e construções", "civil", ["construction schedule"]),
    ("orcamento_obras", "Orçamento de Obras", ["engenharia"], "intermediario", "Estimativa de custos de construção", "civil", ["construction budget"]),
    ("nr_10", "NR-10", ["engenharia"], "basico", "Segurança em instalações elétricas", "seguranca", ["electrical safety"]),
    ("nr_12", "NR-12", ["engenharia"], "intermediario", "Segurança em máquinas e equipamentos", "seguranca", ["machine safety"]),
    ("eficiencia_energetica", "Eficiência Energética", ["engenharia"], "intermediario", "Projetos de redução de consumo energético", "sustentabilidade", ["energy efficiency"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _engenharia_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- PRODUÇÃO/MANUFATURA (25+ skills) -----
_producao_skills = [
    ("gestao_producao", "Gestão de Produção", ["producao"], "intermediario", "Planejamento e controle da produção", "gestao", ["production management"]),
    ("pcp", "PCP (Planejamento e Controle da Produção)", ["producao"], "intermediario", "Planejamento de produção", "planejamento", ["production planning"]),
    ("programacao_producao", "Programação de Produção", ["producao"], "intermediario", "Sequenciamento de ordens de produção", "planejamento", ["scheduling"]),
    ("setup_reducao", "Redução de Setup (SMED)", ["producao"], "avancado", "Metodologia de troca rápida de ferramenta", "lean", ["setup reduction"]),
    ("oee", "OEE (Overall Equipment Effectiveness)", ["producao"], "intermediario", "Indicador de eficiência de equipamento", "indicadores", ["equipment effectiveness"]),
    ("balanceamento_linha", "Balanceamento de Linha", ["producao"], "intermediario", "Distribuição de trabalho em linhas de produção", "otimizacao", ["line balancing"]),
    ("layout_fabrica", "Layout de Fábrica", ["producao", "engenharia"], "intermediario", "Projeto de layout industrial", "otimizacao", ["factory layout"]),
    ("cronanalise", "Cronoánalise", ["producao"], "intermediario", "Estudo de tempos e movimentos", "otimizacao", ["time study"]),
    ("mtm", "MTM (Methods-Time Measurement)", ["producao"], "avancado", "Sistema de tempos pré-determinados", "otimizacao", ["methods time"]),
    ("kanban_producao", "Kanban (Produção)", ["producao"], "intermediario", "Sistema puxado de controle de produção", "lean", ["pull system"]),
    ("jit", "Just in Time", ["producao"], "avancado", "Sistema de produção just in time", "lean", ["jit"]),
    ("heijunka", "Heijunka (Nivelamento)", ["producao"], "avancado", "Nivelamento de produção", "lean", ["leveling"]),
    ("andon", "Andon", ["producao"], "basico", "Sistema visual de status de produção", "lean", ["visual management"]),
    ("poka_yoke", "Poka-Yoke", ["producao", "qualidade"], "intermediario", "Dispositivos à prova de erro", "lean", ["error proofing"]),
    ("gemba", "Gemba", ["producao"], "basico", "Gestão no local de trabalho", "lean", ["workplace management"]),
    ("supervisor_producao", "Supervisão de Produção", ["producao"], "intermediario", "Gestão de equipes de produção", "gestao", ["production supervision"]),
    ("operacao_maquinas", "Operação de Máquinas", ["producao"], "basico", "Operação de equipamentos industriais", "operacional", ["machine operation"]),
    ("seguranca_fabrica", "Segurança Industrial", ["producao", "qualidade"], "intermediario", "Prevenção de acidentes em fábrica", "seguranca", ["industrial safety"]),
    ("ergonomia", "Ergonomia", ["producao", "qualidade"], "intermediario", "Estudo de postos de trabalho ergonômicos", "seguranca", ["ergonomics"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _producao_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- P&D/INOVAÇÃO (20+ skills) -----
_pd_skills = [
    ("pesquisa_desenvolvimento", "Pesquisa e Desenvolvimento", ["pd"], "avancado", "Condução de projetos de P&D", "pesquisa", ["r&d"]),
    ("inovacao_produtos", "Inovação de Produtos", ["pd"], "avancado", "Desenvolvimento de novos produtos", "inovacao", ["product innovation"]),
    ("design_thinking", "Design Thinking", ["pd", "marketing"], "intermediario", "Metodologia de inovação centrada no usuário", "metodologia", ["innovation method"]),
    ("stage_gate", "Stage Gate", ["pd"], "avancado", "Metodologia de desenvolvimento de produtos", "metodologia", ["product development"]),
    ("agile_pd", "Agile para P&D", ["pd"], "intermediario", "Metodologias ágeis em desenvolvimento", "metodologia", ["agile development"]),
    ("mvp", "MVP (Minimum Viable Product)", ["pd", "tecnologia"], "intermediario", "Desenvolvimento de produto mínimo viável", "metodologia", ["lean startup"]),
    ("prototipagem_rapida", "Prototipagem Rápida", ["pd", "engenharia"], "intermediario", "Técnicas de prototipagem rápida", "desenvolvimento", ["rapid prototyping"]),
    ("impressao_3d", "Impressão 3D", ["pd", "engenharia"], "intermediario", "Manufatura aditiva para prototipagem", "tecnologia", ["additive manufacturing"]),
    ("gestao_pi", "Gestão de Propriedade Intelectual", ["pd", "juridico"], "avancado", "Gestão de patentes e PI", "estrategico", ["ip management"]),
    ("patentes", "Patentes", ["pd", "juridico"], "avancado", "Registro e gestão de patentes", "pi", ["patents"]),
    ("trl", "TRL (Technology Readiness Level)", ["pd"], "avancado", "Avaliação de maturidade tecnológica", "avaliacao", ["technology level"]),
    ("open_innovation", "Open Innovation", ["pd"], "avancado", "Inovação aberta com parceiros externos", "estrategico", ["collaborative innovation"]),
    ("parcerias_academicas", "Parcerias Acadêmicas", ["pd"], "intermediario", "Colaboração com universidades e institutos", "parcerias", ["academia"]),
    ("startups_pd", "Relacionamento com Startups", ["pd"], "intermediario", "Corporate venture e parcerias", "parcerias", ["startups"]),
    ("grants_incentivos", "Grants e Incentivos (Lei do Bem)", ["pd", "fiscal"], "avancado", "Captação de incentivos fiscais para P&D", "financiamento", ["incentives"]),
    ("laboratorio", "Gestão de Laboratório", ["pd"], "intermediario", "Operação e gestão de laboratórios", "operacional", ["lab management"]),
    ("ensaios_testes", "Ensaios e Testes", ["pd", "qualidade"], "intermediario", "Condução de ensaios e testes de produto", "operacional", ["testing"]),
    ("regulatorio_pd", "Regulatório de Produtos", ["pd", "compliance"], "avancado", "Aprovações regulatórias de novos produtos", "regulatorio", ["product approval"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _pd_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- ATENDIMENTO/CUSTOMER SUCCESS (25+ skills) -----
_atendimento_skills = [
    ("atendimento_cliente", "Atendimento ao Cliente", ["atendimento"], "basico", "Atendimento e resolução de demandas de clientes", "operacional", ["customer service"]),
    ("customer_success_metodologia", "Metodologia Customer Success", ["atendimento"], "avancado", "Frameworks de sucesso do cliente", "estrategia", ["cs methodology"]),
    ("onboarding_cliente", "Onboarding de Clientes", ["atendimento"], "intermediario", "Implementação e ativação de novos clientes", "jornada", ["customer onboarding"]),
    ("health_score", "Health Score", ["atendimento"], "avancado", "Métricas de saúde do cliente", "analytics", ["customer health"]),
    ("nps", "NPS (Net Promoter Score)", ["atendimento", "marketing"], "intermediario", "Medição de satisfação e lealdade", "metricas", ["loyalty"]),
    ("csat", "CSAT (Customer Satisfaction)", ["atendimento"], "basico", "Medição de satisfação do cliente", "metricas", ["satisfaction"]),
    ("ces", "CES (Customer Effort Score)", ["atendimento"], "intermediario", "Medição de esforço do cliente", "metricas", ["effort"]),
    ("gestao_chamados", "Gestão de Chamados/Tickets", ["atendimento"], "basico", "Atendimento de solicitações via sistema", "operacional", ["ticketing"]),
    ("zendesk", "Zendesk", ["atendimento"], "intermediario", "Plataforma de atendimento ao cliente", "sistemas", ["help desk"]),
    ("intercom", "Intercom", ["atendimento"], "intermediario", "Plataforma de comunicação com clientes", "sistemas", ["messaging"]),
    ("gainsight", "Gainsight", ["atendimento"], "avancado", "Plataforma de customer success", "sistemas", ["cs platform"]),
    ("totango", "Totango", ["atendimento"], "intermediario", "Plataforma de customer success", "sistemas", ["cs platform"]),
    ("sac", "SAC (Serviço de Atendimento ao Consumidor)", ["atendimento"], "basico", "Canais de atendimento ao consumidor", "canais", ["consumer service"]),
    ("call_center", "Operações de Call Center", ["atendimento"], "intermediario", "Gestão de operações de call center", "operacional", ["contact center"]),
    ("omnichannel", "Atendimento Omnichannel", ["atendimento"], "intermediario", "Integração de múltiplos canais de atendimento", "canais", ["multichannel"]),
    ("chatbot", "Chatbots e Automação", ["atendimento", "tecnologia"], "intermediario", "Automação de atendimento via chat", "automacao", ["automation"]),
    ("gestao_reclamacoes", "Gestão de Reclamações", ["atendimento"], "intermediario", "Tratamento e resolução de reclamações", "operacional", ["complaints"]),
    ("reclame_aqui", "Reclame Aqui", ["atendimento"], "basico", "Gestão de reputação em plataformas", "canais", ["reputation"]),
    ("retention", "Retenção de Clientes", ["atendimento"], "avancado", "Estratégias de retenção", "estrategia", ["retention"]),
    ("expansion", "Expansão de Receita", ["atendimento", "comercial"], "avancado", "Upsell e cross-sell em clientes existentes", "estrategia", ["growth"]),
    ("playbooks_cs", "Playbooks de CS", ["atendimento"], "intermediario", "Criação de playbooks de sucesso do cliente", "processos", ["playbooks"]),
    ("qbr", "QBR (Quarterly Business Review)", ["atendimento"], "avancado", "Revisões trimestrais de negócios", "relacionamento", ["business review"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _atendimento_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- ADMINISTRATIVO (15+ skills) -----
_admin_skills = [
    ("rotinas_administrativas", "Rotinas Administrativas", ["administrativo"], "basico", "Execução de atividades administrativas gerais", "operacional", ["admin tasks"]),
    ("gestao_documentos", "Gestão de Documentos", ["administrativo"], "basico", "Organização e controle de documentos", "documentos", ["document management"]),
    ("arquivo", "Arquivamento", ["administrativo"], "basico", "Organização física e digital de arquivos", "documentos", ["filing"]),
    ("secretariado", "Secretariado Executivo", ["administrativo"], "intermediario", "Suporte executivo a diretores", "executivo", ["executive assistant"]),
    ("agenda", "Gestão de Agenda", ["administrativo"], "basico", "Organização de agendas e compromissos", "executivo", ["scheduling"]),
    ("viagens", "Gestão de Viagens", ["administrativo"], "basico", "Organização de viagens corporativas", "executivo", ["travel"]),
    ("eventos_corp", "Organização de Eventos", ["administrativo", "marketing"], "intermediario", "Planejamento de eventos corporativos", "eventos", ["corporate events"]),
    ("correspondencia", "Gestão de Correspondência", ["administrativo"], "basico", "Controle de correspondências", "documentos", ["mail"]),
    ("recepcao", "Recepção", ["administrativo"], "basico", "Atendimento e recepção de visitantes", "atendimento", ["reception"]),
    ("compras_escritorio", "Compras de Escritório", ["administrativo"], "basico", "Aquisição de materiais de escritório", "suprimentos", ["office supplies"]),
    ("controle_patrimonial", "Controle Patrimonial", ["administrativo", "contabil"], "intermediario", "Gestão de ativos e patrimônio", "patrimonio", ["asset control"]),
    ("office_365", "Microsoft Office 365", ["administrativo"], "basico", "Suite de produtividade Microsoft", "ferramentas", ["microsoft"]),
    ("google_workspace", "Google Workspace", ["administrativo"], "basico", "Suite de produtividade Google", "ferramentas", ["google"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _admin_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )

# ----- FACILITIES (15+ skills) -----
_facilities_skills = [
    ("gestao_facilities", "Gestão de Facilities", ["facilities"], "intermediario", "Administração de instalações e serviços", "gestao", ["facility management"]),
    ("manutencao_predial", "Manutenção Predial", ["facilities"], "intermediario", "Manutenção de edificações", "manutencao", ["building maintenance"]),
    ("seguranca_patrimonial", "Segurança Patrimonial", ["facilities"], "intermediario", "Gestão de segurança física", "seguranca", ["physical security"]),
    ("cftv", "CFTV", ["facilities"], "basico", "Circuito fechado de TV", "seguranca", ["surveillance"]),
    ("controle_acesso", "Controle de Acesso", ["facilities"], "basico", "Sistemas de controle de acesso", "seguranca", ["access control"]),
    ("limpeza_conservacao", "Limpeza e Conservação", ["facilities"], "basico", "Gestão de serviços de limpeza", "servicos", ["cleaning"]),
    ("portaria", "Portaria", ["facilities"], "basico", "Gestão de portaria e recepção", "servicos", ["concierge"]),
    ("cafeteria", "Cafeteria/Restaurante", ["facilities"], "basico", "Gestão de serviços de alimentação", "servicos", ["food services"]),
    ("jardinagem", "Jardinagem e Paisagismo", ["facilities"], "basico", "Manutenção de áreas verdes", "servicos", ["landscaping"]),
    ("ar_condicionado", "HVAC/Ar Condicionado", ["facilities"], "intermediario", "Climatização de ambientes", "infraestrutura", ["hvac"]),
    ("elevadores", "Gestão de Elevadores", ["facilities"], "basico", "Manutenção de elevadores", "infraestrutura", ["elevators"]),
    ("sustentabilidade_predial", "Sustentabilidade Predial", ["facilities"], "intermediario", "Práticas sustentáveis em edificações", "sustentabilidade", ["green building"]),
    ("energy_management", "Gestão de Energia", ["facilities"], "intermediario", "Controle de consumo energético", "infraestrutura", ["energy"]),
    ("bms", "BMS (Building Management System)", ["facilities"], "avancado", "Sistemas de automação predial", "sistemas", ["building automation"]),
    ("space_planning", "Space Planning", ["facilities"], "intermediario", "Planejamento de espaços", "projeto", ["workplace"]),
]

for skill_id, nome, areas, nivel, descricao, categoria, palavras in _facilities_skills:
    TECHNICAL_SKILLS[skill_id] = TechnicalSkill(
        id=skill_id,
        nome=nome,
        areas=areas,
        nivel_minimo=nivel,
        descricao=descricao,
        categoria=categoria,
        palavras_chave=palavras
    )


# =============================================================================
# ROLES BY AREA
# =============================================================================

ROLES_CATALOG: dict[str, Role] = {}

# ----- TECNOLOGIA ROLES -----
_tech_roles = [
    ("dev_backend", "Desenvolvedor Backend", "tecnologia", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve e mantém sistemas backend, APIs e integrações", ["python", "java", "nodejs", "sql", "apis_rest", "docker"], ["resolucao_problemas", "trabalho_equipe", "aprendizado_continuo"], ["Dev Backend", "Backend Developer", "Programador Backend"]),
    ("dev_frontend", "Desenvolvedor Frontend", "tecnologia", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve interfaces de usuário e aplicações web", ["react", "typescript", "javascript", "nextjs", "figma"], ["atencao_detalhes", "criatividade", "comunicacao"], ["Dev Frontend", "Frontend Developer", "Programador Frontend"]),
    ("dev_fullstack", "Desenvolvedor Fullstack", "tecnologia", ["junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve aplicações completas, do frontend ao backend", ["react", "nodejs", "typescript", "postgresql", "docker"], ["resolucao_problemas", "adaptabilidade", "organizacao"], ["Dev Fullstack", "Fullstack Developer"]),
    ("engenheiro_dados", "Engenheiro de Dados", "tecnologia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii", "especialista"], "Projeta e mantém pipelines de dados e infraestrutura de dados", ["python", "sql", "spark", "airflow", "kafka", "aws"], ["pensamento_analitico", "resolucao_problemas", "atencao_detalhes"], ["Data Engineer"]),
    ("cientista_dados", "Cientista de Dados", "tecnologia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii", "especialista"], "Desenvolve modelos de machine learning e análises avançadas", ["python", "machine_learning", "sql", "tensorflow", "pytorch"], ["pensamento_analitico", "criatividade", "comunicacao"], ["Data Scientist"]),
    ("devops", "Engenheiro DevOps/SRE", "tecnologia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii", "especialista"], "Gerencia infraestrutura, CI/CD e confiabilidade de sistemas", ["docker", "kubernetes", "aws", "terraform", "cicd", "linux"], ["resolucao_problemas", "adaptabilidade", "senso_urgencia"], ["DevOps Engineer", "SRE", "Site Reliability Engineer"]),
    ("tech_lead", "Tech Lead", "tecnologia", ["senior_i", "senior_ii", "especialista"], "Lidera tecnicamente uma equipe de desenvolvimento", ["python", "microservicos", "scrum", "git"], ["lideranca", "comunicacao", "tomada_decisao", "mentoria"], ["Technical Lead", "Líder Técnico"]),
    ("arquiteto_software", "Arquiteto de Software", "tecnologia", ["senior_ii", "especialista"], "Define arquitetura de sistemas e padrões técnicos", ["microservicos", "aws", "docker", "kubernetes"], ["visao_estrategica", "pensamento_sistemico", "comunicacao"], ["Software Architect"]),
    ("analista_seguranca", "Analista de Segurança da Informação", "tecnologia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Protege sistemas e dados contra ameaças de segurança", ["seguranca_informacao", "linux", "aws"], ["pensamento_critico", "atencao_detalhes", "etica"], ["Security Analyst", "InfoSec Analyst"]),
    ("analista_suporte", "Analista de Suporte/Helpdesk", "tecnologia", ["junior_i", "junior_ii", "pleno_i", "pleno_ii"], "Presta suporte técnico a usuários e sistemas", ["linux", "office_365"], ["orientacao_cliente", "comunicacao", "resolucao_problemas"], ["Support Analyst", "IT Support"]),
    ("product_manager", "Product Manager", "tecnologia", ["pleno_ii", "senior_i", "senior_ii", "especialista"], "Gerencia o ciclo de vida de produtos digitais", ["scrum", "kanban", "ux_ui"], ["lideranca", "comunicacao", "visao_estrategica", "orientacao_cliente"], ["PM", "Gerente de Produto"]),
    ("analista_bi", "Analista de BI", "tecnologia", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Desenvolve análises e dashboards de business intelligence", ["sql", "power_bi", "tableau"], ["pensamento_analitico", "comunicacao", "atencao_detalhes"], ["BI Analyst", "Business Intelligence Analyst"]),
    ("qa_engineer", "Engenheiro de QA", "tecnologia", ["junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Garante qualidade de software através de testes", ["python", "javascript"], ["atencao_detalhes", "pensamento_critico", "organizacao"], ["QA", "Quality Assurance", "Tester"]),
    ("gerente_ti", "Gerente de TI", "tecnologia", ["gerente"], "Gerencia equipes e operações de tecnologia", ["scrum", "kanban"], ["lideranca", "gestao_stakeholders", "tomada_decisao", "planejamento"], ["IT Manager"]),
    ("cto", "CTO (Chief Technology Officer)", "tecnologia", ["diretor", "c_level"], "Dirige a estratégia tecnológica da empresa", ["microservicos", "aws"], ["visao_estrategica", "lideranca", "tomada_decisao", "inovacao"], ["Diretor de Tecnologia"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _tech_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- FINANCEIRO ROLES -----
_fin_roles = [
    ("analista_financeiro", "Analista Financeiro", "financeiro", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Realiza análises financeiras e suporte à tomada de decisão", ["fpa", "excel_avancado_fin", "power_bi", "orcamento"], ["pensamento_analitico", "atencao_detalhes", "organizacao"], ["Financial Analyst"]),
    ("analista_fpa", "Analista de FP&A", "financeiro", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Responsável por planejamento financeiro e análise de variância", ["fpa", "orcamento", "forecast", "modelagem_financeira"], ["pensamento_analitico", "comunicacao", "visao_estrategica"], ["FP&A Analyst"]),
    ("analista_tesouraria", "Analista de Tesouraria", "financeiro", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Gerencia fluxo de caixa e operações de tesouraria", ["tesouraria", "fluxo_caixa", "cambio"], ["atencao_detalhes", "organizacao", "etica"], ["Treasury Analyst"]),
    ("controller", "Controller", "financeiro", ["senior_i", "senior_ii", "gerente"], "Responsável por controladoria e reporting gerencial", ["controladoria", "relatorios_gerenciais", "kpis_financeiros", "sap_fi"], ["lideranca", "pensamento_analitico", "etica", "comunicacao"], ["Controlador"]),
    ("coordenador_financeiro", "Coordenador Financeiro", "financeiro", ["coordenador"], "Coordena atividades financeiras e equipe", ["fpa", "tesouraria", "controladoria"], ["lideranca", "organizacao", "gestao_tempo"], ["Financial Coordinator"]),
    ("gerente_financeiro", "Gerente Financeiro", "financeiro", ["gerente"], "Gerencia área financeira e estratégia", ["fpa", "controladoria", "tesouraria"], ["lideranca", "visao_estrategica", "tomada_decisao", "gestao_stakeholders"], ["Finance Manager"]),
    ("diretor_financeiro", "Diretor Financeiro", "financeiro", ["diretor"], "Dirige a área financeira da empresa", ["modelagem_financeira", "ma", "investimentos"], ["visao_estrategica", "lideranca", "tomada_decisao", "influencia"], ["Finance Director"]),
    ("cfo", "CFO (Chief Financial Officer)", "financeiro", ["c_level"], "Principal executivo financeiro da empresa", ["ma", "investimentos", "valuation"], ["visao_estrategica", "lideranca", "tomada_decisao", "gestao_stakeholders"], ["Diretor Financeiro"]),
    ("analista_credito", "Analista de Crédito", "financeiro", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Avalia risco de crédito de clientes", ["credito", "sql"], ["pensamento_analitico", "atencao_detalhes", "etica"], ["Credit Analyst"]),
    ("analista_investimentos", "Analista de Investimentos", "financeiro", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Analisa oportunidades de investimento", ["investimentos", "valuation", "modelagem_financeira"], ["pensamento_analitico", "orientacao_dados", "comunicacao"], ["Investment Analyst"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _fin_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- CONTÁBIL ROLES -----
_contabil_roles = [
    ("analista_contabil", "Analista Contábil", "contabil", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Realiza escrituração e análises contábeis", ["contabilidade_geral", "fechamento_contabil", "conciliacao_contabil", "sql"], ["atencao_detalhes", "organizacao", "etica"], ["Accounting Analyst"]),
    ("contador", "Contador", "contabil", ["pleno_ii", "senior_i", "senior_ii", "especialista"], "Responsável pelas demonstrações e conformidade contábil", ["ifrs", "cpc", "balanco_patrimonial", "dre", "sped_contabil"], ["atencao_detalhes", "etica", "comunicacao"], ["Accountant"]),
    ("coordenador_contabil", "Coordenador Contábil", "contabil", ["coordenador"], "Coordena equipe e processos contábeis", ["fechamento_contabil", "ifrs", "consolidacao"], ["lideranca", "organizacao", "gestao_tempo"], ["Accounting Coordinator"]),
    ("gerente_contabil", "Gerente Contábil", "contabil", ["gerente"], "Gerencia área contábil da empresa", ["ifrs", "consolidacao", "auditoria_externa"], ["lideranca", "visao_estrategica", "gestao_stakeholders"], ["Accounting Manager"]),
    ("analista_custos", "Analista de Custos", "contabil", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Analisa e controla custos da empresa", ["contabilidade_custos", "custeio_absorcao", "abc_custos"], ["pensamento_analitico", "atencao_detalhes", "resolucao_problemas"], ["Cost Analyst"]),
    ("analista_ativo_fixo", "Analista de Ativo Fixo", "contabil", ["junior_ii", "pleno_i", "pleno_ii"], "Controla ativos imobilizados e intangíveis", ["ativo_imobilizado", "depreciacao", "intangivel"], ["atencao_detalhes", "organizacao"], ["Fixed Asset Analyst"]),
    ("especialista_ifrs", "Especialista IFRS", "contabil", ["senior_ii", "especialista"], "Expert em normas internacionais de contabilidade", ["ifrs", "cpc", "cpc_06", "cpc_47", "cpc_48"], ["pensamento_analitico", "aprendizado_continuo", "comunicacao"], ["IFRS Specialist"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _contabil_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- FISCAL ROLES -----
_fiscal_roles = [
    ("analista_fiscal", "Analista Fiscal", "fiscal", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Realiza apuração de impostos e obrigações acessórias", ["icms", "pis_cofins", "sped_fiscal", "nfe"], ["atencao_detalhes", "organizacao", "aprendizado_continuo"], ["Tax Analyst"]),
    ("analista_tributario", "Analista Tributário", "fiscal", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Analisa questões tributárias e planejamento fiscal", ["planejamento_tributario", "irpj", "csll", "lucro_real"], ["pensamento_analitico", "etica", "resolucao_problemas"], ["Tax Analyst"]),
    ("especialista_fiscal", "Especialista Fiscal", "fiscal", ["senior_ii", "especialista"], "Expert em legislação tributária e fiscal", ["planejamento_tributario", "transfer_pricing", "contencioso_tributario"], ["pensamento_critico", "comunicacao", "influencia"], ["Tax Specialist"]),
    ("coordenador_fiscal", "Coordenador Fiscal", "fiscal", ["coordenador"], "Coordena equipe e processos fiscais", ["sped_fiscal", "icms", "planejamento_tributario"], ["lideranca", "organizacao", "gestao_tempo"], ["Tax Coordinator"]),
    ("gerente_fiscal", "Gerente Fiscal/Tributário", "fiscal", ["gerente"], "Gerencia área fiscal e estratégia tributária", ["planejamento_tributario", "contencioso_tributario"], ["lideranca", "visao_estrategica", "gestao_stakeholders"], ["Tax Manager"]),
    ("diretor_tributario", "Diretor Tributário", "fiscal", ["diretor"], "Dirige estratégia tributária da empresa", ["planejamento_tributario", "ma", "tributacao_internacional"], ["visao_estrategica", "lideranca", "influencia"], ["Tax Director"]),
    ("analista_retencoes", "Analista de Retenções", "fiscal", ["junior_ii", "pleno_i", "pleno_ii"], "Responsável por retenções na fonte", ["retencoes_fonte", "inss_retido", "iss_retido"], ["atencao_detalhes", "organizacao"], ["Withholding Analyst"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _fiscal_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- RH ROLES -----
_rh_roles = [
    ("analista_rs", "Analista de R&S", "rh", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Conduz processos de recrutamento e seleção", ["recrutamento_selecao", "entrevista_competencias", "linkedin_recruiter", "ats"], ["comunicacao", "empatia", "organizacao"], ["Recruiter", "Recrutador"]),
    ("analista_td", "Analista de T&D", "rh", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Desenvolve e executa programas de treinamento", ["td", "lms", "lnt", "pdi"], ["comunicacao", "criatividade", "organizacao"], ["Training Analyst"]),
    ("analista_remuneracao", "Analista de Remuneração", "rh", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Gerencia estrutura de cargos e salários", ["cargos_salarios", "pesquisa_salarial", "remuneracao_variavel"], ["pensamento_analitico", "confidencialidade", "atencao_detalhes"], ["Compensation Analyst"]),
    ("business_partner_rh", "Business Partner de RH", "rh", ["senior_i", "senior_ii", "coordenador"], "Atua como parceiro estratégico das áreas de negócio", ["business_partner", "avaliacao_desempenho", "pesquisa_clima"], ["comunicacao", "influencia", "visao_estrategica", "empatia"], ["HRBP"]),
    ("headhunter", "Headhunter", "rh", ["pleno_ii", "senior_i", "senior_ii"], "Realiza hunting de executivos e posições estratégicas", ["hunting", "linkedin_recruiter", "entrevista_competencias"], ["comunicacao", "negociacao", "networking", "persistencia"], ["Executive Recruiter"]),
    ("coordenador_rh", "Coordenador de RH", "rh", ["coordenador"], "Coordena subsistemas de RH", ["recrutamento_selecao", "td", "avaliacao_desempenho"], ["lideranca", "organizacao", "comunicacao"], ["HR Coordinator"]),
    ("gerente_rh", "Gerente de RH", "rh", ["gerente"], "Gerencia área de recursos humanos", ["business_partner", "people_analytics", "cultura_organizacional"], ["lideranca", "visao_estrategica", "gestao_stakeholders"], ["HR Manager"]),
    ("diretor_rh", "Diretor de RH", "rh", ["diretor"], "Dirige estratégia de pessoas da empresa", ["cultura_organizacional", "sucessao", "people_analytics"], ["visao_estrategica", "lideranca", "influencia"], ["HR Director", "Diretor de Pessoas"]),
    ("chro", "CHRO (Chief Human Resources Officer)", "rh", ["c_level"], "Principal executivo de pessoas da empresa", ["cultura_organizacional", "sucessao", "diversidade_inclusao"], ["visao_estrategica", "lideranca", "influencia", "empatia"], ["CPO", "Chief People Officer"]),
    ("analista_diversidade", "Analista de Diversidade e Inclusão", "rh", ["pleno_i", "pleno_ii", "senior_i"], "Desenvolve programas de D&I", ["diversidade_inclusao", "pesquisa_clima"], ["empatia", "comunicacao", "consciencia_cultural"], ["D&I Analyst"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _rh_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- DP ROLES -----
_dp_roles = [
    ("analista_dp", "Analista de Departamento Pessoal", "dp", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Executa rotinas de departamento pessoal", ["folha_pagamento", "esocial", "admissao", "demissao"], ["atencao_detalhes", "organizacao", "etica"], ["Payroll Analyst"]),
    ("analista_folha", "Analista de Folha de Pagamento", "dp", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Processa folha de pagamento e encargos", ["folha_pagamento", "encargos_sociais", "esocial", "sistemas_dp"], ["atencao_detalhes", "organizacao", "gestao_tempo"], ["Payroll Specialist"]),
    ("analista_beneficios", "Analista de Benefícios", "dp", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Administra benefícios corporativos", ["beneficios_dp", "plano_saude", "vale_transporte"], ["organizacao", "orientacao_cliente", "negociacao"], ["Benefits Analyst"]),
    ("coordenador_dp", "Coordenador de DP", "dp", ["coordenador"], "Coordena equipe e processos de DP", ["folha_pagamento", "esocial", "clt"], ["lideranca", "organizacao", "atencao_detalhes"], ["Payroll Coordinator"]),
    ("gerente_dp", "Gerente de DP", "dp", ["gerente"], "Gerencia departamento pessoal", ["folha_pagamento", "clt", "esocial"], ["lideranca", "gestao_stakeholders", "etica"], ["Payroll Manager"]),
    ("tecnico_seguranca", "Técnico de Segurança do Trabalho", "dp", ["junior_ii", "pleno_i", "pleno_ii"], "Atua na prevenção de acidentes de trabalho", ["saude_seguranca", "cipa", "cat"], ["atencao_detalhes", "comunicacao", "proatividade"], ["Safety Technician"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _dp_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- COMERCIAL ROLES -----
_comercial_roles = [
    ("vendedor", "Vendedor", "comercial", ["junior_i", "junior_ii", "pleno_i", "pleno_ii"], "Realiza vendas e atendimento a clientes", ["vendas_consultivas", "crm_comercial", "prospeccao"], ["comunicacao", "negociacao", "resiliencia", "foco_resultados"], ["Sales Rep"]),
    ("sdr", "SDR (Sales Development Representative)", "comercial", ["junior_i", "junior_ii", "pleno_i"], "Prospecta e qualifica leads para vendas", ["prospeccao", "cold_calling", "crm_comercial"], ["comunicacao", "persistencia", "proatividade"], ["BDR"]),
    ("account_executive", "Account Executive", "comercial", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Conduz vendas e fechamento de negócios", ["vendas_consultivas", "spin_selling", "salesforce"], ["negociacao", "comunicacao", "foco_resultados", "resiliencia"], ["AE", "Executivo de Contas"]),
    ("key_account_manager", "Key Account Manager", "comercial", ["senior_i", "senior_ii", "especialista"], "Gerencia contas estratégicas", ["key_account", "account_management", "upselling"], ["relacionamento_interpessoal", "negociacao", "visao_estrategica"], ["KAM", "Gerente de Contas Chave"]),
    ("coordenador_comercial", "Coordenador Comercial", "comercial", ["coordenador"], "Coordena equipe de vendas", ["gestao_pipeline", "forecast_vendas", "crm_comercial"], ["lideranca", "organizacao", "foco_resultados"], ["Sales Coordinator"]),
    ("gerente_comercial", "Gerente Comercial", "comercial", ["gerente"], "Gerencia área comercial e equipes de vendas", ["vendas_enterprise", "forecast_vendas", "gestao_pipeline"], ["lideranca", "visao_estrategica", "negociacao", "foco_resultados"], ["Sales Manager"]),
    ("diretor_comercial", "Diretor Comercial", "comercial", ["diretor"], "Dirige estratégia comercial da empresa", ["vendas_enterprise", "precificacao"], ["visao_estrategica", "lideranca", "gestao_stakeholders"], ["Sales Director", "CCO"]),
    ("pre_vendas", "Pré-vendas/Sales Engineer", "comercial", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Suporte técnico ao processo de vendas", ["rfp", "demonstracao_produto", "proposta_comercial"], ["comunicacao", "resolucao_problemas", "orientacao_cliente"], ["Pre-Sales", "Solution Engineer"]),
    ("customer_success_manager", "Customer Success Manager", "comercial", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Gerencia sucesso e retenção de clientes", ["customer_success", "upselling", "churn"], ["empatia", "comunicacao", "resolucao_problemas", "orientacao_cliente"], ["CSM"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _comercial_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- MARKETING ROLES -----
_marketing_roles = [
    ("analista_marketing", "Analista de Marketing", "marketing", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Executa estratégias e campanhas de marketing", ["marketing_digital", "analytics_mkt", "social_media"], ["criatividade", "comunicacao", "adaptabilidade"], ["Marketing Analyst"]),
    ("analista_performance", "Analista de Performance/Growth", "marketing", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Gerencia mídia paga e otimização de conversão", ["google_ads", "meta_ads", "analytics_mkt", "ab_testing"], ["pensamento_analitico", "orientacao_dados", "foco_resultados"], ["Growth Analyst", "Performance Analyst"]),
    ("analista_conteudo", "Analista de Conteúdo", "marketing", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Produz conteúdo para diferentes canais", ["content_marketing", "copywriting", "seo"], ["criatividade", "comunicacao", "organizacao"], ["Content Analyst", "Copywriter"]),
    ("social_media_manager", "Social Media Manager", "marketing", ["pleno_i", "pleno_ii", "senior_i"], "Gerencia redes sociais da marca", ["social_media", "community_management"], ["criatividade", "comunicacao", "adaptabilidade"], ["SMM"]),
    ("product_marketing_manager", "Product Marketing Manager", "marketing", ["senior_i", "senior_ii", "especialista"], "Gerencia marketing de produto", ["product_marketing", "go_to_market", "posicionamento"], ["comunicacao", "visao_estrategica", "pensamento_analitico"], ["PMM"]),
    ("brand_manager", "Brand Manager", "marketing", ["senior_i", "senior_ii", "gerente"], "Gerencia estratégia de marca", ["branding", "posicionamento", "pesquisa_mercado"], ["criatividade", "visao_estrategica", "comunicacao"], ["Gerente de Marca"]),
    ("coordenador_marketing", "Coordenador de Marketing", "marketing", ["coordenador"], "Coordena equipe e projetos de marketing", ["marketing_digital", "inbound_marketing"], ["lideranca", "organizacao", "comunicacao"], ["Marketing Coordinator"]),
    ("gerente_marketing", "Gerente de Marketing", "marketing", ["gerente"], "Gerencia área de marketing", ["branding", "marketing_digital", "product_marketing"], ["lideranca", "visao_estrategica", "criatividade"], ["Marketing Manager"]),
    ("cmo", "CMO (Chief Marketing Officer)", "marketing", ["diretor", "c_level"], "Dirige estratégia de marketing da empresa", ["branding", "go_to_market", "growth_hacking"], ["visao_estrategica", "lideranca", "inovacao"], ["Diretor de Marketing"]),
    ("designer", "Designer Gráfico/Visual", "marketing", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Cria materiais visuais e peças de comunicação", ["figma", "identidade_visual"], ["criatividade", "atencao_detalhes", "comunicacao"], ["Graphic Designer"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _marketing_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- JURIDICO ROLES -----
_juridico_roles = [
    ("advogado_jr", "Advogado Júnior", "juridico", ["junior_i", "junior_ii"], "Advogado em início de carreira, suporte jurídico geral", ["contratos", "revisao_contratos"], ["atencao_detalhes", "comunicacao", "etica"], ["Junior Lawyer"]),
    ("advogado_contratos", "Advogado Contratual", "juridico", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Especialista em elaboração e revisão de contratos", ["contratos", "revisao_contratos", "negociacao_juridica"], ["atencao_detalhes", "negociacao", "comunicacao"], ["Contract Lawyer"]),
    ("advogado_trabalhista", "Advogado Trabalhista", "juridico", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Especialista em direito trabalhista", ["direito_trabalhista", "contencioso_trabalhista", "consultivo_trabalhista"], ["comunicacao", "resolucao_problemas", "empatia"], ["Labor Lawyer"]),
    ("advogado_societario", "Advogado Societário", "juridico", ["pleno_ii", "senior_i", "senior_ii", "especialista"], "Especialista em direito societário e M&A", ["direito_societario", "ma_juridico", "governanca_corporativa"], ["pensamento_analitico", "atencao_detalhes", "confidencialidade"], ["Corporate Lawyer"]),
    ("advogado_tributario", "Advogado Tributário", "juridico", ["pleno_ii", "senior_i", "senior_ii", "especialista"], "Especialista em direito tributário", ["direito_tributario_jur", "contencioso_tributario_jur"], ["pensamento_analitico", "atencao_detalhes", "persistencia"], ["Tax Lawyer"]),
    ("coordenador_juridico", "Coordenador Jurídico", "juridico", ["coordenador"], "Coordena equipe e processos jurídicos", ["contratos", "contencioso_civel"], ["lideranca", "organizacao", "comunicacao"], ["Legal Coordinator"]),
    ("gerente_juridico", "Gerente Jurídico", "juridico", ["gerente"], "Gerencia departamento jurídico", ["contratos", "direito_societario", "compliance_juridico"], ["lideranca", "visao_estrategica", "gestao_stakeholders"], ["Legal Manager"]),
    ("diretor_juridico", "Diretor Jurídico", "juridico", ["diretor"], "Dirige área jurídica da empresa", ["direito_societario", "ma_juridico", "governanca_corporativa"], ["visao_estrategica", "lideranca", "influencia"], ["General Counsel", "CLO"]),
    ("especialista_lgpd", "Especialista LGPD/DPO", "juridico", ["senior_i", "senior_ii", "especialista"], "Responsável por proteção de dados", ["lgpd_juridico", "direito_digital"], ["atencao_detalhes", "comunicacao", "etica"], ["DPO", "Data Protection Officer"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _juridico_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- COMPLIANCE ROLES -----
_compliance_roles = [
    ("analista_compliance", "Analista de Compliance", "compliance", ["junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Executa atividades de conformidade e controles", ["programa_compliance", "politicas_corporativas", "treinamento_compliance"], ["atencao_detalhes", "etica", "comunicacao"], ["Compliance Analyst"]),
    ("analista_riscos", "Analista de Riscos", "compliance", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Identifica e avalia riscos corporativos", ["gestao_riscos", "matriz_riscos", "controles_internos"], ["pensamento_analitico", "atencao_detalhes", "comunicacao"], ["Risk Analyst"]),
    ("auditor_interno", "Auditor Interno", "compliance", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Realiza auditorias internas", ["auditoria_interna", "auditoria_processos", "controles_internos"], ["pensamento_critico", "atencao_detalhes", "etica", "comunicacao"], ["Internal Auditor"]),
    ("coordenador_compliance", "Coordenador de Compliance", "compliance", ["coordenador"], "Coordena programa de compliance", ["programa_compliance", "gestao_riscos", "kyc"], ["lideranca", "organizacao", "comunicacao"], ["Compliance Coordinator"]),
    ("gerente_compliance", "Gerente de Compliance", "compliance", ["gerente"], "Gerencia área de compliance", ["programa_compliance", "erm", "anticorrupcao"], ["lideranca", "visao_estrategica", "influencia", "etica"], ["Compliance Manager"]),
    ("cco", "CCO (Chief Compliance Officer)", "compliance", ["diretor", "c_level"], "Dirige programa de compliance da empresa", ["programa_compliance", "erm", "governanca_corporativa"], ["visao_estrategica", "lideranca", "etica", "influencia"], ["Diretor de Compliance"]),
    ("analista_pld", "Analista PLD/AML", "compliance", ["pleno_i", "pleno_ii", "senior_i"], "Especialista em prevenção à lavagem de dinheiro", ["pld", "kyc"], ["atencao_detalhes", "etica", "pensamento_critico"], ["AML Analyst"]),
    ("gerente_auditoria", "Gerente de Auditoria Interna", "compliance", ["gerente"], "Gerencia equipe de auditoria interna", ["auditoria_interna", "sox_compliance", "coso"], ["lideranca", "pensamento_critico", "comunicacao"], ["Internal Audit Manager"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _compliance_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- OPERAÇÕES ROLES -----
_operacoes_roles = [
    ("analista_processos", "Analista de Processos", "operacoes", ["junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Mapeia e melhora processos organizacionais", ["gestao_processos", "bpm", "lean"], ["pensamento_analitico", "organizacao", "comunicacao"], ["Process Analyst"]),
    ("analista_projetos", "Analista de Projetos", "operacoes", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Apoia gestão de projetos corporativos", ["project_management", "agile_ops"], ["organizacao", "comunicacao", "gestao_tempo"], ["Project Analyst"]),
    ("gerente_projetos", "Gerente de Projetos", "operacoes", ["senior_i", "senior_ii", "gerente"], "Gerencia projetos de média e alta complexidade", ["project_management", "pmp", "agile_ops"], ["lideranca", "comunicacao", "gestao_stakeholders", "resolucao_problemas"], ["Project Manager", "PM"]),
    ("coordenador_operacoes", "Coordenador de Operações", "operacoes", ["coordenador"], "Coordena operações e equipe", ["gestao_processos", "kpis_operacionais"], ["lideranca", "organizacao", "foco_resultados"], ["Operations Coordinator"]),
    ("gerente_operacoes", "Gerente de Operações", "operacoes", ["gerente"], "Gerencia área de operações", ["lean_six_sigma", "capacity_planning", "erp"], ["lideranca", "visao_estrategica", "foco_resultados"], ["Operations Manager"]),
    ("diretor_operacoes", "Diretor de Operações", "operacoes", ["diretor"], "Dirige operações da empresa", ["lean_six_sigma", "change_management"], ["visao_estrategica", "lideranca", "tomada_decisao"], ["COO", "Chief Operations Officer"]),
    ("especialista_lean", "Especialista Lean/Six Sigma", "operacoes", ["senior_i", "senior_ii", "especialista"], "Expert em metodologias de melhoria", ["lean_six_sigma", "kaizen", "six_sigma"], ["pensamento_analitico", "comunicacao", "influencia"], ["Lean Six Sigma Expert"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _operacoes_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- LOGÍSTICA ROLES -----
_logistica_roles = [
    ("analista_logistica", "Analista de Logística", "logistica", ["junior_i", "junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Executa atividades de logística e distribuição", ["gestao_estoques", "transporte", "wms"], ["organizacao", "resolucao_problemas", "atencao_detalhes"], ["Logistics Analyst"]),
    ("analista_supply_chain", "Analista de Supply Chain", "logistica", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Analisa e otimiza cadeia de suprimentos", ["supply_chain_management", "sop", "demand_planning"], ["pensamento_analitico", "visao_sistemica", "comunicacao"], ["Supply Chain Analyst"]),
    ("analista_comex", "Analista de Comércio Exterior", "logistica", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Executa operações de importação/exportação", ["comercio_exterior", "importacao", "exportacao", "despacho_aduaneiro"], ["atencao_detalhes", "organizacao", "aprendizado_continuo"], ["Foreign Trade Analyst"]),
    ("coordenador_logistica", "Coordenador de Logística", "logistica", ["coordenador"], "Coordena operações logísticas", ["gestao_estoques", "transporte", "wms"], ["lideranca", "organizacao", "resolucao_problemas"], ["Logistics Coordinator"]),
    ("gerente_logistica", "Gerente de Logística", "logistica", ["gerente"], "Gerencia área de logística", ["supply_chain_management", "tms", "wms"], ["lideranca", "visao_estrategica", "foco_resultados"], ["Logistics Manager"]),
    ("gerente_supply_chain", "Gerente de Supply Chain", "logistica", ["gerente"], "Gerencia cadeia de suprimentos", ["supply_chain_management", "sop", "demand_planning"], ["lideranca", "visao_estrategica", "pensamento_sistemico"], ["Supply Chain Manager"]),
    ("diretor_supply_chain", "Diretor de Supply Chain", "logistica", ["diretor"], "Dirige cadeia de suprimentos", ["supply_chain_management", "sop"], ["visao_estrategica", "lideranca", "tomada_decisao"], ["Supply Chain Director", "CSCO"]),
    ("supervisor_armazem", "Supervisor de Armazém", "logistica", ["coordenador"], "Supervisiona operações de armazém", ["armazenagem", "wms", "picking_packing"], ["lideranca", "organizacao", "senso_urgencia"], ["Warehouse Supervisor"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _logistica_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- COMPRAS ROLES -----
_compras_roles = [
    ("comprador", "Comprador", "compras", ["junior_i", "junior_ii", "pleno_i", "pleno_ii"], "Executa processos de compras", ["cotacao", "pedido_compra", "negociacao_compras"], ["negociacao", "organizacao", "atencao_detalhes"], ["Buyer", "Purchasing Agent"]),
    ("analista_compras", "Analista de Compras", "compras", ["junior_ii", "pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Analisa e otimiza processos de compras", ["strategic_sourcing", "vendor_management", "spend_analysis"], ["negociacao", "pensamento_analitico", "comunicacao"], ["Procurement Analyst"]),
    ("coordenador_compras", "Coordenador de Compras", "compras", ["coordenador"], "Coordena equipe e processos de compras", ["strategic_sourcing", "contratos_compras", "vendor_management"], ["lideranca", "negociacao", "organizacao"], ["Procurement Coordinator"]),
    ("gerente_compras", "Gerente de Compras", "compras", ["gerente"], "Gerencia área de compras", ["strategic_sourcing", "category_management", "tcl"], ["lideranca", "visao_estrategica", "negociacao"], ["Procurement Manager"]),
    ("diretor_compras", "Diretor de Compras/Suprimentos", "compras", ["diretor"], "Dirige estratégia de suprimentos", ["strategic_sourcing", "category_management"], ["visao_estrategica", "lideranca", "negociacao"], ["Chief Procurement Officer", "CPO"]),
    ("category_manager", "Category Manager", "compras", ["senior_i", "senior_ii", "especialista"], "Gerencia categorias específicas de compras", ["category_management", "strategic_sourcing", "tcl"], ["pensamento_analitico", "negociacao", "visao_estrategica"], ["Gerente de Categoria"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _compras_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- ADMINISTRATIVO ROLES -----
_administrativo_roles = [
    ("assistente_administrativo", "Assistente Administrativo", "administrativo", ["junior_i", "junior_ii", "pleno_i"], "Presta apoio administrativo às áreas, organiza documentos e rotinas de escritório", ["office_365", "excel"], ["organizacao", "comunicacao", "atencao_detalhes"], ["Assistente Admin", "Administrative Assistant"]),
    ("analista_administrativo", "Analista Administrativo", "administrativo", ["pleno_i", "pleno_ii", "senior_i"], "Analisa processos administrativos, elabora relatórios e propõe melhorias", ["excel", "power_bi", "office_365"], ["pensamento_analitico", "organizacao", "resolucao_problemas"], ["Administrative Analyst"]),
    ("secretaria_executiva", "Secretária Executiva", "administrativo", ["pleno_i", "pleno_ii", "senior_i"], "Assessora diretamente executivos, gerencia agendas e comunicações corporativas", ["office_365", "excel"], ["comunicacao", "organizacao", "confidencialidade", "gestao_tempo"], ["Executive Secretary", "Secretária de Diretoria"]),
    ("recepcionista", "Recepcionista", "administrativo", ["junior_i", "junior_ii"], "Recepciona visitantes, atende ligações e presta suporte inicial aos clientes", ["office_365"], ["comunicacao", "orientacao_cliente", "organizacao"], ["Receptionist"]),
    ("coordenador_administrativo", "Coordenador Administrativo", "administrativo", ["coordenador"], "Coordena equipe e processos administrativos da organização", ["excel", "power_bi", "office_365"], ["lideranca", "organizacao", "gestao_tempo", "comunicacao"], ["Administrative Coordinator"]),
    ("gerente_administrativo", "Gerente Administrativo", "administrativo", ["gerente"], "Gerencia área administrativa, orçamento e serviços gerais", ["excel", "power_bi"], ["lideranca", "visao_estrategica", "gestao_stakeholders", "tomada_decisao"], ["Administrative Manager"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _administrativo_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- QUALIDADE ROLES -----
_qualidade_roles = [
    ("analista_qualidade", "Analista de Qualidade", "qualidade", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Analisa e controla processos de qualidade, elabora documentação e indicadores", ["gestao_qualidade", "iso_9001", "masp", "excel"], ["pensamento_analitico", "atencao_detalhes", "resolucao_problemas"], ["Quality Analyst"]),
    ("inspetor_qualidade", "Inspetor de Qualidade", "qualidade", ["junior_i", "junior_ii", "pleno_i"], "Inspeciona produtos e processos para garantir conformidade com padrões de qualidade", ["controle_qualidade", "cep"], ["atencao_detalhes", "organizacao", "orientacao_qualidade"], ["Quality Inspector"]),
    ("auditor_qualidade", "Auditor de Qualidade", "qualidade", ["pleno_ii", "senior_i", "senior_ii", "especialista"], "Conduz auditorias internas e externas de sistemas de qualidade", ["auditoria_qualidade", "auditor_lider", "iso_9001"], ["pensamento_critico", "comunicacao", "atencao_detalhes", "etica"], ["Quality Auditor"]),
    ("coordenador_qualidade", "Coordenador de Qualidade", "qualidade", ["coordenador"], "Coordena equipe e processos de qualidade, implementa melhorias", ["gestao_qualidade", "iso_9001_impl", "auditoria_qualidade"], ["lideranca", "organizacao", "comunicacao", "resolucao_problemas"], ["Quality Coordinator"]),
    ("gerente_qualidade", "Gerente de Qualidade", "qualidade", ["gerente"], "Gerencia sistema de gestão da qualidade e certificações", ["gestao_qualidade", "iso_9001_impl", "auditor_lider"], ["lideranca", "visao_estrategica", "tomada_decisao", "gestao_stakeholders"], ["Quality Manager"]),
    ("engenheiro_qualidade", "Engenheiro de Qualidade", "qualidade", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve e implementa processos e sistemas de garantia da qualidade", ["fmea", "cep", "msa", "gestao_qualidade"], ["pensamento_analitico", "resolucao_problemas", "inovacao"], ["Quality Engineer"]),
    ("especialista_six_sigma", "Especialista Six Sigma", "qualidade", ["senior_i", "senior_ii", "especialista"], "Lidera projetos de melhoria usando metodologia Six Sigma (Green/Black Belt)", ["six_sigma", "cep", "fmea", "masp"], ["pensamento_analitico", "lideranca", "resolucao_problemas", "orientacao_dados"], ["Six Sigma Specialist", "Black Belt", "Green Belt"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _qualidade_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- ENGENHARIA ROLES -----
_engenharia_roles = [
    ("engenheiro_civil", "Engenheiro Civil", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Projeta e acompanha obras de construção civil e infraestrutura", ["autocad", "excel"], ["pensamento_analitico", "atencao_detalhes", "resolucao_problemas"], ["Civil Engineer"]),
    ("engenheiro_mecanico", "Engenheiro Mecânico", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Projeta e desenvolve sistemas mecânicos e equipamentos industriais", ["autocad", "solidworks"], ["pensamento_analitico", "criatividade", "resolucao_problemas"], ["Mechanical Engineer"]),
    ("engenheiro_eletrico", "Engenheiro Elétrico", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Projeta e mantém sistemas elétricos e de potência", ["autocad"], ["pensamento_analitico", "atencao_detalhes", "resolucao_problemas"], ["Electrical Engineer"]),
    ("engenheiro_automacao", "Engenheiro de Automação", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve e implementa sistemas de automação industrial", ["plc", "scada"], ["pensamento_analitico", "inovacao", "resolucao_problemas"], ["Automation Engineer"]),
    ("engenheiro_processos", "Engenheiro de Processos", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Otimiza processos industriais e de manufatura", ["lean", "six_sigma", "excel"], ["pensamento_analitico", "resolucao_problemas", "orientacao_dados"], ["Process Engineer"]),
    ("coordenador_engenharia", "Coordenador de Engenharia", "engenharia", ["coordenador"], "Coordena equipe e projetos de engenharia", ["excel", "ms_project"], ["lideranca", "organizacao", "comunicacao", "gestao_projetos_soft"], ["Engineering Coordinator"]),
    ("gerente_engenharia", "Gerente de Engenharia", "engenharia", ["gerente"], "Gerencia área de engenharia, orçamento e recursos técnicos", ["excel", "power_bi"], ["lideranca", "visao_estrategica", "tomada_decisao", "gestao_stakeholders"], ["Engineering Manager"]),
    ("projetista", "Projetista", "engenharia", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Desenvolve projetos técnicos e detalhamentos em CAD", ["autocad", "solidworks"], ["atencao_detalhes", "criatividade", "organizacao"], ["Designer", "Design Engineer"]),
    ("desenhista_tecnico", "Desenhista Técnico/CAD", "engenharia", ["junior_i", "junior_ii", "pleno_i"], "Elabora desenhos técnicos e modelos 3D conforme especificações", ["autocad", "solidworks"], ["atencao_detalhes", "organizacao"], ["CAD Technician", "Technical Drawer"]),
    ("engenheiro_manutencao", "Engenheiro de Manutenção", "engenharia", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Planeja e coordena manutenção preventiva e corretiva de equipamentos", ["pcm", "excel"], ["pensamento_analitico", "resolucao_problemas", "organizacao"], ["Maintenance Engineer"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _engenharia_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- PRODUÇÃO/MANUFATURA ROLES -----
_producao_roles = [
    ("operador_producao", "Operador de Produção", "producao", ["junior_i", "junior_ii"], "Opera máquinas e equipamentos na linha de produção", ["5s"], ["atencao_detalhes", "trabalho_equipe", "senso_urgencia"], ["Production Operator"]),
    ("lider_producao", "Líder de Produção", "producao", ["pleno_i", "pleno_ii"], "Lidera equipe operacional na linha de produção", ["lean", "5s"], ["lideranca", "comunicacao", "trabalho_equipe", "senso_urgencia"], ["Production Leader", "Team Leader"]),
    ("supervisor_producao", "Supervisor de Produção", "producao", ["coordenador"], "Supervisiona operações de produção e equipe de líderes", ["lean", "kaizen", "5s"], ["lideranca", "gestao_conflitos", "tomada_decisao"], ["Production Supervisor"]),
    ("coordenador_producao", "Coordenador de Produção", "producao", ["coordenador"], "Coordena múltiplas linhas de produção e processos fabris", ["lean", "mrp", "excel"], ["lideranca", "organizacao", "gestao_stakeholders"], ["Production Coordinator"]),
    ("gerente_producao", "Gerente de Produção", "producao", ["gerente"], "Gerencia área de produção, metas e indicadores de performance", ["lean", "six_sigma", "mrp"], ["lideranca", "visao_estrategica", "tomada_decisao", "foco_resultados"], ["Production Manager", "Plant Manager"]),
    ("diretor_industrial", "Diretor Industrial", "producao", ["diretor"], "Dirige operações industriais e estratégia de manufatura", ["lean", "six_sigma"], ["visao_estrategica", "lideranca", "tomada_decisao", "gestao_stakeholders"], ["Industrial Director", "VP Manufacturing"]),
    ("analista_pcp", "Analista de PCP", "producao", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Planeja e controla produção, gerencia ordens e sequenciamento", ["mrp", "excel", "erp"], ["pensamento_analitico", "organizacao", "atencao_detalhes"], ["PCP Analyst", "Production Planning Analyst"]),
    ("planejador_producao", "Planejador de Produção", "producao", ["pleno_i", "pleno_ii", "senior_i"], "Elabora planos de produção e balanceamento de capacidade", ["mrp", "excel", "sop"], ["pensamento_analitico", "organizacao", "resolucao_problemas"], ["Production Planner"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _producao_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- P&D/INOVAÇÃO ROLES -----
_pd_roles = [
    ("pesquisador", "Pesquisador", "pd", ["pleno_i", "pleno_ii", "senior_i", "senior_ii", "especialista"], "Conduz pesquisas científicas e tecnológicas para desenvolvimento de novos produtos", ["metodologia_cientifica", "excel"], ["pensamento_analitico", "curiosidade", "criatividade"], ["Researcher"]),
    ("analista_pd", "Analista de P&D", "pd", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Apoia projetos de pesquisa e desenvolvimento, documenta resultados", ["excel", "metodologia_cientifica"], ["pensamento_analitico", "organizacao", "atencao_detalhes"], ["R&D Analyst"]),
    ("cientista_pesquisa", "Cientista de Pesquisa", "pd", ["senior_i", "senior_ii", "especialista"], "Lidera pesquisas científicas avançadas e publicações técnicas", ["metodologia_cientifica"], ["pensamento_analitico", "criatividade", "inovacao", "comunicacao"], ["Research Scientist"]),
    ("gerente_inovacao", "Gerente de Inovação", "pd", ["gerente"], "Gerencia portfólio de projetos de inovação e parcerias tecnológicas", ["gestao_projetos", "excel"], ["lideranca", "visao_estrategica", "inovacao", "criatividade"], ["Innovation Manager"]),
    ("diretor_pd", "Diretor de P&D", "pd", ["diretor"], "Dirige estratégia de pesquisa e desenvolvimento da organização", ["gestao_projetos"], ["visao_estrategica", "lideranca", "inovacao", "tomada_decisao"], ["R&D Director", "VP R&D"]),
    ("analista_novos_produtos", "Analista de Novos Produtos", "pd", ["junior_ii", "pleno_i", "pleno_ii", "senior_i"], "Analisa viabilidade e desenvolve especificações de novos produtos", ["excel", "gestao_projetos"], ["pensamento_analitico", "criatividade", "orientacao_cliente"], ["New Products Analyst"]),
    ("engenheiro_desenvolvimento", "Engenheiro de Desenvolvimento", "pd", ["pleno_i", "pleno_ii", "senior_i", "senior_ii"], "Desenvolve e valida novos produtos e processos", ["autocad", "solidworks", "fmea"], ["pensamento_analitico", "criatividade", "resolucao_problemas"], ["Development Engineer"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _pd_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- ATENDIMENTO AO CLIENTE/CUSTOMER SUCCESS ROLES -----
_atendimento_roles = [
    ("atendente", "Atendente/Agente de Atendimento", "atendimento", ["junior_i", "junior_ii"], "Atende clientes por telefone, chat ou email, resolve demandas de primeiro nível", ["crm", "zendesk"], ["orientacao_cliente", "comunicacao", "empatia", "resiliencia"], ["Customer Service Agent", "Support Agent"]),
    ("analista_customer_success", "Analista de Customer Success", "atendimento", ["junior_ii", "pleno_i", "pleno_ii"], "Acompanha jornada do cliente, identifica oportunidades e previne churn", ["crm", "customer_success"], ["orientacao_cliente", "comunicacao", "proatividade", "pensamento_analitico"], ["CS Analyst"]),
    ("customer_success_manager", "Customer Success Manager", "atendimento", ["pleno_ii", "senior_i", "senior_ii"], "Gerencia carteira de clientes, garantindo sucesso e expansão", ["crm", "customer_success"], ["orientacao_cliente", "negociacao", "relacionamento_interpessoal", "visao_cliente"], ["CSM"]),
    ("coordenador_atendimento", "Coordenador de Atendimento", "atendimento", ["coordenador"], "Coordena equipe de atendimento e indicadores de qualidade", ["crm", "zendesk"], ["lideranca", "orientacao_cliente", "gestao_conflitos", "organizacao"], ["Customer Service Coordinator"]),
    ("gerente_customer_success", "Gerente de Customer Success", "atendimento", ["gerente"], "Gerencia área de Customer Success, estratégia de retenção e expansão", ["crm", "customer_success"], ["lideranca", "visao_estrategica", "orientacao_cliente", "tomada_decisao"], ["CS Manager", "Head of Customer Success"]),
    ("supervisor_sac", "Supervisor de SAC", "atendimento", ["coordenador"], "Supervisiona operações de SAC e qualidade de atendimento", ["crm", "zendesk"], ["lideranca", "orientacao_cliente", "gestao_conflitos", "senso_urgencia"], ["SAC Supervisor", "Call Center Supervisor"]),
    ("especialista_cx", "Especialista CX (Customer Experience)", "atendimento", ["senior_i", "senior_ii", "especialista"], "Mapeia jornada do cliente e implementa melhorias na experiência", ["crm", "ux_ui"], ["visao_cliente", "pensamento_analitico", "criatividade", "comunicacao"], ["CX Specialist", "Customer Experience Specialist"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _atendimento_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )

# ----- FACILITIES/INFRAESTRUTURA PREDIAL ROLES -----
_facilities_roles = [
    ("analista_facilities", "Analista de Facilities", "facilities", ["junior_ii", "pleno_i", "pleno_ii"], "Analisa e controla serviços de facilities, contratos e fornecedores", ["excel", "office_365"], ["organizacao", "negociacao", "atencao_detalhes"], ["Facilities Analyst"]),
    ("coordenador_facilities", "Coordenador de Facilities", "facilities", ["coordenador"], "Coordena operações de facilities, manutenção e serviços gerais", ["excel", "office_365"], ["lideranca", "organizacao", "negociacao", "resolucao_problemas"], ["Facilities Coordinator"]),
    ("gerente_facilities", "Gerente de Facilities", "facilities", ["gerente"], "Gerencia infraestrutura predial, orçamento e contratos de serviços", ["excel", "power_bi"], ["lideranca", "visao_estrategica", "negociacao", "gestao_stakeholders"], ["Facilities Manager"]),
    ("tecnico_manutencao_predial", "Técnico de Manutenção Predial", "facilities", ["junior_i", "junior_ii", "pleno_i"], "Executa manutenção preventiva e corretiva em instalações prediais", ["excel"], ["atencao_detalhes", "resolucao_problemas", "proatividade"], ["Building Maintenance Technician"]),
    ("supervisor_limpeza_copa", "Supervisor de Limpeza e Copa", "facilities", ["coordenador"], "Supervisiona equipes de limpeza e serviços de copa", ["excel"], ["lideranca", "organizacao", "atencao_detalhes"], ["Cleaning Supervisor", "Housekeeping Supervisor"]),
]

for role_id, nome, area_id, niveis, descricao, tecnicas, comportamentais, variantes in _facilities_roles:
    ROLES_CATALOG[role_id] = Role(
        id=role_id,
        nome=nome,
        area_id=area_id,
        niveis_aplicaveis=niveis,
        descricao=descricao,
        competencias_tecnicas=tecnicas,
        competencias_comportamentais=comportamentais,
        variantes_nome=variantes
    )


# =============================================================================
# SERVICE CLASS
# =============================================================================

class OrganizationCatalogService:
    """
    Service for managing and querying the organizational catalog.
    
    Provides comprehensive access to areas, roles, seniority levels,
    and competencies typical of Brazilian organizations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # -------------------------------------------------------------------------
    # AREAS
    # -------------------------------------------------------------------------
    
    def get_all_areas(self) -> list[dict[str, Any]]:
        """Get all organizational areas."""
        return [area.to_dict() for area in AREAS_CATALOG.values()]
    
    def get_area_by_id(self, area_id: str) -> dict[str, Any] | None:
        """Get a specific area by ID."""
        area = AREAS_CATALOG.get(area_id)
        return area.to_dict() if area else None
    
    def detect_area_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Detect the most likely area from a text (job title, description, etc).
        
        Args:
            text: Text to analyze
            
        Returns:
            Best matching area or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for area in AREAS_CATALOG.values():
            score = 0
            for keyword in area.palavras_chave:
                if keyword.lower() in text_lower:
                    score += 1
                    if keyword.lower() == text_lower:
                        score += 2
            
            if score > best_score:
                best_score = score
                best_match = area
        
        return best_match.to_dict() if best_match else None
    
    # -------------------------------------------------------------------------
    # SENIORITY LEVELS
    # -------------------------------------------------------------------------
    
    def get_all_seniority_levels(self) -> list[dict[str, Any]]:
        """Get all seniority levels ordered by hierarchy."""
        levels = list(SENIORITY_LEVELS.values())
        levels.sort(key=lambda x: x.ordem)
        return [level.to_dict() for level in levels]
    
    def get_seniority_by_id(self, seniority_id: str) -> dict[str, Any] | None:
        """Get a specific seniority level by ID."""
        level = SENIORITY_LEVELS.get(seniority_id)
        return level.to_dict() if level else None
    
    # -------------------------------------------------------------------------
    # ROLES
    # -------------------------------------------------------------------------
    
    def get_roles_by_area(self, area_id: str) -> list[dict[str, Any]]:
        """Get all roles for a specific area."""
        roles = [
            role.to_dict() for role in ROLES_CATALOG.values()
            if role.area_id == area_id
        ]
        return roles
    
    def get_all_roles(self) -> list[dict[str, Any]]:
        """Get all roles."""
        return [role.to_dict() for role in ROLES_CATALOG.values()]
    
    def get_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        """Get a specific role by ID."""
        role = ROLES_CATALOG.get(role_id)
        return role.to_dict() if role else None
    
    def get_role_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get a role by name, checking main name and variants.
        
        Args:
            name: Role name to search
            
        Returns:
            Matching role or None
        """
        name_lower = name.lower().strip()
        
        for role in ROLES_CATALOG.values():
            if role.nome.lower() == name_lower:
                return role.to_dict()
            
            for variant in role.variantes_nome:
                if variant.lower() == name_lower:
                    return role.to_dict()
        
        best_match = None
        best_score = 0.6
        
        for role in ROLES_CATALOG.values():
            score = SequenceMatcher(None, role.nome.lower(), name_lower).ratio()
            if score > best_score:
                best_score = score
                best_match = role
            
            for variant in role.variantes_nome:
                score = SequenceMatcher(None, variant.lower(), name_lower).ratio()
                if score > best_score:
                    best_score = score
                    best_match = role
        
        return best_match.to_dict() if best_match else None
    
    # -------------------------------------------------------------------------
    # TECHNICAL SKILLS
    # -------------------------------------------------------------------------
    
    def get_technical_skills_by_area(self, area_id: str) -> list[dict[str, Any]]:
        """Get all technical skills for a specific area."""
        skills = [
            skill.to_dict() for skill in TECHNICAL_SKILLS.values()
            if area_id in skill.areas
        ]
        return skills
    
    def get_all_technical_skills(self) -> list[dict[str, Any]]:
        """Get all technical skills."""
        return [skill.to_dict() for skill in TECHNICAL_SKILLS.values()]
    
    def get_technical_skill_by_id(self, skill_id: str) -> dict[str, Any] | None:
        """Get a specific technical skill by ID."""
        skill = TECHNICAL_SKILLS.get(skill_id)
        return skill.to_dict() if skill else None
    
    # -------------------------------------------------------------------------
    # BEHAVIORAL SKILLS
    # -------------------------------------------------------------------------
    
    def get_all_behavioral_skills(self) -> list[dict[str, Any]]:
        """Get all behavioral competencies."""
        return [skill.to_dict() for skill in BEHAVIORAL_SKILLS.values()]
    
    def get_behavioral_skill_by_id(self, skill_id: str) -> dict[str, Any] | None:
        """Get a specific behavioral skill by ID."""
        skill = BEHAVIORAL_SKILLS.get(skill_id)
        return skill.to_dict() if skill else None
    
    def get_behavioral_skills_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get behavioral skills by category."""
        return [
            skill.to_dict() for skill in BEHAVIORAL_SKILLS.values()
            if skill.categoria == category
        ]
    
    # -------------------------------------------------------------------------
    # SUGGESTIONS
    # -------------------------------------------------------------------------
    
    def suggest_skills_for_role(
        self,
        role_name: str,
        seniority_id: str | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Suggest technical and behavioral skills for a role.
        
        Args:
            role_name: Name of the role
            seniority_id: Optional seniority level to adjust suggestions
            
        Returns:
            Dict with 'technical' and 'behavioral' skill lists
        """
        role_data = self.get_role_by_name(role_name)
        
        if not role_data:
            return {"technical": [], "behavioral": []}
        
        technical_skills = []
        for skill_id in role_data.get("competencias_tecnicas", []):
            skill = self.get_technical_skill_by_id(skill_id)
            if skill:
                technical_skills.append(skill)
        
        area_skills = self.get_technical_skills_by_area(role_data.get("area_id", ""))
        for skill in area_skills[:10]:
            if skill["id"] not in [s["id"] for s in technical_skills]:
                technical_skills.append(skill)
        
        behavioral_skills = []
        for skill_id in role_data.get("competencias_comportamentais", []):
            skill = self.get_behavioral_skill_by_id(skill_id)
            if skill:
                behavioral_skills.append(skill)
        
        if seniority_id:
            seniority = self.get_seniority_by_id(seniority_id)
            if seniority and seniority.get("ordem", 0) >= 10:
                leadership_skills = ["lideranca", "gestao_stakeholders", "visao_estrategica", "tomada_decisao"]
                for skill_id in leadership_skills:
                    skill = self.get_behavioral_skill_by_id(skill_id)
                    if skill and skill["id"] not in [s["id"] for s in behavioral_skills]:
                        behavioral_skills.append(skill)
        
        return {
            "technical": technical_skills,
            "behavioral": behavioral_skills
        }
    
    def search_skills(self, query: str) -> dict[str, list[dict[str, Any]]]:
        """
        Search for skills by name or keyword.
        
        Args:
            query: Search query
            
        Returns:
            Dict with 'technical' and 'behavioral' matching skills
        """
        if not query or len(query) < 2:
            return {"technical": [], "behavioral": []}
        
        query_lower = query.lower()
        
        technical_matches = []
        for skill in TECHNICAL_SKILLS.values():
            if query_lower in skill.nome.lower():
                technical_matches.append((skill, 1.0))
                continue
            
            for keyword in skill.palavras_chave:
                if query_lower in keyword.lower():
                    technical_matches.append((skill, 0.8))
                    break
            else:
                if query_lower in skill.descricao.lower():
                    technical_matches.append((skill, 0.5))
        
        behavioral_matches = []
        for skill in BEHAVIORAL_SKILLS.values():
            if query_lower in skill.nome.lower():
                behavioral_matches.append((skill, 1.0))
                continue
            
            for sub in skill.subcategorias:
                if query_lower in sub.lower():
                    behavioral_matches.append((skill, 0.8))
                    break
            else:
                if query_lower in skill.descricao.lower():
                    behavioral_matches.append((skill, 0.5))
        
        technical_matches.sort(key=lambda x: x[1], reverse=True)
        behavioral_matches.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "technical": [s.to_dict() for s, _ in technical_matches[:20]],
            "behavioral": [s.to_dict() for s, _ in behavioral_matches[:20]]
        }
    
    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    
    def get_catalog_summary(self) -> dict[str, Any]:
        """
        Get a complete summary of the catalog for review.
        
        Returns:
            Complete catalog summary with counts and samples
        """
        areas = self.get_all_areas()
        seniority_levels = self.get_all_seniority_levels()
        all_roles = self.get_all_roles()
        all_technical_skills = self.get_all_technical_skills()
        all_behavioral_skills = self.get_all_behavioral_skills()
        
        roles_by_area = {}
        for area in areas:
            area_roles = self.get_roles_by_area(area["id"])
            roles_by_area[area["id"]] = {
                "area_nome": area["nome"],
                "quantidade_cargos": len(area_roles),
                "cargos": [r["nome"] for r in area_roles]
            }
        
        technical_by_area = {}
        for area in areas:
            area_skills = self.get_technical_skills_by_area(area["id"])
            technical_by_area[area["id"]] = {
                "area_nome": area["nome"],
                "quantidade_skills": len(area_skills),
                "skills": [s["nome"] for s in area_skills]
            }
        
        behavioral_by_category = {}
        for skill in all_behavioral_skills:
            cat = skill["categoria"]
            if cat not in behavioral_by_category:
                behavioral_by_category[cat] = []
            behavioral_by_category[cat].append(skill["nome"])
        
        return {
            "resumo": {
                "total_areas": len(areas),
                "total_niveis_senioridade": len(seniority_levels),
                "total_cargos": len(all_roles),
                "total_competencias_tecnicas": len(all_technical_skills),
                "total_competencias_comportamentais": len(all_behavioral_skills)
            },
            "areas": areas,
            "niveis_senioridade": seniority_levels,
            "cargos_por_area": roles_by_area,
            "competencias_tecnicas_por_area": technical_by_area,
            "competencias_comportamentais_por_categoria": behavioral_by_category,
            "todos_cargos": all_roles,
            "todas_competencias_tecnicas": all_technical_skills,
            "todas_competencias_comportamentais": all_behavioral_skills
        }


organization_catalog_service = OrganizationCatalogService()
