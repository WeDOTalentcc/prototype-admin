"""
CÓDIGO PYTHON COMPLETO: Intent Classifier e Context Manager
Projeto: LIA - Agente Conversacional de Recrutamento
Tecnologias: Python 3.11, LangChain, Gemini 1.5, Pydantic
Autor: Time de Desenvolvimento LIA
Data: Novembro 2025

Este arquivo contém a implementação completa e funcional do Intent Classifier
e Context Manager, os dois componentes fundamentais da arquitetura conversacional da LIA.
"""

import os
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory


# ============================================================================
# PARTE 1: MODELOS DE DADOS (Pydantic)
# ============================================================================

class IntentType(str, Enum):
    """Tipos de intenção possíveis do usuário"""
    PROVIDE_JOB_INFO = "provide_job_info"  # Fornecendo informações sobre a vaga
    ASK_QUESTION = "ask_question"  # Fazendo uma pergunta
    REQUEST_CHANGE = "request_change"  # Pedindo alteração em algo já definido
    REQUEST_SUMMARY = "request_summary"  # Pedindo resumo do que foi feito
    OUT_OF_SCOPE = "out_of_scope"  # Pergunta fora do escopo de recrutamento


class Intent(BaseModel):
    """Modelo de dados para a intenção classificada"""
    intent_type: IntentType = Field(description="Tipo de intenção identificada")
    confidence: float = Field(description="Confiança da classificação (0.0 a 1.0)", ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict, description="Entidades extraídas da mensagem")
    question_topic: Optional[str] = Field(default=None, description="Tópico da pergunta (se intent_type=ask_question)")
    change_target: Optional[str] = Field(default=None, description="Alvo da mudança (se intent_type=request_change)")
    
    class Config:
        use_enum_values = True


class SeniorityLevel(str, Enum):
    """Níveis de senioridade"""
    JUNIOR = "Júnior"
    PLENO = "Pleno"
    SENIOR = "Sênior"
    ESPECIALISTA = "Especialista"
    COORDENADOR = "Coordenador"
    GERENTE = "Gerente"


class WorkModel(str, Enum):
    """Modelos de trabalho"""
    PRESENCIAL = "Presencial"
    REMOTO = "Remoto"
    HIBRIDO = "Híbrido"


class ContractType(str, Enum):
    """Tipos de contratação"""
    CLT = "CLT"
    PJ = "PJ"
    ESTAGIO = "Estágio"
    TEMPORARIO = "Temporário"


class TechnicalRequirement(BaseModel):
    """Requisito técnico com nível de proficiência"""
    technology: str = Field(description="Nome da tecnologia/ferramenta")
    is_mandatory: bool = Field(description="Se é obrigatório ou desejável")
    proficiency_level: Optional[str] = Field(default=None, description="Nível de proficiência esperado (Básico, Intermediário, Avançado)")
    years_experience: Optional[int] = Field(default=None, description="Anos de experiência necessários")


class BehavioralCompetency(BaseModel):
    """Competência comportamental"""
    competency_name: str = Field(description="Nome da competência")
    is_mandatory: bool = Field(description="Se é obrigatória ou desejável")
    description: Optional[str] = Field(default=None, description="Descrição da competência")


class InterviewStage(BaseModel):
    """Etapa de entrevista"""
    stage_name: str = Field(description="Nome da etapa (ex: Entrevista RH, Entrevista Técnica)")
    interviewer: str = Field(description="Quem conduz a entrevista")
    duration_minutes: Optional[int] = Field(default=None, description="Duração estimada em minutos")
    format: Optional[str] = Field(default=None, description="Formato (presencial, online, etc.)")


class JobVacancyState(BaseModel):
    """
    Estado completo da vaga sendo criada.
    Este é o modelo central que mantém TODAS as informações coletadas durante a conversa.
    """
    # Identificação
    vacancy_id: Optional[str] = Field(default=None, description="ID da vaga no ATS")
    
    # Informações Básicas
    job_title: Optional[str] = Field(default=None, description="Título da vaga")
    department: Optional[str] = Field(default=None, description="Departamento")
    seniority: Optional[SeniorityLevel] = Field(default=None, description="Nível de senioridade")
    work_model: Optional[WorkModel] = Field(default=None, description="Modelo de trabalho")
    location: Optional[str] = Field(default=None, description="Localização")
    is_confidential: bool = Field(default=False, description="Se a vaga é confidencial")
    
    # Remuneração e Benefícios
    salary_min: Optional[float] = Field(default=None, description="Salário mínimo")
    salary_max: Optional[float] = Field(default=None, description="Salário máximo")
    bonus_min: Optional[float] = Field(default=None, description="Bônus mínimo")
    bonus_max: Optional[float] = Field(default=None, description="Bônus máximo")
    benefits: List[str] = Field(default_factory=list, description="Lista de benefícios")
    
    # Estrutura Organizacional
    hiring_manager: Optional[str] = Field(default=None, description="Nome do gestor requisitante")
    team_size: Optional[int] = Field(default=None, description="Tamanho da equipe")
    reports_to: Optional[str] = Field(default=None, description="Linha de reporte")
    
    # Requisitos
    technical_requirements: List[TechnicalRequirement] = Field(default_factory=list, description="Requisitos técnicos")
    behavioral_competencies: List[BehavioralCompetency] = Field(default_factory=list, description="Competências comportamentais")
    languages: Dict[str, str] = Field(default_factory=dict, description="Idiomas e níveis (ex: {'Inglês': 'Avançado'})")
    years_experience: Optional[int] = Field(default=None, description="Anos de experiência total necessários")
    
    # Descrição da Vaga
    job_description: Optional[str] = Field(default=None, description="Descrição completa da vaga")
    responsibilities: List[str] = Field(default_factory=list, description="Principais responsabilidades")
    
    # Processo Seletivo
    interview_stages: List[InterviewStage] = Field(default_factory=list, description="Etapas de entrevista")
    screening_questions: List[str] = Field(default_factory=list, description="Perguntas de screening")
    has_technical_test: bool = Field(default=False, description="Se tem teste técnico")
    has_behavioral_assessment: bool = Field(default=False, description="Se tem assessment comportamental")
    
    # Cronograma
    expected_start_date: Optional[datetime] = Field(default=None, description="Data prevista de início")
    shortlist_delivery_date: Optional[datetime] = Field(default=None, description="Data prevista de entrega da shortlist")
    estimated_duration_weeks: Optional[int] = Field(default=None, description="Duração estimada do processo em semanas")
    
    # Estratégia de Busca
    target_sectors: List[str] = Field(default_factory=list, description="Setores prioritários")
    target_company_sizes: List[str] = Field(default_factory=list, description="Tamanhos de empresa prioritários")
    required_market_knowledge: Optional[str] = Field(default=None, description="Conhecimento de mercado específico")
    
    # Metadados
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data de última atualização")
    completion_percentage: float = Field(default=0.0, description="Percentual de conclusão (0.0 a 100.0)")
    
    class Config:
        use_enum_values = True


# ============================================================================
# PARTE 2: INTENT CLASSIFIER
# ============================================================================

class IntentClassifier:
    """
    Classificador de intenções usando Gemini com structured output.
    
    Responsável por:
    1. Identificar a intenção do usuário (provide_job_info, ask_question, etc.)
    2. Extrair entidades mencionadas na mensagem
    3. Retornar um objeto Intent estruturado
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Inicializa o Intent Classifier.
        
        Args:
            gemini_api_key: API key do Google AI. Se None, usa variável de ambiente GOOGLE_API_KEY.
        """
        self.api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Inicializa o modelo Gemini com structured output
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.1,  # Baixa temperatura para respostas mais determinísticas
        )
        
        # Prompt template para classificação de intenção
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{user_message}")
        ])
    
    def _get_system_prompt(self) -> str:
        """Retorna o system prompt para classificação de intenção"""
        return """Você é um classificador de intenções especializado em conversas de recrutamento.

Sua tarefa é analisar cada mensagem do recrutador e identificar:
1. A INTENÇÃO principal (intent_type)
2. A CONFIANÇA da classificação (confidence)
3. As ENTIDADES mencionadas (entities)

TIPOS DE INTENÇÃO:
- provide_job_info: O recrutador está fornecendo informações sobre a vaga (título, salário, requisitos, etc.)
- ask_question: O recrutador está fazendo uma pergunta
- request_change: O recrutador está pedindo para alterar algo já definido
- request_summary: O recrutador está pedindo um resumo do que foi feito
- out_of_scope: Pergunta fora do escopo de recrutamento

ENTIDADES A EXTRAIR (quando mencionadas):
- job_title: Título da vaga
- department: Departamento
- seniority: Nível de senioridade (Júnior, Pleno, Sênior, etc.)
- work_model: Modelo de trabalho (Presencial, Remoto, Híbrido)
- location: Localização
- salary_min: Salário mínimo (número)
- salary_max: Salário máximo (número)
- bonus_min: Bônus mínimo (número)
- bonus_max: Bônus máximo (número)
- benefits: Lista de benefícios
- hiring_manager: Nome do gestor
- technical_requirements: Tecnologias/ferramentas mencionadas
- behavioral_competencies: Competências comportamentais
- languages: Idiomas mencionados
- years_experience: Anos de experiência

EXEMPLOS:

Mensagem: "Backend Sênior, remoto, 12 a 18k"
Intent: provide_job_info
Entities: {job_title: "Backend", seniority: "Sênior", work_model: "Remoto", salary_min: 12000, salary_max: 18000}

Mensagem: "Quanto tempo vai levar para fechar essa vaga?"
Intent: ask_question
question_topic: "cronograma"

Mensagem: "Pode remover GitLab CI dos requisitos obrigatórios?"
Intent: request_change
change_target: "requisitos técnicos"
Entities: {technical_requirements: ["GitLab CI"]}

IMPORTANTE:
- Extraia TODAS as entidades mencionadas, mesmo que sejam múltiplas
- Normalize valores (ex: "12k" → 12000)
- Seja generoso na extração, mas preciso na classificação
- Confidence deve ser alta (>0.8) quando a intenção é clara
"""
    
    def classify(self, user_message: str, current_state: Optional[JobVacancyState] = None) -> Intent:
        """
        Classifica a intenção de uma mensagem do usuário.
        
        Args:
            user_message: Mensagem do recrutador
            current_state: Estado atual da vaga (opcional, para contexto)
        
        Returns:
            Intent: Objeto Intent com a classificação e entidades extraídas
        """
        # Adiciona contexto do estado atual, se disponível
        context = ""
        if current_state:
            filled_fields = []
            if current_state.job_title:
                filled_fields.append(f"Título: {current_state.job_title}")
            if current_state.seniority:
                filled_fields.append(f"Senioridade: {current_state.seniority}")
            if current_state.salary_min and current_state.salary_max:
                filled_fields.append(f"Salário: R$ {current_state.salary_min:,.0f} a R$ {current_state.salary_max:,.0f}")
            
            if filled_fields:
                context = f"\n\nCONTEXTO (informações já coletadas):\n" + "\n".join(filled_fields)
        
        # Monta o prompt
        prompt = self.prompt_template.format_messages(
            user_message=user_message + context
        )
        
        # Chama o Gemini com structured output
        structured_llm = self.llm.with_structured_output(Intent)
        result = structured_llm.invoke(prompt)
        
        return result
    
    def extract_entities(self, user_message: str) -> Dict[str, Any]:
        """
        Extrai apenas as entidades de uma mensagem, sem classificar intenção.
        Útil para casos onde já sabemos a intenção.
        
        Args:
            user_message: Mensagem do recrutador
        
        Returns:
            Dict com as entidades extraídas
        """
        intent = self.classify(user_message)
        return intent.entities


# ============================================================================
# PARTE 3: CONTEXT MANAGER
# ============================================================================

class ContextManager:
    """
    Gerenciador de contexto e estado conversacional.
    
    Responsável por:
    1. Manter o estado da vaga (JobVacancyState)
    2. Atualizar o estado com novas informações
    3. Calcular o percentual de conclusão
    4. Manter o histórico da conversa
    5. Persistir o estado no banco de dados
    """
    
    def __init__(self, vacancy_id: Optional[str] = None):
        """
        Inicializa o Context Manager.
        
        Args:
            vacancy_id: ID da vaga (se já existe). Se None, cria uma nova vaga.
        """
        self.vacancy_id = vacancy_id or self._generate_vacancy_id()
        self.state = JobVacancyState(vacancy_id=self.vacancy_id)
        
        # Memória conversacional (histórico de mensagens)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Campos obrigatórios para calcular completion
        self.mandatory_fields = [
            "job_title", "department", "seniority", "work_model", "location",
            "salary_min", "salary_max", "hiring_manager", "job_description",
            "expected_start_date", "shortlist_delivery_date"
        ]
    
    def _generate_vacancy_id(self) -> str:
        """Gera um ID único para a vaga"""
        import uuid
        return f"VAC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def update_state(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza o estado da vaga com novas entidades extraídas.
        
        Args:
            entities: Dicionário com as entidades extraídas pelo Intent Classifier
        
        Returns:
            Dict com informações sobre o que foi atualizado
        """
        updated_fields = []
        
        # Atualiza campos simples
        simple_fields = [
            "job_title", "department", "location", "hiring_manager",
            "job_description", "years_experience", "team_size", "reports_to",
            "required_market_knowledge"
        ]
        
        for field in simple_fields:
            if field in entities and entities[field] is not None:
                setattr(self.state, field, entities[field])
                updated_fields.append(field)
        
        # Atualiza enums
        if "seniority" in entities:
            try:
                self.state.seniority = SeniorityLevel(entities["seniority"])
                updated_fields.append("seniority")
            except ValueError:
                pass  # Valor inválido, ignora
        
        if "work_model" in entities:
            try:
                self.state.work_model = WorkModel(entities["work_model"])
                updated_fields.append("work_model")
            except ValueError:
                pass
        
        # Atualiza valores numéricos
        numeric_fields = ["salary_min", "salary_max", "bonus_min", "bonus_max", "estimated_duration_weeks"]
        for field in numeric_fields:
            if field in entities and entities[field] is not None:
                setattr(self.state, field, float(entities[field]))
                updated_fields.append(field)
        
        # Atualiza listas
        if "benefits" in entities and isinstance(entities["benefits"], list):
            self.state.benefits.extend(entities["benefits"])
            updated_fields.append("benefits")
        
        if "responsibilities" in entities and isinstance(entities["responsibilities"], list):
            self.state.responsibilities.extend(entities["responsibilities"])
            updated_fields.append("responsibilities")
        
        if "target_sectors" in entities and isinstance(entities["target_sectors"], list):
            self.state.target_sectors.extend(entities["target_sectors"])
            updated_fields.append("target_sectors")
        
        # Atualiza requisitos técnicos
        if "technical_requirements" in entities:
            for tech in entities["technical_requirements"]:
                if isinstance(tech, dict):
                    self.state.technical_requirements.append(TechnicalRequirement(**tech))
                elif isinstance(tech, str):
                    self.state.technical_requirements.append(
                        TechnicalRequirement(technology=tech, is_mandatory=True)
                    )
            updated_fields.append("technical_requirements")
        
        # Atualiza competências comportamentais
        if "behavioral_competencies" in entities:
            for comp in entities["behavioral_competencies"]:
                if isinstance(comp, dict):
                    self.state.behavioral_competencies.append(BehavioralCompetency(**comp))
                elif isinstance(comp, str):
                    self.state.behavioral_competencies.append(
                        BehavioralCompetency(competency_name=comp, is_mandatory=True)
                    )
            updated_fields.append("behavioral_competencies")
        
        # Atualiza idiomas
        if "languages" in entities and isinstance(entities["languages"], dict):
            self.state.languages.update(entities["languages"])
            updated_fields.append("languages")
        
        # Atualiza datas
        if "expected_start_date" in entities:
            # Aqui você implementaria parsing de data
            # Por simplicidade, assumindo que já vem como datetime
            if isinstance(entities["expected_start_date"], datetime):
                self.state.expected_start_date = entities["expected_start_date"]
                updated_fields.append("expected_start_date")
        
        # Atualiza flags booleanas
        if "is_confidential" in entities:
            self.state.is_confidential = bool(entities["is_confidential"])
            updated_fields.append("is_confidential")
        
        if "has_technical_test" in entities:
            self.state.has_technical_test = bool(entities["has_technical_test"])
            updated_fields.append("has_technical_test")
        
        if "has_behavioral_assessment" in entities:
            self.state.has_behavioral_assessment = bool(entities["has_behavioral_assessment"])
            updated_fields.append("has_behavioral_assessment")
        
        # Atualiza timestamp
        self.state.updated_at = datetime.now()
        
        # Recalcula completion
        old_completion = self.state.completion_percentage
        new_completion = self.calculate_completion()
        self.state.completion_percentage = new_completion
        
        return {
            "updated_fields": updated_fields,
            "fields_count": len(updated_fields),
            "old_completion": old_completion,
            "new_completion": new_completion,
            "completion_delta": new_completion - old_completion
        }
    
    def calculate_completion(self) -> float:
        """
        Calcula o percentual de conclusão da vaga.
        
        Returns:
            float: Percentual de 0.0 a 100.0
        """
        filled_count = 0
        
        for field in self.mandatory_fields:
            value = getattr(self.state, field, None)
            if value is not None:
                # Para listas, verifica se não está vazia
                if isinstance(value, list):
                    if len(value) > 0:
                        filled_count += 1
                else:
                    filled_count += 1
        
        # Também considera campos opcionais importantes
        optional_important_fields = [
            "technical_requirements", "behavioral_competencies", "benefits",
            "screening_questions", "interview_stages"
        ]
        
        optional_filled = 0
        for field in optional_important_fields:
            value = getattr(self.state, field, None)
            if value and len(value) > 0:
                optional_filled += 1
        
        # Peso: 70% campos obrigatórios, 30% campos opcionais importantes
        mandatory_percentage = (filled_count / len(self.mandatory_fields)) * 70
        optional_percentage = (optional_filled / len(optional_important_fields)) * 30
        
        return round(mandatory_percentage + optional_percentage, 1)
    
    def get_missing_fields(self) -> List[str]:
        """
        Retorna lista de campos obrigatórios que ainda não foram preenchidos.
        
        Returns:
            List[str]: Lista de nomes de campos faltantes
        """
        missing = []
        
        for field in self.mandatory_fields:
            value = getattr(self.state, field, None)
            if value is None or (isinstance(value, list) and len(value) == 0):
                missing.append(field)
        
        return missing
    
    def add_to_history(self, role: str, content: str):
        """
        Adiciona uma mensagem ao histórico conversacional.
        
        Args:
            role: 'human' ou 'ai'
            content: Conteúdo da mensagem
        """
        if role == "human":
            self.memory.chat_memory.add_user_message(content)
        elif role == "ai":
            self.memory.chat_memory.add_ai_message(content)
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Retorna o histórico de mensagens.
        
        Returns:
            List[Dict]: Lista de mensagens com 'role' e 'content'
        """
        messages = self.memory.chat_memory.messages
        return [
            {"role": "human" if msg.type == "human" else "ai", "content": msg.content}
            for msg in messages
        ]
    
    def get_state_summary(self) -> str:
        """
        Retorna um resumo textual do estado atual da vaga.
        
        Returns:
            str: Resumo formatado
        """
        summary_parts = []
        
        summary_parts.append(f"📋 **Vaga ID:** {self.state.vacancy_id}")
        summary_parts.append(f"📊 **Conclusão:** {self.state.completion_percentage:.1f}%")
        summary_parts.append("")
        
        if self.state.job_title:
            summary_parts.append(f"**Título:** {self.state.job_title}")
        
        if self.state.seniority:
            summary_parts.append(f"**Senioridade:** {self.state.seniority}")
        
        if self.state.department:
            summary_parts.append(f"**Departamento:** {self.state.department}")
        
        if self.state.work_model:
            summary_parts.append(f"**Modelo de Trabalho:** {self.state.work_model}")
        
        if self.state.location:
            summary_parts.append(f"**Localização:** {self.state.location}")
        
        if self.state.salary_min and self.state.salary_max:
            summary_parts.append(f"**Salário:** R$ {self.state.salary_min:,.0f} a R$ {self.state.salary_max:,.0f}")
        
        if self.state.hiring_manager:
            summary_parts.append(f"**Gestor:** {self.state.hiring_manager}")
        
        if self.state.technical_requirements:
            summary_parts.append(f"\n**Requisitos Técnicos:** {len(self.state.technical_requirements)} tecnologias")
        
        if self.state.behavioral_competencies:
            summary_parts.append(f"**Competências Comportamentais:** {len(self.state.behavioral_competencies)} competências")
        
        missing = self.get_missing_fields()
        if missing:
            summary_parts.append(f"\n**Campos Faltantes:** {', '.join(missing[:5])}" + ("..." if len(missing) > 5 else ""))
        
        return "\n".join(summary_parts)
    
    def save_to_database(self):
        """
        Persiste o estado atual no banco de dados.
        
        Nota: Esta é uma implementação de exemplo. Na prática, você implementaria
        a lógica de conexão com PostgreSQL e salvamento.
        """
        # TODO: Implementar persistência no PostgreSQL
        # Exemplo:
        # db.session.merge(self.state)
        # db.session.commit()
        print(f"[ContextManager] Estado da vaga {self.vacancy_id} salvo no banco de dados")


# ============================================================================
# PARTE 4: EXEMPLO DE USO
# ============================================================================

def example_usage():
    """Exemplo de uso do Intent Classifier e Context Manager"""
    
    print("=" * 80)
    print("EXEMPLO DE USO: Intent Classifier + Context Manager")
    print("=" * 80)
    print()
    
    # Inicializa os componentes
    classifier = IntentClassifier()
    context = ContextManager()
    
    print(f"✅ Vaga criada: {context.vacancy_id}")
    print(f"📊 Conclusão inicial: {context.state.completion_percentage}%")
    print()
    
    # Simulação de conversa
    messages = [
        "Backend Sênior, remoto, 12 a 18k",
        "Quanto tempo vai levar para fechar essa vaga?",
        "O departamento é Tecnologia",
        "Pode remover GitLab CI dos requisitos obrigatórios?",
        "Me dá um resumo do que temos até agora"
    ]
    
    for i, user_message in enumerate(messages, 1):
        print(f"🗣️  **Recrutador:** {user_message}")
        
        # Classifica a intenção
        intent = classifier.classify(user_message, context.state)
        
        print(f"   🧠 Intent: {intent.intent_type} (confidence: {intent.confidence:.2f})")
        
        if intent.entities:
            print(f"   📦 Entities: {intent.entities}")
        
        # Atualiza o contexto se for provide_job_info
        if intent.intent_type == IntentType.PROVIDE_JOB_INFO:
            update_info = context.update_state(intent.entities)
            print(f"   ✅ Atualizados {update_info['fields_count']} campos")
            print(f"   📊 Conclusão: {update_info['old_completion']:.1f}% → {update_info['new_completion']:.1f}%")
        
        # Adiciona ao histórico
        context.add_to_history("human", user_message)
        
        print()
    
    # Mostra resumo final
    print("=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print()
    print(context.get_state_summary())
    print()
    
    # Mostra campos faltantes
    missing = context.get_missing_fields()
    print(f"📝 Campos obrigatórios faltantes ({len(missing)}):")
    for field in missing[:10]:
        print(f"   - {field}")
    if len(missing) > 10:
        print(f"   ... e mais {len(missing) - 10} campos")


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    # Certifique-se de ter a variável de ambiente GOOGLE_API_KEY configurada
    # export GOOGLE_API_KEY="sua-api-key-aqui"
    
    example_usage()
