"""
ReAct Agent Registry - Registro centralizado dos agentes ReAct.

Implementa o padrão Singleton para gerenciar todos os agentes de domínio
da plataforma LIA. Fornece registro, descoberta, instanciação e
monitoramento de status dos agentes.
"""
import logging
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

from lia_agents_core.working_memory import WorkingMemoryService
from lia_agents_core.observability import ReActObserver

if TYPE_CHECKING:
    from lia_agents_core.agent_interface import BaseAgent

logger = logging.getLogger(__name__)


class ReactAgentRegistry:
    """Registro singleton de todos os agentes ReAct disponíveis na plataforma.

    Mantém um mapeamento de domínio → classe de agente (não instâncias)
    e permite instanciação sob demanda, consulta de status e descoberta
    de capacidades.

    IMPORTANTE: O registry armazena CLASSES e configs, não instâncias.
    Para uso session-safe, utilize AgentFactory.create_agent() que cria
    uma instância nova a cada chamada.
    """

    _instance: Optional["ReactAgentRegistry"] = None
    _initialized: bool = False

    def __new__(cls) -> "ReactAgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, "BaseAgent"] = {}
        self._initialized = True
        logger.info("[ReactAgentRegistry] Inicializado")

    def register(
        self,
        domain: str,
        agent_class: Type["BaseAgent"],
        config: Optional[dict] = None,
    ) -> None:
        """Registra um agente no registry.

        Args:
            domain: Identificador do domínio (ex: 'wizard', 'pipeline').
            agent_class: Classe do agente que implementa BaseAgent.
            config: Configurações opcionais do agente.
        """
        self._registry[domain] = {
            "agent_class": agent_class,
            "config": config or {},
        }
        logger.info(
            f"[ReactAgentRegistry] Agente registrado: domain={domain} "
            f"class={agent_class.__name__}"
        )

    def get_agent(self, domain: str) -> "BaseAgent":
        """Retorna uma instância (cacheada) do agente para o domínio especificado.

        ATENÇÃO: Este método reutiliza instâncias cacheadas e NÃO é session-safe.
        Para criar instâncias isoladas por sessão, use AgentFactory.create_agent().

        Args:
            domain: Identificador do domínio.

        Returns:
            Instância do agente (pode ser compartilhada entre chamadas).

        Raises:
            KeyError: Se o domínio não estiver registrado.
        """
        if domain not in self._registry:
            raise KeyError(
                f"Domínio '{domain}' não registrado. "
                f"Domínios disponíveis: {list(self._registry.keys())}"
            )

        if domain not in self._instances:
            entry = self._registry[domain]
            agent_class = entry["agent_class"]
            self._instances[domain] = agent_class()
            logger.info(
                f"[ReactAgentRegistry] Instância criada: domain={domain} "
                f"class={agent_class.__name__}"
            )

        return self._instances[domain]

    def get_all_agents(self) -> Dict[str, "BaseAgent"]:
        """Retorna todas as instâncias de agentes registrados.

        Instancia agentes que ainda não foram criados.

        Returns:
            Dicionário domínio → instância do agente.
        """
        for domain in self._registry:
            if domain not in self._instances:
                self.get_agent(domain)
        return dict(self._instances)

    def list_domains(self) -> List[str]:
        """Lista todos os domínios registrados.

        Returns:
            Lista de identificadores de domínio.
        """
        return list(self._registry.keys())

    async def get_agent_status(self, domain: str) -> dict:
        """Retorna o status e saúde de um agente específico.

        Args:
            domain: Identificador do domínio.

        Returns:
            Dicionário com informações de status do agente.

        Raises:
            KeyError: Se o domínio não estiver registrado.
        """
        agent = self.get_agent(domain)
        try:
            status = await agent.get_status()
        except Exception as exc:
            logger.error(
                f"[ReactAgentRegistry] Erro ao obter status do agente {domain}: {exc}"
            )
            status = {
                "domain": domain,
                "status": "error",
                "error": str(exc),
            }
        return status

    def get_capabilities(self) -> dict:
        """Retorna as capacidades de todos os agentes registrados.

        Inclui domínio, classe, ferramentas disponíveis e configuração
        de cada agente.

        Returns:
            Dicionário com as capacidades de todos os agentes.
        """
        capabilities: Dict[str, Any] = {}
        for domain, entry in self._registry.items():
            agent_class = entry["agent_class"]
            agent_info: Dict[str, Any] = {
                "class": agent_class.__name__,
                "config": entry.get("config", {}),
            }

            if domain in self._instances:
                instance = self._instances[domain]
                agent_info["available_tools"] = instance.available_tools
                agent_info["domain_name"] = instance.domain_name
            else:
                agent_info["available_tools"] = []
                agent_info["domain_name"] = domain

            capabilities[domain] = agent_info

        return capabilities

    def is_registered(self, domain: str) -> bool:
        """Verifica se um domínio está registrado.

        Args:
            domain: Identificador do domínio.

        Returns:
            True se o domínio estiver registrado.
        """
        return domain in self._registry

    def __repr__(self) -> str:
        domains = ", ".join(self._registry.keys()) or "nenhum"
        return f"<ReactAgentRegistry domains=[{domains}]>"


def register_react_agents() -> ReactAgentRegistry:
    """Registra todos os 11 agentes ReAct da plataforma.

    Utiliza importação lazy para evitar dependências circulares.

    Returns:
        Instância do registry com todos os agentes registrados.
    """
    registry = ReactAgentRegistry()

    if registry.list_domains():
        logger.debug("[register_react_agents] Agentes já registrados, pulando")
        return registry

    from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent
    registry.register("wizard", WizardReActAgent, {
        "description": "Agente do wizard de criação de vagas",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
    registry.register("pipeline", PipelineReActAgent, {
        "description": "Agente do pipeline de triagem de CVs",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
    registry.register("sourcing", SourcingReActAgent, {
        "description": "Agente de sourcing e busca de candidatos",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
    registry.register("talent", TalentReActAgent, {
        "description": "Agente assistente de talentos",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
    registry.register("jobs_management", JobsMgmtReActAgent, {
        "description": "Agente de gestão de vagas",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
    registry.register("kanban", KanbanReActAgent, {
        "description": "Agente assistente do kanban de recrutamento",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
    registry.register("policy", PolicyReActAgent, {
        "description": "Agente de configuração de políticas de contratação",
        "model_provider": "claude",
        "max_iterations": 5,
        "langgraph_native": True,
    })

    from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
    registry.register("automation", AutomationReActAgent, {
        "description": "Agente de decomposição de tarefas e planejamento de execução",
        "model_provider": "claude",
        "max_iterations": 6,
        "langgraph_native": True,
    })

    from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
    registry.register("analytics", AnalyticsReActAgent, {
        "description": "Agente de analytics, KPIs e previsões de contratação",
        "model_provider": "claude",
        "max_iterations": 6,
        "langgraph_native": True,
    })

    from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
    registry.register("communication", CommunicationReActAgent, {
        "description": "Agente de comunicação multi-canal com conformidade LGPD",
        "model_provider": "claude",
        "max_iterations": 6,
        "langgraph_native": True,
    })

    from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
    registry.register("ats_integration", ATSIntegrationReActAgent, {
        "description": "Agente de integração bidirecional com plataformas ATS",
        "model_provider": "claude",
        "max_iterations": 6,
        "langgraph_native": True,
    })

    logger.info(
        f"[register_react_agents] {len(registry.list_domains())} agentes registrados: "
        f"{registry.list_domains()}"
    )

    return registry


class AgentFactory:
    """Fábrica para instanciação de agentes com contexto de sessão.

    Encapsula a criação de agentes garantindo que o registry esteja
    inicializado e fornecendo uma interface simplificada para o
    restante da aplicação.
    """

    def __init__(self, registry: Optional[ReactAgentRegistry] = None) -> None:
        """Inicializa a fábrica.

        Args:
            registry: Registry a utilizar. Se não fornecido, usa o singleton.
        """
        self._registry = registry or ReactAgentRegistry()

    def create_agent(
        self,
        domain: str,
        session_id: str,
        company_id: str,
        user_id: str,
    ) -> "BaseAgent":
        """Cria uma instância NOVA do agente para o domínio e sessão especificados.

        Cada chamada cria uma instância fresca com seu próprio
        WorkingMemoryService e ReActObserver, garantindo isolamento
        entre sessões e evitando vazamento de estado.

        Args:
            domain: Identificador do domínio do agente.
            session_id: Identificador da sessão.
            company_id: Identificador da empresa (multi-tenancy).
            user_id: Identificador do usuário.

        Returns:
            Instância nova do agente pronta para uso.

        Raises:
            KeyError: Se o domínio não estiver registrado.
        """
        if not self._registry.is_registered(domain):
            raise KeyError(
                f"Domínio '{domain}' não registrado. "
                f"Domínios disponíveis: {self._registry.list_domains()}"
            )

        entry = self._registry._registry[domain]
        agent_class = entry["agent_class"]

        agent = agent_class()

        agent._session_context = {
            "session_id": session_id,
            "company_id": company_id,
            "user_id": user_id,
        }

        agent._working_memory_service = WorkingMemoryService()

        agent._observer = ReActObserver(
            session_id=session_id,
            domain=domain,
            agent_class=agent_class.__name__,
        )

        logger.debug(
            f"[AgentFactory] Nova instância criada: domain={domain} "
            f"session={session_id} company={company_id} "
            f"class={agent_class.__name__}"
        )

        return agent
