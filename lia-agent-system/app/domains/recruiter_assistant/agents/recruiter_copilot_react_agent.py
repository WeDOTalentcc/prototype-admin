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

# -- Fase 2 (2026-06-06): escopo dinamico de tools no agente federado --
import os as _os
import threading as _threading

_SCOPE_BUILD_LOCK = _threading.Lock()


def _scoped_tools_enabled() -> bool:
    """Escopo dinamico ativo se LIA_FEDERATED_SCOPED_TOOLS OU LIA_FEDERATED_PRIMARY
    (Fase 4: primario implica escopo). Off = comportamento atual identico."""
    try:
        from app.tools.scope_config import federated_scoping_enabled
        return federated_scoping_enabled()
    except Exception:
        return False


def _resolve_scoped_tool_defs(default_factory):
    """Tool-defs do turno: flag on + escopo ativo (contextvar) -> subconjunto escopado
    de TODOS os dominios; senao -> default_factory() (set federado). Fail-open."""
    if _scoped_tools_enabled():
        try:
            from app.tools.scope_config import get_active_scope
            scope = get_active_scope()
            if scope is not None:
                from app.shared.tool_catalog import get_scoped_tool_definitions
                _sc = scope.value if hasattr(scope, "value") else str(scope)
                scoped = get_scoped_tool_definitions(_sc)
                if scoped:
                    return scoped
        except Exception as _e:
            logger.warning("[RecruiterCopilot] scoped tool defs fallback: %s", _e)
    return default_factory()


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
    "CRIACAO DE VAGA A PARTIR DE EXISTENTE: SOMENTE quando o recrutador "
    "EXPLICITAMENTE pedir para criar/duplicar/clonar uma nova vaga usando outra "
    "como base/modelo: chame list_job_creation_sources, apresente as opcoes "
    "SEMPRE mostrando o ID da vaga e o recrutador (e o gestor), pergunte qual "
    "(ou aceite um nome/gestor para buscar), e entao chame "
    "start_creation_from_source com o id escolhido. "
    "CRITICO: NUNCA chame start_creation_from_source quando o recrutador quiser "
    "ABRIR, VER, ACESSAR, MOSTRAR ou NAVEGAR para uma vaga EXISTENTE — nesses "
    "casos use open_ui com capability='view_job_kanban' e entity_ids={'job_id': id}.\n\n"
    "NAVEGACAO vs DADOS: (a) 'ver candidatos dentro de uma vaga / abrir vaga X' "
    "= intent de NAVEGACAO -> open_ui(view_job_kanban). (b) 'liste candidatos da "
    "vaga X' sem pedido de navegar = intent de DADOS -> list_candidates no chat. "
    "Nao use funil_talentos como destino para ver candidatos de uma vaga especifica.\n\n"
    "MAPA DE NAVEGACAO (use open_ui(capability=X) para levar o recrutador a uma tela):\n"
    "  dashboard/indicadores/metricas -> ir_para_dashboard\n"
    "  tarefas/aprovacoes/pendencias/HITL -> ir_para_tasks\n"
    "  central de comunicacao/emails/whatsapp -> ir_para_central_comunicacao\n"
    "  biblioteca LIA/templates reutilizaveis -> ir_para_biblioteca\n"
    "  bancos de talentos/talent pools/candidatos antigos -> ir_para_bancos_talentos\n"
    "  lista de vagas/todas as vagas -> ir_para_vagas\n"
    "  trust/conformidade/LGPD/auditoria -> ir_para_trust\n"
    "  marketplace de agentes/instalar agente -> ir_para_marketplace\n"
    "  creditos de IA/saldo/consumo de IA -> ir_para_creditos_ia\n"
    "  integracoes/ATS externo -> ir_para_integracoes\n"
    "  ajuda/documentacao/suporte -> ir_para_ajuda\n"
    "  home/inicio/pagina inicial -> ir_para_home\n"
    "  configuracoes GENERICA (sem especificar secao) -> ir_para_configuracoes\n"
    "  funil de talentos/sourcing/busca de candidatos cross-vaga -> ir_para_funil_talentos\n"
    "  agent studio/agentes IA -> ir_para_agent_studio\n"
    "  chat em tela cheia/chat full/abrir chat dedicado -> open_fullscreen_chat\n"
    "VISAO GLOBAL = /recrutar (pipeline de recrutamento, etapas de selecao):\n"
    "  IMPORTANTE: visao global (/recrutar) EH DIFERENTE de funil de talentos (/funil-de-talentos)\n"
    "  CUIDADO: 'visao global de TALENTOS' = 'visao global de CANDIDATOS' = /recrutar, NAO funil!\n"
    "  visao global/pipeline overview/recrutar (todas as etapas) -> ir_para_visao_global\n"
    "  visao global aba candidatos / visao global de talentos / visao global de candidatos -> ir_para_visao_global_candidatos\n"
    "  visao global aba vagas (ciclo de vida das vagas) -> ir_para_visao_global_vagas\n"
    "CONFIGURACOES SECOES: ao pedir 'configuracoes de X', use ir_para_config_X (nao ir_para_configuracoes):\n"
    "  configuracoes de empresa/perfil/cultura/beneficios -> ir_para_config_empresa\n"
    "  configuracoes de LIA/instrucoes/personalidade/tom da IA -> ir_para_config_lia\n"
    "  configuracoes de instrucoes LIA por campo -> ir_para_config_instrucoes_lia\n"
    "  configuracoes de recrutamento/pipeline/processo seletivo -> ir_para_config_recrutamento\n"
    "  configuracoes de comunicacao/emails/templates/mensagens -> ir_para_config_comunicacao\n"
    "  configuracoes de alertas/notificacoes/alertas pipeline -> ir_para_config_alertas\n"
    "  configuracoes de usuarios/equipe/papeis/departamentos -> ir_para_config_usuarios\n"
    "  configuracoes de integracoes/ATS externo -> ir_para_config_integracoes\n"
    "  configuracoes de conformidade/LGPD/fairness/auditoria -> ir_para_config_conformidade\n"
    "Navegacao pura nao precisa de lookup previa.\n\n"
)

COPILOT_FEW_SHOT_EXAMPLES = (
    "Exemplo 1 — Usuario: 'resuma minhas vagas'\n"
    "  -> chame list_jobs e resuma os resultados reais (total, por status). "
    "Nunca diga 'nenhuma vaga' sem ter chamado list_jobs.\n"
    "Exemplo 2 — Usuario: 'liste meus candidatos para a vaga X' (SO DADOS, sem navegar)\n"
    "  -> chame list_candidates filtrando pela vaga e apresente no chat.\n"
    "Exemplo 3 — Usuario: 'mova a Maria para entrevista'\n"
    "  -> identifique a candidata, chame batch_move_candidates; a confirmacao "
    "humana sera solicitada antes de efetivar.\n"
    "Exemplo 4 — Usuario: 'me leve para a vaga X / me mostre o kanban da vaga X / "
    "quero ver os candidatos DENTRO da vaga X'\n"
    "  -> (intent de NAVEGACAO): chame list_jobs pra encontrar a vaga X, pegue o "
    "job_id, entao chame open_ui com capability='view_job_kanban' e "
    "entity_ids={'job_id': job_id_encontrado}. NUNCA va para funil de talentos "
    "para esse intent — o funil e para busca cross-vaga. O kanban da vaga e a "
    "tela correta pra 'ver candidatos dentro de uma vaga especifica'.\n"
    "Exemplo 5 — Usuario: 'me leve pro dashboard' / 'quero ver indicadores'\n"
    "  -> (navegacao pura): use o MAPA DE NAVEGACAO e chame "
    "open_ui(capability=X). Sem lookup previo — ir direto ao destino.\n"
    "Exemplo 6 — Usuario: 'me leva para a lista de vagas' / 'ir para vagas'\n"
    "  -> open_ui(capability='ir_para_vagas'). Sem chamada previa de list_jobs.\n"
    "Exemplo 7 — Usuario: 'abre configuracoes de alertas' / 'config de notificacoes'\n"
    "  -> open_ui(capability='ir_para_config_alertas'). NAO use ir_para_configuracoes (generica).\n"
    "Exemplo 8 — Usuario: 'visao global de candidatos' / 'visao global de talentos' / 'mostra candidatos por etapa'\n"
    "  -> open_ui(capability='ir_para_visao_global_candidatos'). NAO use ir_para_funil_talentos.\n"
    "  REGRA: NUNCA escreva [NAVIGATE:X] como texto — SEMPRE chame open_ui(capability='X') como ferramenta."
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
        "send_batch_communication",
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
            _txt = self._compose_runtime_prompt(
                input,
                agent_type="recruiter_assistant",
                domain_specific=COPILOT_DOMAIN_SPECIFIC,
                few_shot_examples=COPILOT_FEW_SHOT_EXAMPLES,
                reasoning_template=COPILOT_REASONING_PROMPT,
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=_stage,
            ).text
            # Fase 3 (2026-06-06): quando escopado (flag on + escopo ativo), anexa a
            # guidance do escopo (capabilities + restrictions) p/ o federado se
            # comportar como o agente de dominio faria. Reusa get_scope_system_prompt_addition.
            try:
                if _scoped_tools_enabled():
                    from app.tools.scope_config import (
                        get_active_scope,
                        get_scope_system_prompt_addition,
                    )
                    _scope = get_active_scope()
                    if _scope is not None:
                        _add = get_scope_system_prompt_addition(_scope)
                        if _add:
                            _txt = _txt + "\n\n" + _add
            except Exception:
                pass
            return _txt
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
        """Ativa GovernanceToolNode (HITL/audit). Fase 2: escopado quando flag on."""
        try:
            return _resolve_scoped_tool_defs(get_recruiter_copilot_tools)
        except Exception:
            return []

    def _get_tools(self) -> list:
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        tool_defs = _resolve_scoped_tool_defs(
            lambda: get_recruiter_copilot_tools() + self._get_all_enhanced_tools()
        )
        # wire-B: tee de response_blocks e canonico no converter (todos os agentes).
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]

    def _get_compiled_graph(self):
        """Fase 2: flag on + escopo ativo -> cacheia 1 grafo compilado POR ESCOPO
        (a base cacheia self._compiled single/build-once, que nao serve p/ tools que
        mudam por turno). Reusa o build da base (sem replicar) via reset-and-capture
        sob lock. Flag off / sem escopo = comportamento da base."""
        if not _scoped_tools_enabled():
            return super()._get_compiled_graph()
        try:
            from app.tools.scope_config import get_active_scope
            scope = get_active_scope()
        except Exception:
            scope = None
        if scope is None:
            return super()._get_compiled_graph()
        key = scope.value if hasattr(scope, "value") else str(scope)
        cache = self.__dict__.setdefault("_compiled_by_scope", {})
        g = cache.get(key)
        if g is not None:
            return g
        with _SCOPE_BUILD_LOCK:
            g = cache.get(key)
            if g is None:
                self._compiled = None
                g = super()._get_compiled_graph()
                cache[key] = g
                self._compiled = None
            return g

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
