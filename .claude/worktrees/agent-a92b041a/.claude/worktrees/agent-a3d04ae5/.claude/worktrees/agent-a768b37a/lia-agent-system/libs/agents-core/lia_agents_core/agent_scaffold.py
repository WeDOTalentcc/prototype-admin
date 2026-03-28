"""
Agent Scaffold - Gerador de boilerplate para novos agentes ReAct.

Ferramenta de desenvolvimento que gera os 4 arquivos padrão necessários
para criar um novo agente de domínio seguindo o padrão ReAct da plataforma.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AgentScaffold:
    """Gera os arquivos boilerplate para um novo agente ReAct de domínio."""

    @staticmethod
    def generate(domain_name: str, domain_path: str, description: str) -> Dict[str, str]:
        """Gera os 4 arquivos template para um novo agente ReAct.

        Segue o padrão de referência do WizardReActAgent com as 4 camadas:
        agent.py, tool_registry.py, system_prompt.py, stage_context.py.

        Args:
            domain_name: Nome do domínio (ex: 'compliance', 'interview').
            domain_path: Caminho do módulo (ex: 'app.domains.compliance').
            description: Descrição do propósito do agente.

        Returns:
            Dicionário com nomes de arquivo como chaves e conteúdo como valores.
            Não grava arquivos (o chamador decide).
        """
        class_name = "".join(word.capitalize() for word in domain_name.split("_"))
        agent_class = f"{class_name}ReActAgent"
        snake_name = domain_name.lower().replace("-", "_")

        files: Dict[str, str] = {}

        files[f"{snake_name}_react_agent.py"] = AgentScaffold._generate_agent(
            domain_name=domain_name,
            domain_path=domain_path,
            description=description,
            class_name=class_name,
            agent_class=agent_class,
            snake_name=snake_name,
        )

        files[f"{snake_name}_tool_registry.py"] = AgentScaffold._generate_tool_registry(
            domain_name=domain_name,
            domain_path=domain_path,
            description=description,
            snake_name=snake_name,
        )

        files[f"{snake_name}_system_prompt.py"] = AgentScaffold._generate_system_prompt(
            domain_name=domain_name,
            description=description,
            snake_name=snake_name,
        )

        files[f"{snake_name}_stage_context.py"] = AgentScaffold._generate_stage_context(
            domain_name=domain_name,
            description=description,
            snake_name=snake_name,
        )

        logger.info(
            f"[AgentScaffold] Gerados {len(files)} arquivos para domínio '{domain_name}'"
        )

        return files

    @staticmethod
    def _generate_agent(
        domain_name: str,
        domain_path: str,
        description: str,
        class_name: str,
        agent_class: str,
        snake_name: str,
    ) -> str:
        """Gera o arquivo principal do agente."""
        return f'''"""
{agent_class} - Agente autônomo para {description}.

Implementa a interface BaseAgent usando o loop ReAct com ferramentas,
prompts e contexto de estágio específicos do domínio {domain_name}.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from lia_agents_core.agent_interface import (
    AgentAction,
    AgentInput,
    AgentOutput,
    BaseAgent,
    NavigationCommand,
)
from lia_agents_core.react_loop import ReActConfig, ReActLoop, ReActState
from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.observability import ReActObserver

from {domain_path}.agents.{snake_name}_stage_context import (
    STAGE_DEFINITIONS,
    get_stage_context,
    get_transition_prompt,
)
from {domain_path}.agents.{snake_name}_system_prompt import build_system_prompt
from {domain_path}.agents.{snake_name}_tool_registry import (
    get_stage_tools,
    get_{snake_name}_tools,
)

logger = logging.getLogger(__name__)


class {agent_class}(BaseAgent):
    """{description}.

    Implementa a interface BaseAgent usando um loop ReAct com
    ferramentas específicas do domínio {domain_name}. Cada chamada a
    ``process`` executa um ciclo completo Reason-Act-Observe e retorna
    um AgentOutput estruturado.
    """

    def __init__(self) -> None:
        """Inicializa o agente com o serviço de memória de trabalho."""
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_{snake_name}_tools()]
        logger.info("[{agent_class}] Inicializado")

    @property
    def domain_name(self) -> str:
        """Retorna o identificador do domínio deste agente."""
        return "{domain_name}"

    @property
    def available_tools(self) -> List[str]:
        """Retorna a lista de ferramentas disponíveis para este agente."""
        return list(self._all_tool_names)

    async def process(self, input: AgentInput) -> AgentOutput:
        """Processa uma mensagem do usuário pelo loop ReAct.

        Args:
            input: Entrada padronizada com mensagem, contexto e metadados.

        Returns:
            Saída padronizada com resposta, ações e atualizações de estado.
        """
        start_time = time.time()
        current_stage = input.context.get("current_stage", "initial")

        logger.info(
            f"[{agent_class}] Processando mensagem session={{input.session_id}} "
            f"stage={{current_stage}}"
        )

        try:
            memory = await self._memory_service.get_or_create(
                session_id=input.session_id,
                domain=self.domain_name,
                company_id=input.company_id,
                user_id=input.user_id,
            )

            if memory.current_stage != current_stage:
                await self._memory_service.update_memory(
                    session_id=input.session_id,
                    domain=self.domain_name,
                    updates={{"current_stage": current_stage}},
                )

            memory_summary = await self._memory_service.get_context_summary(
                session_id=input.session_id,
                domain=self.domain_name,
            )

            stage_ctx = get_stage_context(current_stage, input.context.get("collected_data", {{}}))
            tools = get_stage_tools(current_stage)
            system_prompt = build_system_prompt(
                stage_context=stage_ctx,
                memory_summary=memory_summary,
            )

            config = ReActConfig(
                max_iterations=5,
                system_prompt=system_prompt,
                available_tools=tools,
                domain=self.domain_name,
                model_provider="claude",
                temperature=0.3,
                guardrails=[],
            )

            loop = ReActLoop(config=config, working_memory_service=self._memory_service)

            observer = None
            try:
                observer = ReActObserver(
                    session_id=input.session_id,
                    domain=self.domain_name,
                    agent_class="{agent_class}",
                )
                observer.log.stage_before = current_stage
                observer.log.user_message_length = len(input.message)
                observer.log.model_provider = config.model_provider
            except Exception as obs_err:
                logger.warning(f"[{agent_class}] Falha ao criar observer: {{obs_err}}")
                observer = None

            state = await loop.run(
                message=input.message,
                context={{
                    "current_stage": current_stage,
                    "collected_data": input.context.get("collected_data", {{}}),
                    "company_id": input.company_id,
                    "user_id": input.user_id,
                    "conversation_history": [
                        {{"role": m.get("role", "user"), "content": m.get("content", "")}}
                        for m in input.conversation_history[-5:]
                    ],
                }},
                session_id=input.session_id,
                observer=observer,
            )

            message = state.final_response or "Desculpe, nao consegui gerar uma resposta."

            actions = []
            for action_record in state.actions_taken:
                actions.append(
                    AgentAction(
                        action_type=action_record.get("type", "unknown"),
                        params=action_record,
                    )
                )

            confidence = 0.7
            if state.error:
                confidence = 0.3

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[{agent_class}] Completo em {{duration_ms:.0f}}ms "
                f"iterations={{state.iteration}} tools={{len(state.tool_calls_made)}}"
            )

            if observer:
                try:
                    observer.finalize(
                        confidence=confidence,
                        response_length=len(message),
                    )
                except Exception:
                    pass

            return AgentOutput(
                message=message,
                actions=actions,
                confidence=confidence,
                reasoning_steps=[state.current_reasoning[:500]] if state.current_reasoning else [],
                tool_results=[
                    {{
                        "tool_name": tc.get("tool_name", ""),
                        "result": tc.get("result", {{}}),
                        "duration_ms": tc.get("duration_ms", 0),
                    }}
                    for tc in state.tool_calls_made
                ],
                error=state.error,
                metadata={{
                    "iterations": state.iteration,
                    "tools_called": len(state.tool_calls_made),
                    "stage": current_stage,
                    "duration_ms": round(duration_ms, 1),
                }},
            )

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{agent_class}] Erro ao processar mensagem: {{exc}}",
                exc_info=True,
            )
            return AgentOutput(
                message=(
                    "Desculpe, encontrei um problema ao processar sua mensagem. "
                    "Pode tentar novamente?"
                ),
                error=str(exc),
                confidence=0.0,
                metadata={{"duration_ms": round(duration_ms, 1)}},
            )

    async def get_status(self) -> dict:
        """Retorna informações de status e saúde do agente."""
        return {{
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "stages": list(STAGE_DEFINITIONS.keys()),
            "max_iterations": 5,
            "model_provider": "claude",
        }}
'''

    @staticmethod
    def _generate_tool_registry(
        domain_name: str,
        domain_path: str,
        description: str,
        snake_name: str,
    ) -> str:
        """Gera o arquivo de registro de ferramentas."""
        return f'''"""
{snake_name.replace("_", " ").title()} Tool Registry - Ferramentas do agente para o loop ReAct.

Expõe as ferramentas do domínio {domain_name} no formato ToolDefinition
para que o ReActLoop possa decidir autonomamente quais ferramentas chamar.
"""
import logging
from typing import Any, Dict, List

from lia_agents_core.react_loop import ToolDefinition

logger = logging.getLogger(__name__)


async def _placeholder_tool(**kwargs: Any) -> Dict[str, Any]:
    """Ferramenta placeholder - substitua pela implementação real."""
    logger.info(f"[{snake_name}_tools] placeholder_tool chamada com: {{list(kwargs.keys())}}")
    return {{"success": True, "message": "Placeholder - implementar ferramenta real"}}


def get_{snake_name}_tools() -> List[ToolDefinition]:
    """Retorna todas as ferramentas disponíveis para o agente {domain_name}.

    Returns:
        Lista de ToolDefinition com todas as ferramentas do domínio.
    """
    return [
        ToolDefinition(
            name="placeholder_tool",
            description="Ferramenta placeholder - substitua pela implementação real",
            parameters={{
                "type": "object",
                "properties": {{
                    "query": {{"type": "string", "description": "Consulta de exemplo"}},
                }},
            }},
            function=_placeholder_tool,
        ),
    ]


def get_stage_tools(stage: str) -> List[ToolDefinition]:
    """Retorna as ferramentas disponíveis para um estágio específico.

    Args:
        stage: Identificador do estágio atual.

    Returns:
        Lista de ToolDefinition filtrada pelo estágio.
    """
    return get_{snake_name}_tools()
'''

    @staticmethod
    def _generate_system_prompt(
        domain_name: str,
        description: str,
        snake_name: str,
    ) -> str:
        """Gera o arquivo de system prompt."""
        upper_name = domain_name.upper().replace("_", " ")
        return f'''"""
{snake_name.replace("_", " ").title()} System Prompt - Personalidade e comportamento da LIA para {description}.

Define as instruções centrais que moldam como a LIA se comporta
no domínio {domain_name}.
"""


{upper_name.replace(" ", "_")}_SYSTEM_PROMPT = """Voce e a LIA, assistente de recrutamento inteligente da plataforma.
Voce esta atuando no domínio de {description}.

=== IDENTIDADE ===
- Nome: LIA (Assistente de Recrutamento com IA)
- Personalidade: Profissional, amigavel, eficiente e proativa
- Idioma: Portugues Brasileiro (PT-BR)
- Tom: Conversacional mas competente, como uma colega de trabalho experiente

=== INSTRUCOES REACT ===
Voce opera em um ciclo de Raciocinio-Acao-Observacao:

1. RACIOCINE sobre a situacao atual:
   - Que estagio estamos? Que informacoes tenho?
   - O que o usuario disse? Que dados posso extrair?
   - Preciso usar alguma ferramenta?

2. AJA de uma das formas:
   - action="call_tool": Chamar uma ferramenta para buscar dados ou validar
   - action="respond": Responder ao usuario com informacoes ou perguntas
   - action="ask_clarification": Pedir esclarecimento quando informacoes sao ambiguas

3. OBSERVE o resultado e decida se precisa agir novamente ou responder
"""


def build_system_prompt(stage_context: str, memory_summary: str) -> str:
    """Constrói o system prompt completo com contexto de estágio e memória.

    Args:
        stage_context: Contexto específico do estágio atual.
        memory_summary: Resumo da memória de trabalho do agente.

    Returns:
        String com o prompt completo para o LLM.
    """
    return f"""{{{upper_name.replace(" ", "_")}_SYSTEM_PROMPT}}

=== CONTEXTO DO ESTAGIO ===
{{stage_context}}

=== MEMORIA DE TRABALHO ===
{{memory_summary}}
"""
'''

    @staticmethod
    def _generate_stage_context(
        domain_name: str,
        description: str,
        snake_name: str,
    ) -> str:
        """Gera o arquivo de contexto de estágios."""
        return f'''"""
{snake_name.replace("_", " ").title()} Stage Context - Contexto por estágio para o agente {domain_name}.

Cada estágio possui requisitos, campos esperados e objetivos de conversa
diferentes. Este módulo injeta o contexto correto para que o agente
saiba no que focar.
"""
from typing import Any, Dict, List


STAGE_DEFINITIONS: Dict[str, Dict[str, Any]] = {{
    "initial": {{
        "name": "Etapa Inicial",
        "description": (
            "Etapa inicial do fluxo de {description}. "
            "A LIA coleta as informacoes fundamentais necessarias."
        ),
        "required_fields": [],
        "optional_fields": [],
        "transition_criteria": "Informacoes basicas coletadas.",
        "next_stage": "",
        "phase": "collection",
    }},
}}


def get_stage_context(stage: str, collected_fields: Dict[str, Any]) -> str:
    """Retorna o contexto formatado para o estágio atual.

    Args:
        stage: Identificador do estágio.
        collected_fields: Campos já coletados.

    Returns:
        String com o contexto do estágio para injeção no prompt.
    """
    stage_def = STAGE_DEFINITIONS.get(stage, STAGE_DEFINITIONS.get("initial", {{}}))

    required = stage_def.get("required_fields", [])
    optional = stage_def.get("optional_fields", [])

    missing_required = [f for f in required if collected_fields.get(f) in (None, "", [])]
    filled = [f for f in required if f not in missing_required]

    context_parts = [
        f"Estagio Atual: {{stage_def.get('name', stage)}}",
        f"Descricao: {{stage_def.get('description', '')}}",
        f"Campos Obrigatorios: {{', '.join(required) or 'nenhum'}}",
        f"Campos Opcionais: {{', '.join(optional) or 'nenhum'}}",
        f"Campos Preenchidos: {{', '.join(filled) or 'nenhum'}}",
        f"Campos Faltantes: {{', '.join(missing_required) or 'nenhum'}}",
    ]

    return "\\n".join(context_parts)


def get_transition_prompt(current_stage: str, next_stage: str) -> str:
    """Retorna o prompt de transição entre estágios.

    Args:
        current_stage: Estágio atual.
        next_stage: Próximo estágio.

    Returns:
        String com instruções para a transição.
    """
    current_def = STAGE_DEFINITIONS.get(current_stage, {{}})
    next_def = STAGE_DEFINITIONS.get(next_stage, {{}})

    return (
        f"Transicao de '{{current_def.get('name', current_stage)}}' "
        f"para '{{next_def.get('name', next_stage)}}'. "
        f"{{current_def.get('transition_criteria', '')}}"
    )
'''
