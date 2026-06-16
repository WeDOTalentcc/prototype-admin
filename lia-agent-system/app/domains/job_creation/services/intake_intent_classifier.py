"""Intake Intent Classifier — Task #1098.

Substitui (defense-in-depth) o IF/ELSE estático do "input-thin guard"
em ``app/domains/job_creation/graph.py::jd_enrichment_node`` por um
classificador LLM (Claude Haiku, temp=0) com schema Pydantic obrigatório
e allowlist enforced. Mesmo padrão do
``WizardGateClassifier`` (Task #1085) e ``IntakeExtractor`` —
sync por contrato porque é chamado de dentro de um nó síncrono do
LangGraph (``jd_enrichment_node``).

## Por que existir

O guard estático de Task #1096 (``raw_len < 100 and not parsed_title``)
trata QUALQUER mensagem curta como "intent_only" e pede JD/upload. Isso
pega corretamente o caso "vamos abrir uma vaga" mas trata mal:

- Perguntas meta sobre o wizard ("o que você precisa de mim?", "como
  funciona?", "onde está o painel?") — o usuário fica sem resposta útil.
- Frases que JÁ trazem o título do cargo embutido em forma coloquial
  ("preciso de um dev pleno react") — o guard dispara mesmo quando o
  IntakeExtractor regex falha.
- Requisições off-topic ("oi tudo bem?", "que dia é hoje?") — o guard
  responde com o template de "preciso da JD", confundindo o recrutador.

Com o classifier, dividimos em 4 intents canônicos:

  * ``provides_jd_intent`` — usuário JÁ está fornecendo material útil
    (JD colada, título de cargo coloquial, briefing curto). Continua
    para o LLM enrichment, mesmo com `raw_len` curto. O LLM se vira.
  * ``meta_question`` — usuário pergunta sobre o wizard, sobre a UI,
    sobre o que a LIA precisa. Devolve resposta útil contextual SEM
    cair no template de guard.
  * ``intent_only`` — usuário só sinaliza "quero abrir uma vaga". Aí
    sim o guard original faz sentido — pede JD/upload/título.
  * ``off_topic`` — saudação, pergunta fora de escopo. Redireciona
    educadamente para o título da vaga.

## Segurança e custo

- Output 100% Pydantic-validado + allowlist post-hoc (mesma defesa
  em profundidade do WizardGateClassifier).
- Mutação de state DETERMINÍSTICA: o caller (``jd_enrichment_node``)
  mapeia ``intent`` → branch fixo. ``conversational_reply`` do LLM
  é exibido AO USUÁRIO mas nunca interpretado como controle de fluxo.
- ≤300 tokens/turno, ≤700ms p95.
- ``LIA_WIZARD_INTAKE_LLM_CLASSIFIER`` (default ``1`` em dev, ``0``
  em prod até GA). Quando OFF, ``classify_sync`` retorna ``None`` e o
  caller cai 100% no guard estático original (preserva fail-closed).
- Em qualquer falha (timeout, sem API key, schema inválido,
  off-allowlist), retorna ``None`` (fail-OPEN para o guard original
  — não troca um problema de UX por um problema de disponibilidade).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


# Allowlist canônica.
ALLOWED_INTAKE_INTENTS: frozenset[str] = frozenset({
    "provides_jd_intent",
    "meta_question",
    "intent_only",
    "off_topic",
})


def is_classifier_enabled() -> bool:
    """Read at call-time so test/runtime overrides take effect.

    Default: ON em dev/test, OFF em prod/staging. Mesma postura do
    LIA_WIZARD_LLM_GATES (Task #1085).
    """
    val = os.environ.get("LIA_WIZARD_INTAKE_LLM_CLASSIFIER")
    if val is None:
        # Architect feedback: parity with all canonical env detectors —
        # checa APP_ENV / ENVIRONMENT / LIA_ENV. Sem LIA_ENV o classifier
        # ficaria ON por default em prod-only-LIA_ENV deployments,
        # violando o rollout contract (OFF em prod/staging até GA).
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
        return float(os.environ.get("LIA_WIZARD_INTAKE_CLASSIFIER_TIMEOUT_S", "5"))
    except (TypeError, ValueError):
        return 5.0


from app.shared.llm_models import CANONICAL_HAIKU_MODEL

# Task #1123 — canonical default delegado a app.shared.llm_models. O
# literal "claude-3-5-haiku-20241022" usado por 15+ callsites retornava
# UNSUPPORTED_MODEL do modelfarm proxy local
# (localhost:1106/modelfarm/anthropic), fazendo o classifier fail-OPEN
# silenciosamente em todo turno e deixando o guard estático firing
# para sempre. Override por env var preservado.
_DEFAULT_MODEL = os.environ.get(
    "LIA_WIZARD_INTAKE_CLASSIFIER_MODEL",
    CANONICAL_HAIKU_MODEL,
)


try:
    from pydantic import BaseModel, Field, field_validator

    class IntakeIntentOutput(BaseModel):
        intent: Literal[
            "provides_jd_intent",
            "meta_question",
            "intent_only",
            "off_topic",
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
    "Você é um classificador de intenção do PRIMEIRO turno do wizard de "
    "criação de vaga da Plataforma LIA. O recrutador acabou de mandar uma "
    "mensagem curta no chat e você precisa decidir UMA ÚNICA categoria "
    "entre 4 opções:\n\n"
    "1. 'provides_jd_intent' — A mensagem JÁ traz material útil para abrir "
    "a vaga (título de cargo, descrição, briefing curto). Exemplos: "
    "\"desenvolvedor python senior\", \"preciso de um dev pleno react\", "
    "\"vaga: gerente de produto sênior remoto\".\n\n"
    "2. 'meta_question' — O recrutador faz uma pergunta SOBRE o wizard, a "
    "UI, ou o que a LIA precisa. Exemplos: \"o que você precisa de mim?\", "
    "\"como funciona isso?\", \"onde fica o painel?\", \"o que eu faço "
    "agora?\".\n\n"
    "3. 'intent_only' — O recrutador SÓ sinaliza intenção de criar vaga, "
    "sem dar matéria-prima. Exemplos: \"vamos abrir uma vaga\", \"quero "
    "criar vaga\", \"preciso contratar\".\n\n"
    "4. 'off_topic' — Saudações, pequena conversa, ou tópicos fora de "
    "criação de vaga. Exemplos: \"oi tudo bem?\", \"que dia é hoje?\", "
    "\"você é uma IA?\".\n\n"
    "Responda OBRIGATORIAMENTE chamando a tool 'classify_intake' com JSON "
    "válido. Em 'conversational_reply' escreva uma resposta curta em PT-BR "
    "(≤2 frases) que será mostrada ao recrutador — útil e contextual ao "
    "intent escolhido. Em caso de dúvida entre 'intent_only' e "
    "'meta_question', escolha 'meta_question' (mais útil ao recrutador). "
    "Confidence ≥0.85 só quando o intent for inequívoco."
)


_PROMPT_REL_PATH = "prompts/job_creation/intake_intent_classifier.yaml"


def _load_system_prompt() -> str:
    """Load YAML prompt if present; else inline default. Cached na instância."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return _INLINE_SYSTEM_PROMPT
    app_root = Path(__file__).resolve().parents[3]
    prompt_path = app_root / _PROMPT_REL_PATH
    try:
        data = yaml.safe_load(prompt_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return _INLINE_SYSTEM_PROMPT
    except Exception as exc:
        logger.warning("[IntakeIntentClassifier] prompt YAML load failed: %s", exc)
        return _INLINE_SYSTEM_PROMPT
    return data.get("system_prompt") or _INLINE_SYSTEM_PROMPT


class IntakeIntentClassifier:
    """Sync LLM classifier para o primeiro turno do wizard.

    Singleton process-wide via ``get_intake_intent_classifier()``. Stateless,
    seguro entre threads. NÃO chama LangGraph nem o IntakeExtractor — só
    decide o branch que o ``jd_enrichment_node`` vai tomar.
    """

    def __init__(self, model: str | None = None) -> None:
        self._model = model or _DEFAULT_MODEL
        self._system_prompt: str | None = None

    def _get_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = _load_system_prompt()
        return self._system_prompt

    def classify_sync(
        self,
        *,
        user_message: str,
        has_panel_form: bool = False,
        has_attached_file: bool = False,
        last_turns: list[str] | None = None,
    ) -> IntakeIntentOutput | None:
        """Classifica o intent do primeiro turno. Sync por contrato.

        Returns:
            ``IntakeIntentOutput`` em sucesso. ``None`` quando a flag está
            OFF, quando não há API key, ou em qualquer erro (timeout,
            schema inválido, off-allowlist) — caller deve tratar ``None``
            como "use o guard estático original".
        """
        if not is_classifier_enabled():
            return None
        msg = (user_message or "").strip()
        if not msg:
            return None

        api_key = (
            os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not api_key:
            logger.debug("[IntakeIntentClassifier] no API key — skip")
            return None

        try:
            from anthropic import Anthropic  # type: ignore  # W3-027-EXEMPT: tool_choice forcing (tool_choice={'type':'tool','name':...}) not exposed by factory API
        except ImportError:  # pragma: no cover — anthropic é dep oficial
            return None

        client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": _get_timeout_s()}
        base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        if base_url:
            client_kwargs["base_url"] = base_url

        try:
            client = Anthropic(**client_kwargs)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("[IntakeIntentClassifier] client init failed: %s", exc)
            return None

        schema = {
            "type": "object",
            "required": ["intent", "conversational_reply", "confidence"],
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": sorted(ALLOWED_INTAKE_INTENTS),
                    "description": "Intent classificado, OBRIGATORIAMENTE da allowlist.",
                },
                "conversational_reply": {
                    "type": "string",
                    "description": (
                        "Resposta natural curta em PT-BR (≤2 frases) — "
                        "útil e contextual ao intent escolhido."
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
            "name": "classify_intake",
            "description": "Classifica o intent do primeiro turno do wizard.",
            "input_schema": schema,
        }

        ctx_bits = []
        if has_panel_form:
            ctx_bits.append("painel-lateral=preenchido-parcialmente")
        if has_attached_file:
            ctx_bits.append("arquivo-anexado=sim")
        ctx = ", ".join(ctx_bits) if ctx_bits else "(sem contexto extra)"

        # Task #1123 — últimas 3 turns para que o classifier saiba se o
        # recrutador acabou de fazer a mesma pergunta meta (evita loop).
        turns_block = "(sem histórico)"
        if last_turns:
            _lines: list[str] = []
            for _t in [str(t or "").strip() for t in last_turns if t][-3:]:
                if _t:
                    _lines.append(f"- {_t[:300]}")
            if _lines:
                turns_block = "\n".join(_lines)[:1200]

        user_block = (
            f"# Contexto da sessão\n{ctx}\n\n"
            f"# Histórico recente da conversa\n{turns_block}\n\n"
            f"# Mensagem do recrutador\n{msg[:1500]}\n\n"
            "Classifique o intent chamando a tool 'classify_intake'."
        )

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=300,
                temperature=0.0,
                system=self._get_prompt(),
                messages=[{"role": "user", "content": user_block}],
                tools=[tool],
                tool_choice={"type": "tool", "name": "classify_intake"},
            )
        except Exception as exc:
            logger.info("[IntakeIntentClassifier] LLM call failed (fail-open): %s", exc)
            return None

        raw: dict[str, Any] | None = None
        for block in getattr(response, "content", []) or []:
            if (
                getattr(block, "type", None) == "tool_use"
                and getattr(block, "name", None) == "classify_intake"
            ):
                inp = getattr(block, "input", None)
                if isinstance(inp, dict):
                    raw = inp
                    break
        if not raw:
            logger.info("[IntakeIntentClassifier] LLM returned no tool_use block")
            return None

        # Defesa em profundidade: allowlist enforced antes do Pydantic.
        if raw.get("intent") not in ALLOWED_INTAKE_INTENTS:
            logger.warning(
                "[IntakeIntentClassifier] off-allowlist intent=%r — fallback",
                raw.get("intent"),
            )
            return None

        try:
            return IntakeIntentOutput.model_validate(raw)
        except Exception as exc:
            logger.warning("[IntakeIntentClassifier] schema invalid: %s — fallback", exc)
            return None


_default_classifier: IntakeIntentClassifier | None = None


def get_intake_intent_classifier() -> IntakeIntentClassifier:
    global _default_classifier  # noqa: PLW0603
    if _default_classifier is None:
        _default_classifier = IntakeIntentClassifier()
    return _default_classifier
