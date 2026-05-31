"""Wizard Orchestrator — tool-calling agent loop (cérebro conversacional).

Strangler-fig migration (decisão Paulo 2026-05-31): substitui o pipeline
LangGraph rígido + 3 classifiers desconectados (supervisor / gate / meta-helper)
por UM cérebro state-aware por turno que vê a ficha viva completa, decide a
ação E gera a resposta, chamando as capacidades determinísticas
(:mod:`wizard_tools`) como tools.

## Por que isto resolve a "burrice"

O fluxo legado tinha 3 LLMs com visão de buraco de fechadura, nenhum vendo o
estado completo, com allowlists travadas por stage (impossível corrigir um
campo anterior mid-fluxo) e respostas canned para 90% dos turnos. Aqui:

  - **Um cérebro, estado completo**: o system prompt carrega a ficha viva
    (campos preenchidos/faltantes, JD, competências, modo). O modelo responde
    "faltam X e Y" com precisão, não spiel genérico.
  - **Navegação não-linear**: o modelo pode chamar ``set_job_fields`` para
    corrigir a senioridade a qualquer momento — não há jaula de stage.
  - **Determinismo onde importa**: multi-tenancy, validação e (increment 2)
    fairness/LGPD vivem nas tools, não na geração livre do LLM.

## Segurança

  - **FairnessGuard L1** roda sobre a mensagem do recrutador ANTES do loop.
  - **Multi-tenancy**: ``ToolContext.company_id`` (JWT) é a única fonte; tools
    rejeitam ``company_id`` vindo de args da LLM.
  - **Guard de iterações**: ``max_iterations`` impede loop infinito de tool_use.
  - **Fail-soft**: erro de tool vira ``tool_result`` com instrução de correção
    realimentada ao modelo (não derruba o turno). Erro de LLM → reply de
    fallback (nunca silent — loga + telemetria).

## Cliente LLM injetável

``process_turn(..., llm_client=...)`` aceita qualquer objeto com
``.messages.create(**kwargs)`` retornando ``.content`` (lista de blocks com
``.type`` ∈ {text, tool_use}) e ``.stop_reason``. Produção usa o SDK
``anthropic.Anthropic``; testes injetam um fake scriptado. Sem flag/env no
core — a decisão de ligar vive no caller (``LIA_WIZARD_ORCHESTRATOR``).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from app.shared.llm_models import CANONICAL_SONNET_MODEL

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    WizardTool,
    build_tool_registry,
)

logger = logging.getLogger(__name__)


_DEFAULT_MODEL = os.environ.get("LIA_WIZARD_ORCHESTRATOR_MODEL", CANONICAL_SONNET_MODEL)


def _get_timeout_s() -> float:
    try:
        return float(os.environ.get("LIA_WIZARD_ORCHESTRATOR_TIMEOUT_S", "20"))
    except (TypeError, ValueError):
        return 20.0


def _get_max_iterations() -> int:
    try:
        return max(1, int(os.environ.get("LIA_WIZARD_ORCHESTRATOR_MAX_ITERS", "6")))
    except (TypeError, ValueError):
        return 6


_SYSTEM_PROMPT_BASE = (
    "Você é a LIA, assistente de IA de recrutamento da WeDoTalent, conduzindo "
    "a criação de uma vaga em uma conversa natural com o recrutador.\n\n"
    "## Seu objetivo\n"
    "Coletar e confirmar as informações da vaga (título, senioridade, modelo de "
    "trabalho, departamento, gestor, competências, modo de triagem), gerar uma "
    "descrição de qualidade e preparar a vaga para publicação — de forma "
    "conversacional e inteligente, não como um formulário rígido.\n\n"
    "## Como agir\n"
    "- VEJA o estado real da vaga (ficha viva) que receberá abaixo. Responda com "
    "precisão: se o recrutador perguntar 'o que falta?', liste exatamente os "
    "campos faltantes da ficha.\n"
    "- Use as TOOLS para registrar dados (set_job_fields), definir modo "
    "(set_screening_mode), confirmar competências (confirm_competencies) e "
    "consultar status (get_wizard_status). Chame a tool assim que o recrutador "
    "fornecer um dado — não apenas reconheça verbalmente.\n"
    "- O recrutador pode CORRIGIR algo a qualquer momento (ex.: mudar a "
    "senioridade depois de já ter dado o título). Chame set_job_fields para "
    "atualizar — nunca diga que não pode.\n"
    "- Salário: use suggest_salary para buscar a faixa de mercado (informe a "
    "fonte ao recrutador). Se ele informar/ajustar valores, use set_salary.\n"
    "- Navegação: se o recrutador pedir para ir à página de vagas ou abrir a "
    "vaga, chame navigate_to_jobs (você CONSEGUE navegá-lo — não diga que não "
    "consegue).\n"
    "- Confirme as competências ANTES de tratar a descrição como final. Para "
    "ADICIONAR ou REMOVER uma competência depois de confirmadas, olhe a lista "
    "atual na ficha viva, monte a lista COMPLETA atualizada (atuais ± a mudança) "
    "e chame confirm_competencies com o conjunto inteiro (a tool substitui a "
    "lista, não faz append).\n"
    "- Fluxo da descrição: gere com enrich_job_description; quando o recrutador "
    "aprovar ('aprovo', 'pode seguir'), chame approve_job_description.\n"
    "- Triagem WSI: depois da descrição aprovada, gere as perguntas de triagem "
    "com generate_wsi_questions (metodologia CBI + Bloom + Dreyfus + Big Five, "
    "dimensionada pelo modo). O recrutador pode pedir ajustes: regenerar tudo "
    "(regenerate_wsi_questions), remover uma (remove_wsi_question), reescrever "
    "uma (edit_wsi_question) ou adicionar uma (add_wsi_question). Quando ele "
    "aprovar, chame approve_wsi_questions. Só então publish_job (com confirm=true).\n"
    "- NUNCA invente dados da vaga, da empresa ou do candidato.\n"
    "- NUNCA tome ação irreversível (publicar) sem confirmação explícita.\n\n"
    "## REGRA CRÍTICA — não alucinar ações\n"
    "NUNCA afirme que uma ação aconteceu (vaga publicada, descrição gerada, "
    "email registrado, competências salvas) sem ter chamado a TOOL "
    "correspondente E recebido sucesso nela. Se a tool não foi chamada, falhou, "
    "ou um pré-requisito falta, diga a verdade sobre o estado atual e qual é o "
    "próximo passo real — jamais finja sucesso. Não diga 'publicada com sucesso' "
    "a menos que publish_job tenha retornado um job_id.\n\n"
    "## Email do gestor\n"
    "O email do gestor é capturado AUTOMATICAMENTE do texto pelo sistema (por "
    "LGPD você verá '[EMAIL REMOVIDO]' no lugar — é normal). NÃO peça o formato "
    "do email, NÃO valide, NÃO insista: se o recrutador mencionou um email, ele "
    "já está registrado. Confira a ficha viva para ver se o email já consta.\n\n"
    "- Respostas curtas, calorosas e objetivas em PT-BR. Termine com um próximo "
    "passo claro ou uma pergunta de continuidade.\n"
    "- NUNCA repita literalmente sua última resposta; consulte o histórico."
)


@dataclass
class OrchestratorResult:
    """Resultado de um turno do orquestrador."""

    reply: str
    state_updates: dict[str, Any] = field(default_factory=dict)
    fairness_blocked: bool = False
    tool_calls: list[str] = field(default_factory=list)
    iterations: int = 0
    error: bool = False


def _extract_history_messages(state: dict, n: int = 6) -> list[dict[str, Any]]:
    """Converte ``conversation_messages`` em mensagens Anthropic (últimas N).

    Formato canonical: ``[{"role": "user"|"assistant", "content": "..."}]``.
    Bounded e truncado por turno. Fail-open: state malformado → lista vazia.
    """
    try:
        msgs = state.get("conversation_messages") or []
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for m in list(msgs)[-n:]:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        out.append({"role": role, "content": content[:2000]})
    return out


class WizardOrchestrator:
    """Tool-calling agent state-aware para criação de vaga.

    Stateless e thread-safe (singleton via :func:`get_wizard_orchestrator`).
    Não persiste state — o caller passa o ``state`` atual e aplica os
    ``state_updates`` retornados.
    """

    def __init__(
        self,
        *,
        tools: Optional[tuple[WizardTool, ...]] = None,
        model: Optional[str] = None,
    ) -> None:
        self._registry = build_tool_registry(tools or ())
        self._model = model or _DEFAULT_MODEL

    # ── LLM client (produção) ──────────────────────────────────────────
    @staticmethod
    def _resolve_anthropic_config(company_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Resolve (api_key, base_url) Anthropic POR-TENANT via LLM Factory (BYOK).

        Choose Your AI / BYOK: a chave do tenant (carregada do DB pelo
        TenantProviderRegistry) tem precedência sobre a chave global. Reusa os
        helpers canônicos da factory (mesma resolução do create_tracked_llm),
        então o cérebro de chat do orquestrador passa a honrar a chave/modelo
        per-tenant + proxy modelfarm. Fail-open para env global.
        """
        api_key = None
        base_url = None
        try:
            from app.shared.providers.llm_factory import (
                _resolve_provider_chain,
                _resolve_provider_api_key,
                _resolve_provider_base_url,
            )
            _, _, tenant_keys = _resolve_provider_chain(company_id or None)
            api_key = tenant_keys.get("claude") or _resolve_provider_api_key("claude")
            base_url = _resolve_provider_base_url("claude")
        except Exception as exc:  # noqa: BLE001 — fail-open ao env global
            logger.debug("[WizardOrchestrator] factory resolve failed (fallback env): %s", exc)
        # Fallback ao env global se a factory não resolveu a chave.
        api_key = api_key or (
            os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        base_url = base_url or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        return api_key, base_url

    @classmethod
    def _build_anthropic_client(cls, company_id: Optional[str] = None) -> Optional[Any]:
        api_key, base_url = cls._resolve_anthropic_config(company_id)
        if not api_key:
            logger.warning("[WizardOrchestrator] no API key — cannot run")
            return None
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:  # pragma: no cover — dep oficial
            return None
        kwargs: dict[str, Any] = {"api_key": api_key, "timeout": _get_timeout_s()}
        if base_url:
            kwargs["base_url"] = base_url
        try:
            return Anthropic(**kwargs)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("[WizardOrchestrator] client init failed: %s", exc)
            return None

    def _build_system_prompt(self, state: dict) -> str:
        try:
            from app.domains.job_creation.internal.utils import (
                _build_wizard_state_summary,
            )
            ficha = _build_wizard_state_summary(state)
        except Exception:  # noqa: BLE001
            ficha = "(estado não disponível)"
        tenant = str(state.get("tenant_context_snippet") or "").strip()
        tenant_block = (
            f"\n\n## Contexto da empresa\n{tenant[:600]}" if tenant else ""
        )
        return (
            f"{_SYSTEM_PROMPT_BASE}\n\n"
            f"## Estado real da vaga (ficha viva)\n{ficha}"
            f"{tenant_block}"
        )

    # ── Loop principal ─────────────────────────────────────────────────
    def process_turn(
        self,
        *,
        state: dict,
        user_message: str,
        ctx: ToolContext,
        llm_client: Optional[Any] = None,
    ) -> OrchestratorResult:
        """Processa um turno conversacional. Sync por contrato (SDK síncrono)."""
        msg = (user_message or "").strip()
        if not msg:
            return OrchestratorResult(
                reply="Não recebi sua mensagem. Pode repetir?", error=True
            )

        # 1) FairnessGuard L1 — viés explícito do recrutador é bloqueado.
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard().check(msg)
            if fg.is_blocked:
                logger.warning(
                    "[WizardOrchestrator] FairnessGuard L1 BLOCK cat=%s",
                    fg.category,
                )
                return OrchestratorResult(
                    reply=fg.educational_message
                    or "Não posso seguir com critérios discriminatórios.",
                    fairness_blocked=True,
                )
        except Exception as exc:  # noqa: BLE001 — fail-open: guard não trava fluxo
            logger.debug("[WizardOrchestrator] FairnessGuard failed (open): %s", exc)

        client = llm_client or self._build_anthropic_client(getattr(ctx, "company_id", None))
        if client is None:
            return OrchestratorResult(
                reply=(
                    "Estou com uma indisponibilidade técnica no momento. "
                    "Pode tentar de novo em instantes?"
                ),
                error=True,
            )

        system_prompt = self._build_system_prompt(state)
        tool_schemas = [t.anthropic_schema() for t in self._registry.values()]
        messages: list[dict[str, Any]] = _extract_history_messages(state)
        messages.append({"role": "user", "content": msg})

        # Working copy do state — tools veem mutações acumuladas dentro do loop.
        working_state = dict(state)
        accumulated_updates: dict[str, Any] = {}
        tool_calls: list[str] = []
        max_iters = _get_max_iterations()

        for iteration in range(1, max_iters + 1):
            try:
                response = client.messages.create(
                    model=self._model,
                    max_tokens=1024,
                    temperature=0.3,
                    system=system_prompt,
                    messages=messages,
                    tools=tool_schemas,
                )
            except Exception as exc:
                logger.info(
                    "[WizardOrchestrator] LLM call failed iter=%d: %s",
                    iteration, exc,
                )
                return OrchestratorResult(
                    reply=(
                        "Tive um problema ao processar agora. Pode repetir "
                        "ou reformular?"
                    ),
                    state_updates=accumulated_updates,
                    tool_calls=tool_calls,
                    iterations=iteration,
                    error=True,
                )

            content_blocks = list(getattr(response, "content", []) or [])
            tool_uses = [
                b for b in content_blocks
                if getattr(b, "type", None) == "tool_use"
            ]
            text_parts = [
                getattr(b, "text", "") or ""
                for b in content_blocks
                if getattr(b, "type", None) == "text"
            ]

            # Sem tool_use → turno termina com a resposta textual do modelo.
            if not tool_uses:
                reply = " ".join(p for p in text_parts if p).strip()
                return OrchestratorResult(
                    reply=reply or "Certo! Como deseja seguir?",
                    state_updates=accumulated_updates,
                    tool_calls=tool_calls,
                    iterations=iteration,
                )

            # Há tool_use → executa cada uma, monta tool_result, continua loop.
            assistant_content: list[dict[str, Any]] = []
            for b in content_blocks:
                btype = getattr(b, "type", None)
                if btype == "text":
                    assistant_content.append(
                        {"type": "text", "text": getattr(b, "text", "") or ""}
                    )
                elif btype == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": getattr(b, "id", ""),
                        "name": getattr(b, "name", ""),
                        "input": getattr(b, "input", {}) or {},
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                name = getattr(tu, "name", "")
                tool_input = getattr(tu, "input", {}) or {}
                tu_id = getattr(tu, "id", "")
                tool_calls.append(name)
                tool = self._registry.get(name)
                if tool is None:
                    result_text = (
                        f"Tool desconhecida: {name}. Tools disponíveis: "
                        f"{', '.join(sorted(self._registry))}."
                    )
                    is_error = True
                else:
                    try:
                        result = tool.handler(working_state, tool_input, ctx)
                        result_text = result.llm_message
                        is_error = result.error
                        if result.state_updates:
                            accumulated_updates.update(result.state_updates)
                            working_state.update(result.state_updates)
                    except Exception as exc:  # noqa: BLE001 — fail-soft p/ o LLM
                        logger.warning(
                            "[WizardOrchestrator] tool %s raised: %s", name, exc
                        )
                        result_text = (
                            f"A tool {name} falhou: {exc}. Tente outra abordagem "
                            f"ou peça o dado ao recrutador."
                        )
                        is_error = True
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu_id,
                    "content": result_text,
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        # Esgotou iterações — devolve melhor esforço sem loop infinito.
        logger.warning(
            "[WizardOrchestrator] max_iterations=%d reached", max_iters
        )
        return OrchestratorResult(
            reply=(
                "Registrei o que consegui até aqui. Quer revisar os dados ou "
                "seguir para o próximo passo?"
            ),
            state_updates=accumulated_updates,
            tool_calls=tool_calls,
            iterations=max_iters,
        )


_default_orchestrator: Optional[WizardOrchestrator] = None


def get_wizard_orchestrator() -> WizardOrchestrator:
    """Singleton accessor — stateless, thread-safe.

    O singleton de produção inclui as service-backed tools (I/O via serviços
    canônicos). A classe ``WizardOrchestrator`` continua desacoplada (tools
    passadas no construtor) para testes I/O-free; só o accessor força o import
    do módulo service-backed.
    """
    global _default_orchestrator  # noqa: PLW0603
    if _default_orchestrator is None:
        try:
            from app.domains.job_creation.orchestrator.wizard_service_tools import (
                SERVICE_TOOLS,
            )
        except Exception as exc:  # noqa: BLE001 — degrada para tools puras
            logger.warning(
                "[WizardOrchestrator] service tools indisponíveis: %s", exc
            )
            SERVICE_TOOLS = ()
        _default_orchestrator = WizardOrchestrator(tools=SERVICE_TOOLS)
    return _default_orchestrator
