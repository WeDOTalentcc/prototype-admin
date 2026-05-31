"""Wizard meta-question helper — Task #1123.

Gera resposta conversacional rica para perguntas meta / off-topic /
ask_clarification feitas no meio dos 4 gates HITL do wizard de criação
de vaga. Usa Claude Sonnet (não Haiku) para entregar uma resposta
contextual em PT-BR que combina:

  - ``tenant_context_snippet`` (nome/setor da empresa, plano, etc.) —
    para a resposta soar tenant-aware;
  - ``last_turns`` (últimos turnos da conversa) — para não repetir a
    mesma coisa nem ignorar contexto recente;
  - ``stage_description`` — uma frase curta descrevendo onde o wizard
    está (ex.: "escolhendo modo de triagem WSI").

A resposta SEMPRE termina com uma pergunta de continuidade ("deseja
continuar com X?") para não deixar o recrutador travado.

## Contrato de segurança

- **Mutação de state**: nenhuma. O caller (gate_node) mantém o state
  inalterado e popula apenas ``gate_clarify_message`` com o retorno
  desta função. O LLM aqui é gerador de texto puro — nunca controle
  de fluxo.
- **Fail-OPEN**: qualquer falha (sem API key, timeout, exceção)
  devolve ``None`` (e o caller cai no texto canned do classifier).
- **Custo**: chamada Sonnet ~$0.003/turno, timeout default 6s, max
  200 tokens — só dispara em ask_question / off_topic / ask_clarification
  (≤10% dos turnos do wizard em produção típica).
- **FairnessGuard**: já roda no caller ANTES da classificação; aqui
  não chamamos novamente — a mensagem que chega já foi liberada.

## Sync por contrato

Mesmo padrão do ``IntakeIntentClassifier``: graph nodes são síncronos
e chamamos via ``anthropic.Anthropic`` SDK síncrono. Sem
``asyncio.run`` / ThreadPoolExecutor — simplifica o caller.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.shared.llm_models import CANONICAL_SONNET_MODEL

logger = logging.getLogger(__name__)


_DEFAULT_MODEL = os.environ.get(
    "LIA_WIZARD_META_HELPER_MODEL", CANONICAL_SONNET_MODEL,
)


def _get_timeout_s() -> float:
    try:
        return float(os.environ.get("LIA_WIZARD_META_HELPER_TIMEOUT_S", "6"))
    except (TypeError, ValueError):
        return 6.0


_SYSTEM_PROMPT = (
    "Você é a LIA, assistente de IA de recrutamento da Plataforma "
    "WeDoTalent. O recrutador está no meio do wizard de criação de "
    "vaga e fez uma pergunta meta (sobre o wizard, sobre o que você "
    "precisa, sobre como decidir alguma coisa) OU mandou uma mensagem "
    "fora de contexto. Você receberá o ESTADO REAL da vaga (ficha viva) "
    "com campos preenchidos, campos faltantes, status da JD, competências "
    "e modo de triagem. USE ESSES DADOS para responder com precisão. "
    "Por exemplo: se o recrutador perguntar 'o que falta?' ou 'o que você "
    "precisa?', liste exatamente os campos faltantes da ficha viva. Se a "
    "JD já foi gerada, reconheça isso na resposta. "
    "Responda de forma curta (2-4 frases) em PT-BR. "
    "SEMPRE termine com uma pergunta de continuidade contextual. "
    "NUNCA invente dados da vaga, da empresa ou do candidato. "
    "NUNCA execute ação — você é só geração de texto. "
    "NUNCA repita literalmente a última resposta da LIA (consulte o "
    "histórico para evitar loop). Se o histórico mostra que o recrutador "
    "já fez esta pergunta, reconheça e ofereça uma explicação alternativa."
)


def generate_meta_response_sync(
    *,
    stage: str,
    user_message: str,
    tenant_context_snippet: str = "",
    last_turns: list[str] | None = None,
    stage_description: str = "",
    wizard_state_summary: str = "",
) -> str | None:
    """Gera resposta conversacional para pergunta meta / off-topic.

    Returns:
        String pronta para ``gate_clarify_message``. ``None`` em qualquer
        falha (sem API key, timeout, exceção) — caller cai no fallback
        canned. NUNCA levanta exceção (todas capturadas internamente).
    """
    msg = (user_message or "").strip()
    if not msg:
        return None

    api_key = (
        os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    if not api_key:
        logger.debug("[WizardMetaHelper] no API key — skip")
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
        logger.warning("[WizardMetaHelper] client init failed: %s", exc)
        return None

    # Histórico recente — últimas 3 turns, truncadas a 300 chars.
    turns_block = "(sem histórico)"
    if last_turns:
        _lines: list[str] = []
        for _t in [str(t or "").strip() for t in last_turns if t][-3:]:
            if _t:
                _lines.append(f"- {_t[:300]}")
        if _lines:
            turns_block = "\n".join(_lines)[:1200]

    state_block = (wizard_state_summary or "(estado não disponível)")[:800]
    user_block = (
        f"# Stage atual do wizard\n{stage}\n\n"
        f"# Descrição do stage (em uma frase)\n{(stage_description or '(não disponível)')[:300]}\n\n"
        f"# Estado real da vaga (ficha viva — use isto para responder 'o que falta?')\n{state_block}\n\n"
        f"# Contexto da empresa (tenant)\n{(tenant_context_snippet or '(não disponível)')[:500]}\n\n"
        f"# Histórico recente da conversa\n{turns_block}\n\n"
        f"# Mensagem do recrutador (pergunta meta / off-topic)\n{msg[:1500]}\n\n"
        "Responda em PT-BR (2-4 frases). Use o estado real da vaga para responder "
        "com precisão (ex: se perguntou 'o que falta?', liste os campos faltantes). "
        "Termine com uma pergunta de continuidade contextual ao stage."
    )

    try:
        response = client.messages.create(
            model=_DEFAULT_MODEL,
            max_tokens=300,
            temperature=0.3,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_block}],
        )
    except Exception as exc:
        logger.info("[WizardMetaHelper] LLM call failed (fail-open): %s", exc)
        return None

    text_parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text":
            t = getattr(block, "text", "") or ""
            if t:
                text_parts.append(t)
    reply = " ".join(text_parts).strip()
    if not reply:
        return None
    return reply[:1000]
