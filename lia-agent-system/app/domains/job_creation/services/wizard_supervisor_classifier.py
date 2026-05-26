"""Wizard Supervisor Classifier — Task #1127 (T1.1).

Classificador LLM **pre-graph** que decide a INTENÇÃO GLOBAL do recrutador
antes do ``JobCreationGraph`` ser invocado em qualquer turno do wizard de
criação de vaga. Espelha o padrão arquitetural do
``IntakeIntentClassifier`` (Task #1098) e do ``WizardGateClassifier``
(Task #1085): Pydantic schema + allowlist enforced + sync por contrato
+ fail-OPEN em qualquer erro + env-flagged.

## Por que existir

O wizard hoje assume implicitamente que toda mensagem do recrutador é
"continuar o fluxo atual". Mas o usuário enterprise muda de intenção
mid-flow: cancela, pergunta meta, quer abrir uma SEGUNDA vaga sem
descartar a primeira, ou retomar um draft. Sem um supervisor explícito,
essas intenções vazam para os nós do graph e produzem:

  - perguntas meta tratadas como JD ("o que você precisa de mim?" vira
    título de vaga em ``intake_node``);
  - "cancela" tratado como resposta de gate (FairnessGuard / classifier
    interpretam como rejeição de candidato);
  - "abre outra vaga" descarta silenciosamente o draft atual.

O supervisor classifica em 6 intents canônicos e devolve ao caller
(``WizardSessionService.process_message``) uma decisão DETERMINÍSTICA
sobre a rota.

## Allowlist canônica (NÃO estender sem RFC)

  * ``create_new`` — recrutador pediu uma vaga NOVA (sem indicar que
    quer descartar a atual). Caller decide UX (sugerir abrir paralela,
    ou confirmar descarte do draft atual).
  * ``resume_draft`` — recrutador pediu para RETOMAR um draft anterior
    (referência explícita: "retoma a vaga de ontem", "o draft do dev").
  * ``edit_published`` — recrutador quer EDITAR uma vaga já publicada
    ("muda a vaga de engenheiro pleno", "ajusta a do gerente").
  * ``meta_question`` — pergunta meta sobre o wizard, o que a LIA
    precisa, como funciona, onde está o painel. SHORT-CIRCUIT do graph:
    caller responde via ``wizard_meta_question_helper`` e NÃO avança o
    nó atual.
  * ``exit_wizard`` — recrutador quer SAIR do wizard ("cancela", "deixa
    pra lá", "tchau"). Caller emite mensagem de despedida; não muta
    state.
  * ``continue_current`` — default: a mensagem é parte natural do fluxo
    atual (resposta a gate, follow-up de JD, etc). Caller passa ao graph
    sem mudança.

## Segurança

- Mutação de state pelo supervisor: ZERO. O caller decide com base no
  ``intent`` retornado. ``conversational_reply`` é texto de UX, nunca
  controle de fluxo.
- ``FairnessGuard`` continua rodando dentro dos nós do graph (não é
  responsabilidade desta camada).
- ``tenant_context_snippet`` é passado APENAS como contexto opcional
  para o LLM (snippet curto, sem PII).
- Fail-OPEN: em qualquer falha devolve ``None`` → caller trata como
  ``continue_current`` (preserva fluxo legacy).
- Env-flagged: ``LIA_WIZARD_SUPERVISOR_CLASSIFIER`` (default ON em
  dev/test, OFF em prod/staging até GA). Quando OFF, ``classify_sync``
  retorna ``None`` imediatamente — zero custo, zero risco.

## Sync por contrato

Mesmo padrão de ``IntakeIntentClassifier``: ``process_message`` é async
mas a chamada ao supervisor é síncrona (sem ``await``) porque o SDK
``anthropic.Anthropic`` é síncrono. O sync call está dentro de
``asyncio.to_thread`` no caller para não bloquear o event loop.

## Custo

Haiku ~$0.0005/turno, ≤300 tokens, p95 ≤700ms, timeout default 5s.
Só dispara em wizard turns (≤2% dos turnos totais do chat).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Literal

from app.shared.llm_models import CANONICAL_HAIKU_MODEL

logger = logging.getLogger(__name__)


# Allowlist canônica. NÃO estender sem RFC.
ALLOWED_SUPERVISOR_INTENTS: frozenset[str] = frozenset({
    "create_new",
    "resume_draft",
    "edit_published",
    "meta_question",
    "exit_wizard",
    "continue_current",
})


def is_supervisor_enabled() -> bool:
    """Read at call-time. Default: ON em dev/test, OFF em prod/staging.

    Mesma postura do ``LIA_WIZARD_LLM_GATES`` (Task #1085) e
    ``LIA_WIZARD_INTAKE_LLM_CLASSIFIER`` (Task #1098). Permite GA
    gradual sem deploy.
    """
    val = os.environ.get("LIA_WIZARD_SUPERVISOR_CLASSIFIER")
    if val is None:
        env = (
            os.environ.get("APP_ENV")
            or os.environ.get("ENVIRONMENT")
            or os.environ.get("LIA_ENV")
            or ""
        ).lower()
        return env not in {"production", "prod", "staging"}
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_timeout_s() -> float:
    try:
        return float(os.environ.get("LIA_WIZARD_SUPERVISOR_TIMEOUT_S", "5"))
    except (TypeError, ValueError):
        return 5.0


_DEFAULT_MODEL = os.environ.get(
    "LIA_WIZARD_SUPERVISOR_MODEL",
    CANONICAL_HAIKU_MODEL,
)


try:
    from pydantic import BaseModel, Field, field_validator

    class SupervisorIntentOutput(BaseModel):
        """Schema canônico do supervisor — output Pydantic-validado."""

        intent: Literal[
            "create_new",
            "resume_draft",
            "edit_published",
            "meta_question",
            "exit_wizard",
            "continue_current",
        ]
        conversational_reply: str = Field(default="")
        confidence: float = Field(default=0.0)

        @field_validator("confidence")
        @classmethod
        def _clip_confidence(cls, v: float) -> float:
            try:
                f = float(v)
            except (TypeError, ValueError):
                return 0.0
            return max(0.0, min(1.0, f))

        @field_validator("conversational_reply")
        @classmethod
        def _trim_reply(cls, v: str) -> str:
            return (v or "")[:600]

except ImportError:  # pragma: no cover — pydantic é dep oficial
    raise


_INLINE_SYSTEM_PROMPT = (
    "Você é o SUPERVISOR de intenção do wizard de criação de vaga da "
    "Plataforma LIA. Sua tarefa: classificar a INTENÇÃO GLOBAL do "
    "recrutador no turno atual. Você NÃO responde a vaga, NÃO classifica "
    "JD, NÃO interpreta gate — apenas decide a ROTA. Existem 6 categorias "
    "canônicas (responda EXATAMENTE uma):\n\n"
    "1. 'create_new' — recrutador quer abrir uma VAGA NOVA. Exemplos: "
    "\"quero abrir outra vaga\", \"vamos criar uma vaga de gerente\", "
    "\"preciso de mais uma vaga\".\n\n"
    "2. 'resume_draft' — recrutador faz referência EXPLÍCITA a um draft "
    "anterior. Exemplos: \"retoma a vaga de ontem\", \"continua o draft "
    "do dev\", \"abre aquele rascunho\".\n\n"
    "3. 'edit_published' — recrutador quer EDITAR uma vaga já publicada. "
    "Exemplos: \"muda a vaga de engenheiro pleno\", \"ajusta a do "
    "gerente\", \"corrige o salário daquela vaga publicada\".\n\n"
    "4. 'meta_question' — pergunta SOBRE o wizard, sobre o que a LIA "
    "precisa, sobre a UI, sobre o processo. Exemplos: \"o que você "
    "precisa de mim?\", \"como funciona?\", \"em que etapa estamos?\", "
    "\"o que esse painel mostra?\".\n\n"
    "5. 'exit_wizard' — recrutador quer SAIR / CANCELAR o wizard INTEIRO, "
    "não apenas responder negativamente a uma pergunta específica. "
    "Exemplos claros: \"cancela tudo\", \"desisto da vaga\", \"depois eu "
    "volto\", \"tchau LIA\", \"vamos parar essa criação\", \"sair do "
    "wizard\". "
    "ANTI-EXEMPLOS — JAMAIS classifique como 'exit_wizard':\n"
    "  • \"agora não\" / \"agora nao\" → respondendo pergunta sim/não\n"
    "  • \"não\" / \"nao\" isolado → respondendo gate ou proposta\n"
    "  • \"depois\" isolado → respondendo timing de proposta\n"
    "  • \"não vou aprovar isso\" → resposta de gate (continue_current)\n"
    "  • \"agora não quero ir pra lá\" → resposta a proposta navegação\n"
    "Em TODOS esses anti-exemplos use 'continue_current'.\n\n"
    "6. 'continue_current' — DEFAULT. A mensagem é resposta natural à "
    "pergunta corrente do wizard (JD colada, aprovação, ajuste de "
    "competência, escolha de pipeline, resposta sim/não a propostas, etc.). "
    "Use SEMPRE que não houver evidência clara das outras 5.\n\n"
    "REGRA CRÍTICA 1: em dúvida entre 'create_new' e 'continue_current', "
    "escolha 'continue_current'. O wizard está SEMPRE em andamento; o "
    "recrutador só salta de vaga quando diz claramente. NÃO interprete "
    "menção a OUTRO cargo no meio de uma JD como 'create_new'.\n\n"
    "REGRA CRÍTICA 2 — disambiguar SIM/NÃO contra HISTÓRICO: se a "
    "mensagem é uma RESPOSTA CURTA (≤25 chars) tipo sim/não/agora-não/"
    "depois/pode/aprovo/rejeito E o HISTÓRICO RECENTE mostra a LIA "
    "fazendo uma pergunta sim/não (proposta de navegação, gate de "
    "aprovação, escolha de modo, confirmação de ação), classifique "
    "SEMPRE como 'continue_current'. 'exit_wizard' exige verbo "
    "EXPLÍCITO de abandono do wizard inteiro, não apenas negação à "
    "pergunta corrente.\n\n"
    "Responda OBRIGATORIAMENTE chamando a tool 'classify_supervisor' com "
    "JSON válido. Em 'conversational_reply' escreva uma resposta curta em "
    "PT-BR (≤2 frases) APENAS para os intents 'meta_question' e "
    "'exit_wizard' (será mostrada ao recrutador). Para os outros 4, "
    "deixe 'conversational_reply' vazio — o graph vai gerar a resposta. "
    "Confidence ≥0.85 só quando o intent for inequívoco."
)


class WizardSupervisorClassifier:
    """Sync LLM supervisor pre-graph para o wizard de criação de vaga.

    Singleton process-wide via ``get_wizard_supervisor_classifier()``.
    Stateless, seguro entre threads. NÃO chama LangGraph, NÃO muta state.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or _DEFAULT_MODEL

    def classify_sync(
        self,
        *,
        user_message: str,
        current_stage: str | None = None,
        tenant_context_snippet: str = "",
        last_turns: list[str] | None = None,
        has_active_draft: bool = False,
    ) -> SupervisorIntentOutput | None:
        """Classifica a intenção global do turno. Sync por contrato.

        Args:
            user_message: mensagem do recrutador (turno atual).
            current_stage: stage atual do graph (apenas para contexto do
                prompt; supervisor NÃO muta).
            tenant_context_snippet: snippet curto do tenant (nome/setor),
                opcional. Resolvido via
                ``resolve_tenant_snippet_for_non_react`` no caller.
            last_turns: últimos turnos da conversa (≤3), para detectar
                loops e mudanças de intenção.
            has_active_draft: ``True`` se há checkpoint LangGraph ativo
                neste thread (passa contexto ao LLM sem expor PII).

        Returns:
            ``SupervisorIntentOutput`` em sucesso. ``None`` quando a flag
            está OFF, sem API key, ou em qualquer erro — caller DEVE
            tratar ``None`` como ``continue_current`` (preserva fluxo
            legacy).
        """
        if not is_supervisor_enabled():
            return None
        msg = (user_message or "").strip()
        if not msg:
            return None

        api_key = (
            os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not api_key:
            logger.debug("[WizardSupervisor] no API key — skip")
            return None

        try:
            from anthropic import Anthropic  # type: ignore  # W3-027-EXEMPT: tool_choice forcing (tool_choice={'type':'tool','name':...}) not exposed by factory API
        except ImportError:  # pragma: no cover — anthropic é dep oficial
            return None

        client_kwargs: dict[str, Any] = {
            "api_key": api_key, "timeout": _get_timeout_s(),
        }
        base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        if base_url:
            client_kwargs["base_url"] = base_url

        try:
            client = Anthropic(**client_kwargs)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("[WizardSupervisor] client init failed: %s", exc)
            return None

        schema = {
            "type": "object",
            "required": ["intent", "conversational_reply", "confidence"],
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": sorted(ALLOWED_SUPERVISOR_INTENTS),
                    "description": (
                        "Intent classificado, OBRIGATORIAMENTE da allowlist."
                    ),
                },
                "conversational_reply": {
                    "type": "string",
                    "description": (
                        "Resposta em PT-BR (≤2 frases). Preencher APENAS "
                        "para 'meta_question' e 'exit_wizard'. Vazio para "
                        "os outros 4 intents."
                    ),
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "additionalProperties": False,
        }
        tool = {
            "name": "classify_supervisor",
            "description": (
                "Classifica a intenção global do recrutador no turno "
                "atual do wizard de criação de vaga."
            ),
            "input_schema": schema,
        }

        stage_label = current_stage or "(não iniciado)"
        draft_flag = "sim" if has_active_draft else "não"
        tenant_block = (tenant_context_snippet or "")[:1500] or "(não disponível)"

        turns_block = "(sem histórico)"
        if last_turns:
            _lines: list[str] = []
            for _t in [str(t or "").strip() for t in last_turns if t][-3:]:
                if _t:
                    _lines.append(f"- {_t[:300]}")
            if _lines:
                turns_block = "\n".join(_lines)[:1200]

        user_block = (
            f"# Stage atual do wizard\n{stage_label}\n\n"
            f"# Draft ativo neste thread?\n{draft_flag}\n\n"
            f"# Contexto do tenant\n{tenant_block}\n\n"
            f"# Histórico recente da conversa\n{turns_block}\n\n"
            f"# Mensagem do recrutador\n{msg[:1500]}\n\n"
            "Classifique chamando a tool 'classify_supervisor'."
        )

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=300,
                temperature=0.0,
                system=_INLINE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_block}],
                tools=[tool],
                tool_choice={"type": "tool", "name": "classify_supervisor"},
            )
        except Exception as exc:
            logger.info(
                "[WizardSupervisor] LLM call failed (fail-open): %s", exc,
            )
            return None

        raw: dict[str, Any] | None = None
        for block in getattr(response, "content", []) or []:
            if (
                getattr(block, "type", None) == "tool_use"
                and getattr(block, "name", None) == "classify_supervisor"
            ):
                inp = getattr(block, "input", None)
                if isinstance(inp, dict):
                    raw = inp
                    break
        if not raw:
            logger.info("[WizardSupervisor] LLM returned no tool_use block")
            return None

        # Defesa em profundidade: allowlist enforced antes do Pydantic.
        if raw.get("intent") not in ALLOWED_SUPERVISOR_INTENTS:
            logger.warning(
                "[WizardSupervisor] off-allowlist intent=%r — fallback",
                raw.get("intent"),
            )
            return None

        try:
            return SupervisorIntentOutput.model_validate(raw)
        except Exception as exc:
            logger.warning(
                "[WizardSupervisor] schema invalid: %s — fallback", exc,
            )
            return None


_default_classifier: WizardSupervisorClassifier | None = None


def get_wizard_supervisor_classifier() -> WizardSupervisorClassifier:
    """Singleton accessor — stateless, thread-safe."""
    global _default_classifier  # noqa: PLW0603
    if _default_classifier is None:
        _default_classifier = WizardSupervisorClassifier()
    return _default_classifier
