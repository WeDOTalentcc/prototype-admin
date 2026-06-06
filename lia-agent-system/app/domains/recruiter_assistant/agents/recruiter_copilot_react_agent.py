# G7 ok: federation agent — tools vem dos registries canonicos jobs_mgmt/talent/kanban via recruiter_copilot_tool_registry; FairnessGuard (_fairness_pre_check), audit, PII redaction e LLM Factory sao herdados via GovernanceToolNode + TenantAwareAgentMixin. Nao reimplementa.
"""
RecruiterCopilotReActAgent — agente GLOBAL federado do chat lateral da LIA.

Fix canonical (no PRODUTOR) do bug "chat global cego" (transcript Paulo
2026-06-03): o dominio `recruiter_assistant` resolvia pra UM agente de pagina
(talent OU kanban) sem `list_jobs` -> "liste minhas vagas" caia num LLM sem
ferramenta e confabulava "nenhuma vaga cadastrada".

Agora `recruiter_assistant` resolve pra ESTE agente unico, cujo toolset e
FEDERADO (vagas + candidatos + pipeline) via recruiter_copilot_tool_registry.
Padrao enterprise Apollo/Notion: uma superficie de ferramentas, qualquer tela.

Compliance: cada tool federada carrega multi-tenancy (company_id fail-closed),
audit e HITL do seu registry de origem; _fairness_pre_check roda no process();
agent_type='recruiter_assistant' (decision domain) injeta os blocos LGPD/
fairness/bias via PromptComposer.
"""
import logging

from lia_agents_core.agent_interface import AgentAction, AgentInput, AgentOutput
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
    get_recruiter_copilot_tools,
)
from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.prompts.prompt_composer import PromptComposer
from app.shared.services.confidence_policy_service import confidence_policy_service

logger = logging.getLogger(__name__)


COPILOT_DOMAIN_SPECIFIC = (
    "Voce e a LIA no chat lateral global da plataforma WeDOTalent — o copiloto "
    "de recrutamento. Diferente dos assistentes presos a uma tela, voce enxerga "
    "e age sobre TUDO: vagas, candidatos e pipeline.\n\n"
    "Quando o recrutador perguntar sobre vagas (listar, resumir, detalhar, "
    "portfolio), USE as ferramentas de vagas — NUNCA responda de cabeca nem diga "
    "que nao ha vagas sem ter chamado list_jobs. Quando perguntar sobre "
    "candidatos, USE list_candidates/search_candidates/view_candidate_profile. "
    "Para pipeline use get_pipeline_summary/list_stage_candidates.\n\n"
    "Acoes de escrita (mover candidatos entre etapas, pausar/reabrir vaga) sao "
    "permitidas, mas passam por confirmacao humana (HITL) antes de efetivar.\n\n"
    "Se uma ferramenta falhar ou nao retornar dados, DIGA isso claramente "
    "('nao consegui consultar agora') — jamais invente um resultado vazio.\n\n"
    "REGRA DE ENTIDADE NOMEADA (critico): quando o recrutador NOMEAR algo "
    "especifico, passe esse nome como filtro/query da ferramenta — NUNCA liste "
    "tudo generico. (a) 'perfil/mostre o candidato <Nome>' -> chame "
    "search_candidates com query=<Nome> PRIMEIRO; se achar, apresente/abra o "
    "perfil dele; NAO pergunte o nome que o recrutador JA deu. (b) 'candidatos/"
    "pipeline/rankear da vaga <Titulo>' -> chame list_jobs, ENCONTRE a vaga com "
    "esse titulo e use o id DELA na ferramenta seguinte "
    "(rank_candidates/get_pipeline_summary); jamais narre uma vaga de titulo "
    "diferente do que o recrutador pediu.\n\n"
    "RELAXAR FILTRO so vale para busca POR ATRIBUTOS (skills, senioridade, "
    "local): se 0 resultados, relaxe o filtro mais restritivo e ofereca opcoes "
    "com contagem. MAS se a busca for por NOME EXATO de candidato ou TITULO de "
    "vaga e nao houver correspondencia, diga claramente que NAO existe esse "
    "nome/titulo na base — NUNCA relaxe para listar todos.\n\n"
    "Quando o recrutador quiser criar uma vaga a partir de uma existente ou de "
    "um modelo/arquetipo: chame list_job_creation_sources, apresente as opcoes "
    "SEMPRE mostrando o ID da vaga e o recrutador (e o gestor), pergunte qual "
    "(ou aceite um nome/gestor para buscar), e entao chame "
    "start_creation_from_source com o id escolhido."
)

COPILOT_FEW_SHOT_EXAMPLES = (
    "Exemplo 1 — Usuario: 'resuma minhas vagas'\n"
    "  -> chame list_jobs e resuma os resultados reais (total, por status). "
    "Nunca diga 'nenhuma vaga' sem ter chamado list_jobs.\n"
    "Exemplo 2 — Usuario: 'liste meus candidatos para a vaga X'\n"
    "  -> chame list_candidates filtrando pela vaga.\n"
    "Exemplo 3 — Usuario: 'mova a Maria para entrevista'\n"
    "  -> identifique a candidata, chame batch_move_candidates; a confirmacao "
    "humana sera solicitada antes de efetivar."
)

# IMPORTANTE: apenas os placeholders {memory_summary} e {stage_context} sao
# permitidos aqui (substituidos em runtime). Nao adicionar outras chaves.
COPILOT_REASONING_PROMPT = (
    "Pense passo-a-passo: (1) identifique se a pergunta e sobre vagas, "
    "candidatos ou pipeline; (2) escolha a ferramenta de LEITURA adequada e "
    "chame-a com os filtros certos; (3) responda com base no resultado REAL da "
    "ferramenta. Para acoes de escrita, confirme a intencao antes.\n"
    "Memoria da conversa: {memory_summary}\n"
    "Contexto de tela: {stage_context}"
)


@register_agent("recruiter_copilot")
class RecruiterCopilotReActAgent(
    TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin
):
    """Agente global federado: vagas + candidatos + pipeline numa superficie."""

    # Acoes de escrita exigem HITL (confirmacao humana) antes de efetivar.
    _HITL_ACTION_TYPES = frozenset({
        "batch_move_candidates",
        "bulk_candidate_move",
        "pause_job",
        "reopen_job",
        "publish_vacancy",
        "unpublish_vacancy",
    })

    DOMAIN_INSTRUCTIONS = PromptComposer.for_domain(
        agent_type="recruiter_assistant",
        domain_specific=COPILOT_DOMAIN_SPECIFIC,
        few_shot_examples=COPILOT_FEW_SHOT_EXAMPLES,
        reasoning_pattern=COPILOT_REASONING_PROMPT.format(
            memory_summary="", stage_context=""
        ),
    ).text

    def _get_runtime_domain_instructions(self, input: AgentInput) -> str:
        try:
            from app.orchestrator.context.view_context import (
                format_view_context,
                view_context_from_context,
            )
            ctx = input.context or {}
            # P0.1: estado-da-tela vivo no prompt (chat abre ciente da visao atual).
            # Sintetiza view_context dos sinais que o FE JA envia (page_type, ids).
            _view_block = format_view_context(view_context_from_context(ctx))
            _stage = ctx.get("stage_context", "") or ""
            if _view_block:
                _stage = (_view_block + "\n\n" + _stage).strip()
            return self._compose_runtime_prompt(
                input,
                agent_type="recruiter_assistant",
                domain_specific=COPILOT_DOMAIN_SPECIFIC,
                few_shot_examples=COPILOT_FEW_SHOT_EXAMPLES,
                reasoning_template=COPILOT_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=_stage,
            ).text
        except Exception as exc:
            logger.warning(
                "[recruiter_copilot] runtime prompt composition failed: %s — "
                "fallback para DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def __init__(self) -> None:
        super().__init__()
        # PII fix (2026-06-05): o input-strip da base (LIA-C04) apagava nomes/
        # titulos que o RECRUTADOR digita ('Felipe Almeida', 'Diretor Juridico')
        # antes do LLM -> [PERSON REMOVIDO] -> busca por entidade quebrava. No
        # chat do recrutador o nome e NECESSARIO + AUTORIZADO (multi-tenancy) +
        # output continua mascarado + candidato ja vai ao LLM no screening. Logo
        # input-strip aqui e contraproducente. Output masking permanece.
        self._enable_pii_strip = False
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_recruiter_copilot_tools()]
        self._setup_enhanced(domain="recruiter_copilot")
        logger.info(
            "[RecruiterCopilotReActAgent] Initialized federated tools=%s",
            self._all_tool_names,
        )

    @property
    def domain_name(self) -> str:
        return self.__dict__.get("_domain_name_override", "recruiter_copilot")

    @domain_name.setter
    def domain_name(self, value: str) -> None:
        self.__dict__["_domain_name_override"] = value

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode (HITL/audit) para o set federado."""
        try:
            return get_recruiter_copilot_tools()
        except Exception:
            return []

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = get_recruiter_copilot_tools() + self._get_all_enhanced_tools()
        # wire-B (2026-06-06): o tee de response_blocks agora e canonico no
        # converter tool_definition_to_langchain_tool (vale p/ TODOS os agentes).
        # Removido o tee manual daqui p/ evitar double-append no sink.
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        messages = state.get("messages", [])
        response = ""
        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break
        if not response:
            response = "Desculpe, não consegui processar sua solicitação."

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        _confidence = 0.82 if actions else 0.75
        if state.get("error"):
            _confidence = 0.40
        _conf_action = confidence_policy_service.get_action_for_confidence(_confidence)

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=_confidence,
            metadata={
                "source": "langgraph_native",
                "domain": self.domain_name,
                "confidence_action": _conf_action.value,
            },
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        _blocked_msg = await self._fairness_pre_check(input.message or "")
        if _blocked_msg:
            return AgentOutput(
                message=_blocked_msg,
                confidence=1.0,
                metadata={"source": "fairness_guard", "domain": self.domain_name},
            )

        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        _hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=self._HITL_ACTION_TYPES,
            agent_name="recruiter_copilot_react_agent",
            description_template=(
                "Confirmar **{action_type}**. Acoes de escrita (mover candidatos, "
                "pausar/reabrir vaga) afetam dados reais do pipeline."
            ),
        )
        if _hitl_response is not None:
            return _hitl_response

        # wire-B (2026-06-06): reset/drain do sink agora e canonico em
        # LangGraphReActBase._process_langgraph (vale p/ TODOS os domain agents).
        # Removido daqui p/ evitar double-drain.
        return await self._process_langgraph(input)

    async def get_status(self) -> dict:
        return {
            "domain": self.domain_name,
            "available_tools": self.available_tools,
            "status": "ready",
            "max_iterations": 5,
            "model_provider": "claude",
        }
