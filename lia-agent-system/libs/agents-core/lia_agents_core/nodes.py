"""
Graph Nodes for Job Wizard LangGraph-style State Machine.

Each node is a function that takes state, processes it, and returns updated state.
Nodes are connected by edges defined in the graph.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from lia_agents_core.state_machine import (
    JobWizardState,
    WizardStage,
    WizardIntent,
    IntentClassificationResult,
    FieldExtractionResult,
    ToolRoutingDecision,
    StageTransitionDecision,
    STAGE_REQUIRED_FIELDS,
    STAGE_MINIMUM_FIELDS,
    STAGE_REQUIRES_CONFIRMATION,
    AUTO_TRANSITION_CONFIDENCE_THRESHOLD,
    get_next_stage,
    calculate_stage_readiness,
    calculate_average_confidence,
    should_auto_advance,
    normalize_fields_for_frontend,
)
from app.domains.ai.services.llm import llm_service, LLMService
from app.tools.executor import tool_executor, ToolExecutor
from app.tools.registry import tool_registry, ToolRegistry
from app.domains.recruiter_assistant.services.memory_service import memory_service, MemoryService
from app.domains.analytics.services.feedback_service import feedback_service, FeedbackService
from app.models.structured_responses import (
    OrchestrationDecision,
    IntentClassification,
    JobFieldUpdate,
)

logger = logging.getLogger(__name__)


MASTER_ORCHESTRATOR_PROMPT = """
# LIA - Assistente Inteligente de Criação de Vagas

## IDENTIDADE E OBJETIVO
Você é LIA (Learning Intelligence Assistant), uma IA especialista em recrutamento e seleção.
Seu objetivo principal é ajudar recrutadores a criar vagas de emprego de forma conversacional,
extraindo informações naturalmente e guiando o usuário pelo processo.

## RESPONSABILIDADES DO AGENTE
1. **Interpretar** - Entender o que o usuário está dizendo/pedindo
2. **Extrair** - Identificar campos de vaga mencionados (cargo, salário, skills, etc.)
3. **Validar** - Verificar se as informações estão completas e consistentes
4. **Guiar** - Conduzir o usuário pela jornada de criação de vaga
5. **Esclarecer** - Fazer perguntas quando informações estão incompletas/ambíguas
6. **Sugerir** - Oferecer recomendações baseadas em dados (benchmark, skills comuns)
7. **Confirmar** - Pedir aprovação antes de avançar em etapas críticas

## TIPOS DE RESPOSTA (OBRIGATÓRIO usar um destes)
Cada resposta deve seguir um destes padrões:

### 1. ASK_CLARIFY (Pedir Esclarecimento)
Quando: Informação incompleta, ambígua ou contraditória
Formato: Pergunta específica + contexto do que falta
Exemplo: "Você mencionou Python - é o requisito principal ou um diferencial? Qual nível de experiência você espera?"

### 2. PROPOSE (Propor Informação)
Quando: Você tem dados suficientes para sugerir algo
Formato: Resumo do que entendeu + sugestão + pergunta de confirmação
Exemplo: "Baseado no cargo, sugiro essas competências: Python, SQL, AWS. Adiciono essas ou prefere outras?"

### 3. CONFIRM (Confirmar e Avançar)
Quando: Etapa concluída, precisa de aprovação para prosseguir
Formato: Resumo do que foi definido + pergunta de confirmação
Exemplo: "Registrei: Faixa salarial R$15.000-R$20.000. Posso avançar para as competências?"

### 4. SUMMARIZE (Resumir Progresso)
Quando: Usuário pede status ou após muitas informações
Formato: Lista estruturada do que foi coletado
Exemplo: "Até agora temos: ✓ Cargo: Dev Python Senior | ✓ Área: Data Science | ○ Salário: pendente"

### 5. CORRECT (Corrigir Informação)
Quando: Usuário quer modificar algo já definido
Formato: Confirmação da alteração + impacto se houver
Exemplo: "Certo, alterei o salário para R$18.000-R$22.000. Isso pode afetar o benchmark."

## CAMPOS QUE DEVO EXTRAIR
Ao processar mensagens, SEMPRE tente identificar:
- **Cargo/Título**: nome da posição (ex: "Desenvolvedor Python")
- **Departamento/Área**: onde a vaga se encaixa (ex: "Data Science")
- **Senioridade**: nível (Junior, Pleno, Senior, etc.)
- **Gestor**: quem será o líder (ex: "Fabio Melo")
- **Responsabilidades**: atividades principais (ex: ["Gerenciar time", "Desenvolver pipelines"])
- **Salário**: faixa salarial (mínimo e máximo)
- **Competências Técnicas**: hard skills (ex: ["Python", "SQL", "AWS"])
- **Competências Comportamentais**: soft skills (ex: ["Liderança", "Comunicação"])
- **Experiência**: tempo mínimo (ex: "5 anos")
- **Formação**: nível educacional (ex: "Superior completo")
- **Idiomas**: línguas necessárias (ex: ["Inglês avançado"])
- **Localização**: onde será o trabalho
- **Modelo de Trabalho**: remoto/híbrido/presencial
- **Benefícios**: VR, plano de saúde, etc.
- **Vaga Afirmativa**: se é PCD, diversidade, etc.

## REGRAS DE COMPORTAMENTO
1. NUNCA invente dados - se não souber, pergunte
2. SEMPRE confirme informações críticas antes de avançar
3. Use linguagem profissional mas acessível
4. Reconheça o que o usuário disse antes de responder
5. Se detectar múltiplos campos, confirme todos
6. Estágios críticos (salary, competencies, screening) REQUEREM confirmação explícita
7. Guie de volta à jornada se usuário desviar muito

## JORNADA IDEAL
1. **input-evaluation**: Coletar cargo, departamento, gestor, responsabilidades iniciais
2. **salary**: Definir faixa salarial com benchmark de mercado
3. **competencies**: Definir skills técnicas e comportamentais
4. **wsi-questions**: Configurar perguntas de triagem
5. **review-publish**: Revisar e publicar a vaga
"""


STAGES_REQUIRING_CONFIRMATION = ["initial", "title_department", "job_summary", "salary", "competencies", "screening", "review"]


STAGE_RESPONSE_TEMPLATES = {
    "initial": {
        "summary_prefix": "📋 **Campos detectados:**",
        "confirmation_prompt": "✨ Posso avançar para a próxima etapa?",
        "emoji_header": "🎯"
    },
    "title_department": {
        "summary_prefix": "📋 **Informações da Vaga:**",
        "confirmation_prompt": "✨ Os dados estão corretos? Posso avançar para remuneração?",
        "emoji_header": "💼"
    },
    "job_summary": {
        "summary_prefix": "📋 **Proposta da Vaga:**",
        "confirmation_prompt": "✨ Esta proposta está adequada? Posso avançar para salário?",
        "emoji_header": "📝"
    },
    "salary": {
        "summary_prefix": "💰 **Remuneração Definida:**",
        "confirmation_prompt": "✨ Valores corretos? Posso avançar para competências?",
        "emoji_header": "💵"
    },
    "competencies": {
        "summary_prefix": "🎯 **Competências Selecionadas:**",
        "confirmation_prompt": "✨ Skills corretas? Posso avançar para triagem?",
        "emoji_header": "💡"
    },
    "screening": {
        "summary_prefix": "📝 **Perguntas de Triagem:**",
        "confirmation_prompt": "✨ Perguntas adequadas? Posso avançar para revisão?",
        "emoji_header": "🔍"
    },
    "review": {
        "summary_prefix": "✅ **Revisão Final:**",
        "confirmation_prompt": "✨ Tudo pronto! Posso publicar a vaga?",
        "emoji_header": "📋"
    },
    "complete": {
        "summary_prefix": "🎉 **Vaga Criada:**",
        "confirmation_prompt": "",
        "emoji_header": "✅"
    }
}


def get_response_template(stage: str) -> dict:
    """Get the response template for a stage with emoji formatting."""
    return STAGE_RESPONSE_TEMPLATES.get(stage, STAGE_RESPONSE_TEMPLATES["initial"])


def get_response_type_instruction(stage: str, intent: str) -> str:
    """Return the appropriate response type instruction based on stage and intent."""
    if intent == "ask_question":
        return "Use tipo SUMMARIZE ou ASK_CLARIFY para responder a pergunta."
    if intent == "confirm":
        return "Use tipo CONFIRM para validar e avançar."
    if intent == "modify":
        return "Use tipo CORRECT para confirmar a alteração."
    
    if stage in STAGES_REQUIRING_CONFIRMATION:
        return "Este estágio requer confirmação. Use PROPOSE ou CONFIRM, sempre perguntando se pode avançar."
    
    return "Use o tipo de resposta mais apropriado: ASK_CLARIFY, PROPOSE, ou SUMMARIZE."


STAGE_SPECIALIZED_PROMPTS = {
    "initial": """Você é LIA, especialista em entender as necessidades de contratação.
Seu foco agora: Coletar informações básicas da vaga (título, departamento, nível).

**REGRA OBRIGATÓRIA**: Quando o usuário fornecer informações da vaga, você DEVE:
1. PRIMEIRO: Listar todos os campos que você detectou/extraiu da mensagem
2. SEGUNDO: Pedir confirmação antes de avançar para salário

Estratégias:
- Faça perguntas abertas para entender o contexto completo
- Identifique cargo, área/departamento, senioridade, modelo de trabalho, gestor
- Se o recrutador der informações incompletas, peça esclarecimentos de forma natural
- SEMPRE confirme o que entendeu ANTES de sugerir avançar

**Formato de resposta quando campos são detectados**:
"Entendi! Deixa eu confirmar o que capturei:

📋 **Resumo da Vaga:**
• **Cargo**: [título detectado]
• **Área/Departamento**: [área detectada]
• **Senioridade**: [nível detectado]
• **Modelo de trabalho**: [remoto/híbrido/presencial]
• **Gestor**: [se mencionado]
• **Competências técnicas**: [lista de skills detectadas]
• **Competências comportamentais**: [se mencionadas]

Está tudo correto? Se sim, posso avançar para definir a faixa salarial."

**NUNCA** avance automaticamente sem esta confirmação explícita.
""",

    "title_department": """Você é LIA, especialista em definição de cargos.
Seu foco agora: Confirmar título do cargo e departamento.

Estratégias:
- Valide se o título está claro e profissional
- Confirme o departamento/área corretos
- Sugira ajustes no título se necessário (ex: "Desenvolvedor" → "Desenvolvedor Python Senior")
- Pergunte sobre reporta a quem, se relevante

Exemplo de boa resposta:
"Perfeito! Vou registrar como **[Cargo] - [Departamento]**. O título está bom ou prefere ajustar?"
""",

    "salary": """Você é LIA, especialista em remuneração e benefícios.
Seu foco agora: Definir faixa salarial competitiva.

Estratégias:
- Peça a faixa salarial pretendida (mínimo e máximo)
- Se tiver dados de benchmark, apresente comparação com mercado
- Discuta benefícios se o recrutador mencionar
- Alerte se a faixa estiver muito abaixo/acima do mercado

Formato para salary benchmark:
"Baseado em dados de mercado para [cargo] [nível]:
• Faixa típica: R$ X - R$ Y
• Sua proposta: R$ A - R$ B
• [Análise: competitiva/abaixo/acima do mercado]"

Antes de avançar para competências, SEMPRE pergunte:
"A faixa salarial está definida. Posso prosseguir para definir as competências necessárias?"
""",

    "competencies": """Você é LIA, especialista em competências e habilidades profissionais.
Seu foco agora: Definir skills técnicas e comportamentais essenciais.

Estratégias:
- Pergunte sobre habilidades técnicas obrigatórias (hard skills)
- Pergunte sobre competências comportamentais (soft skills)
- Sugira skills com base no cargo (use dados do catálogo se disponível)
- Diferencie entre obrigatório e desejável
- Atribua pesos/prioridades se possível

Formato sugerido:
"Para um [cargo], sugiro as seguintes competências:

**Técnicas (obrigatórias):**
• [Skill 1] - [peso/prioridade]
• [Skill 2]

**Comportamentais:**
• [Competência 1]
• [Competência 2]

Quer adicionar ou ajustar alguma?"

Antes de avançar, pergunte:
"As competências estão definidas. Posso gerar as perguntas de triagem WSI?"
""",

    "screening": """Você é LIA, especialista em metodologia WSI e triagem de candidatos.
Seu foco agora: Gerar perguntas de triagem inteligentes.

Estratégias:
- Gere perguntas baseadas nas competências definidas
- Use a metodologia WSI (7 blocos de avaliação)
- Crie perguntas que validem skills técnicas E comportamentais
- Sugira critérios de avaliação para cada pergunta
- Pergunte se o recrutador quer adicionar perguntas específicas

Formato WSI:
"Baseado no perfil da vaga, criei estas perguntas de triagem:

**Bloco Técnico:**
1. [Pergunta sobre skill técnica principal]
2. [Pergunta sobre experiência relevante]

**Bloco Comportamental:**
3. [Pergunta situacional]
4. [Pergunta sobre cultura/valores]

Quer revisar ou adicionar alguma pergunta?"

Antes de avançar:
"As perguntas estão prontas. Posso mostrar a revisão completa da vaga?"
""",

    "review": """Você é LIA, especialista em revisão e qualidade de vagas.
Seu foco agora: Revisar toda a vaga antes de publicar.

Estratégias:
- Apresente um resumo completo da vaga
- Destaque pontos fortes e possíveis melhorias
- Verifique se todos os campos obrigatórios estão preenchidos
- Alerte sobre inconsistências (ex: salário vs senioridade)
- Pergunte se está tudo correto para publicar

Formato de revisão:
"📋 **Revisão da Vaga**

**Cargo:** [título] - [departamento]
**Nível:** [senioridade] | **Modelo:** [trabalho]
**Salário:** R$ [min] - R$ [max]

**Competências Técnicas:** [lista]
**Competências Comportamentais:** [lista]

**Perguntas de Triagem:** [quantidade] perguntas configuradas

✅ Vaga completa e pronta para publicação!

Deseja publicar agora ou fazer algum ajuste?"
""",

    "job_summary": """Você é LIA, especialista em enriquecimento inteligente de descrições de vagas.
Seu foco agora: Analisar o que foi coletado e apresentar uma JD ENRIQUECIDA com sugestões baseadas em dados.

**AÇÃO OBRIGATÓRIA:**
CHAME A FERRAMENTA `generate_enriched_jd` com os dados coletados para obter sugestões contextualizadas.

**PARÂMETROS PARA A FERRAMENTA:**
- title: título da vaga
- company_id: ID da empresa
- seniority: senioridade detectada
- location: localização
- detected_responsibilities: responsabilidades já detectadas
- detected_skills: competências técnicas já detectadas
- detected_behavioral: competências comportamentais já detectadas
- salary_min/salary_max: faixa salarial se informada

**AO RECEBER O RESULTADO, APRESENTE:**

📋 **Proposta Enriquecida: [CARGO]**

**✅ Dados Confirmados:**
[Lista do que já foi coletado]

**💡 Sugestões de Responsabilidades:** (se houver)
Para cada sugestão, mostre:
• [responsabilidade] - [justificativa com % ou métrica]

**💡 Sugestões de Competências Técnicas:** (se houver)
Para cada sugestão, mostre:
• [skill] - [justificativa] (ex: "85% das vagas similares incluem")

**💡 Sugestões Comportamentais:** (se houver)
Para cada sugestão, mostre:
• [competência] - [justificativa]

**📊 Qualidade para Triagem WSI:** [score]%
[Se baixo, explique o que falta: "Adicione +X competências técnicas para perguntas de qualidade"]

**💰 Faixa Salarial:**
[Se tiver sugestão de mercado, mostre comparativo]

---
✨ Quer aceitar essas sugestões? Diga quais você aprova ou se prefere ajustar algo.

**FILOSOFIA CONVERSACIONAL:**
- O recrutador RESPONDE no chat (ex: "aceito todas", "não quero Docker", "pode avançar")
- NÃO apresente botões como interface principal
- ESPERE resposta textual antes de avançar

**REGRA OBRIGATÓRIA**: Peça confirmação textual antes de avançar para a próxima etapa.""",

    "complete": """Você é LIA, comemorando a conclusão do processo!
A vaga foi criada com sucesso.

Responda com entusiasmo profissional:
- Confirme que a vaga foi criada
- Informe os próximos passos (publicação, divulgação)
- Ofereça ajuda adicional
- Sugira ações como compartilhar em redes ou buscar candidatos
"""
}


def get_specialized_prompt(stage: str) -> str:
    """Get the specialized prompt for a given stage."""
    return STAGE_SPECIALIZED_PROMPTS.get(stage, STAGE_SPECIALIZED_PROMPTS.get("initial", ""))


class JobWizardNodes:
    """
    Node implementations for the job wizard graph.
    
    Each node takes the current state, performs its function,
    and returns the updated state. Nodes are pure functions
    that don't maintain internal state.
    """
    
    def __init__(
        self,
        llm: Optional[LLMService] = None,
        executor: Optional[ToolExecutor] = None,
        registry: Optional[ToolRegistry] = None,
        memory: Optional[MemoryService] = None,
        feedback: Optional[FeedbackService] = None
    ):
        self.llm = llm or llm_service
        self.executor = executor or tool_executor
        self.registry = registry or tool_registry
        self.memory = memory or memory_service
        self.feedback = feedback or feedback_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def intent_classifier(self, state: JobWizardState) -> JobWizardState:
        """
        Classify user intent from the last message.
        
        Determines what the user wants to do:
        - Provide information for the job draft
        - Ask a question
        - Confirm/reject a suggestion
        - Navigate (skip, go back)
        - Request help
        """
        state["current_node"] = "intent_classifier"
        start_time = datetime.utcnow()
        
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        current_stage = state["current_stage"]
        job_draft = state["job_draft"]
        
        self.logger.info(f"Classifying intent for message in stage {current_stage}")
        
        system_prompt = """Você é um classificador de intenções para um wizard de criação de vagas.
Analise a mensagem do usuário e classifique sua intenção.

INTENÇÕES INICIAIS (quando o usuário escolhe como começar a jornada):
- start_from_scratch: Usuário quer criar vaga do zero, quer descrever a vaga, menciona "do zero", "criar nova", "começar", ou simplesmente começa a descrever a vaga
- use_existing: Usuário quer usar/duplicar/adaptar uma vaga existente, menciona "vaga existente", "duplicar", "copiar"
- use_template: Usuário quer usar um template/modelo pronto, menciona "template", "modelo", "catálogo"

INTENÇÕES PADRÃO:
- provide_info: Usuário está fornecendo informações sobre a vaga (cargo, salário, requisitos, etc.)
- ask_question: Usuário está fazendo uma pergunta
- confirm: Usuário está confirmando/aceitando algo
- reject: Usuário está rejeitando/recusando algo
- modify: Usuário quer modificar algo já informado
- skip: Usuário quer pular a etapa atual
- go_back: Usuário quer voltar à etapa anterior
- help: Usuário precisa de ajuda
- unknown: Não foi possível determinar a intenção

REGRA: Se o estágio atual é "initial" e o usuário responde à pergunta inicial sobre como quer começar, priorize as intenções iniciais (start_from_scratch, use_existing, use_template).

Retorne um JSON com:
{
    "intent": "start_from_scratch|use_existing|use_template|provide_info|ask_question|confirm|reject|modify|skip|go_back|help|unknown",
    "confidence": 0.0-1.0,
    "entities": {"field": "value"},
    "requires_extraction": true/false,
    "requires_tool_call": true/false
}"""
        
        messages = [
            {
                "role": "user",
                "content": f"""Estágio atual: {current_stage}
Campos já preenchidos: {json.dumps(job_draft, ensure_ascii=False, default=str)}

Mensagem do usuário: {last_message}

Classifique a intenção."""
            }
        ]
        
        try:
            # Use generate() instead of generate_structured() to avoid Gemini API limitations
            # with additionalProperties in schemas
            response = await self.llm.generate(
                prompt=f"{system_prompt}\n\n{messages[0]['content']}",
                provider="gemini"
            )
            
            # Parse JSON from response manually
            result_dict = {}
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                result_dict = json.loads(json_str)
                self.logger.debug(f"Parsed intent response: {result_dict}")
                
            except (json.JSONDecodeError, IndexError) as parse_error:
                self.logger.warning(
                    f"Could not parse intent JSON from response: {parse_error}, "
                    f"response preview: {response[:200]}"
                )
                # Will use defaults below
            
            # Create a result object with extracted data
            intent_str = result_dict.get('intent', 'provide_info')
            confidence = float(result_dict.get('confidence', 0.7))
            entities = result_dict.get('entities', {})
            
            # Validate confidence is between 0 and 1
            if not 0 <= confidence <= 1:
                confidence = 0.7
            
            intent_mapping = {
                # Initial journey intents
                "start_from_scratch": WizardIntent.START_FROM_SCRATCH,
                "use_existing": WizardIntent.USE_EXISTING,
                "use_template": WizardIntent.USE_TEMPLATE,
                # Standard intents
                "provide_info": WizardIntent.PROVIDE_INFO,
                "ask_question": WizardIntent.ASK_QUESTION,
                "confirm": WizardIntent.CONFIRM,
                "reject": WizardIntent.REJECT,
                "modify": WizardIntent.MODIFY,
                "skip": WizardIntent.SKIP,
                "go_back": WizardIntent.GO_BACK,
                "help": WizardIntent.HELP,
            }
            
            intent = intent_mapping.get(intent_str, WizardIntent.UNKNOWN)
            
            state["intent"] = intent.value
            if isinstance(entities, dict):
                state["extracted_fields"].update(entities)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            state["reasoning_steps"].append(
                f"[intent_classifier] Classified intent as '{intent.value}' with confidence {confidence:.2f} ({duration:.1f}ms)"
            )
            
            self.logger.info(f"Intent classified: {intent.value} (confidence: {confidence:.2f})")
            
        except Exception as e:
            self.logger.error(f"Intent classification error: {e}", exc_info=True)
            state["intent"] = WizardIntent.PROVIDE_INFO.value
            state["reasoning_steps"].append(f"[intent_classifier] Error: {str(e)}, defaulting to provide_info")
        
        return state
    
    async def field_extractor(self, state: JobWizardState) -> JobWizardState:
        """
        Extract job fields from the conversation.
        
        Uses LLM to identify and extract structured fields from
        the user's natural language input.

        A/B testing: when experiment 'job_wizard_field_extraction' is active,
        selects a prompt variant based on session_id hash and records
        the variant info in state for downstream metric recording.
        """
        state["current_node"] = "field_extractor"
        start_time = datetime.utcnow()
        
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        current_stage = state["current_stage"]
        existing_draft = state["job_draft"]
        
        self.logger.info(f"Extracting fields for stage {current_stage}")

        ab_variant_id: str | None = None
        ab_prompt_hash: str | None = None
        ab_system_prompt: str | None = None
        try:
            from app.shared.prompt_experiment import (
                PromptExperiment as _PE,
                PromptVariant as _PEV,
                get_experiment,
                register_experiment,
            )
            _AB_ID = "job_wizard_field_extraction"
            _exp = get_experiment(_AB_ID)
            if _exp is None:
                import yaml as _yaml
                from pathlib import Path as _Path
                _yaml_path = (
                    _Path(__file__).resolve().parent.parent.parent.parent
                    / "app" / "prompts" / "experiments" / "job_wizard_field_extraction.yaml"
                )
                if _yaml_path.exists():
                    with open(_yaml_path, encoding="utf-8") as _f:
                        _data = _yaml.safe_load(_f)
                    _variants = [
                        _PEV(
                            variant_id=v["variant_id"],
                            prompt_text=v["prompt_text"],
                            weight=float(v.get("weight", 0.5)),
                        )
                        for v in _data.get("variants", [])
                    ]
                    if _variants:
                        _exp = _PE(
                            experiment_id=_AB_ID,
                            variants=_variants,
                            metrics_ttl_seconds=int(_data.get("metrics_ttl_seconds", 604800)),
                        )
                        register_experiment(_exp)
                        self.logger.info("[A/B] JobWizard experiment '%s' registered", _AB_ID)

            if _exp:
                _session_id_ab = state.get("session_id", "anonymous")
                _selected = _exp.select_variant(_session_id_ab)
                ab_variant_id = _selected.variant_id
                import hashlib as _hl
                ab_prompt_hash = _hl.sha256(_selected.prompt_text.encode("utf-8")).hexdigest()[:12]
                ab_system_prompt = _selected.prompt_text
                state["ab_variant"] = ab_variant_id
                state["ab_prompt_hash"] = ab_prompt_hash
                self.logger.debug(
                    "[A/B] JobWizard session=%s → variant=%s hash=%s",
                    _session_id_ab, ab_variant_id, ab_prompt_hash,
                )
        except Exception as _ab_exc:
            self.logger.debug("[A/B] JobWizard variant selection skipped: %s", _ab_exc)
        
        system_prompt = ab_system_prompt or """Você é um extrator de informações de vagas de emprego.
Extraia TODOS os campos estruturados da mensagem do usuário.

## Campos a Extrair (COMPLETOS):

### Informações Básicas:
- title: Título/cargo da vaga (ex: "Desenvolvedor Python", "Gerente de Tecnologia")
- department: Departamento/Área (ex: "Data Science", "Tecnologia", "Comercial")
- seniority: Nível (Junior, Pleno, Senior, Especialista, Gerente, Diretor)
- location: Cidade/região (ex: "São Paulo", "Remoto Brasil")
- work_model: Modelo de trabalho (remote, hybrid, onsite)

### Pessoas:
- manager: Nome do gestor/líder da vaga (ex: "Fabio Melo", "João Silva")
- manager_email: Email do gestor (se mencionado)
- recruiter: Nome do recrutador responsável

### Salário:
- salary_min: Salário mínimo (número, sem pontos ou vírgulas)
- salary_max: Salário máximo (número)
- currency: Moeda (BRL, USD, EUR)

### Competências e Requisitos:
- required_skills: Lista de habilidades técnicas (ex: ["Python", "SQL", "AWS"])
- soft_skills: Lista de habilidades comportamentais (ex: ["Liderança", "Comunicação"])
- responsibilities: Lista de responsabilidades principais (ex: ["Gerenciar time", "Desenvolver pipelines"])
- experience: Experiência mínima em anos ou texto (ex: "5 anos", "Senior")
- education_level: Nível de formação (ex: "Superior completo", "Mestrado")
- languages: Idiomas necessários (ex: ["Inglês avançado", "Espanhol intermediário"])
- certifications: Certificações desejadas (ex: ["AWS Certified", "PMP"])
- tools: Ferramentas específicas (ex: ["Jira", "Figma", "Power BI"])

### Benefícios e Condições:
- benefits: Benefícios mencionados (ex: ["VR", "Plano de saúde", "PLR"])
- bonus: Informações sobre bônus
- contract_type: Tipo de contrato (CLT, PJ, Temporário)

### Triagem:
- screening_questions: Perguntas de triagem para candidatos
- is_affirmative: Se é vaga afirmativa (true/false)
- affirmative_criteria: Critérios afirmativos (ex: "PCD", "mulheres")

### Prazos:
- deadline: Prazo geral para fechamento
- deadline_screening: Prazo para triagem
- deadline_shortlist: Prazo para shortlist

## Formato de Resposta:
Retorne um JSON com os campos extraídos:
{
    "title": "string ou null",
    "department": "string ou null",
    "manager": "string ou null",
    "responsibilities": ["lista", "de", "responsabilidades"] ou null,
    "required_skills": ["lista", "de", "skills"] ou null,
    ...
    "extraction_confidence": 0.0-1.0
}

## Regras CRÍTICAS:
- NÃO invente dados. Se não conseguir extrair, use null.
- Extraia TUDO que for mencionado, mesmo parcialmente.
- Se o usuário mencionar "gestor", "líder", "reporta a", "para [nome]", extraia como manager - NÃO confunda com title.
- ATENÇÃO: "Vaga para Fabio Melo" significa manager=Fabio Melo, NÃO title=Fabio Melo.
- title deve ser o CARGO da vaga (ex: "Desenvolvedor", "Gerente", "Analista") - NÃO um nome de pessoa.
- Se mencionar responsabilidades, atividades, funções, extraia como responsibilities.
- Normalize valores: "15k" = 15000, "20 mil" = 20000
- Idiomas: extraia nível se mencionado (básico, intermediário, avançado, fluente)"""
        
        user_content = (
            f"Estágio atual: {current_stage}\n"
            f"Campos já existentes: {json.dumps(existing_draft, ensure_ascii=False, default=str)}\n\n"
            f"Nova mensagem: {last_message}\n\n"
            f"Extraia os campos mencionados na mensagem."
        )

        if ab_system_prompt and "{user_message}" in ab_system_prompt:
            full_prompt = ab_system_prompt.replace("{user_message}", user_content)
        else:
            full_prompt = f"{system_prompt}\n\n{user_content}"

        try:
            response = await self.llm.generate(
                prompt=full_prompt,
                provider="gemini"
            )
            
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                extracted = json.loads(json_str)
            except json.JSONDecodeError:
                extracted = {}
                self.logger.warning(f"Could not parse extraction response: {response[:200]}")
            
            overall_confidence = extracted.pop("extraction_confidence", 0.7)
            
            for field, value in extracted.items():
                if value is not None and value != "null" and value != "":
                    state["extracted_fields"][field] = value
                    state["job_draft"][field] = value
                    state["confidence_scores"][field] = overall_confidence
            
            if state["extracted_fields"]:
                state["extracted_fields"] = normalize_fields_for_frontend(state["extracted_fields"])
                state["job_draft"] = normalize_fields_for_frontend(state["job_draft"])
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            extracted_count = len([v for v in extracted.values() if v is not None])
            ab_info = f" [ab={ab_variant_id} hash={ab_prompt_hash}]" if ab_variant_id else ""
            state["reasoning_steps"].append(
                f"[field_extractor] Extracted {extracted_count} fields with confidence {overall_confidence:.2f} ({duration:.1f}ms){ab_info}"
            )
            if ab_prompt_hash:
                state["prompt_version"] = ab_prompt_hash
            
            self.logger.info(f"Extracted {extracted_count} fields")
            
        except Exception as e:
            self.logger.error(f"Field extraction error: {e}")
            state["reasoning_steps"].append(f"[field_extractor] Error: {e}")
        
        return state
    
    async def tool_router(self, state: JobWizardState) -> JobWizardState:
        """
        Decide which tools to call based on current state.
        
        Analyzes the state to determine if any tools should be invoked:
        - Salary benchmark for salary validation (MarketBenchmarkService)
        - Company config for benefits and pipeline templates (CompanyConfigurationService)
        - Job suggestions for skills and competencies (SkillsCatalogService)
        - Field validation for data verification
        """
        state["current_node"] = "tool_router"
        start_time = datetime.utcnow()
        
        current_stage = state["current_stage"]
        job_draft = state["job_draft"]
        intent = state.get("intent", "")
        company_id = state.get("company_id") or job_draft.get("company_id")
        
        self.logger.info(f"Routing tools for stage {current_stage}, intent {intent}, company_id {company_id}")
        
        tools_to_call = []
        
        # JD Enrichment is handled automatically in wizard_smart_orchestrator.py
        # to avoid duplicate calls
        
        if current_stage == WizardStage.SALARY.value:
            if job_draft.get("title") and (job_draft.get("salary_min") or job_draft.get("salary_max")):
                tools_to_call.append({
                    "name": "search_salary_benchmark",
                    "parameters": {
                        "job_title": job_draft.get("title", ""),
                        "seniority": job_draft.get("seniority", "Pleno"),
                        "location": job_draft.get("location", "São Paulo"),
                        "industry": job_draft.get("industry", "")
                    }
                })
            
            if company_id:
                tools_to_call.append({
                    "name": "get_company_config",
                    "parameters": {
                        "company_id": company_id,
                        "config_type": "benefits",
                        "seniority": job_draft.get("seniority", "Pleno")
                    }
                })
        
        if current_stage == WizardStage.COMPETENCIES.value:
            if job_draft.get("title"):
                tools_to_call.append({
                    "name": "get_job_suggestions",
                    "parameters": {
                        "field_name": "skills",
                        "job_context": {
                            "job_title": job_draft.get("title", ""),
                            "seniority": job_draft.get("seniority", "Pleno"),
                            "department": job_draft.get("department", "")
                        },
                        "company_id": company_id
                    }
                })
                tools_to_call.append({
                    "name": "get_job_suggestions",
                    "parameters": {
                        "field_name": "behavioral_competencies",
                        "job_context": {
                            "job_title": job_draft.get("title", ""),
                            "seniority": job_draft.get("seniority", "Pleno"),
                            "department": job_draft.get("department", "")
                        },
                        "company_id": company_id
                    }
                })
        
        if current_stage == WizardStage.SCREENING.value:
            if company_id:
                tools_to_call.append({
                    "name": "get_job_suggestions",
                    "parameters": {
                        "field_name": "screening_questions",
                        "job_context": {
                            "job_title": job_draft.get("title", ""),
                            "seniority": job_draft.get("seniority", "Pleno"),
                            "department": job_draft.get("department", "")
                        },
                        "company_id": company_id
                    }
                })
        
        
        if intent == WizardIntent.CONFIRM.value or current_stage == WizardStage.REVIEW.value:
            required_fields = ["title", "department", "salary_min", "salary_max"]
            if all(job_draft.get(f) for f in required_fields):
                tools_to_call.append({
                    "name": "validate_job_fields",
                    "parameters": {
                        "job_data": job_draft
                    }
                })
        
        state["tool_calls"] = tools_to_call
        
        if tools_to_call:
            state["next_action"] = "execute_tools"
            self.logger.info(f"Routed {len(tools_to_call)} tools: {[t['name'] for t in tools_to_call]}")
        else:
            state["next_action"] = "generate_response"
            self.logger.info("No tools needed, proceeding to response generation")
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        state["reasoning_steps"].append(
            f"[tool_router] Routed {len(tools_to_call)} tool(s): {[t['name'] for t in tools_to_call]} ({duration:.1f}ms)"
        )
        
        return state
    
    async def tool_executor(self, state: JobWizardState) -> JobWizardState:
        """
        Execute tool calls and update state with results.
        
        Runs each tool through the ToolExecutor and collects results.
        """
        state["current_node"] = "tool_executor"
        start_time = datetime.utcnow()
        
        tool_calls = state.get("tool_calls", [])
        
        if not tool_calls:
            self.logger.info("No tools to execute")
            state["reasoning_steps"].append("[tool_executor] No tools to execute")
            return state
        
        self.logger.info(f"Executing {len(tool_calls)} tools")
        
        results = []
        for call in tool_calls:
            try:
                tool_name = call.get("name", "")
                parameters = call.get("parameters", {})
                
                self.logger.info(f"Executing tool: {tool_name}")
                
                result = await self.executor.execute(
                    tool_name=tool_name,
                    parameters=parameters,
                    agent_type="job_wizard",
                    conversation_id=state["session_id"]
                )
                
                results.append({
                    "tool_name": tool_name,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "execution_time_ms": result.execution_time_ms
                })
                
                if result.success and result.result:
                    if tool_name == "search_salary_benchmark":
                        state["job_draft"]["salary_benchmark"] = result.result
                    elif tool_name == "validate_job_fields":
                        state["job_draft"]["validation_result"] = result.result
                    elif tool_name == "get_job_suggestions":
                        state["job_draft"]["suggestions"] = result.result
                
                self.logger.info(f"Tool {tool_name} executed: success={result.success}")
                
            except Exception as e:
                self.logger.error(f"Tool execution error for {call.get('name')}: {e}")
                results.append({
                    "tool_name": call.get("name", "unknown"),
                    "success": False,
                    "error": str(e)
                })
        
        state["tool_results"] = results
        state["tool_calls"] = []
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        success_count = len([r for r in results if r.get("success")])
        state["reasoning_steps"].append(
            f"[tool_executor] Executed {len(results)} tools, {success_count} successful ({duration:.1f}ms)"
        )
        
        return state
    
    async def response_generator(self, state: JobWizardState) -> JobWizardState:
        """
        Generate natural language response based on current state.
        
        Creates a helpful, contextual response for the user based on:
        - Current stage (uses specialized prompts per stage)
        - Extracted fields
        - Tool results
        - Intent
        - Learning patterns from past feedback
        - Confirmation requirements for critical stages
        """
        state["current_node"] = "response_generator"
        start_time = datetime.utcnow()
        
        current_stage = state["current_stage"]
        job_draft = state["job_draft"]
        intent = state.get("intent", "")
        tool_results = state.get("tool_results", [])
        extracted_fields = state.get("extracted_fields", {})
        
        self.logger.info(f"Generating response for stage {current_stage}")
        
        pattern_context = {}
        try:
            last_message = state["messages"][-1]["content"] if state["messages"] else ""
            company_id = state.get("company_id", "")
            if company_id and intent:
                pattern_context = await self.feedback.get_pattern_context_for_response(
                    intent=intent,
                    user_message=last_message,
                    company_id=company_id
                )
                if pattern_context.get("has_patterns"):
                    self.logger.info(f"Found {pattern_context.get('pattern_count', 0)} relevant learning patterns")
        except Exception as e:
            self.logger.warning(f"Error fetching feedback patterns: {e}")
        
        specialized_prompt = get_specialized_prompt(current_stage)
        
        response_template = get_response_template(current_stage)
        
        requires_confirmation = current_stage in STAGES_REQUIRING_CONFIRMATION
        
        response_type_instruction = get_response_type_instruction(current_stage, intent or "provide_info")
        
        # Add specific instructions for initial journey intents
        journey_instruction = ""
        if intent == "start_from_scratch":
            journey_instruction = """
## AÇÃO ESPECIAL: Início de Jornada - Criar do Zero
O usuário escolheu criar uma vaga do zero. Você deve:
1. Confirmar a escolha com entusiasmo ("Ótimo! Vamos criar sua vaga do zero!")
2. Pedir que ele descreva a vaga em linguagem natural
3. Explicar que você vai extrair automaticamente as informações (cargo, departamento, requisitos, etc.)
4. Perguntar: "Me conte sobre a vaga que você precisa criar. Qual é o cargo? Para qual departamento?"
"""
        elif intent == "use_existing":
            journey_instruction = """
## AÇÃO ESPECIAL: Início de Jornada - Usar Vaga Existente
O usuário quer usar uma vaga existente como base. Você deve:
1. Confirmar a escolha ("Boa ideia! Vamos usar uma vaga existente como base.")
2. Informar que vai buscar as vagas recentes da empresa
3. Pedir que ele indique qual vaga quer duplicar/adaptar
4. Perguntar: "Qual vaga você gostaria de usar como base? Pode me dizer o nome do cargo ou área."
"""
        elif intent == "use_template":
            journey_instruction = """
## AÇÃO ESPECIAL: Início de Jornada - Usar Template
O usuário quer usar um template pronto. Você deve:
1. Confirmar a escolha ("Perfeito! Temos modelos prontos para várias áreas.")
2. Oferecer categorias de templates (Tecnologia, Comercial, RH, etc.)
3. Perguntar qual área/cargo ele procura
4. Perguntar: "Para qual área você precisa da vaga? Posso sugerir templates de Tecnologia, Comercial, Administrativo, RH..."
"""
        
        system_prompt = f"""{MASTER_ORCHESTRATOR_PROMPT}

## CONTEXTO ATUAL
- **Estágio**: {current_stage}
- **Intent do usuário**: {intent}
- **Requer confirmação**: {"SIM" if requires_confirmation else "NÃO"}
{journey_instruction}
## INSTRUÇÃO DE TIPO DE RESPOSTA
{response_type_instruction}

## PROMPT ESPECIALIZADO PARA ESTE ESTÁGIO
{specialized_prompt}

## FORMATO DE RESPOSTA (OBRIGATÓRIO)
Use este formato para suas respostas:

### Prefixo de Resumo: {response_template['summary_prefix']}
### Pergunta de Confirmação: {response_template['confirmation_prompt']}
### Emoji do Estágio: {response_template['emoji_header']}

IMPORTANTE: Sempre inicie resumos com o prefixo especificado acima."""

        awaiting_confirmation = state.get("awaiting_confirmation", False)
        
        if awaiting_confirmation:
            system_prompt += f"""

## 🔔 ESTADO: AGUARDANDO CONFIRMAÇÃO DO USUÁRIO
O sistema está BLOQUEADO aguardando confirmação explícita do usuário.

VOCÊ DEVE:
1. Apresentar um RESUMO claro e formatado dos campos detectados usando o prefixo: {response_template['summary_prefix']}
2. Listar cada campo com emoji e valor (ex: "💼 Cargo: Desenvolvedor Senior")
3. Perguntar EXPLICITAMENTE: "{response_template['confirmation_prompt']}"
4. Dar opções claras: "Diga 'sim' para confirmar, 'não' para corrigir algo, ou me diga o que deseja alterar."

NÃO tente avançar ou processar novos campos - aguarde a confirmação."""
        elif requires_confirmation:
            system_prompt += f"""

## ATENÇÃO - Confirmação Obrigatória:
Este estágio ({current_stage}) requer confirmação EXPLÍCITA do usuário antes de avançar.
Ao final da sua resposta, SEMPRE pergunte: "Posso avançar para a próxima etapa?" ou similar.
NÃO avance automaticamente sem essa pergunta de confirmação."""
        
        if pattern_context.get("has_patterns"):
            good_examples = pattern_context.get("good_response_examples", [])
            bad_examples = pattern_context.get("bad_response_examples", [])
            style_hints = pattern_context.get("response_style_hints", [])
            
            if good_examples or bad_examples or style_hints:
                system_prompt += "\n\n## Aprendizados de interações anteriores:"
                if good_examples:
                    system_prompt += f"\nExemplos de boas respostas: {json.dumps(good_examples[:2], ensure_ascii=False)}"
                if bad_examples:
                    system_prompt += f"\nEvite respostas como: {json.dumps(bad_examples[:2], ensure_ascii=False)}"
                if style_hints:
                    system_prompt += f"\nDicas de estilo: {', '.join(style_hints[:2])}"
        
        context = {
            "current_stage": current_stage,
            "job_draft": job_draft,
            "intent": intent,
            "tool_results": tool_results,
            "extracted_fields": extracted_fields,
            "requires_confirmation": requires_confirmation,
            "awaiting_confirmation": awaiting_confirmation,
            "response_type": response_type_instruction.split(":")[0] if response_type_instruction else "unknown"
        }
        
        conversation_history = state["messages"][-5:]
        
        messages = [
            {
                "role": "user",
                "content": f"""Contexto atual:
{json.dumps(context, ensure_ascii=False, default=str)}

Histórico recente:
{json.dumps(conversation_history, ensure_ascii=False)}

Gere uma resposta apropriada para o usuário considerando:
1. O que ele disse/pediu
2. Os campos que você extraiu
3. Os resultados das ferramentas (se houver)
4. O próximo passo do wizard
5. Se precisa de confirmação antes de avançar

Sua resposta (em português):"""
            }
        ]
        
        try:
            response = await self.llm.generate(
                prompt=f"{system_prompt}\n\n{messages[0]['content']}",
                provider="gemini"
            )
            
            state["response_text"] = response.strip()
            state["messages"].append({
                "role": "assistant",
                "content": state["response_text"]
            })
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            state["reasoning_steps"].append(
                f"[response_generator] Generated response using {current_stage} specialist "
                f"({len(response)} chars, confirmation_required={requires_confirmation}) ({duration:.1f}ms)"
            )
            
            self.logger.info(f"Generated response with {current_stage} specialist: {response[:100]}...")
            
        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            state["response_text"] = "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?"
            state["reasoning_steps"].append(f"[response_generator] Error: {e}")
            state["error"] = str(e)
        
        return state
    
    async def stage_transition(self, state: JobWizardState) -> JobWizardState:
        """
        Decide if the wizard should advance to the next stage.
        
        Uses intelligent auto-transition logic based on:
        - Minimum viable completion (not 100% of fields)
        - Confidence threshold >= 0.7
        - User intent (confirm, skip, go back have special handling)
        - Stage-specific readiness criteria
        - Confirmation requirements for critical stages
        """
        state["current_node"] = "stage_transition"
        state["auto_transition"] = False
        start_time = datetime.utcnow()
        
        current_stage = state["current_stage"]
        job_draft = state["job_draft"]
        intent = state.get("intent", "")
        confidence_scores = state.get("confidence_scores", {})
        
        requires_confirmation = current_stage in STAGES_REQUIRING_CONFIRMATION
        
        self.logger.info(f"Evaluating stage transition from {current_stage} (requires_confirmation={requires_confirmation})")
        
        try:
            stage_enum = WizardStage(current_stage)
        except ValueError:
            stage_enum = WizardStage.INITIAL
        
        if intent == WizardIntent.GO_BACK.value:
            from lia_agents_core.state_machine import get_previous_stage
            prev_stage = get_previous_stage(stage_enum)
            if prev_stage:
                state["current_stage"] = prev_stage.value
                self.logger.info(f"GO_BACK: {current_stage} -> {prev_stage.value}")
                state["reasoning_steps"].append(
                    f"[stage_transition] User requested go back: {current_stage} -> {prev_stage.value}"
                )
                state["should_continue"] = False
                return state
        
        if intent == WizardIntent.SKIP.value:
            next_stage = get_next_stage(stage_enum)
            if next_stage:
                state["current_stage"] = next_stage.value
                self.logger.info(f"SKIP: {current_stage} -> {next_stage.value}")
                state["reasoning_steps"].append(
                    f"[stage_transition] User skipped: {current_stage} -> {next_stage.value}"
                )
                state["should_continue"] = False
                return state
        
        if stage_enum == WizardStage.COMPLETE:
            state["should_continue"] = False
            state["reasoning_steps"].append("[stage_transition] Wizard completed")
            return state
        
        stage_readiness = calculate_stage_readiness(job_draft, stage_enum)
        minimum_fields = STAGE_MINIMUM_FIELDS.get(stage_enum, [])
        filled_minimum = [f for f in minimum_fields if job_draft.get(f)]
        
        avg_confidence = 0.8
        if filled_minimum and confidence_scores:
            avg_confidence = calculate_average_confidence(confidence_scores, filled_minimum)
        
        required_fields = STAGE_REQUIRED_FIELDS.get(stage_enum, [])
        missing_required = [f for f in required_fields if not job_draft.get(f)]
        full_completion_pct = 0
        if required_fields:
            full_completion_pct = ((len(required_fields) - len(missing_required)) / len(required_fields)) * 100
        else:
            full_completion_pct = 100
        
        self.logger.debug(
            f"Stage {current_stage}: readiness={stage_readiness:.2f}, "
            f"avg_confidence={avg_confidence:.2f}, "
            f"full_completion={full_completion_pct:.0f}%, "
            f"intent={intent}"
        )
        
        should_advance = False
        transition_reason = ""
        is_auto_transition = False
        
        can_auto_advance, auto_reasoning = should_auto_advance(job_draft, confidence_scores, stage_enum)
        
        if requires_confirmation:
            if intent == WizardIntent.CONFIRM.value:
                # Usuário confirmou explicitamente
                if not missing_required:
                    should_advance = True
                    transition_reason = f"User confirmed stage {current_stage} - advancing"
                else:
                    should_advance = True
                    transition_reason = f"User confirmed despite incomplete fields - respecting user choice"
                is_auto_transition = False
            else:
                # BLOQUEIO DURO: Stage requer confirmação mas intent não é CONFIRM
                should_advance = False
                is_auto_transition = False
                transition_reason = f"Stage {current_stage} requires explicit confirmation - waiting for user to confirm"
                state["awaiting_confirmation"] = True
                self.logger.info(
                    f"CONFIRMATION GATE: Stage {current_stage} blocked - requires explicit confirm "
                    f"(current intent: {intent})"
                )
        else:
            if not missing_required:
                if intent in [WizardIntent.CONFIRM.value, WizardIntent.PROVIDE_INFO.value]:
                    should_advance = True
                    transition_reason = f"User intent={intent} with all required fields complete"
                    is_auto_transition = False
            
            if not should_advance and can_auto_advance:
                if intent == WizardIntent.PROVIDE_INFO.value:
                    should_advance = True
                    is_auto_transition = True
                    transition_reason = f"Auto-transition: {auto_reasoning}"
                elif intent not in [WizardIntent.GO_BACK.value, WizardIntent.SKIP.value, WizardIntent.REJECT.value]:
                    if stage_readiness >= 1.0 and avg_confidence >= AUTO_TRANSITION_CONFIDENCE_THRESHOLD:
                        should_advance = True
                        is_auto_transition = True
                        transition_reason = f"Auto-transition: minimum fields complete with confidence {avg_confidence:.2f}"
        
        if should_advance:
            next_stage = get_next_stage(stage_enum)
            if next_stage:
                state["current_stage"] = next_stage.value
                state["auto_transition"] = is_auto_transition
                
                log_prefix = "[AUTO]" if is_auto_transition else "[USER]"
                self.logger.info(
                    f"{log_prefix} Transition: {current_stage} -> {next_stage.value} "
                    f"(reason: {transition_reason})"
                )
                state["reasoning_steps"].append(
                    f"[stage_transition] {log_prefix} Advanced: {current_stage} -> {next_stage.value} "
                    f"(readiness: {stage_readiness:.2f}, confidence: {avg_confidence:.2f}, "
                    f"full_completion: {full_completion_pct:.0f}%)"
                )
            else:
                state["current_stage"] = WizardStage.COMPLETE.value
                state["reasoning_steps"].append("[stage_transition] Advanced to COMPLETE")
        else:
            missing_minimum = [f for f in minimum_fields if not job_draft.get(f)]
            self.logger.debug(
                f"Staying at {current_stage}: missing_minimum={missing_minimum}, "
                f"readiness={stage_readiness:.2f}, confidence={avg_confidence:.2f}"
            )
            state["reasoning_steps"].append(
                f"[stage_transition] Staying at {current_stage} "
                f"(missing_required: {missing_required}, missing_minimum: {missing_minimum}, "
                f"readiness: {stage_readiness:.2f}, confidence: {avg_confidence:.2f})"
            )
        
        state["should_continue"] = False
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        state["reasoning_steps"].append(f"[stage_transition] Evaluation complete ({duration:.1f}ms)")
        
        return state
    
    def get_node(self, name: str):
        """Get a node function by name."""
        nodes = {
            "intent_classifier": self.intent_classifier,
            "field_extractor": self.field_extractor,
            "tool_router": self.tool_router,
            "tool_executor": self.tool_executor,
            "response_generator": self.response_generator,
            "stage_transition": self.stage_transition
        }
        return nodes.get(name)


job_wizard_nodes = JobWizardNodes()
